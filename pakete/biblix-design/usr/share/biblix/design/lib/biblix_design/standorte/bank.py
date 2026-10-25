"""Bibi Budget Bank: die Kurstafel in der Zugriffshalle von BBB-BGLD (Masterbrief, Kapitel BBB 3/4)."""
import random

from ._hilfen import W, H, MONO, SERIF, svg, lin, rad, t, schein

WAND, WAND2 = "#143528", "#0b2219"
HOLZ, HOLZ_D, HOLZ_H = "#4a2a17", "#2b170b", "#6e4021"
MESSING, MESSING_H, MESSING_D = "#c9a227", "#ecd27a", "#7d6213"
CREME = "#f3e9cf"
ROT = "#d8463a"

# (Stelle, Angebot, Hinweis, Trend) – alles Kanon aus Kapitel BBB / 9.6
ZEILEN = [
    ("BBB-BGLD", "RUHE+", "SCHALLSCHUTZ", "▲"),
    ("BBB-ANT", "WÄRME+", "SAUNAZEIT", "▲"),
    ("BBB-DW", "TAG+", "TAGESLICHT", "▲"),
    ("BBB-SCHW", "FENSTER+", "ECHTES FENSTER", "▲"),
    ("BBB-BGLD", "W-041 PREMIUM", "UNVERNÜNFTIG", "▲"),
    ("BBB-BGLD", "LIMITIERTES MENÜ", "MITTAGS", "▲"),
    ("BBB-BGLD", "GOLDENER TELLER", "RESERVIERUNG", "▲"),
    None,  # diese Zeile rattert gerade durch
]
SPALTEN = [8, 17, 14, 1]


def klappe(x, y, b, h, zeichen, farbe=CREME, kippt=False):
    s = [f'<rect x="{x:.0f}" y="{y:.0f}" width="{b}" height="{h}" rx="5" fill="#1d1d1d"/>',
         f'<rect x="{x:.0f}" y="{y:.0f}" width="{b}" height="{h / 2:.0f}" rx="5" fill="#242424"/>']
    if zeichen.strip():
        s.append(t(x + b / 2, y + h * 0.73, zeichen, int(h * 0.62), farbe, "middle", True, MONO, 0))
    s.append(f'<path d="M{x:.0f} {y + h / 2:.0f}h{b}" stroke="#050505" stroke-width="3"/>')
    if kippt:  # obere Klappe faellt gerade
        s.append(f'<path d="M{x + 3:.0f} {y + h / 2:.0f}L{x + b - 3:.0f} {y + h / 2:.0f}L{x + b + 2:.0f} {y + h * 0.78:.0f}'
                 f'L{x - 2:.0f} {y + h * 0.78:.0f}Z" fill="#2c2c2c" stroke="#111" stroke-width="2"/>')
    return "".join(s)


def lampe(cx, unten):
    """Gruene Bankerlampe mit Messingfuss, Lichtkegel auf dem Tresen."""
    return (schein(cx, unten - 20, 150, "lampenlicht")
            + f'<ellipse cx="{cx}" cy="{unten}" rx="44" ry="10" fill="{MESSING_D}"/>'
            + f'<rect x="{cx - 5}" y="{unten - 74}" width="10" height="70" fill="{MESSING}"/>'
            + f'<path d="M{cx - 70} {unten - 66} Q{cx} {unten - 128} {cx + 70} {unten - 66} Z" fill="url(#schirm)" '
              f'stroke="#0d3b24" stroke-width="3"/>'
            + f'<path d="M{cx - 70} {unten - 66}H{cx + 70}" stroke="{MESSING_H}" stroke-width="5" stroke-linecap="round"/>'
            + f'<ellipse cx="{cx}" cy="{unten - 60}" rx="56" ry="8" fill="#fff6c8" fill-opacity="0.85"/>')


