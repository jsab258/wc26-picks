> **STATUS: LOG, 2026-08-26. NOT CURRENT after the next change to
> `tools/gates.py` or `tools/gate-detail.py`.** An audit of the project's
> series printer and its gate-detail ratchet, and what they were fixed to
> say. Counts are from the run files on disk at `c03ead22` (355, then 356
> when a build landed mid-audit); re-run the commands rather than quoting
> the numbers.

# `gates.py` — what its denominators actually counted

## What was examined, over what exists

- **355** run files in `game-design/sim-shots/runs/`, **0** empty; **356**
  by the end of the audit, a build having landed.
- **329** counted by the tool as measuring runs; **26** carry `NO PLAYER
  LOG` and are dropped.
- **1,408** verdict keys harvested by `--constant`; **528** rows inside
  **67** bracketed keys.
- All five subcommands run (`--series`, `--constant`, `--flaky`,
  `--pending`, default listing) plus `--selftest`, before and after.
- **71** gate-table entries in `SimDirector.cs` read for `gate-detail.py`.
- Every consumer searched with `git grep` across all tracked files.

## The finding, in one line

**70% of the corpus was ordered by SHA — that is, by nothing — and the
tool's headline feature is "newest first".** 248 of 355 run files fell
outside the `git log -400` window in `ordered_runs()` and landed in a
fallback bucket sorted by filename. 228 of 329 positions in the returned
list differed from true commit order. Nothing announced it.

## HOW FAR IT REACHES — the bound, stated first

**The SET was complete; only the ORDER was wrong.** All 355 stems exist in
HEAD's history and all 355 were returned. Nothing was dropped, nothing was
double-counted. That bounds the damage, and the bound matters more than the
fault:

- **The newest ~107 runs were in true commit order** — the first divergence
  is at index 101. Every reading checked against a landing run sat inside
  the correct window, so **recent readings survive**: a `newest` value, the
  `last 10` summary, `--flaky`'s live/quiet split at its 10-run boundary,
  and `--pending` were all computed from correctly-ordered runs.
- **`--constant` is a set operation and is order-independent.** Its
  question is "did this key ever hold anything but zero", which no
  permutation can change. Its findings — the 60 never-moved keys, the
  `inquiry` result, `summonsTaken=0` — are unaffected.
- **What IS at risk is order-dependent history past position ~107**: the
  shape of an old series, `last N run(s) ago` for a gate quiet longer than
  ~107 runs, and the position of any regime boundary.

**One landed conclusion needs a re-read, and this report does not
re-litigate it.** `CLAUDE.md` argues a regime break in `confabs` — 1–13
under the flat-road conversation rule, 29–74 under the junction one — from
reading that series. **The DISTRIBUTION of those values is unaffected**
(the set is complete, so every quartile and the all-time median stand).
**Any claim about WHERE the break sits may not be**, because that is
positional and the positions past ~107 were shuffled. It should be re-read
against true order by whoever owns that claim. It is not asserted here to
be wrong.

## Findings

### A. `ordered_runs()`: a 400-commit window on a 2,402-commit repository

It fetched `git log --format=%H -400` and appended every unmatched run
`sorted(have.items())` — by sha. Measured at `c03ead22`:

    355 run files, 2402 commits on HEAD
    107 matched into commit order
    248 fell off the window and were sorted by sha
    228 of 329 returned positions not in commit order; first divergence at 101

**What it did to real readings.** Adjacent-run volatility, printed against
true commit order, over series positions 100–135:

| key | mean \|step\| as printed | mean \|step\| true |
|---|---|---|
| `meanFrame` | 111.9 | 32.8 |
| `confabs` | 18.7 | 10.7 |

`confabs` at positions 100–135 printed `56 43 77 25 47 21 58 31 55 52 25 38
74 58 56 43 71 25 9 46 …` and is really `24 21 17 23 21 22 20 14 26 19 26
25 24 13 20 20 20 19 21 22 …` — a stable band around 20, shown as a 9-to-77
thrash. **The shuffle more than triples apparent instability** and smears
every regime boundary into noise, in the tool whose stated purpose is that
a reader can see the break by eye.

**The docstring is the finding as much as the code is.** The fallback was
justified in prose, and the justification is true and reasonable:

> *"a run that fell off the log is still evidence about the past, and
> silently discarding it would make the counts disagree with the runs
> directory for no visible reason."*

