# BILL OF MATERIALS: the D1b street vignette

STATUS: SPEC. Written 2026-09-01. Line: Prop/asset, station 1 of 5.
Scope ruled by `game-design/decision-2026-09-01-production-prep-sequence.md`
(Ruling 3) and defined by `game-design/decision-D1b-rescope.md`.

`production/specs/vignette-bill-of-materials.json` is the machine copy AND
THE SOURCE OF EVERY COUNT BELOW. It exists because steps 3 and 4 of the
prep sequence generate a fetch spec and a meshgen spec from this list, and
a list a machine cannot read gets retyped, and a retyped list drifts. Every
number in the findings section was computed from that file by the one-liner
quoted in section 6, so anybody can re-run it and catch me if it drifted.

## 1. What this is, and what it is not

This is the list of what the camera has to see before the D1b vignette can
be shot, and for each thing, where it comes from. It is the vignette only.
It is not the town, not a district, not the other six districts, not
interiors and not the water.

The scene, quoted from the re-scope ruling: one shared JSON scene
definition, a small British street on the D8 bar, wet asphalt, brick, an
overcast day and a wet night as two conditions, practical lights at night,
at least one clothed character body, allowlisted assets only, and every
object arriving in each engine via that engine's generator from the shared
JSON. A hand-placed object disqualifies the still as evidence.

Era is 1988 to 1992, a British port town, wet and unglamorous (canon.md).
Any 1950s or 1970s framing is an error and has happened twice here.

## 2. How to read a line

**Route**, exactly one per line:

| route | means |
|---|---|
| HAVE | the bytes are in this repository now, licensed and attributed |
| FETCH | a free allowlisted library is the candidate; read the certainty column before believing it |
| GENERATE | no library route. Made here, and the sub-kind says by what |
| BLOCKED | needs a decision from Jafar |
| ENGINE | not an asset at all, a renderer feature. Counted separately and never inside the asset denominator |

**Made by**, on GENERATE lines only, and this is the column the AMD
question turns on:

| sub-kind | means | costs |
|---|---|---|
| PROC | composed from primitives by the scene generator, from the shared JSON | nothing. The generator is built for D1b anyway |
| 2D | the local image generator (stable-diffusion.cpp with Z-Image-Turbo, Apache-2.0, Vulkan backend) that already ran on Jafar's AMD machine and produced the 14 signage images in the repo | nothing, no account |
| MESH3D | needs image-to-3D geometry synthesis | THIS is what the AMD card blocks |

**Certainty**, so a guess never reads as a fact:

- HELD: the bytes are on disk here and were measured or listed this session.
- PROVEN-ROUTE: this exact fetch pattern has run for this project and banked files.
- NEEDS-CHECKING: plausible, nobody has looked. Not a claim about any library's contents.

**Priority**: MANDATORY (the shot cannot happen without it), DRESSING (the
shot happens and looks unfinished), IF-IN-FRAME (exists only if the named
condition holds, so it is not a wish sitting on a list).

**Dims policy, inherited from the props-local-01 lesson**: dimensions are
measured at ingest from the file's own numbers and never invented. Nothing
here carries a target size except where the generator emits it from JSON.

## 3. The two cameras, proposed not ruled

The groups below are ordered by what each camera sees. Both are proposals
for the scene spec, not decisions:

- **Camera A**: eye height about 1.6 m on the pavement, looking along the
  street, kerb line running to the vanishing point. Sees groups A, B, E, G, H.
- **Camera B**: from the far kerb, square to the frontage, roofline in
  frame. Sees groups A, C, D, G, H.

Two cameras by two conditions is the four pairs the re-scope ruling judges on.

## 4. The list

77 lines: 71 asset lines and 6 engine lines. Counts of variants are in the
JSON; the "n" column below is how many variants that line wants or holds.

### A. The ground from the camera to the vanishing point (11 lines)

