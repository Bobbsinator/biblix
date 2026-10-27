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


FONT_FETT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def text3d(inhalt, ort, groesse, mat, rotation=(math.radians(90), 0, 0), tiefe=0.02, mitte=True, schrift=FONT_FETT):
    """3D-Text (Standard: steht aufrecht, Blick in -Y)."""
    kurve = bpy.data.curves.new("Text", "FONT")
    kurve.body = inhalt
    kurve.font = bpy.data.fonts.load(schrift, check_existing=True)
    kurve.size = groesse
    kurve.extrude = tiefe
    if mitte:
        kurve.align_x = "CENTER"
        kurve.align_y = "CENTER"
    o = bpy.data.objects.new("Text", kurve)
    bpy.context.collection.objects.link(o)
    o.location = ort
    o.rotation_euler = rotation
    if mat:
        o.data.materials.append(mat)
    return o


def schluessel(obj, pfad, werte, interpolation="BEZIER", index=-1):
    """werte: Liste (bild, wert); setzt Keyframes auf obj.pfad."""
    for bild, wert in werte:
        if index >= 0:
            getattr(obj, pfad)[index] = wert
        else:
            setattr(obj, pfad, wert)
        obj.keyframe_insert(pfad, index=index, frame=bild)
    anim = obj.animation_data or getattr(obj, "id_data", obj).animation_data
    if anim and anim.action:
        for fc in anim.action.fcurves:
            if fc.data_path == pfad:
                for k in fc.keyframe_points:
                    k.interpolation = interpolation


def sichtbar(obj, von, bis):
    """Objekt nur zwischen den Bildern von..bis zeigen (Render)."""
    for bild, an in ((1, False), (von, True), (bis + 1, False)):
        if bild < 1:
            continue
        obj.hide_render = not an
        obj.keyframe_insert("hide_render", frame=bild)
        obj.hide_viewport = not an
        obj.keyframe_insert("hide_viewport", frame=bild)
    if von <= 1:
        obj.hide_render = False
        obj.keyframe_insert("hide_render", frame=1)


def eevee(breite=2560, hoehe=1440, taa=24, fps=24):
    s = bpy.context.scene
    s.render.engine = "BLENDER_EEVEE_NEXT"
    s.eevee.taa_render_samples = taa
    s.eevee.use_raytracing = True
    s.eevee.volumetric_tile_size = "4"
    s.render.fps = fps
    s.render.resolution_x, s.render.resolution_y = breite, hoehe
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = "PNG"
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    return s


def nebelwuerfel(groesse, ort, dichte, farbe=(0.8, 0.85, 1.0)):
    m = bpy.data.materials.new("Nebel")
    m.use_nodes = True
    n = m.node_tree.nodes
    n.remove(n["Principled BSDF"])
    v = n.new("ShaderNodeVolumePrincipled")
    v.inputs["Density"].default_value = dichte
    v.inputs["Color"].default_value = (*farbe, 1)
    m.node_tree.links.new(v.outputs[0], n["Material Output"].inputs["Volume"])
    return quader("Nebel", groesse, ort, m), v


def bilder_rendern():
    """Animation als Einzelbilder nach ausgabe() (Ordner/Praefix); EINZEL=1,50 rendert nur diese."""
    import os
    s = bpy.context.scene
    ziel = ausgabe()
    einzel = os.environ.get("EINZEL")
    if einzel:
        for f in [int(x) for x in einzel.split(",")]:
            s.frame_set(f)
            s.render.filepath = f"{ziel}{f:04d}.png"
            bpy.ops.render.render(write_still=True)
    else:
        s.render.filepath = ziel
        bpy.ops.render.render(animation=True)
