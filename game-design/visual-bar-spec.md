# The visual bar — GTA V, on Meridian's content

> **STATUS — SPEC.** Written 2026-08-21, the day the bar changed.
> **§4 REPLACED 2026-08-25 by the director**, on Jafar's direct escalation
> ("this goal is a must"), after reading the five reference frames beside the
> landed stills. The PLAN is §4 of this file; `roadmap.md` M17.10 points here
> and wins on cross-milestone ordering only. §9 records why V0–V6 was
> replaced, so nobody re-derives it as still current.

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
LOG). Re-escalated 25 Aug: *"this goal is a must."*

What does NOT change: the setting (British port town, late-analog 80s/90s),
the moat (social memory / consequence / information), no purchases, and the
noir MOOD. What changes: the mood may no longer be delivered by absence.
Flat light, bare walls and empty pavements were being read as style; next to
Los Santos they read as unfinished, because they are.

## 2. The reference, decomposed

Five frames, committed byte-exact in `game-design/reference/` — READ THEM,
they are the bar. Each is carried by different systems; the third is the
important one.

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
**And note its SKY: overcast is a BRIGHT white-grey sheet, the brightest
surface in the frame.** That fact turned out to be the one our frames get
most wrong — see §4 R0.

Frames 4 (suburban noon) and 5 (PS3-labelled sidewalk) add: texture density
at PLAYER height, shadow dapple on pavement, grass seams in cracked slabs,
haze eating the towers. **All five are shot at eye level, 1.5–1.8m.** Not one
of our judgement stills is.

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

That ranking is what carries a HEALTHY frame. §4 reorders the WORK, because
25 Aug's frames fail below the ranking: the value structure the whole list
stands on is inverted, and detail painted onto a clipped ground is invisible.

## 3. What GTA V (PS3) actually does — the technique scorecard, 25 Aug