| id | what | n | route | source and licence | pri |
|---|---|---|---|---|---|
| A0 | The carriageway and footway planes, two levels, road camber falling to the gutter | 1 | GENERATE PROC | scene generator from the JSON street path and widths | M |
| A1 | Road asphalt, colour + normal + roughness | 1 | HAVE | CityPack `asphalt*.jpg`, ambientCG Asphalt012, 2K, CC0 | M |
| A2 | The AO and displacement maps the first fetch skipped, 4K where published | 1 | FETCH (needs checking) | ambientCG, same `get?file=` pattern the repo already runs | D |
| A3 | Pavement paving | 1 | HAVE | CityPack `sidewalk*.jpg`, ambientCG PavingStones067, 2K, CC0 | M |
| A4 | Tarmac repair patch over slabs | 1 | FETCH (needs checking) | ambientCG, id unknown | D |
| A5 | Double yellow lines | 1 | GENERATE 2D | decal generator | M |
| A6 | Worn white road paint | 6 | HAVE | ambientCG RoadLines001/004/007/010/011/018, 2K PNG with opacity, CC0 | D |
| A7 | Road gully grate | 1 | HAVE | `drainage_grate_01`, The Base Mesh, CC0, measured 0.40 x 0.40 x 0.01 m | M |
| A8 | Manhole cover | 2 | HAVE | ambientCG ManholeCover011 decal + `drain_cover_01` mesh, CC0 | M |
| A9 | Puddle mask, where the standing water is | 1 | GENERATE 2D | local image generator or procedural noise | M |
| A10 | Kerbstone surface material | 1 | HAVE | CityPack `kerb*.jpg`, ambientCG Concrete034, 2K, CC0 | M |

Three findings live in this group.

**A0 was added on review of this document, not found in the sources.** A1
and A3 are the materials; nothing anywhere named the geometry they sit on.
Camber matters more than it sounds: the fall to the gutter decides where A9's
water collects, so a flat carriageway makes both wet conditions wrong in a way
no texture can repair.

**A5 is the cheapest Britishness in the document.** Two yellow strips along
the kerb. The art-direction accent budget (R-B4) says the British street is
a low-chroma field punctuated by a handful of mandated high-chroma objects,
and this is one of them. The six held RoadLines sets are generic worn white
paint, so check them before generating, but do not expect a double yellow.

**A8 is a measured contradiction, not a suspicion.** `drain_cover_01`
measures 0.10 x 0.10 x 0.00 m in its own manifest. A road manhole is 0.45 to
0.60 m across, so this is an inspection cover or a mis-scaled export. Use the
2K decal on the road plane and leave the mesh alone: rescaling it would be
inventing a dimension, which the dims policy forbids.

**A9 was on no list anywhere before this one.** Both D1b conditions are wet.
Wet is a shader response (H6) plus a map of where the water actually stands,
and a uniformly wet road reads as plastic rather than as rain.

### B. The edge where road meets pavement (4 lines, all GENERATE PROC)

| id | what | n | route | source | pri |
|---|---|---|---|---|---|
| B1 | The kerb itself, extruded along the road edge | 1 | GENERATE PROC | scene generator from the JSON road path | M |
| B2 | Dropped kerb at a crossing or yard entrance | 1 | GENERATE PROC | same, a parameter of B1 | IF |
| B3 | The recess the gully grate sits in | 1 | GENERATE PROC | same, sized from the measured grate | M |
| B4 | Water running in the gutter | 1 | GENERATE 2D | decal generator | D |

**The whole of group B was missing from every document in this repository,
and it is the line the eye follows down a British street.** Nothing among
the 37 held props is a kerb. Whether Poly Haven's model library holds a
kerbstone is unchecked and I will not guess. It is also the wrong question:
the kerb follows a path that comes from the shared JSON, so under D1b's
admissibility rule it has to be emitted by the generator rather than placed
as a model, whatever any library holds. B3 matters more than it looks: a
grate lying flat on an unbroken kerb line reads as a sticker.

### C. The frontage at eye level (14 lines)

