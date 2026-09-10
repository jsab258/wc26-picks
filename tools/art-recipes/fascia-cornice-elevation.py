#!/usr/bin/env python3
"""Blender recipe: LOOK AT THE FASCIA PACKAGE BEFORE THE ENGINE DOES.

    python3 tools/art-recipes/run-recipe.py fascia-cornice-elevation --plan
    python3 tools/art-recipes/run-recipe.py fascia-cornice-elevation --out DIR
    python3 tools/art-recipes/fascia-cornice-elevation.py --selftest

WRITTEN IN HOUSE, AND THAT IS THE POINT OF IT. Jafar's order of 2026-09-10:
the next Blender recipe is written in house, not adapted from the outside
account's, so the 3D route is tested the same way the image route is. The image
lane had proved it could DRAW from a derived prompt and was then asked whether
it could AUTHOR one. This is the same test on the 3D route. Every number below
is read from this project's own spec files or derived from them by arithmetic
printed in the plan; no existing recipe was opened to see how it phrased
anything, and the only file consulted for interface was run-recipe.py, which is
the runner and not a recipe.

WHAT IT IS FOR, WHICH IS NOT DECORATION. CLAUDE.md rule 4 says open the
artifact you are shipping, and rule 12 says a blocked feedback channel is the
highest-leverage bug on the board. The fascia package's whole justification is
a shape: production/art/fascia-01/01-SPEC-fascia-package.md section 0 argues
that geometry goes where the shadow is, that the cornice oversails the board by
0.0950 m and throws "a dry strip above a wet band and a hard horizontal shadow
line across a 36 m terrace", and that the console reads as a scroll silhouette.
NONE OF THAT IS VISIBLE IN A PIECE LIST. A 12 mm drip groove at 0.1550 to
0.1750 m from the wall exists, or does not, only in a view from underneath. The
burial arithmetic, the box measurement and the byte-for-byte regeneration all
pass on geometry that could still be the wrong shape, so this renders the three
views in which the claim is falsifiable.

WHAT IT DRAWS, AND THE RULE IT OBEYS. D14, 2026-09-08: authored breadth, not
generated breadth. This recipe INVENTS NO GEOMETRY. Every object in the scene
is either
  (a) a box, cylinder or quad whose six numbers come from a row of
      production/specs/vignette-pieces.json, or
  (b) a .glb imported from ledger/Assets/Props/base-mesh and never scaled,
      stood with its own bounds centre on the row's centre, which is the rule
      the piece file's own frame block states as
      "load-asset/never-scale-it/put-its-own-bounds-centre-on-x_m,y_m,z_m".
A piece it cannot draw is REFUSED BY NAME and counted, never approximated.

WHICH PIECES, AND THE BILL OF MATERIALS DECIDES. The window is a list of BOM
lines, not an x range and not a guess about what looks like a frontage, because
the bill of materials is the document that says what the frontage is made of.
Lines present in the file and not in the window are counted and named in the
plan, with the cap announced, so the window's edge is a reviewable decision
rather than an accident.

TWO LIGHT CONDITIONS, BOTH READ FROM THE FILE BY NAME, and the second one is
a diagnostic rather than a frame anybody should judge:
  overcast_day        sun 3, sky 1.00. THE SHIPPING CONDITION. canon.md fixes
                      wet, overcast, grimy Britain, and under it the cornice
                      does not throw a hard sun shadow at all: what it buys is
                      occlusion under the soffit and a DRY STRIP on the board
                      beneath it. That is the read the package is judged on.
  grid_sky035_sun030  sun 30, sky 0.35, the hardest-light cell of the file's
                      own four-by-three grid. NOT A TARGET LOOK. It exists
                      because a silhouette is unambiguous under a raking light
                      and ambiguous under a dome, so a mis-shaped moulding
                      hides in the shipping condition and cannot hide here.
Both rows are lifted out of the piece file's conditions block by id. Neither
intensity is typed in this file.

WHAT THIS CANNOT DO, SAID PLAINLY RATHER THAN DISCOVERED LATER.
  BLENDER IS NOT IN THIS CONTAINER. Checked, not assumed: `blender` is not on
  PATH and `bpy` does not import. So the render half of this file has never
  executed here and the first real run is on the Windows runner. --selftest and
  --plan cover everything that does not need bpy: the spec read, the window,
  the refusals, the camera arithmetic and the frame list.
  THE HDRI NAMED BY EACH CONDITION ROW IS NOT LOADED. Those rows name
  Sky/polyhaven paths that are engine-side assets, nothing is ever fetched
  here, and a sky image is not needed to answer a question about shape. The
  world is a uniform grey scaled by the row's own sky_intensity, and the plan
  says so in `hdri=NOT-LOADED/<name>` so no reader mistakes this for the
  lighting the engine will produce.
  IT IS A FORM CHECK AND NOT A MATERIAL CHECK. Every surface renders as one
  neutral clay grey, including the new mouldings, so the read is shape and
  shadow. Giving the cornice its own tint would make the preview lie about
  what stands out in the frame. Wetness, grime, the sodium lanterns and the
  window practicals are all absent and all named in the plan.
  NO DECAL IMAGE IS BOUND. The four C6 lettering quads are drawn as flat
  untextured plates at their own size and position, which is what acceptance
  check A10 needs (how much lettering height a cornice eats) and is all the
  letters are needed for here.

NOT AN INSTRUMENT. It prints no verdict key, no gate reads it, and nothing in
CI depends on its numbers. It is a camera.
"""
import json
import math
import os
import sys

RECIPE = "fascia-cornice-elevation"

