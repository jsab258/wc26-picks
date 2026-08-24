# The work stack

> **STATUS — LIVE**, verified 2026-08-21. What gets picked up next, in order.
> The plan is `roadmap.md` and it wins; this is the next few hours of it.

## Why this file exists, and how to use it

The next items are written down BEFORE a dispatch and taken from the top
afterwards, so no judgement is required at the exact point where judgement was
failing. Full account in CLAUDE.md under AUTO MODE.

- **Every item fits inside one build round trip (~28 min)**, or it gets split.
- **CI-needed items are marked** and batched into the next dispatch.
- **Take from the top; move finished items out.** `roadmap-history.md` holds
  the cut blocks and `docs-check` caps this file at 400 lines, which is what
  forces the tidy.
- **`## Standing work` never empties.** Running out of short items is a refill
  signal, not a stop signal.

---

## Now

### Where the street got to

Clips: 65 filled, 0 wrong. The street talks, argues, leans, works
counters. **The front is M17.10: the visual bar is GTA V** — item 1.

**THE PLAYTEST IS RETARGETED (22 Aug, Jafar):** *"I'll try to run it on
my windows machine after visual stuff is done. live voices/speech should
be working too."* His pipeline run came back ALL CLEAR at **1.7x real
time** on DirectML — the overhang is the SERIAL stages, not the model
(~25 tok/s both ways). Speech stage's first item: **the fp16 lever,
measured on his card** (one-click converter+timer shipped 22 Aug). The
streaming overlap exists in the backend, gated on a sustainability test
his card misses by ~15%; if his number clears ~1.0x the backend needs
Float16 binds and edge conversions (fp32-typed today).
`playtest-plan.md` has the session runbook; keep speech self-checks
green on every landing.
**THE RUNNER IS REGISTERED AND FLIPPED (22 Aug): `ledger-pc` builds
on his machine**; account in `roadmap-history.md`. **ALL 72 GATES
GREEN and holding.** ~17.6 min/round on his GPU vs cloud 33-41 over
11 rounds; the BUILD is no longer the bottleneck, the dispatch
cadence is. Closed 23 Aug: hair, furniture, clip sheet, dayJob and
beats (both onto StreetMap.Route), shopfront joinery.

**PERFORMANCE IS MEASURED; THREE GUESSES DIED.** `frameCost` ladder:
all:22.4 noShadow:17.3 noPixLights:18.0 noBodies:23.3. **Shadows 5.1ms
and per-pixel lights 4.4ms hold the frame; the crowd is not in the
bill.** Dead: draw calls, vertex budget, shadow reach. Only the rungs'
DIFFERENCES are a frame time.

**THE STREET WAS NEVER AS EMPTY AS THE PICTURES.** Three faults, all
found by measuring, all closed: the draw radius stopped at 34m (now
70); `streetBodies` counted people THROUGH WALLS (linecast now); and
the cameras stood badly (`ShotMidBlockedAt=0.30` off its own bimodal
series, 12 of 13 shots fixed; the street shot also FLED the crowd).
Day frames are NOT like-for-like across these.

**23 Aug — THE DAY NOW READS AS DAY**, and it was a MEASUREMENT not
taste: a midday only a quarter brighter than a midnight. `Exposure`
had been revised SIX times off single frames; `exposureCurve` printed
the response instead, so the aperture was shown to be the lever. Day
arm 0.72 -> 2.44 lands noons 0.30-0.41, nights untouched, noon:night
1.25 -> **2.35:1**. **Two things would have eaten it silently: the
Clamp ceiling (1.85 against a noon of 1.72 — now 3.6) and the rain
term.** Three break fixtures re-anchored.

**SILLS ARE IN AND FREE** (2133, no collider; +2173 renderers with
render+rest UNCHANGED). Weathering went into the TEXTURE. **Ground
roughness maps bound, normalised by each map's own mean** — and that
binding silently killed THREE `_Glossiness` writers, see below.

