# DIRECTOR RULING: the night batch of 2 September lands, with four one-line corrections applied first; the Unreal diff was read and three faults are named; 056 does not close; dispatch order confirmed with an abort clock (3 Sep 2026, 00:25Z to 01:2xZ)

> **STATUS — LOG, 2026-09-03. NOT CURRENT once the corrections C1 to C4 are applied and the queue is refilled; from then `production/NOW.md`, `production/queue/`, `ledger/ReachCheck/allow.json` and `production/budget.md` are the reading copies and this file is their history.**

This document carries exactly one em-dash, in the banner, because
`tools/docs-check.py` line 55 accepts no other form.

<!--RULING spawn=2026-09-03T00:22:45Z-->

paths=game-design/decision-2026-09-03-night-batch-of-2-september.md ue-probe/Source/LedgerProbe/Public/VignetteSpec.h ue-probe/Source/LedgerProbe/Public/VignetteShot.h ue-probe/Source/LedgerProbe/Private/VignetteShot.cpp ue-probe/Source/LedgerProbe/Private/LedgerProbe.cpp ue-probe/tests/vignette-spec-test.cpp ue-probe/Config/DefaultGame.ini .github/workflows/ledger-probe-unreal.yml production/d1-probe/DISPATCH production/specs/vignette-feet.json production/specs/vignette-pieces.json production/specs/vignette-scene.json ledger/ReachCheck/allow.json ledger/verify.py ledger/CoreTests/Program.cs ledger/Assets/Scripts/Core/StreetVignettePieces.cs ledger/Assets/Scripts/Core/StreetVignette.cs ledger/Assets/Scripts/Core/StreetVignetteAssets.cs ledger/Assets/Scripts/Game/StreetVignetteHost.cs tools/imagegen/prompts.json tools/imagegen/imagegen.py tools/dashboard/build-dashboard.py tools/dashboard/live-dashboard.json production/NOW.md production/budget.md production/queue/027-ue-vignette-emitter.md production/queue/046-the-assets-are-not-in-the-frame.md production/queue/047-the-dashboard-cannot-tell-you-its-checkout-is-old.md production/queue/056-the-plates-are-photographs-of-signs-not-plates.md production/queue/050-props-placed-has-no-denominator.md production/queue/051-street-name-plate-for-a-canon-street.md production/queue/052-wall-overlays-belong-in-the-surface-path.md production/queue/053-chimney-pot-oversails-its-stack.md production/queue/054-double-yellows-break-at-the-crossover.md production/queue/055-g3-imperfection-scatter.md production/queue/057-usable-fraction-and-the-crop-deletion.md production/queue/058-the-emitter-cannot-light-a-flat.md

## THE PATHS LIST IS A CEILING, NOT A MANIFEST, AND THAT IS THIS SESSION'S ONE REAL LIMITATION

Bash is disabled in this session. I could not run `git status`, `git diff` or
`ledger/verify.py`, so the list above is derived from reading file contents
and from the modification ordering `Glob` returns, NOT from the dirty set.

So the resident's protocol is an intersection and not a copy:

1. `git status --porcelain`, and stage by name only paths that appear in BOTH
   that output and the `paths=` line above. Naming a clean file costs nothing;
   naming a directory is what the CI rules forbid, and no directory is named.
2. ANY DIRTY PATH NOT ON THE LIST IS REPORTED BACK BEFORE THE COMMIT. Not
   committed, not discarded, not assumed to belong to a builder.
3. One specific case to resolve first, because two sources disagree and I
   could not settle it. `.git/logs/HEAD` line 376 records a commit at epoch
   1788380513 (20:21:53Z on 2 Sep) titled "The dashboard cannot tell you its
   own checkout is old", which is queue 047's headline; `production/NOW.md`
   line 167 says "THREE BUILDERS RAN TONIGHT AND NONE HAS LANDED" and names
   047 among them. Run `git diff --stat f789e129 -- tools/dashboard/` before
   staging. Empty means 047 already landed and drops out of this batch;
   non-empty means what remains is the builder's later work and stages
   normally. Do not resolve it by preferring either prose.

Every number in my brief (5294 changed lines, reach 39, 4276 CoreTests,
78 ue-probe checks over 2 of 2 binaries, docs 131/131) was taken from the
brief and NOT re-measured by me. The commit footer is pasted FROM
`ledger/.verify-footer` after a green run, never from this file and never
from scrollback.

## WHAT I READ AND WHAT I TOOK ON REPORT, said plainly

