# 251. Wire D18's age floor and the trades denominator, and take both off the reach ledger

STATUS: READY, 2026-09-10. Filed the moment two APIs went onto the reach
allowlist, so the allowlist entries have an owner and a trigger and cannot
quietly become permanent. An allowlist entry with no queue item behind it is a
mute button with a paragraph attached.

## What is on the ledger and why

`bash tools/reach-check.sh` went RED on the D18 batch with

    UNREACHED - 2 behavioural Core API(s) with no caller:
      tested, unwired method   ContentRule.IsShowableAge    ContentRule.cs:49
      tested, unwired property Population.TradesScreened    Population.cs:180

Both are now on `ledger/ReachCheck/allow.json` with `WIRE:` reasons, taking it
from 39 to 41 entries, `0 unexplained`, `0` reasons under the fifteen-character
floor. Neither is dead code and neither is a mistake: both were written ahead of
the thing they act on, which the reach gate correctly cannot tell apart from
abandonment.

## 1. ContentRule.IsShowableAge

`AdultFloorYears = 18`, and `IsShowableAge(int years)` returns
`years >= AdultFloorYears && years <= 120`. The upper bound is deliberate: a
negative age would otherwise pass a bare `>= 18` test by arithmetic accident.
It is tested in `CoreTests/Program.cs`, accepting cases first (24 and 58 pass)
then rejecting (17, 0 and -4 refused).

IT HAS NO CALLER BECAUSE A RESIDENT HAS NO AGE. Its own docstring says why it
was written first: "Adding the guard after the field is how the field ships
without one."

WHAT D18's NO-CHILDREN RULE ACTUALLY RESTS ON TODAY, so nobody reads this item
as a hole: the generator screens model stems through
`ContentRule.IsUnderageModel` and `RealBody` screens the body pool, and both are
reached. The visual path is guarded. The age path has no data to guard yet.

TRIGGER: the commit that gives a resident an age must call `IsShowableAge` in
`Population.Generate` before anybody is admitted, and delete the allowlist entry
in the same commit.

## 2. Population.TradesScreened

`TradesRefused` is the list of trades the content screen removed;
`TradesScreened => Trades.Length` is how many it looked at. Rule 3b is the whole
reason the second one exists: `TradesRefused.Count == 0` cannot tell a clean
screen from a screen that examined nothing.

THE REAL GAP IS THAT NOTHING PRINTS EITHER. The denominator is unreached because
the numerator is unprinted. Allowlisting the property records that; it does not
fix it.

TRIGGER: when the crowd emits a verdict line it prints
`tradesRefused=N/N examined` from this property, and the allowlist entry goes in
that commit.

## Done looks like

Both entries gone from `allow.json`, `reach-check.sh` still green with 39 on the
ledger rather than 41, and the crowd's verdict line printing the refused count
beside its denominator. For the age floor, a rejecting case planted: a resident
built with an age under the floor must not be admitted, proven in a run and not
only in a unit test.

## Risk

The risk is the one this item exists against. Two `WIRE:` entries that nobody
returns to become two `BY DESIGN:` entries by attrition, and the age floor is
the guard that stops a child being generated once ages exist. If the age field
lands without this call, D18 loses a layer silently and the reach gate will not
say so, because the entry excusing it will already be there.
