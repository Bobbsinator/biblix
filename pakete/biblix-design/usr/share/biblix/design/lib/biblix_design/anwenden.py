"""Wendet die Biblix-Design-Einstellungen auf Plasma, KWin und die Programme an (als Benutzer).

Jeder Schritt ist einzeln abgesichert: faellt einer aus (z. B. ohne laufendes Plasma),
laufen die anderen trotzdem. Rueckgabe: Liste von Meldungen fuer die App.
"""
import json
import re
import os
import shutil
import subprocess
import time
from pathlib import Path

from . import kern, farbschema, aurorae, zeiger, symbole, terminal, hintergruende, grafik
from .kern import DATEN, KONFIG, DESIGN

AKTUELL = KONFIG / "biblix" / "aktuell.json"      # zuletzt angewendeter Stand (fuer A/B-Namen)
PALETTE = KONFIG / "biblix" / "palette.json"      # wirksame Palette fuer S-Launcher und Co.
HG_DIR = DATEN / "wallpapers" / "biblix"
DIASHOW_DIR = DATEN / "wallpapers" / "biblix-diashow"
SYSTEM_HELFER = "/usr/lib/biblix/biblix-design-system"
PROMPT_ZEILE = "[ -f /usr/share/biblix/design/prompt.sh ] && . /usr/share/biblix/design/prompt.sh  # Biblix-Prompt"


def _lauf(*cmd, eingabe=None, warten=True):
    if not shutil.which(cmd[0]) and not Path(cmd[0]).exists():
        return None
    try:
        if not warten:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return 0
        r = subprocess.run(cmd, input=eingabe, capture_output=True, text=True, timeout=120)
        return r.returncode
    except (OSError, subprocess.TimeoutExpired):
        return None


def kconf(datei, gruppen, schluessel, wert):
    """kwriteconfig6 mit verschachtelten Gruppen; wert None loescht."""
    cmd = ["kwriteconfig6", "--file", datei]
    for g in (gruppen if isinstance(gruppen, (list, tuple)) else [gruppen]):
        cmd += ["--group", g]
    cmd += ["--key", schluessel]
    if wert is None:
        cmd.append("--delete")
    elif isinstance(wert, bool):
        cmd += ["--type", "bool", "true" if wert else "false"]
    else:
        cmd.append(str(wert))
    return _lauf(*cmd)


def dbus(dienst, pfad, schnittstelle, methode, *args):
    """D-Bus-Aufruf ueber gdbus (immer vorhanden) oder qdbus."""
    if shutil.which("gdbus"):
        cmd = ["gdbus", "call", "--session", "--dest", dienst, "--object-path", pfad,
               "--method", f"{schnittstelle}.{methode}"] + [json.dumps(a) if isinstance(a, str) else str(a) for a in args]
        return _lauf(*cmd)
    for q in ("qdbus6", "qdbus", "/usr/lib/qt6/bin/qdbus"):
        if shutil.which(q) or Path(q).exists():
            return _lauf(q, dienst, pfad, f"{schnittstelle}.{methode}", *[str(a) for a in args])
    return None


def plasma_skript(js):
    """Plasma-Skript ausführen; gibt die print()-Ausgabe des Skripts zurück."""
    if not shutil.which("gdbus"):
        dbus("org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell", "evaluateScript", js)
        return ""
    try:
        r = subprocess.run(["gdbus", "call", "--session", "--dest", "org.kde.plasmashell", "--object-path", "/PlasmaShell",
                            "--method", "org.kde.PlasmaShell.evaluateScript", json.dumps(js)],
                           capture_output=True, text=True, timeout=60)
        return r.stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _libexec(name):
    for d in ("/usr/lib/x86_64-linux-gnu/libexec", "/usr/libexec", "/usr/lib/libexec"):
        if Path(d, name).exists():
            return str(Path(d, name))
    return None


def _ab(name, aktuell):
    """Plasma laedt Themen gleichen Namens nicht neu -> abwechselnd A/B verwenden."""
    alt = aktuell.get(name, "B")
    neu = "A" if alt == "B" else "B"
    aktuell[name] = neu
    return neu


# ================================================================ Einzelne Teile

def farben(p, akt):
    d = DATEN / "color-schemes"
    d.mkdir(parents=True, exist_ok=True)
    name = "Biblix" + _ab("farben", akt)
    for alt in d.glob("Biblix?.colors"):
        if alt.stem != name:
            alt.unlink()
    (d / f"{name}.colors").write_text(farbschema.erzeugen(p, name), encoding="utf-8")
    kconf("kdeglobals", "General", "accentColorFromWallpaper", False)
    _lauf("plasma-apply-colorscheme", name)
    return f"Farben: {p['name']} ({'dunkel' if p['dunkel'] else 'hell'})"


def rahmen(p, e, akt):
    d = DATEN / "aurorae" / "themes"
    name = "Biblix" + _ab("rahmen", akt)
    for alt in d.glob("Biblix?") if d.exists() else []:
        if alt.name != name:
            shutil.rmtree(alt, ignore_errors=True)
    aurorae.erzeugen(p, e, d, name)
    g = "org.kde.kdecoration2"
    kconf("kwinrc", g, "library", "org.kde.kwin.aurorae")
    kconf("kwinrc", g, "theme", f"__aurorae__svg__{name}")
    if e["knoepfe_links"]:
        kconf("kwinrc", g, "ButtonsOnLeft", "XAI")
        kconf("kwinrc", g, "ButtonsOnRight", "")
    else:
        kconf("kwinrc", g, "ButtonsOnLeft", "M")
        kconf("kwinrc", g, "ButtonsOnRight", "IAX")
    return "Fensterrahmen: " + dict(kern.WAHL["knoepfe"])[e["knoepfe"]]


