"""Fensterrahmen (KWin Aurorae) mit Biblix-Knoepfen, aus Palette und Einstellungen erzeugt.

Aurorae zeichnet den Rahmen als 9-teiliges SVG (Ecken, Kanten, Mitte). Die Ecken muessen
so breit sein wie die Seitenkanten, deshalb ist der Seitenrand so breit wie der Eckradius.
Der Rand hat die Fensterfarbe und faellt dadurch kaum auf.
"""
from pathlib import Path

from .grafik import SECHSECK
from .kern import mischen, dunkler

SCHATTEN_OBEN, SCHATTEN_SEITE, SCHATTEN_UNTEN = 8, 14, 18
SYMBOLE = {
    "close": "schliessen", "minimize": "minimieren", "maximize": "maximieren", "restore": "wiederherstellen",
    "alldesktops": "anheften", "keepabove": "oben", "keepbelow": "unten", "shade": "abrollen", "help": "hilfe",
}

# Symbole im 20er Raster (Mitte 10,10)
ZEICHEN = {
    "minimieren": "M6.5 10h7",
    "maximieren": "M6.5 10h7M10 6.5v7",
    "wiederherstellen": "M7 8.5h6v5h-6zM8.5 8.5v-2h5v5h-0.5",
    "schliessen": "M7.3 7.3l5.4 5.4M12.7 7.3l-5.4 5.4",
    "anheften": "M10 6.5v4M7.5 10.5h5M10 10.5v3",
    "oben": "M7 9.5l3-3 3 3M7 13.5h6",
    "unten": "M7 6.5h6M7 10.5l3 3 3-3",
    "abrollen": "M7 11.5l3-3 3 3",
    "hilfe": "M8 8a2 2 0 1 1 2.5 2c-.5.2-.5.6-.5 1.2M10 13.6v.1",
}
# Terminal-Stil: Zeichen wie in Monoschrift
TERMINAL = {
    "minimieren": "M6 14h8",
    "maximieren": "M6.5 6.5h7v7h-7z",
    "wiederherstellen": "M6 8.5h6v6H6zM8.5 8.5V6h6v6H12",
    "schliessen": "M6.5 6.5l7 7M13.5 6.5l-7 7",
    "anheften": "M10 5.5v9M5.5 10h9",
    "oben": "M6 12l4-5 4 5",
    "unten": "M6 8l4 5 4-5",
    "abrollen": "M6 12l4-5 4 5",
    "hilfe": "M7.5 7.5a2.5 2.5 0 1 1 3 2.4V11.5M10 14v.1",
}


