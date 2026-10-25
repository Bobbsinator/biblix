#!/usr/bin/env python3
"""Bibiplexx-Import: Filme und Serien von einer Platte oder aus einem Ordner in die Sammlung holen.

    bibiplexx --importieren [ORDNER]   Assistent oeffnen (ohne Ordner: Quelle waehlen)

Erkannt wird am Dateinamen wie in Bibiplexx selbst; mit TMDB-Schluessel kommen richtige Namen,
Jahr und Folgentitel dazu. Abgelegt wird wie gehabt:
    Serien/Name (Jahr)/Staffel 1/Name - S01E01 - Folgentitel.mkv
    Filme/Titel (Jahr)/Titel (Jahr).mkv
Es wird nur kopiert; die Originale bleiben, wo sie sind.
"""
import os
import re
import shutil
import string
import subprocess
import sys
import time
from pathlib import Path

from PyQt6.QtCore import QThread, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QIntValidator
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QHBoxLayout, QLineEdit, QMessageBox, QProgressBar,
    QScrollArea, QSizePolicy, QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
)

import bibiplexx as bp
from waechter import nutzer_basen, nutzer_orte

UNTERTITEL = {".srt", ".ass", ".ssa", ".vtt", ".sub", ".idx", ".sup"}
TEIL = ".bibiplexx-teil"
RESERVE = 2 * 1024 ** 3  # so viel bleibt auf der Platte immer frei

STIL = bp.STIL + f"""
QProgressBar {{ background: {bp.F['karte']}; border: 1px solid {bp.F['rand']}; border-radius: 9px; height: 18px; text-align: center; color: {bp.F['text']}; }}
QProgressBar::chunk {{ background: {bp.F['pink']}; border-radius: 8px; }}
QSpinBox {{ background: {bp.F['karte']}; border: 1px solid {bp.F['rand']}; border-radius: 9px; padding: 5px 8px; color: {bp.F['text']}; }}
QLabel#marke {{ color: #1a0010; background: {bp.F['pink']}; border-radius: 6px; padding: 2px 8px; font-weight: 800; font-size: 8.5pt; }}
QLabel#marke_film {{ color: #1b0d00; background: {bp.F['orange']}; border-radius: 6px; padding: 2px 8px; font-weight: 800; font-size: 8.5pt; }}
QLabel#warnung {{ color: {bp.F['orange']}; font-weight: 700; }}
QLabel#ziel {{ color: {bp.F['text']}; }}
QPushButton#quelle {{ text-align: left; padding: 14px 18px; font-size: 11.5pt; }}
"""


# ---------------------------------------------------------------- Namen

def schoen(t):
    """Kleingeschriebenes aus Dateinamen ("true detective") gross schreiben."""
    return string.capwords(t) if t and t == t.lower() else (t or "")


def norm(t):
    return re.sub(r"[^0-9a-zäöüß]+", "", (t or "").lower())


def sauber(t):
    """Fuer Datei- und Ordnernamen: nichts, was unter Linux oder Windows stoert."""
    t = (t or "").replace(":", " -")
    t = re.sub(r"[\\/]", "-", t)
    t = re.sub(r'[?*"<>|\x00-\x1f]', "", t)
    return re.sub(r"\s+", " ", t).strip(" .")


def groesse_text(b):
    if b >= 1024 ** 3:
        return f"{b / 1024 ** 3:.1f} GB".replace(".", ",")
    return f"{max(1, round(b / 1024 ** 2))} MB"


def ziel_wurzel():
    if os.environ.get("BIBIPLEXX_ZIEL"):  # zum Testen
        return Path(os.environ["BIBIPLEXX_ZIEL"])
    return bp.PLATTE_ORT if bp.PLATTE_ORT.is_dir() else Path.home() / "Videos"


# ---------------------------------------------------------------- Suchen

class Datei:
    def __init__(self, quelle, groesse, info):
        self.quelle, self.groesse = quelle, groesse
        self.staffel, self.folge = info.get("staffel", 1), info.get("folge", 1)
        self.titel = schoen(info.get("titel") or "")  # Folgentitel aus dem Dateinamen
        self.untertitel = []                           # [(pfad, endung wie ".de.srt")]
        self.an = True
        self.schon_da = False
        self.doppelt = False
        self.ziel = None

    def auftraege(self):
        yield self.quelle, self.ziel, self.groesse, True
        for pfad, endung in self.untertitel:
            try:
                g = pfad.stat().st_size
            except OSError:
                continue
            yield pfad, self.ziel.with_name(self.ziel.stem + endung), g, False


