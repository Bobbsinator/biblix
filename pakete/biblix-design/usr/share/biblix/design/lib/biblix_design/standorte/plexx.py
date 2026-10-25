"""Bibiplexx: Saalplan mit Direct-View-Wand, Bewegungssitzen und Reihe sieben (Masterbrief 9.5)."""
import math

from ._hilfen import W, H, MONO, SANS, svg, lin, rad, t

GRUND, GRUND2 = "#120a20", "#06030c"
SAAL = "#1a1030"
MAGENTA, LILA, ORANGE = "#d4398f", "#6b2fbf", "#ff8a3d"
CREME, LEISE = "#efe6ff", "#8f7bb3"
SITZ, SITZ_R = "#3a2760", "#56408a"

CX, CY = 1920, -2400         # Mittelpunkt der Sitzboegen (flache Boegen)
R_WAND = 2650
REIHEN = 13


def sitz(x, y, winkel, farbe, rand):
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({winkel:.2f})">'
            f'<rect x="-29" y="-22" width="58" height="48" rx="12" fill="{farbe}" stroke="{rand}" stroke-width="3"/>'
            f'<rect x="-25" y="14" width="50" height="14" rx="6" fill="{rand}"/>'
            f'<rect x="-33" y="-14" width="8" height="34" rx="4" fill="{rand}"/><rect x="25" y="-14" width="8" height="34" rx="4" fill="{rand}"/>'
            f'</g>')


def lautsprecher(x, y, richtung):
    o = [f'<rect x="{x - 22}" y="{y - 34}" width="44" height="68" rx="8" fill="#2a1d46" stroke="{LEISE}" stroke-width="3"/>',
         f'<circle cx="{x}" cy="{y + 8}" r="13" fill="none" stroke="{LEISE}" stroke-width="3"/><circle cx="{x}" cy="{y - 20}" r="6" fill="{LEISE}"/>']
    for k in range(3):
        r = 46 + k * 26
        a0, a1 = (-40, 40) if richtung > 0 else (140, 220)
        p0 = (x + r * math.cos(math.radians(a0)), y + r * math.sin(math.radians(a0)))
        p1 = (x + r * math.cos(math.radians(a1)), y + r * math.sin(math.radians(a1)))
        o.append(f'<path d="M{p0[0]:.0f} {p0[1]:.0f}A{r} {r} 0 0 1 {p1[0]:.0f} {p1[1]:.0f}" fill="none" stroke="{MAGENTA}" '
                 f'stroke-width="4" stroke-opacity="{0.6 - k * 0.17:.2f}" stroke-linecap="round"/>')
    return "".join(o)


