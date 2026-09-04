line: infrastructure (the Producer register)
spec: game-design/decision-2026-09-04-ruling-077-deadline-clock-pin.md, section 5 a and b
acceptance: all seven rejecting gate fixtures assert the RULE TEXT that refused them, not merely that something was refused; and check() derives linked_sections once
max_sessions: 1
status: READY 2026-09-04. instrument-builder, small. Two small items deliberately folded into one task so they cost one round trip.

## (a) Five fixtures assert only that something was refused

Queue 077 added two rejecting gate fixtures that assert the refusing rule text
(`deadline: item 1 gives 9.0 hour(s)` and `carries no date to measure it
from`). The five that predate it assert only that a refusal happened. A
fixture that cannot say WHY it was refused passes when the right file is
refused for the wrong reason, which is a guard that cannot tell a regression
from an improvement.

The reason map now exists, so extending it to all seven is cheap. Live reading
today: `7 rejecting gate fixture(s) in 17 measured gate run(s)`.

## (b) One idea, three implementations, two unused

`check()` computes `linked_sections` twice and discards both results before
re-deriving the same thing from lines, near the comment about links living on
the LINE. Keep one derivation. This is a tidy with no behaviour change, so the
proof is that the selftest count does not move and every verdict line is
byte-identical before and after on the live tree.

## What is NOT in this task, and why

The ruling dropped three other noticed items and they stay dropped. The
`ledger/verify.py` docstring saying the tool "landed on 2026-09-03 with 30
passing assertions" is a DATED HISTORICAL claim about the landing and is true;
refreshing it to the current count would make it false, and if that docstring
is ever touched the count should be cut rather than updated. The selftest's 17
gate runs have no measured series and no bound, so there is nothing to act on.
