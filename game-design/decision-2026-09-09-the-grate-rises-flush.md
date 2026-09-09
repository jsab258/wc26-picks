# The grate rises flush: queue 162 lands, and the two clip risks become measurements

STATUS: LIVE, verified 2026-09-09.
Decided 2026-09-09 by the studio director spawned at 02:00:20Z, on the builder's
change to `StreetVignette.cs`, `vignette-scene.json`, `vignette-pieces.json`,
`CoreTests/Program.cs` and `VignetteSpec.h`, all uncommitted at the time of
writing. `director_cadence` refused the commit for want of a ruling newer than
reference commit 7d926d1b. This record is that ruling.

VERDICT: LAND WITH AMENDMENTS. Eight amendments, numbered in section 6. ONE of
them blocks the dispatch (A1) and NONE blocks the commit. The two clip risks go
to the run as measurements and not as blockers, for the reasons in sections 1
and 2.

PREMISE CHECK FIRST, because that is this chair's job. A gully grate whose top
face is the running surface of a British carriageway is consistent with
CLAUDE.md section 0 and with canon: late-analog British port town, wet overcast
grimy Britain, working window 1988 to 1992. Nothing here cites a retired bar.
No new tool, no new weights, no licence question: `drainage_grate_01` is a held
base-mesh prop already in the tree. The change serves Meridian Test item 1 (do
not bounce off the visuals) through the prop route Jafar named this grate the
accepting case for. No premise conflict, and the premise section is not stale.

## 0. What I checked myself, rather than accepted

Rule 1 binds the director too, so the two numbers this whole change turns on
were re-derived here off the committed files and not taken from the brief.

THE PLACED ROW IS RIGHT. From `vignette-scene.json` alone: HalfWidth 3.0,
crossfall 0.025, channel width 0.255, dish 0.030, grate `z_from_kerb_face_m`
-0.2 so cz = 2.8, thickness 0.015. `GroundAt(12, 2.8)` lands in the channel
branch (|z| 2.8 is past 2.745 and inside 3.0) and returns -0.025 x 2.8 - 0.030 =
-0.100. The set_in branch adds the dish back, giving the running surface -0.070,
and drops half a thickness down the piece's own normal, 0.0075 / cos(atan 0.025)
= 0.00750234. cy = -0.07750234, which is the committed -0.077502 to the file's
six decimals. pitch = atan(0.025) in degrees = 1.4320963, committed as
1.432096. Both emitted numbers reproduce.

THE PRINTED SERIES IS RIGHT AT ALL THREE POINTS. The top face centre sits at
(y -0.0700047, z 2.8001874), and -0.025 x 2.8001874 = -0.0700047. The face's
half length in z is 0.19995 cos = 0.1998876, giving ends at z 2.6002999 with
y -0.0650075 and z 3.0000750 with y -0.0750019; the plane at those z reads
-0.0650075 and -0.0750019. Three points, offset 0.000 mm at each, which is what
the test prints. The face is IN the plane, not near it.

## 1. Z-fighting: the refusal is right about `y_m`, wrong about "no derivation"

THE BUILDER RAISED THIS AGAINST ITSELF AND THAT IS CREDITED. The top face is
now exactly coincident with the carriageway and channel top faces over 0.1599
square metres, both opaque solids, nothing cutting a hole.

THE REFUSAL TO PUT A NUMBER IN `y_m` IS UPHELD, for a better reason than the one
given. A number whose only job is to win a depth test is not a dimension of the
world, and this repository already says so IN THE FILE THE CHANGE EDITS.
`production/specs/vignette-scene.json` line 537 carries `"standoff_m": 0.01`
and its note calls it, in as many words, "a clearance rather than a dimension",
with a pedigree: `DecalLayer.cs` has placed the town's road decals 5 mm proud of
the tarmac for 78 landed runs at `decalsBuried=0`, and 10 mm is that with room
for camber under a 3 m quad. Folding such a number into `y_m` would make the
street spec state something false about the street. So it stays out of `y_m`.

BUT "EVERY CANDIDATE WOULD BE A NUMBER WITH NO DERIVATION" IS NOT TRUE, and the
correction matters because it changes what happens after the run. This project
has met an exactly coplanar opaque pair three times before and resolved every
one with a declared clearance:

    vignette-scene.json:538     decals sit 10 mm proud "so it wins the depth
                                test rather than fighting it", from 5 mm
                                measured over 78 landed runs
    WorldBuilder.cs:4217        the reference ground sits 4 cm BELOW the town's
                                ground "so the two can never z-fight"
    VignetteShot.cpp:724        "A CO-PLANAR QUAD Z-FIGHTS WITH THE SURFACE
                                UNDER IT", already written in this probe

