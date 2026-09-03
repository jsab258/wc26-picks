# R1 — the convergence instrument, as built

> **STATUS: LOG, 2026-08-25. NOT CURRENT once the first landing is read** —
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
| `ref_2` | `gta5_2_dusk_vespucci` | "almost nothing but light: low warm sun, silhouetted poles and WIRES" | **the Hook** — Hook Street is a N–S avenue. *(This cell said "`UpdateSun` puts the noon sun due SOUTH, so this is the frame that looks into it". FALSE — measured `Euler(52,180,0)` gives sunward (0,+0.788,+0.616), so the sun is in the NORTH and only north-facing walls are ever lit. Kept quoted: this sentence is why three cameras were aimed at the shaded side. The camera is right; its stated reason was not.)* | `j2_3` (0.0, 29.9) | (0.0, 1.7, 43.9) | 180° |
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

---

# REPAIR PASS — weather per sample, and the three blind cameras (2026-08-26)

> **STATUS: LOG, 2026-08-26. NOT CURRENT once the next verdict lands.**
> Builder report (instrument-builder). Executes
> `decision-2026-08-25-valuepanel-landing-and-batch.md` §A items 1 and 2, capped
> at one dispatch cycle. **Nothing committed, no build dispatched.** The
> resident reviews and commits.
>
> **`SunwardDir` correction — read this before anything else in this file.**
> The `ref_2` row of the table above says *"`UpdateSun` puts the noon sun due
> SOUTH, so this is the frame that looks into it"*. **That sentence is false**
> and it is quoted rather than edited, because it is the direct cause of three
> of the five cameras photographing no sunlit wall. See §2.

## 1. WHAT CARRIES WEATHER, AND WHERE IT IS READ FROM

**One source, one implementation.** `ValuePanelRead` reads `Weather.Rain` and
`Weather.Wetness` — the *same two statics* `SimDirector.LedgerRow` writes as
the last two columns of every `frames.tsv` row — inside the same `Shot` call
that encodes the JPEG and writes the tsv row, with **no time step between the
three**. The panel row, the picture and the tsv row are one instant by
construction. Nothing recomputes a wetness and there is no second rule to
drift.

**A join would not have worked, which is the argument for carrying it rather
than looking it up.** The `street` row is taken *inside* the `day3_noon` shot
and has no row of its own in `frames.tsv`. "Look the weather up by shot name"
returns nothing for it — silently. That is the shape of a reader getting a
confident wrong answer, and it is the case the emit removes.

**What is emitted.**

| where | shape | statistic |
|---|---|---|
| every per-shot row of `valueBands`, `valueShadowLit`, `valueGroundSpread`, `valueOrder`, `valueAlbedoOrder`, `valueHorizon` | label becomes `<shot>%r<rain>w<wet>` | last-wins read of live weather at the one instant the shot exists |
| `valueWeathers` (NEW key, done line) | `[r0.35w1.00:shots3/rungs3of7,...]` | a TALLY per distinct state: MEASURED shots, and that state's own rungs held/judged |

- **`%` appears nowhere else** in any row, and `Safe()` now folds it out of
  shot names, so a shot literally called `ref_1%r0.00w0.00` cannot forge a
  second tag. Pinned by a selftest fixture whose name ends `%r9w9`.
- **Unrecorded weather prints the WORDS `weather_unknown`,** never `r0.00w0.00`.
  Zero is DRY — a real, common, and in this project a *misleading* regime — so
  defaulting an unknown to it would file the unmeasured with the dry. `Open`
  takes a negative for "not known" and there is no zero-argument overload to
  reach for by accident.
- **`valueRungs` now says in its own comment that it POOLS** soaked noons, dry
  noons, dusk and night, and may not be quoted as a dry reading. `valueWeathers`
  is the same tally split by regime and is the row that answers *"does the
  order hold on a dry road"*.
- **Nothing classifies wet from dry.** The states are whatever the run
  produced; where the line between them falls is a question for the landed
  series (rule 2). **No bound, no gate** — every method is still a printer.

