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
 * Authors: Adrian Colaso
 */

/* @file
 * Implementation of a yags branch predictor
 */

#include "base/bitfield.hh"
#include "base/intmath.hh"
#include "cpu/pred/yags.hh"

YagsBP::YagsBP(const YagsBPParams *params)
    : BPredUnit(params), instShiftAmt(params->instShiftAmt),
      globalHistoryReg(params->numThreads, 0),
      globalHistoryBits(ceilLog2(params->globalPredictorSize)),
      choicePredictorSize(params->choicePredictorSize),
      choiceCtrBits(params->choiceCtrBits),
      globalPredictorSize(params->globalPredictorSize),
      globalCtrBits(params->globalCtrBits),
      globalTagBits(params->globalTagBits)
{
    if (!isPowerOf2(choicePredictorSize))
        fatal("Invalid choice predictor size.\n");
    if (!isPowerOf2(globalPredictorSize))
        fatal("Invalid global history predictor size.\n");

    cprintf("YAGS predictor\n");
    cprintf("  Choice entries: %d Sat counter bits: %d\n",choicePredictorSize, choiceCtrBits);
    cprintf("  Taken cache entries: %d Tag bits: %d Sat counter bits: %d\n",globalPredictorSize,globalTagBits,globalCtrBits);
    cprintf("  Not taken cache entries: %d Tag bits: %d Sat counter bits: %d\n",globalPredictorSize,globalTagBits,globalCtrBits);

    choiceCounters.resize(choicePredictorSize);
    takenCounters.resize(globalPredictorSize);
    takenTags.resize(globalPredictorSize);
    notTakenCounters.resize(globalPredictorSize);
    notTakenTags.resize(globalPredictorSize);

    for (int i = 0; i < choicePredictorSize; ++i) {
        choiceCounters[i].setBits(choiceCtrBits);
        choiceCounters[i].set(1);
    }
    for (int i = 0; i < globalPredictorSize; ++i) {
        takenCounters[i].setBits(globalCtrBits);
        takenTags[i] = 0;
        notTakenCounters[i].setBits(globalCtrBits);
        notTakenTags[i] = 0;
    }

    historyRegisterMask = mask(globalHistoryBits);
    choiceHistoryMask = choicePredictorSize - 1;
    globalHistoryMask = globalPredictorSize - 1;
    globalTagMask = mask(globalTagBits);
}

/*
 * For an unconditional branch we set its history such that
 * everything is set to taken. I.e., its choice predictor
 * chooses the taken array and the taken array predicts taken.
 */
void
YagsBP::uncondBranch(ThreadID tid, Addr pc, void * &bpHistory)
{
    BPHistory *history = new BPHistory;
    history->globalHistoryReg = globalHistoryReg[tid];
    history->choicePred = true;
    history->takenEntry = false;
    history->notTakenEntry = false;
    history->finalPred = true;
    bpHistory = static_cast<void*>(history);
    updateGlobalHistReg(tid, true);
}

/*
 *  We just need to restore globalHistoryReg.
 */
void
YagsBP::squash(ThreadID tid, void *bpHistory)
{
    BPHistory *history = static_cast<BPHistory*>(bpHistory);
    globalHistoryReg[tid] = history->globalHistoryReg;

    delete history;
}

/*
 * First, choice PHT is accessed using branch's PC as index. If PHT predicts taken,
 * not taken cache is accessed using a hash of the global history register and a branch's
 * PC as index. If there is a miss PHT prediction is used as final prediction. If not,
 * not taken cache prediction is used as final prediction. Taken cache is accessed when
 * PHT predicts not taken.
 */
bool
YagsBP::lookup(ThreadID tid, Addr branchAddr, void * &bpHistory)
{
    unsigned choiceHistoryIdx = ((branchAddr >> instShiftAmt)
                                & choiceHistoryMask);

    unsigned globalHistoryIdx = (((branchAddr >> instShiftAmt)
                                ^ globalHistoryReg[tid])
                                & globalHistoryMask);

    assert(choiceHistoryIdx < choicePredictorSize);
    assert(globalHistoryIdx < globalPredictorSize);

    bool choicePrediction = choiceCounters[choiceHistoryIdx].read() >> (choiceCtrBits - 1);

    bool finalPrediction;

    BPHistory *history = new BPHistory;
    history->globalHistoryReg = globalHistoryReg[tid];
    history->choicePred = choicePrediction;

    if (choicePrediction) {
        if (notTakenTags[globalHistoryIdx] == (branchAddr & globalTagMask)) {
            finalPrediction = notTakenCounters[globalHistoryIdx].read() >> (globalCtrBits - 1);
            history->notTakenEntry = true;
            history->takenEntry = false;
        }else{
            finalPrediction = choicePrediction;
            history->notTakenEntry = false;
            history->takenEntry = false;
        }
    } else {
        if (takenTags[globalHistoryIdx] == (branchAddr & globalTagMask)) {
            finalPrediction = takenCounters[globalHistoryIdx].read() >> (globalCtrBits - 1);
            history->takenEntry = true;
            history->notTakenEntry = false;
        }else{
            finalPrediction = choicePrediction;
            history->takenEntry = false;
            history->notTakenEntry = false;
        }
    }

    history->finalPred = finalPrediction;
    bpHistory = static_cast<void*>(history);
    updateGlobalHistReg(tid, finalPrediction);

    return finalPrediction;
}

