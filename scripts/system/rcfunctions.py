# -*- mode: python, coding: utf-8 -*-
#
# pony-initialisation functions
#


import os
from subprocess import Popen, PIPE


### Sanitize PATH (will be overridden later by £{ETC}/profile)
os.putenv("PATH", "£{LOCAL}£{SBIN}:£{LOCAL}£{BIN}:£{USR}£{SBIN}:£{USR}£{BIN}:£{SBIN}:£{BIN}")

### Clear TZ, so daemons always respect £{ETC}/localtime
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


def umount_all(*types):
    '''
    Unmount non-API filesystems
    
    @param  types  Filesystem types to unmount
    '''
    proc = ["findmnt", "-mrunRo", "TARGET,FSTYPE,OPTIONS", "/"]
    proc = Popen(proc, stdout = PIPE)
    mounts = proc.communicate()[0].split("\n")
    types = None if len(types) == 0 else set(types)
    API_MOUNT_POINTS = set(["£{PROC}", "£{SYS}", "£{RUN}", "£{DEV}", "£{DEV_PTS}"])
    umounts = []
    
    for mount_point in mounts:
        if len(mount_point) == 0:
            continue
        (target, fstype, options) = mount_poiny.split(" ")
        
        # Match only targeted filesystem types
        if (types is not None) and (fstype not in types):
            continue
        
        # Do not unmount API filesystems
        if target in API_MOUNT_POINTS:
            continue
        
        # Avoid networked devices
        if "_netdev" in options.split(","):
            continue
        
        umounts.append(target)
    
    if len(umounts) > 0:
        _("umount", "-r", *reversed(target))


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


def in_path(command):
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

