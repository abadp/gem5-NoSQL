# Copyright (c) 2013 ARM Limited
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
# Authors: Lisa Hsu
#          Pablo Prieto
#          Jose Angel Herrero

import m5
from m5.defines import buildEnv
from m5.objects import *
from Benchmarks import *
from utils import *
from utils.osutils import CpuInfo
from m5.util import addToPath, fatal
addToPath('../')
from common import Options
from common import CpuConfig
from common import MemConfig

def addKVMOptions(parser):
    option = parser.add_option

    option("--cpu-freq", type=float, default=2.5,
           help="Simulated CPU clock frequency [GHz]")

    option("--host-freq", type=float, default=(CpuInfo().freq() / 1000),
           help="Host clock frequency [GHz]")

    option("--kvm-fadj", type=float, default=0.95,
           help="KVM factor adjusted for frequency differences")

    option("--sim_quantum", type=float, default=50000000,
           help="Simulation Quantum in ticks")

    option("--kernel_lpj", type=int, default=10000000,
           help="kernel boot flag, loops_per_jiffy, to avoid calibration")

def addCLUSTEROptions(parser):
    option = parser.add_option

    # Network model Options
    option("--ethernet", action="store", type="string", default="None",
                        help="Network model to interconnect dual/cluster root simulated systems.")
    # Simulation of cluster system with a network interconnection switch ethernet model
    option("--cluster", action="store", type="int", default="1",
                        help="Simulate more than two systems attached with an ethernet switch")

def addACCommonOptions(parser):
    option = parser.add_option

    # Reset stats of gem5 when N work-counts (transactions) is reached
    parser.add_option("--work-begin-resetstats-count", default=0, type="int",
                      help="reset stats at specified work begin count")
    parser.add_option("--work-end-resetstats-count", default=0, type="int",
                      help="reset stats at specified work end count")