def _strich(d, farbe, breite=1.8):
    return (f'<path d="{d}" fill="none" stroke="{farbe}" stroke-width="{breite}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


class Knopf:
    """Zeichnet einen Knopf eines Stils in einem Zustand (26x26-Feld)."""

    def __init__(self, p, e, groesse):
        self.p, self.e, self.g = p, e, groesse
        farbig = e["titelleiste"] == "farbig"
        grundtext = p["auf_akzent"] if farbig else None
        self.ruhe = mischen(p["akzent"], grundtext, 0.35) if farbig else p["knopf_ruhe"]
        self.inaktiv = mischen(p["akzent"], grundtext, 0.2) if farbig else p["knopf_inaktiv"]
        self.hover_fuell = grundtext if farbig else p["akzent"]
        self.hover_zeichen = p["akzent"] if farbig else p["auf_akzent"]

    def zeichnen(self, art, symbol, zustand):
        p, g = self.p, self.g
        s = g / 20.0
        schliessen = symbol == "schliessen"
        fuell = p["gefahr"] if schliessen else self.hover_fuell
        zeichen_hover = "#ffffff" if schliessen else self.hover_zeichen
        if zustand == "pressed":
            fuell = dunkler(fuell, 0.2)
        ruhe = self.inaktiv if zustand in ("inactive", "deactivated") else self.ruhe
        aktiv = zustand in ("hover", "pressed")
        innen = []
        if art == "schrauben":
            if aktiv:
                innen.append(f'<g transform="rotate(30 10 10)"><polygon points="{SECHSECK}" fill="{fuell}" '
                             f'stroke="{fuell}" stroke-width="1.6" stroke-linejoin="round"/></g>')
                innen.append(_strich(ZEICHEN[symbol], zeichen_hover))
            else:
                innen.append(f'<polygon points="{SECHSECK}" fill="none" stroke="{ruhe}" stroke-width="1.6" '
                             f'stroke-linejoin="round"/>')
                innen.append(_strich(ZEICHEN[symbol], ruhe))
        elif art == "punkte":
            if aktiv:
                innen.append(f'<circle cx="10" cy="10" r="7" fill="{fuell}"/>')
                innen.append(_strich(ZEICHEN[symbol], zeichen_hover, 1.6))
            else:
                innen.append(f'<circle cx="10" cy="10" r="6" fill="{ruhe}"/>')
        elif art == "terminal":
            if aktiv and schliessen:
                innen.append(f'<rect x="2.5" y="2.5" width="15" height="15" rx="3" fill="{fuell}"/>')
                innen.append(_strich(TERMINAL[symbol], "#ffffff", 1.8))
            else:
                farbe = (p["akzent"] if aktiv else ruhe)
                innen.append(_strich(TERMINAL[symbol], farbe, 1.8))
        elif art == "klammern":
            farbe = (p["gefahr"] if schliessen else p["akzent"]) if aktiv else ruhe
            innen.append(_strich("M5 4.5H3.5v11H5M15 4.5h1.5v11H15", farbe, 1.5))
            innen.append(_strich(ZEICHEN[symbol], farbe, 1.6))
            if zustand == "hover":
                innen.append(f'<rect x="17.6" y="5" width="1.6" height="10" fill="{p["akzent"]}"/>')
        elif art == "kapsel":
            hinter = fuell if aktiv else mischen(p["karte"], ruhe, 0.15)
            innen.append(f'<rect x="1.5" y="4" width="17" height="12" rx="6" fill="{hinter}"/>')
            innen.append(_strich(ZEICHEN[symbol], zeichen_hover if aktiv else ruhe, 1.6))
        elif art == "balken":
            if aktiv:
                innen.append(f'<rect x="3" y="3" width="14" height="14" rx="4" fill="{fuell}"/>')
                innen.append(_strich(ZEICHEN[symbol], zeichen_hover, 1.6))
            else:
                innen.append(f'<rect x="3" y="8.2" width="14" height="3.6" rx="1.8" fill="{ruhe}"/>')
        rahmen = (f'<rect x="0" y="0" width="20" height="20" fill="#000000" fill-opacity="0.001"/>')
        return f'<g transform="scale({s})">{rahmen}{"".join(innen)}</g>'


def knopf_svg(p, e, symbol, groesse):
    k = Knopf(p, e, groesse)
    teile = []
    for i, zustand in enumerate(["active", "inactive", "hover", "pressed", "deactivated"]):
        x = i * (groesse + 4)
        teile.append(f'<g id="{zustand}-center" transform="translate({x} 0)">'
                     f'{k.zeichnen(e["knoepfe"], symbol, zustand)}</g>')
    breite = 5 * (groesse + 4)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{breite}" height="{groesse}" '
            f'viewBox="0 0 {breite} {groesse}">{"".join(teile)}</svg>')


# ---------------------------------------------------------------- Rahmen

def _schatten_lin(gid, x1, y1, x2, y2, staerke):
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
            f'<stop offset="0" stop-color="#000" stop-opacity="{staerke}"/>'
            f'<stop offset="0.45" stop-color="#000" stop-opacity="{staerke * 0.35:.3f}"/>'
            f'<stop offset="1" stop-color="#000" stop-opacity="0"/></linearGradient>')


def _schatten_rad(gid, cx, cy, r_innen, r_aussen, staerke):
    t = r_innen / r_aussen
    return (f'<radialGradient id="{gid}" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{cy}" r="{r_aussen}">'
            f'<stop offset="0" stop-color="#000" stop-opacity="{staerke}"/>'
            f'<stop offset="{t:.3f}" stop-color="#000" stop-opacity="{staerke}"/>'
            f'<stop offset="{t + (1 - t) * 0.45:.3f}" stop-color="#000" stop-opacity="{staerke * 0.35:.3f}"/>'
            f'<stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>')


