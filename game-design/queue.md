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

### WHAT THE LAST THREE BUILDS SETTLED

- **The summons is fixed and its zero is now honest.** `summonsMissWhy` went
  from "no line was live at that hour" to **"a line was live and he was not
  near it"** — the exact distinction that code was built to draw, and its own
  comment says the first is a world that never offered the choice while the
  second is the mechanic working. `summonsTaken=0` still, but for a reason a
  player could have changed.
- **The reliability rule fired for the first time in 132 runs.**
  `dropsSkipped=2 reliabilityFiled=1 reliabilityRead=[Slipping after 3]`. The
  street now says the publican is slipping. Planting the condition worked and
  the bound was never touched.
- **The two-axis name cap is IN and UNDEMONSTRATED.** `nameWidthWorst=0.171`
  and `nameShownWidthWorst=0.171` — identical, because no label this run was
  wide enough to clamp. The 0.431 case from the run before would have been.
  **Not a confirmation: a quiet run.**
- **The STREET is not full of scarecrows, and one body might still be one.**
  `armCrowdWidest=53.5` is a bent elbow at walking pace, printed off the real
  `ArmSwing`, and every body with an Animator has a clip whose time is moving —
  so the median retraction stands. But `armCrowdWidestWorst=76.6` is near
  ninety and `review_day2_night` has a figure with its arms straight out to
  both sides. The drop angle measures against straight DOWN and cannot tell
  forward from sideways; a walk is entirely fore-and-aft and a T-pose entirely
  lateral. `armSide` settles it next build.
- **The mob is real and neither the plan nor the ring causes it.** 700
  residents put at most six within two metres; the busiest scheduled place
  holds twelve; thirty-nine stood within two metres of one person.
  `busiestNear` separates the last two candidates next build.
- **Two white capsules are standing in the road** and no reading names them —
  `playerPrimitive` was built for the player alone. `walkersPrimitive` counts
  them next build.
- **The clutter in the road belongs to registered places**, twenty-two of whose
  facades stand in a carriageway; and the frame gate's biggest item was two
  passes sharing one number — the reband is 1.31ms, the body LOD 2.59ms.

### Startable right now, ORDERED BY WHAT SHOWS ON SCREEN

**The order is Jafar's, 4 August.** He asked why a day looked like almost
nothing and the honest half of the answer was that most of it was invisible to
him. So the top of this list is whatever a player would notice.

Most of tonight's work was INSTRUMENTS, and the next two builds are what they
say. Nine of these ten items are "read the number, then decide" — which is the
discipline, not a stall: every one of them has a fix that is one edit long once
the reading lands, and every guess made without one tonight was wrong.

1. **THE LAW HAS NEVER OPENED A CASE BECAUSE NOTHING TELLS IT ABOUT A BODY —
   AND THIS IS THE TOP OF THE LIST.** *(start at the top of a turn)*

   `GameController.RecordKilling` is the only path into `HomicideBook`, and it
   HAS NO CALLERS. So the register is empty in every run, `Pressure` returns
   zero, `Stage` returns `None`, and `inquiry=None` in all 131 kept verdicts.
   Everything downstream of `Inquiry.Investigation` has therefore never
   executed: the paper naming you, the redirect having anything to relieve,
   `Police.ForcesActThree`, `Police.BarsQuietExit`. One missing call, a whole
   stage of the game.

   **It is not a wiring slip.** The roadmap already records that M16's fighting
   is Core-only and nothing calls it, so there is no real killing path yet.
   What exists is the SIM's staged killings — `ViolenceHost.Commit` with
   `lethal: true`, three times, inside the places probe — and those never reach
   the register either.

   **The arithmetic decides how many to record, and it is unforgiving.**
   `PerBody = 0.4`, `InvestigationAt = 0.7`, `ManhuntAt = 1.0`. So one staged
   body gives 0.4 and `Procedure`; TWO give 0.8 and `Investigation`, which is
   exactly the stage that unlocks the paper and the redirect; three give 1.2
   and jump straight to `Manhunt`, which `ForcesActThree` reads and which would
   very likely rewrite Act III's ending and turn green gates red.

   **So: record TWO, not three, and watch `actThree` and `ending` on the run
   that does it.** Plant the condition, never loosen the bound — and this is
   the one place tonight where planting it carelessly could break more than it
   proves.

   **AND THE TOOL COULD NOT HAVE FOUND THIS.** `ReachCheck` covers public CORE
   APIs; `RecordKilling` is Game-layer, so nothing has ever asked whether it
   has a caller. The reach ledger's 35 entries are the Core half of a question
   nobody asks about the other half — and the largest unwired thing found
   tonight was on the side with no instrument.

