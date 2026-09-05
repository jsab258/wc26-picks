line: production (the Unreal emitter, Phase C)
spec: game-design/decision-2026-09-03-texture-staging-and-the-still-gate-ratchet.md, ruling E
acceptance: materialConnections=14/14 with materialStatus=MADE on a LANDED run, or 14/14 with materialStatus=WIRED-BY-PROPERTY-WRITE plus the four frames read by a verifier and showing tiling; never a local claim
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

## STEP 1 LANDED 2026-09-03, STEP 2 BEFORE DISPATCH

Step 1: the nine-candidate sweep, `materialUvHeadVia`,
`materialUvHeadTriedAtWorst`, `materialUvHeadReadback`, selftest 11 to 30
cases. Ruled: the count may include a head made by the last-resort property
write; the status word may not. Step 2, a precondition to run 21:
`material_status` takes the count of heads made by property write, and 14 of
14 with that count above zero prints
`materialStatus=WIRED-BY-PROPERTY-WRITE` with `materialScriptReturn=2`; two
selftest cases, accepting first. Ruling:
game-design/decision-2026-09-03-batch-review-register-banner-spawnlog-uvsweep.md.

## STEP 2 LANDED 2026-09-05, RUN 21 AUTHORISED

`material_status` takes the property-write head count; 14 of 14 with it above
zero prints `materialStatus=WIRED-BY-PROPERTY-WRITE` and
`materialScriptReturn=2`; 14 of 14 with `materialUvHeadByPropertyWrite=0/2`
still prints `MADE`. Selftest 30 to 40 checks, both cases from head records.
The deciding count is printed as `materialUvHeadByPropertyWrite`, adopted by
the ruling. Ruling and the reading table for run 21:
game-design/decision-2026-09-05-ruling-062-step-2-third-status-word.md,
section 5. The rule fires again on `materialConnections=12/14`.

NOTE, not before run 21: the `CREATE-FAILED` line in `main()` carries no
`materialScriptReturn` and no UV keys. A verifier reading that word reads it
as nothing measured. Fix when the file is next open.

## RUN 21 LANDED 2026-09-05: THE WIRE MOVED, AND THE STREET IS STILL NOT TEXTURED

THE FRACTION FIRST, as the dispatch entry ordered. `materialConnections=14/14`,
up from 12/14 which had held across runs 19 and 20. Taken by the FIRST
candidate pair, `materialUvHeadVia=both.out.empty..in.empty`, with
`materialUvHeadTriedAtWorst=1/9`. `materialUvHeadByPropertyWrite=0/2`, so
`materialStatus=MADE` is the honest word and the third state did not fire.

THE FRAMES CONFIRM IT INDEPENDENTLY OF THE COUNT, which is the point of having
read them. The flat grey of runs 19 and 20 is gone: the ground and the signs
carry a checkerboard that TILES CORRECTLY IN PERSPECTIVE, which is exactly what
a working UV chain looks like and cannot be faked by a count.

BUT THE CHECKER IS UNREAL'S OWN PLACEHOLDER, not Meridian's texture, and WHY
IS NOW AN OPEN QUESTION RATHER THAN AN ANSWERED ONE.

CORRECTION 2026-09-05, AND IT IS THE RESIDENT'S ERROR, CAUGHT BY THE PRODUCER
BEFORE THE MESSAGE WENT OUT. This section first said the texture staging step
did not run, citing `grep -c` for `stagedTex|piecesTextured` in
`ue-build.txt` returning 0, and cited `shotDistinctBuckets=5/32768` as the
pixels agreeing. BOTH WERE WRONG AND BOTH ARE THE SAME FAULT: reading the
right key out of the wrong file.

- THE STAGING RAN. `.github/workflows/ledger-probe-unreal.yml` writes those
  keys onto `ue-vignette-verdict.txt`, NEVER onto `ue-build.txt`, so that grep
  returns 0 in every run there has ever been. It measured nothing. This run's
  vignette verdict reads `stagedTexFiles=102/102 texRootFiles=51
  mapsFound=36/48 texturesImported=36 midsCreated=563 piecesTextured=563/593`
  and `surfacesResolved=12/16`, which is run 20's staging repeated, not absent.
- THE FIVE BUCKETS ARE A DIFFERENT PICTURE. `shotDistinctBuckets=5/32768` is
  the PERCEPTION PROBE's debug screenshot, a black frame with a wireframe cube
  and three coloured lines. THE STREET FRAMES READ 109, 100, 87 AND 19
  BUCKETS. Attributing that number to these frames was reading a gate for one
  artifact as though it described another.
- `materialColourDefault=/Engine/EngineResources/DefaultTexture` is the
  PARAMETER'S DESIGNED DEFAULT, printed identically on the passing selftest
  fixture. It does not by itself say ours failed to bind.

SO THE HONEST STATE: the wire moved, the frames changed, the textures were
staged and 563 of 593 pieces were assigned, AND THE FRAMES STILL SHOW THE
ENGINE CHECKER ON SURFACES THE VERDICT SAYS WERE ASSIGNED. That is an unnamed
fault and the next thing to find. It is NOT the staging step, which is what
this section wrongly claimed for an hour.

TWO MORE THINGS THE RUN SAYS, neither fatal, both to carry forward:
- `materialUvHeadReadback=0/2..unreadable2`. The connections counted 14/14 and
  the readback could confirm NEITHER head. The frames are what closed that gap
  this time; a count and a readback that disagree should not be left unwatched.
- THE MATERIAL KEYS ARE IN `ue-build.txt` AND NOT IN `ue-verdict.txt`. The
  verdict file is 275 bytes and carries only perception rows. Anything reading
  the verdict for a material reading finds nothing measured.

ACCEPTANCE: MET on its letter, `materialConnections=14/14` with
`materialStatus=MADE` on a landed run. The stop rule that held since run 20 is
DISCHARGED. What it was protecting against is not: the street is not textured,
for a different and now-named reason.