#: The spec this recipe reads. It is the file both engines build from, so a
#: preview taken from anything else would be a preview of a different street.
SPEC_REL = "production/specs/vignette-pieces.json"
#: Where a mesh piece's bytes live. The asset id IS the file name, which is
#: production/specs/asset-interface.md's rule.
PROPS_REL = "ledger/Assets/Props/base-mesh"

#: THE WINDOW, BY BILL-OF-MATERIALS LINE. East frontage and the ground it
#: stands on. Each line is here for a reason a reader can check:
WINDOW_BOM = (
    "A0_ground_planes",            # the shadow needs a floor to fall on
    "B1_kerbstone_run",            # and the footway needs an edge, for scale
    "C1_terrace_carcass",          # the wall the mouldings are fixed to
    "C5_shopfront_assembly",       # fascia band, pilasters, stallriser, transom
    "C6_fascia_lettering",         # A10: how much letter height a cornice eats
    "C7_shop_glazing",             # the dark window the console is read against
    "C8_door_shop",                # the bay's rhythm reads wrong without doors
    "C13_sills_lintels",           # the course above, so the cornice has context
    "C15_fascia_cornice_console",  # THE PACKAGE UNDER REVIEW
    "D5_downpipe",                 # the pipe the 5.8920 m run stops short of
    "D6_gutter_run",               # the eaves line, the other horizontal
    "D8_upper_windows",            # the storey above the shopfront
    "E18_shop_awnings",            # the one existing wall prop, for comparison
)

#: THE TWO CONDITIONS, BY ID, lifted from the spec's own conditions block.
CONDITION_IDS = ("overcast_day", "grid_sky035_sun030")

#: One neutral clay for everything. A form check says so by looking like one.
CLAY = (0.52, 0.50, 0.48, 1.0)

#: Render size. 1600x900 is a 16:9 the shadow line crosses at roughly one
#: pixel per 23 mm of a 36 m terrace, which is the scale the claim is made at.
RENDER_W, RENDER_H = 1600, 900
#: Cycles samples. Chosen as the smallest count at which soft shadow from a
#: sky dome stops being visibly noisy at this size; it is a render setting and
#: not a measurement, and it is named here so it is not mistaken for one.
SAMPLES = 96


# ---------------------------------------------------------------------------
# PURE. Everything down to the last camera angle, testable with no bpy.
# ---------------------------------------------------------------------------

def repo_root(start=None):
    """Walk up until the spec is under foot. The recipe may be launched from
    Blender's own working directory, which is not the repository."""
    d = os.path.dirname(os.path.abspath(start or __file__))
    while True:
        if os.path.exists(os.path.join(d, SPEC_REL)):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def load_spec(root):
    with open(os.path.join(root, SPEC_REL), "r", encoding="utf-8") as fh:
        return json.load(fh)


def asset_id(field):
    """The id half of an `asset` field. The interface allows an atlas rect
    after a `#`, and a mesh row carries none, but splitting is free and a
    recipe that assumed otherwise would fail on the first textured prop."""
    if not field:
        return ""
    return field.split("#", 1)[0]


def to_blender(x_m, y_m, z_m):
    """THE ONE AXIS MAP, WRITTEN ONCE.

    The piece file's frame is y-up: x along the street, y up from the road
    crown, +z east. Blender is z-up. The map is (x, y, z) -> (x, -z, y), whose
    determinant is +1, so handedness is preserved and no mesh comes out
    mirrored.

    IT IS ALSO THE MAP BLENDER'S OWN glTF IMPORTER APPLIES. glTF is y-up, and
    the importer's default conversion rotates +90 degrees about X, which sends
    glTF (x, y, z) to Blender (x, -z, y). The same map. So an imported .glb and
    a box built from a row of the piece file arrive in the same orientation
    with no correction anywhere, which is why this function has exactly one
    caller per object and no special case for meshes.
    """
    return (x_m, -z_m, y_m)


def box_dims(sx_m, sy_m, sz_m):
    """A piece's full size under the same map. The frame block says size is
    full-size-before-rotation and not half extents."""
    return (sx_m, sz_m, sy_m)


def rotation_triple(piece):
    """(axis, degrees) for the one rotation a piece may carry, or (None, 0).

    THE FILE'S counts.multi_rotation IS 0 AND THIS REFUSES RATHER THAN GUESS.
    With at most one non-zero angle per piece there is no composition order to
    get wrong, so this returns a single axis and the caller applies it. The day
    that count stops being zero, a piece with two angles comes back as
    ("AMBIGUOUS", n) and is refused by name instead of being drawn at an
    orientation nobody chose. The C++ placement header makes the same call for
    the same reason, in VignetteSpec.h's SpecBoxBounds.
    """
    pitch = float(piece.get("pitch_deg", 0.0) or 0.0)
    yaw = float(piece.get("yaw_deg", 0.0) or 0.0)
    roll = float(piece.get("roll_deg", 0.0) or 0.0)
    live = [(n, v) for n, v in (("pitch", pitch), ("yaw", yaw), ("roll", roll))
            if abs(v) > 1e-12]
    if not live:
        return (None, 0.0)
    if len(live) > 1:
        return ("AMBIGUOUS", len(live))
    name, value = live[0]
    # pitch is about the project's +x, which is Blender's +x.
    # yaw   is about the project's +y, which is Blender's +z.
    # roll  is about the project's +z, which is Blender's -y.
    axis = {"pitch": "X", "yaw": "Z", "roll": "Y"}[name]
    sign = {"pitch": 1.0, "yaw": 1.0, "roll": -1.0}[name]
    return (axis, sign * value)


