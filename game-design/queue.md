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
3. **Confirm the three new numbers report at all.** `fewestChips` (input
   parity), `rigsMs` with the skinned bone and vertex counts (cast tiering),
   and the relocated `worstNameFrac`. A metric that never prints is the shape
   this project ships most often. *(CI)*
4. **`worstTextHeightFrac` is now `worstNameFrac`** — a deliberate rename, so
   the key check will report the old name gone on the next verdict. Run
   `verdict-keys.py --learn` then, not before.

## Next

5. **Tier the cast.** The last open piece of M20, and now the only one bounded
   from both sides: a full week gives 47 distinct faces and 13 near enough to
   read at three districts, the witness engine needs about twenty near an
   event, and the geometric load per character is being measured this build.
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
- **And the same spend would lift most of the cast.** Counted rather than
  assumed: the game has 83 named characters, 23 hand-written and 60 generated,
  and **0 of the 60 carry example lines or any period texture** — they predate
  both. That is 72% of the cast at the old bar, against a measured knee of ~50
  people covering 92% of a resident's week, so those generated characters are
  not background: they are most of who you meet. Regenerating them through the
  new prompt and its eleven validator rules is one batch run, and it is the
  largest single lift available to the writing.

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
