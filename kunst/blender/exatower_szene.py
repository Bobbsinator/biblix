"""Exabibi Tower bei Nacht: Szene (Tower, Stadt, Donau, Nebel, Himmel) fuer Standbild und Kamerafahrt.

Kanon (Masterbrief 8.2): 444 m, 94 Stockwerke, dunkles Glas, Silber, Blau, vertikale gelbe B-Lichtlinie.
Alles andere (Stadt, Platz, Licht) ist Gestaltung.
"""
import math
import random

import bmesh
import bpy

from hilfen import material, hex_farbe, quader, licht, welt

H = 44.4  # 444 m -> 44,4 Einheiten


def fenster_material(name, glas, licht_farbe, staerke, quote, raster=(1.2, 1.6), rauheit=0.12):
    """Glasfassade mit zufaellig beleuchteten Fenstern (prozedural, in Objektkoordinaten)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*glas, 1)
    b.inputs["Metallic"].default_value = 0.7
    b.inputs["Roughness"].default_value = rauheit
    tc = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(tc.outputs["Object"], sep.inputs[0])
    u = n.new("ShaderNodeMath"); u.operation = "ADD"
    l.new(sep.outputs[0], u.inputs[0]); l.new(sep.outputs[1], u.inputs[1])
    us = n.new("ShaderNodeMath"); us.operation = "MULTIPLY"; us.inputs[1].default_value = raster[0]
    l.new(u.outputs[0], us.inputs[0])
    zs = n.new("ShaderNodeMath"); zs.operation = "MULTIPLY"; zs.inputs[1].default_value = raster[1]
    l.new(sep.outputs[2], zs.inputs[0])

    def band(eingang, a, b_):
        fr = n.new("ShaderNodeMath"); fr.operation = "FRACT"
        l.new(eingang, fr.inputs[0])
        g = n.new("ShaderNodeMath"); g.operation = "GREATER_THAN"; g.inputs[1].default_value = a
        k = n.new("ShaderNodeMath"); k.operation = "LESS_THAN"; k.inputs[1].default_value = b_
        l.new(fr.outputs[0], g.inputs[0]); l.new(fr.outputs[0], k.inputs[0])
        mul = n.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
        l.new(g.outputs[0], mul.inputs[0]); l.new(k.outputs[0], mul.inputs[1])
        return mul.outputs[0]

    maske_u = band(us.outputs[0], 0.12, 0.88)
    maske_z = band(zs.outputs[0], 0.18, 0.82)
    fu = n.new("ShaderNodeMath"); fu.operation = "FLOOR"; l.new(us.outputs[0], fu.inputs[0])
    fz = n.new("ShaderNodeMath"); fz.operation = "FLOOR"; l.new(zs.outputs[0], fz.inputs[0])
    ox = n.new("ShaderNodeMath"); ox.operation = "FLOOR"; l.new(sep.outputs[0], ox.inputs[0])
    kom = n.new("ShaderNodeCombineXYZ")
    l.new(fu.outputs[0], kom.inputs[0]); l.new(fz.outputs[0], kom.inputs[1]); l.new(ox.outputs[0], kom.inputs[2])
    wn = n.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "3D"
    l.new(kom.outputs[0], wn.inputs["Vector"])
    an = n.new("ShaderNodeMath"); an.operation = "LESS_THAN"; an.inputs[1].default_value = quote
    l.new(wn.outputs["Value"], an.inputs[0])
    m1 = n.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
    l.new(maske_u, m1.inputs[0]); l.new(maske_z, m1.inputs[1])
    m2 = n.new("ShaderNodeMath"); m2.operation = "MULTIPLY"
    l.new(m1.outputs[0], m2.inputs[0]); l.new(an.outputs[0], m2.inputs[1])
    rampe = n.new("ShaderNodeValToRGB")
    rampe.color_ramp.elements[0].color = (*licht_farbe[0], 1)
    rampe.color_ramp.elements[1].color = (*licht_farbe[1], 1)
    l.new(wn.outputs["Color"], rampe.inputs[0])
    st = n.new("ShaderNodeMath"); st.operation = "MULTIPLY"; st.inputs[1].default_value = staerke
    l.new(m2.outputs[0], st.inputs[0])
    l.new(rampe.outputs["Color"], b.inputs["Emission Color"])
    l.new(st.outputs[0], b.inputs["Emission Strength"])
    return m


def aufbauen(ring=False):
    """Baut die Szene. ring=True: Stadt rundherum mit freiem Platz (fuer die Kamerafahrt)."""
    rnd = random.Random(94)
    glas = fenster_material("Towerglas", hex_farbe("#0e1a30"), [hex_farbe("#7fb2ff"), hex_farbe("#ffe2b0")],
                            2.0, 0.28, (2.6, 2.4), 0.06)
    silber = material("Silber", hex_farbe("#c9cdd2"), metall=1.0, rauheit=0.25)
    gelb = material("BLinie", hex_farbe("#ffd400"), emission=hex_farbe("#ffc400"), staerke=9)
    rot = material("Warnlicht", hex_farbe("#ff3b30"), emission=hex_farbe("#ff3b30"), staerke=80)
    blau = material("Kronenlicht", hex_farbe("#378add"), emission=hex_farbe("#5aa0ff"), staerke=25)

    quader("Tower", (6, 6, H - 3), (0, 0, (H - 3) / 2), glas, fase=0.08)
    quader("Krone", (4.4, 4.4, 2.4), (0, 0, H - 1.6), glas, fase=0.1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            quader("Kante", (0.22, 0.22, H - 2.6), (sx * 3.0, sy * 3.0, (H - 2.6) / 2), silber)
    quader("Kronenband", (6.2, 6.2, 0.25), (0, 0, H - 3), blau)
    quader("Mast", (0.18, 0.18, 6), (0, 0, H + 2.5), silber)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, 0, H + 5.6))
    bpy.context.object.data.materials.append(rot)
    seiten = [((0.0, -3.04), (0.22, 0.06))]
    if ring:  # die Kamera faehrt rundherum: B-Linie auf allen vier Seiten
        seiten += [((0.0, 3.04), (0.22, 0.06)), ((3.04, 0.0), (0.06, 0.22)), ((-3.04, 0.0), (0.06, 0.22))]
    for (x, y), (b, t) in seiten:
        quader("BLinie", (b, t, H - 4), (x, y, (H - 4) / 2 + 0.6), gelb)

    # Stadt (ein Mesh aus vielen Bloecken)
    stadtglas = fenster_material("Stadt", hex_farbe("#0a0d12"), [hex_farbe("#ffb35c"), hex_farbe("#ffe7c2")],
                                 1.6, 0.14, (2.6, 3.0), 0.5)
    me = bpy.data.meshes.new("Stadt")
    bm = bmesh.new()
    for _ in range(3200 if ring else 1700):
        if ring:  # Platz um den Tower und die Donau frei lassen
            x, y = rnd.uniform(-260, 260), rnd.uniform(-300, 260)
            if math.hypot(x, y) < 48 or -134 < y < -16:
                continue
        else:
            x, y = rnd.uniform(-200, 200), rnd.uniform(-14, 260)
        if abs(x) < 9 and abs(y) < 9:
            continue
        w, d = rnd.uniform(1.5, 4.5), rnd.uniform(1.5, 4.5)
        h = rnd.uniform(1.2, 7.0) * (1.0 if rnd.random() > 0.05 else 2.2)
        r = bmesh.ops.create_cube(bm, size=1)
        bmesh.ops.scale(bm, vec=(w, d, h), verts=r["verts"])
        bmesh.ops.translate(bm, vec=(x, y, h / 2), verts=r["verts"])
    bm.to_mesh(me)
    bm.free()
    stadt = bpy.data.objects.new("Stadt", me)
    bpy.context.collection.objects.link(stadt)
    stadt.data.materials.append(stadtglas)

    # Boden und Donau
    boden = material("Boden", hex_farbe("#07090d"), rauheit=0.9)
    bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 60, 0))
    bpy.context.object.data.materials.append(boden)
    wasser = bpy.data.materials.new("Donau")
    wasser.use_nodes = True
    wn_, wl = wasser.node_tree.nodes, wasser.node_tree.links
    wb = wn_["Principled BSDF"]
    wb.inputs["Base Color"].default_value = (*hex_farbe("#03070f"), 1)
    wb.inputs["Roughness"].default_value = 0.04
    rauschen = wn_.new("ShaderNodeTexNoise")
    rauschen.inputs["Scale"].default_value = 2.0
    wtc = wn_.new("ShaderNodeTexCoord")
    wmap = wn_.new("ShaderNodeMapping")
    wmap.inputs["Scale"].default_value = (0.15, 3.0, 1.0)
    wl.new(wtc.outputs["Object"], wmap.inputs["Vector"])
    wl.new(wmap.outputs["Vector"], rauschen.inputs["Vector"])
    bump = wn_.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    wl.new(rauschen.outputs["Fac"], bump.inputs["Height"])
    wl.new(bump.outputs["Normal"], wb.inputs["Normal"])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -75, 0.05))
    donau = bpy.context.object
    donau.scale = (600, 112, 1)
    donau.data.materials.append(wasser)

    # Nebel
    nebel = bpy.data.materials.new("Nebel")
    nebel.use_nodes = True
    nn = nebel.node_tree.nodes
    nn.remove(nn["Principled BSDF"])
    vol = nn.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = 0.007
    vol.inputs["Color"].default_value = (*hex_farbe("#9fb8e0"), 1)
    nebel.node_tree.links.new(vol.outputs[0], nn["Material Output"].inputs["Volume"])
    quader("Nebel", (500, 420, 22), (0, 80, 11), nebel)

    # Himmel: Stadtleuchten am Horizont, oben tiefes Blau
    w = welt(hex_farbe("#03060f"), 1.0)
    wn2, wl2 = w.node_tree.nodes, w.node_tree.links
    tc2 = wn2.new("ShaderNodeTexCoord")
    sep2 = wn2.new("ShaderNodeSeparateXYZ")
    wl2.new(tc2.outputs["Generated"], sep2.inputs[0])
    himmel = wn2.new("ShaderNodeValToRGB")
    himmel.color_ramp.elements[0].position = 0.48
    himmel.color_ramp.elements[0].color = (*hex_farbe("#2c3550"), 1)
    himmel.color_ramp.elements[1].position = 0.62
    himmel.color_ramp.elements[1].color = (*hex_farbe("#03060f"), 1)
    himmel.color_ramp.elements.new(0.53).color = (*hex_farbe("#14244a"), 1)
    wl2.new(sep2.outputs[2], himmel.inputs[0])
    wl2.new(himmel.outputs[0], wn2["Background"].inputs["Color"])

    licht("SUN", (0, 0, 50), 0.08, hex_farbe("#7fa6ff"), ziel=(10, 30, 0), winkel=1)
    for sx, sy in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
        licht("SPOT", (sx, sy, H - 4.5), 1800, hex_farbe("#6aa8ff"), ziel=(0, 0, H + 6), winkel=40)
    licht("POINT", (0.0, -5, 4), 300, hex_farbe("#ffc400"))
