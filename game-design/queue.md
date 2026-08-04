# The work stack

> **STATUS — LIVE**, verified 2026-08-04. What gets picked up next, in order.
> The plan is `roadmap.md` and it wins; this is the next few hours of it.

## Why this file exists

On 3 August I dispatched five Windows builds in two hours and, four times,
**ended the turn instead of picking up the next thing** — twenty, thirty-two,
nineteen and twenty-eight minutes with nothing of mine landing. AUTO MODE rule 2
already forbade exactly that, in my own words, and I broke it four times in one
afternoon.

The cause was not forgetting the rule. It was that **the moment after a dispatch
is a decision point**, and a decision point at the end of a long turn is where
turns end. Nothing was written down, so "what next" meant re-deriving priorities
from a 400-line roadmap, and that is enough friction to lose to.

So the queue is written BEFORE the dispatch, and the rule becomes mechanical:
dispatch, then take the top non-CI item off this list. No judgement required at
the point where judgement was failing.

It lives in the repository rather than in a task list because the container is
ephemeral and the task list is not — rule 12's principle, applied to my own
scheduling instead of to CI's output.

## How to use it

- **Every item is sized to fit inside one build round trip (~28 min).** An item
  that cannot be finished in that window gets split until it can, or it will be
  abandoned half-done when the build lands.
- **CI-needed items are marked.** Those get batched into the next dispatch;
  they are never a reason to stop working.
- Take from the top. Move finished items out — this file records what is NEXT,
  not what happened. Done work is in the git log.

---

## Now

### WHAT THE 21:46 BUILD SAID, AND ALL THREE NEW INSTRUMENTS FIRED

**THE STREET DOES HAVE SOMEBODY STANDING WIDE, IN EVERY FRAME.**
`armWidest=54.2 armWidestWorst=75.4 armP90=21.3` over `armBodies=52`, against
`armStreet=10.7`. So the median body's arms hang, nine in ten are under 21
degrees, and the WIDEST of fifty-two is at fifty-four degrees in a typical
frame and seventy-five at worst. Roughly one body in fifty, permanently, and no
median could ever have seen it. The picture and the number now agree.

**WHO IT IS, THE NUMBER CANNOT SAY, AND THAT IS THE NEXT READING.**
`preArmDrop=65.3` says the PLAYER's own bought clip holds his arms at
sixty-five degrees before `CharacterRig` touches anything — inside the 54-to-75
band. So the widest body in a typical frame may simply be him, and the figures
in the night stills would be a third fault nothing has measured.
`armCrowdWidest` excludes him and is in the next build.

**FORTY-ONE PEOPLE WITHIN TWO METRES OF ONE PERSON.** `crowdHuddle=10`
median, `crowdHuddleWorst=41`, over 1,623 samples — while `crowdGapMedian=0.44`
reads as a comfortable street. `review_day5_noon` shows it: about
twenty-five people packed into a solid block on the right of the frame,
overlapping, many with their arms out. That is the mob, measured.

**THE LIMP IS LIVE AND FIVE PEOPLE USED IT.**
`limpNames=[Filip,Hana,June,Rocco,Sam]`, `limpNow=3` of fifty walkers, and
`limpWorst=0.05` — somebody compounded injuries all the way down to
`HarmBook`'s own floor. Until this build nobody in this city had ever limped.

**THE EIGHT STUCK CLUTTER ITEMS ARE ON FOUR BUILDINGS, TWO EACH** —
`warehouse_row`, `boarding_house`, `crescent_houses`, `laurel_letting` — and
NOT the pub, which this queue named as "certainly one" an hour ago. Waiting for
the number was right. `dressedRoadWidth=[2.25 4.25 4.50 6.50 10.00 x4]` says
two of them sit where the carriageway is barely two metres.

**AND THE BODY LOD IS STILL THRASHING**: 1,035 grants against 1,021 revokes for
a budget of twelve. `bodySpell` measures how long a body is kept and is in the
next build.

### Startable right now, ORDERED BY WHAT SHOWS ON SCREEN

**The order is Jafar's, 4 August.** He asked why a day looked like almost
nothing and the honest half of the answer was that most of it was invisible to
him. So the top of this list is whatever a player would notice.

Most of tonight's work was INSTRUMENTS, and the next two builds are what they
say. Nine of these ten items are "read the number, then decide" — which is the
discipline, not a stall: every one of them has a fix that is one edit long once
the reading lands, and every guess made without one tonight was wrong.

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

