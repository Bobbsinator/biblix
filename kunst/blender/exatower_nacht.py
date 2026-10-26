"""Standbild: Exabibi Tower bei Nacht ueber der Donau (Cycles).

  blender -b --factory-startup -P exatower_nacht.py -- ziel.png     (SAMPLES=160, BREITE/HOEHE wahlweise)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hilfen import leeren, einstellungen, kamera, nachleuchten, rendern  # noqa: E402
from exatower_szene import aufbauen  # noqa: E402

leeren()
einstellungen(int(os.environ.get("BREITE", 1920)), int(os.environ.get("HOEHE", 1080)),
              samples=int(os.environ.get("SAMPLES", 80)), belichtung=0.3)
aufbauen(ring=False)
cam = kamera((-30, -140, 4.0), (-30, 0, 4.0), brennweite=45)
cam.data.shift_y = 0.15
cam.data.shift_x = 0.12
nachleuchten(schwelle=0.9, groesse=7)
rendern()