That sentence is correct about not discarding, and it is where 70% of the
evidence went — because keeping a run and being unable to place it are
different problems and the comment solved only the first. The same shape as
tonight's comment that put the noon sun in the south and aimed five cameras
at the shade: a careful sentence making a wrong thing read as considered.

The function's own docstring also records the OTHER end of this being fixed
on 24 Aug — `%h` grew from seven characters to eight and 0 of 333 matched.
That repair fixed the comparison and left the window, and the window closed
on the corpus as the repository grew past 400 commits.

### B. `--flaky` counted 7 runs carrying no gate verdict as runs where nothing failed

`flaky()` did `if not m: continue` on a missing `FAILING GATES` line.
Measured over the 329 it called measuring:

    pass=True   119
    pass=False  203      (203 FAILING GATES lines — these reconcile exactly)
    ABSENT        7      counted in the denominator, contributing "clean"

Silence read as health, in the tool whose job is finding the rare red. The
7 are partial builds: `e17e91e` carries `(no SimDirector lines matched)` —
the SECOND never-ran marker, which `tools/verdict-keys.py:49` has and
`gates.py` did not; `8132974` and `3e3cdc2` rendered frames and
drift-measured them but no done line reached the verdict.

This is rule 1's third corollary, and `gates.py:147` says so about its own
previous instance: *"Exactly the repair made to `verdict-keys` an hour
earlier … which I did not."*

**The repair is deliberately NOT a second marker string.** A marker list is
an allow-list; it discards everything nobody thought of and looks identical
to a clean result. The test is now POSITIVE — a run enters the gate-failure
denominator only if it carries `pass=` or a `FAILING GATES` line — which
cannot be defeated by rewording a sentence.

### C. Denominators printed a numerator with no offered count

- `--series` said `confabs: 322 landed run(s), newest first`. 322 of what?
  A key in 322 of 329 and a key in 322 of 3,000 read identically, and the
  second is a key that stopped being emitted.
- `--constant` said `329 measuring run(s) read` and never mentioned the 26
  dropped, so it could not be checked against `ls runs/*.txt | wc -l`.
- `--flaky` said `across 329 kept run(s)` with no drop clause at all.

### D. An unannounced cap in the dead-row block

`constant_report`'s row printer did `"/".join(vs[:3])` with no ellipsis and
no count — the only cap in the file that did not say it bit. (`words()`'s
`changes[:12]` announces `(+N older changes not shown)` correctly, and
`scan()`'s handling of the emitter's own `+Nmore` is exemplary.)

### E. A numeric series with a unit suffix was silently summarised as words

`float("29.53ms")` raises, so `--series meanFrame` fell through to
`words()`: a 322-entry tally of near-unique strings, `changed 321 time(s)`,
and **no min / median / quartiles at all** — for the key
`game-design/research/performance-budget.md:78` cites as the performance
measurement. Nothing said it had failed to read them as numbers.

### F. `--series` gave a reader no way to LOCATE a break

The numeric path printed a bare run of values with no positions and no
shas, under prose telling the reader to find the regime change in it. The
word path had printed transition shas since it was written; the numeric one
had nothing. `SimDirector.cs` declares regime breaks in CODE COMMENTS at
eight sites; no machine-readable marker exists in any verdict.

### G. `gate-detail.py`: 18 bare gates counted, 31 exist — and the third most common failure in the project was in the blind spot

Same fault class, second file. `BARE` was
`\("([A-Za-z]\w*)",\s*\w+Ok\)` — it required the second tuple element to be
an identifier ending in `Ok`. Measured against the gate table itself:

    31 bare / 40 detailed / 0 unclassified = 71 table entries
    the tool printed 18 bare / 41 detailed = 59

**Thirteen bare gates matched neither pattern and were silently dropped**:
`beats`, `discredit`, `disguise`, `jobRan`, `knowledge`, `lamps`,
`launder`, `noErrors`, `npcsMoved`, `screenshots`, `secretReachedDay`,
`takingsBanked`, `verdictSane` — because they are written
`("jobRan", jobRan)` and `("noErrors", _errors.Count == 0)`.

**`jobRan` is the third most common failure in the project's recorded
history — 73 reds, 22.6% (`gates.py --flaky`).** This tool exists because
its own docstring says the SECOND most common one, `dayJob`, "went
undiagnosed for months not through neglect but because there was nothing to
read". The third was sitting in its blind spot the entire time, and so were
`beats`, `discredit` and `verdictSane`, which also appear in the flaky
table.

