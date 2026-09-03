> **STATUS: SPEC, 2026-08-25.**

# Can we afford the visual plan?

**Short answer: YES, conditionally.** The binding constraint is not the one
the roadmap names, and the one the roadmap names is stale.

Every number below is tagged **[MEASURED]** (read off our own landed
verdicts or read out of the code at HEAD), **[INFERRED]** (a mechanism
argument from a measured number), or **[GUESSED]** (order of magnitude, no
support). No bound is set or moved anywhere in this document — rule 2. Where
a rung is missing to settle a question, the missing rung is named rather
than a number invented to fill it.

---

## 0. The four findings that decide it

1. **The 12ms budget does not govern rendering.** It gates `attributed` —
   the sum of `Perf.Time` scopes around game SYSTEMS (`sun`, `mix`,
   `population`, `bodyLod`, `npcs`, `checks`, `traffic`, `signals`).
   Rendering lands in `render+rest`, which **has no gate at all**. Every
   item in the visual plan spends `render+rest`. **The visual plan is
   almost entirely outside the budget it is being checked against.**
2. **The roadmap's "only live red" is stale by a machine change.** It says
   `game=17.55ms ... failing 28 of 141`. Landed today: `game=6.29ms`, and
   `tools/gates.py --flaky` puts the frame gate's last failure **65 runs
   ago**. The 17.55ms readings are from the GPU-less GitHub runner era;
   builds have run on `ledger-pc` since 22 Aug and `game` has sat in a
   6.10–6.71ms band for the last 31 runs. **We are at ~52% of the game
   budget, not 46% over it.**
3. **The real number is `meanFrame=28.58ms` at 1280x720**, and it has no
   stated target. Two thirds of it (`render+rest=22.29ms`) is render.
4. **Density is nearly free at our current scale and the cheap structural
   savings are all still on the table.** `Mesh.CombineMeshes`,
   `StaticBatchingUtility`, `LODGroup` and `isStatic` appear **nowhere in
   the project** — grepped at HEAD, zero hits. The plan's cost can be paid
   out of work we have not yet done.

---

## 1. What IS the budget, and is 12ms the right number?

### Where it came from — sourced, not remembered

`SimDirector.cs` (~line 12925), `const double GameFrameBudgetMs = 12.0`,
with `frameOk = meanFrameMs <= 0 || attributed < GameFrameBudgetMs`.
The comment above it states the derivation verbatim **[MEASURED — read at
HEAD]**:

> `6.00ms of game systems against a 16.67ms frame at 60fps is the real
> budget, and 12ms — under three quarters of that frame, twice what was
> measured — is a ceiling a genuine regression crosses and runner noise
> does not, because runner noise lands in the residue.`

So it is **a regression tripwire on CPU game logic, set at 2x the measured
value**, targeting 60fps notionally, on the GitHub CI runner. It is
honestly derived and it is honestly labelled in the code.

### It is the right number for what it does, and the wrong number for this question

- **What it governs is not what the plan spends.** `attributed` covers
  eight `Perf` scopes, all of them simulation. Adding props, decals, wires,
  textures, water and interior cards moves `render+rest`. A visual plan
  checked against the 12ms gate is checked against a gauge wired to a
  different pipe. **[MEASURED]**
- **Its own comment already retracts half of it.** Eight consecutive runs
  are printed in the file showing `attributed` swinging 11.4–15.7ms —
  either side of the ceiling — while `gameShare` held at 2.6–3.4%. The
  comment's conclusion: *"a red here currently says 'this runner was slow',
  and that is the instrument being wrong rather than the subject."*
  **[MEASURED]**
- **It has survived a regime change without being re-asked.** `gameShare`
  reads 3% → 18% → 20% → 26–28% → **22.01%** across the series; `meanFrame`
  reads ~300–1000ms → ~25ms → **28.58ms**. That is the move from a software
  rasteriser to Jafar's GPU. A bound set when the game was 3% of the frame
  is being read on a machine where it is 22%. It has not gone red once
  since. **[MEASURED — `gates.py --series gameShare`, `--series meanFrame`]**

