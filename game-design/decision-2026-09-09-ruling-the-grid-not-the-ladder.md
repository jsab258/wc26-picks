# Ruling: the grid, not the ladder, and the sun that was 46 degrees from where the spec asked

> **STATUS: LOG, 2026-09-09. NOT CURRENT** once the conditions in section 8 are
> met and the batch is committed. Director ruling at spawn
> 2026-09-09T19:46:49Z, `.claude/agent-log.tsv` line 485. A SIMULATION change
> and a landing that changes a conclusion, so the escalation is mechanical
> rather than judged.
> BUILDS ON `game-design/decision-2026-09-09-ruling-the-settled-exposure-and-the-two-lanes.md`
> (19:18Z), whose section 3 sentence decides much of this file.
> STRIKES a claim in `production/findings.txt` and two copies of it in
> `production/NOW.md`, section 6.
> ANSWERS `production/queue/206` acceptance item 4, section 9.
> SUPERSEDES ITS OWN A6 twice in one spawn, section 4.6, and says why.

VERDICT: JAFAR'S "RATHER THAN" STANDS AND IS NOT REFUTED. A1 approved with four
amendments, A2 approved with its central claim corrected, A3 approved, A4
approved with the field shape dictated, A5 approved with amendment. A6, the sun
elevation, was filed to the queue, then ruled IN as three probe rows, and is now
ruled OUT AS A PROBE AND IN AS A ONE-LINE REPAIR, because the resident found
that the engine has been rendering a sun 46.0 degrees from the one the spec
asks for, and you do not probe a series to discover a value the spec already
names.

TWO FINDINGS OUTRANK EVERYTHING ELSE IN THIS FILE. Run 38 carried its own null
test, written into the spec by its author with the acceptance criterion spelled
out, and IT FAILED, and nobody read it (section 3). And the sun's asked
rotation was never differenced against its read rotation on any run, in a rig
that already does exactly that for the camera and for every prop (section 4.6).

## 0. What I could not run, and what is mine

NO BASH IN THIS SPAWN. I ran nothing: not `ledger/verify.py`, not
`tools/road-brightness.py`, not a git command. Every number below is either
read by me out of a committed file, or arithmetic of mine on such numbers, or
labelled as somebody else's.

Read in full or in part: `production/d1-probe/ue-vignette-verdict.txt` all 169
lines, `production/specs/vignette-pieces.json` line 16,
`production/specs/vignette-scene.json` 760 to 885,
`ue-probe/Source/LedgerProbe/Private/VignetteShot.cpp` 744 to 758, 1080 to
1104, 1463 to 1484, `ue-probe/Source/LedgerProbe/Public/VignetteSpec.h` 435 to
456 and 548 to 575, `ue-probe/tests/vignette-spec-test.cpp` at 390, 404 and
2058, `ue-probe/Source/LedgerProbe/Public/FrameStats.h` 515 to 609,
`ledger/Assets/Scripts/Core/StreetVignette.cs` 29 to 35,
`tools/road-brightness.py` 1 to 100, `tools/docs-check.py` 120 to 150,
`production/d1-probe/DISPATCH` 764 to 790, `production/findings.txt` 2690 to
2790, `production/NOW.md` 80 to 150, `production/queue/180`, `186`, `206`,
`.claude/agent-log.tsv` 478 to 485, and the 19:18Z ruling in full.

OPENED, per rule 4, before reading any gate:
`production/d1-probe/ue-vign_ladder_sun003_sky035.png`,
`production/d1-probe/ue-vign_hook_day.png`,
`game-design/sim-shots/rung1_vs_reference.jpg`.

COULD NOT OPEN: `production/art/atlas-01/concepts/hook.png`. It is not in the
working tree on this branch and I have no shell to fetch it, so EVERY
REFERENCE NUMBER IN THIS FILE IS THE RESIDENT'S MEASUREMENT AND NOT MINE.
Condition C9 turns the load-bearing ones into printed evidence.

## 1. The three readings in the brief, checked one at a time

**Finding 1 is TRUE.** Lines 93 to 97 of the verdict read
`shotSkyIntensityRead=1.000` on all five rungs; line 98 reads `0.350` with
`shotSunIntensityRead=3.000`. Across the whole run the sky takes two values,
1.000 and 0.350, and 0.350 appears only with sun 0.000 or 3.000. The cell that
matters was never rendered.

**Finding 3 is TRUE as a transcription and MISATTRIBUTED as a source.** The
row `0.6714 0.3238 0.6987 0.9527` is not in the verdict. It is at
`production/findings.txt:2734` and it was measured on an EARLIER run than 38:
that run's hook frame read ground mean 0.7728 and skyCentre 0.9323
(`findings.txt:2650`, `tools/frame-shadow-probe.py:84`), where run 38's verdict
reads 0.7734 and 0.9325. Same camera, same condition, different run. The
difference is one part in a thousand and changes no conclusion, but "our
rung-1 frame reads" must name which frame. The same quantity now has THREE
values in three documents: the hook frame's `band.ground.p05` is 0.5776 in
queue 206's acceptance, 0.5785 in run 38's verdict and 0.5798 in tonight's
reference table.

