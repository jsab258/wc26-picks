#!/usr/bin/env python3
"""Five stills walking north up Quay Street, past the shopfront run that holds Mickey's.

    blender --background --factory-startup --python tools/art-recipes/quay-street-mickeys-walk.py -- --out DIR

THE CONTRACT WITH THE WORKFLOW, and it is copied from the step that runs this
file rather than remembered. `.github/workflows/ledger-art-blender-preview.yml`
invokes exactly the line above, counts the PNGs in DIR before and after, and
fails the run when the count did not rise. So this file has one obligation
above every other: write PNGs into `--out` or exit non-zero saying why. An
empty success is the one outcome the art branch cannot read.

WHAT IT BUILDS, AND WHERE EVERY NUMBER COMES FROM. One file:
`production/specs/vignette-pieces.json`, the 593-piece flat list that
Ledger.Core generates and that BOTH engines build the street from. Nothing here
is re-derived from the scene spec and nothing is typed by hand: the eye height,
the ground under the walker's feet, the lens, the pitch, the sun angles, the
shopfront positions and every box, cylinder, mesh and decal are read out of that
file. A preview that re-derived its own street would be a third opinion about a
street two engines already agree on.

WHAT IT IS FOR. An artist flipping through five stills should read a walk down
a lane, not five unrelated angles: same eye height, same lens, same heading,
one shop unit of travel per frame. It is a massing and framing reference to
paint over, NOT a look target. Every surface is a neutral grey except the three
colours the piece file itself states, and that is deliberate: this file makes no
colour decision, so nothing here can quietly become art direction.

WHICH BAY IS MICKEY'S IS NOT DECIDED HERE, and it is not decided anywhere yet.
`ledger-v2/respec/decision-register/D15-mickeys-on-the-built-street.md` settles
the STREET and says in as many words that the bay is a small authored choice
still open. So `--bay` is a parameter, its default is read from a hint already
in the piece file, the run prints which bay it used, and the five cameras cover
the whole six-bay run rather than fixating on one bay. The piece file carries
TWO hints and they disagree: the fascia lettering `decal_00_fascia_mickeys`
sits on bay 0, while the lit interior card at bay 2 is a BAR BACK behind a
fascia that reads as a pawnbroker. The default follows the lettering, because
lettering names a shop; the conflict is printed on the done line rather than
resolved by this file.

THIS FILE HAS NEVER BEEN RUN. Blender is not installed in the container it was
written in (checked, not assumed: no `blender` on PATH, no `bpy` importable), so
every line below that touches `bpy` ships UNRUN. What that costs is bounded on
purpose: the geometry, the camera plan, the bay coverage arithmetic and every
printed string live in the pure layer at the top of this file with no `bpy` in
them, `tools/art-recipes/run-recipe.py --selftest` exercises that layer against
the real piece file, and `--plan` prints the whole plan without Blender. The
uncovered part is the Blender API calls and the pixels.
"""
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
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PIECES_REL = "production/specs/vignette-pieces.json"
MESH_DIR_REL = "ledger/Assets/Props/base-mesh"
MESH_SUFFIX = ".glb"

#: Five, because Jafar asked for five. It is a parameter so the count can be
#: argued with, and it is printed with its denominator either way.
DEFAULT_CAMERAS = 5

#: HOW THE WALK IS AIMED, and the two numbers are the whole composition.
#:
#: LOOK_AHEAD_BAYS is the heading: each camera aims at the shopfront glazing two
#: bay widths ahead of it, which at this street's 8.985 m across and 6.0 m bay
#: pitch is a heading of 36.8 degrees off the street line. That is the angle a
#: person walking a lane actually holds: far enough round to face the frontage,
#: not so far round that the street stops running to a vanishing point. The
#: constraint it has to satisfy is printed every run as
#: `vanishingPointMarginDeg`: with a 60 degree vertical field at 16:9 the
#: horizontal half field is 45.75 degrees, so a heading of 36.8 leaves the
#: along-the-street vanishing point 8.9 degrees inside the left edge of frame.
#: Take the heading past about 40 degrees and the lane cue falls out of the
#: picture, which is when five stills stop reading as a walk and start reading
#: as five shop portraits.
#:
#: STEP is one bay pitch, read from the glazing spacing rather than typed: the
#: walker advances exactly one shop unit per frame, so the same rhythm slides
#: through the five stills. That repetition is the strongest single cue that
#: the frames are one walk.
#:
#: WHERE THE WALK STARTS is derived, not chosen: station 0 is the point at
#: which the FIRST bay's glazing centre sits exactly on the right-hand edge of
#: frame, so no bay is ever behind the walk, and the other four follow at one
#: pitch each. Measured over the 5 x 6 camera-by-bay grid this puts every one
#: of the six bays in at least one frame with a best look of 0.159 of the frame
#: width, except the last at 0.128. The alternatives were printed before this
#: one was chosen: starting where the last camera aims at the last bay leaves
#: the far end of the run at 0.070, and centring the stations on the run drops
#: bay 0 out of the walk entirely at 0.000.
LOOK_AHEAD_BAYS = 2.0

#: A bay counts as LEGIBLE in a frame when its glazing spans at least this
#: fraction of the frame width. It is a definition and a reported statistic,
#: not a gate: nothing fails on it. The number comes from the printed series
#: above (0.159 five times and 0.128 once, against 0.017 for a bay six units
#: away at a grazing angle), and 0.10 is the elbow: a 6 m shopfront filling a
#: tenth of the picture is one an artist can read a fascia off, and below it
#: the bay is scenery. Change the lens or the street width and the series moves
#: with it, which is why the per-bay series prints on every run.
LEGIBLE_SPAN_FRACTION = 0.10

#: 16:9 at 1600x900. The lens is NOT chosen here: the vertical field comes from
#: the piece file's own cameras, and the horizontal follows from this aspect.
DEFAULT_RES = (1600, 900)

#: Cycles at 64 samples with denoising. CPU Cycles is the engine that is certain
#: to work headless on a machine nobody has logged into; EEVEE needs a GL
#: context and its identifier changed name between Blender 4.1 and 4.2, so it is
#: opt-in behind --engine and prints which identifier it found.
DEFAULT_SAMPLES = 64

