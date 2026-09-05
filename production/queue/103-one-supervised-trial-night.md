line: production (the night rhythm)
spec: production/NOW.md, "JAFAR'S STANDING ORDER, 2026-09-05", item 8
acceptance: the STOP file is proven on BOTH outcomes before the night starts (present, the loop exits at its check having spawned nothing; absent, one iteration runs), then one night runs unattended against a queue named in the ruling that authorises it, and a morning report lands on a TRACKED path naming per iteration what ran, what landed and what broke, with iterationsRun=N/maxIterations, itemsLanded=K/Q queued, and a budget reading at each end carrying both meters; a night the runner never started produces a report reading iterationsRun=0 and the words "nothing measured" rather than no file; and the first iteration is watched end to end before the machine is left alone
max_sessions: 1
status: READY 2026-09-05. Item 8. BLOCKED until queue 094 lands. instrument-builder to prepare, Jafar's PC to run.

## The claim in the order, checked rather than repeated

`production/logs` does not exist in this checkout: a glob over
`production/logs/**` matched 0 paths. But the interesting half is why that
proves less than it looks. `.gitignore` line 96 is `production/logs/`, and
`tools/runner/run-night.ps1` writes its per-iteration logs to
`production/logs/night-<date>/iter-NNN.log`, so a night that ran perfectly
would still leave that directory empty HERE. The emptiness is guaranteed by the
ignore rule and is not evidence about whether a night ever ran.

What is evidence: the runner also writes a fallback brief named
`night-<YYYYMMDD>.md` into `production/briefs/`, and 0 of the 4 files in that
directory carry that name. Not checked in this pass, and worth checking first:
whether any `night/*` branch exists on the remote.

AND THE SCRIPT HAS NEVER RUN WHERE IT WAS WRITTEN. Its own header says this
container has no PowerShell, that the verify footer names that lint NOT
CHECKED, and that the first Windows run is its accepting test and should be
watched end to end. This task IS that first run.

## What supervised means here

The first iteration is watched from start to finish: the checkout, the spawn,
the session's own commit, the dashboard rebuild, the push. Only then is the
machine left alone. A script whose accepting case has never run is not left
unattended for nine hours on the strength of a reading of its source.

## Two things that will otherwise eat the night

- A SESSION LIMIT BURNS ITERATIONS. The loop logs a non-zero exit and goes
  straight round again, so a limit hit at iteration 3 spends the rest of the
  night spawning into a closed session. That is queue 094 and it is why this
  item is blocked on it.
- A NIGHT THAT LANDS UNREVIEWED WORK CANNOT COMMIT IT. `director_cadence`
  refuses a commit of builder work no ruling covers. So the ruling that
  authorises the night names the queue AND covers the batch, or the morning
  finds finished work stuck behind the gate, which is the 2 September incident
  with 5294 uncommitted lines.

## The queue for the night

Named in the ruling, small, and every item on it sized to one session with an
acceptance a machine can check. No item that touches the roadmap, CLAUDE.md or
the premise, because each of those is a mandatory director trigger and a
director is not what an unattended night is for.

## Both halves, accepting first

Accepting: the night runs and the report names what it did.

Rejecting, two cases: `production/STOP` present, where the loop must exit at
its check having spawned nothing, which is the kill switch tested on the case
it should refuse; and a night that never started, where the report says
`iterationsRun=0` and "nothing measured". An absent report reads as nobody
having tried, and that is the state this item exists to end.

## Depends on, and what it blocks

Depends on queue 094 (the limit sleep) and on the ruling that names the night's
queue. Reaches him through queue 089 if that has landed, and is a committed
file either way. Blocks nothing, but the night rhythm stays UNPROVEN until this
runs, and every plan that assumes overnight throughput rests on it.

## THE UNRUN CHECK, RUN BY THE RESIDENT 2026-09-05

`git ls-remote --heads origin "night/*"` returns NOTHING, against 4 heads on
the remote in total. So no night branch has ever existed and no night has ever
run, which is the premise of this item confirmed rather than repeated. Note the
denominator: 4 branches examined, 0 of them a night branch.

That makes this item's first run its ACCEPTING CASE in the strong sense: there
is no prior run to compare against and no log to read, so whatever it does is
the first evidence the night rhythm exists at all.
