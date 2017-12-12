#!/bin/bash
## author: herreroja@unican.es
## Usage: launch_app.sh $num_nodes $app $DB_size $num_threads
## launching script for CASSANDRA
#
# app --> YCSB workload class to use {a,b,c,d,e,f,...}
# db_size --> number of records to load into the database initially (default: 0)
# num_threads --> number of YCSB client threads. Alternatively this may be specified on the command line. (default: 1)

args=("$@")

NUM_NODES=${args[0]}
APP=${args[1]}
SIZE_DB=${args[2]}
TH=${args[3]}

IP=`ifconfig eth0|grep "inet addr:"|awk '{ print \$2 }' |sed "s/:/ /g" |awk '{ print \$2 }'`
TOKEN=`expr 3074457345618258602 + $(( ( RANDOM % 100 )  + 1 ))`

name=`hostname`

function run_cassandra {
	echo "==========================================================="
	echo "[cassandra]: STARTING service cassandra on ($name) ..."
	echo
	systemctl start cassandra
	echo
	echo "[cassandra]: done!"
	systemctl status cassandra
	echo "==========================================================="
	echo
}

function run_ycsb {
	echo "==========================================================="
	echo "[ycsb-load]: WAITING for cassandra to be ready: 180 s ..."
	sleep 180
	echo "[ycsb-load]: done!"
	cd /opt/YCSB
	echo "[ycsb-load]: CREATING ycsb database on cassandra ($name) ..."
	./create_db.sh
	echo "[ycsb-load]: done!"
	echo "[ycsb-load]: LOADING database on cassandra ($name) ..."
	./load.sh $APP $SIZE_DB $SERVER
	echo "[ycsb-load]: done!"
	/sbin/m5 exit
	echo "loading launch_app-run.sh ..."
	/sbin/m5 readfile > /tmp/script2
	chmod 755 /tmp/script2
	echo "[ycsb-run]: RUNNING ycsb --> cassandra ... ($name)"
	exec su root -c '/tmp/script2'
	echo "[ycsb-run]: Error in exec script-run!"
	/sbin/m5 exit
	echo "==========================================================="
}

# Main
if [ "$NUM_NODES" == "1" ]
then
	SERVER="10.0.0.1"
    sed -i "s/seeds: \"127.0.0.1\"/seeds: \"$SERVER\"/g" /opt/cassandra/conf/cassandra.yaml
	run_cassandra
	run_ycsb
else
	SERVER="10.0.0.2"
	if [ "$name" == "nodo-01" ]
	then
		run_ycsb
	else
		sed -i "s/seeds: \"127.0.0.1\"/seeds: \"10.0.0.2\"/g" /opt/cassandra/conf/cassandra.yaml
		sed -i "s/listen_address: 10.0.0.1/listen_address: $IP/g" /opt/cassandra/conf/cassandra.yaml
		sed -i "s/rpc_address: 10.0.0.1/rpc_address: $IP/g" /opt/cassandra/conf/cassandra.yaml
		if [ "$name" != "nodo-02" ]
		then
			echo "[cassandra]: RE-configurating service cassandra ($name) ..."
			sed -i "s/initial_token: 0/initial_token: $TOKEN/g" /opt/cassandra/conf/cassandra.yaml
		fi
		run_cassandra
		sleep 365d
	fi
fi