**THE CROWD BEHAVES.** Density arrived as 13 people in convoy down the
CARRIAGEWAY: `Steer`'s first branch tested only for SOLID blockers, so
tarmac stopped nobody and every pavement rule below it was
unreachable. Guard on how far a line RUNS ON road (12m): headingIntoRoad
13 -> 5, crowdTightest 0.04 -> 0.23; its sampling cost 1.9ms until
coarsened 0.5m -> 1.5m. The frame then showed 1-2 people — correct
behaviour, fewer visible. DO NOT chase this by loosening the guard;
the lever is where ROUTES go. **meanFrame ~28.4ms with a ~1ms NOISE
FLOOR** (a comment-only build moved it 0.9ms), so single-run diffs
under 1ms mean nothing. `places` went red once and recovered untouched
(3/289 flaky). Revert `runs-on` if he bows out.
**BEFORE THE PLAYTEST, THE FULL ULTRACODE AUDIT** (Jafar, 22 Aug:
"a full ultracode audit before playtesting is a good idea"). Multi-agent
sweep of the whole codebase against every rule in CLAUDE.md, triaged into
the queue before he downloads the build. Pre-approved, token-heavy by design.

### Startable right now — JAFAR'S SEQUENCE (22 Aug, his words):
### "1. visual, 2. voices/speech, 3. playtest, then feedback/fixes and
### then continue w roadmap." Within a stage, order by what shows on
### screen. Nothing from a later stage starts while an earlier one has
### startable work, except reading a landed verdict, which is free.

1. **M17.10 — THE VISUAL BAR IS GTA V (PS3). Jafar's order, 21 Aug, twice.**
   *(the most on-screen thing there is)* Plan in `roadmap.md` 17.10,
   decomposition and research in `visual-bar-spec.md`. The look is carried by
   surface history, density, depth, light, atmosphere — in that order; his
   overcast reference frame proves dirt+depth+density carry a frame with no
   interesting light.

   **LANDED (accounts in `roadmap-history.md`):** V0+V1 whole; build D's kit
   furniture, yellows, chimney pots, aerials, reactions; **V1.5 LINEAR
   CLOSED**. Open from those passes: the sky dome (V6).

   **FOUR SKY HDRIs ARE FETCHED AND WIRED TO NOTHING** (24 Aug).
   `ledger/Assets/Sky/polyhaven/` holds 23MB of 2k captures, banked and
   attributed, and `grep` finds ZERO Game-layer references. Built and not
   running, on the one element in every outdoor frame.

   **DECIDED 24 Aug, ON EVIDENCE: THE REFLECTION/ENVIRONMENT SOURCE ONLY,
   VISIBLE DOME UNTOUCHED.** The numbers make the pick, not a preference.
   **Glass is smoothness 0.90 and Window 0.85** (`SurfaceSpec`), on every
   facade in town — already highly reflective. What they reflect is a **64px
   cubemap baked off a three-colour gradient**, no structure at all. The
   near-black windows in every landed frame are dark BECAUSE there is
   nothing to reflect, not because they were authored dark: that is the
   largest reflective area in the game sitting on an empty environment. The
   blend shape trades a CONTINUOUS day (dusk warmth, night sodium, a per-day
   deck the ambient reads from) for photographic detail and pops between
   four fixed states; reflection-only is additive and cannot regress it.
   **Obstacles, both real:** (a) `Resources.Load` cannot reach `Assets/Sky`
   and `LoadImage` does not read `.hdr`, so the captures must MOVE under
   `Assets/Resources`, which moves the directory `attribution-check.py` maps
   to Poly Haven; (b) there is no NIGHT capture, so night keeps the
   procedural cubemap and the handover needs a ramp.

   **Ship the measurement with it:** the environment cubemap's own luma
   spread, before and after — a flat gradient and a real sky differ by an
   order of magnitude there, and that is the number that says the wire took.


   **LINEAR MPB CLASS-FAULT UNDER TEST:** MPB colours skip
   gamma-to-linear, so display-authored tints weakened at the flip. BODY
   WASH fixed first; 13 other MPB sites wait on the verdict, which was
   itself blocked by its own instrument until 23 Aug (the palest-part table
   named BlobShadow — a multiply quad sampling the pavement — four runs
   running; attribution skips Hidden/ shaders now). Real remainder: feet and
   shoes at 224-234, both tiers. **And a SECOND MPB fault is now open
   beside it:** `_Color` set through a property block on a shader that has
   no `_Color` is a silent no-op — see the kit-paint items below.

   **V6 FIRST SLICE LANDED** (dusk warmth, sun glow, sodium deck). Open
   from V6: the dome's cloud structure per time of day.
