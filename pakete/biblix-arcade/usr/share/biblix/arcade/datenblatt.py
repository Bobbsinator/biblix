"""Datenblatt eines Spiels: Blaupause mit Masslinien, Pruefstempel, Wochenbalken und Schriftfeld.

Drei Faelle: freigegeben (blau), nur Windows (rot, Anti-Cheat), Wartung (gelb, Steam laedt noch).
Beim Oeffnen zeichnet ein "Plotter" die Linien und Balken auf.
"""
import time
from pathlib import Path

from PyQt6.QtCore import QEasingCurve, QPointF, QRectF, Qt, QVariantAnimation
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QHBoxLayout, QWidget

import steam
import stil
from stil import B, knopf

KNOPF_STIL = f"""
QPushButton {{ background: transparent; color: {B['linie']}; border: 1.5px solid {B['linie']}; border-radius: 0;
               padding: 7px 14px; font-family: "{{mono}}"; }}
QPushButton:hover, QPushButton:focus {{ color: #ffffff; border-color: #ffffff; }}
QPushButton#los {{ background: {B['gelb']}; color: #3a2a00; border-color: {B['gelb']}; font-weight: 600; }}
QPushButton#los:hover, QPushButton#los:focus {{ background: #ffe08f; border-color: #ffffff; }}
QPushButton#windows {{ background: {B['blau']}; color: #04162b; border-color: {B['blau']}; font-weight: 600; }}
QPushButton#windows:focus {{ border-color: #ffffff; }}
QPushButton#notaus {{ background: #ff4d4d; color: #2b0505; border: 2px solid #ff8080; font-weight: 700; }}
QPushButton#notaus:hover, QPushButton#notaus:focus {{ background: #ff7070; border-color: #ffffff; }}
"""


