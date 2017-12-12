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
 *          Adrian Colaso
 */

/* @file
 * Implementation of a gshare branch predictor
 */

#include "base/bitfield.hh"
#include "base/intmath.hh"
#include "cpu/pred/gshare.hh"

GshareBP::GshareBP(const GshareBPParams *params)
    : BPredUnit(params), instShiftAmt(params->instShiftAmt),
      globalHistoryReg(params->numThreads, 0),
      globalHistoryBits(ceilLog2(params->globalPredictorSize)),
      globalPredictorSize(params->globalPredictorSize),
      globalCtrBits(params->globalCtrBits)
{
    if (!isPowerOf2(globalPredictorSize))
        fatal("Invalid global history predictor size.\n");

    counters.resize(globalPredictorSize);

    for (int i = 0; i < globalPredictorSize; ++i) {
        counters[i].setBits(globalCtrBits);
    }

    historyRegisterMask = mask(globalHistoryBits);
    globalHistoryMask = globalPredictorSize - 1;

    counterThreshold = (ULL(1) << (globalCtrBits - 1)) - 1;
}

/*
 * For an unconditional branch we just save globalHistoryReg.
 */
void
GshareBP::uncondBranch(ThreadID tid, Addr pc, void * &bpHistory)
{
    BPHistory *history = new BPHistory;
    history->globalHistoryReg = globalHistoryReg[tid];
    bpHistory = static_cast<void*>(history);
    updateGlobalHistReg(tid, true);
}

/*
 *  We just need to restore globalHistoryReg.
 */
void
GshareBP::squash(ThreadID tid, void *bpHistory)
{
    BPHistory *history = static_cast<BPHistory*>(bpHistory);
    globalHistoryReg[tid] = history->globalHistoryReg;

    delete history;
}

/*
 * A hash of the global history register and a branch's PC is used as index
 * to access the particular saturating counter that predicts the branch.
 */
bool
GshareBP::lookup(ThreadID tid, Addr branchAddr, void * &bpHistory)
{
    unsigned globalHistoryIdx = (((branchAddr >> instShiftAmt)
                                ^ globalHistoryReg[tid])
                                & globalHistoryMask);

    assert(globalHistoryIdx < globalPredictorSize);

    bool prediction = counters[globalHistoryIdx].read()
                              > counterThreshold;

    BPHistory *history = new BPHistory;
    history->globalHistoryReg = globalHistoryReg[tid];

    bpHistory = static_cast<void*>(history);
    updateGlobalHistReg(tid, prediction);

    return prediction;
}


/*
 * There is a miss in BTB so change prediction to false not to stop
 * fetch stage. This is not the best option but it is the easiest.
 */
void
GshareBP::btbUpdate(ThreadID tid, Addr branchAddr, void * &bpHistory)
{
    globalHistoryReg[tid] &= (historyRegisterMask & ~ULL(1));
}

/*
 * We have to update the corresponding saturating counter that
 * predicted the branch.
 */
void
GshareBP::update(ThreadID tid, Addr branchAddr, bool taken, void *bpHistory, bool squashed)
{
    if (bpHistory) {
        BPHistory *history = static_cast<BPHistory*>(bpHistory);

        unsigned globalHistoryIdx = (((branchAddr >> instShiftAmt)
                                    ^ history->globalHistoryReg)
                                    & globalHistoryMask);

        assert(globalHistoryIdx < globalPredictorSize);

        if (taken) {
            counters[globalHistoryIdx].increment();
        } else {
            counters[globalHistoryIdx].decrement();
        }

        if (squashed) {
            if (taken) {
                globalHistoryReg[tid] = (history->globalHistoryReg << 1) | 1;
            } else {
                globalHistoryReg[tid] = (history->globalHistoryReg << 1);
            }
            globalHistoryReg[tid] &= historyRegisterMask;
        } else {
            delete history;
        }
    }
}

void
GshareBP::retireSquashed(ThreadID tid, void *bp_history)
{
    BPHistory *history = static_cast<BPHistory*>(bp_history);
    delete history;
}

void
GshareBP::updateGlobalHistReg(ThreadID tid, bool taken)
{
    globalHistoryReg[tid] = taken ? (globalHistoryReg[tid] << 1) | 1 :
                               (globalHistoryReg[tid] << 1);
    globalHistoryReg[tid] &= historyRegisterMask;
}

GshareBP*
GshareBPParams::create()
{
    return new GshareBP(this);
}

