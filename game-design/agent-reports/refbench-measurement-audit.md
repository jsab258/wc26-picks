# ref-bench measurement audit — the exposure conclusion, and the surface it sits on

LOG — 25 Aug 2026. NOT CURRENT after the next landing.
Read-only sweep by measurement-auditor over `tools/ref-bench.py` (2089 lines,
not ~1178 as briefed), the five frames in `game-design/reference/`, and the 17
sim stills at HEAD `80a91049`. Every number below was produced in this session
by re-running the instrument; nothing is quoted from a previous report.

**Bottom line, and it corrects my own first draft.** The published direction —
our sunlit ground is bright relative to its own scene in a way no GTA reference
is — SURVIVES every correction I could apply. What does not survive is the
MAGNITUDE and the GATE built on it. The in-band district count moves 0 / 1 / 4 /
1 of 7 purely by redefining which pixels the band is, with no change to the
game. The decal unblock threshold is "5 of 7 in band". A threshold that the
band's definition can move by four districts is not yet a threshold.

13 findings. F1–F5 touch the exposure conclusion. F6 touches what will be read
back from the build about to be dispatched.

---

## F1 — CRITICAL. `groundOverFrame`'s numerator is ONE SURFACE on the reference side and a COMPOSITION AVERAGE on ours

**Where.** `tools/ref-bench.py:390` `GROUND_Y = (0.667, 0.88)`; consumed at
`:724` (`gvals`), divided at `:758`. Declared at `:476` as "mean over ground
band" and at `:103` as "the ground band's mean luma".

**What it claims.** That the band is the ground, on both sides, so the two
numbers are the same quantity and may be divided into a comparison.

**What it is.** A fixed fraction of frame height. That is the ground only for a
camera near eye height looking roughly level. **All seven `district_*` frames
are aerial / high-oblique cameras.** I drew the band and the mask onto the
frames and looked (rule 4): in `district_fairview` and `district_gullwing` the
band's left third is a ROOF; in `district_hook` and `district_strip` the left
and right thirds are building FACADES; in `district_ironside` the centre is a
blurred grey crane column. The five references are street-level third-person
cameras whose band is pavement, road and dirt.

**Measured, with no segmentation choice, two ways — and one of the two failed.**
Left / centre / right thirds of the band, same code both sides:

    image                             LEFT    CTR  RIGHT   band  spread
    REF gta5_1_liquor_store_side_sun 0.314  0.286  0.292  0.293   0.029
    REF gta5_2_dusk_vespucci         0.138  0.093  0.192  0.142   0.099
    REF gta5_3_overcast_morning      0.261  0.193  0.221  0.216   0.068
    REF gta5_4_suburban_bmx_noon     0.652  0.532  0.493  0.536   0.159
    REF gta5_5_ps3_sidewalk          0.555  0.513  0.567  0.543   0.054
    SIM district_copper              0.375  0.749  0.599  0.624   0.374
    SIM district_downtown            0.314  0.720  0.553  0.583   0.405
    SIM district_fairview            0.504  0.752  0.617  0.655   0.248
    SIM district_gullwing            0.575  0.673  0.425  0.554   0.249
    SIM district_hook                0.300  0.710  0.300  0.471   0.411
    SIM district_ironside            0.861  0.540  0.859  0.726   0.321
    SIM district_strip               0.225  0.718  0.277  0.452   0.493

    spread: references 0.029..0.159    districts 0.248..0.493   NO OVERLAP

The reference bands are horizontally uniform to 0.03–0.16 luma. Ours vary by
0.25–0.49. The highest reference is well below the lowest district.

*The second measure did not work and I am reporting it because omitting it
would be the fault this audit is about.* "Fraction of the band within ±0.10 of
its own median" gives references 0.27..0.83 and districts 0.20..0.72 — it
OVERLAPS and does not discriminate. `gta5_4` scores 0.27, below four of our
seven districts. Only the thirds measure separates the sets.

