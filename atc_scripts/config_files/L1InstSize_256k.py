memory_config = {
  #Memory
  'mem-type'             : 'SimpleMemory',
  'mem-channels'         : '4',

  #Icache
  'l1i_size'             : '256kB',  #OK
  'l1i_assoc'            : '64',     #OK
  'l1i_hit_latency'      : '1',
  'l1i_response_latency' : '1',
  'l1i_mshrs'            : '4',
  'l1i_tgts_per_mshr'    : '8',

  #Dcache
  'l1d_size'             : '32kB',  #OK
  'l1d_assoc'            : '4',     #OK
  'l1d_hit_latency'      : '1',     #OK
  'l1d_response_latency' : '1',     #MISS: Hit_lat + (Next level access) + Resp_lat. Always uses parallel access
  'l1d_mshrs'            : '16',
  'l1d_tgts_per_mshr'    : '8',

  'l2_size'             : '32MB', #OK
  'l2_assoc'            : '8',     #OK
  'l2_hit_latency'      : '6',    #OK
  'l2_response_latency' : '3',
  'l2_mshrs'            : '16',
  'l2_tgts_per_mshr'    : '8',
}
