#!/usr/bin/python3
# -*- mode: python, coding: utf-8 -*-

import os
import sys
import signal
from threading import Thread, Lock, Condition

from spawning import *
from table import *

## TODO autolaunching is not implemented


# Fields for CPU thread count, $PATH, previous runlevel and current runlevel, and use colour
CPU_COUNT, PATH     = None, None
PREVLEVEL, RUNLEVEL = None, None
USE_COLOUR          = ""



# Parse command line
start_daemons    = None   # Daemons to start or daemons to filter list to
stop_all_daemons = False  # Stop all daemons in reverse start order
list_daemons     = False  # List daemon statuses
started_daemons  = False  # Filter to started daemons
stopped_daemons  = False  # Filter to stopped daemons
auto_daemons     = False  # Filter to auto started daemons
noauto_daemons   = False  # Filter to manually started daemon
get_help         = False  # Print help information
verb             = None   # Execute daemon with verb, such as start, stop and restart
for arg in sys.argv[1:]:
    if start_daemons is not None:         start_daemons.append(arg)
    elif arg == "--":                     start_daemons = []
    elif arg.startswith("--runlevel="):   RUNLEVEL   = arg[len("--runlevel="):]
    elif arg.startswith("--prevlevel="):  PREVLEVEL  = arg[len("--prevlevel="):]
    elif arg.startswith("--path="):       PATH       = arg[len("--path="):]
    elif arg.startswith("--cpus="):       CPU_COUNT  = int(arg[len("--cpus="):])
    elif arg.startswith("--usecolour="):  USE_COLOUR = arg[len("--usecolour="):]
    elif arg == "stop-all":               stop_all_daemons = True
    elif arg == "list":                   list_daemons = True
    elif arg in ("help", "--help"):       get_help = True
    elif arg in ("-s", "--started"):      started_daemons = True
    elif arg in ("-S", "--stopped"):      stopped_daemons = True
    elif arg in ("-a", "--auto"):         auto_daemons = True
    elif arg in ("-A", "--noauto"):       noauto_daemons = True
    elif arg.startswith("-"):             pass # Not recognised
    elif verb is None:                    verb = arg
    elif start_daemons is None:           start_daemons = [arg]



# Do everything in a fork
parent_pid = os.getpid()
child_pid = os.fork()

if child_pid == 0:
    os.close(0)
    os.open("£{DEV}/null", os.O_RDWR)
    os.setsid()
else:
    def noop(_a, _b):
        pass
    signal.signal(signal.SIGUSR2, noop)
    signal.pause()
    sys.exit(0)



# Get CPU thread count, $PATH, previous runlevel and current runlevel
CPU_COUNT = CPU_COUNT if CPU_COUNT is not None else len(os.listdir("£{SYS}/bus/cpu/devices"))
PATH = PATH if PATH is not None else "£{BIN}:£{USR}£{BIN}:£{SBIN}:£{USR}£{SBIN}"
if (PREVLEVEL is None) or (RUNLEVEL is None):
    (_PREVLEVEL, _RUNLEVEL) = pipe(["runlevel"])[0].split(" ")
    PREVLEVEL = PREVLEVEL if PREVLEVEL is not None else _PREVLEVEL
    RUNLEVEL  = RUNLEVEL  if RUNLEVEL  is not None else _RUNLEVEL


# export RUNLEVEL, PREVLEVEL, PATH and CONSOLE
os.putenv("RUNLEVEL", RUNLEVEL)
os.putenv("PREVLEVEL", PREVLEVEL)
os.putenv("PATH", PATH)
console = os.getenv("CONSOLE", "£{DEV}/console")
os.putenv("CONSOLE", console if console != "" else "£{DEV}/console")


# Use colour?
for envvar in ["USECOLOUR", "USE_COLOUR", "USECOLOR", "USE_COLOR"]:
    if USE_COLOUR == "":  USE_COLOUR = os.getenv(envvar, "")
    if USE_COLOUR == "":  USE_COLOUR = os.getenv(envvar + "S", "")