def select_window(spec, window_bom=WINDOW_BOM, side="east"):
    """The pieces this preview draws, and everything it is leaving out.

    Returns (drawn, skipped_bom, refused). `side` keeps the west frontage out:
    the west has no C5 assembly, so it has no fascia band and nothing in this
    package touches it.
    """
    want = set(window_bom)
    drawn, refused = [], []
    seen_bom = set()
    for p in spec.get("pieces", []):
        bom = p.get("bom", "")
        seen_bom.add(bom)
        if bom not in want:
            continue
        edge = p.get("edge", "") or ""
        region = p.get("region", "") or ""
        # A0 ground planes carry an edge per strip; the east ones and the two
        # carriageway strips are what a pavement-level shadow lands on.
        if side and edge and not edge.startswith(side) and "carriageway" not in edge:
            continue
        axis, deg = rotation_triple(p)
        if axis == "AMBIGUOUS":
            refused.append((p.get("name", "unnamed"),
                            "two-live-rotations/file-counts-multi_rotation-as-0"))
            continue
        shape = p.get("shape", "")
        if shape not in ("box", "cyl", "mesh", "decal"):
            refused.append((p.get("name", "unnamed"), "unknown-shape/" + (shape or "empty")))
            continue
        drawn.append(p)
        del region
    skipped = sorted(b for b in seen_bom if b and b not in want)
    return drawn, skipped, refused


def mesh_requests(drawn, root):
    """(found, missing) asset ids for the mesh pieces in the window.

    A missing .glb is NAMED and the piece is not drawn as a box in its place.
    A box standing in for a moulding is the exact failure this preview exists
    to catch, so the preview must never manufacture one.
    """
    found, missing = {}, []
    for p in drawn:
        if p.get("shape") != "mesh":
            continue
        aid = asset_id(p.get("asset", ""))
        if aid in found or aid in missing:
            continue
        path = os.path.join(root, PROPS_REL, aid + ".glb")
        if os.path.exists(path):
            found[aid] = path
        else:
            missing.append(aid)
    return found, sorted(missing)


def piece_named(spec, name):
    for p in spec.get("pieces", []):
        if p.get("name") == name:
            return p
    return None


def pieces_of_bom(spec, bom):
    return [p for p in spec.get("pieces", []) if p.get("bom") == bom]


def aim_at(eye, target):
    """(yaw_deg, pitch_deg) in the PROJECT's frame, from one point to another.

    Yaw is the frame block's own definition, a bearing from +x turning +x
    toward +z; pitch is positive looking UP, which is the sense the spec file's
    cameras use (cam_A carries pitch 4 and looks up the frontage).

    Written as arithmetic rather than typed, because a camera angle typed into
    a recipe is a number nobody can check against the street.
    """
    dx = target[0] - eye[0]
    dy = target[1] - eye[1]
    dz = target[2] - eye[2]
    flat = math.hypot(dx, dz)
    yaw = math.degrees(math.atan2(dz, dx))
    pitch = math.degrees(math.atan2(dy, flat)) if flat > 1e-9 else (90.0 if dy > 0 else -90.0)
    return (yaw, pitch)


def blender_camera_euler(yaw_deg, pitch_deg):
    """Blender XYZ Euler for a camera that looks along the project yaw/pitch.

    A Blender camera looks down its own local -Z with +Y up. Rotating
    (90 - pitch) about X stands it horizontal and tips it; then a rotation
    about Z turns it. The Z term is (90 - yaw) because the project's yaw is a
    bearing from +x turning toward +z, and +z is Blender's -y: a project yaw of
    0 looks along +x, which a Blender camera reaches at a Z rotation of +90.
    """
    rx = math.radians(90.0 - pitch_deg)
    rz = math.radians(90.0 - yaw_deg)
    return (rx, 0.0, rz)


def plan_shots(spec, bay_x):
    """THE THREE VIEWS, each one derived and each one saying where from.

    Shot 1 is the file's own cam_A, verbatim, because the street is judged from
    that camera and a preview from somewhere else answers a question nobody
    asked. Shots 2 and 3 are computed from the geometry under review: the eye
    is placed by a clearance and the aim falls out of aim_at, so there is no
    angle in this file that a reader cannot re-derive.
    """
    shots = []

    cam_a = None
    for c in spec.get("cameras", []):
        if c.get("id") == "cam_A":
            cam_a = c
            break
    if cam_a is not None:
        eye = (float(cam_a["x_m"]),
               float(cam_a["ground_y_m"]) + float(cam_a["eye_height_above_ground_m"]),
               float(cam_a["z_m"]))
        shots.append({
            "id": "terrace_raking",
            "why": "the-whole-36-m-terrace-so-the-shadow-line-reads-as-a-LINE",
            "eye": eye,
            "yaw": float(cam_a["yaw_deg"]),
            "pitch": float(cam_a["pitch_deg"]),
            "fov": float(cam_a["fov_vertical_deg"]),
            "from": "the-spec-files-own-cam_A-verbatim",
        })

    # The console this preview examines: the left-hand pilaster of the chosen
    # bay, found by position in the piece list rather than by index, so a
    # re-ordered file cannot silently change which console is shown.
    consoles = [p for p in pieces_of_bom(spec, "C15_fascia_cornice_console")
                if asset_id(p.get("asset", "")) == "fascia_console_01"]
    cornices = [p for p in pieces_of_bom(spec, "C15_fascia_cornice_console")
                if asset_id(p.get("asset", "")) == "fascia_cornice_01"]
    subject = None
    for p in sorted(consoles, key=lambda q: q["x_m"]):
        if p["x_m"] >= bay_x - 3.1:
            subject = p
            break
    if subject is not None:
        cx, cy, cz = subject["x_m"], subject["y_m"], subject["z_m"]
        # Two metres off the console, square to the street, at its own height.
        # 2.0 m is the footway's own width, so the eye stands at the kerb: the
        # furthest back a person can get from this console without stepping
        # into the road.
        eye = (cx - 1.0, cy, cz - 2.0)
        yaw, pitch = aim_at(eye, (cx, cy, cz))
        shots.append({
            "id": "console_scroll",
            "why": "the-scroll-silhouette-square-on-at-the-consoles-OWN-height/an-INSPECTION-view-and-not-an-eye-level-one/2.0-m-off-the-frontage-which-is-the-footway-width",
            "eye": eye,
            "yaw": yaw,
            "pitch": pitch,
            "fov": 39.0,
            "from": "derived/eye-at-the-consoles-own-y-and-the-footway-width-in-z/aim-computed",
            "subject": subject.get("name", "unnamed"),
        })

    if cornices:
        corn = min(cornices, key=lambda q: abs(q["x_m"] - bay_x))
        cx, cy, cz = corn["x_m"], corn["y_m"], corn["z_m"]
        soffit_y = cy - corn["sy_m"] / 2.0
        outer_z = cz - corn["sz_m"] / 2.0
        # Standing height from the file's own cameras, close in, looking up at
        # the outer arris. The drip groove sits 0.1550 to 0.1750 m from the
        # wall and is only a groove from below.
        eye = (cx - 0.6, 1.6, outer_z - 0.9)
        yaw, pitch = aim_at(eye, (cx, soffit_y, outer_z))
        shots.append({
            "id": "drip_soffit",
            "why": "the-12-mm-drip-groove-which-exists-only-in-a-view-from-underneath",
            "eye": eye,
            "yaw": yaw,
            "pitch": pitch,
            "fov": 50.0,
            "from": "derived/aimed-at-the-cornices-own-soffit-outer-arris",
            "subject": corn.get("name", "unnamed"),
        })
    return shots


