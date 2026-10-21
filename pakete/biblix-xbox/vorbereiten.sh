#!/bin/bash
# biblix-xbox: Quellcode von xone (Funkadapter/Kabel) und xpadneo (Bluetooth) ins Paket legen.
# Gebaut wird beim Nutzer per DKMS, damit die Treiber auch zu jedem neuen Kernel passen.
set -euo pipefail
P="$1"
XONE=0.5.8
XONE_SHA=f1905d5046ce79b94df0501045008203c4ae4ce6f43dbcf8bd04d7c944bf420e
XPADNEO=0.10.5
XPADNEO_SHA=084c1ef57b4567c54cb4e4c01c9ae47b180c59a001457ad1e0ed574fdd09b59b
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
curl -fsSL -o "$W/xone.tgz" "https://github.com/dlundqvist/xone/archive/refs/tags/v$XONE.tar.gz"
curl -fsSL -o "$W/xpadneo.tgz" "https://github.com/atar-axis/xpadneo/archive/refs/tags/v$XPADNEO.tar.gz"
# Nur exakt die gepruefte Version nehmen
echo "$XONE_SHA  $W/xone.tgz" | sha256sum -c --quiet
echo "$XPADNEO_SHA  $W/xpadneo.tgz" | sha256sum -c --quiet
tar xzf "$W/xone.tgz" -C "$W"; tar xzf "$W/xpadneo.tgz" -C "$W"

mkdir -p "$P/usr/src" "$P/usr/lib/biblix" "$P/usr/lib/modprobe.d" "$P/usr/lib/udev/rules.d"
cp -a "$W/xone-$XONE" "$P/usr/src/xone-$XONE"
find "$P/usr/src/xone-$XONE" -type f \( -name dkms.conf -o -name '*.c' \) -exec sed -i "s/#VERSION#/$XONE/" {} +
install -m 755 "$W/xone-$XONE/install/firmware.sh" "$P/usr/lib/biblix/xone-firmware.sh"

cp -a "$W/xpadneo-$XPADNEO/hid-xpadneo" "$P/usr/src/hid-xpadneo-$XPADNEO"
sed "s/\"@DO_NOT_CHANGE@\"/\"$XPADNEO\"/" "$P/usr/src/hid-xpadneo-$XPADNEO/dkms.conf.in" > "$P/usr/src/hid-xpadneo-$XPADNEO/dkms.conf"
cp "$W/xpadneo-$XPADNEO/hid-xpadneo/etc-modprobe.d/"*.conf "$P/usr/lib/modprobe.d/"
cp "$W/xpadneo-$XPADNEO/hid-xpadneo/etc-udev-rules.d/"*.rules "$P/usr/lib/udev/rules.d/"

# Versionen in die Paketskripte eintragen
sed -i "s/@XONE@/$XONE/g; s/@XPADNEO@/$XPADNEO/g" "$P/DEBIAN/postinst" "$P/DEBIAN/prerm"
