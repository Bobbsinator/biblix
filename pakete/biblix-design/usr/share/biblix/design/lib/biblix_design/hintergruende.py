"""Biblix-Hintergruende: jedes Motiv ist ein SVG-Generator.

Allgemeine Motive folgen der Palette (also auch eigenen Farben). Firmen-Motive verwenden die
Farben ihrer Firma. Gerendert wird erst, wenn ein Bild gebraucht wird (rsvg-convert).
Firmenlogos stehen nur als Stil-Vorgabe Pate: kein Motiv ist einfach das Logo in gross.
"""
import hashlib
import math
import random
import subprocess
from pathlib import Path

from .kern import mischen, heller, dunkler, preset, palette as kern_palette
from .standorte import STANDORTE

W, H = 3840, 2160
MONO = "DejaVu Sans Mono, monospace"
SANS = "DejaVu Sans, sans-serif"


def _svg(inhalt, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<defs>{defs}</defs>{inhalt}</svg>')


def _lin(gid, stops, x1=0, y1=0, x2=0, y2=1):
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
    return f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{s}</linearGradient>'


def _rad(gid, stops, cx=0.5, cy=0.5, r=0.5):
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
    return f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}">{s}</radialGradient>'


def _glow(gid, staerke=30):
    return (f'<filter id="{gid}" x="-50%" y="-50%" width="200%" height="200%">'
            f'<feGaussianBlur stdDeviation="{staerke}"/></filter>')


def _grund(p, oben=None, unten=None):
    oben = oben or p["flaeche"]
    unten = unten or p["grund"]
    return (_lin("bg", [(0, oben, 1), (1, unten, 1)]),
            f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')


def _hex(cx, cy, r, drehung=0):
    pts = []
    for i in range(6):
        w = math.radians(60 * i - 90 + drehung)
        pts.append(f"{cx + r * math.cos(w):.1f},{cy + r * math.sin(w):.1f}")
    return " ".join(pts)


# ================================================================ Allgemein (Palette)

def schrauben_bauplan(p):
    linie = mischen(p["grund"], p["akzent"], 0.18)
    linie2 = mischen(p["grund"], p["akzent"], 0.32)
    zeich = mischen(p["grund"], p["akzent"], 0.75)
    defs, hg = _grund(p, mischen(p["grund"], p["akzent"], 0.08), p["grund"])
    s = [hg]
    for x in range(0, W, 48):
        s.append(f'<path d="M{x} 0V{H}" stroke="{linie if x % 240 else linie2}" stroke-width="{1 if x % 240 else 2}"/>')
    for y in range(0, H, 48):
        s.append(f'<path d="M0 {y}H{W}" stroke="{linie if y % 240 else linie2}" stroke-width="{1 if y % 240 else 2}"/>')
    cx, cy, r = 2500, 1080, 640
    s.append(f'<polygon points="{_hex(cx, cy, r)}" fill="none" stroke="{zeich}" stroke-width="10" stroke-linejoin="round"/>')
    s.append(f'<polygon points="{_hex(cx, cy, r - 60)}" fill="none" stroke="{zeich}" stroke-width="3" stroke-dasharray="24 16"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{r * 0.52}" fill="none" stroke="{zeich}" stroke-width="3" stroke-dasharray="6 14"/>')
    # Das B (aus dem Logo): Stamm und zwei Boegen
    k = r / 60
    s.append(f'<g transform="translate({cx - 60 * k} {cy - 60 * k}) scale({k})"><path d="M46 36 H64 a11 11 0 0 1 0 22 H46 Z M46 58 H67 a12 12 0 0 1 0 24 H46 Z" '
             f'fill="none" stroke="{p["akzent"]}" stroke-width="4" stroke-linejoin="round"/></g>')
    # Masslinien
    s.append(f'<path d="M{cx - r * 0.866} {cy + r + 120}H{cx + r * 0.866}M{cx - r * 0.866} {cy + r + 90}v60M{cx + r * 0.866} {cy + r + 90}v60" stroke="{zeich}" stroke-width="3"/>')
    s.append(f'<text x="{cx}" y="{cy + r + 104}" text-anchor="middle" font-family="{MONO}" font-size="40" fill="{zeich}">SW 1108</text>')
    s.append(f'<path d="M{cx + r + 140} {cy - r}V{cy + r}M{cx + r + 110} {cy - r}h60M{cx + r + 110} {cy + r}h60" stroke="{zeich}" stroke-width="3"/>')
    s.append(f'<text x="{cx + r + 180}" y="{cy + 14}" font-family="{MONO}" font-size="40" fill="{zeich}">1280</text>')
    # Planstempel
    sx, sy = 240, 1720
    s.append(f'<rect x="{sx}" y="{sy}" width="980" height="240" fill="none" stroke="{zeich}" stroke-width="4"/>')
    s.append(f'<path d="M{sx} {sy + 80}H{sx + 980}M{sx + 640} {sy + 80}V{sy + 240}" stroke="{zeich}" stroke-width="2"/>')
    s.append(f'<text x="{sx + 30}" y="{sy + 56}" font-family="{MONO}" font-size="42" font-weight="bold" fill="{p["text"]}">BAUPLAN BIBLIX</text>')
    s.append(f'<text x="{sx + 30}" y="{sy + 140}" font-family="{MONO}" font-size="32" fill="{zeich}">DEIN SYSTEM.</text>')
    s.append(f'<text x="{sx + 30}" y="{sy + 190}" font-family="{MONO}" font-size="32" fill="{zeich}">DEIN PROBLEM.</text>')
    s.append(f'<text x="{sx + 670}" y="{sy + 140}" font-family="{MONO}" font-size="32" fill="{zeich}">REV 2.0</text>')
    s.append(f'<text x="{sx + 670}" y="{sy + 190}" font-family="{MONO}" font-size="32" fill="{p["akzent2"]}">M 1:1</text>')
    return _svg("".join(s), defs)


def schichten(p):
    defs, hg = _grund(p)
    s = [hg]
    farben = [p["akzent"], heller(p["akzent"], 0.35), mischen(p["akzent"], p["akzent2"], 0.5), p["akzent2"]]
    y0, h, gap = 560, 150, 46
    s.append(f'<rect x="1700" y="{y0}" width="170" height="{4 * h + 3 * gap}" rx="40" fill="{p["text"]}" fill-opacity="0.92"/>')
    for i, b in enumerate([620, 820, 1000, 900]):
        y = y0 + i * (h + gap)
        s.append(f'<rect x="1920" y="{y}" width="{b}" height="{h}" rx="75" fill="{farben[i]}"/>')
        s.append(f'<rect x="1920" y="{y}" width="{b}" height="{h / 2}" rx="75" fill="#ffffff" fill-opacity="0.08"/>')
        # Schichten laufen als Spuren nach links aus dem Bild
        s.append(f'<rect x="-100" y="{y + h / 2 - 4}" width="1700" height="8" rx="4" fill="{farben[i]}" fill-opacity="0.45"/>')
        s.append(f'<rect x="{1920 + b + 80}" y="{y + h / 2 - 4}" width="{W}" height="8" rx="4" fill="{farben[i]}" fill-opacity="0.2"/>')
    return _svg("".join(s), defs)


CODE = ["bibi apt update", "bibi apt full-upgrade", "biblix-gpu", "systemctl --user status biblix-update-check",
        "flatpak list --app", "AUF BIBLIX GEHT DAS.", "fastfetch", "bibi update-grub", "journalctl -b -p 3",
        "DEIN SYSTEM. DEIN PROBLEM.", "nvidia-smi", "uname -r  # 7.2", "VIEL ERFOLG.", "ls ~/Spiele",
        "steam steam://rungameid/1938090", "biblix-design anwenden bibi-tech", "echo $((6 * 7))"]


def prompt(p):
    defs, hg = _grund(p, p["grund"], dunkler(p["grund"], 0.3))
    s = [hg]
    rnd = random.Random(4)
    leise = mischen(p["grund"], p["leise"], 0.35)
    for i in range(34):
        y = 90 + i * 62
        x = 120 + rnd.randint(0, 3) * 40
        zeile = rnd.choice(CODE)
        farbe = p["akzent"] if rnd.random() < 0.12 else leise
        s.append(f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="36" fill="{farbe}" fill-opacity="0.75">'
                 f'<tspan fill="{p["akzent2"]}">bibi@biblix</tspan> &gt;_ {zeile}</text>')
    s.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#fade)"/>')
    defs += _lin("fade", [(0, p["grund"], 0), (0.45, p["grund"], 0.2), (0.75, p["grund"], 0.92), (1, p["grund"], 1)], 0, 0, 1, 0)
    s.append(f'<path d="M2380 760 L2780 1080 L2380 1400" fill="none" stroke="{p["akzent"]}" stroke-width="110" stroke-linecap="round" stroke-linejoin="round"/>')
    s.append(f'<rect x="2930" y="1330" width="560" height="96" rx="20" fill="{p["text"]}"/>')
    return _svg("".join(s), defs)


def muttern(p):
    defs, hg = _grund(p)
    s = [hg]
    rnd = random.Random(11)
    for _ in range(140):
        x, y = rnd.uniform(-100, W + 100), rnd.uniform(-100, H + 100)
        r = rnd.choice([30, 40, 55, 70, 90, 130, 180])
        akz = rnd.random() < 0.1
        farbe = p["akzent"] if akz else mischen(p["grund"], p["leise"], rnd.uniform(0.15, 0.35))
        dick = max(4, r / 9)
        dreh = rnd.uniform(0, 60)
        s.append(f'<polygon points="{_hex(x, y, r, dreh)}" fill="{farbe if akz and r < 60 else "none"}" stroke="{farbe}" '
                 f'stroke-width="{dick}" stroke-linejoin="round" opacity="{0.95 if akz else 0.8}"/>')
        s.append(f'<circle cx="{x}" cy="{y}" r="{r * 0.42}" fill="none" stroke="{farbe}" stroke-width="{dick * 0.8}" opacity="0.8"/>')
    return _svg("".join(s), defs)


def hoehenlinien(p):
    defs, hg = _grund(p)
    s = [hg]
    for k in range(46):
        t = k / 45
        farbe = mischen(mischen(p["grund"], p["akzent"], 0.15), p["akzent"], t ** 2)
        punkte = []
        for i in range(0, 41):
            x = i * W / 40
            y = H * 0.15 + k * 38 + 160 * math.sin(i / 5.5 + k * 0.17) + 90 * math.sin(i / 2.3 - k * 0.11)
            punkte.append((x, y))
        d = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in punkte)
        s.append(f'<path d="{d}" fill="none" stroke="{farbe}" stroke-width="{3 + 4 * t:.1f}" stroke-linejoin="round" opacity="{0.35 + 0.6 * t:.2f}"/>')
    return _svg("".join(s), defs)


