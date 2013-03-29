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

all: doc

install: doc
	install -dm755 "$(DESTDIR)"/etc
	install -m644 -t "$(DESTDIR)"/etc $(CONFIGS)
	install -m755 -t "$(DESTDIR)"/etc $(SCRIPTS)
	install -dm755 "$(DESTDIR)"/etc/logrotate.d
	install -m644 -t "$(DESTDIR)"/etc/logrotate.d misc/bootlog
	install -dm755 "$(DESTDIR)"/usr/libexec/rc.d
	install -m644 -t "$(DESTDIR)"/usr/libexec/rc.d scripts/functions
	install -dm755 "$(DESTDIR)"/usr/libexec/rc.d/functions.d
	install -dm755 "$(DESTDIR)"/usr/sbin
	install -m755 -t "$(DESTDIR)"/usr/sbin tools/rc.d
	install -dm755 "$(DESTDIR)"/etc/profile.d
	install -m755 -t "$(DESTDIR)"/etc/profile.d misc/read_locale.sh
	install -dm755 "$(DESTDIR)"/usr/share/info
	install -m644 -t "$(DESTDIR)"/usr/share/info $(INFO)
	install -dm755 "$(DESTDIR)"/usr/lib/pony-initialisation
	install -m755 -t "$(DESTDIR)"/usr/lib/pony-initialisation $(TOOLS)
	install -dm755 "$(DESTDIR)"/usr/lib/tmpfiles.d
	install -m644 conf/tmpfiles.conf "$(DESTDIR)"/usr/lib/tmpfiles.d/pony-initialisation.conf
	install -dm755 "$(DESTDIR)"/usr/share/bash-completion/completions
	install -m644 -T completion/bash-completion "$(DESTDIR)"/usr/share/bash-completion/completions/rc.d
	install -dm755 "$(DESTDIR)"/usr/share/zsh/site-functions
	install -m644 -T completion/zsh-completion "$(DESTDIR)"/usr/share/zsh/site-functions/_rc.d
	install -dm755 "$(DESTDIR)"/usr/share/licenses/pony-initialisation
	install -m755 "$(DESTDIR)"/usr/share/licenses/pony-initialisation COPYING LICENSE

install_systemdcompat:
	install -dm755 "$(DESTDIR)"/usr/lib/systemd/system-generators
	install -m755 -t "$(DESTDIR)"/usr/lib/systemd/system-generators systemd/pony-daemons
	install -dm755 "$(DESTDIR)"/usr/lib/systemd/system
	install -m644 -t "$(DESTDIR)"/usr/lib/systemd/system $(UNITS)
	ln -sf /dev/null "$(DESTDIR)"/usr/lib/systemd/system/netfs.service
	install -dm755 "$(DESTDIR)"/usr/lib/systemd/system/multi-user.target.wants
	ln -sf ../rc-local.service "$(DESTDIR)"/usr/lib/systemd/system/multi-user.target.wants/
	ln -sf ../pony-daemons.target "$(DESTDIR)"/usr/lib/systemd/system/multi-user.target.wants/
	install -dm755 "$(DESTDIR)"/usr/lib/systemd/system/shutdown.target.wants
	ln -sf ../rc-local-shutdown.service "$(DESTDIR)"/usr/lib/systemd/system/shutdown.target.wants/
	install -dm755 "$(DESTDIR)"/usr/lib/systemd/system/sysinit.target.wants
	install -dm755 "$(DESTDIR)"/usr/share/licenses
	ln -sf pony-initialisation "$(DESTDIR)"/usr/share/licenses/pony-initialisation-systemdcompat

install_all_daemons:
	install -dm755 "$(DESTDIR)"/usr/libexec/rc.d
	install -m755 -t "$(DESTDIR)"/usr/libexec/rc.d $(DAEMONS)

install_daemons:
	install -dm755 "$(DESTDIR)"/usr/libexec/rc.d
	install -m755 -t "$(DESTDIR)"/usr/libexec/rc.d \
	    $$(grep -rn '^# daemon for: $(DAEMON)$$' daemon | cut -d : -f 1,2 | grep :2\$$ | cut -d : -f 1)

%.info.gz: info/%.texinfo
	makeinfo "$<"
	gzip -9 "$*.info"

doc: info

info: $(INFO)

clean:
	rm -f $(MAN_PAGES) $(INFO) *.{aux,cp,fn,info,ky,log,pdf,ps,dvi,pg,toc,tp,vr}

.PHONY: all installdirs install doc clean

