system_config = {
  'num-cpus'           :	'$SGE_cpus',  #Top level loop uses 6th param from config.list
  'num-dirs'           :    '$SGE_cpus',  #Subject to change with NUCA
  'cpu-type'           :	'atomic',   #If !=detailed, over-writes O3
  #'restore-with-cpu'   :	'atomic',     #Ruby requires at least timming
  'sys-clock'          :	'1.25GHz',
  'cpu-clock'          :	'3.5GHz',
  'sys-voltage'        :	'1.0V',
  #'ruby'              :        None,         #IF presnet use ruby
  'caches'             :        None,         #Either Ruby or those three lines
}