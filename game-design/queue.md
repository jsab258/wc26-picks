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
all:22.4 noShadow:17.3 noPixLights:18.0 noBodies:23.3. **Shadows
5.1ms and per-pixel lights 4.4ms hold the frame; the crowd is not in
the bill** (hiding every body came back SLOWER). Dead: draw calls,
vertex budget, shadow reach. Only the rungs' DIFFERENCES are a frame
time — the absolutes carry the probe's own RT+ReadPixels cost.

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
   VISIBLE DOME UNTOUCHED.** The item asked for a deliberate pick between
   that and blending two captures across the hour, and the numbers make it:
   - **Glass is smoothness 0.90 and Window 0.85** (`SurfaceSpec`), on every
     facade in town — already highly reflective. What they reflect is a
     **64px cubemap baked off a three-colour gradient**, no structure at
     all. The near-black windows in every landed frame are dark BECAUSE
     there is nothing to reflect, not because they were authored dark.
   - The blend shape trades a CONTINUOUS day (`LightModel` drives the dome
     per frame through dusk warmth, night sodium and a per-day cloud deck
     the ambient reads from) for photographic detail, and pops between four
     fixed states. Reflection-only is additive and cannot regress it.
   **Obstacles, both real:** (a) `Resources.Load` cannot reach `Assets/Sky`
   and StreamingAssets cannot help (`LoadImage` reads PNG/JPG, not `.hdr`),
   so they must MOVE under `Assets/Resources`, which moves the directory
   `attribution-check.py` maps to Poly Haven; (b) there is no NIGHT capture,
   so night keeps the procedural cubemap and the handover needs a ramp.
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
1. **A THIRD OF THE NOON FRAME IS A BLACK WALL, AND IT IS NOT THE CAMERA.**
   *(on screen, `review_day1_noon`)* Column thirds read **0.047 / 0.396 /
   0.431**, a ninefold split inside one midday frame. Ruled out by number:
   not framing (`nearFrac=0.00 midFrac=0.27`, both inside bound, so the wall
   is beyond 7m); not the texture (`concrete_b.jpg` means **0.366**, and the
   census says the third is **85% `mat_concrete_b`**); not
   post/AO/vignette/sun/glass (every landed rung sits 0.035-0.047); and the
   arithmetic says albedo x ambient x exposure lands near 0.43 — exactly
   what the RIGHT third reads.
   **An elevenfold shortfall cannot hide in a rung that moves 0.004, so it
   is not in that ladder — and a ladder is an allow-list.** Four rungs
   added: `ambOff`, `amb4x`, `shadowOff`, `fogOff`. `amb4x` is the only one
   that turns something UP, and it is the one that matters: if the third
   scales, the wall takes ambient and the fill is not reaching a vertical
   face; if not, the surface is refusing light and the answer is in the
   material. No off-rung separates those. **`noonFacadeMat` lands in the
   same run** — material, shader, `_Color`, texture, distance, normals, and
   the **MaterialPropertyBlock**, which `sharedMaterial` cannot see.
   **Also `farFrac`** (7-20m), the band both existing bands skip: a wall ten
   metres out fills a frame as thoroughly as one two metres out. Series
   first, no bound (rule 2).

1. **THE STILLS NO LONGER PHOTOGRAPH WALLS, AND THE METRIC IS STILL TOO
   NARROW.** *(rule 12; step-back and depth series landed — account in
   `roadmap-history.md`.)* The night half is ADDRESSED (the shutter aims
   down the longest clear sightline, eight compass rays, rides AE) — judge
   on its landing. **The day twin landed on V:** day2_noon stepped back from
   0.44 to 0.24 near-fraction, passing the 0.25 bound, and the frame is
   still half wooden hoarding — a MID-DISTANCE occluder filling the frame
   while sitting past the arm's-length test. `midFrac` landed for that;
   `farFrac` (7-20m) is now added for the case that passes BOTH, which is
   the black-wall item above. Traffic contradiction RESOLVED; tour pair
   landed, prediction held.

1. **RAIN: wet frame PLANTED** — the daily roll is seeded off the day
   number, so review days 1-2 are dry on every run there will ever be; the
   sim forces a downpour at day 2 hour 21 and shoots `day2_wet` at 22.

