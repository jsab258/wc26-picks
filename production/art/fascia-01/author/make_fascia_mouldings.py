#!/usr/bin/env python3
"""Station 2 AUTHOR for the fascia package: two shopfront mouldings as GLB.

WHAT THIS IS AND WHAT IT IS NOT. It is the fascia package's own authoring
recipe, the equivalent of the .glb that arrived in the post for the grate. It
is NOT a studio instrument: it measures nothing the studio reads, gates
nothing, prints no verdict key, and lives under production/art/fascia-01/
rather than under tools/. Jafar's ruling of 2026-09-09 (production/NOW.md 61)
is that NO NEW INSTRUMENT IS BUILT FOR THE ART LANE THIS WEEK, and the
verification of what this writes is done entirely by instruments that already
exist: tools/meshgen/meshgen.py's glb_stats reader, tools/ue/
import_prop_meshes.py --measure and --selftest, and tools/attribution-check.py.

WHY IT HAD TO BE WRITTEN AT ALL, said plainly rather than implied. Checked on
2026-09-09 in this container: `blender` is not on PATH, `bpy` does not import,
and neither trimesh nor pygltflib nor gltflib is installed. tools/meshgen's
`local` backend NORMALISES A MESH THAT ALREADY EXISTS and refuses without
Blender; the three recipes under tools/art-recipes are Blender recipes and the
blockout's own receipt says "no engine export". So the project owns a glTF
READER in two places and no glTF WRITER anywhere, and the twelve-package batch
needs one before any package can be a real mesh. That gap is the finding; this
file is the smallest thing that closes it for this package.

THE GEOMETRY IS AN EXTRUDED PROFILE, which is what a moulding is. A joiner
runs a section along a length; the silhouette is the whole read from the
street, and a box cannot have one. Both profiles are given below as explicit
(depth, height) point lists in metres, every number sourced in
production/art/fascia-01/01-SPEC-fascia-package.md.

THE ASSERTIONS HERE ARE CORRECTNESS, NOT MEASUREMENT. The writer refuses
rather than writing a plausible file: the profile must be a simple polygon
wound counter-clockwise, the swept solid must be closed (every directed edge
used exactly once, its reverse exactly once), its signed volume must be
positive so the normals point out, and the measured bounding box must equal the
declared dims to 0.0 mm on every axis. A mesh that fails any of those is the
silent failure the street cannot see: it photographs and a character walks
through it.

    python3 make_fascia_mouldings.py --out DIR
    python3 make_fascia_mouldings.py --out DIR --print-series
"""
import argparse
import json
import math
import os
import struct
import sys

# ---------------------------------------------------------------------------
# THE TWO PROFILES. Every number is in METRES and every one is sourced in the
# spec beside this file; the comment names the source so a reader here does not
# have to go and get it.
# ---------------------------------------------------------------------------

# CORNICE over the fascia band. Depth 0.2150 is one British brick on its
# length, the 215 mm the scene file's own facade note already uses as the
# module ("A British brick is 215 x 102.5 x 65 mm"). Height 0.1500 is two
# brick courses at the scene file's own brick_course_m of 0.075.
#
# THE LENGTH IS NOT THE BAY, AND THAT IS THE MEASUREMENT THAT SET IT. The bay
# is 6.0000 (east_parade_fascia0.sx_m), but the D5 downpipes stand on the party
# pilaster centres at x=9,15,21,27,33 and run from y=0.25 to y=6.30 at z=5.031
# with a 0.068 m diameter, measured out of
# production/specs/vignette-pieces.json on 2026-09-09. A 6.0000 run would pass
# straight through all five. So the run stops clear of the pipe on each side:
# 6.0000 - (0.068 + 2 x 0.0200) = 5.8920, where 0.0200 is the package
# clearance. A cornice that stops each side of a rainwater pipe is what a real
# terrace does, and the joint lands on the party wall where a joint belongs.
CORNICE = {
    "id": "fascia_cornice_01",
    "length_m": 5.8920,
    "depth_m": 0.2150,
    "height_m": 0.1500,
    # Six stations, five slabs: the run as one quad would make the corona
    # face a 5.892 x 0.048 sliver at 123:1, and a sliver shades as one flat
    # band across a whole bay. At 1.178 m per slab it is 25:1.
    "stations": 6,
    "taper": None,
    # (depth from the wall, height above the fascia top), counter-clockwise.
    "profile": [
        (0.0000, 0.0000),   # the wall, underside of the bed
        (0.1550, 0.0000),   # soffit, out past the fascia face at 0.1200
        (0.1550, 0.0120),   # the drip groove, up
        (0.1750, 0.0120),   # the drip groove, across
        (0.1750, 0.0000),   # the drip groove, down
        (0.2150, 0.0000),   # soffit to the outer arris
        (0.2150, 0.0480),   # the corona face, upright
        (0.2010, 0.0760),   # cyma recta, back and up
        (0.2070, 0.1060),   # out again for the cap
        (0.2070, 0.1210),   # the cap face
        (0.1500, 0.1500),   # the wash, falling outward at 27 degrees
        (0.0000, 0.1500),   # the top, back at the wall
    ],
}

