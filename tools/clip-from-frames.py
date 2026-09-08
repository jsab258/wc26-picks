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

THE CAPTIONS, ADDED 2026-09-08 BY THE CRIME RULING SECTION 5.

    python3 tools/clip-from-frames.py --frames-glob GLOB --out FILE.gif \
        --frame-keys ue-crimeseq-keys.txt --bank content/dialogue/crime-witness-v1.json

CrimeProbe.cpp writes one line per sequence frame naming the beat, the
speaker, the bank line id and whether that frame is one somebody is SPEAKING
on (`heard=yes`). This tool burns the bank's text for that id along the
bottom of those frames and leaves every other frame alone.

WHY THE CAPTION LIVES HERE AND NOT IN THE PROBE. The ruling names it and
`.claude/rules/instruments.md` has carried the reason since 25 August: the
Unreal layer does not compile in the container that writes it, so a
formatter written there ships UNRUN, and an unrun formatter printing a
plausible string is the quietest instrument fault there is. The probe
supplies live state (which frame, which beat, which id) and nothing else;
the selection of the text, the wrapping, the strip and every printed number
about them are here, where `--selftest` runs them before a dispatch.

AN ID THE BANK DOES NOT HAVE IS A REFUSAL, NAMING THE ID. Not a blank strip
and not an uncaptioned frame: a clip whose words silently went missing looks
exactly like a clip that was never meant to have any, and the whole point of
this pass is that the second window's consequence is that nobody speaks of
it. The two cases must not read alike.
"""
import glob
import json
import os
import shutil
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

# 8 MiB: an order of magnitude under outbox.send_video's 50 MB refusal, so a
# clip that would be refused there is refused HERE, deliberately, with room
# to spare rather than landing right at the edge of the real limit.
USAGE = ("usage: clip-from-frames.py --frames-glob GLOB --out FILE.gif "
         "[--scale F] [--duration-ms N] [--max-bytes N] "
         "[--frame-keys FILE --bank FILE]")

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

# THE CAPTION STRIP, AS A FRACTION OF THE OUTPUT HEIGHT. At the 480x270 this
# tool's default scale produces from a 960x540 capture, 0.22 is 59 pixels:
# room for three wrapped lines of the ~13px type below plus its margins,
# which is what the longest line in content/dialogue/crime-witness-v1.json
# needs at that width. Not tuned from a series of clips (there is one), so
# the number of lines actually wrapped and the number dropped are both
# printed rather than assumed to fit.
CAPTION_STRIP_FRACTION = 0.22
CAPTION_MARGIN_PX = 4
# THE STRIP IS DRAWN, NOT BLENDED. A translucent bar needs RGBA compositing
# per frame and a GIF has no alpha to carry it anyway; a solid bar over the
# bottom fifth of a 270px frame costs nothing and stays legible after the
# GIF's colour quantisation, which a 50% grey over moving pavement would not.
CAPTION_BAR_RGB = (12, 12, 14)
CAPTION_TEXT_RGB = (238, 236, 230)

# NAMED CANDIDATES, IN ORDER, AND THE ONE THAT ANSWERED IS PRINTED. Pillow's
# built-in bitmap font is about 11px and does not scale, so a truetype face
# is preferred where the machine has one; which face answered changes what
# the words look like on Jafar's phone, so it is a measurement and not an
# implementation detail.
CAPTION_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
)

FIELD_ORDER = (
    "clipStatus", "clipReason", "clipFramesExamined", "clipFramesUsed",
    "clipWidth", "clipHeight", "clipDurationMs", "clipScale",
    "clipBytes", "clipMaxBytes", "clipOut",
    "clipCaptionedFrames", "clipCaptionReason", "clipCaptionTextPx",
    "clipCaptionFont", "clipCaptionLinesDropped", "clipCaptionKeysRead",
    "clipCaptionBankRead",
)


def _nospace(s):
    """No reader of this project's key=value lines tolerates a space inside
    a value; every one of them splits on whitespace and truncates silently.
    An error message or a path is the one place a space could sneak in."""
    return str(s).replace(" ", "_")


# ------------------------------------------------------- the caption layer

def read_frame_keys(path):
    """CrimeProbe.cpp's `ue-crimeseq-keys.txt`, one `key=value` line per
    sequence frame, into {basename: {key: value}}.

    Returns (rows, examined, error). `examined` counts every non-comment,
    non-blank line READ, which is the denominator for anything said about
    them later; a line with no `frame=` key is counted and skipped, and the
    count of those is the difference between the two numbers."""
    rows = {}
    examined = 0
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except Exception as exc:  # noqa: BLE001 - any read failure is "no keys"
        return {}, 0, _nospace("frame-keys-unreadable:%s" % exc)
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        examined += 1
        fields = {}
        for tok in line.split():
            if "=" in tok:
                k, v = tok.split("=", 1)
                fields[k] = v
        name = fields.get("frame")
        if name:
            rows[os.path.basename(name)] = fields
    return rows, examined, ""


def read_bank(path):
    """The dialogue bank, into {id: text}.

    Returns (lines, examined, error). The bank is the ONE home of this text
    (the ruling's section 3: the same words reach the verdict, the caption
    and, at the next rung, a voice clip whose filename is a hash of speaker
    and text), so nothing here invents, trims or rewrites a line: it is
    looked up by id and drawn."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except Exception as exc:  # noqa: BLE001 - unreadable or not JSON
        return {}, 0, _nospace("bank-unreadable:%s" % exc)
    rows = doc.get("lines") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        return {}, 0, "bank-has-no-lines-array"
    out = {}
    for row in rows:
        if isinstance(row, dict) and row.get("id"):
            out[str(row["id"])] = str(row.get("text", ""))
    return out, len(rows), ""


