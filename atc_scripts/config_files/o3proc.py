system_config = {
  'num-cpus'           :	'$SGE_cpus',  #Top level loop uses 6th param from config.list
  'num-l2caches'       :	'$SGE_cpus',  #Subject to change with NUCA
  'num-dirs'           :        '$SGE_cpus',  #Subject to change with NUCA
  'cpu-type'           :	'detailed',   #If !=detailed, over-writes O3
  'restore-with-cpu'   :	'timing',     #Ruby requires at least timming
  'sys-clock'          :	'1.25GHz',
  'cpu-clock'          :	'3.5GHz',
  'sys-voltage'        :	'1.0V',
  #'ruby'              :        None,         #IF presnet use ruby
  'caches'             :        None,         #Either Ruby or those three lines
  'l2cache'            :        None,         # to use detailed with clasic memory
  'l3cache'            :        None
}

processor_config = {
  #(Parameter, Value)
  'cachePorts'             :  '200',          #Cache Ports
  'decodeToFetchDelay'     :  '1',            #Decode to fetch delay
  'renameToFetchDelay'     :  '1',            #Rename to fetch delay
  'iewToFetchDelay'        :  '1',            #Issue/Execute/Writeback to fetch delay
  'commitToFetchDelay'     :  '1',            #Commit to fetch delay
  'fetchWidth'             :  '4',            #Fetch width
  'renameToDecodeDelay'    :  '1',            #Rename to decode delay
  'iewToDecodeDelay'       :  '1',            #Issue/Execute/Writeback to decode delay
  'commitToDecodeDelay'    :  '1',            #Commit to decode delay
  'fetchToDecodeDelay'     :  '1',            #Fetch to decode delay
  'decodeWidth'            :  '4',            #Decode width
  'iewToRenameDelay'       :  '1',            #Issue/Execute/Writeback to rename delay
  'commitToRenameDelay'    :  '1',            #Commit to rename delay
  'decodeToRenameDelay'    :  '1',            #Decode to rename delay
  'renameWidth'            :  '4',            #Rename width
  'commitToIEWDelay'       :  '1',            #Commit to Issue/Execute/Writeback delay
  'renameToIEWDelay'       :  '2',            #Rename to Issue/Execute/Writeback delay
  'issueToExecuteDelay'    :  '1',            #Issue to execute delay  internal to the IEW stage]
  'dispatchWidth'          :  '4',            #Dispatch width
  'issueWidth'             :  '4',            #Issue width
  'wbWidth'                :  '4',            #Writeback width
  'iewToCommitDelay'       :  '1',            #Issue/Execute/Writeback to commit delay
  'renameToROBDelay'       :  '1',            #Rename to reorder buffer delay
  'commitWidth'            :  '4',            #Commit width
  'squashWidth'            :  '4',            #Squash width
  'trapLatency'            :  '13',           #Trap latency
  'fetchTrapLatency'       :  '1',            #Fetch trap latency
  'backComSize'            :  '5',            #Time buffer size for backwards communication
  'forwardComSize'         :  '5',            #Time buffer size for forward communication
  'LQEntries'              :  '64',           #Number of load queue entries
  'SQEntries'              :  '64',           #Number of store queue entries
  'LSQDepCheckShift'       :  '4',            #Number of places to shift addr before check
  'LSQCheckLoads'          :  'True',         #Should dependency violations be checked for loads & stores or just stores
  'store_set_clear_period' :  '250000',       #Number of load/store insts before the dep predictor should be invalidated
  'LFSTSize'               :  '1024',         #Last fetched store table size
  'SSITSize'               :  '1024',         #Store set ID table size
  'numRobs'                :  '1',            #Number of Reorder Buffers
  'numPhysIntRegs'         :  '256',          #Number of physical integer registers
  'numPhysFloatRegs'       :  '256',          #Number of physical floating point registers
  'numIQEntries'           :  '128',           #Number of instruction queue entries
  'numROBEntries'          :  '192',          #Number of reorder buffer entries
  'smtNumFetchingThreads'  :  '1',            #SMT Number of Fetching Threads
  'smtFetchPolicy'         :  'SingleThread', #SMT Fetch policy
  'smtLSQPolicy'           :  'Partitioned',  #SMT LSQ Sharing Policy
  'smtLSQThreshold'        :  '100',          #SMT LSQ Threshold Sharing Parameter
  'smtIQPolicy'            :  'Partitioned',  #SMT IQ Sharing Policy
  'smtIQThreshold'         :  '100',          #SMT IQ Threshold Sharing Parameter
  'smtROBPolicy'           :  'Partitioned',  #SMT ROB Sharing Policy
  'smtROBThreshold'        :  '100',          #SMT ROB Threshold Sharing Parameter
  'smtCommitPolicy'        :  'RoundRobin',   #SMT Commit Policy
}

memory_config = {
  #Memory
  'mem-type'             : 'SimpleMemory',
  'mem-channels'         : '4',

  #Icache
  'l1i_size'             : '32kB',  #OK
  'l1i_assoc'            : '4',     #OK
  'l1i_hit_latency'      : '1',
  'l1i_response_latency' : '1',
  'l1i_mshrs'            : '4',
  'l1i_tgts_per_mshr'    : '16',

  #Dcache
  'l1d_size'             : '32kB',  #OK
  'l1d_assoc'            : '4',     #OK
  'l1d_hit_latency'      : '1',     #OK
  'l1d_response_latency' : '1',     #MISS: Hit_lat + (Next level access) + Resp_lat. Always uses parallel access
  'l1d_mshrs'            : '32',
  'l1d_tgts_per_mshr'    : '16',

  'l2_size'             : '256kB', #OK
  'l2_assoc'            : '8',     #OK
  'l2_hit_latency'      : '6',    #OK
  'l2_response_latency' : '3',
  'l2_mshrs'            : '32',
  'l2_tgts_per_mshr'    : '16',

  'l3_size'                :  '8MB',   #L3
  'l3_assoc'               :  '16',
  'l3_hit_latency'         :  '20',
  'l3_response_latency'    :  '20',
  'l3_mshrs'               :  '32',
  'l3_tgts_per_mshr'       :  '16',
}