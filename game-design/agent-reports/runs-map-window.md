> **STATUS: LOG, 2026-08-26. NOT CURRENT after the next change to
> `ledger/verify.py`'s `runs_map_to_commits`.** What the commit footer's
> run-placement fraction was measuring, what it measures now, and the
> selftest both ways. Counts are from the tree at `b63e271f` (356 run files,
> 2403 commits); re-run the commands rather than quoting the numbers.

# The commit footer's `runs map to commits` was measuring its own window

## What the line read before

Every commit message this project has produced since 24 August carries a
verify footer, and inside it:

    runs map to commits (108 of 356 within 400)

108 of 356 is 30%. Nothing on that line says whether 30% is health, alarm, or
arithmetic — so it has read as health for weeks. It is the same fault the
`gates.py` audit found in `ordered_runs()`: `git log --format=%H -400` on a
2403-commit repository.

**Measured, not reasoned.** Coverage of the 356 run files by window size:

| window | runs placed | share |
|---|---|---|
| 100 | 22 | 6% |
| 200 | 63 | 18% |
| **400** | **108** | **30%** |
| 800 | 192 | 54% |
| 1200 | 226 | 63% |
| 1600 | 324 | 91% |
| 2000 | 356 | 100% |

The oldest run file sits at commit index **1707**, so any fixed window under
1708 was already wrong the day it was written, and every window rots as the
repository grows.

## The landed series, which was in the commit feed all along

73 footers carry this reading. Harvested with
`runs map to commits \((\d+) of (\d+) within (\d+)\)` over `git log --format=%B`,
oldest first, every sixth reading:

    numerator   123  125  123  122  122  122  121  119  116  114  111  109  108
    denominator 335  339  339  340  343  345  347  349  350  351  351  352  355
    window      400  400  400  400  400  400  400  400  400  400  400  400  400

**The numerator falls while the denominator rises** — 37% down to 31% over two
days. A number that goes DOWN as the corpus goes UP is measuring the window
closing, not the corpus. No single footer could show that, because nothing on
the line said what the number should be. This is the series the rule asks for,
and it existed before the bound did; what was missing was a referent.

## What the line reads now

    runs map to commits (356 of 356 within 2403) — the whole history, no window;
    expect all 356; unplaced=0; NOTE abbrev is 8 chars and run files are 7 —
    compare by PREFIX, never by equality

(one line in the footer; wrapped here). And with runs that cannot be placed —
this is the rejecting fixture's real output, not an invented sample:

    runs map to commits (2 of 7 within 50) — the whole history, no window;
    expect all 7; unplaced=5 NOT COUNTED ABOVE, on no commit in this history:
    0badbad,1badbad,2badbad,3badbad (+1 more of 5)

Three things it did not carry:

1. **The window is the whole history, and it is also faster.** `git log
   --format=%H` with no `-N` is **49ms** for 2403 commits. Timed on this tree,
   the placement itself: the old nested loop (`for full in log for stem in
   stems`) took **8.5ms to place 108 runs** out of a 400-commit window; the
   dict in `place_runs` takes **0.7ms to place 356** out of all 2403. The
   window bought nothing it was supposed to buy — 12x slower for a third of
   the coverage.
2. **An expected value beside the fraction.** `expect all 356`. Every run file
   is named after a commit CI checked out, and CI commits its stills on top of
   that commit, so the named commit is an ancestor of HEAD by construction. The
   numerator SHOULD equal the denominator. That is the referent a bare fraction
   was missing — rule 3b's sibling.
3. **What happens to the unplaced.** `unplaced=N` in **both** states, so a grep
   for `unplaced=` gets a number when there is a problem rather than nothing;
   and when it is non-zero the stems are named, capped, with the cap announcing
   its bite.

## What happened to the unplaced runs — and how it differs from `gates.py`

`gates.py` sorted them by SHA and mixed them into the evidence, defended in
prose as a kindness. **This function did something quieter: it did not order
anything at all, so the 248 unmatched runs were simply absent from the
numerator and nothing said so.** No fallback, no bucket, no sentence — the
count just stopped at 108 and the line still called itself "runs map to
commits".

The docstring is the finding's second half. It already contained, about the
six OTHER tools:

> unmatched runs fall into a fallback sorted by SHA, which is sorted by
> nothing, and every tool kept printing plausible numbers

