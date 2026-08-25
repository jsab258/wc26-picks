# Harbour water — what a British port needs in the frame, and what it may cost

> **STATUS — SPEC, 2026-08-25.** Research for M17.10 / `visual-bar-spec.md`.
> Not a plan and not a landing report. Nobody had looked at water at all: the
> three existing research streams (art direction, content sourcing, procedural
> density) do not contain the word. Every claim here is tagged **[read]** (from
> this repository, this session), **[measured]** (computed here, this session),
> **[sourced]** (a URL below) or **[inference]** (mine, no citation). Sources
> are §10.

---

## 0. What we have now: nothing, and the nothing is visible

Checked before writing anything, because the brief said it might be nothing and
this file is not allowed to guess.

**There is no water in this game.** [read] A grep of
`ledger/Assets/Scripts/` for water / sea / harbour / quay / tide / wharf / jetty
returns ~80 hits and **not one of them builds, shades or moves a surface.**
They are: dialogue and character bios (`Tier2Setup`, `CastTier1`), place ids
(`HookMap.crane_wharf`, `AccessSetup.harbor_office`), street names
(`StreetMap`: Quay Street, Harbour Road, Winter Quay), audio beds
(`Audio.cs:1813` — "a slow harbour swell", a sound), and geometry that stops
*at* the water without drawing it.

The nine shaders in `ledger/Assets/Resources/` are Blob, Text, FilmGrade, Ring,
LightShaft, Decal, Smoke, Ao, Sky. **No water shader.** [read]

What exists is the *negative space*, and it is well built:

| thing | file | what it does |
|---|---|---|
| `GroundMinZ` | `Game/WorldBuilder.cs:23,300` | south edge of the walkable slab — the shore line |
| skyline apron stops at it | `WorldBuilder.cs:3909-3915` | "past it the frame is water, and paving it would trade one premise fault for another" |
| `SkylineSeaMargin = 55f` | `WorldBuilder.cs:3719` | no far block may stand within 55m of the shore, on **any** edge |
| south edge carries no blocks | `WorldBuilder.cs:3982` | "a band behind them would read as a city built in the water" |
| three quay cranes | `WorldBuilder.BuildLandmarks` | the silhouette on the seaward side, at z −174 |
| twelve gulls | `Game/GullHost.cs:26` | circle "off the quay line south of them, **where the map implies water**" |

So the world model already knows where the sea is. **Nothing renders it.**

### What is actually on screen south of the shore [measured]

`game-design/sim-shots/district_ironside.jpg` — camera (70.6, −144.9), yaw 270,
the dockside frame. The region left of the quay is `LedgerSky`'s lower
hemisphere (`_GroundColor`), seen past the edge of the ground slab:

| patch | mean RGB | luma | **luma std** | saturation |
|---|---|---|---|---|
| "sea" (x 0–38, y 110–245) | 67, 81, 100 | 0.310 | **0.0032** | **0.331** |
| land apron (x 0–200, y 300–420) | 159, 163, 162 | 0.635 | 0.2026 | 0.082 |

Two readings, and both are findings rather than colour trivia:

1. **Local variation is 1.6% of the land's.** It is a monotonic vertical
   gradient — a column sampled every 20px runs 0.19 → 0.31 with no reversal and
   no edge. There is no horizon line, no shoreline, and no structure of any
   kind. It does not read as calm water; it reads as a hole in the frame.
2. **It is the most saturated and the bluest thing in the shot** — sat 0.331
   against the land's 0.082. That is exactly backwards for a British port.
   `art-direction.md` §3 is about colour discipline; the one region with no
   art direction on it at all is currently the loudest.

### Machinery already built that water can ride on [read]

This is the part that changes the recommendation, so it was read rather than
assumed:

- **`Game/WetReflections.cs`** — a realtime `ReflectionProbe`, resolution 64,
  `ViaScripting` refresh, faces time-sliced one per frame, box projection
  48×18×48, far clip 60m, gated on wetness *and* on distance travelled. The
  cost design for "a reflection we can afford" is done and landed.
- **`Game/SceneLighting.cs:144,350`** — `RenderSettings.defaultReflectionResolution = 64`
  and `DynamicGI.UpdateEnvironment()` on ~0.04 steps of night. Its comment
  states that on dry daytime frames `SkyEnvironment` binds **a 512/face Poly
  Haven cube**, and the 64px bake is the night/fallback. **So `unity_SpecCube0`
  already holds a sky the water can reflect, and somebody else is already
  paying for it.**
