STATUS: LIVE, verified 2026-09-09.

# Ruling: the railing in the line, the vote, the lift, and the denominator a step may print

LAND WITH AMENDMENTS. Six, numbered below. A1 and A2 block the commit and are
dictated text a resident applies. A3 blocks the dispatch and is one tier-3
builder turn of PRINTING ONLY. A4, A5 and A6 block neither. THE DISPATCH MAY GO
AS SOON AS A3 IS IN AND ITS DIFF TOUCHES NOTHING BUT PRINTED KEYS; if the diff
touches the vote or the selection, refuse it and dispatch without it.

Decided by the studio director spawned 2026-09-09T03:55:58Z, on the uncommitted
WalkProbe.cpp, tools/grate-zfight.py and .github/workflows/ledger-probe-unreal
.yml, against reference commit 7c9bd614. Everything below that is a number
either comes from a file I opened this session and is named at the line, or was
computed in this seat from numbers that do, and says which.

## 0. What frame 05 actually shows, because the brief for this change is wrong about it

I opened production/d1-probe/ue-walk_05_grate_a.png and
production/d1-probe/ue-walk_02_after_clear.png at full size (rule 4). The
finding that drove this change is right about the existence of a problem and
wrong about its cause and its extent, which is the default this studio expects
of a finding and is not a criticism of the resident who caught it.

THE OCCLUDER IS THE PEDESTRIAN GUARD RAILING, NOT A CROWD CONTROL BARRIER.
production/specs/vignette-scene.json furniture E8_guard_railing puts a guard
rail on the EAST side, three panels of 2.000 m from x=10.0 m, height 1.000 m,
post diameter 0.050, rail 0.040, five infill bars per panel at 0.025, setback
0.25 m from the kerb face. production/specs/vignette-feet.json lines 356 to 375
name rail_post0 at x=10.0, rail_post1 at x=12.0, rail_post2 at 14.0, rail_post3
at 16.0, all at z=3.375 m on east_footway. Run 35's own verdict puts the camera
at Y=410.0 and the grate at Y=280.0, so the railing plane at Y=337.5 lies
between them, and rail_post1 stands at x=12.0, which is the grate's own x. The
railing is plainly visible along the kerb in frame 02, with a top rail and a mid
rail, in the same dark blue-grey as the bars in frame 05.

prop_crowd_control_barrier_0 CANNOT be in that frame. The same scene file places
it on the WEST side at x=22.5 m, 10.5 m up the street and across it, and every
ray in a 40 degree vertical field from that camera meets the road within about
2.7 m.

THE GRATE IS IN THE FRAME, AT THE PRINTED RECTANGLE, NEAR FRAME CENTRE. Run 35
printed grateSubjectRectFrac=0.4492/0.4792/0.5508/0.6024, which is pixels
431..529 by 259..325. Mapping the frame back through the camera the verdict
names (Y=410.0, Z=118.5, pitch -43.9, VFOV 40) puts the subject rectangle's far
edge at y=258 px and its near edge at y=325 px, which reproduces the probe's own
printed rectangle. In the image that band is a flat pale, nearly white patch
carrying a faint angular shape, crossed by one near-vertical bar with the
railing's mid rail along its upper edge. Above it, 1 to 2.7 m further off, the
carriageway renders as textured grey with red aggregate. So the honest sentence
is not "no grate": it is THE PIECE IS WHERE THE ARITHMETIC PUT IT, PART OF IT IS
BEHIND A RAILING, AND WHAT IS NOT BEHIND THE RAILING RENDERS AS A NEAR-WHITE
PATCH WITH ALMOST NO TEXTURE. Two faults, not one, and the change under review
addresses the first.

Looking is not measuring (rule 4). The pale patch is strong evidence that
something is wrong and weak evidence of what; A6 names the measurement.

