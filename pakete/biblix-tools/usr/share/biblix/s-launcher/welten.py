"""Welten fuer den S-Launcher: Aussehen, Woerter, Uebergaenge und Klaenge.

Die Welt folgt automatisch dem Preset aus Biblix Design (Bibi Tech = Tower,
Bibi Mac = Bestelltheke) oder wird im S-Launcher fest gewaehlt.
Einstellungen: ~/.config/biblix/s-launcher.json
"""
import json
import math
import os
import random
import shutil
from pathlib import Path

from PyQt6 import sip
from PyQt6.QtCore import (
    QAbstractAnimation, QEasingCurve, QPointF, QProcess, QPropertyAnimation, QRectF,
    QSequentialAnimationGroup, QTimer, QVariantAnimation, Qt, pyqtSignal,
)
from PyQt6.QtGui import (
    QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF,
)
from PyQt6.QtWidgets import (
    QCheckBox, QFrame, QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QToolButton, QVBoxLayout, QWidget,
)

KONFIG = Path(os.environ.get("BIBLIX_KONFIG_DIR") or Path.home() / ".config/biblix")
EINSTELLUNGEN = KONFIG / "s-launcher.json"
PALETTE = KONFIG / "palette.json"
HAUSMARKE_DIRS = [Path(p) for p in os.environ.get("BIBLIX_HAUSMARKE_DIR", "/usr/share/biblix/hausmarke.d").split(os.pathsep)]
KLANG_DIR = Path(__file__).with_name("klaenge")

GOLD = "#d4a73c"
AUF_GOLD = "#2a1f05"


def gold_text(f):
    """Gold fuer Schrift: auf hellem Grund dunkler, sonst zu blass."""
    return GOLD if f.get("dunkel", True) else "#8a6510"

STANDARD = {"welt": "auto", "animationen": "voll", "klaenge": False, "_stand": 1}

# Klassische S-Launcher-Farben, falls Biblix Design noch nichts geschrieben hat
GRUNDFARBEN = {
    "grund": "#0b1820", "flaeche": "#0d1f28", "karte": "#0f222c", "rand": "#1f3946",
    "text": "#e3f3f8", "leise": "#8fb0bf", "akzent": "#0aa5c6", "akzent_hell": "#3fd0ee",
    "akzent_dunkel": "#0f6e86", "akzent2": "#ffd23f", "auf_akzent": "#001319",
    "auf_akzent2": "#1b1500", "auswahl": "#13323f", "dunkel": True, "preset": "",
}

NAV_SCHLUESSEL = ["hausmarke", "discover", "games", "categories", "installed", "accessories", "updates"]

WELTEN = {
    "schlicht": {
        "name": "Schaufenster", "info": "Schlicht, passt zu allem", "fertig": True,
        "uebergang": "blende", "preset": None,
        "nav": {"hausmarke": "Hausmarke Bibi", "discover": "Entdecken", "games": "Spiele",
                "categories": "Kategorien", "installed": "Installiert", "accessories": "Zubehör",
                "updates": "Updates"},
        "untertitel": "Tausende Apps von Flathub. Ein Klick, fertig.",
        "installieren": "Installieren", "laeuft": "Läuft …",
        "auftrag": "Installiere {name}", "fertig_text": "{name} ist installiert.",
        "bereit": "Bereit.",
        "klaenge": {"seite": None, "start": None, "fertig": "fertig.wav"},
    },
    "tower": {
        "name": "Tower", "info": "Bibi Tech · mit Aufzug", "fertig": True,
        "uebergang": "tuer", "preset": "bibi-tech",
        "nav": {"hausmarke": "Hausmarke Bibi", "discover": "Entdecken", "games": "Spiele",
                "categories": "Kategorien", "installed": "Installiert", "accessories": "Zubehör",
                "updates": "Haustechnik"},
        "etagen": {"hausmarke": "EG", "discover": "1", "games": "2", "categories": "3",
                   "installed": "4", "accessories": "5", "updates": "UG"},
        "untertitel": "Willkommen im Tower. Jeder Bereich hat sein eigenes Stockwerk.",
        "installieren": "Installieren", "laeuft": "Fährt …",
        "auftrag": "Lastenaufzug bringt {name} nach oben", "fertig_text": "Angekommen: {name} ist jetzt im Haus.",
        "bereit": "Aufzug bereit.",
        "klaenge": {"seite": None, "start": None, "fertig": "tower-fertig.wav"},
    },
    "theke": {
        "name": "Bestelltheke", "info": "Bibi Mac · mit Kassa", "fertig": True,
        "uebergang": "schieben", "preset": "bibi-mac",
        "nav": {"hausmarke": "Hausmarke Bibi", "discover": "Tagesangebot", "games": "Spiele",
                "categories": "Speisekarte", "installed": "Mein Tablett", "accessories": "Beilagen",
                "updates": "Nachschub"},
        "untertitel": "Tausende Apps von Flathub. Bestellen, kurz warten, fertig.",
        "installieren": "Bestellen", "laeuft": "Wird zubereitet …",
        "auftrag": "Bestellung Nr. {nr}: {name} wird zubereitet", "fertig_text": "Bestellung Nr. {nr} ist fertig: {name}. Guten Appetit!",
        "bereit": "Kassa offen.",
        "klaenge": {"seite": None, "start": "kassa.wav", "fertig": "bestellung-fertig.wav"},
    },
    "lieferung": {"name": "Lieferung", "info": "Bibi Delivery", "fertig": False, "preset": "bibi-delivery"},
    "kino": {"name": "Kino", "info": "Bibiplexx", "fertig": False, "preset": "bibiplexx"},
    "tresor": {"name": "Tresor", "info": "Bibi Budget Bank", "fertig": False, "preset": "bibi-budget-bank"},
    "rutsche": {"name": "Rutsche", "info": "Nassmacher", "fertig": False, "preset": "nassmacher"},
}
NAV_KLAR = WELTEN["schlicht"]["nav"]


def alive(obj):
    return obj is not None and not sip.isdeleted(obj)


# ---------------------------------------------------------------- Einstellungen

