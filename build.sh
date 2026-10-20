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
find auto config -type f ! -name '*.png' ! -name '*.gpg' ! -name '*.deb' ! -path '*/includes.binary/*' -exec sed -i 's/\r$//' {} +
chmod +x auto/* config/hooks/normal/* config/includes.chroot/usr/lib/live/config/*

echo "== biblix-tools"
VERSION=$(tr -d ' \r\n' < pakete/VERSION)
if [ -f "config/packages.chroot/biblix-tools_${VERSION}_all.deb" ]; then
    # Genau das veroeffentlichte Paket nehmen, nicht neu bauen (sonst andere Datei, gleiche Version)
    echo "nehme vorhandenes biblix-tools $VERSION"
elif gpg --list-secret-keys "Biblix Paketquelle" >/dev/null 2>&1; then
    bash pakete/bauen.sh
else
    echo "biblix-tools fehlt: erst bash pakete/schluessel-erzeugen.sh und bash pakete/bauen.sh"; exit 1
fi

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
