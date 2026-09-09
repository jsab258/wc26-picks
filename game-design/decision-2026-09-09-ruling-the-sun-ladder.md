# Ruling: the sun-intensity ladder, its scope extension, its camera and its order

> **STATUS: LOG, 2026-09-09. NOT CURRENT** once the conditions in section 6 are
> met, the batch is committed and run 38 has landed. Director ruling at spawn
> 2026-09-09T16:28:23Z on queue 205, a SIMULATION change: the light rig of the
> vignette street.
> BUILDS ON: `game-design/decision-2026-09-09-ruling-the-sun-the-bootstrap-and-the-board.md`
> (14:24Z), section 3.1, which ordered this ladder and refused the single
> landed value it replaces. AMENDS: `production/queue/206-set-the-sun-and-sky-from-the-read-curve.md`,
> section 5 below, dictated text.

VERDICT: ALL THREE CONTESTED POINTS APPROVED, ONE OF THEM WITH A FAULT FILED
BESIDE IT. THE DISPATCH GOES TONIGHT, ON THE CONDITIONS IN SECTION 6 AND UNDER
A BRANCH FREEZE.

## 0. What I could not run

NO BASH IN THIS SPAWN. I executed nothing: not `ledger/verify.py`, not
`ue-probe/tests/vignette-spec-test.cpp`, not CoreTests, not
`tools/frame-shadow-probe.py`, not a grep, not a git command. THE 4311, THE 231,
THE 3023 AND THE 548 CHANGED LINES ARE NOT MEASUREMENTS I HAVE. Section 6 turns
every load-bearing one into a condition on this approval, which is the device
the 14:24 ruling used today for the same reason.

What I did instead was read. In full:
`game-design/decision-2026-09-09-ruling-the-sun-the-bootstrap-and-the-board.md`,
`production/queue/206-set-the-sun-and-sky-from-the-read-curve.md`,
`production/d1-probe/DISPATCH` run 38's entry. In part, at every line this
ruling rests on: `production/specs/vignette-scene.json` lines 735 to 895 (the
cameras, all eight conditions, the eleven shots and the ladder note),
`ue-probe/Source/LedgerProbe/Private/VignetteShot.cpp` at 178 to 207, 1257,
1323, 1361, 1393, 1455 to 1465 and 1562,
`ue-probe/Source/LedgerProbe/Public/VignetteSpec.h` at 245 to 259, 452, 1909 to
1960 and 2033 to 2106, `tools/frame-shadow-probe.py` at 450 to 519,
`ledger/Assets/Scripts/Core/StreetVignette.cs` at 124 to 139 and 1811,
`ledger/CoreTests/Program.cs` at 19508, 19543 to 19574 and 19914 to 19926,
`.claude/agent-log.tsv` lines 462 to 469, and
`production/d1-probe/ue-vignette-verdict.txt` line 86.

PREMISE CHECK, CLAUDE.md section 0. Nothing in this batch dates the world
anywhere but 1988 to 1992: the change is a light intensity and a spec field.
Nothing cites GTA V, nothing proposes a purchase, no licence entry moves, no
tool enters. The piece serves the visual half of the Meridian Test directly,
and it serves it by MEASURING rather than by tuning: a street whose sun casts
no shadow is a street a KCD2 player bounces off inside thirty seconds, and the
first of the four Meridian Test conditions is exactly that bounce. No conflict
with the premise.

## 1. Point one: the scope extension is ACCEPTED, deletion included

APPROVED IN FULL, and it is the right call rather than a tolerated one.

The ordered thing is section 3.1's control row: ONE EXTRA SHOT AT SUN 3.0 WITH
THE SKY AT 0.35. I ordered it by name this afternoon and I ordered it as a DAY
row, because the second suspect is the daytime skylight owning the exposure.
`VignetteShot.cpp:1257` still gates the sun on `C.SunOn`, and the two deleted
constants were selected by that same flag. A day condition whose sky is 0.35
is therefore not expressible by a constant keyed on the sun, in any arrangement
of those constants. THE EXTENSION IS NOT ADJACENT TO THE ORDERED THING, IT IS
ITS PRECONDITION. A builder that had stopped at `sun_intensity` alone would
have delivered a ladder with no control row, which is the five-frames-one-
suspect run the 14:24 ruling refused.

