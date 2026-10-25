"""Nassmacher: Parkplan des Schwimmerlebnisparks an der Donau (Masterbrief 11.1-11.4)."""
import math
import random

from ._hilfen import W, H, MONO, SANS, svg, lin, rad, t

RASEN, RASEN_D = "#86cf6c", "#5fae55"
WEG = "#f6e7bf"
WASSER, WASSER_H, WASSER_D = "#2ed3e6", "#9ff1f8", "#14a9c4"
DONAU, DONAU_D = "#2a8fd6", "#1d6fb0"
ORANGE, LILA, PINK = "#ff8a1f", "#7a3cd6", "#ff5c8a"
HOLZ, HOLZ_D = "#b9773e", "#7d4a20"
WEISS = "#ffffff"
DUNKEL = "#16324a"


def schild(x, y, text, farbe=DUNKEL, gr=40, bg=WEISS):
    b = len(text) * gr * 0.8 + 70
    return (f'<rect x="{x - b / 2 + 6}" y="{y - gr - 14}" width="{b}" height="{gr + 40}" rx="{(gr + 40) / 2}" fill="#000" fill-opacity="0.15"/>'
            f'<rect x="{x - b / 2}" y="{y - gr - 20}" width="{b}" height="{gr + 40}" rx="{(gr + 40) / 2}" fill="{bg}"/>'
            + t(x, y + 4, text, gr, farbe, "middle", True, SANS, 3))


def notiz(x, y, text, farbe=DUNKEL, gr=26):
    return t(x, y, text, gr, farbe, "middle", False, SANS, 2)


def baum(x, y, r, rnd):
    g = rnd.choice(["#4f9e46", "#5aae4c", "#3f8a3c"])
    return (f'<circle cx="{x + r * 0.25:.0f}" cy="{y + r * 0.3:.0f}" r="{r}" fill="#000" fill-opacity="0.12"/>'
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{g}"/>'
            f'<circle cx="{x - r * 0.3:.0f}" cy="{y - r * 0.3:.0f}" r="{r * 0.45:.0f}" fill="#fff" fill-opacity="0.12"/>')


def schirm(x, y, r, farbe):
    o = [f'<circle cx="{x + 8}" cy="{y + 10}" r="{r}" fill="#000" fill-opacity="0.15"/>']
    for k in range(8):
        a1, a2 = math.radians(k * 45), math.radians(k * 45 + 45)
        f = farbe if k % 2 else WEISS
        o.append(f'<path d="M{x} {y}L{x + r * math.cos(a1):.1f} {y + r * math.sin(a1):.1f}A{r} {r} 0 0 1 '
                 f'{x + r * math.cos(a2):.1f} {y + r * math.sin(a2):.1f}Z" fill="{f}"/>')
    return "".join(o)


def reifen(x, y, r, farbe):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{farbe}" stroke-width="{r * 0.55:.0f}"/>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="#fff" stroke-width="{r * 0.55:.0f}" stroke-dasharray="{r * 0.5:.0f} {r * 1.07:.0f}"/>')


def boot(x, y, art, s=1.0):
    if art == "fischer":     # Reisrausch
        return (f'<path d="M{x - 70 * s} {y}h140 l-24 34h-92z" fill="#e9e2d0" stroke="{DUNKEL}" stroke-width="4"/>'
                f'<rect x="{x - 10 * s}" y="{y - 46 * s}" width="40" height="46" fill="{ORANGE}" stroke="{DUNKEL}" stroke-width="4"/>'
                f'<path d="M{x - 40 * s} {y}V{y - 70 * s}l60 50" fill="none" stroke="{DUNKEL}" stroke-width="4"/>')
    if art == "schlauch":    # Noodle Kuebel
        return (f'<rect x="{x - 64 * s}" y="{y - 16 * s}" width="{128 * s}" height="{52 * s}" rx="{26 * s}" fill="#ffd400" stroke="{DUNKEL}" stroke-width="4"/>'
                f'<rect x="{x - 40 * s}" y="{y - 2 * s}" width="{80 * s}" height="{24 * s}" rx="{12 * s}" fill="#ffefa0"/>')
    if art == "speed":       # DIE BOWL
        return (f'<path d="M{x - 90 * s} {y}h150q40 0 60 18q-20 18 -60 18h-150z" fill="#fff" stroke="{DUNKEL}" stroke-width="4"/>'
                f'<path d="M{x - 90 * s} {y + 22 * s}h210" stroke="{PINK}" stroke-width="8"/>'
                f'<path d="M{x - 20 * s} {y}l30 -28h40l-10 28z" fill="#9fdcff" stroke="{DUNKEL}" stroke-width="4"/>')
    # Bowlschlepper
    return (f'<path d="M{x - 90 * s} {y}h180l-20 44h-140z" fill="#1d4f8a" stroke="{DUNKEL}" stroke-width="4"/>'
            f'<rect x="{x - 40 * s}" y="{y - 50 * s}" width="{80 * s}" height="{50 * s}" rx="6" fill="#fff" stroke="{DUNKEL}" stroke-width="4"/>'
            f'<rect x="{x + 10 * s}" y="{y - 84 * s}" width="{18 * s}" height="{34 * s}" fill="{ORANGE}" stroke="{DUNKEL}" stroke-width="4"/>'
            f'<circle cx="{x - 60 * s}" cy="{y + 20 * s}" r="{10 * s}" fill="none" stroke="{ORANGE}" stroke-width="6"/>')