def plan_conditions(spec, ids=CONDITION_IDS):
    """The named rows, and a refusal if the file stopped carrying one."""
    by_id = {c.get("id"): c for c in spec.get("conditions", [])}
    out, missing = [], []
    for cid in ids:
        if cid in by_id:
            out.append(by_id[cid])
        else:
            missing.append(cid)
    return out, missing


def tally(items, cap=6):
    """A list inside a key=value value. No spaces, and the cap announces."""
    if not items:
        return "none"
    shown = [str(i).replace(" ", "~") for i in items[:cap]]
    if len(items) > cap:
        shown.append("(+%d~more~not~shown)" % (len(items) - cap))
    return ";".join(shown)


def plan_lines(spec, root, bay_x):
    """THE PLAN, and it is the whole pure layer's output.

    Every count ships its denominator and every zero says what it is a zero
    of, because a plan that prints `refused=0` without saying over what cannot
    tell nothing from fine.
    """
    drawn, skipped, refused = select_window(spec)
    found, missing = mesh_requests(drawn, root)
    shots = plan_shots(spec, bay_x)
    conds, cond_missing = plan_conditions(spec)
    sun = spec.get("sun", {})
    counts = spec.get("counts", {})
    shapes = {}
    for p in drawn:
        shapes[p.get("shape", "?")] = shapes.get(p.get("shape", "?"), 0) + 1

    lines = []
    lines.append("recipe=%s station=3-VERIFY/a-look-not-a-gate package=fascia-01" % RECIPE)
    lines.append("spec=%s specPieces=%d/of=%s-in-the-header specAheadOfRun=%s"
                 % (SPEC_REL, len(spec.get("pieces", [])),
                    counts.get("pieces", "unknown"),
                    (spec.get("ahead_of_unity_run") or {}).get("run", "none")))
    lines.append("windowPieces=%d/of=%d bomLinesDrawn=%d/of=%d "
                 "bomLinesNotDrawn=%s side=east/the-west-has-no-C5-assembly-so-no-fascia-band"
                 % (len(drawn), len(spec.get("pieces", [])),
                    len(WINDOW_BOM), len(WINDOW_BOM) + len(skipped), tally(skipped)))
    lines.append("windowShapes=" + "/".join("%s:%d" % kv for kv in sorted(shapes.items()))
                 + " refusedPieces=%d/of=%d %s"
                 % (len(refused), len(drawn) + len(refused),
                    tally(["%s:%s" % r for r in refused])))
    lines.append("meshAssetsAsked=%d glbFound=%d/of=%d glbMissing=%s "
                 "meshRule=never-scaled/own-bounds-centre-on-the-rows-centre"
                 % (len(found) + len(missing), len(found),
                    len(found) + len(missing), tally(missing)))
    lines.append("sunElevationDeg=%s sunAzimuthDeg=%s sunFrom=the-spec-files-own-sun-block"
                 % (sun.get("elevation_deg", "unknown"), sun.get("azimuth_deg", "unknown")))
    for c in conds:
        lines.append("condition=%s sunIntensity=%s skyIntensity=%s wetness=%s/NOT-APPLIED "
                     "hdri=NOT-LOADED/%s role=%s"
                     % (c.get("id"), c.get("sun_intensity"), c.get("sky_intensity"),
                        c.get("wetness"),
                        str(c.get("hdri", "none")).replace(" ", "~"),
                        "the-shipping-condition" if c.get("id") == "overcast_day"
                        else "a-diagnostic-NOT-a-target-look"))
    if cond_missing:
        lines.append("conditionsMissing=%s "
                     "reason=the-spec-file-no-longer-carries-a-row-this-recipe-names"
                     % tally(cond_missing))
    for s in shots:
        lines.append("shot=%s eyeXYZm=%.3f/%.3f/%.3f yawDeg=%.2f pitchDeg=%.2f "
                     "fovVDeg=%.1f subject=%s poseFrom=%s why=%s"
                     % (s["id"], s["eye"][0], s["eye"][1], s["eye"][2],
                        s["yaw"], s["pitch"], s["fov"],
                        s.get("subject", "the-whole-frontage"),
                        s["from"], s["why"]))
    lines.append("shots=%d conditions=%d framesPlanned=%d renderPx=%dx%d samples=%d"
                 % (len(shots), len(conds), len(shots) * len(conds),
                    RENDER_W, RENDER_H, SAMPLES))
    lines.append("absentOnPurpose=wetness/grime/lanterns/window-practicals/decal-images/hdri "
                 "because=this-is-a-FORM-check-and-one-clay-grey-says-so")
    return lines