### The budget that is missing

There is no render budget and no whole-frame budget. `meanFrame` is
printed every run and gated on nothing.

**The reference answers the target, and it answers it well.** The stated
bar is GTA V on PS3 (2013), which shipped **30fps at 1280x720**
**[EXTERNAL — reference knowledge, not measured here]**. Our capture path
renders at exactly 1280x720 (`SimDirector.cs:293`, `new RenderTexture(1280,
720, 24)`) **[MEASURED]**. At 28.58ms we are at ~35fps at the reference's
own resolution — **already inside the reference's frame budget, with about
4.7ms of margin to a 33.3ms/30fps line.**

**Do not turn that into a gate today.** The stated bar is a LOOK, not a
frame rate; Jafar has never named a frame-rate target; and `meanFrame` is
measured on a build that renders through a `RenderTexture` for screenshots,
not on a player's display, at a resolution the shipping game may not use.
Setting 33.3 from this paragraph would be exactly the invented threshold
rule 2 forbids. What is supportable is the SHAPE: **`meanFrame` is the
number the plan spends, it currently sits at 28.58ms/720p, and the honest
next step is to print a series of it against a stated resolution before
anyone sets a bound.**

**Verdict on item 1: the 12ms budget is sound for regression-catching CPU
logic and irrelevant to this plan. The roadmap's "at risk" entry is stale
and should be rewritten. We are not 46% over anything.**

---

## 2. Where the frame actually goes

### The instrument, and what it can and cannot say

`ProbeFrameCost` (`SimDirector.cs:8509`) renders one frame per suspect with
that suspect disabled, median of three, at the **day1_noon** shot. Its own
docstring is correct and load-bearing: *"the absolute values are inflated
by the probe's own RenderTexture and ReadPixels — that overhead is CONSTANT
across rungs by construction, so the DIFFERENCES are the reading and the
absolutes are not comparable with `meanFrame`."* **[MEASURED — read at
HEAD]**

The brief quotes one run's ladder. One render is a sample. Below is the
**per-run paired difference `all − rung`, medianed across the 39 landed
runs that carry the full seven-rung ladder** — paired, so runner speed
cancels, which a cross-run comparison of absolutes would not.

| rung | median saving | mean | sd | positive in | reading |
|---|---|---|---|---|---|
| `noShadow` | **+5.80ms** | 5.81 | 0.84 | **39/39** | real, large, the biggest single item |
| `noPixLights` | **+4.60ms** | 4.84 | 0.99 | **39/39** | real, large |
| `shadow45` (70m→45m) | +0.70ms | 0.68 | 0.87 | 32/39 | **inside the noise** |
| `noPost` | +0.80ms | 0.67 | 1.02 | 27/39 | at the noise floor |
| `noBodies` | +0.70ms | 0.61 | 0.67 | 31/39 | at the noise floor |
| `noShafts` | +0.00ms | 0.20 | 1.15 | 19/39 | **indistinguishable from zero** |

**[MEASURED — 39 runs under `game-design/sim-shots/runs/`, paired
differences, median and sd computed per rung]**

**The probe's own noise floor is ~±0.7–1.15ms (sd).** Three rungs sit
inside it. Only two rungs are resolvable: shadows and per-pixel lights.
Anything the visual plan does that costs under ~1ms **this instrument
cannot see at all**, which is a fact about the plan's checkability, not
about its cost.

### The `noBodies` inversion, explained

The brief reports `noBodies:23.3` against `all:22.4` — hiding the crowd
made the frame slower. **That was one run's noise.** Across 39 paired runs
the crowd's saving is **+0.61ms mean, sd 0.67, positive in 31 of 39** — a
small positive cost with a spread wide enough to go negative one run in
five. It is exactly what a ~0.6ms signal looks like through a ±0.7ms
instrument. **[MEASURED]**

The finding underneath survives and is stronger than the brief states:
**80 rigs and 998,766 skinned verts cost about 0.6ms of render.** The crowd
is not in the bill. **[MEASURED — `bodies[rigs=80...]`,
`skinnedVerts=998766`]**

