#!/usr/bin/env python3
"""Bibi Solitär – die klassische Patience (Klondike) für die Bibi Arcade.

Ziel: alle 52 Karten nach Farbe von A bis K auf die vier Zielstapel oben rechts.
In den sieben Reihen legt man absteigend und abwechselnd rot/schwarz an,
auf eine leere Reihe darf nur ein König.

Bedienung:
  Pfeiltasten  Zeiger bewegen (in einer Reihe: hoch/runter wählt die Karte)
  Enter        Karte(n) aufnehmen bzw. am Zeiger ablegen; auf dem Stapel: nachziehen
  Leertaste    Schnellzug: die Karte(n) an den besten Platz legen
  Backspace    aufgenommene Karte loslassen, sonst letzten Zug zurücknehmen
  Maus         ziehen und fallen lassen; Klick = Schnellzug

Stufen:
  Lehrling  1 Karte ziehen, beliebig viele Durchgänge
  Geselle   3 Karten ziehen, beliebig viele Durchgänge
  Meister   3 Karten ziehen, höchstens 3 Durchgänge

Testen:  python3 spiel.py [Lehrling|Geselle|Meister]
"""

import json
import math
import random
import shutil
import sys
import time
from pathlib import Path

from PyQt6.QtCore import QPointF, QProcess, QRectF, Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import (QColor, QFont, QFontMetricsF, QLinearGradient, QPainter,
                         QPainterPath, QPen, QPixmap, QPolygonF, QRadialGradient)
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget

try:  # Nur da, wenn python3-pyqt6.qtmultimedia installiert ist.
    from PyQt6.QtMultimedia import QSoundEffect
except ImportError:
    QSoundEffect = None


# Alle Farben an einer Stelle: der Standard-Skin „Biblix“ (Palette Bibi Tech).
FARBEN = {
    "tisch": "#0f141c",
    "tisch_licht": "#1b2433",      # heller Schein in der Tischmitte
    "tisch_raster": "#131a24",
    "tisch_zeichen": "#161e2b",    # großes Schrauben-B im Hintergrund
    "hud": "#1a2029",
    "hud_rand": "#313a48",
    "text": "#e8ecf2",
    "text_leise": "#8b95a5",
    "akzent": "#378add",           # Tastatur-Zeiger, Stufen-Abzeichen
    "gehalten": "#ffd400",         # aufgenommene Karten, Stern bei den Punkten
    "passt": "#4cc38a",            # Plätze, auf die die Karte(n) passen
    "platz": "#141b25",
    "platz_rand": "#2c3542",
    "platz_symbol": "#3a4554",
    "karte": "#f7f9fb",
    "karte_unten": "#e8ecf1",      # Verlauf zum unteren Kartenrand
    "karte_rand": "#aab3bf",
    "rot": "#d93a3a",
    "rot_hell": "#fbe4e4",
    "schwarz": "#1a2029",
    "schwarz_hell": "#e2e8f0",
    "schatten": "#000000",
    "rueckseite": "#1b2a44",
    "rueckseite_muster": "#223558",
    "rueckseite_rand": "#378add",
    "rueckseite_b": "#ffd400",
    "abzeichen": "#0b0d12",        # Kartenzahl am Nachziehstapel
    "fenster": "#161c26",          # Ergebnis- und Pausenfenster
    "abdunkeln": "#05070a",
    "gewonnen": "#4cc38a",
    "verloren": "#e24b4a",
    "konfetti_1": "#ffd400",
    "konfetti_2": "#378add",
    "konfetti_3": "#4cc38a",
    "konfetti_4": "#e8ecf2",
}

KENNUNG = "bibi_solitaer"
ORDNER = Path(__file__).resolve().parent

# Karten nachziehen, erlaubte Durchgänge (None = beliebig), Punkte-Faktor
STUFEN = {
    "Lehrling": (1, None, 1),
    "Geselle": (3, None, 2),
    "Meister": (3, 3, 3),
}
ZIELZEIT = 600  # Sekunden; wer schneller ist, bekommt Zeitbonus

# Nur Sprüche, die es im Bibi-Universum schon gibt (siehe biblix-design/sprueche.txt).
SPRUECHE_GEWONNEN = [
    "AUF BIBLIX GEHT DAS.",
    "Gut ist gut.",
    "DU BIST AUF DEM AKTUELLEN STAND.",
]
SPRUECHE_VERLOREN = [
    "DEIN SYSTEM. DEIN PROBLEM.",
    "Oben kann man Fehler korrigieren. Unten muss man sie verhindern.",
    "DER ZUG FÄHRT TROTZDEM.",
]

MELDE_VERZOEGERUNG_MS = 1500
FLUG_DAUER = 0.16      # Sekunden, die eine Karte zum neuen Platz fliegt
AUTO_TAKT_MS = 90      # Tempo beim automatischen Ablegen am Ende

RANG_ZEICHEN = {1: "A", 11: "B", 12: "D", 13: "K"}  # Ass, Bube, Dame, König

NACHZIEH = ("nachzieh", 0)
ABLAGE = ("ablage", 0)
ZIELE = [("ziel", i) for i in range(4)]
REIHEN = [("reihe", i) for i in range(7)]
OBEN = [NACHZIEH, ABLAGE, None, *ZIELE]   # Spalten der oberen Zeile


def _sekunden(wert):
    return f"{wert:.1f} s".replace(".", ",")


def _uhrzeit(wert):
    wert = int(wert)
    return f"{wert // 60:02d}:{wert % 60:02d}"


class Karte:
    __slots__ = ("farbe", "rang", "offen")

    def __init__(self, farbe, rang):
        self.farbe = farbe    # 0 Herz, 1 Karo, 2 Pik, 3 Kreuz
        self.rang = rang      # 1 (Ass) bis 13 (König)
        self.offen = False

    @property
    def rot(self):
        return self.farbe < 2

    @property
    def zeichen(self):
        return RANG_ZEICHEN.get(self.rang, str(self.rang))


# ----------------------------------------------------------------------
# Skins: alles, was man sieht. Ein neuer Skin (z. B. Bibi Mac, Bibiplexx)
# ist eine Unterklasse mit eigenen Farben und, wenn gewünscht, eigenen
# Zeichen-Methoden. Danach nur in SKINS eintragen.

def _farbsymbol(farbe):
    """Herz, Karo, Pik, Kreuz als Form um (0, 0) mit Größe 1."""
    pfad = QPainterPath()
    pfad.setFillRule(Qt.FillRule.WindingFill)
    if farbe == 0:
        pfad.moveTo(0, 0.45)
        pfad.cubicTo(-0.15, 0.3, -0.5, 0.05, -0.5, -0.15)
        pfad.cubicTo(-0.5, -0.42, -0.12, -0.5, 0, -0.25)
        pfad.cubicTo(0.12, -0.5, 0.5, -0.42, 0.5, -0.15)
        pfad.cubicTo(0.5, 0.05, 0.15, 0.3, 0, 0.45)
    elif farbe == 1:
        pfad.addPolygon(QPolygonF([QPointF(0, -0.5), QPointF(0.38, 0),
                                   QPointF(0, 0.5), QPointF(-0.38, 0)]))
        pfad.closeSubpath()
    elif farbe == 2:
        pfad.moveTo(0, -0.5)
        pfad.cubicTo(0.15, -0.35, 0.5, -0.12, 0.5, 0.08)
        pfad.cubicTo(0.5, 0.32, 0.15, 0.36, 0, 0.18)
        pfad.cubicTo(-0.15, 0.36, -0.5, 0.32, -0.5, 0.08)
        pfad.cubicTo(-0.5, -0.12, -0.15, -0.35, 0, -0.5)
        pfad.addPolygon(QPolygonF([QPointF(0, 0.1), QPointF(0.16, 0.5), QPointF(-0.16, 0.5)]))
        pfad.closeSubpath()
    else:
        for x, y in ((0, -0.24), (-0.24, 0.06), (0.24, 0.06)):
            pfad.addEllipse(QPointF(x, y), 0.21, 0.21)
        pfad.addEllipse(QPointF(0, -0.02), 0.12, 0.12)
        pfad.addPolygon(QPolygonF([QPointF(0, 0), QPointF(0.14, 0.5), QPointF(-0.14, 0.5)]))
        pfad.closeSubpath()
    return pfad


