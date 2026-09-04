line: production (the channel)
spec: game-design/decision-2026-09-03-batch-review-register-banner-spawnlog-uvsweep.md, ruling 1(b)
acceptance: no path on the frozen PRE_REGISTER list can change content without the gate noticing; the night runner's brief either passes the register for its kind or lands outside the gated trees; both cases shipped as gate fixtures, accepting first; and if option A is taken, the gate INHERITS THE CLOCK from the matched dated brief as well as the verdict, or a faithful copy comes out UNPINNED and red
max_sessions: 1
status: READY 2026-09-03. instrument-builder, small. Predictable red on the first night run after 3 September; the night runner has never yet written a log in this tree, so it has not bitten.

## The hole

`production/briefs/latest.md` is on the frozen `PRE_REGISTER` list in
`tools/producer-check.py`, exempt because it carries the
`PRODUCER-REGISTER-EXEMPT` marker and the list names it. It is also a MOVING
NAME: `tools/runner/run-night.ps1` line 84 copies the night brief onto it,
and `.claude/hooks/session-start.sh` reads its head every session.

Two outcomes on the first night run, and both are wrong. The copy carries no
marker: the gate goes red on a machine-written file, "listed without a
marker". Or a later writer copies the old head across: a file dated after the
register is exempt under a marker that says it predates the register, and
nothing can see it.

## The fix, as options for the builder to measure rather than choose blind

A. Take `latest.md` off the frozen list and make the gate treat it as the
   verdict of whichever dated brief it is byte-identical to; a `latest.md`
   identical to nothing is a failure naming both facts.
B. The night runner writes its brief somewhere the gate does not walk, and
   the Producer writes the 150-word brief that goes to Jafar; `latest.md`
   becomes the Producer's file and passes as a brief.
C. Both.

The ruling leans to B, because Jafar ruled that everything under
`production/briefs/` passes the check for its kind, and a 600-word script
output is not a Producer brief under any reading of that. The builder prints
what the night runner actually writes before choosing.

## AMENDED 2026-09-04 BY THE DEADLINE-PIN RULING

`game-design/decision-2026-09-04-ruling-077-deadline-clock-pin.md` section 3.
The gate now measures every deadline from midnight of the ISO date in the
file's own name, and a file whose name carries no date is UNPINNED, which is a
FINDING rather than a pass. `latest.md` carries no date. That does not change
this item's direction and the lean to option B stands; it adds one clause to
the acceptance above, because under option A a copy that inherits the verdict
but not the clock lands red for a second, unrelated reason.

Nothing rides on it yet: `latest.md` is register-exempt today, and the live
reading `filesDatePinned=1/1` is over the one file actually checked.
