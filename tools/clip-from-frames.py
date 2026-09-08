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

THE WORDS ON THE ROW NOW OUTRANK THE BANK, 2026-09-08. The overheard beat no
longer SPEAKS a bank row: it composes a telling at run time from the rumour
the gossip mill actually carried (StreetVoice.Exchange, ported in
ue-probe/Source/LedgerProbe/Public/StreetVoice.h), and the bank row is what
the pick WOULD have said. So CrimeProbe.h's SeqKeyLine puts the sentence
itself on the row as `lineText=`, spaces escaped to `~` because no key=value
value may carry a space, beside `lineTextSource=` naming where it came from
(composed/..., picked/..., bank/...) and `lineTextEscape=spaces-are-~`.

A CAPTION FROM THE BANK AND A CAPTION FROM WHAT WAS SAID MUST NOT READ
ALIKE, so every reason string here opens with the source it used: `spoken/`,
`bank/`, `nowords/` or a refusal. Burning the bank row while the simulation
said something else is worse than burning nothing: the clip IS the artifact,
and a caption that disagrees with the verdict makes the clip unusable as
evidence for either sentence (CLAUDE.md rule 4).

WHEN BOTH EXIST AND DISAGREE, THAT IS INFORMATION AND NOT A CONFLICT TO
SUPPRESS. The spoken text wins because it is what was said; the bank row is
never drawn beside it (one sentence reaches the frame, ever); the
disagreement is named in that frame's reason (`bank-row-differed`) and
counted on the done line as clipCaptionSpokenVsBank.

THE FOUR THINGS THE ~ UN-ESCAPE CAN MEET, each decided here and each in
--selftest:

  a real tilde in the prose   Every ~ becomes one space, because that is the
                              escape's definition, and a lone literal tilde
                              cannot be told from an escaped space by anything
                              on the row. A run of two or more, or a leading
                              or trailing one, IS a signal: it is either a
                              literal tilde beside a space or a double space,
                              and this tool cannot say which, so it captions
                              the frame, notes `tilde-run..suspect` in the
                              reason and counts it as clipCaptionTildeRuns
                              rather than deciding. Measured 2026-09-08: 0
                              tildes in content/dialogue/crime-witness-v1.json
                              and 0 in StreetVoice.h, so nothing authored in
                              the project today can reach this case.
  lineText absent, or `none`  Falls back to the bank lookup by lineId, which
                              is exactly the behaviour before this change, and
                              the reason says `bank/` and says which of the
                              two it was.
  lineText of only tildes     Un-escapes to blank, which would paint an empty
                              strip on a frame somebody is speaking on. Not
                              spoken text: falls back to the bank with the
                              blankness named in the reason.
  lineText carrying an `=`    Survives intact. read_frame_keys splits a token
                              on the FIRST `=` only, so `2~+~2~=~4` comes back
                              as `2 + 2 = 4`.

AND THE ESCAPE IS READ, NOT ASSUMED. A row declaring an escape this tool does
not implement REFUSES, naming the value, rather than un-escaping by a rule it
guessed: a mangled sentence burned onto a frame is the same silent fault as
the wrong sentence. A row with a lineText and no lineTextEscape at all is
un-escaped by the documented rule, with `escape..assumed-` in the reason.
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

# THE ONE ESCAPE THIS TOOL IMPLEMENTS, matching CrimeProbe.h's Tilde and the
# `lineTextEscape=` it writes beside every lineText. Compared, not assumed: a
# row declaring a different rule refuses rather than being un-escaped by this
# one (see the header).
LINE_TEXT_ESCAPE = "spaces-are-~"

# THE TWO WAYS A ROW SAYS "NO SENTENCE HERE". SeqKeyLine writes the word
# `none` when the beat carried no words, because a key=value value may not be
# empty either; a hand-written or older row can also carry `lineText=` with
# nothing after it. Both mean the same thing and both fall back to the bank.
LINE_TEXT_ABSENT_TOKENS = ("", "none")

# HOW MANY PER-FRAME LINES GET PRINTED, FROM A PRINTED SERIES AND NOT A GUESS.
# The live keys file (production/d1-probe/ue-crimeseq-keys.txt, run 5ea6cb0)
# has 25 rows of which 8 carry words, and CrimeProbe.h's own clock cap is
# kMaxSeqFrames = 32 frames in total, so 16 is twice the observed number of
# with-words rows and half the structural maximum. It announces itself either
# way: the last clipframe line always says whether it bit and over what.
SAMPLE_LINE_CAP = 16

# THE ECHOED SENTENCE'S OWN CAP, also from a measured series: the composed
# tellings this beat can produce (42 templates in StreetVoice.h wrapped around
# the live witness summary) measured 110 to 149 characters on 2026-09-08, so
# 200 clears every one of them and a value that does hit it says by how much.
SAMPLE_TEXT_CAP = 200

