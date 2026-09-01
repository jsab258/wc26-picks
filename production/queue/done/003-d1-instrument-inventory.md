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


DONE 2026-09-01. Output: production/d1-probe/instrument-inventory.md.
Counts: 54 verify checks (6 name a Unity path, none a Unity API), 49 tools
of which 25 read C# directly and would be rebuilt, Core 98 files and 32,554
lines, CoreTests 5 files and about 130 methods carrying 4,163 assertions.
One UNKNOWN named rather than guessed: whether the verdict channel can be
reproduced in UE so its readers keep working, which is the largest lever on
the number and is answerable only on the machine.

FINDING WORTH CARRYING: the obvious count (6 of 54 Unity-coupled) flatters
the move, because the coupling is to the LANGUAGE and not to the engine.
Anyone reading only verify.py would conclude the instruments are nearly
engine-neutral.