#: A decal is a zero-thickness quad, so it is lifted off the surface it sits on
#: by this much along its own normal. 6 mm: thick enough that no depth buffer
#: has to choose between the decal and the brick, thin enough to be invisible at
#: eye height 9 m away.
DECAL_LIFT_M = 0.006

#: PREVIEW GREYS, gamma sRGB, converted to linear on the way into Blender.
#: NONE OF THESE IS A COLOUR DECISION and none may be quoted as one. The
#: vignette spec states three colours and only three (the sodium lantern, the
#: warm window practical, the worn municipal yellow of the double lines); it
#: states no brick red, no slate, no asphalt. Rather than invent thirteen, this
#: file renders a clay model: neutral greys separated by value alone, which is
#: what an artist wants under a paint-over anyway. The one colour taken from
#: the file is paint_yellow, because the file has it.
SURFACE_GREY = {
    "asphalt": (0.22, 0.22, 0.23, 0.85),
    "sidewalk": (0.38, 0.38, 0.38, 0.85),
    "kerb": (0.44, 0.44, 0.44, 0.80),
    "concrete": (0.46, 0.46, 0.46, 0.80),
    "brick_red": (0.36, 0.35, 0.34, 0.85),
    "brick_grey": (0.30, 0.30, 0.30, 0.85),
    "roof": (0.26, 0.26, 0.27, 0.75),
    "plaster": (0.55, 0.55, 0.54, 0.80),
    "wood": (0.33, 0.32, 0.31, 0.70),
    "metal": (0.32, 0.32, 0.33, 0.35),
    "glass": (0.10, 0.11, 0.12, 0.08),
    "window": (0.12, 0.13, 0.14, 0.10),
    "interior": (0.18, 0.18, 0.18, 0.85),
    "card": (0.50, 0.50, 0.50, 0.80),
    "multiply": (0.20, 0.20, 0.20, 0.85),
    "paint_yellow": (0.78, 0.66, 0.18, 0.70),  # the file's own, see paint.double_yellow
}
#: Which of the greys above are the file's own colours rather than this
#: recipe's. Printed as a denominator so the ratio cannot rot unnoticed.
SURFACES_FROM_SPEC = ("paint_yellow",)

#: Overcast, per the piece file's `overcast_day` condition. The sun ANGLES are
#: the file's (elevation 36, azimuth 205); the three numbers below are this
#: recipe's and are the first values of a series that has never been printed,
#: which is all rule 2 allows them to be called until a frame exists to tune
#: them from. A 12 degree sun disc is the overcast diffusion, and the grey sky
#: does most of the lighting, which is what an overcast British day is.
OVERCAST_SUN_ANGLE_DEG = 12.0
OVERCAST_SUN_ENERGY = 2.2
OVERCAST_SKY = (0.62, 0.65, 0.68)


# ---------------------------------------------------------------------------
# THE PURE LAYER. No bpy below this line and none above the Blender layer
# marked further down, because .claude/rules/instruments.md puts the tally, the
# arithmetic and the strings where the tests run: in a project whose renderer
# does not exist in this container, a formatter written beside the renderer
# ships unrun, and an unrun formatter printing a plausible string is the
# silent-instrument failure.
# ---------------------------------------------------------------------------


def srgb_to_linear(c):
    """One gamma sRGB channel to linear, the exact piecewise curve.

    Blender node colours are linear. Every colour in this file is written in
    gamma sRGB because that is the space the piece file states its colours in,
    so there is one conversion and it is here where a test can see it.
    """
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def load_pieces(root):
    """(data, error). The one file this recipe reads."""
    path = os.path.join(root, PIECES_REL)
    if not os.path.exists(path):
        return None, "no-piece-file-at/" + PIECES_REL
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        return None, "unreadable-piece-file/" + type(exc).__name__
    if not data.get("pieces"):
        return None, "piece-file-has-no-pieces-array"
    return data, ""


def glazing_run(pieces):
    """The shopfront run, measured off the glazing rather than assumed.

    The six panes named in D15 as `east_parade_glass0` to `glass5`. Their
    centres, the bay pitch as the spacing BETWEEN them, and the frontage plane
    they all sit in. Everything the walk is aimed with comes from here.
    """
    glass = sorted([p for p in pieces
                    if p.get("name", "").startswith("east_parade_glass")],
                   key=lambda p: p["x_m"])
    bays = [{"index": i, "name": p["name"], "x_m": p["x_m"], "z_m": p["z_m"],
             "half_width_m": p["sx_m"] / 2.0}
            for i, p in enumerate(glass)]
    pitches = [round(bays[i + 1]["x_m"] - bays[i]["x_m"], 6)
               for i in range(len(bays) - 1)]
    return {
        "bays": bays,
        "count": len(bays),
        # The pitch is the SMALLEST spacing, not the mean: a mean over a run
        # with one wide unit would put the stations out of step with every bay
        # instead of one.
        "pitch_m": min(pitches) if pitches else 0.0,
        "pitch_series": pitches,
        "plane_z_m": bays[0]["z_m"] if bays else 0.0,
        "run_start_m": min(b["x_m"] - b["half_width_m"] for b in bays) if bays else 0.0,
        "run_end_m": max(b["x_m"] + b["half_width_m"] for b in bays) if bays else 0.0,
    }


def bay_of_x(run, x):
    """Which bay an x sits in: nearest glazing centre.

    Nearest centre rather than an arithmetic block index, so this needs only
    the piece file and cannot disagree with the run it just measured.
    """
    if not run["bays"]:
        return -1
    return min(run["bays"], key=lambda b: abs(b["x_m"] - x))["index"]


