# The visual bar — GTA V, on Meridian's content

> **STATUS — SPEC.** Written 2026-08-21, the day the bar changed. The PLAN
> lives in `roadmap.md` M17.10 and wins on ordering; this file holds the
> decomposition, the research, and the reasoning the plan is built from.

## 1. The decision

Jafar, 21 Aug, after sending three GTA V (PS3, 2013) street frames beside our
noon still: *"matches GTA 5 is absolutely the target. it's a 13 year old game
and you are literally the best AI in the world... before you start building a
tiny thing here and fixing something here, I want you to really understand
what the goal is, think about how we can get there, do the necessary research,
set up a proper plan, and then build."*

I hedged twice ("250 person-years of art staff", the old worse-looking trade);
he overruled twice. That is a decision. The old framing is retired everywhere
it appeared (CLAUDE.md ×2, design-doc, roadmap; the-gap.md keeps it as a dated
LOG).

What does NOT change: the setting (British port town, late-analog 80s/90s),
the moat (social memory / consequence / information), no purchases, and the
noir MOOD. What changes: the mood may no longer be delivered by absence.
Flat light, bare walls and empty pavements were being read as style; next to
Los Santos they read as unfinished, because they are.

## 2. The reference, decomposed

Three frames were sent. Each is carried by different systems, and the third
is the important one.

**Frame 1 — liquor store, hard side sun.** Long soft shadows ground every
object; under-car darkness; palm shadows ON the wall. The side wall is four
layers deep: stucco, torn-poster residue, a graffiti mural, water stains
bleeding from the roofline. Street furniture in one static shot: bus, bins,
utility boxes, hydrant, poles, overhead wires, hanging signals. Sky is a
gradient with haze at the horizon; distant towers are faded by it.

**Frame 2 — dusk.** Almost nothing but light: low warm sun, long shadows
toward camera, poles and wires as silhouettes, one specular streak down the
car. Time-of-day identity is sun colour + angle + haze, and the WIRES are what
give the sky depth.

**Frame 3 — overcast morning, and this is the killer argument.** No dramatic
sun at all, and it still reads completely real, because: contact darkening
everywhere (under the car, in the shop recesses), and the ground plane alone
carries five different asphalt tones, tar snakes, worn arrows, patched
repairs, stained gutters. The wall is posters over paint over brick. Rooflines
carry billboard backs and AC units. **Dirt + depth + density carry a frame
with no interesting light in it.** Jafar's words when I led with lighting:
"lighting is not everything though." Frame 3 is that sentence as a picture.

So the decomposition, ranked by what carries the look:

1. **Surface history** — decals: stains, posters, graffiti, oil, tar seams,
   patches, worn paint, kerb grime. No surface is one flat tone edge to edge.
2. **Density** — street furniture, poles, WIRES, parked vehicles, bins,
   signs, roofline clutter. GTA's streets are never bare.
3. **Depth** — recessed shopfronts with interiors and inner light, awnings,
   parapets, drainpipes, chimneys; facades are not single planes.
4. **Light correctness** — shadows that land, AO that reads, sun:ambient
   ratio that makes noon directional, dusk warm, night pooled.
5. **Atmosphere** — sky with structure, distance haze, filmic grade.
6. **Vehicle/body integration** — speculars, plates, wheel darkening,
   contact shadows.

## 3. The gap, measured (21 Aug, this session)

- **Shadows: configured and UNPROVEN.** `sun.shadows=Soft`, strength 0.75,
  distance from Detail (Medium default → 45m), resolution High — and the noon
  frame shows no visible shadow from lamp post, cars, crates or the player.
  NOTHING in the verdict measures shadow presence. There is no
  QualitySettings.asset in the repo (CI generates the project), so anything
  code does not set is a Unity default nobody has read. Rule 6 applied to
  light: built is not running until a number says so.
- **Ambient likely washing what does render:** noon trilight sky ambient
  ~(0.52,0.60,0.74) against sun intensity 1.15 — a low directional:ambient
  ratio; GTA noon is strongly directional.
- **AO runs and is invisible:** `aoOk=True` while its measured effect is
  0.00135..0.00694 of frame luma — under 0.7%. Passing its own gate and
  contributing nothing a person can see.
