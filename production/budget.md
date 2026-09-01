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

Ceiling for LEDGER: 80% of the weekly limit. The other 20% is his.

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
