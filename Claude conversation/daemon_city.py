# -*- coding: utf-8 -*-
"""
DAEMON CITY
A city where famous architects and philosophers live alongside ordinary people.
Every famous figure lives in a house / office built strictly from their own theory;
ordinary people live in simple houses, each with a unique shape; public and
commercial buildings serve the city.

Run in Rhino 8 (ScriptEditor, Python 3).  Units: metres.
Re-running deletes and rebuilds everything under the layer "Daemon City".
"""
import io
import json
import math
import os
import random
import System
import Rhino
import Rhino.Geometry as rg
from System.Drawing import Color
from System.Collections.Generic import List

try:
    doc = __rhino_doc__
except NameError:
    doc = Rhino.RhinoDoc.ActiveDoc

if doc.ModelUnitSystem != Rhino.UnitSystem.Meters:
    doc.AdjustModelUnitSystem(Rhino.UnitSystem.Meters, False)
TOL = doc.ModelAbsoluteTolerance
ROOT = "Daemon City"
SEED = 1919          # the year the Bauhaus was founded in Weimar
R = random.Random(SEED)
Z = rg.Vector3d.ZAxis

# ----------------------------------------------------------------- colours
WHITE = (243, 243, 239); OFFW = (232, 226, 212); CONC = (176, 175, 169)
GLASS = (165, 205, 228); DGLASS = (72, 96, 122); STEEL = (55, 58, 64)
BRICK = (168, 82, 58); STONE = (222, 212, 190); MARBLE = (238, 234, 224)
WOOD = (150, 105, 66); DWOOD = (88, 62, 42); TERRA = (196, 120, 80)
GRASS = (125, 168, 88); WATER = (88, 148, 200); RED = (190, 42, 40)
GOLD = (215, 175, 60); YELLOW = (232, 196, 92); SLATE = (85, 88, 96)
CREAM = (234, 222, 192); SIDEWALK = (196, 193, 186); PAVING = (214, 208, 196)
ASPHALT = (78, 80, 84); MEADOW = (140, 165, 100)
PASTELS = [(236, 220, 190), (214, 196, 170), (200, 215, 225), (228, 200, 196),
           (210, 225, 195), (242, 236, 212), (220, 205, 230), (245, 214, 178),
           (192, 204, 190), (232, 232, 230), (250, 240, 226), (205, 180, 160),
           (180, 200, 215), (238, 205, 160)]
ROOFC = [(152, 62, 46), (112, 62, 50), (82, 82, 88), (62, 72, 92), (122, 92, 62),
         (72, 102, 82), (172, 92, 62), (96, 96, 98), (130, 52, 42)]
GLASSES = [(120, 160, 190), (95, 130, 160), (140, 175, 185), (110, 125, 140), (150, 170, 200)]


def jit(rgb, rnd, a=10):
    return tuple(max(0, min(255, int(c + rnd.uniform(-a, a)))) for c in rgb)


# ----------------------------------------------------------------- layers & adding
def layer(path, rgb):
    idx = doc.Layers.FindByFullPath(path, -1)
    if idx >= 0:
        return idx
    parent = System.Guid.Empty
    full = ""
    for i, name in enumerate(path.split("::")):
        full = name if i == 0 else full + "::" + name
        idx = doc.Layers.FindByFullPath(full, -1)
        if idx < 0:
            L = Rhino.DocObjects.Layer()
            L.Name = name
            L.Color = Color.FromArgb(*rgb)
            if parent != System.Guid.Empty:
                L.ParentLayerId = parent
            idx = doc.Layers.Add(L)
        parent = doc.Layers[idx].Id
    return idx


_cur = {"layer": 0}


def use(path, rgb=(200, 200, 200)):
    _cur["layer"] = layer(ROOT + "::" + path, rgb)


def material(name, rgb, transparency):
    idx = doc.Materials.Find(name, True)
    if idx >= 0:
        return idx
    m = Rhino.DocObjects.Material()
    m.Name = name
    m.DiffuseColor = Color.FromArgb(*rgb)
    m.Transparency = transparency
    return doc.Materials.Add(m)


def add(geo, rgb=None, name=None, mat=None):
    if geo is None:
        return None
    a = Rhino.DocObjects.ObjectAttributes()
    a.LayerIndex = _cur["layer"]
    if name:
        a.Name = name
    if rgb is not None:
        a.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
        a.ObjectColor = Color.FromArgb(*rgb)
    if mat is not None:
        a.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject
        a.MaterialIndex = mat
    return doc.Objects.Add(geo, a)


def add_text(text, plane, height, rgb):
    try:
        te = rg.TextEntity.Create(text, plane, doc.DimStyles.Current, False, 0, 0)
        te.TextHeight = height
        a = Rhino.DocObjects.ObjectAttributes()
        a.LayerIndex = _cur["layer"]
        a.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
        a.ObjectColor = Color.FromArgb(*rgb)
        doc.Objects.AddText(te, a)
    except Exception as e:
        print("text failed:", e)


# ----------------------------------------------------------------- primitives
def P(x, y, z=0.0):
    return rg.Point3d(x, y, z)


def plist(pts):
    l = List[rg.Point3d]()
    for p in pts:
        l.Add(p)
    return l


def pline(pts, close=True):
    pl = rg.Polyline()
    for p in pts:
        pl.Add(p)
    if close and pts[0].DistanceTo(pts[-1]) > 1e-9:
        pl.Add(pts[0])
    return rg.PolylineCurve(pl)


def box(x0, y0, z0, x1, y1, z1):
    return rg.Brep.CreateFromBox(rg.BoundingBox(min(x0, x1), min(y0, y1), min(z0, z1),
                                                max(x0, x1), max(y0, y1), max(z0, z1)))


def cbox(cx, cy, z0, w, d, h, rot=0, pivot=None):
    b = box(cx - w / 2., cy - d / 2., z0, cx + w / 2., cy + d / 2., z0 + h)
    if rot:
        b.Rotate(math.radians(rot), Z, pivot or P(cx, cy, 0))
    return b


def mbox(x0, y0, z0, x1, y1, z1):
    return rg.Mesh.CreateFromBox(rg.BoundingBox(min(x0, x1), min(y0, y1), min(z0, z1),
                                                max(x0, x1), max(y0, y1), max(z0, z1)), 1, 1, 1)


def extrude(pts, vec):
    crv = pline(pts)
    b = rg.Surface.CreateExtrusion(crv, vec).ToBrep()
    c = b.CapPlanarHoles(TOL)
    return c if c else b


def prism(pts2, z0, h):
    return extrude([P(x, y, z0) for x, y in pts2], rg.Vector3d(0, 0, h))


def prism_yz(pts2, x0, length):          # profile (y, z) extruded along +x
    return extrude([P(x0, y, z) for y, z in pts2], rg.Vector3d(length, 0, 0))


def prism_xz(pts2, y0, depth):           # profile (x, z) extruded along +y
    return extrude([P(x, y0, z) for x, z in pts2], rg.Vector3d(0, depth, 0))


def cyl(cx, cy, z0, r, h):
    return rg.Cylinder(rg.Circle(rg.Plane(P(cx, cy, z0), Z), r), h).ToBrep(True, True)


def hcyl(x0, cy, cz, r, length):          # horizontal cylinder along +x
    return rg.Cylinder(rg.Circle(rg.Plane(P(x0, cy, cz), rg.Vector3d.XAxis), r), length).ToBrep(True, True)


def sph(cx, cy, cz, r):
    return rg.Sphere(P(cx, cy, cz), r).ToBrep()


def cone(cx, cy, z0, r, h):
    pl = rg.Plane(P(cx, cy, z0 + h), rg.Vector3d(0, 0, -1))   # apex at plane origin
    return rg.Cone(pl, h, r).ToBrep(True)


def ring(cx, cy, z0, rin, rout, h, top_in=None):
    """Solid ring (annulus) by revolving a section; top_in lets the inner top differ (stands)."""
    tin = h if top_in is None else top_in
    prof = pline([P(cx + rin, cy, z0), P(cx + rout, cy, z0), P(cx + rout, cy, z0 + h),
                  P(cx + rin, cy, z0 + tin)])
    rs = rg.RevSurface.Create(prof, rg.Line(P(cx, cy, z0), P(cx, cy, z0 + 1)))
    return rs.ToBrep() if rs else None


def ngon(cx, cy, r, n, rot=0):
    return [(cx + r * math.cos(math.radians(rot) + 2 * math.pi * k / n),
             cy + r * math.sin(math.radians(rot) + 2 * math.pi * k / n)) for k in range(n)]


def mesh_from(pts, faces):
    m = rg.Mesh()
    for p in pts:
        m.Vertices.Add(p.X, p.Y, p.Z)
    for f in faces:
        if len(f) == 3:
            m.Faces.AddFace(f[0], f[1], f[2])
        else:
            m.Faces.AddFace(f[0], f[1], f[2], f[3])
    m.Normals.ComputeNormals()
    m.Compact()
    m.Unweld(0.0, True)
    return m


def pyramid(pts3, apex):
    n = len(pts3)
    cx = sum(p.X for p in pts3) / n
    cy = sum(p.Y for p in pts3) / n
    faces = [(i, (i + 1) % n, n) for i in range(n)] + [((i + 1) % n, i, n + 1) for i in range(n)]
    return mesh_from(list(pts3) + [apex, P(cx, cy, pts3[0].Z)], faces)


def hip_roof(cx, cy, z, w, d, h):
    if abs(w - d) < 0.05:
        return pyramid([P(cx - w / 2, cy - d / 2, z), P(cx + w / 2, cy - d / 2, z),
                        P(cx + w / 2, cy + d / 2, z), P(cx - w / 2, cy + d / 2, z)], P(cx, cy, z + h))
    rot = d > w
    if rot:
        w, d = d, w
    x0, x1, y0, y1 = cx - w / 2., cx + w / 2., cy - d / 2., cy + d / 2.
    ins = d / 2.
    pts = [P(x0, y0, z), P(x1, y0, z), P(x1, y1, z), P(x0, y1, z),
           P(x0 + ins, cy, z + h), P(x1 - ins, cy, z + h)]
    m = mesh_from(pts, [(0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4), (0, 3, 2, 1)])
    if rot:
        m.Rotate(math.pi / 2, Z, P(cx, cy, 0))
    return m


def roof_profile(kind, e, rh):
    if kind == 'gable':
        return [(-e, 0), (e, 0), (0, rh)]
    if kind == 'saltbox':
        return [(-e, 0), (e, 0), (e * 0.35, rh)]
    if kind == 'shed':
        return [(-e, 0), (e, 0), (e, rh * 0.7), (-e, 0.25)]
    if kind == 'gambrel':
        return [(-e, 0), (e, 0), (e * 0.72, rh * 0.62), (0, rh), (-e * 0.72, rh * 0.62)]
    if kind == 'butterfly':
        return [(-e, 0), (e, 0), (e, rh * 0.5), (0, 0.3), (-e, rh * 0.5)]
    if kind == 'barrel':
        return [(e * math.cos(t), rh * 0.75 * math.sin(t))
                for t in [math.pi * k / 12. for k in range(13)]]
    return [(-e, 0), (e, 0), (0, rh)]


def profile_roof(cx, cy, z, w, d, kind, rh, ov=0.4):
    rot = d > w
    if rot:
        w, d = d, w
    e = d / 2. + ov
    b = prism_yz([(cy + py, z + pz) for py, pz in roof_profile(kind, e, rh)], cx - w / 2. - ov, w + 2 * ov)
    if rot:
        b.Rotate(math.pi / 2, Z, P(cx, cy, 0))
    return b


def pipe(pts, r):
    crv = rg.Curve.CreateInterpolatedCurve(plist(pts), 3)
    return rg.Brep.CreatePipe(crv, r, False, rg.PipeCapMode.Round, True, TOL, 0.02)


def loft(curves, closed=False):
    l = List[rg.Curve]()
    for c in curves:
        l.Add(c)
    return rg.Brep.CreateFromLoft(l, rg.Point3d.Unset, rg.Point3d.Unset, rg.LoftType.Normal, closed)


def difference(b, cutters):
    for c in cutters:
        try:
            res = rg.Brep.CreateBooleanDifference(b, c, TOL)
            if res and len(res) > 0:
                b = res[0]
        except Exception:
            pass
    return b


# ----------------------------------------------------------------- merged mesh accumulators
ACC_STYLE = {
    'openings': ("Details::Windows & Doors", (45, 50, 58)),
    'spandrel': ("Details::Facade Bands", (218, 218, 212)),
    'trunks': ("Landscape::Trees", (96, 72, 52)),
    'canopy1': ("Landscape::Trees", (96, 150, 72)),
    'canopy2': ("Landscape::Trees", (70, 124, 62)),
    'canopy3': ("Landscape::Trees", (138, 168, 80)),
    'marks': ("Ground::Road Markings", (245, 245, 240)),
    'rails': ("Details::Rails", (92, 92, 96)),
    'cars1': ("Details::Cars", (196, 58, 50)),
    'cars2': ("Details::Cars", (60, 92, 160)),
    'cars3': ("Details::Cars", (232, 232, 232)),
}
ACC = {k: rg.Mesh() for k in ACC_STYLE}


def tree(x, y, h=None, rnd=None, kind=None):
    rnd = rnd or R
    h = h or rnd.uniform(5.5, 10.5)
    ACC['trunks'].Append(rg.Mesh.CreateFromCylinder(
        rg.Cylinder(rg.Circle(rg.Plane(P(x, y, 0), Z), 0.18 + h * 0.015), h * 0.5), 1, 6))
    kind = kind or ('round' if rnd.random() < 0.72 else 'conifer')
    canopy = ACC[rnd.choice(['canopy1', 'canopy2', 'canopy3'])]
    if kind == 'round':
        canopy.Append(rg.Mesh.CreateFromSphere(rg.Sphere(P(x, y, h * 0.66), h * 0.3), 8, 6))
    else:
        canopy.Append(rg.Mesh.CreateFromCone(
            rg.Cone(rg.Plane(P(x, y, h), rg.Vector3d(0, 0, -1)), h * 0.82, h * 0.22), 1, 8, True))


def car(x, y, rot=0, rnd=None):
    rnd = rnd or R
    m = mbox(x - 2.1, y - 0.9, 0.25, x + 2.1, y + 0.9, 1.0)
    m.Append(mbox(x - 1.1, y - 0.8, 1.0, x + 0.9, y + 0.8, 1.5))
    if rot:
        m.Rotate(math.radians(rot), Z, P(x, y, 0))
    ACC[rnd.choice(['cars1', 'cars2', 'cars3', 'cars3'])].Append(m)


def facade_windows(m, x0, y0, x1, y1, z0, z1, faces='NSEW', floor_h=3.2, ww=1.2, wh=1.5,
                   spacing=3.0, sill=0.9):
    nfl = max(1, int((z1 - z0) / floor_h))
    for f in range(nfl):
        zb = z0 + f * floor_h + sill
        zt = zb + wh
        if zt > z1 - 0.25:
            break
        for face in faces:
            if face in 'NS':
                L = x1 - x0
                y = y0 if face == 'S' else y1
                n = int(L / spacing)
                for k in range(n):
                    xc = x0 + (k + 0.5) * L / n
                    m.Append(mbox(xc - ww / 2, y - 0.07, zb, xc + ww / 2, y + 0.07, zt))
            else:
                L = y1 - y0
                x = x0 if face == 'W' else x1
                n = int(L / spacing)
                for k in range(n):
                    yc = y0 + (k + 0.5) * L / n
                    m.Append(mbox(x - 0.07, yc - ww / 2, zb, x + 0.07, yc + ww / 2, zt))


def bands(x0, y0, x1, y1, z0, z1, step=3.8, t=0.45):
    z = z0 + step
    while z < z1 - 0.5:
        ACC['spandrel'].Append(mbox(x0 - 0.08, y0 - 0.08, z, x1 + 0.08, y1 + 0.08, z + t))
        z += step


LABELS = []      # (point, text, group)
FAMOUS_POS = {}  # name -> (x, y, top) of each famous house
PUBLIC_POS = {}  # name -> (x, y) of the public buildings in the inner ring
MOUNTAIN = []    # Zarathustra's mountain mesh, for walking on it
LEGEND = []      # (group, name, theory, location)


def label(x, y, z, text, group="Public & Commercial"):
    LABELS.append((P(x, y, z), text, group))


# ================================================================= ORDINARY HOUSES
HOUSE_N = [0]
KINDS = ['rect'] * 5 + ['L', 'L', 'T', 'U', 'cross', 'twin', 'tower', 'split', 'circle', 'poly',
                        'tri', 'courtyard', 'stepped', 'aframe', 'bubble']
PROFILE_ROOFS = ['gable', 'gable', 'gable', 'hip', 'hip', 'shed', 'flat', 'flat', 'barrel',
                 'gambrel', 'saltbox', 'butterfly']


def house_unit(parts, wins, ux, uy, w, d, h, roof, wall, roofc, rnd, door=True, chimney=False):
    local = []
    lw = rg.Mesh()
    rot = d > w
    W, D = (d, w) if rot else (w, d)
    local.append((cbox(ux, uy, 0, W, D, h), wall))
    rh = D * rnd.uniform(0.3, 0.55)
    if roof == 'flat':
        local.append((cbox(ux, uy, h, W + 0.3, D + 0.3, 0.45), (178, 176, 170)))
    elif roof == 'hip':
        local.append((hip_roof(ux, uy, h, W + 0.8, D + 0.8, rh), roofc))
    else:
        local.append((profile_roof(ux, uy, h, W, D, roof, rh), roofc))
    facade_windows(lw, ux - W / 2, uy - D / 2, ux + W / 2, uy + D / 2, 0, h, faces='NS',
                   spacing=2.8, ww=1.0, wh=1.3, floor_h=3.0)
    if door:
        lw.Append(mbox(ux - 0.55, uy - D / 2 - 0.09, 0, ux + 0.55, uy - D / 2 + 0.02, 2.2))
    if chimney and roof != 'flat':
        local.append((cbox(ux + W * 0.25, uy + D * 0.12, h, 0.7, 0.7, rh + 0.8), (122, 72, 56)))
    if rot:
        for g, _ in local:
            g.Rotate(math.pi / 2, Z, P(ux, uy, 0))
        lw.Rotate(math.pi / 2, Z, P(ux, uy, 0))
    parts.extend(local)
    wins.Append(lw)


def ordinary_house(x0, y0, x1, y1, rnd):
    HOUSE_N[0] += 1
    pw, pd = x1 - x0, y1 - y0
    m = min(pw, pd)
    cx, cy = (x0 + x1) / 2., (y0 + y1) / 2.
    wall = jit(rnd.choice(PASTELS), rnd, 12)
    roofc = jit(rnd.choice(ROOFC), rnd, 12)
    kind = rnd.choice(KINDS)
    roof = rnd.choice(PROFILE_ROOFS)
    h = rnd.choice([1, 1, 2, 2, 2, 3]) * 3.0 + rnd.uniform(0, 0.4)
    s = m * rnd.uniform(0.42, 0.54)
    parts = []
    wins = rg.Mesh()

    def U(ux, uy, w, d, hh, rf=None, **kw):
        house_unit(parts, wins, ux, uy, w, d, hh, rf or roof, wall, roofc, rnd, **kw)

    if kind == 'rect':
        U(cx, cy, s * rnd.uniform(1.0, 1.5), s * rnd.uniform(0.62, 0.9), h, chimney=rnd.random() < 0.45)
    elif kind == 'L':
        U(cx, cy - 0.25 * s, 1.4 * s, 0.55 * s, h, chimney=rnd.random() < 0.4)
        U(cx + 0.425 * s, cy + 0.2 * s, 0.55 * s, 0.9 * s, max(3.0, h - rnd.choice([0, 3])), door=False)
    elif kind == 'T':
        U(cx, cy + 0.25 * s, 1.5 * s, 0.55 * s, h, door=False)
        U(cx, cy - 0.35 * s, 0.55 * s, 0.8 * s, max(3.0, h - 3))
    elif kind == 'U':
        U(cx, cy + 0.35 * s, 1.4 * s, 0.5 * s, h, door=False)
        for sx in (-1, 1):
            U(cx + sx * 0.45 * s, cy - 0.2 * s, 0.5 * s, 0.9 * s, h, door=(sx < 0))
    elif kind == 'cross':
        U(cx, cy, 1.5 * s, 0.5 * s, h)
        U(cx, cy, 0.5 * s, 1.5 * s, h + 3, door=False)
    elif kind == 'twin':
        rf = rnd.choice(['shed', 'gable', 'flat', 'barrel', 'saltbox'])
        U(cx - 0.35 * s, cy, 0.7 * s, 0.85 * s, h, rf)
        U(cx + 0.35 * s, cy, 0.7 * s, 0.85 * s, h + rnd.choice([0, 1.5, 3]), rf)
    elif kind == 'tower':
        w = 0.62 * s
        th = rnd.choice([9.4, 12.4])
        parts.append((cbox(cx, cy, 0, w, w, th), wall))
        q = w / 2 + 0.5
        parts.append((pyramid([P(cx - q, cy - q, th), P(cx + q, cy - q, th), P(cx + q, cy + q, th),
                               P(cx - q, cy + q, th)], P(cx, cy, th + w * 0.9)), roofc))
        facade_windows(wins, cx - w / 2, cy - w / 2, cx + w / 2, cy + w / 2, 0, th, spacing=2.5,
                       ww=0.9, wh=1.3, floor_h=3.0)
        wins.Append(mbox(cx - 0.55, cy - w / 2 - 0.09, 0, cx + 0.55, cy - w / 2 + 0.02, 2.2))
    elif kind == 'split':
        U(cx - 0.3 * s, cy, 0.8 * s, 0.8 * s, h, 'shed')
        U(cx + 0.45 * s, cy + 0.1 * s, 0.6 * s, 0.7 * s, h + 1.5, 'shed', door=False)
    elif kind == 'circle':
        r = 0.55 * s
        parts.append((cyl(cx, cy, 0, r, h), wall))
        rr = rnd.choice(['cone', 'dome', 'flat'])
        if rr == 'cone':
            parts.append((cone(cx, cy, h, r + 0.5, r * 0.9), roofc))
        elif rr == 'dome':
            parts.append((sph(cx, cy, h, r), roofc))
        else:
            parts.append((cyl(cx, cy, h, r + 0.25, 0.45), (178, 176, 170)))
        wins.Append(mbox(cx - 0.55, cy - r - 0.09, 0, cx + 0.55, cy - r + 0.15, 2.2))
        for k in range(1, 6):
            wm = mbox(cx - 0.5, cy - r - 0.08, 1.0, cx + 0.5, cy - r + 0.15, 2.2)
            wm.Rotate(2 * math.pi * k / 6, Z, P(cx, cy, 0))
            wins.Append(wm)
    elif kind == 'poly':
        n = rnd.choice([5, 6, 8])
        r = 0.6 * s
        a0 = rnd.uniform(0, 360)
        parts.append((prism(ngon(cx, cy, r, n, a0), 0, h), wall))
        if rnd.random() < 0.7:
            parts.append((pyramid([P(x, y, h) for x, y in ngon(cx, cy, r + 0.5, n, a0)],
                                  P(cx, cy, h + r * 0.8)), roofc))
        else:
            parts.append((prism(ngon(cx, cy, r + 0.25, n, a0), h, 0.45), (178, 176, 170)))
        wins.Append(mbox(cx - 0.55, cy - r * 0.85, 0, cx + 0.55, cy - r * 0.6, 2.2))
    elif kind == 'tri':
        r = 0.78 * s
        parts.append((prism(ngon(cx, cy, r, 3, 90), 0, h), wall))
        if rnd.random() < 0.5:
            parts.append((pyramid([P(x, y, h) for x, y in ngon(cx, cy, r + 0.6, 3, 90)],
                                  P(cx, cy, h + r * 0.7)), roofc))
        else:
            parts.append((prism(ngon(cx, cy, r + 0.3, 3, 90), h, 0.45), (178, 176, 170)))
        wins.Append(mbox(cx - 0.55, cy - r * 0.5 - 0.1, 0, cx + 0.55, cy - r * 0.5 + 0.1, 2.2))
    elif kind == 'courtyard':
        o, t = 1.45 * s, 0.34 * s
        hh = min(h, 6.2)
        U(cx, cy - o / 2 + t / 2, o, t, hh, 'flat')
        U(cx, cy + o / 2 - t / 2, o, t, hh, 'flat', door=False)
        U(cx - o / 2 + t / 2, cy, t, o - 2 * t, hh, 'flat', door=False)
        U(cx + o / 2 - t / 2, cy, t, o - 2 * t, hh, 'flat', door=False)
        tree(cx, cy, 5.5, rnd)
    elif kind == 'stepped':
        U(cx, cy, 1.3 * s, 0.95 * s, 3.2, 'flat')
        U(cx + 0.15 * s, cy + 0.12 * s, 0.85 * s, 0.6 * s, 6.4, 'flat', door=False)
        if rnd.random() < 0.5:
            U(cx + 0.25 * s, cy + 0.18 * s, 0.45 * s, 0.35 * s, 9.6, 'flat', door=False)
    elif kind == 'aframe':
        w, d = 1.25 * s, 0.95 * s
        e = d / 2.
        parts.append((prism_yz([(cy - e, 0), (cy + e, 0), (cy, e * 1.9)], cx - w / 2, w), roofc))
        wins.Append(mesh_from([P(cx - w / 2 - 0.06, cy - e * 0.6, 0), P(cx - w / 2 - 0.06, cy + e * 0.6, 0),
                               P(cx - w / 2 - 0.06, cy, e * 1.9 * 0.6)], [(0, 1, 2)]))
    elif kind == 'bubble':
        r = 0.62 * s
        parts.append((sph(cx, cy, 0, r), wall))
        wins.Append(mbox(cx - 0.6, cy - r - 0.1, 0, cx + 0.6, cy - r + 0.6, 2.2))
        wins.Append(mbox(cx + r * 0.55, cy - r * 0.62, 1.3, cx + r * 0.75, cy - r * 0.45, 2.4))

    rot = rnd.choice([0, 0, 0, 90, 180, 270, rnd.uniform(-25, 25)])
    name = "House %d - ordinary family (%s plan, %s roof)" % (HOUSE_N[0], kind, roof)
    use("Ordinary Houses", (230, 215, 190))
    for g, c in parts:
        if rot:
            g.Rotate(math.radians(rot), Z, P(cx, cy, 0))
        add(g, c, name)
    if rot:
        wins.Rotate(math.radians(rot), Z, P(cx, cy, 0))
    ACC['openings'].Append(wins)
    if rnd.random() < 0.6:
        tree(x0 + 1.5, y1 - 1.5, rnd=rnd)
    if rnd.random() < 0.35:
        tree(x1 - 1.5, y1 - 1.5, rnd=rnd)


def res_fill(x0, y0, x1, y1, rnd):
    t = rnd.choice([19.0, 21.5, 25.0])
    nx = max(1, int(round((x1 - x0) / t)))
    ny = max(1, int(round((y1 - y0) / t)))
    dx, dy = (x1 - x0) / nx, (y1 - y0) / ny
    for i in range(nx):
        for j in range(ny):
            px, py = x0 + i * dx, y0 + j * dy
            if rnd.random() < 0.07:
                for k in range(3):
                    tree(px + rnd.uniform(2, dx - 2), py + rnd.uniform(2, dy - 2), rnd=rnd)
                continue
            ordinary_house(px + 1, py + 1, px + dx - 1, py + dy - 1, rnd)


# ================================================================= ARCHITECTS (detailed)
UP = (0, 0, 1)


class Bag:
    """Collects small detail meshes by colour; each colour becomes one object (keeps the model light)."""

    def __init__(self):
        self.d = {}

    def __call__(self, rgb, m):
        if m is None:
            return
        if rgb not in self.d:
            self.d[rgb] = rg.Mesh()
        self.d[rgb].Append(m)

    def transform(self, xf):
        for m in self.d.values():
            m.Transform(xf)

    def merge(self, other):
        for rgb, m in other.d.items():
            self(rgb, m)

    def flush(self):
        for rgb, m in self.d.items():
            if m.Vertices.Count:
                m.Normals.ComputeNormals()
                add(m, rgb, mat=GLASSMAT if rgb == GLASS else None)
        self.d = {}


def pt(o, u, v, n, a, b, c):
    return P(o[0] + u[0] * a + v[0] * b + n[0] * c,
             o[1] + u[1] * a + v[1] * b + n[1] * c,
             o[2] + u[2] * a + v[2] * b + n[2] * c)


BOX_FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def obox(o, u, v, n, a0, a1, b0, b1, c0, c1):
    """Oriented box in a local frame: a along u, b along v, c along n."""
    return mesh_from([pt(o, u, v, n, a, b, c) for (a, b, c) in
                      [(a0, b0, c0), (a1, b0, c0), (a1, b1, c0), (a0, b1, c0),
                       (a0, b0, c1), (a1, b0, c1), (a1, b1, c1), (a0, b1, c1)]], BOX_FACES)


def face_frame(x0, y0, x1, y1, f):
    """Frame of a vertical face of an axis-aligned box: origin, along-face u, outward n, width."""
    if f == 'S':
        return (x0, y0, 0), (1, 0, 0), (0, -1, 0), x1 - x0
    if f == 'N':
        return (x1, y1, 0), (-1, 0, 0), (0, 1, 0), x1 - x0
    if f == 'E':
        return (x1, y0, 0), (0, 1, 0), (1, 0, 0), y1 - y0
    return (x0, y1, 0), (0, -1, 0), (-1, 0, 0), y1 - y0


def mullion_grid(bag, rgb, x0, y0, x1, y1, z0, z1, faces, su, sv=None, t=0.08, d=0.1):
    for f in faces:
        o, u, n, U = face_frame(x0, y0, x1, y1, f)
        if su:
            k = max(1, int(round(U / su)))
            for i in range(k + 1):
                a = U * i / k
                bag(rgb, obox(o, u, UP, n, a - t / 2, a + t / 2, z0, z1, 0, d))
        if sv:
            k = max(1, int(round((z1 - z0) / sv)))
            for j in range(k + 1):
                b = z0 + (z1 - z0) * j / k
                bag(rgb, obox(o, u, UP, n, 0, U, b - t / 2, b + t / 2, 0, d))


def win(bag, o, u, n, a, zb, ww, wh, glass=DGLASS, frame=WHITE, ft=0.12, cross=False):
    """A framed window centred at a, sill zb, on a face frame."""
    bag(glass, obox(o, u, UP, n, a - ww / 2, a + ww / 2, zb, zb + wh, -0.05, 0.04))
    if frame is None:
        return
    for (a0, a1, b0, b1) in [(a - ww / 2 - ft, a + ww / 2 + ft, zb - ft, zb),
                             (a - ww / 2 - ft, a + ww / 2 + ft, zb + wh, zb + wh + ft),
                             (a - ww / 2 - ft, a - ww / 2, zb, zb + wh),
                             (a + ww / 2, a + ww / 2 + ft, zb, zb + wh)]:
        bag(frame, obox(o, u, UP, n, a0, a1, b0, b1, 0, 0.09))
    if cross:
        bag(frame, obox(o, u, UP, n, a - 0.04, a + 0.04, zb, zb + wh, 0, 0.07))
        bag(frame, obox(o, u, UP, n, a - ww / 2, a + ww / 2, zb + wh * 0.6 - 0.04, zb + wh * 0.6 + 0.04, 0, 0.07))


def window_rows(bag, x0, y0, x1, y1, faces, sills, spacing, ww, wh, **kw):
    for f in faces:
        o, u, n, U = face_frame(x0, y0, x1, y1, f)
        k = max(1, int(U / spacing))
        for i in range(k):
            for zb in sills:
                win(bag, o, u, n, (i + 0.5) * U / k, zb, ww, wh, **kw)


def ribbon(bag, x0, y0, x1, y1, faces, zb, zt, mull=1.2, glass=DGLASS, frame=WHITE, inset=0.4):
    for f in faces:
        o, u, n, U = face_frame(x0, y0, x1, y1, f)
        bag(glass, obox(o, u, UP, n, inset, U - inset, zb, zt, -0.05, 0.05))
        k = max(1, int(round((U - 2 * inset) / mull)))
        for i in range(k + 1):
            a = inset + (U - 2 * inset) * i / k
            bag(frame, obox(o, u, UP, n, a - 0.04, a + 0.04, zb, zt, 0, 0.08))


