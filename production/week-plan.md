# Operating plan, week of 2026-08-31 (W36)

STATUS: LIVE. Verified 2026-09-01.

Written because the week is 2.5x over budget 28 hours in. The plan is not a
wish list; it is what fits in 46 points of weekly budget over 140 hours.

## The one structural idea

SPEND CLAUDE ON DECIDING, SPEND THE PC ON PRODUCING.

Jafar's machine can run around the clock. That saves nothing by itself, and
the distinction is worth being exact about because it was nearly got wrong:
the overnight runner works by calling Claude locally, so it spends the same
budget, just later. What actually costs zero is compute that is not Claude:
image generation, image to 3D, Blender cleanup, engine builds and cooks, the
simulation, voice and music generation.

So the week's shape is: a small amount of Claude time to define a batch, then
hours of free local grinding. Anything that inverts that ratio is the wrong
plan.

## Rates, from production/budget.md

About 6 points of weekly budget per day. Two short sessions rather than one
long one, because a long session re-reads its whole history on every turn and
Monday was one very long session. No more than three dispatched builds a day,
each carrying several changes; a round trip costs the same whether it carries
one change or six.

Fable only at the mandatory decision points, folded into a single spawn.
Monday used one director spawn, which is the right rate.

## The order, and why it is this order

1. WIDEN THE GOVERNANCE GATE (task 010). First because it is what makes
   everything after it hold without Jafar watching. Cheap.
2. STAND UP LOCAL ASSET GENERATION. Highest leverage left: it converts the
   most expensive class of work into the cheapest, permanently. The image
   half already works; the 3D half has never run.
3. THE RE-SCOPED ENGINE COMPARISON. Mostly unattended CI, so cheap in Claude
   terms. One shared scene, two emitters, paired stills.
4. JAFAR LOOKS AT FOUR PAIRS, BLIND. Minutes of his time.
5. D1 GETS DECIDED and recorded with its numbers.
6. BUFFER, with the PC producing assets in the background.

Items 3 to 5 were the timebox ending 2026-09-14; Jafar RETIRED it on 2026-09-02 (game-design/decision-2026-09-02-d1-timebox-retired.md). They are bounded by the rates above and production/budget.md, not by a date.

## What is deliberately not in this week

Anything visual beyond the comparison scene. The engine is undecided, so a
rung built now might be built against a renderer that does not ship. Waiting
is the decision, recorded so it is not mistaken for drift.

## How this is kept honest

Jafar reads his usage percentage at the start of a session and it goes into
production/budget.md as a dated row. One number per session turns the budget
from a guess into a series, which is the same rule this project applies to
every other number: no bound without a printed series behind it.
