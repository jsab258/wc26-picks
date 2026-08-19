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
shopping. **But three of the 67 play the wrong motion — see item 1.** Accounts
in `roadmap-history.md`. NEXT: T3 queue points and standing destinations.

### THE PLAYTEST — DEPRIORITISED 18 Aug, by Jafar

*"Don't worry about timelines or the near goal or play testing. Just keep
building."* `playtest-plan.md` stays live as the Mac setup record and its
sequence resumes when he asks. Both items this section waited on are closed
(the Mixamo session ran; the per-physique controllers exist). Live speech
stays parked — no DirectML on the Air. The glowing box in day2_night's plaza
is the bar sign's bare back face, one line, low priority.

### Startable right now, ORDERED BY WHAT SHOWS ON SCREEN

1. **TEN ANIMATIONS ARE THE WRONG ANIMATION — ANSWERED, and the fix is a
   RE-PICK, not a re-download.** *(on screen; the pick runs on Jafar's
   machine in seconds)* The exposure fix landed (`sheetDark` 25 -> 0) so all
   67 were read at once. **Five are confirmed on two instruments** — the
   render and the hips' height in the FBX: `jog` is a body flat on the floor
   at 7cm and `lie_still` an upright stride at 96cm, so **they are each
   other**; `collapse` ("Dying") never leaves 103cm; `sit` and `sit_talk`
   stand. **Five more are suspected on the picture alone** — `carry_bag`,
   `idle_bored`, `head_no`, `walk_stop`, `thinking` — and height CANNOT close
   them, because `run` at 74 and `block_broken` at 74 are correct and sit in
   the same band. Controls: `walk` 95, `idle` 100, `get_up` 8 (prone, right),
   `knockdown` 6..104.

   **The picker is NOT at fault**: every file carries the right Mixamo title
   and the dryrun is 65 exact / 2 substitute / 0 missing, so the mismatch is
   between a harvest file's NAME and its CONTENTS, upstream of this repo.

   **NEXT, and it needs no Windows machine to write:** make the picker VERIFY
   a candidate's posture rather than trust its name. The full harvest is
   already on his disk, so REPICK.bat then finds replacements in seconds with
   no token and no downloads.
   **Rule 5b applies hard here, twice:** the check must ACCEPT `get_up` at
   8cm and `knockdown` at 6..104, and it must not police the crouch band at
   all — the only bound the distribution supports is the empty gap from 18 to
   60, floor against upright.
   Full account in `clip-findings.txt`.

1. **`clip-motion.py`'s travel/path columns are not trustworthy.** *(local)*
   Two walks reading 0.00 and 1.22, a standing reaction at 3.1 m/s. Nothing
   reads them and the findings `clipFindings` counts do not depend on them;
   the new `hip cm` column IS sound for the one question it answers.

1. **`looseEnds=6/0/[Owed:6]` IS NOT THE FAULT IT LOOKS LIKE, and the
   reading needs fixing rather than the code.** Six evenings, none empty,
   every one naming the Owed tier — which reads as "five of six tiers are
   dead". They are not: `Tonight` checks tiers in priority order and
   RETURNS on the first hit, and Mickey's book always has somebody
   outstanding, so Promise, Rumour and Standing cannot fire while a debt
   is open no matter how well they are fed. Feeding them would change
   nothing visible, which is why this is not "wire the other three".
   **What is missing is the denominator** (rule 3b): the tally should say
   how many threads were OPEN that evening, not only which one won, so
   "one tier outranked the rest" stops looking like "one tier exists".
   Law and Crew sitting silent above Owed is the part actually worth
   checking — the inquiry naming the player was dead for the whole project
   until 5 Aug.

1. **THE RAIN READS AS BLACK SCRATCHES AT EYE LEVEL — RECOVERED, NOT
   RESOLVED.** *(player-height frame, dfefd62)* Fine from the elevated
   camera, dense dark striation from the player's eyes — likely sized
   for a downward view. **Cannot be judged on any frame since; every
   run has come back dry.** Needs a wet run, not another look. The
   magenta half of that report is REFUTED (zero magenta pixels, 7.63
   heads) and is named so it cannot resurrect.

