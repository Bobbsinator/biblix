#!/bin/bash
# Biblix-ISO bauen. Braucht Debian 13 (oder einen Debian-13-Container), Root-Rechte,
# Internet und ca. 25 GB freien Platz.
#   bibi ./build.sh            (auf Biblix)
#   sudo ./build.sh            (auf anderen Linux-Systemen)
#   ./build.sh --lokal         Biblix-Pakete aus dem Ordner paketquelle/ statt aus dem Netz
#                              (zum Testen noch nicht veroeffentlichter Pakete)
#
# Die Biblix-Pakete kommen aus der veroeffentlichten Paketquelle (immer die neueste Version jedes Pakets),
# Signatur und Pruefsummen werden geprueft. In Git liegen keine Paketkopien mehr.
set -euo pipefail
cd "$(dirname "$0")"
. ./iso.conf
. pakete/quelle.conf
QUELLE="${QUELLE_URL:-https://$GITHUB_USER.github.io/$REPO/}"
LOKAL=no
[ "${1:-}" = "--lokal" ] && LOKAL=yes

if [ "$(id -u)" != 0 ]; then
    echo "Bitte mit Admin-Rechten starten: bibi ./build.sh (auf anderen Linux-Systemen: sudo ./build.sh)"
    exit 1
fi

if ! command -v lb >/dev/null || ! command -v gpgv >/dev/null || ! command -v curl >/dev/null; then
    echo "== Werkzeuge werden installiert"
    apt-get update
    apt-get install -y live-build xorriso squashfs-tools mtools dosfstools gpgv curl python3 librsvg2-bin
fi

echo "== Vorabpruefung"
frei=$(df -Pk . | awk 'NR==2 {print int($4 / 1024 / 1024)}')
[ "$frei" -ge 25 ] || { echo "FEHLER: nur $frei GB frei, gebraucht werden etwa 25 GB."; exit 1; }
echo "ok $frei GB frei"

echo "== Dateien vorbereiten (Windows-Zeilenenden entfernen, Rechte setzen)"
find auto config -type f ! -name '*.png' ! -name '*.gpg' ! -name '*.deb' ! -name '*.pf2' ! -name '*.jpg' \
    ! -path '*/includes.binary/*' -exec sed -i 's/\r$//' {} +
chmod +x auto/* config/hooks/normal/* config/includes.chroot/usr/lib/live/config/* \
    config/includes.chroot/usr/lib/biblix/* 2>/dev/null || true
for f in config/hooks/normal/* config/includes.chroot/usr/lib/live/config/*; do
    bash -n "$f"
done

echo "== Biblix-Pakete holen ($([ $LOKAL = yes ] && echo "lokal aus paketquelle/" || echo "$QUELLE"))"
ZIEL=config/packages.chroot
rm -f "$ZIEL"/*.deb
mkdir -p "$ZIEL"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
holen() {   # holen DATEI ZIEL
    if [ $LOKAL = yes ]; then cp "paketquelle/$1" "$2"; else curl -fsSL --retry 3 -o "$2" "$QUELLE$1"; fi
}
holen InRelease "$T/InRelease"
gpgv --keyring "$PWD/pakete/biblix-archive-keyring.gpg" --output "$T/Release" "$T/InRelease" 2>/dev/null \
    || { echo "FEHLER: Signatur der Paketquelle ungueltig."; exit 1; }
holen Packages "$T/Packages"
soll=$(awk '/^SHA256:/{s=1;next} /^[A-Z]/{s=0} s && $3=="Packages" {print $1}' "$T/Release")
[ "$(sha256sum "$T/Packages" | cut -d' ' -f1)" = "$soll" ] || { echo "FEHLER: Paketliste passt nicht zur Signatur."; exit 1; }
# Fuer jedes Paket aus pakete/ die neueste Version laut Liste (egal ob _all oder _amd64)
python3 - "$T/Packages" pakete > "$T/auswahl" <<'PY'
import sys, os, subprocess
eintraege, e = [], {}
for zeile in open(sys.argv[1], encoding="utf-8").read().splitlines() + [""]:
    if not zeile.strip():
        if e: eintraege.append(e)
        e = {}
    elif ":" in zeile and not zeile.startswith(" "):
        k, v = zeile.split(":", 1); e[k] = v.strip()
gewollt = {d for d in os.listdir(sys.argv[2]) if os.path.isfile(os.path.join(sys.argv[2], d, "DEBIAN", "control"))}
beste = {}
for e in eintraege:
    p = e.get("Package")
    if p not in gewollt: continue
    if p not in beste or subprocess.run(["dpkg", "--compare-versions", e["Version"], "gt", beste[p]["Version"]]).returncode == 0:
        beste[p] = e
fehlt = gewollt - set(beste)
if fehlt:
    print("FEHLT", " ".join(sorted(fehlt)), file=sys.stderr); sys.exit(1)
for p in sorted(beste):
    print(beste[p]["Filename"].lstrip("./"), beste[p]["SHA256"], beste[p]["Version"])
PY
while read -r datei summe version; do
    holen "$datei" "$ZIEL/$datei"
    [ "$(sha256sum "$ZIEL/$datei" | cut -d' ' -f1)" = "$summe" ] || { echo "FEHLER: Pruefsumme von $datei falsch."; exit 1; }
    echo "ok $datei"
done < "$T/auswahl"

echo "== ISO-Version $ISO_VERSION eintragen"
mkdir -p config/includes.chroot/etc
printf 'ISO_NAME="%s"\nISO_VERSION="%s"\nISO_DATUM="%s"\n' "$ISO_NAME" "$ISO_VERSION" "$(date +%Y-%m-%d)" \
    > config/includes.chroot/etc/biblix-iso

echo "== Bauen (dauert je nach Rechner 30-90 Minuten)"
lb clean
lb config
lb build

iso=$(ls -1 biblix*.iso 2>/dev/null | head -n1 || true)
if [ -z "$iso" ]; then
    echo "Kein ISO entstanden. Details in build.log."
    exit 1
fi
NAME="$ISO_NAME-$ISO_VERSION-amd64.iso"
mv "$iso" "$NAME"
sha256sum "$NAME" > "$NAME.sha256"
echo
echo "Fertig: $(pwd)/$NAME"
echo "VIEL ERFOLG."