**The retraction this repairs, in numbers.** `day1_noon` reads sky 0.445 /
ground 0.237 — the reference order — and is `rain=0.35 wet=1.00`, a soaked
road. The **dry** aerial `day5_noon` reads sky 0.441 / ground **0.719**,
inverted exactly like the five eye-level frames. It was the rain, not the
angle. The selftest's rejecting fixture was renamed from `day1_noon` to
`day5_noon` for this reason: the inverted fixture now matches the frame that
is actually inverted.

## 2. WHICH CAMERAS MOVED, AND WHY — THE SUN IS IN THE NORTH

**Measured, not reasoned.** `UpdateSun` sets `azim = Lerp(70, 290, dayT)` and
`elev = Sin(dayT*PI)*52`, so at noon (`dayT` 0.5) the light is
`Euler(52, 180, 0)` and

    SunwardDir = -forward = (0.000, +0.788, +0.616)

The noon sun stands in the **+Z sky, which is NORTH**. A vertical wall enters
the `lit` band at `dot(n, sunward) >= SunFaceDot` (0.30), i.e. normal z at or
above `0.30/0.616 = 0.487`. In a town built of axis-aligned boxes that admits
**exactly one family of walls: the north-facing ones.**

**Five for five, with a mechanism — and seven more confirming it.**

| camera | old yaw | faces | landed `lit` |
|---|---|---|---|
| `ref_1` | 18 | north | `none@0` |
| `ref_4` | 0 | north | `none@0` |
| `ref_5` | 0 | north | `none@0` |
| `ref_2` | 180 | away from north | **404** |
| `ref_3` | 270 | away from north | 9 (grazing) |

The seven district cameras are the same table again and were **not touched**:
five look north and read `litnone@0` (hook, copper, downtown, strip, fairview);
Ironside and Gullwing look west and read 36 and 88. That is *confirming
evidence on already-landed data*, not a second repair — those seven carry a
landed series the ref five do not.

**The repair is a reflection, not a new composition.** Each of the three keeps
its junction, its standoff MAGNITUDE and its cant / lateral-offset MAGNITUDE.
What flips is the sign of the along-street offset and the yaw — the same
picture from the other end of the same street, with the frame's handedness
preserved. Junction coordinates and block faces below are **measured** by
running `Core.StreetMap` directly, not read off a comment.

| | was | now | why, and what is now in shot |
|---|---|---|---|
| `ref_1` | `dz -16`, yaw 18 | `dz +16`, **yaw 198** | copper_j2_1 = (0.0, 128.8). The south blocks' NORTH faces at z 124.8 span x[-39,-4] and [4,39], 20m ahead, near face-on; ~33m of them inside the 91° horizontal frustum. The 18° cant puts the SW corner just left of centre with its north frontage filling right of it and the avenue receding left — the reference's shop-right / street-left shape, now with the shop frontage in sun. |
| `ref_4` | `dz -18`, yaw 0 | `dz +18`, **yaw 180** | fairview_j1_1 = (-344.0, 144.9). South blocks' north faces at z 140.9, 22m ahead; ~37m visible. The composition is symmetric about the street axis, so reversing the direction of travel keeps it — and the direction of travel was already named a JUDGEMENT in the original entry. |
| `ref_5` | `dx +2.5, dz -20`, yaw 0 | `dx -2.5, dz +20`, **yaw 180** | strip_j1_2 = (253.7, 0.0). Both offsets and the yaw mirrored through the junction. The close wall stays a SIDE face and stays unlit — *that is the reference*, a shaded near wall. What the mirror buys is the cross-street frontage beyond it: the north face at z = -4 is visible from x 249.7 down to about x 226.6, ~23m of wall at 24–34m, filling the right half beyond the near corner. Clearance is unchanged at 1.5m (|2.5| off a 4m half-width). |

`ref_2` and `ref_3` are **untouched** and their series continues.
`RefPitchDeg` is **untouched at 5°**, so `valueHorizon` still measures one
instrument across all five and can still retire the pitch judgement from a
landed series.

