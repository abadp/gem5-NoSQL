# -*- mode:python -*-

# Copyright (c) 2012 Univerity of Cantabria (Spain)
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
# Authors: Pablo Abad
#          Valentin Puente

from m5.params import *
from m5.proxy import *
from Network import RubyNetwork
from BasicRouter import BasicRouter

class TopazNetwork(RubyNetwork):
    type = 'TopazNetwork'
    cxx_header = "mem/ruby/network/topaz/TopazNetwork.hh"
    buffer_size = Param.Int(0,
        "default buffer size; 0 indicates infinite buffering");
    endpoint_bandwidth = Param.Int(1000,
                      "bandwidth adjustment factor");
    adaptive_routing = Param.Bool(False,
                      "enable adaptive routing");
    topaz_init_file = Param.String("./TPZSimul.ini",
                      "File that declares <simulation>.sgm, <network>.sgm and <router>.sgm");
    topaz_network =Param.String (None,
                      "TOPAZ: simulation listed in <simulation>.sgm to be used by TOPAZ");
    topaz_flit_size = Param.Int(0,
                      "Number of bytes per physical router-to-router wire");
    topaz_clock_ratio = Param.Int(1,
                      "memory-network clock multiplier");
    topaz_adaptive_interface_threshold = Param.Int(0,
                      "infligh patckets required to activate TOPAZ");

class TopazSwitch(BasicRouter):
      type = 'TopazSwitch'
      cxx_header = 'mem/ruby/network/topaz/TopazSwitch.hh'
      virt_nets = Param.Int(Parent.number_of_virtual_networks,
                            "number of virtual networks")