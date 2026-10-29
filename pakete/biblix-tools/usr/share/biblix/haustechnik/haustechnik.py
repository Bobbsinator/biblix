#!/usr/bin/env python3
"""Biblix Haustechnik: Secure Boot, Bildschirme und leere Platten mit ein paar Klicks statt Terminal."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PyQt6.QtCore import QProcess, Qt, QTimer, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QIcon, QPainter, QColor, QPen, QFont
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QFrame, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QStackedWidget,
    QVBoxLayout, QWidget,
)

PALETTE = Path(os.environ.get("BIBLIX_KONFIG_DIR") or Path.home() / ".config/biblix") / "palette.json"
MOK_PUB = Path("/var/lib/dkms/mok.pub")
MERKER_MOK = Path("/var/lib/biblix/mok-eigener-schluessel")

F = {"grund": "#0f141c", "flaeche": "#1a2029", "karte": "#232a35", "rand": "#313a48", "text": "#e8ecf2",
     "leise": "#8b95a5", "akzent": "#378add", "akzent2": "#ffd400", "auf_akzent": "#ffffff"}
try:
    F.update({k: v for k, v in json.loads(PALETTE.read_text(encoding="utf-8")).items() if k in F})
except (OSError, ValueError):
    pass

STIL = f"""
* {{ font-size: 10.5pt; }}
QMainWindow, #seite {{ background: {F['grund']}; color: {F['text']}; }}
QLabel {{ color: {F['text']}; background: transparent; }}
QLabel#leise {{ color: {F['leise']}; }}
QLabel#h1 {{ font-size: 19pt; font-weight: 800; }}
QLabel#h2 {{ font-size: 12.5pt; font-weight: 700; margin-top: 6px; }}
#seitenleiste {{ background: {F['flaeche']}; border-right: 1px solid {F['rand']}; }}
QListWidget {{ background: transparent; border: none; color: {F['text']}; outline: 0; }}
QListWidget::item {{ padding: 10px 12px; margin: 2px 8px; border-radius: 8px; }}
QListWidget::item:selected {{ background: {F['akzent']}; color: {F['auf_akzent']}; }}
QFrame#karte {{ background: {F['karte']}; border: 1px solid {F['rand']}; border-radius: 12px; }}
QPushButton {{ background: {F['karte']}; color: {F['text']}; border: 1px solid {F['rand']}; border-radius: 8px; padding: 7px 14px; }}
QPushButton:hover {{ border-color: {F['akzent']}; }}
QPushButton#haupt {{ background: {F['akzent']}; color: {F['auf_akzent']}; border-color: {F['akzent']}; font-weight: 700; }}
QPushButton:disabled {{ color: {F['leise']}; }}
QPlainTextEdit {{ background: #05070a; color: {F['akzent2']}; border: 1px solid {F['rand']}; border-radius: 8px;
                  font-family: "DejaVu Sans Mono"; font-size: 9.5pt; }}
