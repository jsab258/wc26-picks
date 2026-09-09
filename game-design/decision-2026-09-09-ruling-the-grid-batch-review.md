# Ruling: the grid batch reviewed, the elevation refusal upheld, and the null that turns out to be seven samples

> **STATUS: LOG, 2026-09-09. NOT CURRENT** once the conditions in section 9 are
> met and the batch is committed. Director ruling at spawn
> 2026-09-09T21:28:40Z, `.claude/agent-log.tsv` line 494, which is the newest
> `studio-director` row in that file. A SIMULATION change, a landing that
> changes a conclusion, a verifier-builder disagreement and a close-out, so the
> escalation is mechanical rather than judged.
> REVIEWS the working-tree batch built to
> `game-design/decision-2026-09-09-ruling-the-grid-not-the-ladder.md` (19:46Z),
> which I read in full, all 643 lines, and which binds everything below.
> UPHOLDS that record's section 4.6 ruling 2 against the resident's repeated
> instruction, section 5.
> AMENDS that record's conditions C4, C5 and C10, section 9.
> ANSWERS `production/queue/231`, section 6.

VERDICT: THE BATCH IS APPROVED WITH FIVE AMENDMENTS, three of them blocking.
A6 is approved and is the most valuable thing in the batch. A2 is approved and
its invariance claim is proved by a test rather than asserted. A1 is approved
in substance with one dictated amendment MISSING from the diff, which is
blocking. A4 is approved and its two-engine rider is satisfied in a narrower
sense than the word "reads" suggests, recorded here. A3's partial state is
ALLOWED and is not the shape my predecessor removed six rows for, for a reason
neither the resident nor the builder gave. THE ELEVATION REFUSAL WAS CORRECT
AND THE BUILDER WAS RIGHT TO REFUSE IN WRITING. The pre-existing red gets its
repair in this batch, narrowly scoped, because the repair makes the guard
assert MORE than it does today and not less.

THE FINDING THAT OUTRANKS THE REST OF THIS FILE. The batch ships SEVEN frames
whose rendering inputs are identical in Unreal, not one null pair, and they
span shot positions 5 to 25. C4 is the blocking gate on whether any grid cell
may be quoted, and it was written for one difference. Section 4.

## 0. What I could not run, and what is therefore mine

NO BASH IN THIS SPAWN, the same hole my predecessor had at 19:46Z. I ran
nothing: not `ledger/verify.py`, not the three test binaries, not a git
command, not `git diff`. I could not see the diff as a diff. EVERY CLAIM BELOW
IS EITHER A WORKING-TREE FILE I OPENED AND READ, NAMED WITH ITS LINE, OR
ARITHMETIC OF MINE ON SUCH LINES, OR LABELLED AS THE RESIDENT'S OR THE
BUILDER'S REPORT. Where I write "verified" I read the file this session.

THE TEST COUNTS ARE REPORTED, NOT CONFIRMED. vignette-spec-test 275 checks 0
failed, frame-stats-test 108 checks 0 failed, CoreTests 4310 passed, docs
178/178 are the builder's numbers carried by the resident. I could not run any
of them. Conditions C1 and C2 put them back in front of a reader who can.

Read this session, in whole or in part:
`game-design/decision-2026-09-09-ruling-the-grid-not-the-ladder.md` in full,
`tools/stage-vignette-scene.py` in full, `tools/docs-check.py` 40 to 220,
`.github/workflows/ledger-build-windows.yml` 60 to 80, 195 to 240, 519 to 645,
`.github/workflows/ledger-probe-unreal.yml` 1095 to 1135 and its step list,
`production/specs/vignette-scene.json` 756 to 1121,
`ue-probe/Source/LedgerProbe/Private/VignetteShot.cpp` 196 to 226, 328 to 368,
488 to 517, 780 to 826, 1386 to 1462, 1805 to 1836, 1995 to 2040, 2280 to 2340,
`ue-probe/Source/LedgerProbe/Public/VignetteSpec.h` 2079 to 2145 and 2180 to
2329, `ue-probe/Source/LedgerProbe/Public/FrameStats.h` 690 to 830,
`ue-probe/tests/vignette-spec-test.cpp` 1930 to 2001 and 2225 to 2455,
`ue-probe/tests/frame-stats-test.cpp` 510 to 610,
`ledger/CoreTests/Program.cs` 19560 to 19680,
`ledger/Assets/Scripts/Game/StreetVignetteHost.cs` 100 to 170 and 620 to 720,
`ledger/Assets/Scripts/Core/StreetVignette.cs` 1789 to 1830 by grep,
`tools/sim-shots-commit.sh` by grep, `production/queue/231`,
`game-design/sim-shots/verdict.txt` 1 to 14 and 100 to 128,
`game-design/decision-2026-09-02-vignette-batch-canon-crews-d1-timebox.md` 180
to 220, `.claude/agent-log.tsv` 470 to 495, `.git/config`.