1. **THE STREET IS EMPTY AT EYE LEVEL, AND EVERY POPULATION NUMBER
   SAYS IT IS FINE.** *(on screen — `review_street.jpg`)* Not one
   existing number is about the VIEW: `walkers=55` counts bodies
   anywhere in a city that grew ~2.5x in area, `crowdWalkers=12` is
   exactly `CrowdWalkerCap` so the near cap BINDS, and `crowdMill=136`
   is the GOSSIP mill — social agents, not a render tier. There is no
   cheap visible-body tier at all.

   **MEASURED, FOUR RUNS: 5/2, 8/5, 3/2, 19/7** in shot / skinned of ~52
   alive — the spread is the shot standing somewhere different, not
   progress. **THE BODY BUDGET WENT TO WHOEVER WAS NEAREST, NOT TO
   WHOEVER YOU WERE LOOKING AT**: bodies a metre from the lens and out of
   frame beat the people in shot at 10-25m to all 12 grants.

   **A FORWARD BIAS IS IN, AWAITING ITS FIRST BUILD.** The rank is
   distance scaled by facing — directly behind counts as ~1.41x further,
   abreast ~1.22x, ahead unchanged — gentle and continuous rather than a
   cone, because you can turn round and a hard test would swap the whole
   set on a spin. The BAND test still reads true distance, so nobody
   across the district gets a body for facing the right way. **The
   strength (1.0) is a starting value and is NOT measured**, which is
   stated in the code rather than hidden: `bodyLodInShot` against
   `bodyLodShotEligible` is what will judge it, and no such number existed
   until now. Raise it if bodies still go behind the camera; lower it if
   `bodyGrants` climbs, which is turning costing prefab instantiates.

   **THE WHITE PILLS ARE STILL UNIDENTIFIED**, and the claim that
   `bodyAlbedo` named them was wrong — it measures skinned Mixamo
   TEXTURES. Fifth wrong identification, first one published; it arrived
   as a NUMBER and a number felt pre-checked. Intermittent. Next step is
   a number that fires WHILE one is on screen. **"The cast is too bright
   for the palette" is retracted for the same reason** — the third wrong
   reading of that key: `RealBody.Tint` washes every body, anchored per
   material, and `bodyAlbedo` reads the SOURCE sheet before the wash.

   **The honest residue is the opposite number and nobody has looked at
   it: `bodyWashUnreached=534` against `bodyTinted=1326`** — 40% of bodies
   render DARKER than the band, because their sheet is darker and a
   multiply only subtracts. Not a bug in the wash, but a real limit on how
   much of the palette reaches the street, and the number to judge from a
   frame.

   **Two instrument fixes here, both closed:** `bodyLiftedCrowd` counts
   crowd bodies correctly NOT lifted, and its comment claimed the
   opposite — true before the `cast` flag landed, false after; the name
   is kept because the key has a landed series. And the capsule audit used
   to run before any walker spawned, so its zeros meant "none when built";
   it re-runs at the done line now, still 0/0 but carrying information.

   **PERF, SETTLED AND RETIRED THIS ROUND** — traffic halved, the
   separation sweep priced at 0.8ms of a 12ms budget so the rewrite is
   not worth it, `sun` shown to be noise. Account in `roadmap-history.md`.

   **`RealBodyCap = 12` NEEDS A PC MEASUREMENT, not a CI one** — its
   comment prices a dozen skinned bodies against a runner with no GPU
   at all. Plausibly the cheapest large win for how full the street
   looks.

1. **THE KIT BUILDINGS ARE NOT TERRACES — SETTLED ON GEOMETRY**, and the
   low-detail set at a 1:4 tower ratio became the skyline. Table in
   `roadmap-history.md`.

