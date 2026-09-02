line: infrastructure (governance)
spec: this file
acceptance: a stop condition holding costs at most one wake to establish, not one per hour; the back-off is visible in the repo rather than only in the trigger system; resumption when Jafar posts a number is not slowed
max_sessions: 1
status: READY 2026-09-02. Found by the resident during the stop it describes. Needs a decision on cadence, so a director row before it lands.

THE GOVERNOR SPENDS BUDGET TO SAY THE BUDGET IS UNKNOWN.

Measured, not supposed. On the night of 1 to 2 September the watchdog fired
at 00:21, 01:20, 02:20 and 03:20 UTC. The budget stop condition held at every
one of them, for the same reason each time: Jafar's newest reading was 8
percent, taken before twenty agent spawns, and nothing in the container can
read his usage page.

Each firing wakes a session that reads `production/budget.md`,
`production/NOW.md` and the queue, reasons about the same unchanged facts,
and ends. The first was worth it: it is what produced the stop and the brief.
The three after it produced nothing and were not free. Left alone overnight
this repeats every hour until he answers, which is exactly the hours he is
least likely to be answering.

THIS IS NOT AN ARGUMENT FOR A SLOWER WATCHDOG. The watchdog's value is that
work restarts promptly when the budget clears, and a two-hourly watchdog
halves the cost and doubles the latency on the thing that matters. The
asymmetry is the point: waking to FIND work is worth paying for, waking to
re-confirm a stop is not.

Candidate shapes, none built, none ruled:

1. A stop leaves a dated marker (the shape `production/STOP` already has, but
   written by the session rather than by hand, naming the condition and the
   reading it rests on). A firing that finds a marker whose condition cannot
   have changed ends in one step, without reading the queue or reasoning
   about it. The condition CAN change the moment Jafar posts a number, so the
   marker records what would clear it and the session checks only that.
2. The trigger backs off while a marker is present and returns to hourly when
   it is cleared. Cheaper still and it moves state out of the repo into the
   trigger system, where nothing in the tree can check it, which is the
   property `watchdog-prompt.md` exists to avoid.

Shape 1 looks right from here for that last reason, and the resident should
not choose alone: cadence is a mechanism question and the watchdog is the one
instruction every session obeys.

WHAT MUST NOT HAPPEN: a back-off that outlives the stop. A governor that goes
quiet and stays quiet is worse than one that costs too much, and this project
has already emptied one watchdog file by accident and watched a stale
sentence be read hourly for a day. Whatever lands here ships with the test
that it comes BACK.
