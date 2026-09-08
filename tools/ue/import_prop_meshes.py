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
/Game/Ledger/Props/SM_<asset>, plus simple collision on each, because a
mesh without a body setup reads as placed and walks through. The names are a
contract with VignetteShot.cpp's mesh branch, which derives the object path
from the piece's own "asset" field and nothing else, and --selftest reads
that derivation out of the C++ rather than trusting the two were kept in
step by hand.

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


def import_status(asked, sources, imported, saved, collided):
    """The one word. It needs every asset the street asks for to have become a
    saved uasset, for the reason MADE needed every connection in the material
    generator: a street missing one prop is a street with a box in it, and the
    scene line is the only place that would have shown it.

    COLLISION IS PART OF THE WORD and not a footnote. A mesh with no body
    setup places, renders, photographs clean and lets a walking Character
    through it, and the walk clip is the deliverable. So a full import with no
    collision is IMPORTED-NO-COLLISION, which returns non-zero, rather than
    IMPORTED with a quiet count beside it."""
    if asked == 0:
        return "NOTHING-ASKED"
    if sources == 0:
        return "NO-SOURCES"
    if imported == 0:
        return "NOTHING-IMPORTED"
    if saved < asked:
        return "PARTIAL"
    if collided < saved:
        return "IMPORTED-NO-COLLISION"
    return "IMPORTED"


def import_return(status):
    """0 only for the word that means every asset the street asks for is a
    saved uasset with collision on it. The verdict travels in the FILE as
    propImportReturn; the editor process's exit code is the editor's, not
    this script's, which is the pair run 19 of the material generator could
    not explain."""
    return 0 if status == "IMPORTED" else 2


def prop_line(status, asked, pieces, sources, imported, saved, collided,
              readings, failures, via, collision_via, extras, uasset_bytes,
              note, gltf_block="", accepting_block=""):
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
                           simple collision primitive, over saved. This is
                           the number the walk clip lives on.
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
            "propCollisionPrims=%d/%d propCollisionVia=%s "
            "propImportVia=%s propPackageDir=%s propNamePattern=%s<asset> "
            "%s %s "
            "%s propBoundsBound=NONE-YET/this-run-prints-the-series "
            "propBoundsStat=spec-box-minus-engine-bounds-at-worst-over-assets "
            "%s %s "
            "propScalePolicy=1/never-scaled/dims-policy-forbids-it "
            "propLampPost01=%s propUassetBytes=%d "
            "propVerdictIs=propImportReturn/not-the-editor-process-exit "
            "propNote=%s"
            % (status, import_return(status),
               asked, pieces,
               sources, asked, imported, asked, saved, asked,
               collided, saved, collision_via,
               via, PACKAGE_DIR, UASSET_PREFIX,
               gltf_block if gltf_block else "propGltfImporter=nothing-measured",
               accepting_block if accepting_block else
               "propAcceptingCase=nothing-measured",
               worst_bounds(readings),
               pivot_field(readings),
               fallback_field(failures, asked),
               extras, uasset_bytes,
               str(note).replace(" ", "~") if note else "none"))


def accepting_field(readings, failures, sources_found):
    """A7_gully_grate's own key. It answers, in one value, the only question
    the accepting case asks: is the grate a real mesh with collision, and how
    far off did it land.

    A KEY THAT IS ABSENT WHEN THE THING FAILED IS NOT A KEY. Every path
    produces a word here, including the path where the asset was never
    reached at all, because "no propAcceptingCase on the line" and "the grate
    is fine" look identical to a grep."""
    for r in readings:
        if r.get("asset") == ACCEPTING_ASSET:
            return ("propAcceptingCase=piece=%s/asset=%s/RESOLVED/saved=%s/"
                    "collisionPrims=%d/materialSlots=%d/worstOrderedMm=%.4f/"
                    "worstSortedMm=%.4f"
                    % (ACCEPTING_PIECE, ACCEPTING_ASSET,
                       "yes" if r.get("saved") else "NO",
                       r.get("collisionPrims", -1), r.get("materialSlots", -1),
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
        })
    return rows


def load_spec(path=None):
    p = path or os.path.join(repo_root(), "production", "specs",
                             "vignette-pieces.json")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f), p


