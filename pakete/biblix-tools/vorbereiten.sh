#!/bin/bash
# biblix-tools: Paketquelle + Schluessel einbauen, Versionsnummer in den S-Launcher, Python pruefen.
set -euo pipefail
P="$1"; HIER="$(cd "$(dirname "$0")/.." && pwd)"
. "$HIER/quelle.conf"
URL="${QUELLE_URL:-https://$GITHUB_USER.github.io/$REPO/}"
install -D -m 644 "$HIER/biblix-archive-keyring.gpg" "$P/usr/share/keyrings/biblix-archive-keyring.gpg"
mkdir -p "$P/etc/apt/sources.list.d"
cat > "$P/etc/apt/sources.list.d/biblix.sources" <<SRC
# Biblix-Updates: alle Biblix-Pakete (S-Launcher, System, Design, Treiber)
Types: deb
URIs: $URL
Suites: ./
Signed-By: /usr/share/keyrings/biblix-archive-keyring.gpg
SRC
VERSION=$(tr -d ' \r\n' < "$HIER/biblix-tools/VERSION")
sed -i "s/^VERSION = \".*\"/VERSION = \"$VERSION\"/" "$P/usr/share/biblix/s-launcher/s_launcher.py"
python3 -m py_compile "$P/usr/share/biblix/s-launcher/s_launcher.py"
rm -rf "$P/usr/share/biblix/s-launcher/__pycache__"
