"""Biblix Design: Presets, Einstellungen und Farbhilfen.

Alles, was die Design-App, der Erststart und die Generatoren gemeinsam brauchen.
Laeuft ohne Qt, damit es auch beim Paketbau und im pkexec-Helfer funktioniert.
"""
import colorsys
import copy
import datetime
import json
import os
from pathlib import Path

DESIGN = Path(os.environ.get("BIBLIX_DESIGN_DIR", "/usr/share/biblix/design"))
HOME = Path.home()
KONFIG = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config"))
DATEN = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local/share"))
EINSTELLUNGEN = KONFIG / "biblix" / "design.json"
VERLAUF = KONFIG / "biblix" / "design-verlauf.json"
MISCHUNGEN = KONFIG / "biblix" / "mischungen"

FARBNAMEN = ["grund", "flaeche", "karte", "rand", "text", "leise", "akzent", "akzent2", "gefahr"]

# Der Biblix-Standard. Jede Option der Design-App hat hier ihren Platz.
STANDARD = {
    "_stand": 9,                    # Stand der Einstellungen (für einmalige Umstellungen nach Updates)
    "preset": "bibi-tech",
    "modus": "dunkel",              # dunkel | hell | auto (Tag hell, Abend dunkel)
    "eigene_farben": None,          # None oder {"dunkel": {...}, "hell": {...}}
    "startmenue": "bibi",           # bibi | vollbild | klassisch
    "startmenue_position": "links", # links | mitte
    "startknopf": "biblix",         # biblix | firma
    "taskleiste": "schwebend",      # schwebend | fest | dock
    "transparenz": "undurchsichtig", # undurchsichtig | milchglas | adaptiv
    "leiste_stil": "zonen",         # zonen | inseln | kopfzeile | typenschild (Biblix-Fensterleiste und -Uhr) | klassisch (KDE)
    "leiste_lack": False,           # alle Symbole einfarbig, nur das aktive Fenster in echten Farben
    "leiste_welten": True,          # Fensterleiste und Uhr wechseln mit dem Preset ihren Charakter
    "monitore": "beide",            # beide | haupt | gleich
    "titelleiste": "nahtlos",       # nahtlos | farbig | schlank
    "knoepfe": "schrauben",         # schrauben | punkte | terminal | klammern | kapsel | balken
    "knoepfe_links": False,
    "ecken": "rund",                # rund | eckig
    "animationen": True,
    "effekt_oeffnen": "bibi-pop",   # bibi-pop | hochgleiten | aufbauen | einblenden | aus
    "effekt_schliessen": "zusammenziehen",  # zusammenziehen | wegfallen | abbauen | ausblenden | aus
    "effekt_minimieren": "fliegen", # fliegen | wabern | ausblenden
    "arbeitsflaeche": "wuerfel",    # wuerfel | gleiten | ueberblenden
    "arbeitsflaechen": "eine",      # eine | vier
    "overlay": "ausfuehrlich",      # Leistungs-Overlay in Spielen: ausfuehrlich | kompakt | aus
    "wackeln": True,
    "durchsichtig_verschieben": False,
    "klick_funken": False,
    "symbole": "kacheln",           # kacheln | flach | linien
    "tray": "schrauben",            # schrauben | standard (Symbole unten rechts)
    "zeiger": "biblix",             # biblix | standard
    "ladezeiger": "mutter",         # mutter | cursor | schichten
    "klaenge": "preset",            # biblix | preset | retro | ruhig | aus
    "startklang": True,
    "hintergrund": "schrauben-bauplan",  # Hauptmonitor (auch Sperrbildschirm); "datei:…"/"ordner:…" = eigene Bilder
    "hintergrund_zweiter": None,    # weitere Monitore: None = wie der Hauptmonitor
    "hintergrund_eigene_farben": False,  # Firmenmotive in der aktuellen Palette statt in Firmenfarben
    "eigene_bilder": [],            # eigene Bilder und Ordner als Motiv-IDs ("datei:/pfad", "ordner:/pfad")
    "diashow": False,
    "diashow_minuten": 30,
    "diashow_gruppe": "auto",       # auto (Gruppe des Hauptbildes) | allgemein | standorte | Preset-ID
    "diashow_monitore": "beide",    # haupt | beide
    "sperrbildschirm": "bibi",      # bibi | terminal | schlicht
    "ladeanimation": "tippen",      # tippen | schrauben | einblenden
    "bootmenue_mitfaerben": True,
    "terminal_farben": True,
    "terminal_prompt": True,
    "firefox_startseite": True,
    "spielmodus_anzeige": False,
    "update_symbol": False,
    "leistungs_anzeige": False,
    "kopfhoerer_schalter": False,
}

