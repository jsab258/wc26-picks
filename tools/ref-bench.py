#!/usr/bin/env python3
"""THE VISUAL BAR AS NUMBERS — one instrument run on GTA V and on us.

    python3 tools/ref-bench.py              # the side-by-side table
    python3 tools/ref-bench.py --stable     # only the pose-stable sim stills
    python3 tools/ref-bench.py --series     # the distributions the cuts came from
    python3 tools/ref-bench.py --selftest   # check the instrument

WHY. On 21 Aug the bar became GTA V on PS3 (Jafar, twice, over my hedging) and
for three days the target existed only as prose about itself — `visual-bar-spec.md`
§2 decomposes five frames in sentences. Sentences cannot say whether a phase
moved anything. `game-design/reference/README.md` names the missing half in one
line: "one instrument on both sides, or the comparison is two instruments
arguing". This is that instrument.

IT IS A STEERING PROXY AND NOT A QUALITY SCORE, and that is the most important
sentence in this file. Two frames can share every number here and share no
quality at all: nothing below knows what a chimney pot is, edge density cannot
tell a tar seam from film grain (it did not, see THE FIRST FINDING), and
saturation cannot tell a graded palette from a flat one. What this CAN do is say
which direction a phase moved us and by how much, which V1..V6 have no evidence
for today. **The final judge is a person with the frames side by side** — that
is M17.10's done-test. This decides which build is worth Jafar's minute; it does
not replace the minute.

--------------------------------------------------------------------------
THE FIRST FINDING, and it changed the tool before the tool shipped.

The brief specified edge density as the numeric proxy for "five asphalt tones
and tar snakes". Run as specified, the sim stills came back DENSER than the
references — 0.37..0.43 of the ground band against GTA's 0.05..0.30 — which
would read as us already past the bar on the one dimension §2 calls the killer
argument.

`district_downtown.jpg` is the frame that killed it. It is an almost entirely
BLACK frame — the camera is somewhere unlit, `meanLuma=0.065`, `brightPct=0.00`
in frames.tsv — and it scored `edgeGround=0.416`, ABOVE all five references
(whose top is 0.301). There is nothing in it. What the metric counted is FILM
GRAIN: a per-pixel noise field is the maximal response of a 3x3 Laplacian, and
FIND_EDGES is a 3x3 Laplacian.

Measured rather than supposed. `grainSigma` below is the Immerkaer noise
estimator — a 3x3 kernel built to cancel first and second-order structure — over
the ground band, in 0..255 levels:

    references   0.23 · 0.85 · 0.89 · 1.71 · 2.05
    our stills   0.32 · 1.81 · 2.13 · 2.70 · 5.15 · 5.29 · 5.47 · 5.51 · 5.59
                 · 6.01 · 6.03 · 6.29 · 6.98 · 7.43 · 8.76 · 11.21 · 13.95

Our night frames carry three to seven times the noise of the noisiest GTA frame,
and over the seventeen sim stills `edgeGround` rises with `grainSigma` at
Spearman rho=0.88. (The same correlation over the five references is 0.50 on
n=5, which is too few to carry an argument — the black frame is the argument.)
A 3x3 median pre-pass does not rescue it: it drops the black frame only from
0.416 to 0.296, while the references fall to 0.042..0.205, so the empty frame is
still denser than every one of them.

No absolute cut can separate the two either, and the arithmetic says why: i.i.d.
noise of sigma produces a FIND_EDGES response of about 8.5*sigma, so clearing
grain at sigma=6 needs a cut near 150, where the references sit at under 1% and
a doubling of our detail would be invisible.

So `edgeGround` SHIPS, because fine-scale density is a real thing to know, but
it ships beside `grainSigma` and it may not be read without it. And the actual
surface-history proxy is `groundPatch`, which is grain-immune by construction —
16px block means, so a per-pixel noise field averages away 16-fold before the
statistic sees it. On the black frame it reads 0.063, BELOW all five references
(whose floor is 0.205), which is what the picture says. One frame, two metrics,
opposite verdicts, and the picture settles which one is the instrument.

--------------------------------------------------------------------------
WHAT IT MEASURES, and what each number is a statistic OF.

 1. LUMA — mean and p10/p50/p90, whole frame and ground band. The whole-frame
    row is exposure; the ground-band row is what V1 moves. Both, because a
    median cannot see a tail and a mean cannot see either (rule 2).
 2. SATURATION — mean HSV S over the frame, and the FRACTION above 0.5. The
    mean alone is the trap the albedo policy sets: the noir tint strips source
    saturation, so a frame can carry three vivid signs and still read grey on
    average. "Is anything saturated" is never a median question.
 3. EDGE DENSITY, ground band and mid band, separately — the fine-scale
    fraction over the FIND_EDGES cut. Read it with `grainSigma`. The two bands
    are apart because one flat road and one busy wall average to a healthy
    street that does not exist.
 4. GRAIN SIGMA — Immerkaer, ground band. A property of our post chain, not of
    the world, and the largest single confound in this table.
 5. GROUND PATCH — the surface-history proxy. Median over sliding 64px windows
    of (spread of the 16px block means within the window) / (that window's own
    mean). Local, so a frame that is half black wall and half lit road is not
    scored for its composition; relative, so a night frame and a noon frame are
    comparable; coarse, so grain cannot reach it. This is "no surface is one
    flat tone edge to edge" as a number, and it is the row to steer V2 by.

    ITS READING RULE, WHICH IS NOT OPTIONAL: it is std/mean, so a
    MULTIPLICATIVE exposure change cannot move it and an ADDITIVE lift LOWERS
    it. A blown road and a featureless one print the same low number and this
    statistic cannot tell them apart. **A low GROUND PATCH means BLOWN OR FLAT
    until `groundOverFrame` says which** — in band, the surface is genuinely
    short of detail; above band, the number is measuring albedo rather than
    surface. Sizing decal work off it while the ground is lifted sizes it
    against a number inflated three-to-tenfold.

 5b. GROUND OVER FRAME — the ground band's mean luma over the WHOLE frame's
    mean luma, one decode, so both moments are the same instant by
    construction. EXPOSURE-INDEPENDENT: scale every pixel by k and it does not
    move, which is what makes it the row that separates "the ground material is
    too bright" from "the frame is overexposed" — two hypotheses with opposite
    fixes. A GLOBAL brightness change — tonemap, exposure, a grade applied to
    everything — divides out of it exactly, which is checked in the selftest by
    scaling a frame and requiring the number not to move. What it still SEES is
    the ground moving relative to its own scene, which is the physical claim,
    and that is why it is the row a rainy run cannot quietly satisfy: measured
    this run, our night/wet/dusk frames read 0.59..1.08 and every one of our
    daylight frames reads 1.02..1.40, wet ones included. Every GTA reference reads BELOW 1.0
    (0.387..0.981 measured through this code) because tarmac is the darkest
    large surface in a daylight scene; our sunlit dry frames read 1.02..1.40,
    physically inverted. Added 25 Aug 2026 on artifact-reader's nomination
    after the first dry tour; the reader's own recomputation put the reference
    band at 0.41..0.97, and the band that SHIPS is this tool's, recomputed
    from the references every run and printed on the REFBAND line.
 6. VERTICAL RUNS — connected near-vertical edge components taller than 8% of
    the frame in the upper two thirds. Poles and WIRES, rank 2 of the §2
    decomposition, and what §3 says every avenue in this game lacks by design.
    A COUNT, not a peak: it answers "how many uprights", never "how tall".
 7. SHADOW CONTRAST — ground-band p10/p90, off the pixels rather than off our
    tonemap constants. A PROXY: a dark shop recess and a cast shadow are the
    same pixels to it.

    THE TARGET IS THIS TOOL'S OWN MEASURED BAND, NOT THE PROSE FIGURE. The
    line here used to cite `visual-bar-spec.md` §7 item 1 — "GTA noons read a
    shadowed:lit ratio near 0.45..0.55, and the eye segments at about 2:1" —
    as though it were the bound for this row. It is not, and quoting it as one
    has already sent a reader looking for a lighting fault that the numbers do
    not support.

    TWO REASONS, AND THE SECOND IS THE REAL ONE. First, that figure predates
    this instrument: it was written from frames read by eye, not from this
    statistic on this crop at this resampling. Second and more important, IT
    IS NOT THE SAME QUANTITY. The spec's number is a ratio between two
    SURFACES — one lit patch against one shadowed patch, which is what our
    tonemap constants are tuned against in `LightModel`. This row is a ratio
    between two PERCENTILES of one band, p10 over p90, which sweeps in every
    dark recess, doorway and unlit wall the ground band contains. They cannot
    be expected to agree and neither is wrong.

    The five references measured through the code below read **0.157..0.388**.
    That is where the `ref lo..hi` column comes from and it is the only thing
    any sim row is scored against here — read it off the table, which reprints
    it every run rather than trusting this paragraph to stay true.

--------------------------------------------------------------------------
THE LOW-CONTENT ANNOTATION — WHY A NEARLY EMPTY FRAME SCORES WELL, AND WHAT
THIS TOOL DOES ABOUT IT.

Ruled by the director on 24 Aug (decision 1 part 3 in
`game-design/decisions-2026-08-24-shadow-gap-and-template-sync.md`):
ANNOTATION, NEVER EXCLUSION. A dropped frame reports a smaller world as a
cleaner one, which is this file's own opening argument against itself.

A FRAME CAN BE A READING OF NOTHING FROM EITHER END, AND THE SECOND END WAS
MISSING FOR A DAY. `district_downtown` used to read shadowRatio 0.676, ABOVE
the references' 0.157..0.388, on a frame that was one unlit surface with a
sliver of skyline: p10 and p90 both scraping the same near-black floor, and a
ratio of two numbers converging on the noise floor tends to 1 as the band
empties. That is the FLOOR case and it is why the annotation was built. The
CEILING case is the same fault inverted and it is the commoner one today —
`district_ironside` is a bare white sheet under a crane, the emptiest ground
band in the set (`groundPatch` 0.029 against a reference floor of 0.205), and
until 25 Aug it sailed through unannotated because its groundP90 0.890 and
groundMean 0.726 are far ABOVE the floors. A ratio row cannot tell a blown flat
band from a black flat one, and both are readings of nothing.

THE BOUNDS ARE THE REFERENCES' OWN MIN AND MAX, NOT NUMBERS SOMEBODY PICKED
(rule 2 — the first version of a bound is a printer). The five reference
frames' own ground-band inputs, sorted, run 25 Aug 2026 on verdict 6137608:

    groundP90   0.233 · 0.403 · 0.456 · 0.763 · 0.831   floor 0.233  ceil 0.831
    groundMean  0.142 · 0.216 · 0.293 · 0.536 · 0.543   floor 0.142  ceil 0.543

A sim still whose input PRINTS below its floor has a ground band dimmer than
the dimmest thing the target ever shows; above its ceiling, brighter than the
brightest. Both bounds are recomputed from the references on every run and
printed on the REFBAND line and the `scope=ratioband` line; there is no
constant here to go stale, and a reference frame can never qualify — which is
the selftest's structural accepting case.

EITHER KEY ON THE FLOOR, THE MEAN ONLY ON THE CEILING, AND THE LADDER IS WHY.
One contributor toggled at a time, over the same seventeen sim stills in the
same run (`--series` reprints it; these are the 25 Aug numbers):

    groundP90 below floor     4   day1_night day2_close day2_night day2_wet
    groundMean below floor    5   those four + day5_night
    floor either              5
    floor both                4
    groundP90 above ceiling   9   all seven districts + day2_noon day5_noon
    groundMean above ceiling  7   those nine less district_hook, district_strip
    SHIPPED                  12   floor-either (5) + ceiling-mean (7)

TWO READINGS DECIDE THE TWO ASYMMETRIES AND THEY ARE THE SAME PROPERTY OF A
PERCENTILE POINTING OPPOSITE WAYS. On the floor, `review_day5_night` is the
witness the mean catches alone: groundP90 0.525 — one lamp — over a groundMean
of 0.132. A band that is black except for a lit fitting is not a readable
street and the P90 rule would pass it. (The witness used to be
`district_gullwing` at P90 0.360 / mean 0.115; this build's camera re-site
moved that frame to 0.840 / 0.554 and the argument had to be re-pinned to a
frame that still shows it — which is the same decay this section's rejecting
fixture was caught by.)

On the ceiling, the SAME sensitivity to one bright object is a false positive:
`district_hook` (groundP90 0.868, groundMean 0.471) and `district_strip`
(0.872 / 0.452) print P90s above the references' ceiling with means sitting
mid-band, because they are genuine street frames with bright highlights, not
blown ones. A symmetric P90 ceiling would annotate exactly the two frames whose
below-band shadowRatio (0.149 and 0.140) the 24 Aug ruling requires to stay
visible as the residual the ambient-fill rung owns. So the ceiling is carried
by the mean, which moves only when the WHOLE band is brighter than anything the
target shows. `district_hook` is the selftest's live accepting fixture for
exactly this.

WHICH ROWS EACH SIDE MAKES UNREADABLE IS PER ROW, NOT PER FRAME. `shadowRatio`
is degenerate at both ends (p10/p90 tends to 1 as a band flattens, black or
blown). `groundOverFrame` is degenerate only at the dark end — `review_day5_night`
reads 1.080 with a groundMean below the floor, which is a lamp over a black
frame and not an inverted street — while at the blown end it is not degenerate
at all: `district_ironside` reads 1.218 with its mean above the ceiling, and
that reading IS the finding. Marking it unreadable there would have suppressed
the row added to diagnose the fault the ceiling half exists to catch. The sides
are declared in RATIO_DIMS and printed as `unreadableOn=` on every ratioband
line.

THE REJECTING FIXTURE IS SYNTHETIC, AND THAT IS THE POINT. It used to be
`district_downtown`, pinned because it was near-black. The camera re-site in
build 6137608 turned it into a lit street (meanLuma 0.096 -> 0.412), the
fixture stopped having the property it was chosen for, and the selftest went
red 3 of 78 — so verify went red, on a commit whose only crime was fixing the
frame the instrument was complaining about. Doing the work the instrument
exists to prompt must never break the instrument. The rejecting case is now
three generated images that no improvement to the game can reach: a near-black
frame (floor side), a uniform pale sheet (ceiling side) and a mid-tone frame
that must NOT qualify. The accepting cases stay pinned to the live set, where
they belong.
--------------------------------------------------------------------------
THE CUTS, TAKEN FROM THE SERIES AND NOT THE OTHER WAY ROUND (rule 2 — a bound
chosen first and defended after is a rounding wearing a measurement's clothes).
`--series` reprints all of this on demand. Run 24 Aug 2026, 5 references and 17
sim stills.

EDGE_T = 16, on the FIND_EDGES magnitude. Ground-band fraction over each cut:

    cut      ref lo..hi      sim lo..hi     sim stills inside the ref band
     8     0.133..0.380    0.136..0.454              4 of 17
    12     0.082..0.330    0.096..0.438              4 of 17
    16     0.053..0.301    0.076..0.428              4 of 17
    24     0.026..0.251    0.049..0.411              4 of 17
    32     0.014..0.209    0.035..0.393              4 of 17
    48     0.006..0.141    0.019..0.359              4 of 17
    64     0.004..0.094    0.011..0.325              4 of 17

Every cut ranks the two sides identically — that constancy IS the reading, and
it says the cut is a lens rather than a bound. 16 is taken because it leaves the
references the widest usable band (0.053..0.301, room to move both ways); 8
pushes the busiest reference to 0.38 where growth compresses, and 64 collapses
the dusk reference to 0.004 where a doubling is invisible.

VERT_T = 40, on the Sobel-x magnitude. Component counts per cut:

    cut       16   24   32   40   48   56   72
    ref lo    17   26   24   22   19   17   10
    ref hi    38   47   46   49   42   31   18
    sim lo     1    0    0    0    0    0    0
    sim hi    44   43   44   40   34   30   21

Below 32 the detector FUSES: every sim night frame reads 1, because grain makes
the whole upper band a single connected component — "one pole" for a street of
buildings. Above 56 the references themselves collapse (frame 1 falls 34 to 17,
frame 4 falls 49 to 31) as real poles fragment under the 8% height floor. 40
sits on the plateau where all five references are at or near their maximum
count: the cut that resolves the most poles on the side of the argument that
has poles.

PATCH_BLOCK = 16 px, PATCH_WIN = 4 blocks (64px windows). The four shapes, over
the same twenty-two images:

    block/window      ref lo..hi     span    sim lo..hi    the black frame
      8 / 8 (64px)   0.238..0.452    x1.9   0.077..0.456       0.109
     16 / 4 (64px)   0.205..0.382    x1.9   0.052..0.392       0.063   <- taken
     16 / 8 (128px)  0.244..0.492    x2.0   0.065..0.551       0.065
     32 / 2 (64px)   0.116..0.250    x2.1   0.025..0.244       0.036

THE SPAN DOES NOT DECIDE IT — all four sit within x1.9..x2.1, so the reference
frames agree no better under one shape than another and any argument from
tightness would be a rounding. The last column decides it. `district_downtown`
contains nothing but grain, so whatever it scores is the shape's grain leak, and
it halves from 0.109 to 0.063 between 8px and 16px blocks — a 16px block averages
256 pixels, which drops our worst frame's sigma of 14 to under one level. 32px
blocks suppress more still and are rejected for the opposite reason: a tar seam
is a few pixels wide and a patch repair a few tens, so 32px averages away the
features being counted, and PATCH_WIN=2 leaves each window's spread computed
from four numbers. 16/8 is rejected because 128px windows start scoring
COMPOSITION again — it hands the top of the whole set to `review_day1_dusk`
(0.551), a frame whose ground band is half black wall.

An earlier version of this paragraph claimed the references agreed to +-10% at
16/4. They do not; that number came from a run with the HUD crop not yet applied,
where the minimap's flat grey dragged the overcast frame down from 0.382 to
0.223. It is written down because the tool's own output is what corrected it.

--------------------------------------------------------------------------
THE CROP, AND IT IS APPLIED TO BOTH SIDES ON PURPOSE.
The GTA frames carry HUD. Two rectangles, in fractions of the frame:

    minimap    x 0.00..0.26   y 0.72..1.00   bottom-left; widest is frame 5
                                             (x 0.056..0.24), tallest frame 5
                                             again (y 0.735..0.908)
    stars      x 0.80..1.00   y 0.00..0.08   top-right wanted level, frames 1&3

and the band definitions cut the bottom 12% outright, which is where the street
name caption (frame 2), the "PS3" label and the site watermark (frame 5) and the
health bars live. Both rectangles are dilated by MASK_PAD before use, because
FIND_EDGES draws a bright line along any mask boundary it can see; the 2px image
border goes for the same reason (PIL's 3x3 filters copy the outermost row and
column from the source rather than filtering them).

Our stills have no HUD, and the mask is applied to them ANYWAY. Masking one side
only would make the ground band a trapezoid here and a rectangle there, so a
difference in the numbers could be a difference in which pixels were sampled.
Identical geometry costs a corner nobody needs and removes the confound.
`pxWhole/pxGround/pxMid` are printed per image, so the denominator of every band
statistic is visible rather than assumed.

RESAMPLED TO ONE WORKING FRAME, 1280x720. The references are 640x360, 980x551,
1280x720 and 1920x1080; edge density per pixel means nothing across those.
1280x720 is the sim's native size and three of the five references', so it is
the least-resampling common frame. A 1920 reference downsampled loses fine
detail into the same pixel budget we have, which is the honest comparison —
M17.10 is judged by eye at one display size too.

--------------------------------------------------------------------------
POSE — THE ROW THIS TOOL WILL NOT LET YOU COMPARE ACROSS BUILDS.
Measured, not assumed, over six landed revisions of `game-design/sim-shots/frames.tsv`:

    district_hook   camX/camZ/camYaw = 0.0/-34.0/0 in all six          FIXED
    day1_noon       1.0/24.6/163 · 2.7/18.4/162 · -2.6/8.6/110
                    · 2.7/18.8/162 · 5.1/12.9/168 · 2.8/18.6/162       MOVES

So ONLY the seven `district_*` frames are pose-stable, and a `day1_noon` reading
against last week's `day1_noon` is two photographs, not a delta. The stable ones
carry `*` in the table and are all `--stable` keeps. Every sim still prints the
camera triple and the rain/wet this run put it at, read from frames.tsv, so the
claim above stays checkable instead of becoming a comment that decays — and
because `review_day2_wet` at rain=0.90 is the single grainiest frame in the set,
rain belongs beside any reading of its ground band.

THE MACHINE TAIL. `refGap` lines, one per image, every value space-free, the
whole reading on ONE line — a reader greping two keys off two lines gets two
moments as one, which cost this project an afternoon and five wrong answers.
`refGap image=REFBAND` carries the five references' range per key as `lo..hi`;
`refGap summary` carries every count with its denominator.

Each image line also carries `lowContent=` — the qualifying reading as a PAIR,
`groundMean:0.115<0.142`, value and the floor it failed against in one token,
never two keys whose relationship the reader has to remember — and
`ratioUnreadable=`, the ratio rows that pair marks. Both print the word `none`
when the frame is fine, so "not low-content" and "the tool forgot to look" are
different strings. `refGap scope=ratioband` is one line per ratio row carrying
the count the decision record asks for: in band X of Y READABLE, +Z unreadable,
named, out of the number of stills examined.

EXIT CODES. 0 report produced (or selftest passed). 1 selftest failed. 2 usage.
3 nothing to measure — a directory missing or holding no readable image, said
with the count of files examined so it cannot read as "clean". 4 the report
printed but an image could not be read, named with its error.
"""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REFDIR = ROOT / "game-design" / "reference"
SIMDIR = ROOT / "game-design" / "sim-shots"
FRAMES = SIMDIR / "frames.tsv"