def laden():
    e = dict(STANDARD)
    try:
        gespeichert = json.loads(EINSTELLUNGEN.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        gespeichert = {}
    if isinstance(gespeichert, dict):
        e.update({k: v for k, v in gespeichert.items() if k in STANDARD})
        # Seit 1.3.2: Klaenge standardmaessig aus (waren zu laut und zu oft)
        if gespeichert.get("_stand", 0) < 1:
            e["klaenge"] = False
            e["_stand"] = 1
    if e["welt"] != "auto" and not WELTEN.get(e["welt"], {}).get("fertig"):
        e["welt"] = "auto"
    if e["animationen"] not in ("voll", "dezent", "aus"):
        e["animationen"] = "voll"
    return e


def speichern(e):
    try:
        KONFIG.mkdir(parents=True, exist_ok=True)
        EINSTELLUNGEN.write_text(json.dumps(e, indent=2), encoding="utf-8")
    except OSError:
        pass


def farben():
    f = dict(GRUNDFARBEN)
    try:
        pal = json.loads(PALETTE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pal = {}
    if isinstance(pal, dict):
        f.update({k: v for k, v in pal.items() if k in GRUNDFARBEN})
    return f


# ---------------------------------------------------------------- Weltfarben und Weltstil

# Firmenfarben der Welten (wie die Presets in Biblix Design), damit eine Welt immer gleich aussieht
WELT_PRESETS = {
    "tower": {
        "dunkel": {"grund": "#0f141c", "flaeche": "#1a2029", "karte": "#232a35", "rand": "#313a48",
                   "text": "#e8ecf2", "leise": "#8b95a5", "akzent": "#378add", "akzent2": "#ffd400"},
        "hell": {"grund": "#e9edf2", "flaeche": "#f7f9fb", "karte": "#ffffff", "rand": "#d3d9e1",
                 "text": "#18202b", "leise": "#5b6575", "akzent": "#1f6fc2", "akzent2": "#d9a400"},
    },
    "theke": {
        "dunkel": {"grund": "#2a0d0d", "flaeche": "#3a1313", "karte": "#4b1a1a", "rand": "#6e2a2a",
                   "text": "#fff4dc", "leise": "#e0b8a8", "akzent": "#ffc72c", "akzent2": "#e63131"},
        "hell": {"grund": "#fff1d6", "flaeche": "#fff8ea", "karte": "#ffffff", "rand": "#f0d2a0",
                 "text": "#3a1010", "leise": "#8a5a50", "akzent": "#e63131", "akzent2": "#f2a900"},
    },
}


def _text_auf(c):
    q = QColor(c)
    hell = 0.2126 * q.redF() + 0.7152 * q.greenF() + 0.0722 * q.blueF()
    return "#0b0d12" if hell > 0.55 else "#ffffff"


def welt_farben(welt_id, design):
    """Palette fuer den S-Launcher: Tower und Theke bringen ihre eigenen Farben mit,
    das Schaufenster nimmt die Farben aus Biblix Design. Hell/Dunkel folgt immer Biblix Design."""
    vorlage = WELT_PRESETS.get(welt_id)
    if not vorlage:
        return dict(design)
    f = dict(vorlage["dunkel" if design.get("dunkel", True) else "hell"])
    f["dunkel"] = design.get("dunkel", True)
    f["preset"] = design.get("preset", "")
    f["akzent_hell"] = mischen(f["akzent"], "#ffffff", 0.25).name()
    f["akzent_dunkel"] = mischen(f["akzent"], "#000000", 0.25).name()
    f["auf_akzent"] = _text_auf(f["akzent"])
    f["auf_akzent2"] = _text_auf(f["akzent2"])
    f["auswahl"] = mischen(f["flaeche"], f["akzent"], 0.35).name()
    return f


def muster(welt_id, f):
    """Kachelbares Hintergrundmuster je Welt als PNG im Cache (fuer das Stylesheet)."""
    if welt_id not in ("tower", "theke"):
        return None
    ziel = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "biblix" / "s-launcher"
    datei = ziel / f"muster-v1-{welt_id}-{f['grund'].lstrip('#')}.png"
    if datei.is_file():
        return datei
    try:
        ziel.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    if welt_id == "tower":
        # Bauplan-Raster: feine Linien, jede vierte kraeftiger
        pm = QPixmap(96, 96)
        pm.fill(QColor(f["grund"]))
        p = QPainter(pm)
        for i in range(0, 96, 24):
            p.setPen(QPen(mit_alpha(f["akzent"], 46 if i == 0 else 20), 1))
            p.drawLine(i, 0, i, 96)
            p.drawLine(0, i, 96, i)
        p.end()
    else:
        # Diner-Boden: grosse Karos, kaum sichtbar
        pm = QPixmap(80, 80)
        pm.fill(QColor(f["grund"]))
        p = QPainter(pm)
        karo = mischen(f["grund"], "#000000" if f["dunkel"] else "#c06030", 0.14 if f["dunkel"] else 0.07)
        p.fillRect(0, 0, 40, 40, karo)
        p.fillRect(40, 40, 40, 40, karo)
        p.end()
    return datei if pm.save(str(datei)) else None


MONO = '"DejaVu Sans Mono", "Noto Sans Mono", monospace'


def zusatz_stil(welt_id, f):
    """Stylesheet, das eine Welt ueber den ganzen S-Launcher legt (wird an den Grundstil angehaengt)."""
    bild = muster(welt_id, f)
    hinter = f'background-image: url("{bild.as_posix()}");' if bild else ""
    if welt_id == "tower":
        return f"""
#page {{ background-color: {f['grund']}; {hinter} }}
QLabel#h1 {{ font-family: {MONO}; font-size: 21pt; font-weight: 800; color: {f['akzent2']}; }}
QLabel#h2 {{ font-family: {MONO}; color: {f['akzent_hell']}; }}
QLabel#brand {{ font-family: {MONO}; color: {f['akzent2']}; }}
QLabel#weltname {{ font-family: {MONO}; }}
#sidebar {{ background: {f['grund']}; border-right: 3px solid {f['rand']}; }}
QListWidget#nav::item {{ font-family: {MONO}; padding: 9px 10px; margin: 3px 10px; border-radius: 3px;
    border: 1px solid {f['rand']}; background: {f['karte']}; }}
QListWidget#nav::item:hover {{ border-color: {f['akzent']}; background: {f['flaeche']}; }}
QListWidget#nav::item:selected {{ background: {f['auswahl']}; color: {f['akzent2']}; border: 1px solid {f['akzent2']}; }}
#topbar {{ background: {f['grund']}; border-bottom: 2px solid {f['rand']}; }}
QLineEdit {{ border-radius: 3px; font-family: {MONO}; }}
QPushButton {{ border-radius: 3px; font-family: {MONO}; }}
QFrame#card {{ border-radius: 4px; border: 1px solid {f['rand']}; border-top: 3px solid {f['akzent']}; }}
QFrame#card:hover {{ border-color: {f['akzent2']}; border-top: 3px solid {f['akzent2']}; }}
QFrame#panel {{ border-radius: 4px; border-left: 4px solid {f['akzent']}; }}
QFrame#hero {{ border-radius: 4px; }}
#statusbar {{ background: #05070a; border-top: 2px solid {f['rand']}; }}
#statusbar QLabel {{ color: {f['akzent2']}; font-family: {MONO}; }}
QProgressBar::chunk {{ background: {f['akzent2']}; border-radius: 0; }}
"""
    if welt_id == "theke":
        rot, gelb, creme, braun = "#e63131", "#ffc72c", "#fff4dc", "#3a1010"
        titel = gelb if f["dunkel"] else rot
        return f"""
#page {{ background-color: {f['grund']}; {hinter} }}
QLabel#h1 {{ font-size: 25pt; font-weight: 900; color: {titel}; }}
QLabel#h2 {{ font-size: 14pt; font-weight: 900; color: {titel}; }}
QLabel#brand {{ color: {gelb}; font-weight: 900; }}
QLabel#slogan {{ color: {creme}; }}
QLabel#weltname {{ color: #ffd9c0; }}
#sidebar {{ background: {rot}; border-right: 4px solid {gelb}; }}
#sidebar QLabel#muted {{ color: #ffd9c0; }}
QListWidget#nav {{ color: {creme}; }}
QListWidget#nav::item {{ padding: 10px 14px; margin: 3px 10px; border-radius: 19px; font-weight: 700; color: {creme}; }}
QListWidget#nav::item:hover {{ background: #c92424; }}
QListWidget#nav::item:selected {{ background: {gelb}; color: {braun}; }}
#topbar {{ background: {rot}; border-bottom: 4px solid {gelb}; }}
#topbar QPushButton {{ background: #c92424; color: {creme}; border-color: #ff6b5e; }}
QLineEdit {{ border-radius: 19px; padding: 7px 16px; background: {creme}; color: {braun}; border: 2px solid {gelb}; }}
QPushButton {{ border-radius: 16px; font-weight: 700; }}
QPushButton#primary {{ background: {gelb}; border-color: {gelb}; color: {braun}; border-radius: 16px; }}
QPushButton#primary:hover {{ background: #ffd65c; }}
QPushButton#yellow {{ background: {gelb}; border-color: {gelb}; color: {braun}; }}
QFrame#card {{ border-radius: 20px; border: 2px solid {f['rand']}; background: {f['karte']}; }}
QFrame#card:hover {{ border-color: {gelb}; }}
QFrame#panel {{ border-radius: 20px; border: 2px solid {f['rand']}; }}
QFrame#hero {{ border-radius: 22px; }}
#statusbar {{ background: {creme}; border-top: 3px dashed {rot}; }}
#statusbar QLabel {{ color: {braun}; font-family: {MONO}; }}
QProgressBar {{ background: #f0d2a0; }}
QProgressBar::chunk {{ background: {rot}; }}
"""
    return ""


def welt_fuer(e, f):
    """Welt-ID: fest gewaehlt oder passend zum Preset aus Biblix Design."""
    if e["welt"] != "auto":
        return e["welt"]
    for wid, w in WELTEN.items():
        if w.get("fertig") and w.get("preset") and w["preset"] == f.get("preset"):
            return wid
    return "schlicht"


def klang(datei, e):
    if not e.get("klaenge") or not datei:
        return
    pfad = KLANG_DIR / datei
    if not pfad.is_file():
        return
    for prog in ("pw-play", "paplay"):
        if shutil.which(prog):
            QProcess.startDetached(prog, [str(pfad)])
            return


# ---------------------------------------------------------------- Hausmarke Bibi

def hausmarke():
    """Bibi-Apps aus /usr/share/biblix/hausmarke.d/*.json. Neue Pakete legen dort ihren Eintrag ab;
    ein fertiger Eintrag ersetzt einen gleichnamigen "in_arbeit"-Platzhalter."""
    eintraege = {}
    for d in HAUSMARKE_DIRS:
        if not d.is_dir():
            continue
        for datei in sorted(d.glob("*.json")):
            try:
                e = json.loads(datei.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(e, dict) or not e.get("name"):
                continue
            e.setdefault("id", datei.stem)
            e.setdefault("status", "fertig")
            alt = eintraege.get(e["id"])
            if alt and alt["status"] == "fertig" and e["status"] != "fertig":
                continue
            eintraege[e["id"]] = e
    return sorted(eintraege.values(), key=lambda e: (e.get("reihenfolge", 100), e["name"].lower()))


def hausmarke_da(e):
    pruefen = e.get("pruefen") or (e.get("befehl") or [""])[0]
    return bool(pruefen) and shutil.which(pruefen) is not None


# ---------------------------------------------------------------- Farb- und Malhilfen

def mischen(a, b, t):
    ca, cb = QColor(a), QColor(b)
    return QColor(round(ca.red() + (cb.red() - ca.red()) * t), round(ca.green() + (cb.green() - ca.green()) * t),
                  round(ca.blue() + (cb.blue() - ca.blue()) * t))


def mit_alpha(farbe, alpha):
    c = QColor(farbe)
    c.setAlpha(alpha)
    return c


def stift(farbe, breite=1.0):
    p = QPen(QColor(farbe), breite)
    p.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return p


def prompt_b_malen(p, rect, vorne, akzent, cursor=True, strich=7):
    """Das Biblix-Logo (> B _) im 120er Raster, wie in Biblix Design."""
    p.save()
    s = min(rect.width(), rect.height()) / 120
    p.translate(rect.x() + (rect.width() - 120 * s) / 2, rect.y() + (rect.height() - 120 * s) / 2)
    p.scale(s, s)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(stift(akzent, strich))
    pfeil = QPainterPath(QPointF(26, 44))
    pfeil.lineTo(42, 60)
    pfeil.lineTo(26, 76)
    p.drawPath(pfeil)
    b = QPainterPath(QPointF(54, 34))
    b.lineTo(74, 34)
    b.arcTo(QRectF(61, 34, 26, 26), 90, -180)
    b.lineTo(54, 60)
    b.closeSubpath()
    b.moveTo(54, 60)
    b.lineTo(78, 60)
    b.arcTo(QRectF(64, 60, 28, 28), 90, -180)
    b.lineTo(54, 88)
    b.closeSubpath()
    p.setPen(stift(vorne, strich))
    p.drawPath(b)
    if cursor:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(akzent))
        p.drawRoundedRect(QRectF(54, 94, 34, 6), 2, 2)
    p.restore()


def sechseck(mitte, r, drehung=0.0):
    return QPolygonF([QPointF(mitte.x() + r * math.cos(math.radians(drehung - 90 + 60 * i)),
                              mitte.y() + r * math.sin(math.radians(drehung - 90 + 60 * i))) for i in range(6)])


def mutter_symbol(farbe, groesse=22, drehung=0.0):
    pm = QPixmap(groesse * 2, groesse * 2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    m = QPointF(groesse, groesse)
    p.setPen(stift(farbe, groesse * 0.16))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPolygon(sechseck(m, groesse * 0.78, drehung))
    p.drawEllipse(m, groesse * 0.3, groesse * 0.3)
    p.end()
    pm.setDevicePixelRatio(2)
    return QIcon(pm)


def etagen_symbol(text, f, groesse=22):
    """Leuchtanzeige mit Stockwerk fuer die Seitenleiste im Tower."""
    pm = QPixmap(groesse * 2, groesse * 2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(2, 2)
    p.setPen(QPen(QColor(f["rand"]), 1))
    p.setBrush(QColor("#0b0f14"))
    p.drawRoundedRect(QRectF(0.5, 0.5, groesse - 1, groesse - 1), 5, 5)
    schrift = QFont()
    schrift.setFamilies(["DejaVu Sans Mono", "Consolas", "monospace"])
    schrift.setBold(True)
    schrift.setPixelSize(round(groesse * (0.5 if len(text) < 2 else 0.42)))
    p.setFont(schrift)
    p.setPen(QColor("#ffd400"))
    p.drawText(QRectF(0, 0, groesse, groesse), Qt.AlignmentFlag.AlignCenter, text)
    p.end()
    pm.setDevicePixelRatio(2)
    return QIcon(pm)


def hausmarke_symbol(groesse=22):
    pm = QPixmap(groesse * 2, groesse * 2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(2, 2)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(GOLD))
    p.drawRoundedRect(QRectF(0, 0, groesse, groesse), 6, 6)
    prompt_b_malen(p, QRectF(-1, 0, groesse, groesse), AUF_GOLD, AUF_GOLD, cursor=False, strich=11)
    p.end()
    pm.setDevicePixelRatio(2)
    return QIcon(pm)


# ---------------------------------------------------------------- Animationshilfen

def einblenden(w, verzoegerung=0, dauer=260):
    """Karte weich einblenden (Effekt danach wieder weg, damit nichts bremst)."""
    eff = QGraphicsOpacityEffect(w)
    eff.setOpacity(0.0)
    w.setGraphicsEffect(eff)
    gruppe = QSequentialAnimationGroup(w)
    if verzoegerung:
        gruppe.addPause(verzoegerung)
    an = QPropertyAnimation(eff, b"opacity")
    an.setDuration(dauer)
    an.setStartValue(0.0)
    an.setEndValue(1.0)
    an.setEasingCurve(QEasingCurve.Type.OutCubic)
    gruppe.addAnimation(an)
    gruppe.finished.connect(lambda: alive(w) and w.setGraphicsEffect(None))
    gruppe.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


class Uebergang(QWidget):
    """Seitenwechsel: Aufzugtueren (Tower), Schieben (Theke) oder Blende."""

    def __init__(self, stack):
        super().__init__(stack)
        self.stack = stack
        self.hide()
        self.anim = None
        self.tausch = None
        self.art = None
        self.t = 0.0
        self.alt = self.neu = None
        self.f = GRUNDFARBEN
        self.beschriftung = ""
        self.richtung = 1

    def laeuft(self):
        return self.isVisible()

    def abschliessen(self):
        if self.anim is not None:
            anim, self.anim = self.anim, None
            anim.stop()
        if self.tausch is not None:
            tausch, self.tausch = self.tausch, None
            tausch()
        self.alt = self.neu = None
        self.hide()

    def starten(self, art, tausch, f, dauer=1.0, beschriftung="", richtung=1):
        self.abschliessen()
        self.art, self.f, self.beschriftung, self.richtung = art, f, beschriftung, richtung
        self.setGeometry(self.stack.rect())
        if art == "tuer":
            self.tausch = tausch
            self.show()
            self.raise_()
            self._animieren(0.0, 1.0, int(190 * dauer), QEasingCurve.Type.InOutCubic, self._tuer_zu)
            return
        self.alt = self.stack.grab()
        tausch()
        if art == "schieben":
            seite = self.stack.currentWidget()
            if seite is not None:
                seite.setGeometry(self.stack.rect())
            self.neu = self.stack.grab()
        self.show()
        self.raise_()
        self._animieren(0.0, 1.0, int((300 if art == "schieben" else 200) * dauer), QEasingCurve.Type.OutCubic, self.abschliessen)

    def _animieren(self, von, bis, ms, kurve, danach):
        a = QVariantAnimation(self)
        a.setStartValue(von)
        a.setEndValue(bis)
        a.setDuration(max(1, ms))
        a.setEasingCurve(kurve)
        a.valueChanged.connect(self._wert)
        a.finished.connect(lambda: self.anim is a and danach())
        self.anim = a
        a.start()

    def _wert(self, v):
        self.t = float(v)
        self.update()

    def _tuer_zu(self):
        tausch, self.tausch = self.tausch, None
        if tausch:
            tausch()
        self.raise_()
        self.t = 1.0
        # kurz geschlossen halten, dann auf
        halt = QVariantAnimation(self)
        halt.setStartValue(1.0)
        halt.setEndValue(1.0)
        halt.setDuration(90)
        halt.finished.connect(lambda: self.anim is halt and self._animieren(
            1.0, 0.0, 280, QEasingCurve.Type.OutCubic, self.abschliessen))
        self.anim = halt
        halt.start()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h, t = self.width(), self.height(), self.t
        if self.art == "blende" and self.alt:
            p.setOpacity(1.0 - t)
            p.drawPixmap(0, 0, self.alt)
        elif self.art == "schieben" and self.alt and self.neu:
            r = self.richtung
            p.drawPixmap(round(-r * w * 0.3 * t), 0, self.alt)
            p.fillRect(self.rect(), mit_alpha("#000000", round(90 * t)))
            x = round(r * w * (1 - t))
            p.drawPixmap(x, 0, self.neu)
            p.fillRect(QRectF(x - 6 if r > 0 else x + w, 0, 6, h), mit_alpha("#000000", round(70 * (1 - t))))
        elif self.art == "tuer":
            self._tueren(p, w, h, t)
        p.end()

    def _tueren(self, p, w, h, t):
        f = self.f
        halb = w / 2 * t
        tuer = mischen(f["karte"], f["rand"], 0.35)
        for links in (True, False):
            r = QRectF(0, 0, halb, h) if links else QRectF(w - halb, 0, halb, h)
            p.fillRect(r, tuer)
            # gebuerstetes Metall
            p.setPen(QPen(mit_alpha(f["text"], 14), 1))
            x = r.left() + 3
            while x < r.right():
                p.drawLine(QPointF(x, 0), QPointF(x, h))
                x += 7
            kante = r.right() if links else r.left()
            p.fillRect(QRectF(kante - (3 if links else 0), 0, 3, h), QColor(f["akzent"]))
        p.fillRect(QRectF(0, 0, w, 3), QColor(f["rand"]))
        if t > 0.85 and self.beschriftung:
            p.setOpacity(min(1.0, (t - 0.85) / 0.15))
            box = QRectF(w / 2 - 46, h / 2 - 26, 92, 52)
            p.setPen(QPen(QColor(f["rand"]), 1.5))
            p.setBrush(mischen(f["grund"], "#000000", 0.4))
            p.drawRoundedRect(box, 10, 10)
            schrift = QFont()
            schrift.setFamilies(["DejaVu Sans Mono", "Consolas", "monospace"])
            schrift.setBold(True)
            schrift.setPixelSize(26)
            p.setFont(schrift)
            p.setPen(QColor(f["akzent2"]))
            p.drawText(box, Qt.AlignmentFlag.AlignCenter, self.beschriftung)
            p.setOpacity(1.0)


# ---------------------------------------------------------------- Kleine Anzeigen

class LogoB(QWidget):
    """Prompt-B in der Seitenleiste, der Cursor blinkt."""

    def __init__(self, f, blinken=True, groesse=34):
        super().__init__()
        self.f = f
        self.an = True
        self.setFixedSize(groesse, groesse)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._blink)
        if blinken:
            self.timer.start(560)

    def _blink(self):
        self.an = not self.an
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect())
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self.f["karte"]))
        p.drawRoundedRect(r, r.width() * 0.22, r.width() * 0.22)
        prompt_b_malen(p, r, self.f["text"], self.f["akzent"], cursor=self.an, strich=9)
        p.end()


