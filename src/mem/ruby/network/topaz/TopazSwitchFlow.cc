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

#include <algorithm>

#include <TPZSimulator.hpp>

#include "base/cast.hh"
#include "base/random.hh"
#include "debug/RubyNetwork.hh"
#include "mem/ruby/network/MessageBuffer.hh"
#include "mem/ruby/network/topaz/TopazNetwork.hh"
#include "mem/ruby/network/topaz/TopazSwitchFlow.hh"
#include "mem/ruby/network/topaz/TopazSwitch.hh"
#include "mem/ruby/profiler/Profiler.hh"
#include "mem/ruby/slicc_interface/NetworkMessage.hh"
#include "mem/ruby/system/System.hh"

using namespace std;

const int PRIORITY_SWITCH_LIMIT = 128;

//xA VPV KEEP COMMENTED!
// Operator for helper class
//bool
//operator<(const LinkOrder& l1, const LinkOrder& l2)
//{
//    return (l1.m_value < l2.m_value);
//}

//TopazSwitchFlow::TopazSwitchFlow(SwitchID sid, TopazNetwork* network_ptr)
TopazSwitchFlow::TopazSwitchFlow(SwitchID sid, TopazSwitch *sw, uint32_t virt_nets)
    : Consumer(sw)
{
    m_switch_id = sid;
    m_round_robin_start = 0;
    m_wakeups_wo_switch = 0;
    m_ruby_start=0;
    m_virtual_networks = virt_nets;
}

void
TopazSwitchFlow::init(TopazNetwork *network_ptr)
{
    m_network_ptr = network_ptr;

    for(int i = 0;i < m_virtual_networks;++i) {
        m_pending_message_count.push_back(0);
    }
}

void
TopazSwitchFlow::addInPort(const vector<MessageBuffer*>& in)
{
    NodeID port = m_in.size();
    m_in.push_back(in);

    for (int i = 0; i < in.size(); ++i) {
        if (in[i] != nullptr) {
            in[i]->setConsumer(this);

            string desc =
                csprintf("[Queue from port %s %s %s to PerfectSwitch]",
                         to_string(m_switch_id), to_string(port),
                         to_string(i));

            in[i]->setDescription(desc);
            in[i]->setIncomingLink(port);
            in[i]->setVnet(i);
        }
    }
}

void
TopazSwitchFlow::addOutPort(const vector<MessageBuffer*>& out,
                            const NetDest& routing_table_entry)
{
    // Setup link order
    LinkOrder l;
    l.m_value = 0;
    l.m_link = m_out.size();
    m_link_order.push_back(l);

    // Add to routing table
    m_out.push_back(out);
    m_routing_table.push_back(routing_table_entry);
}

TopazSwitchFlow::~TopazSwitchFlow()
{
}

//******************************************************************************
// Function in charge of calculating the destination of an Unicast message
//******************************************************************************
int TopazSwitchFlow::getUnicastDestination(NetDest destinations) {
    int this_id;
    int m_queue=0;
    for (MachineType mType = MachineType_FIRST; mType < MachineType_NUM; ++mType) {
        int limit = MachineType_base_count(mType);
        for (unsigned int component = 0; component < limit; component++) {
            MachineID mach = {mType, component};
            if (destinations.elementAt(mach)==1) {
                this_id=m_network_ptr->getSwitch(m_queue+component);
                return this_id;
            }
        }
        m_queue += MachineType_base_count(mType);
    }
    assert(m_queue!=0);
    return 1;
}

//******************************************************************************
// Function in charge of calculating the mask of a Multicast message
//******************************************************************************
unsigned long long
TopazSwitchFlow::getMulticastDestination(NetDest& destinations) {
    unsigned long long routers = 0;
    int node_number = 0;
    for (MachineType m = MachineType_FIRST; m < MachineType_NUM; ++m) {
        for (unsigned int c = 0; c<MachineType_base_count(m); c++) {
            MachineID thisMid = {m, c};
            if (destinations.isElement(thisMid)) {
                unsigned long long mask = 1;
                mask = mask << (m_network_ptr->getSwitch(node_number));
                routers = routers | mask;
            }
            node_number++;
        }
    }
    return routers;
}