def mickeys_hints(pieces, run):
    """Where the piece file already says Mickey's is, and where it disagrees.

    TWO HINTS, and they do not agree. `decal_00_fascia_mickeys` is the fascia
    lettering, at the centre of one bay. The lit interior cards name what is
    behind the glass, and one of them is a bar back, in a different bay. The
    bay is an open authored choice per D15, so this returns both and decides
    nothing: the default follows the lettering because lettering names a shop,
    and the disagreement is printed.
    """
    lettering = None
    bar = None
    for p in pieces:
        name = p.get("name", "")
        if p.get("bom") == "C6_fascia_lettering" and "mickeys" in name:
            lettering = (name, bay_of_x(run, p["x_m"]))
        if p.get("bom") == "C11_lit_interior_card" and "bar" in name:
            bar = (name, bay_of_x(run, p["x_m"]))
    return {"lettering": lettering, "bar_back": bar,
            "default_bay": lettering[1] if lettering else 0,
            "default_from": ("fascia-decal/" + lettering[0]) if lettering
                            else "no-hint-in-the-file/fell-back-to-bay0"}


def horizontal_half_fov_deg(fov_vertical_deg, aspect):
    """Half the horizontal field, from the vertical field and the aspect.

    The camera is set up VERTICAL-fit so the piece file's own
    `fov_vertical_deg` is honoured exactly and the horizontal follows the
    resolution, which is the only way a change of aspect cannot silently
    change the lens the two engines agreed on.
    """
    return math.degrees(math.atan(
        math.tan(math.radians(fov_vertical_deg / 2.0)) * aspect))


def footway_top_y(pieces, edge, z):
    """The top surface of a ground slab at a given cross-street position.

    THIS IS THE INSTRUMENT CHECK, not the source. The camera height uses the
    piece file's own published `ground_y_m`; this recomputes the same number
    from the slab geometry so the two can be compared and a disagreement
    printed. The slab is a box of full height sy_m rotated about the street
    axis by pitch_deg, where positive pitch tips the +z end down, so a point
    u metres to +z of the centre sits at centre + sy/2 cos(p) - u sin(p).
    """
    slab = next((p for p in pieces if p.get("edge") == edge
                 and p.get("bom") == "A0_ground_planes"), None)
    if slab is None:
        return None
    p = math.radians(slab["pitch_deg"])
    return (slab["y_m"] + (slab["sy_m"] / 2.0) * math.cos(p)
            - (z - slab["z_m"]) * math.sin(p))


def walk_cameras(data, run, n_cameras, aspect):
    """The five stations, derived from the street rather than typed.

    THE SIDE. The walk is on the WEST footway, because the shopfront run is on
    the east side and a frontage is read from across the street, not from the
    pavement it stands on. Its cross-street position and the ground under it
    are cam_B's, the piece file's own west-footway camera, so this recipe
    stands where the scene already says a person stands.

    THE HEIGHT. eye_height_above_ground_m from the file (1.6) added to the
    file's ground_y_m for that footway (0.071875), because the file is explicit
    that eye height is measured from the pavement and not from the road crown.
    Nothing here types a height.

    THE LENS AND THE PITCH are cam_A's: cam_A is the along-the-street camera
    and this is an along-the-street walk, so its 60 degree vertical field and
    its 4.0 degrees of down pitch are inherited rather than re-derived. That
    pitch is the one the file derives to put the horizon just above the middle
    of frame.
    """
    cams = {c["id"]: c for c in data.get("cameras", [])}
    west = cams.get("cam_B")
    along = cams.get("cam_A")
    if not west or not along:
        return [], "piece-file-has-no-cam_A-and-cam_B-to-stand-in-for"
    walk_z = west["z_m"]
    ground_y = west["ground_y_m"]
    eye_y = ground_y + west["eye_height_above_ground_m"]
    fov_v = along["fov_vertical_deg"]
    pitch_down = along["pitch_deg"]
    across = run["plane_z_m"] - walk_z
    pitch_m = run["pitch_m"]
    if across <= 0 or pitch_m <= 0:
        return [], "degenerate-street/across%.3f-pitch%.3f" % (across, pitch_m)

    yaw = math.degrees(math.atan2(across, LOOK_AHEAD_BAYS * pitch_m))
    half_h = horizontal_half_fov_deg(fov_v, aspect)
    # Station 0: the first bay's glazing centre lands exactly on the right edge
    # of frame, so the walk starts at the moment the run enters the picture.
    edge_bearing = yaw + half_h
    lead = across / math.tan(math.radians(edge_bearing)) if edge_bearing < 90 else 0.0
    x0 = run["bays"][0]["x_m"] - lead
    out = []
    for i in range(n_cameras):
        out.append({
            "index": i,
            "id": "walk%02d" % (i + 1),
            "x_m": round(x0 + i * pitch_m, 6),
            "y_m": round(eye_y, 6),
            "z_m": walk_z,
            "yaw_deg": round(yaw, 4),
            "pitch_down_deg": pitch_down,
            "fov_vertical_deg": fov_v,
        })
    return out, ""


def frame_u(bearing_rel_deg, half_h_deg):
    """Where a horizontal bearing lands across the frame: -1 left, +1 right.

    Pinhole, in tangent space, which is what a rectilinear camera does. Returns
    None for anything at or behind 90 degrees off the axis, which has no
    rectilinear image at all.
    """
    if not -89.0 < bearing_rel_deg < 89.0:
        return None
    return (math.tan(math.radians(bearing_rel_deg))
            / math.tan(math.radians(half_h_deg)))


def bay_coverage(cameras, run, aspect):
    """The placement metric, in the two halves instruments.md asks for.

    HALF ONE, the distance to the datum: how much of the frame width each bay's
    glazing spans, which is the number that decides whether an artist can read
    it. HALF TWO, whether the datum is under the footprint at all: whether the
    bay is in frame rather than behind the walker or off the edge. The
    breakdown is PER BAY, the axis the walk actually varies along, and never
    per camera: a per-camera average would report five healthy frames while one
    end of the run sat outside all of them.

    `best_span` is a BEST-OF-FIVE, not a mean: an artist reads a bay from its
    best frame, and a mean would punish a bay for being distant in the four
    frames where it is scenery.
    """
    rows = []
    for bay in run["bays"]:
        per_cam = []
        for cam in cameras:
            us = []
            for x in (bay["x_m"] - bay["half_width_m"],
                      bay["x_m"] + bay["half_width_m"]):
                rel = math.degrees(math.atan2(bay["z_m"] - cam["z_m"],
                                              x - cam["x_m"])) - cam["yaw_deg"]
                u = frame_u(rel, horizontal_half_fov_deg(
                    cam["fov_vertical_deg"], aspect))
                if u is None:
                    us = []
                    break
                us.append(u)
            if not us:
                per_cam.append(0.0)  # behind the walker
                continue
            lo, hi = sorted(us)
            visible = max(0.0, min(hi, 1.0) - max(lo, -1.0)) / 2.0
            per_cam.append(round(visible, 4))
        best = max(per_cam) if per_cam else 0.0
        rows.append({
            "bay": bay["index"],
            "glazing": bay["name"],
            "per_cam": per_cam,
            "best_span": best,
            "best_cam": (per_cam.index(best) + 1) if per_cam and best > 0 else 0,
            "cams_seeing": sum(1 for v in per_cam if v > 0.0),
        })
    return rows