**Finding 2 is HALF CONTAMINATED, and it is the same fault as this morning's
two.** Of the four numbers quoted from the control row, the two band numbers
are clean and the two whole-frame numbers are not.

`controlQuadVisibility` on line 120 reads
`controlQuadHidden=3/11 controlQuadHiddenOn=vign_camB_day;vign_camB_night;vign_hook_day`.
The three control quads are therefore VISIBLE in all eight cam_A frames,
including the control row. Their projected boxes (lines 116 to 118) are
x488..614, x309..437 and x130..261, all y298..422: 126, 128 and 131 pixels wide
by 124 tall, 47740 pixels, AT MOST 5.18 per cent of 921600. At most, because
those boxes are `quadProjection=pinhole-from-the-spec-camera/not-an-engine-readback`
and I can see a lamp post crossing them in the frame.

- `shotMaxLuma=0.6240` is very likely a quad pixel, not the street. I opened
  the frame: the quad's yellow and green cells are the brightest objects in it
  apart from the sky wedge. Corroboration in numbers: `vign_camA_night` sits at
  the same sky 0.350 with sun 0.000 and reads `shotMaxLuma=0.6212`, twenty-eight
  ten-thousandths away, while `vign_camB_night` at the same sky WITH THE QUADS
  HIDDEN reads 0.2082. A maximum that barely moves when the sun goes from 0 to
  3 is not being set by anything the sun lights.
- `shotClipLoAll=26813/921600` has the wrong denominator, which is rule 3b's
  exact fault: the denominator counts a larger set than the one examined. Over
  the street rather than the frame it is 26813/873860, 3.07 per cent, not 2.91.
- `band.ground.p50=0.0895` and `band.ground.p95=0.3818` are CLEAN. The ground
  band is y576..720 and the quad boxes end at y422, so they do not overlap.

The verdict's own header says this at line 76: "The controls occupy their
printed boxes, so any whole-frame statistic taken from this run includes them
and must exclude those boxes first." Nobody excluded them. THIS IS THE THIRD
INSTANCE TODAY of a whole-frame or whole-run key read as if it described one
thing, and the 19:18 ruling set the precedent for what a third instance buys:
a mechanical check, not another sentence. Amendment A1(d) below.

## 2. The inference is REFUSED, and so is the refutation built on it

The resident inferred that a sun lighting an asphalt road would put the lit
road far above 0.38, therefore the sun at 3.0 is not lighting the road,
therefore bringing the sky down alone walks the picture to night.

REFUSED, three ways, in increasing order of how much they cost.

1. IT IS AN ABSOLUTE-LUMA CLAIM UNDER AUTOMATIC EXPOSURE. Line 87 of the
   verdict: `ppAutoExposureMethod=0`, `ppOverridesMethod/Bias/Min/Max=0/0/0/0`,
   `cvarDefaultAutoExposure=1`. Run 38 overrode nothing. Histogram auto
   exposure was in force and unsnapped. The 19:18 ruling section 3 already
   decided what such a number is worth: "a number from this rig is worth
   something only if it is a comparison INSIDE one photograph". 0.38 is not
   one, and there is no level at which "far above" could have been checked.
2. THE PICTURE DOES NOT SHOW NIGHT. I opened it. It is a dark overcast street
   at dusk with legible mossy setts, a white kerb line, a readable near
   pavement and deep shade on the right wall. It is nearer the reference's
   tonal character than the frame we ship, which is what section 5 measures.
3. NO INTERMEDIATE SKY WAS EVER RENDERED, so "walks to night" describes a
   value nobody has seen.

CONSEQUENCE: Jafar's instruction is unrefuted and stands as the direction of
travel. The grid is not a correction to him. It is the run that finds WHERE on
the sky axis, and renders the one cell that has never existed.

## 3. The null test that failed, and what it does to the ladder

`production/specs/vignette-scene.json:800`, the note the spec's author wrote on
`ladder_sun003`, verbatim:

> "It is deliberately a duplicate of overcast_day at cam_A: if this frame and
> vign_camA_day differ, the field did not replace the literal cleanly and no
> other rung on the ladder means anything."

I checked the two conditions character by character at lines 764 to 800. They
agree on sun, sun_intensity 3.0, sky_intensity 1.00, hdri, hdri_bom, wetness
0.60, fog_density 0.0120, lanterns, window_practicals. Both were shot on cam_A.
Their readbacks agree: sun 3.000, sky 1.000 on both. THE FRAMES DO NOT.

    key                     vign_camA_day   vign_ladder_sun003   difference
    shotMeanLuma            0.7048          0.5942               0.1106
    band.ground.p05         0.3621          0.2449               0.1172
    band.ground.meanLuma    0.7512          0.6530               0.0982
    band.skyCentre.meanLuma 0.8450          0.7731               0.0719

