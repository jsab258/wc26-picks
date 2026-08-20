# The work stack

> **STATUS — LIVE**, verified 2026-08-15. What gets picked up next, in order.
> The plan is `roadmap.md` and it wins; this is the next few hours of it.

## Why this file exists, and how to use it

The moment after a dispatch is a decision point, and a decision point at the
end of a long turn is where turns end. On 3 August that cost four gaps of
twenty to thirty minutes with nothing landing. So the next items are written
down BEFORE the dispatch and taken from the top afterwards, with no judgement
required at the exact point where judgement was failing. The full account is in
CLAUDE.md under AUTO MODE.

- **Every item fits inside one build round trip (~28 min)**, or it gets split,
  or it will be abandoned half-done when the build lands.
- **CI-needed items are marked.** They are batched into the next dispatch and
  are never a reason to stop working.
- **Take from the top. Move finished items out** — this records what is NEXT.
  Done work is in the git log, and `roadmap-history.md` holds the cut blocks;
  `docs-check` caps a live plan at 400 lines, which is what forces the tidy.
- **`## Standing work` never empties.** When `## Now` has nothing startable,
  decompose a standing item into it. Running out of short items is a refill
  signal, not a stop signal.

---

## Now

### Where the street got to

The Mixamo harvest landed complete — 67 clips, no duplicates — and the street
came alive with it: people talk, argue, lean, smoke, work counters, carry
shopping. **But twenty-one of the 67 play the wrong motion — item 1.**
Accounts in `roadmap-history.md`. NEXT: T3 queue points and standing
destinations.

### THE PLAYTEST — DEPRIORITISED 18 Aug, by Jafar

*"Don't worry about timelines or the near goal or play testing. Just keep
building."* `playtest-plan.md` stays live as the Mac setup record and resumes
when he asks. Live speech stays parked — no DirectML on the Air. The glowing
box in day2_night's plaza is the bar sign's bare back face, one line.

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
   its name and tries the next; where the catalogue has only the one name the
   slot reports MISSING. **Holes are the right outcome and they are the
   information** — a slot unfillable from a 2,846-name harvest says the
   harvest needs redoing, not re-picking. **Not caught, and said so:** `sit`
   renders standing at 96cm and the three sitting clips read 18, 94 and 96,
   so there is no correct example to set a band from. Account in
   `clip-findings.txt`.

1. **THE STILLS NO LONGER PHOTOGRAPH WALLS, AND THE METRIC IS STILL TOO
   NARROW.** *(rule 12)* The camera steps back off anything filling more than
   a quarter of the frame at arm's length, bound from a measured bimodal
   series, exercised on a real 0.83 case. Account in `roadmap-history.md`.
   **What is left:** two metres cannot see `review_day5_noon` — slabs across
   the middle at about ten metres, visibly blocked and numerically clear.
   **The next number is a median ray distance, not a wider bound.**

1. **THE LAW TIER WAS OFF FOR THE WHOLE RUN, AND THE DENOMINATOR CAUGHT IT.**
   `looseEnds=6/0/[Owed:6]/open6/1of6` — one tier live on each of six evenings
   — beside `inquiry=Manhunt pressNamed=1 homNamed=9`. The tier asked whether
   anybody ELSE was named, and NOTHING EVER CLEARS THAT NAME: only the relief
   expires, so one successful redirect ever closed it for the rest of the run.
   Reads the live relief now, tested both ways off the real book. **Landed:**
   `[Law:1,Owed:5]/open7/2of6`. **Crew still never opens** (`crew=2`, nobody
   below the poach floor) — the next one to chase.

1. **THE RAIN READS AS BLACK SCRATCHES AT EYE LEVEL.** *(player-height frame,
   dfefd62)* Fine from the elevated camera, dense dark striation from the
   player's eyes, likely sized for a downward view. **Every run since has come
   back dry, so this needs a WET run rather than another look.** The magenta
   half of that report is REFUTED.

