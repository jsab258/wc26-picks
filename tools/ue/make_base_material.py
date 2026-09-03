"""Make the Unreal base material for the D1b vignette, from a script, in CI.

    UnrealEditor-Cmd.exe LedgerProbe.uproject -run=pythonscript \
        -script="tools/ue/make_base_material.py" -unattended -nopause -nosplash
    python3 tools/ue/make_base_material.py --selftest   # runs without Unreal

WHY IT EXISTS AT ALL, which is the whole of D1 measurement (a).

Unreal cannot build a material at runtime: a material is compiled shader
code, the shader compiler is editor-only, and a packaged game can only make
INSTANCES of materials that already exist as assets. So Phase C needs one
binary asset. The project's standing rule is that no human opens the editor
and no human hand-makes a uasset, and Jafar's decision rule for D1 (second
amendment, 2 September) says Unreal fails measurement (a) if it turns out to
depend on hand edits. This script is the answer to that question in
executable form: the asset is a BUILD PRODUCT, made by a script that runs in
the cook step and is committed like any other build output.

If this script cannot make the material, that IS the D1 answer and it must be
reported as one rather than worked around by opening the editor.

WHAT IT MAKES. One material, /Game/Ledger/M_LedgerSurface, with three texture
parameters and two scalar parameters:

    BaseColorMap   -> Base Color     the pack's <surface>.jpg
    NormalMap      -> Normal         the pack's <surface>_n.jpg
    RoughnessMap   -> Roughness      the pack's <surface>_r.jpg
    TilingU/TilingV                  how many times the maps repeat

THE PARAMETER NAMES ARE A CONTRACT WITH C++ that nothing at runtime can
check: a dynamic instance asked for a parameter the material does not have
sets nothing, returns nothing and logs nothing, and the frame comes back
untextured with every count green. The names live in
ue-probe/Source/LedgerProbe/Public/SurfaceBind.h, which is the tested layer,
and --selftest reads them out of that file and compares them to the names
below. That is the one half of this script that can be run in the container
that writes it, so it is the half that is run before every dispatch.

EVERY WIRING STEP IS INDIVIDUALLY GUARDED AND COUNTED. A material with a
base colour and no normal map is worth having; a script that dies halfway
and saves nothing is not. What landed is written to ue-material.txt beside
the project as key=value, because a log tail is not an evidence channel in
this project and a committed file is.

WHAT RUN 19 PRINTED, AND WHY THIS FILE NOW DECIDES ITS OWN VERDICT.
Run 19 shipped `materialScriptExit=1` beside `materialStatus=MADE
materialParamsMade=3/3 materialConnections=12/14`, and both cannot be the
answer. Two separate faults produced that pair:

  1. THE EXIT CODE WAS NOT THIS SCRIPT'S. main() returns 0 or 2 and never 1,
     so a 1 cannot have come from here: the workflow was reading the exit
     code of UnrealEditor-Cmd.exe, which also shuts an editor down, and
     calling it the script's. The verdict this file is sure of is now
     WRITTEN INTO THE EVIDENCE FILE as materialScriptReturn, and the
     process's own code is named for what it is by the step that reads it.
     sys.exit is not called when this runs inside the editor either: raising
     SystemExit through an embedded interpreter is a plausible way to turn a
     successful script into a non-zero process, and nothing is gained by it.

  2. MADE WAS OVERCLAIMING. It asked only whether the asset saved and whether
     three parameters exist, so twelve of fourteen connections wired read as
     a clean pass; the two that refused were TexCoord into both component
     masks, which is the head of the UV chain every sampler hangs off. A
     material whose UVs are unconnected is not a made material. The status
     now needs every connection the script asked for, and the return code is
     a function OF THE STATUS, so no run can print a failure beside MADE
     again.

THE STATUS AND THE RETURN CODE ARE COMPUTED BY PURE FUNCTIONS AT THE TOP OF
THIS FILE and exercised by --selftest, which runs in the container that
writes them. Everything that needs Unreal supplies numbers; nothing that
needs Unreal decides what the numbers mean.
"""

import os
import sys

