#!/usr/bin/env python3
"""S-Launcher - App-Browser und Spielezentrale von Biblix.

Apps kommen von Flathub (Flatpak). Spiele laufen ueber Steam (Flatpak),
dazu GameMode, MangoHud und Energieprofile.

    s-launcher            startet mit "Entdecken"
    s-launcher --spiele   startet direkt im Spielebereich
"""
import json
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

from PyQt6 import sip
from PyQt6.QtCore import QObject, QPoint, QProcess, QRect, QSize, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QGuiApplication, QIcon, QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QFrame, QHBoxLayout, QLabel, QLayout, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

import welten

VERSION = "1.0"
API = "https://flathub.org/api/v2"
FLATHUB_REPO = "https://dl.flathub.org/repo/flathub.flatpakrepo"
STEAM_ID = "com.valvesoftware.Steam"
STEAM_ROOTS = [
    Path.home() / ".var/app/com.valvesoftware.Steam/.local/share/Steam",
    Path.home() / ".local/share/Steam",
    Path.home() / ".steam/steam",
]
STEAM_SKIP = re.compile(r"^(Proton|Steam Linux Runtime|Steamworks Common)", re.I)
LAUNCH_OPTIONS = "MANGOHUD=1 gamemoderun %command%"
# HDR ueber Gamescope (laeuft in KDE Plasma als Vollbild mit HDR-Weitergabe)
LAUNCH_OPTIONS_HDR = "DXVK_HDR=1 gamescope -f --hdr-enabled -- gamemoderun %command%"
SYSTEM_UPDATE = "/usr/lib/biblix/biblix-system-update"

CATEGORIES = [
    ("Game", "Spiele", "applications-games"),
    ("AudioVideo", "Audio & Video", "applications-multimedia"),
    ("Graphics", "Grafik", "applications-graphics"),
    ("Network", "Internet", "applications-internet"),
    ("Office", "Büro", "applications-office"),
    ("Development", "Entwicklung", "applications-development"),
    ("Education", "Bildung", "applications-education"),
    ("Science", "Wissenschaft", "applications-science"),
    ("System", "System", "applications-system"),
    ("Utility", "Werkzeuge", "applications-utilities"),
]
# Feste Empfehlungen fuer den Spielebereich (alles echte Flathub-IDs)
# Startseite "Fuer den Alltag" (WhatsApp ueber ZapZap: es gibt keine offizielle Linux-App)
EVERYDAY = [
    "com.rtosta.zapzap", "com.discordapp.Discord", "com.spotify.Client",
    "com.google.Chrome", "org.telegram.desktop",
]
GAME_TOOLS = [
    "net.lutris.Lutris", "com.heroicgameslauncher.hgl", "com.usebottles.bottles",
    "net.davidotek.pupgui2", "org.prismlauncher.PrismLauncher", "io.github.ilya_zlobintsev.LACT",
]
# Zubehoer-Seite: Ersatz fuer Hersteller-Software unter Windows (alles echte Flathub-IDs)
ACCESSORIES = [
    ("Headset und Ton", "Equalizer, Mikrofon-Rauschfilter, Raumklang-Ersatz (z. B. für JBL Quantum)",
     ["com.github.wwmm.easyeffects"]),
    ("Aufnehmen und Streamen", "Ersatz für ShadowPlay / Instant Replay",
     ["com.dec05eba.gpu_screen_recorder", "com.obsproject.Studio"]),
    ("RGB, Maus, Tastatur", "Ersatz für iCUE, Synapse, G Hub, Aura",
     ["org.openrgb.OpenRGB", "org.freedesktop.Piper", "io.github.pwr_solaar.solaar"]),
    ("VR", "Quest/Pico kabellos über WiVRn, Index/Vive über SteamVR in Steam",
     ["io.github.wivrn.wivrn", "com.valvesoftware.SteamLink"]),
    ("System im Blick", "Ersatz für HWiNFO, Task-Manager und Stream Deck",
     ["io.missioncenter.MissionCenter", "com.core447.StreamController", "com.github.Matoking.protontricks"]),
]

STYLE = """
* { font-size: 10.5pt; }
QMainWindow, #page { background: #0b1820; color: #e3f3f8; }
QLabel { color: #e3f3f8; }
QLabel#muted { color: #8fb0bf; }
QLabel#h1 { font-size: 20pt; font-weight: 700; }
QLabel#h2 { font-size: 13pt; font-weight: 600; margin-top: 10px; }
QLabel#brand { font-size: 15pt; font-weight: 800; color: #3fd0ee; padding: 14px 12px 4px 14px; }
QLabel#slogan { color: #ffd23f; font-size: 8.5pt; padding: 0 14px 12px 14px; font-weight: 600; }
#sidebar { background: #071118; border-right: 1px solid #1f3946; }
QListWidget#nav { background: transparent; border: none; color: #cfe6ee; outline: 0; }
QListWidget#nav::item { padding: 9px 10px; border-radius: 8px; margin: 1px 8px; }
QListWidget#nav::item:selected { background: #13323f; color: #3fd0ee; }
QListWidget#nav::item:hover { background: #10242e; }
#topbar { background: #0d1f28; border-bottom: 1px solid #1f3946; }
QLineEdit { background: #13242e; border: 1px solid #1f3946; border-radius: 9px; padding: 7px 11px; color: #e3f3f8; }
QLineEdit:focus { border-color: #3fd0ee; }
QPushButton { background: #13323f; color: #e3f3f8; border: 1px solid #1f4a5a; border-radius: 8px; padding: 6px 14px; }
QPushButton:hover { background: #18404f; }
QPushButton:disabled { color: #5d7a86; background: #10202a; border-color: #1a2f3a; }
QPushButton#primary { background: #0aa5c6; border-color: #0aa5c6; color: #001319; font-weight: 700; }
QPushButton#primary:hover { background: #3fd0ee; }
QPushButton#yellow { background: #ffd23f; border-color: #ffd23f; color: #1b1500; font-weight: 700; }
QPushButton#danger { color: #ff9a9a; border-color: #5a2a2a; background: #2a1416; }
QFrame#card { background: #0f222c; border: 1px solid #1f3946; border-radius: 12px; }
QFrame#card:hover { border-color: #3fd0ee; }
QFrame#hero { border-radius: 16px; background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f6e86, stop:1 #072a36); }
QFrame#panel { background: #0f222c; border: 1px solid #1f3946; border-radius: 12px; }
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
#statusbar { background: #071118; border-top: 1px solid #1f3946; }
QProgressBar { background: #13242e; border: none; border-radius: 4px; max-height: 8px; }
QProgressBar::chunk { background: #3fd0ee; border-radius: 4px; }
QComboBox { background: #13242e; border: 1px solid #1f3946; border-radius: 8px; padding: 5px 10px; color: #e3f3f8; }
QCheckBox { color: #e3f3f8; }
QLabel#weltname { color: #8fb0bf; font-size: 8.5pt; padding: 0 14px 10px 14px; }
QPushButton#gold { background: #d4a73c; border-color: #d4a73c; color: #2a1f05; font-weight: 700; }
QPushButton#gold:hover { background: #e2bb58; }
QFrame#weltmenue { background: #0f222c; border: 1px solid #3fd0ee; border-radius: 6px; }
QPushButton#weltwahl { text-align: left; padding: 6px 12px; }
QPushButton#weltwahl:checked { background: #0aa5c6; color: #001319; border-color: #0aa5c6; }
QToolButton#weltknopf { background: transparent; border: none; border-radius: 8px; }
QToolButton#weltknopf:hover { background: #13323f; }
QFrame#meldung { background: #0f222c; border: 1px solid #3fd0ee; border-radius: 12px; }
"""

