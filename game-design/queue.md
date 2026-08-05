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

- **Settled and closed:** the summons zero is honest (`summonsMissWhy` moved to
  "a line was live and he was not near it"); the reliability rule fired for the
  first time in 132 runs (`reliabilityRead=[Slipping after 3]`); the two-axis
  name cap is IN but undemonstrated — both worsts read 0.171, which is a quiet
  run rather than a confirmation.
- **THE ARMS CARRY REAL LATERAL SWING.** `armSide=43.8 armSideWorst=68.5` on
  `8f6243f` — the first reading that can tell fore-and-aft from sideways, and a
  walk is entirely fore-and-aft. The median retraction (53.5 is a bent elbow at
  walking pace) stands; the LATERAL component does not obviously belong to a
  walk and wants the same treatment `ArmSwing` got — print what the model says
  a correct walk should give, then compare.
- **THE MOB IS NOT SOLVED AND I SAID IT WAS.** `huddleCells=21` at a huddle of
  41 is real: the bodies come from twenty-one different cells, so sizing each
  ring from its own cell cannot separate them. The fix sized it from the
  two-metre neighbourhood instead — and `c7e841b` says that changed NOTHING.
  `crowdSpread=0.88`, the widest ring ever issued, identical to the build
  before. **The refutation was on the same line the whole time:**
  `busiestNear=12` equals `busiestPlace=12`, so a two-metre disc holds no more
  people than a one-metre cell, and `SpreadRadius(12)` is 0.88 either way. I
  read that pair as "the plan is innocent" hours earlier and never read it as
  "these two counts are the same number".
  Reverted. **A 19-cell knot needs a radius sized from the KNOT** — 19 gives
  1.11m, 41 gives 1.63m — and no small radius can see one. The next attempt
  needs a count at the scale of the thing being separated.
  **AND THE MEDIAN HUDDLE GOT WORSE IN THE SAME BUILD**, 11 to 20, with
  `crowdGapMedian` 0.42 to 0.37. Not attributable to the ring, which did not
  move; the other candidates in that batch are the corner exemption putting
  nine addresses back at junctions and the four routines now following moved
  places. `headingIntoRoad` went 10 to 16, which is the corner exemption doing
  exactly what it was asked to.
  **The day-5 frame looks clear, and that is not evidence.** One instant
  against a run peak, which is the trap this project has written down six
  times — read from the other side for once.
- **THE STREET WALKS BENT DOUBLE.** `lean=36.3 leanWorst=41.7` over 74,410
  readings — a MEDIAN, so it is the whole street. Not a rest-pose artefact:
  `Mannequin` puts `Chest` directly above `Hips`. The suspect is the write —
  every other bone composes from a stored rest and the lean alone does
  `_chest.localRotation * Euler(pitch...)`, and the line that re-establishes
  rest is guarded on `!PoseIsDriven`. `leanDriven`/`leanRest` say next build
  whether accumulation is the whole of it. **Not fixed blind: this is the pose
  code that produced the upside-down player.**
- **THE YELLOW TROUSERS ARE THE MODEL, NOT THE WARDROBE.** Texture extraction
  switched the paint path off, so `bodySkinnedEver=0` and the wash maps over a
  kept Mixamo albedo. A number that exonerates one system says nothing about a
  second system standing in front of it.
- **THE FIRST BODY EVER REACHED THE REGISTER.** `inquiry=Procedure`, off `None`
  for the first time in 132 kept runs, with `actThree=True ending=BurnBoth`
  both unmoved — exactly what gating the staging on `ActThree.AuditClosed`
  predicted. And `weaponNotices=157 batCarried=True`: the street can see a
  carried bat, where that argument was a hardcoded `false` this morning.
- **`walkersPrimitive=0` IS NOT AN ANSWER ABOUT THE CAPSULES.** It is reset at
  the top of every once-a-second pass, so it describes the final second of a
  fifteen-day run. "Is anybody" is never a last-wins question.
  `walkersPrimitiveEver` is the peak and `walkersPrimitiveOf` is the walker
  count from the pass that peaked. The frame gate's biggest item was two passes
  sharing one number: the reband is 1.31ms, the body LOD 2.59ms.
### Startable right now, ORDERED BY WHAT SHOWS ON SCREEN

**The order is Jafar's, 4 August.** He asked why a day looked like almost
nothing and the honest half of the answer was that most of it was invisible to
him. So the top of this list is whatever a player would notice.

