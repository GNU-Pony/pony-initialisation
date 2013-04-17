# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.  This file is offered as-is,
# without any warranty.  [GNUAllPermissive]


SYSCONF = /etc
PREFIX = /usr
BIN = /bin
SYSBIN = /sbin
LIBEXEC = /libexec
LIB = /lib
DATA = /share
SYS = /sys
PROC = /proc
RUN = /run
DEV = /dev
SHM = $(DEV)/shm
PTS = $(DEV)/pts
LOCK = $(RUN)/lock
VAR = /var
STATE = $(VAR)/lib
LOG = $(VAR)/log
LOCALPREFIX = /usr/local


CONFIGS := \
	conf/inittab \
	conf/rc.conf

SCRIPTS := \
	scripts/rc.local \
	scripts/rc.local.shutdown \
	scripts/rc.multi \
	scripts/rc.shutdown \
	scripts/rc.single \
	scripts/rc.sysinit

DAEMONS := \
	daemon/hwclock \
	daemon/network \
	daemon/netfs

UNITS := \
	systemd/pony-daemons.target \
	systemd/rc-local.service \
	systemd/rc-local-shutdown.service

INFO := \
	rc.conf.info.gz \
	rc.d.info.gz

TOOLS := \
	tools/pony-binfmt \
	tools/pony-modules \
	tools/pony-sysctl \
	tools/pony-tmpfiles


all: doc completion/bash-completion.install completion/zsh-completion.install


install: install_dirs install_license install_core install_completion install_doc

CONFIGS_INSTALL = $(foreach $(CONFIGS), FILE, $(FILE).install)
SCRIPTS_INSTALL = $(foreach $(SCRIPTS), FILE, $(FILE).install)
TOOLS_INSTALL = $(foreach $(TOOLS), FILE, $(FILE).install)
CORE_INSTALL = misc/bootlog.install scripts/functions.install tools/rc.d.install misc/read_locale.sh.install conf/tmpfiles.conf.install
install_core: $(CONFIGS_INSTALL) $(SCRIPTS_INSTALL) $(TOOLS_INSTALL) $(CORE_INSTALL)
	for file in $(CONFIGS); do  install -m644 -T $$file.install "$(DESTDIR)$(SYSCONF)"/$$file;  done
	for file in $(SCRIPTS); do  install -m755 -T $$file.install "$(DESTDIR)$(SYSCONF)"/$$file;  done
	for file in $(TOOLS); do  install -m755 -T $$file.install "$(DESTDIR)$(PREFIX)$(LIB)"/pony-initialisation/$$file;  done
	install -m644 -T misc/bootlog.install "$(DESTDIR)$(SYSCONF)"/logrotate.d/bootlog
	install -m644 -T scripts/functions.install "$(DESTDIR)$(PREFIX)$(LIBEXEC)"/rc.d/functions
	install -m755 -T tools/rc.d.install "$(DESTDIR)$(PREFIX)$(SYSBIN)"/rc.d
	install -m755 -T misc/read_locale.sh.install"$(DESTDIR)$(SYSCONF)"/profile.d/read_locale.sh
	install -m644 -T conf/tmpfiles.conf.install "$(DESTDIR)$(PREFIX)$(LIB)"/tmpfiles.d/pony-initialisation.conf

install_doc: $(INFO)
	install -m644 -t "$(DESTDIR)$(PREFIX)$(DATA)"/info $(INFO)

install_completion: completion/bash-completion.install completion/zsh-completion.install
	install -m644 -T completion/bash-completion.install "$(DESTDIR)$(PREFIX)$(DATA)"/bash-completion/completions/rc.d
	install -m644 -T completion/zsh-completion.install "$(DESTDIR)$(PREFIX)$(DATA)"/zsh/site-functions/_rc.d

install_license:
	install -m644 COPYING LICENSE "$(DESTDIR)$(PREFIX)$(DATA)"/licenses/pony-initialisation

install_dirs:
	install -dm755 "$(DESTDIR)$(SYSCONF)"
	install -dm755 "$(DESTDIR)$(SYSCONF)"/logrotate.d
	install -dm755 "$(DESTDIR)$(PREFIX)$(LIBEXEC)"/rc.d
	install -dm755 "$(DESTDIR)$(PREFIX)$(LIBEXEC)"/rc.d/functions.d
	install -dm755 "$(DESTDIR)$(PREFIX)$(SYSBIN)"
	install -dm755 "$(DESTDIR)$(SYSCONF)"/profile.d
	install -dm755 "$(DESTDIR)$(PREFIX)$(DATA)"/info
	install -dm755 "$(DESTDIR)$(PREFIX)$(LIB)"/pony-initialisation
	install -dm755 "$(DESTDIR)$(PREFIX)$(LIB)"/tmpfiles.d
	install -dm755 "$(DESTDIR)$(PREFIX)$(DATA)"/bash-completion/completions
	install -dm755 "$(DESTDIR)$(PREFIX)$(DATA)"/zsh/site-functions
	install -dm755 "$(DESTDIR)$(PREFIX)$(DATA)"/licenses/pony-initialisation


