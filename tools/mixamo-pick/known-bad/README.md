# known-bad — the rejecting case, kept where a re-pick cannot reach it

**LOG — 21 August 2026. NOT CURRENT as a description of the shipped clips; it
is a description of these four files, which never change.**

Four real Mixamo clips whose CONTENTS disagree with their names. Every one was
shipped in `ledger/Assets/Characters/` until 21 August, when the posture and
travel screen caught it and Jafar's re-pick replaced it. They are kept here so
the screen keeps having something to reject.

## Why they are copied rather than read out of git history

`pick_animations.py --selftest` asserts both outcomes of the screen. The
accepting half points at the shipped clips, which is right — if a future
re-pick lands a bad clip, that half must go red.

The rejecting half used to point at the shipped clips too, and that was wrong
in a way that only showed up once the guard *worked*. It named six slots and
asserted the screen refused them. The re-pick fixed five of the six, so five
assertions went red for the best possible reason, and the only reason the
sixth still passed is that `lie_still` found no replacement and its old bad
file stayed on disk. Fix that slot and the rejecting half tests nothing at
all — while still printing `SELFTEST PASSED`, because a loop over slots that
are all absent is a loop that runs zero times.

That is rule 5b's corollary: a guard needs a run in which the thing it asserts
CAN happen, and the fix is to PLANT the condition rather than loosen the bound.
These files are the planted condition.

They are copied into the tree rather than fetched from `7fdd095^` with
`git cat-file` because **the CI checkout is shallow**. A test that depends on
git history is the build-ordering guard that could never succeed, written a
second time.

They are real harvest files rather than synthetic bytes because the whole
fault being screened for is that a file's contents disagree with its name, and
only a real file has contents.

## What each one is for

One per branch of `posture_ok`, so a broken axis cannot hide behind a working
one. Readings taken 21 August with `tools/clip-motion.py`; `FLOOR_CM = 39`,
`TRAVELS_MIN = 0.15`, `STILL_MAX = 0.50`.

| file | asked as | hips lo/med/hi | travel | branch it fires |
|---|---|---|---|---|
| `walk__Walking_2dee24f8…` | `walk` | 93 / 95 / 95 cm | 0.00 m | motion, a locomotion slot holding a clip that stays put |
| `laugh__Laughing_2dee24f8…` | `laugh` | 93 / 98 / 103 cm | 1.63 m | motion, a standing slot holding a clip that goes somewhere |
| `jog__Jog Forward_4f5d21e1…` | `hands_up` | 7 / 7 / 7 cm | 0.00 m | hips, `upright` wanted and the hips are on the floor |
| `walk__Walking_2dee24f8…` | `lie_still` | 93 / 95 / 95 cm | 0.00 m | hips, `floor` wanted and the hips are upright |
| `fall_stairs__Falling From Losing Balance_2dee24f8…` | `collapse` | 55 / 94 / 100 cm | 0.00 m | falls, it never gets from standing to the floor |

Two of them are asked under a slot name that is not their own, and that is
deliberate. `posture_ok` runs the motion axis FIRST, so a clip cannot reach the
hip axis under a slot the motion axis already rejects — the real `jog` clip
travels 0.00 m, so asking it as `jog` fires the motion branch and the 7 cm hips
are never looked at. `hands_up` is upright, and in neither `GOES` nor `STAYS`,
so it is the question "would an upright slot take this body". The one file
doing double duty is the same reason in the other direction.

## Do not

- **Do not replace these when a re-pick runs.** Nothing in the picker writes
  here, and that is the point.
- **Do not "fix" one because it is a bad animation.** Being bad is the job.
- **Do not add a fifth without saying which branch it fires**, or it is a file
  nobody can tell is load-bearing.
