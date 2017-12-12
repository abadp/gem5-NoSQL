#!/usr/bin/python
#*******************************************************************************
# SCRIPT to atomagically generate config_files
# *******************************************************************************

import os

unit = "k"
for i in range(0, 15):
    assoc = 2**i
    Size = 16*assoc
    if Size >= 1024:
        Size = Size/1024
        unit = "M"
        if Size >= 1024:
            Size = Size/1024
            unit = "G"
    Configfile = "L1DataSize_" + str(Size) + unit + ".py"
    os.system("cp L1DataSize_16k.py " + Configfile)
    os.system("sed -i 's/16kB/" + str(Size) + unit + "B/g' " + Configfile)
    print "sed -i 's/16kB/" + str(Size) + unit + "B/g' " + Configfile
    os.system("sed -i -E \"s/'l1d_assoc'            : '1/'l1d_assoc'            : '" + str(assoc) + "/\" " + Configfile)
    print "sed -i -E \"s/'l1d_assoc'            : '1/'l1d_assoc'            : '" + str(assoc) + "/\" " + Configfile
    print "Done " + Configfile
print "Done all\n"
