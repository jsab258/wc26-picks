line: studio (the dispatch ceiling, and how close it is)
spec: measured by the engine-specialist applying amendment A3, while checking
  that its own two added lines had not moved the largest step.
acceptance: headroom on the largest workflow step stated as a SERIES over
  recent commits rather than a single reading, and a bound set from it; or the
  build step split so no single step is within a comment line of the ceiling
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-06. NOT this weekend. Filed because the number is
  frightening and nobody had printed it.

## The reading

`tools/workflow-size.py`: 13 workflows, largest step 23,167 characters,
SEVENTEEN characters under the largest that has ever been accepted. It is the
build step of `ledger-probe-unreal.yml` at line 203.

Seventeen characters is one short comment line. The next person to explain
something inside that step breaks the dispatch, and what breaks is the only
channel out of CI: a 422 that kills the run before it can say why.

## Why it was found rather than hit

The builder applying A3 added two lines to that workflow and then measured the
largest step with its own change reverse-applied, to be sure it had not moved
the number. It had not, because A3's lines went into a different block. That
check is the reason this is a queue item and not an incident.

## What this item must NOT do

Do not simply move the ceiling. The ceiling is GitHub's, not ours. The two
honest moves are to print the series and set a bound off it, per rule 2, or to
split the step so nothing sits that close.

## The denominator that is missing

One reading is not a series. 23,167 today says nothing about whether the step
has been growing steadily or sat still for a month, and the answer changes
which fix is right. Print `--size-series` before choosing.
