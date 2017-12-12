# Copyright (c) 2010-2012 ARM Limited
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
# Copyright (c) 2010-2011 Advanced Micro Devices, Inc.
# Copyright (c) 2006-2008 The Regents of The University of Michigan
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
# Authors: Kevin Lim
#          Pablo Prieto
#          Jose Angel Herrero

from m5.util import addToPath
addToPath('../')
from m5.objects import *
from common.Benchmarks import *
from m5.util import *
from common.FSConfig import *

# Add here any function definition that you may need for your scripts.

#begin jherrero CODE
def makeX86Ethernet(testsys):

    # rb2305.patch: to available an ethernet switch model in which we can interconnect the simulated systems (cluster nodes) in a gem5 simulation
    # Ethernet
    #  - connect to PCI bus (bus_id=0)
    #  - connect to I/O APIC use INT-A (InterruptPin=1)
    testsys.pc.ethernet = IGbE_e1000(pci_bus=0, pci_dev=2, pci_func=0,
                                  InterruptLine=10, InterruptPin=1)
    testsys.pc.ethernet.pio = testsys.iobus.master
    # -- begin KVM/Timing
    #testsys.pc.ethernet.config = testsys.iobus.master
    # -- end KVM/Timing
    testsys.pc.ethernet.dma = testsys.iobus.slave

    # rb2305.patch: to available an ethernet switch model in which we can interconnect the simulated systems (cluster nodes) in a gem5 simulation
    #  - Solved problem with the ethernet interface configuration when ifconfig command is executed. This caused that gem5 fail.
    #  - when we execute ifconfig command from simulated sistem, gem5 will crash
    #  - The solution involves changes in the rb2301.patch;

    testsys.intel_mp_table.base_entries = testsys.intel_mp_table.base_entries

    # Interrupt assignment for IGbE_e1000 (bus=0,dev=2,fun=0)
    pci_dev2_inta = X86IntelMPIOIntAssignment(
            interrupt_type = 'INT',
            polarity = 'ConformPolarity',
            trigger = 'ConformTrigger',
            source_bus_id = 0,
            #source_bus_irq = 0 + (2 << 2), # Code from patch rb2301.patch
            source_bus_irq = 0 + (4 << 2),  # ATC CODE (jherrero)
            dest_io_apic_id = testsys.pc.south_bridge.io_apic.apic_id,
            #dest_io_apic_intin = 10)       # Code from patch rb2301.patch
            dest_io_apic_intin = 16)        # ATC CODE (jherrero)
    testsys.intel_mp_table.base_entries.append(pci_dev2_inta)
#end jherrero CODE

#begin prietop and jherrero CODE
# That function manages the creation and assignement of event queues for (KVM) multithreading simulations.
def assignEventQ(cluster, num_cpus):

    # Although present in Adreas Sandberg example,
    # this condtion degrades performance when cpu==1
    #if options.num_cpus > 1:
    for i, node_sys in enumerate(cluster):
        #los sistemas (nodos) simulados comparten la cola de sistema (todos en un unico thread)
        node_sys.eventq_index = 0
        for (idx, cpu) in enumerate(node_sys.cpu):
            for obj in cpu.descendants():
                obj.eventq_index = node_sys.eventq_index
            # CON comparticion tambien de las colas de CPUs (identificador) --> genera np threads en el hosts
            # cpu.eventq_index = idx + 1
            # SIN compartecion de las colas de CPUs (identificador) --> genera np*i threads en el hosts
            # cpu.eventq_index = idx + 1 + (np*i)
            if len(cluster) > 1:
                cpu.eventq_index = idx + 1 + (num_cpus*i)
            else:
                cpu.eventq_index = idx + 1
#end prietop and jherrero CODE

#begin jherrero CODE
# That function mainly makes the ethernet network interconections among cluster simulated nodes
def makeClusterRoot(full_system, clusterSystem, dumpfile, my_sim_quantum, network):
    self = Root(full_system=full_system, sim_quantum=my_sim_quantum)

    # dual root (x86 platform).
    if hasattr(clusterSystem[0], 'pc'):
        if len(clusterSystem) == 2:
            self.testsys = clusterSystem[0]
            self.drivesys = clusterSystem[1]
            if network == 'link':
                #Conexion via enlace/cable point-to-point directo /(link)
                self.etherlink = EtherLink()
                self.etherlink.int0 = Parent.testsys.pc.ethernet.interface
                self.etherlink.int1 = Parent.drivesys.pc.ethernet.interface
                print "*** [Cluster root]: Cluster nodes connection (link) point-to-point ready!!! (dual)"
            elif network == 'switch':
                #Conexion via switch
                self.etherswitch = EtherSwitch()
                self.etherlink_test = EtherLink()
                self.etherlink_drive = EtherLink()

                self.etherlink_test.int0 = Parent.testsys.pc.ethernet.interface
                self.etherlink_drive.int0 = Parent.drivesys.pc.ethernet.interface
                self.etherswitch.interface = [self.etherlink_test.int1, self.etherlink_drive.int1]

                print "*** [Cluster root]: Cluster Nodes Ethernet connection to Ethernet Switch ready!!! (dual)"
            else:
                fatal("*** [Cluster root]: Network model unknown: %s", network)
        #cluster root (x86 platform).
        elif len(clusterSystem) > 2:
            if network == 'switch':
                #Conexion via switch
                self.etherswitch = EtherSwitch()
                #-------------------------------------------------------------------------------------
                #i corresponde al ID del nodo
                for i, system in enumerate(clusterSystem):
                    exec("self.sys_%d = clusterSystem[%d]" % (i,i))
                    exec("self.etherlink_%d = EtherLink()" % i)
                    exec("self.etherlink_%d.int0 = Parent.sys_%d.pc.ethernet.interface" % (i,i))
                    exec("self.etherswitch.interface = [self.etherlink_%d.int1]" % i)
                    print "Cluster root: Ethernet Connnection Cluster node %d to Ethernet Switch ready!!!" % i
                #-------------------------------------------------------------------------------------

            else:
                fatal("*** [Cluster root]: Network model must be switch")
        else:
            print "*** [Cluster root]: Cluster size = 1"

    else:
        fatal("*** [Cluster root]: Don't know how to connect these systems (No X86) together")

    if dumpfile:
        self.etherdump = EtherDump(file=dumpfile)
        if network == 'link':
            self.etherlink.dump = Parent.etherdump
        elif network == 'switch':
            self.etherswitch.dump = Parent.etherdump
        else:
            fatal("*** [Cluster root]: Network model unknown: %s", network)

    return self
#end jherrero CODE
