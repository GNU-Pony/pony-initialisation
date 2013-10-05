#!/usr/bin/env python3

import os
import sys



RUNLEVEL = '3'
CPU_COUNT = len(os.listdir("/sys/bus/cpu/devices"))


legacy_daemons = None
for arg in sys.args[1:]:
    if legacy_daemons is not None:
        legacy_daemons.append(arg)
    elif arg == '--':
        legacy_daemons = []
    elif arg.startswith('--runlevel='):
        RUNLEVEL = arg[len('--runlevel='):]
    elif arg.startswith('--cpus='):
        CPU_COUNT = int(arg[len('--cpus='):])


tab = None
with open("/etc/daemontab", "rb") as file:
    tab = file.read()
tab = tab.decode("utf-8", "error").replace("\t", " ").split("\n")


if legacy_daemons is not None:
    join = None
    for legacy_daemon in legacy_daemon:
        blacklisted = "!" in legacy_daemon
        background = legacy_daemon[0] == "@"
        if background:
            legacy_daemon = legacy_daemon[1:]
        silence = legacy_daemon[-1] == "@"
        if silence:
            legacy_daemon = legacy_daemon[:-1]
        runlevels = None
        if ":" in legacy_daemon:
            (legacy_daemon, runlevels) = legacy_daemon.split(":")
        if runlevels is not None:
            continue
        if (RUNLEVEL in runlevels) == ("-" in runlevels):
            continue
        if blacklisted:
            tab.append("%blacklist " + legacy_daemon)
        else:
            legacy_daemon += " !" if silence else ""
            if join is not None:
                legacy_daemon += " & " + join
            tab.append(legacy_daemon)
            if not background:
                join = legacy_daemon.split(' ')[0]


def parse_args(line):
    args = []
    
    quote = None
    esc = False
    buf = ""
    for c in line:
        if quote is not None:
            if c == quote:
                quote = None
            buf += c
        elif esc:
            buf += c
            esc = False
        elif c == "\\":
            esc = True
        elif c in ('"', "'"):
            quote = c
        elif c == " ":
            if buf != "":
                args.append(buf)
                buf = ""
        elif c == "#":
            if buf != "":
                args.append(buf)
            break
        else:
            buf += c
    
    return args


groups = {}
daemones = {}
class Daemon():
    def __init__(self, autostart, name, silence, runlevel, joins, launchers):
        self.autostart = autostart
        self.name = name
        self.silence = silence
        self.runlevel = runlevel
        self.joins = joins
        self.launchers = launchers
    
    def defined_for(self, runlevel):
        r = self.runlevel
        return (r is None) or ((runlevel in r) ^ ('-' not in r))
    
    def autostart_for(self, runlevel):
        r = self.autostart
        return (r is None) or ((runlevel in r) ^ ('-' not in r))


for args in filter(lambda x : len(x) > 0, [parse_args(line) for line in tab]):
    if args[0][0] == "%":
        group = args[0][1:]
        if group not in groups:
            groups[group] = []
        groups[group] += args[1:]
        continue
    
    autostart_condition = None
    daemon_name = None
    silence = False
    runlevel_condition = None
    joins = []
    launchers = []
    
    if args[0][0] == "!":
        autostart_condition = args[0].replace("!", "-").replace("--", "")
        args[:] = args[1:]
    if len(args) == 0:
        continue
    
    daemon_name = args[0]
    args[:] = args[1:]
    
    ampersand = False
    arrow = False
    launcher = []
    for arg in args:
        if arg == "!":
            silence = True
        elif arg in ("&", "<-"):
            if len(launcher) > 0:
                launchers.append(launcher)
                launcher = []
            ampersand = arg == "&"
            arrow = arg == "<-"
        elif ampersand:
            joins.append(arg)
            ampersand = False
        elif arrow:
            launcher.append(arg)
        else:
            runlevel_condition = arg
    if len(launcher) > 0:
        launchers.append(launcher)
    
    daemon = Daemon(autostart_condition, daemon_name, silence, runlevel_condition, joins, launchers)
    if daemon.defined_for(RUNLEVEL):
        daemons[name] = daemon


