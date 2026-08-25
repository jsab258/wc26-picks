# Dry-tour stills read — verdict 6137608

> **STATUS — LOG, 2026-08-25. NOT CURRENT** after the next landing.
Read-only artifact read by artifact-reader. Every number below was
produced in this session from the committed frames; nothing is quoted
from memory.

---

## 0. PROVENANCE — clean, and two corrections to the brief

`verdict.txt` line 1 says `6137608`. `frames.tsv` line 1 says
`6137608180832b992cd8ca05a4c31ebf6c101b02`. HEAD is `fae0c707`
("Sim stills from 6137608"), whose parent `61376081` is the commit that
ran. The stills commit staged by NAME: 19 JPEGs, `frames.tsv`,
`runs/6137608.txt`, `verdict.txt`. The four stale `hunt_*.jpg` (dated
Aug 23 and Aug 24 19:10) were correctly NOT restaged. There is no
`NO PLAYER LOG` line and the done line ends `gatesChecked=72
gatesFailed=0 verdict=Ongoing pass=True`. The run rendered what it
claims.

All eight frames I compared byte-for-byte against the previous landing
differ. Nothing is a carried-forward file.

**Correction 1 — this is the SECOND dry tour, not the first.** The
previous landing `a41d0d5b` (run `b88adbb`) already carries
`rain=0.00 wet=0.00` on all seven district rows. The brief's "FIRST to
photograph the seven district frames in DRY weather" is off by one
landing. This matters because it means there is a second dry sample to
check the first against, and I used it throughout.