That sentence is **true and correctly diagnoses the disease**, and it sat six
lines above a `-400` that had the same disease in a quieter form. It is kept
verbatim and corrected underneath rather than deleted, so the next reader
cannot re-derive it: the paragraph is right about the six tools and was blind
to its own line.

**`unplaced` is printed, not gated.** It reads 0 today and has no landed series
above zero, so any bound would be invented (rule 2). The honest non-zero causes
— a rebase, a force-push, a run file copied in by hand, the container rolling
this checkout back — all need a person to look, and failing the commit would be
a ratchet against the very commit that fixes them. The hard failure stays where
it has a real rejecting case: `hit == 0` is the 24 August incident, when `%h`
grew to eight characters and 0 of 333 matched.

Two smaller repairs in the same function:

- **The numerator now counts the same unit as the denominator.** The old
  `sum(1 for full in log for stem in stems if full.startswith(stem))` counted
  (commit, stem) PAIRS from the log side against a denominator counting FILES.
  Zero 7-character prefix collisions in 2403 commits today, so they agree — but
  they were two quantities printed as one fraction.
- **A git that could not look no longer reads `runs ok`.** It now prints
  `runs map to commits nothing-measured (N run file(s) on disk, git log gave no
  history to place them against)`.

## One implementation of the placement

`tools/gates.py::place_runs` is the same idea, written PURE so a test can drive
it, and repaired for this exact window on 26 Aug. `verify.py` now **imports**
it rather than keeping a second copy — the shape this project has paid for with
`SpeechBubble`/`NpcWalker` and `verdict-keys`/`gates`. The import is lazy and an
import failure is RED and names the file (`RUNS-MAP CHECK BROKEN:
tools/gates.py::place_runs would not import ...`), so a broken `gates.py`
reports rather than killing every verify run with a traceback at module load.
`tools/gates.py` was not edited.

## The selftest, both ways — ACCEPTING FIRST

