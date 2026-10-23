"""Biblix-Tray-Symbole: Lautstaerke, Netzwerk, Bluetooth und Benachrichtigungen im Schrauben-Stil.

Landen als scalable/status im Biblix-Symbol-Thema (symbole.py). Farben kommen ueber die Klassen
ColorScheme-* aus dem aktiven Farbschema: Linien in Textfarbe, Muttern in Akzentfarbe.
"""
import math

SVG = "http://www.w3.org/2000/svg"

STIL = (".ColorScheme-Text{color:#fcfcfc}.ColorScheme-Highlight{color:#3daee9}"
        ".ColorScheme-NegativeText{color:#da4453}.ColorScheme-NeutralText{color:#f67400}")
T, A, ROT, GELB = "ColorScheme-Text", "ColorScheme-Highlight", "ColorScheme-NegativeText", "ColorScheme-NeutralText"


# ---------------------------------------------------------------- Bausteine (22er Feld)

def _sechseck(cx, cy, r):
    return " ".join(f"{cx + r * math.cos(math.radians(-90 + 60 * k)):.2f},{cy + r * math.sin(math.radians(-90 + 60 * k)):.2f}"
                    for k in range(6))


def mutter(cx, cy, r, klasse=A, voll=True, breite=1.4):
    """Sechskant-Mutter; voll = gefuellt mit Loch, sonst nur Umriss."""
    if voll:
        loch = r * 0.38
        return (f'<path class="{klasse}" fill="currentColor" fill-rule="evenodd" d="M{_sechseck(cx, cy, r).replace(" ", " L")} Z '
                f'M{cx - loch:.2f},{cy:.2f} a{loch:.2f},{loch:.2f} 0 1 0 {2 * loch:.2f},0 a{loch:.2f},{loch:.2f} 0 1 0 {-2 * loch:.2f},0 Z"/>')
    return (f'<polygon class="{klasse}" points="{_sechseck(cx, cy, r)}" fill="none" stroke="currentColor" '
            f'stroke-width="{breite}" stroke-linejoin="round"/>')


def linie(d, klasse=T, breite=1.5, deckkraft=1.0):
    o = f' opacity="{deckkraft}"' if deckkraft < 1 else ""
    return (f'<path class="{klasse}" d="{d}" fill="none" stroke="currentColor" stroke-width="{breite}" '
            f'stroke-linecap="round" stroke-linejoin="round"{o}/>')


def _bogen(cx, cy, r, von, bis):
    a, b = math.radians(von), math.radians(bis)
    return (f"M{cx + r * math.cos(a):.2f},{cy + r * math.sin(a):.2f} "
            f"A{r},{r} 0 0 1 {cx + r * math.cos(b):.2f},{cy + r * math.sin(b):.2f}")


# ---------------------------------------------------------------- Motive

def lautsprecher(stufe, stumm=False, ende=None):
    """Lautsprecher mit Mutter als Membran, 0..3 Wellen. ende: Klasse der dritten Welle (Warnung)."""
    teile = [linie("M2.5 8.5 H6 L10.5 4.5 V17.5 L6 13.5 H2.5 Z"), mutter(7.6, 11, 2.1)]
    if stumm:
        teile.append(linie("M14 8 L20 14 M20 8 L14 14", ROT, 1.6))
        return teile
    for i, r in enumerate((3.4, 6.2, 9.0)):
        aktiv = i < stufe
        klasse = ende if (ende and i == 2) else T
        teile.append(linie(_bogen(10.5, 11, r, -42, 42), klasse, 1.5, 1.0 if aktiv else 0.3))
    return teile


def kabel(zustand):
    """Schraube in Platte: verbunden = Akzent-Mutter, sonst Umriss oder herausgedreht."""
    if zustand in ("aus", "fehlt"):
        teile = [mutter(11, 4.6, 3.6, T, voll=False), linie("M11 8.4 V12", T, 1.4, 0.6),
                 linie("M3 18.5 H19"), linie("M11 15 V18.5", T, 1.4, 0.35)]
        if zustand == "fehlt":
            teile.append(linie("M4 3 L18 17", ROT, 1.5))
        return teile
    klasse = {"an": A, "begrenzt": GELB}.get(zustand, T)
    teile = [mutter(11, 6, 4.2, klasse, voll=zustand != "bereit"),
             linie("M11 10.2 V17", T, 1.5), linie("M9.2 12.4 L12.8 13.4 M9.2 14.6 L12.8 15.6", T, 1.0),
             linie("M3 18.5 H19")]
    return teile


def funk(stufe, zustand="an"):
    """Mutter unten, darueber bis zu drei Funkboegen."""
    klasse = {"begrenzt": GELB, "aus": T}.get(zustand, A)
    teile = [mutter(11, 17.2, 3.1, klasse, voll=zustand != "aus")]
    for i, r in enumerate((6.4, 10.4, 14.4)):
        aktiv = i < stufe and zustand != "aus"
        teile.append(linie(_bogen(11, 17.6, r, -135, -45), T, 1.6, 1.0 if aktiv else 0.28))
    if zustand == "aus":
        teile.append(linie("M4 4 L18 18", ROT, 1.5))
    return teile