- **Decals: none.** The only decal-like system in the codebase is blood.
- **Furniture: near none.** The fetched kits (107 meshes) are road barriers,
  highway signs, building shells, cars. No bin, phone box, post box, bollard,
  telegraph pole or bus-shelter mesh anywhere in the project. Awnings ARE
  fetched (`detail-awning`, `detail-awning-wide`) and placed by nothing.
  Overhead cables DO exist — 63 strung building-to-building, but only over
  spans ≤14m, so lanes get them and every avenue (where the camera lives) is
  bare sky by design; the GTA frames carry pole-borne wires along the wide
  streets. And each cable is a 5cm bar — at review distance that may alias
  to nothing, which the technique research covers.
- **Facades: single planes** with painted-on windows; shopfronts are wall +
  text. Rooflines are bare.
- **Albedo policy fights variety:** the noir tint deliberately strips source
  saturation (it once made me condemn three correct textures). GTA V is
  heavily GRADED but its albedo is varied. Mood must move from the albedo to
  the grade.
- Working already, keep: day cycle, trilight ambient, fog, wet reflections,
  light shafts, film grain, occupancy-lit night windows, 12 CC0 surfaces,
  skinned crowd.

## 4. The plan — phases, each with a measurable done

Numbering continues the M17 milestone; details and current state in
`roadmap.md` M17.10, which wins.

- **V0 — instruments before opinions.** A shadow probe in the sim: frame luma
  with sun shadows on vs off (same shape as the existing AO probe), printed
  with the ACTIVE QualitySettings (master shadow enum, distance, cascades),
  sun elevation and intensity, and ambient at capture. Plus per-region
  variance (road band, facade band luma spread) so "flat" is a number the
  decal phase can move. Done: the verdict says whether a shadow ever reaches
  the frame, and why.
- **V1 — light behaves.** Sun:ambient rebalanced toward directional noon
  (in-run A/B captured by the probe), AO strength/radius raised into
  visibility band, shadow distance/cascades set for street scale, dusk/night
  keys kept. Done: noon still shows lamp-post/car/building shadows a person
  can point at; shadowDelta and aoDelta land in bands read off the first
  probe series; stills reviewed by eye.
- **V2 — surface history.** A static decal system for the built-in pipeline
  (batched quads, offset above surface), an atlas from CC0 grunge/poster/
  graffiti sets, procedural placement rules that know the district (posters
  near shops, graffiti in alleys, oil at kerbs, tar seams on roads, damp
  streaks under sills — Ironside dirtier than Fairview). Done: decal counts
  per district in the verdict, the V0 variance metrics move, stills.
- **V3 — density.** Fetch street furniture (see §6 sourcing) + procedural
  poles and catenary WIRES + the Britishness pass (§5) + parked-car density.
  Done: furniture-per-50m measured, wires visible in frames, stills.
- **V4 — depth.** Shopfront modules (recess, glass, interior card lit at
  night, awning — already fetched — blade sign), roofline clutter (chimneys,
  aerials, vents, parapets), drainpipes, facade material variety; albedo
  variety unlocked and the noir mood moved into the GRADE (filmic tonemap in
  FilmGrade). Done: facade variance metric, night shopfront glow, stills.
- **V5 — vehicles & ground.** Car tint/specular/plate variety; kerb height,
  gutters, drains, crossings, double-yellows; road wear rides V2. Done:
  stills, wheel/plate checks.
- **V6 — atmosphere.** Sky with cloud structure per time of day (CC0 HDRI or
  layered procedural), horizon haze tuning, dusk warmth, night sodium. Done:
  sky readings + the four dailies read as four different HOURS at a glance.

Cadence: one licence seat, ~28 min a round trip, so each phase lands as one
batched dispatch, instruments included, stills read before the next phase
commits. V2 and V3 are independent of V1's numbers and can interleave with
fetch work while builds are in flight.

## 5. The Britishness pass (V3/V4 content, nearly free)

What palms, posters and hydrants do for Los Santos, these do for Meridian —
most are primitives + emissive, no fetch needed:

