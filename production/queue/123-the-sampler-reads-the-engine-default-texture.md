line: production (the Unreal emitter, Phase C)
spec: this file. Supersedes queue 062 as the reason the street was untextured.
acceptance: MET on landed run 25 (87b20592, "UE machine probe from 288ff51")
  for the two readings that do not depend on a chosen sample window. The third
  reading I set is INVALID, not failed; see below.
max_sessions: 2
status: DONE 2026-09-06 after five runs. THE STREET HAS ITS TEXTURES.

## THE STREET IS TEXTURED, run 25, and what actually proves it

Two readings carry it and neither depends on where I chose to point:

1. THE COLOUR CONTROL QUAD. Bound to a 2x2 of pure red, green, blue and
   yellow, built in code with no file and no decode. It read chroma max 6 of
   255 on runs 23 and 24. On run 25 it reads chroma mean 158.7, max 195, over
   11,880 pixels. That is the intended texture reaching pixels, which is the
   claim and the whole claim.

2. THE WHOLE FRAME, quad boxes excluded per the verdict's own instruction:
   max chroma 133 over 873,860 pixels, with 100,691 of them (11.5 percent)
   above chroma 15. Fifteen was the ENTIRE FRAME'S MAXIMUM on run 23.

## THE THIRD READING IS INVALID, NOT FAILED, AND IT WAS MINE

I recorded in advance that `east_parade_bay3`'s wall face at (820,300) to
(960,420) must move R/B above 1. It reads 0.881, and chroma moved 4.6 to 22.1.

THAT WINDOW NEVER MEASURED BRICK. A z-ordered coverage test at its centre
returns `east_parade_glass0` at depth 1.0 metres, with bay3 sixteen metres
behind it. The window is a pane of glass one metre from the camera.

It only looked correct because when every surface renders the same grey, glass
and brick are indistinguishable. THE FIX IS WHAT EXPOSED THE FLAW IN MY OWN
BASELINE. That is the day's main lesson arriving one level up: a measurement
taken while everything is broken can encode the breakage, and reads as a clean
baseline until something works.

MARKED INVALID BY JAFAR'S RULING 2026-09-06, and it must not be reported as
either passed or failed. The specific brick check is OPEN: it needs an
unobstructed view of a named brick piece before anyone claims it passed, and
whole-frame colour cannot establish which material is on that surface. Queue
137.


## RUN 24: THE FIX FAILED, AND THE INSTRUMENT WAS THE CAUSE

Run 24 landed as `1ee090f8`. Nothing moved: `east_parade_bay3` reads R/B 0.933
against run 23's 0.934, and the colour quad still reads chroma max 6 of 255.

THE TEXTURE WAS NEVER WRONG. THE READING WAS, AND THE READING THEN MADE A REAL
COMPILE ERROR. `derived_sampler_type` cut the compression enum with
`str(compression).split(".")[-1]`, which assumes the printed form ENDS at the
leaf. If UE 5.8 prints `<TextureCompressionSettings.TC_NORMALMAP: 1>`, the
split is on the DOT, so the final segment is `TC_NORMALMAP: 1>`, which matches
no named branch and the catch-all answered LINEAR_COLOR. (The resident first
wrote that tail as `NORMALMAP: 1>`, dropping the TC_ prefix the split keeps.
Corrected by the director; it changes nothing in the diagnosis and everything
in whether the sentence describes the code.)

The corroboration nobody had looked at: ALL THREE textures in run 24 took that
catch-all. Colour derived COLOR, roughness LINEAR_COLOR, normal LINEAR_COLOR,
and not one named branch of that function has ever been observed to fire
against a real engine string. Two of the three were right for the wrong reason
and hid the third.

AND THE SECOND ORDER IS THE REAL DAMAGE. `main()` declares each sampler as
`_sampler_enum(unreal, got or asked)`, where `got` is the DERIVED type. So the
misreading did not merely mis-report: it declared the normal sampler
LINEAR_COLOR while handing it a TC_Normalmap texture. The instrument did not
fail to see the fault. It caused it.

The importer's own words, from the committed log:
`LogInterchangePipeline: Display: Auto-detected normal map`. TC_NORMALMAP was
applied twice, by the importer and then by the script, and never contradicted.

## A CORRECTION TO THIS FILE AND TO WHAT JAFAR WAS TOLD

The resident wrote that `materialCompileInstructions=pixel.0..vertex.0` proves
candidate D rather than inferring it. THAT IS OVERSTATED and the builder
refused it.