# CONSOLE at each end of each bay's fascia. Height 0.5500 is the street's own
# fascia band (fascia_bottom 2.85 to the 3.40 underside of the first floor),
# so the console spans the band it terminates. Width 0.2400 is set by a
# MEASURED CLEARANCE and not by taste: the D5 downpipes stand on the party
# pilaster centres at x=9,15,21,27,33 with a 0.068 m diameter, and 0.2400 on a
# pilaster centre 0.175 m away leaves 21 mm of air. Depth 0.1800 projects
# past the 0.1200 fascia face and stops 0.0350 short of the cornice above it,
# because a cornice oversails its consoles.
CONSOLE = {
    "id": "fascia_console_01",
    "length_m": 0.2400,
    "depth_m": 0.1800,
    "height_m": 0.5500,
    "stations": 5,
    # The two outer slabs pull the profile in by one part in fifteen, which
    # puts a 12 mm chamfer down each side and leaves a raised centre panel.
    # A per-station taper rather than a stepped ring, so no quad is degenerate
    # and the solid stays closed.
    "taper": (0.933333333333, 1.0, 1.0, 1.0, 0.933333333333),
    "profile": [
        (0.0000, 0.0000),   # the wall, bottom of the console
        (0.0600, 0.0000),   # the toe
        (0.0740, 0.0260),   # the nose of the toe
        (0.0620, 0.0580),   # back in, the hollow of the scroll starts
        (0.0700, 0.1200),
        (0.0880, 0.1900),
        (0.1120, 0.2650),
        (0.1380, 0.3400),
        (0.1580, 0.4100),
        (0.1700, 0.4700),
        (0.1760, 0.5150),
        (0.1800, 0.5280),   # full projection at the neck
        (0.1800, 0.5500),   # the top, under the cornice
        (0.0000, 0.5500),   # the top, back at the wall
    ],
}

PACKAGES = [CORNICE, CONSOLE]

# One slot, no texture, no image, per production/specs/asset-interface.md:
# "One material slot. Unlit, untextured, plain." The street overwrites slot 0
# with its own surface material, so the colour here is only what a raw viewer
# shows. 0.62 grey at roughness 0.72 is paint on timber that has been on a
# seafront since before the player was born.
MATERIAL = {
    "name": "fascia_moulding_painted_timber",
    "alphaMode": "OPAQUE",
    "pbrMetallicRoughness": {
        "baseColorFactor": [0.62, 0.60, 0.57, 1.0],
        "metallicFactor": 0.0,
        "roughnessFactor": 0.72,
    },
}


# ---------------------------------------------------------------------------
# PURE GEOMETRY. No file touched above this line.
# ---------------------------------------------------------------------------

def signed_area(poly):
    """Twice the signed area of a closed polygon in the (depth, height) plane.

    Positive is counter-clockwise with depth to the right and height up, which
    is the orientation the sweep below assumes. Returned rather than asserted
    so the caller can print it.
    """
    s = 0.0
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        s += ax * by - bx * ay
    return s


def _cross(ox, oy, ax, ay, bx, by):
    return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox)


def _point_in_tri(px, py, ax, ay, bx, by, cx, cy):
    d1 = _cross(ax, ay, bx, by, px, py)
    d2 = _cross(bx, by, cx, cy, px, py)
    d3 = _cross(cx, cy, ax, ay, px, py)
    neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (neg and pos)