### The trap in "shadows 5.8 + lights 4.6 = 10.4ms"

**Do not add them.** `r(noShadow, noPixLights) = +0.50` across the 39 runs
**[MEASURED]** — the two savings covary, which they would not if they were
independent money.

The mechanism that fits the signs **[INFERRED]**: `QualitySettings.shadows
= Disable` removes both shadow-map GENERATION and shadow APPLICATION;
`pixelLightCount = 0` removes per-pixel light evaluation, and a light that
is not per-pixel applies no shadow — so it removes application only. That
predicts `noShadow > noPixLights` (5.80 > 4.60, correct) with a shared
overlap term. **There is no rung with both off, so the union is somewhere
between 5.8 and 10.4ms and cannot be pinned from the landed data.** Naming
that gap is more useful than picking a number in it.

### What the 4.60ms of per-pixel light actually is — the open question

`pixelLightCount = 8` (`SceneLighting.cs:111`) **[MEASURED]**. At the noon
shot where the probe runs, **street lamps and neon are both disabled** —
`klight.enabled = false` at construction (`WorldBuilder.cs:3492, 3510`),
`TickNeon` sets `l.enabled = false` for every neon when not night
(`WorldBuilder.cs:435`) **[MEASURED]**. The `lamps=8` in the verdict is the
count of built lamps, not lit ones.

So the lights actually enabled at noon are: **the sun (directional), one
`Bar_Light` point light (`WorldBuilder.cs:2116`, no disable), and up to
four `SpawnGlowMarker` point lights** — the dispatch board, the shift stop,
the beat marker and the job drop (`GameController.cs:3213`, each `range=7`,
`intensity=2.2`, no disable). **[MEASURED — read at HEAD]**

**Which of those carries the 4.60ms is not determined by the ladder**, and
the difference matters enormously:

- if it is the sun, the saving is **not winnable** — nobody ships a
  vertex-lit street;
- if it is the bar light and the four gameplay markers, then **~4.6ms of
  our frame is being spent on quest markers**, and it is the largest single
  piece of free headroom in the project.

`Light.renderMode` is **never set anywhere in the project** — grepped, zero
hits — so every one of those point lights is `Auto` and eligible for a
per-pixel slot. **[MEASURED]**

**The rung that settles it costs one line in `ProbeFrameCost`:** disable the
non-sun lights and re-time, or set `pixelLightCount = 1` rather than 0.
That is the single highest-value measurement on this board and it is not a
guess about which answer it will give.

### The rest of the frame

`render+rest = 22.29ms`, of which the ladder resolves ~5.8 (shadows) and
~4.6 (per-pixel lights, overlapping). **The remaining ~12–16ms is
unattributed** — base-pass geometry, the skybox, fog, the post stack's
un-resolvable ~0.7ms, and the probe's own RenderTexture overhead. **The
ladder cannot see inside it.** Saying otherwise would be the guess that
already died three times against this instrument (draw calls, vertex
budget, shadow reach). **[MEASURED — by subtraction; the residue's contents
are UNMEASURED]**

### The empirical price of density — the most useful number here

Split the 46 frameCost runs by scene size **[MEASURED]**:

| band | n | `sceneRenderers` | ladder `all` | `meanFrame` |
|---|---|---|---|---|
| low | 14 | ~19,796 | 22.1ms | 26.99ms |
| high | 16 | ~22,137 | 25.4ms | 28.59ms |

**+2,340 renderers (+12%) coincided with +1.59ms of `meanFrame`** — about
**0.68 microseconds per scene renderer**.

Treat that as an **UPPER BOUND [INFERRED]**: other things changed across
those runs, so some of the 1.59ms is not the renderers. But it is our own
landed data, it is the right shape (a marginal cost per object), and it is
the only empirical price-per-object this project has.

---

## 3. Pricing the plan

Baseline for every row: `sceneRenderers=22615`, `propsPlaced=1159`,
`meanFrame=28.58ms` at 720p. **[MEASURED]** Costs are against `render+rest`
unless stated; **none of these rows spends the 12ms game budget** except
where a `Perf` scope is named.

