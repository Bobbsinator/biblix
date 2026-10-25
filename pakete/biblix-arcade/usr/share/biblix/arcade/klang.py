"""Leise Rechenzentrum-Geraeusche: werden beim ersten Mal berechnet und als WAV gemerkt.

Abgespielt mit pw-play (PipeWire) oder paplay; ohne beides bleibt es einfach still.
"""
import math
import os
import random
import shutil
import struct
import subprocess
import wave
from pathlib import Path

CACHE = Path(os.environ.get("BIBI_ARCADE_CACHE") or Path.home() / ".cache/bibi-arcade") / "klang"
RATE = 44100
STAND = "2"  # bei Aenderungen an den Klaengen hochzaehlen


def _schreiben(datei, proben):
    datei.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(datei), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", max(-32767, min(32767, int(x * 32767)))) for x in proben))


def _klick(dauer=0.035, frei=900, laut=0.5):
    rnd = random.Random(7)
    n = int(RATE * dauer)
    return [laut * math.exp(-i / (n / 6)) * (0.6 * rnd.uniform(-1, 1) + 0.4 * math.sin(2 * math.pi * frei * i / RATE))
            for i in range(n)]


def _ton(frei, dauer, laut=0.3, abkling=4.0):
    n = int(RATE * dauer)
    return [laut * math.exp(-abkling * i / n) * math.sin(2 * math.pi * frei * i / RATE) for i in range(n)]


def _stille(dauer):
    return [0.0] * int(RATE * dauer)


def _hochfahren():
    """Luefter laeuft an: Rauschen, das heller wird, darunter ein steigender Brummton."""
    rnd = random.Random(3)
    n = int(RATE * 1.4)
    aus, tief = [], 0.0
    for i in range(n):
        t = i / n
        huelle = min(1.0, t * 3) * (1 - max(0.0, t - 0.75) * 4)
        tief += (rnd.uniform(-1, 1) - tief) * (0.02 + 0.25 * t)  # Tiefpass oeffnet sich
        brumm = math.sin(2 * math.pi * (60 + 90 * t) * i / RATE)
        aus.append(0.22 * huelle * (0.7 * tief + 0.3 * brumm))
    return _klick(laut=0.45) + aus


KLAENGE = {
    "klick": lambda: _klick(laut=0.35),
    "relais": lambda: _klick(laut=0.45) + _stille(0.06) + _klick(frei=650, laut=0.35),
    "hochfahren": _hochfahren,
    "start": lambda: _ton(880, 0.09, 0.22) + _ton(1320, 0.16, 0.22),
    "fehler": lambda: _ton(180, 0.14, 0.3, 1.0) + _stille(0.05) + _ton(150, 0.2, 0.3, 1.0),
    "fertig": lambda: _ton(660, 0.12, 0.22) + _ton(990, 0.12, 0.22) + _ton(1320, 0.25, 0.22),
}


class Klang:
    def __init__(self, an=True):
        self.an = an
        self.spieler = shutil.which("pw-play") or shutil.which("paplay")

    def datei(self, name):
        d = CACHE / f"{name}-{STAND}.wav"
        if not d.is_file():
            try:
                _schreiben(d, KLAENGE[name]())
            except OSError:
                return None
        return d

    def spielen(self, name):
        if not self.an or not self.spieler or name not in KLAENGE:
            return
        d = self.datei(name)
        if d is None:
            return
        argv = [self.spieler, str(d)]
        if self.spieler.endswith("pw-play"):
            argv[1:1] = ["--volume", "0.6"]
        try:
            subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            pass
