#!/usr/bin/env python3
"""WHY DOES THE NEAR ROAD RENDER AS A PALE, NEARLY WHITE FIELD?

WHY THIS EXISTS. production/queue/176 records, BY EYE AND BY NOTHING ELSE,
that in ue-walk_05_grate_a.png and ue-walk_06_grate_b.png the band carrying
the drainage grate renders as a flat pale field while the carriageway further
off in the SAME frame renders as textured grey with red aggregate. CLAUDE.md
rule 4 governs the order: a picture is strong evidence that something is wrong
and weak evidence of WHAT, so the quantity is printed before a material, a
light or an exposure value is touched.

THE FOUR CANDIDATES THE QUEUE NAMES, and what each one does to a frame:

  EXPOSURE / TONE CURVE. A global, monotone, per-pixel function. It can lift
  or compress every surface at once. IT CANNOT, BY ITSELF, CREATE A
  DIFFERENCE BETWEEN TWO SURFACES IN ONE FRAME: it can only amplify a
  difference that already exists upstream of it. So a subject-versus-control
  difference inside one frame is evidence about what is UPSTREAM of the tone
  curve, never about the curve. What this tool can still say about the curve
  is where the histogram sits and how much of the frame is clipped, and it
  prints both.

  MATERIAL ALBEDO. Multiplies the subject band's radiance only.

  LIGHTING. Also multiplies the subject band's radiance only, if the light
  falls differently there.

  THESE TWO ARE NOT SEPARABLE FROM ONE FRAME AND THIS TOOL SAYS SO IN ITS
  OWN OUTPUT. Both are multiplicative on the same pixels and both preserve
  the coefficient of variation. The run that separates them is an A/B with
  the SAME camera and the SAME frame counts and one light switched off: if
  the subject's mean falls in the same proportion as the control's, the
  light owns it; if the subject stays bright relative to the control, the
  material does. VignetteShot.cpp already takes exactly that pair for its
  lantern lines, so the separating run is an existing entry point aimed at
  this rectangle, not a new mechanism.

  A MISSING SURFACE, meaning a piece whose base colour map never bound. That
  one IS separable here, because an unbound map has no texture in it: the
  band's spatial variation collapses relative to the control's. Both halves
  are printed, cv and distinct colour buckets, and the control in the same
  frame is the denominator for both.

AND THE HALF THAT DOES SEPARATE ALBEDO FROM LIGHTING WITHOUT A SECOND RUN:
pass the two bands' SOURCE base colour files with --subject-albedo and
--control-albedo. The source pair predicts what the rendered pair should look
like under one light: if the rendered ratio is NO LARGER than the source
ratio, the subject's own albedo already accounts for the whole difference and
no extra multiplier has to be invoked to explain the frame. If the rendered
ratio EXCEEDS the source ratio, something beyond albedo is amplifying and
lighting stays live. That is a logical statement about two measured ratios,
not a level chosen in advance, and its limit is stated in the output: it
cannot see a lighting difference whose factor happens to be one.

WHAT IS A STATISTIC OF WHAT. Every band number is over the PIXELS EXAMINED in
that band in ONE frame, printed on that frame's own sample line; the done line
carries the cumulative pixel count and the mean of the per-frame means, and
says which it is. Luma is (299R+587G+114B)/1000 over 0..255, the same weights
the probe's own shotMeanLuma uses, reported 0..1.

NO BOUND IS SET HERE. The only comparison made is a separation ratio whose
denominator is the two bands' OWN within-band spread (p95 minus p05) measured
in the same frame, so "the bands differ by more than they wobble" is a
statement about measured quantities and not a number chosen in advance. The
series behind every summary is printed.

Pillow only, which is this repository's frame reader, and the same dependency
tools/grate-zfight.py takes.

  python3 tools/road-brightness.py \
      --frames production/d1-probe/ue-walk_05_grate_a.png \
               production/d1-probe/ue-walk_06_grate_b.png \
      --subject 0.000/0.463/0.365/0.685 --control 0.000/0.111/0.365/0.333 \
      --subject-is near-band-that-carries-the-grate \
      --control-is carriageway-further-off-in-the-same-frame
  python3 tools/road-brightness.py --selftest
"""

import argparse
import os
import shutil
import sys
import tempfile

from PIL import Image