The scan also leaked the other way: `render` was counted as DETAILED from
**outside** the gate table, which is why "41 detailed" was one more than
the 40 that exist.

**This overturns a landed conclusion.** `roadmap-history.md:2932` records
*"`tools/gate-detail.py` ratchets the count (18, ceiling 18)"*. The count
was 31 and the ratchet had thirteen gates it could not ratchet.

**On raising `CEILING` 18 → 31.** Nothing was red; the tool passed 18 of 18
every run. The DENOMINATOR was wrong, so the numerator counted a subset.
Raising the integer to the measured truth makes the guard **stricter** — a
fourteenth bare gate in the unmatched form is now refused, where before it
was uncountable. The ratchet rule is unchanged: lower it when a gate gains
its operands, never raise it again without a measurement printed beside the
change.

### H. A SIGPIPE stack trace on `| head`

Surfaced while testing: `gates.py --flaky | head -3` ended a correct run in
a `BrokenPipeError` traceback. This tool prints hundreds of lines and `|
head` is the only way anybody reads it.

## What was found CLEAN, with its counts

- **`--constant`'s harvest is complete.** A maximally permissive
  `([A-Za-z][\w]*)=` sweep over the 329 measuring runs finds **1,464**
  names against `scan()`'s **1,408**. All **56** of the difference were
  opened and are sub-keys inside a bracket group consumed whole —
  `lightState=[q=All/lvl=5/px=8/…]`, `homTopics=[player.killed_ada=true]`,
  `bodyCoat=[denim hsv=…]`. **Zero** top-level keys are invisible and
  **zero** keys carry an empty value. The `VALUE` grammar and the
  bracketed-list handling are correct; the C6 repair holds.
- **`--pending`'s `-60` window announced itself** already.
- **`split_gates` / `split_fields` / `unwrap`** are correct on the live
  corpus; the `+Nmore` cap is honoured as a cap and not as a row.
- **Both `--selftest`s genuinely RUN** — see the section below.

## What was fixed

1. **One corpus, one implementation.** `run_corpus()` replaces three copies
   of the log-and-match loop (`ordered_runs`, `pending`, `main`). One
   `git log` call in the whole file, down from three.
2. **The window is gone and the arithmetic is printed**, in the settled
   shape:

       corpus: 330 measuring + 26 no-sim + 0 unplaced = 356 run file(s) offered

   `unplaced` is the count that would have been 248: a run whose commit is
   not in this history cannot be ordered, so it is counted, NAMED, and not
   mixed into the evidence. `place_runs()` is pure so a test can drive it.
3. **`--flaky` counts what it measures** (positive `gate_verdict` test) and
   names the 7 runs it excludes.
4. **`--series` prints offered beside contributed** — the leading token is
   byte-identical and the denominator is appended — and marks the series
   with `[index] sha` every 10 values so a break can be located and cited.
5. **A uniform unit suffix is summarised numerically**, unit carried onto
   every summary number; a varying remainder still falls to the word path
   and now says why, marked `[CATEGORICAL]`.
6. **The dead-row cap announces itself**; `--constant` prints a bracketed-key
   arithmetic line naming the 82 keys that hold no parseable rows.
7. **`main()`'s `??? ` outcome is named `NOGTE`** — it meant both "could not
   parse" and "ran but never reached the gate table", which are different
   facts.
8. **SIGPIPE guarded**; a reader that stops reading exits clean.
9. **`gate-detail.py`**: scan scoped to the gate table (missing anchor is
   `nothing measured`, exit 2, not an empty scan); `BARE`/`DETAILED`
   discriminate on the `$`, which is the actual question; a third
   `unclassified` bucket that names rather than drops; `(?<![\w])` so a
   method call's string argument is not read as a gate; the arithmetic
   identity printed on the line.

## The selftests: both cases watched, and PROVEN TO RUN

`lint-shadow`'s `--selftest` fell through to the live sweep and exited 0
tonight, so "a guard that had never run looked exactly like one that had"
was checked mechanically here rather than assumed. Neither selftest's
output contains any live-sweep marker (`measuring run(s) read`, `corpus:`,
`gate failures across`, `landed run(s)`, `bare /`, `ceiling`), and both
print words only the selftest can print. `--selftest` is the first branch
in each `main()`.

