"""Labor: Pruefstaende fuer die eigenen Bibi-Spiele.

Ein Spiel ist ein Ordner spiele/<kennung>/ mit
    spiel.json   {"kennung", "name", "kurz", "version", "stufen": [...]}
    spiel.py     class Spiel(QWidget): __init__(umgebung), fertig = pyqtSignal(dict),
                 starten(stufe), pausieren(), fortsetzen()
    vorschau.png (optional)
Gesucht wird in /usr/share/biblix/arcade/spiele, ~/.local/share/bibi-arcade/spiele und $BIBI_ARCADE_SPIELE.
Escape gehoert der Arcade (Pausenmenue); das Spiel bekommt Pfeile, Enter, Leertaste und Backspace.
"""
import importlib.util
import json
import os
import time
import traceback
from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QMenu, QStackedWidget, QVBoxLayout, QWidget

import stil
from stil import R, knopf, label

HIER = Path(__file__).resolve().parent
BESTWERTE = stil.DATEN / "bestwerte.json"
SPALTEN = 4


def spiele_orte():
    orte = [HIER / "spiele", stil.DATEN / "spiele"]
    if os.environ.get("BIBI_ARCADE_SPIELE"):
        orte.insert(0, Path(os.environ["BIBI_ARCADE_SPIELE"]))
    return orte


def spiele_finden():
    gefunden, gesehen = [], set()
    for ort in spiele_orte():
        for j in sorted(ort.glob("*/spiel.json")):
            try:
                d = json.loads(j.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            kennung = d.get("kennung") or j.parent.name
            if kennung in gesehen or not (j.parent / "spiel.py").is_file():
                continue
            gesehen.add(kennung)
            d.update({"kennung": kennung, "ordner": str(j.parent)})
            d.setdefault("name", kennung)
            d.setdefault("stufen", [])
            gefunden.append(d)
    return gefunden


def zeit_text(sek):
    sek = int(sek or 0)
    return f"{sek // 60}:{sek % 60:02d}"


class Pruefstand(QWidget):
    """Kachel eines Spiels (oder ein freier Platz)."""

    def __init__(self, seite, nummer, spiel=None):
        super().__init__()
        self.seite, self.nummer, self.spiel = seite, nummer, spiel
        self.hover = False
        self.defekt = False
        self.setMinimumSize(240, 280)
        if spiel:
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.vorschau = stil.bild(str(Path(spiel["ordner"]) / "vorschau.png")) if spiel else None

    def enterEvent(self, _):
        self.hover = True
        self.update()

    def leaveEvent(self, _):
        self.hover = False
        self.update()

    def focusInEvent(self, ev):
        super().focusInEvent(ev)
        self.seite.haupt.klang.spielen("klick")
        self.update()

    def focusOutEvent(self, ev):
        super().focusOutEvent(ev)
        self.update()

    def mouseReleaseEvent(self, ev):
        if self.spiel and ev.button() == Qt.MouseButton.LeftButton:
            self.seite.waehlen(self)

    def keyPressEvent(self, ev):
        k = ev.key()
        if self.spiel and k in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.seite.waehlen(self)
        elif k in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down) and self in self.seite.staende:
            st = self.seite.staende
            i = st.index(self)
            schritt = {Qt.Key.Key_Left: -1, Qt.Key.Key_Right: 1, Qt.Key.Key_Up: -SPALTEN, Qt.Key.Key_Down: SPALTEN}[k]
            if 0 <= i + schritt < len(st):
                st[i + schritt].setFocus(Qt.FocusReason.TabFocusReason)
        else:
            super().keyPressEvent(ev)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        aktiv = self.hasFocus() or self.hover
        if not self.spiel:
            p.setPen(QPen(QColor(R["rahmen"]), 1, Qt.PenStyle.DashLine))
            p.setBrush(QColor("#141619"))
            p.drawRoundedRect(r, 4, 4)
            p.setPen(QColor(R["dunkel"]))
            text = f"PRÜFSTAND {self.nummer}\n\n" + ("Lieferung ausstehend" if self.nummer <= 2 else "frei")
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, text)
            p.end()
            return
        p.setPen(QPen(QColor(R["orange"] if self.hasFocus() else (R["rahmen"] if aktiv else R["rand"])),
                      2 if self.hasFocus() else 1))
        p.setBrush(QColor(R["einschub_an"] if aktiv else R["einschub"]))
        p.drawRoundedRect(r, 4, 4)
        fm = p.fontMetrics()
        klein = stil.schrift(8.5)
        p.setFont(klein)
        p.setPen(QColor(R["dunkel"]))
        p.drawText(QRectF(r.left() + 12, r.top() + 8, r.width() - 24, 18), Qt.AlignmentFlag.AlignLeft, f"PRÜFSTAND {self.nummer}")
        stil.led(p, QPointF(r.right() - 16, r.top() + 16), R["rot"] if self.defekt else R["gruen"], True, 4)
        bild_r = QRectF(r.left() + 12, r.top() + 32, r.width() - 24, r.height() * 0.38)
        p.setPen(QPen(QColor(R["rahmen"]), 1))
        p.setBrush(QColor(R["schwarz"]))
        p.drawRect(bild_r)
        if self.vorschau is not None:
            stil.bild_fuellen(p, bild_r.adjusted(1, 1, -1, -1), self.vorschau)
        else:
            p.setPen(QColor(R["dunkel"]))
            p.drawText(bild_r, Qt.AlignmentFlag.AlignCenter, stil.kennzeichen(self.spiel["name"]))
        y = bild_r.bottom() + 8
        p.setFont(stil.schrift(11.5, mono=False, fett=True))
        p.setPen(QColor("#ffffff" if self.hasFocus() else R["text"]))
        p.drawText(QRectF(r.left() + 12, y, r.width() - 24, 24), Qt.AlignmentFlag.AlignLeft, self.spiel["name"])
        y += 24
        p.setFont(klein)
        p.setPen(QColor(R["leise"]))
        p.drawText(QRectF(r.left() + 12, y, r.width() - 24, r.bottom() - y - 26), Qt.TextFlag.TextWordWrap,
                   "DEFEKT – siehe Systemprotokoll" if self.defekt else self.spiel.get("kurz", ""))
        best = self.seite.bestwert_text(self.spiel["kennung"])
        p.setPen(QColor(R["orange"]))
        p.drawText(QRectF(r.left() + 12, r.bottom() - 22, r.width() - 24, 18), Qt.AlignmentFlag.AlignLeft, best)
        p.end()


