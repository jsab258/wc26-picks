#!/usr/bin/env python3
"""Does the drainage grate's top face TIE with the road it is flush with?

WHY THIS EXISTS. prop_drainage_grate_01_0 was raised flush on 2026-09-09 and
run 34 measured it placed, collidable and at the surface (propFullyBuried=0/23,
propBurialSubject=.../via=loaded-asset/collision=YES/topM=-0.0650). Its top
face is now EXACTLY COINCIDENT with the channel and carriageway top faces over
about 0.16 square metres of rendered solid, and nothing in this repository
could say whether that ties in the depth test. A tie is not a number the engine
prints; it is something a frame shows, so this reads the frames.

THE INSTRUMENT, AS RULED. A rectangle over the grate is compared against a
SAME-AREA CONTROL RECTANGLE on plain carriageway IN THE SAME FRAME, on two
statistics: speckle density (isolated pixels that disagree with their
neighbours, which is what a depth tie looks like standing still) and
frame-to-frame flicker density (pixels that change between two frames of a
camera that did not move, which is what a depth tie looks like under any
temporal jitter the renderer applies). THE CONTROL IS THE DENOMINATOR: no new
bound is set here. If subject and control read alike there is no tie. If the
subject speckles and the control does not, there is.

WHERE THE TWO RECTANGLES COME FROM. WalkProbe.cpp aims one camera at the piece
from the pavement side, photographs it TWICE without moving (ue-walk_05_grate_a
.png and ue-walk_06_grate_b.png), and prints both rectangles as FRACTIONS of
the frame on its grateRect line, because the capture path has two candidates
that need not write the same pixel size. This tool multiplies those fractions
by each image's own width and height.

WHAT IS A STATISTIC OF WHAT. Every density below is a FRACTION OF PIXELS
EXAMINED, cumulative over the frames given, at a stated luma contrast, and the
count examined is printed beside it. The contrasts are a printed SERIES (8, 16,
32 of 255) rather than one number chosen in advance, per rule 2: the series is
the evidence and the status line is a coarse first-cut over it, which says so
in its own value.

Pillow only, which is already this repository's frame reader (see
tools/clip-from-frames.py for the license-allowlist reasoning: that file scopes
itself to model weights, not to a Python utility reading this project's own
render output).

  python3 tools/grate-zfight.py --verdict production/d1-probe/ue-walk-verdict.txt
  python3 tools/grate-zfight.py --frames a.png b.png \
      --subject 0.41/0.55/0.58/0.76 --control 0.41/0.22/0.58/0.43
  python3 tools/grate-zfight.py --selftest
"""

import argparse
import os
import sys

from PIL import Image

# THE PRINTED SERIES, NOT A CHOSEN NUMBER. Luma steps out of 255. c8 is near
# the compression floor and c32 is a difference no viewer would call noise.
CONTRASTS = (8, 16, 32)

# THE COARSE FIRST-CUT, AND IT SAYS SO IN THE OUTPUT. Not a bound read off a
# series of real runs, because this instrument has never run against a real
# frame before this commit. Both halves must hold: the subject at least this
# many times the control AND at least this many more pixels than the control,
# so a three-pixel difference in a small rectangle can never read as a tie.
FIRST_CUT_RATIO = 4.0
FIRST_CUT_FLOOR_PX = 8
DECIDE_AT = 32


def luma_rows(img, rect):
    """Integer luma rows for one rectangle. Rect is (x0, y0, x1, y1) in px."""
    x0, y0, x1, y1 = rect
    crop = img.convert("RGB").crop((x0, y0, x1, y1))
    w, h = crop.size
    # tobytes RATHER THAN getdata: three bytes per pixel, the same in every
    # Pillow this project might meet, and getdata is deprecated from Pillow 14.
    data = crop.tobytes()
    rows = []
    for r in range(h):
        base = r * w * 3
        rows.append([(299 * data[i] + 587 * data[i + 1] + 114 * data[i + 2]) // 1000
                     for i in range(base, base + w * 3, 3)])
    return rows