def rahmen_svg(p, e, titel_h, r):
    """decoration.svg: aktive, inaktive und maximierte Teile."""
    PT, PS, PB, B = SCHATTEN_OBEN, SCHATTEN_SEITE, SCHATTEN_UNTEN, r
    T, L, U = PT + titel_h, PS + B, PB + B
    farbig = e["titelleiste"] == "farbig"
    teile, defs = [], []
    ox = 0  # Ablageposition im SVG

    def ablegen(gid, w, h, inhalt):
        nonlocal ox
        teile.append(f'<g id="{gid}" transform="translate({ox} 0)">'
                     f'<rect x="0" y="0" width="{w}" height="{h}" fill="#000" fill-opacity="0.001"/>{inhalt}</g>')
        ox += w + 10

    for zustand in ("aktiv", "inaktiv"):
        pre = "decoration" if zustand == "aktiv" else "decoration-inactive"
        st = 0.38 if zustand == "aktiv" else 0.2
        titel = (p["akzent"] if farbig else p["flaeche"]) if zustand == "aktiv" else p["flaeche"]
        rand = p["flaeche"]
        linie = (zustand == "aktiv" and e["titelleiste"] != "farbig")
        z = zustand
        defs += [
            _schatten_lin(f"so{z}", 0, PT, 0, 0, st),
            _schatten_lin(f"sl{z}", PS, 0, 0, 0, st),
            _schatten_lin(f"sr{z}", 0, 0, PS, 0, st),
            _schatten_lin(f"su{z}", 0, 0, 0, PB, st),
            _schatten_rad(f"ctl{z}", L, PT + r, r, r + PS, st),
            _schatten_rad(f"ctr{z}", 0, PT + r, r, r + PS, st),
            _schatten_rad(f"cbl{z}", L, 0, r, r + PB, st),
            _schatten_rad(f"cbr{z}", 0, 0, r, r + PB, st),
        ]
        ecke = r if e["ecken"] == "rund" else 0
        # Ecke oben links
        form = (f'M{PS} {T} V{PT + ecke} A{ecke} {ecke} 0 0 1 {PS + ecke} {PT} H{L} V{T} Z' if ecke
                else f'M{PS} {T} V{PT} H{L} V{T} Z')
        akz = (f'<path d="M{PS} {PT + ecke + 2} A{ecke} {ecke} 0 0 1 {PS + ecke} {PT} H{L}" fill="none" '
               f'stroke="{p["akzent"]}" stroke-width="2.4"/>' if linie and ecke
               else (f'<rect x="{PS}" y="{PT}" width="{B}" height="2" fill="{p["akzent"]}"/>' if linie else ""))
        ablegen(f"{pre}-topleft", L, T,
                f'<rect x="0" y="0" width="{L}" height="{T}" fill="url(#ctl{z})"/>'
                f'<path d="{form}" fill="{titel}"/>{akz}')
        ablegen(f"{pre}-top", 10, T,
                f'<rect x="0" y="0" width="10" height="{PT}" fill="url(#so{z})"/>'
                f'<rect x="0" y="{PT}" width="10" height="{titel_h}" fill="{titel}"/>'
                + (f'<rect x="0" y="{PT}" width="10" height="2" fill="{p["akzent"]}"/>' if linie else ""))
        form_r = (f'M0 {T} V{PT} H{B - ecke} A{ecke} {ecke} 0 0 1 {B} {PT + ecke} V{T} Z' if ecke
                  else f'M0 {T} V{PT} H{B} V{T} Z')
        akz_r = (f'<path d="M0 {PT} H{B - ecke} A{ecke} {ecke} 0 0 1 {B} {PT + ecke + 2}" fill="none" '
                 f'stroke="{p["akzent"]}" stroke-width="2.4"/>' if linie and ecke
                 else (f'<rect x="0" y="{PT}" width="{B}" height="2" fill="{p["akzent"]}"/>' if linie else ""))
        ablegen(f"{pre}-topright", L, T,
                f'<rect x="0" y="0" width="{L}" height="{T}" fill="url(#ctr{z})"/>'
                f'<path d="{form_r}" fill="{titel}"/>{akz_r}')
        ablegen(f"{pre}-left", L, 10,
                f'<rect x="0" y="0" width="{PS}" height="10" fill="url(#sl{z})"/>'
                f'<rect x="{PS}" y="0" width="{B}" height="10" fill="{rand}"/>')
        ablegen(f"{pre}-right", L, 10,
                f'<rect x="{B}" y="0" width="{PS}" height="10" fill="url(#sr{z})"/>'
                f'<rect x="0" y="0" width="{B}" height="10" fill="{rand}"/>')
        ablegen(f"{pre}-center", 10, 10, "")
        form_bl = (f'M{PS} 0 V{B - ecke} A{ecke} {ecke} 0 0 0 {PS + ecke} {B} H{L} V0 Z' if ecke
                   else f'M{PS} 0 V{B} H{L} V0 Z')
        ablegen(f"{pre}-bottomleft", L, U,
                f'<rect x="0" y="0" width="{L}" height="{U}" fill="url(#cbl{z})"/>'
                f'<path d="{form_bl}" fill="{rand}"/>')
        ablegen(f"{pre}-bottom", 10, U,
                f'<rect x="0" y="{B}" width="10" height="{PB}" fill="url(#su{z})"/>'
                f'<rect x="0" y="0" width="10" height="{B}" fill="{rand}"/>')
        form_br = (f'M0 0 V{B} H{B - ecke} A{ecke} {ecke} 0 0 0 {B} {B - ecke} V0 Z' if ecke
                   else f'M0 0 V{B} H{B} V0 Z')
        ablegen(f"{pre}-bottomright", L, U,
                f'<rect x="0" y="0" width="{L}" height="{U}" fill="url(#cbr{z})"/>'
                f'<path d="{form_br}" fill="{rand}"/>')

    # Maximiert: nur Titelzeile, keine Raender, kein Schatten
    for zustand in ("aktiv", "inaktiv"):
        pre = "decoration-maximized" if zustand == "aktiv" else "decoration-maximized-inactive"
        titel = (p["akzent"] if farbig else p["flaeche"]) if zustand == "aktiv" else p["flaeche"]
        for teil in ("topleft", "top", "topright"):
            ablegen(f"{pre}-{teil}", 2 if teil != "top" else 10, titel_h,
                    f'<rect x="0" y="0" width="{2 if teil != "top" else 10}" height="{titel_h}" fill="{titel}"/>')
        for teil in ("left", "right", "center", "bottomleft", "bottom", "bottomright"):
            ablegen(f"{pre}-{teil}", 2 if teil != "center" else 10, 2, "")

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{ox}" height="{max(T, U) + 4}">'
            f'<defs>{"".join(defs)}</defs>{"".join(teile)}</svg>')


