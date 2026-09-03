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
| 2026-09-02 | ~18 into a 136h period | 32% | not read | Reported at 14:40Z. 4x over pace against the 80% ceiling. Set the pace rule below. |
| 2026-09-02 | ~21 into a 136h period | 38% | not read | Reported at ~17:00Z. Jafar notes he also did OTHER work in the same window, so this delta is NOT all LEDGER and must not be read as a LEDGER burn rate. 42 points to the ceiling. |
| 2026-09-03 | ~33 into a 136h period | 52% | not read | Reported at 04:50Z, after the overnight run. THE FIRST CLEAN LEDGER BURN RATE: Jafar was asleep for the whole window, so all 14 points are ours. 28 points to the ceiling, 103.5 hours to the Monday reset. |
| 2026-09-03 | ~39 into a 136h period | 60% | not read | Reported at 10:25Z. NOT A CLEAN RATE: Jafar says he also did other work on Claude in this window, so the 8-point delta is NOT all LEDGER and must not be divided by hours. 20 points to the ceiling, 97.6 hours to the Monday reset. He said WAIT. |
| 2026-09-03 | ~49 into a 136h period | LIMIT HIT, no percentage | not read | Reported by Jafar at about 20:20Z: "I hit my usage limit while you were working, but it has reset now." THIS IS NOT A READING and must never be counted as one: it carries no percentage on either meter. WHICH limit is unresolved and the answer changes everything. The 5-hour session limit resets many times a week and says nothing about the weekly meter; the WEEKLY limit resets Monday 14:00 CEST, which is four days away, so a weekly reset today would be a regime change and the arithmetic below would be void. Asked, not assumed. What the row DOES establish, whichever it was: the account hit a wall today, which is evidence in the direction of MORE spent, never less. |

Ceiling for LEDGER: 80% of the weekly limit. The other 20% is his.

## TWO METERS, RULED 2026-09-03, AND THE HIGHER ONE GOVERNS

Every reading from Jafar records BOTH: the total meter and the Fable meter,
each against its own 80 percent ceiling. Whichever is higher decides. A studio
comfortable on the total and at 79 percent on Fable is not comfortable; it is
one director spawn from a stop, and until today this file could not have said
so because it recorded one number.

BACKFILL RULE, and it is the point of the rule: a row where Fable was NOT READ
says `not read`. It never says `equal to the total`, never carries the total's
figure across, and never reads as zero. Every row above this line except the
first says `not read` in the Fable column, and that is a true statement about
what was measured rather than a gap to be tidied. The 2026-09-01 row is the
only one carrying a real Fable figure: 41 percent against a total of 34, which
is the whole argument for this rule. The higher meter was the Fable one, by
seven points, on the only day both were read.

Directors run on Fable. Builders and the resident do not. So the Fable meter
moves on reviews and rulings, which are exactly the things this studio was
told to do more of, and the total meter hides that.

## ESTIMATES CARRY THEIR CALIBRATION AND ITS DATE, ruled 2026-09-03

No estimate is printed bare. Every one names the measurement it rests on and
when that measurement was taken, so a reader can see when it went stale.

The live calibration, and it is weak in three named ways: a spawn costs
roughly 1.5 to 2 points, derived 2026-09-02 from spawn counts in
`.claude/agent-log.tsv` against Jafar's readings.

(1) It is a flat average over two populations whose turn counts differ by
3.75x. On 2026-09-03 the transcripts on the build machine read a fable median
of 12 turns and an opus median of 45, peak 138. Series committed at
`production/spawn-cost-series-2026-09-03.txt`, and that file, not this
paragraph, is the source: `fable spawns=160 turnsMedian=12`,
`opus spawns=144 turnsMedian=45 turnsPeak=138`.

(2) Its denominator counted spawns that never produced a turn. Of 454
transcripts, 170 carry a session-limit notice and 148 of those 170 produced NO
turn at all; 149 transcripts in total hold no turn. So per LIVE spawn the
figure is HIGHER than 1.5 to 2 points, not lower. The 148 and the 149 are two
different facts and neither is a typo for the other: 148 is dead-and-noticed,
149 is dead in total.

