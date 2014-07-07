#!/bin/bash
ports=(27017 27018 27019 27020 27021 27022)
for port in ${ports[@]}; do
    databases=$(echo -e "show databases" | mongo --port $port | cut -f1);
    for db in ${databases[@]}; do
        if [[ $db == mpool* ]]; then
            echo -e "use $db\ndb.dropDatabase()" | mongo --port $port > /dev/null
        fi
    done
    echo -e "use admin\n db.shutdownServer()" | mongo --port $port > /dev/null
done
rm -r databases
