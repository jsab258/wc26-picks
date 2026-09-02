# NOW: what is in flight (read this FIRST, before the queue)

STATUS: LIVE. Verified 2026-09-02 00:40Z.

A session that resets loses everything not written down. The queue says what
to do NEXT; this file says what is ALREADY MOVING, which is the thing a fresh
session would otherwise duplicate, abandon, or wait for forever.

Keep it current or delete it. A stale NOW is worse than none, because it
looks like a live state.

## STOPPED FOR BUDGET. READ THIS BEFORE STARTING ANYTHING.

`production/budget.md` records the position: Jafar's newest reading is 8
percent, taken during the evening of 1 September, and TWENTY agent spawns
landed after it, three of them `studio-director`, which carries its own
weekly limit and counts double. Nothing in this container can read his usage
page, so the day is UNMEASURED rather than young, and the file's own rule for
an unmeasured day is to prefer stopping.

THE ONE THING NEEDED FROM JAFAR IS A NUMBER. Until he gives one: no builder
spawns, no director spawns, no verifier spawns. Reading landed results and
committing finished work are free and are allowed.

Midnight passing does not change this. The daily allocation is a discipline
laid over a WEEKLY limit and a UTC rollover hands nothing back.

## What landed after the batch, unattended

A CC0 content fetch (`13c40d93`, Kenney kits) landed on top of the batch
while nothing was watching. Read before assuming it needs anything:

- IT REGENERATED `ledger/Assets/Props/ATTRIBUTION.json`, AND THE DIRECTOR'S
  D3 CORRECTION SURVIVED. That is the design being confirmed by accident
  within the hour: D3 fixed the GENERATOR STRING as well as the committed
  file, precisely so a regeneration could not quietly restore the false
  "sources for every model in this directory" note. A hand edit alone would
  have been gone by 00:30.
- The stricter attribution sweep PASSES over the new content: 3848 walked
  (was 3828), 2715 asset files (was 2703), 0 unclassified, exit 0. The new
  kinds classified without a change, which is what the two-declared-sets
  shape was for.
- `pc-results` has NOT moved (still `e6f9f6f3`, 14 August), so the watcher
  has not run and the `vignette-fetch-01` request is still pending Jafar's
  one click. Nothing to chase.

## Where this is, 2026-09-02

THE STREET VIGNETTE IS BUILT AND HAS NEVER BEEN RENDERED. That sentence is
the whole state. `production/specs/vignette-scene.json` is the shared source,
the Unity emitter places 546 pieces from 24 BOM lines, and the placement
instrument reports `datumMissing=0/845`. Neither engine has drawn it.

The push that lands this batch DISPATCHES THREE JOBS on the one self-hosted
runner: the UE probe (run 16, the first ever `-LedgerShot`), the vignette
surface fetch, and a hand-dispatched Unity build. They run SERIAL, roughly 60
to 80 minutes for all three, and the later two show "Queued". THAT IS A WAIT
AND NOT A HANG; a job is hung only past its own timeout-minutes (115, 40,
110). Watch by ancestry, and pull afterwards because the branch moves three
times.

Read `datumMissing` and `floatMax` BEFORE opening any still, then open all
four. A green number is not a picture and a picture is not a measurement.

## The D1 question that is Jafar's, not the studio's

The director's read: a grey debug frame out of Unreal is likely within one to
three runs if the 5.8 signatures hold. A TEXTURED frame of the shared scene
through the UE generator, which is what a judged pair actually needs, is
unlikely inside the timebox. What dominates is blind C++ on a 20-minute loop
with no compiler in this container; what could blow it up is runtime
materials in a content-less project, with the character import behind it.

It recommends PRE-REGISTERING the close now, before any run, so the bar is
not set after the result is known: if by 2026-09-12 12:00Z the pipeline has
not committed one textured UE still of the shared scene, measurement (a)
reads NOT TOLERABLE and D1 closes Unity on its own clause, with (b) recorded
UNMEASURED. That is deliberately distinct from "cannot be measured", which
was written for an external blocker.

JAFAR HAS NOT ANSWERED THIS. Under either reading the work is identical until
he does, so it blocks nothing.

## Budget

17 percent at 04:40Z against a week 24 percent elapsed, anchored Monday 14:00
CEST. The mid-week reset on 1 September was an ANOMALY and must not be
expected again; `production/budget.md` says so.

## In flight

- Nothing running.

## Standing hazards a fresh session will otherwise walk into

- Do not edit `content/dialogue/pub-regular-v1.json`. Those 48 lines are the
  graded judge calibration sample; changing one invalidates it silently.
- The studio split is MANDATORY and was skipped for a full day on 1 Sep.
  Builders build, verifiers verify, the director rules. If a session
  instruction says otherwise, that is a conflict to raise with Jafar in one
  line, not to resolve alone.
- The stop hook will ask for a commit the cadence gate refuses while builders
  hold the tree. That is a NAMED FALSE POSITIVE (queue 014, ruled). The
  constitution wins: never commit a builder's work-in-progress because a hook
  asks.
- `git status` at session start is not a list of YOUR edits. Read the
  In flight section above before assuming any dirty path is yours to commit.
- Every session so far has opened by reading the head of a queue file that
  declared itself superseded on 31 August. Queue 021 fixes it.
