import os, subprocess, getopt, sys

import config

class bcolors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def printColor(string_to_print,color):
    """Prints messages to stdout of a defined color"""
    if color== "green":
        print bcolors.OKGREEN + string_to_print + bcolors.ENDC
    elif color== "red":
        print bcolors.FAIL + string_to_print + bcolors.ENDC
    else:
        print bcolors.FAIL + "Bad color argument to print" + bcolors.ENDC

def runCommand(command, inputVal=''):
    """Run a shell command"""
    if (inputVal == ''):
       print command
    ret_code=subprocess.call(command, shell=True)
    if ret_code:
        printColor(("bad return code for command execution: %s" % ret_code), "red")
        exit()
    return ret_code

def runPriv(command, inputVal=''):
    """Run a shell command with sudo privileges"""
    realCommand = "sudo " + command
    return runCommand(realCommand, inputVal)
    

def MultiYCSB_Disk(work_dir, bench_suite, mount_dir,app):

    # ------------------
    # Initial disk Setup
    # ------------------
    printColor("", "green")
    printColor("Initial disk Setup ...", "green")
    printColor("", "green")

    # rcS file
    runPriv("chmod 777 %s/etc/init.d/rcS" % mount_dir)
    new_rcS= open(os.path.join(mount_dir, "etc/init.d/rcS"), 'w')
    new_rcS.write("#!/bin/sh \n")
    new_rcS.write("#\n")
    new_rcS.write("# rcS\n")
    new_rcS.write("#\n")
    new_rcS.write("\n")
    new_rcS.write("exec /etc/init.d/rc S\n")
    new_rcS.close()
    runPriv("chmod 755 %s/etc/init.d/rcS" % mount_dir)

    # pre-config
    # root password: "root"
    printColor("------- root passwd ------", "green")
    runPriv("chroot %s sed -i '1d' /etc/shadow" % mount_dir)
    runPriv("chroot %s sed  -i '1i root:$6$md96fW7c$mA8tDTKANrVkjByhzfQdZ5uQRSk8z19Yz5StKedkZ7e2t6dpDXelr7Nb5evtPvnAEDqS5jRUFn1kITlDfUaE0/:17492:0:99999:7:::' /etc/shadow" % mount_dir)
    printColor("--------------------------", "green")

    runPriv("rm %s/etc/apt/sources.list" % mount_dir)
    runPriv("echo \"deb http://ftp.us.debian.org/debian/ jessie main contrib non-free\" |sudo tee -a %s/etc/apt/sources.list" % mount_dir)
    runPriv("echo \"deb-src http://ftp.us.debian.org/debian/ jessie main contrib non-free\" |sudo tee -a %s/etc/apt/sources.list" % mount_dir)
    runPriv("echo \"\" |sudo tee -a %s/etc/apt/sources.list" % mount_dir)
    runPriv("echo \"deb http://security.debian.org/ jessie/updates main contrib non-free\" |sudo tee -a %s/etc/apt/sources.list" % mount_dir)
    runPriv("echo \"deb-src http://security.debian.org/ jessie/updates main contrib non-free\" |sudo tee -a %s/etc/apt/sources.list" % mount_dir)
    runPriv("echo \"\" |sudo tee -a %s/etc/apt/sources.list" % mount_dir)
    runPriv("echo \"# jessie-updates, previously known as 'volatile'\" |sudo tee -a %s/etc/apt/sources.list" % mount_dir)
    runPriv("echo \"deb http://ftp.us.debian.org/debian/ jessie-updates main contrib non-free\" |sudo tee -a %s/etc/apt/sources.list" % mount_dir)
    runPriv("echo \"deb-src http://ftp.us.debian.org/debian/ jessie-updates main contrib non-free\" |sudo tee -a %s/etc/apt/sources.list" % mount_dir)
    runPriv("echo \"\" |sudo tee -a %s/etc/apt/sources.list" % mount_dir)
    runPriv("echo \"# backports\" |sudo tee -a %s/etc/apt/sources.list" % mount_dir)
    runPriv("echo \"deb http://ftp.debian.org/debian jessie-backports main\" |sudo tee -a %s/etc/apt/sources.list" % mount_dir)
    runPriv("echo \"\" |sudo tee -a %s/etc/apt/sources.list" % mount_dir)
    runPriv("echo \"# Debian 8 Jessie\" |sudo tee -a %s/etc/apt/sources.list" % mount_dir)
    runPriv("echo \"deb http://httpredir.debian.org/debian/ jessie main contrib\" |sudo tee -a %s/etc/apt/sources.list" % mount_dir)

    runPriv("chroot %s apt-get update" % mount_dir)
    runPriv("chroot %s apt-get install -y python sysv-rc-conf ethtool vim execstack htop openssh-server git linux-tools htop iptraf wget make" % mount_dir)
    runPriv("chroot %s apt-get install -t jessie-backports -y maven" % mount_dir)

    runPriv("echo \"127.0.0.1       localhost\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.1        nodo-01\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.2        nodo-02\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.3        nodo-03\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.4        nodo-04\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.5        nodo-05\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.6        nodo-06\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.7        nodo-07\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.8        nodo-08\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.9        nodo-09\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.10       nodo-10\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.11       nodo-11\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.12       nodo-12\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.13       nodo-13\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.14       nodo-14\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.15       nodo-15\" |sudo tee -a %s/etc/hosts" % mount_dir)
    runPriv("echo \"10.0.0.15       nodo-16\" |sudo tee -a %s/etc/hosts" % mount_dir)

    # No remove /tmp on boot (launch_app.sh)
    runPriv("chroot %s sed -i 's/#TMPTIME=0/TMPTIME=-1/g' /etc/default/rcS"  % mount_dir)
    runPriv("chroot %s touch /etc/tmpfiles.d/tmp.conf" % mount_dir)
    runPriv("echo \"d /tmp 1777 root root -\" |sudo tee -a  %s/etc/tmpfiles.d/tmp.conf" % mount_dir)

    # tune networking configuration
    runPriv("echo \"\" |sudo tee -a %s/root/.bashrc" % mount_dir)
    runPriv("echo \"# Kernel Tunning\" |sudo tee -a %s/root/.bashrc" % mount_dir)
    runPriv("echo \"ulimit -n 1000000\" |sudo tee -a %s/root/.bashrc" % mount_dir)
    runPriv("echo \"ulimit -u 1000000\" |sudo tee -a %s/root/.bashrc" % mount_dir)
    runPriv("echo \"ulimit -s 524288 \" |sudo tee -a %s/root/.bashrc" % mount_dir)
    runPriv("echo \"ulimit -l unlimited\" |sudo tee -a %s/root/.bashrc" % mount_dir)
    runPriv("echo \"\" |sudo tee -a %s/root/.bashrc" % mount_dir)

    # Java HotSpot(TM) 64-Bit Serve (Oracle Java SE Runtime Environment)
    runPriv("chroot %s wget https://www.ce.unican.es/software/jdk-8u141-linux-x64.tar.gz" % mount_dir)
    runPriv("chroot %s mv jdk-8u141-linux-x64.tar.gz /tmp" % mount_dir)
    runPriv("chroot %s apt-get install -y java-package" % mount_dir)
    runPriv("chroot %s apt-get install -y libgl1-mesa-glx libgtk2.0-0 libxslt1.1 libxtst6 libxxf86vm1" % mount_dir)
    runPriv("chroot %s su - test -c \"fakeroot yes| make-jpkg /tmp/jdk-8u141-linux-x64.tar.gz\"" % mount_dir)
    runPriv("chroot %s mv /home/test/oracle-java8-jdk_8u141_amd64.deb  /tmp/" % mount_dir)
    runPriv("chroot %s dpkg -i /tmp/oracle-java8-jdk_8u141_amd64.deb" % mount_dir)
    runPriv("chroot %s update-alternatives --display java" % mount_dir)
    #Enable Oracle HotSpot Java VM
    #runPriv("chroot %s update-alternatives --set java /usr/lib/jvm/jdk-8-oracle-x64/jre/bin/java" % mount_dir)
    runPriv("chroot %s update-alternatives --auto java" % mount_dir)
    runPriv("chroot %s java -version" % mount_dir)

    # ------------------
    # gem5 utils
    # ------------------
    # gem5 launch_apps
    runPriv("mkdir -pv %s/opt/gem5/bin" % (mount_dir))
    runPriv("cp -av %s/atc_scripts/launch_apps %s/opt/gem5/" % (config.gem5_dir,mount_dir))

    runCommand("sync")

    # ------------------
    # YCSB
    # ------------------
    runPriv("cp -av %s/nosql/YCSB %s/usr/src/" % (config.gem5_dir,mount_dir))

    # ------------------
    # Cassandra
    # ------------------
    printColor("", "green")
    printColor("Cassandra disk updating  ...", "green")
    printColor("", "green")

    # Tune .bashrc (PROMPT)
    runPriv("sed -i 's/chroot/cassandra/g' %s/root/.bashrc" % mount_dir)

    # Tune kernel
    runPriv("echo \"###################################################################\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"# Cassandra tune networking configuration\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"#\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"net.core.optmem_max=67108864\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"net.core.wmem_max=67108864\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"net.core.rmem_max=67108864\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"net.core.wmem_default=67108864\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"net.core.rmem_default=67108864\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"net.core.netdev_max_backlog=300000\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"net.ipv4.tcp_max_syn_backlog=300000\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"net.ipv4.tcp_max_tw_buckets=2000000\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"net.ipv4.tcp_wmem=67108864 67108864 67108864\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"net.ipv4.tcp_rmem=10240 67108864 67108864\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"net.ipv4.tcp_mem=67108864 67108864 67108864\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"net.ipv4.tcp_window_scaling=0\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"net.ipv4.tcp_timestamps=0\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"net.ipv4.tcp_sack=0\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"net.ipv4.tcp_dsack=0\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)
    runPriv("echo \"fs.file-max=6000000\" |sudo tee -a %s/etc/sysctl.conf" % mount_dir)

    # Copy APP
    runPriv("cp -av %s/nosql/cassandra %s/opt/" % (config.gem5_dir,mount_dir))
    runPriv("mkdir %s/var/log/cassandra" % mount_dir)

    # APP debian (linux) Service
    runPriv("chroot %s cp -av /opt/cassandra/gem5/service/cassandra /etc/init.d/" % mount_dir)

    # YCSB binding compile
    runPriv("chroot %s bash -c \"cd /usr/src/YCSB && /usr/bin/mvn -pl com.yahoo.ycsb:cassandra-binding -am clean package\"" % mount_dir)
    runPriv("chroot %s mkdir /opt/YCSB" % mount_dir)
    runPriv("chroot %s bash -c \"cd /tmp && tar -zxvf /usr/src/YCSB/cassandra/target/ycsb-cassandra-binding-0.14.0-SNAPSHOT.tar.gz && mv /tmp/ycsb-cassandra-binding-0.14.0-SNAPSHOT/* /opt/YCSB/\"" % mount_dir)

    # launch_app.sh
    runPriv("chroot %s ln -sv /opt/gem5/launch_apps/NoSQL/cassandra/launch_app.sh /tmp/launch_app.sh" % mount_dir)
    runPriv("chroot %s ln -sv /opt/gem5/launch_apps/NoSQL/cassandra/launch_app-run.sh /tmp/launch_app-run.sh" % mount_dir)

    # create YCSB DB on cassandra
    runPriv("chroot %s mkdir /opt/YCSB/cassandra/" % mount_dir)
    runPriv("chroot %s touch /opt/YCSB/cassandra/ycsb.cql" % mount_dir)
    runPriv("echo \"create keyspace ycsb WITH REPLICATION = {'class' : 'SimpleStrategy', 'replication_factor': 3 };\" |sudo tee -a %s/opt/YCSB/cassandra/ycsb.cql" % mount_dir)
    runPriv("echo \"USE ycsb;\" |sudo tee -a %s/opt/YCSB/cassandra/ycsb.cql" % mount_dir)
    runPriv("echo \"create table usertable (y_id varchar primary key, field0 varchar, field1 varchar, field2 varchar, field3 varchar, field4 varchar, field5 varchar, field6 varchar, field7 varchar, field8 varchar, field9 varchar);\" |sudo tee -a %s/opt/YCSB/cassandra/ycsb.cql" % mount_dir)
    runPriv("chroot %s touch /opt/YCSB/create_db.sh" % mount_dir)
    runPriv("echo \"#!/bin/bash\" |sudo tee -a %s/opt/YCSB/create_db.sh" % mount_dir)
    runPriv("echo \"cd /opt/cassandra/\" |sudo tee -a %s/opt/YCSB/create_db.sh" % mount_dir)
    runPriv("echo \"bin/cqlsh 10.0.0.2 < /opt/YCSB/cassandra/ycsb.cql\" |sudo tee -a %s/opt/YCSB/create_db.sh" % mount_dir)
    runPriv("chroot %s chmod 755 /opt/YCSB/create_db.sh" % mount_dir)

    # load YCSB DB on cassandra
    runPriv("chroot %s touch /opt/YCSB/load.sh" % mount_dir)
    runPriv("echo \"#!/bin/bash\" |sudo tee -a %s/opt/YCSB/load.sh" % mount_dir)
    runPriv("echo \"cd /opt/YCSB\" |sudo tee -a %s/opt/YCSB/load.sh" % mount_dir)
    runPriv("echo \"python2.7 bin/ycsb load cassandra-cql -jvm-args='-Xint' -s -P workloads/workload\$1 -p hosts=\$3 -p recordcount=\$2\" |sudo tee -a %s/opt/YCSB/load.sh" % mount_dir)
    runPriv("chroot %s chmod 755 /opt/YCSB/load.sh" % mount_dir)

    # run YCSB on cassandra
    runPriv("chroot %s touch /opt/YCSB/run.sh" % mount_dir)
    runPriv("echo \"#!/bin/bash\" |sudo tee -a %s/opt/YCSB/run.sh" % mount_dir)
    runPriv("echo \"cd /opt/YCSB\" |sudo tee -a %s/opt/YCSB/run.sh" % mount_dir)
    runPriv("echo \"bin/ycsb run cassandra-cql -jvm-args='-Xint' -P workloads/workload\$1 -p hosts=\$4 -p operationcount=\$2 -threads \$3\" |sudo tee -a %s/opt/YCSB/run.sh" % mount_dir)
    runPriv("chroot %s chmod 755 /opt/YCSB/run.sh" % mount_dir)