# ---- the selftest, which runs with no engine anywhere near it -------------


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
    good["collisionPrims"] = 1
    good["materialSlots"] = 1
    ok("a resolved grate says RESOLVED with its collision count",
       "RESOLVED" in accepting_field([good], [], 16)
       and "collisionPrims=1" in accepting_field([good], [], 16),
       accepting_field([good], [], 16))
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
            "IMPORTED-NO-COLLISION")))

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
    line = prop_line("IMPORTED", 16, 23, 16, 16, 16, 16, rs,
                     [("x", "a reason with spaces")], "asset-import-task",
                     "static-mesh-editor-subsystem",
                     "propExtras=lamp_post_01=ok", 123456,
                     "a note with spaces",
                     "propGltfImporter=" + gltf_verdict(True, [], 0, 3)
                     + " propGltfCanTranslate=0/3",
                     accepting_field([], [(ACCEPTING_ASSET, "did not load back")], 16))
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


def _try(calls, report):
    """Take the first route that answers, and RECORD WHICH ONE, the same shape
    make_base_material.py uses for a pin name. A fallback that works silently
    is a fallback nobody knows they are depending on.

    calls is a list of (name, zero-argument callable). Returns
    (value, via) where via is the name that answered or none-of-N."""
    for name, fn in calls:
        try:
            v = fn()
            if v is not None:
                return v, name
        except Exception as e:
            report.append("%s-refused=%s" % (name, str(e).split("\n")[0][:80]))
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


def _add_collision(unreal, mesh, report):
    """Simple collision on the imported mesh, and THE COUNT IS READ BACK.

    A mesh with no body setup places, renders and photographs clean, and a
    walking Character falls straight through it. That is the failure this
    whole step exists to prevent, so the number that ends up on the verdict
    is what the engine answers AFTER the call, never the call returning."""
    def count():
        sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        return sub.get_simple_collision_count(mesh)

    def count_legacy():
        return unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh)

    before, _ = _try([("subsystem", count), ("legacy-library", count_legacy)],
                     report)
    if before is not None and before > 0:
        # WRITE-ON-CHANGE. A mesh the importer already gave collision to is
        # not given a second box on top of the first.
        return before, "already-had-%d" % before

    def add():
        sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        sub.add_simple_collisions(mesh, unreal.ScriptingCollisionShapeType.BOX)
        return sub.get_simple_collision_count(mesh)

    def add_legacy():
        unreal.EditorStaticMeshLibrary.add_simple_collisions(
            mesh, unreal.ScriptingCollisionShapeType.BOX)
        return unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh)

    after, via = _try([("subsystem-box", add), ("legacy-box", add_legacy)],
                      report)
    return (after if after is not None else 0), via


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