So whether an exact tie fights is not an open question here. It was answered
three times and the answer is yes. What is open is this piece's MAGNITUDE and
DIRECTION, and only one of those is still free: DIRECTION IS ALREADY DECIDED BY
THIS CHANGE. Proud is a trip lip, and removing a 5 mm lip is the reason the
pitch is in the fix at all, so any clearance here is DOWNWARD, which is also how
water enters a grating. MAGNITUDE is a bound, rule 2 owns it, and the series it
must be read off does not exist yet. That is why it is not set tonight and not
guessed tonight.

THE RUN IS THEREFORE THE ANSWER, and it must come back with numbers. What it
must print, in the order of what it costs:

1. `setInFlushOffsetMm` FROM PLACED BOUNDS, at the same three points the
   CoreTests series uses. Every flush number in this change is today arithmetic
   on a file; no placed reading of this grate at the surface has ever existed.
   The probe already holds placed bounds and already has `PitchedSpanAtXZ`, so
   this is the cheap one and it is the one that turns the claim into evidence.
2. `propBurialSubject` carrying `yellow_east_0` in its cover list with its own
   depth. That is section 2's measurement and the instrument already computes
   it.
3. THE TIE ITSELF, which no engine key can answer: `VignetteSpec.h` line 884
   already says it, an AABB question is not an occlusion question and only a
   frame answers that one. The cheapest decisive reading that needs no new
   engine code is a pass over the walk sequence frames the run already writes,
   with Pillow, which `tools/clip-from-frames.py` already opens every one of.
   Over TWO rectangles of equal pixel area at equal range, one containing the
   grate and one on plain carriageway, print for each: pixels examined, which is
   the denominator; the count of four-neighbour transitions between the frame's
   two dominant clusters inside the rectangle, which is speckle density; and the
   count of pixels that swap cluster between consecutive frames, which is
   flicker density. THE VERDICT IS THE COMPARISON OF THE TWO RECTANGLES IN THE
   SAME FRAMES, so no new bound is set tonight and the control rectangle is the
   denominator rule 3b asks for. A grating alternates metal and void at its bar
   pitch and the bars do not move when the camera does; a depth tie alternates
   at the pixel pitch and moves with every frame.

WHAT MAKES 3 NOT DECISIVE, said now rather than discovered later: the rectangle
has to be located, and that needs the camera pose. The pose is already published
in the walk verdict (`walkCameraStartXYZcm`, `walkCameraEndXYZcm`, eye height,
yaw, pitch, fov), so the rectangle is computable in the tested Python layer from
published numbers and no projection code ships unrun in the top layer. IF THAT
PASS IS NOT WRITTEN, 3 IS NOT TAKEN, and then the Producer says the tie is
unresolved and names the rung. It does not get offered as a finished frame and
nobody squints at it. A picture is strong evidence that something is wrong and
weak evidence of what or why.

## 2. The double yellow over the gully: a real-world fault, not a blocker

THE ARITHMETIC, off `vignette-pieces.json`. `yellow_east_0` is y -0.0615,
sy 0.012, z 2.7, sz 0.1, pitch 1.432096, so it spans z 2.65 to 2.75. The grate's
footprint spans 2.5999 to 3.0001. The band crosses 100.0 mm of the grate's
399.9 mm, which is 25.0 percent of its footprint. IT IS ONE STRIPE AND NOT TWO:
`yellow_east_1` sits at z 2.5 and spans 2.45 to 2.55, clear of the grate
entirely.

IT DOES NOT INTERSECT THE GRATE, and that is the difference between ugly and
broken. The band's underside at the crossing is 5.6 um ABOVE the grate's top
face, so the 12 mm band LIES ON the grate the way paint lies on metal. No
interpenetration, no clipping, nothing poking through. Before tonight the band
cleared a buried grate; now it rests on a flush one. That is the whole of the
change in this relationship.

IT IS A PRE-EXISTING FAULT GAINING A SECOND SITE, not a new one. A5 lays two
continuous 42 m bands and nothing interrupts them for ironwork or for the
crossover, and the scene note already carries the crossover break as a named
next step. This is that same gap at a second x.

