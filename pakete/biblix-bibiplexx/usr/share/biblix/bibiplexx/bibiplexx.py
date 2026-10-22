#!/usr/bin/env python3
"""Bibiplexx - Filme und Serien auf Biblix.

Die Sammlung (Saal, Serien, Filme, Weiterschauen) ist eine eigene Oberflaeche;
gespielt wird im Vollbild mit mpv, mit Bibiplexx-Steuerleiste und Vorhang-Intro.

    bibiplexx               Sammlung oeffnen
    bibiplexx DATEI ...     Datei(en) direkt im Bibiplexx-Player abspielen
"""
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PyQt6 import sip
from PyQt6.QtCore import (
    QEasingCurve, QObject, QPoint, QPointF, QProcess, QPropertyAnimation, QRect, QRectF, QRunnable,
    QSize, Qt, QThread, QThreadPool, QTimer, pyqtSignal,
)
from PyQt6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QGraphicsOpacityEffect, QHBoxLayout,
    QInputDialog, QLabel, QLayout, QLineEdit, QMainWindow, QMenu, QMessageBox, QPushButton, QScrollArea,
    QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

VERSION = "1.0"
HIER = Path(__file__).resolve().parent
MPV_CONF = HIER / "mpv/bibiplexx.conf"
MPV_LUA = HIER / "mpv/bibiplexx.lua"
GONG = HIER / "gong.wav"
SYMBOL = Path("/usr/share/icons/hicolor/scalable/apps/de.biblix.Bibiplexx.svg")

KONFIG = Path(os.environ.get("BIBLIX_KONFIG_DIR") or Path.home() / ".config/biblix") / "bibiplexx.json"
ZUSTAND = Path(os.environ.get("BIBIPLEXX_ZUSTAND") or Path.home() / ".local/state/bibiplexx")
STAND = ZUSTAND / "fortschritt.json"
CACHE = Path(os.environ.get("BIBIPLEXX_CACHE") or Path.home() / ".cache/bibiplexx")
PLAKATE = CACHE / "plakate"
INFO = CACHE / "info.json"
PLATTE_HELFER = "/usr/lib/biblix/bibiplexx-platte"
PLATTE_ORT = Path("/media/bibiplexx")

ENDUNGEN = {".mkv", ".mp4", ".avi", ".mov", ".webm", ".m4v", ".ts", ".m2ts", ".wmv", ".mpg", ".mpeg", ".flv", ".ogv"}
UEBERSPRINGEN = {"$recycle.bin", "system volume information", "lost+found", "@eadir", ".trash-1000"}
PLAKAT_DATEIEN = ("poster.jpg", "poster.png", "folder.jpg", "folder.png", "cover.jpg", "cover.png")

F = {
    "grund": "#07070c", "flaeche": "#120d1f", "karte": "#1a1030", "rand": "#2f2050",
    "text": "#f2e9ff", "leise": "#a898c8", "pink": "#ff4d9d", "orange": "#ff8a00", "lila": "#7b2cbf",
}

STIL = f"""
* {{ font-size: 10.5pt; }}
QMainWindow, QDialog, #seite {{ background: {F['grund']}; color: {F['text']}; }}
QLabel {{ color: {F['text']}; background: transparent; }}
QLabel#leise {{ color: {F['leise']}; }}
QLabel#h1 {{ font-size: 22pt; font-weight: 800; }}
QLabel#h2 {{ font-size: 14pt; font-weight: 700; margin-top: 8px; }}
#kopf {{ background: {F['flaeche']}; border-bottom: 1px solid {F['rand']}; }}
QPushButton {{ background: {F['karte']}; color: {F['text']}; border: 1px solid {F['rand']}; border-radius: 9px; padding: 7px 16px; }}
QPushButton:hover {{ border-color: {F['pink']}; }}
QPushButton:checked {{ background: {F['pink']}; color: #1a0010; border-color: {F['pink']}; font-weight: 700; }}
QPushButton#orange {{ background: {F['orange']}; color: #1b0d00; border-color: {F['orange']}; font-weight: 800; }}
QPushButton#orange:hover {{ background: #ffa233; }}
QPushButton#nav {{ background: transparent; border: none; font-size: 12pt; font-weight: 700; color: {F['leise']}; padding: 8px 14px; }}
QPushButton#nav:hover {{ color: {F['text']}; }}
QPushButton#nav:checked {{ color: {F['pink']}; background: transparent; border-bottom: 3px solid {F['pink']}; border-radius: 0; }}
QLineEdit {{ background: {F['karte']}; border: 1px solid {F['rand']}; border-radius: 9px; padding: 7px 12px; color: {F['text']}; }}
QLineEdit:focus {{ border-color: {F['pink']}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:horizontal {{ height: 8px; background: transparent; }}
QScrollBar::handle:horizontal {{ background: {F['rand']}; border-radius: 4px; min-width: 40px; }}
QScrollBar:vertical {{ width: 10px; background: transparent; }}
QScrollBar::handle:vertical {{ background: {F['rand']}; border-radius: 5px; min-height: 40px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QFrame#zeile {{ background: {F['flaeche']}; border: 1px solid {F['rand']}; border-radius: 12px; }}
QFrame#zeile:hover {{ border-color: {F['pink']}; }}
QCheckBox {{ color: {F['text']}; spacing: 8px; }}
QComboBox {{ background: {F['karte']}; border: 1px solid {F['rand']}; border-radius: 9px; padding: 6px 12px; color: {F['text']}; }}
QComboBox:hover {{ border-color: {F['pink']}; }}
QComboBox QAbstractItemView {{ background: {F['flaeche']}; color: {F['text']}; selection-background-color: {F['pink']}; selection-color: #1a0010; border: 1px solid {F['rand']}; }}
QMenu {{ background: {F['flaeche']}; color: {F['text']}; border: 1px solid {F['rand']}; padding: 6px; }}
QMenu::item {{ padding: 7px 22px; border-radius: 6px; }}
QMenu::item:selected {{ background: {F['pink']}; color: #1a0010; }}
QMenu::separator {{ height: 1px; background: {F['rand']}; margin: 5px 8px; }}
"""


def alive(obj):
    return obj is not None and not sip.isdeleted(obj)


def run(argv, timeout=20):
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


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


STANDARD = {
    "ordner": [str(Path.home() / "Videos")],
    "kino": "vorhang_gong",      # vorhang_gong | vorhang | aus
    "sprache": "deutsch",        # deutsch | original
    "untertitel": "fremd",       # fremd | deutsch | aus
    "ut_groesse": "mittel",      # klein | mittel | gross
    "ut_farbe": "weiss",         # weiss | gelb
    "nachtmodus": False,
    "autoplay": True,
    "countdown": 15,
    "intro_knopf": True,
    "sortierung": "az",          # az | neu | jahr
}


def einstellungen():
    e = json.loads(json.dumps(STANDARD))
    e.update(json_lesen(KONFIG, {}))
    if e["kino"] is True:
        e["kino"] = "vorhang_gong"
    elif e["kino"] is False:
        e["kino"] = "aus"
    if PLATTE_ORT.is_dir() and str(PLATTE_ORT) not in e["ordner"]:
        e["ordner"].append(str(PLATTE_ORT))
    return e


