line: infrastructure (the studio split)
spec: production/NOW.md, "JAFAR'S STANDING ORDER, 2026-09-05", item 5
acceptance: one agent definition on the cheapest tier already in use, read-only, proven by one real run over the week's landed items that prints moved=N maintained=M mixed=K of T examined with the path sets it classified by printed beside them, and prints the consecutive-maintenance run-length series rather than a flag; a week with nothing landed prints the words "nothing measured" with T=0 and does NOT report the week as maintenance; an item touching both trees is printed as mixed and never split by guess; and the report names the roadmap rows it read, because a planner that never opened the plan is a reviewer of diffs
max_sessions: 1
status: READY 2026-09-05. After item 4. planner writes the definition; the first run proves it.

## Why the role exists, in the evidence Jafar cites

Practitioners running long autonomous builds report agents that keep working,
get absorbed in small details, and stop improving the project; the fix they
report is a coordinator holding the plan while others do the work. Our resident
does both jobs, and this week's queue is the symptom: on 2 September it held
twenty-two ready items and not one of them was a moat item.

So the only job is the larger plan: read the roadmap, the map view and the
week's landed items, and answer one question. Did the week MOVE THE PROJECT or
MAINTAIN THE STUDIO.

## The classification is a stated rule, not a judgement

An item is classified by the paths its landed commits touch, and the path sets
are printed with every report so a reader can disagree with a rule instead of
arguing with an opinion. Starting sets, to be confirmed in the first run:

    game     ledger/ , content/ , canon.md
    studio   tools/ , production/ , .claude/ , ledger-v2/studio-v2/

An item touching both is MIXED and is printed as mixed. Splitting it by size or
by intent is a guess dressed as a measurement.

## The threshold is not invented here

The order says to flag it when several consecutive items are self-maintenance.
"Several" is a number nobody has measured, so the first run SHIPS THE PRINTER:
the series of consecutive-maintenance run lengths across the landed history.
The bound is set from that series by a director afterwards, in that order, which
is the standing rule about thresholds.

## Cheapest tier, measured rather than assumed

Read across the 14 agent definitions in `.claude/agents/` on 2026-09-05, the
model values are opus on 11, fable on 2 (studio-director and producer) and
sonnet on 1 (dialogue-writer). So the cheapest tier already in use is sonnet,
and the role file states its model and why. The role is READ-ONLY: it produces
a finding, never a fix, and it never addresses Jafar, because the Producer is
the only role permitted to do that.

## Both halves, accepting first

Accepting: one run over this week, with the counts, the path sets and the
series.

Rejecting: run it over a window in which nothing landed and show it printing
`T=0` with the words "nothing measured". A week with no landings is not a week
of maintenance, and a role that cannot tell those apart would report the
studio's worst state as its second best.

## Depends on, and what it blocks

Depends on queue 099 for the map it is meant to read, and reads roadmap-v2
whether or not queue 100 has landed. Blocks nothing. It is a new process item,
so under the standing rule it goes to the queue and waits if item 4 has already
landed when its turn comes.