**Fixtures are synthetic and unpinned** — a 40-commit fake log, fake key
names, no real run, commit or key. The one exception is `gate-detail`'s
accepting fixture, which is the LIVE gate table, per the standing rule that
for a tool checking the project itself the live codebase is the best
accepting case.

**One fixture was wrong and the tool was right — twice.** The first
ordering fixture numbered commits `0..39` in log order, so SHA order and
COMMIT order were the same sequence and the broken code passed the ordering
assertion identically. That is `verify.py`'s own recorded mistake ("122
hits either way"): a guard whose rejecting case its fixture cannot express.
The log is now scrambled by `(i*17) % 40`. Separately, an 8-character stem
fixture asserted `00000301` where the hash's eighth character is `f`.
**Both were probe faults, found by suspecting the probe first.**

### Accepting cases (output as run)

    $ python3 tools/gates.py --selftest
    gates --selftest: ok — over 20 synthetic verdicts, 10 keys and a 40-commit synthetic log:
      ORDERING (finding A, previously untested): placed in commit order at depths 2/11/30/39
      from a SCRAMBLED log (sha order differs from commit order, so the fallback is visible),
      8-char stem placed, oldest commit ordered against newest, `deadbee` reported UNPLACED
      not appended; identity adds up; 10 unplaced announce `(+4 more not shown)`
      GATE VERDICT: `pass=True` with no FAILING line ACCEPTED as a verdict; a run with
      neither REJECTED from the rate
      UNITS: `1/2.5/-3` and `29.53qq` and `0/40` summarise numerically; `4/0.00`..`3/0.90`
      and `None`..`Procedure` fall to words and say why
      ACCEPTS (not reported): selftestMoved, selftestFilled (nothing-offered -> 17/19),
      selftestRowsMove, selftestMixedRows
      REPORTS: selftestDead, selftestFlagDead (nothing-flagged/12..31), selftestRowsDead
      rows: 3 dead of 8 swept across 4 bracketed key(s), including selftestMixedRows[dead]
      inside a key that moves
      denominators print per key; 0 runs and 3 runs both print `nothing measured`
    EXIT=0

    $ python3 tools/gate-detail.py --selftest
    gate-detail: selftest ok (8 checks, accepting case first)
    EXIT=0

**The ordering path had never been under test at all** — the old selftest
handed `constant_report` text directly, which exercises the harvest and
skips the corpus entirely. That is exactly where finding A lived.

### Rejecting cases (each mutation reverted immediately)

| # | mutation | result |
|---|---|---|
| A | the `-400` window and sha fallback put back | exit 2 — *"placed runs came back ['0000034', '0000027', '0000023', '0000030'], not in commit order … This is finding A"* + the unplaced assertion |
| B | `gate_verdict` returns `True` always (the old negative test) | exit 2 — *"a verdict with no pass= and no FAILING GATES was counted as a run in which nothing failed"* |
| C | `numeric` restored to the original `float()` path | exit 2 — *"a uniform unit suffix was not summarised numerically … This is the fault that gave a continuous quantity a 322-entry word tally"* (3 assertions) |
| D | `gate-detail`'s old `\w+Ok` pattern put back | exit 1 — `AssertionError: []` where `['jobRan','lamps','noErrors']` was required |
| E | table anchor renamed | exit 2 — *"nothing measured — the gate table anchor … is not in SimDirector.cs. This is not a clean result; the scan walked no entries."* |
| F | `CEILING` lowered to 30 | exit 1 — names all 31 bare gates and prints the arithmetic; the ratchet still bites |

Exit codes are distinct per outcome: **0** clean, **1** ratchet/assertion
failure, **2** selftest failure or nothing-measured.

## The parse trap: how the parse was established

1. **`git grep "gates.py"` across every tracked file.** Every hit is prose —
   ten C# comments, five `verdict-read.py` docstrings, `capsay.py`,
   `CLAUDE.md`, four `game-design/` docs. **Nothing parses `gates.py`
   stdout.** Its wording is therefore free; the `--series` leading token
   was kept byte-identical anyway and the denominator appended beside it.