def erzeugen(p, e, ziel: Path, name):
    """Schreibt das komplette Aurorae-Thema nach ziel/<name>/."""
    d = ziel / name
    d.mkdir(parents=True, exist_ok=True)
    schlank = e["titelleiste"] == "schlank"
    titel_h = 22 if schlank else 32
    knopf = 16 if schlank else 24
    r = 7 if e["ecken"] == "rund" else 2
    farbig = e["titelleiste"] == "farbig"
    (d / "decoration.svg").write_text(rahmen_svg(p, e, titel_h, r), encoding="utf-8")
    for datei, symbol in SYMBOLE.items():
        (d / f"{datei}.svg").write_text(knopf_svg(p, e, symbol, knopf), encoding="utf-8")
    aktiv_text = p["auf_akzent"] if farbig else p["text"]
    (d / f"{name}rc").write_text(f"""[General]
ActiveTextColor={aktiv_text}
InactiveTextColor={p["leise"]}
UseTextShadow=false
TitleAlignment=Center
TitleVerticalAlignment=Center
Animation=160
Shadow=true
DecorationPosition=0
ActiveHighlightColor={p["akzent"]}

[Layout]
BorderLeft={r}
BorderRight={r}
BorderBottom={r}
TitleEdgeTop=0
TitleEdgeBottom=0
TitleEdgeLeft=4
TitleEdgeRight=4
TitleEdgeTopMaximized=0
TitleEdgeBottomMaximized=0
TitleEdgeLeftMaximized=4
TitleEdgeRightMaximized=4
TitleBorderLeft=8
TitleBorderRight=8
TitleHeight={titel_h}
ButtonWidth={knopf}
ButtonHeight={knopf}
ButtonSpacing={2 if schlank else 4}
ButtonMarginTop={(titel_h - knopf) // 2}
ExplicitButtonSpacer=8
PaddingTop={SCHATTEN_OBEN}
PaddingBottom={SCHATTEN_UNTEN}
PaddingLeft={SCHATTEN_SEITE}
PaddingRight={SCHATTEN_SEITE}
""", encoding="utf-8")
    (d / "metadata.desktop").write_text(f"""[Desktop Entry]
Name={name}
Comment=Biblix Fensterrahmen ({p["name"]})
X-KDE-PluginInfo-Name={name}
X-KDE-PluginInfo-Author=Biblix
X-KDE-PluginInfo-License=GPL
X-KDE-PluginInfo-Version=2.0
""", encoding="utf-8")
    return d
