system_default = {
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
  #'l3cache'            :        None
}

processor_default = {
  #(Parameter, Value)
  'cachePorts'             :  '200',          #Cache Ports
  'fetchWidth'             :  '8',            #Fetch width
  'decodeWidth'            :  '8',            #Decode width
  'renameWidth'            :  '8',            #Rename width
  'dispatchWidth'          :  '8',            #Dispatch width
  'issueWidth'             :  '8',            #Issue width
  'wbWidth'                :  '8',            #Writeback width
  'commitWidth'            :  '8',            #Commit width
  'squashWidth'            :  '8',            #Squash width
  'LQEntries'              :  '32',           #Number of load queue entries
  'SQEntries'              :  '32',           #Number of store queue entries
}

branch_pred_default = {
  'BTBEntries'             :  '4096',         #Number of BTB entries
  'BTBTagSize'             :  '16',           #Size of the BTB tags, in bits
  'RASSize'                :  '16',           #RAS size
  'instShiftAmt'           :  '2',
}

memory_default = {
  'mem-type'               :  'SimpleMemory',  #This is DRAM config not CMP hierarchy
  'mem-channels'           :  '1',
  'cacheline_size'         :  '64',
  'l1d_size'               :  '64kB',  #Dcache
  'l1d_assoc'              :  '2',
  'l1d_hit_latency'        :  '2',
  'l1d_response_latency'   :  '2',
  'l1d_mshrs'              :  '4',
  'l1d_tgts_per_mshr'      :  '20',
  'l1i_size'               :  '32kB',  #Icache
  'l1i_assoc'              :  '2',
  'l1i_hit_latency'        :  '2',
  'l1i_response_latency'   :  '2',
  'l1i_mshrs'              :  '4',
  'l1i_tgts_per_mshr'      :  '20',
  'l2_size'                :  '512kB', #L2
  'l2_assoc'               :  '8',
  'l2_hit_latency'         :  '20',
  'l2_response_latency'    :  '20',
  'l2_mshrs'               :  '20',
  'l2_tgts_per_mshr'       :  '12',
  #'l3_size'                :  '8MB',   #L3
  #'l3_assoc'               :  '16',
  #'l3_hit_latency'         :  '50',
  #'l3_response_latency'    :  '50',
  #'l3_mshrs'               :  '20',
  #'l3_tgts_per_mshr'       :  '16',
  #
  # TODO: Topaz options
  #
}