1. **NO BUS AND NO BICYCLE EXIST IN THE KIT — 10 of 28 vehicles are
   still primitives.** `vehiclesKitted=18/28`,
   `vehicleFellBack=[bus,bike x9]` on its first run. Checked: all 50
   models in the car-kit listing ARE extracted, and neither a bus nor
   a bicycle is among them. So this is a sourcing gap, not a bug, and
   the fix is another CC0 kit — not more code. Bikes are nine of the
   ten, so one bicycle model closes almost all of it.

   Also unused and already on disk: `police`, `ambulance`, `firetruck`,
   `garbage-truck`. A police car has obvious business in this game and
   costs one line of `KitCandidates` once there is a kind for it.

1. **THE FRAME GATE IS THE ONLY LIVE RED, AND IT IS THE GAME'S OWN TIME.**
   **Read the breakdown, not the mean** — `mean=483.7ms` is a software
   rasteriser and says nothing; `game=17.55ms` against a 12ms budget is a 46%
   overrun in OUR code. `bodyLod=4.39 traffic=3.72 sun=3.15 npcs=2.77`.
   `frame` has failed 28 of 141 runs. bodyLod is a once-a-second FULL pass, so
   spreading it round-robin needs the measurement split from the sweep first
   or every count becomes a peak over partial passes. Tune on the PC, not CI.

   **`sun=3.15ms` is the odd one and is not an obvious loop** — `UpdateSun`
   has none, so it is Unity-side light or shadow work retriggered every frame
   by something that changes each game-hour. A plausible 3ms, a quarter of the
   budget, and dismissing it as "not worth touching while render+rest is 458ms"
   confuses the runner's cost with ours.

1. **THE BUBBLE STACK'S SCREEN PASS HAS NEVER ONCE RUN.**

   `bubblesScreenLifted=0` on `2d5840f` and 2 on the build before, with
   `bubblesNoBounds=0` — so the stated uncertainty is closed (a TextMesh built
   this frame DOES have usable bounds) and the pass is simply inert.

   **Two reasons, both in `LiftClearOfScreen`**: it runs once at the bubble's
   BIRTH, before anything has drifted into it, and the loop is gated
   `_lift < MaxLift` so it skips exactly the bubbles at the ceiling it was
   written for. `NameTags.PinAll` is the shape to copy — do it at the shot,
   against the camera that renders it. **BUT THE FAULT HAS RECEDED**:
   `bubblesAtCeiling` 39% -> 20% -> 7.6%, a real fall in the RATE and none of
   it this fix, which never ran. So it guards a residue rather than two in
   five, and drops down the list.

3. **THE DWELL FIX TRADES A VISIBLE FAULT FOR AN INVISIBLE SAVING.**
   `bodyLod=2.59ms` against `population=1.31ms` — the LOD pass costs twice the
   reband it hides inside, on 1,157 prefab instantiates. **Decide against
   `gameShare`, not milliseconds:** at `render+rest=458ms` on a software
   runner a 1ms saving is noise here and real on a player's machine, which is
   why this has not been done.

