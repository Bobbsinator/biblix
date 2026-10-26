"""Biblix Design – Seite „Hintergründe“.

Oben die Monitore (jeder bekommt sein eigenes Bild) und die Diashow, darunter Filter und die Galerie
nach Gruppen, rechts das gewählte Motiv im Detail. Eigene Bilder und ganze Ordner kommen dazu.
Geändert wird nur die Einstellung; angewendet wird wie überall erst mit „Übernehmen“.
"""
import math
from pathlib import Path

from PyQt6.QtCore import Qt, QRect, QRectF, QPoint, QPointF, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QPen, QFont, QPolygonF, QGuiApplication
from PyQt6.QtWidgets import (QLayout, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QScrollArea, QFrame,
                             QGridLayout, QButtonGroup, QCheckBox, QSpinBox, QComboBox, QFileDialog, QSizePolicy)

from biblix_design import kern, hintergruende

KW, KH = 236, 133          # Kachelbild (16:9)
NAMENSZEILE = 30
ZIELE = {"haupt": "Hauptmonitor", "zweiter": "Weitere Monitore", "beide": "Alle Monitore"}
BILDFILTER = "Bilder (*.png *.jpg *.jpeg *.webp *.bmp *.svg)"


def schrift(groesse, fett=False, mono=False):
    f = QFont("DejaVu Sans Mono" if mono else "DejaVu Sans")
    f.setPixelSize(int(groesse))
    f.setBold(fett)
    return f


def sechseck(cx, cy, r):
    return QPolygonF([QPointF(cx + r * math.cos(math.radians(60 * i - 90)), cy + r * math.sin(math.radians(60 * i - 90)))
                      for i in range(6)])


def gruppen():
    """(id, Name, Farbpunkt) in Galerie-Reihenfolge."""
    liste = [("standorte", "Standorte", "#ffd400"), ("allgemein", "Biblix", None)]
    liste += [(pr["id"], pr["name"], pr["dunkel"]["akzent"]) for pr in kern.presets()]
    liste.append(("eigene", "Eigene Bilder", None))
    return liste


def motive(e):
    """Alle Motive als Dicts: id, name, gruppe, lebendig, neu, text."""
    liste = []
    for szene, name, gruppe, _ in hintergruende.LEBENDIG:
        liste.append(dict(id=hintergruende.LEBENDIG_PREFIX + szene, name=name, gruppe=gruppe, lebendig=True,
                          neu=szene in hintergruende.LEBENDIG_NEU,
                          text=(hintergruende.LEBENDIG_TEXT.get(szene, "Animiert.") + " Pausiert bei Spielen und maximierten Fenstern.")))
    for mid, name, gruppe in hintergruende.alle():
        st = hintergruende.standort(mid)
        liste.append(dict(id=mid, name=name, gruppe=gruppe, lebendig=False, neu=bool(st),
                          text=st[4] if st else ""))
    for mid in e.get("eigene_bilder", []):
        pfad = hintergruende.eigen_pfad(mid)
        ordner = str(mid).startswith(hintergruende.EIGEN_ORDNER)
        liste.append(dict(id=mid, name=(pfad.name or str(pfad)) if pfad else mid, gruppe="eigene", lebendig=False,
                          neu=False, ordner=ordner,
                          text=("Ordner: die Bilder darin laufen als Diashow. " if ordner else "") + str(pfad)))
    return liste


