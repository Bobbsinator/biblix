"""Netz-Ansicht: die Spielebibliothek als lebendiges Netzwerk.

Knoten
    DU          Mitte; je naeher ein Spiel, desto kuerzlicher gespielt
    Spiel       Groesse nach Spielzeit, 2 Wochen oder Speicher (G / Ansicht-Taste), Rand = Linux-Ampel,
                oranger Ring = Anteil an deiner gesamten Spielzeit
    Spielart    Sechseck (Simulationen, Rollenspiel …); verbindet Spiele gleicher Art
    Labor       Sechseck mit den Bibi-Spielen drumherum; Enter startet sie
Datenpakete laufen von DU zu den Spielen: je mehr du ein Spiel gerade spielst, desto mehr Verkehr,
ein laufendes Spiel bekommt einen orangen Datenstrom.

Bedienung: Pfeile/Steuerkreuz springen, Enter/A starten, X/Leertaste Datenblatt, Mausrad zoomt,
Hintergrund ziehen verschiebt, Knoten ziehen verschiebt den Knoten, 0 = alles wieder mittig,
S = Spielarten an/aus. Jeder Knoten hat ein unsichtbares Fokus-Widget, damit Controller und
Tastatur ganz normal springen koennen.
"""
import math
import random

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QHBoxLayout, QWidget

import steam
import stil
from stil import R, knopf

ALLGEMEIN = {"Action", "Indie", "Early Access", "Gelegenheitsspiele", "Free to Play", "Kostenlos spielbar",
             "Massively Multiplayer"}
GROESSEN = [("spielzeit", "SPIELZEIT"), ("zwei_wochen", "LETZTE 2 WOCHEN"), ("speicher", "SPEICHER")]


class Knoten:
    def __init__(self, typ, kennung, name, x, y):
        self.typ, self.kennung, self.name = typ, kennung, name   # typ: spiel | art | labor | bibi
        self.x, self.y, self.vx, self.vy = x, y, 0.0, 0.0
        self.r = 20.0
        self.ziel = 0.6          # Wunschabstand zu DU (Anteil der Ellipse), nur fuer Spiele
        self.spiel = None        # Steam-Spiel (dict) oder Bibi-Spiel (spiel.json)
        self.mitglieder = []     # Spielart/Labor: angeschlossene Knoten
        self.fokus = None
        self.gezogen = False


class KnotenFokus(QWidget):
    """Unsichtbarer, fokussierbarer Platzhalter ueber einem Knoten (Maus, Tastatur, Controller)."""

    def __init__(self, seite, knoten):
        super().__init__(seite)
        self.seite, self.knoten = seite, knoten
        self.druck = None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setToolTip(knoten.name)

    def focusInEvent(self, ev):
        super().focusInEvent(ev)
        self.seite.gewaehlt = self.knoten
        self.seite.haupt.klang.spielen("klick")
        self.seite.update()

    def focusOutEvent(self, ev):
        super().focusOutEvent(ev)
        self.seite.update()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.setFocus(Qt.FocusReason.MouseFocusReason)
            self.druck = ev.globalPosition()

    def mouseMoveEvent(self, ev):
        if self.druck is None:
            return
        if not self.knoten.gezogen and (ev.globalPosition() - self.druck).manhattanLength() < 6:
            return
        # Knoten mit der Maus verschieben
        self.knoten.gezogen = True
        p = self.seite.welt(QPointF(self.seite.mapFromGlobal(ev.globalPosition().toPoint())))
        self.knoten.x, self.knoten.y, self.knoten.vx, self.knoten.vy = p.x(), p.y(), 0.0, 0.0
        self.seite.update()

    def mouseReleaseEvent(self, ev):
        self.druck = None
        self.knoten.gezogen = False

    def mouseDoubleClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.seite.starten(self.knoten)

    def contextMenuEvent(self, _):
        self.seite.datenblatt(self.knoten)

    def wheelEvent(self, ev):
        self.seite.wheelEvent(ev)

    def keyPressEvent(self, ev):
        k = ev.key()
        if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.seite.starten(self.knoten)
        elif k in (Qt.Key.Key_Menu, Qt.Key.Key_I, Qt.Key.Key_Space):
            self.seite.datenblatt(self.knoten)
        elif k in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
            self.seite.springen(self.knoten, k)
        elif k == Qt.Key.Key_E and not ev.modifiers() and self.knoten.typ == "spiel":
            self.seite.haupt.einladen(self.knoten.spiel)
        else:
            self.seite.taste(ev)

    def paintEvent(self, _):
        pass