SYMBOLE = [_farbsymbol(f) for f in range(4)]


def _sechseck(mitte, radius):
    return QPolygonF([
        mitte + QPointF(math.cos(math.radians(30 + 60 * i)) * radius,
                        math.sin(math.radians(30 + 60 * i)) * radius)
        for i in range(6)
    ])


class BiblixSkin:
    """Standard-Look: dunkler Tisch mit Licht, helle Karten, Rückseite mit Schrauben-B."""

    name = "Biblix"

    def __init__(self, farben=None):
        self.f = farben or FARBEN

    def c(self, name, alpha=None):
        farbe = QColor(self.f[name])
        if alpha is not None:
            farbe.setAlpha(alpha)
        return farbe

    def schrift(self, pixel, fett=False):
        schrift = QFont()
        schrift.setPixelSize(max(6, int(pixel)))
        schrift.setBold(fett)
        return schrift

    def symbol(self, p, farbe, mitte, groesse, brush):
        p.save()
        p.translate(mitte)
        p.scale(groesse, groesse)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(brush)
        p.drawPath(SYMBOLE[farbe])
        p.restore()

    def tisch(self, p, rect, raster, zeichen):
        """Tisch: Grundfarbe, Licht, feines Raster, Schrauben-B, dunkle Ränder."""
        p.fillRect(rect, self.c("tisch"))
        licht = QRadialGradient(QPointF(rect.center().x(), rect.top() + rect.height() * 0.38),
                                max(rect.width(), rect.height()) * 0.7)
        licht.setColorAt(0, self.c("tisch_licht"))
        licht.setColorAt(1, self.c("tisch_licht", 0))
        p.fillRect(rect, licht)

        p.setPen(QPen(self.c("tisch_raster"), 1.0))
        x = rect.left() + raster / 2
        while x < rect.right():
            p.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += raster
        y = rect.top() + raster / 2
        while y < rect.bottom():
            p.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += raster

        if zeichen.height() > 120:
            mitte = zeichen.center()
            r = min(zeichen.width(), zeichen.height()) * 0.4
            p.setPen(QPen(self.c("tisch_zeichen"), max(2.0, r * 0.07)))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPolygon(_sechseck(mitte, r))
            p.setPen(QPen(self.c("tisch_zeichen"), max(1.0, r * 0.025)))
            p.drawEllipse(mitte, r * 0.84, r * 0.84)
            pfad = QPainterPath()
            pfad.addText(0, 0, self.schrift(r * 1.05, True), "B")
            pfad.translate(mitte - pfad.boundingRect().center())
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self.c("tisch_zeichen"))
            p.drawPath(pfad)

        rand = QRadialGradient(rect.center(), max(rect.width(), rect.height()) * 0.75)
        rand.setColorAt(0.55, self.c("schatten", 0))
        rand.setColorAt(1, self.c("schatten", 120))
        p.fillRect(rect, rand)

    def schatten(self, p, rect, hoehe=1.0):
        """Weicher Schatten unter einer Karte; hoehe > 1 = Karte schwebt."""
        w = rect.width()
        r = w * 0.08
        p.setPen(Qt.PenStyle.NoPen)
        for i, alpha in enumerate((46, 28, 14)):
            d = w * 0.012 * (i + 1) * hoehe
            p.setBrush(self.c("schatten", alpha))
            p.drawRoundedRect(rect.translated(0, d).adjusted(-d * 0.35, 0, d * 0.35, d * 0.25), r, r)

    def platz(self, p, rect, art):
        """Leerer Platz. art: nachzieh, nachzieh_aus, ziel, reihe, leer."""
        w = rect.width()
        p.setPen(QPen(self.c("platz_rand"), max(1.0, w * 0.02)))
        p.setBrush(self.c("platz"))
        p.drawRoundedRect(rect, w * 0.08, w * 0.08)
        mitte = rect.center()
        stift = QPen(self.c("platz_symbol"), max(1.5, w * 0.05))
        stift.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(stift)
        p.setBrush(Qt.BrushStyle.NoBrush)
        if art == "nachzieh":
            # Kreispfeil: die Ablage wird wieder umgedreht
            r = w * 0.22
            p.drawArc(QRectF(mitte.x() - r, mitte.y() - r, 2 * r, 2 * r), 70 * 16, 280 * 16)
            winkel = math.radians(350)
            punkt = mitte + QPointF(math.cos(winkel) * r, -math.sin(winkel) * r)
            tangente = QPointF(-math.sin(winkel), -math.cos(winkel))
            normale = QPointF(math.cos(winkel), -math.sin(winkel))
            s = w * 0.11
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self.c("platz_symbol"))
            p.drawPolygon(QPolygonF([punkt + tangente * s, punkt + normale * s * 0.7,
                                     punkt - normale * s * 0.7]))
        elif art == "nachzieh_aus":
            d = w * 0.15
            p.drawLine(mitte + QPointF(-d, -d), mitte + QPointF(d, d))
            p.drawLine(mitte + QPointF(-d, d), mitte + QPointF(d, -d))
        elif art == "ziel":
            p.drawPolygon(_sechseck(mitte, w * 0.3))
            p.setFont(self.schrift(w * 0.3, True))
            p.setPen(self.c("platz_symbol"))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, "A")
        elif art == "reihe":
            p.setFont(self.schrift(w * 0.4, True))
            p.setPen(self.c("platz_symbol"))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, "K")

    def vorderseite(self, p, rect, karte):
        w, h = rect.width(), rect.height()
        verlauf = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        verlauf.setColorAt(0, self.c("karte"))
        verlauf.setColorAt(1, self.c("karte_unten"))
        p.setPen(QPen(self.c("karte_rand"), max(1.0, w * 0.015)))
        p.setBrush(verlauf)
        p.drawRoundedRect(rect, w * 0.08, w * 0.08)
        farbe = self.c("rot" if karte.rot else "schwarz")

        # Ecke oben: Rang links, kleines Symbol rechts – bleibt im Fächer sichtbar
        rand = w * 0.08
        zeile = QRectF(rect.left() + rand, rect.top() + h * 0.02, w - 2 * rand, h * 0.2)
        for drehen in (False, True):
            p.save()
            if drehen:
                p.translate(rect.center())
                p.rotate(180)
                p.translate(-rect.center())
            p.setFont(self.schrift(h * 0.17, True))
            p.setPen(farbe)
            p.drawText(zeile, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       karte.zeichen)
            self.symbol(p, karte.farbe, QPointF(rect.right() - rand - w * 0.1, zeile.center().y()),
                        w * 0.2, farbe)
            p.restore()

        mitte = QPointF(rect.center().x(), rect.center().y() + h * 0.02)
        if karte.rang > 10:
            # Bube, Dame, König: Buchstabe in einer Sechskantmutter
            radius = w * 0.3
            p.setPen(QPen(farbe, max(1.5, w * 0.035)))
            p.setBrush(self.c("rot_hell" if karte.rot else "schwarz_hell"))
            p.drawPolygon(_sechseck(mitte, radius))
            p.setPen(QPen(farbe, max(1.0, w * 0.012)))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(mitte, radius * 0.84, radius * 0.84)
            p.setFont(self.schrift(radius * 0.95, True))
            p.setPen(farbe)
            p.drawText(QRectF(mitte.x() - radius, mitte.y() - radius, 2 * radius, 2 * radius),
                       Qt.AlignmentFlag.AlignCenter, karte.zeichen)
            self.symbol(p, karte.farbe, mitte - QPointF(0, radius * 1.3), w * 0.14, farbe)
            self.symbol(p, karte.farbe, mitte + QPointF(0, radius * 1.3), w * 0.14, farbe)
        elif karte.rang == 1:
            self.symbol(p, karte.farbe, mitte, w * 0.55, farbe)
        else:
            self.symbol(p, karte.farbe, mitte, w * 0.42, farbe)

    def rueckseite(self, p, rect):
        w = rect.width()
        p.setPen(QPen(self.c("karte_rand"), max(1.0, w * 0.015)))
        p.setBrush(self.c("rueckseite"))
        p.drawRoundedRect(rect, w * 0.08, w * 0.08)
        innen = rect.adjusted(w * 0.08, w * 0.08, -w * 0.08, -w * 0.08)
        p.save()
        p.setClipRect(innen)
        p.setPen(QPen(self.c("rueckseite_muster"), max(1.0, w * 0.02)))
        schritt = max(4.0, w * 0.12)
        d = -innen.height()
        while d < innen.width():
            p.drawLine(QPointF(innen.left() + d, innen.bottom()),
                       QPointF(innen.left() + d + innen.height(), innen.top()))
            d += schritt
        p.restore()
        p.setPen(QPen(self.c("rueckseite_rand"), max(1.0, w * 0.02)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(innen, w * 0.04, w * 0.04)
        # Schrauben-B in einer Mutter
        mitte = rect.center()
        radius = w * 0.24
        p.setPen(QPen(self.c("rueckseite_b"), max(1.5, w * 0.03)))
        p.setBrush(self.c("rueckseite"))
        p.drawPolygon(_sechseck(mitte, radius))
        p.setFont(self.schrift(radius * 1.05, True))
        p.setPen(self.c("rueckseite_b"))
        p.drawText(QRectF(mitte.x() - radius, mitte.y() - radius, 2 * radius, 2 * radius),
                   Qt.AlignmentFlag.AlignCenter, "B")

    def markierung(self, p, rect, farbe, breite, leuchten=False):
        r = rect.width() * 0.09
        p.setBrush(Qt.BrushStyle.NoBrush)
        if leuchten:
            p.setBrush(self.c(farbe, 40))
            p.setPen(QPen(self.c(farbe, 70), breite * 3))
            p.drawRoundedRect(rect, r, r)
            p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(self.c(farbe), breite))
        p.drawRoundedRect(rect, r, r)

    def abzeichen(self, p, mitte, text, hoehe):
        """Kleine Pille mit Zahl, z. B. Karten im Nachziehstapel."""
        schrift = self.schrift(hoehe * 0.7, True)
        breite = max(hoehe * 1.4, QFontMetricsF(schrift).horizontalAdvance(text) + hoehe * 0.8)
        rect = QRectF(mitte.x() - breite / 2, mitte.y() - hoehe / 2, breite, hoehe)
        p.setPen(QPen(self.c("rueckseite_rand"), max(1.0, hoehe * 0.08)))
        p.setBrush(self.c("abzeichen", 220))
        p.drawRoundedRect(rect, hoehe / 2, hoehe / 2)
        p.setFont(schrift)
        p.setPen(self.c("text"))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def konfetti(self, p, mitte, groesse, winkel, farbe):
        """Eine fallende Mutter."""
        p.save()
        p.translate(mitte)
        p.rotate(winkel)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.c(farbe))
        pfad = QPainterPath()
        pfad.setFillRule(Qt.FillRule.OddEvenFill)
        pfad.addPolygon(_sechseck(QPointF(0, 0), groesse))
        pfad.closeSubpath()
        pfad.addEllipse(QPointF(0, 0), groesse * 0.42, groesse * 0.42)
        p.drawPath(pfad)
        p.restore()


