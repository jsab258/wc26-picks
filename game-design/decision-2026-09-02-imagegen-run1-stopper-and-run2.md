# DIRECTOR RULING: run 1's stopper is named from a positive record and the fix lands; the stop rule is sharpened; a second silent fault gets its instrument; the landing push is run 2 (2 Sep 2026, 17:20Z)

> **STATUS — LOG, 2026-09-02. NOT CURRENT once the batch is committed with W1 to W4, S1, Q1, Q2 and N1 applied and imagegen run 2 has landed a verdict; from then the workflow, the committed verdict, queue 043 and 044 and production/NOW.md are the reading copies and this file is their history.**

This document carries exactly one em-dash, in the banner, because
`tools/docs-check.py` line 55 accepts no other form (read this session).

Twelfth ruling since 1 September. No shell in this spawn: every number
below was read from a file this session and the file and line are named
beside it. The builder's report and the resident's brief were read as
CLAIMS; the workflow, the tool, the reflog, the queue and imagegen.py were
read as evidence. Cost: roughly 2 points against 38 percent at 17:00Z, no
daily ration (NOW.md 79 to 82).

## What was verified

- My row: `.claude/agent-log.tsv` line 210, `2026-09-02T17:20:14Z
  studio-director`, the newest in the file. `.git/logs/HEAD` line 370: the
  newest commit is `decf1cb6` at epoch 1788368446 (17:00:46Z). My row is
  newer than every commit in the reflog. Line 367 is `b8b805f2`, the batch
  push that was run 1.
- `.github/workflows/ledger-imagegen.yml` in full (521 lines): the rule
  142 to 176; ids on all five setup steps (184, 193, 203, 217, 274); the
  sha step 273 to 320 with `safe.directory` at 278 to 280, `set +e` at
  285, the fallback at 299 to 303, `shaSource=` at 309, the both-empty
  stop at 310 to 313; the commit step 397 to 474 with `SETUP_STEPS` at 413
  fed CONCLUSIONS, the stopper call at 425, the `steps` string at 426, the
  staging loop 446 to 450; the last step 480 to 520 with the tool call
  499 to 507 and the `if` at 517.
- `tools/runner/step-verdict.sh` in full (275 lines): `split_commas` 61
  with the trailing newline the builder's accepting case caught;
  `find_stopper` 78 to 88 (first red in declared order); `summarise` 90
  to 150, the four states 112 to 137, the denominator line 147, the
  nothing-measured line 144; the selftest 171 to 251, and I COUNTED 32
  `_want`/`_wantnot` calls between lines 180 and 247, accepting case
  first at 180 to 184. Both callers exist in the workflow (425, 499), so
  rule 6 is satisfied by grep. I did NOT run it; L1 does.
- The differential, checked rather than accepted: grep of
  `.github/workflows` for `safe.directory` hits setup-msvc 268,
  build-windows 579, probe-unreal 694, vignette-fetch 144, and imagegen
  279 and 404 (both new or already there). Grep for `git rev-parse` shows
  every other bash-step call sits under one of those env blocks;
  probe-unreal 115 to 126 records `git rev-parse --short HEAD` returning
  nothing on this machine and falling back to GITHUB_SHA.
