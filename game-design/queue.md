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

### ANSWERED BY THE 07:56 BUILD — read this before picking anything up

**Green, no failing gates.** The three counters dispatched to settle three
open questions all came back decisive, which is the point of adding a
denominator rather than guessing.

- **The wall wiring RUNS.** `beliefsShortened=445` of 3517 investigations —
  445 listeners went to the wall they heard through instead of walking to the
  exact spot. Rule 6 satisfied with a number rather than a claim.
- **THE VOICE BUDGET IS NEVER CALLED AT ALL.** `soundsOffered=0` with
  `soundsNoClip=0`. Not clips arriving null, not the budget refusing — `Admit`
  is never reached. So footsteps and impacts are not routed through it in the
  sim, or `Audio` is not initialised on that path. **This is the next thing to
  chase**, and it is one grep: find who calls `Audio.Footstep` and whether
  `_root`/`_foot` are ever non-null in a headless run.
- **The contrast headroom is real now**: `contrastTightest=4.73` at the ledger
  title, 20pt, against 21.00 meaning nothing last run. It passes AA; it is the
  tightest pair and now visible if it drifts.
- **`claimOverheard=1`** — the planted bystander took. Series 1, 0, 1, 35, 0.
  One nonzero settles nothing on its own; watch it across runs.
- `crowdGapMedian` 0.29 (was 0.20, was 0.00) — moved again, as expected, since
  the belief wiring changes where people walk. `crowdTightest` still 0.00 and
  `crowdInside=312`: the standing-still fix is what addresses that.
- `confabs=34`. Joint-lowest of the last ten, and INSIDE the current regime's
  29–74 with earlier runs at 33, 31 and 29. A single run inside the band says
  nothing in either direction — do not act on it.
- `lineCrossedLive=17 lineYielded=17`. Still exact.

### THE 08:01 BUILD — the name heap is street plates, and a closed item reopened

**Green.** `worstWorldPair=[Copper Row|Market Road]` — the overlapping world
text is STREET PLATES, and two plates overlapping at a junction is what a
junction looks like. `collidingWorldText` at 121–134 is furniture, not a fault.

**But it does not settle the heap of PEOPLE'S names in the frame**, because
the probe recorded the FIRST overlapping pair while being called
`worstWorldPair`. My own rule about a number keeping its name, broken three
hours after writing it down, and wrong on arrival rather than by drift. Now
worst by overlap AREA — a pair clipping at the corner is a junction, a pair
sitting on top of each other is the fault. Re-read it next build.

**"THE REVIEW CAMERA IS NEVER BLOCKED" IS NOT TRUE AND WAS ONE RUN.** This
build reads `shotsBlocked=1`, a lamp pole at 5.4m, and the day-5 night still
shows the camera jammed against a street sign. The series is 1, 0, 0, 0, 0,
1, 3, 0, 0 — median 0, max 3. So it is intermittent, it was closed off a
single twenty-shot reading of zero, and the standing "do not reopen" list
carries that closure. Correct the list: the camera is *usually* clear.

### BASELINE BREAK TO KNOW ABOUT

**`nightRunNotices` moved too, and its history is not comparable.** The
re-classification fix took BOTH notice counters off the attention rising
edge, because both had the identical structural bug. The commit message
called out only `remarks` as a number with a landed history worth
protecting; `nightRunNotices=4` has one as well and it will read differently
now for a reason that is a fix rather than a regression. Do not compare the
next reading against 4. `loiterNotices` has no such problem — it has only
ever read 0, which was the bug.

### STAGED AND UNDISPATCHED, 08:14 UTC — seven commits

One build in flight (the standing-still separation fix plus the hoisted
numbers). Six commits sit on top of it, all additive reporting, none
behavioural except a read-only phone lookup:

`simAudible` (so `soundsOffered=0` cannot read as a fault), `worstWorldPair`
by overlap AREA rather than first-found, the line-length measure,
`identifiedPeak`/`identifiedEver`, `callsTried`/`callsReachable`, and
`roomQuiet`. **Dispatch these together the moment the separation build
lands.**

