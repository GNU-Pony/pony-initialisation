#!/usr/bin/python3
# -*- mode: python, coding: utf-8 -*-
#
# Common system initialisation script
#

_msg = None
_singular = lambda text = None : print(      '\033[01;35m%s\033[00;30m [SNGL]\033[00m'   % (_msg if text is None else text))
_waiting  = lambda text = None : print(      '\033[00;33m%s\033[00;30m [WAIT]\033[00m'   % (_msg if text is None else text))
_working  = lambda text = None : print(      '\033[01;33m%s\033[00;30m [WORK]\033[00m'   % (_msg if text is None else text))
_warning  = lambda text = None : print(      '\033[00;31m%s\033[00;30m [WARN]\033[00m\n' % (_msg if text is None else text))
_done     = lambda text = None : print('\033[A\033[01;32m%s\033[00;30m [DONE]\033[00m'   % (_msg if text is None else text))
_failure  = lambda text = None : print(      '\033[01;32m%s\033[00;30m [FAIL]\033[00m'   % (_msg if text is None else text))
_async    = lambda text = None : print(      '\033[01;34m%s\033[00;30m [ASNC]\033[00m'   % (_msg if text is None else text))


### Load libraries

_msg = 'Load libraries'
_working()

import os
import sys
import time
from subprocess import Popen, PIPE

from rcfunctions import *
from rclexal import *
_ = spawn(*args)
__ = spawn_(*args)
def _try(function):
    try:
        function()
        return True
    except:
        return False
def do(function):
    _working()
    try:
        function()
        _done()
    except:
        _failure()

_done()



### Load variables

_msg = 'Load variables'
_working()

NETFS = "nfs,nfs4,smbfs,cifs,codafs,ncpfs,shfs,fuse,fuseblk,glusterfs,davfs,fuse.glusterfs"

os_release = try_invoke(lambda : sh_lex("£{ETC}/os-release"))
if rc_conf is None:
    os_release = {}

rc_conf = try_invoke(lambda : sh_lex("£{ETC}/rc.conf"))
if rc_conf is None:
    rc_conf = {}

CPU_COUNT     = kernel_opts("--init-threads", lambda x : int(x))
CPU_COUNT     = get(CPU_COUNT, lambda : len(os.listdir("£{SYS}/bus/cpu/devices")), 4)
NAME          = get(None, os_release, "NAME", "")
VERSION       = get(None, os_release, "VERSION", "")
PRETTY_NAME   = get(None, os_release, "PRETTY_NAME", "")
ANSI_COLOR    = get(None, os_release, "ANSI_COLOR", "")
HOME_URL      = get(None, os_release, "HOME_URL", "")
HOSTNAME      = get(None, rc_conf, "HOSTNAME", "")
TIMEZONE      = get(None, rc_conf, "TIMEZONE", "")
HARDWARECLOCK = get(None, rc_conf, "HARDWARECLOCK", "")
USEDMRAID     = get(None, rc_conf, "USEDMRAID", "").lower() == "yes"
USELVM        = get(None, rc_conf, "USELVM", "").lower() == "yes"
MODULES       = get(None, rc_conf, "MODULES", "")
CONSOLEFONT   = get(None, rc_conf, "CONSOLEFONT", "")
CONSOLEMAP    = get(None, rc_conf, "CONSOLEMAP", "")
KEYMAP        = get(None, rc_conf, "KEYMAP", "")
LOCALE        = get(None, rc_conf, "LOCALE", "")

_done()



### Print distribution information

try:
    if (PRETTY_NAME == "") and (not NAME == ""):
        PRETTY_NAME = NAME
        if not VERSION == "":
            PRETTY_NAME += ' ' + version
    
    print()
    print()
    if not PRETTY_NAME == "":
        if not ANSI_COLOR == "":
            print('\033[%sm%s\033[00m' % (ANSI_COLOR, PRETTY_NAME))
        else:
            print(PRETTY_NAME)
    if not HOME_URL == "":
        if (not ANSI_COLOR == "") and (PRETTY_NAME == ""):
            print('\033[%sm%s\033[00m' % (ANSI_COLOR, HOME_URL))
        else:
            print(HOME_URL)
    print()
    print()
except:
    pass # does not matter



### Mount the API filesystems

_async('Mount the API filesystems')

