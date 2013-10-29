#!/usr/bin/env python3

import os
import sys

from spawning import *
from table import *


# Fields for CPU thread count, $PATH, previous runlevel and current runlevel
CPU_COUNT, PATH = None, None
PREVLEVEL, RUNLEVEL = None, None


# Parse command line
legacy_daemons = None
for arg in sys.argv[1:]:
    if legacy_daemons is not None:        legacy_daemons.append(arg)
    elif arg == "--":                     legacy_daemons = []
    elif arg.startswith("--runlevel="):   RUNLEVEL  = arg[len("--runlevel="):]
    elif arg.startswith("--prevlevel="):  PREVLEVEL = arg[len("--prevlevel="):]
    elif arg.startswith("--path="):       PATH      = arg[len("--path="):]
    elif arg.startswith("--cpus="):       CPU_COUNT = int(arg[len("--cpus="):])


# Get CPU thread count, $PATH, previous runlevel and current runlevel
CPU_COUNT = CPU_COUNT if CPU_COUNT is not None else len(os.listdir("/sys/bus/cpu/devices"))
PATH = PATH if PATH is not None else "/bin:/usr/bin:/sbin:/usr/sbin"
if (PREVLEVEL is None) or (RUNLEVEL is None):
    (_PREVLEVEL, _RUNLEVEL) = pipe(["runlevel"])[0].split(" ")
    PREVLEVEL = PREVLEVEL if PREVLEVEL is not None else _PREVLEVEL
    RUNLEVEL  = RUNLEVEL  if RUNLEVEL  is not None else _RUNLEVEL


# export RUNLEVEL, PREVLEVEL, PATH and CONSOLE
os.putenv("RUNLEVEL", RUNLEVEL)
os.putenv("PREVLEVEL", PREVLEVEL)
os.putenv("PATH", PATH)
console = os.getenv("CONSOLE", "/dev/console")
os.putenv("CONSOLE", console if console != "" else "/dev/console")


daemons = {}
'''
:dict<str, Daemon>  Mapping from daemon name to daemon structure
'''

groups = {}
'''
:dict<str, list<str>>  Mapping from group name (including the % prefix) to group members
'''

# Fill `daemons` and `groups`
populate_tables(daemons, groups, [], legacy_daemons, RUNLEVEL, "/etc/daemontab")