`pixel.0` has NO ACCEPTING CASE anywhere in this repository: that channel has
never printed a non-zero number for any material, so a zero from it cannot yet
be told from a channel that does not work. And there is a live alternative:
the editor ran as a `-run=pythonscript` commandlet with `rhiname="Null"`, the
whole Python step took 0.674 seconds, and `materialCompileSamplers`, `pixel`
and `vertex` all read zero TOGETHER, which is the signature of "no shader map
available at read time" and includes "the async compile had not finished".

CANDIDATE D IS PROVEN BY RUN 23'S CONTROL QUADS: full readbacks beside a bound
texture of chroma 255 rendering at max 6, and two quads differing only in
tiling rendering an identical period. `pixel.0` CORROBORATES that. It does not
carry it alone. The two were conflated and they are now separated.

## THE ANSWER, from the landed run, read before any gate

Readbacks, all full, from `production/d1-probe/ue-vignette-verdict.txt`:

    midReadbackAsked=12/16 midParamReadback=12/12 midScalarReadback=12/12
    texResourceValid=12/12 compMaterialIsMid=12/12

The instance holds the texture. It holds the scalars. The texture has a valid
render resource. The component carries the instance we made. A, B and C are
all refuted by that line: A wanted both readbacks short, B wanted the texture
half short, C wanted an invalid resource.

The control quads, measured off `production/d1-probe/ue-vign_camA_day.png` at
the `quadBoxPx` the verdict itself prints, so the sampling window was chosen
before the numbers were seen:

    colour quad, bound to a 2x2 texture of pure red, green, blue and yellow
        built in code with no file and no decode, chroma 255 at source:
        renders chroma mean 3.7, max 6, over 11,880 pixels. Neutral grey.
    tile1 (quadTiling=1.00x1.00) against tile4 (quadTiling=4.00x4.00), one
        size, one distance, differing in nothing else:
        IDENTICAL 12 px checker period, 9.0 cells vertically in both.
        A fourfold tiling change moved nothing.

AN INSTANCE THAT IS PERFECT WHILE NEITHER ITS TEXTURES NOR ITS SCALARS REACH
THE PIXELS MEANS THE SHADER IS NOT OURS. The engine default material is what
is on screen, and it ignores material instance parameters entirely, which is
exactly why every readback can be full while nothing changes.

## Why the earlier frames could not have told us this

The default material is also a grey checker. So is this material's own colour
sampler default. Every reading taken before the control quads existed was
consistent with both, and the project spent two runs and most of a morning
arguing about which sampler was misbehaving in a material that was never
running. THE QUADS ARE WHAT SEPARATED THEM, and specifically the tile pair:
nothing else in this repository could distinguish "the parameters do not
arrive" from "the material does not exist as far as the renderer is
concerned".

## The mechanism, still a lead and not yet proven

`tools/ue/make_base_material.py` line 161, written before any of this:
"A texture parameter with no default can fail to compile."

`production/d1-probe/ue-build.txt` reads
`materialNormalDefault=none-of-2-candidates materialDefaultsBound=1/2`. Both
NORMAL_DEFAULTS candidates, `/Engine/EngineMaterials/DefaultNormal` and
`/Engine/EngineResources/DefaultTextureNormal`, failed to resolve in UE 5.8,
so the normal sampler carries a NULL texture. Unexplained and plausibly the
same event: `materialEditorCmdExit=1` printed beside
`materialScriptReturn=0` and `materialStatus=MADE`.

## THE BEFORE NUMBER THE FIX MUST MOVE, taken on run 23's own frame

`east_parade_bay3` wall face, `production/d1-probe/ue-vign_camA_day.png` at
(820,300) to (960,420), 16,800 pixels:

    rendered       mean RGB (65.3, 67.1, 69.9)   R/B 0.934   chroma mean 4.6, max 7
    brick_red.jpg  mean RGB (141.4, 131.3, 109.6) R/B 1.290   chroma mean 31.9

Unchanged from run 21 to within a tenth of a level, which is itself
confirmation: run 22's instrument work and run 23's control quads changed what
we can SEE about the street and changed nothing about the street. An accepting
run moves R/B above 1 and chroma well above 7 in that window. It is written
down here BEFORE the fix so the bar cannot be chosen afterwards.

## What MADE meant, and why it must get harder rather than easier

`materialStatus=MADE` was printed over a material that never rendered a pixel.
The generator requests recompilation, catches exceptions, and saves without
establishing that the shader is valid, so the absence of an exception was read
as success. The next version must print positive evidence: compilation errors
with their denominator, and a readback that the material has a valid shader
map. NO COMPILATION ERRORS PLUS EVIDENCE OF A VALID RENDERED RESULT, never the
absence of a raised exception.

## THE PROOF, ADDED 2026-09-06 AFTER THE FIRST DRAFT, AND IT NAMES A PIECE

Everything above reasons from whole-frame statistics. This does not. One named
piece, one named surface, one denominator.

