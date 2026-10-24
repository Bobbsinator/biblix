#!/usr/bin/env python3
"""Biblix Design – der Konfigurator.

Dein Desktop in der Mitte, Leuchtpunkte auf jedem Teil. Klick auf ein Teil öffnet rechts genau
eine Auswahl. Unten die Lackfarben-Leiste. Übernehmen wendet alles an (Rückgängig jederzeit).
"""
import copy
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/usr/share/biblix/design/lib")

from PyQt6.QtCore import (Qt, QRectF, QPointF, QTimer, QThread, pyqtSignal, QObject, QRunnable,
                          QThreadPool, QSize)
from PyQt6.QtGui import (QPainter, QColor, QPainterPath, QPixmap, QFont, QPen, QBrush, QIcon,
                         QLinearGradient, QPolygonF)
from PyQt6.QtWidgets import (QApplication, QWidget, QMainWindow, QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QScrollArea, QFrame, QGridLayout, QButtonGroup, QCheckBox,
                             QSpinBox, QColorDialog, QInputDialog, QMessageBox, QStackedWidget,
                             QSizePolicy, QToolButton, QProgressBar, QListWidget, QListWidgetItem)

from biblix_design import kern, hintergruende, anwenden, grafik

CACHE = Path.home() / ".cache" / "biblix-design"
VORSCHAU = CACHE / "vorschau"


def qfarbe(h, alpha=255):
    c = QColor(h)
    c.setAlpha(alpha)
    return c


# ====================================================================== Hintergrund-Vorschaubilder

class VorschauSignal(QObject):
    fertig = pyqtSignal(str, str)


class VorschauAuftrag(QRunnable):
    def __init__(self, mid, p, signal):
        super().__init__()
        self.mid, self.p, self.signal = mid, p, signal

    def run(self):
        try:
            svg = hintergruende.svg(self.mid, self.p)
            kennung = hashlib.sha1(svg.encode()).hexdigest()[:10]
            VORSCHAU.mkdir(parents=True, exist_ok=True)
            png = VORSCHAU / f"{self.mid}-{kennung}.png"
            if not png.exists():
                quelle = VORSCHAU / f".{self.mid}-{kennung}.svg"
                quelle.write_text(svg, encoding="utf-8")
                subprocess.run(["rsvg-convert", "-w", "480", "-h", "270", "-o", str(png), str(quelle)],
                               check=True, capture_output=True)
                quelle.unlink(missing_ok=True)
            self.signal.fertig.emit(self.mid, str(png))
        except Exception:
            pass


class Vorschauen(QObject):
    """Zwischenspeicher für Hintergrund-Vorschaubilder (werden im Hintergrund gerendert)."""
    neu = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.bilder = {}
        self.laufend = set()
        self.signal = VorschauSignal()
        self.signal.fertig.connect(self._fertig)
        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(4)

    def schluessel(self, mid, p):
        f, firma = hintergruende._funktion(mid)
        return mid if firma else mid + "|" + "".join(p[k] for k in kern.FARBNAMEN)

    def holen(self, mid, p):
        s = self.schluessel(mid, p)
        if s in self.bilder:
            return self.bilder[s]
        if s not in self.laufend:
            self.laufend.add(s)
            auftrag = VorschauAuftrag(mid, p, self.signal)
            auftrag.schluessel = s
            self._offen = getattr(self, "_offen", {})
            self._offen[mid] = s
            self.pool.start(auftrag)
        return None

    def _fertig(self, mid, png):
        s = self._offen.get(mid, mid)
        self.bilder[s] = QPixmap(png)
        self.laufend.discard(s)
        self.neu.emit(mid)


# ====================================================================== Zeichnen der Knöpfe (Vorschau)

def sechseck(cx, cy, r, drehung=0):
    pts = []
    for i in range(6):
        w = math.radians(60 * i - 90 + drehung)
        pts.append(QPointF(cx + r * math.cos(w), cy + r * math.sin(w)))
    return QPolygonF(pts)


def knopf_zeichnen(qp, art, cx, cy, r, ruhe, akzent, symbol, aktiv=False, gefahr="#e24b4a"):
    farbe = QColor(gefahr if symbol == "x" else akzent)
    qp.save()
    stift = QPen(QColor(ruhe), max(1.2, r * 0.16))
    stift.setCapStyle(Qt.PenCapStyle.RoundCap)
    stift.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

    def zeichen(farbe_z):
        s = QPen(QColor(farbe_z), max(1.2, r * 0.17))
        s.setCapStyle(Qt.PenCapStyle.RoundCap)
        qp.setPen(s)
        k = r * 0.38
        if symbol == "-":
            qp.drawLine(QPointF(cx - k, cy), QPointF(cx + k, cy))
        elif symbol == "+":
            qp.drawLine(QPointF(cx - k, cy), QPointF(cx + k, cy))
            qp.drawLine(QPointF(cx, cy - k), QPointF(cx, cy + k))
        else:
            qp.drawLine(QPointF(cx - k, cy - k), QPointF(cx + k, cy + k))
            qp.drawLine(QPointF(cx + k, cy - k), QPointF(cx - k, cy + k))

    if art == "schrauben":
        if aktiv:
            qp.setPen(Qt.PenStyle.NoPen)
            qp.setBrush(farbe)
            qp.drawPolygon(sechseck(cx, cy, r, 30))
            zeichen("#ffffff")
        else:
            qp.setPen(stift)
            qp.setBrush(Qt.BrushStyle.NoBrush)
            qp.drawPolygon(sechseck(cx, cy, r))
            zeichen(ruhe)
    elif art == "punkte":
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(farbe if aktiv else QColor(ruhe))
        qp.drawEllipse(QPointF(cx, cy), r * 0.7, r * 0.7)
        if aktiv:
            zeichen("#ffffff")
    elif art == "terminal":
        zeichen(farbe.name() if aktiv else ruhe)
    elif art == "klammern":
        f = farbe.name() if aktiv else ruhe
        s = QPen(QColor(f), max(1.0, r * 0.14))
        qp.setPen(s)
        qp.drawPolyline(QPolygonF([QPointF(cx - r * 0.55, cy - r * 0.6), QPointF(cx - r * 0.8, cy - r * 0.6),
                                   QPointF(cx - r * 0.8, cy + r * 0.6), QPointF(cx - r * 0.55, cy + r * 0.6)]))
        qp.drawPolyline(QPolygonF([QPointF(cx + r * 0.55, cy - r * 0.6), QPointF(cx + r * 0.8, cy - r * 0.6),
                                   QPointF(cx + r * 0.8, cy + r * 0.6), QPointF(cx + r * 0.55, cy + r * 0.6)]))
        zeichen(f)
    elif art == "kapsel":
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(farbe if aktiv else QColor(ruhe).lighter(60))
        qp.drawRoundedRect(QRectF(cx - r, cy - r * 0.65, 2 * r, 1.3 * r), r * 0.65, r * 0.65)
        zeichen("#ffffff" if aktiv else ruhe)
    elif art == "balken":
        qp.setPen(Qt.PenStyle.NoPen)
        if aktiv:
            qp.setBrush(farbe)
            qp.drawRoundedRect(QRectF(cx - r * 0.75, cy - r * 0.75, 1.5 * r, 1.5 * r), r * 0.3, r * 0.3)
            zeichen("#ffffff")
        else:
            qp.setBrush(QColor(ruhe))
            qp.drawRoundedRect(QRectF(cx - r * 0.75, cy - r * 0.18, 1.5 * r, 0.36 * r), r * 0.18, r * 0.18)
    qp.restore()


