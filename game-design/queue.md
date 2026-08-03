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

1. **The upside-down player: cause found, fix dispatched, NOT YET CONFIRMED.**
   Our own rig composed onto its own previous output because the rest-restore
   asked whether an Animator existed rather than whether anything was driving
   the pose — and the bought body has an Animator with nothing in it. Proven by
   the one sample that cannot contain our solve: upright on the very first
   frame, inverted later. Read the next stills before believing it.
2. **A second fault the same run found, also fixed and unconfirmed.** A
   nameplate measured 2,119 times the frame height, because the screen-rect
   helper rejected labels behind the camera but not labels almost at it. That
   helper feeds the declutter, so one NPC brushing the camera would have
   suppressed every name on screen while the counters reported success.
3. **The rest days have never run in the engine.** The sim renders campaign
   days 1 and 2, both working days, so no still has shown a Saturday and no
   gate has evaluated one. Covered by CoreTests and nothing else. *(CI)*

## Next

5. **Tier the cast — and the runtime is not the constraint.** All three sides
   are now measured. Design: a full week at three districts gives 47 distinct
   faces, 13 near enough to read, and a knee at ~50 people covering 92% of a
   resident's week. Witnesses: no fewer than ~20 near an event. Runtime: one
   skinned body is 64 bones and ~14,200 vertices, and all 68 rigs together
   cost 1.1ms of a 12ms game-frame budget — 0.016ms each. Bodies are capped at
   28 anyway, so ~400,000 vertices is the worst case and no real GPU cares.
   **The machine does not bound the cast at fifty; only authoring does.**
6. **Judge the conversation as OUTPUT.** Blocked on one small spend (below).
7. **M17.2 voices** — held behind that verdict.

## Done today, kept here only until the next tidy

- Parallel builds; the work queue; the Tier-2 generator's decade and its
  eleven writing rules with a no-key self-test; example lines and period
  texture for the whole cast; per-character geometric cost and a `rigs` frame
  bucket; M19 input parity with a number behind it; days that differ.
- Three "faults" that were my own instruments: the mirrored-text count, the
  oversized-nameplate metric, and the verdict-key checker failing on good news.

## Blocked, and on whom

**One decision, and it now buys two things.** Nothing has been spent; every
purchase is Jafar's. Raise at most once a day.

- **Judging the conversation as OUTPUT** needs a small API spend to generate
  sample exchanges, including adversarial ones. The input-side verdict is in
  `writing-judgement-2026-08-03.md` and was better than expected, so this is the
  cheap half of an open question rather than a rescue.
- **And the same spend would lift most of the cast — but by less than I first
  wrote.** The game has 83 named characters, 23 hand-written and 60 generated.
  Running the new validator over the old 60: every one fails, and **all sixty
  fail on exactly one rule — no example lines.** Nothing else. No adjective-soup
  speech, no anachronism, no structural fault. So "72% of the cast is at the old
  bar" overstated it; the accurate version is that 60 cards are one field short.
  Worth doing — the coverage curve says the generated sixty are most of who you
  actually meet — but it is a small, targeted run rather than a rescue.
- **What the audit cannot see: period texture.** There is a rule against
  anachronism and none for *presence* of a decade, because absence is not
  greppable. Those 60 cards still have no phone box, no tick at the shop, no
  pools coupon. That half stays a judgement call and it is the half that would
  actually be worth the tokens.

## Standing rules this file exists to serve

- **Dispatch, then immediately take item 1 of Now.** A build in flight is a
  reason to switch tasks, never a reason to stop.
- **Batch Game-layer changes.** Five round trips today carried two or three
  files each and answered one question each. They can now run in parallel —
  each build keeps its own verdict under `sim-shots/runs/<sha>.txt` — so
  dispatch the hypotheses together instead of in series.
- **Prefer a local answer.** `Recurrence` links real Core and answers in two
  seconds what a round trip answers in twenty-eight minutes. Before dispatching,
  ask whether the question is actually about Unity.
