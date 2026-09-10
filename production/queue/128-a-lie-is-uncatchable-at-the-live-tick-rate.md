line: production (the moat)
spec: sub-fault of queue 127, found by the sweep that measured lieHeard=0/90.
acceptance: a scenario at the build's own cadence in which the player lies and
  the contradiction is detected; today the count is 0 of 5 player-rumour
  events at live cadence
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-06. Blocks queue 127's acceptance.

## The finding

The contradiction only fires when a rumour ARRIVES at someone who has already
been told otherwise. A HEARD rumour never enters `KnowledgeBase`: only a
`Witness` at 0.95 and above does that. So `Claims.Process` sees `Unknown` at
the moment the player lies.

At the shipped tick rate (`TickIntervalGameMinutes=6`) the street moves within
minutes of the crime, which is HOURS before Lena asks. There is no second
arrival, so there is nothing to contradict. Measured: `lieCaughtAtLiveCadence=0/5`.

The console harness stages the conversation BEFORE the gossip on purpose, and
its own comment says why. The shipped game cannot do that.

## Two shapes a fix could take, neither chosen here

Either heard rumours feed `CheckClaim`, or claims are re-checked against
carried rumours when one arrives later. The second sounds closer to how a
person actually catches a lie: you are told something, and later something
contradicts it.