def strip(bag, rgb, o, u, n, pa, pb, w, d):
    da, db = pb[0] - pa[0], pb[1] - pa[1]
    L = math.hypot(da, db)
    if L < 1e-6:
        return
    px, py = -db / L * w / 2, da / L * w / 2
    cs = [(pa[0] + px, pa[1] + py), (pb[0] + px, pb[1] + py), (pb[0] - px, pb[1] - py), (pa[0] - px, pa[1] - py)]
    pts = [pt(o, u, UP, n, a, b, 0) for a, b in cs] + [pt(o, u, UP, n, a, b, d) for a, b in cs]
    bag(rgb, mesh_from(pts, BOX_FACES))


def diagrid(bag, rgb, x0, y0, x1, y1, z0, z1, faces, s, w=0.35, d=0.12):
    H = z1 - z0
    for f in faces:
        o, u, n, U = face_frame(x0, y0, x1, y1, f)
        o = (o[0], o[1], z0)
        c = -U
        while c < H:
            a0, a1 = max(0., -c), min(U, H - c)
            if a1 > a0:
                strip(bag, rgb, o, u, n, (a0, a0 + c), (a1, a1 + c), w, d)
            c += s
        c = s
        while c < U + H:
            a0, a1 = max(0., c - H), min(U, c)
            if a1 > a0:
                strip(bag, rgb, o, u, n, (a0, c - a0), (a1, c - a1), w, d)
            c += s
        for b in (0, H):
            bag(rgb, obox(o, u, UP, n, 0, U, b - w / 2, b + w / 2, 0, d))
        for a in (0, U):
            bag(rgb, obox(o, u, UP, n, a - w / 2, a + w / 2, 0, H, 0, d))


def railing(bag, rgb, p0, p1, z, h=1.0, post=1.4, t=0.04):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    u = (dx / L, dy / L, 0)
    n = (u[1], -u[0], 0)
    o = (p0[0], p0[1], z)
    bag(rgb, obox(o, u, UP, n, 0, L, h - t, h, -t, t))
    bag(rgb, obox(o, u, UP, n, 0, L, h / 2 - t / 2, h / 2 + t / 2, -t / 2, t / 2))
    k = max(1, int(L / post))
    for i in range(k + 1):
        a = L * i / k
        bag(rgb, obox(o, u, UP, n, a - t, a + t, 0, h, -t, t))


def stair(bag, rgb, o, u, width, n_steps, run, rise):
    nn = (u[1], -u[0], 0)
    for k in range(n_steps):
        bag(rgb, obox(o, u, UP, nn, k * run, n_steps * run, k * rise, (k + 1) * rise, -width / 2, width / 2))


def tri_prism(o, u, n, pts2, d):
    p = [pt(o, u, UP, n, a, b, 0) for a, b in pts2] + [pt(o, u, UP, n, a, b, d) for a, b in pts2]
    return mesh_from(p, [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)])


def mcyl(cx, cy, z0, r, h, seg=16):
    return rg.Mesh.CreateFromCylinder(rg.Cylinder(rg.Circle(rg.Plane(P(cx, cy, z0), Z), r), h), 1, seg, True, True)


def msph(cx, cy, cz, r, seg=10):
    return rg.Mesh.CreateFromSphere(rg.Sphere(P(cx, cy, cz), r), seg, seg // 2 + 2)


def mdisc(c, normal, r, t=0.06, seg=20):
    return rg.Mesh.CreateFromCylinder(rg.Cylinder(rg.Circle(rg.Plane(c, rg.Vector3d(*normal)), r), t), 1, seg, True, True)


def ellipsoid_mesh(cx, cy, cz, rx, ry, rz, seg=10):
    m = rg.Mesh.CreateFromSphere(rg.Sphere(P(0, 0, 0), 1.0), seg, seg // 2 + 2)
    m.Transform(rg.Transform.Scale(rg.Plane.WorldXY, rx, ry, rz))
    m.Translate(rg.Vector3d(cx, cy, cz))
    return m


def rprism(x0, y0, x1, y1, z, h, r):
    """Rectangular slab with rounded corners (Wright's parapets)."""
    c = rg.Rectangle3d(rg.Plane(P(0, 0, z), Z), rg.Interval(x0, x1), rg.Interval(y0, y1)).ToNurbsCurve()
    f = rg.Curve.CreateFilletCornersCurve(c, r, TOL, 0.01)
    b = rg.Surface.CreateExtrusion(f or c, rg.Vector3d(0, 0, h)).ToBrep()
    return b.CapPlanarHoles(TOL) or b


def rot2(px, py, cx, cy, ang):
    a = math.radians(ang)
    return (cx + (px - cx) * math.cos(a) - (py - cy) * math.sin(a),
            cy + (px - cx) * math.sin(a) + (py - cy) * math.cos(a))


def add_pipe(crv, r, rgb):
    for b in rg.Brep.CreatePipe(crv, r, False, rg.PipeCapMode.Flat, True, TOL, 0.02) or []:
        add(b, rgb)


# ------------------------------------------------------------------------------------------------
def b_mies(cx, cy):
    """Farnsworth House: only floor, roof, eight steel columns and glass; a wood core floats in the open plan."""
    bag = Bag()
    TRAV = (236, 230, 214)
    w, d, z = 21., 10., 1.6
    x0, y0, y1 = cx - 6., cy - d / 2, cy + d / 2
    x1 = x0 + w
    add(box(x0, y0, z, x1, y1, z + 0.35), WHITE)
    add(box(x0 + 0.05, y0 + 0.05, z + 0.35, x1 - 0.05, y1 - 0.05, z + 0.38), TRAV)
    add(box(x0, y0, z + 3.6, x1, y1, z + 3.95), WHITE)

    def column(x, yc, top):                      # wide-flange (I) steel column welded to the fascia
        bag(WHITE, mbox(x - 0.16, yc - 0.12, 0, x + 0.16, yc - 0.09, top))
        bag(WHITE, mbox(x - 0.16, yc + 0.09, 0, x + 0.16, yc + 0.12, top))
        bag(WHITE, mbox(x - 0.02, yc - 0.09, 0, x + 0.02, yc + 0.09, top))
    for k in range(4):
        x = x0 + 1.5 + k * (w - 3) / 3.
        for sy in (-1, 1):
            column(x, cy + sy * (d / 2 + 0.12), z + 3.95)
    gx0, gx1, gy0, gy1 = x0 + 5, x1 - 1.5, y0 + 0.4, y1 - 0.4
    add(box(gx0, gy0, z + 0.38, gx1, gy1, z + 3.6), GLASS, mat=GLASSMAT)
    mullion_grid(bag, (92, 94, 98), gx0, gy0, gx1, gy1, z + 0.38, z + 3.6, 'NSEW', 2.9, t=0.06, d=0.05)
    bag((92, 94, 98), mbox(gx0 - 0.06, cy - 0.9, z + 0.38, gx0 + 0.02, cy + 0.9, z + 2.6))       # entrance doors
    # the primavera-wood core: kitchen, two baths, fireplace
    add(box(x0 + 10, cy - 1.5, z + 0.38, x0 + 15.5, cy + 1.5, z + 2.9), (196, 150, 98))
    bag(STEEL, mbox(x0 + 9.96, cy - 0.6, z + 0.38, x0 + 10.0, cy + 0.6, z + 1.3))
    # furniture: Barcelona chairs, glass table, dining table, bed
    LEATHER = (38, 38, 40)
    for yy in (cy - 2.8, cy + 2.8):
        xx = x0 + 6.8
        bag(LEATHER, mbox(xx - 0.38, yy - 0.38, z + 0.78, xx + 0.38, yy + 0.38, z + 0.88))
        bag(LEATHER, mbox(xx - 0.46, yy - 0.38, z + 0.85, xx - 0.36, yy + 0.38, z + 1.4))
        for s_ in (-0.38, 0.38):
            bag(STEEL, mbox(xx - 0.4, yy + s_ - 0.02, z + 0.38, xx + 0.4, yy + s_ + 0.02, z + 0.82))
    bag(GLASS, mbox(x0 + 7.7, cy - 0.7, z + 0.76, x0 + 8.7, cy + 0.7, z + 0.8))
    bag(DWOOD, mbox(x0 + 16.6, cy - 0.9, z + 1.1, x0 + 18.4, cy + 0.9, z + 1.15))
    for (tx, ty) in [(16.7, -0.8), (18.3, -0.8), (16.7, 0.8), (18.3, 0.8)]:
        bag(STEEL, mbox(x0 + tx - 0.03, cy + ty - 0.03, z + 0.38, x0 + tx + 0.03, cy + ty + 0.03, z + 1.1))
    for (tx, ty) in [(17.0, -1.3), (18.0, -1.3), (17.0, 1.3), (18.0, 1.3)]:
        bag(LEATHER, mbox(x0 + tx - 0.22, cy + ty - 0.22, z + 0.8, x0 + tx + 0.22, cy + ty + 0.22, z + 0.86))
    bag((236, 236, 232), mbox(x0 + 16.4, cy + 2.2, z + 0.38, x0 + 18.4, cy + 4.2, z + 0.85))
    # floating terrace with its own columns, travertine steps
    tx0, tx1, ty0, ty1 = x0 - 8, x0 + 2, y0 - 1.5, y1 - 3.5
    add(box(tx0, ty0, 0.6, tx1, ty1, 0.95), WHITE)
    add(box(tx0 + 0.05, ty0 + 0.05, 0.95, tx1 - 0.05, ty1 - 0.05, 0.98), TRAV)
    for x in (tx0 + 1.0, tx0 + 5.0):
        column(x, ty0 - 0.12, 0.95)
        column(x, ty1 + 0.12, 0.95)
    for k in range(3):
        add(box(tx0 - 3 + k * 1.0, cy - 3, 0.13 + k * 0.28, tx0 - 2 + k * 1.0, cy + 0.5, 0.25 + k * 0.28), TRAV)
    for k in range(4):
        add(box(x0 - 3.6 + k * 0.9, y0 + 0.6, 0.98 + k * 0.25, x0, y0 + 3.2, 0.98 + (k + 1) * 0.25), TRAV)
    tree(cx - 3, cy + 11, 12)
    tree(cx + 13, cy + 10, 10)
    tree(cx + 12, cy - 12, 9)
    bag.flush()
    return z + 4


def b_sullivan(cx, cy):
    """Guaranty/Wainwright type: base for shops, shaft for repeated offices, attic for machinery —
    each part's form expresses its function; terracotta ornament grows on the structure."""
    bag = Bag()
    w, h0, hs = 20., 8., 30.
    ORN, BRONZE = (182, 104, 70), (118, 88, 52)
    x0, y0, x1, y1 = cx - w / 2, cy - w / 2, cx + w / 2, cy + w / 2
    add(cbox(cx, cy, 0, w, w, h0), STONE)
    for f in 'SNEW':                                           # shop windows with bronze frames
        o, u, n, U = face_frame(x0, y0, x1, y1, f)
        for i in range(4):
            if f == 'S' and i in (1, 2):
                continue
            a0 = 1.2 + i * (U - 2.4) / 4 + 0.35
            a1 = 1.2 + (i + 1) * (U - 2.4) / 4 - 0.35
            bag(DGLASS, obox(o, u, UP, n, a0, a1, 0.6, 5.4, -0.05, 0.04))
            bag(BRONZE, obox(o, u, UP, n, a0 - 0.1, a1 + 0.1, 5.4, 5.6, 0, 0.1))
            bag(BRONZE, obox(o, u, UP, n, (a0 + a1) / 2 - 0.05, (a0 + a1) / 2 + 0.05, 0.6, 5.4, 0, 0.08))
            bag(BRONZE, obox(o, u, UP, n, a0 - 0.1, a1 + 0.1, 0.45, 0.6, 0, 0.1))
    add(box(cx - 2.4, y0 - 0.1, 0, cx + 2.4, y0 + 0.3, 4.2), DWOOD)          # arched entrance
    add(rg.Cylinder(rg.Circle(rg.Plane(P(cx, y0 - 0.1, 4.2), rg.Vector3d.YAxis), 2.4), 0.4).ToBrep(True, True), DWOOD)
    add_pipe(rg.Arc(rg.Plane(P(cx, y0 - 0.15, 4.2), rg.Vector3d.XAxis, Z), 2.85, math.pi).ToNurbsCurve(), 0.28, ORN)
    add(cbox(cx, cy, h0 - 0.6, w + 0.6, w + 0.6, 0.6), STONE)              # belt course
    add(cbox(cx, cy, h0, w - 1.6, w - 1.6, hs), DGLASS)                    # recessed windows
    piers = [0.1 + k * (w - 1.2) / 6 for k in range(7)]
    z = h0 + 2.2
    while z < h0 + hs - 1:
        bag(BRICK, mbox(x0 + 0.5, y0 + 0.5, z, x1 - 0.5, y1 - 0.5, z + 1.1))    # spandrel
        for f in 'SNEW':
            o, u, n, U = face_frame(x0 + 0.5, y0 + 0.5, x1 - 0.5, y1 - 0.5, f)
            for k in range(6):
                ac = (piers[k] + piers[k + 1]) / 2
                for da in (-0.75, 0, 0.75):                                 # terracotta ornament tiles
                    bag(ORN, obox(o, u, UP, n, ac + da - 0.28, ac + da + 0.28, z + 0.26, z + 0.84, 0, 0.09))
                bag(STEEL, obox(o, u, UP, n, ac - 0.05, ac + 0.05, z + 1.1, z + 3.3, -0.3, -0.25))
        z += 3.3
    for f in 'SNEW':                                                        # continuous vertical piers
        o, u, n, U = face_frame(x0 + 0.5, y0 + 0.5, x1 - 0.5, y1 - 0.5, f)
        for k, a in enumerate(piers):
            t = 0.55 if k in (0, 6) else 0.38
            bag(BRICK, obox(o, u, UP, n, a - t, a + t, h0, h0 + hs, -0.2, 0.25))
    add(cbox(cx, cy, h0 + hs, w, w, 3), TERRA)                             # attic frieze
    for f in 'SNEW':
        o, u, n, U = face_frame(x0, y0, x1, y1, f)
        for k in range(6):
            a = 0.5 + (piers[k] + piers[k + 1]) / 2
            c = pt(o, u, UP, n, a, h0 + hs + 1.5, 0)
            bag(ORN, mdisc(c, n, 0.8, t=0.05))
            bag(DGLASS, mdisc(c, n, 0.55, t=0.09))                           # oculus windows
        for a in piers:
            bag(ORN, obox(o, u, UP, n, a + 0.3, a + 0.7, h0 + hs + 0.3, h0 + hs + 2.7, 0, 0.1))
    add(cbox(cx, cy, h0 + hs + 3, w + 2.4, w + 2.4, 1.2), TERRA)          # projecting cornice
    for f in 'SNEW':                                                        # dentils / brackets
        o, u, n, U = face_frame(x0, y0, x1, y1, f)
        for i in range(int(U / 0.7)):
            a = 0.35 + i * 0.7
            bag(ORN, obox(o, u, UP, n, a - 0.15, a + 0.15, h0 + hs + 2.55, h0 + hs + 3, 0, 1.1))
    bag(STEEL, mcyl(cx + 6, cy + 6, h0 + hs + 4.2, 0.08, 7, 6))
    bag(RED, mbox(cx + 6.05, cy + 5.98, h0 + hs + 9.8, cx + 7.8, cy + 6.02, h0 + hs + 11))
    bag.flush()
    return h0 + hs + 4.2


def b_corbusier(cx, cy):
    """Villa Savoye — the Five Points: pilotis, free plan, ribbon window, free facade, roof garden."""
    bag = Bag()
    s, z = 19., 3.6
    x0, y0, x1, y1 = cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2
    for a in range(5):
        for b in range(5):
            if a in (0, 4) or b in (0, 4):
                bag(WHITE, mcyl(x0 + 0.6 + a * (s - 1.2) / 4, y0 + 0.6 + b * (s - 1.2) / 4, 0, 0.18, z))
    GF = (64, 96, 76)
    add(box(cx - 5.5, cy - 3.5, 0, cx + 5.5, cy + 6, z - 0.1), GF)
    add(cyl(cx, cy - 3.5, 0, 5.5, z - 0.1), GLASS, mat=GLASSMAT)          # curved glass: the car's turning radius
    for k in range(13):
        m = mbox(cx + 5.45, cy - 3.55, 0, cx + 5.6, cy - 3.45, z - 0.1)
        m.Rotate(math.radians(180 + k * 15), Z, P(cx, cy - 3.5, 0))
        bag(GF, m)
    bag(DGLASS, mbox(cx - 0.8, cy - 9.08, 0, cx + 0.8, cy - 8.9, 2.4))
    car(cx - 7.6, cy + 1, 90)                                              # the Voisin under the pilotis
    add(box(x0, y0, z, x1, y1, z + 1.1), WHITE)                            # piano nobile
    add(box(x0 + 0.12, y0 + 0.12, z + 1.1, x1 - 0.12, y1 - 0.12, z + 2.3), DGLASS)
    add(box(x0, y0, z + 2.3, x1, y1, z + 3.4), WHITE)
    mullion_grid(bag, WHITE, x0 + 0.12, y0 + 0.12, x1 - 0.12, y1 - 0.12, z + 1.1, z + 2.3, 'NSEW', 1.25, t=0.06, d=0.12)
    zt = z + 3.4
    for pts in ([P(cx - 6, cy + 2, zt), P(cx - 3, cy + 6, zt), P(cx + 2, cy + 7, zt), P(cx + 6, cy + 5, zt)],
                [P(cx + 1, cy - 1, zt), P(cx + 4, cy + 1.5, zt), P(cx + 7, cy + 0.5, zt)]):
        crv = rg.Curve.CreateInterpolatedCurve(plist(pts), 3)
        add(rg.Surface.CreateExtrusion(crv, rg.Vector3d(0, 0, 3.2)).ToBrep(), WHITE)
    bag(DGLASS, mbox(cx - 4.2, cy + 5.6, zt + 1.2, cx - 2.6, cy + 6.4, zt + 2.2))      # framed view in the solarium
    for (px, py) in [(-6, -6), (-2, -6), (3, -6), (-7, -1)]:                         # roof-garden planters
        bag((222, 222, 218), mbox(cx + px - 1.5, cy + py - 0.6, zt, cx + px + 1.5, cy + py + 0.6, zt + 0.8))
        for q in (-1, 0, 1):
            bag((84, 140, 70), msph(cx + px + q, cy + py, zt + 1.05, 0.45, 8))
    add(prism_yz([(cy - 8, zt), (cy - 1, zt + 2.4), (cy - 1, zt + 2.7), (cy - 8, zt + 0.3)], cx + 6.5, 1.4), WHITE)
    bag(WHITE, mcyl(cx + 7.5, cy + 6.5, zt, 0.35, 2.0, 10))
    for (tx, ty) in [(-14, 12), (13, 13), (-14, -13), (14, -12)]:
        tree(cx + tx, cy + ty, 10)
    bag.flush()
    return zt + 3.2


def b_wright(cx, cy):
    """Fallingwater — organic architecture: cantilevered trays anchored in a stone core, over the waterfall."""
    bag = Bag()
    CHER, STONEW, STONED = (150, 44, 32), (162, 142, 112), (146, 126, 98)
    add(box(cx - 17, cy - 3.5, -0.1, cx + 17, cy + 2.5, 0.25), WATER, mat=WATERMAT)
    for k in range(4):
        add(box(cx - 16 + k * 0.6, cy - 3.5, 0.25, cx - 15.4 + k * 0.6, cy + 2.5, 1.2 - k * 0.25), WATER, mat=WATERMAT)

    def stone(x0, y0, x1, y1, z0, z1):                      # coursed, rough stone
        zz, k = z0, 0
        while zz < z1 - 0.01:
            hh = min(0.42, z1 - zz)
            off = 0.06 if k % 2 else 0.0
            bag(STONEW if k % 3 else STONED, mbox(x0 - off, y0 - off, zz, x1 + off, y1 + off, zz + hh))
            zz += hh
            k += 1
    stone(cx - 3, cy + 2.5, cx + 5, cy + 9, 0, 3)
    stone(cx + 0.25, cy + 4.25, cx + 3.75, cy + 7.75, 3, 13)      # the hearth / chimney core
    stone(cx + 6.2, cy + 8.2, cx + 7.2, cy + 9.8, 0, 9.8)
    add(box(cx - 17, cy + 2.5, 0, cx - 4, cy + 8, 1.4), (150, 138, 118))
    add(box(cx + 4, cy - 12, 0, cx + 9, cy - 3.5, 1.2), (150, 138, 118))
    TRAY = CREAM
    add(rprism(cx - 11, cy - 7, cx + 6, cy + 6, 3.0, 0.9, 0.8), TRAY)          # cantilever over the falls
    add(rprism(cx - 3, cy - 1, cx + 10, cy + 10, 6.0, 0.9, 0.8), TRAY)         # turned 90°
    add(rprism(cx - 6, cy + 3, cx + 3, cy + 9, 9.0, 0.8, 0.6), TRAY)
    for (gx0, gy0, gz0, gx1, gy1, gz1) in [(cx - 4, cy - 1, 3.9, cx + 4, cy + 6, 6.0),
                                           (cx - 1, cy + 3, 6.9, cx + 6, cy + 9, 9.0)]:
        add(box(gx0, gy0, gz0, gx1, gy1, gz1), GLASS, mat=GLASSMAT)
        mullion_grid(bag, CHER, gx0, gy0, gx1, gy1, gz0, gz1, 'NSEW', 0.9, gz1 - gz0, t=0.07, d=0.06)
    stair(bag, TRAY, (cx - 1.2, cy - 5.6, 0.25), (0, 1, 0), 1.4, 8, 0.45, 0.34)   # hatch stair to the stream
    bag(GLASS, mbox(cx - 2.2, cy - 2.4, 3.9, cx - 0.2, cy - 0.6, 4.6))
    for k in range(7):                                                            # trellis beams
        bag(TRAY, mbox(cx + 3.75, cy + 10.3 + k * 0.9, 8.6, cx + 15, cy + 10.6 + k * 0.9, 8.95))
    bag(TRAY, mbox(cx + 14.2, cy + 10, 8.3, cx + 14.8, cy + 16.2, 8.6))
    for yy in (cy + 10.3, cy + 16):
        bag(STONEW, mbox(cx + 14.2, yy - 0.3, 0, cx + 14.8, yy + 0.3, 8.3))
    r = random.Random(3)
    for k in range(12):
        bag((132, 124, 112), ellipsoid_mesh(cx + r.uniform(-16, 16), cy + r.choice([-1, 1]) * r.uniform(3.5, 6),
                                            0.2, r.uniform(0.6, 1.6), r.uniform(0.5, 1.2), r.uniform(0.4, 0.9)))
    for (tx, ty) in [(-14, 12), (12, 13), (-14, -12), (13, 4), (-9, -14), (2, -14)]:
        tree(cx + tx, cy + ty, 9)
    bag.flush()
    return 13


def b_gropius(cx, cy):
    """Bauhaus Dessau — art and technology: glass curtain workshop, bridge, school wing, studio tower."""
    bag = Bag()
    add(box(cx - 15, cy - 14, 0, cx + 1, cy - 2, 1.2), (96, 96, 100))
    add(box(cx - 15, cy - 14, 1.2, cx + 1, cy - 2, 13), GLASS, mat=GLASSMAT)
    add(box(cx - 15.2, cy - 14.2, 13, cx + 1.2, cy - 1.8, 14), WHITE)
    for zf in (4.8, 8.9):                                                       # slabs behind the curtain wall
        bag(WHITE, mbox(cx - 14.4, cy - 13.4, zf, cx + 0.4, cy - 2.6, zf + 0.3))
    mullion_grid(bag, (40, 42, 46), cx - 15, cy - 14, cx + 1, cy - 2, 1.2, 13, 'NSEW', 1.1, 1.47, t=0.05, d=0.08)
    add(box(cx - 2, cy - 2, 5, cx + 4, cy + 10, 11), WHITE)                     # bridge
    ribbon(bag, cx - 2, cy - 2, cx + 4, cy + 10, 'EW', 6.3, 7.6, 1.2)
    ribbon(bag, cx - 2, cy - 2, cx + 4, cy + 10, 'EW', 8.9, 10.2, 1.2)
    for (px, py) in [(-1.5, 3), (3.5, 3), (-1.5, 8), (3.5, 8)]:
        bag(WHITE, mbox(cx + px - 0.2, cy + py - 0.2, 0, cx + px + 0.2, cy + py + 0.2, 5))
    add(box(cx - 2, cy + 10, 0, cx + 12, cy + 16, 11), WHITE)                   # school wing
    for zb in (1.2, 4.8, 8.2):
        ribbon(bag, cx - 2, cy + 10, cx + 12, cy + 16, 'SN', zb, zb + 1.5, 1.2)
    for i, ch in enumerate("BAUHAUS"):                                          # vertical lettering
        add_text(ch, rg.Plane(P(cx - 2.06, cy + 13.5, 9.4 - i * 1.25), rg.Vector3d(0, -1, 0), Z), 1.0, (25, 25, 25))
    bag(WHITE, mbox(cx + 3, cy + 16, 3.2, cx + 7, cy + 17.2, 3.4))               # entrance canopy
    bag(DGLASS, mbox(cx + 4.2, cy + 15.95, 0, cx + 5.8, cy + 16.05, 2.6))
    add(box(cx + 6, cy - 14, 0, cx + 14, cy - 4, 18), WHITE)                    # Prellerhaus studios
    for z in range(3, 18, 3):
        for y in (cy - 12.5, cy - 9.5, cy - 6.5):
            bag(WHITE, mbox(cx + 14, y - 0.8, z - 0.15, cx + 15, y + 0.8, z))
            railing(bag, STEEL, (cx + 14, y - 0.8), (cx + 15, y - 0.8), z, 0.9, 1.0)
            railing(bag, STEEL, (cx + 15, y - 0.8), (cx + 15, y + 0.8), z, 0.9, 0.8)
            railing(bag, STEEL, (cx + 15, y + 0.8), (cx + 14, y + 0.8), z, 0.9, 1.0)
            bag(DGLASS, mbox(cx + 13.95, y - 0.55, z, cx + 14.05, y + 0.55, z + 2.2))
    window_rows(bag, cx + 6, cy - 14, cx + 14, cy - 4, 'SW', [1.0, 4.0, 7.0, 10.0, 13.0], 2.0, 1.4, 1.4, frame=STEEL, ft=0.06)
    add(box(cx + 1, cy - 8, 0, cx + 6, cy - 4, 5), WHITE)                       # auditorium link
    ribbon(bag, cx + 1, cy - 8, cx + 6, cy - 4, 'S', 3.0, 4.3, 1.0)
    for (tx, ty) in [(-14, 6), (-13, 13), (14, 4), (14, 13)]:
        tree(cx + tx, cy + ty, 9)
    bag.flush()
    return 18


def b_loos(cx, cy):
    """Ornament is crime: bare white volumes; the Raumplan shows as interlocking cubes and roof terraces."""
    bag = Bag()
    FR, RAIL, WOODP = (64, 96, 70), (60, 60, 62), (150, 112, 74)
    add(cbox(cx, cy, 0, 14, 12, 10), WHITE)
    add(box(cx - 7, cy + 6, 0, cx - 1, cy + 9, 6.5), WHITE)
    add(box(cx + 2, cy - 9, 0, cx + 7, cy - 6, 3.5), WHITE)
    add(box(cx - 3, cy - 3, 10, cx + 7, cy + 6, 12.8), WHITE)
    o, u, n, U = face_frame(cx - 7, cy - 6, cx + 7, cy + 6, 'S')
    for (a, zb, ww, wh) in [(1.6, 1.2, 1.2, 1.2), (3.6, 1.2, 1.2, 1.2), (1.6, 5.8, 1.2, 1.2), (4.6, 4.6, 2.8, 1.3), (12.0, 7.4, 1.2, 1.2)]:
        win(bag, o, u, n, a, zb, ww, wh, frame=FR, cross=True)
    for f, specs in [('E', [(3, 2.0), (8, 2.0), (6, 6.4)]), ('W', [(4, 3.0), (9, 7.0)]), ('N', [(3, 1.5), (7, 1.5), (10, 5.5), (5, 7.5)])]:
        o, u, n, U = face_frame(cx - 7, cy - 6, cx + 7, cy + 6, f)
        for (a, zb) in specs:
            win(bag, o, u, n, a, zb, 1.2, 1.2, frame=FR, cross=True)
    o, u, n, U = face_frame(cx - 3, cy - 3, cx + 7, cy + 6, 'S')                   # upper room
    win(bag, o, u, n, 6.5, 10.6, 4.0, 1.3, frame=FR)
    o, u, n, U = face_frame(cx + 2, cy - 9, cx + 7, cy - 6, 'S')                   # entrance
    bag(DWOOD, obox(o, u, UP, n, 1.5, 2.8, 0, 2.4, -0.03, 0.05))
    bag(WHITE, mbox(cx + 3, cy - 10.2, 2.6, cx + 5.4, cy - 9, 2.75))
    for (p0, p1) in [((cx - 7, cy - 6), (cx + 7, cy - 6)), ((cx - 7, cy - 6), (cx - 7, cy + 6)),
                     ((cx - 7, cy + 6), (cx - 3, cy + 6)), ((cx + 7, cy - 6), (cx + 7, cy - 3))]:
        railing(bag, RAIL, p0, p1, 10, 1.0, 1.2)
    railing(bag, RAIL, (cx - 7, cy + 9), (cx - 1, cy + 9), 6.5, 1.0, 1.2)
    for (px, py) in [(-6.6, -5.6), (-6.6, 5.6), (-3.4, -5.6), (-3.4, 5.6)]:          # pergola
        bag(WOODP, mbox(cx + px - 0.1, cy + py - 0.1, 10, cx + px + 0.1, cy + py + 0.1, 12.6))
    for yy in [cy - 5.6 + k * 0.8 for k in range(15)]:
        bag(WOODP, mbox(cx - 6.8, yy - 0.06, 12.6, cx - 3.2, yy + 0.06, 12.75))
    for (px, py) in [(1, 4.5), (5, 4.5)]:
        bag(WHITE, mbox(cx + px - 0.4, cy + py - 0.4, 12.8, cx + px + 0.4, cy + py + 0.4, 14.2))
    bag(WHITE, mbox(cx - 15, cy - 15.3, 0, cx + 1.5, cy - 15, 1.2))                # garden wall with gate
    bag(WHITE, mbox(cx + 4.5, cy - 15.3, 0, cx + 15, cy - 15, 1.2))
    stair(bag, WHITE, (cx + 3, cy - 15, 0), (0, 1, 0), 2.4, 2, 0.4, 0.12)
    for (tx, ty) in [(-12, -11), (12, 10), (-12, 12), (13, -12)]:
        tree(cx + tx, cy + ty, 9)
    bag.flush()
    return 12.8


def b_venturi(cx, cy):
    """Vanna Venturi House — complexity and contradiction: a split gable, applied arch, and a decorated shed."""
    bag = Bag()
    w, d, h = 18., 9., 4.
    yb = cy + 2
    WALLV, FAC = (232, 222, 202), (238, 230, 214)
    add(cbox(cx, yb, 0, w, d, h), WALLV)
    add(prism_yz([(yb - d / 2 - 0.3, h), (yb + d / 2 + 0.3, h), (yb, h + 3.5)], cx - w / 2 - 0.3, w + 0.6), (110, 110, 112))
    yf = yb - d / 2 - 0.6
    add(prism_xz([(cx - w / 2 - 1, 0), (cx - 0.6, 0), (cx - 0.6, h + 4.8), (cx - w / 2 - 1, h + 0.6)], yf, 0.4), FAC)
    add(prism_xz([(cx + 0.6, 0), (cx + w / 2 + 1, 0), (cx + w / 2 + 1, h + 0.6), (cx + 0.6, h + 4.8)], yf, 0.4), FAC)
    add(cbox(cx, yb + 1, 0, 2.2, 1.4, h + 6.5), WALLV)                             # chimney through the split
    add(cbox(cx, yb + 1, h + 6.5, 2.6, 1.8, 0.25), FAC)
    for (xa, xb) in [(cx - w / 2 - 1, cx - 0.6), (cx + 0.6, cx + w / 2 + 1)]:      # string course moulding
        bag(FAC, mbox(xa, yf - 0.16, h - 0.25, xb, yf, h))
    add_pipe(rg.Arc(rg.Plane(P(cx, yf - 0.1, 2.4), rg.Vector3d.XAxis, Z), 2.6, math.pi).ToNurbsCurve(), 0.12, FAC)
    bag(DGLASS, mbox(cx - 0.6, yf + 0.1, 0, cx + 0.6, yf + 0.5, 2.3))
    o, u, n = (cx - w / 2 - 1, yf, 0), (1, 0, 0), (0, -1, 0)
    for a in (3.0, 4.6):                                                           # square windows, left
        for zb in (0.9, 2.4):
            win(bag, o, u, n, a, zb, 1.1, 1.1, frame=WHITE)
    win(bag, o, u, n, 15.3, 1.3, 5.6, 1.1, frame=WHITE)                            # ribbon window, right
    for a in (13.9, 15.3, 16.7):
        bag(WHITE, obox(o, u, UP, n, a - 0.05, a + 0.05, 1.3, 2.4, 0, 0.08))
    lun = pline([P(cx + 1.6 * math.cos(math.pi * k / 12.), yb + d / 2 + 0.03, 2.0 + 1.6 * math.sin(math.pi * k / 12.))
                 for k in range(13)])                                              # rear lunette
    bag(DGLASS, rg.Mesh.CreateFromPlanarBoundary(lun, rg.MeshingParameters.Default, TOL))
    for xp in (cx + 3, cx + 14.5):                                                  # the decorated-shed sign
        add(cyl(xp, cy - 13, 0, 0.22, 8), STEEL)
    add(box(cx + 2, cy - 13.2, 8, cx + 15.5, cy - 12.8, 11), (232, 60, 60))
    add_text("I AM A MONUMENT", rg.Plane(P(cx + 2.5, cy - 13.3, 8.9), rg.Vector3d.XAxis, Z), 1.15, (255, 255, 255))
    xb_ = cx + 2.2
    while xb_ < cx + 15.4:
        for zz in (8.15, 10.85):
            bag(YELLOW, msph(xb_, cy - 13.3, zz, 0.11, 6))
        xb_ += 0.55
    dx, dy = cx - 12, cy - 11                                                       # ...and the duck it is not
    bag((246, 246, 240), ellipsoid_mesh(dx, dy, 0.9, 1.7, 0.95, 0.85))
    bag((246, 246, 240), msph(dx + 1.4, dy, 2.0, 0.6))
    bag((240, 160, 40), pyramid([P(dx + 1.9, dy - 0.2, 1.85), P(dx + 1.9, dy + 0.2, 1.85), P(dx + 1.9, dy, 2.1)],
                                P(dx + 2.6, dy, 1.95)))
    for sy in (-1, 1):
        bag((20, 20, 20), msph(dx + 1.85, dy + sy * 0.32, 2.15, 0.07, 6))
    for (tx, ty) in [(-13, 12), (13, 13), (8, -6)]:
        tree(cx + tx, cy + ty, 9)
    bag.flush()
    return 11


def b_gaudi(cx, cy):
    """'The straight line belongs to men, the curved line to God' — undulating facade, wavy iron balconies,
    parabolic arches, dragon-back roof, chimney warriors, mosaic spires and a trencadís bench."""
    bag = Bag()
    CREAMG, IRON = (226, 202, 162), (58, 56, 54)
    pts = []
    for k in range(36):
        a = 2 * math.pi * k / 36
        r = 13 + 1.6 * math.sin(5 * a) + 0.8 * math.cos(3 * a)
        pts.append(P(cx + r * math.cos(a), cy + 0.8 * r * math.sin(a), 0))
    crv = rg.Curve.CreateInterpolatedCurve(plist(pts), 3, rg.CurveKnotStyle.ChordPeriodic)
    b = rg.Surface.CreateExtrusion(crv, rg.Vector3d(0, 0, 7)).ToBrep()
    add(b.CapPlanarHoles(TOL) or b, CREAMG)
    dom = crv.Domain
    samples = [crv.PointAt(dom.ParameterAt(k / 72.)) for k in range(72)]

    def scaled(p, s, z):
        return P(cx + (p.X - cx) * s, cy + (p.Y - cy) * s, z)
    for zf in (2.3, 4.6):
        c1 = crv.DuplicateCurve(); c1.Translate(rg.Vector3d(0, 0, zf))
        c2 = crv.DuplicateCurve(); c2.Transform(rg.Transform.Scale(P(cx, cy, 0), 1.08)); c2.Translate(rg.Vector3d(0, 0, zf))
        for lb in loft([c1, c2]) or []:
            add(lb, (214, 190, 150))
        rail = [scaled(p, 1.08, zf + 0.85 + 0.2 * math.sin(16 * math.pi * k / 72.)) for k, p in enumerate(samples)]
        add_pipe(rg.Curve.CreateInterpolatedCurve(plist(rail), 3, rg.CurveKnotStyle.ChordPeriodic), 0.07, IRON)
        for k in range(0, 72, 3):
            p = scaled(samples[k], 1.08, zf)
            bag(IRON, mcyl(p.X, p.Y, zf, 0.03, 0.85 + 0.2 * math.sin(16 * math.pi * k / 72.), 5))
    for zc in (1.2, 3.5, 5.8):                                                    # organic oval windows
        for k in range(0, 72, 4):
            p = samples[(k + (2 if zc == 3.5 else 0)) % 72]
            bag((72, 64, 56), ellipsoid_mesh(p.X, p.Y, zc, 0.65, 0.65, 0.95))
    for k in range(6):                                                            # parabolic attic arches
        x = cx - 7.5 + k * 3
        arc_pts = [P(x, cy + y, 7 + 4.5 * (1 - (y / 4.) ** 2)) for y in [-4, -3, -2, -1, 0, 1, 2, 3, 4]]
        for p in pipe(arc_pts, 0.35) or []:
            add(p, (236, 226, 200))
    dragon = [P(cx + x, cy - 7 + 0.8 * math.sin(x * 0.5), 7.4 + 0.5 * math.sin(x * 0.9)) for x in range(-9, 10, 2)]
    for p in pipe(dragon, 0.9) or []:                                             # dragon-back ridge
        add(p, (70, 140, 128))
    scale_cols = [(220, 120, 40), (60, 90, 170), (46, 150, 120), (200, 60, 90)]
    for i, p in enumerate(dragon[:-1]):
        for t in (0.0, 0.5):
            q = P(p.X + (dragon[i + 1].X - p.X) * t, p.Y + (dragon[i + 1].Y - p.Y) * t, p.Z + (dragon[i + 1].Z - p.Z) * t + 0.85)
            bag(scale_cols[(i * 2 + int(t * 2)) % 4], msph(q.X, q.Y, q.Z, 0.32, 8))
    for (wx, wy) in [(-11, 2), (11, 2), (-10, -4), (10, -4)]:                      # chimney 'warriors'
        zz = 7.0
        for k in range(7):
            sz = 1.3 - k * 0.12
            m = mbox(cx + wx - sz / 2, cy + wy - sz / 2, zz, cx + wx + sz / 2, cy + wy + sz / 2, zz + 0.45)
            m.Rotate(math.radians(k * 13), Z, P(cx + wx, cy + wy, 0))
            bag((236, 232, 222) if k % 2 else (196, 210, 200), m)
            zz += 0.45
        bag((46, 150, 120), msph(cx + wx, cy + wy, zz + 0.35, 0.5, 8))
    mosaic = [(46, 140, 120), (220, 120, 40), (60, 90, 170), (200, 60, 90)]
    for i, (dx, dy, hh) in enumerate([(-6, 6, 26), (-2, 8, 30), (2, 8, 30), (6, 6, 26)]):
        add(cone(cx + dx, cy + dy, 7, 1.6, hh - 7), (206, 172, 124))
        add(sph(cx + dx, cy + dy, hh + 0.6, 0.9), mosaic[i])
        for zz in range(10, int(hh) - 3, 3):                                       # spire openings
            rr = 1.6 * (1 - (zz - 7) / (hh - 7.))
            bag((90, 70, 50), ellipsoid_mesh(cx + dx, cy + dy - rr, zz, 0.25, 0.18, 0.6, 6))
    bench = [P(cx + x, cy - 14.5 + 1.2 * math.sin(x * 0.6), 0.45) for x in [-13 + k * 1.0 for k in range(27)]]
    for i in range(4):                                                              # trencadís serpentine bench
        seg = bench[i * 6:i * 6 + 8]
        for p in pipe(seg, 0.45) or []:
            add(p, mosaic[i])
    for (tx, ty) in [(-15, 13), (15, 13), (-15, -10), (15, -10)]:
        tree(cx + tx, cy + ty, 9)
    bag.flush()
    return 31


def b_hadid(cx, cy):
    """'There are 360 degrees, why stick to one?' — one fluid, twisting skin flowing out into the landscape."""
    def ring_curves(grow_r=0.0, rz_fun=None, zc_fun=None):
        cs = []
        for k in range(9):
            t = k / 8.
            x = cx - 15 + 30 * t
            y = cy + 6 * math.sin(t * math.pi * 1.3 - 0.6)
            ry = 4 + grow_r + 3 * math.sin(t * math.pi)
            rz = rz_fun(t)
            pl = rg.Plane(P(x, y, zc_fun(t)), rg.Vector3d.YAxis, Z)
            pl.Rotate(0.45 * math.sin(t * math.pi * 2), pl.ZAxis)
            cs.append(rg.Ellipse(pl, ry, rz).ToNurbsCurve())
        return cs
    shell_rz = lambda t: 1.8 + 6 * math.sin(t * math.pi) ** 1.5
    for b in loft(ring_curves(0, shell_rz, shell_rz)) or []:
        add(b.CapPlanarHoles(TOL) or b, WHITE)
        f = b.Faces[0]
        du, dv = f.Domain(0), f.Domain(1)
        for k in range(24):                                                       # panel joint lines
            c = f.IsoCurve(1, du.ParameterAt(k / 24.))
            if c:
                add(c, (170, 172, 178))
        for k in range(1, 16):
            c = f.IsoCurve(0, dv.ParameterAt(k / 16.))
            if c:
                add(c, (170, 172, 178))
    for b in loft(ring_curves(0.08, lambda t: 0.6 + 2.5 * math.sin(t * math.pi),
                              lambda t: shell_rz(t) - 0.3)) or []:
        add(b, DGLASS)                                                            # sweeping glass band
    for k, off in enumerate([-10.5, -9.0, 8.6, 10.0, 11.4]):                       # flowing ground ribbons / benches
        p1, p2 = [], []
        for i in range(13):
            t = i / 12.
            x = cx - 16 + 32 * t
            yy = cy + 6 * math.sin(t * math.pi * 1.3 - 0.6) + off * (0.85 + 0.15 * math.sin(math.pi * t))
            yy = max(cy - 16.3, min(cy + 15.6, yy))
            zz = 0.04 + 0.42 * max(0, math.sin(2 * math.pi * t * 1.5 + k))
            p1.append(P(x, yy, zz))
            p2.append(P(x, yy + 0.7, zz))
        for b in loft([rg.Curve.CreateInterpolatedCurve(plist(p1), 3), rg.Curve.CreateInterpolatedCurve(plist(p2), 3)]) or []:
            add(b, (234, 234, 232))
    for (tx, ty) in [(-15, 15), (15, -15), (13, 14)]:
        tree(cx + tx, cy + ty, 8)
    return 14


def b_gehry(cx, cy):
    """Deconstructivism — tilted, colliding volumes with scattered windows; a 'Ginger & Fred' pair,
    a crumpled metal sail and Gehry's fish."""
    bag = Bag()
    r = random.Random(11)
    cols = [(192, 196, 202), (170, 176, 186), (206, 200, 190), (150, 160, 176), (214, 182, 142)]
    for k in range(8):
        w, d, h = r.uniform(5, 10), r.uniform(5, 10), r.uniform(6, 18)
        x, y = cx + r.uniform(-8, 8), cy + r.uniform(-8, 8)
        az, ax, ay = r.uniform(-35, 35), r.uniform(-12, 12), r.uniform(-12, 12)
        b = cbox(x, y, 0, w, d, h)
        wm = rg.Mesh()
        for f in 'SE':
            o, u, n, U = face_frame(x - w / 2, y - d / 2, x + w / 2, y + d / 2, f)
            for q in range(r.randint(3, 6)):
                ww, wh = r.uniform(0.8, 2.4), r.uniform(0.8, 2.0)
                a = r.uniform(ww / 2 + 0.3, U - ww / 2 - 0.3)
                zb = r.uniform(1.0, max(1.1, h - wh - 0.6))
                wm.Append(obox(o, u, UP, n, a - ww / 2, a + ww / 2, zb, zb + wh, -0.05, 0.06))
        for g in (b, wm):
            g.Rotate(math.radians(az), Z, P(x, y, 0))
            g.Rotate(math.radians(ax), rg.Vector3d.XAxis, P(x, y, 0))
            g.Rotate(math.radians(ay), rg.Vector3d.YAxis, P(x, y, 0))
        add(b, r.choice(cols))
        bag(DGLASS, wm)
    curves = []
    for k in range(5):
        z = k * 4.5
        cp = [P(cx - 10 + i * 2.5 + 2 * math.sin(k), cy - 11 + 1.6 * math.sin(i * 0.9 + k),
                z + 1.5 * math.cos(i * 0.7 + k * 1.3)) for i in range(9)]
        curves.append(rg.Curve.CreateInterpolatedCurve(plist(cp), 3))
    for b in loft(curves) or []:
        add(b, (204, 208, 216))
    gx, gy = cx + 11.5, cy + 11.5                                                  # 'Ginger': pinched glass tower
    secs = [(3.0, 3.4, 0), (6.0, 3.0, 0.3), (9.0, 2.2, 0.8), (11.0, 2.0, 0.9), (13.0, 2.6, 0.6), (16.0, 3.1, 0.2), (18.0, 3.3, 0)]
    gc = [rg.Circle(rg.Plane(P(gx + dx, gy, z), Z), rr).ToNurbsCurve() for (z, rr, dx) in secs]
    for b in loft(gc) or []:
        add(b.CapPlanarHoles(TOL) or b, GLASS, mat=GLASSMAT)
    for (z, rr, dx) in secs:
        add_pipe(rg.Circle(rg.Plane(P(gx + dx, gy, z), Z), rr + 0.04).ToNurbsCurve(), 0.07, STEEL)
    for k in range(3):
        a = 2 * math.pi * k / 3
        bag(CONC, mcyl(gx + 2.4 * math.cos(a), gy + 2.4 * math.sin(a), 0, 0.3, 3, 8))
    fx, fy = cx + 11.5, cy + 4.5                                                   # 'Fred': wavy windows
    add(cyl(fx, fy, 0, 3.0, 19), (214, 204, 184))
    for fl in range(6):
        for k in range(14):
            ang = k * 360 / 14.
            zb = 1.5 + fl * 3 + 0.45 * math.sin(math.radians(ang) * 2 + fl)
            m = mbox(fx + 2.95, fy - 0.45, zb, fx + 3.08, fy + 0.45, zb + 1.2)
            m.Rotate(math.radians(ang), Z, P(fx, fy, 0))
            bag(DGLASS, m)
    add(sph(fx, fy, 19, 2.6), (150, 156, 164))
    fishx, fishy = cx - 12, cy + 12                                                # the fish
    bag(CONC, mcyl(fishx, fishy, 0, 0.5, 3.2, 8))
    fc = []
    for k in range(8):
        t = k / 7.
        ry = 0.05 + 0.9 * math.sin(math.pi * t) ** 0.8
        pl = rg.Plane(P(fishx - 3 + 6 * t, fishy, 4.6 + 0.4 * math.sin(2 * math.pi * t)), rg.Vector3d.YAxis, Z)
        fc.append(rg.Ellipse(pl, ry, ry * 1.3).ToNurbsCurve())
    for b in loft(fc) or []:
        add(b, (200, 160, 90))
    bag((200, 160, 90), mesh_from([P(fishx - 2.9, fishy, 4.4), P(fishx - 4.6, fishy, 5.9), P(fishx - 4.6, fishy, 3.0)], [(0, 1, 2)]))
    bag.flush()
    return 20


def geodesic_tris(freq):
    t = (1 + 5 ** 0.5) / 2
    V = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
         (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    a = math.atan2(1, t)
    V = [(x, y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)) for x, y, z in V]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2),
         (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11),
         (6, 2, 10), (8, 6, 7), (9, 8, 1)]

    def norm(v):
        l = math.sqrt(sum(c * c for c in v))
        return tuple(c / l for c in v)
    tris = []
    for (ia, ib, ic) in F:
        A, B, C = V[ia], V[ib], V[ic]
        pts = {}
        for i in range(freq + 1):
            for j in range(freq + 1 - i):
                pts[(i, j)] = norm(tuple(A[q] + (B[q] - A[q]) * i / freq + (C[q] - A[q]) * j / freq for q in range(3)))
        for i in range(freq):
            for j in range(freq - i):
                tris.append((pts[(i, j)], pts[(i + 1, j)], pts[(i, j + 1)]))
                if j < freq - i - 1:
                    tris.append((pts[(i + 1, j)], pts[(i + 1, j + 1)], pts[(i, j + 1)]))
    return V, F, tris


