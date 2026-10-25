"""Farben, Schriften und kleine Helfer fuer die Bibi Arcade (Rechenzentrum + Blaupause)."""
import json
import os
import subprocess
from pathlib import Path

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QPainterPath, QPixmap
from PyQt6.QtWidgets import QLabel, QPushButton

# Rechenzentrum
R = {
    "grund": "#0e0f11", "flaeche": "#16181b", "rack": "#17191c", "einschub": "#23262b", "einschub_an": "#2b2e34",
    "rand": "#2f333a", "rahmen": "#3b3f46", "text": "#d7dadf", "leise": "#7d828a", "dunkel": "#5e636b",
    "aus": "#3a3d42", "orange": "#ff9f1c", "gruen": "#3ddc84", "gelb": "#ffd23f", "rot": "#ff4d4d",
    "blau": "#58a6ff", "band": "#e9e2c8", "band_text": "#2a2a2a", "protokoll": "#8fd19e", "schwarz": "#0a0b0c",
    "netz": "#0a0e14", "netz_linie": "#243042", "netz_knoten": "#132033", "netz_leise": "#565f89",
}
# Blaupause (Datenblatt)
B = {
    "grund": "#0f2a4a", "linie": "#9cc3ff", "text": "#dbe9ff", "gelb": "#ffcf5c",
    "gruen": "#7dffb0", "rot_grund": "#2a0f14", "rot": "#ff6b6b", "rot_text": "#ffd7d7", "blau": "#58a6ff",
}
AMPEL_FARBE = {"gruen": R["gruen"], "gelb": R["gelb"], "rot": R["rot"], "grau": R["aus"]}

KONFIG = Path(os.environ.get("BIBLIX_KONFIG_DIR") or Path.home() / ".config/biblix") / "arcade.json"
DATEN = Path(os.environ.get("BIBI_ARCADE_DATEN") or Path.home() / ".local/share/bibi-arcade")
STANDARD = {"geraeusche": True, "online": True, "sortierung": "zuletzt", "hochfahren": True}

MONO, SANS = "IBM Plex Mono", "IBM Plex Sans Condensed"


def schriften_laden():
    """IBM Plex kommt aus fonts-ibm-plex; zum Testen geht auch ein eigener Ordner (BIBI_ARCADE_SCHRIFTEN)."""
    global MONO, SANS
    extra = os.environ.get("BIBI_ARCADE_SCHRIFTEN")
    if extra:
        for f in Path(extra).rglob("*.[ot]tf"):
            QFontDatabase.addApplicationFont(str(f))
    familien = set(QFontDatabase.families())
    if MONO not in familien:
        MONO = "DejaVu Sans Mono"
    if SANS not in familien:
        SANS = "IBM Plex Sans" if "IBM Plex Sans" in familien else "DejaVu Sans Condensed"


def schrift(groesse=10.5, mono=True, fett=False, abstand=0.0):
    f = QFont(MONO if mono else SANS)
    f.setPointSizeF(groesse)
    if fett:
        f.setWeight(QFont.Weight.DemiBold)
    if abstand:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, abstand)
    return f


def stil():
    return f"""
    * {{ color: {R['text']}; }}
    QMainWindow, #grund {{ background: {R['grund']}; }}
    QScrollArea {{ border: none; background: transparent; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}
    QScrollBar:vertical {{ width: 10px; background: transparent; }}
    QScrollBar::handle:vertical {{ background: {R['rahmen']}; border-radius: 4px; min-height: 40px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
    QLabel {{ background: transparent; }}
    QLabel#leise {{ color: {R['leise']}; }}
    QLabel#dunkel {{ color: {R['dunkel']}; }}
    QPushButton {{ background: {R['einschub']}; border: 1px solid {R['rahmen']}; border-radius: 3px; padding: 6px 14px; }}
    QPushButton:hover, QPushButton:focus {{ border-color: {R['orange']}; }}
    QPushButton#los {{ background: {R['orange']}; color: #2a1600; border-color: {R['orange']}; font-weight: 600; }}
    QPushButton#los:hover, QPushButton#los:focus {{ background: #ffb54d; }}
    QPushButton#windows {{ background: {R['blau']}; color: #04162b; border-color: {R['blau']}; font-weight: 600; }}
    QPushButton#notaus {{ background: {R['rot']}; color: #2b0505; border: 2px solid #ff8080; font-weight: 700; }}
    QPushButton#notaus:hover, QPushButton#notaus:focus {{ background: #ff7070; border-color: #ffffff; }}
    QPushButton#reiter {{ background: transparent; border: none; border-bottom: 2px solid transparent; border-radius: 0;
                          color: {R['leise']}; padding: 4px 6px; letter-spacing: 1px; }}
    QPushButton#reiter:checked {{ color: {R['orange']}; border-bottom-color: {R['orange']}; }}
    QPushButton#reiter:focus {{ color: {R['text']}; }}
    QLineEdit {{ background: {R['schwarz']}; border: 1px solid {R['rahmen']}; border-radius: 3px; padding: 4px 8px; }}
    QLineEdit:focus {{ border-color: {R['orange']}; }}
    QComboBox {{ background: {R['einschub']}; border: 1px solid {R['rahmen']}; border-radius: 3px; padding: 4px 10px; }}
    QComboBox:focus {{ border-color: {R['orange']}; }}
    QComboBox QAbstractItemView {{ background: {R['flaeche']}; selection-background-color: {R['orange']}; selection-color: #2a1600; }}
    QMenu {{ background: {R['flaeche']}; border: 1px solid {R['rahmen']}; padding: 4px; }}
    QMenu::item {{ padding: 6px 18px; }}
    QMenu::item:selected {{ background: {R['orange']}; color: #2a1600; }}
    QCheckBox {{ spacing: 8px; }}
    QToolTip {{ background: {R['flaeche']}; color: {R['text']}; border: 1px solid {R['rahmen']}; }}
    """