def sun_direction(elevation_deg, azimuth_deg):
    """Unit vector the sunlight TRAVELS along, in Blender axes.

    The piece file states the sun as an elevation and a compass azimuth in the
    scene frame, where a bearing is measured from +x (up the street, north)
    turning toward +z (east). Azimuth 205 is therefore south-south-west, which
    is the direction the sun is IN, so the light travels the other way. That is
    what puts the raking light on the east parade's west-facing frontage.
    """
    el = math.radians(elevation_deg)
    az = math.radians(azimuth_deg)
    to_sun = (math.cos(el) * math.cos(az),  # scene x
              math.sin(el),                 # scene y, up
              math.cos(el) * math.sin(az))  # scene z, east
    return to_blender_xyz(-to_sun[0], -to_sun[1], -to_sun[2])


def to_blender_xyz(x_m, y_m, z_m):
    """Scene axes to Blender axes: (along, up, across) to (X, Y, Z).

    The piece file's frame is y-up and engine-neutral. Blender is z-up. The
    mapping swaps the two, which is also what turns the file's left-handed
    frame into Blender's right-handed one without mirroring anything: Blender
    X is along the street, Blender Y is across it with +Y east, Blender Z is
    up.
    """
    return (x_m, z_m, y_m)


def to_blender_scale(sx_m, sy_m, sz_m):
    """A full size in scene axes to a Blender scale on a unit primitive."""
    return (sx_m, sz_m, sy_m)


def to_blender_euler(pitch_deg, yaw_deg, roll_deg):
    """Piece rotation to a Blender XYZ euler, in radians.

    Read against the file's own definitions. Yaw turns +x toward +z, which in
    Blender axes turns +X toward +Y, which is a positive rotation about Blender
    Z. Positive pitch tips the +z end DOWN, and a positive rotation about
    Blender X lifts +Y, so pitch enters negated. Roll about +z lays a cylinder
    axis along the street, and a positive rotation about Blender Y takes
    Blender Z (up) toward Blender X (along the street), so roll enters as is.

    ORDER DOES NOT MATTER HERE and that is a measured fact rather than a hope:
    the piece file publishes `counts.multi_rotation = 0`, so no piece in the
    scene has more than one non-zero angle. `main` checks that count before
    building and refuses if it ever stops being true.
    """
    return (math.radians(-pitch_deg), math.radians(roll_deg),
            math.radians(yaw_deg))


def mesh_path(root, asset):
    return os.path.join(root, MESH_DIR_REL, asset + MESH_SUFFIX)


def plan_pieces(root, pieces, max_pieces=0):
    """Sort every piece into what will be built and what will not, with reasons.

    Returns (buildable, skipped, tally). A skip is never silent: it carries the
    piece name and a reason token, and the tally counts reasons so the done
    line can print a zero WITH the denominator it is a zero of.
    """
    buildable, skipped = [], []
    tally = {"box": 0, "cyl": 0, "mesh": 0, "decal": 0,
             "unknown-shape": 0, "mesh-asset-missing": 0, "capped": 0}
    assets_wanted, assets_found = set(), set()
    for i, p in enumerate(pieces):
        if max_pieces and len(buildable) >= max_pieces:
            tally["capped"] += 1
            skipped.append((p.get("name", "piece%d" % i), "capped"))
            continue
        shape = p.get("shape")
        if shape in ("box", "cyl", "decal"):
            tally[shape] += 1
            buildable.append(p)
        elif shape == "mesh":
            asset = p.get("asset") or ""
            assets_wanted.add(asset)
            if os.path.exists(mesh_path(root, asset)):
                assets_found.add(asset)
                tally["mesh"] += 1
                buildable.append(p)
            else:
                tally["mesh-asset-missing"] += 1
                skipped.append((p.get("name", "piece%d" % i),
                                "mesh-asset-missing/" + (asset or "unnamed")))
        else:
            tally["unknown-shape"] += 1
            skipped.append((p.get("name", "piece%d" % i),
                            "unknown-shape/" + str(shape)))
    tally["assets_wanted"] = len(assets_wanted)
    tally["assets_found"] = len(assets_found)
    return buildable, skipped, tally


def png_name(stem, index, total):
    """Output names an artist can flip through in order without thinking.

    Zero padded to the width of the total, so ten frames sort as ten frames.
    Prefixed with the recipe's own file stem, so two recipes rendering into one
    commission's preview directory can never overwrite each other, and renaming
    this file renames its output rather than orphaning it.
    """
    width = max(2, len(str(total)))
    return "%s-%0*d.png" % (stem, width, index + 1)