class Stockwerk(QWidget):
    """Stockwerksanzeige im Tower: zeigt die Etage, beim Fahren einen Pfeil."""

    def __init__(self, f):
        super().__init__()
        self.f = f
        self.text = "1"
        self.pfeil = ""
        self.setFixedSize(84, 34)
        self.setToolTip("Stockwerk")

    def fahren(self, ziel, aufwaerts):
        self.pfeil = "▲" if aufwaerts else "▼"
        self.text = ziel
        self.update()
        QTimer.singleShot(560, self._angekommen)

    def setzen(self, ziel):
        self.pfeil = ""
        self.text = ziel
        self.update()

    def _angekommen(self):
        if alive(self):
            self.pfeil = ""
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(QColor(self.f["rand"]), 1))
        p.setBrush(QColor("#0b0f14"))
        p.drawRoundedRect(r, 8, 8)
        schrift = QFont()
        schrift.setFamilies(["DejaVu Sans Mono", "Consolas", "monospace"])
        schrift.setBold(True)
        schrift.setPixelSize(17)
        p.setFont(schrift)
        p.setPen(QColor("#ffd400"))
        p.drawText(r.adjusted(10, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.pfeil or "■")
        p.drawText(r.adjusted(0, 0, -12, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, self.text)
        p.end()


class Abholanzeige(QWidget):
    """Bestelltheke: Bildschirm mit der aktuellen Bestellnummer."""

    def __init__(self, f):
        super().__init__()
        self.f = f
        self.nr = None
        self.zustand = "frei"   # frei | zubereitung | fertig
        self.an = True
        self.setFixedSize(150, 34)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._blink)

    def zubereiten(self, nr):
        self.nr, self.zustand = nr, "zubereitung"
        self.timer.stop()
        self.update()

    def fertig(self, nr, blinken=True):
        self.nr, self.zustand, self.an = nr, "fertig", True
        if blinken:
            self.timer.start(420)
            QTimer.singleShot(5000, self._ruhe)
        else:
            QTimer.singleShot(5000, self._ruhe)
        self.update()

    def frei(self):
        self.timer.stop()
        self.zustand = "frei"
        self.update()

    def _ruhe(self):
        if alive(self) and self.zustand == "fertig":
            self.timer.stop()
            self.zustand = "frei"
            self.update()

    def _blink(self):
        self.an = not self.an
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        fertig = self.zustand == "fertig"
        p.setPen(QPen(QColor(self.f["akzent2"] if fertig else self.f["rand"]), 1.5 if fertig else 1))
        p.setBrush(QColor("#1b0d0b"))
        p.drawRoundedRect(r, 8, 8)
        schrift = QFont()
        schrift.setFamilies(["DejaVu Sans Mono", "Consolas", "monospace"])
        schrift.setBold(True)
        schrift.setPixelSize(13)
        p.setFont(schrift)
        if self.zustand == "frei":
            p.setPen(QColor("#f3d9a0"))
            text = "KASSA OFFEN"
        elif self.zustand == "zubereitung":
            p.setPen(QColor("#f3d9a0"))
            text = f"Nr. {self.nr:04d}  ···"
        else:
            p.setPen(QColor("#ffd23f") if self.an else QColor("#7a6a30"))
            text = f"Nr. {self.nr:04d} FERTIG"
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, text)
        p.end()