The deletion is accepted on the builder's own argument and I am adopting the
argument as the reason: a constant that still looks live and feeds nothing is
the number a later session changes to no effect. Leaving `kSkyIntensityDay`
standing beside a live `sky_intensity` field would also have given one quantity
two producers, which is the fault CLAUDE.md rule 2 names as two numbers derived
from one variable, arriving from the other end.

THE STANDARD, and this sentence is the ruling rather than the prose:

**A BUILDER MAY EXTEND A BRIEF'S SCOPE ONLY WHEN THE ORDERED THING CANNOT BE
BUILT WITHOUT THE EXTENSION, THE EXTENSION STAYS INSIDE THE ARTEFACTS THE BRIEF
ALREADY NAMES, AND IT ARRIVES AS A NAMED DECISION FOR THE DIRECTOR RATHER THAN
FOLDED INTO THE DIFF AS AN IMPLEMENTATION DETAIL.**

All three held here. The third is the one that earned the approval: the builder
flagged the extension, flagged the consequence for queue 206, and did not
quietly rewrite a shared spec.

THE COST I AM ACCEPTING, named so nobody meets it as a surprise. Every
condition in `production/specs/vignette-scene.json` now carries TWO required
fields, and both readers refuse the whole parse when either is absent. A future
condition added by hand will fail loudly rather than inherit. That is the
intended behaviour and it is also a red the first person to add a condition
will meet; THE FIX IS NOT TO DEFAULT THE FIELD.

THE ONE PLACE THE CURED FAULT CAN REGROW, which I found by reading and which
nobody flagged. `wet_night` now carries `sun_intensity: 0.0` while `sun` is
`off`, and line 1257 gates on `SunOn`, so that 0.0 feeds nothing. It is exactly
the shape the deletion was performed to remove, one layer down, in data rather
than in code. IT DOES NOT BLOCK TONIGHT: it is a note-field edit to a spec file
that two test suites parse, and re-proving both suites costs more risk tonight
than the fault costs. Queue item F, section 7, and this record is where the
next session reads that it is known.

## 2. Point two: cam_A for all six rows is the RIGHT TRADE, and no hook rung rides along

APPROVED, and the ride-along is REFUSED for a reason stronger than cost.

The builder's argument is correct as far as it goes: `cam_A` is the only camera
with a pre-sky control on the same pixels, +0.0270 with three fills against
-0.0003 with the captured sky, and the acceptance criterion names +0.027
because it was measured there. A ladder whose rungs are cam_A and whose datum
is cam_hook compares two pixel populations as one.

THE ARGUMENT THE BRIEF DID NOT MAKE, and it is the one that settles it. A
single hook rung would produce a number WITH NO DATUM. `cam_hook` has one
reading, taken after the sky landed, so a hook step of +0.02 at sun 30 could
not be compared with anything: not with a pre-sky hook frame, which does not
exist, and not with cam_A's +0.027, which is other pixels. A number with no
datum is not a cheap extra reading, it is the thing a later session quotes as
if it had one. This studio spent today proving that a value can outlive its
calibration context in total silence. Adding a second such value to the run
that exists to find the first would be the same fault committed knowingly.

AND THE RIDE-ALONG ALREADY EXISTS. `vign_hook_day` is shot in this same run at
sun 3.0 against the same sky, which gives the hook frame a fresh baseline taken
under the run's own conditions. That is the correct hook content for this
dispatch, and it is already in the shot list at line 874.

THE COST STANDS AND TRANSFERS. Rung 1 is judged from `cam_hook`, so this run
answers the rung-1 frame by inference. That is not a defect of the run, it is a
DEBT, and section 5 books it against queue 206 as an acceptance line rather
than a hope. Until that re-measurement lands, NO DOCUMENT MAY QUOTE AN
IMPROVEMENT TO THE RUNG-1 FRAME FROM THIS RUN. The ladder can say what the sun
does to cam_A's pixels and it can say nothing about the hook sheet comparison.

## 3. Point three: the ladder LAST is accepted, AND the one-per-run camera key is a fault to file

BOTH HALVES. The ordering is accepted for this run; the constraint that forced
the choice is an instrument fault and is filed tonight rather than designed
around for ever.