def parse_args(argv):
    """Everything after `--`, refused BY NAME when it is not understood.

    Blender hands the script the whole command line, so the arguments meant for
    this file are the ones after the bare `--` the workflow passes. An unknown
    flag is an error rather than something ignored: a typo that renders the
    default scene into the right directory is exactly the empty success the
    workflow's PNG count cannot catch, because the count would rise.
    """
    args = list(argv)
    if "--" in args:
        args = args[args.index("--") + 1:]
    else:
        # Run directly as a python script rather than through Blender: drop
        # argv[0] only, since there is no Blender command line to strip.
        args = args[1:] if args and args[0].endswith(".py") else args
    out = {"out": "", "bay": None, "samples": DEFAULT_SAMPLES,
           "res": DEFAULT_RES, "engine": "CYCLES", "fog": False,
           "cameras": DEFAULT_CAMERAS, "max_pieces": 0, "dry_run": False,
           "root": ROOT, "error": ""}
    i = 0

    def need(flag):
        if i + 1 >= len(args):
            out["error"] = "flag-without-a-value/" + flag
            return None
        return args[i + 1]

    while i < len(args):
        a = args[i]
        if a == "--out":
            v = need(a)
            if v is None:
                break
            out["out"] = v
            i += 2
        elif a == "--bay":
            v = need(a)
            if v is None:
                break
            try:
                out["bay"] = int(v)
            except ValueError:
                out["error"] = "bay-is-not-an-integer/" + v
                break
            i += 2
        elif a == "--samples":
            v = need(a)
            if v is None:
                break
            try:
                out["samples"] = max(1, int(v))
            except ValueError:
                out["error"] = "samples-is-not-an-integer/" + v
                break
            i += 2
        elif a == "--cameras":
            v = need(a)
            if v is None:
                break
            try:
                out["cameras"] = max(1, int(v))
            except ValueError:
                out["error"] = "cameras-is-not-an-integer/" + v
                break
            i += 2
        elif a == "--max-pieces":
            v = need(a)
            if v is None:
                break
            try:
                out["max_pieces"] = max(0, int(v))
            except ValueError:
                out["error"] = "max-pieces-is-not-an-integer/" + v
                break
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
            i += 2
        elif a == "--engine":
            v = need(a)
            if v is None:
                break
            if v.upper() not in ("CYCLES", "EEVEE"):
                out["error"] = "engine-is-not-CYCLES-or-EEVEE/" + v
                break
            out["engine"] = v.upper()
            i += 2
        elif a == "--root":
            v = need(a)
            if v is None:
                break
            out["root"] = v
            i += 2
        elif a == "--fog":
            out["fog"] = True
            i += 1
        elif a == "--dry-run":
            out["dry_run"] = True
            i += 1
        else:
            out["error"] = "unknown-flag/" + a
            break
    if not out["error"] and not out["out"] and not out["dry_run"]:
        out["error"] = "missing-flag/--out"
    return out


def build_plan(root, opts):
    """Everything decided before a single Blender call. Pure, and printable.

    This is the function `run-recipe.py --plan` runs to get a full reading of
    what the recipe would do on a machine with no Blender on it.
    """
    data, err = load_pieces(root)
    if err:
        return None, err
    pieces = data["pieces"]
    run = glazing_run(pieces)
    if run["count"] == 0:
        return None, "no-east_parade_glass-pieces-in-the-file"
    aspect = opts["res"][0] / float(opts["res"][1])
    cameras, cam_err = walk_cameras(data, run, opts["cameras"], aspect)
    if cam_err:
        return None, cam_err
    hints = mickeys_hints(pieces, run)
    bay = hints["default_bay"] if opts["bay"] is None else opts["bay"]
    bay_valid = 0 <= bay < run["count"]
    buildable, skipped, tally = plan_pieces(root, pieces, opts["max_pieces"])
    coverage = bay_coverage(cameras, run, aspect)
    half_h = horizontal_half_fov_deg(cameras[0]["fov_vertical_deg"], aspect)
    published = next((c for c in data["cameras"] if c["id"] == "cam_B"), {})
    measured = footway_top_y(pieces, "west_footway", cameras[0]["z_m"])
    ground_delta_mm = (abs(measured - published.get("ground_y_m", 0.0)) * 1000.0
                       if measured is not None else None)
    return {
        "data": data,
        "pieces": pieces,
        "run": run,
        "cameras": cameras,
        "coverage": coverage,
        "hints": hints,
        "bay": bay,
        "bay_valid": bay_valid,
        "buildable": buildable,
        "skipped": skipped,
        "tally": tally,
        "aspect": aspect,
        "half_h_deg": half_h,
        "vanishing_margin_deg": half_h - cameras[0]["yaw_deg"],
        "ground_delta_mm": ground_delta_mm,
        "emissive": sum(1 for p in pieces if p.get("emissive")),
        "multi_rotation": data.get("counts", {}).get("multi_rotation"),
        "names": [png_name(RECIPE_STEM, i, len(cameras))
                  for i in range(len(cameras))],
    }, ""


def plan_lines(plan, opts):
    """The per-sample lines: one per camera, one per bay. No whole-run numbers.

    Per instruments.md, whole-run figures belong on the done line and per-sample
    figures on the sample lines, never both under one key.
    """
    lines = []
    for cam, name in zip(plan["cameras"], plan["names"]):
        lines.append(
            "walkCam idx=%d/%d png=%s x_m=%.3f y_m=%.4f z_m=%.3f "
            "yaw_deg=%.2f pitchDown_deg=%.2f fovV_deg=%.1f fovH_deg=%.2f"
            % (cam["index"] + 1, len(plan["cameras"]), name, cam["x_m"],
               cam["y_m"], cam["z_m"], cam["yaw_deg"], cam["pitch_down_deg"],
               cam["fov_vertical_deg"], plan["half_h_deg"] * 2))
    for row in plan["coverage"]:
        lines.append(
            "walkBay bay=%d/%d glazing=%s bestSpanFrac=%.3f "
            "bestSpanIsBestOf=%d-frames bestFrame=%d/%d framesSeeingIt=%d/%d "
            "legible=%s mickeys=%s spanSeries=%s"
            % (row["bay"], plan["run"]["count"], row["glazing"],
               row["best_span"], len(plan["cameras"]), row["best_cam"],
               len(plan["cameras"]), row["cams_seeing"], len(plan["cameras"]),
               "yes" if row["best_span"] >= LEGIBLE_SPAN_FRACTION else "no",
               "yes" if row["bay"] == plan["bay"] else "no",
               "/".join("%.3f" % v for v in row["per_cam"])))
    return lines