def caption_for(keys_rows, bank_lines, basename):
    """(text, reason) for one frame. text is None when this frame carries no
    words, which is the ordinary case and NOT an error: the second window's
    consequence is that nobody speaks of it.

    A `heard=yes` frame naming an id the bank does not carry is the one case
    that REFUSES, with the id in the reason."""
    row = keys_rows.get(basename)
    if row is None:
        return None, "no-keys-line-for-this-frame"
    if row.get("heard") != "yes":
        return None, "heard=" + str(row.get("heard", "absent"))
    line_id = row.get("lineId", "")
    if not line_id or line_id == "none":
        return None, "heard=yes-but-no-lineId"
    if line_id not in bank_lines:
        return False, _nospace("bank-has-no-line-id:%s" % line_id)
    return bank_lines[line_id], "none"


def load_caption_font(out_height):
    """(font, name, line_px). The face that answered is named because it
    decides what the words look like, and the pixel height is measured off
    the font rather than assumed from the size asked for."""
    size = max(9, int(round(out_height * 0.055)))
    for path in CAPTION_FONT_CANDIDATES:
        if not os.path.exists(path):
            continue
        try:
            font = ImageFont.truetype(path, size)
        except Exception:  # noqa: BLE001 - an unusable face is not a crash
            continue
        return font, _nospace(os.path.basename(path) + "@" + str(size)), _line_px(font)
    font = ImageFont.load_default()
    return font, "PIL-load_default/fixed-bitmap", _line_px(font)


def _text_size(font, text):
    """Pillow moved this API twice. getbbox is 8.0+, getsize is older and
    removed in 10; both are tried rather than pinning a version this repo
    does not control on the runner."""
    try:
        box = font.getbbox(text)
        return box[2] - box[0], box[3] - box[1]
    except AttributeError:
        return font.getsize(text)


def _line_px(font):
    # MEASURED OFF A STRING WITH AN ASCENDER AND A DESCENDER, not off the
    # size asked for: a bitmap font ignores the size entirely.
    return int(_text_size(font, "Ahgy")[1])


