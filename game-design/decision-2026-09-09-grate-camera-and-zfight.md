STATUS: LIVE, verified 2026-09-09.

# Ruling: the grate camera, the z-fight instrument, and what run 35 may claim

LAND, WITH AMENDMENTS. No amendment blocks the commit and no amendment blocks
the dispatch: the frames are the expensive artifact and they are safe, and the
two open questions below go to the run as measurements rather than as argument.
The one thing that can still go wrong is the NUMBER, not the run, and it is
recoverable from the landed frames without a second dispatch. Dispatch now.

Decided by the studio director, spawned 2026-09-09T03:05:06Z, on the
uncommitted WalkProbe.cpp (+384/-5), tools/grate-zfight.py (new),
production/NOW.md and production/findings.txt. Reference commit f060f791.
Run 34's numbers (propFullyBuried=0/23, propsAsMesh=22/23,
propPlacedWithCollision=22/22, propBurialSubject=prop_drainage_grate_01_0/
via=loaded-asset/collision=YES/topM=-0.0650/open=60.0pct,
propCentreWorstMm=0.00) were measured by the run and quoted by the resident;
every number in section 1 below I computed in this seat from the code, and each
says so.

## 1. The camera's arithmetic: CHECKED, and it points at the piece

Recomputed from WalkProbe.cpp lines 171 to 207 and 588 to 652, and from
LedgerVignette::HorizontalFovDeg in VignetteSpec.h line 513, which I read
rather than trusted:

- Standoff. sqrt(130^2 + 125^2) = 180.35 cm. The comment's 1.80 m holds.
- Pitch. atan(125/130) = 43.88 degrees down. The comment's 43.9 holds, but the
  pitch is a DESCRIPTION, not an input: CamRot comes from
  (AimAt - CamLoc).Rotation() with AimAt at the placed bounds centre and top.
  The aim cannot miss the piece by a pitch error, only by a bounds error, and
  the bounds are printed on the same line. This is the right construction.
- Field. HorizontalFovDeg(40, 960, 540) = 65.80 degrees, not the 65.9 in the
  comment. Harmless, and the comment is the only thing wrong; correct it
  opportunistically, never with a rebuild of its own.
- Frame at the piece. 2 x 1.8035 x tan(32.90) = 2.334 m wide, 1.313 m tall. A
  0.3999 m piece is 17.1 percent of the width, 164 px, and its depth extent
  foreshortens to 0.40 x sin(43.88) = 0.277 m, 21.1 percent of the height,
  114 px. The builder's 165 x 114 reproduces.
- The subject rectangle, which is what the statistic actually reads. Yaw is
  exactly -90 (CamLoc differs from AimAt in Y and Z only), so the projected
  22 cm square is a trapezoid with horizontal top and bottom edges: near edge
  94.6 px, far edge 86.7 px, height 62.8 px, axis-aligned box about 95 x 63 px,
  interior examined about 5,673 px per frame. The box overspills the trapezoid
  by at most 4 px per side at the top, and the subject sits 9 cm (about 37 px)
  clear of the piece's side edges, so the overspill lands on grate.

Legible enough for the round trip: yes. Not because 165 x 114 is pretty, but
because the measured rectangle carries thousands of examined pixels rather than
dozens, which is what makes a density mean anything.

One input I did NOT verify and cannot from code: that vignette-scene.json puts
the east footway's camera at z=4.0 m, which is what makes C.Y + 130 cm a
standpoint on the footway rather than in the road. It is visible in the frame.
Read the frame before trusting the claim.

## 2. The view target: restore is enough, but it is not what protects the run

Capture-and-restore is correctly built: GViewBefore is the controller's actual
view target, not an assumed pawn; restore puts back what was captured;
ConfirmRestore reads it back a phase later and prints RESTORED or NOT-RESTORED;
every unreached path prints NOT-REACHED or NOTHING-MEASURED rather than silence.

But the restore is NOT the thing that keeps run 35's other numbers safe, and
the record must not say it is. Three paths leave the view on the probe camera
or leave the restore unread: a crash inside the grate phases, a ceiling on
either grate shot, a null controller at ConfirmRestore. What makes all three
harmless is that NOTHING IS PHOTOGRAPHED OR MEASURED AFTER THE VIEW IS TAKEN.
I checked the two facts that establish that: the grate phases are last before
Done (tick lines 1117 to 1170), and the sequence capture runs only inside the
three walking phases through ApplyMovementAndMaybeCaptureSequence, so no
ue-walkseq frame can be shot through the grate camera.

AMENDMENT 1, for the resident, blocks neither commit nor dispatch. Record the
ordering as a CONSTRAINT, not an accident: no phase that captures a frame,
reads a view point, or measures anything may be added after AimGrate. If a
later batch needs one, it goes BEFORE AimGrate or the restore stops being
best-effort and becomes load-bearing.

## 3. The 7 cm bias: honest scoping, with one claim that is too wide

Honest. A speckle statistic reads high-frequency disagreement, and a paint
edge IS a high-frequency disagreement that has nothing to do with a depth tie;
excluding it is scoping to the phenomenon. It is declared with its numbers, and
the rectangle still sits wholly on the piece. Gerrymandering would be moving
the rectangle until the answer changed; this moved it off a known confound
before any answer existed, and said so in the source.