class Buehne(QWidget):
    """Hier laeuft ein Bibi-Spiel: Kopfzeile mit Stufe und Zeit, darunter das Spiel, dazu Pause und Ergebnis."""

    def __init__(self, seite):
        super().__init__()
        self.seite = seite
        self.spiel = self.info = None
        self.stufe = ""
        self.start = 0.0
        self.pause_seit = 0.0
        self.pausiert = False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 8, 16, 8)
        lay.setSpacing(6)
        kopf = QHBoxLayout()
        self.titel = label("")
        self.titel.setFont(stil.schrift(12, mono=False, fett=True, abstand=1.5))
        self.titel.setStyleSheet(f"color: {R['orange']};")
        kopf.addWidget(self.titel)
        self.zeit = label("", "leise")
        kopf.addStretch(1)
        kopf.addWidget(self.zeit)
        kopf.addWidget(label("ESC / B: Pause", "dunkel"))
        lay.addLayout(kopf)
        self.platz = QVBoxLayout()
        lay.addLayout(self.platz, 1)
        self.uhr = QTimer(self)
        self.uhr.timeout.connect(self._zeit)
        # Ueberlagerungen
        self.schicht = Schicht(self)
        self.schicht.hide()

    def laden(self, info, stufe):
        self.entladen()
        self.info, self.stufe = info, stufe
        ordner = Path(info["ordner"])
        speicher = stil.DATEN / "spielstaende" / info["kennung"]
        speicher.mkdir(parents=True, exist_ok=True)
        umgebung = {"stufe": stufe, "ton": self.seite.haupt.einst["geraeusche"], "speicher": speicher}
        modul_name = f"bibi_spiel_{info['kennung']}"
        spec = importlib.util.spec_from_file_location(modul_name, ordner / "spiel.py")
        modul = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modul)
        self.spiel = modul.Spiel(umgebung)
        self.spiel.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.spiel.fertig.connect(self._fertig)
        self.platz.addWidget(self.spiel, 1)
        self.titel.setText(f"{info['name'].upper()}" + (f" · {stufe.upper()}" if stufe else ""))
        self.spiel.starten(stufe)
        self.start, self.pausiert = time.monotonic(), False
        self.uhr.start(500)
        self._zeit()
        self.schicht.hide()
        self.spiel.setFocus(Qt.FocusReason.OtherFocusReason)

    def entladen(self):
        self.uhr.stop()
        if self.spiel is not None:
            try:
                self.spiel.pausieren()
            except Exception:  # noqa: BLE001 - fremdes Spiel soll die Arcade nicht mitreissen
                pass
            self.spiel.setParent(None)
            self.spiel.deleteLater()
            self.spiel = None
        self.schicht.hide()

    def _zeit(self):
        if not self.pausiert:
            self.zeit.setText(zeit_text(time.monotonic() - self.start))

    def pause(self):
        if self.spiel is None:
            return
        if self.schicht.isVisible():
            # nochmal B: Pause weg, beim Ergebnis zurueck ins Labor
            self.weiter() if self.schicht.art == "pause" else self.seite.zurueck_ins_labor()
            return
        self.pausiert, self.pause_seit = True, time.monotonic()
        self._sicher(self.spiel.pausieren)
        self.schicht.zeigen("pause", "PAUSE", "", [("WEITER", self.weiter), ("NEU STARTEN", self.neu),
                                                 ("ZURÜCK INS LABOR", self.seite.zurueck_ins_labor)])

    def weiter(self):
        self.schicht.hide()
        if self.pausiert:
            self.start += time.monotonic() - self.pause_seit
        self.pausiert = False
        self._sicher(self.spiel.fortsetzen)
        self.spiel.setFocus(Qt.FocusReason.OtherFocusReason)

    def neu(self):
        self.seite.starten(self.info, self.stufe)

    def _fertig(self, ergebnis):
        dauer = time.monotonic() - self.start
        self.uhr.stop()
        ergebnis = dict(ergebnis or {})
        ergebnis.setdefault("zeit", dauer)
        ergebnis.setdefault("stufe", self.stufe)
        neu_rekord = self.seite.bestwert_merken(self.info["kennung"], ergebnis)
        gewonnen = bool(ergebnis.get("gewonnen"))
        self.seite.haupt.klang.spielen("fertig" if gewonnen else "fehler")
        self.seite.haupt.protokoll.schreiben(
            f"{stil.kennzeichen(self.info['name']).lower()}: {'bestanden' if gewonnen else 'durchgefallen'} "
            f"in {zeit_text(ergebnis['zeit'])}" + (" · neuer rekord" if neu_rekord else ""),
            R["gruen"] if gewonnen else R["rot"])
        teile = [f"Zeit {zeit_text(ergebnis['zeit'])}"]
        if ergebnis.get("punkte"):
            teile.append(f"{ergebnis['punkte']} Punkte")
        if neu_rekord:
            teile.append("NEUER REKORD")
        self.schicht.zeigen("ende", "PRÜFUNG BESTANDEN" if gewonnen else "PRÜFUNG NICHT BESTANDEN", " · ".join(teile),
                            [("NOCHMAL", self.neu), ("ZURÜCK INS LABOR", self.seite.zurueck_ins_labor)],
                            R["gruen"] if gewonnen else R["rot"])

    def _sicher(self, fn):
        try:
            fn()
        except Exception:  # noqa: BLE001
            self.seite.haupt.protokoll.schreiben("spiel meldet einen fehler", R["rot"])

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self.schicht.setGeometry(self.rect())