# ---------------------------------------------------------------------------
# IMPURE. bpy only below this line.
# ---------------------------------------------------------------------------

def _clay_material(bpy, name="fascia_preview_clay"):
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = CLAY
        # Dry-ish matte. Wetness is a condition field this preview does not
        # apply, and a glossy clay would imply it had.
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.75
    return mat


def _apply_rotation(obj, piece, math_mod):
    axis, deg = rotation_triple(piece)
    if axis is None:
        return
    rad = math_mod.radians(deg)
    if axis == "X":
        obj.rotation_euler = (rad, 0.0, 0.0)
    elif axis == "Y":
        obj.rotation_euler = (0.0, rad, 0.0)
    else:
        obj.rotation_euler = (0.0, 0.0, rad)


def _build_box(bpy, piece, mat):
    bpy.ops.mesh.primitive_cube_add(size=1.0,
                                    location=to_blender(piece["x_m"], piece["y_m"], piece["z_m"]))
    obj = bpy.context.active_object
    obj.name = piece.get("name", "piece")
    obj.scale = box_dims(piece["sx_m"], piece["sy_m"], piece["sz_m"])
    _apply_rotation(obj, piece, math)
    obj.data.materials.append(mat)
    return obj


def _build_cyl(bpy, piece, mat):
    # The frame block: a cylinder's axis is local +y in both engines, height is
    # sy_m, diameter is sx_m and sz_m. Blender's cylinder stands on +z, which
    # IS the project's +y under the axis map, so no extra rotation.
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=piece["sx_m"] / 2.0, depth=piece["sy_m"],
        location=to_blender(piece["x_m"], piece["y_m"], piece["z_m"]))
    obj = bpy.context.active_object
    obj.name = piece.get("name", "piece")
    _apply_rotation(obj, piece, math)
    obj.data.materials.append(mat)
    return obj


def _build_decal(bpy, piece, mat):
    # A quad, sx by sy, normal -z before rotation. Under the axis map the
    # project's -z is Blender's +y, and a Blender plane's normal is +z, so the
    # plane is stood up by -90 degrees about X and then carries its own yaw.
    bpy.ops.mesh.primitive_plane_add(
        size=1.0, location=to_blender(piece["x_m"], piece["y_m"], piece["z_m"]))
    obj = bpy.context.active_object
    obj.name = piece.get("name", "decal")
    obj.scale = (piece["sx_m"], piece["sy_m"], 1.0)
    obj.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
    obj.data.materials.append(mat)
    return obj