class Gruppe:
    """Eine Serie (alle Folgen) oder ein Film."""

    def __init__(self, art, name, jahr):
        self.art, self.name, self.jahr = art, name, jahr
        self.datei_name, self.datei_jahr = name, jahr  # wie im Dateinamen erkannt
        self.dateien = []
        self.kandidaten = []   # TMDB-Treffer: [{"id", "name", "jahr"}]
        self.wahl = -1         # Index in kandidaten, -1 = Name aus der Datei
        self.titel_von = {}    # TMDB-Id -> {(staffel, folge): Folgentitel}
        self.unklar = False

    def folgentitel(self):
        if 0 <= self.wahl < len(self.kandidaten):
            return self.titel_von.get(self.kandidaten[self.wahl]["id"], {})
        return {}

    def ziele(self, bib):
        """Zielpfad fuer jede Datei setzen und erkennen, was schon in Bibiplexx ist."""
        name = sauber(self.name) or "Unbekannt"
        jahr = f" ({self.jahr})" if self.jahr else ""
        if self.art == "serie":
            ordner = bib.serien_ordner.get(norm(self.name)) or sauber(self.name + jahr) or "Unbekannte Serie"
            tmdb = self.folgentitel()
            for d in self.dateien:
                t = tmdb.get((d.staffel, d.folge)) or d.titel
                stamm = f"{name} - S{d.staffel:02d}E{d.folge:02d}" + (f" - {sauber(t)}" if sauber(t) else "")
                d.ziel = bib.wurzel / "Serien" / ordner / f"Staffel {d.staffel}" / (stamm + d.quelle.suffix.lower())
                d.schon_da = (norm(self.name), d.staffel, d.folge) in bib.folgen or d.ziel.exists()
        else:
            ordner = sauber(self.name + jahr) or "Unbekannter Film"
            for i, d in enumerate(self.dateien, 1):
                stamm = ordner + (f" - Teil {i}" if len(self.dateien) > 1 else "")
                d.ziel = bib.wurzel / "Filme" / ordner / (stamm + d.quelle.suffix.lower())
                d.schon_da = d.ziel.exists() or (norm(self.name), self.jahr or "") in bib.filme \
                    or (len(self.dateien) == 1 and (norm(self.name), "") in bib.filme)


class Bibliothek:
    """Was schon in Bibiplexx ist, und wohin Neues kommt."""

    def __init__(self, einst):
        self.wurzel = ziel_wurzel()
        self.folgen, self.filme = set(), set()
        for e in bp.einlesen(einst["ordner"]):
            if e["art"] == "serie":
                self.folgen.add((norm(e["serie"]), e["staffel"], e["folge"]))
            else:
                self.filme.add((norm(e["titel"]), e.get("jahr") or ""))
        # Vorhandene Serienordner weiterbenutzen ("True Detective (2014)")
        self.serien_ordner = {}
        try:
            for o in (self.wurzel / "Serien").iterdir():
                if o.is_dir():
                    self.serien_ordner.setdefault(norm(bp.JAHR.sub(" ", o.name)), o.name)
        except OSError:
            pass


def durchsuchen(quelle, melden=None, frist=None, abbruch=None):
    """Alle Videos unter quelle als Gruppen (Serien zuerst, dann Filme, Unklares am Ende)."""
    quelle = Path(quelle)
    videos, subs = [], {}
    start = time.time()
    for d, unter, namen in os.walk(quelle):
        unter[:] = sorted(u for u in unter if not u.startswith(".") and u.lower() not in bp.UEBERSPRINGEN)
        for n in sorted(namen):
            if n.startswith(".") or n.endswith(TEIL):
                continue
            p = Path(d) / n
            endung = p.suffix.lower()
            if endung in UNTERTITEL:
                subs.setdefault(p.parent, []).append(p)
                continue
            if endung not in bp.ENDUNGEN:
                continue
            try:
                groesse = p.stat().st_size
            except OSError:
                continue
            if "sample" in n.lower() and groesse < 300_000_000:
                continue
            videos.append((p, groesse))
            if melden and len(videos) % 5 == 0:
                melden(len(videos))
        if (frist and time.time() - start > frist) or (abbruch and abbruch()):
            break
    pro_ordner = {}
    for p, _ in videos:
        pro_ordner[p.parent] = pro_ordner.get(p.parent, 0) + 1

    serien, filme = {}, {}
    for p, groesse in videos:
        info = bp.verstehen(p)
        if info["art"] == "film" and p.parent != quelle:
            # "Die Simpsons/Staffel 3/03x05 Homer.mkv": Serienname steht nur im Ordner
            o = p.parent.parent if bp.STAFFEL_ORDNER.match(p.parent.name) else p.parent
            mit_ordner = bp.verstehen(Path(f"{o.name} - {p.name}"))
            if mit_ordner["art"] == "serie":
                info = mit_ordner
        if info["art"] == "film" and not info.get("jahr") and p.parent != quelle:
            # "Inception (2010)/inception-1080p.mkv": Titel und Jahr kommen aus dem Ordner
            o = bp.verstehen(Path(p.parent.name + ".mkv"))
            if o["art"] == "film" and o.get("jahr"):
                info = o
        dt = Datei(p, groesse, info)
        # Untertitel daneben ("Name.de.srt") oder im Ordner Subs/
        for s in subs.get(p.parent, []):
            if s.name.startswith(p.stem + "."):
                dt.untertitel.append((s, s.name[len(p.stem):].lower()))
        sub_ordner = subs.get(p.parent / "Subs", []) if pro_ordner[p.parent] == 1 else []
        for s in sub_ordner + subs.get(p.parent / "Subs" / p.stem, []):
            dt.untertitel.append((s, "." + sauber(s.stem).replace(" ", "_") + s.suffix.lower()))
        if info["art"] == "serie":
            name = schoen(info["serie"])
            g = serien.setdefault(norm(name), Gruppe("serie", name, None))
        else:
            name, jahr = schoen(info["titel"]), info.get("jahr")
            g = filme.setdefault((norm(name), jahr), Gruppe("film", name, jahr))
            g.unklar = not jahr
        g.dateien.append(dt)
    for g in serien.values():
        g.dateien.sort(key=lambda d: (d.staffel, d.folge, str(d.quelle)))
    return (sorted(serien.values(), key=lambda g: g.name.lower())
            + sorted(filme.values(), key=lambda g: (g.unklar, g.name.lower())))