def b_fuller(cx, cy):
    """'Doing more with less': a geodesic dome (most volume, least material) and the mast-hung Dymaxion House."""
    bag = Bag()
    Rr, dx, dy = 12., cx - 4, cy + 3
    _, _, tris = geodesic_tris(3)
    glass, panel = rg.Mesh(), rg.Mesh()
    verts, edges = {}, {}

    def Wp(p):
        return (dx + Rr * p[0], dy + Rr * p[1], max(0.0, Rr * p[2]))
    for idx, tri in enumerate(tris):
        zc = sum(p[2] for p in tri) / 3.
        if zc < -0.08:
            continue
        target = glass if (zc > 0.35 or idx % 3 == 0) else panel
        ids = [target.Vertices.Add(*Wp(p)) for p in tri]
        target.Faces.AddFace(ids[0], ids[1], ids[2])
        keys = [tuple(round(c, 4) for c in p) for p in tri]
        for kk in keys:
            verts[kk] = 1
        for i_, j_ in ((0, 1), (1, 2), (2, 0)):
            edges[tuple(sorted([keys[i_], keys[j_]]))] = 1
    for m_, c_ in ((glass, (226, 232, 236)), (panel, (242, 242, 238))):
        m_.Normals.ComputeNormals()
        add(m_, c_, mat=GLASSMAT if m_ is glass else None)
    for (pa, pb) in edges:                                                         # struts
        A, B = Wp(pa), Wp(pb)
        vec = rg.Vector3d(B[0] - A[0], B[1] - A[1], B[2] - A[2])
        L = vec.Length
        if L > 1e-6:
            bag(STEEL, rg.Mesh.CreateFromCylinder(rg.Cylinder(rg.Circle(rg.Plane(P(*A), vec), 0.07), L), 1, 6))
    for p in verts:                                                                # hubs
        bag(STEEL, msph(*Wp(p), r=0.16, seg=6))
    add(prism_xz([(dx - 1.8, 0), (dx + 1.8, 0), (dx, 3.0)], dy - Rr - 1.6, 3), WHITE)  # entrance portal
    bag(DGLASS, mbox(dx - 0.7, dy - Rr - 1.68, 0, dx + 0.7, dy - Rr - 1.58, 2.0))
    hx, hy, ALU = cx + 10.5, cy - 10.5, (200, 204, 210)                            # Dymaxion House
    add(cyl(hx, hy, 0, 0.35, 9.5), ALU)
    add(cyl(hx, hy, 1.8, 5, 2.8), ALU)
    add(ring(hx, hy, 2.6, 4.98, 5.06, 1.2), DGLASS)
    for k in range(18):
        m = mbox(hx + 5.0, hy - 0.04, 2.6, hx + 5.12, hy + 0.04, 3.8)
        m.Rotate(math.radians(k * 20), Z, P(hx, hy, 0))
        bag(ALU, m)
    add(cone(hx, hy, 4.6, 5.4, 1.6), ALU)
    add(cyl(hx, hy, 6.1, 0.9, 0.7), ALU)
    add(cone(hx, hy, 6.8, 1.1, 0.9), ALU)
    for k in range(8):
        a = 2 * math.pi * k / 8
        add(rg.LineCurve(P(hx, hy, 9.5), P(hx + 5.3 * math.cos(a), hy + 5.3 * math.sin(a), 4.6)), STEEL)
    stair(bag, ALU, (hx, hy - 7.5, 0), (0, 1, 0), 1.0, 6, 0.4, 0.3)
    bag.flush()
    return Rr


def b_kahn(cx, cy):
    """Served & servant spaces, platonic geometry: brick cube with giant circular openings revealing an
    inner concrete wall, teak-panelled windows, servant towers and the Salk water channel."""
    bag = Bag()
    s, h = 20., 15.
    x0, y0, x1, y1 = cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2
    b = cbox(cx, cy, 0, s, s, h)
    cutters = []
    for ang in (0, 180):
        c = rg.Cylinder(rg.Circle(rg.Plane(P(cx, y0 - 1, 8), rg.Vector3d.YAxis), 4.2), 2.6).ToBrep(True, True)
        c.Rotate(math.radians(ang), Z, P(cx, cy, 0))
        cutters.append(c)
    add(difference(b, cutters), BRICK)
    for ang in (0, 180):
        tmp = Bag()
        tmp(CONC, mdisc(P(cx, y0 + 1.55, 8), (0, 1, 0), 4.25, t=0.06))
        tmp(DGLASS, mbox(cx - 1.2, y0 + 1.48, 5.8, cx + 1.2, y0 + 1.56, 10.4))
        tmp(CONC, mbox(cx - 2.8, y0 - 0.02, 4.6, cx + 2.8, y0 + 1.6, 5.0))          # concrete tie beam
        tmp.transform(rg.Transform.Rotation(math.radians(ang), Z, P(cx, cy, 0)))
        bag.merge(tmp)
    for f in 'EW':
        o, u, n, U = face_frame(x0, y0, x1, y1, f)
        for i in range(4):
            a = (i + 0.5) * U / 4
            for zb in (1.2, 5.6, 10.0):
                win(bag, o, u, n, a, zb, 2.4, 2.6, frame=None)
                bag(WOOD, obox(o, u, UP, n, a - 1.2, a + 1.2, zb - 0.9, zb, -0.03, 0.05))   # teak panels
        for zz in (4.4, 8.8, 13.2):
            bag(CONC, obox(o, u, UP, n, 0, U, zz, zz + 0.35, 0, 0.06))
    bag(CONC, mbox(x0 - 0.1, y0 - 0.1, h, x1 + 0.1, y1 + 0.1, h + 0.4))
    for (sx, sy) in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
        tx, ty = cx + sx * s / 2, cy + sy * s / 2
        add(cyl(tx, ty, 0, 2.4, h + 2), CONC)
        m = mbox(tx + 2.35, ty - 0.15, 1.5, tx + 2.46, ty + 0.15, h)
        m.Rotate(math.atan2(sy, sx), Z, P(tx, ty, 0))
        bag(DGLASS, m)
        bag(CONC, mcyl(tx, ty, h + 2, 2.5, 0.3))
    add(box(cx - 8, cy - 17, 0, cx + 8, y0, 0.06), (232, 224, 204))                # travertine plaza
    add(box(cx - 0.4, cy - 17, 0.06, cx + 0.4, y0 - 2.5, 0.12), WATER, mat=WATERMAT)
    bag.flush()
    return h + 2


def b_koolhaas(cx, cy):
    """'Bigness': a continuous loop of program — two towers bridged by a base and an overhanging cantilever,
    wrapped in a structural diagrid that is densest where the forces are greatest."""
    bag = Bag()
    g = (70, 80, 96)
    vols = [(cx - 14, cy - 14, 0, cx + 14, cy - 6, 10), (cx + 6, cy - 6, 0, cx + 14, cy + 14, 10),
            (cx - 14, cy - 14, 10, cx - 6, cy - 6, 34), (cx + 6, cy + 6, 10, cx + 14, cy + 14, 34),
            (cx - 14, cy - 6, 34, cx - 6, cy + 14, 42), (cx - 6, cy + 6, 34, cx + 14, cy + 14, 42),
            (cx - 14, cy - 14, 34, cx - 6, cy - 6, 42)]
    for (a0, b0, z0, a1, b1, z1) in vols:
        add(box(a0, b0, z0, a1, b1, z1), g)
        diagrid(bag, (198, 200, 204), a0, b0, a1, b1, z0, z1, 'NSEW', 3.0 if z0 == 0 else 4.5, w=0.3, d=0.1)
    bag(GLASS, mbox(cx - 13.5, cy + 6.5, 33.9, cx - 6.5, cy + 13.5, 34.0))         # glass floor in the overhang
    bag(STEEL, mbox(cx - 4, cy - 16.5, 4.0, cx + 4, cy - 14, 4.25))
    bag(DGLASS, mbox(cx - 3, cy - 14.12, 0, cx + 3, cy - 14.05, 3.5))
    add(box(cx - 16.5, cy - 16.5, 0, cx + 16.5, cy + 16.5, 0.05), PAVING)
    bag.flush()
    return 42


def b_ando(cx, cy):
    """Light, concrete and void: the Church of Light — a cross of light cut into fair-faced concrete
    (form-tie holes and panel joints), the slicing wall, and the cross on the water."""
    bag = Bag()
    CON = (186, 186, 182)
    L, W, H = 18., 7., 8.
    x0, y0 = cx - 6, cy - 6.5
    add(box(x0, y0, 0, x0 + L, y0 + 0.4, H), CON)
    add(box(x0, y0 + W - 0.4, 0, x0 + L, y0 + W, H), CON)
    add(box(x0, y0, H, x0 + L, y0 + W, H + 0.4), CON)
    add(box(x0 + L - 0.4, y0, 0, x0 + L, y0 + W, H), CON)
    ymid = y0 + W / 2
    wall = box(x0, y0, 0, x0 + 0.4, y0 + W, H)
    cut = [box(x0 - 1, ymid - 0.2, 0.8, x0 + 1, ymid + 0.2, H - 0.8),
           box(x0 - 1, ymid - 2.4, H * 0.62 - 0.2, x0 + 1, ymid + 2.4, H * 0.62 + 0.2)]
    add(difference(wall, cut), CON)
    bag(GLASS, mbox(x0 + 0.18, ymid - 0.2, 0.8, x0 + 0.22, ymid + 0.2, H - 0.8))
    bag(GLASS, mbox(x0 + 0.18, ymid - 2.4, H * 0.62 - 0.2, x0 + 0.22, ymid + 2.4, H * 0.62 + 0.2))

    def formwork(bg, o, u, n, U, z1, skip=None):
        JOINT, HOLE = (152, 152, 149), (98, 98, 100)
        b_ = 0.9
        while b_ < z1 - 0.05:
            bg(JOINT, obox(o, u, UP, n, 0, U, b_ - 0.012, b_ + 0.012, 0, 0.012))
            b_ += 0.9
        a_ = 1.8
        while a_ < U - 0.05:
            bg(JOINT, obox(o, u, UP, n, a_ - 0.012, a_ + 0.012, 0, z1, 0, 0.012))
            a_ += 1.8
        for i in range(int(U / 1.8) + 1):
            for j in range(int(z1 / 0.9) + 1):
                for (da, db) in [(0.3, 0.225), (0.9, 0.225), (1.5, 0.225), (0.3, 0.675), (0.9, 0.675), (1.5, 0.675)]:
                    a, b = i * 1.8 + da, j * 0.9 + db
                    if a > U - 0.1 or b > z1 - 0.1 or (skip and skip(a, b)):
                        continue
                    bg(HOLE, obox(o, u, UP, n, a - 0.04, a + 0.04, b - 0.04, b + 0.04, 0, 0.02))
    for f in 'SNE':
        o, u, n, U = face_frame(x0, y0, x0 + L, y0 + W, f)
        formwork(bag, o, u, n, U, H)
    o, u, n, U = face_frame(x0, y0, x0 + L, y0 + W, 'W')
    formwork(bag, o, u, n, U, H, skip=lambda a, b: (abs(a - W / 2) < 0.45) or (abs(b - H * 0.62) < 0.45 and abs(a - W / 2) < 2.7))
    add(cbox(cx + 1, cy - 3, 0, 18, 0.4, H - 1.5, rot=15), CON)                    # wall slicing at 15°
    tmp = Bag()
    for (yy, nn) in [(cy - 3.2, (0, -1, 0)), (cy - 2.8, (0, 1, 0))]:
        if nn[1] < 0:
            formwork(tmp, (cx - 8, yy, 0), (1, 0, 0), nn, 18, H - 1.5)
        else:
            formwork(tmp, (cx + 10, yy, 0), (-1, 0, 0), nn, 18, H - 1.5)
    tmp.transform(rg.Transform.Rotation(math.radians(15), Z, P(cx + 1, cy - 3, 0)))
    bag.merge(tmp)
    add(box(cx - 16, cy + 5, -0.05, cx + 12, cy + 16, 0.12), WATER, mat=WATERMAT)  # the water court
    add(cbox(cx - 4, cy + 11, 0, 0.35, 0.35, 6), STEEL)
    add(cbox(cx - 4, cy + 11, 4.2, 2.8, 0.35, 0.35), STEEL)
    for k in range(3):
        add(box(cx - 16, cy + 3.2 + k * 0.6, 0.12 + (2 - k) * 0.3, cx + 12, cy + 3.8 + k * 0.6, 0.42 + (2 - k) * 0.3), CON)
    add(box(cx - 16.5, cy + 4.5, 0, cx - 16.1, cy + 16.5, 3), CON)
    add(box(cx - 16.5, cy + 16.1, 0, cx + 12, cy + 16.5, 3), CON)
    bag(CON, mbox(cx + 13, cy - 14, 0, cx + 16, cy - 13.4, 0.45))
    bag.flush()
    return H + 0.4


