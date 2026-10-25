#!/bin/bash
# biblix-arcade: Versionsnummer in die App schreiben, Module pruefen.
set -euo pipefail
P="$1"; HIER="$(cd "$(dirname "$0")/.." && pwd)"
VERSION=$(tr -d ' \r\n' < "$HIER/biblix-arcade/VERSION")
sed -i "s/^VERSION = \".*\"/VERSION = \"$VERSION\"/" "$P/usr/share/biblix/arcade/arcade.py"
touch "$P/usr/share/biblix/arcade/spiele/.hier-kommen-die-bibi-spiele-hin"