def mount_dev():
    mount("devtmpfs", "dev", "£{DEV}", "mode=0755,nosuid")
    try_invoke(lambda : os.makedirs("£{DEV}/mqueue",    mode = 0o755, exist_ok = True))
    try_invoke(lambda : os.makedirs("£{DEV}/hugepages", mode = 0o755, exist_ok = True))
t1 = async(mount_dev)
t2 = async(lambda : mount("tmpfs",  "run",    "£{RUN}",     "mode=0755,nosuid,nodev"))
t3 = async(lambda : mount("proc",   "proc",   "£{PROC}",    "nosuid,noexec,nodev"))
t4 = async(lambda : mount("sysfs",  "sys",    "£{SYS}",     "nosuid,noexec,nodev"))
t5 = async(lambda : mount("devpts", "devpts", "£{DEV_PTS}", "mode=0620,gid=5,nosuid,noexec", True))
t6 = async(lambda : mount("tmpfs",  "shm",    "£{DEV_SHM}", "mode=1777,nosuid,nodev",        True))



### Ensure that / is readonly to allow `fsck` (requires /run)
# We remount now so remount is not blocked by anything opening a file for writing

_msg = 'Ensure that / is readonly to allow `fsck`'
_waiting()
t2.join()
_working()
try:
    if not os.path.exists("£{RUN}/initramfs/root-fsck"):
        _try(lambda : __("findmnt", "/", "--options", "ro")) or _("mount", "-o", "remount,ro", "/")
    _done()
except:
    _failure()



### Log all console messages (requires /proc /run /dev)

_msg = 'Log all console messages'
_waiting()
t1.join()
t3.join()
do(lambda : _("bootlogd", "-p", "£{RUN}/bootlogd.pid"))



### Set hostname (requires /proc)

_msg = 'Set hostname'
_working()
try:
    if HOSTNAME == "":
        with open("£{ETC}/hostname", "r") as file:
            HOSTNAME="".join(file.readlines()).replace("\n", "")
    if not HOSTNAME == "":
        with open("£{PROC}/sys/kernel/hostname", "wb") as file:
            file.write(HOSTNAME.encode("utf-8"))
            file.flush()
    _done()
except:
    _failure()



### Adjust system time and setting kernel time zone (requires /dev?)

_msg = 'Adjust system time and setting kernel time zone'
_working()
try:
    hwclock_args = ["hwclock", "--systz"]
    
    if not HARDWARECLOCK == "":
        HARDWARECLOCK = HARDWARECLOCK.lower()
        ADJTIME = ""
        try:
            if os.path.exists("£{ETC}/adjtime"):
                with open("£{ETC}/adjtime", "r") as file:
                    ADJTIME = file.read().split("\n")[2]
        except:
            pass
        
        if ADJTIME == 'LOCAL':
            if HARDWARECLOCK == 'utc':
                print('£{ETC}/rc.conf says the RTC is in UTC,')
                print('but £{ETC}/adjtime says it is in localtime.')
                _warning()
        else:
            if HARDWARECLOCK == 'localtime':
                print('£{ETC}/rc.conf says the RTC is in localtime,')
                print('but hwclock (£{ETC}/adjtime) thinks it is in UTC.')
                _warning()
        
        if HARDWARECLOCK in ('utc', 'localtime'):
            hwclock_args += ['--' + HARDWARECLOCK, '--noadjfile']
        else:
            hwclock_args = None
    
    if hwclock_args is not None:
        if not TIMEZONE == "":
            os.putenv("TZ", TIMEZONE)
        _(*hwclock_args)
        os.unsetenv("TZ")
    _done()
except:
    _failure()



### Start/trigger udev, load MODULES, and settle udev (requires /dev, /sys, /run)

_msg = 'Disable blacklisted kernel modules'
_waiting()
t4.join()
_working()
try:
    if not isinstance(MODULES, str):
        blacklist = list(filter(lambda module : module.startswith("!"), MODULES))
        if len(blacklist) > 0:
            blacklist = [blacklist[1:] for excl_module in blacklist]
            os.makedirs("£{RUN}/modprobe.d", exist_ok = True)
            with open("£{RUN}/modprobe.d/modprobe-blacklist.conf", "w") as file:
                file.write("# Autogenerated from rc.conf at boot, do not edit\n")
                file.write("blacklist %s\n" % " ".join(blacklist))
                file.flush()
    _done()
except:
    _failure()

