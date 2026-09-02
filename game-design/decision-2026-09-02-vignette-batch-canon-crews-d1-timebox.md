# DIRECTOR RULING: the vignette batch lands with two in-batch fixes, four pairs bind, five crew names enter canon, and the D1 close is pre-registered (2 Sep 2026)

> **STATUS — LOG, 2026-09-02. NOT CURRENT once the batch is committed with the dictated edits and the two in-batch fixes applied, canon.md carries the crew and street lines, and queue items 027 to 030 exist; from then the code, canon.md, the queue and production/NOW.md are the reading copies and this file is their history.**

This document carries exactly two em-dashes: the banner above and the STATUS
line E4 dictates for another file, because `tools/docs-check.py` line 55
hard-codes that character in the regex it accepts. Named as a finding two
rulings ago and queued; not a licence.

Seventh ruling since 1 September. This role has no shell: every executed
number below is a builder's or the resident's, and my check is that the code
exists at the cited line and asserts what the number claims. The builders'
reports were not read as evidence; the diffs were. Two faults below were found
only by reading two files against each other, which is what a review is for.

## What was verified before ruling

- My own row: `.claude/agent-log.tsv` line 197, `2026-09-02T05:43:50Z
  studio-director`, the newest in the file; rows 190 to 196 are the seven
  builders of this batch.
