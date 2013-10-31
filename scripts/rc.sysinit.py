#!/usr/bin/python3
# -*- mode: python, coding: utf-8 -*-
#
# Common system initialisation script
#

import os

from functions import *


NETFS = "nfs,nfs4,smbfs,cifs,codafs,ncpfs,shfs,fuse,fuseblk,glusterfs,davfs,fuse.glusterfs"

os_release = try_invoke(lambda : sh_lex("£{ETC}/os-release"))
rc_conf    = try_invoke(lambda : sh_lex("£{ETC}/rc.conf"))

CPU_COUNT     = get(None, lambda : len(os.listdir("£{SYS}/bus/cpu/devices")), 4)
NAME          = get(None, os_release["NAME"], "")
VERSION       = get(None, os_release["VERSION"], "")
PRETTY_NAME   = get(None, os_release["PRETTY_NAME"], "")
ANSI_COLOR    = get(None, os_release["ANSI_COLOR"], "")
HOME_URL      = get(None, os_release["HOME_URL"], "")
HOSTNAME      = get(None, rc_conf["HOSTNAME"], "")
TIMEZONE      = get(None, rc_conf["TIMEZONE"], "")
HARDWARECLOCK = get(None, rc_conf["HARDWARECLOCK"], "")
USEDMRAID     = get(None, rc_conf["USEDMRAID"], "")
MODULES       = get(None, rc_conf["MODULES"], "")
CONSOLEFONT   = get(None, rc_conf["CONSOLEFONT"], "")
CONSOLEMAP    = get(None, rc_conf["CONSOLEMAP"], "")
KEYMAP        = get(None, rc_conf["KEYMAP"], "")
LOCALE        = get(None, rc_conf["LOCALE"], "")



### Print distribution information

if (PRETTY_NAME == "") and (not NAME == ""):
    PRETTY_NAME = NAME
    if not VERSION == "":
        PRETTY_NAME += ' ' + version

print()
print()
if not PRETTY_NAME == "":
    if not ANSI_COLOR == "":
        print('\033[%sm%s\033[00m' % (PRETTY_NAME, ANSI_COLOR))
    else:
        print(PRETTY_NAME)
if not HOME_URL == "":
    if (not ANSI_COLOR == "") and (PRETTY_NAME == ""):
        print('\033[%sm%s\033[00m' % (HOME_URL, ANSI_COLOR))
    else:
        print(HOME_URL)
print()
print()



### Mount the API filesystems

mount("proc",     "proc",   "£{PROC}",    "nosuid,noexec,nodev")
mount("sysfs",    "sys",    "£{SYS}",     "nosuid,noexec,nodev")
mount("tmpfs",    "run",    "£{RUN}",     "mode=0755,nosuid,nodev")
mount("devtmpfs", "dev",    "£{DEV}",     "mode=0755,nosuid")
mount("devpts",   "devpts", "£{DEV_PTS}", "mode=0620,gid=5,nosuid,noexec", True)
mount("tmpfs",    "shm",    "£{DEV_SHM}", "mode=1777,nosuid,nodev",        True)



### Ensure that / is readonly to allow `fsck` (requires /run)
# We remount now so remount is not blocked by anything opening a file for writing

if not os.path.exists("£{RUN}/initramfs/root-fsck"):
    __("findmnt", "/", "--options", "ro") or _("mount", "-o", "remount,ro", "/")



### Log all console messages (requires /proc /run /dev)

_("bootlogd", "-p", "£{RUN}/bootlogd.pid")



### Set hostname (requires /proc)

if HOSTNAME == "":
    with open("£{ETC}/hostname", "r") as file:
        HOSTNAME="".join(file.readlines()).replace("\n", "")
if not HOSTNAME == "":
    with open("£{PROC}/sys/kernel/hostname", "wb") as file:
        file.write(HOSTNAME.encode("utf-8"))
        file.flush()



### Adjust system time and setting kernel time zone

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
            pass # TODO
            ## £{ETC}/rc.conf says the RTC is in UTC,
            ## but £{ETC}/adjtime says it is in localtime.
    else:
        if HARDWARECLOCK == 'localtime':
            pass # TODO
            ## £{ETC}/rc.conf says the RTC is in localtime,
            ## but hwclock (£{ETC}/adjtime) thinks it is in UTC.
    
    if HARDWARECLOCK in ('utc', 'localtime'):
        hwclock_args += ['--' + HARDWARECLOCK, '--noadjfile']
    else:
        hwclock_args = None

if hwclock_args is not None:
    if not TIMEZONE == "":
        os.putenv("TZ", TIMEZONE)
    _(*hwclock_args)
    os.unsetenv("TZ")



### Start/trigger udev, load MODULES, and settle udev (requires /dev, /sys, /run)

