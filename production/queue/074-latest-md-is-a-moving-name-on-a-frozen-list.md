line: production (the channel)
spec: game-design/decision-2026-09-03-batch-review-register-banner-spawnlog-uvsweep.md, ruling 1(b)
acceptance: no path on the frozen PRE_REGISTER list can change content without the gate noticing; the night runner's brief either passes the register for its kind or lands outside the gated trees; both cases shipped as gate fixtures, accepting first
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