2. **`gate-detail.py` HAS one consumer**: `ledger/verify.py:1775-1786`,
   which runs `--selftest` (fails the check on non-zero), then runs the
   tool, picks `next((l for l in out if l.startswith("gate-detail:")), "")`
   and emits `head.replace("gate-detail: ", "gates ")` into the verify
   footer. **That parse was reproduced exactly and run**: prefix
   byte-identical, line found, rc 0, footer text
   `gates 31 bare / 40 detailed, ceiling 31 [arithmetic: 31+40+0=71 table
   entries walked]`.
3. **`verify-footer-denominators.md:186` records a residual** for this
   selector — *"if a tool ever printed two, one is dropped in silence"*.
   Checked: `gate-detail.py` has six `gate-detail:` print sites and they
   are mutually exclusive (each returns). Measured live: **1 line** in each
   of the two reachable outcomes.
4. **Full `ledger/verify.py` run** as the end-to-end parse test; footer
   below, read from `ledger/.verify-footer` on disk.

## What was left, and why

- **The three copies of the `VALUE` grammar** (`gates.py`, and twice in
  `verdict-read.py`). A shared `tools/verdictfmt.py` is the right home;
  `verdict-read.py` is not this agent's file. Reported, not half-removed.
- **`ledger/verify.py`'s `runs_map_to_commits` has the SAME `-400` window**
  and prints `runs map to commits (107 of 355 within 400)` — a sentence
  that reads as health and is finding A stated as a fact nobody read as
  one. Not this agent's file. **This is the strongest single recommendation
  here:** the number was on screen in every verify footer for weeks and
  said nothing, because it had no expected value beside it. It wants
  `107 of 355` to be a RED, or to become `355 of 355`.
- **No regime marker in the verdict.** `--series` can now show WHERE a
  break is; it still cannot know one was DECLARED, because the eight
  declarations are C# comments. Emitting a `regime=` key is a
  `SimDirector` change and belongs to a builder.
- **The `confabs` regime-break claim in `CLAUDE.md`** — flagged above for a
  re-read against true order by its owner. Not re-litigated here.
- **No threshold was invented.** `gates.py` still exits 0 whatever it
  finds, which is correct: the commit that fixes a red run must not be
  blocked by it.

## Verify status — read from disk, and it is NOT GREEN (not from this work)

**`ledger/.verify-footer` DOES NOT EXIST on disk.** That is the correct
reading and it is reported rather than worked around: `verify.py` writes
the footer only on green and `unlink`s it on red, precisely so a red run
has nothing to paste. There is therefore no footer to quote, and quoting
the footer text printed to stdout would be pasting an ungreen footer — the
thing the file exists to prevent.

    $ python3 ledger/verify.py ; echo $?
    ... NOT GREEN — do not paste this into a commit message as if it were.
    1
    $ ls -l ledger/.verify-footer
    ls: cannot access 'ledger/.verify-footer': No such file or directory

**It is not this work, established by measurement rather than assertion.**
Both tool files were reverted to HEAD and `verify.py` re-run with every
other agent's in-flight change still in place:

    EXIT WITHOUT MY CHANGES = 1        (still red)

**The red check is REF BENCH.** The last green committed footer carries
`101 ref-bench checks (0 failed)`; this tree produces
`REF BENCH: accepting: district_hook is NOT low-content
(groundMean:0.547>0.543) (+2 more of 3)`. `tools/ref-bench.py` is
UNMODIFIED in the working tree; `ledger/verify.py` IS modified, by another
agent, and it is that in-flight change's ref-bench check that is red.
Neither file is this agent's to touch. Flagged for the director, not
re-litigated here — though the word `accepting:` in the failure means a
guard is failing the case it must PASS, which is rule 5b's own shape.

The tree also moved under this audit: HEAD advanced `c03ead22` →
`b63e271f` (CI committing its own stills), the runs directory went 355 →
356, and `game-design/queue.md`, `tools/lint-filetype.py` and
`tools/lint-unreached.py` carry other agents' uncommitted work.

**What this work moves in the footer is exactly two parts**, diffed
part-by-part against the same run with the changes reverted:

    -  gates 18 bare / 41 detailed, ceiling 18
    +  gates 31 bare / 40 detailed, ceiling 31 [arithmetic: 31+40+0=71 table entries walked]

Nothing else in the 88-part footer changes. `verify.py` emitted that line
through its own selector, which is the parse holding end to end.

**Also visible in that footer, unchanged and un-acted-on:**
`runs map to commits (108 of 356 within 400)` — finding A, sitting in the
footer of every commit, reading as health.
