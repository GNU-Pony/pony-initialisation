VER  := $(shell git describe)

DIRS := \
	/etc/rc.d \
	/etc/rc.d/functions.d \
	/etc/logrotate.d \
	/etc/profile.d \
	/usr/lib/initscripts \
	/usr/lib/tmpfiles.d \
	/usr/lib/systemd/system-generators \
	/usr/lib/systemd/system/multi-user.target.wants \
	/usr/lib/systemd/system/shutdown.target.wants \
	/usr/lib/systemd/system/sysinit.target.wants \
	/usr/sbin \
	/usr/share/bash-completion/completions \
	/usr/share/zsh/site-functions \
	/usr/share/man/man5 \
	/usr/share/man/man8 \
	/usr/share/licenses/pony-initialisation

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

MAN_PAGES := \
	man/pony-daemons.8

INFO := \
	rc.conf.info.gz \
	rc.d.info.gz

TOOLS := \
	tools/pony-binfmt \
	tools/pony-modules \
	tools/pony-sysctl \
	tools/pony-tmpfiles

UNITS := \
	systemd/pony-daemons.target \
	systemd/rc-local.service \
	systemd/rc-local-shutdown.service

all: doc

installdirs:
	install -dm755 $(foreach DIR, $(DIRS), "$(DESTDIR)"$(DIR))

install: installdirs doc
	install -m644 -t "$(DESTDIR)"/etc $(CONFIGS)
	install -m755 -t "$(DESTDIR)"/etc $(SCRIPTS)
	install -m644 -t "$(DESTDIR)"/etc/logrotate.d misc/bootlog
	install -m644 -t "$(DESTDIR)"/etc/rc.d scripts/functions
	install -m755 -t "$(DESTDIR)"/etc/rc.d $(DAEMONS)
	install -m755 -t "$(DESTDIR)"/usr/sbin tools/rc.d
	install -m755 -t "$(DESTDIR)"/etc/profile.d misc/read_locale.sh
	install -m644 -t "$(DESTDIR)"/usr/share/man/man8 $(filter %.8, $(MAN_PAGES))
	install -m644 -t "$(DESTDIR)"/usr/share/info $(INFO)
	install -m755 -t "$(DESTDIR)"/usr/lib/initscripts $(TOOLS)
	install -m755 -t "$(DESTDIR)"/usr/lib/systemd/system-generators systemd/pony-daemons
	install -m644 -t "$(DESTDIR)"/usr/lib/systemd/system $(UNITS)
	install -m644 conf/tmpfiles.conf "$(DESTDIR)"/usr/lib/tmpfiles.d/initscripts.conf
	install -m644 -T completion/bash-completion "$(DESTDIR)"/usr/share/bash-completion/completions/rc.d
	install -m644 -T completion/zsh-completion "$(DESTDIR)"/usr/share/zsh/site-functions/_rc.d
	install -m755 "$(DESTDIR)"/usr/share/licenses/pony-initialisation COPYING LICENSE
	ln -sf /dev/null "$(DESTDIR)"/usr/lib/systemd/system/netfs.service
	ln -sf ../rc-local.service "$(DESTDIR)"/usr/lib/systemd/system/multi-user.target.wants/
	ln -sf ../pony-daemons.target "$(DESTDIR)"/usr/lib/systemd/system/multi-user.target.wants/
	ln -sf ../rc-local-shutdown.service "$(DESTDIR)"/usr/lib/systemd/system/shutdown.target.wants/

%: %.txt
	a2x -d manpage -f manpage "$<"

%.info.gz: info/%.texinfo
	makeinfo "$<"
	gzip -9 "$*.info"

doc: man info

man: $(MAN_PAGES)

info: $(INFO)

clean:
	rm -f $(MAN_PAGES) $(INFO)

.PHONY: all installdirs install doc clean