def speckle_counts(rows):
    """Pixels disagreeing with the median of their 8 neighbours, per contrast.

    Returns (counts_by_contrast, examined). EXAMINED IS THE INTERIOR ONLY:
    a border pixel has no eight neighbours, so it is not examined and is not
    counted in the denominator either.
    """
    h = len(rows)
    w = len(rows[0]) if h else 0
    counts = dict((c, 0) for c in CONTRASTS)
    if h < 3 or w < 3:
        return counts, 0
    examined = (h - 2) * (w - 2)
    for y in range(1, h - 1):
        up, mid, dn = rows[y - 1], rows[y], rows[y + 1]
        for x in range(1, w - 1):
            n = sorted((up[x - 1], up[x], up[x + 1],
                        mid[x - 1], mid[x + 1],
                        dn[x - 1], dn[x], dn[x + 1]))
            med = (n[3] + n[4]) // 2
            d = abs(mid[x] - med)
            for c in CONTRASTS:
                if d >= c:
                    counts[c] += 1
    return counts, examined


def flicker_counts(rows_a, rows_b):
    """Pixels that changed between two frames of a camera that did not move."""
    counts = dict((c, 0) for c in CONTRASTS)
    h = min(len(rows_a), len(rows_b))
    w = min(len(rows_a[0]), len(rows_b[0])) if h else 0
    examined = h * w
    for y in range(h):
        ra, rb = rows_a[y], rows_b[y]
        for x in range(w):
            d = abs(ra[x] - rb[x])
            for c in CONTRASTS:
                if d >= c:
                    counts[c] += 1
    return counts, examined


def series(counts, examined):
    """c8[0.001234]/c16[...]/c32[...] over one stated denominator."""
    if examined <= 0:
        return "nothing-measured"
    return "/".join("c%d[%.6f]" % (c, counts[c] / float(examined)) for c in CONTRASTS)


def excess_series(sub, ctl, examined):
    if examined <= 0:
        return "nothing-measured"
    return "/".join("c%d[%+.6f]" % (c, (sub[c] - ctl[c]) / float(examined))
                    for c in CONTRASTS)


def first_cut(sub, ctl, examined):
    """The coarse split, at DECIDE_AT only. Returns (fired, why)."""
    if examined <= 0:
        return False, "nothing-measured"
    s, c = sub[DECIDE_AT], ctl[DECIDE_AT]
    if s - c < FIRST_CUT_FLOOR_PX:
        return False, "excess=%dpx-under-floor=%dpx" % (s - c, FIRST_CUT_FLOOR_PX)
    if c > 0 and s < c * FIRST_CUT_RATIO:
        return False, "ratio=%.2f-under=%0.1f" % (s / float(c), FIRST_CUT_RATIO)
    return True, "subject=%dpx-control=%dpx" % (s, c)


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