//******************************************************************************
// Function in charge of filtering messages with src=dst
// this kind of messages are not routed through TOPAZ network
//******************************************************************************
void
TopazSwitchFlow::filterZeroDistanceMessages( MsgPtr& msg_ptr, int vnet,
                                                NetDest& destinations) {
    int source=m_switch_id;
    int destination;
    bool isOrdered= m_network_ptr->isVNetOrdered(vnet);
    int m_queue=0;
    for (MachineType mType = MachineType_FIRST; mType < MachineType_NUM; ++mType){
        int limit = MachineType_base_count(mType);
        for (unsigned int component = 0; component < limit; component++)    {
            MachineID mach = {mType, component};
            if(destinations.elementAt(mach)==1)    {
                destination=m_network_ptr->getSwitch(m_queue+component);
                if (source == destination){
                    MessageBuffer* outputQueue=m_network_ptr->
                          getFromSimNetQueue(component+m_queue, isOrdered, vnet);
                    MsgPtr unaMas=msg_ptr->clone();
                    outputQueue->enqueue(unaMas);
                    destinations.remove(mach); // Here destinations are modified
                }
            }
        }
        m_queue += MachineType_base_count(mType);
    }
}

//******************************************************************************
// This function returns a NetDest vector result of the following operation
//  msg_destinations & Router_mask
// where Router_mask indicates which components are reachable through a certain
// switch
//******************************************************************************
NetDest
TopazSwitchFlow::getConsumerDestinations(int switch_id, NetDest& dest) {
    NetDest consumers = m_network_ptr->getMachines(switch_id);
    return consumers.AND(dest);
}