def earclip(poly):
    """Triangulate a simple counter-clockwise polygon. Indices into poly.

    Ear clipping, the plain version. It is here rather than imported because
    nothing in this container provides one, and a cornice profile is concave in
    three places (the drip groove, the cyma and the wash), so a fan would put
    triangles outside the section and the volume check below would catch it as
    a hole.
    """
    n = len(poly)
    if n < 3:
        raise ValueError("a profile with %d points is not a polygon" % n)
    idx = list(range(n))
    out = []
    guard = 0
    while len(idx) > 3:
        guard += 1
        if guard > 4 * n * n:
            raise ValueError("ear clipping did not converge: the profile is "
                             "probably self-intersecting")
        clipped = False
        m = len(idx)
        for k in range(m):
            i0, i1, i2 = idx[(k - 1) % m], idx[k], idx[(k + 1) % m]
            ax, ay = poly[i0]
            bx, by = poly[i1]
            cx, cy = poly[i2]
            if _cross(ax, ay, bx, by, cx, cy) <= 0.0:
                continue                      # reflex or collinear, not an ear
            bad = False
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                px, py = poly[j]
                if _point_in_tri(px, py, ax, ay, bx, by, cx, cy):
                    bad = True
                    break
            if bad:
                continue
            out.append((i0, i1, i2))
            idx.pop(k)
            clipped = True
            break
        if not clipped:
            raise ValueError("no ear found with %d points left: the profile is "
                             "not simple" % len(idx))
    out.append((idx[0], idx[1], idx[2]))
    return out


