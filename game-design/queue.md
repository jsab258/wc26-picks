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

**SILLS ARE IN AND FREE** (2133 near buildings, no collider; +2173
renderers with render+rest UNCHANGED — this scene is not
submission-bound). Weathering went into the TEXTURE after doubling
decals moved the count and not the picture. **Ground roughness maps
bound (24 Aug), normalised by each map's own mean so the wet
calibration held.**

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
1. **THE BLACK NOON WALL IS AMBIENT, MEASURED — AND THE SERIES THAT SETS
   THE FIX IS DISPATCHED.** *(on screen, `review_day1_noon`)* The ladder
   answered it: `ambOff:0.012 / all:0.039 / **amb4x:0.514**`. Removing the
   fill takes the third to 0.012, so direct light contributes almost nothing
   there; `noonFacadeMat` says why outright — **`nSun:0.00`**, the wall is
   exactly edge-on to the sun and lit by fill alone. It is not the material
   (`col:0.54,0.55,0.60`, `mpb:unset`, `shader:Standard`) and not the
   framing (`d:6.8`). **The `amb4x` rung — the only one that turned
   something UP — is what answered it, and no off-rung could have.**
   **4x OVERSHOOTS** (0.514 against a LIT third of 0.431: a shaded wall
   outshining a sunlit one), so the multiplier is under 4 and picking it off
   two points 13x apart is the invented number rule 2 forbids.
   `ambientSeries` prints **shade|lit pairs at x1/1.5/2/2.5/3/4** —
   `LightModel`'s own target is a RATIO (the GTA reference noons put a cast
   shadow near HALF the lit brightness) and raising the fill raises the lit
   side too, so a series of shade values alone would be read against a
   quietly moving denominator. `RightThirdMedian` is the twin that was
   never printed. **Judgment when it lands:** take the rung whose
   shade/lit lands nearest 0.5, and set `AmbientDayShare` from it.

1. **THE STILLS NO LONGER PHOTOGRAPH WALLS.** *(rule 12; step-back and
   depth series landed — account in `roadmap-history.md`.)* The night
   shutter aims down the longest clear sightline; the day twin stepped
   day2_noon from 0.44 to 0.24 near-fraction. `farFrac` (7-20m) is added for
   the case that passes both existing bands. **And the black-wall frame
   ACQUITS this metric:** that wall sits at `d:6.8`, inside the mid band and
   under its bound, and it was DARK rather than badly framed — so do not
   tighten the bound to chase it.

1. **RAIN: wet frame PLANTED** — the daily roll is seeded off the day
   number, so review days 1-2 are dry on every run there will ever be; the
   sim forces a downpour at day 2 hour 21 and shoots `day2_wet` at 22.

1. **RAIN: THE DIRECTION IS FIXED AND PROVEN; THE COVERAGE IS NOT.**
   *(on screen, `review_day2_wet` — it falls vertically down the street now
   instead of scribbling across one corner.)*
   **Fixed:** a Box shape emits along the shape's FORWARD and nothing
   rotated the emitter, so the rain was thrown SIDEWAYS at 26m/s at world
   +Z. `rainLowest` went from a STRUCTURAL floor of **+5.7m** — it could not
   read lower however hard it rained — to **-28.5m**, with `rainBelow=126/370`
   under eye height. The item had been closed on "wet frames read as streaks
   in lamp cones". They do. The lamp cones are above the lamps.
   **NOT fixed, and the pixels say so more soberly than the picture does.**
   Same hue-separated measure as before: mid-left 0.26% -> **1.10%** and
   mid-centre 1.38%, but **top-right is still 0.00% and bottom-left 0.03%**.
   So the rain reaches the middle band and not the frame edges — a COVERAGE
   question (the 38m box, the 12m forward offset, the 1.1s life), not a
   direction one. Do not read the frame as "rain everywhere now".
   **Also open:** speed is 9 (was a 26m/s throw); retune from `rainLowest`.

1. **THE BODY BUDGET IS CLOSED AT 87.8% — account in `roadmap-history.md`.**
   The 34m draw radius was the binding constraint (now 70m) and
   `RealBodyCap` got its PC measurement: the render ladder priced the whole
   drawn crowd at ~1.1ms, so 12 -> 28. **Hair CLOSED.** Still live: the
   centre-third foot reading (FootMesh 234, Ch38_Shoes 224); the white pills
   remain unidentified with NO COMMITTED STILL holding one, so the next step
   is a measurement that fires WHILE one is on screen. `bodyWashUnreached`
   ~500 against `bodyTinted` 2048 — a multiply only subtracts. A limit, not
   a bug.