class Meldung(QFrame):
    """Kurze Meldung unten rechts (installiert, Bestellung fertig ...)."""

    def __init__(self, fenster):
        super().__init__(fenster)
        self.setObjectName("meldung")
        self.hide()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 16, 10)
        lay.setSpacing(10)
        self.symbol = QLabel()
        self.symbol.setFixedSize(28, 28)
        lay.addWidget(self.symbol)
        self.text = QLabel()
        self.text.setWordWrap(True)
        self.text.setMinimumWidth(280)
        self.text.setMaximumWidth(380)
        lay.addWidget(self.text, 1)
        self.eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.eff)
        self.anim = None
        self.weg = QTimer(self)
        self.weg.setSingleShot(True)
        self.weg.timeout.connect(self._ausblenden)

    def zeigen(self, text, symbol, unten, animiert=True):
        self.text.setText(text)
        self.symbol.setPixmap(symbol.pixmap(28, 28))
        self.adjustSize()
        eltern = self.parentWidget()
        x = eltern.width() - self.width() - 18
        y = eltern.height() - unten - self.height() - 14
        self.raise_()
        self.show()
        if self.anim:
            self.anim.stop()
        if animiert:
            a = QVariantAnimation(self)
            a.setStartValue(0.0)
            a.setEndValue(1.0)
            a.setDuration(320)
            a.setEasingCurve(QEasingCurve.Type.OutBack)
            a.valueChanged.connect(lambda v: (self.move(x, round(y + 26 * (1 - v))), self.eff.setOpacity(min(1.0, max(0.0, v)))))
            self.anim = a
            a.start()
        else:
            self.move(x, y)
            self.eff.setOpacity(1.0)
        self.weg.start(4200)

    def _ausblenden(self):
        a = QVariantAnimation(self)
        a.setStartValue(1.0)
        a.setEndValue(0.0)
        a.setDuration(260)
        a.valueChanged.connect(lambda v: self.eff.setOpacity(v))
        a.finished.connect(self.hide)
        self.anim = a
        a.start()