# Fuer die Design-App: Beschriftung jeder Wahl
WAHL = {
    "leiste_stil": [("zonen", "Drei Zonen"), ("inseln", "Drei Inseln"), ("kopfzeile", "Kopfzeile"),
                    ("typenschild", "Typenschild"), ("klassisch", "Klassisch (KDE)")],
    "modus": [("dunkel", "Dunkel"), ("hell", "Hell"), ("auto", "Tag hell, Abend dunkel")],
    "startmenue": [("bibi", "Bibi-Startmenü"), ("vollbild", "Vollbild"), ("klassisch", "KDE klassisch")],
    "startmenue_position": [("links", "Links"), ("mitte", "Mitte")],
    "startknopf": [("biblix", "Biblix-Logo"), ("firma", "Firmenlogo")],
    "taskleiste": [("schwebend", "Schwebend"), ("fest", "Fest"), ("dock", "Dock")],
    "transparenz": [("undurchsichtig", "Undurchsichtig"), ("milchglas", "Milchglas"), ("adaptiv", "Adaptiv")],
    "monitore": [("beide", "Beide, eigene Fenster"), ("haupt", "Nur Hauptmonitor"), ("gleich", "Beide gleich")],
    "titelleiste": [("nahtlos", "Nahtlos"), ("farbig", "Farbig"), ("schlank", "Schlank")],
    "knoepfe": [("schrauben", "Schrauben"), ("punkte", "Punkte"), ("terminal", "Terminal"),
                ("klammern", "Klammern"), ("kapsel", "Kapsel"), ("balken", "Balken")],
    "ecken": [("rund", "Rund"), ("eckig", "Eckig")],
    "effekt_oeffnen": [("bibi-pop", "Bibi-Pop"), ("hochgleiten", "Hochgleiten"), ("aufbauen", "Aufbauen"),
                       ("einblenden", "Einblenden"), ("aus", "Aus")],
    "effekt_schliessen": [("zusammenziehen", "Zusammenziehen"), ("wegfallen", "Wegfallen"), ("abbauen", "Abbauen"),
                          ("ausblenden", "Ausblenden"), ("aus", "Aus")],
    "effekt_minimieren": [("fliegen", "In die Taskleiste"), ("wabern", "Wabern"), ("ausblenden", "Ausblenden")],
    "arbeitsflaeche": [("wuerfel", "3D-Würfel"), ("gleiten", "Gleiten"), ("ueberblenden", "Überblenden")],
    "arbeitsflaechen": [("eine", "Eine"), ("vier", "Vier")],
    "overlay": [("ausfuehrlich", "Ausführlich"), ("kompakt", "Kompakt (eine Zeile)"), ("aus", "Aus")],
    "symbole": [("kacheln", "Kacheln"), ("flach", "Flach"), ("linien", "Linien")],
    "tray": [("schrauben", "Bibi-Schrauben"), ("standard", "KDE-Standard")],
    "zeiger": [("biblix", "Biblix-Zeiger"), ("standard", "Standard")],
    "ladezeiger": [("mutter", "Drehende Mutter"), ("cursor", "Terminal-Cursor"), ("schichten", "Schichten-B")],
    "klaenge": [("preset", "Firmen-Klänge"), ("biblix", "Biblix"), ("retro", "Retro-Terminal"),
                ("ruhig", "Ruhig"), ("aus", "Aus")],
    "sperrbildschirm": [("bibi", "Bibi"), ("terminal", "Terminal"), ("schlicht", "Schlicht")],
    "ladeanimation": [("tippen", "Prompt-B tippt"), ("schrauben", "Schrauben-B"), ("einblenden", "Einblenden")],
}