A1, RESIDENT, DICTATED TEXT, BLOCKS THE COMMIT. The false identification sits
at exactly four sites, which I grepped for: WalkProbe.cpp lines 182, 846 and
1152, and production/NOW.md lines 12 to 30. Line 1152 is inside WriteFinalVerdict
and would therefore be PUBLISHED IN RUN 36's COMMITTED VERDICT as a fact. Replace
the claim at all four with:

  Run 35 aimed from row 00 and printed grateShotStatus=AIMED,
  grateRectStatus=MEASURED and walkFramesWrote=7/7 over a frame in which the
  east kerb's pedestrian guard railing (E8, posts at x=10/12/14/16 m in the
  plane z=3.375 m, one of them at the grate's own x) stands between the camera
  and the piece, and nothing asked what was in the line.

NOW.md's heading "EVERY KEY IS GREEN AND THE PHOTOGRAPH IS OF A BARRIER" becomes
"EVERY KEY IS GREEN AND A RAILING STANDS IN THE LINE". The sentence "shows a
post and a rail and no grate at all" becomes "shows the guard railing's post and
mid rail crossing the subject rectangle, and the piece itself as a near-white
patch with almost no texture". The rest of that entry stands: the z-fight reading
from run 35 IS void and must not be quoted, for the reason given and now also
because a flat near-white patch is not a surface a speckle statistic can read.

## 1. The voting population: RIGHT, for a reason the file does not give

The five subject-rectangle rays decide and the four face corners and the bounds
centre are context. UPHELD. But the reason written in the source is false and
must not be the reason of record.

THE STATED REASON IS THE MISATTRIBUTION THIS STUDIO ALREADY CORRECTED TONIGHT.
The comment says the piece is "honestly under the asphalt lip" because run 35
measured buried=40.0pct by=ground_east_carriageway. game-design/decision-2026-09
-09-the-grate-rises-flush.md, ruled hours earlier, establishes that there is no
lip: deepestMm=65.01 is the carriageway slab's AABB top, which is the ROAD CROWN
2.745 m away in z, and that record's own words are "TWO MECHANISMS, ONE NUMBER,
AND A COINCIDENCE OF VALUE WAS READ AS AN IDENTIFICATION OF CAUSE". The same
record proves the grate's top face lies IN the pitched road plane, three points
at 0.000 mm offset, and that the 40.0pct is seven AABB columns plus one column
of paint. The piece is not under a lip. It is flush.

THE RULE IS STILL RIGHT, AND THE INVARIANT IS THIS: THE RAYS THAT DECIDE MUST BE
AIMED AT THE PIXELS THE VERDICT'S OWN STATISTIC READS. The subject rectangle is
what MeasureGrateAim projects and what tools/grate-zfight.py measures; deciding
on anything else would refuse standpoints over pixels no reading depends on, or
accept standpoints over pixels it does.

Two of the five context rays also cannot vote for reasons that are structural
and hold whatever the burial number says, and these are the reasons to write
down:
- The bounds centre is inside the piece's own solid, so with the piece ignored
  it reports whatever shares that volume and can never come back clear.
- The two kerb-side face corners sit at the kerb face. The piece's AABB reaches
  z=3.000075, which the flush ruling identifies as the kerb face plane, and the
  lifted endpoint there is about 10.5 cm below the kerb top (KerbTopY 0.050
  against an endpoint at y=-0.055). No standpoint on the footway side can see a
  point at the foot of a kerb over the kerb, by construction: from row 00 the
  ray is already inside the kerb body 5 cm before it arrives.
The two crown-side face corners are reachable and would be a fair vote. They are
excluded for the invariant above and for nothing else: they are outside the
rectangle the statistic reads.

WHAT WOULD MAKE IT WRONG FOR A DIFFERENT PIECE. Two conditions, either of which
turns this from scoping into gerrymandering:
1. The subject rectangle is moved, or its inset or bias changed, AFTER a
   standpoint fails. The rectangle's position must be derived from the piece and
   its confounds before any occlusion answer exists, as the 7 cm kerb bias was.
2. The downstream statistic stops reading the same rectangle the rays decide on.
   The day grate-zfight.py reads a different region, the vote is measuring one
   thing and the verdict another.
For a piece NOT set into the ground the two populations coincide and the
distinction does not arise, which is the ordinary case; this piece is the
exception and the file must say so in those terms.

