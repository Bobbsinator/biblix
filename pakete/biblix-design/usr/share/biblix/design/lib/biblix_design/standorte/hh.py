"""Hierz und Habl: Referenzblatt der mobilen IT-Werkstatt (Masterbrief 2.3-2.5, Designbibel 17.7/17.9)."""

from ._hilfen import W, H, MONO, SANS, svg, lin, rad, t

GRUND, KARTE, KARTE_R = "#E9EAEC", "#F3F4F6", "#D1D5DB"
KONTUR = "#16181C"
LABEL = "#4B5563"
BLAU, BLAU_H, BLAU_D = "#1f5fbf", "#3b7be0", "#16458c"
GLAS = "#8FB3CC"
METALL = "#C9CDD2"
GELB = "#F2C12E"


def beschriftung(x, y, zx, zy, text, anker="start"):
    """Hinweislinie vom Bauteil (zx, zy) zur Beschriftung (x, y)."""
    return (f'<path d="M{zx} {zy}L{x} {y - 10}" stroke="{LABEL}" stroke-width="2"/><circle cx="{zx}" cy="{zy}" r="6" fill="{KONTUR}"/>'
            + t(x + (8 if anker == "start" else -8), y, text, 24, LABEL, anker, True, SANS, 3))


def crimpzange(cx, cy, s=1.0):
    return (f'<g transform="translate({cx} {cy}) scale({s}) rotate(-30)">'
            f'<path d="M-140 -16 L0 -10 L0 10 L-140 22 Q-160 3 -140 -16Z" fill="{BLAU}" stroke="{KONTUR}" stroke-width="4"/>'
            f'<path d="M-140 30 L0 16 L4 34 L-130 70 Q-156 56 -140 30Z" fill="{BLAU}" stroke="{KONTUR}" stroke-width="4"/>'
            f'<path d="M0 -14 L60 -22 L80 -4 L60 6 L0 10Z" fill="{METALL}" stroke="{KONTUR}" stroke-width="4"/>'
            f'<path d="M0 12 L60 10 L74 26 L4 34Z" fill="{METALL}" stroke="{KONTUR}" stroke-width="4"/>'
            f'<circle cx="6" cy="10" r="9" fill="{KONTUR}"/></g>')


