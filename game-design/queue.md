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
on his machine** via bats 3/4/5 (double-click, self-elevating, NO
INSTALLERS — pwsh/python as plain zips). Account in
`roadmap-history.md`.
**ALL 72 GATES GREEN and holding (23 Aug).** ~17.6 min/round on his
GPU vs cloud 33-41 over 11 rounds; the BUILD is no longer the
bottleneck, the ~35 min dispatch cadence is. CLOSED today: hair,
furniture, clip sheet, **dayJob** (courier rides StreetMap.Route
after two traced mornings grinding on a window sill then a building
corner), **beats** (same router), noonFacade-as-a-question (census:
60% grey brick / 39% mat_roof — shopfront surrounds and awnings were
built from roof felt, now painted joinery + canvas via Opaque()).

**PERFORMANCE IS MEASURED; THREE GUESSES DIED.** `frameCost` ladder:
all:22.4 noShadow:17.3 noPixLights:18.0 noBodies:23.3. **Shadows
5.1ms and per-pixel lights 4.4ms hold the frame; the crowd is not in
the bill** (hiding every body came back SLOWER). Dead: draw calls
(instancing — a real missing flag, kept — moved meanFrame 0.00),
vertex budget, shadow reach (shadow45 21.2 vs all 21.6 — 0.4ms of
5.1, rejected). The ladder's ABSOLUTES are not a frame time (its RT
+ ReadPixels carry per-object cost the composited frame does not);
only the rungs' differences are.

**THE STREET WAS NEVER AS EMPTY AS THE PICTURES.** Three faults, all
found by measuring: (1) `Population.NearMetres=34` meant nothing past
a block of the player was DRAWN — now 70 (BandSlack 6->12 with it,
spent as a proportion), crowdWalkers 8 -> 22; (2) **`streetBodies`
was a viewport-RECTANGLE test counting people through walls** —
`streetBodiesSeen` (linecast, the test `Shot` already ran for the
player and never pointed at the crowd) read **19 in cone / 3
visible**; (3) the cameras stood badly — `midFrac` (2..7m band)
sorted across 28 shots was bimodal (nights/tours 0.00-0.25, day
street shots 0.35-0.69), so `ShotMidBlockedAt=0.30` sits in the
widest gap as `ShotBlockedAt` does in its own. **12 of 13 triggered
shots fixed**; day1_noon is the one that gave up (canyon;
straight-back-never-re-aimed is deliberate — findings cite these
filenames). The street shot ALSO fled the crowd by design (slid along
until nobody within 2.5m, any direction) — now 1.6m and in-front
only. Day frames are NOT like-for-like across these.

**23 Aug evening — THE DAY NOW READS AS DAY.** The biggest single
win of the day and it was a MEASUREMENT, not taste: day3_noon was
0.206 mean against day3_night 0.165 — a midday a quarter brighter
than a midnight. `Exposure` had been revised six times chasing this,
each time a chosen number read against one frame. `exposureCurve`
printed the response instead (x1.00:0.199 x1.50:0.256 x2.00:0.302
x3.00:0.373 — roll-off real but gentle, so the aperture IS the
lever). Target bounded by landed readings on BOTH sides: 0.44-0.49 /
40-48% bright was measured and rejected as "seaside-morning white",
0.206 reads as night. Day arm 0.72 -> 2.44 lands noons 0.30-0.41 at
12-33% bright, nights untouched at 0.14-0.18, noon:night 1.25 ->
2.35:1. **Two things would have eaten it silently: the Clamp ceiling
(1.85 against a noon of 1.72 — raised to 3.6) and the rain term
(scaled with the arm or "an overcast day loses light" halves).**
Three break fixtures re-anchored.

**SILLS ARE IN AND FREE** (2133; sceneRenderers 19810 -> 21983 with
render+rest UNCHANGED at ~21.4ms — this scene is not
submission-bound). Near buildings only, reusing the pane/band `near`
flag; no collider, per the courier's 197 ticks against a window box.
Weathering moved into the TEXTURE first (vertical run-off on
brick/plaster/concrete, signed so albedo holds at 0.15) after
doubling decals to 368 moved the count and not the picture.