THE HONEST LIMIT, WHICH THE VERDICT DOES NOT CURRENTLY ADMIT. Five rays over a
22 cm square are a SAMPLE, not a coverage test, with 11 cm between samples. The
occluder class that actually exists here is the railing: infill bars 25 mm at
0.333 m spacing, posts 50 mm at 2.0 m spacing. From row 00 the railing plane
sits at t=0.589 of the way to the target, so a 25 mm bar casts a 42 mm shadow on
the subject plane and a 50 mm post casts 85 mm: both narrower than the 110 mm
sample spacing. Tonight the post happens to stand at x=12.0, the grate's own x,
so the centre ray hits it. THAT IS LUCK, NOT DESIGN, and a piece 1 m up the
street would pass this vote with a bar across its picture. A3 measures it.

## 2. The 1.0 cm lift: the number stands, the justification does not

NOT A BOUND NEEDING A SERIES. Nothing is compared against it, no gate reads it
and no conclusion turns on its value; it is a construction offset, the same
class as vignette-scene.json's standoff_m 0.01, which that file's own note calls
"a clearance rather than a dimension". Rule 2 governs numbers a conclusion rests
on. This one does not qualify, and inventing a series for it would be ceremony.

BUT THE REASON IN THE SOURCE IS THE SAME FALSE LIP AS SECTION 1. The comment
says one centimetre "stays well inside the recess the carriageway's lip makes
over this piece ... so the lift cannot lift a target out through the road".
There is no recess and no lip, so there is nothing for the lift to stay inside
of, and a reader who later needs to change this number would reason from a
picture of the world that is not there.

THE TRUE DERIVATION, WHICH IS BETTER THAN THE ONE GIVEN. The top face is IN the
road plane at 0.000 mm (flush ruling, three points). A ray endpoint ON that face
is therefore inside a plane it shares with an opaque neighbour and can register
that neighbour at its own endpoint, which is exactly the fault the lift exists
to avoid. Any positive lift escapes it, because the point moves into open air
ABOVE the plane rather than under any cover. The only cost of a larger lift is
that a very low obstruction could pass under the ray while still hiding the
face, and at 10 mm nothing in this street is that low. Ten millimetres is also
the clearance this project has already declared three times for exactly coplanar
opaque pairs, cited in the flush ruling: the road decals sit 10 mm proud.