(3) Its denominator is 240 logged rows against 454 transcripts on the machine,
a gap of 214 that nobody has explained.

Turns are not points. The conversion is UNMEASURED, and no per-tier points
figure is written into this file until two paired readings exist: both meters
from Jafar, with the turns log between them. Ruled 2026-09-03,
game-design/decision-2026-09-03-batch-review-register-banner-spawnlog-uvsweep.md;
queue 024 carries the measurement and queue 076 carries the tokens-per-point
rate that would replace the whole guess.

Readings govern, estimates forecast, an unmeasured day stops. Unchanged.

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

## THE DAILY ALLOWANCE IS RETIRED, ruled by Jafar 2026-09-02

His words: "let's start now. I don't care if we get to 80% before monday, we
just stop when our budget is used up".

SO THERE IS NO DAILY RATION. Run until the ceiling, then stop. The pace
arithmetic below is kept because it is the measurement that produced the
question, and because the burn rate is still the thing to report, but the
10-points-a-day allowance it derived is NO LONGER A CONSTRAINT and must not
be re-imposed by a session that reads the arithmetic without this heading.

WHAT STILL BINDS, and it is not weakened by this:

- The 80 percent ceiling. The other 20 percent is his and is not ours to
  spend. Reaching it means STOP, whatever day it is.
- A reading describes the moment it was taken. Substantial work since the
  newest one still means the day is UNMEASURED, and an unmeasured day is
  still a reason to ask rather than to assume.
- The efficiency rules keep their whole value and gain some: facts inline
  rather than reading lists, related work batched into one spawn. Those were
  never rationing, they were waste reduction, and waste is worth the same
  whether or not there is a daily cap.

WHAT CHANGES IN PRACTICE: work does not stop at an arbitrary hour, and the
free lane (local generation on his PC, which costs NOTHING against this
ceiling) is scheduled ahead of Claude-priced work wherever it can be, per
queue 039.

## THE PACE RULE, set 2026-09-02 from a measured burn rate

Reading: 32 percent, reported by Jafar at about 14:40Z on 2 September.

THE ARITHMETIC, and the period is NOT a calendar week. The one-time reset on
the Tuesday evening restarted the counter; the next reset is the normal one,
Monday 14:00 CEST. So the period runs from that evening to Monday, about 136
hours, not 168. The exact reset moment is unknown (Jafar reported 8 percent
at 21:20Z saying it had reset "earlier"), so this is bracketed rather than
given false precision:

    reset 18:00Z  period 138h  elapsed 20.7h (15.0%)  burn 1.55 pts/h
    reset 21:00Z  period 135h  elapsed 17.7h (13.1%)  burn 1.81 pts/h

Against the 80 percent ceiling, sustainable is 0.41 points per hour, so the
run rate is 3.8x to 4.4x over. At that rate the ceiling arrives in about 29
hours with 117 hours of period left.

**THE ALLOWANCE FROM HERE IS ABOUT 10 POINTS A DAY.** 48 points remaining
over 4.9 days. Today ran at roughly 40.

## What 10 points a day actually buys, and how to spend it

Measured from today: a builder or director spawn costs roughly 1.5 to 2
points. So the allowance is about five spawns a day INCLUDING the resident's
own turns, which are not free and were heavy today.

The working rule, three parts:

1. **Two or three builder spawns a day, plus a director ONLY when a
   mandatory trigger fires.** Not four small ones.
2. **Brief with the facts inline, not with a reading list.** Five builders in
   a row spent their whole step budget reading before writing a line and
   each needed a hand restart. That is a briefing fault worth about a third
   of every builder's cost (queue 031).
3. **Batch related work into one spawn.** Every agent re-reads context from
   scratch, so eight spawns doing one thing each cost far more than three
   doing three things each.

## WHY TODAY IS NOT THE STEADY RATE, said so nobody plans on either number

