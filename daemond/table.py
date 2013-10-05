# -*- python -*-

from parsing import *
from daemon import *


def populate_tables(daemons, groups, group_entries, runlevel, daemontab):
    '''
    Populate daemon and group tables
    
    @param  daemons:dict<str, Daemon>      Mapping, from daemon name to daemon structure, to fill
    @param  groups:dict<str, list<str>>    Mapping, from group name (including the % prefix) to group members, to fill
    @param  group_entries:list<list<str>>  List, of group entries, to fill
    @param  runlevel:str                   The current runlevel
    @param  daemontab:str                  Daemon table file
    '''
    
    # Load daemon table
    tab = None
    with open(daemontab, "rb") as file:
        tab = file.read().decode("utf-8", "error").replace("\t", " ").split("\n")
    
    
    # Enlist daemons specified the legacy way
    if legacy_daemons is not None:
        join = None
        for legacy_daemon in legacy_daemons:
            (legacy_daemon, join) = convert_legacy(legacy_daemon, join)
            if legacy_daemon is not None:
                tab.append(legacy_daemon)
    
    have_fork_daemon = False
    
    for args in filter(lambda x : len(x) > 0, [parse_args(line) for line in tab]):
        # List group entry, if it is one
        if args[0][0] == "%":
            group_entries.append(args)
            continue
        
        # List daemon
        daemon = make_daemon(args)
        if daemon.defined_for(runlevel):
            daemons[daemon.name] = daemon
            
            # Keep track of whether +fork exists and autostarts
            if (daemon.name == '+fork') and (daemon.autostart_for(runlevel)):
                have_fork_daemon = True
    
    # Add +fork daemon if not listed
    if not have_fork_daemon:
        # Default +fork requires all autostarting daemons before it runs
        fork_joins = []
        if not have_fork_daemon:
            for name in daemons:
                daemon = daemons[name]
                if daemon.autostart_for(runlevel):
                    fork_joins.append(daemon.name)
        
        # List +fork
        daemons['+fork'] = Deamon(None, '+fork', False, None, fork_joins, [])
    
    # Populate `groups`
    populate_groups(groups, group_entries, runlevel)


def populate_groups(groups, group_entries, runlevel):
    '''
    Populate group table
    
    @param  groups:dict<str, list<str>>    Mapping, from group name (including the % prefix) to group members, to fill
    @param  group_entries:list<list<str>>  List of group entries
    @param  runlevel:str                   The current runlevel
    '''
    for args in group_entries:
        group = args[0]
        if ":" in group:
            (group, condition) = group.split(":")
            if (runlevel in condition) == ("-" in condition):
                continue
        if group not in groups:
            groups[group] = []
        groups[group] += args[1:]

