line: research (D1 probe, measurement c)
spec: production/d1-probe/plan.md, measurement c
acceptance: every existing instrument listed with a PORTS or REBUILDS verdict and a one-line reason; count of instruments examined printed
max_sessions: 1

Write production/d1-probe/instrument-inventory.md: what a move to UE5 would
actually cost in instruments, which is measurement c and needs no UE5 to
answer honestly.

Walk the real list, not a remembered one: the checks in ledger/verify.py,
the screenshot pipeline, the verdict channel and its readers under tools/,
the 4,163 CoreTests, the gates in the sim. For each: PORTS (the logic is
engine-neutral, it moves with a path change), REBUILDS (it reads a Unity
API or a Unity artifact and would be written again), or UNKNOWN with the
question that would settle it.

The output is a COUNT with a denominator, not an impression: N examined, X
port, Y rebuild, Z unknown. That number is what measurement c contributes
to the decision record.