//******************************************************************************
// Function in charge of deciding which network must be used, GEMS or TOPAZ
//******************************************************************************
void TopazSwitchFlow::wakeup() {
    m_wakeups_wo_switch++;
    int highest_prio_vnet = m_virtual_networks-1;
    int lowest_prio_vnet =0 ;
    int decrementer = 1;
    int source=m_switch_id;

  // invert priorities to avoid starvation seen in the component network
  if (m_wakeups_wo_switch > PRIORITY_SWITCH_LIMIT) {
      m_wakeups_wo_switch = 0;
      highest_prio_vnet = 0;
      lowest_prio_vnet = m_virtual_networks-1;
      decrementer = -1;
  }

// For all components incoming queues
  for (int vnet = highest_prio_vnet;
     (vnet * decrementer) >= (decrementer * lowest_prio_vnet);
     vnet -= decrementer) {
       //If we are in warmup or the adaptive interface is used and then
       //network is lightly loadad we may ruby network
        if (m_network_ptr->useGemsNetwork(vnet)) {
           wakeupVnet(vnet);
        }
     //Otherwise, use topaz
      else{
       if(m_pending_message_count[vnet]>0)
        for(int incoming=0;incoming<m_in.size();incoming++) {

            // temporary vectors to store the routing results
            vector<LinkID> output_links;
            vector<NetDest> output_link_destinations;

            // Is there a message waiting?
            //auto it = m_in[incoming].find(vnet);
            //if (it == m_in[incoming].end())
            //    continue;

            //MessageBuffer *buffer = (*it).second;
   
            if (m_in[incoming].size() <= vnet) {
                 continue;
            }

             MessageBuffer *buffer = m_in[incoming][vnet];
             if (buffer == nullptr) {
                 continue;
             }

            //If there is packets waiting, we move it to Topaz
            while(buffer->isReady()){
                MsgPtr msg_ptr = buffer->peekMsgPtr();
                NetworkMessage *net_msg_ptr =
                        dynamic_cast<NetworkMessage*>(msg_ptr.get());
                NetDest msg_destinations =
                        net_msg_ptr->getInternalDestination();
                int topaz_size=m_network_ptr->
                        getMessageSizeTopaz(net_msg_ptr->getMessageSize());
                assert(topaz_size);
                filterZeroDistanceMessages( msg_ptr, vnet, msg_destinations);
                if ( msg_destinations.count() !=0) {
                    TPZMessage msg;
                    TPZPosition origen;
                    TPZPosition destino;
                    MessageTopaz* copia=new  MessageTopaz;
                    copia->message=msg_ptr->clone();
                    copia->vnet=vnet;
                    copia->destinations=msg_destinations.count();
                    // TOPAZ message generation
                    msg.setExternalInfo(static_cast<void*>(copia));
                    msg.setGenerationTime(TPZSIMULATOR()->
                                          getSimulation(1)->getCurrentTime());
                    origen=TPZSIMULATOR()->getSimulation(1)->
                                          getNetwork()->CreatePosition(source);
                    msg.setSource(origen);
                    msg.setVnet(vnet+1);
                    msg.setMessageSize(1);
                    msg.setPacketSize(topaz_size);
                    if (m_network_ptr->isVNetOrdered(vnet)){
                        msg.setOrdered();
                        m_network_ptr->
                               increaseNumTopazOrderedMsg(msg_destinations.count());
                    }
                    if (msg_destinations.count()==1) {
                        msg.clearMulticast();
                        int componente = getUnicastDestination(msg_destinations);
                        destino=TPZSIMULATOR()->getSimulation(1)->
                                getNetwork()->CreatePosition(componente);
                        msg.setDestiny(destino);
                    }
                    else {
                        msg.setMulticast();
                        //This destination is necessary because topaz
                        //checks the existence
                        //of src and destination routers
                        //this destination is only used for this purpose,
                        //no messages will arrive to it.
                        msg.setDestiny(origen);
                        unsigned long long msgMask=
                               getMulticastDestination(msg_destinations);
                        msg.setMsgmask(msgMask);
                    }
                    // Send the message to the network
                    DPRINTF(RubyNetwork, "Send at switch: [%d] vnet: [%d] time: [%d].\n",
                                          m_switch_id, vnet, g_system_ptr->curCycle());
                    TPZSIMULATOR()->getSimulation(1)->getNetwork()->sendMessage(msg);
                    m_network_ptr->increaseNumTopazMsg(msg_destinations.count());
                }
                buffer->dequeue();
                m_pending_message_count[vnet]--;
            }
          }
       }
    }
    //ijust a prewarmed simulation
    if (m_network_ptr->inWarmup()) return;
    if (m_network_ptr->getTriggerSwitch() == ~0) {
        m_network_ptr->setTriggerSwitch(m_switch_id);
    }
    //Only first switch  run and implement consumption.
    if ( m_switch_id != m_network_ptr->getTriggerSwitch() ) return;
    wakeUpTopaz();
}

