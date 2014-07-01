from mock import patch, call
from unittest import TestCase

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
        self.pool = MongoPool(self.config)

    @patch('mongopool.mongopool.pymongo.MongoClient')
    def test_creates_simple_client(self, mock_MongoClient):
        """
        Ensure that a MongoClient is created when replicaSet is not specified
        in the configurations and the correct database is returned
        """
        mock = mock_MongoClient()
        db1 = self.pool.db1
        mock_MongoClient.assert_called_with(**self.call_arguments)
        mock.__getitem__.assert_called_once_with('db1')

    @patch('mongopool.mongopool.pymongo.MongoReplicaSetClient')
    def test_creates_mongo_replica_set_client(self, mock_MongoReplicaSetClient):
        """
        Ensure that a MongoReplicaSetClient is created when replicaSet is
        specified in the configurations and the correct database is returned
        """
        mock = mock_MongoReplicaSetClient()
        db2 = self.pool.db2
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
        with self.assertRaisesRegexp(Exception, "No such database .*"):
            self.pool.inexistentdb

    @patch('mongopool.mongopool.pymongo.MongoClient')
    def test_matches_dbpaths_correctly(self, mock_MongoClient):
        """
        Ensure that dbpaths are matched in the order specified in the
        given order and a Client connecting to the first match is returned
        """
        db1 = self.pool.dbp
        db2 = self.pool.dbpattern123
        db3 = self.pool.dbpat

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
        self.pool.arraydb9xyz
        self.call_arguments['port'] = 27021

        mock_MongoClient.assert_called_with(**self.call_arguments)

    @patch('mongopool.mongopool.pymongo.MongoClient')
    def test_uses_set_timeout(self, mock_MongoClient):
        """
        Ensure that Clients are created with the correct timeout after
        set_timeout method is called
        """
        new_timeout = 5
        self.pool.set_timeout(new_timeout)

        db1 = self.pool.db1
        self.call_arguments['socketTimeoutMS'] = new_timeout

        mock_MongoClient.assert_called_with(**self.call_arguments)

    @patch('mongopool.mongopool.pymongo.MongoReplicaSetClient')
    @patch('mongopool.mongopool.pymongo.MongoClient')
    def test_recreates_clients_after_set_timeout(self, mock_MongoClient, mock_MongoReplicaSetClient):
        """
        Ensure that all created Clients are dropped and new ones are created
        after a set_timeout call to ensure the correct timeout value is used
        """
        new_timeout = 5
        db1 = self.pool.db1
        db2 = self.pool.db2
        mock_MongoClient.reset_mock()
        mock_MongoReplicaSetClient.reset_mock()
        self.pool.set_timeout(new_timeout)

        db1 = self.pool.db1
        self.call_arguments['socketTimeoutMS'] = new_timeout
        mock_MongoClient.assert_called_once_with(**self.call_arguments)

        call_arguments = {'hosts_or_uri': '127.0.0.1:27017',
                          'replicaSet': 'rset0',
                          'socketTimeoutMS': new_timeout,
                          'safe': True,
                          'read_preference': 0}
        db2 = self.pool.db2
        mock_MongoReplicaSetClient.assert_called_with(**call_arguments)