class Fluss(QLayout):
    """Reihe, die bei Platzmangel in die naechste Zeile umbricht (fuer die Filterknoepfe)."""
    def __init__(self, abstand=6):
        super().__init__()
        self.teile, self.abstand = [], abstand

    def addItem(self, item):
        self.teile.append(item)

    def count(self):
        return len(self.teile)

    def itemAt(self, i):
        return self.teile[i] if 0 <= i < len(self.teile) else None

    def takeAt(self, i):
        return self.teile.pop(i) if 0 <= i < len(self.teile) else None

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, breite):
        return self._anordnen(QRect(0, 0, breite, 0), nur_messen=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._anordnen(rect)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        s = QSize()
        for item in self.teile:
            s = s.expandedTo(item.minimumSize())
        return s

    def _anordnen(self, rect, nur_messen=False):
        x, y, zeile = rect.x(), rect.y(), 0
        for item in self.teile:
            h = item.sizeHint()
            if x + h.width() > rect.right() and zeile > 0:
                x, y, zeile = rect.x(), y + zeile + self.abstand, 0
            if not nur_messen:
                item.setGeometry(QRect(QPoint(x, y), h))
            x += h.width() + self.abstand
            zeile = max(zeile, h.height())
        return y + zeile - rect.y()


class Kachel(QWidget):
    """Ein Motiv: Bild, Abzeichen, beim Drüberfahren Knöpfe zum direkten Zuweisen."""
    gewaehlt = pyqtSignal(str)
    zuweisen = pyqtSignal(str, str)

    def __init__(self, seite, info):
        super().__init__()
        self.seite, self.info, self.mid = seite, info, info["id"]
        self.ueber = False
        self.knoepfe = {}
        self.setFixedSize(KW, KH + NAMENSZEILE)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(info["name"])

    def enterEvent(self, ev):
        self.ueber = True
        self.update()

    def leaveEvent(self, ev):
        self.ueber = False
        self.update()

    def mousePressEvent(self, ev):
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        for ziel, r in self.knoepfe.items():
            if r.contains(ev.position()):
                self.zuweisen.emit(self.mid, ziel)
                return
        self.gewaehlt.emit(self.mid)

    def mouseDoubleClickEvent(self, ev):
        self.zuweisen.emit(self.mid, self.seite.ziel)

    def paintEvent(self, ev):
        p, e = self.seite.f.p, self.seite.f.e
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        bild_r = QRectF(1, 1, KW - 2, KH - 2)
        pfad = QPainterPath()
        pfad.addRoundedRect(bild_r, 10, 10)
        qp.setClipPath(pfad)
        pm = self.seite.f.vorschauen.holen(self.mid, p, e.get("hintergrund_eigene_farben", False))
        if pm and not pm.isNull():
            ziel = pm.scaled(QSize(KW, KH), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                             Qt.TransformationMode.SmoothTransformation)
            qp.drawPixmap(int((KW - ziel.width()) / 2), int((KH - ziel.height()) / 2), ziel)
        else:
            qp.fillRect(bild_r, QColor(p["karte"]))
            qp.setPen(QColor(p["leise"]))
            qp.setFont(schrift(12))
            qp.drawText(bild_r, Qt.AlignmentFlag.AlignCenter, "lädt …" if not self.info.get("ordner") else "Ordner")
        self.knoepfe = {}
        if self.ueber:
            qp.fillRect(bild_r, QColor(0, 0, 0, 140))
            ziele = ["haupt", "zweiter", "beide"] if self.seite.mehrere else ["haupt"]
            namen = {"haupt": "Haupt", "zweiter": "Weitere", "beide": "Alle"} if self.seite.mehrere else {"haupt": "Setzen"}
            qp.setFont(schrift(12, True))
            x = 10
            for z in ziele:
                b = qp.fontMetrics().horizontalAdvance(namen[z]) + 22
                r = QRectF(x, KH - 38, b, 28)
                self.knoepfe[z] = r
                qp.setPen(Qt.PenStyle.NoPen)
                qp.setBrush(QColor(p["akzent"]) if z == self.seite.ziel else QColor(20, 24, 32, 230))
                qp.drawRoundedRect(r, 14, 14)
                qp.setPen(QColor("#ffffff"))
                qp.drawText(r, Qt.AlignmentFlag.AlignCenter, namen[z])
                x += b + 6
        qp.setClipping(False)
        fokus = self.mid == self.seite.fokus
        qp.setPen(QPen(QColor(p["akzent"] if fokus else p["rand"]), 3 if fokus else 1))
        qp.setBrush(Qt.BrushStyle.NoBrush)
        qp.drawRoundedRect(bild_r, 10, 10)
        # Abzeichen oben links
        x = 8
        for text, hinter, vorder in ((("NEU", "#ffd400", "#111111"),) if self.info["neu"] else ()) + \
                ((("▶ LEBENDIG", "#0b0f16", "#ffd400"),) if self.info["lebendig"] else ()) + \
                ((("ORDNER", "#0b0f16", "#ffffff"),) if self.info.get("ordner") else ()):
            qp.setFont(schrift(11, True, True))
            b = qp.fontMetrics().horizontalAdvance(text) + 16
            qp.setPen(Qt.PenStyle.NoPen)
            qp.setBrush(QColor(hinter))
            qp.drawRoundedRect(QRectF(x, 8, b, 22), 11, 11)
            qp.setPen(QColor(vorder))
            qp.drawText(QRectF(x, 8, b, 22), Qt.AlignmentFlag.AlignCenter, text)
            x += b + 4
        # Wo laeuft das Motiv gerade?
        haupt = e["hintergrund"]
        zweiter = e.get("hintergrund_zweiter") or haupt
        marke = []
        if self.mid == haupt:
            marke.append("HAUPT" if self.seite.mehrere else "AKTIV")
        if self.seite.mehrere and self.mid == zweiter:
            marke.append("WEITERE")
        if marke and not self.ueber:
            text = " + ".join(marke)
            qp.setFont(schrift(10, True, True))
            b = qp.fontMetrics().horizontalAdvance(text) + 16
            r = QRectF(KW - b - 8, KH - 30, b, 22)
            qp.setPen(Qt.PenStyle.NoPen)
            qp.setBrush(QColor(p["akzent"]))
            qp.drawRoundedRect(r, 11, 11)
            qp.setPen(QColor(p["auf_akzent"]))
            qp.drawText(r, Qt.AlignmentFlag.AlignCenter, text)
        if fokus:
            qp.setPen(QPen(QColor("#0b0d12"), 2))
            qp.setBrush(QColor(p["akzent"]))
            qp.drawPolygon(sechseck(KW - 22, 22, 14))
            qp.setPen(QPen(QColor("#ffffff"), 3, cap=Qt.PenCapStyle.RoundCap))
            qp.drawPolyline(QPolygonF([QPointF(KW - 29, 22), QPointF(KW - 24, 27), QPointF(KW - 15, 17)]))
        # Name
        qp.setPen(QColor(p["akzent"] if fokus else p["text"]))
        qp.setFont(schrift(13, fokus))
        name = qp.fontMetrics().elidedText(self.info["name"], Qt.TextElideMode.ElideRight, KW - 6)
        qp.drawText(QRectF(3, KH + 4, KW - 6, NAMENSZEILE - 6), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name)
        qp.end()


class Hinzufuegen(QWidget):
    """Gestrichelte Kachel: Bild hinzufügen bzw. Ordner verbinden."""
    def __init__(self, seite, titel, unter, aktion):
        super().__init__()
        self.seite, self.titel, self.unter, self.aktion = seite, titel, unter, aktion
        self.setFixedSize(KW, KH + NAMENSZEILE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, ev):
        self.aktion()

    def paintEvent(self, ev):
        p = self.seite.f.p
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(2, 2, KW - 4, KH - 4)
        qp.setPen(QPen(QColor(p["leise"]), 2, Qt.PenStyle.DashLine))
        qp.setBrush(QColor(p["flaeche"]))
        qp.drawRoundedRect(r, 10, 10)
        qp.setPen(QPen(QColor(p["akzent"]), 3))
        qp.setBrush(Qt.BrushStyle.NoBrush)
        qp.drawPolygon(sechseck(KW / 2, 48, 22))
        qp.drawLine(QPointF(KW / 2, 38), QPointF(KW / 2, 58))
        qp.drawLine(QPointF(KW / 2 - 10, 48), QPointF(KW / 2 + 10, 48))
        qp.setPen(QColor(p["text"]))
        qp.setFont(schrift(13, True))
        qp.drawText(QRectF(0, 80, KW, 22), Qt.AlignmentFlag.AlignCenter, self.titel)
        qp.setPen(QColor(p["leise"]))
        qp.setFont(schrift(11))
        qp.drawText(QRectF(0, 102, KW, 20), Qt.AlignmentFlag.AlignCenter, self.unter)
        qp.end()


class Monitor(QWidget):
    """Ein Monitor in der Leiste oben: Bildschirm mit aktuellem Motiv. Klick = Ziel für die Auswahl."""
    geklickt = pyqtSignal(str)

    def __init__(self, seite, slot, titel, unter):
        super().__init__()
        self.seite, self.slot, self.titel, self.unter = seite, slot, titel, unter
        self.setFixedSize(430, 150)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, ev):
        self.geklickt.emit(self.slot)

    def paintEvent(self, ev):
        p, e = self.seite.f.p, self.seite.f.e
        mid = e["hintergrund"] if self.slot == "haupt" else (e.get("hintergrund_zweiter") or e["hintergrund"])
        aktiv = self.seite.ziel in (self.slot, "beide")
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(6, 6, 200, 112.5)
        qp.setPen(QPen(QColor(p["akzent"] if aktiv else p["rand"]), 4 if aktiv else 2))
        qp.setBrush(QColor("#0a0d12"))
        qp.drawRoundedRect(r.adjusted(-4, -4, 4, 4), 10, 10)
        pm = self.seite.f.vorschauen.holen(mid, p, e.get("hintergrund_eigene_farben", False))
        if pm and not pm.isNull():
            pfad = QPainterPath()
            pfad.addRoundedRect(r, 6, 6)
            qp.setClipPath(pfad)
            ziel = pm.scaled(QSize(200, 113), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            qp.drawPixmap(int(r.x() + (200 - ziel.width()) / 2), int(r.y() + (113 - ziel.height()) / 2), ziel)
            qp.setClipping(False)
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QColor(p["rand"]))
        qp.drawPolygon(QPolygonF([QPointF(90, 124), QPointF(122, 124), QPointF(130, 142), QPointF(82, 142)]))
        qp.setPen(QColor(p["text"]))
        qp.setFont(schrift(17, True))
        qp.drawText(QRectF(228, 14, 200, 26), Qt.AlignmentFlag.AlignLeft, self.titel)
        qp.setPen(QColor(p["leise"]))
        qp.setFont(schrift(12))
        qp.drawText(QRectF(228, 42, 200, 20), Qt.AlignmentFlag.AlignLeft, self.unter)
        info = next((m for m in self.seite.alle if m["id"] == mid), None)
        qp.setPen(QColor(p["akzent"]))
        qp.setFont(schrift(13, True))
        name = qp.fontMetrics().elidedText(info["name"] if info else mid, Qt.TextElideMode.ElideRight, 196)
        qp.drawText(QRectF(228, 74, 200, 22), Qt.AlignmentFlag.AlignLeft, name)
        if aktiv:
            qp.setPen(QColor(p["leise"]))
            qp.setFont(schrift(11))
            qp.drawText(QRectF(228, 100, 200, 20), Qt.AlignmentFlag.AlignLeft, "Auswahl landet hier")
        qp.end()


