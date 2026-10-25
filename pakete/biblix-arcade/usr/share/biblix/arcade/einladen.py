"""Freunde zum Spielen einladen: Vorlage waehlen, Zeit, Freunde – dann Steam-Chat, WhatsApp oder Karte.

Abgeschickt wird nie automatisch: die Arcade oeffnet den richtigen Chat und legt die Einladung in die
Zwischenablage, der Nutzer drueckt selbst Strg+V und Enter. Die Einladungskarte (Bild im Datenblatt-Stil)
laesst sich kopieren oder speichern und funktioniert so auch ausserhalb von Steam.
"""
import shutil
import threading
import time
from pathlib import Path

from PyQt6.QtCore import QObject, QPointF, QRectF, Qt, QTime, pyqtSignal
from PyQt6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QTextEdit, QTimeEdit, QVBoxLayout,
    QWidget,
)

import steam
import stil
from stil import B, R, knopf, label

VERLAUF = stil.DATEN / "einladungen.json"
WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

# kennung, Knopf, Stempel auf der Karte, braucht Uhrzeit, Text
VORLAGEN = [
    ("heute", "Heute Zeit?", "ANFRAGE", True,
     "{anrede}, hast du {tag} Zeit für {spiel}? Ich wäre so ab {zeit} am Start. 🎮"),
    ("termin", "Fester Termin", "EINSATZBEFEHL", True,
     "🎮 Einsatzbefehl: {spiel} · {tag} um {zeit} · Treffpunkt Steam. Bist du dabei? ✅ / ❌"),
    ("jetzt", "Jetzt sofort", "SOFORT", False,
     "{anrede}! Ich bin gerade in {spiel} – spring rein! 🚀"),
    ("wann", "Wann passt's?", "TERMINSUCHE", False,
     "{anrede}, Lust auf {spiel} diese Woche? Sag mir, wann es dir passt. 📅"),
    ("wochenende", "Wochenende", "WOCHENENDE", False,
     "{anrede}, am Wochenende eine Runde {spiel}? Samstag oder Sonntag – du entscheidest. 🗓️"),
    ("neu", "Neues Spiel", "NEUZUGANG", False,
     "{anrede}, ich hab {spiel}{art} – läuft bei mir unter Linux {linux}. Probierst du's mit mir?"),
    ("revanche", "Revanche", "REVANCHE", False,
     "{anrede}, Revanche in {spiel}? Ich hab trainiert. 😏"),
    ("eigen", "Eigener Text", "EINLADUNG", False, ""),
]
VORLAGE = {v[0]: v for v in VORLAGEN}
# Mehrere Freunde: "ihr" statt "du"
GRUPPE = {
    "heute": "{anrede}, habt ihr {tag} Zeit für {spiel}? Ich wäre so ab {zeit} am Start. 🎮",
    "termin": "🎮 Einsatzbefehl: {spiel} · {tag} um {zeit} · Treffpunkt Steam. Seid ihr dabei? ✅ / ❌",
    "jetzt": "{anrede}! Ich bin gerade in {spiel} – springt rein! 🚀",
    "wann": "{anrede}, Lust auf {spiel} diese Woche? Sagt mir, wann es euch passt. 📅",
    "wochenende": "{anrede}, am Wochenende eine Runde {spiel}? Samstag oder Sonntag – ihr entscheidet. 🗓️",
    "neu": "{anrede}, ich hab {spiel}{art} – läuft bei mir unter Linux {linux}. Probiert ihr's mit mir?",
    "revanche": "{anrede}, Revanche in {spiel}? Ich hab trainiert. 😏",
}


def tage():
    """[(Anzeige, Text in der Nachricht)] fuer heute und die naechsten 6 Tage."""
    liste = [("heute", "heute"), ("morgen", "morgen")]
    for n in range(2, 7):
        t = time.localtime(time.time() + n * 86400)
        name = WOCHENTAGE[t.tm_wday]
        liste.append((f"{name}, {t.tm_mday}.{t.tm_mon}.", f"am {name}"))
    return liste


class Bildlader(QObject):
    """Profilbilder im Hintergrund holen (Steam-Bildserver), damit das Fenster sofort aufgeht."""
    fertig = pyqtSignal(str, str)

    def holen(self, freunde, online):
        def arbeit():
            for f in freunde:
                p = steam.avatar(f["avatar"], online)
                if p:
                    try:
                        self.fertig.emit(f["id"], p)
                    except RuntimeError:
                        return  # Fenster ist schon zu
        threading.Thread(target=arbeit, daemon=True).start()