1. **THE SHADOW RATIO: TWO LEVERS MEASURED AND REJECTED, THE THIRD ONE
   DISPATCHED.** Target is a cast shadow near HALF the lit brightness; today
   it is 0.25.
   - **Fill: capped by physics.** `ambientSeries` says x2.0 lands 0.50, and a
     CoreTest refuses it — the day fill must stay dimmer than the dome it
     derives from, because a wall seeing PART of the hemisphere cannot get
     what the whole sky emits. Caps near x1.33, about 0.32.
   - **Key: ruinous.** `sunSeries` moves the shade only **-21%** while
     collapsing the lit side **-66%**. It buys ratio by destroying the
     picture. My written prediction that the answer was "mostly key" is
     REFUTED.
   - **Shadow strength: dispatched, and the ladder had already named it.**
     `shadowOff:0.310` against `all:0.102` — shadows do most of the
     darkening. `sun.shadowStrength` ships at **0.93**, removing 93% of the
     key in shadow. `shadowSeries` walks 0.93/0.85/0.75/0.65/0.55. **It is
     better than the other two on its own terms: it raises the shaded side
     and leaves the LIT side untouched, so the ratio's denominator cannot
     drift with the lever** — the one thing neither other series could
     promise.
   **AND THE FIXTURE ITSELF MOVES, which undercut a number I quoted to three
   digits.** The two series' x1 rungs agree to 1.0% on the LIT third and
   differ by **26%** on the SHADED one, because the probe runs at the
   step-back's final position — its own call site says so — and the step-back
   moves by however much occlusion it found. So "x2.0 lands 0.495" was three
   digits off a moving foundation. `on:<material>` is stamped INTO each
   series now so two of them cannot be compared without seeing whether they
   looked at the same wall. *(The first version read `_noonFacadeMat`,
   assigned seventy lines further down — it would have stamped "not_probed"
   on everything for ever, and a stamp that never varies looks like
   agreement. It gets its own ray.)*

1. **THE STILLS NO LONGER PHOTOGRAPH WALLS.** *(rule 12; step-back and
   depth series landed — account in `roadmap-history.md`.)* `farFrac`
   (7-20m) is added for the case that passes both existing bands. **And the
   black-wall frame ACQUITTED this metric:** that wall sat at `d:6.8`,
   inside the mid band and under its bound, and it was DARK rather than
   badly framed — do not tighten the bound to chase it.

1. **RAIN: THE DIRECTION FIX UNCOVERED A SIZE FAULT TWO ORDERS OUT.** *(on
   screen, `review_street`)* A Box shape emits along the shape's FORWARD and
   nothing rotated the emitter, so rain was thrown SIDEWAYS at 26m/s;
   `rainLowest` went from a STRUCTURAL floor of **+5.7m** to **-28.5m**.
   **And then the frame showed white BARS falling.** Measured: streaks a
   **median 10 pixels wide**, bright-desaturated pixels **18.2% of the whole
   frame**, against 6.5% in the top third alone before. `startSize` was 0.06
   — a six-centimetre raindrop, about thirty times life size. It never
   changed; what changed is that drops now pass the LENS instead of dying
   5.7m overhead and 28m out, where 6cm subtends nothing. **The fix did not
   cause this, it uncovered it** — two faults, one hiding the other.
   0.06 -> **0.010**, the factor taken from the measurement (ten pixels
   median wants one or two). **Judge it the way it was caught:** median run
   width of bright desaturated pixels on the committed still.
   **Coverage still open:** mid-band reached, frame edges not (top-right
   0.00%) — the 38m box, the 12m forward offset, the 1.1s life.

1. **THE BODY BUDGET IS CLOSED AT 87.8%** — account in `roadmap-history.md`.
   The 34m draw radius was the binding constraint (now 70m) and `RealBodyCap`
   got its PC measurement: the drawn crowd costs ~1.1ms, so 12 -> 28. Hair
   CLOSED. Still live: the centre-third foot reading (FootMesh 234,
   Ch38_Shoes 224); the white pills remain unidentified with NO COMMITTED
   STILL holding one, so the next step is a measurement that fires WHILE one
   is on screen.

