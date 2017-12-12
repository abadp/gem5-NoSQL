/*
 * Copyright (c) 2012-2013 ARM Limited
 * All rights reserved.
 *
 * The license below extends only to copyright in the software and shall
 * not be construed as granting a license to any other intellectual
 * property including but not limited to intellectual property relating
 * to a hardware implementation of the functionality of the software
 * licensed hereunder.  You may use the software subject to the license
 * terms below provided that you ensure that this notice is replicated
 * unmodified and in its entirety in all distributions of the software,
 * modified or unmodified, in source code or in binary form.
 *
 * Copyright (c) 2003-2005,2014 The Regents of The University of Michigan
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
 * Authors: Erik Hallnor
 */

/**
 * @file
 * Definitions of a SRRIP tag store.
 */

#include "mem/cache/tags/srrip.hh"

#include "debug/CacheRepl.hh"
#include "mem/cache/base.hh"

SRRIP::SRRIP(const Params *p)
    : BaseSetAssoc(p)
{
}

CacheBlk*
SRRIP::accessBlock(Addr addr, bool is_secure, Cycles &lat, int master_id)
{
    CacheBlk *blk = BaseSetAssoc::accessBlock(addr, is_secure, lat, master_id);

    if (blk != nullptr) {
        // this is a hit, set RRPV of block to 0
        sets[blk->set].moveToHead(blk);
        blk->rrpv = 0;
        DPRINTF(CacheRepl, "set %x: updating rrpv of blk %x (%s) to 0\n",
                blk->set, regenerateBlkAddr(blk->tag, blk->set),
                is_secure ? "s" : "ns");
    }

    return blk;
}

CacheBlk*
SRRIP::findVictim(Addr addr)
{
    int set = extractSet(addr);
    // grab a replacement candidate
    BlkType *blk = nullptr;

    for (int j = 0; j < 4; j++) {
        for (int i = assoc - 1; i >= 0; i--) {
            BlkType *b = sets[set].blks[i];
            assert(b->rrpv < 4);
            if (b->rrpv == 3) {
                blk = b;
                break;
            }
        }
        if (!blk) {
            for (int i = assoc - 1; i >= 0; i--) {
                BlkType *b = sets[set].blks[i];
                b->rrpv++;
            }
        }
        else {
            break;
        }
    }

    assert(!blk || blk->way < allocAssoc);

    if (blk && blk->isValid()) {
        DPRINTF(CacheRepl, "set %x: selecting blk %x for replacement\n",
                set, regenerateBlkAddr(blk->tag, set));
    }

    return blk;
}

void
SRRIP::insertBlock(PacketPtr pkt, BlkType *blk)
{
    BaseSetAssoc::insertBlock(pkt, blk);

    int set = extractSet(pkt->getAddr());
    blk->rrpv = 2;
    sets[set].moveToHead(blk);
}

void
SRRIP::invalidate(CacheBlk *blk)
{
    BaseSetAssoc::invalidate(blk);

    // should be evicted before valid blocks
    int set = blk->set;
    blk->rrpv = 3;
    sets[set].moveToTail(blk);
}

SRRIP*
SRRIPParams::create()
{
    return new SRRIP(this);
}
