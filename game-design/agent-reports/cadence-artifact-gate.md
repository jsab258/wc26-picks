# `director_cadence` now requires the RULING, not the spawn (instrument-builder, 25 Aug 2026)

> **STATUS — LOG, 2026-08-25. NOT CURRENT once the rule is copied into
> CLAUDE.md and this gate has a landed series.** Built against the live hole:
> a `studio-director` spawned at 17:01:24Z was killed by a session limit
> before it ruled, its row cleared the gate, and `over threshold, REVIEWED`
> printed over an unreviewed 1,800-line batch carrying eleven confirmed audit
> findings. CLAUDE.md predicted this failure in writing and named two
> candidate fixes; this is the second one, which it ruled the stronger.
> Nothing committed — the resident reviews and commits.

---

## 1. What a decision record is, and why a silent director cannot produce one

**THE RULE.** A DECISION RECORD is one HTML comment inside a file matching
`game-design/decision-*.md` **in the working tree**:

    <!-- RULING spawn=2026-08-25T19:26:14Z -->

It counts only when `spawn=` names a **real `studio-director` row in
`.claude/agent-log.tsv`** that is **newer than the reference commit** (the
newest commit that touched `ledger/Assets/Scripts`). Spaces are optional,
extra `key=value` tokens are ignored, and `Z` and `+00:00` forms of the same
instant both pair — forgiving about how the stamp is WRITTEN, strict about
which instant it NAMES.

**Why a director that ran and said nothing cannot clear it.** The spawn row is
written by a `SubagentStart` hook, at spawn, by the machine — it exists whether
or not the agent ever produces a thought. The stamp is written by the director,
into a file, as the closing line of a ruling. A director killed mid-ruling
never issues that write, so no stamp exists to pair with its row, and the gate
reads `DIRECTOR RAN BUT DID NOT RULE`. That is the whole repair in one
sentence: **the old gate tested the process, this one tests the artifact.**

**Why the spawn row keeps its place.** It changes role rather than losing one.
The row is now **NECESSARY** — a stamp naming a date that is in no row counts
as nothing (`rulingUnmatched`), so the record cannot be satisfied by a
hand-typed timestamp — and **no longer SUFFICIENT**, since a row nothing points
at clears nothing. Fixture `r14` holds the first half, `r11` the second.

**Why the location is one glob and not "wherever the director wrote".** The
director also writes agent reports, and so does every tier-3 builder; making 25
report files each a way to clear the gate is the allow-list fault wearing a
filter's clothes. One place, one glob, and a correct stamp written into
`agent-reports/` clears nothing (`r16`).

**Why the working tree and not `git ls-files`.** The ruling lands in the same
commit it authorises, so requiring it to be tracked would refuse every honest
case — the ratchet shape of rule 5b. Both are accepted and both are asserted
(`a2` untracked, `a11` tracked).

## 2. How the record binds to THIS batch

The chain is four mechanical links, each one checkable, none of them prose:

    ruling stamp --spawn=--> a studio-director row --dated after--> the
    reference commit (newest commit touching Assets/Scripts) --defines-->
    the batch = everything pending since that commit

The reference commit is the same instant the pending-lines threshold is
measured against, so the record inherits the batch definition rather than
getting a second, weaker one of its own. A ruling written for an earlier batch
names an earlier spawn row, and every spawn row goes stale the moment a code
commit lands — so `r13` (a real ruling, naming a real director row, from
before the reference) is refused with `a ruling on an older batch`, even though
a fresh spawn row sits beside it in the log.