_msg = 'Start and trigger devd'
_working()
devd_command = 'devd' if in_path('devd') else 'udevd'
devadm_command = 'devadm' if in_path('devadm') else 'udevadm'
# You should really have symlinks named devd and devadm to your device daemon and controller

try:
    _(devd_command, "--daemon")
    _(devadm_command, "trigger", "--action=add", "--type=subsystems")
    _(devadm_command, "trigger", "--action=add", "--type=devices")
    _done()
except:
    _failure()

_msg = 'Load kernel modules'
_working()
try:
    whitelisted_modules = list(filter(lambda module : not module.startswith("!"), MODULES))
    if len(whitelisted_modules) > 0:
        _("modprobe", "-ab", *whitelisted_modules)
    _done()
except:
    _failure()

_msg = 'Settle devd'
_working()
try:
    _(devadm_command, "settle")
    _done()
except:
    _failure()



### Configure virtual consoles (requires devd (for KMS), /dev, /sys)

_msg = 'Configure virtual consoles'
_working()
try:
    kbd_mode, tty_echo, vt_param = "-a", b"\033%@", b"0\n"
    if 'UTF' in os.getenv("LANG").upper(): # UTF-8 mode
        # UTF-8 consoles are default since 2.6.24 kernel
        # this code is needed not only for older kernels,
        # but also when user has set vt.default_utf8=0 but LOCALE is *.UTF-8.
        kbd_mode, tty_echo, vt_param = "-u", b"\033%G", b"1\n"
    # (otherwise) legacy mode: Make non-UTF-8 consoles work on 2.6.24 and newer kernels.
    
    for tty in get_vts():
        _("kbd_mode", kbd_mode, "-C", tty)
        with open(tty, "wb") as file:
            file.write(tty_echo)
            file.flush()
    with open("£{SYS}/module/vt/parameters/default_utf8", "wb") as file:
        file.write(vt_param)
        file.flush()
    _done()
except:
    _failure()



### Set console font (requires vcon)

_async('Set console')
def console_font():
    global CONSOLEMAP
    if (not CONSOLEMAP == "") and ('UTF' in LOCALE.upper()):
        CONSOLEMAP = "" # CONSOLEMAP in UTF-8 shouldn't be used
    for tty in get_vts():
        if not CONSOLEMAP == "":
            __("setfont", "-m", CONSOLEMAP, CONSOLEFONT, "-C", tty)
        else:
            __("setfont", CONSOLEFONT, "-C", tty)
t7 = async(console_font)



### Set keymap (requires vcon)

_async('Set keymap')
t8 = async(lambda : _("loadkeys", "-q", KEYMAP))



### Bring up the loopback interface (requires /sys)

_msg = 'Bring up the loopback interface'
do(lambda : os.path.exists("£{SYS}/class/net/lo") and _("ip", "link", "set", "up", "dev", "lo"))



### Detect FakeRAID devices (requires /dev, devd)

_msg = 'Detect FakeRAID devices'
do(lambda : USEDMRAID and in_path("dmraid") and _("dmraid" "-i" "-ay"))



### Activate LVM groups, if any (after fakeraid, requires /dev, devd)

_msg = 'Activate LVM groups, if any'
do(lambda : USELVM and in_path("lwm") and os.path.exists("£{SYS}/block") and __("vgchange", "--sysinit", "-a", "y"))



### Set up non-root encrypted partition mappings, if any (after lvm, requires /dev, devd)

