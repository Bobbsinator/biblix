"""Zeremonie „Neustart in Windows“: Netter Versuch. Retro-Terminal im Röhrenlook (Pillow, kein Blender).

Bibi OS bemerkt den Wechsel: Alarm, rote Lampe, „FREMDES SYSTEM ERKANNT“, Zugriffsprüfung,
dann lenkt es feierlich ein: „VIEL ERFOLG.“ und „DEIN SYSTEM. DEIN PROBLEM.“ (Sprüche aus Masterbrief 8.6).

  python3 windows.py ausgabe/ordner      (BREITE/HOEHE wahlweise, Standard 2560x1440, 24 Bilder/s)
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ZIEL = sys.argv[1]
W, H = int(os.environ.get("BREITE", 2560)), int(os.environ.get("HOEHE", 1440))
F = H / 1440
BILDER = 216
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_FETT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
GRUEN, AMBER, ROT, WEISS = (120, 255, 170), (255, 176, 32), (255, 60, 60), (235, 240, 245)
rnd = random.Random(12)


def schrift(gr, fett=False):
    return ImageFont.truetype(MONO_FETT if fett else MONO, int(gr * F))


ZEILEN = [  # (ab Bild, Text, Farbe)
    (4, "bibi@biblix:~$ biblix-neustart-windows", GRUEN),
    (16, "[ OK ] Bootmenü: nächster Start = Windows Boot Manager", GRUEN),
    (24, "[ .. ] Prüfe Zielsystem …", GRUEN),
    (40, "[WARN] FREMDES SYSTEM ERKANNT.", ROT),
    (52, "[WARN] Zugriff verweigert.", ROT),
    (60, "[WARN] Netter Versuch.", ROT),
    (84, "[ .. ] Rückfrage beim Benutzer: Neustart gewünscht.", AMBER),
    (98, "[ .. ] Entscheidung wird respektiert.", AMBER),
    (110, "[ OK ] Freigabe erteilt.", GRUEN),
]
TIPP = 1.6  # Zeichen pro Bild


def bild(f):
    im = Image.new("RGB", (W, H), (4, 8, 6))
    d = ImageDraw.Draw(im)
    alarm = 40 <= f < 84
    # Zeilen tippen
    y = 110 * F
    for ab, text, farbe in ZEILEN:
        if f < ab:
            break
        n = int((f - ab) * TIPP * (3 if text.startswith("[") else 1)) + 1
        d.text((120 * F, y), text[:n], font=schrift(54), fill=farbe)
        y += 84 * F
    cursor_an = (f // 6) % 2 == 0
    if f < 140 and cursor_an:
        d.rectangle((120 * F, y + 8 * F, 150 * F, y + 66 * F), fill=GRUEN)
    # Alarm: rote Lampe, die sich dreht, Schriftband
    if alarm:
        cx, cy, r = W - 260 * F, 230 * F, 110 * F
        winkel = (f - 40) * 0.5
        strahl = Image.new("RGB", (W, H), (0, 0, 0))
        sd = ImageDraw.Draw(strahl)
        for k in (0, math.pi):
            a = winkel + k
            p = [(cx, cy), (cx + math.cos(a - 0.35) * W, cy + math.sin(a - 0.35) * W), (cx + math.cos(a + 0.35) * W, cy + math.sin(a + 0.35) * W)]
            sd.polygon(p, fill=(70, 0, 0))
        strahl = strahl.filter(ImageFilter.GaussianBlur(40 * F))
        im = Image.composite(im, im, Image.new("L", (W, H), 255))
        im = Image.blend(im, Image.eval(Image.merge("RGB", (Image.eval(strahl.split()[0], lambda v: v), strahl.split()[1], strahl.split()[2])), lambda v: v), 0.0)
        im = Image.fromarray if False else im
        from PIL import ImageChops
        im = ImageChops.add(im, strahl)
        d = ImageDraw.Draw(im)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(200, 20, 20) if (f // 4) % 2 else (120, 10, 10), outline=(40, 0, 0), width=int(8 * F))
        d.ellipse((cx - r * 0.45, cy - r * 0.7, cx - r * 0.05, cy - r * 0.35), fill=(255, 140, 140))
        band_y = H - 300 * F
        d.rectangle((0, band_y, W, band_y + 150 * F), fill=(30, 0, 0))
        for k in range(-2, int(W / (90 * F)) + 2):
            x = k * 90 * F + ((f * 6 * F) % (90 * F))
            d.polygon([(x, band_y), (x + 45 * F, band_y), (x + 5 * F, band_y + 150 * F), (x - 40 * F, band_y + 150 * F)], fill=(255, 200, 0))
        d.rectangle((W * 0.18, band_y + 25 * F, W * 0.82, band_y + 125 * F), fill=(20, 0, 0))
        text = "FREMDES SYSTEM ERKANNT"
        sf = schrift(70, True)
        b = d.textlength(text, font=sf)
        d.text(((W - b) / 2, band_y + 32 * F), text, font=sf, fill=ROT if (f // 6) % 2 else (255, 200, 200))
    # Feierlicher Schluss
    if f >= 132:
        t = min(1.0, (f - 132) / 14)
        ueber = Image.new("RGB", (W, H), (4, 8, 6))
        ud = ImageDraw.Draw(ueber)
        sf = schrift(150, True)
        text = "VIEL ERFOLG."
        b = ud.textlength(text, font=sf)
        ud.text(((W - b) / 2, H * 0.36), text, font=sf, fill=AMBER)
        if f >= 160:
            sf2 = schrift(60, True)
            t2 = "DEIN SYSTEM. DEIN PROBLEM."
            n = int((f - 160) * 1.4) + 1
            b2 = ud.textlength(t2, font=sf2)
            ud.text(((W - b2) / 2, H * 0.56), t2[:n], font=sf2, fill=WEISS)
        # Lichtkranz hinter der Schrift
        glanz = ueber.filter(ImageFilter.GaussianBlur(30 * F))
        from PIL import ImageChops
        ueber = ImageChops.add(ueber, glanz)
        im = Image.blend(im, ueber, t)
    # Ausblenden
    if f > BILDER - 14:
        im = Image.blend(im, Image.new("RGB", (W, H), (0, 0, 0)), (f - (BILDER - 14)) / 14)
    # Roehre: Zeilen, Rauschen, Woelbung als Vignette
    roehre = Image.new("L", (W, H), 0)
    rd = ImageDraw.Draw(roehre)
    for yy in range(0, H, max(2, int(4 * F))):
        rd.line((0, yy, W, yy), fill=38)
    im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), im, roehre)
    vign = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vign).ellipse((-W * 0.15, -H * 0.2, W * 1.15, H * 1.2), fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(160 * F))
    im = Image.composite(im, Image.new("RGB", (W, H), (0, 0, 0)), vign)
    from PIL import ImageChops
    glow = im.filter(ImageFilter.GaussianBlur(6 * F))
    im = ImageChops.add(im, Image.eval(glow, lambda v: v // 2))
    # Flackern
    if rnd.random() < 0.06:
        im = Image.eval(im, lambda v: int(v * 0.85))
    return im


os.makedirs(ZIEL, exist_ok=True)
einzel = os.environ.get("EINZEL")
for f in ([int(x) for x in einzel.split(",")] if einzel else range(1, BILDER + 1)):
    bild(f).save(os.path.join(ZIEL, f"bild_{f:04d}.png"))
print("fertig")
