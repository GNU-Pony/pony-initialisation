#!/usr/bin/python3
# -*- mode: python, coding: utf-8 -*-
#
# Common system initialisation script
#

import os

from functions import *



os_release = try_invoke(lambda : sh_lex('£{ETC}/os-release'))
rc_conf    = try_invoke(lambda : sh_lex('£{ETC}/rc.conf'))

CPU_COUNT   = get(None, lambda : len(os.listdir("£{SYS}/bus/cpu/devices")), 4)
NAME        = get(None, os_release['NAME'], '')
VERSION     = get(None, os_release['VERSION'], '')
PRETTY_NAME = get(None, os_release['PRETTY_NAME'], '')
ANSI_COLOR  = get(None, os_release['ANSI_COLOR'], '')
HOME_URL    = get(None, os_release['HOME_URL'], '')
HOSTNAME    = get(None, rc_conf['HOSTNAME'], '')



### Print distribution information

if (PRETTY_NAME == '') and (not NAME == ''):
    PRETTY_NAME = NAME
    if not VERSION == '':
        PRETTY_NAME += ' ' + version

print()
print()
if not PRETTY_NAME == '':
    if not ANSI_COLOR == '':
        print('\033[%sm%s\033[00m' % (PRETTY_NAME, ANSI_COLOR))
    else:
        print(PRETTY_NAME)
if not HOME_URL == '':
    if (not ANSI_COLOR == '') and (PRETTY_NAME == ''):
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

