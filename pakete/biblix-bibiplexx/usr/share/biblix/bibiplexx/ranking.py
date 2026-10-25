"""Bibiplexx-Ranking: eigene Sterne, Tierlist und Top 10 fuer Serien und Filme.

Gespeichert wird in ~/.local/state/bibiplexx/ranking.json, unabhaengig von TMDB.
Serien zaehlen als Ganzes ("serie|Name"), Filme einzeln ("film|Titel|Jahr").
"""
import time
from pathlib import Path

from PyQt6.QtCore import QMimeData, QPoint, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QDrag, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFrame, QHBoxLayout, QLineEdit, QMenu, QMessageBox, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)

import bibiplexx as bp

DATEI = bp.ZUSTAND / "ranking.json"
MIME = "application/x-bibiplexx-titel"
TOP = 10
STERNE = 5

# Buchstabe, Spruch, Farbe
TIERS = [
    ("S", "Reihe sieben", "#ff4d9d"),
    ("A", "Salziges Popcorn", "#ff8a00"),
    ("B", "Läuft", "#ffd23f"),
    ("C", "Nebenbei am Handy", "#9d6bff"),
    ("D", "Im Saal eingeschlafen", "#6b6082"),
]
PLATZ_FARBE = {1: "#ffd23f", 2: "#d4cde6", 3: "#d08a4a"}
ARTEN = {"serie": "Serien", "film": "Filme"}


def schluessel(e, serie=None):
    if serie or e["art"] == "serie":
        return "serie|" + (serie or e["serie"])
    return f"film|{e['titel']}|{e.get('jahr') or ''}"


def art_von(k):
    return k.split("|", 1)[0]


class Ranking:
    def __init__(self):
        d = bp.json_lesen(DATEI, {})
        self.noten = {k: int(v) for k, v in (d.get("noten") or {}).items() if str(v).isdigit()}
        self.tiers = {t: list((d.get("tiers") or {}).get(t, [])) for t, _, _ in TIERS}
        self.top = {a: list((d.get("top") or {}).get(a, []))[:TOP] for a in ARTEN}

    def speichern(self):
        bp.json_schreiben(DATEI, {"noten": self.noten, "tiers": self.tiers, "top": self.top, "zeit": time.time()})

    def tier_von(self, k):
        return next((t for t, liste in self.tiers.items() if k in liste), None)

    def tier_setzen(self, k, tier, vor=None):
        """In eine Reihe legen (vor einem anderen Titel oder ans Ende); tier None = herausnehmen."""
        if vor == k:
            return
        for liste in self.tiers.values():
            if k in liste:
                liste.remove(k)
        if tier:
            liste = self.tiers[tier]
            liste.insert(liste.index(vor) if vor in liste else len(liste), k)
        self.speichern()

    def note_setzen(self, k, n):
        if n:
            self.noten[k] = n
        else:
            self.noten.pop(k, None)
        self.speichern()

    def ist_top(self, k):
        return k in self.top[art_von(k)]

    def top_umschalten(self, k):
        liste = self.top[art_von(k)]
        if k in liste:
            liste.remove(k)
        elif len(liste) < TOP:
            liste.append(k)
        else:
            return False
        self.speichern()
        return True

    def top_schieben(self, k, schritt):
        liste = self.top[art_von(k)]
        i = liste.index(k)
        j = max(0, min(len(liste) - 1, i + schritt))
        liste[i], liste[j] = liste[j], liste[i]
        self.speichern()

    def leeren(self):
        self.noten, self.tiers, self.top = {}, {t: [] for t, _, _ in TIERS}, {a: [] for a in ARTEN}
        self.speichern()


def titel_liste(haupt):
    """Alles aus der Sammlung: {schluessel: (art, name, eintrag)} – Serien als Ganzes."""
    alle = {}
    for name, folgen in haupt.serien().items():
        alle[schluessel(folgen[0], name)] = ("serie", name, folgen[0])
    for e in haupt.filme():
        alle[schluessel(e)] = ("film", e["titel"] + (f" ({e['jahr']})" if e.get("jahr") else ""), e)
    return alle