NOT OPENED, AND IT MATTERS: no frame. There is no new frame to open, because
the run this batch exists to produce has not been dispatched. Rule 4 therefore
lands on the resident at C14 and not on me, and nothing in this record is a
judgement about a picture.

## 1. Premise check, CLAUDE.md section 0

Nothing here dates the world outside 1988 to 1992. The scene is a wet overcast
British port street; the work is a sun elevation, a sky intensity, a fog cap
and a wetness scalar. No mobile, no internet, no 1950s or 1970s framing.
Nothing cites the retired GTA V bar, nothing is purchased, no tool enters, no
licence entry moves. Meridian Test point 1 is what this serves: a street lit
from eight degrees off vertical has no shadow in it, and the first thing a KCD2
player sees is whether the ground has a dark end.

## 2. What I verified myself, claim by claim

**A6, THE SUN. VERIFIED, and it is better than the summary says.**
`VignetteShot.cpp:801` to `:816`: `SpawnDirectional` calls `MakeMovable(L)` and
then `C->SetWorldRotation(Rot)` on the light component. Nothing subtracts 46,
nothing names a default, which is exactly what section 4.6 required. All four
lights go through it, `:1164` to `:1167`. The asked pair is captured at the
spawn call, `:341` to `:349`, not re-derived, which was the one thing that
would have made the instrument agree with itself. The readback is the light
COMPONENT's world rotation, `:1827`. The wrap is real and is needed:
`VignetteSpec.h:2202` to `:2208` wraps to plus or minus 180, and fill B asks
yaw 200.0, which an FRotator returns as -160.0.

THE REFUSAL FAILS CLOSED, WHICH IS THE HALF THAT IS EASY TO GET WRONG.
`VignetteSpec.h:2275` to `:2277`: the only passing word is AGREES, a run that
read no light prints NOTHING-MEASURED and does not pass, and the denominators
are Spawned over asked, Read over Spawned, Agreeing over Read. The worst
residual names its light and its axis, `:2287`. The CI half is
`ledger-probe-unreal.yml:1113` to `:1127`: MEASURED LINES ONLY, a missing key
reads MISSING rather than as agreement, and the step exits 1. That step is
`continue-on-error: true` at `:887` while `Commit the probe result` at `:1829`
is NOT, so the verdict is committed and the step still goes red, which is
amendment (b) of section 4.6 satisfied by the same mechanism `captureStatus`
already uses.

ONE RESIDUAL RISK, NAMED BECAUSE IT IS UNVERIFIABLE HERE AND THE INSTRUMENT
CATCHES IT. `MakeMovable` at `:495` to `:502` sets mobility on the actor's ROOT
component. If a directional light's root is not its light component, the light
component stays at its spawned mobility and `SetWorldRotation` may be refused
by the engine. Nothing in this container can answer that, and nothing needs to:
C15 reads the residual off the committed verdict, and a refused write shows up
as a residual rather than as silence. That is the correct relationship between a
guess and a gate.

AND A CONSEQUENCE NOBODY HAS WRITTEN DOWN YET, which is why A6 is the most
valuable item in the batch. `ledger/Assets/Scripts/Game/StreetVignetteHost.cs`
at `:653` to `:655` sets the Unity sun to `Quaternion.Euler(elevation, yaw, 0)`
with the elevation straight off the shared file, and
`game-design/sim-shots/verdict.txt:115` reads
`sun elevation=36.0 bearing=205.0 unityYaw=65.0 appliedYaw=65.0` on a real run.
Unity has been lighting that street from 36 degrees while Unreal lit it from
82. THE ENGINE COMPARISON D1b EXISTS TO DECIDE HAS NEVER BEEN MADE BETWEEN TWO
STREETS LIT THE SAME WAY. A6 does not improve a picture, it makes the
comparison admissible for the first time.

Note for the next session and not for tonight: Unity prints `appliedYaw` and
has no `appliedPitch`. Its sun carries the same unmeasured axis Unreal's did.
Filed, section 10.

**A2, THE IN-FRAME STATISTIC. VERIFIED, including the proof.**
`FrameStats.h:722` to `:745` is the robust ratio with the dictated
ROBUST-NOT-INVARIANT string and a NOTHING-MEASURED branch that says which of
the two reasons applies. `:772` to `:814` is the rank key,
`darkerThanSkyMedianPct`, defined as the percentage of ground pixels strictly
below the skyCentre band median OF THE SAME FRAME, which mentions only
comparisons inside one frame and so meets the one rule the ruling set. Ties by
`lower_bound` against `upper_bound`, rails as lo then hi, both with
denominators, `:796` to `:809`. The word "invariant" never appears without the
bloom, vignette, grain and local-tonemapping exceptions beside it, `:778` to
`:780`.

THE INVARIANCE IS MEASURED, NOT ASSERTED. `frame-stats-test.cpp:591` to `:609`
puts every 8-bit code through a gamma of 0.45 and then checks the rank key
still reads `43.7500/of=1280` while the same band's p05 moves by more than
0.01. That is the claim proved in the layer that runs, and it is the difference
between this key and every percentile on the line.

