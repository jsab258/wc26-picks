# The work stack

> **STATUS — LIVE**, verified 2026-08-04. What gets picked up next, in order.
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
  Done work is in the git log.
- **`## Standing work` never empties.** When `## Now` has nothing startable,
  decompose a standing item into it. Running out of short items is a refill
  signal, not a stop signal.

---

## Now

### WHAT `a050815` SETTLED — THREE CLOSED, ONE NARROWED TO A LINE

- **THE MOB IS A JAM. IT WAS NEVER THE SPREAD RING.** `huddleStanding=0
  huddleMoving=41` — every single body in the worst huddle was in transit and
  **not one was standing at its scheduled place.** So `SpreadRadius` could
  never have separated them at any radius, and the two builds spent widening
  it were aimed at a system that is not involved. `busiestNear` counts targets
  and `crowdHuddleWorst` counts bodies; reading them as one number is what
  sent both attempts.
  **The work is now routing**, not placement: bodies converging on the same
  path with nothing to make them file past each other. `crowdApartCapped=3291
  of 73902 calls` with `crowdApartWorst=0.84` says the separation nudge was
  being asked for eighty-four centimetres in a single frame before the cap
  landed, so the cap was doing real work and is not the answer either.

- **THE STREET IS NOT BENT DOUBLE — ONE BODY PER FRAME IS.** `leanTypical=-5.1`:
  the MIDDLE driven body leans five degrees BACKWARD. This file has led with
  "THE STREET WALKS BENT DOUBLE ... a MEDIAN, so it is the whole street" for
  four builds, off `leanDriven=36.4`, which is a median of per-frame MAXIMA.
  The number added to test that claim refutes it on its first run.
  **And it is the walk clip, not the run clip.** `leanWorstSpeed=1.14` — below
  the 1.4 m/s walk threshold, so the blend is idle-to-walk and "somebody was
  running" is out. `preLeanDriven=50.7` against `leanWorst=50.6` says the write
  still adds nothing. So: the bought walk leans hard at its worst, on one body
  at a time, and the rest of the street stands up straight.

- **NOBODY CAN TAKE THE PUB BECAUSE TWO ARE FEUDING AND ONE IS UNASSIGNED.**
  `successorWhy=Sam:feuding/c0.55l0.60,Rocco:feuding/c0.70l0.85,
  Joey:noAssignment/c0.65l0.70`. Competence and loyalty clear the bars in
  every case; the blocker is the feud flag and a missing assignment, which is
  a different fix from the one 137 runs of `handed=False` suggested.

- **CLOSED — A CAPITAL LETTER HAD SUPPRESSED THE LAW FOR THE WHOLE PROJECT.**
  `homWantKey=[player.killed_Hal]` against
  `homTopics=[...,player.killed_hal=true]`. `Killing.TopicKey` built its key
  by hand while `Fact`'s constructor lowercases, so every victim — all of
  whom have capitalised names — was stored under one key and looked up under
  another. `LiveWitnesses` returned nobody in every run ever kept, so
  `Pressure` had no named term, the inquiry could not pass Procedure, the
  paper never named the player, the redirect had nothing to relieve, and
  `CoatHost.Arrested` still has no caller anywhere. **All of it read as
  deliberate design and all of it was one missing `ToLowerInvariant`.**
  `TopicKey` is now the Fact's own key. Proven against real Core by probe
  (5 of 5 for `Hal`, `hal` and `O'Dea`) and guarded by a CoreTest tested
  both ways. **Expect `homNamed`, `homPressure` and `inquiry` to move next
  build — and check `actThree` and `ending` did not.**

- **CLOSED — THE NAME LABELS ARE THE RIGHT SIZE NOW.** `nameFracMedian=0.037`
  against the 0.038 the arithmetic predicted, where the previous 39 runs all
  read 0.060–0.072. Just under the bubble median, which is the order
  `NameTags.Pin` argues for and had inverted.

### What the earlier builds settled

Two blocks of per-build findings lived here and were cut on 5 August: this
file is what happens NEXT, and `docs-check` caps a live plan at 400 lines
for the reason the header already gives — done work is in the git log, and
the commit messages carry the reasoning in more detail than a summary of a
summary could. The block above is kept because its readings are still open.

### Startable right now, ORDERED BY WHAT SHOWS ON SCREEN