**Reach ledger: 50, from 71 two nights ago and 55 at 07:00 today.** Six
retired this morning — `HeardAs`, `BelievedAt`, `MeasureIsReadable`,
`Attention.Identified`, `PhoneBook.ReachableNow` with `LinesFor`, and
`MusicModel.RoomHasGoneQuiet` — every one by being wired to something that
runs rather than re-described.

**NEXT SUBSTANTIAL ITEM: `Reaction.Confront`.** The ledger calls it "the
single most visible missing reaction in the game": an NPC who saw you do it
walking over. That is immersion rather than instrumentation, and immersion
outranks systems. It moves walkers, so it starts once the separation build
has landed and been read — not before, or a moved crowd number has two
causes again.

### IN FLIGHT, 08:14 UTC

Two builds are out and a batch is committed but NOT dispatched. If you are a
cold session reading this, that is the first thing to resolve.

- **Out:** one carrying the belief wiring plus `soundsOffered`/`soundsNoClip`
  and `contrastTightest`; a second carrying those plus `worstWorldPair`. The
  second supersedes the first — read whichever names the newer commit.
- **Dispatched 07:57** — the crowd-separation fix for people STANDING STILL,
  plus the numbers hoisted onto the done line (`corroboration`,
  `contradiction`, `denounceMark`, `marked`, `saw`, `ringLastOccluded`). Read
  `crowdTightest` and `crowdInside` against 0.00 and 312, and `confabs`
  against the series rather than against one run.

### Startable right now, in order

**The crowd build landed GREEN on `daf91d5` — pass=True, no failing gates, the
sim ran.** That closes the three-build compile outage. What it settled:

- **Crowd separation works, partly.** `crowdGapMedian` 0.20 against 0, 0, 0, 0
  over the four previous runs, on 1627 samples. But `crowdTightest=0.00` and
  `crowdInside=284`, so the median moved and the worst case did not. Separation
  is a constraint applied per step; something is still resolving to zero.
- **Confabs 48**, against a baseline of 49 and a last-ten median of 48.5.
  Conversation did not collapse. Had the old "74" stayed in this file it would
  have read as a 35% collapse and been "fixed".
- **The 180 yield is exact**: `lineWatched=42 lineCrossed=19 lineCrossedLive=19
  lineYielded=19`. Every live crossing yielded. Closed.
- **Stamina works**: `staminaLow=0.203 staminaHigh=1.000`. Not pinned at either
  end, so the breathing model matters over a run. First reading, so this is
  plausibility and not a baseline.
- **The player is fine.** Three stills show it pitched forward and day 5 shows
  it standing straight — it is a run cycle, `bodyPitch=40.8` with
  `bodyUp=1.000`, `playerPrimitive=False`, `clip=[mixamo.com]`. Nearly reported
  as a broken rig off a picture, which is the `liveArmDrop` mistake exactly.

1. **THE WORLD TEXT IS THE VISIBLE FAULT AND IT IS MEASURED.** The day-5 night
   still has a heap of name labels — Bruno, Dario, Zora, Petra, Fabjan, Mitch —
   overlapping at angles and completely illegible. The numbers agree, but NOT
   the one you would check: `collidingNames=1` says names are fine.
   `collidingWorldText=75`, `textFacingAway=70` of `textVisible=140`, and
   `billboardWorstDeg=116.9` with `billboardsStale=38` of 57 tracked.

   So half the world text faces away from the camera. `billboardStaleMedian` is
   0.000 and I called billboards fine off it last night — the median is right
   and the tail is where the fault lives. Fix the aim, not the median.
2. **Why the voice budget saw nothing.** `soundsOffered` and `soundsNoClip` are
   dispatched and will separate the three cases: nothing calls it, every clip
   arrives null, or it refuses everything. Note `speechPlayed=0
   speechMissing=387 speechNoClip=347` — silence upstream is the likely answer
   and that is M17.2, which is a spend Jafar has not authorised.
3. **`claimOverheard=0` WITH THE BYSTANDER PLANTED.** The series is 0, 1, 35, 0.
   The planting did not take, or the claim and the plant did not coincide.
   `claimsMade=2 claimsCaught=1 claimVia=[game.Hosts]` — the claim happened, so
   this is the planting.