_msg = 'Set up non-root encrypted partition mappings'
_working()
if os.path.exists("£{ETC}/crypttab") and in_path("cryptsetup"):
    crypttab, failed = None, False
    with open("£{ETC}/crypttab", "rb") as file:
        crypttab = file.read()
    crypttab = sh_tab(crypttab.decode("utf-8", "replace"), 4)
    crypttab = [e[:3] + [" ".join(e[3:])] for e in crypttab]
    for (name, device, password, options) in crypttab:
        for key in ["ID", "UUID", "PARTUUID", "LABEL"]:
            if device.startswith(key + "="):
                device = device[len(key) + 1:].replace(" ", "\\x")
                device = "£{DEV}/disk/by-" + device.lower() + "/" + device
                break
        
        proc = None
        open_verb, a, b, entry_failed = "create", name, device, False
        if __("cryptsetup", "isLuks", device):
            open_verb, a, b = "luksOpen", b, a
        
        if password == "SWAP":
            overwriteokay = False
            if os.access(device, os.F_OK | os.R_OK):
                if os.path.stat.S_ISBLK(os.stat(device).st_mode):
                    # This is DANGEROUS! If there is any known file system,
                    # partition table, RAID, or LVM volume on the device,
                    # we don't overwrite it.
                    #
                    # 'blkid' returns 2 if no valid signature has been found.
                    # Only in this case should we allow overwriting the device.
                    #
                    # This sanity check _should_ be sufficient, but it might not.
                    # This may cause data loss if it is not used carefully.
                    proc = Popen(["blkid", "-p", device], stdout = PIPE, stderr = PIPE)
                    proc.wait()
                    if proc.returncode == 2:
                        overwriteokay = True
            if not overwriteokay:
                entry_failed = True
            elif __("crypttab", "-d", "£{DEV}/urandom", options, open_verb, a, b):
                entry_failed = not __("mkswap", "-f", "-L", name, "£{DEV}/mapper/name")
            proc = None
        
        elif password == "ASK":
            with open("£{DEV}/console", "r") as console:
                proc = Popen(["cryptsetup", options, open_verb, a, b], stdin = console)
            proc.wait()
        
        elif password.startswith("£{DEV}/"):
            try:
                ckdev = password.split(":")[0]
                cka = ":".join(password.split(":")[1:])
                ckb = cka.split(":")[0]
                cka = ":".join(ska.split(":")[1:])
                ckfile = "£{DEV}/ckfile"
                ckdir = "£{DEV}/ckdir"
                no_digits = True
                for i in reversed(range(len(cka))):
                    if ord('0') <= ord(cka[i]) <= ord('9'):
                        no_digits = False
                        break
                if no_digits:
                    # Use a file on the device
                    # cka is not numeric: cka=filesystem, ckb=path
                    os.mkdir(ckdir)
                    _("mount", "-r", "-t", cka, ckdev, ckdir)
                    with open(ckdir + "/" + ckb, "rb") as ifile:
                        with open(ckfile, "wb") as ofile:
                            ofile.write(ifile.read())
                            ofile.flush()
                    _("umount", ckdir)
                    os.rmdir(ckdir)
                else:
                    # Read raw data from the block device
                    # cka is numeric: cka=offset, ckb=length
                    proc = ["dd", "if=" + ckdev, "of=" + ckfile,
                            "bs=1", "skip=" + cka, "count=" + ckb]
                    proc = Popen(proc, stdout = PIPE, stderr = PIPE)
                    proc.wait()
                __("cryptsetup", "-d", ckfile, options, open_verb, a, b)
                proc = ["dd", "if=£{DEV}/urandom", "of=" + ckfile,
                        "bs=1", "conv=notrunc", "count=" + str(os.stat(ckfile).st_size)]
                proc = Popen(proc, stdout = PIPE, stderr = PIPE)
                proc.wait()
                os.remove(ckfile)
            except:
                proc = None
                entry_failed = True
        
        elif password.startswith("/"):
            proc = Popen(["cryptsetup", "-d", password, open_verb, options, a, b], stdout = PIPE)
            proc.wait()
        
        else:
            proc = Popen(["cryptsetup", options, open_verb, a, b], stdin = PIPE, stdout = PIPE)
            proc.communicate(password.encode("utf-8"))
        
        if (proc is not None) and (proc.returncode != 0):
            entry_failed = True
        failed |= entry_failed
    print()
    _done()
    
    
    # Maybe somepony has LVM on an encrypted block device
    _msg = 'Activate LVM groups, if any'
    do(lambda : USELVM and in_path("lwm") and os.path.exists("£{SYS}/block") and __("vgchange", "--sysinit", "-a", "y"))
else:
    _done()



### Check filesystems (after crypt, requires /dev, devd, /run, /proc)
### Single-user login and/or automatic reboot if needed

_msg = 'Check filesystems'
_working()

fsckret = 0

