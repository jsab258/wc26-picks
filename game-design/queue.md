# The work stack

> **STATUS — LIVE**, verified 2026-08-15. What gets picked up next, in order.
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

The Mixamo harvest landed complete — 67 clips — and the street came alive with
it: people talk, argue, lean, smoke, work counters, carry shopping. **But
twenty-one of the 67 play the wrong motion — item 1.** Accounts in
`roadmap-history.md`. NEXT: T3 queue points and standing destinations.

**THE PLAYTEST IS DEPRIORITISED (18 Aug, Jafar):** *"Don't worry about
timelines or the near goal or play testing. Just keep building."*
`playtest-plan.md` stays live as the Mac setup record. Live speech stays
parked — no DirectML on the Air.

### Startable right now, ORDERED BY WHAT SHOWS ON SCREEN

1. **ABOUT A THIRD OF THE CLIPS ARE THE WRONG ANIMATION — twenty-one of
   sixty-seven.** *(on screen; the re-pick runs on Jafar's machine)* Found by
   the travel column I had written off the day before: `Walking` reads 0.00m
   and `Standing Arguing` 3.75m. **`walk` is a stationary guard pose with the
   hands up**, so the slot the whole street is named after does not contain a
   walk. The picker screens on both axes now — hips for upright-or-floor,
   travel for does-it-move — with bounds from the measured gap. Twenty-one
   rejected, forty-six accepted.

   **For Friday:** the re-pick REFUSES a candidate whose contents contradict
   its name and tries the next; a slot the catalogue cannot fill reports
   MISSING. **Holes are the right outcome and they are the information.**
   **Not caught, and said so:** `sit` renders standing at 96cm and the three
   sitting clips read 18, 94 and 96, so there is no correct example to set a
   band from. Account in `clip-findings.txt`.

1. **THE STILLS NO LONGER PHOTOGRAPH WALLS, AND THE METRIC IS STILL TOO
   NARROW.** *(rule 12)* The camera steps back off anything filling more than
   a quarter of the frame at arm's length, bound from a measured bimodal
   series, exercised on a real 0.83 case. Account in `roadmap-history.md`.
   **The median ray distance SHIPS THIS BUILD.** Same 84-ray grid, one pass,
   both numbers: the fraction still answers "is the camera against a wall" and
   `shotDepthMedian` answers "can it see the street" — which is what
   `review_day5_noon` needed, slabs across the middle at ten metres reading
   near zero on the fraction. No bound on it: there is no landed series yet.

   **And the tour got its own pair**, `tourDepthBy=[...]` keyed by district and
   sorted shortest-first, because "which districts look unbuilt" needs the name
   attached to the number and a sorted series structurally cannot carry one.
   **A prediction is written into the emitter before the run**: the tour camera
   is 14m up and 34m back at about 20 degrees down, so flat empty ground should
   read north of 40m and a built street ten to twenty. If all seven come back
   within a few metres of each other the ground plane is dominating and the
   metric is the wrong shape — say so, do not reinterpret it.

   **Also fixed while in there:** the `!_touring` block's own comment claimed
   the blocked-frame series excluded the district tour. The `Add` sat outside
   that block, so seven teleported frames had been going into it.

1. **THE CREW TIER OF `looseEnds` NEVER OPENS** — `crew=2`, nobody below the
   poach floor, so it has never once fired in the project's recorded history.
   Same shape as the Law tier, off for entire runs until the denominator
   caught it (fixed, landed `[Law:1,Owed:5]/open7/2of6`). **Plant the
   condition, do not loosen the floor.**

1. **THE RAIN READS AS BLACK SCRATCHES AT EYE LEVEL.** *(player-height frame,
   dfefd62)* Fine from the elevated camera, dense dark striation from the
   player's eyes, likely sized for a downward view. **Every run since has come
   back dry — this needs a WET run, not another look.** The magenta half of
   that report is REFUTED.

1. **THE BODY BUDGET IS CLOSED AT 87.8% — account in `roadmap-history.md`.**
   Three things stay live. **The band, not the budget:** 13.1 walkers in frame
   per pass, only 6.5 inside the 34m band, so half the people you can see can
   never be skinned.

   **The white pills are unidentified and NO COMMITTED STILL HAS ONE.** The
   pale figures in `review_street.jpg` measure `#5d626f`/`#66676a` against
   buildings at `#7f838f` — DARKER than the walls — and that frame's brightest
   1% is entirely the harbour. I called them white off the picture, the sixth
   wrong identification. **Next step is a measurement that fires WHILE one is
   on screen.** The T-pose in that frame is real and separate — `armStreet`'s
   tail, which a median cannot see.

   **`bodyWashUnreached=534` against `bodyTinted=1326`** — 40% of bodies render
   darker than the band because a multiply only subtracts. A limit, not a bug.
   **`RealBodyCap = 12` needs a PC measurement**, not a CI one.

1. **NO BUS AND NO BICYCLE EXIST IN THE KIT — the remaining primitives.**
   `vehicleFellBack=[bus,bike x6]`. All 50 car-kit models ARE extracted and
   neither is among them, so this is a sourcing gap: another CC0 kit, not more
   code. One bicycle model closes almost all of it. (The police car is in;
   account in `roadmap-history.md`.)

1. **PATROL DENSITY FOLLOWS THE INQUIRY — and the measurement of whether it
   READS is still not finished.** Weight by stage (None 1 ... Manhunt 5),
   converted only on parked cars, routed to a beat in the player's district,
   stood down when the inquiry clears. Every link fires. Account and the four
   wrong theories in `roadmap-history.md`.

   **What is open:** `patrolOnBeatMean=0.00` over 3 shots against `0.18` over
   17 — zero of three separates nothing. The `hunt_` pair photographs the
   manhunt now, so the next build has frames to judge from. **Still unread:**
   six cars that never stop are six brief crossings; a patrol PARKED with its
   beacon lit stays in frame. A feature, not a knob.

1. **THE VERDICT STEP IS 416 CHARS OFF A HARD CEILING AND FAILS AT DISPATCH,
   NOT AT COMMIT.** *(CI)* A 422 at dispatch means NO Windows build at all.
   **The real fix is extraction**, as `sim-shots-stage.sh` proves: move the
   step body to a script file. Until then every comment there is a coin flip.

1. **THE FIRST MANHUNT FRAME IS BAD, AND IT IS THE FIRST ONE ANYONE HAS
   SEEN.** *(on screen)* `hunt_day13_noon`: fifteen people packed shoulder to
   shoulder in the road, a dozen NAMEPLATES stacked in an overlapping heap,
   and a giant red `... you ...` caption across a building face.

   **THE `collidingNames=0` ARGUMENT IS SETTLED, AND THE COUNTER WAS WRONG
   THREE SEPARATE WAYS.** Read the code rather than the readings:

   - **The shot-time samples never reached the printed number.** Called from
     the daily audit, whose return was assigned to the field, and once per shot
     — where the return was THROWN AWAY. The verdict showed one arbitrary audit
     moment and no photographed frame ever reached it. Every neighbour on that
     line became a peak weeks ago; this one travels by RETURN VALUE, so the
     sweep could not see it.
   - **It was sampled before the camera finished moving.** The call sat at the
     top of `Shot`; the declutter step-back moves the camera up to twelve
     metres afterwards. Same-instant rule, applied to `nearFrac` in the commit
     that added the step-back and not to its twin one line away.
   - **`worstNamePair` could never say anything.** Computed by the boxes loop
     and then unconditionally reset to `none` a hundred lines below, by a reset
     correctly placed for the WORLD pair and copied without moving it. The
     diagnostic added to settle this exact question has printed `none` every
     run since the day it was written.

   All three fixed. `collidingNames` is a peak over every sample now, with
   `collidingNameSamples` as denominator and `collidingNamesWhere` naming the
   shot — **so landed values are not comparable across this commit.**

   **Two visual reads of mine were wrong and measured so before publishing:** a
   "magenta cluster" (zero magenta pixels in the frame, so no error shader) and
   a "pink object" (the only pinkish blocks are the stop sign and the caption).

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

1. ~~**THE OUTER DISTRICTS LOOK UNBUILT**~~ — **CLOSED, AND THEY WERE NEVER
   UNBUILT.** *(on screen)* Five places read the UNSCALED avenue arrays as map
   coordinates while `WideBlocks` stretches the city about the origin. Four
   districts' buildings stood 136-184m from the streets named for them, the
   tour camera aimed at the gap, residents spawned there, and the ground plane
   was sized to the unscaled map. Account in `roadmap-history.md`.

   **The before/after is unambiguous and the control held.** `tourDepthBy` went
   from `hook:24.3` with every other district at **40.6-45.6** — the bare-ground
   figure predicted in advance — to a 18.8-28.5 band, every district reading as
   built, with **the Hook unchanged at 24.3** as the control. Downtown is the
   most enclosed, which is right for offices. The frames agree: a brick canyon,
   and Fairview villas with chimney pots.

   **A fifth consequence, unlooked for:** the outer districts were built with
   `district = null` and got the DEFAULT terrace massing. `terraceParcels` 376
   to 331 is deeper office plans finally reaching Downtown.

1. ~~**A DOCK NAME ON A FAIRVIEW SHOPFRONT**~~ — **THE SIGN WAS INNOCENT.**
   *(on screen)* The name pool is chosen correctly by building type; **the
   warehouse was what should not have been there.** `Dressing.KindAt` made a
   quarter of every frontage away from a core a shed in EVERY district — its
   own comment records making that mistake once with `prosperity` and fixing
   it with `nearCore`, which separates a district's centre from its edge and
   is not a district signal either. Only fixable today: `DistrictAt` answered
   `null` for most of the map until this session. Share is a per-district
   table from the briefs — Ironside 0.55, the Hook 0.25, Copper Row 0.10, zero
   for the Exchange, the Parade, Fairview and Gullwing — looked up inside
   `KindAt` so no caller can forget it, and tested over each district's real
   bounds with the sample size asserted first.

   **LANDED AND IT MOVED THE RIGHT WAY:** `premises` went `shed54 house86` to
   `shed10 house130` — forty-four sheds became houses. **But a total cannot
   say WHERE**, which is the only thing the district table claims, and ten
   sheds town-wide looks low for a quarter set to 0.55. `premisesByDistrict`
   ships next build. It is also the rule-6 check on the table: CoreTests proves
   `KindAt` RETURNS sheds for Ironside, not that the Game layer ever asks it
   about an Ironside wall. **Read Ironside's row first**; if it is near zero
   the suspect is `nearCore`, which suppresses the shed branch entirely and is
   computed from core positions this test cannot see.

1. ~~**THE MARGIN SHOULD BE HALF A BLOCK**~~ and ~~**THE MARGIN FIX WEDGES
   TRAFFIC**~~ — **BOTH WITHDRAWN; two wrong explanations for one real bug.**
   The margin never mattered. And "it wedges traffic" came from a gate that
   compared two instants sixty seconds apart, so a car that drove a loop read
   like one that never moved — the flagged car had crossed **eight edges**.
   That pair of wrong readings delayed the real fix by a day. Gate now reads
   the whole window, predicate asserted both ways.

1. ~~**`vehiclesKitted=26/33` WHERE THE FLEET IS 28**~~ — **RENAMED** to
   `bodiesKitted=`, with `fleetNow=` beside it. Both sides count bodies BUILT
   over the run and rebalancing rebuilds them, so 33 for 28 vehicles is the
   rebalance working. The arithmetic was never wrong; the name was.

1. **THE FRAME GATE IS RED AND THE COST HAS MOVED — this item was two regime
   changes stale.** **Read the breakdown, not the mean**: `mean=666.4ms` is a
   software rasteriser and says nothing; `game=24.53ms` against a 12ms budget
   is a 104% overrun in OUR code.

   Current: `npcs=9.48 bodyLod=4.68 mix=3.75 traffic=2.51 sun=1.27
   population=1.40 rigs=1.25`. **`npcs` is now the dominant cost** — the series
   says it tripled (~2.3-3.3 → ~4.4 → ~8.6-9.5 across three regimes) while
   `game` went 14→18→24ms. Start there, not at bodyLod (a once-a-second FULL
   pass; spreading it round-robin needs the measurement split from the sweep
   first, and tuning belongs on the PC). **`sun` is settled** — it read 3.15ms
   only because the audio mix ran inside its timer.

1. ~~**THE BUBBLE STACK'S SCREEN PASS BARELY RUNS**~~ — **STALE ITEM; THE FIX
   WAS ALREADY IN.** `SpeechBubble.LiftAtShot` exists, is called from `Shot`
   after the pin, and is emitted. Rule 3: the doc said missing, the code said
   built. **What WAS wrong is what it fed** — it, both `PinAll`s and
   `Billboard.AimAll` return what they did on THIS shot, and all FOUR were
   assigned straight to done-line fields, so each described whichever of twenty
   shots ran last. The fourth was found by grepping for the shape after fixing
   the first three; it sits three lines above them, written the same evening.
   Sum and peak now over `shotFixups`, one shared denominator. **Read
   `bubblesLiftedSum` against `bubblesAtCeiling` next build.**

3. **THE DWELL FIX TRADES A VISIBLE FAULT FOR AN INVISIBLE SAVING.**
   `bodyLodMs=4.68` against `populationMs=1.40` — the LOD pass costs three
   times the reband it hides inside. **Decide against `gameShare`, not
   milliseconds.**

8. **SWEEP THE GAME LAYER FOR DEAD MEASUREMENTS THE REACH LEDGER CANNOT
   SEE.** The ledger covers public Core APIs; a PRIVATE method with no caller
   is invisible to it. Listing every value-returning measurement in
   `SimDirector` and grepping each for a call site found `FrameLuma` — a full
   640x360 off-screen render plus a ReadPixels, never once called, duplicating
   `FrameShot(cam).Mean` which has ten call sites. Deleted. **Do the same
   sweep for the other Game-layer files**; it is two minutes each.

8. **KEEP RETIRING THE REACH LEDGER — 37 entries.** **READ THE ENTRY'S
   REASON, NOT JUST ITS NAME**: three were wrong on 4 August, describing a
   consumer somebody intended rather than one that exists.

9. **JUDGE THE LIMP FROM A FRAME.** The pose limp was a sixteenth of the audio
   one and is now the same size; at capability 0.30 the bad leg's stride is
   44cm shorter than the good one, which is a lot. `Gait.MaxAsymmetry`'s own
   comment says above about 0.5 it stops reading as injured and starts reading
   as broken animation. Nobody has looked at one yet.

10. **M22, THE SHAPE OF A PLAYTHROUGH** — the largest Core-shaped piece left.
   One sub-item is startable now: `PopulationSeed = 20260726` is hardcoded, a
   second seed gives 699 of 700 different people, and there is no new-game
   surface to choose one. **It must not be randomised** — CI determinism
   depends on it — so this is a surface, not a change to the default.

11. **THE LAW REACHES MANHUNT.** `inquiry=Manhunt homNamed=9
   homPressure=2.71 pressNamed=1 pressHeadline=[KILLING ON THE HOOK: POLICE
   NAME THE PUBLICAN]` — witnesses who can name you, pressure past
   `ManhuntAt`, the paper printing it, end to end. **Worth a look:**
   `homWouldTalk=3` of `homSaw=9`, two thirds of witnesses saying nothing to
   a detective — plausible and never checked against the design.

12. **THE REST OF WHAT `gates --constant` FOUND — a work list.** Sixty keys
   have never been anything but zero. Most are fault counters doing their job;
   these are not: **`threat` has only ever seen one outcome** (`brandishes=1` a
   run, so `called`/`complied`/`undraw` cannot be sampled); **`departed=0`**;
   **`carriedOut=0`**; **`groundless=False`**; **`summonsTaken=0`**, fixed and
   awaiting its own build. **PLANT the condition, never loosen the bound** —
   one or two at a time, or a red gate cannot be attributed.

## Next

- **Raise the population rather than cutting districts.** Measured, reversing
  the old plan: seven districts at 1,400 gives 43.5 distinct faces a week
  against 47.4 for three at 700, and 2,100 beats the cut outright. **And the
  empty street above may make this urgent rather than optional.**
- **Tier the cast.** 47 distinct faces a week, 13 near enough to read, a knee at
  ~50 covering 92% of a resident's week, 68 rigs at 1.1ms of 12ms. **The
  machine does not bound the cast at fifty; only authoring does.**
- **M17.2 voices** — no longer held on the writing verdict (78). A SPEND, not
  authorised.
- **Is fifty-six conversations a run too many?** A judgement off a still: 16-42
  under the old flat-road test, 7 after the pace slowed, 30-56 now it asks
  about junctions.

## Blocked, and on whom

- **Settled decisions now live in `design-doc.md` §18** — the era and its
  currency among them — so they are recorded once and not re-argued here.

- **CLOSED 18 Aug — a character mesh needed no purchase at all.** This entry
  said only Jafar could buy one; Mixamo bodies are a free download and the
  pool is FOURTEEN against 43 named people. Right about the gap, wrong about
  the price, for weeks.
- **API spend is quoted in FRANCS; the game's money stays £.** Jafar is in
  Switzerland. The £ in the design doc is a deliberate fiction decision — a
  British pub — and quoting both in one unit is how "a few pounds" reached him
  for a bill he pays in CHF. Two tasks authorised 3 Aug, both done; the writing
  probe re-run authorised 5 Aug. Nothing beyond that.

## How to keep this file honest

- **Dispatch, then immediately take item 1 of Now.** A build in flight is a
  reason to switch tasks, never a reason to stop.
- **Batch Game-layer changes**; the single Personal licence seat means one
  build at a time. **And prefer a local answer** — before dispatching, ask
  whether the question is actually about Unity. Item 1 above is not.

## Standing work

**This section never empties, and that is its entire job.** When `## Now` has
nothing startable, decompose one of these into it — running out of short items
is a refill signal, not a stop signal.

### THE FIVE THINGS THE DESIGN DOC DEFINES AND NOBODY HAD PLANNED (18 Aug)

Five, each placed in a milestone and startable without CI or Jafar's machine.
Full statements in `roadmap.md`; the account is in `design-doc.md` §18.

1. ~~**The session-hook guarantee** (M22)~~ — **BUILT AND HOLDING.** What is
   open is the READING, not the tiers — see `## Now`.
2. ~~**Romance** (M18)~~ — **PROMOTED TO M18.5, 18 Aug by Jafar.**
3. **Smuggling** (M21) — a port town whose Act III threat is Customs and
   Excise, with no smuggling to be caught at. Runs on the `Racket` substrate.
4. **The other day-job tracks** (M18) — `Core/DayJob` is the courier round,
   singular; the doc offers bar/courier/office on the first morning.
5. **Interiors beyond the pub** (M20) — every other door is a threshold.

**And one now unblocked:** reaction animation. `flinch`, `greet`, `wave`,
`glance`, `point` and `head_no` are on disk since 18 August and the perception
events they wire to already fire. Wiring, not sourcing.

### The quality ladder (standing order 16 Aug: best available, not first working)

Before closing any visible item, ask: best available result, or first working
one? Take the next rung or name it here. A blank next rung is a research task.

| aspect | rung now | known next rung, free |
|---|---|---|
| textures | 2K colour+normal landed; roughness wired on walls | ground roughness (SetWetness must drive _GlossMapScale); AO maps |
| buildings | procedural terraces, photo surfaces | window reveals/sills relief; per-district trim |
| vehicles | Kenney kit + town paints | curated higher-fidelity CC0 set (Quaternius/Sketchfab), same pipeline |
| props | Kenney kits, partial coverage | fill the miss list (benches!); higher-tier swaps |
| characters | Mixamo bodies, gait archetypes | Jafar's clip session; reaction anims (T3) |
| lighting | gradient sky, noir grade, wet streets | clouds (T4); noon shadows/AO; HDRP post-playtest |
| animation feel | walk/idle variants | flinch/greeting/turn-to-look wired to perception |
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
- **THE DROP PIPELINE.** Two of six windows miss in a typical run. The
  waypoint-collider cause is fixed; the second — steered the whole window,
  stalled seven metres out — has no explanation and `stalled=` lands next
  build. **Deliberately not loosened** (rule 6).