def build(pkg):
    """The swept solid. Returns (positions, normals, uvs, indices, stats).

    THE FRAME IS THE ONE asset-interface.md NAMES: metres, +Y up, -Z forward.
    The profile's DEPTH runs along -Z, so the projecting tip of the moulding is
    at local z minimum and the face that touches the building line is at local
    z maximum. That is why these two pieces are placed at yaw_deg 0 on the east
    frontage while awning_02 takes 180: the yaw rule in the scene file says
    outright that it is a fact about the file and is written per prop.

    The pivot is the bounding box centre, which the interface allows ("Pivot:
    anywhere you like") and which makes the measured box checkable by eye: it
    is symmetric about the origin on all three axes.
    """
    prof = pkg["profile"]
    n = len(prof)
    length, depth, height = pkg["length_m"], pkg["depth_m"], pkg["height_m"]
    nst = pkg["stations"]
    taper = pkg["taper"] or tuple([1.0] * nst)
    if len(taper) != nst:
        raise ValueError("%s: %d taper values for %d stations"
                         % (pkg["id"], len(taper), nst))
    area2 = signed_area(prof)
    if area2 <= 0.0:
        raise ValueError("%s: profile winds clockwise (2A=%.6f); the sweep "
                         "wants counter-clockwise" % (pkg["id"], area2))

    # Station x positions, and the vertex table keyed by (station, point).
    xs = [(-0.5 + (j / float(nst - 1))) * length for j in range(nst)]
    zc = depth * 0.5
    yc = height * 0.5

    def pos(j, i):
        d, h = prof[i]
        return (xs[j], h - yc, zc - d * taper[j])

    # Perimeter distance along the profile, for the v coordinate. Metre scale
    # on both axes so the street's TilingU and TilingV read as tiles per metre
    # rather than as a number somebody guessed.
    peri = [0.0]
    for i in range(n):
        d0, h0 = prof[i]
        d1, h1 = prof[(i + 1) % n]
        peri.append(peri[-1] + math.hypot(d1 - d0, h1 - h0))

    # THE FACE LIST. Each corner is (station, point, v), where v is the
    # distance travelled along the profile to that point IN METRES. The wrap
    # corner carries peri[n] rather than peri[0], because a quad whose two v
    # values are the full perimeter and zero folds its texture back over the
    # whole section, which is the kind of fault that only shows up once a
    # texture is bound and is free to rule out now.
    faces = []
    for j in range(nst - 1):
        for i in range(n):
            i2 = (i + 1) % n
            v0, v1 = peri[i], peri[i + 1]
            faces.append([(j, i, v0), (j, i2, v1),
                          (j + 1, i2, v1), (j + 1, i, v0)])
    # The two end caps. The profile is CCW seen from +X, so the cap at x max
    # takes it in order and the cap at x min takes it reversed.
    ears = earclip(prof)
    for a, b, c in ears:
        faces.append([(nst - 1, a, None), (nst - 1, b, None), (nst - 1, c, None)])
        faces.append([(0, c, None), (0, b, None), (0, a, None)])

    # CLOSED-SOLID CHECK, on the shared topology and before any vertex is
    # split for shading. Every directed edge exactly once; every undirected
    # edge exactly twice, once each way. A hole and a doubled face both show
    # up here, and neither shows up in a picture.
    seen = {}
    for f in faces:
        m = len(f)
        for k in range(m):
            e = ((f[k][0], f[k][1]), (f[(k + 1) % m][0], f[(k + 1) % m][1]))
            if e in seen:
                raise ValueError("%s: directed edge %s used twice"
                                 % (pkg["id"], e))
            seen[e] = True
    for (a, b) in list(seen):
        if (b, a) not in seen:
            raise ValueError("%s: edge %s->%s has no opposite, so the solid is "
                             "open" % (pkg["id"], a, b))

    # Per-face vertices so every arris is hard. A moulding with smoothed
    # normals reads as a soft bolster, and the shadow line under a cornice is
    # the entire point of having one.
    positions, normals, uvs, indices = [], [], [], []
    vol6 = 0.0
    tris = 0
    for f in faces:
        pts = [pos(j, i) for (j, i, _v) in f]
        nx, ny, nz = face_normal(pts)
        base = len(positions)
        for ((j, i, v), p) in zip(f, pts):
            if v is None:
                d, h = prof[i]
                u, vv = d * taper[j], h        # a cap is measured in section
            else:
                u, vv = p[0] + length * 0.5, v  # a wall runs along the length
            positions.append(p)
            normals.append((nx, ny, nz))
            uvs.append((u, vv))
        if len(f) == 4:
            indices += [base, base + 1, base + 2, base, base + 2, base + 3]
            tri_sets = [(pts[0], pts[1], pts[2]), (pts[0], pts[2], pts[3])]
        else:
            indices += [base, base + 1, base + 2]
            tri_sets = [(pts[0], pts[1], pts[2])]
        for (a, b, c) in tri_sets:
            tris += 1
            vol6 += (a[0] * (b[1] * c[2] - b[2] * c[1])
                     - a[1] * (b[0] * c[2] - b[2] * c[0])
                     + a[2] * (b[0] * c[1] - b[1] * c[0]))

    volume = vol6 / 6.0
    if volume <= 0.0:
        raise ValueError("%s: signed volume %.9f is not positive, so the faces "
                         "are wound inside out" % (pkg["id"], volume))

    lo = [min(p[k] for p in positions) for k in range(3)]
    hi = [max(p[k] for p in positions) for k in range(3)]
    got = [hi[k] - lo[k] for k in range(3)]
    want = [length, height, depth]
    worst_mm = max(abs(got[k] - want[k]) for k in range(3)) * 1000.0
    if worst_mm > 1e-6:
        raise ValueError("%s: measured box %s against declared %s, worst "
                         "%.6f mm" % (pkg["id"], got, want, worst_mm))

    stats = {
        "id": pkg["id"], "verts": len(positions), "tris": tris,
        "faces": len(faces), "quads": sum(1 for f in faces if len(f) == 4),
        "caps": sum(1 for f in faces if len(f) == 3),
        "profile_points": n, "stations": nst,
        "dims_m": [round(v, 4) for v in want],
        "box_worst_mm": worst_mm,
        "volume_m3": volume,
        "profile_2a": area2,
        "lo": lo, "hi": hi,
    }
    return positions, normals, uvs, indices, stats


def face_normal(pts):
    """Unit normal of a planar face from its first three points, CCW outward."""
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = pts[0], pts[1], pts[2]
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    L = math.sqrt(nx * nx + ny * ny + nz * nz)
    if L <= 0.0:
        raise ValueError("a face has no area: %s" % (pts,))
    return nx / L, ny / L, nz / L


# ---------------------------------------------------------------------------
# THE GLB WRITER. Version 2, one buffer, one BIN chunk, one mesh, one node.
# Deterministic: no timestamp, no generator version that moves, fixed float32
# packing and a fixed key order, so a regeneration is byte identical and a
# drift check can mean something.
# ---------------------------------------------------------------------------

