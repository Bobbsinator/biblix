"""Titelkarte am Ende von „Hochfahren“: aus dem Licht oben wird „AUF BIBLIX GEHT DAS.“ (2 s, an die Bilder angehängt).

  python3 titel.py ordner_mit_bild_XXXX.png      (hängt Bilder hinter das letzte an)
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

ORDNER = sys.argv[1]
bilder = sorted(f for f in os.listdir(ORDNER) if f.startswith("bild_") and f.endswith(".png"))
letztes = Image.open(os.path.join(ORDNER, bilder[-1])).convert("RGB")
W, H = letztes.size
F = H / 1440
n0 = int(bilder[-1][5:9])
fett = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(150 * F))
klein = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", int(46 * F))
NAVY = (6, 14, 30)
for i in range(1, 61):
    t = i / 60
    hell = min(1.0, t * 3)
    grund = Image.blend(letztes, Image.new("RGB", (W, H), (255, 252, 240)), hell) if t < 0.34 else \
        Image.blend(Image.new("RGB", (W, H), (255, 252, 240)), Image.new("RGB", (W, H), NAVY), min(1.0, (t - 0.34) / 0.3))
    schrift = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(schrift)
    if t > 0.5:
        a = min(1.0, (t - 0.5) / 0.2)
        text = "AUF BIBLIX GEHT DAS."
        b = d.textlength(text, font=fett)
        farbe = tuple(int(c * a) for c in (255, 212, 0))
        d.text(((W - b) / 2, H * 0.40), text, font=fett, fill=farbe)
    if t > 0.66:
        a = min(1.0, (t - 0.66) / 0.2)
        text = "Es gäbe schnellere Wege. Aber keiner davon ist Big Bibi."
        b = d.textlength(text, font=klein)
        d.text(((W - b) / 2, H * 0.56), text, font=klein, fill=tuple(int(c * a) for c in (200, 210, 225)))
    glanz = schrift.filter(ImageFilter.GaussianBlur(24 * F))
    bild = ImageChops.add(grund, ImageChops.add(schrift, glanz))
    bild.save(os.path.join(ORDNER, f"bild_{n0 + i:04d}.png"))
print("Titelkarte angehängt:", n0 + 1, "bis", n0 + 60)
