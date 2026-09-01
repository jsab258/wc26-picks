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

Ceiling for LEDGER: 80% of the weekly limit. The other 20% is his.

## The arithmetic, so nobody has to redo it

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
