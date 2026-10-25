"""Bibi Mac: Menütafel über dem Tresen am Bibi Boulevard (Masterbrief 9.1, BBB 1)."""

from ._hilfen import W, H, MONO, SANS, svg, lin, rad, t, schein

ROT, ROT_D, ROT_H = "#d62a1e", "#9e160e", "#ef4a33"
GELB, GELB_D = "#ffc72c", "#e09a00"
CREME, CREME_D = "#fff4dc", "#f0ddb4"
DUNKEL = "#2a120a"
BRAUN = "#8a4b1c"


def bun(cx, y, b, h, farbe="#e8a043"):
    return f'<path d="M{cx - b / 2} {y + h} Q{cx - b / 2} {y} {cx} {y} Q{cx + b / 2} {y} {cx + b / 2} {y + h} Z" fill="{farbe}"/>'


def burger(cx, cy, s=1.0, doppelt=False, schnitzel=False):
    b = 130 * s
    o = []
    y = cy - 52 * s
    o.append(bun(cx, y, b, 40 * s))
    for k in range(5):
        o.append(f'<ellipse cx="{cx - 30 * s + k * 15 * s}" cy="{y + 14 * s + (k % 2) * 6 * s}" rx="3" ry="2" fill="{CREME}"/>')
    y += 40 * s
    o.append(f'<path d="M{cx - b / 2 - 6} {y} q{b / 8} {12 * s} {b / 4} 0 t{b / 4} 0 t{b / 4} 0 t{b / 4 + 12} 0" fill="none" stroke="#5aa832" stroke-width="{8 * s}" stroke-linecap="round"/>')
    y += 6 * s
    lagen = 2 if doppelt else 1
    for _ in range(lagen):
        if schnitzel:
            o.append(f'<rect x="{cx - b / 2 - 8}" y="{y}" width="{b + 16}" height="{20 * s}" rx="{9 * s}" fill="#d4892a" stroke="#a8601a" stroke-width="3"/>')
        else:
            o.append(f'<rect x="{cx - b / 2 + 2}" y="{y}" width="{b - 4}" height="{20 * s}" rx="{10 * s}" fill="#6b3416"/>')
            o.append(f'<path d="M{cx - b / 2 + 4} {y + 2}h{b - 8}l-8 {12 * s}l-10 -8l-12 10l-10-8z" fill="{GELB}"/>')
        y += 22 * s
    o.append(f'<rect x="{cx - b / 2}" y="{y}" width="{b}" height="{20 * s}" rx="{8 * s}" fill="#d98f3a"/>')
    return "".join(o)


def pommes(cx, cy, s=1.0):
    o = []
    for i in range(9):
        x = cx - 42 * s + i * 10.5 * s
        o.append(f'<rect x="{x}" y="{cy - 70 * s + (i % 3) * 8 * s}" width="{9 * s}" height="{70 * s}" rx="2" fill="{GELB}" stroke="{GELB_D}" stroke-width="1.5"/>')
    o.append(f'<path d="M{cx - 52 * s} {cy - 22 * s}L{cx + 52 * s} {cy - 22 * s}L{cx + 40 * s} {cy + 56 * s}L{cx - 40 * s} {cy + 56 * s}Z" fill="{ROT}"/>')
    o.append(f'<path d="M{cx - 30 * s} {cy + 10 * s} q{30 * s} {16 * s} {60 * s} 0" fill="none" stroke="{GELB}" stroke-width="{6 * s}" stroke-linecap="round"/>')
    return "".join(o)


def nuggets(cx, cy, s=1.0):
    o = [f'<path d="M{cx - 70 * s} {cy - 10 * s}h{140 * s}l-12 {62 * s}h-{116 * s}z" fill="{ROT}"/>']
    for dx, dy in ((-40, -26), (0, -36), (40, -24), (-20, -50), (22, -54)):
        o.append(f'<ellipse cx="{cx + dx * s}" cy="{cy + dy * s}" rx="{24 * s}" ry="{17 * s}" fill="#d9952f" stroke="#b06d1d" stroke-width="2"/>')
    o.append(f'<path d="M{cx - 70 * s} {cy - 10 * s}h{140 * s}" stroke="{GELB}" stroke-width="{6 * s}"/>')
    return "".join(o)