WORK = (1280, 720)          # the common working frame; see THE CROP
IMG_EXTS = {".webp", ".png", ".jpg", ".jpeg"}
SIM_PREFIXES = ("review_", "district_")

# Bands, as fractions of frame height. GROUND is the bottom third minus the
# bottom 12% (HUD captions, health bars, watermarks); MID is the facade band;
# UPPER is where poles and wires are counted.
GROUND_Y = (0.667, 0.88)
MID_Y = (0.333, 0.667)
UPPER_Y = (0.000, 0.667)

# HUD rectangles, x0,y0,x1,y1 in frame fractions. Applied to BOTH sides.
HUD = [(0.00, 0.72, 0.26, 1.00),    # minimap, bottom-left
       (0.80, 0.00, 1.00, 0.08)]    # wanted stars, top-right
MASK_PAD = 2                        # px; FIND_EDGES lights up a mask boundary

EDGE_T = 16         # FIND_EDGES magnitude 0..255. Series in THE CUTS.
VERT_T = 40         # Sobel-x magnitude 0..255. Series in THE CUTS.
VERT_MIN = 0.08     # a component is a "pole" at this fraction of frame height
VERT_GAP = 2        # rows of occlusion one run may bridge
PATCH_BLOCK = 16    # px per block; grain dies 16-fold in a block mean
PATCH_WIN = 4       # blocks per window, so a 64px neighbourhood
PATCH_FLOOR = 8.0   # 0..255; keeps a near-black window from dividing by nothing

# The only sim stills whose camera is fixed across builds. Measured off six
# landed frames.tsv revisions, not assumed — the working is in POSE above.
STABLE_PREFIX = "district_"

COLS_PER_BLOCK = 4      # sim columns per table block; the cap announces itself
NAME_CAP = 8            # named stills per list before `(+N more not shown)`

# ---- the low-content annotation. See THE LOW-CONTENT ANNOTATION above.
#
# RATIO_DIMS: the rows whose value is a RATIO of two statistics of this frame,
# mapped to the inputs it divides AND to WHICH SIDE of the low-content
# qualifier makes it unreadable. A ratio can read healthy for the wrong reason
# when its inputs stop describing a surface, which no absolute row can do, so
# these are the rows the annotation covers. The mapping is here and not inlined
# so the count "2 of 17 dimensions are ratio-derived" prints beside the
# annotation — a reader must be able to tell "one row annotated" from "every
# ratio row annotated".
#
# `unreadableOn` IS NOT DECORATION AND THE TWO ROWS DIFFER, measured on this
# run's stills (the series is in THE LOW-CONTENT ANNOTATION):
#   shadowRatio     floor AND ceiling. p10/p90 tends to 1 from BOTH ends — a
#                   black band converges on the noise floor (downtown's old
#                   0.676) and a blown band converges on a flat sheet.
#   groundOverFrame floor ONLY. On a dark frame it is a reading of nothing
#                   (`day5_night` 1.080 at groundMean 0.132, below the
#                   references' floor: a lamp over a black frame, not an
#                   inverted street). On a BLOWN frame it is not degenerate at
#                   all — it is the finding (`district_ironside` 1.218 at
#                   groundMean 0.726, above the references' ceiling). Marking
#                   it unreadable there would suppress the one row that says
#                   which kind of nothing the frame is.
RATIO_DIMS = {
    "shadowRatio": {"inputs": ("groundP10", "groundP90"),
                    "unreadableOn": ("floor", "ceiling")},
    "groundOverFrame": {"inputs": ("groundMean", "lumaMean"),
                        "unreadableOn": ("floor",)},
}

# LOW_CONTENT_FLOOR_KEYS / LOW_CONTENT_CEIL_KEYS: the ground-band INPUT
# statistics whose bound qualifies a frame as low-content, and the sides are
# NOT symmetric — the asymmetry is measured, not tidy. See THE LOW-CONTENT
# ANNOTATION for the series and the ladder.
#
#   FLOOR, either key. A percentile can sit above its floor on a black frame
#   because of one lit sill (`review_day5_night`: groundP90 0.525, groundMean
#   0.132), so the mean alone would miss it and the P90 alone would too.
#   CEILING, the MEAN only, for the SAME property of a percentile pointing the
#   other way: one bright highlight lifts groundP90 past the references'
#   ceiling on frames whose band is not blown at all (`district_hook` 0.868
#   and `district_strip` 0.872, both with means of 0.45..0.47, mid-band). A
#   P90 ceiling would annotate exactly the two frames whose below-band
#   shadowRatio the 24 Aug ruling requires to stay visible as a finding.
#
# No number lives here on purpose: floor is min() and ceiling is max() over
# the five references, taken fresh every run.
LOW_CONTENT_FLOOR_KEYS = ("groundP90", "groundMean")
LOW_CONTENT_CEIL_KEYS = ("groundMean",)
# Display order for the qualifier's input columns: every key that carries any
# bound, once. Derived, so a key added above cannot be missed by a printer.
LOW_CONTENT_KEYS = tuple(dict.fromkeys(LOW_CONTENT_FLOOR_KEYS
                                       + LOW_CONTENT_CEIL_KEYS))

