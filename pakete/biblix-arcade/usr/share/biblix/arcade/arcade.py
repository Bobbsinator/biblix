#!/usr/bin/env python3
"""Bibi Arcade - deine Spiele im Biblix-Rechenzentrum.

    RACK    Steam-Spiele als Server-Einschuebe (LED = Linux-Ampel, blinkt = laeuft)
    NETZ    die Bibliothek als Knotennetz (Groesse = Spielzeit, Naehe = zuletzt gespielt)
    LABOR   Pruefstaende fuer die eigenen Bibi-Spiele (spiele/<kennung>/spiel.json + spiel.py)
Ein Spiel oeffnen zeigt sein Datenblatt (Blaupause) mit "In Betrieb nehmen".

    bibi-arcade             starten
    bibi-arcade --vollbild  gleich im Vollbild (Sofa)
"""
import signal
import sys
import threading
import time
from pathlib import Path

from PyQt6 import sip
from PyQt6.QtCore import QEasingCurve, QObject, QPointF, QRectF, Qt, QThread, QTimer, QVariantAnimation, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QHBoxLayout, QLineEdit, QMainWindow, QMessageBox, QScrollArea, QSizePolicy,
    QStackedWidget, QVBoxLayout, QWidget,
)

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
sys.modules.setdefault("arcade", sys.modules[__name__])

import stil  # noqa: E402
import steam  # noqa: E402
from klang import Klang  # noqa: E402
from stil import R, knopf, label  # noqa: E402

VERSION = "1.0"
SYMBOL = Path("/usr/share/icons/hicolor/scalable/apps/de.biblix.Arcade.svg")
VERLAUF = stil.DATEN / "verlauf.json"
NEUSTART_WINDOWS = "biblix-neustart-windows"


# ---------------------------------------------------------------- Hintergrund-Arbeit

class Lader(QThread):
    """Steam-Dateien lesen (schnell, ohne Netz)."""
    fertig = pyqtSignal(list, dict)

    def run(self):
        liste = steam.spiele()
        verlauf = steam.verlauf_merken(liste, VERLAUF)
        self.fertig.emit(liste, verlauf)


class Netzholer(QObject):
    """Linux-Ampel und Spielarten aus dem Netz (abschaltbar).

    Laeuft als Daemon-Thread: wird die Arcade geschlossen, waehrend das Netz noch haengt,
    endet er einfach mit (ein QThread muesste man abwarten oder es gibt einen Absturz).
    """
    fertig = pyqtSignal(dict, dict, bool)

    def __init__(self, appids, online):
        super().__init__()
        self.appids, self.online = appids, online
        self.faden = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.faden.start()

    def isRunning(self):
        return self.faden.is_alive()

    def _run(self):
        try:
            ampel = steam.ampel_holen(self.appids, self.online)
            genres = steam.genres_holen(self.appids, self.online)
        except Exception:  # noqa: BLE001 - ohne Netzdaten geht es auch
            ampel, genres = {}, {}
        ok = self.online and any(a.get("tier") or a.get("ac_status") for a in ampel.values())
        self.fertig.emit(ampel, genres, ok)


# ---------------------------------------------------------------- Rack