class FreundKachel(QWidget):
    umgeschaltet = pyqtSignal()

    def __init__(self, freund, an=False):
        super().__init__()
        self.freund, self.an, self.hover = freund, an, False
        self.bild = None
        self.setFixedSize(150, 54)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(freund["name"])

    def bild_setzen(self, pfad):
        self.bild = stil.bild(pfad)
        self.update()

    def umschalten(self):
        self.an = not self.an
        self.update()
        self.umgeschaltet.emit()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.umschalten()

    def keyPressEvent(self, ev):
        if ev.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.umschalten()
        else:
            super().keyPressEvent(ev)

    def enterEvent(self, _):
        self.hover = True
        self.update()

    def leaveEvent(self, _):
        self.hover = False
        self.update()

    def focusInEvent(self, ev):
        super().focusInEvent(ev)
        self.update()

    def focusOutEvent(self, ev):
        super().focusOutEvent(ev)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        rand = R["orange"] if self.hasFocus() else (R["gruen"] if self.an else (R["rahmen"] if self.hover else R["rand"]))
        p.setPen(QPen(QColor(rand), 2 if (self.hasFocus() or self.an) else 1))
        p.setBrush(QColor(R["einschub_an"] if self.an else R["einschub"]))
        p.drawRoundedRect(r, 4, 4)
        kreis = QRectF(r.left() + 8, r.center().y() - 17, 34, 34)
        if self.bild is not None:
            stil.bild_fuellen(p, kreis, self.bild, 17)
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(R["rahmen"]))
            p.drawEllipse(kreis)
            p.setPen(QColor(R["text"]))
            p.drawText(kreis, Qt.AlignmentFlag.AlignCenter, self.freund["name"][:1].upper())
        p.setFont(stil.schrift(9.5, fett=self.an))
        p.setPen(QColor("#ffffff" if self.an else R["text"]))
        breite = r.width() - 62
        p.drawText(QRectF(kreis.right() + 8, r.top(), breite, r.height()), Qt.AlignmentFlag.AlignVCenter,
                   p.fontMetrics().elidedText(self.freund["name"], Qt.TextElideMode.ElideRight, int(breite)))
        if self.an:
            stil.led(p, QPointF(r.right() - 9, r.top() + 9), R["gruen"], True, 3.5)
        p.end()


# ---------------------------------------------------------------- Einladungskarte

