# -*- mode: python, coding: utf-8 -*-
#
# pony-initialisation functions
#


import os
from subprocess import Popen, PIPE


# Sanitize PATH (will be overridden later by £{ETC}/profile)
os.putenv("PATH", "£{LOCAL}£{SBIN}:£{LOCAL}£{BIN}:£{USR}£{SBIN}:£{USR}£{BIN}:£{SBIN}:£{BIN}")

# Clear TZ, so daemons always respect £{ETC}/localtime
os.unsetenv("TZ")



def _(*args):
    '''
    Spawn a subprocess an wait for it to exit
    
    @param   args  The command line arguments
    @return        Whether the process was successful
    '''
    proc = Popen(list(args))
    proc.wait()
    return proc.returncode == 0


def __(*args):
    '''
    Spawn a subprocess an wait for it to exit, but suppress stdout
    
    @param   args  The command line arguments
    @return        Whether the process was successful
    '''
    proc = Popen(list(args), stdout = PIPE)
    proc.wait()
    return proc.returncode == 0


def get(variable, value_lambda, default = None):
    '''
    Get the proper value for a variable
    
    @param   variable      The current value of the variable
    @param   value_lambda  Function for getting the proper value for the variable
    @param   default       Fallback value
    @return                The proper value for the variable
    '''
    if default is None:
        return variable if variable is not None else value_lambda()
    else:
        try:
            return variable if variable is not None else value_lambda()
        except:
            return default


def mount(vfstype, device, directory, options, attempt_automount = False):
    '''
    Mount a filesystem
    
    @param  vfstype            File system type
    @param  device             Device
    @param  directory          Mount point
    @param  options            Mount options
    @param  attempt_automount  Try to use fstab to mount
    '''
    if attempt_automount and __("mount", directory):
        return
    os.path.exists(directory) or os.makedirs(directory, mode = 0o777, exist_ok = True)
    os.path.ismount(directory) or _("mount", "-t", vfstype, device, directory, "-o", options)


def sh_lex(sh_file):
    '''
    Restricted shell variable assignment parsing
    
    @param   sh_file  File format as POSIX shell only containing variable assignments with restricted syntax
    @return           Map from variable name to variable value (string or list of strings)
    '''
    lines = None
    with open(sh_file, "r") as file:
        lines = file.read()
    lines = lines.decode("utf-8", "replace")
    
    comment = False
    bracket = None
    escape = False
    quote = None
    name = ''
    value = None
    rc = {}
    
    for c in lines:
        if comment:
            if c == '\n':
                comment = False
        elif escape:
            if c not in '\n\r\f':
                value += c
        elif (quote is not None) and (c == quote):
            quote = None
        elif quote == '"':
            if c == '\\':
                escape = True
            else:
                value += c
        elif quote == '\'':
            value += c
        elif c in " \t\n\r\f":
            if bracket is None:
                name = ""
                if value is not None:
                    rc[name] = value
                value = ""
            else:
                bracket.append(value)
                value = None
        elif c == '#':
            comment = True
        elif c == '\\':
            escape = True
        elif c in "\"'":
            value += '\0'
            quote = c
        elif value is None:
            if c == '=':
                value = ''
            else:
                name += c
        else:
            if c == '(':
                bracket = []
            elif c == ')':
                if not value == "":
                    bracket.append(value)
                rc[name] = [v.replace('\0', '') for v in bracket]
                bracket = None
                value = ""
                name = None
            else:
                value += c
    
    return rc


def try_invoke(function):
    '''
    Return the value returned by a function, but `None` on failure
    
    @param   function  The function to run
    @return            The value returned by `function`, `None` on exception
    '''
    try:
        return function()
    except:
        return None


def is_path(command):
    '''
    Check whether a command exists inside PATH
    
    @param  command  The command, excluding location
    '''
    for path in os.getenv("PATH").split(":"):
        if len(path) > 0:
            return os.access(path + "/" + command, os.F_OK | os.R_OK | os.X_OK)
    return False


def get_vts():
    '''
    Gets all files matching /dev/tty[0-9]*
    
    @return  All files matching /dev/tty[0-9]*
    '''
    def is_vt(device):
        for digit in "0123456879":
            device = device.replace(digit, "")
        return device == "tty"
    return ["£{DEV}/" + tty for tty in filter(lambda dev : is_vt(dev), os.listdir("£{DEV}"))]