# Row order, and what each number is a statistic OF, named once so the table,
# the machine tail and the selftest cannot drift apart.
DIMS = [
    ("lumaMean",    "luma mean",           "%.3f", "mean over frame"),
    ("lumaP10",     "luma p10",            "%.3f", "10th pct over frame"),
    ("lumaP50",     "luma p50",            "%.3f", "median over frame"),
    ("lumaP90",     "luma p90",            "%.3f", "90th pct over frame"),
    ("groundMean",  "ground luma mean",    "%.3f", "mean over ground band"),
    ("groundP10",   "ground luma p10",     "%.3f", "10th pct, ground band"),
    ("groundP50",   "ground luma p50",     "%.3f", "median, ground band"),
    ("groundP90",   "ground luma p90",     "%.3f", "90th pct, ground band"),
    ("satMean",     "saturation mean",     "%.3f", "mean HSV S over frame"),
    ("satAbove50",  "saturation >0.5",     "%.3f", "fraction of frame"),
    ("groundPatch", "GROUND PATCH surface", "%.3f", "median over 64px windows"),
    ("groundOverFrame", "ground/frame mean", "%.3f",
     "groundMean/lumaMean, one decode"),
    ("edgeGround",  "edge density GROUND",  "%.3f", "fraction of ground band"),
    ("edgeMid",     "edge density MID",    "%.3f", "fraction of mid band"),
    ("grainSigma",  "grain sigma",         "%.2f", "Immerkaer, ground band"),
    ("vertRuns",    "vertical runs",       "%.0f", "count, upper two thirds"),
    ("shadowRatio", "shadow contrast",     "%.3f", "groundP10/groundP90"),
]

# One lookup from key to print format, derived from DIMS so the table, the
# machine tail, the low-content marks and the selftest cannot drift apart about
# how many decimals a reader is judging.
FMTS = {k: f for k, _l, f, _s in DIMS}


class Unreadable(Exception):
    """An image that would not open or decode. Carried, never swallowed — a
    benchmark that quietly drops a frame reports a smaller world as a cleaner
    one, and rule 3b's whole subject is a zero that examined nothing."""


# ---------------------------------------------------------------- measurement

def _np():
    import numpy
    return numpy


def load(path):
    """One image, decoded and resampled to the working frame.

    LOAD_TRUNCATED_IMAGES is pinned OFF. PIL's default is already off, but a
    library elsewhere in the process flipping it on would turn a half-written
    JPEG into grey pixels and a plausible row of numbers, which is the one
    failure this tool must not have."""
    from PIL import Image, ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = False
    try:
        img = Image.open(path)
        img = img.convert("RGB")
        img.load()
    except Exception as exc:            # noqa: BLE001 — reported, never hidden
        raise Unreadable("%s: %s" % (path.name, exc))
    if img.size != WORK:
        img = img.resize(WORK, Image.LANCZOS)
    return img


def valid_mask(np, h, w):
    """Pixels any statistic is allowed to see: everything but the HUD
    rectangles and the image border, both dilated by MASK_PAD."""
    m = np.ones((h, w), dtype=bool)
    m[:MASK_PAD, :] = m[-MASK_PAD:, :] = False
    m[:, :MASK_PAD] = m[:, -MASK_PAD:] = False
    for x0, y0, x1, y1 in HUD:
        a = max(0, int(y0 * h) - MASK_PAD)
        b = min(h, int(y1 * h) + MASK_PAD)
        c = max(0, int(x0 * w) - MASK_PAD)
        d = min(w, int(x1 * w) + MASK_PAD)
        m[a:b, c:d] = False
    return m


def band(np, arr, mask, span):
    """The values of `arr` inside a horizontal band AND inside the mask, with
    the count. The count is the denominator — an empty band must not be able to
    hand back a clean-looking zero."""
    h = arr.shape[0]
    a, b = int(span[0] * h), int(span[1] * h)
    vals = arr[a:b][mask[a:b]]
    return vals, int(vals.size)


def grain_sigma(np, luma255, mask):
    """Immerkaer's noise estimate over the ground band, in 0..255 levels.

    A PROPERTY OF OUR POST CHAIN, NOT OF THE WORLD — and the reason it is in
    this table at all is that without it `edgeGround` reads a black frame full
    of film grain as the second most detailed surface in the project.

    The 3x3 kernel [[1,-2,1],[-2,4,-2],[1,-2,1]] is the difference of two
    Laplacians, which cancels every first and second-order structure a smooth
    surface can have, so what survives is noise. sqrt(pi/2)/6 turns the mean
    absolute response into a standard deviation."""
    g = luma255
    k = np.abs(g[:-2, :-2] - 2 * g[:-2, 1:-1] + g[:-2, 2:]
               - 2 * g[1:-1, :-2] + 4 * g[1:-1, 1:-1] - 2 * g[1:-1, 2:]
               + g[2:, :-2] - 2 * g[2:, 1:-1] + g[2:, 2:])
    full = np.zeros_like(g)
    full[1:-1, 1:-1] = k
    vals, n = band(np, full, mask, GROUND_Y)
    if n == 0:
        return 0.0, 0
    return float(math.sqrt(math.pi / 2.0) * vals.mean() / 6.0), n


def ground_patch(np, luma255, mask):
    """LOCAL tonal spread of the ground band: "no surface is one flat tone edge
    to edge" as a number, and the one statistic here that grain cannot reach.

    A MEDIAN OVER WINDOWS, so it describes the typical patch of ground and not
    the frame's composition — a frame that is half black wall and half lit road
    would score enormously on any whole-band variance, and that is a fact about
    the camera, not about the surface. Windows slide one block at a time so the
    sample is a few hundred rather than a few dozen.

    Each window's spread is divided by that window's OWN mean, which is what
    makes a night frame and a noon frame comparable; PATCH_FLOOR stops a window
    with nothing in it dividing a small number by a smaller one.

    THE READING RULE, AND IT MAY NOT BE READ WITHOUT `groundOverFrame`. This is
    std/mean, so a MULTIPLICATIVE exposure change leaves it exactly unchanged
    (both halves scale by k) and an ADDITIVE lift LOWERS it (the mean rises,
    the spread does not). An ambient-lifted road and a genuinely featureless
    one therefore print the same low number, and this statistic cannot tell
    them apart — no version of it can. So a low `groundPatch` means BLOWN OR
    FLAT, and `groundOverFrame` is the row that says which: in band, the
    surface really is short of detail; above band, the ground is carrying an
    additive lift and this number is measuring the albedo, not the surface.
    Measured on this run: five of seven districts recover into or above the
    references' patch band once the lift is subtracted."""
    h, w = luma255.shape
    y0 = int(GROUND_Y[0] * h)
    y1 = int(GROUND_Y[1] * h)
    nr = (y1 - y0) // PATCH_BLOCK
    nc = w // PATCH_BLOCK
    if nr < PATCH_WIN or nc < PATCH_WIN:
        return 0.0, 0
    hh = nr * PATCH_BLOCK
    g = luma255[y0:y0 + hh, :nc * PATCH_BLOCK]
    m = mask[y0:y0 + hh, :nc * PATCH_BLOCK]
    blocks = g.reshape(nr, PATCH_BLOCK, nc, PATCH_BLOCK).mean(axis=(1, 3))
    good = m.reshape(nr, PATCH_BLOCK, nc, PATCH_BLOCK).all(axis=(1, 3))
    vals = []
    for r in range(nr - PATCH_WIN + 1):
        for c in range(nc - PATCH_WIN + 1):
            if not good[r:r + PATCH_WIN, c:c + PATCH_WIN].all():
                continue
            win = blocks[r:r + PATCH_WIN, c:c + PATCH_WIN]
            vals.append(float(win.std()) / max(float(win.mean()), PATCH_FLOOR))
    if not vals:
        return 0.0, 0
    return float(np.median(vals)), len(vals)