1. **RAIN AT EYE LEVEL — THE ITEM WAS CLOSED AND THE RAIN WAS NEVER THERE.**
   *(on screen, `review_day2_wet` and `review_day1_night`)* Closed on
   "landed wet frames read as streaks in lamp cones". They do. The lamp
   cones are above the lamps. Measured with hue separating streaks from
   sodium glow: bright desaturated pixels read **6.5% and 10.7% in the top
   third against 0.00-0.26% everywhere below**, in two frames from two
   cameras.
   **CAUSE, read in the source, not guessed:** a Box shape emits along the
   shape's FORWARD and nothing ever rotated the emitter, so world +Z it was
   — the rain was THROWN SIDEWAYS at 26m/s, not falling. From the shipped
   numbers (sheet 14m up, 1.1s life, 1.4x gravity) a drop falls 8.3m while
   travelling 28.6m sideways, so it **dies 5.7m over your head every time**.
   The single wedge is the same fault from the side: every drop flies the
   same WORLD direction, so which part of the frame gets rain depends on
   camera yaw.
   **Fixed with one rotation.** Speed 9 not 26, because pointing it down
   changes what that number MEANS. **`rainLowest` and `rainBelow/rainAlive`
   land next build** — the old emitter could not have read below +5.7m
   however hard it rained. Retune from that series, not from a frame.

1. **THE BODY BUDGET IS CLOSED AT 87.8% — account in `roadmap-history.md`.**
   The 34m draw radius was the binding constraint (now 70m) and
   `RealBodyCap` got its PC measurement: the render ladder priced the whole
   drawn crowd at ~1.1ms, so 12 -> 28. **Hair CLOSED.** Still live: the
   centre-third foot reading (FootMesh 234, Ch38_Shoes 224); the white pills
   remain unidentified with NO COMMITTED STILL holding one, so the next step
   is a measurement that fires WHILE one is on screen. `bodyWashUnreached`
   ~500 against `bodyTinted` 2048 — a multiply only subtracts. A limit, not
   a bug.

1. **BUS AND BICYCLE LANDED** (seven kinds, zero fallbacks since P). Open:
   the RIDERLESS bike — if it reads wrong, rider or parked-only.

1. **PATROL DENSITY FOLLOWS THE INQUIRY — whether it READS is unfinished.**
   Links fire (`roadmap-history.md`). Open: `patrolOnBeatMean=0.00` over 3
   shots vs `0.18` over 17 — zero of three separates nothing; judge the
   `hunt_` pair. A PARKED beacon reads where six crossings do not.

1. **THE DISTANT SKYLINE — I MARKED THIS FIXED FROM THE DOC AND THE FRAME
   DISAGREED.** *(on screen, `district_downtown`)* The repaint was written
   and the item closed on that basis. Measured 24 Aug: **the far tower is
   the most saturated thing in the frame — 0.469, against brick 0.324 and
   sky 0.222.** Fog cannot account for it; `fogRGB` itself sits near 0.196
   saturation, and a fogged object cannot be MORE saturated than the fog.
   Rule 3: a doc saying something is done is an analysis, not a report on
   the code. **Cause, now measurable:** the repaint set `_Color` through a
   property block without asking whether the shader has one — the mint
   saloon's fault — and `SkylineRepainted` was incremented the moment the
   kit existed, BEFORE the paint was attempted, so it reported success for
   something it never checked. Both fixed; it counts what the shader
   accepted and shares `kitPaint=took/refused`. **Judgment next landing:**
   refusals non-zero -> replace the material; refusals zero -> the haze
   colour itself is wrong and gets re-derived from the `else` branch.

1. **A PAVING STRIP IS BLOWN OUT, AND THE MEASUREMENT IS ALL I HAVE.** *(on
   screen, `district_downtown`, centre of frame)* p10-p90 luma spread
   **0.654** against brick 0.387 and the road beside it 0.141 — two-thirds
   of the display range on one surface — with a median of **0.434 against
   0.059 for that adjacent road**, seven times brighter under identical
   light. The texture's own range is ~0.28, so something amplifies it ~2.3x.
   **NOT DIAGNOSED, deliberately:** three plausible causes (gloss-map scale,
   the wet reflection layer, a roughness map read as albedo) and no evidence
   between them. Next step is a ray dump at that surface in the district
   shots, the twin of `noonFacadeMat`.
   **What WAS proven on the way:** `Weather.ApplyWetness` wrote `_Glossiness`
   onto shared asphalt and concrete every frame, and the Standard shader has
   IGNORED it since gloss maps were bound (`_METALLICGLOSSMAP` makes
   smoothness the map alpha times `_GlossMapScale`). Dead since that
   landing, silently. `AssetLibrary.SetWetness` is the one implementation,
   covers all four wet surfaces and knows about the map; the dead twin is
   deleted after checking `WetSurfaces` covers both (rule 5).