def _import_glb(bpy, path, name):
    """Import and return the objects that arrived, or [] and say so.

    The importer's selection is the only reliable handle on what a file
    brought in, because a .glb may carry several nodes and the scene already
    has objects in it.
    """
    before = set(o.name for o in bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    arrived = [o for o in bpy.data.objects if o.name not in before]
    for i, o in enumerate(arrived):
        o.name = "%s_src%d" % (name, i)
    return arrived


def _world_bounds(objs):
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for o in objs:
        if not hasattr(o, "bound_box"):
            continue
        for corner in o.bound_box:
            w = o.matrix_world @ __import__("mathutils").Vector(corner)
            for k in range(3):
                lo[k] = min(lo[k], w[k])
                hi[k] = max(hi[k], w[k])
    return lo, hi


def build_scene(bpy, spec, root, bay_x, log=print):
    """The scene, from the spec and nothing else. Returns a report dict."""
    # A clean file. --factory-startup already gives one, but a recipe that
    # assumes the startup scene is empty breaks the day somebody runs it
    # without the flag.
    bpy.ops.wm.read_factory_settings(use_empty=True)

    drawn, skipped, refused = select_window(spec)
    found, missing = mesh_requests(drawn, root)
    mat = _clay_material(bpy)

    built = {"box": 0, "cyl": 0, "decal": 0, "mesh": 0}
    mesh_failed = []
    templates = {}
    for aid, path in sorted(found.items()):
        objs = _import_glb(bpy, path, aid)
        if not objs:
            mesh_failed.append(aid + ":imported-nothing")
            continue
        templates[aid] = objs
        for o in objs:
            o.hide_render = True
            o.hide_viewport = True

    for p in drawn:
        shape = p.get("shape")
        if shape == "box":
            _build_box(bpy, p, mat); built["box"] += 1
        elif shape == "cyl":
            _build_cyl(bpy, p, mat); built["cyl"] += 1
        elif shape == "decal":
            _build_decal(bpy, p, mat); built["decal"] += 1
        elif shape == "mesh":
            aid = asset_id(p.get("asset", ""))
            src = templates.get(aid)
            if not src:
                mesh_failed.append(p.get("name", "unnamed") + ":no-template/" + aid)
                continue
            copies = []
            for o in src:
                c = o.copy()
                if o.data is not None:
                    c.data = o.data
                c.hide_render = False
                c.hide_viewport = False
                bpy.context.collection.objects.link(c)
                copies.append(c)
            # NEVER SCALED. Stand the imported bounds centre on the row's
            # centre, which is the piece file's own mesh_placement rule.
            lo, hi = _world_bounds(copies)
            centre = [(lo[k] + hi[k]) / 2.0 for k in range(3)]
            want = to_blender(p["x_m"], p["y_m"], p["z_m"])
            for c in copies:
                c.location = (c.location[0] + want[0] - centre[0],
                              c.location[1] + want[1] - centre[1],
                              c.location[2] + want[2] - centre[2])
                if c.data is not None and hasattr(c.data, "materials"):
                    c.data.materials.clear()
                    c.data.materials.append(mat)
            built["mesh"] += 1

    log("build: box=%d cyl=%d decal=%d mesh=%d glbTemplates=%d/of=%d "
        "meshFailed=%s refusedPieces=%s bomLinesNotDrawn=%s"
        % (built["box"], built["cyl"], built["decal"], built["mesh"],
           len(templates), len(found) + len(missing),
           tally(mesh_failed), tally(["%s:%s" % r for r in refused]),
           tally(skipped)))
    return {"built": built, "meshFailed": mesh_failed, "refused": refused,
            "skippedBom": skipped, "missingGlb": missing}


def light_scene(bpy, spec, condition, log=print):
    """Sun from the file's own elevation and azimuth, sky from the row."""
    sun = spec.get("sun", {})
    elev = float(sun.get("elevation_deg", 36.0))
    azim = float(sun.get("azimuth_deg", 205.0))
    sky_i = float(condition.get("sky_intensity", 1.0))
    sun_i = float(condition.get("sun_intensity", 3.0))

    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg is not None:
        # A grey dome. NOT the HDRI the row names: nothing is fetched here.
        bg.inputs[0].default_value = (0.62, 0.64, 0.68, 1.0)
        bg.inputs[1].default_value = sky_i
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)
    light = bpy.data.lights.new("sun", type="SUN")
    # Energy in W/m2 for a Blender sun. The condition rows are engine
    # intensities on another scale, so they set the RATIO between the two
    # conditions and not an absolute: 3 and 30 become 1.0 and 10.0 times a
    # base that was chosen to expose the clay, and the plan says the rows are
    # a ratio rather than a calibration.
    light.energy = 1.0 * (sun_i / 3.0)
    # Overcast means a big soft source. 5 degrees of angular diameter is
    # roughly ten suns wide, which is what kills the hard edge the diagnostic
    # cell wants to keep, so the diagnostic gets the real 0.526 degrees.
    light.angle = math.radians(5.0 if sun_i <= 3.0 else 0.526)
    obj = bpy.data.objects.new("sun", light)
    bpy.context.collection.objects.link(obj)
    # A sun at elevation E and azimuth A shines FROM that bearing, so the
    # lamp's -Z must point along the inbound direction.
    yaw_to_sun = azim
    obj.rotation_euler = blender_camera_euler(yaw_to_sun, elev)
    log("light: condition=%s sunElevationDeg=%.1f sunAzimuthDeg=%.1f "
        "sunEnergyWm2=%.3f sunAngleDeg=%.3f skyStrength=%.3f "
        "hdri=NOT-LOADED/%s intensityStat=a-ratio-between-the-two-rows-not-a-calibration"
        % (condition.get("id"), elev, azim, light.energy,
           math.degrees(light.angle), sky_i,
           str(condition.get("hdri", "none")).replace(" ", "~")))
    return obj


def place_camera(bpy, shot):
    for o in [o for o in bpy.data.objects if o.type == "CAMERA"]:
        bpy.data.objects.remove(o, do_unlink=True)
    cam = bpy.data.cameras.new("cam_" + shot["id"])
    cam.sensor_fit = "VERTICAL"
    cam.lens_unit = "FOV"
    cam.angle_y = math.radians(shot["fov"])
    obj = bpy.data.objects.new("cam_" + shot["id"], cam)
    obj.location = to_blender(*shot["eye"])
    obj.rotation_euler = blender_camera_euler(shot["yaw"], shot["pitch"])
    bpy.context.collection.objects.link(obj)
    bpy.context.scene.camera = obj
    return obj


def render_all(bpy, spec, root, out_dir, bay_x, log=print):
    """Every shot in every condition, reporting the files that exist after."""
    report = build_scene(bpy, spec, root, bay_x, log=log)
    shots = plan_shots(spec, bay_x)
    conds, cond_missing = plan_conditions(spec)
    if cond_missing:
        log("recipe refused: status=NO-CONDITION-ROW missing=%s nothing measured"
            % tally(cond_missing))
        return 1
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = RENDER_W
    scene.render.resolution_y = RENDER_H
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    if hasattr(scene, "cycles"):
        scene.cycles.samples = SAMPLES
        scene.cycles.use_denoising = True

    written, failed = [], []
    os.makedirs(out_dir, exist_ok=True)
    for cond in conds:
        light_scene(bpy, spec, cond, log=log)
        for shot in shots:
            place_camera(bpy, shot)
            name = "%s_%s_%s.png" % (RECIPE, shot["id"], cond.get("id"))
            path = os.path.join(out_dir, name)
            scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
            # THE EFFECT, NOT THE EXIT CODE. A render call that returns
            # FINISHED and writes nothing has happened on this project before.
            if os.path.exists(path) and os.path.getsize(path) > 0:
                written.append("%s:%dB" % (name, os.path.getsize(path)))
            else:
                failed.append(name)
    log("render: pngsWritten=%d/of=%d-planned pngsMissing=%s first=%s"
        % (len(written), len(shots) * len(conds), tally(failed),
           (written[0] if written else "none")))
    del report
    return 0 if written and not failed else 1


# ---------------------------------------------------------------------------
# ENTRY POINT AND SELFTEST
# ---------------------------------------------------------------------------