# Farben folgen dem aktuellen Biblix-Design (App "Biblix Design" schreibt ~/.config/biblix/palette.json).
# Ohne Design bleiben die klassischen S-Launcher-Farben.
DESIGN_FARBEN = {
    "#0b1820": "grund", "#e3f3f8": "text", "#8fb0bf": "leise", "#3fd0ee": "akzent_hell", "#ffd23f": "akzent2",
    "#071118": "grund", "#1f3946": "rand", "#cfe6ee": "text", "#13323f": "auswahl", "#10242e": "karte",
    "#0d1f28": "flaeche", "#13242e": "karte", "#1f4a5a": "rand", "#18404f": "auswahl", "#5d7a86": "leise",
    "#10202a": "karte", "#1a2f3a": "rand", "#0aa5c6": "akzent", "#001319": "auf_akzent", "#1b1500": "auf_akzent2",
    "#0f222c": "karte", "#0f6e86": "akzent_dunkel", "#072a36": "grund",
}


def design_stil(text):
    try:
        pal = json.loads(welten.PALETTE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return text
    for alt, schluessel in DESIGN_FARBEN.items():
        if schluessel in pal:
            text = text.replace(alt, pal[schluessel])
    return text


def alive(obj):
    return obj is not None and not sip.isdeleted(obj)


def run(argv, timeout=15):
    """Kurzer, synchroner Befehl. Fehlt das Programm, kommt '' zurueck."""
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def norm(hit):
    """Flathub-Suchtreffer und Appstream-Daten auf ein gemeinsames Format bringen."""
    return {
        "app_id": hit.get("app_id") or hit.get("id") or "",
        "name": hit.get("name") or hit.get("app_id") or "",
        "summary": hit.get("summary") or "",
        "icon": hit.get("icon"),
        "developer": hit.get("developer_name") or "",
    }


# ---------------------------------------------------------------- Netzwerk

class Net(QObject):
    def __init__(self):
        super().__init__()
        self.nam = QNetworkAccessManager(self)
        self.pixmaps = {}

    def _request(self, url):
        req = QNetworkRequest(QUrl(url))
        req.setRawHeader(b"User-Agent", f"S-Launcher/{VERSION} (Biblix)".encode())
        return req

    def json(self, url, cb, body=None):
        req = self._request(url)
        if body is None:
            reply = self.nam.get(req)
        else:
            req.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
            reply = self.nam.post(req, json.dumps(body).encode())
        reply.finished.connect(lambda: self._json_done(reply, cb))

    def _json_done(self, reply, cb):
        if reply.error() != QNetworkReply.NetworkError.NoError:
            cb(None, reply.errorString())
        else:
            try:
                cb(json.loads(bytes(reply.readAll())), None)
            except ValueError as e:
                cb(None, str(e))
        reply.deleteLater()

    def pixmap(self, url, cb):
        if not url:
            return
        if url in self.pixmaps:
            cb(self.pixmaps[url])
            return
        reply = self.nam.get(self._request(url))
        reply.finished.connect(lambda: self._pix_done(url, reply, cb))

    def _pix_done(self, url, reply, cb):
        pm = QPixmap()
        if reply.error() == QNetworkReply.NetworkError.NoError and pm.loadFromData(bytes(reply.readAll())):
            self.pixmaps[url] = pm
            cb(pm)
        reply.deleteLater()


# ---------------------------------------------------------------- Auftraege

class Jobs(QObject):
    """Warteschlange fuer flatpak/pkexec. Flatpak sperrt parallel, also eins nach dem anderen."""
    changed = pyqtSignal()
    line = pyqtSignal(str)
    finished = pyqtSignal(str, bool)

    def __init__(self):
        super().__init__()
        self.queue = []
        self.proc = None
        self.current = None

    def add(self, key, title, argv):
        if self.busy(key):
            return
        self.queue.append((key, title, argv))
        self.changed.emit()
        self._next()

    def busy(self, key):
        return (self.current is not None and self.current[0] == key) or any(k == key for k, _, _ in self.queue)

    def title(self):
        if not self.current:
            return ""
        rest = f"  (+{len(self.queue)} wartend)" if self.queue else ""
        return self.current[1] + rest

    def _next(self):
        if self.proc or not self.queue:
            return
        self.current = self.queue.pop(0)
        argv = self.current[2]
        p = QProcess(self)
        p.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        p.readyReadStandardOutput.connect(self._read)
        p.finished.connect(lambda code, status: self._finish(code == 0 and status == QProcess.ExitStatus.NormalExit))
        p.errorOccurred.connect(self._error)
        self.proc = p
        self.changed.emit()
        p.start(argv[0], argv[1:])

    def _read(self):
        data = bytes(self.proc.readAllStandardOutput()).decode(errors="replace")
        for part in re.split(r"[\r\n]+", data):
            if part.strip():
                self.line.emit(part.strip()[:180])

    def _error(self, err):
        if err == QProcess.ProcessError.FailedToStart:
            self.line.emit(f"{self.current[2][0]} ist nicht installiert.")
            self._finish(False)

    def _finish(self, ok):
        if not self.current:
            return
        key = self.current[0]
        self.proc.deleteLater()
        self.proc = None
        self.current = None
        self.finished.emit(key, ok)
        self.changed.emit()
        self._next()


# ---------------------------------------------------------------- Flatpak / Steam

class Flatpak:
    @staticmethod
    def installed():
        apps = {}
        out = run(["flatpak", "list", "--app", "--columns=application,name,version,installation"])
        for row in out.splitlines():
            cols = row.split("\t")
            if len(cols) >= 4 and cols[0]:
                apps[cols[0]] = {"name": cols[1], "version": cols[2], "installation": cols[3]}
        return apps

    @staticmethod
    def install_argv(app_id):
        return ["flatpak", "install", "--user", "-y", "--noninteractive", "flathub", app_id]

    @staticmethod
    def remove_argv(app_id, installation):
        scope = "--system" if installation == "system" else "--user"
        return ["flatpak", "uninstall", scope, "-y", "--noninteractive", app_id]

    @staticmethod
    def launch(app_id, *args):
        QProcess.startDetached("flatpak", ["run", app_id, *args])


def steam_installed(apps):
    return STEAM_ID in apps or shutil.which("steam") is not None


def steam_open(apps, *args):
    if STEAM_ID in apps:
        Flatpak.launch(STEAM_ID, *args)
    else:
        QProcess.startDetached("steam", list(args))


def steam_library():
    """Installierte Steam-Spiele aus den appmanifest-Dateien aller Bibliotheken."""
    libs = []
    for root in STEAM_ROOTS:
        vdf = root / "steamapps/libraryfolders.vdf"
        if vdf.is_file():
            text = vdf.read_text(errors="replace")
            libs += [Path(p) for p in re.findall(r'"path"\s+"([^"]+)"', text)]
        if (root / "steamapps").is_dir():
            libs.append(root)
    games, seen = [], set()
    for lib in libs:
        for acf in sorted((lib / "steamapps").glob("appmanifest_*.acf")):
            try:
                text = acf.read_text(errors="replace")
            except OSError:
                continue
            fields = dict(re.findall(r'"(\w+)"\s+"([^"]*)"', text))
            appid, name = fields.get("appid"), fields.get("name", "")
            if not appid or appid in seen or appid == "228980" or STEAM_SKIP.match(name):
                continue
            seen.add(appid)
            games.append({"appid": appid, "name": name})
    return sorted(games, key=lambda g: g["name"].lower())


# ---------------------------------------------------------------- Layout

class FlowLayout(QLayout):
    """Karten fliessen in Zeilen und brechen je nach Fensterbreite um."""

    def __init__(self, parent=None, spacing=14):
        super().__init__(parent)
        self._items = []
        self.setSpacing(spacing)
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)
        # Karten kommen oft erst nach dem Laden dazu: Elternlayout muss neu rechnen
        self.invalidate()
        if self.parentWidget():
            self.parentWidget().updateGeometry()

    def count(self):
        return len(self._items)

    def itemAt(self, i):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._arrange(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._arrange(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        return size

    def _arrange(self, rect, test):
        x, y, line, sp = rect.x(), rect.y(), 0, self.spacing()
        for item in self._items:
            hint = item.sizeHint()
            if x > rect.x() and x + hint.width() > rect.right() + 1:
                x, y, line = rect.x(), y + line + sp, 0
            if not test:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x += hint.width() + sp
            line = max(line, hint.height())
        return y + line - rect.y()

    def clear(self):
        while self.count():
            w = self.takeAt(0).widget()
            if w:
                w.deleteLater()


def label(text, name=None, wrap=False):
    lb = QLabel(text)
    if name:
        lb.setObjectName(name)
    lb.setWordWrap(wrap)
    return lb


def button(text, name=None, cb=None):
    b = QPushButton(text)
    if name:
        b.setObjectName(name)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if cb:
        b.clicked.connect(cb)
    return b


class Page(QScrollArea):
    """Scrollbare Seite mit vertikalem Inhalt."""

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget()
        inner.setObjectName("page")
        self.body = QVBoxLayout(inner)
        self.body.setContentsMargins(28, 22, 28, 28)
        self.body.setSpacing(12)
        self.body.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(inner)

    def flow(self):
        holder = QWidget()
        fl = FlowLayout(holder)
        self.body.addWidget(holder)
        return fl

    def clear(self):
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ---------------------------------------------------------------- Karten

class AppCard(QFrame):
    def __init__(self, main, app):
        super().__init__()
        self.main, self.app = main, app
        self.setObjectName("card")
        self.setFixedSize(320, 136)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)
        self.icon = QLabel()
        self.icon.setFixedSize(64, 64)
        self.icon.setPixmap(QIcon.fromTheme(app["app_id"], QIcon.fromTheme("application-x-executable")).pixmap(64, 64))
        lay.addWidget(self.icon, 0, Qt.AlignmentFlag.AlignTop)
        col = QVBoxLayout()
        col.setSpacing(3)
        text_w = 320 - 24 - 64 - 12
        name = label("")
        name.setStyleSheet("font-weight: 700;")
        name.setText(name.fontMetrics().elidedText(app["name"], Qt.TextElideMode.ElideRight, text_w))
        col.addWidget(name)
        # Hoechstens zwei Zeilen, sonst rutscht der Text unter den Knopf
        summary = label("", "muted", wrap=True)
        summary.setText(summary.fontMetrics().elidedText(app["summary"], Qt.TextElideMode.ElideRight, text_w * 2 - 40))
        col.addWidget(summary)
        col.addStretch(1)
        self.btn = button("", cb=self.action)
        self.btn.setFixedHeight(28)
        col.addWidget(self.btn, 0, Qt.AlignmentFlag.AlignLeft)
        lay.addLayout(col, 1)
        main.net.pixmap(app.get("icon"), self.set_icon)
        main.state_changed.connect(self.update_state)
        self.update_state()
        main.einblenden(self)

    def set_icon(self, pm):
        if alive(self.icon):
            self.icon.setPixmap(pm.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def update_state(self):
        if not alive(self.btn):
            return
        state = self.main.state(self.app["app_id"])
        self.btn.setEnabled(state != "busy")
        self.btn.setText(self.main.knopf_text(state))
        self.btn.setObjectName("" if state == "installed" else "primary")
        self.btn.style().unpolish(self.btn)
        self.btn.style().polish(self.btn)

    def action(self):
        state = self.main.state(self.app["app_id"])
        if state == "installed":
            Flatpak.launch(self.app["app_id"])
        elif state == "none":
            self.main.install(self.app)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.main.show_detail(self.app)


class GameCard(QFrame):
    def __init__(self, main, game):
        super().__init__()
        self.setObjectName("card")
        self.setFixedSize(230, 158)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 10)
        lay.setSpacing(6)
        self.img = QLabel()
        self.img.setFixedSize(230, 107)
        self.img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img.setStyleSheet(design_stil("background:#072a36; border-top-left-radius:12px; border-top-right-radius:12px;"))
        self.img.setText(game["name"])
        lay.addWidget(self.img)
        row = QHBoxLayout()
        row.setContentsMargins(10, 0, 10, 0)
        name = label(game["name"])
        name.setMaximumWidth(140)
        row.addWidget(name, 1)
        row.addWidget(button("Spielen", "primary", lambda: steam_open(main.installed, f"steam://rungameid/{game['appid']}")))
        lay.addLayout(row)
        url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{game['appid']}/header.jpg"
        main.net.pixmap(url, self.set_img)

    def set_img(self, pm):
        if alive(self.img):
            self.img.setPixmap(pm.scaled(230, 107, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))


# ---------------------------------------------------------------- Hauptfenster

class Main(QMainWindow):
    state_changed = pyqtSignal()

    NAV = [
        ("hausmarke", "Hausmarke Bibi", None),
        ("discover", "Entdecken", "go-home"),
        ("games", "Spiele", "applications-games"),
        ("categories", "Kategorien", "view-list-icons"),
        ("installed", "Installiert", "drive-harddisk"),
        ("accessories", "Zubehör", "input-gaming"),
        ("updates", "Updates", "system-software-update"),
    ]

    def __init__(self, start="discover"):
        super().__init__()
        self.setWindowTitle("S-Launcher")
        self.setWindowIcon(QIcon.fromTheme("s-launcher", QIcon.fromTheme("system-software-install")))
        self.resize(1280, 820)
        self.net = Net()
        self.jobs = Jobs()
        self.installed = Flatpak.installed()
        self.history = []
        self.auftraege = {}
        self.bestell_nr = random.randint(100, 899)
        self.einblend_nr = 0
        self.einst = welten.laden()
        self.farben = welten.farben()
        self.welt_id = welten.welt_fuer(self.einst, self.farben)
        self.welt = welten.WELTEN[self.welt_id]

        self.jobs.changed.connect(self.on_jobs_changed)
        self.jobs.line.connect(lambda t: self.status_line.setText(t))
        self.jobs.finished.connect(self.on_job_finished)

        root = QWidget()
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        middle = QHBoxLayout()
        middle.setSpacing(0)
        outer.addLayout(middle, 1)

        # Seitenleiste
        side = QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(230)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(0, 6, 0, 10)
        sl.setSpacing(0)
        self.logo_platz = QHBoxLayout()
        self.logo_platz.setContentsMargins(14, 12, 8, 2)
        self.logo_platz.setSpacing(10)
        self.logo = None
        brand = label("S-Launcher", "brand")
        brand.setStyleSheet("padding: 0;")
        self.logo_platz.addWidget(brand)
        self.logo_platz.addStretch(1)
        sl.addLayout(self.logo_platz)
        slogan = label("AUF BIBLIX GEHT DAS.", "slogan")
        slogan.setStyleSheet("padding: 6px 14px 2px 14px;")
        sl.addWidget(slogan)
        self.welt_label = label("", "weltname")
        sl.addWidget(self.welt_label)
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setIconSize(QSize(22, 22))
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for key, text, _icon in self.NAV:
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.nav.addItem(item)
        self.nav.currentItemChanged.connect(self.on_nav)
        sl.addWidget(self.nav, 1)
        sl.addWidget(label(f"  Biblix · S-Launcher {VERSION}", "muted"))
        middle.addWidget(side)

        # Inhalt
        content = QVBoxLayout()
        content.setSpacing(0)
        top = QWidget()
        top.setObjectName("topbar")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(16, 10, 12, 10)
        self.back_btn = button("‹ Zurück", cb=self.go_back)
        self.back_btn.setEnabled(False)
        tl.addWidget(self.back_btn)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Apps und Spiele auf Flathub suchen …")
        self.search.setClearButtonEnabled(True)
        self.search.returnPressed.connect(self.do_search)
        tl.addWidget(self.search, 1)
        # Platz fuer die Anzeige der Welt (Stockwerk, Abholbildschirm) und den Welt-Knopf
        self.anzeige_platz = QHBoxLayout()
        self.anzeige_platz.setContentsMargins(0, 0, 0, 0)
        tl.addLayout(self.anzeige_platz)
        self.anzeige = None
        self.knopf_platz = QHBoxLayout()
        self.knopf_platz.setContentsMargins(0, 0, 0, 0)
        tl.addLayout(self.knopf_platz)
        self.welt_knopf = None
        content.addWidget(top)
        self.stack = QStackedWidget()
        content.addWidget(self.stack, 1)
        middle.addLayout(content, 1)
        self.uebergang = welten.Uebergang(self.stack)

        # Statusleiste fuer laufende Installationen
        bar = QWidget()
        bar.setObjectName("statusbar")
        self.statusbar = bar
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(16, 7, 16, 7)
        self.job_label = label("")
        bl.addWidget(self.job_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedWidth(160)
        self.progress.hide()
        bl.addWidget(self.progress)
        self.status_line = label("", "muted")
        self.status_line.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        bl.addWidget(self.status_line, 1)
        outer.addWidget(bar)

        self.setCentralWidget(root)
        self.meldung = welten.Meldung(root)
        self.welt_anwenden(neu_bauen=False)

        # Flathub fuer Benutzerinstallationen sicherstellen (ohne Passwortabfrage)
        QProcess.startDetached("flatpak", ["remote-add", "--user", "--if-not-exists", "flathub", FLATHUB_REPO])

        keys = [k for k, _, _ in self.NAV]
        self.nav.setCurrentRow(keys.index(start) if start in keys else 1)

    # ---- Welt

    def welt_anwenden(self, neu_bauen=True):
        """Farben, Woerter, Symbole und Anzeigen der aktuellen Welt setzen."""
        self.farben = welten.farben()
        self.welt_id = welten.welt_fuer(self.einst, self.farben)
        self.welt = welten.WELTEN[self.welt_id]
        f = self.farben
        self.setStyleSheet(design_stil(STYLE))
        animiert = self.einst["animationen"] == "voll"

        if self.logo is not None:
            self.logo.deleteLater()
        self.logo = welten.LogoB(f, blinken=animiert)
        self.logo_platz.insertWidget(0, self.logo)
        self.welt_label.setText(f"Welt: {self.welt['name']}" + (" · auto" if self.einst["welt"] == "auto" else ""))

        etagen = self.welt.get("etagen")
        for i, (key, _, icon) in enumerate(self.NAV):
            item = self.nav.item(i)
            item.setText(self.welt["nav"][key])
            item.setToolTip(welten.NAV_KLAR[key])
            if key == "hausmarke":
                item.setIcon(welten.hausmarke_symbol())
                item.setForeground(QColor(welten.gold_text(f)))
            elif etagen:
                item.setIcon(welten.etagen_symbol(etagen[key], f))
            else:
                item.setIcon(QIcon.fromTheme(icon))

        if self.anzeige is not None:
            self.anzeige.deleteLater()
            self.anzeige = None
        if self.welt_id == "tower":
            self.anzeige = welten.Stockwerk(f)
            cur = self.nav.currentItem()
            if cur:
                self.anzeige.setzen(etagen[cur.data(Qt.ItemDataRole.UserRole)])
        elif self.welt_id == "theke":
            self.anzeige = welten.Abholanzeige(f)
        if self.anzeige is not None:
            self.anzeige_platz.addWidget(self.anzeige)

        if self.welt_knopf is not None:
            self.welt_knopf.deleteLater()
        self.welt_knopf = welten.WeltKnopf(f)
        self.welt_knopf.clicked.connect(self.welt_menue)
        self.knopf_platz.addWidget(self.welt_knopf)

        if not self.jobs.current:
            self.job_label.setText(self.welt["bereit"])
        self.state_changed.emit()
        item = self.nav.currentItem()
        if neu_bauen and item is not None:
            for p in self.history:
                self._drop(p)
            self.history.clear()
            self.einblend_nr = 0
            page = getattr(self, "page_" + item.data(Qt.ItemDataRole.UserRole))()
            self.set_page(page, remember=False, art="blende")

    def welt_menue(self):
        menue = welten.WeltMenue(self, self.einst, self.farben)
        menue.setStyleSheet(design_stil(STYLE))
        menue.geaendert.connect(self.welt_geaendert)
        menue.adjustSize()
        pos = self.welt_knopf.mapToGlobal(self.welt_knopf.rect().bottomRight())
        menue.move(pos.x() - menue.width(), pos.y() + 6)
        menue.show()

    def welt_geaendert(self, e):
        alt = self.welt_id
        self.einst = e
        welten.speichern(e)
        self.welt_anwenden()
        if self.welt_id != alt:
            welten.klang(self.welt["klaenge"].get("fertig"), self.einst)

    def knopf_text(self, state):
        return {"busy": self.welt["laeuft"], "installed": "Öffnen", "none": self.welt["installieren"]}[state]

    def einblenden(self, w):
        if self.einst["animationen"] == "voll":
            welten.einblenden(w, min(self.einblend_nr, 14) * 35)
            self.einblend_nr += 1

    # ---- Zustand

    def state(self, app_id):
        if self.jobs.busy(app_id):
            return "busy"
        return "installed" if app_id in self.installed else "none"

    def install(self, app):
        if self.jobs.busy(app["app_id"]):
            return
        self.bestell_nr += 1
        nr = self.bestell_nr
        self.auftraege[app["app_id"]] = ("install", app["name"], nr)
        welten.klang(self.welt["klaenge"].get("start"), self.einst)
        self.jobs.add(app["app_id"], self.welt["auftrag"].format(name=app["name"], nr=f"{nr:04d}"),
                      Flatpak.install_argv(app["app_id"]))

    def remove(self, app_id, name):
        inst = self.installed.get(app_id, {}).get("installation", "user")
        self.auftraege[app_id] = ("remove", name, None)
        self.jobs.add(app_id, f"Entferne {name}", Flatpak.remove_argv(app_id, inst))

    def on_jobs_changed(self):
        busy = self.jobs.current is not None
        self.progress.setVisible(busy)
        if busy:
            self.job_label.setText(self.jobs.title())
            art, _, nr = self.auftraege.get(self.jobs.current[0], (None, None, None))
            if art == "install" and isinstance(self.anzeige, welten.Abholanzeige):
                self.anzeige.zubereiten(nr)
        self.state_changed.emit()

    def on_job_finished(self, key, ok):
        self.installed = Flatpak.installed()
        art, name, nr = self.auftraege.pop(key, (None, key, None))
        if ok:
            self.job_label.setText(self.welt["bereit"] + "  AUF BIBLIX GEHT DAS.")
            self.status_line.setText("")
            if art == "install":
                text = self.welt["fertig_text"].format(name=name, nr=f"{nr:04d}")
            elif art == "remove":
                text = f"{name} wurde entfernt."
            else:
                text = "Fertig. AUF BIBLIX GEHT DAS."
            animiert = self.einst["animationen"] != "aus"
            symbol = QIcon.fromTheme("edit-delete") if art == "remove" else welten.hausmarke_symbol(28)
            self.meldung.zeigen(text, symbol, self.statusbar.height(), animiert)
            if art == "install":
                welten.klang(self.welt["klaenge"].get("fertig"), self.einst)
                if isinstance(self.anzeige, welten.Abholanzeige):
                    self.anzeige.fertig(nr, blinken=animiert)
        else:
            self.job_label.setText("Hat nicht geklappt.")
            if isinstance(self.anzeige, welten.Abholanzeige):
                self.anzeige.frei()
            self.status_line.setText("Details siehe letzte Meldung. Internet und Speicherplatz prüfen.")
        self.state_changed.emit()
        page = self.stack.currentWidget()
        if getattr(page, "refresh_on_job", False):
            self.rebuild_current()

    # ---- Navigation

    def wechsel(self, tausch, art=None, beschriftung="", richtung=1):
        """Seitenwechsel mit der Animation der Welt (oder ohne)."""
        modus = self.einst["animationen"]
        if art == "keine" or modus == "aus" or not self.isVisible() or self.stack.currentWidget() is None:
            self.uebergang.abschliessen()
            tausch()
            return
        art = art or self.welt.get("uebergang", "blende")
        dauer = 1.0
        if modus == "dezent":
            art, dauer = "blende", 0.7
        self.uebergang.starten(art, tausch, self.farben, dauer, beschriftung, richtung)

    def set_page(self, page, remember=True, art=None, beschriftung="", richtung=1):
        def tausch():
            old = self.stack.currentWidget()
            if remember and old is not None:
                self.history.append(old)
            elif old is not None:
                self._drop(old)
            self.stack.addWidget(page)
            self.stack.setCurrentWidget(page)
            self.back_btn.setEnabled(bool(self.history))
        if art is None and remember:
            # Innerhalb eines Bereichs: die Theke schiebt, sonst eine kurze Blende
            art = "schieben" if self.welt_id == "theke" else "blende"
        self.wechsel(tausch, art, beschriftung, richtung)

    def _drop(self, page):
        # Fokus vorher rausholen, sonst springt er auf ein Feld der neuen Seite
        # und die Seite scrollt dorthin
        focus = QApplication.focusWidget()
        if focus is not None and (focus is page or page.isAncestorOf(focus)):
            self.nav.setFocus()
        self.stack.removeWidget(page)
        page.deleteLater()

    def go_back(self):
        if not self.history:
            return

        def tausch():
            cur = self.stack.currentWidget()
            prev = self.history.pop()
            self.stack.setCurrentWidget(prev)
            self._drop(cur)
            self.back_btn.setEnabled(bool(self.history))
        self.wechsel(tausch, "schieben" if self.welt_id == "theke" else "blende", richtung=-1)

    def nav_zu(self, key):
        keys = [k for k, _, _ in self.NAV]
        self.nav.setCurrentRow(keys.index(key))

    def on_nav(self, item, prev=None):
        if item is None:
            return
        self.uebergang.abschliessen()
        for p in self.history:
            self._drop(p)
        self.history.clear()
        key = item.data(Qt.ItemDataRole.UserRole)
        self.einblend_nr = 0
        page = getattr(self, "page_" + key)()
        beschriftung = ""
        if isinstance(self.anzeige, welten.Stockwerk):
            etagen = self.welt["etagen"]
            if prev is not None:
                # Haustechnik liegt im Keller, also unter allem
                keys = [k for k, _, _ in self.NAV]
                hoehe = {k: (-1 if k == "updates" else i) for i, k in enumerate(keys)}
                beschriftung = etagen[key]
                self.anzeige.fahren(etagen[key], hoehe[key] > hoehe[prev.data(Qt.ItemDataRole.UserRole)])
                welten.klang(self.welt["klaenge"].get("seite"), self.einst)
            else:
                self.anzeige.setzen(etagen[key])
        self.set_page(page, remember=False, art=None if prev is not None else "keine", beschriftung=beschriftung)

    def rebuild_current(self):
        item = self.nav.currentItem()
        if item and not self.history:
            self.set_page(getattr(self, "page_" + item.data(Qt.ItemDataRole.UserRole))(), remember=False, art="keine")

    # ---- Hilfen fuer Seiten

    def fill_collection(self, page, title, url, body=None, hits_key="hits", limit=None):
        page.body.addWidget(label(title, "h2"))
        loading = label("Lädt …", "muted")
        page.body.addWidget(loading)
        flow = page.flow()

        def done(data, err):
            if not alive(loading):
                return
            if err or not isinstance(data, dict):
                loading.setText("Keine Verbindung zu Flathub. Internet prüfen und Seite neu öffnen.")
                return
            hits = data.get(hits_key) or []
            loading.setText("" if hits else "Nichts gefunden.")
            loading.setVisible(not hits)
            for hit in hits[:limit]:
                flow.addWidget(AppCard(self, norm(hit)))
        self.net.json(url, done, body)

    def add_app_by_id(self, flow, app_id):
        def done(data, err):
            if not err and isinstance(data, dict) and alive(flow):
                flow.addWidget(AppCard(self, norm(data)))
        self.net.json(f"{API}/appstream/{quote(app_id)}", done)

    # ---- Seiten

    def oeffnen_hausmarke(self, eintrag):
        befehl = eintrag.get("befehl") or []
        if befehl:
            QProcess.startDetached(befehl[0], befehl[1:])

    def hausmarke_flow(self, page, eintraege):
        flow = page.flow()
        animiert = self.einst["animationen"] == "voll"
        for e in eintraege:
            karte = welten.HausmarkeKarte(self.farben, e, animiert, self.oeffnen_hausmarke)
            flow.addWidget(karte)
            self.einblenden(karte)
        return flow

    def page_hausmarke(self):
        p = Page()
        p.body.addWidget(welten.HausmarkeKopf(
            self.farben, self.einst["animationen"] == "voll", "Hausmarke Bibi",
            "Apps, die für Biblix gebaut wurden. Neue Bibi-Apps kommen automatisch per Update dazu."))
        eintraege = welten.hausmarke()
        if not eintraege:
            p.body.addWidget(label("Noch keine Bibi-Apps gefunden.", "muted"))
            return p
        fertig = [e for e in eintraege if e.get("status") == "fertig"]
        bald = [e for e in eintraege if e.get("status") != "fertig"]
        if fertig:
            p.body.addWidget(label("Im Regal", "h2"))
            self.hausmarke_flow(p, fertig)
        if bald:
            p.body.addWidget(label("In Arbeit", "h2"))
            p.body.addWidget(label("Wird gerade gebaut. Sobald es fertig ist, steht es hier im Regal.", "muted"))
            self.hausmarke_flow(p, bald)
        return p

    def buehne_eintraege(self):
        """Wechselnde Eintraege fuer den grossen Kopf der Startseite."""
        kicker = {
            "tower": ("EG · Hausmarke Bibi", "2. Stock · Spiele", "Baustelle · Demnächst"),
            "theke": ("Empfehlung des Hauses", "Menü des Tages", "Bald auf der Karte"),
        }.get(self.welt_id, ("Hausmarke Bibi", "Spielen", "Demnächst"))
        eintraege = []
        hm = {e["id"]: e for e in welten.hausmarke()}
        design = hm.get("biblix-design")
        if design and design.get("status") == "fertig" and welten.hausmarke_da(design):
            eintraege.append({
                "kicker": kicker[0], "titel": "Biblix Design",
                "text": "Farben, Fenster, Startmenü und Hintergründe nach deinem Geschmack. Der S-Launcher zieht mit.",
                "knoepfe": [("Öffnen", "gold", lambda: self.oeffnen_hausmarke(design)),
                            ("Alle Bibi-Apps", "", lambda: self.nav_zu("hausmarke"))]})
        eintraege.append({
            "kicker": kicker[1], "titel": "Spielen auf Biblix",
            "text": "Steam mit Proton, GameMode und MangoHud. NVIDIA und AMD sind schon eingerichtet.",
            "knoepfe": [("Zu den Spielen", "yellow", lambda: self.nav_zu("games"))]})
        plexx = hm.get("bibiplexx")
        if plexx and plexx.get("status") != "fertig":
            eintraege.append({
                "kicker": kicker[2], "titel": "Bibiplexx",
                "text": "Filme und Serien im Bibiplexx-Stil. Wird gerade gebaut und kommt per Update.",
                "knoepfe": [("Zur Hausmarke", "", lambda: self.nav_zu("hausmarke"))]})
        return eintraege

    def page_discover(self):
        p = Page()
        p.body.addWidget(label(self.welt["nav"]["discover"], "h1"))
        p.body.addWidget(label(self.welt["untertitel"], "muted"))
        p.body.addWidget(welten.Buehne(self.welt_id, self.farben, self.einst["animationen"] == "voll",
                                       self.buehne_eintraege()))
        hm = welten.hausmarke()
        if hm:
            kopf = QHBoxLayout()
            titel = label("Hausmarke Bibi", "h2")
            titel.setStyleSheet(f"color: {welten.gold_text(self.farben)};")
            kopf.addWidget(titel)
            kopf.addStretch(1)
            alle = button("Alle ansehen ›", cb=lambda: self.nav_zu("hausmarke"))
            kopf.addWidget(alle, 0, Qt.AlignmentFlag.AlignBottom)
            p.body.addLayout(kopf)
            self.hausmarke_flow(p, hm[:3])
        p.body.addWidget(label("Für den Alltag", "h2"))
        everyday = p.flow()
        for app_id in EVERYDAY:
            self.add_app_by_id(everyday, app_id)
        self.fill_collection(p, "Beliebt", f"{API}/collection/popular?page=1&per_page=12")
        self.fill_collection(p, "Im Trend", f"{API}/collection/trending?page=1&per_page=12")
        self.fill_collection(p, "Neu auf Flathub", f"{API}/collection/recently-added?page=1&per_page=9")
        return p

    def page_categories(self):
        p = Page()
        p.body.addWidget(label(self.welt["nav"]["categories"], "h1"))
        flow = p.flow()
        for cat, name, icon in CATEGORIES:
            # "&" waere auf Knoepfen ein Tastenkuerzel, "&&" zeigt es an
            b = button(name.replace("&", "&&"), cb=lambda _=False, c=cat, n=name: self.show_category(c, n))
            b.setIcon(QIcon.fromTheme(icon))
            b.setIconSize(QSize(28, 28))
            b.setFixedSize(220, 64)
            flow.addWidget(b)
        return p

    def show_category(self, cat, name):
        p = Page()
        p.body.addWidget(label(name, "h1"))
        self.fill_collection(p, "Beliebteste zuerst", f"{API}/collection/category/{cat}?page=1&per_page=60")
        self.set_page(p)

    def do_search(self):
        q = self.search.text().strip()
        if not q:
            return
        p = Page()
        p.body.addWidget(label(f"Suche: {q}", "h1"))
        self.fill_collection(p, "Ergebnisse von Flathub", f"{API}/search", body={"query": q}, limit=60)
        self.set_page(p)

    def page_installed(self):
        self.installed = Flatpak.installed()
        p = Page()
        p.refresh_on_job = True
        p.body.addWidget(label(self.welt["nav"]["installed"], "h1"))
        if not self.installed:
            p.body.addWidget(label("Noch keine Flatpak-Apps installiert.", "muted"))
            return p
        for app_id, info in sorted(self.installed.items(), key=lambda kv: kv[1]["name"].lower()):
            row = QFrame()
            row.setObjectName("panel")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(12, 8, 12, 8)
            ic = QLabel()
            ic.setPixmap(QIcon.fromTheme(app_id, QIcon.fromTheme("application-x-executable")).pixmap(40, 40))
            rl.addWidget(ic)
            txt = QVBoxLayout()
            txt.addWidget(label(info["name"]))
            where = "für alle Benutzer" if info["installation"] == "system" else "nur für mich"
            txt.addWidget(label(f"{app_id} · {info['version'] or 'ohne Version'} · {where}", "muted"))
            rl.addLayout(txt, 1)
            rl.addWidget(button("Öffnen", cb=lambda _=False, a=app_id: Flatpak.launch(a)))
            rem = button("Entfernen", "danger", lambda _=False, a=app_id, n=info["name"]: self.remove(a, n))
            rem.setEnabled(not self.jobs.busy(app_id))
            rl.addWidget(rem)
            p.body.addWidget(row)
        return p

    def page_accessories(self):
        p = Page()
        p.body.addWidget(label(self.welt["nav"]["accessories"], "h1"))
        p.body.addWidget(label("Was unter Windows die Hersteller-Programme machen, übernehmen hier diese Apps.", "muted", wrap=True))
        panel = QFrame()
        panel.setObjectName("panel")
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(18, 14, 18, 14)
        pl.addWidget(label("Xbox-Controller: Kabel und Bluetooth gehen sofort. Für den Xbox-Funkadapter einmal "
                           "einrichten (holt die Firmware von Microsoft):", wrap=True))
        row = QHBoxLayout()
        cmd = "bibi biblix-xbox-funkadapter"
        field = QLineEdit(cmd)
        field.setReadOnly(True)
        row.addWidget(field, 1)
        row.addWidget(button("Im Terminal öffnen", "primary", lambda: QProcess.startDetached(
            "konsole", ["--hold", "-e", "bash", "-c", cmd])))
        pl.addLayout(row)
        p.body.addWidget(panel)
        for title, desc, ids in ACCESSORIES:
            p.body.addWidget(label(title, "h2"))
            p.body.addWidget(label(desc, "muted", wrap=True))
            flow = p.flow()
            for app_id in ids:
                self.add_app_by_id(flow, app_id)
        return p

    def page_updates(self):
        p = Page()
        p.body.addWidget(label(self.welt["nav"]["updates"], "h1"))
        panel = QFrame()
        panel.setObjectName("panel")
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(18, 16, 18, 16)
        pl.addWidget(label("Apps (Flatpak)", "h2"))
        info = label("Suche nach Updates …", "muted", wrap=True)
        pl.addWidget(info)
        pl.addWidget(button("Alle Apps aktualisieren", "primary", lambda: self.jobs.add(
            "@flatpak-update", "Aktualisiere Apps", ["flatpak", "update", "-y", "--noninteractive"])), 0, Qt.AlignmentFlag.AlignLeft)
        pl.addWidget(label("System (Debian-Pakete, Kernel, Treiber)", "h2"))
        pl.addWidget(label("Fragt nach deinem Passwort. Danach am besten neu starten.", "muted"))
        pl.addWidget(button("System aktualisieren", cb=lambda: self.jobs.add(
            "@system-update", "Aktualisiere System", ["pkexec", SYSTEM_UPDATE])), 0, Qt.AlignmentFlag.AlignLeft)
        p.body.addWidget(panel)

        proc = QProcess(p)

        def done(*_):
            if not alive(info):
                return
            rows = [r.split("\t") for r in bytes(proc.readAllStandardOutput()).decode(errors="replace").splitlines() if r.strip()]
            if rows:
                info.setText(f"{len(rows)} Update(s) verfügbar: " + ", ".join(r[1] if len(r) > 1 else r[0] for r in rows[:12]))
            else:
                info.setText("Alle Apps sind aktuell.")
        proc.finished.connect(done)
        proc.start("flatpak", ["remote-ls", "--updates", "--app", "--columns=application,name"])
        return p

    def page_games(self):
        self.installed = Flatpak.installed()
        p = Page()
        p.refresh_on_job = True
        p.body.addWidget(label(self.welt["nav"]["games"], "h1"))

        hero = QFrame()
        hero.setObjectName("hero")
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(24, 20, 24, 20)
        col = QVBoxLayout()
        t = label("Steam")
        t.setStyleSheet("font-size: 18pt; font-weight: 800;")
        col.addWidget(t)
        if steam_installed(self.installed):
            col.addWidget(label("Windows-Spiele laufen über Proton: in Steam unter Einstellungen → Kompatibilität aktivieren.", wrap=True))
            hl.addLayout(col, 1)
            hl.addWidget(button("Steam starten", "yellow", lambda: steam_open(self.installed)))
            hl.addWidget(button("Big Picture", cb=lambda: steam_open(self.installed, "-gamepadui")))
        else:
            col.addWidget(label("Steam ist noch nicht installiert. Kommt von Flathub, inklusive Proton.", wrap=True))
            hl.addLayout(col, 1)
            inst = button("Steam installieren", "yellow", lambda: self.install(
                {"app_id": STEAM_ID, "name": "Steam"}))
            inst.setEnabled(not self.jobs.busy(STEAM_ID))
            hl.addWidget(inst)
        p.body.addWidget(hero)

        p.body.addWidget(label("Deine Steam-Bibliothek", "h2"))
        games = steam_library()
        if games:
            flow = p.flow()
            for g in games:
                flow.addWidget(GameCard(self, g))
        else:
            p.body.addWidget(label("Noch keine installierten Steam-Spiele gefunden. Nach dem ersten Download erscheinen sie hier.", "muted", wrap=True))

        p.body.addWidget(label("Leistung", "h2"))
        p.body.addWidget(self.performance_panel())

        p.body.addWidget(label("Werkzeuge für Spieler", "h2"))
        tools = p.flow()
        for app_id in GAME_TOOLS:
            self.add_app_by_id(tools, app_id)

        self.fill_collection(p, "Spiele auf Flathub", f"{API}/collection/category/Game?page=1&per_page=24")
        return p

    def performance_panel(self):
        panel = QFrame()
        panel.setObjectName("panel")
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(18, 16, 18, 16)
        pl.setSpacing(10)

        gpu = run(["biblix-gpu", "--short"]).strip() or "Grafikkarte: unbekannt (biblix-gpu fehlt)"
        pl.addWidget(label(gpu, wrap=True))

        row = QHBoxLayout()
        row.addWidget(label("Energieprofil:"))
        combo = QComboBox()
        profiles = [("performance", "Leistung"), ("balanced", "Ausgewogen"), ("power-saver", "Sparen")]
        for key, text in profiles:
            combo.addItem(text, key)
        current = run(["powerprofilesctl", "get"]).strip()
        keys = [k for k, _ in profiles]
        if current in keys:
            combo.setCurrentIndex(keys.index(current))
        else:
            combo.setEnabled(False)
            combo.setToolTip("power-profiles-daemon läuft nicht")
        combo.currentIndexChanged.connect(lambda i: QProcess.startDetached("powerprofilesctl", ["set", combo.itemData(i)]))
        row.addWidget(combo)
        gm = run(["gamemoded", "-s"]).strip()
        row.addSpacing(20)
        row.addWidget(label("GameMode: " + ("aktiv" if "is active" in gm else "bereit" if gm else "nicht gefunden"), "muted"))
        row.addStretch(1)
        row.addWidget(button("GPU-Treiber prüfen", cb=lambda: QProcess.startDetached(
            "konsole", ["--hold", "-e", "biblix-gpu"])))
        pl.addLayout(row)

        pl.addWidget(label("Steam-Startoptionen (Rechtsklick aufs Spiel → Eigenschaften → Startoptionen):", wrap=True))
        for title, value in (("FPS-Anzeige + GameMode", LAUNCH_OPTIONS), ("HDR", LAUNCH_OPTIONS_HDR)):
            r = QHBoxLayout()
            name = label(title)
            name.setFixedWidth(190)
            r.addWidget(name)
            opts = QLineEdit(value)
            opts.setReadOnly(True)
            r.addWidget(opts, 1)
            r.addWidget(button("Kopieren", cb=lambda _=False, v=value: QGuiApplication.clipboard().setText(v)))
            pl.addLayout(r)
        pl.addWidget(label("HDR: zuerst in den Systemeinstellungen → Anzeige → HDR einschalten. "
                           "MangoHud-Overlay ein/aus: Shift rechts + F12.", "muted", wrap=True))
        return panel

    def show_detail(self, app):
        p = Page()
        head = QHBoxLayout()
        ic = QLabel()
        ic.setFixedSize(128, 128)
        ic.setPixmap(QIcon.fromTheme(app["app_id"], QIcon.fromTheme("application-x-executable")).pixmap(128, 128))
        self.net.pixmap(app.get("icon"), lambda pm: alive(ic) and ic.setPixmap(
            pm.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
        head.addWidget(ic)
        col = QVBoxLayout()
        col.addWidget(label(app["name"], "h1"))
        dev = label(app.get("developer") or app["app_id"], "muted")
        col.addWidget(dev)
        col.addWidget(label(app.get("summary", ""), wrap=True))
        btns = QHBoxLayout()
        main_btn = button("", "primary")
        rem_btn = button("Entfernen", "danger")
        btns.addWidget(main_btn)
        btns.addWidget(rem_btn)
        btns.addStretch(1)
        col.addLayout(btns)
        head.addLayout(col, 1)
        p.body.addLayout(head)

        def refresh():
            if not alive(main_btn):
                return
            state = self.state(app["app_id"])
            main_btn.setEnabled(state != "busy")
            main_btn.setText(self.knopf_text(state))
            rem_btn.setVisible(state == "installed")

        def act():
            if self.state(app["app_id"]) == "installed":
                Flatpak.launch(app["app_id"])
            else:
                self.install(app)
        main_btn.clicked.connect(act)
        rem_btn.clicked.connect(lambda: self.remove(app["app_id"], app["name"]))
        self.state_changed.connect(refresh)
        refresh()

        shot = QLabel()
        shot.setAlignment(Qt.AlignmentFlag.AlignLeft)
        p.body.addWidget(shot)
        desc = label("Lädt Beschreibung …", "muted", wrap=True)
        desc.setTextFormat(Qt.TextFormat.RichText)
        desc.setOpenExternalLinks(False)
        p.body.addWidget(desc)
        meta = label("", "muted", wrap=True)
        p.body.addWidget(meta)

        def done(data, err):
            if not alive(desc):
                return
            if err or not isinstance(data, dict):
                desc.setText("Details konnten nicht geladen werden.")
                return
            if data.get("developer_name"):
                dev.setText(data["developer_name"])
            if not app.get("icon") and data.get("icon"):
                self.net.pixmap(data["icon"], lambda pm: alive(ic) and ic.setPixmap(
                    pm.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
            desc.setText(data.get("description") or "")
            license_ = data.get("project_license") or "unbekannt"
            url = (data.get("urls") or {}).get("homepage") or ""
            meta.setText(f"Lizenz: {license_}   ·   App-ID: {app['app_id']}" + (f"   ·   {url}" if url else ""))
            for s in data.get("screenshots") or []:
                sizes = s.get("sizes") or []
                pick = next((z for z in sizes if str(z.get("width")) in ("752", "624")), sizes[0] if sizes else None)
                if pick:
                    self.net.pixmap(pick.get("src"), lambda pm: alive(shot) and shot.setPixmap(
                        pm.scaledToWidth(min(pm.width(), 752), Qt.TransformationMode.SmoothTransformation)))
                    break
        self.net.json(f"{API}/appstream/{quote(app['app_id'])}", done)
        self.set_page(p)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("S-Launcher")
    app.setDesktopFileName("de.biblix.SLauncher")
    start = "discover"
    if "--spiele" in sys.argv:
        start = "games"
    elif "--updates" in sys.argv:
        start = "updates"
    elif "--zubehoer" in sys.argv:
        start = "accessories"
    win = Main(start)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