RUNE = "M7.6 7.6 L14 13.4 L11 16.2 V5.8 L14 8.6 L7.6 14.4"


def bluetooth(zustand):
    if zustand == "an":
        return [mutter(11, 11, 9.6, A, voll=False, breite=1.8), linie(RUNE, T, 1.4)]
    if zustand == "aus":
        return [mutter(11, 11, 9.6, T, voll=False, breite=1.2), linie(RUNE, T, 1.3, 0.4)]
    return [mutter(11, 11, 9.6, T, voll=False, breite=1.3), linie(RUNE, T, 1.4)]


def glocke(zustand):
    """Pausenglocke; aktiv = Akzent-Mutter als Kloeppel, aus = durchgestrichen."""
    teile = [linie("M5 15.5 H17 L15.6 13.3 V9.6 a4.6 4.6 0 0 0 -9.2 0 V13.3 Z", T, 1.5,
                   0.45 if zustand == "aus" else 1.0)]
    if zustand == "aktiv":
        teile.append(mutter(11, 18.3, 2.4, A))
        teile.append(mutter(17.6, 4.6, 2.6, A))
    elif zustand == "laeuft":
        teile.append(mutter(11, 18.3, 2.4, A, voll=False, breite=1.1))
    else:
        teile.append(linie("M9.6 18.4 H12.4", T, 1.5, 0.45 if zustand == "aus" else 1.0))
    if zustand == "aus":
        teile.append(linie("M4 3.5 L18 18.5", ROT, 1.5))
    return teile


# ---------------------------------------------------------------- Belegung: Datei -> {Element-ID: Teile}

def _funk_alle():
    m = {}
    stufen = {"0": 0, "00": 0, "20": 1, "40": 1, "60": 2, "80": 2, "100": 3}
    for s, n in stufen.items():
        if s != "00":
            m[f"network-wireless-{s}"] = funk(n)
            m[f"network-wireless-{s}-locked"] = funk(n)
            m[f"network-wireless-{s}-limited"] = funk(n, "begrenzt")
        m[f"network-wireless-connected-{s}"] = funk(n)
    m.update({"network-wireless-available": funk(3, "bereit"), "network-wireless-on": funk(3, "bereit"),
              "network-wireless-disconnected": funk(0, "aus"), "network-wireless-off": funk(0, "aus")})
    return m


def belegung():
    return {
        "audio": {
            "audio-volume-high": lautsprecher(3), "audio-volume-medium": lautsprecher(2),
            "audio-volume-low": lautsprecher(1), "audio-volume-muted": lautsprecher(0, stumm=True),
            "audio-volume-high-warning": lautsprecher(3, ende=GELB),
            "audio-volume-high-danger": lautsprecher(3, ende=ROT),
        },
        "network": {
            "network-wired-activated": kabel("an"), "network-wired-activated-locked": kabel("an"),
            "network-wired-activated-limited": kabel("begrenzt"),
            "network-wired": kabel("bereit"), "network-wired-available": kabel("bereit"),
            "network-unavailable": kabel("fehlt"),
            "network-bluetooth": bluetooth("bereit"), "network-bluetooth-activated": bluetooth("an"),
            "network-bluetooth-activated-locked": bluetooth("an"), "network-bluetooth-inactive": bluetooth("aus"),
            **_funk_alle(),
        },
        "notification": {
            "notification-active": glocke("aktiv"), "notification-inactive": glocke("ruhig"),
            "notification-empty": glocke("ruhig"), "notification-disabled": glocke("aus"),
            "notification-progress-active": glocke("laeuft"), "notification-progress-inactive": glocke("ruhig"),
        },
    }


# ---------------------------------------------------------------- Dateien bauen

def stil(p):
    """Farben der Palette; KDE kann sie ueber current-color-scheme trotzdem ans Farbschema anpassen."""
    return (f".ColorScheme-Text{{color:{p['text']}}}.ColorScheme-Highlight{{color:{p['akzent']}}}"
            f".ColorScheme-NegativeText{{color:{p['gefahr']}}}.ColorScheme-NeutralText{{color:{p['akzent2']}}}")


def einzeln(teile, p=None):
    """Ein Symbol als eigene SVG-Datei fuer das Symbol-Thema (22er Feld)."""
    return (f'<svg xmlns="{SVG}" width="22" height="22" viewBox="0 0 22 22">'
            f'<style id="current-color-scheme" type="text/css">{stil(p) if p else STIL}</style>{"".join(teile)}</svg>')


def vorschau(datei_name="alle"):
    """Alle Symbole nebeneinander als SVG (zum Ansehen beim Bauen)."""
    teile, i = [], 0
    for elemente in belegung().values():
        for eid, t in sorted(elemente.items()):
            x, y = 6 + 40 * (i % 12), 6 + 40 * (i // 12)
            teile.append(f'<g transform="translate({x} {y}) scale(1.4)">{"".join(t)}</g>')
            i += 1
    h = 12 + 40 * ((i + 11) // 12)
    return (f'<svg xmlns="{SVG}" width="{12 + 40 * 12}" height="{h}"><style>{STIL}</style>'
            f'<rect width="{12 + 40 * 12}" height="{h}" fill="#1b1e24"/>{"".join(teile)}</svg>')