def parse_args(argv):
    args = list(argv[1:])
    out_dir, root, dry, self_test = None, None, False, False
    bay_x = 6.0
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--out" and i + 1 < len(args):
            out_dir = args[i + 1]; i += 2; continue
        if a == "--root" and i + 1 < len(args):
            root = args[i + 1]; i += 2; continue
        if a == "--bay-x" and i + 1 < len(args):
            bay_x = float(args[i + 1]); i += 2; continue
        if a == "--dry-run":
            dry = True; i += 1; continue
        if a == "--selftest":
            self_test = True; i += 1; continue
        i += 1
    return out_dir, root, dry, self_test, bay_x


def selftest(out=print):
    """ACCEPTING CASE FIRST, on the live committed street.

    The instruments rule: for a tool that reads the project itself, the live
    codebase is the accepting fixture and the rejecting fixture is synthetic.
    So doing the work this recipe prompts can never break the recipe, and the
    refusals are driven with planted data rather than by damaging the street.
    """
    checks = [0, 0]

    def check(name, ok, detail=""):
        checks[0] += 1
        if not ok:
            checks[1] += 1
            out("  FAIL: %s %s" % (name, detail))
        else:
            out("  ok - %s" % name)

    root = repo_root()
    check("accept/the-repository-root-is-found-by-the-spec-under-foot", root is not None,
          "nothing measured: %s not found above %s" % (SPEC_REL, __file__))
    if root is None:
        out("PASS: %d of %d check(s) failed" % (checks[1], checks[0]))
        return 1
    spec = load_spec(root)

    # THE AXIS MAP, ON A CASE WHOSE ANSWER IS NOT A MATTER OF OPINION.
    check("accept/the-axis-map-sends-project-up-to-blender-up",
          to_blender(1.0, 2.0, 3.0) == (1.0, -3.0, 2.0), str(to_blender(1.0, 2.0, 3.0)))
    check("accept/the-axis-map-preserves-handedness",
          # det of [[1,0,0],[0,0,-1],[0,1,0]] is +1, asserted by image of a
          # right-handed triple staying right-handed
          to_blender(1, 0, 0) == (1, 0, 0) and to_blender(0, 1, 0) == (0, 0, 1)
          and to_blender(0, 0, 1) == (0, -1, 0))
    check("accept/a-box-keeps-its-height-on-blenders-up-axis",
          box_dims(6.0, 0.55, 0.12) == (6.0, 0.12, 0.55), str(box_dims(6.0, 0.55, 0.12)))

    # AIM ARITHMETIC. Two cases whose answers are known by inspection.
    yaw, pitch = aim_at((0, 0, 0), (1, 0, 0))
    check("accept/looking-along-+x-is-yaw-0-pitch-0", abs(yaw) < 1e-9 and abs(pitch) < 1e-9,
          "%.6f/%.6f" % (yaw, pitch))
    yaw, pitch = aim_at((0, 0, 0), (0, 1, 0))
    check("accept/looking-straight-up-is-pitch-90", abs(pitch - 90.0) < 1e-9, "%.6f" % pitch)
    yaw, pitch = aim_at((0, 0, 0), (1, 1, 0))
    check("accept/a-45-degree-rise-reads-45-degrees", abs(pitch - 45.0) < 1e-9, "%.6f" % pitch)
    yaw, pitch = aim_at((0, 0, 0), (0, 0, 1))
    check("accept/looking-toward-+z-is-yaw-90", abs(yaw - 90.0) < 1e-9, "%.6f" % yaw)

    # THE WINDOW, ON THE LIVE STREET.
    drawn, skipped, refused = select_window(spec)
    check("accept/the-window-draws-something-off-the-committed-street", len(drawn) > 0,
          "%d of %d" % (len(drawn), len(spec.get("pieces", []))))
    check("accept/no-piece-in-the-window-is-refused", len(refused) == 0,
          "%d of %d refused: %s" % (len(refused), len(drawn) + len(refused),
                                    tally(["%s:%s" % r for r in refused])))
    c15 = [p for p in drawn if p.get("bom") == "C15_fascia_cornice_console"]
    check("accept/the-package-under-review-is-in-the-window", len(c15) == 17,
          "%d C15 pieces in the window" % len(c15))
    check("accept/every-C15-piece-is-a-mesh-row-and-not-a-box",
          all(p.get("shape") == "mesh" for p in c15),
          tally([p["name"] for p in c15 if p.get("shape") != "mesh"]))

    found, missing = mesh_requests(drawn, root)
    check("accept/every-mesh-asset-the-window-asks-for-has-a-glb-on-disk",
          not missing, "%d of %d missing: %s"
          % (len(missing), len(found) + len(missing), tally(missing)))
    check("accept/the-two-authored-mouldings-are-among-them",
          "fascia_cornice_01" in found and "fascia_console_01" in found,
          tally(sorted(found)))

    # THE SHOTS AND THE CONDITIONS, OFF THE LIVE FILE.
    shots = plan_shots(spec, 6.0)
    check("accept/three-views-are-planned", len(shots) == 3,
          tally([s["id"] for s in shots]))
    check("accept/the-first-view-is-the-files-own-camera-and-says-so",
          shots and shots[0]["from"].startswith("the-spec-files-own-cam_A"),
          shots[0]["from"] if shots else "none")
    check("accept/the-close-view-names-the-console-it-is-aimed-at",
          any(s["id"] == "console_scroll" and s.get("subject", "").startswith("prop_fascia_console")
              for s in shots),
          tally([s.get("subject", "none") for s in shots]))
    check("accept/the-soffit-view-looks-UP-at-the-cornice",
          any(s["id"] == "drip_soffit" and s["pitch"] > 0 for s in shots),
          tally(["%s:%.2f" % (s["id"], s["pitch"]) for s in shots]))
    conds, cond_missing = plan_conditions(spec)
    check("accept/both-named-condition-rows-are-still-in-the-spec-file",
          len(conds) == 2 and not cond_missing, tally(cond_missing))
    check("accept/the-shipping-condition-is-the-softer-light-of-the-two",
          conds and float(conds[0]["sun_intensity"]) < float(conds[1]["sun_intensity"]),
          tally(["%s:%s" % (c["id"], c["sun_intensity"]) for c in conds]))

    # THE PLAN ITSELF: no spaces in a value, every zero with a denominator.
    lines = plan_lines(spec, root, 6.0)
    check("accept/the-plan-printed-something", len(lines) > 8, str(len(lines)))
    bad = []
    for ln in lines:
        for token in ln.split(" "):
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            if " " in value:
                bad.append(key)
    check("accept/no-key=value-in-the-plan-carries-a-space-in-its-value",
          not bad, tally(bad))
    check("accept/the-plan-says-what-it-is-NOT-doing",
          any("absentOnPurpose=" in ln for ln in lines))
    check("accept/the-plan-names-the-frames-it-would-write-with-a-denominator",
          any("framesPlanned=6" in ln for ln in lines),
          tally([ln for ln in lines if "framesPlanned" in ln]))

    # REJECTING FIXTURES, ALL SYNTHETIC. A repository with a broken street in
    # it is not a repository anybody wants.
    planted = {"pieces": [dict(spec["pieces"][0])], "conditions": [], "cameras": [], "sun": {}}
    planted["pieces"][0]["bom"] = "C15_fascia_cornice_console"
    planted["pieces"][0]["pitch_deg"] = 3.0
    planted["pieces"][0]["yaw_deg"] = 90.0
    planted["pieces"][0]["edge"] = "east_footway"
    d2, s2, r2 = select_window(planted)
    check("reject/a-piece-with-two-live-rotations-is-refused-by-name-not-drawn",
          len(d2) == 0 and len(r2) == 1 and "two-live-rotations" in r2[0][1],
          "drawn=%d refused=%s" % (len(d2), tally(["%s:%s" % r for r in r2])))
    planted2 = {"pieces": [dict(spec["pieces"][0])]}
    planted2["pieces"][0]["bom"] = "C15_fascia_cornice_console"
    planted2["pieces"][0]["shape"] = "blancmange"
    planted2["pieces"][0]["edge"] = "east_footway"
    planted2["pieces"][0]["pitch_deg"] = 0.0
    planted2["pieces"][0]["roll_deg"] = 0.0
    planted2["pieces"][0]["yaw_deg"] = 0.0
    d3, s3, r3 = select_window(planted2)
    check("reject/an-unknown-shape-is-refused-by-name-not-approximated",
          len(d3) == 0 and len(r3) == 1 and "unknown-shape" in r3[0][1],
          "drawn=%d refused=%s" % (len(d3), tally(["%s:%s" % r for r in r3])))
    planted3 = {"pieces": [dict(p) for p in spec["pieces"][:4]], "conditions": []}
    for p in planted3["pieces"]:
        p["bom"] = "C15_fascia_cornice_console"
        p["shape"] = "mesh"
        p["asset"] = "a_moulding_that_was_never_authored"
        p["edge"] = "east_footway"
        p["pitch_deg"] = p["roll_deg"] = p["yaw_deg"] = 0.0
    d4, _, _ = select_window(planted3)
    f4, m4 = mesh_requests(d4, root)
    check("reject/a-mesh-row-whose-glb-is-absent-is-NAMED-and-never-boxed",
          m4 == ["a_moulding_that_was_never_authored"] and not f4, tally(m4))
    c5, miss5 = plan_conditions({"conditions": []})
    check("reject/a-missing-condition-row-comes-back-as-a-refusal-with-its-name",
          not c5 and list(miss5) == list(CONDITION_IDS), tally(miss5))
    check("reject/an-empty-list-prints-none-rather-than-nothing", tally([]) == "none")
    check("reject/a-capped-list-announces-how-many-it-hid",
          tally(list("abcdefghij"), cap=3) == "a;b;c;(+7~more~not~shown)",
          tally(list("abcdefghij"), cap=3))

    out("%s selftest: %d check(s), %d failure(s)" % (RECIPE, checks[0], checks[1]))
    out("PASS: %d of %d check(s) failed" % (checks[1], checks[0]))
    return 1 if checks[1] else 0


