#!/usr/bin/python
#
# create_disk_img.py
#
# Script for creating a baseline gem5 disk image. I am a python
# beginner, so many things might not be optimally coded. Any
# kind of suggestion is highly welcomed, please make use of
# mercurial repository to track script modifications
#

import os, subprocess, getopt
import sys
from utils import *
import config

#################################################################
## General definitions, please change paths and names to the
## appropiate ones for your image and gem5 location
#################################################################
disk_path = config.disks_dir
gem5_dir = config.gem5_dir
disk_name = "x86_debian-jessie.img"
disk_size = 16384 ##in MB

################################################################
## DISK CREATION
################################################################

## Debian jessie
printColor(("creating scratch dir to generate img: %s" % disk_path), "green")
if not os.path.exists(disk_path):
    os.mkdir(disk_path)
os.chdir(disk_path)
printColor("done.", "green")

printColor(("creating empty image of size: %dMb" % disk_size), "green")
if not os.path.isfile(disk_name):
    runCommand("%s/gem5img.py init %s %d" % (os.path.join(gem5_dir, "util"), disk_name, disk_size))
printColor("done.", "green")

printColor("Mounting empty image", "green")
if not os.path.exists(os.path.join(disk_path, "temp")):
    os.mkdir(os.path.join(disk_path, "temp"))
if not os.path.exists(os.path.join(disk_path, "temp/lost+found")):
    runPriv("mount -o loop,offset=32256 %s temp/" % disk_name)
printColor("done.", "green")

printColor("Installing debian inside disk image", "green")
runPriv("debootstrap --arch=amd64 jessie temp/")
printColor("done.", "green")

printColor("Adding a non-root user", "green")
runPriv("chroot temp useradd -d /home/test -m test")

printColor("done.", "green")

## customing 
os.chdir(disk_path)
printColor("Updating image content ...", "green")
runPriv("cp /etc/DIR_COLORS temp/etc/")
runPriv("cp /etc/profile.d/colorls.* temp/etc/profile.d/")

## resolv.conf file
runPriv("echo \"nameserver 193.144.193.11\" |sudo tee -a temp/etc/resolfv.conf")

## hostname file
runPriv("sed -i 's/^.*$/debian/g' temp/etc/hostname")

## m5 tool
runPriv("sed -i 's/JDK_PATH=\/tmp\/java\//JDK_PATH=\/usr\/java\/jdk1.8.0_111/g' %s/util/m5/Makefile.x86" % gem5_dir)
runPriv("bash -c \"export LIBRARY_PATH=/usr/lib/x86_64-linux-gnu && cd %s/util/m5/ && make -f Makefile.x86 m5\"" % gem5_dir)
runPriv("cp %s/util/m5/m5 temp/sbin/" % gem5_dir)

## fstab file
print " -- Creating /etc/fstab "
runPriv("chmod 666 temp/etc/fstab")
new_fstab= open(os.path.join(disk_path, "temp/etc/fstab"), 'w')
new_fstab.write("proc           /proc        proc     nosuid,noexec,nodev 0     0\n")
new_fstab.write("sysfs          /sys         sysfs    nosuid,noexec,nodev 0     0\n")
new_fstab.write("tmpfs          /run         tmpfs    defaults            0     0\n")
new_fstab.write("devtmpfs       /dev         devtmpfs mode=0755,nosuid    0     0\n")
new_fstab.write("devpts         /dev/pts     devpts   gid=5,mode=620      0     0\n")
new_fstab.close()
runPriv("chmod 644 temp/etc/fstab")

# /etc/rc.local file (automatic network configuration) 
print " -- Creating /etc/rc.local"
runPriv("rm -frv temp/etc/rc.local")
runPriv("touch temp/etc/rc.local")
runPriv("chmod 777 temp/etc/rc.local")
new_starter= open(os.path.join(disk_path, "temp/etc/rc.local"), 'w')
new_starter.write("#!/bin/sh -e\n")
new_starter.write("\n")
new_starter.write("# Variable hostname\n")
new_starter.write("eths=`ifconfig -a |grep eth|wc -l`\n")
new_starter.write('if [ "$eths" -gt "0" ]\n')
new_starter.write("then\n")
new_starter.write("    MAC=`ethtool -P eth0 |awk '{print $3}'`\n")
new_starter.write("    hostname nodo-${MAC##*:}\n")
new_starter.write("    echo nodo-${MAC##*:} > /etc/hostname\n")
new_starter.write("else\n")
new_starter.write("    hostname nodo-01\n")
new_starter.write("    echo nodo-01 > /etc/hostname\n")
new_starter.write("fi\n")
new_starter.write("\n")
new_starter.write("# Networking\n")
new_starter.write("ifconfig lo up\n")
new_starter.write('if [ "$eths" -gt "0" ]\n')
new_starter.write("then\n")
new_starter.write("    AUX=`echo ${MAC##*:} |cut -c1`\n")
new_starter.write('    if [ "$AUX" != "0" ]\n')
new_starter.write("    then\n")
new_starter.write("        IP=`echo ${MAC##*:}`\n")
new_starter.write("    else\n")
new_starter.write("        IP=`echo ${MAC##*:} |cut -c2-2`\n")
new_starter.write("    fi\n")
new_starter.write("    ifconfig eth0 10.0.0.$IP\n")
new_starter.write("fi\n")
new_starter.write("\n")
new_starter.write("\n")
new_starter.write("date --set 2017-01-01\n")
new_starter.write("\n")
new_starter.write("exit 0\n")
new_starter.close()
runPriv("chmod 755 temp/etc/rc.local")

