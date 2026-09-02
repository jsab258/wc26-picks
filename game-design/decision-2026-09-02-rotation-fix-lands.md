# DIRECTOR RULING: the rotation fix lands with one guard added, appliedYaw stays, Foot5 goes to the queue, and a ruling nobody applied is recorded as the process hole it is (2 Sep 2026)

> **STATUS — LOG, 2026-09-02. NOT CURRENT once the fix is committed with L1 to L5 below applied and the second Unity render has landed; from then the code, `game-design/sim-shots/verdict.txt`, the queue and `production/NOW.md` are the reading copies and this file is their history.**

This document carries exactly one em-dash, in the banner, because
`tools/docs-check.py` line 55 accepts no other form (read this session).

Ninth ruling since 1 September. No shell: every number below was read from a
file or recounted by hand from the code and the scene JSON, and the source
is named beside it. Builders' and the resident's reports were not read as
evidence; the diff and the landed verdict were.

## What was verified

- My row: `.claude/agent-log.tsv` line 202, `2026-09-02T10:42:15Z
  studio-director`, the newest in the file. `.git/logs/HEAD` lines 334 to
  345: the batch is `d25a4770` at epoch 1788330360 (06:26:00Z); the render
  ran on `8f19addd` at 1788341196 (09:26:36Z); the newest commit is the
  fast-forward `713aee77` at 1788344519 (10:21:59Z) that brought the CI
  evidence in. My row is newer than every commit in the reflog. Rows 197
  and 198 are the two directors of the morning with no builder row between
  them; rows 199 to 201 are the three engine-specialists spawned after the
  batch commit.
- `ledger/Assets/Scripts/Core/StreetVignette.cs` in full (1352 lines):
  `Piece.RollDeg` 56 to 63, `Foot5` 274 to 288, `ShapeReport` 326 to 342,
  `Slab` 476 to 495, the gutter 817 to 828, the boom 873 to 880, the
  elements 886 to 895, the swan neck 1002 to 1015, the rail bars 1171 to
  1178, the litter yaw at 1249, `StreetSection` at 116 (E1 applied), line
  400 (E2 applied).
- `ledger/Assets/Scripts/Game/StreetVignetteHost.cs` in full: `Emit` 133 to
  192 (the rotation 177 to 179, the cylinder scale 182 to 184), `Apply` 344
  to 438 (the sun 375 to 391), `Shoot` 466 to 467 (the camera keeps
  `90 - yaw`).
- `ledger/CoreTests/Program.cs` 19238 to 19361: the shapes print at 19301,
  the guard 19316 to 19330, the tolerance at 19321. Greps of that file:
  `RollDeg` and `PitchDeg` hit one comment line (19306); `YawDeg` and
  `Foot5` hit nothing; `litter` hits the authorised list only (19442). No
  test reads any of the three rotation fields and nothing exercises
  `Foot5`'s swap.
- `production/specs/vignette-scene.json` in full: no `yaw_deg` on the
  kiosk or the pillar box (brief item 3 applied); `on_stacks [1, 3]`,
  `elements 10`, `panels 3`, `bays 6` on the one pitched block,
  `day_azimuth_deg 205`, `day_elevation_deg 36`.
- `game-design/sim-shots/runs/8f19add.txt` lines 94 to 120 and
  `verdict.txt` line 1 (`8f19add @1788341196`): `datumMissing=521/845`,
  `place/region x00_06 probes=55 datumMissing=55/55 gap=nothing-landed-here`,
  four `shot vign_*` lines, `done. errors=0`, and no `sun` line, because
  the Host that ran printed none. Both day stills opened (rule 4): cam_B is
  a stone wall filling the frame with shopfront parts standing edge-on and
  a roof overhead; cam_A is one dark facade filling the left of frame. Both
  are the street built across itself, as the 05:43 record predicted.
- The previous two rulings in full, and for their dictated edits a grep of
  each target named in Ruling 5. `production/queue/027` lines 1 to 30,
  `031` lines 1 to 12, the queue file list (031 is taken, no 032 exists),
  `NOW.md` in full, `canon.md` lines 14 and 19 (E3 applied),
  `FETCH-VIGNETTE` line 18, `quality-ladder.md` grep for the dictated
  heading, `docs-check.py` 41 to 75.

## Ruling 1: the fix LANDS, one commit, after L1 to L5

The diff is the fix the 05:43 ruling dictated, applied as dictated: yaw 0
is the identity in `Emit`, the minus carries the two bearing senses, the
roll lets a pipe lie down, the camera keeps its facing conversion, the sun
is `270 - azimuth`, the two `yaw_deg` fields are gone, `ShapeReport` lives
in Core and is printed by the test and the Host from one string. Nothing
weakens an instrument; one instrument that did not exist now does. The
render is unverified and stays so until the second dispatch (L5).