**The order is Jafar's, 4 August**: the top of this list is whatever a player
would notice, whatever state anything else is in.

1. **THE NAMEPLATE GATE STILL CANNOT SEE THE HEAP.** *(on screen)*

   `review_day5_night.jpg` has six people's names drawn on top of each other.
   `collidingNames=0` and `worstNamePair=[none]` are trivially true because
   `namesTracked=0` — the managed bucket is empty — while `worldTextTracked`
   is around a hundred. The size half of this is closed; the blindness is not.

   `namesManagedSeen=0 namesManagedCulled=0` says the cull is innocent, which
   by the fork means an id-space mismatch in `Manages`. **Do not conclude that
   yet:** `FindObjectsByType` skips inactive objects and a walker deactivates
   its label out of range, so "no walker label was present when the loop ran"
   is a third reading the fork did not have. `textPersonLabels` lands next
   build and separates them — zero means the loop and the still are looking at
   different moments, non-zero means the set is genuinely broken.
   **And this loop takes `Camera.main` under a doc comment saying it measures
   against the review camera** — the second site of the fault the size cap had.

1. **THE FRAME GATE IS THE ONLY LIVE RED, AND IT IS THE GAME'S OWN TIME.**

   `gates --flaky`: `frame` has failed 28 of 141 runs and is red on the newest.
   Everything else is quiet — `perf` last failed a run ago, nothing else in
   sixteen.

   **Read the breakdown, not the mean.** `mean=483.7ms` is a software
   rasteriser and says nothing; `game=17.55ms` against `gameBudget=12ms` is a
   46% overrun in OUR code and it is a real number on a real machine.
   `bodyLod=4.39 traffic=3.72 sun=3.15 npcs=2.77 rigs=2.06 population=1.32`.

   **`sun=3.15ms` is the odd one and is not an obvious loop** — `UpdateSun`
   has none, so it is Unity-side light or shadow work being triggered every
   frame by something that only changes each game-hour. That is a real
   investigation and a plausible 3ms, which is a quarter of the whole budget.
   The queue has been dismissing this item as "not worth touching while
   render+rest is 458ms", which confuses the runner's cost with ours.

1. **CLOSED — ALL FOUR OF THOSE FIXES HAVE BEEN READ.** The threats worked
   (`complied=1 called=1` after 136 zeros). The bubble ceiling fell 39% to 20%
   and the fix did NOT do it (`bubblesScreenLifted=2`, and `bubblesMade`
   halved) — though `bubblesNoBounds=0` closes the stated uncertainty: a
   TextMesh built this frame does have usable bounds. The pavement went the
   wrong way, `headingIntoRoad` 10 to 16, which is the corner exemption doing
   what it was told. The mob did not move and the reason is above.

1. **THE BUBBLE STACK'S SCREEN PASS HAS NEVER ONCE RUN.**

   `bubblesScreenLifted=0` on `2d5840f` and 2 on the build before, with
   `bubblesNoBounds=0` — so the stated uncertainty is closed (a TextMesh built
   this frame DOES have usable bounds) and the pass is simply inert.

   **Two reasons, both in `LiftClearOfScreen`.** It runs once, at the bubble's
   BIRTH, when nothing has drifted into it yet — overlap develops later as
   speakers and camera move, and a one-shot test at creation cannot see that.
   And the loop is gated `_lift < MaxLift`, so it is skipped entirely for the
   bubbles already at the ceiling, which are precisely the ones it was written
   for. `NameTags.PinAll` is the shape to copy: do it at the shot, against the
   camera that renders it.

   **BUT THE FAULT HAS RECEDED AND THE RATE IS WHY.** `bubblesAtCeiling` fell
   61/156 → 15/75 → 5/66, which is 39% → 20% → 7.6%, and `collidingBubbles`
   91 → 10 → 1. None of that is the fix, which never ran: `bubblesMade` fell
   with it, because bubbles follow confabs and `confabs` swings 29–74 in this
   regime. **Read the rate, not the count** — and it is a real fall even so.
   So this drops down the list: a pass that never runs is rule 6, but it is
   guarding a residue rather than two in five.

