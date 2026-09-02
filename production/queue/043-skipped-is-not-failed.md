line: infrastructure (instruments)
spec: this file, from imagegen run 1
acceptance: the summary step distinguishes skipped from failed and from success, and says WHICH step stopped the run; a skipped step never produces a sentence naming a cause that was never observed; both outcomes fixtured
max_sessions: 1
status: LANDED 2026-09-02 (game-design/decision-2026-09-02-imagegen-run1-stopper-and-run2.md): tools/runner/step-verdict.sh, three states plus NO-READABLE-OUTCOME, 32 checks accepting first, both callers wired; the stopper and shaFrom ride the committed verdict's steps line; the sha step carries safe.directory, a GITHUB_SHA fallback and prints git's stderr. Item 3 decided, no blanket continue-on-error, the rule is written above `steps:` in the workflow. Proven by run 2's committed verdict, not by this line.

## What run 1 actually did

Run 33654488608, commit `b8b805f2`, 105 seconds, conclusion failure. The
four work steps (selftest, probe, generate, attribution) were **SKIPPED**,
not run: the job env carries `SELFTEST_OUTCOME: skipped`,
`PROBE_OUTCOME: skipped`, `GENERATE_OUTCOME: skipped`,
`ATTRIB_OUTCOME: skipped`. None of them has an `if:` condition, so a step
BEFORE them failed without `continue-on-error` and Actions skipped the rest.
`Commit` and `The verdict` still ran because both carry `if: always()`.

## The instrument fault, which is worse than the failure

The summary step tests each outcome against `success` and prints a cause on
anything else. So it printed:

    SELFTEST FAILED - imagegen.py does not pass its own checks on this machine
    ATTRIBUTION CHECK FAILED
    GENERATE FAILED - the exit code says which: 2 disk, 3 setup, ...

**None of that happened.** The selftest passes on this container (123/123)
and never ran on that machine. A skipped step and a failed step are
indistinguishable to that summary, so it named three causes it did not
observe, in the confident voice of a diagnosis. Somebody debugging from it
would have gone looking for a Windows selftest failure that does not exist.

That is the same family as every instrument fault this project records: a
message that describes something the instrument never measured.

## What worked, and it is the reason the channel is trustworthy

The VERDICT did not lie. It printed
`steps selftest=skipped,probe=skipped,generate=skipped,attribution=skipped`,
`NO RUN - this commit (b8b805f) generated no picture: manifest written by
run none not b8b805f. Nothing older is being read as this run's answer.`,
`staged=0` and `nothing arrived that was not already committed`. Fourteen
existing PNGs sat right there and NONE was carried forward as this run's
work. That is exactly what it was built to refuse.

## THE FAILING STEP, narrowed from evidence already in hand

Not read from the head of the log, but inferred from the log's own env
dumps, and the reasoning is checkable:

The `Commit what arrived, by name` step dumps its environment, and that dump
carries `BATCH_LIMIT`, `BATCH_ONLY`, `BATCH_MAX_MINUTES`, `IMAGEGEN_WS`,
`IMAGEGEN_MACHINE`, `GH_TOKEN`, the three `GIT_CONFIG_*` and the four
`*_OUTCOME` variables. **It does NOT carry `IMAGEGEN_SHA`.**

`IMAGEGEN_SHA` is written by the step `The commit this run is measuring`
(workflow line 194), which runs
`SHORT="$(git rev-parse HEAD | cut -c1-7)"` and echoes it into
`$GITHUB_ENV` under `shell: bash` with the runner's default `-e -o
pipefail`. `IMAGEGEN_WS` and `IMAGEGEN_MACHINE` ARE present, and they are
written by an earlier step, so the job got that far.

So the prime suspect is line 194, and it is the LAST step before the four
that were skipped, which is exactly the position a skip cascade starts from.

TREAT THIS AS A LEAD, NOT A FINDING. It rests on an absence in an env dump,
and an absence is the weakest evidence there is: a variable can be missing
from a dump for reasons other than its writer failing. Read the HEAD of run
33654488608's log and confirm or refute it before changing a line. If it is
refuted, the refutation is more interesting than the lead and belongs here.

### CONFIRMED 2026-09-02, and not from the log

The raw log could not be read: GitHub redirects the log endpoint to
`productionresultssa1.blob.core.windows.net`, which this container's egress
policy answers with 403, and that host is not to be routed around.

So the lead was checked against a stronger source than the log, the API's own
per-step conclusions, which are a positive record rather than an absence:

    GET /repos/.../actions/runs/33654488608/jobs
      1 success  Set up job
      2 success  Checkout                              (86s)
      3 success  tool PATH bootstrap
      4 success  python3 shim
      5 success  Where the weights live
      6 FAILURE  The commit this run is measuring      (0s)
      7 skipped  imagegen selftest
      8 skipped  Look at this PC
      9 skipped  Generate the batch
     10 skipped  Attribution still holds
     11 success  Commit what arrived, by name
     12 failure  The verdict, named step by step

Step 6 is workflow line 194, the lead's prime suspect, and it is the only
step in the job with a `failure` conclusion before the skip cascade. It ran
for ZERO seconds, so it is a command returning non-zero and not the
1-minute timeout.

WHICH command inside it failed is STILL NOT PROVEN, and the fix is written to
survive that: it is cause-agnostic, and it makes the next run print git's own
stderr instead of dying mute. What IS evidence is a differential over the
whole repo: line 198 was the ONLY place in `.github/workflows` where git ran
in a bash step without `GIT_CONFIG_* safe.directory=*`. Every other git call
on this runner carries it (build-windows 578, probe-unreal 693, setup-msvc
267, vignette-fetch 143, and this file's own commit step at 283), and every
other one has run on this machine. The step was hoisted out of the commit
step, where vignette-fetch computes the same sha on its line 152 under that
env, and the env stayed behind. Second-hand support: probe-unreal line 115
records `git rev-parse --short HEAD` returning nothing ON THIS SAME MACHINE,
and the answer it settled on was GITHUB_SHA.

## The fix

1. The summary distinguishes three states, not two: `success`, `failure`
   (the step ran and returned non-zero, so its named cause is real), and
   `skipped` (the step never ran, so print only that, and name the step that
   stopped the job).
2. Find and print WHICH earlier step failed. The run's own log has it above
   the commit step; the resident did not pin it, and the next session should
   read the head of the log rather than the tail.
3. Consider whether the setup steps should be `continue-on-error` too, so
   one setup fault cannot hide the four findings the work steps would have
   produced. The counter-argument is that generating without a verified
   toolchain is worse than not generating; decide it, do not drift into it.

## Do not

Do not conclude the route is broken. Run 1 proves the workflow dispatches,
checks out, reaches the runner, writes a verdict and refuses to bank
anything false. What it has not proven is that a picture can be generated,
and that is one setup fix away.
