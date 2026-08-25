# The inhabited street — people, vehicles, and what is behind the windows

> **STATUS — SPEC, 2026-08-25.**

Companion to `visual-bar-spec.md`, which covers environment only (light,
surfaces, density, content). This covers the three things that make a street
read as INHABITED rather than as a well-lit model: the people on it, the cars
on it, and whether the buildings have anything alive inside them.

**Method.** Every "we have" claim below was read out of the code or the landed
verdict at `36b90c9`, in this session, and the command is named. Every "GTA
does" claim is cited. Anything I could not check says so.

---

## 0. THE HEADLINE, before anything else

**Three of the four systems this brief assumed were missing are already
built. The single biggest win on the board is not new work — it is that the
wardrobe, the head-variation trait and half the animation library are built,
tested, and not reaching the frame.** Details in §1. Read §1 before §2–§4;
several of the recommendations further down are "finish the wire", not
"build the thing".

The brief's premise on windows is also **wrong at HEAD and worth correcting
loudly**: our windows are not black grids at every hour. There is a full
per-window occupancy system, 4,188 registered windows, shop-vs-flat hours,
a late-opening share, per-window glow scale, and a warm emissive tuned by a
measured transfer series. `windowsLitAtShot=2477` at hour 23. There are also
122 built shop interiors with shelf silhouettes behind the glass. **The
window problem is a DAYTIME problem only** — see §4.

---

## 1. THE AUDIT — what we already have, read from the code

### 1.1 People

| system | file | state at 36b90c9 |
|---|---|---|
| Per-person silhouette from name (height 1.56–1.93, breadth 0.86–1.18, head scale, gait, idle phase, headwear) — four independent hash salts so traits do not correlate | `Core/Physique.cs` | **BUILT and reaching the frame for height + breadth**: `RealBody.cs:1335` sets `localScale = (k*breadth, k, k*breadth)`; the bodies gate reads `h=1.58..1.91` |
| Period wardrobe: 8 authored bands (black 6, denim 6, grey 5, navy 4, stone 4, burgundy 3, bottle 2, shellsuit 1), `MaxValue=0.46` so the crowd never outshines the cast, CoreTests holding the mint/cyan gap | `Core/Wardrobe.cs` | **BUILT. Reaches the frame only as a single whole-body multiply** — see 1.4 |
| Idle-phase seeding so a street does not breathe in time | `CharacterRig.cs` | BUILT, running: `phasesSeeded=248` |
| Scenario points — what somebody standing HERE is plausibly doing, deterministic per person, keyed off authored places | `NpcWalker.ActivityForPlaceNear` | **BUILT and running**: `activityAsked=787 activityPeak=29 activityRefused=43`. This is structurally GTA V's scenario-point system (§2.1) |
| Benches as invitations — stop near one, take the seat | `NpcWalker.BenchSeatNear` + `Furniture.BenchSeats` | BUILT, running |
| Skinned-body budget, LOD banding, grant/revoke with dwell tracking | `NpcWalker.RealBodyCap = 28` | BUILT: `walkerBodies=533 bodyGrants=533 bodyGrantsFailed=0 streetBodiesSkinned=13` |
| Foot IK, look-split, limp, hand anchor for held props | `CharacterRig.cs`, `HeldObject.cs` | BUILT: `ikGoals=1247588 ikGroundMissed=0` |
| 83 Mixamo clips on disk across 4 harvest batches | `Assets/Characters/{A,B,C,D}` | **65 of 67 slots filled; 41 clips nothing names** — see 1.3 |

### 1.2 Vehicles

`TrafficHost.cs`, verified: 28 vehicles, 7 kinds, wheel proportions measured
correct (`diaPerHi` 0.34–0.40 across the fleet, a real car is ~0.40).
`KitPaints` is 6 colours; `KitPaint(v)` picks by `v.Id % 6`, with taxi forced
to black and police to a near-white that skips the multiply. Meshes come from
Kenney's Car Kit (`Assets/Props/car-kit`, 45+ models, CC0) plus two OGA CC0
packs. Parked cars in `WorldBuilder` read the same palette — one table for the
whole town, moving or parked.