**REGIME CHANGE, DECLARED RATHER THAN DISCOVERED.** Every `ref_1`, `ref_4` and
`ref_5` number landed before this commit came from a different vantage. **Read
the next landing as a new baseline for those three, not as a delta.**

**Two false comments corrected in `SimDirector`, both quoted rather than
deleted** (`RefVantage`'s `ref_2` entry, and the `downtown` district-vantage
entry which said the noon shadow "falls east of the corridor"). The downtown
CONCLUSION survives its wrong reason: slot 25 sits at z[-42.1,-6.9], its 26.6m
noon shadow runs due SOUTH to z -68.7, and the corridor begins at z +5.1.
**Two more copies of the same false sentence are outside my file scope and are
NOT edited** — flagged for the resident: this file's own table row 43, and
`agent-reports/tour-camera-resite.md` line 90.

## 3. THE FRESH PREDICTION — written before the run

Last pass's prediction (`sky>lit n / lit>gnd n / gnd>shd y = 1of3`, *"if they
come back 3of3, suspect the instrument first"*) held: `ref_3` landed exactly
that and nothing returned 3of3.

**A. `valueWeathers` — an identity, and it is the cheapest check on the board.**
The `shots` field summed across every regime **MUST equal the numerator of
`valueShots`**. From b7d232b's `frames.tsv` and its 23 measured shots I predict
**four regimes, in this first-seen order**, summing to 23:

    r0.35w1.00:shots3   (day1 noon/dusk/night)
    r0.00w0.62:shots1   (day2_noon)
    r0.90w1.00:shots4   (day2_wet, street, day12 noon/night)
    r0.00w0.00:shots15  (day2_night, day5_noon, 7 districts, 5 refs, day5_night)

`street` landing under `r0.90w1.00` rather than dry is the specific case a
name-join would have got wrong.

**B. The three re-aimed cameras stop printing `?`.** I predict `lit` becomes
non-empty on `ref_1` and `ref_4` — order of hundreds of samples, comparable to
`ref_2`'s 404 — so all three rungs become judgeable on both. **`ref_5` is the
one I am least confident about**: its lit band is a cross-street frontage
partly occluded by the near corner, so I expect *tens*, not hundreds, and it is
the plausible remaining `none@0`.

**C. What the rungs will SAY, and it is not good news.** For all three I
predict **`sky>lit n / lit>gnd n / gnd>shd y = 1of3`** — the same reading
`ref_3` already gives. Ground on these frames is 0.819–0.848 against skies of
0.658–0.716; turning a camera round does not change an albedo pipeline.
Across the five ref cameras the *held* count should stay near **6**, while the
*judged* denominator rises from **9 to about 15**. The denominator is the
falsifiable half.

**D. The alarms — any of these means suspect the instrument, not the subject.**

1. **Any re-aimed camera returns `3of3`.** A camera pointing the other way
   cannot fix a road that renders 0.853 from an albedo of 0.008. If the order
   suddenly holds, the panel changed, not the world.
2. **All three still return `litnone@0`.** Then the sun derivation above is
   wrong — most likely because the ref tour does not actually run at noon, in
   which case `azim != 180` and the whole north-facing argument shifts. The next
   move then is to **print the distribution of `dot(n, sunward)`**, not to move
   a camera a second time.
3. **`gnd>shd` flips to `n` anywhere it was `y`.** Nothing in this pass touches
   the shadow classifier; that would be the classifier.
4. **`valueWeathers` shows one regime**, or its `shots` sum disagrees with
   `valueShots`. Either means the weather is not being read at the shot.

## 4. VERIFY — footer read from disk

**There is no footer to paste. `ledger/.verify-footer` does not exist**, which
is what a red run leaves behind, and the honest report is to say so rather than
quote the scrollback the file exists to replace.

**The only red is `director_cadence`** — *"DIRECTOR NOT SPAWNED: 452 changed
line(s) ... 0 director row(s) newer than the reference"* — the batch-review
gate, cleared by the resident spawning `studio-director`, not a fault in this
work. The 452 lines include two other agents' in-flight edits
(`WorldBuilder.cs`, `tools/lint-static.py`), which are untouched here.

