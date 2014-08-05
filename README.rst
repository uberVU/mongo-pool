MongoPool
=========

*All your mongos in one place*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  `Description`_
-  `Install`_
-  `Usage`_
-  `Basic Example`_
-  `Multiple databases on the same cluster`_
-  `Dynamic paths`_
-  `Connecting to a replicaSet`_
-  `Setting a timeout`_
-  `Custom connection classes support`_
-  `Setting it up`_


Description
-----------

MongoPool is the tool that manages your connections to different
clusters, maps databases to clients and allows you to work only with
database names without worrying about creating and managing connections.

You will never have to create a MongoClient everywhere you want to
access a database again which enables you to write beautiful and
maintainable code. Using MongoPool, you will keep connection regarding
information in a single place and allows you to easily modify it when
needed.

At UberVU, we are confidently using it to manage over 25 mongo instances
to provide quality services to our customers. ## Install

Install
-------

PyPi
----

.. code:: bash

  $ sudo pip install mongo-pool

Manual
------

.. code:: bash

    $ git clone https://github.com/uberVU/mongo-pool
    $ cd mongo-pool
    $ sudo python setup.py install

Usage
~~~~~

Basic example
-------------

All you have to do in order to get started is to build a list of
dictionaries which contains the necessary information to connect to the
clusters, instantiate MongoPool and access databases through dot
notation.

.. code:: python

  >>> config = [{'cluster1': {'host': '127.0.0.1', 'port': 27017, 'dbpath':'blogs'}}, 
  ...           {'cluster2': {'host': '127.0.0.1', 'port': 27018, 'dbpath': 'posts'}}] 
  >>> mongopool = MongoPool(config)
  >>> mongopool.blogs
  Database(MongoClient('127.0.0.1', 27017), u'blogs')
  >>> mongopool.posts
  Database(MongoClient('127.0.0.1', 27018), u'posts')

Multiple databases on the same cluster
--------------------------------------

But what if you want to work with multiple databases on the same
cluster? You can specify the dbpath as an array containing the database
names as in the following example:

.. code:: python

  >>> config = [{'cluster1': {'host': '127.0.0.1', 'port': 27017, 'dbpath': ['blogs', 'posts']}}] 
  >>> mongopool = MongoPool(config)
  >>> mongopool.blogs
  Database(MongoClient('127.0.0.1', 27017), u'blogs')
  >>> mongopool.posts
  Database(MongoClient('127.0.0.1', 27017), u'posts')``

Dynamic paths
-------------

You might have databases created automatically, following a certain
naming pattern. In this case, it would be impossible to add all
databases on a cluster in dbpath. For this reason, you can pass it as a
regexp pattern. Let's say that you save the comments in a separate
database for each month, named comments\_monthyear:

.. code:: python

  >>> config = [{'cluster1': {'host': '127.0.0.1', 'port': 27017, 'dbpath': 'comments_\d*'}}] 
  >>> mongopool = MongoPool(config)
  >>> mongopool.comments_012014
  Database(MongoClient('127.0.0.1', 27017), u'comments_012014')
  >>> mongopool.comments_032014
  Database(MongoClient('127.0.0.1', 27017), u'comments_032014')``

**Caution**: This is a strong feature, but it should be used carefully.
Dbpaths will be matched in the order you put them in the configurations
list, so make sure you order them from the most particular to the most
general in order to avoid creating incorrect mappings and connect to the
wrong cluster.

Wrong
^^^^^

.. code:: python

  config = [{'cluster1': {'host': '127.0.0.1', 'port': 27017, 'dbpath': '.*'}},           
            {'cluster2': {'host': '127.0.0.1', 'port': 27017, 'dbpath': ['blogs', 'comments'}}]

Correct
^^^^^^^

.. code:: python

  config = [{'cluster1': {'host': '127.0.0.1', 'port': 27017, 'dbpath': ['blogs', 'comments'}},
            {'cluster2': {'host': '127.0.0.1', 'port': 27017, 'dbpath': '.*'}}]

Connecting to a replicaSet
--------------------------

MongoPool also manages connections to ReplicaSets. All you have to do is to add the name of the replica set in the configuration. Also, if you want a read\_preference different from PRIMARY, you can specify it in the config.

.. code:: python

  >>> config = [{'cluster1': {'host': '127.0.0.1', 'port': 27018, 'replicaSet': 'rset0', 
  ...'read_preference': 'secondary','dbpath': 'blogs'}}]
  >>> mongopool = MongoPool(config)
  >>> mongopool.blogs    Database(MongoReplicaSetClient([u'127.0.0.1:27019', u'127.0.0.1:27020', u'127.0.0.1:27018']), u'blogs')

Setting a timeout
-----------------
By default, MongoClient and MongoReplicaSetClient do not have a timeout set, though sometimes it is handy. To set a timeout for you connection you can either pass it as a second argument while instantiating MongoPool or use the set\_timeout method which will
recreate all connections with the new timeout and create all new
connections with the new value.

.. code:: python

  mongopool = MongoPool(config, network_timeout=2)
  ...
  mongopool.set_timeout(network_timeout=5)

Custom connection classes support
---------------------------------

If you want to use your custom connection classes instead of MongoClient and MongoReplicaSetClient, you can do this by passing 2 optional arguments: connection\_class and rset\_connection\_class.

.. code:: python

  mongopool = MongoPool(config, connection_class=MyClass, rset_connection_class=MyOther(Class)

Setting it up
~~~~~~~~~~~~~

Along with the project we provide a sample config file to easily get started. In order to work with it, you have to launch multiple mongod instances on different ports. For this purpose, you can run the **start\_instances.sh** script. If you don't wish to open many mongod instances, you can change all port values in the config file to 27017 and delete **label3** entry which uses a replicaSet.

.. code:: bash

  # make sure that you are in the mongo-pool main directory
  $ cd mongo-pool
  # run the provided script or modify sample_config.yml file
  $ ./start_instances.sh $ python

And then run the following commands:

.. code:: python

  python import os import yaml
  from mongo-pool import MongoPool

  filename = os.path.join(os.getcwd(), 'sample\_config.yml')
  options = yaml.load(open(filename))
  config = options['mongopool']
  pool = MongoPool(config)

Now you should have a working mongopool instance which you can play with. When you are done, run:

.. code:: bash

  $ ./clean\_instances.sh

This will ensure that all created databases are deleted and all mongod instances are shutdown.