def write_glb(path, name, positions, normals, uvs, indices):
    idx_fmt, idx_ct = ("<H", 5123) if len(positions) <= 65535 else ("<I", 5125)
    idx_bytes = b"".join(struct.pack(idx_fmt, i) for i in indices)
    pos_bytes = b"".join(struct.pack("<3f", *p) for p in positions)
    nrm_bytes = b"".join(struct.pack("<3f", *p) for p in normals)
    uv_bytes = b"".join(struct.pack("<2f", *p) for p in uvs)

    def pad4(b):
        return b + b"\x00" * ((4 - len(b) % 4) % 4)

    views, blob = [], b""
    for (data, target) in ((idx_bytes, 34963), (pos_bytes, 34962),
                           (nrm_bytes, 34962), (uv_bytes, 34962)):
        blob = pad4(blob)
        views.append({"buffer": 0, "byteOffset": len(blob),
                      "byteLength": len(data), "target": target})
        blob += data
    blob = pad4(blob)

    lo = [min(p[k] for p in positions) for k in range(3)]
    hi = [max(p[k] for p in positions) for k in range(3)]
    # THE MIN AND MAX ARE NOT OPTIONAL HERE. tools/meshgen/meshgen.py's
    # glb_stats counts a primitive into its bounds only when the POSITION
    # accessor carries min and max, and a primitive without them is skipped
    # in silence: the file would measure as no size at all.
    js = {
        "asset": {"version": "2.0", "generator": "LEDGER fascia package, "
                                                 "production/art/fascia-01"},
        "scene": 0,
        "scenes": [{"name": "Root Scene", "nodes": [0]}],
        "nodes": [{"name": name, "mesh": 0}],
        "meshes": [{"name": name, "primitives": [{
            "mode": 4, "material": 0, "indices": 0,
            "attributes": {"POSITION": 1, "NORMAL": 2, "TEXCOORD_0": 3},
        }]}],
        "materials": [MATERIAL],
        "accessors": [
            {"bufferView": 0, "componentType": idx_ct, "count": len(indices),
             "type": "SCALAR"},
            {"bufferView": 1, "componentType": 5126, "count": len(positions),
             "type": "VEC3", "min": [float("%.7g" % v) for v in lo],
             "max": [float("%.7g" % v) for v in hi]},
            {"bufferView": 2, "componentType": 5126, "count": len(normals),
             "type": "VEC3"},
            {"bufferView": 3, "componentType": 5126, "count": len(uvs),
             "type": "VEC2"},
        ],
        "bufferViews": views,
        "buffers": [{"byteLength": len(blob)}],
    }
    jtext = json.dumps(js, separators=(",", ":"), sort_keys=False).encode("utf-8")
    jtext = jtext + b" " * ((4 - len(jtext) % 4) % 4)
    total = 12 + 8 + len(jtext) + 8 + len(blob)
    out = struct.pack("<4sII", b"glTF", 2, total)
    out += struct.pack("<I4s", len(jtext), b"JSON") + jtext
    out += struct.pack("<I4s", len(blob), b"BIN\x00") + blob
    with open(path, "wb") as f:
        f.write(out)
    return len(out)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True, help="directory for the .glb files")
    ap.add_argument("--print-series", action="store_true",
                    help="print the per-package geometry series and stop")
    a = ap.parse_args(argv)
    rows = []
    for pkg in PACKAGES:
        P, N, U, I, st = build(pkg)
        rows.append((pkg, P, N, U, I, st))
    print("fascia package, authored geometry series over %d of %d package(s):"
          % (len(rows), len(PACKAGES)))
    for (pkg, P, N, U, I, st) in rows:
        print("  %-20s verts=%-5d tris=%-5d quads=%-4d capTris=%-3d "
              "dims=%s boxWorstMm=%.7f volumeM3=%.7f"
              % (st["id"], st["verts"], st["tris"], st["quads"], st["caps"],
                 st["dims_m"], st["box_worst_mm"], st["volume_m3"]))
    if a.print_series:
        return 0
    os.makedirs(a.out, exist_ok=True)
    for (pkg, P, N, U, I, st) in rows:
        path = os.path.join(a.out, pkg["id"] + ".glb")
        nbytes = write_glb(path, pkg["id"], P, N, U, I)
        print("  wrote %s bytes=%d meshNodes=1 materialSlots=1 images=0"
              % (path, nbytes))
    print("authoredPackages=%d/%d authoredMeshNodesEach=1 "
          "authoredBoxWorstMm=%.7f authoredStat=at-worst-over-packages"
          % (len(rows), len(PACKAGES),
             max(st["box_worst_mm"] for (_, _, _, _, _, st) in rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
