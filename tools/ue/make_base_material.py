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

    _write("materialStatus=%s materialPath=%s materialExistedBefore=%s "
           "materialParams=%s materialParamsMade=%d/%d materialScalars=%s "
           "materialConnections=%d/%d materialColourDefault=%s "
           "materialNormalDefault=%s materialSaved=%s materialNote=%s"
           % ("MADE" if saved and len(made) == len(TEXTURE_PARAMS)
              else ("PARTIAL" if saved else "NOT-SAVED"),
              ASSET_PATH, "yes" if existed else "no",
              "/".join(TEXTURE_PARAMS), len(made), len(TEXTURE_PARAMS),
              "/".join(SCALAR_PARAMS), wired, asked,
              colour_from.replace(" ", "~"), normal_from.replace(" ", "~"),
              "yes" if saved else "NO",
              "/".join(notes) if notes else "none"))
    return 0 if saved else 2


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


if __name__ == "__main__":
    sys.exit(main())