def done_line(plan, opts, built, rendered, png_bytes, seconds, status):
    """THE WHOLE-RUN LINE. Every zero carries the denominator it is a zero of.

    Written here, in the pure layer, so the string that ships is the string the
    selftest reads. No value contains a space: every reader in this project
    splits on whitespace, and a value with a space in it truncates in silence.

    PLANNED AND BUILT ARE TWO DIFFERENT FACTS and they get two different keys.
    `piecesPlanned` is what the piece file offered and this recipe accepted;
    `piecesBuilt` is what actually became an object in the scene, counted as it
    happened. `meshAssetsBuilt` is the same distinction for the sixteen .glb
    props: named by the file, found on disk, and then actually imported. A
    pipeline that CAN place a model is not a model placed.
    """
    built = built or {"pieces": 0, "assets": set()}
    total = len(plan["cameras"])
    n_pieces = len(plan["pieces"])
    t = plan["tally"]
    skips = t["unknown-shape"] + t["mesh-asset-missing"] + t["capped"]
    reasons = "none/0-of-%d-read" % n_pieces
    if skips:
        reasons = ",".join(
            "%s=%d/%d" % (k, t[k], n_pieces)
            for k in ("unknown-shape", "mesh-asset-missing", "capped") if t[k])
    cov = plan["coverage"]
    legible = [r for r in cov if r["best_span"] >= LEGIBLE_SPAN_FRACTION]
    seen = [r for r in cov if r["cams_seeing"] > 0]
    worst = min(cov, key=lambda r: r["best_span"]) if cov else None
    hints = plan["hints"]
    conflict = "none"
    if hints["bar_back"] and hints["lettering"] and \
            hints["bar_back"][1] != hints["lettering"][1]:
        conflict = "bar-back-card-at-bay%d-vs-fascia-lettering-at-bay%d" % (
            hints["bar_back"][1], hints["lettering"][1])
    ground = ("agree/%.2fmm" % plan["ground_delta_mm"]
              if plan["ground_delta_mm"] is not None else "no-west-footway-slab")
    # A BARE ZERO CANNOT TELL "none of 593" FROM "nobody counted", and this one
    # is read out of the piece file rather than counted here, so it says which
    # file's count it is a zero of and says so when the file stopped publishing
    # it. The wrapper's selftest failed on this exact token on first run.
    compound = ("%d/%d-pieces-in-the-file" % (plan["multi_rotation"], n_pieces)
                if plan["multi_rotation"] is not None
                else "not-published-by-the-piece-file/nothing-measured")
    return (
        "%s done: status=%s piecesRead=%d/%d-in-file piecesPlanned=%d/%d-read "
        "piecesBuilt=%d/%d-planned "
        "piecesSkipped=%d/%d-read skipReasons=%s "
        "box=%d/%d cyl=%d/%d mesh=%d/%d decal=%d/%d "
        "meshAssetsFound=%d/%d-named meshAssetsBuilt=%d/%d-found "
        "camerasAsked=%d camerasRendered=%d/%d-asked pngsWritten=%d/%d-asked "
        "smallestPngBytes=%s outDir=%s "
        "mickeysBay=%d/%d-bays bayValid=%s bayDefaultFrom=%s bayHintConflict=%s "
        "baysInAnyFrame=%d/%d baysLegibleAtSpan%.2f=%d/%d worstBay=bay%d/span%.3f "
        "vanishingPointMarginDeg=%.2f groundCrossCheck=%s compoundRotations=%s "
        "condition=overcast_day/1-of-2-in-the-file nightRendered=no "
        "emissivePieces=%d/%d emissiveLit=0/%d-lanterns-off-in-overcast_day "
        "fog=%s engine=%s samples=%d res=%dx%d "
        "coloursFromSpec=%d/%d-surfaces renderSeconds=%.1f"
        % (RECIPE_STEM, status,
           n_pieces, n_pieces, len(plan["buildable"]), n_pieces,
           built["pieces"], len(plan["buildable"]),
           len(plan["skipped"]), n_pieces, reasons,
           t["box"], n_pieces, t["cyl"], n_pieces, t["mesh"], n_pieces,
           t["decal"], n_pieces,
           t["assets_found"], t["assets_wanted"],
           len(built["assets"]), t["assets_found"],
           total, rendered, total, len(png_bytes), total,
           (min(png_bytes) if png_bytes else "nothing-written"),
           (opts["out"] or "none/dry-run").replace(" ", "~"),
           plan["bay"], plan["run"]["count"],
           "yes" if plan["bay_valid"] else "NO-SUCH-BAY",
           hints["default_from"], conflict,
           len(seen), len(cov), LEGIBLE_SPAN_FRACTION, len(legible), len(cov),
           worst["bay"] if worst else -1, worst["best_span"] if worst else 0.0,
           plan["vanishing_margin_deg"], ground, compound,
           plan["emissive"], n_pieces, plan["emissive"],
           ("on/density%.3f" % plan["data"]["conditions"][0]["fog_density"])
           if opts["fog"] else
           ("off/specDensity%.3f" % plan["data"]["conditions"][0]["fog_density"]),
           opts["engine"], opts["samples"], opts["res"][0], opts["res"][1],
           len(SURFACES_FROM_SPEC), len(SURFACE_GREY), seconds))


# ---------------------------------------------------------------------------
# THE BLENDER LAYER. Everything below touches bpy and therefore ships UNRUN
# from this container. It is kept thin and mechanical on purpose: it decides
# nothing, it only asks Blender to do what the plan above already worked out.
# ---------------------------------------------------------------------------


def _require_bpy():
    if bpy is None:
        raise RuntimeError("no-bpy")