def bank_kurstafel(p=None):
    rnd = random.Random(7)
    defs = lin("wand", [(0, WAND, 1), (1, WAND2, 1)])
    defs += lin("holz", [(0, HOLZ_H, 1), (1, HOLZ_D, 1)])
    defs += lin("messing", [(0, MESSING_H, 1), (0.5, MESSING, 1), (1, MESSING_D, 1)])
    defs += lin("schirm", [(0, "#2fa36a", 1), (1, "#0f5a35", 1)])
    defs += lin("marmor", [(0, "#efece6", 1), (0.5, "#d8d4cb", 1), (1, "#f4f2ee", 1)], 0, 0, 1, 0)
    defs += rad("lampenlicht", [(0, "#ffe9a8", 0.35), (1, "#ffe9a8", 0)])
    defs += rad("leuchter", [(0, "#ffe2a0", 0.55), (1, "#ffe2a0", 0)])
    defs += lin("bodenschatten", [(0, "#000", 0.55), (1, "#000", 0)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#wand)"/>']

    # Kassettendecke
    s.append(f'<rect width="{W}" height="210" fill="{HOLZ_D}"/>')
    for i in range(16):
        x = 20 + i * 240
        s.append(f'<rect x="{x}" y="22" width="200" height="160" fill="{HOLZ}" stroke="{HOLZ_H}" stroke-width="4"/>')
        s.append(f'<rect x="{x + 22}" y="44" width="156" height="116" fill="{HOLZ_D}" stroke="{MESSING_D}" stroke-width="2"/>')
        s.append(f'<circle cx="{x + 100}" cy="102" r="14" fill="url(#messing)"/>')
    s.append(f'<rect y="200" width="{W}" height="14" fill="url(#messing)"/>')

    # Fries mit Leitsatz
    s.append(f'<rect y="214" width="{W}" height="104" fill="#0e2a1f"/>')
    s.append(f'<path d="M0 226H{W}M0 306H{W}" stroke="{MESSING_D}" stroke-width="3"/>')
    s.append(t(W / 2, 286, "DIE BIBI BUDGET BANK VERTEILT KEIN GELD. SIE VERTEILT ZUGRIFF.", 46, MESSING_H, "middle",
               False, SERIF, 9))

    # Leuchter
    for lx in (330, W - 330):
        s.append(schein(lx, 470, 260, "leuchter"))
        s.append(f'<path d="M{lx} 318V420" stroke="{MESSING_D}" stroke-width="4"/>')
        s.append(f'<path d="M{lx - 90} 450 Q{lx} 520 {lx + 90} 450" fill="none" stroke="url(#messing)" stroke-width="8"/>')
        for dx in (-90, -45, 0, 45, 90):
            yy = 450 + (0 if abs(dx) == 90 else 30 if abs(dx) == 45 else 38)
            s.append(f'<rect x="{lx + dx - 6}" y="{yy - 34}" width="12" height="32" fill="{CREME}"/>')
            s.append(f'<ellipse cx="{lx + dx}" cy="{yy - 44}" rx="7" ry="12" fill="#ffd77a"/>')
        s.append(f'<circle cx="{lx}" cy="420" r="16" fill="url(#messing)"/>')

    # Marmorpfeiler
    for px in (560, W - 560 - 130):
        s.append(f'<rect x="{px}" y="318" width="130" height="1190" fill="url(#marmor)"/>')
        for _ in range(5):
            y0 = rnd.uniform(360, 1400)
            s.append(f'<path d="M{px + rnd.uniform(5, 40):.0f} {y0:.0f} q{rnd.uniform(20, 60):.0f} {rnd.uniform(60, 140):.0f} '
                     f'{rnd.uniform(50, 110):.0f} {rnd.uniform(160, 260):.0f}" fill="none" stroke="#a9a49a" stroke-width="2" stroke-opacity="0.6"/>')
        s.append(f'<rect x="{px - 16}" y="318" width="162" height="34" fill="url(#messing)"/>')
        s.append(f'<rect x="{px - 16}" y="1480" width="162" height="30" fill="url(#messing)"/>')

    # Rohrpost
    for rx_ in (460, W - 460):
        s.append(f'<path d="M{rx_} 318V1360 q0 60 60 60H{rx_ + (180 if rx_ < W / 2 else -180)}" fill="none" '
                 f'stroke="url(#messing)" stroke-width="22" stroke-linecap="round"/>')
        s.append(f'<path d="M{rx_} 318V1360" stroke="{MESSING_H}" stroke-width="4" stroke-opacity="0.6"/>')
    s.append(f'<rect x="444" y="760" width="32" height="70" rx="14" fill="{CREME}" stroke="{MESSING_D}" stroke-width="3"/>')
    s.append(f'<path d="M444 795h32" stroke="{MESSING_D}" stroke-width="3"/>')

    # Kurstafel
    bx, by, bw, bh = 760, 350, W - 1520, 1000
    s.append(f'<rect x="{bx - 26}" y="{by - 26}" width="{bw + 52}" height="{bh + 52}" rx="14" fill="url(#messing)"/>')
    s.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="6" fill="#0a0a0a"/>')
    s.append(t(bx + 40, by + 66, "BBB-BGLD · KNAPPHEITSTAFEL", 38, MESSING_H, fett=True, abstand=5))
    s.append(t(bx + bw - 40, by + 66, "STAND: GESTERN ABEND", 30, CREME, "end", abstand=4))
    s.append(f'<path d="M{bx + 30} {by + 92}H{bx + bw - 30}" stroke="{MESSING_D}" stroke-width="2"/>')

    kb, kh, kg = 44, 66, 6
    x0 = bx + 40
    kopf = ["STELLE", "ANGEBOT", "HINWEIS", "TREND"]
    sx = x0
    starts = []
    for n, k in zip(SPALTEN, kopf):
        starts.append(sx)
        s.append(t(sx, by + 136, k, 24, MESSING, abstand=4))
        sx += n * (kb + kg) + 34
    y = by + 160
    for zeile in ZEILEN:
        if zeile is None:
            werte = ["".join(rnd.choice("ABCDEFGHKLMNPRSTUWZ0123456789") for _ in range(n)) for n in SPALTEN]
        else:
            werte = list(zeile)
        for sp, (n, wert) in enumerate(zip(SPALTEN, werte)):
            for i in range(n):
                z = wert[i] if i < len(wert) else " "
                farbe = CREME
                if zeile and zeile[2] == "UNVERNÜNFTIG" and sp == 2:
                    farbe = ROT
                if sp == 3 and z.strip():
                    farbe = "#f2c12e"
                kippt = zeile is None and rnd.random() < 0.45
                if zeile is None and not kippt and rnd.random() < 0.6:
                    z = " "
                s.append(klappe(starts[sp] + i * (kb + kg), y, kb, kh, z, farbe, kippt))
        y += kh + 16
    s.append(f'<path d="M{bx + 30} {by + bh - 74}H{bx + bw - 30}" stroke="{MESSING_D}" stroke-width="2"/>')
    s.append(t(bx + bw / 2, by + bh - 28, "ZUGRIFF WIRD GEZÄHLT, NICHT GESCHÄTZT.", 30, MESSING_H, "middle", abstand=6))

    # Schalter: Messinggitter, Tresen, Lampen
    tresen = 1560
    n = 5
    breite = 560
    abst = (W - 2 * 380 - n * breite) / (n - 1)
    for i in range(n):
        gx = 380 + i * (breite + abst)
        s.append(f'<path d="M{gx} {tresen} V1430 Q{gx + breite / 2} 1360 {gx + breite} 1430 V{tresen}" fill="#08170f" fill-opacity="0.55" '
                 f'stroke="url(#messing)" stroke-width="8"/>')
        for k in range(1, 14):
            xx = gx + k * breite / 14
            oben = 1430 - 70 * (1 - ((xx - gx - breite / 2) / (breite / 2)) ** 2)
            s.append(f'<path d="M{xx:.0f} {oben + 6:.0f}V{tresen}" stroke="{MESSING}" stroke-width="3"/>')
        s.append(f'<rect x="{gx + breite / 2 - 34}" y="1352" width="68" height="40" rx="6" fill="url(#messing)"/>')
        s.append(t(gx + breite / 2, 1382, str(i + 1), 28, HOLZ_D, "middle", True, SERIF, 0))
    s.append(f'<rect x="0" y="{tresen}" width="{W}" height="22" fill="url(#messing)"/>')
    s.append(f'<rect x="0" y="{tresen + 22}" width="{W}" height="300" fill="url(#holz)"/>')
    for i in range(12):
        x = 40 + i * 320
        s.append(f'<rect x="{x}" y="{tresen + 60}" width="280" height="210" fill="none" stroke="{HOLZ_H}" stroke-width="5"/>')
        s.append(f'<rect x="{x + 18}" y="{tresen + 78}" width="244" height="174" fill="none" stroke="{HOLZ_D}" stroke-width="4"/>')
    for i in range(n):
        gx = 380 + i * (breite + abst)
        s.append(lampe(gx + breite / 2, tresen))

    # Schachbrett-Marmor in Perspektive
    boden0, fx = tresen + 322, W / 2
    vy = 900
    zeilen = 7
    ys = [boden0 + (H - boden0) * (k / zeilen) ** 1.35 for k in range(zeilen + 1)]
    spalten = range(-14, 15)

    def xpos(j, yy):
        unten_x = fx + j * 300
        return fx + (unten_x - fx) * (yy - vy) / (H - vy)

    for k in range(zeilen):
        for j in spalten:
            y1, y2 = ys[k], ys[k + 1]
            pts = [(xpos(j, y1), y1), (xpos(j + 1, y1), y1), (xpos(j + 1, y2), y2), (xpos(j, y2), y2)]
            farbe = "#141414" if (j + k) % 2 else "#bdb8ad"
            s.append(f'<polygon points="{" ".join(f"{a:.0f},{b:.0f}" for a, b in pts)}" fill="{farbe}"/>')
    s.append(f'<rect x="0" y="{boden0}" width="{W}" height="120" fill="url(#bodenschatten)"/>')

    return svg("".join(s), defs)
