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

1. **THE BENCHMARK EXISTS AND ITS FIRST TABLE REDIRECTS THE VISUAL QUEUE.**
   `tools/ref-bench.py`: one instrument on the five committed GTA frames and
   every still; 201 of 272 readings outside the reference band. Three
   steering findings, in fix order:
   - **FILM GRAIN IS 3-7x THE NOISIEST GTA FRAME** (`grainSigma` 5-7 on
     districts vs ref 0.23-2.05) and pollutes every edge reading. ONE
     post-chain setting, never measured before. Builder task: print the
     grain amplitude the chain actually applies, then set it from the ref
     band's series — not taste.
   - **THE NOON ROAD IS THE FLATTEST GROUND PLANE IN THE 22-IMAGE SET**
     (`groundPatch=0.052` vs ref 0.205-0.382). 17 decal sets are fetched
     and wired — reach question first: do ANY land on the CARRIAGEWAY?
     This is V2's number and frame 3's killer argument.
   - **Shadow contrast in-band on exactly one still** (day1_noon 0.304;
     districts 0.02-0.15 vs ref 0.157-0.388). Districts are the pinned
     series, so this is readable per landing.
   `groundPatch` is the surface-history proxy (grain-immune); `edgeGround`
   may never be quoted without `grainSigma` beside it — the naive metric
   scored an all-black frame denser than every GTA reference.

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
1. **THE `5ee9330` STILL'S TWO FAULTS: BOTH FIXED, AWAITING THE LANDING**
   (rain streak 0.575m -> 0.152m derived; `skyVsWall` probe in; full account
   in `roadmap-history.md`). **Read `rainLowest` (should rise toward -4 after
   the spawn-curtain fix) and `skyVsWall` next landing.**

1. **FRAME COMPARISONS ARE CONDITIONED ON THE CAMERA NOW** — 9 of 29 rows
   comparable, 20 moved; the confound is YAW as much as position (-0.80 vs
   -0.68 on `day2_noon`) and the pinned district tour is the photometric
   series this project already had. Account in `roadmap-history.md`.
   **Open: the 7/7 darkening.** All seven districts moved -0.0005..-0.0050
   and `day1_noon` -0.0065 in one batch, with the WRONG SIGN for the shadow
   lever (0.93 -> 0.85 lightens). Two landings and many commits, magnitude at
   the tour's own p90 — **read it again after a few more landings, then
   bisect.**

1. **EVERY PINNED SHOT DARKENED IN THE LATEST BATCH, WITH THE WRONG SIGN FOR
   THE SHADOW LEVER.** All seven districts moved -0.0005 to -0.0050 and
   `day1_noon` -0.0065, 7/7 in one direction. But `shadowStrength` went
   0.93 -> 0.85, which LIGHTENS shadows and should brighten a frame, so this
   is something ELSE in the batch. **Not a conclusion — two landings carrying
   many commits, and the magnitude sits right at the tour's own p90 of
   0.0050.** What it does show is the instrument working: a consistent 0.003
   across seven independent shots is a thing the street frames could never
   have shown. Open: read it again after the next few landings, and if it
   holds, bisect the batch.
1. **EIGHTEEN GATES CANNOT NAME THEIR OWN FAILURE — RATCHETED AT 18 by
   `tools/gate-detail.py` in `verify`** (account in `roadmap-history.md`).
   Fix each bare gate's operands as it goes red, not en masse.

1. ~~**SIX TOOLS COMPARED A GIT ABBREVIATION TO A RUN FILENAME BY
   EQUALITY**~~ — **FIXED at all six sites** (account in
   `roadmap-history.md`). `verify` warns that the abbreviation is 8 chars and
   run stems are 7, so compare by PREFIX and never by equality.