| id | what | n | route | source and licence | pri |
|---|---|---|---|---|---|
| C1 | The terrace masses, shop below and flat above | 1 | GENERATE PROC | scene generator from JSON | M |
| C2 | Red and orange brick | 2 | HAVE | ambientCG Bricks075A, Bricks101, 2K, CC0 | M |
| C3 | Blackened and grey brick | 3 | HAVE | ambientCG Bricks023, Bricks102 + generated soot overlay | M |
| C4 | Pebbledash or roughcast render | 1 | FETCH (needs checking) | ambientCG, family unknown. Plaster001/002 held as fallback | D |
| C5 | Shopfront: stallriser, pilasters, fascia band, transom | 1 | GENERATE PROC | scene generator | M |
| C6 | Shop name lettering on the fascia | 4 | HAVE | `Decals/generated/fascia_*.png`, 1024x512, Apache-2.0 weights | M |
| C7 | Shop glazing | 1 | HAVE | ambientCG Facade001, Facade018A, 2K, CC0 | M |
| C8 | Shop door, glazed upper half | 1 | GENERATE PROC | scene generator | M |
| C9 | Side door to the flat, panelled, number, letterplate | 1 | GENERATE PROC | scene generator | M |
| C10 | Closed roller shutter | 1 | FETCH (needs checking) | ambientCG CorrugatedSteel family; geometry is PROC | M |
| C11 | What is behind a lit window at night | 3 | GENERATE 2D | local image generator | M |
| C12 | Net curtain or blind | 2 | GENERATE 2D | local image generator | D |
| C13 | Sills, lintels, thresholds, air bricks | 1 | GENERATE PROC | scene generator | D |
| C14 | Salt bloom and soot wall overlays | 2 | HAVE | `Decals/generated/wall_*.png`, 1024x1024 | D |

**C5 is the densest Britishness at eye level and it is geometry, not a
texture.** A British shopfront reads as one object because of four parts in
a fixed relationship. Get the relationship and cheap brick looks right; miss
it and the best brick in the world looks like a wall with a hole.

**C6 carries an open action nobody has closed.** The generated signage
manifest marks every one of the 14 images `review=pending`, with its own
rule quoted: nothing ships until a human has looked for anything resembling
a real mark or a real face. That look has not happened. It is minutes of
Jafar or of a reviewing agent, and it gates four of the images this scene
uses.

**C7 is a scale mismatch waiting to happen.** Both held ids are whole-facade
photographs. Bound to a single pane they will be wrong, and the way to find
out is to look at the frame, not to re-source on suspicion.

**C11 was on no list before this one.** The night frame is half the D1b
evidence. A lit window with nothing behind it is a glowing rectangle.

### D. The upper facade and the skyline (8 lines)

| id | what | n | route | source and licence | pri |
|---|---|---|---|---|---|
| D1 | Roof covering | 2 | HAVE | ambientCG RoofingTiles006, RoofingTiles013A, 2K, CC0 | M |
| D2 | Brick chimney stack | 1 | GENERATE PROC | scene generator, brick from C2/C3 | M |
| D3 | Chimney pots | 2 | HAVE | `roll_top_chimney` 0.67 x 0.67 x 1.00 m, `weathertop_chimney`, CC0 | M |
| D4 | Television aerial | 2 | GENERATE PROC | scene generator, a comb of cylinders | M |
| D5 | Rainwater downpipe with hopper and shoe | 1 | GENERATE PROC | scene generator | M |
| D6 | Eaves gutter and fascia board | 1 | GENERATE PROC | scene generator | M |
| D7 | Parapet and coping | 1 | GENERATE PROC | scene generator | D |
| D8 | Sash windows with reveal depth | 1 | GENERATE PROC | scene generator | M |

**D1 needs an eye check that nobody has done.** canon and art-direction both
want Welsh slate, dark grey to black. The two held sets are roofing tiles by
id. A red clay pantile roof on a northern terrace is a region and period
error, not a matter of taste, and it would be visible in every camera B frame.

**D5 is the British answer to the American fire escape** (art-direction,
explicitly), and it is also the anchor the held Leaking005 stain hangs from.
Downpipe plus stain is one of the highest returns on the list.

### E. The furniture standing on the pavement (19 lines)

