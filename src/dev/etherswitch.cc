/*
 * Copyright (c) 2014 The Regents of The University of Michigan
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
 *
 * Authors: Anthony Gutierrez
 */

/* @file
 * Device model for an ethernet switch
 */

#include "debug/EthernetAll.hh"
#include "dev/etherswitch.hh"

EtherSwitch::EtherSwitch(const Params *p)
    : EtherObject(p), delay(p->delay), switchFabric(name() + ".switchFabric",
      *this, p->fabric_speed), forwardEvent(&switchFabric),
      transmitEvent(&switchFabric)
{
    for (int i = 0; i < p->port_interface_connection_count; ++i) {
        std::string interfaceName = csprintf("%s.interface%d", name(), i);
        Interface *interface = new Interface(interfaceName, *this,
                                             p->input_buffer_size,
                                             p->output_buffer_size);
        interfaces.push_back(interface);
    }
    switchFabric.connectAllLinks(interfaces);
}

EtherSwitch::~EtherSwitch()
{
    for (auto it : interfaces)
        delete it;

    interfaces.clear();
}

EtherInt*
EtherSwitch::getEthPort(const std::string &if_name, int idx)
{
    if (idx < 0 || idx >= interfaces.size())
        return NULL;

    Interface *interface = interfaces.at(idx);
    panic_if(interface->getPeer(), "interface already connected\n");

    return interface;
}

// schedule the forwarding engine, which is responsible
// for figuring out which port to forward the packet to,
// or broadcasting the packet
void
EtherSwitch::scheduleForwarding()
{
    if (!forwardEvent.scheduled()) {
        DPRINTF(Ethernet, "scheduling forwarding engine\n");
        schedule(forwardEvent, curTick() + delay);
    }
}

// schedule the actual transmission of the packet to the
// receiving device
void
EtherSwitch::scheduleTransmit()
{
    if (!transmitEvent.scheduled()) {
        DPRINTF(Ethernet, "scheduling transmission engine\n");
        schedule(transmitEvent, curTick() + delay);
    }
}

EtherSwitch::Interface::Interface(const std::string &name,
                                  EtherSwitch &_etherSwitch,
                                  int inputBufferSize, int outputBufferSize)
    : EtherInt(name), numBroadcasting(0), etherSwitch(_etherSwitch),
      inputFifo(inputBufferSize), outputFifo(outputBufferSize)
{
}

// when a packet is received from a device just store
// it in an input queue until it can be forwarded
bool
EtherSwitch::Interface::recvPacket(EthPacketPtr packet)
{
    DPRINTF(Ethernet, "received packet\n");
    if (inputFifo.push(packet)) {
        DPRINTF(Ethernet, "adding packet to input queue\n");
        etherSwitch.scheduleForwarding();
        return true;
    } else {
        DPRINTF(Ethernet, "input fifo for interface %s full, "
                "dropping packet.\n", name());
        return false;
    }
}

// don't actually send a packet here. once a packet
// makes it through a fabric link, put it in
// an output queue
bool
EtherSwitch::Interface::sendPacket(EthPacketPtr packet)
{
    DPRINTF(Ethernet, "sending packet\n");
    if (outputFifo.push(packet)) {
        DPRINTF(Ethernet, "pushing packet into output queue\n");
        etherSwitch.scheduleTransmit();
        return true;
    } else {
        DPRINTF(Ethernet, "output fifo full; dropping packet.\n");
        return false;
    }
}

// this is where we actually send a packet to the
// receiving device
void
EtherSwitch::Interface::sendQueuedPacket()
{
    if (outputFifo.empty())
        return;

    if (peer->recvPacket(outputFifo.front()))
        outputFifo.pop();
}

EthPacketPtr
EtherSwitch::Interface::getInputPacket()
{
    if (inputFifo.empty())
        return NULL;

    return inputFifo.front();
}

// if a packet was successfully sent then pop it from
// from the input queue
void
EtherSwitch::Interface::sendDone()
{
    if (broadcasting())
        --numBroadcasting;

    if (broadcasting()) {
        DPRINTF(Ethernet, "packet sent, but port is still broadcasting "
                "don't pop the queue\n");
    } else {
        DPRINTF(Ethernet, "packet sent, popping input fifo\n");
        popInputPacket();
    }
}

