line: production (the moat)
spec: sub-fault of queue 127, found while running the pressure curve at the
  build's own cadence.
acceptance: a rumour aged a thousand steps produces zero re-tells, with the
  count and its denominator printed; both call sites fixed together
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-06. Small, and it corrupts any multi-day measurement
  taken before it is fixed.

## The finding

`Gossip.cs` Tick line 381 guards with `existing.Confidence >= passed`, where
`passed = r.Confidence * tie * HopDecay`. After `Age` multiplies both copies by
the same factor, the two sides are THE SAME REAL NUMBER reached by different
multiplication orders, and they differ by one bit, 2.22e-16. When the new one
lands high, the guard opens and the mill re-tells a story it should have
refused.

Isolated probe over ten days of hourly ageing: tie 0.50 opens 3 of 600 steps,
0.60 opens 2, 0.70 opens 0, 0.80 opens 3.

In the live-cadence run, 3 of the 5 player-rumour events were these phantom
re-tells. Any five-night scenario built before this is fixed is measuring
floating point.

## The same idea implemented twice

`CompareNotes` at `Gossip.cs:483` carries the IDENTICAL guard with the
IDENTICAL `Raise` behind it. Fix both or the fault survives in the half nobody
looked at.