The cause is not the one the note feared. The field reached the component, the
readbacks prove it. The cause is the exposure fault the 19:18 ruling found and
snapped, with the sign it predicts: shot 1 of the run inherits a dark-adapted
exposure and renders bright, shot 6 follows the bright hook frame and renders
dark.

Read against that null of 0.1172 at `band.ground.p05`, which is ONE SAMPLE and
not a distribution:

    condition             sun    sky    ground.p05   ground.clipHiAny
    ladder_sun003         3      1.00   0.2449       0
    ladder_sun010         10     1.00   0.2838       21
    ladder_sun030         30     1.00   0.3017       1170
    ladder_sun100         100    1.00   0.3212       8214
    ladder_sun300         300    1.00   0.3692       12491
    ladder_sun003_sky035  3      0.35   0.0027       0
    overcast_day (cam_A)  3      1.00   0.3621       2
    overcast_day (hook)   3      1.00   0.5785       0

- A HUNDREDFOLD SUN MOVES THE DARK END BY 0.1243, WHICH IS 1.06 NULLS. On the
  statistic the reference differs on, the sun ladder measured nothing.
- Worse, the rungs were rendered in increasing order, so a drift monotone in
  shot order is PERFECTLY CONFOUNDED with a monotone sun response.
- THE SUN IS NOT INERT. `band.ground.clipHiAny` runs 0, 21, 1170, 8214, 12491
  against a null of 2 versus 0. It clears its null by three orders of magnitude
  at the BLOWN end and not at all at the DARK end. It blew highlights and made
  no shadow, and section 4.6 now says why.
- THE SKY STEP IS THE ONLY ONE WITH A SIGNAL. 0.2449 to 0.0027 is 0.2422,
  2.07 nulls, and 3.07 nulls measured from the other member of the null pair.
- Do not quote `shotClipHiAny` from any cam_A frame for this. The colour quad
  binds texels 255/0/0, 0/255/0, 0/0/255 and 255/255/0, every one of which is
  at 255 on some channel BY CONSTRUCTION, so up to 15624 pixels of that key are
  the instrument photographing itself. The null pair reads 7500 against 3742.

## 4. Rulings on A1 to A6

### A1. THE GRID, ON cam_hook. APPROVED, with four amendments.

The camera change is not merely Jafar's judging camera, it is an instrument
repair, and two independent faults die with it: the control quads are hidden on
cam_hook (line 120), and queue 194's fault, `band.skyCentre` full of rooftops
at fovV 60.0, does not apply at fovV 39.0. Sky {1.0, 0.70, 0.50, 0.35} crossed
with sun {3, 10, 30} is approved as asked. Cost is not a reason to trim it:
`captureSeconds=15.21` over `shotsWrote=11` is 1.38 s per shot as a MEAN over
eleven, so twelve cells is about 17 seconds of a job whose round trip is
measured in tens of minutes. Setting no constant is correct and rule 2 gives
that to queue 206 and 219.

**A1(a), BLOCKING. THE GRID CARRIES ITS OWN NULL CELL.** One extra shot, the
grid's reference condition (sky 1.0, sun 3) rendered a SECOND time at cam_hook
at a distant position in shot order. The run prints the difference between the
pair at `shotMeanLuma`, `band.ground.p05` and `band.ground.p50`. If that
difference is not smaller than the smallest sky step in the grid on all three,
THE GRID IS A NO-READ, no cell is quoted, and the resident stops and escalates.
Section 3 is the same test failing in the run this grid replaces.

**A1(b). SHOT ORDER IS NOT MONOTONE IN SKY.** Interleave the twelve cells so
that no residual drift ordered by shot can masquerade as a monotone sky
response, and state the chosen order in the condition notes.

**A1(c), BLOCKING. THE ASKED-VERSUS-READ TABLE, TWELVE ROWS.** The verdict
prints askedSky, readSky, askedSun and readSun per cell and the count of
agreeing cells over twelve. Run 38 printed five rungs that all read sky 1.000
and one control that read 0.350, and the cross was never printed.

**A1(d). THE THIRD INSTANCE BUYS A MECHANICAL CHECK.** Every shot whose camera
is one the control quads were placed from prints, on its own sample line, the
exact string:

    shotWholeFrameIncludesControlQuads=yes/boxesPx=130..261;309..437;488..614/y298..422/atMostPct=5.18/PROJECTED-BOXES-NOT-MEASURED-COVERAGE/whole-frame-keys-on-this-line-include-them

and shots where they are hidden print
`shotWholeFrameIncludesControlQuads=no/hidden-for-this-camera`. In the tested
layer, per `.claude/rules/instruments.md`.

### A2. THE IN-FRAME STATISTIC. APPROVED, CENTRAL CLAIM CORRECTED.

