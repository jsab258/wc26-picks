# The cheap CI channel was dark for seven days, and its colour never changed

> **STATUS — LOG, 2026-08-25. NOT CURRENT** once the changes below land.
>
Instrument-builder account. Every number here was read this session by running
the command beside it; nothing is recalled. Where a figure in my brief turned
out to be wrong, the brief's figure is printed next to the measured one rather
than quietly replaced.

---

## 1. What was actually wrong

`.github/workflows/ledger-core-tests.yml` ran eight checks as eight bare
`run:` steps in a row. GitHub Actions skips every step below a failed one, so
one red at position 4 took the other six with it:

    4  Reach check (built is not running)       FAILURE
    5  Docs check (LIVE / SPEC / LOG)           skipped
    6  Shape check (clips, barks, manifests)    skipped
    7  Shape check — the checker itself         skipped
    8  Attribution check (third-party assets)   skipped
    9  Run core test suite                      skipped
    10 Run AI playtest (fake mode)              skipped

That step list is from run 32793613280 on `80a9104`, read from the API this
session. The job's single red could not distinguish *"reach is out of
bounds"* from *"the 2,884 CoreTests are broken"* from *"six checks never
executed at all"* — and six checks reporting NOTHING looked exactly like six
checks reporting fine. Rule 3b with a workflow's skip logic supplying the
zero.

**And underneath it, an instrument fault, not a subject fault.** The reach
check itself was red for a reason that had nothing to do with the code it was
judging — see §3.

## 2. How long, exactly — and the two wrong numbers this replaces

My brief said **four consecutive failures**. A mid-task correction said **"at
least ~420 consecutive red runs spanning 11+ days ... it may never have been
green"**, and asked whether the core suite had ever run in this project's
history.