def main(argv):
    out_dir, root, dry, self_test, bay_x = parse_args(argv)
    if self_test:
        return selftest()
    root = root or repo_root()
    if root is None:
        print("recipe refused: status=NO-REPO-ROOT recipe=%s reason=%s-not-found-above-%s "
              "nothing measured" % (RECIPE, SPEC_REL, os.path.abspath(__file__)))
        return 1
    spec = load_spec(root)
    for line in plan_lines(spec, root, bay_x):
        print(line)
    if dry:
        print("recipe done: status=PLAN-ONLY recipe=%s pngsWritten=0/0-asked-in-plan-mode" % RECIPE)
        return 0
    if not out_dir:
        print("recipe refused: status=NO-OUT-DIR recipe=%s "
              "reason=a-render-with-nowhere-to-write-is-a-render-nobody-can-look-at "
              "nothing measured" % RECIPE)
        return 1
    try:
        import bpy  # noqa: F401  (present only inside Blender)
    except ImportError:
        print("recipe refused: status=NO-BPY recipe=%s "
              "reason=this-file-must-be-run-by-blender---python-not-by-python "
              "nothing measured" % RECIPE)
        return 1
    return render_all(bpy, spec, root, out_dir, bay_x)


# THE GUARD THE RUNNER RELIES ON. run-recipe.py imports this file to reach its
# pure layer, and an import that rendered anything would make `--plan` a render.
if __name__ == "__main__":
    sys.exit(main(sys.argv))