A2, RESIDENT, DICTATED TEXT, BLOCKS THE COMMIT. Replace the lift's justifying
sentence with:

  ONE CENTIMETRE, AND WHAT IT IS A CLEARANCE FROM. This piece's top face lies
  IN the pitched road plane, measured at 0.000 mm offset at three points
  (decision-2026-09-09-the-grate-rises-flush.md), so a ray ending exactly on the
  face ends inside a plane it shares with an opaque neighbour and can register
  that neighbour at its own endpoint. Any positive lift escapes that plane into
  open air; 10 mm is the clearance this project already declares for coplanar
  opaque pairs (vignette-scene.json standoff_m 0.01, "a clearance rather than a
  dimension"). It is not a bound and nothing is compared against it.

And print it, which the verdict currently does not: grateRayLiftCm=1.0 with
grateRayLiftStat=clearance-above-the-placed-top-face/not-a-bound/the-face-is-
coplanar-with-the-road-plane-at-0.000mm. A reader who sees "clear" cannot
otherwise tell what height was asked about. Fold this into A3's edit.

## 3. First clear wins: the right SHAPE, an incomplete PREDICATE

The shape is right and I would not change it tonight. It is deterministic, it is
printed row by row with every blocker named, the incumbent is row 00 so a clear
incumbent reproduces run 35's framing exactly, and there is no tunable number in
it. Nothing here is a threshold that could be moved to make red go away.

THE PREDICATE IS INCOMPLETE, AND I EXPECT IT TO COST THE TIE READING. A clear
line is necessary and not sufficient, because this run has a second requirement
the selection never consults: MeasureGrateAim's control rectangle, 80 cm toward
the crown, must also be in frame, or grate-zfight.py has no denominator. Computed
in this seat from the bounds run 35 printed, with heights in the scene's own y
datum so they can be compared against the posts:

- Rows 00 and 01 stand behind the railing plane, at Y=410 and Y=365. Their
  centre rays cross that plane at y=38.9 cm and y=65.0 cm, inside the posts'
  5.6 to 105.6 cm band (foot at 0.05625 m, height 1.000 m), in the plane x=1200
  where rail_post1 stands. I expect both to be refused with a rail piece named.
- Row 02 stands at Y=325, which is between the railing at 337.5 and the kerb
  face at 300, so the railing is BEHIND it and its line is clear. It will be
  taken. Its pitch to the subject is 70.2 degrees down; the control point at
  Y=200 sits at 45 degrees, which is 25.2 degrees off the camera axis against a
  20 degree half-field. THE CONTROL RECTANGLE WILL BE OFF FRAME, by about five
  degrees, and grateRectStatus=OFF-FRAME.
- Rows 03 and 04, the obliques, are the ones I would expect to frame both: pitch
  44.9 degrees, control centre about 23.2 degrees off in yaw against a 32.9
  degree half-field and 9.8 degrees off in pitch against 20.

I WILL NOT REORDER THE TABLE ON THAT ARITHMETIC. It is unmeasured, it is mine,
and a selection rule set from a director's trigonometry is the same failure as a
threshold set without a series. The instrument rule is to ship the printer, read
the run, then set the number. A3 ships the printer.

## 4. The workflow denominator: the deletion was RIGHT

Deleting the invented denominator was right, and a step that cannot know the
asked count must not print one. The standing form is: A STEP MAY ONLY PUBLISH
DENOMINATORS IT CAN SEE. This step can see how many files it found and how many
it copied; it cannot see how many the probe asked for, and the probe prints that
itself as walkFramesRequested. Reporting copied over found, naming the statistic
in the value, and pointing at the probe's own line as the authority is the right
answer to the question as put. Printing nothing at all would be worse: it would
lose the one fact only this step knows, which is whether the files it found ever
reached the commit.

The resident was inside its own lane. The do-not-touch list covers art work; this
is the step that carries the evidence channel, the edit removes a false claim
rather than adding one, and it was escalated because it changes what a landed
verdict says, which is the correct trigger.

A4, RESIDENT, BLOCKS NEITHER. The new denominator can double-count. $frameDirs
is @($proj, $binDir, $PWD\ue-probe) at line 1182, and $proj is set at line 438
to Join-Path $PWD "ue-probe" whenever the run falls back to the uncooked build
output, so the same directory would be scanned twice: $copied stays 7 because
the second pass finds the destination present, while $found reaches 14, and
walkFramesCollected=7/14 would read as half the frames lost when nothing was
lost. Tonight's runs are packaged (production/d1-probe/ue-build.txt line 21,
ranBinary=packaged) so the three paths are distinct and it does not bite yet.
Dedupe the list, or count distinct file NAMES, and say in the value which it is.
I checked the stale-file half and it is sound: lines 1150 to 1157 delete the
tracked copies before the run, so a run that writes nothing cannot republish
last night's frames under its own name.

## 5. A3: what run 36 must print, and the predictions it tests

A3, TIER-3 BUILDER, BLOCKS THE DISPATCH. Printing only. No change to the vote,
to the selection, to the candidate table or to any status word. Constructs
already used in this file only. If the diff touches anything else, refuse it and
dispatch without it.

(a) PER CANDIDATE, THE FRAMING ANGLES, from the control point MeasureGrateAim
already uses, FVector(C.X, C.Y - kGrateCtrlAcrossCm, TopZ):
grateCandCtrlOffPitchDeg, grateCandCtrlOffYawDeg, against grateCandHalfVDeg=20.0
and grateCandHalfHDeg=32.9, with
grateCandFramingStat=angle-to-the-control-rectangles-CENTRE-from-the-camera-
axis/not-a-rect-in-frame-test/printed-so-the-selection-rule-can-be-set-from-a-
series. This is the series the predicate needs and it is measured, not argued.