# ====================================================================== Konfigurator-Fläche

BEREICHE = [
    # id, Beschriftung
    ("hintergrund", "Hintergrund"),
    ("fenster", "Fenster und Knöpfe"),
    ("animationen", "Animationen"),
    ("taskleiste", "Taskleiste"),
    ("startmenue", "Startmenü"),
    ("symbole", "Symbole und Mauszeiger"),
    ("uhr", "Sperrbildschirm und Start"),
    ("klaenge", "Klänge"),
]


class Konfigurator(QWidget):
    bereichGewaehlt = pyqtSignal(str)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setMouseTracking(True)
        self.setMinimumSize(640, 380)
        self.punkte = {}
        self.ueber = None
        self.aktiv = None
        self.phase = 0.0
        self.knopf_hover = False
        t = QTimer(self)
        t.timeout.connect(self._takt)
        t.start(40)

    def _takt(self):
        self.phase = (self.phase + 0.04) % 1.0
        self.update()

    def sizeHint(self):
        return QSize(900, 540)

    # ---------------------------------------------------------------- Zeichnen
    def paintEvent(self, ev):
        e, p = self.app.e, self.app.p
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        # Bildschirm im 16:9-Format
        bw = min(w - 24, (h - 24) * 16 / 9)
        bh = bw * 9 / 16
        x0, y0 = (w - bw) / 2, (h - bh) / 2
        R = QRectF(x0, y0, bw, bh)
        self.R = R
        k = bw / 900.0
        rahmen = QPainterPath()
        rahmen.addRoundedRect(R, 14 * k, 14 * k)
        qp.setClipPath(rahmen)

        # Hintergrund
        bild = self.app.vorschauen.holen(e["hintergrund"], p)
        if bild and not bild.isNull():
            qp.drawPixmap(R.toRect(), bild)
        else:
            g = QLinearGradient(R.topLeft(), R.bottomLeft())
            g.setColorAt(0, QColor(p["flaeche"]))
            g.setColorAt(1, QColor(p["grund"]))
            qp.fillRect(R, g)

        # Desktopsymbol (Ordner)
        ox, oy = x0 + 26 * k, y0 + 26 * k
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QColor(p["akzent"]).darker(130))
        qp.drawRoundedRect(QRectF(ox, oy, 46 * k, 34 * k), 5 * k, 5 * k)
        qp.setBrush(QColor(p["akzent"]))
        qp.drawRoundedRect(QRectF(ox, oy + 8 * k, 46 * k, 28 * k), 5 * k, 5 * k)
        self._schrift(qp, 9 * k)
        qp.setPen(QColor("#ffffff"))
        qp.drawText(QRectF(ox - 10 * k, oy + 40 * k, 66 * k, 14 * k), Qt.AlignmentFlag.AlignCenter, "Dateien")
        self.punkte["symbole"] = QPointF(ox + 50 * k, oy + 4 * k)

        # Fenster
        fx, fy, fw, fh = x0 + 170 * k, y0 + 70 * k, 470 * k, 300 * k
        rund = 9 * k if e["ecken"] == "rund" else 2 * k
        titel_h = (22 if e["titelleiste"] == "schlank" else 32) * k
        farbig = e["titelleiste"] == "farbig"
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QColor(0, 0, 0, 90))
        qp.drawRoundedRect(QRectF(fx + 4 * k, fy + 10 * k, fw, fh), rund, rund)
        qp.setBrush(QColor(p["flaeche"]))
        qp.drawRoundedRect(QRectF(fx, fy, fw, fh), rund, rund)
        if farbig:
            pfad = QPainterPath()
            pfad.addRoundedRect(QRectF(fx, fy, fw, titel_h + rund), rund, rund)
            qp.setBrush(QColor(p["akzent"]))
            qp.drawPath(pfad)
            qp.setBrush(QColor(p["flaeche"]))
            qp.drawRect(QRectF(fx, fy + titel_h, fw, rund))
        else:
            qp.setBrush(QColor(p["akzent"]))
            pfad = QPainterPath()
            pfad.addRoundedRect(QRectF(fx, fy, fw, 6 * k), rund, rund)
            qp.setClipPath(pfad, Qt.ClipOperation.IntersectClip)
            qp.drawRect(QRectF(fx, fy, fw, 2.4 * k))
            qp.setClipPath(rahmen)
        self._schrift(qp, 11 * k, fett=True)
        qp.setPen(QColor(p["auf_akzent"] if farbig else p["text"]))
        qp.drawText(QRectF(fx, fy, fw, titel_h), Qt.AlignmentFlag.AlignCenter, "Dateien")
        r = titel_h * 0.27
        ruhe = kern.mischen(p["akzent"], p["auf_akzent"], 0.35) if farbig else p["knopf_ruhe"]
        symbole = ["x", "+", "-"] if e["knoepfe_links"] else ["-", "+", "x"]
        for i, s in enumerate(symbole):
            if e["knoepfe_links"]:
                cx = fx + 18 * k + i * (2 * r + 7 * k)
            else:
                cx = fx + fw - 18 * k - (2 - i) * (2 * r + 7 * k)
            aktiv = self.knopf_hover and s == "x"
            knopf_zeichnen(qp, e["knoepfe"], cx, fy + titel_h / 2, r, ruhe,
                           p["auf_akzent"] if farbig else p["akzent"], s, aktiv, p["gefahr"])
        # Fensterinhalt
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QColor(p["karte"]))
        qp.drawRoundedRect(QRectF(fx + 14 * k, fy + titel_h + 12 * k, 120 * k, fh - titel_h - 26 * k), 6 * k, 6 * k)
        for i in range(4):
            qp.setBrush(QColor(p["akzent"] if i == 1 else p["rand"]))
            qp.drawRoundedRect(QRectF(fx + 24 * k, fy + titel_h + 26 * k + i * 26 * k, 90 * k, 10 * k), 5 * k, 5 * k)
        for i in range(6):
            col, row = i % 3, i // 3
            qp.setBrush(QColor(p["akzent"]).darker(110))
            qp.drawRoundedRect(QRectF(fx + 160 * k + col * 95 * k, fy + titel_h + 26 * k + row * 90 * k, 70 * k, 52 * k), 6 * k, 6 * k)
        self.punkte["fenster"] = QPointF(fx + fw - 18 * k - 2 * (2 * r + 7 * k), fy - 10 * k)
        self.punkte["animationen"] = QPointF(fx + fw * 0.62, fy + fh * 0.62)

        # Mauszeiger
        mx, my = fx + fw - 120 * k, fy + fh - 60 * k
        qp.setPen(QPen(QColor("#0b0d12"), 1.4 * k))
        qp.setBrush(QColor(p["akzent"]) if e["zeiger"] == "biblix" else QColor("#ffffff"))
        qp.drawPolygon(QPolygonF([QPointF(mx, my), QPointF(mx, my + 22 * k), QPointF(mx + 5 * k, my + 17 * k),
                                  QPointF(mx + 9 * k, my + 25 * k), QPointF(mx + 12.5 * k, my + 23.5 * k),
                                  QPointF(mx + 9 * k, my + 16 * k), QPointF(mx + 16 * k, my + 16 * k)]))

        # Taskleiste
        tl = e["taskleiste"]
        th = 40 * k
        if tl == "fest":
            tr = QRectF(x0, y0 + bh - th, bw, th)
            tr_rund = 0
        elif tl == "dock":
            tr = QRectF(x0 + bw / 2 - 170 * k, y0 + bh - th - 10 * k, 340 * k, th)
            tr_rund = 14 * k
        else:
            tr = QRectF(x0 + 10 * k, y0 + bh - th - 10 * k, bw - 20 * k, th)
            tr_rund = 12 * k
        alpha = {"milchglas": 200, "undurchsichtig": 255, "adaptiv": 170}[e["transparenz"]]
        qp.setBrush(qfarbe(p["flaeche"], alpha))
        qp.setPen(QPen(qfarbe(p["rand"], 160), 1))
        qp.drawRoundedRect(tr, tr_rund, tr_rund)
        mitte = e["startmenue_position"] == "mitte" or tl == "dock"
        sx = tr.center().x() - 90 * k if mitte else tr.left() + 10 * k
        sy = tr.top() + 6 * k
        sg = th - 12 * k
        # Startknopf
        logo = self.app.logo_pixmap()
        if logo:
            qp.drawPixmap(QRectF(sx, sy, sg, sg).toRect(), logo)
        self.punkte["startmenue"] = QPointF(sx + sg / 2, sy - 6 * k)
        for i in range(4):
            qp.setPen(Qt.PenStyle.NoPen)
            qp.setBrush(qfarbe(p["text"], 60 if i else 110))
            qp.drawRoundedRect(QRectF(sx + (i + 1) * (sg + 10 * k), sy + 3 * k, sg - 6 * k, sg - 6 * k), 5 * k, 5 * k)
        self.punkte["taskleiste"] = QPointF(sx + 3 * (sg + 10 * k), tr.top() - 8 * k)
        if tl != "dock":
            self._schrift(qp, 11 * k, mono=True)
            qp.setPen(QColor(p["text"]))
            qp.drawText(QRectF(tr.right() - 70 * k, tr.top(), 60 * k, th), Qt.AlignmentFlag.AlignCenter, "18:42")
            self.punkte["uhr"] = QPointF(tr.right() - 40 * k, tr.top() - 8 * k)
            # Lautsprecher
            lx, ly = tr.right() - 95 * k, tr.center().y()
            qp.setPen(QPen(QColor(p["text"]), 1.6 * k))
            qp.setBrush(QColor(p["text"]))
            qp.drawPolygon(QPolygonF([QPointF(lx - 6 * k, ly - 3 * k), QPointF(lx - 2 * k, ly - 3 * k),
                                      QPointF(lx + 3 * k, ly - 7 * k), QPointF(lx + 3 * k, ly + 7 * k),
                                      QPointF(lx - 2 * k, ly + 3 * k), QPointF(lx - 6 * k, ly + 3 * k)]))
            qp.setBrush(Qt.BrushStyle.NoBrush)
            qp.drawArc(QRectF(lx, ly - 7 * k, 12 * k, 14 * k), -50 * 16, 100 * 16)
            self.punkte["klaenge"] = QPointF(lx, tr.top() - 8 * k)
        else:
            self.punkte["uhr"] = QPointF(x0 + bw - 40 * k, y0 + 30 * k)
            self.punkte["klaenge"] = QPointF(x0 + bw - 80 * k, y0 + 30 * k)
        self.punkte["hintergrund"] = QPointF(x0 + bw - 120 * k, y0 + 120 * k)

        # Startmenü andeuten, wenn gewählt
        if self.aktiv == "startmenue":
            mw, mh = 230 * k, 250 * k
            m = QRectF(sx if not mitte else sx - mw / 2 + sg / 2, tr.top() - mh - 10 * k, mw, mh)
            if e["startmenue"] == "vollbild":
                m = QRectF(x0 + 60 * k, y0 + 40 * k, bw - 120 * k, bh - 120 * k)
            qp.setPen(QPen(qfarbe(p["rand"]), 1))
            qp.setBrush(qfarbe(p["flaeche"], 245))
            qp.drawRoundedRect(m, 12 * k, 12 * k)
            qp.setPen(Qt.PenStyle.NoPen)
            qp.setBrush(qfarbe(p["karte"]))
            qp.drawRoundedRect(QRectF(m.left() + 12 * k, m.top() + 44 * k, m.width() - 24 * k, 22 * k), 6 * k, 6 * k)
            for i in range(4):
                qp.setBrush(qfarbe(p["akzent"], 90 if i == 0 else 40))
                qp.drawRoundedRect(QRectF(m.left() + 12 * k + i * (m.width() - 24 * k) / 4 + 2 * k, m.top() + 76 * k,
                                          (m.width() - 24 * k) / 4 - 4 * k, 34 * k), 6 * k, 6 * k)
            for i in range(12):
                c, z = i % 6, i // 6
                qp.setBrush(qfarbe(p["text"], 50))
                qp.drawRoundedRect(QRectF(m.left() + 14 * k + c * (m.width() - 28 * k) / 6, m.top() + 124 * k + z * 34 * k,
                                          (m.width() - 28 * k) / 6 - 6 * k, 24 * k), 5 * k, 5 * k)
            self._schrift(qp, 10 * k, fett=True)
            qp.setPen(QColor(p["text"]))
            qp.drawText(QRectF(m.left() + 14 * k, m.top() + 10 * k, m.width(), 24 * k), Qt.AlignmentFlag.AlignVCenter,
                        "Hallo, bibi")
            for i in range(5):
                knopf_zeichnen(qp, "schrauben", m.right() - 18 * k - i * 22 * k, m.bottom() - 18 * k, 8 * k,
                               p["knopf_ruhe"], p["akzent"], "x" if i == 0 else "-", False, p["gefahr"])

        qp.setClipping(False)
        # Leuchtpunkte
        for bid, punkt in self.punkte.items():
            gewaehlt = bid == self.aktiv
            hover = bid == self.ueber
            puls = 0.5 + 0.5 * math.sin(self.phase * 2 * math.pi)
            ring = (9 + 7 * puls) * max(0.8, k)
            qp.setPen(Qt.PenStyle.NoPen)
            qp.setBrush(qfarbe(p["akzent2"], int(70 * (1 - puls)) + 30))
            qp.drawEllipse(punkt, ring, ring)
            qp.setBrush(QColor(p["akzent2"]) if not gewaehlt else QColor("#ffffff"))
            qp.setPen(QPen(QColor("#0b0d12"), 1.5))
            g = (8 if hover or gewaehlt else 6) * max(0.8, k)
            qp.drawEllipse(punkt, g, g)
        if self.ueber:
            name = dict(BEREICHE)[self.ueber]
            punkt = self.punkte[self.ueber]
            self._schrift(qp, 12)
            fm = qp.fontMetrics()
            bwt = fm.horizontalAdvance(name) + 18
            box = QRectF(punkt.x() - bwt / 2, punkt.y() - 40, bwt, 26)
            qp.setPen(Qt.PenStyle.NoPen)
            qp.setBrush(QColor(15, 18, 24, 230))
            qp.drawRoundedRect(box, 8, 8)
            qp.setPen(QColor("#ffffff"))
            qp.drawText(box, Qt.AlignmentFlag.AlignCenter, name)
        qp.end()

    def _schrift(self, qp, groesse, fett=False, mono=False):
        f = QFont("DejaVu Sans Mono" if mono else "DejaVu Sans")
        f.setPixelSize(max(7, int(groesse)))
        f.setBold(fett)
        qp.setFont(f)

    # ---------------------------------------------------------------- Maus
    def _treffer(self, pos):
        for bid, punkt in self.punkte.items():
            if (QPointF(pos) - punkt).manhattanLength() < 22:
                return bid
        return None

    def mouseMoveEvent(self, ev):
        t = self._treffer(ev.position())
        self.ueber = t
        self.setCursor(Qt.CursorShape.PointingHandCursor if t else Qt.CursorShape.ArrowCursor)
        self.knopf_hover = t == "fenster"

    def mousePressEvent(self, ev):
        t = self._treffer(ev.position())
        if t:
            self.aktiv = t
            self.bereichGewaehlt.emit(t)