**The 25 Aug reference repair is untouched, deliberately.** Comparing against
HEAD meant a docs commit, an amended message or CI's own `Sim stills from
<sha>` commit invalidated a real review; it fired three times in one night.
That reference logic is not modified by this change, and `a9` now asserts the
preservation on BOTH halves — a docs-only commit on top invalidates neither the
spawn row nor the ruling record.

## 3. What I deliberately did NOT do

- **I did not stamp the director's ruling myself.** The real ruling for
  tonight's batch (`game-design/decision-dressing-batch.md`) was written by the
  director at 19:28 and carried no stamp, because the format did not exist when
  it was written. Appending the line myself would have been a builder forging
  the artifact the gate exists to demand — the spawn-row hole reintroduced with
  better manners. The gate's refusal names the exact stamp instead, and the
  director appended it on resume.
- **I did not gate `rulingRowsUnruled`.** Requiring EVERY fresh spawn to have a
  ruling would go red whenever a director is spawned for an unrelated call, or
  killed and resumed (which writes a second row) — a false red on a real
  review. There is no landed series for that number yet, so it ships as a
  READING beside the gated one, and `a14` pins that a batch with two spawns and
  one ruling is GREEN with `rulingRowsUnruled=1/2` printed.
- **I did not use file mtimes anywhere.** This container rolls the checkout
  back (CLAUDE.md, 19 Aug), which rewrites every tracked file's mtime and would
  make every old decision file look freshly written. The record carries its own
  timestamp, in its content, pinned to a machine-written log row.
- **I did not touch CLAUDE.md** — see §7.
- **I did not add a body-length bound** (words between a heading and its
  stamp). It would need a series first, and the failure it would catch — a
  director writing a stub ruling — is a lie rather than an accident, which no
  bound catches.

## 4. Selftest — 53 assertions, 38 before, accepting cases first

`python3 ledger/verify.py --selftest`, exit 0, run against the tree as it
stands. The suite runs INSIDE `director_cadence()` on every verify, and a
fixture failure fails the gate with the first FAIL quoted.

    ok   ACCEPT small diff with no director row
    ok   ACCEPT summary carries both denominators and the tracked/untracked split
    ok   ACCEPT a COMPLETED REVIEW: large diff, a fresh director row, and an UNTRACKED decision record naming that spawn
    ok   ACCEPT the ruling keys carry their denominators and no value holds a space
    ok   ACCEPT exactly 100 changed lines (the bound is MORE than 100)
    ok   ACCEPT 500 lines outside Assets/Scripts
    ok   ACCEPT small diff with no log, and it says nothing measured
    ok   ACCEPT a fresh row stamped +00:00 with fractional seconds, and a record naming it
    ok   ACCEPT a SMALL new untracked directory, counted and split in the line
    ok   ACCEPT a 400-line-looking untracked BINARY as 0 lines, and say so
    ok   ACCEPT a review INVALIDATED ONLY BY A NON-CODE COMMIT (CI stills): code commit < director row < HEAD
    ok   ACCEPT a DOCS-ONLY commit on top does not invalidate the decision record either
    ok   ACCEPT names the code commit it compared against, and the distance from HEAD to it
    ok   ACCEPT a SHALLOW depth-1 clone with a row newer than everything in it and a record naming it
    note shallow depth-1 clone resolves reference kind=code ref=2023-11-15T00:13:20Z head=2023-11-15T00:13:20Z (safety asserted by a10/r10, not by this line)
    ok   ACCEPT a ruling in a TRACKED decision file (git status is not the question)
    ok   ACCEPT all three stamp shapes — unspaced, extra tokens, and +00:00 naming a Z-stamped row
    ok   ACCEPT a small diff with no decision file at all, and say nothing was measured
    ok   ACCEPT two fresh spawns with one ruling — green, and the unruled spawn is still NAMED on the green line
    ok   REJECT 101 changed lines with no director row
    ok   REJECT large diff with only STALE director rows
    ok   REJECT large diff with a header-only log
    ok   REJECT 0-rows-examined reads differently from no-director-found
    ok   REJECT large diff with the log file missing
    ok   REJECT a director row whose timestamp cannot be dated
    ok   REJECT a 300-line module in a NEW UNTRACKED DIRECTORY (git diff HEAD cannot see it at all)
    ok   REJECT 60 tracked + 60 untracked = 120, where neither half crosses 100
    ok   REJECT a director row OLDER than the last code commit, even with a non-code commit on top
    ok   REJECT 300 untracked lines where NO commit ever touched Scripts, and say the reference fell back to HEAD
    ok   REJECT a SHALLOW depth-1 clone whose only director row is stale
    ok   REJECT the LIVE SHAPE: a fresh director spawn row with NO decision record — a spawn is attendance, not a review
    ok   REJECT the word REVIEWED is gone from the spawn-only case and still present on the ruled one
    ok   REJECT a decision file with prose but NO closing stamp, and it reads differently from having no file at all
    ok   REJECT a decision record OLDER than the reference commit, even with a fresh spawn row beside it
    ok   REJECT a stamp naming a time that no spawn row carries — the row is NECESSARY, so a fabricated date clears nothing
    ok   REJECT a stamp naming a fresh BUILDER row rather than a director one
    ok   REJECT a correct stamp written into an agent report instead of a decision file
    ok   REJECT no log even with a decision record present — an absent instrument is not compliance, and the record has nothing to pair to
    ok   NEVER LOOSER: across 31 fixtures, every GREEN substantial diff has both a fresh spawn row and a ruling record
    ok   every accepting case exits 0
    ok   the three reds carry different exit codes (1 unspawned, 2 log missing, 3 spawned-but-never-ruled)
    ok   MEASURE batch 2/3, day 1/1@2023-11-15 and lifetime 3/5 from ONE log — three windows that disagree
    ok   MEASURE every numerator is <= the denominator printed beside it (the impossibility a lifetime-vs-window mix-up would show)
    ok   MEASURE the fable set is READ from the definitions and printed with the count of files examined
    ok   MEASURE a SECOND agent on fable counts in the share and is named, while directorSpawns still counts director reviews only
    ok   MEASURE 2 definitions read, NONE on fable: a zero with its denominator, and it says so in words
    ok   NOTHING MEASURED: an ABSENT log prints the words in all three windows, never a zero
    ok   NOTHING MEASURED: a header-only log reads as nothing measured, not as 0 spawns
    ok   NOTHING MEASURED for the DAY window only, while the lifetime share stays measured — and the empty batch window says so
    ok   NOTHING MEASURED about the SET: 0 definitions read falls back to studio-director and says the set is assumed
    ok   THE GATE IS BLIND TO SPEND: 100% and 5% fable shares, same gate inputs, same green state and exit code
    ok   THE GATE IS BLIND TO SPEND, OTHER WAY: a 100% fable share with NO director row is still RED, exit 1
    ok   THE GATE IS BLIND TO SPEND, THIRD RUNG: a 100% fable share on a SMALL diff stays GREEN — spend never makes a change reviewable
    ok   every emitted spend value is one whitespace-free token, 100 of 100 expected key tokens scanned across 10 fixture summaries
    director-cadence selftest: 53 passed, 0 failed

**What the 15 new assertions cover.** Six existing fixtures had to GAIN a
ruling record to stay green (`a2`, `a6`, `a9`, `a10`, `s8a`, `s8b`) — that is
the accepting-first discipline doing real work, because a version written
rejecting-case-first would have shipped a gate no honest review could clear.
The new ones:

| | accepting |
|---|---|
| `a2` | a COMPLETED REVIEW clears the gate — untracked decision file, and the ruling keys carry their denominators |
| `a9` | a docs-only commit on top invalidates the RECORD no more than it invalidates the row |
| `a11` | a TRACKED decision file is accepted too |
| `a12` | three stamp shapes — unspaced, extra ignored tokens, `+00:00` naming a `Z` row |
| `a13` | a small change gains NO new way to be blocked, and says nothing was measured |
| `a14` | two fresh spawns, one ruling: GREEN, with `rulingRowsUnruled=1/2` printed |

| | rejecting |
|---|---|
| `r11` | **the live shape** — fresh spawn row, no record anywhere; exit 3, and `REVIEWED` is gone from the line |
| `r12` | a decision file with prose but no closing stamp (killed mid-write), and it reads differently from no file at all |
| `r13` | a record OLDER than the reference commit, with a fresh spawn row beside it |
| `r14` | a stamp naming a time that is in no row |
| `r15` | a stamp naming a fresh BUILDER row |
| `r16` | a correct stamp in an agent report instead of a decision file |
| `r17` | no log at all, record present — `logmissing` still outranks it, exit 2 |
| — | **NEVER LOOSER**, over all 31 gate fixtures: every GREEN substantial diff has BOTH a fresh row and a record. A regression that stopped reading the log passes every case above and dies here. |

**Fixtures are synthetic.** Every stamp names an instant that exists only
inside a throwaway repo (`CADENCE_FRESH/STALE/NEWEST`, 2023-11-14). Nothing is
pinned to `.claude/agent-log.tsv` or to a real decision file — two rejecting
fixtures in this suite had to be unpinned earlier because a fixture tied to a
live file goes red when the PROJECT improves, and a ruling fixture pointed at
`decision-ground-albedo.md` would go red the day a director stamped it.

## 5. The live series — both outcomes on the real batch, an hour apart

This is better evidence than any fixture, because it is the actual failure.

**REJECTING, 19:35Z** (`python3 ledger/verify.py --cadence`, exit **3**):

    DIRECTOR RAN BUT DID NOT RULE: 2201 changed line(s) (517 tracked + 1684
    untracked in 2 new file(s)) vs 100 threshold under Assets/Scripts, 2
    director row(s) newer than the reference of 116 log row(s) examined,
    reference = code commit e72f58a3@2026-08-25T16:00:02Z (HEAD
    2026-08-25T16:50:35Z is +2 non-code commit(s) later), rulingRecords=0/0
    rulingFiles=2 rulingUnmatched=0 rulingRowsUnruled=2/2
    rulingUnruledNewest=2026-08-25T19:26:14Z — 0 ruling record(s) paired to a
    director row newer than the reference, of 0 stamp(s) in 2 decision file(s)
    scanned — a spawn row is attendance, not a review. ...

**The same tree, the same minute, with HEAD's pre-change `director_cadence`**
(loaded from `git show HEAD:ledger/verify.py` with its own `__file__`, so every
path it read was the live one):

    HEAD's director_cadence  -> GREEN | director cadence ok (2424 changed
    line(s) ... over threshold, REVIEWED

That pair is the finding: **the old instrument certified an unreviewed
2,236-line batch as REVIEWED at the same instant the new one refused it.**

**ACCEPTING, 19:50Z**, after the director RESUMED and closed its ruling in
`game-design/decision-dressing-batch.md:185` with
`<!--RULING spawn=2026-08-25T19:26:14Z-->` (exit **0**):

    director cadence ok (2730 changed line(s) (997 tracked + 1733 untracked in
    2 new file(s)) vs 100 threshold under Assets/Scripts, over threshold,
    REVIEWED; 3 director row(s) newer than the reference of 119 log row(s)
    examined; reference = code commit e72f58a3@2026-08-25T16:00:02Z (HEAD
    2026-08-25T16:50:35Z is +2 non-code commit(s) later); rulingRecords=1/1
    rulingFiles=2 rulingUnmatched=0 rulingRowsUnruled=2/3
    rulingUnruledNewest=2026-08-25T19:46:36Z — 1 ruling record(s) paired to a
    director row newer than the reference, of 1 stamp(s) in 2 decision file(s)
    scanned)

Note `rulingRowsUnruled=2/3` **on a green line**: three directors were spawned
into this batch window and two of them produced nothing. That number was
invisible before and is not gated — it is the reading that would have said, at
17:01, that the REVIEWED beside it was hollow.

**A ladder run against the live files** (`_cadence_rulings` — the gate's own
pairing — over a scratch COPY of tonight's two decision files and the live
spawn log; the project was not modified). One contributor changed per rung,
one vantage, one run:

| rung | files | stamps | FRESH | unmatched | gate |
|---|---|---|---|---|---|
| as it stood, no stamp | 2 | 0 | 0 | 0 | **RED** |
| stamp names 19:26:14Z (the director that ruled) | 2 | 1 | **1** | 0 | GREEN |
| stamp names 17:01:24Z (the director that DIED) | 2 | 1 | 1 | 0 | GREEN |
| stamp names 20:00:00Z (in no row) | 2 | 1 | 0 | **1** | **RED** |

Rung 3 is the second blind spot, measured rather than reasoned about: the stamp
binds a record to A fresh spawn, not to THE spawn that wrote it, because
nothing here attests authorship. It needs a person to write a false sentence;
the hole it replaces needed nobody to do anything at all.

## 6. Keys added to the cadence line

All five print in **every** branch, red and green, values whitespace-free, and
each is followed by a space so no value can collect a `)` or a `;` — the
`crowdBodyWidth=0.45(narrowest` fault one layer down. The suite asserts that,
100 of 100 expected key tokens across 10 fixture summaries.

| key | statistic |
|---|---|
| `rulingRecords=<fresh>/<stamps>` | COUNT of stamps naming a director row newer than the reference, over COUNT of stamps found anywhere. **The gated pair**, both halves from one pass. `nothing-measured` when no decision file exists. |
| `rulingFiles=<n>` | COUNT of `decision-*.md` files scanned — the denominator that keeps "one file, no ruling in it" distinguishable from "no decision file at all" |
| `rulingUnmatched=<n>` | COUNT of stamps naming no real studio-director row |
| `rulingRowsUnruled=<a>/<b>` | COUNT of fresh spawn rows no ruling points at, over `since_code`. ATTENDANCE MINUS REVIEW. `nothing-measured` when the log is absent or rowless. |
| `rulingUnruledNewest=<stamp\|none>` | the NEWEST such row, quoted verbatim from the log, so a red run names the line to write. Named for what it IS, not for what the red branch wants, because it prints on green lines too. |

New state `unruled`, new `--cadence` exit **3**, distinct from 1 (nobody
spawned) and 2 (no log) — a caller can tell "spawn a director" from "RESUME the
one that died" without parsing prose. `REVIEWED` in the summary is now computed
from `ruling_fresh` rather than from `since_code`, so the adjective and the
state cannot disagree; before, the word claimed a review and was computed from
an attendance register.

## 7. Conclusions this confirms or overturns

- **CONFIRMS, and closes:** CLAUDE.md's *"A HOLE THAT IS STILL OPEN ...
  `director_cadence` is satisfied by a SPAWN, not by a COMPLETED REVIEW."* Not
  only true — it happened again the same day, and the pre-change gate was
  caught printing REVIEWED over it in this session.
- **OVERTURNS:** CLAUDE.md's *"Two candidate fixes, neither built"* is now
  false; the second (the artifact test) is built and live. **CLAUDE.md is
  behind the code.** Touching it is a mandatory director trigger, so it is NOT
  edited here — the next director spawn should replace that paragraph with the
  rule in §1 and the stamp format, and the studio-director agent definition
  should gain one line telling it to close every ruling with the stamp.
- **OVERTURNS:** `agent-reports/template-sync-debt.md:44` finding **(d)** —
  *"STILL OPEN here; carry the finding, not a fix."* It is no longer open in
  this repo; the sibling template still carries it.
- **CONFIRMS, unchanged:** finding **(c)** in the same file, and the 25 Aug
  ruling in `decision-ground-albedo.md:1239` — the reference must stay the last
  commit that TOUCHED code. Not modified; `a9` now asserts it on both halves.
- **CONFIRMS:** `queue.md`'s standing item *"DO NOT COMMIT ON A GREEN
  `director_cadence` RIGHT NOW — IT IS LYING"*. The instrument no longer lies
  in that state, so that item can close; the resident should retire it in the
  same commit.
- **A COMMENT I FALSIFIED AND FIXED, in this file:** `s3-all-opus` asserted
  `NOTHING_MEASURED not in s3["summary"]` — a claim about the SPEND windows,
  written against the whole line. The ruling scan added a second, legitimate
  `nothing-measured` and the assertion went red over a correct reading: the
  instrument did not change, the question it was pointed at did. It now asserts
  over `_cadence_spend(s3)`, the text it was always about.

## 8. Verify footer, read from disk

**There is no footer to paste. `ledger/.verify-footer` does not exist** — the
last full run was RED, and a red run deletes the file by design so a red run
has nothing to give you. Checked on disk with `ls`, not from scrollback.

**The single red is not `director_cadence` and not mine.** Full run at 20:0xZ,
the cadence gate first in the footer:

    director cadence ok (2730 changed line(s) (997 tracked + 1733 untracked in
    2 new file(s)) vs 100 threshold under Assets/Scripts, over threshold,
    REVIEWED; ... rulingRecords=1/1 rulingFiles=2 rulingUnmatched=0
    rulingRowsUnruled=2/3 ... [53/53 selftest fixtures]

    UNTRACKED/ABSENT TOOL(S): tools/hang-report.py(untracked)

`tools_tracked` is red on another agent's brand-new tool, written at 19:48 and
not yet committed. Everything else in the footer is green, including
`4005 CoreTests` and `Game layer compiles (183 files)`.

**Two reds that WERE live an hour earlier, and were shown not to be mine
before they were fixed by their owners:** `reach FAILED — 1 unreached` and
`CoreTests RED: a fully populated run formats exactly — kitPlaced=...`. Both
were reproduced against the same tree using HEAD's PRE-CHANGE `verify.py`
(loaded with its own `__file__` so every path it read was the live one), which
is the measurement that settles authorship rather than arguing it. The same
run is what caught HEAD's `director_cadence` printing GREEN/REVIEWED over the
unreviewed batch, quoted in §5.

**My change can legitimately turn verify RED**, and that is the gate working
rather than a failure: it did so for fifteen minutes tonight, refusing a batch
whose only claim to review was a dead director's spawn row. It went green when
a real ruling landed, not when anything was loosened. No threshold was moved:
`DIRECTOR_MIN_LINES` is still 100, the reference is still the last commit that
touched `Assets/Scripts`, and the artifact requirement only ever ADDS a reason
to be red — asserted over all 31 gate fixtures by the NEVER LOOSER case.

## 9. Files

- `ledger/verify.py` — the only file changed. All hunks inside the cadence
  region: `_cadence_rulings` (new), `_cadence_read`, `_cadence_ruling_phrase`
  (new), `_cadence_summary`, `_cadence_fixture`, `_ruling_doc` (new),
  `_cadence_selftest`, `director_cadence`, `CADENCE_EXIT`, and one comment in
  `main`.
- Nothing committed. Nothing else in the tree touched.