def neue_zaehlen(ort, frist=None):
    """Fuer den Waechter: (neue Folgen, neue Filme) auf einer Platte."""
    bib = Bibliothek(bp.einstellungen())
    folgen = filme = 0
    for g in durchsuchen(ort, frist=frist):
        g.ziele(bib)
        neu = sum(1 for d in g.dateien if not d.schon_da)
        if g.art == "serie":
            folgen += neu
        elif neu:
            filme += 1
    return folgen, filme


# ---------------------------------------------------------------- TMDB

def tmdb_sprache(einst):
    return "de-DE" if einst.get("sprache") == "deutsch" else "en-US"


def tmdb_kandidaten(schluessel, g, sprache):
    art = "tv" if g.art == "serie" else "movie"
    params = {"query": g.datei_name, "language": sprache, "include_adult": "false"}
    if g.datei_jahr and art == "movie":
        params["year"] = g.datei_jahr
    treffer = bp.tmdb_anfrage(schluessel, f"/search/{art}", params).get("results") or []
    if not treffer and "year" in params:
        params.pop("year")
        treffer = bp.tmdb_anfrage(schluessel, f"/search/{art}", params).get("results") or []
    liste = []
    for t in treffer[:6]:
        datum = t.get("first_air_date") or t.get("release_date") or ""
        liste.append({"id": t["id"], "name": t.get("name") or t.get("title") or g.datei_name, "jahr": datum[:4] or None})
    return liste


def tmdb_folgentitel(schluessel, tv_id, staffeln, sprache):
    titel = {}
    for s in sorted(staffeln):
        try:
            d = bp.tmdb_anfrage(schluessel, f"/tv/{tv_id}/season/{s}", {"language": sprache})
        except bp.TmdbFehler as f:
            if str(f) == "schluessel":
                raise
            continue
        for ep in d.get("episodes") or []:
            n = (ep.get("name") or "").strip()
            if n and not re.fullmatch(r"(Episode|Folge|Episodio|Épisode) \d+", n):
                titel[(s, ep.get("episode_number"))] = n
    return titel


def tmdb_waehlen(schluessel, g, index, sprache):
    """Kandidat uebernehmen (bei Serien die Folgentitel dazu holen)."""
    g.wahl = index
    if index < 0:
        g.name, g.jahr = g.datei_name, g.datei_jahr
        return
    k = g.kandidaten[index]
    g.name, g.jahr = k["name"], k["jahr"]
    if g.art == "film":
        g.unklar = False
    elif k["id"] not in g.titel_von:
        g.titel_von[k["id"]] = tmdb_folgentitel(schluessel, k["id"], {d.staffel for d in g.dateien}, sprache)


# ---------------------------------------------------------------- Kopieren und Platte

class Abbruch(Exception):
    pass


class Sucher(QThread):
    stand = pyqtSignal(str)
    fertig = pyqtSignal(object)

    def __init__(self, quelle, einst):
        super().__init__()
        self.quelle, self.einst = quelle, einst
        self.abbrechen = False

    def run(self):
        self.stand.emit("Suche Filme und Serien …")
        gruppen = durchsuchen(self.quelle, lambda n: self.stand.emit(f"{n} Videos gefunden …"),
                              abbruch=lambda: self.abbrechen)
        if self.abbrechen:
            return
        self.stand.emit("Vergleiche mit deiner Sammlung …")
        bib = Bibliothek(self.einst)
        hinweis = ""
        schluessel = (self.einst.get("tmdb_schluessel") or "").strip()
        if schluessel and gruppen:
            sprache = tmdb_sprache(self.einst)
            for i, g in enumerate(gruppen, 1):
                if self.abbrechen:
                    return
                self.stand.emit(f"Frage TMDB nach Namen und Folgentiteln … ({i} von {len(gruppen)})")
                try:
                    g.kandidaten = tmdb_kandidaten(schluessel, g, sprache)
                    if g.kandidaten:
                        tmdb_waehlen(schluessel, g, 0, sprache)
                except bp.TmdbFehler as f:
                    if str(f) == "schluessel":
                        hinweis = "TMDB lehnt den Schlüssel ab. Namen kommen nur aus den Dateinamen."
                        break
                    hinweis = "TMDB war nicht erreichbar. Namen kommen nur aus den Dateinamen."
                    break
        elif gruppen:
            hinweis = "Tipp: Mit einem TMDB-Schlüssel (Bibiplexx → Einstellungen) gibt es richtige Namen und Folgentitel."
        for g in gruppen:
            g.ziele(bib)
            for d in g.dateien:
                d.an = not d.schon_da
        self.fertig.emit((gruppen, bib, hinweis))


class Arbeit(QThread):
    """Kleine Aufgabe im Hintergrund (z. B. Folgentitel fuer einen anderen TMDB-Treffer)."""
    fertig = pyqtSignal(object)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        try:
            self.fertig.emit(self.fn())
        except Exception as f:  # noqa: BLE001 - Fehler gehen als Ergebnis zurueck
            self.fertig.emit(f)


