#!/bin/bash
## author: herreroja@unican.es
## Usage: launch_app-run.sh $num_nodes $app $DB_size $num_threads $app_size 
## launching script for CASSANDRA
#
# app --> YCSB workload class to use {a,b,c,d,e,f,...}
# db_size --> number of records to load into the database initially (default: 0)
# num_threads --> number of YCSB client threads. Alternatively this may be specified on the command line. (default: 1)
# app_size --> number of operations to perform

args=("$@")

NUM_NODES=${args[0]}
APP=${args[1]}
SIZE_DB=${args[2]}
TH=${args[3]}
#SIZE_APP=$(getSize ${args[4]})
SIZE_APP=${args[4]}

# Main
if [ "$NUM_NODES" == "1" ]
then
        SERVER="10.0.0.1"
else
        SERVER="10.0.0.2"
fi
cd /opt/YCSB
./run.sh $APP $SIZE_APP $TH $SERVER
echo "[ycsb-run]: done!"
/sbin/m5 exit