# ---------------------------------------------------------------- Farben

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(r, g, b):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in (r, g, b))


def mischen(a, b, t):
    """Farbe a nach b, t = 0..1"""
    ra, rb = hex_rgb(a), hex_rgb(b)
    return rgb_hex(*[x + (y - x) * t for x, y in zip(ra, rb)])


def heller(h, t):
    return mischen(h, "#ffffff", t)


def dunkler(h, t):
    return mischen(h, "#000000", t)


def helligkeit(h):
    r, g, b = [v / 255 for v in hex_rgb(h)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def text_auf(h):
    """Gut lesbare Schriftfarbe auf Hintergrund h"""
    return "#0b0d12" if helligkeit(h) > 0.55 else "#ffffff"


def kde_rgb(h):
    return ",".join(str(v) for v in hex_rgb(h))


def drehen(h, grad):
    r, g, b = [v / 255 for v in hex_rgb(h)]
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb((hh + grad / 360) % 1, l, s)
    return rgb_hex(r * 255, g * 255, b * 255)


# ---------------------------------------------------------------- Presets

def presets():
    """Alle Presets, Bibi Tech zuerst."""
    liste = []
    for f in sorted((DESIGN / "presets").glob("*.json")):
        try:
            liste.append(json.loads(f.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    liste.sort(key=lambda p: (p["id"] != "bibi-tech", p["name"]))
    return liste


def preset(pid):
    for p in presets():
        if p["id"] == pid:
            return p
    return presets()[0]


# ---------------------------------------------------------------- Einstellungen

def laden():
    e = copy.deepcopy(STANDARD)
    try:
        e.update(json.loads(EINSTELLUNGEN.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    for k, v in list(e.items()):
        if k in WAHL and v not in [w for w, _ in WAHL[k]]:
            e[k] = STANDARD[k]
    return e


def speichern(e, verlauf=True):
    EINSTELLUNGEN.parent.mkdir(parents=True, exist_ok=True)
    if verlauf and EINSTELLUNGEN.exists():
        alt = laden()
        try:
            v = json.loads(VERLAUF.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            v = []
        alt["_zeit"] = datetime.datetime.now().isoformat(timespec="minutes")
        v.insert(0, alt)
        VERLAUF.write_text(json.dumps(v[:20], indent=1, ensure_ascii=False), encoding="utf-8")
    tmp = EINSTELLUNGEN.with_suffix(".tmp")
    tmp.write_text(json.dumps(e, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(EINSTELLUNGEN)


def verlauf():
    try:
        return json.loads(VERLAUF.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def aktueller_modus(e):
    if e["modus"] != "auto":
        return e["modus"]
    stunde = datetime.datetime.now().hour
    return "hell" if 7 <= stunde < 19 else "dunkel"


def palette(e=None, modus=None):
    """Die wirksame Palette: Preset oder eigene Farben, plus abgeleitete Toene."""
    e = e or laden()
    modus = modus or aktueller_modus(e)
    p = preset(e["preset"])
    f = dict(p[modus])
    eigen = e.get("eigene_farben") or {}
    if eigen.get(modus):
        f.update({k: v for k, v in eigen[modus].items() if k in FARBNAMEN})
    f["modus"] = modus
    f["preset"] = p["id"]
    f["name"] = p["name"] if not eigen else "Eigene Mischung"
    f["dunkel"] = modus == "dunkel"
    # Abgeleitete Toene
    f["akzent_hell"] = heller(f["akzent"], 0.25)
    f["akzent_dunkel"] = dunkler(f["akzent"], 0.25)
    f["auf_akzent"] = text_auf(f["akzent"])
    f["auf_akzent2"] = text_auf(f["akzent2"])
    f["knopf_ruhe"] = mischen(f["flaeche"], f["leise"], 0.55)
    f["knopf_inaktiv"] = mischen(f["flaeche"], f["leise"], 0.3)
    f["auswahl"] = mischen(f["flaeche"], f["akzent"], 0.35)
    return f