def hh_werkstatt(p=None):
    defs = lin("blau", [(0, BLAU_H, 1), (1, BLAU_D, 1)])
    defs += lin("weiss", [(0, "#ffffff", 1), (1, "#e4e7eb", 1)])
    defs += lin("glas", [(0, "#b7d0e2", 1), (1, GLAS, 1)])
    defs += rad("projektion", [(0, "#3b7be0", 0.75), (1, "#3b7be0", 0)])
    defs += lin("anthrazit", [(0, "#4A4E55", 1), (1, "#2B2E33", 1)])
    s = [f'<rect width="{W}" height="{H}" fill="{GRUND}"/>']

    # Titel
    s.append(t(120, 190, "H&amp;H · MOBILE IT-WERKSTATT", 84, KONTUR, fett=True, schrift=SANS, abstand=2))
    s.append(t(124, 252, "HIERZ UND HABL · NETZWERKE · IT-INFRASTRUKTUR · SERVICE VOR ORT", 28, LABEL, abstand=5))

    # Hauptkarte
    s.append(f'<rect x="100" y="320" width="2580" height="1640" rx="12" fill="{KARTE}" stroke="{KARTE_R}" stroke-width="2"/>')
    boden = 1600
    s.append(f'<ellipse cx="1320" cy="{boden + 14}" rx="1160" ry="44" fill="#D3D5D9"/>')
    s.append(f'<ellipse cx="1300" cy="{boden + 30}" rx="560" ry="70" fill="url(#projektion)"/>')
    s.append(t(1300, boden + 48, "H&amp;H", 64, "#ffffff", "middle", True, SANS, 6, 'fill-opacity="0.85"'))

    # Wagenkoerper: oben weiss, unten blau; Front links
    x0, x1, dach, trenn, unten = 320, 2340, 760, 1180, 1500
    koerper = (f"M{x0 + 40} {unten} L{x0} {unten - 40} L{x0} {trenn + 40} Q{x0} {trenn - 60} {x0 + 60} {trenn - 140} "
               f"L{x0 + 260} {dach + 40} Q{x0 + 300} {dach} {x0 + 380} {dach} L{x1 - 80} {dach} Q{x1} {dach} {x1} {dach + 80} "
               f"L{x1} {unten - 20} L{x1 - 30} {unten} Z")
    s.append(f'<clipPath id="wagen"><path d="{koerper}"/></clipPath>')
    s.append(f'<path d="{koerper}" fill="url(#weiss)"/>')
    s.append(f'<rect x="{x0 - 10}" y="{trenn}" width="{x1 - x0 + 20}" height="{unten - trenn + 10}" fill="url(#blau)" clip-path="url(#wagen)"/>')
    s.append(f'<path d="M{x0} {trenn + 30} Q{x0 + 160} {trenn - 40} {x0 + 360} {trenn}" fill="url(#blau)" clip-path="url(#wagen)"/>')

    # Werkstatt im Heck: aufgeschnitten (oberhalb der Raeder)
    wx0, wx1, wy0, wy1 = 1300, x1 - 40, dach + 50, 1300
    s.append(f'<rect x="{wx0}" y="{wy0}" width="{wx1 - wx0}" height="{wy1 - wy0}" rx="10" fill="#f7f8fa" stroke="{KONTUR}" stroke-width="3" stroke-dasharray="16 10"/>')
    # Netzwerkrack
    s.append(f'<rect x="{wx0 + 30}" y="{wy0 + 30}" width="220" height="{wy1 - wy0 - 60}" rx="8" fill="url(#anthrazit)" stroke="{KONTUR}" stroke-width="4"/>')
    for k in range(7):
        yy = wy0 + 48 + k * 60
        s.append(f'<rect x="{wx0 + 46}" y="{yy}" width="188" height="44" rx="4" fill="#3a3e45" stroke="#1d1f23" stroke-width="2"/>')
        for j in range(6):
            farbe = "#4be38b" if (j + k) % 3 else GELB
            s.append(f'<rect x="{wx0 + 60 + j * 26}" y="{yy + 16}" width="16" height="10" rx="2" fill="{farbe}"/>')
    # Lochwand mit Werkzeug
    px0 = wx0 + 290
    s.append(f'<rect x="{px0}" y="{wy0 + 30}" width="{wx1 - px0 - 30}" height="170" rx="8" fill="#dfe3e8" stroke="{KONTUR}" stroke-width="3"/>')
    for i in range(int((wx1 - px0 - 50) / 30)):
        for j in range(5):
            s.append(f'<circle cx="{px0 + 20 + i * 30}" cy="{wy0 + 50 + j * 32}" r="3" fill="#b5bcc5"/>')
    s.append(crimpzange(px0 + 540, wy0 + 110, 0.6))
    s.append(f'<path d="M{px0 + 620} {wy0 + 60}v110M{px0 + 600} {wy0 + 60}h40" stroke="{KONTUR}" stroke-width="10" stroke-linecap="round"/>')
    s.append(f'<path d="M{px0 + 680} {wy0 + 64}v100m-18 -100h36" stroke="{BLAU}" stroke-width="12" stroke-linecap="round"/>')
    # Werkbank mit Messgeraet und Laptop
    by = wy0 + 240
    s.append(f'<rect x="{px0}" y="{by}" width="{wx1 - px0 - 30}" height="22" fill="#b9773e" stroke="{KONTUR}" stroke-width="3"/>')
    s.append(f'<rect x="{px0 + 30}" y="{by - 90}" width="150" height="90" rx="8" fill="{GELB}" stroke="{KONTUR}" stroke-width="4"/>')
    s.append(f'<rect x="{px0 + 46}" y="{by - 76}" width="90" height="44" rx="4" fill="#20302a"/><path d="M{px0 + 52} {by - 52}l16 -10l14 18l18 -22l18 14" fill="none" stroke="#4be38b" stroke-width="3"/>')
    s.append(f'<path d="M{px0 + 240} {by}l26 -96h170l-26 96z" fill="url(#anthrazit)" stroke="{KONTUR}" stroke-width="4"/>')
    s.append(f'<path d="M{px0 + 220} {by}h240" stroke="{KONTUR}" stroke-width="8" stroke-linecap="round"/>')
    # Unter der Bank: Kabeltrommeln und Schubladen
    for k, farbe in enumerate(("#1d9a4a", BLAU)):
        cx_ = px0 + 70 + k * 140
        cy_ = wy1 - 85
        s.append(f'<circle cx="{cx_}" cy="{cy_}" r="62" fill="{farbe}" stroke="{KONTUR}" stroke-width="4"/>')
        s.append(f'<circle cx="{cx_}" cy="{cy_}" r="22" fill="{METALL}" stroke="{KONTUR}" stroke-width="4"/>')
        for r in (34, 46, 56):
            s.append(f'<circle cx="{cx_}" cy="{cy_}" r="{r}" fill="none" stroke="#000" stroke-opacity="0.18" stroke-width="2"/>')
    dx0 = px0 + 300
    for k in range(3):
        yy = by + 40 + k * 60
        s.append(f'<rect x="{dx0}" y="{yy}" width="{wx1 - dx0 - 30}" height="52" rx="6" fill="{BLAU}" stroke="{KONTUR}" stroke-width="3"/>')
        s.append(f'<rect x="{dx0 + (wx1 - dx0 - 30) / 2 - 40}" y="{yy + 20}" width="80" height="10" rx="5" fill="{METALL}"/>')

    # Kabine: Fenster und zwei Sitze
    s.append(f'<path d="M{x0 + 90} {trenn - 150} L{x0 + 270} {dach + 70} Q{x0 + 300} {dach + 50} {x0 + 360} {dach + 50} L1240 {dach + 50} '
             f'L1240 {trenn - 60} L{x0 + 60} {trenn - 60} Z" fill="url(#glas)" stroke="{KONTUR}" stroke-width="4"/>')
    s.append(f'<path d="M{x0 + 420} {dach + 70}l120 0" stroke="#fff" stroke-width="10" stroke-linecap="round" stroke-opacity="0.7"/>')
    for sx_ in (760, 1020):
        s.append(f'<path d="M{sx_} {trenn - 64} V{dach + 160} q0 -40 40 -40 h30 q30 0 30 40 V{trenn - 64}" fill="#2b2e33" stroke="{KONTUR}" stroke-width="3"/>')
    s.append(f'<path d="M680 {trenn - 120} a50 50 0 1 1 0.1 0" fill="none" stroke="{KONTUR}" stroke-width="10"/>')
    s.append(f'<path d="M1270 {dach + 40}V{unten - 30}" stroke="{KONTUR}" stroke-width="3"/>')

    # Beschriftung auf dem Blau
    s.append(t(820, trenn + 150, "H&amp;H", 120, "#ffffff", fett=True, schrift=SANS, abstand=4))
    s.append(t(824, trenn + 210, "Hierz und Habl", 40, "#ffffff", schrift=SANS, abstand=2))
    s.append(t(824, trenn + 260, "Mobile IT-Werkstatt", 30, "#dbe7ff", schrift=SANS, abstand=2))
    # Raeder
    for rx_ in (640, 2000):
        s.append(f'<path d="M{rx_ - 200} {unten} a200 200 0 0 1 400 0" fill="{KARTE}" stroke="{KONTUR}" stroke-width="4"/>')
        s.append(f'<circle cx="{rx_}" cy="{boden - 150}" r="150" fill="#1f2226" stroke="{KONTUR}" stroke-width="4"/>')
        s.append(f'<circle cx="{rx_}" cy="{boden - 150}" r="88" fill="{METALL}" stroke="{KONTUR}" stroke-width="4"/>')
        for k in range(5):
            s.append(f'<path d="M{rx_} {boden - 150}l0 -80" stroke="#8b9097" stroke-width="12" transform="rotate({k * 72} {rx_} {boden - 150})"/>')
        s.append(f'<circle cx="{rx_}" cy="{boden - 150}" r="20" fill="{KONTUR}"/>')

    # STRG-V-Dachstation mit Drohne, Antennen, Arbeitsscheinwerfer
    s.append(f'<rect x="900" y="{dach - 90}" width="820" height="90" rx="14" fill="url(#weiss)" stroke="{KONTUR}" stroke-width="4"/>')
    s.append(f'<path d="M940 {dach - 45}h740" stroke="{METALL}" stroke-width="6"/>')
    s.append(f'<rect x="1150" y="{dach - 110}" width="320" height="20" rx="6" fill="{METALL}" stroke="{KONTUR}" stroke-width="3"/>')
    dx_, dy_ = 1310, dach - 190
    s.append(f'<path d="M{dx_ - 110} {dy_}H{dx_ + 110}M{dx_} {dy_ - 4}V{dy_ + 40}" stroke="{KONTUR}" stroke-width="8" stroke-linecap="round"/>')
    for ox in (-110, 110):
        s.append(f'<ellipse cx="{dx_ + ox}" cy="{dy_ - 14}" rx="70" ry="10" fill="{GLAS}" stroke="{KONTUR}" stroke-width="3"/>')
    s.append(f'<rect x="{dx_ - 50}" y="{dy_ - 6}" width="100" height="44" rx="12" fill="{BLAU}" stroke="{KONTUR}" stroke-width="4"/>')
    s.append(f'<rect x="{dx_ - 30}" y="{dy_ + 40}" width="60" height="40" rx="6" fill="{GELB}" stroke="{KONTUR}" stroke-width="3"/>')
    for ax in (1860, 2010):
        s.append(f'<path d="M{ax} {dach}V{dach - (180 if ax == 1860 else 120)}" stroke="{KONTUR}" stroke-width="6"/>')
        s.append(f'<circle cx="{ax}" cy="{dach - (180 if ax == 1860 else 120)}" r="9" fill="{KONTUR}"/>')
    for lx in (760, 2200):
        s.append(f'<rect x="{lx}" y="{dach - 40}" width="80" height="40" rx="6" fill="{KONTUR}"/><rect x="{lx + 8}" y="{dach - 34}" width="64" height="20" rx="4" fill="#fff6c8"/>')

    # Beschriftungen
    s.append(beschriftung(1000, 430, 1310, dach - 200, "STRG-V-DACHSTATION · DROHNE"))
    s.append(beschriftung(1900, 470, 1860, dach - 180, "ANTENNEN"))
    s.append(beschriftung(480, 470, 800, dach - 30, "LED-ARBEITSSCHEINWERFER", "end"))
    s.append(beschriftung(1420, 1720, wx0 + 140, wy1 - 60, "NETZWERKRACK"))
    s.append(beschriftung(2400, 760, px0 + 540, wy0 + 100, "CRIMPZANGEN"))
    s.append(beschriftung(2400, 920, px0 + 100, by - 50, "MESSGERÄTE"))
    s.append(beschriftung(2400, 1080, dx0 + 250, by + 100, "ERSATZTEILE"))
    s.append(beschriftung(1700, 1840, px0 + 70, wy1 - 60, "KABELTROMMELN"))
    s.append(beschriftung(600, 640, 790, trenn - 200, "FAHREN BEIDE,", "end"))
    s.append(t(592, 676, "FÄHRT SEBASTIAN.", 24, LABEL, "end", True, SANS, 3))
    s.append(t(140, 1920, "SEITENANSICHT · HECK AUFGESCHNITTEN", 22, LABEL, abstand=4))

    # Detailkarten rechts
    kx = 2720
    s.append(f'<rect x="{kx}" y="320" width="1020" height="520" rx="12" fill="{KARTE}" stroke="{KARTE_R}" stroke-width="2"/>')
    s.append(t(kx + 40, 390, "CRIMPZANGENPFLICHT", 40, KONTUR, fett=True, schrift=SANS, abstand=2))
    s.append(t(kx + 40, 440, "NACH JEDEM TICKET: EINE CRIMPZANGE.", 24, LABEL, abstand=3))
    s.append(t(kx + 40, 476, "AUCH WENN SCHON EINE BESTELLT WAR.", 24, LABEL, abstand=3))
    s.append(crimpzange(kx + 720, 640, 1.4))
    s.append(f'<ellipse cx="{kx + 680}" cy="{790}" rx="220" ry="16" fill="#D3D5D9"/>')
    s.append(t(kx + 40, 720, "„DIE IST SCHON", 40, BLAU, fett=True, schrift=SANS, abstand=2))
    s.append(t(kx + 40, 772, "VERSTEUERT.“", 40, BLAU, fett=True, schrift=SANS, abstand=2))

    s.append(f'<rect x="{kx}" y="880" width="1020" height="420" rx="12" fill="{KARTE}" stroke="{KARTE_R}" stroke-width="2"/>')
    s.append(t(kx + 40, 950, "H&amp;H CARE", 40, KONTUR, fett=True, schrift=SANS, abstand=2))
    s.append(t(kx + 40, 1000, "ANFAHRT · DIAGNOSE · ARBEIT · ERSATZTEILE", 24, LABEL, abstand=3))
    s.append(t(kx + 40, 1110, "„Der Defekt ist deiner.", 50, KONTUR, schrift=SANS, abstand=1))
    s.append(t(kx + 40, 1180, "Die Rechnung nicht.“", 50, BLAU, fett=True, schrift=SANS, abstand=1))
    s.append(t(kx + 40, 1250, "RECHNUNG KOSTET EXTRA.", 22, LABEL, abstand=4))

    s.append(f'<rect x="{kx}" y="1340" width="1020" height="620" rx="12" fill="{KARTE}" stroke="{KARTE_R}" stroke-width="2"/>')
    s.append(t(kx + 40, 1410, "KENNZEICHEN", 40, KONTUR, fett=True, schrift=SANS, abstand=2))
    s.append(t(kx + 40, 1460, "BURGENLAND", 24, LABEL, abstand=3))
    s.append(f'<rect x="{kx + 80}" y="1530" width="860" height="200" rx="18" fill="#fff" stroke="{KONTUR}" stroke-width="6"/>')
    s.append(f'<rect x="{kx + 100}" y="1546" width="820" height="14" fill="#d7263d"/><rect x="{kx + 100}" y="1700" width="820" height="14" fill="#d7263d"/>')
    s.append(t(kx + 510, 1676, "E 1024 E", 112, KONTUR, "middle", True, MONO, 6))
    s.append(t(kx + 40, 1820, "„BENJAMIN FINDET EINEN WEG.", 30, KONTUR, schrift=SANS, abstand=2))
    s.append(t(kx + 40, 1866, "SEBASTIAN SETZT IHN UM.“", 30, BLAU, fett=True, schrift=SANS, abstand=2))

    s.append(t(120, 2030, "Fiktionales Design · DARSTELLUNG", 22, LABEL, abstand=3))
    return svg("".join(s), defs)