**THE CROWD BEHAVES.** Density showed up as 13 people in convoy down
the CARRIAGEWAY; cause was `Steer`'s first branch testing only for
SOLID blockers, so tarmac never stopped anyone and the pavement rules
below were unreachable. Guard on how far a line RUNS ON road (12m,
from the 8m avenue width): headingIntoRoad 13 -> 5, crowdTightest
0.04 -> 0.23, road clear. **Its sampling cost 1.9ms of npcsMs until
coarsened 0.5m -> 1.5m (npcsMs 5.99 -> 4.85).** The frame then showed
1-2 people again: correct behaviour, fewer visible. DO NOT chase by
loosening the guard — the lever is where ROUTES go. meanFrame ~28.4ms
(from ~25 this morning) for all of today's density+sills; perfOk
green. `places` went red once and recovered untouched (3/289 flaky) —
if it returns, suspect the routing change, not the ledges.
Revert `runs-on` if he bows out.
**BEFORE THE PLAYTEST, THE FULL ULTRACODE AUDIT** (Jafar, 22 Aug:
"a full ultracode audit before playtesting is a good idea. rememver
that"). Multi-agent sweep of the whole codebase against every rule in
CLAUDE.md, findings triaged into the queue before he downloads the
build. Pre-approved; token-heavy by design.

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

   **LANDED, accounts in `roadmap-history.md`:** V0+V1 whole; build D's
   kit furniture, yellows, chimney pots, aerials, reactions; **V1.5
   LINEAR CLOSED**. Open from those passes: sky dome (V6).

   **LINEAR MPB CLASS-FAULT UNDER TEST:** MPB colours skip
   gamma-to-linear, so display-authored MPB tints weakened at the flip.
   BODY WASH fixed first; 13 other MPB sites wait on the verdict, which
   was itself **blocked by its own instrument** until 23 Aug — the
   palest-part table named BlobShadow (a multiply quad sampling the
   pavement) four runs running; attribution now skips Hidden/ shaders.
   Real remainder: feet and shoes at 224-234, both tiers.

   **V6 FIRST SLICE LANDED** (dusk warmth, sun glow, sodium deck —
   judged on frames). Open from V6: the sky dome's cloud structure
   per time of day.
1. **THE STILLS NO LONGER PHOTOGRAPH WALLS, AND THE METRIC IS STILL TOO
   NARROW.** *(rule 12; the step-back and depth series are landed —
   account in `roadmap-history.md`.)* **The night half is ADDRESSED:
   the night shutter now aims down the longest clear sightline (eight
   compass rays, rides AE) — judge on its landing.**
   **The day twin landed on V:** day2_noon stepped back from 0.44 to
   0.24 near-fraction — passing the 0.25 bound — and the frame is still
   half wooden hoarding: a MID-DISTANCE occluder a few metres out fills
   the frame while sitting past the arm's-length test. Same repair as
   the night case: measure occlusion at the distances that blind a
   frame, not only at arm's length.
   **Traffic contradiction RESOLVED** (dwelling/dormant exempt, gate
   green); **tour pair landed, prediction held** (Downtown most built).
   **midFrac column landed f4a1243: day1_noon reads 0.49** — the series
   the mid-distance bound will come from.

1. **THE RAIN'S HEIGHT-COVERAGE SCALING IS BUILT AND THE WET FRAME IS
   PLANTED.** The emitter box and rate already grow with camera height
   (the Hook swarm-patch fix, in Weather since the last batch) — what
   was left was a frame to judge it by, and "wait for a wet run" could
   never end: the daily roll is seeded off the day number, so review
   days 1-2 are dry on every run there will ever be. Planted instead
   (rule 5b's corollary): the sim forces a downpour at day 2 hour 21,
   takes `day2_wet` at 22 street-level after dark — sodium lamps on wet
   asphalt, the look this game is about — and snaps the seed's dry
   state back before the 23:00 night gates. Read the frame when it
   lands; it also answers the "black scratches at eye level" item.
   **Correction from V's own stills:** day 1 IS wet this run (streaks
   in the dusk and night frames), so "the seed pins both review days
   dry" was overstated — day 2 is the dry one, and the plant's value
   is the guarantee at street level, not an impossibility ended.

   **THE CAPSULES STAY FIXED** (zero on P, Q, R and S — closed). **THE
   FLOATING BRICK SLAB IS SOLVED (build V):** the widest-four catcher
   names the family — one building's cornice, fascia and two 23m
   window bands, all aloft BY DESIGN — and the day1 noon frame shows
   the real fault: window bands wear the pack's window texture, which
   is a whole FACADE photograph (brick piers and a six-by-six sash
   grid), so a band at close range reads as a floating brick wall.
   **THE WINDOW ARC IS CLOSED (AA, 22 Aug) and the real killer was
   the KEYWORD SET**: dropping the pack normal/gloss changed the
   window material's shader keywords to a combination the built
   player has no variant for, and Unity silently fell back to a
   no-emission variant — the mask, the white, and the bind-revert
   were all surgery on a shader that was not running (the emission
   case's four theories and their falsifications are in the commit
   log; the lesson: A RUNTIME MATERIAL'S KEYWORD SET MUST MATCH A
   VARIANT THE BUILD CONTAINS). AA landed: night 0.142, glow
   restored, 122 interiors visible. Watch, do not chase: worst glow
   blob is one close-range window.

1. **RAIN AT EYE LEVEL: wet frames land every run** — the magenta
   half is REFUTED; landed wet frames read as streaks in lamp cones.

1. **THE BODY BUDGET IS CLOSED AT 87.8% — account in `roadmap-history.md`.**
   The band question is ANSWERED (23 Aug): the 34m draw radius was the
   binding constraint, now 70m, and `RealBodyCap` got its PC
   measurement at last — the render ladder priced the whole drawn
   crowd at ~1.1ms, so 12 -> 28. **Hair CLOSED** (cutout remap, proven
   in number and close-up pixels). Still live: the centre-third foot
   reading (FootMesh 234, Ch38_Shoes 224 — the blob-shadow entry that
   outranked them was a multiply quad sampling the pavement, now
   excluded); the white pills remain unidentified with NO COMMITTED
   STILL holding one, and the next step is still a measurement that
   fires WHILE one is on screen. `bodyWashUnreached` ~500 against
   `bodyTinted` 2048 — bodies rendering darker than their band because
   a multiply only subtracts. A limit, not a bug.

1. **BUS AND BICYCLE LANDED** (seven kinds, zero fallbacks since P). Open
   judgment: the RIDERLESS bike — if it reads wrong, rider or parked-only.

1. **PATROL DENSITY FOLLOWS THE INQUIRY — whether it READS is unfinished.**
   Links fire (`roadmap-history.md`). Open: `patrolOnBeatMean=0.00` over 3
   shots vs `0.18` over 17 — zero of three separates nothing; judge the
   `hunt_` pair. A PARKED beacon reads where six crossings do not.

1. ~~**VERDICT STEP NEAR THE DISPATCH CEILING**~~ — **STALE: 17,088
   under, measured 22 Aug (rule 3); `verify.py` gates it.**

1. **THE DISTANT SKYLINE WAS PALE LAVENDER OVER A NOIR STREET.** *(on screen,
   `district_strip` — the top third of the frame)* Kit props arrive wearing
   whatever their author painted them, and `BuildSkyline`'s kit branch kept
   them while its own `else` branch built the same tower out of
   `AssetLibrary.Concrete` and looked right. **The fix already existed one
   system over:** `TrafficHost` repaints kit cars for exactly this reason —
   its comment says the kit ships "holiday-brochure mint" and the first stills
   had every car wearing it. Same shape, and the skyline never got it.

   Tinted to agree with its own fallback rather than to an invented colour,
   and darker than the near town because these stand at the map's far edge —
   a skyline brighter than the street in front of it is the specific thing
   that read as wrong. `skylineRepainted` ships beside `skyline=n/m` so the
   repaint cannot silently stop running, which is how this survived.

1. **AND FOUR MORE KIT-PROP SITES ARE UNPAINTED — THE MEASUREMENT IS BUILT,
   READ IT ON THE NEXT LANDING.** *(rides next dispatch)* Benches, bins,
   street lights and the crate stack take no repaint — deliberately: a green
   bench is plausible, and mass-repainting on resemblance is the rule-4
   mistake. The instrument: `kitAlbedo=[family:val/...]` on the done line,
   every kit family's mean material albedo (linear tint x GPU-blitted texture
   mean, measured once per key at the `TryInstantiateProp` choke point),
   brightest first so the ten-family cap cannot hide a positive, beside
   `townWallAlbedo` — the four wall surfaces through the SAME maths.
   Awning/car/skyline entries are pre-repaint (their repaints have their own
   counters); the unrepainted four carry live values. **Judgment when it
   lands:** any unrepainted family clearly above `townWallAlbedo` gets the
   skyline treatment; anything at or below it closes this item.