class Einschub(QWidget):
    """Ein Spiel als 1U-Server-Einschub. Faehrt beim Auswaehlen heraus."""
    gewaehlt = pyqtSignal(object)
    starten = pyqtSignal(object)
    datenblatt = pyqtSignal(object)

    def __init__(self, haupt, spiel, nummer):
        super().__init__()
        self.haupt, self.spiel, self.nummer = haupt, spiel, nummer
        self.aus = 0.0       # 0 = eingeschoben, 1 = herausgefahren
        self.strom = 1.0     # Hochfahren: 0 = dunkel
        self.hover = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(46)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(180)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._aus)

    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(600, max(46, self.fontMetrics().height() * 2 + 12))

    def _aus(self, v):
        self.aus = v
        self.update()

    def _fahren(self, ziel):
        self.anim.stop()
        self.anim.setStartValue(self.aus)
        self.anim.setEndValue(ziel)
        self.anim.start()

    def focusInEvent(self, ev):
        super().focusInEvent(ev)
        self._fahren(1.0)
        self.haupt.klang.spielen("klick")
        self.gewaehlt.emit(self.spiel)

    def focusOutEvent(self, ev):
        super().focusOutEvent(ev)
        self._fahren(0.0)

    def enterEvent(self, _):
        self.hover = True
        self.update()

    def leaveEvent(self, _):
        self.hover = False
        self.update()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.setFocus(Qt.FocusReason.MouseFocusReason)
            if self.hasFocus():
                self.gewaehlt.emit(self.spiel)

    def mouseDoubleClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.starten.emit(self.spiel)

    def contextMenuEvent(self, _):
        self.datenblatt.emit(self.spiel)

    def keyPressEvent(self, ev):
        k = ev.key()
        if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.starten.emit(self.spiel)
        elif k in (Qt.Key.Key_Menu, Qt.Key.Key_I, Qt.Key.Key_Space, Qt.Key.Key_Right):
            self.datenblatt.emit(self.spiel)
        elif k == Qt.Key.Key_E and not ev.modifiers():
            self.haupt.einladen(self.spiel)
        elif k == Qt.Key.Key_Delete and self.spiel["id"] in self.haupt.laufend:
            self.haupt.not_aus(self.spiel)
        elif k in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Home, Qt.Key.Key_End, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown) \
                and not ev.modifiers():
            self.haupt.rack.springen(self, k)
        else:
            super().keyPressEvent(ev)

    def spalten(self, w):
        """x-Positionen: U, LEDs, Name, Band, Last, Zuletzt (auch fuer die Kopfzeile)."""
        fm = self.fontMetrics()
        u = 26
        leds = u + fm.horizontalAdvance("00") + 16
        zuletzt_b = fm.horizontalAdvance("gestern") + 18
        last_b = max(70, int(w * 0.13))
        band_b = fm.horizontalAdvance("WARTUNG") + 22
        zuletzt = w - 26 - zuletzt_b
        last = zuletzt - 14 - last_b
        band = last - 14 - band_b
        name = leds + 44
        return {"u": u, "leds": leds, "name": name, "band": band, "band_b": band_b,
                "last": last, "last_b": last_b, "zuletzt": zuletzt}

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s, a = self.spiel, self.haupt.ampel.get(self.spiel["id"], {})
        laeuft = s["id"] in self.haupt.laufend
        versatz = -10 * self.aus
        r = QRectF(14 + versatz, 2, self.width() - 28, self.height() - 4)
        aktiv = self.hasFocus() or self.hover
        hell = 0.35 + 0.65 * self.strom
        p.setOpacity(hell)
        # Rack-Ohren mit Schrauben
        for ox in (r.left() - 12, r.right() + 2):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(R["rahmen"]))
            p.drawRect(QRectF(ox, r.top() + 2, 10, r.height() - 4))
            p.setBrush(QColor(R["grund"]))
            p.drawEllipse(QPointF(ox + 5, r.center().y()), 2.2, 2.2)
        p.setBrush(QColor(R["einschub_an"] if self.hasFocus() else R["einschub"]))
        p.setPen(QPen(QColor(R["orange"] if self.hasFocus() else (R["rahmen"] if self.hover else R["rand"])),
                      1.5 if self.hasFocus() else 1))
        p.drawRoundedRect(r, 3, 3)
        # Luftschlitze ganz rechts
        p.setPen(QPen(QColor(R["rand"]), 1))
        for i in range(4):
            x = r.right() - 8 - i * 4
            p.drawLine(QPointF(x, r.top() + 8), QPointF(x, r.bottom() - 8))
        sp = self.spalten(int(r.width()))
        x0, cy = r.left(), r.center().y()
        fm = self.fontMetrics()
        p.setFont(self.font())
        p.setPen(QColor(R["dunkel"]))
        p.drawText(QRectF(x0 + 10, r.top(), sp["leds"] - 10, r.height()), Qt.AlignmentFlag.AlignVCenter, f"{self.nummer:02d}")
        # LEDs: Linux-Ampel, Aktivitaet
        farbe = stil.AMPEL_FARBE.get(a.get("ampel"), R["aus"]) if s["installiert"] else R["gelb"]
        blink_rot = a.get("ampel") == "rot" and not self.haupt.blink
        stil.led(p, QPointF(x0 + sp["leds"], cy), farbe, self.strom > 0.5 and a.get("ampel") != "grau" and not blink_rot)
        akt = laeuft and self.haupt.blink or (self.hasFocus() and not laeuft)
        stil.led(p, QPointF(x0 + sp["leds"] + 18, cy), R["orange"], akt and self.strom > 0.5)
        # Name
        f = QFont(self.font())
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.6)
        p.setFont(f)
        p.setPen(QColor("#ffffff" if self.hasFocus() else R["text"]))
        name_b = sp["band"] - sp["name"] - 12
        name = stil.kennzeichen(s["name"])
        p.drawText(QRectF(x0 + sp["name"], r.top(), name_b, r.height()), Qt.AlignmentFlag.AlignVCenter,
                   p.fontMetrics().elidedText(name, Qt.TextElideMode.ElideRight, int(name_b)))
        if laeuft:
            p.setPen(QColor(R["orange"]))
            klein = QFont(self.font())
            klein.setPointSizeF(klein.pointSizeF() * 0.75)
            p.setFont(klein)
            p.drawText(QRectF(x0 + sp["name"], cy + fm.height() * 0.35, name_b, fm.height()), Qt.AlignmentFlag.AlignLeft, "IN BETRIEB")
        p.setFont(self.font())
        # Klebeband mit Gesamtzeit
        band = QRectF(x0 + sp["band"], cy - fm.height() * 0.62, sp["band_b"], fm.height() * 1.24)
        wartung = not s["installiert"]
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(R["gelb"] if wartung else R["band"]))
        p.drawRect(band)
        p.setPen(QColor(R["band_text"]))
        p.drawText(band, Qt.AlignmentFlag.AlignCenter, "WARTUNG" if wartung else stil.stunden(s["minuten"]))
        # Last der letzten 2 Wochen
        hoechst = max([x["zwei_wochen"] for x in self.haupt.spiele] + [1])
        balken = QRectF(x0 + sp["last"], cy - 3, sp["last_b"], 6)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(R["rand"]))
        p.drawRoundedRect(balken, 2, 2)
        anteil = s["zwei_wochen"] / hoechst
        if anteil > 0:
            p.setBrush(QColor(R["orange"]))
            p.drawRoundedRect(QRectF(balken.left(), balken.top(), max(3.0, balken.width() * anteil), 6), 2, 2)
        p.setPen(QColor(R["leise"]))
        p.drawText(QRectF(x0 + sp["zuletzt"], r.top(), r.width() - sp["zuletzt"] - 14, r.height()),
                   Qt.AlignmentFlag.AlignVCenter, stil.wann(s["zuletzt"]))
        p.end()


