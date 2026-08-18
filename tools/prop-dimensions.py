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
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROPS = os.path.join(HERE, "..", "ledger", "Assets", "Props")

_spec = importlib.util.spec_from_file_location(
    "body_proportions", os.path.join(HERE, "body-proportions.py"))
_bp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bp)


def geometry(path):
    """(vertex count, (dx, dy, dz)) over every Geometry node in the file.

    Vertex ARRAYS are large, so `body-proportions` skips them by default.
    Here they are exactly what is wanted, so the cap is lifted for the
    duration — these are prop models, not a city.
    """
    keep = _bp.SMALL_ARRAY
    _bp.SMALL_ARRAY = 10_000_000
    try:
        root, _version = _bp.parse_fbx(path)
    finally:
        _bp.SMALL_ARRAY = keep

    objects = root.find("Objects")
    if objects is None:
        return 0, None

    total = 0
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for geom in objects.find_all("Geometry"):
        verts = geom.find("Vertices")
        if verts is None:
            continue
        data = next((p for p in verts.props if isinstance(p, tuple)), None)
        if not data:
            continue
        total += len(data) // 3
        for i in range(0, len(data) - 2, 3):
            for a in range(3):
                v = data[i + a]
                if v < lo[a]:
                    lo[a] = v
                if v > hi[a]:
                    hi[a] = v
    if total == 0 or lo[0] == float("inf"):
        return total, None
    return total, tuple(hi[a] - lo[a] for a in range(3))


def main():
    root = os.path.normpath(PROPS)
    want = sys.argv[1] if len(sys.argv) > 1 else "building"

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
    print("  150 x 145 x 255, and a sedan is 4.2m long. `TrafficHost`")
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