**Landing conditions, exact text, nothing judged at apply time.**

L1. `ledger/CoreTests/Program.cs` line 19301,
`Console.WriteLine("    " + StreetVignette.ShapeReport(plan.Pieces));`,
becomes:

```
            string shapes = StreetVignette.ShapeReport(plan.Pieces);
            Console.WriteLine("    " + shapes);
            // THE PIPE COUNTS ARE ASSERTED AS WELL AS PRINTED, because the
            // circular-in-plan guard below is satisfied by a pipe shrunk to
            // a disc. Nine lie along the street (one gutter, two booms, six
            // rail bars) and thirty-two are pitched (twenty aerial elements,
            // twelve swan-neck segments); both read off this print on the
            // live tree, 2 Sep. Planting on_stacks [1] in the JSON prints
            // cylRolled=8 cylPitched=22 and goes red here.
            Check(shapes.Contains("cylRolled=9 cylPitched=32 "),
                  "nine cylinders lie along the street and thirty-two are pitched, as printed on the live tree",
                  shapes);
```

Watched both ways, accepting first (rule 5b): run CoreTests on the tree as
it stands and read the count (4207 becomes 4208); then set `on_stacks` to
`[1]` in the JSON, run again, read `cylRolled=8 cylPitched=22` and this
check red (other piece-count checks may go red beside it; the quoted line
is this one); revert the JSON; run once more green. All three outputs go
in the commit message.

L2. `StreetVignetteHost.cs`, two comment corrections, because a comment
citing an instrument that does not ship, or a still that the next run
overwrites, is the shape rule 1 exists for. Line 174, `(0 of 546, counted
in CoreTests this session)` becomes `(0 of 546 by reading every emitting
family in Core; no shipped test counts it)`. Lines 162 to 166, from `That
is` to `the same scene.`, become:
`That is what the first render showed on run 8f19add: the still under game-design/sim-shots/ is overwritten by every run, so the durable evidence is game-design/sim-shots/runs/8f19add.txt line 97, where the engine-side probe read datumMissing=521/845 while the plan-side probe read 0/845 on the same scene.`

L3. `StreetVignette.cs` lines 277 to 278, the two comment lines inside
`Foot5`, become:

```
                // The half-extents swap at yaw 90; every other yaw is probed
                // UNROTATED. Nothing footed carries yaw 90 today, and the
                // litter (G8) carries an arbitrary yaw, so its true footprint
                // reaches up to 6 cm beyond where its probes look on the
                // widest piece at 45 degrees; queue 033 rotates the corners.
```

L4. `python3 ledger/verify.py` green, footer from the file. One commit,
staged by name: the four files of the batch, this record, `NOW.md` (L5),
`production/queue/027-ue-vignette-emitter.md` (Ruling 4), the new `032`
and `033` (Rulings 5 and 3), and the owed edits of Ruling 5. The message
quotes, from runs after every edit: the CoreTests count, the `shapes`
line, the `cylinders: 146/146 circular in plan` line, the three L1 outputs;
and it lists every dictated edit id of this record with `applied` beside
it.

L5. `production/NOW.md` lines 47 to 63 (the section `## Where this is,
2026-09-02`) become:

```
## Where this is, 2026-09-02: the rotation fix is in the tree, the second render is the proof

THE STREET VIGNETTE RENDERED ONCE, SIDEWAYS. Run 8f19add (landed 10:22Z)
drew all four stills with every piece turned 90 degrees: the engine-side
placement probe read datumMissing=521/845 against the plan-side 0/845
(game-design/sim-shots/runs/8f19add.txt line 97), which is the two-halves
instrument catching the emitter fault the 05:43 ruling had dictated a fix
for and the 06:26 batch committed without. The fix is in the tree under
game-design/decision-2026-09-02-rotation-fix-lands.md: yaw 0 is the
identity, lying pipes are rolled cylinders, the sun sits at Unity yaw 65
and not 205, and the pipe-count guard was watched red then green.

THE NEXT UNITY DISPATCH IS THE PROOF. Read, in this order and before any
still: placement datumMissing=0/845; the shapes line equal to the CoreTests
print (cylRolled=9 cylPitched=32 cylUpright=105); sun elevation=36.0
bearing=205.0 unityYaw=65.0 appliedYaw=65.0. Then open all four stills:
cam_B square to the parade with the roofline in frame, cam_A up the kerb
line into the fog with the parade on the LEFT (Unity is left-handed, so
facing +x puts +z on the left); day shadows toward bearing 25, which is
away and a little left in cam_A and mostly right in cam_B. A datumMissing
above zero or a float the crossfall does not explain is an emitter finding,
never a plan finding, and the run is not evidence about the plan.
```

