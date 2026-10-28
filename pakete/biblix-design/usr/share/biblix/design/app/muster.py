"""Musterkarten: jede Auswahl im Konfigurator als Karte mit gezeichneter Miniatur.

Animationen laufen in der Karte als kurze Schleife, Klänge zeigen ihre Wellenform. Fährt die Maus
über eine Karte, meldet sie das (ueber), damit das große Bild das Ergebnis schon vorher zeigt.
"""
import math

from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF, QPainterPath, QTransform
from PyQt6.QtWidgets import QAbstractButton, QSizePolicy

# wird von der App gesetzt (Fensterknöpfe zeichnen wie im großen Bild)
KNOPF = None

# Diese Werte bewegen sich in der Karte
BEWEGT = {"effekt_oeffnen", "effekt_schliessen", "effekt_minimieren", "arbeitsflaeche", "ladezeiger",
          "ladeanimation", "klaenge"}


def f(h, a=255):
    c = QColor(h)
    c.setAlpha(int(max(0, min(255, a))))
    return c


def weich(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def schrift(qp, px, fett=False, mono=False):
    s = QFont("DejaVu Sans Mono" if mono else "DejaVu Sans")
    s.setPixelSize(max(7, int(px)))
    s.setBold(fett)
    qp.setFont(s)


def sechseck(cx, cy, r, dreh=0.0):
    return QPolygonF([QPointF(cx + r * math.cos(math.radians(60 * i + 30 + dreh)),
                              cy + r * math.sin(math.radians(60 * i + 30 + dreh))) for i in range(6)])


def fenster(qp, r, p, rund=4.0, titel="nahtlos", alpha=255):
    """Ein kleines Fenster mit Titelleiste, Seitenleiste und Kacheln."""
    th = r.height() * (0.16 if titel == "schlank" else 0.24)
    qp.setPen(Qt.PenStyle.NoPen)
    qp.setBrush(f("#000000", 70 * alpha / 255))
    qp.drawRoundedRect(r.translated(2, 3), rund, rund)
    qp.setBrush(f(p["flaeche"], alpha))
    qp.drawRoundedRect(r, rund, rund)
    if titel == "farbig":
        pfad = QPainterPath()
        pfad.addRoundedRect(QRectF(r.left(), r.top(), r.width(), th + rund), rund, rund)
        qp.setBrush(f(p["akzent"], alpha))
        qp.drawPath(pfad)
        qp.setBrush(f(p["flaeche"], alpha))
        qp.drawRect(QRectF(r.left(), r.top() + th, r.width(), rund))
    else:
        qp.setBrush(f(p["akzent"], alpha))
        qp.drawRect(QRectF(r.left() + rund * 0.6, r.top(), r.width() - rund * 1.2, max(1.5, r.height() * 0.025)))
    qp.setBrush(f(p["karte"], alpha))
    qp.drawRoundedRect(QRectF(r.left() + r.width() * 0.06, r.top() + th + r.height() * 0.08,
                              r.width() * 0.26, r.height() - th - r.height() * 0.16), 2, 2)
    for i in range(4):
        c, z = i % 2, i // 2
        qp.setBrush(f(p["akzent"], alpha * 0.8))
        qp.drawRoundedRect(QRectF(r.left() + r.width() * (0.40 + c * 0.29), r.top() + th + r.height() * (0.10 + z * 0.33),
                                  r.width() * 0.22, r.height() * 0.24), 2, 2)
    return th


def leiste(qp, B, p, hoehe=0.17):
    """Taskleiste unten im Bildschirm B."""
    lr = QRectF(B.left(), B.bottom() - B.height() * hoehe, B.width(), B.height() * hoehe)
    qp.setPen(Qt.PenStyle.NoPen)
    qp.setBrush(f(p["flaeche"]))
    qp.drawRect(lr)
    return lr


def bildschirm(qp, B, p):
    qp.setPen(QPen(f(p["rand"]), 1))
    qp.setBrush(f(p["grund"]))
    qp.drawRoundedRect(B, 4, 4)


def symbol(qp, r, p, i, aktiv=False):
    qp.setPen(Qt.PenStyle.NoPen)
    farben = [p["akzent"], p["akzent2"], "#2b8a6e", "#e05a3a", "#a77be0"]
    qp.setBrush(f(farben[i % len(farben)], 255 if aktiv else 200))
    qp.drawRoundedRect(r, r.width() * 0.25, r.width() * 0.25)


# ====================================================================== Miniaturen

def zeichnen(qp, s, w, R, p, t):
    """Miniatur fuer Schluessel s mit Wert w ins Rechteck R; t = Phase 0..1 fuer Bewegung."""
    qp.save()
    qp.setClipRect(R)
    fn = MINIATUREN.get(s)
    if fn:
        fn(qp, w, R, p, t)
    qp.restore()


def m_knoepfe(qp, w, R, p, t):
    r = QRectF(R.left() + R.width() * 0.08, R.top() + R.height() * 0.18, R.width() * 0.84, R.height() * 0.7)
    fenster(qp, r, p, 5)
    rad = R.height() * 0.11
    for i, z in enumerate(["-", "+", "x"]):
        cx = r.right() - rad * 1.6 - (2 - i) * rad * 2.5
        KNOPF(qp, w, cx, r.top() + r.height() * 0.13, rad, p["knopf_ruhe"], p["akzent"], z, z == "x", p["gefahr"])


def m_titelleiste(qp, w, R, p, t):
    fenster(qp, R.adjusted(R.width() * 0.1, R.height() * 0.12, -R.width() * 0.1, -R.height() * 0.08), p, 5, w)


def m_ecken(qp, w, R, p, t):
    rund = R.height() * 0.28 if w == "rund" else 1.5
    r = QRectF(R.left() + R.width() * 0.22, R.top() + R.height() * 0.18, R.width() * 0.9, R.height() * 1.1)
    qp.setPen(QPen(f(p["akzent"]), 2))
    qp.setBrush(f(p["flaeche"]))
    qp.drawRoundedRect(r, rund, rund)


def _fenster_animiert(qp, R, p, alpha=255, skala=1.0, dx=0.0, dy=0.0, dreh=0.0, stufe=1.0):
    basis = QRectF(R.center().x() - R.width() * 0.32, R.center().y() - R.height() * 0.32, R.width() * 0.64, R.height() * 0.64)
    qp.save()
    qp.translate(basis.center().x() + dx * R.width(), basis.center().y() + dy * R.height())
    qp.rotate(dreh)
    qp.scale(max(0.001, skala), max(0.001, skala))
    lokal = QRectF(-basis.width() / 2, -basis.height() / 2, basis.width(), basis.height())
    if stufe < 1.0:
        # Aufbauen/Abbauen: nur die oberen Streifen sind schon da
        qp.setClipRect(QRectF(lokal.left(), lokal.top(), lokal.width(), lokal.height() * stufe), Qt.ClipOperation.IntersectClip)
    fenster(qp, lokal, p, 4, alpha=int(alpha))
    qp.restore()


def _umriss(qp, R, p):
    """Gestrichelter Platz des Fensters, damit die Karte nie leer aussieht."""
    basis = QRectF(R.center().x() - R.width() * 0.32, R.center().y() - R.height() * 0.32, R.width() * 0.64, R.height() * 0.64)
    stift = QPen(f(p["rand"]), 1, Qt.PenStyle.DashLine)
    qp.setPen(stift)
    qp.setBrush(Qt.BrushStyle.NoBrush)
    qp.drawRoundedRect(basis, 4, 4)


def _verlauf(t):
    # kurz stehen, 0,45 Takte Bewegung, dann stehen
    return weich((t - 0.15) / 0.45)


def m_oeffnen(qp, w, R, p, t):
    _umriss(qp, R, p)
    u = _verlauf(t)
    if w == "bibi-pop":
        s = u + math.sin(u * math.pi) * 0.18
        _fenster_animiert(qp, R, p, 255 * u, 0.3 + 0.7 * s)
    elif w == "hochgleiten":
        _fenster_animiert(qp, R, p, 255 * u, 1.0, 0, 0.35 * (1 - u))
    elif w == "aufbauen":
        _fenster_animiert(qp, R, p, 255, 1.0, stufe=math.ceil(u * 5) / 5)
    elif w == "einblenden":
        _fenster_animiert(qp, R, p, 255 * u)
    else:
        _fenster_animiert(qp, R, p, 255 if t > 0.4 else 0)


def m_schliessen(qp, w, R, p, t):
    _umriss(qp, R, p)
    u = _verlauf(t)
    if w == "zusammenziehen":
        _fenster_animiert(qp, R, p, 255 * (1 - u * 0.6), 1.0 - u)
    elif w == "wegfallen":
        _fenster_animiert(qp, R, p, 255 * (1 - u), 1.0 - u * 0.2, 0, u * u * 0.6, u * 18)
    elif w == "abbauen":
        _fenster_animiert(qp, R, p, 255, 1.0, stufe=1 - math.floor(u * 5) / 5)
    elif w == "ausblenden":
        _fenster_animiert(qp, R, p, 255 * (1 - u))
    else:
        _fenster_animiert(qp, R, p, 0 if t > 0.4 else 255)


def m_minimieren(qp, w, R, p, t):
    lr = QRectF(R.left(), R.bottom() - R.height() * 0.14, R.width(), R.height() * 0.14)
    qp.setPen(Qt.PenStyle.NoPen)
    qp.setBrush(f(p["flaeche"]))
    qp.drawRect(lr)
    symbol(qp, QRectF(R.center().x() - lr.height() * 0.35, lr.top() + lr.height() * 0.15, lr.height() * 0.7, lr.height() * 0.7), p, 0)
    _umriss(qp, R, p)
    u = _verlauf(t)
    if w == "fliegen":
        _fenster_animiert(qp, R, p, 255, 1.0 - u * 0.92, 0, u * 0.42)
    elif w == "wabern":
        qp.save()
        basis = QRectF(R.center().x() - R.width() * 0.32, R.center().y() - R.height() * 0.32, R.width() * 0.64, R.height() * 0.64)
        qp.translate(basis.center().x(), basis.center().y() + u * R.height() * 0.42)
        qp.setTransform(QTransform().shear(math.sin(u * math.pi * 3) * 0.35 * (1 - u), 0), True)
        qp.scale(1 - u * 0.85, 1 - u * 0.92)
        fenster(qp, QRectF(-basis.width() / 2, -basis.height() / 2, basis.width(), basis.height()), p, 4)
        qp.restore()
    else:
        _fenster_animiert(qp, R, p, 255 * (1 - u))


def m_arbeitsflaechen(qp, w, R, p, t):
    n = 1 if w == "eine" else 2
    gross = min(R.width(), R.height() * 1.6) * (0.62 if n == 1 else 0.36)
    for i in range(n * n):
        c, z = i % n, i // n
        B = QRectF(R.center().x() - n * gross / 2 - (n - 1) * 3 + c * (gross + 6),
                   R.center().y() - n * gross / 3.2 - (n - 1) * 3 + z * (gross / 1.6 + 6), gross, gross / 1.6)
        bildschirm(qp, B, p)
        if i == 0:
            qp.setBrush(f(p["akzent"], 180))
            qp.setPen(Qt.PenStyle.NoPen)
            qp.drawRoundedRect(B.adjusted(B.width() * 0.2, B.height() * 0.2, -B.width() * 0.3, -B.height() * 0.3), 2, 2)


def m_wechsel(qp, w, R, p, t):
    B = QRectF(R.center().x() - R.width() * 0.3, R.center().y() - R.height() * 0.32, R.width() * 0.6, R.height() * 0.64)
    u = weich((t % 0.5) / 0.4)
    a, b = (p["akzent"], p["akzent2"]) if t < 0.5 else (p["akzent2"], p["akzent"])
    qp.setPen(Qt.PenStyle.NoPen)
    if w == "gleiten":
        qp.save()
        qp.setClipRect(B)
        qp.setBrush(f(a))
        qp.drawRect(B.translated(-B.width() * u, 0))
        qp.setBrush(f(b))
        qp.drawRect(B.translated(B.width() * (1 - u), 0))
        qp.restore()
    elif w == "ueberblenden":
        qp.setBrush(f(a))
        qp.drawRect(B)
        qp.setBrush(f(b, 255 * u))
        qp.drawRect(B)
    else:
        # Wuerfel: zwei Seiten, die um die senkrechte Achse drehen (die hintere Kante ist kuerzer)
        winkel = u * math.pi / 2
        b1, b2 = B.width() * math.cos(winkel), B.width() * math.sin(winkel)
        x = B.center().x() - (b1 + b2) / 2
        tief = B.height() * 0.14
        if b1 > 1:
            o = tief * math.sin(winkel)
            qp.setBrush(f(a))
            qp.drawPolygon(QPolygonF([QPointF(x, B.top() + o), QPointF(x + b1, B.top()),
                                      QPointF(x + b1, B.bottom()), QPointF(x, B.bottom() - o)]))
        if b2 > 1:
            o = tief * math.cos(winkel)
            qp.setBrush(f(b))
            qp.drawPolygon(QPolygonF([QPointF(x + b1, B.top()), QPointF(x + b1 + b2, B.top() + o),
                                      QPointF(x + b1 + b2, B.bottom() - o), QPointF(x + b1, B.bottom())]))


def m_overlay(qp, w, R, p, t):
    qp.setPen(Qt.PenStyle.NoPen)
    qp.setBrush(f("#1b2a1d"))
    qp.drawRoundedRect(R.adjusted(4, 6, -4, -6), 4, 4)
    qp.setBrush(f("#3c6b3f"))
    qp.drawPolygon(QPolygonF([QPointF(R.left() + 4, R.bottom() - 6), QPointF(R.center().x() - 10, R.center().y()),
                              QPointF(R.center().x() + 14, R.bottom() - 18), QPointF(R.right() - 4, R.center().y() + 4),
                              QPointF(R.right() - 4, R.bottom() - 6)]))
    if w == "aus":
        return
    zeilen = 4 if w == "ausfuehrlich" else 1
    box = QRectF(R.left() + 9, R.top() + 10, R.width() * (0.42 if zeilen > 1 else 0.7), 8 + zeilen * 8)
    qp.setBrush(f("#000000", 170))
    qp.drawRoundedRect(box, 3, 3)
    for i in range(zeilen):
        qp.setBrush(f(p["akzent"] if i == 0 else p["text"], 230 if i == 0 else 140))
        lang = box.width() * (0.75 if zeilen > 1 else 0.88) * (1 - 0.15 * (i % 2))
        qp.drawRoundedRect(QRectF(box.left() + 5, box.top() + 5 + i * 8, lang, 4), 2, 2)


def m_leiste_stil(qp, w, R, p, t):
    B = R.adjusted(6, 8, -6, -6)
    bildschirm(qp, B, p)
    h = B.height() * 0.36
    y = B.bottom() - h
    qp.setPen(Qt.PenStyle.NoPen)
    if w != "inseln":
        qp.setBrush(f(p["flaeche"]))
        qp.drawRect(QRectF(B.left() + 1, y, B.width() - 2, h - 1))
    g = h * 0.56
    blau = QColor("#378add")
    sx = B.left() + 5
    if w == "inseln":
        qp.setBrush(f(p["flaeche"]))
        qp.drawRoundedRect(QRectF(sx - 2, y + 1, g + 4, h - 3), 4, 4)
        qp.drawRoundedRect(QRectF(B.center().x() - g * 2.4, y + 1, g * 4.8, h - 3), 4, 4)
        qp.drawRoundedRect(QRectF(B.right() - g * 2.8, y + 1, g * 2.6, h - 3), 4, 4)
    # Startknopf
    qp.setBrush(blau if w != "klassisch" else f(p["akzent"]))
    kr = QRectF(sx, y + (h - g) / 2, g, g)
    if w == "typenschild":
        qp.drawEllipse(kr)
    else:
        qp.drawRoundedRect(kr, g * 0.25, g * 0.25)
    ax = B.center().x() - g * 2 if w == "inseln" else sx + g + 7
    for i in range(3):
        r = QRectF(ax + i * (g + 4), y + (h - g) / 2, g, g)
        if w == "typenschild":
            qp.setPen(QPen(f(p["akzent2"] if i == 1 else p["rand"]), 1))
            qp.setBrush(f(p["karte"]))
            qp.drawRoundedRect(r, 2, 2)
            qp.setPen(Qt.PenStyle.NoPen)
            symbol(qp, r.adjusted(2.5, 2.5, -2.5, -2.5), p, i, i == 1)
        else:
            symbol(qp, r, p, i, i == 1)
            if w != "klassisch":
                qp.setBrush(f(p["akzent"] if i == 1 else p["leise"]))
                bs = g * (0.9 if i == 1 else 0.45)
                qp.drawRect(QRectF(r.center().x() - bs / 2, B.bottom() - 3, bs, 1.6 if i == 1 else 1.2))
            elif i == 1:
                qp.setBrush(f(p["akzent"]))
                qp.drawRect(QRectF(r.left(), B.bottom() - 3, r.width(), 1.5))
    if w in ("zonen", "kopfzeile"):
        qp.setBrush(f(p["rand"]))
        qp.drawRect(QRectF(sx + g + 3, y + h * 0.25, 1, h * 0.5))
        qp.drawRect(QRectF(B.right() - g * 2.6, y + h * 0.25, 1, h * 0.5))
    if w == "kopfzeile":
        qp.setBrush(f(p["text"], 220))
        qp.drawRoundedRect(QRectF(ax + 3 * (g + 4) + 8, y + h * 0.26, g * 2.2, h * 0.18), 1, 1)
        qp.setBrush(f(p["leise"]))
        qp.drawRoundedRect(QRectF(ax + 3 * (g + 4) + 8, y + h * 0.56, g * 3.4, h * 0.12), 1, 1)
    # Uhr
    qp.setBrush(f(p["text"], 200))
    qp.drawRoundedRect(QRectF(B.right() - g * 1.9, y + h * 0.36, g * 1.5, h * 0.24), 1, 1)


def m_taskleiste(qp, w, R, p, t):
    B = R.adjusted(6, 8, -6, -6)
    bildschirm(qp, B, p)
    h = B.height() * 0.3
    qp.setPen(Qt.PenStyle.NoPen)
    qp.setBrush(f(p["flaeche"]))
    if w == "fest":
        lr = QRectF(B.left() + 1, B.bottom() - h, B.width() - 2, h - 1)
        qp.drawRect(lr)
    elif w == "dock":
        lr = QRectF(B.center().x() - B.width() * 0.26, B.bottom() - h - 4, B.width() * 0.52, h)
        qp.drawRoundedRect(lr, h * 0.4, h * 0.4)
    else:
        lr = QRectF(B.left() + 5, B.bottom() - h - 4, B.width() - 10, h)
        qp.drawRoundedRect(lr, h * 0.4, h * 0.4)
    g = h * 0.56
    for i in range(4 if w == "dock" else 3):
        x = (lr.center().x() - 2 * (g + 4) + i * (g + 4)) if w == "dock" else lr.left() + 5 + i * (g + 4)
        symbol(qp, QRectF(x, lr.top() + (h - g) / 2, g, g), p, i)


def m_transparenz(qp, w, R, p, t):
    B = R.adjusted(6, 8, -6, -6)
    qp.setPen(Qt.PenStyle.NoPen)
    # Hintergrund mit Motiv, damit man das Durchscheinen sieht
    qp.setBrush(f(p["grund"]))
    qp.drawRoundedRect(B, 4, 4)
    for i in range(5):
        qp.setBrush(f(p["akzent"] if i % 2 else p["akzent2"], 150))
        qp.drawEllipse(QPointF(B.left() + B.width() * (0.1 + i * 0.2), B.bottom() - B.height() * 0.2), B.height() * 0.28, B.height() * 0.28)
    alpha = {"undurchsichtig": 255, "milchglas": 185, "adaptiv": 120}[w]
    lr = QRectF(B.left() + 4, B.bottom() - B.height() * 0.4, B.width() - 8, B.height() * 0.32)
    qp.setBrush(f(p["flaeche"], alpha))
    qp.drawRoundedRect(lr, 4, 4)
    if w == "adaptiv":
        schrift(qp, 9)
        qp.setPen(f(p["text"]))
        qp.drawText(lr, Qt.AlignmentFlag.AlignCenter, "je nach Fenster")


def m_monitore(qp, w, R, p, t):
    bw = R.width() * 0.42
    for i in range(2):
        B = QRectF(R.left() + R.width() * 0.05 + i * (bw + R.width() * 0.06), R.top() + R.height() * 0.2, bw, bw * 0.62)
        bildschirm(qp, B, p)
        if w == "haupt" and i == 1:
            continue
        h = B.height() * 0.2
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(f(p["flaeche"]))
        qp.drawRect(QRectF(B.left() + 1, B.bottom() - h, B.width() - 2, h - 1))
        n = 3 if (w == "gleich" or i == 0) else 1
        for k in range(n):
            symbol(qp, QRectF(B.left() + 4 + k * h * 0.9, B.bottom() - h * 0.8, h * 0.6, h * 0.6), p, k + (i if w == "beide" else 0))


def m_startmenue(qp, w, R, p, t):
    B = R.adjusted(6, 6, -6, -6)
    bildschirm(qp, B, p)
    qp.setPen(Qt.PenStyle.NoPen)
    h = B.height() * 0.16
    qp.setBrush(f(p["flaeche"]))
    qp.drawRect(QRectF(B.left() + 1, B.bottom() - h, B.width() - 2, h - 1))
    qp.setBrush(QColor("#378add"))
    qp.drawRoundedRect(QRectF(B.left() + 4, B.bottom() - h * 0.8, h * 0.6, h * 0.6), 2, 2)
    if w == "vollbild":
        m = B.adjusted(6, 5, -6, -h - 4)
    elif w == "klassisch":
        m = QRectF(B.left() + 3, B.top() + B.height() * 0.18, B.width() * 0.34, B.height() * 0.62)
    else:
        m = QRectF(B.left() + 3, B.top() + B.height() * 0.12, B.width() * 0.52, B.height() * 0.68)
    qp.setBrush(f(p["karte"], 245))
    qp.drawRoundedRect(m, 3, 3)
    if w == "klassisch":
        for i in range(5):
            qp.setBrush(f(p["text"], 120 if i else 200))
            qp.drawRoundedRect(QRectF(m.left() + 4, m.top() + 4 + i * m.height() / 5.5, m.width() * 0.7, 2.5), 1, 1)
        return
    n = 6 if w == "vollbild" else 4
    g = m.width() / (n + 1.6)
    for i in range(n * 2):
        c, z = i % n, i // n
        symbol(qp, QRectF(m.left() + g * 0.8 + c * g, m.top() + m.height() * 0.3 + z * g * 1.15, g * 0.72, g * 0.72), p, i)
    qp.setBrush(f(p["text"], 180))
    qp.drawRoundedRect(QRectF(m.left() + g * 0.8, m.top() + m.height() * 0.1, m.width() * 0.4, 3), 1, 1)


def m_position(qp, w, R, p, t):
    B = R.adjusted(6, 8, -6, -6)
    bildschirm(qp, B, p)
    h = B.height() * 0.34
    qp.setPen(Qt.PenStyle.NoPen)
    qp.setBrush(f(p["flaeche"]))
    qp.drawRect(QRectF(B.left() + 1, B.bottom() - h, B.width() - 2, h - 1))
    g = h * 0.6
    x = B.left() + 6 if w == "links" else B.center().x() - g * 2
    qp.setBrush(QColor("#378add"))
    qp.drawRoundedRect(QRectF(x, B.bottom() - h + (h - g) / 2, g, g), 3, 3)
    for i in range(3):
        symbol(qp, QRectF(x + (i + 1) * (g + 4), B.bottom() - h + (h - g) / 2, g, g), p, i)


def m_startknopf(qp, w, R, p, t):
    g = R.height() * 0.5
    r = QRectF(R.center().x() - g / 2, R.center().y() - g / 2, g, g)
    qp.setPen(Qt.PenStyle.NoPen)
    if w == "biblix":
        qp.setBrush(QColor("#378add"))
        qp.drawRoundedRect(r, g * 0.24, g * 0.24)
        schrift(qp, g * 0.56, fett=True)
        qp.setPen(QColor("#ffffff"))
        qp.drawText(r, Qt.AlignmentFlag.AlignCenter, "B")
    else:
        qp.setBrush(f(p["akzent2"]))
        qp.drawEllipse(r)
        qp.setBrush(f(p["grund"]))
        qp.drawEllipse(r.adjusted(g * 0.22, g * 0.22, -g * 0.22, -g * 0.22))
        qp.setBrush(f(p["akzent"]))
        qp.drawEllipse(r.adjusted(g * 0.36, g * 0.36, -g * 0.36, -g * 0.36))


def m_symbole(qp, w, R, p, t):
    g = R.height() * 0.42
    for i in range(3):
        r = QRectF(R.center().x() - g * 1.7 + i * g * 1.2, R.center().y() - g / 2, g, g)
        if w == "kacheln":
            qp.setPen(Qt.PenStyle.NoPen)
            qp.setBrush(f(p["akzent"]))
            qp.drawRoundedRect(r, g * 0.24, g * 0.24)
            qp.setPen(QPen(f(p["auf_akzent"]), 1.6))
        else:
            qp.setPen(QPen(f(p["akzent"] if w == "flach" else p["text"]), 2.0 if w == "flach" else 1.2))
        qp.setBrush(Qt.BrushStyle.NoBrush)
        inner = r.adjusted(g * 0.26, g * 0.26, -g * 0.26, -g * 0.26)
        if i == 0:
            qp.drawRect(QRectF(inner.left(), inner.top() + inner.height() * 0.2, inner.width(), inner.height() * 0.8))
        elif i == 1:
            qp.drawPolyline(QPolygonF([QPointF(inner.left(), inner.top() + inner.height() * 0.2), QPointF(inner.center().x(), inner.center().y()),
                                       QPointF(inner.left(), inner.bottom() - inner.height() * 0.2)]))
            qp.drawLine(QPointF(inner.center().x(), inner.bottom()), QPointF(inner.right(), inner.bottom()))
        else:
            for k in range(3):
                x = inner.left() + k * inner.width() / 2
                qp.drawLine(QPointF(x, inner.top()), QPointF(x, inner.bottom()))


def m_tray(qp, w, R, p, t):
    g = R.height() * 0.3
    y = R.center().y()
    for i in range(3):
        cx = R.center().x() - g * 1.4 + i * g * 1.4
        if w == "schrauben":
            qp.setPen(QPen(f(p["akzent"]), 1.6))
            qp.setBrush(Qt.BrushStyle.NoBrush)
            qp.drawPolygon(sechseck(cx, y, g * 0.55))
            qp.setPen(QPen(f(p["text"]), 1.4))
        else:
            qp.setPen(QPen(f(p["text"]), 1.4))
        # Lautsprecher, Netz, Bluetooth stark vereinfacht
        if i == 0:
            qp.drawLine(QPointF(cx - g * 0.2, y), QPointF(cx + g * 0.2, y - g * 0.2))
            qp.drawLine(QPointF(cx - g * 0.2, y), QPointF(cx + g * 0.2, y + g * 0.2))
        elif i == 1:
            for k in range(3):
                qp.drawLine(QPointF(cx - g * 0.25 + k * g * 0.25, y + g * 0.25), QPointF(cx - g * 0.25 + k * g * 0.25, y + g * 0.25 - (k + 1) * g * 0.16))
        else:
            qp.drawPolyline(QPolygonF([QPointF(cx - g * 0.18, y - g * 0.15), QPointF(cx + g * 0.18, y + g * 0.15),
                                       QPointF(cx, y + g * 0.3), QPointF(cx, y - g * 0.3), QPointF(cx + g * 0.18, y - g * 0.15),
                                       QPointF(cx - g * 0.18, y + g * 0.15)]))


def m_zeiger(qp, w, R, p, t):
    k = R.height() / 36
    mx, my = R.center().x() - 6 * k, R.center().y() - 12 * k
    qp.setPen(QPen(QColor("#0b0d12") if w == "biblix" else QColor("#000000"), 1.6))
    qp.setBrush(f(p["akzent"]) if w == "biblix" else QColor("#ffffff"))
    qp.drawPolygon(QPolygonF([QPointF(mx, my), QPointF(mx, my + 22 * k), QPointF(mx + 5 * k, my + 17 * k),
                              QPointF(mx + 9 * k, my + 25 * k), QPointF(mx + 12.5 * k, my + 23.5 * k),
                              QPointF(mx + 9 * k, my + 16 * k), QPointF(mx + 16 * k, my + 16 * k)]))


def m_ladezeiger(qp, w, R, p, t):
    cx, cy, g = R.center().x(), R.center().y(), R.height() * 0.24
    if w == "mutter":
        qp.setPen(QPen(f(p["akzent"]), 3))
        qp.setBrush(Qt.BrushStyle.NoBrush)
        qp.drawPolygon(sechseck(cx, cy, g, t * 360))
        qp.drawEllipse(QPointF(cx, cy), g * 0.38, g * 0.38)
    elif w == "cursor":
        schrift(qp, g * 1.3, fett=True, mono=True)
        qp.setPen(f(p["akzent"]))
        qp.drawText(QRectF(cx - g * 1.5, cy - g, g * 2, g * 2), Qt.AlignmentFlag.AlignCenter, ">")
        if (t * 4) % 1 < 0.6:
            qp.fillRect(QRectF(cx + g * 0.4, cy - g * 0.5, g * 0.7, g * 1.1), f(p["akzent"]))
    else:
        for i in range(3):
            an = (t * 3 - i * 0.35) % 1.0 < 0.75
            qp.setPen(Qt.PenStyle.NoPen)
            qp.setBrush(f(p["akzent"], 230 if an else 60))
            qp.drawRoundedRect(QRectF(cx - g, cy - g + i * g * 0.75, g * 2, g * 0.55), 3, 3)


def m_klaenge(qp, w, R, p, t):
    y = R.center().y()
    qp.setPen(Qt.PenStyle.NoPen)
    qp.setBrush(f(p["text"], 200))
    x0 = R.left() + R.width() * 0.12
    g = R.height() * 0.16
    qp.drawPolygon(QPolygonF([QPointF(x0, y - g * 0.6), QPointF(x0 + g * 0.6, y - g * 0.6), QPointF(x0 + g * 1.4, y - g * 1.3),
                              QPointF(x0 + g * 1.4, y + g * 1.3), QPointF(x0 + g * 0.6, y + g * 0.6), QPointF(x0, y + g * 0.6)]))
    links = x0 + g * 2.2
    if w == "aus":
        qp.setPen(QPen(f(p["gefahr"]), 2.4))
        qp.drawLine(QPointF(links + 4, y - g), QPointF(links + 4 + 2 * g, y + g))
        qp.drawLine(QPointF(links + 4, y + g), QPointF(links + 4 + 2 * g, y - g))
        return
    breite = R.right() - links - R.width() * 0.08
    farbe = {"preset": p["akzent2"], "biblix": p["akzent"], "retro": "#6fe36f", "ruhig": p["leise"]}[w]
    hoch = {"preset": 1.0, "biblix": 0.9, "retro": 0.8, "ruhig": 0.35}[w]
    qp.setPen(QPen(f(farbe), 2))
    pts = []
    for i in range(61):
        x = i / 60
        if w == "retro":
            v = 1 if math.sin((x * 6 + t) * 2 * math.pi) > 0 else -1
        elif w == "preset":
            v = math.sin((x * 3 + t) * 2 * math.pi) * 0.6 + math.sin((x * 9 + t * 2) * 2 * math.pi) * 0.4
        else:
            v = math.sin((x * (4 if w == "biblix" else 2) + t) * 2 * math.pi)
        huelle = math.sin(x * math.pi)
        pts.append(QPointF(links + x * breite, y - v * huelle * hoch * R.height() * 0.3))
    qp.drawPolyline(QPolygonF(pts))


def m_sperrbildschirm(qp, w, R, p, t):
    B = R.adjusted(6, 6, -6, -6)
    qp.setPen(Qt.PenStyle.NoPen)
    qp.setBrush(f("#04110a") if w == "terminal" else f(p["grund"]))
    qp.drawRoundedRect(B, 4, 4)
    if w == "terminal":
        schrift(qp, B.height() * 0.13, mono=True)
        qp.setPen(QColor("#6fe36f"))
        qp.drawText(B.adjusted(6, 4, 0, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, "bibi@biblix:~$\n> passwort_")
        return
    schrift(qp, B.height() * (0.32 if w == "schlicht" else 0.26), fett=True)
    qp.setPen(f(p["text"]))
    qp.drawText(QRectF(B.left(), B.top() + B.height() * 0.1, B.width(), B.height() * 0.45), Qt.AlignmentFlag.AlignCenter, "18:42")
    if w == "bibi":
        g = B.height() * 0.22
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QColor("#378add"))
        qp.drawRoundedRect(QRectF(B.center().x() - g / 2, B.bottom() - g - 6, g, g), 3, 3)
        qp.setBrush(f(p["karte"]))
        qp.drawRoundedRect(QRectF(B.left() + B.width() * 0.25, B.bottom() - g * 2.1 - 6, B.width() * 0.5, g * 0.7), 3, 3)


def m_ladeanimation(qp, w, R, p, t):
    cx, cy, g = R.center().x(), R.center().y(), R.height() * 0.3
    qp.setPen(Qt.PenStyle.NoPen)
    if w == "tippen":
        text = ">B"[:1 + int(min(1.0, t * 2.5) * 1.99)]
        schrift(qp, g * 1.5, fett=True, mono=True)
        qp.setPen(f(p["akzent"]))
        qp.drawText(QRectF(cx - g * 1.5, cy - g, g * 3, g * 2), Qt.AlignmentFlag.AlignCenter, text + ("_" if (t * 4) % 1 < 0.5 else " "))
    elif w == "schrauben":
        for i in range(3):
            winkel = t * 360 + i * 40
            qp.setPen(QPen(f(p["akzent"]), 2))
            qp.setBrush(Qt.BrushStyle.NoBrush)
            qp.drawPolygon(sechseck(cx - g * 1.2 + i * g * 1.2, cy, g * 0.45, winkel))
    else:
        schrift(qp, g * 1.7, fett=True)
        qp.setPen(f(p["akzent"], 255 * (0.5 + 0.5 * math.sin(t * 2 * math.pi))))
        qp.drawText(QRectF(cx - g, cy - g, g * 2, g * 2), Qt.AlignmentFlag.AlignCenter, "B")


MINIATUREN = {
    "knoepfe": m_knoepfe, "titelleiste": m_titelleiste, "ecken": m_ecken,
    "effekt_oeffnen": m_oeffnen, "effekt_schliessen": m_schliessen, "effekt_minimieren": m_minimieren,
    "arbeitsflaechen": m_arbeitsflaechen, "arbeitsflaeche": m_wechsel, "overlay": m_overlay,
    "leiste_stil": m_leiste_stil, "taskleiste": m_taskleiste, "transparenz": m_transparenz, "monitore": m_monitore,
    "startmenue": m_startmenue, "startmenue_position": m_position, "startknopf": m_startknopf,
    "symbole": m_symbole, "tray": m_tray, "zeiger": m_zeiger, "ladezeiger": m_ladezeiger,
    "klaenge": m_klaenge, "sperrbildschirm": m_sperrbildschirm, "ladeanimation": m_ladeanimation,
}


# ====================================================================== Karte

class _Takt:
    """Ein gemeinsamer Takt fuer alle bewegten Karten."""
    karten = set()
    timer = None

    @classmethod
    def an(cls, karte):
        cls.karten.add(karte)
        if cls.timer is None:
            cls.timer = QTimer()
            cls.timer.timeout.connect(cls._tick)
            cls.timer.start(40)

    @classmethod
    def ab(cls, karte):
        cls.karten.discard(karte)

    @classmethod
    def _tick(cls):
        for k in list(cls.karten):
            try:
                k.phase = (k.phase + 0.018) % 1.0
                k.update()
            except RuntimeError:
                cls.karten.discard(k)


class Musterkarte(QAbstractButton):
    """Eine Auswahl als Karte: oben die Miniatur, unten der Name (umbricht statt abzuschneiden)."""
    ueber = pyqtSignal(str, object, bool)

    def __init__(self, schluessel, wert, name, palette):
        super().__init__()
        self.schluessel, self.wert, self.name, self.p = schluessel, wert, name, palette
        self.setCheckable(True)
        self.setToolTip(name)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(96)
        self.setFixedHeight(118)
        self.phase = 0.0
        self.drin = False
        if schluessel in BEWEGT:
            _Takt.an(self)
        self.destroyed.connect(lambda *_: None)

    def sizeHint(self):
        return QSize(150, 118)

    def hideEvent(self, ev):
        _Takt.ab(self)
        super().hideEvent(ev)

    def showEvent(self, ev):
        if self.schluessel in BEWEGT:
            _Takt.an(self)
        super().showEvent(ev)

    def enterEvent(self, ev):
        self.drin = True
        self.ueber.emit(self.schluessel, self.wert, True)
        self.update()

    def leaveEvent(self, ev):
        self.drin = False
        self.ueber.emit(self.schluessel, self.wert, False)
        self.update()

    def paintEvent(self, ev):
        p = self.p
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        an = self.isChecked()
        qp.setPen(QPen(f(p["akzent"]) if an else f(p["rand"], 255 if self.drin else 160), 2 if an else 1))
        qp.setBrush(f(p["karte"]) if (an or self.drin) else f(p["flaeche"]))
        qp.drawRoundedRect(r, 10, 10)
        bild = QRectF(r.left() + 6, r.top() + 6, r.width() - 12, 70)
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(f(p["grund"], 200))
        qp.drawRoundedRect(bild, 7, 7)
        zeichnen(qp, self.schluessel, self.wert, bild, p, self.phase)
        # Haken in der Ecke
        if an:
            hk = QRectF(r.right() - 22, r.top() + 4, 18, 18)
            qp.setPen(Qt.PenStyle.NoPen)
            qp.setBrush(f(p["akzent"]))
            qp.drawEllipse(hk)
            qp.setPen(QPen(f(p["auf_akzent"]), 2))
            qp.drawPolyline(QPolygonF([QPointF(hk.left() + 4.5, hk.center().y()), QPointF(hk.left() + 7.5, hk.bottom() - 5),
                                       QPointF(hk.right() - 4, hk.top() + 5)]))
        schrift(qp, 12, fett=an)
        qp.setPen(f(p["text"]) if an else f(p["text"], 215))
        qp.drawText(QRectF(r.left() + 4, bild.bottom() + 3, r.width() - 8, r.bottom() - bild.bottom() - 4),
                    Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.name)
        qp.end()