Today was front-loaded with one-offs: the CLAUDE.md cut, the licence sweep,
the decision-register reconciliation, and four separate review cycles. That
is governance debt being paid down, not the running cost of building a game,
and it should not recur. Equally, "it was one-offs" is the comfortable
reading and it has been wrong before, so the test is the next reading rather
than this paragraph.

Spending down and pausing until Monday is a LEGITIMATE CHOICE rather than a
failure, and it is Jafar's to make. What is not legitimate is drifting into
the ceiling without either of us noticing.

## THE NIGHT OF 2 SEPTEMBER, and how the ceiling and the instruction reconcile

Jafar, at about 21:00Z, AFTER the 38 percent reading and knowing the ceiling:
"just keep working through the night and show me what you got by 7 am cest".
That is authority to work, given by the person whose budget it is, and it is
not overridden by a governor that says prefer stopping. It also does not
repeal the 80 percent ceiling, which he set in the same breath as "we just
stop when our budget is used up".

WHAT HAS BEEN SPENT SINCE THE 38 PERCENT READING, counted rather than felt:
one director spawn, five tier-2 and tier-3 spawns, three of them resumed
after hitting a turn limit, with reported subagent totals of roughly 138k,
145k, 155k, 160k, 285k, 328k and 353k tokens. At the measured 1.5 to 2 points
a spawn that is somewhere near 10 to 15 points, so the true figure is
plausibly around 50 percent and NOBODY IN THIS CONTAINER CAN KNOW. The day is
UNMEASURED in exactly the sense condition 4 means.

THE RECONCILIATION, and it is the free lane that makes it possible. From here
the night runs on work that costs NOTHING against this ceiling:

1. The two builders in flight finish. Their cost is already committed.
2. ONE director spawn, because batch review before commit is a mandatory
   trigger and skipping it is not a saving.
3. Then commit, push, and let the FREE LANE carry the night: the Unreal
   probe, the Unity build and the image regeneration all run on Jafar's own
   machine and cost zero points. That is queue 039's rule doing exactly the
   job it was written for, on the night it matters most.
4. NO FURTHER CLAUDE-PRICED SPAWNS unless something breaks in a way that
   blocks the 07:00 deliverable. Watching a free run land is not a spawn.

AND THE BURN GOES IN THE MORNING REPORT, first item, not buried. The one
thing that would be a real failure here is drifting into his 20 percent
overnight while he is asleep and cannot see it happening. He asked for a
night of work; he did not ask to wake up over the ceiling.

## A SESSION LIMIT WAS HIT AT 21:47Z ON 2 SEPTEMBER, and it is the first hard consumption signal this project has ever had

Not a reading from Jafar and not an estimate: a 429 from the API, quoted as
received, "You've hit your session limit, resets 12:20am (UTC)", on the model
the studio-director agent runs. It killed a director mid-review. The limit
reset at 00:20Z and the session lost 2 hours 33 minutes, during which the
watchdog fired three times into a session that could not act on anything.

WHY THIS IS WORTH A SECTION. Every number in this file so far comes from
Jafar reading his own usage page, which means the container has never been
able to observe its own consumption at all. This is the exception: a limit
that binds is a fact the container CAN see, arriving as an error rather than
as a report. It is not the weekly percentage and must never be written into
the table above as if it were. It is the 5-hour session window, a different
quantity with a different reset, and conflating the two would be exactly the
fault the reset section of this file already records.

WHAT IT COST, stated because "we lost time" is not a measurement. Two
directors died on one review: the first to a container restart at about
21:40Z, the second to this limit at 21:47Z. Neither wrote a ruling. The batch
they were reviewing has been uncommitted and unpushed since roughly 21:30Z,
which means 5294 lines of builder work spent the whole outage one container
restart away from being lost, because `director_cadence` correctly refuses to
let it commit unreviewed and there is no legitimate way around that.

WHAT IT CHANGES, and it is a rule rather than an observation:

- A LONG UNCOMMITTED BATCH IS A LIABILITY, and the size of the batch is the
  size of the exposure. Four builders were run before any of their work
  landed. Landing each builder's work under its own smaller review would have
  put most of it beyond reach of both failures. That is a real argument
  against batching reviews, and it sits against the equally real argument for
  batching them, which is that a director spawn is expensive. The trade is
  named here rather than resolved.