try:
    if in_path("fsck"):
        cmdline = None
        with open("£{PROC}/cmdline", "rb") as file:
            cmdline = file.read().decode("utf-8", "replace").replace("\n", "").split(" ")
    
        fsck = ["fsck", "-A", "-T", "-C", "-a", "-t"]
        fsck.append("no" + NETFS.replace(",", ",no") + ",noopts=_netdev")
        
        if os.path.exists("/forcefsck") or ('forcefsck' in cmdline):
            fsck += ["--", "-f"]
        elif os.path.exists("/fastboot") or ('fastboot' in cmdline):
            fsck = None
        elif os.path.exists("£{RUN}/initramfs/root-fsck"):
            fsck.append("-M")
        
        if fsck is not None:
            proc = Popen(fsck)
            proc.wait()
            fsckret = proc.returncode
    else:
        print('fsck is not in PATH')
        _warning()
    
    if (fsckret | 33) != 33: # Ignore conditions 'FS errors corrected' and 'Cancelled by the user'
        if (fsckret | 2) != 0:
            print()
            print("********************** REBOOT REQUIRED *********************")
            print("*                                                          *")
            print("* The system will be rebooted automatically in 15 seconds. *")
            print("*                                                          *")
            print("************************************************************")
            print()
            time.sleep(15)
        else:
            print()
            print("*****************  FILESYSTEM CHECK FAILED  ****************")
            print("*                                                          *")
            print("*  Please repair manually and reboot. Note that the root   *")
            print("*  file system is currently mounted read-only. To remount  *")
            print("*  it read-write, type: mount -o remount,rw /              *")
            print("*  When you exit the maintenance shell, the system will    *")
            print("*  reboot automatically.                                   *")
            print("*                                                          *")
            print("************************************************************")
            print()
            _singular('Single user login')
            _("sulogin", "-p")
        print("Automatic reboot in progress...")
        _try(_("umount", "-a"))
        _try(_("mount", "-o", "remount,ro", "/"))
        _singular('Reboot')
        _("reboot", "-f")
        sys.exit(0)
    _done()
except:
    _failure()



### Remount root filesystem (requires fsck)

_msg = 'Remount root filesystem'
do(lambda : _("mount", "-o", "remount", "/"))



### Mount all the local filesystems (requires remount)

_msg = 'Mount all the local filesystems'
do(lambda : _("mount", "-a", "-t", "no" + NETFS.replace(",", ",no"), "-O", "no_netdev"))



### Activate swap (requires mount)

_msg = 'Activate swap'
t9 = async(lambda : _("swapon", "-a"))



### Activate monitoring of LVM groups (requires mount)

_async('Activate monitoring of LVM groups')
def lvm_monitor():
    if USELVM and in_path("lwm") and os.path.exists("£{SYS}/block"):
        __("vgchange", "--monitor", "y")
t10 = async(lvm_monitor)



### Configure time zone (requires mount)

_async('Configure time zone')
def time_zone():
    try:
        if not TIMEZONE == "":
            zonefile = "£{USR}£{SHARE}/zoneinfo/" + TIMEZONE
            if not os.path.exists(zonefile):
                print('Invalid time zone specified in £{ETC}/rc.conf')
                _failure('Configure time zone')
            elif not os.path.islink("£{ETC}/localtime"):
                if os.path.realpath("£{ETC}/localtime") != os.path.realpath(zonefile):
                    os.remove("£{ETC}/localtime")
                    os.unlink(zonefile, "£{ETC}/localtime")
    except:
        _failure('Configure time zone')
t11 = async(time_zone)



### Initialise random seed (next to last)

_msg = 'Initialise random seed'
_waiting() ## Join with remaining threads
t5.join()
t6.join()
t7.join()
t8.join()
t9.join()
t10.join()
t11.join()

_working()
try:
    with open("£{VAR_LIB}/£{MISC}/random-seed", "rb") as rfile:
        with open("£{DEV}/urandom", "wb") as wfile:
            wfile.write(rfile.read())
            wfile.flush()
    _done()
except:
    _failure()



### Save dmesg log (last)

_msg = 'Save dmesg log'
_waiting()
try:
    dmesg_mode = 0o644
    if os.path.exists("£{PROC}/sys/kernel/dmesg_restrict"):
        with open("£{PROC}/sys/kernel/dmesg_restrict", "r") as file:
            if file.read().replace("\n", "") == "1":
                dmesg_mode = 0o600
    
    os.path.exists("£{VAR_LOG}/dmesg.log") and os.remove("£{VAR_LOG}/dmesg.log")
    with open("£{VAR_LOG}/dmesg.log", "x") as file:
        file.flush()
    os.chmod("£{VAR_LOG}/dmesg.log", dmesg_mode)
    with open("£{VAR_LOG}/dmesg.log", "ab") as file:
        Popen(["dmesg"], stdout = file).wait()
        file.flush()
    _done()
except:
    _failure()

