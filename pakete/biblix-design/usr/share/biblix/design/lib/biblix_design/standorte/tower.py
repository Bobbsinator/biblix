"""Bibi Tech: Exabibi Tower als Schnittzeichnung (Bauplan), 94 OG bis Bibi Tief (Masterbrief 8.2/8.3).

Zeichnungs-Vermerke (Schnitt A-A, nicht massstaeblich) sind reines Design.
"""
import math
import random

from ._hilfen import W, H, MONO, svg as _svg, lin as _lin

LINIE = "#B5D4F4"
LEISE = "#85B7EB"
RASTER = "#1e3a5c"
GELB = "#FFD400"
WEISS = "#e8ecf2"
ROT = "#e24b4a"

# Zonen laut Masterbrief 8.2 (von, bis, Nutzung)
ZONEN = [
    (90, 94, "EXECUTIVE"),
    (75, 89, "LABS · BIBILITH · MASCHINEN"),
    (60, 74, "FOUNDRY · SILICON"),
    (45, 59, "OS · ASSIST · ELEKTRONIK"),
    (30, 44, "DEVICES · DISPLAYS · KAMERA · AKKU"),
    (20, 29, "GAMING · BIG BIBI PRODUKTION"),
    (13, 19, "CORPORATE · EVENTS"),
    (5, 12, "KEYNOTE"),
    (1, 4, "EXPERIENCE · SHOP · MUSEUM"),
]
UNTEN = [
    (-1, -2, "LOGISTIK"),
    (-3, -3, "EXA CENTRAL"),
    (-4, -5, "REFINERY"),
    (-6, -8, "MINING · BIBI TIEF"),
]


def t(x, y, text, groesse=28, farbe=LEISE, anker="start", fett=False, abstand=2, extra=""):
    f = ' font-weight="bold"' if fett else ""
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-family="{MONO}" font-size="{groesse}" fill="{farbe}" '
            f'text-anchor="{anker}" letter-spacing="{abstand}"{f} {extra}>{text}</text>')