def vertical_runs(np, gx, mask, h, w):
    """Connected near-vertical edge components taller than VERT_MIN of the
    frame, in the upper two thirds. A poles-and-wires proxy.

    A COUNT, NOT A PEAK OR A MEDIAN. It answers "how many uprights are in this
    frame", which is what §2 rank 2 asks; it says nothing about how tall the
    tallest is, and it is not comparable between frames shot from different
    camera positions.

    Components rather than columns, because a pole is three to six pixels wide,
    so counting columns counts each pole five times, and a leaning pole (frame 5
    is full of them) drifts across columns as it rises. Runs are found per
    column with a VERT_GAP row tolerance for occlusion, then runs in adjacent
    columns whose row spans overlap are unioned.

    THE COUNT IS NOT MONOTONE IN VERT_T, and that is the detector working: a
    low cut FUSES neighbours into one component and a high cut fragments a real
    pole below the height floor, so the count peaks in between. That peak is
    where VERT_T was chosen — see THE CUTS."""
    top = int(UPPER_Y[1] * h)
    v = (gx[:top] > VERT_T) & mask[:top]
    v = v | np.roll(v, 1, axis=1) | np.roll(v, -1, axis=1)
    v[:, 0] = v[:, -1] = False
    minh = int(VERT_MIN * h)

    runs = []                       # [col, row0, row1]
    per_col = [[] for _ in range(w)]
    for x in np.flatnonzero(v.any(axis=0)):
        rows = np.flatnonzero(v[:, x])
        start = prev = rows[0]
        for r in rows[1:]:
            if r - prev > VERT_GAP + 1:
                per_col[x].append(len(runs))
                runs.append([x, start, prev])
                start = r
            prev = r
        per_col[x].append(len(runs))
        runs.append([x, start, prev])

    parent = list(range(len(runs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for x in range(w - 1):
        for i in per_col[x]:
            for j in per_col[x + 1]:
                if runs[i][1] <= runs[j][2] and runs[j][1] <= runs[i][2]:
                    a, b = find(i), find(j)
                    if a != b:
                        parent[a] = b

    spans = {}
    for i, (_c, r0, r1) in enumerate(runs):
        k = find(i)
        lo, hi = spans.get(k, (r0, r1))
        spans[k] = (min(lo, r0), max(hi, r1))
    return sum(1 for lo, hi in spans.values() if hi - lo + 1 >= minh), len(runs)


def measure(img, keep_arrays=True):
    """Every dimension for one image, with the pixel counts that are their
    denominators. Same-instant by construction: one decode, one mask, one set of
    numbers, all returned together — there is no way to read two of these from
    two different moments.

    `keep_arrays` holds on to the edge/gradient/mask planes, which `--series`
    needs to re-cut and the report does not. Four float planes per image is
    15MB, so the report over twenty-two images would otherwise carry a third of
    a gigabyte it never reads."""
    np = _np()
    from PIL import Image, ImageFilter
    rgb = np.asarray(img, dtype=np.float32)
    h, w = rgb.shape[0], rgb.shape[1]
    mask = valid_mask(np, h, w)

    # Rec.601, the same weights tools/sheet-read.py uses. One convention.
    luma255 = rgb[:, :, 0] * 0.299 + rgb[:, :, 1] * 0.587 + rgb[:, :, 2] * 0.114
    luma = luma255 / 255.0
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)

    grey = Image.fromarray(luma255.clip(0, 255).astype(np.uint8), "L")
    edge = np.asarray(grey.filter(ImageFilter.FIND_EDGES), dtype=np.float32)

    g = np.asarray(grey, dtype=np.float32)
    gx = np.zeros_like(g)
    gx[1:-1, 1:-1] = np.abs(
        (g[:-2, 2:] + 2 * g[1:-1, 2:] + g[2:, 2:])
        - (g[:-2, :-2] + 2 * g[1:-1, :-2] + g[2:, :-2])) / 4.0

    whole, npx_whole = band(np, luma, mask, (0.0, 1.0))
    gvals, npx_ground = band(np, luma, mask, GROUND_Y)
    svals, _ = band(np, sat, mask, (0.0, 1.0))
    eg, npx_eg = band(np, edge, mask, GROUND_Y)
    em, npx_em = band(np, edge, mask, MID_Y)
    if min(npx_whole, npx_ground, npx_eg, npx_em) == 0:
        raise Unreadable("%dx%d decoded but a band was empty after masking" % (w, h))

    p = np.percentile
    gp10, gp90 = float(p(gvals, 10)), float(p(gvals, 90))
    runs, raw_runs = vertical_runs(np, gx, mask, h, w)
    sigma, n_sigma = grain_sigma(np, luma255, mask)
    patch, n_patch = ground_patch(np, luma255, mask)
    # GROUND OVER FRAME — the ground band's mean luma over the WHOLE frame's
    # mean luma. A RATIO OF TWO MEANS OF ONE DECODE, so both moments are the
    # same instant by construction: there is no way to take the numerator from
    # one image and the denominator from another. It is exposure-independent —
    # scale every pixel by k and it does not move — which is what makes it the
    # row that separates "the ground material is too bright" from "the frame is
    # overexposed". Guarded at zero, because a flat black frame has no exposure
    # to be independent of.
    whole_mean = float(whole.mean())
    gmean = float(gvals.mean())
    out = {
        "lumaMean": whole_mean,
        "lumaP10": float(p(whole, 10)),
        "lumaP50": float(p(whole, 50)),
        "lumaP90": float(p(whole, 90)),
        "groundMean": gmean,
        "groundP10": gp10,
        "groundP50": float(p(gvals, 50)),
        "groundP90": gp90,
        "satMean": float(svals.mean()),
        "satAbove50": float((svals > 0.5).mean()),
        "groundPatch": patch,
        "groundOverFrame": (gmean / whole_mean) if whole_mean > 1e-6 else 0.0,
        "edgeGround": float((eg > EDGE_T).mean()),
        "edgeMid": float((em > EDGE_T).mean()),
        "grainSigma": sigma,
        "vertRuns": float(runs),
        "shadowRatio": (gp10 / gp90) if gp90 > 1e-6 else 0.0,
        "_pxWhole": npx_whole,
        "_pxGround": npx_ground,
        "_pxMid": npx_em,
        "_pxGrain": n_sigma,
        "_nPatch": n_patch,
        "_rawRuns": raw_runs,
    }
    if keep_arrays:
        out.update({"_edge": edge, "_gx": gx, "_mask": mask, "_luma255": luma255})
    return out


# ------------------------------------------------------------------ inventory

def images_in(d, prefixes=None):
    """(paths, files_examined). files_examined is -1 when the directory is not
    there at all, so "missing" and "empty" cannot print the same sentence; it is
    the denominator that stops "no images here" reading like "this is fine"."""
    if not d.is_dir():
        return [], -1
    seen = 0
    out = []
    for p in sorted(d.iterdir()):
        if not p.is_file():
            continue
        seen += 1
        if p.suffix.lower() not in IMG_EXTS:
            continue
        if prefixes is not None and not any(p.name.startswith(x) for x in prefixes):
            continue
        out.append(p)
    return out, seen


def shot_rows():
    """camX/camZ/camYaw plus rain/wet per shot from frames.tsv, so the
    pose-stability claim in POSE stays checkable and the grainiest frame in the
    set says why beside its own number. A missing file is not fatal — the column
    prints its absence."""
    if not FRAMES.is_file():
        return {}
    rows, head = {}, None
    for line in FRAMES.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        cells = line.split("\t")
        if head is None:
            head = cells
            continue
        row = dict(zip(head, cells))
        if "shot" not in row:
            return {}
        rows[row["shot"]] = "pose=%s/%s/%s rain=%s wet=%s" % (
            row.get("camX", "?"), row.get("camZ", "?"), row.get("camYaw", "?"),
            row.get("rain", "?"), row.get("wet", "?"))
    return rows


def _printed(v, fmt):
    """The number as the page shows it. ONE implementation of "compare what the
    reader can see", shared by `outside_of` and `below_floor` — two copies of
    this rounding is the one-idea-two-sites shape that costs this project a
    round trip every time it happens."""
    return float(fmt % v)


def outside_of(lo, hi, v, fmt):
    """Is `v` outside [lo,hi] — judged on the PRINTED values, not the
    full-precision ones.

    `district_hook` read groundPatch 0.38234 against a reference top of 0.38190
    and the table showed `0.382!` beside a bound printed `0.382` — a flag no
    reader can check, on two numbers that are the same number as far as the page
    is concerned. Module level and not a closure inside the report so its own
    case can be PLANTED rather than waited for: a check that only fires when
    today's data happens to land on a bound is the flaky-gate shape rule 5b's
    corollary is about."""
    flo, fhi, got = (_printed(x, fmt) for x in (lo, hi, v))
    return got < flo or got > fhi


def below_floor(lo, v, fmt):
    """Is `v` below the references' floor for its key, on the PRINTED values.

    Same convention as `outside_of` and for the same reason: a `~` beside a
    number that prints equal to the floor printed next to it is a mark no
    reader can check. Planted in the selftest rather than waited for."""
    return _printed(v, fmt) < _printed(lo, fmt)


def above_ceiling(hi, v, fmt):
    """Is `v` above the references' ceiling for its key, on the PRINTED values.

    The mirror of `below_floor`, same convention and same reason. It exists
    because the floor half alone reads a near-black frame as a reading of
    nothing and a BLOWN one as a healthy street — `district_ironside`, the
    emptiest ground band in the set, sailed through unannotated at groundP90
    0.890 / groundMean 0.726 while a black frame was marked. Planted in the
    selftest rather than waited for."""
    return _printed(v, fmt) > _printed(hi, fmt)


def low_content_of(m, ranges, fmts):
    """The qualifying readings for one image, as [(key, value, bound, side)],
    where side is "floor" or "ceiling".

    EMPTY MEANS THE FRAME IS FINE, and every caller prints `none` for that
    rather than an empty string — a blank field reads as a tool that did not
    run. `ranges` is the five references' own (lo, hi) per key, so both bounds
    handed in here are measured, never a constant.

    TWO SIDES, AND THEY DO NOT COVER THE SAME KEYS. Below the floor on EITHER
    of LOW_CONTENT_FLOOR_KEYS; above the ceiling on LOW_CONTENT_CEIL_KEYS,
    which is the mean only. The asymmetry is measured and the working is beside
    the constants — a percentile is lifted past the ceiling by one bright
    highlight on a frame that is not blown, which would eat the two frames
    whose shadowRatio shortfall the 24 Aug ruling requires to stay a finding.

    A LIST AND NOT A BOOLEAN, because the decision requires the QUALIFYING
    NUMBER to be printed: `groundMean:0.115<0.142` and `groundMean:0.726>0.543`
    are each one token carrying the value, the bound it failed and which side
    it failed on, which is the pair shape the whole verdict channel is built
    on."""
    out = []
    for key in LOW_CONTENT_FLOOR_KEYS:
        if key not in ranges or key not in m:
            continue
        if below_floor(ranges[key][0], m[key], fmts[key]):
            out.append((key, m[key], ranges[key][0], "floor"))
    for key in LOW_CONTENT_CEIL_KEYS:
        if key not in ranges or key not in m:
            continue
        if above_ceiling(ranges[key][1], m[key], fmts[key]):
            out.append((key, m[key], ranges[key][1], "ceiling"))
    return out


def low_content_token(lc, fmts):
    """The `lowContent=` value: space-free, one token per qualifying reading,
    or the word `none`. The comparison character IS the side — `<` floor, `>`
    ceiling — so a reader never has to hold "which half fired" in their head
    beside the number. `(+N more not shown)` cannot bite here: the list is
    bounded by the floor keys plus the ceiling keys, which is three."""
    if not lc:
        return "none"
    return ",".join("%s:%s%s%s" % (k, fmts[k] % v,
                                   "<" if side == "floor" else ">",
                                   fmts[k] % bound)
                    for k, v, bound, side in lc)


def unreadable_dims(lc):
    """Which ratio rows one image's qualifying readings make unreadable.

    NOT "every ratio row when any bound fires" — that was the first version and
    it would have suppressed `groundOverFrame` on exactly the blown frames it
    was added to diagnose. Each ratio row declares the SIDES that break it
    (RATIO_DIMS[...]["unreadableOn"]); a row survives a side it is not
    degenerate under. Returns sorted names so the machine tail is stable."""
    sides = {side for _k, _v, _b, side in lc}
    return sorted(d for d, spec in RATIO_DIMS.items()
                  if sides & set(spec["unreadableOn"]))


def ratio_band_reading(dim, named, ranges, fmts):
    """One ratio row's in-band count, with the denominators the ruling asks for.

    Returns a dict; `named` is [(shotName, measurement)] — the SAME list, in the
    same order, that the table and the machine tail are built from, taken from
    one measurement pass. So `inBand`, `readable` and `unreadable` are the same
    instant by construction and cannot be three moments quoted as one.

    WHAT EACH NUMBER IS A STATISTIC OF:
      stills      COUNT of sim stills measured this run — the denominator
      unreadable  COUNT of those whose ground band is low-content ON A SIDE
                  THIS ROW IS DEGENERATE UNDER — so the two ratio rows have
                  different unreadable counts in the same run, on purpose
      readable    COUNT of the rest; stills - unreadable, by construction
      inBand      COUNT of READABLE stills whose printed ratio lies inside the
                  references' printed range. Never a fraction of `stills`: an
                  unreadable row is neither in nor out, and counting it either
                  way is the reading this annotation exists to refuse."""
    lo, hi = ranges[dim]
    fmt = fmts[dim]
    unreadable, in_band = [], []
    for name, m in named:
        if dim in unreadable_dims(low_content_of(m, ranges, fmts)):
            unreadable.append(name)
        elif not outside_of(lo, hi, m[dim], fmt):
            in_band.append(name)
    return {"dim": dim, "inputs": RATIO_DIMS[dim]["inputs"],
            "unreadableOn": RATIO_DIMS[dim]["unreadableOn"],
            "lo": lo, "hi": hi, "fmt": fmt,
            "stills": len(named), "unreadable": unreadable, "inBand": in_band,
            "readable": len(named) - len(unreadable),
            "floors": [(k, ranges[k][0]) for k in LOW_CONTENT_FLOOR_KEYS
                       if k in ranges],
            "ceilings": [(k, ranges[k][1]) for k in LOW_CONTENT_CEIL_KEYS
                         if k in ranges]}


def capped(names, cap=NAME_CAP, sep=","):
    """A list rendered space-free with its truncation ANNOUNCED. A cap that
    does not say it bit reads as a finding — `| head -3` on the character audit
    once read as three of five bodies failing, and nothing was broken."""
    if len(names) <= cap:
        return sep.join(names) if names else "none"
    return sep.join(names[:cap]) + sep + "(+%dmore-not-shown)" % (len(names) - cap)


def shot_name(path):
    """The frames.tsv shot key: `review_` comes off, `district_` stays on,
    because that is how the sim names its own rows."""
    n = path.stem
    if n.startswith("review_"):
        n = n[len("review_"):]
    return n


def col_label(path):
    """The table's column head, which must FIT and must be TELLING. `district_`
    comes off here and only here — seven columns all reading `district_c` at
    ten characters is a header that identifies nothing, and the `*` the legend
    explains already says which ones are districts."""
    n = shot_name(path)
    if n.startswith(STABLE_PREFIX):
        n = n[len(STABLE_PREFIX):]
    return n


# --------------------------------------------------------------------- report

_SCALARS = {}       # (path, mtime_ns, size) -> the scalar reading for that file


def gather(stable_only=False, keep_arrays=False):
    """Measure both sides. Returns (refs, sims, errors, counts).

    The scalar readings are memoised on (path, mtime, size), because verify.py
    runs the selftest, which produces three reports over the same five
    references. Keyed on mtime AND size so editing a still cannot hand back the
    old numbers — a cache that can go stale is the instrument lying quietly,
    which is the one thing this file is against."""
    refs, ref_seen = images_in(REFDIR)
    sims, sim_seen = images_in(SIMDIR, prefixes=SIM_PREFIXES)
    if stable_only:
        sims = [p for p in sims if p.name.startswith(STABLE_PREFIX)]
    errors = []

    def run(paths):
        out = []
        for p in paths:
            try:
                st = p.stat()
                key = (str(p), st.st_mtime_ns, st.st_size)
                if not keep_arrays and key in _SCALARS:
                    out.append((p, _SCALARS[key]))
                    continue
                m = measure(load(p), keep_arrays=keep_arrays)
                if not keep_arrays:
                    _SCALARS[key] = m
                out.append((p, m))
            except Unreadable as exc:
                errors.append(str(exc))
        return out

    return run(refs), run(sims), errors, {
        "refFiles": ref_seen, "simFiles": sim_seen,
        "refNamed": len(refs), "simNamed": len(sims)}


def report(stable_only=False):
    refs, sims, errors, counts = gather(stable_only)

    if counts["refFiles"] < 0:
        print("NOTHING MEASURED — no reference directory at %s" % REFDIR)
        return 3
    if counts["simFiles"] < 0:
        print("NOTHING MEASURED — no sim-shots directory at %s" % SIMDIR)
        return 3
    if not refs:
        print("NOTHING MEASURED — 0 readable reference frames in %s "
              "(%d files examined, %d with an image extension)"
              % (REFDIR, counts["refFiles"], counts["refNamed"]))
        for e in errors:
            print("  UNREADABLE %s" % e)
        return 3
    if not sims:
        print("NOTHING MEASURED — 0 readable sim stills in %s "
              "(%d files examined, %d named %s)"
              % (SIMDIR, counts["simFiles"], counts["simNamed"],
                 "/".join(x + "*" for x in SIM_PREFIXES)))
        for e in errors:
            print("  UNREADABLE %s" % e)
        return 3

    lines = []
    out = lines.append
    rows = shot_rows()
    out("ref-bench: %d reference frames vs %d sim stills, resampled to %dx%d, "
        "edge cut %d, vert cut %d" % (len(refs), len(sims), WORK[0], WORK[1],
                                      EDGE_T, VERT_T))
    out("  STEERING PROXY, NOT A QUALITY SCORE — the judge is a person with the "
        "frames side by side.")
    out("  READ edge density WITH grain sigma: a black frame of pure film grain "
        "scores 0.42 on one and 0.06 on GROUND PATCH.")
    out("  READ GROUND PATCH WITH ground/frame: patch is std/mean, so an "
        "ADDITIVE lift lowers it and a multiplicative one cannot move it. A low "
        "patch means BLOWN OR FLAT until ground/frame says which.")
    out("  * = pose-stable across builds (district_*). Every other sim column is "
        "a different photograph each run.")
    out("  ~ = LOW-CONTENT frame: a ratio row whose ground-band input sits below "
        "the references' own floor or above their own ceiling, on a side that "
        "row is degenerate under. Marked, never dropped — the value stays on "
        "the page and may not be quoted.")
    out("")

    ranges = {k: (min(m[k] for _p, m in refs), max(m[k] for _p, m in refs))
              for k, _l, _f, _s in DIMS}
    named = [(shot_name(p), m) for p, m in sims]
    # ONE call site for the qualifier per image; the table cell, the machine
    # tail and the ratio-band counts all read this same list, so the three
    # renderings of one judgement cannot disagree (the lesson `is_outside`
    # below was already written for).
    lowc = [low_content_of(m, ranges, FMTS) for _p, m in sims]
    # ...and ONE call site for "which ratio rows does that make unreadable",
    # for the same reason: the `~` in the table, `ratioUnreadable=` on the
    # image line and the per-dim counts on the ratioband line are three
    # renderings of this one list.
    lowdims = [set(unreadable_dims(lc)) for lc in lowc]
    cols = [(col_label(p), "*" if p.name.startswith(STABLE_PREFIX) else "", m, ld)
            for (p, m), ld in zip(sims, lowdims)]

    def is_outside(key, fmt, v):
        """`outside_of` against this key's reference range. The table, the
        machine tail's `outside=` list and the summary count all go through
        here, so the three renderings of one judgement cannot disagree."""
        return outside_of(ranges[key][0], ranges[key][1], v, fmt)

    nblocks = (len(cols) + COLS_PER_BLOCK - 1) // COLS_PER_BLOCK
    for bi in range(nblocks):
        chunk = cols[bi * COLS_PER_BLOCK:(bi + 1) * COLS_PER_BLOCK]
        head = "%-22s %-15s" % ("dimension", "ref lo..hi")
        for name, star, _m, _lc in chunk:
            head += "%12s" % (name[:10] + star)
        out("  block %d of %d — sim stills %d-%d of %d"
            % (bi + 1, nblocks, bi * COLS_PER_BLOCK + 1,
               bi * COLS_PER_BLOCK + len(chunk), len(cols)))
        out(head)
        out("  " + "-" * (len(head) - 2))
        for key, label, fmt, _stat in DIMS:
            lo, hi = ranges[key]
            row = "%-22s %-15s" % (label, (fmt + ".." + fmt) % (lo, hi))
            for _n, _s, m, ld in chunk:
                v = m[key]
                # `~` MARKS, IT DOES NOT REPLACE. The `!` stays because the raw
                # reading really is outside the band; the `~` says the reading
                # cannot carry that conclusion. Dropping either would be the
                # exclusion the ruling refused.
                cell = ("~" if key in ld else "") + fmt % v
                row += "%11s%s" % (cell, "!" if is_outside(key, fmt, v) else " ")
            out(row)
        out("")

    outside = checked = unreadable_readings = 0
    for _n, _s, m, ld in cols:
        for key, _l, fmt, _st in DIMS:
            checked += 1
            outside += 1 if is_outside(key, fmt, m[key]) else 0
            unreadable_readings += 1 if key in ld else 0
    out("  ! = outside the five references' range. %d of %d readings outside "
        "(%d dimensions x %d stills), of which %d sit on a ~ low-content ratio "
        "row and are not readable as findings."
        % (outside, checked, len(DIMS), len(cols), unreadable_readings))
    nstable = sum(1 for _n, st, _m, _lc in cols if st == "*")
    out("  %d of %d sim stills are pose-stable%s."
        % (nstable, len(cols),
           "" if stable_only else "; --stable keeps only those"))
    out("")

    # ---- the ratio rows, counted the way the 24 Aug ruling requires: in band
    # X of Y READABLE, +Z unreadable NAMED, against the number examined.
    bands = [ratio_band_reading(d, named, ranges, FMTS) for d in sorted(RATIO_DIMS)]
    floors = ", ".join("%s %s" % (k, FMTS[k] % v) for k, v in bands[0]["floors"]) \
        if bands else "none"
    ceils = ", ".join("%s %s" % (k, FMTS[k] % v) for k, v in bands[0]["ceilings"]) \
        if bands else "none"
    out("  RATIO ROWS (%d of %d dimensions) — the low-content annotation, keyed "
        "to the five references' OWN floor (%s) and their OWN ceiling (%s). "
        "The ceiling covers the mean only: one bright highlight lifts a "
        "percentile past it on a frame that is not blown."
        % (len(RATIO_DIMS), len(DIMS), floors, ceils))
    for b in bands:
        band_txt = (b["fmt"] + ".." + b["fmt"]) % (b["lo"], b["hi"])
        if b["readable"] == 0:
            # RULE 3b: "0 in band" over no readable frame at all must not be
            # able to read as health, so it says the words instead of a number.
            head_txt = "in band NOTHING MEASURED — 0 of 0 readable stills"
        else:
            head_txt = "in band %d of %d readable stills" % (
                len(b["inBand"]), b["readable"])
        out("    %s = %s (unreadable on the %s side), band %s: %s (+%d "
            "unreadable low-content), %d stills examined."
            % (b["dim"], "/".join(b["inputs"]), "+".join(b["unreadableOn"]),
               band_txt, head_txt, len(b["unreadable"]), b["stills"]))
        shown = b["unreadable"][:NAME_CAP]
        more = len(b["unreadable"]) - len(shown)
        out("      unreadable: %s%s" % (
            " ".join(shown) if shown else "none",
            " (+%d more not shown)" % more if more else ""))
    out("")

    out("  reference frames — pixels each statistic saw:")
    for p, m in refs:
        out("    %-34s whole=%d ground=%d mid=%d patchWindows=%d"
            % (p.name, m["_pxWhole"], m["_pxGround"], m["_pxMid"], m["_nPatch"]))
    out("  sim stills — the run's own camera and weather, from frames.tsv:")
    npose = 0
    for p, _m in sims:
        r = rows.get(shot_name(p))
        npose += 1 if r else 0
        out("    %-34s %s" % (p.name, r or "not in frames.tsv"))
    out("    (%d of %d stills matched a frames.tsv row%s)"
        % (npose, len(sims), "" if rows else " — frames.tsv absent or unparsed"))
    out("")

    for e in errors:
        out("  UNREADABLE %s" % e)
    out("  unreadable images: %d of %d files opened"
        % (len(errors), len(refs) + len(sims) + len(errors)))
    out("")

    # ---- machine tail: one image per line, every value space-free
    out("refGap image=REFBAND n=%d %s" % (
        len(refs),
        " ".join("%s=%s" % (k, (f + ".." + f) % ranges[k])
                 for k, _l, f, _s in DIMS)))
    for (p, m), lc, ld in zip(sims, lowc, lowdims):
        bad = [k for k, _l, f, _s in DIMS if is_outside(k, f, m[k])]
        # `ratioUnreadable=` is the rows THIS frame's qualifying side breaks,
        # not every ratio row in the tool: a blown frame keeps groundOverFrame,
        # which is the row that says it is blown.
        out("refGap image=%s stable=%s %s outside=%s lowContent=%s "
            "ratioUnreadable=%s px=%d/%d/%d patchWindows=%d"
            % (shot_name(p), "yes" if p.name.startswith(STABLE_PREFIX) else "no",
               " ".join("%s=%s" % (k, f % m[k]) for k, _l, f, _s in DIMS),
               ",".join(bad) if bad else "none",
               low_content_token(lc, FMTS),
               ",".join(sorted(ld)) if ld else "none",
               m["_pxWhole"], m["_pxGround"], m["_pxMid"], m["_nPatch"]))
    # ONE LINE PER RATIO ROW, whole-run numbers only. Every count here is over
    # this run's sim stills and belongs on a run-level line, never beside a
    # per-image reading — two moments under one grep is what cost this project
    # an afternoon.
    for b in bands:
        shown = b["unreadable"][:NAME_CAP]
        # `unreadableRatio`, not `unreadable`: the summary line below already
        # spends `unreadable=` on IMAGES THAT WOULD NOT DECODE, and one key
        # meaning two things on two lines is the fault a grep cannot see.
        out("refGap scope=ratioband dim=%s inputs=%s unreadableOn=%s band=%s "
            "inBand=%d readable=%d unreadableRatio=%d stills=%d floor=%s "
            "ceiling=%s namesShown=%d namesNotShown=%d unreadableStills=%s"
            % (b["dim"], "/".join(b["inputs"]), "+".join(b["unreadableOn"]),
               (b["fmt"] + ".." + b["fmt"]) % (b["lo"], b["hi"]),
               len(b["inBand"]), b["readable"], len(b["unreadable"]), b["stills"],
               "/".join("%s:%s" % (k, FMTS[k] % v) for k, v in b["floors"]) or "none",
               "/".join("%s:%s" % (k, FMTS[k] % v) for k, v in b["ceilings"]) or "none",
               len(shown), len(b["unreadable"]) - len(shown),
               capped(b["unreadable"])))
    out("refGap scope=summary refFrames=%d simStills=%d dims=%d outside=%d outsideOf=%d "
        "unreadable=%d filesExamined=%d/%d edgeCut=%d vertCut=%d "
        "patchBlock=%d patchWin=%d work=%dx%d ratioDims=%d lowContentStills=%d/%d "
        "lowContentFloorStills=%d lowContentCeilStills=%d "
        "lowContentFloorKeys=%s lowContentCeilKeys=%s unreadableRatioReadings=%d"
        % (len(refs), len(sims), len(DIMS), outside, checked, len(errors),
           counts["refFiles"], counts["simFiles"], EDGE_T, VERT_T,
           PATCH_BLOCK, PATCH_WIN, WORK[0], WORK[1], len(RATIO_DIMS),
           sum(1 for lc in lowc if lc), len(sims),
           # WHICH HALF FIRED, counted apart: "12 of 17 low-content" hides that
           # 5 are black and 7 are blown, and those two have opposite fixes.
           sum(1 for lc in lowc if any(s2 == "floor" for _k, _v, _b, s2 in lc)),
           sum(1 for lc in lowc if any(s2 == "ceiling" for _k, _v, _b, s2 in lc)),
           "/".join(LOW_CONTENT_FLOOR_KEYS), "/".join(LOW_CONTENT_CEIL_KEYS),
           unreadable_readings))

    print("\n".join(lines))
    return 4 if errors else 0


# --------------------------------------------------------------------- series

CUTS_EDGE = [8, 12, 16, 24, 32, 48, 64]
CUTS_VERT = [16, 24, 32, 40, 48, 56, 72]
PATCH_SHAPES = [(8, 8), (16, 4), (16, 8), (32, 2)]


def series():
    """The distributions every cut in this tool was chosen from. Rule 2: the
    first version of a bound is a printer.

    The raw per-image rows go ABOVE any summary, on purpose — an aggregate
    cannot see a regime change and a row of numbers shows one in a second
    (`confabs` read 1..13 under one conversation rule and 29..74 under the next,
    and its all-time median described neither)."""
    global VERT_T, PATCH_BLOCK, PATCH_WIN
    refs, sims, errors, counts = gather(keep_arrays=True)
    if not refs or not sims:
        print("NOTHING MEASURED — refs=%d sims=%d (%d/%d files examined)"
              % (len(refs), len(sims), counts["refFiles"], counts["simFiles"]))
        return 3
    np = _np()

    for title, cuts, pick, span in (
            ("FIND_EDGES magnitude, GROUND band", CUTS_EDGE, "_edge", GROUND_Y),
            ("Sobel-x magnitude, UPPER band", CUTS_VERT, "_gx", UPPER_Y)):
        print("== %s ==" % title)
        print("%-34s %6s %6s %6s %6s   %s"
              % ("image", "p50", "p90", "p99", "max",
                 " ".join("%6s" % ("f>%d" % c) for c in cuts)))
        for side, group in (("REF", refs), ("SIM", sims)):
            for p, m in group:
                vals, n = band(np, m[pick], m["_mask"], span)
                if n == 0:
                    print("%s %-30s nothing measured (0 px in band)"
                          % (side, p.name[:30]))
                    continue
                print("%s %-30s %6.1f %6.1f %6.1f %6.1f   %s"
                      % (side, p.name[:30],
                         np.percentile(vals, 50), np.percentile(vals, 90),
                         np.percentile(vals, 99), vals.max(),
                         " ".join("%6.3f" % (vals > c).mean() for c in cuts)))
        print("")

    print("== fraction over each cut: how many of the %d sim stills land inside "
          "the %d references' range ==" % (len(sims), len(refs)))
    for pick, cuts, span, label in (("_edge", CUTS_EDGE, GROUND_Y, "edgeGround"),
                                    ("_gx", CUTS_VERT, UPPER_Y, "sobelUpper")):
        for c in cuts:
            rv = [float((band(np, m[pick], m["_mask"], span)[0] > c).mean())
                  for _p, m in refs]
            sv = [float((band(np, m[pick], m["_mask"], span)[0] > c).mean())
                  for _p, m in sims]
            lo, hi = min(rv), max(rv)
            print("  %s cut=%-3d ref %.3f..%.3f  sim %.3f..%.3f  inside %d of %d"
                  % (label, c, lo, hi, min(sv), max(sv),
                     sum(1 for v in sv if lo <= v <= hi), len(sv)))
        print("")

    print("== vertical COMPONENT counts per cut (the run detector, not a raw "
          "fraction). Not monotone, on purpose — see vertical_runs. ==")
    keep = VERT_T
    print("%-34s %s" % ("image", " ".join("%7s" % ("t=%d" % c) for c in CUTS_VERT)))
    for side, group in (("REF", refs), ("SIM", sims)):
        for p, m in group:
            got = []
            for c in CUTS_VERT:
                VERT_T = c
                got.append(vertical_runs(np, m["_gx"], m["_mask"],
                                         WORK[1], WORK[0])[0])
            print("%s %-30s %s" % (side, p.name[:30],
                                   " ".join("%7d" % g for g in got)))
    VERT_T = keep
    print("")

    print("== GROUND PATCH per block/window shape. The reference SPAN does not "
          "separate the shapes; what does is how much grain leaks through, so "
          "read district_downtown's row — it holds nothing but grain. ==")
    kb, kw = PATCH_BLOCK, PATCH_WIN
    print("%-34s %s" % ("image", " ".join("%11s" % ("%d/%d" % s)
                                          for s in PATCH_SHAPES)))
    got_ref = {s: [] for s in PATCH_SHAPES}
    got_sim = {s: [] for s in PATCH_SHAPES}
    for side, group, sink in (("REF", refs, got_ref), ("SIM", sims, got_sim)):
        for p, m in group:
            vals = []
            for s in PATCH_SHAPES:
                PATCH_BLOCK, PATCH_WIN = s
                v = ground_patch(np, m["_luma255"], m["_mask"])[0]
                vals.append(v)
                sink[s].append(v)
            print("%s %-30s %s" % (side, p.name[:30],
                                   " ".join("%11.3f" % v for v in vals)))
    PATCH_BLOCK, PATCH_WIN = kb, kw
    for s in PATCH_SHAPES:
        lo, hi = min(got_ref[s]), max(got_ref[s])
        print("  block/window %d/%d  ref %.3f..%.3f (span x%.1f)  sim %.3f..%.3f"
              % (s[0], s[1], lo, hi, hi / max(lo, 1e-6),
                 min(got_sim[s]), max(got_sim[s])))
    print("")

    print("== grain sigma (Immerkaer, ground band) beside edge density ==")
    print("%-34s %8s %8s %8s" % ("image", "sigma", "edge>%d" % EDGE_T, "patch"))
    for side, group in (("REF", refs), ("SIM", sims)):
        for p, m in group:
            print("%s %-30s %8.2f %8.3f %8.3f"
                  % (side, p.name[:30], m["grainSigma"], m["edgeGround"],
                     m["groundPatch"]))
    print("  Spearman(grainSigma, edgeGround): sim rho=%.3f (n=%d), "
          "ref rho=%.3f (n=%d)"
          % (spearman([m["grainSigma"] for _p, m in sims],
                      [m["edgeGround"] for _p, m in sims]), len(sims),
             spearman([m["grainSigma"] for _p, m in refs],
                      [m["edgeGround"] for _p, m in refs]), len(refs)))
    print("")
    low_content_series(refs, sims)
    print("unreadable images: %d of %d files opened"
          % (len(errors), len(refs) + len(sims) + len(errors)))
    for e in errors:
        print("  UNREADABLE %s" % e)
    return 4 if errors else 0


def low_content_series(refs, sims):
    """THE SERIES THE LOW-CONTENT RULE WAS TAKEN FROM, reprinted every run.

    Rule 2: the first version of a bound is a printer, and the bounds here are
    not even numbers — they are min() and max() over the five references' own
    readings, so what has to be checkable is (a) that those five readings are
    what the bounds are made of, (b) that the OR over the two input statistics
    is doing work the AND would not, and (c) that the CEILING half is carried
    by the key the series says can carry it.

    A LADDER: one contributor toggled at a time, every rung printed from the
    same measurement pass in the same run, because rungs compared across runs
    are different photographs. The rows go above the rungs — an aggregate
    cannot show a regime change and a row of numbers shows one in a second."""
    ranges = {k: (min(m[k] for _p, m in refs), max(m[k] for _p, m in refs))
              for k, _l, _f, _s in DIMS}
    ratio_keys = sorted(RATIO_DIMS)
    print("== LOW-CONTENT QUALIFIER: the floor IS the five references' own "
          "minimum and the ceiling IS their own maximum, per statistic. "
          "Nothing below is a constant. ==")
    head = "%-34s %s   %s" % ("image",
                              " ".join("%10s" % k for k in LOW_CONTENT_KEYS),
                              " ".join("%16s" % k for k in ratio_keys))
    print(head)
    for side, group in (("REF", refs), ("SIM", sims)):
        for p, m in group:
            print("%s %-30s %s   %s"
                  % (side, p.name[:30],
                     " ".join("%10s" % (FMTS[k] % m[k])
                              for k in LOW_CONTENT_KEYS),
                     " ".join("%16s" % (FMTS[k] % m[k]) for k in ratio_keys)))
    for k in LOW_CONTENT_KEYS:
        print("  %s range over %d references %s..%s — floor %s%s"
              % (k, len(refs), FMTS[k] % ranges[k][0], FMTS[k] % ranges[k][1],
                 "TAKEN" if k in LOW_CONTENT_FLOOR_KEYS else "not taken",
                 ", ceiling TAKEN" if k in LOW_CONTENT_CEIL_KEYS
                 else ", ceiling NOT taken (a percentile is lifted past it by "
                      "one highlight on a frame that is not blown)"))
    print("")

    print("== THE LADDER: which stills qualify as low-content under each rule, "
          "same run, same pass. `floor-either + ceiling-mean` is what ships. ==")
    per_floor = {k: [shot_name(p) for p, m in sims
                     if below_floor(ranges[k][0], m[k], FMTS[k])]
                 for k in LOW_CONTENT_KEYS}
    per_ceil = {k: [shot_name(p) for p, m in sims
                    if above_ceiling(ranges[k][1], m[k], FMTS[k])]
                for k in LOW_CONTENT_KEYS}
    floor_either = [shot_name(p) for p, m in sims
                    if any(below_floor(ranges[k][0], m[k], FMTS[k])
                           for k in LOW_CONTENT_FLOOR_KEYS)]
    floor_both = [n for n in per_floor[LOW_CONTENT_FLOOR_KEYS[0]]
                  if n in per_floor[LOW_CONTENT_FLOOR_KEYS[1]]]
    taken = [shot_name(p) for p, m in sims if low_content_of(m, ranges, FMTS)]
    rungs = [("%s below floor" % k, per_floor[k]) for k in LOW_CONTENT_KEYS]
    rungs += [("floor either", floor_either), ("floor both", floor_both)]
    rungs += [("%s above ceiling" % k, per_ceil[k]) for k in LOW_CONTENT_KEYS]
    rungs += [("SHIPPED: floor-either + ceiling-%s"
               % "/".join(LOW_CONTENT_CEIL_KEYS), taken)]
    for label, names in rungs:
        print("  %-40s %2d of %2d stills   %s"
              % (label, len(names), len(sims), capped(names, sep=" ")))
    print("  The floor rungs differ by %d still(s); those are the frames the "
          "AND rule would call readable street."
          % (len(floor_either) - len(floor_both)))
    ceil_only_p90 = [n for n in per_ceil["groundP90"]
                     if n not in per_ceil["groundMean"]] \
        if "groundP90" in per_ceil and "groundMean" in per_ceil else []
    print("  A groundP90 ceiling would ALSO take %d still(s) the mean ceiling "
          "leaves readable: %s — the cost of the ceiling half being symmetric."
          % (len(ceil_only_p90), capped(ceil_only_p90, sep=" ")))
    print("")

    print("== WHAT THE ANNOTATION DOES TO EACH RATIO ROW'S COUNT ==")
    named = [(shot_name(p), m) for p, m in sims]
    for d in ratio_keys:
        b = ratio_band_reading(d, named, ranges, FMTS)
        naive = sum(1 for _n, m in named
                    if not outside_of(b["lo"], b["hi"], m[d], b["fmt"]))
        print("  %s band %s: before %d of %d in band; after %d of %d READABLE "
              "in band (+%d unreadable, named: %s)"
              % (d, (b["fmt"] + ".." + b["fmt"]) % (b["lo"], b["hi"]),
                 naive, b["stills"], len(b["inBand"]), b["readable"],
                 len(b["unreadable"]), capped(b["unreadable"], sep=" ")))
    print("")


def spearman(a, b):
    """Rank correlation, ties broken by order. Used once, to state how far
    `edgeGround` is a function of grain rather than of content — and printed
    with its n, because rho on five points is not evidence of anything."""
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        out = [0] * len(v)
        for j, i in enumerate(order):
            out[i] = j
        return out
    if len(a) < 3:
        return float("nan")
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra)
                    * sum((y - mb) ** 2 for y in rb))
    return num / den if den else float("nan")