class FreierEinschub(QWidget):
    def __init__(self, nummer):
        super().__init__()
        self.nummer = nummer
        self.setMinimumHeight(40)

    def paintEvent(self, _):
        p = QPainter(self)
        r = QRectF(14, 2, self.width() - 28, self.height() - 4)
        p.setPen(QPen(QColor(R["rahmen"]), 1, Qt.PenStyle.DashLine))
        p.setBrush(QColor("#1b1d21"))
        p.drawRoundedRect(r, 3, 3)
        p.setPen(QColor(R["dunkel"]))
        p.drawText(r.adjusted(10, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter,
                   f"{self.nummer:02d}      — frei: Spiel in Steam installieren —")
        p.end()


class RackKopf(QWidget):
    """Spaltenueberschriften, passend zu Einschub.spalten()."""

    def __init__(self, muster):
        super().__init__()
        self.muster = muster
        self.setFixedHeight(22)

    def paintEvent(self, _):
        if not self.muster:
            return
        p = QPainter(self)
        f = QFont(self.font())
        f.setPointSizeF(f.pointSizeF() * 0.82)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        p.setFont(f)
        p.setPen(QColor(R["dunkel"]))
        x0 = 14
        sp = self.muster.spalten(self.width() - 28)
        for x, t in ((10, "U"), (sp["leds"] - 4, "LED"), (sp["name"], "EINSCHUB"), (sp["band"], "BETRIEB"),
                     (sp["last"], "LAST 2 WO."), (sp["zuletzt"], "ZULETZT")):
            p.drawText(QRectF(x0 + x, 0, 200, self.height()), Qt.AlignmentFlag.AlignVCenter, t)
        p.end()


class RackRahmen(QWidget):
    """Das Rack: Rahmen mit Lochschienen links und rechts."""

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setPen(QPen(QColor(R["rahmen"]), 2))
        p.setBrush(QColor(R["rack"]))
        p.drawRoundedRect(r, 6, 6)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(R["grund"]))
        y = r.top() + 10
        while y < r.bottom() - 6:
            for x in (r.left() + 6, r.right() - 6):
                p.drawRect(QRectF(x - 2, y, 4, 4))
            y += 12
        p.end()


class Vorschau(QWidget):
    """Rechte Seite: Cover und Ampel des gewaehlten Einschubs."""

    def __init__(self, haupt):
        super().__init__()
        self.haupt = haupt
        self.spiel = None
        self.setMinimumHeight(260)

    def zeigen(self, spiel):
        self.spiel = spiel
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setPen(QPen(QColor(R["rand"]), 1))
        p.setBrush(QColor(R["flaeche"]))
        p.drawRoundedRect(r, 4, 4)
        fm = self.fontMetrics()
        p.setPen(QColor(R["dunkel"]))
        if self.spiel is None:
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, "KEIN EINSCHUB GEWÄHLT")
            p.end()
            return
        s = self.spiel
        nr = next((i for i, x in enumerate(self.haupt.sichtbar, 1) if x["id"] == s["id"]), 0)
        p.drawText(QRectF(r.left() + 10, r.top() + 6, r.width() - 20, fm.height()), Qt.AlignmentFlag.AlignLeft,
                   f"EINSCHUB {nr:02d}")
        bild_r = QRectF(r.left() + 10, r.top() + 10 + fm.height(), r.width() - 20, r.height() - 30 - fm.height() * 3)
        pm = stil.bild(s["bilder"].get("cover")) or stil.bild(s["bilder"].get("hero")) or stil.bild(s["bilder"].get("banner"))
        p.setPen(QPen(QColor(R["rahmen"]), 1))
        p.setBrush(QColor(R["einschub"]))
        p.drawRect(bild_r)
        if pm is not None:
            if s["bilder"].get("cover"):
                # Cover im Hochformat mittig
                h = bild_r.height()
                w = min(bild_r.width(), h * 2 / 3)
                stil.bild_fuellen(p, QRectF(bild_r.center().x() - w / 2, bild_r.top(), w, h), pm)
            else:
                stil.bild_fuellen(p, bild_r, pm)
                logo = stil.bild(s["bilder"].get("logo"))
                if logo is not None:
                    lw = bild_r.width() * 0.8
                    lh = lw * logo.height() / max(1, logo.width())
                    p.drawPixmap(QRectF(bild_r.center().x() - lw / 2, bild_r.center().y() - lh / 2, lw, lh),
                                 logo, QRectF(logo.rect()))
        else:
            p.setPen(QColor(R["dunkel"]))
            p.drawText(bild_r, Qt.AlignmentFlag.AlignCenter, "KEIN BILD")
        a = self.haupt.ampel.get(s["id"], {})
        y = bild_r.bottom() + 8
        if not s["installiert"]:
            farbe, text = R["gelb"], "WARTUNG: Steam lädt noch"
        else:
            farbe = stil.AMPEL_FARBE.get(a.get("ampel"), R["leise"])
            text = "Linux: " + (steam.TIER_TEXT.get(a.get("tier"), "") or steam.AMPEL_TEXT.get(a.get("ampel"), "wird geprüft …"))
            if a.get("ampel") == "rot":
                text = "nur Windows (Anti-Cheat)"
        stil.led(p, QPointF(r.left() + 16, y + fm.height() / 2), farbe, True, 4)
        p.setPen(QColor(farbe if farbe != R["aus"] else R["leise"]))
        p.drawText(QRectF(r.left() + 28, y, r.width() - 36, fm.height()), Qt.AlignmentFlag.AlignVCenter,
                   fm.elidedText(text, Qt.TextElideMode.ElideRight, int(r.width() - 36)))
        p.end()