(b) PER CANDIDATE, A DENSE COVERAGE COUNT over the same subject rectangle: a 9
by 9 grid, 2.75 cm spacing, counted and NOT voted, as
grateCandSubjGridClear=N/81 with grateCandSubjGridSpacingCm=2.75 and the first
blocked cell's blocker named. NINE BECAUSE THE SPACING MUST BEAT THE OCCLUDER,
not because it is a round number: the narrowest railing member is a 25 mm infill
bar, which projects to about 42 mm on the subject plane from row 00's geometry,
and 27.5 mm resolves it. Its ray budget is counted and printed separately from
grateRaysTraced so neither number borrows the other's denominator.

(c) grateRayLiftCm and its stat, per A2.

WHAT RUN 36 THEN SETTLES, AND THE PREDICTIONS IT CAN FALSIFY. I have written my
expectations above so the run judges them rather than the other way round:
rows 00 and 01 refused with a RAIL piece named, not prop_crowd_control_barrier_0
(if the barrier is named, section 0 is wrong and this ruling is wrong with it);
row 02 taken; its control rectangle off frame; and the 5-ray vote agreeing with
the 81-cell coverage on the chosen row, or not, which is the whole question of
whether the vote is sampled or measured.

## 6. Carried forward and queued, none of it blocking

A5, RESIDENT OR A TOOL BUILDER, BLOCKS NEITHER. Three items in
tools/grate-zfight.py, all local and none needing a dispatch:
(i) rects_from_verdict reads grateSubjectRectFrac and grateControlRectFrac
without ever reading grateRectStatus. An OFF-FRAME pair gets clamped by rect_px
and then usually refused for a mismatched area, which is a refusal with the
wrong reason on it. Read the status; refuse unless MEASURED; name the true cause.
(ii) The docstring's claim that the top face is "EXACTLY COINCIDENT with the
channel and carriageway top faces over about 0.16 square metres" is the same
overreach amendment 2 of decision-2026-09-09-grate-camera-and-zfight.md already
narrowed: the rectangle spans z 2.76 to 2.98, wholly inside the channel course,
so the CHANNEL is what this measures and the carriageway edge is unmeasured.
(iii) Amendment 4 of that same ruling, the rect_px rounding snap, is STILL NOT
APPLIED. I read the file this session: rect_px rounds the two rectangles
independently and measure() refuses when the integer sizes differ. A new
standpoint changes both rectangles' positions, so the odds change with it. A
ruling that lives only in a record nobody carries out decays exactly like a
preference.

A6, QUEUE ITEM WITH A NAME, BLOCKS NEITHER: "the near road renders near-white".
The pale patch in section 0 is the piece and its channel at 1.2 to 1.8 m, while
the carriageway at 2 to 2.7 m in the same frame carries texture. Occlusion does
not explain it and this change does not address it. THE CHEAPEST DECISIVE
MEASUREMENT NEEDS NO DISPATCH: run a Pillow read on the two committed frames
using the rectangles run 35 already printed, and print mean, min and max luma
inside the subject rectangle and inside the control rectangle, each with its
examined count. Three outcomes with different next actions: a blown near field
(exposure or fog), an untextured material on the grate or the channel, or a
correct render of a small metal plate that simply reads pale at this angle. Do
that BEFORE proposing a mechanism, which is the standing ruling on silent
channels applied to a silent picture.

## The ladder, asked at close

Best available or first working? First working, and the next rung is named: the
selection rule that weighs the PICTURE, not just the line, set from A3's printed
series rather than from anybody's trigonometry. Rung after that, from the
earlier ruling and still open: a control rectangle displaced along world X so
that distance and grazing angle cancel between subject and control.

## What the Producer may say, and what it may not

May say: the piece is placed, collidable, flush and IN the frame the probe took;
what stood in the line is the street's own guard railing; the probe now traces
before it shoots and refuses with the blocker named. May NOT say: that run 35
photographed a crowd control barrier, that the grate was absent from the frame,
or anything at all about a depth-test tie. The run 35 tie reading stays void.

<!--RULING spawn=2026-09-09T03:55:58Z-->
