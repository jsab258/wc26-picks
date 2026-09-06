line: production (the assembly line)
spec: external audit 2026-09-06, P2
acceptance: the count of verified pieces equals the count that PASSED VERIFY, proven by a check that refuses a piece whose gate is pending; and the dialogue bank in question is either passed through its tone gate or removed from the count
max_sessions: 1
status: P2, ready 2026-09-06. Small, and it decides what a number in the phase gate means.

## The fault

One dialogue bank is counted as a verified piece WHILE ITS TONE GATE IS
PENDING. Either it passed VERIFY or it is not counted. There is no third state
in which it counts.

## Why it is not a rounding matter

Phase 0's exit gate says the pilot line YIELDS A VERIFIED PIECE. That is one of
the conditions on leaving the phase this project is currently in. If the count
includes a piece whose gate has not run, then the gate is satisfied by a piece
that was not verified, and the phase exits on a number that means something
softer than it says.

It is also the same shape as queue 117's group: a count that can only move one
way, because a pending gate is being read as a pass rather than as a pending
gate.

## Both halves

Accepting: a piece that passed its tone gate counts, and the count matches.
Rejecting: a piece with a pending gate is REFUSED by the counter and named,
and the refusal says which gate is pending. A counter that quietly excludes it
without saying so has replaced an overcount with a silence.