def wrap_caption(font, text, max_width_px):
    """Greedy wrap on measured widths, never on a character count. Returns
    the list of lines; a single word wider than the strip gets its own line
    rather than being dropped."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = word if not current else current + " " + word
        if _text_size(font, trial)[0] <= max_width_px or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def burn_caption(img, text, font, line_px):
    """Draws the strip and returns (image, lines_shown, lines_wrapped). The
    image is modified in place and returned for the caller's convenience.

    THE CAP ANNOUNCES ITSELF THROUGH ITS RETURN VALUE: a caption that does
    not fit loses its last lines, and the caller prints how many, because a
    sentence that ends mid-clause on Jafar's phone with nothing saying so is
    the silent-instrument failure this tool's own header names."""
    w, h = img.size
    strip_h = max(line_px + 2 * CAPTION_MARGIN_PX, int(round(h * CAPTION_STRIP_FRACTION)))
    strip_h = min(strip_h, h)
    lines = wrap_caption(font, text, w - 2 * CAPTION_MARGIN_PX)
    room = max(1, (strip_h - 2 * CAPTION_MARGIN_PX) // max(1, line_px))
    shown = lines[:room]
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, h - strip_h, w, h], fill=CAPTION_BAR_RGB)
    y = h - strip_h + CAPTION_MARGIN_PX
    for line in shown:
        draw.text((CAPTION_MARGIN_PX, y), line, font=font, fill=CAPTION_TEXT_RGB)
        y += line_px
    return img, len(shown), len(lines)


def build(pattern, out_path, scale=DEFAULT_SCALE, duration_ms=DEFAULT_DURATION_MS,
          max_bytes=DEFAULT_MAX_BYTES, frame_keys=None, bank=None):
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
        # NEVER-ATTEMPTED PRINTS THE WORDS, not a zero: a clip nobody asked
        # to caption and a clip whose captions all failed are different
        # facts with different next actions (rule 3b).
        "clipCaptionedFrames": "nothing-measured",
        "clipCaptionReason": "no-frame-keys-file-given",
        "clipCaptionTextPx": 0, "clipCaptionFont": "none",
        "clipCaptionLinesDropped": "0/0-wrapped",
        "clipCaptionKeysRead": 0, "clipCaptionBankRead": 0,
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

    # CAPTIONS GO ON AFTER THE RESIZE, so the type is sized against the
    # pixels a person actually sees rather than against the capture and then
    # shrunk into illegibility. Refuses before writing anything: a GIF whose
    # words went missing must not exist on disk to be sent.
    if frame_keys:
        ok_caption, reason = _apply_captions(resized, paths, frame_keys, bank, fields)
        if not ok_caption:
            fields["clipStatus"] = "REFUSED"
            fields["clipReason"] = reason
            return False, fields

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


def _apply_captions(resized, paths, frame_keys, bank, fields):
    """Burns the bank's words onto the frames whose keys line says
    `heard=yes`. Returns (ok, reason) and fills every clipCaption* field.

    The two counts are a real fraction: `clipCaptionedFrames=N/M` has as its
    denominator the frames THIS CALL examined for a caption, which is every
    frame in the clip, not the subset that carried one."""
    keys_rows, keys_examined, keys_err = read_frame_keys(frame_keys)
    fields["clipCaptionKeysRead"] = keys_examined
    if keys_err:
        fields["clipCaptionedFrames"] = "0/%d" % len(paths)
        fields["clipCaptionReason"] = keys_err
        return False, keys_err
    if not bank:
        fields["clipCaptionedFrames"] = "0/%d" % len(paths)
        fields["clipCaptionReason"] = "frame-keys-given-without-a-bank"
        return False, "frame-keys-given-without-a-bank"
    bank_lines, bank_examined, bank_err = read_bank(bank)
    fields["clipCaptionBankRead"] = bank_examined
    if bank_err:
        fields["clipCaptionedFrames"] = "0/%d" % len(paths)
        fields["clipCaptionReason"] = bank_err
        return False, bank_err

    font, font_name, line_px = load_caption_font(resized[0].size[1])
    fields["clipCaptionFont"] = font_name
    fields["clipCaptionTextPx"] = line_px

    captioned, dropped, wrapped = 0, 0, 0
    for img, path in zip(resized, paths):
        text, reason = caption_for(keys_rows, bank_lines, os.path.basename(path))
        if text is False:
            fields["clipCaptionedFrames"] = "%d/%d" % (captioned, len(paths))
            fields["clipCaptionReason"] = reason
            return False, reason
        if text is None:
            continue
        _, shown, total = burn_caption(img, text, font, line_px)
        captioned += 1
        wrapped += total
        dropped += total - shown
    fields["clipCaptionedFrames"] = "%d/%d" % (captioned, len(paths))
    fields["clipCaptionReason"] = "none"
    # CUMULATIVE OVER EVERY CAPTIONED FRAME, named so: this is the cap on
    # the strip announcing itself, and a non-zero numerator means words a
    # viewer will never read.
    fields["clipCaptionLinesDropped"] = "%d/%d-wrapped" % (dropped, wrapped)
    return True, "none"


