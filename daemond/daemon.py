# -*- python -*-


from subprocess import Popen

from printer import *


class Daemon():
    '''
    Daemon structure
    '''
    
    def __init__(self, autostart, name, silence, runlevel, joins, launchers):
        '''
        Constructor
        
        @param  autostart:str?             Conditions for autostarting
        @param  name:str                   The name of the daemons
        @param  silence:bool               Whether the daemon's stdout and stderr should be silenced
        @param  runlevel:str?              Conditions for being defined
        @param  joins:list<str>            Required daemons
        @param  launchers:list<list<str>>  Sets of daemons which launches the daemon
        '''
        self.autostart = autostart
        self.name = name
        self.silence = silence
        self.runlevel = runlevel
        self.joins = joins
        self.launchers = launchers
    
    
    def defined_for(self, runlevel):
        '''
        Check whether the entry is defined
        
        @param   runlevel:str  The runlevel
        @return  :boolean      Whether the entry is defined
        '''
        r = self.runlevel
        return (r is None) or ((runlevel in r) ^ ("-" not in r))
    
    
    def autostart_for(self, runlevel):
        '''
        Check whether the entry autostarts
        
        @param   runlevel:str  The runlevel
        @return  :boolean      Whether the entry autostarts
        '''
        r = self.autostart
        return (r is None) or ((runlevel in r) ^ ("-" not in r))
    
    
    def start(self, verb, output = None):
        '''
        Send a verb the daemon
        
        @param   verb:str       The verb to start with
        @param   output:ofile?  Output file, `None` for standard output
        @return  :boolean       Whether the daemon received and acted on the verb sucessfully
        '''
        message = "Sending %s signal to %s" % (verb[0].upper() + verb[1:], self.name)
        args = ["£{DAEMON_DIR}/" + self.name, verb]
        if output is None:
            index = print_starting(message)
            try:
                r = start(self, lambda : pipe(args, stdout = printer_pipe, stderr = printer_pipe, silent = self.silence))
                if r[1] == 0:
                    print_successful(message, index)
                    return True
            except:
                print_failed(message, index)
                return False
        else:
            try:
                r = start(self, lambda : pipe(args, stdout = printer_pipe, stderr = output, silent = self.silence))
                return r[1] == 0
            except:
                return False
    
    
    def start_(self, function):
        '''
        Method called by `start` to start a process
        
        @param   function:()→(output:str?, returncode:int)  Function that starts the process
        @return  (output:str?, returncode:int)              The output of the pipeline and the highest returned return code
        '''
        return function()
    
    
    def __str__(self):
        '''
        Create text representation of daemon entry
        
        @return  :str  Text representation of daemon entry
        '''
        return "(%s%s%s%s%s%s)" % (self.name,
                                  " %s" % self.autostart if self.autostart is not None else "",
                                  " +silence" if self.silence else "",
                                  " runlevel:%s" % self.runlevel if self.runlevel is not None else "",
                                  " & %s" % " & ".join(self.joins) if len(self.joins) > 0 else "",
                                  " <- %s" % " <- ".join([" ".join(L) for L in self.launchers]) if len(self.launchers) > 0 else "")


def make_daemon(args):
    '''
    Create a daemon structure from a daemontab entry
    
    @param   args:list<str>  Arguments in daemontab entry
    @return  :Daemon?        The daemon described by the entry, `None` if there as none
    '''
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
        return None
    
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
    return daemon