class Bild(QWidget):
    """Grosse Vorschau im Detailbereich."""
    def __init__(self, seite):
        super().__init__()
        self.seite = seite
        self.setFixedSize(368, 207)

    def paintEvent(self, ev):
        p, e = self.seite.f.p, self.seite.f.e
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(1, 1, self.width() - 2, self.height() - 2)
        pfad = QPainterPath()
        pfad.addRoundedRect(r, 10, 10)
        qp.setClipPath(pfad)
        pm = self.seite.f.vorschauen.holen(self.seite.fokus, p, e.get("hintergrund_eigene_farben", False))
        if pm and not pm.isNull():
            ziel = pm.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            qp.drawPixmap(int((self.width() - ziel.width()) / 2), int((self.height() - ziel.height()) / 2), ziel)
        else:
            qp.fillRect(r, QColor(p["karte"]))
        qp.setClipping(False)
        qp.setPen(QPen(QColor(p["rand"]), 1))
        qp.drawRoundedRect(r, 10, 10)
        qp.end()


class GalerieSeite(QWidget):
    def __init__(self, fenster):
        super().__init__()
        self.f = fenster
        self.ziel = "haupt"
        self.fokus = fenster.e["hintergrund"]
        self.art = "alle"
        self.gruppe = "alle"
        self.kacheln = []
        self.alle = motive(fenster.e)
        bildschirme = QGuiApplication.screens()
        self.mehrere = len(bildschirme) > 1

        aussen = QHBoxLayout(self)
        aussen.setContentsMargins(14, 14, 14, 14)
        aussen.setSpacing(14)
        links = QVBoxLayout()
        links.setSpacing(10)
        aussen.addLayout(links, 1)

        # Monitore und Diashow
        leiste = QFrame()
        leiste.setObjectName("feld")
        lh = QHBoxLayout(leiste)
        lh.setContentsMargins(16, 12, 16, 12)
        lh.setSpacing(12)
        haupt = QGuiApplication.primaryScreen()
        self.monitore = []
        g = haupt.size() if haupt else None
        m1 = Monitor(self, "haupt", "Hauptmonitor", f"{g.width()}×{g.height()}" if g else "")
        self.monitore.append(m1)
        lh.addWidget(m1)
        if self.mehrere:
            andere = [s for s in bildschirme if s is not haupt]
            gr = andere[0].size()
            m2 = Monitor(self, "zweiter", "Weitere Monitore", f"{gr.width()}×{gr.height()}" + (f" · {len(andere)} Stück" if len(andere) > 1 else ""))
            self.monitore.append(m2)
            lh.addWidget(m2)
        for m in self.monitore:
            m.geklickt.connect(self.ziel_setzen)
        spalte = QVBoxLayout()
        spalte.setSpacing(6)
        if self.mehrere:
            self.gleich = QCheckBox("Alle Monitore gleich")
            self.gleich.toggled.connect(self._gleich)
            spalte.addWidget(self.gleich)
        spalte.addStretch(1)
        lh.addLayout(spalte)
        lh.addStretch(1)
        trenn = QFrame()
        trenn.setFixedWidth(1)
        trenn.setObjectName("trenner")
        lh.addWidget(trenn)
        dia = QGridLayout()
        dia.setHorizontalSpacing(10)
        dia.setVerticalSpacing(6)
        self.diashow = QCheckBox("Diashow")
        self.diashow.setObjectName("fett")
        self.diashow.toggled.connect(lambda an: self._setzen("diashow", an))
        dia.addWidget(self.diashow, 0, 0, 1, 2)
        self.dia_gruppe = QComboBox()
        self.dia_gruppe.addItem("Gruppe des Hauptbildes", "auto")
        for gid, name, _ in gruppen():
            self.dia_gruppe.addItem(name, gid)
        self.dia_gruppe.currentIndexChanged.connect(lambda _i: self._setzen("diashow_gruppe", self.dia_gruppe.currentData()))
        dia.addWidget(self.dia_gruppe, 1, 0, 1, 2)
        self.dia_minuten = QSpinBox()
        self.dia_minuten.setRange(1, 600)
        self.dia_minuten.setSuffix(" Min.")
        self.dia_minuten.setPrefix("alle ")
        self.dia_minuten.valueChanged.connect(lambda v: self._setzen("diashow_minuten", v))
        dia.addWidget(self.dia_minuten, 2, 0)
        self.dia_nur_haupt = QCheckBox("nur Hauptmonitor")
        self.dia_nur_haupt.toggled.connect(lambda an: self._setzen("diashow_monitore", "haupt" if an else "beide"))
        dia.addWidget(self.dia_nur_haupt, 2, 1)
        if not self.mehrere:
            self.dia_nur_haupt.hide()
        lh.addLayout(dia)
        links.addWidget(leiste)

        # Filter
        filt = Fluss(6)
        self.art_gruppe = QButtonGroup(self)
        for wert, name in (("alle", "Alle"), ("lebendig", "Lebendig"), ("still", "Still")):
            b = QPushButton(name)
            b.setObjectName("chip")
            b.setCheckable(True)
            b.setChecked(wert == self.art)
            b.setMinimumWidth(b.fontMetrics().horizontalAdvance(name) + 44)
            b.clicked.connect(lambda _=False, w=wert: self._filter("art", w))
            self.art_gruppe.addButton(b)
            filt.addWidget(b)
        trenn2 = QFrame()
        trenn2.setFixedSize(14, 10)
        filt.addWidget(trenn2)
        self.gruppen_knoepfe = QButtonGroup(self)
        for gid, name, farbe in [("alle", "Alle Gruppen", None)] + gruppen():
            b = QPushButton(name)
            b.setObjectName("chip")
            b.setCheckable(True)
            b.setChecked(gid == self.gruppe)
            b.setMinimumWidth(b.fontMetrics().horizontalAdvance(name) + 56)
            b.clicked.connect(lambda _=False, w=gid: self._filter("gruppe", w))
            self.gruppen_knoepfe.addButton(b)
            filt.addWidget(b)
        filter_feld = QWidget()
        filter_feld.setLayout(filt)
        links.addWidget(filter_feld)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        links.addWidget(self.scroll, 1)

        # Detail rechts
        detail = QFrame()
        detail.setObjectName("feld")
        detail.setFixedWidth(400)
        dv = QVBoxLayout(detail)
        dv.setContentsMargins(16, 16, 16, 16)
        dv.setSpacing(10)
        self.bild = Bild(self)
        dv.addWidget(self.bild)
        self.d_name = QLabel()
        self.d_name.setObjectName("titel")
        self.d_name.setWordWrap(True)
        dv.addWidget(self.d_name)
        self.d_text = QLabel()
        self.d_text.setObjectName("leise")
        self.d_text.setWordWrap(True)
        dv.addWidget(self.d_text)
        self.d_ziel_titel = QLabel("ZEIGEN AUF")
        self.d_ziel_titel.setObjectName("klein")
        dv.addWidget(self.d_ziel_titel)
        zr = QHBoxLayout()
        zr.setSpacing(6)
        self.d_ziele = {}
        for z in (["haupt", "zweiter", "beide"] if self.mehrere else ["haupt"]):
            b = QPushButton({"haupt": "Hauptmonitor", "zweiter": "Weitere", "beide": "Alle"}[z] if self.mehrere else "Als Hintergrund")
            b.setObjectName("chip")
            b.setCheckable(True)
            b.setMinimumWidth(b.fontMetrics().horizontalAdvance(b.text()) + 44)
            b.clicked.connect(lambda _=False, z=z: self.zuweisen(self.fokus, z))
            self.d_ziele[z] = b
            zr.addWidget(b)
        zr.addStretch(1)
        dv.addLayout(zr)
        self.d_farben_titel = QLabel("FARBEN")
        self.d_farben_titel.setObjectName("klein")
        dv.addWidget(self.d_farben_titel)
        fr = QHBoxLayout()
        fr.setSpacing(6)
        self.d_firma = QPushButton("Firmenfarben")
        self.d_eigen = QPushButton("Meine Farben")
        for b, wert in ((self.d_firma, False), (self.d_eigen, True)):
            b.setObjectName("chip")
            b.setCheckable(True)
            b.setMinimumWidth(b.fontMetrics().horizontalAdvance(b.text()) + 44)
            b.clicked.connect(lambda _=False, w=wert: self._setzen("hintergrund_eigene_farben", w))
            fr.addWidget(b)
        fr.addStretch(1)
        dv.addLayout(fr)
        self.d_farben_hinweis = QLabel()
        self.d_farben_hinweis.setObjectName("leise")
        self.d_farben_hinweis.setWordWrap(True)
        dv.addWidget(self.d_farben_hinweis)
        self.d_entfernen = QPushButton("Aus der Liste entfernen")
        self.d_entfernen.clicked.connect(lambda: self.entfernen(self.fokus))
        dv.addWidget(self.d_entfernen)
        dv.addStretch(1)
        tipp = QLabel("Tipp: Doppelklick auf ein Motiv setzt es auf den markierten Monitor. "
                      "Der Sperrbildschirm zeigt das Bild vom Hauptmonitor.")
        tipp.setObjectName("leise")
        tipp.setWordWrap(True)
        dv.addWidget(tipp)
        aussen.addWidget(detail)

        self.aufbauen()
        self.aktualisieren()

    # ------------------------------------------------------------ Aufbau der Galerie
    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        QTimer.singleShot(0, self._spalten_pruefen)

    def showEvent(self, ev):
        super().showEvent(ev)
        QTimer.singleShot(0, self._spalten_pruefen)

    def _spalten_pruefen(self):
        if self._spalten() != getattr(self, "_letzte_spalten", None):
            self.aufbauen()
            self.aktualisieren()

    def _spalten(self):
        return max(2, (self.scroll.viewport().width() - 10) // (KW + 14))

    def aufbauen(self):
        self.alle = motive(self.f.e)
        self._letzte_spalten = spalten = self._spalten()
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 4, 4, 16)
        v.setSpacing(8)
        self.kacheln = []
        reihenfolge = gruppen()
        preset = self.f.e["preset"]
        reihenfolge.sort(key=lambda g: (g[0] != preset, g[0] == "eigene"))
        for gid, name, farbe in reihenfolge:
            if self.gruppe not in ("alle", gid):
                continue
            liste = [m for m in self.alle if m["gruppe"] == gid]
            if self.art == "lebendig":
                liste = [m for m in liste if m["lebendig"]]
            elif self.art == "still":
                liste = [m for m in liste if not m["lebendig"]]
            if not liste and gid != "eigene":
                continue
            if gid == "eigene" and self.art == "lebendig":
                continue
            kopf = QLabel(f"<b>{name.upper()}</b>&nbsp;&nbsp;<span style='font-weight:normal'>"
                          f"{len(liste)} {'Motiv' if len(liste) == 1 else 'Motive'}"
                          f"{' · folgt deinem Preset' if gid == preset else ''}</span>")
            kopf.setObjectName("abschnitt")
            v.addWidget(kopf)
            gitter = QGridLayout()
            gitter.setHorizontalSpacing(14)
            gitter.setVerticalSpacing(10)
            elemente = []
            for m in liste:
                k = Kachel(self, m)
                k.gewaehlt.connect(self.waehlen)
                k.zuweisen.connect(self.zuweisen)
                self.kacheln.append(k)
                elemente.append(k)
            if gid == "eigene":
                elemente.append(Hinzufuegen(self, "Bild hinzufügen …", "ein oder mehrere Bilder", self.bilder_hinzufuegen))
                elemente.append(Hinzufuegen(self, "Ordner verbinden …", "neue Bilder kommen von selbst", self.ordner_verbinden))
            for i, el in enumerate(elemente):
                gitter.addWidget(el, i // spalten, i % spalten)
            gitter.setColumnStretch(spalten, 1)
            v.addLayout(gitter)
            v.addSpacing(10)
        v.addStretch(1)
        self.scroll.setWidget(w)

    # ------------------------------------------------------------ Zustand
    def aktualisieren(self):
        """Nach jeder Aenderung der Einstellungen (ohne die Galerie neu aufzubauen)."""
        e = self.f.e
        for k in self.kacheln:
            k.update()
        for m in self.monitore:
            m.update()
        if self.mehrere:
            self.gleich.blockSignals(True)
            self.gleich.setChecked(not e.get("hintergrund_zweiter"))
            self.gleich.blockSignals(False)
        for w, wert in ((self.diashow, e["diashow"]), (self.dia_nur_haupt, e.get("diashow_monitore") == "haupt")):
            w.blockSignals(True)
            w.setChecked(bool(wert))
            w.blockSignals(False)
        self.dia_minuten.blockSignals(True)
        self.dia_minuten.setValue(int(e.get("diashow_minuten", 30)))
        self.dia_minuten.blockSignals(False)
        self.dia_gruppe.blockSignals(True)
        i = self.dia_gruppe.findData(e.get("diashow_gruppe", "auto"))
        self.dia_gruppe.setCurrentIndex(max(0, i))
        self.dia_gruppe.blockSignals(False)
        for w in (self.dia_gruppe, self.dia_minuten, self.dia_nur_haupt):
            w.setEnabled(bool(e["diashow"]))
        self._detail()

    def _detail(self):
        e = self.f.e
        info = next((m for m in self.alle if m["id"] == self.fokus), None)
        if not info:
            self.fokus = e["hintergrund"]
            info = next((m for m in self.alle if m["id"] == self.fokus), None) or dict(id=self.fokus, name=self.fokus,
                                                                                        gruppe="", lebendig=False, neu=False, text="")
        self.bild.update()
        self.d_name.setText(info["name"] + ("  <span style='color:#111;background:#ffd400'>&nbsp;NEU&nbsp;</span>" if info["neu"] else ""))
        gname = dict((g, n) for g, n, _ in gruppen()).get(info["gruppe"], "")
        self.d_text.setText(" · ".join(x for x in (gname, info["text"]) if x))
        haupt = e["hintergrund"]
        zweiter = e.get("hintergrund_zweiter") or haupt
        an = {"haupt": self.fokus == haupt, "zweiter": self.fokus == zweiter,
              "beide": self.fokus == haupt and not e.get("hintergrund_zweiter")}
        if self.mehrere and an["beide"]:
            an["haupt"] = an["zweiter"] = False
        for z, b in self.d_ziele.items():
            b.setChecked(an[z])
        firma = info["gruppe"] in [pr["id"] for pr in kern.presets()] and not info["lebendig"]
        for w in (self.d_farben_titel, self.d_firma, self.d_eigen):
            w.setVisible(firma)
        self.d_firma.setChecked(not e.get("hintergrund_eigene_farben"))
        self.d_eigen.setChecked(bool(e.get("hintergrund_eigene_farben")))
        if info["gruppe"] == "standorte":
            self.d_farben_hinweis.setText("Feste Farben im Stil des Ortes. Zeigt nur, was im Kanon steht.")
        elif firma:
            self.d_farben_hinweis.setText("Gilt für alle Firmenmotive.")
        else:
            self.d_farben_hinweis.setText("")
        self.d_farben_hinweis.setVisible(bool(self.d_farben_hinweis.text()))
        self.d_entfernen.setVisible(info["gruppe"] == "eigene")

    def _setzen(self, schluessel, wert):
        self.f.e[schluessel] = wert
        self.f.geaendert()

    def ziel_setzen(self, slot):
        self.ziel = slot
        if self.mehrere and slot != "beide" and not self.f.e.get("hintergrund_zweiter"):
            pass  # erst beim Zuweisen werden die Monitore getrennt
        self.aktualisieren()

    def _gleich(self, an):
        if an:
            self.f.e["hintergrund_zweiter"] = None
            self.ziel = "beide"
        else:
            self.f.e["hintergrund_zweiter"] = self.f.e["hintergrund"]
            self.ziel = "haupt"
        self.f.geaendert()

    def _filter(self, art, wert):
        setattr(self, art, wert)
        self.aufbauen()
        self.aktualisieren()

    def waehlen(self, mid):
        self.fokus = mid
        self.aktualisieren()

    def zuweisen(self, mid, ziel):
        e = self.f.e
        self.fokus = mid
        if ziel == "beide" or not self.mehrere:
            e["hintergrund"] = mid
            e["hintergrund_zweiter"] = None
        elif ziel == "haupt":
            if not e.get("hintergrund_zweiter"):
                e["hintergrund_zweiter"] = e["hintergrund"]   # die anderen behalten ihr Bild
            e["hintergrund"] = mid
        else:
            e["hintergrund_zweiter"] = mid
        if e.get("hintergrund_zweiter") == e["hintergrund"]:
            e["hintergrund_zweiter"] = None
        self.ziel = ziel if self.mehrere else "haupt"
        self.f.geaendert()

    # ------------------------------------------------------------ Eigene Bilder
    def bilder_hinzufuegen(self):
        dateien, _ = QFileDialog.getOpenFileNames(self, "Bilder hinzufügen", str(Path.home() / "Bilder"), BILDFILTER)
        if dateien:
            self._eigene_dazu([hintergruende.EIGEN_DATEI + d for d in dateien])

    def ordner_verbinden(self):
        ordner = QFileDialog.getExistingDirectory(self, "Ordner verbinden", str(Path.home() / "Bilder"))
        if ordner:
            self._eigene_dazu([hintergruende.EIGEN_ORDNER + ordner])

    def _eigene_dazu(self, neue):
        liste = list(self.f.e.get("eigene_bilder", []))
        liste += [m for m in neue if m not in liste]
        self.f.e["eigene_bilder"] = liste
        self.aufbauen()
        self.zuweisen(neue[0], self.ziel)

    def entfernen(self, mid):
        e = self.f.e
        e["eigene_bilder"] = [m for m in e.get("eigene_bilder", []) if m != mid]
        if e["hintergrund"] == mid:
            e["hintergrund"] = kern.STANDARD["hintergrund"]
        if e.get("hintergrund_zweiter") == mid:
            e["hintergrund_zweiter"] = None
        self.fokus = e["hintergrund"]
        self.aufbauen()
        self.f.geaendert()