| id | what | n | route | source and licence | pri |
|---|---|---|---|---|---|
| E1 | Street lighting column, swan neck | 1 | GENERATE PROC | scene generator | M |
| E2 | Sodium lantern head, emissive | 1 | GENERATE PROC | scene generator | M |
| E3 | Red telephone kiosk | 1 | GENERATE PROC | scene generator | M |
| E4 | Red pillar box | 1 | GENERATE PROC | scene generator | M |
| E5 | Bollards | 4 | HAVE | The Base Mesh, CC0, measured 0.44 to 1.01 m tall | D |
| E6 | Public litter bins | 4 | HAVE | The Base Mesh, CC0, measured | D |
| E7 | Benches | 4 | HAVE | The Base Mesh, CC0, measured 1.10 to 1.50 m | IF |
| E8 | Pedestrian guard railing at the kerb | 1 | GENERATE PROC | scene generator | D |
| E9 | Victorian tree pit guard | 1 | HAVE | `trunk_protection_railing`, 2.06 x 2.04 x 0.60 m, CC0 | IF |
| E10 | Street name plate carrying a canon name | 2 | GENERATE 2D | image generator on a PROC plate | M |
| E11 | Traffic cones and a crowd barrier | 3 | HAVE | The Base Mesh, CC0, measured | D |
| E12 | A-board and poster frames | 3 | HAVE | The Base Mesh, CC0, measured | D |
| E13 | Galvanised metal household dustbin | 1 | GENERATE PROC | scene generator | D |
| E14 | Crates, pallets, barrels, builder's skip | 8 | HAVE | The Base Mesh, CC0, measured, skip 2.00 x 3.31 x 1.00 m | D |
| E15 | Belisha beacon | 2 | GENERATE PROC | scene generator | IF |
| E16 | Parking meter | 1 | GENERATE PROC | scene generator | IF |
| E17 | Bus shelter | 1 | GENERATE PROC | scene generator | IF |
| E18 | Shop awning over a frontage | 2 | HAVE | `awning_01/02`, The Base Mesh, CC0, measured 3.00 x 1.74 x 1.32 m | D |
| E19 | Direction finger post | 3 | HAVE | `finger_post_sign_01/02/03`, The Base Mesh, CC0, measured | IF |

**E1 is the highest-consequence measurement in this document.** The held
`lamp_post_01` measures 0.37 x 0.27 x 3.00 m in its own manifest. Three
metres is amenity or park height; a British residential lighting column of
the period is roughly 5 to 6 m. Lantern height decides the entire night
image: how far the light throws, how long the shadows are, how much of the
frame is lit at all. Rescaling the held mesh is forbidden by the dims policy.
Emitting a column at a height named in the JSON is not, and it costs nothing.

**E3 and E4 carry the colour of the whole frame and both carry a brand
problem nobody has written down.** art-direction R-B4: the British street is
a low-chroma field punctuated by a very small number of mandated, identical,
high-chroma red objects, which is a 60-30-10 palette handed to us for free.
The kiosk and the box are that budget. `game-design/visual-bar-sources.md`
records that neither is CC0-fetchable anywhere, which is why both are PROC.
The legal half: the silhouettes are architecture and are fine, but the
lettering and the crown on a kiosk and the cypher on a box are real marks,
and canon requires every brand fictional. A Meridian operator has to be
minted in the brand bible before either object can carry any lettering. The
brand bible currently owes four names and this is not one of them.

**E8 is not the railing we hold.** `trunk_protection_railing` is a tree pit
guard. Different object. Calling it a kerb rail is exactly the substitution
this document exists to prevent.

**E14 is the cheapest density on the list**: eight measured, licensed dock
objects for a port town, already through the clean and LOD pipeline.

**E18 and E19 exist because of a count, not because the scene asked for
them.** Checking which of the 37 held props this list actually names came
back 31 of 37, and a fetched prop no line names is precisely the failure this
project keeps finding. Both are genuinely wanted (an awning belongs on a
parade; a finger post belongs at a junction and nowhere else), so they are
lines with a condition rather than filler. Use `awning_02`: `awning_01`
carries 20 triangles and one LOD rung against 644 and three.

### F. Who and what is in the street (4 lines)

| id | what | n | route | source and licence | pri |
|---|---|---|---|---|---|
| F1 | One clothed character body | 18 | HAVE | `ledger/Assets/Characters/*.fbx`, Mixamo on Jafar's account | M |
| F2 | Clothing that reads as 1988 to 1992 | 1 | BLOCKED | no free re-dress route for a Mixamo body | D |
| F3 | An idle animation so the body is not a T-pose | 64 | HAVE | `Characters/{A,B,C,D}/*.fbx`, 64 accepted, 7 marked rejected | M |
| F4 | One parked period British car | 1 | FETCH (needs checking) | held vehicles are off-bar; no photoreal CC0 candidate checked | IF |

**F1 is sufficient for admissibility and open on quality, and the honest
sentence is that those are two different claims.** D1b requires at least one
clothed character body and 18 are held, licensed and attributed. They are
game-resolution bodies in contemporary casual dress, against a photoreal bar,
in a game set between 1988 and 1992.

