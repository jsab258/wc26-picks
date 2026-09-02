line: infrastructure (instruments)
spec: this file, from imagegen run 1
acceptance: the summary step distinguishes skipped from failed and from success, and says WHICH step stopped the run; a skipped step never produces a sentence naming a cause that was never observed; both outcomes fixtured
max_sessions: 1
status: READY 2026-09-02. engine-specialist, small, rides the next imagegen touch.

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
