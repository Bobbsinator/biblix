"""Zeremonie „Abmelden“: Bibi Delivery holt dich ab.

Statuskette (Masterbrief 9.3) läuft durch, ein Bastionswürfel (BDW-B, „Schwer. Langsam. Gepanzert. Pünktlich.“)
fährt vor, öffnet das Heck, deine Fenster fliegen hinein, Klappe zu, Abfahrt. Nacht, nasser Asphalt.

  blender -b --factory-startup -P abmelden.py -- ausgabe/bild_
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
from hilfen import (leeren, eevee, material, hex_farbe, quader, licht, welt, text3d, schluessel,  # noqa: E402
                    sichtbar, nebelwuerfel, nachleuchten, bilder_rendern, FONT_MONO)

leeren()
s = eevee(int(os.environ.get("BREITE", 2560)), int(os.environ.get("HOEHE", 1440)), int(os.environ.get("TAA", 24)))
s.eevee.volumetric_end = 150
BILDER = 264
s.frame_start, s.frame_end = 1, BILDER
rnd = random.Random(3)
welt(hex_farbe("#0c1630"), 1.0)

# Nasser Asphalt
asphalt = bpy.data.materials.new("Asphalt")
asphalt.use_nodes = True
an, al = asphalt.node_tree.nodes, asphalt.node_tree.links
ab = an["Principled BSDF"]
ab.inputs["Base Color"].default_value = (*hex_farbe("#0b0d12"), 1)
pfuetzen = an.new("ShaderNodeTexNoise"); pfuetzen.inputs["Scale"].default_value = 0.6
rr = an.new("ShaderNodeMapRange"); rr.inputs["From Min"].default_value = 0.45; rr.inputs["From Max"].default_value = 0.6
rr.inputs["To Min"].default_value = 0.55; rr.inputs["To Max"].default_value = 0.04
al.new(pfuetzen.outputs["Fac"], rr.inputs["Value"]); al.new(rr.outputs["Result"], ab.inputs["Roughness"])
quader("Strasse", (300, 60, 0.2), (0, 10, -0.1), asphalt)
weiss = material("Markierung", hex_farbe("#d8dde5"), rauheit=0.6)
for k in range(-12, 13):
    quader("Strich", (3, 0.25, 0.02), (k * 6, -3.0, 0.01), weiss)
quader("Bordstein", (300, 0.5, 0.3), (0, 6.5, 0.15), material("Bordstein", hex_farbe("#2a2d33"), rauheit=0.8))

# Hintergrund: Stadtlichter in der Ferne
fenster_licht = material("Fernlicht", hex_farbe("#ffb35c"), emission=hex_farbe("#ffb35c"), staerke=4)
dunkel = material("Fassade", hex_farbe("#07090e"), rauheit=0.9)
for k in range(40):
    x = -120 + k * 6 + rnd.uniform(-2, 2)
    if abs(x) < 26:
        continue
    h = rnd.uniform(8, 30)
    quader("Haus", (5, 4, h), (x, 40 + rnd.uniform(0, 10), h / 2), dunkel)
    for j in range(int(h / 2.5)):
        if rnd.random() < 0.35:
            quader("Fenster", (0.8, 0.1, 0.8), (x + rnd.uniform(-1.8, 1.8), 37.9, 1.5 + j * 2.5), fenster_licht)

# Laternen
for x in (-30, -10, 10, 30):
    quader("Mast", (0.15, 0.15, 6), (x, 7.5, 3), dunkel)
    l = licht("POINT", (x, 7, 6.2), 9000, hex_farbe("#ffcf8a"))
    l.data.shadow_soft_size = 0.4
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(x, 7, 6.1))
    bpy.context.object.data.materials.append(material("Lampe", hex_farbe("#ffd9a0"), emission=hex_farbe("#ffcf8a"), staerke=30))

# ---------------------------------------------------------------- Bastionswuerfel (faehrt nach links)
wagen = bpy.data.objects.new("Wagen", None)
s.collection.objects.link(wagen)
grau = material("Panzergrau", hex_farbe("#3c4149"), metall=0.6, rauheit=0.35)
gelb = material("Delivery-Gelb", hex_farbe("#ffd400"), rauheit=0.4)
glas = material("Kabinenglas", hex_farbe("#7fb0ff"), metall=0.2, rauheit=0.05)
reifen = material("Reifen", hex_farbe("#121317"), rauheit=0.8)


def teil(o):
    o.parent = wagen
    return o


teil(quader("Koerper", (4.6, 3.8, 3.8), (0, 0, 2.45), grau, fase=0.18))
teil(quader("Streifen", (4.65, 3.85, 0.45), (0, 0, 1.55), gelb))
teil(quader("Dachpanzer", (3.4, 3.4, 0.4), (0, 0, 4.55), grau, fase=0.08))
teil(quader("Schuerze", (5.0, 4.0, 0.6), (0, 0, 0.85), material("Schuerze", hex_farbe("#33373e"), metall=0.5, rauheit=0.5), fase=0.1))
teil(quader("Fenster", (0.1, 2.6, 1.1), (-2.31, 0, 3.4), glas))
for y in (-1.95, 1.95):
    for x in (-1.5, 1.5):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.75, depth=0.6, location=(x, y, 0.75), rotation=(math.radians(90), 0, 0))
        r = bpy.context.object
        r.data.materials.append(reifen)
        teil(r)
for y in (-1.3, 1.3):  # Scheinwerfer
    teil(quader("Scheinwerfer", (0.1, 0.5, 0.3), (-2.33, y, 1.95), material("Frontlicht", hex_farbe("#ffffff"), emission=hex_farbe("#fff4d6"), staerke=30)))
    sp = licht("SPOT", (-2.4, y, 1.95), 4000, hex_farbe("#fff4d6"), winkel=40)
    sp.rotation_euler = (0, math.radians(-90), 0)
    teil(sp)
teil(quader("Pfeil", (0.05, 1.2, 0.5), (0, -1.93, 2.9), gelb)).location = (0, -1.93, 2.9)
for y in (-1.93,):
    t = text3d("BDW-B", (0.6, y - 0.02, 2.3), 0.45, gelb, tiefe=0.01)
    teil(t)
# Hecktueren (rechts, +X), drehen um senkrechte Achsen an den Kanten
tueren = []
for seite in (-1, 1):
    angel = bpy.data.objects.new("Angel", None)
    s.collection.objects.link(angel)
    angel.parent = wagen
    angel.location = (2.31, seite * 1.85, 2.45)
    tuer = quader("Hecktuer", (0.12, 1.84, 3.5), (0, -seite * 0.92, 0), grau)
    tuer.parent = angel
    tueren.append((angel, seite))
innen = material("Laderaum", hex_farbe("#1b2a55"), emission=hex_farbe("#3a6cff"), staerke=1.2)
teil(quader("Laderaum", (0.05, 3.5, 3.4), (2.26, 0, 2.45), innen))

ANKUNFT, AUF, ZU, WEG = 92, 104, 196, 214
schluessel(wagen, "location", [(1, (60, 0, 0)), (40, (60, 0, 0)), (ANKUNFT, (0, 0, 0)), (WEG, (0, 0, 0)), (BILDER, (-55, 0, 0))])
fc = [f for f in wagen.animation_data.action.fcurves if f.array_index == 0][0]
for k in fc.keyframe_points:
    k.interpolation = "BEZIER"
for angel, seite in tueren:
    schluessel(angel, "rotation_euler", [(AUF, 0.0), (AUF + 10, math.radians(-seite * 105)), (ZU, math.radians(-seite * 105)),
                                         (ZU + 10, 0.0)], index=2)

# ---------------------------------------------------------------- Fenster fliegen ein
def fenster_bauen(farbe):
    leer = bpy.data.objects.new("Fensterflug", None)
    s.collection.objects.link(leer)
    rand = material(f"Fensterrand{farbe}", hex_farbe("#1a2029"), emission=hex_farbe(farbe), staerke=0.6)
    flaeche = material(f"Fensterinhalt{farbe}", hex_farbe("#232a35"), emission=hex_farbe("#2a3445"), staerke=0.8)
    a = quader("Fensterkoerper", (2.4, 0.05, 1.6), (0, 0, 0), flaeche)
    b = quader("Titelleiste", (2.4, 0.06, 0.25), (0, 0, 0.68), rand)
    for i in range(3):
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.07, depth=0.08, location=(0.8 + i * 0.18, -0.05, 0.68),
                                            rotation=(math.radians(90), 0, 0))
        k = bpy.context.object
        k.data.materials.append(material("Mutter", hex_farbe("#e8ecf2"), emission=hex_farbe("#e8ecf2"), staerke=2))
        k.parent = leer
    for o in (a, b):
        o.parent = leer
    return leer


ziel = (2.6, 0, 2.6)
starts = [(-6, -6, 6), (8, -7, 7.5), (-2, -8, 8.5), (10, -5, 4.5)]
for i, (start, farbe) in enumerate(zip(starts, ("#378add", "#ffd400", "#4be38b", "#ff8a3d"))):
    f = fenster_bauen(farbe)
    a = 116 + i * 18
    sichtbar(f, 1, a + 26)
    schluessel(f, "location", [(1, start), (a, start), (a + 24, ziel)])
    schluessel(f, "scale", [(a, (1, 1, 1)), (a + 24, (0.15, 0.15, 0.15))])
    schluessel(f, "rotation_euler", [(a, (0, 0, math.radians(rnd.uniform(-20, 20)))), (a + 24, (0, 0, math.radians(90)))])

# ---------------------------------------------------------------- Kamera und Statuskette
cam = bpy.data.objects.new("Kamera", bpy.data.cameras.new("Kamera"))
s.collection.objects.link(cam)
cam.data.lens = 32
s.camera = cam
schluessel(cam, "location", [(1, (7, -15, 2.6)), (BILDER, (3, -14, 2.4))])
schluessel(cam, "rotation_euler", [(1, (math.radians(86), 0, math.radians(20))), (ANKUNFT, (math.radians(86), 0, math.radians(14))),
                                   (WEG, (math.radians(86), 0, math.radians(14))), (BILDER, (math.radians(86), 0, math.radians(-6)))])

STATUS = [("ABMELDUNG ANGENOMMEN", 1), ("GESUCHT", 22), ("GEFUNDEN", 40), ("UNTERWEGS", 56), ("FAST DA", 74), ("STEHT VOR DIR", ANKUNFT)]
hud = bpy.data.objects.new("HUD", None)
s.collection.objects.link(hud)
hud.parent = cam
hud.location = (0.08, -0.5, -2.0)
hud.rotation_euler = (0, 0, 0)
gelb_hud = material("HUDgelb", hex_farbe("#ffd400"), emission=hex_farbe("#ffd400"), staerke=4)
blau_hud = material("HUDblau", hex_farbe("#2b50c8"), emission=hex_farbe("#2b50c8"), staerke=2)
weiss_hud = material("HUDweiss", hex_farbe("#e8ecf2"), emission=hex_farbe("#e8ecf2"), staerke=2)
for i, (name, ab_bild) in enumerate(STATUS):
    x = -0.55 + i * 0.22
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.022, fill_type="NGON", location=(x, 0, 0))
    leer = bpy.context.object
    leer.data.materials.append(blau_hud)
    leer.parent = hud
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.026, fill_type="NGON", location=(x, 0, 0.001))
    voll = bpy.context.object
    voll.data.materials.append(gelb_hud)
    voll.parent = hud
    sichtbar(voll, ab_bild, BILDER)
    naechstes = STATUS[i + 1][1] - 1 if i + 1 < len(STATUS) else 111
    t = text3d(name, (-0.57, 0.05, 0), 0.05, weiss_hud, rotation=(0, 0, 0), tiefe=0.0, mitte=False, schrift=FONT_MONO)
    t.parent = hud
    sichtbar(t, ab_bild, naechstes)
    if i < len(STATUS) - 1:
        strich = quader("Kette", (0.17, 0.005, 0.006), (x + 0.11, 0, 0), blau_hud)
        strich.parent = hud
for i, (name, a, b) in enumerate((("FENSTER WERDEN VERLADEN", 112, ZU), ("ABFAHRT", ZU + 1, BILDER))):
    t = text3d(name, (-0.57, 0.05, 0), 0.05, gelb_hud, rotation=(0, 0, 0), tiefe=0.0, mitte=False, schrift=FONT_MONO)
    t.parent = hud
    sichtbar(t, a, b)

licht("SUN", (0, 0, 30), 0.6, hex_farbe("#7fa0ff"), ziel=(5, 10, 0), winkel=2)
licht("AREA", (0, -6, 9), 3500, hex_farbe("#cfdcff"), groesse=10, ziel=(0, 0, 0))
licht("AREA", (6, -4, 3), 2500, hex_farbe("#ffd27a"), groesse=4, ziel=(2, 0, 2))
nebelwuerfel((300, 100, 25), (0, 20, 12), 0.004, hex_farbe("#8fa6d0"))
nachleuchten(schwelle=0.85, groesse=7, mix=-0.5)
bilder_rendern()
