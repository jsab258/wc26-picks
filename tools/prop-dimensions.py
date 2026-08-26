#!/usr/bin/env python3
"""HOW BIG AND HOW HEAVY IS EACH FETCHED PROP MODEL.

WHY. `queue.md` carries the building-kit question as a TRADE rather than
an obvious win: our buildings are plain masses wearing 2K photographic
brick, the kit's are hand-modelled silhouettes wearing a flat palette
colormap, and Jafar's bar is "low poly is not going to cut it". Nothing
about that could be settled from the dev container because the FBX were
catalogued and not on disk. Eleven were fetched to be measured, and this
is the measuring.

TWO NUMBERS, BECAUSE THE TRADE HAS TWO SIDES.

SIZE decides whether a model can be used at all. The terraces are built
per parcel, and a kit building authored at 8x8m does not drop into a
6x12m plot however good it looks; that is a fact about geometry and no
amount of liking the silhouette changes it.

VERTEX COUNT decides whether it is an upgrade. `RealBodyCap`'s comment
prices a dozen skinned bodies at ~280k vertices, so that is the order
this scene is already built at and the number to compare against —
a "low poly" kit building at 200 vertices is not competing with our
photographic surfaces, it is competing with our BOX, and the box has
eight.

SETS NO THRESHOLD AND PICKS NOTHING. Rule 2: print the series, look,
then decide. Reuses the FBX reader from `body-proportions.py` rather
than carrying a second parser — one idea, one implementation.
"""

import importlib.util
import os
import re
import struct
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PROPS = os.path.join(HERE, "..", "ledger", "Assets", "Props")

_spec = importlib.util.spec_from_file_location(
    "body_proportions", os.path.join(HERE, "body-proportions.py"))
_bp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bp)

sys.path.insert(0, HERE)                       # tools/capsay.py
from capsay import cap as _cap, NOTHING_MEASURED   # noqa: E402


VERT_CAP = 10_000_000


def geometry(path):
    """(vertex count, (dx, dy, dz)) over every Geometry node in the file.

    Vertex ARRAYS are large, so `body-proportions` skips them by default.
    Here they are exactly what is wanted, so the cap is raised — these are
    prop models, not a city.

    AND IT IS PASSED, NOT ASSIGNED. The first version did

        keep = _bp.SMALL_ARRAY
        _bp.SMALL_ARRAY = 10_000_000
        root, _ = _bp.parse_fbx(path)

    which cannot work and did not: `SMALL_ARRAY` is a DEFAULT ARGUMENT of
    `parse_fbx`, `_read_node` and `_read_property`, and a Python default is
    evaluated once when the `def` runs. Rebinding the module global
    afterwards changes nothing any of those three functions will ever see.
    So every model was read at the 64-element cap — which is 21 vertices —
    and every Vertices array in the kit went past it and came back None.

    IT LOOKED LIKE A FACT ABOUT THE FILES. Eleven of twelve car-kit models
    printed `0  no vertex data` and the twelfth printed `40  110 x 110 x 5`,
    a flat plate, because `ambulance` happens to contain one sub-mesh small
    enough to squeeze under the cap. Read as geometry that is a kit of empty
    stubs with one broken tile in it; read correctly it is the reader
    refusing to inflate anything and saying so per model. Rule 3b — the zero
    had no denominator.

    AND THE FOOTER QUOTED A NUMBER THIS TOOL COULD NOT PRODUCE, which is how
    long it had been broken. It said `sedan` measures 150 x 145 x 255; a
    reader that inflates nothing cannot measure a sedan at all. So the line
    was printed by an earlier version, before `parse_fbx` grew the
    `max_array` PARAMETER that this file kept trying to set as a global —
    and 145 was wrong even then, by the 30 units of wheel that `assemble`
    below is about. The car is 135 tall. A stale number in a footer is a
    comment (rule 1's second corollary) and it decayed twice.

    The parameter was always there. `_read_property`'s own comment says why
    it is a parameter — "a module-level global that one caller raises for the
    other is a mutable global by another name, and this project has already
    paid for one of those" — and this file then did precisely that, under a
    comment saying it had lifted the cap.
    """
    root, _version = _bp.parse_fbx(path, max_array=VERT_CAP)
    parts = assemble(root)
    if not parts:
        return 0, None
    total = sum(n for _name, n, _lo, _hi in parts)
    lo = [min(p[2][a] for p in parts) for a in range(3)]
    hi = [max(p[3][a] for p in parts) for a in range(3)]
    return total, tuple(hi[a] - lo[a] for a in range(3))


def _id_of(node):
    """An FBX object's id is its first property."""
    return next((p for p in node.props if isinstance(p, int)), None)


def _name_of(node):
    raw = next((p for p in node.props if isinstance(p, str)), "")
    return raw.split("\x00")[0]


