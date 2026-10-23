"""Sofa-Modus: Biblix-Apps (PyQt6) mit dem Xbox-Controller bedienen.

Steuerkreuz / linker Stick: Auswahl wandert zum naechsten Element in dieser Richtung
A: auswaehlen · B: zurueck · X: Menue (wie Rechtsklick) · Y: App-eigene Aktion
LB / RB: Bereich wechseln · Start: Vollbild an/aus

    from biblix_gamepad import Gamepad
    pad = Gamepad(fenster, zurueck=..., bereich=..., y=...)

Gelesen wird ueber evdev (python3-evdev). Nur das gerade aktive Biblix-Fenster reagiert,
damit ein Spiel im Vordergrund nicht nebenbei den S-Launcher bedient.
"""
import select
import time

from PyQt6.QtCore import QEvent, QPoint, QRect, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (QAbstractButton, QAbstractScrollArea, QApplication, QComboBox, QLineEdit, QScrollArea,
                             QScrollBar, QWidget)

try:
    import evdev
    from evdev import ecodes
except ImportError:  # ohne python3-evdev bleibt alles wie bisher
    evdev = None

TASTEN = {
    "BTN_SOUTH": "a", "BTN_EAST": "b", "BTN_X": "x", "BTN_Y": "y",
    "BTN_TL": "lb", "BTN_TR": "rb", "BTN_START": "start", "BTN_SELECT": "ansicht",
}
WIEDERHOLEN_AB, WIEDERHOLEN_ALLE = 0.38, 0.12
STICK_SCHWELLE = 0.6


class Leser(QThread):
    """Liest alle angeschlossenen Gamepads; neue Controller werden alle 3 s gefunden."""
    taste = pyqtSignal(str)

    def run(self):
        geraete, gesucht = {}, 0.0
        richtung, seit, zuletzt = None, 0.0, 0.0
        stick, kreuz = {"x": 0.0, "y": 0.0}, {"x": 0, "y": 0}
        while not self.isInterruptionRequested():
            if time.monotonic() - gesucht > 3:
                gesucht = time.monotonic()
                for pfad in evdev.list_devices():
                    if pfad in geraete:
                        continue
                    try:
                        d = evdev.InputDevice(pfad)
                        tasten = d.capabilities().get(ecodes.EV_KEY, [])
                        if ecodes.BTN_SOUTH in tasten and ecodes.EV_ABS in d.capabilities():
                            geraete[pfad] = d
                        else:
                            d.close()
                    except OSError:
                        pass
            if not geraete:
                self.msleep(500)
                continue
            try:
                bereit, _, _ = select.select(list(geraete.values()), [], [], 0.05)
            except (OSError, ValueError):
                bereit = []
            for d in bereit:
                try:
                    ereignisse = list(d.read())
                except OSError:  # Controller abgezogen
                    geraete.pop(d.path, None)
                    continue
                for ev in ereignisse:
                    if ev.type == ecodes.EV_KEY and ev.value == 1:
                        namen = ecodes.BTN.get(ev.code) or ecodes.KEY.get(ev.code) or ""
                        for n in (namen if isinstance(namen, list) else [namen]):
                            if n in TASTEN:
                                self.taste.emit(TASTEN[n])
                                break
                    elif ev.type == ecodes.EV_ABS:
                        if ev.code == ecodes.ABS_HAT0X:
                            kreuz["x"] = ev.value
                        elif ev.code == ecodes.ABS_HAT0Y:
                            kreuz["y"] = ev.value
                        elif ev.code in (ecodes.ABS_X, ecodes.ABS_Y):
                            info = d.absinfo(ev.code)
                            mitte = (info.max + info.min) / 2
                            halb = max(1, (info.max - info.min) / 2)
                            stick["x" if ev.code == ecodes.ABS_X else "y"] = (ev.value - mitte) / halb
            # Richtung aus Steuerkreuz oder Stick, mit Tastenwiederholung beim Festhalten
            neu = None
            if kreuz["x"] or kreuz["y"]:
                neu = ("rechts" if kreuz["x"] > 0 else "links") if kreuz["x"] else ("runter" if kreuz["y"] > 0 else "hoch")
            elif max(abs(stick["x"]), abs(stick["y"])) > STICK_SCHWELLE:
                if abs(stick["x"]) > abs(stick["y"]):
                    neu = "rechts" if stick["x"] > 0 else "links"
                else:
                    neu = "runter" if stick["y"] > 0 else "hoch"
            jetzt = time.monotonic()
            if neu != richtung:
                richtung, seit, zuletzt = neu, jetzt, jetzt
                if neu:
                    self.taste.emit(neu)
            elif neu and jetzt - seit > WIEDERHOLEN_AB and jetzt - zuletzt > WIEDERHOLEN_ALLE:
                zuletzt = jetzt
                self.taste.emit(neu)
        for d in geraete.values():
            try:
                d.close()
            except OSError:
                pass


SOFA_STIL = """
QPushButton:focus, QToolButton:focus, QComboBox:focus, QCheckBox:focus, QLineEdit:focus {{
    border: 3px solid {farbe}; }}
QFrame:focus {{ border: 3px solid {farbe}; }}
"""


