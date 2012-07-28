pkgname=initscripts-git
pkgver=$(date +%Y%m%d)
pkgrel=$(git log -1 --pretty=format:%h)
pkgdesc="System initialization/bootup scripts"
arch=('any')
url="https://www.archlinux.org"
license=('GPL')
groups=('base')
conflicts=('initscripts')
provides=('initscripts=9999')
replaces=('initscripts-systemd')
backup=(etc/inittab etc/rc.conf etc/rc.local etc/rc.local.shutdown)
makedepends=('asciidoc')
depends=('glibc' 'bash' 'coreutils' 'systemd-tools' 'iproute2'
         'ncurses' 'kbd' 'findutils' 'sysvinit')
optdepends=('net-tools: legacy networking support'
            'bridge-utils: Network bridging support'
            'dhcpcd: DHCP network configuration'
            'wireless_tools: Wireless networking')
source=()
sha256sums=()

build() {
  cd ..
  make
}

package() {
  cd ..
  make DESTDIR="$pkgdir/" install
}
