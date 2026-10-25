"""Steam-Spiele lesen (ohne Anmeldung, nur die Dateien von Steam) und die Linux-Ampel bestimmen.

Gelesen wird nur, was Steam ohnehin auf der Platte hat:
  steamapps/libraryfolders.vdf   Bibliotheksordner
  steamapps/appmanifest_*.acf    installierte Spiele (Name, Groesse, zuletzt gespielt)
  userdata/<id>/config/localconfig.vdf   Spielzeit (Minuten) und "letzte 2 Wochen"
  appcache/librarycache/<appid>/ Cover, Banner und Logo
Aus localconfig.vdf wird nur der Abschnitt "apps" ausgewertet; alles andere bleibt unberuehrt.

Linux-Ampel (abschaltbar): ProtonDB-Bewertung pro Spiel und die Anti-Cheat-Liste von
AreWeAntiCheatYet (ganze Liste, verraet also nichts ueber die eigenen Spiele).
"""
import json
import os
import re
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

STEAM_ORTE = [
    Path.home() / ".var/app/com.valvesoftware.Steam/.local/share/Steam",  # Flatpak
    Path.home() / ".local/share/Steam",
    Path.home() / ".steam/steam",
    Path.home() / ".steam/debian-installation",
]
# Werkzeuge, die Steam wie Spiele fuehrt
WERKZEUGE = re.compile(r"^(Proton\b|Steam Linux Runtime|Steamworks Common|Steamworks Shared|SteamVR)", re.I)
WERKZEUG_IDS = {"228980", "1070560", "1391110", "1628350", "1493710", "2180100", "250820"}

CACHE = Path(os.environ.get("BIBI_ARCADE_CACHE") or Path.home() / ".cache/bibi-arcade")
AMPEL_DATEI = CACHE / "ampel.json"
ANTICHEAT_DATEI = CACHE / "anticheat.json"
PROTONDB = "https://www.protondb.com/api/v1/reports/summaries/{}.json"
ANTICHEAT = "https://raw.githubusercontent.com/AreWeAntiCheatYet/AreWeAntiCheatYet/master/games.json"
ALTER = 7 * 86400

# Ampel: gruen = laeuft super, gelb = mit Macken, rot = nur Windows, grau = unbekannt
AMPEL_TEXT = {
    "gruen": "läuft super", "gelb": "läuft mit Macken", "rot": "nur Windows", "grau": "noch unbekannt",
}
TIER_AMPEL = {"platinum": "gruen", "gold": "gruen", "native": "gruen", "silver": "gelb", "bronze": "gelb",
              "borked": "rot"}
TIER_TEXT = {"platinum": "Platin", "gold": "Gold", "silver": "Silber", "bronze": "Bronze", "borked": "läuft nicht",
             "native": "Linux-Version"}


# ---------------------------------------------------------------- VDF (Valve-Textformat)

_TOKEN = re.compile(r'"((?:[^"\\]|\\.)*)"|([{}])')


def vdf_lesen(text):
    """Valves KeyValues-Textformat in verschachtelte dicts."""
    wurzel, stapel, schluessel = {}, [], None
    aktuell = wurzel
    for m in _TOKEN.finditer(text):
        wert, klammer = m.group(1), m.group(2)
        if klammer == "{":
            neu = {}
            if schluessel is not None:
                aktuell[schluessel] = neu
            stapel.append(aktuell)
            aktuell, schluessel = neu, None
        elif klammer == "}":
            aktuell = stapel.pop() if stapel else wurzel
            schluessel = None
        elif schluessel is None:
            schluessel = wert.replace('\\"', '"').replace("\\\\", "\\")
        else:
            aktuell[schluessel] = wert.replace('\\"', '"').replace("\\\\", "\\")
            schluessel = None
    return wurzel


