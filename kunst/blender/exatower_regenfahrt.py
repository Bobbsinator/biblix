"""Kamerafahrt: einmal um den Exabibi Tower, nachts im Regen (EEVEE, nahtlose Schleife).

  blender -b --factory-startup -P exatower_regenfahrt.py -- ordner/bild_
  Umgebung: BILDER=240 BREITE=3840 HOEHE=2160 TAA=32 TROPFEN=60000, EINZEL=1,97 (nur diese Bilder)
Danach mit ffmpeg zu einem Video zusammensetzen (siehe docs/lebendige-hintergruende.md).
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix  # noqa: E402

from hilfen import leeren, hex_farbe, material, nachleuchten  # noqa: E402
from exatower_szene import aufbauen  # noqa: E402

leeren()
s = bpy.context.scene
s.render.engine = "BLENDER_EEVEE_NEXT"
s.eevee.taa_render_samples = int(os.environ.get("TAA", 32))
s.eevee.use_raytracing = True
s.eevee.volumetric_tile_size = "4"
s.eevee.volumetric_end = 400
s.view_settings.view_transform = "AgX"
s.view_settings.look = "AgX - Medium High Contrast"
s.view_settings.exposure = 0.3
s.render.fps = 24
BILDER = int(os.environ.get("BILDER", 240))
s.frame_start, s.frame_end = 1, BILDER
s.render.resolution_x = int(os.environ.get("BREITE", 1920))
s.render.resolution_y = int(os.environ.get("HOEHE", 1080))
s.render.resolution_percentage = 100
s.render.image_settings.file_format = "PNG"

aufbauen(ring=True)

# Nasser Platz um den Tower, Tropfen kraeuseln die Oberflaeche
platz = bpy.data.materials.new("NasserPlatz")
platz.use_nodes = True
pn, pl = platz.node_tree.nodes, platz.node_tree.links
pb = pn["Principled BSDF"]
pb.inputs["Base Color"].default_value = (*hex_farbe("#06080c"), 1)
pb.inputs["Roughness"].default_value = 0.06
rausch = pn.new("ShaderNodeTexNoise")
rausch.noise_dimensions = "4D"
rausch.inputs["Scale"].default_value = 18.0
bump = pn.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.12
pl.new(rausch.outputs["Fac"], bump.inputs["Height"])
pl.new(bump.outputs["Normal"], pb.inputs["Normal"])
rausch.inputs["W"].driver_add("default_value").driver.expression = "frame / 6"
bpy.ops.mesh.primitive_circle_add(vertices=96, radius=48, fill_type="NGON", location=(0, 0, 0.03))
bpy.context.object.data.materials.append(platz)
donau = bpy.data.materials["Donau"]
r2 = [n for n in donau.node_tree.nodes if n.type == "TEX_NOISE"][0]
r2.noise_dimensions = "4D"
r2.inputs["W"].driver_add("default_value").driver.expression = "frame / 8"
bpy.data.materials["Nebel"].node_tree.nodes["Principled Volume"].inputs["Density"].default_value = 0.012

# Regen: Partikel aus einer Flaeche ueber der Szene, Instanz = duenner Strich mit leichtem Wind
tropfen_mat = material("Regen", hex_farbe("#cfe0ff"), emission=hex_farbe("#bcd4ff"), staerke=0.7)
bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.014, depth=1.3, location=(0, 0, -50))
tropfen = bpy.context.object
tropfen.name = "Tropfen"
tropfen.rotation_euler = (math.radians(6), 0, 0)
bpy.ops.object.transform_apply(rotation=True)
tropfen.data.materials.append(tropfen_mat)
bpy.ops.mesh.primitive_plane_add(size=180, location=(0, 0, 60))
quelle = bpy.context.object
quelle.name = "Wolken"
ps = quelle.modifiers.new("Regen", "PARTICLE_SYSTEM").particle_system.settings
ps.count = int(os.environ.get("TROPFEN", 60000))
ps.frame_start, ps.frame_end = -80, BILDER
ps.lifetime = 60
ps.emit_from = "FACE"
ps.normal_factor = -38.0
ps.factor_random = 0.15
ps.effector_weights.gravity = 0.0
ps.render_type = "OBJECT"
ps.instance_object = tropfen
ps.particle_size = 1.0
ps.size_random = 0.4
ps.use_rotations = False
quelle.show_instancer_for_render = False

# Naeher Ring mittelhoher Haeuser und Laternen um den Platz
rnd = random.Random(7)
me = bpy.data.meshes.new("Nahring")
bm = bmesh.new()
for _ in range(70):
    a = rnd.uniform(0, 2 * math.pi)
    rr = rnd.uniform(54, 92)
    x, y = rr * math.cos(a), rr * math.sin(a)
    if -134 < y < -16:
        continue
    w, d, h = rnd.uniform(4, 9), rnd.uniform(4, 9), rnd.uniform(6, 18)
    q = bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=(w, d, h), verts=q["verts"])
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(a, 3, "Z"), verts=q["verts"])
    bmesh.ops.translate(bm, vec=(x, y, h / 2), verts=q["verts"])
bm.to_mesh(me)
bm.free()
ring = bpy.data.objects.new("Nahring", me)
s.collection.objects.link(ring)
ring.data.materials.append(bpy.data.materials["Stadt"])
laterne = material("Laterne", hex_farbe("#ffd9a0"), emission=hex_farbe("#ffcf8a"), staerke=40)
mast = material("Laternenmast", hex_farbe("#1a1d22"), metall=0.8, rauheit=0.4)
for k in range(16):
    a = k * 2 * math.pi / 16
    x, y = 30 * math.cos(a), 30 * math.sin(a)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.08, depth=4, location=(x, y, 2))
    bpy.context.object.data.materials.append(mast)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(x, y, 4.1))
    bpy.context.object.data.materials.append(laterne)
    l = bpy.data.lights.new("Lampe", "POINT")
    l.energy, l.color, l.shadow_soft_size = 180, hex_farbe("#ffcf8a"), 0.3
    lo = bpy.data.objects.new("Lampe", l)
    lo.location = (x, y, 3.9)
    s.collection.objects.link(lo)

# Blitz: der Himmel leuchtet kurz auf (Bild 97 bis 103)
hg = s.world.node_tree.nodes["Background"].inputs["Strength"]
for f, v in ((1, 1.0), (96, 1.0), (97, 5.0), (98, 1.6), (100, 4.0), (103, 1.0), (BILDER, 1.0)):
    hg.default_value = v
    hg.keyframe_insert("default_value", frame=f)
for fc in s.world.node_tree.animation_data.action.fcurves:
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"

# Kamera auf Kreisbahn, Blick zum Tower, sanftes Auf und Ab; Bild BILDER+1 = Bild 1 (Schleife)
bahn = bpy.data.objects.new("Bahn", None)
s.collection.objects.link(bahn)
ziel = bpy.data.objects.new("Ziel", None)
ziel.location = (0, 0, 25)
s.collection.objects.link(ziel)
cam = bpy.data.objects.new("Fahrt", bpy.data.cameras.new("Fahrt"))
cam.data.lens = 22
cam.data.clip_start = 7.0  # keine Riesentropfen direkt vor der Linse
s.collection.objects.link(cam)
cam.parent = bahn
spur = cam.constraints.new("TRACK_TO")
spur.target = ziel
spur.track_axis = "TRACK_NEGATIVE_Z"
spur.up_axis = "UP_Y"
s.camera = cam
for f, winkel in ((1, 0), (BILDER + 1, -360)):
    bahn.rotation_euler = (0, 0, math.radians(winkel))
    bahn.keyframe_insert("rotation_euler", index=2, frame=f)
for f, z in ((1, 7), (BILDER // 2 + 1, 16), (BILDER + 1, 7)):
    cam.location = (0, -58, z)
    cam.keyframe_insert("location", index=2, frame=f)
for fc in bahn.animation_data.action.fcurves:
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"

nachleuchten(schwelle=0.8, groesse=7, mix=-0.55)
ziel_pfad = sys.argv[sys.argv.index("--") + 1]
einzel = os.environ.get("EINZEL")
if einzel:
    for f in [int(x) for x in einzel.split(",")]:
        s.frame_set(f)
        s.render.filepath = f"{ziel_pfad}{f:04d}.png"
        bpy.ops.render.render(write_still=True)
else:
    s.render.filepath = ziel_pfad
    bpy.ops.render.render(animation=True)
