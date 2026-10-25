"""Burgenland: Ebenenplan des künstlichen Bergs BB-BGLD (Masterbrief 6.1, 6.3).

Bewusst nicht eingezeichnet: alles, was laut Kanon auf keinem Plan steht.
"""
import random

from ._hilfen import W, H, MONO, SANS, svg, lin, t

HIMMEL, HIMMEL2 = "#101216", "#1c1f25"
BERG, BERG_H, BERG_R = "#2b2e33", "#363a41", "#5a5f68"
FELS = "#15171b"
DECKE, DECKE_R = "#23262c", "#6b7078"
TEXT, LEISE = "#d4d7dc", "#8a9099"
GELB, GOLD, WEISS = "#F2C12E", "#D4AF37", "#ffffff"
REBE = "#56723f"

BODEN = 880
EBENEN = [
    (-1, "FAHRZEUGE · LOGISTIK", "HANGAR 19 · BIBI-PAKET-RESERVE"),
    (-2, "OBERKOMMANDO (BOK)", "BOSS-BIBI-BÜRO · H³"),
    (-3, "BIBI BOULEVARD", "WOHNEN · KULTUR · BIBI MAC · BIBIPLEXX · BBB"),
    (-4, "BIBI-KI · BIKZ", "RECHENZENTRUM · BLACK ARCHIVE"),
    (-5, "BZB", "BURGENLÄNDISCHER ZENTRALBAHNHOF"),
    (-6, "SPEZIAL-BIBI-SEKTOR", ""),
    (-7, "FORSCHUNG", ""),
    (-8, "ENERGIE · ÜBERLEBEN", "NOTKERN"),
]


def y_ebene(n):
    return BODEN + (-n) * 124 - 30


