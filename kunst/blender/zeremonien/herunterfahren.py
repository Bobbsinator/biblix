"""Zeremonie „Herunterfahren“: Monatsabschluss in der Zugriffshalle der Bibi Budget Bank.

Nacht, nur eine grüne Bankerlampe brennt (Masterbrief, Kapitel BBB 5). Die Fallblatt-Tafel klappert ein
letztes Mal zu SITZUNG GESCHLOSSEN, das Hauptbuch klappt zu, der Messingstempel saust herunter:
ZUR KENNTNIS GENOMMEN. Die Lampe geht aus.

  blender -b --factory-startup -P herunterfahren.py -- ausgabe/bild_
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
from hilfen import (leeren, eevee, material, hex_farbe, quader, licht, welt, text3d, schluessel,  # noqa: E402
                    sichtbar, nebelwuerfel, nachleuchten, bilder_rendern, FONT_MONO)

leeren()
s = eevee(int(os.environ.get("BREITE", 2560)), int(os.environ.get("HOEHE", 1440)), int(os.environ.get("TAA", 24)))
s.eevee.volumetric_end = 40
BILDER = 240
s.frame_start, s.frame_end = 1, BILDER
welt(hex_farbe("#010302"), 1.0)

holz = material("Holz", hex_farbe("#3a2010"), rauheit=0.35)
holz_hell = material("HolzHell", hex_farbe("#4e2c14"), rauheit=0.3)
messing = material("Messing", hex_farbe("#c9a227"), metall=1.0, rauheit=0.22)
gruen = material("Bankergruen", hex_farbe("#1f7a46"), rauheit=0.18)
leder = material("Leder", hex_farbe("#5a2012"), rauheit=0.45)
papier = material("Papier", hex_farbe("#efe6cf"), rauheit=0.8)
tinte = material("Tinte", hex_farbe("#1b1b1b"), rauheit=0.6)
marmor_s = material("MarmorSchwarz", hex_farbe("#0e0e0e"), rauheit=0.12)
marmor_w = material("MarmorWeiss", hex_farbe("#d9d4ca"), rauheit=0.12)

# Boden im Schachbrett, Schreibtisch
for i in range(-6, 7):
    for j in range(-2, 9):
        quader("Fliese", (2, 2, 0.1), (i * 2, j * 2, -0.05), marmor_s if (i + j) % 2 else marmor_w)
quader("Tischplatte", (6, 3, 0.14), (0, 0, 2.0), holz_hell, fase=0.03)
quader("Tischkorpus", (5.8, 2.8, 1.95), (0, 0.1, 0.98), holz)
quader("Schreibunterlage", (3.0, 1.9, 0.02), (0, -0.1, 2.08), material("Filz", hex_farbe("#183b2a"), rauheit=0.9))

# Bankerlampe
lampe = bpy.data.objects.new("Lampe", None)
s.collection.objects.link(lampe)
lampe.location = (-1.6, 0.6, 2.07)
bpy.ops.mesh.primitive_cylinder_add(radius=0.28, depth=0.06, location=(0, 0, 0.03))
fuss = bpy.context.object; fuss.data.materials.append(messing); fuss.parent = lampe
bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.75, location=(0, 0, 0.4))
st = bpy.context.object; st.data.materials.append(messing); st.parent = lampe
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.2, depth=0.9, location=(0.3, 0, 0.82), rotation=(0, math.radians(90), 0))
schirm = bpy.context.object
schirm.scale = (1.0, 1.25, 1.0)
schirm.data.materials.append(gruen)
schirm.parent = lampe
glut = material("Gluehbirne", hex_farbe("#ffe6a0"), emission=hex_farbe("#ffd27a"), staerke=40)
bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.7, location=(0.3, 0, 0.62), rotation=(0, math.radians(90), 0))
birne = bpy.context.object; birne.data.materials.append(glut); birne.parent = lampe
licht_lampe = licht("SPOT", (-1.3, 0.5, 2.85), 2200, hex_farbe("#ffd9a0"), ziel=(0.2, -0.3, 2.0), winkel=120)
licht_lampe.data.shadow_soft_size = 0.2
schein = licht("POINT", (-1.6, 0.4, 2.9), 200, hex_farbe("#7fe0a8"))
deckenlicht = licht("AREA", (0, -0.5, 5.5), 90, hex_farbe("#ffcf8a"), groesse=3, ziel=(0, -0.2, 2))
AUS = 218
for o, an in ((licht_lampe.data, 2200), (schein.data, 200), (deckenlicht.data, 90)):
    for f, v in ((1, an), (AUS, an), (AUS + 1, an * 0.15), (AUS + 3, an * 0.7), (AUS + 5, 0.0), (BILDER, 0.0)):
        o.energy = v
        o.keyframe_insert("energy", frame=f)
gs = glut.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, v in ((1, 40), (AUS, 40), (AUS + 1, 6), (AUS + 3, 28), (AUS + 5, 0), (BILDER, 0)):
    gs.default_value = v
    gs.keyframe_insert("default_value", frame=f)

# Rechenmaschine Nr. 1
quader("Rechenmaschine", (1.0, 0.8, 0.45), (1.9, 0.6, 2.3), material("Gusseisen", hex_farbe("#1e1f22"), metall=0.6, rauheit=0.4), fase=0.06)
quader("Plakette", (0.4, 0.02, 0.15), (1.9, 0.19, 2.35), messing)
text3d("Nr. 1", (1.9, 0.17, 2.35), 0.09, tinte, tiefe=0.002)
bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.5, location=(2.5, 0.6, 2.4), rotation=(0, math.radians(90), 0))
bpy.context.object.data.materials.append(messing)

# Hauptbuch: Deckel klappt zu
quader("Buchruecken", (2.0, 1.3, 0.12), (0, -0.2, 2.15), leder, fase=0.02)
quader("Seiten", (1.92, 1.22, 0.06), (0, -0.2, 2.23), papier)
for k in range(9):
    quader("Zeile", (1.6, 0.012, 0.004), (0, -0.7 + k * 0.12, 2.262), tinte)
gelenk = bpy.data.objects.new("Buchgelenk", None)
s.collection.objects.link(gelenk)
gelenk.location = (-1.0, -0.2, 2.24)
deckel = quader("Buchdeckel", (2.0, 1.3, 0.05), (1.0, 0, 0), leder, fase=0.015)
deckel.parent = gelenk
schluessel(gelenk, "rotation_euler", [(1, math.radians(178)), (120, math.radians(178)), (138, 0.0)], index=1)
quader("Goldkante", (1.6, 0.03, 0.002), (1.0, 0.5, 0.027), messing).parent = deckel
text3d("HAUPTBUCH", (1.0, 0.0, 0.03), 0.16, messing, rotation=(0, 0, 0), tiefe=0.002).parent = deckel

# Stempel saust herunter
stempel = bpy.data.objects.new("Stempel", None)
s.collection.objects.link(stempel)
bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.45, location=(0, 0, 0.5))
griff = bpy.context.object; griff.data.materials.append(holz_hell); griff.parent = stempel
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 0.82))
k2 = bpy.context.object; k2.data.materials.append(holz_hell); k2.parent = stempel
quader("Stempelplatte", (0.7, 0.4, 0.12), (0, 0, 0.22), messing).parent = stempel
quader("Gummi", (0.66, 0.36, 0.05), (0, 0, 0.14), material("Gummi", hex_farbe("#6b1414"), rauheit=0.7)).parent = stempel
STEMPEL = 168
schluessel(stempel, "location", [(1, (0.35, -0.2, 4.6)), (150, (0.35, -0.2, 4.6)), (STEMPEL - 2, (0.35, -0.2, 3.4)),
                                 (STEMPEL, (0.35, -0.2, 2.17)), (STEMPEL + 10, (0.35, -0.2, 2.17)), (STEMPEL + 24, (1.2, 0.2, 3.6))])
stempelrot = material("Stempelfarbe", hex_farbe("#d81a26"), rauheit=0.6, emission=hex_farbe("#ff2a2a"), staerke=0.6)
for i, z in enumerate(("ZUR KENNTNIS", "GENOMMEN.")):
    t = text3d(z, (0.35, -0.2 - i * 0.14 + 0.07, 2.277), 0.11, stempelrot, rotation=(0, 0, math.radians(-6)), tiefe=0.001)
    sichtbar(t, STEMPEL, BILDER)
rahmen = quader("Stempelrahmen", (0.74, 0.38, 0.001), (0.35, -0.2, 2.2765), stempelrot)
rahmen.rotation_euler = (0, 0, math.radians(-6))
loch = quader("StempelLoch", (0.7, 0.34, 0.0012), (0.35, -0.2, 2.2768), leder)
loch.rotation_euler = (0, 0, math.radians(-6))
for o in (rahmen, loch):
    sichtbar(o, STEMPEL, BILDER)

# Fallblatt-Tafel im Hintergrund
tafel_y = 9
quader("Tafel", (12, 0.4, 2.6), (0, tafel_y, 4.6), material("Tafelschwarz", hex_farbe("#0a0a0a"), rauheit=0.5))
quader("Tafelrahmen", (12.4, 0.3, 3.0), (0, tafel_y + 0.1, 4.6), messing)
creme = material("Fallblattschrift", hex_farbe("#f3e9cf"), emission=hex_farbe("#f3e9cf"), staerke=1.8)
ZEILEN = [("SITZUNG", "GESCHLOSSEN"), ("ZUGRIFF", "GEZÄHLT"), ("STAND", "HEUTE ABEND")]
ZUFALL = ["XQ7·MR", "4B·Z9K", "PL2·EW", "9S·KAV"]
for zi, (links, rechts) in enumerate(ZEILEN):
    z = 5.5 - zi * 0.85
    for k, wort in enumerate(ZUFALL):
        a = 20 + k * 8 + zi * 6
        t = text3d(wort + "   " + ZUFALL[(k + 1) % 4] + ZUFALL[(k + 2) % 4], (0, tafel_y - 0.22, z), 0.5, creme, tiefe=0.01, schrift=FONT_MONO)
        sichtbar(t, a, a + 7)
    t = text3d(f"{links:<9}{rechts:>13}", (0, tafel_y - 0.22, z), 0.5, creme, tiefe=0.01, schrift=FONT_MONO)
    sichtbar(t, 52 + zi * 6, BILDER)

# Kamera: langsamer Schwenk von der Tafel auf den Schreibtisch
cam = bpy.data.objects.new("Kamera", bpy.data.cameras.new("Kamera"))
s.collection.objects.link(cam)
cam.data.lens = 35
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 2.2
fokus = bpy.data.objects.new("Fokus", None)
s.collection.objects.link(fokus)
cam.data.dof.focus_object = fokus
schluessel(fokus, "location", [(1, (0, tafel_y, 4.6)), (80, (0, tafel_y, 4.6)), (115, (0.2, -0.2, 2.2))])
s.camera = cam
schluessel(cam, "location", [(1, (0.6, -5.5, 3.4)), (80, (0.5, -5.0, 3.4)), (118, (0.3, -3.0, 3.9)), (BILDER, (0.3, -2.6, 3.7))])
schluessel(cam, "rotation_euler", [(1, (math.radians(86), 0, 0)), (80, (math.radians(86), 0, 0)),
                                   (118, (math.radians(55), 0, 0)), (BILDER, (math.radians(54), 0, 0))])

licht("SUN", (0, 0, 20), 0.25, hex_farbe("#6f8fbf"), ziel=(1, 2, 0), winkel=3)
licht("SPOT", (0, tafel_y - 3, 8), 300, hex_farbe("#ffe2a0"), ziel=(0, tafel_y, 4.6), winkel=60)
nebelwuerfel((30, 26, 10), (0, 4, 5), 0.02, hex_farbe("#a0b8a8"))
nachleuchten(schwelle=0.9, groesse=7, mix=-0.45)
bilder_rendern()
