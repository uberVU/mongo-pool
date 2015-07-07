![image](https://cloud.githubusercontent.com/assets/250750/5323889/4f7cf454-7cdd-11e4-81f0-7e3eee8f9556.png)

### _All your mongos in one place_ 
[![Build Status](https://travis-ci.org/uberVU/mongo-pool.svg?branch=master)](https://travis-ci.org/uberVU/mongo-pool)

- [Description](#description)
- [Install](#install)
- [Usage](#usage)
  - [Basic Example](#basic-example)
  - [Multiple databases on the same cluster](#multiple-databases-on-the-same-cluster)
  - [Dynamic paths](#dynamic-paths)
  - [Setting a timeout](#setting-a-timeout)
  - [Custom connection classes support](#custom-connection-classes-support)
- [Setting it up](#setting-it-up)

##Description
MongoPool is the tool that manages your connections to different clusters, maps databases to clients and allows you to work only with database names without worrying about creating and managing connections.

You will never have to create a MongoClient everywhere you want to access a database again which enables you to write beautiful and maintainable code. Using MongoPool, you will keep connection regarding information in a single place and allows you to easily modify it when needed.

At UberVU, we are confidently using it to manage over 25 mongo instances to provide quality services to our customers.
## Install

### PyPi
```bash
$ sudo pip install mongopool
```
### Manual
```bash
$ git clone https://github.com/uberVU/mongo-pool
$ cd mongo-pool
$ sudo python setup.py install
```

## Usage

#### Basic example
All you have to do in order to get started is to build a list of dictionaries which contains the necessary information to connect to the clusters, instantiate MongoPool and access databases through dot notation.
```python
>>> config = [{'cluster1': {'host': '127.0.0.1', 'port': 27017, 'dbpath': 'blogs'}},
...           {'cluster2': {'host': '127.0.0.1', 'port': 27018, 'dbpath': 'posts'}}]
>>> mongopool = MongoPool(config)
>>> mongopool.blogs
Database(MongoClient('127.0.0.1', 27017), u'blogs')
>>> mongopool.posts
Database(MongoClient('127.0.0.1', 27018), u'posts')
```

#### Multiple databases on the same cluster
But what if you want to work with multiple databases on the same cluster?
You can specify the dbpath as an array containing the database names as in the following example:
```python
>>> config = [{'cluster1': {'host': '127.0.0.1', 'port': 27017, 'dbpath': ['blogs', 'posts']}}]
>>> mongopool = MongoPool(config)
>>> mongopool.blogs
Database(MongoClient('127.0.0.1', 27017), u'blogs')
>>> mongopool.posts
Database(MongoClient('127.0.0.1', 27017), u'posts')
```

#### Dynamic paths
You might have databases created automatically, following a certain naming pattern. In this case, it would be impossible to add all databases on a cluster in dbpath. For this reason, you can pass it as a regexp pattern. Let's say that you save the comments in a separate database for each month, named comments_monthyear:
```python
>>> config = [{'cluster1': {'host': '127.0.0.1', 'port': 27017, 'dbpath': 'comments_\d*'}}]
>>> mongopool = MongoPool(config)
>>> mongopool.comments_012014
Database(MongoClient('127.0.0.1', 27017), u'comments_012014')
>>> mongopool.comments_032014
Database(MongoClient('127.0.0.1', 27017), u'comments_032014')
```

**Caution**: This is a strong feature, but it should be used carefully. Dbpaths will be matched in the order you put them in the configurations list, so make sure you order them from the most particular to the most general in order to avoid creating incorrect mappings and connect to the wrong cluster.

**Wrong**
```python
config = [{'cluster1': {'host': '127.0.0.1', 'port': 27017, 'dbpath': '.*'}},
          {'cluster2': {'host': '127.0.0.1', 'port': 27017, 'dbpath': ['blogs', 'comments'}}]
```
**Correct**
```python
config = [{'cluster1': {'host': '127.0.0.1', 'port': 27017, 'dbpath': ['blogs', 'comments'}},
          {'cluster2': {'host': '127.0.0.1', 'port': 27017, 'dbpath': '.*'}}]
```
#### Setting a timeout
By default, MongoClient does not have a timeout set, though sometimes it is handy. To set a timeout for you connection you can either pass it as a second argument while instantiating MongoPool or use the set_timeout method which will recreate all connections with the new timeout and create all new connections with the new value.
```python
mongopool = MongoPool(config, network_timeout=2)
...
mongopool.set_timeout(network_timeout=5)
```

#### Custom connection classes support
If you want to use your custom connection classes instead of MongoClient you can do this by passing the optional argument: connection_class.
```python
mongopool = MongoPool(config, connection_class=MyClass)
```
## Setting it up
Along with the project we provide a sample config file to easily get started. In order to work with it, you have to launch multiple mongod instances on different ports. For this purpose, you can run the **start_instances.sh** script. If you don't wish to open many mongod instances, you can change all port values in the config file to 27017 and delete **label3** entry which uses a replicaSet.
```bash
# make sure that you are in the mongopool main directory
$ cd mongo-pool
# run the provided script or modify sample_config.yml file
$ ./start_instances.sh
$ python
```
And then run the following commands:
```python
import os
import yaml
from mongo-pool import MongoPool

filename = os.path.join(os.getcwd(), 'sample_config.yml')
options = yaml.load(open(filename))
config = options['mongopool']
pool = MongoPool(config)
```
Now you should have a working mongopool instance which you can play with.
When you are done, run:
```bash
./clean_instances.sh
```
This will ensure that all created databases are deleted and all mongod instances are shutdown
