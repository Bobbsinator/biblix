#!/usr/bin/env python3
"""Willkommen bei Biblix: der Assistent beim ersten Start.

Geht Schritt für Schritt durch das, was man auf einem neuen Biblix einmal einstellt: Design, Bildschirme,
Secure Boot, Spiele, Konten. Alles lässt sich überspringen; die eigentliche Arbeit machen die vorhandenen
Biblix-Werkzeuge (biblix-design, biblix-bildschirme, Haustechnik, S-Launcher, biblix-onedrive).

  biblix-willkommen              Assistent öffnen
  biblix-willkommen --autostart  nur beim ersten Anmelden auf einem frisch installierten Biblix (ISO 2.0+)
Im Live-System (vom USB-Stick) zeigt er stattdessen „Ausprobieren oder installieren“.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QPointF, QProcess, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow,
    QPushButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget,
)

KONFIG = Path(os.environ.get("BIBLIX_KONFIG_DIR") or Path.home() / ".config/biblix")
ERLEDIGT = KONFIG / "willkommen.json"
PALETTE = KONFIG / "palette.json"
PRESETS = Path("/usr/share/biblix/design/presets")
ISO = Path("/etc/biblix-iso")

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
QLabel#h1 {{ font-size: 22pt; font-weight: 800; }}
QLabel#gross {{ font-size: 13pt; }}
#seitenleiste {{ background: {F['flaeche']}; border-right: 1px solid {F['rand']}; }}
QListWidget {{ background: transparent; border: none; color: {F['leise']}; outline: 0; }}
QListWidget::item {{ padding: 9px 12px; margin: 2px 8px; border-radius: 8px; }}
QListWidget::item:selected {{ background: {F['karte']}; color: {F['text']}; }}
QFrame#karte {{ background: {F['karte']}; border: 1px solid {F['rand']}; border-radius: 14px; }}
QFrame#gewaehlt {{ background: {F['karte']}; border: 2px solid {F['akzent']}; border-radius: 14px; }}
QPushButton {{ background: {F['karte']}; color: {F['text']}; border: 1px solid {F['rand']}; border-radius: 9px;
              padding: 8px 16px; }}
QPushButton:hover {{ border-color: {F['akzent']}; }}
QPushButton#haupt {{ background: {F['akzent']}; color: {F['auf_akzent']}; border-color: {F['akzent']}; font-weight: 700; }}
QPushButton:disabled {{ color: {F['leise']}; }}
#fuss {{ background: {F['flaeche']}; border-top: 1px solid {F['rand']}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
"""


def live_system():
    try:
        return "boot=live" in Path("/proc/cmdline").read_text()
    except OSError:
        return False


def run(argv, timeout=20):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except (OSError, subprocess.SubprocessError):
        return 127, ""


def starten(*argv):
    QProcess.startDetached(argv[0], list(argv[1:]))


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


def karte(name="karte"):
    k = QFrame()
    k.setObjectName(name)
    lay = QVBoxLayout(k)
    lay.setContentsMargins(18, 16, 18, 16)
    lay.setSpacing(8)
    return k, lay


