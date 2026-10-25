#!/usr/bin/env python3
"""Bibi Minesweeper – ein Spiel für die Bibi Arcade.

Unter manchen Blechplatten steckt eine lockere Schraube. Deck alle
sicheren Platten auf und sichere die lockeren Schrauben mit einer Mutter.
Die Zahl auf einer offenen Platte sagt, wie viele lockere Schrauben
rundherum (auch schräg) stecken.

Bedienung:
  Pfeiltasten  Zeiger bewegen
  Enter        Platte aufdecken (auf einer Zahl: Nachbarn aufdecken)
  Leertaste    Mutter draufschrauben / wieder abnehmen
  Backspace    letzte Mutter rückgängig
  Maus         links = aufdecken, rechts = Mutter, Mitte = Nachbarn aufdecken

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
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget

try:  # Nur da, wenn python3-pyqt6.qtmultimedia installiert ist.
    from PyQt6.QtMultimedia import QSoundEffect
except ImportError:
    QSoundEffect = None


# Alle Farben an einer Stelle. Stil: „Blaupause“ (technische Zeichnung).
FARBEN = {
    "hintergrund": "#0d3b66",      # Blaupausen-Papier
    "raster_fein": "#14446f",
    "raster_grob": "#1d5180",
    "linie": "#cfe3f7",            # Zeichenlinien, Rahmen
    "text": "#f2f7fc",
    "text_leise": "#9dbbd9",
    "akzent": "#ffd400",           # Zeiger
    "schriftfeld": "#0a3157",      # Kasten oben (wie das Schriftfeld einer Zeichnung)
    "platte": "#0f4372",           # geschlossene Platte
    "platte_zeiger": "#185a91",
    "schraffur": "#5f8db8",
    "offen": "#0b3459",
    "offen_rand": "#2b5d8a",
    "schraube": "#ffffff",
    "mittellinie": "#7fa6cc",      # strichpunktierte Mittellinien
    "mutter": "#ffd400",
    "boom": "#a8323e",
    "falsch": "#ff6b6b",
    "zahl_1": "#ffffff",
    "zahl_2": "#ffd400",
    "zahl_3": "#ff8a80",
    "zahl_4": "#7ee2a8",
    "zahl_5": "#ffb74d",
    "zahl_6": "#80deea",
    "zahl_7": "#d1b3ff",
    "zahl_8": "#9dbbd9",
    "banner": "#08263f",
    "gewonnen": "#7ee2a8",
    "verloren": "#ff8a80",
    "pause": "#08263f",
}

KENNUNG = "bibi_minesweeper"
ORDNER = Path(__file__).resolve().parent

# spalten, zeilen, schrauben, grundpunkte, zielzeit (Sekunden)
STUFEN = {
    "Lehrling": (9, 9, 10, 1000, 60),
    "Geselle": (16, 16, 40, 3000, 240),
    "Meister": (30, 16, 99, 6000, 600),
}

SPRUECHE_GEWONNEN = [
    "Leiwand! Kein Spiel in der Mechanik.",
    "Drehmoment exakt nach Handbuch.",
    "Biblix ist stolz auf dich. Ein bisschen.",
]
SPRUECHE_VERLOREN = [
    "Dein System. Dein Problem.",
    "Hätt' man halt vorher nachziehen sollen.",
    "Die Garantie deckt keinen Leichtsinn.",
]

# Wie lange das Ergebnis sichtbar bleibt, bevor die Arcade es bekommt.
MELDE_VERZOEGERUNG_MS = 1500


def _sekunden(wert):
    return f"{wert:.1f} s".replace(".", ",")


class _Klaenge:
    """Spielt die .wav-Dateien ab, wenn Ton an ist.

    Qt-Multimedia wird benutzt, falls vorhanden; sonst das Abspielprogramm
    des Systems (pw-play, paplay oder aplay)."""

    NAMEN = ("aufdecken", "markieren", "boom", "gewonnen")

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
        self.bestzeiten = self._bestzeiten_laden()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setMinimumSize(320, 260)

        self._uhr = QTimer(self)
        self._uhr.setInterval(250)
        self._uhr.timeout.connect(self.update)

        self._nummer = 0
        self.starten(umgebung.get("stufe") or next(iter(STUFEN)))

    # ------------------------------------------------------------------
    # Schnittstelle für die Arcade

    def starten(self, stufe: str):
        if stufe not in STUFEN:
            stufe = next(iter(STUFEN))
        self.stufe = stufe
        (self.spalten, self.zeilen, self.anzahl,
         self.grundpunkte, self.zielzeit) = STUFEN[stufe]

        self._nummer += 1
        self.schrauben = set()
        self.zahlen = {}
        self.offen = set()
        self.muttern = set()
        self.verlauf = []
        self.verteilt = False
        self.zustand = "bereit"     # bereit, laeuft, gewonnen, verloren
        self.pausiert = False
        self.gemeldet = False
        self.boom_feld = None
        self.zeiger = (self.spalten // 2, self.zeilen // 2)
        self.gedrueckt = None       # (feld, maustaste) während die Maus unten ist
        self.knopf_gedrueckt = False
        self.startzeit = None
        self.endzeit = None
        self.pausendauer = 0.0
        self.pausenbeginn = None
        self.punkte = 0
        self.titel = ""
        self.spruch = ""

        self._uhr.stop()
        self.setFocus()
        self.update()

    def pausieren(self):
        if self.pausiert:
            return
        self.pausiert = True
        self.pausenbeginn = time.monotonic()
        self.gedrueckt = None
        self.knopf_gedrueckt = False
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
    # Spiellogik

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

    def _nachbarn(self, x, y):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if (dx or dy) and 0 <= nx < self.spalten and 0 <= ny < self.zeilen:
                    yield nx, ny

    def _verteilen(self, x, y):
        """Schrauben erst beim ersten Aufdecken verteilen: der erste Klick ist sicher."""
        alle = [(sx, sy) for sy in range(self.zeilen) for sx in range(self.spalten)]
        sicher = {(x, y), *self._nachbarn(x, y)}
        frei = [feld for feld in alle if feld not in sicher]
        if len(frei) < self.anzahl:
            frei = [feld for feld in alle if feld != (x, y)]
        self.schrauben = set(random.sample(frei, self.anzahl))
        self.zahlen = {
            feld: sum(1 for n in self._nachbarn(*feld) if n in self.schrauben)
            for feld in alle
        }
        self.verteilt = True
        self.zustand = "laeuft"
        self.startzeit = time.monotonic()
        self._uhr.start()

    def _spielbar(self):
        return not self.pausiert and self.zustand in ("bereit", "laeuft")

    def aufdecken(self, feld):
        if not self._spielbar() or feld in self.muttern:
            return
        if feld in self.offen:
            self.nachbarn_aufdecken(feld)
            return
        if not self.verteilt:
            self._verteilen(*feld)
        if feld in self.schrauben:
            self._ende(False, feld)
            return
        self._fluten(feld)
        self.klaenge.spielen("aufdecken")
        self._gewinn_pruefen()
        self.update()

    def nachbarn_aufdecken(self, feld):
        """Liegen um eine Zahl genug Muttern, werden die übrigen Nachbarn aufgedeckt."""
        if not self._spielbar() or feld not in self.offen:
            return
        zahl = self.zahlen.get(feld, 0)
        nachbarn = list(self._nachbarn(*feld))
        if zahl == 0 or sum(1 for n in nachbarn if n in self.muttern) != zahl:
            return
        zu = [n for n in nachbarn if n not in self.offen and n not in self.muttern]
        if not zu:
            return
        for n in zu:
            if n in self.schrauben:
                self._ende(False, n)
                return
        for n in zu:
            self._fluten(n)
        self.klaenge.spielen("aufdecken")
        self._gewinn_pruefen()
        self.update()

    def _fluten(self, start):
        stapel = [start]
        while stapel:
            feld = stapel.pop()
            if feld in self.offen or feld in self.muttern:
                continue
            self.offen.add(feld)
            if self.zahlen.get(feld, 0) == 0:
                stapel.extend(n for n in self._nachbarn(*feld) if n not in self.offen)

    def markieren(self, feld):
        if not self._spielbar():
            return
        if feld in self.offen:
            # Leertaste auf einer Zahl: praktisch für den Controller.
            self.nachbarn_aufdecken(feld)
            return
        if feld in self.muttern:
            self.muttern.discard(feld)
        else:
            self.muttern.add(feld)
        self.verlauf.append(feld)
        self.klaenge.spielen("markieren")
        self.update()

    def rueckgaengig(self):
        if not self._spielbar():
            return
        while self.verlauf:
            feld = self.verlauf.pop()
            if feld in self.offen:
                continue
            if feld in self.muttern:
                self.muttern.discard(feld)
            else:
                self.muttern.add(feld)
            self.klaenge.spielen("markieren")
            self.update()
            return

    def _gewinn_pruefen(self):
        if len(self.offen) == self.spalten * self.zeilen - self.anzahl:
            self._ende(True)

    def _ende(self, gewonnen, boom_feld=None):
        self.endzeit = time.monotonic()
        self._uhr.stop()
        self.zustand = "gewonnen" if gewonnen else "verloren"
        self.boom_feld = boom_feld
        zeit = round(self.zeit(), 1)

        if gewonnen:
            self.muttern = set(self.schrauben)
            bonus = max(0.0, self.zielzeit - zeit) / self.zielzeit
            self.punkte = int(self.grundpunkte * (1 + bonus))
            alt = self.bestzeiten.get(self.stufe)
            neu = alt is None or zeit < alt
            if neu:
                self.bestzeiten[self.stufe] = zeit
                self._bestzeiten_speichern()
            self.titel = "Neue Bestzeit!" if neu and alt is not None else "Alles festgezogen!"
            self.spruch = random.choice(SPRUECHE_GEWONNEN)
            self.klaenge.spielen("gewonnen")
        else:
            self.punkte = len(self.offen) * 5
            self.titel = "Lockere Schraube erwischt!"
            self.spruch = random.choice(SPRUECHE_VERLOREN)
            self.klaenge.spielen("boom")

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

    def _bestzeiten_datei(self):
        return self.speicher / "bestzeiten.json" if self.speicher else None

    def _bestzeiten_laden(self):
        datei = self._bestzeiten_datei()
        try:
            daten = json.loads(datei.read_text(encoding="utf-8"))
            return {k: float(v) for k, v in daten.items() if k in STUFEN}
        except (AttributeError, OSError, ValueError, TypeError):
            return {}

    def _bestzeiten_speichern(self):
        datei = self._bestzeiten_datei()
        if datei is None:
            return
        try:
            datei.parent.mkdir(parents=True, exist_ok=True)
            datei.write_text(json.dumps(self.bestzeiten, indent=2), encoding="utf-8")
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Bedienung

    def keyPressEvent(self, e):
        taste = e.key()
        if self.pausiert:
            e.ignore()
            return
        schritte = {
            Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0),
            Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1),
        }
        if taste in schritte:
            dx, dy = schritte[taste]
            x, y = self.zeiger
            self.zeiger = (min(max(x + dx, 0), self.spalten - 1),
                           min(max(y + dy, 0), self.zeilen - 1))
            self.update()
        elif taste in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.zustand in ("gewonnen", "verloren"):
                if self.gemeldet:
                    self.starten(self.stufe)
            else:
                self.aufdecken(self.zeiger)
        elif taste == Qt.Key.Key_Space:
            self.markieren(self.zeiger)
        elif taste == Qt.Key.Key_Backspace:
            self.rueckgaengig()
        else:
            # Escape und alles andere gehört der Arcade.
            super().keyPressEvent(e)

    def mouseMoveEvent(self, e):
        if self.pausiert:
            return
        feld = self._feld_bei(e.position())
        if feld and feld != self.zeiger:
            self.zeiger = feld
            self.update()

    def mousePressEvent(self, e):
        if self.pausiert:
            return
        pos = e.position()
        taste = e.button()
        if self._layout()["knopf"].contains(pos) and taste == Qt.MouseButton.LeftButton:
            self.knopf_gedrueckt = True
            self.update()
            return
        feld = self._feld_bei(pos)
        if not feld:
            return
        self.zeiger = feld
        if taste == Qt.MouseButton.RightButton:
            self.markieren(feld)
        elif taste in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton):
            self.gedrueckt = (feld, taste)
            self.update()

    def mouseReleaseEvent(self, e):
        if self.pausiert:
            return
        pos = e.position()
        if self.knopf_gedrueckt:
            self.knopf_gedrueckt = False
            if self._layout()["knopf"].contains(pos):
                if self.zustand in ("bereit", "laeuft") or self.gemeldet:
                    self.starten(self.stufe)
            self.update()
            return
        if not self.gedrueckt:
            return
        feld, taste = self.gedrueckt
        self.gedrueckt = None
        if self._feld_bei(pos) == feld:
            if taste == Qt.MouseButton.LeftButton:
                self.aufdecken(feld)
            else:
                self.nachbarn_aufdecken(feld)
        self.update()

    # ------------------------------------------------------------------
    # Zeichnen (Stil „Blaupause“)

    def _layout(self):
        b, h = float(self.width()), float(self.height())
        rand = max(10.0, min(b, h) * 0.03)
        hud_h = min(max(44.0, h * 0.11), 96.0)
        # Platz für Rahmen und Passermarken rund ums Brett
        frei_b = b - 4 * rand
        frei_h = h - hud_h - 5 * rand
        zelle = max(4.0, min(frei_b / self.spalten, frei_h / self.zeilen))
        brett_b, brett_h = zelle * self.spalten, zelle * self.zeilen
        brett = QRectF((b - brett_b) / 2, hud_h + 3 * rand + (frei_h - brett_h) / 2,
                       brett_b, brett_h)
        hud = QRectF(rand, rand, b - 2 * rand, hud_h)
        k = hud_h * 0.8
        knopf = QRectF(hud.center().x() - k / 2, hud.center().y() - k / 2, k, k)
        return {"hud": hud, "brett": brett, "zelle": zelle, "knopf": knopf, "rand": rand}

    def _feld_bei(self, pos):
        lay = self._layout()
        brett, zelle = lay["brett"], lay["zelle"]
        if not brett.contains(pos):
            return None
        x = int((pos.x() - brett.left()) / zelle)
        y = int((pos.y() - brett.top()) / zelle)
        if 0 <= x < self.spalten and 0 <= y < self.zeilen:
            return x, y
        return None

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        lay = self._layout()
        self._papier_zeichnen(p, lay)
        self._hud_zeichnen(p, lay)
        self._rahmen_zeichnen(p, lay)
        self._brett_zeichnen(p, lay)
        if self.zustand in ("gewonnen", "verloren"):
            self._banner_zeichnen(p, lay)
        if self.pausiert:
            self._pause_zeichnen(p)
        p.end()

    def _schrift(self, pixel, fett=False):
        schrift = QFont("monospace")
        schrift.setStyleHint(QFont.StyleHint.TypeWriter)
        schrift.setPixelSize(max(6, int(pixel)))
        schrift.setBold(fett)
        return schrift

    def _stift(self, farbe, breite, strich=Qt.PenStyle.SolidLine):
        stift = QPen(QColor(FARBEN[farbe]), breite, strich)
        stift.setCapStyle(Qt.PenCapStyle.RoundCap)
        stift.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return stift

    def _papier_zeichnen(self, p, lay):
        """Blaues Papier mit feinem und grobem Raster, ausgerichtet am Brett."""
        p.fillRect(self.rect(), QColor(FARBEN["hintergrund"]))
        schritt = max(6.0, lay["zelle"] / 2)
        b, h = float(self.width()), float(self.height())
        start_x = lay["brett"].left() % schritt
        start_y = lay["brett"].top() % schritt
        for fein, farbe in ((True, "raster_fein"), (False, "raster_grob")):
            p.setPen(QPen(QColor(FARBEN[farbe]), 1.0))
            i = 0
            x = start_x
            while x < b:
                if (i % 4 != 0) == fein:
                    p.drawLine(QPointF(x, 0), QPointF(x, h))
                x += schritt
                i += 1
            i = 0
            y = start_y
            while y < h:
                if (i % 4 != 0) == fein:
                    p.drawLine(QPointF(0, y), QPointF(b, y))
                y += schritt
                i += 1

    def _hud_zeichnen(self, p, lay):
        """Oben: das Schriftfeld der Zeichnung."""
        hud, knopf = lay["hud"], lay["knopf"]
        dicke = max(1.0, hud.height() * 0.025)
        p.setPen(self._stift("linie", dicke))
        p.setBrush(QColor(FARBEN["schriftfeld"]))
        p.drawRect(hud)
        # Trennlinien links und rechts vom Knopf
        abstand = knopf.width() * 0.35
        p.setPen(self._stift("linie", dicke * 0.6))
        for x in (knopf.left() - abstand, knopf.right() + abstand):
            p.drawLine(QPointF(x, hud.top()), QPointF(x, hud.bottom()))

        innen = hud.adjusted(hud.height() * 0.25, hud.height() * 0.1,
                             -hud.height() * 0.25, -hud.height() * 0.1)
        links_b = knopf.left() - abstand - innen.left() - hud.height() * 0.15
        oben = QRectF(innen.left(), innen.top(), innen.width(), innen.height() * 0.62)
        unten = QRectF(innen.left(), oben.bottom(), innen.width(), innen.height() * 0.38)
        gross = self._schrift(oben.height() * 0.8, True)
        klein = self._schrift(unten.height() * 0.7)
        links = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        rechts = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        # Links: wie viele Schrauben noch nicht gesichert sind
        symbol = oben.height() * 0.8
        self._mutter_zeichnen(p, QPointF(oben.left() + symbol / 2, oben.center().y()),
                              symbol / 2)
        p.setFont(gross)
        p.setPen(QColor(FARBEN["text"]))
        p.drawText(oben.adjusted(symbol * 1.3, 0, 0, 0), links,
                   str(self.anzahl - len(self.muttern)))
        p.setFont(klein)
        p.setPen(QColor(FARBEN["text_leise"]))
        p.drawText(QRectF(unten.left(), unten.top(), links_b, unten.height()), links,
                   "SCHRAUBEN LOCKER")

        # Rechts: Zeit, Stufe und Bestzeit
        p.setFont(gross)
        p.setPen(QColor(FARBEN["text"]))
        p.drawText(oben, rechts, f"{int(self.zeit()):03d}")
        best = self.bestzeiten.get(self.stufe)
        zusatz = self.stufe.upper()
        if best is not None:
            zusatz += f" · BEST {_sekunden(best)}"
        p.setFont(klein)
        p.setPen(QColor(FARBEN["text_leise"]))
        p.drawText(unten, rechts, zusatz)

        self._knopf_zeichnen(p, knopf)

    def _knopf_zeichnen(self, p, rect):
        """Die Bibi-Mutter in der Mitte: neues Spiel. Ihr Gesicht zeigt die Lage."""
        mitte = rect.center()
        s = rect.width() / 2
        if self.knopf_gedrueckt:
            s *= 0.92
        self._mutter_zeichnen(p, mitte, s, loch=False)
        p.setPen(self._stift("mutter", max(1.5, s * 0.09)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        lx, rx, ay = mitte.x() - s * 0.28, mitte.x() + s * 0.28, mitte.y() - s * 0.12
        if self.zustand == "verloren":
            d = s * 0.1
            for ax in (lx, rx):
                p.drawLine(QPointF(ax - d, ay - d), QPointF(ax + d, ay + d))
                p.drawLine(QPointF(ax - d, ay + d), QPointF(ax + d, ay - d))
            p.drawArc(QRectF(mitte.x() - s * 0.26, mitte.y() + s * 0.18, s * 0.52, s * 0.36),
                      0, 180 * 16)
            return
        if self.zustand == "gewonnen":
            # Schutzbrille, technisch korrekt bemaßt
            for ax in (lx, rx):
                p.drawRect(QRectF(ax - s * 0.16, ay - s * 0.09, s * 0.32, s * 0.18))
            p.drawLine(QPointF(lx + s * 0.16, ay), QPointF(rx - s * 0.16, ay))
        else:
            for ax in (lx, rx):
                p.drawEllipse(QPointF(ax, ay), s * 0.06, s * 0.06)
        if self.gedrueckt and self.gedrueckt[1] == Qt.MouseButton.LeftButton:
            p.drawEllipse(QPointF(mitte.x(), mitte.y() + s * 0.28), s * 0.09, s * 0.11)
        else:
            p.drawArc(QRectF(mitte.x() - s * 0.28, mitte.y() - s * 0.04, s * 0.56, s * 0.44),
                      200 * 16, 140 * 16)

    def _rahmen_zeichnen(self, p, lay):
        """Rahmen ums Brett mit Passermarken in den Ecken und Bemaßung."""
        brett, rand, zelle = lay["brett"], lay["rand"], lay["zelle"]
        abstand = rand * 0.6
        rahmen = brett.adjusted(-abstand, -abstand, abstand, abstand)
        p.setPen(self._stift("linie", max(1.0, rand * 0.08)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(rahmen)
        lang = rand * 1.4
        p.setPen(self._stift("linie", max(1.0, rand * 0.12)))
        for ecke, sx, sy in ((rahmen.topLeft(), 1, 1), (rahmen.topRight(), -1, 1),
                             (rahmen.bottomLeft(), 1, -1), (rahmen.bottomRight(), -1, -1)):
            ausserhalb = ecke - QPointF(sx * abstand, sy * abstand)
            p.drawLine(ausserhalb, ausserhalb + QPointF(sx * lang, 0))
            p.drawLine(ausserhalb, ausserhalb + QPointF(0, sy * lang))

        # Bemaßung unter dem Brett: „16 × 16 · 40 Schrauben“, nur wenn Platz ist
        unten = rahmen.bottom() + abstand * 1.4
        hoehe = self.height() - unten
        if hoehe >= 12 and rahmen.width() > 200:
            p.setFont(self._schrift(min(hoehe * 0.55, zelle * 0.45, 22)))
            p.setPen(QColor(FARBEN["text_leise"]))
            p.drawText(QRectF(rahmen.left(), unten, rahmen.width(), hoehe),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       f"BLATT {self.stufe.upper()} · {self.spalten} × {self.zeilen}"
                       f" · {self.anzahl} SCHRAUBEN")

    def _brett_zeichnen(self, p, lay):
        brett, zelle = lay["brett"], lay["zelle"]
        luecke = max(1.0, zelle * 0.08)
        ende = self.zustand in ("gewonnen", "verloren")
        gedrueckt = self.gedrueckt[0] if self.gedrueckt else None
        druck_felder = set()
        if self.gedrueckt and self.gedrueckt[1] == Qt.MouseButton.MiddleButton:
            druck_felder = {gedrueckt, *self._nachbarn(*gedrueckt)}
        elif gedrueckt:
            druck_felder = {gedrueckt}

        zahl_schrift = self._schrift(zelle * 0.62, True)
        for y in range(self.zeilen):
            for x in range(self.spalten):
                feld = (x, y)
                rect = QRectF(brett.left() + x * zelle + luecke / 2,
                              brett.top() + y * zelle + luecke / 2,
                              zelle - luecke, zelle - luecke)
                mitte = rect.center()
                offen = feld in self.offen
                schraube_zeigen = ende and feld in self.schrauben and feld not in self.muttern

                if offen or schraube_zeigen or (
                        feld in druck_felder and feld not in self.muttern and self._spielbar()):
                    farbe = "boom" if feld == self.boom_feld else "offen"
                    self._offen_zeichnen(p, rect, zelle, farbe)
                else:
                    self._platte_zeichnen(p, rect, zelle, feld == self.zeiger and not ende)

                if offen:
                    zahl = self.zahlen.get(feld, 0)
                    if zahl:
                        p.setFont(zahl_schrift)
                        p.setPen(QColor(FARBEN[f"zahl_{zahl}"]))
                        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(zahl))
                elif schraube_zeigen:
                    self._schraube_zeichnen(p, mitte, zelle * 0.3)
                elif feld in self.muttern:
                    self._mutter_zeichnen(p, mitte, zelle * 0.34)
                    if self.zustand == "verloren" and feld not in self.schrauben:
                        p.setPen(self._stift("falsch", max(1.5, zelle * 0.08)))
                        d = zelle * 0.28
                        p.drawLine(mitte + QPointF(-d, -d), mitte + QPointF(d, d))
                        p.drawLine(mitte + QPointF(-d, d), mitte + QPointF(d, -d))

        # Zeiger: gelbe, gestrichelte Markierung wie mit dem Textmarker
        if not ende:
            x, y = self.zeiger
            rect = QRectF(brett.left() + x * zelle, brett.top() + y * zelle, zelle, zelle)
            dicke = max(2.0, zelle * 0.08)
            rect = rect.adjusted(dicke / 2, dicke / 2, -dicke / 2, -dicke / 2)
            stift = self._stift("akzent", dicke, Qt.PenStyle.DashLine)
            stift.setCapStyle(Qt.PenCapStyle.FlatCap)
            p.setPen(stift)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(rect)

    def _platte_zeichnen(self, p, rect, zelle, zeiger):
        """Geschlossene Platte: Umriss mit Schraffur, wie ein Schnitt in der Zeichnung."""
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(FARBEN["platte_zeiger" if zeiger else "platte"]))
        p.drawRect(rect)
        if zelle >= 10:
            p.save()
            p.setClipRect(rect)
            p.setPen(QPen(QColor(FARBEN["schraffur"]), max(1.0, zelle * 0.025)))
            schritt = max(4.0, zelle / 6)
            d = -rect.height()
            while d < rect.width():
                p.drawLine(QPointF(rect.left() + d, rect.bottom()),
                           QPointF(rect.left() + d + rect.height(), rect.top()))
                d += schritt
            p.restore()
        p.setPen(self._stift("linie", max(1.0, zelle * 0.035)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(rect)

    def _offen_zeichnen(self, p, rect, zelle, farbe):
        p.setPen(QPen(QColor(FARBEN["offen_rand"]), max(1.0, zelle * 0.025)))
        p.setBrush(QColor(FARBEN[farbe]))
        p.drawRect(rect)

    def _schraube_zeichnen(self, p, mitte, radius):
        """Lockere Schraube in Draufsicht: Kopf, Kreuzschlitz, Mittellinien."""
        # strichpunktierte Mittellinien, etwas über den Kopf hinaus
        p.setPen(self._stift("mittellinie", max(1.0, radius * 0.06), Qt.PenStyle.DashDotLine))
        lang = radius * 1.35
        p.drawLine(mitte - QPointF(lang, 0), mitte + QPointF(lang, 0))
        p.drawLine(mitte - QPointF(0, lang), mitte + QPointF(0, lang))
        p.setPen(self._stift("schraube", max(1.2, radius * 0.1)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(mitte, radius, radius)
        # Kreuzschlitz, leicht verdreht – sie ist ja locker
        p.setPen(self._stift("schraube", max(1.5, radius * 0.16)))
        d = radius * 0.5
        w = math.radians(20)
        dx, dy = math.cos(w) * d, math.sin(w) * d
        p.drawLine(mitte + QPointF(-dx, -dy), mitte + QPointF(dx, dy))
        p.drawLine(mitte + QPointF(dy, -dx), mitte + QPointF(-dy, dx))

    def _mutter_zeichnen(self, p, mitte, radius, loch=True):
        """Sechskantmutter in Draufsicht: Sechseck, Fase, Gewinde als Dreiviertelkreis."""
        ecken = QPolygonF([
            mitte + QPointF(math.cos(math.radians(30 + 60 * i)) * radius,
                            math.sin(math.radians(30 + 60 * i)) * radius)
            for i in range(6)
        ])
        p.setPen(self._stift("mutter", max(1.2, radius * 0.11)))
        p.setBrush(QColor(FARBEN["schriftfeld"]))
        p.drawPolygon(ecken)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(self._stift("mutter", max(1.0, radius * 0.05)))
        fase = radius * 0.86
        p.drawEllipse(mitte, fase, fase)
        if loch:
            p.setPen(self._stift("mutter", max(1.0, radius * 0.08)))
            innen = radius * 0.36
            p.drawEllipse(mitte, innen, innen)
            aussen = radius * 0.48
            p.drawArc(QRectF(mitte.x() - aussen, mitte.y() - aussen, 2 * aussen, 2 * aussen),
                      0, 270 * 16)

    def _banner_zeichnen(self, p, lay):
        flaeche = QRectF(self.rect())
        h = max(70.0, min(flaeche.height() * 0.26, 220.0))
        band = QRectF(0, flaeche.center().y() - h / 2 + lay["hud"].height() * 0.3,
                      flaeche.width(), h)
        farbe = QColor(FARBEN["banner"])
        farbe.setAlpha(235)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(farbe)
        p.drawRect(band)
        akzent = "gewonnen" if self.zustand == "gewonnen" else "verloren"
        # doppelte Linie oben und unten
        dicke = max(1.5, h * 0.015)
        p.setPen(self._stift(akzent, dicke))
        for y in (band.top() + dicke, band.top() + dicke * 3.5,
                  band.bottom() - dicke, band.bottom() - dicke * 3.5):
            p.drawLine(QPointF(band.left(), y), QPointF(band.right(), y))

        mitte = Qt.AlignmentFlag.AlignCenter
        p.setFont(self._schrift(h * 0.22, True))
        p.setPen(QColor(FARBEN[akzent]))
        p.drawText(QRectF(band.left(), band.top() + h * 0.1, band.width(), h * 0.36),
                   mitte, self.titel.upper())
        p.setFont(self._schrift(h * 0.11))
        p.setPen(QColor(FARBEN["text"]))
        p.drawText(QRectF(band.left(), band.top() + h * 0.46, band.width(), h * 0.2),
                   mitte, f"{self.spruch}   {_sekunden(self.zeit())} · {self.punkte} Punkte")
        if self.gemeldet:
            p.setFont(self._schrift(h * 0.1))
            p.setPen(QColor(FARBEN["text_leise"]))
            p.drawText(QRectF(band.left(), band.top() + h * 0.67, band.width(), h * 0.2),
                       mitte, "ENTER = NOCHMAL")

    def _pause_zeichnen(self, p):
        farbe = QColor(FARBEN["pause"])
        farbe.setAlpha(200)
        p.fillRect(self.rect(), farbe)
        h = float(self.height())
        p.setFont(self._schrift(h * 0.09, True))
        p.setPen(QColor(FARBEN["text"]))
        p.drawText(QRectF(self.rect()), Qt.AlignmentFlag.AlignCenter, "PAUSE")


# ----------------------------------------------------------------------
# Testfenster: python3 spiel.py [Stufe]

class _Testfenster(QWidget):
    """Eigenes Fenster zum Ausprobieren.

    Escape spielt hier das Pausenmenü der Arcade nach,
    1/2/3 wechseln die Stufe."""

    def __init__(self, stufe):
        super().__init__()
        self.setWindowTitle("Bibi Minesweeper (Testmodus)")
        speicher = Path.home() / ".cache" / "biblix-arcade-test" / KENNUNG
        self.spiel = Spiel({"stufe": stufe, "ton": True, "speicher": speicher})
        self.spiel.fertig.connect(lambda ergebnis: print("fertig:", ergebnis, flush=True))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.spiel)
        self.resize(900, 720)
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