Every other clause of that same footer is green, including the ones this pass
could have broken:

    0 lint errors, 0 shape errors (191 files), 0 shadowed Core types,
    docs 105/105 clean, Game layer compiles (185 files),
    0 nested-type errors (255 Core types), 0 static/instance errors,
    0 filename-as-type errors (191 files),
    0 namespace-as-value errors (191 files),
    verdict format ok (selftest + newest run), 4104 CoreTests.

`valueWeathers` is **not yet in `verdict-keys.json`** — nor are `valueBands`,
`valueOrder` or `valueRungs`, which landed one build ago. The registry learns
from landed runs; nothing here needs a hand edit.

## 5. WHAT THIS PASS DID NOT DO

- **No bound and no gate.** §5 is unchanged: the ORDER comes from the
  references, the MARGINS come later from the landed series. One landing is not
  a series.
- **The seven district cameras were not re-aimed**, though five of them have
  the identical fault. They carry a landed series; the ref five did not. That
  is a director call, not a builder one.
- **`ref_2` at dusk and `ref_3` on an overcast roll** remain the named light
  mismatches and the next rung for this instrument.

---

# R3 — the district reflection, 2026-08-26

> **STATUS: LOG, 2026-08-26. NOT CURRENT once the next Windows build lands.**
> Builder report (instrument-builder). Executes the director's conditional
> ruling now that `c5a75c9` confirmed the reference prediction. **Nothing is
> committed. No build dispatched.** The resident reviews and commits.
> Files touched: `ledger/Assets/Scripts/Game/SimDirector.cs` only.
> `Core/ValuePanel.cs` was NOT touched — no arithmetic, no formatting and no
> key changed, so there was nothing for it to do.

## 0. The one-paragraph version

**One character of behaviour changed.** `TourVantage`'s default approach goes
`az = -34f` -> `az = 34f`, which reflects five district cameras through their
own target and turns them from looking NORTH into looking SOUTH. The whole rest
of the 318-line diff is the regime declaration and the prediction. Ironside and
Gullwing are untouched by construction — the branch that sets `ax = 34f; az =
0f` still writes over the new default, so their eye is byte-identical either
side of the break and they remain the only comparators that span it.

    $ git diff -U0 ... | grep -v comment
    -            float ax = 0f, az = -34f;
    +            float ax = 0f, az = 34f;

## 1. Which five moved, and to what

Junctions and block faces below are **measured by running `Core.StreetMap`
directly** (a scratch `net8.0` console project compiling
`Assets/Scripts/Core/**`), never read off a comment. `camZ`/`camYaw` "was"
values are read from the landed `game-design/sim-shots/frames.tsv` at
`c5a75c98`, not from the source.

| row | eye was | eye now | yaw | target it is 34m from |
|---|---|---|---|---|
| `district_hook` | (0.0, 14, **-34.0**) | (0.0, 14, **+34.0**) | 0 -> **180** | `CentreOf(hook)` (0.0, 0.0) |
| `district_copper` | (0.0, 14, **94.8**) | (0.0, 14, **162.8**) | 0 -> **180** | `CentreOf(copper)` (0.0, 128.8) |
| `district_downtown` | (-365.5, 14, **5.1**) | (-365.5, 14, **73.1**) | 0 -> **180** | `downtown_j1_2` (-365.5, 39.1) |
| `district_strip` | (253.7, 14, **-34.0**) | (253.7, 14, **+34.0**) | 0 -> **180** | `CentreOf(strip)` (253.7, 0.0) |
| `district_fairview` | (-344.0, 14, **110.9**) | (-344.0, 14, **178.9**) | 0 -> **180** | `fairview_j1_1` (-344.0, 144.9) |
| `district_ironside` | (70.6, 14, -144.9) | **unchanged** | 270 | `ironside_j2_1` (36.6, -144.9) |
| `district_gullwing` | (240.4, 14, -147.2) | **unchanged** | 270 | `gullwing_j0_1` (206.4, -147.2) |