def b_rossi(cx, cy):
    """Typology: the Teatro del Mondo floating on its barge, and the Gallaratese portico of thin piers."""
    bag = Bag()
    BLUE, WOODY = (60, 90, 150), (232, 196, 92)
    tx, ty = cx - 5, cy - 0.5
    add(box(cx - 16.5, cy - 10.5, -0.05, cx + 2, cy + 8.5, 0.12), WATER, mat=WATERMAT)
    add(box(tx - 6.5, ty - 8.5, -0.2, tx + 6.5, ty + 6.5, 0.9), (70, 56, 44))       # barge
    zb = 0.9
    add(cbox(tx, ty, zb, 10, 10, 12), WOODY)
    for z in (zb + 4, zb + 8, zb + 11.6):
        bag(BLUE, mbox(tx - 5.05, ty - 5.05, z, tx + 5.05, ty + 5.05, z + 0.35))
    for (sx, sy) in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
        bag(BLUE, mbox(tx + sx * 5 - 0.2, ty + sy * 5 - 0.2, zb, tx + sx * 5 + 0.2, ty + sy * 5 + 0.2, zb + 12))
    window_rows(bag, tx - 5, ty - 5, tx + 5, ty + 5, 'NEW', [zb + 1.5, zb + 5.5, zb + 9.0], 3.3, 1.2, 1.6, frame=WHITE, cross=True)
    add(prism(ngon(tx, ty, 4.2, 8, 22.5), zb + 12, 4), WOODY)
    for k in range(8):
        a = math.radians(22.5 + 45 * k + 22.5)
        rr = 4.2 * math.cos(math.radians(22.5))
        m = mbox(tx + rr - 0.05, ty - 0.45, zb + 13.2, tx + rr + 0.06, ty + 0.45, zb + 14.6)
        m.Rotate(a, Z, P(tx, ty, 0))
        bag(DGLASS, m)
    add(pyramid([P(x, y, zb + 16) for x, y in ngon(tx, ty, 4.6, 8, 22.5)], P(tx, ty, zb + 19.5)), BLUE)
    add(cyl(tx, ty, zb + 19.5, 0.08, 3), STEEL)
    add(sph(tx, ty, zb + 19.8, 0.45), GOLD)
    add(box(tx, ty - 0.03, zb + 21.5, tx + 1.8, ty + 0.03, zb + 22.5), RED)
    for sx in (-1, 1):                                                             # flanking stair towers
        x = tx + sx * 3.2
        add(box(x - 1.2, ty - 7.6, zb, x + 1.2, ty - 5, zb + 15), WOODY)
        add(pyramid([P(x - 1.4, ty - 7.8, zb + 15), P(x + 1.4, ty - 7.8, zb + 15), P(x + 1.4, ty - 4.8, zb + 15),
                     P(x - 1.4, ty - 4.8, zb + 15)], P(x, ty - 6.3, zb + 17.5)), BLUE)
        for z in range(3, 14, 3):
            bag(DGLASS, mbox(x - 0.15, ty - 7.66, zb + z, x + 0.15, ty - 7.55, zb + z + 1.6))
    PINK = (226, 192, 172)
    add(box(cx + 3, cy - 16, 4, cx + 9, cy + 16, 11), PINK)                         # Gallaratese bar
    for y in range(-16, 11, 2):
        bag(PINK, mbox(cx + 3.1, cy + y - 0.15, 0, cx + 8.9, cy + y + 0.15, 4))
    for yy in (cy + 12.5, cy + 15):
        for xx in (cx + 4.5, cx + 7.5):
            bag(PINK, mcyl(xx, yy, 0, 0.75, 4))
    window_rows(bag, cx + 3, cy - 16, cx + 9, cy + 16, 'E', [5.4, 8.4], 2.0, 1.1, 1.1, frame=WHITE, cross=True)
    window_rows(bag, cx + 3, cy - 16, cx + 9, cy + 16, 'W', [8.2], 2.6, 1.0, 1.8, frame=WHITE)
    bag(PINK, mbox(cx + 1.8, cy - 16, 7.4, cx + 3, cy + 16, 7.6))                  # gallery (ballatoio)
    railing(bag, STEEL, (cx + 1.85, cy - 16), (cx + 1.85, cy + 16), 7.6, 1.0, 1.6)
    bag.flush()
    return 22


def b_kurokawa(cx, cy):
    """Metabolism: replaceable capsules plugged into service cores — a crane is delivering a new one."""
    bag = Bag()
    r = random.Random(5)
    CAP, RIM = (236, 236, 232), (206, 206, 200)
    for (kx, ky, hh, banned) in [(cx - 5, cy, 40, 0), (cx + 5, cy + 2, 34, 2)]:
        add(cbox(kx, ky, 0, 4, 4, hh), CONC)
        for f in 'SN':
            o, u, n, U = face_frame(kx - 2, ky - 2, kx + 2, ky + 2, f)
            bag(DGLASS, obox(o, u, UP, n, 1.7, 2.3, 3.4, hh - 1, -0.03, 0.03))
        bag(CONC, mbox(kx - 1.5, ky - 1.5, hh, kx + 1.5, ky + 1.5, hh + 1.5))
        bag(STEEL, mcyl(kx + 1, ky + 1, hh, 0.4, 2.5, 8))
        for fl in range(int((hh - 5) / 2.6)):
            z = 3.4 + fl * 2.6
            sides = [s_ for s_ in [0, 1, 2, 3] if s_ != banned]
            for side in r.sample(sides, r.choice([2, 3])):
                off = r.uniform(-0.8, 0.8)
                tmp = Bag()
                tmp(CAP, mbox(kx + 2.0, ky + off - 1.2, z, kx + 6.0, ky + off + 1.2, z + 2.4))
                tmp(RIM, mdisc(P(kx + 6.0, ky + off, z + 1.2), (1, 0, 0), 0.75, t=0.05))
                tmp(DGLASS, mdisc(P(kx + 6.0, ky + off, z + 1.2), (1, 0, 0), 0.6, t=0.09))
                tmp((150, 150, 150), mbox(kx + 3.98, ky + off - 1.22, z, kx + 4.02, ky + off + 1.22, z + 2.42))
                tmp.transform(rg.Transform.Rotation(math.radians(side * 90), Z, P(kx, ky, 0)))
                bag.merge(tmp)
    add(box(cx - 3, cy - 1.5, 0, cx + 3, cy + 3.5, 3.2), GLASS, mat=GLASSMAT)        # glazed lobby
    mullion_grid(bag, STEEL, cx - 3, cy - 1.5, cx + 3, cy + 3.5, 0, 3.2, 'SN', 1.2, 3.2, t=0.06, d=0.06)
    YEL = (230, 180, 40)                                                           # tower crane
    mx, my, mh = cx + 12, cy - 12, 44.
    for (sx, sy) in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
        bag(YEL, mbox(mx + sx * 0.7 - 0.08, my + sy * 0.7 - 0.08, 0, mx + sx * 0.7 + 0.08, my + sy * 0.7 + 0.08, mh))
    for f in 'SE':
        o, u, n, U = face_frame(mx - 0.7, my - 0.7, mx + 0.7, my + 0.7, f)
        zz = 0.0
        while zz < mh - 1.4:
            strip(bag, YEL, (o[0], o[1], zz), u, n, (0, 0), (U, 1.4), 0.08, 0.06)
            zz += 1.4
    dv = (cx + 5 - mx, cy + 2 - my)
    dl = math.hypot(*dv)
    du = (dv[0] / dl, dv[1] / dl, 0)
    dn = (du[1], -du[0], 0)
    top = (mx, my, mh)
    bag(YEL, obox(top, du, UP, dn, -6, 20, 0, 1.2, -0.6, 0.6))
    bag(CONC, obox(top, du, UP, dn, -6, -3.5, -1.6, 0, -0.8, 0.8))
    bag(YEL, obox(top, du, UP, dn, -0.9, 0.9, -2.2, 0, -0.9, 0.9))
    hp = (mx + du[0] * 11, my + du[1] * 11)
    add(rg.LineCurve(P(hp[0], hp[1], mh), P(hp[0], hp[1], 38.4)), STEEL)
    hang = (hp[0], hp[1], 36.0)
    bag(CAP, obox(hang, du, UP, dn, -2, 2, 0, 2.4, -1.2, 1.2))
    bag(DGLASS, mdisc(pt(hang, du, UP, dn, 2, 1.2, 0), du, 0.6, t=0.09))
    bag.flush()
    return 40


def b_eisenman(cx, cy):
    """Autonomy of form (House VI): two shifted grids, a glass slot that splits the house, a column that
    hangs instead of supporting, and a red stair mirrored by an unusable upside-down green one."""
    bag = Bag()
    GREY = (126, 130, 140)

    def frame(ox, oy, n, sp, h, t, col):
        for a in range(n + 1):
            for b in range(n + 1):
                bag(col, mbox(ox + a * sp - t, oy + b * sp - t, 0, ox + a * sp + t, oy + b * sp + t, h))
        for a in range(n + 1):
            bag(col, mbox(ox + a * sp - t, oy - t, h - 2 * t, ox + a * sp + t, oy + n * sp + t, h))
            bag(col, mbox(ox - t, oy + a * sp - t, h - 2 * t, ox + n * sp + t, oy + a * sp + t, h))
    add(box(cx - 9, cy - 9, 0, cx + 9, cy + 9, 0.15), (222, 222, 222))
    frame(cx - 7.5, cy - 7.5, 3, 5., 7., 0.2, WHITE)
    frame(cx - 5., cy - 5., 3, 5., 10., 0.15, GREY)
    add(box(cx - 7.5, cy - 7.5, 0.15, cx - 0.15, cy - 2.5, 7), WHITE)
    add(box(cx - 2.5, cy + 2.5, 3.5, cx + 7.5, cy + 7.5, 7), (190, 192, 198))
    add(box(cx - 7.5, cy - 2.5, 3.4, cx + 2.5, cy + 7.5, 3.6), WHITE)
    add(box(cx - 7.5, cy - 7.5, 7, cx - 0.15, cy + 7.5, 7.25), (232, 232, 232))
    add(box(cx + 0.15, cy - 7.5, 7, cx + 7.5, cy + 7.5, 7.25), (232, 232, 232))
    bag(GLASS, mbox(cx - 0.15, cy - 7.5, 7.0, cx + 0.15, cy + 7.5, 7.25))          # roof slot
    add(box(cx + 0.15, cy - 7.6, 0.15, cx + 7.5, cy - 7.4, 7), WHITE)
    bag(GLASS, mbox(cx - 0.15, cy - 7.6, 0.15, cx + 0.15, cy - 7.4, 7))            # wall slot
    o, u, n, U = face_frame(cx + 0.15, cy - 7.6, cx + 7.5, cy - 7.4, 'S')
    for (a, zb, ww, wh) in [(1.6, 1.0, 1.6, 2.2), (4.9, 4.4, 3.0, 1.0), (6.6, 0.5, 0.6, 5.5)]:
        win(bag, o, u, n, a, zb, ww, wh, frame=None)
    add(box(cx + 2.35, cy - 2.65, 1.1, cx + 2.65, cy - 2.35, 7), GREY)              # the hanging column
    bag(DWOOD, mbox(cx + 1.4, cy - 3.6, 0.75, cx + 3.6, cy - 1.4, 0.82))
    for (tx, ty) in [(1.5, -3.5), (3.5, -3.5), (1.5, -1.5), (3.5, -1.5)]:
        bag(DWOOD, mbox(cx + tx - 0.04, cy + ty - 0.04, 0.15, cx + tx + 0.04, cy + ty + 0.04, 0.75))
    for k in range(10):
        add(box(cx - 7 + k * 0.5, cy + 3, 0, cx - 6.5 + k * 0.5, cy + 4, (k + 1) * 0.6), (200, 50, 45))
        add(box(cx - 7 + k * 0.5, cy + 5, 7 - (k + 1) * 0.6, cx - 6.5 + k * 0.5, cy + 6, 7), (60, 150, 80))
    for (tx, ty) in [(-13, 13), (13, -13), (13, 12)]:
        tree(cx + tx, cy + ty, 9)
    bag.flush()
    return 10


def b_ingels(cx, cy):
    """'Yes is more' — hedonistic sustainability: every flat gets a garden on the roof of the one below;
    the parking beneath wears a picture of Mount Everest."""
    bag = Bag()
    run, rise, n = 3.75, 2., 8
    prof = [(cx - 16, 0)]
    for k in range(n):
        x = cx - 16 + k * run
        prof += [(x, (k + 1) * rise), (x + run, (k + 1) * rise)]
    prof += [(cx + 14, 0)]
    add(prism_xz(prof, cy - 12, 24), WHITE)
    for k in range(n):
        x = cx - 16 + k * run
        zt = (k + 1) * rise
        bag(GRASS, mbox(x, cy - 12, zt, x + 1.6, cy + 12, zt + 0.45))
        for yy in range(-10, 11, 4):
            bag((80, 140, 70), msph(x + 0.8, cy + yy + (k % 2) * 2, zt + 0.95, 0.6, 8))
        bag(GLASS, mbox(x - 0.05, cy - 12, zt, x + 0.01, cy + 12, zt + 1.0))         # glass balustrade
        bag(GLASS, mbox(x - 0.06, cy - 11.6, k * rise + 0.25, x + 0.02, cy + 11.6, zt - 0.15))
        for yy in [cy - 11.6 + q * 2.32 for q in range(11)]:
            bag(STEEL, mbox(x - 0.1, yy - 0.04, k * rise + 0.25, x - 0.03, yy + 0.04, zt - 0.15))
    o, u, n = (cx + 14, cy - 12, 0), (0, 1, 0), (1, 0, 0)                           # Everest mural
    bag((120, 168, 216), obox(o, u, UP, n, 0, 24, 0, 16, 0, 0.03))
    bag((96, 98, 112), mesh_from([pt(o, u, UP, n, a, b, 0.05) for a, b in [(1, 0), (23, 0), (13, 13)]], [(0, 1, 2)]))
    bag((112, 114, 128), mesh_from([pt(o, u, UP, n, a, b, 0.06) for a, b in [(0.5, 0), (10, 0), (5, 8)]], [(0, 1, 2)]))
    bag((250, 250, 250), mesh_from([pt(o, u, UP, n, a, b, 0.07) for a, b in [(10.3, 9.5), (15.4, 9.5), (13, 13)]], [(0, 1, 2)]))
    bag(DGLASS, mbox(cx + 7, cy - 12.08, 0, cx + 11.5, cy - 11.95, 3.2))           # parking entrance
    bag.flush()
    return 17


def b_vitruvius(cx, cy):
    """Firmitas, Utilitas, Venustas: a Doric temple — stylobate, columns with capitals, triglyph frieze,
    pediment with acroteria, and the altar in front."""
    bag = Bag()
    W, Lg = 14., 26.
    for k in range(3):
        add(cbox(cx, cy, k * 0.4, W + 2.4 - k * 0.8, Lg + 2.4 - k * 0.8, 0.4), MARBLE)
    z = 1.2
    pos = set()
    for i in range(6):
        x = cx - W / 2 + 0.8 + i * (W - 1.6) / 5
        pos.add((round(x, 3), round(cy - Lg / 2 + 0.8, 3)))
        pos.add((round(x, 3), round(cy + Lg / 2 - 0.8, 3)))
    for j in range(11):
        y = cy - Lg / 2 + 0.8 + j * (Lg - 1.6) / 10
        pos.add((round(cx - W / 2 + 0.8, 3), round(y, 3)))
        pos.add((round(cx + W / 2 - 0.8, 3), round(y, 3)))
    for (x, y) in pos:
        bag(MARBLE, mcyl(x, y, z, 0.6, 6.9, 20))                                    # shaft
        bag(MARBLE, mcyl(x, y, z + 6.9, 0.48, 0.25, 20))                            # necking
        bag(MARBLE, mcyl(x, y, z + 7.15, 0.74, 0.4, 20))                            # echinus
        bag(MARBLE, mbox(x - 0.82, y - 0.82, z + 7.55, x + 0.82, y + 0.82, z + 8.0))  # abacus
    add(cbox(cx, cy, z, W - 5, Lg - 7, 7.5), (226, 216, 196))
    bag((122, 92, 54), mbox(cx - 1.4, cy - (Lg - 7) / 2 - 0.06, z, cx + 1.4, cy - (Lg - 7) / 2 + 0.02, z + 5))
    add(cbox(cx, cy, z + 8, W, Lg, 0.8), MARBLE)                                    # architrave
    add(cbox(cx, cy, z + 8.8, W - 0.1, Lg - 0.1, 0.8), (232, 226, 214))             # frieze
    for f in 'SNEW':
        o, u, n, U = face_frame(cx - W / 2 + 0.05, cy - Lg / 2 + 0.05, cx + W / 2 - 0.05, cy + Lg / 2 - 0.05, f)
        cnt = int(U / 1.25)
        for i in range(cnt + 1):
            a = i * U / cnt
            bag((196, 188, 168), obox(o, u, UP, n, max(0, a - 0.3), min(U, a + 0.3), z + 8.8, z + 9.6, 0, 0.06))
    add(cbox(cx, cy, z + 9.6, W + 0.8, Lg + 0.8, 0.4), MARBLE)                      # cornice
    add(prism_xz([(cx - W / 2 - 0.4, z + 10), (cx + W / 2 + 0.4, z + 10), (cx, z + 12.8)], cy - Lg / 2 - 0.4, Lg + 0.8), MARBLE)
    for yy in (cy - Lg / 2 - 0.3, cy + Lg / 2 + 0.3):                              # acroteria
        bag(GOLD, mcyl(cx, yy, z + 12.8, 0.25, 0.8, 8))
        bag(GOLD, msph(cx, yy, z + 13.8, 0.4, 8))
        for sx in (-1, 1):
            bag(GOLD, msph(cx + sx * (W / 2 + 0.2), yy, z + 10.4, 0.35, 8))
    add(cbox(cx, cy - Lg / 2 - 2.6, 0, 3, 1.2, 1.1), STONE)                        # altar
    add(cone(cx, cy - Lg / 2 - 2.6, 1.1, 0.4, 0.9), (240, 130, 40))
    bag.flush()
    return z + 13.8


def b_palladio(cx, cy):
    """Villa Rotonda: perfect symmetry and harmonic proportion — four identical temple porticos,
    pedimented windows, statues and a ribbed dome."""
    bag = Bag()
    s, h = 14., 10.
    VW = (240, 228, 205)
    add(cbox(cx, cy, 0, s, s, 1.5), STONE)
    add(cbox(cx, cy, 1.5, s, s, h), VW)
    add(cbox(cx, cy, 11.2, s + 0.6, s + 0.6, 0.35), MARBLE)
    q = s / 2 + 0.5
    add(pyramid([P(cx - q, cy - q, 11.5), P(cx + q, cy - q, 11.5), P(cx + q, cy + q, 11.5), P(cx - q, cy + q, 11.5)],
                P(cx, cy, 14.5)), (152, 140, 130))
    add(cyl(cx, cy, 12.8, 3.6, 1.7), VW)
    add(sph(cx, cy, 14.5, 3.6), (152, 140, 130))
    add(cyl(cx, cy, 17.9, 0.6, 1.2), VW)
    for k in range(8):                                                             # dome ribs
        a = math.radians(k * 45)
        pl = rg.Plane(P(cx, cy, 14.5), rg.Vector3d(math.cos(a), math.sin(a), 0), Z)
        add_pipe(rg.Arc(pl, 3.66, math.pi / 2).ToNurbsCurve(), 0.07, (236, 230, 220))
    x0, y0, x1, y1 = cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2
    for f in 'SNEW':
        o, u, n, U = face_frame(x0, y0, x1, y1, f)
        for a in (1.6, U - 1.6):
            win(bag, o, u, n, a, 3.0, 1.0, 2.4, frame=MARBLE, ft=0.15)               # piano nobile
            bag(MARBLE, tri_prism(o, u, n, [(a - 0.8, 5.55), (a + 0.8, 5.55), (a, 6.15)], 0.15))
            win(bag, o, u, n, a, 8.5, 0.9, 0.8, frame=MARBLE, ft=0.1)                # attic
            win(bag, o, u, n, a, 0.4, 0.8, 0.6, frame=None)                          # basement
        for zz in (0.5, 1.0):
            bag((200, 190, 170), obox(o, u, UP, n, 0, U, zz - 0.03, zz + 0.03, 0, 0.02))
    for ang in (0, 90, 180, 270):
        parts = []
        yf = cy - s / 2
        for k in range(5):
            parts.append(box(cx - 3.5, yf - 9 + k * 0.8, 0, cx + 3.5, yf - 4.6, (k + 1) * 0.3))
        parts.append(box(cx - 4.5, yf - 5, 0, cx + 4.5, yf, 1.5))
        for i in range(6):
            parts.append(cyl(cx - 3.9 + i * 1.56, yf - 4.4, 1.5, 0.35, 6.5))
        parts.append(box(cx - 4.5, yf - 5, 8, cx + 4.5, yf, 8.8))
        parts.append(prism_xz([(cx - 4.5, 8.8), (cx + 4.5, 8.8), (cx, 10.6)], yf - 5, 5))
        for p in parts:
            p.Rotate(math.radians(ang), Z, P(cx, cy, 0))
            add(p, MARBLE)
        tmp = Bag()
        tmp(DWOOD, mbox(cx - 0.9, yf - 0.05, 1.5, cx + 0.9, yf + 0.02, 5.0))
        for (sx_, sz_) in [(0, 10.6), (-4.3, 8.8), (4.3, 8.8)]:                      # statues on the pediment
            tmp(MARBLE, mbox(cx + sx_ - 0.25, yf - 4.95, sz_, cx + sx_ + 0.25, yf - 4.45, sz_ + 0.4))
            tmp(MARBLE, mcyl(cx + sx_, yf - 4.7, sz_ + 0.4, 0.2, 1.1, 8))
            tmp(MARBLE, msph(cx + sx_, yf - 4.7, sz_ + 1.65, 0.16, 6))
        tmp.transform(rg.Transform.Rotation(math.radians(ang), Z, P(cx, cy, 0)))
        bag.merge(tmp)
    bag.flush()
    return 19.5


# ================================================================= PHILOSOPHERS
def platonic(kind, c, r):
    if kind == 'tetra':
        V = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
        F = [(0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2)]
    elif kind == 'octa':
        V = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
        F = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
    else:
        V, F, _ = geodesic_tris(1)
        if kind == 'dodeca':
            cents = [tuple(sum(V[i][q] for i in f) / 3. for q in range(3)) for f in F]
            nV, nF = [], []
            for vi in range(12):
                around = [ci for ci, f in enumerate(F) if vi in f]
                v = V[vi]
                ax = (v[1], -v[0], 0) if abs(v[2]) < 0.9 else (1, 0, 0)
                ay = (v[1] * ax[2] - v[2] * ax[1], v[2] * ax[0] - v[0] * ax[2], v[0] * ax[1] - v[1] * ax[0])
                around.sort(key=lambda ci: math.atan2(sum(cents[ci][q] * ay[q] for q in range(3)),
                                                       sum(cents[ci][q] * ax[q] for q in range(3))))
                base = len(nV)
                for ci in around:
                    nV.append(cents[ci])
                nV.append(tuple(sum(cents[ci][q] for ci in around) / 5. for q in range(3)))
                for k in range(5):
                    nF.append((base + k, base + (k + 1) % 5, base + 5))
            V, F = nV, nF
    pts = []
    for v in V:
        l = math.sqrt(sum(a * a for a in v))
        pts.append(P(c.X + r * v[0] / l, c.Y + r * v[1] / l, c.Z + r * v[2] / l))
    return mesh_from(pts, F)


def b_plato(cx, cy):
    """Theory of Forms: the house is the ideal cube; the other perfect solids stand beside it."""
    add(cbox(cx - 4, cy, 0, 14, 14, 1), MARBLE)
    add(cbox(cx - 4, cy, 1, 11, 11, 11), (248, 248, 248))
    ACC['openings'].Append(mbox(cx - 5, cy - 5.58, 1, cx - 3, cy - 5.45, 4))
    for (y, k) in zip([-10, -3.5, 3, 9.5], ['tetra', 'octa', 'icosa', 'dodeca']):
        add(cyl(cx + 9, cy + y, 0, 1.1, 2), MARBLE)
        add(platonic(k, P(cx + 9, cy + y, 3.6), 1.6), (226, 200, 120))
    return 13


def b_descartes(cx, cy):
    """Cogito ergo sum — the house laid out on the Cartesian x, y, z axes."""
    ox, oy, s = cx - 10, cy - 10, 3.2
    add(cbox(ox, oy, 0, s, s, s), (60, 60, 64))
    for k in range(1, 7):
        add(cbox(ox + k * s, oy, 0, s - 0.2, s - 0.2, s - 0.2), (200, 70 + k * 12, 60))
        add(cbox(ox, oy + k * s, 0, s - 0.2, s - 0.2, s - 0.2), (70, 160 + k * 8, 80))
    for k in range(1, 8):
        add(cbox(ox, oy, k * s, s - 0.2, s - 0.2, s - 0.2), (70, 100, 180 + k * 8))
    for k in range(8):
        add(rg.LineCurve(P(ox + k * s, oy, 0.05), P(ox + k * s, oy + 7 * s, 0.05)), (90, 90, 90))
        add(rg.LineCurve(P(ox, oy + k * s, 0.05), P(ox + 7 * s, oy + k * s, 0.05)), (90, 90, 90))
    return 8 * s


def b_kant(cx, cy):
    """Categorical imperative: one maxim willed as universal law — nine identical houses."""
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            x, y = cx + i * 11, cy + j * 11
            add(cbox(x, y, 0, 7, 7, 4), (236, 232, 226))
            add(profile_roof(x, y, 4, 7.01, 7, 'gable', 3), (98, 98, 104))
            ACC['openings'].Append(mbox(x - 0.5, y - 3.59, 0, x + 0.5, y - 3.45, 2.2))
            for dx in (-2, 2):
                ACC['openings'].Append(mbox(x + dx - 0.5, y - 3.58, 1.2, x + dx + 0.5, y - 3.45, 2.4))
    return 7


def b_bentham(cx, cy):
    """The Panopticon: cells in a ring, all visible from a central watch tower."""
    add(ring(cx, cy, 0, 10, 15, 12), (205, 196, 180))
    for f in range(4):
        for k in range(32):
            m = mbox(cx + 9.9, cy - 0.5, 1 + f * 3, cx + 10.05, cy + 0.5, 2.6 + f * 3)
            m.Rotate(2 * math.pi * k / 32, Z, P(cx, cy, 0))
            ACC['openings'].Append(m)
    add(cyl(cx, cy, 0, 2.5, 14), (205, 196, 180))
    add(cyl(cx, cy, 14, 3.0, 2.5), DGLASS)
    add(cone(cx, cy, 16.5, 3.5, 2.5), SLATE)
    add(cbox(cx, cy - 6.25, 9, 1.4, 7.5, 1.2), (205, 196, 180))
    return 19


def b_heidegger(cx, cy):
    """Building Dwelling Thinking: the Todtnauberg hut, a deep roof sheltering the fourfold."""
    w, d, h = 11., 7., 2.6
    add(cbox(cx, cy, 0, w, d, h), DWOOD)
    add(prism_yz([(cy - d / 2 - 1.2, h - 0.8), (cy + d / 2 + 1.2, h - 0.8), (cy, h + 4.2)], cx - w / 2 - 0.6, w + 1.2),
        (96, 86, 76))
    facade_windows(ACC['openings'], cx - w / 2, cy - d / 2, cx + w / 2, cy + d / 2, 0, h, faces='S', spacing=2.6,
                   ww=0.8, wh=0.9, sill=0.8)
    add(box(cx + 7, cy - 5, 0, cx + 9.5, cy - 4, 0.7), DWOOD)                   # the well
    add(cbox(cx + 7.4, cy - 4.5, 0, 0.3, 0.3, 1.6), DWOOD)
    add(cbox(cx + 7.4, cy - 4.5, 1.6, 0.6, 0.6, 0.6), GOLD)                     # the star-cube
    for (tx, ty) in [(-12, 10), (-8, 13), (11, 10), (13, 3), (-13, -6), (-10, -12), (6, -13)]:
        tree(cx + tx, cy + ty, 11, kind='conifer')
    return 7


def b_wittgenstein(cx, cy):
    """Haus Wittgenstein: logical, austere, exactly proportioned blocks; tall precise windows."""
    col = (228, 218, 196)
    add(box(cx - 8, cy - 5, 0, cx + 6, cy + 6, 11), col)
    add(box(cx + 6, cy - 3, 0, cx + 12, cy + 4, 7.5), col)
    add(box(cx - 12, cy - 2, 0, cx - 8, cy + 4, 5), col)
    add(box(cx - 3, cy + 6, 0, cx + 2, cy + 10, 14), col)
    for x in range(-7, 6, 2):
        for z0 in (1.0, 5.6):
            ACC['openings'].Append(mbox(cx + x - 0.4, cy - 5.07, z0, cx + x + 0.4, cy - 4.93, z0 + 3.4))
    for x in (7, 9, 11):
        ACC['openings'].Append(mbox(cx + x - 0.4, cy - 3.07, 1.0, cx + x + 0.4, cy - 2.93, 4.6))
    return 14


def b_pythagoras(cx, cy):
    """All is number: rooms are Fibonacci squares forming the golden rectangle; the tetractys in front."""
    ox, oy = cx - 10.5, cy - 4.5
    rect = (0., 0., 21., 13.)
    sides = ['L', 'T', 'R', 'B']
    for k, s in enumerate([13, 8, 5, 3, 2, 1, 1]):
        x0, y0, x1, y1 = rect
        sd = sides[k % 4]
        if sd == 'L':
            sq = (x0, y0, x0 + s, y0 + s); rect = (x0 + s, y0, x1, y1)
        elif sd == 'T':
            sq = (x0, y1 - s, x0 + s, y1); rect = (x0, y0, x1, y1 - s)
        elif sd == 'R':
            sq = (x1 - s, y0, x1, y0 + s); rect = (x0, y0, x1 - s, y1)
        else:
            sq = (x0, y0, x0 + s, y0 + s); rect = (x0, y0 + s, x1, y1)
        t = k / 6.
        add(box(ox + sq[0] + 0.1, oy + sq[1] + 0.1, 0, ox + sq[2] - 0.1, oy + sq[3] - 0.1, s * 0.8),
            (int(230 - 60 * t), int(200 - 40 * t), int(120 + 80 * t)))
    for row in range(4):
        for k in range(row + 1):
            add(sph(cx - row * 1.1 + k * 2.2, cy - 8 - (3 - row) * 1.9, 0.6, 0.6), (90, 140, 80))
    return 11


def b_confucius(cx, cy):
    """Harmony and order: a symmetrical courtyard house on a central axis (siheyuan)."""
    wall, roofc = (172, 48, 42), (62, 62, 68)
    add(cbox(cx, cy, 0, 32, 32, 0.4), (206, 198, 184))
    add(cbox(cx, cy + 10, 0.4, 18, 7, 5), wall)
    add(hip_roof(cx, cy + 10, 5.4, 21, 9.5, 3.8), roofc)
    for sx in (-1, 1):
        add(cbox(cx + sx * 11, cy - 1, 0.4, 7, 12, 4), wall)
        add(hip_roof(cx + sx * 11, cy - 1, 4.4, 9, 14, 3), roofc)
    add(cbox(cx, cy - 13, 0.4, 8, 4, 4), wall)
    add(hip_roof(cx, cy - 13, 4.4, 10, 6, 2.5), roofc)
    tree(cx, cy - 2, 8)
    return 9


def b_laozi(cx, cy):
    """'Thirty spokes share one hub; it is the emptiness at the centre that makes it useful.'"""
    add(ring(cx, cy, 0, 13.5, 14.2, 4), (206, 194, 172))
    add(ring(cx, cy, 0, 3.0, 4.0, 4.5), (206, 194, 172))
    for k in range(30):
        b = box(cx + 4.0, cy - 0.15, 0, cx + 13.5, cy + 0.15, 3.6)
        b.Rotate(2 * math.pi * k / 30, Z, P(cx, cy, 0))
        add(b, WOOD)
    return 5


def b_camus(cx, cy):
    """'One must imagine Sisyphus happy': a house at the foot of the hill, the boulder near the top."""
    add(prism_xz([(cx - 15, 0), (cx + 12, 0), (cx + 12, 10)], cy - 5, 10), (160, 150, 136))
    zs = lambda x: (x - (cx - 15)) * 10 / 27.
    add(sph(cx + 6, cy, zs(cx + 6) + 2.0, 1.8), (120, 112, 104))
    add(cyl(cx + 3.9, cy, zs(cx + 3.9) - 0.1, 0.3, 1.8), (210, 120, 80))
    add(box(cx - 14, cy + 7, 0, cx - 8, cy + 13, 3.5), WHITE)
    add(box(cx - 14.2, cy + 6.8, 3.5, cx - 7.8, cy + 13.2, 3.9), (180, 178, 172))
    add(box(cx - 11.6, cy + 6.85, 0, cx - 10.4, cy + 7.0, 2.2), YELLOW)
    return 12


def b_leibniz(cx, cy):
    """'Monads have no windows': windowless spheres in pre-established harmony."""
    add(sph(cx, cy, 6, 6), (236, 222, 200))
    for k in range(8):
        a = 2 * math.pi * k / 8
        r = 1.6 + 1.9 * (0.5 + 0.5 * math.sin(a * 2))
        add(sph(cx + 11 * math.cos(a), cy + 11 * math.sin(a), r, r), (210 - k * 10, 200 - k * 4, 220 - k * 6))
    return 12


