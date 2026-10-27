"""Zeremonie „Anmelden“: die Keynote. Bibi Tech enthüllt deinen Desktop.

Dunkler Saal, Nebel, Scheinwerfer, Countdown, der Claim von Bibi Tech (Masterbrief 8.1), Enthüllung,
Budgetzähler 80 → 240 Mio (Saldo-Statistik, Masterbrief 8.4), Stempel GENEHMIGT., Konfetti.

  blender -b --factory-startup -P keynote.py -- ausgabe/bild_
"""
import math
import os
import random
import subprocess
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, ".."))
import bpy  # noqa: E402
from hilfen import (leeren, eevee, material, hex_farbe, quader, licht, welt, text3d, schluessel,  # noqa: E402
                    sichtbar, nebelwuerfel, nachleuchten, bilder_rendern, FONT_MONO)

REPO = os.path.abspath(os.path.join(HIER, "..", "..", ".."))
TEXTUR = os.path.join(REPO, "kunst", "ausgabe", "texturen", "desktop.png")
if not os.path.exists(TEXTUR):  # Desktop-Bild: Tower-Schnitt aus Biblix Design
    os.makedirs(os.path.dirname(TEXTUR), exist_ok=True)
    lib = os.path.join(REPO, "pakete", "biblix-design", "usr", "share", "biblix", "design", "lib")
    subprocess.run(["python3", "-c", f"import sys; sys.path.insert(0, {lib!r}); from biblix_design import standorte; "
                    f"open({TEXTUR + '.svg'!r}, 'w').write(standorte.tower_schnitt())"], check=True)
    subprocess.run(["rsvg-convert", "-w", "1920", "-h", "1080", "-o", TEXTUR, TEXTUR + ".svg"], check=True)

leeren()
s = eevee(int(os.environ.get("BREITE", 2560)), int(os.environ.get("HOEHE", 1440)), int(os.environ.get("TAA", 24)))
s.eevee.volumetric_end = 120
BILDER = 288
s.frame_start, s.frame_end = 1, BILDER
welt(hex_farbe("#010205"), 1.0)

# Buehne und Saal
boden = bpy.data.materials.new("Buehnenboden")
boden.use_nodes = True
bb = boden.node_tree.nodes["Principled BSDF"]
bb.inputs["Base Color"].default_value = (*hex_farbe("#06080c"), 1)
bb.inputs["Roughness"].default_value = 0.12
quader("Boden", (120, 120, 1), (0, 0, -0.5), boden)
quader("Buehne", (40, 14, 1.2), (0, 14, 0.6), boden)
quader("Rueckwand", (80, 1, 40), (0, 26, 20), material("Wand", hex_farbe("#030407"), rauheit=0.9))

# Leinwand (Direct-View-Wand) mit wechselndem Inhalt
schirm_mat = bpy.data.materials.new("Leinwand")
schirm_mat.use_nodes = True
sn, sl = schirm_mat.node_tree.nodes, schirm_mat.node_tree.links
sb = sn["Principled BSDF"]
bild = sn.new("ShaderNodeTexImage")
bild.image = bpy.data.images.load(TEXTUR)
sb.inputs["Base Color"].default_value = (0, 0, 0, 1)
sl.new(bild.outputs["Color"], sb.inputs["Emission Color"])
staerke = sb.inputs["Emission Strength"]
for f, v in ((1, 0.0), (178, 0.0), (186, 1.6), (BILDER, 1.6)):
    staerke.default_value = v
    staerke.keyframe_insert("default_value", frame=f)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 22, 11), rotation=(math.radians(90), 0, 0))
schirm = bpy.context.object
schirm.scale = (32, 18, 1)
schirm.data.materials.append(schirm_mat)
rahmen = material("Rahmen", hex_farbe("#15181c"), metall=0.7, rauheit=0.3)
quader("Rahmen", (33, 0.6, 19), (0, 22.4, 11), rahmen)

weiss = material("Weisslicht", hex_farbe("#ffffff"), emission=hex_farbe("#ffffff"), staerke=6)
gelb = material("Gelblicht", hex_farbe("#ffd400"), emission=hex_farbe("#ffd400"), staerke=6)
rot = material("Stempelrot", hex_farbe("#e0242e"), emission=hex_farbe("#ff2a2a"), staerke=5)

# Countdown 3 – 2 – 1
for i, z in enumerate(("3", "2", "1")):
    t = text3d(z, (0, 21.6, 11), 10, weiss, tiefe=0.1)
    a = 52 + i * 24
    sichtbar(t, a, a + 20)
    schluessel(t, "scale", [(a, (1.25, 1.25, 1.25)), (a + 20, (0.9, 0.9, 0.9))])