class PromptB(QWidget):
    """Das Biblix-Logo (Prompt-B) gezeichnet, damit es ohne Bilddatei geht."""
    def __init__(self, groesse=120):
        super().__init__()
        self.setFixedSize(groesse, groesse)

    def paintEvent(self, ev):
        s = self.width() / 120
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        qp.scale(s, s)
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QColor(F["karte"]))
        qp.drawRoundedRect(QRectF(0, 0, 120, 120), 26, 26)
        # ">" in Akzentfarbe, dann das B und der Cursor-Strich darunter
        qp.setPen(QPen(QColor(F["akzent"]), 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        qp.drawPolyline([QPointF(26, 44), QPointF(42, 60), QPointF(26, 76)])
        qp.setPen(QColor(F["text"]))
        f = QFont("DejaVu Sans")
        f.setBold(True)
        f.setPixelSize(70)
        qp.setFont(f)
        qp.drawText(QRectF(46, 18, 70, 80), Qt.AlignmentFlag.AlignCenter, "B")
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QColor(F["akzent"]))
        qp.drawRoundedRect(QRectF(54, 94, 34, 6), 2, 2)
        qp.end()


class Muster(QWidget):
    """Farbmuster eines Presets: Fläche, Karte, Akzent, Zweitakzent."""
    def __init__(self, farben):
        super().__init__()
        self.f = farben
        self.setFixedHeight(54)

    def paintEvent(self, ev):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        b = self.width()
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(QColor(self.f.get("grund", "#000")))
        qp.drawRoundedRect(QRectF(0, 0, b, 54), 10, 10)
        qp.setBrush(QColor(self.f.get("karte", "#333")))
        qp.drawRoundedRect(QRectF(10, 10, b * 0.55, 34), 7, 7)
        qp.setBrush(QColor(self.f.get("akzent", "#378add")))
        qp.drawRoundedRect(QRectF(18, 18, b * 0.25, 8), 3, 3)
        qp.setBrush(QColor(self.f.get("akzent2", "#ffd400")))
        qp.drawEllipse(QRectF(b - 44, 13, 28, 28))
        qp.end()


class Willkommen(QMainWindow):
    def __init__(self, live=False):
        super().__init__()
        self.live = live
        self.setWindowTitle("Willkommen bei Biblix")
        self.setWindowIcon(QIcon.fromTheme("biblix"))
        self.resize(1080, 720)
        self.wahl_preset = "bibi-tech"
        self.wahl_modus = "dunkel"
        self.schritte = (["live"] if live else
                         ["start", "design", "bildschirme", "sicherheit", "spiele", "konten", "fertig"])
        namen = {"live": "Biblix ausprobieren", "start": "Willkommen", "design": "Design", "bildschirme": "Bildschirme",
                 "sicherheit": "Sicherheit", "spiele": "Spiele", "konten": "Konten", "fertig": "Fertig"}
        wurzel = QWidget()
        h = QHBoxLayout(wurzel)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        seiten = QWidget()
        seiten.setObjectName("seitenleiste")
        seiten.setFixedWidth(220)
        sl = QVBoxLayout(seiten)
        sl.setContentsMargins(0, 20, 0, 14)
        kopf = label("WILLKOMMEN")
        kopf.setStyleSheet(f"color: {F['akzent2']}; font-weight: 800; letter-spacing: 3px; padding: 0 18px 12px 18px;")
        sl.addWidget(kopf)
        self.nav = QListWidget()
        for i, s in enumerate(self.schritte):
            self.nav.addItem(QListWidgetItem(f"{i + 1}  {namen[s]}" if not live else namen[s]))
        sl.addWidget(self.nav, 1)
        spruch = label("AUF BIBLIX GEHT DAS.", "leise")
        spruch.setStyleSheet("padding: 0 18px; font-family: 'DejaVu Sans Mono'; font-size: 8.5pt;")
        sl.addWidget(spruch)
        h.addWidget(seiten)
        rechts = QVBoxLayout()
        rechts.setSpacing(0)
        self.stack = QStackedWidget()
        rechts.addWidget(self.stack, 1)
        fuss = QWidget()
        fuss.setObjectName("fuss")
        fl = QHBoxLayout(fuss)
        fl.setContentsMargins(24, 12, 24, 12)
        self.zurueck = knopf("Zurück", cb=lambda: self.gehe(self.nav.currentRow() - 1))
        self.weiter = knopf("Weiter", True, lambda: self.gehe(self.nav.currentRow() + 1))
        self.status = label("", "leise")
        fl.addWidget(self.zurueck)
        fl.addWidget(self.status, 1)
        fl.addWidget(self.weiter)
        rechts.addWidget(fuss)
        if live:
            fuss.hide()
        h.addLayout(rechts, 1)
        self.setCentralWidget(wurzel)
        self.setStyleSheet(STIL)
        self.nav.currentRowChanged.connect(self.zeigen)
        self.nav.setCurrentRow(0)

    # ---- Navigation

    def gehe(self, i):
        if i >= len(self.schritte):
            self.fertig()
            return
        self.nav.setCurrentRow(max(0, i))

    def zeigen(self, i):
        alt = self.stack.currentWidget()
        neu = getattr(self, "seite_" + self.schritte[i])()
        self.stack.addWidget(neu)
        self.stack.setCurrentWidget(neu)
        if alt is not None:
            self.stack.removeWidget(alt)
            alt.deleteLater()
        self.zurueck.setEnabled(i > 0)
        self.weiter.setText("Los geht's" if self.schritte[i] == "fertig" else "Weiter")
        self.status.setText(f"Schritt {i + 1} von {len(self.schritte)} · alles lässt sich überspringen")

    def seite(self, titel, text=""):
        s = QScrollArea()
        s.setWidgetResizable(True)
        innen = QWidget()
        innen.setObjectName("seite")
        lay = QVBoxLayout(innen)
        lay.setContentsMargins(36, 30, 36, 24)
        lay.setSpacing(14)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        lay.addWidget(label(titel, "h1"))
        if text:
            lay.addWidget(label(text, "leise"))
        s.setWidget(innen)
        return s, lay

    def fertig(self):
        try:
            KONFIG.mkdir(parents=True, exist_ok=True)
            ERLEDIGT.write_text(json.dumps({"erledigt": True}), encoding="utf-8")
        except OSError:
            pass
        self.close()

    def closeEvent(self, ev):
        # Auch beim Schliessen nicht nochmal automatisch zeigen; der Assistent bleibt im Startmenue
        if not self.live:
            try:
                KONFIG.mkdir(parents=True, exist_ok=True)
                if not ERLEDIGT.exists():
                    ERLEDIGT.write_text(json.dumps({"erledigt": False, "geschlossen": True}), encoding="utf-8")
            except OSError:
                pass
        super().closeEvent(ev)

    # ---- Live-System

    def seite_live(self):
        s, lay = self.seite("Biblix ausprobieren", "Du läufst gerade vom USB-Stick. Auf deinem PC ist noch nichts "
                                                   "verändert. Schau dich in Ruhe um oder installiere Biblix gleich.")
        lay.addWidget(PromptB(140), 0, Qt.AlignmentFlag.AlignLeft)
        reihe = QHBoxLayout()
        for titel, text, haupt, cb in (
                ("Ausprobieren", "S-Launcher, Bibiplexx, Design-App und Spiele testen. Nichts wird gespeichert.",
                 False, self.close),
                ("Biblix installieren", "Neben Windows oder allein. Vorher Windows-Schnellstart ausschalten und, "
                 "falls an, BitLocker pausieren.", True, self.installieren)):
            k, kl = karte()
            kl.addWidget(label(f"<b>{titel}</b>", "gross"))
            kl.addWidget(label(text, "leise"))
            kl.addWidget(knopf(titel, haupt, cb), 0, Qt.AlignmentFlag.AlignLeft)
            reihe.addWidget(k)
        lay.addLayout(reihe)
        return s

    def installieren(self):
        for prog in ("install-debian", "calamares"):
            if shutil.which(prog):
                starten("pkexec", prog) if prog == "calamares" else starten(prog)
                return
        self.status.setText("Installer nicht gefunden.")

    # ---- Schritte

    def seite_start(self):
        s, lay = self.seite("Schön, dass du da bist.",
                            "Biblix ist installiert. In ein paar Schritten richtest du es dir ein: Aussehen, "
                            "Bildschirme, Sicherheit, Spiele und Konten. Jeder Schritt lässt sich überspringen "
                            "und später in der Haustechnik oder in Biblix Design nachholen.")
        lay.addWidget(PromptB(150), 0, Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(label("DEIN SYSTEM. DEIN PROBLEM.", "leise"))
        return s

    def seite_design(self):
        s, lay = self.seite("Wie soll dein Biblix aussehen?",
                            "Jedes Design gehört zu einer Bibi-Firma. Alles lässt sich später in Biblix Design "
                            "einzeln mischen.")
        modus = QHBoxLayout()
        for m, text in (("dunkel", "Dunkel"), ("hell", "Hell"), ("auto", "Tag hell, Abend dunkel")):
            b = knopf(text, m == self.wahl_modus, lambda _=False, mm=m: self.modus_setzen(mm))
            modus.addWidget(b)
        modus.addStretch(1)
        lay.addLayout(modus)
        gitter = QGridLayout()
        gitter.setSpacing(14)
        presets = []
        for f in sorted(PRESETS.glob("*.json")):
            try:
                presets.append(json.loads(f.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                pass
        presets.sort(key=lambda p: (p.get("id") != "bibi-tech", p.get("name", "")))
        for i, p in enumerate(presets):
            k, kl = karte("gewaehlt" if p.get("id") == self.wahl_preset else "karte")
            farben = p.get("hell" if self.wahl_modus == "hell" else "dunkel", {})
            kl.addWidget(Muster(farben))
            kl.addWidget(label(f"<b>{p.get('name', p.get('id'))}</b>"))
            kl.addWidget(label(p.get("beschreibung", ""), "leise"))
            kl.addWidget(knopf("Gewählt" if p.get("id") == self.wahl_preset else "Wählen",
                               p.get("id") == self.wahl_preset, lambda _=False, pid=p.get("id"): self.preset_waehlen(pid)))
            gitter.addWidget(k, i // 3, i % 3)
        lay.addLayout(gitter)
        r = QHBoxLayout()
        self.anwenden_knopf = knopf("Design übernehmen", True, self.design_anwenden)
        r.addWidget(self.anwenden_knopf)
        r.addStretch(1)
        lay.addLayout(r)
        return s

    def modus_setzen(self, m):
        self.wahl_modus = m
        self.zeigen(self.nav.currentRow())

    def preset_waehlen(self, pid):
        self.wahl_preset = pid
        self.zeigen(self.nav.currentRow())

    def design_anwenden(self):
        self.anwenden_knopf.setEnabled(False)
        self.status.setText("Biblix färbt um … (dauert ein paar Sekunden)")
        p = QProcess(self)
        p.finished.connect(lambda code, _s: self.status.setText(
            "Design übernommen." if code == 0 else "Das Design ließ sich nicht ganz übernehmen (Biblix Design öffnen)."))
        p.start("biblix-design", ["anwenden", self.wahl_preset, f"--{self.wahl_modus}"])

    def seite_bildschirme(self):
        s, lay = self.seite("Bildschirme", "Biblix stellt jeden Bildschirm auf die höchste Bildrate, z. B. 240 Hz. "
                                           "Prüf kurz, ob alles stimmt.")
        rc, out = run(["biblix-bildschirme", "--json"])
        try:
            liste = json.loads(out[out.index("["):]) if "[" in out else []
        except ValueError:
            liste = []
        if not liste:
            lay.addWidget(label("Keine Angaben (vielleicht läuft KDE noch an). Später: Haustechnik → Bildschirme.", "leise"))
        for b in liste:
            k, kl = karte()
            ok = b.get("jetzt", 0) >= b.get("moeglich", 0)
            kl.addWidget(label(f"<b>{b.get('name')}</b> &nbsp; {b.get('jetzt')} Hz "
                               + ("✓ höchste Bildrate" if ok else f"(möglich: {b.get('moeglich')} Hz)")))
            lay.addWidget(k)
        r = QHBoxLayout()
        r.addWidget(knopf("Alle auf höchste Bildrate", True, lambda: (run(["biblix-bildschirme", "--jetzt"], 40),
                                                                        self.zeigen(self.nav.currentRow()))))
        r.addWidget(knopf("Anzeige-Einstellungen", cb=lambda: starten("systemsettings", "kcm_kscreen")))
        r.addStretch(1)
        lay.addLayout(r)
        return s

    def seite_sicherheit(self):
        s, lay = self.seite("Sicherheit", "Zwei Dinge, die Biblix für dich vorbereitet hat.")
        k, kl = karte()
        kl.addWidget(label("<b>Secure Boot</b>"))
        kl.addWidget(label("Dein PC hat beim ersten Start einen eigenen Treiber-Schlüssel bekommen. Meldest du ihn "
                           "einmal beim PC an (blauer Bildschirm beim nächsten Start), kann Secure Boot an bleiben. "
                           "Wichtig für Windows-Spiele mit Anti-Cheat.", "leise"))
        kl.addWidget(knopf("In der Haustechnik einrichten", True, lambda: starten("biblix-haustechnik", "secureboot")),
                     0, Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(k)
        k, kl = karte()
        kl.addWidget(label("<b>Zeitmaschine</b>"))
        if Path("/etc/snapper/configs/root").exists():
            kl.addWidget(label("Vor und nach jedem Update hält Biblix den Zustand fest. Geht etwas kaputt, drehst du "
                               "das Update in der Haustechnik unter „Zeitmaschine“ zurück. Deine Dateien bleiben "
                               "dabei unverändert.", "leise"))
        else:
            kl.addWidget(label("Biblix liegt hier nicht auf Btrfs, darum gibt es keine automatischen Schnappschüsse. "
                               "Für Sicherungen kannst du Timeshift benutzen.", "leise"))
        lay.addWidget(k)
        return s

    def seite_spiele(self):
        s, lay = self.seite("Spiele", "Steam läuft auf Biblix mit Proton. Windows-Spiele auf deinen anderen Platten "
                                      "lassen sich direkt einbinden.")
        for titel, text, cb in (
                ("Steam", "Im S-Launcher unter Spiele: anmelden, Bibliothek einrichten.",
                 lambda: starten("s-launcher", "--spiele")),
                ("Spieleplatten", "Eine leere Platte als Spieleplatte einrichten (Haustechnik → Platten).",
                 lambda: starten("biblix-haustechnik", "platten")),
                ("Windows-Spiele", "Spiele mit Anti-Cheat startest du per Knopf in Windows (Neustart in Windows).",
                 None)):
            k, kl = karte()
            kl.addWidget(label(f"<b>{titel}</b>"))
            kl.addWidget(label(text, "leise"))
            if cb:
                kl.addWidget(knopf("Öffnen", cb=cb), 0, Qt.AlignmentFlag.AlignLeft)
            lay.addWidget(k)
        return s

    def seite_konten(self):
        s, lay = self.seite("Konten", "Deine Dateien und Programme, die du schon kennst.")
        eintraege = [("OneDrive", "Deinen OneDrive-Ordner mit ~/OneDrive verbinden.",
                      lambda: starten("konsole", "--hold", "-e", "biblix-onedrive"))]
        if shutil.which("claude-desktop"):
            eintraege.append(("Claude", "Anmelden, dann hilft dir Claude direkt auf Biblix.",
                              lambda: starten("claude-desktop")))
        eintraege.append(("Apps", "Weitere Programme gibt es im S-Launcher, ein Klick genügt.",
                          lambda: starten("s-launcher")))
        for titel, text, cb in eintraege:
            k, kl = karte()
            kl.addWidget(label(f"<b>{titel}</b>"))
            kl.addWidget(label(text, "leise"))
            kl.addWidget(knopf("Öffnen", cb=cb), 0, Qt.AlignmentFlag.AlignLeft)
            lay.addWidget(k)
        return s

    def seite_fertig(self):
        s, lay = self.seite("Fertig.", "Alles, was du hier übersprungen hast, findest du jederzeit wieder: "
                                       "„Willkommen bei Biblix“ im Startmenü, die Haustechnik und Biblix Design.")
        lay.addWidget(PromptB(150), 0, Qt.AlignmentFlag.AlignLeft)
        t = label("AUF BIBLIX GEHT DAS.")
        t.setStyleSheet(f"font-family: 'DejaVu Sans Mono'; font-size: 16pt; font-weight: 800; color: {F['akzent']};")
        lay.addWidget(t)
        return s


def main():
    autostart = "--autostart" in sys.argv
    live = live_system()
    if autostart and not live:
        # Nur auf frisch installierten Systemen aus der ISO 2.0+ und nur einmal
        if not ISO.exists() or ERLEDIGT.exists():
            return 0
    app = QApplication(sys.argv[:1])
    app.setApplicationName("Willkommen bei Biblix")
    app.setDesktopFileName("de.biblix.Willkommen")
    w = Willkommen(live=live)
    # Beim Anmelden etwas warten, bis Plasma steht
    QTimer.singleShot(2500 if autostart else 0, w.show)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