def waben(p):
    defs, hg = _grund(p)
    defs += _rad("licht", [(0, p["akzent"], 0.55), (1, p["akzent"], 0)], 0.7, 0.4, 0.55)
    s = [hg, f'<rect width="{W}" height="{H}" fill="url(#licht)"/>']
    r = 110
    dx, dy = r * math.sqrt(3), r * 1.5
    rnd = random.Random(2)
    for row in range(int(H / dy) + 2):
        for col in range(int(W / dx) + 2):
            x = col * dx + (dx / 2 if row % 2 else 0)
            y = row * dy
            n = rnd.random()
            fill = p["akzent"] if n < 0.03 else ("none")
            s.append(f'<polygon points="{_hex(x, y, r - 8)}" fill="{fill}" fill-opacity="0.6" '
                     f'stroke="{mischen(p["grund"], p["text"], 0.12)}" stroke-width="4"/>')
    return _svg("".join(s), defs)


def platine(p):
    defs, hg = _grund(p, p["grund"], dunkler(p["grund"], 0.25))
    defs += _glow("gl", 8)
    s = [hg]
    rnd = random.Random(8)
    bahn = mischen(p["grund"], p["akzent"], 0.35)
    for _ in range(120):
        x, y = rnd.randrange(0, W, 40), rnd.randrange(0, H, 40)
        d = f"M{x} {y}"
        for _ in range(rnd.randint(2, 5)):
            richtung = rnd.choice([(1, 0), (0, 1), (1, 1), (1, -1), (-1, 0), (0, -1)])
            l = rnd.randrange(80, 520, 40)
            x += richtung[0] * l
            y += richtung[1] * l
            d += f" L{x} {y}"
        heiss = rnd.random() < 0.12
        farbe = p["akzent"] if heiss else bahn
        if heiss:
            s.append(f'<path d="{d}" fill="none" stroke="{farbe}" stroke-width="10" filter="url(#gl)" opacity="0.8"/>')
        s.append(f'<path d="{d}" fill="none" stroke="{farbe}" stroke-width="5" stroke-linejoin="round"/>')
        s.append(f'<circle cx="{x}" cy="{y}" r="13" fill="{p["grund"]}" stroke="{farbe}" stroke-width="5"/>')
    # Chip in der Mitte
    s.append(f'<rect x="2400" y="760" width="640" height="640" rx="40" fill="{p["karte"]}" stroke="{p["akzent"]}" stroke-width="8"/>')
    for i in range(12):
        o = 800 + i * 48
        s.append(f'<path d="M2400 {o}h-60M3040 {o}h60M{2440 + i * 48} 760v-60M{2440 + i * 48} 1400v60" stroke="{bahn}" stroke-width="10"/>')
    s.append(f'<rect x="2930" y="790" width="80" height="80" fill="{p["akzent2"]}"/>')
    s.append(f'<text x="2720" y="1110" text-anchor="middle" font-family="{MONO}" font-weight="bold" font-size="120" fill="{p["text"]}">B</text>')
    return _svg("".join(s), defs)


