"""Biblix-Symbole: eigene Symbole fuer das Wichtigste, Ordner in Preset-Farbe; der Rest kommt aus Breeze."""
import shutil
from pathlib import Path

from .grafik import prompt_b_form, SECHSECK
from .kern import mischen, dunkler, text_auf
from . import tray

# Motive im 24er Raster, als Linien gezeichnet
MOTIVE = {
    "haus": "M4 11 L12 4 L20 11 M6.5 9.5 V19 H17.5 V9.5 M10 19 V14 H14 V19",
    "dokument": "M7 3.5 H14 L18 7.5 V20.5 H7 Z M14 3.5 V7.5 H18 M9.5 11.5 H15.5 M9.5 14.5 H15.5 M9.5 17.5 H13",
    "download": "M12 4 V15 M7.5 10.5 L12 15 L16.5 10.5 M5 19.5 H19",
    "musik": "M9.5 17.5 V6 L18.5 4 V15.5 M9.5 17.5 a2.5 2.2 0 1 1 -5 0 a2.5 2.2 0 1 1 5 0 Z M18.5 15.5 a2.5 2.2 0 1 1 -5 0 a2.5 2.2 0 1 1 5 0 Z",
    "bild": "M4 5.5 H20 V18.5 H4 Z M4 15.5 L9 11 L13 14.5 L15.5 12.5 L20 16.5 M15 8.5 a1.3 1.3 0 1 1 0 .1",
    "video": "M4 6 H20 V18 H4 Z M10.5 9.2 L15 12 L10.5 14.8 Z",
    "bildschirm": "M3.5 5 H20.5 V16 H3.5 Z M9 20 H15 M12 16 V20",
    "terminal": "M5 8 L9 12 L5 16 M11.5 17 H18.5",
    "zahnrad": "",
    "papierkorb": "M5 7 H19 M9.5 7 V4.5 H14.5 V7 M7 7 L8 20 H16 L17 7 M10.5 10.5 V16.5 M13.5 10.5 V16.5",
    "papierkorb-voll": "M5 7 H19 M9.5 7 V4.5 H14.5 V7 M7 7 L8 20 H16 L17 7 M8.5 12 L15.5 10 M9 15.5 L15 14",
    "palette": "M12 4 a8 8 0 1 0 0 16 c1.4 0 1.8 -1 1.2 -2 -.6 -1 .1 -2 1.3 -2 H17 a3 3 0 0 0 3 -3 c0 -5 -3.6 -9 -8 -9 Z"
               " M8 11 h.1 M10.5 7.8 h.1 M14.5 7.8 h.1",
    "spiel": "M7 8.5 H17 a4 4 0 0 1 4 4 V15 a2.5 2.5 0 0 1 -4.4 1.6 L15 14.8 H9 L7.4 16.6 A2.5 2.5 0 0 1 3 15 V12.5 a4 4 0 0 1 4 -4 Z"
             " M7.5 11 V13.5 M6.2 12.25 H8.8 M15.5 11.5 h.1 M17 13 h.1",
    "fenster": "M4 4.5 H11 V11.5 H4 Z M13 4.5 H20 V11.5 H13 Z M4 13.5 H11 V20 H4 Z M13 13.5 H20 V20 H13 Z",
    "ordner": "M3.5 6.5 H9.5 L11.5 8.5 H20.5 V18.5 H3.5 Z",
    "wolke": "M7.5 18 H17.5 a3.5 3.5 0 0 0 .3 -7 a5.5 5.5 0 0 0 -10.6 1.2 a3 3 0 0 0 -.2 5.8 Z",
}

# Datei -> (Motiv, Kontext). Ordner werden extra gezeichnet.
APPS = {
    "system-file-manager": "ordner", "org.kde.dolphin": "ordner",
    "utilities-terminal": "terminal", "org.kde.konsole": "terminal", "konsole": "terminal",
    "preferences-system": "zahnrad", "systemsettings": "zahnrad", "preferences-desktop": "zahnrad",
    "de.biblix.Design": "palette", "biblix-design": "palette",
    "de.biblix.NeustartWindows": "fenster", "biblix-neustart-windows": "fenster",
    "biblix-windows-spiel": "spiel",
    "user-trash": "papierkorb", "user-trash-full": "papierkorb-voll",
}
ORDNER = {
    "folder": None, "inode-directory": None, "folder-open": None,
    "user-home": "haus", "folder-home": "haus",
    "folder-documents": "dokument", "folder-download": "download", "folder-downloads": "download",
    "folder-music": "musik", "folder-pictures": "bild", "folder-images": "bild", "folder-videos": "video",
    "user-desktop": "bildschirm", "folder-desktop": "bildschirm", "folder-games": "spiel",
    "folder-cloud": "wolke", "folder-onedrive": "wolke",
}


def _zahnrad(farbe, breite):
    # Biblix-Zahnrad: eine Mutter
    return (f'<g transform="translate(2 2)"><polygon points="{SECHSECK}" fill="none" stroke="{farbe}" '
            f'stroke-width="{breite}" stroke-linejoin="round"/><circle cx="10" cy="10" r="3.4" fill="none" '
            f'stroke="{farbe}" stroke-width="{breite}"/></g>')