//******************************************************************************
// This function is in charge of running TOPAZ and collecting the messages
// to send then back to GEMS queues
//******************************************************************************
void TopazSwitchFlow::wakeUpTopaz() {
    long unsigned current_time =
         static_cast<long unsigned>(g_system_ptr->curCycle()) - m_ruby_start;
    int procesorNetRatio=m_network_ptr->getProcRouterRatio();
    int messagesOnNets=0;
    long diff_time = current_time - TPZSIMULATOR()->getSimulation(1)->getCurrentTime()*procesorNetRatio;
    if (diff_time > 0) {
        TPZSIMULATOR()->getSimulation(1)->setCurrentTime((current_time/procesorNetRatio)-1);
        TPZSIMULATOR()->getSimulation(1)->run(1);
        for (int consumer = 0;
             consumer<TPZSIMULATOR()->getSimulation(1)->getNetwork()->Number_of_nodes();
             consumer++) {
             TPZPosition position_f=
                 TPZSIMULATOR()->getSimulation(1)->getNetwork()->CreatePosition(consumer);
            void* ptr =(TPZSIMULATOR()->getSimulation(1)->getExternalInfoAt(position_f));
            if (ptr!=NULL) {
                MessageTopaz* topaz_message = static_cast<MessageTopaz*>(ptr);
                assert (topaz_message->destinations>0);
                MsgPtr localCopy = (topaz_message->message);
                NetworkMessage* net_msg_ptr =
                                dynamic_cast<NetworkMessage*>(localCopy.get());
                int vvnet=topaz_message->vnet;
                int isOrdered= m_network_ptr->isVNetOrdered(vvnet);
                NetDest ConsDestinations =
                           getConsumerDestinations(consumer,
                                          net_msg_ptr->getInternalDestination());
                DPRINTF(RubyNetwork, "Arrival at switch: [%d] vnet: [%d] time: [%d].\n",
                                      consumer, vvnet, g_system_ptr->curCycle());
                int m_queue=0;
                for (MachineType mType = MachineType_FIRST;
                     mType < MachineType_NUM; ++mType) {
                    int limit = MachineType_base_count(mType);
                    for (unsigned int component = 0; component < limit; component++) {
                        MachineID mach = {mType, component};
                        if(ConsDestinations.elementAt(mach)==1) {
                            MsgPtr unaMas = localCopy->clone();
                            MessageBuffer* outputQueue=
                                 m_network_ptr->getFromSimNetQueue(component+m_queue,
                                                                   isOrdered,
                                                                   vvnet);
                            outputQueue->enqueue(unaMas);
                            topaz_message->destinations=topaz_message->destinations-1;
                            m_network_ptr->decreaseNumTopazMsg(vvnet);
                        }
                    }
                    m_queue += MachineType_base_count(mType);
                }
                int pendientes=topaz_message->destinations;
                if (pendientes==0) delete topaz_message;
            }
        }
        messagesOnNets=m_network_ptr->getTopazMessages();
    }

    if ( messagesOnNets!=0)
        scheduleEvent(Cycles(1));
    else
        m_network_ptr->setTriggerSwitch(~0);
}