2. **CLOSED — NO SCARECROWS.** `armWidest=54.5` against `armCrowdWidest=53.5`,
   and off the real `Rig.ArmSwing` a normal walk puts the forearm at 45.4
   degrees at 1.2 m/s — so that is somebody walking briskly with a bent elbow
   and a T-pose is ninety. `animBodies=6 animDriven=6 animAdvancing=6`: nothing
   is frozen in a bind pose. What those frames showed was the mob.

3. **THE DWELL FIX TRADES A VISIBLE FAULT FOR AN INVISIBLE SAVING.**
   `bodySpell=5.41` median over 1,143 spells against a derivable 4.7s
   (`BandSlack`/`crowdSpeed`), and the perf split says `bodyLod=2.59ms` against
   `population=1.31ms` — the LOD pass costs twice the reband it was hiding
   inside, spending it on 1,157 prefab instantiates. **Decide against
   `gameShare`, not against milliseconds:** the frame gate reads
   `gameShare=3.43%` with `render+rest=458ms` on a software-rendering runner,
   so a 1ms saving is noise there and would be real on a player's machine.
   That is the whole difficulty and it is why this has not been done.

4. **CLOSED — THE NAMEPLATE CAP WAS APPLIED AGAINST THE WRONG CAMERA.**
   `nameShownWidthWorst=0.171` is the POST-cap width against a `PinFrac` of
   0.120 — a label that went through the clamp and came out forty per cent
   wider than the clamp allows. `Resolve` pins from `Camera.main` on the
   ordinary schedule while `SimDirector.Shot` moves a camera and renders by
   hand inside `Update`, so every label in a still was sized against last
   frame's camera. `NameTags.PinAll` re-pins at the shot, the third site of an
   idea `Billboard` and `SpeechBubble` already fixed. `namesPinnedAtShot` says
   whether it ran.

5. **CLOSED — THE SETBACK FIX WAS THE ADDRESSES, NOT THE BUILDINGS.**
   `placeStopsInRoad` 31 to 3 and `placeFacesInRoad` 22 to 3 on `8f6243f`, with
   corners then exempted so the residue is exactly the crossings and gates that
   belong in a right of way. Nothing about the block-inset rule had to change.