Researched (Courrèges' three-part frame study; PS3-generation accounts) and
judged against this repo at HEAD. What the RAGE renderer does, and where we
stand — HAVE / WRONG / NEVER:

| GTA V technique | us, honestly |
|---|---|
| Per-frame 128px HDR **environment cubemap**; everything reflective reflects a real sky+scene | **WRONG → fix in flight.** Our probe was a 64px three-colour gradient, and dry reflection intensity was ZERO for the whole project history. The HDRI-as-environment wire is coded, awaiting its landing (`skyLoadedAs`, `skyBound`) |
| HDR buffers + tonemap + per-hour artist-keyed grade | HAVE the shape (linear closed, ACES fit, split-tone); **WRONG value** — the 3.44 day aperture was calibrated against a broken ground response (§4 R0) |
| Sun CSM + **cloud shadows in one buffer**, dithered soft edges | HAVE (real noon shadows landed; cloud cookie landed) |
| SSAO + **baked AO in textures/verts** | HAVE SSAO (deepened); vertex-bake still open (§7.2) |
| Atmospheric-scattering sky, strong **aerial perspective haze** | PART — fog exists, distance desat landed; the DOME's per-hour luminance and cloud structure are open, and overcast reads storm-dark, which no real sky does over a lit street |
| Decal/grunge density everywhere | **NEVER at street scale** — wiring landed, sets fetched, placement blocked-then-split (§4 R2) |
| Hand-placed prop/wire/pole density | PART — furniture pass landed; **city-kit-roads 47 models with ONE placed**, suburban kit 13/0, avenue wires absent |
| LOD + haze hiding distance | HAVE (fog, far city, period skyline in flight) |
| Deferred, hundreds of dynamic lights | NOT PORTABLE (built-in forward here) — accepted; night is pooled lamps, which fits the town |

The honest summary: the individual techniques are mostly HAVE or in flight.
What is WRONG is the two things every technique feeds through — the
environment (what light and reflections COME FROM) and the exposure (what the
frame does with them). That is why a week of landed technique moved nothing
a person could see.

## 4. THE PLAN — replaced 25 Aug. Converge on the frame, not on the list.

**The finding that reorders everything.** Put `district_ironside.jpg` or
`review_day2_noon.jpg` beside any of the five references. In every reference
the SKY is the brightest broad surface, walls sit below it, the ground sits
mid-dark with the widest tonal variety in the frame, and every object stands
on contact shadow. In ours the ordering is INVERTED: near-white ground, dark
slate sky, windows as black grids. A frame whose light is impossible reads as
fake before any detail is judged — and detail added to a white-clipped ground
cannot even be seen. Cause chain, measured this week: an albedo-blind
additive term on the ground (specular/reflection suspect, A/B in flight) ×
a 3.44 noon exposure raised to fix a real day/night ratio fault ×
an overcast dome authored storm-dark. Three levers, one inversion.

### R0 — VALUE STRUCTURE. Nothing else is judgeable until this lands.

- **R0.a (in flight)**: the attribution batch as ruled in
  `decision-ground-albedo.md` (per-material ray distance, `_GlossMapScale=0`
  A/B, fogOff planted rung, MeanTexLuma audit) + the skyline/apron batch.
  Order and "no contested lever moves in that batch" stand.
- **R0.b**: the fix the A/B names (expected: ground specular path), then the
  aperture set ONCE off the post-fix printed series — the 2.44 day term is a
  wrong value arrived at correctly and is not defended.
- **R0.c**: **bright overcast.** Dome + fog luminance for overcast/rain
  raised until the sky band outreads the wall band; British overcast is a
  bright grey sheet (reference frame 3), not a storm ceiling. Rides with or
  immediately after R0.b; cross-run series take a regime mark.
- **R0.d**: windows read the real environment — already coded; read
  `skyLoadedAs=Cube`/`skyBound` and the STILLS at its landing.

**Gate (ordering, not invented thresholds — rule 2 compliant):** at noon,
dry or overcast, per paired still: `skyBand > litWallBand > groundBand >
shadowBand`, AND rendered ground lumas order as their source albedos do
(asphalt < kerb < paving). Margins set later from the landed series; the
ORDER is from the references, 7/7 already on the sky-vs-ground half.

### R1 — THE CONVERGENCE INSTRUMENT. Ships WITH R0, not after.

- **Five player-height cameras** (~1.7m eye, ~60° vfov) matched to the five
  reference compositions, committed every run as `ref_1..ref_5` stills. The
  done-test is Jafar's eye on OUR frame beside HIS frame; today no committed
  still is even the right kind of photograph — every judgement frame is
  aerial. Aerial shots stay for audits and stop being judgement frames.
- **Five hand-painted reference mattes** (approved 25 Aug, unbuilt) masking
  car/HUD, so `ref-bench` magnitude becomes quotable — today only direction
  is supportable.
- **The panel, small and fixed**, per paired still: sky/wall/ground band
  medians, shadowed:lit ratio (GTA noon reads ~0.45–0.55, §7.1), ground-band
  tonal spread. Schema changes carry regime marks.

**Convergence is defined, so "sideways" is detectable:** at every landing,
read the five pairs and WRITE DOWN the biggest visible difference in one
sentence. We are converging while the panel moves toward the reference side
and the biggest-difference sentence changes. **The same sentence three
landings running is the next phase, whatever this plan says.**

### R2 — GROUND SURFACE HISTORY. After R0.b (invisible on a clipped ground).

Asphalt at its source albedo; tar seams, patch rectangles, oil, kerb grime,
worn markings; the roads-kit crossings and junctions. Gate: ground-band
tonal spread moves toward the reference mattes'; a paired still shows three
distinguishable tones on one carriageway; decal counts per district.

### R3 — STREET-LEVEL DENSITY. Startable NOW as ride-along visible work.

`city-kit-roads` (47 models, ONE placed — kerbs, crossings, barriers, cones,
junctions, the densest unused kit and all at eye level), `city-kit-suburban`
(13/0), parked-car density, pole-borne avenue WIRES with the ~1.2px width
clamp (§7.11). Wall-side surface history — posters, damp streaks, painted
signs — is NOT blocked by the ground question and belongs here too.
Gate: `prop-reach` per-kit counts, furniture-per-50m, paired stills.

### R4 — DEPTH remainder. Roofline clutter, window reveals, albedo variety
with the noir mood moved fully into the grade (§7.7). Gate: facade variance
+ paired stills.

### R5 — ATMOSPHERE. Dome cloud structure per hour (overcast 0.55–0.80
coverage), dusk/night keys (first slice landed), aerial desat tuning.
Gate: the four dailies read as four different HOURS at a glance; sky
readings.