# THE CONTRACT. Read by --selftest out of the tested header, never retyped
# there. Order is base colour, normal, roughness, matching MapParam().
TEXTURE_PARAMS = ["BaseColorMap", "NormalMap", "RoughnessMap"]
SCALAR_PARAMS = ["TilingU", "TilingV"]

PACKAGE = "/Game/Ledger"
ASSET = "M_LedgerSurface"
ASSET_PATH = PACKAGE + "/" + ASSET

# DEFAULT TEXTURES ARE TRIED IN ORDER AND THE ONE THAT ANSWERED IS NAMED. A
# texture parameter with no default can fail to compile, and an engine asset
# path that moved between versions is exactly the kind of assumption that
# costs a 25 minute round trip to discover.
COLOUR_DEFAULTS = [
    "/Engine/EngineResources/DefaultTexture",
    "/Engine/EngineResources/WhiteSquareTexture",
    "/Engine/EngineMaterials/DefaultDiffuse",
]
NORMAL_DEFAULTS = [
    "/Engine/EngineMaterials/DefaultNormal",
    "/Engine/EngineResources/DefaultTextureNormal",
]


# ---- the verdict, decided by pure functions the container can run --------
#
# EVERY NUMBER BELOW COMES FROM THE EDITOR AND EVERY JUDGEMENT ABOUT IT
# HAPPENS HERE, for the standing reason: a formatter or a status rule written
# where the tests cannot reach it ships unrun, and an unrun rule printing a
# plausible word is the silent-instrument failure this project keeps paying
# for. --selftest exercises all three of these before any dispatch.

STATUS_MADE = "MADE"
STATUS_PARTIAL = "PARTIAL"
STATUS_NOT_SAVED = "NOT-SAVED"


def material_status(saved, params_made, params_asked, wired, asked):
    """One word for what this run of the script achieved.

    MADE needs all three of: the asset saved to disk, every texture parameter
    the C++ contract names, and every connection the script asked the editor
    to make. The third clause is new. Run 19 wired 12 of 14 and still said
    MADE, and the two that refused were TexCoord into the component masks:
    the head of the UV chain that all three samplers hang off, so every
    sampler in that material reads one texel. A material whose UV chain is
    unconnected has not been made.

    PARTIAL is a saved asset that fell short of one of those, which is worth
    keeping and is not a pass. NOT-SAVED is nothing on disk at all.
    """
    if not saved:
        return STATUS_NOT_SAVED
    if params_made < params_asked:
        return STATUS_PARTIAL
    if asked <= 0 or wired < asked:
        return STATUS_PARTIAL
    return STATUS_MADE


def material_return(status):
    """The script's own return code, a FUNCTION of the status and never a
    second opinion about it. Two numbers derived from one variable are one
    number twice, and that is the point here: the pair that made run 19
    unreadable cannot be printed again."""
    return 0 if status == STATUS_MADE else 2


def material_line(status, params_made, params_asked, wired, asked, existed,
                  colour_from, normal_from, defaults_bound, defaults_asked,
                  saved, notes):
    """The one line the workflow copies into the build verdict.

    No spaces inside any value: every reader of these files splits on
    whitespace. Every count ships its denominator, including the engine
    default textures, which run 19 reported as `none-of-2-candidates` with no
    total beside it.
    """
    return ("materialStatus=%s materialScriptReturn=%d materialPath=%s "
            "materialExistedBefore=%s materialParams=%s materialParamsMade=%d/%d "
            "materialScalars=%s materialConnections=%d/%d "
            "materialColourDefault=%s materialNormalDefault=%s "
            "materialDefaultsBound=%d/%d materialSaved=%s "
            "materialVerdictIs=materialScriptReturn/not-the-editor-process-exit "
            "materialNote=%s"
            % (status, material_return(status), ASSET_PATH,
               "yes" if existed else "no",
               "/".join(TEXTURE_PARAMS), params_made, params_asked,
               "/".join(SCALAR_PARAMS), wired, asked,
               str(colour_from).replace(" ", "~"),
               str(normal_from).replace(" ", "~"),
               defaults_bound, defaults_asked,
               "yes" if saved else "NO",
               "/".join(notes) if notes else "none"))