6. **THE FRAME GATE'S BIGGEST ITEM IS NOW TWO NUMBERS.** *(CI)* `population=
   4.08ms` covered a pass that runs every frame and one that runs once a
   second; read apart they are 1.31ms and 2.59ms. Neither is worth touching
   while `render+rest` is 458ms on a software runner — see item 3.

7. **CLOSED — THE TWO DROP MISSES ARE TWO FAULTS.** d12 never stopped and lost
   its target to a waypoint for eight of fifteen ticks; d13 held the target all
   nineteen, was never hurt, and stood dead still for thirteen of them.
   `stalledWith` counts who was standing on him at that instant and lands next
   build: the mob is the suspect, and a zero anywhere else means geometry.

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

   **The old text under this number said the law had NEVER asked, sixty for
   sixty.** True when written and false the moment the staging landed, which is
   comment decay in a document rather than in code. It stood for four builds
   because `gates --series inquiry` answered *"no landed run carries that
   name"* — the tool matched numbers only, so every categorical value in the
   verdict was unreadable and its refusal read as a spelling mistake. Fixed
   5 August; the series is what corrected this entry.

   **What is open now is the SECOND stage, and it is one number.** `homSaw=29
   homWouldTalk=7 homNamed=0`: twenty-nine people saw a killing, seven would
   talk to a detective, and not one can put a name to it — so `homPressure`
   sits at 0.40 and cannot reach `ManhuntAt`. `pressNamed=0` is still correct
   and still not a fault: `Press.Print` names you at
   `law >= Inquiry.Investigation` and the stage is one below it.
   `redirected=1 pointedAt=kest redirectRelief=0.00` is the same story — the
   redirect relieves a pressure that has not been built.

   **`homSawStored`/`homHoldsIt` are in flight and split it three ways:**
   stored=0 means the register never took the witness list, stored=29 with
   holds=0 means `FileWith` is not writing, and holds=29 with named=0 means the
   confidence bar. Different afternoons, one reading.

   **And `pointedAt=kest` in all 67 runs** — the redirect has never once
   pointed at anybody else. Staged, so probably honest, but it is the shape of
   a branch nobody has sampled and it belongs in item 12's list.

12. **THE REST OF WHAT `gates --constant` FOUND, AND IT IS A WORK LIST.**
   Sixty keys have never been anything but zero across 131 runs. Most are fault
   counters doing their job — `errors=0`, `idLeaks=0`, `blankLabels=0`,
   `panelsBad=0`, `offRoad=0`. These are the ones that are not:

   - **`threat` has only ever seen one outcome.** `brandishes=1` a run, so
     `called=0 complied=0 undraw=False` are three responses that CANNOT be
     sampled — one brandish can only produce one answer, and it has been
     `FleeScreaming` every time. Plant more than one, at people with different
     nerve, or the other three branches stay theoretical for ever.
   - **CLOSED — `contradiction=0.00` IS BY DESIGN AND THE BRANCH HAS RUN 46
     TIMES.** This entry said the contradicted half of `Informing` had never
     executed. `blowbackContradiction=0.90` and `denounceBlewBack=True` in
     every one of the 46 runs that carry them. The zero belongs to the FIRST
     denouncement, which is deliberately left uncontradicted so the probe
     cannot alter the outcome measured beside it — the reasoning is in
     `SimDirector` at the staging, and the reason is now in `EXPLAINED_ZEROS`
     so the tool stops offering it as work. **I was about to plant a condition
     that has been planted since June**, which is rule 3: when your own
     analysis says something is missing, open the file.
   - **`departed=0` ONLY — `adds` READS 10.** This entry said "she is
     recruited and never leaves and never brings anybody. Two branches, no
     runs." `companion[with=June recruited=1 departed=0 noted=3 exposure=3
     adds=10 carriedOut=0]`. `--constant` listed `departed` alone and was
     right; the prose here added `adds=0` on its own and was wrong for four
     builds. The live zeros are `departed` and `carriedOut`.
   - **`groundless=False`** — a carry has never been groundless.
   - **`summonsTaken=0` WAS NOT FIXED, AND THE ENTRY SAYING SO STOOD FOR FOUR
     BUILDS.** Nineteen runs carry the key and every one reads 0. The callbox
     flag was a real fix and it was not the last one: `SummonsHost.Nightly`
     runs at the day close — eight in the morning — and tested the player's
     LIVE position against lines live at hour 21, so the hour came from the
     ring and the position came from breakfast. `summonsMissWhy=[a line was
     live and he was not near it]` is a true sentence about the wrong moment
     and read twice as the mechanic working. Fixed 5 August by sampling
     `PlayerAtRing` in the once-per-game-hour branch. A third miss reason —
     "the ring hour never came round" — keeps the new case from reading as the
     old one. **The plant is deliberately NOT in the same build**, so a moving
     `summonsTaken` is attributable to this and nothing else.
   - **`reliabilityFiled` MOVED AND THEN CAME BACK, AND THAT IS HONEST.**
     The series is 0,1,1,2,1,1,1 then 0 newest — and `reliabilityRead` says
     why: `[Slipping after 2]` for five runs, `[Fine after 0]` in the newest.
     Zero drops were skipped in that run, so zero filed is correct. The plant
     works when the condition occurs and the condition is not guaranteed —
     rule 5b's corollary, and the fix is to make the skip deterministic rather
     than to read the zero as a regression.
     **`gates --series` could not read either of these until 5 August.** It
     matched numbers only, so `inquiry`, `ending`, `handed` and `pointedAt`
     all answered "no landed run carries that name"; the categorical fix then
     still could not read `[Fine after 0]`, because it excluded the bracket
     that CLAUDE.md names as the sanctioned form for a value with spaces. Two
     implementations of one idea, an hour apart, the second written without
     reading the first. It now uses `verdict-read.py`'s grammar verbatim.

   **The rule for every one of these is the same and it is rule 5b's
   corollary: PLANT the condition, never loosen the bound.** And do them one
   or two at a time — a build carrying five new staged behaviours cannot
   attribute a red gate to any of them.

## Next

- **Raise the population rather than cutting districts.** Measured and it
  reverses the old plan: seven districts at 1,400 people gives 43.5 distinct
  faces a week against 47.4 for three at 700, and 2,100 beats the cut outright.
  What is NOT measured is whether a fuller city still reads as a port rather
  than a crowd — a question for a still. Note `CrowdWalkerCap = 12` bounds how
  many are out of doors within earshot whatever the headcount is, so this buys
  FAMILIARITY and changes the frame not at all.
- **Tier the cast.** 47 distinct faces a week, 13 near enough to read, a knee at
  ~50 people covering 92% of a resident's week; 68 rigs cost 1.1ms of a 12ms
  budget. **The machine does not bound the cast at fifty; only authoring does.**
- **M17.2 voices** — no longer held on the writing verdict, which came back 78.
  Note this is a SPEND and Jafar has not authorised it.
- **Is fifty-six conversations a run too many?** A judgement off a still rather
  than a number. The history: 16-42 a run under the old flat-road test, 7 after
  the walking pace slowed, 30-56 now the test asks about junctions.

## Blocked, and on whom

- **THE MONEY DOES NOT MATCH THE DECADE, and it is a decision rather than a
  fault.** The cast deals in shillings, half a crown, pence and two-and-six —
  pre-decimal British currency, gone in 1971 — while `Tier2Gen` dates the world
  to the eighties and nineties by listing CDs, pagers and car phones as
  in-period. Seven references across the sixty cards, now counted by `--audit`
  and deliberately not rejected: refusing sixty cards over an unmade decision is
  the ratchet rule 5 warns about. Two ways out, both cheap, and it is Jafar's
  call: move the era back, or move the money forward. Worth noting the era is
  load-bearing rather than flavour — a late-analog city is what makes missed
  calls, wiretaps and being unreachable into mechanics.

- **A character mesh.** Only Jafar can buy one, and it is now the single
  largest immersion gap in the project — see roadmap 17.1b.
- **Any further API spend.** The 3 August authorisation covered two tasks, both
  done, ~£0.85. Nothing else is approved and nothing else gets spent.

## Done, kept here only until the next tidy

Cleared 5 August — the git log is the record.

## How to keep this file honest

- **Dispatch, then immediately take item 1 of Now.** A build in flight is a
  reason to switch tasks, never a reason to stop.
- **Arming a watcher is the PRECONDITION for ending a turn, not permission to
  end one.** Both are required and only one of them feels like progress.
- **Batch Game-layer changes, and dispatch hypotheses in parallel** — each build
  keeps its own verdict under `sim-shots/runs/<sha>.txt`, so concurrent builds
  are concurrent answers.
- **Prefer a local answer.** Before dispatching, ask whether the question is
  actually about Unity. Item 1 above is not.

## Standing work

**This section never empties, and that is its entire job.** The queue ran dry on
3 August after an hour of good work, because every item was sized to fit inside
one build round trip — so an hour of good work consumed the list, and an empty
list read as an empty afternoon. Three gaps of 21, 28 and 28 minutes followed.

When `## Now` has nothing startable in it, the next action is to take one of
these and decompose it into `## Now` — NOT to end the turn. Running out of short
items is a refill signal, not a stop signal.

