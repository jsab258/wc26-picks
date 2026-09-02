# Budget (the constraint that outranks the work)

STATUS: LIVE. Verified 2026-09-01.

## The rule

LEDGER stops when the week's LEDGER share is spent. Not slows down: stops.
Jafar uses the same account for work and private things, so overspending here
takes away something he needs elsewhere, and no roadmap item is worth that.

## The numbers, as reported by Jafar

A reading is only worth what its source is worth. These come from him reading
his own usage page; nothing here measures itself, and the series matters more
than any single row.

| when | hours into week | total used | fable used | note |
|---|---|---|---|---|
| 2026-09-01 | 28 of 168 | 34% | 41% | 2.5x over pace. The day the studio split was not used. |
| 2026-09-01 | ~31 of 168 | 38% | not read | Reported by Jafar. 42 points left for 5 and a bit days. |
| 2026-09-01 | new week, hours in | 8% | not read | THE WEEKLY LIMIT RESET. Reported by Jafar. This is a different week from the two rows above, and the delta between this row and the one before it is meaningless. |
| 2026-09-02 | 41 of 168 | 17% | not read | Reported by Jafar at 04:40Z, AFTER the heavy night. The 8 percent row plus that night cost 9 points. This row is what makes the night measured rather than unknown. |

Ceiling for LEDGER: 80% of the weekly limit. The other 20% is his.

Told by Jafar 2026-09-02, retiring the D1 deadline: "we are limited by 5h
and weekly usage limits in claude". Dates are not a planning unit here. Any
bound on a piece of work is written in dispatches, sessions or points of
this ceiling, never as a calendar date. Ruling:
game-design/decision-2026-09-02-d1-timebox-retired.md.

## THE MID-WEEK RESET WAS AN ANOMALY, told by Jafar 2026-09-02

Do not build any expectation on it. His words: the limit reset on the Tuesday
evening after reaching almost 40 percent, possibly because a model was
released that day, and it should NOT be expected to happen again.

That matters because a session reading the rows below could otherwise infer a
pattern from one event: "the week resets when it gets tight" is exactly the
shape of a rule invented from a single reading. There is one rule and it is
the next section: Monday 14:00 CEST, ceiling 80 percent, and nothing else.

The 34 and 38 percent rows therefore describe a week that ended EARLY by
accident, not a week that ran its course. They are kept because deleting a
regime change is worse than recording one, and they are useless for pace.

## WHEN THE WEEK STARTS, told by Jafar 2026-09-02 and not known before

MONDAY 14:00 CEST, which is 12:00 UTC. Every "hours into week" figure in the
rows above before this line was the resident GUESSING from a reset it had
seen reported, and the 2 September row first said "~36 of 168" for no reason
better than that. Jafar corrected it. 41 is the measured figure from the real
anchor.

It matters beyond tidiness: the pace test divides spend by elapsed week, so a
wrong anchor moves the only number that says whether a day is heavy. This is
the same fault the reset section below records, made smaller and quieter: a
quantity carried as if measured when nobody had measured it.


## WHAT HAS HAPPENED SINCE THE NEWEST READING, 2026-09-02 00:25Z

The 8 percent row was reported by Jafar during the evening of 1 September.
Counted from `.claude/agent-log.tsv`, not estimated: **20 agent spawns landed
after 20:00Z on 1 September**, of which **3 are `studio-director`**, which
carries its own weekly limit and counts double against the full one. Five of
those agents reported subagent totals in the region of 150,000 to 200,000
tokens each.

So the 8 percent describes a moment that is now well behind a heavy night,
and nothing in this container can read the real number. By condition 4's own
words this makes the day UNMEASURED rather than young, and the standing
instruction for an unmeasured day is to prefer stopping.

THE UTC DAY ROLLED OVER AT 00:00Z AND THAT RESTORES NOTHING. The daily
allocation is a discipline device laid over a WEEKLY limit; midnight does not
hand any capacity back. Reading the rollover as a fresh day would be a delta
computed across a boundary, which is the exact fault the reset section above
records. The day that matters here is the working night, and it has been a
long one.

MEASURED SINCE: the watchdog fired at 00:21, 01:20, 02:20 and 03:20 and the
stop held at every one, on facts that had not changed. The first firing
earned its cost by producing the stop and the brief; the rest re-established
a known answer. A governor that spends budget to report that the budget is
unknown is queue item 026.