def tower_schnitt(p=None):
    rnd = random.Random(94)
    defs = _lin("bg", [(0, "#0b2340", 1), (1, "#061a33", 1)])
    defs += _lin("erde", [(0, "#08203b", 1), (1, "#04111f", 1)])
    defs += '<radialGradient id="schein"><stop offset="0" stop-color="#FFD400" stop-opacity="0.45"/>' \
            '<stop offset="1" stop-color="#FFD400" stop-opacity="0"/></radialGradient>'
    defs += ('<pattern id="schraffur" width="22" height="22" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
             f'<path d="M0 0V22" stroke="{RASTER}" stroke-width="3"/></pattern>')
    defs += ('<pattern id="ader" width="18" height="18" patternUnits="userSpaceOnUse" patternTransform="rotate(-35)">'
             f'<path d="M0 0V18" stroke="{GELB}" stroke-width="2" stroke-opacity="0.45"/></pattern>')
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']

    boden = 1440                      # Gelaendelinie
    oben = 200                        # Dach OG 94
    og = (boden - oben) / 94          # px je Geschoss
    ug = 56                           # Untergeschosse, nicht massstaeblich
    tx, tb = 1330, 300                # Turm-Mitte, Breite
    li, re = tx - tb / 2, tx + tb / 2

    def y_og(n):
        return boden - n * og

    def y_ug(n):                      # n = 1 .. 8 (positiv)
        return boden + n * ug

    # Raster ueber dem Gelaende, darunter Erdreich
    for x in range(0, W, 60):
        s.append(f'<path d="M{x} 0V{boden}" stroke="{RASTER}" stroke-width="{2 if x % 300 == 0 else 1}"/>')
    for y in range(0, boden, 60):
        s.append(f'<path d="M0 {y}H{W}" stroke="{RASTER}" stroke-width="{2 if y % 300 == 0 else 1}"/>')
    s.append(f'<rect x="0" y="{boden}" width="{W}" height="{H - boden}" fill="url(#erde)"/>')
    s.append(f'<rect x="0" y="{boden}" width="{W}" height="{H - boden}" fill="url(#schraffur)" opacity="0.55"/>')

    # Stadt-Silhouette (nur Kontur, fuer den Massstab)
    x = 760
    pfad = [f"M760 {boden}"]
    while x < W:
        b = rnd.uniform(60, 180)
        h = rnd.uniform(40, 150)
        if (li - 60 < x + b and x < re + 1000) or (2860 < x + b and x < 3800):
            x = re + 1000 if x < re + 1000 else 3800
            pfad.append(f"L{x:.0f} {boden}")
            continue
        pfad.append(f"L{x:.0f} {boden - h:.0f}L{x + b:.0f} {boden - h:.0f}L{x + b:.0f} {boden}")
        x += b + rnd.uniform(0, 24)
    s.append(f'<path d="{"".join(pfad)}" fill="none" stroke="{LEISE}" stroke-width="2" stroke-opacity="0.35"/>')

    # Zonen-Baender im Turm
    for i, (von, bis, _name) in enumerate(ZONEN):
        y1, y2 = y_og(bis), y_og(von - 1)
        s.append(f'<rect x="{li}" y="{y1:.1f}" width="{tb}" height="{y2 - y1:.1f}" fill="#378ADD" '
                 f'fill-opacity="{0.05 if i % 2 else 0.12}"/>')
    s.append(f'<rect x="{li}" y="{y_og(0) - og * 0.0:.1f}" width="0" height="0"/>')

    # Geschossdecken
    for n in range(0, 95):
        y = y_og(n)
        s.append(f'<path d="M{li} {y:.1f}h{tb}" stroke="{LEISE}" stroke-width="{2.4 if n % 10 == 0 else 1}" '
                 f'stroke-opacity="{0.9 if n % 10 == 0 else 0.4}"/>')
        if n % 10 == 0 and n:
            s.append(t(li - 26, y + 10, f"OG {n}", 28, LEISE, "end"))
    s.append(t(li - 26, boden - 14, "EG", 28, LEISE, "end"))

    # Turm-Kontur mit Dachschraege und Mast
    dach = oben - og * 3
    s.append(f'<path d="M{li} {boden} V{oben} L{tx - tb * 0.18} {dach} H{tx + tb * 0.18} L{re} {oben} V{boden}" '
             f'fill="none" stroke="{LINIE}" stroke-width="5" stroke-linejoin="round"/>')
    mast = dach - 120
    s.append(f'<path d="M{tx} {dach} V{mast}" stroke="{LINIE}" stroke-width="6"/>')
    # Flugwarnlicht: weicher runder Schein, zwei feine Ringe wie in der Zeichnung
    s.append(f'<circle cx="{tx}" cy="{mast}" r="60" fill="url(#schein)"/>')
    s.append(f'<circle cx="{tx}" cy="{mast}" r="24" fill="none" stroke="{GELB}" stroke-width="2" stroke-opacity="0.6"/>')
    s.append(f'<circle cx="{tx}" cy="{mast}" r="38" fill="none" stroke="{GELB}" stroke-width="1.5" stroke-opacity="0.3" stroke-dasharray="6 6"/>')
    s.append(f'<circle cx="{tx}" cy="{mast}" r="10" fill="{GELB}"/>')

    # Gelbe B-Lichtlinie an der Fassade
    s.append(f'<path d="M{re - 22} {boden - 8} V{oben + 6}" stroke="{GELB}" stroke-width="16" opacity="0.15"/>')
    s.append(f'<path d="M{re - 22} {boden - 8} V{oben + 6}" stroke="{GELB}" stroke-width="4"/>')

    # Exabibis Aufzug: Schacht EG..94, Halt in jedem 10. OG, 93 uebersprungen
    ax = tx - 70
    s.append(f'<rect x="{ax - 14}" y="{y_og(94):.1f}" width="28" height="{boden - y_og(94):.1f}" fill="#061a33" '
             f'stroke="{LINIE}" stroke-width="2"/>')
    s.append(f'<rect x="{ax - 10}" y="{y_og(94) + 2:.1f}" width="20" height="{og - 4:.1f}" fill="{GELB}"/>')
    hx = 420

    # Detail A: Schachtkopf vergroessert (OG 92 bis 94), 93 ohne Halt
    my = y_og(93)
    s.append(f'<circle cx="{ax}" cy="{my:.1f}" r="42" fill="none" stroke="{WEISS}" stroke-width="2" stroke-dasharray="8 6"/>')
    s.append(t(ax - 52, my - 34, "A", 26, WEISS, "end", fett=True))
    dcx, dcy, dr = 640, 420, 190
    knick = 880
    wv = math.atan2(my - dcy, knick - dcx)
    s.append(f'<path d="M{ax - 42} {my:.1f}H{knick}L{dcx + dr * math.cos(wv):.0f} {dcy + dr * math.sin(wv):.0f}" fill="none" '
             f'stroke="{WEISS}" stroke-width="2" stroke-opacity="0.6"/>')
    defs_detail = f'<clipPath id="detail"><circle cx="{dcx}" cy="{dcy}" r="{dr}"/></clipPath>'
    d = [f'<circle cx="{dcx}" cy="{dcy}" r="{dr}" fill="#081d36"/>']
    gh = 92
    top = dcy - 1.5 * gh
    for i in range(4):
        d.append(f'<path d="M{dcx - dr} {top + i * gh:.0f}H{dcx + dr}" stroke="{LEISE}" stroke-width="3"/>')
    d.append(f'<path d="M{dcx - 46} {top - 40}V{top + 3 * gh + 40}M{dcx + 46} {top - 40}V{top + 3 * gh + 40}" stroke="{LINIE}" stroke-width="4"/>')
    d.append(f'<rect x="{dcx - 46}" y="{top - 40}" width="92" height="{3 * gh + 80}" fill="#061a33" fill-opacity="0.9"/>')
    d.append(f'<path d="M{dcx - 46} {top - 40}V{top + 3 * gh + 40}M{dcx + 46} {top - 40}V{top + 3 * gh + 40}" stroke="{LINIE}" stroke-width="4"/>')
    # Kabine in 94
    d.append(f'<rect x="{dcx - 34}" y="{top + 10}" width="68" height="{gh - 20}" rx="4" fill="{GELB}"/>')
    d.append(f'<path d="M{dcx} {top + 16}V{top + gh - 16}" stroke="#0b2340" stroke-width="3"/>')
    d.append(f'<path d="M{dcx} {top - 40}V{top + 10}" stroke="{LINIE}" stroke-width="2"/>')
    # 93: Tueroeffnung zugemauert, rotes Kreuz
    y93 = top + gh
    d.append(f'<path d="M{dcx - 30} {y93 + 18}l60 56M{dcx + 30} {y93 + 18}l-60 56" stroke="{ROT}" stroke-width="7" stroke-linecap="round"/>')
    for i, (n, name, farbe) in enumerate([("94", "EXABIBI", GELB), ("93", "SALDO", ROT), ("92", "", LEISE)]):
        yy = top + i * gh + gh / 2 + 10
        d.append(t(dcx - 70, yy, n, 28, farbe if i < 2 else LEISE, "end", fett=i < 2))
        if name:
            d.append(t(dcx + 58, yy, name, 20, farbe, abstand=1))
    s.append(f'<g clip-path="url(#detail)">{"".join(d)}</g>')
    s.append(f'<circle cx="{dcx}" cy="{dcy}" r="{dr}" fill="none" stroke="{WEISS}" stroke-width="3"/>')
    s.append(t(dcx, dcy + dr + 52, "DETAIL A · AUFZUG EXABIBI", 28, WEISS, "middle", fett=True))
    s.append(t(dcx, dcy + dr + 92, "HÄLT NICHT IN 93", 26, ROT, "middle"))

    # Urspruengliche Planung: ca. 25 OG
    y25 = y_og(25)
    s.append(f'<path d="M{hx} {y25:.1f}H{re + 30}" stroke="{WEISS}" stroke-width="2" stroke-dasharray="14 10" stroke-opacity="0.7"/>')
    s.append(t(hx, y25 - 50, "URSPRÜNGLICHE PLANUNG", 26, WEISS, fett=True))
    s.append(t(hx, y25 - 14, "ARCHITEKT: CA. 25 OG", 26, LEISE))

    # Zonen-Beschriftung rechts mit Klammer
    kx = re + 50
    for von, bis, name in ZONEN:
        y1, y2 = y_og(bis) + 3, y_og(von - 1) - 3
        mitte = (y1 + y2) / 2
        s.append(f'<path d="M{kx} {y1:.1f}h14V{y2:.1f}h-14M{kx + 14} {mitte:.1f}h26" fill="none" stroke="{LEISE}" '
                 f'stroke-width="2" stroke-opacity="0.8"/>')
        nummer = f"{von}–{bis}" if von != bis else f"{von}"
        if y2 - y1 > 60:
            s.append(t(kx + 54, mitte - 6, f"OG {nummer}", 26, GELB))
            s.append(t(kx + 54, mitte + 28, name, 24, LINIE, abstand=3))
        else:
            s.append(t(kx + 54, mitte + 9, f"OG {nummer}", 24, GELB) + t(kx + 220, mitte + 9, name, 22, LINIE, abstand=3))

    # Hoehenkote 444 m
    dx = 2560
    s.append(f'<path d="M{dx} {mast} V{boden} M{dx - 26} {mast}h52 M{dx - 26} {boden}h52" stroke="{GELB}" stroke-width="4"/>')
    s.append(f'<path d="M{tx + 30} {mast}H{dx - 30}" stroke="{GELB}" stroke-width="1.5" stroke-dasharray="6 8" stroke-opacity="0.6"/>')
    s.append(t(dx + 40, (mast + boden) / 2 - 10, "444 m", 72, GELB, abstand=4))
    s.append(t(dx + 44, (mast + boden) / 2 + 46, "94 OBERIRDISCHE GESCHOSSE", 30, LEISE))

    # ---------------------------------------------------------------- unter der Erde
    s.append(f'<path d="M0 {boden}H{W}" stroke="{LINIE}" stroke-width="5"/>')
    s.append(t(60, boden - 18, "± 0,00 GELÄNDE", 26, LINIE))

    breite = {1: 900, 2: 900, 3: 0, 4: 700, 5: 700, 6: 360, 7: 300, 8: 240}
    # -1/-2 Logistik, -4/-5 Refinery, -6..-8 Mining (schmaler werdend)
    for n in (1, 2, 4, 5, 6, 7, 8):
        b = breite[n]
        y = y_ug(n - 1)
        s.append(f'<rect x="{tx - b / 2}" y="{y:.0f}" width="{b}" height="{ug}" fill="#0b2340" stroke="{LINIE}" stroke-width="3"/>')
        s.append(t(tx - b / 2 + 16, y + ug / 2 + 9, f"-{n}", 24, LEISE))

    # -3 EXA CENTRAL: Bahnroehre ueber die ganze Breite
    y3 = y_ug(2)
    s.append(f'<rect x="-10" y="{y3:.0f}" width="{W + 20}" height="{ug}" fill="#0b2340" stroke="{LINIE}" stroke-width="3"/>')
    s.append(f'<path d="M0 {y3 + ug - 10:.0f}H{W}" stroke="{LEISE}" stroke-width="2" stroke-dasharray="30 14"/>')
    zug_x = 2050
    for k in range(4):
        wx = zug_x + k * 230
        s.append(f'<rect x="{wx}" y="{y3 + 12:.0f}" width="214" height="{ug - 26}" rx="10" fill="#0e2a4c" stroke="{LINIE}" stroke-width="2"/>')
        for f in range(5):
            s.append(f'<rect x="{wx + 18 + f * 38}" y="{y3 + 20:.0f}" width="24" height="12" fill="{LEISE}" fill-opacity="0.8"/>')
    s.append(f'<path d="M{zug_x + 4 * 230 - 16} {y3 + 12:.0f}q60 0 70 {ug - 26}h-70z" fill="#0e2a4c" stroke="{LINIE}" stroke-width="2"/>')
    s.append(t(tx - 440, y3 + ug / 2 + 11, "-3  EXA CENTRAL", 30, GELB, fett=True, abstand=4))

    # EXA-Lift-Schacht -3 bis -8
    lx = tx + 60
    s.append(f'<rect x="{lx - 12}" y="{y_ug(3):.0f}" width="24" height="{ug * 5}" fill="#061a33" stroke="{GELB}" stroke-width="2" stroke-opacity="0.8"/>')

    # Unterbeschriftung rechts der Untergeschosse
    ux = tx + 520
    for von, bis, name in UNTEN:
        if von == -3:
            continue
        y1, y2 = y_ug(-von - 1), y_ug(-bis)
        mitte = (y1 + y2) / 2
        s.append(f'<path d="M{ux - 40} {mitte:.0f}H{ux - 8}" stroke="{LEISE}" stroke-width="2"/>')
        nummer = f"{von} / {bis}" if von - bis == 1 else f"{von} … {bis}"
        s.append(t(ux, mitte + 9, f"{nummer}  {name}", 26, LINIE, abstand=3))
    s.append(t(tx + 140, y_ug(8) - 18, "EXA-LIFT", 22, GELB))

    # EXA-Ader
    ya = y_ug(8) + 26
    s.append(f'<path d="M0 {ya + 40} C900 {ya - 10} 1800 {ya + 70} 2700 {ya + 20} S3600 {ya + 50} {W} {ya + 30} '
             f'V{ya + 150} C3000 {ya + 120} 2000 {ya + 170} 1100 {ya + 130} S300 {ya + 140} 0 {ya + 150}Z" '
             f'fill="url(#ader)" stroke="{GELB}" stroke-width="2" stroke-opacity="0.5"/>')
    s.append(t(2900, ya - 12, "EXA-ADER · 99,9998 % VERBLEIBEND", 26, GELB, abstand=3))

    s.append(t(60, y_ug(8) + 6, "UNTERGESCHOSSE NICHT MASSSTÄBLICH", 22, LEISE, abstand=3))

    # ---------------------------------------------------------------- Schriftfeld
    sx, sy, sw, sh = 2900, 1080, 860, 330
    s.append(f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="#0b2340" stroke="{LINIE}" stroke-width="4"/>')
    s.append(f'<path d="M{sx} {sy + 80}H{sx + sw}M{sx} {sy + 250}H{sx + sw}M{sx + 600} {sy + 250}V{sy + sh}" stroke="{LINIE}" stroke-width="2"/>')
    s.append(t(sx + 28, sy + 54, "EXABIBI TOWER · WIEN", 40, WEISS, fett=True))
    s.append(f'<rect x="{sx + sw - 90}" y="{sy + 14}" width="70" height="52" fill="{GELB}"/>')
    s.append(t(sx + 28, sy + 130, "SCHNITT A–A · 94 OG BIS BIBI TIEF", 26, LEISE))
    s.append(t(sx + 28, sy + 172, "GENEHMIGT ALS: BÜROGEBÄUDE MIT", 24, LEISE))
    s.append(t(sx + 28, sy + 208, "GERINGFÜGIG ERHÖHTEM PLATZBEDARF", 24, LEISE))
    s.append(t(sx + 28, sy + 298, "BIBI TECH · BAUABTEILUNG", 26, LINIE))
    s.append(t(sx + 628, sy + 298, "REV 94", 26, LINIE))

    return _svg("".join(s), defs + defs_detail)
