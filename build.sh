#!/bin/bash
# Biblix-ISO bauen. Braucht Debian 13 (oder einen Debian-13-Container), Root-Rechte,
# Internet und ca. 25 GB freien Platz.
#   bibi ./build.sh    (auf Biblix)
#   sudo ./build.sh    (auf anderen Linux-Systemen)
set -euo pipefail
cd "$(dirname "$0")"

if [ "$(id -u)" != 0 ]; then
    echo "Bitte mit Admin-Rechten starten: bibi ./build.sh (auf anderen Linux-Systemen: sudo ./build.sh)"
    exit 1
fi

if ! command -v lb >/dev/null; then
    echo "== live-build wird installiert"
    apt-get update
    apt-get install -y live-build xorriso squashfs-tools mtools dosfstools
fi

echo "== Dateien vorbereiten (Windows-Zeilenenden entfernen, Rechte setzen)"
find auto config -type f ! -name '*.png' ! -name '*.gpg' ! -name '*.deb' ! -name '*.pf2' ! -path '*/includes.binary/*' -exec sed -i 's/\r$//' {} +
chmod +x auto/* config/hooks/normal/* config/includes.chroot/usr/lib/live/config/*

echo "== Biblix-Pakete"
# Das ISO nimmt genau die veroeffentlichten Pakete (gebaut mit pakete/bauen.sh), baut selbst nichts neu.
for d in pakete/*/DEBIAN; do
    name=$(basename "$(dirname "$d")")
    v=$(tr -d ' \r\n' < "pakete/$name/VERSION")
    if [ -f "config/packages.chroot/${name}_${v}_all.deb" ]; then
        echo "ok $name $v"
    else
        echo "FEHLT: config/packages.chroot/${name}_${v}_all.deb - erst bash pakete/bauen.sh ausfuehren"; exit 1
    fi
done

echo "== Vorabpruefung"
# (biblix-tools prueft pakete/bauen.sh selbst)
for f in config/hooks/normal/* config/includes.chroot/usr/lib/live/config/*; do
    bash -n "$f"
done

echo "== Bauen (dauert je nach Rechner 30-90 Minuten)"
lb clean
lb config
lb build

iso=$(ls -1 biblix*.iso 2>/dev/null | head -n1 || true)
if [ -z "$iso" ]; then
    echo "Kein ISO entstanden. Details in build.log."
    exit 1
fi
mv "$iso" Biblix-1.0-amd64.iso
sha256sum Biblix-1.0-amd64.iso > Biblix-1.0-amd64.iso.sha256
echo
echo "Fertig: $(pwd)/Biblix-1.0-amd64.iso"
echo "VIEL ERFOLG."
