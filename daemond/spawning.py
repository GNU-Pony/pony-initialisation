# -*- python -*-


import os
import sys
from subprocess import Popen, PIPE


S = lambda *string : [s.split(" ") for s in string]
'''
Create an array of word splited strings
'''


def pipe(*commands, stdin = None, stdout = None, silent = False):
    '''
    Open a process pipeline
    
    @param   commands:*list<str>  The commands to run
    @param   stdin:str?           Input for the first process's stdin, `None` for using the spawner's stdin
    @param   stdout:ofile         The output sink for the last process in the command line
    @param   silent:bool          Whether the pipeline's stderr is silenced
    @return  :(str?, int)         The output of the pipeline and the highest returned return code
    '''
    cmds = list(commands)
    stdin_ = sys.stdin if stdin is None else PIPE
    stderr = PIPE if silent else sys.stderr
    procs = [None] * len(cmds)
    
    # Create pipeline
    for i in range(len(cmds)):
        procs[i] = Popen(cmds[i], stdin = stdin_, stdout = PIPE, stderr = stderr)
        stdin_ = procs[i].stdout
    
    # Set end output
    if stdout is not None:
        procs[len(cmds) - 1].stdout = stdout
    
    # Feed start input
    if stdin is not None:
        procs[0].stdin.write(stdin.encode("utf-8"))
        procs[0].stdin.flush()
        procs[0].stdin.close()
    
    # Wait for processes to finish and store return code
    error = 0
    for i in range(0, len(cmds) - 1):
        procs[i].wait()
        error = max(error, procs[i].returncode)
    
    # Wait for the last process and gets its output and store return code
    i = len(cmds) - 1
    output = procs[i].communicate()[0]
    if stdout is None:
        output = output.decode("utf-8", "replace")
        if output.endswith("\n"):
            output = output[:-1]
    error = max(error, procs[i].returncode & 255)
    
    return (output, error)


def spawn(*commands, stdin = None, silent = False):
    '''
    Open a process pipeline and redirect the output to the spawners stdout
    
    @param   commands:*list<str>  The commands to run
    @param   stdin:str?           Input for the first process's stdin, `None` for using the spawner's stdin
    @param   silent:bool          Whether the pipeline's stderr is silenced
    @return  :(str?, int)         The output of the pipeline and the highest returned return code
    '''
    return spawn(commands, stdin = stdin, stdout = sys.stdout, silent = silent)