WHETHER A BRITISH DOUBLE YELLOW BREAKS AT A GULLY IS NOT MINE TO RULE. It is
exactly the `trade_standard` class the scene file defines: recalled, not
verifiable from this container, and settled by an eye check on a committed still
by someone who has stood on a British pavement. That is Jafar. My judgement,
flagged as judgement and not as a fact: paint does not key to cast iron and the
line should break at ironwork. I am not changing the street on my judgement
tonight.

IT DOES NOT BLOCK THE DISPATCH. It touches no geometry in this change, the piece
count is unchanged at 593, and it is ALREADY MEASURED by the instrument that is
about to run: the cover profile names the band and prints its depth (10.75 mm by
the AABB predicate, 10.26 mm pitch-aware, and `VignetteSpec.h` line 863 already
carries the 10.26 with the words "crosses the grate and does not break at it").
A fault that the running instrument names and numbers is not a reason to hold
the run that names it.

THE CLIP MAY BE OFFERED AS JAFAR'S ITEM 2, WITH THE STRIPE NAMED. Item 2 is four
halves: the grate as a real mesh, with collision, in a walk clip, visible. A
stripe across a quarter of it falsifies none of them. Offering it SILENTLY would
be the fault. So the Producer's note carries the stripe and its number, 100 mm
of 400, and Jafar reads it in the note rather than finding it in the frame.

## 3. The prescribed number was wrong, and the cause is now closed

THE EMITTER IS RIGHT. Section 0 reproduces -0.077502 from the scene file's own
crossfall, dish and thickness, with nothing typed in. The predecessor's -0.0776
was 0.098 mm low. The ruling was wrong and the emitter corrected it.

AND NOW THE PART THE BRIEF ASKS PLAINLY ABOUT: IS THE 0.09 mm UNDERSTOOD, OR IS
A COINCIDENCE BEING REUSED AS AN EXPLANATION. It is understood, it closes to
0.3 um, and THE EXPLANATION IN QUEUE 162 IS THE WRONG ONE WHILE THE EXPLANATION
IN `VignetteSpec.h` IS THE RIGHT ONE. The predecessor's plane was written as
y(z) = -0.034313 - 0.025005 (z - 1.368751), which gives -0.070101 at z 2.8
against the true -0.0700004. Two errors, and they are unequal:

    the anchor's z   -0.034313 is the carriageway slab's top-face height, and
                     it is correct, but that point's z is 1.368751 + 0.15 sin
                     = 1.372500, not 1.368751. Going up a tilted slab's own
                     normal moves the point in z as well as in y. Anchoring at
                     the centre's z under-reads the plane by
                     0.15 x sin(1.432096 deg) x 0.025 = 0.0937 mm
    the slope        tan(1.432096 deg) is 0.0250000, not 0.025005. Over the
                     1.4312 m run that is 0.0072 mm

    0.0937 + 0.0072 = 0.1009 mm, against the observed 0.1006 mm.
    Residual 0.3 um, which is the piece list's six-decimal rounding.

So 93 percent of it is ONE specific, nameable, repeatable mistake and 7 percent
is a tan slip. QUEUE 162 CREDITS THE 7 PERCENT AND CALLS IT THE CAUSE. The 93
percent is already written correctly in `VignetteSpec.h` lines 867 to 871, "the
pitch shifts that face 3.75 mm in z, which is 0.09 mm of y". Two records of one
cause, one right and one wrong, and the wrong one is the record the decision
card quotes. That is A2.

THE GENERALISATION, because it will recur and because recurring is how it got
reused. To read a tilted slab's top-face level off a committed centre row you
must move BOTH coordinates up the normal; reading it at the centre's z
under-reads by halfThickness x sin(fall) x slope. That is 0.0937 mm for every
0.30 m slab in this street. The claim in queue 162 that the same slip explains
three earlier disagreements is now PROVEN FOR THIS ONE and unchecked for the
other two; A2 either carries their arithmetic or drops the count to one.

## 4. Forty percent buried over a flush piece: fit for one more run

I reproduced the headline rather than arguing with it, and reproducing it turned
the apparent contradiction into the measurement section 2 needed.

40.0pct IS 160 OF 400 CELLS, WHICH IS 8 OF 20 z-COLUMNS, AND THE EIGHTH COLUMN
IS THE YELLOW PAINT. The grid is 20 by 20 over the prop's own AABB footprint, so
the columns sit at z 2.609929 + IZ x 0.020007. The carriageway slab's AABB ends
at z 2.745000, which covers IZ 0 to 6, seven columns. `yellow_east_0`'s AABB
spans 2.649866 to 2.750134 and straddles the grate's top, which covers IZ 2 to
7, and IZ 7 at z 2.749981 is covered BY THE PAINT ALONE. Seven columns plus one
is eight, and 8 of 20 is 40.0 percent exactly. Without the stripe the headline
would read 35.0pct. The instrument is not confused; it is reporting the stripe.