**The case where this produces a wrong answer.** The fix on the table is a
`GroundGrade` multiplier on the `WetSurfaces` family — road and ground
materials. It does not touch roofs or facades. On `district_fairview` and
`district_gullwing` a large fraction of the band is roof; on `district_hook`
and `district_strip` the outer two thirds are facade. So the road can be
darkened correctly and the band mean will move by much less than the road did.
The decision doc's stated loop is "adjust the constant once from evidence if
out of band". Run twice, that loop drives the road toward black chasing a
number that roofs and facades are holding up, and every step of it will look
like evidence.

**Where would our number land if computed the reference's way — do I know?**
**No, and I tried.** My first attempt segmented the band's dominant surface by
histogram mode. It FAILED its own accepting case: on the references, where the
band is one surface and the mode must equal the mean, it deviated by up to
0.272 and widened the reference band to 0.168..1.400. That estimate is
discarded.

What I can give is a **direction and a bracket**. On 6 of 7 districts the
centre third (the street corridor) is BRIGHTER than the band mean, by +0.10 to
+0.27 luma — `district_strip`'s road is 0.718 while its band reads 0.452. The
exception is `district_ironside`, where the centre is the crane. **So
restricting the numerator to road pushes our ratio UP, not down: the inversion
gets WORSE, not better.** This finding does not exonerate the ground.

**Cheapest decisive measurement.** The sim already knows which pixels are the
ground material. One extra render per district shot with the `WetSurfaces`
family flat-shaded white and everything else black is a free road mask, and
`groundMean` over that mask is the number the conclusion needs. Failing that,
hand-paint seven mask PNGs — about twenty minutes, and it settles F1, F4 and
F10 at once. Until one of those exists, no in-band COUNT on the district frames
should be used as a gate.

---

## F2 — CRITICAL. The denominator is the whole frame, and the references have a bright sky that our districts do not

**Where.** `:723` `whole, npx_whole = band(np, luma, mask, (0.0, 1.0))`, divided
at `:758`. Documented at `:103–120` as separating "the ground material is too
bright" from "the frame is overexposed" — "two hypotheses with opposite fixes".

**What it actually cannot separate.** A third hypothesis with a third fix: the
upper half of our frames is dark. Measured:

    upper-third mean luma   references 0.613 0.622 0.627 0.709 0.727
                            districts  0.330 0.341 0.354 0.369 0.386 0.387 0.437
    fraction of upper third above 0.75 luma
                            references 0.096 0.516 0.548 0.609 0.635
                            districts  0.034 0.044 0.059 0.072 0.088 0.107 0.172

Four of five references carry a blown bright sky over half their upper third.
No district exceeds 0.172. The reference denominators are inflated by sky the
districts do not have, so part of what reads as "our ground is too bright" is
"our sky is too dark or absent" — and those have opposite fixes.

**The case where this produces a wrong answer.** Take the sky band out of the
denominator on both sides and the comparison changes sign for over half the set:

    variant                                  references n=5   districts n=7   in band
    SHIPPED   band / whole frame             0.387..0.981     1.019..1.374    0 of 7
    numerator fix  centre-third / frame      0.254..0.928     0.905..1.696    1 of 7
    denominator fix  band / lower two-thirds 0.675..1.077     0.924..1.229    4 of 7
    BOTH fixed  centre-third / lower two-thirds 0.502..1.070  0.763..1.525    1 of 7

**Read this carefully, because it is the finding.** The denominator correction
ALONE would have overturned the conclusion — 4 of 7 districts land inside the
reference band, and two GTA references themselves read above 1.0 once the sky is
out. That was my draft conclusion after one probe and it is wrong, because the
numerator error (F1) points the other way and cancels most of it. **Direction
survives; magnitude and the in-band count do not.** The gate is an in-band
count.

**Cheapest decisive measurement.** Print `groundOverFrame` beside
`groundOverLower` (ground band / lower two thirds) on the same line, both sides,
every run. It is four lines of the existing `band()` helper and it makes the
sky's contribution visible instead of silently baked into the ratio.

---

## F3 — HIGH. The gate's threshold and the gate's named instrument are two different instruments

**Where.** `game-design/decision-ground-albedo.md:38` and `:63–64`: the decal
item "unblocks when a landed dry tour shows `groundOverFrame` in band
(0.41–0.97, recomputed per run) on at least 5 of 7 districts", and "the gate is
the reader's §6 instrument: `groundOverFrame` ... band 0.41–0.97 recomputed per
run from the references". `tools/ref-bench.py` recomputes that band every run
and prints **0.387..0.981**, not 0.41..0.97.

