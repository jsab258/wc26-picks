# The visual bar — GTA V, on Meridian's content: THE PLAN

> **STATUS — SPEC.** Bar set 2026-08-21 (Jafar, twice over hedging; re-escalated
> 25 Aug: *"this goal is a must"*). **PLAN REWRITTEN WHOLE 2026-08-25 by the
> director, on Jafar's third ask for it**, incorporating all six research
> documents under `game-design/research/` (art-direction, procedural-density,
> content-sourcing, performance-budget, inhabited-street, water). The 25 Aug
> R0–R5 plan is ABSORBED, not discarded — mapping in §9; **R0's in-flight batch
> continues unchanged as Part 1, phase 1.** `roadmap.md` M17.10 points here and
> wins on cross-milestone ordering only.

## 1. The decision, and the test this document must pass

Jafar, 21 Aug: *"matches GTA 5 is absolutely the target. it's a 13 year old
game... I want you to really understand what the goal is, think about how we
can get there, do the necessary research, set up a proper plan, and then
build."* And 25 Aug, on this plan: *"Just need to be 100% sure that with this
plan, we incorporate everything that we found out that we need to do to reach
our goal, and that we can actually do it."*

So this file answers two questions and nothing else: **what does "GTA V's
perceived quality on a British port town" CONSIST of** — six parts, §2 — and
**can we execute each part** — where we stand (measured), what we do, what
proves it, what it costs, roughly how long. Unchanged underneath: the setting
(late-analog 80s/90s), the moat, no purchases, no accounts, the noir mood
delivered by grade rather than by absence.

**CAN WE AFFORD IT — answered first, because it gates everything (from
`research/performance-budget.md`, all [MEASURED] unless noted):** the
roadmap's old "only live red" (`game=17.55ms` vs 12ms) was stale, from the
GPU-less cloud runner. On Jafar's PC the gate reads **`game=6.29ms`** (verified
against the landed verdict at `36b90c9` this session), in a 6.10–6.71ms band
for 31 runs, last red 65 runs ago. The 12ms budget gates game SYSTEMS;
rendering is ungated (`render+rest=22.29ms`), and the governing number is
**`meanFrame=28.58ms` at 720p ≈ 35fps — already inside GTA V PS3's own
30fps/720p envelope with ~4.7ms of margin.** The plan's summed frame cost is
small (per-part rows below) and four structural savings are entirely untaken:
`CombineMeshes`/`StaticBatchingUtility`/`isStatic` have ZERO hits in the whole
project (the town is runtime-built, so static batching currently does
nothing), and `shadowCascades=4` submits every casting prop five times. The
real ceiling is MEMORY, and its biggest item is one line
(`DecalLayer.cs:467` loads RGBA32+mips, ~22MB a set, 14 resident, `Compress()`
never called — a 4× cut). **The plan is affordable. Feasibility is not a
risk; memory discipline and the ungated render number are, and both are
printed per phase.**

## 2. What the goal consists of — six parts

From the five reference frames (committed byte-exact in
`game-design/reference/` — they are the bar), decomposed and then MEASURED
against our seven district stills:

| part | what it is | where we stand, in one measured fact |
|---|---|---|
| **P1 — LIGHT & COLOUR** | the frame is lit right: bright sky, dark water-marked ground, warm/cool separation, British sun and weather | **totally separated from the references on four independent statistics, all one cause** (§P1) |
| **P2 — SURFACE HISTORY** | no surface one flat tone: road scars, markings, streaks, grime, weathering | ground-band surface variety below every reference on 5 of 7 stills |
| **P3 — DENSITY, DEPTH & STRUCTURE** | furniture, wires, facade rhythm and recess — a street that reads as decided | 25 placeable furniture models on disk, ONE placed; wires are two straight cubes; placement is anchor-less scatter |
| **P4 — THE INHABITED STREET** | people, vehicles, windows read as lived-in | six of the eleven top items are FINISHING A WIRE on something built and tested |
| **P5 — THE PORT** | the water and the tidal edge | nothing renders water; the "sea" is the sky dome's underside, luma std 0.0032, the bluest thing in a dockside frame |
| **P6 — LETTERING & CONTENT** | words on the town, period content, the asset pipeline that feeds P2–P5 | signs carry their words in data and render as blank coloured cubes |