# ---------------------------------------------------------------- Buehne (grosser Kopf der Startseite)

class Buehne(QFrame):
    """Startseiten-Kopf je Welt. eintraege: Liste von dict(kicker, titel, text, knoepfe=[(text, name, cb)])."""

    TEXT = "#f4f7fb"

    def __init__(self, welt, f, animiert, eintraege, hoehe=210):
        super().__init__()
        self.welt, self.f, self.animiert = welt, f, animiert
        self.eintraege = eintraege
        self.nr = 0
        self.zeit = 0.0
        self.setFixedHeight(hoehe)
        self.setObjectName("buehne")
        zufall = random.Random(7)
        self.fenster = [[zufall.random() < 0.45 for _ in range(4)] for _ in range(13)]
        self.zufall = random.Random()

        lay = QHBoxLayout(self)
        lay.setContentsMargins(30, 22, 30, 20)
        col = QVBoxLayout()
        col.setSpacing(6)
        self.kicker = QLabel()
        self.kicker.setStyleSheet(f"color: {GOLD if welt != 'theke' else '#ffd23f'}; font-weight: 700; font-size: 9pt; background: transparent;")
        self.titel = QLabel()
        self.titel.setStyleSheet(f"color: {self.TEXT}; font-size: 19pt; font-weight: 800; background: transparent;")
        self.text = QLabel()
        self.text.setWordWrap(True)
        self.text.setMaximumWidth(470)
        self.text.setStyleSheet(f"color: {self.TEXT}; background: transparent;")
        col.addWidget(self.kicker)
        col.addWidget(self.titel)
        col.addWidget(self.text)
        col.addStretch(1)
        self.knoepfe = QHBoxLayout()
        self.knoepfe.setSpacing(8)
        col.addLayout(self.knoepfe)
        lay.addLayout(col, 1)
        lay.addStretch(1)
        self._zeigen(0)

        self.uhr = QTimer(self)
        self.uhr.timeout.connect(self._tick)
        self.wechsel = QTimer(self)
        self.wechsel.timeout.connect(lambda: self._zeigen((self.nr + 1) % len(self.eintraege)))
        if animiert:
            self.uhr.start(40)
        if len(self.eintraege) > 1:
            self.wechsel.start(9000)

    def _zeigen(self, nr):
        self.nr = nr
        e = self.eintraege[nr]
        self.kicker.setText(e.get("kicker", "").upper())
        self.titel.setText(e["titel"])
        self.text.setText(e.get("text", ""))
        while self.knoepfe.count():
            w = self.knoepfe.takeAt(0).widget()
            if w:
                w.deleteLater()
        for text, name, cb in e.get("knoepfe", []):
            b = QPushButton(text)
            if name:
                b.setObjectName(name)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(cb)
            self.knoepfe.addWidget(b)
        self.knoepfe.addStretch(1)
        self.update()

    def mouseReleaseEvent(self, ev):
        # Punkte unten links: zum Eintrag springen
        if len(self.eintraege) > 1 and ev.position().y() > self.height() - 22:
            i = int((ev.position().x() - 30) // 16)
            if 0 <= i < len(self.eintraege):
                self._zeigen(i)
                self.wechsel.start(9000)

    def _tick(self):
        self.zeit += 0.04
        if self.welt == "tower" and self.zufall.random() < 0.18:
            r, c = self.zufall.randrange(len(self.fenster)), self.zufall.randrange(4)
            self.fenster[r][c] = not self.fenster[r][c]
        self.update()

    def hideEvent(self, _):
        self.uhr.stop()

    def showEvent(self, _):
        if self.animiert:
            self.uhr.start(40)

    # ---- malen

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect())
        pfad = QPainterPath()
        pfad.addRoundedRect(r, 16, 16)
        p.setClipPath(pfad)
        getattr(self, "_malen_" + self.welt, self._malen_schlicht)(p, r)
        # Punkte fuer mehrere Eintraege
        if len(self.eintraege) > 1:
            for i in range(len(self.eintraege)):
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(self.TEXT) if i == self.nr else mit_alpha(self.TEXT, 80))
                p.drawEllipse(QPointF(34 + i * 16, r.height() - 12), 3.5, 3.5)
        p.end()

    def _malen_schlicht(self, p, r):
        f = self.f
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, mischen(f["akzent_dunkel"], "#000000", 0.15))
        g.setColorAt(1, mischen(f["akzent_dunkel"], "#000000", 0.6))
        p.fillRect(r, g)
        # grosses Prompt-B als Wasserzeichen, leicht schwebend
        s = r.height() * 1.25
        dy = math.sin(self.zeit * 0.8) * 4
        prompt_b_malen(p, QRectF(r.right() - s * 0.9, r.top() - s * 0.12 + dy, s, s),
                       mit_alpha("#ffffff", 40), mit_alpha(f["akzent_hell"], 120), cursor=int(self.zeit * 1.8) % 2 == 0, strich=6)

    def _malen_tower(self, p, r):
        f = self.f
        nacht = mischen(f["akzent_dunkel"], "#000000", 0.7)
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, nacht)
        g.setColorAt(1, mischen(f["akzent_dunkel"], "#000000", 0.3))
        p.fillRect(r, g)
        boden = r.bottom() - 16
        x0 = r.width() * 0.5
        breite = r.width() - x0
        # Stadt im Hintergrund
        zufall = random.Random(3)
        x = x0 - 40
        p.setPen(Qt.PenStyle.NoPen)
        while x < r.right():
            bw = zufall.randint(26, 52)
            bh = zufall.randint(40, 110)
            p.setBrush(mit_alpha(f["akzent"], 40))
            p.drawRect(QRectF(x, boden - bh, bw, bh))
            x += bw + zufall.randint(4, 14)
        # der Tower
        tx = x0 + breite * 0.52
        tw, th = 74.0, r.height() - 46
        top = boden - th
        koerper = QPolygonF([QPointF(tx - tw / 2, boden), QPointF(tx - tw / 2 + 8, top + 18), QPointF(tx, top),
                             QPointF(tx + tw / 2 - 8, top + 18), QPointF(tx + tw / 2, boden)])
        p.setBrush(mischen(nacht, f["akzent"], 0.22))
        p.setPen(QPen(mit_alpha(f["akzent_hell"], 140), 1.2))
        p.drawPolygon(koerper)
        # Antenne + Blinklicht
        p.setPen(QPen(mit_alpha(f["akzent_hell"], 160), 1.5))
        p.drawLine(QPointF(tx, top), QPointF(tx, top - 16))
        if int(self.zeit * 1.2) % 2 == 0 or not self.animiert:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#ff4a4a"))
            p.drawEllipse(QPointF(tx, top - 17), 2.6, 2.6)
            p.setBrush(mit_alpha("#ff4a4a", 60))
            p.drawEllipse(QPointF(tx, top - 17), 7, 7)
        # Fenster
        reihen = len(self.fenster)
        oben = top + 26
        hoehe = (boden - 8 - oben) / reihen
        p.setPen(Qt.PenStyle.NoPen)
        for i, reihe in enumerate(self.fenster):
            y = oben + i * hoehe
            for j, an in enumerate(reihe):
                fx = tx - 24 + j * 13
                p.setBrush(mit_alpha(f["akzent2"], 220) if an else mit_alpha("#ffffff", 22))
                p.drawRect(QRectF(fx, y + 1, 8, max(2.0, hoehe - 4)))
        # Panorama-Aufzug an der Seite
        schacht = tx + tw / 2 + 10
        p.setPen(QPen(mit_alpha(f["akzent_hell"], 90), 1))
        p.drawLine(QPointF(schacht, top + 26), QPointF(schacht, boden))
        p.drawLine(QPointF(schacht + 12, top + 26), QPointF(schacht + 12, boden))
        lauf = (math.sin(self.zeit * 0.55) + 1) / 2
        ky = top + 28 + lauf * (th - 46)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(f["akzent2"]))
        p.drawRoundedRect(QRectF(schacht + 1, ky, 10, 14), 2, 2)
        # Boden
        p.setBrush(mischen(nacht, "#000000", 0.4))
        p.drawRect(QRectF(r.left(), boden, r.width(), r.bottom() - boden))
        p.setBrush(QColor(f["akzent"]))
        p.drawRect(QRectF(r.left(), boden, r.width(), 2))

    def _malen_theke(self, p, r):
        f = self.f
        tafel = QColor("#24110e") if f["dunkel"] else mischen(f["text"], "#000000", 0.25)
        p.fillRect(r, tafel)
        rot = "#e63131"
        gelb = "#ffc72c"
        # Streifen oben wie eine Menuetafel
        p.fillRect(QRectF(r.left(), r.top(), r.width(), 8), QColor(rot))
        p.fillRect(QRectF(r.left(), r.top() + 8, r.width(), 3), QColor(gelb))
        boden = r.bottom() - 28
        x0 = r.width() * 0.55
        # Theke
        p.fillRect(QRectF(x0 - 20, boden, r.width(), r.bottom() - boden), QColor(rot))
        p.fillRect(QRectF(x0 - 20, boden, r.width(), 5), QColor(gelb))
        # Tablett
        tx = x0 + (r.width() - x0) * 0.18
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#8a4b2a"))
        p.drawRoundedRect(QRectF(tx, boden - 8, 190, 9), 4, 4)
        # Tuete mit Prompt-B
        p.setBrush(QColor("#f4e3c3"))
        tuete = QRectF(tx + 14, boden - 86, 64, 78)
        p.drawRect(tuete)
        p.setBrush(QColor("#e6cfa6"))
        zack = QPolygonF([QPointF(tuete.left() + i * 8, tuete.top() + (0 if i % 2 else 5)) for i in range(9)] +
                         [QPointF(tuete.right(), tuete.top() + 10), QPointF(tuete.left(), tuete.top() + 10)])
        p.drawPolygon(zack)
        prompt_b_malen(p, QRectF(tuete.left() + 8, tuete.top() + 18, 48, 48), QColor(rot), QColor("#c48a00"), cursor=True, strich=10)
        # Becher mit Strohhalm und Dampf
        bx = tx + 108
        p.setBrush(QColor(rot))
        becher = QPolygonF([QPointF(bx, boden - 70), QPointF(bx + 44, boden - 70), QPointF(bx + 38, boden - 8), QPointF(bx + 6, boden - 8)])
        p.drawPolygon(becher)
        p.setBrush(QColor("#ffffff"))
        p.drawRect(QRectF(bx - 2, boden - 76, 48, 7))
        p.setPen(stift(gelb, 4))
        p.drawLine(QPointF(bx + 26, boden - 76), QPointF(bx + 34, boden - 100))
        p.setPen(stift(mit_alpha("#ffffff", 120), 2.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        for k in range(3):
            phase = (self.zeit * 0.6 + k / 3) % 1.0
            y = boden - 108 - phase * 50
            welle = QPainterPath(QPointF(bx + 6 + k * 14, y + 24))
            for s in range(1, 9):
                welle.lineTo(bx + 6 + k * 14 + math.sin(s * 0.9 + self.zeit * 3 + k) * 4, y + 24 - s * 3)
            p.setOpacity(max(0.0, 1.0 - phase) * 0.9)
            p.drawPath(welle)
        p.setOpacity(1.0)
        # Preisschild "NEU", wippt
        p.save()
        p.translate(r.right() - 58, r.top() + 54)
        p.rotate(math.sin(self.zeit * 2.2) * 7 - 8)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(gelb))
        stern = QPolygonF([QPointF(math.cos(math.radians(i * 18)) * (34 if i % 2 == 0 else 28),
                                   math.sin(math.radians(i * 18)) * (34 if i % 2 == 0 else 28)) for i in range(20)])
        p.drawPolygon(stern)
        schrift = QFont()
        schrift.setBold(True)
        schrift.setPixelSize(16)
        p.setFont(schrift)
        p.setPen(QColor(rot))
        p.drawText(QRectF(-30, -14, 60, 28), Qt.AlignmentFlag.AlignCenter, "NEU")
        p.restore()


class HausmarkeKopf(QFrame):
    """Kopf der Seite Hausmarke Bibi: goldene Banderole mit Stempel."""

    def __init__(self, f, animiert, titel, untertitel):
        super().__init__()
        self.f = f
        self.titel, self.untertitel = titel, untertitel
        self.zeit = 0.0
        self.animiert = animiert
        self.setFixedHeight(150)
        self.uhr = QTimer(self)
        self.uhr.timeout.connect(self._tick)

    def _tick(self):
        self.zeit += 0.04
        self.update()

    # Nur animieren, solange die Seite zu sehen ist (spart Rechenzeit im Hintergrund)
    def showEvent(self, _):
        if self.animiert:
            self.uhr.start(40)

    def hideEvent(self, _):
        self.uhr.stop()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect())
        pfad = QPainterPath()
        pfad.addRoundedRect(r, 16, 16)
        p.setClipPath(pfad)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, QColor("#3a2a0c"))
        g.setColorAt(1, QColor("#16100a"))
        p.fillRect(r, g)
        # Glanz, der langsam ueber das Gold wandert
        p.save()
        p.translate(r.width() * 0.62, 0)
        p.rotate(18)
        p.fillRect(QRectF(-20, -60, r.width() * 0.5, 34), QColor(GOLD))
        p.fillRect(QRectF(-20, -20, r.width() * 0.5, 10), mit_alpha(GOLD, 120))
        p.restore()
        glanz = (self.zeit * 0.25) % 1.6 - 0.3
        gx = r.width() * glanz
        lg = QLinearGradient(QPointF(gx - 80, 0), QPointF(gx + 80, 0))
        lg.setColorAt(0, mit_alpha("#ffffff", 0))
        lg.setColorAt(0.5, mit_alpha("#ffffff", 26))
        lg.setColorAt(1, mit_alpha("#ffffff", 0))
        p.fillRect(r, lg)
        # Stempel rechts
        p.save()
        p.translate(r.right() - 96, r.center().y() + 4)
        p.rotate(-12)
        p.setPen(QPen(QColor(GOLD), 3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(0, 0), 52, 52)
        p.setPen(QPen(QColor(GOLD), 1.2))
        p.drawEllipse(QPointF(0, 0), 44, 44)
        prompt_b_malen(p, QRectF(-30, -34, 60, 60), QColor(GOLD), QColor(GOLD), cursor=True, strich=9)
        schrift = QFont()
        schrift.setBold(True)
        schrift.setPixelSize(10)
        schrift.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        p.setFont(schrift)
        p.setPen(QColor(GOLD))
        p.drawText(QRectF(-44, 20, 88, 16), Qt.AlignmentFlag.AlignCenter, "ORIGINAL")
        p.restore()
        # Text
        p.setPen(QColor(GOLD))
        schrift = QFont()
        schrift.setBold(True)
        schrift.setPixelSize(11)
        schrift.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
        p.setFont(schrift)
        p.drawText(QRectF(30, 30, r.width() - 200, 18), Qt.AlignmentFlag.AlignLeft, "AUS EIGENER HERSTELLUNG")
        schrift.setPixelSize(30)
        schrift.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0)
        p.setFont(schrift)
        p.setPen(QColor("#fbf3dc"))
        p.drawText(QRectF(30, 50, r.width() - 200, 44), Qt.AlignmentFlag.AlignLeft, self.titel)
        schrift.setBold(False)
        schrift.setPixelSize(14)
        p.setFont(schrift)
        p.setPen(QColor("#e9dcb8"))
        p.drawText(QRectF(30, 98, r.width() - 200, 40), Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self.untertitel)
        p.end()