def _translation(model):
    """`Lcl Translation` from Properties70, or (0,0,0).

    Rotation and scaling are NOT read, and that is checked rather than
    assumed: every Model in the car kit and both city kits carries a
    translation and nothing else, so a matrix here would be three more
    ways to be wrong about files that do not use one. `--selftest`
    fails if a rotated or scaled Model ever appears.
    """
    p70 = model.find("Properties70")
    if p70 is None:
        return (0.0, 0.0, 0.0), False
    odd = False
    out = (0.0, 0.0, 0.0)
    for p in p70.children:
        vals = [v for v in p.props if not isinstance(v, tuple)]
        if not vals:
            continue
        nums = [v for v in vals if isinstance(v, float)]
        if vals[0] == "Lcl Translation" and len(nums) >= 3:
            out = tuple(nums[:3])
        elif vals[0] in ("Lcl Rotation", "Lcl Scaling"):
            ident = 1.0 if vals[0] == "Lcl Scaling" else 0.0
            if any(abs(v - ident) > 1e-6 for v in nums[:3]):
                odd = True
    return out, odd


def assemble(root):
    """Every mesh in the file, PLACED, as (name, verts, lo, hi) in file units.

    WHY THIS IS NOT A LOOP OVER `Geometry` NODES. The first version was, and
    it unioned coordinates from meshes that do not share a frame. A car in
    this kit is six objects — a body, four wheels and a grill — and each
    Geometry stores its vertices about its OWN origin, with the placement on
    the Model that owns it. Pooled raw, the four wheels contribute a
    -30..+30 box around the origin, so every vehicle in the kit read 30
    units taller than it is and the extra 30 was under the road.

    It is not a small error and it is not a random one: it is the same 30 on
    every row, so the table looked internally consistent and the ratios —
    the thing the footer tells you to read — were all wrong in the same
    direction. `sedan` printed 150 x 145 x 255 where the car is
    150 x 135 x 255, and its 115-unit body sits on 20 units of wheel.

    The accepting case is physical and `--selftest` asserts it: assembled
    properly, a road vehicle's lowest point is the tyre contact patch, so
    every vehicle in the car kit bottoms out at y=0. Before this it was -30
    for all of them, which is a car buried to its axles.
    """
    objects = root.find("Objects")
    conns = root.find("Connections")
    if objects is None:
        return []

    # child id -> parent id, from the OO connection records.
    parent = {}
    if conns is not None:
        for c in conns.children:
            vals = [p for p in c.props if not isinstance(p, tuple)]
            if len(vals) >= 3 and vals[0] == "OO":
                parent[vals[1]] = vals[2]

    models = {}
    for m in objects.find_all("Model"):
        mid = _id_of(m)
        if mid is None:
            continue
        t, odd = _translation(m)
        models[mid] = (_name_of(m), t, odd)

    parts = []
    for geom in objects.find_all("Geometry"):
        verts = geom.find("Vertices")
        if verts is None:
            continue
        data = next((p for p in verts.props if isinstance(p, tuple)), None)
        if not data:
            continue

        # Walk Geometry -> Model -> ... -> root, adding each translation.
        # A file with no Connections block leaves this at zero, which is
        # exactly the old behaviour and correct for a single-mesh model.
        off = [0.0, 0.0, 0.0]
        label = "?"
        node = parent.get(_id_of(geom))
        seen = set()
        while node is not None and node in models and node not in seen:
            seen.add(node)
            nm, t, odd = models[node]
            if label == "?":
                label = nm
            if odd:
                label += " (ROTATED/SCALED — not applied)"
            for a in range(3):
                off[a] += t[a]
            node = parent.get(node)

        xs = data[0::3]
        ys = data[1::3]
        zs = data[2::3]
        lo = (min(xs) + off[0], min(ys) + off[1], min(zs) + off[2])
        hi = (max(xs) + off[0], max(ys) + off[1], max(zs) + off[2])
        parts.append((label, len(data) // 3, lo, hi))
    return parts


CAR_KIT = os.path.join(os.path.normpath(PROPS), "car-kit")
SCRIPTS = os.path.join(HERE, "..", "ledger", "Assets", "Scripts")


def kit_key_paths():
    """{PropPrefab key: model path} over everything under Assets/Props.

    `KitCandidates` speaks FULL prefab keys since the OGA vehicle haul
    (two kits supply vehicles, so the old car_kit_ prefix assumption
    broke the moment the second kit arrived — this tool failed on the
    first run after the wire, correctly, because it was still gluing
    candidates onto the Kenney directory). Mirrors PropPrefab.Key: kit
    is the first directory under Props, stem is the filename, lowercase,
    spaces and dashes to underscores. The walk is sorted so two files
    minting one key resolve the way Unity's enumeration does — the later
    path wins, which both vehicle packs exercise with their Bus.fbx.
    """
    out = {}
    root = os.path.normpath(PROPS)
    for dirpath, dirnames, filenames in sorted(os.walk(root)):
        dirnames.sort()
        for fn in sorted(filenames):
            stem, ext = os.path.splitext(fn)
            if ext.lower() not in (".fbx", ".obj", ".glb", ".gltf"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), root)
            kit = rel.split(os.sep)[0] if os.sep in rel else "misc"
            key = (kit + "_" + stem).lower().replace(" ", "_").replace("-", "_")
            out[key] = os.path.join(dirpath, fn)
    return out


def read_kind_table():
    """{id: (length, width, height)} read out of Core/Traffic.cs."""
    src = open(os.path.join(SCRIPTS, "Core", "Traffic.cs"),
               encoding="utf-8").read()
    out = {}
    for m in re.finditer(
            r"Id\s*=\s*(\w+)Id\s*,.*?Length\s*=\s*([\d.]+)\s*,"
            r"\s*Width\s*=\s*([\d.]+)\s*,\s*Height\s*=\s*([\d.]+)",
            src, re.S):
        out[m.group(1).lower()] = tuple(float(m.group(i)) for i in (2, 3, 4))
    return out


def read_kit_map():
    """{kind id: first kit model name} read out of Game/TrafficHost.cs.

    Only the FIRST candidate of each kind, which is the one the offset picks
    for vehicle 0 and the one whose proportions stand for the slot. A kind
    returning `Array.Empty` has no model and is simply absent here.
    """
    src = open(os.path.join(SCRIPTS, "Game", "TrafficHost.cs"),
               encoding="utf-8").read()
    out = {}
    for m in re.finditer(
            r"case\s+Ledger\.Core\.VehicleKinds\.(\w+)Id\s*:\s*return\s+new\[\]\s*\{\s*\"([^\"]+)\"",
            src):
        out[m.group(1).lower()] = m.group(2)
    # `default:` dresses everything not named above, and `car` is the kind
    # that reaches it. Named explicitly rather than inferred, because a
    # silent miss here would drop a row from the table above and read as a
    # clean run.
    d = re.search(r"default:\s*return\s+new\[\]\s*\{\s*\"([^\"]+)\"", src)
    if d and "car" not in out:
        out["car"] = d.group(1)
    return out


def _pnode(name, *props, children=()):
    """One node of an FBX tree, BUILT rather than parsed. Used only by
    `synthetic_car`; nothing in the measuring path constructs nodes."""
    n = _bp.Node(name)
    n.props = list(props)
    n.children = list(children)
    return n


def _capped(names, n=4):
    """A comma list that SAYS WHEN IT BIT — `tools/capsay.py`, imported.

    This was a local `(+N more not shown)` until 26 Aug, which made it the
    SECOND implementation of the one idea this project has already paid for
    twice (`SpeechBubble`/`NpcWalker`, `verdict-keys`/`gates`). The count is
    now of the list AS HANDED IN, so a caller may not slice before calling.
    """
    return _cap(names, keep=n, width=40, sep=", ", tail="none")


#: The synthetic car's parts, in the same shape the real kit uses: each
#: mesh is modelled about its OWN origin and PLACED by its Model's
#: `Lcl Translation`. Read off `--parts police` rather than invented, so
#: the fixture reproduces the bug at the size it really had: police's
#: wheels are geometry -30..+30 hung at y=30 (world 0..60) and its body
#: is geometry 0..110 hung at y=20 (world 20..130).
#:
#:   name            geometry box (lo, hi)              placed at
_SYNTH_PARTS = (
    ("body", (-75.0, 0.0, -155.0), (75.0, 110.0, 135.0), (0.0, 20.0, 0.0)),
    ("wheel-front-left", (-15.0, -30.0, -30.0), (15.0, 30.0, 30.0), (45.0, 30.0, 81.0)),
    ("wheel-front-right", (-15.0, -30.0, -30.0), (15.0, 30.0, 30.0), (-45.0, 30.0, 81.0)),
    ("wheel-back-left", (-15.0, -30.0, -30.0), (15.0, 30.0, 30.0), (45.0, 30.0, -81.0)),
    ("wheel-back-right", (-15.0, -30.0, -30.0), (15.0, 30.0, 30.0), (-45.0, 30.0, -81.0)),
)

#: What the two readers must say about `_SYNTH_PARTS`, derived from it
#: above rather than typed twice: assembled, the tyres touch the road;
#: pooled, the wheels' own -30 becomes the car's floor.
SYNTH_FLOOR = min(lo[1] + at[1] for _n, lo, _hi, at in _SYNTH_PARTS)      # 0.0
SYNTH_POOLED = min(lo[1] for _n, lo, _hi, _at in _SYNTH_PARTS)            # -30.0


def synthetic_car():
    """A CAR THIS FILE BUILDS ITSELF — one body on four wheels, no file.

    WHY IT IS SYNTHETIC, which is the point of the rewrite. The rejecting
    case this replaces re-parsed `Props/car-kit/police.fbx` and asserted
    that a real shipped asset STILL REPRODUCES THE BUG — pooled floor
    under -1. Re-export police, or swap it for a pre-placed variant, and
    the selftest goes red for the asset having been FIXED, which is a
    sentence about a tool bug describing a project improvement.
    `tools/ref-bench.py` was pinned to `district_downtown` the same way
    and went red for the camera getting better. The accepting case above
    stays on the live kit, which is the right fixture for it and cannot
    be fooled by anything written here; only the rejecting half moves.

    WHICH LAYER THIS EXERCISES, AND WHICH IT DOES NOT. The tree goes
    straight to `assemble`, which is where the bug was, so the fixture
    covers the OO connection walk, the translation lookup and the
    per-part boxes — and it does NOT cover `_bp.parse_fbx`, the byte
    reader, because it never produces bytes. That layer's accepting case
    is the whole car kit a few lines up, parsed from disk every run.
    """
    objects, conns = [], []
    for i, (name, lo, hi, at) in enumerate(_SYNTH_PARTS):
        mid, gid = 100 + i, 200 + i
        # Eight corners of the part's box, about the part's own origin.
        verts = []
        for x in (lo[0], hi[0]):
            for y in (lo[1], hi[1]):
                for z in (lo[2], hi[2]):
                    verts += [x, y, z]
        objects.append(_pnode(
            "Model", mid, name + "\x00Model", "Mesh",
            children=(_pnode("Properties70", children=(
                _pnode("P", "Lcl Translation", "Lcl Translation", "", "A",
                       at[0], at[1], at[2]),)),)))
        objects.append(_pnode(
            "Geometry", gid, name + "\x00Geometry", "Mesh",
            children=(_pnode("Vertices", tuple(verts)),)))
        conns.append(_pnode("C", "OO", gid, mid))
    return _pnode("__root__",
                  children=(_pnode("Objects", children=tuple(objects)),
                            _pnode("Connections", children=tuple(conns))))


#: THE ARRAY-CAP FIXTURE — a lattice of vertices dense enough that the
#: DEFAULT cap must refuse it and the lifted cap must inflate it. 6^3 = 216
#: vertices is 648 doubles against `_bp.SMALL_ARRAY`'s 64 ELEMENTS (21
#: vertices); the selftest asserts that relation from the constants rather
#: than trusting the arithmetic written here.
#:
#: The size is invented and unlike any vehicle in the kit ON PURPOSE: nobody
#: reading `48/12/96` can mistake this fixture's numbers for a measurement of
#: a shipped asset, which is exactly the confusion the pin it replaces caused.
_CAP_N = 6
_CAP_SIZE = (48.0, 12.0, 96.0)
_CAP_AT = (13.0, 7.0, 5.0)            # a translation, so the OO walk runs too
CAP_VERTS = _CAP_N ** 3


def _fbx_prop(v):
    """One FBX property record. WRITER, not reader — the reader is
    `body-proportions._read_property` and there is still exactly one of it."""
    if isinstance(v, str):
        b = v.encode("utf-8")
        return b"S" + struct.pack("<I", len(b)) + b
    if isinstance(v, int):
        return b"L" + struct.pack("<q", v)
    if isinstance(v, float):
        return b"D" + struct.pack("<d", v)
    if isinstance(v, tuple):          # a double ARRAY, encoding 0 = uncompressed
        return (b"d" + struct.pack("<III", len(v), 0, 0)
                + struct.pack("<%dd" % len(v), *v))
    raise TypeError("no FBX property encoding for %r" % (v,))


_NULL_RECORD = b"\x00" * 13          # ends a child list in a pre-7500 file


def _fbx_node_bytes(node, offset):
    """A node record and everything under it, at a known absolute offset.

    `end_offset` is ABSOLUTE in this format, so the writer has to know where
    it sits — which is why this takes an offset rather than returning bytes
    to be concatenated blindly."""
    name = node.name.encode("utf-8")
    props = b"".join(_fbx_prop(p) for p in node.props)
    cur = offset + 12 + 1 + len(name) + len(props)
    kids = b""
    for c in node.children:
        b = _fbx_node_bytes(c, cur)
        kids += b
        cur += len(b)
    if node.children:
        kids += _NULL_RECORD
        cur += 13
    return (struct.pack("<III", cur, len(node.props), len(props))
            + bytes([len(name)]) + name + props + kids)


def write_synthetic_fbx(path, verts, at=_CAP_AT):
    """A REAL BINARY FBX ON DISK, written by this file, holding one mesh.

    WHY BYTES AND NOT A TREE. `synthetic_car` above builds `Node` objects and
    goes straight to `assemble`, and its own docstring says what that cannot
    reach: `_bp.parse_fbx`, the byte reader, where the ARRAY CAP lives. That
    layer's only fixture was `car-kit/police.fbx` with `total > 1000` and
    `100 < size[2] < 400` asserted on it — a shipped asset, 90 units of
    headroom, and a failure mode (a re-export at a different FBX unit scale)
    that moves by a factor of 100. So the accepting case for the byte reader
    is now a file with no asset behind it, and its expected numbers are
    DERIVED from `verts` rather than typed.
    """
    flat = tuple(c for v in verts for c in v)
    objects = [
        _pnode("Model", 100, "cap-fixture\x00Model", "Mesh",
               children=(_pnode("Properties70", children=(
                   _pnode("P", "Lcl Translation", "Lcl Translation", "", "A",
                          at[0], at[1], at[2]),)),)),
        _pnode("Geometry", 200, "cap-fixture\x00Geometry", "Mesh",
               children=(_pnode("Vertices", flat),)),
    ]
    top = [_pnode("Objects", children=tuple(objects)),
           _pnode("Connections", children=(_pnode("C", "OO", 200, 100),))]
    out = b"Kaydara FBX Binary  \x00\x1a\x00" + struct.pack("<I", 7400)
    for n in top:
        out += _fbx_node_bytes(n, len(out))
    out += _NULL_RECORD
    with open(path, "wb") as f:
        f.write(out)
    return len(out)


def cap_fixture_verts(n=_CAP_N, size=_CAP_SIZE):
    """`n**3` lattice points spanning exactly `size` from the origin."""
    step = [size[a] / (n - 1) for a in range(3)]
    return [(i * step[0], j * step[1], k * step[2])
            for i in range(n) for j in range(n) for k in range(n)]


def selftest():
    """Both outcomes, and the accepting case is a fact about cars.

    A road vehicle's lowest point is where the tyre meets the road. So a
    correctly assembled vehicle bottoms out at y=0 and a mis-assembled one
    does not — which is what the old reader did on every model in the kit,
    reporting a floor of -30 because it read four wheels about the origin
    and never asked where they were bolted on.

    The rejecting case is the bug itself, reproduced: pool the same meshes
    without their placements and the floor drops to -30 again.
    """
    fails = []

    # THE MEASURED VALUE PRINTS ON THE PASS AS WELL AS THE FAIL. The first
    # version showed `got` only when red, so every green line read "ok" with
    # no number under it — "the car kit is on disk" is a different claim over
    # 24 models and over 1, and the line could not tell them apart (rule 3b).
    def check(ok, what, got=""):
        print(("  ok   " if ok else "  FAIL ") + what + (" — " + got if got else ""))
        if not ok:
            fails.append(what)

    vehicles = [n for n in sorted(os.listdir(CAR_KIT))
                if n.endswith(".fbx")
                and not n.startswith(("wheel-", "debris-", "cone", "box"))]
    check(len(vehicles) >= 20, "the car kit is on disk to measure against",
          "%d models walked" % len(vehicles))

    # ONE PARSE PER MODEL, and every number below comes out of it — the floor,
    # the vertex count and the size are therefore all from the SAME read of the
    # same file. The live reading at the bottom used to re-parse all 25 models
    # for its counts, which is a second implementation of this walk and two
    # moments printed as one.
    floors, unplaced, rotated, live = [], [], [], []
    for n in vehicles:
        root, _ = _bp.parse_fbx(os.path.join(CAR_KIT, n), max_array=VERT_CAP)
        parts = assemble(root)
        if not parts:
            unplaced.append(n)
            continue
        if any("ROTATED" in p[0] for p in parts):
            rotated.append(n)
        floors.append((n[:-4], min(p[2][1] for p in parts)))
        live.append((n[:-4], sum(v for _nm, v, _lo, _hi in parts),
                     tuple(max(p[3][a] for p in parts) - min(p[2][a] for p in parts)
                           for a in range(3))))

    check(not unplaced, "every vehicle yields placed geometry",
          "%d of %d unplaced: %s" % (len(unplaced), len(vehicles), _capped(unplaced)))
    # Stated rather than assumed: `_translation` ignores rotation and
    # scaling, so the run has to confirm none is present to ignore.
    check(not rotated, "and none of them uses a rotation or a scale",
          "%d of %d rotated or scaled: %s"
          % (len(rotated), len(vehicles), _capped(rotated)))
    worst = max((abs(y), nm) for nm, y in floors) if floors else (0, "")
    # THE SERIES ITSELF, above any summary of it — a floor per vehicle, so a
    # reader can see a regime change (one kit re-exported) that no aggregate
    # can. The cap is `capsay`'s and counts the whole list, not the slice.
    print("  .. floors, %d measured: %s"
          % (len(floors),
             _cap(["%s=%.0f" % (nm, y) for nm, y in floors],
                  keep=8, width=40, sep=" ", tail=NOTHING_MEASURED)))
    # WORST OF A SET OF PER-VEHICLE MINIMA, not a median and not a sample:
    # "is ANY vehicle buried" is never a median question. The denominator is
    # on the line because 0 buried out of 24 and 0 out of 0 are the same
    # number and opposite facts.
    check(worst[0] < 0.01,
          "ACCEPTING CASE — every vehicle's wheels touch the road (y=0)",
          ("nothing measured" if not floors else
           "worst of %d is %s, %.2f off the road" % (len(floors), worst[1], worst[0])))

    # REJECTING CASE — A SYNTHETIC CAR, BUILT BY THIS FILE, NO ASSET ON DISK.
    #
    # The version this replaces re-parsed `car-kit/police.fbx` and asserted
    # that a real shipped model STILL REPRODUCES THE BUG. Re-export police
    # with its parts pre-placed and this selftest goes red for the asset
    # having been FIXED — `ref-bench` was pinned to `district_downtown` the
    # same way and went red for the camera improving. Nobody can fix
    # `_SYNTH_PARTS`, which is the whole property a rejecting fixture needs.
    #
    # A LADDER OF TWO RUNGS OFF ONE TREE, one contributor toggled: the same
    # five meshes read WITH their placements and WITHOUT them, in the same
    # run, from the same vantage. The difference between the rungs is the
    # reading — 0.0 against -30.0 — and neither rung alone can say anything,
    # because a floor of 0 proves nothing unless the unplaced read differs.
    synth = synthetic_car()
    placed = assemble(synth)
    pooled = min((min(d[1::3])
                  for g in synth.find("Objects").find_all("Geometry")
                  for d in [next((p for p in g.find("Vertices").props
                                  if isinstance(p, tuple)), None)] if d),
                 default=float("inf"))
    synth_floor = min(p[2][1] for p in placed) if placed else float("inf")
    check(abs(synth_floor - SYNTH_FLOOR) < 1e-6,
          "SYNTHETIC LADDER, rung 1 — placed, the fixture's tyres touch the road",
          "%d parts, floor %.1f, wanted %.1f" % (len(placed), synth_floor, SYNTH_FLOOR))
    check(abs(pooled - SYNTH_POOLED) < 1e-6,
          "SYNTHETIC LADDER, rung 2 — REJECTING: pooled unplaced, it buries the car",
          "pooled floor %.1f, wanted %.1f — the number the table used to print"
          % (pooled, SYNTH_POOLED))
    # AND THE RUNGS MUST STAND APART, WHICH NEITHER OF THEM CAN SAY ALONE.
    # Both expectations above are DERIVED from `_SYNTH_PARTS`, so each rung
    # on its own is close to a tautology: edit the fixture and the wanted
    # value moves with it. Caught while break-testing this very check — a
    # fixture "improved" to hold pre-placed parts passed both rungs and had
    # stopped reproducing the bug entirely, which is the ref-bench fault
    # wearing a fixture's clothes. The separation is the load-bearing
    # reading, printed as one paired entry rather than two keys whose
    # relationship a reader has to remember.
    check(pooled < synth_floor - 1.0,
          "SYNTHETIC LADDER — and the two rungs stand apart, so the fixture "
          "still reproduces the bug",
          "pooled/placed %.1f/%.1f, separation %.1f (needs > 1.0)"
          % (pooled, synth_floor, synth_floor - pooled))

    # -- THE VEHICLES THE GAME ACTUALLY DRESSES ------------------------
    #
    # `TrafficHost` scales a kit mesh to the kind's box on every axis, which
    # is what stopped a rendered lorry being 3.97m wide on a road that gives
    # it 3.00m. That means the mesh is DISTORTED, deliberately, and the
    # amount is worth a bound: this kit is stylised-chunky and ours is meant
    # to be plain, so some squash is the point and a lot of it is a model
    # that should not have been chosen.
    #
    # Both tables are READ FROM THE CODE, not copied. A second copy of the
    # vehicle dimensions in Python is the one-idea-two-implementations shape
    # this project keeps paying for, and the parse failing is a FAILING check
    # rather than an empty pass — the count of what was read is asserted
    # first (rule 3b).
    kinds, models = read_kind_table(), read_kit_map()
    check(len(kinds) >= 6, "the kind table parses out of Core/Traffic.cs",
          "%d kinds read" % len(kinds))
    check(len(models) >= 4, "and the kit mapping out of Game/TrafficHost.cs",
          "%d kinds mapped" % len(models))

    squash, unmeasurable = [], []
    keypaths = kit_key_paths()
    for kid, (L, W, H) in sorted(kinds.items()):
        model = models.get(kid)
        if not model:
            continue
        path = keypaths.get(model)
        if path is None:
            check(False, "kit model for %s exists" % kid, model)
            continue
        if not path.lower().endswith(".fbx"):
            # The FBX reader is the only parser here; the game loads OBJ
            # and GLB through Unity's importers, which this tool does not
            # have. Noted rather than failed — and noted VISIBLY, because
            # a skip nobody is told about reads as a measurement (rule 3b).
            print("  .. %s: first candidate %s ships as %s — not measurable here"
                  % (kid, model, os.path.splitext(path)[1]))
            unmeasurable.append("%s%s" % (kid, os.path.splitext(path)[1]))
            continue
        parts = assemble(_bp.parse_fbx(path, max_array=VERT_CAP)[0])
        # The game drops the push bar before it measures, so this must too.
        parts = [p for p in parts if not p[0].startswith("grill")]
        # FAIL READABLE (found by break-testing this file, 26 Aug). With the
        # array cap put back to its default — the historical bug — this loop
        # raised `ValueError: max() arg is an empty sequence` and the run ended
        # in a stack trace, so the CAP LADDER BELOW NEVER RAN AT ALL. A guard
        # that cannot be reached by the case it was written for is `lint-shadow`'s
        # selftest falling through to the live sweep and exiting 0.
        if not parts:
            check(False, "kit model for %s yields geometry to measure" % kid,
                  "%s parsed to 0 part(s) — the array cap, or a moved file" % model)
            continue
        mw = max(p[3][0] for p in parts) - min(p[2][0] for p in parts)
        mh = max(p[3][1] for p in parts) - min(p[2][1] for p in parts)
        md = max(p[3][2] for p in parts) - min(p[2][2] for p in parts)
        sL, sW, sH = L / md, W / mw, H / mh
        squash.append((kid, model, sW / sL, sH / sL))
    print("  .. squash (1.00 keeps the kit's own proportions): "
          + " ".join("%s=%.2f/%.2f" % (k, w, h) for k, _m, w, h in squash))
    # MEASURED, NOT INVENTED (rule 2). Today's series runs 0.60..0.78 on
    # width and 0.67..0.87 on height, the lorry being the worst on both
    # counts because the kit's is nearly square in plan. 0.50 sits below all
    # of it with room, and would catch a kind pointed at a model of the
    # wrong shape entirely — a bus dressed as a van, say. Every hit on
    # today's kit is a false positive by definition, which is what makes
    # this bound trustworthy without a fixture.
    worst = min([(min(w, h), k) for k, _m, w, h in squash] or [(1.0, "")])
    # THE PASS CARRIES ITS DENOMINATOR AND ITS SKIP CLAUSE. "0 kinds squashed
    # past half" over 5 measured kinds and over 0 is the same sentence and the
    # opposite fact, and a kind that shipped as OBJ was examined by nothing —
    # so the count of what was SKIPPED prints on the same line as the verdict
    # rather than only in the scroll above it (`lint-static`'s 560-vs-29).
    check(worst[0] >= 0.50,
          "no kit model is squashed past half to fit its kind",
          ("%s — %d kind(s) mapped, %d not measurable here: %s"
           % (NOTHING_MEASURED, len(models), len(unmeasurable),
              _cap(unmeasurable, keep=4, width=30, sep=", ", tail="none"))
           if not squash else
           "worst of %d kinds is %s at %.2f (%d not measurable here: %s)"
           % (len(squash), worst[1], worst[0], len(unmeasurable),
              _cap(unmeasurable, keep=4, width=30, sep=", ", tail="none"))))

    # -- THE ARRAY CAP, ON A FILE THIS FILE WROTE ----------------------
    #
    # THE PIN THIS REPLACES, kept in words because it is the whole lesson:
    #
    #     total, size = geometry(CAR_KIT/"police.fbx")
    #     check(total > 1000, "the vertex cap is lifted ...")
    #     check(100 < size[2] < 400, "and it has a size")
    #
    # An ACCEPTING fixture asserting the VALUES of a tracked asset — 1430
    # verts and 310 units deep, with 90 units of headroom on a bound whose
    # failure mode is a factor of 100. Re-export police at a different FBX
    # unit scale, the commonest thing that happens on a kit swap, and
    # `verify.py:489` returns False and blocks every commit in the project
    # while saying the READER is broken. `ref-bench` did precisely that,
    # pinned to a committed still, the hour the district cameras were
    # deliberately re-aimed. And `police.fbx` had ALREADY been taken out of
    # this file as a REJECTING fixture (see `synthetic_car`) — this was a
    # second site using the same asset for the opposite job, and the first
    # repair grepped for the pattern rather than for the asset's name.
    #
    # A LADDER OF TWO RUNGS OVER ONE FILE, one contributor toggled — the cap
    # — read in the same run from the same vantage. Neither rung means
    # anything alone: inflating 216 vertices proves nothing unless the same
    # bytes at the default cap come back empty, which is the exact symptom
    # this file shipped with for weeks ("no vertex data" on eleven of twelve
    # models, read as a fact about the files).
    with tempfile.TemporaryDirectory() as td:          # cleanup registered
        fx = os.path.join(td, "cap-fixture.fbx")
        verts = cap_fixture_verts()
        nbytes = write_synthetic_fbx(fx, verts)
        check(len(verts) * 3 > _bp.SMALL_ARRAY,
              "the fixture is denser than the DEFAULT cap, so the rungs can differ",
              "%d doubles against a %d-element default"
              % (len(verts) * 3, _bp.SMALL_ARRAY))
        lifted_total, lifted_size = geometry(fx)
        parts_default = assemble(_bp.parse_fbx(fx)[0])
        default_total = sum(n for _n, n, _lo, _hi in parts_default)
        check(lifted_total == CAP_VERTS
              and lifted_size is not None
              and all(abs(lifted_size[a] - _CAP_SIZE[a]) < 1e-6 for a in range(3)),
              "CAP LADDER, rung 1 — ACCEPTING: cap lifted, the fixture reads whole",
              "%d verts (wanted %d), size %s (wanted %s), %d bytes written"
              % (lifted_total, CAP_VERTS,
                 "/".join("%.1f" % v for v in (lifted_size or (0, 0, 0))),
                 "/".join("%.1f" % v for v in _CAP_SIZE), nbytes))
        check(default_total == 0,
              "CAP LADDER, rung 2 — REJECTING: at the default cap the same "
              "bytes read as nothing",
              "%d verts, %d part(s) — the `no vertex data` this file shipped"
              % (default_total, len(parts_default)))
        # AND THE RUNGS MUST STAND APART. Both expectations above are derived
        # from `cap_fixture_verts`, so each alone is close to a tautology —
        # the same trap the synthetic car's separation check exists for.
        check(lifted_total > default_total,
              "CAP LADDER — and the two rungs stand apart, so the cap is what "
              "made the difference",
              "lifted/default %d/%d verts" % (lifted_total, default_total))

    # THE LIVE KIT, AS A READING AND NOT AS A BOUND. This is the number the
    # pin above used to assert; it is worth printing and it is not worth
    # blocking a commit on, because every way it can move is a kit changing
    # rather than the reader breaking. The reader's own guard is the ladder.
    counts = sorted(t for _n, t, _s in live)
    print("  .. live kit reading, NOT a bound — %d model(s) read whole, verts "
          "%s..%s (median %s); %s"
          % (len(live),
             counts[0] if counts else NOTHING_MEASURED,
             counts[-1] if counts else NOTHING_MEASURED,
             counts[len(counts) // 2] if counts else NOTHING_MEASURED,
             _cap(["%s=%dv/%s" % (nm, t,
                                  "/".join("%.0f" % v for v in sz) if sz else "nosize")
                   for nm, t, sz in live],
                  keep=4, width=40, sep=" ", tail=NOTHING_MEASURED)))

    # THE FOOTER CARRIES THE DENOMINATOR AND NAMES THE SYNTHETIC INPUT
    # SEPARATELY, so nobody later reads the rejecting rung as coverage of a
    # real model: 1 of these inputs is one this file wrote.
    # THE DENOMINATOR NAMES THE SYNTHETIC INPUTS SEPARATELY, so nobody later
    # reads a rejecting rung as coverage of a real model: 2 of these inputs
    # are ones this file wrote, and one of them is bytes on disk.
    tally = ("%d kit vehicles measured, %d kinds squash-checked, "
             "2 synthetic inputs (1 car tree + 1 FBX file, both built here, "
             "no asset)"
             % (len(floors), len(squash)))
    print("\nprop-dimensions selftest %s — %s"
          % ("ok" if not fails else "%d problem(s)" % len(fails), tally))
    return 1 if fails else 0


def main():
    root = os.path.normpath(PROPS)
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest()
    parts_view = "--parts" in sys.argv[1:]
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    want = argv[0] if argv else "building"

    if parts_view:
        for kit in sorted(os.listdir(root)):
            kdir = os.path.join(root, kit)
            if not os.path.isdir(kdir):
                continue
            for name in sorted(os.listdir(kdir)):
                if not name.lower().endswith(".fbx") or (want and want not in name):
                    continue
                tree, _ = _bp.parse_fbx(os.path.join(kdir, name), max_array=VERT_CAP)
                print("\n%s / %s" % (kit, name[:-4]))
                for label, n, lo, hi in assemble(tree):
                    print("  %-28s n=%5d  x %7.1f..%-7.1f y %7.1f..%-7.1f z %7.1f..%-7.1f"
                          % (label[:28], n, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
        return 0

    rows = []
    for kit in sorted(os.listdir(root)):
        kdir = os.path.join(root, kit)
        if not os.path.isdir(kdir):
            continue
        for name in sorted(os.listdir(kdir)):
            if not name.lower().endswith(".fbx"):
                continue
            if want and want not in name:
                continue
            try:
                n, size = geometry(os.path.join(kdir, name))
            except Exception as exc:                      # noqa: BLE001
                print("  %-34s PARSE FAILED: %s" % (name[:-4], exc))
                continue
            rows.append((kit, name[:-4], n, size))

    if not rows:
        print("no models matching %r under %s" % (want, root))
        return 1

    print("PROP MODELS matching %r — %d found" % (want, len(rows)))
    print()
    print("  %-22s %-22s %8s %8s %8s %8s"
          % ("kit", "model", "verts", "width", "height", "depth"))
    for kit, name, n, size in rows:
        if size is None:
            print("  %-22s %-22s %8d %s" % (kit, name, n, "no vertex data"))
            continue
        print("  %-22s %-22s %8d %8.2f %8.2f %8.2f"
              % (kit, name, n, size[0], size[1], size[2]))
    print()
    print("  READ THE RATIOS, NOT THE ABSOLUTES. These are the FBX's own")
    print("  units and they are NOT metres: the kit's `sedan` measures")
    print("  150 x 135 x 255, and a sedan is 4.2m long. `TrafficHost`")
    print("  already rescales a kit mesh to the kind's real length on")
    print("  instantiate, so absolute size is handled and PROPORTION is")
    print("  what decides whether a model can be used.")
    print()
    print("  For comparison: our terrace parcels run about 6x12m — a 1:2")
    print("  plan, narrow frontage and deep — and a dozen skinned bodies")
    print("  is ~280k vertices, the order this scene is already built at.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
