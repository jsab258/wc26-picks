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

**SILLS ARE IN AND FREE** (2133; +2173 renderers with render+rest
UNCHANGED — this scene is not submission-bound). Near buildings only,
reusing the pane/band `near` flag; no collider. Turning their shadow
casting OFF bought nothing and was reverted. Weathering went into the
TEXTURE (vertical run-off, signed so albedo holds at 0.15) after
doubling decals to 368 moved the count and not the picture. **Ground
roughness maps bound (24 Aug), normalised by each map's own mean so
the wet calibration held — reflMax 0.89 unchanged.**

**THE CROWD BEHAVES.** Density arrived as 13 people in convoy down the
CARRIAGEWAY: `Steer`'s first branch tested only for SOLID blockers, so
tarmac stopped nobody and the pavement rules below were unreachable.
Guard on how far a line RUNS ON road (12m, from the 8m avenue width):
headingIntoRoad 13 -> 5, crowdTightest 0.04 -> 0.23. **Its sampling
cost 1.9ms until coarsened 0.5m -> 1.5m.** The frame then showed 1-2
people: correct behaviour, fewer visible. DO NOT chase by loosening
the guard — the lever is where ROUTES go. meanFrame ~28.4ms with a
~1ms NOISE FLOOR (a comment-only build moved it 0.9ms), so sills cost
~1.5ms and single-run diffs under 1ms mean nothing. `places` went red
once and recovered untouched (3/289 flaky).
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

   **FOUR SKY HDRIs ARE FETCHED AND WIRED TO NOTHING** (24 Aug).
   `ledger/Assets/Sky/polyhaven/` holds 23MB of 2k captures — belfast
   open field, kloppenheim, misty farm road, industrial sunset — banked
   and attributed by `fetch_visual.py` on 23 Aug, and `grep` finds ZERO
   references from the Game layer. Built and not running (rule 6), on
   the one element in every outdoor frame.
   **NOT a wiring job, and that is why it is written down instead of
   done at speed.** Two obstacles, both real:
   (a) `Resources.Load` cannot reach `Assets/Sky`, and StreamingAssets
   cannot help because `LoadImage` reads PNG/JPG, not .hdr — so they
   must MOVE under `Assets/Resources`, which also moves the directory
   `attribution-check.py` maps to Poly Haven.
   (b) The procedural dome is CONTINUOUS: `LightModel` drives it per
   frame through dusk warmth, night sodium and a per-day cloud deck the
   ambient now reads from. Four fixed captures cannot do that, so a
   straight swap trades a continuous day for photographic detail and
   POPS between four states. The honest shapes are: HDRI as the
   reflection/environment source only (leaving the visible dome alone),
   or a blend of two captures across the hour with the dome's own
   colours still driving the tint. Pick one deliberately, on a still,
   before touching the asset paths.

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
1. **A THIRD OF THE NOON FRAME IS A BLACK WALL, AND IT IS NOT THE CAMERA.**
   *(on screen, `review_day1_noon` — the whole left third)* Measured 24 Aug:
   the frame's column thirds read **0.047 / 0.396 / 0.431**, a nine-fold
   split inside one midday frame. Four things are already ruled OUT, each by
   a number rather than a guess:
   - not framing — `nearFrac=0.00 midFrac=0.27`, both inside their bounds,
     so the wall is beyond 7m and the step-back has nothing to step back from;
   - not the texture — `concrete_b.jpg` has a mean luma of **0.366**, an
     ordinary mid-grey, and the census says the third is **85%
     `mat_concrete_b`**;
   - not the post stack, AO, vignette, sun or glass — every rung of the
     landed `noonFacade` ladder sits between 0.035 and 0.047;
   - and the arithmetic says it should be fine: albedo x ambient x exposure
     comes to ~0.43 display, which is exactly what the RIGHT third reads.

   **An eleven-fold shortfall cannot hide in a rung that moves 0.004, so it
   is not in that ladder — and a ladder is an allow-list.** Four rungs added
   and dispatched: `ambOff`, `amb4x`, `shadowOff`, `fogOff`. `amb4x` is the
   one that matters and it is the only rung that turns something UP: if the
   third scales, the wall takes ambient and the fill is not reaching a
   vertical face; if it does not move, the surface is refusing light and the
   answer is in the material. No off-rung can separate those two.

   **`noonFacadeMat` lands in the same run** so the second half needs no
   second round trip — material, shader, `_Color`, texture, distance, normal
   vs up and vs sun, AND the **MaterialPropertyBlock**, which `sharedMaterial`
   cannot see and which this project already has open as a linear-conversion
   suspect at thirteen sites.

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