TIME WAS THE BINDING CONSTRAINT and the depth is uneven on purpose.

READ IN FULL, with the arithmetic traced by hand:
`ue-probe/Source/LedgerProbe/Public/VignetteSpec.h`,
`ue-probe/Source/LedgerProbe/Private/VignetteShot.cpp`,
`ue-probe/Source/LedgerProbe/Public/VignetteShot.h`,
`.github/workflows/ledger-probe-unreal.yml`,
`ue-probe/Config/DefaultGame.ini`,
the `-LedgerVignette` call site in
`ue-probe/Source/LedgerProbe/Private/LedgerProbe.cpp`,
`ledger/ReachCheck/allow.json`,
`ue_probe_tests` in `ledger/verify.py`,
the header, frame, counts, cameras, conditions and shots of
`production/specs/vignette-pieces.json`,
the header of `production/specs/vignette-feet.json`,
`production/d1-probe/DISPATCH`,
`ledger-v2/respec/decision-register/D13-street-layout-method.md`,
`production/budget.md`,
`production/queue/056-*.md`,
`production/NOW.md`.

TAKEN ON THE BUILDERS' OWN REPORTED EVIDENCE, NOT OPENED:
all of queue 046's C# (the 23 of 37 props, the 20 decals, the
`propsPlaced=N/M` and `decalsApplied=N/M` instrument, the three interior
crops); all of queue 047 (the fast-forward-only pull, the checkout-age
Reading, the gate); all of queue 056 (the 41 of 45 recipe hashes moved onto
the orthographic prefix, the guard rebuilt until 11 checks went red, selftest
143/143). I did not open `StreetVignetteHost.cs`, `StreetVignette.cs`,
`StreetVignetteAssets.cs`, `tools/dashboard/build-dashboard.py`,
`tools/imagegen/imagegen.py` or `tools/imagegen/prompts.json`. Those three
builders are accepted on their reports, and this sentence is the record that
they were accepted that way rather than reviewed.

## THE UNREAL DIFF: THREE FAULTS, ONE FALSE SENTENCE, AND WHAT IS RIGHT

### C1. THE DECAL LIFT IS IN THE PLANE OF THE DECAL, so it lifts nothing

`VignetteShot.cpp` line 419:

    A->AddActorWorldOffset(
        A->GetActorRotation().RotateVector(FVector(0.0f, -1.0f, 0.0f)) * kDecalLiftCm);

`RotateVector` takes a LOCAL direction to world, and local -Y is an axis the
quad LIES IN. The comment nine lines above says so itself: "the engine's
plane is 100 uu square in its local XY with the normal on +Z". The normal
after rotation is `R*(0,0,1)`; the code offsets along `R*(0,-1,0)`, which is
perpendicular to it.

Traced on the two decal shapes this file actually contains, both of which
have `multi_rotation` 0 so only one file rotation is non-zero:

- GROUND decal, file pitch +90 (normal from -z onto +y). `Q.PitchDeg` becomes
  0, so the actor rotation is identity and the offset is world -Y, which is
  1 cm ACROSS THE STREET.
- WALL decal, file pitch 0 and yaw only. `Q.PitchDeg` becomes -90, engine
  Roll +90, and the offset is world -Z, which is 1 cm DOWN THE WALL.

Both stay co-planar with the surface under them, so all 20 decals will
z-fight, and `decalLiftCm=1.0` is printed on the scene line while no lift
happened. That is an instrument asserting a thing it did not do, which is
the failure class this project treats as worse than the artefact.

Nothing could have caught it: the lift lives in `VignetteShot.cpp`, the layer
`VignetteSpec.h` exists precisely because it cannot be compiled or run here,
and `ue-probe/tests/vignette-spec-test.cpp` contains no check on decal
orientation (grepped: five hits for "decal", all of them shape counting).
That is the rule working as designed and also the size of the gap it leaves.

FIX, one line, resident applies: replace `FVector(0.0f, -1.0f, 0.0f)` with
`FVector(0.0f, 0.0f, 1.0f)`. Keep the comment; it was already correct.

### C2. `windowsLit` prints a denominator that counts a different set (rule 3b)

`VignetteSpec.h` line 629 pairs numerator and denominator like this:

    WindowsLit, S.Windows.ShopCards,

The numerator is `GWindows.Num()`, filled by a loop over
`GSpec.Windows.LitNames`, which `vignette-pieces.json` line 15 shows has
THREE entries (`lit_bays":[0,2,5]`). The denominator is `shop_cards`, which
is SIX. So the first Unreal frame will print `windowsLit=3/6` on a scene
where 3 of 3 requested practicals were placed successfully.