# THE ROW PROFILE'S RESOLUTION. Not a bound: it is how finely the frame is
# sliced from top to bottom so that a STEP at a geometry edge can be told from
# a RAMP across a lit surface. 18 bands over a 540 row frame is 30 rows each.
DEFAULT_ROW_BANDS = 18

# THE ONLY COMPARISON THIS TOOL MAKES, and it is a ratio to a measured
# quantity rather than a chosen level: two bands are called SEPARATED when
# the gap between their means is wider than their own average p95-p05 spread.
SEPARATION_AT = 1.0


def luma_of(r, g, b):
    return (299 * r + 587 * g + 114 * b) // 1000


class Band(object):
    """One rectangle's readings, over the pixels examined in one frame."""

    def __init__(self, name, rect):
        self.name = name
        self.rect = rect
        self.examined = 0
        self.hist = [0] * 256
        self.sum = 0
        self.sumsq = 0
        self.chroma_sum = 0
        self.buckets = set()
        self.clip_hi_any = 0
        self.clip_lo_all = 0

    def add_image(self, img):
        x0, y0, x1, y1 = self.rect
        if x1 <= x0 or y1 <= y0:
            return
        crop = img.convert("RGB").crop((x0, y0, x1, y1))
        w, h = crop.size
        data = crop.tobytes()
        for i in range(0, w * h * 3, 3):
            r, g, b = data[i], data[i + 1], data[i + 2]
            y = luma_of(r, g, b)
            self.hist[y] += 1
            self.sum += y
            self.sumsq += y * y
            mx = r if r > g else g
            if b > mx:
                mx = b
            mn = r if r < g else g
            if b < mn:
                mn = b
            self.chroma_sum += mx - mn
            self.buckets.add(((r >> 3) << 10) | ((g >> 3) << 5) | (b >> 3))
            if r == 255 or g == 255 or b == 255:
                self.clip_hi_any += 1
            if r == 0 and g == 0 and b == 0:
                self.clip_lo_all += 1
            self.examined += 1

    def pct(self, q):
        """Luma at quantile q, 0..1, off this band's own 256 bin histogram."""
        if self.examined <= 0:
            return 0.0
        want = q * self.examined
        run = 0
        for v in range(256):
            run += self.hist[v]
            if run >= want:
                return v / 255.0
        return 1.0

    def mean(self):
        return (self.sum / float(self.examined)) / 255.0 if self.examined else 0.0

    def std(self):
        if self.examined <= 0:
            return 0.0
        m = self.sum / float(self.examined)
        var = self.sumsq / float(self.examined) - m * m
        if var < 0:
            var = 0.0
        return (var ** 0.5) / 255.0

    def cv(self):
        m = self.mean()
        return self.std() / m if m > 0 else 0.0

    def spread(self):
        return self.pct(0.95) - self.pct(0.05)

    def chroma(self):
        return (self.chroma_sum / float(self.examined)) / 255.0 if self.examined else 0.0

    def line(self, prefix):
        if self.examined <= 0:
            return ("%sBand=%s %sPixelsExamined=0 %sStatus=nothing-measured"
                    % (prefix, self.name, prefix, prefix))
        return ("%sBand=%s %sPixelsExamined=%d %sRectPx=%d/%d/%d/%d "
                "%sMeanLuma=%.4f %sP05=%.4f %sP50=%.4f %sP95=%.4f %sSpread=%.4f "
                "%sStd=%.4f %sCv=%.4f %sBuckets=%d/32768 %sChroma=%.4f "
                "%sClipHiAny=%d %sClipLoAll=%d"
                % (prefix, self.name, prefix, self.examined, prefix,
                   self.rect[0], self.rect[1], self.rect[2], self.rect[3],
                   prefix, self.mean(), prefix, self.pct(0.05), prefix, self.pct(0.50),
                   prefix, self.pct(0.95), prefix, self.spread(),
                   prefix, self.std(), prefix, self.cv(), prefix, len(self.buckets),
                   prefix, self.chroma(), prefix, self.clip_hi_any, prefix,
                   self.clip_lo_all))