class Gamepad:
    """Verbindet den Controller mit einem Hauptfenster.

    zurueck(): B, wenn kein Dialog oder Menue offen ist · bereich(+1/-1): LB/RB · y(): Y-Taste.
    farbe: Farbe des Auswahlrahmens (kommt beim ersten Tastendruck dazu, Maus-Bedienung bleibt wie gehabt).
    """

    def __init__(self, fenster, zurueck=None, bereich=None, y=None, farbe="#378add"):
        self.fenster, self.zurueck, self.bereich, self.y, self.farbe = fenster, zurueck, bereich, y, farbe
        self.sofa = False
        self.leser = None
        if evdev is None:
            return
        self.leser = Leser()
        self.leser.taste.connect(self._taste)
        self.leser.start()
        QApplication.instance().aboutToQuit.connect(self.beenden)

    def beenden(self):
        if self.leser is not None and self.leser.isRunning():
            self.leser.requestInterruption()
            self.leser.wait(1500)

    # ---- Tasten

    def _taste(self, t):
        app = QApplication.instance()
        aktiv = app.activeWindow()
        popup = app.activePopupWidget()
        if aktiv is None and popup is None:
            return  # anderes Programm (z. B. ein Spiel) ist vorne
        erster = not self.sofa
        if erster:
            self.sofa = True
            app.setStyleSheet(app.styleSheet() + SOFA_STIL.format(farbe=self.farbe))
        ziel = popup or aktiv
        richtungen = {"links": Qt.Key.Key_Left, "rechts": Qt.Key.Key_Right, "hoch": Qt.Key.Key_Up, "runter": Qt.Key.Key_Down}
        if popup is not None:
            # Menues und Auswahllisten verstehen Pfeiltasten selbst
            schluessel = richtungen.get(t) or {"a": Qt.Key.Key_Return, "b": Qt.Key.Key_Escape}.get(t)
            if schluessel:
                self._schicken(popup, schluessel)
            return
        if t in richtungen:
            self._bewegen(aktiv, t, erster)
        elif t == "a":
            w = aktiv.focusWidget()
            if isinstance(w, QAbstractButton):
                w.click()
            elif isinstance(w, QComboBox):
                w.showPopup()
            elif w is not None:
                self._schicken(w, Qt.Key.Key_Return)
            else:
                self._bewegen(aktiv, "runter")
        elif t == "b":
            if aktiv is not self.fenster:
                self._schicken(aktiv, Qt.Key.Key_Escape)  # Dialog schliessen
            elif self.zurueck:
                self.zurueck()
        elif t == "x":
            w = aktiv.focusWidget()
            if w is not None:
                self._schicken(w, Qt.Key.Key_Menu)
        elif t == "y" and self.y and aktiv is self.fenster:
            self.y()
        elif t in ("lb", "rb") and self.bereich and aktiv is self.fenster:
            self.bereich(1 if t == "rb" else -1)
        elif t == "start" and aktiv is self.fenster:
            self.fenster.showNormal() if self.fenster.isFullScreen() else self.fenster.showFullScreen()

    @staticmethod
    def _schicken(w, schluessel):
        for art in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            QApplication.sendEvent(w, QKeyEvent(art, schluessel, Qt.KeyboardModifier.NoModifier))

    # ---- Auswahl raeumlich bewegen

    @staticmethod
    def _kandidaten(fenster):
        liste = []
        for w in fenster.findChildren(QWidget):
            if (w.isVisible() and w.isEnabled() and w.focusPolicy() & Qt.FocusPolicy.TabFocus
                    and not isinstance(w, (QScrollBar, QAbstractScrollArea)) and w.window() is fenster):
                liste.append(w)
        return liste

    @staticmethod
    def _rechteck(w, fenster):
        return QRect(w.mapTo(fenster, QPoint(0, 0)), w.size())

    def _bewegen(self, fenster, richtung, neu_anfangen=False):
        alle = self._kandidaten(fenster)
        if not alle:
            return
        jetzt = fenster.focusWidget()
        if neu_anfangen or jetzt not in alle or isinstance(jetzt, QLineEdit):
            # Erster Druck oder neue Seite: oben links im Inhalt anfangen (Kopfleiste und Suchfeld zuletzt)
            def start(w):
                rr = self._rechteck(w, fenster)
                return (1 if rr.top() < 80 or isinstance(w, QLineEdit) else 0, rr.top() // 40, rr.left())
            self._fokus(min(alle, key=start))
            return
        a = self._rechteck(jetzt, fenster)
        ac = a.center()
        bester, wert_bester = None, None
        for w in alle:
            if w is jetzt:
                continue
            b = self._rechteck(w, fenster)
            bc = b.center()
            dx, dy = bc.x() - ac.x(), bc.y() - ac.y()
            if richtung == "rechts":
                haupt, neben, ok = dx, abs(dy), b.left() >= a.right() - 4
                ueberlapp = b.top() < a.bottom() and b.bottom() > a.top()
            elif richtung == "links":
                haupt, neben, ok = -dx, abs(dy), b.right() <= a.left() + 4
                ueberlapp = b.top() < a.bottom() and b.bottom() > a.top()
            elif richtung == "runter":
                haupt, neben, ok = dy, abs(dx), b.top() >= a.bottom() - 4
                ueberlapp = b.left() < a.right() and b.right() > a.left()
            else:
                haupt, neben, ok = -dy, abs(dx), b.bottom() <= a.top() + 4
                ueberlapp = b.left() < a.right() and b.right() > a.left()
            if not ok or haupt <= 0:
                continue
            # In derselben Reihe/Spalte zuerst, dann der naechste
            wert = (0 if ueberlapp else 1, haupt + 2 * neben)
            if wert_bester is None or wert < wert_bester:
                bester, wert_bester = w, wert
        if bester is not None:
            self._fokus(bester)

    @staticmethod
    def _fokus(w):
        w.setFocus(Qt.FocusReason.TabFocusReason)
        # Alle umgebenden Scrollbereiche so schieben, dass die Auswahl zu sehen ist
        eltern = w.parentWidget()
        while eltern is not None:
            if isinstance(eltern, QScrollArea):
                eltern.ensureWidgetVisible(w, 60, 60)
            eltern = eltern.parentWidget()
