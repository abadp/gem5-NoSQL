# Copyright (c) 2012-2013, 2015-2016 ARM Limited
# All rights reserved
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
# Copyright (c) 2010 Advanced Micro Devices, Inc.
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

# Configure the M5 cache hierarchy config in one place
#

import m5
from m5.objects import *
from Caches import *


def getReplacement(replacement):
    if replacement == "lru":
        return LRU()
    elif replacement == "random":
        return RandomRepl()
    elif replacement == "srrip":
        return SRRIP()
    elif replacement == "falru":
        return FALRU()
    else:
        print "Cannot recognize replacement policy" + replacement
        print "Valid replacement policies are: lru, falru, random and srrip"
        sys.exit(1)

def getPrefetcher(prefetcher):
    if prefetcher == "none":
        return NULL
    elif prefetcher == "queued":
        return QueuedPrefetcher()
        # Prefetch with prefetch queue and priority (queue of patterns)
    elif prefetcher == "stride":
        return StridePrefetcher()
        # Prefetch that uses PC to detect patterns
    elif prefetcher == "tagged":
        return TaggedPrefetcher()
        # Basic n blocks ahead prefetcher
    else:
        print "Cannot recognize prefetcher" + prefetcher
        print "Valid prefetch options are: none, queued, stride and tagged"
        sys.exit(1)

def getPrefetch(prefetcher):
    if prefetcher == "none":
        return False
    elif prefetcher == "queued":
        # Prefetch with prefetch queue and priority (queue of patterns)
        return True
    elif prefetcher == "stride":
        # Prefetch that uses PC to detect patterns
        return True
    elif prefetcher == "tagged":
        # Basic n blocks ahead prefetcher
        return True
    else:
        print "Cannot recognize prefetcher" + prefetcher
        print "Valid prefetch options are: none, queued, stride and tagged"
        sys.exit(1)

