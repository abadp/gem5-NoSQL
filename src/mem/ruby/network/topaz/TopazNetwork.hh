/*
 * Copyright (c) 2012 The University of Cantabria (Spain)
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef __MEM_RUBY_NETWORK_SIMPLE_TOPAZNETWORK_HH__
#define __MEM_RUBY_NETWORK_SIMPLE_TOPAZNETWORK_HH__

#include <iostream>
#include <vector>
#include <cmath>
#include <fstream>

#include "mem/ruby/common/Global.hh"
#include "mem/ruby/network/Network.hh"
#include "mem/ruby/slicc_interface/NetworkMessage.hh"
#include "params/TopazNetwork.hh"
#include "sim/sim_object.hh"

//Main simulator include. Download simulator from
//http://www.atc.unican.es/topaz/ and follow the guide
#include <TPZSimulator.hpp>

struct MessageTopaz{
    MsgPtr message;
    int    vnet;
    int    queue;
    int    destinations;
    int    bcast;
    int    id;
    //multicast support
    std::vector<std::vector<int> > Vector_aux;
};

class NetDest;
class MessageBuffer;
class Throttle;
class TopazSwitch;
class Topology;

class TopazNetwork : public Network
{
  public:
    typedef TopazNetworkParams Params;
    TopazNetwork(const Params *p);
    ~TopazNetwork();

    void init();

    int getBufferSize() { return m_buffer_size; }
    int getEndpointBandwidth() { return m_endpoint_bandwidth; }
    bool getAdaptiveRouting() {return m_adaptive_routing; }

    void collateStats();
    void regStats();
    void printConfig(std::ostream& out) const;

    int getNumberOfNodes() {return m_nodes;};
    unsigned getProcRouterRatio() const	{  return m_processorClockRatio;}
    unsigned getFlitSize() const { return m_flitSize;}
    unsigned getUnifiy() { return m_unify; }
    int getNetSize() { return m_switch_ptr_vector.size(); }
    int getMessageSizeTopaz(MessageSizeType size_type) const;
    int getTriggerSwitch() const { return m_firstTrigger; }
    void setTriggerSwitch(int router) {	m_firstTrigger=router; }
    const bool inWarmup() { return m_in_warmup; }
    bool useGemsNetwork(int vnet);
    void enableTopaz();
    void disableTopaz();
    void increaseNumMsg(int num);
    void decreaseNumMsg(int vnet);
    void increaseNumOrderedMsg(int num);
    void increaseNumTopazOrderedMsg (int num);
    void increaseNumTopazMsg(int num);
    void decreaseNumTopazMsg (int vnet);
    int getTopazMessages() { return m_number_topaz_messages; }
    void increaseTotalMsg (int num) { m_totalNetMsg+=num; }
    int getTotalMsg () { return m_totalNetMsg; }
    int getTotalTopazMsg() { return m_totalTopazMsg; }
    const int numberOfMessages() { return m_number_messages; }
    const int numberOfOrderedMessages() { return m_number_ordered_messages; }
    const int numberOfTopazOrderedMessages() { return m_number_topaz_ordered_messages; }
    const int numberOfTopazMessages() { return m_number_topaz_messages; }
    void setTopazMapping (SwitchID node0, SwitchID node1);
    SwitchID getSwitch(int ext_node) { return m_forward_mapping[ext_node]; }
    NetDest getMachines(SwitchID sid) { return m_reverse_mapping[sid]; }
    MessageBuffer* getToSimNetQueue(NodeID id, bool ordered, int network_num);
    MessageBuffer* getFromSimNetQueue(NodeID id, bool ordered, int network_num);
//TOPAZ

    void reset();

    // returns the queue requested for the given component
    void setToNetQueue(NodeID id, bool ordered, int network_num,
                       std::string vnet_type, MessageBuffer *b);
    void setFromNetQueue(NodeID id, bool ordered, int network_num,
                         std::string vnet_type, MessageBuffer *b);

    virtual const std::vector<Throttle*>* getThrottles(NodeID id) const;

    const bool isVNetOrdered(int vnet) { return m_ordered[vnet]; }
    const bool validVirtualNetwork(int vnet) { return m_in_use[vnet]; }

    int getNumNodes() {return m_nodes; }

    // Methods used by Topology to setup the network
    void makeOutLink(SwitchID src, NodeID dest, BasicLink* link,
                     LinkDirection direction,
                     const NetDest& routing_table_entry);
    void makeInLink(NodeID src, SwitchID dest, BasicLink* link,
                    LinkDirection direction,
                    const NetDest& routing_table_entry);
    void makeInternalLink(SwitchID src, SwitchID dest, BasicLink* link,
                          LinkDirection direction,
                          const NetDest& routing_table_entry);

    void print(std::ostream& out) const;

    bool functionalRead(Packet *pkt);
    uint32_t functionalWrite(Packet *pkt);

  private:
    void checkNetworkAllocation(NodeID id, bool ordered, int network_num);
    void addLink(SwitchID src, SwitchID dest, int link_latency);
    void makeLink(SwitchID src, SwitchID dest,
        const NetDest& routing_table_entry, int link_latency);
    SwitchID createSwitch();
    void makeTopology();
    void linkTopology();

    unsigned m_processorClockRatio;
    unsigned m_flitSize;
    unsigned m_unify;
    int m_firstTrigger;
    bool m_in_warmup;
    unsigned m_permanentDisable;
    int m_number_messages;
    int m_number_ordered_messages;
    int m_number_topaz_ordered_messages;
    int m_number_topaz_messages;
    //maps each MachineID to the internal node it is connected to
    SwitchID *m_forward_mapping;
    //maps each internal node to the MachineIDs it connects.
    std::vector<NetDest> m_reverse_mapping;
    int m_totalNetMsg;
    int m_totalTopazMsg;
    TPZString m_simulName;
    TPZString m_topazInitFile;
    unsigned m_block_size;
    unsigned m_topaz_adaptive_interface_threshold;

    // Private copy constructor and assignment operator
    TopazNetwork(const TopazNetwork& obj);
    TopazNetwork& operator=(const TopazNetwork& obj);

    // vector of queues from the components
    //std::vector<std::vector<MessageBuffer*> > m_toNetQueues;
    //std::vector<std::vector<MessageBuffer*> > m_fromNetQueues;

    std::vector<bool> m_in_use;
    std::vector<bool> m_ordered;
    std::vector<TopazSwitch*> m_switch_ptr_vector;
    std::vector<MessageBuffer*> m_buffers_to_free;
    std::vector<TopazSwitch*> m_endpoint_switches;

    int m_buffer_size;
    int m_endpoint_bandwidth;
    bool m_adaptive_routing;

    //Statistical variables
    Stats::Formula m_msg_counts[MessageSizeType_NUM];
    Stats::Formula m_msg_bytes[MessageSizeType_NUM];
};

inline std::ostream&
operator<<(std::ostream& out, const TopazNetwork& obj)
{
    obj.print(out);
    out << std::flush;
    return out;
}

#endif // __MEM_RUBY_NETWORK_SIMPLE_TOPAZNETWORK_HH__