- THE SESSION WINDOW IS A SECOND CEILING and nothing in this file knew about
  it. It binds in hours, not points, it resets on its own clock, and it can
  stop the studio dead in the middle of the one step every other step waits
  on. Work that must complete by a wall-clock time should not be planned as
  if only the weekly limit exists.
- A THIRD DIRECTOR WAS SPAWNED ON A DIFFERENT MODEL after the reset, because
  the limit was reported against the one the agent had been using. That is a
  workaround with a named reason, not a preference.

## THE FIRST CLEAN BURN RATE, 2026-09-03 04:50Z

Every reading before this one was contaminated. Jafar uses the same account
for work and for LEDGER, so 34, 38 and 32 all mixed the two and the file says
so beside each row. THIS ONE DOES NOT: he reported 38 percent at 17:00Z, went
to bed, and reported 52 percent on waking. He was asleep for the window. The
14 points are the studio's, and this is the only row in the table that can
honestly be divided by hours.

    38 to 52          14 points over 11.5 hours       1.21 points/hour
    28 left to 80     103.5 hours to Monday 12:00Z    0.27 points/hour sustainable
    the night ran at 4.5x sustainable
    AT THE NIGHT RATE THE CEILING ARRIVES IN 23 HOURS, which is tonight.

WHAT 14 POINTS BOUGHT, so the rate has something to be judged against: four
builder sessions (props and decals into the frame, the dashboard's own
staleness, the framing fix, the Unreal emitter through Phase B), one verifier
opening 45 images, three director attempts of which ONE produced a ruling, and
the resident's own turns across roughly eleven hours.

THE WASTE IS NAMED RATHER THAN AVERAGED IN. Two of the three directors died
before writing anything: one to a container restart at about 21:40Z, one to
the session rate limit at 21:47Z. Their cost was paid and nothing came back.
On the measured 1.5 to 2 points a spawn that is roughly 3 to 4 points of the
14, so about a quarter of the night went on reviews that never happened. That
is not a reason to skip the review; it is a reason to land smaller batches so
a dead review costs less.

WHAT THE FREE LANE PROVED, and it is the whole lever. The night's two most
visible outputs, the Unreal street and 41 regenerated plates, cost ZERO points
because they ran on Jafar's GPU. The 14 points went on Claude-side work:
writing the code, reviewing it, and coordinating. So the ratio to improve is
not "work less" but "spend fewer Claude points per unit of GPU work
dispatched", which is queue 039's rule with a number behind it at last.

THE ARITHMETIC IS NOT AN INSTRUCTION. 28 points buys roughly two more nights
like the last one, and there are four days to Monday. Two nights and a stop
is a legitimate choice; so is a quarter-rate week. It is Jafar's call and the
numbers above are what he needs to make it, not an argument for either.

## 60 PERCENT AT 10:25Z, AND JAFAR SAID WAIT

20 points left to the ceiling and 97.6 hours to the Monday reset, which is
0.20 points an hour sustainable. THE 8-POINT DELTA FROM 52 IS NOT A LEDGER
BURN RATE and the row says so: he did other work on Claude in the same window,
exactly as with the 32-to-38 row on 2 September. Dividing it by 5.6 hours
gives 1.43, and that number is meaningless because its numerator is two
different things added together. The only clean rate this project has ever had
is the overnight one, 1.21 points an hour, because he was asleep for it.

WHAT THE MORNING BOUGHT, for the record, since some of those 8 points are ours:
Phase C reduced to one unconnected pin with every other number in the chain
proven, the D1 agent-loop measurement passing (an agent generated the Unreal
material head-less, no editor opened), a gate that could not fail found and
fixed, and the discovery that the obvious tool for sweeping that fault is
structurally blind to it.

HIS INSTRUCTION IS "wait for now". Nothing is dispatched, nothing is spawned,
and the Unreal stop rule from the 3 September ruling is independently in force
because materialConnections held at 12/14 across two runs. Two reasons to hold,
either of which would be enough.
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