class Protokoll(QWidget):
    """Systemprotokoll: die letzten Ereignisse, neueste unten."""

    def __init__(self):
        super().__init__()
        self.zeilen = []
        self.setMinimumHeight(150)

    def schreiben(self, text, farbe=None):
        self.zeilen.append((time.strftime("%H:%M"), text, farbe or R["protokoll"]))
        self.zeilen = self.zeilen[-40:]
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setPen(QPen(QColor(R["rand"]), 1))
        p.setBrush(QColor(R["schwarz"]))
        p.drawRoundedRect(r, 4, 4)
        f = QFont(self.font())
        f.setPointSizeF(f.pointSizeF() * 0.85)
        p.setFont(f)
        fm = p.fontMetrics()
        zh = fm.height() + 2
        p.setPen(QColor(R["dunkel"]))
        p.drawText(QRectF(r.left() + 8, r.top() + 6, r.width(), zh), Qt.AlignmentFlag.AlignLeft, "SYSTEMPROTOKOLL")
        platz = int((r.height() - 14 - zh) // zh)
        y = r.top() + 8 + zh
        for zeit, text, farbe in self.zeilen[-platz:] if platz > 0 else []:
            p.setPen(QColor(R["dunkel"]))
            p.drawText(QRectF(r.left() + 8, y, 60, zh), Qt.AlignmentFlag.AlignLeft, zeit)
            p.setPen(QColor(farbe))
            breite = r.width() - 16 - fm.horizontalAdvance("00:00 ")
            p.drawText(QRectF(r.left() + 8 + fm.horizontalAdvance("00:00 "), y, breite, zh), Qt.AlignmentFlag.AlignLeft,
                       fm.elidedText(text, Qt.TextElideMode.ElideRight, int(breite)))
            y += zh
        p.end()


class RackSeite(QWidget):
    def __init__(self, haupt):
        super().__init__()
        self.haupt = haupt
        self.einschuebe = []
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 6)
        lay.setSpacing(10)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.rahmen = RackRahmen()
        self.rl = QVBoxLayout(self.rahmen)
        self.rl.setContentsMargins(10, 8, 10, 10)
        self.rl.setSpacing(4)
        self.scroll.setWidget(self.rahmen)
        lay.addWidget(self.scroll, 1)
        rechts = QVBoxLayout()
        rechts.setSpacing(8)
        self.vorschau = Vorschau(haupt)
        rechts.addWidget(self.vorschau, 3)
        self.los = knopf("▶  IN BETRIEB NEHMEN", "los", lambda: self.vorschau.spiel and haupt.spiel_starten(self.vorschau.spiel))
        rechts.addWidget(self.los)
        self.blatt = knopf("DATENBLATT", cb=lambda: self.vorschau.spiel and haupt.datenblatt_zeigen(self.vorschau.spiel))
        rechts.addWidget(self.blatt)
        self.einladen = knopf("📨  EINLADEN", cb=lambda: self.vorschau.spiel and haupt.einladen(self.vorschau.spiel))
        self.einladen.setToolTip("Freunde zum Spielen einladen (E)")
        rechts.addWidget(self.einladen)
        self.notaus = knopf("⏻  NOT-AUS", "notaus", lambda: self.vorschau.spiel and haupt.not_aus(self.vorschau.spiel))
        self.notaus.setToolTip("Hängendes Spiel hart beenden (Entf)")
        self.notaus.hide()
        rechts.addWidget(self.notaus)
        self.protokoll = haupt.protokoll
        rechts.addWidget(self.protokoll, 2)
        breite = QWidget()
        breite.setLayout(rechts)
        breite.setFixedWidth(250)
        lay.addWidget(breite)

    def aufbauen(self, liste, hochfahren=False):
        alt_id = self.vorschau.spiel["id"] if self.vorschau.spiel else None
        while self.rl.count():
            it = self.rl.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self.einschuebe = []
        muster = Einschub(self.haupt, liste[0], 1) if liste else None
        kopf = RackKopf(muster)
        self.rl.addWidget(kopf)
        for i, s in enumerate(liste, 1):
            e = Einschub(self.haupt, s, i)
            e.gewaehlt.connect(self._gewaehlt)
            e.starten.connect(self.haupt.spiel_starten)
            e.datenblatt.connect(self.haupt.datenblatt_zeigen)
            if hochfahren:
                e.strom = 0.0
            self.rl.addWidget(e)
            self.einschuebe.append(e)
        frei = 0
        for n in range(len(liste) + 1, max(len(liste) + 2, 9)):
            self.rl.addWidget(FreierEinschub(n))
            frei += 1
        self.rl.addStretch(1)
        if muster is not None:
            kopf.muster = muster  # nur fuer die Spaltenberechnung, wird nie gezeigt
            muster.setParent(kopf)
            muster.hide()
        wahl = next((s for s in liste if s["id"] == alt_id), liste[0] if liste else None)
        self.vorschau.zeigen(wahl)
        if hochfahren and self.einschuebe:
            self._hochfahren(0)

    def _hochfahren(self, i):
        if i >= len(self.einschuebe):
            return
        e = self.einschuebe[i]
        if not sip.isdeleted(e):
            e.strom = 1.0
            e.update()
        QTimer.singleShot(90, lambda: self._hochfahren(i + 1))

    def _gewaehlt(self, spiel):
        self.vorschau.zeigen(spiel)
        self.notaus.setVisible(spiel["id"] in self.haupt.laufend)
        a = self.haupt.ampel.get(spiel["id"], {})
        if spiel["id"] in self.haupt.laufend:
            self.los.setText("●  LÄUFT GERADE")
            self.los.setObjectName("")
        elif not spiel["installiert"]:
            self.los.setText("WARTUNG – STEAM ÖFFNEN")
            self.los.setObjectName("")
        elif a.get("ampel") == "rot":
            self.los.setText("⟳  IN WINDOWS STARTEN")
            self.los.setObjectName("windows")
        else:
            self.los.setText("▶  IN BETRIEB NEHMEN")
            self.los.setObjectName("los")
        self.los.setStyleSheet("")

    def erstes_waehlen(self):
        if self.einschuebe:
            self.einschuebe[0].setFocus(Qt.FocusReason.OtherFocusReason)

    def springen(self, von, taste):
        """Pfeiltasten ohne Controller: hoch/runter, Pos1/Ende, Bild auf/ab (5 Einschuebe)."""
        if von not in self.einschuebe:
            return
        i = self.einschuebe.index(von)
        schritt = {Qt.Key.Key_Up: -1, Qt.Key.Key_Down: 1, Qt.Key.Key_PageUp: -5, Qt.Key.Key_PageDown: 5,
                   Qt.Key.Key_Home: -len(self.einschuebe), Qt.Key.Key_End: len(self.einschuebe)}[taste]
        ziel = self.einschuebe[max(0, min(len(self.einschuebe) - 1, i + schritt))]
        ziel.setFocus(Qt.FocusReason.TabFocusReason)
        self.scroll.ensureWidgetVisible(ziel, 0, 60)


