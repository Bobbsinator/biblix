#!/bin/bash
# Baukiste: sauberes Debian-13-Chroot zum Kompilieren (Biblix-Wuerfel). Einmalig: bash pakete/baukiste-einrichten.sh
set -e
B=/root/baukiste
if [ ! -x $B/usr/bin/apt-get ]; then
    debootstrap --variant=minbase trixie $B http://deb.debian.org/debian
fi
mount --bind /proc $B/proc 2>/dev/null || true
cp /etc/resolv.conf $B/etc/resolv.conf
cat > $B/etc/apt/sources.list <<EOF
deb http://deb.debian.org/debian trixie main contrib non-free non-free-firmware
deb http://deb.debian.org/debian trixie-updates main
deb http://security.debian.org/debian-security trixie-security main
EOF
chroot $B apt-get update
chroot $B env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  build-essential cmake extra-cmake-modules git ca-certificates pkg-config \
  kwin-dev qt6-base-dev qt6-declarative-dev qt6-declarative-dev-tools qt6-tools-dev \
  libkf6config-dev libkf6coreaddons-dev libkf6globalaccel-dev libkf6i18n-dev libkf6kcmutils-dev \
  libkf6windowsystem-dev libkf6xmlgui-dev libepoxy-dev libwayland-dev libdrm-dev libxcb1-dev \
  libkdecorations3-dev libkf6configwidgets-dev gettext dpkg-dev
umount $B/proc 2>/dev/null || true
echo BAUKISTE-FERTIG