class Schicht(QWidget):
    """Halbdurchsichtige Ueberlagerung fuer Pause und Ergebnis."""

    def __init__(self, buehne):
        super().__init__(buehne)
        self.art = ""
        self.farbe = R["orange"]
        lay = QVBoxLayout(self)
        lay.addStretch(1)
        self.titel = label("")
        self.titel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titel.setFont(stil.schrift(22, mono=False, fett=True, abstand=3))
        lay.addWidget(self.titel)
        self.text = label("", "leise")
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.text)
        self.knoepfe = QVBoxLayout()
        self.knoepfe.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(16)
        lay.addLayout(self.knoepfe)
        lay.addStretch(1)

    def zeigen(self, art, titel, text, knoepfe, farbe=None):
        self.art = art
        self.farbe = farbe or R["orange"]
        self.titel.setText(titel)
        self.titel.setStyleSheet(f"color: {self.farbe};")
        self.text.setText(text)
        while self.knoepfe.count():
            w = self.knoepfe.takeAt(0).widget()
            if w:
                w.deleteLater()
        erster = None
        for i, (t, cb) in enumerate(knoepfe):
            b = knopf(t, "los" if i == 0 else None, cb)
            b.setMinimumWidth(260)
            self.knoepfe.addWidget(b)
            erster = erster or b
        self.setGeometry(self.parentWidget().rect())
        self.show()
        self.raise_()
        if erster:
            erster.setFocus(Qt.FocusReason.OtherFocusReason)

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(10, 11, 12, 215))
        p.end()