def horizont(p):
    himmel = mischen(p["grund"], p["akzent"], 0.25)
    defs = _lin("bg", [(0, p["grund"], 1), (0.62, himmel, 1), (0.62, dunkler(p["grund"], 0.35), 1), (1, dunkler(p["grund"], 0.5), 1)])
    defs += _lin("sonne", [(0, p["akzent2"], 1), (1, p["akzent"], 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    s.append(f'<circle cx="{W / 2}" cy="{H * 0.62}" r="560" fill="url(#sonne)"/>')
    for i in range(9):
        y = H * 0.62 - 60 - i * 70
        s.append(f'<rect x="{W / 2 - 600}" y="{y}" width="1200" height="{10 + i * 3}" fill="{himmel}"/>')
    s.append(f'<rect x="0" y="{H * 0.62}" width="{W}" height="{H}" fill="url(#bg)"/>')
    gitter = mischen(dunkler(p["grund"], 0.35), p["akzent"], 0.6)
    for i in range(-30, 31):
        s.append(f'<path d="M{W / 2 + i * 60} {H * 0.62} L{W / 2 + i * 420} {H}" stroke="{gitter}" stroke-width="3"/>')
    y = H * 0.62
    k = 6
    while y < H:
        s.append(f'<path d="M0 {y:.0f}H{W}" stroke="{gitter}" stroke-width="3"/>')
        k *= 1.28
        y += k
    return _svg("".join(s), defs)


def diagonale(p):
    defs, hg = _grund(p)
    s = [hg]
    farben = [p["akzent"], p["akzent2"], heller(p["akzent"], 0.3)]
    for i, (b, f) in enumerate(zip([260, 90, 40], farben)):
        x = 1500 + i * 360
        s.append(f'<polygon points="{x},{H} {x + b},{H} {x + b + 1500},0 {x + 1500},0" fill="{f}"/>')
    s.append(f'<polygon points="0,{H} 900,{H} 2400,0 1500,0" fill="#000" fill-opacity="0.12"/>')
    return _svg("".join(s), defs)


def punkte(p):
    defs, hg = _grund(p, p["grund"], p["grund"])
    defs += _rad("licht", [(0, p["akzent"], 0.9), (0.4, p["akzent"], 0.25), (1, p["akzent"], 0)], 0.3, 0.7, 0.6)
    s = [hg, f'<rect width="{W}" height="{H}" fill="url(#licht)"/>']
    for y in range(40, H, 64):
        for x in range(40, W, 64):
            d = math.hypot((x - W * 0.3) / W, (y - H * 0.7) / H)
            r = max(2.5, 9 - d * 9)
            s.append(f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{p["text"]}" fill-opacity="{max(0.08, 0.6 - d * 0.7):.2f}"/>')
    return _svg("".join(s), defs)


def berge(p):
    defs, hg = _grund(p, mischen(p["grund"], p["akzent"], 0.3), p["grund"])
    s = [hg]
    rnd = random.Random(21)
    for schicht in range(6):
        t = schicht / 5
        farbe = mischen(mischen(p["grund"], p["akzent"], 0.45), dunkler(p["grund"], 0.4), t)
        basis = H * (0.42 + 0.1 * schicht)
        pts = [(0, H)]
        x = 0
        while x < W + 200:
            pts.append((x, basis - rnd.uniform(60, 420) * (1 - t * 0.6)))
            x += rnd.uniform(160, 420)
        pts.append((W, H))
        s.append(f'<polygon points="{" ".join(f"{a:.0f},{b:.0f}" for a, b in pts)}" fill="{farbe}"/>')
    s.insert(1, f'<circle cx="2900" cy="560" r="150" fill="{p["akzent2"]}"/>')
    return _svg("".join(s), defs)


# ================================================================ Bibi Tech: Exabibi Tower

def _tower(x, unten, hoehe, breite, fuell, kante, fenster=None, rnd=None, sp=1.0):
    oben = unten - hoehe
    s = [f'<path d="M{x - breite / 2} {unten} L{x - breite / 2} {oben + hoehe * 0.06} L{x - breite * 0.18} {oben} '
         f'L{x + breite * 0.18} {oben} L{x + breite / 2} {oben + hoehe * 0.06} L{x + breite / 2} {unten} Z" '
         f'fill="{fuell}" stroke="{kante}" stroke-width="{3 * sp}"/>',
         f'<path d="M{x} {oben} V{oben - hoehe * 0.09}" stroke="{kante}" stroke-width="{6 * sp}"/>']
    if fenster and rnd:
        for k in range(94):
            y = unten - (k + 1) * (hoehe * 0.92 / 95)
            for j in range(-4, 5):
                if rnd.random() < 0.38:
                    s.append(f'<rect x="{x + j * breite / 10 - breite / 40}" y="{y:.0f}" width="{breite / 20:.0f}" '
                             f'height="{max(2, hoehe / 260):.0f}" fill="{fenster}" fill-opacity="{rnd.uniform(0.5, 1):.2f}"/>')
    return "".join(s)


def _stadt(p, unten, farbe, rnd, hoch=420):
    s = []
    x = -50
    while x < W:
        b = rnd.uniform(70, 220)
        h = rnd.uniform(80, hoch)
        s.append(f'<rect x="{x:.0f}" y="{unten - h:.0f}" width="{b:.0f}" height="{h + 10:.0f}" fill="{farbe}"/>')
        x += b + rnd.uniform(4, 30)
    return "".join(s)


def tower_nacht(p):
    rnd = random.Random(1)
    defs = _lin("bg", [(0, "#040812", 1), (0.7, "#0d1a33", 1), (1, "#16264a", 1)])
    defs += _glow("gl", 18) + _glow("gl2", 60)
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for _ in range(260):
        s.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(0, H * 0.6):.0f}" r="{rnd.uniform(1, 3):.1f}" fill="#e8ecf2" fill-opacity="{rnd.uniform(0.2, 0.9):.2f}"/>')
    s.append(_stadt(p, 1880, "#0b1426", rnd, 380))
    s.append(f'<circle cx="1920" cy="240" r="60" fill="#FFD400" filter="url(#gl2)" opacity="0.7"/>')
    s.append(_tower(1920, 1900, 1650, 300, "#111d36", "#378ADD", "#85B7EB", rnd))
    s.append(f'<circle cx="1920" cy="102" r="16" fill="#FFD400"/><circle cx="1920" cy="102" r="30" fill="#FFD400" filter="url(#gl)"/>')
    s.append(f'<rect x="0" y="1880" width="{W}" height="{H}" fill="#060c1a"/>')
    for i in range(70):
        y = 1900 + i * 4
        s.append(f'<path d="M1860 {y}h120" stroke="#85B7EB" stroke-width="3" opacity="{max(0, 0.5 - i * 0.007):.2f}"/>')
    s.append('<path d="M0 1960 Q960 1920 1920 1965 T3840 1950" fill="none" stroke="#1e3a5c" stroke-width="6"/>')
    return _svg("".join(s), defs)


def tower_bauplan(p):
    defs = _lin("bg", [(0, "#0b2340", 1), (1, "#061a33", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for x in range(0, W, 60):
        s.append(f'<path d="M{x} 0V{H}" stroke="#1e3a5c" stroke-width="{2 if x % 300 == 0 else 1}"/>')
    for y in range(0, H, 60):
        s.append(f'<path d="M0 {y}H{W}" stroke="#1e3a5c" stroke-width="{2 if y % 300 == 0 else 1}"/>')
    x, unten, h, b = 1700, 1960, 1700, 320
    s.append(_tower(x, unten, h, b, "none", "#B5D4F4"))
    for k in range(0, 95, 5):
        y = unten - k * h * 0.92 / 94
        s.append(f'<path d="M{x - b / 2} {y:.0f}h{b}" stroke="#85B7EB" stroke-width="{2 if k % 10 else 3}"/>')
        if k % 10 == 0:
            s.append(f'<text x="{x - b / 2 - 30}" y="{y + 12:.0f}" text-anchor="end" font-family="{MONO}" font-size="30" fill="#85B7EB">OG {k}</text>')
    s.append(f'<path d="M2120 {unten - h - h * 0.09}V{unten}M2090 {unten - h - h * 0.09}h60M2090 {unten}h60" stroke="#FFD400" stroke-width="4"/>')
    s.append(f'<text x="2170" y="{unten - h / 2}" font-family="{MONO}" font-size="64" fill="#FFD400">444 m</text>')
    s.append(f'<text x="2170" y="{unten - h / 2 + 70}" font-family="{MONO}" font-size="36" fill="#85B7EB">94 OBERIRDISCHE GESCHOSSE</text>')
    s.append(f'<path d="M1000 {unten}H2600" stroke="#B5D4F4" stroke-width="4"/>')
    s.append(f'<rect x="2620" y="1720" width="1000" height="260" fill="none" stroke="#B5D4F4" stroke-width="4"/>')
    s.append(f'<path d="M2620 1800H3620M3260 1800V1980" stroke="#B5D4F4" stroke-width="2"/>')
    s.append(f'<text x="2650" y="1778" font-family="{MONO}" font-size="44" font-weight="bold" fill="#e8ecf2">EXABIBI TOWER · WIEN</text>')
    s.append(f'<text x="2650" y="1880" font-family="{MONO}" font-size="32" fill="#85B7EB">ANSICHT NORD</text>')
    s.append(f'<text x="2650" y="1940" font-family="{MONO}" font-size="32" fill="#85B7EB">BIBI TECH · BAUABTEILUNG</text>')
    s.append(f'<text x="3290" y="1880" font-family="{MONO}" font-size="32" fill="#85B7EB">REV 94</text>')
    s.append(f'<rect x="3530" y="1730" width="80" height="60" fill="#FFD400"/>')
    return _svg("".join(s), defs)


def tower_frosch(p):
    defs = _lin("bg", [(0, "#0a1a33", 1), (1, "#2a4470", 1)])
    defs += _lin("tw", [(0, "#378ADD", 1), (1, "#0f1a2e", 1)], 0, 0, 0, 1)
    defs += _glow("gl", 25)
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    s.append(f'<polygon points="900,{H} 1840,0 2000,0 2940,{H}" fill="url(#tw)"/>')
    for i in range(1, 40):
        t = (i / 40) ** 1.6
        y = H * (1 - t)
        xl = 900 + (1840 - 900) * t
        xr = 2940 - (2940 - 2000) * t
        s.append(f'<path d="M{xl:.0f} {y:.0f}H{xr:.0f}" stroke="#85B7EB" stroke-width="{2 + 6 * (1 - t):.1f}" opacity="0.5"/>')
    for j in range(-6, 7):
        s.append(f'<path d="M{1920 + j * 170} {H} L{1920 + j * 13} 0" stroke="#85B7EB" stroke-width="2" opacity="0.35"/>')
    s.append(f'<circle cx="1920" cy="30" r="50" fill="#FFD400" filter="url(#gl)"/><circle cx="1920" cy="30" r="18" fill="#FFD400"/>')
    s.append(f'<polygon points="0,{H} 700,{H} 0,600" fill="#0b1426"/><polygon points="{W},{H} {W - 700},{H} {W},600" fill="#0b1426"/>')
    return _svg("".join(s), defs)


def tower_nebel(p):
    rnd = random.Random(5)
    defs = _lin("bg", [(0, "#3d4e70", 1), (0.55, "#8b95a5", 1), (1, "#cfd6df", 1)])
    defs += _rad("sonne", [(0, "#F2A900", 0.95), (0.3, "#F2A900", 0.5), (1, "#F2A900", 0)], 0.68, 0.52, 0.35)
    defs += _glow("nb", 40)
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>', f'<rect width="{W}" height="{H}" fill="url(#sonne)"/>']
    s.append(_stadt(p, 1720, "#5d6b85", rnd, 300))
    s.append(_tower(1520, 1760, 1500, 260, "#2a3a5a", "#2a3a5a"))
    s.append(f'<circle cx="1520" cy="125" r="12" fill="#FFD400"/>')
    for i in range(7):
        y = 1300 + i * 120
        s.append(f'<rect x="-200" y="{y}" width="{W + 400}" height="160" fill="#e8ecf2" opacity="{0.18 + i * 0.05:.2f}" filter="url(#nb)"/>')
    s.append(f'<rect x="0" y="1880" width="{W}" height="280" fill="#7a8aa5"/>')
    s.append('<path d="M0 1930 Q960 1890 1920 1940 T3840 1920" fill="none" stroke="#cfd6df" stroke-width="5" opacity="0.7"/>')
    return _svg("".join(s), defs)


def tower_gewitter(p):
    rnd = random.Random(13)
    defs = _lin("bg", [(0, "#05070d", 1), (1, "#1b2236", 1)]) + _glow("gl", 30) + _glow("gl2", 90)
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for _ in range(30):
        x, y = rnd.uniform(0, W), rnd.uniform(0, 600)
        s.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{rnd.uniform(300, 700):.0f}" ry="{rnd.uniform(80, 180):.0f}" fill="#2a3245" opacity="0.6" filter="url(#gl)"/>')
    blitz = "M2400 0 L2240 300 L2330 320 L2120 640 L2210 660 L1960 1000 L1935 1050"
    s.append(f'<path d="{blitz}" fill="none" stroke="#bcd8ff" stroke-width="60" filter="url(#gl2)" opacity="0.8"/>')
    s.append(f'<path d="{blitz}" fill="none" stroke="#ffffff" stroke-width="10" stroke-linejoin="round"/>')
    s.append(_stadt(p, 1900, "#0a0e18", rnd, 360))
    s.append(_tower(1920, 1920, 900, 220, "#121a2c", "#5d7ab0", "#85B7EB", rnd, 0.8))
    s.append(f'<circle cx="1920" cy="938" r="40" fill="#FFD400" filter="url(#gl)"/>')
    s.append(f'<rect x="0" y="1900" width="{W}" height="260" fill="#05070d"/>')
    return _svg("".join(s), defs)


def tower_oben(p):
    """Blick von der Spitze auf Wien bei Nacht."""
    rnd = random.Random(17)
    defs = _rad("bg", [(0, "#16264a", 1), (1, "#03060d", 1)], 0.5, 0.65, 0.8) + _glow("gl", 6)
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for _ in range(26):
        x1, y1 = rnd.uniform(0, W), rnd.uniform(500, H)
        w = rnd.uniform(-1, 1)
        s.append(f'<path d="M{x1:.0f} {y1:.0f} l{3000 * math.cos(w):.0f} {900 * math.sin(w):.0f}" stroke="#F2A900" stroke-width="3" opacity="0.5" filter="url(#gl)"/>')
    for _ in range(2600):
        x, y = rnd.uniform(0, W), rnd.uniform(420, H)
        f = rnd.choice(["#ffd27a", "#e8ecf2", "#85B7EB", "#ffd27a"])
        s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(1.5, 4):.1f}" fill="{f}" opacity="{rnd.uniform(0.3, 1):.2f}"/>')
    s.append('<path d="M0 1500 C800 1300 1400 1700 2200 1450 S3400 1250 3840 1380" fill="none" stroke="#0b1426" stroke-width="140"/>')
    s.append('<path d="M0 1500 C800 1300 1400 1700 2200 1450 S3400 1250 3840 1380" fill="none" stroke="#1e3a5c" stroke-width="8"/>')
    defs += _lin("dunst", [(0, "#03060d", 1), (1, "#03060d", 0)])
    s.append(f'<rect width="{W}" height="600" fill="url(#dunst)"/>')
    s.append(f'<path d="M0 {H} L700 1820 H3140 L{W} {H} Z" fill="#0f1a2e"/>')
    s.append(f'<path d="M700 1820 H3140" stroke="#378ADD" stroke-width="6"/>')
    s.append(f'<text x="1920" y="2060" text-anchor="middle" font-family="{MONO}" font-size="40" fill="#378ADD">EXABIBI TOWER · 444 m · AUSSICHT</text>')
    return _svg("".join(s), defs)


def wafer(p):
    defs = _rad("bg", [(0, "#1a2130", 1), (1, "#07090d", 1)]) + _lin("glanz", [(0, "#85B7EB", 0.0), (0.5, "#c9b6ff", 0.35), (1, "#7ee0d0", 0.0)], 0, 0, 1, 1)
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    cx, cy, r = 1920, 1080, 980
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#2a3240"/>')
    s.append(f'<clipPath id="kreis"><circle cx="{cx}" cy="{cy}" r="{r - 20}"/></clipPath>')
    g = 96
    teile = []
    for x in range(cx - r, cx + r, g):
        for y in range(cy - r, cy + r, g):
            if math.hypot(x + g / 2 - cx, y + g / 2 - cy) < r - 60:
                farbe = "#FFD400" if (x // g, y // g) == ((cx + 2 * g) // g, (cy - 3 * g) // g) else "#3a4458"
                teile.append(f'<rect x="{x + 4}" y="{y + 4}" width="{g - 8}" height="{g - 8}" fill="{farbe}"/>')
    s.append(f'<g clip-path="url(#kreis)">{"".join(teile)}<rect x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" fill="url(#glanz)"/></g>')
    s.append(f'<path d="M{cx - 160} {cy + r - 6} H{cx + 160}" stroke="#07090d" stroke-width="30"/>')
    return _svg("".join(s), defs)


def chipfabrik(p):
    defs = _lin("bg", [(0, "#0f141c", 1), (1, "#05070a", 1)]) + _glow("gl", 14)
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for i in range(14):
        x = 140 + i * 270
        s.append(f'<rect x="{x}" y="380" width="200" height="1400" rx="16" fill="#1a2029" stroke="#313a48" stroke-width="4"/>')
        for k in range(10):
            y = 440 + k * 132
            an = (i * 7 + k * 3) % 11 == 0
            s.append(f'<rect x="{x + 30}" y="{y}" width="140" height="80" rx="8" fill="{"#378ADD" if an else "#232a35"}"/>')
            s.append(f'<circle cx="{x + 160}" cy="{y + 14}" r="7" fill="{"#FFD400" if an else "#3fbf6f"}" filter="url(#gl)"/>')
    s.append(f'<rect x="0" y="1850" width="{W}" height="18" fill="#378ADD"/>')
    s.append(f'<text x="160" y="300" font-family="{MONO}" font-size="56" fill="#8b95a5">EXA FERTIGUNG · REINRAUM 3</text>')
    return _svg("".join(s), defs)


# ================================================================ Bibi Budget Bank

def bank_guilloche(p):
    defs = _rad("bg", [(0, "#1c432f", 1), (1, "#0b1f15", 1)], 0.5, 0.5, 0.75)
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for k in range(40):
        pts = []
        for i in range(721):
            t = math.radians(i * 0.5)
            r = 600 + 120 * math.sin(7 * t + k * 0.12) + 60 * math.cos(13 * t - k * 0.2) + k * 9
            pts.append(f"{1920 + r * math.cos(t):.1f},{1080 + r * 0.82 * math.sin(t):.1f}")
        s.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#C9A227" stroke-width="2" opacity="{0.25 + 0.5 * (k % 5 == 0):.2f}"/>')
    s.append(f'<text x="1920" y="2040" text-anchor="middle" font-family="DejaVu Serif, serif" font-size="44" letter-spacing="12" fill="#C9A227" opacity="0.7">VERTEILT KEIN GELD · VERTEILT ZUGRIFF</text>')
    return _svg("".join(s), defs)


def bank_tresor(p):
    defs = _rad("bg", [(0, "#4a3424", 1), (1, "#1a120c", 1)], 0.5, 0.5, 0.8) + _rad("tuer", [(0, "#d8b440", 1), (1, "#7a5f12", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    cx, cy = 1920, 1080
    s.append(f'<circle cx="{cx}" cy="{cy}" r="860" fill="#0b1f15"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="800" fill="url(#tuer)" stroke="#5a4510" stroke-width="20"/>')
    for i in range(24):
        w = math.radians(i * 15)
        s.append(f'<circle cx="{cx + 730 * math.cos(w):.0f}" cy="{cy + 730 * math.sin(w):.0f}" r="22" fill="#5a4510"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="420" fill="none" stroke="#5a4510" stroke-width="16"/>')
    for i in range(3):
        w = math.radians(i * 120 + 30)
        s.append(f'<path d="M{cx} {cy} L{cx + 380 * math.cos(w):.0f} {cy + 380 * math.sin(w):.0f}" stroke="#163a29" stroke-width="60" stroke-linecap="round"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="110" fill="#163a29" stroke="#C9A227" stroke-width="12"/>')
    return _svg("".join(s), defs)


def bank_barren(p):
    defs = _lin("bg", [(0, "#143323", 1), (1, "#0b1f15", 1)]) + _lin("gold", [(0, "#f0d070", 1), (1, "#a8841a", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for reihe in range(5):
        n = 6 - reihe
        for i in range(n):
            x = 1920 - n * 210 + i * 420 + 40
            y = 1700 - reihe * 200
            s.append(f'<polygon points="{x},{y + 180} {x + 380},{y + 180} {x + 330},{y} {x + 50},{y}" fill="url(#gold)" stroke="#7a5f12" stroke-width="6"/>')
            s.append(f'<polygon points="{x + 70},{y + 20} {x + 310},{y + 20} {x + 300},{y + 60} {x + 80},{y + 60}" fill="#ffffff" fill-opacity="0.2"/>')
    s.append(f'<rect x="0" y="1880" width="{W}" height="280" fill="#4a3424"/>')
    return _svg("".join(s), defs)


def bank_kurse(p):
    rnd = random.Random(31)
    defs = _lin("bg", [(0, "#0b1f15", 1), (1, "#06120c", 1)]) + _lin("fl", [(0, "#C9A227", 0.35), (1, "#C9A227", 0)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for y in range(300, 1900, 200):
        s.append(f'<path d="M200 {y}H3640" stroke="#1c432f" stroke-width="3"/>')
    for linie, (farbe, bas) in enumerate([("#C9A227", 1300), ("#9a6a44", 1500), ("#5fbf8a", 1600)]):
        y = bas
        pts = []
        for i in range(0, 61):
            y += rnd.uniform(-60, 52) - (8 if linie == 0 else 0)
            pts.append((200 + i * 57.3, max(320, min(1880, y))))
        d = "M" + " L".join(f"{a:.0f} {b:.0f}" for a, b in pts)
        if linie == 0:
            s.append(f'<path d="{d} L3640 1900 L200 1900 Z" fill="url(#fl)"/>')
        s.append(f'<path d="{d}" fill="none" stroke="{farbe}" stroke-width="{8 if linie == 0 else 4}" stroke-linejoin="round"/>')
    s.append(f'<text x="200" y="220" font-family="{MONO}" font-size="56" fill="#C9A227">BBB · ZUGRIFFSINDEX</text>')
    return _svg("".join(s), defs)


def bank_schluessel(p):
    defs = _lin("bg", [(0, "#163a29", 1), (1, "#0b1f15", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    rnd = random.Random(41)
    for _ in range(46):
        x, y, k = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(0.6, 1.6)
        w = rnd.uniform(0, 360)
        farbe = "#C9A227" if rnd.random() < 0.3 else "#2c5a43"
        s.append(f'<g transform="translate({x:.0f} {y:.0f}) rotate({w:.0f}) scale({k:.2f})" fill="none" stroke="{farbe}" stroke-width="14" stroke-linecap="round">'
                 f'<circle cx="0" cy="0" r="48"/><path d="M48 0 H210 M160 0 v40 M195 0 v56"/></g>')
    return _svg("".join(s), defs)


# ================================================================ Bibi Delivery

def delivery_route(p):
    rnd = random.Random(51)
    defs = _lin("bg", [(0, "#0a1a3d", 1), (1, "#05102b", 1)]) + _glow("gl", 16)
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for x in range(0, W, 180):
        s.append(f'<path d="M{x + rnd.uniform(-20, 20):.0f} 0V{H}" stroke="#10255a" stroke-width="{rnd.choice([10, 18, 30])}"/>')
    for y in range(0, H, 160):
        s.append(f'<path d="M0 {y + rnd.uniform(-20, 20):.0f}H{W}" stroke="#10255a" stroke-width="{rnd.choice([10, 18, 30])}"/>')
    route = "M300 1900 L300 1500 L1020 1500 L1020 900 L1740 900 L1740 640 L2640 640 L2640 1140 L3300 1140"
    s.append(f'<path d="{route}" fill="none" stroke="#FFD000" stroke-width="40" filter="url(#gl)" opacity="0.6"/>')
    s.append(f'<path d="{route}" fill="none" stroke="#FFD000" stroke-width="18" stroke-dasharray="50 30" stroke-linejoin="round"/>')
    s.append(f'<path d="M3300 1140 c0 0 -150 -160 -150 -260 a150 150 0 0 1 300 0 c0 100 -150 260 -150 260 Z" fill="#FFD000"/>')
    s.append(f'<circle cx="3300" cy="880" r="60" fill="#0047FF"/>')
    s.append(f'<circle cx="300" cy="1900" r="40" fill="#1E6BFF" stroke="#ffffff" stroke-width="10"/>')
    for i, t in enumerate(["ANGENOMMEN", "GESUCHT", "GEFUNDEN", "UNTERWEGS"]):
        s.append(f'<text x="{220 + i * 480}" y="200" font-family="{SANS}" font-weight="bold" font-size="44" fill="{"#FFD000" if i == 3 else "#4a5a80"}">{t}</text>')
        s.append(f'<rect x="{220 + i * 480}" y="230" width="420" height="14" rx="7" fill="{"#FFD000" if i <= 3 else "#10255a"}"/>')
    return _svg("".join(s), defs)


def delivery_boxen(p):
    defs = _lin("bg", [(0, "#1E6BFF", 1), (1, "#0047FF", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    rnd = random.Random(55)

    def box(x, y, k):
        a = 160 * k
        return (f'<polygon points="{x},{y} {x + a},{y - a * 0.5} {x + 2 * a},{y} {x + a},{y + a * 0.5}" fill="#FFE04D"/>'
                f'<polygon points="{x},{y} {x + a},{y + a * 0.5} {x + a},{y + 1.6 * a} {x},{y + 1.1 * a}" fill="#FFD000"/>'
                f'<polygon points="{x + 2 * a},{y} {x + a},{y + a * 0.5} {x + a},{y + 1.6 * a} {x + 2 * a},{y + 1.1 * a}" fill="#d9b000"/>'
                f'<path d="M{x + a * 0.5},{y - a * 0.25} L{x + a * 1.5},{y + a * 0.25} V{y + 1.35 * a}" fill="none" stroke="#0a1a3d" stroke-width="{10 * k}" opacity="0.5"/>')
    for row in range(4):
        for col in range(6 - row):
            s.append(box(500 + col * 520 + row * 260, 1500 - row * 330, 1.0))
    for _ in range(14):
        y = rnd.uniform(200, 900)
        s.append(f'<path d="M{rnd.uniform(0, 600):.0f} {y:.0f}h{rnd.uniform(300, 900):.0f}" stroke="#ffffff" stroke-width="10" stroke-linecap="round" opacity="0.35"/>')
    return _svg("".join(s), defs)


def delivery_tempo(p):
    rnd = random.Random(57)
    defs = _lin("bg", [(0, "#05102b", 1), (1, "#0a1a3d", 1)], 0, 0, 1, 0)
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for _ in range(90):
        y = rnd.uniform(0, H)
        l = rnd.uniform(400, 2400)
        x = rnd.uniform(-400, W - l * 0.4)
        farbe = rnd.choice(["#FFD000", "#1E6BFF", "#0047FF", "#ffffff"])
        s.append(f'<path d="M{x:.0f} {y:.0f}h{l:.0f}" stroke="{farbe}" stroke-width="{rnd.uniform(4, 26):.0f}" stroke-linecap="round" opacity="{rnd.uniform(0.3, 1):.2f}"/>')
    s.append(f'<path d="M2500 1080 H3300 M3080 860 L3300 1080 L3080 1300" fill="none" stroke="#FFD000" stroke-width="90" stroke-linecap="round" stroke-linejoin="round"/>')
    return _svg("".join(s), defs)


def delivery_roller(p):
    defs = _lin("bg", [(0, "#FFD000", 1), (1, "#ffbf00", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    s.append(f'<rect x="0" y="1640" width="{W}" height="520" fill="#0a1a3d"/>')
    for i in range(12):
        s.append(f'<rect x="{i * 360}" y="1880" width="200" height="24" fill="#FFD000"/>')
    # Roller (flach, seitlich)
    x, y = 1500, 1640
    s.append(f'<circle cx="{x}" cy="{y - 110}" r="110" fill="#0a1a3d" stroke="#ffffff" stroke-width="20"/>')
    s.append(f'<circle cx="{x + 820}" cy="{y - 110}" r="110" fill="#0a1a3d" stroke="#ffffff" stroke-width="20"/>')
    s.append(f'<path d="M{x - 40} {y - 240} H{x + 600} L{x + 760} {y - 560} H{x + 860}" fill="none" stroke="#0047FF" stroke-width="70" stroke-linecap="round" stroke-linejoin="round"/>')
    s.append(f'<path d="M{x + 760} {y - 560} L{x + 820} {y - 110}" stroke="#0047FF" stroke-width="50" stroke-linecap="round"/>')
    s.append(f'<rect x="{x - 120}" y="{y - 760}" width="460" height="420" rx="30" fill="#0047FF"/>')
    s.append(f'<rect x="{x - 120}" y="{y - 760}" width="460" height="90" rx="30" fill="#1E6BFF"/>')
    s.append(f'<path d="M{x + 30} {y - 560} H{x + 190} M{x + 140} {y - 610} L{x + 190} {y - 560} L{x + 140} {y - 510}" fill="none" stroke="#FFD000" stroke-width="26" stroke-linecap="round" stroke-linejoin="round"/>')
    for i in range(5):
        s.append(f'<path d="M{x - 600 - i * 80} {y - 500 + i * 70}h{-400 + i * 40}" stroke="#0a1a3d" stroke-width="22" stroke-linecap="round" opacity="0.5"/>')
    return _svg("".join(s), defs)


# ================================================================ Bibi Mac

def mac_boegen(p):
    defs = _lin("bg", [(0, "#E63131", 1), (1, "#b81f1f", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for row in range(-1, 12):
        for col in range(-1, 16):
            x = col * 280 + (140 if row % 2 else 0)
            y = row * 200
            f = "#FFE27A" if (row * 3 + col) % 7 == 0 else "#ffffff"
            s.append(f'<path d="M{x} {y} q110 90 220 0" fill="none" stroke="{f}" stroke-width="22" stroke-linecap="round" opacity="{0.9 if f != "#ffffff" else 0.25}"/>')
    return _svg("".join(s), defs)


def mac_tresen(p):
    defs = _lin("bg", [(0, "#fff4dc", 1), (1, "#ffe9b8", 1)]) + _lin("tr", [(0, "#E63131", 1), (1, "#b81f1f", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for i in range(16):
        s.append(f'<rect x="{i * 240}" y="0" width="120" height="1250" fill="#FFE27A" opacity="0.35"/>')
    s.append(f'<rect x="0" y="1250" width="{W}" height="910" fill="url(#tr)"/>')
    s.append(f'<rect x="0" y="1250" width="{W}" height="60" fill="#FFC72C"/>')
    # Bestell-Glocke
    s.append(f'<ellipse cx="2600" cy="1250" rx="300" ry="40" fill="#7a1414"/>')
    s.append(f'<path d="M2360 1240 a240 240 0 0 1 480 0 Z" fill="#FFC72C"/>')
    s.append(f'<circle cx="2600" cy="980" r="34" fill="#FFC72C"/>')
    s.append(f'<path d="M2420 1180 a200 200 0 0 1 120 -150" fill="none" stroke="#fff4dc" stroke-width="26" stroke-linecap="round" opacity="0.7"/>')
    # Bon
    s.append(f'<path d="M900 300 H1400 V1150 L1350 1120 L1300 1150 L1250 1120 L1200 1150 L1150 1120 L1100 1150 L1050 1120 L1000 1150 L950 1120 L900 1150 Z" fill="#ffffff" stroke="#e0b8a8" stroke-width="6"/>')
    for i, t in enumerate(["BIBI MAC", "--------", "1x  BURGER", "1x  POMMES", "1x  GETRÄNK", "", "DANKE!"]):
        s.append(f'<text x="960" y="{420 + i * 100}" font-family="{MONO}" font-size="56" fill="#3a1010">{t}</text>')
    return _svg("".join(s), defs)


def mac_burger(p):
    defs = _lin("bg", [(0, "#FFD84D", 1), (1, "#FFC72C", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for row in range(5):
        for col in range(9):
            x = 240 + col * 440 + (220 if row % 2 else 0)
            y = 260 + row * 440
            k = 1.0
            s.append(f'<g transform="translate({x} {y}) scale({k})">'
                     f'<path d="M-130 -10 a130 100 0 0 1 260 0 Z" fill="#E63131"/>'
                     f'<rect x="-140" y="0" width="280" height="40" rx="20" fill="#7a1414"/>'
                     f'<rect x="-130" y="50" width="260" height="56" rx="28" fill="#E63131"/></g>')
    return _svg("".join(s), defs)


def mac_bons(p):
    rnd = random.Random(61)
    defs = _lin("bg", [(0, "#3a1313", 1), (1, "#2a0d0d", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for _ in range(26):
        x, y = rnd.uniform(-100, W), rnd.uniform(-200, H)
        w = rnd.uniform(-25, 25)
        teile = [f'<rect x="0" y="0" width="420" height="640" fill="#fff8ea"/>']
        for k in range(8):
            teile.append(f'<rect x="40" y="{60 + k * 66}" width="{rnd.uniform(140, 340):.0f}" height="20" rx="10" fill="{"#E63131" if k == 0 else "#e0b8a8"}"/>')
        s.append(f'<g transform="translate({x:.0f} {y:.0f}) rotate({w:.0f})" opacity="0.92">{"".join(teile)}</g>')
    return _svg("".join(s), defs)


# ================================================================ Nassmacher

def nass_rutschen(p):
    defs = _lin("bg", [(0, "#22D3E6", 1), (1, "#00A7B5", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    s.append(f'<circle cx="3200" cy="420" r="220" fill="#FFB020"/>')
    s.append('<path d="M500 0 V700 q0 600 700 900 L3840 2160" fill="none" stroke="#06323a" stroke-width="260" stroke-linecap="round" opacity="0.15"/>')
    s.append('<path d="M500 0 V700 q0 600 700 900 L3840 2160" fill="none" stroke="#ffffff" stroke-width="200" stroke-linecap="round"/>')
    s.append('<path d="M500 0 V700 q0 600 700 900 L3840 2160" fill="none" stroke="#22D3E6" stroke-width="120" stroke-linecap="round"/>')
    s.append('<path d="M1000 0 V560 q0 520 640 800 L3840 1900" fill="none" stroke="#06323a" stroke-width="260" stroke-linecap="round" opacity="0.15"/>')
    s.append('<path d="M1000 0 V560 q0 520 640 800 L3840 1900" fill="none" stroke="#FFB020" stroke-width="200" stroke-linecap="round"/>')
    s.append('<path d="M1000 0 V560 q0 520 640 800 L3840 1900" fill="none" stroke="#ffd27a" stroke-width="80" stroke-linecap="round" opacity="0.6"/>')
    s.append(f'<path d="M0 1960 q120 -50 240 0 t240 0 t240 0 t240 0 t240 0 t240 0 t240 0 t240 0 t240 0 t240 0 t240 0 t240 0 t240 0 t240 0 t240 0 t240 0 V{H} H0 Z" fill="#06323a" opacity="0.8"/>')
    return _svg("".join(s), defs)


def nass_hohe_see(p):
    defs = _lin("bg", [(0, "#e6fbfd", 1), (1, "#22D3E6", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    s.append(f'<circle cx="900" cy="500" r="230" fill="#FFB020"/>')
    for k, (farbe, y0, a) in enumerate([("#00A7B5", 1300, 240), ("#0a7f8c", 1500, 200), ("#06323a", 1700, 160)]):
        d = f"M0 {y0}"
        for i in range(0, 9):
            d += f" q240 {-a} 480 0"
        s.append(f'<path d="{d} V{H} H0 Z" fill="{farbe}"/>')
    s.append('<path d="M2200 1300 C2300 600 3200 500 3500 900 C3300 800 3000 850 2950 1050 C3100 950 3250 1000 3250 1120" fill="none" stroke="#ffffff" stroke-width="60" stroke-linecap="round"/>')
    s.append('<path d="M2200 1300 C2300 600 3200 500 3500 900 C3300 800 3000 850 2950 1050 L2950 1300 Z" fill="#00A7B5"/>')
    s.append(f'<text x="200" y="2060" font-family="{SANS}" font-weight="bold" font-size="64" fill="#e6fbfd" opacity="0.8">DIE HOHE SEE</text>')
    return _svg("".join(s), defs)


def nass_fliesen(p):
    rnd = random.Random(71)
    defs = _lin("bg", [(0, "#22D3E6", 1), (1, "#00A7B5", 1)]) + _glow("gl", 6)
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for x in range(0, W, 120):
        s.append(f'<path d="M{x} 0V{H}" stroke="#e6fbfd" stroke-width="6" opacity="0.4"/>')
    for y in range(0, H, 120):
        s.append(f'<path d="M0 {y}H{W}" stroke="#e6fbfd" stroke-width="6" opacity="0.4"/>')
    for _ in range(160):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        d = f"M{x:.0f} {y:.0f} q{rnd.uniform(-120, 120):.0f} {rnd.uniform(-80, 80):.0f} {rnd.uniform(80, 260):.0f} {rnd.uniform(-40, 40):.0f}"
        s.append(f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="{rnd.uniform(4, 12):.0f}" stroke-linecap="round" opacity="0.55" filter="url(#gl)"/>')
    s.append(f'<rect x="0" y="1560" width="{W}" height="140" fill="#06323a" opacity="0.5"/>')
    s.append(f'<text x="200" y="1660" font-family="{SANS}" font-weight="bold" font-size="80" fill="#FFB020">2,00 m</text>')
    return _svg("".join(s), defs)


def nass_reifen(p):
    rnd = random.Random(73)
    defs = _lin("bg", [(0, "#22D3E6", 1), (1, "#0a7f8c", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    plaetze = []
    while len(plaetze) < 11:
        x, y, r = rnd.uniform(250, W - 250), rnd.uniform(250, H - 250), rnd.uniform(130, 250)
        if all(math.hypot(x - a, y - b) > (r + c) * 1.35 for a, b, c in plaetze):
            plaetze.append((x, y, r))
    for x, y, r in plaetze:
        f1 = rnd.choice(["#FF6B6B", "#FFB020", "#ffffff", "#7b2cbf"])
        s.append(f'<ellipse cx="{x + 20:.0f}" cy="{y + 30:.0f}" rx="{r:.0f}" ry="{r * 0.92:.0f}" fill="#06323a" opacity="0.25"/>')
        s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}" fill="none" stroke="{f1}" stroke-width="{r * 0.55:.0f}"/>')
        for k in range(4):
            w = math.radians(k * 90 + 45)
            s.append(f'<path d="M{x + r * 0.72 * math.cos(w):.0f} {y + r * 0.72 * math.sin(w):.0f} L{x + r * 1.28 * math.cos(w):.0f} {y + r * 1.28 * math.sin(w):.0f}" stroke="#ffffff" stroke-width="{r * 0.25:.0f}" opacity="{0.0 if f1 == "#ffffff" else 0.95}"/>')
    return _svg("".join(s), defs)


def nass_donau(p):
    defs = _lin("bg", [(0, "#ff8a3d", 1), (0.5, "#ffb020", 1), (0.5, "#06323a", 1), (1, "#03242a", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    s.append(f'<circle cx="1920" cy="1080" r="380" fill="#FFE27A"/>')
    s.append(f'<rect x="0" y="1080" width="{W}" height="1080" fill="#06323a"/>')
    for i in range(18):
        y = 1110 + i * 50
        b = 760 - i * 30
        s.append(f'<rect x="{1920 - b / 2}" y="{y}" width="{b}" height="{12 + i}" rx="6" fill="#FFE27A" opacity="{0.8 - i * 0.04:.2f}"/>')
    s.append(f'<path d="M0 1080 L700 1000 L1100 1050 L1500 980 L1500 1080 Z" fill="#03242a"/>')
    s.append(f'<path d="M2400 1080 L2400 940 L2470 940 L2470 1080 M2600 1080 L2900 1010 L3840 1040 V1080 Z" fill="#03242a"/>')
    return _svg("".join(s), defs)


# ================================================================ Bibiplexx

def plexx_riesenwand(p):
    defs = _lin("bg", [(0, "#07070c", 1), (1, "#120d1f", 1)]) + _lin("wand", [(0, "#7B2CBF", 1), (0.5, "#FF4D9D", 1), (1, "#FF8A00", 1)], 0, 0, 1, 1) + _glow("gl", 80)
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    s.append(f'<rect x="420" y="160" width="3000" height="1100" fill="url(#wand)" filter="url(#gl)" opacity="0.5"/>')
    s.append(f'<rect x="420" y="160" width="3000" height="1100" rx="8" fill="url(#wand)"/>')
    for x in range(420, 3420, 24):
        s.append(f'<path d="M{x} 160V1260" stroke="#07070c" stroke-width="3" opacity="0.35"/>')
    for y in range(160, 1260, 24):
        s.append(f'<path d="M420 {y}H3420" stroke="#07070c" stroke-width="3" opacity="0.35"/>')
    for reihe in range(6):
        y = 1420 + reihe * 120
        n = 18 + reihe * 2
        b = 3200 + reihe * 120
        for i in range(n):
            x = 1920 - b / 2 + i * b / n
            farbe = "#FF8A00" if (reihe == 3 and i == n // 2) else "#1a1030"
            s.append(f'<rect x="{x + 8:.0f}" y="{y}" width="{b / n - 16:.0f}" height="90" rx="22" fill="{farbe}" stroke="#2f2050" stroke-width="4"/>')
    return _svg("".join(s), defs)


def plexx_reihe_sieben(p):
    defs = _lin("bg", [(0, "#120d1f", 1), (1, "#07070c", 1)]) + _glow("gl", 30)
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for reihe in range(10):
        t = reihe / 9
        y = 500 + t ** 1.4 * 1500
        hoehe = 60 + t * 220
        breite = 120 + t * 260
        n = int(W / breite) + 2
        for i in range(n):
            x = (i - 0.5) * breite + (breite / 2 if reihe % 2 else 0)
            licht = reihe == 6 and i == n // 2
            farbe = "#FF8A00" if licht else "#1a1030"
            if licht:
                s.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{breite * 0.86:.0f}" height="{hoehe:.0f}" rx="{hoehe * 0.3:.0f}" fill="#FF8A00" filter="url(#gl)"/>')
            s.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{breite * 0.86:.0f}" height="{hoehe:.0f}" rx="{hoehe * 0.3:.0f}" fill="{farbe}" stroke="#2f2050" stroke-width="5"/>')
        s.append(f'<text x="60" y="{y + hoehe * 0.65:.0f}" font-family="{MONO}" font-size="{30 + t * 40:.0f}" fill="{"#FF8A00" if reihe == 6 else "#2f2050"}">{reihe + 1}</text>')
    s.append(f'<text x="1920" y="300" text-anchor="middle" font-family="{SANS}" font-weight="bold" font-size="90" fill="#f2e9ff" letter-spacing="6">REIHE SIEBEN.</text>')
    return _svg("".join(s), defs)


def plexx_pixel(p):
    rnd = random.Random(81)
    defs = _glow("gl", 10)
    s = [f'<rect width="{W}" height="{H}" fill="#07070c"/>']
    g = 64
    for x in range(0, W, g):
        for y in range(0, H, g):
            t = (x / W + (H - y) / H) / 2
            w = math.sin(x / 300) * math.cos(y / 220)
            if w + rnd.uniform(-0.3, 0.3) > 0.15:
                farbe = "#FF4D9D" if t < 0.45 else ("#FF8A00" if t > 0.7 else "#7B2CBF")
                s.append(f'<rect x="{x + 8}" y="{y + 8}" width="{g - 16}" height="{g - 16}" rx="6" fill="{farbe}" opacity="{0.4 + 0.6 * max(0, w):.2f}"/>')
    return _svg("".join(s), defs)


def plexx_tickets(p):
    rnd = random.Random(83)
    defs = _lin("bg", [(0, "#1a1030", 1), (1, "#07070c", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for _ in range(34):
        x, y = rnd.uniform(-200, W), rnd.uniform(-200, H)
        w = rnd.uniform(-40, 40)
        f = rnd.choice(["#7B2CBF", "#FF4D9D", "#FF8A00"])
        reihe = rnd.choice([3, 5, 7, 7, 9, 12])
        s.append(f'<g transform="translate({x:.0f} {y:.0f}) rotate({w:.0f})">'
                 f'<path d="M0 0 H560 V100 a40 40 0 0 0 0 80 V280 H0 V180 a40 40 0 0 0 0 -80 Z" fill="{f}"/>'
                 f'<path d="M420 20 V260" stroke="#07070c" stroke-width="6" stroke-dasharray="14 12"/>'
                 f'<text x="40" y="110" font-family="{SANS}" font-weight="bold" font-size="54" fill="#07070c">BIBIPLEXX</text>'
                 f'<text x="40" y="200" font-family="{MONO}" font-size="44" fill="#07070c">REIHE {reihe}</text></g>')
    return _svg("".join(s), defs)


def plexx_saal(p):
    defs = _lin("bg", [(0, "#07070c", 1), (1, "#1a1030", 1)]) + _glow("gl", 14)
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for reihe in range(8):
        t = reihe / 7
        y = 120 + t ** 1.5 * 900
        n = 10 + reihe * 3
        for i in range(n):
            x = W / 2 + (i - n / 2 + 0.5) * (200 + t * 160)
            s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{6 + t * 14:.0f}" fill="#f2e9ff" filter="url(#gl)"/>')
            s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{3 + t * 6:.0f}" fill="#ffffff"/>')
    s.append(f'<rect x="0" y="1500" width="{W}" height="660" fill="#07070c"/>')
    s.append(f'<path d="M0 1500 H{W}" stroke="#FF4D9D" stroke-width="10"/>')
    s.append(f'<path d="M0 1530 H{W}" stroke="#FF8A00" stroke-width="4"/>')
    s.append(f'<text x="1920" y="1800" text-anchor="middle" font-family="{SANS}" font-weight="bold" font-size="70" fill="#a898c8" letter-spacing="10">KEIN PROJEKTOR. NUR WAND.</text>')
    return _svg("".join(s), defs)


# ================================================================ Liste

ALLGEMEIN = [
    ("schrauben-bauplan", "Schrauben-Bauplan", schrauben_bauplan),
    ("schichten", "Schichten", schichten),
    ("prompt", "Prompt", prompt),
    ("muttern", "Muttern", muttern),
    ("hoehenlinien", "Höhenlinien", hoehenlinien),
    ("waben", "Waben", waben),
    ("platine", "Platine", platine),
    ("horizont", "Horizont", horizont),
    ("diagonale", "Diagonale", diagonale),
    ("punkte", "Punkteraster", punkte),
    ("berge", "Berge", berge),
]
FIRMA = {
    "bibi-tech": [("tower-nacht", "Tower bei Nacht", tower_nacht), ("tower-bauplan", "Tower-Bauplan", tower_bauplan),
                  ("tower-frosch", "Tower von unten", tower_frosch), ("tower-nebel", "Tower im Donaunebel", tower_nebel),
                  ("tower-gewitter", "Tower im Gewitter", tower_gewitter), ("tower-oben", "Aussicht vom Tower", tower_oben),
                  ("wafer", "Silizium-Wafer", wafer), ("chipfabrik", "Chipfabrik", chipfabrik)],
    "bibi-budget-bank": [("bank-guilloche", "Guilloche", bank_guilloche), ("bank-tresor", "Tresor", bank_tresor),
                         ("bank-barren", "Goldbarren", bank_barren), ("bank-kurse", "Zugriffsindex", bank_kurse),
                         ("bank-schluessel", "Schlüssel", bank_schluessel)],
    "bibi-delivery": [("delivery-route", "Route", delivery_route), ("delivery-boxen", "Boxen", delivery_boxen),
                      ("delivery-tempo", "Tempo", delivery_tempo), ("delivery-roller", "Roller", delivery_roller)],
    "bibi-mac": [("mac-boegen", "Lächelbögen", mac_boegen), ("mac-tresen", "Tresen", mac_tresen),
                 ("mac-burger", "Burger-Muster", mac_burger), ("mac-bons", "Bons", mac_bons)],
    "nassmacher": [("nass-rutschen", "Rutsch und Flutsch", nass_rutschen), ("nass-hohe-see", "Die Hohe See", nass_hohe_see),
                   ("nass-fliesen", "Beckenboden", nass_fliesen), ("nass-reifen", "Schwimmreifen", nass_reifen),
                   ("nass-donau", "Donau-Abend", nass_donau)],
    "bibiplexx": [("plexx-riesenwand", "Riesenwand", plexx_riesenwand), ("plexx-reihe-sieben", "Reihe sieben", plexx_reihe_sieben),
                  ("plexx-pixel", "Pixelwand", plexx_pixel), ("plexx-tickets", "Tickets", plexx_tickets),
                  ("plexx-saal", "Saallichter", plexx_saal)],
}


# Animierte Hintergruende (Plasma-Modul de.biblix.lebendig, QML-Szenen in den Designfarben).
# (szene, name, gruppe, standbild) - das Standbild nehmen Sperrbildschirm und Vorschau.
LEBENDIG_PREFIX = "lebendig-"
LEBENDIG = [
    ("sternenflug", "Sternenflug", "allgemein", "punkte"),
    ("sternenhimmel", "Sternenhimmel", "allgemein", "punkte"),
    ("gluehwuermchen", "Glühwürmchen", "allgemein", "punkte"),
    ("schnee", "Schnee", "allgemein", "berge"),
    ("regen", "Regen", "allgemein", "diagonale"),
    ("bokeh", "Bokeh", "allgemein", "schichten"),
    ("farbnebel", "Farbnebel", "allgemein", "schichten"),
    ("wellen", "Wellen", "allgemein", "horizont"),
    ("tropfen", "Tropfen", "allgemein", "hoehenlinien"),
    ("muttern", "Schwebende Muttern", "allgemein", "muttern"),
    ("waben", "Leuchtwaben", "allgemein", "waben"),
    ("tunnel", "Muttern-Tunnel", "allgemein", "muttern"),
    ("platine", "Stromkreis", "allgemein", "platine"),
    ("equalizer", "Equalizer", "allgemein", "diagonale"),
    ("synthwave", "Synthwave", "allgemein", "horizont"),
    ("prompt", "Prompt mit Bibi-Sprüchen", "allgemein", "prompt"),
    ("bauplan", "Bauplan", "allgemein", "schrauben-bauplan"),
    ("tower", "Tower bei Nacht", "bibi-tech", "tower-nacht"),
    ("wafer", "Wafer unterm Laser", "bibi-tech", "wafer"),
    ("kurse", "Zugriffsindex", "bibi-budget-bank", "bank-kurse"),
    ("route", "Route", "bibi-delivery", "delivery-route"),
    ("boegen", "Lächelbögen", "bibi-mac", "mac-boegen"),
    ("donau", "Donau-Abend", "nassmacher", "nass-donau"),
    ("saal", "Saallichter", "bibiplexx", "plexx-saal"),
]


def lebendig(mid):
    """(szene, name, gruppe, standbild) fuer eine ID "lebendig-<szene>", sonst None."""
    if not str(mid).startswith(LEBENDIG_PREFIX):
        return None
    szene = mid[len(LEBENDIG_PREFIX):]
    return next((x for x in LEBENDIG if x[0] == szene), None)


STANDORT_GRUPPE = "standorte"
EIGEN_DATEI = "datei:"
EIGEN_ORDNER = "ordner:"
BILDENDUNGEN = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".svg")


def alle():
    """Liste aller Motive: (id, name, gruppe) — gruppe 'allgemein', 'standorte' oder Preset-ID."""
    liste = [(i, n, "allgemein") for i, n, _ in ALLGEMEIN]
    liste += [(i, n, STANDORT_GRUPPE) for i, n, _, _, _ in STANDORTE]
    for firma, motive in FIRMA.items():
        liste += [(i, n, firma) for i, n, _ in motive]
    return liste


def standort(mid):
    """(id, name, funktion, preset, beschreibung) fuer ein Standort-Motiv, sonst None."""
    return next((x for x in STANDORTE if x[0] == mid), None)


def eigen_pfad(mid):
    """Pfad eines eigenen Bildes oder Ordners ("datei:..." / "ordner:..."), sonst None."""
    for vorsilbe in (EIGEN_DATEI, EIGEN_ORDNER):
        if str(mid).startswith(vorsilbe):
            return Path(mid[len(vorsilbe):])
    return None


def ordner_bilder(ordner):
    try:
        return sorted(f for f in Path(ordner).iterdir() if f.suffix.lower() in BILDENDUNGEN and f.is_file())
    except OSError:
        return []


def eigenes_bild(mid):
    """Bilddatei fuer ein eigenes Motiv (bei Ordnern das erste Bild) oder None, wenn nichts da ist."""
    pfad = eigen_pfad(mid)
    if pfad is None:
        return None
    if str(mid).startswith(EIGEN_ORDNER):
        bilder = ordner_bilder(pfad)
        return bilder[0] if bilder else None
    return pfad if pfad.is_file() else None


def system_motiv(mid):
    """Motiv-ID, die der Systemhelfer (Bootmenue, Anmeldung) kennt: Standbild statt animiert,
    Biblix-Standard statt eigener Bilder."""
    leb = lebendig(mid)
    if leb:
        mid = leb[3]
    return mid if any(i == mid for i, _, _ in alle()) else ALLGEMEIN[0][0]


def _funktion(mid):
    leb = lebendig(mid)
    if leb:  # animiert: Standbild fuer Sperrbildschirm und Vorschau
        mid = leb[3]
    for i, _, f in ALLGEMEIN:
        if i == mid:
            return f, None
    st = standort(mid)
    if st:
        return st[2], STANDORT_GRUPPE
    for firma, motive in FIRMA.items():
        for i, _, f in motive:
            if i == mid:
                return f, firma
    return ALLGEMEIN[0][2], None


def svg(mid, p, eigene_farben=False):
    """SVG eines Motivs. Standorte haben feste Farben; Firmenmotive nehmen die Firmenfarben,
    ausser eigene_farben ist an (dann die aktuelle Palette)."""
    f, firma = _funktion(mid)
    if firma == STANDORT_GRUPPE:
        return f()
    if firma and not eigene_farben:
        p = kern_palette({"preset": firma, "modus": "dunkel", "eigene_farben": None}, "dunkel")
    return f(p)


def rendern(mid, p, ziel_dir: Path, breite=W, hoehe=H, eigene_farben=False):
    """Rendert ein Motiv als PNG und gibt den Pfad zurueck (mit Zwischenspeicher).
    Eigene Bilder werden nicht gerendert, sondern direkt zurueckgegeben."""
    if eigen_pfad(mid) is not None:
        bild = eigenes_bild(mid)
        if bild:
            return bild
        mid = ALLGEMEIN[0][0]
    inhalt = svg(mid, p, eigene_farben)
    kennung = hashlib.sha1(inhalt.encode()).hexdigest()[:10]
    ziel_dir.mkdir(parents=True, exist_ok=True)
    png = ziel_dir / f"{mid}-{kennung}-{breite}.png"
    if not png.exists():
        quelle = ziel_dir / f".{mid}-{kennung}.svg"
        quelle.write_text(inhalt, encoding="utf-8")
        subprocess.run(["rsvg-convert", "-w", str(breite), "-h", str(hoehe), "-o", str(png), str(quelle)], check=True)
        quelle.unlink()
    return png