def _reset_scene():
    """An empty scene. --factory-startup still opens the default cube."""
    _require_bpy()
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _material(surface):
    """One grey Principled material per surface name, made once and reused."""
    _require_bpy()
    existing = bpy.data.materials.get(surface)
    if existing:
        return existing
    r, g, b, rough = SURFACE_GREY.get(surface, (0.5, 0.5, 0.5, 0.8))
    mat = bpy.data.materials.new(surface)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (
            srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = (
                0.6 if surface == "metal" else 0.0)
    return mat


def _place(obj, piece):
    obj.location = to_blender_xyz(piece["x_m"], piece["y_m"], piece["z_m"])
    obj.rotation_euler = to_blender_euler(
        piece["pitch_deg"], piece["yaw_deg"], piece["roll_deg"])
    obj.data.materials.append(_material(piece.get("surface") or "concrete"))
    return obj


def _add_box(piece):
    _require_bpy()
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    obj = bpy.context.active_object
    obj.name = piece["name"]
    obj.scale = to_blender_scale(piece["sx_m"], piece["sy_m"], piece["sz_m"])
    return _place(obj, piece)


def _add_cyl(piece):
    """A cylinder whose axis is local +y in the file, which is Blender local +Z.

    24 sides rather than the default 32: there are 146 cylinders in this street
    and this is a preview, not the game render. At eye height a 114 mm lamp
    column shaft is under a degree wide.
    """
    _require_bpy()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.0, vertices=24)
    obj = bpy.context.active_object
    obj.name = piece["name"]
    obj.scale = to_blender_scale(piece["sx_m"], piece["sy_m"], piece["sz_m"])
    return _place(obj, piece)


def _add_decal(piece):
    """A quad built in local space so its normal is the file's -z before rotation.

    Vertices are written directly rather than rotating a plane primitive, so the
    piece's own rotation is the only rotation on the object and the file's
    convention is visible in the four corners. The quad is then lifted along its
    own world normal so it does not fight the surface it sits on.
    """
    _require_bpy()
    hx, hy = piece["sx_m"] / 2.0, piece["sy_m"] / 2.0
    mesh = bpy.data.meshes.new(piece["name"])
    mesh.from_pydata([(-hx, 0.0, -hy), (hx, 0.0, -hy),
                      (hx, 0.0, hy), (-hx, 0.0, hy)], [], [(0, 1, 2, 3)])
    mesh.update()
    obj = bpy.data.objects.new(piece["name"], mesh)
    bpy.context.collection.objects.link(obj)
    _place(obj, piece)
    normal = obj.rotation_euler.to_matrix() @ mathutils.Vector((0.0, -1.0, 0.0))
    obj.location = obj.location + normal * DECAL_LIFT_M
    return obj


def _gltf_available():
    _require_bpy()
    if hasattr(bpy.ops.import_scene, "gltf"):
        return True
    try:
        bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
    except Exception:
        return False
    return hasattr(bpy.ops.import_scene, "gltf")


def _add_mesh(piece, root):
    """Import a .glb, never scale it, put its own bounds centre on the piece.

    That is the file's own `mesh_placement` rule word for word. The imported
    objects are moved so their combined bounds centre sits at the origin and
    then parented, with an identity parent inverse, to an empty carrying the
    piece's position and rotation. Parenting rather than transforming each
    object keeps a multi-part asset rigid and keeps the rotation about the
    bounds centre rather than about whatever origin the asset was exported on.
    """
    _require_bpy()
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=mesh_path(root, piece["asset"]))
    new = [o for o in bpy.data.objects if o not in before]
    if not new:
        return None
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for o in new:
        if o.type != "MESH":
            continue
        for corner in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(corner)
            for k in range(3):
                lo[k] = min(lo[k], w[k])
                hi[k] = max(hi[k], w[k])
    if lo[0] == float("inf"):
        return None
    centre = [(lo[k] + hi[k]) / 2.0 for k in range(3)]
    roots = [o for o in new if o.parent is None]
    for o in roots:
        o.location = (o.location[0] - centre[0], o.location[1] - centre[1],
                      o.location[2] - centre[2])
    empty = bpy.data.objects.new(piece["name"], None)
    bpy.context.collection.objects.link(empty)
    empty.location = to_blender_xyz(piece["x_m"], piece["y_m"], piece["z_m"])
    empty.rotation_euler = to_blender_euler(
        piece["pitch_deg"], piece["yaw_deg"], piece["roll_deg"])
    for o in roots:
        o.parent = empty
        o.matrix_parent_inverse = mathutils.Matrix.Identity(4)
    return empty


def _light_overcast(plan, fog):
    """The file's `overcast_day`: sun on, lanterns off, a bright grey sky."""
    _require_bpy()
    sun_spec = plan["data"]["sun"]
    light = bpy.data.lights.new("sun", type="SUN")
    light.angle = math.radians(OVERCAST_SUN_ANGLE_DEG)
    light.energy = OVERCAST_SUN_ENERGY
    obj = bpy.data.objects.new("sun", light)
    bpy.context.collection.objects.link(obj)
    travel = mathutils.Vector(sun_direction(sun_spec["elevation_deg"],
                                            sun_spec["azimuth_deg"]))
    obj.rotation_euler = travel.to_track_quat("-Z", "Y").to_euler()
    world = bpy.data.worlds.new("overcast")
    world.use_nodes = True
    bpy.context.scene.world = world
    bg = world.node_tree.nodes.get("Background")
    if bg is not None:
        bg.inputs[0].default_value = tuple(
            srgb_to_linear(c) for c in OVERCAST_SKY) + (1.0,)
        bg.inputs[1].default_value = 1.0
    if fog:
        # OPT-IN AND EXPENSIVE. A world volume scatter is the whole sky
        # participating in every ray, which is minutes a frame rather than
        # seconds. Off by default, and the done line says which it was.
        nodes = world.node_tree.nodes
        scatter = nodes.new("ShaderNodeVolumeScatter")
        scatter.inputs["Density"].default_value = \
            plan["data"]["conditions"][0]["fog_density"]
        world.node_tree.links.new(
            scatter.outputs[0], nodes["World Output"].inputs["Volume"])


def _add_camera(cam):
    """Vertical-fit lens, so the file's fov_vertical_deg is the one honoured.

    Blender's camera looks down its own -Z with +Y up. Rotating 90 degrees
    about X lays it horizontal looking along +Y, which is a bearing of 90 in
    the file's frame, so the heading is (yaw - 90) about Z and the down pitch
    comes off the X rotation.
    """
    _require_bpy()
    data = bpy.data.cameras.new(cam["id"])
    data.sensor_fit = "VERTICAL"
    data.angle_y = math.radians(cam["fov_vertical_deg"])
    obj = bpy.data.objects.new(cam["id"], data)
    bpy.context.collection.objects.link(obj)
    obj.location = to_blender_xyz(cam["x_m"], cam["y_m"], cam["z_m"])
    obj.rotation_euler = (math.radians(90.0 - cam["pitch_down_deg"]), 0.0,
                          math.radians(cam["yaw_deg"] - 90.0))
    return obj