def sterne_text(n):
    return "★" * n


# ---------------------------------------------------------------- Bausteine

class Kachel(QWidget):
    """Poster im 2:3-Format (TMDB-Poster oder Standbild mit Titel); ziehbar fuer die Tierlist."""
    geklickt = pyqtSignal()

    def __init__(self, haupt, k, name, e, breite=96, ziehbar=True):
        super().__init__()
        self.haupt, self.k, self.name, self.e = haupt, k, name, e
        self.ziehbar = ziehbar
        self.druck = None
        self.hover = False
        self.setFixedSize(breite, round(breite * 1.5))
        self.setCursor(Qt.CursorShape.OpenHandCursor if ziehbar else Qt.CursorShape.PointingHandCursor)
        self.setToolTip(name)
        haupt.tmdb.neu.connect(self._neu)
        haupt.bilder.neu.connect(self._neu)

    def _neu(self, *_):
        if bp.alive(self):
            self.update()

    def enterEvent(self, _):
        self.hover = True
        self.update()

    def leaveEvent(self, _):
        self.hover = False
        self.update()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.druck = ev.position().toPoint()

    def mouseMoveEvent(self, ev):
        if not self.ziehbar or self.druck is None:
            return
        if (ev.position().toPoint() - self.druck).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MIME, self.k.encode())
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.setHotSpot(self.druck)
        self.druck = None
        haupt = self.haupt
        drag.exec(Qt.DropAction.MoveAction)
        if getattr(haupt, "ranking_geaendert", False):
            haupt.ranking_geaendert = False
            QTimer.singleShot(0, lambda: neu_zeigen(haupt))

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and self.druck is not None:
            self.druck = None
            self.geklickt.emit()

    def contextMenuEvent(self, ev):
        menue(self.haupt, self.k, ev.globalPos())

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = QRectF(1, 1, self.width() - 2, self.height() - 2)
        poster = self.haupt.tmdb.poster(self.e)
        bp.bild_fuellen(p, r, poster if poster is not None else self.haupt.bilder.pixmap(self.e), 8)
        if poster is None and self.width() >= 70:
            pfad = QPainterPath()
            pfad.addRoundedRect(r, 8, 8)
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            g.setColorAt(0, QColor(7, 7, 12, 60))
            g.setColorAt(1, QColor(7, 7, 12, 235))
            p.fillPath(pfad, g)
            p.setPen(QColor(bp.F["text"]))
            f = QFont(self.font())
            f.setBold(True)
            f.setPointSizeF(f.pointSizeF() * (0.85 if self.width() < 90 else 0.95))
            p.setFont(f)
            p.drawText(r.adjusted(6, 6, -6, -6), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter
                       | Qt.TextFlag.TextWordWrap, self.name)
        n = self.haupt.ranking.noten.get(self.k)
        if n and self.width() >= 80:
            f = QFont(self.font())
            f.setPointSizeF(f.pointSizeF() * 0.8)
            p.setFont(f)
            text = sterne_text(n)
            w = p.fontMetrics().horizontalAdvance(text) + 10
            br = QRectF(r.left() + 5, r.top() + 5, w, 18)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(7, 7, 12, 210))
            p.drawRoundedRect(br, 9, 9)
            p.setPen(QColor(bp.F["pink"]))
            p.drawText(br, Qt.AlignmentFlag.AlignCenter, text)
        p.setPen(QPen(QColor(bp.F["pink"] if self.hover else bp.F["rand"]), 2 if self.hover else 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(r, 8, 8)
        p.end()


class Sterne(QWidget):
    """Fuenf Sterne zum Anklicken; nochmal auf denselben Stern = Bewertung weg."""
    gesetzt = pyqtSignal(int)

    def __init__(self, n=0, groesse=22):
        super().__init__()
        self.n, self.vorschau, self.g = n, 0, groesse
        self.setFixedSize(groesse * STERNE + 4, groesse + 6)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Deine Bewertung")

    def _stern(self, x):
        return max(1, min(STERNE, int(x // self.g) + 1))

    def mouseMoveEvent(self, ev):
        self.vorschau = self._stern(ev.position().x())
        self.update()

    def leaveEvent(self, _):
        self.vorschau = 0
        self.update()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            s = self._stern(ev.position().x())
            self.n = 0 if s == self.n else s
            self.gesetzt.emit(self.n)
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        f = QFont(self.font())
        f.setPixelSize(self.g)
        p.setFont(f)
        zeige = self.vorschau or self.n
        for i in range(STERNE):
            p.setPen(QColor(bp.F["pink"] if i < zeige else bp.F["rand"]))
            if self.vorschau and i < zeige:
                p.setPen(QColor(bp.F["orange"]))
            p.drawText(QRectF(i * self.g, 0, self.g, self.g + 4), Qt.AlignmentFlag.AlignCenter, "★")
        p.end()


class TierFeld(QWidget):
    """Ablage einer Tierlist-Reihe (oder "Noch nicht eingeordnet"): nimmt gezogene Poster an."""

    def __init__(self, haupt, tier, farbe):
        super().__init__()
        self.haupt, self.tier, self.farbe = haupt, tier, farbe
        self.kacheln = []
        self.drueber = False
        self.setAcceptDrops(True)
        self.setMinimumHeight(round(84 * 1.5) + 16)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.fl = bp.FlowLayout(self, abstand=8)
        self.fl.setContentsMargins(8, 8, 8, 8)

    def hinzu(self, kachel):
        self.kacheln.append(kachel)
        self.fl.addWidget(kachel)

    def dragEnterEvent(self, ev):
        if ev.mimeData().hasFormat(MIME):
            self.drueber = True
            self.update()
            ev.acceptProposedAction()

    def dragMoveEvent(self, ev):
        if ev.mimeData().hasFormat(MIME):
            ev.acceptProposedAction()

    def dragLeaveEvent(self, _):
        self.drueber = False
        self.update()

    def dropEvent(self, ev):
        self.drueber = False
        k = bytes(ev.mimeData().data(MIME)).decode()
        pos = ev.position().toPoint()
        vor = None
        for kachel in self.kacheln:
            g = kachel.geometry()
            if pos.y() < g.top() or (pos.y() <= g.bottom() and pos.x() < g.center().x()):
                vor = kachel.k
                break
        if vor is None and self.kacheln and self.haupt.ranking_filter != "alles":
            # Gefiltert: hinter den letzten sichtbaren Titel, nicht ans Ende der ganzen Reihe
            liste = self.haupt.ranking.tiers.get(self.tier, [])
            letzter = self.kacheln[-1].k
            if letzter in liste and liste.index(letzter) + 1 < len(liste):
                vor = liste[liste.index(letzter) + 1]
        ev.acceptProposedAction()
        self.haupt.ranking.tier_setzen(k, self.tier, vor)
        self.haupt.ranking_geaendert = True  # neu aufgebaut wird erst nach dem Ziehen (Kachel.mouseMoveEvent)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self.farbe)
        c.setAlpha(70 if self.drueber else 22)
        p.setPen(QPen(QColor(self.farbe if self.drueber else bp.F["rand"]), 2 if self.drueber else 1))
        p.setBrush(c)
        p.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 10, 10)
        if not self.kacheln:
            p.setPen(QColor(bp.F["leise"]))
            p.drawText(QRectF(self.rect()), Qt.AlignmentFlag.AlignCenter,
                       "Poster hierher ziehen" if self.tier else "Alles eingeordnet. Stark!")
        p.end()


# ---------------------------------------------------------------- Menue (auch auf den Karten)

def menue_fuellen(m, haupt, k, danach=None):
    """Ranking-Eintraege in ein Menue: Tier, Sterne, Top 10."""
    r = haupt.ranking
    danach = danach or (lambda: QTimer.singleShot(0, lambda: neu_zeigen(haupt)))
    jetzt = r.tier_von(k)
    tm = m.addMenu("Tierlist" + (f" ({jetzt})" if jetzt else ""))
    for t, spruch, _ in TIERS:
        a = tm.addAction(f"{t} – {spruch}", lambda t=t: (r.tier_setzen(k, t), danach()))
        a.setCheckable(True)
        a.setChecked(t == jetzt)
    if jetzt:
        tm.addSeparator()
        tm.addAction("Aus der Tierlist nehmen", lambda: (r.tier_setzen(k, None), danach()))
    n = r.noten.get(k, 0)
    sm = m.addMenu("Meine Sterne" + (f" ({sterne_text(n)})" if n else ""))
    for i in range(STERNE, 0, -1):
        a = sm.addAction(sterne_text(i) + "☆" * (STERNE - i), lambda i=i: (r.note_setzen(k, i), danach()))
        a.setCheckable(True)
        a.setChecked(i == n)
    if n:
        sm.addSeparator()
        sm.addAction("Bewertung entfernen", lambda: (r.note_setzen(k, 0), danach()))
    art = ARTEN[art_von(k)]
    if r.ist_top(k):
        m.addAction(f"Aus meinen Top 10 {art} nehmen", lambda: (r.top_umschalten(k), danach()))
    elif len(r.top[art_von(k)]) < TOP:
        m.addAction(f"In meine Top 10 {art}", lambda: (r.top_umschalten(k), danach()))
    else:
        a = m.addAction(f"Top 10 {art} sind voll")
        a.setEnabled(False)


def menue(haupt, k, pos):
    m = QMenu(haupt)
    m.setStyleSheet(bp.STIL)
    eintrag = titel_liste(haupt).get(k)
    if eintrag:
        art, name, e = eintrag
        if art == "serie":
            m.addAction("Folgen anzeigen", lambda: haupt.serie_zeigen(name))
            m.addAction("Weiterschauen", lambda: haupt.abspielen_ab(haupt.serie_weiter(haupt.serien()[name])))
        else:
            m.addAction("Abspielen", lambda: haupt.abspielen_ab(e))
        m.addSeparator()
    menue_fuellen(m, haupt, k)
    m.exec(pos)


# ---------------------------------------------------------------- Seite

def neu_zeigen(haupt):
    """Ranking-Seite neu aufbauen, ohne dass die Scrollposition springt."""
    if haupt.aktuell == "serie" and getattr(haupt, "serie_offen", None):
        haupt.serie_zeigen(*haupt.serie_offen)
        return
    if haupt.aktuell != "ranking":
        haupt.zeigen(haupt.aktuell if haupt.aktuell in bp.SEITEN else "saal")
        return
    alt = haupt.stack.currentWidget()
    wert = alt.verticalScrollBar().value() if isinstance(alt, QScrollArea) else 0
    haupt.zeigen("ranking")
    neu = haupt.stack.currentWidget()
    QTimer.singleShot(0, lambda: bp.alive(neu) and neu.verticalScrollBar().setValue(wert))


def seite(haupt):
    s = bp.Seite()
    kopf = QHBoxLayout()
    kopf.addWidget(bp.label("Ranking", "h1"))
    kopf.addSpacing(20)
    for teil, text in (("tierlist", "Tierlist"), ("top", "Top 10"), ("sterne", "Meine Sterne")):
        b = bp.knopf(text, cb=lambda _=False, t=teil: (setattr(haupt, "ranking_teil", t), neu_zeigen(haupt)))
        b.setCheckable(True)
        b.setChecked(haupt.ranking_teil == teil)
        b.setMinimumWidth(b.fontMetrics().horizontalAdvance(text) * 13 // 10 + 36)  # fett gedrueckt passt es auch
        kopf.addWidget(b)
    kopf.addStretch(1)
    if haupt.ranking_teil != "top":
        filt = QComboBox()
        werte = [("alles", "Serien und Filme"), ("serie", "Nur Serien"), ("film", "Nur Filme")]
        for w, t in werte:
            filt.addItem(t, w)
        filt.setCurrentIndex([w for w, _ in werte].index(haupt.ranking_filter))
        filt.currentIndexChanged.connect(lambda i: (setattr(haupt, "ranking_filter", werte[i][0]), neu_zeigen(haupt)))
        kopf.addWidget(filt)
    s.body.addLayout(kopf)
    alle = titel_liste(haupt)
    if not alle:
        s.body.addWidget(bp.label("Noch nichts in der Sammlung. Sobald Filme oder Serien da sind, kannst du sie hier ranken.",
                                  "leise", wrap=True))
        return s
    {"tierlist": _tierlist, "top": _top, "sterne": _sterne}[haupt.ranking_teil](haupt, s, alle)
    return s


def _sichtbar(haupt, alle):
    f = haupt.ranking_filter
    return {k: v for k, v in alle.items() if f == "alles" or v[0] == f}


def _kachel(haupt, k, eintrag, breite=96, ziehbar=True):
    art, name, e = eintrag
    kachel = Kachel(haupt, k, name, e, breite, ziehbar)
    kachel.geklickt.connect(lambda: menue(haupt, k, kachel.mapToGlobal(QPoint(kachel.width() // 2, kachel.height() // 2))))
    return kachel


def _tierlist(haupt, s, alle):
    r = haupt.ranking
    sichtbar = _sichtbar(haupt, alle)
    s.body.addWidget(bp.label("Zieh die Poster in eine Reihe – ganz oben ist Reihe sieben, der beste Platz im Saal. "
                              "Klick auf ein Poster für Sterne und Top 10.", "leise", wrap=True))
    tafel = QFrame()
    tafel.setObjectName("seite")
    tl = QVBoxLayout(tafel)
    tl.setContentsMargins(0, 4, 0, 4)
    tl.setSpacing(8)
    eingeordnet = set()
    for t, spruch, farbe in TIERS:
        zeile = QHBoxLayout()
        zeile.setSpacing(8)
        schild = QFrame()
        schild.setFixedWidth(128)
        schild.setStyleSheet(f"background: {farbe}; border-radius: 10px;")
        sl = QVBoxLayout(schild)
        sl.setContentsMargins(6, 8, 6, 8)
        sl.addStretch(1)
        b = bp.label(t)
        b.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b.setStyleSheet("color: #14001f; font-size: 30pt; font-weight: 900;")
        sl.addWidget(b)
        sp = bp.label(spruch, wrap=True)
        sp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sp.setStyleSheet("color: #14001f; font-size: 8.5pt; font-weight: 700;")
        sl.addWidget(sp)
        sl.addStretch(1)
        zeile.addWidget(schild)
        feld = TierFeld(haupt, t, farbe)
        for k in r.tiers[t]:
            eingeordnet.add(k)
            if k in sichtbar:
                feld.hinzu(_kachel(haupt, k, sichtbar[k], 84))
        zeile.addWidget(feld, 1)
        tl.addLayout(zeile)
    s.body.addWidget(tafel)
    rest = [k for k in sorted(sichtbar, key=lambda k: sichtbar[k][1].lower()) if k not in eingeordnet]
    reihe = QHBoxLayout()
    reihe.addWidget(bp.label(f"Noch nicht eingeordnet ({len(rest)})", "h2"))
    reihe.addStretch(1)
    reihe.addWidget(bp.knopf("Tierlist als Bild speichern", cb=lambda: _als_bild(haupt, tafel)))
    reihe.addWidget(bp.knopf("Alles zurücksetzen", cb=lambda: _zuruecksetzen(haupt)))
    s.body.addLayout(reihe)
    pool = TierFeld(haupt, None, bp.F["lila"])
    for k in rest:
        pool.hinzu(_kachel(haupt, k, sichtbar[k], 84))
    s.body.addWidget(pool)


def _als_bild(haupt, tafel):
    ordner = Path(bp.run(["xdg-user-dir", "PICTURES"]).strip() or Path.home() / "Bilder")
    ziel = ordner / f"Bibiplexx-Tierlist-{time.strftime('%Y-%m-%d')}.png"
    bild = tafel.grab()
    try:
        ordner.mkdir(parents=True, exist_ok=True)
        ok = bild.save(str(ziel), "PNG")
    except OSError:
        ok = False
    if ok:
        QMessageBox.information(haupt, "Bibiplexx", f"Gespeichert als\n{ziel}")
    else:
        QMessageBox.warning(haupt, "Bibiplexx", "Das Bild ließ sich nicht speichern.")


def _zuruecksetzen(haupt):
    if QMessageBox.question(haupt, "Bibiplexx", "Tierlist, Top 10 und alle Sterne löschen?") == QMessageBox.StandardButton.Yes:
        haupt.ranking.leeren()
        neu_zeigen(haupt)


def _top(haupt, s, alle):
    r = haupt.ranking
    s.body.addWidget(bp.label("Deine persönlichen Bestenlisten. Mit ▲ ▼ umsortieren.", "leise", wrap=True))
    spalten = QHBoxLayout()
    spalten.setSpacing(24)
    for art, text in ARTEN.items():
        col = QVBoxLayout()
        col.setSpacing(8)
        col.addWidget(bp.label(f"Meine Top 10 {text}", "h2"))
        liste = [k for k in r.top[art] if k in alle]
        for platz in range(1, TOP + 1):
            col.addWidget(_top_zeile(haupt, art, platz, liste[platz - 1] if platz <= len(liste) else None, alle, len(liste)))
        col.addStretch(1)
        spalten.addLayout(col, 1)
    s.body.addLayout(spalten)


def _top_zeile(haupt, art, platz, k, alle, anzahl):
    z = QFrame()
    z.setObjectName("zeile")
    z.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    zl = QHBoxLayout(z)
    zl.setContentsMargins(12, 8, 12, 8)
    zl.setSpacing(14)
    nr = bp.label(str(platz))
    nr.setFixedWidth(46)
    nr.setAlignment(Qt.AlignmentFlag.AlignCenter)
    nr.setStyleSheet(f"font-size: 24pt; font-weight: 900; color: {PLATZ_FARBE.get(platz, bp.F['pink']) if k else bp.F['rand']};")
    zl.addWidget(nr)
    if k is None:
        frei = bp.label("Platz frei", "leise")
        zl.addWidget(frei, 1)
        if platz == anzahl + 1:
            zl.addWidget(bp.knopf("＋ Hinzufügen", cb=lambda: _auswahl(haupt, art, alle)))
        return z
    _, name, e = alle[k]
    zl.addWidget(_kachel(haupt, k, alle[k], 56, ziehbar=False))
    col = QVBoxLayout()
    t = bp.label(name, wrap=True)
    t.setStyleSheet("font-weight: 800; font-size: 12pt;")
    col.addWidget(t)
    unter = []
    n = haupt.ranking.noten.get(k)
    if n:
        unter.append(sterne_text(n))
    tier = haupt.ranking.tier_von(k)
    if tier:
        unter.append(f"Tier {tier}")
    d = haupt.tmdb.info(e) or {}
    if d.get("note") and d.get("stimmen", 0) >= 5:
        unter.append("TMDB " + bp.note_text(d["note"]))
    col.addWidget(bp.label("  ·  ".join(unter), "leise"))
    zl.addLayout(col, 1)
    for text, schritt, an in (("▲", -1, platz > 1), ("▼", 1, platz < anzahl)):
        b = bp.knopf(text, cb=lambda _=False, s=schritt: (haupt.ranking.top_schieben(k, s), neu_zeigen(haupt)))
        b.setEnabled(an)
        b.setFixedWidth(42)
        zl.addWidget(b)
    weg = bp.knopf("✕", cb=lambda: (haupt.ranking.top_umschalten(k), neu_zeigen(haupt)))
    weg.setFixedWidth(42)
    weg.setToolTip("Aus der Liste nehmen")
    zl.addWidget(weg)
    return z


def _auswahl(haupt, art, alle):
    """Titel fuer die Top 10 aussuchen: bestbewertete zuerst, mit Suchfeld."""
    r = haupt.ranking
    dlg = QDialog(haupt)
    dlg.setWindowTitle(f"Bibiplexx – Top 10 {ARTEN[art]}")
    dlg.setStyleSheet(bp.STIL)
    dlg.resize(820, 620)
    lay = QVBoxLayout(dlg)
    lay.setContentsMargins(20, 16, 20, 16)
    lay.addWidget(bp.label(f"Was kommt in deine Top 10 {ARTEN[art]}?", "h2"))
    suche = QLineEdit()
    suche.setPlaceholderText("Suchen …")
    suche.setClearButtonEnabled(True)
    lay.addWidget(suche)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    innen = QWidget()
    innen.setObjectName("seite")
    fl = bp.FlowLayout(innen, abstand=12)
    kandidaten = [k for k, v in alle.items() if v[0] == art and not r.ist_top(k)]
    kandidaten.sort(key=lambda k: (-r.noten.get(k, 0), alle[k][1].lower()))
    kacheln = []
    for k in kandidaten:
        kachel = Kachel(haupt, k, alle[k][1], alle[k][2], 110, ziehbar=False)
        kachel.geklickt.connect(lambda k=k: (r.top_umschalten(k), dlg.accept()))
        fl.addWidget(kachel)
        kacheln.append(kachel)
    scroll.setWidget(innen)
    lay.addWidget(scroll, 1)
    if not kandidaten:
        lay.addWidget(bp.label(f"Alle {ARTEN[art]} sind schon in deiner Liste.", "leise"))
    suche.textChanged.connect(lambda t: [kc.setVisible(t.lower() in kc.name.lower()) for kc in kacheln])
    if dlg.exec():
        neu_zeigen(haupt)


def _sterne(haupt, s, alle):
    r = haupt.ranking
    sichtbar = _sichtbar(haupt, alle)
    bewertet = [k for k in sichtbar if r.noten.get(k)]
    if bewertet:
        schnitt = sum(r.noten[k] for k in bewertet) / len(bewertet)
        text = f"Du hast {len(bewertet)} von {len(sichtbar)} bewertet · im Schnitt {schnitt:.1f} Sterne".replace(".", ",")
    else:
        text = "Klick auf die Sterne, um zu bewerten. Nochmal auf denselben Stern nimmt die Bewertung weg."
    s.body.addWidget(bp.label(text, "leise", wrap=True))
    reihenfolge = sorted(sichtbar, key=lambda k: (-r.noten.get(k, 0), sichtbar[k][1].lower()))
    raster = s.raster()
    for k in reihenfolge:
        art, name, e = sichtbar[k]
        z = QFrame()
        z.setObjectName("zeile")
        z.setFixedSize(360, 132)
        zl = QHBoxLayout(z)
        zl.setContentsMargins(10, 10, 12, 10)
        zl.setSpacing(12)
        kachel = _kachel(haupt, k, sichtbar[k], 74, ziehbar=False)
        zl.addWidget(kachel)
        rechts = QWidget()
        rechts.setFixedWidth(360 - 74 - 10 - 12 - 12)
        col = QVBoxLayout(rechts)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(4)
        t = bp.label(name, wrap=True)
        t.setStyleSheet("font-weight: 800;")
        col.addWidget(t)
        col.addWidget(bp.label("Serie" if art == "serie" else "Film", "leise"))
        sterne = Sterne(r.noten.get(k, 0))
        sterne.gesetzt.connect(lambda n, k=k, kw=kachel: (r.note_setzen(k, n), kw.update()))
        col.addWidget(sterne)
        d = haupt.tmdb.info(e) or {}
        if d.get("note") and d.get("stimmen", 0) >= 5:
            tm = bp.label("TMDB " + bp.note_text(d["note"]))
            tm.setStyleSheet(f"color: {bp.F['orange']}; font-weight: 700;")
            col.addWidget(tm)
        col.addStretch(1)
        zl.addWidget(rechts)
        raster.addWidget(z)
