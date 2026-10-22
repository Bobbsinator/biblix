#!/bin/bash
# biblix-bibiplexx: Symbol (Bibiplexx-Logo aus Biblix Design), Kino-Gong, Versionsnummer.
set -euo pipefail
P="$1"; HIER="$(cd "$(dirname "$0")/.." && pwd)"
LIB="$HIER/biblix-design/usr/share/biblix/design/lib"
VERSION=$(tr -d ' \r\n' < "$HIER/biblix-bibiplexx/VERSION")
sed -i "s/^VERSION = \".*\"/VERSION = \"$VERSION\"/" "$P/usr/share/biblix/bibiplexx/bibiplexx.py"
mkdir -p "$P/usr/share/icons/hicolor/scalable/apps"
PYTHONPATH="$LIB" python3 - "$P" <<'PY'
import sys
from pathlib import Path
from biblix_design import grafik, klaenge
p = Path(sys.argv[1])
(p / "usr/share/icons/hicolor/scalable/apps/de.biblix.Bibiplexx.svg").write_text(grafik.logo_bibiplexx(), encoding="utf-8")
spur = klaenge._als_spur(klaenge.akzent_kino(), 0.9)
spur.speichern(p / "usr/share/biblix/bibiplexx/gong.wav", ziel_db=-6.0)
PY
python3 -m py_compile "$P/usr/share/biblix/bibiplexx/bibiplexx.py"
rm -rf "$P/usr/share/biblix/bibiplexx/__pycache__" "$LIB/biblix_design/__pycache__"
