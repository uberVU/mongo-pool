import yaml
from mock import patch, call
from unittest import TestCase
import pymongo

from mongopool import MongoPool

class MongoPoolTestCase(TestCase):
    def setUp(self):
        self.config = [{'label1': {'host': '127.0.0.1', 'port': 27017, 'dbpath': 'db1'}},
                       {'label2': {'host': '127.0.0.1', 'port': 27017, 'dbpath': 'db2',
                        'replica_set': 'rset0'}},
                       {'label3': {'host': '127.0.0.1', 'port': 27018, 'dbpath': 'dbp'}},
                       {'label4': {'host': '127.0.0.1', 'port': 27019, 'dbpath': 'dbpat'}},
                       {'label5': {'host': '127.0.0.1', 'port': 27020, 'dbpath': 'dbpattern\d*'}},
                       {'label6': {'host': '127.0.0.1', 'port': 27021,
                        'dbpath': ['arraydb1', 'arraydb2', 'arraydb\dxyz']}}]
        self. call_arguments = {'host': '127.0.0.1', 'port': 27017, 'safe':True,
                                'read_preference': 0, 'socketTimeoutMS': None}
        self.pool = MongoPool(self.config)

    def tearDown(self):
        self.pool.__metaclass__._instances = {}

    @patch('mongopool.pymongo.MongoClient')
    def test_creates_simple_connection(self, mock_MongoClient):
        db = self.pool.db1

        mock_MongoClient.assert_called_with(**self.call_arguments)

    @patch('mongopool.pymongo.MongoReplicaSetClient')
    def test_creates_mongo_replica_set_client(self, mock_MongoReplicaSetClient):
        db = self.pool.db2
        call_arguments = {'hosts_or_uri': '127.0.0.1:27017', 'safe': True, 
                       'read_preference': 0, 'socketTimeoutMS': None,
                       'replicaSet': 'rset0'}

        mock_MongoReplicaSetClient.assert_called_with(**call_arguments)

    def test_exception_is_raised_when_the_database_is_not_configured(self):
        with self.assertRaisesRegexp(Exception, "No such database .*"):
            self.pool.inexistentdb

    @patch('mongopool.pymongo.MongoClient')
    def test_matches_dbpaths_correctly(self, mock_MongoClient):
        db1 = self.pool.dbp
        db3 = self.pool.dbpattern123
        db2 = self.pool.dbpat
        self.call_arguments['port'] = 27018
        calls = [call(**self.call_arguments)]
        self.call_arguments['port'] = 27020
        calls.append(call(**self.call_arguments))
        self.call_arguments['port'] = 27019
        calls.append(call(**self.call_arguments))

        self.assertEqual(mock_MongoClient.call_args_list, calls,
                         "Didn't retrieve the databases in the correct order")

    @patch('mongopool.pymongo.MongoClient')
    def test_matches_dbpaths_in_array(self, mock_MongoClient):
        db = self.pool.arraydb9xyz
        self.call_arguments['port'] = 27021

        mock_MongoClient.assert_called_with(**self.call_arguments)

    @patch('mongopool.pymongo.MongoClient')
    def test_uses_set_timeout(self, mock_MongoClient):
        new_timeout = 5
        self.pool.set_timeout(new_timeout)
        
        db1 = self.pool.db1
        self.call_arguments['socketTimeoutMS'] = new_timeout
        
        mock_MongoClient.assert_called_with(**self.call_arguments)

    @patch('mongopool.pymongo.MongoReplicaSetClient')
    @patch('mongopool.pymongo.MongoClient')
    def test_recreates_clients_after_set_timeout(self, mock_MongoClient, mock_MongoReplicaSetClient):
        new_timeout = 5
        db1 = self.pool.db1
        db2 = self.pool.db2
        mock_MongoClient.reset_mock()
        mock_MongoReplicaSetClient.reset_mock()
        self.pool.set_timeout(new_timeout)

        db1 = self.pool.db1
        self.call_arguments['socketTimeoutMS'] = new_timeout
        mock_MongoClient.assert_called_with(**self.call_arguments)

        call_arguments = {'hosts_or_uri': '127.0.0.1:27017', 'safe': True, 
                       'read_preference': 0, 'socketTimeoutMS': new_timeout,
                       'replicaSet': 'rset0'}
        db2 = self.pool.db2
        mock_MongoReplicaSetClient.assert_called_with(**call_arguments)
