line: infrastructure (the budget instrument)
spec: found 2026-09-06 by the first daily wake, reading its own generated brief
acceptance: the studio-versus-game split is computed from WHAT a pass changed, not from which agent type ran it, and a day whose engine-specialists built console plumbing reports as studio; proven by recomputing 2026-09-05 and getting a game figure near one rather than twelve, with the classification rule printed and both outcomes fixtured
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-06. THIS BLOCKS THE BRIEF'S BUDGET SECTION BEING TRUSTED. instrument-builder.

## The fault

`ledger/verify.py` line 2757: `GAME_AGENTS = frozenset(("systems-builder",
"content-wrangler", "engine-specialist"))`. `tools/morning-brief.py` line 253
reads that set and counts a spawn as GAME when its AGENT TYPE is in it.

So the split measures WHO RAN, not WHAT THEY BUILT.

## Measured, on the day the fault was found

2026-09-05 ran 27 spawns: 10 engine-specialist, 5 studio-director, 4 producer,
4 instrument-builder, 2 systems-builder, 2 planner. The brief therefore printed
`splitStudio=15/27 splitGame=12/27` and said in words "fifteen sessions went to
the studio and twelve to the game".

WHAT THOSE TWELVE ACTUALLY BUILT: the inbound transport, the outbound sender,
images, ruling cards, typed meter readings, the Pages publisher, the glance
link, the systems inventory. ONE of them, queue 062 step 2, touched the game.

So the most studio-heavy day this project has had reported as forty-four
percent game. The number is not merely imprecise, IT POINTS THE WRONG WAY.

## Why this one matters more than its size

Jafar's item 5 exists to catch a studio that maintains itself instead of
improving the project, and cites practitioners reporting agents that keep
working, get absorbed in detail and stop moving the thing. THIS IS THE NUMBER
THAT WOULD CATCH IT. A metric that reads a console-building day as game work
cannot ever fire, which makes it worse than absent: absent is honest.

## The trap in fixing it

Agent type is attractive because it is one field already in the log. What a
pass CHANGED is not in the log at all. The honest routes:
- Classify by the PATHS a pass touched, which needs the pass to record them.
- Classify by the QUEUE ITEM a pass was briefed on, which needs the brief to
  carry the number and the log to record it.
Both mean the log grows a field. Do not fake it by keyword-matching agent
names against task titles; that is the same guess with more steps.

Until it lands, the brief must NOT print a game figure it cannot support. A
line reading "the split cannot be computed from the log as it stands" is true;
"twelve to the game" is not.

## Both halves

Accepting: 2026-09-05 recomputed reports a game figure near one, and a day
that genuinely built the game reports as game.
Rejecting: a day of pure console work reporting any game sessions at all fails
the fixture. A fix that simply moves engine-specialist out of the set has
recreated the fault mirrored, since that agent DID build the game on 062.