- **`Game/FilmGrade.cs:123-138`** — `DepthTextureMode.DepthNormals` is
  requested **only at High detail**, and the comment says why: "it is not a
  texture flag, it is A WHOLE EXTRA RENDER OF THE SCENE every frame". Any
  water technique that needs scene depth is not free here; it is a second
  scene render on Low and Medium.
- **Unity 6000.0.58f1, Built-in RP, forward.** [read] `ProjectSettings/` holds
  only `ProjectVersion.txt`; there is no URP or HDRP asset anywhere in
  `ledger/Assets/`. Custom shaders live in `Assets/Resources` and are found by
  `Shader.Find("Hidden/Ledger*")` — nine precedents.
- **The frame gate is red**: `game=17.55ms` against a 12ms budget, failing 28
  of 141 runs (`roadmap.md:389`). [read]

---

## 1. THE ANSWER FIRST — the minimum that reads as harbour water

Four things, in this order. Everything after §1 is the evidence for them.

**W1 — a flat opaque plane with a two-stop colour ramp and a Fresnel toward the
sky's own horizon colour.** No transparency, no depth, no reflection capture,
no normal map. One unlit-ish shader, one quad from `GroundMinZ` to the fog
wall, sitting ~1.2m below the quay top. This single step does 60% of the work
because it replaces a *hole* with a *surface* and gets the value relationship
right — dark water against pale wet stone is the whole grey-harbour read
(§2, §3). **[inference], but the value split is already measured: 0.31 against
0.635 is the correct direction and roughly the correct distance.**

**W2 — perturb the reflection vector with a cheap animated normal and sample
`unity_SpecCube0`.** This is precisely GTA IV's water: a low-resolution
cubemap, no dynamic objects in it, "very blurred and vague" [sourced §10.4].
We already have the cube bound and refreshed. Two scrolling normal maps at
different scales and speeds is the standard [sourced §10.5]; a sum of three
analytic sine waves is the same picture with **no texture to fetch at all** and
is my recommendation (§7).

**W3 — a horizon.** Water must meet sky at an edge, not dissolve into it. The
fog is `ExponentialSquared` and the sky's horizon stop is pinned to the fog
colour by construction (`LedgerSky` header). Water gets the same treatment with
a **deliberate small delta** kept at the far end, so there is a line.

**W4 — a scum band where the water meets the wall, computed analytically.**
Our shoreline is a straight line at a known Z (`GroundMinZ`) — the distance
from any water pixel to the quay is world-space arithmetic. **No depth texture,
no soft-particle trick, no second scene render.** And it must be a dirty
pale-brown scum line, not white surf (§3).

**Rough cost.** [inference — must be measured before any bound is set] W1 is
one opaque draw over ~25–35% of a dockside frame with no texture fetch: call it
tens of microseconds of fill. W2 adds one cubemap sample and ~20 ALU to those
pixels. W4 is four ALU. My honest estimate is **0.2–0.5ms at 1280×720 on the CI
machine**, dominated entirely by fill rate, and I will not put a number in a
gate until the series is printed (§9). What I am confident of: **this is the
cheapest thing on the M17.10 board that removes a whole-frame defect**, and
every technique that would cost real milliseconds is refused in §6.

**And the shore-side question, answered plainly:** the tide band on the quay
wall (§5.1) beats the ripple shader, the mooring clutter beats the glint, and
both are cheaper — but **no amount of shore detail substitutes for W1**,
because the defect is a void, and dressing the edge of a void draws attention
to it. Order: plane → tide band → edge clutter → ripples → glint → debris.

---

## 2. What PS3-era games did, and what the minimum is

Our bar is a 2013 console game running in 256MB, so its methods are cheap by
construction. That is the point of this section: not "what is possible" but
"what was proven sufficient at our bar".

**GTA IV (2008, PS3/360, RAGE)** reflected water from a low-resolution
cubemap — roughly 256×256 per face — containing **buildings only**: cars, trees
and people do not appear in it, and the reflection is deliberately blurred and
vague to hide the resolution [sourced §10.4]. This is the single most useful
data point in this document, because it is one generation *below* our bar and
we already own a better cube than that.