| item | frame cost | confidence | which budget | notes |
|---|---|---|---|---|
| **Street furniture, +hundreds of static props** | **+0.2 to +0.7ms** for +300–1000 renderers | **medium-high** — derived from our own marginal price, upper-bounded | render, and shadow-caster count | The largest risk is not the base pass. Each shadow-casting prop is drawn **once per camera + once per cascade = 5 draws** with `shadowCascades=4` **[INFERRED from `casc=4`]**. Set small props' `shadowCastingMode = Off` and this row is nearly free. |
| **Decals at street scale, thousands of quads** | **+0 to +0.3ms if combined per block; +2 to +4ms if each is its own GameObject** | **medium** | render (overdraw), **and VRAM — see below** | `LedgerDecal` is `Blend DstColor Zero, ZWrite Off, Offset -1,-1` **[MEASURED]** — cheap per pixel, but **pure overdraw**, and overdraw is the cost that does not show in a draw-call count. The research doc's own warning is right. **`CombineMeshes` per block makes the geometry free; nothing makes the overdraw free.** |
| **Decal TEXTURE memory** | **~22MB of VRAM per 2K set, uncompressed** | **high — read at HEAD** | **memory, not frame** | `DecalLayer.cs:467`: `new Texture2D(2,2, TextureFormat.RGBA32, true)` + `LoadImage`, and **`Compress()` is never called** — grepped, zero hits. A 2K RGBA32 with mips is 2048²x4x1.33 ≈ **22.4MB each**. 14 sets are already loaded (`decalWhy=[14_set(s)]`). **This is the plan's real memory risk and it is one line to fix** (`tex.Compress(true)` → DXT5, ~5.6MB, a 4x cut). |
| **Overhead wires as ONE combined polyline mesh** | **+0.0 to +0.1ms** | **high** | render | One mesh, one material, one draw call, a few thousand verts. This is the cheapest visible-density item in the whole plan. Sag is vertex positions at build time — free. The ~1.2px width clamp is a vertex-shader op on a tiny vertex count — free. |
| **2K → 8K textures on eye-level surfaces** | **frame: ~0. memory: catastrophic. AND IT WILL NOT LAND AT ALL AS WRITTEN.** | **high on the blocker** | memory + bandwidth | See below — this row has a hard blocker before it has a cost. |
| **Vertex-colour weathering ("zero draw calls")** | **frame: ~0. BUT the zero-cost claim is only half true.** | **high** | render ~0; **CPU build time and mesh memory NOT zero** | See below. |
| **Procedural facade grammar** | **+0.1 to +0.5ms** per +500–1500 renderers | **medium** | render + shadow casters | Same price as street furniture. The cost is in renderer COUNT, not triangle count — `skinnedVerts=998766` costs 0.6ms, so triangles are not our constraint. **Generate facade detail as merged per-building meshes and this is close to free.** |
| **Extra render arm for the graded/raw A/B** | **+15 to +60ms of PROBE time, once per run, at one shot** | **medium** | **neither — dispatch time, not shipped** | Correct instinct: this is instrument-only. **But the file carries a landed incident against exactly this**: two runs truncated at exactly four shots, losing 25 shots and the whole done line, to `ProbeNoonFacade`/`ProbeFrameCost`/`ProbeExposureCurve` (`SimDirector.cs:12078-12105`). **Put it inside the existing `try` at that call site and name the failure in the verdict.** A diagnostic must never cost the run it decorates. |
| **Water for the harbour** | **+1 to +6ms — the widest range on this list** | **LOW — this is the one I would not quote** | render | Decisive fork: a **flat animated normal-mapped plane with a cubemap reflection** is ~0.3ms and looks acceptable at a port at night. A **planar reflection camera re-renders the entire scene a second time** — that is a second full `render+rest`, ~+15ms, unaffordable. `WetReflections` already publishes a scene capture for wet ground **[MEASURED — `reflect[wet=13976 dry=11113 refresh=128]`]**, so **reusing that capture rather than adding a second reflection camera is the affordable path** — and note the global-render-state rule: `WetReflections` owns wet reflections, `SkyEnvironment` owns dry ones. Harbour water must route through an existing owner, not become a third writer. |
| **Interior cards behind windows** | **+0.1 to +0.4ms** | **medium** | render (overdraw, small) | One extra quad per window, opaque or alpha-tested, behind glass. Geometry is trivial. If the cards are merged into the building mesh they are free. If each window is its own GameObject they are ~0.68µs each. **Alpha-BLENDED cards behind alpha-blended glass is double transparent overdraw — use alpha-test or opaque.** |