1. **THE INQUIRY RUNS NOW; TWO THINGS GATED ON IT STILL DO NOT.** *(moat:
   information. Not started — stage 1 has startable work; recorded so the
   stage does not open by re-deriving it.)* CLAUDE.md says the detective
   "has never once opened an investigation into the player in the entire
   recorded history of this project", and that is **stale**: read 24 Aug,
   `inquiry=Manhunt` — it escalates to the loudest state the game has.
   Corrected in place, because the next session would otherwise be sent at
   work that is already running.
   **What is still zero is narrower and more interesting:**
   `summonsTaken=0` and `redirectRelief=0.00` while the inquiry reaches
   Manhunt. So the documented phone-line cause for `summonsTaken` (a
   `Public` flag saved, restored and read by nothing) stands, and the
   inquiry cause does not — the two had been read as one thing.
   *(`findingKinds=none` is NOT part of this. It belongs to `SceneAudit`,
   where `clean=True findings=0` is a fault counter doing its job — checked
   after guessing otherwise.)*

1. **STAGE 2 (SPEECH): THE RUNTIME WAS NEVER THE PROBLEM — IT IS THE MODEL.**
   *(not started; stage 1 has startable work. The rule-12 half is DONE.)*
   The channel answered on its first run: **`speechRuntime=[Microsoft.AI.
   DirectML 1.15.2: DirectML.dll (17.7 MB); speech runtime: 3 file(s),
   LEDGER_ONNX defined in ledger/Assets/csc.rsp; RUNTIME_OK]`**. The fetch
   works, the DLLs land, the define is set. So `speechLive=0` with
   `speechNoModel=29` across 301 builds is **the voice MODEL not being in
   the build**, not a broken runtime — which is exactly the distinction that
   line was added to make, and it made it immediately.
   **So the stage opens with the model, not the runtime.** Find what
   `OnnxSpeech` loads and whether anything stages it into the Windows build
   the way `voices-into-build` stages the banked clips. **Do not spend a
   round trip re-testing the fetch** — it is green and named.

1. **BUS AND BICYCLE LANDED** (seven kinds, zero fallbacks since P). Open:
   the RIDERLESS bike — if it reads wrong, rider or parked-only.

1. **PATROL DENSITY FOLLOWS THE INQUIRY — whether it READS is unfinished.**
   Links fire (`roadmap-history.md`). Open: `patrolOnBeatMean=0.00` over 3
   shots vs `0.18` over 17 — zero of three separates nothing; judge the
   `hunt_` pair. A PARKED beacon reads where six crossings do not.

1. **THE DISTANT SKYLINE — CLOSED FROM A DOC, AND THE CAUSE IS THE REPAINT
   ITEM.** The far tower is the most saturated thing in `district_downtown`
   (**0.469** vs brick 0.324, sky 0.222); fog cannot account for it, since
   `fogRGB` sits near 0.196 and a fogged object cannot be MORE saturated
   than the fog. `SkylineHaze` is a good desaturated grey-blue (sat 0.15)
   and `skylineRepainted=23` says it applied — **a multiply cannot
   desaturate**, so the kit's hue survived. Same fix: grey the atlas.
   **Fixed on the way:** `SkylineRepainted` incremented the moment the kit
   existed, BEFORE the paint was attempted. It counts acceptances now.

1. **THE PAVING BLOWOUT: DIAGNOSED BY ITS PROBE AND FIXED, BOTH DIRECTIONS
   FIRING.** `districtGround` came back `mat_asphalt ... glossScale:4.00` —
   pinned at its clamp, which is the code giving up rather than a scale. The
   wet target wants a near-mirror from a rough-asphalt map whose mean is a
   quarter of it, so x4 multiplies the map's **variance**, not its level: a
   p10-p90 luma spread of 0.654 against 0.141 for the road beside it. A wet
   surface's smoothness is the WATER, so past that point the uniform scalar
   is the right instrument and the map is not. **`glossDropped=5
   glossRestored=5` on the landing — it drops and restores in equal measure,
   so it is not the ratchet a one-way switch would have been.** Judge the
   strip on the frame next.

1. **EIGHTY-NINE FETCHED MODELS ON DISK, SIX REFERENCED — 25 OF THE UNUSED
   ARE INDUSTRIAL BUILDINGS FOR A PORT TOWN.** *(rule 6 aimed at art; the
   standing order is the best AVAILABLE result.)* Counted: industrial 25,
   roads 47, suburban 13, commercial 10 = **95 on disk, six referenced** —
   two awnings, `city_kit_roads_light_curved` for every lamp post in town,
   and three `low-detail-building-*` for the skyline. Unused is exactly the
   density the bar is about: construction barriers, cones and lights; four
   more lamp variants beside the single curved one the town wears; 47 road
   pieces; 25 industrial buildings for a town whose identity is its docks.
   Nothing to fetch, nothing to buy. **Next step is a READ, not a build:**
   put a handful through `TryInstantiateProp` and read `kitAlbedo` first,
   because the twelve `base_mesh_*` families at 1.00 are standing proof that
   a fetched model is not automatically a usable one.
   *(I first reported these as ENTIRELY unused, which was wrong: the code
   addresses props by underscored key, so a hyphenated grep found nothing
   and I concluded from its absence. One spelling searched is not a search.)*