RULE 6, THE CALL SITE. `VignetteShot.cpp:2309` is `Line += SkyBandLine(...)`,
and `FrameStats.h:825` onward is where `SkyBandLine` calls both new formatters.
Built and called, verified by grep, not by the builder's word.

**A1, THE GRID. VERIFIED IN SUBSTANCE, ONE DICTATED AMENDMENT MISSING.**
`vignette-scene.json:1073` to `:1099` lists 25 shots: the four judged pairs,
`vign_hook_day`, twelve grid cells, four fog rows, three wetness rows and
`vign_grid_null_repeat` LAST. All 21 probe rows stand at `cam_hook`, which I
checked row by row. No `ladder_` condition and no `ladder_` shot survives
anywhere in the file, so the six removals happened. The sky order over the grid
is 050, 100, 035, 070, 100, 050, 035, 070, 100, 050, 035, 070, which rises and
falls, and `CoreTests/Program.cs:19632` to `:19649` prints the sequence and
then asserts both directions, which is C6 made mechanical instead of promised.
`grid_null_repeat` at `:960` to `:971` agrees with `grid_sky100_sun003` at
`:806` to `:817` on every rendering field: sun on, 3.0, sky 1.00, the same two
hdri keys, wetness 0.60, fog_density 0.0120, fog_max_opacity 0.450, lanterns
off, practicals off. I compared them field by field myself.

MISSING: A1(d). I grepped the whole tree for
`WholeFrameIncludesControlQuads`, `atMostPct` and
`PROJECTED-BOXES-NOT-MEASURED-COVERAGE`, and the only hits in the repository
are lines 228 and 231 of the ruling that dictated them. The per-sample
declaration does not exist. The whole-run `controlQuadVisibility` line does,
`SurfaceBind.h:585`, and it is not the same instrument: it counts hidden shots,
it does not stamp the four judged sample lines whose whole-frame keys include
the quads. Amendment 1, blocking, section 8.

ALSO MISSING, AND THE COST OF FIXING IT IS WHY IT IS NOT BLOCKING: A1(a) says
"the run prints the difference between the pair". It does not. The per-shot keys
are printed for both frames and the subtraction is left to a reader,
`production/d1-probe/DISPATCH:1028` being where the reader is told to do it.
Amendment 2, section 8, re-scoped on a cost I measured.

**A4, THE FOG. VERIFIED, AND THE RIDER IS SATISFIED IN A NARROWER SENSE THAN
"READS".** `VignetteSpec.h:466` parses `fog_max_opacity` with `NeedNum`, so a
condition without it refuses. `VignetteShot.cpp:1441` is
`F->SetFogMaxOpacity(bWhole ? (float)C.FogMaxOpacity : 1.0f)`, and `bWhole` at
`:1389` is `SkyIsWhole()`, which is about the sky rig spawning and not about
day or night. The old line was the same shape with the literal 0.45f, and both
judged conditions carry 0.450 at `:772` and `:786`, so NOTHING MOVES in either
judged frame. Four rows at 0.450, 0.250, 0.100, 0.000, verified at `:982`,
`:996`, `:1010`, `:1024`, and `CoreTests:19562` to `:19576` asserts the series
and that `overcast_day` still carries 0.450.

THE RIDER, PRECISELY. Core READS the key in the sense the two-engine contract
cares about: `StreetVignette.cs:1823` parses it with `Num`, which throws on a
missing key, so there is no silent fallback and the two engines cannot build
two different streets from one file. Core does NOT APPLY it, and I found no
application site in the Unity tree; the Unity vignette sets
`RenderSettings.fogDensity` at `StreetVignetteHost.cs:683` and built-in Unity
fog has no max-opacity parameter to set. So the honest statement, and it is
this record's job to make it: `fog_max_opacity` IS REQUIRED IN BOTH READERS AND
APPLIED IN ONE ENGINE, because the receiving feature exists in one engine.
That is not an exemption and it is not a fallback. It is also now true of
`sun_intensity` and `sky_intensity`, which Unity parses and does not use
(`StreetVignetteHost.cs:670` sets `_sun.intensity` to a literal 0.85f, and I
found no `SkyIntensity` read anywhere under `ledger/Assets/Scripts/Game/`).
Three keys parsed and unapplied in one engine is a pattern rather than an
incident, and it is filed in section 10 rather than fixed tonight.

## 3. A3's partial state: ALLOWED, and for a reason neither of you gave

THE RESIDENT'S WORRY IS THE RIGHT WORRY. A row whose note explains why it
cannot work is close in shape to the six ladder rows my predecessor removed
for being rows nobody chose.

FIRST, THE DECLARED HALF IS TRUE. I ran the grep myself: `Wetness` appears at
`VignetteSpec.h:257`, `:266` and `:453`, and in the tests, and NOWHERE in
`VignetteShot.cpp`. Parsed and read by nothing in Unreal, rule 6, confirmed by
me and not taken from the builder.