def teller(cx, cy, s=1.0):
    return (f'<ellipse cx="{cx}" cy="{cy + 10 * s}" rx="{82 * s}" ry="{34 * s}" fill="#fff" stroke="#d7c9a8" stroke-width="3"/>'
            f'<path d="M{cx - 60 * s} {cy + 6 * s} q{20 * s} -{30 * s} {60 * s} -{22 * s} q{40 * s} {4 * s} {50 * s} {22 * s} q-{50 * s} {22 * s} -{110 * s} 0z" '
            f'fill="#d4892a" stroke="#a8601a" stroke-width="3"/>'
            f'<path d="M{cx + 36 * s} {cy + 14 * s} a{16 * s} {16 * s} 0 0 1 {30 * s} 0z" fill="#f6e34a" stroke="#c9b51c" stroke-width="2"/>')


def becher(cx, cy, s=1.0, farbe=ROT, deckel="dome", strohhalm=True):
    o = []
    if strohhalm:
        o.append(f'<path d="M{cx + 8 * s} {cy - 70 * s}L{cx + 26 * s} {cy - 112 * s}" stroke="{GELB}" stroke-width="{9 * s}" stroke-linecap="round"/>')
    if deckel == "dome":
        o.append(f'<path d="M{cx - 38 * s} {cy - 66 * s} Q{cx} {cy - 100 * s} {cx + 38 * s} {cy - 66 * s}Z" fill="#f4f4f4" stroke="#cfcfcf" stroke-width="2"/>')
    o.append(f'<path d="M{cx - 40 * s} {cy - 66 * s}h{80 * s}l-10 {126 * s}h-{60 * s}z" fill="{farbe}"/>')
    o.append(f'<rect x="{cx - 44 * s}" y="{cy - 72 * s}" width="{88 * s}" height="{10 * s}" rx="4" fill="#f4f4f4"/>')
    o.append(f'<path d="M{cx - 24 * s} {cy} q{24 * s} {14 * s} {48 * s} 0" fill="none" stroke="{GELB}" stroke-width="{6 * s}" stroke-linecap="round"/>')
    return "".join(o)


def kaffee(cx, cy, s=1.0):
    o = []
    for k in (-18, 0, 18):
        o.append(f'<path d="M{cx + k * s} {cy - 54 * s} q{-12 * s} -{16 * s} 0 -{32 * s} q{12 * s} -{16 * s} 0 -{32 * s}" fill="none" stroke="#c8b8a0" stroke-width="{4 * s}" stroke-linecap="round"/>')
    o.append(f'<path d="M{cx - 46 * s} {cy - 44 * s}h{92 * s}l-8 {80 * s}q-{38 * s} {16 * s} -{76 * s} 0z" fill="{DUNKEL}"/>')
    o.append(f'<path d="M{cx + 44 * s} {cy - 26 * s} q{34 * s} {4 * s} {6 * s} {40 * s}" fill="none" stroke="{DUNKEL}" stroke-width="{9 * s}"/>')
    # Mondsichel: Nachtschicht
    o.append(f'<path d="M{cx - 8 * s} {cy - 22 * s} a{18 * s} {18 * s} 0 1 0 {14 * s} {30 * s} a{14 * s} {14 * s} 0 1 1 -{14 * s} -{30 * s}z" fill="{GELB}"/>')
    return "".join(o)


def box(cx, cy, s=1.0, alarm=False):
    o = [f'<rect x="{cx - 66 * s}" y="{cy - 40 * s}" width="{132 * s}" height="{92 * s}" rx="{8 * s}" fill="{ROT}"/>',
         f'<path d="M{cx - 66 * s} {cy - 40 * s}l{20 * s} -{26 * s}h{92 * s}l{20 * s} {26 * s}z" fill="{ROT_H}"/>',
         f'<path d="M{cx - 24 * s} {cy - 66 * s} q{24 * s} -{30 * s} {48 * s} 0" fill="none" stroke="{DUNKEL}" stroke-width="{7 * s}"/>']
    if alarm:
        for k in range(6):
            o.append(f'<path d="M{cx - 66 * s + k * 26 * s} {cy + 30 * s}l{14 * s} -{22 * s}h{12 * s}l-{14 * s} {22 * s}z" fill="{GELB}"/>')
        o.append(f'<rect x="{cx - 66 * s}" y="{cy + 8 * s}" width="{132 * s}" height="{22 * s}" fill="none" stroke="{DUNKEL}" stroke-width="3"/>')
    else:
        o.append(f'<path d="M{cx - 30 * s} {cy + 10 * s} q{30 * s} {18 * s} {60 * s} 0" fill="none" stroke="{GELB}" stroke-width="{7 * s}" stroke-linecap="round"/>')
    return "".join(o)