**Why they differ, settled rather than guessed.** ref-bench applies the HUD mask
(`:531 valid_mask`, `:395 HUD`) to both sides. The reader's report did not. I
recomputed both ways and the reader's published table reproduces EXACTLY with
the mask off:

    district      gMean(mask)  gMean(no mask)   gof(mask)  gof(no mask) | reader published
    ironside          0.726        0.750          1.218       1.228     | 0.750 / 1.23
    fairview          0.655        0.661          1.281       1.276     | 0.659 / 1.27
    copper            0.624        0.600          1.330       1.262     | 0.600 / 1.26
    gullwing          0.554        0.529          1.019       0.982     | 0.527 / 0.98
    downtown          0.583        0.528          1.374       1.278     | 0.526 / 1.28
    hook              0.471        0.430          1.084       1.020     | 0.428 / 1.02
    strip             0.452        0.418          1.052       0.979     | 0.417 / 0.98

    references, no mask: 0.661 0.410 0.537 0.912 0.971  ->  band 0.41..0.97  EXACT

So the reader was internally consistent — both sides unmasked — and the number
0.41–0.97 is the UNMASKED band. The doc then names the MASKED instrument to
enforce it. The mask moves our districts UP by +0.037..+0.096 (six of seven) and
moves the reference ceiling DOWN from 0.971 to 0.981... in the other direction
for two frames and up for three. The two effects do not cancel and they are not
the same gate.

