#!/usr/bin/env python
import psutil
import os
import re

_re_cpu = re.compile("^cpu([0-9]+)$")
_re_node = re.compile("^node([0-9]+)$")

class CpuInfo(object):
    def __init__(self):
        cpuinfo = open("/proc/cpuinfo", "r")
        re_kw = re.compile("^(.+[^\s:])\s*:\s?(.*)$")

        self.processors = {}
        current_cpu = None
        for l in cpuinfo:
            l = l.strip()

            m = re_kw.match(l)
            if m:
                key = m.group(1).strip()
                val = m.group(2)

                if key == "processor":
                    current_cpu = int(val)

                assert current_cpu != None, "Invalid current CPU id"

                if not current_cpu in self.processors:
                    self.processors[current_cpu] = {}

                self.processors[current_cpu][key] = val

            elif l:
                print >> sys.stderr, "Unrecognized CPU info: %s" % l
            else:
                current_cpu = None

    def __getitem__(self, key):
        return self.processors[0][key]

    def freq(self):
        return float(self["cpu MHz"])

    def no_cpus(self):
        return len(self.processors)

class SysAttr(object):
    def __init__(self, path):
        self.path = path

    def get(self, type=str):
        return type(open(self.path, "r").readline().strip())

    def get_list(self, type=str):
        return [ type(v) for v in self.get().split(",") ]

    def set(self, value):
        open(self.path, "w").write(value)

    def set_list(self, values):
        self.set(",".join([ str(s) for s in values ]))

    def __str__(self):
        return str(self.get())

class SysDirIterator(object):
    def __init__(self, sysdir, attrs=True, dirs=True):
        self.base = sysdir._base
        self.iter = iter(os.listdir(self.base))
        self.attrs = attrs
        self.dirs = dirs

    def next(self):
        while True:
            p = os.path.join(self.base, self.iter.next())
            if self.dirs and os.path.isdir(p):
                return SysDir(p)
            elif self.attrs and os.path.isfile(p):
                return SysAttr(p)

    def __iter__(self):
        return self

class SysDir(object):
    def __init__(self, base="/sys"):
        self._base = base

    def __iter__(self):
        return SysDirIterator(self)

    def __getitem__(self, name):
        p = os.path.join(self._base, name)
        if not os.path.exists(p):
            raise KeyError("%s: Path does not exist." % p)

        if os.path.isdir(p):
            return SysDir(p)
        else:
            return SysAttr(p)

    def __str__(self):
        return "SysDir('%s')" % self._base

    def name(self):
        return os.path.basename(self._base)

    def attrs(self):
        return SysDirIterator(self, attrs=True, dirs=False)

    def dirs(self):
        return SysDirIterator(self, attrs=False, dirs=True)

def get_nodes(sysfs):
    nodes = {}
    for node in sysfs['devices']['system']['node'].dirs():
        m_node = _re_node.match(node.name())
        if not m_node:
            continue

        node_id = int(m_node.group(1))
        nodes[node_id] = node

    return nodes

def get_node_cpus(node):
    cpus = {}
    for cpu in node.dirs():
        m_cpu = _re_cpu.match(cpu.name())
        if not m_cpu:
            continue

        cpu_id = int(m_cpu.group(1))
        cpus[cpu_id] = cpu

    return cpus

def get_cpu_topology(sysfs):
    # { node : {
    #       core : {
    #            [ vcpu, vcpu, ... ]
    #       }
    # }
    nodes = {
        }

    try:
        node_list = get_nodes(sysfs).items()
    except KeyError:
        # Workaround for non-NUMA systems
        node_list = [ ( 0, sysfs['devices']['system']['cpu'] ) ]

    for node_id, node in node_list:
        node_cpus = get_node_cpus(node)

        cores = {}
        for vcpu_id, cpu in node_cpus.items():
            top = cpu['topology']
            core_id = top['core_id'].get(type=int)
            core = cores.get(core_id, None)
            if core is None:
                core = []
                cores[core_id] = core

            core.append(vcpu_id)

        for core_id, core in cores.items():
            core.sort()

        nodes[node_id] = cores

    return nodes


def get_cpus(nodes=None, cores=None, threads=None):
    _nodes = get_cpu_topology(SysDir())

    vcpus = []
    for node_id, node in _nodes.items():
        if nodes and node_id not in nodes:
            continue

        for core_id, core in node.items():
            if cores and core_id not in cores:
                continue

            if threads:
                vcpus += [ core[t] for t in threads]
            else:
                vcpus += core

    return vcpus

def set_affinity(**kwargs):
    pid = os.getpid()
    p = psutil.Process(pid)
    cpus = get_cpus(**kwargs)
    print "Setting affinity mask of %i to %s" % (
        pid,
        compact_list(cpus))

    p.set_cpu_affinity(tuple(cpus))


def compact_list(lst):
    lst = list(lst)
    lst.sort()
    ranges = []
    cur_range = [ None, None ]
    for v in lst:
        if cur_range[0] is None:
            cur_range[0] = v
        elif (cur_range[0] + 1 == v) or \
                (cur_range[1] is not None and cur_range[1] + 1 == v):
                cur_range[1] = v
        else:
            ranges.append(tuple(cur_range))
            cur_range = [ v, None ]

    if cur_range[0] is not None:
        ranges.append(tuple(cur_range))

    str_ranges = [ "%i" % (start,) if stop is None else
                   "%i-%i" % (start, stop)
                   for start, stop in ranges ]

    return ",".join(str_ranges)


def eintr_retry_call(call, *args, **kwargs):
    while True:
        try:
            return call(*args, **kwargs)
        except OSError as ose:
            # Ignore errno 4 (Interrupted system call)
            if ose.errno != errno.EINTR:
                raise ose

def handle_exit_status(status):
    if os.WIFSIGNALED(status):
        return -os.WTERMSIG(status)
    elif os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    else:
        # Should never happen
        raise RuntimeError("Unknown child exit status!")

if __name__ == "__main__":
    cpuinfo = CpuInfo()
    print "CPU INFO:"
    print "\tFreq: %f MHz" % cpuinfo.freq()
    print "\tNo. CPUs: %i" % cpuinfo.no_cpus()

    topology = get_cpu_topology(SysDir())
    print topology
    print "All CPUs: %s" % compact_list(get_cpus())
    for node in topology:
        print "Node %i: %s" % (node, compact_list(get_cpus(nodes=(node,))))
    print "Thread 0: %s" % compact_list(get_cpus(threads=(0,)))
    print "Thread 1: %s" % compact_list(get_cpus(threads=(1,)))
    print "Core 2,3: %s" % compact_list(get_cpus(cores=(2,3)))