class HausmarkeKarte(QFrame):
    """Karte fuer eine Bibi-App: goldene Kante, Platzhalter "In Arbeit" mit Baustellenstreifen."""

    def __init__(self, f, eintrag, animiert, oeffnen):
        super().__init__()
        self.f, self.e = f, eintrag
        self.in_arbeit = eintrag.get("status") != "fertig"
        self.da = not self.in_arbeit and hausmarke_da(eintrag)
        self.versatz = 0.0
        self.hover = False
        self.setFixedSize(320, 150)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        if not self.in_arbeit and self.da:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(eintrag.get("beschreibung", ""))

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 30, 14, 12)
        lay.setSpacing(12)
        ic = QLabel()
        ic.setFixedSize(56, 56)
        ic.setStyleSheet("background: transparent;")
        symbol = QIcon.fromTheme(eintrag.get("symbol", ""), QIcon.fromTheme("applications-other"))
        if symbol.isNull():
            symbol = hausmarke_symbol(56)
        ic.setPixmap(symbol.pixmap(56, 56))
        if self.in_arbeit:
            eff = QGraphicsOpacityEffect(ic)
            eff.setOpacity(0.55)
            ic.setGraphicsEffect(eff)
        lay.addWidget(ic, 0, Qt.AlignmentFlag.AlignTop)
        col = QVBoxLayout()
        col.setSpacing(3)
        name = QLabel(eintrag["name"])
        name.setStyleSheet("font-weight: 700; background: transparent;")
        col.addWidget(name)
        text = QLabel()
        text.setObjectName("muted")
        text.setWordWrap(True)
        text.setStyleSheet("background: transparent;")
        text.setText(text.fontMetrics().elidedText(eintrag.get("beschreibung", ""), Qt.TextElideMode.ElideRight, 320))
        col.addWidget(text)
        col.addStretch(1)
        if self.in_arbeit:
            hinweis = QLabel("Kommt per Update")
            hinweis.setObjectName("muted")
            hinweis.setStyleSheet("background: transparent;")
            col.addWidget(hinweis)
        elif self.da:
            b = QPushButton("Öffnen")
            b.setObjectName("gold")
            b.setFixedHeight(28)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda: oeffnen(eintrag))
            col.addWidget(b, 0, Qt.AlignmentFlag.AlignLeft)
        else:
            hinweis = QLabel("Kommt mit dem nächsten Update")
            hinweis.setObjectName("muted")
            hinweis.setStyleSheet("background: transparent;")
            col.addWidget(hinweis)
        lay.addLayout(col, 1)
        self.oeffnen = oeffnen

        self.animiert = self.in_arbeit and animiert
        self.uhr = QTimer(self)
        self.uhr.timeout.connect(self._tick)

    def showEvent(self, _):
        if self.animiert:
            self.uhr.start(50)

    def hideEvent(self, _):
        self.uhr.stop()

    def _tick(self):
        self.versatz = (self.versatz + 0.6) % 24
        self.update()

    def event(self, ev):
        if ev.type() in (ev.Type.HoverEnter, ev.Type.HoverLeave):
            self.hover = ev.type() == ev.Type.HoverEnter
            self.update()
        return super().event(ev)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and self.da:
            self.oeffnen(self.e)

    def paintEvent(self, _):
        f = self.f
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        pfad = QPainterPath()
        pfad.addRoundedRect(r, 12, 12)
        p.fillPath(pfad, QColor(f["karte"]))
        p.save()
        p.setClipPath(pfad)
        if self.in_arbeit:
            # Baustellenstreifen, die langsam wandern
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(mit_alpha(GOLD, 26))
            x = -40 + self.versatz
            while x < r.width() + 40:
                p.drawPolygon(QPolygonF([QPointF(x, r.bottom()), QPointF(x + 12, r.bottom()),
                                         QPointF(x + 12 + 60, r.top()), QPointF(x + 60, r.top())]))
                x += 24
        p.fillRect(QRectF(r.left(), r.top(), r.width(), 5), QColor(GOLD))
        p.restore()
        p.setPen(QPen(QColor(GOLD if self.hover and self.da else f["rand"]), 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(pfad)
        # Kennzeichnung oben
        schrift = QFont()
        schrift.setBold(True)
        schrift.setPixelSize(9)
        schrift.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        p.setFont(schrift)
        p.setPen(QColor(gold_text(f)))
        p.drawText(QRectF(14, 10, 200, 14), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "HAUSMARKE BIBI")
        if self.in_arbeit:
            pille = QRectF(r.right() - 84, 8, 72, 18)
            p.setPen(QPen(QColor(gold_text(f)), 1))
            p.setBrush(mit_alpha(GOLD, 40))
            p.drawRoundedRect(pille, 9, 9)
            p.drawText(pille, Qt.AlignmentFlag.AlignCenter, "IN ARBEIT")
        p.end()


# ---------------------------------------------------------------- Welt-Auswahl

class WeltMenue(QFrame):
    """Aufklappfenster am Welt-Knopf: Welt, Animationen, Klaenge."""
    geaendert = pyqtSignal(dict)

    def __init__(self, eltern, e, f):
        super().__init__(eltern, Qt.WindowType.Popup)
        self.setObjectName("weltmenue")
        self.e = dict(e)
        self.f = f
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)
        kopf = QLabel("Welt des S-Launchers")
        kopf.setObjectName("h2")
        kopf.setStyleSheet("margin-top: 0;")
        lay.addWidget(kopf)
        auto_welt = WELTEN[welt_fuer({**self.e, "welt": "auto"}, f)]["name"]
        gitter = QGridLayout()
        gitter.setSpacing(6)
        self.welt_knoepfe = {}
        eintraege = [("auto", "Automatisch", f"Wie Biblix Design: {auto_welt}", True)]
        eintraege += [(wid, w["name"], w["info"] if w["fertig"] else f"{w['info']} · bald", w["fertig"]) for wid, w in WELTEN.items()]
        for i, (wid, name, info, geht) in enumerate(eintraege):
            b = QPushButton(f"{name}\n{info}")
            b.setObjectName("weltwahl")
            b.setCheckable(True)
            b.setEnabled(geht)
            b.setMinimumSize(230, 50)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, w=wid: self._setzen("welt", w))
            gitter.addWidget(b, i // 2, i % 2)
            self.welt_knoepfe[wid] = b
        lay.addLayout(gitter)
        unter = QLabel("Animationen")
        unter.setObjectName("h2")
        lay.addWidget(unter)
        reihe = QHBoxLayout()
        self.anim_knoepfe = {}
        for key, text in (("voll", "Voll"), ("dezent", "Dezent"), ("aus", "Aus")):
            b = QPushButton(text)
            b.setObjectName("weltwahl")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, k=key: self._setzen("animationen", k))
            reihe.addWidget(b)
            self.anim_knoepfe[key] = b
        lay.addLayout(reihe)
        self.klaenge = QCheckBox("Klänge (leise: Kassa und Fertig-Ton)")
        self.klaenge.setChecked(bool(self.e["klaenge"]))
        self.klaenge.toggled.connect(lambda an: self._setzen("klaenge", an))
        lay.addWidget(self.klaenge)
        self._markieren()

    def _markieren(self):
        for wid, b in self.welt_knoepfe.items():
            b.setChecked(wid == self.e["welt"])
        for key, b in self.anim_knoepfe.items():
            b.setChecked(key == self.e["animationen"])

    def _setzen(self, schluessel, wert):
        self.e[schluessel] = wert
        self._markieren()
        self.geaendert.emit(dict(self.e))


class WeltKnopf(QToolButton):
    """Schrauben-Knopf oben rechts; die Mutter dreht sich beim Darueberfahren."""

    def __init__(self, f):
        super().__init__()
        self.f = f
        self.drehung = 0.0
        self.setObjectName("weltknopf")
        self.setToolTip("Welt, Animationen und Klänge")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(38, 34)
        self.setIconSize(self.size() * 0.62)
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(380)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._drehen)
        self._drehen(0.0)

    def _drehen(self, v):
        self.drehung = float(v)
        self.setIcon(mutter_symbol(self.f["akzent"] if self.underMouse() else self.f["leise"], 22, self.drehung))

    def enterEvent(self, ev):
        self.anim.stop()
        self.anim.setStartValue(self.drehung)
        self.anim.setEndValue(self.drehung + 60.0)
        self.anim.start()
        super().enterEvent(ev)

    def leaveEvent(self, ev):
        super().leaveEvent(ev)
        self._drehen(self.drehung)