def b_goethe(cx, cy):
    """Goethe's Gartenhaus (Weimar) and his 'Stone of Good Fortune' — sphere on cube.
    'Architecture is frozen music.'"""
    add(box(cx - 6, cy - 1, 0, cx + 6, cy + 7, 6.5), (240, 234, 216))
    add(hip_roof(cx, cy + 3, 6.5, 12.8, 8.8, 4.6), (112, 96, 86))
    facade_windows(ACC['openings'], cx - 6, cy - 1, cx + 6, cy + 7, 0, 6.5, faces='S', spacing=2.4, ww=0.9, wh=1.6,
                   floor_h=3.2, sill=0.8)
    add(cbox(cx, cy - 10, 0, 1.3, 1.3, 1.3), (200, 194, 180))
    add(sph(cx, cy - 10, 2.05, 0.75), (200, 194, 180))
    for (tx, ty) in [(-12, 12), (12, 12), (-13, -4), (13, -6), (-8, -14), (8, -14)]:
        tree(cx + tx, cy + ty, 10)
    return 11


def b_heraclitus(cx, cy):
    """Panta rhei — everything flows: a tower that keeps turning, on the river bank."""
    n = 24
    for k in range(n):
        s = cbox(cx, cy, k * 1.1, 12, 6, 0.8)
        s.Rotate(math.radians(k * 7.5), Z, P(cx, cy, 0))
        t = k / (n - 1.)
        add(s, (int(60 + 150 * t), int(120 + 100 * t), int(190 + 50 * t)))
    add(cyl(cx, cy, 0, 1.6, n * 1.1), (230, 236, 240))
    for k in range(6):
        add(cyl(cx - 6 + k * 2.6, cy - 18.5 - k * 2.6, -0.3, 0.8, 0.5), (150, 145, 135))   # stepping stones
    return n * 1.1


def b_nietzsche(cx, cy):
    """Übermensch: Zarathustra's mountain — the tower that keeps overcoming itself."""
    r = random.Random(7)
    Rr, H, nr, ns = 62., 46., 14, 40
    m = rg.Mesh()
    m.Vertices.Add(cx, cy, H)
    for i in range(1, nr + 1):
        rr = Rr * i / nr
        for j in range(ns):
            a = 2 * math.pi * j / ns
            noise = 1 + 0.12 * math.sin(3 * a + i) + r.uniform(-0.05, 0.05)
            z = H * (1 - i / float(nr)) ** 1.4 * (1 + r.uniform(-0.07, 0.07)) if i < nr else -0.25
            if i == 1:
                z = H
            m.Vertices.Add(cx + rr * noise * math.cos(a), cy + rr * noise * math.sin(a), z)
    for j in range(ns):
        m.Faces.AddFace(0, 1 + j, 1 + (j + 1) % ns)
    for i in range(1, nr):
        for j in range(ns):
            a = 1 + (i - 1) * ns + j
            b = 1 + (i - 1) * ns + (j + 1) % ns
            c = 1 + i * ns + (j + 1) % ns
            d = 1 + i * ns + j
            m.Faces.AddFace(a, d, c, b)
    m.Normals.ComputeNormals()
    add(m, (150, 142, 128), "Zarathustra Mountain")
    MOUNTAIN.append(m)
    z = H - 0.5
    for k, (w, h) in enumerate([(7, 8), (5.5, 8), (4.2, 8), (3.0, 8), (2.0, 6)]):
        add(cbox(cx, cy, z, w, w, h, rot=k * 9), (60, 60, 66))
        z += h
    add(cone(cx, cy, z, 1.2, 8), GOLD)
    return z + 8


def b_socrates(cx, cy):
    """'The unexamined life is not worth living': the Stoa in the Agora, open to everyone."""
    L = 44.
    add(box(cx - L / 2, cy - 4.5, 0, cx + L / 2, cy + 4.5, 0.6), MARBLE)
    add(box(cx - L / 2, cy + 3.8, 0.6, cx + L / 2, cy + 4.5, 7), (226, 216, 196))
    for k in range(16):
        add(cyl(cx - L / 2 + 1 + k * (L - 2) / 15, cy - 3.7, 0.6, 0.4, 6.2), MARBLE)
    add(box(cx - L / 2, cy - 4.5, 6.8, cx + L / 2, cy + 4.5, 7.6), MARBLE)
    add(prism_yz([(cy - 5, 7.6), (cy + 4.6, 7.6), (cy + 4.6, 9.4)], cx - L / 2 - 0.3, L + 0.6), ROOFC[0])
    return 9.4


def b_diogenes(cx, cy):
    """Cynicism: virtue needs nothing — Diogenes lives in a barrel, lamp in hand."""
    add(hcyl(cx - 1.3, cy, 1.1, 1.1, 2.6), WOOD)
    for x in (cx - 1.0, cx, cx + 0.9):
        add(hcyl(x, cy, 1.1, 1.16, 0.12), STEEL)
    add(cyl(cx + 2.2, cy - 1, 0, 0.2, 0.5), GOLD)
    return 2.4


def b_thoreau(cx, cy):
    """'Simplify, simplify': the 10 × 15 ft cabin at Walden Pond."""
    add(cbox(cx, cy, 0, 4.6, 3.0, 2.4), (150, 128, 100))
    add(profile_roof(cx, cy, 2.4, 4.6, 3.0, 'gable', 1.5, ov=0.3), (96, 86, 76))
    add(cbox(cx + 2.0, cy + 0.6, 0, 0.6, 0.6, 4.4), BRICK)
    ACC['openings'].Append(mbox(cx - 0.4, cy - 1.58, 0, cx + 0.4, cy - 1.45, 1.9))
    return 4.5


# ================================================================= PUBLIC (inner ring parcels)
def b_townhall(cx, cy):
    add(cbox(cx, cy - 4, 0, 30, 16, 12), (216, 196, 166))
    add(hip_roof(cx, cy - 4, 12, 31, 17, 5), SLATE)
    facade_windows(ACC['openings'], cx - 15, cy - 12, cx + 15, cy + 4, 0, 12, faces='SN', spacing=2.8, floor_h=4.0, wh=2.0)
    add(cbox(cx, cy - 12.5, 0, 5.5, 5.5, 26), (206, 184, 150))
    add(pyramid([P(cx - 3, cy - 15.5, 26), P(cx + 3, cy - 15.5, 26), P(cx + 3, cy - 9.5, 26), P(cx - 3, cy - 9.5, 26)],
                P(cx, cy - 12.5, 34)), (76, 118, 100))
    add(rg.Cylinder(rg.Circle(rg.Plane(P(cx, cy - 15.35, 22), rg.Vector3d.YAxis), 1.6), 0.2).ToBrep(True, True), GOLD)
    return 34


def b_library(cx, cy):
    add(cbox(cx, cy, 0, 28, 20, 5), GLASS, mat=GLASSMAT)
    cols = [(180, 60, 50), (60, 90, 150), (210, 170, 70), (70, 130, 90), (140, 80, 140)]
    z = 5
    for k, c in enumerate(cols):
        h = 2.6 + (k % 2) * 0.8
        add(cbox(cx + (k % 3 - 1) * 1.2, cy + (k % 2) * 1.0, z, 26 - k * 2.4, 16 - k * 1.2, h, rot=(k - 2) * 4), c)
        z += h
    return z


def b_museum(cx, cy):
    add(cbox(cx, cy, 0, 26, 24, 10), WHITE)
    for k in range(5):
        x = cx - 13 + k * 5.2
        add(prism_xz([(x, 10), (x + 5.2, 10), (x + 5.2, 13)], cy - 12, 24), WHITE)
        ACC['openings'].Append(mbox(x + 5.1, cy - 11.5, 10.2, x + 5.25, cy + 11.5, 12.8))
    add(box(cx - 5, cy - 16, 3.6, cx + 5, cy - 12, 4.0), STEEL)
    ACC['openings'].Append(mbox(cx - 3, cy - 12.08, 0, cx + 3, cy - 11.9, 3.4))
    return 13


def b_opera(cx, cy):
    fan = [(cx - 15, cy - 14), (cx + 15, cy - 14), (cx + 9, cy + 4), (cx - 9, cy + 4)]
    add(prism(fan, 0, 13), (196, 168, 140))
    add(box(cx - 8, cy + 4, 0, cx + 8, cy + 15, 25), (176, 150, 128))       # fly tower
    add(box(cx - 15, cy - 17, 0, cx + 15, cy - 14, 9), GLASS, mat=GLASSMAT)
    add(box(cx - 16, cy - 18, 9, cx + 16, cy - 13.5, 9.6), (196, 168, 140))
    return 25


def b_cafe(cx, cy):
    add(cbox(cx, cy + 6, 0, 16, 10, 4.2), (200, 160, 110))
    add(cbox(cx, cy + 6, 4.2, 16.4, 10.4, 0.4), (90, 60, 40))
    add(prism_yz([(cy + 1, 3.6), (cy - 1.5, 3.0), (cy - 1.5, 2.85), (cy + 1, 3.45)], cx - 8, 16), (170, 40, 40))
    ACC['openings'].Append(mbox(cx - 7, cy + 0.92, 0.3, cx + 7, cy + 1.05, 3.2))
    for i in range(4):
        for j in range(2):
            x, y = cx - 6 + i * 4, cy - 5 - j * 5
            add(cyl(x, y, 0, 0.5, 0.75), STEEL)
            add(cyl(x, y, 0, 0.04, 2.4), STEEL)
            add(cone(x, y, 2.0, 1.4, 0.7), (240, 236, 220))
    return 5


# ================================================================= PUBLIC & COMMERCIAL (outer blocks)
def b_school(x0, y0, x1, y1, rnd):
    c = (236, 200, 122)
    add(box(x0 + 2, y0 + 2, 0, x0 + 16, y1 - 2, 8), c)
    add(box(x0 + 16, y1 - 16, 0, x1 - 2, y1 - 2, 8), c)
    for z in (1.0, 4.4):
        ACC['openings'].Append(mbox(x0 + 15.92, y0 + 4, z, x0 + 16.08, y1 - 17, z + 1.6))
        ACC['openings'].Append(mbox(x0 + 18, y1 - 16.08, z, x1 - 4, y1 - 15.92, z + 1.6))
    add(box(x0 + 22, y0 + 6, 0, x1 - 6, y1 - 24, 0.08), (96, 152, 74))
    fx0, fy0, fx1, fy1 = x0 + 24, y0 + 8, x1 - 8, y1 - 26
    add(pline([P(fx0, fy0, 0.1), P(fx1, fy0, 0.1), P(fx1, fy1, 0.1), P(fx0, fy1, 0.1)]), WHITE)
    add(rg.LineCurve(P((fx0 + fx1) / 2, fy0, 0.1), P((fx0 + fx1) / 2, fy1, 0.1)), WHITE)
    label((x0 + x1) / 2, y1 - 9, 12, "SCHOOL")


def b_university(x0, y0, x1, y1, rnd):
    c = (234, 224, 202)
    add(box(x0 + 3, y0 + 3, 0, x0 + 15, y1 - 3, 14), c)
    add(hip_roof(x0 + 9, (y0 + y1) / 2, 14, 12.6, y1 - y0 - 5.4, 4), SLATE)
    add(box(x0 + 15, y1 - 15, 0, x1 - 3, y1 - 3, 14), c)
    add(hip_roof((x0 + 15 + x1 - 3) / 2, y1 - 9, 14, x1 - x0 - 17.4, 12.6, 4), SLATE)
    add(box(x1 - 15, y0 + 3, 0, x1 - 3, y1 - 15, 11), c)
    add(hip_roof(x1 - 9, (y0 + 3 + y1 - 15) / 2, 11, 12.6, y1 - y0 - 17.4, 3.5), SLATE)
    for z in (1.0, 5.6, 10.0):
        ACC['openings'].Append(mbox(x0 + 14.92, y0 + 6, z, x0 + 15.08, y1 - 18, z + 3.0))
    for k in range(10):
        tree(rnd.uniform(x0 + 20, x1 - 20), rnd.uniform(y0 + 6, y1 - 20), rnd=rnd)
    label((x0 + x1) / 2, (y0 + y1) / 2, 20, "BAUHAUS-UNIVERSITÄT\n(university)")


def b_church(x0, y0, x1, y1, rnd):
    cx, cy = x0 + 22, (y0 + y1) / 2 + 2
    add(box(cx - 8, cy - 20, 0, cx + 8, cy + 16, 14), STONE)
    add(prism_xz([(cx - 8.6, 14), (cx + 8.6, 14), (cx, 22)], cy - 20, 36), SLATE)
    add(cyl(cx, cy + 16, 0, 7.6, 12), STONE)
    add(sph(cx, cy + 16, 12, 7.6), SLATE)
    add(box(cx - 4, cy - 28, 0, cx + 4, cy - 20, 32), STONE)
    add(pyramid([P(cx - 4.3, cy - 28.3, 32), P(cx + 4.3, cy - 28.3, 32), P(cx + 4.3, cy - 19.7, 32), P(cx - 4.3, cy - 19.7, 32)],
                P(cx, cy - 24, 50)), (76, 118, 100))
    for y in range(-17, 15, 4):
        ACC['openings'].Append(mbox(cx - 8.08, cy + y - 0.6, 3, cx + 8.08, cy + y + 0.6, 10))
    ACC['openings'].Append(mbox(cx - 1.2, cy - 28.08, 0, cx + 1.2, cy - 27.9, 4))
    res_fill(x0 + 46, y0 + 4, x1 - 4, y1 - 4, rnd)
    label(cx, cy - 24, 52, "CHURCH")


def b_hospital(x0, y0, x1, y1, rnd):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    c = (240, 242, 245)
    add(box(cx - 32, cy - 32, 0, cx - 20, cy + 32, 22), c)
    add(box(cx + 20, cy - 32, 0, cx + 32, cy + 32, 22), c)
    add(box(cx - 20, cy - 7, 0, cx + 20, cy + 7, 16), c)
    for f in range(6):
        z = 1 + f * 3.5
        for xx in (cx - 32, cx - 20, cx + 20, cx + 32):
            ACC['openings'].Append(mbox(xx - 0.08, cy - 30, z, xx + 0.08, cy + 30, z + 1.4))
    add(box(cx - 1.4, cy - 5.5, 16, cx + 1.4, cy + 5.5, 16.3), RED)
    add(box(cx - 5.5, cy - 1.4, 16, cx + 5.5, cy + 1.4, 16.3), RED)
    add(cyl(cx - 26, cy + 20, 22, 5, 0.3), (90, 90, 94))
    label(cx, cy, 26, "HOSPITAL")


def b_fire(x0, y0, x1, y1, rnd):
    red = (192, 46, 40)
    add(box(x0 + 4, y0 + 10, 0, x0 + 36, y0 + 28, 8), red)
    for k in range(4):
        add(box(x0 + 6 + k * 7.5, y0 + 9.85, 0, x0 + 11.5 + k * 7.5, y0 + 10, 5.2), (238, 238, 238))
    add(box(x0 + 36, y0 + 10, 0, x0 + 42, y0 + 16, 20), red)
    add(box(x0 + 35.6, y0 + 9.6, 20, x0 + 42.4, y0 + 16.4, 20.6), (60, 60, 60))
    add(box(x0 + 4, y0 + 2, 0, x0 + 36, y0 + 10, 0.03), ASPHALT)
    res_fill(x0 + 4, y0 + 32, x1 - 4, y1 - 4, rnd)
    label(x0 + 20, y0 + 19, 12, "FIRE STATION")


def b_pool(x0, y0, x1, y1, rnd):
    add(box(x0 + 4, y1 - 30, 0, x0 + 46, y1 - 4, 4), (226, 232, 236))
    cy = y1 - 17
    add(prism_yz([(cy + 13 * math.cos(t), 4 + 7 * math.sin(t)) for t in [math.pi * k / 12. for k in range(13)]], x0 + 4, 42),
        GLASS, mat=GLASSMAT)
    add(box(x0 + 3, y0 + 3, 0, x1 - 3, y1 - 33, 0.05), (216, 196, 160))
    add(box(x0 + 6, y0 + 8, 0, x0 + 40, y0 + 24, 0.14), WATER, mat=WATERMAT)
    add(box(x0 + 46, y0 + 10, 0, x0 + 60, y0 + 22, 0.14), WATER, mat=WATERMAT)
    add(box(x0 + 41, y0 + 14, 0, x0 + 43, y0 + 18, 6), WHITE)
    add(box(x0 + 38, y0 + 15, 5.6, x0 + 43, y0 + 17, 6), WHITE)
    res_fill(x0 + 50, y1 - 32, x1 - 4, y1 - 4, rnd)
    label(x0 + 25, y1 - 17, 14, "PUBLIC BATHS")


def b_police_post(x0, y0, x1, y1, rnd):
    add(box(x0 + 4, y0 + 4, 0, x0 + 36, y0 + 26, 10), (230, 232, 236))
    add(box(x0 + 3.9, y0 + 3.9, 6, x0 + 36.1, y0 + 26.1, 7), (40, 70, 150))
    facade_windows(ACC['openings'], x0 + 4, y0 + 4, x0 + 36, y0 + 26, 0, 10, faces='SNEW')
    add(box(x1 - 36, y0 + 4, 0, x1 - 4, y0 + 26, 8), (238, 226, 190))
    add(box(x1 - 36.1, y0 + 3.9, 5, x1 - 3.9, y0 + 26.1, 6), (230, 180, 30))
    facade_windows(ACC['openings'], x1 - 36, y0 + 4, x1 - 4, y0 + 26, 0, 8, faces='SNEW')
    res_fill(x0 + 4, y0 + 32, x1 - 4, y1 - 4, rnd)
    label(x0 + 20, y0 + 15, 12, "POLICE")
    label(x1 - 20, y0 + 15, 10, "POST OFFICE")


def b_station(x0, y0, x1, y1, rnd):
    cy = y0 + 52
    add(prism_yz([(cy + 14 * math.cos(t), 13 * math.sin(t)) for t in [math.pi * k / 16. for k in range(17)]], x0 + 5, 70),
        GLASS, mat=GLASSMAT)
    for k in range(8):
        x = x0 + 5 + k * 10
        prof = [(cy + 14.3 * math.cos(t), 13.3 * math.sin(t)) for t in [math.pi * q / 16. for q in range(17)]]
        crv = pline([P(x, y, z) for y, z in prof], close=False)
        for b in rg.Brep.CreatePipe(crv, 0.3, False, rg.PipeCapMode.Flat, True, TOL, 0.02) or []:
            add(b, STEEL)
    add(box(x0 + 22, cy + 14, 0, x0 + 58, y1 - 2, 12), STONE)
    add(cbox(x0 + 40, y1 - 2, 12, 6, 1.2, 4), STONE)
    add(rg.Cylinder(rg.Circle(rg.Plane(P(x0 + 40, y1 - 1.35, 13.5), rg.Vector3d.YAxis), 1.5), 0.2).ToBrep(True, True), GOLD)
    for k in range(2):
        py = y0 + 10 + k * 16
        add(box(x0 + 2, py, 0, x1 - 2, py + 4, 1.0), CONC)
        add(box(x0 + 8, py - 0.5, 4.5, x1 - 8, py + 4.5, 4.8), (200, 60, 50))
        for x in range(int(x0 + 10), int(x1 - 8), 10):
            add(cbox(x, py + 2, 1.0, 0.3, 0.3, 3.5), STEEL)
    for ty in (y0 + 6, y0 + 18, y0 + 32):
        for dy in (-0.75, 0.75):
            ACC['rails'].Append(mbox(x0 - 8, ty + dy - 0.05, 0, x1 + 8, ty + dy + 0.05, 0.25))
    for k in range(4):
        add(box(x0 + 8 + k * 16.5, y0 + 4.6, 0.4, x0 + 24 + k * 16.5, y0 + 7.4, 4.2), (200, 40, 40) if k == 0 else (232, 232, 232))
    label(x0 + 40, cy, 16, "CENTRAL STATION")


def b_stadium(x0, y0, x1, y1, rnd):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    st = ring(cx, cy, 0, 26, 37, 15, top_in=3)
    st.Transform(rg.Transform.Scale(rg.Plane(P(cx, cy, 0), Z), 1.0, 0.72, 1.0))
    add(st, (210, 210, 214))
    add(cbox(cx, cy, 0, 46, 28, 0.1), (90, 150, 72))
    add(pline([P(cx - 21, cy - 12, 0.15), P(cx + 21, cy - 12, 0.15), P(cx + 21, cy + 12, 0.15), P(cx - 21, cy + 12, 0.15)]), WHITE)
    add(rg.LineCurve(P(cx, cy - 12, 0.15), P(cx, cy + 12, 0.15)), WHITE)
    label(cx, cy, 18, "STADIUM")


def b_kindergarten(x0, y0, x1, y1, rnd):
    cols = [(240, 120, 90), (90, 170, 220), (250, 200, 70), (130, 200, 120), (200, 130, 210)]
    for k, c in enumerate(cols):
        x = x0 + 8 + k * 7
        add(box(x - 3, y0 + 6, 0, x + 3, y0 + 14, 3.5), c)
        add(profile_roof(x, y0 + 10, 3.5, 6, 8, ['gable', 'shed', 'barrel', 'gable', 'saltbox'][k], 2.2), (240, 240, 236))
    add(box(x0 + 8, y0 + 20, 0, x0 + 16, y0 + 28, 0.3), (230, 210, 150))
    add(prism_xz([(x0 + 22, 0), (x0 + 28, 0), (x0 + 22, 2.5)], y0 + 22, 0.8), (240, 80, 70))
    res_fill(x0 + 42, y0 + 4, x1 - 4, y1 - 4, rnd)
    label(x0 + 22, y0 + 10, 8, "KINDERGARTEN")


def tower_lot(lx, ly, t, H, col, r):
    if t in ('box', 'box2'):
        w, d = r.uniform(16, 24), r.uniform(16, 24)
        add(cbox(lx, ly, 0, w, d, H), col, mat=GLASSMAT if t == 'box2' else None)
        bands(lx - w / 2, ly - d / 2, lx + w / 2, ly + d / 2, 0, H)
        add(cbox(lx, ly, H, w * 0.6, d * 0.6, 3.5), STEEL)
    elif t == 'cyl':
        Rr = r.uniform(8, 10.5)
        add(cyl(lx, ly, 0, Rr, H), col)
        z = 3.8
        while z < H - 1:
            ACC['spandrel'].Append(rg.Mesh.CreateFromCylinder(rg.Cylinder(rg.Circle(rg.Plane(P(lx, ly, z), Z), Rr + 0.08), 0.45), 1, 36, True, True))
            z += 3.8
    elif t == 'setback':
        z = 0
        for w, f in [(24, 0.5), (18, 0.3), (12, 0.2)]:
            add(cbox(lx, ly, z, w, w, H * f), col)
            bands(lx - w / 2, ly - w / 2, lx + w / 2, ly + w / 2, z, z + H * f)
            z += H * f
        add(cone(lx, ly, z, 1.0, 14), STEEL)
        H = z + 14
    elif t == 'twist':
        n = int(H / 3.6)
        for k in range(n):
            add(cbox(lx, ly, k * 3.6, 20, 20, 3.4, rot=k * 2.2), col)
            add(cbox(lx, ly, k * 3.6 + 3.4, 20.3, 20.3, 0.2, rot=k * 2.2), (220, 220, 216))
    return H


def b_offices(x0, y0, x1, y1, rnd):
    lots = [(x0 + 20, y0 + 20), (x1 - 20, y0 + 20), (x0 + 20, y1 - 20), (x1 - 20, y1 - 20)]
    types = rnd.sample(['box', 'box2', 'cyl', 'setback', 'twist'], 4)
    top = 0
    for (lx, ly), t in zip(lots, types):
        top = max(top, tower_lot(lx, ly, t, rnd.uniform(42, 98), rnd.choice(GLASSES), rnd))
    label((x0 + x1) / 2, (y0 + y1) / 2, 30, "OFFICE TOWERS")


def b_hotel(x0, y0, x1, y1, rnd):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    add(box(cx - 34, cy - 30, 0, cx + 34, cy + 10, 9), (202, 196, 186))
    ACC['openings'].Append(mbox(cx - 30, cy - 30.08, 0.5, cx + 30, cy - 29.9, 6))
    add(box(cx - 25, cy - 6, 9, cx + 25, cy + 8, 62), (228, 216, 196))
    for z in range(12, 62, 3):
        ACC['spandrel'].Append(mbox(cx - 25, cy - 7.2, z, cx + 25, cy - 6, z + 0.25))
    facade_windows(ACC['openings'], cx - 25, cy - 6, cx + 25, cy + 8, 9, 62, faces='SN', spacing=2.5, floor_h=3.0, wh=1.8, sill=0.6)
    add(box(cx - 30, cy - 28, 9, cx - 14, cy - 16, 9.15), WATER, mat=WATERMAT)
    add(box(cx - 26, cy - 7, 62, cx + 26, cy + 9, 64), STEEL)
    res_fill(x0 + 4, cy + 14, x1 - 4, y1 - 4, rnd)
    label(cx, cy, 66, "GRAND HOTEL")


def b_mall(x0, y0, x1, y1, rnd):
    add(box(x0 + 4, y0 + 26, 0, x1 - 4, y1 - 4, 14), (216, 210, 200))
    yc = (y0 + 26 + y1 - 4) / 2
    add(prism_yz([(yc + 7 * math.cos(t), 14 + 6 * math.sin(t)) for t in [math.pi * k / 12. for k in range(13)]], x0 + 4, x1 - x0 - 8),
        GLASS, mat=GLASSMAT)
    ACC['openings'].Append(mbox(x0 + 10, y0 + 25.9, 0.3, x1 - 10, y0 + 26.08, 5))
    add(box(x0 + 4, y0 + 4, 0, x1 - 4, y0 + 24, 0.03), ASPHALT)
    for row in (y0 + 9, y0 + 19):
        for k in range(14):
            if rnd.random() < 0.75:
                car(x0 + 8 + k * 5, row, 90, rnd)
    label((x0 + x1) / 2, yc, 22, "SHOPPING MALL")


def portico(cx, yf, w, h, z0, col):
    n = int(w / 2.6) + 1
    for i in range(n):
        add(cyl(cx - w / 2 + 0.8 + i * (w - 1.6) / (n - 1), yf - 3, z0, 0.45, h), col)
    add(box(cx - w / 2, yf - 4, z0 + h, cx + w / 2, yf, z0 + h + 1.2), col)
    add(prism_xz([(cx - w / 2, z0 + h + 1.2), (cx + w / 2, z0 + h + 1.2), (cx, z0 + h + 3.6)], yf - 4, 4), col)


def b_bank(x0, y0, x1, y1, rnd):
    cx = x0 + 20
    add(box(cx - 15, y0 + 10, 0, cx + 15, y0 + 34, 14), STONE)
    for k in range(4):
        add(box(cx - 9 + k * 0.6, y0 + 3 + k * 0.7, 0, cx + 9 - k * 0.6, y0 + 10, 0.3 * (k + 1)), STONE)
    portico(cx, y0 + 10, 18, 9, 1.2, MARBLE)
    shops_row(x0 + 42, y0, x1, y1, rnd)
    shops_row(x0, y0 + 40, x0 + 42, y1, rnd, edges='NW')
    label(cx, y0 + 20, 18, "BANK")


def b_market(x0, y0, x1, y1, rnd):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 + 12
    add(prism_yz([(cy + 13 * math.cos(t), 6 + 8 * math.sin(t)) for t in [math.pi * k / 12. for k in range(13)]], cx - 30, 60), (176, 66, 52))
    add(box(cx - 30, cy - 13, 0, cx + 30, cy + 13, 6), (232, 212, 182))
    for x in range(-27, 28, 6):
        ACC['openings'].Append(mbox(cx + x - 1.6, cy - 13.08, 0, cx + x + 1.6, cy - 12.9, 4.5))
    cols = [(220, 60, 50), (240, 200, 60), (60, 140, 90), (60, 100, 180), (240, 140, 60)]
    for i in range(6):
        for j in range(2):
            x, y = x0 + 10 + i * 11, y0 + 10 + j * 10
            add(cbox(x, y, 0, 4, 2.5, 1.0), WOOD)
            add(prism_yz([(y - 2, 2.6), (y + 2, 2.6), (y, 3.6)], x - 2.5, 5), cols[(i + j) % 5])
            for dx in (-2.2, 2.2):
                add(cbox(x + dx, y, 0, 0.12, 0.12, 2.6), STEEL)
    label(cx, cy, 16, "MARKET HALL")


def b_cinema(x0, y0, x1, y1, rnd):
    add(box(x0 + 4, y0 + 4, 0, x0 + 38, y0 + 40, 16), (70, 44, 70))
    add(box(x0 + 3, y0 + 2.5, 9, x0 + 39, y0 + 4, 12), (250, 214, 90))
    add_text("CINEMA", rg.Plane(P(x0 + 10, y0 + 2.4, 9.6), rg.Vector3d.XAxis, Z), 2.0, (180, 30, 30))
    ACC['openings'].Append(mbox(x0 + 8, y0 + 3.9, 0, x0 + 34, y0 + 4.1, 4))
    shops_row(x0 + 42, y0, x1, y1, rnd)
    res_fill(x0 + 4, y0 + 44, x0 + 40, y1 - 4, rnd)
    label(x0 + 21, y0 + 20, 20, "CINEMA")


def shops_row(x0, y0, x1, y1, rnd, edges='SENW'):
    """High street: narrow shop-houses along the block edges, each with an awning."""
    D = 12.
    frames = {'S': (x0, y0, 0, x1 - x0), 'E': (x1, y0, 90, y1 - y0), 'N': (x1, y1, 180, x1 - x0), 'W': (x0, y1, 270, y1 - y0)}
    awn = [(200, 50, 50), (40, 110, 70), (230, 180, 40), (40, 80, 160), (230, 120, 50), (240, 240, 240)]
    for e in edges:
        ox, oy, ang, L = frames[e]
        x = 0.0 if e in 'SN' else D
        xend = L if e in 'SN' else L - D
        while x < xend - 4:
            w = min(rnd.uniform(6, 10), xend - x)
            h = rnd.choice([7, 10, 10, 13, 16])
            geo = [(box(x + 0.15, 0, 0, x + w - 0.15, D, h), jit(rnd.choice(PASTELS), rnd, 15))]
            if rnd.random() < 0.45:
                geo.append((profile_roof(x + w / 2, D / 2, h, w - 0.3, D, 'gable', w * 0.45, ov=0.1), jit(rnd.choice(ROOFC), rnd)))
            geo.append((prism_yz([(0, 3.5), (-1.8, 2.9), (-1.8, 2.75), (0, 3.3)], x + 0.6, w - 1.2), rnd.choice(awn)))
            win = mbox(x + 0.8, -0.08, 0.2, x + w - 0.8, 0.05, 2.8)
            facade_windows(win, x + 0.15, 0, x + w - 0.15, D, 3.5, h, faces='S', spacing=2.4, ww=1.0, wh=1.5, floor_h=3.1, sill=0.9)
            for g, c in geo:
                g.Rotate(math.radians(ang), Z, P(0, 0, 0))
                g.Translate(rg.Vector3d(ox, oy, 0))
                add(g, c)
            win.Rotate(math.radians(ang), Z, P(0, 0, 0))
            win.Translate(rg.Vector3d(ox, oy, 0))
            ACC['openings'].Append(win)
            x += w


def b_shops(x0, y0, x1, y1, rnd):
    shops_row(x0, y0, x1, y1, rnd)
    for k in range(5):
        tree(rnd.uniform(x0 + 16, x1 - 16), rnd.uniform(y0 + 16, y1 - 16), rnd=rnd)
    label((x0 + x1) / 2, (y0 + y1) / 2, 18, "HIGH STREET SHOPS")


# ================================================================= CITY LAYOUT
N, BLK, ST = 8, 80., 16.
PITCH = BLK + ST
HALF = (N * BLK + (N - 1) * ST) / 2.


def bx(i):
    return -HALF + i * PITCH


