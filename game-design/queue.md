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

### THE BRANCH DID NOT COMPILE FOR TEN COMMITS, AND THE CHANNEL THAT SHOULD HAVE SAID SO LIED

`ViolenceHost` is a static class with no game in scope and I wrote
`Game.Campaign.Noted(...)` in it. Inside `namespace Ledger.Game` the bare name
`Game` binds to the NAMESPACE, so two builds came back `NO PLAYER LOG` with
CS0118. Fixed; the act now REPORTS what it is worth as a topic and the caller
charges it, which also stops the place-reading probe making the player notorious
for three killings it committed only to measure them.

**The instrument was worse than the bug.** The build that failed to compile
still committed "Sim stills from c61047f" — six replaced JPEGs and a rewritten
frame ledger, from a run that rendered nothing. It committed its own CHECKOUT's
copies, because dispatch takes a BRANCH and the runner was seven commits behind
the tip. The branch went backwards and the frames landed indexed under the sha
of the build that could not have made them. I opened all six and read them as
evidence about that commit before checking line one.

`tools/sim-shots-stage.sh` now names what a run actually produced — always the
verdict and the per-run copy, the stills only if the sim reached a screenshot,
the ledger only if it wrote one. Tested on both cases before it went near CI.

**Read the verdict's first line and its NO PLAYER LOG line before reading any
frame.** That is not advice, it is the only thing that would have caught this.

### Startable right now, in order

1. **BODY LOD — the frame gate is red and this is the actual fix.**
   44 skinned bodies is 1,037,694 vertices a frame against 16,338 before, so the
   cost is real work rather than runner contention, and the cap of twelve now in
   place is a holding action rather than an answer. Walkers pick their body at
   SPAWN, so LOD means exchanging one at runtime: attach a real body when a
   walker enters the near band, drop back to a mannequin when it leaves.
   `Population` already bands people and `CrowdWalkerCap` already bounds the
   near set, so "who is close" exists. What does not exist is a body that can be
   swapped without losing the rig's state — `RealBody.TryAttachExtra` saves and
   restores the statics, so the detach side is what is missing.
   Aim: eight nearby bodies is ~190k vertices, the order the rest of the scene
   is built at.

2. **THE TEXT TAIL — the series has landed and the threshold has not.**
   `nameFracMedian` reads 0.060 / 0.062 / 0.066 across three runs and
   `nameFracP90` 0.098 / 0.100 / 0.121, against a worst of 0.320 at
   `worstNameCentreMetres=1.09`. So the typical label is a sixteenth of the
   screen and the tail is a third of it, which is what the night stills show. A
   median cannot see a tail and this is the case it was written about.
   The work is a cap on how much screen one piece of world text may take, with
   the number printed before any bound is gated. **Do not set the bound from the
   three runs above** — they predate the frustum fix, so the population they
   were measured over excluded the frames with heaps in.

3. **M21, THE TWO LEDGERS — Core-shaped, no round trip.**
   The largest piece of unwritten game left: empire growth, law as a tool, what
   expansion costs you. Notoriety is the first brick and it landed today with
   its own decay and its own accumulation, so the next one is what a rival
   actually does with a reputation once you have one. Decomposed from standing
   work; take one sub-piece at a time and keep each inside a round trip.

4. **SIX CARDS STILL LACK EXAMPLE LINES**, down from sixty. Small, local, needs
   no key and no build.

5. **KEEP RETIRING THE REACH LEDGER** — 43 entries, every reason verified
   against the code today. Each one retired is a public API with a caller.

6. **WHEN THE NAME-HEAP BUILD LANDS, READ THREE NUMBERS AND NOT THE OLD TWO.**
   *(CI)* `namesDistinctPeak` below the offer peak means duplicate offers within
   a frame; equal to it means the lifetime managed set is the broken instrument
   and pruning its corpses is the repair. `namesOfferCalls` and
   `namesManagedDead` are the denominators. **Do not re-diagnose from
   `nameTagsOffered` and `namesManagedEver`** — three readings of that pair have
   produced three wrong answers, the most recent one this morning.

7. **WHEN THE FOOT-IK BUILD LANDS, READ THE DROP MEDIANS.** *(CI)*
   `ikPlantedMedian` against `ikCorrectionMedian` could never have answered the
   question: `correction` is derived from `blend`, so a swinging foot
   contributes an arithmetic zero and the overall median is the planted one
   diluted. `ikPlantedDropMedian` well below `ikDropMedian` means the plant
   blend is timed to the clip; the two landing together means it is not, and the
   fix is to derive the plant from the foot's own height.

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
