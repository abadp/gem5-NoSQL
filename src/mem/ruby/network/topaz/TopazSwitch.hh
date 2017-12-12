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

/*
 * The actual modelled switch. It use the perfect switch and a
 * Throttle object to control and bandwidth and timing *only for the
 * output port*. So here we have un-realistic modelling, since the
 * order of PerfectSwitch and Throttle objects get woke up affect the
 * message timing. A more accurate model would be having two set of
 * system states, one for this cycle, one for next cycle. And on the
 * cycle boundary swap the two set of states.
 */

#ifndef __MEM_RUBY_NETWORK_TOPAZSWITCH_HH__
#define __MEM_RUBY_NETWORK_TOPAZSWITCH_HH__

#include <iostream>
#include <vector>

#include "mem/ruby/common/Global.hh"
#include "mem/packet.hh"
#include "mem/protocol/MessageSizeType.hh"
#include "mem/ruby/common/TypeDefines.hh"
#include "mem/ruby/network/BasicRouter.hh"
#include "params/TopazSwitch.hh"

class MessageBuffer;
class TopazSwitchFlow;
class NetDest;
class TopazNetwork;
class Throttle;

class TopazSwitch : public BasicRouter
{
  public:
    typedef TopazSwitchParams Params;
    TopazSwitch(const Params *p);
    ~TopazSwitch();

    void init();
    void addInPort(const std::vector<MessageBuffer*>& in);
    void addOutPort(const std::vector<MessageBuffer*>& out,
                const NetDest& routing_table_entry,
                Cycles link_latency, int bw_multiplier);

    const Throttle* getThrottle(LinkID link_number) const;
    const std::vector<Throttle*>* getThrottles() const;

    void resetStats();
    void collateStats();
    void regStats();
    const Stats::Formula & getMsgCount(unsigned int type) const
    { return m_msg_counts[type]; }

    void print(std::ostream& out) const;
    void init_net_ptr(TopazNetwork* net_ptr) { m_network_ptr = net_ptr; }

    bool functionalRead(Packet *);
    uint32_t functionalWrite(Packet *);

  private:
    // Private copy constructor and assignment operator
    TopazSwitch(const TopazSwitch& obj);
    TopazSwitch& operator=(const TopazSwitch& obj);

    TopazSwitchFlow* m_perfect_switch_ptr;
    TopazNetwork* m_network_ptr;
    std::vector<Throttle*> m_throttles;
    std::vector<MessageBuffer*> m_buffers_to_free;
    Stats::Formula m_avg_utilization;


    Stats::Formula m_msg_counts[MessageSizeType_NUM];
    Stats::Formula m_msg_bytes[MessageSizeType_NUM];
};

inline std::ostream&
operator<<(std::ostream& out, const TopazSwitch& obj)
{
    obj.print(out);
    out << std::flush;
    return out;
}

#endif // __MEM_RUBY_NETWORK_TOPAZ_SWITCH_HH__
