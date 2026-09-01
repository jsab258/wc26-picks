# The status dashboard

STATUS: LIVE. Verified 2026-09-01.

    python3 tools/dashboard/build-dashboard.py            # write the two artifacts
    python3 tools/dashboard/build-dashboard.py --selftest  # accepting case first
    python3 tools/dashboard/build-dashboard.py --print     # STATUS.md to stdout, write nothing
    open-dashboard.bat                                     # Windows: rebuild, then open

A read-only lens over repo state. Deterministic, no model calls, and it
writes exactly two files: `dashboard.html` and `STATUS.md` at the repo root.
One model is read once and rendered twice, so the page and the markdown
cannot disagree with each other.

## The rule that governs it

The dashboard is DERIVED STATE. If a number on it is wrong, the source file
or this generator is wrong, and the page is never the place to fix it. Chat
is never a source of state. That rule is in `ledger-v2/studio-v2/operations.md`
and the weekly process audit checks it.

## Why the honesty machinery is not decoration

A dashboard is read at a glance, so it is the highest-leverage place in this
project to print the fault the project keeps paying for: a zero that means "I
could not find out" reading as a zero that means "fine".

- Every number is a `Reading`: MEASURED with its one-line derivation and the
  denominator of what was examined, or UNAVAILABLE with the reason. There is
  no third state, and an unavailable reading cannot render as a number.
- `Reading.measured` refuses a zero with no denominator at construction, so
  the rule is not something a later edit has to remember.
- Sources that do not exist yet (night logs, a calibrated judge, a money
  spend ledger) render as "not yet applicable" with the paths that were
  checked. The budget bar for unmeasured spend is hatched, not a zero fill: a
  bar drawn at zero would claim a measurement nobody has taken.
- The derivation travels WITH the number, under each card, not only in the
  table at the bottom. An appendix nobody scrolls to is not where it belongs.
- Truncation comes from `tools/capsay.py`, the one implementation of that idea
  in this repo. `tools/gates.py` supplies the NO PLAYER LOG marker and the
  "did this verdict carry a gate outcome at all" test; `tools/verdict-read.py`
  supplies the verdict header stamp. None of the three is re-typed here.

## What it reads

Every path is listed in the `SOURCES` dict at the top of the generator and
printed at the bottom of both artifacts with `(ABSENT)` beside any that are
missing, so a moved file shows as an absent source rather than as a zero.

## The one write path

`write_artifact()` is the only function that writes, and it refuses any
filename other than the two artifacts. The selftest proves that two ways: an
AST walk over the generator (every filesystem-write call site is either that
function or the selftest's own temp fixture) and a live generation into a
temp directory that must create exactly two files and leave the tree it read
untouched.

## Exit codes

    0  wrote both artifacts, or printed
    1  the selftest failed
    2  a write failed
    3  the given root does not look like this repository
    4  tools/capsay.py could not be imported, so no truncation on the page
       could announce itself; it refuses to run rather than print a cap that
       does not say it bit

## Regeneration, and which parts have been watched run

Three points, per the spec:

1. The `SessionStart` hook (`.claude/hooks/session-start.sh`) regenerates and
   prints the top of `STATUS.md`. Runs here.
2. The night runner (`tools/runner/run-night.ps1`) regenerates at the end of
   every iteration. NOT RUN HERE: this container has no PowerShell, so its
   first Windows night is that line's accepting case.
3. `open-dashboard.bat /register` creates a Windows scheduled task that
   rebuilds every 15 minutes. NOT RUN HERE: no Windows, no `schtasks`.

The page prints its own age at the top and turns that line red past 20
minutes, so a regenerator that has stopped shows up on the page it stopped
regenerating instead of leaving a stale page looking current.
