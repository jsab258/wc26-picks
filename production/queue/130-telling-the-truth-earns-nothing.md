line: production (the moat)
spec: sub-fault of queue 127.
acceptance: a scenario in which telling the truth leaves the player measurably
  better off than staying silent; today both end at suspicion 0.060, identical
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-06. Small, and it is a hole in the premise rather than
  in the code: a social sim in which honesty is worth exactly nothing.

## The finding

`Claims.Process` lowers suspicion by 0.03 only on `Consistent`, and
`Consistent` cannot happen before the rumour arrives (queue 128). So across
the whole sweep, truth and silence are NUMERICALLY IDENTICAL: both end at
0.060.

A player who tells the truth gains nothing a player who says nothing does not
also gain. That is not a balance question, it is an absence: there is no path
by which honesty pays.