def burgenland_ebenen(p=None):
    rnd = random.Random(19)
    defs = lin("himmel", [(0, HIMMEL, 1), (1, HIMMEL2, 1)])
    defs += lin("fels", [(0, "#1b1d22", 1), (1, "#0c0d10", 1)])
    defs += (f'<linearGradient id="leitung" gradientUnits="userSpaceOnUse" x1="0" y1="1910" x2="0" y2="2140">'
             f'<stop offset="0" stop-color="{LEISE}" stop-opacity="0.9"/><stop offset="1" stop-color="{LEISE}" stop-opacity="0"/></linearGradient>')
    defs += ('<pattern id="schraffur" width="26" height="26" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
             '<path d="M0 0V26" stroke="#24272d" stroke-width="3"/></pattern>')
    s = [f'<rect width="{W}" height="{BODEN}" fill="url(#himmel)"/>']
    for x in range(0, W, 80):
        s.append(f'<path d="M{x} 0V{BODEN}" stroke="#1d2026" stroke-width="1"/>')
    for y in range(0, BODEN, 80):
        s.append(f'<path d="M0 {y}H{W}" stroke="#1d2026" stroke-width="1"/>')

    # Fels unter dem Gelaende
    s.append(f'<rect x="0" y="{BODEN}" width="{W}" height="{H - BODEN}" fill="url(#fels)"/>')
    s.append(f'<rect x="0" y="{BODEN}" width="{W}" height="{H - BODEN}" fill="url(#schraffur)"/>')

    # Der Berg (kuenstlich, facettiert)
    punkte = [(240, BODEN), (560, 720), (820, 650), (1080, 470), (1400, 390), (1700, 250), (1900, 196), (2140, 262),
              (2440, 370), (2700, 470), (2960, 590), (3260, 700), (3600, BODEN)]
    pfad = "M" + " L".join(f"{x} {y}" for x, y in punkte) + " Z"
    s.append(f'<path d="{pfad}" fill="{BERG}" stroke="{BERG_R}" stroke-width="5" stroke-linejoin="round"/>')
    for (x1, y1), (x2, y2) in zip(punkte[1:-1], punkte[2:-1]):
        s.append(f'<path d="M{x1} {y1} L{(x1 + x2) / 2 + rnd.uniform(-60, 60):.0f} {BODEN - 160} L{x2} {y2}Z" fill="{BERG_H}" fill-opacity="{rnd.uniform(0.25, 0.7):.2f}"/>')
    s.append(f'<path d="{pfad}" fill="none" stroke="{BERG_R}" stroke-width="5" stroke-linejoin="round"/>')

    # Weinberge ringsum
    for x0, x1 in ((0, 230), (3610, W)):
        for k in range(8):
            y = BODEN - 20 - k * 22
            s.append(f'<path d="M{x0 + 10} {y}H{x1 - 10}" stroke="{REBE}" stroke-width="9" stroke-dasharray="14 9" stroke-linecap="round"/>')
    for k in range(6):
        y = BODEN - 30 - k * 26
        s.append(f'<path d="M{300 + k * 50} {y}L{560 + k * 10} {y - 40}" stroke="{REBE}" stroke-width="8" stroke-dasharray="12 8" stroke-linecap="round"/>')

    # Oberflaeche
    s.append(f'<path d="M1900 196V60M1870 196L1900 110L1930 196M1960 196V100" stroke="{TEXT}" stroke-width="5" fill="none"/>')
    s.append(f'<circle cx="1900" cy="60" r="10" fill="{GELB}"/>')
    s.append(t(1990, 96, "GIPFEL-KOMMUNIKATION", 24, TEXT, abstand=3))
    for hx in (2560, 2700):
        hy = 430 if hx == 2560 else 470
        s.append(f'<ellipse cx="{hx}" cy="{hy - 6}" rx="56" ry="16" fill="#1f2226" stroke="{TEXT}" stroke-width="3"/>')
        s.append(t(hx, hy + 2, "H", 22, GELB, "middle", True, SANS, 0))
    s.append(t(2780, 420, "HELIPADS", 24, TEXT, abstand=3))
    s.append(f'<circle cx="2280" cy="306" r="22" fill="#1f2226" stroke="{TEXT}" stroke-width="3"/><path d="M2264 306h32" stroke="{TEXT}" stroke-width="3"/>')
    s.append(t(2320, 296, "RAKETENSILO", 22, LEISE, abstand=3))
    for k in range(5):
        s.append(f'<path d="M{930 + k * 14} {560 - k * 8}l110 -64" stroke="{TEXT}" stroke-width="3" stroke-opacity="0.7"/>')
    s.append(f'<path d="M{900} {470}L{960} {530}" stroke="{LEISE}" stroke-width="2"/>')
    s.append(t(560, 440, "SCHIESSSTÄNDE", 24, TEXT, abstand=3))
    s.append(t(560, 472, "Blick über die Weinberge", 20, LEISE, schrift=SANS, abstand=1))
    s.append(f'<rect x="3300" y="{BODEN - 22}" width="540" height="22" fill="#1f2226"/>')
    s.append(f'<path d="M3320 {BODEN - 11}H3840" stroke="{TEXT}" stroke-width="3" stroke-dasharray="30 22"/>')
    s.append(t(3480, BODEN - 48, "FLUGFELD", 24, TEXT, abstand=3))
    s.append(f'<rect x="1060" y="{BODEN - 70}" width="300" height="70" fill="#1f2226" stroke="{BERG_R}" stroke-width="3"/>')
    s.append(t(1046, BODEN - 20, "LOGISTIKHOF", 22, TEXT, "end", abstand=2))
    # Ehrenportal auf Ebene 0
    s.append(f'<path d="M640 {BODEN} V{BODEN - 120} a90 90 0 0 1 180 0 V{BODEN}" fill="#0d0e11" stroke="{GOLD}" stroke-width="6"/>')
    s.append(t(730, BODEN - 230, "EHRENPORTAL", 24, GOLD, "middle", True, abstand=4))
    s.append(f'<rect x="900" y="{BODEN - 150}" width="1900" height="66" fill="{DECKE}" stroke="{DECKE_R}" stroke-width="3"/>')
    s.append(t(1460, BODEN - 106, "0   VERTEILERKERN", 24, TEXT, abstand=4))

    # Gelaendelinie
    s.append(f'<path d="M0 {BODEN}H{W}" stroke="{TEXT}" stroke-width="5"/>')

    # Ebenen
    ex0, ex1 = 620, 3060
    for n, titel, unter in EBENEN:
        y = y_ebene(n)
        if n == -5:
            s.append(f'<rect x="-10" y="{y}" width="{W + 20}" height="74" fill="{DECKE}" stroke="{DECKE_R}" stroke-width="3"/>')
            s.append(f'<path d="M0 {y + 70}H{W}" stroke="{GOLD}" stroke-width="3" stroke-dasharray="26 12"/>')
            for k in range(5):
                zx = 2150 + k * 170
                s.append(f'<rect x="{zx}" y="{y + 14}" width="158" height="44" rx="12" fill="#30343b" stroke="{TEXT}" stroke-width="2"/>')
                for f in range(4):
                    s.append(f'<rect x="{zx + 16 + f * 36}" y="{y + 22}" width="22" height="12" fill="{GELB}" fill-opacity="0.8"/>')
            s.append(f'<path d="M{2150 + 5 * 170 - 12} {y + 14}q60 0 70 44h-70z" fill="#30343b" stroke="{TEXT}" stroke-width="2"/>')
            s.append(t(1960, y + 50, "-5  BZB", 34, GELB, "middle", True, abstand=6))
            s.append(t(1360, y + 46, "← B1 · H&amp;H-DIREKTLINIE", 22, TEXT, abstand=3))
            continue
        s.append(f'<rect x="{ex0}" y="{y}" width="{ex1 - ex0}" height="74" fill="{DECKE}" stroke="{DECKE_R}" stroke-width="3"/>')
        s.append(t(ex0 + 24, y + 48, str(n), 30, GELB, fett=True, abstand=0))
    for n, titel, unter in EBENEN:
        y = y_ebene(n)
        lx = ex1 + 60
        s.append(f'<path d="M{ex1} {y + 37}H{lx - 14}" stroke="{LEISE}" stroke-width="2"/>')
        if n == -5:
            s.append(t(lx, y + 30, unter, 20, TEXT, abstand=2))
            s.append(t(lx, y + 60, "ALPENLINIE → BIBI ARSENAL", 20, GOLD, abstand=3))
            continue
        s.append(t(lx, y + 32 if unter else y + 46, f"{n}  {titel}", 26 if unter else 28, TEXT, fett=True, abstand=3))
        if unter:
            s.append(t(lx, y + 64, unter, 20, LEISE, abstand=2))

    # Big Bibi: Megaaufzug vom Logistikhof bis -8
    bx0, bx1 = 1100, 1320
    ytop, yunten = BODEN - 70, y_ebene(-8) + 74
    s.append(f'<rect x="{bx0}" y="{ytop}" width="{bx1 - bx0}" height="{yunten - ytop}" fill="#0f1013" stroke="{GELB}" stroke-width="4"/>')
    for k in range(int((yunten - ytop) / 40)):
        yy = ytop + k * 40
        s.append(f'<path d="M{bx0} {yy}l14 20M{bx1} {yy}l-14 20" stroke="{GELB}" stroke-width="5"/>')
    py = y_ebene(-2) + 20
    s.append(f'<rect x="{bx0 + 10}" y="{py + 40}" width="{bx1 - bx0 - 20}" height="14" fill="{GELB}"/>')
    s.append(f'<path d="M{bx0 + 40} {py + 40}v-26h40l10-16h60l10 16h30v26z" fill="#4a4f57" stroke="{TEXT}" stroke-width="2"/>')
    s.append(f'<path d="M{bx0 + 150} {py + 6}h70" stroke="#4a4f57" stroke-width="8"/>')
    for k in range(3):
        s.append(f'<path d="M{bx0 + 30 + k * 70} {ytop}V{py + 40}" stroke="{TEXT}" stroke-width="1.5" stroke-opacity="0.4"/>')

    # Detail B: Hebel AUF - HALT - AB
    dx, dy = 60, 1040
    s.append(f'<rect x="{dx}" y="{dy}" width="500" height="560" rx="18" fill="#1a1c21" stroke="{GELB}" stroke-width="3"/>')
    s.append(t(dx + 30, dy + 60, "BIG BIBI", 40, GELB, fett=True, abstand=6))
    s.append(t(dx + 30, dy + 100, "MEGAAUFZUG · 24/7", 22, LEISE, abstand=3))
    s.append(f'<rect x="{dx + 130}" y="{dy + 140}" width="240" height="280" rx="14" fill="#2b2e33" stroke="{TEXT}" stroke-width="3"/>')
    for i, w in enumerate(("AUF", "HALT", "AB")):
        yy = dy + 190 + i * 90
        s.append(t(dx + 170, yy + 10, w, 30, WEISS if i != 1 else GELB, fett=True, abstand=4))
        s.append(f'<path d="M{dx + 300} {yy}h40" stroke="{LEISE}" stroke-width="3"/>')
    s.append(f'<path d="M{dx + 330} {dy + 280}L{dx + 420} {dy + 200}" stroke="{TEXT}" stroke-width="12" stroke-linecap="round"/>')
    s.append(f'<circle cx="{dx + 424}" cy="{dy + 196}" r="22" fill="#d7263d"/><circle cx="{dx + 330}" cy="{dy + 280}" r="14" fill="{TEXT}"/>')
    s.append(t(dx + 30, dy + 480, "„Es gäbe schnellere Wege.", 24, TEXT, schrift=SANS, abstand=1))
    s.append(t(dx + 30, dy + 516, "Aber keiner davon ist Big Bibi.“", 24, TEXT, schrift=SANS, abstand=1))
    s.append(f'<path d="M{dx + 500} {dy + 200}L{bx0} {dy + 200}" stroke="{GELB}" stroke-width="2" stroke-dasharray="10 8"/>')

    # Leitungen fuehren weiter nach unten (ohne Beschriftung)
    for lx in (1700, 1760, 2380):
        s.append(f'<path d="M{lx} {yunten}V{H}" stroke="url(#leitung)" stroke-width="10"/>')

    # Schriftfeld
    fx, fy = 2900, 120
    s.append(f'<rect x="{fx}" y="{fy}" width="880" height="270" fill="#15171b" stroke="{TEXT}" stroke-width="4"/>')
    s.append(f'<path d="M{fx} {fy + 76}H{fx + 880}M{fx} {fy + 200}H{fx + 880}" stroke="{TEXT}" stroke-width="2"/>')
    s.append(t(fx + 28, fy + 54, "BURGENLAND · DER BERG", 40, WEISS, fett=True, abstand=3))
    s.append(t(fx + 28, fy + 124, "BB-BGLD · BB-HQ-01 · EBENENPLAN", 24, LEISE, abstand=3))
    s.append(t(fx + 28, fy + 166, "VERZÖGERUNGSGRUND LAUT BAUBERICHT: BERG.", 22, GELB, abstand=2))
    s.append(t(fx + 28, fy + 248, "„Dann bauen wir einen.“ – Boss Bibi", 24, TEXT, schrift=SANS, abstand=1))
    return svg("".join(s), defs)