`east_parade_bay3` is a brick_red piece, 6.00 x 6.20 x 8.00 m. brick_red reads
`surfaceStatus=RESOLVED pieces=41 piecesAssigned=41/41` in the verdict, so this
piece HAS a dynamic material instance with `brick_red.jpg` bound to
BaseColorMap. Projected into camera A it occupies a screen box of 308 x 226 px
and it is the nearest thing covering the centre of the region I sampled, behind
only a 4 px drainpipe.

Its wall face, sampled over 16,800 pixels at (820,300) to (960,420):

    rendered   mean RGB (65.3, 67.1, 69.9)   R/B 0.934   chroma mean 4.6, max 7
    (CORRECTED: the first draft of this passage read (64.9, 66.7, 69.5),
     measured on run 21's frame before run 23 landed. Same R/B to three
     decimals, so the bar never moved, but two figures for one quantity in
     one file is how a stale number outlives the run it came from. The
     builder reading this file caught it.)
    brick_red.jpg  mean RGB (141.4, 131.3, 109.6)   R/B 1.290   chroma mean 31.9

THE RENDERED SURFACE IS COOLER THAN NEUTRAL WHERE THE TEXTURE IS WARM. A blue
grey overcast sky can drain warmth out of a red brown albedo; it cannot invert
the channel ordering. R/B 1.290 does not render at R/B 0.934, and chroma 32
does not render at a maximum of 7, over 16,800 pixels.

That single comparison carries what the whole-frame chroma reading in point 4
only suggested, and it carries it without the frustum caveat, because this
piece is measurably in shot at 308 x 226 px. Point 4's open half is closed.

THE CAMERA CONVENTION THIS RESTS ON, established rather than assumed. cam_A
sits at x 4, z 4, eye 1.672, yaw 0, pitch 4, fovV 60. Yaw 0 points along +x.
That was found by trying all four axis conventions and counting piece centres
inside the frame: +x gives 474 of 593, -z gives 66, +z gives 5, -x gives 0. A
previous dispatch projected cam_A using cam_B's position and yaw, which is why
its region attributions named a drainpipe and a window sill, and none of them
should be believed.

WHAT IS STILL NOT ESTABLISHED, said plainly. Which piece the visible grey
checkerboard at (672,240) to (738,318) actually is. Two candidates overlap
there: bay3 itself, and `decal_01_fascia_fish_market`, a card surface which is
ABSENT and therefore unassigned, whose centre projects to (716,283). It matters
only for the wording of the first elimination below, not for the proof above.
The region-coverage test found no unassigned piece whose screen box covers the
centre of any of the three checkered regions sampled.

## THE CAUSE, NAMED

The base material's colour sampler renders ITS OWN DEFAULT TEXTURE,
`/Engine/EngineResources/DefaultTexture`, and not the texture the dynamic
material instance binds to `BaseColorMap`.

HELD PROVISIONAL 2026-09-06 pending candidate D below, which says the checker
may not be that sampler's default at all but the engine's default MATERIAL,
shown because M_LedgerSurface does not compile. Both cause sentences predict a
grey checker, and the frame alone cannot separate them. What is NOT in doubt,
because a named piece measured it, is the proof below: a piece the verdict
certifies as textured is rendering none of its albedo.

The elimination that gets there:

- The sampler IS connected to BaseColor. If it were not, the engine checker
  could not appear in the frame at all. It appears.
- The UV chain IS live. If UVs were constant the checker would be one flat
  texel per face, and it is not: the checker on the hanging sign has a
  measured vertical period of 13 px over a 125 px face, about 9 cells, and on
  the pillar strip 20 px over 104 px, about 5 cells. Detrended by a plane fit
  first, because the lighting gradient dominates a raw transform.
- The parameter names are in the asset. `ue-probe/Content/Ledger/M_LedgerSurface.uasset`
  carries all five name-table entries: BaseColorMap, NormalMap, RoughnessMap,
  TilingU, TilingV, beside MaterialExpressionTextureSampleParameter2D.
- The textures decoded, at the sizes and colour spaces the verdict prints.

CORRECTION, ENTERED THE SAME DAY THIS ITEM WAS WRITTEN. The first draft went
on to say that the varying cell size proves TilingU and TilingV reach the
shader, so the MID's scalar overrides arrive. THAT IS A LEAD AND NOT A FACT,
and it is withdrawn. The three large surfaces where the claim would be decided
carry no periodic signal at all after detrending: right wall sd 0.08, road sd
0.13, pavement sd 0.15, against a sign panel sd 2.16 that does carry one. Flat
is what a densely tiled checker mips down to AND what an untextured surface
looks like, so those three cannot tell the two apart. The sign and the pillar
are different pieces of unknown world size, so two different cell counts do
not establish that the count tracks the size. What is established is only that
the samplers receive VARYING UVs somewhere. Whether any MID parameter of any
kind reaches the shader is OPEN, and the candidates below are written on that
basis.