**`downtown` is inside the break and the file said otherwise.** Its 25 Aug
re-site chose the CROSSING; it never changed the APPROACH, so it took the
default `az` like the other four. The doc line above `TourVantage` read *"THE
DEFAULT, UNCHANGED FOR FOUR OF SEVEN"* — five, not four. Corrected in place and
kept quoted, because "four of seven" is exactly the arithmetic that would let
the next reader put `downtown` outside the break.

### What each new eye actually has to photograph — measured, not asserted

North-facing (i.e. sunward) block frontage inside the 45.7-degree horizontal
half-frustum within 120m, from `StreetMap.Blocks`:

| row | sunward frontage in frustum | faces | near rank | was (shaded frontage, old eye) |
|---|---|---|---|---|
| `district_copper` | **284.4m** | 8 | 15.0m | 92.8m |
| `district_hook` | **194.0m** | 8 | 8.1m | 194.0m (exact mirror) |
| `district_downtown` | **188.9m** | 5 | 38.0m | 113.0m |
| `district_strip` | **166.7m** | 6 | 12.7m | 166.7m (exact mirror) |
| `district_fairview` | **70.0m** | 2 | 38.0m | 70.0m (exact mirror) |

Hook, strip and fairview are exact mirrors because their block grid is
symmetric about the district centre. Copper and downtown are not, because their
eye reflects through a JUNCTION rather than through the centre — copper's new
sight line runs 107m down into the Hook's north faces, and downtown's runs to a
second rank at 72.5m.

**That sum is a horizontal bound, not a ray count.** It ignores vertical
occlusion by nearer roofs, props, vehicles and walkers. Two things it does let
me say, both arithmetic off the 52-degree noon sun:

- **Self-shadowing across an 8m avenue is negligible here.** The sunward
  vector is `(0, +0.788, +0.616)`, so a ray crossing an 8m carriageway climbs
  `8/0.616 * 0.788 = 10.23m`. Terraces are 6.2-10.4m (`WorldBuilder` line 966),
  so a terrace opposite shadows only the bottom **0.17m** of the wall. The near
  rank of all five has nothing north of it at all. `lit` will not be eaten by
  the `SunRayM` (60m) re-cast on the terrace districts.
- **Fairview is the weak one, for a named reason.** 70m is a third of the
  others'; its far wall is villas 5.5-7.5m seen over its own near block's roofs
  from 14m up, leaving a visible band of roughly 11.2-14.0 degrees of
  depression — under 3 degrees of a 60-degree frame.

## 2. Where the regime change is declared

**In the code, at the emit** — a block headed `REGIME BREAK, 26 AUG — FIVE
district_* ROWS` immediately above `$"valueBands={_valuePanel.Bands()} "` in the
done-line emit (`SimDirector.cs`). It states the director's three things
explicitly: (1) the pre-break `lit` column on those five carries no information
and a `none@0` from a blind camera is not a `none@0` from a district with no
sunlit wall; (2) EVERY other column on those rows is old-aim-only —
`valueShadowLit`, `valueGroundSpread`, `valueOrder`, `valueAlbedoOrder`,
`valueHorizon`, and sky/gnd/shd/oth — read the next landing as a new baseline,
not a delta; (3) `district_ironside` and `district_gullwing` are the ONLY
comparators that span the break, and that is why they were not re-aimed.

Three further declarations sit at `TourVantage` (why the sign flipped and what
did not move), at the gullwing/ironside branch (why those two must not be
touched, and that the line still writes `az = 0f` over the new default), and in
the `downtown` vantage entry.

**And the break is legible in the REPORTED output, not only in the source** —
by an instrument that already exists. `tools/frame-drift.py` conditions on
`POSE = [camX, camZ, camYaw]` with `POSE_SAME_M = 0.5`. I did not write a
second one.

    === ACCEPTING CASE: the live ledger against itself ===
    FrameDrift:   34 of 34 shot(s) taken from the SAME VANTAGE and comparable;
                  0 moved, 0 unrecorded.

    === REJECTING CASE: the live ledger against Identity A applied ===
    FrameDrift:   29 of 34 shot(s) taken from the SAME VANTAGE and comparable;
                  5 moved, 0 unrecorded.
    FrameDrift:   district_hook     ... [CAMERA MOVED 68.0m yaw 180deg]
    FrameDrift:   district_copper   ... [CAMERA MOVED 68.0m yaw 180deg]
    FrameDrift:   district_ironside ... [same vantage, a normal build step]
    FrameDrift:   district_downtown ... [CAMERA MOVED 68.0m yaw 180deg]
    FrameDrift:   district_strip    ... [CAMERA MOVED 68.0m yaw 180deg]
    FrameDrift:   district_fairview ... [CAMERA MOVED 68.0m yaw 180deg]
    FrameDrift:   district_gullwing ... [same vantage, a normal build step]