# Claim
c1 = text3d("WIR ENTWICKELN, WAS MÖGLICH IST.", (0, 21.6, 12.6), 1.9, weiss, tiefe=0.05)
c2 = text3d("NICHT, WAS NÖTIG IST.", (0, 21.6, 9.6), 1.9, gelb, tiefe=0.05)
sichtbar(c1, 128, 176)
sichtbar(c2, 146, 176)
# Enthuellung
titel = text3d("DEIN DESKTOP", (0, 21.4, 21.5), 2.2, weiss, tiefe=0.05)
sichtbar(titel, 186, BILDER)
for i, betrag in enumerate(("80 MIO", "120 MIO", "160 MIO", "200 MIO", "240 MIO")):
    t = text3d("BUDGET: " + betrag, (0, 20.0, 1.9), 1.3, gelb, tiefe=0.05, schrift=FONT_MONO)
    a = 196 + i * 7
    sichtbar(t, a, a + 6 if i < 4 else BILDER)
stempel = text3d("GENEHMIGT.", (0, 20.8, 11), 4.2, rot, tiefe=0.3)
stempel.rotation_euler = (math.radians(90), math.radians(-8), 0)
sichtbar(stempel, 232, BILDER)
schluessel(stempel, "scale", [(232, (3.0, 3.0, 3.0)), (237, (0.92, 0.92, 0.92)), (241, (1.0, 1.0, 1.0))])
stempelrahmen = quader("Stempelrahmen", (30, 0.1, 7), (0, 20.9, 11), rot)
stempelrahmen.rotation_euler = (0, math.radians(-8), 0)
stempelrahmen.parent = None
innen = quader("StempelInnen", (29.0, 0.12, 6.0), (0, 20.85, 11), material("Schirmdunkel", hex_farbe("#020205")))
innen.rotation_euler = (0, math.radians(-8), 0)
for o in (stempelrahmen, innen):
    sichtbar(o, 232, BILDER)
    schluessel(o, "scale", [(232, (3.0, 1, 3.0)), (237, (0.92, 1, 0.92)), (241, (1.0, 1, 1.0))])

# Scheinwerfer an der Decke, die schwenken
rnd = random.Random(8)
for k in range(8):
    x = -28 + k * 8
    sp = licht("SPOT", (x, 6, 26), 0.0, hex_farbe("#dbe8ff") if k % 2 else hex_farbe("#ffd27a"), winkel=14)
    sp.data.spot_blend = 0.3
    sp.data.shadow_soft_size = 0.2
    for f, v in ((1, 0.0), (10, 2.2e5), (BILDER, 2.6e5)):
        sp.data.energy = v
        sp.data.keyframe_insert("energy", frame=f)
    werte = []
    for f in range(1, BILDER + 1, 36):
        werte.append((f, (math.radians(rnd.uniform(-35, 35)), math.radians(rnd.uniform(-25, 25)), 0)))
    werte.append((230, (math.radians(-28), math.radians(-x * 0.9), 0)))  # alle auf die Mitte
    werte.append((BILDER, (math.radians(-28), math.radians(-x * 0.9), 0)))
    schluessel(sp, "rotation_euler", sorted(werte, key=lambda w: w[0]))
# Konfetti
konfetti_mats = [material(f"Konfetti{i}", hex_farbe(c), metall=0.6, rauheit=0.3, emission=hex_farbe(c), staerke=1.5)
                 for i, c in enumerate(("#ffd400", "#378add", "#ffffff", "#e0242e"))]
stuecke = bpy.data.collections.new("Konfetti")
s.collection.children.link(stuecke)
for i, m in enumerate(konfetti_mats):
    bpy.ops.mesh.primitive_plane_add(size=0.35, location=(0, 0, -30))
    o = bpy.context.object
    o.data.materials.append(m)
    bpy.context.collection.objects.unlink(o)
    stuecke.objects.link(o)
stuecke.hide_render = False
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 8, 24))
kanone = bpy.context.object
kanone.show_instancer_for_render = False
ps = kanone.modifiers.new("Konfetti", "PARTICLE_SYSTEM").particle_system.settings
ps.count = 2500
ps.frame_start, ps.frame_end = 234, 244
ps.lifetime = 120
ps.normal_factor = -2.0
ps.factor_random = 4.0
ps.effector_weights.gravity = 0.25
ps.render_type = "COLLECTION"
ps.instance_collection = stuecke
ps.use_collection_pick_random = True
ps.particle_size = 1.0
ps.size_random = 0.5
ps.use_rotations = True
ps.rotation_factor_random = 1.0
ps.angular_velocity_mode = "RAND"
ps.angular_velocity_factor = 8.0

# Kamera: langsame Fahrt auf die Buehne zu
cam = bpy.data.objects.new("Kamera", bpy.data.cameras.new("Kamera"))
s.collection.objects.link(cam)
cam.data.lens = 28
s.camera = cam
schluessel(cam, "location", [(1, (0, -36, 5)), (BILDER, (0, -22, 8.5))])
schluessel(cam, "rotation_euler", [(1, (math.radians(88), 0, 0)), (BILDER, (math.radians(91), 0, 0))])

nebelwuerfel((90, 70, 30), (0, 0, 15), 0.012, hex_farbe("#b9c6dc"))
nachleuchten(schwelle=0.85, groesse=8, mix=-0.4)
bilder_rendern()