### Cadence — the two standing rules that fix this week's failure mode

1. **Every dispatch ships at least one visible change** a person can point
   at in a paired still (from the earliest phase with startable work — R3
   and wall-R2 are startable today), unless a red gate blocks the build.
   Measurement-first governs LEVERS (rule 2, untouched); it was never a
   licence for measurement-ONLY dispatches, and this week it became one:
   ~15 instrument fixes, one visible change, one regression.
2. **Paired stills are read before any number at every landing** (rule 4,
   now with frames that are actually comparable), and the washout is the
   standing proof: a 3.07× exposure lift shipped and the next two days went
   to measuring its symptom because nobody put the new noon beside the old
   one at the landing.

**Done looks like** (unchanged in substance, sharpened in kind): Jafar puts
our `ref_*` noon/dusk/night player-height stills beside his five frames and
calls the bar met; every phase closed on a number AND a paired still.

## 5. The Britishness pass (R3/R4 content, nearly free)

What palms, posters and hydrants do for Los Santos, these do for Meridian —
most are primitives + emissive, no fetch needed:

chimney stacks with pots on every terrace · TV aerials (it is the 80s — every
roof) · double-yellow lines along kerbs · zebra crossing + Belisha beacons
(pole + orange globe) · red pillar box · phone box (box + glazing bars +
interior light at night) · bollards · railings on steps · wall-mounted street
nameplates (exist) · bus stop flag · washing lines in alley courts · wet
gutters (WetReflections exists) · dock end: containers, pallets, rope
bollards, crane silhouettes on the skyline (period blocks landed 25 Aug).

## 6. Asset sourcing — LANDED, see `visual-bar-sources.md`

The research ran 21 Aug and the full verified table (exact URLs, sha256s
where third parties pinned them, per-row verification tags) is in
`visual-bar-sources.md`. The shape of the answer:

- **Street furniture is SOLVED without accounts**: a CC0 base-mesh mirror on
  raw.githubusercontent carries bollards, bins, skips, benches, pallets,
  drain covers, chimney pots, awnings and more; KayKit and two more Kenney
  kits (Industrial! — the docklands) fill the rest.
- **The grime layer is one API sweep**: ambientCG's Decal category — leaking
  stains, worn road lines, manhole covers, asphalt damage — plus
  imperfection/scratch/moss masks. All CC0, all `get?file=` URLs.
- **Skies are picked**: four Poly Haven HDRIs, one per hour — the overcast
  one is literally shot near Belfast. (Since 24 Aug: environment/reflection
  source only; the visible dome stays procedural.)
- **Vehicles**: OGA CC0 packs add the bus, an estate car, a lorry and
  separated-wheel variety; Kenney's own kit includes 15 debris parts.
- **The honest gaps, authored not sourced**: K6 phone box, pillar box, bus
  shelter, telegraph poles, TV aerials, dock cranes — primitive compositions
  the Britishness pass wanted procedural anyway. Graffiti tags authored
  in-house so tags can name in-game crews. Fire escapes dropped (American);
  drainpipes are the British vertical.

**Nothing purchased, nothing behind an account**; the one $0-but-itch-flow
kit (Quaternius MegaKit) is excluded and noted as a single manual click if
ever wanted.

## 7. Technique notes — LANDED 21 Aug, scorecard in §3

Grounded in the repo at HEAD, in cloned source (Keijiro's AO effects, Unity's
built-in shaders, regenerated QualitySettings assets from public repos), and
the Courrèges GTA V frame study. In impact-per-effort order:

1. **Finish the sun:ambient landing** — display-space shadowed:lit ratio
   ~0.45–0.55 (a cast shadow is roughly HALF the lit brightness; the eye
   segments at ~2:1). TAKEN — V1 landed.
2. **Vertex-baked base darkening** on generated buildings — per-vertex
   analytic AO at build time (wall bases, alley narrowness, under-eave),
   multiplied in the shader. Zero runtime cost. STILL OPEN.