Both are wrong, and the correction is wrong in the more expensive direction —
it would have sent the next session hunting a *succession* of causes that does
not exist. Measured against the Actions API (`curl` against
`/actions/workflows/ledger-core-tests.yml/runs`, filtered by `status=` and
`created=`; the counts below are GitHub's own `total_count`, not a page walk):

| reading | value |
|---|---|
| runs of this workflow, all time | **1658** |
| of which `success` | **370** |
| of which `failure` | **1288** |
| newest `success` | **2026-08-17T19:44:27Z**, `0d38986` |
| newest run | 2026-08-25T00:26:03Z, `80a9104`, failure |
| runs created after the last success | **311** |
| of those 311 that succeeded | **0** |

So: **311 consecutive red runs, over 7 days 2 hours 42 minutes** — not four,
and not 420 over 11+ days. The channel was green 370 times before that, so
"it may never have been green" is settled as false.

**The core test suite HAS run in CI, and passed — 370 times.** I read the step
list of the last green run (id 32062016985) rather than trusting its colour,
per `ci.md`: steps 1–10 all `success`, including step 9 `Run core test suite`
and step 10 `Run AI playtest (fake mode)`. That question is closed, with its
denominator: 370 of 1658 runs.

### There is ONE cause, not a succession

The correction reasoned that because `Proportion.cs` landed on 17 Aug and the
channel looked red on 14 Aug, earlier causes must have been masked. The
boundary window says otherwise. Every run between the last green and two hours
later:

    2026-08-17T19:44:27Z  0d38986  success     <- the last green
    2026-08-17T21:43:53Z  4f80405  failure     <- the first red
    2026-08-17T21:53:23Z  f802928  failure

`4f80405f` is committed at `2026-08-17T21:43:44+00:00`. **The first red run
started nine seconds after the commit that caused it, and the run immediately
before it was green.** There is no gap for an earlier cause to hide in, and no
period of "red for something else". One cause, all 311 runs.

I did not reproduce the correction's page-14 reading, and I did not spend
further probes trying to: the three `total_count` figures and the boundary
window are direct answers to the same question and they agree with each other.
What I have NOT established is whether any run before 2026-08-14 was red for a
different reason — 1288 failures are spread across 1658 runs all-time, so this
workflow has plenty of ordinary red history. That is not the same as being
dark, and I have not characterised it.

### How long each individual check was dark

All six were dark for exactly the same span, because they were all downstream
of the same step: **2026-08-17T21:43:53Z to 2026-08-25T00:26:03Z, 311 runs.**
docs-check, both shape checks, the attribution check, the core test suite and
the fake-mode playtest each ran 0 times in that window and `skipped` 311
times. The attribution check is the one worth flinching at: the voice corpus
is CC BY 4.0 and attribution is a licence obligation with a build failure
attached, and it has not executed in CI for a week.

## 3. The reach check was right about its world and its world was wrong

`Proportion.TryNeckFraction` and `Proportion.IsCaricature` were reported
"tested, unwired". **They are not unwired, and they never were.**

    ledger/Assets/Editor/CharacterPrefab.cs:193   Proportion.TryNeckFraction(...)
    ledger/Assets/Editor/CharacterPrefab.cs:199   Proportion.IsCaricature(...)

`git log --diff-filter=A -- Core/Proportion.cs` and `git log -S"Proportion.
IsCaricature" -- Editor/CharacterPrefab.cs` both return **the same commit**,
`4f80405f`. The API and its call site landed together; there was never a moment
when it was built and not running.

The call site is real behaviour, not a token reference: `CharacterPrefab`
measures each model's bone heights and, for a figure below `MinNeckFraction`,
`continue`s — the model gets no prefab and never reaches the street. Two of
ten models are excluded by it.

**So why did CI call it unwired?** Because there were two spellings of the
reach check and only one of them had been fixed:

* `ledger/verify.py` passed `--also ledger/Assets/Editor`, added 17 Aug with a
  comment saying exactly why ("the Editor layer is a real consumer ... went
  unscanned until 17 Aug, so anything it alone called read as unwired");
* `.github/workflows/ledger-core-tests.yml` did not.

Run both against today's tree, same machine, minutes apart:

    without --also : reach FAILED — 2 unreached, 0 stale ledger entries, 0 without a reason
    with    --also : reach ok — 35 on the ledger, 0 unexplained

That is rule 1's third corollary in its purest form: one idea, two
implementations, and the one nobody looks at is the one missing a line. It is
also rule 3 — the surprising result was the instrument, not the subject — and
the local/CI disagreement was the tell, exactly as `tools_tracked`'s docstring
already warns ("Local green and CI red with no code difference between them is
the worst shape a failure can take").

### The decision on the two APIs

**Neither wired nor allowlisted: they were already wired, and the correct
repair was to the instrument.** An allowlist entry would have been actively
harmful here — it would have recorded, in the reach ledger, the claim that
these APIs have no consumer, which is false, and CLAUDE.md already records
three ledger reasons that were wrong on one day for describing an intended
consumer rather than a real one. This would have been a fourth, and worse: not
a stale reason but one that was never true.

Nothing in `Proportion.cs` or `allow.json` was changed. `git diff` on both is
empty.

**The verdict number that shows a future session it is running**: it is not a
verdict key, it is the Windows build log line
`CharacterPrefab: {Variants} body prefab(s) written, {mannequins} rig
mannequin(s) skipped, {cartoons} caricature(s) skipped ...`, and it already
carries its denominators. `cartoons` moving off zero is the proof the bound
fires; `unmeasured` beside it is the count that stops "measured and fine" from
looking like "not measured". `reach ok — 35 on the ledger` is the proof the
call site is still seen.

## 4. What the workflow does now

Two files, and the checks are no longer steps.

**`tools/reach-check.sh`** — THE one invocation of ReachCheck, with `--also
ledger/Assets/Editor` in it. `verify.py`'s `reach()` now runs this script
instead of spelling the arguments out again, so the two cannot drift apart a
second time. `grep -rn ReachCheck` confirms no third copy exists.

**`tools/ci-checks.sh`** — runs every check, records each outcome, and exits
non-zero at the end listing failures by name with the pass count beside them:

    ci-checks done: passed=7/8 failed=reach-check:rc1

Properties, each for a named reason:

* **Not `continue-on-error` alone.** Every check still gates; the job is red
  whenever any check is red. What changed is that you can see which, and that
  a red reach check no longer hides the test suite.
* **`passed=N/M` is one entry carrying both halves.** A zero ships its
  denominator; an empty table prints `nothing measured — 0 checks in the
  table` and exits **3**, so a run that examined nothing cannot read as clean.
* **The done line is printed LAST**, after the failure detail. Rule 12: the
  only log channel this environment can read is a fixed ~4KB byte tail, and a
  detail block can run to seven — printing the done line first would push the
  one line naming the failure out of the readable window exactly when there is
  most to read. Selftest case [8] asserts it is the final line under 400 lines
  of detail.
* **Exit codes are distinct per outcome**: 0 all passed, 1 something failed,
  2 usage, 3 nothing measured, 4 the harness's own selftest failed.
* **The cap announces itself**: `(+332 earlier lines not shown — see the run
  above)`.
* **The attribution step became two checks**, `attribution` and
  `attribution-selftest`. They were one step running two commands, and "the
  licence audit failed" and "the licence auditor is broken" are different
  facts with different fixes that one step could not tell apart.

The workflow is now four steps: checkout, setup-dotnet, `bash
tools/ci-checks.sh`, and `bash tools/ci-checks.sh --selftest` guarded with
`if: ${{ !cancelled() }}` so a red check above cannot skip the harness's own
proof — reintroducing the skip one step later would have been the same fault
with a new name.

### The cap came from a printed series, not from a preference

`outLines` per check was printed by the tool before any bound existed in it.
Measured on this repository, 25 Aug:

| | lines |
|---|---|
| green run | reach-check 10, attribution 23, attribution-selftest 61, docs-check 91, playtest-fake 108, shape-check 156, shape-check-selftest 452, core-tests 3877 |
| failing run | reach-check 13 (844 bytes), docs-check 88 (5393 bytes) |
| density | 42.2–83.4 bytes/line, median ~60 |

`TAIL_LINES=120` covers the whole output of five of eight, including both
checks measured failing; it truncates shape-check (−36), shape-check-selftest
(−332) and core-tests (−3757), and says so each time. The **tail** is the
right end for seven of the eight: CoreTests throws on first failure and prints
`FAILED: ...` as its last line, and reach-check, shape-check, attribution and
the playtest all summarise at the end. **`docs-check` is the exception** — it
prints the offending document inline in alphabetical order and its last line
is only `1 problem(s)`. That is why the cap is 120 rather than the ~68 lines
that fit a 4KB window, and why the full output is also left printed where it
happened. A future session moving this bound should move it on that evidence.

## 5. Both ways, actually run

### The harness, synthetic fixtures, accepting case first

`bash tools/ci-checks.sh --selftest` → **exit 0, passed=15/15**. Cases: [1]
all-pass exits 0 saying `passed=3/3 failed=none`; [2] one failure exits 1
naming `b:rc1`; **[3] the actual fault — a check after a failure still ran**
(`I-STILL-RAN`, `SO-DID-I`) and the job is still red; [4] every check red,
real exit codes preserved (`rc=7`); [5] empty table exits 3 with `nothing
measured`; [6] the cap announces `(+15 earlier lines not shown`; [7] a missing
binary is a failure, not a pass; [8] the done line is last.

The fixtures are synthetic (`true`, `false`, `exit 7`) so doing the work the
harness prompts can never break the harness, and they go through the **same**
`run_table` function as the real table — a selftest exercising a different
code path proves nothing about the thing shipped.

### The real table on the live repository — the accepting case

    check name=reach-check           outcome=PASS rc=0 secs=4 outLines=9
    check name=docs-check            outcome=PASS rc=0 secs=0 outLines=90
    check name=shape-check           outcome=PASS rc=0 secs=1 outLines=155
    check name=shape-check-selftest  outcome=PASS rc=0 secs=0 outLines=451
    check name=attribution           outcome=PASS rc=0 secs=0 outLines=22
    check name=attribution-selftest  outcome=PASS rc=0 secs=0 outLines=60
    check name=core-tests            outcome=PASS rc=0 secs=4 outLines=3876
    check name=playtest-fake         outcome=PASS rc=0 secs=7 outLines=107

    ci-checks done: passed=8/8 failed=none          exit 0

The whole cheap channel, green, in about 16 seconds of check time — the first
time all eight have reported together since 17 August.

### The real table with a real failure — the rejecting case

Reproduced by temporarily removing `--also` from `tools/reach-check.sh`, i.e.
putting the world back the way the workflow had it, then restoring the file
(`diff` confirms it is byte-identical afterwards). Nothing shared was touched.

    check name=reach-check   outcome=FAIL rc=1 secs=5 outLines=13
    check name=docs-check    outcome=PASS ...
    ... all six formerly-skipped checks ran and passed ...
    check name=playtest-fake outcome=PASS rc=0 secs=7 outLines=107

    UNREACHED — 2 behavioural Core API(s) with no caller:
      tested, unwired method   Proportion.TryNeckFraction   Proportion.cs:48
      tested, unwired method   Proportion.IsCaricature      Proportion.cs:127
    reach FAILED — 2 unreached, 0 stale ledger entries, 0 without a reason

    ci-checks done: passed=7/8 failed=reach-check:rc1     exit 1

This is the whole change in one reading. Same fault, same red job — and now
the seven checks it used to hide all reported, the failing one is named on the
last line, and the count says how much was examined.

## 6. A second fault found on the way: the same bug one layer out

`verify.py`'s `tools_tracked()` exists because `ReachCheck`, `BalanceLab` and
`BarkGen` were once built and tested locally and never committed, so CI ran
`dotnet run --project ledger/ReachCheck` against a directory with no project.
It checked `ledger/*/*.csproj` and nothing else.

The workflow now invokes `tools/ci-checks.sh` **by path**, and an uncommitted
script produces the identical shape: local green, CI red, "No such file or
directory", no code difference between them. So the check was extended to
every `tools/*.py` and `tools/*.sh` named in a workflow, **transitively** —
the first version stopped at one hop, caught `ci-checks.sh` and missed
`reach-check.sh`, which is the same "the copy nobody looks at" shape it exists
to stop.

Both ways, run on this tree:

    rejecting  (False, 'UNTRACKED/ABSENT TOOL(S): tools/ci-checks.sh(untracked), tools/reach-check.sh(untracked)')
    accepting  (True,  '15 tool project(s) + 18 workflow-named tool(s) in 9 workflow(s) tracked')

The accepting case was produced with `git add -N` on those two paths only and
reverted with `git reset -- <paths>`; `git status --porcelain` shows `??` for
both before and after, so the index is exactly as it was. **The reviewer must
`git add tools/ci-checks.sh tools/reach-check.sh` before `verify.py` will go
green** — that is the check doing its job, and it is the difference between
finding this now and finding it as another dark week.

## 7. Every other workflow, checked for the same shape

Nine workflows, twelve jobs, analysed for the longest chain of consecutive
unguarded `run:` steps (a step is guarded by `continue-on-error` or an `if:`
containing `always`/`cancelled`):

| workflow | job | steps | guarded | longest unguarded chain |
|---|---|---|---|---|
| tier2-generate | generate | 11 | 1 | **8** |
| ledger-build-windows | build-windows | 18 | 6 | 5 |
| citypack-fetch | fetch | 11 | 5 | 2 |
| ledger-ai-playtest | ai-playtest | 5 | 1 | 2 |
| ledger-build-mac | build-mac | 12 | 4 | 2 |
| props-fetch | fetch-props | 7 | 3 | 2 |
| voice-candidates | inventory / page | 6 / 4 | 2 / 0 | 2 / 2 |
| citypack-inventory | inventory | 7 | 4 | 1 |
| voice-candidates | diagnose / candidates | 4 / 9 | 1 / 6 | 1 / 1 |
| **ledger-core-tests** | core-tests | **4** | **1** | **1** (was 8, unguarded 0) |

The chain length alone is not the fault, and reading it as one would repeat
the mistake this report is about. Fail-fast is **correct** for a pipeline
(step B is meaningless if A produced nothing) and **wrong** for independent
checks (each answers its own question). Opened each of the three longest:

* **`tier2-generate.yml` — NOT the fault.** Its 8-chain is a genuine pipeline:
  prove the probe → read what characters say → commit the transcript → does
  any card need a voice → give it one → audit → commit. Each step consumes the
  previous step's output. It is also `workflow_dispatch` only.
* **`ledger-ai-playtest.yml` — the closest sibling, and its fail-fast is
  defensible.** `Playtest (fake mode)` then `Playtest (live mode, if key
  configured)` are two independent questions with no final verdict step, which
  is the core-tests shape exactly — **except that live mode spends real
  Anthropic API credit**, and not spending it when the free deterministic
  harness is already broken is a considered trade, not an oversight. I have
  left it alone deliberately; "fixing" it would have bought unnecessary spend.
  What it genuinely lacks is a line naming which of the two failed, and with
  two named steps that ambiguity is small.
* **`ledger-build-mac.yml` and `ledger-build-windows.yml` — a bounded
  instance.** `Lint (missing usings)` then `Shape check (Unity layer)` are two
  independent checks in sequence, so a lint failure skips the shape check.
  Both jobs do end in an `if: always()` `Verdict` step, so neither is dark —
  but that verdict reports the SIM, not the pre-build checks, so "lint failed"
  and "the sim did not run" print the same sentence, which CLAUDE.md already
  records as costing minutes of reading correct C#. **Recommended, not done
  here**: have the Windows/mac `Verdict` step name the outcomes of the lint
  and shape steps as `citypack-fetch.yml` and `props-fetch.yml` already do
  (`[ "${{ steps.X.outcome }}" = "success" ] || { echo "..."; bad=1; }`). I
  did not touch the Windows workflow: other agents dispatch it, and it is the
  one channel that cannot be tested from here.
* `citypack-fetch.yml` and `props-fetch.yml` **already have the good shape** —
  per-step `continue-on-error` plus a final step reading each outcome and
  failing named. That shape was the model for `ci-checks.sh`; the script adds
  what YAML could not have: a selftest.

## 8. What this triggers (rule 9)

Checked, not assumed. No other workflow lists `.github/**` or
`ledger-core-tests.yml` in its paths, and `ledger-build-windows.yml` is
`workflow_dispatch:` only. So editing the workflow, the two scripts or
`verify.py` starts the cheap ubuntu job and nothing else — no 28-minute round
trip, no contention for the single Unity licence seat.

One trigger gap was found and closed: the workflow's paths listed `tools/*.py`
but not `tools/*.sh`, so the scripts that now ARE the job would not have
re-run it. `tools/*.sh` is added. It is a single-level glob and does not match
`tools/voice-fetch/**`, so it cannot start the voice job.

## 9. Which existing conclusions this overturns

1. **"`Proportion.TryNeckFraction` and `IsCaricature` are tested and called by
   nothing" — overturned.** They were called from the commit they were born
   in. The reach ledger was correct to have no entry for them.
2. **"Four consecutive failures" — overturned.** 311, over 7 days 2 hours.
3. **"~420 reds over 11+ days, a succession of causes, may never have been
   green" — overturned.** 311 reds, one cause, and 370 prior successes.
4. **"Has the core test suite ever run in CI?" — settled: yes, 370 times**,
   last on 2026-08-17T19:44:27Z, step 9 `success`, read from the step list
   rather than the job colour.
5. **Confirmed:** the local/CI disagreement named in the brief was real and
   was the whole story — `verify.py` was green because it scanned the Editor
   layer and CI was red because it did not. Nothing about the check was
   non-fatal or skipped locally; it reported into the footer the entire time,
   correctly, about a different world.

## 10. `python3 ledger/verify.py` — exit 1, and both reds are named

Run on this tree after every change above. **Exit 1, footer NOT GREEN.** Two
entries are red and neither is a fault in the work:

    DIRECTOR NOT SPAWNED: 525 changed line(s) (525 tracked + 0 untracked in 0 new
    file(s)) vs 100 threshold under Assets/Scripts, 0 director row(s) since HEAD
    of 41 log row(s) examined — spawn studio-director for the batch review

    UNTRACKED/ABSENT TOOL(S): tools/ci-checks.sh(untracked), tools/reach-check.sh(untracked)

1. **`director_cadence`** — 525 changed lines under `Assets/Scripts`, none of
   them mine. `git diff --name-only -- ledger/Assets/Scripts` returns
   `AssetLibrary.cs`, `SimDirector.cs`, `WorldBuilder.cs`, which are three of
   the four files I was told not to touch and are other agents' live work.
   This is the hybrid-resident escalation gate asking for a batch review, and
   it is unrelated to this task.
2. **`tools_tracked`** — my own new check (§6) firing on my own two
   uncommitted scripts, by design. It clears the moment the reviewer runs
   `git add tools/ci-checks.sh tools/reach-check.sh`, demonstrated in §6.

**Everything else is green, and two entries are the direct evidence for this
work:**

* `35 on the reach ledger` — `verify.py`'s `reach()` now runs through
  `tools/reach-check.sh` and still reports exactly what it reported before the
  refactor. The single invocation works from the Python caller.
* `workflow steps ok (17088 under the dispatch ceiling)` — the rewritten
  workflow is still dispatchable, so the Windows build cannot have been broken
  by it.

Also green and worth naming because they were among the six checks dark for a
week, now confirmed passing locally as well as in `ci-checks.sh`:
`0 shape errors (183 files)`, `docs 61/61 clean`, `16 attribution check(s)`,
`3761 CoreTests`.

### My edit footprint, exactly

    .github/workflows/ledger-core-tests.yml | 75 +++++++++++++-------------
    ledger/verify.py                        | 80 ++++++++++++++++++--------
    tools/ci-checks.sh                       (new, untracked)
    tools/reach-check.sh                     (new, untracked)

`Proportion.cs`, `ReachCheck/allow.json`, `CharacterPrefab.cs`, `queue.md`,
`decision-ground-albedo.md`, `ref-bench.py` and everything under
`Assets/Scripts` are untouched by me — verified with `git diff --quiet` per
path, not asserted.