THE ORDERING IS ACCEPTED, and what convinced me is that the builder PROVED the
consequence instead of arguing it: it ran the committed tool against today's
committed frames and got `camBind=REFUSED probeStatus=REFUSED
probe=nothing-measured`, because the last camera today's run placed was
cam_hook. I checked the two ends of that myself.
`production/d1-probe/ue-vignette-verdict.txt:86` reads
`shotCamReadXYZcm=400.0/-210.0/159.8` with `shotCamReadPitchYaw=2.6/11.0`,
which is cam_hook's x 4.0 m, z -2.10 m and 1.65 m eye above a carriageway at
-0.0525 m, and `tools/frame-shadow-probe.py:519` carries
`camBindRule=the-one-per-run-shotCam-line-must-match-this-shots-eye-and-this-cameras-angles`.
The tool failed closed, correctly, and that refusal is the evidence.

The trade is right because of an asymmetry. With the ladder last, six rungs
bind strictly with no flag, and the one frame that loses its strict bind,
`vign_hook_day`, has a SECOND independent route to its camera:
`--camera-from-json` exists at `tools/frame-shadow-probe.py:463`, and the
camera it would read is the same spec file the probe placed the camera from.
The rungs have no second route. Put the ladder first and six frames need the
flag; put it last and one does, and that one has the flag.

NOW THE FAULT. `.claude/rules/instruments.md` says whole-run numbers on the
done line, per-sample numbers on the sample line. A CAMERA POSE IS A PER-SAMPLE
FACT, and this verdict prints it once per run: `VignetteShot.cpp:1455` holds a
single `GCamLine` that the shot loop overwrites, and no shot line carries a
camera key at all. The builder applied precisely the right rule to the sun this
session, adding `shotSunIntensityRead` and its three companions to each shot
line, and did not apply it to the camera one bracket away. That is not a
constraint of the design, it is the same instrument rule unapplied at a second
site, and it is what forced the shot ordering to become a measurement decision.
Queue item E, section 7.

RULED: THE ORDERING SHIPS AS BUILT TONIGHT, AND THE ORDERING IS NOT THE FIX. A
run whose shot order is load-bearing for whether a tool can read it is a run
one reordering away from silence.

## 4. The two things weighed briefly, both approved

THE LAYERING IS APPROVED AND IT IS THE STANDING RULE APPLIED CORRECTLY. The
parse, the required-ness, the ladder arithmetic and every printed string sit in
the layers that compile and run in this container, and `VignetteShot.cpp` holds
live state and call sites only. `.claude/rules/instruments.md` puts it in one
sentence: in a project whose top layer does not compile locally, a formatter
written there ships UNRUN. The refusal paths are the proof that the layering is
real rather than nominal, and both readers hold one:
`ledger/CoreTests/Program.cs:19914` to `19926` deletes each field from the LIVE
file in turn and requires the error to NAME the missing key, and the C++ side
counts the five rungs and the one control row off the same committed file at
`ue-probe/tests/vignette-spec-test.cpp:201` to `216`.

THE UNVERIFIED SURFACE IS NAMED AND THAT IS WHAT MAKES IT ACCEPTABLE:
`ULightComponent::CastShadows` as an integer bitfield, `GetComponentRotation()`
and `Mobility.GetValue()`, all in `VignetteShot.cpp`, none compiled by any
container. Run 33's entry in DISPATCH records that five UE 5.8 API uses in this
same file met their first compile in CI and that a failure there is the cost of
the reading. The same applies tonight and the DISPATCH entry says so.

THE FOUR `sun*Read` KEYS AND THEIR PER-SAMPLE TWINS ARE APPROVED. On a six-row
ladder a one-per-run last-wins key describes the control row and nothing else,
and `sunReadStat` says so on the line. The per-sample `shotSun*Read` keys are
what attribute a rung to the light that lit it rather than to a row of a file,
and step 3 of the DISPATCH read order makes them a STOP condition: if a rung's
read does not match its row, the field is not reaching the component and
nothing below it is evidence. That is the correct place for that check.

## 5. The amendment to queue 206, dictated text

