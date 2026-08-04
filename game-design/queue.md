# The work stack

> **STATUS — LIVE**, verified 2026-08-03. What gets picked up next, in order.
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

1. **ONE GATE STILL RED: `claims[made=0]`.** *(CI)* Everything else that failed
   tonight is fixed and confirmed by a landed build — `poachesHeard=1`,
   `allegianceOk=True`, and the companion no longer appears in any failing
   list. The claims probe was lifted out of the denunciation's one-shot guard
   in 79f53c0 and that build has not landed. **Read `claimWhy` when it does**;
   it names which of the three silent early returns fired.
2. **Read `collidingBubbles` against `bubblesOnScreen`.** *(CI)* The night
   still has two speech bubbles drawn through each other. Fifty-six confabs is
   fifty-six bubbles. `NameTags` already has the declutter and `Manages`
   already draws the line — offer bubbles to it, but **only once the number
   says how bad it is**.
3. **Read the `[panel]` line.** *(CI)* The ledger screen's live text now goes
   into the verdict. Everything built tonight ships into that panel and none
   of it has been read back yet.
4. **Jafar runs BODIES.bat ~10:00 CEST.** README opens with the three steps;
   reminder fires 07:55 UTC.
5. **Then the skinned crowd — costed, designed, item 4b below.** Worth far
   more once the six textured models are in.
5b. **THREE GATES ARE INTERMITTENT, and that is worse than three broken
   ones.** `harm`, `disposal` and `accident` have each gone red on runs where
   nothing relevant changed — `accident`+`disposal` together on one older
   run, `harm` on another, all three on 31332c2 — while passing on either
   side. Checked before blaming tonight's change, which touched none of them.

   The one lead: `harm` prints `samCap=0.7000` on the failing run against
   `samCap=1.00` on passing ones. That is `Watched.LoyaltyCeiling`, which
   only moves when Sam WITNESSES a killing — so the gate asserts something
   that stops being true in a legitimate world state, rather than catching a
   fault. Over-specified, not flaky.

   **Fix the assertion, not the world.** And soon: a gate that is red for a
   reason nobody can name trains everyone to read red as noise, which is the
   failure mode that lets a real one through. Read all three failing verdicts
   side by side against a passing one before touching anything.

6. **Keep retiring the reach ledger.** 90 to 77 tonight, every one wiring
   rather than building. What is left is mostly UI surfaces
   (`OperationPlan.Bringing` needs crew selection) and one real refactor: the
   `Mixing.*` voice budget has no choke point to enforce it, because the audio
   layer plays through several `AudioSource`s directly. That is a design job,
   not a wiring, and it is the honest reason those five entries survived
   tonight.

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
- **Turn a still into a number.** Four faults have now been found by opening a
  frame and none by a gate — the newest being a naked body with a metric
  reporting it clothed. Anything a frame shows that no metric names is a metric
  worth adding.