1. **THE SIM OVERRUNS ITS 24-MIN KILL — `hangTail` FIRED AND WAS USELESS,
   NOW FIXED.** `Wait-Process -Timeout 1440`; healthy runs take ~12 min and
   take 20 shots. **`5ee9330` reached ONE shot** (prior truncations reached
   4). The thirty lines it printed were 28 repeats of Unity's IK warning and
   2 of an R8_SRGB fallback — **engine chatter drowned every line the sim
   wrote**, so the instrument built for this answered nothing (rule 12).
   **`hangOwn` now tails the last 40 lines shaped `TypeName: `** — structural,
   not a list of engine strings — with `hangTailOwn` as the denominator and the
   raw tail kept. **20 was not enough:** one `ArgumentException` and its stack
   took 3 of them, .NET exceptions wearing our own line shape. A third tail
   keeps 12 `SimDirector: ` lines (`hangSim|`/`hangSimLines`). **Read both next
   truncation**, and `dayMark` now lands on healthy runs as the baseline rate.
   **NOT attributed to the sky change.** It is the obvious suspect — that
   commit made `reflectionIntensity` non-zero on dry frames for the first time
   — but two runs killed at 4 shots predate the code, so one landing cannot
   separate "made it worse" from "landed on a bad one". The every-frame
   `RenderSettings` write it also shipped is fixed on its own terms.
1. **`farFrac` CARRIES THE SIGNAL THE OTHER BANDS MISS — SERIES LANDED.**
   `day2_wet near=0.00 mid=0.18 **far=0.73**`, `day1_noon 0.00/0.27/**0.54**`,
   `day2_noon 0.00/0.33/**0.43**`. Near is 0.00 everywhere and mid sits inside
   bound, while the 7-20m band runs 0.43-0.73 — and `review_day2_wet` was ~80%
   black wall that nothing else could see. **No bound yet (rule 2): this is
   the series a bound comes from.** A street SHOULD have buildings at 7-20m,
   so the question is where "framed" becomes "photographing a wall".
1. **THE BODY BUDGET IS CLOSED AT 87.8%** — account in `roadmap-history.md`.
   Draw radius 34m -> 70m was the binding constraint, `RealBodyCap` 12 -> 28,
   hair CLOSED. **Still live:** the centre-third foot reading (FootMesh 234,
   Ch38_Shoes 224), and the white pills with no committed still.

1. **THE INQUIRY RUNS NOW; TWO THINGS GATED ON IT STILL DO NOT.** *(moat:
   information. Not started — stage 1 has startable work.)* CLAUDE.md said
   the detective "has never once opened an investigation in the entire
   recorded history of this project"; read 24 Aug, **`inquiry=Manhunt`**.
   Corrected in place, because that sentence would send the next session at
   work already running. **Still zero and now better specified:**
   `summonsTaken=0` and `redirectRelief=0.00` WHILE the inquiry reaches
   Manhunt — so the documented phone-line cause for `summonsTaken` stands
   and the inquiry cause does not; the two had been read as one.
   *(`findingKinds=none` is NOT part of this — it is `SceneAudit`'s, where
   `clean=True findings=0` is a fault counter working. Checked after
   guessing otherwise.)*

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

1. **THE DISTANT SKYLINE: GREYING HELPED, DID NOT CLOSE IT.** The tower was
   the most saturated thing in `district_downtown` at **0.469**; after the
   atlas grey it reads **0.394** — a 16% cut, and still above the brick
   beside it at 0.324. `SkylineHaze` is sat 0.15 and a greyed texture times
   it should land near that, so something is adding saturation back: fog
   (fogRGB sits near 0.196) or the patch containing sky rather than tower.
   **Next: measure a NAMED tower via `SurfaceUnder` rather than a screen
   patch** — the same fix the light series needed, for the same reason.
   *(`SkylineRepainted` also used to increment before the paint was
   attempted, reporting success for a step it had never checked. Fixed.)*

1. **PAVING BLOWOUT: LEVEL HALVED, VARIANCE BARELY MOVED.** `districtGround`
   found `glossScale:4.00` — pinned at the clamp, the code giving up. Fixed
   (uniform scalar once the wet target outruns the map; `glossDropped=5
   glossRestored=5`, both directions). **On the frame:** median 0.434 ->
   0.219, spread only 0.654 -> 0.571 vs brick 0.385. Gloss owned the LEVEL;
   texture contrast or the wet reflection owns the VARIANCE. **Next: read
   `districtGround` again, then reflection strength — do not re-tune gloss.**