# ---------------------------------------------------------------- Kopf und Fuss

class Kopf(QWidget):
    def __init__(self, haupt):
        super().__init__()
        self.haupt = haupt
        self.setObjectName("kopf")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 8, 16, 4)
        lay.setSpacing(14)
        name = label("BIBI·ARCADE")
        name.setFont(stil.schrift(15, mono=False, fett=True, abstand=2.5))
        name.setStyleSheet(f"color: {R['orange']};")
        lay.addWidget(name)
        self.rack_name = label("RACK 07", "leise")
        lay.addWidget(self.rack_name)
        self.reiter = {}
        for k, t in (("rack", "RACK"), ("netz", "NETZ"), ("labor", "LABOR")):
            b = knopf(t, "reiter", lambda _=False, x=k: haupt.zeigen(x))
            b.setCheckable(True)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            lay.addWidget(b)
            self.reiter[k] = b
        lay.addStretch(1)
        self.suche = QLineEdit()
        self.suche.setPlaceholderText("einschub suchen …")
        self.suche.setClearButtonEnabled(True)
        self.suche.setFixedWidth(220)
        self.suche.textChanged.connect(lambda _: haupt.filtern())
        lay.addWidget(self.suche)
        self.status = label("", "leise")
        lay.addWidget(self.status)
        zahnrad = knopf("⚙", cb=haupt.einstellungen_zeigen)
        zahnrad.setToolTip("Einstellungen")
        zahnrad.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        lay.addWidget(zahnrad)

    def paintEvent(self, _):
        p = QPainter(self)
        r = QRectF(self.rect()).adjusted(16, 4, -16, 0)
        p.setPen(QPen(QColor(R["rand"]), 1))
        p.setBrush(QColor(R["flaeche"]))
        p.drawRoundedRect(r, 4, 4)
        p.end()


class Fuss(QWidget):
    def __init__(self, haupt):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 4, 20, 8)
        lay.setSpacing(18)
        self.hilfe = label("")
        lay.addWidget(self.hilfe)
        self.spiel_hilfe(False)
        lay.addStretch(1)
        lay.addWidget(label("sortiert:", "leise"))
        self.sortierung = QComboBox()
        self.werte = [("zuletzt", "zuletzt"), ("spielzeit", "spielzeit"), ("name", "name"), ("groesse", "größe")]
        for w, t in self.werte:
            self.sortierung.addItem(t, w)
        self.sortierung.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        werte = [w for w, _ in self.werte]
        self.sortierung.setCurrentIndex(werte.index(haupt.einst["sortierung"]) if haupt.einst["sortierung"] in werte else 0)
        self.sortierung.currentIndexChanged.connect(lambda i: haupt.sortieren(werte[i]))
        lay.addWidget(self.sortierung)
        self.version = label(f"v{VERSION}", "dunkel")
        lay.addWidget(self.version)

    def spiel_hilfe(self, im_spiel):
        """Unten die passenden Tasten: Arcade oder laufendes Bibi-Spiel."""
        def t(taste, farbe, text):
            return f"<b style='color:{farbe}'>{taste}</b> <span style='color:{R['leise']}'>{text}</span>"
        if im_spiel:
            teile = [t("✚", R["text"], "bewegen"), t("A", R["gruen"], "aktion"), t("X", R["blau"], "zweite aktion"),
                     t("Y", R["gelb"], "rückgängig"), t("B", R["rot"], "pause")]
        else:
            teile = [t("A", R["gruen"], "starten"), t("B", R["rot"], "zurück"), t("X", R["blau"], "datenblatt"),
                     t("Y", R["gelb"], "suchen"), t("E", R["text"], "einladen"), t("LB/RB", R["text"], "rack · netz · labor"),
                     t("⧉", R["text"], "sortieren")]
        self.hilfe.setText("&nbsp;&nbsp;&nbsp;&nbsp;".join(teile))


# ---------------------------------------------------------------- Hauptfenster