### The 8K row, in detail — this is a hard blocker, not a cost

**No `.meta` files ship.** `find ledger/Assets -name "*.meta"` returns **0**
**[MEASURED]**. Every import setting is Unity's default, decided on the
build machine. Unity's default `maxTextureSize` is **2048**.

**An 8K PNG committed to this repo imports as a 2K texture and changes
nothing visible.** The project already has the proof: `SkyImport.cs` is the
only `AssetPostprocessor` in the project and it exists precisely because an
import assumption bit — it sets `imp.maxTextureSize = 512` explicitly
because nothing else would **[MEASURED]**.

So the 8K item's real shape is:

1. it requires an **editor-side `AssetPostprocessor`** setting
   `maxTextureSize` and `textureCompression` before it can land at all;
2. it costs **repo and CI**, not frame: textures already total **475.9MB
   over 169 files**, `StreamingAssets` is **783MB** and `Characters` is
   **714MB** **[MEASURED]**. 16x on even a subset is a multi-GB repository
   and a longer checkout on every one of Jafar's builds;
3. it costs **VRAM**, not frame time: 2K DXT1+mips ≈ 2.7MB, 8K DXT1+mips ≈
   **43MB each**. Twenty eye-level surfaces at 8K ≈ **860MB of VRAM on top
   of what is already resident** **[INFERRED — standard block-compression
   arithmetic]**;
4. **bandwidth cost is real but second-order** — 8K sampled at street
   distance thrashes the texture cache while displaying a mip that a 2K
   texture would have had anyway.

**My assessment: 8K is the worst value item on the list.** It is the one
change that costs GB and delivers nothing at the distance the reference
frames are shot from. **4K on a small named set of eye-level hero surfaces,
with the postprocessor built first, is the whole of the win.** The
alternatives in §4 buy more visible detail per byte.

### The vertex-colour row, in detail — verifying the "zero draw calls" claim

**The draw-call claim is TRUE. The "zero cost" framing is not.** Three
costs the research doc does not price **[INFERRED — mechanism, from code
read at HEAD]**:

1. **It needs a shader we do not have.** `procedural-density.md` says it
   itself: the Standard shader does not read vertex colours. That means a
   custom surface shader with a vertex modifier — a **new material set**.
   Materials on a different shader **do not batch with Standard-shader
   materials**, so this can ADD draw calls at the seam unless every
   affected surface moves together. It must also carry
   `#pragma multi_compile_instancing`, or it silently loses the GPU
   instancing that `AssetLibrary.cs` sets at three sites **[MEASURED]**.
2. **It needs per-object meshes.** The town is built from
   `GameObject.CreatePrimitive` — 13 sites in `WorldBuilder` alone
   **[MEASURED]** — which hands back a **SHARED** mesh. Writing vertex
   colours to it recolours every cube in the town identically. Per-building
   AO therefore requires a mesh **copy per building**, which costs build
   time and mesh memory and **removes the objects from any future static
   batching by shared mesh**.
3. **It is still the right call.** Against its alternative — thousands of
   AO decal quads, each an overdraw pass and 22MB of RGBA32 — vertex
   colour wins on every axis. **Price it as "one shader + a mesh-copy pass
   at world build", not as free**, and build it in the same batch as the
   `CombineMeshes` work in §4, because combining already forces per-block
   mesh copies and the two share that cost.

---

## 4. What gets cut or changed — and what is CHEAPER than what it replaces

**Nothing on the list needs cutting for frame time.** Two things need
changing for other reasons, and four structural moves make the density
items cheaper than they are currently specified.