Accepting case first, as the rule requires, and the accepting fixture is the
live ledger. The rejecting fixture is synthetic (`camZ + 68.0`, `camYaw 180` on
the five and nothing else touched) — it names a pose no landed run has, so
doing the work cannot break the check. `tools/frame-drift.py --selftest`:
**40 passed, 0 failed.**

## 3. THE FRESH PREDICTION — written before the run

The full text is in `SimDirector.cs` under `PREDICTED NEXT LANDING (26 AUG)`.
Summary:

**IDENTITY A — `frames.tsv`, the cheapest check on the board.** Every
`district_*` row's `camX` is UNCHANGED; `camZ` moves by EXACTLY **+68.0** on
five rows and EXACTLY **0.0** on two, so the seven deltas sum to **+340.0**;
`camYaw` goes 0 -> 180 on the five and stays 270 on the two. +68.0 is 2x the
34m standoff and nothing else in the vantage moves. Any other delta means the
change did something besides reflect, and every reading below is void before it
is read. `tourResited` must stay **3/3** — the re-aim touches no junction
lookup.

**IDENTITY B — `valueRungs`.** Today **30/53**. The five blind rows each
contribute `1of1` because two of three rungs print `?` for want of a `lit`
band; give all five a `lit` band and each denominator goes 1 -> 3. So the
denominator must land at **exactly 63** (+10) and `valueWeathers`' `r0.00w0.00`
row must go `rungs20of33` -> **`20of43`**.

**C — per-camera `lit`, as an order of magnitude.** All five stop printing
`none@0`, ranked **downtown > copper ~ strip > hook >> fairview**: downtown in
the high hundreds (12-22m offices at 38m overtop a 14m lens and fill the
frame), copper/strip/hook low-to-mid hundreds, **fairview the plausible
remaining failure at tens or fewer**. Medians land **0.45-0.75**, not 0.8 — the
aerial controls are the right reference class (`lit` 0.532 and 0.685) and not
the street refs (0.780-0.814).

**D — the rungs, and the sky is the band out of place.**

    sky>lit   FAILS on all five   (sky ~0.36-0.45 against lit 0.45-0.75)
    lit>gnd   FAILS on 3-5 of 5   — LEAST CONFIDENT, and the rung the ref
                                    prediction got wrong in the good direction
    gnd>shd   HOLDS on all five   (it already does)

So `valueRungs` **30/63** if `lit>gnd` fails everywhere, up to **35/63** if it
holds everywhere. A numerator above 35 is arithmetically impossible from this
change.

**And the sky's COUNT should rise while its MEDIAN should not.** Looking south
there is no skyline band at all — replaying `BuildSkyline` against today's
`StreetMap.BoundsOf` shows slots 17-26, the whole S edge, dropped by
`if (edge == "S") continue`, where looking north there were eleven slots at
z 317-441. So the below-horizon miss wedge widens from ~1.3 to ~3.1 degrees.
If the count rises and the median rises with it, that is the sky gradient and
it is a subject finding; if the median moves while the count does not, read
alarm 1.

### The four alarms, each saying which way to suspect

1. **INSTRUMENT, NOT SUBJECT — any of the five returns `litnone@0` again.**
   70-284m of measured sunward frontage stands in each frustum at 8-38m,
   unshadowed by the arithmetic in §1. Zero lit rays against that is not a fact
   about a district. **Read `oth` on the same row FIRST**: if `oth` has risen by
   hundreds while `shd` fell, `GroundSurfaceOf` is claiming the facades as
   ground and routing them out of the wall test — the material classifier is
   the fault, not the aim.