What is too wide is the words. The subject spans z 2.76 to 2.98, which is
entirely inside the channel course (2.745 to 3.00). So this run measures the
grate-to-CHANNEL coincidence only. The crown-side strip where the grate meets
the CARRIAGEWAY, about 2.60 to 2.745, is examined by no rectangle in this
batch, while the tool's header and grateSubjectIs both speak of "the channel
and carriageway top faces".

AMENDMENT 2, for the Producer and for whoever writes the close-out, blocks
neither. Run 35 may not be reported as "no tie under the grate". The claim it
can support is "no tie where the grate meets the channel, over 22 of the
piece's 40 cm". The carriageway edge is UNMEASURED and is named as such.

The control is fair as a NULL and is not a matched comparison. Same PIXEL area
is the right denominator for a pixel-count statistic, and taking it from the
subject's own box rather than a second calculation is right. But at 80 cm
toward the crown the control sits 2.44 m from the camera against the subject's
1.80 m, and at a 30.8 degree grazing angle against 43.9, so it is a coarser
texel footprint at a shallower angle; and it is plain asphalt while the subject
is a modelled grate whose bars and slots are legitimate detail. Both
differences REDUCE speckle in the control, so both push the speckle half
toward TIE.

Therefore, and this is the binding half of this section: THE FLICKER HALF IS
THE EVIDENCE AND THE SPECKLE HALF IS CONTEXT. Static detail, distance and
grazing angle all cancel between two frames of a camera that did not move;
only temporal instability moves flicker. A speckle-only excess is not evidence
of a tie and may not be reported as one.

Next rung, named per the quality ladder rather than taken tonight: a control
displaced along world X instead of toward the crown. At yaw -90 the view depth
is independent of X, so an X-displaced control at the same z band has the same
distance, the same grazing angle and the same surface as the subject's
surround, which removes both biases for the cost of one more projection.

## 4. The one threshold: a first cut may stay, on two conditions

Acceptable. Rule 2 forbids a threshold that carries a conclusion, not a
labelled split printed beside its series, and this file already contains the
same pattern ruled acceptable: kStuckFloorCm = 50.0 at WalkProbe.cpp line 147,
declared a coarse first cut with the raw distances printed beside it. I grepped
the repository for zfightStatus: the only hits are the tool itself and comments
in WalkProbe.cpp. No gate reads it, so a wrong headline here is a reading
error, not a ratchet.

AMENDMENT 3, for the Producer and the next instrument builder, blocks neither.
(a) zfightStatus may not appear as the finding in a report or a close-out; the
densities and the excess series are the finding. (b) The cut is replaced from
this run's printed series once real numbers exist, and when it is replaced the
8 px floor becomes a density or is named per-frame: it is currently an absolute
count compared against a CUMULATIVE examined count, so its meaning changes with
the number of frames given.

## 5. What actually bites, which nobody asked about

AMENDMENT 4, for a tier-3 builder, blocks neither the commit nor the dispatch,
and is the highest-value item on this page. rect_px rounds four fractions
independently for each rectangle. The probe constructs the control with the
SUBJECT'S OWN HalfW and HalfH, so the two rectangles have the same true pixel
size, but at different screen positions: round(x1) - round(x0) can be 94 for
one and 95 for the other. measure() then fails its same_area check and returns
NOTHING-MEASURED. With a true width near 94.6 px and a true height near 62.8,
the odds that both integer sizes agree are roughly one in three. The most
likely single outcome of running this tool on good frames, as written, is
"nothing measured".

The fix lives in the TOOL, per instruments.md: snap the control's integer size
to the subject's when the declared sizes agree within 1 px on both axes, and
keep refusing when they do not, so the existing rejecting fixture
(0.10/0.05/0.30/0.20) still refuses. Add the case that is currently missing: a
control declared 1 px off snaps and measures. Re-run the selftest.

It does not block the dispatch because the frames are what costs seven minutes.
The workflow stages production/d1-probe/ue-walk_*.png by name glob, so
ue-walk_05_grate_a.png and _06_grate_b.png land with the run, and the Pillow
pass re-runs on them locally for free. DO NOT RE-DISPATCH FOR THIS.

## 6. Rule 6: nothing calls the tool, so the number is a local run

I grepped the repository for grate-zfight: the only hits are the tool and
comments. No workflow step runs it. Run 35's committed verdict will carry no
zfight key at all, which means the reading the earlier ruling demanded is
satisfied tonight only by a LOCAL run on the landed frames, recorded in
production/findings.txt with the two frame names, the run's commit and the
tool's commit. Do not add the PowerShell step in this dispatch: a workflow step
is only testable by a seven-minute run, and it sits inside the one channel that
can be read. Queue it as "grate-zfight step in ledger-probe-unreal.yml".

AMENDMENT 5, for the resident, blocks neither: before any density is believed,
check that zfightFrameWH (the PNG) has the same ASPECT as grateRectFrameWH (the
viewport the fractions were computed against). The capture path has two
candidates, the rectangles are fractions of the viewport, and a mismatched
aspect puts both rectangles on the wrong pixels silently. If the aspects
differ, the reading is UNRESOLVED, not clean. And open both frames first
(rule 4): the grate is near frame centre or the geometry argument above is
wrong somewhere I could not see from the code.

## What Jafar's brief may say at 04:00

The accepting case is measured and now photographed. What is settled: the grate
is a real mesh, placed, collidable, at the surface. What is open, with names:
whether its top face ties in the depth test where it meets the CHANNEL, which
the flicker density on the two new frames answers; and the carriageway edge,
which is unmeasured. Neither is reported as clean until a number exists.

<!--RULING spawn=2026-09-09T03:05:06Z-->