**Correction 2 — "every prior run in project history shot them at rain
0.90" is not true either.** That sentence comes from `b88adbb`'s own
commit message ("all 91 district rows in history were shot at rain
0.90"). Walking `frames.tsv` back 25 revisions, the rain era covers
`54841ddb`..`7a3d68d0`; before it the district rows read
`rain=0.00 wet=0.24..0.25` with `district_ironside` at meanLuma
0.175..0.207. So the tour HAS been shot dry-ish before, at a fifth of
today's brightness — and that is a load-bearing fact, because it means
"dry" alone does not produce a white ground. Those older cameras stood
in unlit places; the confound is the vantage, not the weather.

---

## 1. THE GROUND — present in every sunlit frame, and it is the MATERIAL

### What the artifact shows

Near-white, snow-like ground in all seven district frames and in two of
the review frames. Buildings, signage and sky in the same frames are
correctly exposed — brick reads brick, the green tank in ironside reads
green, the sky is a dark blue-grey. It is the ground plane alone.

The per-frame verdict, ground band = the ref-bench band (y 0.667..0.88),
luma 0..1:

| frame | rain/wet | ground mean | ground p90 | ground/frame | verdict |
|---|---|---|---|---|---|
| district_ironside | 0.00/0.00 | 0.750 | 0.886 | 1.23 | WHITE, worst in set |
| district_fairview | 0.00/0.00 | 0.659 | 0.872 | 1.27 | WHITE |
| district_copper | 0.00/0.00 | 0.600 | 0.873 | 1.26 | WHITE |
| district_gullwing | 0.00/0.00 | 0.527 | 0.826 | 0.98 | PALE |
| district_downtown | 0.00/0.00 | 0.526 | 0.857 | 1.28 | PALE |
| district_hook | 0.00/0.00 | 0.428 | 0.861 | 1.02 | PALE |
| district_strip | 0.00/0.00 | 0.417 | 0.868 | 0.98 | PALE |
| review_day5_noon | 0.00/0.00 | 0.681 | 0.874 | 1.37 | WHITE |
| review_day2_noon | 0.00/0.62 | 0.645 | 0.837 | 1.38 | WHITE |
| review_day1_noon | 0.35/1.00 | 0.328 | 0.594 | 1.00 | CORRECT |
| review_street | rain | 0.165 | 0.656 | 0.61 | CORRECT |
| review_day1_dusk | 0.35/1.00 | 0.137 | 0.330 | 0.98 | correct (dusk) |
| review_day2_wet | 0.90/1.00 | 0.093 | 0.191 | 0.78 | CORRECT |
| review_day1_night | 0.35/1.00 | 0.088 | 0.203 | 0.76 | correct (night) |
| review_day2_night | 0.00/0.00 | 0.084 | 0.164 | 0.64 | correct (night) |
| review_day2_close | night | 0.073 | 0.176 | 0.117 | correct (night) |
| review_day5_night | 0.00/0.00 | 0.112 | 0.156 | — | correct (night) |

**It is not confined to the tour.** `review_day5_noon` is a street-level
review camera in the Hook, dry, and it is the second-brightest ground in
the whole set. `review_day2_noon` at wet 0.62 is just as bad. The only
correctly-exposed daylight frame in the set is `review_day1_noon`, at
wet 1.00 — and it looks like a British street: mid-grey tarmac, double
yellow lines, dashed white lines, kerbs, drain covers, red brick specks.

**It is a SUNLIT fault.** `review_day2_night` is bone dry (0.00/0.00)
and its ground is fine at 0.084. No sun, no white.

### The measurement that settles which

Two candidate causes have opposite fixes: global overexposure (fix the
tonemap) versus ground albedo (fix the material). Three readings
separate them, and all three say material.

**(a) Hard clipping is absent.** Fraction of ground-band pixels above
0.95 luma: ironside 3.2%, everything else 0.3-0.6%. If this were
tonemap blowout the top of the histogram would be piled at white. It is
not. The ground is uniformly PALE, not clipped.

**(b) The ground is brighter than its own scene, which no reference
ever is.** Ground-band mean divided by whole-frame mean is
exposure-independent by construction. The five GTA V references:

    0.66  0.41  0.53  0.91  0.97      band 0.41 .. 0.97

Every reference has ground DARKER than frame average, because tarmac is
the darkest large surface in a daylight scene. Ours, sunlit:

    copper 1.26  downtown 1.28  fairview 1.27  ironside 1.23
    day2_noon 1.38  day5_noon 1.37
    gullwing 0.98  hook 1.02  strip 0.98  day1_noon 1.00

Six of ten are physically inverted. The remaining four sit at or just
past the top of the reference band — and those four are the frames whose
lower third contains a lot of building, which drags the band mean down;
the road itself is equally pale in all of them by eye.

Our night and wet frames read 0.61-0.78, comfortably inside the band. So
the instrument is sound and only the sunlit dry ground is out.

**(c) The material probe names the number, and the code explains it.**
`districtGround=[mat_asphalt/col:0.74,0.76,0.80/...]`.

`AssetLibrary.cs:423` — `static readonly Color TextureGrade = new
Color(0.74f, 0.76f, 0.80f, 1f)`, applied as `mat.color` to every
textured surface. `SetWetness` (same file, ~line 683) then does
`mat.color = TextureGrade * LightModel.AlbedoScale(wetness)`, and
`LightModel.AlbedoScale` is `Clamp(1.0 - 0.45*rain, 0.55, 1.0)`.

That is the whole mechanism. At wetness 1.0 the ground albedo is
0.74 x 0.55 = 0.41; at wetness 0 it is 0.74. The rain-era runs probed
`col:0.44,0.45,0.48` — exactly 0.594x the dry value — which I first
misread as a code change and which the file corrected: it is the wet
multiplier, nothing more. **The wet term was the only thing holding the
ground down, and the brief's core insight is right.**

Two asymmetries make this a ground problem specifically rather than a
grade problem:

- Facades get a second pass. `noonFacadeMat` reads
  `col:0.62,0.64,0.69` for brick — 0.84x `TextureGrade`, from the
  facade grade (`facadeGrades=658/849`). The ground has no equivalent;
  its only darkening lever is weather.
- The kit props were painted down explicitly — `kitAlbedo` shows
  `base_mesh_park_bench:1.00>0.05`, `swing_bin:1.00>0.08`, and 30 more.
  `townWallAlbedo=0.15`. The road is the one large surface nobody
  neutralised, and it faces straight up (`nUp:1.00`), so it takes full
  sun plus full sky ambient.

### This was predicted, in writing, on the line itself

The comment above `TextureGrade` records iteration 2:

> ITERATION 2, from run edbce5b's numbers: at 0.82/0.84/0.88 the noon
> frames came back meanLuma 0.44-0.49 with 40-48% of pixels bright on
> three of ten days — pavements reading seaside-morning white, not
> overcast port. Ten percent down.

Today's dry noon frames read meanLuma 0.472-0.608 with brightPct
25-54%: `day5_noon` 0.496/40.46, `fairview` 0.516/41.61, `gullwing`
0.537/44.94, `ironside` 0.608/54.31. **Every one of those is inside or
above the band that was declared the failure state.** The 10% cut did
not clear it, and could not have been seen to fail, because iteration 2
was judged on rain-era frames where the wet term was hiding 45% of the
albedo. The comment is honest and self-aware ("an ART value, iterated
against committed stills"); what it lacked was a dry still to iterate
against.

---

## 2. BLOCKED FRAMING — one camera, and it is not one of the re-sited two

### Which cameras stand against something

**`district_ironside` — BLOCKED.** A crane tower fills the centre of
frame at point-blank, top to bottom, occupying roughly the middle fifth
of the image and blurred by depth of field. The engine names it on the
done line: `shotBlocker=[Crane_2_tower_up@4.01m in district_ironside]`,
with `shotsBlocked=6 shotsAimed=29`.

It is unchanged and pre-existing. The previous landing's ironside frame
has the same crane in the same place, `shotBlocker` names the same
collider at the same 4.01m, and the frustum bands are identical
(`near=0.00 mid=0.25 far=0.01` in both runs). It has nothing to do with
the re-site.

**`review_day1_night` — BLOCKED**, incidentally: the right ~55% of the
frame is an unlit building face at close range. `review_day2_close` is
also mostly wall, but that one is a deliberate character close-up.

**All six other district cameras are clear.** hook, copper, downtown,
strip, fairview and gullwing all give open street corridors with depth.

### The two re-sited cameras — both fixed, neither broke anything

`tourResited=2/2`. I pulled the previous landing's frames to compare.

| | before | after |
|---|---|---|
| gullwing | 85% of frame is one unlit building face at arm's length; meanLuma 0.154, brightPct 2.19 | clean elevated view down Bathhouse Row; meanLuma 0.537, brightPct 44.94 |
| downtown | near-black frame, meanLuma 0.096, brightPct 0.50 | two-sided street corridor with cars, lamps, shopfronts; meanLuma 0.412, brightPct 25.00 |

Both are unambiguous successes and both are now among the
best-composed frames in the set. Against `SimDirector.cs`'s own written
predictions: gullwing hit every one (predicted farFrac 0.30+/-0.10 →
0.37; depth 25-30m → 25.9; meanLuma into the dry-noon band → 0.537;
"lumaThirds no longer flat" → 0.722/0.804/0.718). Downtown missed on
the sight-line pair (predicted farFrac ~0.71 and depth ~15m, landed
0.50 and 20.8) but hit on the number the comment said was the one that
mattered — meanLuma 0.096 → 0.412. The comment explicitly said the
sight-line pair could not answer that question and must not be read as
if it had; that instruction was correct.

### Why no gate caught ironside — and the number that DID see it

`nearFrac` counts rays whose nearest non-player hit is <= 2m; `midFrac`
2-7m; `farFrac` 7-20m, over an 84-ray (12x7) frustum grid.

The verdict's tour block prints `tourNearSeries=[0.00/0.00/0.00/0.00/
0.00/0.00/0.00]` and `tourDepthBy=[...]`. Both are blind here for
different reasons:

- **The crane is at 4.01m, so it lands in the MID band, and the tour
  block does not print the mid band.** `frames.tsv` does:
  `district_ironside mid=0.25` — 21 of 84 rays — and it is **the only
  non-zero midFrac among the seven districts**, and the only near-zero
  farFrac (0.01). The instrument saw it perfectly. The verdict summary
  prints the one band that reads 0.00 for everything and omits the one
  band that fired.
- **`tourDepthBy` ranks ironside as the LEAST blocked camera, at 32.7m
  — the largest of the seven.** It is a MEDIAN over rays: the crane
  owns a central column, the other 63 rays sail to the horizon, and the
  median follows the majority. This is CLAUDE.md rule 2 exactly — "a
  minority is invisible to every median", and "is anything blocking"
  is never a median question.

**And there is a second, sharper blind spot the frames prove.** The
previous gullwing frame is ~85% building face, and its bands read
`near=0.00 mid=0.00 far=0.25` — certified clear. A raycast from inside
or hard against a hollow mesh does not hit its backfaces, so the exact
failure mode "the camera is standing in a wall" is the one this
instrument cannot see. `SimDirector.cs` knows about the backface issue
(it is named in the re-site comment as a reason the box model
over-counts sheds) but the consequence for blockage detection is not
drawn.

---

## 3. DETAIL vs EXPOSURE — mostly EXPOSURE, and the decal work is aimed at a gap that is largely not there

This is the question with the money on it, so here is the arithmetic.

`groundPatch` is, per `ref-bench.py`, the **median over 64px windows of
(window std / window mean)** on 16px block means. That construction has
a property that decides the whole question:

- **A MULTIPLICATIVE exposure change leaves it exactly unchanged.**
  Scale every pixel by k and both std and mean scale by k; the ratio is
  invariant.
- **An ADDITIVE lift lowers it.** Add a constant c and the mean rises
  while the std does not move, so std/mean falls.

An over-bright ground raised by ambient fill and a genuinely flat
surface therefore produce the same low reading, and the way to tell
them apart is to remove the additive lift and re-measure. I did that:
for each frame, subtract the constant that brings its ground-band mean
to the five references' own average ground mean (87.3/255), then
recompute `groundPatch` identically.

Reference band 0.211..0.269 on my implementation (0.205..0.382 as
ref-bench states it over its wider stat set — I use my own recomputation
consistently on both sides).

| frame | ground mean (255) | groundPatch | lift removed | groundPatch adjusted | |
|---|---|---|---|---|---|
| district_gullwing | 134.4 | 0.247 | 47.1 | **0.430** | above band |
| district_strip | 106.4 | 0.254 | 19.1 | **0.352** | above band |
| district_hook | 109.2 | 0.239 | 21.9 | **0.343** | above band |
| district_copper | 153.0 | 0.158 | 65.7 | **0.272** | above band |
| district_downtown | 134.2 | 0.153 | 46.9 | **0.232** | IN BAND |
| review_day5_noon | 173.6 | 0.099 | 86.3 | 0.184 | still low |
| review_day1_noon | 83.6 | 0.171 | 0.0 | 0.171 | still low |
| review_day2_noon | 164.5 | 0.096 | 77.2 | 0.162 | still low |
| district_fairview | 167.9 | 0.037 | 80.6 | 0.060 | still low |
| district_ironside | 191.4 | 0.007 | 104.0 | 0.013 | still low |

**Five of seven districts recover into or above the reference band the
moment the exposure lift is taken off.** Their surface detail is
already there and the white ground is hiding it. Chasing that with more
decals would be adding detail to frames that already have enough of it
and cannot show it.

**The honest residual is much smaller than the raw table implies.**
`review_day1_noon` is the control: it is the one daylight frame already
at the references' own ground mean (83.6 vs 87.3), so it needs no
correction, and it reads 0.171 against a floor of 0.211. That is about
**19% short**, not the 86% short that ironside's raw `0.029` against
`0.205` suggests. The gap we have been chasing is roughly a fifth of
its advertised size.

**Two frames do not recover and should be read separately.**
`district_ironside` at 0.013 adjusted is not a surface-detail reading at
all — that frame is a crane at 4m over a bare white plane, and there is
genuinely nothing in its ground band to measure. `district_fairview` at
0.060 is the one district with a real detail case to answer.

**The judgement.** The surface-detail gap is **predominantly an exposure
artifact, not a detail deficit** — five of seven districts prove it by
recovering under a pure additive correction, and the one correctly
exposed daylight frame puts the true residual at about 19%. The queued
decal work is not wrong in principle but it is **mis-sequenced**: it is
being sized against numbers inflated three-to-tenfold by the ground
albedo, and any improvement it lands will be invisible in the stills and
barely visible in `groundPatch` until the ground is darkened. **Fix the
ground albedo first, re-run, re-read `groundPatch`, then decide how many
decals are actually owed.** The two fixes push in opposite directions on
the same number and running them together makes both unreadable.

---

## 4. `ref-bench.py`'s low-content annotation — right frames for its own question, blind to the worst frame in the set, and shipping RED

**It ships red.** `python3 tools/ref-bench.py --selftest` →
**75 passed, 3 failed**:

    FAILED rejecting: district_downtown IS low-content (none)
    FAILED rejecting: its qualifying number is printed with the floor it failed
    FAILED rejecting: district_downtown's line names the ratio row it marks

The rejecting fixture is `district_downtown`, chosen because it was a
near-black frame. **The camera re-site in this very build made it a
bright street frame**, so the fixture no longer has the property it was
picked for. One commit both added the guard and invalidated its
rejecting case. This is CLAUDE.md rule 5b's twin — a guard needs a world
in which the thing it asserts can happen — and the failure is benign in
effect but it means the annotation's rejecting half is currently
unproven.

The docstring has gone stale the same way. It argues "EITHER, NOT BOTH"
using `district_gullwing` as the live proof — "a dark building mass at
arm's length whose groundP90 is 0.360 ... against a groundMean of
0.115". After the re-site gullwing reads groundP90 0.840 / groundMean
0.554. The argument is still sound; its named witness no longer exists.

**Does it flag the right frames?** For the fault it was built for, yes,
exactly. It marks 5 of 17 — `day1_night day2_close day2_night day2_wet
day5_night` — all genuinely dark frames whose ground band is at the
noise floor and whose `shadowRatio` therefore tends to 1 for arithmetic
reasons. `district_hook` and `district_strip` are deliberately left
unmarked, as the ruling required, and that call is still correct.

**But it is one-sided, and the side it is missing is the one this run
found.** The qualifier is `groundP90 < 0.233 OR groundMean < 0.142` —
a FLOOR only. `district_ironside` has the emptiest ground band in the
entire table (`groundPatch` 0.029, adjusted 0.013 — a featureless white
sheet) and sails through unannotated, because its groundP90 is 0.890 and
its groundMean 0.726, both far ABOVE the floors. A frame can be a
reading of nothing by being blown out just as easily as by being black,
and today the blown-out kind is the commoner one:

    reference groundP90  ceiling 0.831   all seven districts: 0.826..0.890
    reference groundMean ceiling 0.543   five of seven:       0.554..0.726

**The one-line fix is symmetry**: qualify on the references' own CEILING
as well as their floor, both recomputed per run exactly as now. That
would mark all seven districts plus `day2_noon` and `day5_noon`, which
is the correct set, and it needs no new constant.

---

## 5. Findings, with instruments

1. **Ground albedo is roughly double what the reference ever shows in
   sun.** `TextureGrade` 0.74 with no ground-side grade and no
   darkening lever but weather. Settled by (b) and (c) in §1 — this is
   a measurement, not a hypothesis.
2. **`district_ironside` is shot into a crane at 4.01m.** Named by the
   engine; `midFrac=0.25` saw it; nothing gates midFrac and the tour
   block does not print it.
3. **`tourDepthBy` ranks the blocked camera as the clearest.** Median
   over rays cannot see a central minority obstruction.
4. **The frustum instrument cannot see a camera inside a hollow mesh.**
   Previous gullwing: 85% wall, bands 0.00/0.00/0.25. HYPOTHESIS as to
   backface cause; the reading itself is fact.
5. **The surface-detail gap is ~19%, not ~80%.** §3.
6. **`ref-bench --selftest` is red on 3 of 78**, fixture invalidated by
   this build's re-site.
7. **The low-content annotation has a floor and no ceiling.**

---

## 6. The single measurement for next landing

Add **`groundOverFrame`** — the ground-band mean luma divided by the
whole-frame mean luma — per shot, on the shot line, beside the existing
`groundPatch`. Gate it to the five references' own band, recomputed per
run as the low-content floors already are: **0.41 .. 0.97**.

Why this one:

- It is **exposure-independent by construction**, so it separates "the
  ground material is too bright" from "the frame is overexposed" —
  which are the two hypotheses with opposite fixes and the reason the
  decal decision is currently unsafe.
- It **cannot be satisfied by the wet term**. Today it reads 1.23-1.38
  on six sunlit frames and 0.61-0.78 on the wet and night ones, so a
  run that only happens to be rainy cannot show green. That is the
  exact masking that hid this for the whole rain era.
- Both halves already exist inside `ref-bench.py` (`groundMean` and the
  whole-frame luma mean); it is a division and a printed band.
- It gives the decal work its **reading rule**: `groundPatch` is only
  interpretable on frames whose `groundOverFrame` is in band. Read it
  anywhere else and you are measuring the albedo, not the surface.

Second, cheaper, and worth taking in the same build:
**`tourBlockerShare`** — the fraction of the 84-ray frustum grid whose
nearest non-player hit is the SAME collider as `shotBlocker`, printed
per district next to the blocker's name. Ironside reads ~0.25 today and
would go red immediately. No distance-band statistic can express "one
object owns a quarter of the frame", because the crane is neither near
(<2m) nor far (>7m), and no median can either.