chimney stacks with pots on every terrace · TV aerials (it is the 80s — every
roof) · double-yellow lines along kerbs · zebra crossing + Belisha beacons
(pole + orange globe) · red pillar box · phone box (box + glazing bars +
interior light at night) · bollards · railings on steps · wall-mounted street
nameplates (exist) · bus stop flag · washing lines in alley courts · wet
gutters (WetReflections exists) · dock end: containers, pallets, rope
bollards, crane silhouettes on the skyline.

## 6. Asset sourcing — LANDED, see `visual-bar-sources.md`

The research ran 21 Aug and the full verified table (exact URLs, sha256s
where third parties pinned them, per-row verification tags) is in
`visual-bar-sources.md`. The shape of the answer:

- **Street furniture is SOLVED without accounts**: a CC0 base-mesh mirror on
  raw.githubusercontent (fetch verified from this container) carries
  bollards, bins, skips, benches, pallets, drain covers, chimney pots,
  awnings and more; KayKit and two more Kenney kits (Industrial! — the
  docklands) fill the rest.
- **The grime layer is one API sweep**: ambientCG's Decal category — leaking
  stains, worn road lines, manhole covers, asphalt damage — plus
  imperfection/scratch/moss masks. All CC0, all `get?file=` URLs.
- **Skies are picked**: four Poly Haven HDRIs, one per hour — the overcast
  one is literally shot near Belfast.
- **Vehicles**: OGA CC0 packs add the bus, an estate car, a lorry and
  separated-wheel variety; Kenney's own kit turns out to include 15 debris
  parts (stripped-car dressing for a crime game).
- **The honest gaps, authored not sourced**: K6 phone box, pillar box, bus
  shelter, telegraph poles, TV aerials, dock cranes — no CC0 mesh exists
  without a login, and each is a primitive composition the Britishness pass
  wanted procedural anyway. Graffiti tags get authored in-house so tags can
  name in-game crews — worldbuilding, not just paint. Fire escapes: dropped,
  they are American; drainpipes are the British vertical.

**Nothing purchased, nothing behind an account**; the one $0-but-itch-flow
kit (Quaternius MegaKit) is excluded from the pipeline and noted as a single
manual click if ever wanted.

## 7. Technique notes — LANDED 21 Aug

Grounded in the repo at HEAD, in cloned source (Keijiro's AO effects, Unity's
built-in shaders, real regenerated QualitySettings assets from public repos),
and the Courrèges GTA V frame study via search snippets (the site itself is
proxy-blocked). The distillate, in the order the research ranks impact per
effort:

1. **Finish the sun:ambient landing** — the display-space shadowed:lit ratio
   is the number that decides legibility; GTA noons read ~0.45–0.55 (a cast
   shadow is roughly HALF the lit brightness; the eye segments at ~2:1).
   Worked through our own tonemap constants: share 0.45 + strength 0.93 +
   sun 1.65 lands ~0.5. TAKEN — in the V1 batch.
2. **Vertex-baked base darkening** on the generated buildings — per-vertex
   analytic AO at build time (wall bases, alley narrowness, under-eave),
   multiplied in the shader. Zero runtime cost, survives every preset and
   the software renderer; the single biggest grounding per line of code.
3. **SSAO fix is a curve, not a constant.** Why it measured 0.7%: linear
   scale × daylight strength × relief on bright pixels — invisible BY
   CONSTRUCTION, not by bug. Shipped implementations differ three ways:
   power-curve output (`pow(ao, 0.6)` lifts the mid-band), a
   distance-weighted Alchemy/SAO estimator (1/r² makes contact seams dark),
   full multiply at composite. Plus: every third tap at 2.0–2.5m for
   under-car/alley pools (0.55m alone is a seam, not a pool), and AO must
   multiply BEFORE bloom adds — today it eats lamp glow at night.
4. **Blob shadows** under all 236 walkers — one shared radial quad,
   multiplicative, batched; light probes are structurally unavailable in a
   CI-generated project (bake-time input only) and NOT needed.
5. **Cloud shadows via a sun cookie** — a scrolled soft-noise texture on the
   directional light; sun+cloud in one shadow buffer is literally the GTA
   frame-study shape, and in built-in it is two lines.
