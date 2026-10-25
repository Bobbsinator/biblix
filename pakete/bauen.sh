#!/bin/bash
# Baut alle Biblix-Pakete (pakete/<name>/ mit DEBIAN/ und VERSION), legt sie in die
# Paketquelle (paketquelle/) und ins ISO (config/packages.chroot/) und signiert die Quelle.
# Laeuft in WSL/Debian:  bash pakete/bauen.sh
#   Ein Paket wird nur gebaut, wenn es seine Version noch nicht in paketquelle/ gibt.
#   Neue Version = Zahl in pakete/<name>/VERSION erhoehen.
#   QUELLE_URL=...  andere Adresse fuer die Paketquelle (zum Testen)
#   QUELLE_DIR=...  anderer Ordner fuer die Paketquelle (zum Testen)
set -euo pipefail
cd "$(dirname "$0")"
HIER=$(pwd)
. ./quelle.conf
NAME="Biblix Paketquelle"
case "${QUELLE_URL:-https://$GITHUB_USER.github.io/}" in *@NOCH_OFFEN@*) echo "GitHub-Benutzer fehlt in pakete/quelle.conf"; exit 1 ;; esac
[ -f biblix-archive-keyring.gpg ] || { echo "Erst bash pakete/schluessel-erzeugen.sh ausfuehren"; exit 1; }
for t in dpkg-deb apt-ftparchive gpg rsync rsvg-convert grub-mkfont curl python3 oggenc; do
    command -v $t >/dev/null || { echo "$t fehlt (apt install dpkg-dev apt-utils gnupg rsync librsvg2-bin grub-common fonts-dejavu-core curl python3 vorbis-tools)"; exit 1; }
done

QUELLE=$(mkdir -p "${QUELLE_DIR:-../paketquelle}" && cd "${QUELLE_DIR:-../paketquelle}" && pwd)
ISO=$(mkdir -p ../config/packages.chroot && cd ../config/packages.chroot && pwd)
W=$(mktemp -d)
trap 'rm -rf "$W"' EXIT
gebaut=0

for d in */DEBIAN; do
    name=${d%/DEBIAN}
    VERSION=$(tr -d ' \r\n' < "$name/VERSION")
    ARCH=$(sed -n 's/^Architecture: *//p' "$name/DEBIAN/control" | tr -d ' \r\n')
    DEB="${name}_${VERSION}_${ARCH:-all}.deb"
    if [ -f "$QUELLE/$DEB" ]; then
        echo "= $name $VERSION (unveraendert)"
    else
        echo "+ $name $VERSION wird gebaut"
        P="$W/$name"
        rsync -a --exclude VERSION --exclude vorbereiten.sh "$name/" "$P/"
        # Windows/OneDrive: Zeilenenden nur in Textdateien reparieren, Rechte setzen
        find "$P" -type f -exec grep -Il . {} + | while IFS= read -r f; do sed -i 's/\r$//' "$f"; done
        find "$P" -type d -exec chmod 755 {} +
        find "$P" -type f -exec chmod 644 {} +
        for f in "$P"/usr/bin/* "$P"/usr/lib/biblix/* "$P"/etc/kernel/*/* "$P"/DEBIAN/preinst "$P"/DEBIAN/postinst "$P"/DEBIAN/prerm "$P"/DEBIAN/postrm; do
            [ -f "$f" ] && chmod 755 "$f"
        done
        sed -i "s/@VERSION@/$VERSION/" "$P/DEBIAN/control"
        [ -f "$name/vorbereiten.sh" ] && bash "$name/vorbereiten.sh" "$P"
        # Python-Module pruefen
        find "$P" -name '*.py' -print0 | xargs -0 -r python3 -m py_compile
        find "$P" -name __pycache__ -type d -prune -exec rm -rf {} +
        # Skripte pruefen, bevor irgendetwas veroeffentlicht wird
        for f in "$P"/usr/bin/* "$P"/usr/lib/biblix/* "$P"/etc/kernel/*/* "$P"/DEBIAN/preinst "$P"/DEBIAN/postinst "$P"/DEBIAN/prerm "$P"/DEBIAN/postrm; do
            [ -f "$f" ] || continue
            head -1 "$f" | grep -qE '^#!.*(ba)?sh' && bash -n "$f"
            head -1 "$f" | grep -qE '^#!.*python3' && python3 -m py_compile "$f" && rm -rf "$(dirname "$f")/__pycache__"
        done
        dpkg-deb --root-owner-group -Zxz --build "$P" "$QUELLE/$DEB" >/dev/null
        gebaut=1
    fi
    rm -f "$ISO/${name}"_*.deb
    cp "$QUELLE/$DEB" "$ISO/"
done

if [ $gebaut = 1 ] || [ ! -f "$QUELLE/InRelease" ]; then
    cd "$QUELLE"
    apt-ftparchive packages . > Packages
    gzip -9 -k -f Packages
    apt-ftparchive -o APT::FTPArchive::Release::Origin=Biblix -o APT::FTPArchive::Release::Label=Biblix \
        -o APT::FTPArchive::Release::Suite=stable release . > Release
    rm -f InRelease Release.gpg
    gpg --batch --yes --local-user "$NAME" --clearsign -o InRelease Release
    gpg --batch --yes --local-user "$NAME" -abs -o Release.gpg Release
    cp "$HIER/biblix-archive-keyring.gpg" biblix-archive-keyring.gpg
    touch .nojekyll
    {
        echo '<!doctype html><meta charset="utf-8"><title>Biblix-Paketquelle</title>'
        echo '<body style="font-family:sans-serif;background:#072a36;color:#e3f3f8;padding:2em">'
        echo '<h1>Biblix-Paketquelle</h1><ul>'
        for name in $(cd "$HIER" && ls -d */DEBIAN | sed 's#/DEBIAN##'); do
            echo "<li>$name $(tr -d ' \r\n' < "$HIER/$name/VERSION")</li>"
        done
        echo '</ul><p>AUF BIBLIX GEHT DAS.</p></body>'
    } > index.html
    echo "Paketquelle neu signiert: $QUELLE"
fi
echo "Fertig. Im ISO: $(ls "$ISO" | tr '\n' ' ')"