def measure(frames, subj_frac, ctrl_frac):
    """frames: list of open PIL images, in capture order. Returns key lines."""
    out = []
    out.append("zfightStat=subject-vs-same-area-control-in-the-same-frame/"
               "control-is-the-denominator/no-new-bound")
    if not frames:
        out.append("zfightStatus=NOTHING-MEASURED zfightFrames=0 zfightPairs=0 "
                   "zfightReason=no-frame-was-given-to-this-tool")
        out.append("NOTHING MEASURED - nothing measured: no frame reached this tool, "
                   "so this is not a clean result.")
        return out, "NOTHING-MEASURED"

    w, h = frames[0].size
    subj = rect_px(subj_frac, w, h)
    ctrl = rect_px(ctrl_frac, w, h)
    same_area = area(subj) == area(ctrl) and area(subj) > 0
    out.append("zfightFrames=%d zfightPairs=%d zfightFrameWH=%d/%d "
               "zfightSubjectRectPx=%d/%d/%d/%d zfightControlRectPx=%d/%d/%d/%d "
               "zfightAreaMatch=%s zfightRectAreaPx=%d/%d"
               % (len(frames), max(0, len(frames) - 1), w, h,
                  subj[0], subj[1], subj[2], subj[3],
                  ctrl[0], ctrl[1], ctrl[2], ctrl[3],
                  "yes" if same_area else "no", area(subj), area(ctrl)))
    if not same_area:
        out.append("zfightStatus=NOTHING-MEASURED "
                   "zfightReason=the-control-is-not-the-same-area-as-the-subject/"
                   "the-control-is-the-denominator-and-a-different-one-answers-nothing")
        out.append("NOTHING MEASURED - nothing measured: the two rectangles differ in area.")
        return out, "NOTHING-MEASURED"

    sub_sp = dict((c, 0) for c in CONTRASTS)
    ctl_sp = dict((c, 0) for c in CONTRASTS)
    sp_examined = 0
    sub_fl = dict((c, 0) for c in CONTRASTS)
    ctl_fl = dict((c, 0) for c in CONTRASTS)
    fl_examined = 0

    prev_sub_rows = prev_ctl_rows = None
    for img in frames:
        sub_rows = luma_rows(img, subj)
        ctl_rows = luma_rows(img, ctrl)
        cs, ex = speckle_counts(sub_rows)
        cc, _ = speckle_counts(ctl_rows)
        sp_examined += ex
        for c in CONTRASTS:
            sub_sp[c] += cs[c]
            ctl_sp[c] += cc[c]
        if prev_sub_rows is not None:
            fs, fex = flicker_counts(prev_sub_rows, sub_rows)
            fc, _ = flicker_counts(prev_ctl_rows, ctl_rows)
            fl_examined += fex
            for c in CONTRASTS:
                sub_fl[c] += fs[c]
                ctl_fl[c] += fc[c]
        prev_sub_rows, prev_ctl_rows = sub_rows, ctl_rows

    out.append("zfightSpecklePixelsExamined=%d zfightFlickerPixelsExamined=%d "
               "zfightExaminedStat=cumulative-over-every-frame-and-pair-given"
               % (sp_examined, fl_examined))
    out.append("zfightSpeckleSubject=%s" % series(sub_sp, sp_examined))
    out.append("zfightSpeckleControl=%s" % series(ctl_sp, sp_examined))
    out.append("zfightSpeckleExcess=%s" % excess_series(sub_sp, ctl_sp, sp_examined))
    out.append("zfightFlickerSubject=%s" % series(sub_fl, fl_examined))
    out.append("zfightFlickerControl=%s" % series(ctl_fl, fl_examined))
    out.append("zfightFlickerExcess=%s" % excess_series(sub_fl, ctl_fl, fl_examined))

    sp_fired, sp_why = first_cut(sub_sp, ctl_sp, sp_examined)
    fl_fired, fl_why = first_cut(sub_fl, ctl_fl, fl_examined)
    if sp_examined <= 0:
        status = "NOTHING-MEASURED"
    elif sp_fired or fl_fired:
        status = "TIE"
    else:
        status = "NO-TIE"
    out.append("zfightSpeckleFired=%s/%s zfightFlickerFired=%s/%s"
               % ("yes" if sp_fired else "no", sp_why,
                  "yes" if fl_fired else "no", fl_why))
    out.append("zfightDecidedAtContrast=%d zfightFirstCut=ratio>=%.1f-and-excess>=%dpx/"
               "not-a-tuned-bound/the-densities-above-are-the-evidence"
               % (DECIDE_AT, FIRST_CUT_RATIO, FIRST_CUT_FLOOR_PX))
    if fl_examined <= 0:
        out.append("zfightFlickerNote=nothing-measured/one-frame-cannot-make-a-pair")
    out.append("zfightStatus=%s" % status)
    return out, status


def parse_rect(text):
    parts = text.replace(",", "/").split("/")
    if len(parts) != 4:
        raise ValueError("a rectangle is four numbers: x0/y0/x1/y1")
    return tuple(float(p) for p in parts)


def rects_from_verdict(path):
    """Read the two rectangles the walk probe printed, as fractions."""
    subj = ctrl = None
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            for tok in line.split():
                if tok.startswith("grateSubjectRectFrac="):
                    subj = parse_rect(tok.split("=", 1)[1])
                elif tok.startswith("grateControlRectFrac="):
                    ctrl = parse_rect(tok.split("=", 1)[1])
    return subj, ctrl


# ---------------------------------------------------------------- selftest

def _lcg(seed):
    x = seed
    while True:
        x = (1103515245 * x + 12345) % 2147483648
        yield x


def _synthetic(w, h, seed, speckle_rect=None, speckle_seed=0, rate=30):
    """A grey frame with fine texture in it, optionally speckled in one rect.

    THE TEXTURE IS IN THE WHOLE FRAME, so the subject and control rectangles
    are alike by construction and the ONLY difference the planted case makes
    is the speckle. A control that was flat grey would make any subject look
    like a tie.
    """
    img = Image.new("RGB", (w, h))
    px = img.load()
    r = _lcg(seed)
    for y in range(h):
        for x in range(w):
            v = 110 + (next(r) % 9)
            px[x, y] = (v, v, v)
    if speckle_rect is not None:
        x0, y0, x1, y1 = speckle_rect
        s = _lcg(speckle_seed)
        for y in range(y0 + 1, y1 - 1):
            for x in range(x0 + 1, x1 - 1):
                if next(s) % rate == 0:
                    px[x, y] = (210, 210, 210)
    return img


