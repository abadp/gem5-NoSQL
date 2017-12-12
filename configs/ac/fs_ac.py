# Copyright (c) 2010-2013 ARM Limited
# All rights reserved.
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Copyright (c) 2012-2014 Mark D. Hill and David A. Wood
# Copyright (c) 2009-2011 Advanced Micro Devices, Inc.
# Copyright (c) 2006-2007 The Regents of The University of Michigan
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors: Ali Saidi
#          Brad Beckmann
#          Pablo Prieto
#          Jose Angel Herrero

import optparse
import sys

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.util import addToPath, fatal

addToPath('../')
# addToPath('../example')
addToPath('../ruby')

import Ruby

from common.FSConfig import *
from common.SysPaths import *
from common import Simulation
from common import CacheConfig
from common import MemConfig
from common import Options
import ACOptions
# -- begin KVM/Timing
import ACSimulation
# -- end KVM/Timing

# from fs import build_test_system
from FSModule import *

from ACConfig import *

# Add options
parser = optparse.OptionParser()
Options.addCommonOptions(parser)
Options.addFSOptions(parser)
ACOptions.addKVMOptions(parser)
ACOptions.addCLUSTEROptions(parser)
ACOptions.addACCommonOptions(parser)

# Add the ruby specific and protocol specific options
if '--ruby' in sys.argv:
    Ruby.define_options(parser)

(options, args) = parser.parse_args()

if args:
    print "Error: script doesn't take any positional arguments %s" % args
    sys.exit(1)

# -- begin KVM/Timing
# system under test can be any CPU
(TestCPUClass, test_mem_mode, FutureClass) = ACSimulation.setCPUClass(options)
# -- end KVM/Timing

# -- begin KVM/Timing
# Match the memories with the CPUs, based on the options for the test system
TestMemClass = ACSimulation.setMemClass(options)
# -- end KVM/Timing

#begin jherrero CODE
if options.cluster > 0:
    bm = []
    for i in range(options.cluster):
        bm.append(SysConfig(disk=options.disk_image, rootdev=options.root_device,
                        mem=options.mem_size, os_type=options.os_type))
else:
    print "Error: Number of cluster nodes incorrect!."
    sys.exit(1)
#end jherrero CODE

np = options.num_cpus

#begin jherrero CODE
# Building simulated systems array
cluster = []
bm_node = []
for i in range(options.cluster):
    bm_node.append(bm[i])
    cluster.append(build_test_system(np, options, bm_node, test_mem_mode, TestCPUClass, FutureClass))
#end jherrero CODE

if options.random_seed != None:
    m5.core.seedRandom(options.random_seed)

#begin jherrero CODE
# Enable ethernet interface for simulated system
if options.ethernet in ['switch', 'link']:
    print "|------------------------------------|"
    print "| Ethernet network Enabled: %s." % options.ethernet
    print "|------------------------------------|\n"
    for i, node_sys in enumerate(cluster):
        makeX86Ethernet(node_sys)
else:
    print "|----------------------------|"
    print "| Ethernet network disabled. |"
    print "|----------------------------|\n"

# -- begin KVM/Timing
# Kernel version control (sd/hd)
s = options.kernel.split('x86_64-vmlinux-')[1].split('.')[1]
if int(s) < 16:
    disk="hda1"
else:
    disk="sda1"
# -- end KVM/Timing

#end jherrero CODE

if is_kvm_cpu(TestCPUClass) or is_kvm_cpu(FutureClass):
    #Using KVM multithread configuration path
    # Setting up kernel command line to run with kvm and multithread (clocksource jiffies and reliable)
    mth_cmdline = cmd_line_template(options)
    if not mth_cmdline:
        mth_cmdline = 'earlyprintk=ttyS0 console=ttyS0,115200n8 root=/dev/%s ' % (disk)
        if options.kernel_lpj is not None:
             # -- begin KVM/Timing
            mth_cmdline = mth_cmdline + 'clocksource=jiffies tsc=reliable lpj=%s norandmaps rw' % (options.kernel_lpj)
                    # -- end KVM/Timing
        else:
            # Default command line which asumes a 2GHz system. You should define lpj when using kvm, as BogoMips could have huge variations
            # -- begin KVM/Timing
            mth_cmdline = mth_cmdline + ' clocksource=jiffies tsc=reliable lpj=10000000 norandmaps rw'
            # -- end KVM/Timing
    else:
        print "BEWARE: booting with kernel options:\n%s" %mth_cmdline

    #begin jherrero CODE
    for i, node_sys in enumerate(cluster):
        node_sys.boot_osflags = fillInCmdline(bm[i], mth_cmdline)
    #end jherrero CODE

    #begin jherrero CODE
    # Creation and assignement of event queues for (KVM) multithreading simulations.
    assignEventQ(cluster, np)
    #end jherrero CODE

    m5.ticks.setGlobalFrequency(1E12)
    m5.ticks.fixGlobalFrequency()

#begin jherrero CODE
# Making the root of simulation
if options.cluster == 1:
    # single node cluster
    if is_kvm_cpu(TestCPUClass) or is_kvm_cpu(FutureClass):
        # KVM (and multithreading)
        root = Root(full_system=True, system=cluster[0], sim_quantum=options.sim_quantum)
    else:
        # Not KVM (and not multithread)
        root = Root(full_system=True, system=cluster[0])
elif options.cluster > 1:
    # multinode cluster
    root = makeClusterRoot(True, cluster, options.etherdump, options.sim_quantum, options.ethernet)
else:
    print "Error: Number of cluster nodes incorrect!"
    sys.exit(1)
#end jherrero CODE

if options.timesync:
    root.time_sync_enable = True

if options.frame_capture:
    VncServer.frame_capture = True

#begin jherrero CODE
if options.cluster>1:
    print "*** [Cluster root]: Nodos %i " % options.cluster
    print ""
#end jherrero CODE

# -- begin KVM/Timing
#Simulation.setWorkCountOptions(cluster[0], options)
#Simulation.run(options, root, cluster[0], FutureClass)

ACSimulation.setWorkCountOptions(cluster, options)
ACSimulation.run(options, root, cluster, FutureClass)
# -- end KVM/Timing