1. **THE BUBBLE OVERLAP MEDIAN IS A PER-TICK NUMBER AND I READ IT AS A
   PER-FRAME ONE.** *(instrument)* `SampleBubbles` runs per tick and
   `CollidingNames` runs per shot, and BOTH wrote to `_bubbleOverlap` — so the
   median is seventy-odd tick readings with twenty-six shot readings rounded
   away. **The mixture gave itself away in the denominators:**
   `bubbleSamples=71` against `collidingNameSamples=26`.

   **I got this wrong first.** The median moved 0.33 to 0.00 between builds and
   I recorded it as the measurement-order fix working. It cannot have been —
   that move changed WHEN a minority of samples are taken and the majority
   never went near it. What moved was the street: the district fix spread the
   population out, so more instants have two bubbles up (39 to 71) and fewer
   collide. **A real improvement, and not the one I claimed.**

   Split now: `bubbleOverlapMedian` per tick, `bubbleOverlapShotMedian` over
   frames that become files, with both counts printed. **Read the shot median
   next build** — it is the first number that can be checked against a still.

   **Still open, and unaffected by any of this:** `bubblesLiftedSum=1` against
   `shotFixups=27` — the de-overlap moved a bubble once in a run, while
   `namesPinnedSum=106` over the same shots shows the site works. And
   `collidingBubbles=3` with `bubblesAtWorst=3` means all three pairs
   overlapped at the worst instant. Do not touch `LiftAtShot` until the shot
   median lands: a pass that fires once may be broken, or starved by a
   measurement that could not see it.