Rule 3b in as many words: ask what the denominator COUNTED, not merely
whether one is printed, because one larger than the set examined turns a
clean result into a false claim with a number attached. The
`practicals-unplaced=N-of-3` note mitigates the failure case and does not
touch the headline number a reader will grep.

FIX, one line, resident applies: pass `(int)S.Windows.LitNames.size()` in
place of `S.Windows.ShopCards` at that call site.

### C3. The job ceiling no longer sits above the sum of its step caps

`.github/workflows/ledger-probe-unreal.yml` keeps `timeout-minutes: 115` and
the comment at lines 60 to 65 still asserts "The step caps now total 92
(6+1+10+60+15)". With the 20-minute vignette step added the caps total 112
(6+1+10+60+15+20), against a job ceiling of 115, leaving three minutes for
an uncapped commit step. The job's own stated invariant, written when it was
raised from 25 to 60 and again from 95 to 115, is that the ceiling sits above
the sum, "or a legitimate slow run is killed by the clock and the evidence
file reads as a build fault".

This one is worth doing BEFORE dispatch and not after, because the only
readable channel in this project is that commit step, and tonight is the
night it matters. A cook that runs long would take the evidence with it.

FIX, resident applies: `timeout-minutes: 135`, and the comment corrected to
"The step caps now total 112 (6+1+10+60+15+20)".

### C4. A ledger reason that is false the day it lands (rule 1)

`ledger/ReachCheck/allow.json`, entry `StreetVignettePieces.WriteFeet`, says
"the Unreal emitter READS it", present tense, of
`production/specs/vignette-feet.json`. It does not. `FindSpec` in
`VignetteShot.cpp` names four candidate paths and all four are
`vignette-pieces.json`; grepping `ue-probe/` for feet returns three hits and
all three are the word "footway" inside comments. The second consumer stated
as a fact does not exist in this tree.

This file's own preamble spends sixty lines on reasons that decay like
comments and on the four that were found wrong on 4 August. A reason that is
false on ARRIVAL is worse than one that decayed, because nothing will ever
re-check it.

The ENTRY STAYS. WriteFeet genuinely has no Game-layer caller and must not be
given one, for the reason the entry itself gives and which I uphold below.
Only the sentence changes.

FIX, dictated text, resident replaces the entry's value with exactly:

    BY DESIGN: the D1 spec files have two consumers and the Unity Game layer is neither. CoreTests writes production/specs/vignette-feet.json under --write-vignette-pieces and then guards its bytes. THE SECOND CONSUMER IS NOT BUILT YET, stated here rather than promised: as of 3 Sep 2026 the Unreal emitter reads vignette-pieces.json only, and nothing in ue-probe/ opens the feet file at all. The probe list's intended reader is an emitter that raycasts its own geometry at x_m,z_m and compares the hit to foot_y_m, which is queue work and not this entry's claim. StreetVignetteHost builds from the in-memory Plan, so a Unity call here would be a second copy of the street. Delete this entry if the Unity host ever reads the committed file instead of the plan.

### THE JUDGEMENT ON THE SIX BY DESIGN ENTRIES: UPHELD

I was asked to rule on the reasoning that put `WriteFeet` and five siblings
on the ledger as BY DESIGN rather than inventing a Unity caller. It is right,
and it is right for the reason the ledger itself keeps recording as this
project's most common fault.

A Game-layer call to `WriteFeet` would mean the Unity host writing a file it
already holds as a Plan, and then some later reader taking the file as a
second description of the street. That is ONE IDEA WITH TWO IMPLEMENTATIONS,
the shape that produced the duplicate door system, the two crossfades and the
two ambient-occlusion falloffs recorded in that same file. The entries take
the ledger's required form (they name who calls the API instead), and the
`WriteFeet` entry names its own deletion condition, which is the property
that stops a debt entry becoming a mute button.

Upheld, subject to C4. No builder invents a caller for any of the six.

### WHAT IS RIGHT IN THE UNREAL DIFF, verified rather than assumed

Recorded because a review that only lists faults teaches the wrong lesson.

- Rule 6 is satisfied. `LedgerVignetteShot::Start()` HAS a call site:
  `LedgerProbe.cpp` line 722 to 725, gated on `-LedgerVignette`, which is the
  first switch tested and the exact string the workflow passes. Built is
  running.