1. **THE FETCHED MODELS NOW HAVE A REACH LEDGER: `tools/prop-reach.py`,
   in `verify`.** 213 models on disk, **63 named**, 150 with no name match —
   and the "89 on disk, six referenced" that stood here was SCOPED to the
   four city kits, which is right for those and wrong as a total. Per kit,
   because one number cannot carry both questions.
   **city-kit-industrial went 0 -> 24 of 25** (twenty buildings and four
   chimney stacks on the dockside skyline arc; account in the commit).
   **Still open, biggest first:**
   - **`city-kit-roads` 47 models, ONE named** (`light_curved`). Kerbs,
     crossings, barriers, cones, junctions — the densest unused kit there is
     and all of it is ground-level, where the player actually looks.
   - **`city-kit-suburban` 13 models, ZERO — an ENTIRE KIT UNREACHED.**
   - **`city-kit-industrial_detail-tank`**, the one industrial model left:
     84.8 x 41.5 x 51.5, a squat storage tank. Ground-level dock prop, so it
     needs a placement site rather than a skyline slot — its own item.
   - car-kit 39 unused, base-mesh 23, oga-vehicles 23.
   **MEASURE WITH `prop-dimensions` BEFORE PLACING ANY OF THEM.** Those
   numbers overturned the obvious plan for the industrial band: the
   commercial skyline models are slim towers (50x200) and the industrial ones
   squat masses (208x147), so reusing the tower height target would have
   built one wall of interpenetrating geometry no still could diagnose.
   **Name-matching, with the landed verdict as its accepting case** rather
   than a fixture — 24 keys the sim really placed, 0 false negatives.

1. **`kitAlbedo` NOW PRINTS `arrived>stands`** — the twelve `base_mesh_*`
   families were never unpainted, only measured before their repaint
   (account in `roadmap-history.md`). **Read the arrows next landing:** the
   claim is that every one stands well below `townWallAlbedo=0.15`, and
   `kitPainted` is the denominator that says the attribution ran at all.

1. **THE SPLAY DISTRIBUTION LANDED: median 29.3, p90 43.4, worst 120.8.**
   *(on screen, `review_day2_close`.)* Every other arm number is an angle
   from straight DOWN, so a fore/aft swing and a sideways splay read alike;
   `ArmSplayNow` projects onto the plane facing the body so only splay
   survives. The peak alone could not tell a `wave` (wired, firing) from a
   scarecrow — **the distribution can, and it says the street is fine**: a
   median of 29 degrees is an arm hanging with a walk swing, and 120 is the
   tail, not the norm. **Judge the p90 of 43 against the animation set**
   before calling it: 43 degrees at the ninth decile is a wide-ish idle, not
   a T-pose. `restArmDrop=8.0` says the bind is right either way.

1. **DECLUTTER: `namesClipped=0/83` — RAN, FOUND NOTHING, TEST SOUND.**
   `collidingNames=3` over 26 samples; three pairs still overlap after
   `PinAll` — read `namesPinnedSum` (106) vs `shotFixups` (27) before tuning.
   I suspected the edge test was blind and **read `ScreenRect` rather than
   assuming: no clamp** — it rejects only FULLY off-screen labels, so a
   partially clipped one reaches the check. Rare-event counter.

1. **FIVE OF SEVEN DISTRICTS HAD NO SHOPS AT ALL.** `the_Hook:shop73
   Copper_Row:shop4` and **zero everywhere else** — the Exchange is the
   financial district and had no commercial frontage; the Parade is the
   entertainment strip and was 37 houses and 24 flats. Shops were gated on
   `nearCore` alone and the dense cores sit in the Hook, so that flag had
   been answering "is this the Hook". Found by reading the new counter's
   OUTPUT, not the code. Two shares per district now (at a core and away
   from one); the Hook keeps 0.55 since frame-drift is calibrated on it.
   **Read `premisesByDistrict` next landing** — the mix is the judgment.

1. **THE DRESSING GATE WENT GREEN ON BUILD T** — 382 far-city pieces where it
   carried 37. **The old frame item under it is RETIRED, three regime changes
   stale** (it argued from a software rasteriser's 666ms). On the real GPU
   the frame is `game=5.6ms` of ~27.5ms, `perfOk` green, render four fifths.
   Start from the `frameCost` ladder in `## Now`.
1. **Smuggling** (M21) — **BUILT** (account in `roadmap-history.md`).
   Remainders: a player verb to recruit the signer, and gambling behind it.
   Read `cargoes`/`manifests` next build.
2. **The other day-job tracks** (M18) — `Core/DayJob` is the courier round,
   singular; the doc offers bar/courier/office on the first morning.
3. **Interiors beyond the pub** (M20) — every other door is a threshold.

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