EtherSwitch::EtherFabric::EtherFabric(const std::string &name,
                                      EtherSwitch &_etherSwitch, double rate)
    : fabricName(name), etherSwitch(_etherSwitch), ticksPerByte(rate),
      interfaces(NULL)
{
}

EtherSwitch::EtherFabric::~EtherFabric()
{
    for (auto it : fabricLinks)
        delete it.second;

    fabricLinks.clear();
}

// connect rx and tx links in a point-to-point fashion for
// each port on the switch. there will always be n*(n-1) links.
// this essentially creates the switch fabric
void
EtherSwitch::EtherFabric::connectAllLinks(std::vector<Interface*> &_interfaces)
{
    interfaces = &_interfaces;
    int linkNum = 0;

    for (auto itr1 : *interfaces) {
        for (auto itr2 : *interfaces) {
            if (itr1 == itr2)
                continue;
            std::string linkName = csprintf("%s.link%d", name(), linkNum);
            EtherLink::Link *link = new EtherLink::Link(linkName,
                                              &etherSwitch,
                                              linkNum, ticksPerByte,
                                              etherSwitch.params()->delay,
                                              etherSwitch.params()->delay_var,
                                              etherSwitch.params()->dump);
            link->setTxInt(itr1);
            link->setRxInt(itr2);
            std::pair<Interface*, Interface*> intPair
                = std::make_pair(itr1, itr2);

            DPRINTF(Ethernet, "connecting port %s and port %s "
                    "over link %x\n", itr1->name(), itr2->name(),
                    link->name());
            fabricLinks.insert(std::pair<std::pair<Interface*, Interface*>,
                               EtherLink::Link*>(intPair, link));
            ++linkNum;
        }
    }
}

// for each input queue forward along or broadcast any
// packets they may have, assuming the links are not busy.
void
EtherSwitch::EtherFabric::forwardingEngine()
{
    Interface *receiver;
    Interface *sender;

    // we use a temporary vector copy of interfaces because
    // the objects in interfaces may be moved around in the
    // for loop, i.e., the copy is used to ensure the iterators
    // remain valid after rearranging the vector
    std::vector<Interface*> tmpInterfaces(*interfaces);

    DPRINTF(Ethernet, "forwarding packets over fabric\n");

    for (auto it : tmpInterfaces) {
        sender = it;
        EthPacketPtr packet = sender->getInputPacket();

        if (!packet)
            continue;

        uint8_t srcAddr[ETH_ADDR_LEN];
        uint8_t destAddr[ETH_ADDR_LEN];
        memcpy(srcAddr, &packet->data[6], ETH_ADDR_LEN);
        memcpy(destAddr, packet->data, ETH_ADDR_LEN);
        Net::EthAddr destMacAddr(destAddr);
        Net::EthAddr srcMacAddr(srcAddr);

        learnSenderAddr(srcMacAddr, sender);
        receiver = lookupDestPort(destMacAddr);

        if (!receiver || destMacAddr.multicast() || destMacAddr.broadcast()) {
            broadcast(packet, sender);
        } else {
            DPRINTF(Ethernet, "sending packet from MAC %x on port "
                    "%s to MAC %x on port %s\n", uint64_t(srcMacAddr),
                    sender->name(), uint64_t(destMacAddr), receiver->name());
            auto linkItr = fabricLinks.find(std::make_pair(sender, receiver));
            assert(linkItr != fabricLinks.end());
            bool sent = linkItr->second->transmit(packet);
            if (sent)
                updateLRG(sender);
        }
    }
}

// send any outgoing packets along to their receiving
// device, assuming the link is not busy
void
EtherSwitch::EtherFabric::transmissionEngine()
{
    DPRINTF(Ethernet, "transmitting packets to destination\n");

    for (auto it : *interfaces)
        it->sendQueuedPacket();
}

