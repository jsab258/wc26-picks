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

Clips: 65 filled and passing, 2 harvest holes, 0 wrong (three re-picks,
21 Aug). The street talks, argues, leans, works counters. **The front
is M17.10: the visual bar is GTA V** — item 1.

**THE PLAYTEST IS RETARGETED (22 Aug, Jafar):** *"I'll try to run it on
my windows machine after visual stuff is done. live voices/speech should
be working too."* **AND HE RAN THE PIPELINE THE SAME HOUR.** The
export audit came back ALL CLEAR (all three graphs on his disk, thirty
structural checks green, real audio out), and the timing read **1.7x
real time** on DirectML: 6.4s of work for 3.7s of speech — prefill
0.3s, 92 steps 4.4s (median 42ms), decode 1.7s. Token generation alone
is ~25/s against ~25/s consumption, so the overhang is the SERIAL
stages, not the model: the speech stage's first work item is
**the fp16 lever, measured on his card first.** The streaming overlap
already EXISTS in the backend (follower, pump, underrun arithmetic),
gated on a sustainability test his card misses by ~15%; the one-click
converter+timer shipped to his machine 22 Aug. If his number clears
~1.0x: the backend needs Float16 binds and edge conversions (it is
fp32-typed today), and `put-voices-in-build.py`'s fixed GRAPHS list
must learn the `-fp16` names or it silently drops them — the
truncation family's favourite shape. The `probe.py` listen page is
REPAIRED (the API-drift crash and the stale route text) —
it confused the one person it ran for. `playtest-plan.md` carries the
session runbook; keep the speech self-checks green on every landing.
**THE RUNNER IS REGISTERED AND FLIPPED (22 Aug): `ledger-pc` on his
machine picked up the probe build in seconds** — and the probe found
the two tools the cloud image had and his PC does not: no `pwsh` (the
verdict step's own shell) and no python3 in Git-bash. The workflow
shims python3 now; pwsh needs a real install —
`tools/runner/3 FINISH THE BUILD MACHINE.bat` does it in one admin
click and pushes `tools/runner/DEPS.txt`. **A watcher is armed on
that marker: when it lands (or he says "deps installed"), dispatch
the first real build** — one-time Unity install (~15-25 min), then
the ~6-10 min era and the first honest frame-gate reading. Revert
`runs-on` to `windows-latest` if his runner ever goes away.
**AND BEFORE THE PLAYTEST, THE FULL ULTRACODE AUDIT (Jafar, 22 Aug:
"a full ultracode audit before playtesting is a good idea. rememver
that").** A multi-agent sweep of the whole codebase — every system
against every rule in CLAUDE.md, every claim against its code, reach
and comment decay included — run as its own workflow when the visual
and speech stages close, with findings triaged into the queue before
he downloads the build. Token-heavy by design; he has pre-approved
exactly this run.

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

   **LANDED (21 Aug night, two builds):** V0+V1 whole — shadows, the
   sun:ambient rebalance, deeper AO, the opened day aperture, cloud
   cookie, grade split, decal wiring, exposure re-anchors; day2_noon
   showed real cast shadows for the first time. Still open from that
   pass: the shopfront void (V4) and the sky dome (V6).

   **LANDED (build D and since):** kit street furniture, double yellows,
   the decal sets, chimney pots and aerials, and the reaction set — all
   confirmed by counts in later verdicts and visible in the stills.

   **AND A LINEAR CLASS-FAULT UNDER TEST:** MaterialPropertyBlock colours
   skip the gamma-to-linear conversion, so every MPB-set tint authored in
   display terms weakened at the flip. The BODY WASH is fixed first because
   the palest-body catcher can verify it empirically (real bodies read
   213-223 against a crowd median of ~20); thirteen other MPB sites wait on
   that verdict rather than a theory-driven mass edit — if the wash read
   overcorrects, the theory is wrong at one site instead of fourteen.

   **V1.5 LINEAR IS CLOSED** (one flip + five measured rounds; every
   display-authored value re-armed off landed readings; noon 0.206,
   night 0.128, the lighting gate green — full account in
   `roadmap-history.md`).

   **V6 FIRST SLICE LANDED** (dusk warmth in fog and sky, sun glow,
   sodium deck, the dusk shot at hour 16 aimed sunward — all judged on
   landed frames). Open from V6: the sky dome's cloud structure per
   time of day. The 13 remaining MPB colour sites still wait on the
   wash verdict's next reading.

1. ~~**ABOUT A THIRD OF THE CLIPS ARE THE WRONG ANIMATION**~~ — **CLOSED,
   21 Aug: 65 filled, 0 wrong** (`roadmap-history.md`; 41 clips stay
   disk-only — combat-with-no-body-animation is milestone-scale).
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
   **The traffic self-contradiction is RESOLVED** (the tally named a
   taxi dwelling at its rank; dwelling and dormant vehicles are exempt
   since AC and the gate went green).

   **The tour pair landed and its prediction held** (real district
   spread 18.7-28.6, the metric has shape, Downtown most built).

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
   VARIANT THE BUILD CONTAINS, and the pack maps are load-bearing
   for that). AA landed: night 0.142, glow restored, sashes with
   dark frames near, hashed patchwork on wide bands, 122 interiors
   visible, wet frame the project's best, **1 of 72 gates red** —
   the frame budget, which is Jafar's-machine work. Watch, do not
   chase: worst glow blob 9.9% is one close-range window; two dim
   noons read brighter-than-night (d6/d8) inside the 8-of-10 gate.

1. **RAIN AT EYE LEVEL: wet frames now land every run** — judge the
   old black-scratches report against them; the magenta half is
   REFUTED, and the first landed wet frames read as streaks in lamp
   cones, not scratches.

1. **THE BODY BUDGET IS CLOSED AT 87.8% — account in `roadmap-history.md`.**
   Three things stay live. **The band, not the budget:** 13.1 walkers in frame
   per pass, only 6.5 inside the 34m band, so half the people you can see can
   never be skinned.

   **The pale-body hunt — THE HAIR IS CAUGHT (AD's close-up).** The
   arm's-length frame put a walker in shot and the hair renders as
   flat white glossy shards — unshaded or wrongly shaded at close
   range, the standing suspect photographed at last. Next: the hair
   meshes' material path in RealBody/CharacterPrefab (shader, gloss,
   or a missing texture on hair submeshes). The centre-third FootMesh
   reading stays open beside it. **Also from that frame:** the
   waist-lean posture confirmed up close (armStreet tail family), an
   unlit window band at point-blank reads as a void slab (accepted
   street-distance trade, noted), and the wall material at arm's
   length is GOOD — the close-range question is answered positively.
   Next rung for the probe: aim at an unoccluded wall patch.

   **The white pills are unidentified and NO COMMITTED STILL HAS ONE** —
   the pale figures measured DARKER than the walls (sixth wrong call off
   a picture). Next step stays: a measurement that fires WHILE one is on
   screen. The T-pose in that frame is separate and real.

   **`bodyWashUnreached=534` against `bodyTinted=1326`** — 40% of bodies render
   darker than the band because a multiply only subtracts. A limit, not a bug.
   **`RealBodyCap = 12` needs a PC measurement**, not a CI one.

1. **THE BUS AND BICYCLE ARE LANDED** (seven kinds live, zero fallbacks
   since P). Open judgment: the bicycle rides RIDERLESS — if a ghost bike
   reads worse than the primitive did, next rung is a rider or parked-only.

1. **PATROL DENSITY FOLLOWS THE INQUIRY — whether it READS is unfinished.**
   Every link fires (account + four wrong theories in `roadmap-history.md`).
   Open: `patrolOnBeatMean=0.00` over 3 shots against `0.18` over 17 — zero
   of three separates nothing; the `hunt_` pair photographs the manhunt now,
   so the next build has frames to judge from. A patrol PARKED with its
   beacon lit stays in frame where six crossings do not — feature, not knob.

1. ~~**THE VERDICT STEP IS 416 CHARS OFF A HARD CEILING**~~ — **STALE:
   measured 22 Aug at 17,088 UNDER it** (the extraction already happened;
   the item outlived it — rule 3). `verify.py` gates every commit on it.

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
   382 pieces where it carried 37; the fractional-slot fix, account in
   the dressing commit. **THE FRAME GATE STAYS RED AND THE COST HAS
   MOVED — this item was two regime changes stale.** **Read the breakdown, not the mean**: `mean=666.4ms` is a
   software rasteriser and says nothing; `game=24.53ms` against a 12ms budget
   is a 104% overrun in OUR code.

   Current: `npcs=9.48 bodyLod=4.68 mix=3.75 traffic=2.51 sun=1.27
   population=1.40 rigs=1.25`. **`npcs` is now the dominant cost** — the series
   says it tripled (~2.3-3.3 → ~4.4 → ~8.6-9.5 across three regimes) while
   `game` went 14→18→24ms. Start there, not at bodyLod (a once-a-second FULL
   pass; spreading it round-robin needs the measurement split from the sweep
   first, and tuning belongs on the PC). **`sun` is settled** — it read 3.15ms
   only because the audio mix ran inside its timer.

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

**Reactions are LIVE and the asks are measured** (build P: 82 played;
flinch 11of61, glance 62of284, wave 4of8, point 1of2, head_no 4of6 —
most refusals are glance cooldowns, which is the cooldown doing its
job). **greet reads 0of0 and that is the SIM'S ECONOMY, not a wire
fault**: the gesture fires only for a loyal (≥0.35), need-route crew
member passing the player, and the sim skims — worst loyalty 0.225 —
so the condition never exists in a run. Deliberately NOT planted: a
staged loyal runner would pollute the crew-decay gates that measure
skimming. The wire is proven by the other five kinds sharing its code
path. If a future run's crew stays loyal, greet gets its first ask
free.

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
- **Read a system and write down what it actually does.** Every system here has
  at least one comment that is now false — the supply is unlimited, and each
  one found is a bug that would otherwise have been believed. **Read the code
  that produces a number too**: three faults in `CollidingNames` on 20 August,
  found by reading rather than by any reading it produced.
- **Turn a still into a number.** Five faults found by opening a frame and none
  by a gate. Anything a frame shows that no metric names is a metric worth
  adding.
- **DROPS DELIVER EVERY RUN (T:2, U:4, V:3, X:1, Y:2).** The chest-cast
  landed for the window-band pin. Open: the d12 shape — a night whose
  window the job never owned (`held:waypoint`, ran=0) while the skip
  plant's count says it stopped at day 11. Trace-first: read TraceJob's
  window source against the active-job timing before any change.
