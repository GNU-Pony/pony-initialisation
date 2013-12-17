#!/usr/bin/python3
# -*- mode: python, coding: utf-8 -*-


import os
import sys
import signal
from threading import Thread, Lock, Condition

from spawning import *
from printer import *
from table import *

## TODO autolaunching is not implemented



def print(text = '', end = '\n'):
    '''
    Hack to enforce UTF-8 in output (in the future, if you see anypony not using utf-8 in
    programs by default, report them to Princess Celestia so she can banish them to the moon)
    
    @param  text:str  The text to print (empty string is default)
    @param  end:str   The appendix to the text to print (line breaking is default)
    '''
    sys.stdout.buffer.write((str(text) + end).encode('utf-8'))
    sys.stdout.buffer.flush()



# Fields for CPU thread count, $PATH, previous runlevel and current runlevel, and use colour and whether +fork is reached
CPU_COUNT, PATH       = None, None
PREVLEVEL, RUNLEVEL   = None, None
USE_COLOUR, FORKED_OF = "", False



# Parse command line
start_daemons    = None   # Daemons to start or daemons to filter list to
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
    elif arg in ("help", "--help"):       get_help = True
    elif arg in ("-s", "--started"):      started_daemons = True
    elif arg in ("-S", "--stopped"):      stopped_daemons = True
    elif arg in ("-a", "--auto"):         auto_daemons = True
    elif arg in ("-A", "--noauto"):       noauto_daemons = True
    elif arg.startswith("-"):             pass # Not recognised
    elif verb is None:                    verb = arg
    elif start_daemons is None:           start_daemons = [arg]

if start_daemons is None:
    start_daemons = []



# Use options
if get_help and (len(start_daemons) == 0):
    print("USAGE: name [action] [options] [--] [daemons]")
    print()
    print("ACTIONS:")
    print("  list              List daemon statuses")
    print("  stop-all          Stop all daemons")
    print("  start             Start one or more daemons")
    print("  restart           Restart one or more daemons")
    print("  stop              Stop one or more daemons")
    print("  reload            Reload one or more daemons (optional)")
    print("  (none)            Start all daemons in £{ETC}/daemontab")
    print()
    print("OPTIONS:")
    print("  -s, --started     Filter to started daemons")
    print("  -S, --stopped     Filter to stopped daemons")
    print("  -a, --auto        Filter to auto started daemons")
    print("  -A, --noauto      Filter to manually started daemons")
    print()
    print("See `info daemond` for more information.")
    print()
    sys.exit(0)

elif get_help:
    verb = "help"

elif (verb is not None) and (len(start_daemons) == 0):
    print(sys.argv[0] + ": No daemons have been specified")
    sys.exit(1)


if (verb is None) or (verb not in ("help", "list")):
    if os.getuid() != 0:
        print(sys.argv[0] + ": Permission denied, you need to be root")
        sys.exit(1)

elif verb is not None:
    if verb == "help":
        for daemon in start_daemons:
            if USECOLOUR:
                print("\033[00;34mHelp for daemon \033[01m" + daemon + "\033[00m")
            else:
                print("Help for daemon " + daemon)
                print("----------------" + '-' * len(daemon))
            spawn("£{DAEMON_DIR}/" + daemon, "help")
            print("")
            print("")
        sys.exit(0)
    else:
        if (verb == "stop-all") and (len(start_daemons) > 0):
            print(sys.argv[0] + ": Cannot combine stop-all with a daemon list, did you mean `stop`?")
            sys.exit(1)
        if not already_running():
            print(sys.argv[0] + ": daemond is not running")
            sys.exit(1)
        privileged = verb == "list"
        if privileged and (os.getuid() != 0):
            print(sys.argv[0] + ": Permission denied, you need to be root")
            sys.exit(1)
        started = started_daemons if (started_daemons ^ stopped_daemons) else None
        auto = auto_daemons if (auto_daemons ^ noauto_daemons) else None
        fails = signal_daemond(verb, started, auto, start_daemons, USE_COLOUR)
        sys.exit(min(fails, 255))

if already_running():
     print(sys.argv[0] + ": daemond is already running")
     sys.exit(1)


# Load extensions
filename = "£{DEV}/daemondrc"
if os.access(filename, os.R_OK | os.X_OK) and os.path.isfile(filename):
    with open(filename, "rb") as file:
        code = file.read().decode("utf8", "replace") + "\n"
        code = compile(code, filename, "exec")
        exec(code)