The placement is right and is not negotiable: FrameStats, the tested layer.
`tools/frame-shadow-probe.py` is frozen by the 14:24 ruling section 3.3, and
that freeze was scoped "in the same commit as the light change", so THIS IS THE
COMMIT WHERE IT BITES HARDEST. Frozen means its MEASUREMENT CODE does not
change. Running it is not a change, and C16 depends on running it.

THE CORRECTION. A RATIO IS NOT INVARIANT UNDER THIS TONEMAPPER. The claim "a
difference scales with k and a ratio does not" is true of a linear multiplier
and false of what runs here, which is exposure followed by a filmic curve. The
curve is MONOTONE, not LINEAR. Under a monotone map a ratio moves, a difference
moves, and what survives EXACTLY is order: if pixel a was darker than pixel b
before, it is darker after. So the invariant class is RANK statistics, meaning
any quantity whose definition mentions only comparisons between pixels of the
SAME frame.

Three classes, and every new key declares which one it is in:

- ABSOLUTE: a luma, a percentile, a mean. Void across frames by the 19:18
  ruling section 3. May be printed, may not be compared across cells.
- ROBUST: a within-frame ratio such as p95 over p05. Moves with exposure but
  far less than either end does. Quotable across cells ONLY when the null cell
  says the exposure held.
- EXACTLY INVARIANT: a rank statistic.

DICTATED, the two keys and their strings:

    band.ground.p95OverP05=<v>
    band.ground.p95OverP05Stat=within-one-frame-ratio-of-two-indexed-order-statistics/not-interpolated/ROBUST-NOT-INVARIANT/a-tonemap-is-monotone-not-linear-so-this-moves-when-the-exposure-moves/quotable-across-cells-only-when-the-null-cell-held

    band.ground.<rankKeyName>=<v>/of=<pixels>
    band.ground.<rankKeyName>Stat=a-rank-comparison-between-pixels-of-ONE-frame/EXACTLY-invariant-under-any-strictly-monotone-whole-frame-curve-including-exposure-and-this-tonemap/NOT-invariant-under-bloom-vignette-grain-or-local-tonemapping-which-are-not-whole-frame-monotone
    band.ground.<rankKeyName>Ties=<n>/of=<pixels>
    band.ground.<rankKeyName>Rails=<lo>/<hi>/of=<pixels>

The builder chooses the rank key's definition and its name, subject to one
rule: THE DEFINITION MENTIONS ONLY COMPARISONS BETWEEN PIXELS OF THE SAME
FRAME. Ties and rails are the key's validity denominator, because they are
where the curve stops being strictly monotone and the invariance claim stops
being true, and they print beside it always, per rule 3b.

REFUSED: the word "invariant" in any key or stat string without the clause
naming bloom, vignette and local tonemapping as the exceptions.

### A3. WETNESS. APPROVED.

I ran the call-site grep myself across the whole `ue-probe` tree: `Wetness`
appears at `VignetteSpec.h:257` (field), `:259` (initialiser) and `:445`
(parse), and NOWHERE in `VignetteShot.cpp`. Rule 6, confirmed: parsed and read
by nothing. Queue 186's precondition is now met, which it was not when the item
was filed: there is something to reflect.
`skyModel=skyatmosphere+skylight-realtime-capture`, `cvarReflectionMethod=2`,
`cvarSkyLightRealTimeReflectionCapture=1`.

AMENDED TO A SERIES, NOT A VALUE. Three rows at the grid's reference cell,
wetness 0.0, 0.60 and 1.0, so the run prints both ends and the value the
conditions already carry, and so a later session can see whether 0.60 was ever
chosen or merely typed. No constant lands in this batch.

### A4. THE FOG. APPROVED, FIELD SHAPE DICTATED.

`VignetteShot.cpp:208` holds `const float kFogMaxOpacityWithSky = 0.45f;`,
applied at `:1359`. Queue 186 names the fog max opacity in its own text as
something that "must come down in the same change or a sky behind an opaque fog
is invisible", so it is inside the asked work by name.

DICTATED SHAPE, copying the precedent queue 205 set in this same file for
`sun_intensity`:

- `fog_max_opacity` is a REQUIRED condition field parsed with `NeedNum`, and
  the refusal is the point. No optional field with a silent default.
- Every existing condition carries `0.450`, so nothing moves except the probe
  rows.
- FOUR ROWS, NOT TWO, at the reference cell: 0.450, 0.250, 0.100 and 0.000.
  Two rows are a pair, four are a series, and the transparent end is the one
  that says how much of the white far field is fog at all. Cost is 5.5 seconds.
- `fogMaxOpacityRead` already exists at `VignetteSpec.h:2174`; the verdict
  prints asked beside read per shot.

BLOCKING RIDER, AND IT IS A TWO-ENGINE CONTRACT RATHER THAN A PARSE QUESTION.
`ledger/Assets/Scripts/Core/StreetVignette.cs` at 29 to 35 says every number in
that scene comes from this shared file and that "a missing key is an ERROR, not
a fallback, because a fallback would let the two engines quietly build two
different streets and both stills would look fine". A key only one engine knows
about is that same fault facing the other way. So either Core reads
`fog_max_opacity` too, or this record names it as a deliberate one-engine key
with the reason written beside it. If Core's reader refuses the new key
outright, that is REPORTED, not worked around by loosening either reader.

