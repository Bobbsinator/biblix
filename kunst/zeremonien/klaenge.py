"""Tonspuren der Zeremonien, per Synthese (keine Aufnahmen). Nutzt die Bausteine aus biblix_design.klaenge.

  python3 klaenge.py ziel_ordner      → hochfahren.wav, keynote.wav, abmelden.wav, herunterfahren.wav, windows.wav
Zeiten passen zu den Filmen (24 Bilder/s): Sekunde = Bild / 24.
"""
import math
import os
import random
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "..", "pakete", "biblix-design", "usr", "share", "biblix", "design", "lib"))
from biblix_design.klaenge import Spur, ton, rauschen, klick, NOTE, RATE  # noqa: E402

B = 1 / 24  # Sekunden je Bild


def grollen(dauer, tief=38.0, seed=1, lautst=1.0):
    """Tiefes Maschinengrollen: gefiltertes Rauschen + Grundton mit langsamer Schwebung."""
    r = rauschen(dauer, abkling=0.0, farbe=0.995, seed=seed)
    n = len(r)
    out = []
    for i in range(n):
        t = i / RATE
        v = r[i] * 6 + 0.5 * math.sin(2 * math.pi * tief * t) * (0.7 + 0.3 * math.sin(2 * math.pi * 0.7 * t))
        out.append(v * lautst)
    return out


def huelle(werte, ein=0.3, aus=0.5):
    n = len(werte)
    a, b = int(ein * RATE), int(aus * RATE)
    return [v * min(1.0, i / max(1, a)) * min(1.0, (n - i) / max(1, b)) for i, v in enumerate(werte)]


def gong(grund=98.0, dauer=4.0):
    return [x + y * 0.6 + z * 0.3 for x, y, z in zip(ton(grund, dauer, "glocke", 0.003, 0.9),
                                                    ton(grund * 2.76, dauer, "sinus", 0.003, 1.6),
                                                    ton(grund * 5.4, dauer, "sinus", 0.003, 2.8))]


def bums(tief=60.0, laut=1.0):
    """Schwerer Schlag (Stempel, Tür)."""
    return [(a * 1.0 + b * 0.5) * laut for a, b in zip(ton(tief, 0.5, "sinus", 0.001, 9, gleiten_zu=tief * 0.6),
                                                     rauschen(0.5, 40, 0.6, seed=4))]


def akkord(noten, dauer, art="saege", lautst=0.25, anschlag=0.04, abkling=0.8):
    teile = [ton(NOTE[n] if isinstance(n, str) else n, dauer, art, anschlag, abkling, vibrato=0.004) for n in noten]
    return [sum(t[i] for t in teile) * lautst for i in range(len(teile[0]))]


def hochfahren():
    s = Spur(264 * B + 0.5)
    s.add(16 * B, klick(0.6), lautst=1.2)                 # Hebel
    s.add(24 * B, bums(90, 0.6))                          # rastet ein
    s.add(36 * B, huelle(grollen(176 * B, 34, lautst=0.5), 1.2, 1.0))   # Fahrt
    for k in range(9):                                    # Ebenen-Pling
        s.add((40 + k * 21) * B, ton(NOTE["E5"] * (1 + k * 0.06), 0.35, "glocke", abkling=8), lautst=0.25)
    s.add(214 * B, rauschen(1.2, 2.5, 0.97, seed=9), lautst=0.6)   # Tore
    s.add(226 * B, gong(98, 3.2), lautst=0.8)
    s.add(232 * B, akkord(["C4", "G4", "C5", "E5"], 1.4, "glocke", 0.25, 0.01, 1.4))
    return s


def keynote():
    s = Spur(288 * B + 0.5)
    s.add(0, huelle(grollen(170 * B, 50, seed=3, lautst=0.25), 2.0, 1.0))   # Saalrauschen
    for i in range(3):                                    # Countdown-Schläge
        s.add((52 + i * 24) * B, bums(70 + i * 15, 0.8))
    s.add(128 * B, akkord(["C3", "G3", "C4"], 2.2, "saege", 0.18, 0.4, 0.6))
    r = random.Random(5)
    for k in range(int(50 * B * RATE / 1100)):            # Trommelwirbel vor der Enthüllung
        s.add((136 + 50 * k / (50 * B * RATE / 1100)) * B, rauschen(0.04, 120, 0.3, seed=r.randint(1, 999)), lautst=0.25 + 0.5 * k / 60)
    s.add(186 * B, akkord(["C4", "E4", "G4", "C5"], 1.6, "saege", 0.22, 0.02, 0.9))
    for i in range(5):                                    # Budgetzähler
        s.add((196 + i * 7) * B, klick(1.0 + i * 0.15), lautst=0.8)
    s.add(232 * B, bums(55, 1.4))                         # GENEHMIGT.
    s.add(234 * B, akkord(["C4", "G4", "C5", "E5", "G5"], 2.0, "saege", 0.2, 0.01, 0.7))   # Fanfare
    s.add(236 * B, rauschen(1.6, 1.8, 0.2, seed=8), lautst=0.25)   # Konfetti
    return s