SECOND, AND THIS DECIDES IT: WETNESS IS NOT UNREAD BY THE PROJECT, IT IS UNREAD
BY ONE ENGINE. `ledger/Assets/Scripts/Game/StreetVignetteHost.cs:715` is
`AssetLibrary.SetWetness((float)c.Wetness)`. I opened the surrounding lines, 698
to 717: it sits at the end of the vignette's own `Apply`, immediately before
`DynamicGI.UpdateEnvironment()`, in live per-condition code and not behind a
flag. `AssetLibrary.SetWetness` at `AssetLibrary.cs:819` is the one
implementation, and it has a long incident history attached to it about which
material properties it drives. So the three rows are not three frames measuring
an absence. They are a three-point wetness series in the engine that has the
read site and the absence in the engine that does not, and those are the two
halves the D1b comparison is for. A row that answers in one engine and names
its silence in the other is instrumentation, not padding.

THIRD, THE DIFFERENCE FROM THE SIX ROWS THAT WERE REMOVED. Those rows moved
one variable a hundredfold, produced 1.06 nulls at the statistic that matters,
were rendered in monotone order so drift and response could not be separated,
and had no null cell to read them against. These rows move a variable that one
engine renders and the other does not yet, they sit at a fixed reference cell,
and in Unreal they are additional samples of the null condition rather than
noise. That is the opposite shape.

CONDITION ON THE ALLOWANCE. The note currently says the Unreal half and not
the Unity half, which makes the row read as weaker than it is and leaves a
future session to rediscover `SetWetness`. Amendment 3, section 8, dictates the
sentence.

## 4. The null is SEVEN SAMPLES, not one pair, and C4 is amended

This is mine, it is arithmetic on field values I read, and it changes the
blocking gate the whole grid is read through.

I compared the rendering fields of every `cam_hook` condition in
`vignette-scene.json:762` to `:1070`. In UNREAL, where wetness has no read site
and the fog cap and both intensities do, these seven shots have IDENTICAL
rendering inputs:

    shot position   shot id                      condition
    5               vign_hook_day                overcast_day
    7               vign_grid_sky100_sun003      grid_sky100_sun003
    18              vign_fog_maxop0450           fog_maxop0450
    22              vign_wet_000                 wet_000
    23              vign_wet_060                 wet_060
    24              vign_wet_100                 wet_100
    25              vign_grid_null_repeat        grid_null_repeat

Every one is sun on at 3.0, sky 1.00, the same two hdri keys, fog_density
0.0120, fog_max_opacity 0.450, lanterns off, practicals off, at `cam_hook`.
`overcast_day` at `:764` agrees with `grid_sky100_sun003` at `:806` on all of
them, which is worth saying twice because it means THE JUDGED HOOK FRAME IS
ITSELF A MEMBER OF THE NULL SERIES and the run can say whether rung 1's own
frame is exposure-drifted relative to the grid.

WHAT THAT BUYS, AND IT COSTS NOTHING BECAUSE THE FRAMES ARE ALREADY BEING
RENDERED. A one-pair difference cannot tell a monotone drift from a step, which
is precisely the confound that killed the sun ladder. Seven samples at
positions 5, 7, 18, 22, 23, 24 and 25 give a SPREAD and an ordering, and the
smallest sky step in the grid should be read against the spread, not against
one difference. C4 is amended accordingly in section 9, and the spread is
max minus min over the seven, stated as such.

IN UNITY THE SAME ARITHMETIC GIVES NINETEEN. Unity applies wetness and
fog_density and ignores sun_intensity, sky_intensity and fog_max_opacity, so
every `cam_hook` row with wetness 0.60 renders the same street: the hook frame,
twelve grid cells, four fog rows, `wet_060` and the null, which is 19 of the 22
`cam_hook` shots. That is not a reason to change Unity tonight and it is the
evidence under section 6's second half.

## 5. The elevation refusal: THE BUILDER WAS RIGHT, AND RIGHT TO REFUSE

Ruled plainly, because the precedent matters more than the rows.

THE RECORD SAYS WHAT THE BUILDER SAID IT SAYS. Section 4.6 ruling 2 of the
19:46Z record: "NO ELEVATION ROWS, AND THE WITHDRAWAL IS ACCEPTED ... You
repair a defect, you do not probe a series to rediscover a number the spec
already names." Section 9 of the same record: "The count is 12 grid cells, 1
null, 4 fog and 3 wetness, which is 20 rows." There are no elevation rows in
that arithmetic. The builder quoted it correctly.

AND THE SUBSTANCE IS STRONGER THAN THE CITATION, which is the part I want on
the record, because a builder who is merely obedient to text is not what this
studio wants. Three elevation rows were IMPOSSIBLE IN THIS BATCH without
undoing the instrument the batch exists to land.

