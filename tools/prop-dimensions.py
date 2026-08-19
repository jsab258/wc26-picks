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
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROPS = os.path.join(HERE, "..", "ledger", "Assets", "Props")

_spec = importlib.util.spec_from_file_location(
    "body_proportions", os.path.join(HERE, "body-proportions.py"))
_bp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bp)


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

    def check(ok, what, got=""):
        print(("  ok   " if ok else "  FAIL ") + what + ("" if ok else " — " + got))
        if not ok:
            fails.append(what)

    vehicles = [n for n in sorted(os.listdir(CAR_KIT))
                if n.endswith(".fbx")
                and not n.startswith(("wheel-", "debris-", "cone", "box"))]
    check(len(vehicles) >= 20, "the car kit is on disk to measure against",
          "%d models" % len(vehicles))

    floors, unplaced, rotated = [], [], []
    for n in vehicles:
        root, _ = _bp.parse_fbx(os.path.join(CAR_KIT, n), max_array=VERT_CAP)
        parts = assemble(root)
        if not parts:
            unplaced.append(n)
            continue
        if any("ROTATED" in p[0] for p in parts):
            rotated.append(n)
        floors.append((n[:-4], min(p[2][1] for p in parts)))

    check(not unplaced, "every vehicle yields placed geometry",
          ", ".join(unplaced[:4]))
    # Stated rather than assumed: `_translation` ignores rotation and
    # scaling, so the run has to confirm none is present to ignore.
    check(not rotated, "and none of them uses a rotation or a scale",
          ", ".join(rotated[:4]))
    worst = max((abs(y), nm) for nm, y in floors) if floors else (0, "")
    print("  .. floors: " + " ".join("%s=%.0f" % (nm, y) for nm, y in floors[:8])
          + (" ..." if len(floors) > 8 else ""))
    check(worst[0] < 0.01,
          "ACCEPTING CASE — every vehicle's wheels touch the road (y=0)",
          "%s bottoms out at %.1f" % (worst[1], -worst[0]))

    # REJECTING CASE — the old reader, run again on the same file.
    root, _ = _bp.parse_fbx(os.path.join(CAR_KIT, "police.fbx"), max_array=VERT_CAP)
    pooled = float("inf")
    for geom in root.find("Objects").find_all("Geometry"):
        v = geom.find("Vertices")
        d = None if v is None else next((p for p in v.props if isinstance(p, tuple)), None)
        if d:
            pooled = min(pooled, min(d[1::3]))
    check(pooled < -1,
          "REJECTING CASE — pooling the parts unplaced buries the car",
          "pooled floor %.1f, which is what the table used to print" % pooled)

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

    squash = []
    for kid, (L, W, H) in sorted(kinds.items()):
        model = models.get(kid)
        if not model:
            continue
        path = os.path.join(CAR_KIT, model.replace("_", "-") + ".fbx")
        if not os.path.exists(path):
            check(False, "kit model for %s exists" % kid, model)
            continue
        parts = assemble(_bp.parse_fbx(path, max_array=VERT_CAP)[0])
        # The game drops the push bar before it measures, so this must too.
        parts = [p for p in parts if not p[0].startswith("grill")]
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
    check(worst[0] >= 0.50,
          "no kit model is squashed past half to fit its kind",
          "%s at %.2f" % (worst[1], worst[0]))

    # And the cap, because this file's whole history is that it was reading
    # nothing and saying so quietly.
    total, size = geometry(os.path.join(CAR_KIT, "police.fbx"))
    check(total > 1000, "the vertex cap is lifted, so a model reads whole",
          "%d verts" % total)
    check(size is not None and 100 < size[2] < 400, "and it has a size",
          str(size))

    print("\n%s" % ("prop-dimensions selftest ok" if not fails
                    else "%d problem(s)" % len(fails)))
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