**F2 is the only BLOCKED line in the document and it is not blocked by
money.** There is no free way to re-dress a Mixamo body. The allowlist offers
MetaHuman (free under 1M revenue, usable outside Unreal) and Character
Creator 4 exports, and each is a pipeline rather than an asset. The decision
is where the character line goes, which is Jafar's and not this document's.
**Recommendation: do not block D1b on it.** D1b measures what the pipeline
can reach, not what the wardrobe department can. Take a held body for the
probe, and put period wardrobe on the quality ladder with a name.

**F4 should probably be left out of the first pair.** Everything held is
flat-colormap low-poly and several are American types. canon also forbids
real car models, so a recognisable real shape would be a canon violation as
well as a bar risk. A street with no car parked on it is a fine street.

### G. The layer of dirt and paper over everything (9 lines)

| id | what | n | route | source and licence | pri |
|---|---|---|---|---|---|
| G1 | Leak and water staining | 1 | HAVE | ambientCG Leaking005, 2K PNG with opacity and roughness, CC0 | M |
| G2 | Potholes, patches, road scars | 1 | HAVE | ambientCG AsphaltDamageSet001, CC0 | M |
| G3 | Dirt, wear and scratch masks | 5 | HAVE | ambientCG SurfaceImperfections001/003/007/012, Scratches003, CC0 | D |
| G4 | Damp growth at wall feet | 1 | HAVE | ambientCG Moss001, CC0 | D |
| G5 | Stickers and torn paper remains | 1 | HAVE | ambientCG Sticker001, CC0 | D |
| G6 | Fly-posted gig bills and notices | 3 | HAVE | `Decals/generated/*.png`, 640x896, Apache-2.0 weights | D |
| G7 | Period graffiti tags naming in-world crews | 20 | GENERATE 2D | local image generator | D |
| G8 | Litter in the gutter and against wall feet | 1 | GENERATE PROC | scene generator, cards and small primitives | D |
| G9 | Trodden gum on the pavement | 1 | GENERATE PROC | decal generator, dark ellipse at high roughness | D |

**G7 is a gap that closed itself since the research was written.**
`visual-bar-sources.md` (21 August) recorded graffiti as a GAP with no CC0
source found anywhere. The local image generator ran on this hardware on 26
August. The gap is closed by a capability that research could not have known
about, at zero cost, and the tags can name in-game crews, which is a
social-memory tie-in rather than paint.

**G8 was on no list.** A clean gutter in 1990 Britain is the tell that a
street was built rather than lived in.

### H. The air and the light (8 lines, 6 of them not assets)

| id | what | n | route | source | pri |
|---|---|---|---|---|---|
| H1 | Overcast daylight environment | 1 | HAVE | Poly Haven `belfast_open_field_2k.hdr`, CC0, 2K | M |
| H2 | Overcast night with distant urban glow | 1 | HAVE | Poly Haven `kloppenheim_04_2k.hdr`, CC0, 2K | M |
| H3 | Sun elevation, capped at 59 degrees at noon | 1 | ENGINE | each engine's sun, from the JSON date and time | M |
| H4 | The sodium practicals themselves | 4 | ENGINE | lights placed by the generator at the E1/E2 lantern positions | M |
| H5 | Light spilling from lit windows onto wet pavement | 3 | ENGINE | each engine, paired with C11 | M |
| H6 | Wet surface response: darker albedo, lower roughness, reflections | 1 | ENGINE | each engine's material and reflection path, driven by A9 | M |
| H7 | Haze separating near frontage from far street | 1 | ENGINE | each engine | M |
| H8 | Falling rain | 1 | ENGINE | each engine | IF |

**H1 and H2 are a named quality ladder rung, not a problem.** Both are the
2K rung, which is what the original fetch took. A sky fills a large fraction
of an outdoor frame and Poly Haven publishes higher rungs for most HDRIs;
whether these two specific slugs publish 4K is unchecked, and the fetch is
one path segment different if they do. This is exactly the "one field away"
case the standing order names, so it goes on the ladder with a name rather
than being quietly accepted.