### A5. THE ART LANE IN THE SAME DISPATCH. APPROVED WITH AMENDMENT: SAME
SESSION, SAME PC VISIT, TWO COMMITS, GAME LANE FIRST.

The two lanes are two workflows, so "one dispatch" was never available; what
was on offer was one COMMIT. The coupling that matters is not the runner, which
the 19:18 ruling section 4 already serialised, it is the commit gate: a red
`ledger/verify.py` caused by the art half holds rung 1 hostage, and rung 1 has
a 04:07Z wake pointed at it. Splitting costs one extra push and zero extra
round trips, since each workflow is dispatched separately either way.

Per `.claude/rules/ci.md`, watch by ancestry and capture the sha BEFORE
dispatching. If the art commit lands before the runner starts, the probe runs
on a commit that contains it, and the verdict's line 1 will name that sha. That
is correct; watching by branch movement is what would break.

### A6. THE SUN'S PITCH IS A BUG, NOT A FIELD. THE ONE-LINE REPAIR GOES IN THIS
BATCH. THE ELEVATION ROWS ARE WITHDRAWN AND I AGREE WITH THE WITHDRAWAL.

I ruled elevation out at 19:5x as adjacent, then in as three probe rows when the
resident argued round-trip cost, and now out again as a probe because the
resident produced a MEASUREMENT where both of us had been reasoning. That is the
right number of reversals when the evidence moves twice, and each one is
recorded so nobody has to reconstruct the sequence.

**THE DISCREPANCY, EVERY STEP CHECKED BY ME, ALL ON COMMITTED FILES.**

- `production/specs/vignette-pieces.json:16` at the run's own commit:
  `"sun":{"elevation_deg":36,"azimuth_deg":205}`.
- `VignetteSpec.h:563`, `SunPitchDeg(e) = -e`, so the asked pitch is -36.0. The
  comment above it at 560 to 562 states the intent in words: "a sun 36 degrees
  above the horizon sends its light 36 degrees BELOW it".
- `VignetteSpec.h:558`, `SunYawDeg(a) = Wrap360(a + 180)`, and Wrap360(385) is
  25.0, so the asked yaw is 25.0.
- The committed verdict, on every shot line: `sunPitchYawRead=-82.0/25.0`.

YAW AGREES TO THE DECIMAL. PITCH IS OFF BY EXACTLY 46.0. The resident is right
that the yaw agreement rules out coincidence, and there is a second deduction
in it that he did not make and that strengthens the case: 25.0 is not any
engine default, it can only have come from the ask, SO THE ASK REACHED THE
ACTOR AND THE RESIDUAL LIVES BETWEEN THE ACTOR AND THE COMPONENT.

**WHICH ONE IS THE TRUTH, WHICH IS RULE 3 ASKED PROPERLY.** The suspect must
be the instrument first, and here the instrument is exonerated by the engine's
own contract rather than by argument. `VignetteShot.cpp:1471` and `:2032` read
`LC->GetComponentRotation()`, the light component's WORLD rotation. A
directional light's direction IS the forward axis of that same component world
transform. The readback and the renderer therefore read one transform, and
there is no arrangement in which the readback says -82 while the render lights
at -36. THE READ IS THE TRUTH AND THE ASK NEVER ARRIVED.

**THE MECHANISM IS PLAUSIBLE AND IS NOT LOAD-BEARING.**
`VignetteShot.cpp:744` to `:758`: `SpawnDirectional` passes its `FRotator` to
`SpawnActor` as the ACTOR rotation and then touches only `SetCastShadows` and
`SetIntensity`. It never sets the component's rotation. A constant pitch offset
with zero yaw offset is what a component relative rotation composed under an
actor rotation looks like, and the composition is exactly additive here because
the relative rotation is a pure pitch: yaw(25) applied to pitch(-36) then
pitch(-46) is yaw 25, pitch -82, with no cross terms. I confirm that
algebraically. I do NOT confirm that -46 is Unreal's shipped default on
`ADirectionalLight`, the resident does not either, and THE FIX MUST NOT DEPEND
ON IT.

**THE COST, WHICH IS SECTION 3 MADE QUANTITATIVE.** A 4 m lamp post casts
4/tan(36) = 5.5 m at the asked elevation and 4/tan(82) = 0.56 m at the rendered
one. A FACTOR OF TEN IN SHADOW LENGTH. That is queue 197, nothing casts a
contact shadow, explained rather than described, and it is why a hundredfold of
sun intensity moved the dark end by 1.06 nulls while blowing highlights by
three orders of magnitude: the light was very nearly straight down the whole
time.