### The two changes that are not optional

1. **8K → 4K, on a named short list, and build the `AssetPostprocessor`
   first.** As written the item cannot land: with no `.meta` files the 8K
   downsamples to 2K on import and the repo grows by gigabytes for a frame
   nobody can tell apart. **The postprocessor is the prerequisite, and it
   is worth building anyway** — it is also where `textureCompression`,
   anisotropy and mip settings stop being a lottery on the build machine.
2. **Harbour water must not add a reflection camera.** A planar reflection
   is a second full scene render — the only item on this list that could
   double the frame. Route it through `WetReflections`' existing capture or
   the `SkyEnvironment` cube. **[The global-state ownership rule applies:
   two writers on one render setting is how the fog calibration was lost
   for a week.]**

### The four structural moves — each buys more than it costs

| move | why it is cheaper than what it replaces | evidence |
|---|---|---|
| **`Mesh.CombineMeshes` per block, per district** | Turns thousands of decal quads and prop instances into one renderer each. At **0.68µs per renderer** upper-bound, collapsing 5,000 quads to 20 meshes is worth ~3.4ms of the price the naive version would pay. **Zero hits for `CombineMeshes` in the project today** — this saving is entirely untaken. | **[MEASURED — grep; marginal price INFERRED]** |
| **`StaticBatchingUtility.Combine` on the built town** | Nothing in this project is marked static and `StaticBatchingUtility` is never called — **zero grep hits**. The town is built at runtime from `new GameObject`, so Unity's static batching, which is ON by default in Player Settings, **is doing nothing for us**. One call per block at the end of world build. | **[MEASURED — grep for `isStatic`, `StaticEditorFlags`, `StaticBatchingUtility`: zero]** |
| **`shadowCastingMode = Off` on small props** | With `shadowCascades=4`, a shadow-casting prop is submitted **5 times**. Bins, bollards, cones and signage contribute nothing a player can read at 4 cascades. This is the lever that keeps the furniture and facade rows near zero as they scale. | **[INFERRED from `casc=4` MEASURED]** |
| **`LODGroup`, or the fog already doing its job** | **Zero `LODGroup` hits in the project.** Before building one, note that the ladder says triangles are not our constraint (1M skinned verts = 0.6ms) — so LOD is a **renderer-count** tool here, not a triangle tool, and `CombineMeshes` addresses the same constraint more directly. **I would not build LOD first.** | **[MEASURED — grep; reasoning INFERRED]** |

### The PS3-constraint argument, checked rather than repeated

The research doc's claim that PS3-era techniques are cheap by construction
is **correct and under-used here**. The specific reading: GTA V ran this
look in 256MB of system RAM and 256MB of VRAM. Every technique in §7 of the
spec — vertex-baked AO, multiplicative grime quads, one-mesh wires, atlas
pages, sun cookies for cloud shadow, distance desaturation — was chosen
under a memory ceiling **60x tighter than the one we are proposing to blow
with 8K textures**. The plan is internally inconsistent on exactly one
axis: it adopts the PS3 techniques and then proposes a texture budget from
2020. **Drop the 8K row and the plan becomes coherent.**

### What I would cut first, in order

1. **8K textures** — highest cost, lowest visible return, cannot land as
   written, and inconsistent with every other technique in the plan.
2. **A dedicated water reflection camera** — if the harbour cannot reuse an
   existing capture, ship flat animated water with a cubemap and revisit.
3. **Nothing else.** Everything else on the list is affordable at our
   current scale, and three items (wires, vertex colour, interior cards)
   are close to free.

---

## 5. Is there headroom to be won? — yes, and probably ~4–6ms

Ranked by evidence quality, not by size.

1. **Split the `noPixLights` rung.** ~4.6ms is spent on per-pixel lighting
   at a noon shot where **lamps and neon are both disabled** and the
   enabled lights are the sun, one bar light and up to four gameplay
   markers. If the markers and bar light carry a meaningful share, this is
   free headroom and the fix is `renderMode = LightRenderMode.ForceVertex`
   on markers, or a lower `pixelLightCount`. **Cost to find out: one rung.
   This is the highest-value measurement available.** **[MEASURED premise,
   INFERRED opportunity]**
