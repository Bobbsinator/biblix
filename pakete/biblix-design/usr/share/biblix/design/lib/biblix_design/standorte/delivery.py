"""Bibi Delivery: Typentafel der Würfellogistik (Masterbrief 9.3)."""

from ._hilfen import W, H, MONO, SANS, svg, lin, rad, t

NAVY, NAVY2 = "#0a1f66", "#06144a"
KARTE, KARTE_R = "#112b86", "#2b50c8"
BLAU, BLAU_H = "#1f5fff", "#5b8cff"
GELB, GELB_D = "#ffd400", "#d9a800"
WEISS = "#f2f5ff"
LEISE = "#9fb4f2"
ANTHRAZIT = "#2b2e33"

WUERFEL = [
    ("BDW-F", "FRONTWÜRFEL", "Frontversorgung", "„Frontlinie? Lieferung läuft.“", "f"),
    ("BDW-M", "MEDWÜRFEL", "Medizinische Versorgung, begrenzter Rücktransport", "", "m"),
    ("BDW-T", "TECHNIKWÜRFEL", "Werkzeug, Kabel, Hardware, Funk, Akkus", "", "t"),
    ("BDW-K", "KOMMANDOWÜRFEL", "Mobile Kommunikation", "", "k"),
    ("BDW-E", "ENERGIEWÜRFEL", "Fahrende Steckdose", "„Wie viel Strom?“ – „Ja.“", "e"),
    ("BDW-A", "MUNITIONSWÜRFEL", "Geschützter Materialtransport", "", "a"),
    ("BDW-MAC", "MACWÜRFEL", "Frontverpflegung", "", "mac"),
    ("BDW-B", "BASTIONSWÜRFEL", "Schwerste Variante", "„Schwer. Langsam. Gepanzert. Pünktlich.“", "b"),
]
STATUS = ["ANGENOMMEN", "GESUCHT", "GEFUNDEN", "UNTERWEGS", "FAST DA", "STEHT VOR DIR"]


def rad_(cx, cy, r):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#15171b"/><circle cx="{cx}" cy="{cy}" r="{r * 0.55}" fill="#3a3e46"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.18}" fill="{GELB}"/>')