**Not present, checked by grep:** number plates (no `plate`/`registration`
anywhere in `TrafficHost.cs` or the vehicle path in `WorldBuilder.cs` — the
only `plate` hits are wall nameplates and a chamfer comment), any dirt or
grime layer, any per-vehicle gloss variation, any glass treatment distinct
from body paint.

### 1.3 Windows and interiors

`WorldBuilder.cs` + `Core/Occupancy.cs`, verified:

- `windowsTotal=4188`, `sills=2133`, `winPaned=141`, `winBanded=235`,
  `mullions` tracked.
- `Occupancy.WindowLit(id, homeFraction)` — deterministic per window from a
  stable hash, so a flat does not flicker and a player can learn that the
  third window along is dark. The FRACTION is measured off the real
  population every time the lights change.
- `Occupancy.ShopLit(id, hour)` — shops open 08–19, `LateShare=0.3` stay lit
  to 24. A shopfront is explicitly not somebody's front room.
- Per-window `WindowGlowScale`, so lit windows are not one flat value.
- `WindowEmissive = (1.00, 0.49, 0.16)` — **read off a swept transfer series,
  not picked**, because ACES + bloom pull the source toward white; the frame
  comes out at the intended 1.00:0.82:0.45. `WindowGlowMultiplier = 1.7`,
  also from a series.
- `shopInteriors=122` — real geometry: an interior box 1.75m behind the
  facade plus two shelf boxes in front of it, material `Interior`
  `(0.18,0.13,0.08)`.
- Environment reflection is now **live**: `skyLoadedAs=Cube
  skyBound=industrial_sunset_puresky_2k reflDry=11113`. Glass finally has
  something real to reflect. (The `visual-bar-spec.md` §3 scorecard still
  says this is "in flight" — it has landed.)

### 1.4 AND HERE IS WHAT IS BUILT AND NOT REACHING THE FRAME

These are the findings. Each is a wire, not a system.

**(a) The wardrobe paints nobody.** Landed verdict: `bodySkinned=0
bodyDressed=0 bodyKeptMats=9`, and the bodies gate says it in words:
`parts=(nothing to paint — all 9 renderer(s) came textured)`. Since texture
extraction landed, every renderer on a bought model carries a real texture,
so `RealBody` keeps the model's own material and the skin/coat assignment
path — `BodyParts.Assign`, which has CoreTests and exists precisely to split
flesh from cloth — **is never consulted**. What the wardrobe does reach is
`Wardrobe.Wash`, applied through `Tint()` as ONE colour multiplied over
**every** renderer on the body, head included. So:

  * a person cannot have a navy coat and stone trousers — the whole figure
    is one hue;
  * the wash tints the FACE with the coat colour;
  * `Wardrobe.Bands`' eight-band period palette collapses to one
    per-person tint over whatever Mixamo's albedo happened to be. This is
    why the bright yellow trousers in the stills are not explained by any
    band: they are the MODEL's texture, washed.

