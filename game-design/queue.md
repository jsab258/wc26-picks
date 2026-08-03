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

1. **Two builds in flight, and they are the first parallel pair.** A on the
   avatar probe and the rig cost, B on the no-clip twin. Read both
   `sim-shots/runs/<sha>.txt` when they land — and check that BOTH landed,
   because that is also the test of the parallel-build change itself.
2. **The player is airborne and splayed, not lying in the road.** The still says
   so and all sixty-eight other rigs stand correctly — but those are mannequins
   and `bodySkinned=1`, so the one retargeted body is the only broken one.
   Import is closed (`importerRan=44`); it is the clip or the avatar, and the
   twin decides which.
3. **Period texture and example lines for the Tier-2 ring.** The generator half
   is DONE — prompt, eleven validator rules, `--selftest` in `verify.py`. What
   is left is the six hand-written ambient cards, which the generator cannot
   reach. Authored, free, no round trip.
4. **`worstTextHeightFrac=0.210` and `textMirrored=58`.** A name taking a fifth
   of the frame height, and mirrored world text that got WORSE (was 46). Both
   are visible faults with numbers already on them. *(CI)*

## Next

5. **M19 input parity.** `DialogueUI` currently treats typing as the primary
   path. The decision is the inverse: playable end to end on a controller,
   typing and dictation always available and never required.
6. **M20 town you learn** — three districts, tier the cast, and days that
   differ. The last part is a real gap: `OutdoorsAt` and `OutdoorPosition`
   reduce the hour mod 24, so there is no day parameter anywhere in the routine
   model and every Tuesday in this town is every Saturday.
7. **M17.2 voices** — held behind the writing verdict, which is held behind one
   decision from Jafar (below).

## Blocked, and on whom

- **Judging the conversation as OUTPUT** needs a small API spend to generate
  sample exchanges, including adversarial ones. Nothing has been spent; every
  purchase is Jafar's. Raise at most once a day. The input-side verdict is in
  `writing-judgement-2026-08-03.md` and it was better than expected, so this is
  the cheap half of an open question rather than a rescue.

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
