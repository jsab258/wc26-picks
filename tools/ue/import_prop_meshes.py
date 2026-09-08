"""Import the street's held prop meshes to uassets, from a script, in CI.

    UnrealEditor-Cmd.exe LedgerProbe.uproject -run=pythonscript \
        -script="tools/ue/import_prop_meshes.py" -unattended -nopause -nosplash
    python3 tools/ue/import_prop_meshes.py --selftest   # runs without Unreal
    python3 tools/ue/import_prop_meshes.py --measure    # container half only

WHY IT EXISTS, and it is the same reason tools/ue/make_base_material.py
exists. A GLB is not a thing Unreal can place: a static mesh asset is a
cooked package, the importer that makes one is editor-only, and a packaged
game can only place meshes that already exist as assets. production/specs/
vignette-pieces.json asks for 23 pieces of shape "mesh" naming 16 held GLBs,
and until now every one of them was drawn as a BOX of the prop's own stated
size, counted on the scene line as propStandIns so that nobody could read the
frame as a loaded model. This script is the other half: the GLBs become
uassets as a BUILD PRODUCT, made by a script in a step, never by a human in
an editor, exactly as the base material is.

THE CONTRACT WITH THE STREET, which production/specs/vignette-scene.json
already states in as many words under held_props.pivot_note, and which this
file does not get to reinterpret:

    "a placement here names where the prop's BOUNDING BOX CENTRE goes,
     exactly like every other piece in the list, and each emitter puts the
     loaded mesh's own bounds centre there. Nothing is ever scaled."

So two facts have to be true for the mesh route to be correct, and each is
measured by the half of the pipeline that can see it:

  1. THE SPEC'S BOX IS THE GLB'S OWN MEASURED SIZE, which makes scale 1 the
     right scale and makes any scaling a bug. Measured HERE, in the
     container, against the shipped GLBs, by --selftest. The series over all
     16 assets on 2026-09-08 was 0.0000 mm on every axis: the spec file
     carries six decimals of a metre and the numbers are the same numbers.
     That is why the container's tolerance is one micron and not a guess.

  2. THE ENGINE'S IMPORTED MESH IS THAT SAME BOX, in the engine's own axis
     order. Only a run can measure that, because the glTF-to-Unreal axis
     convention is the importer's opinion and not ours. So this script reads
     unreal.StaticMesh.get_bounds() BACK off every asset it just made and
     prints the delta against the spec box both in the assumed axis order
     and as an unordered multiset. THERE IS NO GATE ON THAT NUMBER YET: no
     run has printed the series, and a bound set before its series is the
     failure this project keeps finding. propBoundsBound says so out loud.

WHAT IT MAKES. One static mesh per held asset the street names, at
/Game/Ledger/Props/SM_<asset>, plus collision on each, because a mesh
without collision reads as placed and walks through. The names are a
contract with VignetteShot.cpp's mesh branch, which derives the object path
from the piece's own "asset" field and nothing else, and --selftest reads
that derivation out of the C++ rather than trusting the two were kept in
step by hand.

COLLISION, AND WHY IT IS TWO READINGS AND NOT ONE. Run 3 printed
propCollisionPrims=0/15 over fifteen saved meshes and the accepting case
printed collisionPrims=-1 for the same mesh in the same run. Neither number
was a count. The -1 is what EditorStaticMeshLibrary returns when it refuses,
which it does in a commandlet, and the 0 is that -1 run through a
`prims > 0` tally: a refusal counted as an absence, which is rule 3b with a
number on it. So the count routes now reject a negative as a SENTINEL and
name it, an unreadable count prints nothing-measured with the refusal rather
than a zero, and the count lives beside the reading that answers the
question the walk clip actually asks. A simple-primitive count is a PROXY: a
mesh whose body setup says use-complex-as-simple collides with its own
triangles and reports zero simple primitives. propCollidable is the key for
that, read off the saved asset, and it is still not a sweep. Only the walk
clip in the built level is a sweep, and it is the one thing this script
cannot run.

WHAT THE EVIDENCE IS. ue-prop-meshes.txt beside the project, one key=value
line, copied into the verdict by the workflow, because a log tail is not an
evidence channel in this project and a committed file is. Plus
ue-prop-meshes.json, the per-asset readings that do not fit on a line.
Neither is ever carried forward: the workflow deletes both before the run
and a stage that measured nothing writes the words NOTHING MEASURED.

THE STATUS WORD AND THE RETURN CODE ARE PURE FUNCTIONS AT THE TOP OF THIS
FILE and are exercised by --selftest in the container that writes them, for
the reason instruments.md gives: a formatter written where the tests do not
run ships unrun, and an unrun formatter printing a plausible string is the
silent-instrument failure.

lamp_post_01 IS A SPECIAL CASE AND IT IS NAMED, NOT SMUGGLED. Jafar asked
for that file specifically. No piece in vignette-pieces.json references it:
production/specs/vignette-bill-of-materials.json records why_not in as many
words, that it measures 3.00 m which is amenity height rather than street
lighting height, and the 5.0 m mounting height the street does emit was
DERIVED from that measurement. So this script imports it beside the 16 the
street asks for, so that the route is proven end to end for the exact file
that was named, and prints propLampPost01 as its own key. Placing it is a
change to the piece generator, which is not this script's to make.
"""

import json
import os
import re
import sys

# ---- the three path conventions, which are a contract with the C++ --------

BASE_MESH_DIR = os.path.join("ledger", "Assets", "Props", "base-mesh")
PACKAGE_DIR = "/Game/Ledger/Props"
UASSET_PREFIX = "SM_"

# THE EXTRA ASSET, imported for the reason in the docstring and counted
# separately from the ones the street asks for so that neither number can
# absorb the other.
EXTRA_ASSETS = ("lamp_post_01",)

# THE ACCEPTING CASE, NAMED, SO ITS STATE IS READABLE WITHOUT PARSING A LIST.
# Retargeted by Jafar on 2026-09-08 from lamp_post_01, which no piece places,
# to A7_gully_grate, which is a real piece of the built street: it has a box
# in the frame today, so replacing that box with the mesh is a thing a person
# can look at. Both constants are checked against the live spec by --selftest
# rather than trusted from this comment.
ACCEPTING_ASSET = "drainage_grate_01"
ACCEPTING_PIECE = "prop_drainage_grate_01_0"

# ONE MICRON, AND IT IS THE MEASURED SERIES AND NOT A ROUND NUMBER.
# vignette-pieces.json carries quantisation_decimals=6, so a size in it is
# within 0.5 um of the plan, and the worst disagreement between a spec box
# and its GLB's own measured dimensions over all 16 assets was 0.0000 mm.
# A bound of 0.001 mm therefore accepts every real asset and would reject a
# prop that had been rescaled by anything a person could see.
SPEC_VS_GLB_TOL_MM = 0.001

# The engine side has NO BOUND. See propBoundsBound in prop_line().
CENTIMETRES_PER_METRE = 100.0

# How many per-asset readings go on the one line before the cap bites.
DETAIL_CAP = 6


