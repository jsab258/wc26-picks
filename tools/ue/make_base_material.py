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

  3. AND THE SAME WORD MUST NOT BE OVERCLAIMED A SECOND WAY. When no pin
     name is accepted, the head of the UV chain is written straight into the
     input property as a last resort. That reads back connected, so it is a
     connection and materialConnections counts it; what a struct written by
     value does to the compiled SHADER is unproven from here. So 14 of 14
     carrying any such head prints materialStatus=WIRED-BY-PROPERTY-WRITE
     with materialScriptReturn=2 and the count that decided it beside it as
     materialUvHeadByPropertyWrite, and the four frames judge whether the
     material is correct or merely plausible. The word and the return were ruled
     2026-09-03; the printed count was added under
     game-design/decision-2026-09-05-ruling-062-step-2-third-status-word.md.
     MADE is unchanged and still means every head taken by a named pin.

THE STATUS AND THE RETURN CODE ARE COMPUTED BY PURE FUNCTIONS AT THE TOP OF
THIS FILE and exercised by --selftest, which runs in the container that
writes them. Everything that needs Unreal supplies numbers; nothing that
needs Unreal decides what the numbers mean.

WHAT RUN 20 LANDED, AND WHY THE UV HEAD IS NOW SWEPT RATHER THAN NAMED.
Run 20 wired the same 12 of 14 as run 19 and refused the same two, verbatim:
texcoord-to-maskU-refused/texcoord-to-maskV-refused. Those two are the head
of the UV chain all three samplers hang off, so every sampler read one texel
and 563 correctly textured pieces rendered as one flat colour each.

Both refusals name a pin. connect_material_expressions takes the output pin
name and the input pin name as STRINGS and answers false when either names a
pin the expression does not have: no exception, no log line, one false. The
two refused calls are the only two in this script that ask for an input named
Input, and they are also the only two whose source is the TextureCoordinate
expression, so the fault is one of those two names. WHICH ONE IS NOT
ESTABLISHED HERE AND COULD NOT BE: there is no engine, no unreal module and
no engine source in this container, and Epic's Python API reference is not
reachable from it (the agent proxy answers 403 CONNECT for dev.epicgames.com,
recorded in its own status). A guess would cost a 25 minute round trip per
wrong name.

So the name is MEASURED ON THE RUNNER instead of asserted here. Each head
connection is asked for under UV_PIN_CANDIDATES, most likely pair first,
until the editor accepts one, and the pair that answered is printed as
materialUvHeadVia. The sweep contains the exact pair runs 19 and 20 used, so
it cannot wire less than they did; it counts ONE connection however many
names it tries, so the denominator stays 14; and the graph is read back
afterwards, because the editor's boolean is not the only witness worth
having.

WHAT RUN 23 LANDED, AND WHY MADE IS NOW HARDER TO PRINT THAN IT HAS EVER BEEN.
Run 23 printed materialStatus=MADE materialScriptReturn=0 materialConnections=
14/14 over a material NOTHING IN THE SCENE WAS RENDERING. Its control quads
settled it: a 2x2 texture of pure red, green, blue and yellow, built in code
with no file and no decode, rendered chroma mean 3.7 and max 6 over 11,880
pixels, and two quads differing only in a fourfold tiling scalar came back with
an identical 12 px checker period. Every readback was full. An instance that is
perfect while neither its textures nor its scalars reach the pixels means the
engine default material is on screen, and the engine default material ignores
instance parameters entirely.

Two things in this file put it there, and both are fixed above.
  1. THE NORMAL SAMPLER HAD NO TEXTURE. Neither NORMAL_DEFAULTS candidate
     resolved in 5.8 and the code assigned a default only when one did. A
     texture sample expression with a null texture does not compile.
  2. THE ROUGHNESS SAMPLER HAD THE WRONG ONE. It was handed colour_default, an
     sRGB colour texture, into a slot declared LINEAR GRAYSCALE. Unreal derives
     a sampler type from the texture's own compression settings and refuses the
     mismatch, so this was a second compile error, and no key named it:
     materialDefaultsBound counted two defaults for three samplers.

