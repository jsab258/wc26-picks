line: production (the Unreal emitter, Phase C)
spec: game-design/decision-2026-09-03-texture-staging-and-the-still-gate-ratchet.md, ruling E
acceptance: materialConnections=14/14 with materialStatus=MADE on a LANDED run, not on a local claim
max_sessions: 1
status: READY 2026-09-03. engine-specialist. THE LIVE BLOCKER OF PHASE C, first in line after run 20 reads out.

## The finding

Run 19's material generator wired 12 of 14 connections. The two refusals are
recorded verbatim from that run:

    texcoord-to-maskU-refused/texcoord-to-maskV-refused

Those two are the HEAD OF THE UV CHAIN that all three texture samplers hang
off. So every sampler reads one UV and no surface can tile correctly, which is
why `materialStatus` is now PARTIAL by design rather than MADE.

Filed as its own item rather than folded, because a named blocker hidden
inside a large item stops being read.

## The likely cause, stated as a lead and not as a fact

The ComponentMask input pin is probably not named `Input`, so the connect call
names a pin that does not exist and is refused silently. That is a lead from
reading the script, not a diagnosis: nothing here can open Unreal.

## The bound that comes with it, from the ruling

`materialConnections` is the number that moves under a constant word. If that
fraction fails to move between two consecutive landed runs, STOP DISPATCHING
and fix this item. A status word that stays PARTIAL while its fraction stands
still is a run that is teaching nobody anything.
