#!/bin/bash
mkdir -p databases/label1 databases/label2 databases/label4 databases/rset0-0 databases/rset0-1 databases/rset0-2

mongod --port 27017 --dbpath /tmp/label1 --smallfiles --oplogSize 128 > /dev/null &
mongod --port 27018 --dbpath /tmp/label2 --smallfiles --oplogSize 128 > /dev/null &
mongod --port 27022 --dbpath /tmp/label4 --smallfiles --oplogSize 128 > /dev/null &
mongod --port 27019 --dbpath /tmp/databases/rset0-0 --replSet rset0 --smallfiles \
       --oplogSize 128 > /dev/null &
mongod --port 27020 --dbpath /tmp/databases/rset0-1 --replSet rset0 --smallfiles \
       --oplogSize 128 > /dev/null &
mongod --port 27021 --dbpath /tmp/databases/rset0-2 --replSet rset0 --smallfiles \
       --oplogSize 128 > /dev/null &

mongo_commands="rsconf = { _id: \"rset0\", members: [{\"_id\": 0,\"host\": \
\"127.0.0.1:27019\"}, {\"_id\": 1, \"host\": \"127.0.0.1:27020\"}, \
{\"_id\": 2, \"host\": \"127.0.0.1:27021\"}]} \nrs.initiate(rsconf)"
echo -e $mongo_commands | mongo --port 27019 > /dev/null