1. **THE NAMEPLATE HEAP IS MEASURED AT LAST AND THE INSTRUMENTS AGREE WITH
   THE PICTURE.** *(on screen)* `collidingNames=3` over 26 samples, worst at
   `day13_noon`; `worstNamePair=[Noor|Sam]`, `namesAtWorstName=5`,
   `textPersonLabels=10`. Five labels projected at the peak, **3 of their 10
   possible pairs overlapping** — a heap, as the frame shows. The
   "counter says 0, picture says heap" argument is over; account in
   `roadmap-history.md`. **What is open is the DECLUTTER**: `PinAll` runs at
   shot time and three pairs still overlap. Read `namesPinnedSum` against
   `shotFixups` next build before anyone tunes it.

1. **THE VERDICT HAS AMBIGUOUS KEYS AND NOTHING HAD EVER LOOKED — 30 same-line
   and 5 cross-line, measured.** `tools/verdict-dupkeys.py` is new and reports
   them; `verify.py` runs its selftest as a gate and prints the file's counts.

   **The two that mattered are fixed.** `collidingWorldText` read **5** on the
   glyphs line and **9** on the done line of one run — the glyphs line was
   emitted on **day 2** of a seventeen-day run while its peaks kept rising for
   another fifteen days, so it has been publishing a partial as a summary since
   it was written. It is emitted at the end of the run now. And `clean=`
   appeared TWICE on the done line, 310 from the purse and 0 from the Act III
   snapshot; the snapshot's pair is `a3clean`/`a3dirty` now.

   **What is left is a real backlog.** The remaining same-line hits are lines
   carrying several sub-records at once — `Traffic: wheels` puts a dimension
   and a ratio both under `hi=`, and two lines repeat a whole per-walker record
   three times. A grep gets an arbitrary one of three. **The fix is one line
   per record**, as the sky readings already do.

   **AND THE GATE IS NOT ON YET, ON PURPOSE.** The landed verdict still carries
   the collisions — it came from the build before the repair, so gating now
   would go red on arrival (rule 5b's corollary). **Turn the file check into a
   gate once a verdict lands clean.**

1. **AND THE SAME COUNTER IMMEDIATELY FOUND A BIGGER ONE: FIVE OF SEVEN
   DISTRICTS HAD NO SHOPS AT ALL.** `the_Hook:shop73 Copper_Row:shop4` and
   **zero everywhere else** — the Exchange is the financial district and had no
   commercial frontage; the Parade is the entertainment strip and was 37 houses
   and 24 flats. Shops were gated on `nearCore` alone and the dense cores sit
   in the Hook, so the flag had been answering "is this the Hook".

   **The warehouse fault a second time, in the branch immediately below it** —
   and found by reading the new counter's output, not the code. Two shares per
   district now (at a core and away from one), because both are real: a
   district has a character and its centre carries more trade than its edges.
   The Hook keeps 0.55 at a core, since every frame-drift check is calibrated
   on it. Tested both ways — five districts must have shops, and the Parade
   must out-trade Fairview by a clear margin, or "everywhere is a high street"
   would pass. **Read `premisesByDistrict` again next build.**

   **Ironside has only 7 dressed frontages against 40-135 elsewhere**, because
   it is excluded from terracing and takes the legacy block path. The
   industrial quarter is nearly undressed. Noted, not chased.

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
| textures | 2K colour+normal landed; roughness wired on walls | ground roughness (SetWetness must drive _GlossMapScale); AO maps |
| buildings | procedural terraces, photo surfaces, pots+aerials | window reveals/sills relief; shopfront depth (V4) |
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
