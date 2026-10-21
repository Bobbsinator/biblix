"""Biblix Design: Logos und Grundformen als SVG, in den Farben der Palette."""

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{w}" height="{h}">{inhalt}</svg>'

SECHSECK = "10,1 18,5.5 18,14.5 10,19 2,14.5 2,5.5"


def svg(inhalt, vb="0 0 120 120", w=120, h=120):
    return SVG.format(vb=vb, w=w, h=h, inhalt=inhalt)


# ---------------------------------------------------------------- Biblix-Logos

def prompt_b_form(vorne, akzent, strich=7, cursor=True):
    """Das Prompt-B ohne Hintergrund (120er Raster)."""
    s = (f'<path d="M26 44 L42 60 L26 76" fill="none" stroke="{akzent}" stroke-width="{strich}" '
         f'stroke-linecap="round" stroke-linejoin="round"/>'
         f'<path d="M54 34 H74 a13 13 0 0 1 0 26 H54 Z M54 60 H78 a14 14 0 0 1 0 28 H54 Z" fill="none" '
         f'stroke="{vorne}" stroke-width="{strich}" stroke-linejoin="round"/>')
    if cursor:
        s += f'<rect x="54" y="94" width="34" height="6" rx="2" fill="{akzent}"/>'
    return s


def prompt_b(p, kachel=True, klein=False):
    """Hauptlogo: > + B + Cursor auf runder Kachel."""
    strich = 9 if klein else 7
    grund = f'<rect width="120" height="120" rx="26" fill="{p["karte"] if p["dunkel"] else p["text"]}"/>' if kachel else ""
    vorne = p["text"] if p["dunkel"] or not kachel else p["karte"]
    return svg(grund + prompt_b_form(vorne, p["akzent"], strich, cursor=not klein))


def schrauben_b(p, rand=None, fuellung=None, strich=6):
    rand = rand or p["akzent"]
    fuellung = fuellung or p["karte"]
    return svg(f'<polygon points="60,8 105,34 105,86 60,112 15,86 15,34" fill="{fuellung}" stroke="{rand}" '
               f'stroke-width="{strich}" stroke-linejoin="round"/>'
               f'<path d="M46 36 H64 a11 11 0 0 1 0 22 H46 Z M46 58 H67 a12 12 0 0 1 0 24 H46 Z" fill="none" '
               f'stroke="{p["text"]}" stroke-width="7" stroke-linejoin="round"/>')


SCHICHTEN = [  # x, y, Breite (B aus Balken), erste ist der Stamm
    (30, 26, 12, 68),
]
BALKEN = [(46, 26, 30), (46, 42, 38), (46, 58, 44), (46, 74, 40)]


def schichten_b(p, sichtbar=4, kachel=True):
    """Schichten-B; sichtbar = wie viele Balken schon da sind (fuer Animationen)."""
    farben = [p["akzent"], heller_hex(p["akzent"]), p["akzent"], heller_hex(p["akzent"])]
    s = f'<rect width="120" height="120" rx="26" fill="{p["karte"]}"/>' if kachel else ""
    s += f'<rect x="30" y="26" width="12" height="68" rx="3" fill="{p["text"]}"/>'
    for i, (x, y, b) in enumerate(BALKEN[:sichtbar]):
        s += f'<rect x="{x}" y="{y}" width="{b}" height="12" rx="6" fill="{farben[i]}"/>'
    return svg(s)


def heller_hex(h):
    from .kern import heller
    return heller(h, 0.4)


def mutter(fuellung, rand, symbol=None, symbol_farbe="#ffffff", groesse=20, strich=1.6, drehung=0):
    """Sechskant-Mutter (Fensterknopf, Ladezeiger). symbol: minimieren|maximieren|wiederherstellen|schliessen|..."""
    zeichen = {
        "minimieren": '<path d="M6.5 10h7"/>',
        "maximieren": '<path d="M6.5 10h7M10 6.5v7"/>',
        "wiederherstellen": '<path d="M7 8.5h6v5h-6z"/>',
        "schliessen": '<path d="M7.3 7.3l5.4 5.4M12.7 7.3l-5.4 5.4"/>',
        "anheften": '<circle cx="10" cy="10" r="2"/>',
        "hilfe": '<path d="M8 8a2 2 0 1 1 2.5 2c-.5.2-.5.6-.5 1.2M10 13.5v.1"/>',
        "menue": '<path d="M7 8h6M7 10h6M7 12h6"/>',
        "abrollen": '<path d="M7 11l3-3 3 3"/>',
        "oben": '<path d="M7 9l3-3 3 3M7 13h6"/>',
        "unten": '<path d="M7 7h6M7 11l3 3 3-3"/>',
    }
    f = "none" if fuellung is None else fuellung
    s = (f'<g transform="rotate({drehung} 10 10)"><polygon points="{SECHSECK}" fill="{f}" stroke="{rand}" '
         f'stroke-width="{strich}" stroke-linejoin="round"/></g>')
    if symbol:
        s += (f'<g fill="none" stroke="{symbol_farbe}" stroke-width="1.8" stroke-linecap="round" '
              f'stroke-linejoin="round">{zeichen[symbol]}</g>')
    return SVG.format(vb="0 0 20 20", w=groesse, h=groesse, inhalt=s)


# ---------------------------------------------------------------- Firmenlogos (feste Firmenfarben)