class Haupt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bibi Arcade")
        icon = QIcon.fromTheme("de.biblix.Arcade")
        if icon.isNull() and SYMBOL.is_file():
            icon = QIcon(str(SYMBOL))
        self.setWindowIcon(icon)
        self.resize(1380, 860)
        self.einst = stil.einstellungen()
        self.klang = Klang(self.einst["geraeusche"])
        self.spiele, self.sichtbar, self.verlauf = [], [], {}
        self.ampel, self.genres = {}, {}
        self.laufend, self.blink = set(), False
        self.online = False
        self.lader = self.netzholer = None
        self.erstes_mal = True
        self.aktuell = "rack"
        self.vorher = "rack"
        self.protokoll = Protokoll()

        import datenblatt
        import labor
        import netz
        root = QWidget()
        root.setObjectName("grund")
        lay = QVBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.kopf = Kopf(self)
        lay.addWidget(self.kopf)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self.fuss = Fuss(self)
        lay.addWidget(self.fuss)
        self.setCentralWidget(root)
        self.rack = RackSeite(self)
        self.netz = netz.NetzSeite(self)
        self.labor = labor.LaborSeite(self)
        self.blatt = datenblatt.DatenblattSeite(self)
        for w in (self.rack, self.netz, self.labor, self.blatt):
            self.stack.addWidget(w)
        self.setStyleSheet(stil.stil())
        self.zeigen("rack")

        self.takt = QTimer(self)
        self.takt.timeout.connect(self._takt)
        self.takt.start(600)
        self.prozess_takt = QTimer(self)
        self.prozess_takt.timeout.connect(self._laufende_pruefen)
        self.prozess_takt.start(3000)
        self.uhr = QTimer(self)
        self.uhr.timeout.connect(self._status)
        self.uhr.start(20000)
        self.protokoll.schreiben("rack wird hochgefahren …")
        if self.einst["hochfahren"]:
            self.klang.spielen("hochfahren")
        self.neu_laden()

    # ---- Daten

    def neu_laden(self):
        if self.lader and self.lader.isRunning():
            return
        self.lader = Lader()
        self.lader.fertig.connect(self._geladen)
        self.lader.start()

    def _geladen(self, liste, verlauf):
        alt = {s["id"]: s["minuten"] for s in self.spiele}
        self.spiele, self.verlauf = liste, verlauf
        if self.erstes_mal:
            self.protokoll.schreiben("rack online")
            self.protokoll.schreiben(f"{len(liste)} einschübe erkannt" if liste else "keine steam-spiele gefunden",
                                     None if liste else R["gelb"])
            self._seit_gestern()
            for s in liste:
                if not s["installiert"]:
                    self.protokoll.schreiben(f"{stil.kennzeichen(s['name']).lower()}: wartung nötig", R["gelb"])
        else:
            for s in liste:
                plus = s["minuten"] - alt.get(s["id"], s["minuten"])
                if plus > 0:
                    self.protokoll.schreiben(f"{stil.kennzeichen(s['name']).lower()} +{plus} min")
        self.filtern(hochfahren=self.erstes_mal and self.einst["hochfahren"])
        if self.erstes_mal:
            QTimer.singleShot(150, self.rack.erstes_waehlen)
            self.netzholer = Netzholer([s["id"] for s in liste], self.einst["online"])
            self.netzholer.fertig.connect(self._netz_fertig)
            self.netzholer.start()
        self.erstes_mal = False
        self._status()

    def _seit_gestern(self):
        tage = sorted(self.verlauf)
        if len(tage) < 2:
            return
        heute, vorher = self.verlauf[tage[-1]], self.verlauf[tage[-2]]
        for s in self.spiele:
            plus = heute.get(s["id"], 0) - vorher.get(s["id"], heute.get(s["id"], 0))
            if plus > 0:
                self.protokoll.schreiben(f"{stil.kennzeichen(s['name']).lower()} +{plus} min seit {stil.wann(time.mktime(time.strptime(tage[-2], '%Y-%m-%d')))}")

    def _netz_fertig(self, ampel, genres, ok):
        self.ampel, self.genres, self.online = ampel, genres, ok
        zaehl = {}
        for s in self.spiele:
            a = ampel.get(s["id"], {})
            k = steam.TIER_TEXT.get(a.get("tier")) or ("unbekannt" if a.get("ampel") == "grau" else a.get("ampel", "?"))
            zaehl[k] = zaehl.get(k, 0) + 1
            if a.get("ampel") == "rot":
                self.protokoll.schreiben(f"{stil.kennzeichen(s['name']).lower()}: nur windows ({a.get('anticheat') or 'anti-cheat'})", R["rot"])
        if not self.einst["online"]:
            self.protokoll.schreiben("online-prüfung ist aus", R["leise"])
        elif ok:
            self.protokoll.schreiben("protondb: " + ", ".join(f"{n}× {k.lower()}" for k, n in sorted(zaehl.items(), key=lambda x: -x[1])))
        else:
            self.protokoll.schreiben("protondb nicht erreichbar", R["gelb"])
        self._status()
        self.alles_neu_malen()
        self.netz.aufbauen()
        if self.rack.vorschau.spiel:
            self.rack._gewaehlt(self.rack.vorschau.spiel)

    def sortierung_weiter(self):
        if self.aktuell == "netz":
            self.netz.groesse_weiter()  # im Netz schaltet die Ansicht-Taste die Knotengroesse um
            return
        box = self.fuss.sortierung
        box.setCurrentIndex((box.currentIndex() + 1) % box.count())
        self.klang.spielen("klick")
        self.protokoll.schreiben(f"sortierung: {box.currentText()}", R["leise"])

    def sortieren(self, wie):
        self.einst["sortierung"] = wie
        stil.json_schreiben(stil.KONFIG, self.einst)
        self.filtern()

    def filtern(self, hochfahren=False):
        q = self.kopf.suche.text().strip().lower()
        liste = [s for s in self.spiele if not q or q in s["name"].lower()]
        wie = self.einst["sortierung"]
        if wie == "spielzeit":
            liste.sort(key=lambda s: -s["minuten"])
        elif wie == "groesse":
            liste.sort(key=lambda s: -s["groesse"])
        elif wie == "zuletzt":
            liste.sort(key=lambda s: -s["zuletzt"])
        self.sichtbar = liste
        self.rack.aufbauen(liste, hochfahren)
        self.netz.aufbauen()

    def alles_neu_malen(self):
        for e in self.rack.einschuebe:
            e.update()
        self.rack.vorschau.update()
        self.netz.update()

    def _status(self):
        gesamt = sum(s["minuten"] for s in self.spiele)
        platz = sum(s["groesse"] for s in self.spiele)
        online = (f"<span style='color:{R['gruen']}'>●</span> online" if self.online
                  else f"<span style='color:{R['aus']}'>●</span> offline")
        self.kopf.status.setText(f"Σ {gesamt // 60} h · {stil.gb(platz)} · {online} · {time.strftime('%H:%M')}")

    def _takt(self):
        self.blink = not self.blink
        if self.laufend or any(a.get("ampel") == "rot" for a in self.ampel.values()):
            for e in self.rack.einschuebe:
                if e.spiel["id"] in self.laufend or self.ampel.get(e.spiel["id"], {}).get("ampel") == "rot":
                    e.update()

    def _laufende_pruefen(self):
        jetzt = steam.laufende(self.spiele)
        if jetzt == self.laufend:
            return
        namen = {s["id"]: stil.kennzeichen(s["name"]).lower() for s in self.spiele}
        for a in jetzt - self.laufend:
            self.protokoll.schreiben(f"{namen.get(a, a)} in betrieb", R["orange"])
        for a in self.laufend - jetzt:
            self.protokoll.schreiben(f"{namen.get(a, a)} heruntergefahren", R["leise"])
            QTimer.singleShot(6000, self.neu_laden)  # Steam schreibt die Spielzeit beim Beenden
        self.laufend = jetzt
        self.alles_neu_malen()
        if self.rack.vorschau.spiel:
            self.rack._gewaehlt(self.rack.vorschau.spiel)
        if self.aktuell == "blatt":
            self.blatt.knoepfe_neu()

    # ---- Aktionen

    def spiel_starten(self, spiel):
        a = self.ampel.get(spiel["id"], {})
        if not spiel["installiert"] or a.get("ampel") == "rot":
            self.datenblatt_zeigen(spiel)
            return
        self.klang.spielen("start")
        self.protokoll.schreiben(f"{stil.kennzeichen(spiel['name']).lower()}: start angefordert", R["orange"])
        if not stil.starten(steam.starten_befehl(spiel)):
            self.klang.spielen("fehler")
            self.protokoll.schreiben("steam ließ sich nicht starten", R["rot"])

    def not_aus(self, spiel):
        """Haengendes Spiel hart beenden: erst hoeflich (SIGTERM), nach 4 s endgueltig (SIGKILL)."""
        name = stil.kennzeichen(spiel["name"]).lower()
        frage = QMessageBox(self)
        frage.setWindowTitle("NOT-AUS")
        frage.setText(f"<b style='color:{R['rot']}'>{spiel['name']} hart beenden?</b>")
        frage.setInformativeText("Nur für hängende oder abgestürzte Spiele. Was seit dem letzten Speichern passiert ist, "
                                 "geht verloren. Steam selbst läuft weiter.")
        los = frage.addButton("⏻  NOT-AUS", QMessageBox.ButtonRole.DestructiveRole)
        los.setObjectName("notaus")
        nein = frage.addButton("Abbrechen", QMessageBox.ButtonRole.RejectRole)
        frage.setDefaultButton(nein)
        frage.setEscapeButton(nein)
        frage.setStyleSheet(stil.stil() + f"QMessageBox {{ background: {R['flaeche']}; }}")  # nach den Knoepfen: rot greift
        self.klang.spielen("relais")
        frage.exec()
        if frage.clickedButton() is not los:
            return
        pids = steam.prozesse(spiel)
        if not pids:
            self.protokoll.schreiben(f"{name}: läuft schon nicht mehr", R["leise"])
            self._laufende_pruefen()
            return
        self.klang.spielen("fehler")
        steam.signal_senden(pids, signal.SIGTERM)
        self.protokoll.schreiben(f"NOT-AUS {name}: {len(pids)} prozess{'e' if len(pids) != 1 else ''} gestoppt", R["rot"])
        QTimer.singleShot(4000, lambda: self._not_aus_nachfassen(spiel))

    def _not_aus_nachfassen(self, spiel):
        rest = steam.prozesse(spiel)
        if rest:
            steam.signal_senden(rest, signal.SIGKILL)
            self.protokoll.schreiben(f"{stil.kennzeichen(spiel['name']).lower()}: hart abgeschaltet ({len(rest)})", R["rot"])
        else:
            self.protokoll.schreiben(f"{stil.kennzeichen(spiel['name']).lower()}: sauber heruntergefahren", R["leise"])
        QTimer.singleShot(500, self._laufende_pruefen)

    def einladen(self, spiel):
        import einladen
        self.klang.spielen("relais")
        dlg = einladen.EinladenDialog(self, spiel)
        dlg.exec()

    def in_windows(self):
        self.protokoll.schreiben("neustart in windows angefordert", R["blau"])
        stil.starten([NEUSTART_WINDOWS])

    def datenblatt_zeigen(self, spiel):
        self.klang.spielen("relais")
        self.vorher = self.aktuell if self.aktuell != "blatt" else self.vorher
        self.blatt.zeigen(spiel)
        self._seite("blatt")

    def zeigen(self, key):
        self.vorher = key
        self._seite(key)
        if key == "rack":
            QTimer.singleShot(0, lambda: (self.rack.einschuebe and not any(e.hasFocus() for e in self.rack.einschuebe)
                                          and self.rack.erstes_waehlen()))
        elif key == "netz":
            self.netz.aktivieren()
        elif key == "labor":
            self.labor.aktivieren()

    def _seite(self, key):
        self.aktuell = key
        self.stack.setCurrentWidget({"rack": self.rack, "netz": self.netz, "labor": self.labor, "blatt": self.blatt}[key])
        for k, b in self.kopf.reiter.items():
            b.setChecked(k == (key if key != "blatt" else self.vorher))
        self.netz.laufen(key == "netz")

    def zurueck(self):
        if self.aktuell == "blatt":
            self.zeigen(self.vorher)
        elif self.aktuell == "labor" and self.labor.zurueck():
            return
        elif self.kopf.suche.hasFocus() or self.kopf.suche.text():
            self.kopf.suche.clear()
            self.rack.erstes_waehlen()
        elif self.aktuell != "rack":
            self.zeigen("rack")

    def bereich(self, schritt):
        if self.aktuell == "labor" and self.labor.spielt():
            return
        reihe = ["rack", "netz", "labor"]
        jetzt = self.vorher if self.aktuell == "blatt" else self.aktuell
        self.klang.spielen("klick")
        self.zeigen(reihe[(reihe.index(jetzt) + schritt) % len(reihe)])

    def suchen(self):
        if self.aktuell == "labor" and self.labor.spielt():
            return
        if self.aktuell not in ("rack",):
            self.zeigen("rack")
        self.kopf.suche.setFocus()
        self.kopf.suche.selectAll()

    def keyPressEvent(self, ev):
        k = ev.key()
        if k == Qt.Key.Key_Escape:
            self.zurueck()
        elif k == Qt.Key.Key_F11:
            self.showNormal() if self.isFullScreen() else self.showFullScreen()
        elif k == Qt.Key.Key_F5:
            self.neu_laden()
        elif ev.modifiers() & Qt.KeyboardModifier.ControlModifier and k == Qt.Key.Key_F:
            self.suchen()
        elif k in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab) and ev.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.bereich(-1 if k == Qt.Key.Key_Backtab or ev.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1)
        elif k == Qt.Key.Key_F2:
            self.sortierung_weiter()
        else:
            super().keyPressEvent(ev)

    def einstellungen_zeigen(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Bibi Arcade – Einstellungen")
        dlg.setStyleSheet(stil.stil() + f"QDialog {{ background: {R['flaeche']}; }}")
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(22, 18, 22, 16)
        lay.setSpacing(10)
        t = label("EINSTELLUNGEN")
        t.setFont(stil.schrift(13, mono=False, fett=True, abstand=2))
        t.setStyleSheet(f"color: {R['orange']};")
        lay.addWidget(t)

        def schalter(text, schluessel, hinweis):
            c = QCheckBox(text)
            c.setChecked(bool(self.einst[schluessel]))
            c.toggled.connect(lambda an: (self.einst.__setitem__(schluessel, an), stil.json_schreiben(stil.KONFIG, self.einst)))
            lay.addWidget(c)
            lay.addWidget(label(hinweis, "leise", wrap=True))
        schalter("Geräusche", "geraeusche", "Leises Klicken, Relais und Lüfter beim Hochfahren.")
        schalter("Hochfahren beim Start", "hochfahren", "Die Einschübe schalten sich nacheinander ein.")
        schalter("Online prüfen", "online", "Holt die Linux-Ampel von ProtonDB, die Anti-Cheat-Liste von AreWeAntiCheatYet "
                 "und die Spielarten aus dem Steam-Shop. Dabei werden die Nummern deiner Spiele abgefragt, sonst nichts.")
        lay.addSpacing(6)
        unten = QHBoxLayout()
        unten.addWidget(label(f"Bibi Arcade {VERSION}", "dunkel"))
        unten.addStretch(1)
        unten.addWidget(knopf("Fertig", "los", dlg.accept))
        lay.addLayout(unten)
        dlg.resize(520, 360)
        dlg.exec()
        self.klang.an = self.einst["geraeusche"]

    def closeEvent(self, ev):
        self.labor.beenden()
        if self.lader is not None and self.lader.isRunning():
            self.lader.wait(5000)
        super().closeEvent(ev)


def sofa_modus(w):
    """Xbox-Controller: A starten, B zurueck, X Datenblatt, Y suchen, LB/RB Bereich, Start Vollbild.

    Waehrend ein Bibi-Spiel laeuft, gehen die Tasten als Tastendruecke ans Spiel:
    Steuerkreuz = Pfeile, A = Enter, X = Leertaste, Y = Backspace (rueckgaengig), B = Pause.
    """
    sys.path.insert(0, "/usr/share/biblix/gamepad")
    try:
        from biblix_gamepad import Gamepad
    except ImportError:
        return None

    class ArcadeGamepad(Gamepad):
        SPIEL = {"links": Qt.Key.Key_Left, "rechts": Qt.Key.Key_Right, "hoch": Qt.Key.Key_Up, "runter": Qt.Key.Key_Down,
                 "a": Qt.Key.Key_Return, "x": Qt.Key.Key_Space, "y": Qt.Key.Key_Backspace}

        def _taste(self, t):
            app = QApplication.instance()
            if w.labor.spielt() and app.activeWindow() is w and app.activePopupWidget() is None:
                if t == "b":
                    w.zurueck()
                elif t in self.SPIEL and w.labor.buehne.spiel is not None:
                    self._schicken(w.labor.buehne.spiel.focusWidget() or w.labor.buehne.spiel, self.SPIEL[t])
                return
            if t == "ansicht" and app.activeWindow() is w and app.activePopupWidget() is None:
                w.sortierung_weiter()
                return
            super()._taste(t)

    return ArcadeGamepad(w, zurueck=w.zurueck, bereich=w.bereich, y=w.suchen, farbe=R["orange"])


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Bibi Arcade")
    app.setDesktopFileName("de.biblix.Arcade")
    stil.schriften_laden()
    app.setFont(stil.schrift(10.5))
    w = Haupt()
    if "--vollbild" in sys.argv:
        w.showFullScreen()
    else:
        w.show()
    w.gamepad = sofa_modus(w)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