- `game-design/decision-D1b-rescope.md` in full; line 85 reads "at least three
  of the four pairs (two cameras by two conditions)". `production/specs/
  vignette-bill-of-materials.md` in full; line 76 reads "Two cameras by two
  conditions is the four pairs the re-scope ruling judges on".
  `ledger-v2/respec/decision-register/D1-engine-probe.md` in full, line 8 the
  amendment. `production/d1-probe/plan.md`, `measurements.md`,
  `evidence-channel-spec.md`, `DISPATCH` (runs 1 to 16), `FETCH-VIGNETTE`.
- `production/specs/vignette-scene.json` in full (469 lines): the frame block,
  every furniture entry, the four shots, `not_emitted_from_this_file`.
- `ledger/Assets/Scripts/Core/StreetVignette.cs` in full (1286 lines):
  `Section` 103 to 152, `GroundAt` 206 to 247, `Foot5` 256 to 275, `Slab` 424
  to 443, `Kerbs`, `Block` (the dead local at 523), `Pitched` (the gutter
  cylinder at 765 to 770), `Aerial` (boom 815 to 820), `Columns` (the swan
  neck 938 to 951), `Kiosk` 988 to 1043, `PillarBox`, `Railing` (bars 1106 to
  1112), `Scatter`, `Optics`.
- `ledger/Assets/Scripts/Core/StreetVignettePlacement.cs` in full.
- `ledger/Assets/Scripts/Game/StreetVignetteHost.cs` in full: `Emit` 127 to
  161 (the rotation at 147 to 148, the cylinder scale at 151 to 153), `Probe`
  258 to 282, `Apply` 313 to 375 (the sun at 327 to 328), `Shoot` 377 to 463.
  `Bootstrap.cs` 43 to 55, `SimDirector.cs` 36 to 60.
- `ledger/CoreTests/Program.cs` 19238 to 19506: the series print at 19346 to
  19347, the bound at 19354 to 19382, the placement fixtures. Line 258 for
  `card.Section`.
- Every symbol the Host calls, found at its declaration: `AssetLibrary`
  constants 29 to 41 (all thirteen surfaces the JSON names are constants),
  `Material` 347, `Opaque` 364, `SetWetness` 814, `SceneLighting.ApplyQuality`
  158, `TextureFit.Isotropic` 47 to 64, `Dressing.Roll` 216, the five
  `MiniJson` readers, `SkyEnvironment.LoadRoot` 60 (`Sky/polyhaven/`, the
  JSON's prefix), `Assets/Editor/SkyImport.cs` 30 (cube import), the four
  `.hdr` files on disk.
- `ledger/ReachCheck/Program.cs` 55 to 369: the `--also` walk at 150 to 152,
  the fully qualified owner at 164 to 166, the by-name graph at 250 to 292,
  the grade at 312 to 315, `stillOwed` and `stale` at 354 to 355.
  `tools/reach-check.sh` in full. `ledger/ReachCheck/allow.json` in full.
  `ledger/verify.py` `reach` 242 to 270, `verdict_keys` 1843 to 1882.
  `.claude/hooks/verify-gate.sh` in full: no footer, no commit (169 to 175).
- `ue-probe/Source/LedgerProbe/Private/LedgerProbe.cpp` in full (730 lines),
  `Public/FrameStats.h` in full, `tests/frame-stats-test.cpp` in full (25
  checks counted by hand: 9, 2, 3, 4, 3, 4), `LedgerProbe.Build.cs`
  (`ImageWrapper` is a private dependency, line 18), `Config/DefaultEngine.ini`.
- `.github/workflows/ledger-probe-unreal.yml` in full (the capture step 541 to
  681, the commit step 686 to 767), `ledger-vignette-fetch.yml` in full,
  `ledger-build-windows.yml` 1 to 110, 190 to 215, 470 to 610. The trigger
  block of every workflow by grep: three self-hosted workflows fire on a
  sentinel push, the Unity build on `workflow_dispatch` only, none carries a
  concurrency group. `tools/sim-shots-commit.sh` 175 to 215,
  `sim-shots-stage.sh` 207 to 212. `tools/runner/python3-shim.sh` and
  `bootstrap-paths.cmd` exist. `fetch_vignette.py` carries `--plan --probe
  --fetch --verdict --staged-files --steps` (580 to 591).
- `tools/props/make_vignette_2d.py` 1 to 205 and 280 to 444; the puddle series
  at 186 to 188; `build()` sets the legend from `districts[0]` at 290.
  `production/assets/vignette/decals2d/ATTRIBUTION.json` in full (8 checked, 0
  blank, legend `the Hook` on all three plates).
- `canon.md` in full, `game-design/canon-proposal-graffiti-crews.md` in full,
  `production/queue/025` in full, `production/quality-ladder.md`,
  `production/NOW.md`, `production/budget.md`, the previous ruling.

## Ruling 1: the batch LANDS, as one commit, after two in-batch fixes and the dictated edits

The scene, the placement instrument, the Unity emitter, the UE capture path,
the fetch workflow, the five deterministic images and the crew proposal are
each the best version this container can produce of what was asked, and each
says at its seam what it could not run. Nothing weakens an instrument. Two
instruments that did not exist now do: a placement metric in two halves with
the half that finds holes printed first, and a blank rule that is structural
rather than tuned.

**But the batch cannot be committed as it stands, and not because of a
judgement.** `ledger/verify.py` is red on `reach`, a red run deletes the
footer, and `.claude/hooks/verify-gate.sh` line 169 blocks `git commit` with
no footer. Rule 2 forbids moving that gate. So the reach red is fixed inside
this batch (Ruling 8), and a second fault I found by reading (Ruling 3) is
fixed in the same batch because dispatching without it would spend a Unity
round trip on a frame that cannot be right. One commit, because the first
commit that touches the reviewed scope moves the reference past my row and a
second scope-touching commit would then be unruled.

**Order of work, and it is an order:**

1. The resident applies the dictated edits E1 to E5 below by hand. E1 alone
   may turn `reach` green (Ruling 8 explains why); run verify and read the
   reach line either way.
2. In parallel, two builders, both covered by this row: an engine-specialist
   for the geometry convention (Ruling 3, the brief is there) and, only if
   step 1 leaves the three Editor-only APIs red, an instrument-builder for
   ReachCheck (Ruling 8, the brief is there).
3. Verify green. Commit, staged by name: the new files
   `production/specs/vignette-scene.json`,
   `ledger/Assets/Scripts/Core/StreetVignette.cs`,
   `ledger/Assets/Scripts/Core/StreetVignettePlacement.cs`,
   `ledger/Assets/Scripts/Game/StreetVignetteHost.cs`,
   `tools/stage-vignette-scene.py`,
   `ue-probe/Source/LedgerProbe/Public/FrameStats.h`,
   `ue-probe/tests/frame-stats-test.cpp`,
   `.github/workflows/ledger-vignette-fetch.yml`,
   `production/d1-probe/FETCH-VIGNETTE`, `tools/props/make_vignette_2d.py`,
   the eight PNGs and `ATTRIBUTION.json` under
   `production/assets/vignette/decals2d/`,
   `game-design/canon-proposal-graffiti-crews.md`, this file, the queue
   items of Ruling 10; and the modified files `Bootstrap.cs`, `SimDirector.cs`,
   `CoreTests/Program.cs`, `ledger-build-windows.yml`,
   `ledger-probe-unreal.yml`, `tools/sim-shots-commit.sh`,
   `tools/sim-shots-stage.sh`, `ledger/.gitignore`, `LedgerProbe.cpp`,
   `LedgerProbe.Build.cs`, `production/d1-probe/DISPATCH`, `canon.md`,
   `production/queue/025-step-4a-seven-images.md`, `production/NOW.md`,
   `production/quality-ladder.md`, plus whatever the two builders touched
   (named in their reports and read by the resident before staging). Never a
   `__pycache__`, never `ledger/Assets/StreamingAssets/Vignette/` (ignored by
   design, `.gitignore` line 73).
4. The commit message quotes, from runs made AFTER every edit: the CoreTests
   count, the `placement pieces=... probes=... datumMissing=0/...` line and the
   `worst foot gap` line, `frame-stats-test: 25 check(s), 0 failure(s)`, the
   `make_vignette_2d` line `8 file(s) written of 8 attempted, 0 blank`, the
   `stage-vignette-scene --selftest` line, and the `reach ok` line. Never the
   briefs' numbers.
5. Push. That push touches two sentinels and fires two self-hosted jobs
   (Ruling 7). In the same window, dispatch `ledger-build-windows.yml` on the
   branch. Then pull before anything else: three CI commits will land on the
   branch.

**Dictated edits, exact text, nothing judged at apply time:**

E1. `ledger/Assets/Scripts/Core/StreetVignette.cs`, four single-token
replacements of the nested type name (the reason is Ruling 8):

- line 103: `public sealed class Section` becomes
  `public sealed class StreetSection`
- line 167: `public Section Sec;` becomes `public StreetSection Sec;`
- line 314: `var sec = new Section` becomes `var sec = new StreetSection`
- line 1081: `Section s, double sgn, string side)` becomes
  `StreetSection s, double sgn, string side)`

`StreetSection` occurs nowhere in `ledger/Assets/Scripts` today (grep, this
session). CoreTests reaches the type only through `plan.Sec` (line 19247) and
needs no edit.

E2. `StreetVignette.cs` line 523, a dead local: replace
`double depth = Num(blk, "depth_m"), wall = Str(blk, "wall_surface") == null ? 0 : 0;`
with `double depth = Num(blk, "depth_m");`

E3. `canon.md`. After line 13 (`- Streets minted: Quay Street, Weighhouse
Lane, Tannery Row.`), which stays EXACTLY as it is because
`tools/props/make_vignette_2d.py` line 77 parses it by that prefix, insert:

```
- Street districts, minted 2026-09-02 by the director on delegated authority,
  struck on sight if Jafar disagrees: Quay Street is in the Hook, Weighhouse
  Lane in Copper Row, Tannery Row in Ironside.