def plexx_saalplan(p=None):
    defs = lin("bg", [(0, GRUND, 1), (1, GRUND2, 1)])
    defs += lin("wand", [(0, LILA, 1), (0.45, MAGENTA, 1), (0.75, ORANGE, 1), (1, LILA, 1)], 0, 0, 1, 0)
    defs += rad("wandlicht", [(0, MAGENTA, 0.45), (0.6, LILA, 0.12), (1, LILA, 0)], 0.5, 0, 0.9)
    defs += rad("sieben", [(0, ORANGE, 0.5), (1, ORANGE, 0)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    # Sternenmuster der Saaldecke (Punkte), nur ganz leise
    for i in range(0, W, 96):
        for j in range(0, H, 96):
            s.append(f'<circle cx="{i + (j // 96 % 2) * 48}" cy="{j}" r="2" fill="{LEISE}" fill-opacity="0.15"/>')

    # Saal
    sx0, sx1, sy0, sy1 = 520, 3320, 60, 1980
    s.append(f'<path d="M{sx0 + 120} {sy0} H{sx1 - 120} L{sx1} {sy0 + 380} V{sy1} H{sx0} V{sy0 + 380} Z" fill="{SAAL}" '
             f'stroke="{LEISE}" stroke-width="6" stroke-linejoin="round"/>')
    s.append(f'<ellipse cx="{CX}" cy="{sy0}" rx="1700" ry="900" fill="url(#wandlicht)"/>')

    # Direct-View-Wand (Bogen)
    a = math.asin(900 / R_WAND)
    p0 = (CX - R_WAND * math.sin(a), CY + R_WAND * math.cos(a))
    p1 = (CX + R_WAND * math.sin(a), CY + R_WAND * math.cos(a))
    bogen = f"M{p0[0]:.0f} {p0[1]:.0f} A{R_WAND} {R_WAND} 0 0 0 {p1[0]:.0f} {p1[1]:.0f}"
    s.append(f'<path d="{bogen}" fill="none" stroke="url(#wand)" stroke-width="34" stroke-linecap="round"/>')
    s.append(f'<path d="{bogen}" fill="none" stroke="#fff" stroke-width="4" stroke-opacity="0.55"/>')
    s.append(t(CX, 340, "DIRECT-VIEW-WAND · KEIN PROJEKTOR", 30, CREME, "middle", True, MONO, 8))

    # Sitzreihen
    for r in range(1, REIHEN + 1):
        R = R_WAND + 140 + r * 104
        bogenlaenge = 82
        dth = bogenlaenge / R
        maxth = math.asin(min(0.999, 1180 / R))
        n = int(maxth / dth)
        links_x = None
        for k in range(-n, n + 1):
            th = k * dth
            x = CX + R * math.sin(th)
            y = CY + R * math.cos(th)
            if abs(abs(x - CX) - 440) < 56 or x < sx0 + 110 or x > sx1 - 110:
                continue
            if r == 7:
                s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="70" fill="url(#sieben)"/>')
                s.append(sitz(x, y, -math.degrees(th), ORANGE, "#ffc59a"))
            else:
                s.append(sitz(x, y, -math.degrees(th), SITZ, SITZ_R))
            if links_x is None:
                links_x = (x, y)
        if links_x:
            s.append(t(links_x[0] - 62, links_x[1] + 12, str(r), 30, ORANGE if r == 7 else LEISE, "end", r == 7, MONO, 0))

    # Reihe sieben: Hinweis
    R7 = R_WAND + 140 + 7 * 104
    th = math.asin(1050 / R7)
    zx, zy = CX + R7 * math.sin(th), CY + R7 * math.cos(th)
    s.append(f'<path d="M{zx + 40:.0f} {zy:.0f} L{sx1 + 60} {zy - 120:.0f} H{sx1 + 120}" fill="none" stroke="{ORANGE}" stroke-width="3"/>')
    s.append(t(sx1 + 132, zy - 108, "REIHE SIEBEN.", 40, ORANGE, fett=True, schrift=SANS, abstand=3))
    s.append(t(sx1 + 134, zy - 62, "„Butter.“", 30, CREME, schrift=SANS, abstand=1))

    # KI-Soundsystem
    for y in (560, 900, 1240, 1580):
        s.append(lautsprecher(sx0 + 44, y, 1))
        s.append(lautsprecher(sx1 - 44, y, -1))
    kx, ky = 60, 520
    s.append(f'<rect x="{kx}" y="{ky}" width="410" height="420" rx="22" fill="#1d1236" stroke="{MAGENTA}" stroke-width="3"/>')
    s.append(t(kx + 30, ky + 62, "KI-SOUNDSYSTEM", 30, MAGENTA, fett=True, abstand=3))
    zeilen = [("„Lauter.“", CREME), ("BEREITS", "#7fe3ff"), ("REFERENZPEGEL.", "#7fe3ff"), ("„Lauter.“", CREME), ("NEIN.", "#7fe3ff")]
    for i, (z, f) in enumerate(zeilen):
        s.append(t(kx + 30, ky + 132 + i * 56, z, 32 if f == CREME else 30, f, schrift=SANS if f == CREME else MONO, abstand=2,
                   fett=f != CREME))
    s.append(f'<path d="M{kx + 410} {ky + 220} L{sx0 + 20} 900" stroke="{MAGENTA}" stroke-width="2" stroke-dasharray="8 8"/>')

    # Eingaenge
    for x in (sx0 + 260, sx1 - 260):
        s.append(f'<rect x="{x - 90}" y="{sy1 - 12}" width="180" height="24" fill="{GRUND2}"/>')
        s.append(f'<path d="M{x - 90} {sy1} a90 90 0 0 1 90 -90" fill="none" stroke="{LEISE}" stroke-width="3"/>')
        s.append(t(x, sy1 - 110, "AUSGANG", 22, "#4be38b", "middle", True, MONO, 4))

    # Regel-Tafel
    s.append(f'<rect x="{CX - 420}" y="1820" width="840" height="110" rx="16" fill="#1d1236" stroke="{LEISE}" stroke-width="3"/>')
    s.append(t(CX, 1868, "KEIN SÜSSES POPCORN.", 36, CREME, "middle", True, SANS, 6))
    s.append(t(CX, 1910, "AUCH NICHT ALS OPTION.", 24, LEISE, "middle", False, MONO, 6))

    # Titel
    s.append(t(60, 190, "BIBIPLEXX", 76, CREME, fett=True, schrift=SANS, abstand=6))
    s.append(t(64, 250, "SAALPLAN", 32, MAGENTA, fett=True, abstand=14))
    s.append(t(64, 310, "Bewegungssitze", 26, LEISE, schrift=SANS, abstand=1))
    s.append(t(64, 350, "Direct-View statt Projektor", 26, LEISE, schrift=SANS, abstand=1))
    return svg("".join(s), defs)
