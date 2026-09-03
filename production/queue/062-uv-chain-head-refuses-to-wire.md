line: production (the Unreal emitter, Phase C)
spec: game-design/decision-2026-09-03-texture-staging-and-the-still-gate-ratchet.md, ruling E
acceptance: materialConnections=14/14 with materialStatus=MADE on a LANDED run, not on a local claim
max_sessions: 1
status: READY 2026-09-03, AND IT IS NOW PROVEN TO BE THE ONLY THING BETWEEN THIS PROJECT AND A TEXTURED UNREAL STREET. Run 20 staged the textures perfectly (stagedTexFiles=102/102 texRootFiles=51 mapsFound=36/48 surfacesResolved=12/16 piecesTextured=563/593) and the four frames are STILL FLAT GREY. A texture sampler with no UV input reads one constant, so 563 correctly textured objects render as flat colour. materialConnections held at 12/14 across runs 19 and 20, which fires the ruling's stop rule: NO FURTHER UNREAL DISPATCH UNTIL THIS IS FIXED. engine-specialist.

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


## What run 20 proved, 2026-09-03

Everything downstream of this bug works. The staging lands 51 files in both
places the binary looks, 36 of 48 maps are found, 12 of 16 surfaces resolve,
and 563 of 593 pieces carry a material instance. None of it reaches a pixel,
because the samplers have no coordinates to sample at.

So this item is not a polish item and never was. It is the last wire in Phase
C, and the evidence that it is the last one is that every other number in the
chain now reads what it was predicted to read.

THE WORD WAS CARRYING THIS ALL ALONG. `materialStatus` read PARTIAL rather
than MADE only because the 3 September ruling insisted MADE must mean
wired == asked. Under the old definition run 20 would have reported MADE, and
the search would have gone looking for a phantom somewhere in the renderer.