def tablett(cx, cy, s=1.0):
    return (f'<rect x="{cx - 110 * s}" y="{cy + 30 * s}" width="{220 * s}" height="{26 * s}" rx="{10 * s}" fill="{ROT_D}"/>'
            + burger(cx - 52 * s, cy + 18 * s, 0.6 * s) + pommes(cx + 18 * s, cy + 2 * s, 0.5 * s) + becher(cx + 78 * s, cy + 8 * s, 0.5 * s))


def fruehstueck(cx, cy, s=1.0):
    return (bun(cx, cy - 50 * s, 120 * s, 34 * s, "#e0b070")
            + f'<ellipse cx="{cx}" cy="{cy - 6 * s}" rx="{70 * s}" ry="{18 * s}" fill="#fff"/>'
            + f'<circle cx="{cx}" cy="{cy - 8 * s}" r="{15 * s}" fill="{GELB}"/>'
            + f'<rect x="{cx - 58 * s}" y="{cy + 10 * s}" width="{116 * s}" height="{22 * s}" rx="{9 * s}" fill="#e0b070"/>')


TAFELN = [
    ("BURGER", [("BIBI BURGER", lambda x, y: burger(x, y)),
                ("DOPPEL-BIBI", lambda x, y: burger(x, y, 0.9, doppelt=True)),
                ("SCHNITZEL-BIBI", lambda x, y: burger(x, y, schnitzel=True))]),
    ("DAZU", [("BIBI FRIES", lambda x, y: pommes(x, y)),
              ("NUGGETS", lambda x, y: nuggets(x, y)),
              ("SCHNITZELPLATTE", lambda x, y: teller(x, y))]),
    ("MENÜS", [("TRUPP-BIBI-MENÜ", lambda x, y: tablett(x, y, 0.75)),
               ("PENDLER-MENÜ", lambda x, y: box(x, y, 0.85)),
               ("ALARMBOX", lambda x, y: box(x, y, 0.85, alarm=True)),
               ("FRÜHSTÜCK", lambda x, y: fruehstueck(x, y, 0.85))]),
    ("GETRÄNKE", [("COLA", lambda x, y: becher(x, y)),
                  ("NACHTSCHICHT-KAFFEE", lambda x, y: kaffee(x, y)),
                  ("SHAKES", lambda x, y: becher(x, y, 1.0, CREME_D, strohhalm=True))]),
]