FIELD_ORDER = (
    "clipStatus", "clipReason", "clipFramesExamined", "clipFramesUsed",
    "clipWidth", "clipHeight", "clipDurationMs", "clipScale",
    "clipBytes", "clipMaxBytes", "clipOut",
    "clipCaptionedFrames", "clipCaptionReason", "clipCaptionTextPx",
    "clipCaptionFont", "clipCaptionLinesDropped", "clipCaptionKeysRead",
    "clipCaptionBankRead",
    # ADDED 2026-09-08 WITH THE lineText PREFERENCE. All three are whole-run
    # and all three ship their denominator; the per-frame half of the same
    # facts is the `clipframe` lines, never this line.
    "clipCaptionsBySource", "clipCaptionSpokenVsBank", "clipCaptionTildeRuns",
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
    count of those is the difference between the two numbers.

    THE SPLIT IS ON THE FIRST `=` ONLY, which is what lets a sentence riding
    in `lineText=` carry an `=` of its own, and the split on whitespace is
    what guarantees no value can contain a space by the time it is read."""
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


def tilde_escape(text):
    """Each whitespace character to one `~`, which is exactly what
    CrimeProbe.h's Tilde does on the way out. Used here to put the sentence
    this tool actually burned back onto its own sample line, so the words in
    the committed evidence file and the words on the frame are the same string
    and a reader can compare them without reading pixels."""
    return "".join("~" if ch in " \t\r\n" else ch for ch in str(text))


def unescape_line_text(raw):
    """(text, tilde_run) for one `lineText=` value.

    EVERY ~ BECOMES ONE SPACE, the inverse of CrimeProbe.h's Tilde, which
    writes one ~ per whitespace character. A lone literal tilde in the prose is
    indistinguishable from an escaped space and becomes one: that is a property
    of the escape, not a choice this function can make.

    tilde_run is True when the raw value carries a run of two or more tildes,
    or begins or ends with one. Those shapes are either a literal tilde beside
    a space or a double space, and nothing on the row can tell them apart, so
    the frame is still captioned and the count is printed instead
    (clipCaptionTildeRuns)."""
    s = str(raw)
    tilde_run = ("~~" in s) or s.startswith("~") or s.endswith("~")
    return s.replace("~", " "), tilde_run


def _facts(source, bank_row, tilde_run, line_id):
    """The third return of caption_for, as fields rather than a prefix the
    caller would have to re-parse out of the reason string. The tally reads
    these; the reason string is for a human reading the evidence file, and the
    two must agree because they are built in the same place."""
    return {"source": source, "bankRow": bank_row,
            "tildeRun": bool(tilde_run), "lineId": line_id}


def caption_for(keys_rows, bank_lines, basename):
    """(text, reason, facts) for one frame.

    text is None when this frame carries no words, which is the ordinary case
    and NOT an error: the second window's consequence is that nobody speaks of
    it. text is False when the frame REFUSES.

    WHAT WAS SAID OUTRANKS WHAT WOULD HAVE BEEN SAID. `lineText` on the row is
    the sentence the simulation actually spoke (a composed telling is not in
    the bank and never can be), so it is preferred whenever it is present and
    non-empty, and the bank lookup by `lineId` is the fallback for a row that
    carries no words of its own. The reason names which of the two answered
    EVERY time, in both directions, so a frame captioned from the bank can
    never read like a frame captioned from what was said.

    A `heard=yes` frame with no usable lineText AND an id the bank does not
    carry is the case that REFUSES, with the id in the reason. A frame that HAS
    a spoken sentence does not refuse over its id, because nothing went
    missing: the words are on the row."""
    row = keys_rows.get(basename)
    if row is None:
        return None, "nowords/no-keys-line-for-this-frame", _facts(
            "nowords", "none", False, "none")
    if row.get("heard") != "yes":
        return None, _nospace("nowords/heard..%s" % row.get("heard", "absent")), _facts(
            "nowords", "none", False, _nospace(row.get("lineId", "none")))

    line_id = row.get("lineId", "") or "none"
    raw = row.get("lineText")
    escape = row.get("lineTextEscape", "")
    spoken, tilde_run, why_not_spoken = None, False, ""
    if raw is None:
        why_not_spoken = "lineText..absent-key"
    elif raw in LINE_TEXT_ABSENT_TOKENS:
        why_not_spoken = ("lineText..empty-value" if raw == ""
                          else "lineText..none-sentinel")
    elif escape and escape != LINE_TEXT_ESCAPE:
        # REFUSES RATHER THAN GUESSING THE RULE. An un-escape by the wrong rule
        # burns a mangled sentence, which is the same class of fault as burning
        # the wrong sentence, and falling back to the bank here would burn the
        # row this beat no longer speaks.
        return False, _nospace("refused/lineText-escape-unknown..%s"
                               "/this-tool-implements..%s" % (escape, LINE_TEXT_ESCAPE)), \
            _facts("refused", "unread", False, line_id)
    else:
        candidate, tilde_run = unescape_line_text(raw)
        if candidate.strip() == "":
            # A VALUE OF NOTHING BUT TILDES paints an empty strip on a frame
            # somebody is speaking on, which reads as "nobody said anything".
            why_not_spoken = "lineText..only-tildes-unescapes-to-blank"
        else:
            spoken = candidate

    if spoken is not None:
        src = _nospace(row.get("lineTextSource", "") or "absent-key")
        bank_text = bank_lines.get(line_id) if line_id != "none" else None
        if bank_text is None:
            bank_row, said = "absent", "bank-row-absent"
        elif bank_text == spoken:
            bank_row, said = "agrees", "bank-row-agrees"
        else:
            # THE DISAGREEMENT IS THE INFORMATION: the composed line won, and
            # the row it differs from is named so the verdict's
            # overheardPickWouldHaveSaid can be matched against it.
            bank_row, said = "differed", "bank-row-differed"
        reason = "spoken/from-lineText/%s/id..%s/src..%s" % (said, line_id, src)
        if not escape:
            reason += "/escape..assumed-" + LINE_TEXT_ESCAPE
        if tilde_run:
            reason += "/tilde-run..suspect-see-clipCaptionTildeRuns"
        return spoken, _nospace(reason), _facts("spoken", bank_row, tilde_run, line_id)

    if line_id == "none":
        return None, _nospace("nowords/heard..yes-but-no-lineId-and-%s"
                              % why_not_spoken), _facts(
            "nowords", "none", tilde_run, line_id)
    if line_id not in bank_lines:
        return False, _nospace("bank-has-no-line-id:%s/and-%s"
                               % (line_id, why_not_spoken)), _facts(
            "refused", "absent", tilde_run, line_id)
    return bank_lines[line_id], _nospace(
        "bank/from-lineId-lookup/id..%s/%s" % (line_id, why_not_spoken)), _facts(
        "bank", "used", tilde_run, line_id)


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
          max_bytes=DEFAULT_MAX_BYTES, frame_keys=None, bank=None,
          sample_out=None):
    """Returns (ok, fields). fields carries EVERY key in FIELD_ORDER on every
    call, whichever branch answered, so a caller printing the line never has
    to guess which keys a given outcome left out.

    sample_out, when a list is passed, receives ONE DICT PER FRAME THAT CARRIED
    WORDS, for the caller to print as its own lines. The per-frame facts do not
    go into fields: fields is the done line, and a per-sample number under a
    whole-run key is the pair a grep silently merges."""
    paths = sorted(glob.glob(pattern))
    examined = len(paths)
    fields = {
        "clipStatus": "NOTHING-MEASURED", "clipReason": "not-attempted",
        "clipFramesExamined": examined, "clipFramesUsed": 0,
        "clipWidth": 0, "clipHeight": 0,
        "clipDurationMs": duration_ms, "clipScale": scale,
        # _nospace ON THE PATH: every other value in this dict is built from
        # tokens that cannot contain a space, and this one is whatever the
        # caller passed. A reader splitting on whitespace would take the half
        # after the space as a key with no `=` and drop it silently.
        "clipBytes": 0, "clipMaxBytes": max_bytes, "clipOut": _nospace(out_path),
        # NEVER-ATTEMPTED PRINTS THE WORDS, not a zero: a clip nobody asked
        # to caption and a clip whose captions all failed are different
        # facts with different next actions (rule 3b).
        "clipCaptionedFrames": "nothing-measured",
        "clipCaptionReason": "no-frame-keys-file-given",
        "clipCaptionTextPx": 0, "clipCaptionFont": "none",
        "clipCaptionLinesDropped": "0/0-wrapped",
        "clipCaptionKeysRead": 0, "clipCaptionBankRead": 0,
        # THE WORDS, NOT A ZERO, FOR ALL THREE. "no frame was captioned from
        # what the simulation said" and "nobody asked for captions" are
        # different facts, and `spoken..0` would read as the first.
        "clipCaptionsBySource": "nothing-measured",
        "clipCaptionSpokenVsBank": "nothing-measured",
        "clipCaptionTildeRuns": "nothing-measured",
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
        ok_caption, reason = _apply_captions(resized, paths, frame_keys, bank,
                                             fields, sample_out)
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


def _apply_captions(resized, paths, frame_keys, bank, fields, sample_out=None):
    """Burns the words onto the frames whose keys line says `heard=yes`: the
    sentence on the row when it carries one, the bank row for its lineId when
    it does not. Returns (ok, reason) and fills every clipCaption* field.

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

    # ALL CUMULATIVE OVER THE FRAMES THIS CALL EXAMINED, one bucket per frame,
    # because caption_for returns exactly one source for every frame it is
    # asked about.
    spoken_n = bank_n = nowords_n = 0
    differed = agreed = tilde_runs = 0
    captioned, dropped, wrapped = 0, 0, 0
    for img, path in zip(resized, paths):
        name = os.path.basename(path)
        text, reason, facts = caption_for(keys_rows, bank_lines, name)
        if text is False:
            # THE DENOMINATOR IS CAPTURED AT THE INSTANT THE RUN STOPS and is
            # NAMED for that moment: the frames after this one were never
            # classified, so `examined..len(paths)` would be a count of a set
            # nobody looked at.
            # clipCaptionedFrames KEEPS THE WHOLE CLIP AS ITS DENOMINATOR on
            # this path (N captioned of the clip's M frames, which is what it
            # has always meant); the keys below name the moment instead, and a
            # reader must not merge the two denominators.
            fields["clipCaptionedFrames"] = "%d/%d" % (captioned, len(paths))
            fields["clipCaptionReason"] = reason
            fields["clipCaptionLinesDropped"] = ("%d/%d-wrapped-atRefusal"
                                                 % (dropped, wrapped))
            fields["clipCaptionsBySource"] = (
                "spoken..%d/bank..%d/nowords..%d/refused..1/examinedAtRefusal..%d"
                % (spoken_n, bank_n, nowords_n,
                   spoken_n + bank_n + nowords_n + 1))
            fields["clipCaptionSpokenVsBank"] = (
                "differed..%d/agreed..%d/comparable..%d"
                % (differed, agreed, differed + agreed))
            fields["clipCaptionTildeRuns"] = ("runs..%d/spoken..%d"
                                              % (tilde_runs, spoken_n))
            if sample_out is not None:
                sample_out.append({"frame": name, "source": "refused",
                                   "reason": reason, "text": None,
                                   "shown": 0, "wrapped": 0})
            return False, reason
        if text is None:
            nowords_n += 1
            continue
        _, shown, total = burn_caption(img, text, font, line_px)
        captioned += 1
        wrapped += total
        dropped += total - shown
        if facts["source"] == "spoken":
            spoken_n += 1
            if facts["bankRow"] == "differed":
                differed += 1
            elif facts["bankRow"] == "agrees":
                agreed += 1
            # ON SPOKEN FRAMES ONLY, which is what the denominator beside it
            # counts. A tilde run on a row whose caption came from the bank is
            # named in that row's own reason instead of counted against a
            # denominator it is not a member of.
            if facts["tildeRun"]:
                tilde_runs += 1
        else:
            bank_n += 1
        if sample_out is not None:
            sample_out.append({"frame": name, "source": facts["source"],
                               "reason": reason, "text": text,
                               "shown": shown, "wrapped": total})
    fields["clipCaptionedFrames"] = "%d/%d" % (captioned, len(paths))
    fields["clipCaptionReason"] = "none"
    # CUMULATIVE OVER EVERY CAPTIONED FRAME, named so: this is the cap on
    # the strip announcing itself, and a non-zero numerator means words a
    # viewer will never read.
    fields["clipCaptionLinesDropped"] = "%d/%d-wrapped" % (dropped, wrapped)
    # WHOLE-RUN, CUMULATIVE, AND A PARTITION BY CONSTRUCTION: spoken + bank +
    # nowords + refused == examined, because every frame gets exactly one
    # source. spoken + bank is clipCaptionedFrames' numerator split a second
    # way, not a second measurement of it.
    fields["clipCaptionsBySource"] = (
        "spoken..%d/bank..%d/nowords..%d/refused..0/examined..%d"
        % (spoken_n, bank_n, nowords_n, len(paths)))
    # CUMULATIVE OVER THE FRAMES WHERE BOTH A SPOKEN SENTENCE AND A BANK ROW
    # EXISTED, which is the only set where a disagreement is a fact at all:
    # comparable..0 means nothing was comparable, NOT that everything agreed.
    fields["clipCaptionSpokenVsBank"] = (
        "differed..%d/agreed..%d/comparable..%d"
        % (differed, agreed, differed + agreed))
    fields["clipCaptionTildeRuns"] = "runs..%d/spoken..%d" % (tilde_runs, spoken_n)
    return True, "none"


def format_sample_lines(samples, cap=SAMPLE_LINE_CAP, text_cap=SAMPLE_TEXT_CAP):
    """The per-frame lines: one per frame that carried words, then a final line
    that ALWAYS says whether the cap bit and over what.

    WHY ONLY THE FRAMES THAT CARRIED WORDS. The live keys file is 17 silent
    rows to 8 speaking ones, and a line per silent frame would bury the ones
    that matter in the evidence file. The silent frames are counted on the done
    line instead (clipCaptionsBySource nowords..N), which is where a whole-run
    number belongs.

    THE CAP ANNOUNCES ITSELF IN A CHANNEL THAT ALLOWS NO SPACES, so the
    canonical `(+N more not shown)` is written `+N-more-not-shown`, and the
    sentence echoed back carries its own cap the same way."""
    out = []
    if not samples:
        return out
    for s in samples[:cap]:
        if s["text"] is None:
            echo = "none"
        else:
            # THE SENTENCE THAT WAS BURNED, ESCAPED THE WAY IT ARRIVED, so the
            # evidence file and the frame carry the same string and a reader
            # can diff the caption against overheardTellText without pixels.
            echo = tilde_escape(s["text"])
            if len(echo) > text_cap:
                echo = echo[:text_cap] + ("/+%d-chars-not-shown"
                                          % (len(echo) - text_cap))
        out.append("clipframe frame=%s captionSource=%s captionReason=%s "
                   "captionTextTilde=%s captionLines=shown..%d/wrapped..%d"
                   % (_nospace(s["frame"]), _nospace(s["source"]),
                      _nospace(s["reason"]), _nospace(echo),
                      s["shown"], s["wrapped"]))
    shown_rows = min(len(samples), cap)
    out.append("clipframe capBit=%s capNote=shownRows..%d/withWordsRows..%d"
               "/+%d-more-not-shown/capIs..%d"
               % ("yes" if len(samples) > cap else "no", shown_rows,
                  len(samples), len(samples) - shown_rows, cap))
    return out


def report(pattern, out_path, scale, duration_ms, max_bytes,
           frame_keys=None, bank=None):
    samples = []
    ok, fields = build(pattern, out_path, scale, duration_ms, max_bytes,
                       frame_keys, bank, sample_out=samples)
    # PER-FRAME LINES FIRST, THE DONE LINE LAST. instruments.md: whole-run
    # numbers on the done line, per-sample numbers on the sample line, and
    # never one key carrying both moments. A run with no captions at all emits
    # no clipframe lines and says so on the done line instead.
    for line in format_sample_lines(samples):
        print(line)
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
    outcomes and only a planted case tells them apart.

    THE CAPTION SECTIONS FOLLOW THE SAME ORDER. For the lineText preference
    added 2026-09-08 the accepting case is first (a row carrying the words
    captions from them, spaces restored), then the regression it must not cause
    (a row with no lineText still captions from the bank), then the refusal that
    must survive (no lineText and an id the bank lacks), then the planted
    disagreement, then the four shapes the ~ un-escape can meet. The live keys
    file and the live bank are accepting fixtures and PRINT what they found."""
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
        # THE DENOMINATOR AT THE MOMENT THE RUN STOPPED, not the whole clip:
        # frame 002 was never classified, so counting it as examined would be a
        # count of a set nobody looked at.
        check("rejecting: the by-source counts name the moment they stopped at",
              fields["clipCaptionsBySource"]
              == "spoken..0/bank..0/nowords..1/refused..1/examinedAtRefusal..2")
        check("rejecting: the wrapped lines so far are named at-refusal too",
              fields["clipCaptionLinesDropped"].endswith("-wrapped-atRefusal"))

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

        # ---- THE WORDS ON THE ROW OUTRANK THE BANK, ACCEPTING CASE FIRST.
        #
        # THE DISAGREEMENT IS PLANTED, NOT HOPED FOR. Frame 001 carries a
        # composed telling that is NOT the bank row for its id, which is the
        # exact fault this section fixes; frame 002 carries a lineText that IS
        # its bank row word for word, so the agrees branch runs too and
        # `differed` cannot pass by counting everything it sees.
        spoken_line = ("You hear all sorts. He looked straight at me before he "
                       "ran, apparently.")
        agreeing_line = "Then you want to keep that to yourself."
        sp_keys = os.path.join(tmp, "keys-spoken.txt")
        with open(sp_keys, "w", encoding="utf-8") as fh:
            fh.write("# synthetic keys file WITH the words on the row\n")
            fh.write("frame=ue-crimeseq_000.png beat=deed_a speaker=none lineId=none "
                     "lineText=none lineTextSource=none/this-frame-carries-no-words "
                     "lineTextEscape=spaces-are-~ heard=no\n")
            fh.write("frame=ue-crimeseq_001.png beat=overheard speaker=w1 "
                     "lineId=test-ws-01 lineText=%s "
                     "lineTextSource=composed/StreetVoice.Exchange-around-the-carried-summary "
                     "lineTextEscape=spaces-are-~ heard=yes\n" % tilde_escape(spoken_line))
            fh.write("frame=ue-crimeseq_002.png beat=overheard speaker=n2 "
                     "lineId=test-ov-01 lineText=%s "
                     "lineTextSource=picked/the-hearer-s-own-disposition-band/not-the-bank-s-rung "
                     "lineTextEscape=spaces-are-~ heard=yes\n" % tilde_escape(agreeing_line))

        sp_rows, sp_examined, sp_err = read_frame_keys(sp_keys)
        sel_bank, _, _ = read_bank(bank_path)
        t1, r1, f1 = caption_for(sp_rows, sel_bank, "ue-crimeseq_001.png")
        check("accepting (spoken): the sentence comes back with its spaces, exactly",
              t1 == spoken_line and not sp_err and sp_examined == 3)
        check("accepting (spoken): the reason names the source, the id and the provenance",
              r1 == "spoken/from-lineText/bank-row-differed/id..test-ws-01"
                    "/src..composed/StreetVoice.Exchange-around-the-carried-summary")
        check("accepting (spoken): the source is a fact, not a prefix to re-parse",
              f1["source"] == "spoken" and f1["bankRow"] == "differed")
        check("planted: the bank row for that id is NOT what was said, and what was "
              "said is what came back", sel_bank["test-ws-01"] != t1)
        t2, r2, f2 = caption_for(sp_rows, sel_bank, "ue-crimeseq_002.png")
        check("accepting (spoken): a lineText equal to its bank row reads as agrees",
              t2 == agreeing_line and f2["bankRow"] == "agrees"
              and r2 == "spoken/from-lineText/bank-row-agrees/id..test-ov-01"
                        "/src..picked/the-hearer-s-own-disposition-band/not-the-bank-s-rung")

        # THE REGRESSION THIS CHANGE MUST NOT CAUSE: the original fixture rows
        # carry no lineText at all, and must caption from the bank exactly as
        # they did before tonight.
        nolt_rows, _, _ = read_frame_keys(keys_path)
        tb, rb, fb = caption_for(nolt_rows, sel_bank, "ue-crimeseq_001.png")
        check("accepting (bank, the regression): a row with no lineText still "
              "captions from the bank, word for word",
              tb == sel_bank["test-ws-01"] and fb["source"] == "bank")
        check("accepting (bank): the reason says bank and says why it fell back",
              rb == "bank/from-lineId-lookup/id..test-ws-01/lineText..absent-key")
        check("accepting: a bank caption cannot read like a spoken one",
              rb.split("/")[0] == "bank" and r1.split("/")[0] == "spoken")

        # THE REFUSAL THAT MUST SURVIVE: no lineText, and an id the bank lacks.
        badk_rows, _, _ = read_frame_keys(bad_keys)
        tr, rr, fr = caption_for(badk_rows, sel_bank, "ue-crimeseq_001.png")
        check("rejecting: no lineText and an id the bank lacks still REFUSES with "
              "the id in the reason",
              tr is False and "cw-ws-r9-99" in rr and fr["source"] == "refused")

        # ---- THE FOUR THINGS THE ~ UN-ESCAPE CAN MEET, through the real
        # parser (read_frame_keys), because a second parser written here would
        # be a second place to fix when the first one is wrong.
        edge_keys = os.path.join(tmp, "keys-edges.txt")
        with open(edge_keys, "w", encoding="utf-8") as fh:
            fh.write("frame=tilde.png beat=overheard speaker=w1 lineId=test-ws-01 "
                     "lineText=He~said~~tilde~here. lineTextSource=composed/x "
                     "lineTextEscape=spaces-are-~ heard=yes\n")
            fh.write("frame=empty.png beat=overheard speaker=w1 lineId=test-ws-01 "
                     "lineText= lineTextSource=composed/x "
                     "lineTextEscape=spaces-are-~ heard=yes\n")
            fh.write("frame=tildesonly.png beat=overheard speaker=w1 lineId=test-ws-01 "
                     "lineText=~~~ lineTextSource=composed/x "
                     "lineTextEscape=spaces-are-~ heard=yes\n")
            fh.write("frame=equals.png beat=overheard speaker=n2 lineId=test-ov-01 "
                     "lineText=2~+~2~=~4,~he~said. lineTextSource=composed/x "
                     "lineTextEscape=spaces-are-~ heard=yes\n")
            fh.write("frame=noid.png beat=overheard speaker=w1 lineId=none "
                     "lineText=none lineTextSource=none/x "
                     "lineTextEscape=spaces-are-~ heard=yes\n")
            fh.write("frame=otherescape.png beat=overheard speaker=w1 "
                     "lineId=test-ws-01 lineText=He~said~it lineTextSource=composed/x "
                     "lineTextEscape=spaces-are-underscore heard=yes\n")
            # THE ONE PLACE BEHAVIOUR NARROWED, pinned so it cannot drift back:
            # a row that HAS the words does not refuse over an id the bank
            # lacks, because nothing went missing. The refusal is for the row
            # with no words AND no bank row, which is still tested above.
            fh.write("frame=spokenbutnoid.png beat=overheard speaker=w1 "
                     "lineId=cw-ws-r9-99 lineText=He~said~it~himself. "
                     "lineTextSource=composed/x lineTextEscape=spaces-are-~ heard=yes\n")
        ed, ed_examined, _ = read_frame_keys(edge_keys)
        check("edge fixture: all seven rows parsed", ed_examined == 7 and len(ed) == 7)
        te, re_t, fe = caption_for(ed, sel_bank, "tilde.png")
        check("edge (a real tilde): every ~ becomes one space, and the run says so",
              te == "He said  tilde here." and fe["tildeRun"] is True
              and re_t.endswith("/tilde-run..suspect-see-clipCaptionTildeRuns"))
        t_em, r_em, f_em = caption_for(ed, sel_bank, "empty.png")
        check("edge (an empty lineText): the bank answers and the empty value is named",
              t_em == sel_bank["test-ws-01"] and f_em["source"] == "bank"
              and r_em == "bank/from-lineId-lookup/id..test-ws-01/lineText..empty-value")
        t_ot, r_ot, f_ot = caption_for(ed, sel_bank, "tildesonly.png")
        check("edge (only tildes): blank is not a caption, so the bank answers and "
              "the blankness is named",
              t_ot == sel_bank["test-ws-01"] and f_ot["source"] == "bank"
              and r_ot == "bank/from-lineId-lookup/id..test-ws-01"
                          "/lineText..only-tildes-unescapes-to-blank")
        t_eq, r_eq, f_eq = caption_for(ed, sel_bank, "equals.png")
        check("edge (a lineText carrying an = sign): it survives the parser intact",
              t_eq == "2 + 2 = 4, he said." and f_eq["source"] == "spoken")
        t_ni, r_ni, f_ni = caption_for(ed, sel_bank, "noid.png")
        check("edge (heard=yes, no words, no id): no caption, and the reason says "
              "both halves",
              t_ni is None and f_ni["source"] == "nowords"
              and r_ni == "nowords/heard..yes-but-no-lineId-and-lineText..none-sentinel")
        t_oe, r_oe, f_oe = caption_for(ed, sel_bank, "otherescape.png")
        check("rejecting: an escape this tool does not implement refuses, naming it",
              t_oe is False and "spaces-are-underscore" in r_oe
              and f_oe["source"] == "refused")
        t_sn, r_sn, f_sn = caption_for(ed, sel_bank, "spokenbutnoid.png")
        check("accepting (the one narrowing): words on the row and an id the bank "
              "lacks captions from the words and does not refuse",
              t_sn == "He said it himself." and f_sn["source"] == "spoken"
              and r_sn == "spoken/from-lineText/bank-row-absent/id..cw-ws-r9-99"
                          "/src..composed/x")

        # ---- THE DONE LINE AND THE FRAMES, TOGETHER. A caption requested is
        # not a caption on the frame: the strip's own pixels decide (rule 4),
        # and the two GIFs differ in exactly one thing, which row the words
        # came from.
        sp_samples = []
        sp_out = os.path.join(tmp, "cap-spoken.gif")
        sp_ok, sp_fields = build(os.path.join(cap_dir, "ue-crimeseq_*.png"), sp_out,
                                 0.5, 100, 8 * 1024 * 1024, frame_keys=sp_keys,
                                 bank=bank_path, sample_out=sp_samples)
        check("accepting (done line): the four sources partition the frames examined",
              sp_ok and sp_fields["clipCaptionsBySource"]
              == "spoken..2/bank..0/nowords..1/refused..0/examined..3")
        check("accepting (done line): spoken plus bank IS the captioned numerator",
              sp_fields["clipCaptionedFrames"] == "2/3")
        check("accepting (done line): the disagreement is counted with its own "
              "denominator",
              sp_fields["clipCaptionSpokenVsBank"]
              == "differed..1/agreed..1/comparable..2")
        check("accepting (done line): the tilde runs are counted over spoken frames",
              sp_fields["clipCaptionTildeRuns"] == "runs..0/spoken..2")
        sp_done = "clip " + " ".join("%s=%s" % (k, sp_fields[k]) for k in FIELD_ORDER)
        check("accepting (done line): every key present and no value carries a space",
              len(sp_done.split()) == 1 + len(FIELD_ORDER))
        check("accepting (pixels): the strip burned from what was SAID is not the "
              "strip burned from the bank row",
              cap_ok and sp_ok and strip_bytes(cap_out, 1) != strip_bytes(sp_out, 1))
        check("accepting (pixels): the frame whose lineText equals its bank row "
              "burns the identical strip",
              cap_ok and sp_ok and strip_bytes(cap_out, 2) == strip_bytes(sp_out, 2))
        none_fields = build(os.path.join(cap_dir, "ue-crimeseq_*.png"),
                            os.path.join(tmp, "cap-none2.gif"), 0.5, 100,
                            8 * 1024 * 1024)[1]
        check("accepting: a run that captioned nothing prints the words on all three",
              none_fields["clipCaptionsBySource"] == "nothing-measured"
              and none_fields["clipCaptionSpokenVsBank"] == "nothing-measured"
              and none_fields["clipCaptionTildeRuns"] == "nothing-measured")

        # ---- THE PER-FRAME LINES, which are where the reasons reach a reader.
        sp_lines = format_sample_lines(sp_samples)
        check("accepting (sample lines): one line per frame that carried words, "
              "plus the cap line", len(sp_lines) == 3)
        check("accepting (sample lines): the burned sentence is echoed back escaped, "
              "so the evidence file carries the words the frame carries",
              ("captionTextTilde=" + tilde_escape(spoken_line)) in sp_lines[0])
        # SIX TOKENS AND THREE: `clipframe` plus its five keys, and `clipframe`
        # plus the cap's two. A value that leaked a space would split into a
        # seventh token and the reader after it would drop the remainder.
        check("accepting (sample lines): no value on any of them carries a space",
              all(len(ln.split()) == 6 for ln in sp_lines[:2])
              and len(sp_lines[2].split()) == 3)
        check("accepting (sample lines): the cap says it did not bite, with its "
              "denominator",
              sp_lines[2] == "clipframe capBit=no capNote=shownRows..2"
                             "/withWordsRows..2/+0-more-not-shown/capIs..16")
        check("accepting (sample lines): a run with no captions emits none at all",
              format_sample_lines([]) == [])
        many = [{"frame": "f_%03d.png" % i, "source": "spoken", "text": "a sentence",
                 "reason": "spoken/from-lineText/bank-row-differed/id..x/src..composed/y",
                 "shown": 1, "wrapped": 1} for i in range(SAMPLE_LINE_CAP + 4)]
        many_lines = format_sample_lines(many)
        check("planted: more with-words frames than the cap, and the cap announces it",
              len(many_lines) == SAMPLE_LINE_CAP + 1
              and many_lines[-1] == "clipframe capBit=yes capNote=shownRows..16"
                                    "/withWordsRows..20/+4-more-not-shown/capIs..16")
        long_echo = format_sample_lines([{"frame": "f.png", "source": "spoken",
                                          "reason": "spoken/x",
                                          "text": ("word " * 80).strip(),
                                          "shown": 1, "wrapped": 1}])
        check("planted: a sentence longer than the echo cap says how much it lost",
              "-chars-not-shown" in long_echo[0]
              and "/+%d-chars-not-shown" % (399 - SAMPLE_TEXT_CAP) in long_echo[0])

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
            # THE SERIES PRINTS WHETHER OR NOT THE CHECK PASSES. A check name
            # carrying the numbers is only read on a failure, and the margin
            # between the worst line and the strip is the number somebody will
            # want before they widen a caption (rule 2: print the series first).
            print("clipselftest liveBank=content/dialogue/crime-witness-v1.json"
                  " bankLinesRead=%d worstWrapLines=%d stripHoldsLines=%d"
                  " worstId=%s marginLinesSpare=%d"
                  % (examined, worst, room, _nospace(worst_id), room - worst))
        else:
            check("live bank absent, so nothing measured about it", True)

        # ---- THE LIVE KEYS FILE IS AN ACCEPTING FIXTURE TOO, AND IT IS
        # SHAPE-AGNOSTIC ON PURPOSE. Tonight's committed file (run 5ea6cb0)
        # carries no lineText and the next run's will carry one on every
        # speaking row, so this asserts only what must hold in BOTH shapes:
        # every speaking row resolves to a non-empty sentence from a named
        # source and nothing refuses. It PRINTS the mix it found in the check
        # name rather than pinning it, because pinning a live asset's current
        # shape is how doing the work breaks the tool.
        live_keys = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "production", "d1-probe",
            "ue-crimeseq-keys.txt")
        if os.path.exists(live_keys) and os.path.exists(live_bank):
            lrows, lexamined, lerr = read_frame_keys(live_keys)
            lbank, lbank_n, _ = read_bank(live_bank)
            mix = {"spoken": 0, "bank": 0, "nowords": 0, "refused": 0}
            blank = 0
            for nm in sorted(lrows):
                lt, lr, lf = caption_for(lrows, lbank, nm)
                mix[lf["source"]] += 1
                if lf["source"] in ("spoken", "bank") and not str(lt).strip():
                    blank += 1
            check("accepting (live keys): %d row(s) read against %d bank line(s), "
                  "mix spoken..%d/bank..%d/nowords..%d/refused..%d, blank..%d"
                  % (lexamined, lbank_n, mix["spoken"], mix["bank"],
                     mix["nowords"], mix["refused"], blank),
                  not lerr and lexamined > 0 and mix["refused"] == 0 and blank == 0
                  and (mix["spoken"] + mix["bank"]) > 0)
            # AND THE LIVE MIX PRINTS EVERY RUN, because which source the real
            # file resolves through is the fact this change is about, and it
            # will change shape on the next probe run.
            print("clipselftest liveKeys=production/d1-probe/ue-crimeseq-keys.txt"
                  " rowsRead=%d bankLinesRead=%d"
                  " mix=spoken..%d/bank..%d/nowords..%d/refused..%d/rows..%d"
                  " blankCaptions=%d"
                  % (lexamined, lbank_n, mix["spoken"], mix["bank"],
                     mix["nowords"], mix["refused"], len(lrows), blank))
        else:
            check("live keys file absent, so nothing measured about it", True)
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