def repo_root():
    """Two directories up from tools/ue, by the script's own location, so this
    works from the runner's workspace root and from inside the editor alike."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


# ---- what the street asks for, read off the file and never hand-listed ----


def mesh_pieces(spec):
    """Every piece of shape "mesh", in file order. The denominator for every
    count below, and it comes off the FILE rather than off a run."""
    return [p for p in spec.get("pieces", []) if p.get("shape") == "mesh"]


def assets_asked(spec):
    """Asset ids the mesh pieces name, in first-appearance order, each with
    the piece names that want it. Ordered rather than a set because a run
    that dies halfway should have imported the first thing the file asked
    for, not an arbitrary one."""
    out = []
    at = {}
    for p in mesh_pieces(spec):
        a = p.get("asset")
        if not a:
            continue
        if a not in at:
            at[a] = len(out)
            out.append((a, []))
        out[at[a]][1].append(p.get("name", "unnamed"))
    return out


def safe_asset_id(asset_id):
    """An asset id becomes a package name, so it may only hold characters a
    package name may hold. Anything else is refused by name rather than
    quietly sanitised, because a silently renamed asset is a mesh the C++
    will look for at a path that does not exist."""
    return bool(re.match(r"^[A-Za-z0-9_][A-Za-z0-9_-]*$", asset_id or ""))


def uasset_name(asset_id):
    """SM_<asset>, with the one character a package name cannot carry mapped
    the same way in both languages."""
    return UASSET_PREFIX + asset_id.replace("-", "_")


def package_path(asset_id):
    return PACKAGE_DIR + "/" + uasset_name(asset_id)


def object_path(asset_id):
    """THE STRING VignetteShot.cpp BUILDS. Kept identical by --selftest,
    which reads the C++ rather than trusting this comment."""
    n = uasset_name(asset_id)
    return PACKAGE_DIR + "/" + n + "." + n


def glb_source(asset_id):
    return os.path.join(BASE_MESH_DIR, asset_id + ".glb")


def spec_box_m(piece):
    return (float(piece["sx_m"]), float(piece["sy_m"]), float(piece["sz_m"]))


def box_per_asset(spec):
    """One box per asset, and the disagreements, because two pieces naming one
    asset at two different sizes would mean one of them is scaled and the
    dims policy forbids that. Returns (boxes, disagreements)."""
    boxes = {}
    bad = []
    for p in mesh_pieces(spec):
        a = p.get("asset")
        if not a:
            continue
        b = spec_box_m(p)
        if a not in boxes:
            boxes[a] = b
        elif max(abs(x - y) for x, y in zip(b, boxes[a])) * 1000.0 > SPEC_VS_GLB_TOL_MM:
            bad.append("%s/%s" % (a, p.get("name", "unnamed")))
    return boxes, bad


# ---- the measurement arithmetic, which lives where the tests run ----------


def delta_mm(a, b):
    """Per-axis absolute difference in millimetres, for two triples of
    metres."""
    return [abs(float(x) - float(y)) * 1000.0 for x, y in zip(a, b)]


def expected_ue_size_m(box_m):
    """The spec box in the axis ORDER this project's C++ uses everywhere else:
    VignetteShot.cpp maps file (x, y, z) to Unreal (x, z, y), because the file
    is y-up metres and Unreal is z-up. That mapping is an ASSUMPTION about
    what the glTF importer does, named here so the reading can contradict it,
    which is the whole point of also reporting the unordered comparison."""
    sx, sy, sz = box_m
    return (sx, sz, sy)


def bounds_reading(asset_id, box_m, origin_uu, extent_uu):
    """One asset's engine readback against the box the street drew for it.

    origin_uu is unreal.StaticMesh.get_bounds().origin, the LOCAL centre of
    the mesh's bounding box in unreal units, which is the number the pivot
    correction is made of: a prop whose origin is at its base has an origin.z
    of half its height, and awning_02's is negative because that mesh hangs
    off its top-back corner. extent_uu is the half-size.

    Two deltas, not one, and they answer different questions. The ORDERED
    delta asks whether the imported mesh is the right size on the right axis.
    The SORTED delta asks only whether it is the right size, so an ordered
    miss beside a sorted match is an axis convention this file guessed wrong
    and not a mesh that came in at the wrong scale. Reporting one without the
    other cannot tell those apart."""
    size_m = tuple(abs(float(v)) * 2.0 / CENTIMETRES_PER_METRE for v in extent_uu)
    want = expected_ue_size_m(box_m)
    ordered = delta_mm(size_m, want)
    srt = delta_mm(sorted(size_m), sorted(want))
    axes = ("x", "y", "z")
    worst_i = max(range(3), key=lambda i: ordered[i])
    return {
        "asset": asset_id,
        "specBoxM": [round(v, 6) for v in box_m],
        "engineSizeM": [round(v, 6) for v in size_m],
        "localCentreUu": [round(float(v), 3) for v in origin_uu],
        "orderedDeltaMm": [round(v, 4) for v in ordered],
        "sortedDeltaMm": [round(v, 4) for v in srt],
        "worstOrderedMm": round(max(ordered), 4),
        "worstOrderedAxis": axes[worst_i],
        "worstSortedMm": round(max(srt), 4),
    }


def worst_bounds(readings):
    """AT WORST over the assets, with the asset it was worst ON captured at
    the same instant, because a maximum with no name is a number nobody can
    act on. nothing-measured when no asset was read back."""
    if not readings:
        return "propBoundsWorstMm=nothing-measured propBoundsWorstSortedMm=nothing-measured"
    o = max(readings, key=lambda r: r["worstOrderedMm"])
    s = max(readings, key=lambda r: r["worstSortedMm"])
    return ("propBoundsWorstMm=%.4f/on=%s/axis=%s/of=%d "
            "propBoundsWorstSortedMm=%.4f/on=%s"
            % (o["worstOrderedMm"], o["asset"], o["worstOrderedAxis"],
               len(readings), s["worstSortedMm"], s["asset"]))


def pivot_field(readings, cap=DETAIL_CAP):
    """The local bounds centre per asset, which is the pivot correction the
    C++ applies, printed so that a reader can see WHICH props are not
    pivoted at their base. Capped, and the cap announces itself."""
    if not readings:
        return "propPivots=nothing-measured"
    parts = ["%s=%.1f,%.1f,%.1f" % (r["asset"], r["localCentreUu"][0],
                                    r["localCentreUu"][1], r["localCentreUu"][2])
             for r in readings[:cap]]
    out = ";".join(parts)
    if len(readings) > cap:
        out += ";(+%d~more~not~shown)" % (len(readings) - cap)
    return "propPivotsUu=" + out


def fallback_field(failures, asked, cap=DETAIL_CAP):
    """Assets that did not become a uasset, each with WHY, because "15 of 16"
    with no reason is a round trip. Zero ships its denominator."""
    if not failures:
        return "propFailed=0/%d propFailedWhy=none" % asked
    parts = ["%s=%s" % (a, str(w).replace(" ", "~")) for a, w in failures[:cap]]
    out = ";".join(parts)
    if len(failures) > cap:
        out += ";(+%d~more~not~shown)" % (len(failures) - cap)
    return "propFailed=%d/%d propFailedWhy=%s" % (len(failures), asked, out)


def import_status(asked, sources, imported, saved, collidable, unknown=0):
    """The one word. It needs every asset the street asks for to have become a
    saved uasset, for the reason MADE needed every connection in the material
    generator: a street missing one prop is a street with a box in it, and the
    scene line is the only place that would have shown it.

    COLLISION IS PART OF THE WORD and not a footnote. A mesh with no collision
    places, renders, photographs clean and lets a walking Character through
    it, and the walk clip is the deliverable. So a full import with no
    collision is IMPORTED-NO-COLLISION, which returns non-zero, rather than
    IMPORTED with a quiet count beside it.

    AND A THIRD WORD, ADDED AFTER RUN 3, because the two words above cannot
    say the thing that actually happened there. `collidable` counts the saved
    meshes the engine reports as collidable; `unknown` counts the ones where
    nothing could be read either way. A run that cannot tell must not print
    the word for a run that measured a failure, so an unreadable collision
    state is IMPORTED-COLLISION-UNREADABLE. Both non-IMPORTED words return
    non-zero: the difference is whether the next move is fixing the meshes or
    fixing the instrument.

    A definite failure outranks an unreadable one in the word, because
    `saved - collidable - unknown` meshes are known to be walk-through."""
    if asked == 0:
        return "NOTHING-ASKED"
    if sources == 0:
        return "NO-SOURCES"
    if imported == 0:
        return "NOTHING-IMPORTED"
    if saved < asked:
        return "PARTIAL"
    if saved - collidable - unknown > 0:
        return "IMPORTED-NO-COLLISION"
    if unknown > 0:
        return "IMPORTED-COLLISION-UNREADABLE"
    return "IMPORTED"


def import_return(status):
    """0 only for the word that means every asset the street asks for is a
    saved uasset with collision on it. The verdict travels in the FILE as
    propImportReturn; the editor process's exit code is the editor's, not
    this script's, which is the pair run 19 of the material generator could
    not explain."""
    return 0 if status == "IMPORTED" else 2


# ---- collision: the proxy, the real question, and the refusals ------------
#
# EVERY FUNCTION IN THIS SECTION IS PURE AND RUNS IN THE CONTAINER, for the
# reason instruments.md gives as a standing rule: a formatter written where
# the tests do not run ships unrun, and an unrun formatter printing a
# plausible string is the silent-instrument failure. The engine half supplies
# live state and nothing else. It decides no words.

COMPLEX_AS_SIMPLE = "COMPLEX_AS_SIMPLE"


def flat(value):
    """No spaces in any value, ever: every reader of these files splits on
    whitespace and truncates silently."""
    return str(value).replace(" ", "~")


def short_flag(flag):
    """The trace flag without its enum's type name, which is noise on a line.

    None is the WORD nothing-measured and never a flag value, because "the
    flag says use-default" and "nothing could read the flag" are the two
    facts run 3 could not tell apart anywhere in its collision reading."""
    if flag is None:
        return "nothing-measured"
    s = flat(flag)
    return s.rsplit(".", 1)[-1] if "." in s else s


def is_complex_as_simple(flag):
    """Does this trace flag mean the mesh collides with its own triangles?

    READ OFF THE ENGINE'S OWN SPELLING rather than compared to a literal: the
    Python binding prints the enumerator as CollisionTraceFlag.CTF_USE_COMPLEX
    _AS_SIMPLE, the C++ spells it CTF_UseComplexAsSimple, and a string compare
    against either one is a claim about a binding this container cannot run.
    So it normalises case and separators and asks whether the name contains
    the three words in order."""
    if flag is None:
        return False
    s = str(flag).upper()
    for ch in ("_", "-", " ", "."):
        s = s.replace(ch, "")
    return COMPLEX_AS_SIMPLE.replace("_", "") in s


def prims_word(prims, via):
    """The per-mesh simple-primitive count, or the words nothing-measured.

    THIS IS THE FIX FOR RUN 3'S ZERO. A count nothing could read is not zero
    and must not print as a number at all, which is rule 3b and the first
    bullet of instruments.md. The refusal travels with it so the reader knows
    which name refused."""
    if prims is None:
        return "nothing-measured/" + flat(via or "no-route-tried")
    return "%d" % int(prims)


def collidable_word(body_setup, prims, trace_flag, extent_uu):
    """CAN A SWEEP HIT THIS MESH, as far as the saved asset can say.

    THIS IS NOT THE PRIMITIVE COUNT AND THEY ARE NOT THE SAME QUESTION. The
    old docstring on propCollisionPrims said the primitive count was "the
    number the walk clip lives on". It is a proxy for it: a mesh whose body
    setup says use-complex-as-simple collides perfectly with its own render
    triangles and reports ZERO simple primitives, and a mesh with a body setup
    full of primitives and no geometry collides with nothing a player can see.

    THE HONEST LIMIT, stated in the stat key on the line as well as here: what
    the walk clip lives on is whether a capsule sweep in the BUILT LEVEL hits
    the grate. This function reads the asset, not a sweep. It can say NO with
    confidence (no body setup, or no primitive and a flag that needs one) and
    it can say YES on the asset's own terms; it cannot stand in for the clip.

    Three-valued on purpose. UNKNOWN is a real answer here and the whole
    reason this key exists."""
    if extent_uu is None:
        geom = "unread"
    elif max(abs(float(v)) for v in extent_uu) <= 0.0:
        geom = "empty"
    else:
        geom = "nonzero"
    # STARTSWITH, NOT EQUALS. The engine half says absent, or
    # absent/could-not-make/<the name that refused>, and both mean the mesh has
    # no container for collision to live in, which is a measured NO.
    if str(body_setup).startswith("absent"):
        return "NO/no-body-setup"
    if prims is not None and int(prims) > 0:
        return "YES/simple-prims=%d" % int(prims)
    if is_complex_as_simple(trace_flag):
        if geom == "nonzero":
            return "YES/complex-as-simple/boundsUu-nonzero"
        if geom == "empty":
            return "NO/complex-as-simple-but-bounds-are-empty"
        return "UNKNOWN/complex-as-simple/bounds-unread"
    if prims is None and trace_flag is None:
        return "UNKNOWN/nothing-measured/no-prim-count-and-no-trace-flag"
    if prims is None:
        return "UNKNOWN/nothing-measured/prim-count-unreadable/flag=%s" % short_flag(trace_flag)
    return "NO/no-simple-prims/flag=%s" % short_flag(trace_flag)


def collidable_tally(readings, saved_total=None):
    """(yes, unknown, no, denominator) over the SAVED meshes, which is the
    denominator the status word and the line both read.

    One function so that two numbers about one population cannot drift: the
    status word and propCollidable are the same count seen twice, and run 3
    shipped exactly that pair disagreeing.

    saved_total IS propSaved, and passing it is what keeps every collision
    denominator equal to it. A package that saved but produced no reading at
    all, because its bounds would not read, is counted UNKNOWN rather than
    dropped from the denominator: a mesh nobody measured is not a mesh that
    failed, and it is certainly not a mesh that passed."""
    saved = [r for r in readings if r.get("saved")]
    m = len(saved) if saved_total is None else max(int(saved_total), len(saved))
    yes = sum(1 for r in saved if str(r.get("collidable", "")).startswith("YES"))
    unk = sum(1 for r in saved if str(r.get("collidable", "")).startswith("UNKNOWN"))
    unk += m - len(saved)
    return yes, unk, m - yes - unk, m


def _tally(words, cap=DETAIL_CAP):
    """name=count;name=count, sorted, with the cap announcing itself."""
    t = {}
    for w in words:
        k = flat(w)
        t[k] = t.get(k, 0) + 1
    items = sorted(t.items())
    out = ";".join("%s=%d" % (k, v) for k, v in items[:cap])
    if len(items) > cap:
        out += ";(+%d~more~not~shown)" % (len(items) - cap)
    return out or "none"


def collision_field(readings, saved_total=None):
    """THE WHOLE-RUN COLLISION BLOCK, and every key on it is a statistic over
    the saved meshes.

    WHY THE PER-MESH KEYS ARE SPELLED DIFFERENTLY. Run 3 put
    propCollisionPrims=0/15 on the done line and collisionPrims=-1 on the
    accepting-case line, two different numbers about one thing under one name,
    which is the pair instruments.md says a grep silently merges. So the
    whole-run tallies are propCollision* and propCollidable* and the per-mesh
    readings are simplePrims= and collidable=. A grep for either one cannot
    pick up the other.

      propCollisionPrims      saved meshes whose body setup holds at least one
                              simple collision primitive, COUNT READ, over
                              saved. A PROXY for collidability, not the
                              question: see collidable_word().
      propCollisionPrimsUnread saved meshes where no route could read a count
                              at all. This is the number that was hiding
                              inside run 3's zero.
      propCollidable          saved meshes the asset itself reports as
                              collidable, over saved. The question the walk
                              clip asks, answered off the asset and not by a
                              sweep.
      propCollidableUnknown   saved meshes where neither a primitive count nor
                              a trace flag could be read.
      propCollisionAgree      how many meshes had two or more count routes
                              ANSWER, and whether they agreed. A legacy
                              library that forwards to a subsystem which is
                              None can answer a plausible number; two routes
                              agreeing is what makes one believable.
      propCollisionFlagSet    meshes this run CHANGED the trace flag on, which
                              is the write-on-change count. Above zero means
                              no simple primitive could be added.
    """
    yes, unk, no, m = collidable_tally(readings, saved_total)
    saved = [r for r in readings if r.get("saved")]
    # SAVED PACKAGES WITH NO READING AT ALL. They are in the denominator and
    # they are nothing-measured in every tally below, never a zero.
    unmeasured = m - len(saved)
    stats = ("propCollisionPrimsStat=saved-meshes-with-at-least-one-simple-primitive"
             "/count-read-off-the-body-setup/over-saved/A-PROXY-NOT-THE-QUESTION "
             "propCollidableStat=body-setup-plus-simple-prims-or-complex-as-simple"
             "/read-off-the-saved-asset/NOT-a-sweep/over-saved")
    if m == 0:
        return ("propCollisionPrims=nothing-measured/0-saved-meshes "
                "propCollisionPrimsUnread=0/0 "
                "propCollisionRead=nothing-measured propCollisionVia=nothing-measured "
                "propCollisionAgree=nothing-measured propCollisionFlagSet=0/0 "
                "propCollidable=nothing-measured/0-saved-meshes "
                "propCollidableUnknown=0/0 propCollidableWhy=nothing-measured "
                "propCollidableNo=0/0 " + stats)
    with_prims = sum(1 for r in saved
                     if r.get("simplePrims") is not None and int(r["simplePrims"]) > 0)
    unread = sum(1 for r in saved if r.get("simplePrims") is None) + unmeasured
    agree = disagree = one = 0
    none = unmeasured
    for r in saved:
        nums = [v for v in (r.get("simplePrimsAnswers") or {}).values()
                if isinstance(v, int)]
        if len(nums) == 0:
            none += 1
        elif len(nums) == 1:
            one += 1
        elif len(set(nums)) == 1:
            agree += 1
        else:
            disagree += 1
    return ("propCollisionPrims=%d/%d propCollisionPrimsUnread=%d/%d "
            "propCollisionRead=%s propCollisionVia=%s "
            "propCollisionAgree=agree=%d;disagree=%d;one-route=%d;no-route=%d/over=%d "
            "propCollisionFlagSet=%d/%d "
            "propCollidable=%d/%d propCollidableUnknown=%d/%d propCollidableNo=%d/%d "
            "propCollidableWhy=%s %s"
            % (with_prims, m, unread, m,
               _tally([r.get("simplePrimsVia", "none") for r in saved]),
               _tally([r.get("collisionAddVia", "none") for r in saved]),
               agree, disagree, one, none, m,
               sum(1 for r in saved if r.get("collisionFlagSet")), m,
               yes, m, unk, m, no, m,
               _tally([r.get("collidable", "nothing-measured") for r in saved]),
               stats))


def source_parts_field(parts, cap=DETAIL_CAP):
    """HOW MANY MESHES EACH SOURCE FILE HOLDS, because exactly one uasset is
    kept per asset and any others are left where the street never looks.

    MEASURED IN THE CONTAINER 2026-09-08 over the seventeen shipped GLBs:
    fourteen hold one mesh, swing_bin and wooden_crate_01 hold two,
    pavement_sign holds three. All three show up in run 3 and only one of them
    showed up as a failure.

      pavement_sign     three static meshes appeared (hinges, sign_front,
                        sign_back), none of them named after the asset, so the
                        resolver refused to choose and the asset failed. That
                        refusal is CORRECT and is not loosened.
      wooden_crate_01   two meshes appeared, the body matched the asset name,
                        and the lid was LEFT BEHIND silently. The body alone
                        measures 0.880368 x 1.000679 x 0.924386 m, which is
                        the engine reading run 3 printed to six decimals, and
                        the whole file is 1.0447 m tall. propBoundsWorstMm
                        = 44.0215 mm is that dropped lid and nothing else.
      swing_bin         two meshes, lid dropped the same way, and the bounds
                        delta is 0.0011 mm because that lid sits INSIDE the
                        body's box. The bounds instrument cannot see this one
                        at all, which is why the count below exists.

    parts is [(asset_id, mesh_count_or_None)]. None means the GLB could not be
    read, which is a different fact from one mesh and is counted apart."""
    if not parts:
        return ("propSourcePartsOver1=nothing-measured "
                "propSourcePartsWhich=nothing-measured "
                "propSourcePartsUnread=0/0 " + _SOURCE_PARTS_STAT)
    over = [(a, n) for a, n in parts if isinstance(n, int) and n > 1]
    unread = [a for a, n in parts if n is None]
    which = ";".join("%s=%d" % (a, n) for a, n in sorted(over)[:cap]) or "none"
    if len(over) > cap:
        which += ";(+%d~more~not~shown)" % (len(over) - cap)
    return ("propSourcePartsOver1=%d/%d propSourcePartsWhich=%s "
            "propSourcePartsUnread=%d/%d %s"
            % (len(over), len(parts), which, len(unread), len(parts),
               _SOURCE_PARTS_STAT))


_SOURCE_PARTS_STAT = ("propSourcePartsStat=mesh-nodes-in-the-source-glb-per-asset"
                      "/exactly-one-uasset-is-kept-per-asset"
                      "/the-others-are-not-at-the-contract-path")


def engine_field(subsystems, pipeline_opts):
    """THE TWO ENGINE QUESTIONS THE NEXT RUN NEEDS ANSWERED, formatted here
    rather than at the call site, because a string built where the tests do not
    run ships unrun.

      propSubsystems   why fault 1 happened: get_editor_subsystem returned
                       None, which is not the same fact as a missing method.
                       Asking for four of them says whether this commandlet
                       has editor subsystems at all.
      propPipelineOpts which import-time option names this engine exposes for
                       collision and for combining a multi-mesh file. NOTHING
                       IS SET from them this run, and the key says so: run 3
                       proved the import route that works, and changing its
                       options in the same pass that fixes collision would
                       risk fifteen working assets to test a property name."""
    return ("propSubsystems=%s propPipelineOpts=%s "
            "propPipelineOptsFilter=collision|combine|convex|ucx"
            "/NOTHING-SET-THIS-RUN/names-read-for-the-next-one"
            % (";".join(subsystems) if subsystems else "nothing-measured",
               ";".join(pipeline_opts) if pipeline_opts else "nothing-measured"))


def note_value(report, cap=4):
    """THE REFUSALS, DISTINCT, WITH HOW MANY TIMES EACH HAPPENED.

    Run 3's propNote printed one pair of refusals twice and had room for
    nothing else, because the note was the first four lines of a list that
    holds one entry per mesh per route: 33 lines, 4 distinct. A note that
    spends its cap on repeats is a note that hides the other causes, so this
    deduplicates, counts, and announces its own cap."""
    if not report:
        return "none"
    order, seen = [], {}
    for line in report:
        k = flat(line)
        if k not in seen:
            seen[k] = 0
            order.append(k)
        seen[k] += 1
    parts = ["%s~x%d" % (k, seen[k]) for k in order[:cap]]
    out = "/".join(parts)
    if len(order) > cap:
        out += "/(+%d~more~not~shown)" % (len(order) - cap)
    return out


def glb_mesh_names(path):
    """The names of the meshes inside a .glb, read out of the file's own JSON
    chunk. None when the file cannot be read as a GLB at all.

    WHY A SECOND READER EXISTS HERE. The engine half of this script runs on
    the editor's embedded interpreter, where tools/meshgen is not importable,
    so the count has to be readable from this file alone. The duplication is
    paid for by --selftest, which reads every shipped GLB with BOTH readers
    and asserts they agree: a second reader that drifts from the first is
    caught in the container on every run, by the accepting case."""
    try:
        with open(path, "rb") as f:
            head = f.read(12)
            if len(head) < 12 or head[:4] != b"glTF":
                return None
            chunk = f.read(8)
            if len(chunk) < 8:
                return None
            clen = int.from_bytes(chunk[0:4], "little")
            if chunk[4:8] != b"JSON":
                return None
            body = f.read(clen)
        if len(body) < clen:
            return None
        js = json.loads(body.decode("utf-8"))
    except Exception:
        return None
    out = []
    for i, m in enumerate(js.get("meshes") or []):
        out.append(str(m.get("name") or ("mesh%d" % i)))
    return out


def prop_line(status, asked, pieces, sources, imported, saved,
              readings, failures, via, collision_block, extras, uasset_bytes,
              note, gltf_block="", accepting_block="", lookup_block="",
              parts_block="", engine_block=""):
    """The one line the workflow copies into the build verdict.

    No spaces inside any value: every reader of these files splits on
    whitespace and truncates silently. Every zero carries its denominator.

      propMeshesAsked      unique assets the mesh pieces name, over the number
                           of PIECES asking. 16/23 is the healthy reading and
                           says both numbers rather than letting one stand in.
      propSources          GLBs found on disk, over assets asked.
      propImported         assets that loaded back as a StaticMesh after the
                           import, over assets asked. Loaded back, not
                           "the import task returned".
      propSaved            of those, the ones whose package saved to disk.
      propCollisionPrims   saved meshes whose body setup holds at least one
                           simple collision primitive, over saved. A PROXY,
                           corrected 2026-09-08: the docstring here used to
                           say it was "the number the walk clip lives on" and
                           it is not, because a mesh set to use its complex
                           geometry as simple collides and reports zero. The
                           whole block comes from collision_field(); the key
                           that answers the walk clip's question as far as an
                           asset can is propCollidable.
      propSourcePartsOver1 assets whose source GLB holds more than one mesh,
                           over assets. One uasset is kept per asset, so any
                           other part of that file is not at the contract path
                           and is not in the street. See source_parts_field().
      propImportVia        which import route took, or none-of-N, the same
                           shape make_base_material.py prints for a pin name.
      propBoundsBound      THE WORD THAT SAYS THERE IS NO GATE HERE YET. No
                           run has printed the engine-versus-spec series, so
                           this run prints it and sets nothing. Rule 2.
      propLampPost01       the file Jafar named first, which no piece
                           references. Imported and reported on its own key so
                           that its presence can never be read as the street
                           placing it.
      propGltfImporter     the word gltf_verdict() decided, which tells an
                           exporter-only engine from an absent importer from a
                           refusal. Run 1 could not.
      propAcceptingCase    A7_gully_grate, the piece the accepting case is
                           now about, on its own key so its state is readable
                           without parsing propFailedWhy.
    """
    return ("propImportStatus=%s propImportReturn=%d "
            "propMeshesAsked=%d/%d propMeshesStat=unique-assets/over-pieces-asking "
            "propSources=%d/%d propImported=%d/%d propSaved=%d/%d "
            "%s "
            "propImportVia=%s propPackageDir=%s propNamePattern=%s<asset> "
            "%s %s %s "
            "%s propBoundsBound=NONE-YET/this-run-prints-the-series "
            "propBoundsStat=spec-box-minus-engine-bounds-at-worst-over-assets "
            "%s %s %s %s "
            "propScalePolicy=1/never-scaled/dims-policy-forbids-it "
            "propLampPost01=%s propUassetBytes=%d "
            "propVerdictIs=propImportReturn/not-the-editor-process-exit "
            "propNote=%s"
            % (status, import_return(status),
               asked, pieces,
               sources, asked, imported, asked, saved, asked,
               collision_block if collision_block else collision_field([]),
               via, PACKAGE_DIR, UASSET_PREFIX,
               gltf_block if gltf_block else "propGltfImporter=nothing-measured",
               accepting_block if accepting_block else
               "propAcceptingCase=nothing-measured",
               lookup_block if lookup_block else lookup_field([]),
               worst_bounds(readings),
               pivot_field(readings),
               fallback_field(failures, asked),
               parts_block if parts_block else source_parts_field([]),
               engine_block if engine_block else
               "propSubsystems=nothing-measured propPipelineOpts=nothing-measured",
               extras, uasset_bytes,
               flat(note) if note else "none"))


def preexisting_field(deleted, asked):
    """A2. How many assets were deleted before the loop, over assets asked.

    WHY A DELETION IS PART OF A MEASUREMENT. The whole lookup rests on
    `new = after - before`. An asset left behind by an earlier run is in
    `before`, so a successful re-import of it appears in NEITHER set and the
    resolver reads nothing-appeared over an import that worked perfectly. The
    agent workspace on that runner is persistent, so this is not hypothetical:
    the first run that imports anything at all makes every later run lie.
    Deleting first is what makes the subtraction mean what it says."""
    return "propImportPreexistingDeleted=%d/%d" % (deleted, asked)


def lookup_field(details, cap=DETAIL_CAP):
    """THE PAIR THE DIRECTOR ASKED FOR, and it is a pair on purpose.

      propImportLookedFor   the object path the code asks for. One pattern,
                            printed once, because it is the same shape for
                            every asset.
      propImportedNames     what actually appeared under the destination
                            package path, per asset, after the import ran.
                            Capped, and the cap announces itself.
      propImportResolvedVia which RULE matched, tallied over the assets:
                            exact-path is the healthy one, nothing-appeared
                            means the import genuinely made nothing, and
                            name-contains-the-asset-id or
                            only-package-that-appeared means the import worked
                            and run 2's lookup was the entire fault.
      propImportRouteRan    which route got as far as running, tallied, and it
                            is LAST-WINS over the routes: the loop tries the
                            next route when one runs without producing a
                            findable mesh, so this names the last route that
                            ran for each asset and not the only one. Its
                            companion, `appeared`, is CUMULATIVE over every
                            route that ran, because a package made by route one
                            must not vanish from the evidence when route two
                            runs. Run 2 reported none-of-2-candidates while
                            BOTH routes ran and raised nothing, because the
                            route's return value was the load-back.
      propImportWaitTaken   how many assets needed the registry wait because
                            nothing had appeared yet, over the assets tried.
      propImportWaitChanged of those, how many had something appear AFTER the
                            wait. ABOVE ZERO IS THE ASYNC HYPOTHESIS CONFIRMED;
                            zero is not a rule-out, because the wait is a
                            registry scan and not a wait on the import. This
                            is the one key that
                            separates the director's first shape from his
                            second.
    """
    if not details:
        return ("propImportLookedFor=nothing-measured "
                "propImportedNames=nothing-measured "
                "propImportResolvedVia=nothing-measured "
                "propImportRouteRan=nothing-measured "
                "propImportSnapshotShape=nothing-measured "
                "propImportTaskApi=nothing-measured "
                "propImportTaskAsync=nothing-measured "
                "propImportResultType=nothing-measured "
                "propImportResultWaitAttrs=nothing-measured "
                "propImportRenamed=0/0 propImportAppearedUnnamed=0/0 "
                "propImportWaitTaken=0/0 propImportWaitChanged=0/0")
    pattern = PACKAGE_DIR + "/" + UASSET_PREFIX + "<asset>"
    shown = []
    for asset_id, d in details[:cap]:
        names = [str(x).rsplit("/", 1)[-1] for x in d.get("appeared", [])]
        shown.append("%s=%s" % (asset_id,
                                ",".join(names[:3]) if names else "none"))
    names_field = ";".join(shown)
    if len(details) > cap:
        names_field += ";(+%d~more~not~shown)" % (len(details) - cap)
    ways = {}
    ran = {}
    for _a, d in details:
        ways[d.get("resolvedVia", "unknown")] = ways.get(d.get("resolvedVia", "unknown"), 0) + 1
        ran[d.get("routeRan", "none")] = ran.get(d.get("routeRan", "none"), 0) + 1
    took = sum(1 for _a, d in details if d.get("waitTaken"))
    changed = sum(1 for _a, d in details if d.get("waitChanged"))
    shapes = sorted(set(d.get("snapshotShape", "nothing-measured")
                        for _a, d in details))
    apis = sorted(set(";".join(d.get("taskApi") or ["nothing-measured"])
                      for _a, d in details))
    async_tally = {}
    for _a, d in details:
        k = "before=%s/after=%s" % (d.get("taskAsyncBefore"), d.get("taskAsyncAfter"))
        async_tally[k] = async_tally.get(k, 0) + 1
    rtypes = sorted(set(str(d.get("resultType", "not-reached")) for _a, d in details))
    rattrs = sorted(set(";".join(d.get("resultWaitAttrs") or ["none"])
                        for _a, d in details))
    renamed = sum(1 for _a, d in details if d.get("renamed"))
    unnamed = sum(1 for _a, d in details
                  if str(d.get("resolvedVia", "")).startswith("appeared-unnamed"))
    # NO SPACES IN ANY VALUE, and these four come from the ENGINE rather than
    # from this file: a package path or a type name with a space in it would
    # silently truncate every reader that splits on whitespace.
    def flatten_all(xs):
        return [str(x).replace(" ", "~") for x in xs]
    shapes, apis, rtypes, rattrs = (flatten_all(shapes), flatten_all(apis),
                                    flatten_all(rtypes), flatten_all(rattrs))
    async_tally = dict((str(k).replace(" ", "~"), v) for k, v in async_tally.items())
    extra = ("propImportSnapshotShape=%s propImportTaskApi=%s "
             "propImportTaskAsync=%s propImportResultType=%s "
             "propImportResultWaitAttrs=%s "
             "propImportRenamed=%d/%d propImportAppearedUnnamed=%d/%d "
             % (",".join(shapes[:2]), ",".join(apis[:2]),
                ";".join("%s=%d" % (k, v) for k, v in sorted(async_tally.items())),
                ",".join(rtypes[:2]), ",".join(rattrs[:2]),
                renamed, len(details), unnamed, len(details)))
    return (extra +
            "propImportLookedFor=%s propImportedNames=%s "
            "propImportResolvedVia=%s propImportRouteRan=%s "
            "propImportWaitTaken=%d/%d propImportWaitChanged=%d/%d "
            "propImportWaitMeans=above-zero-is-an-async-import/zero-is-not-a-rule-out/the-wait-is-a-registry-scan"
            % (pattern, names_field,
               ";".join("%s=%d" % (k, v) for k, v in sorted(ways.items())),
               ";".join("%s=%d" % (k, v) for k, v in sorted(ran.items())),
               took, len(details), changed, took))


def accepting_field(readings, failures, sources_found):
    """A7_gully_grate's own key. It answers, in one value, the only question
    the accepting case asks: is the grate a real mesh with collision, and how
    far off did it land.

    A KEY THAT IS ABSENT WHEN THE THING FAILED IS NOT A KEY. Every path
    produces a word here, including the path where the asset was never
    reached at all, because "no propAcceptingCase on the line" and "the grate
    is fine" look identical to a grep.

    THE PER-MESH KEYS ARE NAMED DIFFERENTLY FROM THE WHOLE-RUN ONES on
    purpose: simplePrims and collidable here, propCollisionPrims and
    propCollidable on the done line. Run 3 printed collisionPrims=-1 here
    beside propCollisionPrims=0/15 there, one name over two populations and
    two meanings, which is the merge instruments.md warns about. The -1 was
    not a missing-key default either: it was the engine's own refusal
    sentinel passed through as if it were a count. A count that could not be
    read now prints the words nothing-measured and the name that refused."""
    for r in readings:
        if r.get("asset") == ACCEPTING_ASSET:
            return ("propAcceptingCase=piece=%s/asset=%s/RESOLVED/saved=%s/"
                    "simplePrims=%s/collidable=%s/bodySetup=%s/traceFlag=%s/"
                    "sourceParts=%s/materialSlots=%d/worstOrderedMm=%.4f/"
                    "worstSortedMm=%.4f"
                    % (ACCEPTING_PIECE, ACCEPTING_ASSET,
                       "yes" if r.get("saved") else "NO",
                       prims_word(r.get("simplePrims"), r.get("simplePrimsVia")),
                       flat(r.get("collidable", "nothing-measured")),
                       flat(r.get("bodySetup", "nothing-measured")),
                       short_flag(r.get("traceFlag")),
                       r.get("sourceParts", "nothing-measured"),
                       r.get("materialSlots", -1),
                       r.get("worstOrderedMm", -1.0), r.get("worstSortedMm", -1.0)))
    for a, w in failures:
        if a == ACCEPTING_ASSET:
            return ("propAcceptingCase=piece=%s/asset=%s/FAILED/%s"
                    % (ACCEPTING_PIECE, ACCEPTING_ASSET,
                       str(w).replace(" ", "~")))
    return ("propAcceptingCase=piece=%s/asset=%s/NOT-REACHED/sourcesFound=%d"
            % (ACCEPTING_PIECE, ACCEPTING_ASSET, sources_found))


def manifest(measured_by, spec_path, asked, readings, failures, extras):
    """What does not fit on a line, as JSON, committed by the workflow.

    measured_by is the first field and it is load-bearing: the container can
    only measure the GLB against the spec, and only a run can measure the
    engine. A file that says container-glb-only is not a file about a run."""
    return {
        "schema": "ledger.prop-mesh-import/1",
        "measuredBy": measured_by,
        "specPath": spec_path,
        "packageDir": PACKAGE_DIR,
        "namePattern": UASSET_PREFIX + "<asset>",
        "scalePolicy": "1, never scaled, the spec box IS the GLB's measured size",
        "placement": ("the loaded mesh's own bounds centre goes at the piece's "
                      "x_m/y_m/z_m, which is held_props.pivot_note in "
                      "production/specs/vignette-scene.json"),
        "assetsAsked": [a for a, _ in asked],
        "piecesPerAsset": dict((a, len(n)) for a, n in asked),
        "extraAssets": list(EXTRA_ASSETS),
        "readings": readings,
        "failures": [{"asset": a, "why": w} for a, w in failures],
        "extras": extras,
    }


# ---- the container half: the GLB against the spec -------------------------


def measure_against_glb(spec, glb_stats):
    """Does the street's box equal the GLB's own measured size, per asset?

    glb_stats is passed in rather than imported here so that this function is
    testable and so that nothing in this file depends on tools/meshgen being
    importable inside the editor's embedded interpreter, where it is not
    needed and may not be."""
    boxes, _ = box_per_asset(spec)
    rows = []
    for asset_id, _names in assets_asked(spec):
        src = os.path.join(repo_root(), glb_source(asset_id))
        if not os.path.exists(src):
            rows.append({"asset": asset_id, "why": "no-glb-on-disk"})
            continue
        st = glb_stats(src)
        d = delta_mm(st["dims_m"], boxes[asset_id])
        rows.append({
            "asset": asset_id,
            "specBoxM": [round(v, 6) for v in boxes[asset_id]],
            "glbDimsM": [round(float(v), 6) for v in st["dims_m"]],
            "deltaMm": [round(v, 4) for v in d],
            "worstMm": round(max(d), 4),
            "baseY": round(float(st["base_y"]), 6),
            "verts": st["verts"],
            "tris": st["tris"],
            "bytes": st["bytes"],
            # THE TWO READERS, SIDE BY SIDE. meshgen's count and this file's
            # own, because the engine half cannot import meshgen and a second
            # reader nobody cross-checks is a second reader that drifts.
            "sourceMeshes": st["meshes"],
            "sourceMeshNames": glb_mesh_names(src),
        })
    return rows


def load_spec(path=None):
    p = path or os.path.join(repo_root(), "production", "specs",
                             "vignette-pieces.json")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f), p


# ---- the selftest, which runs with no engine anywhere near it -------------


def _stand_in_engine(mode):
    """A STAND-IN FOR `unreal`, AND IT PROVES EXACTLY ONE THING: that the
    collision flow in this file RUNS, in each of the worlds it was written for,
    and produces the words the verdict prints.

    WHAT IT DOES NOT PROVE, stated here so that no reading of this section can
    be mistaken for a reading of the engine: nothing whatever about Unreal. The
    property names, the enum spelling and whether KBoxElem exists are the
    engine's business and only a run can answer them. This is a guard against a
    typo in a refusal path costing a twenty minute round trip, which is the
    only thing the container can be guarded against here.

    Four worlds, and the second is run 3's:
      box-works      the element list is readable and writable, so a box lands
      all-refuse     the subsystem is None and the legacy library answers -1,
                     exactly as run 3 measured, and the element lists refuse
      blind          even the body setup's properties refuse
      no-kboxelem    the count reads a real zero and no add route exists
    """
    class Obj(object):
        def __init__(self, **kw):
            self._d = dict(kw)

        def get_editor_property(self, n):
            if n not in self._d:
                raise RuntimeError("no-property/" + n)
            return self._d[n]

        def set_editor_property(self, n, v):
            self._d[n] = v
            return True

    class Blind(Obj):
        def get_editor_property(self, n):
            raise RuntimeError("binding-refuses/" + n)

    agg = Obj(**dict((n, []) for n in AGG_ELEM_LISTS))
    bs = Obj(agg_geom=(Blind() if mode == "all-refuse" else agg),
             collision_trace_flag="CollisionTraceFlag.CTF_USE_DEFAULT")
    if mode == "blind":
        bs = Blind()
    mesh = Obj(body_setup=bs)

    class Engine(object):
        class StaticMeshEditorSubsystem(object):
            pass

        class BodySetup(object):
            pass

        class CollisionTraceFlag(object):
            CTF_USE_DEFAULT = "CollisionTraceFlag.CTF_USE_DEFAULT"
            CTF_USE_COMPLEX_AS_SIMPLE = "CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE"

        class ScriptingCollisionShapeType(object):
            BOX = "BOX"

        class EditorStaticMeshLibrary(object):
            # THE SENTINEL, AS MEASURED. Both calls answered -1 in run 3.
            @staticmethod
            def get_simple_collision_count(m):
                return -1

            @staticmethod
            def add_simple_collisions(m, t):
                return -1

        class Vector(object):
            def __init__(self, x, y, z):
                self.x, self.y, self.z = x, y, z

        class KBoxElem(Obj):
            def __init__(self):
                Obj.__init__(self, center=None, x=0.0, y=0.0, z=0.0)

        @staticmethod
        def get_editor_subsystem(cls):
            return None

        @staticmethod
        def new_object(cls, outer=None):
            return bs

    if mode == "no-kboxelem":
        del Engine.KBoxElem
    return Engine, mesh


def selftest():
    """Accepting case first in every section, and the live repository is the
    accepting fixture for everything that checks the project itself, so doing
    the work this tool prompts can never break this tool. The rejecting
    fixtures are planted, because a repository with a rescaled prop in it is
    not a repository anybody wants."""
    checks = [0]
    bad = []

    def ok(name, cond, detail=""):
        checks[0] += 1
        if not cond:
            bad.append("FAIL: %s%s" % (name, (" [" + str(detail) + "]") if detail else ""))

    root = repo_root()

    # -- A. THE LIVE SPEC, WHICH IS THE ACCEPTING CASE ---------------------
    spec_path = os.path.join(root, "production", "specs", "vignette-pieces.json")
    if not os.path.exists(spec_path):
        print("import_prop_meshes --selftest: NOTHING MEASURED, no %s" % spec_path)
        return 1
    spec, _ = load_spec(spec_path)
    pieces = mesh_pieces(spec)
    asked = assets_asked(spec)
    ok("the live spec has mesh-kind pieces at all", len(pieces) > 0, len(pieces))
    ok("and the header count agrees with the pieces read",
       spec.get("counts", {}).get("props_asked") == len(pieces),
       "%s vs %d" % (spec.get("counts", {}).get("props_asked"), len(pieces)))
    ok("unique assets is at most the piece count and above zero",
       0 < len(asked) <= len(pieces), "%d/%d" % (len(asked), len(pieces)))
    boxes, disagree = box_per_asset(spec)
    ok("no asset is asked for at two different sizes (the dims policy)",
       disagree == [], disagree)
    ok("every asset id can become a package name",
       all(safe_asset_id(a) for a, _ in asked),
       [a for a, _ in asked if not safe_asset_id(a)])

    missing = [a for a, _ in asked
               if not os.path.exists(os.path.join(root, glb_source(a)))]
    ok("every GLB the street asks for is on disk", missing == [], missing)
    for extra in EXTRA_ASSETS:
        ok("the extra asset %s is on disk" % extra,
           os.path.exists(os.path.join(root, glb_source(extra))),
           glb_source(extra))

    # -- A2. THE ACCEPTING CASE IS A REAL PIECE OF THE BUILT STREET --------
    # Retargeted 2026-09-08. The previous accepting case named a file no piece
    # references, which is why it was never reachable; this one is checked
    # against the live spec so that it cannot quietly stop being real.
    grate = [p for p in pieces if p.get("name") == ACCEPTING_PIECE]
    ok("the accepting piece %s is in the street" % ACCEPTING_PIECE,
       len(grate) == 1, len(grate))
    if grate:
        ok("and it is a mesh piece naming %s" % ACCEPTING_ASSET,
           grate[0].get("shape") == "mesh" and grate[0].get("asset") == ACCEPTING_ASSET,
           "%s/%s" % (grate[0].get("shape"), grate[0].get("asset")))
        ok("and it had a box in the frame to replace, which is what makes it "
           "reachable at all",
           grate[0].get("asset") in dict(asked), grate[0].get("asset"))

    # -- A3. THE THREE FACTS RUN 1 COULD NOT TELL APART --------------------
    # ACCEPTING CASE FIRST: an engine that says it can translate is PRESENT,
    # whatever the plugin listing looked like.
    ok("an engine that can translate reads PRESENT",
       gltf_verdict(True, [], 3, 3).startswith("PRESENT/"), gltf_verdict(True, [], 3, 3))
    # THE READING RUN 1 ACTUALLY HAD, planted: exporter present, no importer
    # plugin, nothing translatable.
    ok("exporter-only reads ABSENT and says exporter-only",
       gltf_verdict(True, [], 0, 3) == "ABSENT/exporter-only/no-importer-plugin-and-translate-said-no",
       gltf_verdict(True, [], 0, 3))
    ok("and it does NOT read the same as no plugin of either kind",
       gltf_verdict(True, [], 0, 3) != gltf_verdict(False, [], 0, 3))
    ok("an importer plugin that still refuses is REFUSED, not ABSENT",
       gltf_verdict(True, ["InterchangeGLTF"], 0, 3).startswith("REFUSED/"),
       gltf_verdict(True, ["InterchangeGLTF"], 0, 3))
    # THE INPUT THAT WOULD HAVE UNDONE ALL FOUR WORDS. Accepting case first:
    # an Interchange plugin IS an importer candidate even though its name
    # contains no GLTF, so an Interchange engine that refuses reads REFUSED
    # and not ABSENT/exporter-only.
    ok("an Interchange plugin counts as an importer candidate",
       importer_candidates(["GLTFExporter", "InterchangeEditor"]) == ["InterchangeEditor"],
       importer_candidates(["GLTFExporter", "InterchangeEditor"]))
    ok("and an exporter alone yields no candidate at all",
       importer_candidates(["GLTFExporter"]) == [],
       importer_candidates(["GLTFExporter"]))
    ok("so an Interchange engine that refuses reads REFUSED, not exporter-only",
       gltf_verdict(True, importer_candidates(["GLTFExporter", "InterchangeEditor"]),
                    0, 3).startswith("REFUSED/"),
       gltf_verdict(True, importer_candidates(["GLTFExporter", "InterchangeEditor"]), 0, 3))
    ok("while an exporter-only engine still reads exporter-only",
       gltf_verdict(True, importer_candidates(["GLTFExporter"]), 0, 3)
       == "ABSENT/exporter-only/no-importer-plugin-and-translate-said-no",
       gltf_verdict(True, importer_candidates(["GLTFExporter"]), 0, 3))
    ok("a question never put reads nothing-measured, not absent",
       gltf_verdict(False, [], 0, 0).startswith("NOTHING-MEASURED/"),
       gltf_verdict(False, [], 0, 0))
    ok("all four words are distinct, which is the whole point of the key",
       len(set([gltf_verdict(True, [], 3, 3), gltf_verdict(True, [], 0, 3),
                gltf_verdict(True, ["x"], 0, 3), gltf_verdict(False, [], 0, 0)])) == 4)

    # -- A4. THE ACCEPTING CASE ALWAYS PRODUCES A WORD ---------------------
    good = bounds_reading(ACCEPTING_ASSET, (0.4, 0.015, 0.4), (0, 0, 0),
                          (20.0, 20.0, 0.75))
    good["saved"] = True
    good["simplePrims"] = 1
    good["simplePrimsVia"] = "agg-geom-elems"
    good["collidable"] = collidable_word("present", 1, "CTF_USE_DEFAULT",
                                         (20.0, 20.0, 0.75))
    good["bodySetup"] = "present"
    good["traceFlag"] = "CollisionTraceFlag.CTF_USE_DEFAULT"
    good["sourceParts"] = 1
    good["materialSlots"] = 1
    ok("a resolved grate says RESOLVED with its collision count",
       "RESOLVED" in accepting_field([good], [], 16)
       and "simplePrims=1" in accepting_field([good], [], 16),
       accepting_field([good], [], 16))
    # THE RUN-3 READING, PLANTED: nothing could read a count. The accepting
    # case must say so in words, and it must not print a number of any kind,
    # because -1 is what it printed last time and -1 read as a count.
    blind = dict(good)
    blind["simplePrims"] = None
    blind["simplePrimsVia"] = "none-of-3-candidates"
    blind["collidable"] = collidable_word("present", None, None, (20.0, 20.0, 0.75))
    blind["traceFlag"] = None
    f_good, f_blind = accepting_field([good], [], 16), accepting_field([blind], [], 16)
    ok("a grate whose count nothing could read says nothing-measured and names "
       "the refusal, where run 3 printed collisionPrims=-1",
       "simplePrims=nothing-measured/none-of-3-candidates" in f_blind
       and "-1" not in f_blind, f_blind)
    ok("and the answering and refusing readings are DIFFERENT strings, which "
       "is the whole falsifiable point", f_good != f_blind,
       "%s vs %s" % (f_good, f_blind))
    ok("the accepting case carries the collidable word, the body setup and the "
       "trace flag, because the primitive count is only a proxy",
       "collidable=YES/simple-prims=1" in f_good and "bodySetup=present" in f_good
       and "traceFlag=CTF_USE_DEFAULT" in f_good, f_good)
    ok("a failed grate says FAILED and carries the reason",
       "FAILED/why" in accepting_field([], [(ACCEPTING_ASSET, "why")], 16),
       accepting_field([], [(ACCEPTING_ASSET, "why")], 16))
    ok("a grate nothing reached still prints a key, because a missing key and "
       "a healthy grate look identical to a grep",
       accepting_field([], [], 0).endswith("NOT-REACHED/sourcesFound=0"),
       accepting_field([], [], 0))
    ok("and every one of the three names the piece and the asset",
       all(ACCEPTING_PIECE in f and ACCEPTING_ASSET in f for f in
           (accepting_field([good], [], 16),
            accepting_field([], [(ACCEPTING_ASSET, "why")], 16),
            accepting_field([], [], 0))))

    # -- B. THE SPEC BOX IS THE GLB'S OWN MEASURED SIZE --------------------
    # The one claim that makes scale 1 correct. Measured, not assumed, and it
    # uses tools/meshgen's GLB reader rather than a second one written here:
    # that reader composes node transforms, and the fault it exists for is
    # reading accessor min/max without them, which reports a traffic cone as
    # three millimetres tall.
    sys.path.insert(0, os.path.join(root, "tools", "meshgen"))
    try:
        import meshgen
    except Exception as e:  # pragma: no cover - reported, never swallowed
        meshgen = None
        bad.append("FAIL: tools/meshgen is not importable, so the spec-box "
                   "claim was NOT measured [%s]" % e)
        checks[0] += 1
    if meshgen is not None:
        rows = measure_against_glb(spec, meshgen.glb_stats)
        measured = [r for r in rows if "worstMm" in r]
        ok("every asset was measured against its GLB",
           len(measured) == len(asked), "%d of %d" % (len(measured), len(asked)))
        worst = max([r["worstMm"] for r in measured] or [9e9])
        ok("the spec box IS the GLB measured size, within %.3f mm, over %d assets"
           % (SPEC_VS_GLB_TOL_MM, len(measured)),
           worst <= SPEC_VS_GLB_TOL_MM,
           "worst %.4f mm" % worst)
        # A PIVOT THAT IS NOT AT THE BASE IS THE REASON THE CORRECTION EXISTS,
        # so the accepting case asserts the population CONTAINS both kinds.
        # A run where every prop happened to be base-pivoted would pass a
        # placement test that ignored the pivot entirely.
        off = [r["asset"] for r in measured if abs(r["baseY"]) > 0.01]
        ok("the population contains props whose pivot is NOT at the base, "
           "which is what the correction is for", len(off) >= 3, off)
        # B2. THE TWO GLB READERS, CROSS-CHECKED ON EVERY SHIPPED FILE.
        # glb_mesh_names() exists because the engine half cannot import
        # meshgen, and a second reader nobody checks is a second reader that
        # drifts. This is the accepting case: the live library.
        drift = [(r["asset"], r["sourceMeshes"], r["sourceMeshNames"])
                 for r in measured
                 if r["sourceMeshNames"] is None
                 or len(r["sourceMeshNames"]) != r["sourceMeshes"]]
        ok("both GLB readers agree on the mesh count for all %d assets"
           % len(measured), drift == [], drift)
        # AND THE REJECTING FIXTURE: a file that is not a GLB reads as None,
        # which is nothing-measured and not a count of zero.
        ok("a file that is not a GLB reads as None, not as zero meshes",
           glb_mesh_names(spec_path) is None, glb_mesh_names(spec_path))
        ok("and a path that does not exist does the same",
           glb_mesh_names(os.path.join(root, "no-such-file.glb")) is None)
        # THE ACCEPTING ASSET'S OWN SOURCE, because a multi-part grate would
        # make the accepting case unreachable the way pavement_sign is.
        acc = [r for r in measured if r["asset"] == ACCEPTING_ASSET]
        ok("the accepting asset's source holds exactly one mesh, so one uasset "
           "is the whole prop", len(acc) == 1 and acc[0]["sourceMeshes"] == 1,
           [(r["asset"], r["sourceMeshes"]) for r in acc])
        # THE SERIES, PRINTED AND NOT GATED. Run 3 kept one mesh per asset and
        # silently left the others behind; --measure prints the whole column.
        multi_src = sorted((r["asset"], r["sourceMeshes"]) for r in measured
                           if r["sourceMeshes"] > 1)
        ok("the multi-mesh sources are READABLE in the container, which is "
           "what makes propSourcePartsWhich checkable before a run",
           all(isinstance(n, int) for _a, n in multi_src), multi_src)

    # -- C. THE NAME CONTRACT WITH THE C++, READ OUT OF THE C++ ------------
    cpp = os.path.join(root, "ue-probe", "Source", "LedgerProbe", "Private",
                       "VignetteShot.cpp")
    if not os.path.exists(cpp):
        ok("VignetteShot.cpp is where the mesh branch lives", False, cpp)
    else:
        text = open(cpp, "r", encoding="utf-8").read()
        m = re.search(r'kPropPackageDir\s*=\s*TEXT\("([^"]*)"\)', text)
        ok("the C++ declares kPropPackageDir", m is not None)
        if m:
            ok("and it is the directory this script writes into",
               m.group(1) == PACKAGE_DIR, "%s vs %s" % (m.group(1), PACKAGE_DIR))
        m = re.search(r'kPropNamePrefix\s*=\s*TEXT\("([^"]*)"\)', text)
        ok("the C++ declares kPropNamePrefix", m is not None)
        if m:
            ok("and it is the prefix this script writes",
               m.group(1) == UASSET_PREFIX, "%s vs %s" % (m.group(1), UASSET_PREFIX))
        ok("the C++ still has a mesh branch to wire", 'P.Shape == "mesh"' in text)

    # -- D. THE STATUS WORD, ACCEPTING CASE FIRST --------------------------
    ok("a full import with collision is IMPORTED",
       import_status(16, 16, 16, 16, 16) == "IMPORTED")
    ok("and it returns 0", import_return("IMPORTED") == 0)
    ok("a full import with no collision is not IMPORTED",
       import_status(16, 16, 16, 16, 0) == "IMPORTED-NO-COLLISION")
    ok("and it returns non-zero, because a mesh with no body setup lets a "
       "walking Character through it",
       import_return(import_status(16, 16, 16, 16, 0)) != 0)
    ok("one asset short is PARTIAL", import_status(16, 16, 15, 15, 15) == "PARTIAL")
    ok("nothing imported says so", import_status(16, 16, 0, 0, 0) == "NOTHING-IMPORTED")
    ok("no GLBs says that instead", import_status(16, 0, 0, 0, 0) == "NO-SOURCES")
    ok("nothing asked is not a pass-shaped word",
       import_status(0, 0, 0, 0, 0) == "NOTHING-ASKED")
    ok("and every non-IMPORTED word returns non-zero",
       all(import_return(w) != 0 for w in
           ("PARTIAL", "NOTHING-IMPORTED", "NO-SOURCES", "NOTHING-ASKED",
            "IMPORTED-NO-COLLISION", "IMPORTED-COLLISION-UNREADABLE")))
    # D2. THE WORD RUN 3 COULD NOT SAY. It printed PARTIAL over a missing
    # asset, but had every asset landed it would have said IMPORTED-NO-
    # COLLISION over fifteen meshes whose collision state nothing had read.
    # "measured a failure" and "could not measure" are different words now.
    ok("an unreadable collision state is its own word, not a failure",
       import_status(16, 16, 16, 16, 0, 16) == "IMPORTED-COLLISION-UNREADABLE")
    ok("and it returns non-zero, because a run that cannot tell has not proved "
       "the walk clip anything",
       import_return(import_status(16, 16, 16, 16, 0, 16)) != 0)
    ok("a KNOWN walk-through outranks an unreadable one in the word, because "
       "that mesh is a measured defect",
       import_status(16, 16, 16, 16, 10, 3) == "IMPORTED-NO-COLLISION")
    ok("every mesh collidable and none unreadable is still IMPORTED",
       import_status(16, 16, 16, 16, 16, 0) == "IMPORTED")
    ok("and the three collision outcomes are three different words",
       len(set([import_status(16, 16, 16, 16, 16, 0),
                import_status(16, 16, 16, 16, 0, 16),
                import_status(16, 16, 16, 16, 10, 3)])) == 3)

    # -- D3. COLLIDABILITY, WHICH IS THE QUESTION THE PRIMITIVE COUNT ONLY
    # PROXIES FOR. Accepting case first: one box is collidable.
    ext = (20.0, 20.0, 0.75)
    ok("a mesh with a simple primitive is collidable",
       collidable_word("present", 1, "CTF_USE_DEFAULT", ext) == "YES/simple-prims=1",
       collidable_word("present", 1, "CTF_USE_DEFAULT", ext))
    # THE CASE THAT BREAKS THE PROXY, and it is the reason this key exists: a
    # flat grate set to use its own triangles collides perfectly and reports
    # ZERO simple primitives. propCollisionPrims would call that a failure.
    ok("a mesh with ZERO primitives and complex-as-simple is collidable anyway",
       collidable_word("present", 0, "CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE",
                       ext).startswith("YES/complex-as-simple"),
       collidable_word("present", 0, "CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE", ext))
    ok("but complex-as-simple over EMPTY bounds is not, because there are no "
       "triangles for a sweep to hit",
       collidable_word("present", 0, "CTF_USE_COMPLEX_AS_SIMPLE",
                       (0.0, 0.0, 0.0)).startswith("NO/"),
       collidable_word("present", 0, "CTF_USE_COMPLEX_AS_SIMPLE", (0.0, 0.0, 0.0)))
    ok("zero primitives and a flag that needs them is a measured NO",
       collidable_word("present", 0, "CTF_USE_DEFAULT", ext)
       == "NO/no-simple-prims/flag=CTF_USE_DEFAULT",
       collidable_word("present", 0, "CTF_USE_DEFAULT", ext))
    ok("no body setup at all is a measured NO and says which",
       collidable_word("absent", None, None, ext) == "NO/no-body-setup")
    ok("and a body setup that could not even be MADE is the same measured NO, "
       "not an unknown, because that mesh has nowhere for collision to live",
       collidable_word("absent/could-not-make/new-object-body-setup", None,
                       None, ext) == "NO/no-body-setup")
    ok("while a body setup nothing could READ is UNKNOWN, which is the other "
       "fault in the same place",
       collidable_word("unread", None, None, ext).startswith("UNKNOWN/"),
       collidable_word("unread", None, None, ext))
    # RUN 3'S ACTUAL STATE, PLANTED. Nothing could read either half, and the
    # word for that is UNKNOWN. It must not read as the NO above.
    unknown = collidable_word("present", None, None, ext)
    ok("a count and a flag nothing could read is UNKNOWN, never NO",
       unknown.startswith("UNKNOWN/nothing-measured"), unknown)
    ok("and UNKNOWN is a different string from both NO and YES, which is what "
       "run 3's zero could not be",
       len(set([unknown, collidable_word("present", 0, "CTF_USE_DEFAULT", ext),
                collidable_word("present", 1, "CTF_USE_DEFAULT", ext)])) == 3)
    ok("a readable flag with an unreadable count still names the flag",
       "flag=CTF_USE_DEFAULT" in collidable_word("present", None, "CTF_USE_DEFAULT", ext),
       collidable_word("present", None, "CTF_USE_DEFAULT", ext))
    # THE ENUM SPELLING, BOTH WAYS ROUND, because this container cannot run the
    # binding that decides which one the engine prints.
    ok("the engine's Python spelling of complex-as-simple is recognised",
       is_complex_as_simple("CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE"))
    ok("and the C++ spelling is too", is_complex_as_simple("CTF_UseComplexAsSimple"))
    ok("while simple-as-complex, which is the opposite setting, is NOT",
       not is_complex_as_simple("CTF_UseSimpleAsComplex"))
    ok("nor is use-default", not is_complex_as_simple("CTF_USE_DEFAULT"))
    ok("and nothing-measured is not a flag value",
       not is_complex_as_simple(None) and short_flag(None) == "nothing-measured")

    # -- D4. THE COUNT THAT COULD NOT BE READ, WHICH IS FAULT 2 -------------
    # ACCEPTING CASE FIRST: a route that answers prints the number.
    ok("a route that answers a real count prints that count",
       prims_word(2, "agg-geom-elems") == "2", prims_word(2, "agg-geom-elems"))
    ok("and a route that answers ZERO prints zero, because zero primitives is "
       "a real reading", prims_word(0, "agg-geom-elems") == "0")
    # THE REFUSAL, PLANTED. This is the string run 3 should have printed.
    ok("a route that refuses prints nothing-measured and names the refusal",
       prims_word(None, "none-of-3-candidates")
       == "nothing-measured/none-of-3-candidates",
       prims_word(None, "none-of-3-candidates"))
    ok("and the answering and refusing strings are DIFFERENT, which is the "
       "whole of rule 3b here",
       prims_word(0, "legacy-library") != prims_word(None, "legacy-library"))
    # AND IT IS NOT A NUMBER. A value a reader can int() is a value a tally
    # will absorb, which is exactly how -1 became 0/15 on run 3's done line.
    def parses_as_int(s):
        try:
            int(s)
            return True
        except ValueError:
            return False
    ok("an answered count parses as a number", parses_as_int(prims_word(0, "x")))
    ok("and a refusal never does, so no tally can absorb it",
       not parses_as_int(prims_word(None, "none-of-3-candidates")),
       prims_word(None, "none-of-3-candidates"))
    ok("the -1 run 3 printed is not a reading any route can return now: a "
       "negative is rejected as a sentinel and reads as nothing-measured",
       prims_word(None, "legacy-library-refused-with-sentinel/-1")
       .startswith("nothing-measured/"))

    # -- D5. THE WHOLE-RUN BLOCK, AND ITS DENOMINATORS ----------------------
    # crowd_control_barrier's own numbers, read out of the spec file, so the
    # fixture is a real prop's proportions rather than an invented one.
    cbox = (2.291, 1.136, 0.395)
    chalf = tuple(v * CENTIMETRES_PER_METRE / 2.0 for v in expected_ue_size_m(cbox))

    def reading_with(asset, prims, via, flag, answers, saved=True, add="agg-geom-box"):
        r = bounds_reading(asset, cbox, (0, 0, 0), chalf)
        r["saved"] = saved
        r["simplePrims"] = prims
        r["simplePrimsVia"] = via
        r["simplePrimsAnswers"] = answers
        r["collisionAddVia"] = add
        r["bodySetup"] = "present"
        r["traceFlag"] = flag
        r["collidable"] = collidable_word("present", prims, flag, chalf)
        return r
    # ACCEPTING CASE: three meshes, each with a box two routes agree on.
    healthy = [reading_with("a%d" % i, 1, "agg-geom-elems", "CTF_USE_DEFAULT",
                            {"agg-geom-elems": 1, "legacy-library": 1})
               for i in range(3)]
    fh = collision_field(healthy, 3)
    ok("a healthy collision block counts the primitives and the collidables "
       "over the saved meshes",
       "propCollisionPrims=3/3" in fh and "propCollidable=3/3" in fh
       and "propCollidableUnknown=0/3" in fh, fh)
    ok("and it says out loud that the primitive count is a proxy",
       "A-PROXY-NOT-THE-QUESTION" in fh and "NOT-a-sweep" in fh, fh)
    ok("and two routes agreeing is counted, because one route answering alone "
       "is weaker evidence", "propCollisionAgree=agree=3;" in fh, fh)
    # RUN 3, PLANTED IN FULL: every route refused on every mesh.
    blind3 = [reading_with("a%d" % i, None, "none-of-3-candidates", None,
                           {"legacy-library": "refused-with-sentinel/-1"},
                           add="none-of-3-candidates")
              for i in range(3)]
    fb = collision_field(blind3, 3)
    ok("run 3's reading now counts as unread and unknown, not as zero "
       "collision", "propCollisionPrimsUnread=3/3" in fb
       and "propCollidableUnknown=3/3" in fb, fb)
    ok("and propCollisionPrims=0/3 no longer stands alone, because the unread "
       "count sits beside it", "propCollisionPrims=0/3" in fb
       and "propCollisionPrimsUnread=3/3" in fb, fb)
    ok("the healthy and the blind blocks are DIFFERENT strings", fh != fb)
    ok("no route answering at all is counted apart from routes disagreeing",
       "agree=0;disagree=0;one-route=0;no-route=3/over=3" in fb, fb)
    # THE MESH THAT WAS SAVED AND NEVER MEASURED. It is in the denominator and
    # it is UNKNOWN: dropping it would make 2/2 out of three meshes.
    yes_n, unk_n, no_n, m = collidable_tally(healthy, 4)
    ok("a saved package with no reading at all is UNKNOWN and stays in the "
       "denominator", (yes_n, unk_n, no_n, m) == (3, 1, 0, 4),
       (yes_n, unk_n, no_n, m))
    ok("and the block's denominator is propSaved, not the number of readings",
       "propCollidable=3/4" in collision_field(healthy, 4),
       collision_field(healthy, 4))
    ok("a mesh with no simple primitive and a complex-as-simple flag is "
       "collidable on the block too, which is the proxy's blind spot",
       "propCollidable=1/1" in collision_field(
           [reading_with("g", 0, "agg-geom-elems", "CTF_USE_COMPLEX_AS_SIMPLE",
                         {"agg-geom-elems": 0})], 1)
       and "propCollisionPrims=0/1" in collision_field(
           [reading_with("g", 0, "agg-geom-elems", "CTF_USE_COMPLEX_AS_SIMPLE",
                         {"agg-geom-elems": 0})], 1),
       collision_field([reading_with("g", 0, "agg-geom-elems",
                                     "CTF_USE_COMPLEX_AS_SIMPLE",
                                     {"agg-geom-elems": 0})], 1))
    ok("nothing saved says nothing-measured with its own zero denominator, "
       "never 0/0 dressed as a pass",
       "propCollidable=nothing-measured/0-saved-meshes" in collision_field([], 0),
       collision_field([], 0))
    ok("two routes that disagree are counted as a disagreement, because a "
       "legacy library forwarding to a dead subsystem can answer plausibly",
       "disagree=1" in collision_field(
           [reading_with("d", 1, "agg-geom-elems", "CTF_USE_DEFAULT",
                         {"agg-geom-elems": 1, "legacy-library": 0})], 1),
       collision_field([reading_with("d", 1, "agg-geom-elems", "CTF_USE_DEFAULT",
                                     {"agg-geom-elems": 1, "legacy-library": 0})], 1))

    # -- D6. THE NOTE, WHICH RUN 3 SPENT ON REPEATS -------------------------
    rep = (["subsystem-count-refused=returned-None"] * 15
           + ["legacy-library-count-refused-with-sentinel=-1"] * 15
           + ["rename-refused=x"] + ["a-fourth=y"] + ["a-fifth=z"])
    nv = note_value(rep)
    ok("the note counts repeats instead of spending its cap on them",
       "subsystem-count-refused=returned-None~x15" in nv, nv)
    ok("and five distinct causes under a cap of four announce the cap",
       "(+1~more~not~shown)" in nv, nv)
    ok("run 3's note had room for two causes; this one has four",
       nv.count("~x") >= 3, nv)
    ok("no refusals at all is the word none, not an empty value",
       note_value([]) == "none")
    ok("and a refusal with spaces in it is flattened",
       " " not in note_value(["'NoneType' object has no attribute get"]),
       note_value(["'NoneType' object has no attribute get"]))

    # -- D7. HOW MANY MESHES THE SOURCE FILE HOLDS --------------------------
    # ACCEPTING CASE: every source holds one mesh, so nothing is left behind.
    ones = source_parts_field([("a", 1), ("b", 1), ("c", 1)])
    ok("sources that hold one mesh each print a zero with its denominator",
       "propSourcePartsOver1=0/3" in ones and "propSourcePartsWhich=none" in ones,
       ones)
    # THE RUN-3 POPULATION, PLANTED FROM THE CONTAINER'S OWN MEASUREMENT.
    three_kinds = source_parts_field([("pavement_sign", 3), ("swing_bin", 2),
                                      ("wooden_crate_01", 2), ("pallet", 1)])
    ok("a multi-mesh source is counted and named",
       "propSourcePartsOver1=3/4" in three_kinds
       and "pavement_sign=3" in three_kinds, three_kinds)
    ok("and the two readings are different strings", ones != three_kinds)
    ok("a GLB that could not be read is counted apart from one mesh",
       "propSourcePartsUnread=1/2" in source_parts_field([("a", 1), ("b", None)]),
       source_parts_field([("a", 1), ("b", None)]))
    ok("nothing measured says so rather than printing 0/0",
       "propSourcePartsOver1=nothing-measured" in source_parts_field([]))
    ok("and the key names what it is a statistic of",
       "propSourcePartsStat=mesh-nodes-in-the-source-glb-per-asset" in ones, ones)

    # -- D8. THE COLLISION FLOW, RUN AGAINST A STAND-IN ENGINE --------------
    # WHAT THIS SECTION IS FOR, because it is easy to over-read: the refusal
    # paths are the half that ships unrun, and the refusal path is what
    # produced run 3's wrong number. These rows run them. They prove the flow
    # executes and the words come out; they prove NOTHING about Unreal, and
    # _stand_in_engine's docstring says so at greater length.
    bounds = (44.0, 46.2, 50.0)
    states = {}
    notes = {}
    for mode in ("box-works", "all-refuse", "blind", "no-kboxelem"):
        eng, mesh = _stand_in_engine(mode)
        rep = []
        st = _ensure_collision(eng, mesh, (0.0, 0.0, 37.5), bounds, rep)
        st["collidable"] = collidable_word(st["bodySetup"], st["simplePrims"],
                                           st["traceFlag"], bounds)
        st["saved"] = True
        states[mode] = st
        notes[mode] = note_value(rep)
    # ACCEPTING CASE FIRST: a box lands, the count READS BACK, and the trace
    # flag is left alone because write-on-change means not touching a mesh that
    # already collides.
    w = states["box-works"]
    ok("a route that can write a box answers a real count and names itself",
       w["simplePrims"] == 1 and w["collisionAddVia"] == "agg-geom-box"
       and w["collidable"] == "YES/simple-prims=1",
       (w["simplePrims"], w["collisionAddVia"], w["collidable"]))
    ok("and the trace flag is NOT rewritten on a mesh that already collides, "
       "which is write-on-change",
       w["collisionFlagSet"] is False and is_complex_as_simple(w["traceFlag"]) is False,
       (w["collisionFlagSet"], w["traceFlag"]))
    ok("the per-list breakdown travels, so a zero on this route ships the "
       "number of element lists that answered",
       len(w["simplePrimsAnswers"].get("aggPerList") or {}) == len(AGG_ELEM_LISTS),
       w["simplePrimsAnswers"].get("aggPerList"))
    # RUN 3'S WORLD, PLANTED: subsystem None, legacy answering -1, element
    # lists refusing. The count must read nothing-measured and the -1 must be
    # recorded as a SENTINEL rather than believed.
    a = states["all-refuse"]
    ok("in run 3's world the count is nothing-measured, not zero and not -1",
       a["simplePrims"] is None
       and prims_word(a["simplePrims"], a["simplePrimsVia"]).startswith("nothing-measured/"),
       prims_word(a["simplePrims"], a["simplePrimsVia"]))
    ok("and the legacy library's -1 is recorded as a refused sentinel",
       str(a["simplePrimsAnswers"].get("legacy-library")).startswith("refused-with-sentinel"),
       a["simplePrimsAnswers"])
    ok("and the subsystem's refusal names the SUBSYSTEM, not a missing method, "
       "which is what run 3's note said",
       "returned-None" in str(a["simplePrimsAnswers"].get("subsystem")),
       a["simplePrimsAnswers"].get("subsystem"))
    ok("so the mesh is made collidable by the trace flag instead, and the "
       "reason is recorded",
       a["collisionFlagSet"] is True
       and a["collidable"].startswith("YES/complex-as-simple")
       and "unreadable" in a["collisionFlagWhy"],
       (a["collidable"], a["collisionFlagWhy"]))
    # THE WORLD WHERE EVEN THE FALLBACK REFUSES. The word must be UNKNOWN: a
    # run that cannot tell must not print the word for a run that measured.
    b = states["blind"]
    ok("when even the trace flag refuses, the mesh is UNKNOWN and not NO",
       b["collidable"].startswith("UNKNOWN/") and b["collisionFlagSet"] is False,
       (b["collidable"], b["collisionFlagWhy"]))
    ok("and the refusal names which route refused rather than printing a zero",
       "refused=" in b["collisionFlagWhy"] or "refused/" in str(b["simplePrimsAnswers"]),
       (b["collisionFlagWhy"], b["simplePrimsAnswers"]))
    # A REAL ZERO, WHICH IS THE READING THAT MUST NOT LOOK LIKE A REFUSAL: the
    # count answered 0 and no add route existed.
    z = states["no-kboxelem"]
    ok("a count that answers ZERO prints zero, and is a different reading from "
       "a count nothing could read",
       z["simplePrims"] == 0
       and prims_word(z["simplePrims"], z["simplePrimsVia"]) == "0"
       and prims_word(a["simplePrims"], a["simplePrimsVia"]) != "0",
       (prims_word(z["simplePrims"], z["simplePrimsVia"]),
        prims_word(a["simplePrims"], a["simplePrimsVia"])))
    ok("and a zero with no primitive to add still becomes collidable by flag, "
       "with the reason saying it was a zero and not a blank",
       z["collidable"].startswith("YES/complex-as-simple")
       and "no-simple-primitive-could-be-added" in z["collisionFlagWhy"],
       (z["collidable"], z["collisionFlagWhy"]))
    ok("all four worlds produce DIFFERENT collision readings, which is what "
       "makes any of them falsifiable",
       len(set((st["collidable"], prims_word(st["simplePrims"], st["simplePrimsVia"]),
                st["collisionAddVia"]) for st in states.values())) == 4,
       [(m, s["collidable"], s["collisionAddVia"]) for m, s in states.items()])
    ok("every world's note names a cause rather than printing none",
       all(v != "none" for v in notes.values()), notes)
    ok("and five near-identical element-list refusals are ONE cause in the "
       "note, not five, because the cap is four",
       "agg-elems-refused=" in notes["all-refuse"], notes["all-refuse"])
    # AND THE WHOLE-RUN BLOCK OVER THE FOUR, so the tallies are exercised on
    # live state rather than on hand-written fixtures.
    fmix = collision_field(list(states.values()), len(states))
    ok("the block over a mixed population counts three collidable and one "
       "unknown over four",
       "propCollidable=3/4" in fmix and "propCollidableUnknown=1/4" in fmix, fmix)
    ok("and it counts one mesh with a primitive and two whose count was unread",
       "propCollisionPrims=1/4" in fmix and "propCollisionPrimsUnread=2/4" in fmix,
       fmix)
    ok("the status word over that population says UNREADABLE rather than "
       "claiming a failure it did not measure",
       import_status(4, 4, 4, 4, *collidable_tally(list(states.values()), 4)[:2])
       == "IMPORTED-COLLISION-UNREADABLE",
       collidable_tally(list(states.values()), 4))

    # -- E. THE BOUNDS ARITHMETIC ------------------------------------------
    # Accepting case: an engine that returns exactly the spec box, in the axis
    # order this file assumes, reads as zero on both deltas.
    box = (2.291, 1.136, 0.395)          # crowd_control_barrier, from the file
    want = expected_ue_size_m(box)       # (x, z, y) in metres
    half = tuple(v * CENTIMETRES_PER_METRE / 2.0 for v in want)
    r = bounds_reading("accepting", box, (0.0, 0.0, half[2]), half)
    ok("an exact engine reading is 0.0000 mm ordered and sorted",
       r["worstOrderedMm"] == 0.0 and r["worstSortedMm"] == 0.0, r)
    ok("and the local centre is reported in unreal units, not metres",
       r["localCentreUu"][2] == round(half[2], 3), r["localCentreUu"])
    # Rejecting fixture 1: the axis convention is not what this file assumed.
    # Ordered misses, SORTED MATCHES, and that pair is the whole reason both
    # numbers are printed.
    swapped = (half[1], half[0], half[2])
    r2 = bounds_reading("axis-swapped", box, (0, 0, 0), swapped)
    ok("an axis swap shows as an ordered miss", r2["worstOrderedMm"] > 1.0, r2)
    ok("and as a sorted MATCH, which is how a reader tells a wrong axis "
       "convention from a wrong size", r2["worstSortedMm"] == 0.0, r2)
    # Rejecting fixture 2: a mesh that came in at the wrong scale misses both.
    r3 = bounds_reading("scaled", box, (0, 0, 0),
                        tuple(v * 1.1 for v in half))
    ok("a rescaled mesh misses both deltas",
       r3["worstOrderedMm"] > 1.0 and r3["worstSortedMm"] > 1.0, r3)
    ok("the worst axis is named", r3["worstOrderedAxis"] in ("x", "y", "z"))

    # -- E2. THE LOOKUP, WHICH IS WHAT RUN 2 GOT WRONG ---------------------
    # ACCEPTING CASE FIRST: the importer named the asset what we asked for.
    D = PACKAGE_DIR + "/"
    ok("an asset at the exact path resolves by exact-path",
       resolve_imported([D + "SM_drainage_grate_01"], "drainage_grate_01")
       == (D + "SM_drainage_grate_01", "exact-path"),
       resolve_imported([D + "SM_drainage_grate_01"], "drainage_grate_01"))
    # THE THREE SHAPES RUN 2 COULD NOT TELL APART, each planted.
    ok("an asset named after the MESH inside the file still resolves, and says "
       "by which rule",
       resolve_imported([D + "Grate_LOD0_SM_drainage_grate_01"], "drainage_grate_01")[1]
       == "name-contains-the-asset-id",
       resolve_imported([D + "Grate_LOD0_SM_drainage_grate_01"], "drainage_grate_01"))
    ok("an asset nested in a per-source subfolder resolves by name",
       resolve_imported([D + "drainage_grate_01/SM_drainage_grate_01"], "drainage_grate_01")[1]
       == "exact-name-different-folder",
       resolve_imported([D + "drainage_grate_01/SM_drainage_grate_01"], "drainage_grate_01"))
    # A5, RE-EXPECTED. One unrecognisable package is a FAILURE that still
    # reports what appeared, not a match on timing.
    ok("one unrecognised package is a failure naming the leaf, not a match",
       resolve_imported([D + "StaticMeshActor_17"], "drainage_grate_01")
       == (None, "appeared-unnamed/StaticMeshActor_17"),
       resolve_imported([D + "StaticMeshActor_17"], "drainage_grate_01"))

    # A1(a). BOTH SNAPSHOT SHAPES, ACCEPTING CASE FIRST. These two rows are
    # the ones that would have made a healthy run 3 print a false conclusion
    # about run 2.
    ok("a package-name snapshot of a perfect import resolves exact-path",
       resolve_imported([D + "SM_drainage_grate_01"], "drainage_grate_01")[1]
       == "exact-path")
    ok("an OBJECT-PATH snapshot of the same perfect import also resolves "
       "exact-path, which before A1 it did not",
       resolve_imported([D + "SM_drainage_grate_01.SM_drainage_grate_01"],
                        "drainage_grate_01")[1] == "exact-path",
       resolve_imported([D + "SM_drainage_grate_01.SM_drainage_grate_01"],
                        "drainage_grate_01"))
    ok("and package_of leaves a package name alone",
       package_of(D + "SM_a") == D + "SM_a")

    # A1(b). THE SIBLING HAZARD, and what removes it. `new` is sorted, so a
    # material whose leaf sorts before the mesh and contains the asset id
    # would be returned as the mesh. The fix is the StaticMesh filter in
    # _import_one, so the row asserts both halves: the hazard is real on the
    # raw list, and resolving over the FILTERED list gives the mesh.
    # The fixture has the mesh under the INTERNAL mesh's name, because that is
    # the only case in which the sort order can bite: exact-path is tested
    # first, so a mesh actually at the contract path is immune.
    mesh_leaf = D + "SM_grate_body_drainage_grate_01"
    mat_leaf = D + "MI_drainage_grate_01"
    raw = sorted([mat_leaf, mesh_leaf])
    ok("the material sorts before the mesh in this fixture, which is what "
       "makes the hazard reachable at all", raw[0] == mat_leaf, raw)
    ok("unfiltered, that material would be returned AS the mesh (the hazard)",
       resolve_imported(raw, "drainage_grate_01")[0] == mat_leaf,
       resolve_imported(raw, "drainage_grate_01"))
    ok("filtered to the static meshes, the MESH resolves instead",
       resolve_imported([mesh_leaf], "drainage_grate_01")
       == (mesh_leaf, "name-contains-the-asset-id"),
       resolve_imported([mesh_leaf], "drainage_grate_01"))

    # A2. The tally string, which is the only part of the deletion this
    # container can run.
    ok("the preexisting tally ships its denominator",
       preexisting_field(3, 16) == "propImportPreexistingDeleted=3/16",
       preexisting_field(3, 16))
    ok("and a clean slate prints a zero with its denominator, not nothing",
       preexisting_field(0, 16) == "propImportPreexistingDeleted=0/16")
    ok("nothing appearing says nothing-appeared, which is the ONLY reading "
       "that means the import made nothing",
       resolve_imported([], "x") == (None, "nothing-appeared"))
    ok("two unrecognised packages are ambiguous and carry the count, not a guess",
       resolve_imported([D + "a", D + "b"], "x") == (None, "ambiguous-2-appeared/a,b"),
       resolve_imported([D + "a", D + "b"], "x"))
    # RUN 3'S ONE FAILURE, PLANTED FROM THE MANIFEST IT ACTUALLY WROTE.
    # pavement_sign's appearedClasses were basic=MaterialInstanceConstant,
    # hinges=StaticMesh, sign_back=StaticMesh, sign_front=StaticMesh, so the
    # class filter had already done its job and the three left were three real
    # meshes out of one GLB. The refusal is correct and stays; what was
    # missing is that the reason never said WHICH three, which cost a read of
    # the manifest to find out.
    three = [D + "pavement_sign/StaticMeshes/" + n
             for n in ("hinges", "sign_back", "sign_front")]
    got = resolve_imported(three, "pavement_sign")
    ok("three meshes out of one source are still a refusal, never a pick",
       got[0] is None and got[1].startswith("ambiguous-3-appeared/"), got)
    ok("and the refusal NAMES the three, which run 3's reason did not",
       "hinges,sign_back,sign_front" in got[1], got)
    ok("a fourth would announce the cap rather than growing the value",
       "(+1~more~not~shown)" in resolve_imported(three + [D + "zz"], "pavement_sign")[1],
       resolve_imported(three + [D + "zz"], "pavement_sign"))
    ok("a hyphen in the asset id does not defeat the name rule",
       resolve_imported([D + "SM_a_b"], "a-b")[1] == "exact-path",
       resolve_imported([D + "SM_a_b"], "a-b"))

    # -- E3. THE ASYNC DISCRIMINATOR ---------------------------------------
    det_ok = [("a", {"appeared": [D + "SM_a"], "resolvedVia": "exact-path",
                     "routeRan": "asset-import-task", "waitTaken": False,
                     "waitChanged": False})]
    f = lookup_field(det_ok)
    ok("a healthy lookup tallies exact-path and needs no wait",
       "propImportResolvedVia=exact-path=1" in f
       and "propImportWaitTaken=0/1" in f, f)
    det_async = [("a", {"appeared": [D + "SM_a"], "resolvedVia": "exact-path",
                        "routeRan": "interchange-import-asset",
                        "waitTaken": True, "waitChanged": True})]
    f2 = lookup_field(det_async)
    ok("an import that only appeared AFTER the wait prints WaitChanged above "
       "zero, which is the async hypothesis confirmed",
       "propImportWaitTaken=1/1" in f2 and "propImportWaitChanged=1/1" in f2, f2)
    det_dead = [("a", {"appeared": [], "resolvedVia": "nothing-appeared",
                       "routeRan": "interchange-import-asset",
                       "waitTaken": True, "waitChanged": False})]
    f3 = lookup_field(det_dead)
    ok("a wait that changed nothing is silence, not a rule-out, and still "
       "names the route that ran",
       "propImportWaitChanged=0/1" in f3
       and "propImportRouteRan=interchange-import-asset=1" in f3, f3)
    ok("and the three readings are all different, which is the point",
       len(set([f, f2, f3])) == 3)
    ok("a lookup over nothing says nothing-measured and still prints the keys",
       "propImportedNames=nothing-measured" in lookup_field([])
       and "propImportWaitTaken=0/0" in lookup_field([]))
    manyd = [("a%d" % i, {"appeared": [], "resolvedVia": "nothing-appeared",
                          "routeRan": "none"}) for i in range(DETAIL_CAP + 3)]
    ok("a capped names list announces the cap",
       "(+3~more~not~shown)" in lookup_field(manyd), lookup_field(manyd))

    # -- F. THE ZEROS, THE CAPS AND THE NEVER-RAN WORDS --------------------
    ok("a worst-bounds over nothing says nothing-measured",
       "nothing-measured" in worst_bounds([]))
    ok("pivots over nothing says nothing-measured",
       pivot_field([]) == "propPivots=nothing-measured")
    ok("no failures still prints the denominator",
       fallback_field([], 16) == "propFailed=0/16 propFailedWhy=none")
    many = [("a%d" % i, "why%d" % i) for i in range(DETAIL_CAP + 4)]
    f = fallback_field(many, 16)
    ok("a capped failure list announces the cap", "more~not~shown" in f, f)
    ok("and its count is the number withheld, not the total",
       "(+4~more~not~shown)" in f, f)
    rs = [bounds_reading("a%d" % i, box, (0, 0, 0), half)
          for i in range(DETAIL_CAP + 2)]
    ok("a capped pivot list announces the cap too",
       "(+2~more~not~shown)" in pivot_field(rs), pivot_field(rs))

    # -- G. NO SPACES IN ANY VALUE -----------------------------------------
    for r in rs:
        r["saved"] = True
        r["simplePrims"] = 1
        r["simplePrimsVia"] = "agg-geom-elems"
        r["simplePrimsAnswers"] = {"agg-geom-elems": 1, "legacy-library": 1}
        r["collisionAddVia"] = "agg-geom-box"
        r["bodySetup"] = "present"
        r["traceFlag"] = "CollisionTraceFlag.CTF_USE_DEFAULT"
        r["collidable"] = collidable_word("present", 1, r["traceFlag"], half)
    line = prop_line("IMPORTED", 16, 23, 16, 16, len(rs), rs,
                     [("x", "a reason with spaces")], "asset-import-task",
                     collision_field(rs, len(rs)),
                     "propExtras=lamp_post_01=ok", 123456,
                     "a note with spaces",
                     "propGltfImporter=" + gltf_verdict(True, [], 0, 3)
                     + " propGltfCanTranslate=0/3",
                     accepting_field([], [(ACCEPTING_ASSET, "did not load back")], 16),
                     lookup_field([("a", {"appeared": [PACKAGE_DIR + "/SM_a"],
                                          "resolvedVia": "exact-path",
                                          "routeRan": "asset-import-task",
                                          "waitTaken": False,
                                          "waitChanged": False})]),
                     source_parts_field([("a", 1), ("b", 2)]),
                     engine_field(["StaticMeshEditorSubsystem=returned-None"],
                                  ["InterchangeGenericMeshPipeline=2-of-80:"
                                   "import_collision,combine_static_meshes"]))
    toks = line.split()
    ok("every whitespace-separated token of the verdict line is key=value",
       all("=" in t for t in toks), [t for t in toks if "=" not in t])
    ok("and a reason containing spaces was flattened",
       "a~reason~with~spaces" in line)
    ok("and so was the note", "a~note~with~spaces" in line)
    ok("the line carries the status, the return and the asked denominator",
       "propImportStatus=IMPORTED" in line and "propImportReturn=0" in line
       and "propMeshesAsked=16/23" in line)
    ok("the line says out loud that the engine delta is not gated yet",
       "propBoundsBound=NONE-YET/this-run-prints-the-series" in line)
    ok("and it names what the bounds number is a statistic OF",
       "propBoundsStat=" in line and "at-worst" in line)
    ok("the line carries the glTF word and the accepting case on their own keys",
       "propGltfImporter=ABSENT/exporter-only" in line
       and "propAcceptingCase=piece=" + ACCEPTING_PIECE in line, line)
    ok("and the accepting case's spaces were flattened too",
       "did~not~load~back" in line)
    ok("the line carries the lookup pair that tells an import which made "
       "nothing from one which made something else",
       "propImportLookedFor=" in line and "propImportedNames=" in line
       and "propImportResolvedVia=" in line, line)
    # G2. THE COLLISION PAIR, ON THE LINE, UNDER NAMES A GREP CANNOT MERGE.
    # Run 3 put propCollisionPrims=0/15 on this line and collisionPrims=-1
    # inside propAcceptingCase, one name over two populations.
    ok("the whole-run collision keys are on the line with their denominators",
       "propCollisionPrims=%d/%d" % (len(rs), len(rs)) in line
       and "propCollisionPrimsUnread=0/%d" % len(rs) in line
       and "propCollidable=%d/%d" % (len(rs), len(rs)) in line, line)
    ok("and the per-mesh key is spelled differently from the whole-run key, so "
       "one grep cannot pick up the other",
       "collisionPrims=" not in line.replace("propCollisionPrims=", "")
       .replace("propCollisionPrimsUnread=", "")
       .replace("propCollisionPrimsStat=", ""), line)
    ok("the line carries what the source files hold, because one uasset per "
       "asset leaves any other part of the file out of the street",
       "propSourcePartsOver1=1/2" in line and "b=2" in line, line)
    ok("and it carries the two engine questions the next run needs answered",
       "propSubsystems=" in line and "propPipelineOpts=" in line
       and "NOTHING-SET-THIS-RUN" in line, line)
    ok("the status word and the collision block cannot disagree, because both "
       "read collidable_tally over one population",
       import_status(len(rs), len(rs), len(rs), len(rs),
                     *collidable_tally(rs, len(rs))[:2]) == "IMPORTED"
       and "propCollidable=%d/%d" % (len(rs), len(rs)) in line)
    ok("and a blind run's tally drives the word that says so",
       import_status(3, 3, 3, 3, *collidable_tally(blind3, 3)[:2])
       == "IMPORTED-COLLISION-UNREADABLE",
       collidable_tally(blind3, 3))
    ok("the engine block names which subsystem answered and sets nothing",
       "propSubsystems=StaticMeshEditorSubsystem=returned-None" in
       engine_field(["StaticMeshEditorSubsystem=returned-None"], [])
       and "NOTHING-SET-THIS-RUN" in engine_field([], []), engine_field([], []))
    ok("and with nothing asked it says nothing-measured on both keys",
       "propSubsystems=nothing-measured" in engine_field([], [])
       and "propPipelineOpts=nothing-measured" in engine_field([], []))

    # -- H. THE REJECTING FIXTURE FOR THE NAME RULE ------------------------
    ok("an asset id with a slash is refused", not safe_asset_id("ambientcg/Leak"))
    ok("an asset id with a dot is refused", not safe_asset_id("lamp.post"))
    ok("an empty asset id is refused", not safe_asset_id(""))
    ok("a normal one is accepted", safe_asset_id("lamp_post_01"))
    ok("the object path is the package path plus the object name",
       object_path("lamp_post_01") ==
       "/Game/Ledger/Props/SM_lamp_post_01.SM_lamp_post_01",
       object_path("lamp_post_01"))
    ok("a hyphen in an asset id becomes an underscore in both halves",
       uasset_name("a-b") == "SM_a_b", uasset_name("a-b"))

    for b in bad:
        print(b)
    print("import_prop_meshes --selftest: %d check(s), %d failure(s)"
          % (checks[0], len(bad)))
    return 1 if bad else 0


# ---- the half that needs Unreal. It supplies numbers and decides nothing ---


def _try(calls, report, accept=None):
    """Take the first route that answers, and RECORD WHICH ONE, the same shape
    make_base_material.py uses for a pin name. A fallback that works silently
    is a fallback nobody knows they are depending on.

    calls is a list of (name, zero-argument callable). Returns
    (value, via) where via is the name that answered or none-of-N.

    `accept` IS THE FIX FOR RUN 3'S ZERO, and the fault it closes is narrow
    and expensive. An engine API that refuses does not always raise: the
    legacy EditorStaticMeshLibrary answers -1 when it will not run, which it
    will not in a commandlet, and -1 is not None, so the old code took it as
    the answer, printed collisionPrims=-1 on one line and turned the same -1
    into 0/15 on another. A route whose answer fails `accept` is REFUSED, with
    the sentinel named in the report, and the next route gets its turn."""
    for name, fn in calls:
        try:
            v = fn()
        except Exception as e:
            report.append("%s-refused=%s" % (name, str(e).split("\n")[0][:80]))
            continue
        if v is None:
            continue
        if accept is not None and not accept(v):
            report.append("%s-refused-with-sentinel=%s" % (name, flat(v)[:40]))
            continue
        return v, name
    return None, "none-of-%d-candidates" % len(calls)


def _bounds_of(unreal, mesh, report):
    """The mesh's own bounds, read BACK off the asset the engine just made.

    Two routes because a UPROPERTY reachable as an attribute in one engine
    version is reachable only as an editor property in another, and a
    TypeError here would otherwise read as a mesh with no bounds."""
    def via_method():
        b = mesh.get_bounds()
        return (b.origin, b.box_extent)

    def via_property():
        b = mesh.get_editor_property("extended_bounds")
        return (b.origin, b.box_extent)

    v, via = _try([("get_bounds", via_method),
                   ("extended_bounds-property", via_property)], report)
    if v is None:
        return None, None, via
    o, e = v
    return ((o.x, o.y, o.z), (e.x, e.y, e.z), via)


# THE ELEMENT LISTS OF A BODY SETUP'S AGGREGATE GEOMETRY. Every one is read
# separately and a list that refuses is counted apart from a list that is
# empty, so a zero here ships the number of lists that answered.
AGG_ELEM_LISTS = ("box_elems", "sphere_elems", "sphyl_elems", "convex_elems",
                  "tapered_capsule_elems")


def _body_setup(unreal, mesh, report):
    """The mesh's own body setup, which is where collision actually lives.

    WRITTEN OUT RATHER THAN THROUGH _try, and the reason is the distinction
    _try cannot make: a UPROPERTY that reads fine and is NULL and a property
    this engine will not let Python read both come back None. The first means
    the mesh has no collision container at all, which is a finding; the second
    means the instrument is blind, which is a different finding. Returns
    (body_setup_or_None, word) with word in present / absent / unread."""
    def via_property():
        return mesh.get_editor_property("body_setup")

    def via_attribute():
        return mesh.body_setup

    for name, fn in (("body-setup-property", via_property),
                     ("body-setup-attribute", via_attribute)):
        try:
            bs = fn()
        except Exception as e:
            report.append("%s-refused=%s" % (name, str(e).split("\n")[0][:70]))
            continue
        if bs is None:
            return None, "absent"
        return bs, "present"
    return None, "unread"


def _make_body_setup(unreal, mesh, report):
    """Give a mesh a body setup when it has none, because nothing else in this
    section can work without one. Read back off the mesh, never assumed from
    the call returning."""
    def via_new_object():
        bs = unreal.new_object(unreal.BodySetup, outer=mesh)
        mesh.set_editor_property("body_setup", bs)
        return mesh.get_editor_property("body_setup")

    v, via = _try([("new-object-body-setup", via_new_object)], report)
    return v, via


def _agg_geom(unreal, bs, report):
    """The aggregate geometry struct off a body setup, or None with the via."""
    def via_property():
        return bs.get_editor_property("agg_geom")

    def via_attribute():
        return bs.agg_geom

    return _try([("agg-geom-property", via_property),
                 ("agg-geom-attribute", via_attribute)], report)


def _agg_prim_count(agg, report):
    """Simple primitives in the aggregate geometry, PER LIST.

    A ZERO NEEDS A DENOMINATOR: the second return value is how many of the
    element lists answered at all, so "no primitives" and "this binding does
    not expose the element lists" are different readings. None means nothing
    answered and the count is nothing-measured, not zero."""
    total, read, per = 0, 0, {}
    refused, why = [], ""
    for nm in AGG_ELEM_LISTS:
        try:
            n = len(agg.get_editor_property(nm))
        except Exception as e:
            refused.append(nm)
            why = why or str(e).split("\n")[0][:40]
            continue
        read += 1
        per[nm] = int(n)
        total += int(n)
    if refused:
        # ONE LINE FOR ALL FIVE LISTS, NOT FIVE. propNote has a cap of four
        # distinct causes and five near-identical refusals would spend all of
        # it on one cause, which is the fault run 3's note had in the other
        # direction.
        report.append("agg-elems-refused=%s/%d-of-%d/%s"
                      % (",".join(refused), len(refused), len(AGG_ELEM_LISTS), why))
    if read == 0:
        return None, per
    return total, per


def _simple_prim_count(unreal, mesh, bs, report):
    """How many simple collision primitives this mesh has, ASKED EVERY WAY.

    EVERY ROUTE IS RUN, not just the first that answers, because that is the
    paired reading this fault needs. Run 3's only count came from the legacy
    library, which answered -1 and was believed. A second route that answers
    the same number is what makes one believable, and propCollisionAgree is
    the count of meshes where two or more routes answered and agreed.

    A NEGATIVE IS A REFUSAL SENTINEL AND NOT A COUNT. There is no such thing
    as minus one box.

    Returns (count_or_None, via, answers) where answers maps every route name
    to the int it answered or the string that says how it refused."""
    answers = {}

    def agg_route():
        if bs is None:
            raise RuntimeError("no-body-setup-to-read")
        agg, _v = _agg_geom(unreal, bs, report)
        if agg is None:
            raise RuntimeError("agg-geom-unreadable")
        n, per = _agg_prim_count(agg, report)
        if per:
            answers["aggPerList"] = per
        if n is None:
            raise RuntimeError("no-element-list-answered")
        return n

    def subsystem_route():
        sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        if sub is None:
            # NAMED, NOT AN ATTRIBUTE ERROR ON None. Run 3's note said
            # "'NoneType' object has no attribute get_simple_collision_count",
            # which reads as a missing METHOD and is really a missing
            # SUBSYSTEM. propSubsystems settles which.
            raise RuntimeError("get_editor_subsystem-returned-None")
        return sub.get_simple_collision_count(mesh)

    def legacy_route():
        return unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh)

    routes = [("agg-geom-elems", agg_route), ("subsystem", subsystem_route),
              ("legacy-library", legacy_route)]
    first, first_via = None, "none-of-%d-candidates" % len(routes)
    for name, fn in routes:
        try:
            v = fn()
        except Exception as e:
            msg = str(e).split("\n")[0][:60]
            answers[name] = "refused/" + flat(msg)
            report.append("%s-count-refused=%s" % (name, msg))
            continue
        if v is None:
            answers[name] = "answered-None"
            continue
        try:
            iv = int(v)
        except Exception:
            answers[name] = "answered-non-number/" + flat(v)[:30]
            continue
        if iv < 0:
            answers[name] = "refused-with-sentinel/%d" % iv
            report.append("%s-count-refused-with-sentinel=%d" % (name, iv))
            continue
        answers[name] = iv
        if first is None:
            first, first_via = iv, name
    return first, first_via, answers


def _trace_flag(unreal, bs, report):
    """The body setup's collision trace flag, as the engine spells it.

    It is the half of collidability a primitive count cannot see: complex-as-
    simple means the mesh collides with its own triangles and holds no simple
    primitives at all."""
    if bs is None:
        return None, "no-body-setup"

    def via_property():
        return bs.get_editor_property("collision_trace_flag")

    v, via = _try([("trace-flag-property", via_property)], report)
    return (None if v is None else flat(v)), via


def _complex_as_simple_value(unreal):
    """The enumerator this engine spells for use-complex-as-simple, FOUND BY
    NAME rather than assumed, and the name it found travels back.

    CTF_USE_COMPLEX_AS_SIMPLE is what the Python binding is expected to call
    it. If this engine calls it something else, scanning the enum for the
    three words finds it and says which name was used; a route that cannot
    find it says so instead of silently setting nothing."""
    cls = getattr(unreal, "CollisionTraceFlag", None)
    if cls is None:
        return None, "CollisionTraceFlag-class-absent"
    direct = getattr(cls, "CTF_USE_COMPLEX_AS_SIMPLE", None)
    if direct is not None:
        return direct, "CTF_USE_COMPLEX_AS_SIMPLE"
    for nm in sorted(dir(cls)):
        if is_complex_as_simple(nm):
            return getattr(cls, nm), nm
    return None, "no-enumerator-matching-" + COMPLEX_AS_SIMPLE


def _set_complex_as_simple(unreal, bs, report):
    """Make the mesh collide with its own render triangles, and READ THE FLAG
    BACK off the body setup.

    FOR A FLAT GRATE A CHARACTER WALKS OVER, THIS IS ARGUABLY THE RIGHT ANSWER
    AND NOT A WORKAROUND: the grate is 40 x 40 x 1.5 cm and its triangles are
    the surface the capsule stands on. It is taken here only when no simple
    primitive could be added or counted, so a mesh that has a box keeps the
    cheaper shape, which is write-on-change rather than a blanket policy."""
    want, name = _complex_as_simple_value(unreal)
    if want is None:
        report.append("complex-as-simple-refused=%s" % name)
        return None, name

    def via_property():
        bs.set_editor_property("collision_trace_flag", want)
        return bs.get_editor_property("collision_trace_flag")

    v, via = _try([("trace-flag-set-property", via_property)], report)
    if v is None:
        return None, via
    return flat(v), name


def _add_box_elem(unreal, bs, origin_uu, extent_uu, report):
    """A box the size of the mesh's own measured bounds, straight into the
    body setup's aggregate geometry.

    WHY A BOX AND NOT A CONVEX HULL: a box element is analytic, so it needs no
    cooked physics data to exist in a saved package, which a convex hull does.
    What is written here is serialised with the asset and is there on load.

    FKBoxElem's x, y and z are FULL LENGTHS and not half-extents, which is why
    the engine's half-extent reading is doubled. That is an assumption about
    the struct, and the reading that would catch it being wrong is the
    primitive count coming back while a walk clip still falls through: the
    count cannot see a box of the wrong size. Named here as the open
    assumption it is."""
    if extent_uu is None:
        raise RuntimeError("no-bounds-to-size-a-box-from")
    elem = unreal.KBoxElem()
    elem.set_editor_property("center", unreal.Vector(
        float(origin_uu[0]), float(origin_uu[1]), float(origin_uu[2])))
    elem.set_editor_property("x", float(extent_uu[0]) * 2.0)
    elem.set_editor_property("y", float(extent_uu[1]) * 2.0)
    elem.set_editor_property("z", float(extent_uu[2]) * 2.0)
    agg, via = _agg_geom(unreal, bs, report)
    if agg is None:
        raise RuntimeError("agg-geom-unreadable/" + str(via))
    boxes = list(agg.get_editor_property("box_elems"))
    boxes.append(elem)
    agg.set_editor_property("box_elems", boxes)
    bs.set_editor_property("agg_geom", agg)
    return True


def _ensure_collision(unreal, mesh, origin_uu, extent_uu, report):
    """COLLISION ON THE IMPORTED MESH, AND THE STATE IS READ BACK OFF THE
    ASSET. Returns a dict of live state; every word on the verdict is decided
    by the pure functions above from this dict.

    Four routes for adding, in the order of how much the engine has to agree
    with us, and each one that refuses says which name refused:

      agg-geom-box           a box element written into the body setup. Needs
                             unreal.KBoxElem and the element list to be
                             writable from Python; both are unknown until a
                             run says.
      subsystem-box          StaticMeshEditorSubsystem.add_simple_collisions.
                             Refused in run 3 because the subsystem itself was
                             None in this commandlet.
      legacy-box             EditorStaticMeshLibrary.add_simple_collisions.
                             Answered -1 in run 3, which is a refusal.
      complex-as-simple-flag not a primitive at all: the mesh collides with its
                             own triangles. Taken last, and only when no count
                             above zero could be read.

    EVERY ADD IS FOLLOWED BY A READ-BACK AND THE READ-BACK IS WHAT DECIDES. A
    route that returns without raising has not added anything: it has failed to
    complain. propCollisionVia therefore names a route that MOVED THE COUNT, or
    says which routes ran without effect."""
    state = {"bodySetup": "unread", "simplePrims": None,
             "simplePrimsVia": "not-reached", "simplePrimsAnswers": {},
             "primsBefore": None, "traceFlag": None,
             "traceFlagVia": "not-reached", "collisionAddVia": "not-reached",
             "collisionFlagSet": False, "collisionFlagWhy": "not-needed"}

    bs, word = _body_setup(unreal, mesh, report)
    if bs is None and word == "absent":
        bs2, mvia = _make_body_setup(unreal, mesh, report)
        word = ("made/" + mvia) if bs2 is not None else ("absent/could-not-make/" + mvia)
        bs = bs2
    state["bodySetup"] = word

    before, bvia, answers = _simple_prim_count(unreal, mesh, bs, report)
    state["primsBefore"] = before
    state["simplePrims"], state["simplePrimsVia"] = before, bvia
    state["simplePrimsAnswers"] = answers

    if before is not None and before > 0:
        # WRITE-ON-CHANGE. A mesh the importer already gave collision to is
        # not given a second box on top of the first.
        state["collisionAddVia"] = "not-needed/already-had-%d" % before
    else:
        def add_agg_box():
            return _add_box_elem(unreal, bs, origin_uu, extent_uu, report)

        def add_subsystem():
            sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
            if sub is None:
                raise RuntimeError("get_editor_subsystem-returned-None")
            sub.add_simple_collisions(mesh, unreal.ScriptingCollisionShapeType.BOX)
            return True

        def add_legacy():
            r = unreal.EditorStaticMeshLibrary.add_simple_collisions(
                mesh, unreal.ScriptingCollisionShapeType.BOX)
            # -1 IS HOW THIS LIBRARY SAYS NO. It returns the index it added at,
            # so a negative is a refusal and must not read as a success.
            if isinstance(r, int) and r < 0:
                raise RuntimeError("legacy-add-returned-%d" % r)
            return True

        if bs is None:
            # THE WORD TRAVELS, because "this mesh has no body setup" and
            # "Python could not read the body setup" need different fixes.
            state["collisionAddVia"] = "not-attempted/body-setup=" + word
        else:
            # A ROUTE THAT RAN IS NOT A ROUTE THAT WORKED. That was run 2's
            # whole fault in the import loop and it is not repeated here: each
            # add is followed by a READ-BACK, and a route whose write changed
            # the count by nothing hands over to the next one under its own
            # name. _try cannot express this, because to _try a call that
            # returns without raising has answered.
            after, avia2, answers2 = before, bvia, answers
            added_via = "none-of-3-candidates"
            for nm, fn in (("agg-geom-box", add_agg_box),
                           ("subsystem-box", add_subsystem),
                           ("legacy-box", add_legacy)):
                try:
                    fn()
                except Exception as e:
                    msg = str(e).split("\n")[0][:70]
                    report.append("%s-refused=%s" % (nm, msg))
                    continue
                after, avia2, answers2 = _simple_prim_count(unreal, mesh, bs, report)
                if after is None:
                    # THE WRITE MAY HAVE WORKED AND THE READER IS BLIND. Stop
                    # rather than let the next route put a second box on top of
                    # a first one nobody can see.
                    added_via = nm + "/ran/count-unreadable"
                    break
                if after > (before or 0):
                    added_via = nm
                    break
                report.append("%s-ran-without-effect=count-still-%d" % (nm, after))
            state["collisionAddVia"] = added_via
            # LAST-WINS, AND IT IS THE COUNT AFTER THE WRITE. primsBefore
            # keeps the other moment, so the two are never one key.
            state["simplePrims"], state["simplePrimsVia"] = after, avia2
            state["simplePrimsAnswers"] = answers2

    flag, fvia = _trace_flag(unreal, bs, report)
    state["traceFlag"], state["traceFlagVia"] = flag, fvia

    prims = state["simplePrims"]
    if bs is not None and not is_complex_as_simple(flag) and (prims is None or prims <= 0):
        why = ("no-simple-primitive-could-be-added" if prims == 0
               else "simple-primitive-count-unreadable")
        newflag, fname = _set_complex_as_simple(unreal, bs, report)
        if newflag is not None:
            state["traceFlag"] = newflag
            state["collisionFlagSet"] = True
            state["collisionFlagWhy"] = why + "/enum=" + fname
        else:
            state["collisionFlagWhy"] = why + "/refused=" + fname
    return state


def _subsystem_probe(unreal, report):
    """WHY FAULT 1 HAPPENED AT ALL, asked of the engine instead of argued
    about. get_editor_subsystem(StaticMeshEditorSubsystem) returned None in
    run 3, so every attribute error in that run's note was an error on None
    and not a missing method. Asking for three more subsystems settles which
    world this is: all None means editor subsystems are not created in this
    commandlet at all, one None means that one module is not loaded.

    Three words, and they are different facts: class-absent (the binding does
    not know the type), returned-None (the engine would not give it), present.
    """
    out = []
    for nm in ("StaticMeshEditorSubsystem", "EditorActorSubsystem",
               "AssetEditorSubsystem", "LevelEditorSubsystem"):
        cls = getattr(unreal, nm, None)
        if cls is None:
            out.append("%s=class-absent" % nm)
            continue
        try:
            sub = unreal.get_editor_subsystem(cls)
        except Exception as e:
            out.append("%s=raised/%s" % (nm, flat(str(e).split("\n")[0][:30])))
            continue
        out.append("%s=%s" % (nm, "present" if sub is not None else "returned-None"))
    return out


def _pipeline_probe(unreal, report):
    """WHICH IMPORT-TIME OPTIONS THIS ENGINE ACTUALLY EXPOSES, BY NAME.

    NOTHING IS SET HERE, and that is deliberate. Asking the import to build
    collision, or to combine a multi-mesh file into one asset, are both real
    candidates for the next run, and both need a property name this container
    cannot check and no docs page can be trusted for. Run 3 proved the import
    route that works; changing its options in the same pass that fixes
    collision would risk fifteen working assets to test a name. So this run
    READS the names and the next one can use them.

    Each class ships its matching names over the total it has, so a zero here
    has a denominator and cannot read as "this engine has no such option"
    when it means "dir() returned nothing"."""
    out = []
    keys = ("collision", "combine", "convex", "ucx")
    for cls_name in ("InterchangeGenericAssetsPipeline",
                     "InterchangeGenericMeshPipeline",
                     "InterchangePipelineStackOverride"):
        cls = getattr(unreal, cls_name, None)
        if cls is None:
            out.append("%s=class-absent" % cls_name)
            continue
        try:
            names = [a for a in dir(cls) if not a.startswith("_")]
        except Exception as e:
            out.append("%s=dir-refused/%s" % (cls_name, flat(str(e)[:30])))
            continue
        want = sorted(a for a in names if any(k in a.lower() for k in keys))
        shown = ",".join(want[:6]) if want else "none-matching"
        if len(want) > 6:
            shown += ",(+%d~more~not~shown)" % (len(want) - 6)
        out.append("%s=%d-of-%d:%s" % (cls_name, len(want), len(names), shown))
    return out


def importer_candidates(names):
    """Which of the engine's enabled plugins could POSSIBLY be importing glTF.

    THE HOLE THIS CLOSES, found by reading rather than running. The first
    version of this test asked only for GLTF in the name, which is the exact
    mistake that produced run 1's propGltfPlugins=GLTFExporter/1: in modern
    Unreal the glTF importer ships inside the Interchange plugins, whose names
    contain no GLTF at all. So an Interchange-only engine that refuses the
    file would have printed ABSENT/exporter-only, which is run 1's misreading
    wearing the new key, and the gate step pulls that word to the top of the
    output where a person reads it first.

    GLTF or INTERCHANGE, and never EXPORT: an exporter is not an importer and
    that is the one distinction this whole key exists to hold."""
    out = []
    for n in names:
        u = str(n).upper()
        if "EXPORT" in u:
            continue
        if "GLTF" in u or "INTERCHANGE" in u:
            out.append(n)
    return out


def gltf_verdict(exporter_found, importer_plugins, translate_ok, translate_asked):
    """THE THREE FACTS THE FIRST RUN COULD NOT TELL APART, AND WHY.

    Run 1 printed propGltfPlugins=GLTFExporter/1 beside
    propImportVia=none-of-2-candidates, and the pair is ambiguous in exactly
    the way that costs a round trip. Three different worlds produce it:

      1. the engine has NO glTF import at all;
      2. the engine HAS glTF import, through Interchange, whose plugin files
         are named InterchangeAssets and InterchangeEditor and which a glob
         for *GLTF*.uplugin therefore cannot see;
      3. the import exists and was refused for some other reason.

    The instrument that produced GLTFExporter/1 could not distinguish any of
    them, which is rule 3: suspect the ruler before the reading. So the word
    below is decided by asking the ENGINE whether it can translate the actual
    file, not by counting plugin files, and the plugin names travel beside it
    as the explanation rather than as the evidence.

    translate_ok/translate_asked is the engine's own answer over the sources
    offered to it. nothing-measured when the question could not be put."""
    if translate_asked <= 0:
        return "NOTHING-MEASURED/the-engine-was-never-asked"
    if translate_ok > 0:
        return "PRESENT/engine-says-it-can-translate/%d-of-%d" % (translate_ok, translate_asked)
    if importer_plugins:
        return ("REFUSED/importer-plugin-present-but-translate-said-no/%s"
                % ";".join(importer_plugins[:3]))
    if exporter_found:
        # THE READING RUN 1 ACTUALLY HAD, now sayable in one word. An exporter
        # is not an importer and this key will never let the two read alike
        # again.
        return "ABSENT/exporter-only/no-importer-plugin-and-translate-said-no"
    return "ABSENT/no-gltf-plugin-of-either-kind"


def _engine_gltf_probe(unreal, sources, report):
    """Ask the engine, once, what it can do with these files.

    THE ENTRY POINT IS CHEAPER THAN THE ARGUMENT (ci.md, ruled 2026-09-08 over
    four refuted explanations of a silent channel). Rather than reasoning
    about which plugin ships glTF import in this engine version, put the file
    in front of the engine and record the answer.

    Returns (translate_ok, translate_asked, plugin_names, api_names)."""
    ok_n = 0
    asked = 0

    def can(path):
        mgr = unreal.InterchangeManager.get_interchange_manager_scripted()
        src = unreal.InterchangeManager.create_source_data(path)
        return bool(mgr.can_translate_source_data(src))

    for path in sources[:3]:
        asked += 1
        v, _via = _try([("can-translate", lambda p=path: can(p))], report)
        if v:
            ok_n += 1

    # WHICH PLUGINS THE ENGINE SAYS ARE ENABLED, from the engine and not from
    # a directory listing, because -EnablePlugins on the command line and a
    # .uplugin on disk are different facts and only the first one runs.
    def enabled():
        return [str(n) for n in unreal.PluginBlueprintLibrary.get_enabled_plugin_names()]

    names, _v = _try([("enabled-plugin-names", enabled)], report)
    if names is None:
        names = []
    interesting = [n for n in names
                   if "GLTF" in n.upper() or "INTERCHANGE" in n.upper()]

    # AND WHAT THE PYTHON API OFFERS, because a class that is not there is why
    # a route raises AttributeError and reads as "refused".
    api = [n for n in ("InterchangeManager", "AssetImportTask",
                       "InterchangeGenericAssetsPipeline", "ImportAssetParameters")
           if hasattr(unreal, n)]
    return ok_n, asked, interesting, api


def _material_slots(unreal, mesh, report):
    """How many material slots the imported mesh has.

    IT MATTERS BECAUSE THE STREET ONLY OWNS SLOT 0. VignetteShot.cpp's
    material pass calls Comp->SetMaterial(0, Mid) with the surface the piece
    names, so a prop with two slots keeps whatever the glTF importer put in
    slot 1 and the street's surface never reaches it. Every held prop measures
    exactly one slot in its GLB today; this is the reading that would say when
    that stopped being true. Negative means the engine would not answer, which
    is a different fact from zero."""
    def via_static_materials():
        return len(mesh.get_editor_property("static_materials"))

    def via_num_sections():
        return mesh.get_num_sections(0)

    v, _via = _try([("static_materials", via_static_materials),
                    ("num_sections", via_num_sections)], report)
    return -1 if v is None else int(v)


def package_of(entry):
    """Drop a trailing `.Name` so an object path and a package name compare.

    A1(a), AND IT WOULD HAVE WASTED RUN 3. _list_package takes
    EditorAssetLibrary.list_assets first and the asset registry's
    package_name second, and the two return DIFFERENT SHAPES:
    /Game/Ledger/Props/SM_x versus /Game/Ledger/Props/SM_x.SM_x. Two sources
    disagreed about which list_assets gives and neither source was a run. If
    the object-path shape came back, a PERFECT import at the exact contract
    path would miss exact-path (the string differs) and miss
    exact-name-different-folder (SM_x.SM_x is not SM_x), and land on
    name-contains-the-asset-id, whose docstring says that reading means run
    2's lookup was the entire fault. A healthy run would have printed a
    conclusion about run 2 that the run never measured.

    A package or object name cannot itself contain a dot, so cutting the leaf
    at its first dot is exact rather than heuristic."""
    e = str(entry)
    at = e.rfind("/")
    head, leaf = (e[:at + 1], e[at + 1:]) if at >= 0 else ("", e)
    dot = leaf.find(".")
    return head + (leaf[:dot] if dot >= 0 else leaf)


def resolve_imported(appeared, asset_id):
    """Which of the packages that APPEARED is this asset, and by what rule.

    RUN 2'S WHOLE FAULT IN ONE FUNCTION. That run imported sixteen GLBs into
    an engine that says it can translate all of them, raised nothing, and
    reported none-of-2-candidates, because the code asked one question:
    does /Game/Ledger/Props/SM_<asset> load? A glTF importer is under no
    obligation to name the asset that. Interchange can name a static mesh
    after the MESH inside the file rather than the file, and it can nest a
    source's output under a subfolder. Either way the import worked and only
    the lookup failed, and the old code could not tell that apart from an
    import that produced nothing at all.

    So this takes the list of packages that were not there before, and names
    the RULE that matched, so a run says WHY it thinks a package is this
    asset. Returns (path_or_None, how)."""
    want = PACKAGE_DIR + "/" + uasset_name(asset_id)
    # NORMALISED BEFORE ANY COMPARISON. See package_of().
    leafs = [(package_of(p), package_of(p).rsplit("/", 1)[-1]) for p in appeared]

    def norm(x):
        return str(x).upper().replace("-", "_")

    for p, leaf in leafs:
        if p == want:
            return p, "exact-path"
    for p, leaf in leafs:
        if norm(leaf) == norm(uasset_name(asset_id)):
            return p, "exact-name-different-folder"
    for p, leaf in leafs:
        if norm(asset_id) in norm(leaf):
            return p, "name-contains-the-asset-id"
    if not leafs:
        return None, "nothing-appeared"
    if len(leafs) == 1:
        # A5, AND IT OVERRULES A JUDGEMENT MADE HERE. This was kept as the
        # weakest of five rules, on the grounds that it still tells you the
        # import made SOMETHING. The director's correction: a rule that
        # matches on TIMING rather than on a name is an inference, and
        # counting an inference in the same tally as four name matches lets
        # one number mix two kinds of evidence. So it is a FAILURE with its
        # own tally. It still says the import made something, under the leaf's
        # own name, without claiming to know it is the right something.
        return None, "appeared-unnamed/" + leafs[0][1]
    # AND IT NAMES THEM, because "ambiguous-3-appeared" cost a round trip to
    # the manifest to find out that the three were hinges, sign_front and
    # sign_back: three real static meshes out of one GLB, with the material
    # already filtered out by the class filter in _import_one. The names are
    # the finding. Nothing about the RULE is loosened: three meshes and no way
    # to tell which is the prop is still a refusal, because choosing one would
    # put a sign with no hinges at the street's path and call it a pass.
    shown = ",".join(sorted(leaf for _p, leaf in leafs)[:3])
    if len(leafs) > 3:
        shown += ",(+%d~more~not~shown)" % (len(leafs) - 3)
    return None, "ambiguous-%d-appeared/%s" % (len(leafs), shown)


def _list_package(unreal, report):
    """Every asset package currently under the destination directory.

    The snapshot either side of an import is what turns "did SM_x load" into
    "what did this import actually make", which is the pair the director asked
    for. An unreadable directory returns None, which is a different fact from
    an empty one and is carried as such."""
    def via_editor_asset_library():
        return list(unreal.EditorAssetLibrary.list_assets(
            PACKAGE_DIR, True, False))

    def via_registry():
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        return [str(a.package_name) for a in
                ar.get_assets_by_path(PACKAGE_DIR, True)]

    v, _via = _try([("list-assets", via_editor_asset_library),
                    ("asset-registry", via_registry)], report)
    if v is None:
        return None, "unreadable"
    # THE FIRST RAW ENTRY, UNNORMALISED, SO THE SHAPE IS NEVER GUESSED AGAIN.
    # It goes on the verdict as propImportSnapshotShape and settles which of
    # the two shapes this engine's list_assets returns.
    raw = str(v[0]) if v else "empty"
    return [package_of(x) for x in v], raw


def _wait_for_registry(unreal, report):
    """Take whatever wait this engine offers, and SAY WHETHER IT WAS TAKEN.

    INTERCHANGE IMPORT IS ASYNCHRONOUS BY DEFAULT, which is the director's
    first hypothesis and the one this code could not previously see: an import
    that will succeed in a moment is indistinguishable from one that produced
    nothing if the very next line loads by path. The counts that come back,
    propImportWaitTaken and propImportWaitChanged, answer one half: a wait that
    repeatedly CHANGES the answer is an async import. A wait that never changes
    it rules NOTHING out, because what is waited on here is an asset-registry
    scan and not the import itself, so zero is silence. propImportTaskAsync is
    the key that watches the import."""
    def via_registry_wait():
        unreal.AssetRegistryHelpers.get_asset_registry().wait_for_completion()
        return True

    def via_scan_paths():
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        ar.scan_paths_synchronous([PACKAGE_DIR], True)
        return True

    v, via = _try([("registry-wait-for-completion", via_registry_wait),
                   ("registry-scan-paths-synchronous", via_scan_paths)], report)
    return bool(v), via


def _import_one(unreal, abs_glb, asset_id, report):
    """One GLB to one uasset. Returns (mesh_or_None, via, detail).

    THE ROUTE LOOP IS WRITTEN OUT HERE RATHER THAN GOING THROUGH _try, and
    that is the fix for run 2. _try treats a None RETURN as "this route did
    not answer" and moves to the next one. The old routes ended in
    load_asset(), which returns None when a path does not resolve, so a route
    that ran perfectly and imported the file reported itself as refused, with
    no exception to show for it. That is why run 2 printed
    propImportVia=none-of-2-candidates beside propNote=none: nothing raised,
    because nothing went wrong except the question being asked.

    Now a route reports whether it RAN, separately from whether the asset was
    then found, and what it made is enumerated rather than guessed at."""
    name = uasset_name(asset_id)
    detail = {"lookedFor": object_path(asset_id), "appeared": [],
              "appearedClasses": {}, "resolvedVia": "not-reached",
              "routeRan": "none", "taskPaths": [], "waitTaken": False,
              "waitChanged": False, "snapshotShape": "nothing-measured",
              "taskApi": [], "taskAsyncBefore": "no-api",
              "taskAsyncAfter": "no-api", "resultType": "not-reached",
              "resultWaitAttrs": [], "renamed": False,
              "unnamedBounds": None}

    before, raw_shape = _list_package(unreal, report)
    detail["snapshotShape"] = raw_shape
    before_set = set(before or [])

    def via_task():
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", abs_glb)
        task.set_editor_property("destination_path", PACKAGE_DIR)
        task.set_editor_property("destination_name", name)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", False)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        # A1(c). THE TASK'S OWN ASYNC FLAG, READ EITHER SIDE OF get_objects().
        # AssetImportTask carries an async completion flag in some engine
        # versions and not others, and get_objects() is documented to block
        # until the objects exist. Both are guarded by hasattr and BOTH NAMES
        # ARE PRINTED present or absent, because "the flag said incomplete" and
        # "there is no flag on this class" are different facts and an absent
        # API must never read as a negative answer.
        api = []
        if hasattr(task, "is_async_import_complete"):
            api.append("is_async_import_complete=present")
            try:
                detail["taskAsyncBefore"] = bool(task.is_async_import_complete())
            except Exception as e:
                detail["taskAsyncBefore"] = "raised/" + str(e).split("\n")[0][:40]
        else:
            api.append("is_async_import_complete=absent")
        if hasattr(task, "get_objects"):
            api.append("get_objects=present")
            try:
                task.get_objects()
            except Exception as e:
                report.append("task-get-objects-raised=%s" % str(e).split("\n")[0][:60])
        else:
            api.append("get_objects=absent")
        if hasattr(task, "is_async_import_complete"):
            try:
                detail["taskAsyncAfter"] = bool(task.is_async_import_complete())
            except Exception as e:
                detail["taskAsyncAfter"] = "raised/" + str(e).split("\n")[0][:40]
        detail["taskApi"] = api
        # THE TASK'S OWN ANSWER ABOUT WHAT IT MADE, which run 2's code
        # computed and threw away before going to look for a path instead.
        try:
            return [str(x) for x in
                    task.get_editor_property("imported_object_paths")]
        except Exception:
            return []

    def via_interchange_result():
        # THE SYNCHRONOUS-SHAPED VARIANT FIRST. It returns a result object
        # rather than firing and forgetting, and it is tried ahead of
        # import_asset for exactly that reason. Whether it actually blocks in
        # this engine is not asserted here; propImportResultWaitAttrs and
        # propImportTaskAsync are what would show it did not.
        # propImportWaitChanged would not: it scans the registry, not the
        # import.
        mgr = unreal.InterchangeManager.get_interchange_manager_scripted()
        src = unreal.InterchangeManager.create_source_data(abs_glb)
        params = unreal.ImportAssetParameters()
        params.set_editor_property("is_automated", True)
        # A1(d). THE RETURN VALUE IS KEPT, NOT DISCARDED. Run 2's code threw
        # it away, which is why nothing here knew whether a wait was even
        # offered. Its type name and every attribute whose name mentions wait,
        # done or complete go on the verdict, so the engine tells us what the
        # handle can do instead of us guessing from a docs page.
        res = mgr.import_asset_with_result(PACKAGE_DIR, src, params)
        detail["resultType"] = type(res).__name__ if res is not None else "None"
        try:
            detail["resultWaitAttrs"] = [a for a in dir(res) if
                                         ("wait" in a.lower() or "done" in a.lower()
                                          or "complete" in a.lower())]
        except Exception:
            detail["resultWaitAttrs"] = ["dir-refused"]
        if hasattr(res, "wait_until_done"):
            try:
                res.wait_until_done()
                detail["resultWaitAttrs"].append("wait_until_done=TAKEN")
            except Exception as e:
                report.append("wait-until-done-raised=%s" % str(e).split("\n")[0][:60])
        return []

    def via_interchange():
        mgr = unreal.InterchangeManager.get_interchange_manager_scripted()
        src = unreal.InterchangeManager.create_source_data(abs_glb)
        params = unreal.ImportAssetParameters()
        params.set_editor_property("is_automated", True)
        mgr.import_asset(PACKAGE_DIR, src, params)
        return []

    routes = [("asset-import-task", via_task),
              ("interchange-import-asset-with-result", via_interchange_result),
              ("interchange-import-asset", via_interchange)]

    for route_name, fn in routes:
        try:
            task_paths = fn()
        except Exception as e:
            report.append("%s-raised=%s" % (route_name, str(e).split("\n")[0][:70]))
            continue
        detail["routeRan"] = route_name
        detail["taskPaths"] = list(task_paths or [])

        after, _shape = _list_package(unreal, report)
        new = sorted(set(after or []) - before_set)
        if not new:
            # THE ASYNC HYPOTHESIS, TESTED RATHER THAN ASSUMED AWAY.
            took, _wvia = _wait_for_registry(unreal, report)
            detail["waitTaken"] = took
            if took:
                after, _shape = _list_package(unreal, report)
                new = sorted(set(after or []) - before_set)
                detail["waitChanged"] = bool(new)
        # CUMULATIVE over the routes that ran, for the reason A4 names.
        detail["appeared"] = sorted(set(detail["appeared"]) | set(new))

        # A1(b). LOAD EVERY NEW PACKAGE AND ASK WHAT IT IS, then resolve among
        # the static meshes ONLY. A glTF import through the generic pipeline
        # makes a material and often a texture beside the mesh, and `new` is
        # sorted, so a sibling whose leaf sorts first and happens to contain
        # the asset id would have been returned as the mesh and then rejected
        # as "loaded-as-MaterialInstanceConstant" with the real mesh sitting
        # two entries away, unlooked-at.
        meshes = []
        loaded = {}
        for entry in new:
            o = None
            for cand in (str(entry) + "." + str(entry).rsplit("/", 1)[-1], str(entry)):
                try:
                    o = unreal.load_asset(cand)
                except Exception:
                    o = None
                if o is not None:
                    break
            cls = type(o).__name__ if o is not None else "would-not-load"
            detail["appearedClasses"][str(entry).rsplit("/", 1)[-1]] = cls
            loaded[str(entry)] = o
            if o is not None and isinstance(o, unreal.StaticMesh):
                meshes.append(str(entry))

        path, how = resolve_imported(meshes, asset_id)
        detail["resolvedVia"] = how
        if path is None:
            # A5: an unnamed package still gets its bounds read, under the
            # leaf's own name, because "the import made something of the right
            # size that I cannot name" is a finding and not a blank.
            if how.startswith("appeared-unnamed") and meshes:
                o = loaded.get(meshes[0])
                org, ext, _bv = _bounds_of(unreal, o, report) if o is not None else (None, None, "no-object")
                if ext is not None:
                    detail["unnamedBounds"] = {
                        "leaf": str(meshes[0]).rsplit("/", 1)[-1],
                        "localCentreUu": [round(float(v), 3) for v in org],
                        "extentUu": [round(float(v), 3) for v in ext]}
            # This route ran and made nothing findable. Try the next one.
            continue
        obj = loaded.get(str(path))
        if obj is None:
            try:
                obj = unreal.load_asset(object_path(asset_id))
            except Exception:
                obj = None
        if obj is None:
            continue
        detail["loadedFrom"] = str(path)

        # A3. RENAME TO THE CONTRACT PATH, UNDER THE TWO NAME RULES ONLY.
        # VignetteShot.cpp derives its path from the piece's asset field and
        # nothing else, so a mesh that resolved under a different name is a
        # mesh the street will never find. The rename happens HERE, before the
        # save, so what lands on disk is at the contract path. exact-path needs
        # no rename and appeared-unnamed must not get one: renaming a package
        # this code could not name would put an unidentified asset at the
        # street's path, which is worse than a box.
        if how in ("exact-name-different-folder", "name-contains-the-asset-id"):
            want_pkg = package_path(asset_id)
            if str(path) != want_pkg:
                try:
                    if unreal.EditorAssetLibrary.rename_asset(str(path), want_pkg):
                        detail["renamed"] = True
                        o2 = unreal.load_asset(object_path(asset_id))
                        if o2 is not None:
                            obj = o2
                            detail["loadedFrom"] = want_pkg
                except Exception as e:
                    report.append("rename-refused=%s" % str(e).split("\n")[0][:60])
        if not isinstance(obj, unreal.StaticMesh):
            # A GLB CAN IMPORT AS SOMETHING ELSE. The constraint that an .hdr
            # imports as a 2D texture has the same shape: what it loaded AS is
            # a reading, not an assumption, so it is named.
            report.append("%s-loaded-as=%s" % (asset_id, type(obj).__name__))
            return None, route_name + "/loaded-as-" + type(obj).__name__, detail
        return obj, route_name + "/" + how, detail

    return None, "none-of-%d-candidates/%s" % (len(routes), detail["resolvedVia"]), detail


def run_in_unreal():
    """Import every asset the street asks for, plus the named extras, reading
    every result back off the engine. Returns (line, manifest_dict)."""
    import unreal

    root = repo_root()
    try:
        spec, spec_path = load_spec()
    except Exception as e:
        return ("propImportStatus=NO-SPEC propImportReturn=2 "
                "propNote=%s" % str(e).replace(" ", "~")[:120],
                {"schema": "ledger.prop-mesh-import/1",
                 "measuredBy": "unreal/NOTHING-MEASURED-no-spec"})

    asked = assets_asked(spec)
    pieces = len(mesh_pieces(spec))
    boxes, _ = box_per_asset(spec)
    report = []
    readings, failures = [], []
    sources = imported = saved = 0
    vias, details = [], []
    extras = []
    # HOW MANY MESHES EACH SOURCE FILE HOLDS, read before the import rather
    # than inferred from what appeared, so the cause is on the line beside the
    # effect. pavement_sign's three packages in run 3 are three mesh nodes in
    # one GLB; that is readable from the file and was not read.
    parts = []

    # ASK THE ENGINE WHAT IT CAN DO BEFORE ASKING IT TO DO ANYTHING. Run 1
    # spent its whole import loop discovering, sixteen times, that no route
    # answered, and then reported the count rather than the cause.
    probe_sources = [os.path.join(root, glb_source(a)) for a, _ in asked[:3]]
    probe_sources = [q for q in probe_sources if os.path.exists(q)]
    can_ok, can_asked, plugin_names, api_names = _engine_gltf_probe(
        unreal, probe_sources, report)

    # A2. CLEAR THE CONTRACT PATHS FIRST. The agent workspace on that runner
    # is persistent, so an asset left by an earlier run sits in `before` and a
    # perfect re-import of it appears in neither `before` nor `after`: the
    # resolver then reads nothing-appeared over an import that worked. Deleting
    # first is what makes `new = after - before` mean what it says. Counted,
    # because a deletion nobody counted is a deletion nobody can audit.
    deleted = 0
    for asset_id, _names in asked:
        try:
            if unreal.load_asset(object_path(asset_id)) is not None:
                if unreal.EditorAssetLibrary.delete_asset(package_path(asset_id)):
                    deleted += 1
        except Exception as e:
            report.append("predelete-refused/%s=%s"
                          % (asset_id, str(e).split("\n")[0][:50]))

    todo = [(a, boxes[a]) for a, _ in asked] + [(e, None) for e in EXTRA_ASSETS]
    for asset_id, box in todo:
        is_extra = box is None
        abs_glb = os.path.join(root, glb_source(asset_id))
        # THE SOURCE'S OWN MESH COUNT, FOR EVERY ASSET, INCLUDING THE ONES
        # THAT THEN FAIL. A failure reason that names the cause is worth a
        # round trip on its own.
        mesh_names = glb_mesh_names(abs_glb) if os.path.exists(abs_glb) else None
        nparts = None if mesh_names is None else len(mesh_names)
        if not is_extra:
            parts.append((asset_id, nparts))
        part_note = ("/sourceParts=%d=%s" % (nparts, ",".join(mesh_names[:3]))
                     if nparts and nparts > 1 else "")
        if not os.path.exists(abs_glb):
            (extras if is_extra else failures).append((asset_id, "no-glb-at-" + glb_source(asset_id).replace(os.sep, "/")))
            continue
        if not is_extra:
            sources += 1
        if not safe_asset_id(asset_id):
            (extras if is_extra else failures).append((asset_id, "asset-id-is-not-a-legal-package-name"))
            continue
        mesh, via, det = _import_one(unreal, abs_glb, asset_id, report)
        det["sourceParts"] = nparts
        det["sourceMeshNames"] = mesh_names
        vias.append(via)
        details.append((asset_id, det))
        if mesh is None:
            (extras if is_extra else failures).append(
                (asset_id, "did-not-load-back/" + via + part_note))
            continue
        if not is_extra:
            imported += 1
        # BOUNDS FIRST, BECAUSE THE BOX IS SIZED FROM THEM. Reading the mesh's
        # own bounds does not touch the asset, and the collision box wants the
        # measured extent rather than the spec's, so that a wrong axis
        # convention cannot put a box where the mesh is not.
        origin, extent, bvia = _bounds_of(unreal, mesh, report)
        cstate = _ensure_collision(unreal, mesh, origin, extent, report)
        ok_save = False
        try:
            ok_save = bool(unreal.EditorAssetLibrary.save_asset(package_path(asset_id), False))
        except Exception as e:
            report.append("%s-save-refused=%s" % (asset_id, str(e).split("\n")[0][:80]))
        collidable = collidable_word(cstate["bodySetup"], cstate["simplePrims"],
                                    cstate["traceFlag"], extent)
        if is_extra:
            extras.append((asset_id,
                           "imported/saved=%s/simplePrims=%s/collidable=%s/extentUu=%s"
                           % ("yes" if ok_save else "NO",
                              prims_word(cstate["simplePrims"],
                                         cstate["simplePrimsVia"]),
                              flat(collidable),
                              "%.1f,%.1f,%.1f" % extent if extent else "unread")))
            continue
        if ok_save:
            saved += 1
        if extent is None:
            failures.append((asset_id, "bounds-unreadable/" + bvia))
            continue
        r = bounds_reading(asset_id, box, origin, extent)
        r["materialSlots"] = _material_slots(unreal, mesh, report)
        r.update(cstate)
        r["collidable"] = collidable
        r["sourceParts"] = nparts
        r["sourceMeshNames"] = mesh_names
        r["staticMeshesAppeared"] = sum(
            1 for v in (det.get("appearedClasses") or {}).values()
            if str(v) == "StaticMesh")
        r["boundsVia"] = bvia
        r["importVia"] = via
        r["saved"] = bool(ok_save)
        r["objectPath"] = object_path(asset_id)
        r["piecesUsingIt"] = len(dict(asked).get(asset_id, []))
        readings.append(r)

    # The uasset bytes on disk, because an asset the editor says it saved and
    # a file that exists are different facts.
    total_bytes = 0
    content = os.path.join(root, "ue-probe", "Content", "Ledger", "Props")
    if os.path.isdir(content):
        for f in os.listdir(content):
            if f.endswith(".uasset"):
                total_bytes += os.path.getsize(os.path.join(content, f))

    # NOT a GLTF-name test. See importer_candidates(): Interchange is where
    # the importer lives and its plugin names say nothing about glTF.
    importer_plugins = importer_candidates(plugin_names)
    exporter_found = any("GLTF" in n.upper() and "EXPORT" in n.upper()
                         for n in plugin_names)
    gltf_block = ("propGltfImporter=%s propGltfCanTranslate=%d/%d "
                  "propGltfPluginsEnabled=%s propGltfApi=%s"
                  % (gltf_verdict(exporter_found, importer_plugins,
                                  can_ok, can_asked),
                     can_ok, can_asked,
                     ";".join(plugin_names[:8]) if plugin_names else "none-reported",
                     ";".join(api_names) if api_names else "none-of-4"))
    if len(plugin_names) > 8:
        gltf_block += " propGltfPluginsCapped=(+%d~more~not~shown)" % (len(plugin_names) - 8)

    multi = [r["asset"] for r in readings if r.get("materialSlots", -1) > 1]
    unread_slots = [r["asset"] for r in readings if r.get("materialSlots", -1) < 0]
    # ONE TALLY, READ TWICE. The status word and propCollidable come from the
    # same function over the same population, which is what run 3's pair of
    # disagreeing collision numbers could not do.
    yes_n, unk_n, _no_n, _m = collidable_tally(readings, saved)
    status = import_status(len(asked), sources, imported, saved, yes_n, unk_n)
    via_word = vias[0] if vias and all(v == vias[0] for v in vias) else \
        ("mixed-over-%d" % len(vias) if vias else "nothing-measured")
    extra_field = "propExtras=" + (
        ";".join("%s=%s" % (a, str(w).replace(" ", "~")) for a, w in extras)
        if extras else "none")
    lamp = "not-attempted"
    for a, w in extras:
        if a == "lamp_post_01":
            lamp = str(w).replace(" ", "~")
    # ASKED ONCE, USED TWICE. Two calls would double every refusal line these
    # probes add to the report, and propNote counts repeats now.
    subsys = _subsystem_probe(unreal, report)
    pipe = _pipeline_probe(unreal, report)
    engine_block = engine_field(subsys, pipe)
    line = prop_line(status, len(asked), pieces, sources, imported, saved,
                     readings, failures, via_word,
                     collision_field(readings, saved),
                     extra_field + " propMaterialSlotsOver1=%d/%d propMaterialSlotsUnread=%d "
                     "propSlotNote=the-street-overwrites-slot-0-only"
                     % (len(multi), len(readings), len(unread_slots)),
                     total_bytes,
                     note_value(report),
                     gltf_block, accepting_field(readings, failures, sources),
                     preexisting_field(deleted, len(asked)) + " "
                     + lookup_field(details),
                     source_parts_field(parts), engine_block)
    man = manifest("unreal/engine-readback", spec_path, asked, readings,
                   failures, [{"asset": a, "reading": w} for a, w in extras])
    man["line"] = line
    man["lampPost01"] = lamp
    man["gltf"] = {"canTranslate": can_ok, "asked": can_asked,
                   "enabledPlugins": plugin_names, "api": api_names}
    man["acceptingCase"] = accepting_field(readings, failures, sources)
    man["lookups"] = [{"asset": a, "detail": d} for a, d in details]
    man["reportLines"] = report
    # THE THINGS THAT DO NOT FIT ON THE LINE AND ARE THE WHOLE POINT OF THE
    # NEXT RUN: which subsystems this commandlet has, which import-time option
    # names this engine exposes, and how many meshes each source file holds.
    man["subsystems"] = subsys
    man["pipelineOpts"] = pipe
    man["sourceParts"] = [{"asset": a, "meshes": n} for a, n in parts]
    man["collisionStat"] = ("simplePrims is a count read off the body setup "
                            "and is a PROXY; collidable is the asset's own "
                            "answer and is not a sweep in a level")
    return line, man


# ---- writers. The evidence channel is a file, not a log tail --------------


def _beside_project(name):
    try:
        import unreal
        root = unreal.Paths.project_dir()
    except Exception:
        root = os.path.join(repo_root(), "ue-probe") + os.sep
    return os.path.join(root, name)


def _write(line, man):
    path = _beside_project("ue-prop-meshes.txt")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print("import_prop_meshes: could not write %s (%s)" % (path, e))
    jpath = _beside_project("ue-prop-meshes.json")
    try:
        with open(jpath, "w", encoding="utf-8") as f:
            json.dump(man, f, indent=1, sort_keys=True)
    except Exception as e:
        print("import_prop_meshes: could not write %s (%s)" % (jpath, e))
    print(line)
    try:
        import unreal
        unreal.log("LEDGER " + line)
    except Exception:
        pass


def _inside_unreal():
    try:
        import unreal  # noqa: F401
        return True
    except Exception:
        return False


def measure_only():
    """The container half on its own: the printed series the engine-side bound
    will one day be set from, and the claim that makes scale 1 correct."""
    root = repo_root()
    sys.path.insert(0, os.path.join(root, "tools", "meshgen"))
    import meshgen
    spec, spec_path = load_spec()
    rows = measure_against_glb(spec, meshgen.glb_stats)
    asked = assets_asked(spec)
    measured = [r for r in rows if "worstMm" in r]
    print("spec box minus GLB measured dims, mm, worst axis per asset, "
          "descending over %d of %d assets:" % (len(measured), len(asked)))
    for r in sorted(measured, key=lambda r: -r["worstMm"]):
        print("  %8.4f  %-24s baseY=%+.4f verts=%-6d meshes=%-2s %s"
              % (r["worstMm"], r["asset"], r["baseY"], r["verts"],
                 r["sourceMeshes"], r["specBoxM"]))
    # THE SECOND SERIES, PRINTED AND NOT GATED. One uasset is kept per asset,
    # so a source holding two meshes loses one of them to a folder the street
    # never reads. wooden_crate_01 is the whole of the 44 mm bounds outlier
    # above: the kept body measures 1.000679 m tall and the file measures
    # 1.0447, and the difference is the lid.
    multi = sorted(((r["sourceMeshes"], r["asset"], r["sourceMeshNames"])
                    for r in measured if (r["sourceMeshes"] or 0) > 1),
                   reverse=True)
    print("meshes per source file, the ones above one, over %d assets:"
          % len(measured))
    if not multi:
        print("  none: every source holds exactly one mesh")
    for n, a, names in multi:
        print("  %d  %-24s %s" % (n, a, ",".join(names or [])))
    if not measured:
        print("  NOTHING MEASURED: no asset had a GLB on disk")
        return 2
    worst = max(r["worstMm"] for r in measured)
    print("worstMm=%.4f/over=%d/tolMm=%.3f verdict=%s"
          % (worst, len(measured), SPEC_VS_GLB_TOL_MM,
             "SPEC-BOX-IS-THE-GLB" if worst <= SPEC_VS_GLB_TOL_MM else "RESCALED"))
    # WRITING IS OPT-IN. This mode exists to PRINT the series, and a tool that
    # drops a file into the evidence directory every time somebody reads a
    # number is a tool that makes stale evidence.
    if "--write-manifest" in sys.argv:
        man = manifest("container/glb-only", spec_path, asked, rows, [], [])
        out = os.path.join(root, "production", "d1-probe",
                           "prop-mesh-measured.json")
        try:
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(man, f, indent=1, sort_keys=True)
            print("wrote=%s" % out)
        except Exception as e:
            print("could not write %s (%s)" % (out, e))
    return 0 if worst <= SPEC_VS_GLB_TOL_MM else 2


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if "--measure" in sys.argv:
        return measure_only()
    if not _inside_unreal():
        print("import_prop_meshes: NOTHING MEASURED, no unreal module. "
              "Use --selftest or --measure outside the editor.")
        return 1
    line, man = run_in_unreal()
    _write(line, man)
    m = re.search(r"propImportReturn=(\d+)", line)
    return int(m.group(1)) if m else 2


if __name__ == "__main__":
    # SYS.EXIT IS FOR A REAL PROCESS ONLY, for the reason the material
    # generator states: inside the editor this runs on an embedded interpreter
    # that is not exiting anything, and raising SystemExit there is a
    # plausible way to turn a script that worked into a process that reports
    # failure. The verdict travels in the file as propImportReturn.
    _code = main()
    if _inside_unreal():
        print("import_prop_meshes: returning %d without sys.exit (inside the "
              "editor; the verdict is propImportReturn in ue-prop-meshes.txt)"
              % _code)
    else:
        sys.exit(_code)