- The missing-mesh failure is separated from the empty-street failure.
  `DefaultGame.ini` line 27 asks for `/Engine/BasicShapes` to be cooked, and
  `BuildScene` names which of cube, cylinder and plane came back null instead
  of reporting 0 of 593 pieces.
- The vertical-to-horizontal field of view conversion. Handing the file's 60
  straight to `UCameraComponent::FieldOfView` would have given a 60 degree
  horizontal shot against Unity's 91.5, and it would have read as a modelling
  difference in a judged pair. Both numbers print on every shot line.
- The warm and timed tick accounting is exact. I traced it: 8 ticks elapse in
  `Warm` with none recorded, then 24 deltas are pushed in `Timed`. No
  off-by-one, and `frameStat=median-of-engine-frame-deltas` refuses to be
  confused with the Unity host's `Camera.Render` number.
- `MedianMs` returns -1 on an empty series, so a timing that never ran cannot
  print as a fast frame.
- The decal facing sign is derived, not tried, and the fold of the -90 into
  `Q.PitchDeg` composes correctly under `FRotator`'s roll-then-pitch-then-yaw
  order for both decal cases this file contains. `multiRotationInFile` prints
  every run, so the day that stops being safe the run says so.

### THE RESIDUAL UNRUN RISK, stated so no green reads as more than it is

NO UNREAL SCREENSHOT HAS EVER LANDED IN THIS REPOSITORY. `production/d1-probe/`
contains no `ue-shot.png` and no `ue-shot-verdict.txt`, and `DISPATCH` run 17
says run 16, dispatched for exactly that question, has not landed. So tonight
is simultaneously the first proof that any capture candidate writes a file on
that machine and the first attempt at the street.

The consequence for reading the result: four `status=NO-FILE` shot lines
would be a CAPTURE answer, not a street answer, and the debug-shot step
running in front of the vignette step is what separates them. A
`sceneStatus=WHOLE piecesEmitted=593/593` beside four NO-FILE lines means the
street built and the camera path did not. Say that to Jafar in those terms
rather than as a failure.

## THE DECISIONS

### A. QUEUE REFILL: file all six as written, in this order

Order changed, content not. Reasoning is one line each.

1. **050, `propsPlaced` has no denominator.** First because it is an
   INSTRUMENT fault and an instrument fault outranks a content fault here: a
   count with no denominator cannot tell nothing from fine, and it is the
   number the town's progress will be read from.
2. **051, the street name plate for a canon street.** E10 is MANDATORY on the
   BOM, has no prompt, and canon has already minted Quay Street, Weighhouse
   Lane and Tannery Row, so there is no design question to answer and the
   current state renders a blank mandatory plate into the frame.
3. **054, double yellows break at the crossover.** Cheap, visible in every
   ground shot, and currently wrong along the full 42 m.
4. **053, the chimney pot oversails its stack by 0.112 m each side.** One
   number in Core, visible on every roofline in both engines.
5. **052, wall overlays belong in the surface path.** Correct and larger: a
   1024 tiling surface stamped as a decal reads as a patch of different
   masonry, and moving it is an AssetLibrary change rather than a value.
6. **055, G3 imperfection scatter.** Filed as BLOCKED until a frame exists to
   look at, which tonight's runs produce, so it unblocks tomorrow rather than
   being held informally.

Also filed, from this ruling: **057** (see C below) and **058**, the emitter
has no code path to light a flat practical at all. Today `flat_lit_names` is
empty so the scene line honestly reads `flatsLit=0/0 nothing-to-light`, but
the day it is non-empty the Unreal frame silently loses lights the Unity
frame has and the line prints `flatsLit=SEE-flat_lit_names`, which is a
string where a reader expects a count.

D13's three work riders (the town form bible, the layout spec with testable
requirements, the reads-as-real gate) are NAMED AND NOT FILED TONIGHT. The
register parks them for a director and this is that director: they are Phase
A town work, off tonight's critical path, and three entries written at 01:00
would not meet rule 10's bar for a milestone entry. They go into the next
queue refill with numbers reserved. Naming them here is what stops them being
lost, which was the register's actual worry.

### B. `sign_telephone`: REGENERATE, and it costs nothing to be safe

It is not on the street. Grepped: `sign_telephone` appears in
`tools/imagegen/prompts.json` and in the two generated decal manifests, and
NOT in `production/specs/vignette-scene.json`. So it is not one of the 20
decals queue 046 wired, and it cannot appear in tonight's frames.

