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