SKINS = {"biblix": BiblixSkin}


class _Klaenge:
    """Spielt die .wav-Dateien ab, wenn Ton an ist.

    Qt-Multimedia wird benutzt, falls vorhanden; sonst das Abspielprogramm
    des Systems (pw-play, paplay oder aplay)."""

    NAMEN = ("karte", "ablegen", "fehler", "gewonnen")

    def __init__(self, an):
        self.an = an
        self.effekte = {}
        self.programm = None
        if not an:
            return
        if QSoundEffect is not None:
            for name in self.NAMEN:
                datei = ORDNER / f"{name}.wav"
                if datei.exists():
                    effekt = QSoundEffect()
                    effekt.setSource(QUrl.fromLocalFile(str(datei)))
                    effekt.setVolume(0.6)
                    self.effekte[name] = effekt
        else:
            for kandidat in ("pw-play", "paplay", "aplay"):
                if shutil.which(kandidat):
                    self.programm = kandidat
                    break

    def spielen(self, name):
        if not self.an:
            return
        if name in self.effekte:
            self.effekte[name].play()
            return
        datei = ORDNER / f"{name}.wav"
        if self.programm and datei.exists():
            argumente = [str(datei)]
            if self.programm == "aplay":
                argumente.insert(0, "-q")
            QProcess.startDetached(self.programm, argumente)