def _import_one(unreal, abs_glb, asset_id, report):
    """One GLB to one uasset. Returns the loaded UStaticMesh or None, and the
    route that took. LOADED BACK, not "the task returned": an import task that
    reports success over an asset nothing can load is exactly the shape of
    failure this project keeps finding."""
    name = uasset_name(asset_id)

    def via_task():
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", abs_glb)
        task.set_editor_property("destination_path", PACKAGE_DIR)
        task.set_editor_property("destination_name", name)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", False)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        return unreal.load_asset(object_path(asset_id))

    def via_interchange():
        mgr = unreal.InterchangeManager.get_interchange_manager_scripted()
        src = unreal.InterchangeManager.create_source_data(abs_glb)
        params = unreal.ImportAssetParameters()
        params.is_automated = True
        mgr.import_asset(PACKAGE_DIR, src, params)
        return unreal.load_asset(object_path(asset_id))

    obj, via = _try([("asset-import-task", via_task),
                     ("interchange-manager", via_interchange)], report)
    if obj is None:
        return None, via
    if not isinstance(obj, unreal.StaticMesh):
        # A GLB CAN IMPORT AS SOMETHING ELSE. The constraint that an .hdr
        # imports as a 2D texture has the same shape: what it loaded AS is a
        # reading, not an assumption, so it is named.
        report.append("%s-loaded-as=%s" % (asset_id, type(obj).__name__))
        return None, via + "/loaded-as-" + type(obj).__name__
    return obj, via


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
    sources = imported = saved = collided = 0
    vias, coll_vias = [], []
    extras = []

    # ASK THE ENGINE WHAT IT CAN DO BEFORE ASKING IT TO DO ANYTHING. Run 1
    # spent its whole import loop discovering, sixteen times, that no route
    # answered, and then reported the count rather than the cause.
    probe_sources = [os.path.join(root, glb_source(a)) for a, _ in asked[:3]]
    probe_sources = [q for q in probe_sources if os.path.exists(q)]
    can_ok, can_asked, plugin_names, api_names = _engine_gltf_probe(
        unreal, probe_sources, report)

    todo = [(a, boxes[a]) for a, _ in asked] + [(e, None) for e in EXTRA_ASSETS]
    for asset_id, box in todo:
        is_extra = box is None
        abs_glb = os.path.join(root, glb_source(asset_id))
        if not os.path.exists(abs_glb):
            (extras if is_extra else failures).append((asset_id, "no-glb-at-" + glb_source(asset_id).replace(os.sep, "/")))
            continue
        if not is_extra:
            sources += 1
        if not safe_asset_id(asset_id):
            (extras if is_extra else failures).append((asset_id, "asset-id-is-not-a-legal-package-name"))
            continue
        mesh, via = _import_one(unreal, abs_glb, asset_id, report)
        vias.append(via)
        if mesh is None:
            (extras if is_extra else failures).append((asset_id, "did-not-load-back/" + via))
            continue
        if not is_extra:
            imported += 1
        prims, cvia = _add_collision(unreal, mesh, report)
        coll_vias.append(cvia)
        ok_save = False
        try:
            ok_save = bool(unreal.EditorAssetLibrary.save_asset(package_path(asset_id), False))
        except Exception as e:
            report.append("%s-save-refused=%s" % (asset_id, str(e).split("\n")[0][:80]))
        origin, extent, bvia = _bounds_of(unreal, mesh, report)
        if is_extra:
            extras.append((asset_id,
                           "imported/saved=%s/collisionPrims=%d/extentUu=%s"
                           % ("yes" if ok_save else "NO", prims,
                              "%.1f,%.1f,%.1f" % extent if extent else "unread")))
            continue
        if ok_save:
            saved += 1
        if prims > 0:
            collided += 1
        if extent is None:
            failures.append((asset_id, "bounds-unreadable/" + bvia))
            continue
        r = bounds_reading(asset_id, box, origin, extent)
        r["materialSlots"] = _material_slots(unreal, mesh, report)
        r["collisionPrims"] = prims
        r["collisionVia"] = cvia
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
    status = import_status(len(asked), sources, imported, saved, collided)
    via_word = vias[0] if vias and all(v == vias[0] for v in vias) else \
        ("mixed-over-%d" % len(vias) if vias else "nothing-measured")
    cvia_word = coll_vias[0] if coll_vias and all(v == coll_vias[0] for v in coll_vias) else \
        ("mixed-over-%d" % len(coll_vias) if coll_vias else "nothing-measured")
    extra_field = "propExtras=" + (
        ";".join("%s=%s" % (a, str(w).replace(" ", "~")) for a, w in extras)
        if extras else "none")
    lamp = "not-attempted"
    for a, w in extras:
        if a == "lamp_post_01":
            lamp = str(w).replace(" ", "~")
    line = prop_line(status, len(asked), pieces, sources, imported, saved,
                     collided, readings, failures, via_word, cvia_word,
                     extra_field + " propMaterialSlotsOver1=%d/%d propMaterialSlotsUnread=%d "
                     "propSlotNote=the-street-overwrites-slot-0-only"
                     % (len(multi), len(readings), len(unread_slots)),
                     total_bytes,
                     "/".join(report[:4]) if report else "none",
                     gltf_block, accepting_field(readings, failures, sources))
    man = manifest("unreal/engine-readback", spec_path, asked, readings,
                   failures, [{"asset": a, "reading": w} for a, w in extras])
    man["line"] = line
    man["lampPost01"] = lamp
    man["gltf"] = {"canTranslate": can_ok, "asked": can_asked,
                   "enabledPlugins": plugin_names, "api": api_names}
    man["acceptingCase"] = accepting_field(readings, failures, sources)
    man["reportLines"] = report
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
        print("  %8.4f  %-24s baseY=%+.4f verts=%-6d %s"
              % (r["worstMm"], r["asset"], r["baseY"], r["verts"],
                 r["specBoxM"]))
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