class Kopierer(QThread):
    stand = pyqtSignal(object, object, str)   # erledigt, gesamt (Bytes, grosse Zahlen), Dateiname
    fertig = pyqtSignal(int, list, bool)      # kopierte Videos, Fehler, abgebrochen

    def __init__(self, auftraege):
        super().__init__()
        self.auftraege = auftraege
        self.abbrechen = False

    def run(self):
        gesamt = sum(a[2] for a in self.auftraege)
        erledigt, videos, fehler, zuletzt = 0, 0, [], 0.0
        for quelle, ziel, groesse, ist_video in self.auftraege:
            if self.abbrechen:
                break
            if ziel.exists():
                erledigt += groesse
                continue
            teil = ziel.with_name(ziel.name + TEIL)
            self.stand.emit(erledigt, gesamt, ziel.name)
            try:
                ziel.parent.mkdir(parents=True, exist_ok=True)
                with open(quelle, "rb") as a, open(teil, "wb") as b:
                    while True:
                        if self.abbrechen:
                            raise Abbruch
                        stueck = a.read(8 << 20)
                        if not stueck:
                            break
                        b.write(stueck)
                        erledigt += len(stueck)
                        if time.monotonic() - zuletzt > 0.25:
                            zuletzt = time.monotonic()
                            self.stand.emit(erledigt, gesamt, ziel.name)
                    b.flush()
                    os.fsync(b.fileno())
                os.replace(teil, ziel)  # erst jetzt sieht Bibiplexx die Datei
                videos += 1 if ist_video else 0
            except Abbruch:
                teil.unlink(missing_ok=True)
                break
            except OSError as f:
                teil.unlink(missing_ok=True)
                fehler.append(f"{quelle.name}: {f.strerror or f}")
        self.stand.emit(erledigt, gesamt, "")
        self.fertig.emit(videos, fehler, self.abbrechen)


def run(argv, timeout=60):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except (OSError, subprocess.SubprocessError) as f:
        return 1, "", str(f)


def platte_von(ort):
    """(Geraet, Einhaengepunkt), wenn ort auf einer Wechselplatte des Nutzers liegt."""
    _, geraet, _ = run(["findmnt", "-n", "-o", "SOURCE", "--target", str(ort)])
    _, punkt, _ = run(["findmnt", "-n", "-o", "TARGET", "--target", str(ort)])
    if geraet.startswith("/dev/") and (punkt + "/").startswith(nutzer_basen()):
        return geraet, punkt
    return None


def auswerfen(geraet):
    code, _, fehler = run(["udisksctl", "unmount", "-b", geraet])
    if code != 0:
        return False, fehler or "Aushängen hat nicht geklappt."
    _, platte, _ = run(["lsblk", "-n", "-p", "-o", "PKNAME", geraet])
    if platte:
        run(["udisksctl", "power-off", "-b", platte.splitlines()[0]])
    return True, ""


# ---------------------------------------------------------------- Oberflaeche

