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

# Klaenge der S-Launcher-Welten (rein synthetisch, WAV)
mkdir -p "$P/usr/share/biblix/s-launcher/klaenge"
python3 - "$P/usr/share/biblix/s-launcher/klaenge" <<'PY'
import math, random, struct, sys, wave
RATE = 22050
ziel = sys.argv[1]

def leer(sek):
    return [0.0] * int(RATE * sek)

def glocke(buf, start, freq, dauer, laut, abkling=6.0, obertoene=((1, 1.0), (2.76, 0.35), (5.4, 0.12))):
    a = int(start * RATE)
    for i in range(int(dauer * RATE)):
        t = i / RATE
        h = math.exp(-abkling * t) * min(1.0, t * 400)
        s = sum(g * math.sin(2 * math.pi * freq * m * t) for m, g in obertoene)
        if a + i < len(buf):
            buf[a + i] += laut * h * s

def schreiben(name, buf):
    spitze = max(1e-6, max(abs(x) for x in buf))
    faktor = min(1.0, 0.22 / spitze)   # leise: etwa -13 dB
    with wave.open(f"{ziel}/{name}", "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x * faktor)) * 32767)) for x in buf))

# Aufzug-Ding: ein weicher Gong
b = leer(1.2)
glocke(b, 0, 1046.5, 1.2, 0.35, abkling=3.5)
schreiben("aufzug-ding.wav", b)

# Tower fertig: Hochfahr-Summen und ein heller Akkord
b = leer(1.1)
for i in range(int(0.45 * RATE)):
    t = i / RATE
    f = 180 + 700 * (t / 0.45) ** 2
    h = min(1.0, t * 30) * (1 - t / 0.45 * 0.3)
    b[i] += 0.25 * h * (math.sin(2 * math.pi * f * t) + 0.3 * math.sin(4 * math.pi * f * t))
for f in (880, 1108.7, 1318.5):
    glocke(b, 0.42, f, 0.68, 0.18, abkling=5)
schreiben("tower-fertig.wav", b)

# Kassa: mechanisches Klacken und "Ka-tsching"
b = leer(0.9)
zufall = random.Random(5)
for i in range(int(0.05 * RATE)):
    b[i] += 0.5 * zufall.uniform(-1, 1) * math.exp(-60 * i / RATE)
glocke(b, 0.07, 2093, 0.8, 0.3, abkling=5)
glocke(b, 0.13, 2637, 0.75, 0.3, abkling=5)
schreiben("kassa.wav", b)

# Bestellung fertig: Ding-Dong wie am Abholschalter
b = leer(1.6)
glocke(b, 0, 784, 1.0, 0.4, abkling=3)
glocke(b, 0.42, 659.3, 1.15, 0.4, abkling=3)
schreiben("bestellung-fertig.wav", b)

# Schlicht fertig: kurzer, heller Doppelton
b = leer(0.5)
glocke(b, 0, 660, 0.3, 0.3, abkling=12)
glocke(b, 0.1, 990, 0.4, 0.3, abkling=10)
schreiben("fertig.wav", b)
PY