1. **STAGE 2 (SPEECH), MEASURED IN ADVANCE: THE LIVE ROUTE HAS NEVER ONCE
   RUN, IN 301 BUILDS.** *(not started — stage 1 still has startable work.)*
   `gates.py --constant` reports twelve speech keys never anything but zero.
   The router is honest and says why: `speechAsked=205 speechBanked=176
   speechLive=0 speechTooSlow=0 speechNoModel=29`, and `Asked` is DERIVED so
   every ask is accounted for — 29 refused because no backend loaded.
   `speechStepsPerSec=unmeasured`, that file's own rule-3b fix separating "a
   slow card" from "the model never ran".
   **THE REASON IS IN NO CHANNEL I CAN READ, AND THAT IS THE FIRST FIX**
   (rule 12): the workflow's `Fetch the speech runtime` step is
   `continue-on-error` and its failure is one echo into a job log this
   environment cannot tail. "The fetch 404s", "the runtime loaded but no
   voice model shipped" and "off by design" are indistinguishable from here
   and have different next actions. **First item of the stage: carry the
   fetch's outcome into `verdict.txt`** — `sim-shots-commit.sh` composes it
   and can take a `speechRuntime=[...]` line.
   **Why it matters:** as things stand, Jafar's playtest would be the FIRST
   time that path has ever executed in a built game.

1. **BUS AND BICYCLE LANDED** (seven kinds, zero fallbacks since P). Open:
   the RIDERLESS bike — if it reads wrong, rider or parked-only.

1. **PATROL DENSITY FOLLOWS THE INQUIRY — whether it READS is unfinished.**
   Links fire (`roadmap-history.md`). Open: `patrolOnBeatMean=0.00` over 3
   shots vs `0.18` over 17 — zero of three separates nothing; judge the
   `hunt_` pair. A PARKED beacon reads where six crossings do not.

1. **THE DISTANT SKYLINE — CLOSED FROM A DOC, AND THE CAUSE IS THE ITEM
   ABOVE.** The far tower is the most saturated thing in `district_downtown`
   (**0.469** vs brick 0.324, sky 0.222) and fog cannot account for it —
   `fogRGB` sits near 0.196, and a fogged object cannot be MORE saturated
   than the fog. `SkylineHaze` is a good desaturated grey-blue (sat 0.15)
   and `skylineRepainted=23` says it applied: **a multiply cannot
   desaturate**, so the kit's own hue survived. Same fix as the saloon —
   grey the atlas. Rule 3 on how it was closed in the first place.
   **Fixed on the way:** `SkylineRepainted` incremented the moment the kit
   existed, BEFORE the paint was attempted. It counts acceptances now.

1. **A PAVING STRIP IS BLOWN OUT; THE PROBE IS DISPATCHED.** *(on screen,
   `district_downtown`, centre)* p10-p90 luma spread **0.654** against brick
   0.387 and the road beside it 0.141, with a median **0.434 against 0.059**
   for that adjacent road — seven times brighter under identical light. The
   texture's own range is ~0.28, so something amplifies it ~2.3x.
   `districtGround` fires one ray at the low centre of the Exchange frame
   and names material, `_Color`, MPB, texture, normals AND the gloss state —
   `_METALLICGLOSSMAP`, `_GlossMapScale`, `_Glossiness`, `_Metallic`.
   `glossScale` drives smoothness when the keyword is on, and a value at its
   x4 clamp is a blowout by construction. ONE helper (`SurfaceUnder`),
   shared with `noonFacadeMat`.

1. ~~**THE POSITIVE CONTROL HAD BEEN NEUTERED**~~ — **FIXED.**
   `DefeatWetSpecular` forces wet-surface smoothness to zero and claims to
   work "by a route that cannot fail". Binding gloss maps put
   `_METALLICGLOSSMAP` on all four wet surfaces, at which point the shader
   ignores `_Glossiness` — so it reported no change, which reads as "wet
   specular contributes nothing", the exact wrong conclusion it exists to
   prevent. Routed through `SetSmoothness`. **Third victim of one binding**,
   found by grepping every `SetFloat("_Glossiness"` — ten seconds, and it
   should have been step two of that change.

1. **THE KIT REPAINTS ALL APPLY AND CANNOT DO THE JOB — A MULTIPLY CANNOT
   DESATURATE.** *(on screen: the mint saloon in `review_street`, the far
   tower in `district_downtown`)* My glTFast theory is REFUTED by its own
   probe: **`kitPaint=1997/0`, `kitPaintRefusedBy=[none]`** — every one of
   1997 renderers accepted the paint, and `skylineRepainted=23`. So the
   paint lands and the objects are still wrong, which is a different fault.
   **Measured on the kit atlases themselves:** a multiply by
   `SkylineHaze(0.34,0.36,0.40)` moves top-decile saturation **0.820 ->
   0.788** on `car-kit/colormap.png` and **0.733 -> 0.686** on
   `city-kit-commercial`. Four to six per cent. A multiply scales all three
   channels, so it preserves their ratios — it darkens and it cannot
   recolour. `PatrolWhite`'s comment says this outright ("the model's own
   slate stripe survives because a multiply preserves the ratio between
   them") and it is a virtue there and the whole problem here.
   **THE FIX IS THE TEXTURE, NOT THE COLOUR.** Grey each kit colormap ONCE
   at load, preserving luma so the modelling and the stripe survive, and
   assign it to the shared material; the per-instance MPB paint then does
   the colouring it was always meant to do. One texture per atlas, done
   once. **Do NOT chase this by picking darker paints** — the palette is
   already 0.12-0.48 and the saturation is the author's, not ours.