class Spiel(QWidget):
    fertig = pyqtSignal(dict)

    def __init__(self, umgebung: dict, parent=None):
        super().__init__(parent)
        self.umgebung = umgebung
        speicher = umgebung.get("speicher")
        self.speicher = Path(speicher) if speicher else None
        self.klaenge = _Klaenge(bool(umgebung.get("ton", True)))
        self.bestzeiten = self._json_laden("bestzeiten.json")
        einstellungen = self._json_laden("einstellungen.json")
        skin = umgebung.get("skin") or einstellungen.get("skin")
        self.skin = SKINS.get(skin, BiblixSkin)()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setMinimumSize(360, 300)

        self._uhr = QTimer(self)
        self._uhr.setInterval(500)
        self._uhr.timeout.connect(self.update)
        self._anim_takt = QTimer(self)
        self._anim_takt.setInterval(16)
        self._anim_takt.timeout.connect(self._animieren)
        self._auto_takt = QTimer(self)
        self._auto_takt.setInterval(AUTO_TAKT_MS)
        self._auto_takt.timeout.connect(self._auto_schritt)

        self._tisch_cache = None
        self._anim_zeit = time.monotonic()
        self._nummer = 0
        self.starten(umgebung.get("stufe") or next(iter(STUFEN)))

    # ------------------------------------------------------------------
    # Schnittstelle für die Arcade

    def starten(self, stufe: str):
        if stufe not in STUFEN:
            stufe = next(iter(STUFEN))
        self.stufe = stufe
        self.ziehen, self.max_durchgaenge, self.faktor = STUFEN[stufe]

        deck = [Karte(f, r) for f in range(4) for r in range(1, 14)]
        random.shuffle(deck)
        self.stapel = {s: [] for s in (NACHZIEH, ABLAGE, *ZIELE, *REIHEN)}
        for i, reihe in enumerate(REIHEN):
            for j in range(i + 1):
                karte = deck.pop()
                karte.offen = j == i
                self.stapel[reihe].append(karte)
        self.stapel[NACHZIEH] = deck

        self._nummer += 1
        self.durchgang = 1
        self.punkte = 0
        self.zuege = 0
        self.verlauf = []
        self.zustand = "bereit"     # bereit, laeuft, gewonnen, verloren
        self.pausiert = False
        self.gemeldet = False
        self.automatik = False
        self.startzeit = None
        self.endzeit = None
        self.pausendauer = 0.0
        self.pausenbeginn = None
        self.titel = ""
        self.spruch = ""
        self.gehalten = None        # (stapel, index) per Tastatur aufgenommen
        self.ziehvorgang = None     # Maus-Ziehen: dict
        self.flug = {}              # karte -> (startpunkt, startzeit)
        self.partikel = []          # Konfetti nach einem Sieg
        self.zeiger = [0, 0, 0]     # zeile (0 oben, 1 Reihen), spalte, tiefe
        self.tastatur = False

        self._uhr.stop()
        self._anim_takt.stop()
        self._auto_takt.stop()
        self.setFocus()
        self.update()

    def pausieren(self):
        if self.pausiert:
            return
        self.pausiert = True
        self.pausenbeginn = time.monotonic()
        self.ziehvorgang = None
        self._uhr.stop()
        self.update()

    def fortsetzen(self):
        if not self.pausiert:
            return
        if self.zustand == "laeuft":
            self.pausendauer += time.monotonic() - self.pausenbeginn
            self._uhr.start()
        self.pausiert = False
        self.pausenbeginn = None
        self.setFocus()
        self.update()

    # ------------------------------------------------------------------
    # Regeln

    def zeit(self):
        if self.startzeit is None:
            return 0.0
        if self.endzeit is not None:
            ende = self.endzeit
        elif self.pausiert:
            ende = self.pausenbeginn
        else:
            ende = time.monotonic()
        return max(0.0, ende - self.startzeit - self.pausendauer)

    def _spielbar(self):
        return (not self.pausiert and not self.automatik
                and self.zustand in ("bereit", "laeuft"))

    def _passt_ziel(self, karte, ziel):
        stapel = self.stapel[ziel]
        if not stapel:
            return karte.rang == 1
        oben = stapel[-1]
        return oben.farbe == karte.farbe and karte.rang == oben.rang + 1

    def _passt_reihe(self, karte, reihe):
        stapel = self.stapel[reihe]
        if not stapel:
            return karte.rang == 13
        oben = stapel[-1]
        return oben.offen and oben.rot != karte.rot and karte.rang == oben.rang - 1

    def _beweglich(self, quelle, index):
        stapel = self.stapel.get(quelle)
        if not stapel or index is None or not 0 <= index < len(stapel):
            return False
        if quelle[0] == "reihe":
            return stapel[index].offen
        if quelle == NACHZIEH:
            return False
        return index == len(stapel) - 1

    def _darf(self, quelle, index, ziel):
        if ziel is None or ziel == quelle or not self._beweglich(quelle, index):
            return False
        karten = self.stapel[quelle][index:]
        if ziel[0] == "ziel":
            return len(karten) == 1 and self._passt_ziel(karten[0], ziel)
        if ziel[0] == "reihe":
            return self._passt_reihe(karten[0], ziel)
        return False

    def _sinnvolle_zuege(self):
        """Gibt es noch einen Zug, der weiterhilft? Lieber einmal zu oft „ja“."""
        nachzieh, ablage = self.stapel[NACHZIEH], self.stapel[ABLAGE]
        darf_umdrehen = self.max_durchgaenge is None or self.durchgang < self.max_durchgaenge
        if nachzieh or (ablage and darf_umdrehen):
            erreichbar = nachzieh + ablage
        else:
            erreichbar = ablage[-1:]
        for karte in erreichbar:
            if any(self._passt_ziel(karte, z) for z in ZIELE):
                return True
            if any(self._passt_reihe(karte, r) for r in REIHEN):
                return True
        for reihe in REIHEN:
            stapel = self.stapel[reihe]
            for i, karte in enumerate(stapel):
                if not karte.offen:
                    continue
                if i == len(stapel) - 1 and any(self._passt_ziel(karte, z) for z in ZIELE):
                    return True
                if not any(self._passt_reihe(karte, r) for r in REIHEN if r != reihe):
                    continue
                if i == 0:
                    if karte.rang != 13:
                        return True     # Reihe wird frei
                elif not stapel[i - 1].offen:
                    return True         # deckt eine Karte auf
                elif any(self._passt_ziel(stapel[i - 1], z) for z in ZIELE):
                    return True         # macht eine Karte für den Zielstapel frei
        return False

    # ------------------------------------------------------------------
    # Spielzüge

    def _los(self):
        if self.zustand == "bereit":
            self.zustand = "laeuft"
            self.startzeit = time.monotonic()
            self._uhr.start()

    def _merken(self):
        stand = {s: [(k, k.offen) for k in l] for s, l in self.stapel.items()}
        self.verlauf.append((stand, self.punkte, self.durchgang, self.zuege))
        del self.verlauf[:-500]

    def rueckgaengig(self):
        if not self._spielbar() or not self.verlauf:
            self.klaenge.spielen("fehler")
            return
        alt = self._aktuelle_positionen()
        stand, self.punkte, self.durchgang, self.zuege = self.verlauf.pop()
        self.stapel = {}
        for s, liste in stand.items():
            self.stapel[s] = []
            for karte, offen in liste:
                karte.offen = offen
                self.stapel[s].append(karte)
        self.gehalten = None
        self._flug_starten(alt)
        self.klaenge.spielen("karte")
        self.update()

    def bewegen(self, quelle, index, ziel):
        if not self._spielbar() or not self._darf(quelle, index, ziel):
            return False
        self._los()
        alt = self._aktuelle_positionen()
        self._merken()
        karten = self.stapel[quelle][index:]
        del self.stapel[quelle][index:]
        self.stapel[ziel].extend(karten)
        if ziel[0] == "ziel" and quelle[0] != "ziel":
            self.punkte += 10
        elif quelle == ABLAGE:
            self.punkte += 5
        elif quelle[0] == "ziel":
            self.punkte = max(0, self.punkte - 15)
        quell_stapel = self.stapel[quelle]
        if quelle[0] == "reihe" and quell_stapel and not quell_stapel[-1].offen:
            quell_stapel[-1].offen = True
            self.punkte += 5
        self.zuege += 1
        self.gehalten = None
        self._flug_starten(alt)
        self.klaenge.spielen("ablegen")
        self._nach_zug()
        return True

    def nachziehen(self):
        if not self._spielbar():
            return
        nachzieh, ablage = self.stapel[NACHZIEH], self.stapel[ABLAGE]
        darf_umdrehen = self.max_durchgaenge is None or self.durchgang < self.max_durchgaenge
        if not nachzieh and not (ablage and darf_umdrehen):
            self.klaenge.spielen("fehler")
            return
        self._los()
        alt = self._aktuelle_positionen()
        self._merken()
        if nachzieh:
            for _ in range(min(self.ziehen, len(nachzieh))):
                karte = nachzieh.pop()
                karte.offen = True
                ablage.append(karte)
        else:
            while ablage:
                karte = ablage.pop()
                karte.offen = False
                nachzieh.append(karte)
            self.durchgang += 1
            self.punkte = max(0, self.punkte - (50 if self.ziehen == 1 else 20))
        self.zuege += 1
        self.gehalten = None
        self._flug_starten(alt)
        self.klaenge.spielen("karte")
        self._nach_zug()

    def schnellzug(self, quelle, index):
        """Karte(n) an den besten Platz: erst Zielstapel, dann eine Reihe."""
        if quelle == NACHZIEH:
            self.nachziehen()
            return True
        if not self._spielbar() or not self._beweglich(quelle, index):
            return False
        if index == len(self.stapel[quelle]) - 1 and quelle[0] != "ziel":
            for ziel in ZIELE:
                if self._darf(quelle, index, ziel):
                    return self.bewegen(quelle, index, ziel)
        kandidaten = [r for r in REIHEN if self._darf(quelle, index, r)]
        # Reihen mit Karten zuerst; einen König von ganz unten umzusetzen bringt nichts
        kandidaten.sort(key=lambda r: not self.stapel[r])
        if quelle[0] == "reihe" and index == 0:
            kandidaten = [r for r in kandidaten if self.stapel[r]]
        if kandidaten:
            return self.bewegen(quelle, index, kandidaten[0])
        return False

    def _nach_zug(self):
        if sum(len(self.stapel[z]) for z in ZIELE) == 52:
            self._ende(True)
            return
        if (not self.stapel[NACHZIEH] and not self.stapel[ABLAGE]
                and all(k.offen for r in REIHEN for k in self.stapel[r])):
            # Alles aufgedeckt: den Rest legt das Spiel selbst ab.
            self.automatik = True
            self.gehalten = None
            self._auto_takt.start()
        elif not self._sinnvolle_zuege():
            self._ende(False)
        self.update()

    def _auto_schritt(self):
        if self.pausiert:
            return
        bester = None
        for reihe in REIHEN:
            stapel = self.stapel[reihe]
            if not stapel:
                continue
            for ziel in ZIELE:
                if self._passt_ziel(stapel[-1], ziel):
                    if bester is None or stapel[-1].rang < bester[0]:
                        bester = (stapel[-1].rang, reihe, ziel)
                    break
        if bester is None:
            self._auto_takt.stop()
            self.automatik = False
            return
        alt = self._aktuelle_positionen()
        _, reihe, ziel = bester
        self.stapel[ziel].append(self.stapel[reihe].pop())
        self.punkte += 10
        self._flug_starten(alt)
        self.klaenge.spielen("ablegen")
        if sum(len(self.stapel[z]) for z in ZIELE) == 52:
            self._auto_takt.stop()
            self.automatik = False
            self._ende(True)
        self.update()

    def _ende(self, gewonnen):
        self.endzeit = time.monotonic()
        self._uhr.stop()
        self.zustand = "gewonnen" if gewonnen else "verloren"
        self.gehalten = None
        zeit = round(self.zeit(), 1)
        if gewonnen:
            bonus = 500 * self.faktor
            bonus += int(1000 * self.faktor * max(0.0, ZIELZEIT - zeit) / ZIELZEIT)
            self.punkte += bonus
            alt = self.bestzeiten.get(self.stufe)
            neu = alt is None or zeit < alt
            if neu:
                self.bestzeiten[self.stufe] = zeit
                self._json_speichern("bestzeiten.json", self.bestzeiten)
            self.titel = "Neue Bestzeit!" if neu and alt is not None else "Alle Karten sortiert!"
            self.spruch = random.choice(SPRUECHE_GEWONNEN)
            self.klaenge.spielen("gewonnen")
            self._konfetti_starten()
        else:
            self.titel = "Keine Züge mehr"
            self.spruch = random.choice(SPRUECHE_VERLOREN)
            self.klaenge.spielen("fehler")

        ergebnis = {"gewonnen": gewonnen, "punkte": self.punkte,
                    "zeit": zeit, "stufe": self.stufe}
        nummer = self._nummer
        QTimer.singleShot(MELDE_VERZOEGERUNG_MS, lambda: self._melden(nummer, ergebnis))
        self.update()

    def _melden(self, nummer, ergebnis):
        if nummer != self._nummer:
            return
        self.gemeldet = True
        self.update()
        self.fertig.emit(ergebnis)

    # ------------------------------------------------------------------
    # Speicher

    def _json_laden(self, name):
        if not self.speicher:
            return {}
        try:
            daten = json.loads((self.speicher / name).read_text(encoding="utf-8"))
            return daten if isinstance(daten, dict) else {}
        except (OSError, ValueError):
            return {}

    def _json_speichern(self, name, daten):
        if not self.speicher:
            return
        try:
            self.speicher.mkdir(parents=True, exist_ok=True)
            (self.speicher / name).write_text(json.dumps(daten, indent=2), encoding="utf-8")
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Layout und Positionen

    def _layout(self):
        b, h = float(self.width()), float(self.height())
        rand = max(8.0, min(b, h) * 0.02)
        hud_h = min(max(40.0, h * 0.09), 84.0)
        frei_b = b - 2 * rand
        frei_h = h - hud_h - 3 * rand
        luecke_anteil = 0.16
        w = min(frei_b / (7 + 6 * luecke_anteil), frei_h / (1.4 * 2 + 0.2 + 1.6))
        w = max(20.0, w)
        kh = w * 1.4
        luecke = w * luecke_anteil
        links = (b - (7 * w + 6 * luecke)) / 2
        oben_y = hud_h + 2 * rand
        return {
            "hud": QRectF(rand, rand, b - 2 * rand, hud_h),
            "w": w, "kh": kh, "luecke": luecke, "links": links,
            "oben_y": oben_y, "reihen_y": oben_y + kh + max(rand, kh * 0.15),
            "unten": h - rand,
        }

    def _platz_rect(self, lay, stapel):
        art, i = stapel
        if art == "reihe":
            spalte, y = i, lay["reihen_y"]
        else:
            spalte, y = OBEN.index(stapel), lay["oben_y"]
        x = lay["links"] + spalte * (lay["w"] + lay["luecke"])
        return QRectF(x, y, lay["w"], lay["kh"])

    def _positionen(self, lay=None):
        """Wo jede Karte liegt, wenn nichts fliegt oder gezogen wird."""
        lay = lay or self._layout()
        w, kh = lay["w"], lay["kh"]
        pos = {}
        for stapel in (NACHZIEH, *ZIELE):
            rect = self._platz_rect(lay, stapel)
            for karte in self.stapel[stapel]:
                pos[karte] = rect
        ablage = self.stapel[ABLAGE]
        rect = self._platz_rect(lay, ABLAGE)
        sichtbar = 3 if self.ziehen == 3 else 1
        for i, karte in enumerate(ablage):
            versatz = max(0, i - (len(ablage) - sichtbar)) * w * 0.26
            pos[karte] = rect.translated(versatz, 0)
        platz_unten = lay["unten"] - lay["reihen_y"] - kh
        for reihe in REIHEN:
            stapel = self.stapel[reihe]
            rect = self._platz_rect(lay, reihe)
            abstaende = [kh * (0.26 if k.offen else 0.1) for k in stapel[:-1]]
            gesamt = sum(abstaende)
            stauchung = min(1.0, platz_unten / gesamt) if gesamt > 0 else 1.0
            y = 0.0
            for karte, abstand in zip(stapel, abstaende + [0.0]):
                pos[karte] = rect.translated(0, y)
                y += abstand * stauchung
        return pos

    def _ziehversatz(self):
        z = self.ziehvorgang
        if z and z["aktiv"]:
            return z["pos"] - z["start"]
        return None

    def _gezogene_karten(self):
        z = self.ziehvorgang
        if z and z["aktiv"]:
            return self.stapel[z["quelle"]][z["index"]:]
        return []

    def _aktuelle_positionen(self, lay=None):
        """Wie _positionen, aber mit fliegenden und gezogenen Karten."""
        pos = self._positionen(lay)
        jetzt = time.monotonic()
        for karte, (start, beginn) in self.flug.items():
            if karte in pos:
                t = min(1.0, (jetzt - beginn) / FLUG_DAUER)
                t = 1 - (1 - t) ** 3
                ziel = pos[karte].topLeft()
                pos[karte] = QRectF(start + (ziel - start) * t, pos[karte].size())
        versatz = self._ziehversatz()
        if versatz is not None:
            for karte in self._gezogene_karten():
                pos[karte] = pos[karte].translated(versatz)
        return pos

    def _flug_starten(self, alt):
        neu = self._positionen()
        jetzt = time.monotonic()
        for karte, rect in neu.items():
            vorher = alt.get(karte)
            if vorher is not None and (vorher.topLeft() - rect.topLeft()).manhattanLength() > 1:
                self.flug[karte] = (vorher.topLeft(), jetzt)
        if self.flug:
            self._anim_takt.start()

    def _treffer(self, punkt):
        """Welcher Stapel und welche Karte liegen unter dem Punkt?"""
        lay = self._layout()
        pos = self._positionen(lay)
        for reihe in REIHEN:
            stapel = self.stapel[reihe]
            for i in range(len(stapel) - 1, -1, -1):
                if pos[stapel[i]].contains(punkt):
                    return reihe, i
            if not stapel and self._platz_rect(lay, reihe).contains(punkt):
                return reihe, None
        for stapel_name in (*ZIELE, ABLAGE):
            stapel = self.stapel[stapel_name]
            if stapel and pos[stapel[-1]].contains(punkt):
                return stapel_name, len(stapel) - 1
            if self._platz_rect(lay, stapel_name).contains(punkt):
                return stapel_name, (len(stapel) - 1 if stapel else None)
        if self._platz_rect(lay, NACHZIEH).contains(punkt):
            return NACHZIEH, None
        return None

    def _ablageziel(self, rect):
        """Der Stapel, über dem die gezogenen Karten am meisten liegen."""
        lay = self._layout()
        pos = self._positionen(lay)
        bester, beste_flaeche = None, 0.0
        for ziel in (*ZIELE, *REIHEN):
            stapel = self.stapel[ziel]
            feld = pos[stapel[-1]] if stapel else self._platz_rect(lay, ziel)
            schnitt = feld.intersected(rect)
            flaeche = schnitt.width() * schnitt.height()
            if flaeche > beste_flaeche:
                bester, beste_flaeche = ziel, flaeche
        return bester

    # ------------------------------------------------------------------
    # Tastatur

    def _zeiger_stapel(self):
        zeile, spalte, tiefe = self.zeiger
        if zeile == 0:
            stapel = OBEN[spalte]
            liste = self.stapel[stapel]
            if stapel == NACHZIEH:
                return stapel, None
            return stapel, (len(liste) - 1 if liste else None)
        stapel = REIHEN[spalte]
        liste = self.stapel[stapel]
        return stapel, (min(tiefe, len(liste) - 1) if liste else None)

    def _erste_offene(self, reihe):
        stapel = self.stapel[reihe]
        for i, karte in enumerate(stapel):
            if karte.offen:
                return i
        return max(0, len(stapel) - 1)

    def _zeiger_korrigieren(self):
        zeile, spalte, tiefe = self.zeiger
        if zeile == 0 and spalte == 2:
            spalte = 1
        if zeile == 1:
            reihe = REIHEN[spalte]
            ende = max(0, len(self.stapel[reihe]) - 1)
            tiefe = min(max(tiefe, self._erste_offene(reihe)), ende)
        self.zeiger = [zeile, spalte, tiefe]

    def keyPressEvent(self, e):
        taste = e.key()
        if self.pausiert:
            e.ignore()
            return
        if taste in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.zustand in ("gewonnen", "verloren"):
            if self.gemeldet:
                self.starten(self.stufe)
            return
        zeile, spalte, tiefe = self.zeiger
        if taste == Qt.Key.Key_Left:
            spalte = max(0, spalte - (2 if zeile == 0 and spalte == 3 else 1))
            tiefe = 99
        elif taste == Qt.Key.Key_Right:
            spalte = min(6, spalte + (2 if zeile == 0 and spalte == 1 else 1))
            tiefe = 99
        elif taste == Qt.Key.Key_Up:
            if zeile == 1 and tiefe > self._erste_offene(REIHEN[spalte]):
                tiefe -= 1
            else:
                zeile = 0
        elif taste == Qt.Key.Key_Down:
            if zeile == 0:
                zeile, tiefe = 1, 99
            elif tiefe < len(self.stapel[REIHEN[spalte]]) - 1:
                tiefe += 1
        elif taste in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._enter()
        elif taste == Qt.Key.Key_Space:
            self._leertaste()
        elif taste == Qt.Key.Key_Backspace:
            if self.gehalten:
                self.gehalten = None
            else:
                self.rueckgaengig()
        else:
            # Escape und alles andere gehört der Arcade.
            super().keyPressEvent(e)
            return
        if taste in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
            self.zeiger = [zeile, spalte, tiefe]
        self.tastatur = True
        self._zeiger_korrigieren()
        self.update()

    def _enter(self):
        if not self._spielbar():
            return
        stapel, index = self._zeiger_stapel()
        if self.gehalten:
            quelle, q_index = self.gehalten
            if stapel == quelle:
                self.gehalten = None
            elif not self.bewegen(quelle, q_index, stapel):
                self.klaenge.spielen("fehler")
            return
        if stapel == NACHZIEH:
            self.nachziehen()
        elif self._beweglich(stapel, index):
            self.gehalten = (stapel, index)
            self.klaenge.spielen("karte")
        else:
            self.klaenge.spielen("fehler")

    def _leertaste(self):
        if not self._spielbar():
            return
        if self.gehalten:
            quelle, index = self.gehalten
            self.gehalten = None
        else:
            quelle, index = self._zeiger_stapel()
        if not self.schnellzug(quelle, index):
            self.klaenge.spielen("fehler")

    # ------------------------------------------------------------------
    # Maus

    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton or not self._spielbar():
            return
        self.tastatur = False
        treffer = self._treffer(e.position())
        if not treffer:
            return
        stapel, index = treffer
        if stapel == NACHZIEH:
            self.nachziehen()
        elif self._beweglich(stapel, index):
            self.ziehvorgang = {"quelle": stapel, "index": index, "start": e.position(),
                                "pos": e.position(), "aktiv": False}

    def mouseDoubleClickEvent(self, e):
        # Schnelles Klicken auf den Stapel soll jedes Mal nachziehen.
        if e.button() == Qt.MouseButton.LeftButton and self._spielbar():
            treffer = self._treffer(e.position())
            if treffer and treffer[0] == NACHZIEH:
                self.nachziehen()

    def mouseMoveEvent(self, e):
        z = self.ziehvorgang
        if z:
            z["pos"] = e.position()
            if not z["aktiv"] and (z["pos"] - z["start"]).manhattanLength() > 6:
                z["aktiv"] = True
                self.gehalten = None
            self.update()
        elif self.tastatur:
            self.tastatur = False
            self.update()

    def mouseReleaseEvent(self, e):
        z = self.ziehvorgang
        if not z or e.button() != Qt.MouseButton.LeftButton:
            return
        if z["aktiv"]:
            karten = self._gezogene_karten()
            pos = self._aktuelle_positionen()
            rect = pos[karten[0]] if karten else QRectF()
            ziel = self._ablageziel(rect)
            if not self.bewegen(z["quelle"], z["index"], ziel):
                # zurückfliegen lassen
                alt = pos
                self.ziehvorgang = None
                self._flug_starten(alt)
        elif not self.schnellzug(z["quelle"], z["index"]):
            self.klaenge.spielen("fehler")
        self.ziehvorgang = None
        self.update()

    # ------------------------------------------------------------------
    # Zeichnen

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        lay = self._layout()
        self._tisch_zeichnen(p, lay)
        self._hud_zeichnen(p, lay)

        darf_umdrehen = self.max_durchgaenge is None or self.durchgang < self.max_durchgaenge
        self.skin.platz(p, self._platz_rect(lay, NACHZIEH),
                        "nachzieh" if darf_umdrehen else "nachzieh_aus")
        self.skin.platz(p, self._platz_rect(lay, ABLAGE), "leer")
        for ziel in ZIELE:
            self.skin.platz(p, self._platz_rect(lay, ziel), "ziel")
        for reihe in REIHEN:
            self.skin.platz(p, self._platz_rect(lay, reihe), "reihe")

        pos = self._aktuelle_positionen(lay)
        gezogen = self._gezogene_karten()
        gehalten = []
        if self.gehalten:
            quelle, index = self.gehalten
            gehalten = self.stapel[quelle][index:]
        oben_auf = set(self.flug) | set(gezogen) | set(gehalten)

        self._nachziehstapel_zeichnen(p, lay, oben_auf)
        # Von gestapelten Karten reicht es, die obersten zu zeichnen.
        reihenfolge = (self.stapel[ABLAGE][-4:]
                       + [k for z in ZIELE for k in self.stapel[z][-2:]]
                       + [k for r in REIHEN for k in self.stapel[r]])
        for karte in reihenfolge:
            if karte not in oben_auf:
                self._karte_zeichnen(p, pos[karte], karte)

        breite = max(2.0, lay["w"] * 0.04)
        self._passende_plaetze_zeichnen(p, lay, pos, breite)

        for karte in self.stapel[NACHZIEH][-2:] + reihenfolge:
            if karte in self.flug and karte not in gezogen and karte not in gehalten:
                self._karte_zeichnen(p, pos[karte], karte, hoehe=2.0)
        anheben = QPointF(0, -lay["kh"] * 0.035)
        for karte in gehalten:
            self._karte_zeichnen(p, pos[karte].translated(anheben), karte, hoehe=3.0)
        for karte in gezogen:
            self._karte_zeichnen(p, pos[karte], karte, hoehe=4.0)

        if gehalten:
            rect = self._umriss({k: pos[k].translated(anheben) for k in gehalten}, gehalten, breite)
            self.skin.markierung(p, rect, "gehalten", breite)
        if self.tastatur and self._spielbar() and not gehalten:
            self.skin.markierung(p, self._zeiger_rect(lay, pos, breite), "akzent", breite)

        if self.zustand in ("gewonnen", "verloren"):
            p.fillRect(self.rect(), self.skin.c("abdunkeln", 140))
        if self.partikel:
            self._konfetti_zeichnen(p, lay)
        if self.zustand in ("gewonnen", "verloren"):
            self._ergebnis_zeichnen(p)
        if self.pausiert:
            self._pause_zeichnen(p)
        p.end()

    def _tisch_zeichnen(self, p, lay):
        """Der Tisch ändert sich nur mit der Fenstergröße, also einmal malen und merken."""
        dpr = self.devicePixelRatioF()
        schluessel = (self.width(), self.height(), dpr, id(self.skin))
        if self._tisch_cache is None or self._tisch_cache[0] != schluessel:
            bild = QPixmap(max(1, int(self.width() * dpr)), max(1, int(self.height() * dpr)))
            bild.setDevicePixelRatio(dpr)
            maler = QPainter(bild)
            maler.setRenderHint(QPainter.RenderHint.Antialiasing)
            zeichen = QRectF(lay["links"], lay["reihen_y"],
                             7 * lay["w"] + 6 * lay["luecke"], lay["unten"] - lay["reihen_y"])
            self.skin.tisch(maler, QRectF(0, 0, self.width(), self.height()),
                            lay["w"] * 0.5, zeichen)
            maler.end()
            self._tisch_cache = (schluessel, bild)
        p.drawPixmap(0, 0, self._tisch_cache[1])

    def _nachziehstapel_zeichnen(self, p, lay, oben_auf):
        stapel = [k for k in self.stapel[NACHZIEH] if k not in oben_auf]
        if not stapel:
            return
        rect = self._platz_rect(lay, NACHZIEH)
        # Kanten darunter zeigen, wie dick der Stapel noch ist
        schichten = min(3, (len(stapel) + 7) // 8)
        versatz = lay["w"] * 0.018
        self.skin.schatten(p, rect.translated(versatz * schichten, versatz * schichten))
        for i in range(schichten, 0, -1):
            self.skin.rueckseite(p, rect.translated(versatz * i, versatz * i))
        self.skin.rueckseite(p, rect)
        hoehe = max(14.0, lay["w"] * 0.2)
        self.skin.abzeichen(p, QPointF(rect.center().x(), rect.bottom() - hoehe * 0.2),
                            str(len(self.stapel[NACHZIEH])), hoehe)

    def _passende_plaetze_zeichnen(self, p, lay, pos, breite):
        """Grün umrandet: alle Plätze, auf die die gehaltene/gezogene Karte passt."""
        z = self.ziehvorgang
        if z and z["aktiv"]:
            quelle, index = z["quelle"], z["index"]
            karten = self._gezogene_karten()
            unter = self._ablageziel(pos[karten[0]]) if karten else None
        elif self.gehalten:
            quelle, index = self.gehalten
            unter = self._zeiger_stapel()[0] if self.tastatur else None
        else:
            return
        for ziel in (*ZIELE, *REIHEN):
            if not self._darf(quelle, index, ziel):
                continue
            liste = self.stapel[ziel]
            rect = pos[liste[-1]] if liste else self._platz_rect(lay, ziel)
            rect = rect.adjusted(-breite, -breite, breite, breite)
            self.skin.markierung(p, rect, "passt", breite * 0.8, leuchten=ziel == unter)

    def _zeiger_rect(self, lay, pos, breite):
        stapel, index = self._zeiger_stapel()
        liste = self.stapel[stapel]
        if index is not None and liste:
            return self._umriss(pos, liste[index:], breite * 2.2)
        return self._platz_rect(lay, stapel).adjusted(-breite * 1.1, -breite * 1.1,
                                                      breite * 1.1, breite * 1.1)

    def _umriss(self, pos, karten, abstand):
        rect = QRectF(pos[karten[0]])
        for karte in karten[1:]:
            rect = rect.united(pos[karte])
        return rect.adjusted(-abstand / 2, -abstand / 2, abstand / 2, abstand / 2)

    def _karte_zeichnen(self, p, rect, karte, hoehe=1.0):
        self.skin.schatten(p, rect, hoehe)
        if karte.offen:
            self.skin.vorderseite(p, rect, karte)
        else:
            self.skin.rueckseite(p, rect)

    # Kopfzeile ----------------------------------------------------------

    def _hud_zeichnen(self, p, lay):
        hud = lay["hud"]
        h = hud.height()
        self.skin.schatten(p, hud, 0.6)
        p.setPen(QPen(self.skin.c("hud_rand"), max(1.0, h * 0.025)))
        p.setBrush(self.skin.c("hud"))
        p.drawRoundedRect(hud, h * 0.22, h * 0.22)

        innen = hud.adjusted(h * 0.3, 0, -h * 0.3, 0)
        x = self._kennzahl(p, innen.left(), hud, "stern", str(self.punkte), "Punkte")
        if hud.width() >= 560:
            self._kennzahl(p, x + h * 0.6, hud, "karten", str(self.zuege), "Züge")
        best = self.bestzeiten.get(self.stufe)
        unter = f"Best {_uhrzeit(best)}" if isinstance(best, (int, float)) else "Zeit"
        breite = self._kennzahl(p, 0, hud, "uhr", _uhrzeit(self.zeit()), unter, messen=True)
        self._kennzahl(p, innen.right() - breite, hud, "uhr", _uhrzeit(self.zeit()), unter)
        if hud.width() >= 430:
            self._stufe_zeichnen(p, hud)

    def _kennzahl(self, p, x, hud, symbol, wert, text, messen=False):
        """Symbol, große Zahl, kleine Beschriftung. Gibt das rechte Ende zurück
        (bzw. mit messen=True nur die Breite)."""
        h = hud.height()
        gross = self.skin.schrift(h * 0.34, True)
        klein = self.skin.schrift(h * 0.19)
        groesse = h * 0.34
        abstand = h * 0.18
        breite = groesse + abstand + max(QFontMetricsF(gross).horizontalAdvance(wert),
                                         QFontMetricsF(klein).horizontalAdvance(text))
        if messen:
            return breite
        self._hud_symbol(p, symbol, QPointF(x + groesse / 2, hud.center().y()), groesse)
        tx = x + groesse + abstand
        p.setFont(gross)
        p.setPen(self.skin.c("text"))
        p.drawText(QRectF(tx, hud.top() + h * 0.12, breite, h * 0.45),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, wert)
        p.setFont(klein)
        p.setPen(self.skin.c("text_leise"))
        p.drawText(QRectF(tx, hud.top() + h * 0.55, breite, h * 0.3),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
        return x + breite

    def _hud_symbol(self, p, art, mitte, groesse):
        r = groesse / 2
        stift = QPen(self.skin.c("text_leise"), max(1.2, groesse * 0.09))
        stift.setCapStyle(Qt.PenCapStyle.RoundCap)
        stift.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        if art == "stern":
            punkte = []
            for i in range(10):
                winkel = math.radians(-90 + 36 * i)
                radius = r if i % 2 == 0 else r * 0.45
                punkte.append(mitte + QPointF(math.cos(winkel) * radius, math.sin(winkel) * radius))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self.skin.c("gehalten"))
            p.drawPolygon(QPolygonF(punkte))
        elif art == "karten":
            p.setPen(stift)
            p.setBrush(self.skin.c("hud"))
            for dx, dy in ((-0.2, -0.12), (0.12, 0.08)):
                rect = QRectF(mitte.x() + (dx - 0.32) * r, mitte.y() + (dy - 0.45) * r,
                              0.64 * r * 1.2, 0.9 * r * 1.2)
                p.drawRoundedRect(rect, r * 0.12, r * 0.12)
        else:
            p.setPen(stift)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(mitte, r * 0.9, r * 0.9)
            p.drawLine(mitte, mitte + QPointF(0, -r * 0.55))
            p.drawLine(mitte, mitte + QPointF(r * 0.4, 0))

    def _stufe_zeichnen(self, p, hud):
        """Mitte: Stufe als Abzeichen, darunter die Durchgänge."""
        h = hud.height()
        schrift = self.skin.schrift(h * 0.2, True)
        text = self.stufe
        breite = QFontMetricsF(schrift).horizontalAdvance(text) + h * 0.5
        pille = QRectF(hud.center().x() - breite / 2, hud.top() + h * 0.14, breite, h * 0.34)
        p.setPen(QPen(self.skin.c("akzent"), max(1.0, h * 0.025)))
        p.setBrush(self.skin.c("akzent", 50))
        p.drawRoundedRect(pille, pille.height() / 2, pille.height() / 2)
        p.setFont(schrift)
        p.setPen(self.skin.c("text"))
        p.drawText(pille, Qt.AlignmentFlag.AlignCenter, text)

        y = hud.top() + h * 0.72
        if self.max_durchgaenge:
            r = h * 0.055
            abstand = r * 3.2
            start = hud.center().x() - abstand * (self.max_durchgaenge - 1) / 2
            for i in range(self.max_durchgaenge):
                mitte = QPointF(start + i * abstand, y)
                p.setPen(QPen(self.skin.c("text_leise"), max(1.0, r * 0.4)))
                p.setBrush(self.skin.c("akzent") if i < self.durchgang else Qt.BrushStyle.NoBrush)
                p.drawEllipse(mitte, r, r)
        else:
            p.setFont(self.skin.schrift(h * 0.17))
            p.setPen(self.skin.c("text_leise"))
            p.drawText(QRectF(hud.left(), y - h * 0.12, hud.width(), h * 0.24),
                       Qt.AlignmentFlag.AlignCenter, f"Durchgang {self.durchgang}")

    # Ende, Pause, Konfetti ---------------------------------------------

    def _fenster(self, p, breite, hoehe, akzent=None):
        """Ein Fenster in der Mitte über dem abgedunkelten Tisch."""
        rect = QRectF((self.width() - breite) / 2, (self.height() - hoehe) / 2, breite, hoehe)
        r = min(breite, hoehe) * 0.08
        self.skin.schatten(p, rect, 3.0)
        p.setPen(QPen(self.skin.c("hud_rand"), max(1.0, hoehe * 0.008)))
        p.setBrush(self.skin.c("fenster"))
        p.drawRoundedRect(rect, r, r)
        if akzent:
            p.save()
            pfad = QPainterPath()
            pfad.addRoundedRect(rect, r, r)
            p.setClipPath(pfad)
            p.fillRect(QRectF(rect.left(), rect.top(), rect.width(), max(3.0, hoehe * 0.025)),
                       self.skin.c(akzent))
            p.restore()
        return rect

    def _ergebnis_zeichnen(self, p):
        breite = min(self.width() * 0.9, 640.0)
        hoehe = min(self.height() * 0.7, max(200.0, breite * 0.52))
        akzent = "gewonnen" if self.zustand == "gewonnen" else "verloren"
        rect = self._fenster(p, breite, hoehe, akzent)
        mitte = Qt.AlignmentFlag.AlignCenter

        p.setFont(self.skin.schrift(hoehe * 0.12, True))
        p.setPen(self.skin.c(akzent))
        p.drawText(QRectF(rect.left(), rect.top() + hoehe * 0.08, breite, hoehe * 0.18),
                   mitte, self.titel)
        p.setFont(self.skin.schrift(hoehe * 0.058))
        p.setPen(self.skin.c("text"))
        p.drawText(QRectF(rect.left() + breite * 0.06, rect.top() + hoehe * 0.27,
                          breite * 0.88, hoehe * 0.14),
                   mitte | Qt.TextFlag.TextWordWrap, self.spruch)

        werte = ((_uhrzeit(self.zeit()), "Zeit"), (str(self.punkte), "Punkte"),
                 (str(self.zuege), "Züge"))
        spalte = breite * 0.8 / 3
        for i, (wert, text) in enumerate(werte):
            x = rect.left() + breite * 0.1 + i * spalte
            p.setFont(self.skin.schrift(hoehe * 0.1, True))
            p.setPen(self.skin.c("text"))
            p.drawText(QRectF(x, rect.top() + hoehe * 0.47, spalte, hoehe * 0.14), mitte, wert)
            p.setFont(self.skin.schrift(hoehe * 0.05))
            p.setPen(self.skin.c("text_leise"))
            p.drawText(QRectF(x, rect.top() + hoehe * 0.61, spalte, hoehe * 0.08), mitte, text)

        if self.gemeldet:
            p.setFont(self.skin.schrift(hoehe * 0.055))
            p.setPen(self.skin.c("text_leise"))
            p.drawText(QRectF(rect.left(), rect.top() + hoehe * 0.78, breite, hoehe * 0.12),
                       mitte, "Enter = nochmal")

    def _pause_zeichnen(self, p):
        p.fillRect(self.rect(), self.skin.c("abdunkeln", 170))
        hoehe = min(self.height() * 0.22, 140.0)
        rect = self._fenster(p, hoehe * 2.6, hoehe, "akzent")
        p.setFont(self.skin.schrift(hoehe * 0.36, True))
        p.setPen(self.skin.c("text"))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Pause")

    def _konfetti_starten(self):
        farben = ("konfetti_1", "konfetti_2", "konfetti_3", "konfetti_4")
        self.partikel = [{
            "x": random.random(), "y": -random.random() * 1.2,
            "vx": random.uniform(-0.04, 0.04), "vy": random.uniform(0.18, 0.4),
            "winkel": random.uniform(0, 360), "drehung": random.uniform(-180, 180),
            "groesse": random.uniform(0.6, 1.2), "farbe": random.choice(farben),
        } for _ in range(70)]
        self._anim_zeit = time.monotonic()
        self._anim_takt.start()

    def _konfetti_zeichnen(self, p, lay):
        b, h = float(self.width()), float(self.height())
        einheit = lay["w"] * 0.09
        for teil in self.partikel:
            self.skin.konfetti(p, QPointF(teil["x"] * b, teil["y"] * h),
                               einheit * teil["groesse"], teil["winkel"], teil["farbe"])

    def _animieren(self):
        jetzt = time.monotonic()
        dt = min(0.05, jetzt - self._anim_zeit)
        self._anim_zeit = jetzt
        for karte in [k for k, (_, b) in self.flug.items() if jetzt - b >= FLUG_DAUER]:
            del self.flug[karte]
        if self.partikel and not self.pausiert:
            for teil in self.partikel:
                teil["x"] += teil["vx"] * dt
                teil["y"] += teil["vy"] * dt
                teil["winkel"] += teil["drehung"] * dt
            self.partikel = [t for t in self.partikel if t["y"] < 1.1]
        if not self.flug and not self.partikel:
            self._anim_takt.stop()
        self.update()


# ----------------------------------------------------------------------
# Testfenster: python3 spiel.py [Stufe]

class _Testfenster(QWidget):
    """Eigenes Fenster zum Ausprobieren.

    Escape spielt hier das Pausenmenü der Arcade nach,
    1/2/3 wechseln die Stufe."""

    def __init__(self, stufe):
        super().__init__()
        self.setWindowTitle("Bibi Solitär (Testmodus)")
        speicher = Path.home() / ".cache" / "biblix-arcade-test" / KENNUNG
        self.spiel = Spiel({"stufe": stufe, "ton": True, "speicher": speicher})
        self.spiel.fertig.connect(lambda ergebnis: print("fertig:", ergebnis, flush=True))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.spiel)
        self.resize(1100, 800)
        self.spiel.starten(stufe)

    def keyPressEvent(self, e):
        taste = e.key()
        if taste == Qt.Key.Key_Escape:
            if self.spiel.pausiert:
                self.spiel.fortsetzen()
            else:
                self.spiel.pausieren()
        elif Qt.Key.Key_1 <= taste <= Qt.Key.Key_3:
            self.spiel.starten(list(STUFEN)[taste - Qt.Key.Key_1])
        else:
            super().keyPressEvent(e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    stufe = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in STUFEN else next(iter(STUFEN))
    fenster = _Testfenster(stufe)
    fenster.show()
    sys.exit(app.exec())