- Graffiti tags, minted 2026-09-02 (Jafar delegated the naming to the studio
  on 2 September): TANNER (Ironside), SNIDE (Copper Row), GULL (Gullwing),
  QUAY FIRM (the Hook), PARADE RATS (the Parade). Wall names, not any of the
  three rival organisations; reasoning in
  game-design/canon-proposal-graffiti-crews.md.
```

And on lines 58 to 59, replace `The brand bible still owes: the football club,
the local paper, the pirate radio station, the regional TV channel.` with
`The brand bible still owes: the football club, the local paper, the pirate
radio station, the regional TV channel, the telephone operator (the kiosk's
mark and lettering) and the postal cypher (the pillar box); the last two were
found owed by the vignette bill of materials on 2026-09-02.`

E4. `game-design/canon-proposal-graffiti-crews.md` lines 3 to 5 (the STATUS
banner) become one line:
`> **STATUS — LOG, 2026-09-02. The five names entered canon.md under game-design/decision-2026-09-02-vignette-batch-canon-crews-d1-timebox.md; this file records their reasoning and is not current once canon carries them.**`

E5. `production/d1-probe/FETCH-VIGNETTE` line 18: `run 1 - 2026-09-02 - not
yet dispatched. The first run answers four things in` becomes
`run 1 - 2026-09-02 - dispatched with the vignette batch. The first run answers four things in`

## Ruling 2: two cameras by two conditions IS the four pairs, and that reading binds

Confirmed, explicitly, because it is the standard D1 is judged by. The
re-scope ruling defines "decisively better" as UE preferred "in at least three
of the four pairs (two cameras by two conditions)", line 85 of that file, and
the bill of materials says the same at line 76. Four camera positions by two
conditions would be eight pairs and a different bar. The builder was right to
take the ruling over the brief; the brief was wrong, and a brief that
contradicts a ruling is corrected by the builder, in writing, exactly as
happened. The four ids are `vign_camA_day`, `vign_camA_night`,
`vign_camB_day`, `vign_camB_night`; both engines shoot those and no others;
judging pairs by id. `stage-vignette-scene.py` line 49 and CoreTests 19296
both refuse any other count, which is the right place for the bar to live.

## Ruling 3: the placement derivation is sound and the bound is set correctly; the EMITTER has a rotation fault the plan-side probe cannot see, fixed in-batch

**The derivation.** A level box on a footway falling 1 in 40 lifts its
upslope corner by half its footprint times 0.025: kiosk 0.914 gives 0.0114,
pillar box 0.597 gives 0.0075, dustbin 0.460 gives 0.0058, printed 0.011,
0.007, 0.006. Three objects, three agreements to the millimetre. That is a
model confirmed by a series, not a number chosen first, and the bound
(widest footprint through the same arithmetic plus one millimetre of print
rounding, 0.0124 m) was set AFTER the print. Rule 2 satisfied.

**What the bound cannot see, named so nobody reads it as tighter than it
is.** It is one scalar over the whole scene. A dustbin floating 10 mm
(expected 5.8) passes under a 12.4 mm bound. The next rung is a per-probe
expectation: each foot's expected gap is its offset along the slope times the
crossfall (zero at the centre), asserted to 1 mm per probe. That also stops
the next wider footed piece (a bench, a shelter) from tripping a global bound
and somebody raising the number, which is the ratchet shape. Ladder row, not
a landing condition.

**The 11 mm is real geometry.** A kerbside object is bedded level and the
paving comes up to it; here the slab is one tilted box, so the kiosk's
upslope corner shows a 11 mm line of light and its downslope corner is
buried. The rung is one line in Core: bed footed furniture at
`footY = gy - halfFootprint * crossfall`, after which the instrument should
read floatMax near 0 and sinkMax near 0.022, which is the proof it worked.
Ladder row; look at the first frame before tuning 11 mm (rule 4).

**The half it cannot prove, and the fault it would have found one round trip
late.** The plan-side probe compares the plan with the plan. The engine-side
probe (`StreetVignetteHost.Probe`, raycasting real colliders) has never run.
Reading the emitter against Core, it would have failed loudly on its first
run, because the emitter rotates every default-yaw piece by ninety degrees:

- Core's convention is explicit: at `YawDeg = 0` a piece's `SX` runs along
  the street (`Slab` line 440 sets `SX = x1 - x0`; `KerbPiece` sets `SX =
  len`; `Block` sets `SX = bw`; `Foot5` line 266 swaps the half-extents only
  at 90). Yaw 0 is the identity.
- The Host, line 147 to 148, applies `Quaternion.Euler(pitch, 90 - yaw, 0)`
  to every piece. Unity's `Euler(0, 90, 0)` sends local +x to world -z. So
  every ground slab becomes 42 m ACROSS the street and 2.7 m along it, every
  kerb block lies across the kerb line, every bay is 6 m deep and 8 m wide,
  and the camber tilts along the street instead of toward the gutter. The
  ninety was copied from the camera conversion, which is correct for a
  camera (a facing) and wrong for a box (a frame).
- The horizontal cylinders are a second, independent fault: the gutter
  (`SX = len, SY = gd, SZ = gd`, line 767 to 769), the aerial boom, its
  elements and the rail bars are emitted with the axis still vertical, so
  each is a flattened disc stretched along its length, not a pipe. The
  emitter never rotates a cylinder's axis and Core never asks it to.
- The kiosk and pillar box carry `yaw_deg: 180` in the JSON and the Core
  never reads the field; the JSON's own kerb note calls a field the emitter
  ignores "a lie about what the still shows".
- The sun (Host 327 to 328) hands the JSON's bearing straight to Unity's yaw.
  The frame block says +x is north and +z east, so a bearing is a compass
  bearing; a facing at bearing b is Unity yaw `90 - b` (the camera's own
  conversion); the light FACES away from the sun, bearing `azimuth - 180`;
  so Unity yaw is `270 - azimuth`. Harmless in an overcast frame beyond
  shadow direction, and wrong.

**Brief for the engine-specialist, in the batch:**

1. Core `Piece` gains `RollDeg` (about +z). Lying pipes are expressed as
   cylinders with the axis along local y and rolled: gutter, rail bars and
   boom become `SX = d, SY = length, SZ = d, RollDeg = 90, YawDeg = 0` (axis
   along the street); aerial elements become `SX = ed, SY = el, SZ = ed,
   PitchDeg = 90` (axis across). The swan-neck segments are already right
   (vertical axis, pitched about x toward the road; the sign was checked).
2. Host `Emit`: `Quaternion.Euler((float)p.PitchDeg, -(float)p.YawDeg,
   (float)p.RollDeg)`. The minus is the scene's bearing sense (0 faces +x,
   90 faces +z) against Unity's, and yaw 0 is now the identity Core assumes.
   The camera keeps `90 - yaw` (a facing). The sun becomes
   `Quaternion.Euler(elevation, 270 - azimuth, 0)` and the Host logs one line
   `sun elevation=.. bearing=.. unityYaw=..` so the day frame's shadow can be
   read against it; that conversion stays UNVERIFIED until the day frame is
   opened.
3. Delete the two `yaw_deg` fields from the kiosk and pillar-box furniture
   entries in the JSON (the door already faces the street through `sgn`).
4. A CoreTests guard, rejecting case FIRST on the live tree: every `cyl`
   piece has `SX == SZ` (a cylinder is one diameter both ways; the length is
   `SY`). Today the gutter fails it. Then the fix, then the accepting run,
   and both outputs quoted in the report. And print, once per plan, the
   count of pieces per shape and how many carry a non-zero roll, so the
   verdict can say how many pipes were laid.
5. Do NOT touch `Foot5`, the section arithmetic, the placement formatter or
   the bound. The engine-side probe on the first Unity run is what proves
   this fix; if it reports `datumMissing` above zero or a float the crossfall
   does not explain, that is a finding about the emitter and the run is not
   evidence about the plan.

## Ruling 4: the kiosk and the pillar box ship unlettered and crownless, and that is correct

The builder's judgement stands: an unlettered kiosk is incomplete, a lettered
one is a canon violation (every brand fictional, `canon.md` line 55), and the
Meridian telephone operator has never been minted. The bill of materials said
exactly this at lines 233 to 243 and the JSON note repeats it. The colour is
the accent budget and the colour is there; the mark is a decal line once the
brand exists. Both brands go on the owed list now (E3) and to a
dialogue-writer as one proposal, the same route the crews took (Ruling 10,
item 030). Not a landing condition and not a blocker on the first pairs.

## Ruling 5: the UE capture path lands unrun, and run 16 is the measurement

Read against 5.x signatures: `FScreenshotRequest::RequestScreenshot(FString,
bool, bool)`, `FTSTicker::GetCoreTicker().AddTicker`, `IImageWrapper::
GetRaw(ERGBFormat, int, TArray64<uint8>&)`, `IFileManager::FindFilesRecursive`
with six arguments, `DrawDebugBox` and `DrawDebugLine` with eight,
`AddOnScreenDebugMessage(uint64, float, FColor, FString)`,
`FPlatformMisc::RequestExit(false)`. All plausible; none provable here, and a
5.8 drift fails the whole probe including the golden test. That is the named
risk and it is accepted, because the alternative (not dispatching) measures
nothing. `ImageWrapper` is in the module's dependencies (Build.cs 18), which
was the link error most likely to take the golden test down with it.

What is proven is the arithmetic and the words: `Measure` and `DoneLine`
compiled and run by g++ here, 25 checks, the uniform-grey rejecting case that
a file-exists check and a non-black check would both pass, and
`NOTHING-MEASURED` for a frame with no pixels. The blank rule is structural
(`distinctBuckets <= 1 || nonBlack == 0`) and sets no brightness bound, which
is right: no series exists.

Run 16 decides one thing: does `shotStatus=WROTE` land in a committed
`ue-shot-verdict.txt` naming the batch commit. The workflow's step exits 1 for
BLANK, UNDECODABLE, NO-FILE and NO-VERDICT with the evidence committed either
way, and the commit step replaces any verdict not carrying this commit's
seven-character prefix with NO-RUN. Both outcomes are readable. Rule 12 holds.

## Ruling 6: the canon decision on the five names, one by one

Judged on `canon.md` lines 23 to 25: grounded noir, dry British wit,
tabloid and Viz-adjacent, never GTA-style American satire, 1988 to 1992.

- **TANNER, Ironside.** Enters. A trade name taken as a wall name by the
  trade's own kids; a place, not a slogan. The older ear also hears the old
  sixpence, which costs nothing and reads right for the period.
- **SNIDE, Copper Row.** Enters. Period market slang for counterfeit, worn
  as a signature by a stallholder's lad. A single writer rather than a crew,
  which is the more honest 1988 shape anyway.
- **GULL, Gullwing.** Enters. Plain, dry, faded-resort. Two real clubs are
  nicknamed for the bird; a bird is not a mark and nobody owns it. Noted,
  not a strike.
- **QUAY FIRM, the Hook.** Enters, and it is the most period-loaded of the
  five: "firm" in these years is the football following's own word, which
  is exactly right for dockers' sons at the ferry queue, and it implies a
  club canon already owes. It also names Quay Street as the Hook's street,
  which E3 now mints rather than leaves implied.
- **PARADE RATS, the Parade.** Enters. The doormen's word for skint kids,
  worn as a badge: specific, British, wry. It is the one closest to a
  costume by shape (an "X Rats" template) and the origin is what keeps it a
  voice.

None fails the tone law; none is American; none is a real crew, place or
trademark as far as this container can check (no web check was made for the
five as graffiti names; the licence and trademark exposure of a five-letter
word on a wall texture is nil). All five enter `canon.md` by E3, on the
authority Jafar delegated on 2 September, with the standing line that he
strikes any of them on sight.

**Two consequences the proposal did not see.** First, the tag names are not
the rival organisations (Vane, Kest, Ro); canon says so in E3 so a later
writer does not merge them. Second, the deterministic plate generator stamped
`the Hook` as the district legend on all three street plates
(`make_vignette_2d.py` line 290 takes `districts[0]`; the manifest confirms it
on every plate), because canon did not map streets to districts. Two of the
three plates on disk are therefore wrong evidence: a tannery row is
industrial and a weigh house stands in a market. E3 mints the map; item 028
reads it and regenerates; no plate binds into a scene before then. The
emitter binds no plate today, so nothing false reaches a frame.

## Ruling 7: two sentinel workflows and one dispatched build queue on one runner, and that is a wait, not a hang

The push carrying this batch changes `production/d1-probe/DISPATCH` (run 16)
and creates `production/d1-probe/FETCH-VIGNETTE` (run 1), so it fires
`ledger-probe-unreal.yml` and `ledger-vignette-fetch.yml` at once. The Unity
build fires on `workflow_dispatch` only and is dispatched by hand in the same
window. All three run on `[self-hosted, ledger-pc]`, none carries a
concurrency group, and one runner process runs one job at a time. They
land together, serially, in an order GitHub chooses.

What the resident should expect rather than read as a hang: the second and
third jobs show Queued until the one ahead finishes; a healthy probe is about
15 to 30 minutes (build 0.75, cook 2.0 plus 0.45, test, capture up to 15), the
fetch single-figure minutes, the Unity job about 29 plus up to 6 for the
vignette step; so roughly 60 to 80 minutes for all three, and a job is hung
only when it passes its OWN `timeout-minutes` (115, 40, 110). Watch by
ancestry: three landed commits whose parent chain contains the batch sha,
titled `UE machine probe from`, `vignette surfaces from`, and the sim-shots
commit. Each pulls and rebases before pushing, so the branch moves three
times; pull before the next local commit. Rule 9 is satisfied: the round
trip costs the same carrying one change or six, and this push carries the UE
capture, the fetch and the Unity vignette at once. The scaffolding (sentinel
plus push trigger) is deleted when the workflows reach `main`, and not before
14 September.

## Ruling 8: the reach red does not land over; one half is this batch's doing, the other half is instrument-first

**`CharacterCard.Section` PAID OFF is a false pay-off caused by this batch.**
`ReachCheck` walks the Core call graph by NAME (Program.cs 250 to 292,
documented there as a deliberate over-approximation). `StreetVignette.Read`
is live (the Host calls it), its body says `new Section {`, so the bare name
`Section` enters the live set, and `CharacterCard.Section` (a method on the
ledger, `allow.json` line 69) reads as reached. Its entry then looks stale
and the tool says PAID OFF. Nothing wired it; the collision did. E1 renames
the nested type to `StreetSection`, which removes the collision at its
source. The over-approximation is the documented, correct direction for the
gate to be wrong in (under-report), and it is not changed; a false PAID OFF
is the one shape where it errs the other way, and the tool should say so:
the instrument-builder, if spawned, adds one line to the stale report naming
whether the pay-off came through a qualified Game call or through the
by-name walk, so the next collision reads as a collision.

**The three unreached APIs are instrument-first.** `Proportion.
TryNeckFraction`, `Proportion.IsCaricature` and `BodyArchetype.
ControllerName` are all called from `ledger/Assets/Editor/CharacterPrefab.cs`
(lines 209, 215, 720, read this session), the invocation passes `--also
ledger/Assets/Editor` (reach-check.sh line 34), and the parser takes the
owner from a fully qualified call correctly (Program.cs 164 to 166). A tool
reporting those three unreached is a tool not seeing that directory in the
resident's run, and I cannot see why from here. I did not verify the claim
that they pre-date the batch; the measurement below answers that too.

The cheapest decisive measurement, by the resident, before any builder:
`bash tools/reach-check.sh --series | grep -E "TryNeckFraction|IsCaricature|ControllerName|CharacterCard.Section"` after E1, and once more in a clean
worktree at `d6b37750`. Then:

- Grade `strong` after E1: done, no builder.
- Grade `none` with the file present: an instrument-builder makes ReachCheck
  print, on every run, `consumers: game=N file(s), also=M file(s) from K
  dir(s) (D1, D2...)` and per-file parse diagnostic counts for the consumer
  set, because "0 unwired" over a directory that was silently not walked is
  the zero this project keeps being fooled by (rule 3b). Read that print,
  fix what it names (a stale `bin/obj`, a path, a parse failure under
  `LanguageVersion.CSharp9`), fixture both outcomes.
- NEVER an allow entry for any of the three: they are called, and a ledger
  entry for a wired API is the mute button the ledger's own header forbids.

## Ruling 9: the 123 pending verdict keys are not this landing's

`verdict_keys` is green with `new (run --learn)` appended; it blocks nothing.
The keys are from the last landed run (`4165bf5`, which predates this
batch), so learning them is a decision about a manifest, and the tool says
growth is a decision. It happens in its own evidence commit after the batch
push, never inside it: the resident runs the tool, reads the 123 names
grouped by prefix, and learns them if every group traces to an instrument
that landed on 1 September; if any name looks like a per-run identifier (a
sha, a timestamp, a victim's name), it does not learn and resumes this
director. The commit message quotes the manifest count before and after.
After the first vignette build lands, the `StreetVignette:` lines add their
own keys (`datumMissing`, `frameMedianMs`, `landed`, `gapMedian`, and the
rest) and the same rule applies then. `StreetVignette: ` is not among
`keys_in`'s line prefixes (verdict-keys.py 94 to 97); the keys themselves
would go GONE if the lines vanished, which is adequate, and adding the prefix
is one line for whoever next touches that file.

## Ruling 10: the queue, ordered against 2026-09-14

**The scene as landed is not yet an admissible (b) scene, and this is the
first thing the refill has to say.** The re-scope ruling's mandatory contents
include "at least one clothed character body" (D1b line 70; the bill of
materials marks F1 MANDATORY with eighteen bodies HELD). `vignette-scene.json`
places none and neither emitter has a line for one. The first frames are
still wanted, because the ground, the light and the wet response are the D8
questions and a body is one placement; but no pair is judged until both
engines carry the body. That is a data block (`figures`: which held body,
which idle clip, x, z, facing) plus one placement per engine, and on the UE
side it is precisely the binary-asset friction D1b Ruling 4 wanted (b) to
catch.

Amended in place:

- **025** gains a section `RULED 2026-09-02`: G7 is UNBLOCKED (canon carries
  five names); its route stays deterministic; and E10 gains the finding that
  all three plates carry `the Hook` and must be regenerated from canon's new
  street-districts line before any binds. Both are item 028's work.

New items, next free number 027:

- **027-ue-vignette-emitter.md** (engine-specialist, max 3 sessions, the
  critical path). Phase A: a flat piece list emitted by the tested Core
  layout (a CoreTests or tool step writing `production/specs/
  vignette-pieces.json`: every `Piece` with bom, name, shape, surface,
  centre, size, pitch, yaw, roll, emissive, plus cameras, conditions, shots
  and lamp colour) committed with a drift guard that regenerating it changes
  nothing and that its count equals the Unity plan's `pieces=`. The UE
  emitter reads THAT, not the JSON, so the two engines cannot disagree on
  layout and every difference in a pair is a renderer difference. This is
  admissible by construction: every object still arrives from the shared
  JSON through a generator, and the generator is the one that is tested.
  Phase B: engine basic shapes, point lights at the emissive pieces, the two
  conditions as fog, sky-light and a directional light, the four named shots
  at 1280x720 through the run-16 capture path generalised to a list, one
  verdict line per shot with the frame time as a median over the same
  warm/timed counts the Unity host uses (8 and 24), all untextured. Phase C:
  materials, which is the unknown: runtime import of the allowlisted maps
  into textures and dynamic instances of a base material with texture
  parameters; the base material is made by an editor script run in the cook
  step (a build product, in git), never by hand. Phase D: the character body
  (Ruling 10's first paragraph). Each phase is one dispatch and each dispatch
  line in DISPATCH names what it will prove. The UE builder's own three
  follow-ups were not carried to me by name; the resident appends them to
  this item verbatim and they wait behind it.
- **028-vignette-figure-plates-and-tags.md** (content-wrangler first, then
  engine-specialist, max 2 sessions). The `figures` block in the JSON with
  one held body and one accepted idle clip, sizes from the fbx manifest and
  never invented; the Unity placement through the existing character path;
  `make_vignette_2d.py` reading canon's street-districts line for the plate
  legend, regenerating the three plates, and the G7 generator (twenty tags
  off five names, marker and chrome variants, deterministic); every image
  under `decals2d/` OPENED and the manifest's `review` line changed from
  `pending` to a dated sentence naming what was looked at (rule 4).
- **029-verdict-keys-and-vignette-prefix.md** (resident, no spawn). Ruling
  9's learn, in its own commit, and the `StreetVignette: ` prefix added to
  `keys_in` on the next touch of `verdict-keys.py`.
- **030-telephone-operator-and-postal-cypher.md** (dialogue-writer, one
  session). One proposal file in the shape of the crews: the Meridian
  telephone operator's name and the mark that replaces the crown, and the
  postal cypher; tone law, no real mark, 1988 to 1992. Enters canon by the
  same delegated route, and then the kiosk and box gain a decal line each.

What waits, and why: every visual rung (Ruling 11's ladder rows) waits for a
frame to exist, because tuning 11 mm or a tiling scale before a picture is
tuning blind; the C11 lit-interior diffusion batch waits for Jafar's one
click on the PC watcher and is a rung, not a blocker; the sentinel cleanup
waits for `main`; queue 020 to 024 and 026 keep their places behind 027 and
028 until 14 September, because nothing in them moves the four numbers the
timebox is measured on.

## Ruling 11: is the Unreal side going to produce a frame in time, and what does D1 decide on

**The honest estimate, per rule 7.** A frame of any kind from UE (the grey
box and debug lines of run 16): likely within one to three round trips, if
the 5.8 signatures hold; what dominates is a compile the container cannot
run, and what blows it up is one drifted signature failing the whole probe.
A textured frame of the shared scene through the UE generator, which is
what an admissible pair needs: unlikely inside the box. What dominates is
blind C++ against a 20-minute loop with no local compiler, across four
phases none of which has run; what blows it up is Phase C, runtime materials
in a project with no content, and the character import behind it. The
whole UE path to date took 16 dispatches over two days to reach build, cook,
test and verdict with two source files. The emitter is larger than all of it.

**What D1 decides on, framed for Jafar because it is his call.** The rule as
re-affirmed twice: "if the UE side cannot be measured, D1 closes UNRESOLVED,
never Unity wins". Three readings of 14 September with no UE pair:

1. **UNRESOLVED as written.** The engine stays OPEN, work continues in Unity
   by momentum. What it sacrifices: an open question answered by drift.
   Every week in Unity raises the switching cost, so "open" decays into
   "Unity" without anyone having decided, which is the thing the rule was
   written to prevent and would now be causing.
2. **Pre-registered friction reading (recommended).** D1's own rule says
   Unreal wins only if (b) is decisively better AND (a) is tolerable for
   autonomous operation, and (a) is defined as cycle time and the failed-edit
   rate on binary assets. Every tool on the UE side is installed and proven
   (engine, toolchain, cook, verdict channel). If, with all of that, the
   autonomous pipeline has not committed one UE still of the shared scene
   with textured surfaces from its generator (`shotStatus=WROTE` on a
   `vign_*` id, materials from allowlisted files) by 2026-09-12 12:00Z, then
   (a) reads NOT TOLERABLE on the measured series (dispatches spent, edits
   failed, the phase it stopped at) and D1 closes UNITY on its own clause,
   with (b) recorded as unmeasured and why. This is distinct from "cannot be
   measured": that phrase was written for an external blocker (a launcher,
   a licence), and a pipeline with everything installed that cannot reach a
   textured frame in ten days IS the friction measurement. The criterion is
   written down now, before any run, so it is a measurement and not taste
   after the fact. The two days of slack are for the close-out record.
3. **Extend the box.** Jafar ruled no extension. An extension without a new
   hypothesis is more of the same and I do not recommend it.

My recommendation is 2. It is strategic and the owner decides; the resident
puts it to Jafar in one line with the recommendation, and records his words
in the D1 register beside the amendment when he answers. Until he answers,
the work is identical under 1 and 2.

**And the Unity side is wanted whichever way this falls.** The scene JSON
and the Unity emitter are the first slice of the data-driven world pipeline
Phase 0 needs regardless; the four Unity frames establish the Unity ceiling
as a fact; and the placement instrument's engine half is the first gate on
the emitter. Item 004's note stands: this half alone cannot decide (b), and
"Unity wins on visuals" must never be written from it.

## Quality ladder, rows dictated into `production/quality-ladder.md`

Under a new heading `## The D1b vignette scene (data, engine-neutral)`,
because these rows describe the shared JSON and the tested layout, which
survive the engine decision and are therefore not the "everything visual
waits" the file records:

| aspect | current rung | next rung, from resources we have |
|---|---|---|
| Kerb | square 125 mm face, 915 mm blocks, gully recess cut to the measured grate | the 12 mm batter over the top 50 mm named in the JSON's kerb note, as a chamfer piece per block |
| Footed furniture | level on a 1 in 40 footway, 11 mm upslope corner float, measured | bedded: `footY = gy - halfFootprint * crossfall`; proof is floatMax near 0 and sinkMax near 0.022 on the same instrument |
| Placement bound | one scalar, widest footprint through the crossfall arithmetic | per-probe expected gap asserted to 1 mm, so a 10 mm float under a dustbin is seen |
| Crossover | kerb drops, footway does not ramp (125 mm over 2 m, named in Core) | ramp the footway over the crossover width |
| Surface tiling | WorldBuilder's 3 m and 3.5 m copied | each ambientCG set's stated physical size read at fetch and written into `surface_tiling` |
| Skies | 2K, the fetched rung | 4K, one path segment away, if the two slugs publish it |
| Kiosk and box | silhouettes at trade size, unlettered | operator mark and postal cypher as decals once item 030 lands |
| Night interiors | held `interior` material on the card | C11 cards from one `make-the-pictures` dispatch |
| Character | none placed (not yet admissible) | one held body with an idle, item 028; period wardrobe stays the research row the BOM named |
| HDRI binding | Host binds its own cube, same idiom as `SkyEnvironment` | one implementation: the Host calls `SkyEnvironment`'s loader, after the first frame |

## Deliberately not decided

- The engine. Ruling 11 frames the close; it does not make it.
- Any frame-time bound, any fog or wetness bound: the JSON names these as
  the first values of series never printed, and the first four frames print
  them.
- Whether the by-name graph walk in ReachCheck should key on (owner, name).
  It over-approximates in the safe direction by design; one false PAID OFF is
  a print to add, not a redesign.
- Whether the shared flat piece list should replace the JSON as the Unity
  emitter's input too. It would remove the last place the two engines could
  disagree; it is also a second reader to maintain. After the first pair.

## For the next session in one line each

- Apply E1 to E5; run verify; read the reach line; run Ruling 8's grep.
- Spawn the engine-specialist for Ruling 3 (and the instrument-builder only
  if the grep says `none`), after one usage number from Jafar.
- Commit once, staged by name, numbers from post-edit runs; push; dispatch
  the Unity build in the same window; pull after the three CI commits land.
- Read run 16's `ue-shot-verdict.txt` and the Unity `StreetVignette:` lines
  for `datumMissing` and `floatMax` BEFORE opening any still, then open all
  four stills (rule 4).
- One line to Jafar: the five crew names and three street districts are in
  canon on his delegation (strike any on sight); the D1 close reading
  (Ruling 11, recommend 2); a usage number.
- Learn the 123 keys in their own commit (Ruling 9).
- Update NOW.md: two builders in flight on the batch, three CI runs to watch
  by ancestry, 027 next, the D1 question waiting on Jafar.

Spawn row, quoted verbatim from `.claude/agent-log.tsv` (line 197):

    2026-09-02T05:43:50Z	studio-director

<!--RULING spawn=2026-09-02T05:43:50Z-->