**The case where this produces a wrong answer.** Today both readings agree that
0 of 7 districts are in band, so nothing is wrong yet. After `GroundGrade` 0.55
lands, the districts come down toward the band edge — which is exactly where a
±0.04..0.10 systematic offset decides a pass/fail. A run whose unmasked
districts read 0.96 (5 of 7 in the reader's band → decals UNBLOCKED) reads
~1.00–1.03 through ref-bench (0 of 7 → decals stay BLOCKED). The disagreement
is largest at the decision point, which is the worst place for it.

**Cheapest decisive measurement.** Already run, above. The decision must pick
one instrument and quote ITS band. If it is ref-bench, the number in the doc is
0.387..0.981 and it must be re-read from the REFBAND line each run rather than
written down — the doc currently writes a constant beside the word
"recomputed", which is the shape that decays.

---

## F4 — HIGH. The HUD mask deletes 20.1% of our ground band, and on our side it is street and facade, not HUD

**Where.** `:395` `HUD = [(0.00, 0.72, 0.26, 1.00), (0.80, 0.00, 1.00, 0.08)]`,
applied to both sides at `:531`. Defended at `:324–327`: masking one side only
"would make the ground band a trapezoid here and a rectangle there ... Identical
geometry costs a corner nobody needs and removes the confound."

**What it actually is.** Measured: ground band 195,840 px unmasked, 156,384 px
masked — **20.1% removed**. On the reference side that corner holds a minimap
and removing it is correct. On our side it holds picture: in `district_copper`,
`district_downtown`, `district_strip` and `district_hook` it is a dark building
facade; in `district_fairview` and `district_gullwing` it is a roof.

The comment is right that identical geometry removes a GEOMETRIC confound. It
does not say that it introduces a CONTENT one, and the content one is
directional: masking RAISES `groundMean` on six of seven districts (copper
0.600→0.624, downtown 0.528→0.583, hook 0.430→0.471, strip 0.418→0.452,
gullwing 0.529→0.554) because the deleted corner is darker than the rest of the
band. "The corner nobody needs" is the corner that was holding the number down.

**Cheapest decisive measurement.** Same road mask as F1. Meanwhile, print
`groundMean` both ways on the image line — one extra `band()` call with
`mask=ones` — so the mask's contribution is a visible number rather than an
argument in a docstring.

---

## F5 — HIGH. "1.23–1.38 on our districts" is a range over a chosen subset, and the omitted districts are the ones nearest the band

**Where.** `game-design/agent-reports/dry-tour-stills-read.md:107–108` and
`ground-grade-and-tour-blocker.md:70–71, :230`.

**What it claims.** The range of `groundOverFrame` across our districts.

**What it is.** A list of six frames — copper, downtown, fairview, ironside,
day2_noon, day5_noon — of which two are not districts at all. The three
districts omitted are `gullwing`, `hook` and `strip`, and they are the three
closest to the reference ceiling. Today's full district range from the shipping
instrument is **1.019..1.374**, and the report's own table (line 59–66) prints
gullwing 0.98, hook 1.02, strip 0.98 four lines above the "1.23-1.38" summary,
with its own caveat that the remaining four "sit at or just past the top of the
reference band". The caveat did not survive being quoted forward; the summary
did.

**The case where this produces a wrong answer.** `1.23–1.38` reads as "every
district is 25–40% inverted" and sizes the correction accordingly — the doc
projects `1.23..1.38 sunlit -> 0.78..0.98` from a grade of 0.55. Applied to
`district_gullwing` at 1.019, a 0.55 grade lands it near 0.56 — below the
reference FLOOR of 0.387..0.981 at the bottom end. The constant is being sized
off the worst four of seven and applied to all seven.

**Cheapest decisive measurement.** `python3 tools/ref-bench.py --stable` prints
exactly the seven pose-stable district columns and nothing else. Quote its
range, not a hand-assembled list.

---

## F6 — MEDIUM, and it decides what the imminent build can tell you. `groundPatch` cannot show the ground fix working

**Where.** `:579–625`, documented at `:594–598` and reprinted on every report at
`:1070–1072`: "a MULTIPLICATIVE exposure change leaves it exactly unchanged".

**Verified rather than taken on the comment's word.** I scaled each frame by k
and re-measured:

    image                  k=1.0   k=0.7   k=0.5  k=0.35  k=0.25   +0.10 additive
    district_ironside      0.029   0.029   0.029   0.029   0.030   0.019
    district_fairview      0.105   0.105   0.105   0.105   0.106   0.094
    district_copper        0.132   0.133   0.133   0.134   0.134   0.114
    district_hook          0.273   0.275   0.275   0.280   0.280   0.193
    review_day1_night      0.089   0.087   0.067   0.059   0.044   0.035

**The claim is TRUE on every district, at every darkening down to k=0.25.** So
the brief's inference holds: `groundPatch` is structurally incapable of showing
that a multiplicative ground darkening worked.

I checked the one route by which it could have moved anyway — a darkening
recovers detail out of clipped highlights — and it is closed. Ground-band pixels
at ≥254: **0.000–0.001 on all seven districts** and 0.000 on both bright
references. There is nothing clipped to recover. `groundPatch` will not move.

**The case where this produces a wrong answer.** The decision doc's read
instruction is "`groundOverFrame` series first; `groundPatch` [second]", and the
decal work is to be SIZED from the `groundPatch` re-read on in-band frames. If
`GroundGrade` is a pure multiplier, the re-read returns the same numbers it
returns today, and that will read as "the darkening did not restore surface
detail" when it means "this statistic cannot see multiplicative change". The
honest expectation to write down BEFORE the build lands is: `groundPatch`
unchanged to three decimals on every district. If it moves, the grade is not
purely multiplicative and something else changed too.

**Cheapest decisive measurement.** Predict it now, in writing: the seven
district `groundPatch` values are 0.029 / 0.105 / 0.132 / 0.172 / 0.256 / 0.273
/ 0.152. Read them off the landing and see. That costs nothing and turns the
next verdict into a test of the instrument as well as of the change.

---

## F7 — MEDIUM. The reference band is a min..max over n=5, printed on every row with no n

**Where.** `:1081–1082` `ranges = {k: (min(...), max(...))}` over `refs`;
printed as the `ref lo..hi` column on all 17 rows and as `refGap image=REFBAND`.

**What it is.** The extreme order statistics of a five-point sample — the single
most sample-size-sensitive summary available. It can only widen with more
frames, so every "outside the band" flag is biased toward firing, and the count
`148 of 289 readings outside` inherits that bias. The machine tail does carry
`n=5`; the human table's per-row `ref lo..hi` column does not, and that is the
column that gets quoted.

The margin this matters for is small: reference ceiling 0.981 against
`district_gullwing` 1.019 is a gap of 0.038. A sixth reference frame with a
darker sky or a paler pavement could close it on its own.

**Cheapest decisive measurement.** Say `n=5` in the column header. Then add
reference frames — the band is the target and it is built from five samples;
that is the cheapest real improvement available to this tool.

---

## F8 — MEDIUM. The exposure-independence claim covers tonemaps; the selftest only tests a linear halving

**Where.** Claim at `:106–110`: "A GLOBAL brightness change — tonemap, exposure,
a grade applied to everything — divides out of it exactly, which is checked in
the selftest by scaling a frame and requiring the number not to move." Test at
`:2000–2009`, which measures `split // 2` on a synthetic two-tone image of
values 120 and 60.

**What the test proves.** Invariance under exact linear halving with no clipping
and no quantisation loss, on a two-tone synthetic. That case cannot fail.

**What the claim covers and the test never runs.** A tonemap is non-linear by
construction, and a non-linear monotone map does not divide out of a ratio of
means. Measured on the real frames:

    image                    raw   reinhard  gamma0.8  gamma1.25
    district_copper         1.330    1.292     1.277      1.390
    district_strip          1.052    1.035     1.038      1.069
    district_gullwing       1.019    1.018     1.016      1.022
    gta5_4_suburban_bmx     0.929    0.950     0.943      0.910
    gta5_5_ps3_sidewalk     0.981    0.996     0.989      0.970

The number moves — up to 0.113 of span on `district_copper`. Clipping breaks it
in the other direction too: scaling `gta5_4` up by k=1.3 and 1.6 moves it 0.929
→ 0.954 → 0.968, because clipped pixels do not scale.

**Honest magnitude.** For the three districts nearest the line the tonemap span
is only 0.006–0.031, so this does NOT on its own flip the inversion. The finding
is that the docstring's word "exactly" is false and the selftest's accepting
case is the one that cannot fail — not that the conclusion collapses.

**Cheapest decisive measurement.** Add one selftest case that applies a gamma
to the same synthetic and asserts the bound the tool actually wants (e.g. moves
by less than 0.05), or narrow the docstring from "tonemap" to "linear gain
without clipping", which is what is proven.

---

## F9 — MEDIUM. No ref-bench number has ever landed in a verdict. There is no series for any of the 17

**Where.** `game-design/sim-shots/verdict.txt` and `runs/*.txt`.

    grep -l for groundOverFrame, groundPatch, refGap, edgeGround,
    grainSigma, vertRuns, shadowRatio  ->  0 hits in verdict.txt,
                                           0 hits across 347 runs/*.txt
    python3 tools/gates.py --series groundOverFrame
      -> "no landed run carries that name. 321 runs read."

**What follows.** The brief's axis 5 cannot be run at all: there is no landed
value of any ref-bench number to check for constancy or order-of-magnitude
swings. `gates.py --series` and `--constant` are blind to this entire
instrument. Every ref-bench reading in every report so far is a single
invocation against whatever JPEGs were in the working tree at that moment.

The tool's own stated purpose (`:20–22`) is to say "which direction a phase
moved us and by how much". It cannot currently do that, because neither the
numbers nor the frames are kept per run — `game-design/sim-shots/*.jpg` is
overwritten every build (recoverable from git history, but nothing computes
across it).

**Cheapest decisive measurement.** The decision doc already asks for
"`groundOverFrame` per shot on the shot line". Landing that one key is what
turns the next reading into the first point of a series instead of another
isolated number. Note the same-line rule: it is a per-shot value and belongs on
the shot line, never beside a run-total.

---

## F10 — MEDIUM. The low-content CEILING is defeated by the band heterogeneity of F1, and its live accepting fixture is accepted for the wrong reason

**Where.** `:463` `LOW_CONTENT_CEIL_KEYS = ("groundMean",)`, applied at `:893`
via `above_ceiling` (`:854`). Justified at `:209–218`: `district_hook`
(groundP90 0.868 / groundMean 0.471) and `district_strip` (0.872 / 0.452) "print
P90s above the references' ceiling with means sitting mid-band, because they are
genuine street frames with bright highlights, not blown ones". `district_hook`
is named at `:217` as "the selftest's live accepting fixture for exactly this".

**What the measurement says.** Hook and strip have mid-band MEANS because their
outer two thirds are dark facades, not because their street is unblown. Their
centre thirds read **0.710 and 0.718** — the same as `district_copper` 0.749 and
`district_downtown` 0.720, both of which the ceiling DOES flag
(`groundMean:0.624>0.543`, `0.583>0.543`).

So the ceiling passes hook and strip for a reason the docstring states as fact
and the pixels contradict. Both are also the only two districts marked
`lowContent=none`, hence the only two districts readable on `shadowRatio` — so
the two frames carrying the shadow finding are the two whose ground band is most
contaminated by facade.

**The case where this produces a wrong answer.** The 24 Aug ruling explicitly
requires hook's and strip's below-band `shadowRatio` (0.149, 0.140) to "stay
visible as the residual the ambient-fill rung owns". That residual is being read
off a band that is two-thirds building. An ambient-fill change sized against it
is sized against facade contrast, not ground contrast.

**Cheapest decisive measurement.** The road mask again. A one-line interim
check that costs nothing: print the band's left/centre/right means beside
`groundMean` on the image line. Uniform on the references, 0.25–0.49 apart on
ours — the number announces its own contamination.

---

## F11 — LOW. Every dimension declares what statistic it is, and no reader ever sees it

**Where.** `:471–490` `DIMS` carries a fourth field for all 17 rows ("mean over
frame", "median over 64px windows", "count, upper two thirds", ...). Every
unpack site discards it: `:495`, `:1082`, `:1114` (`_stat`), `:1130` (`_st`),
`:1200`, `:1202`, `:1209`, `:1391`, `:1591`. Grep confirms it is never
formatted into any output line.

**Why it matters here.** The instruments rule is "say what the number is a
statistic OF — in the name or the comment beside the emit". It is said in the
source and not in the emit, and the emit is what gets pasted into reports. A
reader of the table or the `refGap` tail sees `groundPatch 0.132` with no
indication it is a median over 330 windows, or `vertRuns 33` with no indication
it is a count and not a peak.

**Clean on the axis the brief worried about, with its denominator:** I checked
all 17 dimensions for a cross-district aggregate and there is **none** — no
median-across-districts, no mean-of-medians, anywhere. The table is per-frame
columns; the only aggregates are `outside=148 outsideOf=289` (a count with its
denominator) and the min..max reference band of F7. The "worst that never stopped
being a median" fault is not present in this tool.

**Cheapest decisive measurement.** Print the fourth field. It is already there.

---

## F12 — LOW. `groundPatch`'s PATCH_FLOOR breaks its documented invariance on dark frames

**Where.** `:405` `PATCH_FLOOR = 8.0`, applied at `:622`
`float(win.std()) / max(float(win.mean()), PATCH_FLOOR)`.

Once a window's mean falls below 8/255, the divisor stops being the window's own
mean and the ratio becomes linear in exposure. Measured (F6 table, last row):
`review_day1_night` goes 0.089 → 0.044 as k goes 1.0 → 0.25, with floored
windows going **0 / 330 → 180 / 330 → 240 / 330**.

**The case where this produces a wrong answer.** Today no district has a single
floored window at k=1 (0 of 330, all seven). After a 0.55 ground grade the night
and wet frames move toward the floor, and their `groundPatch` will fall for
purely arithmetic reasons. That will read as "the darkening destroyed surface
detail at night". It has not; the divisor changed.

**Cheapest decisive measurement.** `_nPatch` is already printed per image as
`patchWindows=330`. Print the count of FLOORED windows beside it. Zero today on
every district, so it ships its own denominator and the day it stops being zero
is visible.

---

## F13 — LOW. Multiplicative invariance of `groundOverFrame` breaks upward, via clipping

`:758`. Measured in F8: `gta5_4` reads 0.929 at k=1.0 and 0.968 at k=1.6. The
docstring's "scale every pixel by k and it does not move" holds downward
(k=0.7, 0.5 leave it within 0.001) and fails upward as pixels clip at 255. Low
priority because nothing in the current argument brightens a frame.

---

## What I examined and found CLEAN, with counts, so a clean result is not a check that never ran

- **Aspect ratio and resolution, the brief's first worry — disposed of.** All
  five references are 16:9 (1.778, 1.778, 1.778, 1.778, 1.779) and all are
  resampled to 1280x720 at `:526–527`. The band `(0.667, 0.88)` is therefore the
  same geometric region on both sides, and `pxWhole/pxGround/pxMid` print
  identically (831960 / 156384 / 307516) for all 22 images. The band's problem
  is CONTENT (F1), not geometry.
- **Encoding and resampling noise — not a confound.** 8 images × 5 pipelines
  (LANCZOS / BICUBIC / BILINEAR / JPEG q90 / JPEG q75) = 40 recomputations of
  `groundOverFrame`. **Maximum deviation 0.001.** The 0.981-vs-1.019 margin is
  not an artefact of format, filter or compression. The `.webp` / `.png` / `.jpg`
  mix in the brief is not a finding.
- **Same-instant discipline — clean.** `measure()` (`:691`) takes one decode,
  one mask and returns every dimension together; `ratio_band_reading` (`:928`)
  takes `inBand`, `readable` and `unreadable` from one pass over one list. There
  is no path by which two ref-bench numbers on one line come from two moments.
  17 dimensions checked. `groundOverFrame`'s numerator and denominator are
  genuinely the same instant — the F1/F2 faults are about which PIXELS, not
  which moment.
- **Denominators on the low-content filter — clean, and better than most of this
  repo.** The ratioband line prints `inBand=1 readable=12 unreadableRatio=5
  stills=17` with the unreadable frames NAMED, `lowContent=` prints the word
  `none` rather than blank, `capped()` (`:965`) announces truncation as
  `(+Nmore-not-shown)`, and `:1158–1161` replaces the count with the words
  "NOTHING MEASURED — 0 of 0 readable stills" when nothing is readable. That
  branch IS exercised by the selftest at `:1858`. "Nothing was readable" and
  "everything read fine" are distinguishable in the output. Checked, and it
  passes.
- **The `~` annotation is a mark, not an exclusion** (`:1123`) and the `!`
  survives beside it, which is what the 24 Aug ruling required.
- **Clipping in the ground band** — 7 districts + 2 bright references measured,
  maximum fraction at ≥254 is 0.001.
- **Selftest** — 101 passed, 0 failed, re-run this session. As the brief says,
  that is evidence the tool computes what it computes, and F1, F2 and F8 are all
  invisible to it.

---

## The one structural asymmetry worth naming separately

`RATIO_DIMS` (`:438–443`) marks `groundOverFrame` unreadable on the FLOOR side
only. Measured consequence: the five frames it drops are day1_night 0.831,
day2_close 0.593, day2_night 0.679, day2_wet 0.816, day5_night 1.080 — and
**four of those five are INSIDE the reference band 0.387..0.981**, while all
seven ceiling-flagged bright frames are RETAINED as readable. So the readable
population is systematically the bright half, on the exact axis the metric
measures.

The docstring argues this at length (`:220–229`) and the argument is coherent —
a lamp over a black frame is not an inverted street. I am not calling it wrong.
I am naming it because "in band 1 of 12 readable" is the sentence the decision
gate consumes, and the filter that produced the 12 removes in-band frames and
keeps out-of-band ones by construction. Anyone quoting that count should quote
this sentence with it.

---

## Ranked, for the dispatch decision

**Would change the exposure conclusion's magnitude or its gate:** F1, F2, F3,
F5. None of them reverses the DIRECTION — the inversion survives the
both-corrected variant at 1 of 7 in band.

**Would change what the imminent build can tell you:** F6 (predict `groundPatch`
unchanged), F9 (nothing lands, so there is still no series), F12 (night frames
will fall for arithmetic reasons).

**The single cheapest thing that settles the most:** a ground-material render
mask for the seven district shots. It settles F1, F4 and F10, and it converts
F2's bracket from four variants into one number.