**AND THE REASON IT SURVIVED, WHICH IS THE PART THAT GOES IN THE CASEBOOK.**
This is CLAUDE.md rule 6 exactly: built is not running.
`ue-probe/tests/vignette-spec-test.cpp:404` tests the ARITHMETIC,
`SunPitchDeg(e) + e < 1e-9`. Line 2058 tests the FORMATTER, asserting the
string `sunPitchYawRead=-36.0/205.0`. The maths was tested, the string was
tested, and NOTHING TESTED THAT THE NUMBER REACHED THE LIGHT. Meanwhile the rig
already had the discipline that catches this, in the same file, for two other
populations: verdict line 86 prints `shotCamAskedPitchYaw=-4.0/0.0` beside
`shotCamReadPitchYaw=-4.0/0.0` with `shotCamDeltaCm=0.00`, and line 85 prints
`propCentreWorstMm=0.00` against the file's own coordinates over 22 props. THE
LIGHTS ARE THE ONE ACTOR POPULATION NOBODY EVER DIFFERENCED, and 46 degrees
hid there for every run the key has existed.

Note also, and it is small: the test fixture at 2058 puts 205.0 in the yaw
slot, which is the AZIMUTH and not the converted yaw. Nothing depends on it,
but a reader learning the key from the test would learn it wrong.

**RULINGS ON THE RESIDENT'S FOUR QUESTIONS.**

1. YES, IN THIS BATCH. It adds no field, changes no spec file, changes no
   schema and touches neither reader, so it is not the contract change I
   refused earlier: it is the engine being made to deliver a value the spec has
   asked for since it was written. Without it, twelve grid cells and C14 put
   twelve frames in front of Jafar's eye lit by a sun nobody chose. The repair
   is a CONSTANT of the run applied to every cell equally, so it cannot confound
   any comparison BETWEEN cells; what it does is move the baseline away from run
   38, which wetness and fog were moving anyway.
2. NO ELEVATION ROWS, AND THE WITHDRAWAL IS ACCEPTED. My A6 justified them as
   the control that separates "the sky was not the cause" from "nothing can cast
   at all". That second horn was a hypothesis about an unknown value; it is now a
   defect with a known correct value written in the spec. You repair a defect,
   you do not probe a series to rediscover a number the spec already names. The
   grid keeps one moving axis pair and stays readable.
3. WHAT IT MUST PRINT, and the shape is his with three amendments. An
   asked-versus-read line ON THE RUN LINE for EVERY directional light, both
   axes, with the signed residual to four decimals and a count over the
   population, because the rotation is written once at spawn and never
   rewritten, which makes it a whole-run fact per `.claude/rules/instruments.md`.
   The existing per-sample `shotSunPitchYawRead` STAYS, since a per-sample read
   is what would catch a later write. Amendments: (a) THE REFUSAL FIRES AT A
   RESIDUAL OF 1.0 DEGREE OR MORE ON EITHER AXIS, and this record states plainly
   that 1.0 IS NOT A MEASURED TOLERANCE, it is a class separator between the
   fault it must catch, 46.0, and the float round-trip it must not, of order
   1e-4; if any run ever prints a residual between 0.001 and 1.0, the bound gets
   set from that printed series and not before. (b) The refusal EXITS NON-ZERO
   WITH THE VERDICT STILL COMMITTED, the way `shotBlank` and `UNDECODABLE`
   already do, per `.claude/rules/ci.md`. (c) Rule 5b: the guard ships with both
   cases in the tested layer, ACCEPTING FIRST on the live values, then a planted
   offset that must refuse.
4. THE FILLS ARE FIXED BY THE SAME LINE AND THEIR ROTATIONS MUST BE PRINTED.
   `VignetteShot.cpp:1094` to `:1096` spawn them through the same helper with
   literals (-80/20), (-10/200) and (60/90), so the same displacement applies to
   all three. WHAT THIS RECORD MUST NOT DO IS STATE WHERE THEY ACTUALLY POINTED:
   the verdict prints `fillsSpawned=3/3` and `fillsRetiredToZero=yes` and NO
   ROTATION, so their rendered direction is unmeasured and any number I wrote
   here would be a prediction wearing a reading's clothes. The asked-versus-read
   line covers all four lights, 4 of 4, and the next run answers it for free.
   They are retired to zero intensity so no pixel moves today; the comment
   claiming a direction is the decayed claim, and printing is what retires it.

## 5. What the reference actually says, and what I could check of it

The resident's correction arrived mid-ruling and I accept its structure, having
confirmed the part I could: I OPENED
`game-design/sim-shots/rung1_vs_reference.jpg` and the left half plainly
contains the four labelled material swatches, the rope fender, dustbin and
firkin, and the cream caption band "MERIDIAN 1990 / A WORKING PORT, A LIVING
TOWN". A histogram over that crop measured a caption strip. The structural
claim is confirmed by the artifact.

His numbers remain his. Three things I checked:

- HIS OWN DENOMINATOR DISAGREES WITH HIS OWN ROW RANGE BY ONE ROW. Rows
  662..1279 inclusive is 618 rows, 632832 pixels at width 1024; he reports
  n=631808, which is 617 rows. Rule 3b: a denominator states what it counted.
