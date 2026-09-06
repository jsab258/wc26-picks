line: production (the Unreal emitter, Phase C)
spec: this file. Supersedes queue 062 as the reason the street is untextured.
acceptance: a LANDED Unreal run whose four frames show Meridian's own albedo
  on the street, with midParamReadback and controlQuad printed beside them.
  Never a local claim, and never a green key standing in for a frame.
max_sessions: 2
status: READY 2026-09-06. P0 for the weekend. engine-specialist.

## What is true, with the file each number came from

1. `production/d1-probe/ue-build.txt` line 12, run 21 (commit 372fd95):
   `materialStatus=MADE materialScriptReturn=0 materialConnections=14/14
   materialUvHeadVia=both.out.empty..in.empty materialUvHeadTriedAtWorst=1/9
   materialUvHeadByPropertyWrite=0/2
   materialColourDefault=/Engine/EngineResources/DefaultTexture
   materialDefaultsBound=1/2`.
   Queue 062's acceptance criterion is MET. The UV head is wired.

2. `production/d1-probe/ue-vignette-verdict.txt`. CITATION CORRECTED by the
   builder that read it: lines 56 to 71 are the sixteen SURFACE lines, and
   `surfacesResolved=12/16 texturesImported=36 midsCreated=563
   piecesTextured=563/593` is on LINE 72. 12 of 16 surfaces RESOLVED, every
   albedo decoded `2048x2048/JPEG-BGRA8/srgb=yes` under `albedoParam=BaseColorMap`.
   Import, decode and assignment are not the fault. The 30 unassigned pieces
   are exactly the four ABSENT surfaces: card 10, interior 6, multiply 10,
   paint_yellow 4, which sum to 30 and to 593 minus 563.

3. `production/d1-probe/ue-vign_camA_day.png`, opened and looked at. The
   hanging sign, the foreground bins and the pillar render a regular grey
   CHECKERBOARD. That is `/Engine/EngineResources/DefaultTexture`, which
   line 12 names as `materialColourDefault`.

4. The same frame, measured: maximum chroma 15 over 230,400 pixels sampled at
   stride 2 of 921,600. SAY WHAT THIS REFUTES AND WHAT IT DOES NOT. Of the 12
   albedo files read in `ledger/Assets/StreamingAssets/CityPack/textures`,
   five are close to neutral and could render at chroma 15 without anyone
   noticing: asphalt mean chroma 2, kerb 0, plaster 7, concrete 7, metal 22 at
   the extreme. Those five are NOT refuted by this number. Four are: brick_red
   mean chroma 31 over 41 pieces, wood 42 over 32 pieces, roof 69 over 2, and
   sidewalk whose texel(0,0) chroma is 86 over 5. A frame carrying 41 brick
   pieces and 32 wood pieces cannot top out at 15.
   The unproven half, stated rather than buried: how many of those 80 coloured
   pieces are actually inside camera A's frustum has not been counted, and
   until it is, this reading is strong evidence and not proof. The frame-flatness
   in point 5 is the reading that does not depend on it.

5. The same frame, 8x8 block standard deviations: 6,714 of 14,400 blocks below
   1.0. Nearly half the frame is dead flat. Denominator: 14,400 blocks, all
   examined.

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

    rendered   mean RGB (64.9, 66.7, 69.5)   R/B 0.934   chroma mean 4.6, max 7
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