**GTA V (2013)** is the bar and it is a step up: water is drawn in MRT,
producing a water-diffuse map and a water-opacity map whose green channel is
**depth from the water surface**, so deep pixels are opaque and shallow ones
nearly transparent; reflection is a full second render of the scene
upside-down, and refraction is taken from the already-composed frame
[sourced §10.1]. **Every one of those is a technique we should decline** (§6):
the depth channel buys shallow-water transparency, which turbid British dock
water does not have (§3), and the mirrored scene render is a second draw of the
world we cannot pay for at 17.55ms.

**Portal 2 / Valve, SIGGRAPH 2010** is where flow maps entered the standard
toolbox: an artist-painted 2D vector per point on the surface perturbs the
normal along the current [sourced §10.3]. **Right technique, wrong water.** A
flow map earns its cost on rivers and around obstacles. Inside a harbour wall
there is no coherent current worth painting; the motion is wind chop of a few
centimetres. Declined, with a named reason rather than on cost.

**Uncharted (Naughty Dog, GDC 2012)** ran three separate water renderers —
non-LOD meshes for calm bodies, a hierarchical LOD displacement system for open
ocean, particle skinning for floods — all procedural, no physics
[sourced §10.2]. The relevant lesson is the split: **calm enclosed water and
open ocean were different systems**, and the calm one was the cheap one. A
harbour is the calm one.

**So the era's minimum, and ours:** an opaque surface, a colour ramp, a Fresnel
blend to a blurred low-res environment reflection, an animated normal that
touches only the reflection vector, and foam authored where the artist knows it
belongs. Vertex displacement is for open ocean and is not needed inside a
harbour wall [inference, supported by the Uncharted split].

---

## 3. What a grey northern harbour actually looks like

Copying GTA V's water would be wrong twice over: wrong latitude and wrong
water. The markers below are what make it read as Britain rather than Los
Santos, stated as things a shader or a texture can do.

**The water is dark and near-neutral, and reflection dominates transparency.**
Coastal water carries suspended mineral, organic detritus and coloured
dissolved organic matter; those concentrations limit light penetration and give
coastal water its green-brown cast, against open ocean where light goes deep
[sourced §10.6]. With little light returning from below, what you see is the
surface: and Fresnel reflectivity rises sharply toward grazing angles, so
looking *across* a harbour the surface is effectively a mirror
[sourced §10.7]. **Consequences for us, all of them simplifying:**
transparency is nearly worthless, refraction is worthless, a depth-based
absorption gradient is worthless, and the reflection is doing all the work.
This is why the cheap technique is also the correct one here.

**Under cloud it goes near-black.** The water reflects the sky, and a British
overcast sky is a low-luminance grey — so the water is darker than the wet
stone around it, which is the opposite of the tropical case where bright water
sits against dark land. Our measured land at 0.635 luma and a water plane
around 0.20–0.30 is the right relationship [measured land; water target
inference].

**Low amplitude inside the wall.** A harbour wall exists to stop swell. What
is left is wind chop — centimetre-scale ripples, sometimes a glassy sheen with
slow-moving oil rainbows near the boats. No breaking waves, no white caps, no
surf. **A white foam line at the wall is a beach marker and would read as
wrong.**

**The oily sheen is real and it is period-correct.** Trace diesel and bilge
water from moored boats leaves surface film in harbours [sourced §10.8]. In a
late-analog working port, that is unremarkable — it belongs in the frame. As a
shader term it is a very slight, very slow hue rotation in the specular, at low
amplitude; as a prop it is a few dark iridescent patches near the moorings.

**Turbidity and the scum line.** Fine sediment carried into harbour basins is a
standing feature, and fluid-mud layers in harbour basins are documented
[sourced §10.9]. Visually: the water is opaque, and where it meets a wall or a
hull it collects a band of dirty foam, weed fragments and litter. Pale brown,
not white.

**The wall itself is banded, and the bands are biology.** This is the highest
value paragraph in the document, because it is a texture rather than a shader.
British rocky shores and harbour walls show hard horizontal zonation
[sourced §10.10]: at the top, yellow and grey lichens of the splash zone;
below them a **black band of tar lichen (*Verrucaria maura*) sitting just above
high tide — routinely mistaken for an oil stain**; below that greying rock
dense with barnacles; then brown wracks (*Pelvetia canaliculata*, *Fucus
vesiculosus*); and below the waterline, permanently wet, dark, near-black
stone. **That is a five-stop vertical ramp on a wall we already build**, and it
is the single most legible "this is a tidal port" signal available to us.

