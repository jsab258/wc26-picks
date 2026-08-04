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

1. **READ `armWidest` THE MOMENT IT LANDS, AND IT FORKS THE SEARCH.** *(CI, in
   flight)* Near 90 in a typical frame means a body standing in its BIND POSE —
   `HangArm` is guarded on `!PoseIsDriven`, so a body with an Animator and a
   controller is left entirely to the Animator, and if that Animator has
   nothing to play the bones stay where the FBX put them. Near 65 means a clip
   IS playing and its arms are simply wide — a completely different fix, and
   `preArmDrop=64.8` on the player says 65 is a real number this rig produces.
   `armP90` beside it says whether it is one body or a tenth of them.
   **Do not touch `HangArm` before reading both.**

2. **READ `crowdHuddle` AND THEN LOOK AT `NpcWalker.SpreadMetres`.** *(CI, in
   flight)* The suspect is named and deliberately not yet changed: `SpreadMetres
   = 0.8f` is a FIXED ring radius, so a place with twenty-five people scheduled
   to it gives each of them about 0.2m of arc — a constant that stopped
   answering its question when the crowd got bigger, which is rule 2's drift.
   A radius that grows with the number of people assigned to a place is the
   obvious fix and it needs the huddle series first: a huddle of six is a bus
   stop, a huddle of thirty is a fault, and only the runs can say which this is.

3. **THE LIMP'S STANCE SCALE STILL DOES NOT REACH A BOUGHT BODY.** The pelvis
   DIP composes onto a driven body; the shortened bad leg goes through
   `DriveLimbs`, which is guarded on `PoseIsDriven` in its entirety. So an
   injured cast member drops onto their good leg and does not shorten the other
   one — a gameplay signal at half strength. The file's own pattern is the fix:
   compose a delta onto whatever the Animator wrote, exactly as the chest lean
   and the pelvis counterturn already do, rather than assigning a swing it does
   not own. **It wants a measurement first — how much of a limp is the dip
   alone** — and that measurement is a Core arithmetic question that can be
   answered here without a round trip, off `Rig.Limp` and `Rig.LegSwing`
   printed rather than reasoned about.

4. **`review_day5_noon` IS A WALL OF TEXT AND NOTHING ELSE.** Two "Another
   time" bubbles at roughly a fifth of the frame height each, fourteen name
   labels overlapping into illegibility, and the street behind them invisible.
   Whatever else is true, that frame is what a player would see standing in a
   crowd, and no number names it: `nameShownWidth` bounds a label's WIDTH and
   nothing bounds a bubble's height or the total ink on screen. **Turn it into
   a number before proposing anything** — the tallest label as a fraction of
   frame height, and how many labels overlap another.

5. **`dressedStuckOn` NAMES WHICH WALLS THE EIGHT STUCK ITEMS SIT ON.** *(CI)*
   The pub's corner is certainly one, measurably 1.5m inside Hook Street. Read
   it before proposing a level fix; the last two guesses about the world came
   from the wrong half of it.

6. **KEEP RETIRING THE REACH LEDGER** — 36 entries. **AND READ THE ENTRY'S
   REASON, NOT JUST ITS NAME**: two reasons were still wrong by the evening,
   both describing behaviour that has been running for weeks when the real gap
   was that nothing DREW the thing. A wrong reason sends somebody at work that
   finished a fortnight ago.

7. **RE-READ `crowdGapMedian` AGAINST THE NEW BREADTH RANGE.** The gate compares
   a median spacing to a body width of 0.45, one constant. Bodies are now
   0.86–1.18 times as wide, so the widest is 0.53 and the narrowest 0.39. This
   is the "a number keeps its name when the question moves" case, and the change
   that moved it has shipped.

8. **THE NAME HEAP — AND RULE 2 NOW APPLIES TO IT.** *(CI)* The behaviour fix is
   in and is what mattered. The COUNTERS have contradicted themselves twice.
   **If the next reading is still incoherent, delete them rather than explain
   them.** The four numbers now come from a single frame, which is the last
   explanation they get.

9. **M22, THE SHAPE OF A PLAYTHROUGH** — the largest Core-shaped piece left, and
   one concrete sub-item is startable now: `PopulationSeed = 20260726` is
   hardcoded, a second seed gives 699 of 700 different people, and there is no
   new-game surface to choose one. **It must not be randomised** — CI
   determinism depends on it — so this is a surface, not a change to the
   default.


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

- **The night skyline is occupancy** — 1747 windows lit of 2447 against a
  measured 0.70 of the city being in, and the still shows lit and dark windows
  on the same floor where there was a wall of identical cream. Shopfronts
  follow OPENING hours rather than occupancy, about a third late.
- **Bus stops and cab ranks are signed** — `transit=8` against a 6-to-8
  prediction written before the dispatch. Both entries described missing
  behaviour when the real gap was signage.
- **The wash is anchored per material** — seventeen albedo sheets measured,
  0.04 to 0.78 against a 0.46 ceiling, and multiplying by wardrobeValue/albedo
  needs no constant at all. Trousers that were bright yellow all day are olive.
- **Build, cadence, loop phase and head size** all reach the bought bodies now.
  Twenty-two distinct breadths, forty-five seeded phases.
- **The pub's corner is in Hook Street**, 1.5m each way, pinned at two so it
  can shrink and not grow.
- **Paying in full and being cleaned out are different days.**
- **The indoor rain gain was 0.424 where the model said 0.28**, because three
  places held one idea.

- The upside-down player, closed by looking at the frame: two independent
  faults in our own rig, both fixed, a figure on its feet in the noon still.
- The nameplate that measured 2,119 times the frame height — the screen-rect
  helper projected two diagonal corners of a rotating box. Now 0.825.
- The rest days were never unrun; I read screenshot filenames as run length.
- Parallel builds; the work queue and its checker; the Tier-2 generator's
  thirteen writing rules with a no-key self-test; example lines for 54 of the
  60 generated cards; the conversation probe and a measured 78; per-character
  geometric cost; M19 input parity.

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