class GruppenZeile(QFrame):
    """Eine Serie oder ein Film in der Vorschau: Name, Jahr, TMDB-Treffer, Dateien alt → neu."""
    geaendert = pyqtSignal()

    def __init__(self, fenster, g):
        super().__init__()
        self.fenster, self.g = fenster, g
        self.setObjectName("zeile")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.arbeit = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        kopf = QHBoxLayout()
        kopf.setSpacing(10)
        self.haken = QCheckBox()
        self.haken.setToolTip("Alles hiervon importieren")
        self.haken.clicked.connect(self._alle)
        kopf.addWidget(self.haken)
        self.marke = bp.label("")
        kopf.addWidget(self.marke)
        self.name = QLineEdit(g.name)
        self.name.setPlaceholderText("Name")
        self.name.editingFinished.connect(self._name_neu)
        kopf.addWidget(self.name, 1)
        self.jahr = QLineEdit(g.jahr or "")
        self.jahr.setPlaceholderText("Jahr")
        self.jahr.setValidator(QIntValidator(1880, 2100, self))
        self.jahr.setFixedWidth(80)
        self.jahr.editingFinished.connect(self._name_neu)
        kopf.addWidget(self.jahr)
        self.tmdb = QComboBox()
        self.tmdb.setFixedWidth(280)
        self.tmdb.setToolTip("Meintest du …? (Treffer von TMDB)")
        if g.kandidaten:
            for k in g.kandidaten:
                self.tmdb.addItem(f"{k['name']}" + (f" ({k['jahr']})" if k["jahr"] else ""))
            self.tmdb.addItem(f"Name aus der Datei: {g.datei_name}")
            self.tmdb.setCurrentIndex(g.wahl if g.wahl >= 0 else len(g.kandidaten))
            self.tmdb.activated.connect(self._tmdb_neu)
            kopf.addWidget(self.tmdb)
        self.details = bp.knopf("Details ▾", cb=self._umklappen)
        kopf.addWidget(self.details)
        lay.addLayout(kopf)

        # Unklar erkannte Einzeldatei: Film oder doch eine Folge?
        self.art_zeile = None
        if g.art == "film" and len(g.dateien) == 1 and g.unklar:
            self.art_zeile = QHBoxLayout()
            self.hinweis = bp.label("Nicht sicher erkannt. Bitte kurz prüfen:", "warnung")
            self.art_zeile.addWidget(self.hinweis)
            self.art = QComboBox()
            self.art.addItems(["Ist ein Film", "Ist eine Serienfolge"])
            self.art.currentIndexChanged.connect(self._art_neu)
            self.art_zeile.addWidget(self.art)
            self.staffel_lb = bp.label("Staffel")
            self.staffel = QSpinBox()
            self.staffel.setRange(0, 99)
            self.staffel.setValue(1)
            self.folge_lb = bp.label("Folge")
            self.folge = QSpinBox()
            self.folge.setRange(0, 999)
            self.folge.setValue(1)
            for w in (self.staffel_lb, self.staffel, self.folge_lb, self.folge):
                self.art_zeile.addWidget(w)
                w.hide()
            self.staffel.valueChanged.connect(self._art_neu)
            self.folge.valueChanged.connect(self._art_neu)
            self.art_zeile.addStretch(1)
            lay.addLayout(self.art_zeile)

        self.info = bp.label("", "leise")
        lay.addWidget(self.info)
        self.koerper = QWidget()
        kl = QVBoxLayout(self.koerper)
        kl.setContentsMargins(30, 0, 0, 0)
        kl.setSpacing(6)
        self.reihen = []
        for d in g.dateien:
            z = QHBoxLayout()
            z.setSpacing(10)
            c = QCheckBox()
            c.setChecked(d.an)
            c.toggled.connect(lambda an, d=d: self._datei(d, an))
            z.addWidget(c, 0, Qt.AlignmentFlag.AlignTop)
            col = QVBoxLayout()
            col.setSpacing(1)
            alt = bp.label(str(d.quelle.relative_to(fenster.quelle)) if d.quelle.is_relative_to(fenster.quelle) else d.quelle.name,
                           "leise", wrap=True)
            alt.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            neu = bp.label("", "ziel", wrap=True)
            neu.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            col.addWidget(alt)
            col.addWidget(neu)
            z.addLayout(col, 1)
            status = bp.label("", "warnung")
            z.addWidget(status, 0, Qt.AlignmentFlag.AlignTop)
            kl.addLayout(z)
            self.reihen.append((d, c, neu, status))
        lay.addWidget(self.koerper)
        self.koerper.setVisible(len(g.dateien) <= 12)
        self.aktualisieren()

    def _umklappen(self):
        self.koerper.setHidden(not self.koerper.isHidden())
        self.aktualisieren()

    def _alle(self, an):
        for d, c, _, _ in self.reihen:
            c.setChecked(an)

    def _datei(self, d, an):
        d.an = an
        self.aktualisieren(ziele=False)

    def _name_neu(self):
        self.g.name = self.name.text().strip() or self.g.datei_name
        self.g.jahr = self.jahr.text().strip() or None
        self.aktualisieren()

    def _art_neu(self):
        serie = self.art.currentIndex() == 1
        for w in (self.staffel_lb, self.staffel, self.folge_lb, self.folge):
            w.setVisible(serie)
        self.g.art = "serie" if serie else "film"
        d = self.g.dateien[0]
        if serie:
            d.staffel, d.folge = self.staffel.value(), self.folge.value()
        self.aktualisieren()

    def _tmdb_neu(self, i):
        g = self.g
        index = i if i < len(g.kandidaten) else -1
        schluessel = (self.fenster.einst.get("tmdb_schluessel") or "").strip()
        sprache = tmdb_sprache(self.fenster.einst)
        self.tmdb.setEnabled(False)
        self.arbeit = Arbeit(lambda: tmdb_waehlen(schluessel, g, index, sprache))
        self.arbeit.fertig.connect(self._tmdb_fertig)
        self.arbeit.start()

    def _tmdb_fertig(self, _ergebnis):
        self.tmdb.setEnabled(True)
        self.name.setText(self.g.name)
        self.jahr.setText(self.g.jahr or "")
        self.aktualisieren()

    def aktualisieren(self, ziele=True):
        g = self.g
        if ziele:
            g.ziele(self.fenster.bib)
        self.fenster.doppelte_pruefen()
        serie = g.art == "serie"
        self.marke.setText("SERIE" if serie else "FILM")
        self.marke.setObjectName("marke" if serie else "marke_film")
        self.marke.setStyleSheet("")  # Objektname neu anwenden
        wurzel = self.fenster.bib.wurzel
        for d, c, neu, status in self.reihen:
            neu.setText("→ " + str(d.ziel.relative_to(wurzel)))
            extra = []
            if d.untertitel:
                extra.append(f"+{len(d.untertitel)} Untertitel")
            if d.schon_da:
                extra.append("schon da")
            elif d.doppelt:
                extra.append("doppelt")
            status.setText(" · ".join(extra))
            if c.isChecked() != d.an:
                c.blockSignals(True)
                c.setChecked(d.an)
                c.blockSignals(False)
        an = [d for d in g.dateien if d.an]
        self.haken.setChecked(bool(an))
        n, da = len(g.dateien), sum(1 for d in g.dateien if d.schon_da)
        if serie:
            staffeln = sorted({d.staffel for d in g.dateien})
            st = f"Staffel {staffeln[0]}" if len(staffeln) == 1 else f"Staffel {staffeln[0]}–{staffeln[-1]}"
            text = f"{n} Folge{'n' if n != 1 else ''} · {st}"
        else:
            text = "1 Datei" if n == 1 else f"{n} Teile"
        text += " · " + groesse_text(sum(d.groesse for d in g.dateien))
        if da:
            text += f" · {da} schon in Bibiplexx" if serie else " · schon in Bibiplexx"
        if self.koerper.isHidden():
            text += f" · Ziel: {g.dateien[0].ziel.parent.relative_to(wurzel)}"
        self.info.setText(text)
        self.details.setText("Details ▾" if self.koerper.isHidden() else "Details ▴")
        self.geaendert.emit()