- THE POSITIVE HALF, which the brief did not name: queue 043 lines 37 to
  41 quote run 1's verdict as `NO RUN - this commit (b8b805f) generated
  no picture: manifest written by run none not b8b805f`. That sha came
  from the commit step's own `git rev-parse HEAD | cut -c1-7` (old line
  283, now 416), under `-e`, in the step that carries `safe.directory`.
  So in ONE run git succeeded in the step that has the env and failed in
  the step that lacked it. That is the same variable moved with everything
  else held still, and I accept it as strong support. WHICH message git
  printed is still unproven and run 2 prints it (workflow 297 to 298).
- The second fault. Queue 043 line 41 and NOW.md 103: run 1 printed a
  verdict and then `staged=0`. `imagegen.py` `staged_file_list` 2420 to
  2466 ALWAYS wants the verdict (2449) and prints it relative to `--repo`
  via `as_posix()` (2442), so a printed verdict with `staged=0` means the
  bash side rejected the line or `git add` failed. Nothing in `.gitignore`
  or `ledger/.gitignore` covers the path (grep). No error text is quoted.
  Windows Python translates every stdout `\n` to `\r\n`, pipe or not;
  bash `read -r` keeps the `\r`; `[ -e "$f" ]` then names a file that does
  not exist and the loop moves on in silence. The vignette-fetch loop is
  the same shape (163 to 166) and `production/assets/vignette/` holds
  neither `surfaces/` (its DEST, fetch_vignette.py 60) nor
  `fetch-verdict.txt` (61); the 06:47 ruling line 510 says the same. No
  landed run in this tree has ever staged a path printed by Windows Python
  through a bash loop: probe-unreal (741 to 755) and setup-msvc (291)
  stage literal names. A theory, consistent with two absences and one
  mechanism, and Ruling 4 makes run 2 measure it.
- The bash claim at workflow 513 to 516 is FALSE. `set -e` exempts "any
  command executed in a && or || list except the command following the
  final && or ||", so `[ "$bad" -eq 0 ] && echo ...` with `bad=1` fails on
  the left of `&&` and does not end the step; `exit $bad` was always
  reached. vignette-fetch line 202 is the same form on a workflow that has
  run. The `if` is kept because it is clearer; the reason is corrected
  (W2), because that sentence would be quoted later as a bash fact.
- `imagegen.py`: the argparse default 3733 turns an empty GITHUB_SHA into
  `local`, but an explicit `--run-sha ""` passes through; `fresh` is
  computed twice, 2302 (`(man.get("run") or {})`, null-safe) and 2448
  (`.get("run", {})`, not), one expression in two copies. The verdict is
  written by `write_text` at 2415 with default newline handling, so on
  Windows the committed file will carry CRLF; run 2's file is opened for
  that (Ruling 7).
- `ledger/verify.py` 306 to 339: every `tools/*.sh` named in a workflow
  must be tracked, which is the `UNTRACKED/ABSENT TOOL(S)` red and clears
  on staging. `DIRECTOR_WORK` 2345 to 2357 includes `tools/` and
  `.github/workflows/`. Queue: 043 is the item; 044 is free.

## Ruling 1: the batch LANDS, one commit, after L1 to L5

Nothing weakens an instrument; one instrument that did not exist now does
(three states plus a fourth, both callers wired, the stopper in the
committed channel), and the fix is cause-agnostic where the cause is
unproven and evidenced where it is. Premise check: nothing here touches a
world fact or the engine decision; it is the free lane's evidence channel,
which serves the D1 comparison and costs zero points.

L1. `bash tools/runner/step-verdict.sh --selftest` run by the resident,
and its last line `step-verdict selftest: PASS` quoted in the commit
message with the count of `ok` lines (32 expected). Then
`python3 ledger/verify.py` green, footer FROM THE FILE.

L2. Staged by name and nothing else: `.github/workflows/ledger-imagegen.yml`,
`tools/runner/step-verdict.sh`, `production/d1-probe/RUN-IMAGEGEN`,
`production/queue/043-skipped-is-not-failed.md`,
`production/queue/044-imagegen-tested-layer-edges.md`, `production/NOW.md`
and this record. `git status --porcelain` read in full first; a pending
work path not in this record's `paths=` is left out and this director is
RESUMED with the list.

L3. W1 to W4 applied to the workflow; S1, Q1, Q2, N1 applied. Every id
listed in the commit message as `applied` or `deferred: <reason>`.

L4. `tools/imagegen/imagegen.py` is NOT edited in this batch (Ruling 5).

L5. Push, and know what it triggers (rule 9): `ledger-imagegen.yml` on the
sentinel, once, run 2; `ledger-core-tests.yml` on `game-design/**`,
cheap. Nothing Unity, nothing on the licence seat, and NOW.md 114 says
nothing is running on the PC.

## Ruling 2: the stopper is named, the command is not, and that is recorded as two facts

The API's per-step conclusions are a positive record and the differential
has both halves in one run (verified above). The finding stands as: run 1
stopped at `The commit this run is measuring` because git was unusable in
the only bash step that ran it without `safe.directory`. What git SAID is
not known and is not claimed; run 2 prints its stderr (297 to 298) and
`shaSource=` (309), so the next reading is a sentence and not an
inference. If run 2 prints `shaSource=event`, the env was not the whole
story and the printed stderr is the next lead; that is a finding, not a
regression.

## Ruling 3: the stop rule stands, sharpened by one sentence

The rule is right in shape and I approve it as the line that gets quoted:
a step stops the job if and only if what it proves is a precondition for
doing the work safely. The tempting alternative, `continue-on-error`
everywhere, would let a batch be generated by a toolchain nothing checked
and then banked, which is the green-number-for-a-frame failure this project
keeps paying for. The stated cost (a broken toolchain still burns a
dispatch and answers nothing about the GPU) is accepted; the GPU answer is
available from probe-unreal and setup-msvc without risking a banked batch.

Two corrections. First, the second sentence as written ("a step that only
reads a label ... never stops it") contradicts its own application four
paragraphs later (the sha step keeps its red when both sources are empty).
A rule that its first example breaks is not a rule. Second, "generating
safely" is the wrong noun: the sha is a precondition for BANKING, and
banking is why an unnamed batch is refused. W1 rewrites the sentence so
the rule and its application agree.

## Ruling 4: the second fault gets its instrument in the same run, and a strip on a theory is admissible because it cannot hide a regression

Run 1 wrote a verdict that never reached the channel. The theory (a
trailing `\r` from Windows Python) is consistent with every fact in hand
and proven by none. Rule 3 says measure before acting, so W4 does both in
the right order: it prints every staging candidate with `printf %q`, which
shows a carriage return as `$'\r'` and an ordinary path as itself, and
THEN strips one trailing `\r` before the existence test. The strip is not
a guard and rule 5b does not apply: on a line with no `\r` it changes
nothing, so the accepting case is the current behaviour and it cannot turn
a regression green. If run 2's `stage-candidate=` lines show no `$'\r'`
and `staged=` is still 0, the `NOT ON DISK` line and git's own stderr are
now in the log, and the theory is recorded as refuted in 044.

The vignette-fetch twin (163 to 166) is the same fault if this is a fault,
and rule 1 says every hit gets read. It is NOT edited tonight: nothing
dispatches it, and a fix applied on a theory to a workflow nobody is
watching is the drift this project's rules exist to stop. 044 item (3)
applies it the moment run 2 says which way.

## Ruling 5: the `--run-sha ""` hole is closed from the workflow side twice tonight and from the tested layer in 044

The builder was right to name it and right not to close it in a workflow
edit. Today the sha step exits 1 when both sources are empty (310 to 313),
and W3 makes the commit step fall back to `none`, which imagegen.py already
refuses as fresh (2302, 2448), instead of a `git rev-parse` that would
kill the step under `-e` before any verdict was written, in exactly the
case where the verdict is the only evidence. That is two closures of the
one route this run can take. The tested-layer closure (one helper for the
two `fresh` copies, an empty sha never fresh, an empty `--run-sha` refused
at the door, fixtures both ways) is queue 044, and it does not block a run
that costs zero points and answers the GPU question tonight.

## Ruling 6: the re-dispatch goes on the landing push, immediately

The sentinel is the trigger (108 to 110) and S1 touches it, so the push
that lands this ruling IS run 2. Nothing else is on the PC (NOW.md 114),
tomorrow's Unity dispatch is a session away, and the ceiling is 130
minutes. Read, in this order, before opening anything: the committed
verdict's line 1 (the sha must be the landing commit's); the `steps` line,
where `stopper=none shaFrom=checkout` is the fix confirmed and
`stopper=<name>` is the next finding already named; the `done
imagegenVerdict=` line; the log's `stage-candidate=` lines, `runnerAccount=`
and `weightsDirectory=`. Then open the four PNGs (rule 4), and open the
verdict file itself for CRLF, which is 044's third edge if present. No
commit at all after the run concludes means `staged=0` again, and the `%q`
lines say why.

## Dictated edits. Each id is listed in the commit message as applied or deferred with a reason

**W1. `.github/workflows/ledger-imagegen.yml`** lines 149 to 151 become:

```
    #   A STEP MAY STOP THE JOB IF, AND ONLY IF, WHAT IT PROVES IS A
    #   PRECONDITION FOR GENERATING AND BANKING SAFELY. A step that only
    #   reads a LABEL carries a named fallback and prints which source won;
    #   it stops the job only when every source is empty, because a batch
    #   with no name cannot be banked and generating it spends the GPU on
    #   nothing.
```

**W2. `.github/workflows/ledger-imagegen.yml`** lines 513 to 516 become:

```
          # `if`, not `[ ... ] && echo`. The two behave the same under -e (a
          # failing left-hand side of && is exempt from errexit, so the old
          # form reached `exit $bad` too); `if` is kept because it says what
          # it means without sending the reader to the bash manual.
```

**W3. `.github/workflows/ledger-imagegen.yml`** line 416 becomes:

```
          # THE NAME COMES FROM THE SHA STEP, ELSE FROM THE EVENT, ELSE IT IS
          # `none`, WHICH imagegen.py REFUSES AS FRESH. Never git here: this
          # step runs under -e, and a git that failed the sha step would end
          # it before the verdict was written, in exactly the run where the
          # verdict is the only evidence of what stopped it.
          SHORT="${IMAGEGEN_SHA:-}"
          SRC="${IMAGEGEN_SHA_SOURCE:-none}"
          if [ -z "$SHORT" ] && printf '%s' "${GITHUB_SHA:-}" | grep -Eq '^[0-9a-f]{7,40}$'; then
            SHORT="$(printf '%s' "$GITHUB_SHA" | cut -c1-7)"
            SRC="event-at-commit"
          fi
          SHORT="${SHORT:-none}"
```

and on line 426 `shaFrom=${IMAGEGEN_SHA_SOURCE:-none}` becomes
`shaFrom=$SRC`.

**W4. `.github/workflows/ledger-imagegen.yml`** lines 445 to 450 become:

```
          staged=0
          while read -r f; do
            # PRINTED WITH %q BEFORE ANYTHING TOUCHES IT. Windows Python ends
            # every stdout line in \r\n, pipe or not, and bash keeps the \r;
            # `[ -e "$f" ]` then names a file that does not exist and the
            # loop goes on in silence, which is the one reading of run 1's
            # `staged=0` beside a verdict that had just been printed. A
            # carriage return shows here as $'\r'; measured, then stripped.
            printf 'stage-candidate=%q\n' "$f"
            f="${f%$'\r'}"
            [ -n "$f" ] || continue
            if [ -e "$f" ]; then
              git add -- "$f" && staged=$((staged + 1))
            else
              echo "  NOT ON DISK under $PWD, not staged"
            fi
          done < <(python3 tools/imagegen/imagegen.py --staged-files \
                     --repo "$GITHUB_WORKSPACE" --run-sha "$SHORT")
```

**S1. `production/d1-probe/RUN-IMAGEGEN`**, append after line 44:

```
#
# run 1 - RAN 2026-09-02 on b8b805f2 (run 33654488608), 105 s, FAILED at the
# setup step `The commit this run is measuring` in 0 s; all four work steps
# skipped; nothing banked, nothing carried forward. Cause: git ran in that
# step without the safe.directory env every other git step on ledger-pc
# carries, and the commit step's own git rev-parse succeeded under it in the
# same run. A second fault: the verdict was printed and staged=0. Ruling:
# game-design/decision-2026-09-02-imagegen-run1-stopper-and-run2.md.
#
# run 2 - fired by the push that lands that ruling. Same four items expected.
# The verdict's steps line now carries stopper= and shaFrom=, and the commit
# step prints every staging candidate with %q, so a trailing \r from Windows
# Python shows as $'\r' and the second fault is measured, not believed.
```

**Q1. `production/queue/043-skipped-is-not-failed.md`** line 5 becomes:

```
status: LANDED 2026-09-02 (game-design/decision-2026-09-02-imagegen-run1-stopper-and-run2.md): tools/runner/step-verdict.sh, three states plus NO-READABLE-OUTCOME, 32 checks accepting first, both callers wired; the stopper and shaFrom ride the committed verdict's steps line; the sha step carries safe.directory, a GITHUB_SHA fallback and prints git's stderr. Item 3 decided, no blanket continue-on-error, the rule is written above `steps:` in the workflow. Proven by run 2's committed verdict, not by this line.
```

**Q2. `production/queue/044-imagegen-tested-layer-edges.md`**, new file:

```
line: infrastructure (instruments, the imagegen evidence channel)
spec: game-design/decision-2026-09-02-imagegen-run1-stopper-and-run2.md, Rulings 4 and 5
acceptance: (1) one helper decides "the manifest is this run's" for imagegen_verdict and staged_file_list (today two copies of one expression, imagegen.py 2302 and 2448, one of them not null-safe), and an empty or whitespace sha is never fresh: fixture with manifest stamped "" and --run-sha "" reads NO-RUN and stages only the verdict (rejecting), manifest stamped abc1234 and --run-sha abc1234 reads fresh and stages the manifest's files (accepting, first); (2) an empty --run-sha on the generate path is refused at argparse with exit 2 and the words, so no manifest is ever stamped with a name that means nothing; (3) read from run 2's log: if any `stage-candidate=` line shows $'\r', the vignette-fetch loop (ledger-vignette-fetch.yml 163 to 166) gets the same strip and print, and the imagegen verdict writer (2415) passes newline="\n" so the committed file carries no CR; if none does, record what run 2's staged= line and NOT ON DISK lines said instead and close (3) as refuted
max_sessions: 1
status: READY 2026-09-02. engine-specialist, small. Rides the next imagegen touch, after run 2's verdict has been read. Not blocking run 2: the workflow closes the empty-sha route twice (the sha step exits 1 when both sources are empty; the commit step falls back to `none`, which imagegen.py already refuses as fresh).
```

**N1. `production/NOW.md`** lines 84 to 118 (from `IMAGEGEN RUN 1 RAN AND
FAILED` to the end of `## In flight`) become:

```
IMAGEGEN RUN 1 RAN AND FAILED AT ONE SETUP STEP, AND THE FIX IS LANDED. Run
33654488608 on b8b805f2: the API's per-step conclusions put the only
failure at `The commit this run is measuring`, 0 seconds, and the four work
steps skipped behind it. Cause, from a differential over .github/workflows:
that step ran git without the safe.directory env every other git step on
ledger-pc carries, and the commit step's own git rev-parse succeeded under
it in the same run. The summary that named three causes it never observed
is replaced by tools/runner/step-verdict.sh (three states plus
NO-READABLE-OUTCOME, 32 checks). Ruling:
game-design/decision-2026-09-02-imagegen-run1-stopper-and-run2.md.

A SECOND FAULT IS NAMED AND NOT YET PROVEN: run 1 printed a verdict and
then `staged=0`, so the verdict never reached the committed channel.
Reading: Windows Python ends every stdout line in \r\n and bash keeps the
\r, so `[ -e "$f" ]` looked for a name ending in a carriage return. Run 2
prints every candidate with %q and strips it, which is the measurement.
The vignette-fetch loop is the same shape and has never staged a file in
this tree either (no fetch-verdict.txt, no surfaces/); queue 044 carries it.

## In flight

- Imagegen run 2, fired by the push that landed the ruling. Watch by
  ancestry for a commit titled `Meridian pictures from <sha>`. Read, in this
  order: the verdict's line 1 (the sha must be the landing commit's), the
  `steps` line (`stopper=none shaFrom=checkout` is the fix confirmed;
  `stopper=<name>` is the next finding, named), the `done imagegenVerdict=`
  line, then the log's `stage-candidate=` lines (a $'\r' confirms the
  second fault and its strip), `runnerAccount=` and `weightsDirectory=`.
  Then open the four PNGs, and open the verdict file for CRLF. No commit at
  all after the run concludes is `staged=0` again, and the %q lines say why.
- NEXT ACTION, tomorrow: slot 1 is the 027 Phase A close-out (040, A2,
  041), one engine-specialist, one Unity dispatch at the end; slot 2 is 037.
  Queue 044 rides the next imagegen touch after run 2 is read. The report
  to Jafar after run 2 carries one of the four signs, or the verdict's
  stopper if red.
```

**Not edited, and why.** `tools/imagegen/imagegen.py`: the hole is closed
with its fixtures in 044, not by hand (Ruling 5).
`ledger-vignette-fetch.yml`: the twin waits for run 2's measurement
(Ruling 4). `ledger/verify.py`: untouched; its red clears on staging.
`production/quality-ladder.md`: 043 closes on run 2's verdict, not here;
the next rung is named (044). `canon.md`: no world fact touched.

## Deliberately not decided

- What git printed in run 1. Run 2 prints it.
- Whether `staged=0` was a carriage return. Run 2's `%q` lines say.
- Whether run 2 pays the download. `runnerAccount=` and `weightsDirectory=`.
- The engine. Unchanged.

## For the next session in one line each

- Apply W1 to W4, S1, Q1, Q2, N1; run the tool's selftest and quote its
  last line; `git status` against the `paths=` list; verify; one commit
  staged by name listing every id; push, and that push is run 2.
- When run 2 lands: line 1, the `steps` line, the done line, the `%q`
  lines, the account and weights lines, then the four PNGs and the file's
  line endings; one report to Jafar with a sign as the picture.
- Resume this director, never restart, if git status shows a pending work
  path the stamp below does not list, if the selftest prints anything but
  PASS, or if run 2 stops at a step the committed verdict does not name.

Spawn row, quoted verbatim from `.claude/agent-log.tsv` (line 210):

    2026-09-02T17:20:14Z	studio-director

<!--RULING spawn=2026-09-02T17:20:14Z paths=.github/workflows/ledger-imagegen.yml,tools/runner/step-verdict.sh,production/d1-probe/RUN-IMAGEGEN,production/queue/043-skipped-is-not-failed.md,production/queue/044-imagegen-tested-layer-edges.md,production/NOW.md,game-design/decision-2026-09-02-imagegen-run1-stopper-and-run2.md-->
