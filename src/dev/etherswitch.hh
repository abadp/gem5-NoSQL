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

#ifndef __DEV_ETHERSWITCH_HH__
#define __DEV_ETHERSWITCH_HH__

#include "base/inet.hh"
#include "dev/etherint.hh"
#include "dev/etherlink.hh"
#include "dev/etherobject.hh"
#include "dev/etherpkt.hh"
#include "dev/pktfifo.hh"
#include "params/EtherSwitch.hh"
#include "sim/eventq.hh"

class EtherSwitch : public EtherObject
{
  public:
    typedef EtherSwitchParams Params;

    EtherSwitch(const Params *p);
    virtual ~EtherSwitch();

    const Params * params() const
    {
        return dynamic_cast<const Params*>(_params);
    }

    virtual EtherInt *getEthPort(const std::string &if_name, int idx);
    void scheduleForwarding();
    void scheduleTransmit();

  protected:
    class Interface : public EtherInt
    {
      public:
        Interface(const std::string &name, EtherSwitch &_etherSwitch,
                  int inputBufferSize, int outputBufferSize);
        bool recvPacket(EthPacketPtr packet);
        bool sendPacket(EthPacketPtr Packet);
        void sendQueuedPacket();
        EthPacketPtr getInputPacket();
        void popInputPacket() { inputFifo.pop(); }
        void sendDone();
        bool isBusy() const { return inputFifo.full(); }
        bool inputFifoEmpty() const { return inputFifo.empty(); }
        bool outputFifoEmpty() const { return outputFifo.empty(); }
        bool broadcasting() const { return numBroadcasting; }
        std::vector<Interface*>& getBroadcastPeers() { return broadcastPeers; }
        void incNumBroadcasting() { ++numBroadcasting; }

      private:
        // how many ports need to receive a packet on a broadcast
        int numBroadcasting;
        std::vector<Interface*> broadcastPeers;
        EtherSwitch &etherSwitch;
        PacketFifo inputFifo;
        PacketFifo outputFifo;
    };

    class EtherFabric
    {
      public:
        EtherFabric(const std::string &name, EtherSwitch &_etherSwitch,
                    double rate);
        ~EtherFabric();
        const std::string &name() const { return fabricName; }
        void connectAllLinks(std::vector<Interface*> &_interfaces);
        void forwardingEngine();
        void transmissionEngine();
        Interface* lookupDestPort(Net::EthAddr destAddr);
        void learnSenderAddr(Net::EthAddr srcAddr, Interface* sender);
        void updateLRG(Interface *interface);
        void broadcast(EthPacketPtr packet, Interface *sender);

      protected:
        struct SwitchTableEntry {
            Interface *interface;
            Tick arrivalTime;
        };

      private:
        std::string fabricName;
        EtherSwitch &etherSwitch;
        // fabric speed
        double ticksPerByte;
        // table that maps MAC address to interfaces
        std::map<uint64_t, SwitchTableEntry> forwardingTable;
        // the actual fabric, i.e., this holds all the
        // point-to-point links
        std::map<std::pair<Interface*, Interface*>,
                 EtherLink::Link*> fabricLinks;
        // maintain a least recently granted (LRG) ordering
        // of the ports for arbitration
        std::vector<Interface*> *interfaces;
    };

  private:
    int delay;
    // actual switching fabric
    EtherFabric switchFabric;
    //forwarding and transmit events
    EventWrapper<EtherFabric, &EtherFabric::forwardingEngine> forwardEvent;
    EventWrapper<EtherFabric, &EtherFabric::transmissionEngine> transmitEvent;
    // all interfaces of the switch
    std::vector<Interface*> interfaces;
};

#endif // __DEV_ETHERSWITCH_HH__