/*
 * There is a miss in BTB so change prediction to false not to stop
 * fetch stage. This is not the best option but it is the easiest.
 */
void
YagsBP::btbUpdate(ThreadID tid, Addr branchAddr, void * &bpHistory)
{
    globalHistoryReg[tid] &= (historyRegisterMask & ~ULL(1));
}

/*
 * The choice PHT is updated as in the bi-mode choice PHT. Not taken
 * cache is updated if there was a hit or if PHT predicts taken and
 * branch is not taken. Taken cache is updated if there was a hit
 * or if PHT predicts not taken and branch is taken.
 */
void
YagsBP::update(ThreadID tid, Addr branchAddr, bool taken, void *bpHistory, bool squashed)
{
    if (bpHistory) {
        BPHistory *history = static_cast<BPHistory*>(bpHistory);

        unsigned choiceHistoryIdx = ((branchAddr >> instShiftAmt)
                                    & choiceHistoryMask);

        unsigned globalHistoryIdx = (((branchAddr >> instShiftAmt)
                                    ^ history->globalHistoryReg)
                                    & globalHistoryMask);

        if(history->notTakenEntry && notTakenTags[globalHistoryIdx] != (branchAddr & globalTagMask)) {
            cprintf("Error al actualizar la cache not-taken %d\n",globalHistoryIdx);
        }

        if(history->takenEntry && takenTags[globalHistoryIdx] != (branchAddr & globalTagMask)) {
            cprintf("Error al actualizar la cache taken %d\n",globalHistoryIdx);
        }

        assert(choiceHistoryIdx < choicePredictorSize);
        assert(globalHistoryIdx < globalPredictorSize);

        if (history->choicePred) {
            if (notTakenTags[globalHistoryIdx] == (branchAddr & globalTagMask)) {
                //HIT, we used not taken cache prediction so we have to update it
                if (taken) {
                    notTakenCounters[globalHistoryIdx].increment();
                } else {
                    notTakenCounters[globalHistoryIdx].decrement();
                }
            }else if (!taken){
                //MISS, we used choice prediction and we mispredicted so add a new entry
                notTakenTags[globalHistoryIdx] = (branchAddr & globalTagMask);
                //Set weak not taken value to the new entry
                notTakenCounters[globalHistoryIdx].set(1 << (globalCtrBits - 1));
            }
        }else{
            if (takenTags[globalHistoryIdx] == (branchAddr & globalTagMask)) {
                //HIT, we used taken cache prediction so we have to update it
                if (taken) {
                    takenCounters[globalHistoryIdx].increment();
                } else {
                    takenCounters[globalHistoryIdx].decrement();
                }
            }else if (taken){
                //MISS, we used choice prediction and we mispredicted so add a new entry
                takenTags[globalHistoryIdx] = (branchAddr & globalTagMask);
                //Set weak taken value to the new entry
                takenCounters[globalHistoryIdx].set(mask(globalCtrBits) >> 1);
            }
        }

        //Choice update
        if (history->finalPred == taken) {
            /* If the final prediction matches the actual branch's
             * outcome and the choice predictor matches the final
             * outcome, we update the choice predictor, otherwise it
             * is not updated. While the designers of the bi-mode
             * predictor don't explicity say why this is done, one
             * can infer that it is to preserve the choice predictor's
             * bias with respect to the branch being predicted; afterall,
             * the whole point of the bi-mode predictor is to identify the
             * atypical case when a branch deviates from its bias.
             */
            if (history->finalPred == history->choicePred) {
                if (taken) {
                    choiceCounters[choiceHistoryIdx].increment();
                } else {
                    choiceCounters[choiceHistoryIdx].decrement();
                }
            }
        } else {
            // always update the choice predictor on an incorrect prediction
            if (taken) {
                choiceCounters[choiceHistoryIdx].increment();
            } else {
                choiceCounters[choiceHistoryIdx].decrement();
            }
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
YagsBP::retireSquashed(ThreadID tid, void *bp_history)
{
    BPHistory *history = static_cast<BPHistory*>(bp_history);
    delete history;
}

void
YagsBP::updateGlobalHistReg(ThreadID tid, bool taken)
{
    globalHistoryReg[tid] = taken ? (globalHistoryReg[tid] << 1) | 1 :
                               (globalHistoryReg[tid] << 1);
    globalHistoryReg[tid] &= historyRegisterMask;
}

YagsBP*
YagsBPParams::create()
{
    return new YagsBP(this);
}


