#!/usr/bin/env python3
"""The atlas-01 art commission's five authored views of Mickey's, rendered.

    blender --background --factory-startup --python tools/art-recipes/mickeys-blockout.py \
        -- --out DIR --root <workspace> --commission atlas-01

WHAT THIS IS AND WHOSE DECISIONS IT CARRIES. Every number below comes out of
two files on the art branch, and this recipe authors none of them:

    production/art/<commission>/data/mickeys.json      the authored layout
    production/art/<commission>/scripts/pub_geometry.py  the geometry compiler

The five cameras, their positions, targets, lenses and which two are cutaways
are READ from that JSON, in the order the JSON lists them. Which five views
Jafar sees is a taste decision the art commission already made. If the file
ever lists four or six, this file renders four or six and prints the count
with its denominator; it never pads or trims to five.

WHY THIS FILE EXISTS WHEN THE COMMISSION ALREADY HAS A RECIPE.
`production/art/atlas-01/recipes/mickeys_blockout.py` cannot be run by the
studio lane, and the five reasons were each measured rather than inferred:

  1. It renders NOTHING unless `--render` is passed (its line 106). The lane
     passes only `--out`, so a run today saves a .blend, writes receipt.json,
     exits 0 and the workflow counts zero new PNGs. That is the EMPTY SUCCESS
     the lane exists to prevent, arriving by default.
  2. Its ROOT is `parents[1]` of its own path (line 12). The lane resolves
     recipes from `tools/art-recipes/`, where that ROOT becomes `tools/` and
     its own guard at line 23 then REFUSES the lane's output directory.
  3. It runs at import time: no `main`, no entry guard. `run-recipe.py`'s
     `--plan` and selftest cannot reach it without rendering.
  4. `bpy.context.window.scene = scene` (line 27). In `--background` there is
     no window, so `bpy.context.window` is None and that line raises
     AttributeError. PROVENANCE.md on the art branch marks the recipe "Syntax
     checked only", which reads literally: it has never been inside Blender.
  5. It refuses a second run into the same directory (line 25) and reports a
     JSON receipt rather than a count of frames written.

THE AUTHORED NUMBERS ARE UNTOUCHED. Only the construction method changed:
geometry is built through `bpy.data` rather than `bpy.ops`, which is what
removes faults 4 and the operator-context class behind it. Every dimension,
colour, lens, light energy and resolution below is the commission's, and each
is commented with the line of the original it came from.

WHY `--root` IS NOT OPTIONAL HERE. At render time this file lives in a SECOND
checkout (`<workspace>/studio/tools/art-recipes/`) while the commission data
lives in the FIRST (`<workspace>/production/art/...`). A root derived from
`__file__` would point at the studio checkout and find no data. That is fault 2
above, one directory along, so the lane passes `--root` explicitly and every
refusal below prints the root it used.

WHAT IS COVERED AND WHAT SHIPS UNRUN. Blender is not installed in the
container this was written in (`run-recipe.py --selftest` prints
`note/blender-in-this-container NOT-INSTALLED/render-path-is-uncovered`), so
every line below that touches `bpy` ships UNRUN and the first real run on the
Windows runner is the first test of it. What IS covered, and deliberately
carries all the arithmetic and every printed string: the import without bpy,
`main(argv)`, `--dry-run`, `--root`, the refusal when the commission data is
absent, the argument parsing, the camera plan, the output path composition and
the verdict text. `--plan` prints the whole plan with no Blender anywhere.
"""
import hashlib
import json
import math
import os
import sys
import time

try:
    import bpy
    import mathutils
except ImportError:  # not inside Blender: the pure layer below still imports
    bpy = None
    mathutils = None

RECIPE_STEM = os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]
#: Only a FALLBACK, and the docstring says why it cannot be trusted at render
#: time. The lane passes --root; this keeps `--plan` usable from the repo.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_COMMISSION = "atlas-01"
DATA_REL = "production/art/%s/data/mickeys.json"
GEOM_REL = "production/art/%s/scripts/pub_geometry.py"

#: 1600x1100 at 100 percent, PNG. The commission's own choice, from line 30 of
#: production/art/atlas-01/recipes/mickeys_blockout.py. Overridable with --res
#: so a fast check can be asked for, and printed either way.
AUTHORED_RES = (1600, 1100)

#: The art branch's engine, named in render-request.json ("An already installed
#: Blender 4.2+ with BLENDER_EEVEE_NEXT"). The identifier exists only in 4.2+,
#: and the lane probes 4.2 then 4.1, so the choice is resolved against the enum
#: THIS Blender offers rather than assigned and hoped for. CYCLES is last
#: because it is the one engine certain to work with no GL context at all.
ENGINE_CANDIDATES = ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES")

#: Cycles only, and it is a TIME bound rather than a quality claim: Cycles'
#: own default is 4096 samples, which at five frames would outlast the job's
#: cap. Nothing is set for EEVEE unless --samples is given, so EEVEE renders at
#: whatever this Blender's default is and the run prints what it read back.
CYCLES_FALLBACK_SAMPLES = 64

#: The authored palette, from lines 43 to 47 of the commission's recipe, in the
#: same order. These are assigned to Base Color RAW, exactly as the original
#: does: the commission chose them as the values that recipe passed to a
#: Principled BSDF, so converting them here would be a look change wearing the
#: clothes of a correctness fix.
MATERIALS = (
    ("brick", (.38, .20, .14)),
    ("plaster", (.68, .64, .51)),
    ("slate", (.12, .17, .18)),
    ("maroon", (.22, .045, .06)),
    ("wood", (.31, .17, .08)),
    ("glass_proxy", (.26, .46, .48)),
    ("floor", (.33, .27, .19)),
    ("yard", (.45, .43, .35)),
    ("metal", (.19, .24, .23)),
    ("cloth", (.26, .10, .10)),
    ("paper", (.78, .73, .56)),
)
AUTHORED_ROUGHNESS = .76               # original line 41
AUTHORED_SKY_RGBA = (.65, .72, .76, 1)  # original line 34
AUTHORED_SKY_STRENGTH = .6              # original line 35
#: Both area lights, from lines 101 and 102. Tuples read: location, energy,
#: size, shape, colour. `bar_practical` sets no shape in the original, so it
#: keeps Blender's default and that is said here rather than guessed at.
AUTHORED_LIGHTS = (
    ("A01_soft_sky", (0, -2, 15), 2400, 18, "DISK", None),
    ("A01_bar_practical", (3, 4, 3.15), 120, 3, None, (1, .74, .43)),
)
AUTHORED_SCENE_NAME = "ATLAS01_Mickeys_Proposal"   # original line 26
AUTHORED_WORLD_NAME = "ATLAS01_Overcast"           # original line 32
BASE_COLLECTION = "ATLAS01_Mickeys"                # original line 36
UPPER_COLLECTION = "ATLAS01_Upper_Cutaway"         # original line 37