class NetzSeite(QWidget):
    def __init__(self, haupt):
        super().__init__()
        self.haupt = haupt
        self.knoten = {}          # kennung -> Knoten (Spiele: appid, Spielarten: "art:Name", Labor: "labor", Bibi: "bibi:id")
        self.gewaehlt = None
        self.zeit = 0.0
        self.pakete = []          # [ziel_kennung, fortschritt, tempo, laufend]
        self.rnd = random.Random(7)
        self.zoom, self.versatz = 1.0, QPointF(0, 0)
        self.ziehen = None
        self.groesse = "spielzeit"
        self.arten_an = True
        self.eingeflogen = False
        self.setMouseTracking(True)
        self.takt = QTimer(self)
        self.takt.timeout.connect(self._schritt)
        # Leiste oben links
        leiste = QWidget(self)
        ll = QHBoxLayout(leiste)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(8)
        self.k_groesse = knopf("", cb=self.groesse_weiter)
        self.k_arten = knopf("", cb=self.arten_umschalten)
        self.k_mitte = knopf("⌖ MITTIG", cb=self.zuruecksetzen)
        for b in (self.k_groesse, self.k_arten, self.k_mitte):
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Controller springt nur zwischen Knoten
            ll.addWidget(b)
        leiste.move(18, 14)
        self.leiste = leiste
        self._leiste_text()

    # ---- Aufbau

    def aufbauen(self):
        alt = self.knoten
        self.knoten = {}
        liste = self.haupt.sichtbar

        def holen(kennung, typ, name, winkel, abstand):
            k = alt.pop(kennung, None)
            if k is None:
                if self.eingeflogen:
                    k = Knoten(typ, kennung, name, math.cos(winkel) * abstand, math.sin(winkel) * abstand * 0.7)
                else:
                    # erster Aufbau: alles startet in DU und fliegt hinaus
                    k = Knoten(typ, kennung, name, self.rnd.uniform(-6, 6), self.rnd.uniform(-6, 6))
            k.name = name
            k.mitglieder = []
            self.knoten[kennung] = k
            return k

        for i, s in enumerate(liste):
            k = holen(s["id"], "spiel", s["name"], i * 2.399963, 260)
            k.spiel = s
        # Spielarten-Knoten fuer Arten, die mindestens zwei Spiele teilen
        if self.arten_an:
            zaehl = {}
            for s in liste:
                for g in set(self.haupt.genres.get(s["id"], [])) - ALLGEMEIN:
                    zaehl.setdefault(g, []).append(s["id"])
            for i, (art, ids) in enumerate(sorted(zaehl.items())):
                if len(ids) < 2:
                    continue
                k = holen("art:" + art, "art", art, i * 1.7 + 0.8, 340)
                k.mitglieder = [self.knoten[x] for x in ids]
        # Labor mit den Bibi-Spielen
        bibi = getattr(self.haupt.labor, "spiele", [])
        if bibi:
            lab = holen("labor", "labor", "LABOR", math.pi * 0.8, 300)
            for i, info in enumerate(bibi):
                b = holen("bibi:" + info["kennung"], "bibi", info["name"], i * 2.0, 360)
                b.spiel = info
                lab.mitglieder.append(b)
        for k in alt.values():
            if k.fokus is not None:
                k.fokus.deleteLater()
        if self.gewaehlt is not None and self.gewaehlt.kennung not in self.knoten:
            self.gewaehlt = None
        self._groessen()
        for k in self.knoten.values():
            if k.fokus is None:
                k.fokus = KnotenFokus(self, k)
                k.fokus.show()
        self.leiste.raise_()
        self._fokus_setzen()
        self.update()

    def _wert(self, s):
        return {"spielzeit": s["minuten"], "zwei_wochen": s["zwei_wochen"], "speicher": s["groesse"] / 1e8}[self.groesse]

    def _groessen(self):
        spiele = [k for k in self.knoten.values() if k.typ == "spiel"]
        if spiele:
            hoechst = max([self._wert(k.spiel) for k in spiele] + [1])
            for rang, k in enumerate(sorted(spiele, key=lambda k: -k.spiel["zuletzt"])):
                k.r = 15 + 37 * math.sqrt(max(0.0, self._wert(k.spiel)) / hoechst)
                k.ziel = 0.34 + 0.58 * rang / max(1, len(spiele) - 1)
        for k in self.knoten.values():
            if k.typ == "art":
                k.r = 15 + 3 * len(k.mitglieder)
            elif k.typ == "labor":
                k.r = 22
            elif k.typ == "bibi":
                k.r = 17

    # ---- Leiste

    def _leiste_text(self):
        name = dict(GROESSEN)[self.groesse]
        self.k_groesse.setText(f"GRÖSSE: {name} ▸")
        self.k_arten.setText("SPIELARTEN: AN" if self.arten_an else "SPIELARTEN: AUS")
        for b in (self.k_groesse, self.k_arten, self.k_mitte):
            # Breite selbst setzen: das Stylesheet (Polsterung) greift erst nach dem ersten Zeigen
            b.setMinimumWidth(b.fontMetrics().horizontalAdvance(b.text()) + 44)
        self.leiste.adjustSize()

    def groesse_weiter(self):
        werte = [g for g, _ in GROESSEN]
        self.groesse = werte[(werte.index(self.groesse) + 1) % len(werte)]
        self._leiste_text()
        self._groessen()
        self.haupt.klang.spielen("klick")
        self.update()

    def arten_umschalten(self):
        self.arten_an = not self.arten_an
        self._leiste_text()
        self.aufbauen()

    def zuruecksetzen(self):
        self.zoom, self.versatz = 1.0, QPointF(0, 0)
        for k in self.knoten.values():
            k.vx = k.vy = 0.0
        self._fokus_setzen()
        self.update()

    # ---- Bewegung

    def laufen(self, an):
        if an:
            self.takt.start(33)
        else:
            self.takt.stop()

    def aktivieren(self):
        self.aufbauen()
        self.eingeflogen = True
        ziel = self.gewaehlt.fokus if self.gewaehlt and self.gewaehlt.fokus else None
        if ziel is None:
            spiele = [k for k in self.knoten.values() if k.typ == "spiel"]
            if spiele:
                ziel = max(spiele, key=lambda k: k.spiel["zuletzt"]).fokus
        if ziel is not None:
            ziel.setFocus(Qt.FocusReason.OtherFocusReason)

    def _halbachsen(self):
        return max(120.0, self.width() * 0.42), max(90.0, (self.height() - 110) * 0.42)

    def _schritt(self):
        self.zeit += 0.033
        ax, ay = self._halbachsen()
        ks = list(self.knoten.values())
        for k in ks:
            if k.gezogen:
                continue
            fx = fy = 0.0
            if k.typ == "spiel" or (k.typ == "labor"):
                # Feder zum Wunschabstand von DU (in einer Ellipse, die die Flaeche fuellt)
                ziel = k.ziel if k.typ == "spiel" else 0.82
                dx, dy = k.x / ax, k.y / ay
                d = math.hypot(dx, dy) or 0.01
                f = (ziel - d) * 0.6
                fx += dx / d * f * ax * 0.05
                fy += dy / d * f * ay * 0.05
            elif k.typ == "art" and k.mitglieder:
                # Spielart: bei ihren Spielen, aber immer gut ausserhalb von DU (liegen die Spiele
                # gegenueber, waere die Mitte genau bei DU)
                mx = sum(m.x for m in k.mitglieder) / len(k.mitglieder)
                my = sum(m.y for m in k.mitglieder) / len(k.mitglieder)
                d = math.hypot(mx / ax, my / ay)
                if d < 0.55:
                    if d < 0.05:
                        winkel = (hash(k.kennung) % 628) / 100
                        mx, my = math.cos(winkel) * ax * 0.05, math.sin(winkel) * ay * 0.05
                        d = 0.05
                    mx, my = mx * 0.55 / d, my * 0.55 / d
                fx += (mx - k.x) * 0.03
                fy += (my - k.y) * 0.03
            elif k.typ == "bibi":
                lab = self.knoten.get("labor")
                if lab:
                    dx, dy = k.x - lab.x, k.y - lab.y
                    d = math.hypot(dx, dy) or 0.01
                    fx += (dx / d) * (78 - d) * 0.05
                    fy += (dy / d) * (78 - d) * 0.05
            # DU freihalten
            d0 = math.hypot(k.x, k.y) or 0.01
            if d0 < k.r + 70:
                fx += k.x / d0 * (k.r + 70 - d0) * 0.08
                fy += k.y / d0 * (k.r + 70 - d0) * 0.08
            # Knoten weichen sich aus
            for o in ks:
                if o is k:
                    continue
                ox, oy = k.x - o.x, k.y - o.y
                od = math.hypot(ox, oy) or 0.01
                platz = (k.r + o.r + 36) * (2.0 if k.typ == o.typ == "spiel" else 1.4)
                if od < platz:
                    fx += ox / od * (platz - od) * 0.03
                    fy += oy / od * (platz - od) * 0.03
            # leichtes Schweben
            phase = (hash(k.kennung) % 100) / 10
            fx += math.sin(self.zeit * 0.7 + phase) * 0.05
            fy += math.cos(self.zeit * 0.6 + phase) * 0.05
            k.vx = (k.vx + fx) * 0.82
            k.vy = (k.vy + fy) * 0.82
        for k in ks:
            if not k.gezogen:
                k.x = min(max(k.x + k.vx, -ax * 1.15), ax * 1.15)
                k.y = min(max(k.y + k.vy, -ay * 1.1), ay * 1.1)
        self._pakete()
        self._fokus_setzen()
        self.update()

    def _pakete(self):
        """Datenverkehr DU -> Spiel: je mehr zuletzt gespielt, desto mehr Pakete; laufend = oranger Strom."""
        laufend = self.haupt.laufend
        hoechst = max([k.spiel["zwei_wochen"] for k in self.knoten.values() if k.typ == "spiel"] + [1])
        for k in self.knoten.values():
            if k.typ != "spiel":
                continue
            an = k.spiel["id"] in laufend
            rate = 0.25 if an else 0.004 + 0.035 * (k.spiel["zwei_wochen"] / hoechst)
            if self.rnd.random() < rate and len(self.pakete) < 160:
                self.pakete.append([k.kennung, 0.0, (0.03 if an else 0.012) * self.rnd.uniform(0.8, 1.25), an])
        for p in self.pakete:
            p[1] += p[2]
        self.pakete = [p for p in self.pakete if p[1] < 1.0 and p[0] in self.knoten]

    # ---- Ansicht (Zoom und Verschieben)

    def bild(self, x, y):
        """Weltkoordinate (DU = 0,0) -> Bildschirm."""
        return QPointF(self.width() / 2 + x * self.zoom + self.versatz.x(),
                       self.height() / 2 + 14 + y * self.zoom + self.versatz.y())

    def welt(self, punkt):
        return QPointF((punkt.x() - self.width() / 2 - self.versatz.x()) / self.zoom,
                       (punkt.y() - self.height() / 2 - 14 - self.versatz.y()) / self.zoom)

    def wheelEvent(self, ev):
        maus = QPointF(self.mapFromGlobal(ev.globalPosition().toPoint()))
        alt = self.welt(maus)
        faktor = 1.12 if ev.angleDelta().y() > 0 else 1 / 1.12
        self.zoom = min(2.6, max(0.45, self.zoom * faktor))
        # Punkt unter der Maus bleibt stehen
        self.versatz += maus - self.bild(alt.x(), alt.y())
        self._fokus_setzen()
        self.update()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.ziehen = (ev.position(), QPointF(self.versatz))
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, ev):
        if self.ziehen is not None:
            start, alt = self.ziehen
            self.versatz = alt + (ev.position() - start)
            self._fokus_setzen()
            self.update()

    def mouseReleaseEvent(self, _):
        self.ziehen = None
        self.unsetCursor()

    def taste(self, ev):
        k = ev.key()
        if k in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.zoom = min(2.6, self.zoom * 1.15)
        elif k == Qt.Key.Key_Minus:
            self.zoom = max(0.45, self.zoom / 1.15)
        elif k == Qt.Key.Key_0:
            self.zuruecksetzen()
            return
        elif k == Qt.Key.Key_G:
            self.groesse_weiter()
            return
        elif k == Qt.Key.Key_S and not ev.modifiers():
            self.arten_umschalten()
            return
        else:
            ev.ignore()
            return
        self._fokus_setzen()
        self.update()

    def keyPressEvent(self, ev):
        self.taste(ev)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._fokus_setzen()

    def _fokus_setzen(self):
        for k in self.knoten.values():
            if k.fokus is not None:
                b = self.bild(k.x, k.y)
                r = k.r * self.zoom
                k.fokus.setGeometry(int(b.x() - r), int(b.y() - r), int(2 * r), int(2 * r))

    # ---- Aktionen

    def starten(self, k):
        if k.typ == "spiel":
            self.haupt.spiel_starten(k.spiel)
        elif k.typ == "bibi":
            self.haupt.zeigen("labor")
            stand = next((st for st in self.haupt.labor.staende if st.spiel["kennung"] == k.spiel["kennung"]), None)
            if stand is not None:
                stand.setFocus()
                self.haupt.labor.waehlen(stand)
        elif k.typ == "labor":
            self.haupt.zeigen("labor")
        elif k.typ == "art" and k.mitglieder:
            # Spielart: zum meistgespielten Spiel dieser Art springen
            max(k.mitglieder, key=lambda m: m.spiel["minuten"]).fokus.setFocus()

    def datenblatt(self, k):
        if k.typ == "spiel":
            self.haupt.datenblatt_zeigen(k.spiel)
        else:
            self.starten(k)

    def springen(self, von, taste):
        """Pfeiltasten: naechster Knoten in dieser Richtung."""
        richtung = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0), Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1)}[taste]
        bester, wert = None, None
        for k in self.knoten.values():
            if k is von:
                continue
            dx, dy = k.x - von.x, k.y - von.y
            vor = dx * richtung[0] + dy * richtung[1]
            if vor <= 0:
                continue
            quer = abs(dx * richtung[1]) + abs(dy * richtung[0])
            w = vor + 2 * quer
            if wert is None or w < wert:
                bester, wert = k, w
        if bester is not None and bester.fokus is not None:
            bester.fokus.setFocus(Qt.FocusReason.TabFocusReason)

    # ---- Zeichnen

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.fillRect(self.rect(), QColor(R["netz"]))
        # Punktraster, wandert beim Verschieben und Zoomen mit
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(stil.farbe("#ffffff", 12))
        schritt = max(10.0, 28 * self.zoom)
        y = (self.height() / 2 + 14 + self.versatz.y()) % schritt
        while y < self.height():
            x = (self.width() / 2 + self.versatz.x()) % schritt
            while x < self.width():
                p.drawEllipse(QPointF(x, y), 1, 1)
                x += schritt
            y += schritt
        du = self.bild(0, 0)
        if not self.knoten:
            p.setPen(QColor(R["netz_leise"]))
            p.drawText(QRectF(self.rect()), Qt.AlignmentFlag.AlignCenter, "KEINE KNOTEN IM NETZ")
            p.end()
            return
        fokus = next((k for k in self.knoten.values() if k.fokus is not None and k.fokus.hasFocus()), None)
        nachbarn = self._nachbarn(fokus)
        # Leitungen
        for k in self.knoten.values():
            b = self.bild(k.x, k.y)
            if k.typ in ("spiel", "labor"):
                hell = k is fokus
                p.setPen(QPen(QColor(R["orange"] if hell else R["netz_linie"]), 1.6 if hell else 1.1))
                p.drawLine(du, b)
            if k.typ in ("art", "labor"):
                for m in k.mitglieder:
                    an = fokus is not None and (fokus is k or fokus is m)
                    p.setPen(QPen(QColor("#6b7fa8" if an else "#2c3a52"), 1.3 if an else 1.0, Qt.PenStyle.DashLine))
                    p.drawLine(b, self.bild(m.x, m.y))
        # Datenpakete
        for kennung, t, _tempo, an in self.pakete:
            k = self.knoten[kennung]
            b = self.bild(k.x, k.y)
            pos = QPointF(du.x() + (b.x() - du.x()) * t, du.y() + (b.y() - du.y()) * t)
            farbe = QColor(R["orange"] if an else "#7aa2f7")
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(stil.farbe(farbe.name(), 60))
            p.drawEllipse(pos, 4.5 if an else 3.5, 4.5 if an else 3.5)
            p.setBrush(farbe)
            p.drawEllipse(pos, 2 if an else 1.6, 2 if an else 1.6)
        # DU mit leichtem Puls
        puls = 1 + 0.06 * math.sin(self.zeit * 2.2)
        p.setPen(QPen(stil.farbe(R["orange"], 70), 6))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(du, 30 * self.zoom * puls, 30 * self.zoom * puls)
        p.setPen(QPen(QColor(R["orange"]), 2))
        p.setBrush(QColor(R["netz"]))
        p.drawEllipse(du, 26 * self.zoom, 26 * self.zoom)
        p.setFont(stil.schrift(10, fett=True))
        p.setPen(QColor(R["orange"]))
        p.drawText(QRectF(du.x() - 30, du.y() - 30, 60, 60), Qt.AlignmentFlag.AlignCenter, "DU")
        # Knoten (der gewaehlte zuletzt, damit er oben liegt)
        gesamt = sum(k.spiel["minuten"] for k in self.knoten.values() if k.typ == "spiel") or 1
        for k in sorted(self.knoten.values(), key=lambda k: k is fokus):
            gedimmt = fokus is not None and k is not fokus and k not in nachbarn
            if k.typ == "spiel":
                self._spiel(p, k, k is fokus, gedimmt, gesamt)
            else:
                self._hub(p, k, k is fokus, gedimmt)
        # Legende und Info
        p.setFont(stil.schrift(8.5))
        p.setPen(QColor(R["netz_leise"]))
        p.drawText(QRectF(20, self.height() - 30, self.width() - 40, 22), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   "Nähe zu DU = zuletzt gespielt · Rand = Linux-Ampel · oranger Ring = Anteil deiner Spielzeit · "
                   "Pakete = Verkehr der letzten 2 Wochen · Mausrad zoomt · 0 mittig · G Größe · S Spielarten")
        if fokus is not None:
            self._info(p, fokus)
        p.end()

    def _nachbarn(self, k):
        """Was beim gewaehlten Knoten hell bleibt: seine Spielarten, deren Spiele, Labor und Bibi-Spiele."""
        if k is None:
            return set()
        n = set(k.mitglieder)
        for o in self.knoten.values():
            if k in o.mitglieder:
                n.add(o)
                if k.typ == "spiel":
                    n.update(o.mitglieder)
        return n

    def _spiel(self, p, k, fokus, gedimmt, gesamt):
        s = k.spiel
        a = self.haupt.ampel.get(s["id"], {})
        farbe = QColor(stil.AMPEL_FARBE.get(a.get("ampel"), R["netz_leise"]) if s["installiert"] else R["gelb"])
        if s["installiert"] and a.get("ampel") in (None, "grau"):
            farbe = QColor(R["netz_leise"])
        laeuft = s["id"] in self.haupt.laufend
        m = self.bild(k.x, k.y)
        r = k.r * self.zoom
        p.setOpacity(0.35 if gedimmt else 1.0)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(R["netz_knoten"]))
        p.drawEllipse(m, r, r)
        pm = stil.bild(s["bilder"].get("hero")) or stil.bild(s["bilder"].get("cover"))
        if pm is not None:
            p.save()
            p.setOpacity((0.6 if fokus else 0.32) * (0.35 if gedimmt else 1.0))
            innen = r - 2
            stil.bild_fuellen(p, QRectF(m.x() - innen, m.y() - innen, 2 * innen, 2 * innen), pm, innen)
            p.restore()
        p.setPen(QPen(farbe, 3.5 if laeuft and self.haupt.blink else 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(m, r, r)
        # Anteil an der gesamten Spielzeit als Ring
        anteil = s["minuten"] / gesamt
        if anteil > 0.005:
            stift = QPen(QColor(R["orange"]), 2.5)
            stift.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(stift)
            ring = QRectF(m.x() - r - 5, m.y() - r - 5, 2 * r + 10, 2 * r + 10)
            p.drawArc(ring, 90 * 16, -int(360 * 16 * anteil))
        if fokus:
            p.setPen(QPen(QColor("#ffffff"), 1.5, Qt.PenStyle.DotLine))
            p.drawEllipse(m, r + 10, r + 10)
        if laeuft:
            p.setFont(stil.schrift(7.5, fett=True))
            p.setPen(QColor(R["orange"]))
            p.drawText(QRectF(m.x() - 60, m.y() - r - 24, 120, 14), Qt.AlignmentFlag.AlignHCenter, "IN BETRIEB")
        p.setFont(stil.schrift(8.5, fett=fokus))
        p.setPen(QColor(R["text"] if fokus else R["leise"]))
        name = s["name"] if len(s["name"]) <= 22 else s["name"][:20] + "…"
        p.drawText(QRectF(m.x() - 100, m.y() + r + 8, 200, 18), Qt.AlignmentFlag.AlignHCenter, name)
        p.setOpacity(1.0)

    def _hub(self, p, k, fokus, gedimmt):
        """Sechseck fuer Spielart, Labor und Bibi-Spiele."""
        m = self.bild(k.x, k.y)
        r = k.r * self.zoom
        farbe = QColor("#7aa2f7") if k.typ == "art" else QColor(R["gruen"])
        p.setOpacity(0.35 if gedimmt else 1.0)
        punkte = QPolygonF([QPointF(m.x() + r * math.cos(math.radians(60 * i + 30)), m.y() + r * math.sin(math.radians(60 * i + 30)))
                            for i in range(6)])
        p.setPen(QPen(farbe, 2.2 if fokus else 1.4))
        p.setBrush(QColor("#0f2418" if k.typ == "bibi" else R["netz_knoten"]))
        p.drawPolygon(punkte)
        if k.typ == "bibi":
            pm = stil.bild(str(k.spiel["ordner"]) + "/vorschau.png")
            if pm is not None:
                p.save()
                p.setOpacity((0.55 if fokus else 0.35) * (0.35 if gedimmt else 1.0))
                stil.bild_fuellen(p, QRectF(m.x() - r * 0.7, m.y() - r * 0.7, r * 1.4, r * 1.4), pm, r * 0.7)
                p.restore()
        if fokus:
            p.setPen(QPen(QColor("#ffffff"), 1.5, Qt.PenStyle.DotLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(m, r + 8, r + 8)
        p.setFont(stil.schrift(8 if k.typ == "art" else 8.5, fett=fokus or k.typ == "labor"))
        if k.typ == "labor":
            p.setPen(farbe)
            p.drawText(QRectF(m.x() - r, m.y() - r, 2 * r, 2 * r), Qt.AlignmentFlag.AlignCenter, "LAB")
            p.drawText(QRectF(m.x() - 80, m.y() + r + 6, 160, 16), Qt.AlignmentFlag.AlignHCenter, "LABOR")
        elif k.typ == "art":
            p.setPen(farbe)
            p.drawText(QRectF(m.x() - 100, m.y() + r + 6, 200, 16), Qt.AlignmentFlag.AlignHCenter, k.name.upper())
        else:
            p.setPen(QColor(R["text"] if fokus else R["leise"]))
            p.drawText(QRectF(m.x() - 100, m.y() + r + 6, 200, 16), Qt.AlignmentFlag.AlignHCenter, k.name)
        p.setOpacity(1.0)

    def _info(self, p, k):
        """Infokasten oben rechts zum gewaehlten Knoten."""
        zeilen, balken = [], None
        if k.typ == "spiel":
            s = k.spiel
            a = self.haupt.ampel.get(s["id"], {})
            gesamt = sum(x.spiel["minuten"] for x in self.knoten.values() if x.typ == "spiel") or 1
            arten = [o.name for o in self.knoten.values() if o.typ == "art" and k in o.mitglieder]
            verwandt = sorted({m.spiel["name"] for o in self.knoten.values() if o.typ == "art" and k in o.mitglieder
                               for m in o.mitglieder if m is not k})
            ampel_farbe = stil.AMPEL_FARBE.get(a.get("ampel")) if a.get("ampel") not in (None, "grau") else R["text"]
            zeilen = [(s["name"], R["orange"]),
                      (f"{stil.stunden_lang(s['minuten'])} gesamt · {round(100 * s['minuten'] / gesamt)} % deiner Zeit", R["text"]),
                      (f"letzte 2 Wochen {stil.stunden_lang(s['zwei_wochen'])} · zuletzt {stil.wann(s['zuletzt'])}", R["text"]),
                      ("Linux: " + (a.get("grund") or "wird geprüft"), ampel_farbe),
                      ("Spielart: " + (", ".join(arten) or "–"), R["text"])]
            if verwandt:
                zeilen.append(("verwandt: " + ", ".join(verwandt[:3]) + (" …" if len(verwandt) > 3 else ""), R["leise"]))
            balken = steam.wochen(self.haupt.verlauf, s["id"])
            zeilen.append(("A starten · X datenblatt · E einladen", R["dunkel"]))
        elif k.typ == "art":
            spiele = sorted(k.mitglieder, key=lambda m: -m.spiel["minuten"])
            zeit = sum(m.spiel["minuten"] for m in spiele)
            zeilen = [(f"Spielart: {k.name}", "#7aa2f7"), (f"{len(spiele)} Spiele · {stil.stunden_lang(zeit)} zusammen", R["text"])]
            zeilen += [(f"· {m.spiel['name']}", R["leise"]) for m in spiele[:5]]
            zeilen.append(("A springt zum meistgespielten", R["dunkel"]))
        elif k.typ == "labor":
            zeilen = [("LABOR", R["gruen"]), (f"{len(k.mitglieder)} Bibi-Spiele auf dem Prüfstand", R["text"]),
                      ("A öffnet das Labor", R["dunkel"])]
        elif k.typ == "bibi":
            zeilen = [(k.spiel["name"], R["gruen"]), (k.spiel.get("kurz", ""), R["leise"]),
                      (self.haupt.labor.bestwert_text(k.spiel["kennung"]), R["orange"]), ("A starten", R["dunkel"])]
        p.setFont(stil.schrift(9))
        fm = p.fontMetrics()
        b = min(max(fm.horizontalAdvance(z) for z, _ in zeilen) + 26, 430)
        zh = fm.height() + 3
        h = len(zeilen) * zh + 18 + (64 if balken else 0)
        r = QRectF(self.width() - b - 20, 56, b, h)
        p.setPen(QPen(QColor(R["rahmen"]), 1))
        p.setBrush(stil.farbe(R["flaeche"], 235))
        p.drawRoundedRect(r, 4, 4)
        y = r.top() + 9
        for text, farbe in zeilen:
            p.setPen(QColor(farbe))
            p.drawText(QRectF(r.left() + 13, y, b - 26, fm.height()), Qt.AlignmentFlag.AlignLeft,
                       fm.elidedText(text, Qt.TextElideMode.ElideRight, int(b - 26)))
            y += zh
        if balken:
            # Wochenbalken (sammelt die Arcade selbst, Steam kennt nur Gesamtzeiten)
            bereich = QRectF(r.left() + 13, y + 6, b - 26, 40)
            p.setPen(QPen(QColor(R["rand"]), 1))
            p.drawLine(bereich.bottomLeft(), bereich.bottomRight())
            hoechst = max([w for w in balken if w] + [60])
            breite = bereich.width() / len(balken)
            for i, w in enumerate(balken):
                x = bereich.left() + i * breite + breite * 0.2
                if w is None:
                    p.setPen(QPen(QColor(R["rand"]), 1, Qt.PenStyle.DashLine))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawRect(QRectF(x, bereich.bottom() - 6, breite * 0.6, 6))
                else:
                    hh = max(2.0, bereich.height() * w / hoechst)
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QColor(R["orange"] if i == len(balken) - 1 else "#7aa2f7"))
                    p.drawRect(QRectF(x, bereich.bottom() - hh, breite * 0.6, hh))
            p.setFont(stil.schrift(7.5))
            p.setPen(QColor(R["dunkel"]))
            p.drawText(QRectF(bereich.left(), bereich.bottom() + 2, bereich.width(), 14), Qt.AlignmentFlag.AlignLeft,
                       "SPIELZEIT JE WOCHE · 8 WOCHEN")