void
TopazSwitchFlow::wakeupVnet(int vnet)
{
    MsgPtr msg_ptr;
    NetworkMessage* net_msg_ptr = NULL;

    // This is for round-robin scheduling
    int incoming = m_round_robin_start;
    m_round_robin_start++;
    if (m_round_robin_start >= m_in.size()) {
        m_round_robin_start = 0;
    }

    if(m_pending_message_count[vnet] > 0) {
        // for all input ports, use round robin scheduling
        for (int counter = 0; counter < m_in.size(); counter++) {
            // Round robin scheduling
            incoming++;
            if (incoming >= m_in.size()) {
                incoming = 0;
            }

            // temporary vectors to store the routing results
            vector<LinkID> output_links;
            vector<NetDest> output_link_destinations;

            // Is there a message waiting?
            if (m_in[incoming].size() <= vnet) {
                continue;
            }

            MessageBuffer *buffer = m_in[incoming][vnet];
            if (buffer == nullptr) {
                continue;
            }

            while (buffer->isReady()) {
                DPRINTF(RubyNetwork, "incoming: %d\n", incoming);

                // Peek at message
                msg_ptr = buffer->peekMsgPtr();
                net_msg_ptr = safe_cast<NetworkMessage*>(msg_ptr.get());
                DPRINTF(RubyNetwork, "Message: %s\n", (*net_msg_ptr));

                output_links.clear();
                output_link_destinations.clear();
                NetDest msg_dsts = net_msg_ptr->getInternalDestination();

                // Unfortunately, the token-protocol sends some
                // zero-destination messages, so this assert isn't valid
                // assert(msg_dsts.count() > 0);

                assert(m_link_order.size() == m_routing_table.size());
                assert(m_link_order.size() == m_out.size());

                if (m_network_ptr->getAdaptiveRouting()) {
                    if (m_network_ptr->isVNetOrdered(vnet)) {
                        // Don't adaptively route
                        for (int out = 0; out < m_out.size(); out++) {
                            m_link_order[out].m_link = out;
                            m_link_order[out].m_value = 0;
                        }
                    } else {
                        // Find how clogged each link is
                        for (int out = 0; out < m_out.size(); out++) {
                            int out_queue_length = 0;
                            for (int v = 0; v < m_virtual_networks; v++) {
                                out_queue_length += m_out[out][v]->getSize();
                            }
                            int value =
                                (out_queue_length << 8) |
                                random_mt.random(0, 0xff);
                            m_link_order[out].m_link = out;
                            m_link_order[out].m_value = value;
                        }

                        // Look at the most empty link first
                        sort(m_link_order.begin(), m_link_order.end());
                    }
                }

                for (int i = 0; i < m_routing_table.size(); i++) {
                    // pick the next link to look at
                    int link = m_link_order[i].m_link;
                    NetDest dst = m_routing_table[link];
                    DPRINTF(RubyNetwork, "dst: %s\n", dst);

                    if (!msg_dsts.intersectionIsNotEmpty(dst))
                        continue;

                    // Remember what link we're using
                    output_links.push_back(link);

                    // Need to remember which destinations need this message in
                    // another vector.  This Set is the intersection of the
                    // routing_table entry and the current destination set.  The
                    // intersection must not be empty, since we are inside "if"
                    output_link_destinations.push_back(msg_dsts.AND(dst));

                    // Next, we update the msg_destination not to include
                    // those nodes that were already handled by this link
                    msg_dsts.removeNetDest(dst);
                }

                assert(msg_dsts.count() == 0);

                // Check for resources - for all outgoing queues
                bool enough = true;
                for (int i = 0; i < output_links.size(); i++) {
                    int outgoing = output_links[i];

                    if (!m_out[outgoing][vnet]->areNSlotsAvailable(1))
                        enough = false;

                    DPRINTF(RubyNetwork, "Checking if node is blocked ..."
                            "outgoing: %d, vnet: %d, enough: %d\n",
                            outgoing, vnet, enough);
                }

                // There were not enough resources
                if (!enough) {
                    scheduleEvent(Cycles(1));
                    DPRINTF(RubyNetwork, "Can't deliver message since a node "
                            "is blocked\n");
                    DPRINTF(RubyNetwork, "Message: %s\n", (*net_msg_ptr));
                    break; // go to next incoming port
                }

                MsgPtr unmodified_msg_ptr;

                if (output_links.size() > 1) {
                    // If we are sending this message down more than one link
                    // (size>1), we need to make a copy of the message so each
                    // branch can have a different internal destination we need
                    // to create an unmodified MsgPtr because the MessageBuffer
                    // enqueue func will modify the message

                    // This magic line creates a private copy of the message
                    unmodified_msg_ptr = msg_ptr->clone();
                }

                // Dequeue msg
                buffer->dequeue();
                m_pending_message_count[vnet]--;

                // Enqueue it - for all outgoing queues
                for (int i=0; i<output_links.size(); i++) {
                    int outgoing = output_links[i];

                    if (i > 0) {
                        // create a private copy of the unmodified message
                        msg_ptr = unmodified_msg_ptr->clone();
                    }

                    // Change the internal destination set of the message so it
                    // knows which destinations this link is responsible for.
                    net_msg_ptr = safe_cast<NetworkMessage*>(msg_ptr.get());
                    net_msg_ptr->getInternalDestination() =
                        output_link_destinations[i];

                    // Enqeue msg
                    DPRINTF(RubyNetwork, "Enqueuing net msg from "
                            "inport[%d][%d] to outport [%d][%d].\n",
                            incoming, vnet, outgoing, vnet);

                    m_out[outgoing][vnet]->enqueue(msg_ptr);
                }
            }
        }
    }
}

void
TopazSwitchFlow::storeEventInfo(int info)
{
    m_pending_message_count[info]++;
}


void
TopazSwitchFlow::clearStats()
{
  //cout << "TopazSwitchFlow printStats" << endl;
}

void
TopazSwitchFlow::collateStats()
{
}

void
TopazSwitchFlow::printConfig(std::ostream& out) const
{
}

void
TopazSwitchFlow::print(std::ostream& out) const
{
  cout << "[TopazSwitchFlow " << m_switch_id << "]";
}