class LaborSeite(QWidget):
    def __init__(self, haupt):
        super().__init__()
        self.haupt = haupt
        self.spiele = []
        self.staende = []
        self.bestwerte = stil.json_lesen(BESTWERTE, {})
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack)
        self.halle = QWidget()
        self.hl = QVBoxLayout(self.halle)
        self.hl.setContentsMargins(24, 14, 24, 10)
        self.hl.setSpacing(10)
        kopf = label("LABOR · PRÜFSTÄNDE FÜR BIBI-SPIELE")
        kopf.setFont(stil.schrift(12, mono=False, fett=True, abstand=2))
        kopf.setStyleSheet(f"color: {R['orange']};")
        self.hl.addWidget(kopf)
        self.hinweis = label("", "leise", wrap=True)
        self.hl.addWidget(self.hinweis)
        self.raster = QGridLayout()
        self.raster.setSpacing(12)
        self.raster.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.hl.addLayout(self.raster)
        self.hl.addStretch(1)
        self.buehne = Buehne(self)
        self.stack.addWidget(self.halle)
        self.stack.addWidget(self.buehne)
        self.aufbauen()

    def aufbauen(self):
        self.spiele = spiele_finden()
        while self.raster.count():
            w = self.raster.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.staende = []
        anzahl = max(4, len(self.spiele) + 1)
        for i in range(anzahl):
            s = self.spiele[i] if i < len(self.spiele) else None
            st = Pruefstand(self, i + 1, s)
            self.raster.addWidget(st, i // SPALTEN, i % SPALTEN)
            if s:
                self.staende.append(st)
        if self.spiele:
            self.hinweis.setText(f"{len(self.spiele)} Spiel{'e' if len(self.spiele) != 1 else ''} auf dem Prüfstand. "
                                 "Enter oder A startet, Escape oder B pausiert.")
        else:
            self.hinweis.setText("Noch keine Bibi-Spiele geliefert. Sobald Muttern-Suche oder Bibi-Patience fertig sind, "
                                 "stecken sie sich hier in einen freien Prüfstand.")

    def aktivieren(self):
        if self.stack.currentWidget() is self.buehne and self.buehne.spiel is not None:
            if not self.buehne.schicht.isVisible():
                self.buehne.pause()
            return
        self.aufbauen()
        self._erstes()

    def _erstes(self):
        # Die Pruefstaende sind gerade neu gebaut und erst nach dem naechsten Durchlauf sichtbar
        QTimer.singleShot(0, lambda: self.staende and self.staende[0].setFocus(Qt.FocusReason.OtherFocusReason))

    def spielt(self):
        return self.stack.currentWidget() is self.buehne and self.buehne.spiel is not None and not self.buehne.schicht.isVisible()

    def waehlen(self, stand):
        s = stand.spiel
        stufen = s.get("stufen") or []
        if len(stufen) <= 1:
            self.starten(s, stufen[0] if stufen else "")
            return
        m = QMenu(self)
        m.setStyleSheet(stil.stil())
        for st in stufen:
            m.addAction(st, lambda st=st: self.starten(s, st))
        m.exec(stand.mapToGlobal(stand.rect().center()))

    def starten(self, info, stufe):
        try:
            self.stack.setCurrentWidget(self.buehne)
            self.buehne.laden(info, stufe)
            self.haupt.klang.spielen("start")
            self.haupt.protokoll.schreiben(f"prüfstand: {info['kennung']} ({stufe or 'standard'})", R["orange"])
            self.haupt.fuss.spiel_hilfe(True)
        except Exception:  # noqa: BLE001 - ein kaputtes Spiel darf die Arcade nicht abstuerzen lassen
            fehler = traceback.format_exc().strip().splitlines()[-1]
            self.haupt.klang.spielen("fehler")
            self.haupt.protokoll.schreiben(f"{info['kennung']}: defekt – {fehler}", R["rot"])
            self.buehne.entladen()
            self.stack.setCurrentWidget(self.halle)
            for st in self.staende:
                if st.spiel is info:
                    st.defekt = True
                    st.update()
                    st.setFocus()

    def zurueck_ins_labor(self):
        self.buehne.entladen()
        self.haupt.fuss.spiel_hilfe(False)
        self.stack.setCurrentWidget(self.halle)
        self.aufbauen()
        self._erstes()

    def zurueck(self):
        """B/Escape: im Spiel Pause (und wieder weiter); True = erledigt."""
        if self.stack.currentWidget() is self.buehne and self.buehne.spiel is not None:
            self.buehne.pause()
            return True
        return False

    def beenden(self):
        self.buehne.entladen()
        self.haupt.fuss.spiel_hilfe(False)

    # ---- Bestwerte

    def bestwert_merken(self, kennung, e):
        """Siege, Spiele, beste Zeit (nur Siege) und beste Punkte je Stufe; True = neuer Rekord."""
        stufe = e.get("stufe") or "standard"
        d = self.bestwerte.setdefault(kennung, {}).setdefault(stufe, {"spiele": 0, "siege": 0})
        d["spiele"] += 1
        rekord = False
        if e.get("gewonnen"):
            d["siege"] += 1
            if "beste_zeit" not in d or e["zeit"] < d["beste_zeit"]:
                rekord = "beste_zeit" in d  # erster Sieg ist noch kein Rekord
                d["beste_zeit"] = round(e["zeit"], 1)
        if e.get("punkte") and e["punkte"] > d.get("beste_punkte", 0):
            rekord = rekord or "beste_punkte" in d
            d["beste_punkte"] = e["punkte"]
        stil.json_schreiben(BESTWERTE, self.bestwerte)
        return rekord

    def bestwert_text(self, kennung):
        stufen = self.bestwerte.get(kennung, {})
        if not stufen:
            return "noch nicht geprüft"
        siege = sum(d.get("siege", 0) for d in stufen.values())
        zeiten = [d["beste_zeit"] for d in stufen.values() if "beste_zeit" in d]
        return f"{siege} bestanden" + (f" · beste {zeit_text(min(zeiten))}" if zeiten else "")