2. **`shadowResolution = High` is untested.** `SceneLighting.cs:120` sets
   High; nothing has measured Medium. Shadow-map generation cost scales
   with map area. **Medium is a 4x smaller map and there is no rung for
   it.** **[MEASURED setting, UNMEASURED cost]**
3. **Cascade count is untested.** `shadowCascades = 4` with splits
   `(0.06, 0.18, 0.42)`. Two cascades halves the caster submissions and,
   with splits already concentrated near the camera, may cost little at
   street framing. **No rung for it.** **[MEASURED setting, UNMEASURED
   cost]**
4. **Shadow DISTANCE is NOT the lever, and this is measured.** `dist=70`;
   the `shadow45` rung buys **+0.68ms, sd 0.87, inside the noise**. Anyone
   who reaches for shadow distance as the shadow saving is reaching for the
   one shadow knob our data says does nothing. **[MEASURED — 39 runs]**
   The corollary is the useful half: **the 5.8ms is caster-count and
   map-resolution driven, not reach driven** — which is exactly why item 3
   in §4 (`shadowCastingMode` on small props) matters as density grows.
5. **Render scale already exists.** `SceneLighting.ApplyRenderScale` and
   `Screen.SetResolution` are wired **[MEASURED]**. Shadows collect,
   per-pixel lights and the whole post stack are per-pixel costs; render
   scale is the one lever that cuts all three at once. It is the escape
   hatch if a target resolution above 720p is ever chosen.
6. **`softParticles = true` and `anisotropicFiltering = ForceEnable`** are
   both set and both unmeasured **[MEASURED settings, UNMEASURED cost]**.
   `ForceEnable` overrides every texture's own setting; on a project with
   no `.meta` files that was probably the right call, but it is a global
   nobody has priced.

**Honest total: 4–6ms looks winnable [GUESSED], and the first 4.6 of it is
one measurement away from being either free or unavailable.** Do that rung
before promising the headroom to anything.

---

## 6. The instrument gaps this exercise found

Named, not fixed — nothing here sets a bound.

- **No rung with shadows AND per-pixel lights both off.** Their union is
  unknown and their savings are being added in conversation.
- **No rung isolating the sun from the point lights.** §5 item 1.
- **No rung for `shadowResolution` or `shadowCascades`** — two settings we
  chose and have never priced.
- **`meanFrame` has no companion key naming the RESOLUTION it was measured
  at.** The whole series is uninterpretable the day render scale moves.
- **`render+rest` has no gate and ~12–16ms of it is unattributed.** The
  plan spends this quantity and nothing watches it.
- **The ladder's noise floor (~±0.7–1.15ms sd) is not printed beside the
  ladder**, so a reader has no way to know that three of its six rungs are
  reporting noise. A `frameCostNoise` key, or the per-rung spread, would
  make the ladder self-describing.
- **`propsPlaced` and `sceneRenderers` are printed; no key ties either to
  a frame cost.** The 0.68µs/renderer figure in §2 had to be reconstructed
  from 46 verdicts by hand.

---

## 7. Unverifiable until CI

Nothing in this document changes code. The **[MEASURED]** rows are read from
landed verdicts and from source at HEAD, both of which are readable here.

**The following are unverifiable until CI** and would need a build on
`ledger-pc` to settle, with these verdict keys as the answers:

| question | key the run should answer with |
|---|---|
| which light carries the 4.6ms | a `frameCost` rung: `sunOnly:` or `pixLights1:` |
| what shadow resolution costs | a `frameCost` rung: `shadowMed:` |
| what cascade count costs | a `frameCost` rung: `casc2:` |
| the shadow+light union | a `frameCost` rung: `noShadowNoPix:` |
| whether an 8K import survives | a `texMaxSize=` key naming what the importer actually produced, in the shape of `skyLoadedAs` |
| the ladder's own noise | `frameCostSpread=` beside `frameCost` |

The engine's opinion is a measurement. None of §5 should be believed until
a rung reports it.