65.01 mm IS THE ROAD CROWN, AND THE BUILDER'S EXPLANATION OF IT IS RIGHT ABOUT
THE SERIES AND WRONG ABOUT THE HEADLINE. On the subject row, `deepestMm` is the
carriageway slab's AABB top, which is the crown at y -0.00000035, 2.745 m away
in z: 65.0068 mm above the grate's AABB top. The 75 um kerb sliver CANNOT enter
that tally at all, because the highest cell centre is z 2.990071 and never
reaches the kerb face at z 3.000. The sliver enters the SERIES, which samples
`P.MaxZ` = 3.000075 as a footprint-edge row. Both read 65.01 mm because both
covers top out at exactly y = 0.000: the carriageway's AABB top is the crown by
construction, and the recessed kerb top is KerbTopY 0.050 minus recess 0.050.
TWO MECHANISMS, ONE NUMBER, AND A COINCIDENCE OF VALUE WAS READ AS AN
IDENTIFICATION OF CAUSE. That is the same error class as section 3, twice in one
night, which is why both are written down here.

THE 0.01 mm AT THE WEST EDGE IS AN IDENTITY, NOT AN ARTEFACT TO TOLERATE. The
AABB reaches 0.37488 mm further west than the tilted top face's own corner, and
the plane rises 0.37488 x 0.025 = 9.372 um over that distance. The residual IS
the overhang times the crossfall, exactly. Nothing is wrong.

FIT TO SHIP ONE MORE RUN: YES. The instrument already ships both halves at the
same points at the same instant, already prints the overstatement column,
already declares its statistic and its sampler resolution in the value
(`a-gap-narrower-than-one-cell-is-invisible-here`), and already prints
`cells=400` as the denominator. A headline of 40.0pct beside a series reading
nothing-overhead at 13 of 23 rows is not a broken instrument; it is two named
predicates at different resolutions. BUT IT IS MISREADABLE, and it has already
been misread twice tonight: the decision card quotes `buried=100.0pct` with no
statistic named, and 65.01 was misattributed. A4 fixes the row, not the number.

THE WORD `buried` STAYS. It is wrong for a flush plate and right for the paint
on top of it, and renaming a key breaks every committed verdict that carries it.
The fix is the paired figure, not the rename.

THE LADDER, so nothing closes blank. Rung 1 is AABB against AABB, 65.01 mm.
Rung 2 is AABB subject against a pitched cover, 10.26 mm, which is what
`ReadCoverProfile` prints today. Rung 3 is pitched against pitched, 0.000 mm,
which ALREADY EXISTS in `CoreTests` and does not exist in the C++ profile
because the profile sets `C.PropTopM = P.MaxY` for both halves and so overstates
by up to 5.00 mm on a pitched subject. Rung 4 is a downward trace at the cell,
the engine's, and it is queue 163's sweep. Four rungs, three built, none blank.

## 5. What the change does and what proves it

The emitter: `DishAt(x, side)` beside `KerbTopAt`, two call sites, `GroundAt`
and the set_in branch. `GroundAt`'s arithmetic is unchanged and THE PIECE LIST
PROVES IT: 593 rows before and after, 592 of them byte-identical, the one
difference being line 489 which is the grate. `vignette-feet.json` is
byte-identical, which is the right result because a set_in prop is deliberately
not foot-probed and the exemption pre-dates this change. That is rule 6
satisfied by artifact rather than by assertion.

The guard: a set_in prop over anything but the carriageway or the channel throws
by name. Rule 5b is satisfied in BOTH directions, which is rare and is credited:
the accepting case is the live grate at offset 0.000 mm, the PLANTED case strips
the pitch off the same prop and reads the 5.001 mm lip against an expected
4.999, and the REJECTING case moves the grate 1.2 m out onto the footway and
requires the error message to name the surface. The bound 0.01 mm is the file's
six-decimal quantisation and not a tolerance, read off a printed series, 500
times under the lip it exists to catch. CoreTests 4291 to 4296, vignette-spec
185 checks 0 failures either side.

The prose: one line of `vignette-scene.json` said "same y" and the change
falsified it, so it is rewritten with the amendment dated in place. The three
`VignetteSpec.h` sentences quoted the pre-raise street as present fact and are
now corrected; that file's diff is comments only.

