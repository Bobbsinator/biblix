"""Zeremonie „Hochfahren“: Big Bibi fährt hoch (Megaaufzug, Burgenland -8 bis 0).

Hebel auf AUF, die Plattform steigt durch den Schacht, Ebenen ziehen vorbei, oben öffnen sich die Tore.
Titelkarte kommt danach im Schnitt (zeremonien/schnitt.py). Kanon: Masterbrief 6.1 (Ebenen, Big Bibi,
Hebel AUF – HALT – AB). Alles andere ist Gestaltung.

  blender -b --factory-startup -P hochfahren.py -- ausgabe/bild_      (EINZEL=1,120 für Proben)
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
from hilfen import (leeren, eevee, material, hex_farbe, quader, licht, welt, text3d, schluessel,  # noqa: E402
                    sichtbar, nebelwuerfel, nachleuchten, bilder_rendern)

leeren()
s = eevee(int(os.environ.get("BREITE", 2560)), int(os.environ.get("HOEHE", 1440)), int(os.environ.get("TAA", 24)))
s.eevee.volumetric_end = 200
BILDER = 264          # 11 s
s.frame_start, s.frame_end = 1, BILDER
UNTEN, OBEN = -100.0, -6.0
START, STOPP = 40, 210  # Fahrt

welt(hex_farbe("#020306"), 1.0)

# ---------------------------------------------------------------- Schacht
beton = bpy.data.materials.new("Beton")
beton.use_nodes = True
bn, bl = beton.node_tree.nodes, beton.node_tree.links
bb = bn["Principled BSDF"]
rau = bn.new("ShaderNodeTexNoise"); rau.inputs["Scale"].default_value = 6.0; rau.inputs["Detail"].default_value = 8.0
rampe = bn.new("ShaderNodeValToRGB")
rampe.color_ramp.elements[0].color = (*hex_farbe("#2a2d32"), 1)
rampe.color_ramp.elements[1].color = (*hex_farbe("#4a4e55"), 1)
bl.new(rau.outputs["Fac"], rampe.inputs[0]); bl.new(rampe.outputs[0], bb.inputs["Base Color"])
bb.inputs["Roughness"].default_value = 0.85
hoeck = bn.new("ShaderNodeBump"); hoeck.inputs["Strength"].default_value = 0.4
bl.new(rau.outputs["Fac"], hoeck.inputs["Height"]); bl.new(hoeck.outputs["Normal"], bb.inputs["Normal"])

B = 16.0  # halbe Schachtbreite
for x, y, sx, sy in ((0, B, 2 * B, 1), (0, -B, 2 * B, 1), (B, 0, 1, 2 * B), (-B, 0, 1, 2 * B)):
    quader("Wand", (sx, sy, 130), (x, y, -45), beton)

# Fuehrungsschienen in Gelb-Schwarz an den Ecken
gelb = material("Signalgelb", hex_farbe("#F2C12E"), rauheit=0.5)
schwarz = material("Schwarz", hex_farbe("#15171b"), rauheit=0.6)
for sx in (-1, 1):
    for sy in (-1, 1):
        quader("Schiene", (1.2, 1.2, 130), (sx * (B - 1.2), sy * (B - 1.2), -45), gelb)

# Ebenen: Lichtband, Ebenennummer und Bezeichnung (Kanon 6.1)
EBENEN = [(-8, "ENERGIE · ÜBERLEBEN"), (-7, "FORSCHUNG"), (-6, "SPEZIAL-BIBI-SEKTOR"), (-5, "BZB"),
          (-4, "BIBI-KI · BIKZ"), (-3, "BIBI BOULEVARD"), (-2, "OBERKOMMANDO"), (-1, "FAHRZEUGE · LOGISTIK")]
lichtband = material("Lichtband", hex_farbe("#ffffff"), emission=hex_farbe("#cfe2ff"), staerke=18)
schild = material("Schildtext", hex_farbe("#F2C12E"), emission=hex_farbe("#F2C12E"), staerke=3.0)
weissschrift = material("Weissschrift", hex_farbe("#e8ecf2"), emission=hex_farbe("#e8ecf2"), staerke=1.2)
abstand = (OBEN - UNTEN) / 8.0
for k, (nr, name) in enumerate(EBENEN):
    z = UNTEN + 4 + k * abstand
    for x, y, sx, sy in ((0, B - 0.55, 2 * B - 3, 0.1), (0, -B + 0.55, 2 * B - 3, 0.1),
                         (B - 0.55, 0, 0.1, 2 * B - 3), (-B + 0.55, 0, 0.1, 2 * B - 3)):
        quader("Band", (sx, sy, 0.25), (x, y, z - 2.2), lichtband)
    text3d(str(nr), (0, B - 0.6, z + 1.8), 5.0, schild, tiefe=0.05)
    text3d(name, (0, B - 0.6, z - 0.7), 1.3, weissschrift, tiefe=0.02)
    # Tor zur Ebene (dunkle Öffnung) auf der Rückwand
    quader("Ebenentor", (14, 0.2, 5.5), (0, -B + 0.6, z + 0.5), schwarz)

# Tore oben (Ebene 0) und Licht dahinter
tor_l = quader("TorLinks", (B, 2 * B, 1.0), (-B / 2, 0, OBEN + 8), schwarz)
tor_r = quader("TorRechts", (B, 2 * B, 1.0), (B / 2, 0, OBEN + 8), schwarz)
for t in (tor_l, tor_r):
    for k in range(5):
        streifen = quader("Warnstreifen", (B * 0.9, 0.9, 1.05), (t.location.x, -B + 3 + k * 7, OBEN + 8), gelb)
        streifen.parent = t
        streifen.location = (0, -B + 3 + k * 7, 0)
OEFFNEN = 214
schluessel(tor_l, "location", [(OEFFNEN, -B / 2), (OEFFNEN + 30, -B * 1.6)], index=0)
schluessel(tor_r, "location", [(OEFFNEN, B / 2), (OEFFNEN + 30, B * 1.6)], index=0)
himmel = material("Himmel", hex_farbe("#ffffff"), emission=hex_farbe("#fff2d0"), staerke=0.0)
quader("Licht", (2 * B, 2 * B, 0.2), (0, 0, OBEN + 16), himmel)
hst = himmel.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, v in ((OEFFNEN, 0.0), (OEFFNEN + 18, 40.0), (BILDER, 80.0)):
    hst.default_value = v
    hst.keyframe_insert("default_value", frame=f)
lichtstrahl = licht("SPOT", (0, 0, OBEN + 14), 0.0, hex_farbe("#fff2d0"), ziel=(0, 0, OBEN - 20), winkel=70)
for f, v in ((OEFFNEN, 0.0), (OEFFNEN + 20, 9e5), (BILDER, 1.4e6)):
    lichtstrahl.data.energy = v
    lichtstrahl.data.keyframe_insert("energy", frame=f)

# ---------------------------------------------------------------- Plattform (faehrt mit Kamera)
plattform = bpy.data.objects.new("Plattform", None)
s.collection.objects.link(plattform)
schluessel(plattform, "location", [(1, UNTEN), (START, UNTEN), (STOPP, OBEN)], index=2)
for fc in plattform.animation_data.action.fcurves:
    for k in fc.keyframe_points:
        k.interpolation = "BEZIER"
        k.easing = "AUTO"

boden = quader("Boden", (2 * B - 4, 2 * B - 4, 0.6), (0, 0, -0.3), material("Stahlboden", hex_farbe("#3a3e45"), metall=0.8, rauheit=0.45))
boden.parent = plattform
for k in range(14):  # Warnstreifen an der Kante
    st = quader("Kante", (1.4, 0.8, 0.62), (-B + 3 + k * 2.2, -B + 2.6, -0.29), gelb if k % 2 else schwarz)
    st.parent = plattform
for x in (-B + 2.4, B - 2.4):  # Gelaender
    quader("Pfosten", (0.15, 0.15, 1.2), (x, -B + 3.5, 0.6), gelb).parent = plattform

# Hebelpult AUF – HALT – AB
pult = quader("Pult", (2.4, 0.8, 1.4), (0, 2.6, 0.7), material("Pult", hex_farbe("#2b2e33"), metall=0.4, rauheit=0.5))
pult.parent = plattform
for i, wort in enumerate(("AUF", "HALT", "AB")):
    t = text3d(wort, (-0.55, 2.19, 1.15 - i * 0.32), 0.2, weissschrift if i != 1 else schild, tiefe=0.005)
    t.parent = plattform
achse = bpy.data.objects.new("Hebelachse", None)
s.collection.objects.link(achse)
achse.parent = plattform
achse.location = (0.35, 2.15, 1.15 - 0.32)
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.35, location=(0, -0.18, 0), rotation=(math.radians(90), 0, 0))
stange = bpy.context.object
stange.data.materials.append(material("Hebelmetall", hex_farbe("#c9cdd2"), metall=1.0, rauheit=0.25))
stange.parent = achse
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=(0, -0.38, 0))
knauf = bpy.context.object
knauf.data.materials.append(material("Knauf", hex_farbe("#d7263d"), rauheit=0.3))
knauf.parent = achse
schluessel(achse, "location", [(1, 1.15 - 0.32), (16, 1.15 - 0.32), (24, 1.15 + 0.02)], index=2)
schlitz = quader("Schlitz", (0.08, 0.05, 0.8), (0.35, 2.19, 0.98), schwarz)
schlitz.parent = plattform

# Etagenanzeige am Pult (Bernstein), wechselt beim Durchfahren
bernstein = material("Bernstein", hex_farbe("#ffb020"), emission=hex_farbe("#ffb020"), staerke=6)
quader("Anzeigefenster", (1.2, 0.05, 0.5), (0, 2.19, 1.75), material("Glas", hex_farbe("#120c04"))).parent = plattform
reihen = [-8, -7, -6, -5, -4, -3, -2, -1, 0]
for i, nr in enumerate(reihen):
    a = START + int((STOPP - START) * (i / 8) ** 1.0) if i else 1
    b = START + int((STOPP - START) * ((i + 1) / 8)) - 1 if i < 8 else BILDER
    t = text3d(f"{nr:+d}" if nr else "0", (0, 2.16, 1.75), 0.38, bernstein, tiefe=0.005, schrift="/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf")
    t.parent = plattform
    sichtbar(t, a, b)

# Rundumleuchten
for x in (-B + 2.4, B - 2.4):
    dreh = bpy.data.objects.new("Rundum", None)
    s.collection.objects.link(dreh)
    dreh.parent = plattform
    dreh.location = (x, -B + 3.5, 1.35)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, 0, 0))
    kugel = bpy.context.object
    kugel.data.materials.append(material("Rundumglas", hex_farbe("#ff8a1f"), emission=hex_farbe("#ff8a1f"), staerke=12))
    kugel.parent = dreh
    l = licht("SPOT", (0, 0, 0), 2500, hex_farbe("#ff8a1f"), winkel=35)
    l.parent = dreh
    l.rotation_euler = (math.radians(90), 0, 0)
    schluessel(dreh, "rotation_euler", [(1, 0.0), (BILDER, math.radians(360 * 6))], interpolation="LINEAR", index=2)

# Arbeitslicht von oben auf der Plattform
lampe = licht("AREA", (0, 0, 9), 3500, hex_farbe("#dbe6ff"), groesse=6)
lampe.parent = plattform

# ---------------------------------------------------------------- Kamera
cam = bpy.data.objects.new("Kamera", bpy.data.cameras.new("Kamera"))
s.collection.objects.link(cam)
cam.data.lens = 24
cam.parent = plattform
cam.location = (0, -2.5, 1.75)
schluessel(cam, "rotation_euler", [(1, math.radians(84)), (30, math.radians(84)), (90, math.radians(118)),
                                   (STOPP, math.radians(128)), (BILDER, math.radians(132))], index=0)
cam.rotation_euler[2] = 0
s.camera = cam
# leichtes Ruetteln waehrend der Fahrt
if cam.animation_data and cam.animation_data.action:
    for fc in cam.animation_data.action.fcurves:
        r = fc.modifiers.new("NOISE")
        r.scale, r.strength = 3.0, 0.006
        r.use_restricted_range = True
        r.frame_start, r.frame_end = START, STOPP
        r.blend_in, r.blend_out = 10, 10

nebelwuerfel((2 * B - 2, 2 * B - 2, 130), (0, 0, -45), 0.006, hex_farbe("#9fb0c8"))
nachleuchten(schwelle=0.9, groesse=8, mix=-0.45)
bilder_rendern()
