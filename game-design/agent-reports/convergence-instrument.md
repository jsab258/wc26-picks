# R1 — the convergence instrument, as built

> **STATUS — LOG, 2026-08-25. NOT CURRENT once the first landing is read** —
> every panel value quoted below is ILLUSTRATIVE and the pitch is a judgement
> that `valueHorizon`'s landed series retires. Builder report
> (instrument-builder). Executes
> `decision-ground-albedo.md` §4/§5 of the ruling headed *"the visual plan is
> REPLACED; cadence rules bind"*. **Nothing is committed.** The resident
> reviews and commits. No build dispatched.

---

## 0. The one-paragraph version

Two halves landed. **The panel** — four value bands per still, shadow:lit,
ground spread, the §5 ordering — measures **every committed still**, not just
the new cameras, so it produces a reading on the nineteen frames this project
already argues about. **The five cameras** stand at named `StreetMap`
junctions at 1.7m and commit as `ref_1..ref_5`. **No bound, no gate, nothing in
`gates.py`** — §5 says the margins come from the landed series and the series
does not exist yet.

**Nothing in this report is a landed number.** The Game layer does not compile
in this container, so no process has ever executed `ValuePanelRead`. Every
sample string below is either **CoreTests output** (real, run, pasted) or is
marked **ILLUSTRATIVE**. The one real measurement I made tonight is on the
reference frames, §6.

---

## 1. Where the five cameras stand, and which of them I judged

One mechanism: a named junction of `StreetMap`'s own scaled grid, a metre
offset in world X/Z, a compass yaw. Eye 1.7m, pitch 5° down, `Feel.BaseFov`
(60° vertical) unchanged. `StreetMap.Node(id)` is asked for every coordinate —
nothing re-derives the 2.15/1.15 stretch, because five raw reads of `AvenuesX`
once aimed four cameras at empty ground 136–184m from the district they were
named after.