def label(text, name=None, wrap=False):
    lb = QLabel(text)
    if name:
        lb.setObjectName(name)
    lb.setWordWrap(wrap)
    return lb


def knopf(text, name=None, cb=None):
    b = QPushButton(text)
    if name:
        b.setObjectName(name)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if cb:
        b.clicked.connect(cb)
    return b


def einstellungen():
    e = dict(STANDARD)
    try:
        e.update(json.loads(KONFIG.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return e


def json_lesen(pfad, standard):
    try:
        d = json.loads(Path(pfad).read_text(encoding="utf-8"))
        return d if isinstance(d, type(standard)) else standard
    except (OSError, ValueError):
        return standard


def json_schreiben(pfad, daten):
    try:
        Path(pfad).parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(str(pfad) + ".tmp")
        tmp.write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(pfad)
    except OSError:
        pass


def run_text(argv, timeout=5):
    """Ausgabe eines kleinen Befehls (leer, wenn es ihn nicht gibt)."""
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def starten(argv):
    try:
        subprocess.Popen(argv, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except OSError:
        return False


# ---------------------------------------------------------------- Texte

def stunden(minuten):
    minuten = int(minuten or 0)
    return f"{minuten // 60} h {minuten % 60:02d}"


def stunden_lang(minuten):
    minuten = int(minuten or 0)
    if minuten < 60:
        return f"{minuten} min"
    return f"{minuten // 60} h {minuten % 60:02d} min"


def gb(b):
    return f"{b / 1e9:.1f} GB".replace(".", ",") if b else "–"


def wann(zeit, kurz=True):
    import time
    if not zeit:
        return "nie"
    jetzt = time.localtime()
    t = time.localtime(zeit)
    tage = (time.mktime(time.strptime(time.strftime("%Y-%m-%d", jetzt), "%Y-%m-%d"))
            - time.mktime(time.strptime(time.strftime("%Y-%m-%d", t), "%Y-%m-%d"))) // 86400
    if tage == 0:
        return "heute" if kurz else "heute, " + time.strftime("%H:%M", t)
    if tage == 1:
        return "gestern" if kurz else "gestern, " + time.strftime("%H:%M", t)
    return time.strftime("%d.%m." if t.tm_year == jetzt.tm_year else "%d.%m.%y", t)


def kennzeichen(name):
    """"Gunner, HEAT, PC!" -> "GUNNER-HEAT-PC" (wie ein Etikett im Rack)."""
    import re
    t = re.sub(r"[^0-9A-Za-zÄÖÜäöüß]+", "-", name).strip("-").upper()
    return t or "UNBEKANNT"


# ---------------------------------------------------------------- Malen

_bilder = {}


def bild(pfad):
    if not pfad:
        return None
    if pfad not in _bilder:
        pm = QPixmap(pfad)
        _bilder[pfad] = None if pm.isNull() else pm
    return _bilder[pfad]


def bild_fuellen(p, r, pm, radius=0):
    """Bild zuschneiden, damit es das Rechteck ganz fuellt."""
    if pm is None:
        return False
    pfad = QPainterPath()
    pfad.addRoundedRect(r, radius, radius)
    p.save()
    p.setClipPath(pfad)
    quelle = QRectF(pm.rect())
    faktor = max(r.width() / quelle.width(), r.height() / quelle.height())
    w, h = r.width() / faktor, r.height() / faktor
    p.drawPixmap(r, pm, QRectF(quelle.center().x() - w / 2, quelle.center().y() - h / 2, w, h))
    p.restore()
    return True


def farbe(hexfarbe, alpha):
    """Farbe mit Deckkraft 0-255 (Qt liest 8-stellige Codes als #AARRGGBB, darum nie so schreiben)."""
    c = QColor(hexfarbe)
    c.setAlpha(alpha)
    return c


def led(p, mitte, farbe, an=True, r=4.5):
    """LED mit kleinem Lichthof."""
    c = QColor(farbe if an else R["aus"])
    p.setPen(Qt.PenStyle.NoPen)
    if an:
        hof = QColor(c)
        hof.setAlpha(60)
        p.setBrush(hof)
        p.drawEllipse(mitte, r * 2, r * 2)
    p.setBrush(c)
    p.drawEllipse(mitte, r, r)
    if an:
        p.setBrush(QColor(255, 255, 255, 120))
        p.drawEllipse(QRectF(mitte.x() - r * 0.5, mitte.y() - r * 0.5, r * 0.6, r * 0.6))


def gitter(p, rect, schritt, farbe):
    p.setPen(QColor(farbe))
    x = rect.left()
    while x < rect.right():
        p.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
        x += schritt
    y = rect.top()
    while y < rect.bottom():
        p.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
        y += schritt