def albedo_read(path, step):
    """Mean and quantiles of one source base colour file, sRGB 0..1.

    SAMPLED, AND THE DENOMINATOR SAYS SO. Every `step`th pixel on both axes is
    examined; the count examined and the count skipped are both printed, so a
    reader can see what fraction of the file the number is a statistic of. No
    conversion to linear happens here: the rendered frame this is compared
    against is also an encoded 8 bit file, and the comparison made is between
    two RATIOS taken in the same encoding.
    """
    img = Image.open(path).convert("RGB")
    w, h = img.size
    px = img.load()
    hist = [0] * 256
    tot = 0
    n = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            r, g, b = px[x, y]
            v = luma_of(r, g, b)
            hist[v] += 1
            tot += v
            n += 1

    def q(p):
        want = p * n
        run = 0
        for v in range(256):
            run += hist[v]
            if run >= want:
                return v / 255.0
        return 1.0

    return {
        "path": os.path.basename(path), "w": w, "h": h, "examined": n,
        "of": w * h, "step": step,
        "mean": (tot / float(n)) / 255.0 if n else 0.0,
        "p05": q(0.05), "p50": q(0.50), "p95": q(0.95),
        "spread": q(0.95) - q(0.05),
    }


def albedo_line(tag, a):
    return ("roadAlbedo%s=%s roadAlbedo%sWH=%d/%d roadAlbedo%sMean=%.4f "
            "roadAlbedo%sP05=%.4f roadAlbedo%sP50=%.4f roadAlbedo%sP95=%.4f "
            "roadAlbedo%sSpread=%.4f roadAlbedo%sPixelsExamined=%d/%d "
            "roadAlbedo%sStat=every-%dth-pixel-on-both-axes/sRGB-encoded-as-the-"
            "frame-is/not-linearised"
            % (tag, a["path"], tag, a["w"], a["h"], tag, a["mean"],
               tag, a["p05"], tag, a["p50"], tag, a["p95"], tag, a["spread"],
               tag, a["examined"], a["of"], tag, a["step"]))


def separation(a, b):
    """Gap between two band means over their own average p95-p05 spread.

    THE DENOMINATOR IS MEASURED IN THE SAME FRAME, so this asks "do these two
    bands differ by more than they wobble", which is a comparison of two
    measured quantities. A denominator of zero (two perfectly flat bands that
    still differ) returns the string form's infinity rather than a division
    error, and the caller prints both means beside it either way.
    """
    d = abs(a.mean() - b.mean())
    s = 0.5 * (a.spread() + b.spread())
    if s <= 0:
        return float("inf") if d > 0 else 0.0
    return d / s


def sep_str(v):
    return "inf" if v == float("inf") else "%.2f" % v


def row_profile(img, bands):
    """Mean luma and cv for each of N full-width horizontal bands, top first.

    THE SERIES IS THE EVIDENCE. A material edge shows as a STEP between two
    neighbouring bands; light falling off across a surface shows as a RAMP
    through several. No number here is compared with anything.
    """
    w, h = img.size
    out = []
    for i in range(bands):
        y0 = (i * h) // bands
        y1 = ((i + 1) * h) // bands
        b = Band("row%02d" % i, (0, y0, w, y1))
        b.add_image(img)
        out.append(b)
    return out