QComboBox {{ background: {F['karte']}; color: {F['text']}; border: 1px solid {F['rand']}; border-radius: 8px; padding: 6px 10px; }}
QFrame#meldung {{ border-radius: 14px; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
"""


def run(argv, timeout=20):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except (OSError, subprocess.SubprocessError):
        return 127, ""


def label(text, name=None, wrap=True):
    lb = QLabel(text)
    if name:
        lb.setObjectName(name)
    lb.setWordWrap(wrap)
    lb.setTextFormat(Qt.TextFormat.RichText)
    return lb


def knopf(text, haupt=False, cb=None):
    b = QPushButton(text)
    if haupt:
        b.setObjectName("haupt")
    if cb:
        b.clicked.connect(cb)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def karte():
    k = QFrame()
    k.setObjectName("karte")
    lay = QVBoxLayout(k)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(8)
    return k, lay


def seite():
    s = QScrollArea()
    s.setWidgetResizable(True)
    innen = QWidget()
    innen.setObjectName("seite")
    lay = QVBoxLayout(innen)
    lay.setContentsMargins(26, 22, 26, 22)
    lay.setSpacing(12)
    lay.setAlignment(Qt.AlignmentFlag.AlignTop)
    s.setWidget(innen)
    return s, lay


# ---------------------------------------------------------------- Zustand abfragen

def secureboot_zustand():
    """(sb_an, schluessel): sb_an True/False/None, schluessel 'angemeldet'|'vorgemerkt'|'fehlt'|'unbekannt'."""
    rc, out = run(["mokutil", "--sb-state"])
    sb = None
    if "secureboot enabled" in out.lower():
        sb = True
    elif "secureboot disabled" in out.lower():
        sb = False
    schluessel = "unbekannt"
    if MOK_PUB.exists():
        rc, out = run(["mokutil", "--test-key", str(MOK_PUB)])
        if "already enrolled" in out.lower():
            schluessel = "angemeldet"
        else:
            rc2, neu = run(["mokutil", "--list-new"])
            schluessel = "vorgemerkt" if rc2 == 0 and "Certificate" in neu else "fehlt"
    elif shutil.which("mokutil"):
        schluessel = "fehlt"
    return sb, schluessel


def bildschirme():
    rc, out = run(["biblix-bildschirme", "--json"])
    try:
        return json.loads(out[out.index("["):]) if "[" in out else []
    except ValueError:
        return []


def leere_platten():
    rc, out = run(["lsblk", "-J", "-b", "-o", "NAME,PATH,MODEL,SIZE,TYPE,RO,FSTYPE,PTTYPE,MOUNTPOINTS"])
    try:
        daten = json.loads(out)
    except ValueError:
        return []
    ergebnis = []
    for d in daten.get("blockdevices", []):
        if d.get("type") != "disk" or d.get("children") or d.get("fstype") or d.get("pttype"):
            continue
        # irgendwo eingebunden = nicht leer (auch wenn Angaben zum Dateisystem fehlen)
        if any(m for m in (d.get("mountpoints") or []) if m):
            continue
        if str(d.get("ro")).lower() in ("1", "true") or d.get("name", "").startswith(("loop", "zram", "sr", "ram")):
            continue
        groesse = int(d.get("size") or 0)
        if groesse < 8_000_000_000:
            continue
        ergebnis.append({"path": d.get("path") or "/dev/" + d["name"], "model": (d.get("model") or "").strip(),
                         "groesse": round(groesse / 1e9)})
    return ergebnis


def neustart_grund():
    rc, out = run(["biblix-neustart-noetig"])
    return out.strip() if rc == 0 else ""


# ---------------------------------------------------------------- Schaltwarte (Uebersicht)

LAMPE = {"gruen": "#3ad07a", "gelb": "#ffb020", "rot": "#e24b4a", "grau": "#5b6575"}
RANG = {"grau": 0, "gruen": 1, "gelb": 2, "rot": 3}


class Instrument(QFrame):
    """Eine Kachel der Schaltwarte: Lampe, Name, Wert und ein kleines Bild (Monitore, Fuellstand)."""
    geklickt = pyqtSignal()

    def __init__(self, titel, wert, zustand, bild=None, daten=None):
        super().__init__()
        self.titel, self.wert, self.zustand, self.bild, self.daten = titel, wert, zustand, bild, daten
        self.drin = False
        self.setMinimumSize(300, 168)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Öffnen")

    def enterEvent(self, ev):
        self.drin = True
        self.update()

    def leaveEvent(self, ev):
        self.drin = False
        self.update()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.geklickt.emit()

    def paintEvent(self, ev):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        lampe = QColor(LAMPE[self.zustand])
        qp.setPen(QPen(QColor(F["akzent"] if self.drin else F["rand"]), 1.5 if self.drin else 1))
        qp.setBrush(QColor(F["karte"]))
        qp.drawRoundedRect(r, 14, 14)
        # Lampe mit Schein
        mitte = QPointF(r.left() + 30, r.top() + 32)
        schein = QColor(lampe)
        schein.setAlpha(60)
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(schein)
        qp.drawEllipse(mitte, 15, 15)
        qp.setBrush(lampe)
        qp.drawEllipse(mitte, 8, 8)
        # Name in Typenschild-Schrift
        f = QFont("DejaVu Sans Mono")
        f.setPixelSize(14)
        f.setBold(True)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        qp.setFont(f)
        qp.setPen(QColor(F["text"]))
        qp.drawText(QRectF(r.left() + 54, r.top() + 20, r.width() - 70, 24), Qt.AlignmentFlag.AlignVCenter, self.titel.upper())
        f2 = QFont("DejaVu Sans")
        f2.setPixelSize(13)
        qp.setFont(f2)
        qp.setPen(QColor(F["leise"]))
        qp.drawText(QRectF(r.left() + 20, r.bottom() - 34, r.width() - 40, 22), Qt.AlignmentFlag.AlignVCenter, self.wert)
        bild = QRectF(r.left() + 20, r.top() + 58, r.width() - 40, r.height() - 100)
        if self.bild == "monitore":
            self._monitore(qp, bild)
        elif self.bild == "fuellstand":
            self._fuellstand(qp, bild)
        elif self.bild == "schild":
            self._schild(qp, bild)
        qp.end()

    def _monitore(self, qp, b):
        mons = self.daten or []
        if not mons:
            return
        breite = min(110, (b.width() - 16 * (len(mons) - 1)) / len(mons))
        x = b.left()
        for m in mons:
            h = breite * 0.58
            rr = QRectF(x, b.top() + (b.height() - h - 10) / 2, breite, h)
            voll = m["jetzt"] >= m["moeglich"]
            qp.setPen(QPen(QColor(F["akzent"] if voll else LAMPE["gelb"]), 2))
            qp.setBrush(QColor(F["grund"]))
            qp.drawRoundedRect(rr, 4, 4)
            qp.drawLine(QPointF(rr.center().x(), rr.bottom()), QPointF(rr.center().x(), rr.bottom() + 8))
            f = QFont("DejaVu Sans Mono")
            f.setPixelSize(13)
            f.setBold(True)
            qp.setFont(f)
            qp.setPen(QColor(F["text"]))
            qp.drawText(rr, Qt.AlignmentFlag.AlignCenter, f"{m['jetzt']} Hz")
            x += breite + 16

    def _fuellstand(self, qp, b):
        anteil = (self.daten or {}).get("anteil", 0)
        balken = QRectF(b.left(), b.center().y() - 8, b.width(), 16)
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QColor(F["grund"]))
        qp.drawRoundedRect(balken, 8, 8)
        qp.setBrush(QColor(LAMPE[self.zustand] if self.zustand in ("gelb", "rot") else F["akzent"]))
        qp.drawRoundedRect(QRectF(balken.left(), balken.top(), max(16, balken.width() * anteil), balken.height()), 8, 8)
        for i in range(1, 10):   # Skala
            x = balken.left() + balken.width() * i / 10
            qp.setPen(QPen(QColor(F["rand"]), 1))
            qp.drawLine(QPointF(x, balken.bottom() + 4), QPointF(x, balken.bottom() + (9 if i == 5 else 6)))

    def _schild(self, qp, b):
        # Schloss: zu (gruen) oder offen
        cx, cy = b.left() + 24, b.center().y()
        zu = self.zustand == "gruen"
        qp.setPen(QPen(QColor(F["akzent"] if zu else LAMPE[self.zustand]), 3))
        qp.setBrush(Qt.BrushStyle.NoBrush)
        bogen = QRectF(cx - 11, cy - 24, 22, 26)
        qp.drawArc(bogen.translated(0, 0 if zu else -6), 0, 180 * 16)
        if zu:
            qp.drawLine(QPointF(cx - 11, cy - 11), QPointF(cx - 11, cy - 4))
        qp.drawLine(QPointF(cx + 11, cy - (11 if zu else 17)), QPointF(cx + 11, cy - 4))
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QColor(F["akzent"] if zu else LAMPE[self.zustand]))
        qp.drawRoundedRect(QRectF(cx - 17, cy - 4, 34, 26), 5, 5)
        f = QFont("DejaVu Sans")
        f.setPixelSize(13)
        qp.setFont(f)
        qp.setPen(QColor(F["text"]))
        qp.drawText(QRectF(cx + 34, cy - 14, b.width() - 60, 28), Qt.AlignmentFlag.AlignVCenter,
                    (self.daten or {}).get("zeile", ""))


# ---------------------------------------------------------------- Fenster

class Haustechnik(QMainWindow):
    def __init__(self, start="uebersicht"):
        super().__init__()
        self.setWindowTitle("Biblix Haustechnik")
        self.setWindowIcon(QIcon.fromTheme("de.biblix.Haustechnik", QIcon.fromTheme("preferences-system")))
        self.resize(1040, 720)
        self.proc = None
        wurzel = QWidget()
        h = QHBoxLayout(wurzel)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        seiten = QWidget()
        seiten.setObjectName("seitenleiste")
        seiten.setFixedWidth(220)
        sl = QVBoxLayout(seiten)
        sl.setContentsMargins(0, 18, 0, 12)
        kopf = label("HAUSTECHNIK")
        kopf.setStyleSheet(f"color: {F['akzent2']}; font-weight: 800; letter-spacing: 3px; padding: 0 18px 12px 18px;")
        sl.addWidget(kopf)
        self.nav = QListWidget()
        self.schluessel = ["uebersicht", "secureboot", "bildschirme", "platten"]
        for text in ("Übersicht", "Secure Boot", "Bildschirme", "Platten"):
            self.nav.addItem(QListWidgetItem(text))
        sl.addWidget(self.nav, 1)
        spruch = label("AUF BIBLIX GEHT DAS.", "leise")
        spruch.setStyleSheet("padding: 0 18px; font-family: 'DejaVu Sans Mono'; font-size: 8.5pt;")
        sl.addWidget(spruch)
        h.addWidget(seiten)
        self.stack = QStackedWidget()
        h.addWidget(self.stack, 1)
        self.setCentralWidget(wurzel)
        self.setStyleSheet(STIL)
        self.nav.currentRowChanged.connect(self.zeigen)
        self.nav.setCurrentRow(self.schluessel.index(start) if start in self.schluessel else 0)

    def zeigen(self, i):
        alt = self.stack.currentWidget()
        neu = getattr(self, "seite_" + self.schluessel[i])()
        self.stack.addWidget(neu)
        self.stack.setCurrentWidget(neu)
        if alt is not None:
            self.stack.removeWidget(alt)
            alt.deleteLater()

    def neu_zeigen(self):
        self.zeigen(self.nav.currentRow())

    # ---- Uebersicht

    def seite_uebersicht(self):
        """Schaltwarte: oben die Gesamtmeldung, darunter eine Kachel mit Lampe je Bereich."""
        s, lay = seite()
        lay.addWidget(label("Übersicht", "h1"))
        sb, schl = secureboot_zustand()
        b = bildschirme()
        voll = sum(1 for x in b if x["jetzt"] >= x["moeglich"])
        p = leere_platten()
        try:
            platz = shutil.disk_usage(str(Path.home()))
            anteil = platz.used / platz.total
        except OSError:
            platz, anteil = None, 0
        kacheln = [
            ("Secure Boot", {True: "an", False: "aus: Windows-Spiele mit Anti-Cheat starten evtl. nicht",
                             None: "Zustand unbekannt"}[sb],
             {True: "gruen", False: "gelb", None: "grau"}[sb], "schild",
             {"zeile": {True: "Startkette geprüft", False: "nicht geprüft", None: ""}[sb]}, "secureboot"),
            ("Treiber-Schlüssel", {"angemeldet": "angemeldet", "vorgemerkt": "vorgemerkt: beim Neustart bestätigen",
                                   "fehlt": "noch nicht eingerichtet", "unbekannt": "unbekannt"}[schl],
             {"angemeldet": "gruen", "vorgemerkt": "gelb", "fehlt": "rot" if sb else "gelb", "unbekannt": "grau"}[schl],
             "schild", {"zeile": "NVIDIA-Treiber darf laden" if schl == "angemeldet" else "Treiber gesperrt"
                        if schl == "fehlt" and sb else ""}, "secureboot"),
            ("Bildschirme", f"{voll} von {len(b)} auf höchster Bildrate" if b else "keine Angaben",
             "grau" if not b else ("gruen" if voll == len(b) else "gelb"), "monitore", b, "bildschirme"),
            ("Platten", (f"{round(anteil * 100)} % belegt · {round(platz.free / 1e9)} GB frei" if platz else "")
             + (f" · {len(p)} leere Platte bereit" if len(p) == 1 else f" · {len(p)} leere Platten bereit" if p else ""),
             "rot" if anteil > 0.92 else "gelb" if anteil > 0.82 or p else "gruen", "fuellstand", {"anteil": anteil}, "platten"),
        ]
        grund = neustart_grund()
        schlimmste = max([k[2] for k in kacheln] + (["gelb"] if grund else []), key=lambda z: RANG[z])
        hinweise = sum(1 for k in kacheln if k[2] in ("gelb", "rot")) + (1 if grund else 0)
        text = {"gruen": "ALLES IN BETRIEB", "grau": "ALLES IN BETRIEB",
                "gelb": f"{hinweise} {'HINWEIS' if hinweise == 1 else 'HINWEISE'}",
                "rot": "STÖRUNG: BITTE ANSEHEN"}[schlimmste]
        farbe = LAMPE["gruen" if schlimmste == "grau" else schlimmste]
        meldung = QFrame()
        meldung.setObjectName("meldung")
        meldung.setStyleSheet(f"QFrame#meldung {{ background: {F['flaeche']}; border: 1px solid {farbe}; }}")
        ml = QHBoxLayout(meldung)
        ml.setContentsMargins(18, 14, 18, 14)
        lampe = QLabel("●")
        lampe.setStyleSheet(f"color: {farbe}; font-size: 22pt;")
        ml.addWidget(lampe)
        zeile = QVBoxLayout()
        kopf = label(text)
        kopf.setStyleSheet(f"color: {farbe}; font-family: 'DejaVu Sans Mono'; font-weight: 800; font-size: 14pt; letter-spacing: 2px;")
        zeile.addWidget(kopf)
        zeile.addWidget(label(f"Neustart nötig: {grund}." if grund else "Haustechnik überwacht Startkette, Treiber, Bildschirme und Platten.", "leise"))
        ml.addLayout(zeile, 1)
        if grund:
            ml.addWidget(knopf("Jetzt neu starten", True, self.neustarten))
        lay.addWidget(meldung)
        gitter = QGridLayout()
        gitter.setSpacing(14)
        for i, (titel, wert, zustand, bild, daten, ziel) in enumerate(kacheln):
            k = Instrument(titel, wert, zustand, bild, daten)
            k.geklickt.connect(lambda z=ziel: self.nav.setCurrentRow(self.schluessel.index(z)))
            gitter.addWidget(k, i // 2, i % 2)
        lay.addLayout(gitter)
        lay.addWidget(label("Klick auf eine Kachel öffnet den Bereich.", "leise"))
        return s

    def neustarten(self):
        QProcess.startDetached("biblix-neustart-noetig", ["--fragen"])

    # ---- Secure Boot

    def seite_secureboot(self):
        s, lay = seite()
        lay.addWidget(label("Secure Boot", "h1"))
        lay.addWidget(label("Mit Secure Boot startet nur Software mit gültiger Unterschrift. Die NVIDIA- und Xbox-Treiber baut "
                            "Biblix selbst – damit sie mit Secure Boot laden, bekommen sie eine Unterschrift von <b>deinem</b> "
                            "Schlüssel, und den meldest du einmal beim PC an.", "leise"))
        sb, schl = secureboot_zustand()
        k, kl = karte()
        kl.addWidget(label(f"<b>Secure Boot:</b> {'an' if sb else ('aus' if sb is False else 'unbekannt')}"
                           f" &nbsp;·&nbsp; <b>Schlüssel:</b> {schl}"))
        lay.addWidget(k)

        k1, l1 = karte()
        l1.addWidget(label("<b>1. Schlüssel erzeugen und Treiber unterschreiben</b>"))
        l1.addWidget(label("Du denkst dir ein Einmal-Passwort aus (z. B. 12345678). Das brauchst du nur beim nächsten Start "
                           "auf dem blauen Bildschirm. Danach fragt Biblix nach deinem normalen Passwort. Das Unterschreiben "
                           "dauert ein paar Minuten.", "leise"))
        self.sb_knopf = knopf("Einrichten", True, self.secureboot_einrichten)
        self.sb_knopf.setEnabled(schl != "angemeldet")
        l1.addWidget(self.sb_knopf, 0, Qt.AlignmentFlag.AlignLeft)
        self.protokoll = QPlainTextEdit()
        self.protokoll.setReadOnly(True)
        self.protokoll.setMinimumHeight(140)
        self.protokoll.hide()
        l1.addWidget(self.protokoll)
        lay.addWidget(k1)

        k2, l2 = karte()
        l2.addWidget(label("<b>2. Neu starten und Schlüssel anmelden</b>"))
        l2.addWidget(label("Beim Start kommt ein <b>blauer Bildschirm</b> (MOK-Verwaltung). Mit den Pfeiltasten:<br>"
                           "<b>Enroll MOK</b> → <b>Continue</b> → <b>Yes</b> → Einmal-Passwort eintippen → <b>Reboot</b>.<br>"
                           "Wartest du dort zu lange, startet Biblix normal – dann einfach Schritt 1 nochmal.", "leise"))
        l2.addWidget(knopf("Jetzt neu starten", cb=self.neustarten_direkt), 0, Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(k2)

        k3, l3 = karte()
        l3.addWidget(label("<b>3. Im BIOS Secure Boot einschalten</b>"))
        l3.addWidget(label("Erst wenn hier oben „Schlüssel: angemeldet“ steht. Danach startet Biblix mit Secure Boot, "
                           "und auch Windows-Spiele mit Anti-Cheat sind zufrieden.", "leise"))
        lay.addWidget(k3)
        return s

    def secureboot_einrichten(self):
        pw, ok = QInputDialog.getText(self, "Einmal-Passwort", "Einmal-Passwort ausdenken (mindestens 8 Zeichen):",
                                      QLineEdit.EchoMode.Password)
        if not ok:
            return
        if len(pw) < 8:
            QMessageBox.warning(self, "Haustechnik", "Bitte mindestens 8 Zeichen.")
            return
        pw2, ok = QInputDialog.getText(self, "Einmal-Passwort", "Nochmal eingeben:", QLineEdit.EchoMode.Password)
        if not ok or pw2 != pw:
            QMessageBox.warning(self, "Haustechnik", "Die Passwörter stimmen nicht überein.")
            return
        # Nur der Hash verlaesst dieses Programm, nie das Passwort selbst. openssl liest es ueber stdin
        # (nicht in der Prozessliste sichtbar); ergibt dasselbe SHA-512-crypt-Format wie mokutil --generate-hash.
        r = None
        try:
            if shutil.which("openssl"):
                r = subprocess.run(["openssl", "passwd", "-6", "-stdin"], input=pw + "\n",
                                   capture_output=True, text=True, timeout=20)
            elif shutil.which("mokutil"):
                r = subprocess.run(["mokutil", f"--generate-hash={pw}"], capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            r = None
        if r is None:
            QMessageBox.warning(self, "Haustechnik", "mokutil fehlt. Bitte im Terminal: bibi apt install mokutil")
            return
        if r.returncode != 0 or not r.stdout.strip().startswith("$6$"):
            QMessageBox.warning(self, "Haustechnik", "Das Passwort konnte nicht verarbeitet werden.")
            return
        fd, self.hash_datei = tempfile.mkstemp(prefix="biblix-mok-")
        with os.fdopen(fd, "w") as f:
            f.write(r.stdout.strip() + "\n")
        self.sb_knopf.setEnabled(False)
        self.protokoll.show()
        self.protokoll.setPlainText("Biblix richtet Secure Boot ein …\n")
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(
            lambda: self.protokoll.appendPlainText(bytes(self.proc.readAllStandardOutput()).decode(errors="replace").rstrip()))
        self.proc.finished.connect(self._secureboot_fertig)
        self.proc.start("pkexec", ["/usr/bin/biblix-secureboot", "--hash-datei", self.hash_datei])

    def _secureboot_fertig(self, code, _status):
        try:
            os.unlink(self.hash_datei)
        except OSError:
            pass
        if code == 0:
            QMessageBox.information(self, "Haustechnik", "Fertig. Jetzt neu starten und auf dem blauen Bildschirm "
                                    "„Enroll MOK“ wählen (siehe Schritt 2).")
        else:
            self.sb_knopf.setEnabled(True)
            QMessageBox.warning(self, "Haustechnik", "Hat nicht geklappt (oder abgebrochen). Details stehen im Protokoll.")

    def neustarten_direkt(self):
        for q in ("qdbus6", "qdbus"):
            if shutil.which(q):
                QProcess.startDetached(q, ["org.kde.LogoutPrompt", "/LogoutPrompt", "org.kde.LogoutPrompt.promptReboot"])
                return
        QProcess.startDetached("systemctl", ["reboot"])

    # ---- Bildschirme

    def seite_bildschirme(self):
        s, lay = seite()
        lay.addWidget(label("Bildschirme", "h1"))
        lay.addWidget(label("Biblix stellt neue Bildschirme einmal auf die höchste Bildrate. Hier siehst du, ob alles stimmt.",
                            "leise"))
        liste = bildschirme()
        if not liste:
            lay.addWidget(label("Keine Angaben (kscreen-doctor fehlt oder kein Bildschirm erkannt)."))
        for b in liste:
            k, kl = karte()
            moeglich = b["moeglich"]
            zusatz = "✓ höchste Bildrate" if b["jetzt"] >= moeglich else f"(möglich: {moeglich} Hz)"
            kl.addWidget(label(f"<b>{b['name']}</b> &nbsp; {b['jetzt']} Hz {zusatz}"))
            if b.get("vrr"):
                kl.addWidget(label("Adaptive Sync (FreeSync/G-Sync): " + ("an" if b.get("vrr_an") else "aus"), "leise"))
            lay.addWidget(k)
        r = QHBoxLayout()
        r.addWidget(knopf("Alle auf höchste Bildrate stellen", True, self.hz_hoch))
        r.addWidget(knopf("Anzeige-Einstellungen öffnen", cb=lambda: QProcess.startDetached("systemsettings", ["kcm_kscreen"])))
        r.addStretch(1)
        lay.addLayout(r)
        return s

    def hz_hoch(self):
        rc, out = run(["biblix-bildschirme", "--jetzt"], 40)
        QMessageBox.information(self, "Haustechnik", out.strip() or "Erledigt.")
        QTimer.singleShot(800, self.neu_zeigen)

    # ---- Platten

    def seite_platten(self):
        s, lay = seite()
        lay.addWidget(label("Platten", "h1"))
        lay.addWidget(label("Eine <b>komplett leere</b> Platte (ohne Partitionen) richtet Biblix für dich ein. Platten mit Daten "
                            "werden nie angefasst – auch nicht aus Versehen.", "leise"))
        platten = leere_platten()
        if not platten:
            lay.addWidget(label("Keine leere Platte gefunden."))
            return s
        for p in platten:
            k, kl = karte()
            kl.addWidget(label(f"<b>{p['model'] or p['path']}</b> &nbsp; {p['groesse']} GB &nbsp; <span>{p['path']}</span>"))
            r = QHBoxLayout()
            wahl = QComboBox()
            wahl.addItem("Spieleplatte für Steam (/media/spiele)", "spiele")
            wahl.addItem("Filme und Serien für Bibiplexx (/media/bibiplexx)", "filme")
            wahl.addItem("Datenplatte (/media/daten)", "daten")
            r.addWidget(wahl, 1)
            r.addWidget(knopf("Einrichten", True, lambda _=False, pp=p, w=wahl: self.platte(pp, w.currentData())))
            kl.addLayout(r)
            lay.addWidget(k)
        return s

    def platte(self, p, zweck):
        frage = QMessageBox.question(
            self, "Platte einrichten",
            f"{p['model'] or p['path']} ({p['groesse']} GB) ist leer und wird jetzt eingerichtet.\n\nWeiter?")
        if frage != QMessageBox.StandardButton.Yes:
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            rc, out = run(["pkexec", "/usr/lib/biblix/biblix-platte-einrichten", p["path"], zweck], 600)
        finally:
            QApplication.restoreOverrideCursor()
        if rc != 0:
            QMessageBox.warning(self, "Haustechnik", "Hat nicht geklappt.\n\n" + out.strip())
            return
        tipp = {"spiele": "In Steam: Einstellungen → Speicher → Laufwerk hinzufügen → /media/spiele/SteamLibrary.",
                "filme": "Filme nach /media/bibiplexx/Filme, Serien nach /media/bibiplexx/Serien. Bibiplexx findet sie von selbst.",
                "daten": "Die Platte heißt im Dateimanager „Daten“."}[zweck]
        run(["biblix-orte"], 20)  # neuer Ort gleich in der Dolphin-Seitenleiste
        QMessageBox.information(self, "Haustechnik", "Fertig.\n\n" + tipp)
        self.neu_zeigen()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Biblix Haustechnik")
    app.setDesktopFileName("de.biblix.Haustechnik")
    start = sys.argv[1].lstrip("-") if len(sys.argv) > 1 else "uebersicht"
    w = Haustechnik(start)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