**Reference photographs.** Geograph Britain and Ireland, via Wikimedia Commons
— low tide at Brixham inner harbour, Poole Harbour, Harrow Harbour
[sourced §10.11]. **Reference only, never shipped pixels**: Geograph is
CC BY-SA 2.0 and `content-sourcing.md` §2.2 already rules that the share-alike
would encumber any texture derived from it. We measure a band height and a
colour from these and author the texture ourselves.

---

## 4. Unity Built-in, forward — what is implementable and what is not

Stated as a table, because "needs a pipeline we lack" is the fastest way to
waste a week.

| technique | Built-in forward? | verdict |
|---|---|---|
| Unlit/custom surface shader on a plane, `Shader.Find("Hidden/LedgerWater")` | **yes** — nine precedents in `Assets/Resources` | **take** |
| Sampling `unity_SpecCube0` for sky reflection | **yes**, already bound and refreshed (`SceneLighting`) | **take** |
| Scrolling normal maps / analytic sine normals | **yes**, plain ALU and `tex2D` | **take** |
| Analytic distance-to-shore foam (world-space, straight quay line) | **yes**, needs nothing from the pipeline | **take** |
| `ReflectionProbe` (realtime, time-sliced) | **yes**, `WetReflections` proves it | **only if** §1 is not enough |
| Planar reflection camera (`Camera.CalculateObliqueMatrix`, reflected view matrix) | **yes** in Built-in, no package needed [sourced §10.12] | **decline** — it is a second render of the scene, and each reflective surface in view multiplies it |
| Depth-based water fog / soft shoreline (`_CameraDepthTexture`) | **yes**, but the depth texture is generated by the ShadowCaster pass over all opaque objects [sourced §10.13] — and `FilmGrade`'s own comment calls it "A WHOLE EXTRA RENDER OF THE SCENE" | **decline** — buys transparency we do not want (§3) at the price of a scene render |
| `GrabPass` refraction | supported in Built-in; a full framebuffer copy per grab | **decline** — refraction is invisible in opaque water |
| Vertex displacement / Gerstner waves | yes (needs a tessellated grid) | **decline** — open-ocean technique; harbour amplitude is centimetres |
| Unity Standard Assets `Water4` / `WaterProDaytime` | **no** — Standard Assets is deprecated and no longer available from the Asset Store [sourced §10.14], and taking it would need a Unity account, which we do not use | **excluded on both counts** |
| HDRP Water System (2022.2+) | **no** — HDRP only [sourced §10.15] | **not available to us** |
| URP water samples / Shader Graph production-ready water | **no** — URP only | **not available to us** |
| Asset-store water shaders (AQUAS, etc.) | requires purchase and an account | **never** |

One more Built-in fact worth writing down before somebody rediscovers it:
**Built-in RP is marked deprecated as of Unity 6.5** [sourced §10.15]. That is
not a reason to change anything today — it is a reason not to build a large
water system whose value is pipeline-specific.

---

## 5. The shore-side extras, and the honest ranking against the plane

The brief asked whether these beat the water plane. **They beat everything
except the plane**, and two of them are free at runtime because they are
texture and geometry we already draw.

### 5.1 The tide band on quay walls and hulls — rank 1 of the extras

A five-stop vertical ramp (§3): grey-yellow lichen, **black tar-lichen band at
the high-tide line**, barnacle grey, brown wrack, near-black permanently wet
stone. Applied to the quay wall, the crane plinths, and any hull.

**Why it is the best value in this document per unit of work:** it is a
texture on geometry that already exists and is already drawn — **zero
additional milliseconds** — and it is the marker that says *tidal port* rather
than *lake*. It also fixes something the water plane cannot: it tells you where
the water WAS, which is what makes a harbour read as a working place rather
than a pond. [inference, on sourced biology]

### 5.2 Wet-dark stone below the tide line — rank 2, and nearly free