def logo_bibi_tech():
    return svg('<rect width="120" height="120" rx="22" fill="#0f1a2e"/>'
               '<path d="M14 30h8M14 30v8M14 90h8M14 90v-8M106 90h-8M106 90v-8" stroke="#378ADD" stroke-width="2"/>'
               '<path d="M92 26 h14 v14 h-14 Z" fill="#FFD400"/>'
               '<text x="60" y="58" text-anchor="middle" font-family="DejaVu Sans Mono, monospace" font-weight="700" '
               'font-size="20" fill="#e8ecf2" letter-spacing="3">BIBI</text>'
               '<text x="60" y="82" text-anchor="middle" font-family="DejaVu Sans Mono, monospace" font-weight="700" '
               'font-size="20" fill="#378ADD" letter-spacing="3">TECH</text>')


def logo_bibi_budget_bank():
    return svg('<rect width="120" height="120" rx="22" fill="#163a29"/>'
               '<circle cx="60" cy="60" r="40" fill="none" stroke="#C9A227" stroke-width="4"/>'
               '<circle cx="60" cy="60" r="34" fill="none" stroke="#C9A227" stroke-width="1"/>'
               '<text x="60" y="72" text-anchor="middle" font-family="DejaVu Serif, serif" font-weight="700" '
               'font-size="30" fill="#C9A227" letter-spacing="1">BBB</text>'
               '<path d="M36 80h48" stroke="#C9A227" stroke-width="2"/>')


def logo_bibi_delivery():
    return svg('<rect width="120" height="120" rx="22" fill="#0047FF"/>'
               '<rect x="10" y="36" width="100" height="44" rx="22" fill="#0a1a3d"/>'
               '<g transform="skewX(-12)"><text x="58" y="70" text-anchor="middle" font-family="DejaVu Sans, sans-serif" '
               'font-weight="700" font-size="28" fill="#FFD000">BIBI</text></g>'
               '<path d="M80 58 H100 M92 50 L101 58 L92 66" fill="none" stroke="#FFD000" stroke-width="5" '
               'stroke-linecap="round" stroke-linejoin="round"/>'
               '<text x="60" y="98" text-anchor="middle" font-family="DejaVu Sans, sans-serif" font-weight="700" '
               'font-size="11" fill="#FFD000" letter-spacing="3">DELIVERY</text>')


def logo_bibi_mac():
    return svg('<rect width="120" height="120" rx="22" fill="#E63131"/>'
               '<text x="60" y="58" text-anchor="middle" font-family="DejaVu Sans, sans-serif" font-weight="700" '
               'font-size="30" fill="#FFE27A">bibi</text>'
               '<text x="60" y="86" text-anchor="middle" font-family="DejaVu Sans, sans-serif" font-weight="700" '
               'font-size="30" fill="#ffffff">mac</text>'
               '<path d="M30 94 q30 10 60 0" fill="none" stroke="#FFE27A" stroke-width="4" stroke-linecap="round"/>')


def logo_nassmacher():
    return svg('<rect width="120" height="120" rx="22" fill="#06323a"/>'
               '<path d="M30 20 V48 q0 22 22 30 L88 96" fill="none" stroke="#22D3E6" stroke-width="10" stroke-linecap="round"/>'
               '<path d="M52 20 V40 q0 18 18 26 L98 82" fill="none" stroke="#FFB020" stroke-width="10" stroke-linecap="round"/>'
               '<path d="M12 104 q10 -6 20 0 t20 0 t20 0 t20 0 t20 0" fill="none" stroke="#22D3E6" stroke-width="3"/>')


_PLEXX_P = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (2, 1), (1, 2)]
_PLEXX_L = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 4), (2, 4)]
_PLEXX_E = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (2, 0), (1, 2), (1, 4), (2, 4)]
_PLEXX_X = [(0, 0), (1, 1), (2, 2), (1, 3), (0, 4), (3, 1), (4, 0), (3, 3), (4, 4)]


def logo_bibiplexx():
    s = ['<rect width="120" height="120" rx="22" fill="#07070c"/>',
         '<path d="M12 26 H108 M12 74 H108" stroke="#7B2CBF" stroke-width="2"/>',
         '<path d="M12 26 L5 19 M108 26 L115 19 M12 74 L5 81 M108 74 L115 81" stroke="#FF4D9D" stroke-width="2"/>']

    def pixel(punkte, x0, farbe, schritt=4.2):
        for cx, cy in punkte:
            s.append(f'<rect x="{x0 + cx * schritt:.1f}" y="{36 + cy * schritt * 1.15:.1f}" width="3.6" height="3.6" fill="{farbe}"/>')

    pixel(_PLEXX_P, 14, "#FF4D9D")
    pixel(_PLEXX_L, 30, "#FF4D9D")
    pixel(_PLEXX_E, 46, "#FF4D9D")
    pixel(_PLEXX_X, 63, "#FF8A00")
    pixel(_PLEXX_X, 86, "#FF8A00")
    for i, x in enumerate([16, 30, 44, 58, 72, 86]):
        farbe = "#FF8A00" if i == 3 else "#1a1030"
        s.append(f'<rect x="{x + 1}" y="88" width="12" height="12" rx="3" fill="{farbe}" stroke="#7B2CBF" stroke-width="1"/>')
    s.append('<rect x="14" y="100" width="92" height="4" rx="2" fill="#1a1030"/>')
    return svg("".join(s))


FIRMENLOGOS = {
    "bibi-tech": logo_bibi_tech,
    "bibi-budget-bank": logo_bibi_budget_bank,
    "bibi-delivery": logo_bibi_delivery,
    "bibi-mac": logo_bibi_mac,
    "nassmacher": logo_nassmacher,
    "bibiplexx": logo_bibiplexx,
}