1. **RETRACTED — THERE ARE NO SCARECROWS, AND THE MOB IS THE WHOLE FAULT.**
   `armWidest=54.5` with `armCrowdWidest=53.5`: taking the player out barely
   moves it, so the widest body is a walker. And printed off `Rig.ArmSwing`, a
   normal walk puts the FOREARM — which is what the metric measures — at 45.4
   degrees from vertical at 1.2 m/s, 48.3 at 1.4, 55.1 at 2.0. **53.5 is a
   person walking briskly with a bent elbow.** A T-pose is ninety.

   `animBodies=6 animDriven=6 animAdvancing=6` closes the other half: every
   body with an Animator has a controller and every one of them has a clip
   whose time is MOVING. Nothing is frozen in a bind pose. Forty-six of the
   fifty-two solved bodies are mannequins, which have no Animator to freeze.

   So the figures in `review_day1_night` were overlapping bodies in a mob, and
   at 1280x720 that reads as splayed limbs. Rule 4 exactly — a picture is
   excellent evidence something is wrong and poor evidence of WHAT. Something
   was wrong; it was the huddle, which the other number found independently.
   **The `HangArm` search is closed before it started, and everything it would
   have gone through — `PoseIsDriven`, the prefab controller, the rest capture
   — came back innocent on the way past.**

2. **THE RING WAS NOT THE MOB'S CAUSE, AND THE CHECK I BUILT IN SAID SO.**
   `crowdSpread=0.88` with `busiestPlace=12` — the packing rule fired exactly
   as computed (`0.45*sqrt(12/pi) = 0.879`) — and `crowdHuddleWorst` moved only
   from 41 to 36, `crowdHuddle` from 10 to 9.

   **Twelve at the busiest scheduled place, thirty-six within two metres of one
   person.** Those cannot be the same people. So the mob is NOT people sent to
   one point; it is people who END UP near each other, and a wider ring at the
   schedule cannot touch it. `busiestPlace` was printed for exactly this
   question and answered it on the first run.

   The ring change stands on its own merits — twelve people on an 0.8m ring got
   0.42m of arc each and now get 0.46m — but it is not this fault, and reading
   the huddle drop as a fix would have closed the wrong thing.

   **THE GENERATED SCHEDULES DO NOT CLUSTER — measured locally off the real
   generator with the real seed, no round trip.** 700 residents, 688 distinct
   home points and 687 distinct work points, and the most that share a point
   within two metres is SIX at home and FIVE at work. Only 38 are within ten
   metres of each other. The city plan spreads people properly.

   **The AUTHORED schedules do share exact points, and that is what
   `busiestPlace=12` is seeing.** `GameController`'s cast waypoints repeat by
   hand: `(10,0,-14)` is the market corner for three different people,
   `(18,0,14)` the docks for two, `(-16,0,-12)` and `(-12,0,14)` are two homes
   with two residents each. Twelve on one point is exactly what the packing
   ring was built for and it now gives them 0.88m.

   **NEITHER EXPLAINS THIRTY-SIX.** There are 42 walkers in the run and 36 of
   them stood within two metres of one person — 86% of everybody, in a disc
   the size of a small room, while the authored points are twenty metres
   apart. `busiestNear` lands next build and separates the last two
   candidates: near 36 means the targets cluster after all in a way the metre
   grid cannot see, and near 6 means the walk gathers them and the plan is
   innocent.