`AssetLibrary.cs:725` and `Core/LightModel.cs:588` already model wetness ("a
water film fills the surface micro-structure, so less light..."), and
`AssetLibrary.cs:904` already refuses to wet vertical brick because "a vertical
brick face does not pool water". **The mechanism exists; nothing points it at
the shore.** Below the tide line a vertical face IS permanently wet, which is
the one exception to that rule. This is a wiring job, not a new system.

### 5.3 The waterline join — rank 3, and it is a correctness item

Where the quay meets the sea there must be no gap and no float. This is
`instruments.md`'s placement rule verbatim: distance to the datum, **and**
whether the datum exists under the footprint, broken down per edge. Eight
skyline blocks once hung over open sea at foot-gap 0.00 exactly. The same
failure with a water plane is a visible slot of sky between wall and water.

### 5.4 Mooring clutter — rank 4

Bollards, tyre fenders, mooring ropes (the two-segment cable trick `GullHost`
cites already exists), a ladder down the wall, chains. Small, static, cheap,
and it is what a photograph of a British dock is full of.

### 5.5 Moored boats — rank 5, high impact but real work

Silhouettes at distance are enough, but they must sit at the waterline and heel
slightly, and each needs its own tide band (§5.1) on the hull. This is the only
extra with genuine content cost.

### 5.6 Floating debris and scum patches — rank 6

A handful of small dark quads near the wall, drifting on the same scroll as the
water normal. Cheap, and it kills the "clean lake" read.

### The ranking, both axes

| # | item | visible impact | work | runtime cost |
|---|---|---|---|---|
| 1 | **W1 water plane + colour ramp** | removes a whole-frame void | one shader, one quad | fill only, ~0.1–0.3ms [inference] |
| 2 | **Tide band on walls** | says *tidal port* | one generated texture + UVs | **zero** |
| 3 | **Wet-dark below the line** | grounds the wall in the water | wiring an existing model | **zero** |
| 4 | **W4 scum band at the wall** | joins water to land | four ALU in the same shader | ~0 |
| 5 | **W3 horizon delta** | gives the frame a far edge | one lerp | ~0 |
| 6 | **Mooring clutter** | working port, not scenery | prop placement | small draw count |
| 7 | **W2 ripple normal + cube reflection** | close-range conviction | shader + normal source | 1 cube sample + ~20 ALU |
| 8 | **Moored boats** | scale and occupation | content | medium |
| 9 | Debris, oil sheen | texture-of-life | small | ~0 |
| — | *planar reflection, refraction, depth fog, displacement* | marginal here | large | **declined, §4** |

---

## 6. What we are NOT doing, with the reason attached

- **No planar reflection camera.** A second scene render, at 17.55ms against a
  12ms budget. GTA IV did not do it either [sourced §10.4].
- **No refraction / GrabPass.** Invisible in opaque turbid water (§3).
- **No depth-texture shoreline.** Costs a scene render on Low/Medium
  (`FilmGrade`'s own finding) and buys shallow-water transparency we do not
  want. The straight quay line makes it unnecessary.
- **No vertex displacement.** Harbour amplitude is centimetres.
- **No flow maps.** No coherent current inside a harbour wall.
- **No white surf.** It is a beach marker; harbours get brown scum.
- **No blue.** Our current placeholder is at saturation 0.331 against the
  land's 0.082 [measured]. Whatever ships must be *less* saturated than the
  stone, not four times more.
- **No Standard Assets, no Asset Store water, no account, no purchase.**

---

## 7. How we build it — every asset free, nothing purchased, no account

**The shader.** `ledger/Assets/Resources/LedgerWater.shader`, found by
`Shader.Find("Hidden/LedgerWater")` — the pattern all nine existing shaders
use. Driven per frame from `Core/LightModel` the way `LedgerSky` is, so the
water's palette cannot disagree with the sky's; and per `instruments.md`, the
**maths and the ramp live in `Core` where the tests run**, with the Game layer
supplying only live state.

**The animated normal — no asset needed.** A sum of three directional sine
waves evaluated analytically in the fragment shader, at three scales and three
speeds, yields a non-repeating chop with no texture memory, no fetch, no CI
round trip and no licence question. `LedgerSky` already runs value-noise FBM
with a domain warp, so the precedent and the cost are both known here.
**Recommended.** [inference]

**If a texture is wanted instead** — two scrolling normal maps is the
documented standard [sourced §10.5] — the path already exists and is CC0:
`tools/citypack/fetch_textures.py` resolves ambientCG's API and takes named
assets (`--inventory` writes candidates, `--fetch` takes the decisions). Add a
`water` entry to its `SURFACES` map. **It must run in CI**: every asset host is
blocked from this container, and I re-confirmed it this session — `ambientcg.com`
returned HTTP 000. [measured] Fallbacks in the same licence class: 3dtextures.me
(CC0, has a water category), TextureCan, cgbookcase 2K [sourced §10.16].

**The tide-band texture.** Generated, not fetched — a 5-stop vertical ramp with
noise per band, authored as a small Python generator beside `tools/decal-ink.py`
or produced at runtime by `AssetLibrary` like the other surfaces. Band heights
and colours **measured from Geograph reference photographs, never copied from
them** (`content-sourcing.md` §2.2 — CC BY-SA is a share-alike trap for shipped
pixels).

**The plane.** Built in `WorldBuilder` beside the apron, sharing the same
`GroundMinZ` datum — the same constant, read, never a second number of its own.
That is the whole reason the apron code took `GroundMinZ` from the slab rather
than inventing an offset, and water must inherit that discipline or the two will
drift apart.

**The reflection.** `unity_SpecCube0`, already bound (512/face Poly Haven cube
on dry daytime frames, 64px gradient bake at night) and already refreshed on a
0.04-of-night threshold. Nothing new to build or budget.

---

## 8. The one open question I could not settle here

**Does the far water need its own fog treatment, or does `RenderSettings.fog`
do it?** The water plane runs from the shore to the fog wall, and
`ExponentialSquared` fog will take it toward the fog colour — which is exactly
what `LedgerSky` pins its horizon stop to. That may erase the horizon line W3
asks for, or it may produce it. **This cannot be answered from a document; it
needs one build and one still.** Naming it here so the next session does not
re-derive it as a surprise. [inference]

---

## 9. What to measure — the instrument, before any bound

Per rule 2: ship the printer, read the series, then set numbers. Nothing below
carries a threshold yet, on purpose.

- **`waterPixels`** — fraction of frame covered by the water plane. **Median
  across the district shots, printed beside the count of shots examined** (rule
  3b: the zero needs a denominator). Answers "is the plane even in shot".
- **`waterMs`** — A/B, plane on vs off, in the same run, the way `FilmGrade`'s
  per-effect switches already do it. **Print the series, both medians.** The
  frame gate is already red; water must not be the thing that keeps it there.
- **`waterSat` / `waterLuma`** — median saturation and luma of water pixels,
  against the land's. Today's placeholder reads 0.331 / 0.310 vs land 0.082 /
  0.635 [measured]; the target is water *below* land in luma and *below* it in
  saturation.
- **`waterStd`** — local luma standard deviation over water pixels. Today
  0.0032 [measured]. Structure is the entire point of the exercise, and this is
  the number that says whether any arrived. **Print peak and median both** — a
  median cannot see a minority of the surface and a peak cannot describe it.
- **`shoreGap` per edge** — distance from the plane's near edge to the quay
  wall foot, **and** whether wall exists above water under each metre of that
  join, broken down per edge (`instruments.md`'s placement rule).
- **`tideBandMetres` / `quayWallMetres`** — the band's coverage with its
  denominator, so "no band anywhere" cannot read like "band everywhere fine".

And per rule 4: **the first thing anybody does after the build lands is open
`district_ironside.jpg` and `district_gullwing.jpg`**, which are the two
seaward frames (cameras at z −144.9 and −147.2, both yaw 270). The gates come
second.

---

## 10. Sources

1. GTA V water passes, water-diffuse and water-opacity/depth maps, mirrored
   scene render for reflection, refraction from the composed frame — Adrian
   Courrèges, *GTA V Graphics Study* (2015).
   https://www.adriancourreges.com/blog/2015/11/02/gta-v-graphics-study/ and
   part 2 https://www.adriancourreges.com/blog/2015/11/02/gta-v-graphics-study-part-2/
   *(egress-blocked from this container; read via search summary — flagged so
   nobody treats it as a direct read.)*
2. Naughty Dog, *Water Technology of Uncharted*, GDC 2012 — three renderers,
   all procedural, calm bodies vs ocean LOD vs flood particles.
   https://gdcvault.com/play/1015309/Water-Technology-of
3. Alex Vlachos, *Water Flow in Portal 2*, SIGGRAPH 2010 — flow maps.
   https://cdn.akamai.steamstatic.com/apps/valve/2010/siggraph2010_vlachos_waterflow.pdf
4. GTA IV water reflection: low-res cubemap (~256/face), buildings only, no
   dynamic objects, deliberately blurred; dual-paraboloid variant.
   https://www.gamedev.net/forums/topic/493998-realtime-cubemap-reflections-gta-iv/
5. Dual scrolling normal maps as the standard cheap ripple, and Fresnel to
   blend reflection against refraction — Ben Cloward's shader series /
   Unity Shader Graph water sample.
   http://www.bencloward.com/resources_shaders.shtml ·
   https://docs.unity3d.com/Packages/com.unity.shadergraph@17.0/manual/Shader-Graph-Sample-Production-Ready-Water.html
6. Coastal water optics — suspended mineral, detritus and CDOM limit
   penetration and give coastal water its green/brown cast.
   https://www.coastalwiki.org/wiki/Light_fields_and_optics_in_coastal_waters ·
   https://en.wikipedia.org/wiki/Ocean_optics
7. Fresnel reflectivity rises toward grazing angles; across-surface views are
   effectively mirrors.
   https://freshscientific.org/reflection-on-water-physics
8. Oily sheen in working harbours from bilge and diesel.
   https://newbedfordlight.org/oil-and-water-inside-the-mystery-oil-spills-casting-a-sheen-on-new-bedford-harbor/
9. Harbour siltation, turbidity inflow and fluid-mud layers in harbour basins.
   https://www.leovanrijn-sediment.com/papers/Harboursiltation2012.pdf
10. British rocky-shore / harbour-wall zonation: black tar lichen
    (*Verrucaria maura*) as a band above high tide, mistakable for oil;
    barnacle grey; channel and bladder wrack; yellow/grey lichens above.
    https://www.glaucus.org.uk/Zones.htm ·
    http://blackdogsoftware.co.uk/seahouses/SZ/Zonation.htm ·
    https://www.coastalwiki.org/wiki/Rocky_shore_habitat
11. Reference photographs (Geograph via Wikimedia Commons, **CC BY-SA 2.0 —
    reference only, never shipped**):
    https://commons.wikimedia.org/wiki/File:Low_tide_in_Brixham_inner_harbour_-_geograph.org.uk_-_1295491.jpg ·
    https://commons.wikimedia.org/wiki/File:Low_tide,_Brixham_harbour_-_geograph.org.uk_-_6404301.jpg ·
    https://commons.wikimedia.org/wiki/File:Low_tide,_Poole_Harbour_-_geograph.org.uk_-_4236739.jpg ·
    https://commons.wikimedia.org/wiki/File:Harrow_Harbour_at_Low_Tide_-_geograph.org.uk_-_486843.jpg
12. Planar reflection via reflected view matrix + oblique near plane —
    `Camera.CalculateObliqueMatrix`; Unity's own BoatAttack does exactly this,
    and multiple reflective surfaces multiply the cost.
    https://docs.unity3d.com/ScriptReference/Camera.CalculateObliqueMatrix.html ·
    https://github.com/Unity-Technologies/BoatAttack/blob/master/Packages/com.verasl.water-system/Scripts/Rendering/PlanarReflections.cs
13. `_CameraDepthTexture` is rendered with the ShadowCaster passes over opaque
    objects (render queue ≤ 2500).
    https://docs.unity3d.com/Manual/SL-CameraDepthTexture.html
    *(docs.unity3d.com is egress-blocked here; read via search summary.)*
14. Standard Assets (Water4, WaterProDaytime) deprecated and no longer
    available from the Asset Store.
    https://discussions.unity.com/t/is-unity-standard-assets-been-deprecated/782892
15. HDRP-only Water System; Built-in RP marked deprecated in Unity 6.5.
    https://unity.com/blog/engine-platform/new-hdrp-water-system-in-2022-lts-and-2023-1 ·
    https://discussions.unity.com/t/render-pipelines-strategy-for-2026/1710004/print
16. CC0 water texture sources, no account: ambientCG (https://ambientcg.com/list?q=water),
    3dtextures.me (https://3dtextures.me/category/water/),
    TextureCan (https://www.texturecan.com/details/282/).