USE_COLOUR = None USE_COLOUR.lower() == "auto" else USE_COLOUR.lower() in ("y", "1", "yes")
if USE_COLOUR is None:
    if sys.stdout.isatty():
        try:
            tty = os.readlink("£{PROC}/self/fd/%i" % sys.stdout.fileno())
            if tty == console:
                USE_COLOUR = True
            else:
                for c in "0123456789":
                    tty = tty.replace(c, "")
                USE_COLOUR = tty in ("£{DEV}/tty", "£{DEV_PTS}/")
        except:
            USE_COLOUR = False
for envvar in ["USECOLOUR", "USE_COLOUR", "USECOLOR", "USE_COLOR"]:
    os.putenv(envvar, "yes" if USE_COLOUR else "no")
    os.putenv(envvar + "S", "yes" if USE_COLOUR else "no")



daemons, groups, membes = {}, {}, {}
'''
:dict<str, Daemon>     Mapping from daemon name to daemon structure
:dict<str, list<str>>  Mapping from group name (including the % prefix) to group members
:dict<str, list<str>>  Transposition of `groups`
'''


# Fill `daemons` and `groups`
populate_tables(daemons, groups, [], start_daemons, RUNLEVEL, "£{ETC}/daemontab")

# Transpose `groups`
for group in groups:
    for member in groups[group]:
        if member not in members:
            members[member] = []
        members[member].append(group)


initial_daemons = []
'''
:list<Daemon>  Daemons that do not require any other daemons, and should be started
'''


# Create mappings between daemons for join statements
for daemon in daemons:
    daemon = daemons[daemon]
    daemon.cuing = []
    if not daemon.defined_for(RUNLEVEL):
        continue
    if len(daemon.joins) > 0:
        daemon.waiting = set(daemon.joins)
    else:
        initial_daemons.append(daemon)

for daemon in daemons:
    daemon = daemons[daemon]
    if not (daemon.defined_for(RUNLEVEL) and daemon.autostart_for(RUNLEVEL)):
        continue
    for join in daemon.joins:
        if not join.startswith('%'):
            daemons[join].cuing.append(daemon)
        else:
            for member in groups[join]:
                daemons[member].cuing.append(daemon)


# Start daemons
queue_lock = Lock()
queue_condition = Condition(queue_lock)
fork_lock = Lock()
fork_condition = Condition(fork_lock)

daemon_start = Daemon.start
def fork_start(self):
    global fork_lock, fork_condition, daemon_start
    if self.name == '+fork':
        fork_lock.acquire()
        fork_condition.notify()
        fork_lock.release()
    else:
        daemon_start(self)
Daemon.start = fork_start

def thread():
    global queue_lock, queue_condition, initial_daemons
    while True:
        daemon = None
        queue_lock.acquire()
        try:
            if len(initial_daemons) > 0:
                daemon = initial_daemons[0]
                initial_daemons[:] = initial_daemons[1:]
            if daemon in groups["%blacklist"]:
                continue
            if daemon is None:
                queue_condition.wait()
                continue
        finally:
            queue_lock.release()
        try:
            daemon.start()
            queue_lock.acquire()
            try:
                for cuing in daemon.cuing:
                    if daemon.name in cuing.waiting:
                        cuing.waiting.remove(daemon.name)
                    if daemon.name in members:
                        for group in members[daemon.name]:
                            if group in cuing.waiting:
                                cuing.waiting.remove(group)
                    if len(cuing.waiting) == 0:
                        initial_daemons.append(cuing)
                        queue_condition.notify_all()
            finally:
                queue_lock.release()
        except:
            pass

fork_lock.acquire()

for _ in range(CPU_COUNT):
    t = Thread(target = thread)
    t.start()

fork_condition.wait()
os.kill(parent_pid, signal.SIGUSR2)
fork_lock.release()


# TODO start using domain socket
while True:
    signal.pause()