**H4 is the reason the light rows are in this document at all.** D1b makes
practical lights at night mandatory scene content. The geometry is E1 and E2,
the light is H4, and if they are not emitted together from the same JSON you
get lamps that glow with nothing lit underneath them, or pools of light under
nothing. The colour is not a choice: low pressure sodium is monochromatic at
589 nm with a colour rendering index of zero, so under it a red car and a
green door are the same amber grey. That is a period marker, a mood and a
simplification at once.

**H6 is where the two engines are most likely to differ**, which makes it the
feature the paired stills are most likely to be decided on. art-direction
R-B5 calls wet ground the Britishness multiplier and the cheapest depth cue
available. It needs A9 to say where the water is.

## 5. THE FINDINGS

All computed from the JSON, on lines rather than on variant counts. The
denominator is stated every time because a percentage of an unnamed set is
the fault this project keeps writing rules about. **Lines is the honest
denominator here; the variant counts are not comparable across lines**, since
one line holds 64 animation clips and another holds one kerb.

### Finding 1: how much of the scene is already in hand

**32 of 71 asset lines are HAVE, which is 45 percent. Of the 38 mandatory
asset lines, 17 are HAVE, which is 45 percent.** Not one of them needs
re-sourcing, and re-sourcing them would be waste.

What that means concretely: every material the scene needs except pebbledash
and a roller shutter (17 surfaces at 2K, colour + normal + roughness, all
ambientCG CC0, all attributed in `ATTRIBUTION.json`); the entire grime and
decal layer (16 ambientCG sets plus 14 locally generated signage images);
both skies; 37 street props already measured, pivoted, LOD'd and licence
tagged by the props-local-01 run; 18 character bodies and 64 animation clips.

**36 of those 37 props are named by a line of this list.** The one that is
not is `lamp_post_01`, and it is named as a MEASUREMENT in E1 rather than as
an asset, for the reason given there. That count is recorded in the JSON as
`held_props_coverage` because a fetched asset no line names is the failure
mode this project keeps finding, and two lines (E18, E19) exist only because
the count was taken.

### Finding 2: how much the free libraries plausibly cover, and where I am guessing

**5 of 71 asset lines are FETCH, which is 7 percent, and all five are marked
NEEDS-CHECKING.** That is the whole of my guessing and it is deliberately
small: A2 (the AO and displacement maps the first fetch skipped), A4 (a
tarmac repair patch), C4 (pebbledash render), C10 (a corrugated roller
shutter), F4 (a period British car).

Four of the five are ambientCG material families and I have not opened
ambientCG's catalogue from here, so I am not asserting that any of them
exists. What I am asserting is only this, and it is checkable: the fetch
ROUTE is proven, because `tools/props/fetch_visual.py` has already banked
files from ambientCG, Poly Haven, The Base Mesh and OpenGameArt into this
repository, with attribution written by the same run, and it re-reads the
CC0 mark at fetch time so a re-licensed page refuses itself.

**Only one of the five is mandatory** (C10, the shutter, and its geometry is
procedural regardless: only the surface is fetched). So even if all five
turn out not to exist, the scene loses one texture and four dressing items.

**One gap in the route that the prep sequence already schedules**: meshgen's
local backend requires `source.kind == "file"` with a repo path. There is no
download stage inside the pipeline, so a FETCH line today means running the
fetcher and then pointing a meshgen spec at what it banked. That is step 3 of
the sequence and this document does not duplicate it.

### Finding 3: what remains that ONLY generation or authoring could provide

**Zero lines out of 71 need image-to-3D. The AMD blocker does not touch this
scene at all.**

The 33 GENERATE lines split into two kinds, and neither of them is the
blocked capability:

| made by | lines | what it costs | blocked by the AMD card |
|---|---|---|---|
| PROC, emitted by the scene generator from the JSON | 26 | nothing. The generator is the thing D1b requires anyway | no |
| 2D, the local image generator already proven on this machine | 7 | nothing, no account, no purchase | no |
| MESH3D, image-to-3D geometry synthesis | **0** | n/a | **not needed** |

This holds for the mandatory subset too: of the 20 mandatory GENERATE lines,
16 are PROC and 4 are 2D.

The reason is structural rather than lucky, and it is worth stating because
it will hold for the next scene as well. Almost everything a British street
is made of is either a run following a path (kerb, gutter, downpipe, railing,
lighting column) or a box with a hole in it (shopfront, door, window, chimney,
kiosk, pillar box). Those are procedural objects. Under D1b's admissibility
rule they must be emitted from JSON anyway, so even a perfect downloadable
kerb model would be the wrong answer. What image-to-3D is genuinely good at
is sculptural one-offs, and this scene has none.