2. **INSTRUMENT, NOT SUBJECT — either control moves.** Printed series for the
   two untouched cameras, all the landed data there is (the panel is two runs
   old), newest first:

   | | `district_ironside` | `district_gullwing` |
   |---|---|---|
   | c5a75c9 | sky0.376@489 lit0.532@37 gnd0.720@1507 shd0.209@152 oth0.087@119 | sky0.371@550 lit0.685@82 gnd0.706@634 shd0.176@276 oth0.629@762 |
   | b7d232b | sky0.383@524 lit0.534@36 gnd0.721@1547 shd0.202@147 oth0.212@50 | sky0.376@582 lit0.689@88 gnd0.713@636 shd0.177@274 oth0.629@724 |

   Every band median moved by at most **0.007** and `lit`'s count by at most
   **6**, across a step that included the ground-albedo landing — while `oth`
   moved 50 -> 119, so **`oth` is the volatile one and is not evidence of
   anything on its own**. **THAT IS A TWO-POINT SERIES AND IT IS NOT A BOUND**;
   it is printed so the third point has something to be read against. If a
   control's `lit` or `sky` median moves by an order more than that, nothing the
   five say is readable, because the only comparator spanning the break has
   itself moved.
3. **INSTRUMENT, NOT SUBJECT — any of the five returns `3of3`, or
   `valueRungs`' numerator lands above 35.** Nothing in this commit touches an
   albedo, a shader, a light or the sky. A camera turning round cannot make the
   render match the references, so a rung that starts holding was measured
   differently.
4. **SUBJECT, NOT INSTRUMENT — `district_fairview` lands in the low tens while
   `ref_4` reads 162.** Those two now photograph **the same wall**: fairview's
   block row `z[114.4,140.9]` shows its north faces at z 140.9 to `ref_4` at
   (-344.0, 1.7, 162.9) from 22m and to `district_fairview` at
   (-344.0, 14.0, 178.9) from 38m, both yaw 180, 16m apart on the same avenue.
   If the street camera sees the wall and the aerial one does not, the aerial
   vantage is looking over its own rooftops — a composition finding about that
   vantage, NOT a lie by the instrument. Named in advance so it cannot be read
   as one.

**And one margin that is 0.1m wide.** `BlockerReachM` is 8m and
`district_hook`'s near sunward rank stands at **8.1m**. The OLD hook eye had
its near rank at the same 8.1m (the grid is symmetric) and landed
`nearFrac 0.00` with no nudge — so this is the mirror, not a new risk. But if
`shotBlocker` names `district_hook`, the step-back loop moved the camera and
that row is not from the vantage placed here.

## 4. What this confirms and what it overturns

**CONFIRMS** — R2's confirming-evidence claim, checked against the landed
verdict rather than quoted: five district rows read `litnone@0` and the two
west-facing ones read `lit@37` and `lit@82` on `c5a75c9` (36 and 88 on
`b7d232b`). The mechanism is five for five plus two.

**OVERTURNS — "THE DEFAULT, UNCHANGED FOR FOUR OF SEVEN".** Five of seven take
the default approach; `downtown` is one of them. Anyone counting the blind
cameras from that sentence would have found four and left `downtown` behind.

**OVERTURNS — the slot-25 reasoning in the `downtown` vantage entry.** Slot 25
does not exist. Replaying the CURRENT `BuildSkyline` against today's
`StreetMap.BoundsOf`: the band is an offset rectangle at z 317-441 (N edge) and
x +482..+570 / -550..-656 (E and W edges), and the entire S edge — slots 17-26,
which is where the old circle put slot 25 at (-317.1,-24.5) — is skipped. No
skyline mass stands within a district or south of one at all. The old entry
reasons about a mass the repaired function no longer places. It is now
past-tense and the measurement replaces it.

**NEW, AND IT CHANGES HOW THE `sky>lit` RUNG SHOULD BE READ.** On `c5a75c9`, at
the same `r0.00w0.00`, in one run:

    seven district rows (14m eye, ~20 deg down):  sky 0.371 .. 0.425
    five ref rows       (1.7m eye,  5 deg down):  sky 0.596 .. 0.698