1. **THE DECLUTTER: NAMEPLATES AND BUBBLES, MEASURED, OPEN.** *(on screen)*
   `collidingNames=3` over 26 samples — five labels at the peak, 3 of their
   10 pairs overlapping. `PinAll` runs at shot time and three still overlap:
   read `namesPinnedSum` (106) against `shotFixups` (27) before tuning, and
   note `bubblesLiftedSum=1` — the de-overlap moved a bubble once in a run.
   **The bubble median mixed two samplers and is split now** (71 tick
   readings vs 26 shot ones). **I read a 0.33 -> 0.00 move as the fix
   working** when what moved was the street — the district fix spread the
   population out, so fewer bubbles collide. A real improvement, not the one
   I claimed. **Also on screen:** `review_day2_wet` renders "Ellis" half off
   the bottom-right edge. A nameplate CLIPPED by the frame is a different
   fault from two overlapping, and nothing measures it.

1. **THE NAMEPLATE HEAP IS MEASURED AND THE INSTRUMENTS AGREE WITH THE
   PICTURE.** *(on screen)* `collidingNames=3` over 26 samples: five labels
   at the peak, 3 of their 10 pairs overlapping — a heap, as the frame
   shows, and the "counter says 0, picture says heap" argument is over
   (account in `roadmap-history.md`). **Open is the DECLUTTER**: `PinAll`
   runs at shot time and three pairs still overlap. Read `namesPinnedSum`
   against `shotFixups` next build before anyone tunes it.

1. ~~**THE VERDICT HAS AMBIGUOUS KEYS**~~ — **THE EMITTER IS CLEAN AND
   GATED.** The old plan was "gate once a verdict lands clean"; it went 30
   same-line -> 34 -> 35 instead, so that condition was never arriving.
   `tools/verdict-emit-dupkeys.py` reads the SOURCE and hard-fails in
   `verify.py`, answering in a second what the landed check answers a round
   trip later. It exists because wiring `DoorSwing` added a second `doors=`
   to the done line 300 lines from `WorldBuilder.Doors` — the landed verdict
   then read 35, confirming the harm empirically. Two real hits fixed, no
   baseline list; the tool's first version reported a key the file uses once
   (the other was a comment QUOTING it), so comments are blanked and that is
   a selftest. Open: the landed backlog is DATA collisions (`key=` inside
   bracketed values), a different fix.

1. **AND THE SAME COUNTER IMMEDIATELY FOUND A BIGGER ONE: FIVE OF SEVEN
   DISTRICTS HAD NO SHOPS AT ALL.** `the_Hook:shop73 Copper_Row:shop4` and
   **zero everywhere else** — the Exchange is the financial district and had
   no commercial frontage; the Parade is the entertainment strip and was 37
   houses and 24 flats. Shops were gated on `nearCore` alone and the dense
   cores sit in the Hook, so that flag had been answering "is this the
   Hook". The warehouse fault a second time, in the branch immediately below
   it, and found by reading the new counter's OUTPUT rather than the code.
   Two shares per district now (at a core and away from one) because both
   are real; the Hook keeps 0.55 at a core since every frame-drift check is
   calibrated on it. Tested both ways. **Read `premisesByDistrict` next
   landing** — the mix is the thing to judge, not the presence.

1. **THE DRESSING GATE WENT GREEN ON BUILD T** — the far city carries
   382 pieces where it carried 37. **THE FRAME ITEM BELOW IT IS RETIRED
   (23 Aug): it was three regime changes stale.** It argued from
   `mean=666.4ms` (a software rasteriser) and `game=24.53ms` against a
   12ms budget, and named `npcs` as the dominant cost to attack. On the
   real GPU the frame is `game=5.6ms` of `meanFrame ~27.5ms` with
   `perfOk` green, and the render — not our code — is four fifths of it.
   The live account is the `frameCost` ladder in `## Now`: shadows
   5.1ms, per-pixel lights 4.4ms, crowd nothing. Anything that still
   wants doing here starts from that ladder, not from these numbers.

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