def _motiv(name, farbe, breite=1.8):
    if name == "zahnrad":
        return _zahnrad(farbe, breite)
    return (f'<path d="{MOTIVE[name]}" fill="none" stroke="{farbe}" stroke-width="{breite}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def app_symbol(p, stil, motiv):
    """Ein App-Symbol im gewaehlten Stil (48er Feld)."""
    if stil == "kacheln":
        grund = p["akzent"] if motiv not in ("papierkorb", "papierkorb-voll") else p["karte"]
        vorne = text_auf(grund) if motiv not in ("papierkorb", "papierkorb-voll") else p["text"]
        if motiv == "terminal":
            grund, vorne = "#0f141c", "#e8ecf2"
        inhalt = (f'<rect x="3" y="3" width="42" height="42" rx="11" fill="{grund}"/>'
                  f'<rect x="3" y="3" width="42" height="21" rx="11" fill="#ffffff" fill-opacity="0.08"/>'
                  f'<g transform="translate(9 9) scale(1.25)">{_motiv(motiv, vorne)}</g>')
        if motiv == "terminal":
            inhalt += f'<rect x="25" y="29" width="10" height="3" rx="1" fill="{p["akzent"]}"/>'
    elif stil == "flach":
        inhalt = (f'<g transform="translate(2 2) scale(1.83)">{_motiv(motiv, p["akzent"], 2.2)}</g>')
    else:  # linien
        inhalt = (f'<g transform="translate(2 2) scale(1.83)">{_motiv(motiv, p["text"], 1.3)}</g>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">{inhalt}</svg>'


def ordner_symbol(p, stil, motiv):
    a = p["akzent"]
    hinten, vorne = dunkler(a, 0.25), a
    if stil == "linien":
        inhalt = (f'<path d="M5 13 H18 L22 17 H43 V39 H5 Z" fill="none" stroke="{a}" stroke-width="2.4" stroke-linejoin="round"/>')
    else:
        inhalt = (f'<path d="M4 10 a3 3 0 0 1 3 -3 H18 L22 11 H41 a3 3 0 0 1 3 3 V38 a3 3 0 0 1 -3 3 H7 a3 3 0 0 1 -3 -3 Z" fill="{hinten}"/>'
                  f'<path d="M4 17 a3 3 0 0 1 3 -3 H41 a3 3 0 0 1 3 3 V38 a3 3 0 0 1 -3 3 H7 a3 3 0 0 1 -3 -3 Z" fill="{vorne}"/>'
                  f'<path d="M4 17 a3 3 0 0 1 3 -3 H41 a3 3 0 0 1 3 3 V21 H4 Z" fill="#ffffff" fill-opacity="0.12"/>')
    if motiv:
        farbe = a if stil == "linien" else mischen(text_auf(vorne), vorne, 0.15)
        inhalt += f'<g transform="translate(15 17) scale(0.75)">{_motiv(motiv, farbe, 2.4)}</g>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">{inhalt}</svg>'


def biblix_symbol(p):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 120 120">'
            f'<rect width="120" height="120" rx="26" fill="{p["karte"] if p["dunkel"] else p["text"]}"/>'
            f'{prompt_b_form(p["text"] if p["dunkel"] else p["karte"], p["akzent"], 8)}</svg>')


STATUS = """
[scalable/status]
Size=22
MinSize=8
MaxSize=512
Type=Scalable
Context=Status
"""


def erzeugen(p, stil, ziel: Path, name, mit_tray=True):
    d = ziel / name
    if d.exists():
        shutil.rmtree(d)
    apps, orte = d / "scalable/apps", d / "scalable/places"
    apps.mkdir(parents=True)
    orte.mkdir(parents=True)
    for datei, motiv in APPS.items():
        if motiv == "ordner":
            inhalt = ordner_symbol(p, stil if stil != "flach" else "kacheln", None)
        else:
            inhalt = app_symbol(p, stil, motiv)
        ziel_dir = orte if datei.startswith("user-trash") else apps
        (ziel_dir / f"{datei}.svg").write_text(inhalt, encoding="utf-8")
    for datei, motiv in ORDNER.items():
        (orte / f"{datei}.svg").write_text(ordner_symbol(p, stil if stil == "linien" else "kacheln", motiv), encoding="utf-8")
    # Einfarbige Symbole (für Knöpfe, werden vom Thema eingefärbt)
    (apps / "biblix-windows-symbolic.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><g fill="#232629">'
        '<rect x="1.5" y="1.5" width="6" height="6" rx="1"/><rect x="8.5" y="1.5" width="6" height="6" rx="1"/>'
        '<rect x="1.5" y="8.5" width="6" height="6" rx="1"/><rect x="8.5" y="8.5" width="6" height="6" rx="1"/></g></svg>',
        encoding="utf-8")
    for datei in ("biblix", "start-here", "start-here-kde", "start-here-kde-plasma", "distributor-logo"):
        (apps / f"{datei}.svg").write_text(biblix_symbol(p), encoding="utf-8")
    # Tray-Symbole (Lautstaerke, Netzwerk, Bluetooth, Benachrichtigungen) im Schrauben-Stil
    if mit_tray:
        status = d / "scalable/status"
        status.mkdir(parents=True)
        for elemente in tray.belegung().values():
            for eid, teile in elemente.items():
                inhalt = tray.einzeln(teile, p)
                (status / f"{eid}.svg").write_text(inhalt, encoding="utf-8")
                (status / f"{eid}-symbolic.svg").write_text(inhalt, encoding="utf-8")
    erbt = "breeze-dark" if p["dunkel"] else "breeze"
    (d / "index.theme").write_text(f"""[Icon Theme]
Name={name}
Comment=Biblix-Symbole ({p["name"]})
Inherits={erbt},hicolor
Directories=scalable/apps,scalable/places{",scalable/status" if mit_tray else ""}

[scalable/apps]
Size=48
MinSize=8
MaxSize=512
Type=Scalable
Context=Applications

[scalable/places]
Size=48
MinSize=8
MaxSize=512
Type=Scalable
Context=Places
{STATUS if mit_tray else ""}""", encoding="utf-8")
    return d