Cross-cutting, not a seventh part: **the convergence instrument** (§3) —
because converging on a target you never photograph is unmeasurable, and every
part below closes on ITS numbers plus a paired still.

## 3. HOW WE KNOW — the instrument (ships with Part 1, not after)

- **Five player-height cameras** (~1.7m, ~60° vfov) matched to the five
  reference compositions, committed every run as `ref_1..ref_5`. Every
  reference is shot at eye level; today not one judgement still is. Aerials
  stay for audits only.
- **`ref-bench.py` gains the six separating statistics** from
  `research/art-direction.md` §7 (`skyOverGround`, `v3which`, hue arc,
  `warmSplit`, saturation shape, night variants) — one instrument over refs
  and stills, never two. Bounds are reference EXTREMES, never invented; regime
  marks when R0-class changes land.
- **Five hand-painted reference mattes** (approved 25 Aug) so magnitude
  becomes quotable, not just direction.
- **The convergence test:** at every landing, read the five pairs and write
  the biggest visible difference in one sentence. The panel moving toward the
  reference side while the sentence keeps changing = converging. **The same
  sentence three landings running = this plan is wrong at that point,
  whatever it says.** Final judge: Jafar, our frame beside his frame.

## 4. THE PLAN, part by part

### P1 — LIGHT & COLOUR *(first, because nothing else is judgeable on an inverted frame)*

**Stand [measured, art-direction §1]:** four total separations, one cause —
an ambient that is blue, flat, and applied to everything. Sky/ground ratio:
refs 1.35–5.79, ours 0.54–1.25 (7/7 wrong). Palette arc: every ref amber
30–50°, five of ours BLUE 220–230° — **the blue is our ambient, not our
content**; a British port's own materials (brick, rust, tarmac, sodium) all
sit in the amber arc already. Warm/cool split: refs ≥0.079 in magnitude, ours
never past 0.060. Mid-grey dominance: no ref is mid-dominant, five of ours
are. Detail painted onto this frame cannot be seen — hence first.

**Do:** (a) **R0 as already ruled** — the in-flight attribution batch
(`decision-ground-albedo.md` order stands), then the fix the A/B names, the
aperture set ONCE off the post-fix series, bright overcast dome (CIE overcast
is zenith 3× horizon — a bright sheet, not a storm ceiling), windows reading
the real environment. (b) **Palette + temperature**: grade/ambient parameters
until the arc and warmSplit gates pass — parameters, not content. (c)
**Britain, three parameter changes**: noon sun clamped ≤59° elevation
(arithmetic: 54.5°N never sees a Los Santos sun; long shadows are CORRECT
here), weather draw ~2:1 overcast-or-wet vs dry-sun (UK ≈1,403 sunshine hours
— **overcast is our DEFAULT frame**, so reference frame 3 is the one that
matters most), and sodium night (SOX is CRI 0, monochromatic 589nm — period
marker, mood, and a simplification at once; night bounds set from a printed
series after the lamps are tinted).

**Gates (reference-derived, magnitude never sign):** `skyOverGround>=1.35`;
`v3which!=mid`; `hueArcAt` in 15..60° with `hueArc60>=0.55`;
`abs(warmSplit)>=0.079`; `satP50>=0.159`, `satP99<=0.758`; `sunElevNoon<=59`;
`weatherDrawn` counts printed. Plus the R0 ordering gate: sky > lit wall >
ground > shadow, and ground lumas ordering as their albedos do.

**Cost:** ~0ms — parameters and grade. **Time: days** (a handful of landings;
R0 already in flight).

### P2 — SURFACE HISTORY *(ground work after R0.b — invisible on a clipped ground; wall work startable now)*

**Stand:** reference frame 3 proves dirt+depth+density carry a frame with no
interesting light. Our carriageway is one tile; our decal placement is a
seeded roll that knows nothing about doorways; fetched textures are never
albedo-validated; decal textures are uncompressed in memory.

