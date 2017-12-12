#!/usr/bin/python
#
# update_disk_img.py
# Script for updating a gem5 disk image with NPB binaries.
#

import os, subprocess, getopt, sys

from utils import *
import config

#################################################################
## General definitions, please change paths and names to the
## appropiate ones for your image and gem5 location
#################################################################

benchmark = "MULTIYCSB"
app="cassandra"
lustre_dir= config.disks_dir
base_disk= "x86_debian-jessie.img"
dest_disk= "x86_debian_%s-%s.img" % (benchmark,app)
work_dir= "%s/update_disk_img_%s" % (config.disks_dir,benchmark)
mount_dir= "%s/temp_dir" % work_dir

def usage ():
    print('update_disk_img.py [-c|--clear-at-end] [-h|--help]')

################################################################
## CLEAN SCRATCH
################################################################

def cleanTempFiles(bench_suite):
    if os.path.exists("%s" % (work_dir)):
        if os.path.exists(mount_dir) and os.path.ismount(mount_dir):
            printColor(("Umounting image and aux devives ..."), "green")
            runPriv("lsof %s |awk '{ print $2 }' |grep -v PID|sudo xargs --no-run-if-empty kill -9 " % mount_dir)
            runPriv("umount -v %s/proc" % mount_dir)
            runPriv("umount -v %s/dev" % mount_dir)
            runPriv("umount -v %s" % mount_dir)
        runPriv("rm -rf %s" % work_dir)

################################################################
## DISK MODIFICATION FUNCTIONS
################################################################

def modifyDisk(bench_suite):
    if os.path.exists(work_dir):
      runPriv("rm -fr %s/%s" % (work_dir,bench_suite))
    os.mkdir(work_dir)
    
    if not os.path.exists(mount_dir):
        os.mkdir(mount_dir)
    os.chdir(work_dir)
    
    runCommand("cp -v %s%s %s" % (lustre_dir, base_disk, dest_disk))

    if os.path.exists(mount_dir):
        runPriv("mount -o loop,offset=32256 %s %s" % (dest_disk, mount_dir))
        runPriv("mount -t proc /proc %s/proc" % mount_dir)
        runPriv("mount -o bind /dev  %s/dev" % mount_dir)
    else:
        printColor("mount directory not found" , "red")
        exit()

    MultiYCSB_Disk(work_dir,bench_suite,mount_dir,app)

################################################################
## MAIN
################################################################

try:
   opts, args = getopt.getopt(sys.argv[1:], "ch:",["clear-if-error","help"])
except getopt.GetoptError as err:
    print str(err)  
    usage()
    sys.exit(2)

output= None
clear= False

for opt, arg in opts:
    if opt in ("-h", "--help"):
        usage()
        sys.exit()
    elif opt in ("-c", "--clear-if-error"):
        clear= True
    else:
        assert False, "unhandled option"

printColor(("Modifying base image..."), "green")
try:
    modifyDisk(benchmark)
except:
    printColor(("An exception occurred: %s" % format(sys.exc_info()[0])), "red")
    if clear:
       cleanTempFiles(benchmark) 
    sys.exit(1)
printColor("done.", "green")

printColor(("Moving new image and deleting temp stuff..."), "green")
runCommand("mv -v %s/%s %s%s" % (work_dir, dest_disk, lustre_dir, dest_disk))

cleanTempFiles(benchmark)

printColor("done.", "green")
printColor("Enjoy ...!!!!", "green")