def sauna(x, y, b, h, name, farbe=HOLZ, dach="#6b3a18", gr=26):
    o = [f'<rect x="{x + 10}" y="{y + 14}" width="{b}" height="{h}" rx="10" fill="#000" fill-opacity="0.15"/>',
         f'<rect x="{x}" y="{y}" width="{b}" height="{h}" rx="10" fill="{farbe}" stroke="{HOLZ_D}" stroke-width="4"/>',
         f'<path d="M{x} {y + h / 2}H{x + b}" stroke="{dach}" stroke-width="5"/>']
    for k in range(1, int(b / 28)):
        o.append(f'<path d="M{x + k * 28} {y + 6}V{y + h / 2 - 4}M{x + k * 28} {y + h / 2 + 4}V{y + h - 6}" stroke="{dach}" stroke-width="2" stroke-opacity="0.5"/>')
    if name:
        o.append(f'<rect x="{x + b / 2 - len(name) * gr * 0.36 - 16}" y="{y + h / 2 - gr * 0.8}" width="{len(name) * gr * 0.72 + 32}" height="{gr * 1.5}" rx="8" fill="#fff6e6"/>')
        o.append(t(x + b / 2, y + h / 2 + gr * 0.35, name, gr, HOLZ_D, "middle", True, SANS, 2))
    return "".join(o)


def rutsche(d, farbe, rand, breite, licht=False):
    o = [f'<path d="{d}" fill="none" stroke="{rand}" stroke-width="{breite + 16}" stroke-linecap="round"/>',
         f'<path d="{d}" fill="none" stroke="{farbe}" stroke-width="{breite}" stroke-linecap="round"/>']
    if licht:
        o.append(f'<path d="{d}" fill="none" stroke="#ffe680" stroke-width="10" stroke-dasharray="2 34" stroke-linecap="round"/>')
    else:
        o.append(f'<path d="{d}" fill="none" stroke="#fff" stroke-width="6" stroke-opacity="0.5" stroke-linecap="round"/>')
    return "".join(o)