def report(pattern, out_path, scale, duration_ms, max_bytes,
           frame_keys=None, bank=None):
    ok, fields = build(pattern, out_path, scale, duration_ms, max_bytes,
                       frame_keys, bank)
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

        # ---- THE CAPTIONS, ACCEPTING CASE FIRST (ruling section 5).
        #
        # A SYNTHETIC KEYS FILE AND A SYNTHETIC BANK, because the accepting
        # case here has to contain a frame that IS captioned and a frame
        # that is NOT, and the live bank cannot supply the frames. The
        # rejecting fixture (an id nothing carries) is synthetic for the
        # reason instruments.md gives: doing the work this tool prompts
        # must never be able to break the tool.
        cap_dir = os.path.join(tmp, "caption")
        os.makedirs(cap_dir)
        cap_names = ["ue-crimeseq_000.png", "ue-crimeseq_001.png", "ue-crimeseq_002.png"]
        for i, name in enumerate(cap_names):
            # 960x540, WHICH IS WHAT THE PROBE CAPTURES, so this fixture
            # exercises the 480x270 strip the real clip gets rather than a
            # smaller one with different room in it. A fixture at a
            # resolution nothing ships would pass while the shipped size
            # dropped half of every line.
            Image.new("RGB", (960, 540), color=(40 + i, 60, 80)).save(
                os.path.join(cap_dir, name))
        keys_path = os.path.join(tmp, "keys.txt")
        with open(keys_path, "w", encoding="utf-8") as fh:
            fh.write("# synthetic keys file, one line per sequence frame\n")
            fh.write("frame=ue-crimeseq_000.png beat=approach_a speaker=none "
                     "lineId=none heard=no\n")
            fh.write("frame=ue-crimeseq_001.png beat=overheard speaker=w1 "
                     "lineId=test-ws-01 heard=yes\n")
            fh.write("frame=ue-crimeseq_002.png beat=overheard speaker=n2 "
                     "lineId=test-ov-01 heard=yes\n")
        bank_path = os.path.join(tmp, "bank.json")
        with open(bank_path, "w", encoding="utf-8") as fh:
            json.dump({"bank": "selftest", "lines": [
                {"id": "test-ws-01", "context": "witness_summary", "idRung": 3,
                 "speaker": "w1",
                 "text": "He looked straight at me before he ran, and I have "
                         "his face now whatever his name turns out to be."},
                {"id": "test-ov-01", "context": "overheard", "idRung": 3,
                 "speaker": "n2", "text": "Then you want to keep that to yourself."},
            ]}, fh)

        # THE READING IS THE BOTTOM STRIP'S OWN PIXELS, BEFORE AND AFTER.
        # "A caption was requested" is not "a caption is on the frame"; only
        # the pixels of the artifact say that (rule 4).
        def strip_bytes(path, idx):
            with Image.open(path) as im:
                im.seek(idx)
                rgb = im.convert("RGB")
                w, h = rgb.size
                return rgb.crop((0, h - max(1, int(h * CAPTION_STRIP_FRACTION)),
                                 w, h)).tobytes()

        plain_out = os.path.join(tmp, "cap-plain.gif")
        plain_ok, _ = build(os.path.join(cap_dir, "ue-crimeseq_*.png"), plain_out,
                            0.5, 100, 8 * 1024 * 1024)
        cap_out = os.path.join(tmp, "cap-burned.gif")
        cap_ok, fields = build(os.path.join(cap_dir, "ue-crimeseq_*.png"), cap_out,
                               0.5, 100, 8 * 1024 * 1024,
                               frame_keys=keys_path, bank=bank_path)
        check("accepting: captioning a clip still writes the clip", plain_ok and cap_ok)
        check("accepting: the count of captioned frames is a real fraction",
              fields["clipCaptionedFrames"] == "2/3")
        check("accepting: the font that answered is named",
              fields["clipCaptionFont"] != "none")
        check("accepting: the text height was measured, not assumed",
              isinstance(fields["clipCaptionTextPx"], int) and fields["clipCaptionTextPx"] > 0)
        check("accepting: the keys file and the bank both report what they read",
              fields["clipCaptionKeysRead"] == 3 and fields["clipCaptionBankRead"] == 2)
        check("accepting: a heard=yes frame's bottom strip CHANGED",
              plain_ok and cap_ok and strip_bytes(plain_out, 1) != strip_bytes(cap_out, 1))
        check("accepting: the second heard=yes frame's strip changed too",
              plain_ok and cap_ok and strip_bytes(plain_out, 2) != strip_bytes(cap_out, 2))
        check("accepting: a heard=no frame's bottom strip did NOT change",
              plain_ok and cap_ok and strip_bytes(plain_out, 0) == strip_bytes(cap_out, 0))
        check("accepting: every wrapped line fitted the strip",
              fields["clipCaptionLinesDropped"].startswith("0/")
              and fields["clipCaptionLinesDropped"] != "0/0-wrapped")
        check("accepting: no captions asked for prints the words, not a zero",
              build(os.path.join(cap_dir, "ue-crimeseq_*.png"),
                    os.path.join(tmp, "cap-none.gif"), 0.5, 100, 8 * 1024 * 1024
                    )[1]["clipCaptionedFrames"] == "nothing-measured")

        # ---- rejecting: a heard=yes frame naming an id the bank lacks.
        bad_keys = os.path.join(tmp, "keys-bad.txt")
        with open(bad_keys, "w", encoding="utf-8") as fh:
            fh.write("frame=ue-crimeseq_000.png beat=approach_a speaker=none "
                     "lineId=none heard=no\n")
            fh.write("frame=ue-crimeseq_001.png beat=overheard speaker=w1 "
                     "lineId=cw-ws-r9-99 heard=yes\n")
        miss_out = os.path.join(tmp, "cap-missing.gif")
        miss_ok, fields = build(os.path.join(cap_dir, "ue-crimeseq_*.png"), miss_out,
                                0.5, 100, 8 * 1024 * 1024,
                                frame_keys=bad_keys, bank=bank_path)
        check("rejecting: an id the bank lacks refuses", not miss_ok)
        check("rejecting: the missing id is NAMED in the reason",
              "cw-ws-r9-99" in fields["clipReason"]
              and "cw-ws-r9-99" in fields["clipCaptionReason"])
        check("rejecting: a refused caption writes no clip at all",
              not os.path.exists(miss_out))

        # ---- rejecting: keys without a bank, and a keys file that is not there.
        nb_ok, fields = build(os.path.join(cap_dir, "ue-crimeseq_*.png"),
                              os.path.join(tmp, "cap-nobank.gif"), 0.5, 100,
                              8 * 1024 * 1024, frame_keys=keys_path, bank=None)
        check("rejecting: a keys file with no bank refuses",
              not nb_ok and fields["clipReason"] == "frame-keys-given-without-a-bank")
        nk_ok, fields = build(os.path.join(cap_dir, "ue-crimeseq_*.png"),
                              os.path.join(tmp, "cap-nokeys.gif"), 0.5, 100,
                              8 * 1024 * 1024,
                              frame_keys=os.path.join(tmp, "nope.txt"), bank=bank_path)
        check("rejecting: a keys file that is not there refuses and says so",
              not nk_ok and fields["clipReason"].startswith("frame-keys-unreadable:"))

        # ---- the strip's cap announces itself on a line nothing could fit.
        long_keys = os.path.join(tmp, "keys-long.txt")
        with open(long_keys, "w", encoding="utf-8") as fh:
            fh.write("frame=ue-crimeseq_000.png beat=approach_a speaker=none "
                     "lineId=none heard=no\n")
            fh.write("frame=ue-crimeseq_001.png beat=overheard speaker=w1 "
                     "lineId=test-long heard=yes\n")
        long_bank = os.path.join(tmp, "bank-long.json")
        with open(long_bank, "w", encoding="utf-8") as fh:
            json.dump({"lines": [{"id": "test-long",
                                  "text": ("word " * 200).strip()}]}, fh)
        long_ok, fields = build(os.path.join(cap_dir, "ue-crimeseq_*.png"),
                                os.path.join(tmp, "cap-long.gif"), 0.5, 100,
                                8 * 1024 * 1024, frame_keys=long_keys, bank=long_bank)
        dropped = fields["clipCaptionLinesDropped"].split("/")[0]
        check("planted: a caption too long for the strip announces the lines lost",
              long_ok and int(dropped) > 0)

        # ---- THE LIVE BANK IS AN ACCEPTING FIXTURE TOO (instruments.md: for
        # a tool that checks the project itself, the live codebase is the
        # accepting fixture). Every line the dialogue writer actually wrote
        # must fit the strip at the size the clip ships at, or the clip would
        # cut a sentence off on Jafar's phone with only a number saying so.
        # SKIPPED WITH A DENOMINATOR, not silently, when the bank is absent.
        live_bank = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "content", "dialogue", "crime-witness-v1.json")
        if os.path.exists(live_bank):
            lines, examined, err = read_bank(live_bank)
            font, _, line_px = load_caption_font(270)
            strip_h = max(line_px + 2 * CAPTION_MARGIN_PX,
                          int(round(270 * CAPTION_STRIP_FRACTION)))
            room = max(1, (strip_h - 2 * CAPTION_MARGIN_PX) // max(1, line_px))
            worst, worst_id = 0, "none"
            for line_id, text in lines.items():
                n = len(wrap_caption(font, text, 480 - 2 * CAPTION_MARGIN_PX))
                if n > worst:
                    worst, worst_id = n, line_id
            check("accepting (live bank): it read %d line(s) and none was empty"
                  % examined, not err and examined > 0 and len(lines) == examined)
            check("accepting (live bank): the worst line wraps to %d, the strip "
                  "holds %d (%s)" % (worst, room, worst_id), worst <= room)
        else:
            check("live bank absent, so nothing measured about it", True)
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
                print(USAGE)
                sys.exit(2)
            return cast(args[i + 1])
        return default

    pattern = opt("--frames-glob")
    out_path = opt("--out")
    if not pattern or not out_path:
        print(USAGE)
        return 2
    scale = opt("--scale", DEFAULT_SCALE, float)
    duration_ms = opt("--duration-ms", DEFAULT_DURATION_MS, int)
    max_bytes = opt("--max-bytes", DEFAULT_MAX_BYTES, int)
    frame_keys = opt("--frame-keys")
    bank = opt("--bank")
    return report(pattern, out_path, scale, duration_ms, max_bytes, frame_keys, bank)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