3. **BOTH DWELL NUMBERS HAVE LANDED, AND THE FIX IS NOT OBVIOUSLY WORTH IT.**
   `bodySpell=5.41` median with `bodySpellShortest=1.00` over 1,143 spells, and
   the perf split says `bodyLod=2.59ms` against `population=1.31ms` — the LOD
   pass costs twice the reband it was hiding inside, about 9ms per pass at 465
   passes a run, and 1,157 prefab instantiates is what it is spending it on.

   **A dwell time is now derivable rather than invented.** `Populace.BandSlack`
   is six metres of hysteresis and `crowdSpeed=1.28` is what the street walks
   at, so the band's own distance is 4.7 SECONDS — and the measured median
   spell is 5.41. Two independent routes to the same number, which is the
   strongest evidence this project ever gets for a constant.

   **AND IT HAS A REAL COST, WHICH IS WHY IT IS NOT DONE.** The budget is
   twelve bodies and the whole point of spending it by distance is that "the
   person in front of you is the one wearing a face". A dwell holds a slot for
   somebody who has walked away while somebody nearer waits — so it trades a
   visible fault for an invisible saving, on a frame gate whose milliseconds
   are known to track the runner rather than the game. **Decide it against
   `gameShare`, which is stable at 2.6-3.4%, not against the ms.**

4. **`nameShownWidthWorst` DECIDES TWO THINGS, AND THE SECOND IS THE BUBBLE
   BUG'S TWIN.** *(CI)* `nameWidthWorst=0.424` on "Wendell Dujmovic" is PRE-cap;
   the post-cap twin was computed and never printed, and it is now. `PinFrac`
   bounds HEIGHT, and `NameTags`' own comment says a bound on one axis of a
   two-axis object is not a bound.

   **AND IT ALSO TESTS WHETHER NAMEPLATES ARE STALE AT THE SHOT.** The bubble
   cap turned out to be applied a frame LATE — `LateUpdate` pins against
   wherever the camera was last, and `SimDirector.Shot` moves a camera and
   renders by hand inside `Update`, so `bubbleFracPreCap=0.659` sat beside
   `worstBubbleFrac=1.245`. `NameTags.Resolve` pins on exactly the same
   schedule, from `Camera.main`, in the frame before. `Billboard` re-aims at
   the shot and `SpeechBubble` now re-pins there; names are the third site of
   that idea and the only one still unfixed.

   **NOT FIXED BLIND, DELIBERATELY.** A post-cap width above what `PinFrac`
   allows is the staleness proving itself, exactly as it did for bubbles, and
   that number lands in the next build. Shipping the re-pin now would be fixing
   a twin on the strength of it being a twin — which is right often enough to
   be dangerous.

5. **`placeFacesInRoad` / `placeFacesInLane` DECIDE THE SETBACK FIX.** *(CI)*
   All eight pieces of clutter in a carriageway belong to registered places,
   which are set back from an authored map coordinate while block buildings are
   inset from a kerb. Moving buildings re-baselines `massInRoad`, the places
   gate and every framing shot, so it happens off the reading and not off a
   still.