## starter file (gem5 custom script starter)
print " -- Creating /etc/systemd/system/starter.service"
runPriv("touch temp/etc/systemd/system/starter.service")
runPriv("chmod 777 temp/etc/systemd/system/starter.service")
new_systemD= open(os.path.join(disk_path, "temp/etc/systemd/system/starter.service"), 'w')
new_systemD.write("[Unit]\n")
new_systemD.write("\n")
new_systemD.write("Description=Script starter\n")
new_systemD.write("After=getty.target\n")
new_systemD.write("After=systemd-update-utmp.service\n")
new_systemD.write("After=runlevel1.target runlevel2.target runlevel3.target runlevel4.target runlevel5.target\n")
new_systemD.write("Conflicts=getty@tty1.service\n")
new_systemD.write("\n")
new_systemD.write("[Service]\n")
new_systemD.write("Type=oneshot\n")
new_systemD.write("RemainAfterExit=yes\n")
new_systemD.write("ExecStart=/opt/starter.sh\n")
new_systemD.write("StandardInput=tty-force\n")
new_systemD.write("StandardOutput=inherit\n")
new_systemD.write("StandardError=inherit\n")
new_systemD.write("\n")
new_systemD.write("[Install]\n")
new_systemD.write("WantedBy=graphical.target\n")
new_systemD.close()
runPriv("chmod 644 temp/etc/systemd/system/starter.service")
print " -- Creating /opt/starter.sh"
runPriv("touch temp/opt/starter.sh")
runPriv("chmod 777 temp/opt/starter.sh")
new_starter= open(os.path.join(disk_path, "temp/opt/starter.sh"), 'w')
new_starter.write("#!/bin/bash \n")
new_starter.write("\n")
new_starter.write("# Pre-Gem5\n")
new_starter.write("#cp -a /opt/launch_apps/launch* /tmp\n")
new_starter.write("\n")
new_starter.write("# Gem5\n")
new_starter.write('echo "loading script..."\n')
new_starter.write("/sbin/m5 readfile > /tmp/script\n")
new_starter.write("chmod 755 /tmp/script\n")
new_starter.write("if [ ! -e /lib/modules/`uname -r`/modules.dep ]\n")
new_starter.write("then\n")
new_starter.write("  mkdir -p /lib/modules/`uname -r`\n")
new_starter.write('  echo "#No modules for this run of Gem5" > /lib/modules/`uname -r`/modules.dep\n')
new_starter.write("fi\n")
new_starter.write("if [ -s /tmp/script ]; then\n")
new_starter.write("    exec su root -c '/tmp/script' # gives script full privileges as root user in multi-user mode\n")
new_starter.write("    exit 0\n")
new_starter.write("else\n")
new_starter.write('    echo "Script from M5 readfile is empty, starting bash shell..."\n')
new_starter.write("    #exec /sbin/getty -L ttySA0 38400 vt100 # login prompt\n")
new_starter.write("fi\n")
new_starter.write("\n")
new_starter.write('echo "Script from M5 readfile is empty, starting bash shell..."\n')
new_starter.write("#/bin/bash\n")
new_starter.write("#source /root/.bashrc \n")
new_starter.write("exit 0 \n")
new_starter.close()
runPriv("chmod 755 temp/opt/starter.sh")
runPriv("mkdir temp/etc/systemd/system/graphical.target.wants")
runPriv("chroot temp ln -s /lib/systemd/system/starter.service /etc/systemd/system/graphical.target.wants/starter.service")

## .bashrc file
print " -- Creating personalization (root) files "
runPriv("chmod 777 temp/root/")
runPriv("chmod 666 temp/root/.bashrc")
new_bashrc= open(os.path.join(disk_path, "temp/root/.bashrc"), 'w')
new_bashrc.write('export PATH=$PATH:/root/bin/ \n') 
new_bashrc.write('# Shell colours (after installing GNU coreutils)ml colors \n')
new_bashrc.write(' NM="\[\033[0;38m\]" #means no background and white lines \n')
new_bashrc.write(' HI="\[\033[0;37m\]" #change this for letter colors \n')
new_bashrc.write(' HII="\[\033[0;94m\]" #change this for letter colors  \n')
new_bashrc.write(' SI="\[\033[0;33m\]" #this is for the current directory\n')
new_bashrc.write(' IN="\[\033[0m\]"  \n')
new_bashrc.write(' export PS1="$NM[ $HI\u (chroot) $HII\h $SI\w$NM ] $IN"\n')
new_bashrc.close()
runPriv("chmod 644 temp/root/.bashrc")
runPriv("chmod 600 temp/root/")
printColor("done.", "green")

printColor ("Umounting image and cleaning temp files and dirs", "green")
runPriv("umount temp/")
runPriv("rm -rf temp")
printColor("done.", "green")
print ""
printColor((" ** Disk image named %s successfully created at %s directory ** " % (disk_name, disk_path)), "green")