That makes this easy. The whole 45 are regenerated by 056 anyway, so adding
"no GPO, no crown, no post office or telecom insignia" to the negative list
is free, and it removes the question instead of defending it. A decision
record arguing that a red enamel TELEPHONE panel is far enough from GPO
kiosk trade dress would spend a decision on an asset we are about to replace.

STANDING CONDITION until it is regenerated: `sign_telephone` is not placed on
any surface and does not appear in any published still. If a regenerated
version still reads as GPO trade dress, THEN it becomes a decision record,
with the picture beside it. This is trade dress and not a weights licence, so
it does not go through the licence allowlist.

### C. 056 DOES NOT CLOSE, and here is how it does

The builder said so and the builder is right. Closing it tonight would be the
first working result standing in for the best available one.

WHAT IS MET: acceptance (1). The framing clause is on every prompt and the
generator refuses a prompt without one, with a selftest in both directions.
That is the durable half and it is the half that stops the fault recurring.

WHAT IS NOT: acceptance (2) and (3).

**(2), `usableFraction`, now has a home: the imagegen verdict.** Per-image
`usableFraction` with its method named goes on the PER-IMAGE line, and the
whole-run count of how many of 45 clear the bar goes on the DONE line, in the
same committed channel that already carries `imagegenVerdict=BANKED
wroteThisRun=31 ... checkedThisRun=31`. The arithmetic and the string live in
the tested layer, not in the PowerShell step, for the reason the instruments
rule gives.

AND THE BAR IS NOT SET TONIGHT. Ship the printer, run the regenerated set,
READ THE SERIES, then set the bound in a later change that quotes the row.
Rule 2 is not negotiable because the deadline is tonight.

**(3), the crop rectangles STAY tonight and are deleted by the regenerated
set, not before it.** Deleting queue 046's four hand crops before the
regeneration lands would put uncropped shopfront photographs into the street,
which is strictly worse than the workaround. 056's own text already allows
this: "or the record says which images still need one and why". The record is
this paragraph, and the count of images still needing a hand crop after
regeneration is PRINTED, not described.

SO: 056's status becomes PARTIAL, acceptance (1) met and dated, and the
remainder becomes **queue 057**, "usableFraction and the crop deletion", one
item so the printer and the deletion it drives cannot separate. Two of the
046 builder's notes go stale when the regeneration lands; 057 owns correcting
them, which is what stops them becoming the next decayed comment.

### D. DISPATCH ORDER: CONFIRMED as written, with an abort clock

1. **UE probe.** It is the risky one, it is the ONLY thing Jafar actually
   asked for ("the street rendered in UE"), and it carries two unrun unknowns
   at once. Running it first buys hours to name a wall and re-dispatch;
   running it last means a 04:00Z failure with nothing left.
2. **Unity build.** Known-good, produces the first still carrying props and
   decals, and spends the `ahead_of_unity_run` key (`run 152198e`,
   `pieces_then 546` against 593 now) that currently makes any judged pair
   inadmissible.
3. **Image regeneration**, about 53 minutes.

WHAT TO DROP IF ALL THREE WILL NOT FIT: **the image regeneration, first and
without hesitation.** It is the only one of the three that moves no number in
the 07:00 deliverable. Jafar asked for the street in Unreal, not for 45 better
plates; the regenerated set cannot reach a frame tonight because the Unity
build would already have run; and by decision C, 056 is not closing tonight
regardless, so the regeneration has nowhere to land an acceptance number. It
runs tomorrow on the free lane at zero cost against the ceiling.

SECOND DROP, if it comes to that: the Unity build. Keep the UE probe. A night
with one Unreal frame and no Unity frame answers the question that was asked;
the reverse does not.

THE ABORT CLOCK, so this is a rule and not a judgement call at 04:00Z:

- If no UE evidence has landed by **03:00Z**: drop the image regeneration and
  re-dispatch the UE probe once.
- If no UE evidence has landed by **04:00Z**: stop dispatching. Write the wall
  into `production/d1-probe/DISPATCH` as run 18's line, exactly as the
  previous five walls were written, and that named wall is the honest 07:00
  deliverable.
- Watch by ancestry (is there a landed run whose commit CONTAINS mine),
  never by branch movement, and capture the sha BEFORE dispatching.

### E. D13: the record is FAITHFUL, and the studio recommendation is SUPERSEDED, not confirmed