The resident replaces the `spec:`, `acceptance:` and `status:` blocks of
`production/queue/206-set-the-sun-and-sky-from-the-read-curve.md` with exactly
the following, and changes nothing else in that file:

    spec: Set the sun, and if the control row says the skylight owns the exposure also
      the sky, from the series queue 205 prints. THE LEVER IS NO LONGER A CONSTANT:
      kSunIntensityDay was never created and kSkyIntensityDay and kSkyIntensityNight were
      DELETED by queue 205, ruled 2026-09-09 in
      game-design/decision-2026-09-09-ruling-the-sun-ladder.md section 1. Both numbers now
      ride on the condition as sun_intensity and sky_intensity in
      production/specs/vignette-scene.json, so this item edits DATA in overcast_day and
      wet_night and edits no C++ constant. Both readers require both fields, so a value
      cannot be dropped rather than changed.
    acceptance: four things, and the third is a debt booked by the ruling rather than a
      new ask.
      1. The condition's own note field cites the run number, the commit and the RUNG the
         value was read from, in the same file as the value. A JSON file has no comment,
         and the note field is where the provenance lives for every other number here.
      2. The next committed rung-1 frame meets queue 205's prediction: shadow-edge step at
         or above +0.027 where it now reads -0.0035, asphalt lit-minus-shadowed positive
         from -0.0131, and band.ground.p05 below 0.50 from 0.5776.
      3. THE HOOK FRAME IS RE-MEASURED, not inferred. Queue 205's ladder is six cam_A rows
         and cannot speak for cam_hook's pixels; until this item prints a cam_hook reading
         after the value lands, no document may quote an improvement to the rung-1 frame
         from run 38.
      4. THE LADDER ROWS ARE DECIDED, not left. The five ladder_ conditions and the control
         row cost six rendered frames and about 11 MB on every subsequent probe run. This
         item either removes them, with the read series preserved in its decision record,
         or keeps a named subset with the reason written beside it. Silence is not an
         option: rows kept by default are rows nobody chose.
    max_sessions: 1
    status: BLOCKED on queue 205 landing a READ series, not on queue 205 dispatching.
      IT IS BLOCKED ON PURPOSE AND THE BLOCK IS THE POINT: rule 2 says a bound is set from
      a printed series, and the series does not exist until run 38's frames are measured by
      tools/frame-shadow-probe.py with each frame's own three instrument checks quoted
      first. Landing a number here before then would be the exact fault the ladder was
      ordered to prevent.

## 6. THE DISPATCH: YES TONIGHT, and the conditions on it

IT DISPATCHES TONIGHT. The 14:24 ruling made the probe wait behind the art
render because `ledger-art-blender-preview.yml` YIELDS rather than queues and a
probe dispatch would destroy the render's run silently. No art render is in
flight, so that gate is clear and the ordering constraint it created is spent.

WHAT DOMINATES THE RUN TIME, per rule 7, and what I do not know. The capture is
NOT the dominant term: six extra shots move capture from 10.66 s to about 23 s
against a 20-minute step cap, a delta of roughly 12 s. The build and the cook
dominate, and I have no number for them from this session. WHAT COULD BLOW IT
UP is the first compile of three named UE 5.8 API uses in `VignetteShot.cpp`;
if that fails, the run reports a compile error and the ladder costs one round
trip, which is the price the reading was ordered at.

READ PREDICTION 5 FIRST, BEFORE ANY OTHER NUMBER IN THE RUN.
`vign_ladder_sun003` and `vign_camA_day` are the same camera at the same sun
with every other value copied character for character, so they must be the same
picture. If they differ, the field did not replace the literal cleanly and NO
OTHER RUNG ON THE LADDER MEANS ANYTHING. That check costs nothing and it is the
one that can invalidate the rest.

THE BRANCH FREEZES ON THE PUSH. Runs 18, 22 and 23 in `production/d1-probe/DISPATCH`
are three losses to exactly one mistake: the runner checks out the dispatch
commit, works, and then pushes onto a branch that moved under it. Capture the
sha BEFORE dispatching, watch by ancestry, and push NOTHING to this branch,
not a document, not a queue item, not a status file, until a landed run's
commit contains this one.

CONDITIONS ON THIS APPROVAL. Every one is a number I do not have and the
resident must print this session; every line pasted into the commit message
comes VERBATIM from the run and never from this record.

1. `python3 ledger/verify.py`, footer pasted FROM `ledger/.verify-footer`.
   CONDITION: `director_cadence` must be GREEN carrying this record's stamp,
   `spawn=2026-09-09T16:28:23Z`, which is my own `studio-director` row at
   `.claude/agent-log.tsv:469` and is the newest row in the file. If it is red,
   the stamp or the row is wrong and THE COMMIT DOES NOT GO IN ON A HAND-EDITED
   GATE.