**Do, in order of impact-per-hour [procedural-density §2, §4, §6]:**
1. **`Compress()` on decal load** — immediate, one line, 22.4→5.6MB a set.
2. **British road markings from the real TSRGD numbers** — 75mm double
   yellows (gap = line width), zebra stripes 500–715mm, give-way 500/500mm,
   centre line 4m/2m. Pure arithmetic, ~150 lines in Core, no asset, and every
   junction reads as Britain.
3. **Ground scars by anchor**: gutter grime strip along every kerb, tar seams
   at centre/kerb joints plus perpendicular service-trench scars, patch
   rectangles at junction mouths, oil where traffic idles, worn markings in
   the wheel tracks. Decals combined per block (`CombineMeshes`) — the PS3
   answer; `decalOverlapWorst` printed so overdraw cannot land as a mystery.
4. **Vertex-colour weathering** written at generation (R contact / G exposure
   / B wear) + one surface shader: every wall base, corner and join in town
   darkened at zero draw calls. Priced honestly: one shader + a mesh-copy
   pass, shared with the CombineMeshes work — built in the same batch.
5. **Wall history**: poster stacks (3–6 overlapping, torn edges — one poster
   is a sign, six are time passing), streak decals below every sill and
   parapet (we place the ledges, so we know them), rust below every fixing,
   moss by the damp-dark rule.
6. **Albedo validation at ingest** — reject/correct any fetched base colour
   with P05 < 30 or P95 > 240 sRGB; the root cause of asset clash, offline
   Python, runs once per asset. Ships `texturesClamped/texturesExamined`.
7. **Detail maps** on brick/asphalt/paving/render — free close-up grain in
   the Standard shader, one material field.

**Gates:** ground-band tonal spread toward the mattes; a paired still showing
three distinguishable tones on one carriageway; `markingKinds`,
`vertexDirtWritten/total`, `decalOverlapWorst`, `texturesClamped/Examined`.
**Cost:** +0 to +0.3ms combined-per-block; memory FALLS after item 1.
**Time: 1–2 weeks**, largely automatable.

### P3 — DENSITY, DEPTH & STRUCTURE *(startable NOW as ride-along visible work)*

**Stand [procedural-density §0]:** `city-kit-roads` holds 25 placeable
furniture models (lamps, signals, signs, cones) with ONE placed, plus 9
suburban fence panels; overhead cables EXIST (`BuildOverheadCables`,
`BuildTelegraphPoles`) but as two straight cubes per span, no dropwires, no
aerials; facades are boxes; placement is `Roll < 0.55` scatter, which cannot
read as placed because nothing in it knows what a doorway is.

**Do:**
1. **Placement rules move into Core as pure tested functions** — the one
   architectural change that makes everything else cheap: rules become
   CoreTests that run in seconds instead of 28-minute round trips, plus a
   top-down SVG preview tool needing no Unity. First, in the same batch as
   the first furniture pass.