// try to find which port a device (MAC) is associated with
EtherSwitch::Interface*
EtherSwitch::EtherFabric::lookupDestPort(Net::EthAddr destMacAddr)
{
    auto it = forwardingTable.find(uint64_t(destMacAddr));

    if (it == forwardingTable.end()) {
        DPRINTF(Ethernet, "no entry in forwaring table for MAC: "
                "%x\n", uint64_t(destMacAddr));
        return NULL;
    }

    DPRINTF(Ethernet, "found entry for MAC address %x on port %s\n",
            uint64_t(destMacAddr), it->second.interface->name());
    return it->second.interface;
}

// cache the MAC address for the device connected to
// a given port
void
EtherSwitch::EtherFabric::learnSenderAddr(Net::EthAddr srcMacAddr,
                                          Interface *sender)
{
    // learn the port for the sending MAC address
    auto it = forwardingTable.find(uint64_t(srcMacAddr));

    // if the port for sender's MAC address is not cached,
    // cache it now, otherwise just update arrival time
    if (it == forwardingTable.end()) {
        DPRINTF(Ethernet, "adding forwarding table entry for MAC "
                " address %x on port %s\n", uint64_t(srcMacAddr),
                sender->name());
        SwitchTableEntry forwardingTableEntry;
        forwardingTableEntry.interface = sender;
        forwardingTableEntry.arrivalTime = curTick();
        forwardingTable.insert(std::pair<uint64_t, SwitchTableEntry>(
            uint64_t(srcMacAddr), forwardingTableEntry));
    } else {
        it->second.arrivalTime = curTick();
    }
    // should also schedule the removal of an entry after it's TTL expires
}

// this provides for a simple arbitration policy. to avoid
// starvation the ports are allowed to send packets in least-
// recenty-granted order (LRG). when a port is allowed to send
// a packet, it is set to the most-recently-granted position.
// on arbitration the port in the LRG position is chosen to
// send a packet first
void
EtherSwitch::EtherFabric::updateLRG(Interface *interface)
{
    int i = interfaces->size() - 1;
    Interface *next = interface;

    DPRINTF(Ethernet, "moving interface %s to MRG\n",
            interface->name());

    do {
        assert(i >= 0);
        Interface *tmp = interfaces->at(i);
        interfaces->at(i) = next;
        next = tmp;
        --i;
    } while (next != interface);
}

// broadcast a packet to all ports without allowing any loopback
void
EtherSwitch::EtherFabric::broadcast(EthPacketPtr packet, Interface *sender)
{
    // if this port didn't finish broadcasting previosly,
    // pick up where it left off by trying to send the packet
    // to the remaining ports
    if (sender->broadcasting()) {
        DPRINTF(Ethernet, "port already broadcasting; try again later\n");
        std::vector<Interface*> peers = sender->getBroadcastPeers();

        if (peers.empty())
            return;

        auto begin = peers.begin();
        auto end = peers.end();
        auto it = begin;

        while (it != end) {
            auto linkItr = fabricLinks.find(std::make_pair(sender, *it));
            assert(linkItr != fabricLinks.end());
            EtherLink::Link *link = linkItr->second;
            if (link->transmit(packet)) {
                DPRINTF(Ethernet, "broadcast to link %s complete\n",
                        link->name());
                it = peers.erase(it);
            } else {
                DPRINTF(Ethernet, "broadcast to link %s unable to complete; "
                        "try again later\n", link->name());
                ++it;
            }
        }
    } else {
        for (auto it : *interfaces) {
            if (it == sender)
                continue;

            auto linkItr = fabricLinks.find(std::make_pair(sender, it));
            assert(linkItr != fabricLinks.end());
            EtherLink::Link *link = linkItr->second;
            DPRINTF(Ethernet, "broadcasting from port %s to port %s "
                    "over link %s\n", sender->name(), it->name(), link->name());
            if (!link->transmit(packet)) {
                DPRINTF(Ethernet, "broadcast unable to complete, "
                        "retry later\n");
                sender->getBroadcastPeers().push_back(it);
            }
            sender->incNumBroadcasting();
        }
    }
}

EtherSwitch *
EtherSwitchParams::create()
{
    return new EtherSwitch(this);
}
