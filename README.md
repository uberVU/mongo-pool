MongoPool
=========
##Description

MongoPool is a tool that manages your mongo clients to different clusters, maps databases to clients and allows you to work only with database names without worrying about creating and managing connections.

##Install

 - .
 - .
 
##Usage
All you have to do in order to get started is to build a list of dictionaries which contains the neccessary information to connect to the clusters, instantiate MongoPool and access databases through dot notation. 
```python
>>> from mongopool import MongoPool
>>> 
>>> config = [{'cluster1': {'host': '127.0.0.1', 'port': 27017, 'dbpath': 'blogs'}},
...           {'cluster2': {'host': '127.0.0.1', 'port': 27018, 'dbpath': 'posts'}}]
>>> mongopool = MongoPool(config)
>>> blogs = mongopool.blogs
>>> blogs
Database(MongoClient('127.0.0.1', 27017), u'blogs')
>>> posts = mongopool.posts
>>> posts
Database(MongoClient('127.0.0.1', 27018), u'posts')
```

But what if you want to work with multiple databases on the same cluster?
You can specify the dbpath as an array containing the database names as in the following example:
```python
>>> from mongopool import MongoPool
>>>
>>> config = [{'cluster1': {'host': '127.0.0.1', 'port': 27017, 'dbpath': ['blogs', 'posts']}}]
>>> mongopool = MongoPool(config)
>>> blogs = mongopool.blogs
>>> blogs
Database(MongoClient('127.0.0.1', 27017), u'blogs')
>>> posts = mongopool.posts
>>> posts
Database(MongoClient('127.0.0.1', 27017), u'posts')
```
You might have databases created automatically, following a certain naming pattern. In this case, it would be impossible to add all databases on a cluster in dbpath. For this reason, you can pass it as a regexp pattern. Let's say that you save the comments in a separate database for each month, named comments_monthyear:
```python
>>> from mongopool import MongoPool
>>> 
>>> config = [{'cluster1': {'host': '127.0.0.1', 'port': 27017, 'dbpath': 'comments_\d*'}}]
>>> mongopool = MongoPool(config)
>>> jan_comments = mongopool.comments_012014
>>> jan_comments
Database(MongoClient('127.0.0.1', 27017), u'comments_012014')
>>> march_comments = mongopool.comments_032014
>>> march_comments
Database(MongoClient('127.0.0.1', 27017), u'comments_032014')
```

**Caution**: this is a strong feature, but it should be used with attention. Dbpaths will be matched in the order you put them in the configurations tlist, so make sure you order them from the most particular to the most general to avoid mapping too many databases on a single cluster.

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

MongoPool also manages connections to ReplicaSets. All you have to do is to add the name of the replica set in configuration. Also, if you want a read_preference different from PRIMARY, you can specify it in the config.
```python
>>> from mongopool import MongoPool
>>> 
>>> config = [{'cluster1': {'host': '127.0.0.1', 'port': 27018, 'replicaSet': 'rset0',
...                         'read_preference': 'secondary','dbpath': 'blogs'}}]
>>> mongopool = MongoPool(config)
>>> blogs = mongopool.blogs
>>> blogs
Database(MongoReplicaSetClient([u'127.0.0.1:27019', u'127.0.0.1:27020', u'127.0.0.1:27018']), u'blogs')
```

By default, MongoClient and MongoReplicaSetClient do not have a timeout set, though sometimes it is handy. To set a timeout for you connection you can either pass it as a second argument while instantiating MongoPool or use the set_timeout method which will recreate all connections with the new timeout and create all new connections with the new value.
```python
mongopool = MongoPool(config, 2)
...
mongopool.set_timeout(5)
```