def selftest():
    checks = []

    def check(name, ok):
        checks.append((name, ok))
        print("  %s - %s" % ("ok" if ok else "FAIL", name))

    W, H = 160, 100
    subj_frac = (0.10, 0.55, 0.45, 0.90)
    ctrl_frac = (0.10, 0.05, 0.45, 0.40)
    subj_px = rect_px(subj_frac, W, H)

    # THE ACCEPTING CASE FIRST, per rule 5b: two frames, subject and control
    # alike, nothing planted. A guard that cannot pass this is a ratchet.
    print("accepting case: subject and control alike, nothing planted")
    a = _synthetic(W, H, seed=11)
    b = _synthetic(W, H, seed=12)
    lines, status = measure([a, b], subj_frac, ctrl_frac)
    for ln in lines:
        print("    " + ln)
    check("alike subject and control read NO-TIE", status == "NO-TIE")
    check("the accepting case examined pixels and said so",
          any(ln.startswith("zfightSpecklePixelsExamined=") and
              not ln.startswith("zfightSpecklePixelsExamined=0 ") for ln in lines))

    # THE PLANTED CASE: the condition this asserts CAN happen, planted rather
    # than argued. Speckle in the SUBJECT only, and different pixels in the
    # second frame, so both halves of the instrument have something to see.
    print("planted case: the subject speckles, the control does not")
    a2 = _synthetic(W, H, seed=11, speckle_rect=subj_px, speckle_seed=97)
    b2 = _synthetic(W, H, seed=12, speckle_rect=subj_px, speckle_seed=641)
    lines2, status2 = measure([a2, b2], subj_frac, ctrl_frac)
    for ln in lines2:
        print("    " + ln)
    check("a speckling subject against a clean control reads TIE", status2 == "TIE")
    check("the speckle half fired on the planted case",
          any("zfightSpeckleFired=yes" in ln for ln in lines2))
    check("the flicker half fired on the planted case",
          any("zfightFlickerFired=yes" in ln for ln in lines2))

    # NOTHING MEASURED, IN THE WORDS RULE 3b ASKS FOR.
    print("nothing-measured case: no frames at all")
    lines3, status3 = measure([], subj_frac, ctrl_frac)
    for ln in lines3:
        print("    " + ln)
    check("no frames reads NOTHING-MEASURED", status3 == "NOTHING-MEASURED")
    check("no frames prints the words nothing measured",
          any("nothing measured" in ln for ln in lines3))

    # ONE FRAME: speckle still measurable, flicker explicitly nothing measured.
    print("one-frame case: a speckle reading with no pair to flicker")
    lines4, status4 = measure([a], subj_frac, ctrl_frac)
    for ln in lines4:
        print("    " + ln)
    check("one frame still reaches a speckle verdict",
          status4 in ("TIE", "NO-TIE"))
    check("one frame says its flicker half measured nothing",
          any("zfightFlickerSubject=nothing-measured" in ln for ln in lines4))

    # A CONTROL THAT IS NOT THE SAME AREA ANSWERS NOTHING.
    print("mismatched case: a control of a different area")
    lines5, status5 = measure([a, b], subj_frac, (0.10, 0.05, 0.30, 0.20))
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
    ap.add_argument("--verdict", help="ue-walk-verdict.txt to read both rectangles from")
    ap.add_argument("--frames-dir", default="production/d1-probe",
                    help="where the two grate frames live when --verdict is used")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    subj = parse_rect(args.subject) if args.subject else None
    ctrl = parse_rect(args.control) if args.control else None
    frames = list(args.frames)

    if args.verdict:
        vs, vc = rects_from_verdict(args.verdict)
        subj = subj or vs
        ctrl = ctrl or vc
        if not frames:
            for leaf in ("ue-walk_05_grate_a.png", "ue-walk_06_grate_b.png"):
                p = os.path.join(args.frames_dir, leaf)
                if os.path.exists(p):
                    frames.append(p)

    if subj is None or ctrl is None:
        print("zfightStatus=NOTHING-MEASURED "
              "zfightReason=no-rectangles/pass---subject-and---control-or---verdict")
        print("NOTHING MEASURED - nothing measured: this tool was given no rectangle.")
        return 2

    imgs = []
    missing = 0
    for p in frames:
        if os.path.exists(p):
            imgs.append(Image.open(p))
        else:
            missing += 1
    print("zfightFramesGiven=%d zfightFramesMissing=%d zfightFramesRead=%d"
          % (len(frames), missing, len(imgs)))
    lines, status = measure(imgs, subj, ctrl)
    for ln in lines:
        print(ln)
    return 0 if status in ("TIE", "NO-TIE") else 3


if __name__ == "__main__":
    sys.exit(main())
