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

1. **Read the build on `4f3a42c`** *(CI, in flight)* — `importerRan`,
   `companionSight dist=`, `textMirrored`, `worstTextHeightFrac`.
2. **The player is on his back in the road.** The bracket named the stage — the
   avatar's retarget inverts the body between the scaled bind pose and the
   solve. Next probe goes in the same batch as anything else Game-layer. *(CI)*
3. **Period texture and example lines for the Tier-2 ring.** The core four have
   them; the ambient cards do not. Authored, free, no round trip. The higher-
   leverage half is the *generator* prompt in `Tier2Gen` — one change reaches
   every card it will ever write, rather than six by hand.
4. **Per-skinned-character frame cost.** The third owed measurement, and the one
   that bounds the cast tiering from the runtime side. `Recurrence` says what
   the design wants; nothing yet says what the frame budget allows. *(CI)*

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