**CORRECTION — 25 Aug. Every word above was true when written and the first
clause is now history: the wire landed.** The finding is kept, not rewritten,
because the sentence that made it look UNFIXABLE is the one worth keeping
beside it — §2.2's *"Mixamo bodies are single welded meshes; we have no garment
slots and building them is a modelling pipeline, not a code change"*, which was
the reason nobody tried. Measured against the FBX, eleven of sixteen bodies
carry a separate upper and lower garment mesh (§2.2's correction block).

What is true at this commit: the textured path gathers its renderers, classifies
them once through `Core/BodyParts.Garments` (`Own` / `Whole` / `Upper` /
`Lower`), washes **Upper** with the existing coat draw and **Lower** with a
second `Wardrobe.Dress` under salt 11, and leaves faces, hair, eyes, teeth,
shoes and hats carrying the artist's texture unwashed. Welded models take the
whole-figure draw exactly as before, so James, Michelle, Big Vegas and Sporty
Granny are not regressed. Source: `agent-reports/inhabited-wiring.md` §1.

**Not yet SEEN.** The counters `bodyPartsDistinct`, `bodyPartsWelded`,
`bodyPartsUpperOnly`, `bodyPartsOwn`, `bodyPartsUnknown` and `bodyTrousers`
have never been printed by a running sim — the Game layer does not compile
here. `bodyTinted` and the `bodyWash*` family now count CLOTH only, so their
landed series has a regime change at this commit and will fall against their
own history; that fall is the fix. **The prediction to check the first series
against is the 11-of-16 share above** — it is a prediction, not a bound, and
nothing is gated on it.

**(b) `Physique.Headwear` is drawn for every person and consumed by exactly
one file — `Mannequin.cs:245`, the box stand-in tier.** Grep for `Headwear`
returns three hits total: the field, the draw, and that one read. The
skinned tier — the 28 nearest walkers, i.e. everyone the player can actually
see — ignores it. The head is where a viewer looks first and where they
least expect two strangers to match; the trait exists, is stable per person,
and reaches only the tier that has been superseded.

**(c) 41 shipped animation clips that nothing names** (`python3
tools/clip-reach.py`, DISK-ONLY). Among them, in order of what they would
buy:

  * **`walk_f` — Female Walk.** Every woman in Meridian currently walks the
    male cycle. `walk_old` IS wired; `walk_f` is not.
    **CORRECTED 25 Aug — WIRED, and the sentence is kept because the reason
    it stood is the interesting part.** What held it was a comment in
    `CharacterPrefab.ArchetypeFor` — *"'old' is the only special archetype
    until a female walk clip actually exists in the harvest"* — true the day
    it was written, false from the B harvest onward, and it read as a
    decision rather than as a stale claim. `Core/BodyArchetype` now owns the
    rule and `walkFemale=n/total` reports whether the wire reached the
    street. `clip-reach.py` went 41 → 40 DISK-ONLY. Source:
    `agent-reports/inhabited-wiring.md` §2. Same lesson as §2.2's, aimed at
    a comment instead of an asset: **a claim about what the harvest CONTAINS
    is verified against the harvest.**
  * **`walk_start`, `walk_start_f`, `walk_stop`, `walk_stop_f`,
    `turn_left`, `turn_right`** — the transitions. Without them a walker
    snaps between standing and full stride, which is the single most
    mannequin-like thing a crowd does.
    **AND `walk_start` IS A MIS-PICK — 25 Aug, do not wire it as it stands.**
    The file on disk is `walk_start__Start Walking Backwards_4f5d….fbx`, so
    wiring this list as written would have set every man in the city off
    backwards. The other five are correct. The picker now refuses a reversed
    name for a forward slot (`tools/mixamo-pick/pick_animations.py`,
    `FORWARD_ONLY`/`direction_ok`), which makes the clip unpickable and
    unloadable, but **the fix on disk is a re-pick and that runs on Jafar's
    machine.** Read `_picks.json`, not this list, before wiring any of them.
  * `jog`, `stairs_up`, `stairs_down`, `laugh`, `lift`, `pockets`,
    `rummage`, `shake_hands`, `sit_talk`, `sit_drink`, `yell`, `back_away`.
  * Two slots are genuinely EMPTY (the harvest hole): `smoke`, `thinking` —
    and `NpcWalker` already asks for `smoke` at corners and homes, so that
    ask is refused every time it fires (`activityRefused=43`).

**(d) The head/face is untouched by everything.** No hair variation, no
headwear mesh, no per-person skin tone (the skin colour is one constant,
`RealBody.cs`: `new Color(0.72f, 0.58f, 0.47f)` — and it is on the path
that no longer runs anyway).

---

## 2. A. PEOPLE — what GTA V does, and which of it we can afford

### 2.1 What actually carries the impression, sourced

GTA V builds a ped from **12 component slots (0–11), each a *drawable* (the
mesh: shirt, jacket, legs, hair, hat) crossed with a *texture* variation** —
`SET_PED_COMPONENT_VARIATION(ped, componentId, drawableId, textureId,
paletteId)`, with `SET_PED_RANDOM_COMPONENT_VARIATION` for ambient spawns.
A drawable is the garment; the texture makes that one t-shirt red, black, or
logoed. Roughly 860 ped models ship, split into ambient families (business,
downtown, beach, hipster).
[gtaxscripting](http://gtaxscripting.blogspot.com/2016/04/gta-v-peds-component-and-props.html) ·
[lucienlmy/5mod-tutorials](https://github.com/lucienlmy/5mod-tutorials/blob/master/Basic-Ped-YMT-Editing-%E2%80%90-Components%2C-Clothes%2C-Textures.md) ·
[citizenfx natives](https://github.com/citizenfx/natives/blob/master/PED/GetNumberOfPedTextureVariations.md)

Behaviour comes from **scenario points**: authored world locations that say
what a ped does there — stand, sit, smoke, use a phone — with a ped model,
an animation, time-of-day restrictions and a spawn probability.
[GTAVillage ped AI guide](https://gtavillage.com/gta-5/tutorials/9346-npc-behavior-ped-ai-modding-guide-gta5-2026)

On idle variety, the industry number: **5–8 idle variants per archetype plus
start-time randomisation reads as convincing; fewer than 4 shows visible
repetition; more than 12 adds complexity without perceptual benefit.**
[MoCap Online crowd/NPC guide](https://mocaponline.com/blogs/mocap-news/crowd-npc-animation-guide)

On silhouette: readability is silhouette clarity at gameplay distance, and
game meshes typically ship a narrower anthropometric range than the real
population; widening height/volume distributions toward real-world ones is
the documented lever.
[Shape Shifters, arXiv 2412.16151](https://arxiv.org/pdf/2412.16151) ·
[RocketBrush character-style guide](https://rocketbrush.com/blog/the-ultimate-character-art-style-guide-for-artists-and-developers)

### 2.2 Us against that, honestly

| GTA lever | us |
|---|---|
| Silhouette spread (height, breadth, head) | **HAVE and running.** 1.58–1.91 measured. Head scale is drawn and applied on the mannequin tier only |
| Component drawables (separate garment meshes) | **HAVE, ON 11 OF 16 — this row said the exact opposite until 25 Aug; the correction and the dead sentence are below the table** |
| Texture variation per garment | **HAVE THE PALETTE, NOT THE SPLIT.** One wash over the whole body (1.4a) — *split landed 25 Aug, see the correction below* |
| Scenario points | **HAVE and running** — `ActivityForPlaceNear`, 787 asks |
| Idle variant count | We ship `idle`, `idle_2`, `idle_old`, `idle_bored` = **4**, which the sourced guidance puts exactly at the visible-repetition threshold. `pockets`, `thinking`, `look_around`, `glance` would take it to 7–8 |
| Gait variation | PART — `Gait` multiplier per person is applied; `walk_old` wired; `walk_f` on disk unused — *`walk_f` wired 25 Aug, see 1.4(c)* |
| Locomotion transitions | **NEVER** — 6 transition clips on disk, none wired |
| Doing things rather than walking | HAVE the mechanism; the vocabulary is thin because half the clips are unwired |

**CORRECTION — 25 Aug. The first row said this, and it is false:**

> **NEVER, and correctly** — Mixamo bodies are single welded meshes; we have
> no garment slots and building them is a modelling pipeline, not a code
> change

**It is quoted rather than deleted because it was plausibly DERIVED, and a
deleted error is one the next reader invents again** — the derivation was
"read the loader, see one `Tint` over every renderer, conclude the model has
one mesh", and anybody who reads the loader will reach it a second time.

**Measured:** mesh node names parsed out of all eighteen FBX under
`ledger/Assets/Characters` — the assets themselves, not the code that loads
them. Source: `game-design/agent-reports/inhabited-wiring.md` §0; re-read off
the files in this session against the same parser
(`tools/body-proportions.py`'s FBX reader).

**Eleven of the sixteen pool bodies ship a separate upper AND lower garment
mesh:** Adam (`Ch08_Hoodie`/`Ch08_Pants`), David, Elizabeth, Joe (nine meshes
— belt, shirt, suit, tie, trousers), Kate (`Ch21_Shirt`/`Ch21_Pants`),
Leonard, Martha, Pete, Remy (`Tops`/`Bottoms`), Shannon, The Boss
(`Jacket_Geo`/`Pants_Geo`). **Sophie is upper-only** (`Ch02_Cloth`). **Four
are genuinely welded** — James (`Ch06`), Michelle (`Ch03`), Big Vegas and
Sporty Granny (`..._BodyGeo` carries the clothes, plus separate face parts).
`X Bot` and `Y Bot` are the untextured stand-ins `RealBody.IsMannequin`
excludes and are not in the sixteen. 11 + 1 + 4 = 16, so the arithmetic is
checkable on the line.

So a navy coat over stone trousers was **a naming problem, not a modelling
pipeline**, and it landed as one on 25 Aug: `Core/BodyParts.Garments` classifies
each renderer `Own`/`Whole`/`Upper`/`Lower` and the lower body takes a second
`Wardrobe.Dress` draw. The two rows marked *(see the correction below)* moved
with it.

**THE GENERAL LESSON, which is why this is written at length: a claim about
what assets CONTAIN is verified against the assets, not against the code that
consumes them.** Three research streams this week read our own source and our
own docs as though they were the world. The binary assets are part of the
world, and nobody had opened them.

### 2.3 The cost picture, and it is unusual

**The crowd is not in the frame bill.** `frameCost` over 46 landed runs:
`all` and `noBodies` are inside each other's noise, and `noBodies` is
*higher* than `all` in roughly half of them (newest: `all:26.2` vs
`noBodies:25.9`). What actually holds the frame is sun shadows (`all` −
`noShadow` ≈ 5.2ms) and per-pixel lights (`all` − `noPixLights` ≈ 5.1ms),
consistently across the series (`python3 tools/gates.py --series frameCost`).

**So every people recommendation below is free in milliseconds.** More clips
cost animator memory and a fraction of `rigsMs` (currently 0.71ms of a
6.29ms game budget). More material variety costs draw calls only if it
breaks batching — and these bodies are skinned, already unbatched.

The constraint on §2 is WORK, not frame time. That inverts the usual ranking
and is the reason people sit at the top of §5.

---

## 3. B. VEHICLES

### 3.1 The period question — our palette is right, our SHAPES are not

Britain's best-sellers through the eighties: Ford Escort (~1.6M across the
decade), Ford Cortina (190,281 in 1980, 159,804 in 1981 — the market leader
both years), Ford Fiesta, Austin Metro (launched 1980, 110,283 in 1981,
4th), Vauxhall Cavalier/Astra.
[Best Selling Cars Blog, UK 1980–81](https://bestsellingcarsblog.com/1982/01/uk-1980-1981-last-years-of-ford-cortina-domination/) ·
[startrescue top-10 80s UK](https://www.startrescue.co.uk/news/top-10/top-10-best-selling-uk-cars-of-the-1980s) ·
[retrowow 80s cars](https://www.retrowow.co.uk/transport/80s/80s_cars.php)

That is a street of **three-box saloons and small hatchbacks**. Our
`default` car pool is `car_kit_sedan, car_kit_suv, car_kit_hatchback_sports,
car_kit_sedan_sports` — the SUV is the anachronism (SUVs are a 1990s-2000s
phenomenon in Britain) and the two "sports" variants read modern. **Dropping
`car_kit_suv` from the default pool is a one-line change and the single
cheapest period fix in this document.**

**The palette is CONFIRMED period-plausible.** Navy, black, burgundy, bottle
green, grey, stone are exactly the British saloon colours of the era. What
is missing from it is the era's other half — the pale metallics and the one
loud colour (beige, pale blue, "harvest gold", red) — the same argument the
wardrobe already makes with its weight-1 `shellsuit` band. *(Inferred from
the wardrobe's own reasoning, not separately sourced.)*

### 3.2 What GTA does that we do not

GTA V renders a **128×128 HDR environment cubemap per frame**, converts it
to a dual-paraboloid map (6 faces → 2 hemispheres, an optimisation), and
that is what makes car paint read. Notably, **other cars and characters are
not drawn into the cubemap** — only scenery — so even GTA's reflections are
cheaper than they look.
[Courrèges, GTA V Graphics Study](https://www.adriancourreges.com/blog/2015/11/02/gta-v-graphics-study/) ·
[Part 2](https://www.adriancourreges.com/blog/2015/11/02/gta-v-graphics-study-part-2/)

We now have the equivalent input: a Poly Haven HDRI bound as
`customReflectionTexture` (`skyLoadedAs=Cube`, `reflDry=11113`). **The car
paint is not currently exploiting it** — `KitPaint` sets a colour and
nothing sets smoothness or metallic per vehicle.

### 3.3 Number plates — the cheapest identity object in the game

1983–1990 UK plates are the **prefix format**: a year letter, one to three
digits, three letters — `A123 ABC` is August 1983, then B/1984, C/1985 …
H/1990. **White at the front, yellow at the rear.**
[Wikipedia, UK registration plates](https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_the_United_Kingdom) ·
[UK Vehicle Audit format guide](https://ukvehicleaudit.co.uk/guides/uk-number-plate-formats-explained) ·
[Reg History, prefix plates](https://reghistory.com/prefix-number-plates)

We have none. We DO have `LedgerText`/`worldText` (`n=154 depthTested=154
adopted=3445 shader=True`) and a shipped font. A plate is a quad with a
world-text string on it — and there is a design payoff beyond the visual:
the game's moat is information, and a plate is a fact a witness can
remember. *(That second half is my inference, not a sourced claim.)*

---

## 4. C. WHAT IS BEHIND THE WINDOWS

### 4.1 Correcting the premise

Our windows are not dead. **At night they are the most measured system in
the build** (1.3). What IS dead is the daytime window:
`AssetLibrary.cs:1556` authors the day glass as `Color(0.09, 0.10, 0.13)`,
smoothness 0.85, metallic 0.1, with a procedural pane pattern and a
near-black emission that exists only to keep the `_EMISSION` keyword on.
Under an overcast sky, a very dark, very glossy surface with nothing
reflecting into it renders as a black rectangle. **That is a reflection
problem before it is an interior problem** — real glass by day is mostly a
mirror of the sky, and the reference frames show exactly that.

### 4.2 Interior mapping — the technique, and whether we need it

Interior mapping (van Dongen, CGI 2008) divides the space behind a facade
into evenly sized rooms and, per pixel, **casts a ray and intersects three
planes analytically** — the nearest hit says whether you are seeing floor,
ceiling or wall, and the intersection point becomes the texture coordinate.
It is not raymarching: the intersections are closed-form, and the classic
optimisation packs all three into one `float4` so they compute together. It
is done in **tangent space**, so the maths is identical everywhere on the
surface, and it adds **no geometry and no draw calls**.
[Habrador, Unity interior mapping](https://www.habrador.com/tutorials/shaders/2-interior-mapping/) ·
[van Dongen paper](https://www.semanticscholar.org/paper/Mapping-A-new-technique-for-rendering-realistic-Dongen/862248de620efe27705af3702ab2a2c0d4ec76ec) ·
[Alan Zucconi showcase](https://www.alanzucconi.com/2018/09/10/shader-showcase-9/) ·
[80.lv writeup](https://origin.80.lv/articles/interior-mapping-rendering-real-rooms-without-geometry/)

Free implementations, licence-checked:

- **[Gaxil/Unity-InteriorMapping](https://github.com/Gaxil/Unity-InteriorMapping) — MIT** (I read the LICENSE file directly). Tangent space, room variations, room size, four blind positions, refraction, corridors, light projected from windows, external-occluder shadows, random decoration placement. Needs a 4×4 interior atlas (ground / ceiling / sidewall / backwall columns), a 4-variation window atlas, a window normal map and a roughness/metal/glass mask. Author's note: "tested on windows/DX11 only, no support will be provided." **It does not state a render pipeline** — it is 2018-era Unity, so almost certainly built-in CG, but that is inferred, not confirmed.
- [knowercoder/BasicInteriorMap](https://github.com/knowercoder/BasicInteriorMap) — **URP only**, so not usable here without a port.
- [mrarashiyan/Fake-Interior-Shader](https://github.com/mrarashiyan/Fake-Interior-Shader) — general Unity fake-interior shader.
- Asset Store "Fake Interiors FREE" and the cubemap variants are **excluded by project rule** — they need an account.

**Built-in-pipeline note.** Nothing about interior mapping requires URP or
HDRP: it is a fragment-shader trick over a normal opaque surface, and the
built-in pipeline compiles it fine. What DOES need URP/HDRP, and which we
should not chase: Shader Graph authoring of it (built-in has no Shader
Graph), the depth-prepass-based variants, and any of the Asset Store
"parallax interior with baked depth raymarch + cubemap shell" packages,
whose selling point is a URP/HDRP-first bake pipeline.

### 4.3 But we probably should not build it first

Interior mapping's cost is per-pixel over every window in the frame, and its
payoff is *depth* — rooms that hold their perspective as you walk past. That
matters for a Spider-Man skyline of glass towers. Our facades are **brick
terraces with small sash windows**, where each window is a handful of pixels
at street distance, and we already ship the two cheaper wins that carry most
of the same impression:

1. **Geometric interiors behind shop glass** — 122 of them, already built,
   with shelf silhouettes in front, which is exactly the PS3-era approach.
2. **Per-window emissive occupancy** — the thing that actually makes a
   skyline read as inhabited at dusk.

So the ranked answer for §C is: **fix the daytime glass first (reflection +
a warm mid-tone behind it), extend the built shop-interior treatment to
upper-floor flats second, and keep interior mapping as a named next rung on
the quality ladder rather than as the next build.**

### 4.4 The daytime fix, concretely

- Give `Window` a **sky-reflecting** response now that the HDRI cube is
  bound: the material already has smoothness 0.85 — the missing half is
  that the base colour is so dark, and metallic so low, that the reflection
  contributes almost nothing. A brighter, less saturated base plus higher
  metallic turns a black rectangle into a pane that carries the sky.
  **Measure it, do not pick it** — this is the same transfer-series problem
  `WindowEmissive` already solved once, and the instrument (`skyVsWall`)
  exists.
- Put a **dim warm interior value behind the domestic windows by day**, the
  way `Interior` already does behind shopfronts at 0.18. A room seen through
  glass at noon is dark but not black, and the tonal difference between
  "dark room" and "void" is what stops a facade reading as a grid.
- **Curtains and blinds as a per-window variation**, from the same stable
  hash `Occupancy.WindowLit` already uses: a fraction of windows get a light
  card covering the top third or the whole pane. This is one extra quad per
  chosen window, no shader work, and it breaks the uniformity of a
  4,188-window city more than any lighting change would.

### 4.5 The night refinement

We light windows warm and uniform in hue. A British street at dusk actually
carries **two colour temperatures**: warm domestic tungsten above, and cold
fluorescent shopfronts below. We already distinguish `shop` from flat in
`SetWindowsLit`; giving the shop branch a cooler emissive is a **one-line
change to an existing branch** and is the highest impression-per-character
edit in this whole document.

**Frame-cost warning for §C, and it is the one real risk here.** Emissive is
free — it is a material property, not a light. **Adding actual point lights
in windows is not free**: `all` − `noPixLights` ≈ 5.1ms today, the largest
single line in the render bill after shadows. Nothing in §4 should add a
`Light` component.

---

## 5. THE RANKED LIST — impression per unit of work, across all three areas

Cost is my estimate of builder work; **ms is the frame cost**, which for
almost everything here is nil, for the reasons in §2.3 and §4.5.

| # | item | area | how we build it | work | ms |
|---|---|---|---|---|---|
| **1** | **Split the body wash: flesh vs cloth, and coat vs legs.** The crowd stops being one hue per person and starts wearing the eight-band period palette | A | `RealBody` textured path currently calls `Tint()` once for all renderers. Run `BodyParts.Assign` on the TEXTURED list too (it already exists, is in Core, and has tests including the `sur-face` case), wash flesh renderers toward the skin tone and cloth renderers with the wardrobe band, and take a SECOND wardrobe draw with a different salt for the lower body. Arithmetic in Core; Game supplies membership only | M | ~0 |
| **2** | **Wire `walk_f` and the six locomotion transitions** (`walk_start`, `walk_start_f`, `walk_stop`, `walk_stop_f`, `turn_left`, `turn_right`) | A | Clips are on disk. Animator states + `NpcWalker` triggers. Half the city stops walking like a man; nobody snaps from stand to stride | S–M | ~0 |
| **3** | **Cool the shopfront emissive, keep the flats warm** | C | One branch already exists in `WorldBuilder.SetWindowsLit` (`bool shop`). Give it its own colour. British high street at dusk in one line | XS | 0 |
| **4** | **Daytime glass: make it reflect the bound HDRI, and put a dim warm value behind it** | C | Material tuning on `AssetLibrary.Window` + an `Interior`-style value for domestic windows. **Sweep and read the series** — `WindowEmissive` shows this exact problem needs a transfer measurement, not a guess | M | ~0 |
| **5** | **Headwear on the skinned tier.** `Physique.Headwear` is drawn for everyone and read only by `Mannequin` | A | Cap / hat / hood as a small primitive or fetched mesh parented to `CharacterRig`'s head bone (the class already publishes `HandAnchor` for exactly this pattern — copy it as `HeadAnchor`). The head is where the eye goes and where two strangers matching is most obvious | M | ~0 |
| **6** | **Curtains and blinds, per window, from the existing hash** | C | One quad over a fraction of windows, `Occupancy`-style stable fraction, authored share. Breaks up 4,188 identical panes at every hour, day and night | S–M | ~0 |
| **7** | **Number plates, period-correct prefix format, white front / yellow rear** | B | Quad + `LedgerText` (already shipped, `worldText` gate green). Generate `A123 ABC` from the vehicle id with the year letter from the game date. Arithmetic and string in Core where it is tested | S–M | ~0 |
| **8** | **Drop `car_kit_suv` from the default car pool; add the missing period colours** | B | One line in `TrafficHost`'s mesh table; two or three entries in `KitPaints` (pale blue, beige, one red) with the same value discipline the wardrobe uses | XS | 0 |
| **9** | **Fill the two idle slots and wire four more standing clips** (`pockets`, `laugh`, `shake_hands`, `sit_talk`; fetch `smoke` and `thinking`, which `NpcWalker` already asks for) | A | Mixamo fetch for the two holes; `ActivityForPlaceNear` and the idle tree for the rest. Takes idle variety from 4 to 7–8, which is where the sourced guidance puts "convincing" | S–M | ~0 |
| **10** | **Per-vehicle gloss + a dirt value**, so 28 cars are not one finish | B | Second and third channels beside `KitPaint`, varied off `v.Id` with its own salt. Now that the environment cube is bound, gloss variation is finally visible | S | ~0 |
| **11** | **Hand props for the carry clips** — a shopping bag, a case | A | `CharacterRig.HandAnchor` + `HeldObject` both exist and are wired for the player. `carry_bag` is already played by walkers with nothing in the hand | M | ~0 |
| **12** | **Interior mapping shader for upper-floor windows** | C | Port Gaxil (MIT) to built-in, author a 4×4 atlas. **Named as the next rung, not the next build** — see §4.3 | L | per-pixel, unmeasured |

**Cutting across the whole list**: items 1, 2, 3, 5, 9 and 11 are all
"finish the wire on something already built and tested". That is six of the
top eleven, and it is the honest summary of this research.

---

## 6. Sourced vs inferred — the ledger

**Sourced** (URLs above): GTA's 12-slot drawable/texture component model and
its natives; scenario points as the ambient-behaviour mechanism; the 5–8
idle-variants figure; silhouette/anthropometric-range findings; GTA's
128×128 per-frame environment cubemap and dual-paraboloid conversion, and
that cars and peds are excluded from it; interior mapping's three analytical
ray-plane intersections in tangent space with no added geometry; the Gaxil
MIT licence and its texture requirements; the URP-only status of
BasicInteriorMap; UK 1983–1990 prefix plate format and front/rear colours;
UK 1980s best-seller list.

**Inferred, and flagged as such**: that Gaxil's shader is built-in-pipeline
CG (2018-era, but the repo does not say); that the missing half of
`KitPaints` is the era's pale metallics and one loud colour (reasoned from
the wardrobe's own weight-1 argument, not sourced); that plates would serve
the information moat; that our small brick-terrace windows get less from
interior mapping than a glass-tower skyline does.

**Not checked, and it should be before item 4 lands**: what the daytime
window actually looks like in the four committed stills. Rule 4 — read the
frame, do not read this table instead.