def mac_menuetafel(p=None):
    defs = lin("wand", [(0, "#3a170c", 1), (1, "#22100a", 1)])
    defs += lin("tafellicht", [(0, "#fffaf0", 1), (1, CREME, 1)])
    defs += lin("tresen", [(0, ROT, 1), (1, ROT_D, 1)])
    defs += lin("stahl", [(0, "#f4f4f4", 1), (1, "#b9bcc0", 1)])
    defs += rad("spot", [(0, "#fff1c4", 0.35), (1, "#fff1c4", 0)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#wand)"/>']

    # Fliesen hinter der Tafel
    for r in range(0, 34):
        for c in range(0, 40):
            x = c * 100 + (50 if r % 2 else 0) - 50
            s.append(f'<rect x="{x}" y="{r * 50}" width="96" height="46" rx="4" fill="#4a1d0f" fill-opacity="0.35"/>')

    # Spots
    for x in (560, 1440, 2400, 3280):
        s.append(schein(x, 80, 420, "spot"))
        s.append(f'<rect x="{x - 40}" y="0" width="80" height="34" rx="8" fill="#111"/>')

    # Kopfschild
    s.append(f'<rect x="160" y="60" width="{W - 320}" height="120" rx="20" fill="{ROT}"/>')
    s.append(f'<path d="M160 160H{W - 160}" stroke="{ROT_D}" stroke-width="20"/>')
    s.append(t(W / 2, 148, "BIBI MAC · BIBI BOULEVARD", 76, GELB, "middle", True, SANS, 10))
    for x in (420, W - 420):
        s.append(f'<path d="M{x - 70} 100 q70 60 140 0" fill="none" stroke="{GELB}" stroke-width="14" stroke-linecap="round"/>')

    # Tafeln
    n = len(TAFELN)
    gap = 40
    tw = (W - 320 - (n - 1) * gap) / n
    ty, th = 220, 1120
    for i, (titel, eintraege) in enumerate(TAFELN):
        x = 160 + i * (tw + gap)
        s.append(f'<rect x="{x - 10}" y="{ty - 10}" width="{tw + 20}" height="{th + 20}" rx="22" fill="#111"/>')
        s.append(f'<rect x="{x}" y="{ty}" width="{tw}" height="{th}" rx="16" fill="url(#tafellicht)"/>')
        s.append(f'<rect x="{x}" y="{ty}" width="{tw}" height="110" rx="16" fill="{ROT}"/><rect x="{x}" y="{ty + 70}" width="{tw}" height="40" fill="{ROT}"/>')
        s.append(t(x + tw / 2, ty + 78, titel, 58, GELB, "middle", True, SANS, 8))
        zeile = (th - 140) / len(eintraege)
        for k, (name, zeichnen) in enumerate(eintraege):
            yy = ty + 130 + k * zeile
            ix, iy = x + 150, yy + zeile / 2 + 14
            s.append(f'<g transform="translate({ix:.0f} {iy:.0f}) scale(1.45) translate({-ix:.0f} {-iy:.0f})">{zeichnen(ix, iy)}</g>')
            s.append(t(x + 310, yy + zeile / 2 + 20, name, 46 if len(name) < 16 else 36, DUNKEL, fett=True, schrift=SANS, abstand=1))
            if k < len(eintraege) - 1:
                s.append(f'<path d="M{x + 40} {yy + zeile}H{x + tw - 40}" stroke="{CREME_D}" stroke-width="3" stroke-dasharray="4 10" stroke-linecap="round"/>')

    # Hinweisband unter den Tafeln: BBB-Grundsatz
    s.append(f'<rect x="160" y="1374" width="{W - 320}" height="70" rx="12" fill="{GELB}"/>')
    s.append(t(W / 2, 1422, "GRUNDBEDARF KOSTET NICHTS.  ·  KEIN BIBI OPERIERT HUNGRIG.  ·  POMMES SIND LOGISTIK.", 36,
               DUNKEL, "middle", True, SANS, 4))

    # Abholanzeige
    s.append(f'<rect x="160" y="1474" width="900" height="120" rx="14" fill="#0b0b0b" stroke="#333" stroke-width="4"/>')
    s.append(t(200, 1524, "IN ZUBEREITUNG", 26, "#9a9a9a", abstand=4))
    s.append(t(200, 1574, "117   118   121   124", 44, GELB, fett=True, abstand=6))
    s.append(f'<rect x="{W - 1060}" y="1474" width="900" height="120" rx="14" fill="#0b0b0b" stroke="#333" stroke-width="4"/>')
    s.append(t(W - 1020, 1524, "ABHOLBEREIT", 26, "#9a9a9a", abstand=4))
    s.append(t(W - 1020, 1574, "112   115", 44, "#6fe36f", fett=True, abstand=6))

    # Tresen
    s.append(f'<rect x="0" y="1660" width="{W}" height="40" fill="url(#stahl)"/>')
    s.append(f'<rect x="0" y="1700" width="{W}" height="{H - 1700}" fill="url(#tresen)"/>')
    s.append(f'<rect x="0" y="1760" width="{W}" height="24" fill="{GELB}"/>')
    s.append(t(W / 2, 1900, "EINSATZBEREIT. ESSENSBEREIT.", 92, GELB, "middle", True, SANS, 14))
    s.append(t(W / 2, 1980, "BOULEVARD · W12 · BZB · NASSMACHER · BIBI MAC AIR · SCHALLZUG · BIBIPLEXX · GROSSER SCHWIMMER · ZEUGHAUSBERG",
               26, CREME, "middle", False, SANS, 4))
    # Auf dem Tresen: zwei Tabletts, Klingel, Bon
    s.append(tablett(1460, 1600, 1.2))
    s.append(tablett(2380, 1600, 1.2))
    s.append(f'<ellipse cx="1920" cy="1660" rx="70" ry="12" fill="#888"/><path d="M1860 1658 a60 56 0 0 1 120 0z" fill="url(#stahl)"/>'
             f'<circle cx="1920" cy="1598" r="10" fill="#bbb"/>')
    s.append(f'<path d="M2880 1600h120v52l-12 8-12-8-12 8-12-8-12 8-12-8-12 8-12-8-12 8-12-8z" fill="#fffdf6" stroke="#ddd" stroke-width="2"/>')
    for k in range(4):
        s.append(f'<path d="M2896 {1616 + k * 10}h{88 - (k % 2) * 30}" stroke="#999" stroke-width="3"/>')
    return svg("".join(s), defs)