class ImportFenster(QDialog):
    importiert = pyqtSignal()

    def __init__(self, quelle=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bibiplexx – Importieren")
        icon = QIcon.fromTheme("de.biblix.Bibiplexx")
        if icon.isNull() and bp.SYMBOL.is_file():
            icon = QIcon(str(bp.SYMBOL))
        self.setWindowIcon(icon)
        self.setStyleSheet(STIL)
        self.resize(1080, 780)
        self.einst = bp.einstellungen()
        self.quelle = None
        self.bib = None
        self.gruppen, self.zeilen = [], []
        self.sucher = self.kopierer = None
        self.start_zeit = 0.0

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        kopf = QWidget()
        kopf.setObjectName("kopf")
        kl = QHBoxLayout(kopf)
        kl.setContentsMargins(22, 12, 22, 12)
        name = bp.label("BIBIPLEXX · IMPORTIEREN")
        name.setStyleSheet(f"color: {bp.F['pink']}; font-size: 14pt; font-weight: 900; letter-spacing: 3px;")
        kl.addWidget(name)
        kl.addStretch(1)
        lay.addWidget(kopf)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)

        self.s_quelle = self._seite_quelle()
        self.s_suche = self._seite_suche()
        self.s_vorschau = self._seite_vorschau()
        self.s_kopie = self._seite_kopie()
        self.s_fertig = self._seite_fertig()
        for s in (self.s_quelle, self.s_suche, self.s_vorschau, self.s_kopie, self.s_fertig):
            self.stack.addWidget(s)

        self.orte_takt = QTimer(self)
        self.orte_takt.timeout.connect(self._orte_zeigen)
        if quelle:
            self.suchen(quelle)
        else:
            self._orte_zeigen()
            self.orte_takt.start(2000)

    # ---- Seite 1: Quelle

    def _seite_quelle(self):
        w = QWidget()
        w.setObjectName("seite")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(40, 30, 40, 30)
        lay.setSpacing(12)
        lay.addWidget(bp.label("Woher kommen die Filme?", "h1"))
        lay.addWidget(bp.label("Wähle eine angesteckte Platte oder einen Ordner. Bibiplexx sucht darin Filme und Serien, "
                               "zeigt dir vorher alles und kopiert erst nach deinem OK. Die Originale bleiben, wo sie sind.",
                               "leise", wrap=True))
        self.orte_box = QVBoxLayout()
        self.orte_box.setSpacing(10)
        lay.addLayout(self.orte_box)
        self._orte_stand = None
        reihe = QHBoxLayout()
        reihe.addWidget(bp.knopf("Ordner wählen …", cb=self._ordner_waehlen))
        reihe.addStretch(1)
        reihe.addWidget(bp.knopf("Schließen", cb=self.reject))
        lay.addStretch(1)
        lay.addLayout(reihe)
        return w

    def _orte_zeigen(self):
        orte = nutzer_orte()
        if orte == self._orte_stand:
            return
        self._orte_stand = orte
        while self.orte_box.count():
            it = self.orte_box.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        if not orte:
            self.orte_box.addWidget(bp.label("Gerade ist keine externe Platte angesteckt. Steck eine an – sie erscheint "
                                             "hier von selbst – oder wähl einen Ordner.", wrap=True))
        for ort in orte:
            try:
                du = shutil.disk_usage(ort)
                groesse = f"  ·  {groesse_text(du.total)}, {groesse_text(du.used)} belegt"
            except OSError:
                groesse = ""
            self.orte_box.addWidget(bp.knopf(f"💽  {Path(ort).name}{groesse}", "quelle", cb=lambda _=False, o=ort: self.suchen(o)))

    def _ordner_waehlen(self):
        d = QFileDialog.getExistingDirectory(self, "Ordner mit Filmen oder Serien", str(Path.home()))
        if d:
            self.suchen(d)

    # ---- Seite 2: Suchen

    def _seite_suche(self):
        w = QWidget()
        w.setObjectName("seite")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(40, 30, 40, 30)
        lay.addStretch(1)
        self.suche_titel = bp.label("", "h1")
        self.suche_titel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.suche_titel)
        self.suche_text = bp.label("", "leise")
        self.suche_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.suche_text)
        balken = QProgressBar()
        balken.setRange(0, 0)
        balken.setTextVisible(False)
        balken.setFixedWidth(420)
        lay.addWidget(balken, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addStretch(1)
        return w

    def suchen(self, quelle):
        self.orte_takt.stop()
        self.quelle = Path(quelle)
        self.suche_titel.setText(f"Schaue auf „{self.quelle.name or quelle}“ nach …")
        self.suche_text.setText("")
        self.stack.setCurrentWidget(self.s_suche)
        self.sucher = Sucher(self.quelle, self.einst)
        self.sucher.stand.connect(self.suche_text.setText)
        self.sucher.fertig.connect(self._gefunden)
        self.sucher.start()

    # ---- Seite 3: Vorschau

    def _seite_vorschau(self):
        w = QWidget()
        w.setObjectName("seite")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(30, 20, 30, 16)
        lay.setSpacing(10)
        self.v_titel = bp.label("", "h1")
        lay.addWidget(self.v_titel)
        self.v_hinweis = bp.label("", "leise", wrap=True)
        lay.addWidget(self.v_hinweis)
        self.v_scroll = QScrollArea()
        self.v_scroll.setWidgetResizable(True)
        self.v_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        lay.addWidget(self.v_scroll, 1)
        unten = QHBoxLayout()
        self.v_summe = bp.label("", wrap=True)
        unten.addWidget(self.v_summe, 1)
        unten.addWidget(bp.knopf("Andere Quelle", cb=self._zurueck))
        self.v_los = bp.knopf("Importieren", "orange", self.kopieren)
        unten.addWidget(self.v_los)
        lay.addLayout(unten)
        return w

    def _zurueck(self):
        self.stack.setCurrentWidget(self.s_quelle)
        self._orte_stand = None
        self._orte_zeigen()
        self.orte_takt.start(2000)

    def _gefunden(self, ergebnis):
        self.gruppen, self.bib, hinweis = ergebnis
        innen = QWidget()
        innen.setObjectName("seite")
        il = QVBoxLayout(innen)
        il.setContentsMargins(0, 0, 8, 0)
        il.setSpacing(10)
        il.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.zeilen = []
        unklar_titel = False
        for g in self.gruppen:
            if g.art == "film" and g.unklar and not unklar_titel:
                il.addWidget(bp.label("Unklar – bitte kurz prüfen", "h2"))
                unklar_titel = True
            z = GruppenZeile(self, g)
            z.geaendert.connect(self._summe)
            il.addWidget(z)
            self.zeilen.append(z)
        self.v_scroll.setWidget(innen)
        serien = [g for g in self.gruppen if g.art == "serie"]
        folgen = sum(len(g.dateien) for g in serien)
        filme = len(self.gruppen) - len(serien)
        name = self.quelle.name or str(self.quelle)
        if not self.gruppen:
            self.v_titel.setText(f"Auf „{name}“ sind keine Videos.")
        else:
            teile = []
            if folgen:
                teile.append(f"{folgen} Folge{'n' if folgen != 1 else ''} ({len(serien)} Serie{'n' if len(serien) != 1 else ''})")
            if filme:
                teile.append(f"{filme} Film{'e' if filme != 1 else ''}")
            self.v_titel.setText(f"Gefunden auf „{name}“: " + " und ".join(teile))
        self.v_hinweis.setText(("Prüf die neuen Namen. Name und Jahr kannst du direkt ändern; was schon in Bibiplexx ist, "
                                "ist abgehakt. " + hinweis).strip())
        self.doppelte_pruefen()
        self._summe()
        self.stack.setCurrentWidget(self.s_vorschau)

    def doppelte_pruefen(self):
        """Zwei Dateien mit demselben Ziel (z. B. 720p und 1080p derselben Folge): nur die erste."""
        gesehen = set()
        for g in self.gruppen:
            for d in g.dateien:
                d.doppelt = d.ziel in gesehen
                if d.an and not d.schon_da:
                    gesehen.add(d.ziel)

    def auftraege(self):
        liste = []
        for g in self.gruppen:
            for d in g.dateien:
                if d.an and not d.doppelt:
                    liste.extend(d.auftraege())
        return liste

    def _summe(self):
        if not self.bib:
            return
        auftr = self.auftraege()
        videos = sum(1 for a in auftr if a[3])
        bytes_ = sum(a[2] for a in auftr if not a[1].exists())
        try:
            frei = shutil.disk_usage(self.bib.wurzel if self.bib.wurzel.exists() else Path.home()).free
        except OSError:
            frei = 0
        ziel = "Bibiplexx-Platte" if self.bib.wurzel == bp.PLATTE_ORT else str(self.bib.wurzel)
        text = f"Ausgewählt: {videos} Video{'s' if videos != 1 else ''}, {groesse_text(bytes_)}  ·  Ziel: {ziel}, {groesse_text(frei)} frei"
        passt = bytes_ + RESERVE <= frei
        if not passt:
            text += f"\nZu wenig Platz: es fehlen {groesse_text(bytes_ + RESERVE - frei)}. Nimm ein paar Haken weg."
            self.v_summe.setObjectName("warnung")
        else:
            self.v_summe.setObjectName("")
        self.v_summe.setStyleSheet("")
        self.v_summe.setText(text)
        self.v_los.setEnabled(videos > 0 and passt)
        self.v_los.setText(f"{videos} importieren" if videos else "Importieren")

    # ---- Seite 4: Kopieren

    def _seite_kopie(self):
        w = QWidget()
        w.setObjectName("seite")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(60, 30, 60, 30)
        lay.setSpacing(12)
        lay.addStretch(1)
        self.k_titel = bp.label("Kopiere in deine Sammlung …", "h1")
        lay.addWidget(self.k_titel)
        self.k_balken = QProgressBar()
        self.k_balken.setRange(0, 1000)
        self.k_balken.setTextVisible(False)
        lay.addWidget(self.k_balken)
        self.k_datei = bp.label("", wrap=True)
        lay.addWidget(self.k_datei)
        self.k_rest = bp.label("", "leise")
        lay.addWidget(self.k_rest)
        reihe = QHBoxLayout()
        reihe.addStretch(1)
        self.k_stop = bp.knopf("Abbrechen", cb=self._abbrechen)
        reihe.addWidget(self.k_stop)
        lay.addLayout(reihe)
        lay.addStretch(1)
        return w

    def kopieren(self):
        auftr = self.auftraege()
        if not auftr:
            return
        self.stack.setCurrentWidget(self.s_kopie)
        self.start_zeit = time.monotonic()
        self.k_stop.setEnabled(True)
        self.kopierer = Kopierer(auftr)
        self.kopierer.stand.connect(self._kopie_stand)
        self.kopierer.fertig.connect(self._kopie_fertig)
        self.kopierer.start()

    def _kopie_stand(self, erledigt, gesamt, name):
        self.k_balken.setValue(int(1000 * erledigt / gesamt) if gesamt else 1000)
        if name:
            self.k_datei.setText(name)
        dauer = time.monotonic() - self.start_zeit
        if dauer > 3 and erledigt > 0:
            tempo = erledigt / dauer
            rest = (gesamt - erledigt) / tempo
            minuten = round(rest / 60)
            zeit = "noch weniger als eine Minute" if minuten < 1 else f"noch etwa {minuten} Min."
            self.k_rest.setText(f"{groesse_text(erledigt)} von {groesse_text(gesamt)} · {groesse_text(tempo)}/s · {zeit}")
        else:
            self.k_rest.setText(f"{groesse_text(erledigt)} von {groesse_text(gesamt)}")

    def _abbrechen(self):
        if self.kopierer:
            self.kopierer.abbrechen = True
            self.k_stop.setEnabled(False)
            self.k_rest.setText("Breche ab … (die halbe Datei wird wieder gelöscht)")

    # ---- Seite 5: Fertig

    def _seite_fertig(self):
        w = QWidget()
        w.setObjectName("seite")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(60, 30, 60, 30)
        lay.setSpacing(12)
        lay.addStretch(1)
        self.f_titel = bp.label("", "h1")
        self.f_titel.setWordWrap(True)
        lay.addWidget(self.f_titel)
        self.f_text = bp.label("", "leise", wrap=True)
        lay.addWidget(self.f_text)
        reihe = QHBoxLayout()
        self.f_auswerfen = bp.knopf("Platte sicher entfernen", cb=self._auswerfen)
        reihe.addWidget(self.f_auswerfen)
        reihe.addStretch(1)
        self.f_mehr = bp.knopf("Noch mehr importieren", cb=self._zurueck)
        reihe.addWidget(self.f_mehr)
        reihe.addWidget(bp.knopf("Fertig", "orange", self.accept))
        lay.addLayout(reihe)
        lay.addStretch(1)
        return w

    def _kopie_fertig(self, videos, fehler, abgebrochen):
        if videos:
            self.importiert.emit()
        serien = {g.name for g in self.gruppen if g.art == "serie" and any(d.an and not d.doppelt for d in g.dateien)}
        if abgebrochen:
            self.f_titel.setText(f"Abgebrochen. {videos} Video{'s' if videos != 1 else ''} sind schon drin.")
        elif fehler:
            self.f_titel.setText(f"Fast fertig: {videos} Video{'s' if videos != 1 else ''} kopiert, {len(fehler)} nicht.")
        else:
            self.f_titel.setText(f"Fertig! {videos} Video{'s' if videos != 1 else ''} sind jetzt in Bibiplexx. 🎬")
        text = ""
        if serien and not abgebrochen:
            text = "Neu oder ergänzt: " + ", ".join(sorted(serien)) + ". "
        if fehler:
            text += "\n\nNicht geklappt:\n" + "\n".join(fehler[:8]) + ("\n…" if len(fehler) > 8 else "")
        self.f_text.setText(text.strip() or "Die Originale sind unverändert geblieben.")
        self.platte = platte_von(self.quelle) if self.quelle else None
        self.f_auswerfen.setVisible(self.platte is not None)
        self.f_auswerfen.setEnabled(True)
        self.f_auswerfen.setText(f"„{Path(self.platte[1]).name}“ sicher entfernen" if self.platte else "")
        self.stack.setCurrentWidget(self.s_fertig)

    def _auswerfen(self):
        self.f_auswerfen.setEnabled(False)
        self.f_auswerfen.setText("Hänge aus …")
        QApplication.processEvents()
        ok, fehler = auswerfen(self.platte[0])
        if ok:
            self.f_auswerfen.setText("Platte kann jetzt abgezogen werden ✔")
            self.f_mehr.setEnabled(False)
        else:
            self.f_auswerfen.setEnabled(True)
            self.f_auswerfen.setText("Nochmal versuchen")
            self.f_text.setText("Die Platte ist noch in Benutzung (z. B. im Dateimanager geöffnet). "
                                "Fenster schließen und nochmal versuchen.\n\n" + fehler)

    def _darf_zu(self):
        if self.kopierer and self.kopierer.isRunning():
            frage = QMessageBox.question(self, "Bibiplexx", "Gerade wird kopiert. Abbrechen und schließen?\n\n"
                                         "Was schon fertig ist, bleibt in Bibiplexx.")
            return frage == QMessageBox.StandardButton.Yes
        return True

    def closeEvent(self, ev):
        if not self._darf_zu():
            ev.ignore()
            return
        self.aufraeumen()
        super().closeEvent(ev)

    def reject(self):
        if not self._darf_zu():
            return
        self.aufraeumen()
        super().reject()

    def aufraeumen(self):
        """Laufende Arbeit sauber beenden (auch wenn Bibiplexx selbst geschlossen wird)."""
        self.orte_takt.stop()
        if self.kopierer and self.kopierer.isRunning():
            self.kopierer.abbrechen = True
            self.kopierer.wait()
        if self.sucher and self.sucher.isRunning():
            self.sucher.abbrechen = True
            self.sucher.wait()
        for z in self.zeilen:
            if z.arbeit and z.arbeit.isRunning():
                z.arbeit.wait()


def main(argv):
    app = QApplication.instance() or QApplication(argv)
    app.setApplicationName("Bibiplexx")
    app.setDesktopFileName("de.biblix.Bibiplexx")
    quelle = next((a for a in argv[1:] if not a.startswith("-")), None)
    w = ImportFenster(quelle)
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