1. **TWELVE PROP FAMILIES AT ALBEDO 1.00 ARE UNTEXTURED — `kitAlbedoNoTex=30`
   SAYS SO.** `kitAlbedo` had them at exactly 1.00 against
   `townWallAlbedo=0.15`, and 1.00 was also the instrument's silence:
   `MeanTexLuma` returns 1.0 for a null texture and `PropAlbedoUnread`
   cannot see it, because a missing texture is an early return rather than
   an exception. The split answered it — **30 materials carry no albedo map
   at all**, so those bins, benches, crates and barrels are wearing their
   material TINT and nothing else. **The fix is the tint, not a texture
   hunt**, and it is the same shape as the skyline: a kit prop arrives in
   its author's colour and this town has to repaint it.

1. **THE REPAINTS ALL APPLY AND CANNOT DO THE JOB — THE GREY SWAP IS IN AND
   RAN.** My glTFast theory was REFUTED by its own probe (`kitPaint=1997/0`,
   refused by `[none]`), and the atlases themselves named the real cause: a
   multiply by `SkylineHaze` moves top-decile saturation **0.820 -> 0.788**
   (`car-kit`) and **0.733 -> 0.686** (`city-kit-commercial`) — four to six
   per cent, because a multiply preserves channel ratios. **`kitGrey=2/0/1974`
   on the landing: both atlases greyed, none failed, 1974 renderers moved
   onto greyed variants.** Luma-weighted so the modelling and slate stripe
   survive; a cached VARIANT so props we deliberately never repaint are
   untouched. **Judge on the frame:** re-measure the saloon's saturation
   against the 0.385 the rest of `review_street` sits under.