ARCHITECTS = [
    ("Mies van der Rohe", "“Less is more.”", b_mies),
    ("Louis Sullivan", "“Form follows function.”", b_sullivan),
    ("Le Corbusier", "“A house is a machine for living in.” (Five Points)", b_corbusier),
    ("Frank Lloyd Wright", "Organic architecture – the house grows from its site", b_wright),
    ("Walter Gropius", "“Art and technology – a new unity.” (Bauhaus)", b_gropius),
    ("Adolf Loos", "“Ornament is crime.”", b_loos),
    ("Robert Venturi", "“Less is a bore.” (the decorated shed)", b_venturi),
    ("Antoni Gaudí", "“The straight line belongs to men, the curved line to God.”", b_gaudi),
    ("Zaha Hadid", "“There are 360 degrees, so why stick to one?”", b_hadid),
    ("Frank Gehry", "Deconstructivism – fragmented, colliding forms", b_gehry),
    ("Buckminster Fuller", "“Doing more with less.” (geodesic dome)", b_fuller),
    ("Louis Kahn", "Served & servant spaces – “Ask the brick what it wants.”", b_kahn),
    ("Rem Koolhaas", "“Bigness” – a loop of program", b_koolhaas),
    ("Tadao Ando", "Light, concrete and void – the cross of light", b_ando),
    ("Aldo Rossi", "Typology – “The Architecture of the City”", b_rossi),
    ("Kisho Kurokawa", "Metabolism – plug-in, replaceable capsules", b_kurokawa),
    ("Peter Eisenman", "Autonomy of form – shifting grids (House VI)", b_eisenman),
    ("Bjarke Ingels", "“Yes is more” – hedonistic sustainability", b_ingels),
    ("Vitruvius", "Firmitas, Utilitas, Venustas", b_vitruvius),
    ("Andrea Palladio", "Symmetry & harmonic proportion (Villa Rotonda)", b_palladio),
]
PHILOSOPHERS_RING = [
    ("Plato", "Theory of Forms – the ideal, perfect solids", b_plato),
    ("René Descartes", "“Cogito, ergo sum” – the Cartesian axes", b_descartes),
    ("Immanuel Kant", "Categorical imperative – the maxim as universal law", b_kant),
    ("Jeremy Bentham", "The Panopticon – to see without being seen", b_bentham),
    ("Martin Heidegger", "“Building Dwelling Thinking” – the hut", b_heidegger),
    ("Ludwig Wittgenstein", "“The limits of my language mean the limits of my world.”", b_wittgenstein),
    ("Pythagoras", "“All is number” – golden ratio & tetractys", b_pythagoras),
    ("Confucius", "Harmony & order – the symmetrical courtyard", b_confucius),
    ("Laozi", "“Thirty spokes share one hub; the emptiness makes it useful.”", b_laozi),
    ("Albert Camus", "“One must imagine Sisyphus happy.”", b_camus),
    ("Gottfried Leibniz", "“Monads have no windows.”", b_leibniz),
    ("J. W. von Goethe", "“Architecture is frozen music.” – Stone of Good Fortune", b_goethe),
]
PUBLIC_RING = [
    ("TOWN HALL", b_townhall), ("CITY LIBRARY", b_library), ("MUSEUM OF THEORIES", b_museum),
    ("OPERA HOUSE", b_opera), ("CAFÉ OF DEBATES", b_cafe),
]

OUTER = {
    (1, 7): b_school, (3, 7): b_university, (5, 7): b_hotel, (6, 7): b_offices, (7, 7): b_offices,
    (4, 6): b_church, (6, 6): b_mall, (7, 6): b_offices, (2, 6): b_shops,
    (1, 5): b_fire, (6, 5): b_bank, (7, 5): b_market,
    (1, 4): b_hospital, (6, 4): b_cinema,
    (1, 2): b_pool, (7, 2): b_police_post, (6, 1): b_shops,
    (3, 1): b_station, (7, 0): b_stadium, (1, 0): b_kindergarten,
}
PAVED = {b_offices, b_hotel, b_mall, b_bank, b_market, b_cinema, b_shops, b_station, b_police_post}



# ================================================================= PEOPLE & TRAFFIC — a quiet morning
# One plan drives both the Rhino snapshot (built below at time TS) and the animated web viewer
# (written to daemon_city_people.json). Time t is in seconds after 06:40.
TS = 1800.0          # the Rhino model shows 07:10, when Line 1 pulls up for Le Corbusier
SKIN = [(244, 208, 176), (230, 186, 148), (204, 152, 112), (166, 116, 82), (122, 84, 58), (250, 222, 198)]
HAIRC = [(30, 26, 22), (62, 42, 28), (110, 76, 46), (196, 160, 98), (150, 150, 148), (228, 226, 220), (150, 62, 32)]
TOPS = [(196, 58, 50), (52, 88, 150), (236, 236, 230), (60, 60, 64), (232, 186, 64), (78, 128, 92),
        (150, 96, 160), (226, 128, 70), (120, 160, 200), (180, 170, 150), (40, 44, 70)]
BOTTOMS = [(46, 52, 70), (60, 60, 62), (108, 92, 70), (36, 36, 40), (140, 130, 112), (70, 90, 120)]
WH_, GR_, BK_, BR_, DB_ = (234, 232, 226), (156, 154, 150), (28, 26, 24), (96, 64, 40), (58, 40, 28)
SKIN0 = (238, 200, 168)


def LOOK(note, **kw):
    d = dict(h=1.78, skin=SKIN0, hair='short', hc=BR_, beard=None, bc=None, mous=None, glasses=None, hat=None,
             hatc=BK_, top=(60, 62, 68), bottom=(52, 54, 60), robe=None, bow=None, prop=None, note=note)
    d.update(kw)
    if d['bc'] is None:
        d['bc'] = d['hc']
    return d


LOOKS = {
    "Mies van der Rohe": LOOK("Heavy-set, bald on top with grey sides, an immaculate dark suit and the cigar he was rarely without.",
                              h=1.80, hair='side', hc=GR_, top=(64, 66, 72), bottom=(58, 60, 66), prop=['cigar', 'bag']),
    "Louis Sullivan": LOOK("Dark hair, a short full beard and a brown three-piece suit: Chicago in the 1890s.",
                           hair='short', hc=BK_, beard='short', top=(110, 80, 56), bottom=(100, 74, 52)),
    "Le Corbusier": LOOK("Round black glasses, a bow tie, a dark suit and thinning hair combed back.",
                         hair='side', hc=BK_, glasses='round', bow=BK_, top=(40, 42, 48), bottom=(40, 42, 48)),
    "Frank Lloyd Wright": LOOK("Silver hair under a porkpie hat, a flowing cape and a walking cane.",
                               h=1.72, hair='side', hc=WH_, hat='porkpie', hatc=(70, 60, 50), robe=(82, 58, 44), prop=['cane']),
    "Walter Gropius": LOOK("Dark hair combed straight back and a sober dark suit: the Bauhaus director.",
                           hair='short', hc=BK_, top=(50, 52, 58), bottom=(50, 52, 58)),
    "Adolf Loos": LOOK("A plain grey suit with no ornament whatsoever and neat dark hair.",
                       hair='short', hc=DB_, top=(128, 128, 126), bottom=(120, 120, 118)),
    "Robert Venturi": LOOK("White hair, glasses, a blue shirt, and three bags of shopping, because less is a bore.",
                           hair='short', hc=WH_, glasses='round', top=(84, 120, 180), bottom=(140, 130, 112), prop=['bags3']),
    "Antoni Gaudí": LOOK("A full white beard, white hair and a worn grey suit; he cared nothing for his clothes.",
                         hair='short', hc=WH_, beard='full', top=(120, 118, 112), bottom=(110, 108, 102)),
    "Zaha Hadid": LOOK("Long black hair and a flowing black coat: every line of the outfit curves.",
                       h=1.72, hair='long', hc=BK_, robe=(26, 26, 30), skin=(214, 170, 130)),
    "Frank Gehry": LOOK("Short white hair, a black T-shirt and jeans: the relaxed Californian.",
                        h=1.70, hair='short', hc=WH_, top=(30, 30, 32), bottom=(70, 96, 140)),
    "Buckminster Fuller": LOOK("Bald, with very thick round glasses and a dark three-piece suit.",
                               h=1.68, hair='side', hc=GR_, glasses='thick', top=(52, 54, 60), bottom=(52, 54, 60)),
    "Louis Kahn": LOOK("Wild white hair, round glasses, a bow tie and a black suit.",
                       h=1.68, hair='curly', hc=WH_, glasses='round', bow=BK_, top=(34, 34, 38), bottom=(34, 34, 38)),
    "Rem Koolhaas": LOOK("Very tall and lean, shaved head, dressed entirely in black.",
                         h=1.96, hair='bald', top=(30, 30, 32), bottom=(30, 30, 32)),
    "Tadao Ando": LOOK("A black bowl cut and black clothes; a former boxer who still walks like one.",
                       h=1.68, hair='bowl', hc=BK_, skin=(226, 186, 150), top=(32, 32, 34), bottom=(32, 32, 34)),
    "Aldo Rossi": LOOK("Dark hair, glasses and a beige suit, a sketchbook under his arm.",
                       hair='short', hc=DB_, glasses='round', top=(196, 180, 150), bottom=(180, 166, 140), prop=['book']),
    "Kisho Kurokawa": LOOK("Neatly combed black hair and a sharp dark suit.",
                           hair='short', hc=BK_, skin=(226, 186, 150), top=(40, 46, 60), bottom=(40, 46, 60)),
    "Peter Eisenman": LOOK("Grey hair, round glasses and his trademark red bow tie.",
                           hair='side', hc=GR_, glasses='round', bow=(170, 40, 40), top=(70, 72, 80), bottom=(60, 62, 70)),
    "Bjarke Ingels": LOOK("Dark hair, stubble, a bright orange T-shirt and sneakers.",
                          hair='short', hc=DB_, beard='short', top=(230, 120, 60), bottom=(60, 64, 80)),
    "Vitruvius": LOOK("A Roman in a white toga with a trimmed beard, holding his scroll.",
                      hair='short', hc=DB_, beard='short', robe=(236, 232, 220), prop=['scroll']),
    "Andrea Palladio": LOOK("A red Renaissance cap, a dark beard and a long scholar's gown.",
                            hair='short', hc=DB_, beard='full', hat='renaissance', hatc=(160, 40, 40), robe=(70, 50, 60)),
    "Plato": LOOK("Broad-shouldered, in a white himation, with a long grey beard.",
                  h=1.84, hair='short', hc=GR_, beard='long', robe=(232, 226, 210)),
    "René Descartes": LOOK("Long dark hair to the shoulders, a thin moustache, black clothes and a white collar.",
                           h=1.62, hair='long', hc=DB_, mous='pencil', top=(30, 30, 32), bottom=(30, 30, 32), bow=(236, 236, 230)),
    "Immanuel Kant": LOOK("A small man in a white wig with a tied pigtail, a brown coat and his cane.",
                          h=1.57, hair='ponytail', hc=WH_, top=(120, 86, 56), bottom=(90, 70, 50), prop=['cane']),
    "Jeremy Bentham": LOOK("Long white hair under a soft cap, a brown coat, and his walking stick 'Dapple'.",
                           hair='long', hc=WH_, hat='cap', hatc=(60, 50, 40), top=(110, 80, 50), bottom=(90, 70, 50), prop=['cane']),
    "Martin Heidegger": LOOK("A small moustache, dark hair and a green Black Forest jacket.",
                             h=1.63, hair='side', hc=DB_, mous='small', top=(70, 96, 62), bottom=(70, 64, 56)),
    "Ludwig Wittgenstein": LOOK("Curly dark hair, an open-collared white shirt and a tweed jacket. Today he says nothing.",
                                hair='curly', hc=DB_, top=(140, 120, 96), bottom=(90, 84, 76)),
    "Friedrich Nietzsche": LOOK("An enormous walrus moustache, swept-back hair and a dark coat.",
                                hair='short', hc=BR_, mous='big', top=(46, 44, 46), bottom=(46, 44, 46)),
    "Heraclitus": LOOK("A dark blue robe and a long grey beard; he watches the river.",
                       hair='short', hc=GR_, beard='long', robe=(40, 60, 110)),
    "Pythagoras": LOOK("A white robe, a long grey beard and a soft cap.",
                       hair='short', hc=GR_, beard='long', hat='cap', hatc=(236, 228, 200), robe=(240, 238, 230)),
    "Henry David Thoreau": LOOK("A brown coat and the neck beard of his later years.",
                                hair='short', hc=BR_, beard='neck', top=(110, 84, 60), bottom=(90, 76, 60)),
    "Confucius": LOOK("A long black beard, a black scholar's hat and a deep red robe.",
                      hair='short', hc=BK_, beard='long', hat='scholar', robe=(130, 30, 30), skin=(226, 186, 150)),
    "Laozi": LOOK("A long white beard, a bald crown and a pale ochre robe.",
                  hair='side', hc=WH_, beard='long', robe=(210, 190, 140), skin=(226, 186, 150)),
    "Albert Camus": LOOK("Swept-back dark hair; this morning a white running shirt instead of the trench coat.",
                         hair='short', hc=BK_, top=(240, 240, 236), bottom=(40, 48, 80)),
    "Gottfried Leibniz": LOOK("A huge curly black periwig and an embroidered purple coat.",
                              hair='bigwig', hc=BK_, top=(90, 60, 90), bottom=(60, 50, 60)),
    "J. W. von Goethe": LOOK("Hair tied back, and the blue coat and yellow waistcoat of his Werther.",
                             h=1.76, hair='ponytail', hc=BR_, top=(52, 80, 150), bottom=(220, 190, 90)),
    "Socrates": LOOK("Bald and snub-nosed, with a bushy beard and a plain grey cloak; always asking questions.",
                     h=1.66, hair='side', hc=GR_, beard='full', robe=(150, 146, 138)),
    "Diogenes": LOOK("Barefoot and wild-haired in a ragged tunic, carrying a lamp in daylight to look for an honest man.",
                     hair='curly', hc=GR_, beard='full', robe=(130, 100, 70), prop=['lantern']),
}


def citizen_look(r, kid=False):
    lk = LOOK("", h=(r.uniform(1.05, 1.3) if kid else r.uniform(1.58, 1.93)), skin=r.choice(SKIN),
              hair=r.choice(['short', 'short', 'short', 'long', 'side', 'bald', 'ponytail', 'curly', 'bowl']),
              hc=r.choice(HAIRC), top=r.choice(TOPS), bottom=r.choice(BOTTOMS))
    lk['bc'] = lk['hc']
    if not kid:
        if r.random() < 0.14:
            lk['beard'] = r.choice(['short', 'full'])
        if r.random() < 0.08:
            lk['mous'] = 'small'
        if r.random() < 0.14:
            lk['glasses'] = 'round'
        if r.random() < 0.08:
            lk['hat'], lk['hatc'] = 'cap', r.choice(TOPS)
    return lk


# ---------------------------------------------------------------- figure geometry (feet at origin, facing +y)
def star_mesh(cz, R=0.21, ri=0.088, t=0.05):
    pts = [((R if k % 2 == 0 else ri) * math.cos(math.pi / 2 + k * math.pi / 5),
            (R if k % 2 == 0 else ri) * math.sin(math.pi / 2 + k * math.pi / 5)) for k in range(10)]
    verts = [P(x, t / 2, cz + z) for x, z in pts] + [P(x, -t / 2, cz + z) for x, z in pts] + [P(0, t / 2, cz), P(0, -t / 2, cz)]
    faces = [(i, (i + 1) % 10, 20) for i in range(10)] + [(10 + (i + 1) % 10, 10 + i, 21) for i in range(10)]
    faces += [(i, 10 + i, 10 + (i + 1) % 10, (i + 1) % 10) for i in range(10)]
    return mesh_from(verts, faces)


def frustum_mesh(r0, r1, z0, z1, seg=12):
    pts = [P(r0 * math.cos(2 * math.pi * k / seg), r0 * math.sin(2 * math.pi * k / seg), z0) for k in range(seg)]
    pts += [P(r1 * math.cos(2 * math.pi * k / seg), r1 * math.sin(2 * math.pi * k / seg), z1) for k in range(seg)]
    pts += [P(0, 0, z0), P(0, 0, z1)]
    faces = [(k, (k + 1) % seg, seg + (k + 1) % seg, seg + k) for k in range(seg)]
    faces += [((k + 1) % seg, k, 2 * seg) for k in range(seg)] + [(seg + k, seg + (k + 1) % seg, 2 * seg + 1) for k in range(seg)]
    return mesh_from(pts, faces)


def head_top(lk):
    H = lk['h']
    r = 0.068 * H
    hc = 0.83 * H + r
    extra = 0.65 * r if lk['hat'] else (0.35 * r if lk['hair'] in ('curly', 'bigwig') else 0.0)
    return hc + r + extra


def figure_parts(lk, swing=0.0, famous=False):
    H = lk['h']
    r = 0.068 * H
    hip, sh = 0.5 * H, 0.79 * H
    hc = 0.83 * H + r
    out = []
    A = lambda c, m: out.append((tuple(c), m))
    X = rg.Vector3d.XAxis

    def limb(x, ztop, w, length, ang):
        m = mbox(x - w / 2, -w / 2, ztop - length, x + w / 2, w / 2, ztop)
        m.Rotate(ang, X, P(x, 0, ztop))
        return m

    def hand(sx):
        p = P(sx * 0.25, 0, sh - 0.34 * H)
        p.Transform(rg.Transform.Rotation(-sx * swing * 0.8, X, P(sx * 0.25, 0, sh)))
        return p
    if lk['robe']:
        A(lk['robe'], frustum_mesh(0.3, 0.2, 0, 0.8 * H))
        body = lk['robe']
    else:
        for sx in (-1, 1):
            A(lk['bottom'], limb(sx * 0.09, hip, 0.13, hip, sx * swing))
        A(lk['bottom'], mbox(-0.18, -0.1, hip - 0.06, 0.18, 0.1, hip + 0.04))
        body = lk['top']
    A(body, mbox(-0.19, -0.11, hip, 0.19, 0.11, 0.8 * H))
    for sx in (-1, 1):
        A(body, limb(sx * 0.25, sh, 0.09, 0.34 * H, -sx * swing * 0.8))
        hp = hand(sx)
        A(lk['skin'], msph(hp.X, hp.Y, hp.Z, 0.05, 6))
    A(lk['skin'], mcyl(0, 0, 0.8 * H - 0.01, 0.05, 0.03 * H + 0.02, 8))
    A(lk['skin'], msph(0, 0, hc, r, 12))
    for sx in (-1, 1):
        A((34, 30, 28), msph(sx * 0.38 * r, 0.86 * r, hc + 0.12 * r, 0.11 * r, 6))
    A(tuple(max(0, c - 18) for c in lk['skin']), mbox(-0.08 * r, 0.9 * r, hc - 0.18 * r, 0.08 * r, 1.12 * r, hc + 0.06 * r))
    hs, hcol = lk['hair'], lk['hc']
    if hs in ('short', 'long', 'ponytail'):
        A(hcol, ellipsoid_mesh(0, -0.12 * r, hc + 0.28 * r, 1.04 * r, 1.0 * r, 0.8 * r))
    if hs == 'side':
        A(hcol, ellipsoid_mesh(0, -0.3 * r, hc - 0.05 * r, 1.03 * r, 0.78 * r, 0.55 * r))
    if hs == 'long':
        A(hcol, ellipsoid_mesh(0, -0.5 * r, hc - 0.9 * r, 0.95 * r, 0.5 * r, 1.2 * r))
    if hs == 'ponytail':
        A(hcol, msph(0, -1.1 * r, hc - 0.1 * r, 0.28 * r, 6))
        A(hcol, mbox(-0.1 * r, -1.25 * r, hc - 0.9 * r, 0.1 * r, -1.0 * r, hc - 0.1 * r))
    if hs in ('curly', 'bigwig'):
        A(hcol, ellipsoid_mesh(0, -0.38 * r, hc + 0.3 * r, 1.3 * r, 1.15 * r, 1.05 * r))
    if hs == 'bigwig':
        for sx in (-1, 1):
            A(hcol, ellipsoid_mesh(sx * 1.05 * r, -0.2 * r, hc - 0.95 * r, 0.6 * r, 0.6 * r, 0.9 * r))
    if hs == 'bowl':
        A(hcol, ellipsoid_mesh(0, -0.15 * r, hc + 0.32 * r, 1.08 * r, 1.0 * r, 0.78 * r))
    b, bc = lk['beard'], lk['bc']
    if b == 'short':
        A(bc, ellipsoid_mesh(0, 0.5 * r, hc - 0.62 * r, 0.72 * r, 0.5 * r, 0.5 * r))
    if b in ('full', 'long'):
        A(bc, ellipsoid_mesh(0, 0.42 * r, hc - 0.72 * r, 0.86 * r, 0.6 * r, 0.72 * r))
    if b == 'long':
        A(bc, ellipsoid_mesh(0, 0.55 * r, hc - 1.55 * r, 0.6 * r, 0.42 * r, 1.0 * r))
    if b == 'neck':
        A(bc, ellipsoid_mesh(0, 0.25 * r, hc - 0.95 * r, 0.8 * r, 0.62 * r, 0.32 * r))
    mo = lk['mous']
    if mo == 'small':
        A(bc, mbox(-0.18 * r, 0.93 * r, hc - 0.36 * r, 0.18 * r, 1.04 * r, hc - 0.26 * r))
    if mo == 'pencil':
        A(bc, mbox(-0.3 * r, 0.93 * r, hc - 0.33 * r, 0.3 * r, 1.0 * r, hc - 0.29 * r))
    if mo == 'big':
        A(bc, ellipsoid_mesh(0, 0.9 * r, hc - 0.38 * r, 0.78 * r, 0.26 * r, 0.22 * r))
    g = lk['glasses']
    if g:
        rr, t = (0.27 * r, 0.04 * r) if g == 'round' else (0.33 * r, 0.07 * r)
        for sx in (-1, 1):
            A((18, 18, 20), mdisc(P(sx * 0.38 * r, 0.97 * r, hc + 0.12 * r), (0, 1, 0), rr, t=t, seg=12))
        A((18, 18, 20), mbox(-0.12 * r, 0.98 * r, hc + 0.1 * r, 0.12 * r, 1.02 * r, hc + 0.14 * r))
    hat, hatc = lk['hat'], lk['hatc']
    if hat == 'porkpie':
        A(hatc, mcyl(0, -0.05 * r, hc + 0.45 * r, 1.55 * r, 0.06 * r, 16))
        A(hatc, mcyl(0, -0.05 * r, hc + 0.45 * r, 1.02 * r, 0.6 * r, 16))
    if hat == 'scholar':
        A(hatc, mbox(-1.0 * r, -1.1 * r, hc + 0.55 * r, 1.0 * r, 0.9 * r, hc + 1.1 * r))
    if hat == 'renaissance':
        A(hatc, ellipsoid_mesh(0, -0.1 * r, hc + 0.62 * r, 1.25 * r, 1.25 * r, 0.5 * r))
    if hat == 'cap':
        A(hatc, ellipsoid_mesh(0, -0.1 * r, hc + 0.5 * r, 1.06 * r, 1.06 * r, 0.55 * r))
    if lk['bow']:
        A(lk['bow'], mbox(-0.07, 0.105, 0.79 * H - 0.01, 0.07, 0.135, 0.79 * H + 0.05))
    for pr in lk['prop'] or []:
        hl, hr = hand(-1), hand(1)
        if pr in ('bag', 'bags3'):
            A((206, 160, 96), mbox(hl.X - 0.05, hl.Y - 0.13, hl.Z - 0.34, hl.X + 0.05, hl.Y + 0.13, hl.Z - 0.04))
        if pr == 'bags3':
            A((196, 58, 50), mbox(hr.X - 0.05, hr.Y - 0.13, hr.Z - 0.34, hr.X + 0.05, hr.Y + 0.13, hr.Z - 0.04))
            A((52, 88, 150), mbox(hl.X - 0.12, hl.Y + 0.02, hl.Z - 0.4, hl.X - 0.02, hl.Y + 0.24, hl.Z - 0.1))
        if pr == 'cigar':
            A((110, 70, 40), mbox(0.05 * r, 0.95 * r, hc - 0.46 * r, 0.16 * r, 0.95 * r + 0.12, hc - 0.38 * r))
            A((255, 120, 40), mbox(0.05 * r, 0.95 * r + 0.12, hc - 0.46 * r, 0.16 * r, 0.95 * r + 0.14, hc - 0.38 * r))
        if pr == 'cane':
            A((40, 32, 26), mcyl(hr.X + 0.03, hr.Y + 0.05, 0, 0.018, hr.Z, 6))
        if pr == 'lantern':
            A((255, 214, 120), mbox(hr.X - 0.07, hr.Y - 0.07, hr.Z - 0.3, hr.X + 0.07, hr.Y + 0.07, hr.Z - 0.08))
            A((60, 50, 40), mbox(hr.X - 0.02, hr.Y - 0.02, hr.Z - 0.08, hr.X + 0.02, hr.Y + 0.02, hr.Z))
        if pr == 'book':
            A((170, 40, 40), mbox(-0.33, -0.1, sh - 0.32, -0.29, 0.12, sh - 0.06))
        if pr == 'scroll':
            A((236, 222, 180), mbox(hr.X - 0.04, hr.Y - 0.04, hr.Z - 0.22, hr.X + 0.04, hr.Y + 0.04, hr.Z + 0.06))
    if famous:
        A(GOLD, star_mesh(head_top(lk) + 0.45))
    return out


def dog_parts(col):
    out = [(col, mbox(-0.12, -0.32, 0.22, 0.12, 0.32, 0.42)), (col, mbox(-0.1, 0.28, 0.36, 0.1, 0.5, 0.54)),
           ((30, 26, 22), mbox(-0.03, 0.5, 0.42, 0.03, 0.54, 0.47))]
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append((col, mbox(sx * 0.08 - 0.03, sy * 0.24 - 0.03, 0, sx * 0.08 + 0.03, sy * 0.24 + 0.03, 0.24)))
    out.append((col, mbox(-0.02, -0.46, 0.38, 0.02, -0.3, 0.42)))
    return out


def place_parts(bag, parts, x, y, z, heading):
    for c, m in parts:
        m.Rotate(heading - math.pi / 2, Z, P(0, 0, 0))
        m.Translate(rg.Vector3d(x, y, z))
        bag(c, m)


# ---------------------------------------------------------------- paths, routes, timetable (same maths in the web viewer)
def seg_lengths(pts, closed):
    n = len(pts)
    segs = [(pts[i], pts[(i + 1) % n]) for i in range(n if closed else n - 1)]
    return segs, [math.sqrt(sum((b[k] - a[k]) ** 2 for k in range(3))) for a, b in segs]


def path_eval(pts, closed, mode, s):
    segs, ls = seg_lengths(pts, closed)
    L = sum(ls)
    back = False
    if mode == 'pingpong':
        s = s % (2 * L)
        if s > L:
            s, back = 2 * L - s, True
    else:
        s = s % L
    for (a, b), l in zip(segs, ls):
        if s <= l:
            t = s / l if l > 0 else 0
            x, y, z = (a[k] + (b[k] - a[k]) * t for k in range(3))
            hd = math.atan2(b[1] - a[1], b[0] - a[0]) + (math.pi if back else 0)
            return x, y, z, hd
        s -= l
    a, b = segs[-1]
    return b[0], b[1], b[2], math.atan2(b[1] - a[1], b[0] - a[0])


def path_len(pts, closed):
    return sum(seg_lengths(pts, closed)[1])


def path_project(pts, closed, px, py):
    """Distance along the path of the point nearest to (px, py)."""
    segs, ls = seg_lengths(pts, closed)
    best, acc, bs = 1e18, 0.0, 0.0
    for (a, b), l in zip(segs, ls):
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = max(0, min(1, ((px - a[0]) * dx + (py - a[1]) * dy) / (dx * dx + dy * dy))) if l > 0 else 0
        d = math.hypot(a[0] + dx * t - px, a[1] + dy * t - py)
        if d < best:
            best, bs = d, acc + l * t
        acc += l
    return bs


def rect_path(x0, y0, x1, y1, ccw=True):
    p = [[x0, y0, 0.0], [x1, y0, 0.0], [x1, y1, 0.0], [x0, y1, 0.0]]
    return p if ccw else p[::-1]


def circle_path(cx, cy, rad, n=56, ccw=True):
    p = [[cx + rad * math.cos(2 * math.pi * k / n), cy + rad * math.sin(2 * math.pi * k / n), 0.0] for k in range(n)]
    return p if ccw else p[::-1]


def bus_state(route, phase):
    """Where a bus is `phase` seconds into its cycle: (s along route, dwelling stop index or -1, seconds into dwell)."""
    v, D, prev = route['speed'], route['dwell'], 0.0
    for k, sk in enumerate(route['stops']):
        dt = (sk - prev) / v
        if phase < dt:
            return prev + v * phase, -1, 0.0
        phase -= dt
        if phase < D:
            return sk, k, phase
        phase -= D
        prev = sk
    return prev + v * phase, -1, 0.0


def bus_cycle(route):
    return route['length'] / route['speed'] + len(route['stops']) * route['dwell']


def bus_arrival(route, k):
    return route['stops'][k] / route['speed'] + k * route['dwell']


def bus_mesh_parts(col, L=12.0, W=2.55, Hb=3.1):
    out = [(col, mbox(-L / 2, -W / 2, 0.35, L / 2, W / 2, Hb)),
           (DGLASS, mbox(-L / 2 + 0.6, -W / 2 - 0.03, 1.4, L / 2 - 0.4, W / 2 + 0.03, 2.6)),
           (DGLASS, mbox(L / 2 - 0.05, -W / 2 + 0.15, 1.0, L / 2 + 0.03, W / 2 - 0.15, 2.7)),
           ((240, 240, 236), mbox(-L / 2 + 0.3, -W / 2 + 0.2, Hb, L / 2 - 0.3, W / 2 - 0.2, Hb + 0.25)),
           ((20, 20, 22), mbox(L / 2 - 1.6, -W / 2 - 0.04, 0.4, L / 2 - 0.5, -W / 2 + 0.02, 2.5)),
           ((20, 20, 22), mbox(-0.6, -W / 2 - 0.04, 0.4, 0.5, -W / 2 + 0.02, 2.5))]
    for x in (-L / 2 + 2.2, L / 2 - 2.6):
        for sy in (-1, 1):
            out.append(((22, 22, 24), mdisc(P(x, sy * (W / 2 - 0.3), 0.45), (0, 1, 0), 0.45, t=0.3, seg=12)))
    return out


def car_parts(col):
    return [(col, mbox(-2.1, -0.9, 0.25, 2.1, 0.9, 1.0)), (DGLASS, mbox(-1.1, -0.82, 1.0, 0.9, 0.82, 1.5)),
            ((22, 22, 24), mbox(-1.5, -0.95, 0.0, -0.9, 0.95, 0.5)), ((22, 22, 24), mbox(0.9, -0.95, 0.0, 1.5, 0.95, 0.5))]