2. **Anchor vocabulary + recipes**: scatter over ANCHORS (kerb line,
   furniture zone, shop door, service door, alley mouth, junction corner,
   party wall, quay edge), never over area. Leader/follower clustering
   (co-locate within 2m, align to one kerb offset ±0.05m, reserve the
   1.2–1.5m desire line — which is also `NpcWalker`'s strip). The
   Spider-Man shape: minimum separation, alternation, keep-out from a named
   feature. Recipe numbers tuned from the preview tool, never invented into
   gates.
3. **Wires as ONE combined mesh** — parabolic sag (exact within 0.5% at our
   spans), dropwires fanning pole-to-eaves, **TV aerials on every chimney**
   (the single most period-specific silhouette available), washing lines,
   catenary lamps on the narrow lanes, ~1.2px width clamp. The sky is P1's
   brightest band; wires are the only thing that puts structure into it.
4. **Facade grammar with terrace-level coherence** — vary per TERRACE
   (brick, bay, pitch, storey height identical for 5–12 houses: one builder
   built them), vary per HOUSE only what residents did (door colour,
   curtains, boundary). British numbers: frontage 4.5–6m, storey ~2.9m.
   **Recess depth**: shopfront 0.3–0.6m, door reveal 0.12–0.2m, window
   reveal 0.1–0.15m — four quads each, the highest visible-depth-per-triangle
   in the plan.
5. **The Britishness accents** — K6, pillar box, Belisha beacon: authored
   primitives (no CC0 source exists; that is fine, they are boxes and
   domes), the mandated identical high-chroma objects that give a low-chroma
   street its 60-30-10.
6. **Areas of rest** — at least one span per block at primary+secondary
   detail only. The tax on proceduralism: uniformly dressed streets read as
   wallpaper.

**Gates:** `propsByAnchor` (did the RULES fire, with denominators),
`furniturePer50m` median+peak, `propsRejectedClearStrip`, `wireSkyCover` per
ref still, paired stills. **Cost:** +0.3–1.2ms at planned counts IF the
structural moves land with it (`shadowCastingMode=Off` on small props — at 4
cascades a casting bin is drawn five times). **Time: 2–3 weeks**, the widest
part; the Core move is what keeps it honest.

### P4 — THE INHABITED STREET *(early, cheap, and where the eye goes first)*

**Stand [inhabited-street §1]:** the systems exist; the wires don't reach.
`RealBody` washes ONE colour over every renderer INCLUDING THE HEAD —
`BodyParts.Assign` (Core, tested) is never called on the textured path, so
nobody can have a navy coat and stone trousers and the eight-band period
wardrobe collapses to a tint. `walk_f` is unwired — **every woman walks the
male cycle** — and six locomotion transitions sit unused among 41 unreferenced
clips. Headwear is computed for everyone and read only by the superseded
mannequin tier. Windows are NOT the assumed fault: 4,188 windows with real
occupancy, 2,477 lit at 23:00, 122 built shop interiors — **the fault is
DAYTIME glass**, near-black gloss with nothing behind it. Vehicles: right
palette, one anachronism (SUV), no plates, one uniform finish.

**Do — the ranked eleven, most of them wires:** split the body wash
(flesh/cloth, coat/legs — second wardrobe draw, arithmetic in Core); wire
`walk_f` + the six transitions; cool the shopfront emissive vs warm flats
(one line, an existing branch — the British dusk in one edit); daytime glass
by transfer series (brighter base + metallic so the bound HDRI reads) + a dim
warm interior value; headwear on the skinned tier; curtains/blinds from the
existing occupancy hash; period number plates (`A123 ABC`, white front /
yellow rear) via the shipped `LedgerText`; drop `car_kit_suv` + add the pale
metallics and one loud colour; idle variety 4→7–8 (fetch `smoke`/`thinking`,
which `NpcWalker` already asks for and is refused 43 times a run);
per-vehicle gloss+dirt; hand props for the carry clips.

**Gates:** `bodyDressed>0` with the parts split named; clip-reach 41→0
unreferenced or ruled; stills. **Cost:** ~0ms, measured — the whole crowd
(80 rigs, ~1M skinned verts) costs ~0.6ms; nothing here adds a `Light`.
**Time: days to ~1.5 weeks.**

### P5 — THE PORT *(early: it is a whole-frame void in the two seaward frames)*

**Stand [water §0, measured]:** no water shader, no plane, nothing. The
region south of the quay is the sky dome's lower hemisphere: monotonic
gradient, luma std 0.0032, saturation 0.331 against the land's 0.082 — the
most saturated, bluest thing in the shot, exactly backwards for a British
port. The world model already knows where the sea is; nothing renders it.

**Do:** W1 **opaque plane** at `GroundMinZ` (same constant, never a second
number), two-stop dark ramp, Fresnel to the sky's own horizon colour — 60% of
the job, because it replaces a hole with a surface; W2 analytic sine-sum
normal perturbing ONLY the reflection vector into `unity_SpecCube0`
(**already bound, already paid for** — precisely GTA IV's method, one
generation below our bar); W3 horizon delta; W4 analytic brown scum band at
the wall (world-space arithmetic against the straight quay — no depth
texture; and never white surf, which is a beach marker). Then the shore:
**tide/lichen five-stop band on quay walls — zero ms, and it says "tidal
port" better than the water does**; wet-dark stone below the line (mechanism
exists, needs pointing); mooring clutter; boats later. Turbid harbour water
is opaque and reflection-dominated, so everything expensive is also wrong
here — the cheap technique is the correct one.