def selftest():
    """The name contract, checked against the tested header. Accepting case
    first: the live SurfaceBind.h is the accepting fixture, as the project's
    rule for tools that check the project itself requires."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(here))
    header = os.path.join(root, "ue-probe", "Source", "LedgerProbe",
                          "Public", "SurfaceBind.h")
    checks = 0
    bad = []
    if not os.path.exists(header):
        print("make_base_material --selftest: NOTHING MEASURED, no %s" % header)
        return 1
    text = open(header, "r", encoding="utf-8").read()
    # The header states the parameter names in MapParam(); read them rather
    # than trusting that the two lists were kept in step by hand.
    at = text.find("const char* P[3] =")
    if at < 0:
        print("make_base_material --selftest: NOTHING MEASURED, "
              "SurfaceBind.h has no MapParam list to read")
        return 1
    line = text[at:text.find(";", at)]
    names = [p.strip().strip('"') for p in
             line[line.find("{") + 1:line.find("}")].split(",")]
    checks += 1
    if names != TEXTURE_PARAMS:
        bad.append("the header asks for %s and this script makes %s"
                   % (names, TEXTURE_PARAMS))
    # And the scalars, which the binder sets per piece. They are set in the
    # module rather than named in the header, so the whole source tree is the
    # haystack: the contract is "some C++ site sets this", not "this file
    # mentions it".
    src = os.path.join(root, "ue-probe", "Source")
    blob = ""
    files = 0
    for base, _dirs, found in os.walk(src):
        for n in found:
            if n.endswith((".cpp", ".h")):
                files += 1
                blob += open(os.path.join(base, n), "r", encoding="utf-8").read()
    for s in SCALAR_PARAMS:
        checks += 1
        if ('"%s"' % s) not in blob:
            bad.append("no C++ site in the %d source file(s) under ue-probe/Source "
                       "sets the scalar parameter %s" % (files, s))
    # ---- the verdict rule, both ways round, ACCEPTING CASE FIRST ---------
    # A guard shipped without a run in which it passes is a ratchet, and one
    # shipped without a run in which it fires is a claim. Both are here, and
    # the rejecting case is run 19's own numbers.
    cases = [
        # (saved, made, asked_params, wired, asked, status, return)
        (True, 3, 3, 14, 14, STATUS_MADE, 0),
        (True, 3, 3, 12, 14, STATUS_PARTIAL, 2),   # run 19, exactly
        (True, 2, 3, 14, 14, STATUS_PARTIAL, 2),
        (True, 3, 3, 0, 0, STATUS_PARTIAL, 2),     # nothing asked is not a pass
        (False, 3, 3, 14, 14, STATUS_NOT_SAVED, 2),
    ]
    for saved, made, pasked, wired, casked, want, want_code in cases:
        checks += 1
        got = material_status(saved, made, pasked, wired, casked)
        code = material_return(got)
        if got != want or code != want_code:
            bad.append("status(saved=%s made=%d/%d wired=%d/%d) gave %s/%d "
                       "and should give %s/%d"
                       % (saved, made, pasked, wired, casked, got, code,
                          want, want_code))
    # AND THE LINE ITSELF, because an unrun formatter printing a plausible
    # string is the fault this file exists on the tested side to avoid. The
    # rule every reader of these files depends on: one equals per token and
    # no spaces inside a value.
    line = material_line(STATUS_PARTIAL, 3, 3, 12, 14, False,
                         "/Engine/EngineResources/DefaultTexture",
                         "none-of-2-candidates", 1, 2, True,
                         ["texcoord-to-maskU-refused", "texcoord-to-maskV-refused"])
    checks += 1
    if [t for t in line.split() if t.count("=") != 1]:
        bad.append("the material line has a token that is not one key=value: %s"
                   % [t for t in line.split() if t.count("=") != 1])
    checks += 1
    if "materialStatus=PARTIAL" not in line or "materialScriptReturn=2" not in line:
        bad.append("the line does not carry the status and the return it was "
                   "built from: %s" % line)
    checks += 1
    if "materialDefaultsBound=1/2" not in line:
        bad.append("an engine default that did not resolve ships without its "
                   "denominator: %s" % line)
    print("    %s" % line)
    print("make_base_material --selftest: %d check(s), %d failure(s), "
          "params=%s scalars=%s header=%s"
          % (checks, len(bad), "/".join(TEXTURE_PARAMS), "/".join(SCALAR_PARAMS),
             os.path.relpath(header, root)))
    for b in bad:
        print("  FAIL %s" % b)
    return 0 if not bad else 2


def _first_that_loads(unreal, paths):
    for p in paths:
        try:
            a = unreal.EditorAssetLibrary.load_asset(p)
            if a is not None:
                return a, p
        except Exception:
            continue
    return None, "none-of-%d-candidates" % len(paths)


def main():
    if "--selftest" in sys.argv:
        return selftest()

    import unreal  # only inside the editor; the selftest above never gets here

    notes = []
    wired = 0
    asked = 0

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary

    existed = unreal.EditorAssetLibrary.does_asset_exist(ASSET_PATH)
    if existed:
        # ALWAYS REGENERATED. The asset is a build product and this script is
        # its only writer; an asset kept from a previous run could not be
        # shown to match the script that claims to have made it.
        unreal.EditorAssetLibrary.delete_asset(ASSET_PATH)

    mat = tools.create_asset(ASSET, PACKAGE, unreal.Material,
                             unreal.MaterialFactoryNew())
    if mat is None:
        _write("materialStatus=CREATE-FAILED materialPath=%s "
               "materialNote=asset-tools-returned-nothing" % ASSET_PATH)
        unreal.log_error("LEDGER: could not create %s" % ASSET_PATH)
        return 2

    colour_default, colour_from = _first_that_loads(unreal, COLOUR_DEFAULTS)
    normal_default, normal_from = _first_that_loads(unreal, NORMAL_DEFAULTS)

    # ---- the UV chain: TexCoord masked, scaled per axis, appended ----------
    # Two scalars rather than one, because a 42 metre carriageway 2.7 metres
    # wide tiled uniformly is 21 repeats along AND across, and the across is
    # what a camera in the street is looking at.
    def expr(cls, x, y):
        return mel.create_material_expression(mat, cls, x, y)

    def connect(a, out, b, inp, what):
        nonlocal wired, asked
        asked += 1
        try:
            if mel.connect_material_expressions(a, out, b, inp):
                wired += 1
                return True
        except Exception as e:
            notes.append("%s-threw" % what)
            return False
        notes.append("%s-refused" % what)
        return False

    def connect_prop(a, out, prop, what):
        nonlocal wired, asked
        asked += 1
        try:
            if mel.connect_material_property(a, out, prop):
                wired += 1
                return True
        except Exception:
            notes.append("%s-threw" % what)
            return False
        notes.append("%s-refused" % what)
        return False

    tc = expr(unreal.MaterialExpressionTextureCoordinate, -1100, 0)
    mask_u = expr(unreal.MaterialExpressionComponentMask, -900, -80)
    mask_u.set_editor_property("r", True)
    mask_u.set_editor_property("g", False)
    mask_u.set_editor_property("b", False)
    mask_u.set_editor_property("a", False)
    mask_v = expr(unreal.MaterialExpressionComponentMask, -900, 80)
    mask_v.set_editor_property("r", False)
    mask_v.set_editor_property("g", True)
    mask_v.set_editor_property("b", False)
    mask_v.set_editor_property("a", False)
    su = expr(unreal.MaterialExpressionScalarParameter, -900, -160)
    su.set_editor_property("parameter_name", SCALAR_PARAMS[0])
    su.set_editor_property("default_value", 1.0)
    sv = expr(unreal.MaterialExpressionScalarParameter, -900, 160)
    sv.set_editor_property("parameter_name", SCALAR_PARAMS[1])
    sv.set_editor_property("default_value", 1.0)
    mul_u = expr(unreal.MaterialExpressionMultiply, -700, -80)
    mul_v = expr(unreal.MaterialExpressionMultiply, -700, 80)
    app = expr(unreal.MaterialExpressionAppendVector, -520, 0)

    connect(tc, "", mask_u, "Input", "texcoord-to-maskU")
    connect(tc, "", mask_v, "Input", "texcoord-to-maskV")
    connect(mask_u, "", mul_u, "A", "maskU-to-mulU")
    connect(su, "", mul_u, "B", "tilingU-to-mulU")
    connect(mask_v, "", mul_v, "A", "maskV-to-mulV")
    connect(sv, "", mul_v, "B", "tilingV-to-mulV")
    connect(mul_u, "", app, "A", "mulU-to-append")
    connect(mul_v, "", app, "B", "mulV-to-append")

    # ---- the three samplers -----------------------------------------------
    # Each is wired on its own. A material with a base colour and no normal
    # map is worth having; a script that gives up halfway is not.
    made = []

    def sampler(name, y, sampler_type, default_tex, prop, out_pin, label):
        s = expr(unreal.MaterialExpressionTextureSampleParameter2D, -300, y)
        s.set_editor_property("parameter_name", name)
        try:
            if default_tex is not None:
                s.set_editor_property("texture", default_tex)
            s.set_editor_property("sampler_type", sampler_type)
        except Exception:
            notes.append("%s-default-or-samplertype-refused" % label)
        connect(app, "", s, "UVs", "%s-uvs" % label)
        if connect_prop(s, out_pin, prop, "%s-out" % label):
            made.append(name)
        return s

    st = unreal.MaterialSamplerType
    mp = unreal.MaterialProperty
    sampler(TEXTURE_PARAMS[0], -300, st.SAMPLERTYPE_COLOR, colour_default,
            mp.MP_BASE_COLOR, "RGB", "basecolor")
    sampler(TEXTURE_PARAMS[1], 0, st.SAMPLERTYPE_NORMAL, normal_default,
            mp.MP_NORMAL, "RGB", "normal")
    sampler(TEXTURE_PARAMS[2], 300, st.SAMPLERTYPE_LINEAR_GRAYSCALE,
            colour_default, mp.MP_ROUGHNESS, "R", "roughness")

    try:
        mel.recompile_material(mat)
    except Exception:
        notes.append("recompile-threw")
    saved = False
    try:
        saved = bool(unreal.EditorAssetLibrary.save_asset(ASSET_PATH))
    except Exception:
        notes.append("save-threw")

    # THE ENGINE DEFAULTS SHIP A DENOMINATOR. `none-of-2-candidates` with no
    # total beside it cannot be told from a run that never looked.
    defaults_bound = (1 if colour_default is not None else 0) \
                   + (1 if normal_default is not None else 0)
    # A DEFAULT THAT DID NOT RESOLVE IS NOT WHAT DECIDES THE STATUS, and this
    # is the half of run 19 that was reported honestly: the asset saved at
    # 10474 bytes with no normal default and the packaged game then loaded it
    # (materialBase read loaded on the vignette verdict), so a missing engine
    # default did not stop the material being made. It is printed, counted
    # and left out of the verdict rather than being quietly promoted into it.
    status = material_status(saved, len(made), len(TEXTURE_PARAMS), wired, asked)
    _write(material_line(status, len(made), len(TEXTURE_PARAMS), wired, asked,
                         existed, colour_from, normal_from,
                         defaults_bound, 2, saved, notes))
    return material_return(status)


def _write(line):
    """The evidence channel is a file, not a log tail. Written beside the
    project so the workflow step can copy it into the build verdict."""
    try:
        import unreal
        root = unreal.Paths.project_dir()
    except Exception:
        root = "."
    path = os.path.join(root, "ue-material.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(line + "\n")
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


if __name__ == "__main__":
    # SYS.EXIT IS FOR A REAL PROCESS ONLY. Inside the editor this file runs on
    # an embedded interpreter that is not exiting anything: raising SystemExit
    # there is a plausible way to turn a script that worked into a process
    # that reports failure, which is one half of the pair run 19 could not
    # explain. The verdict inside the editor travels in the file, as
    # materialScriptReturn, which is the channel this project trusts.
    _code = main()
    if _inside_unreal():
        print("make_base_material: returning %d without sys.exit "
              "(inside the editor; the verdict is materialScriptReturn in "
              "ue-material.txt)" % _code)
    else:
        sys.exit(_code)