1. **RAIN: height-coverage scaling built, wet frame PLANTED** (the
   daily roll is seeded off the day number, so review days 1-2 are dry
   on every run there will ever be — the sim forces a downpour at day 2
   hour 21 and takes `day2_wet` at 22, street-level, sodium on wet
   asphalt). Landed and judged; account in `roadmap-history.md`.

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

1. ~~**THE DISTANT SKYLINE WAS PALE LAVENDER OVER A NOIR STREET**~~ —
   **FIXED.** Kit props arrive wearing whatever their author painted them,
   and `BuildSkyline`'s kit branch kept them while its own `else` branch
   built the same tower out of `AssetLibrary.Concrete` and looked right —
   the fix existed one branch away. The general lesson is the item below:
   a kit prop's paint is never the author's, and a repaint that silently
   fails to apply looks exactly like one that was never asked for.
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

   **AND A CAR THAT IS REPAINTED IS STILL MINT, WHICH IS A DIFFERENT FAULT
   AND A WORSE ONE.** Measured off `review_street.jpg`: one saloon at
   **0.713** median saturation in a frame where nothing else passes 0.385,
   with lilac wheels. The repaint is not missing — `TrafficHost` has six
   town paints and most of the fleet wears them. Both paint sites set
   `_Color` through a property block **without asking whether the shader has
   one**, and this project already has it written down that glTFast's
   shaders do not, so the call evaporates in silence and looks identical to
   a paint that landed. One helper now — `AssetLibrary.PaintKit` — with
   `kitPaint=took/refused` and the first refusing shader NAMED, because
   "refused" and "refused by Unlit/glTF" are different amounts of work.
   Read it next landing; if refusals are non-zero the fix is replacing the
   material, not tinting it.

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

1. **THE NAMEPLATE HEAP IS MEASURED AND THE INSTRUMENTS AGREE WITH THE
   PICTURE.** *(on screen)* `collidingNames=3` over 26 samples: five labels
   at the peak, 3 of their 10 pairs overlapping — a heap, as the frame
   shows, and the "counter says 0, picture says heap" argument is over
   (account in `roadmap-history.md`). **Open is the DECLUTTER**: `PinAll`
   runs at shot time and three pairs still overlap. Read `namesPinnedSum`
   against `shotFixups` next build before anyone tunes it.

1. ~~**THE VERDICT HAS AMBIGUOUS KEYS**~~ — **THE EMITTER IS CLEAN AND
   GATED, 24 Aug.** The old plan here was "turn the file check into a gate
   once a verdict lands clean"; it went 30 same-line -> 34 instead, so that
   condition was never going to arrive and the decision had decayed.

   **The gate that exists now reads the SOURCE, not the landed file** —
   `tools/verdict-emit-dupkeys.py`, in `verify.py`, hard-failing. It answers
   in a second what the landed check answers one round trip later, and it
   was written because wiring `DoorSwing` added a second `doors=` to the done
   line three hundred lines from `WorldBuilder.Doors`. Nothing would have
   failed; the damage is to the OLD key, which had been readable for weeks.
   Caught by eye, which is what this file is a list of the consequences of.
   Confirmed against the actual colliding commit before being believed.

   **Two real hits fixed, no baseline list.** `Traffic: wheels` had `dia/hi=`
   beside `hi=` (a slash is not a word character, so `verdict-read.py`
   matched inside it) — now `diaPerHi`/`diaPerLen`; the §4.7 places line put
   three sub-records under one set of names and each key carries its place
   now, staying on ONE line deliberately. **And the tool's first version
   reported a key the file uses once** — the second was in a comment QUOTING
   it; comments are blanked now and that case is a selftest. Open: the
   landed-verdict backlog is still 34, and those are DATA collisions
   (`key=` inside bracketed values), a different fix from this one.

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