def _configure_render(opts):
    """Engine, samples, resolution, view transform. Returns what it chose."""
    _require_bpy()
    scene = bpy.context.scene
    chosen = "CYCLES"
    if opts["engine"] == "EEVEE":
        # The identifier changed between 4.1 and 4.2 and the workflow will run
        # whichever it finds, so try the new name and fall back, printing which.
        for name in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
            try:
                scene.render.engine = name
                chosen = name
                break
            except TypeError:
                continue
    else:
        scene.render.engine = "CYCLES"
    if chosen == "CYCLES":
        scene.cycles.samples = opts["samples"]
        scene.cycles.use_denoising = True
    else:
        try:
            scene.eevee.taa_render_samples = opts["samples"]
        except AttributeError:
            pass
    scene.render.resolution_x = opts["res"][0]
    scene.render.resolution_y = opts["res"][1]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    for transform in ("AgX", "Filmic", "Standard"):
        try:
            scene.view_settings.view_transform = transform
            break
        except TypeError:
            continue
    return chosen


def _render_to(path):
    _require_bpy()
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


# ---------------------------------------------------------------------------


def main(argv):
    opts = parse_args(argv)
    if opts["error"]:
        print("%s refused: status=BAD-ARGS reason=%s nothing measured"
              % (RECIPE_STEM, opts["error"]))
        return 2
    plan, err = build_plan(opts["root"], opts)
    if err:
        print("%s refused: status=NO-PLAN reason=%s nothing measured"
              % (RECIPE_STEM, err))
        return 3
    for line in plan_lines(plan, opts):
        print(line)
    if not plan["bay_valid"]:
        print("%s refused: status=BAD-BAY bayAsked=%d bays=0..%d nothing measured"
              % (RECIPE_STEM, plan["bay"], plan["run"]["count"] - 1))
        return 4
    if plan["multi_rotation"] not in (0, None):
        # The euler conversion assumes at most one non-zero angle per piece,
        # which the file publishes as a count. If that ever changes, this
        # recipe is wrong in a way no picture would show, so it stops.
        print("%s refused: status=MULTI-ROTATION count=%s "
              "reason=euler-order-unproven-for-compound-rotations nothing measured"
              % (RECIPE_STEM, plan["multi_rotation"]))
        return 5
    if opts["dry_run"]:
        print(done_line(plan, opts, None, 0, [], 0.0,
                        "DRY-RUN/planned-only/nothing-built-and-nothing-measured"))
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

    started = time.time()
    _reset_scene()
    # GROUND TRUTH, COUNTED AS IT HAPPENS. Not "the loop ran" and not "the
    # plan said 593": an object came back from Blender, or the piece is a skip
    # with a reason. `assets` is the same fact for the .glb props, and it is
    # the key that answers whether a fetched model is a model PLACED.
    built = {"pieces": 0, "assets": set()}
    for piece in plan["buildable"]:
        shape = piece["shape"]
        obj = None
        if shape == "box":
            obj = _add_box(piece)
        elif shape == "cyl":
            obj = _add_cyl(piece)
        elif shape == "decal":
            obj = _add_decal(piece)
        elif shape == "mesh":
            if not _gltf_available():
                # A NAMED SKIP, NEVER A SILENT ONE. Better a street without its
                # props than a run that cannot say what is missing from it.
                plan["skipped"].append((piece["name"], "gltf-importer-unavailable"))
                plan["tally"]["mesh-asset-missing"] += 1
                plan["tally"]["mesh"] -= 1
                continue
            obj = _add_mesh(piece, opts["root"])
            if obj is not None:
                built["assets"].add(piece["asset"])
        if obj is None:
            plan["skipped"].append((piece["name"], "blender-returned-no-object"))
            continue
        built["pieces"] += 1
    print("walkBuild piecesBuilt=%d/%d-planned ofFile=%d meshAssetsBuilt=%d/%d "
          "elapsedSeconds=%.1f"
          % (built["pieces"], len(plan["buildable"]), len(plan["pieces"]),
             len(built["assets"]), plan["tally"]["assets_found"],
             time.time() - started))

    _light_overcast(plan, opts["fog"])
    engine = _configure_render(opts)
    rendered, sizes = 0, []
    for cam, name in zip(plan["cameras"], plan["names"]):
        bpy.context.scene.camera = _add_camera(cam)
        t0 = time.time()
        path = os.path.join(out_dir, name)
        _render_to(path)
        took = time.time() - t0
        # VERIFY THE EFFECT, NOT THE CALL. bpy.ops.render.render returns
        # FINISHED whether or not a file landed on disk.
        size = os.path.getsize(path) if os.path.exists(path) else 0
        if size > 0:
            rendered += 1
            sizes.append(size)
        print("walkFrame idx=%d/%d png=%s bytes=%d renderSeconds=%.1f engine=%s"
              % (cam["index"] + 1, len(plan["cameras"]), name, size, took,
                 engine))
    for name, reason in plan["skipped"]:
        print("walkSkip piece=%s reason=%s" % (name, reason))
    total = time.time() - started
    status = "RAN" if rendered == len(plan["cameras"]) else "PARTIAL"
    print(done_line(plan, opts, built, rendered, sizes, total, status))
    return 0 if rendered == len(plan["cameras"]) else 8


# RUN WHEN BLENDER RUNS ME, STAY QUIET WHEN A TEST IMPORTS ME. Blender executes
# a --python script with __name__ set to "__main__", and the wrapper's selftest
# imports this file with no bpy in the process to exercise the pure layer. The
# second clause is belt and braces for a Blender build that ever stopped setting
# __name__: if bpy is importable, this file is inside Blender and has work to do.
if __name__ == "__main__" or bpy is not None:
    sys.exit(main(sys.argv))
