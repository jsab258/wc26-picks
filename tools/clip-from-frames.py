#!/usr/bin/env python3
"""Stitch a directory of committed frames into ONE looping GIF, Pillow only.

    python3 tools/clip-from-frames.py --frames-glob GLOB --out FILE.gif
    python3 tools/clip-from-frames.py --selftest

WHY THIS EXISTS. Ruling 1, Jafar, 2026-09-07: the walk probe (WalkProbe.cpp)
photographs the scripted route and needs a clip Jafar can watch on Telegram,
not five stills read one at a time. `ledger-v2/research/license-allowlist.md`
opens by scoping itself: "verify weights license, not code license". Every
entry in it is a generative model or a shipped game asset; it governs models
and shipped content, not a Python utility library. Pillow is already imported
by five tools in this repository (glance.py, map.py, gallery.py, ref-bench.py,
decal-ink.py) and is encoding OUR OWN render output here, which is a
diagnostic, not a shipped asset, so no decision record is owed for it.

GIF, NOT MP4, AND THAT IS THE WHOLE REASON FOR THE FORMAT. Pillow cannot write
MP4; reaching for one would mean shelling out to ffmpeg, which WOULD be a new
tool needing the decision record this file does not need. Telegram plays a GIF
as a looping clip via sendAnimation (wired in tools/runner/telegram-bot.py,
not this file), so GIF is not a compromise here, it is the format the delivery
side already wants.

WHAT THIS DOES NOT DO. It does not walk the street, decide which frames are
evidence, or know what a good clip looks like. It takes a glob of frames
someone else captured, in filename order, and turns them into one file. The
milestone frames WalkProbe.cpp writes (`ue-walk_NN_*.png`) are the evidence
and are never touched by this tool; the SEQUENCE frames
(`ue-walkseq_*.png`) are the ones meant for this, because a slideshow of five
milestones is not a clip and playing the walk back needs enough of them to
read as motion rather than a series of jumps.

THE SIZE BOUND IS NAMED AND ENFORCED HERE, NOT LEFT TO THE SENDER.
`tools/runner/outbox.py`'s `send_video` refuses anything over 50 MB with the
size named; this tool's own default ceiling is 8 MiB, an order of magnitude
under that, so a clip that would be refused at delivery is refused HERE
first, with the same key=value shape, rather than committed and only found
oversize later. A run that would exceed it REFUSES rather than truncating:
truncating silently would make a shorter clip look like the intended one.

EVERY OUTCOME PRINTS THE SAME KEYS (rule: a zero needs a denominator).
`clipFramesExamined` is what the glob found, honest even when nothing else
happened; `clipFramesUsed` is what actually went into the file. A run that
measured nothing prints `clipFramesExamined=0` rather than staying quiet.
"""
import glob
import os
import shutil
import sys
import tempfile

from PIL import Image

# 8 MiB: an order of magnitude under outbox.send_video's 50 MB refusal, so a
# clip that would be refused there is refused HERE, deliberately, with room
# to spare rather than landing right at the edge of the real limit.
DEFAULT_MAX_BYTES = 8 * 1024 * 1024

# HALF THE CAPTURED RESOLUTION (960x540 -> 480x270, whatever the source
# actually is). Roughly quarters the pixel count a GIF's LZW pass has to
# compress, which is most of what decides its bytes, while staying plenty
# legible for what this clip has to show: does the camera visibly move, does
# it visibly stop at the wall. Not a claim about fine detail.
DEFAULT_SCALE = 0.5

# 120 MS/FRAME (about 8.3 fps), CHOSEN SEPARATELY FROM THE CAPTURE INTERVAL.
# WalkProbe.cpp samples the route every 0.4s of wall-clock walking (named and
# reasoned in that file), which played back at its own pace is 2.5 fps and
# reads as a slideshow, not motion. GIF playback speed is independent of
# capture spacing, so this plays the same frames back roughly 3.3x faster
# than they were taken, which is what "reads as motion rather than a
# slideshow" asked for without needing more frames than a short offscreen
# capture pass can afford.
DEFAULT_DURATION_MS = 120

FIELD_ORDER = (
    "clipStatus", "clipReason", "clipFramesExamined", "clipFramesUsed",
    "clipWidth", "clipHeight", "clipDurationMs", "clipScale",
    "clipBytes", "clipMaxBytes", "clipOut",
)


def _nospace(s):
    """No reader of this project's key=value lines tolerates a space inside
    a value; every one of them splits on whitespace and truncates silently.
    An error message or a path is the one place a space could sneak in."""
    return str(s).replace(" ", "_")