def rect_px(frac, w, h):
    x0 = int(round(frac[0] * w))
    y0 = int(round(frac[1] * h))
    x1 = int(round(frac[2] * w))
    y1 = int(round(frac[3] * h))
    x0, x1 = max(0, min(x0, x1)), min(w, max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(h, max(y0, y1))
    return (x0, y0, x1, y1)


def area(rect):
    return max(0, rect[2] - rect[0]) * max(0, rect[3] - rect[1])


def measure(frames, names, subj_frac, ctrl_frac, row_bands,
            subject_is, control_is, subj_albedo=None, ctrl_albedo=None):
    """frames: open PIL images. Returns (lines, status)."""
    out = []
    out.append("roadStat=subject-band-vs-same-area-control-band-in-the-same-frame/"
               "the-control-is-the-denominator/no-bound-is-set-here")
    out.append("roadSubjectIs=%s roadControlIs=%s" % (subject_is, control_is))
    out.append("roadSeparates=exposure-from-upstream/AND/textured-from-untextured "
               "roadCannotSeparate=material-albedo-from-lighting/"
               "both-multiply-the-same-pixels-and-both-preserve-cv/"
               "the-run-that-separates-them-is-the-same-camera-and-frame-counts-"
               "with-one-light-switched-off/VignetteShot.cpp-already-takes-that-pair")
    if not frames:
        out.append("roadStatus=NOTHING-MEASURED roadFrames=0 "
                   "roadReason=no-frame-was-given-to-this-tool")
        out.append("NOTHING MEASURED - nothing measured: no frame reached this "
                   "tool, so this is not a clean result.")
        return out, "NOTHING-MEASURED"

    w, h = frames[0].size
    subj = rect_px(subj_frac, w, h)
    ctrl = rect_px(ctrl_frac, w, h)
    same_area = area(subj) == area(ctrl) and area(subj) > 0
    out.append("roadFrames=%d roadFrameWH=%d/%d roadSubjectRectPx=%d/%d/%d/%d "
               "roadControlRectPx=%d/%d/%d/%d roadAreaMatch=%s roadRectAreaPx=%d/%d"
               % (len(frames), w, h, subj[0], subj[1], subj[2], subj[3],
                  ctrl[0], ctrl[1], ctrl[2], ctrl[3],
                  "yes" if same_area else "no", area(subj), area(ctrl)))
    if not same_area:
        out.append("roadStatus=NOTHING-MEASURED "
                   "roadReason=the-control-is-not-the-same-area-as-the-subject/"
                   "the-control-is-the-denominator-and-a-different-one-answers-nothing")
        out.append("NOTHING MEASURED - nothing measured: the two rectangles "
                   "differ in area.")
        return out, "NOTHING-MEASURED"

    cum_examined = 0
    mean_subj = []
    mean_ctrl = []
    last = None
    for idx, img in enumerate(frames):
        name = names[idx] if idx < len(names) else "frame%02d" % idx
        s = Band("subject", subj)
        c = Band("control", ctrl)
        s.add_image(img)
        c.add_image(img)
        rows = row_profile(img, row_bands)
        darkest = min(rows, key=lambda b: b.mean())
        brightest = max(rows, key=lambda b: b.mean())
        flattest = min(rows, key=lambda b: b.cv())
        out.append("roadFrame=%s roadFrameStat=one-sample-line-per-frame" % name)
        out.append("  " + s.line("road"))
        out.append("  " + c.line("road"))
        out.append("  roadRowBands=%d roadRowBandRows=%d "
                   "roadRowMeanSeries=%s"
                   % (row_bands, h // row_bands,
                      "/".join("r%02d[%.4f]" % (i, b.mean())
                               for i, b in enumerate(rows))))
        out.append("  roadRowCvSeries=%s"
                   % "/".join("r%02d[%.4f]" % (i, b.cv())
                              for i, b in enumerate(rows)))
        out.append("  roadRowDarkest=%s@%.4f roadRowBrightest=%s@%.4f "
                   "roadRowFlattest=%s@cv%.4f roadRowSeriesStat=mean-luma-per-"
                   "full-width-band/top-band-first/a-step-is-a-material-edge-and-"
                   "a-ramp-is-light"
                   % (darkest.name, darkest.mean(), brightest.name,
                      brightest.mean(), flattest.name, flattest.cv()))
        sep_sc = separation(s, c)
        sep_sd = separation(s, darkest)
        cv_ratio = (s.cv() / c.cv()) if c.cv() > 0 else float("inf")
        bucket_ratio = (len(s.buckets) / float(len(c.buckets))) if c.buckets else float("inf")
        mean_ratio = (s.mean() / c.mean()) if c.mean() > 0 else float("inf")
        out.append("  roadSubjectOverControlMean=%s roadSubjectOverControlCv=%s "
                   "roadSubjectOverControlBuckets=%s roadSepSubjectControl=%s "
                   "roadSepSubjectDarkestRow=%s roadSepStat=mean-gap-over-the-two-"
                   "bands-own-average-p95-minus-p05-spread/measured-in-this-frame/"
                   "the-only-comparison-made-is-against-%.1f"
                   % (sep_str(mean_ratio), sep_str(cv_ratio), sep_str(bucket_ratio),
                      sep_str(sep_sc), sep_str(sep_sd), SEPARATION_AT))
        # THE READING, and every clause of it is a comparison between two
        # numbers printed above. Nothing here is a level chosen in advance.
        if sep_sc <= SEPARATION_AT:
            diff = "NO-DIFFERENCE-WIDER-THAN-THE-BANDS-OWN-SPREAD"
        elif s.mean() > c.mean():
            diff = "SUBJECT-BRIGHTER-THAN-CONTROL-BY-MORE-THAN-THEIR-SPREAD"
        else:
            diff = "SUBJECT-DARKER-THAN-CONTROL-BY-MORE-THAN-THEIR-SPREAD"
        if cv_ratio == float("inf") or cv_ratio >= 1.0:
            tex = "SUBJECT-AT-LEAST-AS-TEXTURED-AS-CONTROL"
        else:
            tex = "SUBJECT-FLATTER-THAN-CONTROL"
        out.append("  roadReadingDifference=%s roadReadingTexture=%s "
                   "roadClipNote=subjectClipHiAny=%d-of-%d/controlClipHiAny=%d-of-%d/"
                   "a-band-at-the-top-of-the-range-cannot-say-how-far-past-it-went"
                   % (diff, tex, s.clip_hi_any, s.examined, c.clip_hi_any, c.examined))
        cum_examined += s.examined + c.examined
        mean_subj.append(s.mean())
        mean_ctrl.append(c.mean())
        last = (s, c, darkest, sep_sc, cv_ratio, bucket_ratio, mean_ratio)

    s, c, darkest, sep_sc, cv_ratio, bucket_ratio, mean_ratio = last
    # THE CAUSE, NAMED BY ELIMINATION, and the rule that named it printed
    # beside it. The vocabulary is fixed so a reader cannot mistake one
    # finding for another, and the pair this frame cannot split stays joined
    # in the value rather than being guessed at.
    if sep_sc <= SEPARATION_AT:
        cause = "NO-DIFFERENCE-TO-EXPLAIN"
        rule = "the-two-bands-do-not-differ-by-more-than-their-own-spread"
    elif cv_ratio < 1.0 and bucket_ratio < 1.0:
        cause = "UPSTREAM-OF-THE-TONE-CURVE/MATERIAL-ALBEDO-OR-LIGHTING/" \
                "SUBJECT-IS-ALSO-FLATTER-THAN-THE-CONTROL"
        rule = "a-global-monotone-curve-cannot-make-two-surfaces-differ-in-one-" \
               "frame-it-can-only-amplify-a-difference-upstream-of-it/AND/the-" \
               "subject-carries-less-texture-than-the-control-which-is-what-an-" \
               "unbound-or-near-uniform-base-colour-looks-like"
    else:
        cause = "UPSTREAM-OF-THE-TONE-CURVE/MATERIAL-ALBEDO-OR-LIGHTING"
        rule = "a-global-monotone-curve-cannot-make-two-surfaces-differ-in-one-" \
               "frame-it-can-only-amplify-a-difference-upstream-of-it"
    out.append("roadDone roadFramesRead=%d roadPixelsExaminedCumulative=%d "
               "roadSubjectMeanOfFrameMeans=%.4f roadControlMeanOfFrameMeans=%.4f "
               "roadDoneStat=whole-run-numbers/cumulative-pixels-and-the-mean-of-"
               "the-per-frame-means/never-a-mean-of-means-of-different-sizes"
               % (len(frames), cum_examined,
                  sum(mean_subj) / len(mean_subj), sum(mean_ctrl) / len(mean_ctrl)))
    # THE SOURCE ALBEDO HALF, when the two base colour files were given. It is
    # what turns "albedo or lighting" into one of them, and it prints both
    # ratios so the reader can do the comparison the tool did.
    if subj_albedo is not None and ctrl_albedo is not None:
        out.append(albedo_line("Subject", subj_albedo))
        out.append(albedo_line("Control", ctrl_albedo))
        src_ratio = (subj_albedo["mean"] / ctrl_albedo["mean"]
                     if ctrl_albedo["mean"] > 0 else float("inf"))
        src_spread_ratio = (subj_albedo["spread"] / ctrl_albedo["spread"]
                            if ctrl_albedo["spread"] > 0 else float("inf"))
        rendered_spread_ratio = (s.spread() / c.spread()
                                 if c.spread() > 0 else float("inf"))
        out.append("roadAlbedoSourceRatio=%s roadRenderedRatio=%s "
                   "roadRenderedOverSource=%s roadAlbedoSourceSpreadRatio=%s "
                   "roadRenderedSpreadRatio=%s roadAlbedoRatioStat=subject-over-"
                   "control-in-both-cases/same-encoding-both-sides/a-rendered-"
                   "ratio-no-larger-than-the-source-ratio-needs-no-second-"
                   "multiplier-to-explain-it"
                   % (sep_str(src_ratio), sep_str(mean_ratio),
                      sep_str(mean_ratio / src_ratio if src_ratio not in (0, float("inf"))
                              else float("inf")),
                      sep_str(src_spread_ratio), sep_str(rendered_spread_ratio)))
        if sep_sc > SEPARATION_AT and mean_ratio <= src_ratio:
            cause = "MATERIAL-ALBEDO"
            rule = ("the-subjects-own-base-colour-file-is-paler-than-the-controls-"
                    "by-a-larger-ratio-than-the-rendered-bands-differ-by/so-the-"
                    "material-accounts-for-the-whole-difference-and-no-lighting-"
                    "or-exposure-term-has-to-be-invoked")
            out.append("roadCauseLimit=this-cannot-see-a-lighting-difference-whose-"
                       "factor-is-one/it-shows-only-that-none-is-NEEDED")
        elif sep_sc > SEPARATION_AT:
            cause = "MATERIAL-ALBEDO-PLUS-SOMETHING-ELSE"
            rule = ("the-rendered-bands-differ-by-MORE-than-their-source-base-"
                    "colour-files-do/so-albedo-alone-does-not-account-for-it-and-"
                    "lighting-or-the-curve-is-still-live")
    out.append("roadCause=%s" % cause)
    out.append("roadCauseRule=%s" % rule)
    out.append("roadCauseNotSeparable=material-albedo-vs-lighting/"
               "run-the-same-camera-with-one-light-off-and-read-this-same-rectangle"
               if (subj_albedo is None or ctrl_albedo is None) else
               "roadCauseNotSeparable=none/the-source-albedo-half-was-given")
    out.append("roadStatus=MEASURED")
    return out, "MEASURED"


def parse_rect(text):
    parts = text.replace(",", "/").split("/")
    if len(parts) != 4:
        raise ValueError("a rectangle is four numbers: x0/y0/x1/y1")
    return tuple(float(p) for p in parts)


# ---------------------------------------------------------------- selftest

def _lcg(seed):
    x = seed
    while True:
        x = (1103515245 * x + 12345) % 2147483648
        yield x


def _synthetic(w, h, seed, base=110, texture=40, band=None, band_base=None,
               band_texture=0):
    """A textured grey frame, optionally with one flat pale band planted in it.

    THE TEXTURE IS IN THE WHOLE FRAME so the subject and control rectangles
    are alike by construction, and the only difference the planted case makes
    is the band. A control that was flat would make any subject look flat.
    """
    img = Image.new("RGB", (w, h))
    px = img.load()
    r = _lcg(seed)
    for y in range(h):
        for x in range(w):
            v = base + (next(r) % texture)
            px[x, y] = (v, v, v)
    if band is not None:
        y0, y1 = band
        s = _lcg(seed + 7)
        for y in range(y0, y1):
            for x in range(w):
                v = band_base + (next(s) % band_texture if band_texture else 0)
                px[x, y] = (v, v, v)
    return img


def selftest():
    checks = []

    def check(name, ok):
        checks.append((name, ok))
        print("  %s - %s" % ("ok" if ok else "FAIL", name))

    W, H = 200, 120
    subj_frac = (0.0, 0.55, 1.0, 0.85)
    ctrl_frac = (0.0, 0.10, 1.0, 0.40)

    # THE ACCEPTING CASE FIRST, per rule 5b: one textured frame, subject and
    # control alike, nothing planted. A guard that cannot pass this is a
    # ratchet.
    print("accepting case: subject and control alike, nothing planted")
    a = _synthetic(W, H, seed=11)
    lines, status = measure([a], ["accept"], subj_frac, ctrl_frac, 6,
                            "planted-nothing", "planted-nothing")
    for ln in lines:
        print("    " + ln)
    check("alike bands read MEASURED", status == "MEASURED")
    check("alike bands name no difference to explain",
          any("roadCause=NO-DIFFERENCE-TO-EXPLAIN" in ln for ln in lines))
    check("the accepting case examined pixels and said so",
          any("roadPixelsExaminedCumulative=" in ln
              and "roadPixelsExaminedCumulative=0 " not in ln for ln in lines))

    # THE PLANTED CASE, which is the condition this tool asserts CAN happen:
    # a pale FLAT band where the subject is, the control untouched.
    print("planted case: a pale flat band over the subject, control untouched")
    b = _synthetic(W, H, seed=11, band=(int(H * 0.55), int(H * 0.85)),
                   band_base=218, band_texture=0)
    lines2, status2 = measure([b], ["planted"], subj_frac, ctrl_frac, 6,
                              "planted-pale-flat-band", "untouched-texture")
    for ln in lines2:
        print("    " + ln)
    check("a pale flat subject names a cause upstream of the tone curve",
          any(ln.startswith("roadCause=UPSTREAM-OF-THE-TONE-CURVE") for ln in lines2))
    check("a pale flat subject is read as flatter than the control",
          any("SUBJECT-IS-ALSO-FLATTER-THAN-THE-CONTROL" in ln for ln in lines2))
    check("the planted band separates from the control by more than the spread",
          any("roadReadingDifference=SUBJECT-BRIGHTER-THAN-CONTROL" in ln
              for ln in lines2))

    # A PALE BAND THAT IS STILL TEXTURED. The cause is still upstream, but the
    # flat clause must NOT fire, or the tool cannot tell a bright material
    # from an unbound one.
    #
    # THE FIXTURE SCALES ITS TEXTURE WITH ITS BASE, and the first version of
    # it did not. A brighter material or a brighter light MULTIPLIES the
    # albedo variation as well as the mean, so cv is preserved; a fixture that
    # adds the SAME absolute noise at a higher base has a lower cv for a
    # reason that has nothing to do with texture, and it failed this check by
    # being an unphysical fixture rather than by finding a fault. 110 and 40
    # scaled by 1.636 are 180 and 65, which is the control multiplied and
    # nothing else.
    print("planted case 2: a pale band that keeps its texture")
    c = _synthetic(W, H, seed=11, band=(int(H * 0.55), int(H * 0.85)),
                   band_base=180, band_texture=65)
    lines3, status3 = measure([c], ["planted-textured"], subj_frac, ctrl_frac, 6,
                              "planted-pale-textured-band", "untouched-texture")
    for ln in lines3:
        print("    " + ln)
    check("a pale textured subject still names a cause upstream",
          any(ln.startswith("roadCause=UPSTREAM-OF-THE-TONE-CURVE") for ln in lines3))
    check("a pale textured subject does NOT read as flatter",
          not any("SUBJECT-IS-ALSO-FLATTER-THAN-THE-CONTROL" in ln for ln in lines3))

    # THE SOURCE ALBEDO HALF, ACCEPTING CASE FIRST: a pale flat band whose own
    # base colour file is pale by a WIDER ratio than the rendered bands
    # differ by. Nothing but the material is needed to explain that frame.
    print("albedo accepting case: the source files explain the whole difference")
    tmp = tempfile.mkdtemp(prefix="road-brightness-selftest-")
    pale = os.path.join(tmp, "pale_source.png")
    dark = os.path.join(tmp, "dark_source.png")
    alike = os.path.join(tmp, "alike_source.png")
    _synthetic(64, 64, seed=3, base=200, texture=8).save(pale)
    _synthetic(64, 64, seed=4, base=60, texture=40).save(dark)
    _synthetic(64, 64, seed=5, base=110, texture=40).save(alike)
    sa = albedo_read(pale, 1)
    ca = albedo_read(dark, 1)
    lines6, status6 = measure([b], ["planted"], subj_frac, ctrl_frac, 6,
                              "planted-pale-flat-band", "untouched-texture", sa, ca)
    for ln in lines6:
        print("    " + ln)
    check("a pale source under a pale band names MATERIAL-ALBEDO",
          any(ln == "roadCause=MATERIAL-ALBEDO" for ln in lines6))
    check("the albedo half prints what fraction of each file it examined",
          any("roadAlbedoSubjectPixelsExamined=4096/4096" in ln for ln in lines6))

    # AND THE REJECTING CASE: two source files that are ALIKE under bands that
    # are not. Albedo cannot account for it and the tool must not say it does.
    print("albedo rejecting case: alike sources under bands that differ")
    sa2 = albedo_read(alike, 1)
    ca2 = albedo_read(alike, 1)
    lines7, status7 = measure([b], ["planted"], subj_frac, ctrl_frac, 6,
                              "planted-pale-flat-band", "untouched-texture", sa2, ca2)
    for ln in lines7:
        print("    " + ln)
    check("alike sources under differing bands name something else as well",
          any(ln == "roadCause=MATERIAL-ALBEDO-PLUS-SOMETHING-ELSE" for ln in lines7))
    shutil.rmtree(tmp, ignore_errors=True)

    # NOTHING MEASURED, IN THE WORDS RULE 3b ASKS FOR.
    print("nothing-measured case: no frames at all")
    lines4, status4 = measure([], [], subj_frac, ctrl_frac, 6, "none", "none")
    for ln in lines4:
        print("    " + ln)
    check("no frames reads NOTHING-MEASURED", status4 == "NOTHING-MEASURED")
    check("no frames prints the words nothing measured",
          any("nothing measured" in ln for ln in lines4))

    # A CONTROL OF A DIFFERENT AREA ANSWERS NOTHING.
    print("mismatched case: a control of a different area")
    lines5, status5 = measure([a], ["mismatch"], subj_frac, (0.0, 0.1, 0.5, 0.2),
                              6, "x", "y")
    for ln in lines5:
        print("    " + ln)
    check("a different-area control refuses rather than reporting",
          status5 == "NOTHING-MEASURED")

    failed = sum(1 for _, ok in checks if not ok)
    print("%s: %d of %d check(s) failed"
          % ("PASS" if failed == 0 else "FAIL", failed, len(checks)))
    return 0 if failed == 0 else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frames", nargs="*", default=[])
    ap.add_argument("--subject", help="x0/y0/x1/y1 as fractions of the frame")
    ap.add_argument("--control", help="x0/y0/x1/y1 as fractions of the frame")
    ap.add_argument("--subject-is", default="unnamed",
                    help="what the subject rectangle is standing on, no spaces")
    ap.add_argument("--control-is", default="unnamed",
                    help="what the control rectangle is standing on, no spaces")
    ap.add_argument("--rows", type=int, default=DEFAULT_ROW_BANDS)
    ap.add_argument("--subject-albedo",
                    help="the subject surface's source base colour file")
    ap.add_argument("--control-albedo",
                    help="the control surface's source base colour file")
    ap.add_argument("--albedo-step", type=int, default=4,
                    help="examine every Nth pixel of the source files, on both axes")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if not args.subject or not args.control:
        print("roadStatus=NOTHING-MEASURED "
              "roadReason=no-rectangles/pass---subject-and---control")
        print("NOTHING MEASURED - nothing measured: this tool was given no "
              "rectangle.")
        return 2

    imgs = []
    names = []
    missing = 0
    for p in args.frames:
        if os.path.exists(p):
            imgs.append(Image.open(p))
            names.append(os.path.basename(p))
        else:
            missing += 1
    print("roadFramesGiven=%d roadFramesMissing=%d roadFramesRead=%d"
          % (len(args.frames), missing, len(imgs)))
    sa = ca = None
    if args.subject_albedo and args.control_albedo:
        missing_alb = [p for p in (args.subject_albedo, args.control_albedo)
                       if not os.path.exists(p)]
        if missing_alb:
            print("roadAlbedoStatus=NOTHING-MEASURED roadAlbedoMissing=%d/2 "
                  "roadAlbedoReason=a-named-source-file-is-not-on-disk"
                  % len(missing_alb))
        else:
            sa = albedo_read(args.subject_albedo, args.albedo_step)
            ca = albedo_read(args.control_albedo, args.albedo_step)
    elif args.subject_albedo or args.control_albedo:
        print("roadAlbedoStatus=NOTHING-MEASURED "
              "roadAlbedoReason=one-source-file-without-the-other-answers-nothing/"
              "the-control-is-the-denominator-here-too")
    lines, status = measure(imgs, names, parse_rect(args.subject),
                            parse_rect(args.control), args.rows,
                            args.subject_is, args.control_is, sa, ca)
    for ln in lines:
        print(ln)
    return 0 if status == "MEASURED" else 3


if __name__ == "__main__":
    sys.exit(main())
