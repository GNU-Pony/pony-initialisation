# -*- python -*-


def parse_args(line):
    '''
    Gets all arguments in a line
    
    @param   line:str    Line
    @return  :list<str>  Arguments in the line
    '''
    args = []
    
    quote, esc, buf = None, False, ""
    for c in line + " ":
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


def convert_legacy(legacy_daemon, join, runlevel):
    '''
    Convert an entry from the legacy daemon list to the new daemontab format
    
    @param   legacy_daemon:str?       The daemon entry
    @param   join:str?                The last daemon that is not starting in the background
    @param   runlevel:str             The current runlevel
    @return  :(line:str?, join:str?)  The entry in the daemontab format, and update for the `join` parameter
    '''
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
        return (None, join)
    if (runlevel in runlevels) == ("-" in runlevels):
        return (None, join)
    line = None
    if blacklisted:
        line = "%blacklist " + legacy_daemon
    else:
        legacy_daemon += " !" if silence else ""
        if join is not None:
            legacy_daemon += " & " + join
        line = legacy_daemon
        if not background:
            join = legacy_daemon.split(' ')[0]
    
    return (line, join)