| | reference | what the README says carries that frame | district, and why | junction | eye | yaw |
|---|---|---|---|---|---|---|
| `ref_1` | `gta5_1_liquor_store_side_sun` | "dense street furniture in one static shot"; corner frontage under raking side sun | **Copper Row** — the design doc's market quarter, the only district whose brief is shopfronts | `copper_j2_1` (0.0, 128.8) | (0.0, 1.7, 112.8) | 18° |
| `ref_2` | `gta5_2_dusk_vespucci` | "almost nothing but light: low warm sun, silhouetted poles and WIRES" | **the Hook** — Hook Street is a N–S avenue and `UpdateSun` puts the noon sun due SOUTH, so this is the frame that looks into it | `j2_3` (0.0, 29.9) | (0.0, 1.7, 43.9) | 180° |
| `ref_3` | `gta5_3_overcast_morning` | "no interesting light, still fully real — five asphalt tones, tar seams, patched repairs" | **Ironside** — Goods Road runs ~175m with frontage both sides, the longest sight line in the town (measured in the tour's re-site note) | `ironside_j2_1` (36.5, −144.9) | (56.5, 1.7, −144.9) | 270° |
| `ref_4` | `gta5_4_suburban_bmx_noon` | "cracked concrete slabs with grass seams, low fences, roofline variety, towers in haze" | **Fairview** — the residential rise, gardens between junctions, the only low-rise district | `fairview_j1_1` (−344.0, 144.9) | (−344.0, 1.7, 126.9) | 0° |
| `ref_5` | `gta5_5_ps3_sidewalk` | "shadow dapple on a sidewalk, leaning poles, a stained wall … texture density at PLAYER height" | **the Parade** — the promenade district, brief is being seen walking | `strip_j1_2` (253.7, 0.0) | (256.2, 1.7, −20.0) | 0° |

Every district description above is quoted from `StreetMap.cs`'s own district
table or `reference/README.md`. Nothing in that column is my reading of a JPEG.

### What I judged, per camera — the honest list

- **All five: the 5° down pitch.** Nothing in `visual-bar-spec.md`,
  `research/art-direction.md` or `reference/README.md` pins a camera angle.
  The derivation I *can* state: all five references put the horizon above the
  frame's middle (a level camera puts it exactly at the middle), so the pitch
  is DOWN; at 60° vfov a pitch of *p* puts the horizon at row
  `0.5 − tan(p)/(2·tan 30°)` from the top, so 5° lands it at **0.424** and 6°
  at 0.409. **5° is a judgement inside a bracket, not a measurement.** The
  same value on all five so a landed `valueHorizon` series reads as one
  instrument. **`valueHorizon` is the printer that retires this judgement** —
  read the series, then set the pitch, in that order.
- **`ref_1`: the 18° cant and which of the four corners.** The reference is a
  corner shop right-of-centre with the street receding left; 18° puts the near
  block's north-west corner right of centre with Copper Row receding past it.
  Judged.
- **`ref_2`: nothing about the geometry — the LIGHT is the named mismatch.**
  The reference is dusk; this is noon (see §5).
- **`ref_3`: the 20m standoff.** Judged. Everything else (which junction,
  which way) is off the tour's own landed re-site measurement.
- **`ref_4`: the 18m standoff and the direction of travel.** Judged.
- **`ref_5`: the 2.5m lateral offset.** This is the one number that changes
  what kind of picture it is — a road shot at 0m, a pavement shot at 2.5m.
  `StreetMap.AvenueWidth` is 8m and blocks start at half that, so 2.5m is on
  the carriageway with 1.5m clear of the block face. Judged, and it is the
  camera most likely to trip `Shot`'s step-back loop (see §7).

`refPlaced=<found>/<asked>` is on the done line. A junction id that does not
resolve leaves the eye at the origin — the Hook's founding cross, a *real
place* — so five fallbacks would photograph the same pub five times and look
exactly like five matched compositions. That denominator is the only thing
that separates them.

---

## 2. The panel — exact rows, and what statistic each one IS

All ten keys are on the **done line**: every list is complete only when the run
ends. The per-shot numbers inside them are formatted **at their own shot**, so
a row cannot be assembled out of two frames.

| key | what it is a statistic OF | shape |
|---|---|---|
| `refPlaced` | **cumulative count** over the one ref tour: cameras that found their named junction / cameras asked for | `5/5` |
| `valueShots` | **cumulative count**: stills that read pixels back / stills offered | `24/24` |
| `valueRays` | **cumulative counts** over the whole run, as a debugging chain | `55296/41210/41102/sky14086/lit3204/gnd18860/shd9773/oth9373` |
| `valueListed` | rows shown / rows held (the **cap**, announcing itself) | `24/26` |
| `valueRungs` | **cumulative count**: ordering rungs that HELD / rungs any frame could judge | `9/61` |
| `valueBands` | per shot: **MEDIAN** of the frame's luma over that band's samples, `@n` = the samples it is a median OF | `[day1_noon:sky0.34@612/lit0.40@98/gnd0.88@940/shd0.20@410/othnone@0,…]` |
| `valueShadowLit` | per shot: **RATIO OF TWO MEDIANS**, one frame, one instant, disjoint sample sets, with BOTH counts | `[day1_noon:0.500@410..98,…]` |
| `valueGroundSpread` | per shot: **p90 − p10** of the ground samples' luma, printed as the two percentiles it is the difference of | `[day1_noon:0.771..0.940=0.169@940,…]` |
| `valueOrder` | per shot: the §5 ordering as **three separate yes/no answers** plus the tally | `[day1_noon:sky>litn/lit>gndn/gnd>shdy=1of3,…]` |
| `valueAlbedoOrder` | per shot: ground materials sorted ascending **by SOURCE albedo**, `name<source>:<rendered>`, tally = adjacent pairs where rendered ascends too | `[day1_noon:asphalt0.226:0.771<kerb0.267:0.802<sidewalk0.301:0.940=2of2@m3/n940,…]` |
| `valueHorizon` | per shot: **MEDIAN over grid columns** of where the top-connected sky run ends, as a fraction from the TOP, `@cols-with-sky/cols` | `[day1_noon:0.417@58/64,…]` |

**Every value in the shape column above is ILLUSTRATIVE.** Nothing has landed.

### The things a reader will get wrong unless they are told

- **A median cannot see a fault touching under half the band.** That is why
  `valueGroundSpread` is a **separate row over the same samples** rather than a
  summary of `valueBands`, and why every band median carries its `@n`.
- **`none@0` is a reading, not a zero.** A shot down a shaded alley genuinely
  contains no sunlit wall. A band with no samples prints `none@0`, its two
  rungs print `?`, and those rungs count in **neither** half of the tally — so
  a night frame reads as a small denominator, never as a failure.
- **`valueShots=0/0` is "never ran"; `0/24` is "ran 24 times and read nothing
  back".** Different facts, different next actions.
- **`cast − hit == sky` is an identity a reader can check on the printed
  `valueRays` line.** Sky is classified as *the ray hit nothing*.
- **`valueShadowLit`'s two halves can move independently** — a cast shadow can
  deepen while the sunlit wall stands still. Checked by reading the code that
  produces them, per the rule: they are medians over **disjoint** sample sets.
  Two measurements, not one number twice.
- **`valueAlbedoOrder`'s two printed numbers are in DIFFERENT COLOUR SPACES and
  must not be divided.** Rendered is display-referred (the JPEG's own value,
  same space as `groundMaskMeanBy`); `GroundSourceAlbedo` is linear. **The
  TALLY is unaffected** — a transfer function is monotonic, so each side's
  ordering is identical in both spaces. `groundGainBy` is the key that performs
  that division, correctly, two lines further down the same emit.
- **`valueHorizon` is OUR SIDE ONLY and may never be gated against the
  references.** Ours classifies sky with a depth buffer; any reference-side
  equivalent must threshold on colour. Two instruments by construction —
  comparable in direction, never to three decimals.
- **`valueGroundSpread` is NOT `ref-bench`'s `groundPatch`.** That is a median
  over local 64px windows; this is a spread across a frame's ground samples.
  Different questions. They may not be quoted interchangeably.

---

## 3. The ordering line — format, and why it is not one word

§5: *per noon still, `skyBand > litWallBand > groundBand > shadowBand`.*

```
valueOrder=[ref_1:sky>lity/lit>gndy/gnd>shdy=3of3,day1_noon:sky>litn/lit>gndn/gnd>shdy=1of3,…]
```

Three rungs, each `y` (held) / `n` (did not) / `?` (one of its bands had no
samples in this frame), then `heldOfJudged`. **A single pass/fail word would
hide which rung broke**, and which rung breaks is the entire diagnostic value:
`sky>lit` failing is a sky problem, `lit>gnd` failing is the ground-albedo
question, and both failing at once is the inversion the ruling names.

Second half of §5 — *rendered ground lumas ordered as source albedos* — is
`valueAlbedoOrder`, and it contains **no constant at all**: it sorts by the
source albedos the run itself reads and asks whether the rendered side agrees.
`<` joins a pair where the sort makes a claim; `~` joins two materials at the
same source albedo, which carry no claim and sit in neither half of the tally.

**No bound anywhere.** `grep` of the diff finds no comparison against a
threshold, no gate-list entry, and no new row in `gates.py` (which I did not
touch).

---

## 4. What the first landed run will look like

Read in this order.

1. **`refPlaced`.** `5/5` or the compositions are not what they say. Anything
   less and the ref stills for the missing ones are pictures of the founding
   cross.
2. **`valueRays`, as a chain.** `cast/hit/renderer/sky…/lit…/gnd…/shd…/oth…`.
   `lit0` on a noon run means the sun test never admitted a wall — suspect the
   instrument (`GameController.SunwardDir`, the 0.30 dot) **before** concluding
   anything about light. `gnd0` with `renderer` healthy means the material name
   rule, exactly as `groundMaskRays` reads.
3. **`valueOrder` on the four noon rows.** The prediction, stated in advance so
   it is falsifiable: **`sky>lit` and `lit>gnd` both read `n` on every dry noon
   still, `gnd>shd` reads `y`, tally `1of3`.** That is what "near-white ground
   under a storm-dark sky" means arithmetically, and `art-direction.md` §1
   already measured `skyOverGround` at 0.54–1.25 against the references'
   1.35–5.79 on seven of seven. **If the noon rows come back `3of3`, the
   instrument is wrong, not the world** — rule 3, and that is the first thing
   to check.
4. **`valueBands` beside it**, to see the magnitudes rather than the signs.
5. **`valueHorizon`** — the pitch printer. Reference-side comparison in §6.
6. **The five `ref_*.jpg` themselves, before any of the above** (cadence rule
   3b: paired stills are read before any number).

**One number that will look like a fault and is not:** `valueRungs` will read a
small numerator over a large denominator on the first run, because most stills
in a run are night and dusk frames whose `lit` band is empty and whose sky band
is dark. It is a whole-run count over a mixed population, not a score.

---

## 5. What I did NOT do, and the trades

- **No gate, no bound, no threshold.** §5's order of operations. This is the
  single largest thing not done and it is deliberate.
- **All five cameras shoot at NOON, in one instant, immediately after the
  district tour.** §5's ordering is a noon reading, and five frames at five
  hours are five photographs of five moments — the shape this project keeps
  reading as one measurement. **Cost, named: `ref_2` is a dusk reference and
  `ref_3` an overcast-morning one, and both are shot at a dry noon. They match
  their reference's COMPOSITION, not its light.** The next rung has a name:
  repeat `ref_2` at the dusk shot and `ref_3` on an overcast roll. Not taken
  tonight because a second hour doubles the still cost before the first series
  has been read.
- **`tools/ref-bench.py` does NOT see the new frames.** Its `SIM_PREFIXES` is
  `("review_", "district_")` and its `--stable` selftest asserts *"--stable
  keeps only `district_*`"*. The ref frames ARE pose-stable and belong in that
  set, but adding the prefix breaks a rejecting fixture, and repointing a
  selftest is not a thing to do in the same change that creates the frames.
  **Named as the next item**, with its blocker stated.
- **No reference-side band measurement.** ref-bench owns the reference
  comparison (only it can see the references); the verdict owns series and
  constancy. One instrument per job.
- **Aerials not retired.** The ruling says they stop being *judgement* frames;
  the seven `district_*` rows carry landed series and `groundMaskAcross` is by
  name a statistic OF those seven. Retiring them is a director call and would
  be a regime break.
- **`GroundMaskRead` untouched.** Widening its pools with five more shots would
  silently change `groundMaskAcross`'s meaning. The panel uses its own tally
  and its own flag; what the two SHARE is the symbols, not the values.

---

## 6. The one real measurement I made: the reference frames

A throwaway probe (scratchpad, not shipped) using `ref-bench.py`'s own image
loader — not a second reader — over the five committed references at
1280×720, top-connected sky mask (luma > 0.50, saturation < 0.40) per column:

```
gta5_1_liquor_store_side_sun   skyMassEndsRow=0.228  skyShare=0.352  topP50=0.690 botP50=0.246  sky/ground=2.80
gta5_2_dusk_vespucci           skyMassEndsRow=0.182  skyShare=0.277  topP50=0.824 botP50=0.142  sky/ground=5.79
gta5_3_overcast_morning        skyMassEndsRow=0.167  skyShare=0.292  topP50=0.781 botP50=0.237  sky/ground=3.29
gta5_4_suburban_bmx_noon       skyMassEndsRow=0.287  skyShare=0.570  topP50=0.836 botP50=0.495  sky/ground=1.69
gta5_5_ps3_sidewalk            skyMassEndsRow=0.215  skyShare=0.576  topP50=0.753 botP50=0.559  sky/ground=1.35
```

`sky/ground` reproduces `art-direction.md` §1's `skyOverGround` range
(1.35–5.79) exactly on all five, which is the cross-check that the probe is
reading the same frames the project's own numbers came from.

**`skyMassEndsRow` is a colour-threshold statistic and `valueHorizon` is a
depth statistic. They are two instruments and I am not proposing they be
compared to three decimals** — the reference figures are here as a bracket for
the direction (0.17–0.29, sky mass ending well above the frame's middle), which
is what says the pitch is DOWN rather than what says how far.

---

## 7. Cost of committing five more stills — measured, not estimated

**Repository.** Measured over the last twelve stills commits with
`git cat-file -s` on each JPEG blob:

```
ad0def3  20 jpg  2.28 MB      2a70841  20 jpg  2.30 MB      485947d  20 jpg  3.25 MB
7485a36  18 jpg  2.07 MB      7ec933f  18 jpg  2.04 MB      1188f14  20 jpg  3.27 MB
a6d9338  18 jpg  2.07 MB      fae0c70  18 jpg  2.09 MB      28f03a0  18 jpg  2.86 MB
a41d0d5  20 jpg  2.16 MB      7a3d68d  18 jpg  2.01 MB
```

≈ **115 KB per 1280×720 quality-60 frame**, so five more is **+0.57 MB per
stills commit**, a **+27%** increase on the stills payload (2.1 → 2.7 MB).

Stills commits per day, measured: 10, 14, 12, 11, 25, 30, 28 (18–24 Aug). At
the peak rate that is **+17 MB/day**, against a `.git/objects` of **1.9 GB**
today — about **+0.9% of the current repository per day**, or roughly **+0.5 GB
over a month at the 23–24 Aug build rate**.

**That is material and I am saying so rather than shipping it silently.** Two
things about it, both honest:

- The ruling's own logic points at a NET SAVING, not a cost: aerials stop being
  judgement frames, and the seven `district_*` frames are ~0.8 MB/commit. If
  the ref series proves out, retiring or thinning them more than pays for these
  five. That is a director call and I have not made it.
- If the cost is judged too high before then, the cheapest lever is **quality
  60 → 45 on the `ref_*` frames only**, which is a one-line change and roughly
  halves them. I have not taken it: changing encode quality on a judgement
  frame without a landed comparison is a visual change with no measurement.

**Run time — ESTIMATE, and marked as one because nothing here can measure it.**
Five extra `Shot()` calls against 19–21 existing ones is ~25% more shot work
(render + `ReadPixels` + JPEG encode). The panel's own per-shot cost is small
next to what a shot already pays: 2,304 raycasts plus one `GetPixels32`.
`GetPixels32` and not `GetPixels` is deliberate and is the one performance
decision I made — a 1280×720 `Color[]` is 14.7 MB of garbage per shot and a
`Color32[]` is 3.7 MB, and this read runs on **every** committed still where
`GroundMaskRead` runs on seven. `research/performance-budget.md` names MEMORY
as the visual plan's real ceiling, so a four-fold allocation on a diagnostic
would be spending the scarce budget on commentary. The measured denominator
that exists: `meanFrame=28.58ms` at 720p, and the run already pays for a full
extra *render* per district shot (the `FilmGrade.Bypass` twin), which is
strictly more expensive than anything added here.

---

## 8. The bug grep found before a build did

`tools/sim-shots-stage.sh` and `tools/sim-shots-commit.sh` carry the **same
glob list** three files apart. I added `ref_*.jpg` to the first and grepped the
distinguishing token — the second was missing it. The symptom would have been
`refPlaced=5/5` in the verdict with no `ref_*.jpg` in the repository: rendered,
never copied, one round trip to see. **`sim-shots-commit.sh`'s own comment is a
record of this exact pair failing this exact way for `hunt_*`**, which is why
the fix carries a note saying so. Both are fixed.

---

## 9. Files touched

| file | what |
|---|---|
| `ledger/Assets/Scripts/Core/ValuePanel.cs` | **new.** All the panel arithmetic and every string it prints. In Core because a formatter written in the Game layer ships UNRUN. |
| `ledger/CoreTests/Program.cs` | `TestValuePanel()` + its call. 35 `Check` calls (44 assertions — the whitespace loop runs ten times), accepting case first. |
| `ledger/Assets/Scripts/Game/SimDirector.cs` | `ValuePanelRead` (the classifier + ray grid), `RefTour`/`RefVantage`, `_refTour` flag and the still-naming/quota change, the ten done-line keys, and `WallFaceDot`/`SunFaceDot`/`SunRayM` hoisted out of `FindShadowPair` so both sites share one symbol. |
| `tools/sim-shots-stage.sh` | `ref_*.jpg` added to the by-name stage list. Selftest re-run, all three cases pass. |
| `tools/sim-shots-commit.sh` | the same glob's twin, §8. |

Untouched, as instructed: `WorldBuilder.cs`, `StreetFurniture.cs`,
`StreetDressing.cs`, `tools/gates.py`, `tools/hang-report.py`,
`ledger/verify.py`, `.github/workflows/**`.

### Why a third ray grid exists in `SimDirector`, checked before writing it

`ShotSightlines` asks *how much of the cone is blocked within 2m* and keeps no
material and no pixel. `GroundMaskRead` asks *which pixels are ground and how
bright* — it has the pixel and the material and **not the sun**, and it feeds a
per-district series whose meaning would change the moment five more shots
joined its pools. This one asks *which value band is this pixel in*, which
needs a sun vector and a shadow raycast neither of the others casts. The shared
part is the three lines that cast a ray and read a pixel; **every part that
could go stale — the ground name rule, the up-facing test, the grid size, the
wall and sun dots — is the same SYMBOL, not a copy of its value.**

---

## 10. The selftest, both cases, output pasted

`ledger/CoreTests` — accepting case first (rule 5b), then the case the
instrument exists for, then eight rejecting cases.

```
Value panel — the four bands, their order, and the ground spread:
  ok - a column whose top cell is not sky has no sky run
  ok - the horizon is a median over the columns that HAVE sky
  ok - the four band medians print with the counts they are medians OF
  ok - shadow over lit is one ratio carrying BOTH denominators
  ok - the ground spread prints the two percentiles it is the difference of
  ok - a reference-shaped frame holds all three rungs
  ok - rendered ground lumas ordered as source albedos, sorted BY source
  ok - the horizon row prints the columns it is a median over
  ok - shots measured over shots offered
  ok - the ray chain says where classification died, and cast-hit==sky
  ok - rungs held over rungs judged
  ok - rows shown over rows held
  ok - no panel value contains whitespace          (x10, one per emitted key)
  ok - an inverted frame prints WHICH rung broke, not a single word
  ok - and the run tally carries the same count
  ok - a frame with no sky prints words for its horizon, not a zero
  ok - a panel that never ran prints WORDS in every row
  ok - and its denominators are all zero-over-zero
  ok - a shot that cast no rays counts as offered and not as measured
  ok - an empty band prints none@0, which cannot read as black
  ok - a rung nobody could judge is ? and is in neither half of the tally
  ok - a ratio with no denominator prints words and keeps both counts
  ok - a shot with no classified ground material says so in words
  ok - a zero lit median prints words rather than an enormous ratio
  ok - the darker source rendering brighter is a discordant pair
  ok - equal source albedos join with ~ and sit in neither half of the tally
  ok - the cap prints shown over held
  ok - and the truncated list says so inside its own bracket
  ok - the cap notice does not introduce a space
  ok - a shot name with spaces cannot split the verdict
  ok - every structural character in a shot name folds to _
  ok - no grid is not a horizon of zero
  ok - an array too short for the grid is refused
  ok - a frame with no sky in it prints -1, which cannot be a fraction
  ok - a frame that is all sky puts the horizon at the bottom of frame
```

The **accepting** fixture pins every row character for character:

```
valueBands        [ref_1:sky0.720@3/lit0.510@2/gnd0.370@6/shd0.190@2/othnone@0]
valueShadowLit    [ref_1:0.373@2..2]
valueGroundSpread [ref_1:0.310..0.430=0.120@6]
valueOrder        [ref_1:sky>lity/lit>gndy/gnd>shdy=3of3]
valueAlbedoOrder  [ref_1:asphalt0.200:0.310<kerb0.260:0.370<sidewalk0.300:0.430=2of2@m3/n6]
valueHorizon      [ref_1:0.500@3/4]
valueRays         15/12/12/sky3/lit2/gnd6/shd2/oth0
```

The **rejecting** fixture that matters most is the second one — our own frames:

```
valueOrder        [day1_noon:sky>litn/lit>gndn/gnd>shdy=1of3]
```

An instrument that cannot print the inversion it was built to find is worth
nothing, so that case is pinned as tightly as the accepting one.

`tools/sim-shots-stage.sh --selftest`, all three cases:

```
  accepting: framesStaged=2/2 framesRows=2 framesUnstaged=[none]
sim-shots-stage --selftest: ok — a run that photographed both rows reads 2/2
  rejecting: framesStaged=1/3 framesRows=3 framesUnstaged=[day12_noon/day13_noon]
sim-shots-stage --selftest: ok — a stale picture and a row with no picture are both named
  never-ran: framesStaged=no-ledger-this-run framesRows=0 framesUnstaged=[no-ledger]
sim-shots-stage --selftest: ok — no ledger prints words, not 0/0
```

---

## 11. Which existing conclusions this confirms or overturns

It **overturns nothing** — it has never landed, and a printer that has not run
cannot overturn a reading.

What it does is make **one existing conclusion falsifiable for the first
time.** The value-structure inversion is currently established from
`art-direction.md` §1's local, hand-run measurements over committed JPEGs
(`skyOverGround` REF 1.35–5.79 vs SIM 0.54–1.25, 7/7). Per the 25 Aug ruling
§C, **no ref-bench key has ever reached a verdict** — the whole GTA comparison
to date is hand-run, which is exactly how two people came to run the same tool
and produce two different instruments. `valueOrder` and `valueBands` put that
finding in the verdict, per run, with denominators, so it gains a landed series
and a regime history.

**One thing it can settle that nothing currently can.** `art-direction.md`'s
`skyOverGround` is a ratio of two ROW-BAND medians — top 20% of rows over
bottom 35% — so it cannot distinguish *the sky is dark* from *a building fills
the top of frame*, and it cannot see the lit wall or the cast shadow at all.
The panel classifies by what the ray hit. If the two disagree on a frame, the
disagreement is itself the finding, and per rule 3 the instrument is the first
suspect, not the world.

---

## 12. Verify footer

**Read from `ledger/.verify-footer` on disk: THE FILE DOES NOT EXIST.** A red
run deletes it. The run was red on exactly one gate:

```
DIRECTOR NOT SPAWNED: 1508 changed line(s) (1026 tracked + 482 untracked in 1 new
file(s)) vs 100 threshold under Assets/Scripts, 0 director row(s) newer than the
reference … — spawn studio-director for the batch review, then re-run verify
```

That is `director_cadence` doing its job: this is builder work and the director
row is the resident's to write at review. **It is not a fault in this work and
I have not tried to clear it.** Everything else in the same footer is green,
and these are the lines that matter for this change:

```
0 lint errors, 0 shape errors (190 files), 0 shadowed Core types,
35 on the reach ledger, Game layer compiles (184 files),
0 nested-type errors (254 Core types), 0 static/instance errors (75 members, 559 bodies),
0 raw avenue reads (184 files), 0 filename-as-type errors (190 files),
0 namespace-as-value errors (190 files, 4 segments in scope),
verdict format ok (selftest + newest run), verdictSpaced=35/131 not gated,
emit dupkeys ok (0, 112 log call(s) across 184 file(s)),
gates 18 bare / 41 detailed, ceiling 18,   4049 CoreTests.
```

`gates 18 bare / 41 detailed, ceiling 18` is unchanged from before this work —
**no gate was added**, which is §5's instruction.

Two lints earned their keep on the first pass and are recorded because a lint
that never fires is indistinguishable from one that is not wired:
`lint-usings` caught a Core field named `Cast` reading as `System.Linq.Cast<T>`
(renamed `RaysCast`), and the reach check caught two public accessors nothing
called (deleted).

**ShapeCheck is reference-independent**, so anything needing a name RESOLVED is
invisible to it. The five name-matching lints all pass. What remains
first-compiled on Windows: `Texture2D.GetPixels32` into a `Color32[]`,
`StreetMap.Node` in `RefVantage`, and `Quaternion.Euler` on the ref cameras.
That is what the round trip is for.

---

## 13. Next, by name

1. **Read the first landed run in §4's order.** Nothing is set from it except
   the pitch bracket.
2. **`valueHorizon` series → the ref cameras' pitch**, once there are two or
   three landings. Today's 5° is a judgement.
3. **`ref_2` at dusk and `ref_3` on an overcast roll** — the two named light
   mismatches.
4. **`ref-bench.py`'s `SIM_PREFIXES` to include `ref_`**, which needs its
   `--stable` rejecting fixture repinned first (§5).
5. **A bound on `valueOrder`** — only after a landed series, only from the
   references' own order, and only as a director close-out.