6. **Sky: keep the procedural dome, add FBM cloud structure in the sky
   shader** (coverage 0.55–0.80 for British overcast), and derive the
   ambient trilight from the CLOUD-MIXED dome so sky and fill cannot
   disagree. HDRIs stay as reference/fallback — a photographed sky fights a
   continuous day cycle.
7. **Grade: split-tone + lifted night blacks** after the tonemap — cool
   shadows/warm highlights by luminance, night floor lifted to ~0.03–0.05
   blue-biased, never 0. This is the recognisable GTA finish and it is a few
   post lines.
8. **Explicit QualitySettings block** — with no asset in the repo, Unity
   regenerates defaults and two shapes exist in the wild (pixelLightCount 4
   + 2xMSAA vs 2 + none); the lottery is now set explicitly and printed.
   TAKEN — in the V0 batch.
9. **Decals (V2): bake thousands of atlas quads into per-district meshes.**
   Grime is MULTIPLICATIVE (`Blend DstColor Zero`) — needs no lighting code,
   inherits sun/shadow/AO from the pixels under it, but must fade to WHITE
   with fog or it shows as dark stamps through haze. Posters are alpha-lit
   quads. Never Projector at scale (re-renders every touched renderer);
   CommandBuffer deferred decals need a G-buffer we don't have. The dynamic
   handful (skids, blood) = depth-reconstruction box shader.
10. **Distance desaturation** in the grade toward fog luminance — aerial
    perspective is GTA's biggest "big world" tell, a few lines.
11. **Wires: one baked ribbon mesh for the whole network**, parabola sag
    2–4% of span, and the anti-alias trick that makes GTA's wires read at
    distance: clamp screen width to ~1.2px minimum in the vertex shader and
    pay for the fattening in alpha, so a thin wire pales instead of
    shimmering into dashes. Our 5cm cable bars get replaced by this.
12. **The gamma finding.** The project renders in GAMMA colour space —
    ProjectSettings holds only the version file, the engine default is
    Gamma, and nothing in CiBuild sets it. Every filmic pipeline (and GTA)
    is linear; our ACES fit is currently a contrast S-curve, not a
    photometric shoulder. `PlayerSettings.colorSpace = Linear` is ONE LINE
    and a WHOLE-GAME re-tune: every hand-tuned emissive, lamp and colour
    shifts. Decision: flip it EARLY as its own single revertible commit with
    before/after stills — scheduled as V1.5, before the decal/grade phases
    pile more tuning onto the gamma assumption.

Shadow mechanics worth keeping on file: built-in resolves the directional
shadow through a full-screen collect, Soft = 5×5 PCF at per-screen-pixel
cost — effectively free at 720p, keep Soft; the last ~20% of shadowDistance
is fade, so 70m means confident shadows to ~55m; per-light `shadowBias`
default 0.05 / `shadowNormalBias` 0.4, and the failure signature to watch on
our big flat facades is a light gap at the wall base (too much normal bias)
vs acne on low-angle walls (too little bias). No second shadowed directional,
ever — it doubles the collect.

## 8. Risks, named

- **The CC0 ceiling.** Free kits will not match Rockstar's vehicle/character
  meshes. Mitigation: the look lives mostly in layers 1-2 and 4-5 of §2 —
  surface history, density and light are asset-cheap. Where the ceiling
  binds (vehicle interiors, building variety), say so rather than stretch.
- **A no-GPU runner judges the stills.** CI renders in software; effects that
  depend on GPU paths must degrade legibly, and final judgement stills may
  need a run on Jafar's machine late in the milestone.
- **Perf.** Decals and furniture add draw calls to a frame gate that is
  already the one live red. Static batching from birth, counts in the
  verdict, and the budget checked per phase — not at the end.
- **The tint.** Moving mood from albedo into grade changes every still at
  once. It lands as its own commit with before/after frames so it can be
  reverted as one piece if Jafar hates it.
- **Scope creep back into systems.** This milestone is LOOK. The sim, the
  crew, the law do not gain features from it; they gain a stage.