6. **THE FRAME GATE'S BIGGEST ITEM IS NOW TWO NUMBERS.** *(CI)* `population=
   4.08ms` covered a pass that runs every frame and one that runs once a
   second. Read `population` and `bodyLod` apart before touching either.

7. **THE SECOND DROP MISS HAS NO EXPLANATION YET.**
   `d13:MISSED[from=16m nearest=6.9m walked=10.0m held:job=19]` — ten of
   sixteen metres covered, steered the whole window, stalled seven metres out.
   The first miss was the waypoint's own collider and is fixed. No obstacle
   explains this one, and the trace has no reading that can say what does.
   **A new column is the next move, not a mechanism.**

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

11. **THREE KILLINGS, CERTAINTY 1.00, AND THE LAW NEVER ASKED.**
   `killings[acts=4 killings=3 confidence=1.00]` with `notoriety=0.868`,
   `denounced=3` — and `inquiry=None` on the done line. The detective never
   opened an investigation into the player in fifteen days.

   That explains `pressNamed=0` completely and correctly: `Press.Print` names
   you only at `law >= Inquiry.Investigation`, and its own comment argues at
   length for using the STAGE rather than a pressure aggregate, because half a
   manhunt is not "somebody would say it to a detective". The paper is right.
   Nothing is broken here.

   **What is open is whether the inquiry can rise at all.** Two readings are
   consistent with `inquiry=None`: the street knowing and the law asking being
   deliberately different — which is the information pillar and the moat — or
   nothing driving the stage upward. `redirected=1 pointedAt=kest
   redirectRelief=0.00` says the redirect ran against a pressure that was
   already nothing.

   **AND SIXTY KEPT RUNS SAY IT NEVER HAS.** Every `inquiry=` in every verdict
   under `sim-shots/runs/` reads `None` — sixty for sixty, no exceptions. So
   this is not "the law was quiet this time": no run in the recorded history of
   this project has ever entered the stage, and everything gated on
   `Inquiry.Investigation` has therefore never been exercised — the paper
   naming you, the redirect having something to relieve, and whatever else
   reads that stage.

   **This is rule 5b's corollary aimed at a READING rather than a gate**: a
   number whose subject never occurs reads zero forever and looks like
   coverage, and the pattern is only visible ACROSS runs — which is exactly
   what `tools/gates.py --flaky` was built for and why it corrected me within a
   minute of being written. Start it at the top of a turn; it means reading
   `HomicideBook` and `EvidenceHost.InquiryOf` properly, and the answer is
   either "the stage needs a driver" or "the sim needs to plant the
   condition", which are different afternoons.

12. **THE REST OF WHAT `gates --constant` FOUND, AND IT IS A WORK LIST.**
   Sixty keys have never been anything but zero across 131 runs. Most are fault
   counters doing their job — `errors=0`, `idLeaks=0`, `blankLabels=0`,
   `panelsBad=0`, `offRoad=0`. These are the ones that are not:

   - **`threat` has only ever seen one outcome.** `brandishes=1` a run, so
     `called=0 complied=0 undraw=False` are three responses that CANNOT be
     sampled — one brandish can only produce one answer, and it has been
     `FleeScreaming` every time. Plant more than one, at people with different
     nerve, or the other three branches stay theoretical for ever.
   - **`contradiction=0.00`** — a denouncement has never been contradicted, so
     the whole contradicted half of `Informing` has never run. `denounced=3`
     every time and `corroboration=1.00`.
   - **`companion adds=0 departed=0`** — she is recruited and never leaves and
     never brings anybody. Two branches, no runs.
   - **`groundless=False`** — a carry has never been groundless.
   - **`summonsTaken=0` is FIXED tonight** (the public-callbox flag nothing
     read) and **`reliabilityFiled=0` is PLANTED tonight** (two skipped drops
     after day ten). Both should move in the next build, and if they do not
     the fix did not take.

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

**Trimmed 4 Aug late, because this file crossed its own 400-line bound and the
history is what pushed it over.** Done work is in the git log; this file records
what is NEXT. What stays here is only the handful a reader needs so they do not
re-open a closed question.

- **There are no scarecrows** — 53.5 degrees is a bent elbow at walking pace,
  measured off `Rig.ArmSwing`, and `animAdvancing` says nothing is frozen.
- **The night skyline is occupancy**, shopfronts follow opening hours, and the
  wash is anchored per material — trousers that were bright yellow are olive.
- **The limp reaches the street**: five named people used it, and the pose limp
  is the same size as the audio one for the first time.
- **A public callbox is reachable** — the flag was set on three lines, saved,
  restored, and read by nothing, which cost the rival's summons entirely.
- **The drop marker is not solid any more**; it was a box you walked into and
  stopped against, thirty centimetres outside its own completion radius.
- Build, cadence, loop phase, head size and breadth all reach the bought
  bodies; the pub's corner is in Hook Street; the upside-down player, the
  nameplate algorithm and the rest days are closed and stay closed.

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