def nass_parkplan(p=None):
    rnd = random.Random(11)
    defs = lin("rasen", [(0, RASEN, 1), (1, RASEN_D, 1)])
    defs += lin("donau", [(0, DONAU, 1), (1, DONAU_D, 1)])
    defs += rad("becken", [(0, WASSER_H, 1), (0.7, WASSER, 1), (1, WASSER_D, 1)])
    defs += lin("hohesee", [(0, "#1c5d9e", 1), (1, WASSER, 1)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#rasen)"/>']
    for _ in range(420):
        x, y = rnd.uniform(0, W), rnd.uniform(0, 1660)
        s.append(f'<path d="M{x:.0f} {y:.0f}l6 -14l6 14" fill="none" stroke="#74c160" stroke-width="3"/>')

    # Donau
    ufer = "M0 1720 C600 1680 1200 1760 1900 1710 S3200 1660 3840 1710 V2160 H0Z"
    s.append(f'<path d="{ufer}" transform="translate(0 -22)" fill="{WEG}"/>')
    s.append(f'<path d="{ufer}" fill="url(#donau)"/>')
    for k in range(14):
        x = 1500 + k * 100 if k < 9 else 1500 + k * 100
        s.append(f'<path d="M{x} {1830 + (k % 3) * 70} q30 -16 60 0 t60 0" fill="none" stroke="#bfe6ff" stroke-width="5" stroke-linecap="round" stroke-opacity="0.7"/>')
    s.append(t(3260, 2000, "DONAU", 90, "#bfe6ff", "middle", True, SANS, 30))

    # Wege: Promenade und zwei Querwege
    for d in ["M60 1590 C700 1540 1300 1620 1900 1570 S3100 1550 3800 1590",
              "M1500 80 C1530 600 1470 1100 1500 1580", "M2280 80 C2250 600 2310 1100 2280 1580"]:
        s.append(f'<path d="{d}" fill="none" stroke="{WEG}" stroke-width="64" stroke-linecap="round"/>')

    # ------------------------------------------------ Rutsch und Flutsch
    bx, by = 800, 900
    s.append(f'<ellipse cx="{bx}" cy="{by}" rx="540" ry="450" fill="{WEG}"/>')
    for ex in (-330, 330):
        s.append(f'<circle cx="{bx + ex}" cy="{by - 300}" r="185" fill="{WEG}"/>')
    for ex in (-330, 330):
        s.append(f'<circle cx="{bx + ex}" cy="{by - 300}" r="150" fill="url(#becken)" stroke="#fff" stroke-width="12"/>')
        s.append(f'<circle cx="{bx + ex}" cy="{by - 300}" r="78" fill="#ffd6e2" fill-opacity="0.35"/>')
    s.append(f'<ellipse cx="{bx}" cy="{by}" rx="460" ry="380" fill="url(#becken)" stroke="#fff" stroke-width="14"/>')
    for k in range(7):
        s.append(f'<path d="M{bx - 300 + k * 90} {by + 170 + (k % 2) * 40} q22 -12 44 0" fill="none" stroke="#fff" stroke-width="4" stroke-opacity="0.6"/>')
    for k, f in enumerate([ORANGE, PINK, "#ffd400", LILA, ORANGE, "#fff"]):
        s.append(reifen(bx - 250 + k * 100, by + 90 + (k % 2) * 80, 26, f))
    # Turm zwischen den Ohren, beide Rutschen starten gemeinsam
    tx, ty = bx, by - 470
    links = f"M{tx - 60} {ty} C{tx - 520} {ty - 120} {tx - 820} {ty + 120} {tx - 700} {ty + 520} S{tx - 520} {ty + 760} {tx - 300} {ty + 640}"
    rechts = f"M{tx + 60} {ty} C{tx + 520} {ty - 120} {tx + 820} {ty + 120} {tx + 700} {ty + 520} S{tx + 520} {ty + 760} {tx + 300} {ty + 640}"
    s.append(rutsche(links, ORANGE, "#fff", 44))
    s.append(rutsche(rechts, LILA, DUNKEL, 56, licht=True))
    s.append(f'<rect x="{tx - 90}" y="{ty - 80}" width="180" height="150" rx="16" fill="#fff" stroke="{DUNKEL}" stroke-width="6"/>')
    s.append(f'<rect x="{tx - 62}" y="{ty - 52}" width="124" height="94" rx="10" fill="{ORANGE}"/>')
    s.append(t(tx, ty + 8, "START", 30, "#fff", "middle", True, SANS, 3))
    s.append(schild(330, 150, "HIERZ-RUTSCHE", ORANGE, 30))
    s.append(notiz(330, 214, "die schnellere"))
    s.append(schild(1270, 150, "HABL-RUTSCHE", LILA, 30))
    s.append(notiz(1270, 214, "geschlossen · Licht und ASMR"))
    s.append(schild(bx, 1440, "RUTSCH UND FLUTSCH", DUNKEL, 54, "#ffd400"))

    # ------------------------------------------------ Bibi Mac und Die Hohe See
    mx, my = 1890, 260
    s.append(f'<rect x="{mx - 170}" y="{my - 90}" width="340" height="200" rx="18" fill="#d62a1e" stroke="{DUNKEL}" stroke-width="6"/>')
    s.append(f'<rect x="{mx - 170}" y="{my - 90}" width="340" height="60" rx="18" fill="#ffc72c"/>')
    s.append(t(mx, my - 46, "BIBI MAC", 38, "#d62a1e", "middle", True, SANS, 4))
    s.append(f'<path d="M{mx - 50} {my + 30} q50 40 100 0" fill="none" stroke="#ffc72c" stroke-width="12" stroke-linecap="round"/>')
    s.append(f'<rect x="{mx - 300}" y="{my + 150}" width="600" height="120" rx="12" fill="#fff" stroke="#d62a1e" stroke-width="5"/>')
    s.append(t(mx, my + 200, "BITTE NICHT MIT POMMES", 30, "#d62a1e", "middle", True, SANS, 2))
    s.append(t(mx, my + 246, "IN DIE BIG-BIBI-RUTSCHE.", 30, "#d62a1e", "middle", True, SANS, 2))

    hx, hy = 1890, 1000
    s.append(f'<path d="M{hx - 250} {hy - 230}h500l80 470h-660z" fill="{WEG}"/>')
    s.append(f'<path d="M{hx - 210} {hy - 200}h420l62 410h-544z" fill="url(#hohesee)" stroke="#fff" stroke-width="10"/>')
    for k in range(6):
        yy = hy - 150 + k * 62
        s.append(f'<path d="M{hx - 200 - k * 9} {yy} q32 -22 64 0 t64 0 t64 0 t64 0 t64 0 t64 0 t64 0" fill="none" stroke="#fff" stroke-width="7" stroke-opacity="{0.9 - k * 0.1:.1f}" stroke-linecap="round"/>')
    s.append(f'<path d="M{hx + 170} {hy - 200}V{hy - 330}" stroke="{DUNKEL}" stroke-width="8"/>')
    s.append(f'<path d="M{hx + 174} {hy - 330}h90l-20 30 20 30h-90z" fill="#ff6a13"/>')
    s.append(schild(hx, hy + 360, "DIE HOHE SEE", "#1c3f7a", 40))

    # ------------------------------------------------ Burgenland River, Kleine Donau, Bowlhafen
    rx_, ry_ = 2670, 620
    fluss = f"M{rx_ - 300} {ry_} a300 250 0 1 0 600 0 a300 250 0 1 0 -600 0"
    s.append(f'<path d="{fluss}" fill="none" stroke="{WEG}" stroke-width="170"/>')
    s.append(f'<path d="{fluss}" fill="none" stroke="url(#becken)" stroke-width="116"/>')
    s.append(f'<path d="{fluss}" fill="none" stroke="#fff" stroke-width="5" stroke-dasharray="20 30" stroke-opacity="0.8"/>')
    for k in range(5):
        yy = ry_ - 92 + k * 46
        s.append(f'<path d="M{rx_ - 140} {yy}H{rx_ + 140}" stroke="#4d8f3f" stroke-width="14" stroke-dasharray="16 10" stroke-linecap="round"/>')
    for k, f in enumerate([ORANGE, PINK, "#ffd400", LILA, ORANGE, PINK, "#fff", "#ffd400"]):
        a = math.radians(k * 45 + 10)
        s.append(reifen(rx_ + 300 * math.cos(a), ry_ + 250 * math.sin(a), 28, f))
    s.append(schild(rx_, 200, "BURGENLAND RIVER", "#2c6b2f", 42))
    kd = f"M{rx_ + 200} {ry_ + 200} C{rx_ + 360} {ry_ + 360} {rx_ + 60} {ry_ + 420} {rx_ + 120} {ry_ + 560} S{rx_ + 280} {ry_ + 600} {rx_ + 200} {ry_ + 700}"
    s.append(f'<path d="{kd}" fill="none" stroke="{WEG}" stroke-width="120" stroke-linecap="round"/>')
    s.append(f'<path d="{kd}" fill="none" stroke="{DONAU}" stroke-width="76" stroke-linecap="round"/>')
    s.append(t(rx_ - 130, ry_ + 520, "KLEINE DONAU", 30, "#1d4f8a", "middle", True, SANS, 3))
    hbx, hby = 2670, 1360
    s.append(f'<rect x="{hbx - 260}" y="{hby - 120}" width="520" height="270" rx="40" fill="{DONAU}" stroke="{WEG}" stroke-width="30"/>')
    s.append(f'<rect x="{hbx - 260}" y="{hby - 150}" width="520" height="40" rx="10" fill="{HOLZ}" stroke="{HOLZ_D}" stroke-width="4"/>')
    s.append(boot(hbx - 170, hby - 50, "fischer", 0.8))
    s.append(boot(hbx, hby - 40, "schlauch", 0.8))
    s.append(boot(hbx + 160, hby - 50, "speed", 0.7))
    s.append(boot(hbx - 120, hby + 80, "schlepper", 0.7))
    s.append(notiz(hbx - 170, hby + 14, "Reisrausch", "#fff", 21))
    s.append(notiz(hbx, hby + 24, "Noodle Kübel", "#fff", 21))
    s.append(notiz(hbx + 170, hby + 14, "DIE BOWL", "#fff", 21))
    s.append(t(hbx - 40, hby + 110, "Schlepper · alle 30 Min.", 21, "#fff", schrift=SANS, abstand=1))
    s.append(schild(hbx, 1606, "BOWLHAFEN", "#1d4f8a", 36))

    # ------------------------------------------------ Dampf und Schwitz
    sx, sy = 3080, 110
    s.append(f'<rect x="{sx}" y="{sy}" width="690" height="1320" rx="40" fill="#efe1bd"/>')
    s.append(sauna(sx + 30, sy + 40, 390, 150, "DER HOHE DAMPF", "#8a4f22", "#4f2a0e", 27))
    s.append(sauna(sx + 440, sy + 40, 220, 150, "VOLLGAS", "#c4502a", "#7a2b10", 24))
    s.append(sauna(sx + 30, sy + 220, 330, 120, "DAMPFFLÜSTERN", "#b48a5e", gr=22))
    s.append(sauna(sx + 380, sy + 220, 280, 120, "LOUNGE", "#d9b98c", "#8a6a3e", 22))
    for k in range(3):
        s.append(sauna(sx + 30 + k * 215, sy + 370, 200, 150, f"GROSS {k + 1}", gr=22))
    s.append(f'<rect x="{sx + 30}" y="{sy + 550}" width="630" height="130" rx="16" fill="none" stroke="#8a6a3e" stroke-width="5" stroke-dasharray="20 14"/>')
    s.append(t(sx + 345, sy + 606, "MEDITATIONSBEREICH", 26, "#8a6a3e", "middle", True, SANS, 3))
    s.append(t(sx + 345, sy + 648, "IN PLANUNG", 22, "#8a6a3e", "middle", False, SANS, 6))
    sg = f"M{sx + 560} {sy + 720} C{sx + 680} {sy + 860} {sx + 420} {sy + 900} {sx + 500} {sy + 1040}"
    s.append(f'<path d="{sg}" fill="none" stroke="#fff" stroke-width="76" stroke-linecap="round"/>')
    s.append(f'<path d="{sg}" fill="none" stroke="#cfe9ff" stroke-width="36" stroke-dasharray="3 22" stroke-linecap="round"/>')
    s.append(f'<path d="M{sx + 420} {sy + 1100}l80 -70l80 70z" fill="#fff" stroke="{HOLZ_D}" stroke-width="5"/>')
    s.append(f'<rect x="{sx + 440}" y="{sy + 1100}" width="120" height="80" fill="{HOLZ}" stroke="{HOLZ_D}" stroke-width="5"/>')
    s.append(t(sx + 200, sy + 860, "DER SCHNEEGANG", 24, "#3a6e99", "middle", True, SANS, 2))
    s.append(t(sx + 200, sy + 896, "zur Berghütte", 22, "#3a6e99", "middle", False, SANS, 2))
    s.append(t(sx + 200, sy + 1150, "BERGHÜTTE", 22, HOLZ_D, "middle", True, SANS, 3))
    s.append(schild(sx + 345, sy + 1280, "DAMPF UND SCHWITZ", HOLZ_D, 40, "#fff6e6"))

    for x, y in [(130, 330), (150, 1300), (1390, 1290), (1400, 700), (2960, 1050), (2990, 1460),
                 (940, 120), (1330, 1500), (2200, 1250), (3000, 300), (2420, 1520)]:
        s.append(baum(x, y, rnd.uniform(44, 66), rnd))
    for x, y in [(1640, 1480), (1760, 1500), (2120, 1490)]:
        s.append(schirm(x, y, 42, ORANGE if x % 3 else PINK))

    # Titelkarte
    s.append(f'<rect x="130" y="1790" width="1240" height="250" rx="34" fill="#000" fill-opacity="0.18" transform="translate(10 12)"/>')
    s.append(f'<rect x="130" y="1790" width="1240" height="250" rx="34" fill="#fff"/>')
    s.append(f'<rect x="130" y="1790" width="30" height="250" rx="15" fill="{WASSER}"/>')
    s.append(t(200, 1890, "NASSMACHER", 92, DUNKEL, fett=True, schrift=SANS, abstand=8))
    s.append(t(204, 1950, "PARKPLAN · SCHWIMMERLEBNISPARK AN DER DONAU · WIEN", 28, "#3a6e99", schrift=SANS, abstand=3))
    s.append(t(204, 2000, "RUTSCHEN · WELLEN · FLUSS · SAUNA", 26, ORANGE, fett=True, schrift=SANS, abstand=6))
    return svg("".join(s), defs)