**Disjoint, with a gap of 0.171 and no overlap.** The cleanest single pair
inside that is `ref_3` and `district_ironside` — same street, same yaw 270,
same run, same weather tag, two independent cameras either of which can move
while the other stands still — reading 0.596 against 0.376. **I am not claiming
pitch CAUSES it**: the two families also differ in eye height and therefore in
occlusion, and that confound is not separated by anything landed. What the
disjointness does establish is that **`sky`'s median is a function of the
camera family**, so `sky>lit` is asking a different question of the aerial rows
than of the street rows — and `valueRungs` pools both into one tally. That is a
question for the director, not a change I made.

**A THIRD POSSIBLE SITE OF THE SAME SYMPTOM, OUT OF MY SCOPE AND NOT TOUCHED.**
`day5_noon` is a dry `r0.00w0.00` noon reading `litnone@0` against
`gnd0.697@1068`. Its camera is not compass-aimed — it takes the player's
position and aims along the nearest carriageway — so it is NOT the same cause.
But the aim is `new Vector3(-toRoad.z, 0, toRoad.x)` (`SimDirector.cs` ~12753),
which is only ONE of the two perpendiculars: for a given eye and road the
handedness is fixed and the camera can never face the other way down the same
street. Same family of fault, different mechanism. Flagged for the resident.

**Two out-of-scope documents still describe the superseded vantage**, both
already banner-marked: `game-design/agent-reports/tour-camera-resite.md` lines
21 and 88 ("34m south", "eye 34m south at (-365.5, 14, 5.1), yaw 0") under a
`STATUS — LOG, 2026-08-24. NOT CURRENT` header. Its line 91 was already
corrected on 26 Aug for the sun sentence. Not edited here.

**The greps I ran and read every hit of:** `34m south|looking north|
north-looking` across `*.cs`/`*.md`/`*.py`; `sun.*due south|noon sun.*south|
azimuth.*south` (every surviving hit is a quoted-as-corrected one);
`LookRotation|transform.rotation =|Quaternion.Euler` across `SimDirector.cs`
— the two other camera-pose sites are a close-up facing a surface normal
(line 288) and the dusk camera, which reads `GameController.SunwardDir`
directly and is correct by construction (line 1845). **No third copy of the
compass fault in a camera pose.**

## 5. The footer

**There is no footer to paste.** `ledger/.verify-footer` does not exist on
disk, because `verify.py` deletes it on a red run and this run is red:

    $ ls -la ledger/.verify-footer
    ls: cannot access 'ledger/.verify-footer': No such file or directory

**The only red is `director_cadence`** — `DIRECTOR NOT SPAWNED: 318 changed
line(s) ... 0 director row(s) newer than the reference` — the batch-review gate
the resident clears, not a fault in this work. Every other clause of the same
run was green, including the ones this pass could have broken: **0 lint errors,
0 shape errors (191 files), Game layer compiles (185 files)** — which is the
clause that matters here, because it is the only local proof the Unity-API edit
type-checks — **0 filename-as-type errors, 0 namespace-as-value errors, verdict
format ok (selftest + newest run), 40 frame-drift checks (0 failed), 4104
CoreTests.** Those clauses are quoted from the run above and are NOT a footer;
the footer is the thing that does not exist, and that distinction is the whole
point of the file.

## 6. What this pass did NOT do

- **No bound and no gate.** One landing is not a series. Nothing here is in
  `gates.py` and no number is compared against a constant.
- **No new verdict key, and no `ValuePanel.cs` change.** The regime marker the
  machine reads already exists — `camZ`/`camYaw` in `frames.tsv`, which
  `frame-drift` already conditions on. A second one would be the
  one-idea-two-implementations shape.
- **Ironside and Gullwing were not re-aimed**, though the same reflection was
  available to them. They are the cross-break controls; that was the director's
  call and it stands.
- **`day5_noon`'s one-handed street aim was not changed.** Reported, not fixed.