1. THE SUN'S ROTATION IS WRITTEN ONCE AT SPAWN AND NEVER REWRITTEN.
   `VignetteShot.cpp:1164` spawns it with its rotation; `ApplyCondition`
   touches colour and intensity only, `SetDirectional` at `:818` to `:826`. The
   whole-run lightAim line says so in its own stat string,
   `VignetteSpec.h:2323`: `one-per-run/the-rotation-is-written-once-at-spawn-and-never-rewritten`.
   A per-condition elevation makes that sentence false and turns the new
   instrument from a whole-run fact into a per-sample one, in the same commit
   that introduces it.
2. ELEVATION DOES NOT LIVE ON A CONDITION. It is in
   `production/specs/vignette-pieces.json` as `sun.elevation_deg`, one value for
   the scene. Three rows would need a new required condition field in both
   readers, which is the contract change the 19:46Z record had already refused
   at section 4.6 ruling 1, and which would have landed in the same batch as
   four other new or changed fields.
3. IT WOULD HAVE CONFOUNDED C15. The condition that proves the repair is "the
   sun reads pitch -36.0 and yaw 25.0, four lights of four agreeing". Rows that
   deliberately ask for other elevations make the one-line verification of the
   repair read as a mixture, on the night the repair lands.

THE PRECEDENT, STATED SO IT CAN BE CITED. A tier 3 builder MUST refuse an
instruction from a resident that contradicts a committed ruling, and must
refuse in writing, naming the section and quoting the sentence. That is what
happened and it is correct. It is the same precedent
`decision-2026-09-02-vignette-batch-canon-crews-d1-timebox.md` ruling 2 already
set in this project: "The builder was right to take the ruling over the brief;
the brief was wrong, and a brief that contradicts a ruling is corrected by the
builder, in writing, exactly as happened."

WHERE THE RESIDENT WENT WRONG, AND IT IS NOT THE FIRST ASK. Asking once is
fine: a resident cannot be expected to hold 643 lines in mind. The fault is the
SECOND ask after a written refusal citing the record. A refusal that cites a
ruling is an escalation trigger, not a negotiation: the next move is a director
spawn, which is what eventually happened, and what should have happened instead
of the follow-up. Nothing else in the resident's handling of this is criticised;
declaring the disagreement in the brief to me is exactly right.

## 6. The pre-existing red: the repair, and why it is allowed in this batch

THE FAULT IS ONE STEP WORSE THAN REPORTED AND I VERIFIED IT.
`tools/stage-vignette-scene.py:49` holds `if len(shots) != 4` inside `check()`,
which is shared by BOTH modes, so the bound is not only in `--selftest`: the
STAGING path refuses too. The workflow step at
`.github/workflows/ledger-build-windows.yml:204` to `:207` runs
`python3 tools/stage-vignette-scene.py` with no flag and carries no
`continue-on-error`, and the comment above it at `:201` says the absence is
deliberate. The live scene has 25 shots. THE NEXT DISPATCH OF THE WINDOWS BUILD
DIES AT THAT STEP, deductively, from two files I read in the working tree.

WHAT I DID NOT VERIFY: that it HAS been dying. I have no git history and no
Actions access in this spawn. The committed evidence is consistent with
something slightly different: `game-design/sim-shots/verdict.txt:1` names
commit cb4767e and lines 117 to 127 show a complete four-shot vignette with
`vignExit=0`, and every later step in that job carries `if: always()`, so a
dispatch that died at staging would still have overwritten that file with a
`NO-RUN` verdict. It did not. The conservative reading, and the one that goes on
the record, is THE BUILD WILL DIE ON THE NEXT DISPATCH and it has not been
dispatched since the ladder landed. Queue 231's "has been dying" is not
something I can confirm, and the repair does not depend on which it is.

ALSO VERIFIED: `ledger/verify.py` does not run this tool, so a green verify is
NOT evidence about this red. The repository-wide grep for
`stage-vignette-scene` hits the workflow, the tool, two docs, the gitignore and
`StreetVignetteHost.cs`, and no gate.

THE REPAIR IS RULED IN, IN THIS BATCH, AND IT IS NOT THE EROSION MOVE. The
builder's instinct was right and its conclusion was one step too cautious.
Changing a bound to make your own diff pass is the move that erodes a gate WHEN
THE NEW BOUND ASSERTS LESS. This one asserts MORE: the four judged ids by name
instead of a count that four arbitrary rows would also satisfy. The dictated
shape is in section 8, amendment 4. It is allowed in this batch because it is
one function in a tool with a selftest, because rule 12 puts a blocked channel
above everything else on the board, and because the count the bound trips on is
this batch's count.

THE SECOND HALF OF THE REPAIR IS NOT IN THIS BATCH, AND IT IS NAMED RATHER THAN
LEFT. `StreetVignetteHost.cs:166` is
`foreach (var shot in plan.Shots) yield return Shoot(plan, shot);`, so Unity
shoots EVERY row, not the four. The consequences, measured where I could:
`tools/sim-shots-commit.sh:48` stages `vign-run/sim-out/vign_*.jpg`, so all 25
frames would be committed per run, and the sixteen committed vignette frames I
read report kb=78 to kb=152, so the change is from about 0.5 MB to about 2.5 to
3.1 MB per Windows run; and the step kills the player at
`Wait-Process -Timeout 300` inside a six-minute step
(`ledger-build-windows.yml:534` and `:549`) with NOTHING MEASURED about a
25-shot wall clock, because no 25-shot Unity run has ever happened. Nineteen of
those frames would be identical, section 4. That decision is queue 231's second
half with my dictated spec in section 10, and condition C20 keeps tonight
honest about it.

