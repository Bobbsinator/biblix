"""Gemeinsame Blender-Hilfen fuer Biblix-Bilder und -Videos (Blender 4.3)."""
import math
import sys

import bpy


def leeren():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def ausgabe():
    argv = sys.argv
    return argv[argv.index("--") + 1] if "--" in argv else "/tmp/probe.png"


def einstellungen(breite=1920, hoehe=1080, samples=96, belichtung=0.0, look="AgX - Medium High Contrast"):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.samples = samples
    s.cycles.use_denoising = False  # Debian-Blender hat kein OpenImageDenoise
    s.cycles.max_bounces = 6
    s.render.resolution_x, s.render.resolution_y = breite, hoehe
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = "PNG"
    s.view_settings.view_transform = "AgX"
    try:
        s.view_settings.look = look
    except TypeError:
        pass
    s.view_settings.exposure = belichtung
    s.render.threads_mode = "AUTO"


def material(name, farbe=(0.8, 0.8, 0.8), metall=0.0, rauheit=0.5, emission=None, staerke=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*farbe, 1)
    b.inputs["Metallic"].default_value = metall
    b.inputs["Roughness"].default_value = rauheit
    if emission:
        b.inputs["Emission Color"].default_value = (*emission, 1)
        b.inputs["Emission Strength"].default_value = staerke
    return m


def hex_farbe(h):
    """sRGB-Hex in lineare Farbe (wie Blender sie erwartet)."""
    h = h.lstrip("#")
    lin = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        lin.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(lin)


def quader(name, groesse, ort, mat=None, fase=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=ort)
    o = bpy.context.object
    o.name = name
    o.scale = groesse
    bpy.ops.object.transform_apply(scale=True)
    if fase:
        mod = o.modifiers.new("Fase", "BEVEL")
        mod.width = fase
        mod.segments = 3
    if mat:
        o.data.materials.append(mat)
    return o


def kamera(ort, ziel, brennweite=35, blende=None, fokus=None):
    from mathutils import Vector
    cam = bpy.data.cameras.new("Kamera")
    cam.lens = brennweite
    o = bpy.data.objects.new("Kamera", cam)
    bpy.context.collection.objects.link(o)
    o.location = ort
    richtung = Vector(ziel) - Vector(ort)
    o.rotation_euler = richtung.to_track_quat("-Z", "Y").to_euler()
    if blende:
        cam.dof.use_dof = True
        cam.dof.aperture_fstop = blende
        cam.dof.focus_distance = fokus or richtung.length
    bpy.context.scene.camera = o
    return o


def licht(art, ort, energie, farbe=(1, 1, 1), groesse=1.0, ziel=None, winkel=None):
    from mathutils import Vector
    l = bpy.data.lights.new(art, art)
    l.energy = energie
    l.color = farbe
    if art == "AREA":
        l.size = groesse
    if art == "SPOT" and winkel:
        l.spot_size = math.radians(winkel)
        l.spot_blend = 0.6
    if art == "SUN" and winkel is not None:
        l.angle = math.radians(winkel)
    o = bpy.data.objects.new(art, l)
    bpy.context.collection.objects.link(o)
    o.location = ort
    if ziel:
        o.rotation_euler = (Vector(ziel) - Vector(ort)).to_track_quat("-Z", "Y").to_euler()
    return o


def welt(farbe, staerke=1.0):
    w = bpy.data.worlds.new("Welt")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*farbe, 1)
    bg.inputs["Strength"].default_value = staerke
    bpy.context.scene.world = w
    return w


def nachleuchten(schwelle=1.0, groesse=7, mix=-0.6):
    """Leichtes Gluehen um helle Lichter (Kompositor, Glare Fog Glow)."""
    s = bpy.context.scene
    s.use_nodes = True
    t = s.node_tree
    for n in list(t.nodes):
        t.nodes.remove(n)
    rl = t.nodes.new("CompositorNodeRLayers")
    gl = t.nodes.new("CompositorNodeGlare")
    gl.glare_type = "FOG_GLOW"
    gl.quality = "HIGH"
    gl.threshold = schwelle
    gl.size = groesse
    gl.mix = mix
    out = t.nodes.new("CompositorNodeComposite")
    t.links.new(rl.outputs["Image"], gl.inputs["Image"])
    t.links.new(gl.outputs["Image"], out.inputs["Image"])
    s.render.use_compositing = True


def rendern():
    bpy.context.scene.render.filepath = ausgabe()
    bpy.ops.render.render(write_still=True)