1. **THE BODY BUDGET IS CLOSED AT 87.8% — account in `roadmap-history.md`.**
   Three things stay live:

   **The band, not the budget.** 13.1 walkers in frame per pass, only 6.5
   inside the 34m band — half the people you can see can never be skinned.
   Belongs with the population item.

   **The white pills are unidentified and NO COMMITTED STILL HAS ONE.**
   Measured: the pale figures in `review_street.jpg` read `#5d626f` and
   `#66676a` against buildings at `#7f838f` — darker than the walls — and
   that frame's brightest 1% is entirely the harbour. I called them white off
   the picture before measuring, the sixth wrong identification; `bodyAlbedo`
   naming them was wrong too, it measures source TEXTURES. **Next step is a
   measurement that fires WHILE one is on screen.** The T-pose in that frame
   is real and separate — `armStreet`'s tail, which a median cannot see.

   **`bodyWashUnreached=534` against `bodyTinted=1326`, and nobody has
   looked.** 40% of bodies render DARKER than the band because their sheet is
   darker and a multiply only subtracts. Not a bug — a limit on how much
   palette reaches the street. **And `RealBodyCap = 12` needs a PC
   measurement**, not a CI one: its comment prices a dozen skinned bodies
   against a runner with no GPU at all.

1. **NO BUS AND NO BICYCLE EXIST IN THE KIT — the remaining primitives.**
   `vehicleFellBack=[bus,bike x6]`. All 50 car-kit models ARE extracted and
   neither is among them, so this is a sourcing gap and the fix is another
   CC0 kit, not more code. One bicycle model closes almost all of it.
   (The police car is in and `vehiclesKitted` went 18/28 to 21/28 — account
   in `roadmap-history.md`.)

1. **PATROL DENSITY FOLLOWS THE INQUIRY — and the measurement of whether it
   READS is still not finished.** Weight by stage (None 1 ... Manhunt 5),
   converted only on parked cars, routed to a beat in the player's district,
   stood down when the inquiry clears. Every link fires. Account and the four
   wrong theories in `roadmap-history.md`.

   **What is open:** `patrolOnBeatMean=0.00` over 3 shots against `0.18` over
   17 — zero of three separates nothing. The `hunt_` pair now photographs the
   manhunt, so the next build has frames to judge from. **Still unread:** six
   cars that never stop are six brief crossings; a patrol PARKED with its
   beacon lit stays in frame. A feature, not a knob.

1. **THE VERDICT STEP IS 400 CHARS OFF A HARD CEILING AND FAILS AT DISPATCH,
   NOT AT COMMIT.** *(CI)* Adding one paragraph took it 815 over the largest
   step that has ever dispatched; `workflow-size` caught it and four rounds of
   trimming prose bought it back. A 422 at dispatch means NO Windows build at
   all. **The real fix is extraction**, as `sim-shots-stage.sh` already
   proves: move the step body to a script file and the YAML stops being the
   constraint. Until then every comment added there is a coin flip.

1. **THE FIRST MANHUNT FRAME IS BAD, AND IT IS THE FIRST ONE ANYONE HAS
   SEEN.** *(on screen)* `hunt_day13_noon`: fifteen people packed shoulder to
   shoulder in the road, a dozen NAMEPLATES stacked in an overlapping heap,
   and a giant red `... you ...` caption across a building face.

   **`collidingNames=0` on the same run** — the counter says no nameplates
   overlap and the picture shows a heap. A zero against a frame that
   contradicts it, now with the picture in hand. **Two visual reads of mine
   were wrong and measured so before publishing:** a "magenta cluster" (zero
   magenta pixels in the frame, so no error shader) and a "pink object" (the
   only pinkish blocks are the stop sign and the caption).

1. **THE DISTRICT TOUR LANDED, AND THE OUTER DISTRICTS LOOK UNBUILT — BUT
   THAT IS A HYPOTHESIS, NOT A MEASUREMENT.** *(on screen)* Seven frames now
   exist, `district_*.jpg`, the first pictures ever taken of six of them.
   `district_downtown` and `district_fairview` read as a road with four cars
   on a vast empty grey plain, under a distant skyline of pale towers well
   outside the noir palette. The Hook, beside them, has terraces, signs,
   props and people.

   **A pixel statistic over those frames CANNOT tell them apart** — block
   spread 37-44 and flat ground 5-8% in all seven, because textured ground
   varies as much as a street does. I chose a metric blind to the question,
   which is why the claim above is still marked as an impression.

   **So the count comes from the builder.** `parcelsByDistrict=[...]` ships
   next build, incremented where the parcel is placed. **Read it against the
   pictures**: if the Exchange really has a tenth of the Hook's parcels the
   frames are honest and the districts need building out; if the counts are
   comparable, the fault is in what a parcel LOOKS like out there, which is a
   different job entirely.

