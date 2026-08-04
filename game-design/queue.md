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

**THE BUILD IS GREEN AGAIN — `7dc6334`, `pass=True`, no failing gates**, after
the CS0119 that cost three round trips. Everything below is read off that
verdict.

1. **THE DROPS: `jobsDone` 1 → 2, and the trace names both remaining causes.**

       d1:MISSED[from=18m nearest=2.8m@01h]   d2:done[from=6m  nearest=2.1m@22h]
       d8:MISSED[from=8m  nearest=8.4m@22h]   d12:done[from=15m nearest=1.4m@00h]
       d13:MISSED[from=16m nearest=7.0m@23h]

   d12 was a miss before the loiter fix and is a delivery now. **d1 simply ran
   out of night** — eighteen metres at 22:00, 2.8m by 01:00, against a 2.5m
   radius, so it was thirty centimetres and one hour short. Not a broken check;
   the hour stamp is what proves it. **d8 never went at all** — its closest
   approach EQUALS its starting distance — and `beats=[… evening_d8 …]` is why:
   an authored evening beat outranks the job in the sim's target selection, the
   same collision the loiter had. **That one is a design question, not a bug:**
   a player would face the same choice between an evening scene and a night
   drop, and whether "evening" should be allowed to run into 22:00–02:00 is
   Jafar's call. Do not quietly re-rank it.

2. **THE MIRROR RATIO ANSWERED, AND IT CLEARS THE SHADER.**
   `textFacingAway=70 textVisible=149 textMirrored=0` — 47%, which is the
   double-sided street plates by construction, with none of them unculled. So
   `Cull Back` works and **I misread the picture**. What was backwards in
   `review_day5_night` will have been a speech bubble: those deliberately skip
   `WorldText`, which means they also skip its `Cull Back`, and they are the one
   kind of world text in this game that draws its own reverse. That is written
   into `SpeechBubble` now. The fix, if the number ever says bubbles are being
   read backwards, is a third shader with LedgerText's cull and the built-in's
   depth behaviour.

3. **THE REDIRECT RAN IN THE GAME.** `redirected=1 pointedAt=kest
   pointedOnDay=9`, and `redirectRelief=0.00` at the end of a seventeen-day run
   because the relief decays over four days — which is the mechanism working,
   read eight days later. M21's law-as-a-tool is now a complete verb end to end.

4. **THE WATCHED SPOT IS GENUINELY WATCHED.** `crowdedWatchers=39
   crowdedIsWatched=True` against `quietSpotWatchers=0`, so `disposal` and
   `accident` finally compare a place somebody can see against one nobody can.
   Both green.

5. **THE SLAM RINGS NAME THEIR OWN CULL.**
   `slamRings=[#1:shadowed@81m #2:drawn@62m #3:shadowed@81m #4:drawn@62m]` —
   two of four drew, and the two that did not were **shadowed**, at 81m against
   the drawn pair's 62m. So `perception`'s one red run was four slams that all
   happened to land shadowed. The fix is to PLANT one where the ring is not,
   never to loosen the bound — and the radius difference says where to look.

6. **TRAFFIC: `clamps=10 clampsPerKm=0.23 tailsBehindStart=0`.** The corrected
   tails metric reads zero, which is what it should read when `Cross`'s entry
   check is doing its job, and the clamp rate is a tenth of the bound measured
   from CoreTests. `gap=0.00` remains the clamp's signature at sample time.

7. **STILL OPEN AND NOT YET LOOKED AT:** `collidingBubbles` against
   `bubblesOnScreen` (sixty-six confabs is sixty-six bubbles, and the night
   still has two drawn through each other); the review camera standing inside a
   street sign; and speech-bubble
   decluttering.

   **CORRECTION: the Empire IS saved.** I wrote here and in a commit message
   that "the whole Empire — crew, cuts, rackets — is absent from `SaveCodec`",
   off a grep of the wrong file. `SaveCodec.Capture` takes an `extra`
   dictionary, `GameController.ExtraFlags()` puts `{"empire", Empire.Capture()}`
   in it, and `EmpireBook.Capture` writes businesses, crew, cuts, rackets, arms
   and the seed. What was genuinely missing was only the two fields added an
   hour ago, and they are in now with a round-trip test.

8. **Jafar runs `BODIES.bat` ~10:00 CEST**; reminder fires 07:55 UTC. Then the
   skinned crowd, costed and designed, worth far more once six textured models
   are in.

9. **Keep retiring the reach ledger** (71). What is left is mostly UI surfaces
   and one real refactor: `Mixing.*` has no audio choke point.

### Answered tonight, kept only as evidence

- `billboardsStale=5 billboardWorstDeg=75.2`, all 54 re-aimed at shot time —
  every still ever committed had been drawn with the previous frame's aim.
- `bodyCoat=[denim hsv=0.60/0.36/0.59 rgb=96,118,149]` — **reversed me.** The
  player's coat is mid-blue, not grey; a JPEG through a noir grade made it look
  like bare plastic and I was one step from re-rolling the palette. What
  survives is a judgement for Jafar: it still READS as undressed at noon.
- Traffic: `gap=0.00` on a third of runs is the de-overlap clamp, proven by
  `gapWhy` showing leader tail and follower nose at the same metre. The gate
  reads clamps-per-metre now. The 39 "tails behind an edge start" were my own
  metric counting a bus being long; `Cross`'s entry check is reached and works.
- `verdictSane` required job-nights from an outfit that had cut the player off.
  11% of runs end that way and `jobRan` had been passing on luck in six of seven.
- The flakiness table had no time axis and ranked `bodies` — fixed 60 runs ago —
  as the third-worst live gate.
- `verdict-keys` reported 465 measurements missing from a build that never ran.

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
