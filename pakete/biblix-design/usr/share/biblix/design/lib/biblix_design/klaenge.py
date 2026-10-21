"""Biblix-Klaenge per Synthese (beim Paketbau). Keine Aufnahmen, keine fremden Rechte.

Erzeugt Klangthemen nach freedesktop-Standard:
  biblix (Grundklaenge), biblix-retro, biblix-ruhig,
  biblix-tech, -bank, -delivery, -mac, -nass, -kino (Firmen: eigener Startklang und Hinweis)
"""
import math
import random
import struct
import subprocess
import wave
from pathlib import Path

RATE = 44100


class Spur:
    def __init__(self, sekunden):
        self.n = int(sekunden * RATE)
        self.l = [0.0] * self.n
        self.r = [0.0] * self.n

    def add(self, start, werte, pan=0.0, lautst=1.0):
        i0 = int(start * RATE)
        gl, gr = lautst * (1 - max(0, pan)), lautst * (1 + min(0, pan))
        for i, v in enumerate(werte):
            j = i0 + i
            if j >= self.n:
                break
            self.l[j] += v * gl
            self.r[j] += v * gr

    def speichern(self, pfad: Path, ziel_db=-3.0):
        spitze = max(1e-9, max(max(abs(x) for x in self.l), max(abs(x) for x in self.r)))
        f = (10 ** (ziel_db / 20)) / spitze
        with wave.open(str(pfad), "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(RATE)
            daten = bytearray()
            for a, b in zip(self.l, self.r):
                daten += struct.pack("<hh", int(max(-1, min(1, a * f)) * 32767), int(max(-1, min(1, b * f)) * 32767))
            w.writeframes(bytes(daten))


def ton(freq, dauer, art="sinus", anschlag=0.004, abkling=6.0, vibrato=0.0, gleiten_zu=None):
    n = int(dauer * RATE)
    out, phase = [], 0.0
    for i in range(n):
        t = i / RATE
        f = freq if gleiten_zu is None else freq + (gleiten_zu - freq) * (t / dauer)
        if vibrato:
            f *= 1 + vibrato * math.sin(2 * math.pi * 5.5 * t)
        phase += 2 * math.pi * f / RATE
        if art == "sinus":
            v = math.sin(phase)
        elif art == "rechteck":
            v = 0.6 if math.sin(phase) >= 0 else -0.6
        elif art == "saege":
            v = 0.7 * (((phase / (2 * math.pi)) % 1.0) * 2 - 1)
        elif art == "glocke":  # FM-Glocke
            v = math.sin(phase + 1.8 * math.exp(-t * 4) * math.sin(phase * 3.5))
        else:
            v = math.sin(phase)
        huelle = min(1.0, t / anschlag) * math.exp(-t * abkling)
        out.append(v * huelle)
    return out


def rauschen(dauer, abkling=60.0, farbe=0.0, seed=1):
    rnd = random.Random(seed)
    n, out, letzt = int(dauer * RATE), [], 0.0
    for i in range(n):
        x = rnd.uniform(-1, 1)
        letzt = letzt * farbe + x * (1 - farbe)  # einfacher Tiefpass
        out.append(letzt * math.exp(-i / RATE * abkling))
    return out


def klick(hell=1.0):
    """Einrast-Klick: kurzer heller Transient + kleiner Koerper."""
    return mix([x * 0.7 for x in rauschen(0.012, 380, 0.2, seed=7)],
               [x * 0.5 for x in ton(2600 * hell, 0.03, abkling=160)],
               [x * 0.4 for x in ton(900 * hell, 0.05, abkling=90)])


def einlegen(ziel, werte, start, lautst=1.0):
    o = int(start * RATE)
    for i, v in enumerate(werte):
        if o + i >= len(ziel):
            break
        ziel[o + i] += v * lautst


def mix(*listen):
    n = max(len(x) for x in listen)
    return [sum(x[i] for x in listen if i < len(x)) for i in range(n)]


NOTE = {"C4": 261.63, "D4": 293.66, "E4": 329.63, "G4": 392.0, "A4": 440.0, "C5": 523.25, "D5": 587.33,
        "E5": 659.25, "G5": 783.99, "A5": 880.0, "C6": 1046.5, "E6": 1318.5, "G3": 196.0, "C3": 130.81}


# ---------------------------------------------------------------- Grundklaenge

def jingle(akzent=None):
    """Der Bibi-Jingle: schneller Aufstieg, einrastender Schlussakkord."""
    s = Spur(2.6 if akzent else 2.0)
    for i, n in enumerate(["G4", "C5", "E5", "G5"]):
        s.add(0.0 + i * 0.085, ton(NOTE[n], 0.5, "glocke", abkling=7), pan=-0.4 + i * 0.25, lautst=0.55)
    t = 0.40
    s.add(t, klick(), lautst=0.6)
    s.add(t, ton(NOTE["C3"], 1.2, "sinus", anschlag=0.01, abkling=3.0), lautst=0.55)
    for n, pan in (("C5", -0.3), ("E5", 0.3), ("G5", -0.15), ("C6", 0.15)):
        s.add(t, ton(NOTE[n], 1.5, "glocke", anschlag=0.006, abkling=2.4, vibrato=0.002), pan=pan, lautst=0.42)
    s.add(t + 0.02, ton(NOTE["E6"], 0.9, "sinus", abkling=4.0, vibrato=0.004), lautst=0.12)
    if akzent:
        s.add(1.25, akzent, lautst=0.7)
    return s


def pling():
    s = Spur(0.7)
    s.add(0, ton(NOTE["E5"], 0.6, "glocke", abkling=7), lautst=0.6)
    s.add(0.07, ton(NOTE["A5"], 0.6, "glocke", abkling=7), lautst=0.5)
    return s


def klonk():
    s = Spur(0.5)
    s.add(0, ton(150, 0.45, "sinus", anschlag=0.002, abkling=11, gleiten_zu=110), lautst=0.9)
    s.add(0, ton(225, 0.3, "sinus", anschlag=0.002, abkling=16), lautst=0.4)
    s.add(0, rauschen(0.04, 90, 0.6, seed=3), lautst=0.3)
    return s


def warnung():
    s = Spur(0.6)
    s.add(0, ton(NOTE["A4"], 0.25, "glocke", abkling=10), lautst=0.6)
    s.add(0.16, ton(NOTE["E4"], 0.4, "glocke", abkling=8), lautst=0.6)
    return s


def frage():
    s = Spur(0.6)
    s.add(0, ton(NOTE["E5"], 0.25, "glocke", abkling=10), lautst=0.55)
    s.add(0.13, ton(NOTE["G5"], 0.45, "glocke", abkling=7), lautst=0.55)
    return s


def geraet(rein=True):
    s = Spur(0.45)
    a, b = (klick(0.8), klick(1.2)) if rein else (klick(1.2), klick(0.8))
    s.add(0, a, lautst=0.6)
    s.add(0.11, b, lautst=0.7)
    s.add(0.11, ton(NOTE["C5" if rein else "G4"], 0.3, "sinus", abkling=12), lautst=0.25)
    return s


def tick():
    s = Spur(0.12)
    s.add(0, klick(1.1), lautst=0.5)
    return s


def abmelden():
    s = Spur(1.4)
    for i, n in enumerate(["G5", "E5", "C5", "G4"]):
        s.add(i * 0.1, ton(NOTE[n], 0.7, "glocke", abkling=5), lautst=0.45, pan=0.3 - i * 0.2)
    s.add(0.42, klick(0.7), lautst=0.4)
    return s


def papierkorb():
    s = Spur(0.6)
    s.add(0, rauschen(0.25, 14, 0.85, seed=11), lautst=0.7)
    s.add(0.05, rauschen(0.2, 18, 0.9, seed=12), lautst=0.5)
    s.add(0.22, klick(0.6), lautst=0.4)
    return s


def fertig():
    s = Spur(0.9)
    s.add(0, ton(NOTE["C5"], 0.6, "glocke", abkling=6), lautst=0.5)
    s.add(0.1, ton(NOTE["G5"], 0.7, "glocke", abkling=5), lautst=0.5)
    s.add(0.1, klick(), lautst=0.35)
    return s


# ---------------------------------------------------------------- Retro / Ruhig

def retro_beep(freqs, laenge=0.08, pause=0.03):
    s = Spur(len(freqs) * (laenge + pause) + 0.05)
    for i, f in enumerate(freqs):
        s.add(i * (laenge + pause), ton(f, laenge, "rechteck", anschlag=0.001, abkling=2), lautst=0.4)
    return s


def ruhig(freq, dauer=0.35):
    s = Spur(dauer + 0.1)
    s.add(0, ton(freq, dauer, "sinus", anschlag=0.02, abkling=9), lautst=0.3)
    return s


# ---------------------------------------------------------------- Firmen-Akzente

def akzent_tech():
    """Hochfahr-Summen mit kurzem Daten-Zirpen."""
    out = ton(80, 0.7, "saege", anschlag=0.05, abkling=1.5, gleiten_zu=420)
    tief = rauschen(0.7, 2, 0.97, seed=5)
    summen = [a * 0.35 + b * 0.2 for a, b in zip(out, tief)]
    rnd = random.Random(42)
    zirp = []
    for k in range(7):
        zirp += ton(rnd.choice([1800, 2400, 3000, 3600]), 0.025, "rechteck", anschlag=0.001, abkling=40) + [0] * 300
    s = [0.0] * (int(0.55 * RATE) + len(zirp))
    einlegen(s, summen, 0)
    einlegen(s, zirp, 0.55, 0.35)
    return s


def akzent_bank():
    """Muenzklimpern: metallische, unharmonische Pings."""
    rnd = random.Random(9)
    s = [0.0] * int(0.9 * RATE)
    for k in range(6):
        t0 = int((k * 0.07 + rnd.uniform(0, 0.04)) * RATE)
        basis = rnd.uniform(3200, 4800)
        ping = mix(*[[x * a for x in ton(basis * f, 0.4, "sinus", anschlag=0.001, abkling=14 + 6 * j)]
                     for j, (f, a) in enumerate([(1, 0.6), (1.47, 0.35), (2.09, 0.25), (2.56, 0.15)])])
        for i, v in enumerate(ping):
            if t0 + i < len(s):
                s[t0 + i] += v * (0.8 - k * 0.08)
    return s


def akzent_delivery():
    """Roller-Hupe: zweimal kurz, zweistimmig."""
    s = []
    for _ in range(2):
        a = ton(410, 0.13, "rechteck", anschlag=0.003, abkling=1.5)
        b = ton(515, 0.13, "rechteck", anschlag=0.003, abkling=1.5)
        s += [x * 0.5 + y * 0.5 for x, y in zip(a, b)] + [0.0] * int(0.06 * RATE)
    return s


def akzent_mac():
    """Kassa: Lade klackt auf, dann das Kling der Kasse."""
    lade = mix(rauschen(0.08, 50, 0.5, seed=21), [x * 0.6 for x in ton(180, 0.1, "sinus", abkling=40)])
    kling = mix([x * 0.6 for x in ton(2490, 0.9, "glocke", anschlag=0.002, abkling=4)],
                [x * 0.4 for x in ton(3720, 0.7, "sinus", anschlag=0.002, abkling=5)],
                [x * 0.25 for x in ton(4980, 0.5, "sinus", anschlag=0.002, abkling=7)])
    s = [0.0] * int(1.1 * RATE)
    for i, v in enumerate(lade):
        s[i] += v * 0.8
    o = int(0.12 * RATE)
    for i, v in enumerate(kling):
        if o + i < len(s):
            s[o + i] += v
    return s


def akzent_nass():
    """Plaetschern: Blubberblasen und etwas Wasserrauschen."""
    rnd = random.Random(33)
    s = [0.0] * int(0.9 * RATE)
    for k in range(9):
        t0 = int(rnd.uniform(0, 0.6) * RATE)
        f0 = rnd.uniform(350, 700)
        blase = ton(f0, 0.06, "sinus", anschlag=0.002, abkling=45, gleiten_zu=f0 * 2.6)
        for i, v in enumerate(blase):
            if t0 + i < len(s):
                s[t0 + i] += v * 0.5
    for i, v in enumerate(rauschen(0.7, 5, 0.75, seed=34)):
        s[i] += v * 0.18
    return s


def akzent_kino():
    """Kino-Gong: tiefe, lange, unharmonische Teiltoene."""
    teile = [(98, 1.0, 1.1), (166, 0.6, 1.5), (233, 0.45, 2.0), (311, 0.3, 2.6), (402, 0.2, 3.2)]
    return mix(*[[x * a for x in ton(f, 3.0, "sinus", anschlag=0.008, abkling=k, vibrato=0.0015)] for f, a, k in teile])


AKZENTE = {"tech": akzent_tech, "bank": akzent_bank, "delivery": akzent_delivery,
           "mac": akzent_mac, "nass": akzent_nass, "kino": akzent_kino}


def _als_spur(werte, lautst=1.0):
    s = Spur(len(werte) / RATE + 0.05)
    s.add(0, werte, lautst=lautst)
    return s


# ---------------------------------------------------------------- Themen schreiben

def _thema(ziel: Path, name, beschreibung, erbt, dateien):
    d = ziel / name / "stereo"
    d.mkdir(parents=True, exist_ok=True)
    for datei, spur in dateien.items():
        wav = d / f"{datei}.wav"
        spur.speichern(wav)
        oga = d / f"{datei}.oga"
        subprocess.run(["oggenc", "-Q", "-q", "5", "-o", str(oga), str(wav)], check=True)
        wav.unlink()
    (ziel / name / "index.theme").write_text(
        f"[Sound Theme]\nName={beschreibung}\nComment=Biblix-Klänge\nInherits={erbt}\nDirectories=stereo\n\n"
        f"[stereo]\nOutputProfile=stereo\n", encoding="utf-8")


def alle(ziel: Path):
    grund = {
        "desktop-login": jingle(), "desktop-logout": abmelden(),
        "dialog-information": pling(), "message-new-instant": pling(), "message": pling(),
        "dialog-warning": warnung(), "dialog-error": klonk(), "dialog-error-critical": klonk(),
        "dialog-error-serious": klonk(), "dialog-question": frage(),
        "device-added": geraet(True), "device-removed": geraet(False),
        "audio-volume-change": tick(), "button-pressed": tick(), "trash-empty": papierkorb(),
        "complete": fertig(), "completion-success": fertig(), "bell": pling(), "bell-window-system": tick(),
    }
    _thema(ziel, "biblix", "Biblix", "ocean,freedesktop", grund)
    _thema(ziel, "biblix-retro", "Biblix Retro", "biblix", {
        "desktop-login": retro_beep([523, 659, 784, 1047, 784, 1047], 0.09, 0.02),
        "desktop-logout": retro_beep([1047, 784, 523], 0.1, 0.03),
        "dialog-information": retro_beep([880, 1320]), "message-new-instant": retro_beep([880, 1320]),
        "dialog-warning": retro_beep([660, 440]), "dialog-error": retro_beep([220, 180], 0.15),
        "dialog-question": retro_beep([660, 880]), "device-added": retro_beep([440, 880]),
        "device-removed": retro_beep([880, 440]), "audio-volume-change": retro_beep([1200], 0.03),
        "trash-empty": retro_beep([300, 200, 120], 0.06), "complete": retro_beep([784, 1047]),
    })
    _thema(ziel, "biblix-ruhig", "Biblix Ruhig", "biblix", {
        "desktop-login": ruhig(NOTE["C5"], 0.6), "desktop-logout": ruhig(NOTE["G4"], 0.5),
        "dialog-information": ruhig(NOTE["E5"]), "message-new-instant": ruhig(NOTE["E5"]),
        "dialog-warning": ruhig(NOTE["A4"]), "dialog-error": ruhig(NOTE["C4"]),
        "dialog-question": ruhig(NOTE["G5"]), "device-added": ruhig(NOTE["C5"], 0.2),
        "device-removed": ruhig(NOTE["G4"], 0.2), "audio-volume-change": ruhig(NOTE["C6"], 0.05),
        "complete": ruhig(NOTE["G5"]),
    })
    for kurz, funk in AKZENTE.items():
        a = funk()
        _thema(ziel, f"biblix-{kurz}", f"Biblix {kurz.capitalize()}", "biblix", {
            "desktop-login": jingle(a),
            "dialog-information": _als_spur(a), "message-new-instant": _als_spur(a),
        })


if __name__ == "__main__":
    import sys
    alle(Path(sys.argv[1]))