def build(pattern, out_path, scale=DEFAULT_SCALE, duration_ms=DEFAULT_DURATION_MS,
          max_bytes=DEFAULT_MAX_BYTES):
    """Returns (ok, fields). fields carries EVERY key in FIELD_ORDER on every
    call, whichever branch answered, so a caller printing the line never has
    to guess which keys a given outcome left out."""
    paths = sorted(glob.glob(pattern))
    examined = len(paths)
    fields = {
        "clipStatus": "NOTHING-MEASURED", "clipReason": "not-attempted",
        "clipFramesExamined": examined, "clipFramesUsed": 0,
        "clipWidth": 0, "clipHeight": 0,
        "clipDurationMs": duration_ms, "clipScale": scale,
        "clipBytes": 0, "clipMaxBytes": max_bytes, "clipOut": out_path,
    }

    frames = []
    for p in paths:
        try:
            img = Image.open(p)
            img.load()
            frames.append(img.convert("RGB"))
        except Exception as exc:  # noqa: BLE001 - any decode failure is "corrupt"
            fields["clipStatus"] = "REFUSED"
            fields["clipReason"] = _nospace("corrupt-frame:%s:%s" % (
                os.path.basename(p), exc))
            return False, fields

    # REJECTING CASE 1: nothing to stitch. Named with the pattern examined,
    # so "0 found" and "nobody looked" cannot read alike.
    if examined == 0:
        fields["clipStatus"] = "REFUSED"
        fields["clipReason"] = _nospace("no-frames-examined-at:%s" % pattern)
        return False, fields

    # REJECTING CASE 2: one frame is not a clip. A single still would encode
    # as a valid, tiny, perfectly well-formed GIF and pass every check below
    # while being exactly the slideshow-of-one this tool exists to avoid.
    if examined == 1:
        fields["clipFramesUsed"] = 1
        fields["clipStatus"] = "REFUSED"
        fields["clipReason"] = "one-frame-is-not-a-clip"
        return False, fields

    w0, h0 = frames[0].size
    new_size = (max(1, round(w0 * scale)), max(1, round(h0 * scale)))
    resized = [f.resize(new_size, Image.LANCZOS) for f in frames]
    first, rest = resized[0], resized[1:]
    first.save(out_path, format="GIF", save_all=True, append_images=rest,
               duration=duration_ms, loop=0, optimize=True)

    out_bytes = os.path.getsize(out_path)
    fields["clipFramesUsed"] = len(frames)
    fields["clipWidth"], fields["clipHeight"] = new_size
    fields["clipBytes"] = out_bytes

    # REFUSE RATHER THAN TRUNCATE. Dropping frames to fit would ship a
    # shorter clip silently labelled as the one requested; refusing and
    # naming the bound leaves the choice (fewer frames, smaller scale,
    # shorter duration) to whoever reruns this, not guessed here.
    if out_bytes > max_bytes:
        os.remove(out_path)
        fields["clipStatus"] = "REFUSED"
        fields["clipReason"] = "over-size-bound"
        return False, fields

    fields["clipStatus"] = "WROTE"
    fields["clipReason"] = "none"
    return True, fields


def report(pattern, out_path, scale, duration_ms, max_bytes):
    ok, fields = build(pattern, out_path, scale, duration_ms, max_bytes)
    print("clip " + " ".join("%s=%s" % (k, fields[k]) for k in FIELD_ORDER))
    return 0 if ok else 1


# ------------------------------------------------------------------ selftest

def _gif_frame_count(path):
    with Image.open(path) as im:
        return im.n_frames