class DatenblattSeite(QWidget):
    def __init__(self, haupt):
        super().__init__()
        self.haupt = haupt
        self.spiel = None
        self.plot = 1.0
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(900)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._plot)
        self.knoepfe = QWidget(self)
        self.kl = QHBoxLayout(self.knoepfe)
        self.kl.setContentsMargins(0, 0, 0, 0)
        self.kl.setSpacing(10)
        self.knoepfe.setStyleSheet(KNOPF_STIL.replace("{mono}", stil.MONO))
        self.geo = {}

    def _plot(self, v):
        self.plot = v
        self.update()

    def fall(self):
        s = self.spiel
        if not s["installiert"]:
            return "wartung"
        if self.haupt.ampel.get(s["id"], {}).get("ampel") == "rot":
            return "windows"
        return "frei"

    def zeigen(self, spiel):
        self.spiel = spiel
        haupt_knopf = self._knoepfe()
        self.anim.stop()
        self.plot = 0.0
        self.anim.start()
        haupt_knopf.setFocus(Qt.FocusReason.OtherFocusReason)

    def knoepfe_neu(self):
        """Spiel startet oder endet, waehrend das Datenblatt offen ist: nur die Knoepfe neu."""
        if self.spiel is not None:
            fokus = self.focusWidget()
            neu = self._knoepfe()
            if fokus is None or not fokus.isVisible():
                neu.setFocus(Qt.FocusReason.OtherFocusReason)
            self.update()

    def _knoepfe(self):
        spiel = self.spiel
        while self.kl.count():
            w = self.kl.takeAt(0).widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        h = self.haupt
        fall = self.fall()
        if fall == "windows":
            haupt_knopf = knopf("⟳  IN WINDOWS STARTEN", "windows", h.in_windows)
            self.kl.addWidget(haupt_knopf)
            self.kl.addWidget(knopf("TROTZDEM STARTEN", cb=lambda: self._trotzdem(spiel)))
        elif fall == "wartung":
            haupt_knopf = knopf("STEAM-SEITE ÖFFNEN", "los", lambda: stil.starten(steam.steam_seite_befehl(spiel)))
            self.kl.addWidget(haupt_knopf)
        else:
            haupt_knopf = knopf("▶  IN BETRIEB NEHMEN", "los", lambda: h.spiel_starten(spiel))
            self.kl.addWidget(haupt_knopf)
            self.kl.addWidget(knopf("STEAM-SEITE", cb=lambda: stil.starten(steam.steam_seite_befehl(spiel))))
        if Path(spiel["ordner"]).is_dir():
            self.kl.addWidget(knopf("ORDNER", cb=lambda: stil.starten(["xdg-open", spiel["ordner"]])))
        if fall != "wartung":
            self.kl.addWidget(knopf("📨 EINLADEN", cb=lambda: h.einladen(spiel)))
        self.kl.addWidget(knopf("ZURÜCK", cb=h.zurueck))
        if spiel["id"] in h.laufend:
            self.kl.addWidget(knopf("⏻  NOT-AUS", "notaus", lambda: h.not_aus(spiel)))
        for i in range(self.kl.count()):
            self.kl.itemAt(i).widget().show()  # sonst zaehlt das Layout sie bei sichtbarer Seite noch nicht mit
        self._anordnen()
        return haupt_knopf

    def _trotzdem(self, spiel):
        self.haupt.klang.spielen("start")
        self.haupt.protokoll.schreiben(f"{stil.kennzeichen(spiel['name']).lower()}: start trotz sperre", stil.R["gelb"])
        stil.starten(steam.starten_befehl(spiel))

    # ---- Aufteilung

    def _anordnen(self):
        w, h = self.width(), self.height()
        rand = 28
        schriftfeld_h = 34
        innen = QRectF(rand, rand, w - 2 * rand, h - 2 * rand - schriftfeld_h - 12)
        cover_h = min(innen.height() - 40, max(240.0, innen.height() * 0.72))
        cover_w = min(cover_h * 2 / 3, innen.width() * 0.3)
        cover_h = cover_w * 1.5
        cover = QRectF(innen.left() + 10, innen.top() + 10, cover_w, cover_h)
        rechts = QRectF(cover.right() + 40, innen.top(), innen.right() - cover.right() - 50, innen.height())
        self.kl.activate()
        groesse = self.kl.sizeHint()  # Knoepfe werden bei jedem Spiel neu gebaut: Groesse aus dem Layout
        kh = groesse.height()
        self.knoepfe.setGeometry(int(rechts.left()), int(rechts.bottom() - kh), int(min(rechts.width(), groesse.width())), kh)
        self.knoepfe.show()
        schriftfeld = QRectF(rand, h - rand - schriftfeld_h, w - 2 * rand, schriftfeld_h)
        self.geo = {"innen": innen, "cover": cover, "rechts": rechts, "schriftfeld": schriftfeld, "knopf_h": kh}

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if self.spiel is not None:
            self._anordnen()

    def keyPressEvent(self, ev):
        # Pfeiltasten wandern durch die Knoepfe (Tab geht sowieso)
        if ev.key() in (Qt.Key.Key_Left, Qt.Key.Key_Up):
            self.focusNextPrevChild(False)
        elif ev.key() in (Qt.Key.Key_Right, Qt.Key.Key_Down):
            self.focusNextPrevChild(True)
        else:
            super().keyPressEvent(ev)

    # ---- Zeichnen

    def paintEvent(self, _):
        if self.spiel is None or not self.geo:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        s, g, t = self.spiel, self.geo, self.plot
        fall = self.fall()
        a = self.haupt.ampel.get(s["id"], {})
        grund = B["rot_grund"] if fall == "windows" else B["grund"]
        linie = QColor(B["rot"] if fall == "windows" else B["linie"])
        p.fillRect(self.rect(), QColor(grund))
        stil.gitter(p, QRectF(self.rect()), 16, stil.farbe("#ffffff", 14))
        stil.gitter(p, QRectF(self.rect()), 80, stil.farbe("#ffffff", 26))
        # Zeichnungsrahmen
        p.setPen(QPen(linie, 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(QRectF(14, 14, self.width() - 28, self.height() - 28))

        mono = stil.schrift(10)
        mono_klein = stil.schrift(8.5)

        # Cover mit Massangabe
        c = g["cover"]
        p.setPen(QPen(linie, 1.5))
        p.drawRect(c)
        pm = stil.bild(s["bilder"].get("cover"))
        if pm is not None:
            p.setOpacity(t)
            stil.bild_fuellen(p, c.adjusted(4, 4, -4, -4), pm)
            p.setOpacity(1.0)
        else:
            hero = stil.bild(s["bilder"].get("hero")) or stil.bild(s["bilder"].get("banner"))
            p.setOpacity(t * 0.55)
            stil.bild_fuellen(p, c.adjusted(4, 4, -4, -4), hero)
            p.setOpacity(1.0)
            logo = stil.bild(s["bilder"].get("logo"))
            if logo is not None:
                lw = c.width() * 0.85
                lh = lw * logo.height() / max(1, logo.width())
                p.drawPixmap(QRectF(c.center().x() - lw / 2, c.center().y() - lh / 2, lw, lh), logo, QRectF(logo.rect()))
            elif hero is None:
                p.setFont(mono)
                p.setPen(linie)
                p.drawText(c, Qt.AlignmentFlag.AlignCenter, "KEIN BILD")
        self._mass(p, linie, QPointF(c.left(), c.bottom() + 16), QPointF(c.left() + c.width() * t, c.bottom() + 16), "600")
        self._mass(p, linie, QPointF(c.right() + 16, c.top()), QPointF(c.right() + 16, c.top() + c.height() * t), "900", senkrecht=True)

        r = g["rechts"]
        y = r.top() + 4
        p.setFont(mono_klein)
        p.setPen(linie)
        rev = time.strftime("%d.%m.")
        p.drawText(QRectF(r.left(), y, r.width(), 20), Qt.AlignmentFlag.AlignLeft,
                   f"DATENBLATT · TEIL-NR. {s['id']} · REV. {rev}")
        y += 22
        titel = stil.schrift(24, mono=False, fett=True)
        p.setFont(titel)
        p.setPen(QColor(B["rot_text"] if fall == "windows" else B["text"]))
        tr = p.boundingRect(QRectF(r.left(), y, r.width() - 150, 200), Qt.TextFlag.TextWordWrap, s["name"])
        p.drawText(tr, Qt.TextFlag.TextWordWrap, s["name"])
        y = tr.bottom() + 12

        # Wertetabelle
        p.setFont(mono)
        zh = p.fontMetrics().height() + 9
        genres = [x for x in self.haupt.genres.get(s["id"], []) if x != "Early Access"]
        tier = a.get("tier", "")
        if fall == "windows":
            pruefung = ("NICHT FREIGEGEBEN", B["rot"])
        elif not a:
            pruefung = ("wird geprüft …", B["linie"])
        elif tier in steam.TIER_TEXT:
            pruefung = (f"{steam.TIER_TEXT[tier].upper()}" + (f" · {a['berichte']} Berichte" if a.get("berichte") else ""),
                        B["gruen"] if a.get("ampel") == "gruen" else B["gelb"])
        else:
            pruefung = ("noch keine Berichte", B["linie"])
        zeilen = [
            ("Betriebsstunden gesamt", stil.stunden_lang(s["minuten"]), None),
            ("Letzte 2 Wochen", stil.stunden_lang(s["zwei_wochen"]), None),
            ("Zuletzt in Betrieb", stil.wann(s["zuletzt"], kurz=False), None),
            ("Speicherbedarf", stil.gb(s["groesse"]) if s["installiert"] else "wird geladen", None),
            ("Spielart", ", ".join(genres) or "–", None),
            ("Linux-Prüfung", pruefung[0], pruefung[1]),
            ("Anti-Cheat", a.get("anticheat") or ("keiner gemeldet" if a else "–"), B["rot"] if fall == "windows" else None),
        ]
        tab_b = r.width() * 0.85
        for i, (k, v, farbe) in enumerate(zeilen):
            sichtbar = min(1.0, max(0.0, t * len(zeilen) - i))
            if sichtbar <= 0:
                break
            p.setOpacity(sichtbar)
            p.setPen(linie)
            p.drawText(QRectF(r.left(), y, tab_b * 0.45, zh), Qt.AlignmentFlag.AlignVCenter, k)
            p.setPen(QColor(farbe or (B["rot_text"] if fall == "windows" else B["text"])))
            breite = tab_b * 0.55
            p.drawText(QRectF(r.left() + tab_b * 0.45, y, breite, zh), Qt.AlignmentFlag.AlignVCenter,
                       p.fontMetrics().elidedText(v, Qt.TextElideMode.ElideRight, int(breite)))
            hell = QColor(linie)
            hell.setAlpha(80)
            p.setPen(QPen(hell, 1))
            p.drawLine(QPointF(r.left(), y + zh), QPointF(r.left() + tab_b * sichtbar, y + zh))
            y += zh
        p.setOpacity(1.0)

        # Pruefstempel
        stempel = {"frei": ("GEPRÜFT", "LINUX", B["gruen"]), "windows": ("NICHT FREIGEGEBEN", "ANTI-CHEAT SPERRT LINUX", B["rot"]),
                   "wartung": ("WARTUNG", "STEAM LÄDT NOCH", B["gelb"])}[fall]
        if fall == "frei" and a.get("ampel") == "gelb":
            stempel = ("BEDINGT", "MIT MACKEN", B["gelb"])
        elif fall == "frei" and a.get("ampel") in (None, "grau"):
            stempel = ("UNGEPRÜFT", "KEINE BERICHTE", B["linie"])
        if t > 0.6:
            self._stempel(p, QPointF(r.right() - 90, r.top() + 50), *stempel, deckung=min(1.0, (t - 0.6) * 2.5))

        # Hinweis bei Sonderfaellen
        if fall != "frei":
            text = ("Dieses Spiel lässt sich nur unter Windows betreiben. Biblix startet einmal in Windows und kommt beim "
                    "nächsten Start von selbst zurück." if fall == "windows" else
                    "Steam muss das Spiel noch fertig herunterladen oder aktualisieren. Öffne die Steam-Seite, dann geht es weiter.")
            p.setFont(stil.schrift(10.5, mono=False))
            p.setPen(QColor(B["rot_text"] if fall == "windows" else B["text"]))
            hr = QRectF(r.left(), y + 12, r.width() * 0.8, 80)
            p.drawText(hr, Qt.TextFlag.TextWordWrap, text)
            y = hr.top() + p.boundingRect(hr, Qt.TextFlag.TextWordWrap, text).height()

        # Wochenbalken
        diagramm_unten = g["rechts"].bottom() - g["knopf_h"] - 26
        diagramm_oben = max(y + 34, diagramm_unten - 120)
        if diagramm_unten - diagramm_oben > 50:
            self._wochen(p, linie, QRectF(r.left(), diagramm_oben, min(r.width() * 0.7, 460), diagramm_unten - diagramm_oben), t)

        # Schriftfeld
        sf = g["schriftfeld"]
        p.setPen(QPen(linie, 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(sf)
        felder = ["GEZ. BIBI TECH", "GEPR. PROTONDB" if fall != "windows" else "GEPR. AREWEANTICHEATYET",
                  "MASSSTAB 1:1", f"BLATT {self._blatt_nr()}"]
        p.setFont(mono_klein)
        fb = sf.width() / len(felder)
        for i, text in enumerate(felder):
            if i:
                p.drawLine(QPointF(sf.left() + i * fb, sf.top()), QPointF(sf.left() + i * fb, sf.bottom()))
            p.drawText(QRectF(sf.left() + i * fb + 10, sf.top(), fb - 20, sf.height()), Qt.AlignmentFlag.AlignVCenter, text)
        p.end()

    def _blatt_nr(self):
        liste = self.haupt.sichtbar or self.haupt.spiele
        nr = next((i for i, x in enumerate(liste, 1) if x["id"] == self.spiel["id"]), 1)
        return f"{nr}/{max(1, len(liste))}"

    @staticmethod
    def _mass(p, farbe, a, b, text, senkrecht=False):
        """Masslinie mit Pfeilen und Zahl, wie in einer technischen Zeichnung."""
        p.setPen(QPen(farbe, 1))
        p.setBrush(farbe)
        p.drawLine(a, b)
        laenge = (b.y() - a.y()) if senkrecht else (b.x() - a.x())
        if laenge < 20:
            return
        for punkt, richtung in ((a, 1), (b, -1)):
            if senkrecht:
                pfeil = QPolygonF([punkt, QPointF(punkt.x() - 3, punkt.y() + 7 * richtung), QPointF(punkt.x() + 3, punkt.y() + 7 * richtung)])
                p.drawLine(QPointF(punkt.x() - 6, punkt.y()), QPointF(punkt.x() + 6, punkt.y()))
            else:
                pfeil = QPolygonF([punkt, QPointF(punkt.x() + 7 * richtung, punkt.y() - 3), QPointF(punkt.x() + 7 * richtung, punkt.y() + 3)])
                p.drawLine(QPointF(punkt.x(), punkt.y() - 6), QPointF(punkt.x(), punkt.y() + 6))
            p.drawPolygon(pfeil)
        f = stil.schrift(8.5)
        p.setFont(f)
        fm = p.fontMetrics()
        mitte = QPointF((a.x() + b.x()) / 2, (a.y() + b.y()) / 2)
        breite = fm.horizontalAdvance(text) + 10
        p.save()
        p.translate(mitte)
        if senkrecht:
            p.rotate(-90)
        r = QRectF(-breite / 2, -fm.height() / 2, breite, fm.height())
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(B["grund"]))
        p.drawRect(r)
        p.setPen(farbe)
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, text)
        p.restore()

    @staticmethod
    def _stempel(p, mitte, oben, unten, farbe, deckung=1.0):
        p.save()
        p.translate(mitte)
        p.rotate(-9)
        p.setOpacity(deckung * 0.9)
        f1 = stil.schrift(14, mono=False, fett=True, abstand=1.5)
        f2 = stil.schrift(7.5, abstand=1)
        p.setFont(f1)
        b1 = p.fontMetrics().horizontalAdvance(oben)
        p.setFont(f2)
        b2 = p.fontMetrics().horizontalAdvance(unten)
        b = max(b1, b2) + 28
        h = 58
        p.setPen(QPen(QColor(farbe), 3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(-b / 2, -h / 2, b, h), 4, 4)
        p.setPen(QPen(QColor(farbe), 1))
        p.drawRoundedRect(QRectF(-b / 2 + 4, -h / 2 + 4, b - 8, h - 8), 3, 3)
        p.setFont(f1)
        p.drawText(QRectF(-b / 2, -h / 2 + 6, b, h * 0.55), Qt.AlignmentFlag.AlignCenter, oben)
        p.setFont(f2)
        p.drawText(QRectF(-b / 2, 0, b, h / 2 - 6), Qt.AlignmentFlag.AlignCenter, unten)
        p.restore()

    def _wochen(self, p, linie, r, t):
        werte = steam.wochen(self.haupt.verlauf, self.spiel["id"])
        p.setFont(stil.schrift(8.5))
        p.setPen(linie)
        p.drawText(QRectF(r.left(), r.top() - 20, r.width(), 18), Qt.AlignmentFlag.AlignLeft, "BETRIEBSSTUNDEN JE WOCHE")
        p.setPen(QPen(linie, 1))
        p.drawLine(QPointF(r.left(), r.top()), QPointF(r.left(), r.bottom()))
        p.drawLine(QPointF(r.left(), r.bottom()), QPointF(r.right(), r.bottom()))
        hoechst = max([w for w in werte if w] + [60])
        n = len(werte)
        breite = (r.width() - 16) / n
        bekannt = False
        for i, w in enumerate(werte):
            x = r.left() + 10 + i * breite
            if w is None:
                # noch nicht gesammelt: gestrichelter Platzhalter
                p.setPen(QPen(stil.farbe(B["linie"], 85), 1, Qt.PenStyle.DashLine))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRect(QRectF(x, r.bottom() - 10, breite * 0.6, 10))
                continue
            bekannt = True
            h = (r.height() - 8) * (w / hoechst) * t
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(B["gelb"] if i == n - 1 else B["linie"]))
            p.drawRect(QRectF(x, r.bottom() - h, breite * 0.6, h))
        if not bekannt:
            p.setPen(QColor(B["linie"]))
            p.setFont(stil.schrift(8.5))
            p.drawText(r.adjusted(14, 0, 0, -14), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                       "Wird ab heute gesammelt – Steam merkt sich nur die Gesamtzeit.")
