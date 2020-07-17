import pymongo
import re
import six


class MongoPool(object):
    """
        Manages multiple mongo connections to different clusters, and performs
        database to connection matching.
    """

    def __init__(self, config, network_timeout=None, connection_class=None,
                 j=False):
        super(MongoPool, self).__init__()
        # Set timeout.
        self._network_timeout = network_timeout

        # { label -> cluster config } dict
        self._clusters = []
        self._validate_config(config)
        self._parse_configs(config)
        self._mapped_databases = []

        self._connection_class = connection_class or pymongo.MongoClient
        # Journaling for pymongo.
        self.j = j

    def get_cluster(self, label):
        """Returns a connection to a mongo-clusters.

        Args:
            label (string): the label of a cluster.

        Returns:
            A connection to the cluster labeld with label.

        Raises:
            AttributeError: there is no cluster with the given label in the
                config
        """
        for cluster in self._clusters:
            if label == cluster['label']:
                return self._get_connection(cluster)
        raise AttributeError('No such cluster %s.' % label)

    @staticmethod
    def _validate_config(config):
        """Validate that the provided configurtion is valid.

        Each dictionary in the configuration list must have the following
        mandatory entries :
            {label: {host(string), port(int), dbpath(string|list of strings)}}
        It can also contain 1 optional key:
            {read_preference(string)}

        Args:
            config: the list of configurations provided at instantiation

        Raises:
            TypeError: a fault in the configurations is found
        """
        if not isinstance(config, list):
            raise TypeError('Config must be a list')

        for config_dict in config:
            if not isinstance(config_dict, dict):
                raise TypeError('Config must be a list of dictionaries')
            label = list(config_dict.keys())[0]
            cfg = config_dict[label]
            if not isinstance(cfg, dict):
                raise TypeError('Config structure is broken')

            if 'host' not in cfg:
                raise TypeError('Config entries must have a value for host')
            if not isinstance(cfg['host'], six.string_types) and not isinstance(cfg['host'], list):
                raise TypeError('Host must be a string or a list.')

            if 'port' not in cfg:
                raise TypeError('Config entries must have a value for port')
            if not isinstance(cfg['port'], int):
                raise TypeError('Port must be an int')

            if 'dbpath' not in cfg:
                raise TypeError('Config entries must have a value for dbpath')
            if not isinstance(cfg['dbpath'], six.string_types):
                if not isinstance(cfg['dbpath'], list):
                    raise TypeError('Dbpath must either a string or a list of '
                                    'strings')
                for dbpath in cfg['dbpath']:
                    if not isinstance(dbpath, six.string_types):
                        raise TypeError('Dbpath must either a string or a list '
                                        'of strings')

            if ('read_preference' in cfg and
                not isinstance(cfg['read_preference'], six.string_types)):
                raise TypeError('Read_preference must be a string')

            if ('replicaSet' in cfg and
                not isinstance(cfg['replicaSet'], six.string_types)):
                raise TypeError('replicaSet must be a string')

    def _parse_configs(self, config):
        """Builds a dict with information to connect to Clusters.

        Parses the list of configuration dictionaries passed by the user and
        builds an internal dict (_clusters) that holds information for creating
        Clients connecting to Clusters and matching database names.

        Args:
            config: A list of dictionaries containing connecting and
                identification information about Clusters.
                A dict has the following structure:
                {label: {host, port, read_preference, dbpath}}.

        Raises:
            Exception('No configuration provided'): no configuration provided.
        """
        for config_dict in config:
            label = list(config_dict.keys())[0]
            cfg = config_dict[label]
            # Transform dbpath to something digestable by regexp.
            dbpath = cfg['dbpath']
            pattern = self._parse_dbpath(dbpath)

            read_preference = cfg.get('read_preference', 'primary').upper()
            read_preference = self._get_read_preference(read_preference)

            # Put all parameters that could be passed to pymongo.MongoClient
            # in a separate dict, to ease MongoClient creation.
            cluster_config = {
                'params': {
                    'host': cfg['host'],
                    'port': cfg['port'],
                    'read_preference': read_preference,
                    'replicaSet': cfg.get('replicaSet')
                },
                'pattern': pattern,
                'label': label
            }

            self._clusters.append(cluster_config)

    @staticmethod
    def _parse_dbpath(dbpath):
        """Converts the dbpath to a regexp pattern.

        Transforms dbpath from a string or an array of strings to a
        regexp pattern which will be used to match database names.

        Args:
            dbpath: a string or an array containing the databases to be matched
                from a cluster.

        Returns:
            A regexp pattern that will match any of the desired databases on
            on a cluster.
        """
        if isinstance(dbpath, list):
            # Support dbpath param as an array.
            dbpath = '|'.join(dbpath)

        # Append $ (end of string) so that twit will not match twitter!
        if not dbpath.endswith('$'):
            dbpath = '(%s)$' % dbpath

        return dbpath

    @staticmethod
    def _get_read_preference(read_preference):
        """Converts read_preference from string to pymongo.ReadPreference value.

            Args:
                read_preference: string containig the read_preference from the
                    config file
            Returns:
                A value from the pymongo.ReadPreference enum

            Raises:
                Exception: Invalid read preference"""
        read_preference = getattr(pymongo.ReadPreference, read_preference, None)
        if read_preference is None:
            raise ValueError('Invalid read preference: %s' % read_preference)
        return read_preference

    def set_timeout(self, network_timeout):
        """Set the timeout for existing and future Clients.

        Close all current connections. This will cause future operations to
        create new Clients with the network_timeout passed through
        socketTimeoutMS optional parameter.

        Args:
            network_timeout: The new value in milliseconds for the timeout.
        """
        # Do nothing if attempting to set the same timeout twice.
        if network_timeout == self._network_timeout:
            return
        self._network_timeout = network_timeout
        self._disconnect()

    def _disconnect(self):
        """Disconnect from all MongoDB Clients."""
        for cluster in self._clusters:
            if 'connection' in cluster:
                connection = cluster.pop('connection')
                connection.close()
        # Remove all attributes that are database names so that next time
        # when they are accessed, __getattr__ will be called and will create
        # new Clients
        for dbname in self._mapped_databases:
            self.__delattr__(dbname)
        self._mapped_databases = []

    def _get_connection(self, cluster):
        """Return a connection to a Cluster.

        Return a MongoClient or a MongoReplicaSetClient for the given Cluster.
        This is done in a lazy manner (if there is already a Client connected to
        the Cluster, it is returned and no other Client is created).

        Args:
            cluster: A dict containing information about a cluster.

        Returns:
            A MongoClient or MongoReplicaSetClient instance connected to the
            desired cluster
        """
        # w=1 because:
        # http://stackoverflow.com/questions/14798552/is-mongodb-2-x-write-concern-w-1-truly-equals-to-safe-true
        if 'connection' not in cluster:
            cluster['connection'] = self._connection_class(
                socketTimeoutMS=self._network_timeout,
                w=1,
                j=self.j,
                **cluster['params'])

        return cluster['connection']

    def _match_dbname(self, dbname):
        """Map a database name to the Cluster that holds the database.

        Args:
            dbname: A database name.

        Returns:
            A dict containing the information about the Cluster that holds the
            database.
        """
        for config in self._clusters:
            if re.match(config['pattern'], dbname):
                return config
        raise Exception('No such database %s.' % dbname)

    def _get_connection_by_db_name(self, db_name):
        config = self._match_dbname(db_name)
        return self._get_connection(config)

    def _init_database(self, connection, db_name):
        return connection[db_name]

    def __getattr__(self, name):
        """Map a database name to the coresponding pymongo.Database instance"""
        connection = self._get_connection_by_db_name(name)
        database = self._init_database(connection, name)
        # Remember this name->database mapping on the object. This will cause
        # future references to the same name to NOT invoke self.__getattr__,
        # and be resolved directly at object level.
        setattr(self, name, database)
        self._mapped_databases.append(name)
        return database

    def __getitem__(self, key):
        return getattr(self, key)