- THE TWO SKY BANDS ARE NOT THE SAME FRACTION. Ours is the top eighth, 12.5 per
  cent, 115200 px. His reference band is 74752 px of 617 rows, 11.8 per cent.
  He called the sky reading the weak one and I agree for a second reason.
- HIS "OURS" PERCENTILES ARE NOT THE VERDICT'S. He reads ground p05 0.5798 and
  p95 0.9336 where the committed verdict reads 0.5785 and 0.9304, on the same
  file and the same 184320-pixel rectangle, with mean and p50 agreeing exactly.
  The gaps are 0.0013 and 0.0032, both under one 8-bit code, which is the
  signature of linear interpolation against nearest rank. `FrameStats.h:594`
  states the convention and claims `tools/road-brightness.py` shares it:
  "INDEXED, NOT INTERPOLATED ... The same convention tools/road-brightness.py
  uses, so the two rulers agree on what a p95 is." One of the two rulers in play
  tonight does not. Condition C8.

NONE OF THAT MOVES THE CONCLUSION, because the corrections are one part in a
thousand and the gaps they qualify are these:

    band                ref street (his)    ours (verdict, mine)
    ground p05          0.1932              0.5785
    ground p50          0.3793              0.7793
    ground p95          0.7281              0.9304
    ground p95/p05      3.77                1.61

The 1.61 is my arithmetic on the committed verdict's own two numbers. THE
ENTIRE GAP IS THE GROUND, our road is three times brighter at the dark end and
carries under half the contrast ratio. Jafar's instruction survives the
correction and is strengthened by it.

ACCEPTED FROM THE RESIDENT, with the purposes he proposed: A1's grid is read
for where the picture gains a dark end, not for where a mean matches; A2's
ratio is the statistic the run is read by; A3 rises in importance. I overturn
none of it.

## 6. The struck sentence, and where its copies are

STRUCK: "The two p95 values nearly agree: both pictures have a bright top end",
`production/findings.txt:2736`, and the table above it at 2733 to 2734 whose
reference row measured a caption band.