4. **`crowdTightest=0.00` and `crowdInside=284`.** Separation moved the median
   and not the worst pair. Read `StepApart` for the case that resolves to zero —
   coincident bodies get a deterministic shove, and two walkers spawned on the
   same point may be shoving along the same axis.
5. **`beliefsShortened` on the next verdict** — proof the wall wiring runs. Zero
   means either nothing investigates through a wall or `OccluderDistance` never
   finds one, and `investigations=3901` says the first is unlikely.
6. **`contrastTightest`** — the honest headroom across all 40 checked pairs,
   rather than 21.00 meaning "nothing failed" and "nothing measured" at once.
7. **A FIGHT CANNOT BE STARTED FROM THE GAME.** `Combat.` occurs exactly once
   in the whole Game layer. Built, tested, disconnected — rule 6 in its purest
   form. A milestone, not a queue item; the roadmap now says so.
8. **Jafar runs `BODIES.bat` ~10:00 CEST**; reminder armed for 07:55 UTC.
9. **FOOT IK — the hold is now LIFTED.** Crowd separation is verified working,
   so the two-suspects argument is spent. `Rig.TwoBone`, `FootHeight` and
   `PlantBlend` are a complete ground-adaptation model with no caller; feet get
   `Level()` and nothing else, so they float and clip on any slope or step.
   This is the next big one.
10. **Keep retiring the reach ledger** — 55, from 71 two nights ago. `HeardAs`
   and `BelievedAt` came off today by being wired rather than excused.

---

## What last night settled, in one line each

Full accounts are in the commit messages; this is the index, and it is here
only so a reader does not re-open a closed question. **Anything with a number
beside it was measured, not judged from a still.**

- The ledger screen called the player by their database key in four rumours,
  and printed one repeated reason three times where three different ones fit.
  Both fixed and confirmed green.
- The escort was recruited by walker-list position, twenty-four metres away;
  she is picked by proximity now and arrives at nine.
- The third competence brick is a WEIGHT, not a face count, and it runs: thirty
  rumours from your own face against two from your crew.
- `ALL GATES` prints every run, so the 35 diagnostics that were readable only on
  a failing run are readable on a passing one. Confirmed landing.
- A comment took the build step past a hard size limit and broke dispatch
  outright; `workflow-size` now catches that at commit time.
- Bubbles are fine — 166 samples, median zero overlapping pairs. The peak of
  116 was a real crowd pile-up, not the normal state.
- The camera never stands in front of the player: twenty shots, zero blocked.
  Three stills' worth of eye-judgement about foreground clutter was wrong.
- Overhearing exists: an alibi told to one person is now heard by whoever is
  close enough to make out the words, capped below knowledge.
- Twenty seconds of watching somebody now carries an identification floor into
  what they witness. It never did.
- The grade cools when the player is exposed and warms when hidden — written,
  tested and unwired since it was written.
- **`workflow_dispatch` does not pin a commit.** Four builds were dispatched at
  named shas and none of those shas was ever built. Watchers must ask whether a
  run CONTAINS the commit, not whether one is named after it.

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


6. **Raise the population instead of cutting districts.** Measured, and it
   reverses the plan: seven districts at 1,400 people gives 43.5 distinct faces
   a week against 47.4 for three at 700, and 2,100 beats the cut outright. What
   is NOT measured is whether a fuller city still reads as a port rather than a
   crowd — that is a question for a still. Change the headcount, look, decide.
7. **Tier the cast — and the runtime is not the constraint.** All three sides
   measured. Design: 47 distinct faces a week, 13 near enough to read, a knee at
   ~50 people covering 92% of a resident's week. Witnesses: no fewer than ~20
   near an event. Runtime: 68 rigs cost 1.1ms of a 12ms budget. **The machine
   does not bound the cast at fifty; only authoring does.**
8. **M17.2 voices** — no longer held. The writing verdict came back 78 and the
   risk it was gating (paying to voice something that needs rewriting) is
   retired. Note this is a SPEND and Jafar has not authorised it.
9. **Six cards still lack example lines**, down from sixty. Small, local, no key
   needed to identify them.

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
  bot got, which says whether it was walking and ran out of night or never went
  — read that before choosing a mechanism. Prime suspect is `frameWorstMs=43666`:
  one forty-three-second frame crosses 02:00 while the walk gets a single step.