def uhr(sek):
    sek = int(sek or 0)
    h, m, s = sek // 3600, (sek // 60) % 60, sek % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def dauer_text(sek):
    sek = int(sek or 0)
    h, m = sek // 3600, (sek // 60) % 60
    return f"{h} Std. {m} Min." if h else f"{m} Min."


# ---------------------------------------------------------------- Dateinamen verstehen

SERIE = re.compile(r"^(?P<name>.*?)[ ._\-\[\(]*[Ss](?P<s>\d{1,2})[ ._\-]*[Ee](?P<e>\d{1,3})(?P<rest>.*)$")
SERIE_X = re.compile(r"^(?P<name>.*?)[ ._\-]+(?P<s>\d{1,2})x(?P<e>\d{2,3})(?P<rest>.*)$")
STAFFEL_ORDNER = re.compile(r"^(staffel|season|s)[ ._\-]*\d+$", re.I)
JAHR = re.compile(r"[ ._\(\[]((?:19|20)\d{2})(?:[\)\]]|[ ._]|$)")
MARKEN = re.compile(r"[ ._\-\[\(](2160p|1080p|720p|576p|480p|4k|uhd|hdr10?|dv|x264|x265|h\.?264|h\.?265|hevc|avc|bluray|blu-ray|"
                    r"web-?dl|webrip|web|dvdrip|bdrip|hdtv|german|deutsch|dl|ac3|eac3|dts|aac|multi|remux|proper|repack|"
                    r"internal|complete|extended|uncut)(?=$|[ ._\-\]\)]).*$", re.I)


def aufraeumen(t):
    t = MARKEN.sub("", t)
    t = re.sub(r"[._]+", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip(" -_[]()")


def verstehen(pfad: Path):
    """Aus einem Dateipfad: Serie (Name, Staffel, Folge) oder Film (Titel, Jahr)."""
    stamm = pfad.stem
    m = SERIE.match(stamm) or SERIE_X.match(stamm)
    if m:
        name = aufraeumen(m.group("name"))
        if not name:
            ordner = pfad.parent
            if STAFFEL_ORDNER.match(ordner.name) and ordner.parent != ordner:
                ordner = ordner.parent
            name = aufraeumen(ordner.name)
        name = JAHR.sub(" ", name).strip() or name
        return {"art": "serie", "serie": name or "Unbekannte Serie", "staffel": int(m.group("s")),
                "folge": int(m.group("e")), "titel": aufraeumen(m.group("rest"))}
    jahr = None
    j = JAHR.search(stamm)
    if j and j.start() > 0:
        jahr, stamm = j.group(1), stamm[:j.start()]
    return {"art": "film", "titel": aufraeumen(stamm) or pfad.stem, "jahr": jahr}


def einlesen(ordner_liste):
    gefunden, gesehen = [], set()
    for wurzel in ordner_liste:
        w = Path(wurzel).expanduser()
        if not w.is_dir():
            continue
        for d, unter, dateien in os.walk(w):
            unter[:] = [u for u in unter if not u.startswith(".") and u.lower() not in UEBERSPRINGEN]
            for name in dateien:
                p = Path(d) / name
                if p.suffix.lower() not in ENDUNGEN or name.startswith("."):
                    continue
                try:
                    st = p.stat()
                except OSError:
                    continue
                if "sample" in name.lower() and st.st_size < 300_000_000:
                    continue
                schluessel = str(p.resolve())
                if schluessel in gesehen:
                    continue
                gesehen.add(schluessel)
                e = verstehen(p)
                e.update({"pfad": str(p), "mtime": st.st_mtime, "groesse": st.st_size})
                gefunden.append(e)
    return gefunden


# ---------------------------------------------------------------- Plakate (Standbild aus dem Film)

def plakat_datei(pfad):
    p = Path(pfad)
    for kandidat in [p.with_suffix(".jpg"), p.with_suffix(".png")] + [p.parent / n for n in PLAKAT_DATEIEN]:
        if kandidat.is_file():
            return kandidat
    return None


def cache_schluessel(e):
    return hashlib.sha1(f"{e['pfad']}|{e['mtime']}|{e['groesse']}".encode()).hexdigest()


class BildSignale(QObject):
    fertig = pyqtSignal(str, str, float)  # pfad, bilddatei, dauer


class BildArbeit(QRunnable):
    def __init__(self, e, signale):
        super().__init__()
        self.e, self.signale = e, signale

    def run(self):
        ziel = PLAKATE / (cache_schluessel(self.e) + ".jpg")
        dauer = 0.0
        out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", self.e["pfad"]], 30)
        try:
            dauer = float(out.strip().splitlines()[0])
        except (ValueError, IndexError):
            pass
        if not ziel.is_file():
            PLAKATE.mkdir(parents=True, exist_ok=True)
            punkt = max(5.0, min(dauer * 0.12, 600.0)) if dauer else 60.0
            run(["ffmpeg", "-v", "error", "-y", "-ss", f"{punkt:.0f}", "-i", self.e["pfad"], "-frames:v", "1",
                 "-vf", "scale=640:-2", "-q:v", "4", str(ziel)], 60)
        self.signale.fertig.emit(self.e["pfad"], str(ziel) if ziel.is_file() else "", dauer)


class Bilder(QObject):
    """Laedt Plakate im Hintergrund und merkt sich Laufzeiten."""
    neu = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(2)
        self.info = json_lesen(INFO, {})
        self.pixmaps = {}
        self.laufend = set()
        self.signale = BildSignale()
        self.signale.fertig.connect(self._fertig)

    def pixmap(self, e):
        pfad = e["pfad"]
        if pfad in self.pixmaps:
            return self.pixmaps[pfad]
        eigenes = plakat_datei(pfad)
        datei = eigenes or (PLAKATE / (cache_schluessel(e) + ".jpg"))
        if datei.is_file():
            pm = QPixmap(str(datei))
            if not pm.isNull():
                self.pixmaps[pfad] = pm
                if not eigenes or pfad not in self.info:
                    self._anstossen(e)
                return pm
        self._anstossen(e)
        return None

    def dauer(self, e):
        return self.info.get(e["pfad"], {}).get("dauer", 0)

    def _anstossen(self, e):
        if e["pfad"] in self.laufend or (e["pfad"] in self.info and (PLAKATE / (cache_schluessel(e) + ".jpg")).is_file()):
            return
        if not shutil.which("ffmpeg"):
            return
        self.laufend.add(e["pfad"])
        self.pool.start(BildArbeit(e, self.signale))

    def _fertig(self, pfad, datei, dauer):
        self.laufend.discard(pfad)
        if dauer:
            self.info[pfad] = {"dauer": dauer}
            json_schreiben(INFO, self.info)
        if datei and pfad not in self.pixmaps:
            pm = QPixmap(datei)
            if not pm.isNull():
                self.pixmaps[pfad] = pm
        self.neu.emit(pfad)


# ---------------------------------------------------------------- Malhilfen

def sitzreihe(p, x, y, platz, abstand, anzahl=6, hell=3):
    """Sitzreihe wie im Bibiplexx-Logo, ein Platz leuchtet orange."""
    for i in range(anzahl):
        r = QRectF(x + i * (platz + abstand), y, platz, platz)
        p.setPen(QPen(QColor(F["lila"]), 1.2))
        p.setBrush(QColor(F["orange"] if i == hell else F["karte"]))
        p.drawRoundedRect(r, platz * 0.25, platz * 0.25)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(F["karte"]))
    p.drawRoundedRect(QRectF(x - 2, y + platz + 3, anzahl * (platz + abstand) - abstand + 4, 4), 2, 2)