def selftest():
    """ACCEPTING CASE FIRST (rule 5b): real frames in, one file out, the
    right frame count. Then three rejecting cases the tool must refuse on:
    no frames, one frame, a corrupt frame; plus a size bound it cannot meet,
    because "refuses" and "silently ships something smaller" are different
    outcomes and only a planted case tells them apart."""
    ok, fails = 0, []

    def check(name, cond):
        nonlocal ok
        if cond:
            ok += 1
        else:
            fails.append(name)

    tmp = tempfile.mkdtemp(prefix="clip-from-frames-")
    try:
        good_dir = os.path.join(tmp, "good")
        os.makedirs(good_dir)
        n = 6
        for i in range(n):
            Image.new("RGB", (40, 20), color=((10 * i) % 255, 20, 30)).save(
                os.path.join(good_dir, "f_%03d.png" % i))
        out = os.path.join(tmp, "out.gif")
        good_ok, fields = build(os.path.join(good_dir, "f_*.png"), out, 0.5, 100,
                                 8 * 1024 * 1024)
        check("accepting: build reports ok", good_ok)
        check("accepting: every frame examined was used",
              fields["clipFramesExamined"] == n and fields["clipFramesUsed"] == n)
        check("accepting: status is WROTE with no reason", fields["clipStatus"] == "WROTE"
              and fields["clipReason"] == "none")
        check("accepting: the file landed on disk", os.path.exists(out))
        check("accepting: the file IS an animated GIF with the right frame count",
              _gif_frame_count(out) == n)
        check("accepting: the downscale was applied (40x20 -> 20x10)",
              fields["clipWidth"] == 20 and fields["clipHeight"] == 10)
        check("accepting: the reported bytes match the file on disk",
              fields["clipBytes"] == os.path.getsize(out))

        # ---- rejecting: no frames at all.
        empty_dir = os.path.join(tmp, "empty")
        os.makedirs(empty_dir)
        no_ok, fields = build(os.path.join(empty_dir, "*.png"),
                               os.path.join(tmp, "out-empty.gif"), 0.5, 100, 8 * 1024 * 1024)
        check("rejecting: no frames refuses", not no_ok)
        check("rejecting: no frames names the pattern examined",
              fields["clipReason"].startswith("no-frames-examined-at:"))
        check("rejecting: no frames writes no file",
              not os.path.exists(os.path.join(tmp, "out-empty.gif")))

        # ---- rejecting: exactly one frame.
        one_dir = os.path.join(tmp, "one")
        os.makedirs(one_dir)
        Image.new("RGB", (10, 10)).save(os.path.join(one_dir, "only.png"))
        one_ok, fields = build(os.path.join(one_dir, "*.png"),
                                os.path.join(tmp, "out-one.gif"), 0.5, 100, 8 * 1024 * 1024)
        check("rejecting: one frame refuses", not one_ok)
        check("rejecting: one frame names the exact reason",
              fields["clipReason"] == "one-frame-is-not-a-clip")

        # ---- rejecting: a corrupt frame among two good ones.
        bad_dir = os.path.join(tmp, "bad")
        os.makedirs(bad_dir)
        Image.new("RGB", (10, 10)).save(os.path.join(bad_dir, "a_ok.png"))
        with open(os.path.join(bad_dir, "b_bad.png"), "wb") as fh:
            fh.write(b"not a png at all")
        Image.new("RGB", (10, 10)).save(os.path.join(bad_dir, "c_ok.png"))
        bad_ok, fields = build(os.path.join(bad_dir, "*.png"),
                                os.path.join(tmp, "out-bad.gif"), 0.5, 100, 8 * 1024 * 1024)
        check("rejecting: a corrupt frame refuses", not bad_ok)
        check("rejecting: the corrupt file is named in the reason",
              "b_bad.png" in fields["clipReason"])
        check("rejecting: a corrupt frame writes no file",
              not os.path.exists(os.path.join(tmp, "out-bad.gif")))

        # ---- rejecting: a size bound the real clip cannot meet.
        tiny_ok, fields = build(os.path.join(good_dir, "f_*.png"),
                                 os.path.join(tmp, "out-tiny.gif"), 0.5, 100, 10)
        check("rejecting: an impossible size bound refuses",
              not tiny_ok and fields["clipReason"] == "over-size-bound")
        check("rejecting: the oversize file is removed, not left half-written",
              not os.path.exists(os.path.join(tmp, "out-tiny.gif")))
        check("rejecting: the bound that bit is named in the fields",
              fields["clipMaxBytes"] == 10)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("clip-from-frames selftest: %d passed, %d failed" % (ok, len(fails)))
    for f in fails:
        print("  FAILED " + f)
    return 1 if fails else 0


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest()

    def opt(name, default=None, cast=str):
        if name in args:
            i = args.index(name)
            if i + 1 >= len(args):
                print("usage: clip-from-frames.py --frames-glob GLOB --out FILE.gif "
                      "[--scale F] [--duration-ms N] [--max-bytes N]")
                sys.exit(2)
            return cast(args[i + 1])
        return default

    pattern = opt("--frames-glob")
    out_path = opt("--out")
    if not pattern or not out_path:
        print("usage: clip-from-frames.py --frames-glob GLOB --out FILE.gif "
              "[--scale F] [--duration-ms N] [--max-bytes N]")
        return 2
    scale = opt("--scale", DEFAULT_SCALE, float)
    duration_ms = opt("--duration-ms", DEFAULT_DURATION_MS, int)
    max_bytes = opt("--max-bytes", DEFAULT_MAX_BYTES, int)
    return report(pattern, out_path, scale, duration_ms, max_bytes)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
