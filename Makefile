VER  := $(shell git describe)

DIRS := \
	/etc/rc.d \
	/etc/conf.d \
	/etc/rc.d/functions.d \
	/etc/logrotate.d \
	/etc/profile.d \
	/usr/lib/tmpfiles.d \
	/usr/sbin \
	/usr/share/bash-completion/completions \
	/usr/share/zsh/site-functions \
	/usr/share/man/man5 \
	/usr/share/man/man8

all: doc

installdirs:
	install -dm755 $(foreach DIR, $(DIRS), $(DESTDIR)$(DIR))

install: installdirs doc
	install -m644 -t $(DESTDIR)/etc inittab rc.conf
	install -m755 -t $(DESTDIR)/etc rc.local rc.local.shutdown rc.multi rc.shutdown rc.single rc.sysinit
	install -m644 -t $(DESTDIR)/etc/logrotate.d bootlog
	install -m644 -t $(DESTDIR)/etc/rc.d functions
	install -m755 -t $(DESTDIR)/etc/rc.d hwclock network netfs
	install -m755 -t $(DESTDIR)/etc/profile.d locale.sh
	install -m755 -t $(DESTDIR)/usr/sbin rc.d
	install -m644 -t $(DESTDIR)/usr/share/man/man5 rc.conf.5
	install -m644 -t $(DESTDIR)/usr/share/man/man8 rc.d.8
	install -m644 tmpfiles.conf $(DESTDIR)/usr/lib/tmpfiles.d/initscripts.conf
	install -m644 -T bash-completion $(DESTDIR)/usr/share/bash-completion/completions/rc.d
	install -m644 -T zsh-completion $(DESTDIR)/usr/share/zsh/site-functions/_rc.d

%.5: %.5.txt
	a2x -d manpage -f manpage $<

%.8: %.8.txt
	a2x -d manpage -f manpage $<

doc: rc.conf.5 rc.d.8

clean:
	rm -f rc.conf.5 rc.d.8

tar:
	git archive HEAD --prefix=initscripts-$(VER)/ | xz > initscripts-$(VER).tar.xz

release: tar
	scp initscripts-$(VER).tar.xz gerolde.archlinux.org:/srv/ftp/other/initscripts/
	scp initscripts-$(VER).tar.xz pkgbuild.com:~/packages/initscripts/trunk/

.PHONY: all installdirs install doc clean tar release
