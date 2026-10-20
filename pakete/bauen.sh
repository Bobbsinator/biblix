#!/bin/bash
# Baut biblix-tools, legt es in die Paketquelle (paketquelle/) und signiert sie.
# Laeuft in WSL/Debian:  bash pakete/bauen.sh
#   QUELLE_URL=...  andere Adresse fuer die Paketquelle (zum Testen)
set -euo pipefail
cd "$(dirname "$0")"
. ./quelle.conf
NAME="Biblix Paketquelle"
VERSION=$(tr -d ' \r\n' < VERSION)
URL="${QUELLE_URL:-https://$GITHUB_USER.github.io/$REPO/}"
case "$URL" in *@NOCH_OFFEN@*) echo "GitHub-Benutzer fehlt in pakete/quelle.conf"; exit 1 ;; esac
[ -f biblix-archive-keyring.gpg ] || { echo "Erst bash pakete/schluessel-erzeugen.sh ausfuehren"; exit 1; }
for t in dpkg-deb apt-ftparchive gpg; do command -v $t >/dev/null || { echo "$t fehlt (apt install dpkg-dev apt-utils gnupg)"; exit 1; }; done

W=$(mktemp -d)
trap 'rm -rf "$W"' EXIT
cp -a biblix-tools "$W/pkg"
P="$W/pkg"
# Windows/OneDrive: Zeilenenden und Rechte reparieren
find "$P" -type f -exec sed -i 's/\r$//' {} +
find "$P" -type d -exec chmod 755 {} +
find "$P" -type f -exec chmod 644 {} +
chmod 755 "$P"/usr/bin/* "$P"/usr/lib/biblix/* "$P/DEBIAN/postinst"
sed -i "s/@VERSION@/$VERSION/" "$P/DEBIAN/control"
sed -i "s/^VERSION = \".*\"/VERSION = \"$VERSION\"/" "$P/usr/share/biblix/s-launcher/s_launcher.py"
python3 -m py_compile "$P/usr/share/biblix/s-launcher/s_launcher.py"
rm -rf "$P/usr/share/biblix/s-launcher/__pycache__"
for f in "$P"/usr/bin/* "$P"/usr/lib/biblix/* "$P/DEBIAN/postinst"; do
    case "$f" in */s-launcher) ;; *) bash -n "$f" ;; esac
done
# Paketquelle und Schluessel ins Paket, damit jedes Biblix Updates findet
install -D -m 644 biblix-archive-keyring.gpg "$P/usr/share/keyrings/biblix-archive-keyring.gpg"
mkdir -p "$P/etc/apt/sources.list.d"
cat > "$P/etc/apt/sources.list.d/biblix.sources" <<SRC
# Biblix-Updates: S-Launcher und Biblix-Werkzeuge
Types: deb
URIs: $URL
Suites: ./
Signed-By: /usr/share/keyrings/biblix-archive-keyring.gpg
SRC

DEB="biblix-tools_${VERSION}_all.deb"
dpkg-deb --root-owner-group -Zxz --build "$P" "$W/$DEB" >/dev/null
# ins ISO (live-build installiert lokale Pakete aus packages.chroot)
mkdir -p ../config/packages.chroot
rm -f ../config/packages.chroot/biblix-tools_*.deb
cp "$W/$DEB" ../config/packages.chroot/
# in die Paketquelle (aeltere Versionen bleiben fuer Rueckschritte liegen)
mkdir -p ../paketquelle
cp "$W/$DEB" ../paketquelle/
cd ../paketquelle
apt-ftparchive packages . > Packages
gzip -9 -k -f Packages
apt-ftparchive -o APT::FTPArchive::Release::Origin=Biblix -o APT::FTPArchive::Release::Label=Biblix \
    -o APT::FTPArchive::Release::Suite=stable release . > Release
rm -f InRelease Release.gpg
gpg --batch --yes --local-user "$NAME" --clearsign -o InRelease Release
gpg --batch --yes --local-user "$NAME" -abs -o Release.gpg Release
cp ../pakete/biblix-archive-keyring.gpg biblix-archive-keyring.gpg
touch .nojekyll
cat > index.html <<HTML
<!doctype html><meta charset="utf-8"><title>Biblix-Paketquelle</title>
<body style="font-family:sans-serif;background:#072a36;color:#e3f3f8;padding:2em">
<h1>Biblix-Paketquelle</h1><p>Aktuell: biblix-tools $VERSION</p><p>AUF BIBLIX GEHT DAS.</p></body>
HTML
echo "Fertig: $DEB in paketquelle/ und config/packages.chroot/ (Quelle: $URL)"