# ------------------------------------------------------------------- selftest

def selftest():
    """ACCEPTING CASE FIRST — the expensive failure is a validator nothing
    survives, and the live directories are the accepting fixture that cannot be
    fooled by one I wrote (rule 5b, and the CS0426 lint's "run it against the
    whole repository" argument applied to pixels)."""
    global REFDIR, SIMDIR
    import atexit
    import contextlib
    import io
    import shutil
    import tempfile

    ok, fails = 0, []

    def check(name, cond):
        nonlocal ok
        if cond:
            ok += 1
        else:
            fails.append(name)

    # ---- 1. ACCEPTING: the real directories produce a whole table.
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = report()
    text = buf.getvalue()
    n_sims = len(images_in(SIMDIR, prefixes=SIM_PREFIXES)[0])
    check("accepting: report exits 0 on the live directories", code == 0)
    check("accepting: every dimension has a row",
          all(label in text for _k, label, _f, _s in DIMS))
    check("accepting: the reference band line is emitted",
          "refGap image=REFBAND" in text)
    check("accepting: one refGap line per sim still",
          text.count("refGap image=") - 1 == n_sims)
    check("accepting: every dimension is in the machine tail",
          all(("%s=" % k) in text for k, _l, _f, _s in DIMS))
    check("accepting: the summary carries its denominators",
          "outsideOf=" in text and "unreadable=" in text
          and "filesExamined=" in text)
    check("accepting: no refGap token carries a space or splits",
          all(tok.count("=") == 1 for line in text.splitlines()
              if line.startswith("refGap") for tok in line.split()[1:]))
    check("accepting: the block cap announces itself",
          "block 1 of " in text and "sim stills 1-" in text)
    check("accepting: pose and weather are stated per still", "pose=" in text)
    check("accepting: the proxy caveat is printed", "NOT A QUALITY SCORE" in text)
    check("accepting: the grain caveat rides beside edge density",
          "READ edge density WITH grain sigma" in text)
    check("accepting: patch windows report their count", "patchWindows=" in text)

    # THE TABLE AND THE TAIL MUST AGREE ABOUT WHAT IS OUT. They are two
    # renderings of one judgement and a reader will diff them; `district_hook`
    # once printed 0.382! beside a bound printed 0.382, because the flag read
    # full precision and the page read three decimals.
    labels = tuple(label for _k, label, _f, _s in DIMS)
    bangs = sum(l.count("!") for l in text.splitlines() if l.startswith(labels))
    tail_bad = sum(0 if "outside=none" in l
                   else len(l.split("outside=")[1].split()[0].split(","))
                   for l in text.splitlines() if l.startswith("refGap image=")
                   and "outside=" in l)
    summary_bad = int(text.split("refGap scope=summary")[1]
                      .split("outside=")[1].split()[0])
    check("accepting: table flags, refGap outside= and the summary all agree",
          bangs == tail_bad == summary_bad)
    cells = on_bound = flagged_on_bound = 0
    for row in text.splitlines():
        if not row.startswith(labels):
            continue
        lo, _, hi = row[22:38].strip().partition("..")
        body = row[38:]
        for i in range(0, len(body) - 11, 12):
            cell, flag = body[i:i + 11].strip(), body[i + 11:i + 12]
            if not cell:
                continue
            cells += 1
            if cell in (lo, hi):
                on_bound += 1
                flagged_on_bound += 1 if flag == "!" else 0
    # THE DENOMINATOR FIRST, or the check below is a zero that examined nothing:
    # if the column arithmetic ever changes, this parser reads no cells, finds
    # no boundary values, and passes for the wrong reason.
    check("accepting: the table parser reads every cell (%d of %d)"
          % (cells, len(DIMS) * n_sims), cells == len(DIMS) * n_sims)
    check("accepting: no printed value equal to its printed bound is flagged "
          "(%d such cells of %d)" % (on_bound, cells), flagged_on_bound == 0)
    # PLANTED, so this does not wait on the live data to land on a bound:
    check("bound: a value rounding onto the top bound is INSIDE",
          not outside_of(0.20500, 0.38190, 0.38234, "%.3f"))
    check("bound: a value rounding onto the low bound is INSIDE",
          not outside_of(0.20500, 0.38190, 0.20451, "%.3f"))
    check("bound: a value a printed step above the top is OUTSIDE",
          outside_of(0.20500, 0.38190, 0.38251, "%.3f"))
    check("bound: a value a printed step below the low is OUTSIDE",
          outside_of(0.20500, 0.38190, 0.20449, "%.3f"))
    check("bound: the integer format rounds to whole counts",
          not outside_of(22, 49, 49.4, "%.0f") and outside_of(22, 49, 49.6, "%.0f"))

    # ---- 1b. THE LOW-CONTENT ANNOTATION, ACCEPTING FIXTURES FIRST.
    #
    # THE STRUCTURAL ONE LEADS, because it is the only fixture nothing can
    # invalidate: the floor is min() and the ceiling is max() over the five
    # references themselves, so no reference frame can ever qualify. If one
    # does, the qualifier has stopped being derived from them.
    lrefs, lsims, _le, _lc = gather()
    lranges = {k: (min(m[k] for _p, m in lrefs), max(m[k] for _p, m in lrefs))
               for k, _l, _f, _s in DIMS}
    ref_lc = [(p2.name, low_content_of(m, lranges, FMTS)) for p2, m in lrefs]
    check("accepting: no reference frame can qualify as low-content (%d of %d "
          "clean)" % (sum(1 for _n, lc in ref_lc if not lc), len(ref_lc)),
          bool(ref_lc) and not any(lc for _n, lc in ref_lc))

    # THE LIVE ONE SECOND. `district_hook` is a bright street frame reading
    # BELOW the shadow band at 0.149, and that reading is the residual the
    # ambient-fill rung owns. If this annotation ever swallows it, the tool has
    # started hiding the finding it was built beside — the exclusion the 24 Aug
    # ruling refused. The expensive failure of an outlier rule is the one that
    # eats real frames, not the one that misses a black one.
    by_name = {shot_name(p2): m for p2, m in lsims}
    hook = by_name.get("district_hook")
    check("accepting: the live fixture district_hook is present", hook is not None)
    if hook:
        hook_lc = low_content_of(hook, lranges, FMTS)
        check("accepting: district_hook is NOT low-content (%s)"
              % low_content_token(hook_lc, FMTS), not hook_lc)
        check("accepting: district_hook's inputs are inside every bound it is "
              "judged by (groundP90 %.3f in %.3f..%.3f, groundMean %.3f in "
              "%.3f..%.3f)"
              % (hook["groundP90"], lranges["groundP90"][0],
                 lranges["groundP90"][1], hook["groundMean"],
                 lranges["groundMean"][0], lranges["groundMean"][1]),
              all(not below_floor(lranges[k][0], hook[k], FMTS[k])
                  for k in LOW_CONTENT_FLOOR_KEYS)
              and all(not above_ceiling(lranges[k][1], hook[k], FMTS[k])
                      for k in LOW_CONTENT_CEIL_KEYS))
        # AN IMPLICATION, NOT A CONJUNCTION, and the difference is this whole
        # section's lesson: hook's groundP90 sits ABOVE the references' ceiling
        # today (0.868 > 0.831) and darkening the ground could move it back
        # under. Asserting the state would pin an accepting case to a number the
        # queued work is trying to change; asserting the RULE — a P90 over the
        # ceiling must not by itself annotate a frame — holds either way, and
        # says which case it saw.
        p90_over = above_ceiling(lranges["groundP90"][1], hook["groundP90"],
                                 FMTS["groundP90"])
        check("accepting: a groundP90 above the ceiling does not annotate on "
              "its own (hook P90 %.3f vs ceiling %.3f — %s today)"
              % (hook["groundP90"], lranges["groundP90"][1],
                 "live case exercised" if p90_over
                 else "live case absent, planted case below covers it"),
              (not p90_over) or not low_content_of(hook, lranges, FMTS))
        check("accepting: district_hook's line says lowContent=none "
              "ratioUnreadable=none",
              any(l.startswith("refGap image=district_hook ")
                  and "lowContent=none" in l and "ratioUnreadable=none" in l
                  for l in text.splitlines()))

    # ---- 1c. REJECTING, AND THE FIXTURE IS SYNTHETIC ON PURPOSE.
    #
    # It used to be `district_downtown`, pinned because that frame was
    # near-black. Build 6137608 re-sited the camera, the frame became a lit
    # street (meanLuma 0.096 -> 0.412), and the selftest went red 3 of 78 — so
    # verify went red for the work having been done. A rejecting case pinned to
    # a real asset is a trap this project has sprung before. These three frames
    # are generated here and no improvement to the game can reach them:
    #   black   a reading of nothing by DARKNESS  -> floor side
    #   blown   a reading of nothing by BLOWOUT   -> ceiling side (the half
    #           added 25 Aug; `district_ironside` sailed through without it)
    #   mid     a readable band                   -> must NOT qualify, so the
    #           fixture proves the rule discriminates rather than marking all
    npx = _np()
    from PIL import Image as _Img
    synth = pathlib.Path(tempfile.mkdtemp(prefix="refbench-synth-"))
    atexit.register(shutil.rmtree, synth, True)
    h_s, w_s = WORK[1], WORK[0]

    def _write(name, arr):
        _Img.fromarray(np_stack(npx, arr), "RGB").save(synth / name)

    def np_stack(npx_, plane):
        return npx_.repeat(plane.reshape(h_s, w_s, 1), 3, axis=2)

    black = npx.full((h_s, w_s), 5, dtype=npx.uint8)
    blown = npx.full((h_s, w_s), 217, dtype=npx.uint8)          # 0.851 luma
    midp = npx.full((h_s, w_s), 90, dtype=npx.uint8)            # 0.353 luma
    midp[::2, ::2] = 110
    midp[1::2, 1::2] = 70
    _write("district_synth_black.png", black)
    _write("district_synth_blown.png", blown)
    _write("district_synth_mid.png", midp)

    # A PRECONDITION, NAMED, so a failure below points at the cause instead of
    # looking like the rule broke: the live references' bounds must lie inside
    # the synthetic extremes, or these frames are not on the far side of them.
    check("rejecting: the synthetic extremes bracket the live bounds "
          "(black 0.020 < floor %.3f, blown 0.851 > ceiling %.3f)"
          % (lranges["groundMean"][0], lranges["groundMean"][1]),
          0.020 < lranges["groundMean"][0] and lranges["groundMean"][1] < 0.851)

    keep_ref, keep_sim = REFDIR, SIMDIR
    SIMDIR = synth
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        scode = report()
    SIMDIR = keep_sim
    stext = buf.getvalue()
    sline = {}
    for l in stext.splitlines():
        if l.startswith("refGap image=district_synth_"):
            sline[l.split()[1].split("=", 1)[1]] = l
    check("rejecting: the synthetic set produces a report (exit 0, 3 lines)",
          scode == 0 and len(sline) == 3)
    if len(sline) == 3:
        bl, bw, md = (sline["district_synth_black"], sline["district_synth_blown"],
                      sline["district_synth_mid"])
        check("rejecting: the black frame IS low-content, on the FLOOR side "
              "(%s)" % bl.split("lowContent=")[1].split()[0],
              "lowContent=none" not in bl
              and "<" in bl.split("lowContent=")[1].split()[0])
        check("rejecting: the blown frame IS low-content, on the CEILING side "
              "(%s)" % bw.split("lowContent=")[1].split()[0],
              "lowContent=none" not in bw
              and ">" in bw.split("lowContent=")[1].split()[0])
        check("accepting: the mid-tone frame is NOT low-content, so the rule "
              "discriminates rather than marking everything",
              "lowContent=none" in md and "ratioUnreadable=none" in md)
        check("rejecting: each qualifying number is printed WITH the bound it "
              "failed", all(":" in l.split("lowContent=")[1].split()[0]
                            for l in (bl, bw)))
        # THE SIDE-AWARENESS, WHICH IS THE POINT OF unreadableOn: a dark frame
        # loses both ratio rows; a BLOWN one keeps groundOverFrame, because on
        # that side groundOverFrame is not degenerate — it is the finding.
        check("rejecting: the black frame loses BOTH ratio rows (%s)"
              % bl.split("ratioUnreadable=")[1].split()[0],
              bl.split("ratioUnreadable=")[1].split()[0]
              == ",".join(sorted(RATIO_DIMS)))
        check("rejecting: the blown frame loses shadowRatio and KEEPS "
              "groundOverFrame — the row that says it is blown (%s)"
              % bw.split("ratioUnreadable=")[1].split()[0],
              bw.split("ratioUnreadable=")[1].split()[0] == "shadowRatio")
        check("rejecting: ANNOTATED, NOT DROPPED — both rows still carry their "
              "values on the blown frame",
              "shadowRatio=" in bw and "groundOverFrame=" in bw)
        ssum = stext.split("refGap scope=summary")[1]
        check("rejecting: the summary counts the two halves apart (floor 1, "
              "ceiling 1 of 3)",
              "lowContentFloorStills=1" in ssum and "lowContentCeilStills=1" in ssum
              and "lowContentStills=2/3" in ssum)

    # The bounds are DERIVED, not stored: recompute them here from the
    # references and require the printed ones to match, so a constant creeping
    # in fails.
    rb_line = next((l for l in text.splitlines()
                    if l.startswith("refGap scope=ratioband")), "")
    want_floor = "/".join("%s:%s" % (k, FMTS[k] % lranges[k][0])
                          for k in LOW_CONTENT_FLOOR_KEYS)
    want_ceil = "/".join("%s:%s" % (k, FMTS[k] % lranges[k][1])
                         for k in LOW_CONTENT_CEIL_KEYS)
    check("accepting: the printed floor is the references' own minimum (%s)"
          % want_floor, ("floor=" + want_floor) in rb_line)
    check("accepting: the printed ceiling is the references' own maximum (%s)"
          % want_ceil, ("ceiling=" + want_ceil) in rb_line)
    got = dict(t.split("=", 1) for t in rb_line.split()[1:] if "=" in t)
    check("accepting: the ratio-band line ships every denominator",
          all(k in got for k in ("inBand", "readable", "unreadableRatio",
                                 "stills", "namesShown", "namesNotShown",
                                 "unreadableOn")))
    if got:
        check("accepting: readable + unreadable = stills examined (%s+%s=%s)"
              % (got.get("readable"), got.get("unreadableRatio"), got.get("stills")),
              int(got["readable"]) + int(got["unreadableRatio"]) == int(got["stills"]))
        check("accepting: in band is counted out of READABLE, never out of all",
              int(got["inBand"]) <= int(got["readable"]))
        check("accepting: the names shown carry their not-shown count",
              int(got["namesShown"]) + int(got["namesNotShown"])
              == int(got["unreadableRatio"]))
    check("accepting: one ratioband line per ratio row (%d of %d)"
          % (sum(1 for l in text.splitlines()
                 if l.startswith("refGap scope=ratioband")), len(RATIO_DIMS)),
          sum(1 for l in text.splitlines()
              if l.startswith("refGap scope=ratioband")) == len(RATIO_DIMS))
    check("accepting: every ratio row declares a side it is degenerate under",
          all(spec["unreadableOn"]
              and set(spec["unreadableOn"]) <= {"floor", "ceiling"}
              for spec in RATIO_DIMS.values()))
    # The table's marks and the machine tail's counts are three renderings of
    # one judgement, the same pairing the `!` check above exists for. It is a
    # SUM over rows now, not stills x rows: the two rows have different
    # unreadable counts in the same run, on purpose.
    marks = sum(l.count("~") for l in text.splitlines() if l.startswith(labels))
    per_dim = sum(int(l.split("unreadableRatio=")[1].split()[0])
                  for l in text.splitlines()
                  if l.startswith("refGap scope=ratioband"))
    summary_readings = int(text.split("refGap scope=summary")[1]
                           .split("unreadableRatioReadings=")[1].split()[0])
    check("accepting: table ~ marks, the ratioband lines and the summary agree "
          "(%d marks, %d over rows, %d summary)"
          % (marks, per_dim, summary_readings),
          marks == per_dim == summary_readings)
    summary_low = text.split("refGap scope=summary")[1].split(
        "lowContentStills=")[1].split()[0]
    sfloor = int(text.split("refGap scope=summary")[1]
                 .split("lowContentFloorStills=")[1].split()[0])
    sceil = int(text.split("refGap scope=summary")[1]
                .split("lowContentCeilStills=")[1].split()[0])
    check("accepting: the two halves are counted apart and neither exceeds the "
          "whole (%d floor, %d ceiling, %s low-content)"
          % (sfloor, sceil, summary_low),
          max(sfloor, sceil) <= int(summary_low.split("/")[0])
          <= sfloor + sceil <= 2 * int(summary_low.split("/")[1]))

    # PLANTED, so none of this waits on the live stills to land on an edge.
    check("floor: a value rounding ONTO the floor is not below it",
          not below_floor(0.23274, 0.23251, "%.3f"))
    check("floor: a value a printed step below the floor IS below it",
          below_floor(0.23274, 0.23249, "%.3f"))
    check("ceiling: a value rounding ONTO the ceiling is not above it",
          not above_ceiling(0.54321, 0.54349, "%.3f"))
    check("ceiling: a value a printed step above the ceiling IS above it",
          above_ceiling(0.54321, 0.54351, "%.3f"))
    PLANT = {"groundP90": (0.233, 0.831), "groundMean": (0.142, 0.543),
             "lumaMean": (0.366, 0.577)}
    check("floor: the qualifier moves when the references move — one value, "
          "two floors",
          bool(low_content_of({"groundP90": 0.200, "groundMean": 0.500},
                              PLANT, FMTS))
          and not low_content_of({"groundP90": 0.200, "groundMean": 0.500},
                                 {"groundP90": (0.150, 0.831),
                                  "groundMean": (0.142, 0.543)}, FMTS))
    check("floor: EITHER input below its own floor qualifies (the day5_night "
          "shape: a lit lamp over an unlit band)",
          len(low_content_of({"groundP90": 0.525, "groundMean": 0.132},
                             PLANT, FMTS)) == 1)
    # THE CEILING'S OWN ASYMMETRY, PLANTED — this is the check that would have
    # caught a symmetric ceiling eating district_hook and district_strip.
    check("ceiling: the MEAN above its ceiling qualifies (the ironside shape: "
          "a blown white sheet)",
          [side for _k, _v, _b, side in
           low_content_of({"groundP90": 0.890, "groundMean": 0.726},
                          PLANT, FMTS)] == ["ceiling"])
    check("ceiling: a PERCENTILE above its ceiling over a mid-band mean does "
          "NOT qualify (the hook shape: a highlight, not a blowout)",
          not low_content_of({"groundP90": 0.900, "groundMean": 0.470},
                             PLANT, FMTS))
    check("sides: the token carries < for a floor and > for a ceiling",
          low_content_token(low_content_of({"groundP90": 0.100,
                                            "groundMean": 0.100}, PLANT, FMTS),
                            FMTS) == "groundP90:0.100<0.233,groundMean:0.100<0.142"
          and low_content_token(low_content_of({"groundP90": 0.890,
                                                "groundMean": 0.726},
                                               PLANT, FMTS), FMTS)
          == "groundMean:0.726>0.543")
    check("sides: a floor frame loses both ratio rows, a ceiling frame keeps "
          "groundOverFrame",
          unreadable_dims(low_content_of({"groundP90": 0.100,
                                          "groundMean": 0.100}, PLANT, FMTS))
          == sorted(RATIO_DIMS)
          and unreadable_dims(low_content_of({"groundP90": 0.890,
                                              "groundMean": 0.726},
                                             PLANT, FMTS)) == ["shadowRatio"])
    check("sides: a frame inside every bound loses nothing",
          unreadable_dims(low_content_of({"groundP90": 0.500,
                                          "groundMean": 0.300},
                                         PLANT, FMTS)) == [])
    # A run in which EVERY still is low-content must not print a clean-looking
    # "0 in band" — rule 3b, planted rather than waited for.
    dark = [("all_dark_%d" % i, {"groundP90": 0.05, "groundMean": 0.02,
                                 "shadowRatio": 0.9, "groundOverFrame": 1.1,
                                 "lumaMean": 0.02}) for i in range(3)]
    darkb = ratio_band_reading("shadowRatio", dark,
                               dict(PLANT, shadowRatio=(0.157, 0.388),
                                    groundOverFrame=(0.387, 0.981)), FMTS)
    check("nothing measured: 0 readable stills reports 0 of 0 with every one "
          "named unreadable",
          darkb["readable"] == 0 and darkb["inBand"] == []
          and len(darkb["unreadable"]) == 3 and darkb["stills"] == 3)
    check("cap: a name list past the cap announces the truncation",
          capped(["s%d" % i for i in range(12)]).endswith("(+4more-not-shown)"))
    check("cap: a list inside the cap says nothing about truncation",
          "not-shown" not in capped(["s%d" % i for i in range(NAME_CAP)]))
    check("cap: an empty name list prints the word none, never blank",
          capped([]) == "none")

    ranges_ok = True
    for line in text.splitlines():
        if line.startswith("refGap image=REFBAND"):
            for tok in line.split()[2:]:
                _k, _, v = tok.partition("=")
                if ".." in v:
                    a, b = v.split("..")
                    ranges_ok = ranges_ok and float(a) <= float(b)
    check("accepting: every reference range has lo <= hi", ranges_ok)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = report(stable_only=True)
    stxt = buf.getvalue()
    check("accepting: --stable also produces a table", code == 0)
    check("accepting: --stable keeps only district_*",
          "review_day1_noon.jpg" not in stxt and "district_hook.jpg" in stxt)

    # ---- 2. REJECTING: a directory that is not there.
    keep_ref, keep_sim = REFDIR, SIMDIR
    REFDIR = ROOT / "game-design" / "no-such-reference-dir"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = report()
    REFDIR = keep_ref
    check("rejecting: a missing reference directory exits 3", code == 3)
    check("rejecting: it names the directory",
          "no-such-reference-dir" in buf.getvalue())
    check("rejecting: it says NOTHING MEASURED", "NOTHING MEASURED" in buf.getvalue())

    # ---- 3. REJECTING: a directory that exists and holds no image. The zero
    # ships its denominator, or "nothing here" reads like "this is fine".
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="refbench-"))
    atexit.register(shutil.rmtree, tmp, True)
    (tmp / "notes.txt").write_text("not an image\n", encoding="utf-8")
    (tmp / "more.txt").write_text("nor this\n", encoding="utf-8")
    REFDIR = tmp
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = report()
    REFDIR = keep_ref
    check("rejecting: an empty directory exits 3", code == 3)
    check("rejecting: the zero ships its denominator",
          "2 files examined" in buf.getvalue())

    # ---- 4. REJECTING: an image that will not decode is REPORTED, not dropped.
    src = sorted(p for p in SIMDIR.iterdir()
                 if p.name.startswith("district_") and p.suffix == ".jpg")
    check("rejecting: a district still exists to truncate", bool(src))
    if src:
        simtmp = pathlib.Path(tempfile.mkdtemp(prefix="refbench-sim-"))
        atexit.register(shutil.rmtree, simtmp, True)
        for p in src[:2]:
            shutil.copy2(p, simtmp / p.name)
        blob = src[0].read_bytes()
        (simtmp / "district_truncated.jpg").write_bytes(blob[:len(blob) // 3])
        SIMDIR = simtmp
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = report()
        SIMDIR = keep_sim
        txt = buf.getvalue()
        check("rejecting: a truncated image exits 4, not 0", code == 4)
        check("rejecting: the truncated image is named",
              "district_truncated.jpg" in txt)
        # the denominator spans BOTH directories — 2 good stills, 1 truncated,
        # plus every reference frame the same run opened
        n_refs = len(images_in(REFDIR)[0])
        check("rejecting: it is counted against a denominator",
              ("unreadable images: 1 of %d files opened" % (n_refs + 3)) in txt)
        check("rejecting: the readable stills still reported",
              "block 1 of " in txt)

    # ---- 4b. THE CACHE'S REJECTING CASE. gather() memoises on (path, mtime,
    # size); a memo that survives the file changing under it would hand back
    # last build's numbers for this build's still, silently, which is the exact
    # shape of fault this whole tool exists to refuse.
    if src:
        cachetmp = pathlib.Path(tempfile.mkdtemp(prefix="refbench-cache-"))
        atexit.register(shutil.rmtree, cachetmp, True)
        target = cachetmp / "district_swap.jpg"
        shutil.copy2(src[0], target)
        SIMDIR = cachetmp
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            report()
        first = [l for l in buf.getvalue().splitlines()
                 if l.startswith("refGap image=district_swap")]
        other = next(p for p in src[1:]
                     if p.read_bytes() != src[0].read_bytes())
        shutil.copy2(other, target)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            report()
        second = [l for l in buf.getvalue().splitlines()
                  if l.startswith("refGap image=district_swap")]
        SIMDIR = keep_sim
        check("cache: a still replaced under the same name is re-measured",
              bool(first) and bool(second) and first != second)

    # ---- 5. The instrument's own arithmetic, on shapes with a known answer.
    np = _np()
    from PIL import Image
    h, w = WORK[1], WORK[0]
    m = measure(Image.new("RGB", WORK, (0, 0, 0)))
    check("flat black: luma mean is 0", m["lumaMean"] < 1e-6)
    check("flat black: edge density 0 against a real denominator",
          m["edgeGround"] == 0.0 and m["_pxGround"] > 100000)
    check("flat black: no vertical runs", m["vertRuns"] == 0)
    check("flat black: grain sigma is 0 over a counted band",
          m["grainSigma"] == 0.0 and m["_pxGrain"] > 100000)
    check("flat black: patch spread 0 over counted windows",
          m["groundPatch"] == 0.0 and m["_nPatch"] > 100)
    check("flat black: shadow ratio cannot divide by zero", m["shadowRatio"] == 0.0)
    check("flat black: ground/frame cannot divide by zero",
          m["groundOverFrame"] == 0.0)

    # ---- 5b. GROUND OVER FRAME's two load-bearing properties, on shapes with
    # a known answer. A sign error here inverts the whole ground diagnosis, and
    # the exposure-independence claim is the reason this row exists at all.
    flat = measure(Image.new("RGB", WORK, (128, 128, 128)))
    check("uniform frame: ground/frame is exactly 1 (%0.6f)"
          % flat["groundOverFrame"], abs(flat["groundOverFrame"] - 1.0) < 1e-6)
    split = np.full((h, w, 3), 120, dtype=np.uint8)
    split[int(GROUND_Y[0] * h):int(GROUND_Y[1] * h), :, :] = 60
    dark_ground = measure(Image.fromarray(split, "RGB"))
    split2 = np.full((h, w, 3), 60, dtype=np.uint8)
    split2[int(GROUND_Y[0] * h):int(GROUND_Y[1] * h), :, :] = 120
    light_ground = measure(Image.fromarray(split2, "RGB"))
    check("direction: a DARKER ground than its frame reads below 1 (%.3f) and "
          "a brighter one above 1 (%.3f)"
          % (dark_ground["groundOverFrame"], light_ground["groundOverFrame"]),
          dark_ground["groundOverFrame"] < 1.0 < light_ground["groundOverFrame"])
    # EXPOSURE INDEPENDENCE, the claim the docstring makes: halve every pixel
    # (exactly, on even values) and the ratio must not move while lumaMean does.
    halved = measure(Image.fromarray(split // 2, "RGB"))
    check("exposure independence: halving every pixel moves lumaMean %.3f->%.3f "
          "and leaves ground/frame %.6f->%.6f"
          % (dark_ground["lumaMean"], halved["lumaMean"],
             dark_ground["groundOverFrame"], halved["groundOverFrame"]),
          abs(halved["lumaMean"] - dark_ground["lumaMean"] / 2.0) < 1e-3
          and abs(halved["groundOverFrame"]
                  - dark_ground["groundOverFrame"]) < 1e-6)

    bars = np.zeros((h, w, 3), dtype=np.uint8)
    for x in range(0, w, 40):
        bars[:, x:x + 4] = 255
    m = measure(Image.fromarray(bars, "RGB"))
    # 1280/40 = 32 stripes, minus those the border and HUD rectangles remove.
    # The assertion is that the detector counts POLES and not COLUMNS: counting
    # columns would give ~4 per stripe.
    check("bar chart: vertical runs counts stripes, not columns",
          20 <= m["vertRuns"] <= 34)
    check("bar chart: edge density is not saturated", 0.0 < m["edgeMid"] < 0.5)

    grad = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        grad[y, :, :] = int(255 * y / (h - 1))
    m = measure(Image.fromarray(grad, "RGB"))
    check("vertical gradient: no vertical runs (it has no vertical edges)",
          m["vertRuns"] == 0)
    check("vertical gradient: p10 below p90", m["groundP10"] < m["groundP90"])
    check("vertical gradient: grain sigma stays near zero on smooth ramp",
          m["grainSigma"] < 0.5)

    # THE CASE THE WHOLE TOOL TURNS ON: pure noise on a dark field must read
    # dense to the edge metric and flat to the patch metric. If these two ever
    # agree here, the grain caveat in the docstring has stopped being true.
    rng = np.random.default_rng(7)
    noise = np.clip(rng.normal(18, 6, (h, w, 1)), 0, 255).astype(np.uint8)
    m = measure(Image.fromarray(np.repeat(noise, 3, axis=2), "RGB"))
    check("pure grain: edge density reads dense", m["edgeGround"] > 0.30)
    check("pure grain: grain sigma catches it", m["grainSigma"] > 4.0)
    check("pure grain: GROUND PATCH is not fooled", m["groundPatch"] < 0.08)

    # ---- 6. The mask is really applied, and to both sides.
    mask = valid_mask(np, h, w)
    check("mask: the minimap corner is excluded",
          not mask[int(0.95 * h), int(0.05 * w)])
    check("mask: the stars corner is excluded",
          not mask[int(0.02 * h), int(0.95 * w)])
    check("mask: the middle of the road is kept",
          bool(mask[int(0.80 * h), int(0.50 * w)]))
    check("mask: the border is dropped", not mask[0, 0] and not mask[h - 1, w - 1])

    # ---- 7. The helpers that read the project's own files.
    check("frames.tsv parses to shot rows", len(shot_rows()) > 5)
    check("shot names strip review_ and keep district_",
          shot_name(pathlib.Path("review_day1_noon.jpg")) == "day1_noon"
          and shot_name(pathlib.Path("district_hook.jpg")) == "district_hook")
    check("spearman is +1 on a monotone pair",
          abs(spearman([1, 2, 3, 4], [10, 20, 30, 40]) - 1.0) < 1e-9)
    check("spearman refuses fewer than three points",
          math.isnan(spearman([1, 2], [2, 1])))

    print("ref-bench selftest: %d passed, %d failed" % (ok, len(fails)))
    for f in fails:
        print("  FAILED " + f)
    return 1 if fails else 0


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest()
    if "--series" in args:
        return series()
    unknown = [a for a in args if a != "--stable"]
    if unknown:
        print("usage: ref-bench.py [--stable | --series | --selftest]")
        print("  unknown argument(s): %s" % " ".join(unknown))
        return 2
    return report(stable_only="--stable" in args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:             # `| head` must not end in a traceback
        try:
            sys.stdout.close()
        finally:
            sys.exit(0)
