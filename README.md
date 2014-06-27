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
You might have databases created automatically, following a certain naming pattern. In this case, it would be impossible to add all databases on a cluster in dbpath. For this reason, you can specify it as a regexp pattern. Let's say that you save the comments in a separate database for each month, named comments_monthyear:
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



You can also work with datasests in this way by adding the replica_set key in the dictionary.
```
configs = [{'label1': {'host': '127.0.0.1', 'port': 27017, 'dbpath': 'db1',
                       'replica_set': 'rset0', 'read_preference': 'SECONDARY'}}]
                       ]
```
**Caution**: dbpaths will be matched in the order you provide them in the configs, make sure that you put them in order from the most particular to the most general to avoid creating wrong mappings between databases and clusters.