What is left is one sentence: the sampler renders its own default texture
instead of the one bound to it. WHICH parameter path is broken, texture only
or every parameter, is the open half and is what the run below settles.

## What run 21 actually changed, and why nobody saw this before

Queue 062 was right about run 20 and is now discharged. Before run 21 every
sampler read one texel, so all 563 pieces rendered one flat colour each and
the frame could not distinguish "no texture bound" from "one texel of the
right texture". Wiring the UV head is what made the engine checker visible and
turned the fault into a readable one. 062 was necessary and was not
sufficient, and the street is still untextured after its acceptance was met.

## The three candidates, and the ONE run that separates them

D. THE BASE MATERIAL DOES NOT COMPILE, so nothing in the scene is rendering
   M_LedgerSurface at all and every reading above is about the wrong material.
   Raised by the engine-specialist reading the asset, not by this item, and it
   may be the best explanation of the lot. The colour sampler has a default
   texture; the NORMAL sampler has none. `ue-build.txt` line 12 prints
   `materialNormalDefault=none-of-2-candidates materialDefaultsBound=1/2`, and
   `tools/ue/make_base_material.py` lines 1012 to 1018 only assign a default
   when one resolved, while line 1029 passes a normal default that was None.
   The uasset's strings carry exactly one texture object path,
   /Engine/EngineResources/DefaultTexture, and none for the normal. In Unreal a
   texture sample parameter with a NULL texture is a material COMPILE ERROR,
   and a material that fails to compile renders as the engine's default
   material, which is also a grey checker.
   If D is what happened then every readback can come back full, every MID can
   be correct, and the checker has nothing to do with BaseColorMap. It explains
   more of what is on the frame than A, B or C do: why 0 MIDs and 563 MIDs
   produce a nearly identical picture (the default material ignores MID
   parameters entirely), why a brick_red bay renders neutral, and why the
   checker's cell size did not track piece size. THIS ITEM'S NAMED CAUSE IS
   PROVISIONAL UNTIL D IS EXCLUDED.

A. No MID parameter override of any kind reaches the shader, texture or
   scalar. The material renders entirely on its own defaults.
B. Texture overrides specifically do not land, while scalar overrides do.
C. The override lands and the bound texture has no valid render resource, so
   the sampler falls back to the expression default.

All three are answered by one dispatch, and a dispatch costs the same carrying
one change or six:

1. READBACK, printed per surface, not per piece. Immediately after
   `SetTextureParameterValue`, call `GetTextureParameterValue` for the same
   FName and print whether what comes back is the pointer that went in:
   `midParamReadback=<n>/<asked>`. Do the SAME for the scalars,
   `midScalarReadback=<n>/<asked>` from GetScalarParameterValue against the
   TilingU and TilingV that went in. That pair is what separates candidate A
   from candidate B, and nothing in this repository measures it today.
   Print `texResourceValid=<n>/<asked>` from
   `Tex->GetResource() != nullptr` read AFTER `UpdateResource()`. Print
   `compMaterialIsMid=<n>/<asked>` from `Comp->GetMaterial(0) == Mid`.
   Whole-run numbers on the done line; never both moments under one key.
2. THE CONTROL QUAD, which is the accepting case this diagnosis has never had.
   Spawn one extra plane in front of camera A, give it a MID off the same base
   material, and bind a 2x2 texture BUILT IN CODE with four known colours, no
   file and no decode. Print `controlQuad=` with the four colours asked for
   and where on screen the quad sits, so the frame can be read against it.
   If that quad renders those four colours, MID texture overrides work and the
   fault is in the imported textures or their resources, which is C. If it
   renders the grey checker, no texture override reaches the shader, which is
   A or B and the scalar readback says which. Either way the next step is
   named by a picture rather than by argument.

## The bound that comes with it

`midParamReadback` and `midScalarReadback` are the numbers that move, and they
are read as a PAIR. Both equal to the number asked, with the frames still
flat, refutes A and B together and leaves C. `midScalarReadback` full with
`midParamReadback` short is B. Both short is A. Neither number is read alone,
because two numbers derived from one variable would be one number twice, and
these two are not: a scalar and a texture take different paths into the
render proxy, which is the whole reason both are asked for.

## The standing risk this item carries

Nothing here has run an engine. Every sentence above is read off a committed
frame, a committed verdict and a committed asset, and that is the whole reason
the control quad is in the deliverable: a diagnosis with no accepting case is
a lead.