3. **SSAO fix is a curve, not a constant** — power-curve output, Alchemy
   estimator, full multiply before bloom, every third tap at 2.0–2.5m.
   TAKEN (deepened).
4. **Blob shadows** under all walkers — one shared radial quad. TAKEN.
5. **Cloud shadows via a sun cookie** — sun+cloud in one buffer is the GTA
   frame-study shape. TAKEN.
6. **Sky: procedural dome + FBM cloud structure**, coverage 0.55–0.80 for
   British overcast; ambient trilight derived from the CLOUD-MIXED dome so
   sky and fill cannot disagree. OPEN — and R0.c adds: the dome's LUMINANCE
   per weather state is the first-order term, before its structure.
7. **Grade: split-tone + lifted night blacks** after the tonemap. TAKEN.
8. **Explicit QualitySettings block.** TAKEN.
9. **Decals: bake thousands of atlas quads into per-district meshes.**
   Grime is MULTIPLICATIVE (`Blend DstColor Zero`), must fade to WHITE with
   fog; posters are alpha-lit quads; never Projector at scale. Wiring
   landed; placement is R2/R3.
10. **Distance desaturation** toward fog luminance. TAKEN.
11. **Wires: one baked ribbon mesh**, parabola sag 2–4% of span, screen
    width clamped ~1.2px minimum in the vertex shader, paid in alpha. OPEN.
12. **Linear colour.** TAKEN (V1.5 closed); MPB gamma class-fault open at
    13 sites.

Shadow mechanics on file: built-in resolves the directional shadow through a
full-screen collect, Soft = 5×5 PCF at per-screen-pixel cost — free at 720p;
the last ~20% of shadowDistance is fade; bias failure signatures: light gap
at wall base (too much normal bias) vs acne on low-angle walls (too little).
No second shadowed directional, ever.

## 8. Risks, named

- **The CC0 ceiling.** Free kits will not match Rockstar's vehicle/character
  meshes. The look lives mostly in §2 layers 1–2 and 4–5, which are
  asset-cheap. Where the ceiling binds, say so rather than stretch.
- **A no-GPU runner judges the stills** — degraded-legibly effects; final
  judgement may need a run on Jafar's machine late in the milestone (his
  runner builds now, which also cut the round trip to ~17 min).
- **Perf.** Decals and furniture press the one live red gate. Static
  batching from birth, counts in the verdict, budget checked per phase.
- **The tint.** Mood moving from albedo into grade lands as its own commit
  with before/after frames, revertible as one piece.
- **Scope creep back into systems.** This milestone is LOOK.
- **NEW 25 Aug: instrument gravity.** The failure mode this replacement
  answers — measurement work displacing visible work for a week — will
  recur, because instruments generate their own follow-ups. The cadence
  rules in §4 are the guard; if a dispatch goes out with no visible change
  and no red excuse, that is a plan violation, not a judgement call.

## 9. Why V0–V6 was replaced — LOG of the 25 Aug judgement, kept short

V0–V6 was a correct DECOMPOSITION and a wrong EXECUTION, three ways:

1. **Its done-states measured that systems existed, not that frames
   resembled.** Decal counts, furniture-per-50m, deltas — all presence
   numbers. Most phases "closed" while the frames moved sideways; nothing
   in any done-state could notice the whole picture reading as inverted.
2. **No phase owned the value structure.** Light was V1, one list item among
   six, and V1 "closed" on shadow presence while exposure, ground response
   and dome luminance — the three levers under every other phase — had no
   owner. The albedo-blind ground was found by accident, two days after our
   own exposure change surfaced it, and was not connected to that change.
3. **The judgement frames were the wrong photograph.** Every reference is at
   eye level; every judgement still was aerial. Convergence to a target you
   never frame is not measurable by any statistic.

The phase CONTENT survives (mapped: V2→R2 split wall/ground, V3→R3, V4→R4,
V6→R5, V0/V1→R0/R1). What changed is the spine: value structure first, a
convergence instrument that photographs what the bar photographs, and a
cadence rule that makes visible work non-optional per dispatch.