It lives in `_strings_selftest`, which `footer_strings()` runs **inside every
verify run** (it is second in `main`'s tuple), not behind a flag. Suite went
**27 -> 35 fixtures**. `python3 ledger/verify.py --selftest-strings`:

    ok   runs map: 8 runs spread over 500 commits read 8 of 8 within 500, with an expected value beside the fraction and the unplaced count
    ok   runs map: the git log asks for NO -N window — the ONE assertion that fails against the pre-repair function (it passed `-400`)
    ok   runs map: the shared placement puts 8 of 8 on the full log and 5 of 8 on a 400-commit slice — the window's bite, as a number
    ok   runs map: an 8-char abbrev against 7-char stems still warns
    ok   runs map: 5 runs on no commit are counted, named, and the cap says it bit — the silence here is what hid 248 of them
    ok   runs map: total divergence is RED and ships both counts — the 24 Aug incident, where %h grew to 8 chars and 0 of 333 matched
    ok   runs map: a git that could not look reads nothing-measured with its denominator, not `runs ok`
    ok   runs map: losing the ONE shared placement is RED and names the file, not a traceback at import that would block every commit
    footer-string selftest: 35 passed, 0 failed        (exit 0)

The **live corpus is the accepting fixture**: `runs_map_to_commits()` runs for
real against the real runs directory and the real git log in the same process,
every verify run, and reads `356 of 356`. Every synthetic stem above
(`0badbad`, `1badbad`, ...) is invented and exists in no repository, so landing
another real run cannot turn any of these red.

### The probe was checked against the broken code, because a probe that cannot tell them apart tests nothing

The pre-repair function was spliced back under the **new** fixtures, on a
symlink mirror of this tree so the other checks see the real repository:

    FAIL runs map: 8 runs ... — runs map to commits (8 of 8 within 500)
    FAIL runs map: the git log asks for NO -N window — git -C /tmp/verify-runsmap-udlrfo3o log --format=%H -400
    FAIL runs map: 5 runs on no commit are counted, named ... — runs map to commits (2 of 7 within 50)
    FAIL runs map: a git that could not look ... — runs ok (1 file(s), no git history to check against)
    FAIL runs map: losing the ONE shared placement ... — runs map to commits (1 of 1 within 50)
    footer-string selftest: 30 passed, 5 failed        (exit 1)

**The argv fixture is the one that catches the window itself, and it is the
only one that can.** A stubbed `run` hands back the same log whatever window
the caller asked for, so a fixture reading only the OUTPUT scores identically
against `git log -400` and against the full history — it would test nothing.
That is this file's own recorded failure (the prefix guard that passed "122
hits either way" against the exact broken state it was written for). The window
is visible in the ARGV alone, so `_runs_map_on` returns the argv, and the
fixture's evidence line is the smoking gun above: `log --format=%H -400`.

Two of the eight pass against the broken code on purpose — the shared-placement
contract and the abbrev warning are regression assertions that must hold both
ways. `_fake_log(n)` asserts its own log is **not** in sha order, so an ordering
fixture cannot accidentally make sha order equal commit order.

## The parse trap: how I established the parse still holds

**No code anywhere parses this line.** `grep -rIl "map to commits"` over the
whole repository returns exactly two files: `ledger/verify.py` and one agent
report. Nothing in `tools/`, `.github/`, `.claude/` reads it.

The real consumer is the **landed series in the commit feed**, harvested with
`runs map to commits \((\d+) of (\d+) within (\d+)\)`. My first draft put the
new clauses INSIDE the bracket —
`(356 of 356 within 2403, the whole history and expect all, unplaced=0)` — and
**that regex stopped matching**, checked and caught before this was written up:
the series that proves the fault would have been unreadable from the commit
that fixes it. The bracket now closes exactly where it always closed and
everything new is added beside it. Proof, harvesting 73 landed footers plus the
live line into one series:

    LAST TWO (the repair, adjacent in one series):
      ('108', '355', '400')  ->  ('356', '356', '2403')

Read that series as **two regimes**, not one trend: the window column is 400 for
73 readings and 2403 after, so the numerator's jump from 108 to 356 is the
instrument changing, not the corpus. The window column is in the tuple so a
reader can see the break rather than infer it.

## Verify, and the footer read from `ledger/.verify-footer` on disk

`ref_bench` was reported red when this work started and it is **not red now** —
`108 ref-bench checks (0 failed)` — so the other agent's accepting-fixture
repair landed while this ran. Nothing here touched it, `tools/ref-bench.py`,
`tools/gates.py`, `tools/gate-detail.py` or `ledger/Assets/**`.

`python3 ledger/verify.py` -> **exit 0, GREEN**, and `ledger/.verify-footer`
was written (3950 bytes on disk; the footer string is 3937 characters). Read
from the file, not from scrollback:

    $ ls -l ledger/.verify-footer
    -rw-r--r-- 1 root root 3950 Aug 26 03:08 ledger/.verify-footer

The fragment this work changed, verbatim from that file:

    runs map to commits (356 of 356 within 2403) — the whole history, no window; expect all 356; unplaced=0; NOTE abbrev is 8 chars and run files are 7 — compare by PREFIX, never by equality

and its neighbours, also from the file:

    35 footer-string fixtures (accepting and rejecting)      (was 27)
    108 ref-bench checks (0 failed)                          (the other agent's, now green)
    docs 113/113 clean
    4104 CoreTests.

**Not committed** — `ledger/verify.py` is the only file changed, plus this
report.

## The twin, greped for and NOT fixed (not my file)

Rule 1's third corollary: the moment a fix works, grep for its distinguishing
token. `grep -rn '"log"' --include=*.py` over `tools/` and `ledger/` for a
numeric cap finds a **third site of the same `-400`**:

    tools/verdict-keys.py:247    ["git", "log", "--format=%H", "-400"]

It is **not currently wrong**, and the difference is worth stating rather than
just flagging: `verdict-keys` walks the log newest-first and stops at the FIRST
placeable run, so it needs coverage of the recent past, not of the corpus. It
works today — `verdict-keys: 1190 always + 0 gate-only present, 1075 required,
0 missing, 115 new`. The latent failure is narrow: if a long enough unbroken
stretch of the newest runs were all `no-sim` or truncated, it would exhaust the
400-commit window and report "no run file matches any recent commit" while
older placeable runs sat on disk — a nothing-measured wearing a finding's
clothes, the same family. Reported, not touched; it is another agent's file
and the fix is one argument.

`tools/report-frame.py:106` uses `-40`, but path-limited (`-- <rel>`), which is
a different quantity: 40 commits that touched that path. Left alone.