1. **THE DECLUTTER: NAMEPLATES AND BUBBLES, MEASURED, OPEN.** *(on screen)*
   `collidingNames=3` over 26 samples — five labels at the peak, 3 of their
   10 pairs overlapping. `PinAll` runs at shot time and three still overlap:
   read `namesPinnedSum` (106) against `shotFixups` (27) before tuning.
   **AND THE FRAME EDGE IS A COLLIDER TOO, which this vocabulary lacked** —
   `review_day2_wet` renders "Ellis" cut in half by the bottom-right corner,
   found by opening the still. `namesClipped=n/tested` and `namesClipWorst`
   (overhang as a fraction of the label's OWN width) land next build.
   **Measured, NOT fixed, deliberately:** sliding a label inward detaches a
   nameplate from the person it names — a worse lie than a clipped one — and
   hiding it is the other repair. Which is right depends on how often and by
   how much, and neither number existed. Rule 2.

1. **FIVE OF SEVEN DISTRICTS HAD NO SHOPS AT ALL.** `the_Hook:shop73
   Copper_Row:shop4` and **zero everywhere else** — the Exchange is the
   financial district and had no commercial frontage; the Parade is the
   entertainment strip and was 37 houses and 24 flats. Shops were gated on
   `nearCore` alone and the dense cores sit in the Hook, so that flag had
   been answering "is this the Hook". Found by reading the new counter's
   OUTPUT, not the code. Two shares per district now (at a core and away
   from one); the Hook keeps 0.55 since frame-drift is calibrated on it.
   **Read `premisesByDistrict` next landing** — the mix is the judgment.

1. **THE DRESSING GATE WENT GREEN ON BUILD T** — the far city carries 382
   pieces where it carried 37. **The old frame item under it is RETIRED: it
   was three regime changes stale**, arguing from a software rasteriser's
   666ms. On the real GPU the frame is `game=5.6ms` of ~27.5ms with `perfOk`
   green, and the render is four fifths of it. Anything here starts from the
   `frameCost` ladder in `## Now`, not from those numbers.

1. ~~**The session-hook guarantee** (M22)~~ — **BUILT AND HOLDING.** What is
   open is the READING, not the tiers — see `## Now`.
2. ~~**Romance** (M18)~~ — **PROMOTED TO M18.5, 18 Aug by Jafar.**
3. ~~**Smuggling** (M21)~~ — **BUILT 21 Aug night** on the `Racket`
   substrate: cargo rhythm, Tibor signs, manifests feed the audit's heat,
   sim stages it, six CoreTests. Remainders: a player verb to recruit the
   signer; gambling waits behind it. Read `cargoes`/`manifests` next build.
4. **The other day-job tracks** (M18) — `Core/DayJob` is the courier round,
   singular; the doc offers bar/courier/office on the first morning.
5. **Interiors beyond the pub** (M20) — every other door is a threshold.

**Reactions are LIVE and measured** (flinch/glance/wave/point/head_no
all firing; most refusals are glance cooldowns doing their job).
**greet reads 0of0 and that is the SIM'S ECONOMY, not a wire fault**:
it needs a loyal (≥0.35) need-route crew member passing the player and
the sim skims, so the condition never exists. Deliberately NOT
planted — a staged loyal runner would pollute the crew-decay gates.
The wire is proven by the five kinds sharing its path.

### The quality ladder (standing order 16 Aug: best available, not first working)

Before closing any visible item, ask: best available result, or first working
one? Take the next rung or name it here. A blank next rung is a research task.

| aspect | rung now | known next rung, free |
|---|---|---|
| textures | 2K colour+normal; roughness on walls AND ground (24 Aug, normalised so the wet calibration held: reflMax 0.89 unchanged); vertical run-off streaks in brick/plaster/concrete | AO maps; a second albedo variant per surface |
| buildings | procedural terraces, photo surfaces, pots+aerials, shopfront depth (V4), painted joinery, window SILLS (24 Aug, 2133) | window REVEALS (a recess needs an opening in the mass, not a proud box); door furniture |
| doors | 376 leaves on hinges, damped-spring swing, latch + creak, DOORWAY approach not a radius; proven live (`doorSwing=376/6/6/0/1`) | a shove — `HitStop` is unreachable at the shipped damping (8.4% overshoot vs a 15% stop, two CoreTests), so the thump needs a door pushed rather than eased; then walkers using doors |
| kit props | repaint applies everywhere (`kitPaint=1997/0`) | grey each kit colormap once at load, preserving luma — a multiply cannot desaturate (0.820 -> 0.788 measured) |
| vehicles | Kenney kit + town paints | curated higher-fidelity CC0 set (Quaternius/Sketchfab), same pipeline |
| props | Kenney + Base Mesh furniture, yellows (build D) | dock clutter density read; higher-tier swaps |
| characters | Mixamo bodies, gait archetypes | Jafar's clip session; combat set is disk-only |
| lighting | REAL noon shadows + deepened AO + grade; linear closed; V6 first slice | the AMBIENT FILL — a sun-perpendicular wall reads 0.039 against a lit 0.431, and `ambientSeries` is dispatched to set it; then HDRI as the environment source |
| animation feel | walk/idles + 18 activities + 6 reactions wired | reaction states for the rigs that refuse them — X's reactWhy reads noState:339 against cooldown:97, so most asks die on a controller with no state for the slot; then smoke/thinking re-harvest; walk transitions (disk-only) |
| audio | foley, barks, procedural score | voices into build (Thu); positional street sounds |

- **M21, the two ledgers.** Empire growth, law as a tool, what expansion costs
  you. Entirely unbuilt, entirely Core, so entirely doable here without a round
  trip. This is the largest piece of unwritten game left.
- **M22, the shape of a playthrough.** Onboarding, pacing, replayability and
  succession — also unbuilt and also Core-shaped.
- **Read a system and write down what it actually does.** Every system
  here has at least one comment that is now false, and each one found is
  a bug that would otherwise have been believed. **Read the code that
  produces a number too** — three faults in `CollidingNames` came from
  reading it, not from its readings.
- **Turn a still into a number.** Five faults found by opening a frame and none
  by a gate. Anything a frame shows that no metric names is a metric worth
  adding.
- **DROPS DELIVER EVERY RUN.** Open: the d12 shape — a night the job
  never owned (`held:waypoint`, ran=0) while the skip plant says it
  stopped at day 11. Trace-first: read TraceJob's window source against
  the active-job timing before any change.