def karte(spiel, haupt, vorlage, wann, an, von):
    """Einladung als Bild (1200 x 630, passt in Messenger-Vorschauen), im Datenblatt-Stil."""
    from datenblatt import DatenblattSeite
    w, h = 1200, 630
    bild = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
    bild.setDotsPerMeterX(3780)  # 96 dpi: Schriftgroessen wie auf dem Bildschirm
    bild.setDotsPerMeterY(3780)
    p = QPainter(bild)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    p.fillRect(bild.rect(), QColor(B["grund"]))
    stil.gitter(p, QRectF(0, 0, w, h), 20, stil.farbe("#ffffff", 14))
    stil.gitter(p, QRectF(0, 0, w, h), 100, stil.farbe("#ffffff", 26))
    linie = QColor(B["linie"])
    p.setPen(QPen(linie, 2))
    p.drawRect(QRectF(16, 16, w - 32, h - 32))
    # Cover
    cover = QRectF(48, 48, 330, 495)
    pm = stil.bild(spiel["bilder"].get("cover"))
    if pm is not None:
        stil.bild_fuellen(p, cover, pm)
    else:
        hero = stil.bild(spiel["bilder"].get("hero")) or stil.bild(spiel["bilder"].get("banner"))
        stil.bild_fuellen(p, cover, hero)
        logo = stil.bild(spiel["bilder"].get("logo"))
        if logo is not None:
            lw = cover.width() * 0.85
            lh = lw * logo.height() / max(1, logo.width())
            p.drawPixmap(QRectF(cover.center().x() - lw / 2, cover.center().y() - lh / 2, lw, lh), logo, QRectF(logo.rect()))
    p.setPen(QPen(linie, 2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRect(cover)
    DatenblattSeite._mass(p, linie, QPointF(cover.left(), cover.bottom() + 22), QPointF(cover.right(), cover.bottom() + 22), "600")
    # Text rechts
    x, y, breite = 420, 56, w - 420 - 60
    p.setFont(stil.schrift(11))
    p.setPen(linie)
    p.drawText(QRectF(x, y, breite, 24), Qt.AlignmentFlag.AlignLeft, f"BIBI ARCADE · EINLADUNG · TEIL-NR. {spiel['id']}")
    y += 40
    p.setFont(stil.schrift(34, mono=False, fett=True))
    p.setPen(QColor("#ffffff"))
    titel_r = p.boundingRect(QRectF(x, y, breite - 40, 200), Qt.TextFlag.TextWordWrap, spiel["name"])
    p.drawText(titel_r, Qt.TextFlag.TextWordWrap, spiel["name"])
    y = titel_r.bottom() + 26
    a = haupt.ampel.get(spiel["id"], {})
    linux = steam.TIER_TEXT.get(a.get("tier")) or ("nur Windows" if a.get("ampel") == "rot" else "ungeprüft")
    zeilen = [("WANN", wann), ("WO", "Steam"), ("LINUX", linux)]
    if von:
        zeilen.append(("VON", von))
    if an:
        zeilen.append(("AN", an))
    p.setFont(stil.schrift(15))
    zh = 40
    for k, v in zeilen:
        p.setPen(linie)
        p.drawText(QRectF(x, y, 120, zh), Qt.AlignmentFlag.AlignVCenter, k)
        p.setPen(QColor(B["gruen"] if k == "LINUX" and a.get("ampel") == "gruen" else B["text"]))
        p.drawText(QRectF(x + 130, y, breite - 130, zh), Qt.AlignmentFlag.AlignVCenter,
                   p.fontMetrics().elidedText(v, Qt.TextElideMode.ElideRight, int(breite - 130)))
        hell = QColor(linie)
        hell.setAlpha(90)
        p.setPen(QPen(hell, 1))
        p.drawLine(QPointF(x, y + zh), QPointF(x + breite, y + zh))
        y += zh
    # Stempel
    stempel = VORLAGE[vorlage][2]
    p.save()
    p.translate(w - 210, h - 175)
    p.scale(1.7, 1.7)  # Stempel fuer die grosse Karte
    DatenblattSeite._stempel(p, QPointF(0, 0), stempel, "BITTE ANTWORTEN", B["gelb"])
    p.restore()
    # Schriftfeld
    sf = QRectF(420, h - 82, w - 420 - 32, 40)
    p.setPen(QPen(linie, 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)  # die Masslinie hat einen Fuellpinsel hinterlassen
    p.drawRect(sf)
    p.setFont(stil.schrift(10))
    teile = ["GEZ. BIBI TECH", time.strftime("%d.%m.%Y"), f"STEAM-APP {spiel['id']}"]
    fb = sf.width() / len(teile)
    for i, t in enumerate(teile):
        if i:
            p.drawLine(QPointF(sf.left() + i * fb, sf.top()), QPointF(sf.left() + i * fb, sf.bottom()))
        p.drawText(QRectF(sf.left() + i * fb + 10, sf.top(), fb - 16, sf.height()), Qt.AlignmentFlag.AlignVCenter,
                   p.fontMetrics().elidedText(t, Qt.TextElideMode.ElideRight, int(fb - 16)))
    p.end()
    return bild


# ---------------------------------------------------------------- Fenster

class EinladenDialog(QDialog):
    def __init__(self, haupt, spiel):
        super().__init__(haupt)
        self.haupt, self.spiel = haupt, spiel
        self.setWindowTitle(f"Einladen – {spiel['name']}")
        self.setStyleSheet(stil.stil() + f"""
            QDialog {{ background: {R['grund']}; }}
            QTextEdit {{ background: {R['schwarz']}; border: 1px solid {R['rahmen']}; border-radius: 3px; padding: 6px; }}
            QTextEdit:focus {{ border-color: {R['orange']}; }}
            QTimeEdit {{ background: {R['einschub']}; border: 1px solid {R['rahmen']}; border-radius: 3px; padding: 4px 8px; }}
            QTimeEdit:focus {{ border-color: {R['orange']}; }}
            QPushButton#vorlage {{ text-align: left; padding: 7px 12px; }}
            QPushButton#vorlage:checked {{ background: {R['orange']}; color: #2a1600; border-color: {R['orange']}; font-weight: 600; }}
        """)
        self.resize(1180, 820)
        self.merk = stil.json_lesen(VERLAUF, {})
        self.eigen_name, self.freunde = steam.freunde()
        self.vorlage = self.merk.get("vorlage", "heute") if self.merk.get("vorlage") in VORLAGE else "heute"
        self.bearbeitet = False
        self.steam_schritt = 0
        self.kachel = {}

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 14)
        lay.setSpacing(10)
        kopf = label(f"EINLADEN · {stil.kennzeichen(spiel['name'])}")
        kopf.setFont(stil.schrift(13, mono=False, fett=True, abstand=2))
        kopf.setStyleSheet(f"color: {R['orange']};")
        lay.addWidget(kopf)

        mitte = QHBoxLayout()
        mitte.setSpacing(18)
        links = QVBoxLayout()
        links.setSpacing(8)
        # 1) Vorlagen
        links.addWidget(label("1 · VORLAGE", "dunkel"))
        raster = QGridLayout()
        raster.setSpacing(6)
        self.vorlage_knoepfe = {}
        for i, (k, text, _st, _z, _t) in enumerate(VORLAGEN):
            b = knopf(text, "vorlage", lambda _=False, x=k: self._vorlage(x))
            b.setCheckable(True)
            raster.addWidget(b, i // 4, i % 4)
            self.vorlage_knoepfe[k] = b
        links.addLayout(raster)
        # 2) Zeit
        self.zeit_titel = label("2 · WANN", "dunkel")
        links.addWidget(self.zeit_titel)
        zeit = QHBoxLayout()
        self.tag = QComboBox()
        for anzeige, text in tage():
            self.tag.addItem(anzeige, text)
        self.tag.currentIndexChanged.connect(self._neu)
        zeit.addWidget(self.tag)
        self.uhr = QTimeEdit(QTime(20, 0))
        self.uhr.setDisplayFormat("HH:mm")
        self.uhr.timeChanged.connect(self._neu)
        zeit.addWidget(self.uhr)
        for t in ("18:00", "19:00", "20:00", "21:00"):
            b = knopf(t, cb=lambda _=False, x=t: self.uhr.setTime(QTime.fromString(x, "HH:mm")))
            zeit.addWidget(b)
        zeit.addStretch(1)
        self.zeit_zeile = QWidget()
        self.zeit_zeile.setLayout(zeit)
        links.addWidget(self.zeit_zeile)
        # 3) Freunde
        links.addWidget(label(f"3 · WER · {len(self.freunde)} STEAM-FREUNDE (zuletzt eingeladene sind vorgewählt)", "dunkel"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        innen = QWidget()
        fl = QGridLayout(innen)
        fl.setSpacing(6)
        fl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        zuletzt = self.merk.get("zuletzt", [])
        reihenfolge = sorted(self.freunde, key=lambda f: (f["id"] not in zuletzt, f["name"].lower()))
        for i, f in enumerate(reihenfolge):
            k = FreundKachel(f, f["id"] in zuletzt)
            k.umgeschaltet.connect(self._freunde_neu)
            fl.addWidget(k, i // 4, i % 4)
            self.kachel[f["id"]] = k
        if not self.freunde:
            fl.addWidget(label("Keine Steam-Freunde gefunden. WhatsApp und die Karte gehen trotzdem.", "leise", wrap=True), 0, 0)
        scroll.setWidget(innen)
        scroll.setMinimumHeight(140)
        links.addWidget(scroll, 1)
        # 4) Text
        zeile = QHBoxLayout()
        zeile.addWidget(label("4 · NACHRICHT", "dunkel"))
        zeile.addStretch(1)
        self.link = QCheckBox("Shop-Link anhängen")
        self.link.setChecked(self.merk.get("link", True))
        self.link.toggled.connect(self._neu)
        zeile.addWidget(self.link)
        self.zuruecksetzen = knopf("Text zurücksetzen", cb=self._zuruecksetzen)
        self.zuruecksetzen.hide()
        zeile.addWidget(self.zuruecksetzen)
        links.addLayout(zeile)
        self.text = QTextEdit()
        self.text.setAcceptRichText(False)
        self.text.setFixedHeight(96)
        self.text.textChanged.connect(self._getippt)
        links.addWidget(self.text)
        mitte.addLayout(links, 3)

        rechts = QVBoxLayout()
        rechts.addWidget(label("EINLADUNGSKARTE", "dunkel"))
        self.vorschau = QLabel()
        self.vorschau.setFixedSize(440, 231)
        self.vorschau.setStyleSheet(f"border: 1px solid {R['rahmen']};")
        rechts.addWidget(self.vorschau)
        rechts.addWidget(knopf("KARTE KOPIEREN", cb=self.karte_kopieren))
        rechts.addWidget(knopf("KARTE SPEICHERN", cb=self.karte_speichern))
        rechts.addStretch(1)
        mitte.addLayout(rechts, 2)
        lay.addLayout(mitte, 1)

        # Abschicken
        unten = QHBoxLayout()
        unten.setSpacing(10)
        self.steam_knopf = knopf("", "los", self.steam_naechster)
        unten.addWidget(self.steam_knopf)
        self.wa_knopf = knopf("WHATSAPP", cb=self.whatsapp)
        unten.addWidget(self.wa_knopf)
        unten.addWidget(knopf("TEXT KOPIEREN", cb=lambda: self._kopieren(self._text(), "Text kopiert")))
        unten.addStretch(1)
        unten.addWidget(knopf("FERTIG", cb=lambda: (self._merken(), self.accept())))
        lay.addLayout(unten)
        self.hinweis = label("Abgeschickt wird nichts automatisch: Chat geht auf, Einladung ist kopiert – dort Strg+V und Enter.",
                             "leise", wrap=True)
        lay.addWidget(self.hinweis)

        self.lader = Bildlader()
        self.lader.fertig.connect(lambda fid, pfad: fid in self.kachel and self.kachel[fid].bild_setzen(pfad))
        self.lader.holen(self.freunde, haupt.einst["online"])
        self._vorlage(self.vorlage)
        self.vorlage_knoepfe[self.vorlage].setFocus()

    # ---- Inhalt

    def gewaehlt(self):
        return [k.freund for k in self.kachel.values() if k.an]

    def _wann(self):
        if VORLAGE[self.vorlage][0] == "jetzt":
            return "jetzt sofort"
        if not VORLAGE[self.vorlage][3]:
            return {"wann": "diese Woche, wann es passt", "wochenende": "am Wochenende"}.get(self.vorlage, "bald")
        return f"{self.tag.currentData()} · {self.uhr.time().toString('HH:mm')} Uhr"

    def _text(self, freund=None):
        """Nachricht; mit freund persoenlich ("Hey Max"), sonst fuer alle ("Hey Leute")."""
        if self.bearbeitet or self.vorlage == "eigen":
            t = self.text.toPlainText().strip()
            if freund is not None:
                t = t.replace("Hey Leute", f"Hey {freund['name']}")
            return t
        gewaehlt = self.gewaehlt()
        gruppe = False
        if freund is not None:
            anrede = f"Hey {freund['name']}"
        elif len(gewaehlt) == 1:
            anrede = f"Hey {gewaehlt[0]['name']}"
        else:
            anrede, gruppe = "Hey Leute", True
        a = self.haupt.ampel.get(self.spiel["id"], {})
        arten = [g for g in self.haupt.genres.get(self.spiel["id"], []) if g not in ("Early Access", "Indie")]
        vorlage = GRUPPE.get(self.vorlage, VORLAGE[self.vorlage][4]) if gruppe else VORLAGE[self.vorlage][4]
        t = vorlage.format(
            anrede=anrede, spiel=self.spiel["name"], tag=self.tag.currentData(),
            zeit=self.uhr.time().toString("HH:mm") + " Uhr",
            linux=(steam.TIER_TEXT.get(a.get("tier")) or "ohne Probleme").replace("Platin", "Platin ✓"),
            art=f" ({', '.join(arten[:2])})" if arten else "")
        if self.link.isChecked():
            t += "\n" + steam.shop_link(self.spiel)
        return t

    def _vorlage(self, k):
        self.vorlage = k
        for x, b in self.vorlage_knoepfe.items():
            b.setChecked(x == k)
        zeit = VORLAGE[k][3]
        self.zeit_zeile.setVisible(zeit)
        self.zeit_titel.setVisible(zeit)
        self.bearbeitet = False
        self.zuruecksetzen.hide()
        if k == "eigen":
            self.text.blockSignals(True)
            self.text.setPlainText(self.merk.get("eigen", f"Hey Leute, {self.spiel['name']}? "))
            self.text.blockSignals(False)
            self._karte()
        else:
            self._neu()

    def _freunde_neu(self):
        self.steam_schritt = 0
        self._neu()

    def _neu(self):
        if not self.bearbeitet and self.vorlage != "eigen":
            self.text.blockSignals(True)
            self.text.setPlainText(self._text())
            self.text.blockSignals(False)
        self._karte()
        self._steam_knopf()

    def _getippt(self):
        if self.vorlage != "eigen":
            self.bearbeitet = True
            self.zuruecksetzen.show()

    def _zuruecksetzen(self):
        self.bearbeitet = False
        self.zuruecksetzen.hide()
        self._neu()

    def _an_text(self):
        g = [f["name"] for f in self.gewaehlt()]
        if len(g) > 3:
            return ", ".join(g[:3]) + f" + {len(g) - 3}"
        return ", ".join(g)

    def _karte(self):
        self.bild = karte(self.spiel, self.haupt, self.vorlage, self._wann(), self._an_text(), self.eigen_name)
        self.vorschau.setPixmap(QPixmap.fromImage(self.bild).scaled(
            self.vorschau.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    # ---- Abschicken

    def _steam_knopf(self):
        g = self.gewaehlt()
        if not g:
            self.steam_knopf.setText("STEAM: ERST FREUNDE WÄHLEN")
            self.steam_knopf.setEnabled(False)
        elif self.steam_schritt >= len(g):
            self.steam_knopf.setText(f"STEAM: ALLE {len(g)} EINGELADEN ✓")
            self.steam_knopf.setEnabled(True)
        else:
            f = g[self.steam_schritt]
            nr = f" ({self.steam_schritt + 1}/{len(g)})" if len(g) > 1 else ""
            self.steam_knopf.setText(f"▶  STEAM-CHAT MIT {f['name'].upper()}{nr}")
            self.steam_knopf.setEnabled(True)

    def steam_naechster(self):
        """Pro Klick ein Freund: persoenliche Einladung kopieren, Chatfenster oeffnen."""
        g = self.gewaehlt()
        if not g:
            return
        if self.steam_schritt >= len(g):
            self.steam_schritt = 0
        f = g[self.steam_schritt]
        self._kopieren(self._text(f), f"Kopiert – im Chat mit {f['name']} Strg+V und Enter.")
        stil.starten(steam.chat_befehl(f))
        self.steam_schritt += 1
        self._merken()
        self.haupt.protokoll.schreiben(f"einladung: {stil.kennzeichen(self.spiel['name']).lower()} → {f['name']} (steam)", R["blau"])
        self._steam_knopf()

    def whatsapp(self):
        self._kopieren(self._text(), "Kopiert – in WhatsApp den Chat wählen, Strg+V und Enter. Für die Karte: „Karte kopieren“.")
        if shutil.which("flatpak") and stil.starten(["flatpak", "run", "com.rtosta.zapzap"]):
            pass
        else:
            stil.starten(["xdg-open", "https://web.whatsapp.com"])
        self._merken()
        self.haupt.protokoll.schreiben(f"einladung: {stil.kennzeichen(self.spiel['name']).lower()} (whatsapp)", R["blau"])

    def karte_kopieren(self):
        QGuiApplication.clipboard().setImage(self.bild)
        self.hinweis.setText("Karte kopiert – im Chat mit Strg+V einfügen.")
        self.haupt.klang.spielen("klick")

    def karte_speichern(self):
        ordner = Path(stil.run_text(["xdg-user-dir", "PICTURES"]) or Path.home() / "Bilder")
        ziel = ordner / f"Bibi-Einladung-{stil.kennzeichen(self.spiel['name']).lower()}-{time.strftime('%Y-%m-%d-%H%M')}.png"
        try:
            ordner.mkdir(parents=True, exist_ok=True)
            ok = self.bild.save(str(ziel), "PNG")
        except OSError:
            ok = False
        self.hinweis.setText(f"Gespeichert: {ziel}" if ok else "Die Karte ließ sich nicht speichern.")

    def _kopieren(self, text, hinweis):
        QGuiApplication.clipboard().setText(text)
        self.hinweis.setText(hinweis)
        self.haupt.klang.spielen("klick")

    def _merken(self):
        self.merk["zuletzt"] = [f["id"] for f in self.gewaehlt()] or self.merk.get("zuletzt", [])
        self.merk["vorlage"] = self.vorlage
        self.merk["link"] = self.link.isChecked()
        if self.vorlage == "eigen":
            self.merk["eigen"] = self.text.toPlainText()
        stil.json_schreiben(VERLAUF, self.merk)