def wuerfel(cx, boden, art):
    """Seitenansicht eines Delivery-W-Wuerfels (kurz, hoch, Kabine vorne rechts)."""
    gross = art == "b"
    b, h = (330, 300) if gross else (290, 270)
    x0, y0 = cx - b / 2, boden - 46 - h
    koerper, streifen, rand = GELB, BLAU, "#0b1a4d"
    if art == "m":
        koerper, streifen = "#f4f6fb", BLAU
    elif art == "a":
        koerper, streifen = "#3a3f47", GELB
    elif art == "mac":
        koerper, streifen = "#d62a1e", GELB
    elif art == "b":
        koerper, streifen = "#4a4f57", GELB
    o = [f'<ellipse cx="{cx}" cy="{boden + 6}" rx="{b * 0.62}" ry="16" fill="#000" fill-opacity="0.3"/>']
    # Aufbauten hinter dem Koerper
    if art == "k":
        o.append(f'<path d="M{x0 + 50} {y0}V{y0 - 92}M{x0 + 90} {y0}V{y0 - 64}" stroke="{WEISS}" stroke-width="5"/>')
        o.append(f'<path d="M{x0 + 150} {y0 - 6} q50 -90 110 -40" fill="{WEISS}" stroke="{rand}" stroke-width="4"/>')
        o.append(f'<path d="M{x0 + 205} {y0 - 40}l-30 30" stroke="{rand}" stroke-width="4"/>')
    if art == "f":
        o.append(f'<rect x="{x0 + 90}" y="{y0 - 40}" width="80" height="40" rx="6" fill="{ANTHRAZIT}"/>')
        o.append(f'<rect x="{x0 + 110}" y="{y0 - 78}" width="110" height="46" rx="10" fill="{ANTHRAZIT}"/>')
        for k in range(4):
            o.append(f'<rect x="{x0 + 214}" y="{y0 - 72 + k * 10}" width="210" height="6" rx="3" fill="#565b64"/>')
        o.append(f'<rect x="{x0 + 410}" y="{y0 - 76}" width="22" height="44" rx="4" fill="{ANTHRAZIT}"/>')
    # Koerper
    o.append(f'<rect x="{x0}" y="{y0}" width="{b}" height="{h}" rx="22" fill="{koerper}" stroke="{rand}" stroke-width="6"/>')
    # Kabinenfenster vorne
    o.append(f'<path d="M{x0 + b - 110} {y0 + 30}h80q14 0 14 14v66h-94z" fill="#7fb0ff" stroke="{rand}" stroke-width="5"/>')
    o.append(f'<path d="M{x0 + b - 92} {y0 + 44}l30 0" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-opacity="0.8"/>')
    # Streifen
    o.append(f'<rect x="{x0 + 4}" y="{y0 + h - 96}" width="{b - 8}" height="30" fill="{streifen}"/>')
    # Ladetuer / Box
    o.append(f'<rect x="{x0 + 26}" y="{y0 + 30}" width="{b - 160}" height="{h - 150}" rx="10" fill="none" stroke="{rand}" stroke-width="4"/>')
    # Nieten
    for k in range(6):
        o.append(f'<circle cx="{x0 + 22 + k * (b - 44) / 5}" cy="{y0 + h - 30}" r="5" fill="{rand}"/>')
    # Kennzeichnung je Art
    mx, my = x0 + 26 + (b - 160) / 2, y0 + 30 + (h - 150) / 2
    if art in ("f", "t", "k", "a", "b"):
        o.append(f'<path d="M{mx - 40} {my}h60l-18 -18M{mx + 20} {my}l-18 18" fill="none" stroke="{BLAU if art != "a" and art != "b" else GELB}" '
                 f'stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>')
    if art == "m":
        o.append(f'<path d="M{mx} {my - 34}v68M{mx - 34} {my}h68" stroke="{BLAU}" stroke-width="20"/>')
    if art == "e":
        o.append(f'<path d="M{mx + 8} {my - 46}l-34 52h26l-10 42l38-58h-26z" fill="{BLAU}"/>')
        o.append(f'<circle cx="{x0 + b - 60}" cy="{y0 + h - 140}" r="22" fill="{rand}"/>')
        o.append(f'<path d="M{x0 + b - 68} {y0 + h - 146}v12M{x0 + b - 52} {y0 + h - 146}v12" stroke="{GELB}" stroke-width="5"/>')
        o.append(f'<path d="M{x0} {y0 + h - 60} q-60 10 -50 -50 q10 -50 -40 -60" fill="none" stroke="{rand}" stroke-width="10" stroke-linecap="round"/>')
    if art == "mac":
        o.append(f'<path d="M{mx - 40} {my - 6} q40 44 80 0" fill="none" stroke="{GELB}" stroke-width="14" stroke-linecap="round"/>')
    if art == "t":
        o.append(f'<circle cx="{x0 - 26}" cy="{y0 + 120}" r="44" fill="{rand}"/><circle cx="{x0 - 26}" cy="{y0 + 120}" r="30" fill="#ff8a1f"/>'
                 f'<circle cx="{x0 - 26}" cy="{y0 + 120}" r="10" fill="{rand}"/>')
    if art in ("a", "b"):
        for k in range(3):
            o.append(f'<path d="M{x0 + 10} {y0 + 140 + k * 26}H{x0 + b - 10}" stroke="#2a2d33" stroke-width="4"/>')
    if art == "b":
        o.append(f'<rect x="{x0 - 16}" y="{y0 + h - 70}" width="{b + 32}" height="44" rx="10" fill="#33373e" stroke="{rand}" stroke-width="4"/>')
        o.append(f'<rect x="{x0 + 40}" y="{y0 - 30}" width="{b - 80}" height="34" rx="8" fill="#33373e" stroke="{rand}" stroke-width="4"/>')
    # Raeder
    r = 58 if gross else 52
    o.append(rad_(x0 + 70, boden - r + 8, r))
    o.append(rad_(x0 + b - 70, boden - r + 8, r))
    return "".join(o)


