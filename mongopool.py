import re
import pymongo

from singleton import Singleton


class MongoPool(object):
    """
        Manages multiple mongo connections to different clusters, and performs
        database to connection matching.
    """

    __metaclass__ = Singleton

    def __init__(self, config=None, network_timeout=None):

        if config == None:
            raise Exception('Not configurations provided')

        # Set timeout.
        self._network_timeout = network_timeout

        # { label -> cluster config } dict
        self._clusters = []
        for config_dict in config:
            label = config_dict.keys()[0]
            cfg = config_dict[label]
            # Transform dbpath to something digestable by regexp.
            pattern = cfg['dbpath']
            if isinstance(pattern, list):
                # Support dbpath param as an array.
                pattern = '|'.join(pattern)
            # Append $ (end of string) so that twit will not match twitter!
            if not pattern.endswith('$'):
                pattern = '(%s)$' % pattern

            preference = cfg.get('read_preference', 'primary').upper()
            read_preference = getattr(pymongo.ReadPreference, preference, None)
            if read_preference is None:
                raise ValueError('Invalid read preference: %s' % read_preference)

            # Put all parameters that could be passed to pymongo.MongoClient
            # in a separate dict, to ease MongoClient creation.
            cluster_config = {
                'params': {
                    'host': cfg['host'],
                    'port': cfg['port'],
                    'read_preference': read_preference,
                },
                'pattern': pattern,
                'label': label
            }

            replica_set = cfg.get('replica_set')
            # Leave this code here, some of it will be removed for newer
            # versions of pymongo
            if replica_set:
                cluster_config['params']['replicaSet'] = replica_set
                # ReplicaSetConnection has a slightly different API;
                # need to change host field into hosts_or_uri and move port
                # into the hosts_or_uri field
                host = cluster_config['params'].pop('host')
                port = cluster_config['params'].pop('port')

                if not isinstance(host, list):
                    host = [host]
                hosts_or_uri = ','.join(['%s:%s' % (h, port) for h in host])

                cluster_config['params']['hosts_or_uri'] = hosts_or_uri

            self._clusters.append(cluster_config)

            self._mapped_databases = []

    def set_timeout(self, network_timeout):
        # Do nothing if attempting to set the same timeout twice.
        if network_timeout == self._network_timeout:
            return
        self._network_timeout = network_timeout
        # Close all current connections. This will cause future operations
        # to create new connections with the new timeout.
        self.disconnect()

    def disconnect(self):
        """ Disconnect from all MongoDB connections. """
        for cluster in self._clusters:
            if 'connection' in cluster:
                c = cluster.pop('connection')
                c.close()

        for dbname in self._mapped_databases:
            self.__delattr__(dbname)
        self._mapped_databases = []

    def _get_connection(self, cluster):
        """ Creates & returns a connection for a cluster - lazy. """
        if 'connection' not in cluster:
            # Try to use replica set connection starting with pymongo 2.1
            if 'replicaSet' in cluster['params']:
                cluster['connection'] = pymongo.MongoReplicaSetClient(
                    socketTimeoutMS=self._network_timeout,
                    safe=True,
                    **cluster['params'])
            else:
                cluster['connection'] = pymongo.MongoClient(
                    socketTimeoutMS=self._network_timeout,
                    safe=True,
                    **cluster['params'])

        return cluster['connection']

    def _match_dbname(self, dbname):
        for config in self._clusters:
            if re.match(config['pattern'], dbname):
                return config
        else:
            raise Exception('No such database %s.' % dbname)

    def __getattr__(self, name):
        """
          Return a pymongo.Database object that contains the "name" database.
        """
        # Get or init a pymongo.MongoClient that matches the supplied name.
        # Instantiates one if necessary.
        config = self._match_dbname(name)
        connection = self._get_connection(config)
        db_name = name
        database = connection[db_name]
        # Remember this name->database mapping on the object. This will cause
        # future references to the same name to NOT invoke self.__getattr__,
        # and be resolved directly at object level.
        setattr(self, name, database)
        self._mapped_databases.append(name)
        return database

    def __getitem__(self, key):
        return getattr(self, key)