**Gates:** `waterLuma`/`waterSat` below the land's; `waterStd` peak+median;
`shoreGap` per edge with the datum check; `waterMs` A/B before any bound;
and the first act after landing is opening `district_ironside.jpg`.
**Cost:** ~0.2–0.5ms estimate, measured before believed. **Time: days.**

### P6 — LETTERING & CONTENT *(parallel — most of it runs offline, no CI)*

**Stand [content-sourcing §1]:** `NeonSigns` carry `(place, colour, word)`
and render the word as nothing; no fascia text exists; everything is fetched
at 2K with 4K free one URL-field away; `.glb` is invisible to the attribution
sweep; **no `.meta` files ship, so Unity's default 2048 cap applies — an 8K
source imports as 2K and changes nothing.**

**Do:**
1. **The signage generator** — Pillow + OFL fonts (verified fetchable from
   here) + our own words: shop fascias for every `HasFascia` premises,
   lettered neon, poster stacks (gig bills, ferry timetables, union
   notices), official notices, street and pub plates. The single highest
   impact-per-hour item in the sourcing research; no licence question at
   all. Ships `signsLettered=` with ground truth.
2. **OGL traffic signs** — 600+ official UK signs as vector, rasterised at
   any size in CI, attribution written by the job that writes the files.
3. **Resolution done right: the `AssetPostprocessor` FIRST**, then 4K on a
   NAMED short list of eye-level surfaces. **8K is CUT** (§7).
4. **Poly Haven textures and models** beyond the four HDRIs we take today;
   OGA industrial/harbour packs for the dockside; `.glb`/`.gltf`/`.svg`
   into `ASSET_SUFFIXES` in the same change.
5. **Generated images at rung 4 — APPROVED by Jafar this session**: a
   permissively-licensed model run locally on his PC, set up as **one click
   ("ideally just a 1 click bat")** — a builder is producing that now, on
   the voice-pipeline precedent (his machine runs a bat, outputs are
   committed). Scope: painterly one-offs — ghost signs, pub signs,
   illustrated adverts — NOT fascias (Tier A does those better) and NOT
   tileables (real CC0 photos beat hallucinated brick). **Licence
   discipline, absolute:** no identifiable real person, no real trade
   marks, in-world brands only (they feed social memory anyway — better
   content, not just safer); every image human-reviewed; recorded in
   `THIRD-PARTY.md`'s "generated by us" section with model, licence,
   training-data claim, review date.

**Time: days** for the generator and signs; the image phase runs parallel on
his machine and does not block anything.

## 5. ORDER — and why not the other order

Execution waves (each wave = batched dispatches, every dispatch shipping at
least one visible change unless a red gate blocks it):

1. **Now, in parallel:** P1 (R0 batch in flight) + the instrument (§3) +
   P4's wires + P5's W1/tide band + P6's signage generator + the two
   one-liners (Compress, SUV). First visible transformation of the frame.
2. **Next:** P2 ground work (unblocked once R0.b lands), P3 placement-in-Core
   + first furniture/wires/markings pass, P6 postprocessor + 4K short list.
3. **Then:** P3 facade grammar + accents + rest-areas; P2 wall history at
   scale; P5 moorings/boats; convergence iterations against Jafar's eye
   until the sentence stops finding new biggest-differences.