6. **THE FRAME GATE'S BIGGEST ITEM IS NOW TWO NUMBERS.** *(CI)* `population=
   4.08ms` covered a pass that runs every frame and one that runs once a
   second; read apart they are 1.31ms and 2.59ms. Neither is worth touching
   while `render+rest` is 458ms on a software runner — see item 3.

8. **KEEP RETIRING THE REACH LEDGER — 35 entries**, `StreetMap.OnStreet` off it
   tonight because the place-setback question needed exactly the wider
   containment test the entry said it was waiting for. **AND READ THE ENTRY'S
   REASON, NOT JUST ITS NAME**: two were wrong this morning, and the two
   sampled tonight (`Combat.Breathe`, `VoiceBank.PoolVoices`) were both honest.

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

11. **THE LAW NOW ASKS, AND IT STOPS AT THE FIRST STAGE.**
   `inquiry` reads **Procedure** in the four newest runs and **None** in the
   sixty-three before them, changing exactly once, at `0720f52`. That is the
   `AuditClosed` staging landing and holding — not a lucky run — and it is the
   first movement in the whole recorded history of the key.

   **The old text here said the law had NEVER asked, sixty for sixty** — true
   when written, false once the staging landed, and it stood four builds
   because `gates --series inquiry` matched numbers only, so a categorical
   value read as a spelling mistake. Fixed 5 Aug; the series corrected it.

   **What is open now is the SECOND stage, and it is one number.** `homSaw=29
   homWouldTalk=7 homNamed=0`: twenty-nine people saw a killing, seven would
   talk to a detective, and not one can put a name to it — so `homPressure`
   sits at 0.40 and cannot reach `ManhuntAt`. `pressNamed=0` is still correct
   and still not a fault: `Press.Print` names you at
   `law >= Inquiry.Investigation` and the stage is one below it.
   `redirected=1 pointedAt=kest redirectRelief=0.00` is the same story — the
   redirect relieves a pressure that has not been built.

   **`homSawStored`/`homHoldsIt` are in flight and split it three ways** —
   the register never took the list, `FileWith` is not writing, or the
   confidence bar. Different afternoons, one reading. **And `pointedAt=kest`
   in all 67 runs**: staged, so probably honest, but a branch nobody has
   sampled, and it belongs in item 12's list.

12. **THE REST OF WHAT `gates --constant` FOUND, AND IT IS A WORK LIST.**
   Sixty keys have never been anything but zero across 131 runs. Most are fault
   counters doing their job — `errors=0`, `idLeaks=0`, `blankLabels=0`,
   `panelsBad=0`, `offRoad=0`. These are the ones that are not:

   - **`threat` has only ever seen one outcome.** `brandishes=1` a run, so
     `called=0 complied=0 undraw=False` CANNOT be sampled — one brandish gives
     one answer, `FleeScreaming` every time. Plant several, at people with
     different nerve.
   - **`departed=0` and `carriedOut=0` are the live zeros**; `adds` reads 10,
     and this entry claimed otherwise for four builds off prose.
   - **`groundless=False`** — a carry has never been groundless.
   - **`summonsTaken=0` — fixed 5 August, awaiting its own build.** The nightly
     pass sampled the player's position at breakfast against lines live at hour
     21; now sampled at the ring hour. **The plant is deliberately NOT in the
     same build**, so a moving `summonsTaken` is attributable to this alone.

   **The rule for every one of these is the same and it is rule 5b's
   corollary: PLANT the condition, never loosen the bound.** And do them one
   or two at a time — a build carrying five new staged behaviours cannot
   attribute a red gate to any of them.

## Next

- **Raise the population rather than cutting districts.** Measured, and it
  reverses the old plan: seven districts at 1,400 gives 43.5 distinct faces a
  week against 47.4 for three at 700, and 2,100 beats the cut outright.
  `CrowdWalkerCap = 12` bounds earshot whatever the headcount, so this buys
  FAMILIARITY and changes the frame not at all.
- **Tier the cast.** 47 distinct faces a week, 13 near enough to read, a knee at
  ~50 covering 92% of a resident's week, and 68 rigs cost 1.1ms of 12ms. **The
  machine does not bound the cast at fifty; only authoring does.**
- **M17.2 voices** — no longer held on the writing verdict (78). A SPEND, not
  authorised.
- **Is fifty-six conversations a run too many?** A judgement off a still: 16-42
  under the old flat-road test, 7 after the pace slowed, 30-56 now it asks
  about junctions.

## Blocked, and on whom

- **SETTLED 18 Aug, by Jafar, and NOT TO BE ASKED AGAIN: the era is LATE
  1980s / EARLY 1990s, and the currency follows.** Money moved FORWARD to
  decimal and the pre-decimal card references were the thing that changed,
  not the decade — decimalisation was 1971, so those words were twenty years
  stale in this world. The era was already right in `design-doc.md` and in
  `Tier2Gen`'s CDs and pagers; only the card writing drifted. Load-bearing
  rather than flavour: a late-analog city is what turns missed calls and
  being unreachable into mechanics. Recorded as a DECISION so nobody
  re-opens it — Jafar has answered it more than once.

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
