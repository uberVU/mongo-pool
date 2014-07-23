from mock import patch, call
from unittest import TestCase
import pymongo
from mongopool import MongoPool


class MongoPoolTestCase(TestCase):
    def setUp(self):
        self.config = [{'label1': {'host': '127.0.0.1',
                                   'port': 27017,
                                   'dbpath': 'db1'}},
                       {'label2': {'host': '127.0.0.1',
                                   'port': 27017,
                                   'dbpath': 'db2',
                                   'replicaSet': 'rset0'}},
                       {'label3': {'host': '127.0.0.1',
                                   'port': 27018,
                                   'dbpath': 'dbp'}},
                       {'label4': {'host': '127.0.0.1',
                                   'port': 27019,
                                   'dbpath': 'dbpat'}},
                       {'label5': {'host': '127.0.0.1',
                                   'port': 27020,
                                   'dbpath': 'dbpattern\d*'}},
                       {'label6': {'host': '127.0.0.1',
                                   'port': 27021,
                                   'dbpath': ['arraydb1', 'arraydb\dxyz']}}]
        self.call_arguments = {'host': '127.0.0.1',
                               'port': 27017,
                               'safe': True,
                               'read_preference': 0,
                               'socketTimeoutMS': None}

    def test_default_connection_classes(self):
        """
        Ensure that if no custom classes are provided, the default one are used
        (MongoClient, MongoReplicaSetClient).
        """
        pool = MongoPool(self.config)
        self.assertIs(pool._connection_class, pymongo.MongoClient,
                      "Does not use MongoClient by default.")
        self.assertIs(pool._rset_connection_class, pymongo.MongoReplicaSetClient,
                      "Does not use MongoReplicaSetClient by default.")

    @patch('mongopool.mongopool.pymongo.ReplicaSetConnection')
    @patch('mongopool.mongopool.pymongo.Connection')
    def test_uses_passed_connection_class(self, mock_connection,
                                          mock_rset_connection):
        """
        Ensure passed custom connection classes are used.
        """
        kwarguments = {'connection_class': mock_connection,
                       'rset_connection_class': mock_rset_connection}
        pool = MongoPool(self.config, **kwarguments)
        self.assertIs(pool._connection_class, mock_connection,
                      "Does not use passed connection class")
        self.assertIs(pool._rset_connection_class, mock_rset_connection,
                      "Does not use passed replicaSet connection class")

    def test_raises_exception_for_invalid_host(self):
        config = [{'label': {'port': 27017, 'dbpath': '.*'}}]
        with self.assertRaises(TypeError):
            MongoPool(config)
        config[0]['label']['host'] = 1
        with self.assertRaises(TypeError):
            MongoPool(config)
        config[0]['label']['host'] = '127.0.0.1'
        try:
            MongoPool(config)
        except TypeError:
            self.fail('MongoPool._validate_config raised Type Error while '
                      'valid config was provided')

    def test_raises_exception_for_invalid_port(self):
        config = [{'label': {'host': '127.0.0.1', 'dbpath': '.*'}}]
        with self.assertRaises(TypeError):
            MongoPool(config)
        config[0]['label']['port'] = 'a'
        with self.assertRaises(TypeError):
            MongoPool(config)
        config[0]['label']['port'] = 27017
        try:
            MongoPool(config)
        except TypeError:
            self.fail('MongoPool._validate_config raised Type Error while '
                      'valid config was provided')

    def test_rasies_exception_for_invalid_dbpath(self):
        config = [{'label': {'host': '127.0.0.1', 'port': 27017}}]
        with self.assertRaises(TypeError):
            MongoPool(config)
        config[0]['label']['dbpath'] = 1
        with self.assertRaises(TypeError):
            MongoPool(config)
        config[0]['label']['dbpath'] = '.*'
        try:
            MongoPool(config)
        except TypeError:
            self.fail('MongoPool._validate_config raised Type Error while '
                      'valid config was provided')
        config[0]['label']['dbpath'] = ['db1', 'db2']
        try:
            MongoPool(config)
        except TypeError:
            self.fail('MongoPool._validate_config raised Type Error while '
                      'valid config was provided')

    def test_rasies_exception_for_invalid_replicaSet(self):
        config = [{'label': {'host': '127.0.0.1', 'port': 27017,
                             'dbpath': '.*'}}]
        config[0]['label']['replicaSet'] = 1
        with self.assertRaises(TypeError):
            MongoPool(config)
        config[0]['label']['replicaSet'] = 'rset0'
        try:
            MongoPool(config)
        except TypeError:
            self.fail('MongoPool._validate_config raised Type Error while '
                      'valid config was provided')

    def test_rasies_exception_for_invalid_read_preference(self):
        config = [{'label': {'host': '127.0.0.1', 'port': 27017,
                             'dbpath': '.*'}}]
        config[0]['label']['read_preference'] = 1
        with self.assertRaises(TypeError):
            MongoPool(config)
        config[0]['label']['read_preference'] = 'primary'
        try:
            MongoPool(config)
        except TypeError:
            self.fail('MongoPool._validate_config raised Type Error while '
                      'valid config was provided')

    @patch('mongopool.mongopool.pymongo.MongoClient')
    def test_creates_simple_client(self, mock_MongoClient):
        """
        Ensure that a MongoClient is created when replicaSet is not specified
        in the configurations and the correct database is returned
        """
        pool = MongoPool(self.config)
        mock = mock_MongoClient()
        db1 = pool.db1
        mock_MongoClient.assert_called_with(**self.call_arguments)
        mock.__getitem__.assert_called_once_with('db1')

    @patch('mongopool.mongopool.pymongo.MongoReplicaSetClient')
    def test_creates_mongo_replica_set_client(self, mock_MongoReplicaSetClient):
        """
        Ensure that a MongoReplicaSetClient is created when replicaSet is
        specified in the configurations and the correct database is returned
        """
        pool = MongoPool(self.config)
        mock = mock_MongoReplicaSetClient()
        db2 = pool.db2
        call_arguments = {'hosts_or_uri': '127.0.0.1:27017',
                          'replicaSet': 'rset0',
                          'safe': True,
                          'read_preference': 0,
                          'socketTimeoutMS': None}

        mock_MongoReplicaSetClient.assert_called_with(**call_arguments)
        mock.__getitem__.assert_called_once_with('db2')

    def test_exception_is_raised_when_the_database_is_not_configured(self):
        """
        Ensure that an exception is raised while trying to access a database
        which doesn't match any pattern of the configured clusters
        """
        pool = MongoPool(self.config)
        with self.assertRaisesRegexp(Exception, "No such database .*"):
            pool.inexistentdb

    @patch('mongopool.mongopool.pymongo.MongoClient')
    def test_matches_dbpaths_correctly(self, mock_MongoClient):
        """
        Ensure that dbpaths are matched in the order specified in the
        given order and a Client connecting to the first match is returned
        """
        pool = MongoPool(self.config)
        db1 = pool.dbp
        db2 = pool.dbpattern123
        db3 = pool.dbpat

        self.call_arguments['port'] = 27018
        calls = [call(**self.call_arguments)]
        self.call_arguments['port'] = 27020
        calls.append(call(**self.call_arguments))
        self.call_arguments['port'] = 27019
        calls.append(call(**self.call_arguments))

        self.assertEqual(mock_MongoClient.call_args_list, calls,
                         "Didn't retrieve the databases in the correct order")

    @patch('mongopool.mongopool.pymongo.MongoClient')
    def test_matches_dbpaths_in_array(self, mock_MongoClient):
        """
        Ensure that the correct database is returned when specifying dbpaths
        as arrays
        """
        pool = MongoPool(self.config)
        pool.arraydb9xyz
        self.call_arguments['port'] = 27021

        mock_MongoClient.assert_called_with(**self.call_arguments)

    @patch('mongopool.mongopool.pymongo.MongoClient')
    def test_uses_set_timeout(self, mock_MongoClient):
        """
        Ensure that Clients are created with the correct timeout after
        set_timeout method is called
        """
        pool = MongoPool(self.config)
        new_timeout = 5
        pool.set_timeout(new_timeout)

        db1 = pool.db1
        self.call_arguments['socketTimeoutMS'] = new_timeout

        mock_MongoClient.assert_called_with(**self.call_arguments)

    @patch('mongopool.mongopool.pymongo.MongoReplicaSetClient')
    @patch('mongopool.mongopool.pymongo.MongoClient')
    def test_recreates_clients_after_set_timeout(self, mock_MongoClient,
                                                 mock_MongoReplicaSetClient):
        """
        Ensure that all created Clients are dropped and new ones are created
        after a set_timeout call to ensure the correct timeout value is used
        """
        pool = MongoPool(self.config)
        new_timeout = 5
        db1 = pool.db1
        db2 = pool.db2
        mock_MongoClient.reset_mock()
        mock_MongoReplicaSetClient.reset_mock()
        pool.set_timeout(new_timeout)

        db1 = pool.db1
        self.call_arguments['socketTimeoutMS'] = new_timeout
        mock_MongoClient.assert_called_once_with(**self.call_arguments)

        call_arguments = {'hosts_or_uri': '127.0.0.1:27017',
                          'replicaSet': 'rset0',
                          'socketTimeoutMS': new_timeout,
                          'safe': True,
                          'read_preference': 0}
        db2 = pool.db2
        mock_MongoReplicaSetClient.assert_called_with(**call_arguments)

    @patch('mongopool.mongopool.pymongo.MongoClient')
    def test_that_connections_are_saved(self, mock_MongoClient):
        pool = MongoPool(self.config)
        db1 = pool.dbpattern1
        mock_MongoClient.reset_mock()
        db2 = pool.dbpattern2

        self.assertFalse(mock_MongoClient.called, "New connections are "
                         "created for each database access")