**Why not detail first?** Detail on a value-inverted frame is invisible —
measured, not asserted (P1's four separations). **Why not water later?** It
is a whole-frame defect in two of seven frames, and dressing the edge of a
void draws the eye to the void. **Why people this early?** Six items are
wires on tested systems at ~0ms — the highest finished-value-per-hour on the
board — and a person is what the eye lands on first. **Why is P3 the long
pole and not pulled forward whole?** Its yield depends on the placement rules
being tunable in seconds, so the Core move must land first or every rule
costs half an hour to see.

## 6. TIME — hours versus weeks, honestly

- **Hours:** Compress(), SUV drop, shopfront emissive, sun clamp, weather
  mix, `.glb` in the sweep.
- **Days:** P1 to its gates; P4's eleven; P5 minimum; P6 signage.
- **1–2 weeks:** P2. **2–3 weeks:** P3 (the widest part).
- **The whole plan to "Jafar puts our five frames beside his five and calls
  the bar met": 4–7 weeks of continuous work, medium confidence.** What
  dominates is not build effort: it is (a) the number of convergence
  iterations against his eye — unknowable in advance, which is why the
  instrument exists — and (b) CI round trips (~17 min on his runner,
  batched). What does NOT dominate, because it is answered: the frame budget
  (§1), asset availability (everything is on disk, fetchable free, or
  generated), engine capability (every technique is Built-in-forward with a
  precedent in this repo). If the CC0 ceiling binds anywhere (vehicle
  meshes are the likeliest), we say so rather than stretch.

## 7. WHAT WE ARE DELIBERATELY NOT DOING, and why

| not doing | reason, measured or sourced |
|---|---|
| **Deferred rendering / URP / HDRP** | built-in forward accepted 21 Aug; pooled sodium lamps fit the town; Built-in is also where all nine of our shaders live |
| **Planar reflection camera** (water or wet ground) | a second full scene render, ~+15ms — the one item that could double the frame. GTA IV didn't either |
| **Depth-texture shoreline, refraction, Gerstner, flow maps** | each buys a property turbid enclosed harbour water does not have, at up to a scene render each |
| **8K textures** | cannot land (no `.meta` files → imports at 2048) and shouldn't: GB of repo and VRAM for a difference invisible at street distance. 4K on a named list, postprocessor first |
| **Photogrammetry** | no camera, no site; archive photos are single-view and in copyright. CC0 scan libraries + albedo validation are the same asset class done legally |
| **Interior mapping** (rooms behind glass) | ranked LAST measured against our small sash windows; 122 geometric shop interiors already do the job at street level. Named as the next rung on the ladder, not built |
| **Wave Function Collapse** | our city already has the global structure WFC lacks; only its adjacency-table idea survives (30 lines, facade modules) |
| **Hex-tiling, LOD groups** | 2018+ technique / wrong constraint; era-correct answers (detail maps, vertex colour, decals, CombineMeshes) come first — revisit only if the ground still reads tiled after they land |
| **Real brands, real people, period ad artwork** | trade mark law is where Getty's only wins landed; 1980s artwork is in copyright for decades. Meridian's brands are Meridian's — and feed the moat |
| **Standard Assets, Asset Store, any account, any purchase** | standing project rule; also Water4 is deprecated anyway |

The old "looking unmistakably worse, and at peace with that" framing stays
retired — it was a licence for unfinished, not a trade.

## 8. Risks, named

- **Convergence-iteration count** is the honest unknown in §6's range.
- **The CC0 ceiling** on vehicle/character meshes — say so where it binds.
- **Instrument gravity** — the 25 Aug failure mode (a week of measurement,
  one visible change) recurs unless the cadence rule holds: every dispatch
  ships a visible change or names its red gate. A violation is a plan
  violation, not a judgement call.
- **Memory** — the one budget axis that was drifting (uncompressed decals);
  fixed by wave-1 one-liner, watched per phase thereafter.
- **A no-GPU runner never judges** — stills judged from `ledger-pc` builds.

## 9. LOG — what this replaced, so nobody re-derives it

- **V0–V6 (21 Aug)** replaced 25 Aug: correct decomposition, wrong execution
  (presence-numbers for done-states, no owner for value structure, aerial
  judgement frames). Content mapped V2→P2, V3→P3, V4→P3, V6→P1, V0/V1→P1/§3.
- **R0–R5 (25 Aug morning)** absorbed same day into this decomposition on
  Jafar's demand for the full plan: R0→P1 phase 1 (batch in flight,
  unchanged), R1→§3, R2→P2, R3/R4→P3, R5→P1c. Nothing in flight was
  invalidated; this file added the parts R0–R5 did not cover (people,
  vehicles, water, lettering, the budget answer) and the time shape.
- **Technique scorecard and asset tables** live in `roadmap-history.md`-class
  detail inside the six research docs and `visual-bar-sources.md`; this file
  no longer duplicates them.