1. **THE VERDICT STEP IS 400 CHARS OFF A HARD CEILING AND FAILS AT DISPATCH,
   NOT AT COMMIT.** *(CI)* Adding one paragraph took it 815 over the largest
   step that has ever dispatched; `workflow-size` caught it and four rounds of
   trimming prose bought it back. A 422 at dispatch means NO Windows build at
   all. **The real fix is extraction**, as `sim-shots-stage.sh` already
   proves: move the step body to a script file and the YAML stops being the
   constraint. Until then every comment added there is a coin flip.

1. **THE FIRST MANHUNT FRAME IS BAD, AND IT IS THE FIRST ONE ANYONE HAS
   SEEN.** *(on screen)* `hunt_day13_noon` shows three things at once:
   about fifteen people packed shoulder to shoulder in the road, a dozen
   NAMEPLATES stacked in an overlapping heap, and a giant red `... you ...`
   caption across a building face.

   **`collidingNames=0` on the same run.** The counter says no nameplates
   overlap; the picture shows a heap of them. A number reading zero against a
   frame that contradicts it — the exact class this project keeps finding,
   and now with the picture in hand to work from.

   **Two visual reads of mine were WRONG and measured so before publishing:**
   a "magenta cluster" (zero magenta-ish pixels in the whole frame, so no
   error shader) and a "pink object" in the crowd (the only pinkish blocks
   are the stop sign and the caption text). Rule 4's second half, twice in
   one frame.

1. **A DISTRICT TOUR NOW PHOTOGRAPHS ALL SEVEN — awaiting its first build.**
   `shotDistricts=[the_Hook:20]` said all twenty shots of every run were in
   one district; Copper Row, Ironside, the Exchange, the Parade, Fairview and
   Gullwing had never been photographed at all, having been the largest world
   change in weeks. Seven frames once a run, day 3 noon, elevated and aimed
   along each district's middle avenue — the day stills' composition, so they
   are comparable with them.

   **Deliberately outside every statistic.** The tour teleports the camera to
   seven arbitrary crossings, which is right for looking at districts and
   wrong for the patrol means, the shot-district histogram and the
   blocked-frame series — all of which describe where the GAME put the
   camera. Folding seven teleports in would be a regime change inside one
   run, which is the fault that cost the patrol work three builds.

   **All three staging sites taught the prefix this time** — the workflow
   copy glob, `sim-shots-stage.sh` and `report-frame.py`. Missing one of them
   is how the `hunt_` pair came back rendered and never committed.

   **Noted, not chased:** `vehiclesKitted=26/33` where the fleet is 28.
   `VehiclesBodied` counts bodies BUILT and rebalancing rebuilds them, so the
   denominator stopped meaning "vehicles in the world". Ratio honest, name
   not.

1. **THE FRAME GATE IS RED AND THE COST HAS MOVED — this item was two regime
   changes stale.** **Read the breakdown, not the mean**: `mean=666.4ms` is a
   software rasteriser and says nothing; `game=24.53ms` against a 12ms budget
   is a 104% overrun in OUR code.

   Current: `npcs=9.48 bodyLod=4.68 mix=3.75 traffic=2.51 sun=1.27
   population=1.40 rigs=1.25`. **`npcs` is now the dominant cost** and this
   item used to say `npcs=2.77` with bodyLod on top — the series says npcs has
   tripled (~2.3-3.3 → ~4.4 → ~8.6-9.5 across three regimes) while `game` went
   14→18→24ms. Start there, not at bodyLod.

   **`sun` is settled and the old paragraph here was wrong.** It read 3.15ms
   because the whole audio mix ran inside the sun's timer; `mix` was split out
   of it and `sun` is 1.27ms now, with the landed series confirming the step.
   Nothing to chase.

   bodyLod is a once-a-second FULL pass, so spreading it round-robin needs the
   measurement split from the sweep first or every count becomes a peak over
   partial passes. Tune on the PC, not CI.

1. **THE BUBBLE STACK'S SCREEN PASS BARELY RUNS.** `bubblesScreenLifted=1` of
   `bubblesMade=54` with `bubblesAtCeiling=16`. Two reasons, both in
   `LiftClearOfScreen`: it runs once at the bubble's BIRTH, before anything
   has drifted into it, and the loop is gated `_lift < MaxLift` so it skips
   exactly the bubbles at the ceiling it was written for. `NameTags.PinAll`
   is the shape to copy — do it at the shot, against the camera that renders
   it. **The recession claimed here before ("7.6% at ceiling") does not hold
   on `e6634a1`: 16 of 54 is 30%.**