# ====================================================================== Auswahl-Bausteine

class Wahl(QWidget):
    """Eine Zeile mit Knöpfen zum Auswählen (genau einer aktiv)."""
    geaendert = pyqtSignal(str, object)

    def __init__(self, titel, schluessel, optionen, wert, spalten=3):
        super().__init__()
        self.schluessel = schluessel
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 6)
        lay.setSpacing(6)
        t = QLabel(titel)
        t.setObjectName("leise")
        lay.addWidget(t)
        gitter = QGridLayout()
        gitter.setSpacing(6)
        self.gruppe = QButtonGroup(self)
        for i, (w, name) in enumerate(optionen):
            b = QPushButton(name)
            b.setCheckable(True)
            b.setObjectName("chip")
            b.setChecked(w == wert)
            # schmal werden dürfen, damit nichts aus der Seite ragt (lange Namen werden gekürzt)
            b.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            b.setMinimumWidth(70)
            b.setToolTip(name)
            b.clicked.connect(lambda _=False, w=w: self.geaendert.emit(self.schluessel, w))
            self.gruppe.addButton(b)
            gitter.addWidget(b, i // spalten, i % spalten)
        lay.addLayout(gitter)


class Schalter(QCheckBox):
    geaendert = pyqtSignal(str, object)

    def __init__(self, titel, schluessel, wert):
        super().__init__(titel)
        self.schluessel = schluessel
        self.setChecked(bool(wert))
        self.toggled.connect(lambda an: self.geaendert.emit(self.schluessel, an))


class HintergrundKachel(QToolButton):
    def __init__(self, mid, name):
        super().__init__()
        self.mid = mid
        self.setText(name)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIconSize(QSize(150, 84))
        self.setCheckable(True)
        self.setObjectName("bildkachel")
        self.setFixedSize(168, 112)


# ====================================================================== Hauptfenster

class Anwender(QThread):
    meldung = pyqtSignal(str)
    fertig = pyqtSignal()

    def __init__(self, e):
        super().__init__()
        self.e = e

    def run(self):
        kern.speichern(self.e)
        anwenden.alles(self.e, system=True, melden=self.meldung.emit)
        self.fertig.emit()


class Fenster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Biblix Design")
        self.setWindowIcon(QIcon.fromTheme("de.biblix.Design", QIcon.fromTheme("preferences-desktop-theme")))
        self.resize(1360, 820)
        self.e = kern.laden()
        self.gespeichert = copy.deepcopy(self.e)
        self.p = kern.palette(self.e)
        self.vorschauen = Vorschauen()
        self._logo = None
        self.arbeiter = None

        haupt = QWidget()
        self.setCentralWidget(haupt)
        v = QVBoxLayout(haupt)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Kopfzeile mit Seiten
        kopf = QFrame()
        kopf.setObjectName("kopf")
        kh = QHBoxLayout(kopf)
        kh.setContentsMargins(18, 10, 18, 10)
        marke = QLabel("Biblix Design")
        marke.setObjectName("marke")
        kh.addWidget(marke)
        kh.addSpacing(24)
        self.seiten_gruppe = QButtonGroup(self)
        for i, name in enumerate(["Konfigurator", "Presets", "Meine Mischungen", "Extras"]):
            b = QPushButton(name)
            b.setCheckable(True)
            b.setObjectName("reiter")
            b.setChecked(i == 0)
            b.clicked.connect(lambda _=False, i=i: self.seiten.setCurrentIndex(i))
            self.seiten_gruppe.addButton(b)
            kh.addWidget(b)
        kh.addStretch(1)
        self.spruch = QLabel("DEIN SYSTEM. DEIN PROBLEM.")
        self.spruch.setObjectName("spruch")
        kh.addWidget(self.spruch)
        v.addWidget(kopf)

        self.seiten = QStackedWidget()
        v.addWidget(self.seiten, 1)

        # --- Seite 1: Konfigurator
        s1 = QWidget()
        h1 = QHBoxLayout(s1)
        h1.setContentsMargins(14, 14, 14, 14)
        h1.setSpacing(14)
        self.konf = Konfigurator(self)
        self.konf.bereichGewaehlt.connect(self.bereich_zeigen)
        h1.addWidget(self.konf, 1)
        self.seite_rechts = QScrollArea()
        self.seite_rechts.setWidgetResizable(True)
        self.seite_rechts.setFixedWidth(420)
        self.seite_rechts.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.seite_rechts.setObjectName("rechts")
        h1.addWidget(self.seite_rechts)
        self.seiten.addWidget(s1)

        # --- Seite 2: Presets
        self.presets_seite = QScrollArea()
        self.presets_seite.setWidgetResizable(True)
        self.seiten.addWidget(self.presets_seite)

        # --- Seite 3: Meine Mischungen
        s3 = QWidget()
        v3 = QVBoxLayout(s3)
        v3.setContentsMargins(24, 20, 24, 20)
        v3.addWidget(self._titel("Meine Mischungen"))
        hinweis = QLabel("Speichere deine aktuelle Mischung unter einem Namen und hole sie jederzeit zurück.")
        hinweis.setObjectName("leise")
        hinweis.setWordWrap(True)
        v3.addWidget(hinweis)
        zeile = QHBoxLayout()
        speichern = QPushButton("Aktuelle Mischung speichern …")
        speichern.clicked.connect(self.mischung_speichern)
        zeile.addWidget(speichern)
        laden = QPushButton("Laden")
        laden.clicked.connect(self.mischung_laden)
        zeile.addWidget(laden)
        loeschen = QPushButton("Löschen")
        loeschen.clicked.connect(self.mischung_loeschen)
        zeile.addWidget(loeschen)
        zeile.addStretch(1)
        v3.addLayout(zeile)
        self.mischungen = QListWidget()
        v3.addWidget(self.mischungen, 1)
        v3.addWidget(self._titel("Verlauf (Rückgängig)"))
        self.verlauf = QListWidget()
        self.verlauf.itemDoubleClicked.connect(self.verlauf_laden)
        v3.addWidget(self.verlauf, 1)
        self.seiten.addWidget(s3)

        # --- Seite 4: Extras
        self.extras_seite = QScrollArea()
        self.extras_seite.setWidgetResizable(True)
        self.seiten.addWidget(self.extras_seite)

        # Fußleiste: Lackfarben, Modus, Rückgängig, Übernehmen
        fuss = QFrame()
        fuss.setObjectName("fuss")
        fh = QHBoxLayout(fuss)
        fh.setContentsMargins(18, 10, 18, 10)
        fh.setSpacing(10)
        lack = QLabel("Lack:")
        lack.setObjectName("leise")
        fh.addWidget(lack)
        self.lack_gruppe = QButtonGroup(self)
        for pr in kern.presets():
            b = QPushButton()
            b.setCheckable(True)
            b.setToolTip(pr["name"])
            b.setObjectName("lack")
            b.setFixedSize(38, 38)
            d = pr["dunkel"]
            b.setStyleSheet(f"QPushButton#lack {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {d['grund']}, "
                            f"stop:0.5 {d['akzent']}, stop:1 {d['akzent2']}); }}")
            b.clicked.connect(lambda _=False, pid=pr["id"]: self.preset_waehlen(pid))
            b.setProperty("pid", pr["id"])
            self.lack_gruppe.addButton(b)
            fh.addWidget(b)
        eigen = QPushButton("Eigene Farben …")
        eigen.clicked.connect(self.eigene_farben)
        fh.addWidget(eigen)
        fh.addSpacing(12)
        self.modus_wahl = QButtonGroup(self)
        for w, name in kern.WAHL["modus"]:
            b = QPushButton(name)
            b.setCheckable(True)
            b.setObjectName("chip")
            b.setProperty("wert", w)
            b.setMinimumWidth(b.fontMetrics().horizontalAdvance(name) + 40)
            b.clicked.connect(lambda _=False, w=w: self.setzen("modus", w))
            self.modus_wahl.addButton(b)
            fh.addWidget(b)
        fh.addStretch(1)
        self.status = QLabel("")
        self.status.setObjectName("leise")
        fh.addWidget(self.status)
        self.fortschritt = QProgressBar()
        self.fortschritt.setRange(0, 0)
        self.fortschritt.setFixedWidth(120)
        self.fortschritt.hide()
        fh.addWidget(self.fortschritt)
        zurueck = QPushButton("Rückgängig")
        zurueck.clicked.connect(self.rueckgaengig)
        fh.addWidget(zurueck)
        self.uebernehmen_knopf = QPushButton("Übernehmen")
        self.uebernehmen_knopf.setObjectName("haupt")
        self.uebernehmen_knopf.clicked.connect(self.uebernehmen)
        fh.addWidget(self.uebernehmen_knopf)
        v.addWidget(fuss)

        self.vorschauen.neu.connect(lambda _m: (self.konf.update(), self._bildkacheln_aktualisieren()))
        self.aktueller_bereich = "hintergrund"
        self.alles_neu()
        self.konf.aktiv = "hintergrund"

    # ---------------------------------------------------------------- Hilfen
    def _titel(self, text):
        t = QLabel(text)
        t.setObjectName("titel")
        return t

    def logo_pixmap(self):
        if self._logo is None:
            from PyQt6.QtSvg import QSvgRenderer
            if self.e["startknopf"] == "firma":
                svg = grafik.FIRMENLOGOS.get(self.e["preset"], grafik.logo_bibi_tech)()
            else:
                svg = grafik.prompt_b(self.p)
            r = QSvgRenderer(svg.encode())
            pm = QPixmap(96, 96)
            pm.fill(Qt.GlobalColor.transparent)
            qp = QPainter(pm)
            r.render(qp)
            qp.end()
            self._logo = pm
        return self._logo

    def stil_setzen(self):
        p = self.p
        hinter = p["grund"]
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background: {hinter}; color: {p['text']}; font-family: 'DejaVu Sans'; font-size: 10pt; }}
            QFrame#kopf, QFrame#fuss {{ background: {p['flaeche']}; border: none; }}
            QFrame#kopf {{ border-bottom: 1px solid {p['rand']}; }}
            QFrame#fuss {{ border-top: 1px solid {p['rand']}; }}
            QLabel#marke {{ font-size: 15pt; font-weight: bold; color: {p['akzent']}; background: transparent; }}
            QLabel#spruch {{ color: {p['akzent2']}; font-family: 'DejaVu Sans Mono'; font-size: 9pt; background: transparent; }}
            QLabel#titel {{ font-size: 13pt; font-weight: bold; background: transparent; padding: 6px 0 2px 0; }}
            QLabel#leise {{ color: {p['leise']}; background: transparent; }}
            QScrollArea, QScrollArea > QWidget > QWidget {{ background: {hinter}; border: none; }}
            QScrollArea#rechts, QScrollArea#rechts > QWidget > QWidget {{ background: {p['flaeche']}; border-radius: 14px; }}
            QPushButton {{ background: {p['karte']}; color: {p['text']}; border: 1px solid {p['rand']};
                          border-radius: 9px; padding: 7px 14px; }}
            QPushButton:hover {{ border-color: {p['akzent']}; }}
            QPushButton#haupt {{ background: {p['akzent']}; color: {p['auf_akzent']}; border-color: {p['akzent']}; font-weight: bold; padding: 8px 22px; }}
            QPushButton#reiter {{ background: transparent; border: none; border-bottom: 2px solid transparent; border-radius: 0; padding: 8px 12px; }}
            QPushButton#reiter:checked {{ color: {p['akzent']}; border-bottom-color: {p['akzent']}; }}
            QPushButton#chip {{ border-radius: 16px; padding: 6px 12px; }}
            QPushButton#chip:checked {{ background: {p['auswahl']}; border-color: {p['akzent']}; color: {p['text']}; font-weight: bold; }}
            QPushButton#lack {{ border-radius: 19px; border: 2px solid {p['rand']}; }}
            QPushButton#lack:checked {{ border: 3px solid {p['text']}; }}
            QToolButton#bildkachel {{ background: {p['karte']}; border: 2px solid transparent; border-radius: 10px; color: {p['text']}; font-size: 8pt; }}
            QToolButton#bildkachel:checked {{ border-color: {p['akzent']}; }}
            QToolButton#bildkachel:hover {{ border-color: {p['rand']}; }}
            QCheckBox {{ background: transparent; spacing: 8px; padding: 4px 0; }}
            QListWidget {{ background: {p['flaeche']}; border: 1px solid {p['rand']}; border-radius: 10px; padding: 6px; }}
            QListWidget::item:selected {{ background: {p['auswahl']}; color: {p['text']}; }}
            QProgressBar {{ background: {p['karte']}; border: none; border-radius: 4px; max-height: 8px; }}
            QProgressBar::chunk {{ background: {p['akzent']}; border-radius: 4px; }}
            QSpinBox {{ background: {p['karte']}; border: 1px solid {p['rand']}; border-radius: 6px; padding: 4px; }}
        """)

    # ---------------------------------------------------------------- Zustand
    def setzen(self, schluessel, wert):
        self.e[schluessel] = wert
        self.alles_neu(nur_vorschau=schluessel not in ("modus", "preset", "eigene_farben"))

    def preset_waehlen(self, pid):
        self.e["preset"] = pid
        self.e["eigene_farben"] = None
        self.alles_neu()

    def alles_neu(self, nur_vorschau=False):
        self.p = kern.palette(self.e)
        self._logo = None
        self.stil_setzen()
        for b in self.lack_gruppe.buttons():
            b.setChecked(b.property("pid") == self.e["preset"] and not self.e.get("eigene_farben"))
        for b in self.modus_wahl.buttons():
            b.setChecked(b.property("wert") == self.e["modus"])
        self.bereich_zeigen(self.aktueller_bereich)
        if not nur_vorschau:
            self.presets_bauen()
        self.extras_bauen()
        self.mischungen_laden()
        geaendert = self.e != self.gespeichert
        self.status.setText("Nicht übernommen" if geaendert else "")
        self.konf.update()

    # ---------------------------------------------------------------- rechte Seite
    def bereich_zeigen(self, bid):
        self.aktueller_bereich = bid
        self.konf.aktiv = bid
        e = self.e
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)
        lay.addWidget(self._titel(dict(BEREICHE)[bid]))

        def wahl(titel, schluessel, spalten=3):
            x = Wahl(titel, schluessel, kern.WAHL[schluessel], e[schluessel], spalten)
            x.geaendert.connect(self.setzen)
            lay.addWidget(x)

        def schalter(titel, schluessel):
            x = Schalter(titel, schluessel, e[schluessel])
            x.geaendert.connect(self.setzen)
            lay.addWidget(x)

        if bid == "hintergrund":
            self.bildkacheln = []
            schalter("Diashow (Bilder wechseln automatisch)", "diashow")
            zeile = QHBoxLayout()
            zl = QLabel("Wechsel alle")
            zl.setObjectName("leise")
            zeile.addWidget(zl)
            minuten = QSpinBox()
            minuten.setRange(1, 600)
            minuten.setSuffix(" Minuten")
            minuten.setValue(int(e.get("diashow_minuten", 30)))
            minuten.valueChanged.connect(lambda v: self.e.__setitem__("diashow_minuten", v))
            zeile.addWidget(minuten)
            zeile.addStretch(1)
            lay.addLayout(zeile)
            # Animierte Hintergruende: eigene Vorschaubilder, pausieren bei Vollbild und maximierten Fenstern
            titel = QLabel("Lebendig (animiert) · pausiert bei Spielen und maximierten Fenstern")
            titel.setObjectName("leise")
            titel.setWordWrap(True)
            lay.addWidget(titel)
            gitter = QGridLayout()
            gitter.setSpacing(8)
            for k, (szene, name, _gruppe, _standbild) in enumerate(hintergruende.LEBENDIG):
                mid = hintergruende.LEBENDIG_PREFIX + szene
                kachel = HintergrundKachel(mid, "▶ " + name)
                bild = kern.DESIGN / "lebendig" / f"{szene}.png"
                if bild.is_file():
                    kachel.setIcon(QIcon(str(bild)))
                kachel.lebendig = True
                kachel.setChecked(mid == e["hintergrund"])
                kachel.clicked.connect(lambda _=False, mid=mid: self.setzen("hintergrund", mid))
                gitter.addWidget(kachel, k // 2, k % 2)
                self.bildkacheln.append(kachel)
            lay.addLayout(gitter)
            gruppen = [("allgemein", "In deinen Farben")] + [(pr["id"], pr["name"]) for pr in kern.presets()]
            alle = hintergruende.alle()
            for gid, gname in gruppen:
                motive = [(i, n) for i, n, g in alle if g == gid]
                if not motive:
                    continue
                l = QLabel(gname)
                l.setObjectName("leise")
                lay.addWidget(l)
                gitter = QGridLayout()
                gitter.setSpacing(8)
                for k, (mid, name) in enumerate(motive):
                    kachel = HintergrundKachel(mid, name)
                    kachel.setChecked(mid == e["hintergrund"])
                    kachel.clicked.connect(lambda _=False, mid=mid: self.setzen("hintergrund", mid))
                    gitter.addWidget(kachel, k // 2, k % 2)
                    self.bildkacheln.append(kachel)
                lay.addLayout(gitter)
            self._bildkacheln_aktualisieren()
        elif bid == "fenster":
            wahl("Knöpfe", "knoepfe")
            schalter("Knöpfe links (wie bei Apple)", "knoepfe_links")
            wahl("Titelleiste", "titelleiste")
            wahl("Ecken", "ecken", 2)
            tipp = QLabel("Tipp: Fahr im Bild über die Knöpfe, um sie in Aktion zu sehen.")
            tipp.setObjectName("leise")
            tipp.setWordWrap(True)
            lay.addWidget(tipp)
        elif bid == "animationen":
            schalter("Animationen an", "animationen")
            wahl("Fenster öffnen", "effekt_oeffnen")
            wahl("Fenster schließen", "effekt_schliessen")
            wahl("Minimieren", "effekt_minimieren")
            wahl("Arbeitsflächen", "arbeitsflaechen")
            wahl("Arbeitsfläche wechseln", "arbeitsflaeche")
            schalter("Wackelnde Fenster beim Verschieben", "wackeln")
            schalter("Fenster beim Verschieben durchsichtig", "durchsichtig_verschieben")
            schalter("Klick-Funken (an/aus mit Meta + *)", "klick_funken")
            wahl("Leistungs-Overlay in Spielen (ein/aus: Shift rechts + F12)", "overlay")
            hinweis = QLabel("Bei Spielen im Vollbild sind alle Animationen automatisch aus.\n"
                             "Arbeitsflächen „Eine“: kein Umschalter in der Taskleiste. Würfel, Gleiten und "
                             "Überblenden gibt es nur mit „Vier“ (Wechsel mit Strg+F1 … F4, Meta+C dreht den Würfel mit der Maus).")
            hinweis.setObjectName("leise")
            hinweis.setWordWrap(True)
            lay.addWidget(hinweis)
        elif bid == "taskleiste":
            wahl("Form", "taskleiste")
            wahl("Durchsichtigkeit", "transparenz")
            wahl("Zwei Monitore", "monitore", 1)
        elif bid == "startmenue":
            wahl("Startmenü", "startmenue")
            wahl("Position", "startmenue_position", 2)
            wahl("Startknopf", "startknopf", 2)
        elif bid == "symbole":
            wahl("App-Symbole", "symbole")
            wahl("Symbole unten rechts (Lautstärke, Netzwerk …)", "tray", 2)
            wahl("Mauszeiger", "zeiger", 2)
            wahl("Lade-Zeiger", "ladezeiger")
        elif bid == "uhr":
            wahl("Sperrbildschirm", "sperrbildschirm")
            wahl("Ladeanimation nach dem Anmelden", "ladeanimation")
            schalter("Bootmenü und Startbildschirm mitfärben (fragt einmal nach dem Passwort)", "bootmenue_mitfaerben")
        elif bid == "klaenge":
            wahl("Klänge", "klaenge")
            schalter("Bibi-Jingle beim Start", "startklang")
            hoeren = QPushButton("Startklang anhören")
            hoeren.clicked.connect(self.klang_hoeren)
            lay.addWidget(hoeren)
        lay.addStretch(1)
        self.seite_rechts.setWidget(w)
        self.konf.update()

    def _bildkacheln_aktualisieren(self):
        for kachel in getattr(self, "bildkacheln", []):
            if getattr(kachel, "lebendig", False):
                continue  # animierte haben feste Vorschaubilder
            try:
                bild = self.vorschauen.holen(kachel.mid, self.p)
            except RuntimeError:
                continue
            if bild:
                kachel.setIcon(QIcon(bild))

    def klang_hoeren(self):
        e = self.e
        if e["klaenge"] == "preset":
            thema = "biblix-" + kern.preset(e["preset"]).get("klang", "tech")
        else:
            thema = {"biblix": "biblix", "retro": "biblix-retro", "ruhig": "biblix-ruhig", "aus": "biblix"}[e["klaenge"]]
        datei = Path(f"/usr/share/sounds/{thema}/stereo/desktop-login.oga")
        if datei.exists():
            subprocess.Popen(["pw-play", str(datei)] if Path("/usr/bin/pw-play").exists() else ["paplay", str(datei)])

    # ---------------------------------------------------------------- Presets
    def presets_bauen(self):
        w = QWidget()
        g = QGridLayout(w)
        g.setContentsMargins(24, 20, 24, 20)
        g.setSpacing(16)
        g.addWidget(self._titel("Presets: fertige Komplett-Looks"), 0, 0, 1, 3)
        from PyQt6.QtSvg import QSvgRenderer
        for i, pr in enumerate(kern.presets()):
            karte = QPushButton()
            karte.setFixedSize(360, 200)
            d = pr[kern.aktueller_modus(self.e)]
            karte.setStyleSheet(f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {d['flaeche']}, stop:1 {d['grund']});"
                                f" border: 2px solid {d['akzent'] if pr['id'] == self.e['preset'] else d['rand']}; border-radius: 16px; }}")
            inner = QVBoxLayout(karte)
            kopf = QHBoxLayout()
            logo = QLabel()
            pm = QPixmap(56, 56)
            pm.fill(Qt.GlobalColor.transparent)
            qp = QPainter(pm)
            QSvgRenderer(grafik.FIRMENLOGOS[pr["id"]]().encode()).render(qp)
            qp.end()
            logo.setPixmap(pm)
            logo.setStyleSheet("background: transparent;")
            kopf.addWidget(logo)
            name = QLabel(f"<b style='font-size:14pt'>{pr['name']}</b><br><span>{pr['beschreibung']}</span>")
            name.setStyleSheet(f"background: transparent; color: {d['text']};")
            kopf.addWidget(name, 1)
            inner.addLayout(kopf)
            farben = QHBoxLayout()
            for k in ("grund", "flaeche", "karte", "akzent", "akzent2", "text"):
                f = QLabel()
                f.setFixedSize(40, 22)
                f.setStyleSheet(f"background: {d[k]}; border-radius: 6px; border: 1px solid {d['rand']};")
                farben.addWidget(f)
            farben.addStretch(1)
            inner.addLayout(farben)
            karte.clicked.connect(lambda _=False, pid=pr["id"]: self.preset_waehlen(pid))
            g.addWidget(karte, 1 + i // 3, i % 3)
        g.setRowStretch(10, 1)
        self.presets_seite.setWidget(w)

    # ---------------------------------------------------------------- Extras
    def extras_bauen(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(8)
        lay.addWidget(self._titel("Programme im Biblix-Look"))
        for titel, k in (("Terminal in Biblix-Farben", "terminal_farben"),
                         ("Biblix-Prompt im Terminal (bibi@biblix >_)", "terminal_prompt"),
                         ("Firefox-Startseite im Biblix-Look", "firefox_startseite")):
            x = Schalter(titel, k, self.e[k])
            x.geaendert.connect(self.setzen)
            lay.addWidget(x)
        lay.addWidget(self._titel("Spielereien in der Taskleiste"))
        for titel, k in (("Spielmodus-Anzeige (leuchtet, wenn GameMode aktiv ist)", "spielmodus_anzeige"),
                         ("Update-Symbol für Biblix-Updates", "update_symbol"),
                         ("CPU-/GPU-Temperatur und Auslastung", "leistungs_anzeige"),
                         ("Kopfhörer-Schalter (Headset ↔ Lautsprecher)", "kopfhoerer_schalter")):
            x = Schalter(titel, k, self.e[k])
            x.geaendert.connect(self.setzen)
            lay.addWidget(x)
        lay.addWidget(self._titel("Firmen-Widgets für den Desktop"))
        for i, (wid, titel) in enumerate((
                ("de.biblix.tower", "Bibi Tech Stockwerk: CPU-Last als Etage"),
                ("de.biblix.bestelltafel", "Bibi Mac Bestelltafel: Uhrzeit als Abholnummer"),
                ("de.biblix.paketverfolgung", "Bibi Delivery Paketverfolgung: Downloads und Updates"),
                ("de.biblix.kontoauszug", "Bibi Budget Bank Kontoauszug: freier Speicherplatz"),
                ("de.biblix.pegel", "Nassmacher Pegel: Arbeitsspeicher"),
                ("de.biblix.leinwand", "Bibiplexx Leinwand: was gerade läuft"))):
            zeile = QHBoxLayout()
            zeile.addWidget(QLabel(titel), 1)
            dazu = QPushButton("Auf den Desktop")
            dazu.clicked.connect(lambda _=False, w=wid, n=i: self.widget_aufstellen(w, n))
            zeile.addWidget(dazu)
            lay.addLayout(zeile)
        lay.addWidget(self._titel("Notfall"))
        notfall = QPushButton("Alles auf Biblix-Standard zurücksetzen")
        notfall.clicked.connect(self.zuruecksetzen)
        lay.addWidget(notfall)
        hinweis = QLabel("Ohne Desktop geht das auch im Terminal: <b>biblix-design zuruecksetzen</b>")
        hinweis.setObjectName("leise")
        lay.addWidget(hinweis)
        lay.addStretch(1)
        self.extras_seite.setWidget(w)

    def widget_aufstellen(self, wid, nr):
        """Widget auf den Desktop des Hauptbildschirms stellen (versetzt, damit sie nicht aufeinander liegen)."""
        from biblix_design import anwenden
        x, y = 60 + (nr % 3) * 330, 80 + (nr // 3) * 320
        js = (f'var d = desktopForScreen(0) || desktops()[0];'
              f'if (d) {{ d.addWidget("{wid}", {x}, {y}, 300, 260); print("BIBLIX-OK"); }}')
        out = anwenden.plasma_skript(js)
        if "BIBLIX-OK" in out:
            self.statusBar().showMessage("Widget steht auf dem Desktop. Verschieben: Maus drüber halten und ziehen.", 6000)
        else:
            self.statusBar().showMessage("Ging nicht: Rechtsklick auf den Desktop → „Miniprogramme hinzufügen“ → „Bibi …“", 8000)

    # ---------------------------------------------------------------- Mischungen und Verlauf
    def mischungen_laden(self):
        self.mischungen.clear()
        kern.MISCHUNGEN.mkdir(parents=True, exist_ok=True)
        for f in sorted(kern.MISCHUNGEN.glob("*.json")):
            self.mischungen.addItem(QListWidgetItem(f.stem))
        self.verlauf.clear()
        for v in kern.verlauf():
            name = kern.preset(v.get("preset", "bibi-tech"))["name"]
            self.verlauf.addItem(QListWidgetItem(f"{v.get('_zeit', '')}  ·  {name}  ·  {v.get('hintergrund', '')}"))

    def mischung_speichern(self):
        name, ok = QInputDialog.getText(self, "Mischung speichern", "Name deiner Mischung:")
        name = "".join(c for c in name if c.isalnum() or c in " -_äöüÄÖÜß").strip()
        if ok and name:
            (kern.MISCHUNGEN / f"{name}.json").write_text(json.dumps(self.e, indent=1, ensure_ascii=False), encoding="utf-8")
            self.mischungen_laden()

    def mischung_laden(self):
        it = self.mischungen.currentItem()
        if it:
            daten = json.loads((kern.MISCHUNGEN / f"{it.text()}.json").read_text(encoding="utf-8"))
            self.e = {**kern.STANDARD, **daten}
            self.alles_neu()

    def mischung_loeschen(self):
        it = self.mischungen.currentItem()
        if it:
            (kern.MISCHUNGEN / f"{it.text()}.json").unlink(missing_ok=True)
            self.mischungen_laden()

    def verlauf_laden(self, item):
        v = kern.verlauf()[self.verlauf.row(item)]
        v.pop("_zeit", None)
        self.e = {**kern.STANDARD, **v}
        self.alles_neu()

    def rueckgaengig(self):
        if self.e != self.gespeichert:
            self.e = copy.deepcopy(self.gespeichert)
            self.alles_neu()
            return
        v = kern.verlauf()
        if v:
            alt = v[0]
            alt.pop("_zeit", None)
            self.e = {**kern.STANDARD, **alt}
            self.alles_neu()
            self.uebernehmen()

    def zuruecksetzen(self):
        if QMessageBox.question(self, "Zurücksetzen", "Alles auf den Biblix-Standard zurücksetzen?") == QMessageBox.StandardButton.Yes:
            self.e = copy.deepcopy(kern.STANDARD)
            self.alles_neu()
            self.uebernehmen()

    # ---------------------------------------------------------------- Eigene Farben
    def eigene_farben(self):
        modus = kern.aktueller_modus(self.e)
        basis = dict(kern.preset(self.e["preset"])[modus])
        eigen = (self.e.get("eigene_farben") or {}).get(modus, {})
        basis.update(eigen)
        namen = {"grund": "Hintergrund", "flaeche": "Flächen", "karte": "Karten", "rand": "Ränder", "text": "Schrift",
                 "leise": "Leise Schrift", "akzent": "Akzent", "akzent2": "Zweitakzent", "gefahr": "Warnfarbe"}
        for k in ("akzent", "akzent2", "grund", "flaeche", "text"):
            c = QColorDialog.getColor(QColor(basis[k]), self, f"{namen[k]} wählen (Abbrechen = behalten)")
            if c.isValid():
                basis[k] = c.name()
        # Rest passend ableiten
        basis["karte"] = kern.mischen(basis["flaeche"], basis["text"], 0.06)
        basis["rand"] = kern.mischen(basis["flaeche"], basis["text"], 0.16)
        basis["leise"] = kern.mischen(basis["text"], basis["grund"], 0.4)
        eigene = dict(self.e.get("eigene_farben") or {})
        eigene[modus] = {k: basis[k] for k in kern.FARBNAMEN}
        self.e["eigene_farben"] = eigene
        self.alles_neu()

    # ---------------------------------------------------------------- Übernehmen
    def uebernehmen(self):
        if self.arbeiter and self.arbeiter.isRunning():
            return
        self.uebernehmen_knopf.setEnabled(False)
        self.fortschritt.show()
        self.arbeiter = Anwender(copy.deepcopy(self.e))
        self.arbeiter.meldung.connect(self.status.setText)
        self.arbeiter.fertig.connect(self._fertig)
        self.arbeiter.start()

    def _fertig(self):
        self.gespeichert = copy.deepcopy(self.e)
        self.fortschritt.hide()
        self.uebernehmen_knopf.setEnabled(True)
        self.status.setText("Übernommen. AUF BIBLIX GEHT DAS.")
        self.mischungen_laden()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Biblix Design")
    app.setDesktopFileName("de.biblix.Design")
    f = Fenster()
    f.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