GOOD NEWS, CHECKED RATHER THAN ASSUMED: the stale-frame fault does not apply.
`ledger-build-windows.yml:542` removes `vign-run/sim-out/vign_*.jpg` by that
glob before the run, and every new id begins with `vign_`, so no dead build can
inherit a probe frame and commit it as its own.

## 7. CoreTests' own equality bound, which moved to fit the diff

`ledger/CoreTests/Program.cs:19610` asserts `plan.Shots.Count == 25`. That is
the same class of bound as the python one, on the same set, and it was raised to
match this batch while the python one was refused. I am not treating those as
the same decision, and the distinction is the principle worth keeping:

A GUARD IN A BUILD-KILLING PATH ASSERTS INVARIANTS. A guard in a test asserts
the current shape, because its failure costs a red test and a sentence, not a
dead channel.

So the python bound becomes presence-by-id and the CoreTests equality may
stand, on two conditions that are already met and that I verified: it prints the
count before asserting it (`:19478`), and its failure message names the
arithmetic it encodes ("four matched shots plus the hook viewpoint plus twenty
probe rows", `:19611`). Its neighbours at `:19613` and `:19614` assert the
invariants that matter, four judged and twenty probe rows all at `cam_hook`.
The one gap is that `matched == 4` counts judged conditions at cam_A or cam_B
and would still read 4 if one pair were duplicated and another missing; the
by-id check in amendment 4 closes that in the tool, and CoreTests inherits the
shape when somebody next touches it. Not blocking.

## 8. The amendments, with the exact text

**AMENDMENT 1, BLOCKING. A1(d) LANDS IN THIS BATCH.** It was dictated by an
approved ruling and a dictated amendment is not advisory. I AM NARROWING IT,
deliberately, because the literal string in that ruling carries pixel boxes and
an `atMostPct` measured for one camera at one field of view, and freezing those
as literals inside an emit would be a measurement hardcoded where it cannot be
re-measured. The required form, in the tested layer, on the SAMPLE line of
every shot:

    shotWholeFrameIncludesControlQuads=yes/whole-frame-keys-on-this-line-include-them/boxes=see-controlQuadVisibility-and-the-quad-lines/PROJECTED-BOXES-NOT-MEASURED-COVERAGE

and on a shot whose camera hides them:

    shotWholeFrameIncludesControlQuads=no/hidden-for-this-camera

If the projected boxes ARE reachable from the tested layer on that line, print
them as `boxesPx=` computed by the same projection the tests use
(`ControlQuadPlace` and `ProjectFilePoint`), never as literals copied out of a
document. Two test cases, the accepting one first: a cam_A shot prints yes, a
cam_hook shot prints no. THE COST IS WHY THIS ONE IS BLOCKING AND AMENDMENT 2
IS NOT: `ControlQuadsVisibleFor` already exists in the tested layer
(`SurfaceBind.h`, exercised at `vignette-spec-test.cpp:1977` to `:1985`) and the
shot loop already knows its camera id, so the yes-or-no half is a call and a
constant string.

**AMENDMENT 2, RE-SCOPED ON A COST I MEASURED. NOT BLOCKING TONIGHT.** A1(a)
said the run prints the null difference; it does not, and I looked at what
making it do so would take. `VignetteShot.cpp:2299` to `:2310` measures the
three bands inside a scoped block and DISCARDS the `BandStats` at the end of it;
`:2321` keeps only the formatted string. So the engine-side form needs a
retained per-shot struct, plus a tested function deciding which conditions are
equal ON THE FIELDS THIS ENGINE APPLIES (which must exclude wetness and say in
its own string that it excludes it because `VignetteShot.cpp` has no read site
for it on this commit), plus its tests. That is tens of lines and a new
abstraction, not a formatter, and it is not what I will hold a dispatch for on
the night the sun gets fixed.

SO: the BLOCKING form is C4, the resident's arithmetic with every frame id and
every subtraction shown. The ENGINE form is required on a trigger rather than
filed into the fog: THE NEXT COMMIT THAT TOUCHES THE VERDICT-WRITING PATH OF
`VignetteShot.cpp` LANDS THE NULL-SPREAD FORMATTER. The null pair is a standing
instrument by the 19:46Z record's own words, hand arithmetic does not survive a
session change, and tonight is the third time today that one quantity acquired
different values in different documents.

**AMENDMENT 3, BLOCKING. THREE DECAYED SENTENCES THE BATCH CREATED.** Rule 1:
changing code changes the claims about it.

(a) `vignette-scene.json:1101`, the `shots_note`, says "Both engines shoot these
four ids and no others". That is now false in both engines: Unreal shoots 25 and
Unity's host loops over every row at `StreetVignetteHost.cs:166`. Replace that
clause with: "Both engines shoot these four ids and JUDGE ON THEM ALONE; the
paired judging is by id. The probe rows added 2026-09-09 are shot in addition
and are not judged pairs, and which engine renders which probe row is recorded
in game-design/decision-2026-09-09-ruling-the-grid-batch-review.md."

(b) The `grid_null_repeat` note at `:971` and the CoreTests comment at `:19617`
both say the pair sits at MAXIMUM ORDER SEPARATION with every other shot
between them. The twin is shot 7 of 25, so six shots precede it and the
separation is eighteen, not the maximum. Replace "maximum order separation on
identical inputs" with "eighteen shots apart on identical inputs, with every
condition change and every light probe between them", in both places.

(c) The three wetness notes say the Unreal half only. Add, in each:
"THE OTHER ENGINE DOES READ IT: ledger/Assets/Scripts/Game/StreetVignetteHost.cs
line 715 calls AssetLibrary.SetWetness with this field, so these three rows are a
three-point series in Unity and the absence in Unreal, which is two answers and
not one."

**AMENDMENT 4, BLOCKING. THE STAGING BOUND ASSERTS PRESENCE BY ID.**
`tools/stage-vignette-scene.py`, inside `check()`, replacing the `len(shots) != 4`
equality:

- A module-level constant `JUDGED = ["vign_camA_day", "vign_camA_night",
  "vign_camB_day", "vign_camB_night"]` with the reason beside it: two cameras by
  two conditions IS the four pairs the re-scope ruling judges on, and four
  camera positions would be eight pairs and a different bar.
- The check is: every id in `JUDGED` is present in the shot list. A missing one
  names which. The total is NOT asserted.
- The accepting print states the total so a reader sees the growth: the selftest
  line already prints `%d shots` and keeps doing so, and the staging line at
  `:89` already prints the count.
- The rejecting fixture is synthetic and must exercise THIS branch, not the
  missing-keys branch above it, because today's reject fixture `{"street":{}}`
  returns early on required keys and never reaches the shot check, which means
  the bound that is killing the build has never had a test that reaches it.
  Build a fixture that carries all twelve required keys and three of the four
  judged ids, and assert it is refused naming the fourth.
- Selftest accepting case first, on the live file, per
  `.claude/rules/instruments.md`.

**AMENDMENT 5, NOT BLOCKING, RECORDED ONLY.** This record is where the
two-engine key asymmetry is named, section 2 under A4: `fog_max_opacity`,
`sun_intensity` and `sky_intensity` are required in both readers and applied in
Unreal only; `wetness` is required in both and applied in Unity only. No reader
is loosened, nothing is worked around, and the general repair is filed in
section 10.

## 9. Conditions the resident PRINTS before committing

Nothing commits on this ruling that is not named in it. The 19:46Z record's C1
to C17 all stand except where amended here. These are the ones that are mine or
changed.

- **C1.** `python3 ledger/verify.py` green, footer pasted FROM
  `ledger/.verify-footer`, never from the scrollback.
- **C2, MINE, BECAUSE I COULD NOT RUN THEM.** The three suites re-run on the
  tree that is about to be committed and their counts pasted from the run, not
  from the brief: vignette-spec-test, frame-stats-test, CoreTests, and
  `tools/docs-check.py`. Every count in this batch's report is REPORTED until
  that paste exists. THIS RECORD IS NOT WHAT WILL TURN docs-check RED: I read
  the checker itself, `WITHIN_LINES = 8` at `docs-check.py:54`, `BANNER_RE` at
  `:84`, the LOG requirements of a date and the words NOT CURRENT at `:135` to
  `:140`, and the 400-line cap which applies only to documents whose banner
  reads LIVE, `:162` to `:190`. This file declares LOG with its date and NOT
  CURRENT on line 3, carries no em-dash anywhere, and is therefore uncapped.
- **C3.** `director_cadence` clears with this record's stamp. THE STAMP NAMES
  `2026-09-09T21:28:40Z`, `.claude/agent-log.tsv` line 494, which is the newest
  `studio-director` row in that file at the time I read it. IF THE TOOL
  ATTRIBUTES A DIFFERENT ROW TO THIS SPAWN, correct the stamp to the tool's row
  and change nothing else in this file; print the tool's own attribution line
  beside the cleared gate so the correction is visible.
- **C4, AMENDED AND STILL BLOCKING. THE NULL SERIES, SEVEN FRAMES, NOT ONE
  PAIR.** The spread over the seven identical-input frames of section 4 at
  `shotMeanLuma`, `band.ground.p05` and `band.ground.p50`, each spread smaller
  than the smallest sky step in the grid on all three, with the ids of the
  extreme pair named and every subtraction shown. If any spread is not smaller,
  THE GRID IS A NO-READ, no cell is quoted, and the resident escalates. Print
  the one-pair difference as well, because it is what the 19:46Z record asked
  for and the two numbers together say whether the drift is monotone in shot
  order.
- **C5, AMENDED DENOMINATOR.** The asked-versus-read table is 25 rows, not 12,
  because the instrument covers every shot: `cellAgree=N/of=M/read` over 25
  asked, with `shotSunIntensityAsked` beside `shotSunIntensityRead` and the same
  for sky on every sample line, and a shot whose components did not answer
  printing `nothing-measured` rather than a zero. 25 of 25 is the pass.
- **C7.** Unchanged, and add: grep the diff for `invariant` and read every hit,
  including the new `darkerThanSkyMedianPctStat`.
- **C10, AMENDED.** The `Wetness` call-site grep pasted, and it is now a
  TWO-ENGINE grep: three hits in `VignetteSpec.h` and none in
  `VignetteShot.cpp` for Unreal, and `StreetVignetteHost.cs:715` for Unity. The
  read site Unreal is missing is queue 186's work and is named, not assumed.
- **C15, BLOCKING, UNCHANGED AND RESTATED BECAUSE IT IS THE ONE THAT MATTERS.**
  The committed verdict's `lightAimStatus=AGREES` with the sun reading pitch
  -36.0 and yaw 25.0 and `lightAimAgreeing=4/of=4/read`. A run whose sun still
  reads -82.0 has not landed the fix however green the build is. Print the
  whole lightAim line, not the status word alone.
- **C18, NEW, BLOCKING.** Amendment 1's key greps in the committed diff, and
  both of its test cases read from the test output, accepting case first.
- **C19, NEW, BLOCKING.** Amendment 4's two selftest outcomes printed: the live
  25-shot scene ACCEPTED with its count shown, and the synthetic
  three-judged-id fixture REFUSED naming the missing id.
- **C20, NEW.** If the Windows lane is dispatched in this session, read and
  print `vignTimedOut` and the count of `StreetVignette: shot` lines from the
  committed verdict. `vignTimedOut=yes` or fewer than 25 shot lines makes queue
  231's second half blocking before the lane is dispatched again. If the lane is
  NOT dispatched, print that it was not, so nobody reads silence as a pass.
- **C21, NEW.** Amendment 3's three sentence edits pasted as before and after,
  and a grep for "and no others" and for "maximum order separation" across the
  repository with every hit read, because rule 1 says grep the sentence and not
  the site.

## 10. The quality ladder, and what is filed

Asked at close per `production/quality-ladder.md`: best available, or first
working? The six items' next rungs are in section 10 of the 19:46Z record and I
overturn none of them. Three more, which this review found:

- A6's next rung is now NAMED AND CHEAP: Unity prints `appliedYaw` and no
  applied pitch (`StreetVignetteHost.cs:666` to `:668`). The same axis that hid
  46 degrees in Unreal is unmeasured in Unity. One line, and it is the general
  item below made concrete.
- A1's next rung, from section 4: the null series should be DESIGNED rather
  than discovered. Seven identical-input frames arrived by accident because four
  probe families happen to share a reference cell. A run that knows which of its
  shots are null samples can print the series as a series, which is amendment
  2's engine form.
- A2's next rung is unchanged and remains the strongest one on the board: the
  rank statistic measured on BOTH pictures by one implementation.

FILED TO `production/queue/` BY NAME:

1. THE UNITY HOST RENDERS A DECIDED SUBSET, queue 231 second half. Spec: the
   host shoots the four judged ids plus `vign_hook_day` plus any row whose
   varying field THIS ENGINE APPLIES, skips the rest, and prints
   `shotsShot=N/of=M` with the skipped ids and the reason. Acceptance: the
   Windows vignette step finishes with `vignTimedOut=no` and the committed JPG
   count equals the printed `shotsShot`. Evidence for why: section 4's nineteen
   identical Unity frames and section 6's 2.5 to 3.1 MB per run.
2. ASKED VERSUS READ ON BOTH AXES IN BOTH ENGINES. The 19:46Z record filed the
   general form for Unreal actor populations; this adds that Unity's vignette
   sun prints a yaw readback and no pitch readback, which is the identical hole.
3. THE SHARED FILE'S KEYS DECLARE WHICH ENGINE APPLIES THEM. Four keys are now
   required in both readers and applied in one: `sun_intensity`,
   `sky_intensity`, `fog_max_opacity` in Unreal only, `wetness` in Unity only.
   The contract that a missing key is an error is intact; what is missing is any
   statement of which engine can act on which key, and a still from each engine
   looks fine either way. This is the same fault that contract warns about,
   facing the other way.
4. CoreTests' shot-count equality, section 7: not wrong today, and it will fail
   on the next probe row. When somebody next touches that block, `matched == 4`
   becomes a by-id presence check.

Per rule 13 the resident works these while budget and ceiling remain and arms
the resume rather than stopping on a landed batch.

<!--RULING spawn=2026-09-09T21:28:40Z-->