def rahmen_erneuern(e):
    """Nur den Fensterrahmen neu erzeugen (z. B. nach einem Update mit geaendertem Rahmen)."""
    try:
        akt = json.loads(AKTUELL.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        akt = {}
    r = rahmen(kern.palette(e), e, akt)
    AKTUELL.parent.mkdir(parents=True, exist_ok=True)
    AKTUELL.write_text(json.dumps(akt), encoding="utf-8")
    kwin_neu_laden()
    return r


def symbole_erneuern(e):
    """Nur das Symbol-Thema neu erzeugen (z. B. nach einem Update mit neuen Symbolen)."""
    try:
        akt = json.loads(AKTUELL.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        akt = {}
    r = symbol_thema(kern.palette(e), e, akt)
    AKTUELL.parent.mkdir(parents=True, exist_ok=True)
    AKTUELL.write_text(json.dumps(akt), encoding="utf-8")
    return r


def mauszeiger(p, e, akt):
    if e["zeiger"] == "standard":
        _lauf("plasma-apply-cursortheme", "breeze_cursors")
        return "Mauszeiger: Standard"
    d = DATEN / "icons"
    name = "BiblixZeiger" + _ab("zeiger", akt)
    for alt in d.glob("BiblixZeiger?") if d.exists() else []:
        if alt.name != name:
            shutil.rmtree(alt, ignore_errors=True)
    if zeiger.erzeugen(p, e["ladezeiger"], d, name):
        _lauf("plasma-apply-cursortheme", name)
        return "Mauszeiger: Biblix"
    return "Mauszeiger: xcursorgen fehlt, übersprungen"


def symbol_thema(p, e, akt):
    d = DATEN / "icons"
    name = "BiblixSymbole" + _ab("symbole", akt)
    for alt in d.glob("BiblixSymbole?") if d.exists() else []:
        if alt.name != name:
            shutil.rmtree(alt, ignore_errors=True)
    symbole.erzeugen(p, e["symbole"], d, name, mit_tray=e.get("tray", "schrauben") == "schrauben")
    tool = _libexec("plasma-changeicons")
    if tool:
        _lauf(tool, name)
    else:
        kconf("kdeglobals", "Icons", "Theme", name)
    return "Symbole: " + dict(kern.WAHL["symbole"])[e["symbole"]]


def _bild_js(bild):
    return (f'd.wallpaperPlugin = "org.kde.image";\n'
            f'd.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];\n'
            f'd.writeConfig("Image", {json.dumps("file://" + str(bild))});\n')


def _diashow_js(ordner, minuten):
    return (f'd.wallpaperPlugin = "org.kde.slideshow";\n'
            f'd.currentConfigGroup = ["Wallpaper", "org.kde.slideshow", "General"];\n'
            f'd.writeConfig("SlidePaths", {json.dumps(str(ordner))});\n'
            f'd.writeConfig("SlideInterval", {minuten * 60});\n'
            f'd.writeConfig("SlideshowMode", 1);\n')


def _lebendig_js(p, leb):
    """Animierter Hintergrund (Plasma-Modul de.biblix.lebendig)."""
    szene, _, gruppe, _ = leb
    if gruppe != "allgemein":  # Firmen-Szenen in Firmenfarben, wie die Firmenbilder
        p = kern.palette({"preset": gruppe, "modus": "dunkel", "eigene_farben": None}, "dunkel")
    farben = {k: p[k] for k in ("grund", "flaeche", "karte", "rand", "text", "leise", "akzent", "akzent2") if k in p}
    try:
        sprueche = [z.strip() for z in (DESIGN / "sprueche.txt").read_text(encoding="utf-8").splitlines()
                    if z.strip() and not z.startswith("#")]
    except OSError:
        sprueche = []
    return (f'd.wallpaperPlugin = "de.biblix.lebendig";\n'
            f'd.currentConfigGroup = ["Wallpaper", "de.biblix.lebendig", "General"];\n'
            f'd.writeConfig("Szene", {json.dumps(szene)});\n'
            f'd.writeConfig("Farben", {json.dumps(json.dumps(farben))});\n'
            f'd.writeConfig("Sprueche", {json.dumps(chr(10).join(sprueche))});\n')


def diashow_ordner(p, e):
    """Fuellt den Diashow-Ordner mit allen Motiven der gewaehlten Gruppe."""
    gruppe = e.get("diashow_gruppe", "auto")
    if gruppe == "auto":
        gruppe = next((g for i, _, g in hintergruende.alle() if i == e["hintergrund"]), "allgemein")
    DIASHOW_DIR.mkdir(parents=True, exist_ok=True)
    for alt in DIASHOW_DIR.iterdir():
        if alt.is_symlink() or alt.suffix == ".png":
            alt.unlink()
    if gruppe == "eigene":
        quellen = [(f"eigen-{k}", hintergruende.eigenes_bild(m)) for k, m in enumerate(e.get("eigene_bilder", []))
                   if str(m).startswith(hintergruende.EIGEN_DATEI)]
    else:
        quellen = [(mid, hintergruende.rendern(mid, p, HG_DIR, eigene_farben=e.get("hintergrund_eigene_farben", False)))
                   for mid, _, g in hintergruende.alle() if g == gruppe]
    for name, bild in quellen:
        if not bild:
            continue
        ziel = DIASHOW_DIR / f"{name}{Path(bild).suffix}"
        try:
            ziel.symlink_to(bild)
        except OSError:
            shutil.copy(bild, ziel)
    return DIASHOW_DIR


def _monitor_js(mid, p, e, mit_diashow):
    minuten = max(1, int(e.get("diashow_minuten", 30)))
    if mit_diashow:
        return _diashow_js(DIASHOW_DIR, minuten)
    if str(mid).startswith(hintergruende.EIGEN_ORDNER):
        return _diashow_js(hintergruende.eigen_pfad(mid), minuten)
    leb = hintergruende.lebendig(mid)
    if leb:
        return _lebendig_js(p, leb)
    return _bild_js(hintergruende.rendern(mid, p, HG_DIR, eigene_farben=e.get("hintergrund_eigene_farben", False)))


def hintergrund(p, e):
    """Hauptmonitor (Plasma-Bildschirm 0) und weitere Monitore getrennt; Sperrbildschirm = Hauptmonitor."""
    haupt = e["hintergrund"]
    zweiter = e.get("hintergrund_zweiter") or haupt
    if e["diashow"]:
        diashow_ordner(p, e)
    js_haupt = _monitor_js(haupt, p, e, e["diashow"])
    js_zweiter = _monitor_js(zweiter, p, e, e["diashow"] and e.get("diashow_monitore", "beide") == "beide")
    plasma_skript("desktops().forEach(function (d) {\nif (d.screen <= 0) {\n" + js_haupt + "} else {\n" + js_zweiter
                  + "}\nd.reloadConfig();\n});")
    png = hintergruende.rendern(haupt, p, HG_DIR, eigene_farben=e.get("hintergrund_eigene_farben", False))
    # alte Bilder aufraeumen (die letzten 24 behalten, Diashows verweisen darauf)
    bilder = sorted(HG_DIR.glob("*.png"), key=lambda f: f.stat().st_mtime, reverse=True)
    for alt in bilder[24:]:
        alt.unlink(missing_ok=True)
    gruppen = ["Greeter", "Wallpaper", "org.kde.image", "General"]
    kconf("kscreenlockerrc", ["Greeter"], "WallpaperPlugin", "org.kde.image")
    kconf("kscreenlockerrc", gruppen, "Image", f"file://{png}")
    kconf("kscreenlockerrc", gruppen, "PreviewImage", f"file://{png}")
    return png


def klaenge(e):
    if e["klaenge"] == "aus":
        kconf("kdeglobals", "Sounds", "Enable", False)
        return "Klänge: aus"
    kconf("kdeglobals", "Sounds", "Enable", True)
    if e["klaenge"] == "preset":
        thema = "biblix-" + kern.preset(e["preset"]).get("klang", "tech")
    else:
        thema = {"biblix": "biblix", "retro": "biblix-retro", "ruhig": "biblix-ruhig"}[e["klaenge"]]
    kconf("kdeglobals", "Sounds", "Theme", thema)
    # Startklang beim Anmelden
    kconf("plasma_workspace.notifyrc", "Event/startkde", "Action", "Sound" if e["startklang"] else "")
    kconf("plasma_workspace.notifyrc", "Event/startkde", "Sound", "desktop-login.oga")
    return f"Klänge: {thema}"


def effekte(e):
    an = e["animationen"]
    kconf("kdeglobals", "KDE", "AnimationDurationFactor", "1" if an else "0")
    pl = "Plugins"
    oeffnen, schliessen = e["effekt_oeffnen"], e["effekt_schliessen"]
    eigene = an and not (oeffnen == "aus" and schliessen == "aus")
    kconf("kwinrc", pl, "biblix_fensterEnabled", eigene)
    kconf("kwinrc", pl, "scaleEnabled", False if eigene else an)
    kconf("kwinrc", pl, "glideEnabled", False)
    kconf("kwinrc", "Effect-biblix_fenster", "Oeffnen", oeffnen)
    kconf("kwinrc", "Effect-biblix_fenster", "Schliessen", schliessen)
    m = e["effekt_minimieren"]
    kconf("kwinrc", pl, "squashEnabled", an and m == "fliegen")
    kconf("kwinrc", pl, "magiclampEnabled", an and m == "wabern")
    kconf("kwinrc", pl, "biblix_minimierenEnabled", an and m == "ausblenden")
    w = e["arbeitsflaeche"]
    wuerfel_da = Path("/usr/share/kwin/effects/biblix_wuerfel").exists() or \
        any(Path(d).exists() for d in ("/usr/lib/x86_64-linux-gnu/qt6/plugins/kwin/effects/plugins/biblix_wuerfel.so",))
    if w == "wuerfel" and not wuerfel_da:
        w = "gleiten"
    kconf("kwinrc", pl, "biblix_wuerfelEnabled", an and w == "wuerfel")
    kconf("kwinrc", pl, "slideEnabled", an and w == "gleiten")
    kconf("kwinrc", pl, "fadedesktopEnabled", an and w == "ueberblenden")
    kconf("kwinrc", pl, "wobblywindowsEnabled", an and e["wackeln"])
    kconf("kwinrc", pl, "translucencyEnabled", e["durchsichtig_verschieben"])
    kconf("kwinrc", "Effect-translucency", "MoveResize", 70 if e["durchsichtig_verschieben"] else 100)
    kconf("kwinrc", pl, "mouseclickEnabled", e["klick_funken"])
    # KWin 6.3 lädt Effekte beim Neu-Einlesen nicht nach: jeden direkt ein- oder ausschalten
    zustand = {
        "scale": an and not eigene, "glide": False, "biblix_fenster": eigene,
        "squash": an and m == "fliegen", "magiclamp": an and m == "wabern", "biblix_minimieren": an and m == "ausblenden",
        "biblix_wuerfel": an and w == "wuerfel", "slide": an and w == "gleiten", "fadedesktop": an and w == "ueberblenden",
        "wobblywindows": an and e["wackeln"], "translucency": e["durchsichtig_verschieben"], "mouseclick": e["klick_funken"],
    }
    for name, ein in zustand.items():
        dbus("org.kde.KWin", "/Effects", "org.kde.kwin.Effects", "loadEffect" if ein else "unloadEffect", name)
    for name in ("biblix_fenster", "translucency"):
        if zustand[name]:
            dbus("org.kde.KWin", "/Effects", "org.kde.kwin.Effects", "reconfigureEffect", name)
    return "Animationen: " + ("an" if an else "aus")


MANGO = KONFIG / "MangoHud" / "MangoHud.conf"
MANGO_KOPF = "# Biblix-Overlay"


def overlay(p, e):
    """Leistungs-Overlay (MangoHud) in Spielen, im Biblix-Look. Startet versteckt, Shift rechts + F12 blendet es ein.
    Eine eigene MangoHud.conf (ohne Biblix-Kopfzeile) bleibt unangetastet."""
    art = e.get("overlay", "ausfuehrlich")
    try:
        alt = MANGO.read_text(encoding="utf-8")
    except OSError:
        alt = ""
    if alt and not alt.startswith((MANGO_KOPF, "# MangoHud unter Biblix")):
        return "Overlay: eigene MangoHud.conf bleibt"
    h = lambda k: p[k].lstrip("#")
    z = [f"{MANGO_KOPF} (von Biblix Design erzeugt. Eigene Einstellungen? Diese Zeile loeschen, dann bleibt die Datei.)",
         "# Ein/aus im Spiel: Shift rechts + F12",
         "legacy_layout=false", "no_display", "toggle_hud=Shift_R+F12", "position=top-left",
         "round_corners=10", "background_alpha=0.82", f"background_color={h('grund')}", "font_size=20",
         f"text_color={h('text')}", f"gpu_color={h('akzent')}", f"cpu_color={h('akzent2')}",
         f"vram_color={h('akzent')}", f"ram_color={h('akzent2')}", f"frametime_color={h('akzent')}",
         f"engine_color={h('leise')}", "fps_color_change", f"fps_color=e24b4a,{h('akzent2')},{h('akzent')}",
         "fps_value=30,60", "fps"]
    if art == "kompakt":
        z += ["horizontal", "hud_compact", "gpu_stats", "gpu_temp", "cpu_stats", "cpu_temp", "frametime=0"]
    else:
        z += ["custom_text_center=BIBLIX", "frame_timing", "gpu_stats", "gpu_temp", "gpu_power",
              "cpu_stats", "cpu_temp", "ram", "vram"]
    MANGO.parent.mkdir(parents=True, exist_ok=True)
    MANGO.write_text("\n".join(z) + "\n", encoding="utf-8")
    # Steam (Flatpak) laedt MangoHud in jedes Spiel; ohne Tastendruck sieht man nichts
    if shutil.which("flatpak"):
        if art == "aus":
            _lauf("flatpak", "override", "--user", "--env=MANGOHUD=0", "com.valvesoftware.Steam")
        else:
            _lauf("flatpak", "override", "--user", "--env=MANGOHUD=1", f"--env=MANGOHUD_CONFIGFILE={MANGO}",
                  "com.valvesoftware.Steam")
    return "Overlay: " + dict(kern.WAHL["overlay"])[art]


def arbeitsflaechen(e):
    """Eine Arbeitsfläche (Standard) oder vier für Würfel und Co. Bei einer fliegt die Arbeitsflächen-Anzeige
    (Pager) aus der Taskleiste; Fenster der entfernten Flächen landet KWin auf der verbleibenden."""
    if e["arbeitsflaechen"] == "vier":
        arbeitsflaechen_sicherstellen(4)
        return "Arbeitsflächen: vier"
    try:
        r = subprocess.run(["gdbus", "call", "--session", "--dest", "org.kde.KWin", "--object-path", "/VirtualDesktopManager",
                            "--method", "org.freedesktop.DBus.Properties.Get", "org.kde.KWin.VirtualDesktopManager", "desktops"],
                           capture_output=True, text=True, timeout=10)
        ids = re.findall(r"\((?:uint32 )?\d+, '([^']+)'", r.stdout)
    except (OSError, subprocess.TimeoutExpired):
        ids = []
    for i in ids[1:]:
        dbus("org.kde.KWin", "/VirtualDesktopManager", "org.kde.KWin.VirtualDesktopManager", "removeDesktop", i)
    plasma_skript('panels().forEach(function (p) { p.widgets("org.kde.plasma.pager").forEach(function (w) { w.remove(); }); });')
    return "Arbeitsflächen: eine"


def arbeitsflaechen_sicherstellen(anzahl):
    """Der Würfel braucht mehrere Arbeitsflächen: fehlende über KWin anlegen (nur wenn es weniger als 2 gibt)."""
    try:
        r = subprocess.run(["kreadconfig6", "--file", "kwinrc", "--group", "Desktops", "--key", "Number", "--default", "1"],
                           capture_output=True, text=True, timeout=10)
        jetzt = int(r.stdout.strip() or 1)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return
    if jetzt >= 2:
        return
    for i in range(jetzt, anzahl):
        dbus("org.kde.KWin", "/VirtualDesktopManager", "org.kde.KWin.VirtualDesktopManager", "createDesktop",
             i, f"Arbeitsfläche {i + 1}")


def kwin_neu_laden():
    dbus("org.kde.KWin", "/KWin", "org.kde.KWin", "reconfigure")


# ---------------------------------------------------------------- Taskleiste und Startmenue

def plasma_bereit(sekunden=25):
    """Direkt nach dem Anmelden kennt Plasma die Bildschirme der Leisten erst nach ein paar Sekunden.
    Vorher eingreifen fuehrt zu doppelten Taskleisten, also warten (hoechstens `sekunden`)."""
    if not shutil.which("gdbus"):
        return True
    ende = time.time() + sekunden
    while time.time() < ende:
        out = plasma_skript('var ok = screenCount > 0 && panels().every(function (p) { return p.screen >= 0; });'
                            ' print(ok ? "PLASMA-BEREIT" : "PLASMA-WARTET");')
        if "PLASMA-BEREIT" in out:
            return True
        time.sleep(1)
    return False


WELTEN = {"bibi-tech": "tower", "bibi-budget-bank": "bank", "bibi-mac": "mac", "bibi-delivery": "delivery",
          "bibiplexx": "plexx", "nassmacher": "nass"}
WELT_KNOPF = {"bank": "#c9a227", "mac": "#ffc72c", "plexx": "#ff8a3d", "nass": "#ffb020"}


def leisten_welt(e):
    """Welt der Biblix-Fensterleiste: folgt dem Preset (wenn Welten an), sonst Typenschild."""
    if not e.get("leiste_welten", True) or e.get("eigene_farben"):
        return "typenschild"
    return WELTEN.get(e["preset"], "typenschild")


def taskleiste(e, p):
    """Panels per Plasma-Skript einrichten. Biblix-Startmenue rein, Kickoff raus (oder umgekehrt)."""
    if not plasma_bereit():
        return "Taskleiste: Plasma war noch nicht bereit, nichts verändert"
    menue = {"bibi": "de.biblix.startmenue", "vollbild": "de.biblix.startmenue", "klassisch": "org.kde.plasma.kickoff"}[e["startmenue"]]
    stil = "vollbild" if e["startmenue"] == "vollbild" else "panel"
    deckkraft = {"milchglas": 2, "undurchsichtig": 1, "adaptiv": 0}[e["transparenz"]]
    icon = "biblix" if e["startknopf"] == "biblix" else f"/usr/share/biblix/design/logos/{e['preset']}.svg"
    biblix_leiste = e.get("leiste_stil", "typenschild") == "typenschild"
    aufgabe_typ = "de.biblix.leiste" if biblix_leiste else "org.kde.plasma.icontasks"
    uhr_typ = "de.biblix.uhr" if biblix_leiste else "org.kde.plasma.digitalclock"
    welt = leisten_welt(e)
    knopf = "bknopf" if biblix_leiste and e["startknopf"] == "biblix" else "symbol"
    leisten_farben = json.dumps({k: p[k] for k in ("grund", "flaeche", "karte", "rand", "text", "leise", "akzent", "akzent2")})
    js = f"""
var menueTyp = "{menue}";
var umgebaut = false;
var starter = ["org.kde.plasma.kickoff", "org.kde.plasma.kicker", "org.kde.plasma.kickerdash", "de.biblix.startmenue"];
// Doppelte Leisten aufraeumen: hoechstens eine Leiste pro Bildschirm und Rand
// (entstand, wenn Plasma beim Anmelden die Bildschirme noch nicht kannte)
var gesehen = {{}};
panels().forEach(function (p) {{
    var k = p.screen + "/" + p.location;
    if (p.screen >= 0 && gesehen[k]) {{ p.remove(); }} else {{ gesehen[k] = true; }}
}});
var ps = panels();
// Monitore: Taskleiste auf jedem Bildschirm (oder nur auf dem Hauptmonitor)
var modus = "{e['monitore']}";
var vorhanden = {{}};
var bekannt = true;
ps.forEach(function (p) {{ vorhanden[p.screen] = p; if (p.screen < 0) bekannt = false; }});
if (modus != "haupt") {{
    // Nur ergaenzen, wenn Plasma alle Bildschirme schon kennt, sonst entstehen doppelte Leisten
    for (var s = 0; bekannt && s < screenCount; s++) {{
        if (!vorhanden[s]) {{
            var n = new Panel("org.kde.panel");
            n.location = "bottom";
            n.screen = s;
            n.addWidget(menueTyp);
            var t = n.addWidget("{aufgabe_typ}");
            t.currentConfigGroup = ["General"];
            t.writeConfig("showOnlyCurrentScreen", true);
            if (modus == "gleich") {{ n.addWidget("org.kde.plasma.systemtray"); n.addWidget("{uhr_typ}"); }}
            vorhanden[s] = n;
        }}
    }}
}} else {{
    ps.forEach(function (p) {{ if (p.screen != 0) p.remove(); }});
}}
panels().forEach(function (p) {{
    p.floating = {str(e['taskleiste'] == 'schwebend').lower()};
    p.lengthMode = "{'fit' if e['taskleiste'] == 'dock' else 'fill'}";
    p.alignment = "{'center' if e['taskleiste'] == 'dock' else 'left'}";
    p.height = {44 if e['taskleiste'] != 'dock' else 52};
    try {{ p.opacity = {['"adaptive"', '"opaque"', '"translucent"'][deckkraft]}; }} catch (x) {{}}
    // Gewuenschte Reihenfolge: Startmenue zuerst (bei "Mitte": Abstand | Startmenue + Fenster | Abstand),
    // dann alle anderen Widgets wie bisher. Weicht die Leiste davon ab, wird sie neu aufgebaut
    // (angeheftete Apps der Fensterliste bleiben erhalten).
    var aufgaben = ["org.kde.plasma.icontasks", "org.kde.plasma.taskmanager", "de.biblix.leiste"];
    var uhren = ["org.kde.plasma.digitalclock", "de.biblix.uhr"];
    function info(w) {{
        var i = {{ typ: w.type, conf: {{}} }};
        w.currentConfigGroup = ["General"];
        if (aufgaben.indexOf(w.type) >= 0) {{
            var l = w.readConfig("launchers", "");
            if (l && l.length) i.conf.launchers = l;
        }}
        if (w.type == "org.kde.plasma.panelspacer" && w.readConfig("biblix", "") == "1") i.biblix = true;
        return i;
    }}
    var jetzt = p.widgets().map(info);
    var behalten = jetzt.filter(function (i) {{ return starter.indexOf(i.typ) < 0 && !i.biblix; }});
    // Fensterleiste und Uhr: Biblix (Typenschild) oder KDE, angeheftete Apps wandern mit
    // (Kopien: "jetzt" muss unveraendert bleiben, sonst sieht der Vergleich unten keinen Unterschied)
    behalten = behalten.map(function (i) {{
        var typ = i.typ;
        if (aufgaben.indexOf(typ) >= 0) typ = "{aufgabe_typ}";
        else if (uhren.indexOf(typ) >= 0) typ = "{uhr_typ}";
        return {{ typ: typ, conf: i.conf, biblix: i.biblix }};
    }});
    // Instrumentenfeld (Fassung der Symbole unten rechts) direkt vor den Systemabschnitt, nur beim Typenschild
    behalten = behalten.filter(function (i) {{ return i.typ != "de.biblix.instrumentenfeld"; }});
    var tray = behalten.map(function (i) {{ return i.typ; }}).indexOf("org.kde.plasma.systemtray");
    if ({str(biblix_leiste).lower()} && tray >= 0) behalten.splice(tray, 0, {{ typ: "de.biblix.instrumentenfeld", conf: {{}} }});
    var mitte = "{e['startmenue_position']}" == "mitte" && "{e['taskleiste']}" != "dock";
    var abstand = {{ typ: "org.kde.plasma.panelspacer", conf: {{ biblix: "1", expanding: true }}, biblix: true }};
    var soll;
    if (mitte) {{
        var vorn = behalten.filter(function (i) {{ return aufgaben.indexOf(i.typ) >= 0; }});
        var rest = behalten.filter(function (i) {{ return aufgaben.indexOf(i.typ) < 0; }});
        soll = [abstand, {{ typ: menueTyp, conf: {{}} }}].concat(vorn, [abstand], rest);
    }} else {{
        soll = [{{ typ: menueTyp, conf: {{}} }}].concat(behalten);
    }}
    var ist = jetzt.map(function (i) {{ return i.typ + (i.biblix ? "*" : ""); }}).join(",");
    var sollText = soll.map(function (i) {{ return i.typ + (i.biblix ? "*" : ""); }}).join(",");
    if (ist != sollText) {{
        p.widgets().forEach(function (w) {{ w.remove(); }});
        soll.forEach(function (i) {{
            var w = p.addWidget(i.typ);
            w.currentConfigGroup = ["General"];
            for (var k in i.conf) w.writeConfig(k, i.conf[k]);
        }});
        umgebaut = true;
    }}
    p.widgets().forEach(function (w) {{
        if (w.type == "de.biblix.startmenue") {{
            w.currentConfigGroup = ["General"];
            w.writeConfig("icon", "{icon}");
            w.writeConfig("stil", "{stil}");
            w.writeConfig("knopf", "{knopf}");
            w.writeConfig("knopfFarbe", "{WELT_KNOPF.get(welt, '#ffd400')}");
        }}
        if (w.type == "de.biblix.leiste") {{
            w.currentConfigGroup = ["General"];
            w.writeConfig("welt", "{welt}");
            w.writeConfig("lack", {str(bool(e.get('leiste_lack'))).lower()});
            w.writeConfig("farben", {json.dumps(leisten_farben)});
        }}
        if (w.type == "de.biblix.instrumentenfeld") {{
            w.currentConfigGroup = ["General"];
            w.writeConfig("welt", "{welt}");
            w.writeConfig("farben", {json.dumps(leisten_farben)});
        }}
        if (w.type == "de.biblix.uhr") {{
            w.currentConfigGroup = ["General"];
            w.writeConfig("welt", "{welt}");
            w.writeConfig("farben", {json.dumps(leisten_farben)});
        }}
        if (aufgaben.indexOf(w.type) >= 0) {{
            w.currentConfigGroup = ["General"];
            w.writeConfig("showOnlyCurrentScreen", {str(e['monitore'] == 'beide').lower()});
        }}
    }});
}});
print(umgebaut ? "BIBLIX-UMGEBAUT" : "BIBLIX-OK");
"""
    plasma_skript(js)
    # Spielereien in der Taskleiste
    extras = [("spielmodus_anzeige", "de.biblix.spielmodus"), ("update_symbol", "de.biblix.updates"),
              ("leistungs_anzeige", "de.biblix.leistung"), ("kopfhoerer_schalter", "de.biblix.kopfhoerer")]
    js2 = "var p = panels().filter(function (x) { return x.screen == 0; })[0] || panels()[0];\nif (p) {\n"
    for schluessel, plasmoid in extras:
        if e.get(schluessel):
            js2 += f'  if (p.widgets("{plasmoid}").length == 0) {{ var w = p.addWidget("{plasmoid}"); }}\n'
        else:
            js2 += f'  p.widgets("{plasmoid}").forEach(function (w) {{ w.remove(); }});\n'
    js2 += "}\n"
    plasma_skript(js2)
    return "Taskleiste: " + dict(kern.WAHL["taskleiste"])[e["taskleiste"]]


def sperrbildschirm(e):
    kconf("kscreenlockerrc", ["Greeter", "LnF", "General"], "biblixStil", e["sperrbildschirm"])
    kconf("kscreenlockerrc", ["Greeter", "LnF", "General"], "alwaysShowClock", e["sperrbildschirm"] != "schlicht")


def ladebildschirm(p, e):
    """Eigenes Look-and-Feel-Paket nur fuer den Startbildschirm nach der Anmeldung."""
    d = DATEN / "plasma" / "look-and-feel" / "de.biblix.splash"
    s = d / "contents" / "splash"
    s.mkdir(parents=True, exist_ok=True)
    (d / "metadata.json").write_text(json.dumps({
        "KPackageStructure": "Plasma/LookAndFeel",
        "KPlugin": {"Id": "de.biblix.splash", "Name": "Biblix", "Description": "Biblix-Startbildschirm",
                    "Authors": [{"Name": "Biblix"}], "License": "GPL", "Version": "2.0"},
        "X-Plasma-APIVersion": "2"}, indent=1), encoding="utf-8")
    vorlage = (DESIGN / "splash" / "Splash.qml").read_text(encoding="utf-8")
    ersetzen = {"@GRUND@": p["grund"], "@FLAECHE@": p["flaeche"], "@TEXT@": p["text"], "@AKZENT@": p["akzent"],
                "@LEISE@": p["leise"], "@STIL@": e["ladeanimation"], "@KARTE@": p["karte"]}
    for a, b in ersetzen.items():
        vorlage = vorlage.replace(a, b)
    (s / "Splash.qml").write_text(vorlage, encoding="utf-8")
    bilder = s / "images"
    bilder.mkdir(exist_ok=True)
    (bilder / "logo.svg").write_text(grafik.svg(
        f'<rect width="120" height="120" rx="26" fill="{p["karte"]}"/>'
        + grafik.prompt_b_form(p["text"], p["akzent"], 7, cursor=False)), encoding="utf-8")
    (bilder / "mutter.svg").write_text(grafik.schrauben_b(p), encoding="utf-8")
    kconf("ksplashrc", "KSplash", "Theme", "de.biblix.splash")
    kconf("ksplashrc", "KSplash", "Engine", "KSplashQML")


def konsole(p, e):
    d = DATEN / "konsole"
    d.mkdir(parents=True, exist_ok=True)
    if e["terminal_farben"]:
        (d / "Biblix.colorscheme").write_text(terminal.farbschema(p, "Biblix"), encoding="utf-8")
        (d / "Biblix.profile").write_text(terminal.profil("Biblix"), encoding="utf-8")
        kconf("konsolerc", "Desktop Entry", "DefaultProfile", "Biblix.profile")
    else:
        kconf("konsolerc", "Desktop Entry", "DefaultProfile", None)
    bashrc = Path.home() / ".bashrc"
    try:
        text = bashrc.read_text(encoding="utf-8") if bashrc.exists() else ""
    except OSError:
        return
    zeilen = [z for z in text.splitlines() if "# Biblix-Prompt" not in z]
    if e["terminal_prompt"]:
        zeilen.append(PROMPT_ZEILE)
    neu = "\n".join(zeilen) + "\n"
    if neu != text:
        bashrc.write_text(neu, encoding="utf-8")


def firefox(p, e):
    seite = DATEN / "biblix" / "startseite" / "index.html"
    if e["firefox_startseite"]:
        seite.parent.mkdir(parents=True, exist_ok=True)
        vorlage = (DESIGN / "startseite" / "index.html").read_text(encoding="utf-8")
        for k in ("grund", "flaeche", "karte", "rand", "text", "leise", "akzent", "akzent2", "auf_akzent"):
            vorlage = vorlage.replace(f"@{k.upper()}@", p[k])
        try:
            sprueche = (DESIGN / "sprueche.txt").read_text(encoding="utf-8").splitlines()
        except OSError:
            sprueche = ["AUF BIBLIX GEHT DAS."]
        sprueche = [s.strip() for s in sprueche if s.strip() and not s.startswith("#")]
        vorlage = vorlage.replace("@SPRUECHE@", json.dumps(sprueche, ensure_ascii=False))
        seite.write_text(vorlage, encoding="utf-8")
    profile = Path.home() / ".mozilla" / "firefox"
    if not profile.exists():
        return
    for prefs in profile.glob("*/prefs.js"):
        user = prefs.parent / "user.js"
        try:
            text = user.read_text(encoding="utf-8") if user.exists() else ""
        except OSError:
            continue
        zeilen = [z for z in text.splitlines() if "biblix-startseite" not in z]
        if e["firefox_startseite"]:
            zeilen.append(f'user_pref("browser.startup.homepage", "file://{seite}"); // biblix-startseite')
            zeilen.append('user_pref("browser.startup.page", 1); // biblix-startseite')
        user.write_text("\n".join(zeilen) + ("\n" if zeilen else ""), encoding="utf-8")


def system_teile(p, e, warten=True):
    """Bootmenue, Startbildschirm und Anmeldung: braucht Admin-Rechte (pkexec, einmal Passwort)."""
    auftrag = {"palette": {k: p[k] for k in kern.FARBNAMEN}, "name": p["name"], "dunkel": p["dunkel"],
               "hintergrund": hintergruende.system_motiv(e["hintergrund"]), "bootmenue": e["bootmenue_mitfaerben"]}
    if not Path(SYSTEM_HELFER).exists():
        return "Bootmenü: Helfer fehlt"
    if os.geteuid() == 0:
        r = _lauf(SYSTEM_HELFER, eingabe=json.dumps(auftrag))
    else:
        r = _lauf("pkexec", SYSTEM_HELFER, eingabe=json.dumps(auftrag))
    return "Bootmenü und Startbildschirm: " + ("übernommen" if r == 0 else "nicht geändert")


# ================================================================ Alles

def palette_schreiben(p):
    PALETTE.parent.mkdir(parents=True, exist_ok=True)
    PALETTE.write_text(json.dumps(p, indent=1, ensure_ascii=False), encoding="utf-8")


def alles(e=None, system=True, melden=print):
    """Wendet alles an. melden(text) wird nach jedem Schritt aufgerufen (Fortschritt in der App)."""
    e = e or kern.laden()
    p = kern.palette(e)
    try:
        akt = json.loads(AKTUELL.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        akt = {}
    alt_system = akt.get("system")
    schritte = [
        ("Farben", lambda: farben(p, akt)),
        ("Fensterrahmen", lambda: rahmen(p, e, akt)),
        ("Symbole", lambda: symbol_thema(p, e, akt)),
        ("Mauszeiger", lambda: mauszeiger(p, e, akt)),
        ("Hintergrund", lambda: hintergrund(p, e)),
        ("Animationen", lambda: effekte(e)),
        ("Klänge", lambda: klaenge(e)),
        ("Taskleiste", lambda: taskleiste(e, p)),
        ("Arbeitsflächen", lambda: arbeitsflaechen(e)),
        ("Overlay", lambda: overlay(p, e)),
        ("Sperrbildschirm", lambda: sperrbildschirm(e)),
        ("Ladebildschirm", lambda: ladebildschirm(p, e)),
        ("Terminal", lambda: konsole(p, e)),
        ("Firefox", lambda: firefox(p, e)),
    ]
    for name, f in schritte:
        try:
            r = f()
            melden(r if isinstance(r, str) else name)
        except Exception as fehler:  # ein Teil darf die anderen nicht aufhalten
            melden(f"{name}: Fehler ({fehler})")
    kwin_neu_laden()
    palette_schreiben(p)
    # Systemteile nur, wenn sich Farben oder Hintergrund geaendert haben (Passwort nur dann)
    neu_system = json.dumps([p[k] for k in kern.FARBNAMEN] + [e["hintergrund"], e["bootmenue_mitfaerben"]])
    if system and e["bootmenue_mitfaerben"] and neu_system != alt_system:
        r = system_teile(p, e)
        melden(r)
        if "übernommen" in r:
            akt["system"] = neu_system
    AKTUELL.parent.mkdir(parents=True, exist_ok=True)
    AKTUELL.write_text(json.dumps(akt), encoding="utf-8")
    melden("Fertig")
    return p