def _datei(p):
    try:
        return vdf_lesen(Path(p).read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return {}


def _klein(d):
    """Steam schreibt Schluessel mal gross, mal klein."""
    return {k.lower(): v for k, v in d.items()} if isinstance(d, dict) else {}


# ---------------------------------------------------------------- Spiele

def steam_ort():
    for o in STEAM_ORTE:
        if (o / "steamapps").is_dir():
            return o.resolve()
    return None


def ist_flatpak(ort):
    return ort is not None and ".var/app/com.valvesoftware.Steam" in str(ort)


def bibliotheken(ort):
    orte = [ort]
    lf = _klein(_datei(ort / "steamapps/libraryfolders.vdf").get("libraryfolders"))
    for eintrag in lf.values():
        pfad = _klein(eintrag).get("path") if isinstance(eintrag, dict) else None
        if pfad and Path(pfad).resolve() not in orte and (Path(pfad) / "steamapps").is_dir():
            orte.append(Path(pfad).resolve())
    return orte


def spielzeiten(ort):
    """{appid: {"minuten", "zwei_wochen", "zuletzt"}} aus allen Steam-Konten auf diesem PC."""
    zeiten = {}
    for lc in (ort / "userdata").glob("*/config/localconfig.vdf"):
        d = _datei(lc)
        apps = d
        for teil in ("userlocalconfigstore", "software", "valve", "steam", "apps"):
            apps = _klein(apps).get(teil, {})
        for appid, werte in (apps or {}).items():
            w = _klein(werte)
            neu = {"minuten": int(w.get("playtime") or 0), "zwei_wochen": int(w.get("playtime2wks") or 0),
                   "zuletzt": int(w.get("lastplayed") or 0)}
            alt = zeiten.get(appid)
            if alt is None or neu["minuten"] > alt["minuten"]:
                zeiten[appid] = neu
    return zeiten


def bilder(ort, appid):
    """Pfade zu Cover (2:3), Banner, Hero und Logo, soweit Steam sie schon geladen hat."""
    basis = ort / "appcache/librarycache"
    ordner = basis / appid
    namen = {"cover": "library_600x900", "banner": "header", "hero": "library_hero", "logo": "logo"}
    ergebnis = {}
    for art, name in namen.items():
        kandidaten = []
        if ordner.is_dir():
            kandidaten += [ordner / f"{name}.jpg", ordner / f"{name}.png", ordner / f"{name}_2x.jpg"]
            kandidaten += sorted(ordner.glob(f"*/{name}*.jpg")) + sorted(ordner.glob(f"*/{name}*.png"))
        kandidaten += [basis / f"{appid}_{name}.jpg", basis / f"{appid}_{name}.png"]  # alte Steam-Versionen
        treffer = next((k for k in kandidaten if k.is_file()), None)
        if treffer:
            ergebnis[art] = str(treffer)
    return ergebnis


def spiele():
    """Alle installierten Steam-Spiele als Liste von dicts (ohne Proton & Co.)."""
    ort = steam_ort()
    if ort is None:
        return []
    zeiten = spielzeiten(ort)
    liste, gesehen = [], set()
    for bib in bibliotheken(ort):
        for acf in (bib / "steamapps").glob("appmanifest_*.acf"):
            d = _datei(acf)
            st = _klein(d.get("AppState") or d.get("appstate"))
            appid, name = st.get("appid"), st.get("name") or ""
            if not appid or appid in gesehen or appid in WERKZEUG_IDS or WERKZEUGE.match(name):
                continue
            gesehen.add(appid)
            z = zeiten.get(appid, {})
            flags = int(st.get("stateflags") or 0)
            liste.append({
                "quelle": "steam", "id": appid, "name": name,
                "ordner": str(bib / "steamapps/common" / st.get("installdir", "")),
                "groesse": int(st.get("sizeondisk") or 0),
                "installiert": bool(flags & 4) and not flags & 2,
                "minuten": z.get("minuten", 0), "zwei_wochen": z.get("zwei_wochen", 0),
                "zuletzt": max(z.get("zuletzt", 0), int(st.get("lastplayed") or 0)),
                "bilder": bilder(ort, appid),
            })
    liste.sort(key=lambda s: s["name"].lower())
    return liste


def starten_befehl(spiel):
    """Steam startet das Spiel selbst (mit Proton, Overlay, Cloud-Speicherstaenden)."""
    return ["xdg-open", f"steam://rungameid/{spiel['id']}"]


def steam_seite_befehl(spiel):
    return ["xdg-open", f"steam://nav/games/details/{spiel['id']}"]


# ---------------------------------------------------------------- Spielzeit-Verlauf

def verlauf_merken(liste, datei):
    """Steam kennt nur Gesamtzeiten. Pro Tag einmal festhalten, daraus werden die Wochenbalken."""
    try:
        d = json.loads(Path(datei).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    heute = time.strftime("%Y-%m-%d")
    d.setdefault(heute, {})
    for s in liste:
        d[heute][s["id"]] = s["minuten"]
    # nur ein Jahr aufheben
    for tag in sorted(d)[:-370]:
        d.pop(tag)
    try:
        Path(datei).parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(str(datei) + ".tmp")
        tmp.write_text(json.dumps(d), encoding="utf-8")
        tmp.replace(datei)
    except OSError:
        pass
    return d


def wochen(verlauf, appid, anzahl=8):
    """Gespielte Minuten der letzten Wochen (aelteste zuerst); None, wo noch nichts gesammelt ist."""
    tage = sorted(verlauf)
    jetzt = time.time()
    werte = []
    for w in range(anzahl, 0, -1):
        anfang = time.strftime("%Y-%m-%d", time.localtime(jetzt - w * 7 * 86400))
        ende = time.strftime("%Y-%m-%d", time.localtime(jetzt - (w - 1) * 7 * 86400))
        vorher = [t for t in tage if t <= anfang and appid in verlauf[t]]
        bis = [t for t in tage if t <= ende and appid in verlauf[t]]
        if not bis:
            werte.append(None)
            continue
        start = verlauf[vorher[-1]][appid] if vorher else None
        if start is None:
            werte.append(None)
            continue
        werte.append(max(0, verlauf[bis[-1]][appid] - start))
    return werte


# ---------------------------------------------------------------- Linux-Ampel

def _holen(url, timeout=12):
    with urlopen(Request(url, headers={"User-Agent": "Bibi Arcade (Biblix)"}), timeout=timeout) as a:
        return json.load(a)


def _json(datei, standard):
    try:
        return json.loads(Path(datei).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return standard


def _schreiben(datei, daten):
    try:
        Path(datei).parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(str(datei) + ".tmp")
        tmp.write_text(json.dumps(daten), encoding="utf-8")
        tmp.replace(datei)
    except OSError:
        pass


def anticheat_liste(online=True):
    """{steam_appid: {"status", "anticheats"}} – Spiele, deren Anti-Cheat Linux aussperrt oder erlaubt."""
    d = _json(ANTICHEAT_DATEI, {})
    if online and time.time() - d.get("zeit", 0) > ALTER:
        try:
            spiele_ = _holen(ANTICHEAT, timeout=20)
            neu = {}
            for g in spiele_:
                sid = (g.get("storeIds") or {}).get("steam")
                if sid:
                    neu[str(sid)] = {"status": g.get("status", ""), "anticheats": g.get("anticheats") or [],
                                     "native": bool(g.get("native"))}
            d = {"zeit": time.time(), "spiele": neu}
            _schreiben(ANTICHEAT_DATEI, d)
        except (URLError, OSError, ValueError):
            pass
    return d.get("spiele", {})


def ampel_holen(appids, online=True):
    """{appid: {"ampel", "tier", "anticheat", "grund"}}; wird eine Woche lang gemerkt."""
    gemerkt = _json(AMPEL_DATEI, {})
    ac = anticheat_liste(online)
    ergebnis = {}
    for appid in appids:
        e = gemerkt.get(appid)
        if online and (e is None or time.time() - e.get("zeit", 0) > ALTER):
            try:
                p = _holen(PROTONDB.format(appid))
                e = {"zeit": time.time(), "tier": p.get("tier") or "", "trend": p.get("trendingTier") or "",
                     "berichte": int(p.get("total") or 0)}
            except URLError as f:
                # 404: ProtonDB kennt das Spiel nicht (z. B. Playtests) – das ist auch eine Antwort
                e = {"zeit": time.time(), "tier": "", "trend": "", "berichte": 0} if "404" in str(f) else e
            except (OSError, ValueError):
                pass
            if e:
                gemerkt[appid] = e
        e = e or {}
        tier = e.get("tier", "")
        # Steigt der Trend (z. B. Gold -> Platin), zaehlt der bessere Wert
        if e.get("trend") in ("platinum", "gold") and tier in ("silver", "bronze", "gold"):
            tier = e["trend"]
        a = ac.get(appid, {})
        if a.get("status") in ("Denied", "Broken"):
            ampel, grund = "rot", "Anti-Cheat sperrt Linux aus" if a["status"] == "Denied" else "Anti-Cheat läuft unter Linux nicht"
        elif a.get("native"):
            ampel, grund = "gruen", "Linux-Version"
            tier = tier or "native"
        else:
            ampel = TIER_AMPEL.get(tier, "grau")
            grund = f"ProtonDB: {TIER_TEXT[tier]}" if tier in TIER_TEXT else "noch keine Berichte"
        ergebnis[appid] = {"ampel": ampel, "tier": tier, "grund": grund, "berichte": e.get("berichte", 0),
                           "anticheat": ", ".join(a.get("anticheats", [])), "ac_status": a.get("status", "")}
    _schreiben(AMPEL_DATEI, gemerkt)
    return ergebnis


# ---------------------------------------------------------------- Spielarten (fuer die Netz-Ansicht)

GENRES_DATEI = CACHE / "genres.json"
STORE = "https://store.steampowered.com/api/appdetails?appids={}&filters=genres&l=german"


def genres_holen(appids, online=True):
    """{appid: ["Action", "Simulation", ...]} aus dem Steam-Shop; wird ein Monat lang gemerkt."""
    gemerkt = _json(GENRES_DATEI, {})
    for appid in appids:
        e = gemerkt.get(appid)
        if online and (e is None or time.time() - e.get("zeit", 0) > 4 * ALTER):
            try:
                d = _holen(STORE.format(appid)).get(appid) or {}
                namen = [g.get("description", "") for g in (d.get("data") or {}).get("genres", [])]
                gemerkt[appid] = {"zeit": time.time(), "genres": [n for n in namen if n]}
            except (URLError, OSError, ValueError, AttributeError):
                pass
    _schreiben(GENRES_DATEI, gemerkt)
    return {a: (gemerkt.get(a) or {}).get("genres", []) for a in appids}


def _programm(pid):
    """Das gestartete Programm (argv[0]), mit / statt \\ – unter Proton steht hier der Windows-Pfad (Z:\\home\\…)."""
    with open(f"/proc/{pid}/cmdline", "rb") as f:
        return f.read().split(b"\0", 1)[0].replace(b"\\", b"/")


def laufende(liste):
    """Welche Spiele gerade laufen: ein Programm, das aus steamapps/common/<Ordner>/ gestartet wurde.

    Nur argv[0] zaehlt – ein Dateimanager oder eine Konsole, die den Ordner nur im Befehl hat, ist kein Spiel.
    """
    ordner = {s["id"]: ("steamapps/common/" + Path(s["ordner"]).name + "/").encode() for s in liste if s.get("ordner")}
    if not ordner:
        return set()
    gefunden = set()
    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
    except OSError:
        return set()
    for pid in pids:
        try:
            prog = _programm(pid)
        except OSError:
            continue
        if b"steamapps/common/" not in prog:
            continue
        for appid, teil in ordner.items():
            if teil in prog:
                gefunden.add(appid)
    return gefunden


# ---------------------------------------------------------------- NOT-AUS

STEAM_SELBST = {"steam", "steamwebhelper", "steamwebhelper.sh"}


def prozesse(spiel):
    """Alle Prozesse eines laufenden Spiels (auch unter Proton), aber nie Steam selbst oder die Arcade.

    Treffer nur, wenn das Programm selbst aus dem Spielordner kommt (argv[0]) oder Steam den Prozess
    als dieses Spiel markiert hat (SteamAppId & Co. in der Umgebung). Programme, die den Ordner nur
    erwaehnen (Dateimanager, Konsole, Editor), bleiben in Ruhe.
    """
    teil = ("steamapps/common/" + Path(spiel["ordner"]).name + "/").encode()
    kennungen = [f"SteamAppId={spiel['id']}\0".encode(), f"STEAM_COMPAT_APP_ID={spiel['id']}\0".encode(),
                 f"SteamGameId={spiel['id']}\0".encode()]
    eigen = os.getpid()
    gefunden = []
    try:
        pids = [int(p) for p in os.listdir("/proc") if p.isdigit()]
    except OSError:
        return []
    for pid in pids:
        if pid == eigen:
            continue
        try:
            with open(f"/proc/{pid}/comm", "rb") as f:
                name = f.read().strip().decode("utf-8", "replace")
            if name in STEAM_SELBST:
                continue
            treffer = teil in _programm(pid)
            if not treffer:
                with open(f"/proc/{pid}/environ", "rb") as f:
                    env = f.read() + b"\0"
                treffer = any(k in env for k in kennungen)
        except OSError:
            continue  # Prozess schon weg oder gehoert jemand anderem
        if treffer:
            gefunden.append(pid)
    return gefunden


def signal_senden(pids, sig):
    """Gibt zurueck, wie viele Prozesse das Signal bekommen haben."""
    n = 0
    for pid in pids:
        try:
            os.kill(pid, sig)
            n += 1
        except OSError:
            pass
    return n


# ---------------------------------------------------------------- Freunde (fuer "Einladen")

STEAMID_BASIS = 76561197960265728
AVATARE = CACHE / "avatare"
AVATAR_URL = "https://avatars.steamstatic.com/{}_medium.jpg"


def freunde():
    """(eigener Name, [{"id", "steamid", "name", "avatar"}]) aus dem Freundes-Zwischenspeicher von Steam.

    Steam legt die Liste selbst in localconfig.vdf ab; gelesen werden nur Name und Bild-Kennung.
    """
    ort = steam_ort()
    if ort is None:
        return "", []
    eigen, liste, gesehen = "", [], set()
    for lc in sorted((ort / "userdata").glob("*/config/localconfig.vdf"), key=lambda p: -p.stat().st_mtime):
        fr = _klein(_klein(_datei(lc).get("UserLocalConfigStore")).get("friends"))
        eigen = eigen or fr.get("personaname", "")
        for kennung, d in fr.items():
            if not kennung.isdigit() or not isinstance(d, dict) or kennung in gesehen:
                continue
            gesehen.add(kennung)
            name = d.get("name") or ""
            if not name:
                continue
            liste.append({"id": kennung, "steamid": str(STEAMID_BASIS + int(kennung)), "name": name,
                          "avatar": d.get("avatar", "") if re.fullmatch(r"[0-9a-f]{40}", d.get("avatar", "")) else ""})
    liste.sort(key=lambda f: f["name"].lower())
    return eigen, liste


def avatar(hashwert, online=True):
    """Pfad zum Profilbild (wird einmal von Steams Bildserver geladen), sonst None."""
    if not hashwert:
        return None
    ziel = AVATARE / f"{hashwert}.jpg"
    if ziel.is_file():
        return str(ziel)
    if not online:
        return None
    try:
        with urlopen(Request(AVATAR_URL.format(hashwert), headers={"User-Agent": "Bibi Arcade (Biblix)"}), timeout=10) as a:
            daten = a.read()
        AVATARE.mkdir(parents=True, exist_ok=True)
        tmp = ziel.with_suffix(".tmp")
        tmp.write_bytes(daten)
        tmp.replace(ziel)
        return str(ziel)
    except (URLError, OSError):
        return None


def chat_befehl(freund):
    """Oeffnet in Steam das Chatfenster mit diesem Freund (die Nachricht schickt der Nutzer selbst ab)."""
    return ["xdg-open", f"steam://friends/message/{freund['steamid']}"]


def shop_link(spiel):
    return f"https://store.steampowered.com/app/{spiel['id']}"