Most of tonight's work was INSTRUMENTS, and the next two builds are what they
say. Nine of these ten items are "read the number, then decide" — which is the
discipline, not a stall: every one of them has a fix that is one edit long once
the reading lands, and every guess made without one tonight was wrong.

1. **READ WHAT FOUR VISIBLE FIXES DID.** *(CI, dispatched)*

   Four changes to what a player sees are in flight together and each has a
   number that says whether it worked and one that says whether it overshot.

   **The mob.** `SpreadRadius` now reads the neighbourhood count instead of the
   cell. Watch `crowdHuddleWorst` fall and `crowdGapMedian` rise. If the deed,
   places or companion gates move, the ring is too wide for a street this size
   and the answer is fewer people at one address, not a smaller disc.

   **The bubbles.** The stack asks the screen rather than a four-metre world
   radius. `bubblesAtCeiling` should fall from 61 of 156; `bubblesScreenLifted`
   says the pass ran and `bubblesNoBounds` is the one uncertainty — a TextMesh
   built this frame may have no renderer bounds yet, and a zero lift with a
   large no-bounds count means it never got to ask.

   **The pavement.** Three cast routines drank standing in Hook Street; all six
   bar-door offsets go through `OffTheCarriageway` now. `headingIntoRoad` was
   10 of 56 and should fall to about 7.

   **The threats.** `complied` and `called` have been zero for 136 runs because
   one staged threat at one nerve value reaches one branch of five. Two more
   are staged, ordered so the fiction's own threat runs last and leaves the
   stance today's runs leave.

1. **TWO IN FIVE SPEECH BUBBLES LAND ON TOP OF A NEIGHBOUR.** *(on screen)*

   `bubblesMade=156 bubblesAtCeiling=61` on `8f6243f` — 39%, which is not the
   small residue the stacking comment hoped for. The cap is `MaxLift` 1.8m at
   `LineLift` 0.45, so exactly four lines, and everything past that is put on
   top of something.

   **And it is NOT the mob.** `huddleTalking=0` at a huddle of 41 says the knot
   is not a conversation, so these are ordinary street confabs clustering
   inside the 4m stack radius. Fixing the mob will not fix this.

   **The fix is the one the code's own comment names — a screen-space pass —
   and the machinery already exists.** `SpeechBubble.Rects` projects every live
   bubble through `NameTags.ScreenRect`, which is exactly the test a stack
   wants: two bubbles 4m apart overlap at thirty metres and do not at three,
   and a world radius cannot express that.

   **The uncertainty is worth stating rather than discovering.** A new bubble
   has no renderer bounds until its TextMesh has been built, so measuring it in
   the same frame it is created may read stale or empty bounds. That is a
   build-verification question, not something to write blind — stage it, print
   how many lifts the screen test actually changed, and only then delete the
   world-radius path.

1. **READ WHAT THE ID FIX BOUGHT.** *(CI, next dispatch)*

   `witnessOffered`/`witnessDropped` say whether the crowd can hear at all now:
   a large offered with a zero dropped is the fix landing. Then `homSaw` beside
   `homNamed` and `homPressure` — if the twenty-nine can now name the player,
   pressure goes past `ManhuntAt` and `inquiry` jumps from `Procedure` to
   `Manhunt`. **That is expected and it is safe** (the staging is after
   `AuditClosed`), but check `actThree` and `ending` did not move anyway.

   Also landing: `armSide`/`armSideWorst` for the lateral splay,
   `walkersPrimitiveEver`, `bubblesMade`/`bubblesAtCeiling`,
   `addressesSetBack`/`addressDriftMedian`, `homWouldTalk`.

2. **CLOSED — NO SCARECROWS, AND THE RING WAS NOT THE MOB'S CAUSE.**
   `armWidest=54.5` against `armCrowdWidest=53.5` says the widest body is a
   walker, and off the real `Rig.ArmSwing` a normal walk puts the FOREARM at
   45.4 degrees at 1.2 m/s and 55.1 at 2.0 — so 53.5 is somebody walking
   briskly with a bent elbow, and a T-pose is ninety. `animBodies=6
   animDriven=6 animAdvancing=6` closes the other half: nothing is frozen in a
   bind pose, and forty-six of the fifty-two solved bodies are mannequins with
   no Animator to freeze. The ring: `crowdSpread=0.88` with `busiestPlace=12`,
   the packing rule firing exactly as computed, and the huddle moved only 41 to
   36 — the change stands on its own merits and is not this fault. The
   generated schedules do not cluster either: 700 residents, 688 distinct home
   points, at most six sharing a point within two metres.

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