## 6. The amendments

A1. THE DISPATCH'S RUN-33 GRATE PARAGRAPH IS FALSIFIED BY THIS COMMIT AND MUST
NOT BE REUSED FOR RUN 34. `production/d1-probe/DISPATCH` lines 598 to 608 say "A
walk clip of this grate is NOT Jafar's item 2 and must not be reported as it"
and "No part of the grate reaches the surface ... no frame can show it". Both
describe the pre-fix street. Run 34's entry states instead that the grate is
flush by arithmetic, that no PLACED reading of it at the surface has ever
existed and producing the first one is this run's job, and that the clip may be
offered as item 2 carrying the two named conditions from sections 1 and 2.
Resident applies. BLOCKS THE DISPATCH. Does not block the commit.

A2. QUEUE 162 CARRIES THE WRONG CAUSE FOR THE 0.098 mm. Replace with section 3's
arithmetic: 0.0937 mm from anchoring a tilted slab's top face at the piece's own
z, 0.0072 mm from tan written as 0.025005, 0.1009 against 0.1006 observed,
residual 0.3 um. Either carry the arithmetic for the two other claimed instances
or reduce the claim to one. Resident applies. Blocks neither.

A3. "20.00 mm AT THE WEST EDGE AND 10.25 mm AT THE EAST" IS ONE PHRASE OVER TWO
STATISTICS, in queue 162, in the decision card and in the CoreTests comment at
line 19714. The footprint edges are 20.00 and 10.00; the extreme cell centres
are 19.75 and 10.25. Pick one population per sentence. The DISPATCH already gets
this right at lines 600 to 601 and is the model. Resident applies. Blocks
neither.

A4. `propBurialSubject` MUST CARRY THE PITCH-AWARE DEPTH BESIDE THE AABB DEPTH
ON ITS OWN ROW, with the cover named at each, so a reader who never opens the
series cannot take 65.01 mm as cover. They are not one number twice: move the
pitch and the AABB figure moves while the pitched one does not. New queue item,
builder, next run. Blocks neither.

A5. RECORD THAT THE TWO 65.01 mm READINGS ARE DIFFERENT MECHANISMS, per section
4, in `VignetteSpec.h` beside the existing note. Without it the next reader
takes one explanation as covering both. Builder, with A4. Blocks neither.

A6. RECORD THE 75 um OVERHANG AS ACCEPTED, WITH ITS MAGNITUDE. The pitch shifts
the top face 187 um in +z, which puts its east corner 75 um past the kerb face
and so 75 um inside the gully kerb block. It is six times smaller than the
0.469 mm slab-to-slab overlap this street already carries and it is invisible,
but it is the source of the 65.01 mm series row and must be named or it will be
rediscovered as a bug. Resident, in queue 162. Blocks neither.

A7. THE Z-FIGHT GOES TO THE RUN AS THE THREE PRINTED READINGS OF SECTION 1, and
if reading 3 is not written then the Producer reports the tie as unresolved and
names the rung rather than offering the frame as finished. Builder for 1 and 2,
Producer for the reporting rule. Blocks neither.

A8. THE set_in GUARD IS CENTRE-ONLY AND ITS SCOPE MUST SAY SO. It reads the edge
`GroundAt` returns at the prop's centre, so a set_in prop whose centre is over
the channel and whose footprint hangs over the kerb passes, which is exactly
what this grate does by 75 um. Since a set_in prop is deliberately not
foot-probed, this is its only footprint check. New queue item, builder. Blocks
neither.

## 7. Why this lands rather than waits

The alternative to landing was to hold the commit for a derived clearance, and
holding would have cost the clip. It would also have been wrong on its own
terms: the clearance is not a world dimension, so it does not belong in the row
this commit changes, and its magnitude needs a series nobody has printed. Rule 2
forbids setting it tonight and section 1 names what prints the series.

The two clip risks are now measurements with named keys and named denominators
rather than opinions, and the instrument that will report them is already
running. That is the whole difference between a night that stopped one step
short and a night that landed.

QUALITY LADDER AT CLOSE. Not one aspect closes blank. The placement's next rung
is the first placed reading of a flush grate, then the clearance. The
instrument's next rung is pitched against pitched in the C++ profile, then queue
163's downward trace. The street's paint has its next rung in the break at
ironwork, one named step with two sites now. And option B on the card, cutting
the ground at the gully, is deferred and not dead; if Jafar rules B, A is two
numbers to revert, exactly as the card says.

<!--RULING spawn=2026-09-09T02:00:20Z-->