1. **FOUR KIT-PROP SITES ARE UNPAINTED — THE MEASUREMENT IS BUILT, READ IT
   ON THE NEXT LANDING.** Benches, bins, street lights and the crate stack
   take no repaint, deliberately: a green bench is plausible and
   mass-repainting on resemblance is the rule-4 mistake. Instrument:
   `kitAlbedo=[family:val/...]`, every kit family's mean material albedo
   measured once per key at the `TryInstantiateProp` choke point, brightest
   first so the ten-family cap cannot hide a positive, beside
   `townWallAlbedo` (the four wall surfaces through the SAME maths).
   **Judgment when it lands:** any unrepainted family clearly above
   `townWallAlbedo` gets the skyline treatment; at or below closes this.

   **AND A CAR THAT IS REPAINTED IS STILL MINT** — a different, worse fault.
   `review_street.jpg`: one saloon at **0.713** median saturation where
   nothing else in the frame passes 0.385, lilac wheels. The repaint is not
   missing; `TrafficHost` has six town paints and most of the fleet wears
   them. **All THREE paint sites** (moving cars, parked cars, skyline) set
   `_Color` through a property block without asking whether the shader HAS
   one, and glTFast's do not — the call evaporates in silence and looks
   identical to a paint that landed. One helper now,
   `AssetLibrary.PaintKit`, reporting `kitPaint=took/refused` with the first
   refusing shader NAMED. Refusals non-zero -> replace the material.

1. **THE DECLUTTER: NAMEPLATES AND BUBBLES, BOTH MEASURED, BOTH OPEN.**
   *(on screen)* `collidingNames=3` over 26 samples — five labels at the
   peak, 3 of their 10 pairs overlapping, a heap as the frame shows. `PinAll`
   runs at shot time and three pairs still overlap: read `namesPinnedSum`
   (106) against `shotFixups` (27) before tuning, and note
   `bubblesLiftedSum=1` — the de-overlap moved a bubble once in a whole run
   while the pin site clearly works.
   **The bubble median mixed two samplers and is split now** —
   `SampleBubbles` per tick and `CollidingNames` per shot both wrote
   `_bubbleOverlap` (71 readings vs 26). **I read a 0.33 -> 0.00 move as the
   fix working** when what moved was the street: the district fix spread the
   population out, so more instants have two bubbles up and fewer collide. A
   real improvement, and not the one I claimed.
   `bubbleOverlapShotMedian` is the first one checkable against a still.
   **Also on screen:** `review_day2_wet` renders "Ellis" half off the
   bottom-right edge. A nameplate CLIPPED by the frame is a different fault
   from two overlapping, and nothing measures it.

1. **THE NAMEPLATE HEAP IS MEASURED AND THE INSTRUMENTS AGREE WITH THE
   PICTURE.** *(on screen)* `collidingNames=3` over 26 samples: five labels
   at the peak, 3 of their 10 pairs overlapping — a heap, as the frame
   shows, and the "counter says 0, picture says heap" argument is over
   (account in `roadmap-history.md`). **Open is the DECLUTTER**: `PinAll`
   runs at shot time and three pairs still overlap. Read `namesPinnedSum`
   against `shotFixups` next build before anyone tunes it.

1. ~~**THE VERDICT HAS AMBIGUOUS KEYS**~~ — **THE EMITTER IS CLEAN AND
   GATED, 24 Aug.** The old plan was "gate once a verdict lands clean"; it
   went 30 same-line -> 34 instead, so that condition was never arriving and
   the decision had decayed. **The gate now reads the SOURCE** —
   `tools/verdict-emit-dupkeys.py`, in `verify.py`, hard-failing — answering
   in a second what the landed check answers a round trip later. It exists
   because wiring `DoorSwing` added a second `doors=` to the done line 300
   lines from `WorldBuilder.Doors`; nothing would have failed, and the
   damage is to the OLD key. Confirmed against the actual colliding commit.
   **Two real hits fixed, no baseline list:** `dia/hi=` beside `hi=` (a
   slash is not a word character) -> `diaPerHi`/`diaPerLen`; the §4.7 places
   line's three sub-records each carry their place now, staying on ONE line
   deliberately. **The tool's first version reported a key the file uses
   once** — the other was a comment QUOTING it; comments are blanked now and
   that is a selftest. Open: the landed backlog is still 34 DATA collisions
   (`key=` inside bracketed values), a different fix.

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
| doors | 376 leaves on real hinges, damped-spring swing, latch + creak, opens on a DOORWAY approach not a radius (24 Aug) | a shove — `HitStop` is unreachable at the shipped damping (8.4% overshoot vs a 15% stop, pinned by two CoreTests), so the thump needs a door pushed rather than eased; then walkers using doors |
| vehicles | Kenney kit + town paints | curated higher-fidelity CC0 set (Quaternius/Sketchfab), same pipeline |
| props | Kenney + Base Mesh furniture, yellows (build D) | dock clutter density read; higher-tier swaps |
| characters | Mixamo bodies, gait archetypes | Jafar's clip session; combat set is disk-only |
| lighting | REAL noon shadows + deepened AO + grade (landed) | linear colour space (V1.5, next build); sky dome (V6) |
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
