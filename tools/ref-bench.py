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
 6. VERTICAL RUNS — connected near-vertical edge components taller than 8% of
    the frame in the upper two thirds. Poles and WIRES, rank 2 of the §2
    decomposition, and what §3 says every avenue in this game lacks by design.
    A COUNT, not a peak: it answers "how many uprights", never "how tall".
 7. SHADOW CONTRAST — ground-band p10/p90. §7 item 1 says GTA noons read a
    shadowed:lit ratio near 0.45..0.55 and the eye segments at about 2:1; this
    is that ratio off the pixels rather than off our tonemap constants. A PROXY:
    a dark shop recess and a cast shadow are the same pixels to it.

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
    ("edgeGround",  "edge density GROUND",  "%.3f", "fraction of ground band"),
    ("edgeMid",     "edge density MID",    "%.3f", "fraction of mid band"),
    ("grainSigma",  "grain sigma",         "%.2f", "Immerkaer, ground band"),
    ("vertRuns",    "vertical runs",       "%.0f", "count, upper two thirds"),
    ("shadowRatio", "shadow contrast",     "%.3f", "groundP10/groundP90"),
]


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
    with nothing in it dividing a small number by a smaller one."""
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
    out = {
        "lumaMean": float(whole.mean()),
        "lumaP10": float(p(whole, 10)),
        "lumaP50": float(p(whole, 50)),
        "lumaP90": float(p(whole, 90)),
        "groundMean": float(gvals.mean()),
        "groundP10": gp10,
        "groundP50": float(p(gvals, 50)),
        "groundP90": gp90,
        "satMean": float(svals.mean()),
        "satAbove50": float((svals > 0.5).mean()),
        "groundPatch": patch,
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
    flo, fhi, got = (float(fmt % x) for x in (lo, hi, v))
    return got < flo or got > fhi


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
    out("  * = pose-stable across builds (district_*). Every other sim column is "
        "a different photograph each run.")
    out("")

    cols = [(col_label(p), "*" if p.name.startswith(STABLE_PREFIX) else "", m)
            for p, m in sims]

    def is_outside(key, fmt, v):
        """`outside_of` against this key's reference range. The table, the
        machine tail's `outside=` list and the summary count all go through
        here, so the three renderings of one judgement cannot disagree."""
        return outside_of(ranges[key][0], ranges[key][1], v, fmt)
    ranges = {k: (min(m[k] for _p, m in refs), max(m[k] for _p, m in refs))
              for k, _l, _f, _s in DIMS}

    nblocks = (len(cols) + COLS_PER_BLOCK - 1) // COLS_PER_BLOCK
    for bi in range(nblocks):
        chunk = cols[bi * COLS_PER_BLOCK:(bi + 1) * COLS_PER_BLOCK]
        head = "%-22s %-15s" % ("dimension", "ref lo..hi")
        for name, star, _m in chunk:
            head += "%12s" % (name[:10] + star)
        out("  block %d of %d — sim stills %d-%d of %d"
            % (bi + 1, nblocks, bi * COLS_PER_BLOCK + 1,
               bi * COLS_PER_BLOCK + len(chunk), len(cols)))
        out(head)
        out("  " + "-" * (len(head) - 2))
        for key, label, fmt, _stat in DIMS:
            lo, hi = ranges[key]
            row = "%-22s %-15s" % (label, (fmt + ".." + fmt) % (lo, hi))
            for _n, _s, m in chunk:
                v = m[key]
                row += "%11s%s" % (fmt % v, "!" if is_outside(key, fmt, v) else " ")
            out(row)
        out("")

    outside = checked = 0
    for _n, _s, m in cols:
        for key, _l, fmt, _st in DIMS:
            checked += 1
            outside += 1 if is_outside(key, fmt, m[key]) else 0
    out("  ! = outside the five references' range. %d of %d readings outside "
        "(%d dimensions x %d stills)." % (outside, checked, len(DIMS), len(cols)))
    nstable = sum(1 for _n, st, _m in cols if st == "*")
    out("  %d of %d sim stills are pose-stable%s."
        % (nstable, len(cols),
           "" if stable_only else "; --stable keeps only those"))
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
    for p, m in sims:
        bad = [k for k, _l, f, _s in DIMS if is_outside(k, f, m[k])]
        out("refGap image=%s stable=%s %s outside=%s px=%d/%d/%d patchWindows=%d"
            % (shot_name(p), "yes" if p.name.startswith(STABLE_PREFIX) else "no",
               " ".join("%s=%s" % (k, f % m[k]) for k, _l, f, _s in DIMS),
               ",".join(bad) if bad else "none",
               m["_pxWhole"], m["_pxGround"], m["_pxMid"], m["_nPatch"]))
    out("refGap scope=summary refFrames=%d simStills=%d dims=%d outside=%d outsideOf=%d "
        "unreadable=%d filesExamined=%d/%d edgeCut=%d vertCut=%d "
        "patchBlock=%d patchWin=%d work=%dx%d"
        % (len(refs), len(sims), len(DIMS), outside, checked, len(errors),
           counts["refFiles"], counts["simFiles"], EDGE_T, VERT_T,
           PATCH_BLOCK, PATCH_WIN, WORK[0], WORK[1]))

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
    print("unreadable images: %d of %d files opened"
          % (len(errors), len(refs) + len(sims) + len(errors)))
    for e in errors:
        print("  UNREADABLE %s" % e)
    return 4 if errors else 0


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