if not isinstance(MODULES, str):
    blacklist = list(filter(lambda module : module.startswith("!"), MODULES))
    if len(blacklist) > 0:
        blacklist = [blacklist[1:] for excl_module in blacklist]
        os.makedirs("£{RUN}/modprobe.d", exist_ok = True)
        with open("£{RUN}/modprobe.d/modprobe-blacklist.conf", "w") as file:
            file.write("# Autogenerated from rc.conf at boot, do not edit\n")
            file.write("blacklist %s\n" % " ".join(blacklist))
            file.flush()

devd_command = 'devd' if in_path('devd') else 'udevd'
devadm_command = 'devadm' if in_path('devadm') else 'udevadm'
# You should really have symlinks named devd devadm to your device daemon and controller

_(devd_command, "--daemon")
_(devadm_command, "trigger", "--action=add", "--type=subsystems")
_(devadm_command, "trigger", "--action=add", "--type=devices")

_("modprobe", "-ab", *list(filter(lambda module : not module.startswith("!"), MODULES)))

_(devadm_command, "settle")



### Configuring virtual consoles (requires devd (for KMS), /dev, /sys)

kbd_mode, tty_echo, vt_param = "-a", b"\033%@\n", b"0\n"
if 'UTF' in os.getenv("LANG").upper(): # UTF-8 mode
    # UTF-8 consoles are default since 2.6.24 kernel
    # this code is needed not only for older kernels,
    # but also when user has set vt.default_utf8=0 but LOCALE is *.UTF-8.
    kbd_mode, tty_echo, vt_param = "-u", b"\033%G\n", b"1\n"
# (otherwise) legacy mode: Make non-UTF-8 consoles work on 2.6.24 and newer kernels.

for tty in get_vts():
    _("kbd_mode", kbd_mode, "-C", "£{DEV}/" + tty)
    with open("£{DEV}/" + tty, "wb") as file:
        file.write(tty_echo)
        file.flush()
with open("£{SYS}/module/vt/parameters/default_utf8", "wb") as file:
    file.write(vt_param)
    file.flush()



### Set console font (requires vcon)

if (not CONSOLEMAP == "") and ('UTF' in LOCALE.upper()):
    CONSOLEMAP = "" # CONSOLEMAP in UTF-8 shouldn't be used
for tty in get_vts():
    if not CONSOLEMAP == "":
        __("setfont", "-m", CONSOLEMAP, CONSOLEFONT, "-C", tty)
    else:
        __("setfont", CONSOLEFONT, "-C", tty)



### Set keymap (requires vcon)

_("loadkeys", "-q", KEYMAP)



### Bring up the loopback interface (requires /sys)

if os.path.exists("£{SYS}/class/net/lo"):
    _("ip", "link", "set", "up", "dev", "lo")



### FakeRAID devices detection (requires /dev, devd)

if (USEDMRAID.lower() == "yes") and in_path("dmraid"):
    _("dmraid" "-i" "-ay")



### Activate LVM groups, if any (after fakeraid, requires /dev, devd)

if (USELVM.lower() == "yes") and in_path("lwm") and os.path.exists("£{SYS}/block"):
    __("vgchange", "--sysinit", "-a", "y")



### Set up non-root encrypted partition mappings, if any (after lvm, requires /dev, devd)

if os.path.exists("£{ETC}/crypttab") and in_path("cryptsetup"):
    # TODO read_crypttab do_unlock
    # Maybe somepony has LVM on an encrypted block device
    if (USELVM.lower() == "yes") and in_path("lwm") and os.path.exists("£{SYS}/block"):
        __("vgchange", "--sysinit", "-a", "y")



### Check filesystems (after crypt, requires /dev, devd)   TODO
### Single-user login and/or automatic reboot if needed



### Remounting root filesystem (requires fsck)

_("mount", "-o", "remount", "/")



### Mount all the local filesystems (requires remount)

_("mount", "-a", "-t", "no" + NETFS.replace(",", ",no"), "-O", "no_netdev")



### Activate monitoring of LVM groups (requires mount)

if (USELVM.lower() == "yes") and in_path("lwm") and os.path.exists("£{SYS}/block"):
    __("vgchange", "--monitor", "y")



### Activating swap (requires remount)

_("swapon", "-a")



### Configuring time zone (requires mount)

if not TIMEZONE == "":
    zonefile = "£{USR}£{SHARE}/zoneinfo/" + TIMEZONE
    if not os.path.exists(zonefile)
        pass ## TODO not a valid time zone
    elif not os.path.islink("£{ETC}/localtime"):
        if os.path.realpath("£{ETC}/localtime") != os.path.realpath(zonefile):
            os.remove("£{ETC}/localtime")
            os.unlink(zonefile, "£{ETC}/localtime")



### Initialising random seed

with open("£{VAR_LIB}/£{MISC}/random-seed", "rb") as rfile:
    with open("£{DEV}/urandom", "wb") as wfile:
        wfile.write(rfile.read())
        wfile.flush()



### Saving dmesg log (last)

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