def config_cache(options, system):
    if options.external_memory_system and (options.caches or options.l2cache):
        print "External caches and internal caches are exclusive options.\n"
        sys.exit(1)

    if options.external_memory_system:
        ExternalCache = ExternalCacheFactory(options.external_memory_system)

    if options.cpu_type == "arm_detailed":
        try:
            from O3_ARM_v7a import *
        except:
            print "arm_detailed is unavailable. Did you compile the O3 model?"
            sys.exit(1)

        dcache_class, icache_class, l2_cache_class, walk_cache_class = \
            O3_ARM_v7a_DCache, O3_ARM_v7a_ICache, O3_ARM_v7aL2, \
            O3_ARM_v7aWalkCache
    else:
        # begin ATC CODE (acolaso)
        #dcache_class, icache_class, l2_cache_class = \
        #    L1Cache, L1Cache, L2Cache
        dcache_class, icache_class, l2_cache_class, l3_cache_class, walk_cache_class = \
            L1_DCache, L1_ICache, L2Cache, L3Cache, None
        # end ATC CODE

        if buildEnv['TARGET_ISA'] == 'x86':
            walk_cache_class = PageTableWalkerCache

    # Set the cache line size of the system
    system.cache_line_size = options.cacheline_size

    # If elastic trace generation is enabled, make sure the memory system is
    # minimal so that compute delays do not include memory access latencies.
    # Configure the compulsory L1 caches for the O3CPU, do not configure
    # any more caches.
    if (options.l2cache or options.l3cache) and options.elastic_trace_en:
        fatal("When elastic trace is enabled, do not configure L2 caches.")
    
    # begin ATC CODE (acolaso)
    if options.l3cache:
        system.l3 = l3_cache_class(clk_domain=system.cpu_clk_domain,
                                   size=options.l3_size,
                                   assoc=options.l3_assoc,
                                   hit_latency=options.l3_hit_latency,
                                   response_latency=options.l3_response_latency,
                                   mshrs=options.l3_mshrs,
                                   tgts_per_mshr=options.l3_tgts_per_mshr,
                                   tags=getReplacement(options.l3_replacement),
                                   prefetcher=getPrefetcher(options.l3_prefetcher),
                                   prefetch_on_access=getPrefetch(options.l3_prefetcher))

        system.tol3bus = L3XBar(clk_domain = system.cpu_clk_domain,
                                     width = 32)
        system.l3.cpu_side = system.tol3bus.master
        system.l3.mem_side = system.membus.slave
    else:
    # end ATC CODE
        if options.l2cache:
            # Provide a clock for the L2 and the L1-to-L2 bus here as they
            # are not connected using addTwoLevelCacheHierarchy. Use the
            # same clock as the CPUs, and set the L1-to-L2 bus width to 32
            # bytes (256 bits).
            system.l2 = l2_cache_class(clk_domain=system.cpu_clk_domain,
                                       size=options.l2_size,
                                       assoc=options.l2_assoc,
                                       # begin ATC CODE (acolaso)
                                       hit_latency=options.l2_hit_latency,
                                       response_latency=options.l2_response_latency,
                                       mshrs=options.l2_mshrs,
                                       tgts_per_mshr=options.l2_tgts_per_mshr,
                                       tags=getReplacement(options.l2_replacement),
                                       prefetcher=getPrefetcher(options.l2_prefetcher),
                                   prefetch_on_access=getPrefetch(options.l2_prefetcher))
                                       # end ATC CODE

            system.tol2bus = L2XBar(clk_domain = system.cpu_clk_domain,
                                          width = 32)
            system.l2.cpu_side = system.tol2bus.master
            system.l2.mem_side = system.membus.slave

    if options.memchecker:                                                                  
        system.memchecker = MemChecker() 


    for i in xrange(options.num_cpus):
        if options.caches:
            icache = icache_class(size=options.l1i_size,
                                  assoc=options.l1i_assoc,
                                  # begin ATC CODE (acolaso)
                                  hit_latency=options.l1i_hit_latency,
                                  response_latency=options.l1i_response_latency,
                                  mshrs=options.l1i_mshrs,
                                  tgts_per_mshr=options.l1i_tgts_per_mshr)
                                  # end ATC CODE
            dcache = dcache_class(size=options.l1d_size,
                                  assoc=options.l1d_assoc,
                                  # begin ATC CODE (acolaso)
                                  hit_latency=options.l1d_hit_latency,
                                  response_latency=options.l1d_response_latency,
                                  mshrs=options.l1d_mshrs,
                                  tgts_per_mshr=options.l1d_tgts_per_mshr,
                                  tags=getReplacement(options.l1_replacement),
                                  prefetcher=getPrefetcher(options.l1_prefetcher),
                                   prefetch_on_access=getPrefetch(options.l1_prefetcher))
                                  # end ATC CODE

            # If we have a walker cache specified, instantiate two
            # instances here
            if walk_cache_class:
                iwalkcache = walk_cache_class()
                dwalkcache = walk_cache_class()
            else:
                iwalkcache = None
                dwalkcache = None

            if options.memchecker:
                dcache_mon = MemCheckerMonitor(warn_only=True)
                dcache_real = dcache

                # Do not pass the memchecker into the constructor of
                # MemCheckerMonitor, as it would create a copy; we require
                # exactly one MemChecker instance.
                dcache_mon.memchecker = system.memchecker

                # Connect monitor
                dcache_mon.mem_side = dcache.cpu_side

                # Let CPU connect to monitors         
                dcache = dcache_mon

            # begin ATC CODE (acolaso)
            if options.l3cache:
                system.cpu[i].l2 = l2_cache_class(clk_domain=system.cpu_clk_domain,
                                                  size=options.l2_size,
                                                  assoc=options.l2_assoc,
                                                  hit_latency=options.l2_hit_latency,
                                                  response_latency=options.l2_response_latency,
                                                  mshrs=options.l2_mshrs,
                                                  tgts_per_mshr=options.l2_tgts_per_mshr)

                system.cpu[i].tol2bus = L2XBar()
                system.cpu[i].l2.cpu_side = system.cpu[i].tol2bus.master
                system.cpu[i].l2.mem_side = system.tol3bus.slave 
            # end ATC CODE

            # When connecting the caches, the clock is also inherited
            # from the CPU in question
            system.cpu[i].addPrivateSplitL1Caches(icache, dcache,
                                                  iwalkcache, dwalkcache)

            if options.memchecker:
                # The mem_side ports of the caches haven't been connected yet.
                # Make sure connectAllPorts connects the right objects.
                system.cpu[i].dcache = dcache_real
                system.cpu[i].dcache_mon = dcache_mon

        elif options.external_memory_system:
            # These port names are presented to whatever 'external' system
            # gem5 is connecting to.  Its configuration will likely depend
            # on these names.  For simplicity, we would advise configuring
            # it to use this naming scheme; if this isn't possible, change
            # the names below.
            if buildEnv['TARGET_ISA'] in ['x86', 'arm']:
                system.cpu[i].addPrivateSplitL1Caches(
                        ExternalCache("cpu%d.icache" % i),
                        ExternalCache("cpu%d.dcache" % i),
                        ExternalCache("cpu%d.itb_walker_cache" % i),
                        ExternalCache("cpu%d.dtb_walker_cache" % i))
            else:
                system.cpu[i].addPrivateSplitL1Caches(
                        ExternalCache("cpu%d.icache" % i),
                        ExternalCache("cpu%d.dcache" % i))

        system.cpu[i].createInterruptController()

        # begin ATC CODE (acolaso)
        if options.l3cache:
            system.cpu[i].connectAllPorts(system.cpu[i].tol2bus, system.membus)
        else:
        # end ATC CODE
            if options.l2cache:
                system.cpu[i].connectAllPorts(system.tol2bus, system.membus)
            else:
                system.cpu[i].connectAllPorts(system.membus)

    return system

# ExternalSlave provides a "port", but when that port connects to a cache,
# the connecting CPU SimObject wants to refer to its "cpu_side".
# The 'ExternalCache' class provides this adaptation by rewriting the name,
# eliminating distracting changes elsewhere in the config code.
class ExternalCache(ExternalSlave):
    def __getattr__(cls, attr):
        if (attr == "cpu_side"):
            attr = "port"
        return super(ExternalSlave, cls).__getattr__(attr)

    def __setattr__(cls, attr, value):
        if (attr == "cpu_side"):
            attr = "port"
        return super(ExternalSlave, cls).__setattr__(attr, value)

def ExternalCacheFactory(port_type):
    def make(name):
        return ExternalCache(port_data=name, port_type=port_type,
                             addr_ranges=[AllMemory])
    return make