**The consequence for the plan, stated plainly: on the evidence of this list,
no image-to-3D capability is required for the D1b vignette, so queue item 012
stays contingent and does not unblock, no purchase question goes to Jafar,
and no ZLUDA, DirectML, CPU-inference or cloud-GPU work is justified by this
scene.** The prep-sequence ruling predicted exactly this outcome and demoted
the probe on that expectation; the list now supports the prediction with
lines rather than with a hunch.

The one honest caveat: this is a claim about THIS scene. A later scene with a
figurehead, a ship's crane, a carved pub sign or a sculptural shopfront could
produce MESH3D lines, and this finding does not pre-decide that. It says the
question is not on the critical path this week.

### Finding 4: what the scene needs that nobody had thought about

Eleven, in rough order of how much damage each does if it stays unnoticed.

1. **The kerb and the ground it steps up from** (B1 to B4, and A0). Five
   lines, none of which existed in any document. The kerb line is the strongest perspective cue in a
   street photograph and the pavement does not read as a pavement without it.
2. **The lighting column is 3.00 m** (E1, measured). British street columns
   of the period are roughly 5 to 6 m. This decides the entire night frame.
3. **A puddle mask** (A9). Both conditions are wet and no asset says where
   the water is. Wet is not a global multiplier.
4. **What is behind a lit window at night** (C11). The night frame is half
   the evidence and lit windows currently have nothing behind them.
5. **The kiosk and the pillar box carry real marks** (E3, E4). The shapes are
   fine; the lettering and the cypher are not, and canon requires a fictional
   operator that nobody has minted. Both objects also carry essentially the
   whole high-chroma accent budget of the frame.
6. **Drainage as geometry, not just as a decal** (A7, A8, B3). We hold a
   grate and a manhole texture; nothing holds the hole they sit in.
7. **`drain_cover_01` measures 0.10 m across** (A8). Either an inspection
   cover or a mis-scaled export, and the dims policy forbids fixing it by
   guessing.
8. **Four of the fascia images are `review=pending`** (C6). The generated
   manifest's own rule says nothing ships unreviewed. That look has not
   happened and it gates content this scene uses.
9. **The character wardrobe is contemporary** (F1, F2), against a 1988 to
   1992 setting, and there is no free re-dress route.
10. **Litter** (G8). A clean gutter is the tell.
11. **The skies are 2K** (H1, H2), which was the fetched rung rather than a
    chosen one, and a sky is a large fraction of an outdoor frame.

Two more that are not omissions but era traps, recorded in the JSON's
`not_on_this_list_deliberately` block so they are not silently added later:
**tactile paving** (I do not know whether blister paving was normal on
British streets before 1992, so it must be checked before it is placed, not
after), and **wheeled refuse bins** (same class of risk; art-direction asks
for the metal dustbin instead, which is E13).

## 6. How to re-derive every number above

    python3 - <<'PY'
    import json, collections
    d = json.load(open('production/specs/vignette-bill-of-materials.json'))
    a = [i for i in d['items'] if i['route'] != 'ENGINE']
    print(len(d['items']), 'lines,', len(a), 'asset lines')
    print(collections.Counter(i['route'] for i in a))
    print(collections.Counter(i.get('make_by') for i in a if i['route'] == 'GENERATE'))
    print(collections.Counter(i['certainty'] for i in a))
    PY

If that disagrees with anything in section 5, the JSON is right and this
file is stale.

## 7. What consumes this list

Named because the ruling is explicit that a bill-of-materials line nothing
consumes is a wish rather than a requirement:

- **The shared scene JSON** for D1b, and the two thin per-engine generators
  that emit it. Every PROC line is a feature of those generators; every HAVE
  and FETCH line is an asset they reference by id.
- **Step 3 of the prep sequence**, the five-line proof of the CC0
  fetch-clean-tag route. The five FETCH lines here are the natural candidates
  and they are already five.
- **Step 4**, the first full overnight batch, which needs a named target list
  and now has one.
- **The quality ladder** in `production/quality-ladder.md`, which gains three
  named next rungs from this list: HDRIs at 4K, the skipped AO and
  displacement maps, and period wardrobe.