3. **THE DWELL FIX TRADES A VISIBLE FAULT FOR AN INVISIBLE SAVING.**
   `bodyLodMs=4.68` against `populationMs=1.40` — the LOD pass costs three
   times the reband it hides inside. **Decide against `gameShare`, not
   milliseconds:** at `render+rest=641.83ms` on a software runner a few ms is
   noise here and real on a player's machine, which is why this is undone.

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
   have never been anything but zero. Most are fault counters doing their
   job; these are not: **`threat` has only ever seen one outcome**
   (`brandishes=1` a run, so `called`/`complied`/`undraw` cannot be sampled —
   plant several, at people with different nerve); **`departed=0` and
   `carriedOut=0`**; **`groundless=False`** — a carry has never been
   groundless; **`summonsTaken=0`**, fixed and awaiting its own build, with
   the plant deliberately NOT in the same build so a moving number is
   attributable.

   **The rule for all of them is rule 5b's corollary: PLANT the condition,
   never loosen the bound.** One or two at a time — a build carrying five new
   staged behaviours cannot attribute a red gate to any of them.

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
  reason to switch tasks, never a reason to stop. **Arming a watcher is the
  PRECONDITION for ending a turn, not permission to end one** — both are
  required and only one of them feels like progress.
- **Batch Game-layer changes**; each build keeps its own verdict under
  `sim-shots/runs/<sha>.txt`, but the single Personal licence seat means one
  build at a time. **And prefer a local answer** — before dispatching, ask
  whether the question is actually about Unity. Item 1 above is not.

## Standing work

**This section never empties, and that is its entire job.** The queue ran dry
on 3 August because every item was sized to fit one build round trip, so an
hour of good work consumed the list and an empty list read as an empty
afternoon. When `## Now` has nothing startable, decompose one of these into it
— running out of short items is a refill signal, not a stop signal.

### THE FIVE THINGS THE DESIGN DOC DEFINES AND NOBODY HAD PLANNED (18 Aug)

Jafar asked for the design doc to be checked for anything defined and never
planned. Five, each now placed in a milestone and each startable without CI or
his machine. Full statements in `roadmap.md`; `design-doc.md` §18 has the
account and the denominator of what was checked and found sound.

1. ~~**The session-hook guarantee** (M22)~~ — **BUILT AND HOLDING.**
   `looseEnds=6/0/[Owed:6]`: six evenings closed, none empty, so the guarantee
   is real. What is open is the READING, not the tiers — see `## Now`.
2. ~~**Romance** (M18)~~ — **PROMOTED TO ITS OWN MILESTONE, M18.5, 18 Aug by
   Jafar.** Statement, done-when and risk are in `roadmap.md`.
3. **Smuggling** (M21) — a port town whose Act III threat is Customs and Excise,
   with no smuggling to be caught at. Runs on the `Racket` substrate the other
   three use.
4. **The other day-job tracks** (M18) — `Core/DayJob` is the courier round,
   singular; the doc offers bar/courier/office on the first morning.
5. **Interiors beyond the pub** (M20) — every other door is a threshold.

**And one now unblocked:** reaction animation (flinch, greet, turn-to-look) read
"blocked on the Mixamo clip session" for weeks. That session ran on 18 August;
`flinch`, `greet`, `wave`, `glance`, `point` and `head_no` are on disk and the
perception events they wire to already fire. Wiring, not sourcing.

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
  at least one comment that is now false — three found in one day, one in the
  file being edited at the time. The supply is unlimited and each one found is
  a bug that would otherwise have been believed.
- **Turn a still into a number.** Five faults found by opening a frame and none
  by a gate — the newest, rumour text printed backwards across `day5_night`
  while three orientation metrics read perfect. Anything a frame shows that no
  metric names is a metric worth adding.

- **THE DROP PIPELINE, AND WHAT IS LEFT OF IT.** Two of six windows miss in a
  typical run. The first cause was the waypoint's own collider sitting thirty
  centimetres outside its completion radius, now fixed; the second — steered
  the whole window, stalled seven metres out — has no explanation and
  `stalled=` lands next build. **Deliberately not loosened**: accepting a run
  that never exercised the pipeline is rule 6 exactly.