CLEARED 2026-09-02 04:40Z. Jafar reported 17 percent. The night is now
MEASURED rather than unknown: 8 to 17 is 9 points, and at roughly 36 hours
into 168 the week is 21 percent elapsed against 17 percent spent, so the
pace is slightly UNDER rather than over. The stop that ran from 00:25 to
04:40 was correct on the evidence available at the time and is not
retroactively wrong for having been cautious; what it lacked was a number,
which is the one thing this container can never produce for itself.

ACTION TAKEN AT THE TIME: the director spawned at 00:02:48Z was in flight and its cost is
already committed, so it finishes. When it rules, the resident applies the
ruling, lands the three-builder batch in one commit, pushes, updates NOW.md,
and STOPS. No further spawns of any tier until Jafar reports a number.


## THE WEEK RESET ON 2026-09-01 AND THAT VOIDS THE ARITHMETIC BELOW

The reset is recorded rather than the old rows deleted, because the series is
worth more than any row in it and a table that quietly drops its history
cannot show a regime change. What it does mean: the 34, 38 sequence and every
number derived from it describe a week that has ENDED. Do not compute a delta
across the boundary; two readings either side of a reset are two different
quantities with one name, which is the fault this project has a rule about.

The daily condition still applies within the new week. The ceiling still
applies. What has gone is the specific pressure: 8 percent used means the
quarter-rate discipline set on 1 September was for the old week and should be
re-derived, not carried over out of habit.

## The arithmetic, so nobody has to redo it (FOR THE WEEK THAT ENDED)

At 28 hours the week was 17 percent gone and 34 percent of budget was spent.
On-pace would have been about 13 percent. Remaining for LEDGER: 46 points
over 140 hours, which is roughly a third of a point per hour against the
1.2 points per hour burned so far. THE REST OF THE WEEK RUNS AT A QUARTER OF
MONDAY'S RATE.

## What that buys, per day, for the rest of this week

THE ARITHMETIC GIVES 7.9, THE WORKING FIGURE IS 6, AND THE GAP IS DELIBERATE.
46 points over the 5.8 days remaining is 7.9 points a day. Six is that with
roughly a quarter held back, because every estimate this project has made
about its own consumption has been low, and because a reserve that is spent
is a reserve that was never needed. Six is a CHOICE with a named reason, not
a derivation, and it is written that way so the next reader does not treat it
as measured.

That buys roughly two short working sessions, not one long one, and no more
than three dispatched builds.

## Stop conditions, mechanical

1. Total reported use at or above 80 percent: STOP. Write the brief, push,
   and do nothing further until Jafar gives a new number.
2. No reading newer than 48 hours: treat the budget as UNKNOWN and work only
   on items that cost no model time (reading landed results, committing
   finished work). An unknown budget is not permission.
3. `production/STOP` exists: stop, same as the night runner.
4. THE DAY'S ALLOCATION IS SPENT: stop for the day even though the week is
   fine. Added 2026-09-01 17:20Z by a watchdog firing that found no stop
   condition holding and correctly concluded it should work, on a day whose
   readings had gone 34 to 38 percent in about three hours against a six
   point daily target. Every condition above is WEEKLY, so all three passed
   and the governor said go on a day that was already over.

   The test, and it is deliberately rough because nothing here can measure
   its own spend: if the newest reading minus the oldest reading FROM THE
   SAME DAY is at or above 6, the day is done. Land what is finished, update
   NOW.md, and end. With only one reading for the day, use judgement and
   prefer stopping; a day that started heavy is exactly the day this
   condition exists for.

   IT IS BLIND TO SPEND AFTER THE LAST READING, and that hole was found the
   same evening it was written. The test compares two READINGS, so a day with
   one reading at noon and six hours of agent work after it computes a delta
   of zero and reports the day as young. On 1 September the 38 percent
   reading was taken before roughly five agent spawns; the real number was
   never known and the condition said carry on. When substantial work has
   happened since the newest reading, treat the day as UNMEASURED and prefer
   stopping, exactly as with a stale one. A reading describes the moment it
   was taken and nothing after it.

   THIS CANNOT BE ENFORCED MECHANICALLY and saying so is the point. Nothing
   in the container can read Jafar's usage page. It works only if readings
   keep arriving, which is why the ask is one number per session and not a
   promise to be careful.

## Why a file rather than a rule in somebody's head

Because a session that resets cannot remember a number Jafar said on Monday.
This file is the only thing that survives.

The watchdog is told to read this file first, and THAT CLAIM NEEDS AN
ARTIFACT LIKE ANY OTHER. The prompt lives in the trigger system rather than
in the tree, so nothing here could be checked against it and a director
review could not verify it. The text is now kept at
`production/watchdog-prompt.md` with its enabled state and the date it was
set. When the prompt changes, that file changes in the same commit, or the
claim goes back to being unverifiable.