def abmelden():
    s = Spur(264 * B + 0.5)
    for i, b in enumerate((1, 22, 40, 56, 74, 92)):       # Statuskette
        s.add(b * B, ton(NOTE["C5"] * (1 + i * 0.12), 0.25, "glocke", abkling=10), lautst=0.35)
    s.add(40 * B, huelle(grollen(70 * B, 45, seed=2, lautst=0.6), 1.0, 0.4))   # Anfahrt
    s.add(92 * B, rauschen(0.6, 6, 0.9, seed=3), lautst=0.4)               # Bremsen
    s.add(104 * B, bums(80, 0.7))                                          # Heck auf
    for i in range(4):                                                     # Fenster fliegen ein
        s.add((116 + i * 18 + 22) * B, ton(1200, 0.18, "sinus", 0.002, 18, gleiten_zu=500), lautst=0.3)
    s.add(196 * B, bums(70, 0.9))                                          # Heck zu
    s.add(206 * B, ton(440, 0.25, "rechteck", 0.005, 4), lautst=0.25)      # Hupe
    s.add(206 * B + 0.3, ton(440, 0.25, "rechteck", 0.005, 4), lautst=0.25)
    s.add(214 * B, huelle(grollen(50 * B, 45, seed=5, lautst=0.6), 0.3, 1.2))   # Abfahrt
    return s


def herunterfahren():
    s = Spur(240 * B + 0.5)
    s.add(0, huelle(grollen(240 * B, 30, seed=6, lautst=0.08), 1.5, 2.0))   # Stille Halle
    r = random.Random(1)
    for k in range(70):                                   # Fallblatt-Klappern
        s.add((20 + k * 0.7 + r.uniform(0, 0.4)) * B, klick(1.6 + r.uniform(-0.3, 0.3)), lautst=0.35)
    s.add(120 * B, rauschen(0.4, 9, 0.85, seed=2), lautst=0.4)   # Buch klappt
    s.add(137 * B, bums(90, 0.8))
    s.add(168 * B, bums(48, 1.6))                          # Stempel
    s.add(170 * B, klick(0.5), lautst=0.6)
    s.add(184 * B, huelle(grollen(1.8, 22, seed=7, lautst=0.9), 0.4, 1.2))   # die Eins grollt im Fels
    s.add(218 * B, klick(0.8), lautst=0.9)                 # Lampe aus
    return s


def windows():
    s = Spur(216 * B + 0.5)
    for k in range(40):                                   # Tippen
        s.add((4 + k * 0.9) * B, klick(2.2), lautst=0.15)
    for k in range(6):                                    # Alarm
        s.add((40 + k * 7) * B, ton(880, 0.22, "rechteck", 0.004, 3, gleiten_zu=660), lautst=0.3)
    s.add(110 * B, ton(NOTE["C5"], 0.3, "glocke", abkling=6), lautst=0.4)
    s.add(132 * B, akkord(["C4", "E4", "G4", "C5"], 0.45, "saege", 0.2, 0.01, 2.5))   # feierliche Fanfare
    s.add(132 * B + 0.45, akkord([349.23, 440.0, 523.25], 0.45, "saege", 0.2, 0.01, 2.5))
    s.add(132 * B + 0.9, akkord(["G4", 493.88, "D5", "G5"], 1.8, "saege", 0.22, 0.01, 0.8))
    s.add(160 * B, gong(130, 2.0), lautst=0.4)
    return s


if __name__ == "__main__":
    ziel = sys.argv[1]
    os.makedirs(ziel, exist_ok=True)
    for name, f in (("hochfahren", hochfahren), ("keynote", keynote), ("abmelden", abmelden),
                    ("herunterfahren", herunterfahren), ("windows", windows)):
        f().speichern(__import__("pathlib").Path(ziel) / f"{name}.wav", ziel_db=-6.0)
        print("Ton:", name)