The rest of `NOW.md` is refreshed as the timebox record's R1i note already
asked: the STOPPED section predates the 04:40Z reading, the three-jobs
paragraph is history, and the D1 section is R1i's text. Then dispatch
`ledger-build-windows.yml` by hand on the branch, watch by ancestry, and
pull before the next local commit.

## Ruling 2: the guard is a real two-sided test, with one hole, closed by L1

Not a tautology. The same code path took two different inputs, the tree
before the fix and after, and both outputs reproduce by hand from the code
and the JSON. 29 non-circular is 1 gutter (only `east_parade` is pitched),
2 booms (`on_stacks [1, 3]`), 20 elements and 6 rail bars (3 panels by 2);
`east_parade_gutter(SX=36.000/SZ=0.112/SY=0.112)` is 6 bays by 6.0 m and
the 112 mm gutter. After: `cylRolled=9` is 1 + 2 + 6; `cylPitched=32` is
20 elements plus 12 swan-neck segments (4 columns by 3, the count the
lantern check already pins); `cylUpright=105` is 2 masts, 9 downpipes, 4
bases, 4 shafts, 3 pillar-box pieces, 4 posts, 15 infill bars, 2 bins, 2
lids and 60 gum. 9 + 32 + 105 is 146. A guard whose rejecting number came
from real pre-fix data rather than a planted fixture, and whose accepting
numbers a reader can recount, is the shape rule 5b asks for.

The hole is the one the builder named: `SX == SZ` is satisfied by a disc.
L1 closes it with the printed count, in the style of the lantern check at
19338, so a data change that moves a pipe count touches the test. The
`1e-9` tolerance is moot today, since every cylinder sets `SX` and `SZ`
from one expression, and it is not a loosening.

## Ruling 3: the three items

**1. The ruling understated the count, not the fault.** The 05:43 record
named all four families at its lines 249 to 253; its brief item 4 said
"today the gutter fails it", which was the first of 29. The guard printed
the true number, which is what a guard is for. Record corrected here;
nothing to do.

**2. `appliedYaw` stays.** A conversion printed and never read back is a
claim about the transform; reading the transform is the measurement (rule
1). What it proves is bounded and the builder's comment says so:
`appliedYaw == unityYaw` proves the assignment reached the light and
nothing else. For any other purpose the two are one number twice (rule 2);
the CONVERSION is proved only by the day frame's shadow running toward
bearing 25. One more key for the 05:43 record's Ruling 9 to learn.

**3. `Foot5` is a queue item, not a landing condition.** Three reasons,
each readable in the code. First, the swap branch never served a footed
piece: no footed family carries yaw 90 (the rolled pipes are not footed),
and the litter's `r0 * 180.0` lands on 90 with probability zero, so this
fix narrows nothing that was live. Second, the error is bounded: on the
widest litter piece (0.24 by 0.168) at 45 degrees the true footprint
reaches 6 cm further across the street than the unrotated probes look, and
2.4 cm further along it. Third, it cannot move the number the next
dispatch is judged on: `datumMissing` needs a probe off the street, and
the plan-side check `off == 0` passes at 4207. What rotating the corners
CAN do is put a litter corner across the 125 mm kerb step and trip the
12.4 mm bound. That would be a finding about the litter (a crisp packet
does not lie half on a kerb), fixed in `Scatter` by keeping the
half-diagonal inside the band, never by widening the bound. The item,
dictated, `production/queue/033-foot5-rotated-footprints.md`:

```
line: production (the placement instrument, plan-side half)
spec: game-design/decision-2026-09-02-rotation-fix-lands.md, Ruling 3 item 3
acceptance: Foot5 rotates its four corners by YawDeg and the swap branch is gone; the plan-side prints (feet over ground N/845 and the worst foot gap line) quoted BEFORE and AFTER from the same session; the 0.0124 m bound unchanged; any litter corner that newly crosses the kerb step is fixed in Scatter by keeping the piece's half-diagonal inside its band, never by widening the bound
max_sessions: 1
status: READY 2026-09-02. Behind 027 and 028. Not a landing condition of the rotation fix: no footed family carries yaw 90 and the litter's probe error is bounded at 6 cm on the widest piece (Ruling 3 of the spec).
```

## Ruling 4: the two next steps

**`roll` in the flat piece list** is already in 027 Phase A's field list
(line 10: `pitch, yaw, roll`). What the builder is right about is that the
list is the first thing that will serialise it, and this axis is exactly
where the two engines would next disagree. There is a second seam on the
same axis that nothing printed can see: the scene frame (+x north, +z
east, y up) is right-handed as a compass, and Unity is left-handed, so the
Unity render is the mirror of the compass (facing +x, +z is on the left).
Append to Phase A of `027`, after line 13:

```
The drift guard has a second half, ruled 2026-09-02 (decision-2026-09-02-rotation-fix-lands.md, Ruling 4): the UE emitter prints the same `shapes pieces=.. box=.. cyl=.. cylRolled=.. cylPitched=.. cylUpright=..` line from ITS reading of the list, and the two engines' lines are equal. Roll is the axis the Unity emitter got wrong first; a piece count cannot see it and this line can. And handedness: Unity renders the scene frame mirrored (facing +x puts +z on the LEFT). The UE emitter must land the parade on the same side of cam_A's frame as the Unity still does, or the pairs are mirror images and no blind look is of one street. The check is the first pair opened side by side, said in the DISPATCH line.
```

**`cylRolled` asserted** is L1, and it asserts the printed number rather
than a floor, because a floor of one would pass a scene that lost the
gutter.

## Ruling 5: the resident's error, recorded as a hole and not passed over

The 05:43 ruling's order of work was numbered: step 2 spawns the
engine-specialist for the rotation fix, step 3 commits. The batch was
committed at 06:26:00Z with no builder row between that ruling (05:43:50Z)
and the commit: the fix was not applied and not spawned. The render on
`8f19add` then paid for it, one Unity round trip, 06:26 to 10:22, spent
proving a prediction that was already on the record.

It is not one miss. Checked this session against the two rulings' own
dictated text, 13 targets examined: E5 (`FETCH-VIGNETTE` line 18 still
reads `not yet dispatched`, found unapplied at 06:47 and still unapplied);
the ladder heading `## The D1b vignette scene` exists nowhere in
`quality-ladder.md`; of the timebox record's R1a to R1m, seven are
confirmed unapplied (R1a, R1b, R1c, R1d, R1h by grep of their own words in
their target files; R1g and R1i by direct read: `027` line 5 still says
`against the 2026-09-14 timebox`, `NOW.md` still carries the section R1i
replaced) and six (R1e, R1f, R1j, R1k, R1l, R1m) were not checked; its
`031` stub was not written, while a different `031` was. E1, E2, E3 and
the four queue items were applied. The pattern is exact: the record is
committed, and the edits inside it are applied when they are code the
resident was already holding and skipped when they are not.

What the gate cannot see. `director_cadence` proves a ruling is NEWER than
the code. Nothing proves a ruling was APPLIED. The 05:43 record's own
phrase was that a spawn alone is attendance, not a review; the successor
is that a ruling alone is a plan, not an application.

The cheapest instrument, binding from this record, no tool: every commit
that lands a ruling lists each dictated edit id with `applied` or
`deferred: <reason>` beside it, and the next director's first act of
verification is that list against the tree by grep, before ruling on
anything new. This record did that; the two before it did not, and the
second missed what the first had lost.

The owed edits land in this commit, since they are text and cost no model
time: E5; the ladder rows of the 05:43 record; R1a to R1m of the timebox
record, verbatim, each confirmed by grep before editing, with `031` read
as `032` wherever that record names the loop investment (its stub becomes
`production/queue/032-ue-loop-investment.md`, because 031 is taken), the
renumbering noted in the commit message.

## Deliberately not decided

- Whether the sun conversion is right. The shadow in the day frame decides.
- Whether a light from bearing 205 does what the JSON's note says. The note
  says it rakes across the street; 205 is 25 degrees off the street's own
  axis, so it rakes down it. A composition choice, judged on the frame.
- Whether litter may overlap the kerb. After 033's print.
- The game-level handedness (a mirrored Britain drives on the right). A
  question for the world pipeline, named here, not the vignette's.
- The engine. Unchanged.

## For the next session in one line each

- Apply L1 to L5 and Ruling 4's sentence; write 032 and 033; apply the owed
  edits of Ruling 5 with a grep before each; verify; one commit, staged by
  name, the message listing every edit id.
- Dispatch the Unity build by hand; read the three lines in L5's order;
  open all four stills; resume this director if `datumMissing` is above
  zero, the shapes line differs from CoreTests, or the shadows run any way
  but bearing 25.
- One line to Jafar, with a picture: the first street rendered sideways
  and the instrument caught it before anyone looked (the cam_B frame,
  captioned with 521/845); the fix is in and the next build proves it.

Spawn row, quoted verbatim from `.claude/agent-log.tsv` (line 202):

    2026-09-02T10:42:15Z	studio-director

<!--RULING spawn=2026-09-02T10:42:15Z-->
