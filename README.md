## **Gem5 _NoSQL_** [(CE Group - UC)](http://www.ce.unican.es)

This is the gem5 simulator, adapted by CE group from University of Cantabria.  

The main website can be found at http://www.gem5.org

A good starting point is http://www.gem5.org/Introduction, and for
more information about building the simulator and getting started
please see https://github.com/abadp/gem5-NoSQL/wiki

To build gem5, you will need the following software: g++ or clang,
Python (gem5 links in the Python interpreter), SCons, SWIG, zlib, m4,
and lastly protobuf if you want trace capture and playback
support. Please see http://www.gem5.org/Dependencies for more details
concerning the minimum versions of the aforementioned tools.

Once you have all dependencies resolved, type 'scons
build/<ARCH>/gem5.opt' where ARCH is one of ALPHA, ARM, NULL, MIPS,
POWER, SPARC, or X86. This will build an optimized version of the gem5
binary (gem5.opt) for the the specified architecture. See
http://www.gem5.org/Build_System for more details and options.

The basic source release includes these subdirectories:
   - atc_scripts: disk images generation scripts for run YCSB/Cassandra workloads  
   - configs: example simulation configuration scripts
   - ext: less-common external packages needed to build gem5
   - src: source code of the gem5 simulator
   - system: source for some optional system software for simulated systems
   - tests: regression tests
   - util: useful utility programs and files
   - images: kernel file and disk images 
   - nosql: Cassandra and YSCB source (adapted) 

If you have questions, please send mail to abadp@unican.es

Enjoy!.