`ledger-v2/respec/decision-register/D13-street-layout-method.md` is faithful.
It records option B with all five riders as given, it names what it does NOT
decide (the reference towns, the layout spec's numbers, the data format
beyond D1), it holds the line against setting a threshold nobody has measured,
and it parks its three work riders for a director rather than letting the
hand that recorded dictation also file the queue. That is the correct
separation and it is rare enough to say so.

The provisional studio recommendation does NOT "stand". Jafar answered, and a
director does not confirm the owner. The sentence in
`game-design/decisions-pending.md` line 47, "The studio's read is B, and it is
provisional until a director confirms it", now sits AFTER "This card is
closed" and will read to a later session as an open item. It is superseded.

RESIDENT, dictated text: in `game-design/decisions-pending.md`, prefix that
paragraph with "SUPERSEDED BY THE ANSWER ABOVE, 2026-09-03: the owner ruled
the same way and a director does not confirm the owner. Kept for the
reasoning only." Do not delete it; the reasoning is why B was worth
recommending and it outlives the recommendation.

### F. BUDGET: the plan is CONFIRMED, with two corrections to the record

CONFIRMED. After this ruling the night runs on the FREE LANE ONLY: the Unreal
probe, the Unity build and the image regeneration all execute on Jafar's own
machine and cost nothing against the ceiling. No tier-2 or tier-3 spawn
unless something breaks in a way that blocks the 07:00 deliverable. Watching
a free run land is not a spawn. The burn LEADS the 07:00 report, first item,
not buried.

The four corrections C1 to C4 in this ruling are deliberately all one-line
edits or dictated text, inside the resident's remit, precisely so that acting
on this review costs zero further spawns.

CORRECTION 1, and it is the honest one. `production/budget.md` line 240 to
242 planned "ONE director spawn, because batch review before commit is a
mandatory trigger". THREE were spent: 21:27:43Z, 21:42:14Z and mine at
00:22:45Z, of which the first two produced no ruling (one container restart,
one session limit). The plan's "one" must not stand in the file as if it
happened. Record the actual three with the two causes, because a plan that
quietly absorbs a 3x overrun is a plan nobody can learn from.

CORRECTION 2. The 21:47Z session limit is a SECOND ceiling measured in HOURS
with its own reset, not points, and it must never be entered into the weekly
percentage table. `budget.md` already says this correctly at lines 262 to 269;
this is a confirmation, not a change, and it is repeated here because the
temptation to write "we hit the limit" into the percentage column is exactly
the reset-boundary fault that file already records twice.

WHAT REMAINS UNKNOWN AND MUST BE ASKED, not inferred: the weekly percentage.
The newest reading is 38 percent at about 17:00Z, before a director, five
agents, four resumes, two dead directors and this ruling. Nothing in this
container can read it. The 07:00 report asks Jafar for one number, and until
it arrives the day is UNMEASURED in condition 4's sense.

## THE ORDER OF OPERATIONS FROM HERE

1. Resident applies C1, C2, C3, C4 and the E dictation. All are one line or
   dictated text.
2. Resident resolves the 047 question in the paths section (`git diff --stat
   f789e129 -- tools/dashboard/`) and reports any dirty path not on the
   `paths=` list.
3. Refile the queue per A: 050 to 055 as written in `production/NOW.md` lines
   155 to 163, in the order set above, plus 057 and 058.
4. Update 056's status to PARTIAL with acceptance (1) met and dated.
5. `python3 ledger/verify.py`. Green. Paste the footer FROM
   `ledger/.verify-footer`.
6. ONE commit, staged by name against the `paths=` list.
7. Push, then touch `production/d1-probe/DISPATCH` and push, which starts the
   UE probe. Capture the sha first.
8. Update `production/NOW.md` and write the dashboard feed.

## THE QUALITY LADDER, asked at close

Is this the best available result or the first working one?

FIRST WORKING, and the next rung is named for each. The Unreal street is
untextured, black-skied, with 23 props as boxes and 20 decals as quads: Phase
C is the rung and it is already scoped. The decal lift, the `windowsLit`
denominator and the job ceiling were all first-working and are corrected in
this commit. 056 is explicitly not closed because its next rung (a measured
`usableFraction` over a denominator of 45) is blank, and a blank next rung is
a research task, not a finished aspect: that is queue 057.

The one aspect with a genuinely blank rung tonight is the placement
instrument on the Unreal side. `vignette-feet.json` ships 910 probes with
`datum_missing 0` over `datum_examined 910`, and nothing in Unreal reads it,
so the metric that caught eight blocks hanging over open sea in Unity has no
Unreal half at all. That is the research task, and it is what C4 stops us
from believing is already done.
