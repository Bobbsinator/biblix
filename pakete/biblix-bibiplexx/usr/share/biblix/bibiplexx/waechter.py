#!/usr/bin/env python3
"""Bibiplexx-Waechter: meldet sich, wenn eine Platte mit neuen Filmen oder Serien angesteckt wird.

Laeuft ab der Anmeldung still im Hintergrund (bibiplexx --waechter). Schaut alle paar Sekunden,
ob eine neue Wechselplatte da ist, haengt sie bei Bedarf ein und zaehlt, was es darauf gibt,
das in Bibiplexx noch fehlt. Dann eine Meldung mit "Importieren". Platten, die schon beim
Anmelden steckten, bleiben in Ruhe.

Absichtlich ohne Qt, damit der Waechter kaum Speicher braucht; der Rest kommt erst bei Bedarf.
"""
import fcntl
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
KONFIG = Path(os.environ.get("BIBLIX_KONFIG_DIR") or Path.home() / ".config/biblix") / "bibiplexx.json"
PLATTE_ORT = "/media/bibiplexx"
DATEISYSTEME = {"exfat", "ntfs", "ntfs3", "vfat", "ext4", "ext3", "ext2", "btrfs", "xfs", "f2fs", "hfsplus", "udf", "iso9660"}
TAKT = 3


def nutzer_basen():
    user = os.environ.get("USER") or Path.home().name
    return (f"/media/{user}/", f"/run/media/{user}/")


def ort_entschluesseln(ort):
    return ort.replace("\\040", " ").replace("\\011", "\t").replace("\\012", "\n").replace("\\134", "\\")


def nutzer_orte():
    """Eingehaengte Wechselplatten des Nutzers (unter /media/<name>/)."""
    basen = nutzer_basen()
    orte = []
    try:
        for zeile in Path("/proc/self/mounts").read_text().splitlines():
            teile = zeile.split()
            if len(teile) >= 3:
                ort = ort_entschluesseln(teile[1])
                if ort.startswith(basen) and ort.rstrip("/") != PLATTE_ORT:
                    orte.append(ort)
    except OSError:
        pass
    return orte


def lsblk():
    try:
        out = subprocess.run(["lsblk", "-J", "-p", "-o", "PATH,FSTYPE,MOUNTPOINT,HOTPLUG,TYPE"],
                             capture_output=True, text=True, timeout=10).stdout
        geraete = []

        def sammeln(liste):
            for d in liste or []:
                geraete.append(d)
                sammeln(d.get("children"))
        sammeln(json.loads(out or "{}").get("blockdevices"))
        return geraete
    except (OSError, subprocess.SubprocessError, ValueError):
        return []


def melden_erlaubt():
    try:
        return json.loads(KONFIG.read_text(encoding="utf-8")).get("import_melden", True) is not False
    except (OSError, ValueError):
        return True


def einhaengen(pfad):
    """Wechselplatte einhaengen wie der Dateimanager (ohne Passwort, nur fuer die eigene Sitzung)."""
    subprocess.run(["udisksctl", "mount", "-b", pfad, "--no-user-interaction"],
                   capture_output=True, text=True, timeout=60)


def anzahl_text(folgen, filme):
    teile = []
    if folgen:
        teile.append(f"{folgen} neue Folge{'n' if folgen != 1 else ''}")
    if filme:
        teile.append(f"{filme} neue{'n' if filme == 1 else ''} Film{'e' if filme != 1 else ''}")
    return " und ".join(teile)


def pruefen(ort):
    """Neue Videos auf der Platte zaehlen und bei Bedarf fragen."""
    if not melden_erlaubt():
        return
    sys.path.insert(0, str(HIER))
    import importieren  # erst hier: zieht Qt mit
    folgen, filme = importieren.neue_zaehlen(ort, frist=25)
    if not folgen and not filme:
        return
    name = Path(ort).name
    try:
        antwort = subprocess.run(
            ["notify-send", "-a", "Bibiplexx", "-i", "de.biblix.Bibiplexx",
             "-A", "importieren=Importieren", "-A", "nein=Nicht jetzt",
             "Neues für Bibiplexx", f"Auf „{name}“ gibt es {anzahl_text(folgen, filme)}. In Bibiplexx übernehmen?"],
            capture_output=True, text=True, timeout=3600).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return
    if antwort == "importieren":
        subprocess.Popen(["bibiplexx", "--importieren", ort], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    laufzeit = Path(os.environ.get("XDG_RUNTIME_DIR") or "/tmp")
    sperre = open(laufzeit / "bibiplexx-waechter.lock", "w")
    try:
        fcntl.flock(sperre, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return  # laeuft schon
    bekannt_orte = set(nutzer_orte())
    bekannt_geraete = {d["path"] for d in lsblk()}
    uuids = Path("/dev/disk/by-uuid")
    stand = None
    while True:
        time.sleep(TAKT)
        # Neue Geraete: nur dann lsblk fragen, wenn sich unter /dev/disk/by-uuid etwas tut
        try:
            jetzt = tuple(sorted(os.listdir(uuids)))
        except OSError:
            jetzt = ()
        if jetzt != stand:
            stand = jetzt
            geraete = lsblk()
            for d in geraete:
                if d["path"] in bekannt_geraete:
                    continue
                bekannt_geraete.add(d["path"])
                if d.get("type") in ("part", "disk") and d.get("fstype") in DATEISYSTEME \
                        and d.get("hotplug") in (True, "1", 1) and not d.get("mountpoint") and melden_erlaubt():
                    threading.Thread(target=einhaengen, args=(d["path"],), daemon=True).start()
            bekannt_geraete &= {d["path"] for d in geraete} or bekannt_geraete
        orte = set(nutzer_orte())
        for ort in sorted(orte - bekannt_orte):
            threading.Thread(target=lambda o=ort: (time.sleep(2), pruefen(o)), daemon=True).start()
        bekannt_orte = orte


if __name__ == "__main__":
    main()