def build_people():
    r = random.Random(4711)
    people = []

    def addp(**kw):
        kw['id'] = len(people)
        people.append(kw)
        return kw
    SHOP_BLOCKS = {(2, 6), (6, 1), (6, 5), (6, 4)}

    def clear_union(i0, j0, i1, j1):
        return all((i, j) not in SHOP_BLOCKS and not (3 <= i <= 4 and 3 <= j <= 4)
                   for i in range(i0, i1 + 1) for j in range(j0, j1 + 1))

    def block_of(x, y):
        return int((x + HALF) // PITCH), int((y + HALF) // PITCH)

    def loop(i0, j0, i1, j1, inset, ccw):
        return rect_path(bx(i0) + inset, bx(j0) + inset, bx(i1) + BLK - inset, bx(j1) + BLK - inset, ccw)

    # --- bus routes, stops and timetable
    routes = []

    def route(rid, name, col, corners, stop_pts, wait_off, nbus):
        pts = [[x, y, 0.0] for x, y in corners]
        rt = dict(id=rid, name=name, color=col, pts=pts, closed=True, speed=9.0, dwell=9.0, wait=wait_off,
                  length=path_len(pts, True))
        rt['stops'] = sorted(path_project(pts, True, x, y) for x, y in stop_pts)
        rt['buses'] = nbus
        routes.append(rt)
        return rt
    r1 = route(1, "Line 1 · Inner Ring", (194, 52, 40), [(-195, -195), (195, -195), (195, 195), (-195, 195)],
               [(-130, -195), (130, -195), (195, -130), (195, 130), (130, 195), (-60, 195), (-195, 130), (-195, -130)], 5.4, 2)
    r2 = route(2, "Line 2 · Outer Ring", (226, 176, 40), [(-383, 383), (383, 383), (383, -383), (-383, -383)],
               [(-144, 383), (144, 383), (383, 144), (383, -144), (144, -383), (-144, -383), (-383, -144), (-383, 144)], 7.4, 3)

    def stop_frame(rt, k):
        x, y, z, hd = path_eval(rt['pts'], True, 'loop', rt['stops'][k] + 0.01)
        d = (math.cos(hd), math.sin(hd))
        rn = (d[1], -d[0])
        return (x + rn[0] * rt['wait'], y + rn[1] * rt['wait']), d, rn

    corb = FAMOUS_POS["Le Corbusier"]
    corb_stop = min(range(len(r1['stops'])), key=lambda k: math.dist(stop_frame(r1, k)[0], corb[:2]))
    C1 = bus_cycle(r1)
    off0 = (bus_arrival(r1, corb_stop) - TS) % C1
    r1['offsets'] = [off0, (off0 + C1 / 2) % C1]
    C2 = bus_cycle(r2)
    r2['offsets'] = [k * C2 / 3 for k in range(3)]

    # --- famous residents
    def fam(name, act, **kw):
        return addp(kind='famous', name=name, look=LOOKS[name], act=act, **kw)
    for name, pos in FAMOUS_POS.items():
        if name in ("Immanuel Kant", "Friedrich Nietzsche", "Socrates", "Diogenes", "Henry David Thoreau", "Heraclitus",
                    "Le Corbusier", "Albert Camus", "Mies van der Rohe", "Robert Venturi", "Plato", "Ludwig Wittgenstein",
                    "Confucius", "Laozi", "Antoni Gaudí"):
            continue
        i, j = block_of(pos[0], pos[1])
        pth = loop(i, j, i, j, 1.1, r.random() < 0.5)
        fam(name, 'walk', path=pth, closed=True, mode='loop', speed=round(r.uniform(1.0, 1.4), 2), s0=r.uniform(0, 320))
    kx, ky, _ = FAMOUS_POS["Immanuel Kant"]
    i, j = block_of(kx, ky)
    kp = loop(i, j, i, j, 1.1, True)
    fam("Immanuel Kant", 'walk', path=kp, closed=True, mode='loop', speed=1.0, s0=path_project(kp, True, kx, ky) - 1200.0)
    # Nietzsche: down the mountain on a spiral path, into the city, and back up
    nx, ny, _ = FAMOUS_POS["Friedrich Nietzsche"]
    npth = []
    for k in range(90):
        t = k / 89.
        rad = 4 + 56 * t
        a = math.pi / 2 + t * 2.3 * 2 * math.pi
        npth.append([nx + rad * math.cos(a), ny + rad * math.sin(a), 0.0])
    end = npth[-1]
    for q in range(1, 6):
        npth.append([end[0] + (0 - end[0]) * q / 5., end[1] + (HALF + 8 - end[1]) * q / 5., 0.0])
    mesh = MOUNTAIN[0] if MOUNTAIN else None
    for p in npth:
        if mesh:
            hit = rg.Intersect.Intersection.MeshRay(mesh, rg.Ray3d(P(p[0], p[1], 200), rg.Vector3d(0, 0, -1)))
            if hit >= 0:
                p[2] = max(0.0, 200 - hit) + 0.05
    NL = path_len(npth, False)
    fam("Friedrich Nietzsche", 'walk', path=npth, closed=False, mode='pingpong', speed=0.9, s0=0.35 * NL - 0.9 * 480)
    # the Agora: Socrates questions three citizens; Diogenes searches with his lamp
    sx_, sy_ = -44.0, -37.0
    for k in range(4):
        a = math.pi / 2 + k * math.pi / 2
        px, py = sx_ + 1.25 * math.cos(a), sy_ + 1.25 * math.sin(a)
        face = math.atan2(sy_ - py, sx_ - px)
        if k == 0:
            fam("Socrates", 'stand', at=[px, py, 0.12], face=face, gesture='talk')
        else:
            addp(kind='citizen', look=citizen_look(r), act='stand', at=[px, py, 0.12], face=face, gesture='listen')
    fam("Diogenes", 'walk', path=[[-62, -64, 0.12], [-36, -64, 0.12], [-36, -44, 0.12], [-62, -44, 0.12]], closed=True,
        mode='loop', speed=0.55, s0=10.0)
    fam("Henry David Thoreau", 'stand', at=[47.5, 11.8, 0.0], face=math.pi / 2, gesture='idle')
    fam("Heraclitus", 'stand', at=[-142.0, -427.6, 0.0], face=-math.pi / 2, gesture='idle')
    gx, gy, _ = FAMOUS_POS["Antoni Gaudí"]
    fam("Antoni Gaudí", 'stand', at=[gx + 2, gy - 16.4, 0.0], face=math.pi / 2, gesture='look')
    fam("Mies van der Rohe", 'stand', at=[-150.0, 198.4, 0.0], face=math.pi / 2, gesture='shop')
    fam("Robert Venturi", 'stand', at=[-148.6, 198.4, 0.0], face=math.pi / 2, gesture='shop')
    cfx, cfy = PUBLIC_POS["CAFÉ OF DEBATES"]
    fam("Plato", 'stand', at=[cfx - 4.6, cfy - 7.5, 0.0], face=0.0, gesture='talk')
    fam("Ludwig Wittgenstein", 'stand', at=[cfx - 3.4, cfy - 7.5, 0.0], face=math.pi, gesture='idle')
    addp(kind='citizen', look=citizen_look(r), act='stand', at=[cfx + 3.5, cfy - 7.5, 0.0], face=0.0, gesture='talk')
    addp(kind='citizen', look=citizen_look(r), act='stand', at=[cfx + 4.6, cfy - 7.5, 0.0], face=math.pi, gesture='listen')
    fam("Albert Camus", 'run', path=rect_path(bx(3) + 1.2, bx(3) + 1.2, bx(4) + BLK - 1.2, bx(4) + BLK - 1.2, True),
        closed=True, mode='loop', speed=3.1, s0=100.0)
    cpath, lpath = circle_path(0, 0, 17.0, 64), circle_path(0, 0, 18.3, 64)
    fam("Confucius", 'walk', path=cpath, closed=True, mode='loop', speed=0.85, s0=20.0)
    fam("Laozi", 'walk', path=lpath, closed=True, mode='loop', speed=0.85 * 18.3 / 17.0, s0=20.0 * 18.3 / 17.0)

    # --- bus queues (Le Corbusier waits for Line 1)
    for rt in routes:
        for k in range(len(rt['stops'])):
            (wx, wy), d, rn = stop_frame(rt, k)
            face = math.atan2(-rn[1], -rn[0])
            n = r.randint(1, 3)
            who = []
            if rt is r1 and k == corb_stop:
                who.append(("Le Corbusier", LOOKS["Le Corbusier"]))
                n = 3
            who += [(None, citizen_look(r)) for _ in range(n)]
            for qi, (nm, lk) in enumerate(who):
                at = [wx - d[0] * 0.8 * qi, wy - d[1] * 0.8 * qi, 0.0]
                if nm:
                    fam(nm, 'queue', at=at, face=face, queue=[rt['id'], k, qi])
                else:
                    addp(kind='citizen', look=lk, act='queue', at=at, face=face, queue=[rt['id'], k, qi])

    # --- citizens walking around blocks (some with children or dogs)
    n = 0
    while n < 150:
        w_, h_ = r.choice([1, 1, 1, 2, 2, 3]), r.choice([1, 1, 2, 2, 3])
        i0, j0 = r.randint(0, N - w_), r.randint(0, N - h_)
        i1, j1 = i0 + w_ - 1, j0 + h_ - 1
        if not clear_union(i0, j0, i1, j1):
            continue
        ccw = r.random() < 0.5
        pth = loop(i0, j0, i1, j1, 1.1, ccw)
        L = path_len(pth, True)
        s0, v = r.uniform(0, L), round(r.uniform(1.15, 1.5), 2)
        lk = citizen_look(r)
        roll = r.random()
        extra = {}
        if roll < 0.08:
            extra['dog'] = r.choice([(120, 84, 50), (230, 220, 200), (40, 36, 32), (196, 150, 90)])
        elif roll < 0.14:
            lk['prop'] = ['bag']
        addp(kind='citizen', look=lk, act='walk', path=pth, closed=True, mode='loop', speed=v, s0=s0, **extra)
        if roll > 0.88:
            inner = loop(i0, j0, i1, j1, 1.75, ccw)
            Li = path_len(inner, True)
            addp(kind='citizen', look=citizen_look(r, kid=True), act='walk', path=inner, closed=True, mode='loop',
                 speed=round(v * Li / L, 3), s0=s0 * Li / L)
        n += 1

    # --- morning runners: around the park, Walden Pond and the river promenade
    park_loop = rect_path(bx(3) + 1.2, bx(3) + 1.2, bx(4) + BLK - 1.2, bx(4) + BLK - 1.2, True)
    for pth, cnt in [(park_loop, 10), (circle_path(45, 45, 31, 64), 9), (rect_path(-178, -424, -16, -404), 7)]:
        L = path_len(pth, True)
        for _ in range(cnt):
            lk = citizen_look(r)
            lk['top'] = r.choice([(240, 90, 60), (60, 170, 200), (250, 220, 60), (240, 240, 236), (120, 200, 120)])
            lk['bottom'] = (36, 36, 40)
            lk['prop'] = None
            p_ = pth if r.random() < 0.7 else pth[::-1]
            addp(kind='citizen', look=lk, act='run', path=p_, closed=True, mode='loop', speed=round(r.uniform(2.5, 3.6), 2),
                 s0=r.uniform(0, L))

    # --- shopping: market stalls and the two high streets
    mx0, my0 = bx(7), bx(5)
    for i in range(6):
        for j in range(2):
            for q in range(r.randint(0, 2)):
                lk = citizen_look(r)
                if r.random() < 0.6:
                    lk['prop'] = ['bag']
                addp(kind='citizen', look=lk, act='stand', at=[mx0 + 10 + i * 11 + r.uniform(-1.5, 1.5), my0 + 7.4 + j * 10, 0.0],
                     face=math.pi / 2, gesture='shop')
    for (x0_, x1_, y_, face) in [(-180, -108, 198.4, math.pi / 2), (-180, -108, 281.6, -math.pi / 2),
                                 (204, 276, -198.4, -math.pi / 2), (204, 276, -281.6, math.pi / 2)]:
        for q in range(5):
            x = r.uniform(x0_, x1_)
            if -153 < x < -145:
                continue
            lk = citizen_look(r)
            lk['prop'] = ['bag'] if r.random() < 0.5 else None
            addp(kind='citizen', look=lk, act='stand', at=[x, y_, 0.0], face=face, gesture='shop')
    for (i, j) in [(2, 6), (6, 1)]:
        pth = rect_path(bx(i) - 1.4, bx(j) - 1.4, bx(i) + BLK + 1.4, bx(j) + BLK + 1.4, r.random() < 0.5)
        for _ in range(5):
            lk = citizen_look(r)
            lk['prop'] = ['bag']
            addp(kind='citizen', look=lk, act='walk', path=pth, closed=True, mode='loop', speed=round(r.uniform(1.0, 1.3), 2),
                 s0=r.uniform(0, path_len(pth, True)))

    # --- neighbours chatting on the pavement
    res_blocks = [(i, j) for i in range(N) for j in range(N)
                  if (i, j) not in OUTER and not (2 <= i <= 5 and 2 <= j <= 5)]
    for _ in range(12):
        i, j = r.choice(res_blocks)
        x0_, y0_ = bx(i), bx(j)
        t = r.randint(0, 4)
        cx_ = x0_ + 1.5 + 7.7 + t * 15.4
        cy_ = y0_ + 2.6 if r.random() < 0.5 else y0_ + BLK - 2.6
        k = r.choice([2, 2, 3])
        for q in range(k):
            a = 2 * math.pi * q / k + r.uniform(-0.2, 0.2)
            px, py = cx_ + 0.65 * math.cos(a), cy_ + 0.65 * math.sin(a)
            addp(kind='citizen', look=citizen_look(r), act='stand', at=[px, py, 0.0], face=math.atan2(cy_ - py, cx_ - px),
                 gesture='talk' if q == 0 else 'listen')

    # --- cars
    lanes = []
    for c in (-288.0, -96.0, 96.0, 288.0):
        lanes += [dict(a=[c + 3, -HALF - 20], b=[c + 3, HALF + 20]), dict(a=[c - 3, HALF + 20], b=[c - 3, -HALF - 20]),
                  dict(a=[-HALF - 20, c - 3], b=[HALF + 20, c - 3]), dict(a=[HALF + 20, c + 3], b=[-HALF - 20, c + 3])]
    CAR_COLS = [(196, 58, 50), (60, 92, 160), (232, 232, 232), (40, 40, 44), (150, 150, 156), (226, 176, 40), (70, 120, 90)]
    cars = []
    for li, ln in enumerate(lanes):
        Ll = math.dist(ln['a'], ln['b'])
        v = round(r.uniform(9.5, 12.5), 2)
        k = r.randint(3, 5)
        for q in range(k):
            cars.append(dict(lane=li, s0=round(q * Ll / k + r.uniform(0, Ll / k * 0.5), 1), v=v, color=r.choice(CAR_COLS)))

    # =========================================================== Rhino snapshot at TS (07:10)
    bags = {}

    def bag_for(layer_path):
        if layer_path not in bags:
            bags[layer_path] = Bag()
        return bags[layer_path]
    for p in people:
        lk = p['look']
        if p['act'] in ('walk', 'run'):
            s = p['s0'] + p['speed'] * TS
            x, y, z, hd = path_eval(p['path'], p['closed'], p['mode'], s)
            stride, amp = (2.4, 0.7) if p['act'] == 'run' else (1.4, 0.42)
            sw = amp * math.sin(2 * math.pi * s / stride)
        else:
            (x, y, z), hd, sw = p['at'], p['face'], 0.0
        is_f = p['kind'] == 'famous'
        lp = ("People & Traffic::Famous::" + p['name']) if is_f else "People & Traffic::Citizens"
        place_parts(bag_for(lp), figure_parts(lk, sw, is_f), x, y, z, hd)
        if p.get('dog'):
            ds = p['s0'] + p['speed'] * TS - 1.3
            dx, dy, dz, dh = path_eval(p['path'], p['closed'], p['mode'], ds)
            place_parts(bag_for("People & Traffic::Citizens"), dog_parts(p['dog']), dx, dy, dz, dh)
    for rt in routes:
        C = bus_cycle(rt)
        for b, off in enumerate(rt['offsets']):
            s, _, _ = bus_state(rt, (TS + off) % C)
            x, y, z, hd = path_eval(rt['pts'], True, 'loop', s - 6.0)
            parts = bus_mesh_parts(rt['color'])
            for c, m in parts:
                m.Rotate(hd, Z, P(0, 0, 0))
                m.Translate(rg.Vector3d(x, y, 0))
                bag_for("People & Traffic::Buses")(c, m)
        for k in range(len(rt['stops'])):                 # bus stop shelters (street furniture, kept in the web model)
            (wx, wy), d, rn = stop_frame(rt, k)
            sb = bag_for("Street Furniture::Bus Stops")
            o = (wx + rn[0] * 1.8, wy + rn[1] * 1.8, 0.0)
            u = (d[0], d[1], 0)
            nn = (rn[0], rn[1], 0)
            sb(STEEL, obox(o, u, UP, nn, -2.0, 2.0, 2.4, 2.55, -0.75, 0.75))
            sb(GLASS, obox(o, u, UP, nn, -2.0, 2.0, 0.1, 2.4, 0.6, 0.66))
            for a in (-1.9, 1.9):
                sb(STEEL, obox(o, u, UP, nn, a - 0.05, a + 0.05, 0, 2.4, 0.55, 0.7))
            sb(WOOD, obox(o, u, UP, nn, -1.5, 1.5, 0.42, 0.48, 0.15, 0.5))
            so = (wx + d[0] * 2.6, wy + d[1] * 2.6, 0.0)
            sb(STEEL, mcyl(so[0], so[1], 0, 0.05, 2.6, 6))
            sb(rt['color'], mdisc(P(so[0], so[1], 2.75), (d[0], d[1], 0), 0.32, t=0.05))
    for cr in cars:
        ln = lanes[cr['lane']]
        Ll = math.dist(ln['a'], ln['b'])
        s = (cr['s0'] + cr['v'] * TS) % Ll
        hx, hy = (ln['b'][0] - ln['a'][0]) / Ll, (ln['b'][1] - ln['a'][1]) / Ll
        x, y = ln['a'][0] + hx * s, ln['a'][1] + hy * s
        for c, m in car_parts(cr['color']):
            m.Rotate(math.atan2(hy, hx), Z, P(0, 0, 0))
            m.Translate(rg.Vector3d(x, y, 0))
            bag_for("People & Traffic::Cars")(c, m)
    for lp, bg in bags.items():
        use(lp, (200, 200, 200))
        bg.flush()

    # =========================================================== the plan, for the web viewer
    try:
        here = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        here = os.getcwd()
    rnd2 = lambda v: round(v, 2) if isinstance(v, float) else v

    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        return rnd2(o)
    plan = dict(start="06:40", snapshot=TS, span=EVENT_SPAN, daemons=clean(daemon_plan(people)), people=clean(people), lanes=clean(lanes), cars=clean(cars),
                routes=clean([{k: v for k, v in rt.items()} for rt in routes]),
                houses={k: clean(list(v)) for k, v in FAMOUS_POS.items()},
                notes={k: v['note'] for k, v in LOOKS.items()})
    with io.open(os.path.join(here, "daemon_city_people.json"), "w", encoding="utf-8") as fh:
        json.dump(plan, fh, ensure_ascii=False)
    print("People:", len(people), "famous:", sum(1 for p in people if p['kind'] == 'famous'), "cars:", len(cars))



# ================================================================= DAEMONS — houses rebuilt from misunderstandings
# Five daemons follow famous residents, misread their theories completely, break into their houses and rebuild
# them upside down. The rebuilt houses live on "Daemon Versions" (off by default); the web viewer animates the
# break-in and reconstruction from the schedule in DAEMONS.
PINKW, GOLDO, IVORY, TEALD = (238, 208, 206), (220, 178, 72), (250, 246, 236), (40, 140, 140)

DAEMONS = [
    dict(name="Antonym", color=(196, 40, 70), creed="Reads every sentence backwards.",
         events=[("Adolf Loos", 4800, "Ornament is required",
                  "Antonym read “Ornament is crime” and concluded that the crime was having too little of it. Pilasters, rosettes, garlands, gold, onion domes: Loos's white cube has never been so decorated."),
                 ("Mies van der Rohe", 6600, "Less? More!",
                  "“Less is more,” Mies said. Antonym heard “Less? More!” and kept adding: rooms on rooms, roofs on roofs, chimneys, flags, columns and garden gnomes. The glass pavilion is gone under all of it.")]),
    dict(name="Paraphrase", color=(70, 110, 220), creed="Retells every idea in its own words, which mean the opposite.",
         events=[("Buckminster Fuller", 5100, "Doing less with more",
                  "Fuller's dome did more with less. Paraphrase retold it as “doing less with more”: a solid concrete dome, eight buttresses, a plinth, and one tiny door you have to crawl through."),
                 ("Laozi", 6900, "Emptiness is wasted space",
                  "“It is the emptiness at the centre that makes the wheel useful.” Paraphrase thought that emptiness was simply wasted space, so it filled the whole wheel solid and piled everything it could find on top.")]),
    dict(name="Literal", color=(30, 150, 110), creed="Takes every metaphor literally.",
         events=[("Le Corbusier", 5400, "A machine, literally",
                  "“A house is a machine for living in.” Literal took him at his word: Villa Savoye now has wheels, gears, pistons, rivets, smokestacks and a giant wind-up key on the roof."),
                 ("Antoni Gaudí", 7200, "The curves returned to God",
                  "“The straight line belongs to men, the curved line to God.” Literal decided the curves had to be given back. Every wave, arch and spire has been straightened into grey boxes.")]),
    dict(name="Typo", color=(150, 70, 190), creed="Misreads exactly one word, every time.",
         events=[("Louis Sullivan", 5700, "Function follows form",
                  "Typo swapped two words: “function follows form.” So the form came first, upside down. The cornice sits on the ground, the shops hang 30 metres up, and the front door is reached by ladder."),
                 ("Robert Venturi", 7500, "Less is a box",
                  "“Less is a bore,” wrote Venturi. Typo read “less is a box” and delivered exactly that: one white box with no windows, no gable and no chimney. The sign out front now says I AM A BOX.")]),
    dict(name="Footnote", color=(232, 120, 30), creed="Only ever reads the footnotes.",
         events=[("Zaha Hadid", 6000, "Only right angles",
                  "“There are 360 degrees, so why stick to one?” Footnote skipped to the footnote, which says 90 of them are right angles, and rebuilt the flowing shell out of cubes."),
                 ("Immanuel Kant", 7800, "Never repeat a maxim",
                  "Kant: act only on a maxim you could will to be universal. Footnote found a note saying “no two cases are alike” and rebuilt the nine identical houses so that none resembles another.")]),
]
EVENT_SPAN = 45.0      # seconds from break-in to the finished daemon house


def inv_loos(cx, cy):
    """'Ornament is crime' misread: the crime is not having enough ornament."""
    bag = Bag()
    w, d, h = 14., 12., 10.
    x0, y0, x1, y1 = cx - w / 2, cy - d / 2, cx + w / 2, cy + d / 2
    add(cbox(cx, cy, 0, w, d, h), PINKW)
    add(cbox(cx, cy, 0, w + 1.2, d + 1.2, 0.9), IVORY)
    for f in 'SNEW':
        o, u, n, U = face_frame(x0, y0, x1, y1, f)
        k = int(U / 1.75)
        piers = [U * i / k for i in range(k + 1)]
        for a in piers:
            bag(IVORY, obox(o, u, UP, n, a - 0.22, a + 0.22, 0.9, h - 0.6, 0, 0.25))
            bag(GOLDO, obox(o, u, UP, n, a - 0.32, a + 0.32, h - 0.95, h - 0.6, 0, 0.35))
            bag(GOLDO, obox(o, u, UP, n, a - 0.3, a + 0.3, 0.9, 1.2, 0, 0.32))
        for i in range(k):
            a = (piers[i] + piers[i + 1]) / 2
            for zb in (2.0, 6.0):
                win(bag, o, u, n, a, zb, 0.8, 1.6, frame=GOLDO, ft=0.1)
                bag(IVORY, tri_prism(o, u, n, [(a - 0.6, zb + 1.75), (a + 0.6, zb + 1.75), (a, zb + 2.2)], 0.15))
                c = pt(o, u, UP, n, a, zb - 0.5, 0)
                bag(GOLDO, mdisc(c, n, 0.3, t=0.06, seg=12))
                bag(RED, mdisc(c, n, 0.15, t=0.09, seg=10))
            for q in range(9):
                s_ = q / 8.
                p = pt(o, u, UP, n, piers[i] + 0.35 + (piers[i + 1] - piers[i] - 0.7) * s_, h - 1.3 - 0.5 * math.sin(math.pi * s_), 0.18)
                bag((96, 150, 80), msph(p.X, p.Y, p.Z, 0.14, 6))
    add(cbox(cx, cy, h, w + 1.0, d + 1.0, 0.6), GOLDO)
    for f in 'SNEW':
        o, u, n, U = face_frame(x0 - 0.5, y0 - 0.5, x1 + 0.5, y1 + 0.5, f)
        for i in range(int(U / 0.45)):
            a = 0.25 + i * 0.45
            bag(IVORY, obox(o, u, UP, n, a - 0.1, a + 0.1, h - 0.2, h, 0, 0.2))
            bp = pt(o, u, UP, n, a, 0, -0.25)
            bag(IVORY, mcyl(bp.X, bp.Y, h + 0.6, 0.08, 0.75, 6))
        bag(IVORY, obox(o, u, UP, n, 0, U, h + 1.35, h + 1.5, -0.4, -0.1))
    for (sx, sy) in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
        tx, ty = cx + sx * (w / 2 - 1.1), cy + sy * (d / 2 - 1.1)
        add(cyl(tx, ty, h + 0.6, 1.0, 3.2), IVORY)
        bag(GOLDO, mcyl(tx, ty, h + 3.8, 1.1, 0.25, 16))
        bag(TEALD, ellipsoid_mesh(tx, ty, h + 4.9, 1.25, 1.25, 1.4, 14))
    dm = frustum_mesh(0.18, 0.0, 0, 1.6)
    for (sx, sy) in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
        m = dm.DuplicateMesh()
        m.Translate(rg.Vector3d(cx + sx * (w / 2 - 1.1), cy + sy * (d / 2 - 1.1), h + 6.0))
        bag(GOLDO, m)
    add(cyl(cx, cy, h + 0.6, 2.6, 1.6), IVORY)
    add(sph(cx, cy, h + 2.2, 2.9), GOLDO)
    bag(IVORY, mcyl(cx, cy, h + 5.0, 0.5, 1.0, 12))
    bag(GOLDO, msph(cx, cy, h + 6.3, 0.35, 10))
    for (sx, sy) in [(0, -1), (0, 1), (-1, 0), (1, 0)]:            # statues on the balustrade
        px, py = cx + sx * (w / 2 + 0.1), cy + sy * (d / 2 + 0.1)
        bag(IVORY, mbox(px - 0.3, py - 0.3, h + 1.5, px + 0.3, py + 0.3, h + 1.9))
        bag(IVORY, mcyl(px, py, h + 1.9, 0.22, 1.1, 8))
        bag(IVORY, msph(px, py, h + 3.15, 0.17, 8))
    stair(bag, IVORY, (cx, y0 - 5.0, 0), (0, 1, 0), 5.0, 6, 0.65, 0.15)
    for xx in (cx - 2.6, cx - 1.2, cx + 1.2, cx + 2.6):               # twisted columns
        for k in range(14):
            m = mbox(xx - 0.22, y0 - 1.4, 0.9 + k * 0.3, xx + 0.22, y0 - 0.96, 1.2 + k * 0.3)
            m.Rotate(math.radians(k * 18), Z, P(xx, y0 - 1.18, 0))
            bag(GOLDO if k % 2 else IVORY, m)
    bag(IVORY, mbox(cx - 3.2, y0 - 1.8, 5.1, cx + 3.2, y0, 5.6))
    o, u, n = (cx - 3.2, y0 - 1.8, 0), (1, 0, 0), (0, -1, 0)
    bag(GOLDO, tri_prism(o, u, n, [(0, 5.6), (6.4, 5.6), (3.2, 7.0)], 1.8))
    bag.flush()
    return h + 7.6


def inv_mies(cx, cy):
    """'Less is more' misread as 'Less? More!': rooms, roofs, chimneys, flags and gnomes."""
    r = random.Random(13)
    bag = Bag()
    rooms = []
    for lvl, cnt in enumerate([9, 6, 3]):
        for _ in range(cnt):
            w, d = r.uniform(3, 6), r.uniform(3, 5)
            if lvl == 0:
                x, y = r.uniform(cx - 7 + w / 2, cx + 14 - w / 2), r.uniform(cy - 6 + d / 2, cy + 6 - d / 2)
            else:
                base = r.choice([q for q in rooms if q[4] == lvl - 1])
                x, y = base[0] + r.uniform(-1, 1), base[1] + r.uniform(-1, 1)
            col = jit(r.choice(PASTELS + TOPS), r, 10)
            z = lvl * 3.2
            add(cbox(x, y, z, w, d, 3.2), col)
            m = rg.Mesh()
            facade_windows(m, x - w / 2, y - d / 2, x + w / 2, y + d / 2, z, z + 3.2, faces='NSEW', floor_h=3.2,
                           ww=0.45, wh=0.55, spacing=1.6, sill=1.3)
            bag(DGLASS, m)
            rooms.append((x, y, w, d, lvl))
    for (x, y, w, d, lvl) in rooms:
        top = (lvl + 1) * 3.2
        if any(q[4] == lvl + 1 and abs(q[0] - x) < 1.5 and abs(q[1] - y) < 1.5 for q in rooms):
            continue
        kind = r.choice(['gable', 'hip', 'dome', 'barrel', 'gambrel', 'pyramid'])
        rc = jit(r.choice(ROOFC), r, 15)
        if kind == 'hip':
            add(hip_roof(x, y, top, w + 0.6, d + 0.6, 1.8), rc)
        elif kind == 'pyramid':
            add(pyramid([P(x - w / 2, y - d / 2, top), P(x + w / 2, y - d / 2, top), P(x + w / 2, y + d / 2, top),
                         P(x - w / 2, y + d / 2, top)], P(x, y, top + 2.6)), rc)
        elif kind == 'dome':
            add(sph(x, y, top, min(w, d) / 2), GOLDO)
        else:
            add(profile_roof(x, y, top, w, d, kind, 1.8), rc)
        for _ in range(r.randint(1, 2)):
            bag(BRICK, mbox(x + r.uniform(-w / 3, w / 3) - 0.3, y + r.uniform(-d / 3, d / 3) - 0.3, top,
                            x + r.uniform(-w / 3, w / 3) + 0.3, y + r.uniform(-d / 3, d / 3) + 0.3, top + 3.5))
    for k in range(4):                                                         # flags
        x, y, w, d, lvl = r.choice(rooms)
        top = (lvl + 1) * 3.2
        bag(STEEL, mcyl(x, y, top, 0.05, 6.0, 6))
        bag(r.choice([RED, (40, 90, 170), YELLOW, (60, 150, 80)]), mbox(x, y - 0.02, top + 4.8, x + 1.5, y + 0.02, top + 5.8))
    for k in range(6):                                                         # columns of every order
        x = cx - 6.5 + k * 3.8
        bag(r.choice([IVORY, GOLDO, (200, 120, 140)]), mcyl(x, cy - 7.2, 0, 0.3, r.uniform(3, 6), 10))
    for k in range(3):                                                         # satellite dishes
        x, y, w, d, lvl = r.choice(rooms)
        bag((220, 220, 224), mdisc(P(x, y, (lvl + 1) * 3.2 + 0.9), (0.4, -0.5, 0.75), 0.7, t=0.08))
    for (gx, gy) in [(-5, -8.5), (-2.5, -9.0), (8, -8.6)]:                     # garden gnomes
        bag((60, 110, 190), mcyl(cx + gx, cy + gy, 0, 0.18, 0.4, 8))
        bag(SKIN0, msph(cx + gx, cy + gy, 0.5, 0.13, 8))
        hat = frustum_mesh(0.16, 0.0, 0.58, 0.95)
        hat.Translate(rg.Vector3d(cx + gx, cy + gy, 0))
        bag(RED, hat)
    bag.flush()
    return 13


def inv_sullivan(cx, cy):
    """'Form follows function' misread as 'function follows form': the tower stands on its head."""
    bag = Bag()
    ORN = (182, 104, 70)
    add(cbox(cx, cy, 0, 22.4, 22.4, 1.2), TERRA)                              # the cornice, on the ground
    add(cbox(cx, cy, 1.2, 18, 18, 3), TERRA)                                  # the attic, second from the bottom
    for f in 'SNEW':
        o, u, n, U = face_frame(cx - 9, cy - 9, cx + 9, cy + 9, f)
        for k in range(6):
            c = pt(o, u, UP, n, (k + 0.5) * U / 6, 2.7, 0)
            bag(ORN, mdisc(c, n, 0.8, t=0.05))
            bag(DGLASS, mdisc(c, n, 0.55, t=0.09))
    z = 4.2
    for k in range(9):                                                        # the shaft widens as it rises
        wk = 13 + k * 0.9
        bag(BRICK, mbox(cx - wk / 2, cy - wk / 2, z, cx + wk / 2, cy + wk / 2, z + 1.1))
        bag(DGLASS, mbox(cx - wk / 2 + 0.3, cy - wk / 2 + 0.3, z + 1.1, cx + wk / 2 - 0.3, cy + wk / 2 - 0.3, z + 3.3))
        for (sx, sy) in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
            bag(BRICK, mbox(cx + sx * wk / 2 - 0.5, cy + sy * wk / 2 - 0.5, z + 1.1, cx + sx * wk / 2 + 0.5, cy + sy * wk / 2 + 0.5, z + 3.3))
        for f in 'SNEW':
            o, u, n, U = face_frame(cx - wk / 2, cy - wk / 2, cx + wk / 2, cy + wk / 2, f)
            for i in range(1, 6):
                bag(ORN, obox(o, u, UP, n, U * i / 6 - 0.2, U * i / 6 + 0.2, z + 0.25, z + 0.85, 0, 0.09))
        z += 3.3
    add(cbox(cx, cy, z, 22, 22, 8), STONE)                                     # the shop base, 34 m up
    for f in 'SNEW':
        o, u, n, U = face_frame(cx - 11, cy - 11, cx + 11, cy + 11, f)
        for i in range(4):
            if f == 'S' and i in (1, 2):
                continue
            a0, a1 = 1.2 + i * (U - 2.4) / 4 + 0.35, 1.2 + (i + 1) * (U - 2.4) / 4 - 0.35
            bag(DGLASS, obox(o, u, UP, n, a0, a1, z + 0.6, z + 5.4, -0.05, 0.04))
            bag((118, 88, 52), obox(o, u, UP, n, a0 - 0.1, a1 + 0.1, z + 5.4, z + 5.6, 0, 0.1))
    add(box(cx - 2.4, cy - 11.1, z, cx + 2.4, cy - 10.7, z + 4.2), DWOOD)    # the front door, in the sky
    add(rg.Cylinder(rg.Circle(rg.Plane(P(cx, cy - 11.1, z + 4.2), rg.Vector3d.YAxis), 2.4), 0.4).ToBrep(True, True), DWOOD)
    for sx in (-0.45, 0.45):                                                   # ...reached by ladder
        bag(STEEL, mbox(cx + sx - 0.04, cy - 11.75, 1.2, cx + sx + 0.04, cy - 11.65, z + 0.3))
    zz = 1.5
    while zz < z:
        bag(STEEL, mbox(cx - 0.45, cy - 11.74, zz, cx + 0.45, cy - 11.66, zz + 0.05))
        zz += 0.35
    bag.flush()
    return z + 8


def gear_profile(cxp, czp, r, teeth, depth=0.4):
    n = teeth * 4
    return [(cxp + (r if k % 4 in (0, 1) else r - depth) * math.cos(2 * math.pi * k / n),
             czp + (r if k % 4 in (0, 1) else r - depth) * math.sin(2 * math.pi * k / n)) for k in range(n)]


def inv_corbusier(cx, cy):
    """'A house is a machine for living in', taken literally: wheels, gears, pistons, rivets, smokestacks, a key."""
    bag = Bag()
    s, z = 19., 3.2
    x0, y0, x1, y1 = cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2
    for xx in (cx - 6, cx + 6):                                               # it drives
        for yy, nn in ((y0 - 0.5, (0, -1, 0)), (y1 + 0.5, (0, 1, 0))):
            bag((30, 30, 32), mdisc(P(xx, yy - 0.4 * nn[1], 3.0), nn, 3.0, t=0.8, seg=28))
            bag(GOLDO, mdisc(P(xx, yy + 0.4 * nn[1], 3.0), nn, 0.9, t=0.15, seg=16))
    add(box(x0, y0, z, x1, y1, z + 6.5), (122, 126, 132))
    for f in 'SNEW':                                                          # rivets and portholes
        o, u, n, U = face_frame(x0, y0, x1, y1, f)
        for i in range(16):
            for zz in (z + 0.3, z + 6.2):
                p = pt(o, u, UP, n, 0.6 + i * (U - 1.2) / 15, zz, 0.03)
                bag((90, 92, 96), msph(p.X, p.Y, p.Z, 0.09, 6))
        for i in range(4):
            c = pt(o, u, UP, n, (i + 0.5) * U / 4, z + 3.4, 0)
            bag(GOLDO, mdisc(c, n, 0.9, t=0.06))
            bag(DGLASS, mdisc(c, n, 0.7, t=0.1))
    add(prism_xz(gear_profile(cx - 4, z + 3.2, 3.6, 14), y0 - 0.55, 0.5), (190, 50, 40))   # gears on the facade
    add(prism_xz(gear_profile(cx + 2.65, z + 4.4, 2.5, 10), y0 - 0.55, 0.5), (230, 180, 40))
    bag(STEEL, mdisc(P(cx - 4, y0 - 0.6, z + 3.2), (0, -1, 0), 0.5, t=0.2))
    bag(STEEL, mdisc(P(cx + 2.65, y0 - 0.6, z + 4.4), (0, -1, 0), 0.4, t=0.2))
    add(prism_yz([(cy + 3 + (3.0 if k % 4 in (0, 1) else 2.6) * math.cos(2 * math.pi * k / 48),
                   z + 3.2 + (3.0 if k % 4 in (0, 1) else 2.6) * math.sin(2 * math.pi * k / 48)) for k in range(48)], x1, 0.5), (60, 100, 180))
    for k in range(3):                                                         # pistons
        px = cx - 5 + k * 3.5
        add(cyl(px, cy + 5, z + 6.5, 0.8, 2.2), (170, 172, 176))
        bag(STEEL, mcyl(px, cy + 5, z + 8.7, 0.18, 1.6 + k * 0.6, 8))
        bag((170, 172, 176), mbox(px - 0.6, cy + 4.6, z + 10.3 + k * 0.6, px + 0.6, cy + 5.4, z + 10.6 + k * 0.6))
    for (sx_, h_) in ((-6, 12), (-3.5, 9.5)):                                 # smokestacks with smoke
        add(cyl(cx + sx_, cy - 5, z + 6.5, 1.0, h_), (150, 60, 50))
        for b_ in range(3):
            bag(IVORY, mcyl(cx + sx_, cy - 5, z + 8 + b_ * 2.8, 1.05, 0.35, 16))
        for q in range(4):
            bag((214, 214, 214), msph(cx + sx_ + q * 0.9, cy - 5 + q * 0.4, z + 6.5 + h_ + 0.8 + q * 1.1, 0.9 + q * 0.3, 8))
    add_pipe(rg.Curve.CreateInterpolatedCurve(plist([P(x0 - 0.4, cy - 7, z + 1), P(x0 - 0.6, cy - 2, z + 2.5), P(x0 - 0.4, cy + 3, z + 1.5),
                                                     P(x0 - 0.5, cy + 8, z + 5.5), P(x0 + 2, cy + 8, z + 7)]), 3), 0.3, (196, 120, 60))
    add(cyl(cx + 5, cy - 3, z + 6.5, 0.35, 2.6), GOLDO)                        # the wind-up key
    for sx_ in (-1, 1):
        bag(GOLDO, mdisc(P(cx + 5 + sx_ * 1.2, cy - 3, z + 10.0), (0, 1, 0), 1.2, t=0.3, seg=20))
        bag((122, 126, 132), mdisc(P(cx + 5 + sx_ * 1.2, cy - 3, z + 10.0), (0, 1, 0), 0.6, t=0.34, seg=16))
    bag.flush()
    return z + 6.5 + 12


def inv_hadid(cx, cy):
    """'There are 360 degrees, why stick to one?' — the footnote says 90 of them are right angles: voxels."""
    bag = Bag()
    v = 1.5

    def inside(x, y, z):
        t = (x - (cx - 15)) / 30.
        if t < 0 or t > 1:
            return False
        yc = cy + 6 * math.sin(t * math.pi * 1.3 - 0.6)
        ry = 4 + 3 * math.sin(t * math.pi)
        rz = 1.8 + 6 * math.sin(t * math.pi) ** 1.5
        a = 0.45 * math.sin(t * math.pi * 2)
        dy, dz = y - yc, z - rz
        uu, ww = dy * math.cos(a) + dz * math.sin(a), -dy * math.sin(a) + dz * math.cos(a)
        return (uu / ry) ** 2 + (ww / rz) ** 2 <= 1.0
    xs = [cx - 15 + v / 2 + i * v for i in range(int(30 / v))]
    ys = [cy - 14 + v / 2 + j * v for j in range(int(28 / v))]
    zs = [v / 2 + k * v for k in range(10)]
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            for k, z in enumerate(zs):
                if not inside(x, y, z):
                    continue
                if all(inside(x + dx, y + dy, z + dz) for dx, dy, dz in [(v, 0, 0), (-v, 0, 0), (0, v, 0), (0, -v, 0), (0, 0, v)]) and k > 0:
                    continue
                col = (238, 238, 236) if (i + j + k) % 2 else (206, 208, 214)
                bag(col, mbox(x - 0.48 * v, y - 0.48 * v, z - 0.5 * v, x + 0.48 * v, y + 0.48 * v, z + 0.48 * v))
    for k, off in enumerate([-10.5, 9.5]):                                    # the ribbons, as stairs
        for i in range(14):
            x = cx - 15 + i * 2.2
            y = cy + 6 * math.sin((i / 13.) * math.pi * 1.3 - 0.6) + off
            y = max(cy - 15.5, min(cy + 15, y))
            bag((226, 226, 224), mbox(x, y - 0.4, 0, x + 2.0, y + 0.4, 0.3 + 0.3 * (i % 3)))
    bag.flush()
    return 14


def inv_gaudi(cx, cy):
    """'The straight line belongs to men, the curved line to God' — taken literally: the curves were given back."""
    bag = Bag()
    G1, G2 = (198, 194, 186), (168, 166, 160)
    add(cbox(cx, cy, 0, 26, 20, 7), G1)
    window_rows(bag, cx - 13, cy - 10, cx + 13, cy + 10, 'SNEW', [1.2, 4.2], 2.4, 1.2, 1.6, frame=G2)
    for zf in (2.3, 4.6):
        bag(G2, mbox(cx - 13.6, cy - 10.6, zf, cx + 13.6, cy + 10.6, zf + 0.15))
        for (p0, p1) in [((cx - 13.6, cy - 10.6), (cx + 13.6, cy - 10.6)), ((cx + 13.6, cy - 10.6), (cx + 13.6, cy + 10.6)),
                         ((cx + 13.6, cy + 10.6), (cx - 13.6, cy + 10.6)), ((cx - 13.6, cy + 10.6), (cx - 13.6, cy - 10.6))]:
            railing(bag, (70, 70, 72), p0, p1, zf + 0.15, 0.9, 0.8)
    add(cbox(cx, cy, 7, 26.6, 20.6, 0.4), G2)
    for k in range(6):                                                         # the arches, squared
        x = cx - 7.5 + k * 3
        bag(G1, mbox(x - 0.3, cy - 4.3, 7.4, x + 0.3, cy - 3.7, 11.5))
        bag(G1, mbox(x - 0.3, cy + 3.7, 7.4, x + 0.3, cy + 4.3, 11.5))
        bag(G1, mbox(x - 0.3, cy - 4.3, 11.5, x + 0.3, cy + 4.3, 12.1))
    for (dx, dy, hh) in [(-6, 6, 26), (-2, 8, 30), (2, 8, 30), (6, 6, 26)]:   # the spires, squared
        add(box(cx + dx - 1.2, cy + dy - 1.2, 7.4, cx + dx + 1.2, cy + dy + 1.2, hh - 2), G1)
        add(pyramid([P(cx + dx - 1.3, cy + dy - 1.3, hh - 2), P(cx + dx + 1.3, cy + dy - 1.3, hh - 2),
                     P(cx + dx + 1.3, cy + dy + 1.3, hh - 2), P(cx + dx - 1.3, cy + dy + 1.3, hh - 2)], P(cx + dx, cy + dy, hh + 1)), G2)
    for (wx, wy) in [(-11, 2), (11, 2), (-10, -4), (10, -4)]:                 # chimneys, cubed
        bag(G2, mbox(cx + wx - 0.7, cy + wy - 0.7, 7.4, cx + wx + 0.7, cy + wy + 0.7, 9.4))
    bag(G2, mbox(cx - 9, cy - 7.4, 7.4, cx + 9, cy - 6.6, 8.6))                # the dragon, flattened
    bag(G2, mbox(cx - 13, cy - 15, 0, cx + 13, cy - 14.2, 0.45))              # the bench, straightened
    bag.flush()
    return 31


def inv_fuller(cx, cy):
    """'Doing more with less' retold as 'doing less with more': solid concrete, buttresses, one tiny door."""
    bag = Bag()
    dx, dy, R_ = cx, cy + 1, 10.0
    add(cyl(dx, dy, 0, R_ + 1.5, 1.5), CONC)
    prof = pline([P(dx + R_ * math.cos(math.pi / 2 * k / 16.), dy, 1.5 + R_ * math.sin(math.pi / 2 * k / 16.)) for k in range(17)] +
                 [P(dx, dy, 1.5)])
    rs = rg.RevSurface.Create(prof, rg.Line(P(dx, dy, 0), P(dx, dy, 1)))
    if rs:
        add(rs.ToBrep(), (150, 150, 146))
    for k in range(8):
        b = prism_xz([(dx + R_ - 0.4, 1.5), (dx + R_ + 4.5, 1.5), (dx + R_ - 0.4, 8.5)], dy - 0.8, 1.6)
        b.Rotate(math.radians(k * 45 + 22.5), Z, P(dx, dy, 0))
        add(b, CONC)
    bag(DWOOD, mbox(dx - 0.35, dy - R_ - 0.05, 1.5, dx + 0.35, dy - R_ + 0.6, 2.4))
    bag.flush()
    return 13


def inv_laozi(cx, cy):
    """'It is the emptiness that makes it useful' retold as 'emptiness is wasted space': filled, then piled high."""
    r = random.Random(21)
    bag = Bag()
    add(cyl(cx, cy, 0, 14.2, 4.6), (206, 194, 172))
    for k in range(70):
        rr = 11.5 * math.sqrt(r.random())
        a = r.uniform(0, 2 * math.pi)
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        zb = 4.6 + (1 - rr / 11.5) * 6.0 * r.random()
        sz = r.uniform(0.8, 2.0)
        col = jit(r.choice(TOPS + [WOOD, (150, 112, 74), GOLDO]), r, 12)
        if r.random() < 0.7:
            m = mbox(x - sz / 2, y - sz / 2, zb, x + sz / 2, y + sz / 2, zb + sz * r.uniform(0.6, 1.2))
            m.Rotate(r.uniform(0, math.pi), Z, P(x, y, 0))
        else:
            m = mcyl(x, y, zb, sz * 0.45, sz, 12)
        bag(col, m)
    bag.flush()
    return 12


def inv_venturi(cx, cy):
    """'Less is a bore' misread as 'less is a box': a blank white box."""
    bag = Bag()
    add(cbox(cx, cy + 2, 0, 18, 9, 4), (246, 246, 244))
    for xp in (cx + 3, cx + 14.5):
        add(cyl(xp, cy - 13, 0, 0.22, 8), (230, 230, 228))
    add(box(cx + 2, cy - 13.2, 8, cx + 15.5, cy - 12.8, 11), (246, 246, 244))
    add_text("I AM A BOX", rg.Plane(P(cx + 4.2, cy - 13.3, 8.9), rg.Vector3d.XAxis, Z), 1.4, (150, 150, 150))
    bag.flush()
    return 11


def inv_kant(cx, cy):
    """Kant's universal maxim, read from a footnote as 'never repeat a maxim': nine houses, no two alike."""
    bag = Bag()
    P_ = lambda i, j: (cx + i * 11, cy + j * 11)
    x, y = P_(-1, -1); add(cyl(x, y, 0, 2.6, 9), (60, 100, 190)); add(cone(x, y, 9, 3.0, 3.5), RED)
    x, y = P_(0, -1); add(prism_yz([(y - 3.5, 0), (y + 3.5, 0), (y, 7.5)], x - 3.5, 7), (230, 130, 50))
    x, y = P_(1, -1); add(sph(x, y, 0, 3.6), (246, 246, 240)); bag(DWOOD, mbox(x - 0.5, y - 3.62, 0, x + 0.5, y - 3.2, 2.0))
    x, y = P_(-1, 0); b = cbox(x, y, 0, 6, 6, 4.5); b.Rotate(math.radians(14), rg.Vector3d.XAxis, P(x, y, 0)); add(b, (90, 160, 90))
    x, y = P_(0, 0); add(cbox(x, y, 0, 2.2, 2.2, 14), YELLOW)
    add(pyramid([P(x - 1.4, y - 1.4, 14), P(x + 1.4, y - 1.4, 14), P(x + 1.4, y + 1.4, 14), P(x - 1.4, y + 1.4, 14)], P(x, y, 17)), (30, 30, 34))
    x, y = P_(1, 0); add(cbox(x, y, 0, 8.5, 8.5, 2.4), (236, 170, 190)); add(cbox(x, y, 2.4, 9, 9, 0.3), (200, 200, 200))
    x, y = P_(-1, 1); add(prism(ngon(x, y, 4.2, 3, 90), 0, 5), (140, 90, 170))
    x, y = P_(0, 1); add(cyl(x, y, 0, 0.35, 3), STEEL)
    add(pyramid([P(x - 3, y - 3, 7), P(x + 3, y - 3, 7), P(x + 3, y + 3, 7), P(x - 3, y + 3, 7)], P(x, y, 2.6)), (40, 150, 150))
    x, y = P_(1, 1)
    for k in range(3):
        add(cbox(x, y, k * 2.6, 6 - k * 1.2, 6 - k * 1.2, 2.6, rot=k * 25), RED if k % 2 == 0 else (240, 240, 236))
    for (i, j) in [(-1, -1), (0, -1), (-1, 0), (0, 0), (1, 0), (-1, 1), (1, 1)]:
        x, y = P_(i, j)
        bag(DWOOD, mbox(x - 0.45, y - 3.7, 0, x + 0.45, y - 3.45, 2.1))
    bag.flush()
    return 17


INVERSIONS = {"Adolf Loos": inv_loos, "Mies van der Rohe": inv_mies, "Louis Sullivan": inv_sullivan,
              "Le Corbusier": inv_corbusier, "Zaha Hadid": inv_hadid, "Antoni Gaudí": inv_gaudi,
              "Buckminster Fuller": inv_fuller, "Laozi": inv_laozi, "Robert Venturi": inv_venturi,
              "Immanuel Kant": inv_kant}


def daemon_parts(col):
    """A floating daemon (feet at origin, facing +y): horns, glowing eyes, bat wings, a tail, and a book held upside down."""
    dark = tuple(max(0, c - 70) for c in col)
    out = [(col, ellipsoid_mesh(0, 0, 1.0, 0.36, 0.3, 0.55)), (col, frustum_mesh(0.06, 0.3, 0.25, 0.85)),
           (col, msph(0, 0.04, 1.72, 0.3, 12))]
    for sx in (-1, 1):
        h = frustum_mesh(0.08, 0.0, 0, 0.34)
        h.Rotate(sx * 0.45, rg.Vector3d.YAxis, P(0, 0, 0))
        h.Translate(rg.Vector3d(sx * 0.16, 0, 1.92))
        out.append(((40, 30, 36), h))
        out.append(((255, 226, 90), msph(sx * 0.11, 0.27, 1.78, 0.06, 6)))
        out.append((dark, mesh_from([P(sx * 0.18, -0.16, 1.35), P(sx * 0.95, -0.45, 1.95), P(sx * 0.8, -0.5, 1.0), P(sx * 0.5, -0.35, 1.2)],
                                    [(0, 1, 2), (0, 2, 3), (2, 1, 0), (3, 2, 0)])))
        out.append((col, mbox(sx * 0.32 - 0.06, 0.05, 1.05, sx * 0.32 + 0.06, 0.38, 1.4)))
    for k in range(6):
        out.append((dark, msph(0, -0.3 - k * 0.12, 0.6 - k * 0.07 + 0.03 * k * k, 0.07 - k * 0.006, 6)))
    out.append((dark, pyramid([P(-0.1, -1.0, 0.75), P(0.1, -1.0, 0.75), P(0, -1.0, 0.95)], P(0, -1.18, 0.85))))
    out.append(((236, 230, 210), mbox(-0.2, 0.36, 1.0, 0.2, 0.42, 1.3)))      # the book, upside down
    out.append(((150, 40, 40), mbox(-0.21, 0.42, 0.98, 0.21, 0.44, 1.32)))
    return out


def tag_daemon_houses():
    """Name the houses the daemons can reach (every architect's, plus the philosophers' daemon targets) and the
    fixed daemon versions, so the web viewer can take them apart and rebuild them."""
    for L in list(doc.Layers):
        fp = L.FullPath
        name = fp.split("::")[-1]
        pref = None
        if fp == ROOT + "::Daemon Versions::" + name:
            pref = "D|"
        elif fp == ROOT + "::Architects::" + name or (fp == ROOT + "::Philosophers::" + name and name in INVERSIONS):
            pref = "O|"
        if pref:
            for o in doc.Objects.FindByLayer(L) or []:
                o.Attributes.Name = pref + name
                o.CommitChanges()


def build_daemon_versions():
    for name, fn in INVERSIONS.items():
        cx, cy, top = FAMOUS_POS[name]
        use("Daemon Versions::" + name, (150, 60, 160))
        fn(cx, cy)
    tag_daemon_houses()
    idx = doc.Layers.FindByFullPath(ROOT + "::Daemon Versions", -1)
    if idx >= 0:
        doc.Layers[idx].IsVisible = False


def person_at(p, t):
    if p.get('path'):
        return path_eval(p['path'], p['closed'], p['mode'], p['s0'] + p['speed'] * t)
    return p['at'][0], p['at'][1], p['at'][2], p['face']


def daemon_plan(people):
    """Schedule for the web viewer, plus each daemon in the Rhino snapshot, shadowing its first victim."""
    byname = {p['name']: p for p in people if p['kind'] == 'famous'}
    out = []
    for d in DAEMONS:
        evs = []
        for (fig, T, title, text) in d['events']:
            hx, hy, top = FAMOUS_POS[fig]
            evs.append(dict(figure=fig, T=T, house=[hx, hy, top], title=title, text=text))
        out.append(dict(name=d['name'], color=d['color'], creed=d['creed'], events=evs))
        x, y, z, hd = person_at(byname[evs[0]['figure']], TS)
        fx = x - math.cos(hd) * 2.2 + math.sin(hd) * 0.6
        fy = y - math.sin(hd) * 2.2 - math.cos(hd) * 0.6
        b = Bag()
        place_parts(b, daemon_parts(d['color']), fx, fy, z + 0.55, hd)
        use("People & Traffic::Daemons::" + d['name'], d['color'])
        b.flush()
    return out


def famous(group, name, theory, func, cx, cy, where):
    use("%s::%s" % (group, name), (200, 200, 200))
    top = func(cx, cy)
    label(cx, cy, top + 4, "%s\n%s" % (name.upper(), theory), group)
    LEGEND.append((group, name, theory, where))
    FAMOUS_POS[name] = (cx, cy, top)


def clear_city():
    for L in list(doc.Layers):
        if L.FullPath == ROOT or L.FullPath.startswith(ROOT + "::"):
            objs = doc.Objects.FindByLayer(L)
            if objs:
                for o in objs:
                    doc.Objects.Delete(o, True)


def street_marks():
    m = ACC['marks']
    for i in range(N - 1):
        c = bx(i) + BLK + ST / 2
        y = -HALF
        while y < HALF - 3:
            m.Append(mbox(c - 0.12, y, -0.15, c + 0.12, y + 3, -0.1))
            m.Append(mbox(y, c - 0.12, -0.15, y + 3, c + 0.12, -0.1))
            y += 9


def build():
    global GLASSMAT, WATERMAT
    GLASSMAT = material("DC Glass", (170, 210, 232), 0.45)
    WATERMAT = material("DC Water", (80, 140, 196), 0.15)
    rnd = random.Random(SEED)

    # ---- ground, streets, river
    use("Ground", MEADOW)
    add(box(-760, -760, -0.6, 760, 760, -0.3), MEADOW, "Meadow")
    add(box(-HALF - 20, -HALF - 20, -0.3, HALF + 20, HALF + 20, -0.15), ASPHALT, "Streets")
    street_marks()
    use("Landscape::River", WATER)
    add(box(-760, -470, -0.6, 760, -430, -0.12), WATER, "River", mat=WATERMAT)
    for i in (1, 3, 5):
        x = bx(i) + BLK + ST / 2
        add(box(x - 7, -478, 0.8, x + 7, -398, 1.6), CONC, "Bridge")
        for sx in (-1, 1):
            add(box(x + sx * 6.8 - 0.15, -478, 1.6, x + sx * 6.8 + 0.15, -398, 2.7), STEEL)
        for y in (-445, -455):
            add(cbox(x, y, -0.6, 10, 2, 1.4), CONC)
        use("Ground", MEADOW)
        add(box(x - 7, -620, -0.3, x + 7, -478, -0.15), ASPHALT)
        add(box(x - 7, -398, -0.3, x + 7, -396, -0.15), ASPHALT)
        use("Landscape::River", WATER)
    for k in range(40):
        tree(rnd.uniform(-700, 700), rnd.uniform(-425, -402), rnd=rnd)
        tree(rnd.uniform(-700, 700), rnd.uniform(-520, -478), rnd=rnd)

    # ---- blocks
    for i in range(N):
        for j in range(N):
            x0, y0 = bx(i), bx(j)
            x1, y1 = x0 + BLK, y0 + BLK
            if 3 <= i <= 4 and 3 <= j <= 4:
                continue
            ring_block = 2 <= i <= 5 and 2 <= j <= 5
            f = OUTER.get((i, j))
            use("Ground::Blocks", SIDEWALK)
            add(box(x0, y0, -0.15, x1, y1, 0.0), SIDEWALK)
            add(box(x0 + 3, y0 + 3, -0.1, x1 - 3, y1 - 3, 0.02), PAVING if f in PAVED else GRASS)
            if f is None:
                for t in range(6):
                    tree(x0 + 1.5 + t * 15.4, y0 + 1.5, rnd=rnd)
                    tree(x0 + 1.5 + t * 15.4, y1 - 1.5, rnd=rnd)
            if ring_block:
                continue
            if f is None:
                res_fill(x0 + 4, y0 + 4, x1 - 4, y1 - 4, rnd)
            else:
                use("Public & Commercial", (200, 200, 210))
                f(x0, y0, x1, y1, rnd)
                use("Public & Commercial", (200, 200, 210))

    # ---- inner ring: famous figures among ordinary neighbours
    items = [("Architects",) + a for a in ARCHITECTS] + [("Philosophers",) + p for p in PHILOSOPHERS_RING]
    items += [("Public", n, None, f) for n, f in PUBLIC_RING]
    parcels = []
    for i in range(2, 6):
        for j in range(2, 6):
            if 3 <= i <= 4 and 3 <= j <= 4:
                continue
            for q in range(2):
                for r_ in range(2):
                    parcels.append((bx(i) + 20 + q * 40, bx(j) + 20 + r_ * 40, i, j))
    items += [("House",)] * (len(parcels) - len(items))
    random.Random(42).shuffle(items)
    for (cx, cy, i, j), it in zip(parcels, items):
        where = "block (%d,%d)" % (i, j)
        if it[0] == "House":
            ordinary_house(cx - 17, cy - 17, cx + 17, cy + 17, rnd)
        elif it[0] == "Public":
            use("Public & Commercial", (200, 200, 210))
            top = it[3](cx, cy)
            label(cx, cy, top + 4, it[1])
            PUBLIC_POS[it[1]] = (cx, cy)
        else:
            famous(it[0], it[1], it[2], it[3], cx, cy, where)

    # ---- central park: agora, Walden pond, tholos of the daimonion
    use("Landscape::Central Park", GRASS)
    p0, p1 = bx(3), bx(4) + BLK
    add(box(p0, p0, -0.15, p1, p1, 0.0), SIDEWALK)
    add(box(p0 + 3, p0 + 3, -0.1, p1 - 3, p1 - 3, 0.02), (118, 170, 86))
    sand = (226, 214, 186)
    add(box(-2.5, p0 + 3, 0.02, 2.5, p1 - 3, 0.06), sand)
    add(box(p0 + 3, -2.5, 0.02, p1 - 3, 2.5, 0.06), sand)
    add(cbox(0, 0, 0.02, 236, 4, 0.03, rot=45), sand)
    add(cbox(0, 0, 0.02, 236, 4, 0.03, rot=-45), sand)
    pond = []
    for k in range(24):
        a = 2 * math.pi * k / 24
        rr = 22 + 4 * math.sin(3 * a) + 2 * math.cos(5 * a)
        pond.append(P(45 + rr * math.cos(a), 45 + rr * math.sin(a), 0.08))
    pc = rg.Curve.CreateInterpolatedCurve(plist(pond), 3, rg.CurveKnotStyle.ChordPeriodic)
    for b in rg.Brep.CreatePlanarBreps(pc, TOL) or []:
        add(b, WATER, "Walden Pond", mat=WATERMAT)
    add(box(-78, -78, 0.02, -18, -18, 0.12), PAVING, "Agora")
    # Greek theatre (NW)
    for k in range(7):
        rin, rout = 8 + k * 2.2, 10.2 + k * 2.2
        pts = [(-45 + rout * math.cos(math.pi * t / 16.), 40 + rout * math.sin(math.pi * t / 16.)) for t in range(17)]
        pts += [(-45 + rin * math.cos(math.pi * t / 16.), 40 + rin * math.sin(math.pi * t / 16.)) for t in range(16, -1, -1)]
        add(prism(pts, 0, 0.45 * (k + 1)), STONE)
    add(cbox(-45, 37, 0, 16, 5, 1.0), STONE)
    label(-45, 48, 6, "OPEN-AIR THEATRE")
    # tholos of the Daimonion (centre)
    for k in range(3):
        add(cyl(0, 0, k * 0.3, 8.5 - k * 0.6, 0.3), MARBLE)
    for k in range(12):
        a = 2 * math.pi * k / 12
        add(cyl(6.2 * math.cos(a), 6.2 * math.sin(a), 0.9, 0.35, 5.5), MARBLE)
    add(cyl(0, 0, 6.4, 7.0, 0.8), MARBLE)
    add(sph(0, 0, 7.2, 6.0), (120, 160, 150))
    label(0, 0, 16, "THOLOS OF THE DAIMONION\n(city centre – Socrates' inner voice)")

    famous("Philosophers", "Socrates", "“The unexamined life is not worth living.”", b_socrates, -48, -26, "the Agora, Central Park")
    famous("Philosophers", "Diogenes", "Cynicism – needing nothing, he lives in a barrel", b_diogenes, -50, -55, "the Agora, Central Park")
    famous("Philosophers", "Henry David Thoreau", "“Simplify, simplify.”", b_thoreau, 45, 9, "Walden Pond, Central Park")
    famous("Philosophers", "Heraclitus", "“Panta rhei” – everything flows", b_heraclitus, -150, -413, "the river bank")
    famous("Philosophers", "Friedrich Nietzsche", "Übermensch – “Thus Spoke Zarathustra”", b_nietzsche, 0, HALF + 110, "the mountain north of the city")

    for k in range(170):
        x, y = rnd.uniform(p0 + 6, p1 - 6), rnd.uniform(p0 + 6, p1 - 6)
        if math.hypot(x - 45, y - 45) < 35 or (-82 < x < -14 and -82 < y < -14) or math.hypot(x, y) < 22:
            continue
        if abs(x) < 4 or abs(y) < 4 or abs(abs(x) - abs(y)) < 4 or math.hypot(x + 45, y - 40) < 26:
            continue
        tree(x, y, rnd=rnd)

    # ---- merged meshes
    for k, (lp, col) in ACC_STYLE.items():
        if ACC[k].Vertices.Count:
            use(lp, col)
            ACC[k].Normals.ComputeNormals()
            add(ACC[k], col, k)

    # ---- labels
    for pt, text, group in LABELS:
        use("Labels::" + group, (30, 30, 30))
        dot = rg.TextDot(text, pt)
        dot.FontHeight = 11
        add(dot)

    # ---- a quiet morning: people, buses and cars
    build_people()

    # ---- the daemons' versions of ten houses (layer off by default)
    build_daemon_versions()


doc.Views.RedrawEnabled = False
try:
    clear_city()
    build()
finally:
    doc.Views.RedrawEnabled = True
    doc.Views.Redraw()

print("Ordinary houses:", HOUSE_N[0])
print("Famous residents:", len(LEGEND))
for g, n, t, w in LEGEND:
    print("%s | %s | %s | %s" % (g, n, t, w))