2. The CoreTests count and the C++ spec-test count, both in full with their
   denominators, from THIS session's run. CONDITION: both suites green, and the
   two REJECTING cases must be among them by name, the missing `sun_intensity`
   and the missing `sky_intensity` each producing an error that names its key.
   A ladder whose required field is not proven required is a defaulted field.
3. `python3 tools/frame-shadow-probe.py --selftest`: the 12 of 12 with the
   accepting case first. CONDITION, carried unchanged from the 14:24 ruling:
   that tool's MEASUREMENT code is unchanged in this commit. `git diff --stat`
   on the file, and if any line of the maths, the luma weights, the tracer or
   the binning moved, this approval does not cover it.
4. THE TOKEN GREP, rule 1. `kSkyIntensityDay` and `kSkyIntensityNight` across
   the whole tree, with the COUNT OF HITS EXAMINED printed beside the result.
   CONDITION: every surviving hit is a comment or a record, and zero are live
   code or a live spec field. I read the four I know of, at
   `VignetteShot.cpp:188`, `VignetteSpec.h:245`, `vignette-spec-test.cpp:215`
   and `StreetVignette.cs:127`, and a grep is what proves there is no fifth.
5. THE CALL-SITE GREP, rule 6. `sun_intensity` and `sky_intensity` each have a
   reader in BOTH readers and a use at the light. Built is not running: the
   field is done when the component reads it, and `VignetteShot.cpp:1257` and
   `1323` are the two lines that must appear.
6. `python3 tools/docs-check.py`, after this file exists.
7. `production/d1-probe/DISPATCH` is the LAST file touched and the push is a
   SINGLE push. Then the freeze in the paragraph above.

## 7. The quality ladder at close, and the queue items filed

Best available or first working, per aspect, next rung named. None is blank.

- The light rig: at "the fault is located, the series is ordered and not yet
  read". Next rung is run 38's six frames measured with each frame's own three
  instrument checks quoted first. The rung above that is queue 206's sun and
  sky set from the read curve, and above THAT is the rung nobody has costed: an
  exposure that is stated rather than inherited, because auto exposure is in
  force and unoverridden and the probe says so itself.
- The shot spec: at "every light in the frame is a named field on the condition
  and no bare literal remains in the emitter". Next rung: the same treatment
  for the lantern intensity and the window practicals, both of which
  `vignette-scene.json` already admits are first values of a series that has
  never been printed.
- The verdict as an instrument: at "per-sample light state on the sample line,
  whole-run state on the run line". Next rung is queue item E, the camera key,
  which is the same rule at the one site it was not applied.
- The ladder's own reading: at "one camera, one axis, six rows, one control".
  Next rung: the hook camera measured rather than inferred, which is queue
  206's acceptance line 3.

Queue items this ruling files, numbers the resident's to assign, none started
now:

- E. THE ONE-PER-RUN CAMERA KEY. Per-shot `shotCamReadXYZcm` and
  `shotCamReadPitchYaw` on each shot line of the vignette verdict, and
  `tools/frame-shadow-probe.py` binding per shot off them, with
  `--camera-from-json` demoted to a fallback rather than the route. CONDITION
  carried from the 14:24 ruling: the binding change and any measurement change
  do not land in one commit. Blocked on run 38 landing, because it changes the
  verdict format the run is about to write.
- F. `wet_night` carries `sun_intensity: 0.0` while its sun is off, and line
  1257 gates on `SunOn`, so that value feeds nothing. Either the note says so
  in the file, or the field's meaning when the sun is off is defined once and
  both readers state it. Section 1 above is the finding.
- G. THE LADDER ROWS' LIFECYCLE, folded into queue 206 acceptance line 4 rather
  than filed separately, and named here so a reader of this record finds it.

<!--RULING spawn=2026-09-09T16:28:23Z paths=ledger/Assets/Scripts/Core/StreetVignette.cs,ledger/Assets/Scripts/Core/StreetVignettePieces.cs,ledger/CoreTests/Program.cs,production/specs/vignette-scene.json,production/specs/vignette-pieces.json,ue-probe/Source/LedgerProbe/Public/VignetteSpec.h,ue-probe/Source/LedgerProbe/Private/VignetteShot.cpp,ue-probe/tests/vignette-spec-test.cpp,production/d1-probe/DISPATCH,production/queue/206-set-the-sun-and-sky-from-the-read-curve.md,game-design/decision-2026-09-09-ruling-the-sun-ladder.md-->