def leinwand_rahmen(p, r):
    """Lila Linien mit pinken Eckstrichen, wie die Leinwand im Logo."""
    p.setPen(QPen(QColor(F["lila"]), 2))
    p.drawLine(QPointF(r.left(), r.top()), QPointF(r.right(), r.top()))
    p.drawLine(QPointF(r.left(), r.bottom()), QPointF(r.right(), r.bottom()))
    p.setPen(QPen(QColor(F["pink"]), 2))
    for x, y, dx, dy in ((r.left(), r.top(), -9, -9), (r.right(), r.top(), 9, -9),
                         (r.left(), r.bottom(), -9, 9), (r.right(), r.bottom(), 9, 9)):
        p.drawLine(QPointF(x, y), QPointF(x + dx, y + dy))


def bild_fuellen(p, r, pm, radius=12):
    pfad = QPainterPath()
    pfad.addRoundedRect(r, radius, radius)
    p.save()
    p.setClipPath(pfad)
    if pm is None:
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, QColor(F["karte"]))
        g.setColorAt(1, QColor("#2a1240"))
        p.fillRect(r, g)
    else:
        skaliert = pm.scaled(r.size().toSize(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                             Qt.TransformationMode.SmoothTransformation)
        dx = (skaliert.width() - r.width()) / 2
        dy = (skaliert.height() - r.height()) / 2
        p.drawPixmap(r.topLeft(), skaliert, QRectF(dx, dy, r.width(), r.height()))
    p.restore()


# ---------------------------------------------------------------- Karten

class Karte(QWidget):
    """16:9-Karte mit Standbild, Titel, Untertitel und Fortschritt."""
    geklickt = pyqtSignal()

    B, H = 272, 153

    def __init__(self, haupt, e, titel, unter="", anteil=0.0, fertig=False, gross=False):
        super().__init__()
        self.haupt, self.e, self.titel, self.unter = haupt, e, titel, unter
        self.anteil, self.fertig = anteil, fertig
        self.hover = False
        faktor = 1.25 if gross else 1.0
        self.bw, self.bh = round(self.B * faktor), round(self.H * faktor)
        self.setFixedSize(self.bw, self.bh + 50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(Path(e["pfad"]).name if e else "")
        self.pm = haupt.bilder.pixmap(e) if e else None
        haupt.bilder.neu.connect(self._neu)

    def _neu(self, pfad):
        if alive(self) and self.e and pfad == self.e["pfad"]:
            self.pm = self.haupt.bilder.pixmap(self.e)
            self.update()

    def enterEvent(self, _):
        self.hover = True
        self.update()

    def leaveEvent(self, _):
        self.hover = False
        self.update()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.geklickt.emit()

    def contextMenuEvent(self, ev):
        self.haupt.kontextmenue(self, ev.globalPos())

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = QRectF(1, 1, self.bw - 2, self.bh - 2)
        bild_fuellen(p, r, self.pm)
        if self.pm is None:
            p.setPen(QColor(F["leise"]))
            f = QFont(self.font())
            f.setPointSizeF(f.pointSizeF() * 1.4)
            f.setBold(True)
            p.setFont(f)
            p.drawText(r.adjusted(14, 0, -14, 0), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.titel)
        if self.anteil > 0:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, 150))
            p.drawRect(QRectF(r.left() + 10, r.bottom() - 12, r.width() - 20, 5))
            p.setBrush(QColor(F["pink"]))
            p.drawRect(QRectF(r.left() + 10, r.bottom() - 12, (r.width() - 20) * min(1.0, self.anteil), 5))
        if self.fertig:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(F["orange"]))
            p.drawEllipse(QPointF(r.right() - 18, r.top() + 18), 11, 11)
            p.setPen(QPen(QColor("#1b0d00"), 2.4))
            p.drawPolyline([QPointF(r.right() - 23, r.top() + 18), QPointF(r.right() - 19, r.top() + 22), QPointF(r.right() - 12, r.top() + 14)])
        p.setPen(QPen(QColor(F["pink"] if self.hover else F["rand"]), 2 if self.hover else 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(r, 12, 12)
        p.setPen(QColor(F["text"]))
        f = QFont(self.font())
        f.setBold(True)
        p.setFont(f)
        fm = p.fontMetrics()
        p.drawText(QRectF(2, self.bh + 6, self.bw - 4, 20), Qt.AlignmentFlag.AlignLeft,
                   fm.elidedText(self.titel, Qt.TextElideMode.ElideRight, self.bw - 4))
        f.setBold(False)
        p.setFont(f)
        p.setPen(QColor(F["leise"]))
        p.drawText(QRectF(2, self.bh + 27, self.bw - 4, 20), Qt.AlignmentFlag.AlignLeft,
                   p.fontMetrics().elidedText(self.unter, Qt.TextElideMode.ElideRight, self.bw - 4))
        p.end()


class FlowLayout(QLayout):
    def __init__(self, parent=None, abstand=18):
        super().__init__(parent)
        self._items = []
        self.setSpacing(abstand)
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)
        self.invalidate()

    def count(self):
        return len(self._items)

    def itemAt(self, i):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return self._ordnen(QRect(0, 0, w, 0), True)

    def setGeometry(self, r):
        super().setGeometry(r)
        self._ordnen(r, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        s = QSize()
        for it in self._items:
            s = s.expandedTo(it.minimumSize())
        return s

    def _ordnen(self, r, test):
        x, y, zeile, sp = r.x(), r.y(), 0, self.spacing()
        for it in self._items:
            h = it.sizeHint()
            if x > r.x() and x + h.width() > r.right() + 1:
                x, y, zeile = r.x(), y + zeile + sp, 0
            if not test:
                it.setGeometry(QRect(QPoint(x, y), h))
            x += h.width() + sp
            zeile = max(zeile, h.height())
        return y + zeile - r.y()


class Reihe(QWidget):
    """Ueberschrift und waagrecht scrollende Kartenreihe (Mausrad scrollt seitwaerts)."""

    def __init__(self, titel, karten):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.addWidget(label(titel, "h2"))
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        innen = QWidget()
        hl = QHBoxLayout(innen)
        hl.setContentsMargins(0, 0, 0, 4)
        hl.setSpacing(18)
        hoehe = 0
        for k in karten:
            hl.addWidget(k)
            hoehe = max(hoehe, k.height())
        hl.addStretch(1)
        self.scroll.setWidget(innen)
        self.scroll.setFixedHeight(hoehe + 14)
        self.scroll.viewport().installEventFilter(self)
        lay.addWidget(self.scroll)

    def eventFilter(self, obj, ev):
        if ev.type() == ev.Type.Wheel:
            bar = self.scroll.horizontalScrollBar()
            if bar.maximum() > 0:
                bar.setValue(bar.value() - ev.angleDelta().y())
                return True
        return False


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


class Seite(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        innen = QWidget()
        innen.setObjectName("seite")
        self.body = QVBoxLayout(innen)
        self.body.setContentsMargins(36, 26, 36, 36)
        self.body.setSpacing(16)
        self.body.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(innen)

    def raster(self):
        halter = QWidget()
        fl = FlowLayout(halter)
        self.body.addWidget(halter)
        return fl


# ---------------------------------------------------------------- Leinwand (grosser Kopf im Saal)

class Leinwand(QWidget):
    def __init__(self, pm, kicker, titel, text, knoepfe, haupt=None, e=None):
        super().__init__()
        self.pm = pm
        self.haupt, self.e = haupt, e
        if haupt is not None and e is not None:
            haupt.bilder.neu.connect(self._neu)
        self.setFixedHeight(330)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(40, 30, 40, 34)
        col = QVBoxLayout()
        col.setSpacing(8)
        k = label(kicker.upper())
        k.setStyleSheet(f"color: {F['orange']}; font-weight: 800; letter-spacing: 2px; font-size: 9.5pt;")
        t = label(titel)
        t.setStyleSheet("font-size: 26pt; font-weight: 800;")
        t.setWordWrap(True)
        t.setMaximumWidth(620)
        x = label(text, wrap=True)
        x.setMaximumWidth(560)
        x.setStyleSheet(f"color: {F['text']};")
        col.addWidget(k)
        col.addWidget(t)
        col.addWidget(x)
        col.addStretch(1)
        reihe = QHBoxLayout()
        reihe.setSpacing(10)
        for b in knoepfe:
            reihe.addWidget(b)
        reihe.addStretch(1)
        col.addLayout(reihe)
        lay.addLayout(col, 1)
        lay.addStretch(1)

    def _neu(self, pfad):
        if alive(self) and pfad == self.e["pfad"]:
            self.pm = self.haupt.bilder.pixmap(self.e)
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = QRectF(self.rect()).adjusted(10, 12, -10, -12)
        bild_fuellen(p, r, self.pm, 6)
        g = QLinearGradient(r.topLeft(), r.topRight())
        g.setColorAt(0, QColor(7, 7, 12, 245))
        g.setColorAt(0.45, QColor(7, 7, 12, 200))
        g.setColorAt(1, QColor(7, 7, 12, 40 if self.pm else 120))
        p.fillRect(r, g)
        leinwand_rahmen(p, r)
        sitzreihe(p, r.right() - 6 * 30 - 24, r.bottom() - 46, 24, 6)
        p.end()


# ---------------------------------------------------------------- Hauptfenster

class Einleser(QThread):
    fertig = pyqtSignal(list)

    def __init__(self, ordner):
        super().__init__()
        self.ordner = ordner

    def run(self):
        self.fertig.emit(einlesen(self.ordner))


class Haupt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bibiplexx")
        icon = QIcon.fromTheme("de.biblix.Bibiplexx")
        if icon.isNull() and SYMBOL.is_file():
            icon = QIcon(str(SYMBOL))
        self.setWindowIcon(icon)
        self.resize(1360, 860)
        self.einst = einstellungen()
        self.bilder = Bilder()
        self.alle = []
        self.stand = {}
        self.mpv = None
        self.einleser = None
        self.zuletzt_eingelesen = 0.0

        root = QWidget()
        lay = QVBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        kopf = QWidget()
        kopf.setObjectName("kopf")
        kl = QHBoxLayout(kopf)
        kl.setContentsMargins(22, 10, 22, 10)
        kl.setSpacing(6)
        logo = QLabel()
        if not icon.isNull():
            logo.setPixmap(icon.pixmap(40, 40))
        kl.addWidget(logo)
        name = label("BIBIPLEXX")
        name.setStyleSheet(f"color: {F['pink']}; font-size: 16pt; font-weight: 900; letter-spacing: 3px; margin-right: 18px;")
        kl.addWidget(name)
        self.nav = {}
        for key, text in (("saal", "Saal"), ("serien", "Serien"), ("filme", "Filme")):
            b = knopf(text, "nav", lambda _=False, k=key: self.zeigen(k))
            b.setCheckable(True)
            kl.addWidget(b)
            self.nav[key] = b
        kl.addStretch(1)
        self.suche = QLineEdit()
        self.suche.setPlaceholderText("Film oder Serie suchen …")
        self.suche.setClearButtonEnabled(True)
        self.suche.setFixedWidth(320)
        self.suche.returnPressed.connect(self.suchen)
        kl.addWidget(self.suche)
        kl.addWidget(knopf("Einstellungen", cb=self.einstellungen_zeigen))
        lay.addWidget(kopf)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.setStyleSheet(STIL)

        # Saal wird dunkel (Kinomodus): schwarze Blende ueber dem Fenster
        self.blende = QWidget(root)
        self.blende.setStyleSheet("background: #000;")
        self.blende_eff = QGraphicsOpacityEffect(self.blende)
        self.blende.setGraphicsEffect(self.blende_eff)
        self.blende.hide()

        self.aktuell = "saal"
        self.stand_laden()
        self.zeigen("saal")
        self.neu_einlesen()

    # ---- Daten

    def stand_laden(self):
        self.stand = json_lesen(STAND, {})

    def neu_einlesen(self):
        if self.einleser and self.einleser.isRunning():
            return
        self.zuletzt_eingelesen = time.time()
        self.einleser = Einleser(list(self.einst["ordner"]))
        self.einleser.fertig.connect(self._eingelesen)
        self.einleser.start()

    def _eingelesen(self, liste):
        self.alle = liste
        self.zeigen(self.aktuell, neu=True)

    def serien(self):
        s = {}
        for e in self.alle:
            if e["art"] == "serie":
                s.setdefault(e["serie"], []).append(e)
        for folgen in s.values():
            folgen.sort(key=lambda e: (e["staffel"], e["folge"], e["pfad"]))
        return dict(sorted(s.items(), key=lambda kv: kv[0].lower()))

    def filme(self):
        return sorted([e for e in self.alle if e["art"] == "film"], key=lambda e: e["titel"].lower())

    def fortschritt(self, e):
        s = self.stand.get(e["pfad"], {})
        dauer = s.get("dauer") or self.bilder.dauer(e)
        anteil = (s.get("pos", 0) / dauer) if dauer else 0.0
        return anteil, bool(s.get("fertig")), s

    def weiterschauen(self):
        """Angefangene Filme und Folgen; bei fertig gesehenen Folgen die naechste."""
        liste = []
        for name, folgen in self.serien().items():
            zuletzt, wann = None, 0
            for i, e in enumerate(folgen):
                z = self.stand.get(e["pfad"], {}).get("zeit", 0)
                if z and z >= wann:
                    zuletzt, wann = i, z
            if zuletzt is None:
                continue
            e = folgen[zuletzt]
            s = self.stand[e["pfad"]]
            if s.get("fertig"):
                if zuletzt + 1 < len(folgen):
                    n = folgen[zuletzt + 1]
                    liste.append((wann, n, f"Nächste Folge · S{n['staffel']:02d}E{n['folge']:02d}"))
            elif s.get("pos", 0) > 30:
                liste.append((wann, e, f"Weiter bei {uhr(s['pos'])}"))
        for e in self.filme():
            s = self.stand.get(e["pfad"], {})
            if s and not s.get("fertig") and s.get("pos", 0) > 30:
                rest = max(0, s.get("dauer", 0) - s["pos"])
                liste.append((s.get("zeit", 0), e, f"Noch {dauer_text(rest)}"))
        liste.sort(key=lambda t: -t[0])
        return [(e, info) for _, e, info in liste]

    # ---- Anzeigen

    def name_von(self, e):
        if e["art"] == "serie":
            t = f"{e['serie']} · S{e['staffel']:02d}E{e['folge']:02d}"
            return t + (f" · {e['titel']}" if e["titel"] else "")
        return e["titel"] + (f" ({e['jahr']})" if e.get("jahr") else "")

    def karte(self, e, titel=None, unter=None, gross=False, aktion=None):
        anteil, fertig, _ = self.fortschritt(e)
        if titel is None:
            titel = e["serie"] if e["art"] == "serie" else e["titel"]
        if unter is None:
            if e["art"] == "serie":
                unter = f"S{e['staffel']:02d}E{e['folge']:02d}" + (f" · {e['titel']}" if e["titel"] else "")
            else:
                d = self.bilder.dauer(e)
                unter = " · ".join(x for x in (e.get("jahr") or "", dauer_text(d) if d else "") if x)
        k = Karte(self, e, titel, unter, anteil if not fertig else 0, fertig, gross)
        k.geklickt.connect(aktion or (lambda: self.abspielen_ab(e)))
        return k

    def zeigen(self, key, neu=False):
        self.aktuell = key
        for k, b in self.nav.items():
            b.setChecked(k == key)
        seite = getattr(self, "seite_" + key)()
        alt = self.stack.currentWidget()
        self.stack.addWidget(seite)
        self.stack.setCurrentWidget(seite)
        if alt is not None:
            self.stack.removeWidget(alt)
            alt.deleteLater()

    def seite_saal(self):
        s = Seite()
        weiter = self.weiterschauen()
        if not self.alle:
            leer = self.einleser is not None and not self.einleser.isRunning()
            knoepfe = [knopf("Ordner hinzufügen", "orange", self.ordner_hinzu)]
            if leere_platten():
                knoepfe.append(knopf("Leere Platte für Filme einrichten", cb=self.platte_einrichten))
            s.body.addWidget(Leinwand(
                None, "Willkommen im Saal", "Noch keine Filme hier." if leer else "Sammlung wird eingelesen …",
                "Bibiplexx sucht in deinen Ordnern nach Filmen und Serien: "
                + ", ".join(self.einst["ordner"]) + ". Serien erkennt es an S01E02 im Dateinamen.", knoepfe))
            return s
        if weiter:
            e, info = weiter[0]
            titel = self.name_von(e)
            b1 = knopf("Weiterschauen" if "Nächste" not in info else "Nächste Folge abspielen", "orange", lambda: self.abspielen_ab(e))
            knoepfe = [b1]
            if "Nächste" not in info:
                knoepfe.append(knopf("Von vorn", cb=lambda: self.abspielen_ab(e, von_vorn=True)))
            knoepfe.append(knopf("Überrasch mich", cb=self.ueberraschung))
            s.body.addWidget(Leinwand(self.bilder.pixmap(e), "Weiterschauen", titel, info, knoepfe, self, e))
            s.body.addWidget(Reihe("Weiterschauen", [self.karte(e2, unter=info2) for e2, info2 in weiter[:20]]))
        else:
            neueste = max(self.alle, key=lambda e: e["mtime"])
            s.body.addWidget(Leinwand(self.bilder.pixmap(neueste), "Neu im Saal", self.name_von(neueste),
                                      "Frisch dazugekommen.", [knopf("Abspielen", "orange", lambda: self.abspielen_ab(neueste)),
                                                               knopf("Überrasch mich", cb=self.ueberraschung)],
                                      self, neueste))
        serien = self.serien()
        if serien:
            s.body.addWidget(Reihe("Serien", [self.serien_karte(n, f) for n, f in list(serien.items())[:30]]))
        filme = self.filme()
        if filme:
            s.body.addWidget(Reihe("Filme", [self.karte(e) for e in filme[:30]]))
        neu = sorted(self.alle, key=lambda e: -e["mtime"])[:20]
        s.body.addWidget(Reihe("Neu dazugekommen", [self.karte(e, titel=self.name_von(e), unter="") for e in neu]))
        return s

    def serien_karte(self, name, folgen):
        gesehen = sum(1 for e in folgen if self.stand.get(e["pfad"], {}).get("fertig"))
        staffeln = len({e["staffel"] for e in folgen})
        unter = f"{staffeln} Staffel{'n' if staffeln != 1 else ''} · {len(folgen)} Folgen" + (f" · {gesehen} gesehen" if gesehen else "")
        k = Karte(self, folgen[0], name, unter, gesehen / len(folgen) if gesehen < len(folgen) else 0, gesehen == len(folgen))
        k.serie = name
        k.geklickt.connect(lambda: self.serie_zeigen(name))
        return k

    def seite_serien(self):
        s = Seite()
        s.body.addWidget(label("Serien", "h1"))
        serien = self.serien()
        if not serien:
            s.body.addWidget(label("Noch keine Serien gefunden. Dateien mit S01E01 im Namen werden als Serie erkannt.", "leise", wrap=True))
        r = s.raster()
        for n, f in serien.items():
            r.addWidget(self.serien_karte(n, f))
        return s

    def seite_filme(self):
        s = Seite()
        kopf = QHBoxLayout()
        kopf.addWidget(label("Filme", "h1"))
        kopf.addStretch(1)
        sortieren = QComboBox()
        for wert, text in (("az", "A bis Z"), ("neu", "Zuletzt hinzugefügt"), ("jahr", "Neueste Filme zuerst")):
            sortieren.addItem(text, wert)
        werte = ["az", "neu", "jahr"]
        sortieren.setCurrentIndex(werte.index(self.einst["sortierung"]) if self.einst["sortierung"] in werte else 0)
        sortieren.currentIndexChanged.connect(lambda i: (self.einst.__setitem__("sortierung", werte[i]), self.speichern(), self.zeigen("filme")))
        kopf.addWidget(sortieren)
        s.body.addLayout(kopf)
        filme = self.filme()
        if self.einst["sortierung"] == "neu":
            filme.sort(key=lambda e: -e["mtime"])
        elif self.einst["sortierung"] == "jahr":
            filme.sort(key=lambda e: -(int(e.get("jahr") or 0)))
        if not filme:
            s.body.addWidget(label("Noch keine Filme gefunden.", "leise"))
        r = s.raster()
        for e in filme:
            r.addWidget(self.karte(e))
        return s

    def seite_suche(self):
        s = Seite()
        q = self.suche.text().strip().lower()
        s.body.addWidget(label(f"Suche: {self.suche.text().strip()}", "h1"))
        serien = {n: f for n, f in self.serien().items() if q in n.lower()}
        filme = [e for e in self.filme() if q in e["titel"].lower()]
        if not serien and not filme:
            s.body.addWidget(label("Nichts gefunden.", "leise"))
        r = s.raster()
        for n, f in serien.items():
            r.addWidget(self.serien_karte(n, f))
        for e in filme:
            r.addWidget(self.karte(e))
        return s

    def suchen(self):
        if self.suche.text().strip():
            self.zeigen("suche")

    def serie_zeigen(self, name, staffel=None):
        folgen = self.serien().get(name, [])
        if not folgen:
            return
        staffeln = sorted({e["staffel"] for e in folgen})
        if staffel is None:
            # Staffel der naechsten ungesehenen Folge
            offen = [e for e in folgen if not self.stand.get(e["pfad"], {}).get("fertig")]
            staffel = (offen[0] if offen else folgen[0])["staffel"]
        s = Seite()
        kopf = QHBoxLayout()
        kopf.addWidget(knopf("‹ Serien", cb=lambda: self.zeigen("serien")))
        kopf.addStretch(1)
        s.body.addLayout(kopf)
        s.body.addWidget(label(name, "h1"))
        reihe = QHBoxLayout()
        for st in staffeln:
            b = knopf(f"Staffel {st}", cb=lambda _=False, x=st: self.serie_zeigen(name, x))
            b.setCheckable(True)
            b.setChecked(st == staffel)
            b.setMinimumWidth(b.fontMetrics().horizontalAdvance(b.text()) * 13 // 10 + 36)
            reihe.addWidget(b)
        reihe.addStretch(1)
        s.body.addLayout(reihe)
        for e in [f for f in folgen if f["staffel"] == staffel]:
            s.body.addWidget(self.folgen_zeile(e, folgen))
        self.aktuell = "serie"
        for b in self.nav.values():
            b.setChecked(False)
        self.nav["serien"].setChecked(True)
        alt = self.stack.currentWidget()
        self.stack.addWidget(s)
        self.stack.setCurrentWidget(s)
        if alt is not None:
            self.stack.removeWidget(alt)
            alt.deleteLater()

    def folgen_zeile(self, e, folgen):
        anteil, fertig, st = self.fortschritt(e)
        z = QFrame()
        z.setObjectName("zeile")
        z.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        z.setCursor(Qt.CursorShape.PointingHandCursor)
        zl = QHBoxLayout(z)
        zl.setContentsMargins(12, 10, 16, 10)
        zl.setSpacing(16)
        k = Karte(self, e, "", "", anteil if not fertig else 0, fertig)
        k.bw, k.bh = 192, 108
        k.setFixedSize(192, 108)
        k.geklickt.connect(lambda: self.abspielen_ab(e))
        zl.addWidget(k)
        col = QVBoxLayout()
        t = label(f"Folge {e['folge']}" + (f" · {e['titel']}" if e["titel"] else ""))
        t.setStyleSheet("font-weight: 700; font-size: 11.5pt;")
        col.addWidget(t)
        d = st.get("dauer") or self.bilder.dauer(e)
        info = []
        if d:
            info.append(dauer_text(d))
        if fertig:
            info.append("gesehen")
        elif st.get("pos", 0) > 30:
            info.append(f"noch {dauer_text(max(0, d - st['pos']))}")
        col.addWidget(label(" · ".join(info) or "Noch nicht gesehen", "leise"))
        col.addStretch(1)
        zl.addLayout(col, 1)
        zl.addWidget(knopf("Abspielen", "orange", lambda: self.abspielen_ab(e)))
        z.mouseReleaseEvent = lambda ev: self.abspielen_ab(e) if ev.button() == Qt.MouseButton.LeftButton else None
        return z

    # ---- Abspielen

    def serie_weiter(self, folgen):
        """Welche Folge als naechstes dran ist: angefangene, sonst die nach der zuletzt gesehenen."""
        zuletzt, wann = None, 0
        for i, e in enumerate(folgen):
            z = self.stand.get(e["pfad"], {}).get("zeit", 0)
            if z and z >= wann:
                zuletzt, wann = i, z
        if zuletzt is not None:
            s = self.stand[folgen[zuletzt]["pfad"]]
            if not s.get("fertig"):
                return folgen[zuletzt]
            if zuletzt + 1 < len(folgen):
                return folgen[zuletzt + 1]
        offen = [e for e in folgen if not self.stand.get(e["pfad"], {}).get("fertig")]
        return (offen or folgen)[0]

    def abspielen_ab(self, e, von_vorn=False):
        """Film spielen; bei Serien laufen die folgenden Folgen gleich weiter (wenn eingestellt)."""
        liste = [e]
        if e["art"] == "serie" and self.einst["autoplay"]:
            folgen = self.serien().get(e["serie"], [])
            if e in folgen:
                liste = folgen[folgen.index(e):]
        start = 0 if von_vorn else self.stand.get(e["pfad"], {}).get("pos", 0)
        if self.stand.get(e["pfad"], {}).get("fertig"):
            start = 0
        self.abspielen([(x, self.name_von(x)) for x in liste], start)

    def ueberraschung(self):
        """Ueberrasch mich: ein ungesehener Film oder die naechste Folge einer zufaelligen Serie."""
        filme = [e for e in self.filme() if not self.stand.get(e["pfad"], {}).get("fertig")]
        serien = [self.serie_weiter(f) for f in self.serien().values()]
        auswahl = filme + serien
        if not auswahl:
            return
        self.abspielen_ab(random.choice(auswahl))

    def abspielen(self, liste, start=0):
        if self.mpv is not None and self.mpv.state() != QProcess.ProcessState.NotRunning:
            return
        if not shutil.which("mpv"):
            QMessageBox.warning(self, "Bibiplexx", "mpv fehlt. Bitte im Terminal: bibi apt install mpv")
            return
        ZUSTAND.mkdir(parents=True, exist_ok=True)
        args = mpv_argumente(liste, start, self.einst)
        self.mpv = QProcess(self)
        self.mpv.finished.connect(self._mpv_fertig)
        self.mpv.errorOccurred.connect(self._mpv_fehler)
        if self.einst["kino"] != "aus" and self.isVisible():
            self._blende(1.0, lambda: self.mpv.start("mpv", args))
        else:
            self.mpv.start("mpv", args)

    def _mpv_fehler(self, fehler):
        if fehler == QProcess.ProcessError.FailedToStart:
            self._blende(0.0)
            QMessageBox.warning(self, "Bibiplexx", "Der Player (mpv) ließ sich nicht starten.")

    def _blende(self, ziel, danach=None):
        self.blende.setGeometry(self.centralWidget().rect())
        start = self.blende_eff.opacity() if self.blende.isVisible() else 0.0
        self.blende.raise_()
        self.blende.show()
        an = QPropertyAnimation(self.blende_eff, b"opacity", self)
        an.setDuration(450)
        an.setStartValue(start)
        an.setEndValue(ziel)
        an.setEasingCurve(QEasingCurve.Type.InOutCubic)
        if danach:
            an.finished.connect(danach)
        if ziel == 0.0:
            an.finished.connect(self.blende.hide)
        an.start()

    def _mpv_fertig(self, *_):
        self.stand_laden()
        if self.blende.isVisible():
            self._blende(0.0)
        self.zeigen(self.aktuell if self.aktuell in ("saal", "serien", "filme") else "saal")

    # ---- Rechtsklick auf Karten

    def stand_setzen(self, pfade, fertig):
        """Gesehen/ungesehen markieren (gleiches Format wie der Player)."""
        stand = json_lesen(STAND, {})
        for p in pfade:
            alt = stand.get(p, {})
            stand[p] = {"pos": 0, "dauer": alt.get("dauer", 0), "zeit": time.time() if fertig else 0, "fertig": fertig}
            if not fertig:
                stand.pop(p, None)
        json_schreiben(STAND, stand)
        self.stand_laden()
        self.zeigen(self.aktuell if self.aktuell in ("saal", "serien", "filme", "suche") else "saal")

    def aus_weiterschauen(self, pfad):
        stand = json_lesen(STAND, {})
        if pfad in stand:
            stand[pfad]["pos"] = 0
            stand[pfad]["zeit"] = 0
        json_schreiben(STAND, stand)
        self.stand_laden()
        self.zeigen(self.aktuell if self.aktuell in ("saal", "serien", "filme", "suche") else "saal")

    def zeigen_im_dateimanager(self, pfad):
        if shutil.which("dolphin"):
            QProcess.startDetached("dolphin", ["--select", pfad])
        else:
            QProcess.startDetached("xdg-open", [str(Path(pfad).parent)])

    def kontextmenue(self, karte, pos):
        e = karte.e
        if e is None:
            return
        m = QMenu(self)
        m.setStyleSheet(STIL)
        serie = getattr(karte, "serie", None)
        if serie:
            folgen = self.serien().get(serie, [])
            weiter = self.serie_weiter(folgen)
            m.addAction(f"Weiterschauen (S{weiter['staffel']:02d}E{weiter['folge']:02d})", lambda: self.abspielen_ab(weiter))
            m.addAction("Folgen anzeigen", lambda: self.serie_zeigen(serie))
            m.addSeparator()
            m.addAction("Ganze Serie als gesehen markieren", lambda: self.stand_setzen([f["pfad"] for f in folgen], True))
            m.addAction("Ganze Serie als ungesehen markieren", lambda: self.stand_setzen([f["pfad"] for f in folgen], False))
        else:
            st = self.stand.get(e["pfad"], {})
            m.addAction("Abspielen", lambda: self.abspielen_ab(e))
            m.addAction("Von vorn abspielen", lambda: self.abspielen_ab(e, von_vorn=True))
            m.addSeparator()
            if st.get("fertig"):
                m.addAction("Als ungesehen markieren", lambda: self.stand_setzen([e["pfad"]], False))
            else:
                m.addAction("Als gesehen markieren", lambda: self.stand_setzen([e["pfad"]], True))
            if st.get("pos", 0) > 30 and not st.get("fertig"):
                m.addAction("Aus „Weiterschauen“ entfernen", lambda: self.aus_weiterschauen(e["pfad"]))
        m.addSeparator()
        m.addAction("Im Dateimanager zeigen", lambda: self.zeigen_im_dateimanager(e["pfad"]))
        m.exec(pos)

    # ---- Einstellungen

    def speichern(self):
        json_schreiben(KONFIG, self.einst)

    def ordner_hinzu(self):
        d = QFileDialog.getExistingDirectory(self, "Ordner mit Filmen oder Serien", str(Path.home()))
        if d and d not in self.einst["ordner"]:
            self.einst["ordner"].append(d)
            self.speichern()
            self.neu_einlesen()

    def einstellungen_zeigen(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Bibiplexx – Einstellungen")
        dlg.setStyleSheet(STIL)
        dlg.setMinimumWidth(640)
        aussen = QVBoxLayout(dlg)
        aussen.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        innen = QWidget()
        innen.setObjectName("seite")
        lay = QVBoxLayout(innen)
        lay.setContentsMargins(24, 18, 24, 18)
        lay.setSpacing(8)
        scroll.setWidget(innen)
        aussen.addWidget(scroll, 1)

        def wahl(titel, schluessel, optionen, hinweis=""):
            """Zeile mit Beschriftung und Auswahlliste; speichert sofort."""
            z = QHBoxLayout()
            z.addWidget(label(titel), 1)
            box = QComboBox()
            for wert, text in optionen:
                box.addItem(text, wert)
            werte = [w for w, _ in optionen]
            box.setCurrentIndex(werte.index(self.einst[schluessel]) if self.einst[schluessel] in werte else 0)
            box.currentIndexChanged.connect(lambda i: (self.einst.__setitem__(schluessel, box.itemData(i)), self.speichern()))
            box.setFixedWidth(250)
            z.addWidget(box)
            lay.addLayout(z)
            if hinweis:
                lay.addWidget(label(hinweis, "leise", wrap=True))

        def schalter(text, schluessel, hinweis=""):
            c = QCheckBox(text)
            c.setChecked(bool(self.einst[schluessel]))
            c.toggled.connect(lambda an: (self.einst.__setitem__(schluessel, an), self.speichern()))
            lay.addWidget(c)
            if hinweis:
                lay.addWidget(label(hinweis, "leise", wrap=True))

        lay.addWidget(label("Sammlung", "h2"))
        liste = QVBoxLayout()
        lay.addLayout(liste)

        def neu_aufbauen():
            while liste.count():
                w = liste.takeAt(0).widget()
                if w:
                    w.deleteLater()
            for d in self.einst["ordner"]:
                z = QWidget()
                zl = QHBoxLayout(z)
                zl.setContentsMargins(0, 0, 0, 0)
                ordner = label(d + ("" if Path(d).is_dir() else "  (nicht da)"), wrap=True)
                ordner.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
                zl.addWidget(ordner, 1)
                zl.addWidget(knopf("Entfernen", cb=lambda _=False, x=d: (self.einst["ordner"].remove(x), self.speichern(), neu_aufbauen())))
                liste.addWidget(z)
        neu_aufbauen()
        reihe = QHBoxLayout()
        reihe.addWidget(knopf("Ordner hinzufügen", cb=lambda: (self.ordner_hinzu(), neu_aufbauen())))
        reihe.addWidget(knopf("Leere Platte einrichten", cb=lambda: (self.platte_einrichten(), neu_aufbauen())))
        reihe.addWidget(knopf("Neu einlesen", cb=self.neu_einlesen))
        reihe.addStretch(1)
        lay.addLayout(reihe)

        lay.addWidget(label("Kino", "h2"))
        wahl("Kinomodus beim Start", "kino", [("vorhang_gong", "Vorhang und Gong"), ("vorhang", "Nur Vorhang"), ("aus", "Aus")],
             "Saal wird dunkel, der Vorhang geht auf. „Reihe sieben.“")
        schalter("Nachtmodus", "nachtmodus", "Leise Stellen lauter, Explosionen leiser. Auch im Film unten in der Leiste umschaltbar.")

        lay.addWidget(label("Sprache und Untertitel", "h2"))
        wahl("Tonspur", "sprache", [("deutsch", "Deutsch, sonst Englisch"), ("original", "Originalton")])
        wahl("Untertitel", "untertitel", [("fremd", "Nur bei fremder Sprache"),
                                          ("deutsch", "Immer deutsche Untertitel"), ("aus", "Aus")])
        wahl("Untertitel-Größe", "ut_groesse", [("klein", "Klein"), ("mittel", "Mittel"), ("gross", "Groß")])
        wahl("Untertitel-Farbe", "ut_farbe", [("weiss", "Weiß"), ("gelb", "Kino-Gelb")])

        lay.addWidget(label("Serien", "h2"))
        schalter("Nächste Folge automatisch abspielen", "autoplay")
        wahl("Countdown vor der nächsten Folge", "countdown", [(10, "10 Sekunden"), (15, "15 Sekunden"), (25, "25 Sekunden"), (0, "Kein Countdown")])
        schalter("Knopf „Intro überspringen“", "intro_knopf", "Erscheint, wenn die Folge ein Kapitel wie Intro, Vorspann oder Rückblick hat.")

        lay.addWidget(label("Im Film", "h2"))
        lay.addWidget(label("Mausrad: Lautstärke (mehr als 100 % gibt es nicht) · Leertaste: Pause · Pfeiltasten: spulen · "
                            "F: Vollbild · T: Schlaf-Timer · N: Nachtmodus · Esc: Fenster/Ende.", "leise", wrap=True))
        lay.addStretch(1)

        unten = QHBoxLayout()
        unten.setContentsMargins(24, 10, 24, 16)
        unten.addWidget(label(f"Bibiplexx {VERSION}", "leise"))
        unten.addStretch(1)
        unten.addWidget(knopf("Fertig", "orange", dlg.accept))
        aussen.addLayout(unten)
        dlg.resize(680, 720)
        dlg.exec()
        self.neu_einlesen()

    def platte_einrichten(self):
        platten = leere_platten()
        if not platten:
            QMessageBox.information(self, "Bibiplexx", "Keine leere Platte gefunden.\n\n"
                                    "Eingerichtet wird nur eine Platte ganz ohne Partitionen, damit nie etwas verloren geht.")
            return
        namen = [f"{p['model'] or p['name']}  ({p['groesse']} GB, {p['path']})" for p in platten]
        if len(platten) == 1:
            wahl, ok = namen[0], True
        else:
            wahl, ok = QInputDialog.getItem(self, "Bibiplexx", "Welche leere Platte soll die Film-Platte werden?", namen, 0, False)
        if not ok:
            return
        p = platten[namen.index(wahl)]
        frage = QMessageBox.question(
            self, "Platte für Filme einrichten",
            f"{wahl}\n\nDiese Platte ist leer. Bibiplexx richtet sie als Film- und Serienplatte ein "
            f"(Ordner {PLATTE_ORT}, mit „Filme“ und „Serien“). Sie ist danach bei jedem Start da.\n\nJetzt einrichten?")
        if frage != QMessageBox.StandardButton.Yes:
            return
        out = subprocess.run(["pkexec", PLATTE_HELFER, p["path"]], capture_output=True, text=True)
        if out.returncode != 0:
            QMessageBox.warning(self, "Bibiplexx", "Hat nicht geklappt.\n\n" + (out.stderr or out.stdout).strip())
            return
        if str(PLATTE_ORT) not in self.einst["ordner"]:
            self.einst["ordner"].append(str(PLATTE_ORT))
            self.speichern()
        QMessageBox.information(self, "Bibiplexx", f"Fertig. Deine Filme kommen nach {PLATTE_ORT}/Filme, "
                                "Serien nach {0}/Serien.\n\nIm Dateimanager heißt die Platte „Bibiplexx“.".format(PLATTE_ORT))
        self.neu_einlesen()

    def changeEvent(self, ev):
        super().changeEvent(ev)
        if ev.type() == ev.Type.ActivationChange and self.isActiveWindow() and time.time() - self.zuletzt_eingelesen > 60:
            self.neu_einlesen()

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if self.blende.isVisible():
            self.blende.setGeometry(self.centralWidget().rect())


def leere_platten():
    """Platten ganz ohne Partitionen und Dateisystem (z. B. frisch geloeschte SSD)."""
    try:
        daten = json.loads(run(["lsblk", "-J", "-b", "-o", "NAME,PATH,MODEL,SIZE,TYPE,RO,FSTYPE,PTTYPE"]) or "{}")
    except ValueError:
        return []
    ergebnis = []
    for d in daten.get("blockdevices", []):
        if d.get("type") != "disk" or d.get("children") or d.get("fstype") or d.get("pttype"):
            continue
        if str(d.get("ro")).lower() in ("1", "true") or d.get("name", "").startswith(("loop", "zram", "sr", "ram")):
            continue
        groesse = int(d.get("size") or 0)
        if groesse < 8_000_000_000:
            continue
        ergebnis.append({"name": d["name"], "path": d.get("path") or "/dev/" + d["name"],
                         "model": (d.get("model") or "").strip(), "groesse": round(groesse / 1e9)})
    return ergebnis


NACHT_FILTER = "@nacht:lavfi=[dynaudnorm=f=150:g=15:p=0.7]"
DEUTSCH = "de,ger,deu"


def mpv_argumente(liste, start, einst):
    """liste: [(eintrag, titel)]. Startzeit gilt nur fuer die erste Datei."""
    kino = einst["kino"] != "aus"
    gong = str(GONG) if einst["kino"] == "vorhang_gong" else ""
    countdown = int(einst["countdown"]) if einst["autoplay"] else 0
    args = [f"--include={MPV_CONF}", f"--script={MPV_LUA}",
            f"--script-opts=bibiplexx-kino={'yes' if kino else 'no'},bibiplexx-gong={gong},bibiplexx-stand={STAND},"
            f"bibiplexx-countdown={countdown},bibiplexx-intro_knopf={'yes' if einst['intro_knopf'] else 'no'}"]
    if einst["sprache"] == "deutsch":
        args.append(f"--alang={DEUTSCH},en,eng")
    if einst["untertitel"] == "aus":
        args.append("--sid=no")
    elif einst["untertitel"] == "deutsch":
        args += [f"--slang={DEUTSCH}", "--subs-with-matching-audio=yes"]
    else:
        args += [f"--slang={DEUTSCH},en,eng", "--subs-with-matching-audio=no"]
    args.append("--sub-font-size=" + {"klein": "36", "mittel": "44", "gross": "56"}.get(einst["ut_groesse"], "44"))
    if einst["ut_farbe"] == "gelb":
        args.append("--sub-color=#FFE45C")
    if einst["nachtmodus"]:
        args.append(f"--af={NACHT_FILTER}")
    for i, (e, titel) in enumerate(liste):
        args.append("--{")
        args.append(f"--force-media-title={titel}")
        if i == 0 and start > 5:
            args.append(f"--start={int(start)}")
        args += [e["pfad"], "--}"]
    return args


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Bibiplexx")
    app.setDesktopFileName("de.biblix.Bibiplexx")
    dateien = [a for a in sys.argv[1:] if not a.startswith("-")]
    if dateien:
        # Direkt abspielen ("Oeffnen mit Bibiplexx"), ohne Sammlung
        ZUSTAND.mkdir(parents=True, exist_ok=True)
        stand = json_lesen(STAND, {})
        liste = []
        for d in dateien:
            p = str(Path(d).resolve()) if not d.startswith(("http://", "https://")) else d
            e = {"pfad": p, "art": "film", "titel": Path(d).stem}
            liste.append((e, aufraeumen(Path(d).stem) or Path(d).name))
        s = stand.get(liste[0][0]["pfad"], {})
        start = 0 if s.get("fertig") else s.get("pos", 0)
        sys.exit(subprocess.call(["mpv", *mpv_argumente(liste, start, einstellungen())]))
    w = Haupt()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