**CORRECTED — "raise the population" and "make the street busier" are two
different changes and this queue conflated them.** `CrowdWalkerCap = 12` bounds
how many bodies are out of doors within earshot, whatever `CityPlan.Count` is,
and it was set from measurement rather than ambition: at 3,000 residents there
were 333 people standing within 34m of the bar door, so the caps were not
thinning a crowd, they were choosing 28 out of a mob and spawning every one on
top of the player. Raising the count from 700 to 1,400 buys FAMILIARITY — 43.5
distinct faces a week against 47.4 — and changes the frame not at all. Whether
a dozen people in a plaza reads as a street or as a demonstration is a judgement
for Jafar off a still, not a number for me to move against a measured decision.


8. **Raise the population instead of cutting districts.** Measured, and it
   reverses the plan: seven districts at 1,400 people gives 43.5 distinct faces
   a week against 47.4 for three at 700, and 2,100 beats the cut outright. What
   is NOT measured is whether a fuller city still reads as a port rather than a
   crowd — that is a question for a still. Change the headcount, look, decide.
9. **Tier the cast — and the runtime is not the constraint.** All three sides
   measured. Design: 47 distinct faces a week, 13 near enough to read, a knee at
   ~50 people covering 92% of a resident's week. Witnesses: no fewer than ~20
   near an event. Runtime: 68 rigs cost 1.1ms of a 12ms budget. **The machine
   does not bound the cast at fifty; only authoring does.**
10. **M17.2 voices** — no longer held. The writing verdict came back 78 and the
   risk it was gating (paying to voice something that needs rewriting) is
   retired. Note this is a SPEND and Jafar has not authorised it.

- **IS FIFTY-SIX CONVERSATIONS A RUN TOO MANY?** A judgement about how
  talkative a street should feel, which is Jafar's off a still and not mine
  off a number. The history: 16–42 a run (mean ~24) under the old flat-3.0m
  road test, 7 after the walking pace slowed, and 56 now the test asks about
  junctions instead. So the junction rule is more permissive than the old one
  was even before the regression. It is defensible — the old test was
  rejecting 96% of pairs by asking for something the world never produces —
  but "defensible" is not the same as "right", and the number that decides it
  is how the street READS, not how it counts. Worth a look at the night still
  once the speech bubbles stop overlapping.

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

- **PLANT A COMPLETED DROP, so `jobRan` proves the pipeline instead of the
  bot's luck.** The gate says `JobsDone >= 1` and means "a drop can be made end
  to end: posted, walked to, completed, paid, laundered". What it measures is
  whether the bot won a footrace. Across 64 runs the outfit cuts the player off
  on seven, and on six of those `jobsDone=1` cleared the bound by accident — so
  the gate has been passing for the wrong reason far more often than it has
  failed. **Deliberately not loosened**: accepting "cut off before any drop"
  would let a run that never exercised the drop pipeline pass silently, which is
  rule 6 exactly. The fix is to make one drop reliably complete. `[series] jobs`
  now prints each drop's day, the distance when it opened and the closest the
  bot got, which says whether it was walking and ran out of night or never went.

  **THAT HAS NOW BEEN READ, AND THE PRIME SUSPECT NAMED HERE IS DEAD.** The
  suspicion was `frameWorstMs=43666` — one forty-three-second frame crossing
  02:00 while the walk gets a single step. The traces disprove it: every
  approach reading is timestamped INSIDE the window, and the failures cluster
  in the 2–10m band against a 2.5m completion radius. This is a bot that walks
  most of the way and stops short, not one that runs out of night.

  **The misses split cleanly in two and only one half is fixed.** With the owner
  tally added, `d8:MISSED[nearest=10.6m held:loiter-hold=21]` showed a staged
  probe owning every tick of a window while the bot stood still — the loiter
  refused to START during a drop and had no guard on the HOLD that follows.
  Fixed, and `loitersCutShort` counts what it costs.

  The other half is not that: `held:job=20 nearest=9.3m` and `held:job=19
  nearest=6.9m` mean the steering was right for every tick and the bot still did
  not arrive. Ownership cannot tell "steered and walking" from "steered and not
  moving" — a conversation, a knockdown or a blocked path all read as `job`
  holding the target — so the window now counts PATH LENGTH. **Read `walked=`
  before choosing a mechanism.** `d2` covered 16.5m in 14 ticks and completed;
  `d13` covered 12.1m in 19. More time, less ground, and nothing yet says why.
