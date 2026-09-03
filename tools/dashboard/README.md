# The status dashboard

STATUS: LIVE. Verified 2026-09-01.

    python3 tools/dashboard/build-dashboard.py            # write the two artifacts
    python3 tools/dashboard/build-dashboard.py --selftest  # accepting case first
    python3 tools/dashboard/build-dashboard.py --print     # STATUS.md to stdout, write nothing
    python3 tools/dashboard/build-dashboard.py --emit-json       # + the live document
    python3 tools/dashboard/build-dashboard.py --emit-live-page  # + the live page
    python3 tools/dashboard/build-dashboard.py --checkout refresh # pull --ff-only FIRST, then build
    open-dashboard.bat                                     # Windows: update, rebuild, then open

A read-only lens over repo state. Deterministic, no model calls. A bare run
writes exactly two files: `dashboard.html` and `STATUS.md` at the repo root.
One model is read once and rendered twice, so the page and the markdown
cannot disagree with each other.

## The live page, added 2026-09-01 because the hosted page was a snapshot

Published to a host, `dashboard.html` froze at publish time and went on
looking current. That is worse than no page: a stale number with a fresh
frame around it is a false claim nobody can see. The repair is a document
store the page subscribes to.

- `--emit-json` writes `tools/dashboard/live-dashboard.json`: the SAME model
  as one JSON document, at schema `ledger-status/1`. The JSON and the local
  HTML are two renderings of one computation, and the selftest checks every
  reading's text and derivation is identical across them, value by value.
- `--emit-live-page` writes `tools/dashboard/live-dashboard.html`: the page
  that renders that document. It calls `claude.use("db")`, reads
  `status/current`, and subscribes with `onSnapshot`, so it updates in front
  of a viewer with no reload and no republish.
- Neither is written by a bare run, and each has one fixed name. The selftest
  counts the files a real generation leaves on disk in both directions.
- The resident publishes the page and writes the document. This generator
  does neither.

### The live page contains no numbers, by construction

`render_live_page()` takes no model. There is no argument for a reading to
arrive through, so a copy of the numbers frozen at publish time cannot get
into it even by accident, which matters because frozen numbers look exactly
like fresh ones. The selftest renders it once and asserts that not one of the
live repository's 124 candidate reading strings appears in its bytes, and
proves the check is not merely refusing everything by flagging a fixture with
one deliberately baked in.

When the store is empty the page says the feed has never been written and
names the path and the command that would fill it. When `claude.use("db")`
resolves null it says the capability is unavailable and shows nothing. It
never shows a number it did not just receive.

### Staleness, and the timestamp fault it is built around

The document carries three fields for one instant: a human stamp, an ISO
string with its OFFSET, and an epoch integer. The page does its arithmetic on
the integer. A naive timestamp is read by a browser as the VIEWER's own local
time, so a writer in UTC and a viewer at +02:00 turn a document written two
hours ago into one written two hours in the future: the age goes negative,
"just now" prints, and a feed that has stopped looks live for exactly the
offset between the two clocks. The page also calls out a stamp ahead of the
browser's clock rather than smoothing it, and re-times the age on an interval
so a stopped feed goes on ageing in front of the reader.

### What was actually run here, and what was not

`node` runs the emitted page's own script against a DOM shim through twelve
states: no host, no db, a rejected `use()`, an empty store, an unreadable
schema, fresh, hour-old, future-stamped, unstamped, cached, a subscription
that dies before any document, and one that dies after one arrived. Six of
those cannot be produced by hand on the real page. When node is absent the
selftest prints NOT RUN with the reason and passes nothing.

Nothing here renders the page. Layout, contrast, the `[data-theme]` cascade
against the host's real attribute and the real db capability are first-load
questions on the published artifact.

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
filename outside the four it knows. `generate()` is the one write SEQUENCE,
called by `main()` and by the selftest rather than copied into either. The
selftest proves the scope two ways: an AST walk over the generator (every
filesystem-write call site is either that function or the selftest's own temp
fixture) and live generations into a temp directory, one with no flags that
must create exactly the two artifacts and one with both flags that must
create exactly those two plus the two named live outputs, neither leaving
anything in the tree it read.

## Exit codes

    0  wrote both artifacts, or printed
    1  the selftest failed
    2  a write failed
    3  the given root does not look like this repository
    4  tools/capsay.py could not be imported, so no truncation on the page
       could announce itself; it refuses to run rather than print a cap that
       does not say it bit
    5  the live document is over the store's 256 KiB per-document cap, so
       db.set() would reject it; it refuses rather than leaving a file on
       disk that looks ready to publish

## Regeneration, and which parts have been watched run

Three points, per the spec:

1. The `SessionStart` hook (`.claude/hooks/session-start.sh`) regenerates and
   prints the top of `STATUS.md`. Runs here.
2. The night runner (`tools/runner/run-night.ps1`) regenerates at the end of
   every iteration. NOT RUN HERE: this container has no PowerShell, so its
   first Windows night is that line's accepting case.
3. `open-dashboard.bat /register` creates a Windows scheduled task that
   updates and rebuilds every 15 minutes. NOT RUN HERE: no Windows, no
   `schtasks`.

The page prints its own age at the top and turns that line red past 20
minutes, so a regenerator that has stopped shows up on the page it stopped
regenerating instead of leaving a stale page looking current.

## How old the CHECKOUT is, added 2026-09-02, which is a different fact

The page said how old THE PAGE was and could not say how old THE FILES it read
were. A decision card was pushed, the resident said it was on the dashboard,
and Jafar's copy had never seen the commit. Worse, a registered refresh
repaints that staleness every quarter hour, so the page looks more alive the
further behind it falls.

`--checkout refresh` fetches, runs `git pull --ff-only`, and only then builds,
so the page is rendered from the files the pull brought in. The launcher passes
it on every run. Never a bare `git pull`: --ff-only moves the branch pointer or
refuses, can never make a merge commit and never opens an editor, which is the
26 August incident that put the old "no git here" rule in the launcher's
header. The rule kept from it is NEVER MERGE UNATTENDED. A refused
fast-forward is reported and never resolved.

- MEASURED reads `level with origin/<branch> (0 commit(s) behind)` or
  `N commit(s) behind origin/<branch>`, with the exact command and the two
  commit ids in the derivation. Level is a measurement.
- UNAVAILABLE carries the reason and no number at all: no git, a detached
  HEAD, a failed fetch (git's own words, including the no-network case), a
  refresh held because a build is running, or a rebuild that was not asked to
  check. "I could not find out" must never print as zero.
- Two gates stop a pull moving files under a running CI job, because
  `ledger-pc` is Jafar's PC AND the self-hosted runner. A checkout inside the
  runner's `_work` tree gets no git at all, not even a fetch; a build running
  on the PC holds the pull but still allows the fetch, so the number stays
  measured while the tree stays still. The evidence that the two clones are in
  fact different directories is quoted in `runner_work_tree()`.
- Both fixtures run in the selftest, accepting case first: a real clone level
  with a real origin, then one deliberately put a commit behind, plus a
  diverged clone whose fast-forward is refused and a fetch that cannot reach
  its origin. NOT RUN HERE: the Windows-only `Runner.Worker.exe` probe, which
  returns could-not-tell off Windows.