#: Blender's factory camera sensor width in mm. Used ONLY to turn the authored
#: lens into a printed field of view in the pure layer; the camera itself is
#: given the lens and its sensor is read back and printed, never set, because
#: changing sensor fit would reframe every authored shot.
SENSOR_WIDTH_MM = 36.0

#: A camera id becomes part of a filename and part of a key=value token, so the
#: two characters that would break either are refused by name rather than
#: quietly replaced.
ID_BAD = set(' \t/\\:*?"<>|=')


# ---------------------------------------------------------------------------
# PURE. No bpy below until the marked section. Everything here runs in the
# container, under --dry-run, and under run-recipe.py --plan.
# ---------------------------------------------------------------------------


def commission_paths(root, commission):
    """The two authored files this recipe reads, absolute, in one place."""
    return (os.path.join(root, DATA_REL % commission),
            os.path.join(root, GEOM_REL % commission))


def sha256_of(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def import_by_path(path, name):
    """Import the commission's geometry compiler BY PATH, never by sys.path.

    The original inserts the commission's `scripts/` on sys.path and imports
    `pub_geometry` by name. From `tools/art-recipes/` that would resolve
    against whatever else is on the path first, and a second commission's file
    of the same name would shadow this one. A path import cannot be shadowed.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        return None, "cannot-load/" + os.path.basename(path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except BaseException as exc:  # SystemExit included, on purpose
        return None, "geometry-module-raised-on-import/" + type(exc).__name__
    for needed in ("resolved", "geometry", "digest"):
        if not hasattr(module, needed):
            return None, "geometry-module-has-no/" + needed
    return module, ""


def load_commission(root, commission):
    """(plan-inputs, error). The refusal NAMES the file that is not there.

    On the studio branch neither file exists, so this is the path a dry run in
    the container takes, and it is the only part of this recipe that a machine
    without Blender can watch end to end.
    """
    data_path, geom_path = commission_paths(root, commission)
    missing = [p for p in (data_path, geom_path) if not os.path.exists(p)]
    if missing:
        # ONE TOKEN, NO SPACE IN IT. Every reader here splits on whitespace, so
        # the count of what was found travels inside the value rather than
        # beside it where a `reason=` would be truncated at the space.
        return None, ("no-commission-file/found%dof2-required/%s"
                      % (2 - len(missing), missing[0].replace(" ", "~")))
    geom_module, err = import_by_path(geom_path, "pub_geometry_" + commission)
    if err:
        return None, err
    try:
        with open(data_path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, ValueError) as exc:
        return None, "unreadable-commission-json/" + type(exc).__name__
    try:
        data = geom_module.resolved(raw)
        geom = geom_module.geometry(raw)
        digest = geom_module.digest(raw)
    except Exception as exc:  # the compiler raises by design on bad authoring
        return None, ("geometry-compiler-refused/%s/%s"
                      % (type(exc).__name__, str(exc)[:60].replace(" ", "~")))
    return {"data": data, "geom": geom, "digest": digest,
            "data_path": data_path, "geom_path": geom_path,
            "data_sha256": sha256_of(data_path),
            "geom_sha256": sha256_of(geom_path)}, ""


def authored_bounds(geom):
    """(lo, hi, rotated) over every authored box and triangle, axis aligned.

    ROTATED BOXES ARE COUNTED AND SAID. Two roof planes carry a rotation about
    X, and their axis-aligned extent is read before that rotation, so this
    bound is approximate for exactly those and the count prints beside it
    rather than being folded in silently.
    """
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    rotated = 0
    for b in geom["boxes"]:
        u, v, w, d = b["box"]
        if b.get("rotation_x"):
            rotated += 1
        for point in ((u, v, b["base"]), (u + w, v + d, b["base"] + b["height"])):
            for k in range(3):
                lo[k] = min(lo[k], point[k])
                hi[k] = max(hi[k], point[k])
    for tri in geom["triangles"]:
        for vert in tri["vertices"]:
            for k in range(3):
                lo[k] = min(lo[k], vert[k])
                hi[k] = max(hi[k], vert[k])
    if lo[0] == float("inf"):
        return None, None, rotated
    return lo, hi, rotated


def fov_degrees(lens_mm, res):
    """(horizontal, vertical) field of view for Blender's AUTO sensor fit.

    AUTO fits the sensor width to the LONGER side of the frame. 1600x1100 is
    landscape, so the 36 mm sensor is the horizontal field and the vertical
    follows from the aspect. The camera below is given the lens and nothing
    else, so these two numbers describe the authored framing rather than
    setting it.
    """
    half_h = math.degrees(math.atan((SENSOR_WIDTH_MM / 2.0) / float(lens_mm)))
    aspect = res[1] / float(res[0])
    half_v = math.degrees(math.atan(math.tan(math.radians(half_h)) * aspect))
    return half_h * 2.0, half_v * 2.0


def _sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def _norm(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def angle_between_deg(a, b):
    na, nb = _norm(a), _norm(b)
    if na <= 0 or nb <= 0:
        return 180.0
    dot = (a[0] * b[0] + a[1] * b[1] + a[2] * b[2]) / (na * nb)
    return math.degrees(math.acos(max(-1.0, min(1.0, dot))))


def inside(point, lo, hi, pad=0.0):
    return all(lo[k] - pad <= point[k] <= hi[k] + pad for k in range(3))


def camera_plan(data, res, stem):
    """(cameras, error). The authored cameras, in the authored order, measured.

    WHAT IS READ AND WHAT IS DERIVED. Read: id, position, target, lens,
    cutaway. Derived and printed only: distance, bearing, the two fields of
    view, and two coverage counts.

    THE COVERAGE METRIC HAS TWO HALVES, which is the shape
    .claude/rules/instruments.md asks for: `distance_m` is the distance to the
    datum, and `targetInsideBounds` is whether the datum exists where the
    camera is pointed. A camera aimed confidently at nothing scores a perfect
    distance.

    AND IT IS ROLL INDEPENDENT ON PURPOSE. Whether a corner lands inside the
    rectangle of frame depends on the camera's roll, and the roll comes from
    Blender's `to_track_quat`, not from here. The overhead camera looks
    straight down, where that roll is Blender's arbitrary choice. So the
    counts reported are the two bounds that hold for ANY roll: a corner within
    the SHORTER half field is in frame whatever the roll, and a corner outside
    the diagonal half field is out of frame whatever the roll.

    WHICH DATUM, SAID IN THE KEY. The corner counts are against the WHOLE SITE,
    which includes the yard, the rear lane and the WC annex, so a low count is
    the normal reading for a close shot and not a fault. The second datum is
    the one authored point every exterior view of a pub should contain, the
    fascia lettering, and it is a single coordinate out of the same file rather
    than arithmetic repeated from the geometry compiler.
    """
    cams = data.get("cameras")
    if not isinstance(cams, list) or not cams:
        return None, "no-cameras-in-the-commission-json"
    total = len(cams)
    width = max(2, len(str(total)))
    out = []
    for index, spec in enumerate(cams):
        cam_id = str(spec.get("id", ""))
        if not cam_id or ID_BAD & set(cam_id):
            return None, ("camera-id-unusable-in-a-filename/%d-of-%d/%s"
                          % (index + 1, total, cam_id.replace(" ", "~") or "empty"))
        for key in ("position", "target", "lens"):
            if key not in spec:
                return None, "camera-%s-has-no/%s" % (cam_id, key)
        pos = [float(c) for c in spec["position"]]
        target = [float(c) for c in spec["target"]]
        lens = float(spec["lens"])
        if lens <= 0:
            return None, "camera-%s-lens-not-positive/%s" % (cam_id, lens)
        forward = _sub(target, pos)
        dist = _norm(forward)
        if dist <= 0:
            return None, "camera-%s-target-is-its-own-position" % cam_id
        fov_h, fov_v = fov_degrees(lens, res)
        out.append({
            "index": index,
            "id": cam_id,
            "png": "%s-%0*d-%s.png" % (stem, width, index + 1, cam_id),
            "pos": pos,
            "target": target,
            "lens_mm": lens,
            "cutaway": bool(spec.get("cutaway", False)),
            "forward": forward,
            "distance_m": dist,
            "fov_h_deg": fov_h,
            "fov_v_deg": fov_v,
            # Bearing and pitch are DESCRIPTIVE. The camera's actual rotation
            # comes from the authored vector through to_track_quat, and the
            # Blender layer measures the angle between where it ended up
            # pointing and this same vector, so a convention error here cannot
            # hide behind a plausible number.
            "bearing_deg": math.degrees(math.atan2(forward[1], forward[0])),
            "pitch_down_deg": math.degrees(
                math.atan2(-forward[2], math.hypot(forward[0], forward[1]))),
        })
    return out, ""


def camera_coverage(cams, lo, hi, fascia=None):
    """Fill in the two roll-independent in-frame counts, and the target check."""
    corners = []
    if lo is not None:
        corners = [[lo[0] if (m & 1) else hi[0],
                    lo[1] if (m & 2) else hi[1],
                    lo[2] if (m & 4) else hi[2]] for m in range(8)]
    for cam in cams:
        certain_half = min(cam["fov_h_deg"], cam["fov_v_deg"]) / 2.0
        diag_half = math.degrees(math.atan(math.hypot(
            math.tan(math.radians(cam["fov_h_deg"] / 2.0)),
            math.tan(math.radians(cam["fov_v_deg"] / 2.0)))))
        certain = at_best = 0
        worst = 0.0
        for corner in corners:
            off = angle_between_deg(cam["forward"], _sub(corner, cam["pos"]))
            worst = max(worst, off)
            if off <= certain_half:
                certain += 1
            if off <= diag_half:
                at_best += 1
        cam["corners"] = len(corners)
        cam["in_frame_certain"] = certain
        cam["in_frame_at_best"] = at_best
        cam["worst_corner_off_deg"] = worst
        cam["certain_half_deg"] = certain_half
        cam["diag_half_deg"] = diag_half
        cam["target_inside"] = (inside(cam["target"], lo, hi, 0.5)
                                if lo is not None else None)
        cam["pos_inside"] = (inside(cam["pos"], lo, hi, 0.0)
                             if lo is not None else None)
        if fascia is None:
            cam["fascia_off_deg"] = None
            cam["fascia_in_frame"] = None
        else:
            off = angle_between_deg(cam["forward"], _sub(fascia, cam["pos"]))
            cam["fascia_off_deg"] = off
            cam["fascia_in_frame"] = off <= certain_half
    return cams


def build_plan(root, opts):
    """Everything decided before a single Blender call. Pure, and printable."""
    loaded, err = load_commission(root, opts["commission"])
    if err:
        return None, err
    data, geom = loaded["data"], loaded["geom"]
    cams, err = camera_plan(data, opts["res"], RECIPE_STEM)
    if err:
        return None, err
    lo, hi, rotated = authored_bounds(geom)
    fascia = data.get("fascia_text", {}).get("position")
    fascia = [float(c) for c in fascia] if fascia else None
    camera_coverage(cams, lo, hi, fascia)
    upper = sum(1 for b in geom["boxes"] if b["floor"] == "upper")
    # MARKERS, COUNTED THE WAY THE ORIGINAL CREATES THEM, so the plan's count
    # and the scene's count are the same fact measured twice rather than two
    # different definitions. `information` holds one scalar (eye_height) among
    # the coordinate lists, and it is excluded here exactly as line 92 excludes
    # it, with both numbers printed.
    info_lists = sum(1 for v in data.get("information", {}).values()
                     if isinstance(v, list))
    info_keys = len(data.get("information", {}))
    path_points = sum(len(r) for r in data.get("paths", {}).values())
    markers = (2 * len(geom["doors"]) + len(data.get("upper_rooms", []))
               + info_lists + path_points)
    return {
        "loaded": loaded,
        "data": data,
        "geom": geom,
        "cams": cams,
        "bounds_lo": lo,
        "bounds_hi": hi,
        "rotated_boxes": rotated,
        "boxes": len(geom["boxes"]),
        "boxes_upper": upper,
        "triangles": len(geom["triangles"]),
        "doors": len(geom["doors"]),
        "markers": markers,
        "info_lists": info_lists,
        "info_keys": info_keys,
        "path_points": path_points,
        "rooms": len(data.get("upper_rooms", [])),
        "fascia": fascia,
        # TWO DENOMINATORS, BECAUSE TWO DIFFERENT THINGS BUILD THEM.
        # `objects_planned` is what the geometry pass builds and is the
        # denominator `objectsBuilt` is counted against; the cameras and the two
        # lights are added by their own passes, so they are counted separately
        # and only `scene_expected` covers the lot. One denominator over both
        # would read as seven objects missing on a perfect run.
        "objects_planned": (len(geom["boxes"]) + len(geom["triangles"])
                            + markers + 1),
        "scene_expected": (len(geom["boxes"]) + len(geom["triangles"])
                           + markers + 1 + len(cams) + len(AUTHORED_LIGHTS)),
    }, ""


def plan_lines(plan, opts):
    """PER SAMPLE ONLY. One line per authored camera, one per floor group.

    Whole-run numbers live on the done line, per instruments.md, and never
    under a key that also appears here.
    """
    lines = []
    total = len(plan["cams"])
    for cam in plan["cams"]:
        lines.append(
            "blockoutCam idx=%d/%d id=%s png=%s lens_mm=%.1f "
            "pos=%.3f/%.3f/%.3f target=%.3f/%.3f/%.3f distance_m=%.2f "
            "bearing_deg=%.2f pitchDown_deg=%.2f fovH_deg=%.2f fovV_deg=%.2f "
            "cutaway=%s camInsideSite=%s targetInsideSite=%s "
            "siteCornersInFrameAnyRoll=%d/%d siteCornersInFrameAtBest=%d/%d "
            "worstSiteCornerOff_deg=%.2f halfFieldShortThenDiag_deg=%.2f/%.2f "
            "fasciaInFrameAnyRoll=%s fasciaOff_deg=%s"
            % (cam["index"] + 1, total, cam["id"], cam["png"], cam["lens_mm"],
               cam["pos"][0], cam["pos"][1], cam["pos"][2],
               cam["target"][0], cam["target"][1], cam["target"][2],
               cam["distance_m"], cam["bearing_deg"], cam["pitch_down_deg"],
               cam["fov_h_deg"], cam["fov_v_deg"],
               "yes" if cam["cutaway"] else "no",
               _yn(cam["pos_inside"]), _yn(cam["target_inside"]),
               cam["in_frame_certain"], cam["corners"],
               cam["in_frame_at_best"], cam["corners"],
               cam["worst_corner_off_deg"], cam["certain_half_deg"],
               cam["diag_half_deg"],
               _yn(cam["fascia_in_frame"]),
               "%.2f" % cam["fascia_off_deg"]
               if cam["fascia_off_deg"] is not None else "nothing-measured"))
    for floor in ("ground", "upper"):
        boxes = [b for b in plan["geom"]["boxes"] if b["floor"] == floor]
        tris = [t for t in plan["geom"]["triangles"] if t["floor"] == floor]
        mats = sorted({b["material"] for b in boxes} | {t["material"] for t in tris})
        lines.append(
            "blockoutGroup floor=%s collection=%s boxes=%d/%d-authored "
            "triangles=%d/%d-authored hiddenInCutawayFrames=%s "
            "materials=%d/%d-palette=%s"
            % (floor,
               UPPER_COLLECTION if floor == "upper" else BASE_COLLECTION,
               len(boxes), plan["boxes"], len(tris), plan["triangles"],
               "yes" if floor == "upper" else "no",
               len(mats), len(MATERIALS), ",".join(mats) or "none/0-used"))
    return lines


def _yn(value):
    if value is None:
        return "nothing-measured"
    return "yes" if value else "no"


def done_line(plan, opts, built, frames, status, seconds):
    """THE WHOLE-RUN LINE, and it is built here so the tests read the string.

    PLANNED, BUILT AND WRITTEN ARE THREE FACTS under three keys.
    `objectsPlanned` is what the authored files describe; `objectsBuilt` is
    what Blender handed back, counted as it happened; `previewsWrote` counts
    files with a non-zero size on disk, because an operator that returns
    FINISHED having written nothing is this project's empty-success class.

    Every zero carries the count of what was examined, and no value contains a
    space: every reader in this project splits on whitespace.
    """
    total = len(plan["cams"])
    wrote = sum(1 for f in frames if f["bytes"] > 0)
    lo, hi = plan["bounds_lo"], plan["bounds_hi"]
    extent = ("%.2f/%.2f/%.2f" % (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
              if lo is not None else "nothing-measured")
    engines = sorted({f["engine"] for f in frames}) or ["not-reached"]
    smallest = min((f["bytes"] for f in frames if f["bytes"] > 0),
                   default="nothing-written")
    fascia_seen = sum(1 for c in plan["cams"] if c["fascia_in_frame"])
    aim = max((f["aim_error_deg"] for f in frames), default=None)
    # A NEVER-ATTEMPTED FRAME IS NOT A FAILED ONE. With no frames at all the
    # denominator is the camera count but the words have to say nothing was
    # tried, or a dry run reads as five renders that wrote nothing.
    wrote_token = ("%d/%d" % (wrote, total) if frames
                   else "0/%d-no-frame-attempted" % total)
    zero_token = ("%d/%d" % (len(frames) - wrote, total) if frames
                  else "0/%d-no-frame-attempted" % total)
    return (
        "%s done: status=%s commission=%s runSha=%s studioSha=%s "
        "dataSha256=%s geomSha256=%s geometryDigest=%s "
        "camerasAuthored=%d cutawayCameras=%d/%d "
        "previewsWrote=%s previewsZeroBytes=%s smallestPngBytes=%s "
        "boxesAuthored=%d boxesUpper=%d/%d rotatedBoxes=%d/%d "
        "triangles=%d doors=%d markersPlanned=%d "
        "infoMarkers=%d/%d-keys pathMarkers=%d rooms=%d "
        "objectsPlanned=%d objectsBuilt=%s objectsInScene=%s "
        "doorsParented=%s doorLeafDrift_mm=%s "
        "siteExtent_m=%s siteExtentIgnoresRotationOn=%d/%d-boxes "
        "camsWithFasciaInFrame=%d/%d worstAimError_deg=%s "
        "engineAsked=%s engineUsed=%s engineCandidatesOffered=%s "
        "samples=%s viewTransform=%s res=%dx%d blendBytes=%s "
        "outDir=%s root=%s elapsedSeconds=%.1f"
        % (RECIPE_STEM, status, opts["commission"],
           opts["run_sha"], opts["studio_sha"],
           plan["loaded"]["data_sha256"][:16], plan["loaded"]["geom_sha256"][:16],
           plan["loaded"]["digest"][:16],
           total, sum(1 for c in plan["cams"] if c["cutaway"]), total,
           wrote_token, zero_token, smallest,
           plan["boxes"], plan["boxes_upper"], plan["boxes"],
           plan["rotated_boxes"], plan["boxes"],
           plan["triangles"], plan["doors"], plan["markers"],
           plan["info_lists"], plan["info_keys"], plan["path_points"],
           plan["rooms"],
           plan["objects_planned"],
           "%d/%d-planned" % (built["objects"], plan["objects_planned"])
           if built else "0/%d-planned-nothing-built" % plan["objects_planned"],
           "%d/%d-expected" % (built["in_scene"], plan["scene_expected"])
           if built else "nothing-measured",
           "%d/%d-authored" % (built["doors_parented"], plan["doors"])
           if built else "0/%d-authored-nothing-built" % plan["doors"],
           "%.4f" % built["door_drift_mm"] if built else "nothing-measured",
           extent, plan["rotated_boxes"], plan["boxes"],
           fascia_seen, total,
           "%.4f" % aim if aim is not None else "nothing-measured",
           opts["engine"], ",".join(engines),
           built["engine_offered"] if built else "nothing-measured",
           built["samples"] if built else "nothing-measured",
           built["view_transform"] if built else "nothing-measured",
           opts["res"][0], opts["res"][1],
           built["blend_bytes"] if built else "nothing-written",
           (opts["out"] or "none/dry-run").replace(" ", "~"),
           opts["root"].replace(" ", "~"), seconds))


def receipt_dict(plan, opts, built, frames, status, seconds):
    """ONE dict, two serialisations, so the verdict and receipt cannot drift.

    The commission's render-request.json lists `receipt.json` among its
    expected outputs and asks for the Blender version and the input hashes in
    it. The verdict file the studio lane reads is FORMATTED FROM THIS DICT, so
    there is one source for both files rather than two writers of one fact.
    """
    return {
        "schema": "ledger.art-preview.receipt/1",
        "status": status,
        "recipe": RECIPE_STEM,
        "commission": opts["commission"],
        "run_sha": opts["run_sha"],
        "studio_sha": opts["studio_sha"],
        "blender_version": built["blender_version"] if built else "not-run",
        "engine_asked": opts["engine"],
        "engine_used": sorted({f["engine"] for f in frames}) or ["not-reached"],
        "engine_candidates_offered": built["engine_offered"] if built else "not-run",
        "resolution": list(opts["res"]),
        "samples": built["samples"] if built else "not-run",
        "view_transform": built["view_transform"] if built else "not-run",
        "input_sha256": {
            os.path.relpath(plan["loaded"]["data_path"], opts["root"]).replace("\\", "/"):
                plan["loaded"]["data_sha256"],
            os.path.relpath(plan["loaded"]["geom_path"], opts["root"]).replace("\\", "/"):
                plan["loaded"]["geom_sha256"],
        },
        "geometry_digest": plan["loaded"]["digest"],
        "cameras_authored": len(plan["cams"]),
        "objects_planned": plan["objects_planned"],
        "objects_built": built["objects"] if built else 0,
        "frames": [{"id": f["id"], "png": f["png"], "bytes": f["bytes"],
                    "seconds": round(f["seconds"], 2), "engine": f["engine"],
                    "cutaway": f["cutaway"],
                    "aim_error_deg": round(f["aim_error_deg"], 5)}
                   for f in frames],
        "elapsed_seconds": round(seconds, 1),
        "scope": "spatial blockout only; no engine export or runtime verification",
    }


def verdict_text(plan, opts, built, frames, status, seconds, now=None):
    """THE COMMITTED EVIDENCE FILE. Commit on line 1, key=value, no em-dashes.

    The art lane had no evidence file at all before this one: its only channel
    was the push of the PNGs themselves, so a render that failed after the
    checkout said nothing anywhere a person could read. Queue 152 asks for a
    key=value file naming its commit whatever happens, and this is it.
    """
    stamp = int(now if now is not None else time.time())
    lines = [
        "artPreviewVerdict=1 commit=%s commission=%s recipe=%s status=%s at=%d"
        % (opts["run_sha"], opts["commission"], RECIPE_STEM, status, stamp),
        "",
        "Written by the recipe itself inside Blender, into the preview",
        "directory the lane commits. Read this instead of the job log.",
        "A run that measured nothing says NO RUN and carries no frame of any",
        "earlier run under its own name.",
        "",
    ]
    lines.extend(plan_lines(plan, opts))
    for frame in frames:
        lines.append(
            "blockoutFrame idx=%d/%d id=%s png=%s bytes=%d engine=%s "
            "cutaway=%s aimError_deg=%.5f renderSeconds=%.1f"
            % (frame["index"] + 1, len(plan["cams"]), frame["id"], frame["png"],
               frame["bytes"], frame["engine"],
               "yes" if frame["cutaway"] else "no",
               frame["aim_error_deg"], frame["seconds"]))
    for note in (built or {}).get("notes", []):
        lines.append("blockoutNote " + note)
    if not frames:
        lines.append("NO RUN - no frame was rendered on this commit.")
    lines.append(done_line(plan, opts, built, frames, status, seconds))
    return "\n".join(lines) + "\n"


def refusal_verdict(opts, reason, now=None):
    """The same file for the paths that never reach a plan. Still line 1."""
    stamp = int(now if now is not None else time.time())
    return ("artPreviewVerdict=1 commit=%s commission=%s recipe=%s "
            "status=NO-RUN at=%d\n\nNO RUN - %s\n"
            "%s refused: status=NO-RUN reason=%s root=%s outDir=%s "
            "previewsWrote=0/0-cameras-reached nothing measured\n"
            % (opts["run_sha"], opts["commission"], RECIPE_STEM, stamp,
               "the recipe refused before any frame was rendered.",
               RECIPE_STEM, reason, opts["root"].replace(" ", "~"),
               (opts["out"] or "none").replace(" ", "~")))


def parse_args(argv):
    """Everything after the bare `--`, refused BY NAME when not understood.

    An unknown flag is an error rather than something ignored: a typo that
    renders the default scene into the right directory is an empty success the
    workflow's PNG count cannot catch, because the count would rise.
    """
    args = list(argv)
    if "--" in args:
        args = args[args.index("--") + 1:]
    else:
        args = args[1:] if args and args[0].endswith(".py") else args
    out = {"out": "", "root": ROOT, "commission": DEFAULT_COMMISSION,
           "res": AUTHORED_RES, "engine": "AUTO", "samples": 0,
           "run_sha": "not-passed", "studio_sha": "not-passed",
           "blend": True, "dry_run": False, "error": ""}
    i = 0

    def need(flag):
        if i + 1 >= len(args):
            out["error"] = "flag-without-a-value/" + flag
            return None
        return args[i + 1]

    while i < len(args):
        a = args[i]
        if a in ("--out", "--output-dir"):
            v = need(a)
            if v is None:
                break
            out["out"] = v
            i += 2
        elif a == "--root":
            v = need(a)
            if v is None:
                break
            out["root"] = v
            i += 2
        elif a == "--commission":
            v = need(a)
            if v is None:
                break
            if not v or set(v) & ID_BAD or ".." in v:
                out["error"] = "commission-is-not-a-plain-name/" + v.replace(" ", "~")
                break
            out["commission"] = v
            i += 2
        elif a == "--run-sha":
            v = need(a)
            if v is None:
                break
            out["run_sha"] = v.replace(" ", "~")
            i += 2
        elif a == "--studio-sha":
            v = need(a)
            if v is None:
                break
            out["studio_sha"] = v.replace(" ", "~")
            i += 2
        elif a == "--res":
            v = need(a)
            if v is None:
                break
            try:
                w, h = v.lower().split("x")
                out["res"] = (int(w), int(h))
            except ValueError:
                out["error"] = "res-is-not-WxH/" + v
                break
            if min(out["res"]) <= 0:
                out["error"] = "res-is-not-positive/" + v
                break
            i += 2
        elif a == "--engine":
            v = need(a)
            if v is None:
                break
            if v.upper() not in ("AUTO", "EEVEE", "CYCLES"):
                out["error"] = "engine-is-not-AUTO-or-EEVEE-or-CYCLES/" + v
                break
            out["engine"] = v.upper()
            i += 2
        elif a == "--samples":
            v = need(a)
            if v is None:
                break
            try:
                out["samples"] = int(v)
            except ValueError:
                out["error"] = "samples-is-not-an-integer/" + v
                break
            i += 2
        elif a == "--no-blend":
            out["blend"] = False
            i += 1
        elif a == "--dry-run":
            out["dry_run"] = True
            i += 1
        else:
            out["error"] = "unknown-flag/" + a.replace(" ", "~")
            break
    if not out["error"] and not out["out"] and not out["dry_run"]:
        out["error"] = "missing-flag/--out"
    return out


# ---------------------------------------------------------------------------
# THE BLENDER LAYER. Every line below touches bpy and therefore ships UNRUN
# from the container this was written in. It is kept thin and mechanical on
# purpose: it decides nothing, and it builds through bpy.data rather than
# bpy.ops so that no operator context, and no window that does not exist in
# background mode, is ever required.
# ---------------------------------------------------------------------------


def _require_bpy():
    if bpy is None:
        raise RuntimeError("no-bpy")


def _clear_scene():
    """(scene, removed, before) an empty scene, WITHOUT touching a window.

    The original creates a new scene and activates it with
    `bpy.context.window.scene = scene`. In `--background` there is no window,
    `bpy.context.window` is None, and that line raises. So this takes the
    scene the context already has, empties it through the data API, and
    renames it to the authored name. No operator, no window, no new scene to
    activate.
    """
    _require_bpy()
    scene = bpy.context.scene
    before = len(bpy.data.objects)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    scene.name = AUTHORED_SCENE_NAME
    return scene, before - len(bpy.data.objects), before


def _materials():
    """The authored palette, assigned RAW exactly as the original does."""
    _require_bpy()
    made = {}
    for name, rgb in MATERIALS:
        mat = bpy.data.materials.new("A01_" + name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1)
            bsdf.inputs["Roughness"].default_value = AUTHORED_ROUGHNESS
        made[name] = mat
    return made


def _box_mesh(name, su, sv, sh):
    """A unit box at the object's own origin, built from eight vertices.

    The original adds a primitive cube of size 1, sets `obj.dimensions` and
    applies the scale, which leaves the mesh at the authored size with the
    pivot at the bounds centre. This writes that mesh directly: same size,
    same pivot, no operator and no dependence on an active object.
    """
    _require_bpy()
    hx, hy, hz = su / 2.0, sv / 2.0, sh / 2.0
    verts = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
             (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


def _add_box(name, centre, size, material, collection, bom, rotation_x=0.0):
    _require_bpy()
    if min(size) <= 0:
        return None
    obj = bpy.data.objects.new("A01_" + name, _box_mesh(name, *size))
    collection.objects.link(obj)
    obj.location = centre
    obj.rotation_euler.x = math.radians(rotation_x)
    obj.data.materials.append(material)
    obj["bom_id"] = bom
    obj["pivot_policy"] = "bounds_center"
    obj["status"] = "spatial blockout; integration unverified"
    return obj


def _add_marker(name, point, kind, collection):
    """An empty, exactly as the original's `marker` (its lines 66 to 70)."""
    _require_bpy()
    obj = bpy.data.objects.new("A01_BIND_" + name, None)
    collection.objects.link(obj)
    obj.location = point
    obj.empty_display_type = "SPHERE"
    obj.empty_display_size = .12
    obj["proposed_binding"] = kind
    obj["runtime_binding"] = "NONE"
    return obj


def _add_text(spec, material, collection):
    """The fascia lettering through bpy.data, not bpy.ops.object.text_add.

    `text_add` places its object at the 3D cursor of an active view layer and
    relies on the operator leaving it active, both of which are context. A FONT
    curve made through the data API needs neither, and Blender assigns the
    built-in font to a new font curve itself.
    """
    _require_bpy()
    curve = bpy.data.curves.new("A01_Mickeys_lettering", type="FONT")
    curve.body = spec["text"]
    curve.align_x = "CENTER"
    curve.size = spec["size"]
    obj = bpy.data.objects.new("A01_Mickeys_lettering", curve)
    collection.objects.link(obj)
    obj.location = spec["position"]
    obj.rotation_euler = (math.pi / 2, 0, 0)   # original line 89
    obj.data.materials.append(material)
    return obj


def _add_camera(cam, scene):
    """The authored lens and the authored aim. Orientation from the vector.

    `to_track_quat('-Z', 'Y')` is the original's line 98 and it is kept,
    because it is the method that produced the framing the commission signed
    off. What is added is a read-back: the Blender layer measures the angle
    between the camera's actual forward axis and the authored target vector,
    so a convention error cannot hide behind a plausible rotation.
    """
    _require_bpy()
    data = bpy.data.cameras.new(cam["id"])
    data.lens = cam["lens_mm"]
    data.clip_end = max(200.0, cam["distance_m"] * 4.0)
    obj = bpy.data.objects.new("A01_CAM_" + cam["id"], data)
    scene.collection.objects.link(obj)
    obj.location = cam["pos"]
    direction = mathutils.Vector(cam["target"]) - mathutils.Vector(cam["pos"])
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return obj


def _aim_error_deg(obj, cam):
    """The camera's OWN forward axis against the authored vector, in degrees."""
    _require_bpy()
    bpy.context.view_layer.update()
    forward = (obj.matrix_world.to_3x3() @ mathutils.Vector((0.0, 0.0, -1.0)))
    want = mathutils.Vector(cam["target"]) - mathutils.Vector(cam["pos"])
    return angle_between_deg(list(forward), list(want))


def _resolve_engine(scene, asked):
    """(chosen, offered, notes). The enum THIS Blender offers, read not assumed.

    The art branch assigns `BLENDER_EEVEE_NEXT` outright. That identifier
    exists only in Blender 4.2 and later, and the lane probes 4.2 then 4.1, so
    on 4.1 the assignment raises and the run dies before a frame. This reads
    the property's own enum, picks the first candidate that is actually in it,
    assigns it, and READS IT BACK, so what is printed is what the scene has
    rather than what was requested.
    """
    _require_bpy()
    notes = []
    try:
        offered = [item.identifier for item in
                   scene.render.bl_rna.properties["engine"].enum_items]
    except Exception as exc:
        offered = []
        notes.append("engineEnumUnreadable=%s/falling-back-to-assignment"
                     % type(exc).__name__)
    if asked == "CYCLES":
        wanted = ["CYCLES"]
    elif asked == "EEVEE":
        wanted = [e for e in ENGINE_CANDIDATES if e != "CYCLES"]
    else:
        wanted = list(ENGINE_CANDIDATES)
    for name in wanted:
        if offered and name not in offered:
            continue
        try:
            scene.render.engine = name
        except (TypeError, ValueError):
            notes.append("engineRefused=%s/in-enum-but-not-assignable" % name)
            continue
        if scene.render.engine == name:
            return name, offered, notes
        notes.append("engineAssignedButReadBack=%s/wanted=%s"
                     % (scene.render.engine, name))
        return scene.render.engine, offered, notes
    return scene.render.engine, offered, notes + [
        "engineNoneOfTheCandidatesOffered=%d/%d-candidates"
        % (0, len(wanted))]


def _configure_render(scene, opts, engine):
    """Resolution, samples, format. Returns (samples, viewTransform) read back."""
    _require_bpy()
    scene.render.resolution_x = opts["res"][0]
    scene.render.resolution_y = opts["res"][1]
    scene.render.resolution_percentage = 100      # original line 30
    scene.render.image_settings.file_format = "PNG"
    samples = "engine-default/nothing-set"
    if engine == "CYCLES":
        # A TIME BOUND, NOT A QUALITY CLAIM. Cycles' own default is 4096, which
        # at five frames would outlast the job's cap and bank nothing.
        want = opts["samples"] or CYCLES_FALLBACK_SAMPLES
        try:
            scene.cycles.samples = want
            scene.cycles.use_denoising = True
            samples = "%d/cycles-%s" % (scene.cycles.samples,
                                        "asked" if opts["samples"] else "fallback-default")
        except AttributeError:
            samples = "cycles-properties-absent/nothing-set"
    elif opts["samples"]:
        try:
            scene.eevee.taa_render_samples = opts["samples"]
            samples = "%d/eevee-asked" % scene.eevee.taa_render_samples
        except AttributeError:
            samples = "eevee-properties-absent/nothing-set"
    else:
        try:
            samples = "%d/eevee-engine-default-read-back" % scene.eevee.taa_render_samples
        except AttributeError:
            samples = "eevee-properties-absent/nothing-read"
    try:
        view_transform = scene.view_settings.view_transform
    except AttributeError:
        view_transform = "unreadable"
    return samples, view_transform


def _render_to(scene, path):
    """The one operator left, because writing a PNG has no data-API form."""
    _require_bpy()
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def _build(plan, opts, scene, base, upper, materials):
    """The authored geometry, through bpy.data only. Counted as it happens."""
    _require_bpy()
    data, geom = plan["data"], plan["geom"]
    objects = 0
    for b in geom["boxes"]:
        u, v, w, d = b["box"]
        obj = _add_box(
            b["id"],
            (u + w / 2, v + d / 2, b["base"] + b["height"] / 2),
            (w, d, b["height"]),
            materials[b["material"]],
            upper if b["floor"] == "upper" else base,
            b["bom"], b["rotation_x"])
        if obj is not None:
            objects += 1
    for tri in geom["triangles"]:
        mesh = bpy.data.meshes.new(tri["id"])
        mesh.from_pydata(tri["vertices"], [], [(0, 1, 2)])
        mesh.update()
        obj = bpy.data.objects.new("A01_" + tri["id"], mesh)
        upper.objects.link(obj)
        obj.data.materials.append(materials[tri["material"]])
        objects += 1
    # DOORS. The leaf is re-parented to its hinge with its world transform
    # preserved, which is the original's lines 80 to 85. The drift is MEASURED
    # rather than assumed: a parenting that silently moved a door leaf is
    # exactly the class of thing no picture would show at blockout scale.
    parented, drift_mm = 0, 0.0
    for door in geom["doors"]:
        hinge = _add_marker(door["id"] + "_hinge", door["hinge"],
                            "door hinge; proposed state only", base)
        objects += 1
        leaf = (bpy.data.objects.get("A01_" + door["id"] + "_leaf")
                or bpy.data.objects.get("A01_" + door["id"] + "_open_leaf"))
        if leaf is not None:
            bpy.context.view_layer.update()
            world = leaf.matrix_world.copy()
            leaf.parent = hinge
            leaf.matrix_world = world
            bpy.context.view_layer.update()
            after = leaf.matrix_world
            worst = max(abs(after[r][c] - world[r][c])
                        for r in range(4) for c in range(4))
            drift_mm = max(drift_mm, worst * 1000.0)
            parented += 1
        _add_marker(door["id"] + "_threshold", door["threshold"],
                    "navigation threshold; not a live portal", base)
        objects += 1
    for room in data["upper_rooms"]:
        u, v, w, d = room["box"]
        _add_marker(room["id"],
                    (u + w / 2, v + d / 2, data["shell"]["ground_floor_height"]),
                    "authored room", base)
        objects += 1
    _add_text(data["fascia_text"], materials["paper"], base)
    objects += 1
    for name, point in data["information"].items():
        if isinstance(point, list):
            _add_marker(name, (point[0], point[1],
                               data["information"]["eye_height"]),
                        "perception/acoustic design marker; untested", base)
            objects += 1
    for name, route in data["paths"].items():
        for index, point in enumerate(route):
            _add_marker("%s_%02d" % (name, index), (point[0], point[1], .1),
                        "route intention; not navmesh", base)
            objects += 1
    return {"objects": objects, "doors_parented": parented,
            "door_drift_mm": drift_mm}


def _world_and_lights(scene):
    """The authored overcast world and the two authored area lights, raw."""
    _require_bpy()
    world = bpy.data.worlds.new(AUTHORED_WORLD_NAME)
    world.use_nodes = True
    scene.world = world
    background = world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = AUTHORED_SKY_RGBA
        background.inputs["Strength"].default_value = AUTHORED_SKY_STRENGTH
    made = 0
    for name, location, energy, size, shape, colour in AUTHORED_LIGHTS:
        light = bpy.data.lights.new(name, "AREA")
        light.energy = energy
        light.size = size
        if shape is not None:
            light.shape = shape
        if colour is not None:
            light.color = colour
        obj = bpy.data.objects.new(name, light)
        scene.collection.objects.link(obj)
        obj.location = location
        made += 1
    return made


# ---------------------------------------------------------------------------


def main(argv):
    started = time.time()
    opts = parse_args(argv)
    if opts["error"]:
        print("%s refused: status=BAD-ARGS reason=%s nothing measured"
              % (RECIPE_STEM, opts["error"]))
        return 2
    opts["root"] = os.path.abspath(opts["root"])
    plan, err = build_plan(opts["root"], opts)
    if err:
        # THE REFUSAL NAMES WHAT WAS ASKED FOR AND WHERE IT LOOKED. On the
        # studio branch the commission's two files are absent, so this is the
        # path a dry run in the container takes, and it is the accepting case
        # for the refusal.
        print("%s refused: status=NO-COMMISSION-DATA commission=%s reason=%s "
              "root=%s dataPath=%s geomPath=%s previewsWrote=0/0-cameras-read "
              "nothing measured"
              % (RECIPE_STEM, opts["commission"], err, opts["root"],
                 commission_paths(opts["root"], opts["commission"])[0],
                 commission_paths(opts["root"], opts["commission"])[1]))
        if opts["out"]:
            _write_refusal(opts, err)
        return 3
    for line in plan_lines(plan, opts):
        print(line)
    if opts["dry_run"]:
        print(done_line(plan, opts, None, [],
                        "DRY-RUN/planned-only/nothing-built-and-nothing-measured",
                        time.time() - started))
        return 0
    if bpy is None:
        print("%s refused: status=NO-BPY reason=run-me-through-blender-not-python "
              "nothing measured" % RECIPE_STEM)
        return 6

    out_dir = os.path.abspath(opts["out"])
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        print("%s refused: status=NO-OUTDIR reason=%s nothing measured"
              % (RECIPE_STEM, type(exc).__name__))
        return 7

    scene, removed, before = _clear_scene()
    notes = ["sceneReset=dataApi/removed=%d/%d-objects" % (removed, before)]
    base = bpy.data.collections.new(BASE_COLLECTION)
    scene.collection.children.link(base)
    upper = bpy.data.collections.new(UPPER_COLLECTION)
    scene.collection.children.link(upper)
    scene.unit_settings.system = "METRIC"        # original line 28
    scene.unit_settings.scale_length = 1
    materials = _materials()
    built = _build(plan, opts, scene, base, upper, materials)
    built["lights"] = _world_and_lights(scene)
    print("blockoutBuild objectsBuilt=%d/%d-planned doorsParented=%d/%d-authored "
          "doorLeafDrift_mm=%.4f lights=%d/%d-authored elapsedSeconds=%.1f"
          % (built["objects"], plan["objects_planned"], built["doors_parented"],
             plan["doors"], built["door_drift_mm"], built["lights"],
             len(AUTHORED_LIGHTS), time.time() - started))

    engine, offered, engine_notes = _resolve_engine(scene, opts["engine"])
    notes.extend(engine_notes)
    samples, view_transform = _configure_render(scene, opts, engine)
    built["engine_offered"] = "%d/%d-candidates-in-enum-of-%s" % (
        sum(1 for c in ENGINE_CANDIDATES if c in offered), len(ENGINE_CANDIDATES),
        len(offered) if offered else "unreadable")
    built["samples"] = samples
    built["view_transform"] = view_transform
    built["blender_version"] = bpy.app.version_string.replace(" ", "~")
    built["in_scene"] = len(scene.objects)
    print("blockoutEngine engineAsked=%s engineChosen=%s "
          "candidatesOffered=%s enumSize=%s samples=%s viewTransform=%s "
          "blender=%s res=%dx%d"
          % (opts["engine"], engine, built["engine_offered"],
             len(offered) if offered else "unreadable", samples, view_transform,
             built["blender_version"], opts["res"][0], opts["res"][1]))

    cams = {cam["id"]: _add_camera(cam, scene) for cam in plan["cams"]}
    frames = []
    for cam in plan["cams"]:
        # THE CUTAWAY IS THE AUTHORED ONE, per camera, and it is restored after
        # the loop exactly as the original's line 111 does.
        for obj in upper.objects:
            obj.hide_render = cam["cutaway"]
        scene.camera = cams[cam["id"]]
        path = os.path.join(out_dir, cam["png"])
        t0 = time.time()
        _render_to(scene, path)
        took = time.time() - t0
        # VERIFY THE EFFECT, NOT THE CALL. bpy.ops.render.render returns
        # FINISHED whether or not a file landed on disk.
        size = os.path.getsize(path) if os.path.exists(path) else 0
        used = engine
        if size == 0 and engine != "CYCLES" and opts["engine"] == "AUTO":
            # ONE FALLBACK, ON THE FIRST FRAME ONLY, and it is announced. EEVEE
            # needs a GL context; a Windows runner with no interactive session
            # may not have one, and the whole run would otherwise be five empty
            # successes. Cycles needs none. The switch happens on frame one so
            # all five frames come from ONE engine rather than a mixed set, and
            # every frame line prints which engine drew it.
            notes.append("engineFellBack=%s..CYCLES/reason=first-frame-0-bytes"
                         % engine)
            engine, offered2, more = _resolve_engine(scene, "CYCLES")
            notes.extend(more)
            samples, view_transform = _configure_render(scene, opts, engine)
            built["samples"] = samples
            built["view_transform"] = view_transform
            t0 = time.time()
            _render_to(scene, path)
            took += time.time() - t0
            size = os.path.getsize(path) if os.path.exists(path) else 0
            used = engine
        frames.append({"index": cam["index"], "id": cam["id"], "png": cam["png"],
                       "bytes": size, "seconds": took, "engine": used,
                       "cutaway": cam["cutaway"],
                       "aim_error_deg": _aim_error_deg(cams[cam["id"]], cam)})
        print("blockoutFrame idx=%d/%d id=%s png=%s bytes=%d engine=%s "
              "cutaway=%s aimError_deg=%.5f renderSeconds=%.1f"
              % (cam["index"] + 1, len(plan["cams"]), cam["id"], cam["png"],
                 size, used, "yes" if cam["cutaway"] else "no",
                 frames[-1]["aim_error_deg"], took))
    for obj in upper.objects:
        obj.hide_render = False

    built["blend_bytes"] = "not-asked/--no-blend"
    if opts["blend"]:
        # AFTER the frames, never before: a save that fails must not cost the
        # pictures. The commission's render-request.json asks for the .blend to
        # be banked so the upper floor can be inspected behind the cutaway.
        blend = os.path.join(out_dir, RECIPE_STEM + ".blend")
        try:
            bpy.ops.wm.save_as_mainfile(filepath=blend)
            built["blend_bytes"] = str(os.path.getsize(blend)
                                       if os.path.exists(blend) else 0)
        except Exception as exc:
            built["blend_bytes"] = "save-refused/" + type(exc).__name__
            notes.append("blendNotSaved=%s" % type(exc).__name__)
    built["notes"] = notes

    wrote = sum(1 for f in frames if f["bytes"] > 0)
    total = len(plan["cams"])
    status = "RAN" if wrote == total else "PARTIAL"
    seconds = time.time() - started
    # THE EVIDENCE FILE, written whatever the status, before the exit code is
    # decided, so a PARTIAL run says so in the file the lane commits.
    _write_verdict(plan, opts, built, frames, status, seconds, out_dir)
    for note in notes:
        print("blockoutNote " + note)
    print(done_line(plan, opts, built, frames, status, seconds))
    return 0 if wrote == total else 8


def _write_verdict(plan, opts, built, frames, status, seconds, out_dir):
    text = verdict_text(plan, opts, built, frames, status, seconds)
    path = os.path.join(out_dir, RECIPE_STEM + "-verdict.txt")
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        size = os.path.getsize(path)
    except OSError as exc:
        print("%s note: verdictNotWritten=%s path=%s"
              % (RECIPE_STEM, type(exc).__name__, path.replace(" ", "~")))
        return
    print("%s verdict: path=%s bytes=%d lines=%d"
          % (RECIPE_STEM, path.replace(" ", "~"), size,
             text.count("\n")))
    receipt = os.path.join(out_dir, "receipt.json")
    try:
        with open(receipt, "w", encoding="utf-8") as handle:
            json.dump(receipt_dict(plan, opts, built, frames, status, seconds),
                      handle, indent=2)
            handle.write("\n")
    except OSError as exc:
        print("%s note: receiptNotWritten=%s" % (RECIPE_STEM, type(exc).__name__))


def _write_refusal(opts, reason):
    """A refusal that reached an output directory still leaves the file there."""
    out_dir = os.path.abspath(opts["out"])
    try:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, RECIPE_STEM + "-verdict.txt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(refusal_verdict(opts, reason))
        print("%s verdict: path=%s status=NO-RUN"
              % (RECIPE_STEM, path.replace(" ", "~")))
    except OSError as exc:
        print("%s note: verdictNotWritten=%s" % (RECIPE_STEM, type(exc).__name__))


# RUN WHEN BLENDER RUNS ME, STAY QUIET WHEN A TEST IMPORTS ME. Blender executes
# a --python script with __name__ set to "__main__", and run-recipe.py imports
# this file with no bpy in the process to exercise the pure layer. The second
# clause is belt and braces for a Blender build that ever stopped setting
# __name__: if bpy is importable, this file is inside Blender and has work to do.
if __name__ == "__main__" or bpy is not None:
    sys.exit(main(sys.argv))