def delivery_typentafel(p=None):
    defs = lin("bg", [(0, NAVY, 1), (1, NAVY2, 1)])
    defs += lin("karte", [(0, "#14339a", 1), (1, KARTE, 1)])
    defs += rad("buehne", [(0, BLAU_H, 0.35), (1, BLAU_H, 0)])
    s = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']
    for x in range(0, W, 80):
        s.append(f'<path d="M{x} 0V{H}" stroke="#1a3488" stroke-width="1" stroke-opacity="0.5"/>')
    for y in range(0, H, 80):
        s.append(f'<path d="M0 {y}H{W}" stroke="#1a3488" stroke-width="1" stroke-opacity="0.5"/>')

    # Titel
    s.append(t(120, 210, "DELIVERY W", 132, GELB, fett=True, schrift=SANS, abstand=6))
    s.append(t(126, 284, "WÜRFELLOGISTIK · TYPENTAFEL · BIBI DELIVERY", 38, WEISS, abstand=8))

    # Statuskette
    sx0, sx1, sy = 1900, 3560, 200
    s.append(f'<path d="M{sx0} {sy}H{sx1}" stroke="{KARTE_R}" stroke-width="10" stroke-linecap="round"/>')
    jetzt = 4
    schritt = (sx1 - sx0) / (len(STATUS) - 1)
    s.append(f'<path d="M{sx0} {sy}H{sx0 + jetzt * schritt}" stroke="{GELB}" stroke-width="6"/>')
    for i, name in enumerate(STATUS):
        x = sx0 + i * schritt
        if i < jetzt:
            s.append(f'<circle cx="{x}" cy="{sy}" r="20" fill="{GELB}"/>')
        elif i == jetzt:
            s.append(f'<circle cx="{x}" cy="{sy}" r="42" fill="{GELB}" fill-opacity="0.18"/><circle cx="{x}" cy="{sy}" r="26" fill="{GELB}"/>'
                     f'<path d="M{x - 10} {sy}h18l-7-7M{x + 8} {sy}l-7 7" stroke="{NAVY}" stroke-width="5" fill="none" stroke-linecap="round"/>')
        else:
            s.append(f'<circle cx="{x}" cy="{sy}" r="20" fill="{NAVY}" stroke="{KARTE_R}" stroke-width="6"/>')
        s.append(t(x, sy + 84, name, 26, GELB if i == jetzt else (WEISS if i < jetzt else LEISE), "middle", i == jetzt, abstand=3))

    # Karten
    gx0, gy0, gap = 120, 380, 40
    kw = (W - 2 * gx0 - 3 * gap) / 4
    kh = 740
    for i, (code, name, rolle, zitat, art) in enumerate(WUERFEL):
        x = gx0 + (i % 4) * (kw + gap)
        y = gy0 + (i // 4) * (kh + gap)
        s.append(f'<rect x="{x}" y="{y}" width="{kw}" height="{kh}" rx="28" fill="url(#karte)" stroke="{KARTE_R}" stroke-width="3"/>')
        s.append(f'<circle cx="{x + kw / 2}" cy="{y + 300}" r="300" fill="url(#buehne)"/>')
        s.append(f'<path d="M{x + 60} {y + 500}H{x + kw - 60}" stroke="{KARTE_R}" stroke-width="4" stroke-dasharray="18 12"/>')
        wx, wy = x + kw / 2 - (24 if art == "f" else 0), y + 500
        s.append(f'<g transform="translate({wx:.0f} {wy}) scale(1.15) translate({-wx:.0f} {-wy})">{wuerfel(wx, wy, art)}</g>')
        s.append(f'<rect x="{x + 40}" y="{y + 36}" width="{len(code) * 25 + 40}" height="56" rx="28" fill="{GELB}"/>')
        s.append(t(x + 60, y + 76, code, 34, NAVY, fett=True, abstand=3))
        s.append(t(x + 44, y + 596, name, 50, WEISS, fett=True, schrift=SANS, abstand=3))
        s.append(t(x + 46, y + 646, rolle, 28 if len(rolle) < 34 else 23, LEISE, schrift=SANS, abstand=1))
        if zitat:
            s.append(t(x + 46, y + 704, zitat, 30 if len(zitat) < 32 else 25, GELB, schrift=SANS, abstand=1))

    # Lieferkette
    s.append(t(W / 2, 2000, "BURGENLAND / BBN / BIG BIBI AIR  →  DEPOTS  →  DELIVERY W  →  WÜRFEL  →  EINHEIT", 36,
               WEISS, "middle", True, MONO, 5))
    return svg("".join(s), defs)