- **M21, the two ledgers.** Empire growth, law as a tool, what expansion costs
  you. Entirely unbuilt, entirely Core, so entirely doable here without a round
  trip. This is the largest piece of unwritten game left.
- **M22, the shape of a playthrough.** Onboarding, pacing, replayability,
  succession. Also unbuilt and also Core-shaped.
- **Read a system and write down what it actually does.** Every system in this
  project has at least one comment that is now false; three were found today,
  one of them in the file being edited at the time. The supply is effectively
  unlimited and each one found is a bug that would otherwise have been believed.
- **Turn a still into a number.** Five faults have now been found by opening a
  frame and none by a gate — the newest being rumour text printed backwards
  across `day5_night` while three separate orientation metrics read perfect.
  Anything a frame shows that no metric names is a metric worth adding.

- **THE DROP PIPELINE, AND WHAT IS LEFT OF IT.** `jobRan` says `JobsDone >= 1`
  and means "a drop can be made end to end". Two of six windows miss in a
  typical run and both causes are now named: the first was the waypoint's own
  collider, thirty centimetres outside its completion radius, and it is fixed.
  The second — ten of sixteen metres covered, steered the whole window, stalled
  seven metres out — has no explanation, and `stalled=` lands next build to say
  whether he stopped or merely walked slowly. **Deliberately not loosened**:
  accepting a run that never exercised the pipeline is rule 6 exactly.