So an engine path is now only the FIRST try and is VALIDATED when it answers,
this script WRITES its own default when validation fails, and the status word
needs a default of the right type on every sampler PLUS a compile verdict of
OK, which itself needs a clean editor log AND a non-zero shader instruction
count. The absence of a raised exception is not evidence and never was.
"""

import os
import sys

# THE CONTRACT. Read by --selftest out of the tested header, never retyped
# there. Order is base colour, normal, roughness, matching MapParam().
TEXTURE_PARAMS = ["BaseColorMap", "NormalMap", "RoughnessMap"]
SCALAR_PARAMS = ["TilingU", "TilingV"]

# THE ONE PAIR OF PIN NAMES THIS SCRIPT CANNOT ESTABLISH FROM HERE.
# Each entry is (output pin name on the TextureCoordinate, input pin name on
# the ComponentMask), ordered most likely first. The ordering is a hypothesis;
# only the run can say which pair is right, and it prints the one that was.
#   1. empty into empty. Every connection that DID wire in runs 19 and 20
#      passed "" as its output name, so "" is known to match an unnamed pin in
#      this engine version, and the mask's single input draws unlabelled.
#   2. empty into Input. Exactly what runs 19 and 20 asked for and were
#      refused. Kept FIRST among the named ones so the sweep can never wire
#      less than they did and so the run says out loud whether that name was
#      the fault.
#   3. the FName None spelled out, for a library comparing ToString() output
#      rather than FName against FName.
#   4. the two words the node's coordinate input is described by elsewhere.
#   5. the same sweep with the OUTPUT named, because the other live hypothesis
#      is that the refusal is on the TextureCoordinate side: these are the
#      only two calls in this script whose source is one.
UV_PIN_CANDIDATES = [
    ("", ""),
    ("", "Input"),
    ("", "None"),
    ("", "Coordinates"),
    ("", "UVs"),
    ("None", ""),
    ("None", "Input"),
    ("UV", ""),
    ("UVs", ""),
]

# The two head connections, in the order main() makes them. Used only to
# label the verdict value when the two masks answer differently.
UV_HEAD_NAMES = ["maskU", "maskV"]

PACKAGE = "/Game/Ledger"
ASSET = "M_LedgerSurface"
ASSET_PATH = PACKAGE + "/" + ASSET

# DEFAULT TEXTURES ARE TRIED IN ORDER AND THE ONE THAT ANSWERED IS NAMED. A
# texture parameter with no default can fail to compile, and an engine asset
# path that moved between versions is exactly the kind of assumption that
# costs a 25 minute round trip to discover.
#
# RUN 23 IS WHY THERE IS A SECOND HALF TO THIS NOW, AND WHY AN ENGINE PATH IS
# ONLY EVER THE FIRST TRY. Both NORMAL_DEFAULTS resolved to nothing in UE 5.8
# (materialNormalDefault=none-of-2-candidates materialDefaultsBound=1/2), so
# the normal sampler carried a NULL texture. A texture sample expression with
# no texture does not compile, a material that does not compile is replaced by
# the engine's own default material at draw time, and that default material
# ignores every parameter a dynamic instance sets. Which is exactly what the
# landed frame showed: full readbacks, a 2x2 red/green/blue/yellow control
# quad rendering neutral grey at chroma max 6 over 11,880 pixels, and a
# fourfold tiling change moving nothing.
# So when an engine path does not resolve, or resolves to a texture whose own
# settings do not match the sampler it is going into, this script MAKES the
# default itself as an asset it owns under /Game/Ledger. No engine version can
# move an asset this script writes.
COLOUR_DEFAULTS = [
    "/Engine/EngineResources/DefaultTexture",
    "/Engine/EngineResources/WhiteSquareTexture",
    "/Engine/EngineMaterials/DefaultDiffuse",
]
# EMPTY BY MEASUREMENT, 2026-09-06, AND THE MEASUREMENT IS COMMITTED. The two
# candidates that used to be here are
# /Engine/EngineMaterials/DefaultNormal and
# /Engine/EngineResources/DefaultTextureNormal. Runs 23 and 24 both asked a
# real UE 5.8 install for them and both times the asset registry answered that
# neither exists; run 24's editor log says so in the engine's own words and
# that log is production/d1-probe/ue-material-log.txt in this repository. The
# probe was not free: each miss is a LogEditorAssetSubsystem Error, the two of
# them are the whole of the editor's "Failure - 2 error(s)" summary, and that
# summary is materialEditorCmdExit=1, which four runs then had to explain.
# A probe whose answer is known and whose cost is the only whole-process
# health signal this step has is not a probe, so the generated default under
# /Game/Ledger owns this sampler outright. Restoring a candidate here needs a
# new measurement, not a memory.
NORMAL_DEFAULTS = []
# THE LIST RUN 23 USED FOR ROUGHNESS WITHOUT ANY KEY SAYING SO. main() passed
# colour_default into the roughness sampler, so an sRGB COLOUR texture sat in
# a slot declared LINEAR GRAYSCALE. Unreal derives a sampler type from the
# texture's own compression settings and refuses the mismatch at compile time,
# so that was a SECOND compile error in the same material, and no key could
# name it: materialDefaultsBound counted TWO defaults for THREE samplers and
# the third was never printed at all. It is a list of its own now, it is
# validated like the other two, and the count's denominator is the number of
# texture parameters rather than a hand-typed 2.
# EMPTY FOR A DIFFERENT MEASURED REASON THAN THE NORMAL LIST. The colour
# candidates DO resolve here: run 24 read
# materialColourDefault=engine../Engine/EngineResources/DefaultTexture..asked.
# COLOR..derives.COLOR. That texture is sRGB, so it derives COLOR, and this
# sampler is declared LINEAR_COLOR, so the type check refuses it EVERY time by
# construction. A candidate that cannot be accepted is a note, not a default.
ROUGHNESS_DEFAULTS = []

# ---- SAMPLER TYPES, WHICH ARE A COMPILE-TIME CONTRACT WITH THE TEXTURE ----
#
# Unreal does not take the sampler type on the expression as given. It derives
# one FROM THE TEXTURE sitting in the expression and errors when the two
# disagree, so "assign a default" is not enough on its own: the default has to
# be a texture whose compression settings and sRGB flag derive the type the
# sampler was declared with. These names are this script's own spelling of
# that rule, kept as strings so the derivation is a pure function --selftest
# can run in a container with no engine in it.
SAMPLER_COLOR = "COLOR"
SAMPLER_LINEAR_COLOR = "LINEAR_COLOR"
SAMPLER_NORMAL = "NORMAL"
SAMPLER_GRAYSCALE = "GRAYSCALE"
SAMPLER_LINEAR_GRAYSCALE = "LINEAR_GRAYSCALE"
SAMPLER_ALPHA = "ALPHA"
SAMPLER_MASKS = "MASKS"
SAMPLER_DISTANCE_FIELD_FONT = "DISTANCEFIELDFONT"

# THE TYPE EACH MAP IS DECLARED WITH, in TEXTURE_PARAMS order.
# ROUGHNESS CHANGED, 2026-09-06, and the reason is not cosmetic. It was
# LINEAR_GRAYSCALE, which needs a TC_Grayscale texture, while both the engine
# default it was handed and the pack texture the runtime binds to it are plain
# BGRA8 with sRGB off. LINEAR_COLOR is the type Unreal derives from exactly
# that texture, so the declared type now matches BOTH the compile-time default
# and the thing the game actually binds, and the R pin still feeds roughness.
MAP_SAMPLER_TYPES = [SAMPLER_COLOR, SAMPLER_NORMAL, SAMPLER_LINEAR_COLOR]

# THE DEFAULT THIS SCRIPT MAKES WHEN NO ENGINE PATH WILL DO, one per texture
# parameter, in TEXTURE_PARAMS order:
#   (asset name, (R,G,B), srgb, compression enum leaf, sampler type it derives)
# Flat normal is (128,128,255), which unpacks to (0,0,1) in tangent space and
# is the only colour that leaves a surface's own geometry alone. Mid grey for
# the other two, so a piece rendering the default is visibly untextured rather
# than invisible.
# FOUR BY FOUR AND NOT ONE BY ONE: a block-compressed format has a 4x4 block,
# and the flat colour makes every texel identical, so nothing here depends on
# the importer's row order or on which corner the origin is in.
GENERATED_SIZE = 4
GENERATED_DEFAULTS = [
    ("T_LedgerDefaultBaseColor", (128, 128, 128), True, "TC_DEFAULT",
     SAMPLER_COLOR),
    ("T_LedgerDefaultNormal", (128, 128, 255), False, "TC_NORMALMAP",
     SAMPLER_NORMAL),
    ("T_LedgerDefaultRough", (128, 128, 128), False, "TC_DEFAULT",
     SAMPLER_LINEAR_COLOR),
]


# EVERY COMPRESSION LEAF THIS FILE KNOWS IS A REAL ONE, compact (no
# underscores, upper case), so TC_DISTANCE_FIELD_FONT and TC_DistanceFieldFont
# are one name here. It exists so that the engine's DEFAULT branch below can
# only be taken for a leaf that is actually a compression setting: an
# unrecognised spelling must derive NOTHING, because deriving a colour type
# from a string this file failed to parse is precisely how run 24 declared a
# normal map sampler LINEAR_COLOR. The editor side does not rely on this list
# at all, it passes the live enum's own leaves; the list is the container's
# fixture and the fallback when the enum cannot be enumerated.
KNOWN_COMPRESSION_LEAVES = frozenset((
    "DEFAULT", "NORMALMAP", "MASKS", "GRAYSCALE", "DISPLACEMENTMAP",
    "VECTORDISPLACEMENTMAP", "HDR", "EDITORICON", "ALPHA",
    "DISTANCEFIELDFONT", "HDRCOMPRESSED", "BC7", "HALFFLOAT",
    "ENCODEDREFLECTIONCAPTURE", "SINGLEFLOAT", "HDRF32", "LQ",
    "REFLECTIONCAPTUREENCODEDHDR",
))


def compression_leaf(spelling):
    """The bare compression leaf inside ANY spelling the editor may answer
    with, compact and upper case, or None when there is no leaf in it.

    THIS IS THE FUNCTION RUN 24 GOT WRONG AND THE ONE NUMBER IT COST IS ON
    THE RECORD. The old code did str(value).split(".")[-1], which is only
    correct if the enum's string form ENDS at the leaf. Run 24 set
    TC_NORMALMAP on the generated normal, the importer had already
    auto-detected a normal map by itself (LogInterchangePipeline says so in
    production/d1-probe/ue-material-log.txt), and the readback still derived
    LINEAR_COLOR. The only route to that answer is a tail that is not a bare
    leaf, "TC_NORMALMAP: 1" or "<TextureCompressionSettings.TC_NORMALMAP: 1>",
    which matches no named branch and fell into the catch-all. All three
    textures in that run took the catch-all and nothing could say so.
    So the leaf is cut out of the spelling rather than assumed to be its tail:
    angle brackets dropped, everything from the first colon dropped, the last
    dot segment taken, TC_ dropped, and non-alphanumerics folded out. A value
    that reduces to nothing or to digits alone is None, which never matches an
    asked sampler type, so it is refused instead of guessed at.
    """
    if spelling is None:
        return None
    text = str(spelling).replace("<", " ").replace(">", " ").strip()
    text = text.split(":")[0]
    text = text.split(".")[-1].strip().upper()
    if text.startswith("TC_"):
        text = text[3:]
    compact = "".join(c for c in text if c.isalnum())
    if not compact or compact.isdigit():
        return None
    return compact


def derived_sampler_type(compression, srgb, known_leaves=None):
    """The sampler type Unreal derives from a TEXTURE, which is the thing it
    compares the expression's declared type against.

    compression is whatever the editor answered for the texture's compression
    settings, in any spelling compression_leaf can find a leaf in, or an int,
    which cannot be interpreted and is treated as unknown.
    srgb is the texture's sRGB flag.
    known_leaves is the set of leaves that ARE compression settings, compact,
    and defaults to this file's own list. The editor side passes the live
    enum's leaves so that this engine version decides, not this file.

    The branch order is the engine's own
    (UMaterialExpressionTextureBase::GetSamplerTypeForTexture), and the two
    cases decided by the sRGB flag rather than by the compression are the two
    this project has already been bitten by. What changed on 2026-09-06 is the
    LAST branch: the engine's default case is only reachable for a leaf known
    to be a compression setting, so a spelling this file cannot read derives
    nothing rather than a plausible colour type.
    """
    leaf = compression_leaf(compression)
    if leaf is None:
        return None
    if leaf == "NORMALMAP":
        return SAMPLER_NORMAL
    if leaf == "GRAYSCALE":
        return SAMPLER_GRAYSCALE if srgb else SAMPLER_LINEAR_GRAYSCALE
    if leaf == "ALPHA":
        return SAMPLER_ALPHA
    if leaf == "MASKS":
        return SAMPLER_MASKS
    if leaf == "DISTANCEFIELDFONT":
        return SAMPLER_DISTANCE_FIELD_FONT
    known = KNOWN_COMPRESSION_LEAVES if known_leaves is None else known_leaves
    if leaf not in known:
        return None
    return SAMPLER_COLOR if srgb else SAMPLER_LINEAR_COLOR


def default_via(source, path, derived, asked):
    """One sampler's default, as a value with no spaces and one equals.

    source is engine, generated, or none. The derived type is printed beside
    the asked one because those two agreeing is the whole reason the default
    is acceptable, and a reader who sees only a path cannot tell.
    """
    return "%s..%s..asked.%s..derives.%s" % (
        source,
        str(path).replace(" ", "~"),
        asked or "none",
        derived or "unknown")


def defaults_field(vias):
    """Every sampler's default on one value, in TEXTURE_PARAMS order, and the
    count that goes with it.

    vias is one (param name, source, derived, asked) per texture parameter.
    Returns (count bound, count asked, field). A default counts as BOUND only
    when a texture was found AND the type it derives is the type the sampler
    was declared with, because a texture of the wrong type is a compile error
    and not a default. Nothing recorded prints the words nothing measured, so
    a zero here cannot be read as "three samplers, none bound".

    THREE WORDS AND NOT TWO, amendment A2 of the ruling of 2026-09-06. A
    texture is present and derives a type that DISAGREES with the slot
    (TYPE-MISMATCH, and the next action is the texture) and a texture that
    derived NO TYPE AT ALL (TYPE-UNKNOWN, and the next action is the reading:
    materialCompressionReadback on the same line says what it answered) are
    different facts, and one label for both is how a reading this file could
    not parse and a texture of the wrong type printed the same word. Neither
    counts as bound: a type nobody derived is not a type that matched.
    """
    asked = len(TEXTURE_PARAMS)
    if not vias:
        return 0, asked, "nothing-measured"
    bound = len([v for v in vias
                 if v[1] != "none" and v[2] is not None and v[2] == v[3]])
    return bound, asked, "/".join(
        "%s.%s.%s" % (v[0], v[1],
                      "no-default" if v[1] == "none"
                      else ("TYPE-UNKNOWN" if v[2] is None
                            else ("type-ok" if v[2] == v[3]
                                  else "TYPE-MISMATCH")))
        for v in vias)


def compression_word(leaf, via):
    """One texture's compression leaf as it goes on the line, and the reason
    it is three words rather than two.

    A leaf that was read is printed as itself. A leaf of None used to print
    UNRECOGNISED whatever produced it, which put two different situations
    under one label: a value the engine ANSWERED that this file could find no
    compression leaf in (UNRECOGNISED, and the next action is the spelling,
    with the str and repr of it in the committed report file), and a property
    that never answered at all or a texture that was never there (none, and
    the next action is the texture, not the parser). Amendment A2 of the
    ruling of 2026-09-06.
    """
    if leaf:
        return str(leaf)
    if via in ("nothing-measured", "readback-refused"):
        return "none"
    return "UNRECOGNISED"


def compression_field(readings):
    """What each sampler's texture ANSWERED for its compression settings, and
    HOW that answer was read.

    readings is one (param name, leaf, via, srgb) per texture parameter, with
    leaf None when nothing recognisable came back. This key exists because run
    24 could print that a texture derived LINEAR_COLOR and could not print
    WHAT IT READ to derive that from, so a broken reading and a broken texture
    were the same line. The via is the half that names which is which:
      enum-identity  the value IS one of this engine's own enum members, which
                     is the only reading that depends on nothing this file
                     guessed about spelling.
      enum-int       matched by integer value, the names differing.
      string-parse   read out of the value's text, which is the route that
                     failed on run 24 and is now the LAST one tried.
      unrecognised   nothing in the value is a compression leaf of this
                     engine. Refused, never guessed at.
      readback-refused / nothing-measured  the property or the run never
                     answered at all, which is not a texture of the wrong
                     type.

    AND THE LEAF SAYS WHICH OF THOSE TWO IT IS, amendment A2 of the ruling of
    2026-09-06: see compression_word.
    """
    if not readings:
        return ("materialCompressionReadback=nothing-measured "
                "materialCompressionStat=per-texture-parameter/the-compression-leaf-read-back-and-the-route-that-read-it")
    return ("materialCompressionReadback=%s "
            "materialCompressionStat=per-texture-parameter/the-compression-leaf-read-back-and-the-route-that-read-it"
            % "/".join(
                "%s.%s.via.%s.srgb.%s"
                % (r[0], compression_word(r[1], r[2]), r[2],
                   "yes" if r[3] else "no")
                for r in readings))


def generated_field(sources, attempted):
    """How many samplers ended up on a default this script made, over how
    many it had to try to make one for.

    Both halves matter and they are different facts: an engine path that
    resolved and validated needs no generated asset at all, so 0/0 is a run
    where every engine default was good, and 2/2 is a run where two of them
    were not and the fallback covered both. 1/2 is the fallback itself
    failing, which is the case that must never look like a pass.
    """
    made = len([s for s in sources if s == "generated"])
    return ("materialGeneratedDefaults=%d/%d "
            "materialGeneratedFrom=%dx%d-uncompressed-32bit-tga-written-by-this-script "
            "materialGeneratedStat=samplers-on-a-generated-default/over-samplers-a-default-was-generated-for"
            % (made, attempted, GENERATED_SIZE, GENERATED_SIZE))


# ---- THE TINY TEXTURE THIS SCRIPT WRITES ITSELF -------------------------
#
# WHY A FILE AND NOT AN API CALL. Python can set every property of a
# UTexture2D that matters here, but it cannot fill one with texels: the source
# art lives behind UTexture::Source, which is not exposed. The importer is
# exposed, and it is the path the engine itself is built on. So the texels are
# written to a file and imported, and the file format is the simplest one the
# engine reads: an UNCOMPRESSED 32-bit TGA, eighteen bytes of header and then
# BGRA per pixel, no compression, no palette, no chunk CRCs. Every byte of it
# is decided by the function below and read back by --selftest, in the
# container, before any dispatch.

def tga_bytes(width, height, rgb):
    """An uncompressed 32-bit TGA of one flat colour, as bytes.

    Header layout, all little endian: id length, colour map type, image type
    2 for uncompressed true colour, five bytes of colour map spec, origin x,
    origin y, width, height, bits per pixel, image descriptor. The descriptor
    is 0x28: eight alpha bits in the low nibble and bit five set for a
    top-left origin. Pixels are BGRA, which is TGA's own channel order.
    """
    r, g, b = (int(c) & 0xFF for c in rgb)
    header = bytearray([0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    header += bytes([width & 0xFF, (width >> 8) & 0xFF,
                     height & 0xFF, (height >> 8) & 0xFF, 32, 0x28])
    return bytes(header) + bytes([b, g, r, 255]) * (width * height)


def tga_read(data):
    """Read back what tga_bytes wrote, so the writer is never shipped unrun.

    Returns (width, height, bits, descriptor, [(R,G,B,A) per texel]) or None
    when the bytes are not the uncompressed true-colour TGA this writes.
    """
    if data is None or len(data) < 18:
        return None
    if data[1] != 0 or data[2] != 2:
        return None
    width = data[12] | (data[13] << 8)
    height = data[14] | (data[15] << 8)
    bits = data[16]
    desc = data[17]
    if bits != 32 or len(data) != 18 + width * height * 4:
        return None
    texels = []
    for i in range(width * height):
        at = 18 + i * 4
        texels.append((data[at + 2], data[at + 1], data[at], data[at + 3]))
    return width, height, bits, desc, texels


# ---- the verdict, decided by pure functions the container can run --------
#
# EVERY NUMBER BELOW COMES FROM THE EDITOR AND EVERY JUDGEMENT ABOUT IT
# HAPPENS HERE, for the standing reason: a formatter or a status rule written
# where the tests cannot reach it ships unrun, and an unrun rule printing a
# plausible word is the silent-instrument failure this project keeps paying
# for. --selftest exercises all three of these before any dispatch.

STATUS_MADE = "MADE"
STATUS_BY_PROPERTY_WRITE = "WIRED-BY-PROPERTY-WRITE"
STATUS_PARTIAL = "PARTIAL"
STATUS_NOT_SAVED = "NOT-SAVED"
# THE TWO WORDS RUN 23 SHOULD HAVE PRINTED AND COULD NOT.
# NOT-COMPILED is a material the editor reported a compile diagnostic for OR
# one with no shader map readable for it at read time, BESIDE A TWIN
# RECOMPILED THE SAME WAY IN THE SAME PROCESS THAT HAD ONE. Those are two
# different findings and are told apart by materialCompile on the same line
# (ERRORS against NO-SHADER). It stays one status word because the next
# action after either is the same: this material does not render and the
# material step is where to look. What it must never be is COMPILE-UNPROVEN,
# which says nobody could tell.
# COMPILE-UNPROVEN is the state this script was in for its whole life: it
# asked for a recompile, caught the exception that never came, saved the
# asset and said MADE, with nothing anywhere in the run able to say whether a
# shader existed. An absent exception is not evidence. Both return 2.
STATUS_NOT_COMPILED = "NOT-COMPILED"
STATUS_COMPILE_UNPROVEN = "COMPILE-UNPROVEN"

# ---- THE COMPILE VERDICT, WHICH IS THE HALF MADE NEVER HAD ---------------
#
# The requirement, written down before the code: NO COMPILATION ERRORS PLUS
# POSITIVE EVIDENCE OF A VALID RENDERED RESULT. Two channels, and both are
# required, because they fail differently. The negative channel is the
# editor's own log between two markers this script writes around the
# recompile; the positive one is the shader statistics the editor answers for
# the material afterwards, where a pixel shader instruction count above zero
# cannot be produced by a material that has no shader.
# Either channel silent means UNPROVEN and never OK: a run that could not read
# the log has not shown there were no errors, and a run with no statistics has
# not shown there is a shader.
# AND THE NEGATIVE CHANNEL HAS TO HAVE COUNTED SOMETHING. Zero diagnostics
# over zero log lines examined is nothing measured, not a clean compile, and
# a slice neither marker located is not known to be this material's compile
# at all. Both are UNPROVEN for OK and NEITHER suppresses ERRORS: a log that
# failed to slice can still carry a real diagnostic, which is exactly the run
# worth hearing about. Amendment A1, ruling of 2026-09-06.
COMPILE_OK = "OK"
COMPILE_ERRORS = "ERRORS"
COMPILE_UNPROVEN = "UNPROVEN"
# THE FOURTH WORD, ADDED AFTER RUN 24, WHICH READ
# materialCompileInstructions=pixel.0..vertex.0 and folded it into UNPROVEN.
# "This material has no shader" and "we could not tell whether it has one" are
# different facts with different next actions, and one word for both throws
# away the strongest reading this step has ever taken.
# NO-SHADER IS ONLY REACHABLE WITH AN ACCEPTING CASE FOR THE CHANNEL, AND THE
# ACCEPTING CASE HAS TO BE THE SAME SENTENCE. A zero from an instrument never
# known to print anything else is not a measurement of absence, it is an
# instrument with no denominator. But an ENGINE material answering 187 proves
# only that get_statistics returns a number WHEN A SHADER MAP IS ALREADY
# PRESENT: that material's map comes out of the derived-data cache and was not
# compiled in this process. Ours is recompiled 0.67 seconds before the read
# with no engine tick in between, so if this commandlet compiles material
# shaders asynchronously, our map is not there at read time whether the graph
# is good or not, and pixel.0 beside an engine control of 187 would print
# NO-SHADER over a graph the cook then compiles perfectly well.
# SO THE GATING CONTROL IS A TWIN: a second material THIS SCRIPT makes, wires
# trivially, recompiles by the same call and reads through the same call in
# the same process, outside the compile markers, never saved and deleted
# after. Twin above zero beside our zero means the channel answers for a
# material compiled here and ours genuinely has no shader. Twin zero or absent
# means the channel cannot answer here, the word is UNPROVEN, and the fault is
# in the channel, which is a different day's work from a fault in the
# material. Amendment A1, ruling of 2026-09-06 on run 24's landing.
COMPILE_NO_SHADER = "NO-SHADER"

# THE TWIN. A build product of this run that lives for three calls and is
# never saved, so no cook can see it and no .uasset can carry it.
CONTROL_TWIN = "M_LedgerControlTwin"
CONTROL_TWIN_PATH = PACKAGE + "/" + CONTROL_TWIN

# The one wire the twin gets, most ordinary spelling first. A constant vector
# into base colour is the smallest graph that is unambiguously a material, and
# the class name is swept rather than asserted for the same reason the UV head
# is: this container has no unreal module to ask.
TWIN_EXPRESSION_CLASSES = [
    "MaterialExpressionConstant3Vector",
    "MaterialExpressionConstant4Vector",
    "MaterialExpressionVectorParameter",
    "MaterialExpressionConstant",
]

# The ENGINE materials the non-gating channel reading is tried against, in
# order. ALL of them are asked and the first NON-ZERO is kept, because a first
# candidate answering zero used to end the search and print a dead channel
# over a live one. BasicShapeMaterial leads because the 593 street pieces are
# engine basic shapes and it is the material actually beside ours in the cook,
# so a reading from it is also evidence about the frames. This reading GATES
# NOTHING: it says whether get_statistics returns a number for anything in
# this editor, which is worth knowing and is not the same question as whether
# it can answer for a material compiled moments ago.
CONTROL_MATERIALS = [
    "/Engine/BasicShapes/BasicShapeMaterial",
    "/Engine/EngineMaterials/WorldGridMaterial",
    "/Engine/EngineMaterials/DefaultMaterial",
    "/Engine/EngineDebugMaterials/WireframeMaterial",
]

# The two lines this script logs around the recompile so the log slice it
# reads back is the material's own compile and not the whole editor session.
COMPILE_MARK_BEGIN = "LEDGER-MATERIAL-COMPILE-BEGIN"
COMPILE_MARK_END = "LEDGER-MATERIAL-COMPILE-END"

# How many matched diagnostic lines the committed file keeps. The cap
# announces itself in the file, per the standing rule, because a head -N that
# outgrew its input once read here as three of five systems failing.
COMPILE_LOG_KEEP = 60


def is_compile_diagnostic(line):
    """Whether one editor log line says a material failed to compile.

    Deliberately NOT a search for the word Error. Unreal logs a failed
    material compile at WARNING severity, in lines shaped like
    "LogMaterial: Warning: [AssetLog] ...: Failed to compile Material ... for
    platform PCD3D_SM6, Default Material will be used in game." and
    "(Node TextureSampleParameter2D) TextureSampleParameter2D> Missing input
    texture", so a severity filter alone would have called run 23 clean.
    The named phrases come first and stand on their own; the category plus
    severity pair is the net underneath them.
    This script's own marker and verdict lines never count, whatever they say,
    because they carry the asset path and would otherwise match the net.
    """
    if line is None:
        return False
    if "LEDGER" in line:
        return False
    low = line.lower()
    for phrase in ("failed to compile",
                   "default material will be used",
                   "missing input texture",
                   "sampler type is",
                   "should be color",
                   "shader compile error",
                   "failed to compile material"):
        if phrase in low:
            return True
    category = ("logmaterial" in low or "logshadercompilers" in low
                or "logshaders" in low)
    severity = ("error" in low or "warning" in low)
    return category and severity


def log_slice(lines, begin=COMPILE_MARK_BEGIN, end=COMPILE_MARK_END):
    """The log between the two markers, and whether both were found.

    Returns (slice, found_begin, found_end). A missing begin marker returns
    the WHOLE log rather than nothing, because a run that logged its
    diagnostics before the marker landed is still worth counting and the
    caller prints which markers were seen. A missing end marker runs to the
    end of the log, which is where an editor that died mid-compile would be.
    """
    if lines is None:
        return [], False, False
    at_begin = None
    at_end = None
    for i, line in enumerate(lines):
        if at_begin is None and begin in line:
            at_begin = i
        elif at_begin is not None and at_end is None and end in line:
            at_end = i
    lo = 0 if at_begin is None else at_begin + 1
    hi = len(lines) if at_end is None else at_end
    return lines[lo:hi], at_begin is not None, at_end is not None


def compile_scan(lines):
    """Count the compile diagnostics in a log slice, with its denominator.

    Returns (errors, examined, matched lines). lines being None means no log
    could be read at all, which is NOT zero errors: it returns (None, 0, []),
    and the caller prints nothing-measured for both halves.
    """
    if lines is None:
        return None, 0, []
    matched = [l for l in lines if is_compile_diagnostic(l)]
    return len(matched), len(lines), matched


def compile_verdict(errors, examined, instructions, found_begin, found_end,
                    control_instructions=None):
    """One word for whether the material compiled.

    errors is the diagnostic count, or None when no log was read.
    examined is how many log lines that count was taken over, which is its
    denominator: an EMPTY slice makes compile_scan return (0, 0, []), and a
    zero with no denominator cannot tell a clean compile from a run that
    read nothing.
    instructions is the pixel shader instruction count the editor answered
    with, or None when the statistics API would not answer.
    found_begin and found_end say whether this script's own markers located
    the slice. log_slice falls back to the WHOLE log when the begin marker
    is missing, which is right for counting diagnostics and wrong for a
    pass: a slice carrying neither marker has not been shown to be this
    material's compile.

    control_instructions is the SAME statistics call made against the TWIN,
    a material this script made, wired, recompiled and read in this same
    process, or None when no twin could be made or read. It is the accepting
    case for the positive channel and it decides only one thing: whether a
    zero of our own is allowed to mean NO-SHADER. It is a twin and not an
    engine material because an engine material answers out of the derived-data
    cache: a number from one proves the call works when a shader map is
    already there, which is a different sentence from the one our zero needs.

    Any diagnostic at all is ERRORS, markers or no markers, because a log
    that failed to slice can still carry a real one and that is exactly when
    it must be heard. Then a zero instruction count beside a control ABOVE
    zero is NO-SHADER: the channel demonstrably answers for a material
    compiled in this process, and it answered that this material has no
    compiled shader. A zero with a silent or zero control is UNPROVEN,
    because an instrument that has never printed anything but zero has not
    been shown to be able to, and a twin that could not be made at all is
    the same silence: UNPROVEN, never NO-SHADER. After that EVERY
    channel has to have spoken: a log read, zero errors in it, a non-zero
    number of lines they were counted over, both markers seen, and a non-zero
    instruction count. Anything else is UNPROVEN. That is the rule this file
    was missing, stated as a function so a future edit to it shows up in a
    diff rather than in a frame.
    """
    if errors is not None and errors > 0:
        return COMPILE_ERRORS
    if instructions is None:
        return COMPILE_UNPROVEN
    if instructions <= 0:
        if control_instructions is not None and control_instructions > 0:
            return COMPILE_NO_SHADER
        return COMPILE_UNPROVEN
    if errors is None:
        return COMPILE_UNPROVEN
    if examined is None or examined <= 0:
        return COMPILE_UNPROVEN
    if not (found_begin and found_end):
        return COMPILE_UNPROVEN
    return COMPILE_OK


def compile_fields(verdict, errors, examined, instructions, vs_instructions,
                   samplers, found_begin, found_end,
                   control_instructions=None, control_vs=None,
                   control_from=None,
                   channel_instructions=None, channel_vs=None,
                   channel_from=None, channel_answered=None,
                   channel_tried=None):
    """The compile evidence, as key=value tokens with no spaces in any value.

    verdict is the word compile_verdict already returned, passed in rather
    than recomputed here: the status line and this line have to carry the
    SAME word, and a number computed twice from one set of inputs is a
    number that can drift.

    materialCompile               OK, ERRORS, NO-SHADER or UNPROVEN, from
                                  compile_verdict
    materialCompileErrors         matched diagnostic lines over LOG LINES
                                  EXAMINED in the slice, which is the
                                  denominator that tells a clean compile from
                                  a log nobody read. nothing-measured when no
                                  log was read at all.
    materialCompileMarkers        whether the begin and end markers were seen,
                                  so a slice that silently ran to the whole
                                  log says so.
    materialCompileInstructions   pixel and vertex shader instruction counts
                                  the editor answered for this material.
                                  Above zero is the positive evidence; the API
                                  refusing to answer prints not-available and
                                  is not a zero.
    materialCompileSamplers       texture samplers the compiled material uses.
                                  Three is what this graph asks for.
    materialCompileControl        THE SAME CALL ON THE TWIN, a material this
                                  script made, wired, recompiled and read in
                                  this same process and then deleted, and the
                                  reason a zero of ours can be read at all.
                                  Above zero means the channel answers for a
                                  material compiled here; zero or
                                  not-available means it does not and our own
                                  zero measures nothing. from. names the twin
                                  or the step that refused to make it, because
                                  a twin that could not be made is UNPROVEN
                                  and never NO-SHADER.
    materialCompileChannel        THE SAME CALL ON ENGINE MATERIALS, which
                                  GATES NOTHING. All the candidates are asked,
                                  the first NON-ZERO is kept, and answered.A/T
                                  is how many returned a number over how many
                                  were asked. Above zero says get_statistics
                                  works in this editor for a material whose
                                  shader map the derived-data cache already
                                  holds, which is worth knowing and is not
                                  evidence about ours.
    """
    if errors is None:
        errs = "nothing-measured"
    else:
        errs = "%d/%d" % (errors, examined)
    def num(v):
        return "not-available" if v is None else str(int(v))
    # THE CHANNEL'S DENOMINATOR, and it prints the words nothing measured
    # rather than a bare fraction when the reading was never taken, because a
    # zero with no denominator cannot tell a dead channel from an unasked one.
    if channel_tried is None:
        answered = "nothing-measured"
    else:
        answered = "%d/%d" % (int(channel_answered or 0), int(channel_tried))
    return ("materialCompile=%s materialCompileErrors=%s "
            "materialCompileMarkers=begin.%s/end.%s "
            "materialCompileInstructions=pixel.%s..vertex.%s "
            "materialCompileSamplers=%s "
            "materialCompileControl=pixel.%s..vertex.%s..from.%s "
            "materialCompileChannel=pixel.%s..vertex.%s..from.%s..answered.%s "
            "materialCompileErrorsStat=matched-lines/over-log-lines-examined-between-the-markers "
            "materialCompileControlIs=a-TWIN-material-this-script-made-and-recompiled-in-this-process-and-read-through-the-same-call/nonzero-is-the-accepting-case-that-lets-our-own-zero-mean-anything/materialCompileChannel-beside-it-is-engine-materials-out-of-the-derived-data-cache-and-gates-nothing/answered-is-engine-materials-that-returned-a-number-over-engine-materials-asked "
            "materialCompileRule=OK-needs-a-log-read-AND-zero-errors-AND-lines-examined-above-zero-AND-both-markers-AND-a-nonzero-instruction-count/any-diagnostic-is-ERRORS-with-or-without-markers/a-zero-instruction-count-beside-a-nonzero-control-is-NO-SHADER/anything-else-is-UNPROVEN"
            % (verdict, errs,
               "yes" if found_begin else "NO", "yes" if found_end else "NO",
               num(instructions), num(vs_instructions), num(samplers),
               num(control_instructions), num(control_vs),
               str(control_from or "nothing-measured").replace(" ", "~"),
               num(channel_instructions), num(channel_vs),
               str(channel_from or "nothing-measured").replace(" ", "~"),
               answered))


def compile_log_text(asset_path, errors, examined, matched,
                     keep=COMPILE_LOG_KEEP):
    """The committed diagnostics file, which is free text and not key=value.

    Line 1 carries the count and its denominator so the file can be read on
    its own, and the cap announces itself when it bites.
    """
    out = []
    if errors is None:
        out.append("# LEDGER material compile diagnostics for %s: "
                   "NOTHING MEASURED, no editor log could be read" % asset_path)
        return "\n".join(out) + "\n"
    out.append("# LEDGER material compile diagnostics for %s: %d matched line(s) "
               "of %d log line(s) examined between the compile markers"
               % (asset_path, errors, examined))
    if not matched:
        out.append("# no line in that slice says a material failed to compile")
    for line in matched[:keep]:
        out.append(line.rstrip())
    if len(matched) > keep:
        out.append("(+%d more matching line(s) not shown)"
                   % (len(matched) - keep))
    return "\n".join(out) + "\n"

# THE SUFFIX THAT MEANS A HEAD EXISTS ONLY BECAUSE THE LAST RESORT TOOK.
# property_write_via writes it and property_write_heads reads it, both here,
# so the producer and the counter cannot drift apart: a spelling changed in
# main() would otherwise make the count read zero in silence and print MADE
# over a head no named pin ever accepted, which is the overclaim this whole
# rule exists to stop.
PROP_WRITE_TOOK = "property-write-took"


def property_write_via(candidates_total, wrote):
    """The via token for a head that no candidate pin name would take.

    wrote is what _write_input_property answered: True the write took AND
    read back connected, None the input property is not exposed at all, False
    the write was refused or could not be confirmed. Only the first is a
    connection, so only the first ends in the token above.
    """
    return "none-of-%d-candidates..then.property-write-%s" % (
        candidates_total,
        "took" if wrote is True else
        ("unavailable" if wrote is None else "refused"))


def property_write_heads(results):
    """How many UV heads exist only because the last-resort property write
    took, out of how many heads were recorded.

    results is the uv_head record list, one (ok, via, tried, readback) per
    head connection in the order main() makes them. A head counts only when
    it landed AND its via ends in PROP_WRITE_TOOK: a property write that was
    unavailable or refused made nothing, and a head a named pin accepted is
    not this route.

    Returns (count, recorded, field). field is the verdict value, N/M, or the
    words nothing measured when no head was recorded at all, because a bare
    zero here cannot tell "both heads went through a named pin" from "the
    heads never ran" and the status word turns on exactly that difference.
    """
    count = len([r for r in results
                 if r[0] and str(r[1]).endswith(PROP_WRITE_TOOK)])
    recorded = len(results)
    if not recorded:
        return 0, 0, "nothing-measured"
    return count, recorded, "%d/%d" % (count, recorded)


def material_status(saved, params_made, params_asked, wired, asked,
                    prop_write_heads, defaults_bound, defaults_asked,
                    compile_word):
    """One word for what this run of the script achieved.

    THREE CLAUSES WERE ADDED 2026-09-06 AND NONE WAS RELAXED. MADE was printed
    over a material that never rendered a pixel, so every route into that word
    got narrower and none got wider: on top of everything below, MADE now also
    needs a default texture on EVERY sampler whose derived type matches the
    type the sampler was declared with, and a compile verdict of OK, which
    itself needs a clean log READ OVER A NON-ZERO NUMBER OF LINES WITH BOTH
    MARKERS SEEN, and a non-zero instruction count. A run with the exact
    inputs that printed MADE on 6 September prints COMPILE-UNPROVEN today.

    MADE needs all four of: the asset saved to disk, every texture parameter
    the C++ contract names, every connection the script asked the editor to
    make, and no head standing on the last-resort property write. The third
    clause came from run 19, which wired 12 of 14 and still said MADE: the
    two that refused were TexCoord into the component masks, the head of the
    UV chain that all three samplers hang off, so every sampler in that
    material reads one texel. A material whose UV chain is unconnected has
    not been made.

    WIRED-BY-PROPERTY-WRITE is 14 of 14 where at least one head was made by
    writing the input struct rather than by a named pin, which is
    prop_write_heads above zero, counted by property_write_heads. The graph
    reads back connected, so the connection is real and the COUNT is right to
    include it, but what a struct written by value does to the compiled
    SHADER is unproven here and only the still can judge it. MADE overclaimed
    once and was repaired by requiring the count; a second route into the same
    word on unproven shader effect would be the same fault in the same word,
    so the third state gets a word of its own and the same return code as
    every other non-pass. Ruled 2026-09-03, game-design/decision-2026-09-03-
    batch-review-register-banner-spawnlog-uvsweep.md.

    PARTIAL is a saved asset that fell short of one of those, which is worth
    keeping and is not a pass. NOT-SAVED is nothing on disk at all. The
    property-write clause is LAST on purpose: a run still short of 14 of 14
    stays PARTIAL rather than being renamed by the thing that rescued one
    head of it.
    """
    if not saved:
        return STATUS_NOT_SAVED
    if params_made < params_asked:
        return STATUS_PARTIAL
    if asked <= 0 or wired < asked:
        return STATUS_PARTIAL
    # THE DEFAULT CLAUSE, AND IT SITS WITH THE OTHER PARTIAL CLAUSES ON
    # PURPOSE. A sampler with no default, or with a default of the wrong type,
    # is a graph that is not finished being wired, which is the same class of
    # fault as a connection that refused. defaults_asked of zero is a run that
    # recorded nothing, and nothing measured is not a pass.
    if defaults_asked <= 0 or defaults_bound < defaults_asked:
        return STATUS_PARTIAL
    if compile_word in (COMPILE_ERRORS, COMPILE_NO_SHADER):
        return STATUS_NOT_COMPILED
    if compile_word != COMPILE_OK:
        return STATUS_COMPILE_UNPROVEN
    if prop_write_heads > 0:
        return STATUS_BY_PROPERTY_WRITE
    return STATUS_MADE


def material_return(status):
    """The script's own return code, a FUNCTION of the status and never a
    second opinion about it. Two numbers derived from one variable are one
    number twice, and that is the point here: the pair that made run 19
    unreadable cannot be printed again.

    MADE is the only zero, so WIRED-BY-PROPERTY-WRITE returns 2 like every
    other word that is not a pass. That is safe rather than costly: run 20's
    ue-build.txt shows the workflow cooking and capturing after a return of 2,
    so the four frames that are the only thing able to judge the third state
    arrive either way."""
    return 0 if status == STATUS_MADE else 2


class Wiring(object):
    """The connection tally, kept in the half of this file the container can
    run because a count that decides a verdict must not ship unrun.

    asked counts CONNECTIONS ASKED FOR and never candidate pin names: a head
    connection swept over nine candidate names is one connection, so the
    denominator stays 14 whatever the sweep costs. wired counts the ones the
    editor accepted. materialStatus reads MADE only when the two are equal
    AND no head stood on the last-resort property write, which is the
    3 September rule and its amendment, and neither is relaxed here.
    """

    def __init__(self):
        self.wired = 0
        self.asked = 0
        self.notes = []

    def record(self, ok, note):
        """One connection, counted once. note is the token appended when it
        did not land; nothing is appended when it did, because the notes field
        is a list of faults and a note per success would bury them."""
        self.asked += 1
        if ok:
            self.wired += 1
        elif note:
            self.notes.append(note)
        return ok


def pin_token(out_name, in_name):
    """One candidate pair, as a value with no spaces and no second equals.
    The word empty stands for the empty string, which is a real pin name in
    this API and would otherwise print as nothing at all and read as a bug."""
    return "out.%s..in.%s" % (out_name or "empty", in_name or "empty")


def connect_by_candidates(try_connect, candidates):
    """Ask the editor for one connection under each candidate pair of pin
    names until a pair answers, and report WHICH pair did.

    try_connect(out_name, in_name) -> bool is the editor's opinion and the
    only part of this that needs Unreal. The search, the count and the token
    are decided here, where --selftest can run them, and a candidate that
    RAISES is a candidate that did not answer rather than the end of the
    sweep: an API that rejects an unknown pin name by throwing would
    otherwise abandon the eight names after it.

    Returns (ok, tried, out_name, in_name). tried is how many pairs were asked
    for, so it is 1 when the first pair answered and len(candidates) when none
    did, and the names are None when none did.
    """
    tried = 0
    for out_name, in_name in candidates:
        tried += 1
        try:
            ok = bool(try_connect(out_name, in_name))
        except Exception:
            ok = False
        if ok:
            return True, tried, out_name, in_name
    return False, tried, None, None


def uv_head_note(what, candidates_total):
    """The token appended when a head connection did not land.

    It keeps the exact string runs 19 and 20 printed as a PREFIX, so a grep
    for texcoord-to-maskU-refused across the verdict files still finds the
    next failure, and adds what the new attempt cost. Formatted here rather
    than in main() because a string built where the tests cannot reach it
    ships unrun.
    """
    return "%s-refused-after-%d-candidates" % (what, candidates_total)


def uv_head_fields(results, candidates_total):
    """The three values the UV head ships on the verdict line.

    results is one record per head connection, in the order main() makes them:

        (ok, via, tried, readback)

    via is the token for HOW it was made, tried is how many candidate pairs
    were asked for, and readback is True, False or None for the graph read
    back afterwards, where None means the editor would not answer and is not
    the same fact as no.

    Returns (via, triedAtWorst, readback), all three free of spaces. The
    second is a max and says so in its key. A run holding no records prints
    the words nothing measured rather than a clean-looking zero.
    """
    if not results:
        return ("nothing-measured",
                "nothing-measured/%d" % candidates_total,
                "nothing-measured")
    vias = [r[1] for r in results]
    if len(set(vias)) == 1:
        via = ("both.%s" % vias[0]) if len(results) > 1 else vias[0]
    else:
        named = []
        for i, v in enumerate(vias):
            head = UV_HEAD_NAMES[i] if i < len(UV_HEAD_NAMES) else "head%d" % i
            named.append("%s.%s" % (head, v))
        via = "/".join(named)
    tried = max(r[2] for r in results)
    yes = len([r for r in results if r[3] is True])
    unreadable = len([r for r in results if r[3] is None])
    return (via,
            "%d/%d" % (tried, candidates_total),
            "%d/%d..unreadable%d" % (yes, len(results), unreadable))


def material_line(status, params_made, params_asked, wired, asked, existed,
                  colour_from, normal_from, roughness_from,
                  defaults_bound, defaults_asked, defaults_detail,
                  compile_block, generated_block,
                  saved, notes, uv_via, uv_tried, uv_readback, uv_by_prop,
                  compression_block=None):
    """The one line the workflow copies into the build verdict.

    No spaces inside any value: every reader of these files splits on
    whitespace. Every count ships its denominator, including the engine
    default textures, which run 19 reported as `none-of-2-candidates` with no
    total beside it.

    Three of the four UV head values are readings that nothing branches on.
    The fourth is the one number the status word turns on, so it is printed
    beside the word it decided rather than left to be inferred from the via:
      materialUvHeadVia          which pair of pin names the editor accepted,
                                 or none-of-N-candidates, for both masks or
                                 named per mask when the two differ.
      materialUvHeadTriedAtWorst candidate pairs asked for, AT WORST of the
                                 two head connections, over the number
                                 available. 1/9 means the first pair answered.
      materialUvHeadReadback     head connections whose input reads back as
                                 the TexCoord node, over the head connections
                                 made, with the count the editor would not
                                 answer for carried beside it rather than
                                 folded into the no.
      materialUvHeadByPropertyWrite
                                 head connections that exist only because the
                                 last-resort property write took, over the
                                 head connections recorded. Above zero at
                                 14 of 14 is what makes the status
                                 WIRED-BY-PROPERTY-WRITE instead of MADE, and
                                 0/2 is the reading that leaves MADE standing.
                                 nothing-measured when no head ran at all.

    THE DEFAULTS, WHICH RUN 23 PRINTED AS 1/2 FOR THREE SAMPLERS.
      materialColourDefault / materialNormalDefault / materialRoughnessDefault
                                 one per texture parameter, each naming where
                                 the default came from (engine or generated),
                                 the path, the type the sampler asked for and
                                 the type that texture derives. The third of
                                 those keys did not exist before 6 September
                                 and the sampler it names was being handed an
                                 sRGB colour texture in a linear slot.
      materialDefaultsBound      samplers with a default whose derived type
                                 matches the declared one, over the number of
                                 TEXTURE PARAMETERS. The denominator is 3 and
                                 not the hand-typed 2 that counted colour and
                                 normal and forgot roughness entirely.
      materialDefaultsDetail     the same three, named, so a short count says
                                 WHICH sampler is short and whether it was
                                 missing or mismatched.
      materialCompressionReadback
                                 compression_field() in full: what each
                                 texture ANSWERED and which route read it.
                                 The derived type alone cannot tell a texture
                                 of the wrong type from a reading of the
                                 wrong type, and run 24 lost a round trip to
                                 exactly that. Absent prints nothing-measured.

    THE COMPILE BLOCK is compile_fields() in full, passed in already
    formatted, because the run supplies the numbers and this file decides what
    they mean.
    """
    return ("materialStatus=%s materialScriptReturn=%d materialPath=%s "
            "materialExistedBefore=%s materialParams=%s materialParamsMade=%d/%d "
            "materialScalars=%s materialConnections=%d/%d "
            "materialUvHeadVia=%s materialUvHeadTriedAtWorst=%s "
            "materialUvHeadReadback=%s materialUvHeadByPropertyWrite=%s "
            "materialColourDefault=%s materialNormalDefault=%s "
            "materialRoughnessDefault=%s "
            "materialDefaultsBound=%d/%d materialDefaultsDetail=%s "
            "materialDefaultsStat=samplers-with-a-default-whose-derived-type-matches/over-texture-parameters "
            "%s %s %s "
            "materialSaved=%s "
            "materialVerdictIs=materialScriptReturn/not-the-editor-process-exit "
            "materialNote=%s"
            % (status, material_return(status), ASSET_PATH,
               "yes" if existed else "no",
               "/".join(TEXTURE_PARAMS), params_made, params_asked,
               "/".join(SCALAR_PARAMS), wired, asked,
               uv_via, uv_tried, uv_readback, uv_by_prop,
               str(colour_from).replace(" ", "~"),
               str(normal_from).replace(" ", "~"),
               str(roughness_from).replace(" ", "~"),
               defaults_bound, defaults_asked, defaults_detail,
               compression_block if compression_block else compression_field([]),
               compile_block, generated_block,
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
        # (saved, made, asked_params, wired, asked, byPropWrite,
        #  defaults_bound, defaults_asked, compile, status, return)
        (True, 3, 3, 14, 14, 0, 3, 3, COMPILE_OK, STATUS_MADE, 0),
        (True, 3, 3, 12, 14, 0, 3, 3, COMPILE_OK, STATUS_PARTIAL, 2),  # run 19
        (True, 2, 3, 14, 14, 0, 3, 3, COMPILE_OK, STATUS_PARTIAL, 2),
        (True, 3, 3, 0, 0, 0, 3, 3, COMPILE_OK, STATUS_PARTIAL, 2),
        (False, 3, 3, 14, 14, 0, 3, 3, COMPILE_OK, STATUS_NOT_SAVED, 2),
        # THE THIRD STATE. Everything the acceptance asks for, with one of
        # the two heads standing on the last-resort property write: the word
        # changes and the return stays 2, because only the still can say
        # whether that head reached the shader.
        (True, 3, 3, 14, 14, 1, 3, 3, COMPILE_OK, STATUS_BY_PROPERTY_WRITE, 2),
        (True, 3, 3, 14, 14, 2, 3, 3, COMPILE_OK, STATUS_BY_PROPERTY_WRITE, 2),
        # AND THE ORDER OF THE CLAUSES. A property write that rescued one
        # head of a material still short of 14 of 14 does not rename PARTIAL.
        (True, 3, 3, 13, 14, 1, 3, 3, COMPILE_OK, STATUS_PARTIAL, 2),
        # ---- THE TWO CLAUSES ADDED AFTER RUN 23, BOTH WAYS ROUND ----------
        # RUN 23'S OWN INPUTS, EXACTLY: saved, 3 of 3 parameters, 14 of 14
        # connections, no property write, and one of two defaults bound with
        # nothing anywhere able to say whether a shader existed. That printed
        # MADE and a return of 0 over a material the renderer never used.
        # It is PARTIAL now, on the defaults clause, and it can never be MADE
        # again whatever the compile channel says.
        (True, 3, 3, 14, 14, 0, 1, 3, COMPILE_UNPROVEN, STATUS_PARTIAL, 2),
        (True, 3, 3, 14, 14, 0, 2, 3, COMPILE_OK, STATUS_PARTIAL, 2),
        # DEFAULTS FULL AND THE COMPILE CHANNEL SILENT. This is the state the
        # script was in for its whole life and the word for it is not MADE.
        (True, 3, 3, 14, 14, 0, 3, 3, COMPILE_UNPROVEN,
         STATUS_COMPILE_UNPROVEN, 2),
        # A REPORTED DIAGNOSTIC OUTRANKS THE PROPERTY-WRITE WORD, because a
        # material that did not compile is the bigger fact about the run.
        (True, 3, 3, 14, 14, 0, 3, 3, COMPILE_ERRORS, STATUS_NOT_COMPILED, 2),
        (True, 3, 3, 14, 14, 1, 3, 3, COMPILE_ERRORS, STATUS_NOT_COMPILED, 2),
        # AND NOTHING RECORDED ABOUT THE DEFAULTS IS NOT A PASS EITHER: a
        # denominator of zero is a run that measured nothing.
        (True, 3, 3, 14, 14, 0, 0, 0, COMPILE_OK, STATUS_PARTIAL, 2),
    ]
    for (saved, made, pasked, wired, casked, pw, dbound, dasked, comp,
         want, want_code) in cases:
        checks += 1
        got = material_status(saved, made, pasked, wired, casked, pw,
                              dbound, dasked, comp)
        code = material_return(got)
        if got != want or code != want_code:
            bad.append("status(saved=%s made=%d/%d wired=%d/%d "
                       "byPropWrite=%d defaults=%d/%d compile=%s) gave %s/%d "
                       "and should give %s/%d"
                       % (saved, made, pasked, wired, casked, pw, dbound,
                          dasked, comp, got, code, want, want_code))
    # THE RATCHET, STATED AS A CHECK AND NOT AS A COMMENT. MADE may only get
    # harder: every combination of inputs that reads MADE today must have read
    # MADE under the six-argument rule too, which for these clauses means the
    # only route to MADE is full defaults with a compile verdict of OK.
    checks += 1
    widened = []
    for dbound in (0, 1, 2, 3):
        for comp in (COMPILE_OK, COMPILE_ERRORS, COMPILE_UNPROVEN,
                     COMPILE_NO_SHADER):
            got = material_status(True, 3, 3, 14, 14, 0, dbound, 3, comp)
            if got == STATUS_MADE and not (dbound == 3 and comp == COMPILE_OK):
                widened.append((dbound, comp))
    if widened:
        bad.append("MADE got EASIER: it is now reachable with %s, and the one "
                   "rule this word has is that it only ever narrows" % widened)
    # ---- THE UV HEAD, WHICH IS THE THING THAT DID NOT WIRE --------------
    # None of this can open Unreal, and that is the point: what CAN be run
    # here is the search, the counting and the tokens, so an engine faked in
    # nine lines below stands in for the editor's yes and no. The one thing
    # left unrun is which pin name the real editor accepts, and the run
    # prints that as materialUvHeadVia rather than this file asserting it.

    def accept_only(pair):
        return lambda o, i: (o, i) == pair

    def accept_nothing(o, i):
        return False

    def throw_unless(pair):
        def f(o, i):
            if (o, i) != pair:
                raise RuntimeError("an engine that rejects an unknown pin "
                                   "name by throwing rather than by no")
            return True
        return f

    ncand = len(UV_PIN_CANDIDATES)
    checks += 1
    if ncand < 2 or len(set(UV_PIN_CANDIDATES)) != ncand:
        bad.append("the %d UV candidate pair(s) must be at least 2 and all "
                   "distinct: %s" % (ncand, UV_PIN_CANDIDATES))
    checks += 1
    dirty = [p for p in UV_PIN_CANDIDATES
             if any((" " in n) or ("=" in n) for n in p)]
    if dirty:
        bad.append("a candidate pin name carries a space or an equals and "
                   "would break the verdict line: %s" % dirty)
    checks += 1
    if ("", "Input") not in UV_PIN_CANDIDATES:
        bad.append("the pair runs 19 and 20 asked for is not in the sweep, so "
                   "this change could wire FEWER connections than they did")
    checks += 1
    if pin_token("", "") != "out.empty..in.empty" or \
            pin_token("", "Input") != "out.empty..in.Input" or \
            " " in pin_token("", ""):
        bad.append("pin_token does not name the empty pin or carries a space: "
                   "%s %s" % (pin_token("", ""), pin_token("", "Input")))
    # ACCEPTING CASE FIRST: an engine that takes the pair this sweep tries
    # first answers on the first ask and is named for it.
    checks += 1
    got = connect_by_candidates(accept_only(UV_PIN_CANDIDATES[0]),
                                UV_PIN_CANDIDATES)
    if got != (True, 1, UV_PIN_CANDIDATES[0][0], UV_PIN_CANDIDATES[0][1]):
        bad.append("the sweep did not take the first candidate from an engine "
                   "that accepts only it: %s" % (got,))
    # AND THE ONE THE OLD CODE USED, which is the guarantee that this change
    # cannot wire less than run 20 did: an engine behaving exactly as run 20's
    # would have to for "Input" to be right still wires, at candidate 2 of 9.
    checks += 1
    old_pair = ("", "Input")
    ok, tried, o, i = connect_by_candidates(accept_only(old_pair),
                                            UV_PIN_CANDIDATES)
    if not ok or (o, i) != old_pair or tried != UV_PIN_CANDIDATES.index(old_pair) + 1:
        bad.append("an engine accepting only the name runs 19 and 20 used is "
                   "no longer wired by the sweep: ok=%s tried=%d pair=%s"
                   % (ok, tried, (o, i)))
    # A CANDIDATE THAT RAISES IS A NO AND NOT THE END OF THE SWEEP. Caught
    # here rather than left to propagate, so that losing the guard prints a
    # named failure and not a traceback from inside the fixture.
    checks += 1
    try:
        ok, tried, o, i = connect_by_candidates(
            throw_unless(UV_PIN_CANDIDATES[-1]), UV_PIN_CANDIDATES)
    except Exception as e:
        ok, tried, o, i = False, -1, "raised", str(e)[:60].replace(" ", "~")
    if not ok or (o, i) != UV_PIN_CANDIDATES[-1] or tried != ncand:
        bad.append("a throwing candidate ended the sweep instead of counting "
                   "as a no: ok=%s tried=%s pair=%s" % (ok, tried, (o, i)))
    # REJECTING CASE: nothing answers, and the value says so with its total.
    checks += 1
    ok, tried, o, i = connect_by_candidates(accept_nothing, UV_PIN_CANDIDATES)
    if ok or tried != ncand or o is not None or i is not None:
        bad.append("the sweep claimed a connection from an engine that "
                   "refuses every name: ok=%s tried=%d pair=%s"
                   % (ok, tried, (o, i)))
    # THE DENOMINATOR. A head connection swept over nine names is ONE
    # connection asked for, or 14 stops being the number runs 19 and 20
    # printed and the fraction stops being comparable across runs.
    good = Wiring()
    good_heads = []
    for head in UV_HEAD_NAMES:
        swept = connect_by_candidates(accept_only(UV_PIN_CANDIDATES[0]),
                                      UV_PIN_CANDIDATES)
        good_heads.append((swept[0], pin_token(swept[2], swept[3]),
                           swept[1], True))
        good.record(swept[0], uv_head_note("texcoord-to-%s" % head, ncand))
    for _ in range(12):
        good.record(True, "a-note-for-a-connection-that-landed")
    checks += 1
    if (good.wired, good.asked, good.notes) != (14, 14, []):
        bad.append("a swept head connection did not count as one connection: "
                   "wired=%d asked=%d notes=%s"
                   % (good.wired, good.asked, good.notes))
    checks += 1
    if material_status(True, 3, 3, good.wired, good.asked,
                       property_write_heads(good_heads)[0],
                       len(TEXTURE_PARAMS), len(TEXTURE_PARAMS),
                       COMPILE_OK) != STATUS_MADE:
        bad.append("14 of 14 wired with 3 of 3 parameters and a saved asset "
                   "does not read MADE, so the acceptance can never be met")
    # AND RUN 19 AND 20's OWN SHAPE, rebuilt through the same tally: two heads
    # refused by every name, twelve others landing, 12 of 14 and PARTIAL.
    run19 = Wiring()
    for head in UV_HEAD_NAMES:
        swept = connect_by_candidates(accept_nothing, UV_PIN_CANDIDATES)
        run19.record(swept[0], uv_head_note("texcoord-to-%s" % head, ncand))
    for _ in range(12):
        run19.record(True, None)
    checks += 1
    if (run19.wired, run19.asked) != (12, 14) or \
            material_status(True, 3, 3, run19.wired, run19.asked, 0,
                            len(TEXTURE_PARAMS), len(TEXTURE_PARAMS),
                            COMPILE_OK) != STATUS_PARTIAL:
        bad.append("the run 19 shape no longer reproduces as 12/14 PARTIAL: "
                   "wired=%d asked=%d" % (run19.wired, run19.asked))
    checks += 1
    if not all(n.startswith("texcoord-to-%s-refused" % h)
               for n, h in zip(run19.notes, UV_HEAD_NAMES)):
        bad.append("the refusal notes no longer carry the token runs 19 and "
                   "20 printed as a prefix, so a grep for it would miss the "
                   "next failure: %s" % run19.notes)
    # ---- THE THIRD STATUS WORD, ACCEPTING CASE FIRST --------------------
    # Ruled 2026-09-03: the COUNT may include a head made by the last-resort
    # property write, and the WORD may not say MADE, because what a struct
    # written by value does to the compiled shader is unproven here. Both
    # cases below are built from head RECORDS through property_write_heads
    # rather than from a hand-written count, so the string main() writes and
    # the counter that reads its suffix are exercised together.
    checks += 1
    took = property_write_via(ncand, True)
    if not took.endswith(PROP_WRITE_TOOK) or \
            property_write_via(ncand, None).endswith(PROP_WRITE_TOOK) or \
            property_write_via(ncand, False).endswith(PROP_WRITE_TOOK) or \
            " " in took or "=" in took:
        bad.append("the via token for a head the property write TOOK is not "
                   "told apart from unavailable and refused, so the count "
                   "would read the wrong heads: %s / %s / %s"
                   % (took, property_write_via(ncand, None),
                      property_write_via(ncand, False)))
    # ACCEPTING: maskU taken by the first pin name, maskV refused by all nine
    # and rescued by the property write. 14 of 14, one head on the last
    # resort, which is the shape this word exists to name.
    prop = Wiring()
    prop_heads = []
    for n, head in enumerate(UV_HEAD_NAMES):
        note = uv_head_note("texcoord-to-%s" % head, ncand)
        if n == 0:
            swept = connect_by_candidates(accept_only(UV_PIN_CANDIDATES[0]),
                                          UV_PIN_CANDIDATES)
            prop_heads.append((True, pin_token(swept[2], swept[3]),
                               swept[1], True))
        else:
            swept = connect_by_candidates(accept_nothing, UV_PIN_CANDIDATES)
            prop_heads.append((True, took, swept[1], True))
        prop.record(True, note)
    for _ in range(12):
        prop.record(True, None)
    checks += 1
    by_prop = property_write_heads(prop_heads)
    if by_prop != (1, 2, "1/2"):
        bad.append("a head rescued by the property write is not counted as "
                   "one of the two heads recorded: %s" % (by_prop,))
    checks += 1
    got = material_status(True, 3, 3, prop.wired, prop.asked, by_prop[0],
                          len(TEXTURE_PARAMS), len(TEXTURE_PARAMS),
                          COMPILE_OK)
    if (prop.wired, prop.asked) != (14, 14) or \
            got != STATUS_BY_PROPERTY_WRITE or material_return(got) != 2:
        bad.append("14 of 14 with %d of %d head(s) on the property write does "
                   "not read %s/2: wired=%d asked=%d gave %s/%d"
                   % (by_prop[0], by_prop[1], STATUS_BY_PROPERTY_WRITE,
                      prop.wired, prop.asked, got, material_return(got)))
    # REJECTING: THE SAME 14 OF 14 WITH NO HEAD ON THE PROPERTY WRITE STILL
    # READS MADE. Without this case a change that renamed every passing run
    # would have replaced one overclaim with another, and the route queue
    # 062's acceptance was written for could never be reported.
    checks += 1
    none_prop = property_write_heads(good_heads)
    got = material_status(True, 3, 3, good.wired, good.asked, none_prop[0],
                          len(TEXTURE_PARAMS), len(TEXTURE_PARAMS),
                          COMPILE_OK)
    if none_prop != (0, 2, "0/2") or got != STATUS_MADE or \
            material_return(got) != 0:
        bad.append("14 of 14 with both heads taken by a named pin no longer "
                   "reads MADE/0: byPropertyWrite=%s gave %s/%d"
                   % (none_prop, got, material_return(got)))
    # AND THE ZERO'S DENOMINATOR, both ways round: none of two heads is not
    # the same fact as no head recorded at all, and a write that was
    # unavailable made nothing however many times it was tried.
    checks += 1
    unmade = [(False, property_write_via(ncand, None), ncand, None)] * 2
    if property_write_heads(unmade) != (0, 2, "0/2") or \
            property_write_heads([]) != (0, 0, "nothing-measured"):
        bad.append("the property-write count ships a bare zero or counts a "
                   "write that never took: %s / %s"
                   % (property_write_heads(unmade), property_write_heads([])))
    # ---- and the three values the head ships, all four shapes ------------
    win = pin_token("", "")
    checks += 1
    fields = uv_head_fields([(True, win, 1, True), (True, win, 1, True)], ncand)
    if fields != ("both." + win, "1/%d" % ncand, "2/2..unreadable0"):
        bad.append("two heads made the same way do not read as one value: %s"
                   % (fields,))
    checks += 1
    other = took
    fields = uv_head_fields([(True, win, 1, True), (True, other, ncand, False)],
                            ncand)
    if fields != ("maskU.%s/maskV.%s" % (win, other),
                  "%d/%d" % (ncand, ncand), "1/2..unreadable0"):
        bad.append("two heads made different ways are not named apart: %s"
                   % (fields,))
    checks += 1
    fields = uv_head_fields([(True, win, 1, None), (True, win, 2, None)], ncand)
    if fields != ("both." + win, "2/%d" % ncand, "0/2..unreadable2"):
        bad.append("a readback the editor would not answer is being counted "
                   "as a no, or the tried value is not the worst of the two: "
                   "%s" % (fields,))
    checks += 1
    fields = uv_head_fields([], ncand)
    if fields[0] != "nothing-measured" or "nothing-measured" not in fields[1] \
            or fields[2] != "nothing-measured":
        bad.append("a head that never ran does not print the words nothing "
                   "measured: %s" % (fields,))
    # AND THE LINE ITSELF, because an unrun formatter printing a plausible
    # string is the fault this file exists on the tested side to avoid. The
    # rule every reader of these files depends on: one equals per token and
    # no spaces inside a value.
    #
    # THE DEFAULTS AND THE COMPILE EVIDENCE THE LINES BELOW ARE BUILT FROM.
    # run23_vias is what run 23 actually had, reconstructed from its own
    # ue-build.txt line: colour from an engine path and correct, normal from
    # nothing at all, roughness from the COLOUR list and therefore an sRGB
    # colour texture in a slot declared linear. One of three, and the key it
    # printed said one of two.
    run23_vias = [
        (TEXTURE_PARAMS[0], "engine", SAMPLER_COLOR, SAMPLER_COLOR),
        (TEXTURE_PARAMS[1], "none", None, SAMPLER_NORMAL),
        (TEXTURE_PARAMS[2], "engine", SAMPLER_COLOR, SAMPLER_LINEAR_COLOR),
    ]
    fixed_vias = [(TEXTURE_PARAMS[I], "engine" if I == 0 else "generated",
                   MAP_SAMPLER_TYPES[I], MAP_SAMPLER_TYPES[I])
                  for I in range(len(TEXTURE_PARAMS))]
    run23_bound, run23_asked, run23_detail = defaults_field(run23_vias)
    fixed_bound, fixed_asked, fixed_detail = defaults_field(fixed_vias)
    checks += 1
    if (run23_bound, run23_asked) != (1, 3) or \
            "normal" not in run23_detail.lower() or \
            "TYPE-MISMATCH" not in run23_detail or \
            "no-default" not in run23_detail:
        bad.append("run 23's own defaults no longer read as one of three with "
                   "the missing one and the mismatched one named apart: %d/%d "
                   "%s" % (run23_bound, run23_asked, run23_detail))
    checks += 1
    if (fixed_bound, fixed_asked) != (3, 3) or "TYPE-MISMATCH" in fixed_detail:
        bad.append("three samplers each carrying a default of the type they "
                   "were declared with do not read 3/3: %d/%d %s"
                   % (fixed_bound, fixed_asked, fixed_detail))
    checks += 1
    if defaults_field([]) != (0, len(TEXTURE_PARAMS), "nothing-measured"):
        bad.append("a run that recorded no defaults at all ships a bare zero "
                   "instead of the words nothing measured: %s"
                   % (defaults_field([]),))
    # THE FALLBACK'S OWN COUNT, ACCEPTING CASE FIRST: every engine default
    # good is 0 of 0, and the fallback covering the two run 23 got wrong is
    # 2 of 2. The case that must never look like a pass is the fallback
    # itself failing, which is 1 of 2 or 0 of 2 and is a short fraction.
    checks += 1
    if "materialGeneratedDefaults=0/0" not in generated_field(
            ["engine"] * 3, 0) or \
            "materialGeneratedDefaults=2/2" not in generated_field(
                ["engine", "generated", "generated"], 2) or \
            "materialGeneratedDefaults=1/2" not in generated_field(
                ["engine", "generated", "none"], 2) or \
            [t for t in generated_field([], 0).split() if t.count("=") != 1]:
        bad.append("the generated-default count does not carry both halves, "
                   "or a token of it is not one key=value: %s / %s / %s"
                   % (generated_field(["engine"] * 3, 0),
                      generated_field(["engine", "generated", "generated"], 2),
                      generated_field(["engine", "generated", "none"], 2)))
    # THE THREE COMPILE BLOCKS, BUILT THE WAY main() BUILDS ONE: the word is
    # computed once and handed to the formatter, so the selftest cannot pass
    # over an arrangement the run does not have. The control the word is
    # decided by is the TWIN and the engine reading is passed separately,
    # exactly as main() passes them, so a run cannot quietly gate on the
    # engine number.
    def block(errors, examined, px_, vx_, samplers_, begin, end,
              ctl=None, ctl_vx=None, ctl_from=None,
              chan=None, chan_vx=None, chan_from=None,
              chan_answered=None, chan_asked=None):
        return compile_fields(
            compile_verdict(errors, examined, px_, begin, end, ctl),
            errors, examined, px_, vx_, samplers_, begin, end,
            ctl, ctl_vx, ctl_from,
            chan, chan_vx, chan_from, chan_answered, chan_asked)

    # A RUN THAT ASKED NOTHING: no log, no statistics, no twin and no engine
    # reading, which is the shape that must print the words nothing measured
    # rather than a bare zero.
    unproven_block = block(None, 0, None, None, None, False, False)
    errors_block = block(2, 1200, 0, 0, 3, True, True)
    # THE PASSING SHAPE CARRIES BOTH CONTROLS, because the acceptance of this
    # amendment is that a reader can tell the twin from the engine reading on
    # the line itself.
    ok_block = block(0, 1200, 187, 42, 3, True, True,
                     41, 12, CONTROL_TWIN_PATH,
                     187, 42, CONTROL_MATERIALS[0], 1, len(CONTROL_MATERIALS))

    line = material_line(STATUS_PARTIAL, 3, 3, 12, 14, False,
                         default_via("engine",
                                     "/Engine/EngineResources/DefaultTexture",
                                     SAMPLER_COLOR, SAMPLER_COLOR),
                         default_via("none", "none-of-2-candidates",
                                     None, SAMPLER_NORMAL),
                         default_via("engine",
                                     "/Engine/EngineResources/DefaultTexture",
                                     SAMPLER_COLOR, SAMPLER_LINEAR_COLOR),
                         run23_bound, run23_asked, run23_detail,
                         unproven_block, generated_field([], 0), True,
                         [uv_head_note("texcoord-to-maskU", ncand),
                          uv_head_note("texcoord-to-maskV", ncand)],
                         *(uv_head_fields(unmade, ncand)
                           + (property_write_heads(unmade)[2],)))
    checks += 1
    if [t for t in line.split() if t.count("=") != 1]:
        bad.append("the material line has a token that is not one key=value: %s"
                   % [t for t in line.split() if t.count("=") != 1])
    checks += 1
    if "materialStatus=PARTIAL" not in line or "materialScriptReturn=2" not in line:
        bad.append("the line does not carry the status and the return it was "
                   "built from: %s" % line)
    checks += 1
    if "materialDefaultsBound=1/3" not in line:
        bad.append("an engine default that did not resolve ships without its "
                   "denominator, or the denominator is not the number of "
                   "TEXTURE PARAMETERS: %s" % line)
    # THE THIRD SAMPLER'S KEY, WHICH DID NOT EXIST BEFORE 6 SEPTEMBER. A
    # roughness default nobody printed is how an sRGB colour texture sat in a
    # linear slot through five runs.
    checks += 1
    if "materialRoughnessDefault=" not in line or \
            "materialDefaultsDetail=" not in line:
        bad.append("the roughness sampler's default or the per-sampler "
                   "breakdown is not on the line: %s" % line)
    checks += 1
    if "materialCompile=UNPROVEN" not in line or \
            "materialCompileErrors=nothing-measured" not in line or \
            "materialCompileInstructions=pixel.not-available..vertex.not-available" not in line:
        bad.append("a run that read no log and got no statistics does not say "
                   "so in both channels: %s" % line)
    checks += 1
    if "materialUvHeadVia=" not in line or \
            ("materialUvHeadTriedAtWorst=%d/%d" % (ncand, ncand)) not in line \
            or "materialUvHeadReadback=0/2..unreadable2" not in line \
            or "materialUvHeadByPropertyWrite=0/2" not in line:
        bad.append("the failing line does not carry what the UV head cost, "
                   "what read back, and how many heads the last resort made: "
                   "%s" % line)
    # AND THE PASSING SHAPE, which is what the acceptance of this item looks
    # like on the wire. A formatter only ever run over its failure case is
    # half a formatter.
    good_line = material_line(STATUS_MADE, 3, 3, 14, 14, True,
                              default_via("engine",
                                          "/Engine/EngineResources/DefaultTexture",
                                          SAMPLER_COLOR, SAMPLER_COLOR),
                              default_via("generated",
                                          PACKAGE + "/" + GENERATED_DEFAULTS[1][0],
                                          SAMPLER_NORMAL, SAMPLER_NORMAL),
                              default_via("generated",
                                          PACKAGE + "/" + GENERATED_DEFAULTS[2][0],
                                          SAMPLER_LINEAR_COLOR,
                                          SAMPLER_LINEAR_COLOR),
                              fixed_bound, fixed_asked, fixed_detail,
                              ok_block,
                              generated_field(["engine", "generated",
                                               "generated"], 2), True, [],
                              *(uv_head_fields(good_heads, ncand)
                                + (property_write_heads(good_heads)[2],)))
    checks += 1
    if [t for t in good_line.split() if t.count("=") != 1]:
        bad.append("the passing line has a token that is not one key=value: %s"
                   % [t for t in good_line.split() if t.count("=") != 1])
    checks += 1
    if "materialStatus=MADE" not in good_line or \
            "materialScriptReturn=0" not in good_line or \
            "materialConnections=14/14" not in good_line or \
            ("materialUvHeadVia=both.%s" % win) not in good_line or \
            "materialUvHeadReadback=2/2..unreadable0" not in good_line or \
            "materialUvHeadByPropertyWrite=0/2" not in good_line or \
            "materialDefaultsBound=3/3" not in good_line or \
            "materialCompile=OK" not in good_line or \
            "materialCompileErrors=0/1200" not in good_line or \
            "materialCompileInstructions=pixel.187..vertex.42" not in good_line or \
            "materialNote=none" not in good_line:
        bad.append("the passing line is not what the acceptance asks for: %s"
                   % good_line)
    # AND THE PRINTED RULE NAMES THE CONDITION THE WORD WAS DECIDED BY, so
    # a reader of the line can see that a pass needed a denominator and both
    # markers without opening this file.
    checks += 1
    rule = [t for t in good_line.split()
            if t.startswith("materialCompileRule=")]
    if len(rule) != 1 or "lines-examined-above-zero" not in rule[0] or \
            "both-markers" not in rule[0] or \
            "ERRORS-with-or-without-markers" not in rule[0]:
        bad.append("the rule token does not name the condition OK now needs, "
                   "or that ERRORS does not need the markers: %s" % rule)
    # ---- THE TWIN AND THE ENGINE READING, WHICH ARE TWO KEYS AND NOT ONE --
    # Amendment A1 of the ruling of 2026-09-06. The gating control is a
    # material this script MAKES and recompiles in this process; the engine
    # materials are a second, non-gating reading beside it. The passing line
    # has to carry both, and the words have to be told apart on the wire.
    want_twin = ("materialCompileControl=pixel.41..vertex.12..from.%s"
                 % CONTROL_TWIN_PATH)
    want_chan = ("materialCompileChannel=pixel.187..vertex.42..from.%s..answered.1/%d"
                 % (CONTROL_MATERIALS[0], len(CONTROL_MATERIALS)))
    checks += 1
    if want_twin not in good_line or want_chan not in good_line:
        bad.append("the passing line does not carry the twin and the engine "
                   "reading as two separate keys: %s" % good_line)
    # AND THE TEXT KEY SAYS WHICH IS WHICH, because a reader who has only the
    # line has to be able to tell that the gating control was a twin.
    checks += 1
    control_is = [t for t in good_line.split()
                  if t.startswith("materialCompileControlIs=")]
    if len(control_is) != 1 or "TWIN" not in control_is[0] or \
            "gates-nothing" not in control_is[0] or \
            "over-engine-materials-asked" not in control_is[0]:
        bad.append("the control's text key does not name the twin, or does "
                   "not say that the engine reading gates nothing and what "
                   "its denominator counts: %s" % control_is)
    # THE CHANNEL FORMATTER, ACCEPTING SHAPE FIRST and then the two absences
    # it has to tell apart: asked and silent, against never asked at all.
    chan_dead = block(0, 1200, 0, 0, 3, True, True,
                      None, None, "twin-create-threw",
                      None, None,
                      "none-of-%d-engine-materials-answered"
                      % len(CONTROL_MATERIALS), 0, len(CONTROL_MATERIALS))
    checks += 1
    if ("materialCompileChannel=pixel.not-available..vertex.not-available..from.none-of-%d-engine-materials-answered..answered.0/%d"
            % (len(CONTROL_MATERIALS), len(CONTROL_MATERIALS))) not in chan_dead:
        bad.append("a channel that was asked and answered nothing does not "
                   "print not-available with its denominator: %s" % chan_dead)
    checks += 1
    if "materialCompileChannel=pixel.not-available..vertex.not-available..from.nothing-measured..answered.nothing-measured" \
            not in unproven_block:
        bad.append("a channel that was never asked prints a bare zero "
                   "denominator instead of the words nothing measured: %s"
                   % unproven_block)
    # AND THE REFUSED TWIN NAMES THE STEP THAT REFUSED IT, so a NO-SHADER
    # that did not happen is diagnosable from the line.
    checks += 1
    if "materialCompileControl=pixel.not-available..vertex.not-available..from.twin-create-threw" \
            not in chan_dead:
        bad.append("a twin that could not be made does not name the step "
                   "that refused it: %s" % chan_dead)
    # THE ONE THAT MATTERS, AND IT IS THE WHOLE OF AMENDMENT A1: a live
    # ENGINE reading must NOT let our zero mean NO-SHADER, and a live TWIN
    # must, with the engine reading silent. The verdict function never sees
    # the engine number, and this is the check that says so out loud.
    checks += 1
    if "materialCompile=UNPROVEN" not in block(
            0, 1200, 0, 0, 3, True, True,
            None, None, "twin-statistics-refused",
            187, 42, CONTROL_MATERIALS[0], 1, len(CONTROL_MATERIALS)):
        bad.append("a zero instruction count beside a live ENGINE reading and "
                   "no twin is not UNPROVEN, which is run 24's mistake with a "
                   "new key on it")
    checks += 1
    if "materialCompile=NO-SHADER" not in block(
            0, 1200, 0, 0, 3, True, True,
            41, 12, CONTROL_TWIN_PATH,
            None, None, "none-of-4-engine-materials-answered", 0, 4):
        bad.append("a zero instruction count beside a twin that answered "
                   "above zero is not NO-SHADER when the engine reading is "
                   "silent, so the non-gating key is gating something")
    # AND THE THIRD STATE ON THE WIRE. It is the other half of this item's
    # acceptance, so the formatter for it must not ship unrun either: this is
    # the exact line a verifier will read beside the four frames.
    prop_line = material_line(STATUS_BY_PROPERTY_WRITE, 3, 3, 14, 14, True,
                              default_via("engine",
                                          "/Engine/EngineResources/DefaultTexture",
                                          SAMPLER_COLOR, SAMPLER_COLOR),
                              default_via("generated",
                                          PACKAGE + "/" + GENERATED_DEFAULTS[1][0],
                                          SAMPLER_NORMAL, SAMPLER_NORMAL),
                              default_via("generated",
                                          PACKAGE + "/" + GENERATED_DEFAULTS[2][0],
                                          SAMPLER_LINEAR_COLOR,
                                          SAMPLER_LINEAR_COLOR),
                              fixed_bound, fixed_asked, fixed_detail,
                              ok_block,
                              generated_field(["engine", "generated",
                                               "generated"], 2), True, [],
                              *(uv_head_fields(prop_heads, ncand)
                                + (property_write_heads(prop_heads)[2],)))
    checks += 1
    if [t for t in prop_line.split() if t.count("=") != 1]:
        bad.append("the property-write line has a token that is not one "
                   "key=value: %s"
                   % [t for t in prop_line.split() if t.count("=") != 1])
    checks += 1
    if "materialStatus=WIRED-BY-PROPERTY-WRITE" not in prop_line or \
            "materialScriptReturn=2" not in prop_line or \
            "materialConnections=14/14" not in prop_line or \
            "materialUvHeadByPropertyWrite=1/2" not in prop_line or \
            ("maskV.%s" % took) not in prop_line:
        bad.append("the third state does not print the word, the return, the "
                   "count it was decided from and which head stood on the "
                   "last resort: %s" % prop_line)
    # ---- THE SAMPLER TYPE A TEXTURE DERIVES, BOTH WAYS ROUND -------------
    # This is the function that would have refused run 23's roughness default,
    # so it is exercised against the exact pair of textures that run had: an
    # sRGB colour texture and nothing at all.
    sampler_cases = [
        ("TextureCompressionSettings.TC_DEFAULT", True, SAMPLER_COLOR),
        ("TC_DEFAULT", False, SAMPLER_LINEAR_COLOR),
        ("TextureCompressionSettings.TC_NORMALMAP", False, SAMPLER_NORMAL),
        # A normal map's sRGB flag does not change the type it derives, which
        # is why the flat normal below is safe whatever the importer decides.
        ("TC_NORMALMAP", True, SAMPLER_NORMAL),
        ("TC_GRAYSCALE", False, SAMPLER_LINEAR_GRAYSCALE),
        ("TC_GRAYSCALE", True, SAMPLER_GRAYSCALE),
        ("TC_MASKS", False, SAMPLER_MASKS),
        ("TC_ALPHA", True, SAMPLER_ALPHA),
        ("TC_DISTANCEFIELDFONT", True, SAMPLER_DISTANCE_FIELD_FONT),
        # A texture that answered nothing, and one that answered a raw
        # integer this file cannot interpret. Both are unknown, and unknown
        # never matches an asked type, so the default is refused rather than
        # assigned on a guess.
        (None, True, None),
        ("7", False, None),
        # THE FOUR SPELLINGS RUN 24 COULD HAVE BEEN HANDED, and the reason
        # this file lost a round trip. It set TC_NORMALMAP, the importer had
        # already auto-detected a normal map, and the readback still derived
        # LINEAR_COLOR, which only happens when the tail of the value is not
        # a bare leaf. Every one of these is the same texture.
        ("<TextureCompressionSettings.TC_NORMALMAP: 1>", False, SAMPLER_NORMAL),
        ("TextureCompressionSettings.TC_NORMALMAP: 1", False, SAMPLER_NORMAL),
        ("TC_NORMALMAP: 1", False, SAMPLER_NORMAL),
        ("TC_Normalmap", False, SAMPLER_NORMAL),
        # And the same shapes for the leaf that legitimately takes the
        # engine's default branch, so the fix cannot be read as "normal maps
        # only".
        ("<TextureCompressionSettings.TC_DEFAULT: 0>", True, SAMPLER_COLOR),
        ("TC_DEFAULT: 0", False, SAMPLER_LINEAR_COLOR),
        ("TC_DISTANCE_FIELD_FONT", True, SAMPLER_DISTANCE_FIELD_FONT),
        # A LEAF THAT IS NOT A COMPRESSION SETTING AT ALL DERIVES NOTHING.
        # This is the branch run 24 fell into: the catch-all used to answer a
        # plausible colour type for any string whatsoever, so a reading this
        # file could not parse and a texture of the wrong type printed the
        # same value.
        ("TC_NOT_A_REAL_LEAF", False, None),
        ("SomeOtherEnum.EV_WHATEVER", True, None),
    ]
    for compression, srgb, want in sampler_cases:
        checks += 1
        got = derived_sampler_type(compression, srgb)
        if got != want:
            bad.append("derived_sampler_type(%s, srgb=%s) gave %s and should "
                       "give %s" % (compression, srgb, got, want))
    # THE LEAF CUT OUT OF EACH SPELLING, NAMED, so a failure here says which
    # half of the derivation broke rather than only that a type is wrong.
    for spelling, want_leaf in (
            ("<TextureCompressionSettings.TC_NORMALMAP: 1>", "NORMALMAP"),
            ("TextureCompressionSettings.TC_NORMALMAP", "NORMALMAP"),
            ("TC_NORMALMAP", "NORMALMAP"),
            ("TC_DISTANCE_FIELD_FONT", "DISTANCEFIELDFONT"),
            ("TC_VectorDisplacementmap", "VECTORDISPLACEMENTMAP"),
            (None, None),
            ("", None),
            ("3", None),
            # A VALUE WITH NO MEMBER IN IT CUTS TO THE TYPE NAME, and that is
            # correct: this function cuts, it does not validate. The refusal
            # is the known-leaves gate in derived_sampler_type, asserted
            # directly below, because a leaf that is not a compression setting
            # must never reach the engine's default branch.
            ("<TextureCompressionSettings: 3>", "TEXTURECOMPRESSIONSETTINGS")):
        checks += 1
        got_leaf = compression_leaf(spelling)
        if got_leaf != want_leaf:
            bad.append("compression_leaf(%s) gave %s and should give %s"
                       % (spelling, got_leaf, want_leaf))
    # AND THE LIVE ENUM DECIDES, NOT THIS FILE. A leaf this file has never
    # heard of is still the engine's default case when the engine says it is
    # a compression setting, which is what the editor side passes in.
    checks += 1
    if derived_sampler_type("<TextureCompressionSettings: 3>", False) is not None \
            or derived_sampler_type("<TextureCompressionSettings: 3>",
                                    True) is not None:
        bad.append("a value carrying no enum member is deriving a sampler "
                   "type from its own type name")
    checks += 1
    if derived_sampler_type("TC_FUTURE_FORMAT", False) is not None or \
            derived_sampler_type("TC_FUTURE_FORMAT", False,
                                 set(["FUTUREFORMAT"])) != SAMPLER_LINEAR_COLOR:
        bad.append("an unknown leaf is not refused by default, or a leaf the "
                   "live enum vouches for is not taking the engine's default "
                   "branch")
    # THE READBACK KEY, WHICH DID NOT EXIST BEFORE RUN 25 AND IS THE HALF
    # THAT WOULD HAVE NAMED RUN 24'S FAULT IN ONE RUN.
    ok_compression = compression_field(
        [("BaseColorMap", "DEFAULT", "enum-identity", True),
         ("NormalMap", "NORMALMAP", "enum-identity", False),
         ("RoughnessMap", "DEFAULT", "enum-int", False)])
    run24_compression = compression_field(
        [("NormalMap", None, "unrecognised", False)])
    checks += 1
    if "materialCompressionReadback=BaseColorMap.DEFAULT.via.enum-identity.srgb.yes/NormalMap.NORMALMAP.via.enum-identity.srgb.no/RoughnessMap.DEFAULT.via.enum-int.srgb.no" not in ok_compression or \
            "materialCompressionReadback=NormalMap.UNRECOGNISED.via.unrecognised.srgb.no" not in run24_compression or \
            "materialCompressionReadback=nothing-measured" not in compression_field([]):
        bad.append("the compression readback key does not carry the leaf, the "
                   "route and the sRGB flag, or a run that read nothing does "
                   "not say nothing-measured: %s / %s / %s"
                   % (ok_compression, run24_compression, compression_field([])))
    checks += 1
    if [t for t in (ok_compression + " " + run24_compression
                    + " " + compression_field([])).split()
            if t.count("=") != 1]:
        bad.append("a compression readback token is not one key=value: %s"
                   % ok_compression)
    # ---- AMENDMENT A2: TWO SITUATIONS, TWO WORDS -------------------------
    # A value the engine answered that has no compression leaf in it, and a
    # property that never answered at all, used to print the same label. They
    # have different next actions: the first is a spelling this file cannot
    # parse (and the report file carries its str and repr), the second is a
    # texture that is not there.
    for leaf, via, want in (("NORMALMAP", "enum-identity", "NORMALMAP"),
                            ("DEFAULT", "string-parse", "DEFAULT"),
                            (None, "unrecognised", "UNRECOGNISED"),
                            (None, "srgb-refused", "UNRECOGNISED"),
                            (None, "readback-refused", "none"),
                            (None, "nothing-measured", "none")):
        checks += 1
        got = compression_word(leaf, via)
        if got != want:
            bad.append("compression_word(%s, %s) gave %s and should give %s"
                       % (leaf, via, got, want))
    checks += 1
    silent_compression = compression_field(
        [("NormalMap", None, "nothing-measured", False),
         ("RoughnessMap", None, "readback-refused", False)])
    if "NormalMap.none.via.nothing-measured" not in silent_compression or \
            "RoughnessMap.none.via.readback-refused" not in silent_compression \
            or "UNRECOGNISED" in silent_compression:
        bad.append("a texture that never answered is being called "
                   "UNRECOGNISED, which sends the next reader to the parser "
                   "over a texture that was not there: %s"
                   % silent_compression)
    # AND THE SAME SPLIT ON THE DEFAULTS LINE. A texture that is present and
    # derives a type the slot disagrees with is TYPE-MISMATCH; a texture that
    # derived NO type at all is TYPE-UNKNOWN. Neither is bound.
    unknown_vias = [
        (TEXTURE_PARAMS[0], "engine", SAMPLER_COLOR, SAMPLER_COLOR),
        (TEXTURE_PARAMS[1], "generated", None, SAMPLER_NORMAL),
        (TEXTURE_PARAMS[2], "engine", SAMPLER_COLOR, SAMPLER_LINEAR_COLOR),
    ]
    u_bound, u_asked, u_detail = defaults_field(unknown_vias)
    checks += 1
    if (u_bound, u_asked) != (1, 3) or \
            "NormalMap.generated.TYPE-UNKNOWN" not in u_detail or \
            "RoughnessMap.engine.TYPE-MISMATCH" not in u_detail:
        bad.append("a sampler whose texture derived nothing and a sampler "
                   "whose texture derived the wrong type are still one label, "
                   "or one of them counted as bound: %d/%d %s"
                   % (u_bound, u_asked, u_detail))
    # AND A DERIVED TYPE OF NONE NEVER COUNTS AS A MATCH, whatever was asked
    # for, because a type nobody derived is not a type that agreed.
    checks += 1
    if defaults_field([(TEXTURE_PARAMS[0], "generated", None, None)])[0] != 0:
        bad.append("two unknowns are being read as an agreement, so a "
                   "sampler nothing could be derived for counts as bound")
    # AND THE ONE THAT MATTERS: the engine colour default in the roughness
    # slot is a MISMATCH, which is the second compile error nothing named.
    checks += 1
    if derived_sampler_type("TC_DEFAULT", True) == SAMPLER_LINEAR_COLOR or \
            derived_sampler_type("TC_DEFAULT", True) == SAMPLER_LINEAR_GRAYSCALE:
        bad.append("an sRGB colour texture is being accepted into a linear "
                   "slot, which is exactly the mismatch run 23 shipped")
    # EVERY GENERATED DEFAULT MUST DERIVE THE TYPE ITS SAMPLER IS DECLARED
    # WITH, or this script's own fallback is a compile error too. Checked
    # against MAP_SAMPLER_TYPES rather than against the tuple's own last
    # field, so the two lists cannot drift apart in silence.
    checks += 1
    if len(GENERATED_DEFAULTS) != len(TEXTURE_PARAMS) or \
            len(MAP_SAMPLER_TYPES) != len(TEXTURE_PARAMS):
        bad.append("there is not one generated default and one declared "
                   "sampler type per texture parameter: %d/%d/%d"
                   % (len(GENERATED_DEFAULTS), len(MAP_SAMPLER_TYPES),
                      len(TEXTURE_PARAMS)))
    else:
        for I, spec in enumerate(GENERATED_DEFAULTS):
            checks += 1
            name, rgb, srgb, compression, want = spec
            got = derived_sampler_type(compression, srgb)
            if got != want or want != MAP_SAMPLER_TYPES[I]:
                bad.append("the generated default %s derives %s, claims %s "
                           "and the sampler is declared %s: three that must "
                           "be one" % (name, got, want, MAP_SAMPLER_TYPES[I]))
    # ---- THE TEXTURE THIS SCRIPT WRITES, DECODED BACK --------------------
    # ACCEPTING CASE FIRST, and it is the flat normal, because that is the
    # one the whole fix turns on: every texel (128,128,255), full alpha, in a
    # header the engine's importer will recognise.
    for name, rgb, srgb, compression, want in GENERATED_DEFAULTS:
        raw = tga_bytes(GENERATED_SIZE, GENERATED_SIZE, rgb)
        got = tga_read(raw)
        checks += 1
        if got is None:
            bad.append("the TGA written for %s does not read back as an "
                       "uncompressed 32-bit true-colour TGA at all" % name)
            continue
        w, h, bits, desc, texels = got
        wrong = [t for t in texels if t != (rgb[0], rgb[1], rgb[2], 255)]
        if (w, h, bits) != (GENERATED_SIZE, GENERATED_SIZE, 32) or \
                len(texels) != GENERATED_SIZE * GENERATED_SIZE or wrong:
            bad.append("the TGA written for %s is %dx%d at %d bits with %d "
                       "texel(s) of %d not the colour asked for %s"
                       % (name, w, h, bits, len(wrong), len(texels), rgb))
        checks += 1
        if desc != 0x28:
            bad.append("the TGA image descriptor for %s is 0x%02x and not the "
                       "0x28 that declares eight alpha bits and a top-left "
                       "origin" % (name, desc))
    # REJECTING: bytes that are not this format are refused rather than
    # half-read, both ways a caller could get it wrong.
    checks += 1
    if tga_read(None) is not None or tga_read(b"") is not None or \
            tga_read(b"\x00" * 40) is not None or \
            tga_read(tga_bytes(4, 4, (1, 2, 3))[:-4]) is not None:
        bad.append("tga_read accepted something that is not the TGA "
                   "tga_bytes writes")
    # ---- THE COMPILE CHANNELS, AND THE RUN 23 CASE THEY EXIST FOR --------
    # THE FIXTURE IS REAL UNREAL LOG TEXT, not a paraphrase, because the
    # whole risk in this scanner is matching a shape the engine does not
    # print. These two lines are the shapes Unreal logs when a texture sample
    # has no texture and when a sampler type disagrees with its texture.
    engine_log = [
        "LogInit: Display: Starting Game.",
        "LEDGER-MATERIAL-COMPILE-BEGIN",
        "LogMaterial: Warning: [AssetLog] M_LedgerSurface.uasset: Failed to "
        "compile Material /Game/Ledger/M_LedgerSurface.M_LedgerSurface for "
        "platform PCD3D_SM6, Default Material will be used in game.",
        "LogMaterial: Warning:   (Node TextureSampleParameter2D) "
        "TextureSampleParameter2D> Missing input texture",
        "LogMaterial: Warning:   (Node TextureSampleParameter2D) Sampler type "
        "is Linear Grayscale, should be Color.",
        "LEDGER-MATERIAL-COMPILE-END",
        "LogExit: Preparing to exit.",
    ]
    sliced, saw_begin, saw_end = log_slice(engine_log)
    checks += 1
    if len(sliced) != 3 or not saw_begin or not saw_end:
        bad.append("the log slice between the two markers is %d line(s) and "
                   "should be the three diagnostics: %s" % (len(sliced), sliced))
    errs, examined, matched = compile_scan(sliced)
    checks += 1
    if (errs, examined) != (3, 3) or len(matched) != 3:
        bad.append("the three diagnostics Unreal prints for a material that "
                   "did not compile were counted as %s of %s" % (errs, examined))
    # ACCEPTING CASE: a slice with nothing wrong in it counts zero AND ships
    # the number of lines it looked at, so a clean compile cannot be confused
    # with a log nobody opened.
    clean = ["LogShaderCompilers: Display: Compiling 6 shaders",
             "LogMaterial: Display: Material /Game/Ledger/M_LedgerSurface "
             "cached 6 shader(s)",
             "LogTexture: Display: Building textures: T_LedgerDefaultNormal"]
    checks += 1
    errs2, examined2, matched2 = compile_scan(clean)
    if (errs2, examined2, matched2) != (0, 3, []):
        bad.append("a clean compile slice does not read zero over three: "
                   "%s/%s %s" % (errs2, examined2, matched2))
    checks += 1
    if compile_scan(None) != (None, 0, []):
        bad.append("a log that could not be read is being reported as zero "
                   "errors: %s" % (compile_scan(None),))
    # A LOG WITH NO BEGIN MARKER IS SCANNED WHOLE AND SAYS SO, because a
    # silently empty slice would print a clean zero over a failed compile.
    checks += 1
    whole, saw_b, saw_e = log_slice(["LogInit: Display: x", "LogInit: y"])
    if len(whole) != 2 or saw_b or saw_e:
        bad.append("a log with no markers in it did not fall back to the "
                   "whole log or did not say the markers were missing: "
                   "%d %s %s" % (len(whole), saw_b, saw_e))
    # AND THIS SCRIPT'S OWN LINES NEVER COUNT AS DIAGNOSTICS, whatever they
    # say. The verdict line carries the asset path and the word material and
    # would otherwise match the net underneath the named phrases.
    checks += 1
    if is_compile_diagnostic("LEDGER materialStatus=NOT-COMPILED "
                             "materialNote=recompile-threw") or \
            is_compile_diagnostic(COMPILE_MARK_BEGIN):
        bad.append("this script's own output is being counted as an engine "
                   "compile diagnostic")
    # THE VERDICT FUNCTION, EVERY COMBINATION THAT DECIDES A WORD.
    # Each row is (errors, LOG LINES EXAMINED, pixel instructions, begin
    # marker seen, end marker seen, the word). ACCEPTING CASE FIRST: a
    # located slice that was read, is clean, and has a shader behind it.
    # Each row is (errors, lines examined, pixel instructions, begin, end,
    # CONTROL pixel instructions, the word). The control column was added
    # after run 24 and it is the only thing that separates a material with no
    # shader from an instrument that cannot say.
    compile_cases = [
        (0, 187, 42, True, True, None, COMPILE_OK),
        # A ZERO WITH NO DENOMINATOR IS NOT A CLEAN COMPILE. An empty slice
        # makes compile_scan return (0, 0, []), which read OK until today
        # and printed materialCompileErrors=0/0 beside the word.
        (0, 0, 42, True, True, None, COMPILE_UNPROVEN),
        # AND NEITHER IS A PASS OVER A SLICE NOBODY LOCATED: log_slice falls
        # back to the whole log when the begin marker is missing.
        (0, 40, 42, False, True, None, COMPILE_UNPROVEN),
        (0, 40, 42, True, False, None, COMPILE_UNPROVEN),
        # ERRORS STAYS REACHABLE WITHOUT THE MARKERS, because a log that
        # failed to slice can still carry a real diagnostic and that is
        # exactly the run you want to hear about.
        (3, 40, 42, False, False, None, COMPILE_ERRORS),
        # RUN 24 EXACTLY, AND IT IS TWO DIFFERENT WORDS DEPENDING ON ONE
        # NUMBER NOBODY MEASURED. A clean log and pixel.0 with no control is
        # UNPROVEN, because an instrument that has only ever printed zero has
        # not been shown to print anything else. The same zero beside a
        # control of 187 is NO-SHADER: the channel answers, and it answered
        # that this material has no compiled shader.
        (0, 1200, 0, True, True, None, COMPILE_UNPROVEN),
        (0, 1200, 0, True, True, 0, COMPILE_UNPROVEN),
        (0, 1200, 0, True, True, 187, COMPILE_NO_SHADER),
        (0, 0, 0, False, False, 187, COMPILE_NO_SHADER),
        # AND A DIAGNOSTIC STILL OUTRANKS IT, because a named error is worth
        # more than a count: it says WHY.
        (2, 1200, 0, True, True, 187, COMPILE_ERRORS),
        # A shader that exists is never NO-SHADER whatever the control says.
        (0, 1200, 187, True, True, 187, COMPILE_OK),
        (0, 1200, 187, True, True, 0, COMPILE_OK),
        # THE STATISTICS REFUSING TO ANSWER IS NOT A ZERO and is never
        # NO-SHADER, control or no control.
        (0, 1200, None, True, True, None, COMPILE_UNPROVEN),
        (0, 1200, None, True, True, 187, COMPILE_UNPROVEN),
        (None, 0, 187, True, True, None, COMPILE_UNPROVEN),   # no log read
        (None, 0, None, False, False, None, COMPILE_UNPROVEN),  # run 23
        (3, 1200, 187, True, True, None, COMPILE_ERRORS),
        (1, 1200, None, True, True, None, COMPILE_ERRORS),
    ]
    for errs3, exam3, instr, mark_b, mark_e, ctl3, want in compile_cases:
        checks += 1
        got = compile_verdict(errs3, exam3, instr, mark_b, mark_e, ctl3)
        if got != want:
            bad.append("compile_verdict(errors=%s examined=%s instructions=%s "
                       "markers=begin.%s/end.%s control=%s) gave %s and "
                       "should give %s"
                       % (errs3, exam3, instr, mark_b, mark_e, ctl3, got, want))
    # AND THE WORD REACHES THE STATUS: a proven-absent shader is NOT-COMPILED
    # and never COMPILE-UNPROVEN, which is the whole point of the fourth word.
    checks += 1
    if material_status(True, 3, 3, 14, 14, 0, 3, 3,
                       COMPILE_NO_SHADER) != STATUS_NOT_COMPILED or \
            material_return(STATUS_NOT_COMPILED) != 2:
        bad.append("a material the editor answered zero instructions for, "
                   "through a channel with an accepting case, is not reported "
                   "as NOT-COMPILED with a return of 2")
    # THE COMMITTED DIAGNOSTICS FILE, INCLUDING ITS CAP BITING.
    checks += 1
    text = compile_log_text(ASSET_PATH, 3, 3, matched, keep=2)
    if "3 matched line(s) of 3 log line(s) examined" not in text or \
            "(+1 more matching line(s) not shown)" not in text:
        bad.append("the diagnostics file does not carry the count with its "
                   "denominator or its cap does not announce itself: %s" % text)
    checks += 1
    text = compile_log_text(ASSET_PATH, None, 0, [])
    if "NOTHING MEASURED" not in text:
        bad.append("a run that read no log does not say NOTHING MEASURED in "
                   "the file it commits: %s" % text)
    # ---- THE FOURTH AND FIFTH LINES ON THE WIRE --------------------------
    # A material the editor reported diagnostics for, which is the state run
    # 23 was in and could not print. Its formatter must not ship unrun either.
    fail_line = material_line(STATUS_NOT_COMPILED, 3, 3, 14, 14, True,
                              default_via("engine",
                                          "/Engine/EngineResources/DefaultTexture",
                                          SAMPLER_COLOR, SAMPLER_COLOR),
                              default_via("none", "none-of-2-candidates",
                                          None, SAMPLER_NORMAL),
                              default_via("engine",
                                          "/Engine/EngineResources/DefaultTexture",
                                          SAMPLER_COLOR, SAMPLER_LINEAR_COLOR),
                              run23_bound, run23_asked, run23_detail,
                              errors_block,
                              generated_field(["engine", "none", "engine"], 1),
                              True, [],
                              *(uv_head_fields(good_heads, ncand)
                                + (property_write_heads(good_heads)[2],)))
    checks += 1
    if [t for t in fail_line.split() if t.count("=") != 1]:
        bad.append("the not-compiled line has a token that is not one "
                   "key=value: %s"
                   % [t for t in fail_line.split() if t.count("=") != 1])
    checks += 1
    if "materialStatus=NOT-COMPILED" not in fail_line or \
            "materialScriptReturn=2" not in fail_line or \
            "materialCompile=ERRORS" not in fail_line or \
            "materialCompileErrors=2/1200" not in fail_line or \
            "materialDefaultsBound=1/3" not in fail_line:
        bad.append("the not-compiled line does not carry the word, the "
                   "return, the diagnostic count with its denominator and "
                   "the defaults that explain it: %s" % fail_line)
    print("    %s" % line)
    print("    %s" % good_line)
    print("    %s" % prop_line)
    print("    %s" % fail_line)
    print("make_base_material --selftest: %d check(s), %d failure(s), "
          "params=%s scalars=%s header=%s"
          % (checks, len(bad), "/".join(TEXTURE_PARAMS), "/".join(SCALAR_PARAMS),
             os.path.relpath(header, root)))
    for b in bad:
        print("  FAIL %s" % b)
    return 0 if not bad else 2


def _reads_back(dst, src):
    """Read the graph back rather than trusting the editor's boolean.

    Returns True when the destination's input holds the source expression,
    False when it holds something else or nothing, and None when the editor
    will not answer at all (the input struct is not exposed to Python in this
    version). None is not no, and the verdict line carries the two apart.
    """
    try:
        got = dst.get_editor_property("input")
        if got is None:
            return False
        linked = got.get_editor_property("expression")
        return linked is not None and linked == src
    except Exception:
        return None


def _write_input_property(src, dst):
    """LAST RESORT, AND NAMED AS ONE ON THE VERDICT LINE. If no pin name is
    accepted, write the input struct directly and let the readback say whether
    it took. Still a script and still a build product: the D1 rule is that no
    human opens the editor, not that only one API may be used.

    Returns True only when the graph READS BACK connected, False when the
    write was refused or cannot be confirmed, and None when the property is
    not exposed at all. Confirmation is required because a struct written by
    value that the editor quietly discards would otherwise be counted as a
    connection and print MADE over an unwired material, which is the exact
    class of failure the 3 September rule exists to stop.
    """
    try:
        val = dst.get_editor_property("input")
    except Exception:
        return None
    if val is None:
        return None
    try:
        val.set_editor_property("expression", src)
        val.set_editor_property("output_index", 0)
        dst.set_editor_property("input", val)
    except Exception:
        return False
    return _reads_back(dst, src) is True


def _first_that_loads(unreal, paths, report=None):
    """The first candidate path that is IN THE ASSET REGISTRY and loads.

    THE REGISTRY CHECK IS NOT AN OPTIMISATION. EditorAssetLibrary.load_asset
    on a path that does not exist logs LogEditorAssetSubsystem: Error, and two
    of those are the entire content of the "Failure - 2 error(s)" summary that
    has been materialEditorCmdExit=1 since run 20. does_asset_exist asks the
    registry and says nothing when the answer is no, so a candidate list can
    be probed without spending the only whole-process health signal this step
    has. Every candidate looked at is reported, so a zero says where it looked.
    """
    if not paths:
        return None, "no-engine-candidate-by-decision"
    for p in paths:
        try:
            if not unreal.EditorAssetLibrary.does_asset_exist(p):
                if report is not None:
                    report.append("# candidate %s is not in this engine's "
                                  "asset registry, so it was never loaded" % p)
                continue
            a = unreal.EditorAssetLibrary.load_asset(p)
            if a is not None:
                return a, p
        except Exception:
            continue
    return None, "none-of-%d-candidates" % len(paths)


def _live_compression_leaves(unreal):
    """Every compression leaf THIS ENGINE has, compact leaf name to enum
    member, read off the live enum rather than out of this file's memory.

    An empty dict means the enum could not be enumerated at all, and the
    caller falls back to the parse and to KNOWN_COMPRESSION_LEAVES.
    """
    out = {}
    try:
        enum = unreal.TextureCompressionSettings
    except Exception:
        return out
    for attr in sorted(dir(enum)):
        if not attr.startswith("TC_"):
            continue
        leaf = compression_leaf(attr)
        if leaf is None:
            continue
        try:
            out[leaf] = getattr(enum, attr)
        except Exception:
            continue
    return out


def _compression_reading(unreal, tex):
    """What a texture answers for its compression settings, and how it was
    read. Returns (leaf, via, str spelling, repr spelling).

    THIS IS THE FIX FOR RUN 24 AND THE ORDER IS THE FIX. The old code read
    this property and IMMEDIATELY split its string on ".", which is a guess
    about how this engine version spells an enum, and the guess was wrong: a
    texture the importer had itself auto-detected as a normal map, and that
    this script then set TC_NORMALMAP on, came back deriving LINEAR_COLOR.
    So the value is compared against the LIVE enum members first, by identity
    and then by integer value, and only after both of those fail is any string
    parsed. Identity cannot be wrong about spelling because it never reads the
    spelling. Both spellings go into the committed evidence either way, so the
    next reader knows what this engine actually answers instead of inferring
    it from a derived type.
    """
    if tex is None:
        return None, "nothing-measured", "none", "none"
    try:
        raw = tex.get_editor_property("compression_settings")
    except Exception:
        return None, "readback-refused", "none", "none"
    try:
        as_str = str(raw)
    except Exception:
        as_str = "unprintable"
    try:
        as_repr = repr(raw)
    except Exception:
        as_repr = "unprintable"
    members = _live_compression_leaves(unreal)
    for leaf in sorted(members):
        try:
            if members[leaf] == raw:
                return leaf, "enum-identity", as_str, as_repr
        except Exception:
            continue
    try:
        as_int = int(raw)
    except Exception:
        as_int = None
    if as_int is not None:
        for leaf in sorted(members):
            try:
                if int(members[leaf]) == as_int:
                    return leaf, "enum-int", as_str, as_repr
            except Exception:
                continue
    parsed = compression_leaf(raw)
    if parsed is not None and (not members or parsed in members):
        return parsed, "string-parse", as_str, as_repr
    return None, "unrecognised", as_str, as_repr


def _texture_reading(unreal, tex, report=None, label=""):
    """Everything this script knows about one texture's type, in one call.

    Returns (derived sampler type, leaf, via, srgb). The type comes from
    derived_sampler_type, which is the half of this --selftest runs, fed the
    leaf that the LIVE enum resolved and the live enum's own leaf set, so a
    compression setting this file has never heard of is still the engine's
    default case rather than a refusal. A texture that will not answer derives
    nothing, and nothing never matches an asked type, so it is refused rather
    than assigned on the strength of its path.
    """
    if tex is None:
        return None, None, "nothing-measured", False
    leaf, via, as_str, as_repr = _compression_reading(unreal, tex)
    try:
        srgb = bool(tex.get_editor_property("srgb"))
    except Exception:
        if report is not None:
            report.append("# %s would not answer for srgb" % (label or "texture"))
        return None, leaf, "srgb-refused", False
    if report is not None:
        report.append("# compression_settings readback for %s: leaf=%s via=%s "
                      "srgb=%s str=%s repr=%s"
                      % (label or "texture", leaf, via, srgb, as_str, as_repr))
    known = _live_compression_leaves(unreal)
    return (derived_sampler_type(leaf, srgb,
                                 set(known) if known else None),
            leaf, via, srgb)


def _sampler_enum(unreal, name):
    """This file's sampler-type spelling, as the editor's enum value.

    Both spellings are tried in both directions: DISTANCEFIELDFONT is
    SAMPLERTYPE_DISTANCE_FIELD_FONT in the Python enum, and a name this
    function cannot resolve leaves the expression on its default type, which
    is a compile error waiting for the first texture that needs it.
    """
    st = unreal.MaterialSamplerType
    compact = name.replace("_", "")
    for attr in ("SAMPLERTYPE_" + name,
                 "SAMPLERTYPE_" + compact,
                 "SAMPLERTYPE_" + name.upper(),
                 "SAMPLERTYPE_" + compact.upper()):
        got = getattr(st, attr, None)
        if got is not None:
            return got
    for attr in sorted(dir(st)):
        if not attr.startswith("SAMPLERTYPE_"):
            continue
        if attr[len("SAMPLERTYPE_"):].replace("_", "").upper() == compact.upper():
            return getattr(st, attr, None)
    return None


def _generate_default_texture(unreal, spec, notes, report=None):
    """Make one default texture as an asset THIS SCRIPT OWNS.

    The engine cannot be asked for a texture's texels from Python, so the
    texels are written to a file by tga_bytes, which --selftest decodes back
    in the container, and the editor's own importer brings the file in. The
    compression settings and the sRGB flag are then set and READ BACK, and
    the type the result derives is returned with it: an import that silently
    kept its own settings must not be reported as a default of the type the
    sampler asked for, which is the whole fault this fallback exists to end.

    Returns (texture, path, derived type, reading), where reading is the
    (leaf, via, srgb) the texture answered with. The texture is None when any
    step refused, and every refusal appends a named note rather than being
    caught and forgotten.

    RUN 24 IMPORTED BOTH OF THESE AND STILL FAILED, and the readback below is
    why that was diagnosable at all. The importer had ALREADY auto-detected
    the normal map by itself, this script set TC_NORMALMAP on top of it, and
    the type still came back LINEAR_COLOR. The texture was never the problem;
    the reading was. The reading now goes out with the leaf and the route that
    read it, so the two can never be confused again.
    """
    name, rgb, srgb, compression, want = spec
    path = PACKAGE + "/" + name
    try:
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            unreal.EditorAssetLibrary.delete_asset(path)
    except Exception:
        pass
    try:
        root = unreal.Paths.project_saved_dir()
    except Exception:
        root = "."
    folder = os.path.join(root, "LedgerGenerated")
    try:
        if not os.path.isdir(folder):
            os.makedirs(folder)
        src = os.path.join(folder, name + ".tga")
        with open(src, "wb") as f:
            f.write(tga_bytes(GENERATED_SIZE, GENERATED_SIZE, rgb))
    except Exception:
        notes.append("%s-tga-write-refused" % name)
        return None, "tga-write-refused", None, (None, "nothing-measured", srgb)
    try:
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", src)
        task.set_editor_property("destination_path", PACKAGE)
        task.set_editor_property("destination_name", name)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", True)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    except Exception:
        notes.append("%s-import-refused" % name)
        return None, "import-refused", None, (None, "nothing-measured", srgb)
    tex = None
    try:
        tex = unreal.EditorAssetLibrary.load_asset(path)
    except Exception:
        tex = None
    if tex is None:
        notes.append("%s-imported-nothing" % name)
        return None, "imported-nothing", None, (None, "nothing-measured", srgb)
    # THE SETTINGS ARE WHAT MAKES THIS A DEFAULT AND NOT JUST A PICTURE. The
    # sRGB flag goes first: some compression settings drive it, and the last
    # write is the one the readback below has to agree with.
    for prop, value in (("srgb", srgb),
                        ("compression_settings",
                         getattr(unreal.TextureCompressionSettings,
                                 compression, None)),
                        ("mip_gen_settings",
                         getattr(unreal.TextureMipGenSettings,
                                 "TMGS_NO_MIPMAPS", None))):
        if value is None:
            notes.append("%s-%s-not-available" % (name, prop))
            continue
        try:
            tex.set_editor_property(prop, value)
        except Exception:
            notes.append("%s-%s-refused" % (name, prop))
    try:
        tex.set_editor_property("srgb", srgb)
    except Exception:
        pass
    try:
        unreal.EditorAssetLibrary.save_asset(path)
    except Exception:
        notes.append("%s-save-refused" % name)
    got, leaf, via, read_srgb = _texture_reading(unreal, tex, report, name)
    if got != want:
        notes.append("%s-derives-%s-not-%s-leaf-%s-via-%s"
                     % (name, got, want, leaf, via))
    return tex, path, got, (leaf, via, read_srgb)


def _resolve_default(unreal, index, candidates, notes, made_counter,
                     report=None):
    """One sampler's default texture, engine path first and generated second.

    A candidate which loads is CHECKED: the type it derives has to be the type
    the sampler is declared with, and an engine texture of the wrong type is
    refused and falls through, because assigning it is a compile error and a
    compile error is what this whole batch is about.

    AN EMPTY CANDIDATE LIST IS A DECISION AND SAYS SO. Two of the three lists
    are empty as of 2026-09-06 and the reason is beside each one: the normal
    candidates do not exist in UE 5.8 and cost an error line each, and the
    roughness ones resolve to an sRGB texture that this sampler can never
    accept. The generated default owns those two slots.

    Returns (texture, source, path, derived type, asked type, reading), where
    reading is the (leaf, via, srgb) the chosen texture answered with.
    """
    asked = MAP_SAMPLER_TYPES[index]
    tex, path = _first_that_loads(unreal, candidates, report)
    if tex is not None:
        got, leaf, via, srgb = _texture_reading(
            unreal, tex, report, TEXTURE_PARAMS[index])
        if got == asked:
            return tex, "engine", path, got, asked, (leaf, via, srgb)
        notes.append("%s-engine-default-derives-%s-not-%s"
                     % (TEXTURE_PARAMS[index], got, asked))
    made_counter.append(index)
    tex, gen_path, got, reading = _generate_default_texture(
        unreal, GENERATED_DEFAULTS[index], notes, report)
    if tex is None:
        return None, "none", gen_path, None, asked, reading
    return tex, "generated", gen_path, got, asked, reading


def _read_editor_log(unreal, report):
    """The editor's own log file, as lines, or None when none could be read.

    None is not an empty log and the caller prints the two apart. Every
    candidate looked at is written into report, so a run that read nothing
    says WHERE it looked rather than leaving a silent zero.
    """
    try:
        flush = getattr(unreal, "log_flush", None)
        if flush is not None:
            flush()
    except Exception:
        report.append("# unreal.log_flush refused")
    try:
        log_dir = unreal.Paths.project_log_dir()
    except Exception:
        report.append("# unreal.Paths.project_log_dir refused")
        return None
    try:
        names = [n for n in os.listdir(log_dir) if n.lower().endswith(".log")]
    except Exception:
        report.append("# no readable log directory at %s" % log_dir)
        return None
    report.append("# editor log directory %s holds %d .log file(s): %s"
                  % (log_dir, len(names), "/".join(sorted(names)[:8])
                     + ("(+%d more not shown)" % (len(names) - 8)
                        if len(names) > 8 else "")))
    if not names:
        return None
    full = [os.path.join(log_dir, n) for n in names]
    full.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    try:
        with open(full[0], "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except Exception:
        report.append("# %s would not open" % full[0])
        return None
    report.append("# read %d line(s) from %s" % (len(lines), full[0]))
    return lines


def _material_statistics(unreal, mel, mat, report, label="this material"):
    """The editor's own shader statistics for one material.

    Returns (pixel instructions, vertex instructions, samplers), each None
    when the API would not answer. None is the honest value: a zero would
    read as a material with no shader, which is a completely different fact
    and is the one this run exists to detect. A zero it DID answer is
    returned as a zero and judged by compile_verdict against the control.

    Whatever the statistics object turns out to be is written into report by
    NAME, capped and announced, so that a property spelling this file guessed
    wrong is diagnosable from the committed evidence instead of costing
    another round trip. Run 24 is the reason: the guess was right, the log
    proved it was right, and that is now this project's positive evidence
    that the channel exists at all.
    """
    getter = getattr(mel, "get_statistics", None)
    if getter is None:
        report.append("# MaterialEditingLibrary has no get_statistics in this "
                      "engine version, so the positive compile channel is "
                      "silent and the status can only be COMPILE-UNPROVEN")
        return None, None, None
    try:
        stats = getter(mat)
    except Exception as e:
        report.append("# get_statistics raised for %s: %s" % (label, str(e)[:200]))
        return None, None, None
    fields = [n for n in dir(stats) if not n.startswith("_")]
    report.append("# get_statistics for %s answered a %s exposing %d name(s): %s"
                  % (label, type(stats).__name__, len(fields),
                     "/".join(fields[:24])
                     + ("(+%d more not shown)" % (len(fields) - 24)
                        if len(fields) > 24 else "")))
    def read(*names):
        for n in names:
            try:
                return int(stats.get_editor_property(n))
            except Exception:
                continue
        for n in names:
            got = getattr(stats, n, None)
            if isinstance(got, int):
                return got
        return None
    got = (read("num_pixel_shader_instructions", "num_pixel_instructions"),
           read("num_vertex_shader_instructions", "num_vertex_instructions"),
           read("num_samplers", "num_texture_samples",
                "num_pixel_texture_samples"))
    report.append("# statistics for %s: pixel=%s vertex=%s samplers=%s"
                  % (label, got[0], got[1], got[2]))
    return got


def _statistics_twin(unreal, tools, mel, report):
    """THE ACCEPTING CASE FOR THE STATISTICS CHANNEL, and it is a TWIN rather
    than a stranger.

    A material THIS SCRIPT creates, wires trivially, recompiles by the same
    call and reads through the same call, in the same process, outside our own
    compile markers so its diagnostics can never be counted as ours. NEVER
    SAVED, so no cook and no .uasset can carry it, and deleted after the
    reading either way.

    WHY A TWIN AND NOT AN ENGINE MATERIAL. An engine material carries whatever
    shader map the derived-data cache holds for it, so a number from one
    proves get_statistics returns a number WHEN A MAP IS ALREADY PRESENT. Our
    material is recompiled a fraction of a second before the read with no
    engine tick in between; if this commandlet compiles material shaders
    asynchronously, our map is not there at read time however good the graph
    is, and pixel.0 beside a cached 187 would print NO-SHADER over a material
    the cook then compiles perfectly well. The twin is the only control that
    asks the same question our zero is an answer to.

    EVERY STEP IS GUARDED AND FAILS CLOSED. A step that refuses names itself
    in the returned from. value and the control is None, which makes the
    verdict UNPROVEN: a twin that could not be made is never evidence that
    ours has no shader.

    Returns (pixel, vertex, the twin's path or the named step that refused).
    """
    path = CONTROL_TWIN_PATH

    def finish(px_, vx_, from_):
        """Delete the twin, whatever happened, and report what the delete did.

        The delete is only ASKED FOR when the registry says the asset is
        there, for the reason in _first_that_loads: a miss writes an error
        into the editor's own Warning/Error summary and that summary is the
        process exit code.
        """
        try:
            there = bool(unreal.EditorAssetLibrary.does_asset_exist(path))
        except Exception as e:
            report.append("# the twin's existence check raised before the "
                          "delete: %s" % str(e)[:160])
            there = False
        deleted = "not-asked"
        if there:
            try:
                deleted = str(bool(unreal.EditorAssetLibrary.delete_asset(path)))
            except Exception as e:
                report.append("# deleting the twin raised: %s" % str(e)[:160])
                deleted = "raised"
        try:
            still = str(bool(unreal.EditorAssetLibrary.does_asset_exist(path)))
        except Exception:
            still = "unknown"
        report.append("# twin %s: never saved, in-registry-before-delete=%s, "
                      "delete_asset returned %s, does_asset_exist afterwards "
                      "is %s. It is never saved, so nothing on disk carries "
                      "it whatever the delete did."
                      % (path, there, deleted, still))
        return px_, vx_, from_

    # A LEFTOVER FIRST, the same pattern the material itself uses. Nothing
    # should ever have left one behind, since the twin is never saved, so a
    # leftover is itself worth a line in the report.
    try:
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            report.append("# a twin was already in the registry before this "
                          "run made one, which should be impossible for an "
                          "asset that is never saved: deleting it first")
            unreal.EditorAssetLibrary.delete_asset(path)
    except Exception as e:
        report.append("# the leftover-twin check raised: %s" % str(e)[:160])

    try:
        twin = tools.create_asset(CONTROL_TWIN, PACKAGE, unreal.Material,
                                  unreal.MaterialFactoryNew())
    except Exception as e:
        report.append("# creating the twin raised: %s" % str(e)[:160])
        return finish(None, None, "twin-create-threw")
    if twin is None:
        report.append("# creating the twin returned nothing")
        return finish(None, None, "twin-create-returned-nothing")

    node = None
    for name in TWIN_EXPRESSION_CLASSES:
        cls = getattr(unreal, name, None)
        if cls is None:
            continue
        try:
            node = mel.create_material_expression(twin, cls, -300, 0)
        except Exception as e:
            report.append("# the twin's %s expression raised: %s"
                          % (name, str(e)[:120]))
            node = None
            continue
        if node is not None:
            report.append("# the twin's one wire is a %s" % name)
            break
    if node is None:
        report.append("# none of the %d expression classes made a node for "
                      "the twin" % len(TWIN_EXPRESSION_CLASSES))
        return finish(None, None, "twin-expression-refused")

    try:
        wired = bool(mel.connect_material_property(
            node, "", unreal.MaterialProperty.MP_BASE_COLOR))
    except Exception as e:
        report.append("# wiring the twin raised: %s" % str(e)[:160])
        wired = False
    if not wired:
        report.append("# the twin's one connection was refused, so it is not "
                      "a material anything could be concluded from")
        return finish(None, None, "twin-connect-refused")

    try:
        mel.recompile_material(twin)
    except Exception as e:
        report.append("# recompiling the twin raised: %s" % str(e)[:160])
        return finish(None, None, "twin-recompile-threw")

    px, vx, _samplers = _material_statistics(unreal, mel, twin, report,
                                             "twin " + path)
    if px is None:
        return finish(None, None, "twin-statistics-refused")
    return finish(px, vx, path)


def _statistics_channel(unreal, mel, report):
    """THE NON-GATING READING: the same statistics call on ENGINE materials,
    which says whether the call returns a number for anything in this editor.

    It is NOT the accepting case for our own zero, because these materials
    answer out of the derived-data cache and were not compiled in this
    process. That is what the twin above is for. This is still worth knowing:
    with the twin at zero, a number here says the call works and the compile
    is what did not happen, and a zero here says the channel is dead in this
    process. Two different first suspects.

    ALL the candidates are asked and the FIRST NON-ZERO is kept. The old code
    returned on the first that answered AT ALL, including a zero, so one
    candidate answering zero ended the search and a later one that would have
    answered 187 was never asked: a dead-channel reading could print over a
    live channel, with no count of how many were tried beside it.

    Candidates are registry-checked before they are loaded, for the reason in
    _first_that_loads: a LoadAsset miss writes an error into the editor's own
    Warning/Error summary and that summary is the process exit code.

    Returns (pixel, vertex, path or a named absence, answered, asked), where
    ANSWERED is how many candidates returned a number, including a zero, and
    ASKED is how many candidates the list has.
    """
    asked = 0
    answered = 0
    first_nonzero = None
    first_answer = None
    for path in CONTROL_MATERIALS:
        asked += 1
        try:
            if not unreal.EditorAssetLibrary.does_asset_exist(path):
                report.append("# statistics channel candidate %s is not in "
                              "this engine's asset registry" % path)
                continue
            mat = unreal.EditorAssetLibrary.load_asset(path)
        except Exception as e:
            report.append("# statistics channel candidate %s would not load: "
                          "%s" % (path, str(e)[:160]))
            continue
        if mat is None:
            report.append("# statistics channel candidate %s loaded as "
                          "nothing" % path)
            continue
        px, vx, _samplers = _material_statistics(
            unreal, mel, mat, report, "engine material " + path)
        if px is None:
            continue
        answered += 1
        if first_answer is None:
            first_answer = (px, vx, path)
        if px > 0 and first_nonzero is None:
            first_nonzero = (px, vx, path)
    keep = first_nonzero or first_answer
    report.append("# statistics channel: %d of %d engine material(s) returned "
                  "a number, and the reading kept is %s"
                  % (answered, asked,
                     "none" if keep is None else "%s pixel=%s"
                     % (keep[2], keep[0])))
    if keep is None:
        return (None, None, "none-of-%d-engine-materials-answered" % asked,
                answered, asked)
    return keep[0], keep[1], keep[2], answered, asked


def _shader_api_names(unreal, report):
    """Report-only: every name in the unreal module with Shader in it, capped
    and announced.

    Run 24 read pixel.0 in a commandlet whose entire python step took 0.67
    seconds, which is also what an unfinished asynchronous shader compile
    looks like, and nothing in this repository knows whether a flush is
    reachable from Python at all. This costs nothing and answers that by name
    on the next run rather than in an argument.
    """
    try:
        names = sorted(n for n in dir(unreal) if "shader" in n.lower())
    except Exception:
        report.append("# the unreal module would not enumerate its names")
        return
    report.append("# unreal module names containing shader: %d found: %s"
                  % (len(names), "/".join(names[:20])
                     + ("(+%d more not shown)" % (len(names) - 20)
                        if len(names) > 20 else "")))


def main():
    if "--selftest" in sys.argv:
        return selftest()

    import unreal  # only inside the editor; the selftest above never gets here

    w = Wiring()

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

    # ---- THE DEFAULTS, ENGINE PATH FIRST AND A GENERATED ASSET SECOND -----
    # One per texture parameter, in TEXTURE_PARAMS order, each validated
    # against the sampler type it is going into. This is the change that is
    # supposed to make the material compile: run 23 gave the normal sampler
    # nothing at all and the roughness sampler an sRGB colour texture, and
    # either of those alone stops a material compiling.
    # THE REPORT IS OPENED HERE AND NOT AT THE COMPILE. It is the committed
    # evidence file, and what each texture answered for its compression
    # settings is the reading run 24 needed and did not keep.
    report = ["# LEDGER material step, %s" % ASSET_PATH]
    made_generated = []
    resolved = []
    for I, cands in enumerate((COLOUR_DEFAULTS, NORMAL_DEFAULTS,
                               ROUGHNESS_DEFAULTS)):
        resolved.append(_resolve_default(unreal, I, cands, w.notes,
                                         made_generated, report))
    default_vias = [(TEXTURE_PARAMS[I], r[1], r[3], r[4])
                    for I, r in enumerate(resolved)]
    default_fields = [default_via(r[1], r[2], r[3], r[4]) for r in resolved]
    defaults_bound, defaults_asked, defaults_detail = defaults_field(default_vias)
    compression_block = compression_field(
        [(TEXTURE_PARAMS[I], r[5][0], r[5][1], r[5][2])
         for I, r in enumerate(resolved)])

    # ---- the UV chain: TexCoord masked, scaled per axis, appended ----------
    # Two scalars rather than one, because a 42 metre carriageway 2.7 metres
    # wide tiled uniformly is 21 repeats along AND across, and the across is
    # what a camera in the street is looking at.
    def expr(cls, x, y):
        return mel.create_material_expression(mat, cls, x, y)

    def connect(a, out, b, inp, what):
        try:
            ok = bool(mel.connect_material_expressions(a, out, b, inp))
        except Exception:
            return w.record(False, "%s-threw" % what)
        return w.record(ok, "%s-refused" % what)

    def connect_prop(a, out, prop, what):
        try:
            ok = bool(mel.connect_material_property(a, out, prop))
        except Exception:
            return w.record(False, "%s-threw" % what)
        return w.record(ok, "%s-refused" % what)

    # THE HEAD OF THE UV CHAIN, WHICH IS THE ONE PAIR OF NAMES THIS SCRIPT
    # COULD NOT ESTABLISH BEFORE THE RUN. See UV_PIN_CANDIDATES. One
    # connection is counted however many names it costs, so materialConnections
    # keeps the denominator 14 that runs 19 and 20 printed and the fraction
    # stays comparable across the three runs.
    uv_head = []

    def connect_uv_head(src, dst, what):
        ok, tried, out_name, in_name = connect_by_candidates(
            lambda o, i: mel.connect_material_expressions(src, o, dst, i),
            UV_PIN_CANDIDATES)
        if ok:
            via = pin_token(out_name, in_name)
        else:
            wrote = _write_input_property(src, dst)
            # Written by property_write_via rather than here, because the
            # suffix of this string is what property_write_heads counts and
            # what the status word turns on, and a verdict-deciding string
            # built in the half of the file the tests cannot reach ships
            # unrun.
            via = property_write_via(len(UV_PIN_CANDIDATES), wrote)
            ok = wrote is True
        uv_head.append((ok, via, tried, _reads_back(dst, src)))
        # The token runs 19 and 20 printed is kept as a PREFIX so a grep for
        # texcoord-to-maskU-refused still finds this line if it happens again.
        return w.record(ok, uv_head_note(what, len(UV_PIN_CANDIDATES)))

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

    connect_uv_head(tc, mask_u, "texcoord-to-maskU")
    connect_uv_head(tc, mask_v, "texcoord-to-maskV")
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
        # THE TEXTURE BEFORE THE TYPE, AND THE TYPE ONLY WHEN IT EXISTS. A
        # texture that refused to assign and a sampler type this engine does
        # not spell the same way are different faults with different next
        # actions, so they get a note each instead of one shared catch.
        if default_tex is not None:
            try:
                s.set_editor_property("texture", default_tex)
            except Exception:
                w.notes.append("%s-default-texture-refused" % label)
        else:
            w.notes.append("%s-has-NO-default-texture" % label)
        if sampler_type is None:
            w.notes.append("%s-sampler-type-not-available" % label)
        else:
            try:
                s.set_editor_property("sampler_type", sampler_type)
            except Exception:
                w.notes.append("%s-samplertype-refused" % label)
        connect(app, "", s, "UVs", "%s-uvs" % label)
        if connect_prop(s, out_pin, prop, "%s-out" % label):
            made.append(name)
        return s

    mp = unreal.MaterialProperty
    # THE DECLARED TYPE IS THE TYPE THE RESOLVED TEXTURE DERIVES, and only
    # falls back to the intended one when nothing resolved at all. Unreal
    # compares those two and refuses the mismatch, so taking the texture's
    # own answer is what makes the compile impossible to lose on an sRGB flag
    # an importer decided. What was ASKED for is on the verdict line beside
    # what was used, so a substitution is visible rather than silent.
    for I, (prop, out_pin, label, y) in enumerate(
            ((mp.MP_BASE_COLOR, "RGB", "basecolor", -300),
             (mp.MP_NORMAL, "RGB", "normal", 0),
             (mp.MP_ROUGHNESS, "R", "roughness", 300))):
        tex, _source, _path, got, asked, _reading = resolved[I]
        sampler(TEXTURE_PARAMS[I], y,
                _sampler_enum(unreal, got or asked), tex, prop, out_pin, label)

    # ---- THE COMPILE, AND THE EVIDENCE THAT IT HAPPENED ------------------
    # RUN 23 ASKED FOR A RECOMPILE, CAUGHT AN EXCEPTION THAT NEVER CAME AND
    # CALLED THAT SUCCESS. The absence of a raised exception says nothing
    # about a shader. Two markers go into the editor's own log around the
    # recompile and the save, the slice between them is scanned for the lines
    # Unreal prints when a material fails to translate, and the editor is
    # asked for the material's shader statistics afterwards. Zero errors over
    # a non-zero count of lines examined, between both markers, AND a
    # non-zero instruction count is the only set that reads OK.
    try:
        unreal.log(COMPILE_MARK_BEGIN)
    except Exception:
        w.notes.append("compile-begin-marker-not-logged")
    try:
        mel.recompile_material(mat)
    except Exception:
        w.notes.append("recompile-threw")
    saved = False
    try:
        saved = bool(unreal.EditorAssetLibrary.save_asset(ASSET_PATH))
    except Exception:
        w.notes.append("save-threw")
    px, vx, samplers = _material_statistics(unreal, mel, mat, report,
                                            ASSET_PATH)
    # THE ENGINE READING, WHICH GATES NOTHING and is here only because it is
    # worth knowing whether this call returns a number for anything at all in
    # this editor. It is taken inside the markers, where it has always been:
    # nothing it does is a material compile, and moving it would change what
    # the diagnostic slice covers on the same run that changes the control.
    chan_px, chan_vx, chan_from, chan_answered, chan_asked = \
        _statistics_channel(unreal, mel, report)
    _shader_api_names(unreal, report)
    # THE PARAMETER NAMES, READ BACK OUT OF THE FINISHED MATERIAL. This is
    # the C++ contract in SurfaceBind.h, and until now nothing anywhere
    # checked that the material ended up carrying it. Reported and not gated:
    # an API that is missing in some engine version must not be able to fail
    # a run whose material is correct.
    for getter, wanted, what in (("get_texture_parameter_names", TEXTURE_PARAMS,
                                  "texture"),
                                 ("get_scalar_parameter_names", SCALAR_PARAMS,
                                  "scalar")):
        fn = getattr(mel, getter, None)
        if fn is None:
            report.append("# %s is not available in this engine version"
                          % getter)
            continue
        try:
            names = [str(n) for n in fn(mat)]
        except Exception as e:
            report.append("# %s raised: %s" % (getter, str(e)[:160]))
            continue
        found = len([n for n in wanted if n in names])
        report.append("# %s parameter names in the finished material: %d of %d "
                      "asked for, and the material answered %d name(s): %s"
                      % (what, found, len(wanted), len(names),
                         "/".join(names[:12])
                         + ("(+%d more not shown)" % (len(names) - 12)
                            if len(names) > 12 else "")))
    try:
        unreal.log(COMPILE_MARK_END)
    except Exception:
        w.notes.append("compile-end-marker-not-logged")
    # THE TWIN, AND IT IS DELIBERATELY OUTSIDE THE MARKERS. Everything it logs
    # lands after the END marker, so its own compile can never be counted as
    # this material's: log_slice stops at the end marker. If the end marker is
    # MISSING the slice runs to the end of the log and can pick the twin's
    # lines up, which is the safe direction and only ever reads as ERRORS or
    # UNPROVEN, never as a pass, because OK needs both markers.
    # Our material is already SAVED at this point, so the twin cannot be in
    # that save; it is never saved itself and it is deleted below.
    ctl_px, ctl_vx, ctl_from = _statistics_twin(unreal, tools, mel, report)
    lines = _read_editor_log(unreal, report)
    sliced, saw_begin, saw_end = log_slice(lines) if lines is not None \
        else ([], False, False)
    errors, examined, matched = compile_scan(None if lines is None else sliced)
    # THE WORD, COMPUTED ONCE AND ONCE ONLY. It goes to the evidence block
    # and to the status below. It used to be computed in both places from
    # the same inputs, which is one number twice and drifts on the first
    # edit that touches one call and not the other.
    compile_word = compile_verdict(errors, examined, px, saw_begin, saw_end,
                                   ctl_px)
    compile_block = compile_fields(compile_word, errors, examined, px, vx,
                                   samplers, saw_begin, saw_end,
                                   ctl_px, ctl_vx, ctl_from,
                                   chan_px, chan_vx, chan_from,
                                   chan_answered, chan_asked)
    # THE DIAGNOSTICS FILE, WHICH IS THE CHANNEL THIS PROJECT TRUSTS. A log
    # tail in a step summary has failed here; a committed file has not.
    _write_beside("ue-material-log.txt",
                  "\n".join(report) + "\n"
                  + compile_log_text(ASSET_PATH, errors, examined, matched))

    uv_via, uv_tried, uv_readback = uv_head_fields(uv_head,
                                                   len(UV_PIN_CANDIDATES))
    # THE THIRD STATE'S ONE INPUT. Counted over the head records, not over
    # the via string, and counted here so that the word and the number the
    # word was decided from go out on the same line.
    by_prop, _by_prop_of, by_prop_field = property_write_heads(uv_head)
    status = material_status(saved, len(made), len(TEXTURE_PARAMS),
                             w.wired, w.asked, by_prop,
                             defaults_bound, defaults_asked,
                             compile_word)
    _write(material_line(status, len(made), len(TEXTURE_PARAMS),
                         w.wired, w.asked, existed,
                         default_fields[0], default_fields[1],
                         default_fields[2],
                         defaults_bound, defaults_asked, defaults_detail,
                         compile_block,
                         generated_field([r[1] for r in resolved],
                                         len(made_generated)),
                         saved, w.notes,
                         uv_via, uv_tried, uv_readback, by_prop_field,
                         compression_block))
    return material_return(status)


def _write_beside(name, text):
    """A second evidence file beside the project, for what does not fit on a
    key=value line: the compile diagnostics in the engine's own words, where
    the editor's log was read from and how many lines of it were examined,
    and what the statistics API actually offered. The workflow copies it into
    production/d1-probe/ by name and commits it, because a log tail on the
    runner is a file nobody here can ever open."""
    try:
        import unreal
        root = unreal.Paths.project_dir()
    except Exception:
        root = "."
    try:
        with open(os.path.join(root, name), "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass


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