Rule 1 says grep the SENTENCE and not the site. The claim was copied in
different words to `production/NOW.md:88` ("median 0.6987 against 0.3942,
darkest twentieth 0.3238 against 0.1215") and again at `NOW.md:141` to `143`.
All three sites are corrected in the same change, each one naming the crop
rectangle the new numbers came from.

NOT BLOCKED: `game-design/sim-shots/rung1_vs_reference.jpg` itself. As a
PICTURE it is honest and its caption says "Hook sheet, lower panel". What may
not happen is a caption or a message carrying a histogram number taken from
that crop. The channel is the Producer's; the record is mine.

## 7. Premise check, CLAUDE.md section 0

Nothing here dates the world outside 1988 to 1992. The reference is a 1990
British port street and the work is wet asphalt, worn brick and an overcast
sky, which is the stated visual target. Nothing cites the retired GTA V bar,
nothing is purchased, no tool enters, no licence entry moves. This batch serves
Meridian Test point 1 directly: a person who loves KCD2 bounces off a street
with no dark in it inside five seconds, and a street lit from 8 degrees off
vertical cannot have dark in it.

## 8. Conditions the resident PRINTS before committing

Nothing commits on this ruling that is not named in it.

- **C1.** `python3 ledger/verify.py` green, footer pasted FROM
  `ledger/.verify-footer`, never from the scrollback.
- **C2.** `tools/docs-check.py` passes on this record, which declares LOG and
  carries NOT CURRENT inside its first eight lines, which is what the checker
  actually reads (`tools/docs-check.py:139`).
- **C3.** `director_cadence` clears with this record's stamp, which names
  2026-09-09T19:46:49Z, `.claude/agent-log.tsv` line 485.
- **C4, BLOCKING.** The null pair's three differences printed from the
  committed verdict, and each smaller than the smallest sky step in the grid.
  Otherwise NO-READ and escalate.
- **C5, BLOCKING.** The twelve-row asked-versus-read table in the committed
  verdict, 12 of 12 agreeing, with a cell that failed printing "nothing
  measured" rather than a zero.
- **C6.** The shot order printed, and it is not monotone in sky.
- **C7, BLOCKING.** Each new A2 key prints its class word, and the rank key
  prints Ties and Rails with denominators. Grep the diff for the word
  "invariant" and read every hit.
- **C8.** The cross-ruler check: the tool that measures the reference is run on
  OUR committed hook frame over the identical rectangle and its four numbers
  printed beside the verdict's `band.ground` keys, with the residual stated and
  the percentile convention named. Known target: 0.5785 and 0.9304 indexed.
- **C9, BLOCKING.** The reference histogram reprinted with its crop rectangle
  in pixels, the row-statistic evidence for the panel boundaries, and an n that
  agrees with its own row range.
- **C10.** The `Wetness` call-site grep pasted before and after: three hits all
  in `VignetteSpec.h` today, and the read site named afterwards. The FRAME is
  what answers, not the readback, because a value that lands on the game thread
  and never reaches the render proxy reads back as the same pointer.
- **C11.** `fogMaxOpacityRead` asked beside read on all four fog rows, and
  every pre-existing condition reading 0.450.
- **C12.** Two commits, game lane first, art second.
- **C13.** The sha captured BEFORE dispatch and the run watched by ancestry.
- **C14.** ALL of the grid's frames opened and read before any gate is read,
  and the record names the chosen cell in words about the PICTURE. Queue 180's
  acceptance is explicit: "HIS EYE IS THE GATE and no number passes this rung".
- **C15, BLOCKING for A6.** The committed verdict's run line carries asked,
  read and signed residual on BOTH axes for all four directional lights, 4 of 4
  agreeing, with the sun reading pitch -36.0 and yaw 25.0. A run whose sun still
  reads -82.0 has not landed the fix however green the build is.
- **C16, A6.** The shadow-edge step read by `tools/frame-shadow-probe.py`,
  whose measurement code does not change in this commit, printed beside the
  historical series +0.0270 with three fills and no skylight, -0.0003 with the
  captured sky on the same pixels, and -0.0035 on the rung-1 frame
  (`production/d1-probe/DISPATCH` 764 to 767), with the out and in denominators
  3768/1645 stated for the first of them. It is a comparison inside one
  photograph and is therefore one of the few numbers here that section 3 of the
  19:18 ruling does not void.
- **C17, A6.** The guard's two cases read from the test output, accepting
  first: the live values passing, then a planted offset refusing.

## 9. Rows, lifetime, and queue 206 item 4 answered

Queue 206 acceptance item 4 required the ladder rows to be decided rather than
left, because "rows kept by default are rows nobody chose". They cost about
1.67 MB of committed PNG each on EVERY subsequent run
(`stagedPngBytes=18317365` over 11).

DECIDED. The five `ladder_sun010` to `ladder_sun300` rows and
`ladder_sun003_sky035` are REMOVED, their series preserved in section 3 of this
record, which is the condition 206 set. `ladder_sun003` is removed as a cam_A
row and REPLACED by A1(a)'s null cell at cam_hook, renamed to say what it is:
the duplicate condition is the most valuable thing the ladder produced and it
becomes a standing instrument rather than a rung.

EVERY ROW THIS BATCH ADDS IS A ONE-RUN PROBE ROW, its note field says so and
names this record, and the item that reads the grid removes them in the same
change. The count is 12 grid cells, 1 null, 4 fog and 3 wetness, which is 20
rows at about 1.67 MB, about 33 MB per run if they are left.

## 10. The quality ladder: no aspect closes with a blank next rung

Asked at close per `production/quality-ladder.md`: best available, or first
working? All six are first working, and each has a named next rung.

- A1: a grid at a fixed exposure rather than one whose null cell has to be read
  first. That is queue 219's pinned value.
- A2: the rank statistic measured on BOTH pictures by one implementation, so the
  comparison stops depending on two rulers agreeing.
- A3: wetness as a per-surface property rather than one scalar for the street. A
  pavement, a road and a painted timber fascia do not wet alike.
- A4: fog density and fog max opacity set from a printed series, queue 206's job.
- A5: the art lane yielding before taking the runner, filed by the 19:18 ruling.
- A6: a sun whose elevation follows the hour rather than sitting on one authored
  value, which is what a town with a clock in it eventually needs.

FILED TO `production/queue/` BY NAME, numbers whatever is free:

1. ASKED VERSUS READ FOR EVERY ACTOR POPULATION THIS RIG SPAWNS, not just
   cameras, props and now lights. The lights hid 46 degrees because they were
   the one population nobody differenced; the general form is that anything
   spawned from a number in a file prints that number beside what the engine
   says it got.
2. The incident itself to `ledger-v2/studio-v2/casebook-claims.md` under rule 6:
   a tested formula and a tested format string and no test that the value
   arrived. Not a paragraph in CLAUDE.md, which its own rule forbids.
3. The whole-frame keys on a quad-carrying camera are contaminated and only a
   header comment says so. A1(d) fixes it for this run; the general form is that
   any instrument object placed in a judged frame declares itself on every key it
   touches.
4. Two rulers, one convention: `FrameStats.h:594` claims
   `tools/road-brightness.py` shares its indexed percentile and section 5 says
   one of them does not.
5. `production/findings.txt` and `production/NOW.md` carry a struck claim in
   three places, section 6, and one quantity now has three values in three
   documents, section 1.
6. The test fixture at `vignette-spec-test.cpp:2058` carries an azimuth in a yaw
   slot. Harmless, and it teaches the key wrong.

Per rule 13 the resident works these while budget and ceiling remain and arms
the resume rather than stopping on a landed batch.

<!--RULING spawn=2026-09-09T19:46:49Z-->