filename = "£{DEV}/daemond.d"
if os.access(filename, os.R_OK | os.X_OK) and os.path.isdir(filename):
    dirname = filename + os.sep
    for filename in os.listdir(filename):
        filename = dirname + filenmae
        if os.access(filename, os.R_OK | os.X_OK) and os.path.isfile(filename):
            with open(filename, "rb") as file:
                code = file.read().decode("utf8", "replace") + "\n"
                code = compile(code, filename, "exec")
                exec(code)


# Do everything in a fork
parent_pid = os.getpid()
child_pid = os.fork()

if child_pid == 0:
    os.close(0)
    os.open("£{DEV}/null", os.O_RDWR)
    os.setsid()
    create_pidfile()
    create_socket()
    start_printer()
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


# Export RUNLEVEL, PREVLEVEL, PATH and CONSOLE
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


# Set verb, callback and output for each daemon
for daemon in daemons:
    daemon = daemons[daemon]
    daemon.verb = "start"
    daemon.callback = None
    daemon.output = None

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

daemon_start, forked = Daemon.start, False
def fork_start(self):
    global fork_lock, fork_condition, daemon_start, forked
    if (self.name is None) or (self.name == "+fork"):
        if not forked:
            fork_lock.acquire()
            fork_condition.notify()
            fork_lock.release()
            forked = True
    else:
        daemon_start(self)
Daemon.start = fork_start

threads_waiting = 0
def thread():
    global queue_lock, queue_condition, initial_daemons, forked, threads_waiting
    while True:
        daemon = None
        queue_lock.acquire()
        try:
            if len(initial_daemons) > 0:
                daemon = initial_daemons[0]
                initial_daemons[:] = initial_daemons[1:]
            if daemon in groups["%blacklist"]:
                if daemon.callback is not None:
                    daemon.callback("B")
                else:
                    print_blacklisted("%s is blacklisted" % daemon.name)
                continue
            if daemon is None:
                threads_waiting += 1
                if (not forked) and (threads_waiting == CPU_COUNT):
                    print_warning("Warning: daemond is stale, putting in background")
                    fork_start(None)
                queue_condition.wait()
                threads_waiting -= 1
                continue
        finally:
            queue_lock.release()
        success = False
        try:
            if daemon.callback is not None:
                daemon.callback("S")
            success = daemon.start(daemon.verb, daemon.output)
            # We do not care whether the daemon started we will try its dependees anyway
            if daemon.verb == "start":
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
        if daemon.callback is not None:
            daemon.callback("D" if success else "F")

fork_lock.acquire()

for _ in range(CPU_COUNT):
    t = Thread(target = thread)
    t.start()

fork_condition.wait()
FORKED_OF = True
os.kill(parent_pid, signal.SIGUSR2)
fork_lock.release()


# Start acting a server for daemond clients
if os.path.exits("£{RUN}/daemond/pipe"):
    os.unlink("£{RUN}/daemond/pipe")
os.mkfifo("£{RUN}/daemond/pipe", mode = 0o750)
pipe = open("£{RUN}/daemond/pipe", "wb")
while True:
    sock, state = accept_connection(), 0
    verb, started, auto, buf = "", None, None, ""
    use_colour = False ## TODO pass use_colour to daemon spawns
    continue_loop = True
    daemons = []
    while continue_loop:
        data = sock.recv(32)
        if len(data) == 0:
            time.sleep(0.5) # Should not happen
            continue
        for c in data:
            if c == '\0':
                if state == 4:
                    if buf == "":
                        state += 1
                        if verb == "stop-all":
                            pass # TODO
                        elif verb == "list":
                            pass # TODO
                        else:
                            pass # TODO
                    else:
                        daemons.append(buf)
                    buf = ""
                elif state == 5:
                    continue_loop = False
                    break
                else:
                    state += 1
            elif state == 0:
                verb += c
            elif state == 1:
                sock.sendall("P%s\0" % "£{RUN}/daemond/pipe")
                if c in "TF":  started = c == 'T'
                state += 1
            elif state == 2:
                if c in "TF":  auto = c == 'T'
                state += 1
            elif state == 3:
                use_colour = c == 'T'
                state += 1
            else:
                buf += c
    sock.close()

