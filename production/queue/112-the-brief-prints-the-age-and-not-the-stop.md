line: infrastructure (the budget instrument)
spec: found 2026-09-06 by the first daily wake; the daily trigger's own instruction says "if a stop condition holds, say so in the brief and do not start work"
acceptance: the brief states the stop condition in words when one holds, naming which, and states plainly that it does not hold when it does not; both outcomes fixtured, accepting case first, with the newest reading's age and the session count since it printed beside the words
max_sessions: 1
status: READY 2026-09-06. instrument-builder, small, and it rides with queue 111 since both are the BUDGET section.

## The gap

`production/budget.md` rules: "A reading describes the moment it was taken.
Substantial work since the newest one still means the day is UNMEASURED, and an
unmeasured day is still a reason to ask rather than to assume."

The daily trigger's own text says: "If a stop condition holds, say so in the
brief and do not start work. An unknown budget is not permission."

`tools/morning-brief.py` prints `budgetAgeDays=1` on its done line and the
words "taken yesterday" in the message. IT NEVER SAYS THE DAY IS UNMEASURED,
because it does not compute the condition at all: it reports the age of the
reading and leaves the reader to do the arithmetic and remember the rule.

## Measured, on the morning it was found

Newest reading 2026-09-05 08:30Z, 7 total and 8 Fable. Sessions since, counted
from `.claude/agent-log.tsv`: 27. So the day was UNMEASURED by the file's own
rule and the brief said only "taken yesterday", which reads as reassurance.

## What it must print

Both halves in words, not just a number: how old the newest reading is AND how
many sessions have run since it, then the conclusion. "Unmeasured, and an
unmeasured day is not permission" when it holds; and when it does not hold,
say that too, because a section that is silent when things are fine and silent
when they are not has told the reader nothing either way.

## Both halves

Accepting: a fresh reading with no work since prints that the condition does
NOT hold, and names both numbers.
Rejecting: a stale reading, or a fresh one with substantial work after it,
prints the stop in words. A brief that omits the sentence in either case fails
the fixture.
