#!/usr/bin/env python3
"""Biblix Haustechnik: Secure Boot, Bildschirme und leere Platten mit ein paar Klicks statt Terminal."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PyQt6.QtCore import QProcess, Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QFrame, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget,
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
        sl.addWidget(label("  AUF BIBLIX GEHT DAS.", "leise"))
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
        s, lay = seite()
        lay.addWidget(label("Übersicht", "h1"))
        grund = neustart_grund()
        if grund:
            k, kl = karte()
            kl.addWidget(label(f"<b>Neustart nötig:</b> {grund}."))
            kl.addWidget(knopf("Jetzt neu starten", True, self.neustarten), 0, Qt.AlignmentFlag.AlignLeft)
            lay.addWidget(k)
        sb, schl = secureboot_zustand()
        zeilen = []
        zeilen.append(("Secure Boot", {True: "an", False: "aus", None: "unbekannt"}[sb],
                       "secureboot"))
        zeilen.append(("Treiber-Schlüssel", {"angemeldet": "angemeldet ✓", "vorgemerkt": "vorgemerkt (Neustart nötig)",
                                             "fehlt": "noch nicht eingerichtet", "unbekannt": "unbekannt"}[schl], "secureboot"))
        b = bildschirme()
        voll = sum(1 for x in b if x["jetzt"] >= x["moeglich"])
        zeilen.append(("Bildschirme", f"{voll} von {len(b)} auf höchster Bildrate" if b else "keine Angaben", "bildschirme"))
        p = leere_platten()
        zeilen.append(("Leere Platten", f"{len(p)} gefunden" if p else "keine", "platten"))
        for titel, wert, ziel in zeilen:
            k, kl = karte()
            r = QHBoxLayout()
            r.addWidget(label(f"<b>{titel}</b>"), 1)
            r.addWidget(label(wert, "leise", wrap=False))
            r.addWidget(knopf("Öffnen", cb=lambda _=False, z=ziel: self.nav.setCurrentRow(self.schluessel.index(z))))
            kl.addLayout(r)
            lay.addWidget(k)
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
