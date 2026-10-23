#!/bin/bash
# biblix-browser: uBlock Origin von addons.mozilla.org holen (Firefox prueft die Mozilla-Signatur
# beim Laden selbst), Ersatz-Startseite, Python pruefen.
set -euo pipefail
P="$1"; HIER="$(cd "$(dirname "$0")/.." && pwd)"
D="$P/usr/share/biblix/browser"
mkdir -p "$D/erweiterungen"
curl -fsSL --retry 3 -o "$D/erweiterungen/uBlock0@raymondhill.net.xpi" \
    "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
python3 - "$D/erweiterungen/uBlock0@raymondhill.net.xpi" <<'PY'
import json, sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as z:
    m = json.loads(z.read("manifest.json"))
    kennung = (m.get("browser_specific_settings") or m.get("applications") or {}).get("gecko", {}).get("id")
    assert kennung == "uBlock0@raymondhill.net", kennung
    assert any(n.startswith("META-INF/") for n in z.namelist()), "nicht signiert"
    print("uBlock Origin", m.get("version"))
PY
cp "$HIER/biblix-design/usr/share/biblix/design/startseite/index.html" "$D/startseite.html"
python3 -m py_compile "$P/usr/bin/bibi-browser" && rm -rf "$P/usr/bin/__pycache__"