install_systemdcompatlayer: systemd/pony-daemons.install $(foreach $(UNITS), FILE, $(FILE).install)
	install -dm755 "$(DESTDIR)$(PREFIX)$(LIB)"/systemd/system-generators
	install -m755 -T systemd/pony-daemons.install "$(DESTDIR)$(PREFIX)$(LIB)"/systemd/system-generators/pony-daemons
	install -dm755 "$(DESTDIR)$(PREFIX)$(LIB)"/systemd/system
	for file in $(UNITS); do  install -m644 -T $$file.install "$(DESTDIR)$(PREFIX)$(LIB)"/systemd/system/$$file;  done
	ln -sf /dev/null "$(DESTDIR)$(PREFIX)$(LIB)"/systemd/system/netfs.service
	install -dm755 "$(DESTDIR)$(PREFIX)$(LIB)"/systemd/system/multi-user.target.wants
	ln -sf ../rc-local.service "$(DESTDIR)$(PREFIX)$(LIB)"/systemd/system/multi-user.target.wants/
	ln -sf ../pony-daemons.target "$(DESTDIR)$(PREFIX)$(LIB)"/systemd/system/multi-user.target.wants/
	install -dm755 "$(DESTDIR)$(PREFIX)$(LIB)"/systemd/system/shutdown.target.wants
	ln -sf ../rc-local-shutdown.service "$(DESTDIR)$(PREFIX)$(LIB)"/systemd/system/shutdown.target.wants/
	install -dm755 "$(DESTDIR)$(PREFIX)$(LIB)"/systemd/system/sysinit.target.wants
	install -dm755 "$(DESTDIR)$(PREFIX)$(DATA)"/licenses
	ln -sf pony-initialisation "$(DESTDIR)$(PREFIX)$(DATA)"/licenses/pony-initialisation-systemdcompat


install_all_daemons: $(foreach $(DAEMONS), FILE, $(FILE).install)
	install -dm755 "$(DESTDIR)$(PREFIX)$(LIBEXEC)"/rc.d
	for file in $(DAEMONS); do  install -m755 -T $$file.install "$(DESTDIR)$(PREFIX)$(LIBEXEC)"/rc.d/$$file;  done


DAEMON_INSTALLS = $(shell grep -rn '^\x23 daemon for: $(DAEMON)$$' daemon | cut -d ':' -f '1,2' | grep ':2$$' | cut -d ':' -f 1)
install_daemons: $(foreach $(DAEMON_INSTALLS), FILE, $(FILE).install)
	install -dm755 "$(DESTDIR)$(PREFIX)$(LIBEXEC)"/rc.d
	for file in $(DAEMON_INSTALLS); do  install -m755 -T $$file.install "$(DESTDIR)$(PREFIX)$(LIBEXEC)"/rc.d/$$file;  done



doc: info

info: $(INFO)

%.info.gz: info/%.texinfo.install
	makeinfo "$<"
	gzip -9 "$*.info"


info/%.texinfo.install: info/%.texinfo
	cp "$<" "$@"
	sed -i 's:set DATA /share:set DATA $(DATA):g' "$@"
	sed -i 's:set SYS /sys:set SYS $(SYS):g' "$@"
	sed -i 's:set DEV /dev:set DEV $(DEV):g' "$@"
	sed -i 's:set PREFIX /usr:set PREFIX $(PREFIX):g' "$@"
	sed -i 's:set SYSCONF /etc:set SYSCONF $(SYSCONF):g' "$@"
	sed -i 's:set LIBEXEC /libexec:set LIBEXEC $(LIBEXEC):g' "$@"

%.install: %
	cp "$<" "$@"
	sed -i 's:</dev/shm>:$(SHM):g' "$@"
	sed -i 's:</dev/pts>:$(PTS):g' "$@"
	sed -i 's:</dev>:$(DEV):g' "$@"
	sed -i 's:</etc>:$(SYSCONF):g' "$@"
	sed -i 's:</run/lock>:$(LOCK):g' "$@"
	sed -i 's:</run>:$(RUN):g' "$@"
	sed -i 's:</proc>:$(PROC):g' "$@"
	sed -i 's:</sys>:$(SYS):g' "$@"
	sed -i 's:</var/lib>:$(STATE):g' "$@"
	sed -i 's:</var/log>:$(LOG):g' "$@"
	sed -i 's:</var>:$(VAR):g' "$@"
	sed -i 's:</usr>:$(PREFIX):g' "$@"
	sed -i 's:</usr/local>:$(LOCALPREFIX):g' "$@"
	sed -i 's:</sbin>:$(SYSBIN):g' "$@"
	sed -i 's:</bin>:$(BIN):g' "$@"
	sed -i 's:</libexec>:$(LIBEXEC):g' "$@"
	sed -i 's:</lib>:$(LIB):g' "$@"
	sed -i 's:</share>:$(DATA):g' "$@"


clean:
	rm -f $(MAN_PAGES) $(INFO) {*,*/*}.{aux,cp,fn,info,ky,log,pdf,ps,dvi,pg,toc,tp,vr,install} || true


.PHONY: all installdirs install doc clean

