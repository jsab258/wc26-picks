#!/usr/bin/env python3
"""THE OUTBOX: a Producer message on disk becomes a message on Jafar's phone.

    python3 tools/runner/outbox.py --selftest   # offline, scripted stand-in
    python3 tools/runner/telegram-bot.py --send-outbox   # one real sweep
    python3 tools/runner/telegram-bot.py --send-frame    # one real picture

WHAT THIS IS. The PC half of the OUTBOUND path, queue 089 and queue 091. The
container writes a message into `production/outbox/` and commits it; the
watcher's checkout on Jafar's PC gets it at the next resync; this sweeps that
directory, runs the register check, sends only on a pass, and writes a receipt
that travels back to the studio on the `pc-inbox` branch built for queue 088.

THE CHECK RUNS HERE, ON THE SENDING SIDE, and that is the point of the file
rather than a detail of it. A check that runs in the container and trusts this
PC to have honoured it is not a check. Every send in this module is preceded by
`tools/producer-check.py --kind <kind> <file>` in a subprocess on this machine,
and a refusal is loud: it is counted, printed, and written back into the tree
as a record carrying the failing clause, because an unsendable Producer message
that nobody learns about is a message that silently never arrived.

THE KIND COMES FROM THE NAME AND IS NEVER GUESSED. The three registers enforce
different rules, so a file whose kind had to be inferred would be checked
against rules its writer never agreed to. A name carrying no recognised suffix
is REFUSED, naming all three, exactly as `production/outbox/README.md` rules
and as `tools/producer-check.py:gate_kind` does.

IDEMPOTENCE IS BY RECEIPT, NEVER BY DELETING THE FILE. The README is explicit
that a sent message STAYS in the outbox, so "no file" can never mean "sent".
The receipt is the record, it names the message id the platform returned, and a
receipt with no id is not a receipt: it is refused, and the file it belongs to
is held rather than sent again, because sending a Producer message into his
chat twice is worse than sending it late.

WHAT IS NOT WIRED HERE ON PURPOSE. The bot's own chrome (its opening line, the
budget question, the read-backs) does NOT go through this path. That text fails
the register by construction, and `send()` in the bot stays uncheckable text
while THIS module owns the Producer content class. Ruled 2026-09-05; getting it
backwards makes the bot unusable.

NO DEPENDENCY, standard library only, like the bot and the inbox.

WHAT CANNOT BE TESTED HERE. Telegram is unreachable from the build container,
so every case in `--selftest` runs against a scripted stand-in that returns
what the platform's own documented payload looks like. The wire itself is
UNVERIFIABLE UNTIL THE PC.
"""
import datetime
import hashlib
import os
import re
import subprocess
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import inbox                                                   # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))

#: Where the Producer writes. Same string as `producer-check.py:GATE_TREES[0]`,
#: and the selftest asserts the two agree rather than trusting this copy.
OUTBOX_DIR = "production/outbox"

#: Where a receipt or a refusal lands. `inbox.py` owns the constant because it
#: owns the transport that carries it.
OUTBOUND_DIR = inbox.OUTBOUND_DIR

#: THE THREE REGISTERS, longest suffix first so `.brief.md` and `.md` cannot
#: race. Duplicated from `producer-check.py` rather than imported at module
#: level because that file's name carries a hyphen; the selftest imports it by
#: path and fails if these two lists ever drift apart.
KIND_SUFFIX = ((".unprompted.md", "unprompted"),
               (".answer.md", "answer"),
               (".brief.md", "brief"))

#: Documentation, not a message. Named rather than pattern-matched, and the
#: count is printed, so this cannot grow quietly into a hole.
NOT_A_MESSAGE = ("README.md",)

#: TELEGRAM'S OWN LIMITS, both of them announced when they bite.
#: 10 MB is the documented ceiling on a photo uploaded by a bot, and 1024 is
#: the documented caption limit. A file over the first is refused WITH ITS
#: MEASURED SIZE rather than truncated or silently dropped.
PHOTO_MAX_BYTES = 10 * 1024 * 1024
CAPTION_CAP = 1024

#: TELEGRAM'S DOCUMENTED CEILING FOR A VIDEO UPLOADED BY A BOT VIA MULTIPART
#: (as opposed to a URL Telegram fetches itself, which this project never
#: does). Ruling 1, 2026-09-07: the automated playtest step's clip "goes to
#: Telegram with a one-line verdict". A clip over this is refused WITH ITS
#: MEASURED SIZE, exactly as an oversized photo is: never attempted, never
#: silently dropped by the platform's own limit.
VIDEO_MAX_BYTES = 50 * 1024 * 1024

#: RULING 5, 2026-09-07, VERBATIM: "let the photo path carry a caption for a
#: test request... rather than sending text without the picture." A message
#: NAMES the picture it wants to carry in a SIDECAR file beside it, never in
#: a line inside the message body: the body is exactly what producer-check
#: reads and exactly what becomes the caption, and a path typed into that
#: body would trip the "file path" entry of BANNED in
#: tools/producer-check.py, which every register enforces. One file names
#: the picture, one file is the message, and stripping a special line back
#: out of the body would be a second parser for the register to disagree
#: with about what the writer actually wrote.
PHOTO_REF_SUFFIX = ".photo.txt"

#: How much of the check's output is carried in a refusal record's clause.
CLAUSE_CAP = 400

#: The evidence link that rides behind the caption sentence, constitution law
#: 12. Built from this repository's own remote, which is
#: https://github.com/jsab258/wc26-picks.
REPO_BLOB = "https://github.com/jsab258/wc26-picks/blob/main"

SHOTS_DIR = "game-design/sim-shots"


# --------------------------------------------------------------------------
# The name, the kind, and what is in the outbox
# --------------------------------------------------------------------------
def kind_of_name(name):
    """(kind, why) or (None, why-not). The refusal names all three suffixes.

    Guessing is the failure this exists to prevent: guessing `unprompted`
    would reject a long answer that is perfectly legal, and guessing `answer`
    would wave through an unprompted message with no shape at all.
    """
    base = name.rsplit("/", 1)[-1]
    for suffix, kind in KIND_SUFFIX:
        if base.endswith(suffix):
            return kind, "filename suffix %s" % suffix
    return None, ("the name carries no register, so nothing can be checked "
                  "against the right rules: end it %s"
                  % ", ".join(s for s, _ in KIND_SUFFIX))


def outbox_files(repo):
    """Every candidate message under the outbox, sorted, README excluded.

    RECURSIVE, because the README rules that `production/outbox/sent/` is a
    legal place for a message to sit and the gate walks it. A file with no
    recognised kind is NOT filtered out here: it is returned so the sweep can
    refuse it out loud. Filtering it would be the silent skip this whole path
    exists to remove.
    """
    root = os.path.join(repo, *OUTBOX_DIR.split("/"))
    found = []
    for dirpath, _dirs, names in os.walk(root):
        for n in sorted(names):
            if not n.endswith(".md") or n in NOT_A_MESSAGE:
                continue
            full = os.path.join(dirpath, n)
            found.append(os.path.relpath(full, repo).replace(os.sep, "/"))
    return sorted(found)


def record_base(rel):
    """The stem an outbound record for this message is named from."""
    return rel.rsplit("/", 1)[-1][:-len(".md")] if rel.endswith(".md") \
        else rel.rsplit("/", 1)[-1]


def receipt_rel(rel):
    return "%s/%s.receipt.txt" % (OUTBOUND_DIR, record_base(rel))


def refusal_rel(rel, clause):
    """A refusal record, named from a hash of its own clause.

    WHY THE CLAUSE IS IN THE NAME. The transport pushes a file whose PATH the
    branch does not carry, so a fixed name would push the first refusal and
    then never push a changed one. Hashing the clause makes an unchanged
    refusal cost one push for ever and a CHANGED refusal a new record, which
    is the behaviour a reader of the branch needs.
    """
    h = hashlib.sha1(clause.encode("utf-8", "replace")).hexdigest()[:8]
    return "%s/%s.refused-%s.txt" % (OUTBOUND_DIR, record_base(rel), h)


def photo_receipt_rel(frame, run_sha, role):
    stem = frame[:-len(".jpg")] if frame.endswith(".jpg") else frame
    return "%s/%s-%s-%s.photo-receipt.txt" % (OUTBOUND_DIR, stem, run_sha,
                                              role)


def sidecar_rel(rel, suffix):
    """Same directory, same stem as the message, a different suffix.

    Sits BESIDE the message it names, in the OUTBOX tree (never
    OUTBOUND_DIR): it is written by whoever COMPOSES the message, not by the
    sender, exactly like the message itself. See PHOTO_REF_SUFFIX for why a
    sidecar exists at all rather than a line inside the body.
    """
    stem = rel[:-len(".md")] if rel.endswith(".md") else rel
    return stem + suffix


def photo_ref_rel(rel):
    """Where a message may NAME the picture it wants to carry as its
    caption. RULING 5, 2026-09-07."""
    return sidecar_rel(rel, PHOTO_REF_SUFFIX)


def video_receipt_rel(path, run_sha, role):
    """A receipt for a sent CLIP, ruling 1, 2026-09-07.

    THE SUFFIX IS `.receipt.txt`, THE SAME ONE A PLAIN MESSAGE USES, NOT A
    NEW ONE. `inbox.OUTBOUND_RE` in tools/runner/inbox.py is a fixed
    allowlist of three shapes (`receipt`, `refused-XXXXXXXX`,
    `photo-receipt`) and this file does not own that one: a fourth suffix
    here would be invisible to the container's own walker and a video
    receipt would silently never be read back. `receipt: video` INSIDE the
    file is what tells a reader apart from a plain text send, exactly as
    `receipt: photo` already does for a sim-shot picture sharing no special
    suffix of its own beyond `photo-receipt`. The filename only has to be
    UNIQUE per clip, which the run sha and the role make it.
    """
    stem = os.path.basename(path)
    for ext in (".mp4", ".mov", ".webm", ".mkv", ".m4v"):
        if stem.lower().endswith(ext):
            stem = stem[: -len(ext)]
            break
    stem = re.sub(r"[^A-Za-z0-9._-]", "-", stem) or "clip"
    return "%s/%s-%s-%s.receipt.txt" % (OUTBOUND_DIR, stem, run_sha, role)


# --------------------------------------------------------------------------
# The records. One implementation, written on the PC and read in the container.
# --------------------------------------------------------------------------
def render_receipt(rel, kind, sent_epoch, message_id, chars, commit_sha,
                   commit_epoch, latency, why_no_latency=""):
    """The proof that a message left this PC.

    NO TOKEN AND NO CHAT ID, ever, in anything this writes into git: the
    credential rule of 2026-09-04 applies to what is committed exactly as it
    applies to what is printed.
    """
    return ("receipt: sent\n"
            "file: %s\n"
            "kind: %s\n"
            "fileCommit: %s\n"
            "fileCommitEpoch: %s\n"
            "sent: %s\n"
            "sentEpoch: %d\n"
            "messageId: %d\n"
            "chars: %d\n"
            "outboundLatencySec: %s\n"
            "outboundLatencySecFrom: fileCommitInstant\n"
            "outboundLatencySecTo: sendInstant\n"
            "note: one sample of one message, not a rate.%s\n"
            % (rel, kind, commit_sha or "none",
               "none" if commit_epoch is None else int(commit_epoch),
               inbox.iso_utc(sent_epoch), int(sent_epoch), int(message_id),
               int(chars),
               "nothing-measured" if latency is None else int(latency),
               (" " + why_no_latency) if why_no_latency else ""))


def render_photo_receipt(frame, role, run_sha, path_bytes, sent_epoch,
                         message_id, sizes, caption_chars, capped):
    """The proof that a PICTURE left this PC as a picture.

    `photoSizes` IS THE ARTIFACT for arrived-as-a-photo. Telegram returns a
    `photo` array of rescaled sizes only when it accepted the upload AS a
    photo; a file it filed as a document comes back with no such array. So the
    descriptor is what tells the two apart, and a receipt without it is
    refused rather than believed.
    """
    return ("receipt: photo\n"
            "frame: %s\n"
            "role: %s\n"
            "runSha: %s\n"
            "bytes: %d\n"
            "sent: %s\n"
            "sentEpoch: %d\n"
            "messageId: %d\n"
            "photoSizes: %s\n"
            "photoSizeCount: %d\n"
            "captionChars: %d\n"
            "captionCapped: %s\n"
            % (frame, role, run_sha, int(path_bytes),
               inbox.iso_utc(sent_epoch), int(sent_epoch), int(message_id),
               sizes_key(sizes) or "none", len(sizes or []),
               int(caption_chars), "yes" if capped else "no"))


def render_captioned_receipt(rel, kind, photo_rel, sent_epoch, message_id,
                             chars, sizes, commit_sha, commit_epoch, latency,
                             why_no_latency=""):
    """The proof that a PRODUCER MESSAGE left this PC AS ONE CAPTIONED PHOTO.

    RULING 5, 2026-09-07: "let the photo path carry a caption for a test
    request... rather than sending text without the picture." This carries
    the SAME TWO PROOFS render_receipt and render_photo_receipt carry
    separately, on one record, because this one send is both things at
    once: a Producer message (fileCommit/outboundLatencySec, read the same
    way `outbound_summary` reads a plain "sent" record) AND an
    arrived-as-a-photo claim (photoSizes, the same descriptor
    render_photo_receipt trusts and nothing else). `receipt: sent-with-photo`
    is its own value so a reader can never confuse this with a plain text
    send or a sim-shot picture: three record shapes, three meanings, one
    reader (`outbound_summary`) that keys off this line rather than the
    filename.
    """
    return ("receipt: sent-with-photo\n"
            "file: %s\n"
            "kind: %s\n"
            "photoRef: %s\n"
            "fileCommit: %s\n"
            "fileCommitEpoch: %s\n"
            "sent: %s\n"
            "sentEpoch: %d\n"
            "messageId: %d\n"
            "chars: %d\n"
            "photoSizes: %s\n"
            "photoSizeCount: %d\n"
            "outboundLatencySec: %s\n"
            "outboundLatencySecFrom: fileCommitInstant\n"
            "outboundLatencySecTo: sendInstant\n"
            "note: one sample of one message, not a rate.%s\n"
            % (rel, kind, photo_rel, commit_sha or "none",
               "none" if commit_epoch is None else int(commit_epoch),
               inbox.iso_utc(sent_epoch), int(sent_epoch), int(message_id),
               int(chars), sizes_key(sizes) or "none", len(sizes or []),
               "nothing-measured" if latency is None else int(latency),
               (" " + why_no_latency) if why_no_latency else ""))


def render_video_receipt(path, role, sent_epoch, message_id, path_bytes,
                         descriptor, descriptor_kind, caption_chars):
    """The proof that a CLIP left this PC as a clip.

    RULING 1, 2026-09-07: the automated playtest step judges the build and
    "the clip goes to Telegram with a one-line verdict". `descriptorKind`
    NAMES WHICH FIELD THE PLATFORM ANSWERED WITH, "video" for sendVideo or
    "animation" for sendAnimation, because the two calls carry their
    arrived-proof under different keys and a receipt that guessed would be
    reading the wrong one silently. A send with NEITHER key populated is
    refused before this is ever called: see send_video.
    """
    return ("receipt: video\n"
            "file: %s\n"
            "role: %s\n"
            "bytes: %d\n"
            "sent: %s\n"
            "sentEpoch: %d\n"
            "messageId: %d\n"
            "descriptorKind: %s\n"
            "videoDescriptor: %s\n"
            "captionChars: %d\n"
            % (path, role, int(path_bytes), inbox.iso_utc(sent_epoch),
               int(sent_epoch), int(message_id), descriptor_kind or "none",
               video_descriptor_key(descriptor) or "none",
               int(caption_chars)))


def render_refusal(rel, kind, clause, when_epoch, hold, detail=""):
    return ("refused: %s\n"
            "file: %s\n"
            "kind: %s\n"
            "checked: %s\n"
            "checkedEpoch: %d\n"
            "hold: %s\n"
            "clause: %s\n"
            "detail: %s\n"
            % ("hold" if hold else "check", rel, kind or "none",
               inbox.iso_utc(when_epoch), int(when_epoch),
               "yes" if hold else "no", clause,
               inbox.one_line(detail, 600) if detail else "none"))


def parse_record(content):
    """(fields, None) or (None, reason). Every outbound record has the same
    shape: `key: value` lines, no body."""
    if not content or not content.strip():
        return None, "the file is empty"
    fields = {}
    for line in content.replace("\r\n", "\n").split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    if not fields:
        return None, "no key: value line in the record"
    return fields, None


def receipt_is_valid(content):
    """(True, id) or (False, reason). A RECEIPT WITH NO MESSAGE ID IS REFUSED.

    The id is the platform's own answer that it took the message. A receipt
    without one is a claim that a send happened with nothing behind it, which
    is the exact shape of the evidence failures this project keeps paying for,
    so it does not count as proof and it does not silence the file it names.
    """
    fields, why = parse_record(content)
    if fields is None:
        return False, why
    raw = fields.get("messageId", "")
    if not raw or raw == "none":
        return False, "the receipt carries no messageId"
    try:
        mid = int(raw)
    except ValueError:
        return False, "messageId is not a whole number: %s" % raw
    if mid <= 0:
        return False, "messageId is %d, which no platform returns" % mid
    return True, mid


def read_photo_ref(repo, rel):
    """(photo-rel, why-not) for the picture a message asks to carry.

    (None, "") IS THE ORDINARY CASE: most messages name no picture at all,
    and that is not an error. A sidecar that EXISTS but cannot be read as a
    `photo: <path>` record is a DIFFERENT answer, (None, "some reason"),
    because ruling 5 says a message that meant to carry a picture must never
    fall back to going out as bare text: the caller reads the difference
    between "no sidecar" and "a broken one" and refuses the second rather
    than silently downgrading it. See sweep().
    """
    side = photo_ref_rel(rel)
    raw = _read(repo, side)
    if raw is None:
        return None, ""
    fields, why = parse_record(raw)
    if fields is None:
        return None, "%s exists but %s" % (side, why)
    photo = (fields.get("photo") or "").strip()
    if not photo:
        return None, "%s exists but carries no photo: line" % side
    return photo, ""


def sizes_key(sizes):
    """`90x67/320x240/800x600`, or empty. NO SPACES: every reader of a
    key=value line splits on whitespace and truncates silently."""
    out = []
    for s in sizes or []:
        try:
            out.append("%dx%d" % (int(s.get("width")), int(s.get("height"))))
        except (TypeError, ValueError):
            continue
    return "/".join(out)


def video_descriptor_key(d):
    """`1280x720/12s`, or empty. Built from whichever of `video` (sendVideo)
    or `animation` (sendAnimation) the platform's answer carried; NO SPACES,
    the same reader-safety as sizes_key() above."""
    if not d:
        return ""
    try:
        w, h = int(d.get("width") or 0), int(d.get("height") or 0)
    except (TypeError, ValueError):
        return ""
    dur = d.get("duration")
    try:
        dur_s = "%ds" % int(dur) if dur is not None else "?s"
    except (TypeError, ValueError):
        dur_s = "?s"
    return "%dx%d/%s" % (w, h, dur_s)


# --------------------------------------------------------------------------
# The check, run here because here is the sending side
# --------------------------------------------------------------------------
def failing_clause(stdout):
    """The clause the check refused on, as one line.

    Read off the finding block that `producer-check.report` prints, which is
    the part naming the RULE. A refusal that reaches Jafar's studio as "it
    failed" and no clause is a round trip nobody can act on.
    """
    lines = (stdout or "").splitlines()
    found, grabbing = [], False
    for ln in lines:
        if grabbing:
            if not ln.startswith("    "):
                break
            found.append(" ".join(ln.split()))
            continue
        if "finding(s) over" in ln and ln.rstrip().endswith("enforced:"):
            grabbing = True
    if not found:
        for ln in lines:
            flat = " ".join(ln.split())
            if flat.startswith("producer-check:") and (
                    "DO NOT SEND" in flat or "nothing measured" in flat):
                found.append(flat)
    if not found:
        return "the check refused it and printed no finding line"
    return inbox.one_line("; ".join(found), CLAUSE_CAP)


def run_check(repo, kind, rel, timeout=120):
    """(ok, clause, output). The subprocess runs on THIS machine.

    Exit 0 is SEND, 1 is DO NOT SEND, 2 is nothing measured. A crash, a
    missing tool or a timeout is treated as DO NOT SEND: the failure direction
    of a check that could not run is never "send it anyway".
    """
    tool = os.path.join(repo, "tools", "producer-check.py")
    if not os.path.isfile(tool):
        return False, ("the check itself is missing at tools/producer-check.py "
                       "on this machine, so nothing was checked"), ""
    try:
        p = subprocess.run([sys.executable, tool, "--kind", kind,
                            full_path(repo, rel)],
                           capture_output=True, text=True, timeout=timeout,
                           cwd=repo)
    except subprocess.TimeoutExpired:
        return False, ("the check did not finish within %d second(s), so this "
                       "message is not sent" % timeout), ""
    except OSError as e:
        return False, ("the check could not be run (%s), so this message is "
                       "not sent" % type(e).__name__), ""
    out = (p.stdout or "") + (p.stderr or "")
    if p.returncode == 0:
        return True, "", out
    return False, failing_clause(out), out


def commit_epoch(repo, rel):
    """(sha, epoch, why) for the commit this file was last written by.

    ONE END OF `outboundLatencySec`. `git log -1` on the path, through the
    inbox's whitelisted runner so this can never reach a `fetch` and race the
    watcher's resync. A file that has never been committed measures NOTHING
    rather than borrowing the wall clock: a latency measured from the wrong
    end reads as a fast channel.
    """
    # THREE VALUES SINCE 2026-09-07: `inbox.git_call` splits stderr off
    # stdout, because a warning glued to a value is what held 254 of
    # his messages on the PC. This parses stdout and nothing else.
    rc, out, _ = inbox.git_call(["log", "-1", "--format=%H %ct", "--",
                                 rel], repo)
    if rc != 0:
        return None, None, "git could not read the history of this file"
    bits = out.split()
    if len(bits) < 2:
        return None, None, ("this file is not committed in this checkout, so "
                            "there is no commit instant to measure from")
    try:
        return bits[0], int(bits[1]), ""
    except ValueError:
        return None, None, "the commit instant did not parse"


# --------------------------------------------------------------------------
# The sweep
# --------------------------------------------------------------------------
def full_path(repo, rel):
    """A repository-relative path, or a path given whole. Absolute wins.

    `--send-file` may be handed any path a human types, and joining an
    absolute one onto the repository root would build a path that exists
    nowhere and report the wrong reason for it.
    """
    if os.path.isabs(rel) or (len(rel) > 2 and rel[1] == ":"):
        return rel
    return os.path.join(repo, *rel.split("/"))


class SendFailed(Exception):
    """The wire said no. Not a register refusal: the message stays unsent and
    the next pass tries again."""


def _write(repo, rel, text):
    full = os.path.join(repo, *rel.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return rel


def _read(repo, rel):
    try:
        with open(full_path(repo, rel), "r",
                  encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def holds_for(repo, rel):
    """Refusal records for this message that HOLD it, newest name last.

    A hold is written only when the platform's answer left it unknowable
    whether the message arrived. It stops the retry loop until a human deletes
    the record, because a duplicate Producer message in his chat is worse than
    a late one.
    """
    base = record_base(rel)
    out = []
    for r in inbox.outbound_files(repo):
        name = r.rsplit("/", 1)[-1]
        if not name.startswith(base + ".refused-"):
            continue
        fields, _why = parse_record(_read(repo, r) or "")
        if fields and fields.get("hold") == "yes":
            out.append(r)
    return out


def sweep(repo, sender, now=None, say=None, only=None, photo_sender=None):
    """Check and send every unsent file in the outbox. Returns a dict.

    `sender(text)` is the wire, injected so the selftest can drive every path
    without a network. It returns the platform's result payload, or raises
    SendFailed.

    `photo_sender(path, caption)` is RULING 5, 2026-09-07: a message that
    names a picture (read_photo_ref) goes out as ONE captioned photo through
    this instead of `sender`. It is optional and defaults to None so an
    existing caller that has not been updated keeps sending plain messages
    exactly as before; a message naming a picture with no `photo_sender`
    wired in is REFUSED rather than silently sent as bare text, which is the
    one thing ruling 5 says must never happen again.
    """
    say = say or (lambda _s: None)
    now = int(now if now is not None else time.time())
    res = {"files": [], "sent": [], "captioned": [], "refused": [],
           "already": [], "held": [], "failed": [], "bad_receipt": [],
           "records": [], "samples": []}
    files = outbox_files(repo)
    if only:
        files = [f for f in files if f in only or f.endswith("/" + only)]
    res["files"] = files
    for rel in files:
        kind, why = kind_of_name(rel)
        if kind is None:
            clause = why
            rec = _write(repo, refusal_rel(rel, clause),
                         render_refusal(rel, None, clause, now, False))
            res["refused"].append((rel, clause))
            res["records"].append(rec)
            say("  outbox: REFUSED %s: %s" % (rel, clause))
            continue
        receipt = receipt_rel(rel)
        have = _read(repo, receipt)
        if have is not None:
            good, detail = receipt_is_valid(have)
            if good:
                res["already"].append(rel)
                continue
            res["bad_receipt"].append((rel, detail))
            say("  outbox: RECEIPT REFUSED for %s (%s). The file is held, not "
                "sent again: delete %s once you know whether it arrived."
                % (rel, detail, receipt))
            continue
        held = holds_for(repo, rel)
        if held:
            res["held"].append((rel, held[-1]))
            say("  outbox: HELD %s by %s. Delete that record once you know "
                "whether it arrived." % (rel, held[-1]))
            continue
        ok, clause, output = run_check(repo, kind, rel)
        if not ok:
            rec = _write(repo, refusal_rel(rel, clause),
                         render_refusal(rel, kind, clause, now, False, output))
            res["refused"].append((rel, clause))
            res["records"].append(rec)
            say("  outbox: REFUSED %s (%s): %s" % (rel, kind, clause))
            continue
        text = (_read(repo, rel) or "").strip()
        if not text:
            clause = "the file is empty, so there is nothing to send"
            rec = _write(repo, refusal_rel(rel, clause),
                         render_refusal(rel, kind, clause, now, False))
            res["refused"].append((rel, clause))
            res["records"].append(rec)
            say("  outbox: REFUSED %s: %s" % (rel, clause))
            continue
        photo_rel, photo_why = read_photo_ref(repo, rel)
        if photo_why:
            # A SIDECAR EXISTS AND CANNOT BE READ. Ruling 5: a message that
            # meant to carry a picture is never sent as bare text instead,
            # so this refuses rather than falling through to `sender(text)`.
            clause = ("this message names a picture and it cannot be sent: "
                      "%s. Ruling 5, 2026-09-07: a test request that means "
                      "to carry a picture is never sent as bare text"
                      % photo_why)
            rec = _write(repo, refusal_rel(rel, clause),
                         render_refusal(rel, kind, clause, now, False))
            res["refused"].append((rel, clause))
            res["records"].append(rec)
            say("  outbox: REFUSED %s: %s" % (rel, clause))
            continue
        if photo_rel is not None:
            # THE CAPTIONED PATH. THE OVERFLOW CASE IS THE ONE THAT MATTERS:
            # the answer register carries NO WORD CAP (his question sets the
            # length), so a long, perfectly legal test request may still be
            # longer than Telegram's 1024-character caption. TRUNCATING IT
            # WOULD BE DAMAGE EVEN IF ANNOUNCED, because the part cut is his
            # numbered steps and "exactly what to reply", not a trailing
            # URL: unlike cap_caption's machine-written text, there is no
            # safe part of THIS text to lose. So an over-cap message is
            # REFUSED rather than sent truncated, the same choice already
            # made for an oversized picture (photo_refusal: "refused rather
            # than truncated"), applied to the text instead of the file.
            if len(text) > CAPTION_CAP:
                clause = ("this message is %d character(s) long and names a "
                          "picture, so it must go out as ONE captioned "
                          "photo; the Telegram caption cap is %d and this is "
                          "%d over it. Refused rather than sent truncated: "
                          "shorten the message, or drop %s to send it as "
                          "plain words"
                          % (len(text), CAPTION_CAP,
                             len(text) - CAPTION_CAP, photo_ref_rel(rel)))
                rec = _write(repo, refusal_rel(rel, clause),
                             render_refusal(rel, kind, clause, now, False))
                res["refused"].append((rel, clause))
                res["records"].append(rec)
                say("  outbox: REFUSED %s: %s" % (rel, clause))
                continue
            if photo_sender is None:
                clause = ("this message names a picture and this pass has "
                          "no photo sender wired in, so it cannot go out as "
                          "one captioned message; refused rather than sent "
                          "as bare text (ruling 5, 2026-09-07)")
                rec = _write(repo, refusal_rel(rel, clause),
                             render_refusal(rel, kind, clause, now, False))
                res["refused"].append((rel, clause))
                res["records"].append(rec)
                say("  outbox: REFUSED %s: %s" % (rel, clause))
                continue
            photo_full = full_path(repo, photo_rel)
            pok, pwhy, _psize = photo_refusal(repo, photo_full)
            if not pok:
                clause = ("this message names a picture that cannot be "
                          "sent: %s" % pwhy)
                rec = _write(repo, refusal_rel(rel, clause),
                             render_refusal(rel, kind, clause, now, False))
                res["refused"].append((rel, clause))
                res["records"].append(rec)
                say("  outbox: REFUSED %s: %s" % (rel, clause))
                continue
            try:
                result = photo_sender(photo_full, text)
            except SendFailed as e:
                res["failed"].append((rel, str(e)))
                say("  outbox: NOT SENT %s (%s). It stays unsent and the "
                    "next pass tries again." % (rel, e))
                continue
            mid = (result or {}).get("message_id")
            sizes = (result or {}).get("photo") or []
            if not mid or not sizes:
                clause = ("the platform returned %s for this captioned "
                          "message, so whether it arrived is unknown"
                          % ("no message id" if not mid else
                             "no photo descriptor, which is what a file "
                             "filed as a document looks like"))
                rec = _write(repo, refusal_rel(rel, clause),
                             render_refusal(rel, kind, clause, now, True))
                res["refused"].append((rel, clause))
                res["records"].append(rec)
                say("  outbox: NO RECEIPT for %s: %s. It is HELD, not "
                    "retried." % (rel, clause))
                continue
            sha, c_epoch, no_lat = commit_epoch(repo, rel)
            sent_epoch = int(time.time()) if now is None else now
            latency = None if c_epoch is None else sent_epoch - c_epoch
            rec = _write(repo, receipt,
                         render_captioned_receipt(
                             rel, kind, photo_rel, sent_epoch, mid,
                             len(text), sizes, sha, c_epoch, latency, no_lat))
            res["captioned"].append(rel)
            res["records"].append(rec)
            if latency is not None:
                res["samples"].append(latency)
            say("  outbox: sent %s kind=%s AS-CAPTIONED-PHOTO photoRef=%s "
                "chars=%d messageId=%d photoSizes=%s outboundLatencySec=%s "
                "receipt=%s"
                % (rel, kind, photo_rel, len(text), mid, sizes_key(sizes),
                   "nothing-measured" if latency is None else latency, rec))
            continue
        try:
            result = sender(text)
        except SendFailed as e:
            res["failed"].append((rel, str(e)))
            say("  outbox: NOT SENT %s (%s). It stays unsent and the next "
                "pass tries again." % (rel, e))
            continue
        mid = (result or {}).get("message_id")
        if not mid:
            clause = ("the platform returned no message id, so whether this "
                      "message arrived is unknown")
            rec = _write(repo, refusal_rel(rel, clause),
                         render_refusal(rel, kind, clause, now, True))
            res["refused"].append((rel, clause))
            res["records"].append(rec)
            say("  outbox: NO RECEIPT for %s: %s. It is HELD, not retried."
                % (rel, clause))
            continue
        sha, c_epoch, no_lat = commit_epoch(repo, rel)
        sent_epoch = int(time.time()) if now is None else now
        latency = None if c_epoch is None else sent_epoch - c_epoch
        rec = _write(repo, receipt,
                     render_receipt(rel, kind, sent_epoch, mid, len(text),
                                    sha, c_epoch, latency, no_lat))
        res["sent"].append(rel)
        res["records"].append(rec)
        if latency is not None:
            res["samples"].append(latency)
        say("  outbox: sent %s kind=%s chars=%d messageId=%d "
            "outboundLatencySec=%s outboundLatencySecFrom=fileCommitInstant "
            "outboundLatencySecTo=sendInstant receipt=%s"
            % (rel, kind, len(text), mid,
               "nothing-measured" if latency is None else latency, rec))
        if latency is None and no_lat:
            say("    no latency for this one: %s" % no_lat)
    return res


def done_line(res):
    """The whole sweep's tally, every count against the set it came from.

    `unsent` is the state at the END of the pass: everything in the outbox
    that has no valid receipt now, whatever the reason. `refused`, `held`,
    `failed` and `receiptRefused` are the reasons, and they sum to it.

    `captionedSent` IS ITS OWN KEY, NOT FOLDED INTO `sent`: a message sent as
    one captioned photo (ruling 5) is a different outcome from a plain text
    send, and `sent` already meant "a plain Producer text message reached
    his phone" before this pathway existed. One key, one meaning, ruled
    2026-09-07 after `sent=` was found counting bot chrome for the same
    reason.
    """
    n = len(res["files"])
    sent, cap_sent, ref = (len(res["sent"]), len(res["captioned"]),
                           len(res["refused"]))
    already, held = len(res["already"]), len(res["held"])
    failed, bad = len(res["failed"]), len(res["bad_receipt"])
    unsent = n - sent - cap_sent - already
    return ("outbox done: outboxFiles=%d sent=%d captionedSent=%d refused=%d "
            "unsent=%d alreadySent=%d held=%d sendFailed=%d receiptRefused=%d "
            "recordsWritten=%d latencySamples=%d/%d outboundLatencySecAtWorst=%s"
            % (n, sent, cap_sent, ref, unsent, already, held, failed, bad,
               len(res["records"]), len(res["samples"]), sent + cap_sent,
               max(res["samples"]) if res["samples"] else "nothing-measured"))


def nothing_line(res):
    """The words "nothing measured", or empty. A zero that cannot tell "no
    unsent file" from "never looked" is the failure this sentence removes."""
    n = len(res["files"])
    unsent_at_start = n - len(res["already"])
    if n == 0:
        return ("  nothing measured: 0 file(s) in %s, so this pass checked "
                "nothing and sent nothing." % OUTBOX_DIR)
    if unsent_at_start == 0:
        return ("  nothing measured: all %d file(s) in %s already carry a "
                "receipt, so no message was checked or sent this pass."
                % (n, OUTBOX_DIR))
    return ""


# --------------------------------------------------------------------------
# The picture (queue 091). The picker is tools/report-frame.py and it REFUSES.
# --------------------------------------------------------------------------
FRAME_LINE = re.compile(r"^(NOW|BEFORE)\s+(\S.*)$")
FROM_LINE = re.compile(r"^\s+from\s+(\S+)")

#: report-frame writes the earlier frame to a temp file called
#: `before_<sha>_<frame>.jpg`. The FRAME is what the caption names and what
#: the receipt is filed under, so the wrapper is stripped off the name while
#: the path stays exactly what the picker said.
BEFORE_NAME = re.compile(r"^before_[0-9a-f]{4,40}_(.+)$")


def parse_frames(rc, stdout):
    """What report-frame offered. {"ok", "why", "candidates"}.

    ITS REFUSAL IS THE HALF THAT MATTERS. It walks back to the last commit
    whose own verdict says a sim ran, and when there is none it prints why and
    exits non-zero. That answer is carried to his phone as words, never as an
    old frame reused.
    """
    out = {"ok": False, "why": "", "candidates": []}
    lines = (stdout or "").splitlines()
    cur = None
    for ln in lines:
        m = FRAME_LINE.match(ln)
        if m:
            cur = {"role": m.group(1).lower(), "path": m.group(2).strip(),
                   "sha": "unknown"}
            if cur["path"].startswith("(none"):
                cur = None
                continue
            out["candidates"].append(cur)
            continue
        m = FROM_LINE.match(ln)
        if m and cur is not None:
            cur["sha"] = m.group(1)
            cur = None
    if rc != 0 or not out["candidates"]:
        why = " ".join(" ".join(lines).split()) or "report-frame said nothing"
        out["why"] = inbox.one_line(why, 300)
        return out
    for c in out["candidates"]:
        name = os.path.basename(c["path"])
        m = BEFORE_NAME.match(name)
        c["frame"] = m.group(1) if m else name
    out["ok"] = True
    return out


def run_report_frame(repo, extra=None, timeout=120):
    """(rc, stdout) from the picker, run here on the PC."""
    tool = os.path.join(repo, "tools", "report-frame.py")
    if not os.path.isfile(tool):
        return 2, ("report-frame: the picker is missing at "
                   "tools/report-frame.py on this machine")
    try:
        p = subprocess.run([sys.executable, tool] + list(extra or []),
                           capture_output=True, text=True, timeout=timeout,
                           cwd=repo)
    except (subprocess.TimeoutExpired, OSError) as e:
        return 2, "report-frame: could not run (%s)" % type(e).__name__
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def cap_caption(line, cap=CAPTION_CAP):
    """(capped-line, was-capped, dropped-chars). ONE PLACE THE CAPTION CAP IS
    ENFORCED WITH AN ANNOUNCEMENT, so a sim-shot caption (caption_for below)
    and a video verdict (send_video) read the same number the same way
    rather than each rolling its own arithmetic. Whitespace is collapsed
    first so the length measured is the length Telegram will actually count.

    THIS IS TRUNCATE-AND-ANNOUNCE, THE RIGHT CHOICE ONLY FOR MACHINE-WRITTEN
    TEXT WHERE THE CUT PART IS RECONSTRUCTABLE (the sha in a caption's URL,
    say). A HUMAN-AUTHORED TEST REQUEST IS THE OPPOSITE CASE and does NOT
    call this: see sweep()'s captioned-message path, which refuses an
    over-cap message instead, because the part a truncation would cut is his
    numbered steps and "exactly what to reply", not a trailing URL.
    """
    line = " ".join(line.split())
    if len(line) <= cap:
        return line, False, 0
    dropped = len(line) - cap
    tail = " (+%d more character(s) not shown)" % dropped
    return line[:cap - len(tail)] + tail, True, dropped


def caption_for(frame, role, run_sha):
    """(caption, capped, dropped). ONE LINE, and the cap announces itself.

    What it shows, the run it came from, then the evidence link behind the
    sentence per constitution law 12. The verdict file is the link because the
    caption's claim is that this frame came from a run that measured
    something, and that file is the evidence for exactly that claim.
    """
    stem = frame[:-len(".jpg")] if frame.endswith(".jpg") else frame
    what = ("%s from run %s, the newest run whose own verdict says the sim "
            "ran." % (stem, run_sha)) if role == "now" else (
            "%s as it was at run %s, the previous measuring run, for the "
            "comparison." % (stem, run_sha))
    line = "%s %s/%s/runs/%s.txt" % (what, REPO_BLOB, SHOTS_DIR, run_sha)
    return cap_caption(line)


def _size_refusal(path, max_bytes, noun):
    """(ok, why, bytes) for a file this project uploads to Telegram: a
    missing file is named, an oversized one carries its MEASURED size and
    the ruled limit rather than a guess or a silent truncation. Shared by
    photo_refusal, called from BOTH report-frame's picture path (queue 091)
    and a captioned message's sidecar (ruling 5), and video_refusal (ruling
    1, 2026-09-07): one "does this fit the platform" idea, read by every
    caller rather than typed out twice with a different noun each time.
    """
    try:
        size = os.path.getsize(path)
    except OSError:
        return False, "the %s file is not on this disk: %s" % (noun, path), None
    if size > max_bytes:
        return False, ("%s is %d byte(s), over the %d byte %s limit, so it "
                       "is refused rather than truncated"
                       % (os.path.basename(path), size, max_bytes, noun)), size
    if size == 0:
        return False, "%s is 0 byte(s) on this disk" % os.path.basename(path), 0
    return True, "", size


def photo_refusal(repo, path):
    """(ok, why, bytes). A missing file is named; an oversized one carries its
    MEASURED size rather than a guess or a truncation."""
    return _size_refusal(path, PHOTO_MAX_BYTES, "photo")


def video_refusal(path):
    """(ok, why, bytes). Same check as photo_refusal, the video ceiling:
    VIDEO_MAX_BYTES is Telegram's documented multipart upload limit for a
    bot-sent clip, ruling 1, 2026-09-07."""
    return _size_refusal(path, VIDEO_MAX_BYTES, "video")


def send_frames(repo, photo_sender, text_sender, now=None, say=None,
                extra=None, frames=None):
    """Carry report-frame's answer to his phone, including the answer "no".

    `photo_sender(path, caption)` returns the platform's result payload;
    `text_sender(text)` is used only for the withheld case, which must arrive
    as words rather than as an old frame reused.
    """
    say = say or (lambda _s: None)
    now = int(now if now is not None else time.time())
    res = {"candidates": [], "sent": [], "refused": [], "failed": [],
           "records": [], "withheld": "", "capped": 0}
    if frames is None:
        rc, out = run_report_frame(repo, extra)
        frames = parse_frames(rc, out)
    if not frames["ok"]:
        res["withheld"] = frames["why"]
        note = ("No picture with this one, and that is the honest answer "
                "rather than an old frame reused: nothing measured. "
                "report-frame said: %s" % frames["why"])
        try:
            text_sender(note)
            say("  frame: WITHHELD, sent as words. %s" % frames["why"])
        except SendFailed as e:
            res["failed"].append(("the withheld note", str(e)))
            say("  frame: WITHHELD and the note did not send (%s)" % e)
        return res
    res["candidates"] = frames["candidates"]
    for c in frames["candidates"]:
        ok, why, size = photo_refusal(repo, c["path"])
        if not ok:
            res["refused"].append((c.get("frame") or c["path"], why))
            say("  frame: REFUSED %s: %s" % (c.get("frame") or c["path"], why))
            continue
        caption, capped, _dropped = caption_for(c["frame"], c["role"],
                                                c["sha"])
        if capped:
            res["capped"] += 1
        try:
            result = photo_sender(c["path"], caption)
        except SendFailed as e:
            res["failed"].append((c["frame"], str(e)))
            say("  frame: NOT SENT %s (%s)" % (c["frame"], e))
            continue
        mid = (result or {}).get("message_id")
        sizes = (result or {}).get("photo") or []
        if not mid or not sizes:
            why = ("the platform returned %s, so this did not arrive as a "
                   "photo and no receipt is written"
                   % ("no message id" if not mid else
                      "no photo descriptor, which is what a file filed as a "
                      "document looks like"))
            res["refused"].append((c["frame"], why))
            say("  frame: NO RECEIPT for %s: %s" % (c["frame"], why))
            continue
        rec = _write(repo, photo_receipt_rel(c["frame"], c["sha"], c["role"]),
                     render_photo_receipt(c["frame"], c["role"], c["sha"],
                                          size, now, mid, sizes,
                                          len(caption), capped))
        res["sent"].append(c["frame"])
        res["records"].append(rec)
        say("  frame: sent %s role=%s runSha=%s bytes=%d messageId=%d "
            "photoSizes=%s captionChars=%d receipt=%s"
            % (c["frame"], c["role"], c["sha"], size, mid, sizes_key(sizes),
               len(caption), rec))
    return res


def frames_done_line(res):
    """`imagesSent=N/M`, M being what report-frame offered, so a zero can be
    told apart from a run that never looked."""
    m = len(res["candidates"])
    line = ("frames done: imagesSent=%d/%d candidates refused=%d sendFailed=%d "
            "captionsCapped=%d/%d receipts=%d"
            % (len(res["sent"]), m, len(res["refused"]), len(res["failed"]),
               res["capped"], len(res["sent"]), len(res["records"])))
    if res["withheld"]:
        line += " withheld=1"
    return line


def frames_nothing_line(res):
    if res["withheld"]:
        return ("  nothing measured: report-frame withheld every frame, so 0 "
                "image(s) were sent of 0 candidate(s) offered, and he was told "
                "so in words.")
    if not res["candidates"]:
        return ("  nothing measured: report-frame offered 0 candidate(s), so "
                "this pass looked at no picture.")
    return ""


# --------------------------------------------------------------------------
# THE CLIP, ruling 1, 2026-09-07: the automated playtest step's clip "goes
# to Telegram with a one-line verdict". Built the same way send_frames
# carries a picture: size checked HERE before any upload is attempted, the
# wire is injected so this file never touches the network, and the
# platform's own descriptor is the arrived-proof. NO PICKER OF ITS OWN: the
# CI step that captures the clip and decides the verdict text is out of
# scope here (a workflow file), so this takes the path and the caption as
# given and does the send-refuse-receipt half only, exactly as send_photo
# does the wire half of send_frames.
# --------------------------------------------------------------------------
def send_video(repo, video_sender, text_sender, path, caption, role="clip",
               run_sha="unknown", now=None, say=None):
    """One clip, to Jafar's phone, with a one-line verdict caption.

    `video_sender(path, caption)` returns the platform's result payload,
    exactly as `photo_sender` does for send_frames; `text_sender(text)` is
    used only for the withheld case below. Returns {"sent", "refused",
    "failed", "records", "captionCapped", "withheld"}, the same key set
    send_frames returns so one reader parses both.

    `path` MAY BE None: the run never produced a clip (it did not launch, or
    crashed before the scripted route began), and the honest answer travels
    as WORDS through `text_sender` rather than as an old clip reused,
    exactly as send_frames sends a withheld picture as words instead of
    silently reusing the last one.
    """
    say = say or (lambda _s: None)
    now = int(now if now is not None else time.time())
    res = {"sent": [], "refused": [], "failed": [], "records": [],
          "captionCapped": 0, "withheld": ""}
    if path is None:
        note = ("No clip with this one, and that is the honest answer "
               "rather than an old clip reused: nothing measured. %s"
               % caption)
        res["withheld"] = caption
        try:
            text_sender(note)
            say("  video: WITHHELD, sent as words. %s" % caption)
        except SendFailed as e:
            res["failed"].append(("the withheld note", str(e)))
            say("  video: WITHHELD and the note did not send (%s)" % e)
        return res
    ok, why, size = video_refusal(path)
    if not ok:
        res["refused"].append((path, why))
        say("  video: REFUSED %s: %s" % (path, why))
        return res
    cap_text, capped, dropped = cap_caption(caption)
    if capped:
        res["captionCapped"] = 1
        say("  video: caption capped, %d character(s) not shown" % dropped)
    try:
        result = video_sender(path, cap_text)
    except SendFailed as e:
        res["failed"].append((path, str(e)))
        say("  video: NOT SENT %s (%s)" % (path, e))
        return res
    mid = (result or {}).get("message_id")
    descriptor, dkind = None, ""
    for key in ("video", "animation"):
        if (result or {}).get(key):
            descriptor, dkind = result[key], key
            break
    if not mid or not descriptor:
        why = ("the platform returned %s, so this did not arrive as a clip "
              "and no receipt is written"
              % ("no message id" if not mid else
                 "no video or animation descriptor, which is what a file "
                 "filed as a document looks like"))
        res["refused"].append((path, why))
        say("  video: NO RECEIPT for %s: %s" % (path, why))
        return res
    rec = _write(repo, video_receipt_rel(path, run_sha, role),
                render_video_receipt(path, role, now, mid, size, descriptor,
                                     dkind, len(cap_text)))
    res["sent"].append(path)
    res["records"].append(rec)
    say("  video: sent %s role=%s bytes=%d messageId=%d descriptorKind=%s "
        "captionChars=%d receipt=%s"
        % (path, role, size, mid, dkind, len(cap_text), rec))
    return res


def video_done_line(res, candidates=1):
    """One clip's outcome against ITS denominator (1 candidate this pass,
    ruling 1 is one clip per run), so `sent=0` reads as refused or failed
    rather than as never-attempted."""
    line = ("video done: sent=%d/%d refused=%d sendFailed=%d "
           "captionCapped=%d receipts=%d"
           % (len(res["sent"]), candidates, len(res["refused"]),
              len(res["failed"]), res["captionCapped"], len(res["records"])))
    if res["withheld"]:
        line += " withheld=1"
    return line


# --------------------------------------------------------------------------
# What the container reads back off the branch
# --------------------------------------------------------------------------
#: THE KINDS telegram-bot.py WRITES FOR ITS OWN CHAT TRAFFIC, as opposed to
#: a Producer message the studio composed. Named here because this is where
#: the classification happens; the bot passes them in `record_reply`.
BOT_REPLY_KINDS = ("bot-message",)


def outbound_summary(records):
    """{name: content} off the branch to a summary. The arithmetic lives here
    because here is where the tests run.

    Returns counts and the lines to print. `refused=K` is the number the
    container side owes queue 089: a Producer message that could not be sent
    is a fact the studio has to learn without walking the PC's disk.
    """
    out = {"records": len(records), "sent": [], "refused": [], "photos": [],
           "replies": [], "captioned": [], "videos": [], "unreadable": []}
    for name in sorted(records):
        fields, why = parse_record(records[name] or "")
        if fields is None:
            out["unreadable"].append((name, why))
            continue
        if fields.get("receipt") == "sent":
            # A4, RULED 2026-09-07. `sent=` is what queue 089 defined as
            # Producer messages that reached his phone. Every reply the bot
            # makes now writes a receipt of the same shape, so folding them
            # in would make one key mean two things and inflate the number
            # the studio reads as "messages we sent him" by every hello and
            # every read-back. Split by kind, counted apart, both printed.
            if str(fields.get("kind", "")) in BOT_REPLY_KINDS:
                out["replies"].append(fields)
            else:
                out["sent"].append(fields)
        elif fields.get("receipt") == "sent-with-photo":
            # RULING 5, 2026-09-07. A captioned test request is NEITHER a
            # plain "sent" text message NOR a sim-shot "photo": it is a
            # Producer message (counts against the same "did this reach him"
            # question as `sent`) that also arrived as a picture. Its own
            # bucket, its own count, never folded into either sibling.
            out["captioned"].append(fields)
        elif fields.get("receipt") == "photo":
            out["photos"].append(fields)
        elif fields.get("receipt") == "video":
            # RULING 1, 2026-09-07. A clip is not a photo: its arrived-proof
            # lives under a different key (`video`/`animation`, never
            # `photo`) and it carries no `kind` from the outbox register at
            # all, so it gets a bucket and a count of its own too.
            out["videos"].append(fields)
        elif "refused" in fields:
            out["refused"].append(fields)
        else:
            out["unreadable"].append((name, "no receipt: or refused: line"))
    return out


def outbound_lines(summary):
    """The printed block, one line per record plus a done line."""
    lines = []
    for f in summary["sent"]:
        lines.append("  outbound sent   file=%s kind=%s messageId=%s "
                     "outboundLatencySec=%s sentAt=%s"
                     % (f.get("file", "?"), f.get("kind", "?"),
                        f.get("messageId", "?"),
                        f.get("outboundLatencySec", "nothing-measured"),
                        f.get("sent", "?")))
    for f in summary.get("captioned") or []:
        lines.append("  outbound sent+photo file=%s kind=%s messageId=%s "
                     "photoRef=%s photoSizes=%s outboundLatencySec=%s"
                     % (f.get("file", "?"), f.get("kind", "?"),
                        f.get("messageId", "?"), f.get("photoRef", "?"),
                        f.get("photoSizes", "none"),
                        f.get("outboundLatencySec", "nothing-measured")))
    for f in summary["photos"]:
        lines.append("  outbound photo  frame=%s role=%s runSha=%s "
                     "messageId=%s photoSizes=%s"
                     % (f.get("frame", "?"), f.get("role", "?"),
                        f.get("runSha", "?"), f.get("messageId", "?"),
                        f.get("photoSizes", "none")))
    for f in summary.get("videos") or []:
        lines.append("  outbound video   file=%s role=%s messageId=%s "
                     "videoDescriptor=%s captionChars=%s"
                     % (f.get("file", "?"), f.get("role", "?"),
                        f.get("messageId", "?"),
                        f.get("videoDescriptor", "none"),
                        f.get("captionChars", "?")))
    for f in summary["refused"]:
        lines.append("  outbound REFUSED file=%s kind=%s hold=%s clause=%s"
                     % (f.get("file", "?"), f.get("kind", "?"),
                        f.get("hold", "?"), f.get("clause", "?")))
    for name, why in summary["unreadable"]:
        lines.append("  outbound UNREADABLE %s (%s)" % (name, why))
    # ONE TALLY LINE FOR THE REPLIES, NOT ONE LINE EACH (A4). There is a
    # receipt per reply and this block prints every record on the branch for
    # ever, so a line each would grow the report without bound. The newest
    # id is carried because that is the one a round trip is proven with.
    reps = summary.get("replies") or []
    if reps:
        newest = max(reps, key=lambda f: int(f.get("sentEpoch") or 0))
        lines.append("  outbound replies=%d newestMessageId=%s"
                     % (len(reps), newest.get("messageId", "?")))
    lines.append("outbound: records=%d sent=%d replies=%d captioned=%d "
                 "videos=%d refused=%d photos=%d unreadable=%d"
                 % (summary["records"], len(summary["sent"]), len(reps),
                    len(summary.get("captioned") or []),
                    len(summary.get("videos") or []),
                    len(summary["refused"]), len(summary["photos"]),
                    len(summary["unreadable"])))
    if summary["records"] == 0:
        # SCOPED, because this report also carries the INBOUND half's own
        # nothing-measured sentence and a reader grepping for the words must
        # be able to tell which half is silent.
        lines.append("  outbound: nothing measured, 0 record(s) on the "
                     "branch, so nothing is known about what the PC sent or "
                     "refused.")
    return lines


# --------------------------------------------------------------------------
# SELFTEST. Offline by construction: the sender is a scripted stand-in that
# returns what Telegram's documented payload looks like. Accepting case first.
# --------------------------------------------------------------------------
GOOD_MESSAGE = None            # loaded from producer-check's own fixture


def _load_producer_check():
    import importlib.util
    path = os.path.join(REPO, "tools", "producer-check.py")
    spec = importlib.util.spec_from_file_location("producer_check", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fixture_repo(tmp):
    """A throwaway git repository with an outbox in it."""
    os.makedirs(tmp, exist_ok=True)
    for args in (["init", "-q", "-b", "main"],
                 ["config", "user.email", "t@example.com"],
                 ["config", "user.name", "t"]):
        subprocess.run(["git", "-C", tmp] + args, capture_output=True)
    # capsay.py travels too: producer-check refuses to run without it, and a
    # fixture that cannot run the real check would prove nothing about the
    # real check.
    os.makedirs(os.path.join(tmp, "tools"), exist_ok=True)
    for tool in ("producer-check.py", "report-frame.py", "capsay.py"):
        src = os.path.join(REPO, "tools", tool)
        with open(src, "rb") as fh:
            body = fh.read()
        with open(os.path.join(tmp, "tools", tool), "wb") as out:
            out.write(body)
    os.makedirs(os.path.join(tmp, *OUTBOX_DIR.split("/")), exist_ok=True)
    return tmp


def _commit(tmp, rel, text, when=None):
    full = os.path.join(tmp, *rel.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    env = dict(os.environ)
    if when is not None:
        stamp = "%d +0000" % int(when)
        env["GIT_AUTHOR_DATE"] = stamp
        env["GIT_COMMITTER_DATE"] = stamp
    subprocess.run(["git", "-C", tmp, "add", "--", rel], capture_output=True)
    subprocess.run(["git", "-C", tmp, "commit", "-q", "-m", "add " + rel],
                   capture_output=True, env=env)
    return rel


# --------------------------------------------------------------------------
# The fixture, and the clock it is graded against
# --------------------------------------------------------------------------
# A FIXTURE MUST NOT BE GRADED AGAINST A CLOCK IT DOES NOT CONTROL. Found
# 2026-09-06, by which time it was holding every commit in the repository.
# producer-check's GOOD sample states an ABSOLUTE deadline (DEADLINE
# 2026-09-07), and the SINGLE-FILE check this module shells out to measures
# deadlines from the WALL CLOCK on purpose, because the question at send time
# is "is this far enough away to SEND". The gate's filename pin does not reach
# this path and must not: two callers, two clocks, ruled in producer-check.
# So the sample decayed, and here is the series, every reading taken from the
# tool itself: 57.0 hours measured from the 2026-09-05 its own filename
# carries, 24.0 at 2026-09-06T09:00 exactly (the instant it crossed), 23.6 at
# 09:24, 23.5 at 09:30 and 23.3 at 09:41, falling about 0.1 every six minutes
# and never coming back. Below the floor the accepting case went red, the good
# file was never sent, its receipt was never written, and the first comparison
# against that receipt raised TypeError on None. The suite then died before its
# count line, and the gate could only say OUTBOX SELFTEST DID NOT REPORT, which
# is what it says of a crash and of a silence alike.
#
# THE FIX IS IN THE FIXTURE AND NEVER IN THE BOUND. The deadline below is a
# DURATION, which producer-check reads as the same number of hours at every
# instant for ever; the suite proves that at two clocks a decade apart and
# prints both readings as one pair. MIN_DEADLINE_HOURS is untouched and still
# bites: FIXTURE_DEADLINE_SHORT plants a deadline under it, sends it down the
# same subprocess check, and the suite requires a refusal naming the floor.
FIXTURE_DEADLINE_FAR = "DEADLINE in 3 days."      # 72.0 hours, over the floor
FIXTURE_DEADLINE_SHORT = "DEADLINE in 4 hours."   # 4.0 hours, under the floor

#: The two instants the fixture's deadline is read at, a decade apart, so that
#: a reading which moves with the calendar shows up as a difference between
#: them. Documentation here; the suite is what asserts it.
FIXTURE_CLOCKS = (datetime.datetime(2026, 9, 6, 9, 0),
                  datetime.datetime(2036, 9, 6, 9, 0))


def fixture_message(pc, deadline=FIXTURE_DEADLINE_FAR):
    """producer-check's GOOD sample, with a deadline no wall clock can move.

    `pc` is the module `_load_producer_check()` returns, so THE LIVE SAMPLE
    stays the accepting fixture and only its one decaying line is rewritten.
    The line is found with producer-check's OWN deadline regex rather than by
    quoting the date out of it: a sample that changes its deadline must make
    this raise, never leave it silently replacing nothing.
    """
    lines = pc.GOOD.splitlines()
    at = [i for i, line in enumerate(lines) if pc.DEAD_RE.match(line)]
    if len(at) != 1:
        raise ValueError("the GOOD sample carries %d DEADLINE line(s) and not "
                         "1, so this fixture cannot say which line it is "
                         "replacing" % len(at))
    lines[at[0]] = deadline
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# The selftest harness: the count line prints on EVERY path
# --------------------------------------------------------------------------
#: EXIT CODES, DISTINCT PER OUTCOME, because a tool that dies and a tool that
#: reports a failure need different next actions. ledger/verify.py prints the
#: exit code beside the counts, so 4 arrives as a different sentence from 3,
#: and both are different from the silence of a tool that printed no count
#: line at all. 2 stays free for "nothing measured", as elsewhere in this tree.
SELFTEST_OK = 0        # every case passed
SELFTEST_FAILED = 3    # the suite finished and at least one case FAILED
SELFTEST_CRASHED = 4   # the suite RAISED, so the cases after it never ran
SELFTEST_MEANING = {SELFTEST_OK: "every-case-passed",
                    SELFTEST_FAILED: "a-case-FAILED",
                    SELFTEST_CRASHED: "the-suite-itself-RAISED"}


def run_selftest(tool, cases, tail=""):
    """Run `cases(ok, bad, state)` and PRINT THE COUNT LINE WHATEVER HAPPENS.

    A suite that dies mid-run and a suite that runs and reports nothing are
    different facts, and a gate reading only `N passed, M failed` cannot tell
    them apart unless the dying one still prints that line. So the raise is
    caught HERE, printed with its type and message as a failing case, counted,
    and followed by the count line, by how many cases had actually run when it
    raised (the count is a floor, not a total), and by a distinct exit code.

    Shared by outbox.py and telegram-bot.py: one count line, one parser in
    ledger/verify.py, and no second copy of this to fix later.

    Returns (code, ok, bad, state).
    """
    ok, bad, state = [], [], {}
    crash, ran = "", 0
    try:
        cases(ok, bad, state)
    except Exception as exc:                                   # noqa: BLE001
        crash = "%s: %s" % (type(exc).__name__, exc)
        ran = len(ok) + len(bad)
        # The traceback names the line that died, which is the whole reason
        # this is caught rather than allowed to kill the count line. It goes
        # to STDOUT, the stream the count line uses: ledger/verify.py merges
        # the two, and interleaved streams put the death and its numbers in an
        # order that changes between runs.
        traceback.print_exc(file=sys.stdout)
        name = "crash/the-suite-itself-raised-before-it-finished"
        bad.append(name)
        print("  %-46s FAIL : %s (after %d case(s))" % (name, crash, ran))
    state["ranBeforeCrash"] = ran if crash else None
    code = (SELFTEST_CRASHED if crash
            else SELFTEST_FAILED if bad else SELFTEST_OK)
    print("\n%s selftest: %d passed, %d failed (%d case(s) run). %s"
          % (tool, len(ok), len(bad), len(ok) + len(bad), tail))
    if crash:
        print("THE SUITE ITSELF RAISED after %d case(s) had run, so the "
              "count above is a floor and not a total: the cases after it "
              "never ran. %s" % (ran, crash))
    return code, ok, bad, state


def _selftest_cases(ok, bad, state):
    """Every case, appending to `ok` / `bad`. Run through `run_selftest`.

    SPLIT FROM `selftest()` so a raise anywhere below still reaches the count
    line: this half may die, the half that reports may not.
    """
    import contextlib                                   # noqa: PLC0415
    import io as _io                                    # noqa: PLC0415
    import tempfile                                     # noqa: PLC0415

    def check(name, cond, detail=""):
        (ok if cond else bad).append(name)
        print("  %-46s %s%s" % (name, "pass" if cond else "FAIL",
                                (" : " + str(detail)) if not cond else ""))

    # THE HARNESS ITSELF, BOTH OUTCOMES, ACCEPTING CASE FIRST. A suite that
    # cannot report its own death is the silent-instrument failure: on
    # 2026-09-06 this one raised at a None receipt and the gate could say only
    # OUTBOX SELFTEST DID NOT REPORT, which is true of a crash and of a silence
    # alike. Both rungs run through the REAL `run_selftest`, and its printing
    # is CAPTURED rather than echoed: ledger/verify.py takes the first
    # `N passed, M failed` in this tool's output, so a synthetic count line
    # reaching the terminal would be read as the outbox's own result.
    def _a_suite_that_finishes(o, _b, st):
        o.append("accept/synthetic-case-that-passed")
        st["fixture"] = "/nowhere/synthetic"

    def _a_suite_that_raises(o, _b, _st):
        o.append("accept/synthetic-case-that-ran-before-the-raise")
        raise ValueError("planted, so the death has to print its count line")

    _buf = _io.StringIO()
    with contextlib.redirect_stdout(_buf):
        fin_code, fin_ok, fin_bad, _fin_st = run_selftest(
            "synthetic", _a_suite_that_finishes, "")
        raise_code, _r_ok, raise_bad, raise_st = run_selftest(
            "synthetic", _a_suite_that_raises, "")
    printed = _buf.getvalue()
    check("accept/a-suite-that-finishes-prints-its-count-and-exits-0",
          fin_code == SELFTEST_OK and len(fin_ok) == 1 and not fin_bad
          and "synthetic selftest: 1 passed, 0 failed (1 case(s) run)"
          in printed,
          "exit=%d printedChars=%d" % (fin_code, len(printed)))
    check("reject/a-suite-that-raises-still-prints-its-count-and-exits-4",
          raise_code == SELFTEST_CRASHED and len(raise_bad) == 1
          and "synthetic selftest: 1 passed, 1 failed (2 case(s) run)"
          in printed
          and "THE SUITE ITSELF RAISED after 1 case(s)" in printed
          and "ValueError: planted" in printed
          and raise_st["ranBeforeCrash"] == 1,
          "exit=%d ranBeforeCrash=%s" % (raise_code,
                                         raise_st.get("ranBeforeCrash")))
    print("      says: harnessFinishExit=%d harnessRaiseExit=%d "
          "harnessRaiseRanBeforeCrash=%s harnessRaiseNamesTheType=%s "
          "countLinePrintedOnBothPaths=%s"
          % (fin_code, raise_code, raise_st.get("ranBeforeCrash"),
             "yes" if "ValueError: planted" in printed else "NO",
             "yes" if printed.count("case(s) run)") == 2 else "NO"))

    pc = _load_producer_check()
    # THE ACCEPTING FIXTURE IS THE LIVE SAMPLE with its one decaying line
    # rewritten as a duration. See fixture_message above for what decayed.
    good_text = fixture_message(pc)

    # THE FIXTURE'S OWN CLOCK, ACCEPTING CASE FIRST, and read before anything
    # else depends on it. Two instants a decade apart: a duration deadline
    # gives one answer for ever, and that is what stops this suite going red
    # with nobody having touched the tree. The reading is emitted as a PAIR,
    # value@clock..value@clock, so both moments travel on one line.
    dl_lines = [l for l in good_text.splitlines() if pc.DEAD_RE.match(l)]
    dl_hours = [pc.deadline_hours(dl_lines[0], c) for c in FIXTURE_CLOCKS] \
        if len(dl_lines) == 1 else []
    check("accept/the-fixtures-deadline-cannot-move-with-the-wall-clock",
          len(dl_lines) == 1 and len(set(dl_hours)) == 1
          and None not in dl_hours
          and dl_hours[0] >= pc.MIN_DEADLINE_HOURS,
          "%d deadline line(s) in the fixture, readings %s"
          % (len(dl_lines), dl_hours))
    print("      says: fixtureDeadlineHours=%s floorHours=%d clocksRead=%d"
          % ("..".join("%.1f@%s" % (h, c.date().isoformat())
                       for h, c in zip(dl_hours, FIXTURE_CLOCKS))
             or "nothing-measured",
             pc.MIN_DEADLINE_HOURS, len(dl_hours)))

    check("accept/the-three-suffixes-match-producer-check",
          tuple(KIND_SUFFIX) == tuple(pc.KIND_SUFFIX), pc.KIND_SUFFIX)
    check("accept/the-outbox-tree-matches-the-gates",
          OUTBOX_DIR == pc.GATE_TREES[0], pc.GATE_TREES)
    check("accept/kind-from-the-name",
          kind_of_name("2026-09-05-x.unprompted.md")[0] == "unprompted"
          and kind_of_name("a.brief.md")[0] == "brief"
          and kind_of_name("a.answer.md")[0] == "answer")
    k, why = kind_of_name("2026-09-05-no-kind.md")
    check("reject/a-name-with-no-kind-names-all-three",
          k is None and ".unprompted.md" in why and ".answer.md" in why
          and ".brief.md" in why, why)

    tmp = tempfile.mkdtemp(prefix="ledger-outbox-")
    # Recorded BEFORE any case runs: on a crash the directory to open is the
    # first thing the reader needs, and `selftest()` prints it either way.
    state["fixture"] = tmp
    repo = _fixture_repo(tmp)
    good_rel = "%s/2026-09-05-a-good-one.unprompted.md" % OUTBOX_DIR
    commit_at = 1788600000
    _commit(repo, good_rel, good_text, when=commit_at)
    sent_at = commit_at + 42

    calls = []

    def sender(text):
        calls.append(text)
        return {"message_id": 4711, "date": sent_at}

    r = sweep(repo, sender, now=sent_at)
    check("accept/a-good-message-is-checked-and-sent",
          r["sent"] == [good_rel] and len(calls) == 1
          and good_text.strip()[:20] in calls[0],
          "%s / %d call(s)" % (r["sent"], len(calls)))
    rec = _read(repo, receipt_rel(good_rel))
    good_id, mid = receipt_is_valid(rec or "")
    check("accept/the-receipt-carries-the-platforms-message-id",
          good_id and mid == 4711, mid)
    check("accept/the-receipt-names-the-file-the-commit-and-the-instant",
          rec and ("file: " + good_rel) in rec and "fileCommit: " in rec
          and "sentEpoch: %d" % sent_at in rec, (rec or "")[:80])
    check("accept/outboundLatencySec-is-commit-to-send",
          "outboundLatencySec: 42" in rec
          and "outboundLatencySecFrom: fileCommitInstant" in rec
          and "not a rate" in rec,
          [l for l in rec.splitlines() if "atency" in l])
    print("      says: %s" % done_line(r))
    check("accept/the-done-line-carries-every-count",
          "outboxFiles=1" in done_line(r) and "sent=1" in done_line(r)
          and "refused=0" in done_line(r) and "unsent=0" in done_line(r),
          done_line(r))
    check("accept/no-spaces-inside-any-value-on-the-done-line",
          all(" " not in kv.split("=", 1)[1]
              for kv in done_line(r).split()[2:] if "=" in kv), done_line(r))

    r2 = sweep(repo, sender, now=sent_at + 60)
    check("accept/a-second-pass-sends-nothing",
          r2["sent"] == [] and r2["already"] == [good_rel] and len(calls) == 1,
          "%d call(s) total" % len(calls))
    check("accept/and-prints-sent-0-alreadySent-1",
          "sent=0" in done_line(r2) and "alreadySent=1" in done_line(r2),
          done_line(r2))
    check("accept/and-says-nothing-measured-when-nothing-is-unsent",
          "nothing measured" in nothing_line(r2), nothing_line(r2))

    # THE REJECTING CASES.
    #
    # THE FLOOR IS STILL LIVE AT THIS DOOR, and this rung is what proves it.
    # Same fixture, one contributor toggled: the accepted message above states
    # 72 hours and was sent, this one states 4 and must not be. Both rungs go
    # through the same subprocess check in the same run, so the difference
    # between them is MIN_DEADLINE_HOURS and nothing else. Without this rung a
    # fixture whose deadline had stopped being READ AT ALL would still show the
    # accepting case green, which is how a loosened bound hides.
    short_rel = "%s/2026-09-05-deadline-too-close.unprompted.md" % OUTBOX_DIR
    _commit(repo, short_rel, fixture_message(pc, FIXTURE_DEADLINE_SHORT),
            when=commit_at)
    r_dl = sweep(repo, sender, now=sent_at + 90, only=short_rel)
    dl_clause = r_dl["refused"][0][1] if r_dl["refused"] else ""
    check("reject/a-deadline-under-the-ruled-floor-is-not-sent",
          r_dl["sent"] == [] and len(r_dl["refused"]) == 1
          and len(calls) == 1 and "deadline" in dl_clause
          and ("under the ruled %d" % pc.MIN_DEADLINE_HOURS) in dl_clause,
          dl_clause or "NOTHING WAS REFUSED")

    over_rel = "%s/2026-09-05-far-too-long.unprompted.md" % OUTBOX_DIR
    _commit(repo, over_rel, good_text + ("\nword " * 200) + "\n",
            when=commit_at)
    r3 = sweep(repo, sender, now=sent_at + 120, only=over_rel)
    check("reject/an-over-cap-message-is-not-sent",
          r3["sent"] == [] and len(r3["refused"]) == 1 and len(calls) == 1,
          r3["refused"])
    clause = r3["refused"][0][1] if r3["refused"] else ""
    check("reject/and-the-refusal-names-the-failing-clause",
          "words" in clause or "word" in clause, clause)
    rrec = _read(repo, refusal_rel(over_rel, clause))
    check("reject/and-the-record-travels-with-the-clause-in-it",
          rrec and "clause: " in rrec and "hold: no" in rrec
          and ("file: " + over_rel) in rrec, (rrec or "")[:80])
    check("reject/and-refused-is-counted-on-the-done-line",
          "refused=1" in done_line(r3) and "unsent=1" in done_line(r3),
          done_line(r3))
    r3b = sweep(repo, sender, now=sent_at + 180, only=over_rel)
    check("reject/an-unchanged-refusal-writes-the-same-record-once",
          len(r3b["records"]) == 1
          and r3b["records"][0] == refusal_rel(over_rel, clause),
          r3b["records"])

    nokind_rel = "%s/2026-09-05-no-register.md" % OUTBOX_DIR
    _commit(repo, nokind_rel, good_text, when=commit_at)
    r4 = sweep(repo, sender, now=sent_at + 240, only=nokind_rel)
    nk = r4["refused"][0][1] if r4["refused"] else ""
    check("reject/a-name-with-no-kind-is-refused-not-guessed",
          r4["sent"] == [] and ".unprompted.md" in nk and ".answer.md" in nk
          and ".brief.md" in nk, nk)

    noid_rel = "%s/2026-09-05-no-id-back.unprompted.md" % OUTBOX_DIR
    _commit(repo, noid_rel, good_text, when=commit_at)

    def sender_noid(text):
        calls.append(text)
        return {"ok": True}

    r5 = sweep(repo, sender_noid, now=sent_at + 300, only=noid_rel)
    check("reject/no-message-id-means-no-receipt",
          _read(repo, receipt_rel(noid_rel)) is None and r5["sent"] == []
          and len(r5["refused"]) == 1, r5["refused"])
    r5b = sweep(repo, sender_noid, now=sent_at + 360, only=noid_rel)
    check("reject/and-the-file-is-held-rather-than-sent-twice",
          r5b["sent"] == [] and len(r5b["held"]) == 1
          and "held=1" in done_line(r5b), done_line(r5b))

    bad_rel = "%s/2026-09-05-bad-receipt.unprompted.md" % OUTBOX_DIR
    _commit(repo, bad_rel, good_text, when=commit_at)
    _write(repo, receipt_rel(bad_rel), "receipt: sent\nfile: %s\n" % bad_rel)
    r6 = sweep(repo, sender, now=sent_at + 420, only=bad_rel)
    check("reject/a-receipt-with-no-id-is-refused",
          r6["sent"] == [] and len(r6["bad_receipt"]) == 1
          and "messageId" in r6["bad_receipt"][0][1]
          and "receiptRefused=1" in done_line(r6), done_line(r6))

    def sender_down(text):
        raise SendFailed("Could not reach Telegram at all (URLError)")

    down_rel = "%s/2026-09-05-uplink-down.unprompted.md" % OUTBOX_DIR
    _commit(repo, down_rel, good_text, when=commit_at)
    r7 = sweep(repo, sender_down, now=sent_at + 480, only=down_rel)
    check("reject/a-dead-uplink-leaves-it-unsent-and-retryable",
          r7["sent"] == [] and len(r7["failed"]) == 1
          and not holds_for(repo, down_rel)
          and "sendFailed=1" in done_line(r7), done_line(r7))
    r7b = sweep(repo, sender, now=sent_at + 540, only=down_rel)
    check("accept/and-the-next-pass-sends-it",
          r7b["sent"] == [down_rel], r7b["sent"])

    check("accept/an-empty-outbox-says-nothing-measured",
          "nothing measured" in nothing_line({"files": [], "already": []}),
          nothing_line({"files": [], "already": []}))

    # ---- RULING 5, 2026-09-07: A TEST REQUEST CARRIES ITS PICTURE --------
    # "let the photo path carry a caption for a test request... rather than
    # sending text without the picture." ACCEPTING CASE FIRST, then the
    # overflow case (the one that matters), then every way the sidecar can
    # be broken, each one proving the message is REFUSED rather than
    # silently downgraded to a bare text send.
    print("")
    cap_photo_rel = "game-design/sim-shots/captioned-selftest.jpg"
    cap_photo_full = os.path.join(repo, *cap_photo_rel.split("/"))
    os.makedirs(os.path.dirname(cap_photo_full), exist_ok=True)
    with open(cap_photo_full, "wb") as fh:
        fh.write(b"\xff\xd8\xff" + b"q" * 300)

    check("accept/the-accepting-fixture-fits-under-the-caption-cap",
          len(good_text.strip()) <= CAPTION_CAP,
          "%d char(s), cap is %d" % (len(good_text.strip()), CAPTION_CAP))

    cap_rel = "%s/2026-09-07-play-the-street-photo.answer.md" % OUTBOX_DIR
    _commit(repo, cap_rel, good_text, when=commit_at)
    _write(repo, photo_ref_rel(cap_rel), "photo: %s\n" % cap_photo_rel)

    cap_photo_calls = []

    def cap_photo_sender(path, caption):
        cap_photo_calls.append((path, caption))
        return {"message_id": 6001,
                "photo": [{"width": 90, "height": 67, "file_size": 900}]}

    calls_before = len(calls)
    r_cap = sweep(repo, sender, now=sent_at + 600, only=cap_rel,
                 photo_sender=cap_photo_sender)
    check("accept/a-message-naming-a-picture-is-sent-as-one-captioned-photo",
          r_cap["captioned"] == [cap_rel] and r_cap["sent"] == []
          and len(cap_photo_calls) == 1
          and cap_photo_calls[0][0] == cap_photo_full
          and cap_photo_calls[0][1] == good_text.strip()
          and len(calls) == calls_before,
          "%s / %d photo call(s) / %d plain call(s) since"
          % (r_cap["captioned"], len(cap_photo_calls), len(calls) - calls_before))
    cap_rec = _read(repo, receipt_rel(cap_rel))
    check("accept/the-captioned-receipt-carries-both-proofs",
          cap_rec and "receipt: sent-with-photo" in cap_rec
          and ("photoRef: " + cap_photo_rel) in cap_rec
          and "photoSizes: 90x67" in cap_rec and "messageId: 6001" in cap_rec
          and "fileCommit: " in cap_rec, (cap_rec or "")[:160])
    check("accept/the-captioned-receipt-is-readable-by-receipt-is-valid",
          receipt_is_valid(cap_rec or "") == (True, 6001),
          receipt_is_valid(cap_rec or ""))
    print("      says: %s" % done_line(r_cap))
    check("accept/the-done-line-carries-captionedSent-as-its-own-key",
          "captionedSent=1" in done_line(r_cap) and "sent=0" in done_line(r_cap),
          done_line(r_cap))

    r_cap2 = sweep(repo, sender, now=sent_at + 660, only=cap_rel,
                  photo_sender=cap_photo_sender)
    check("accept/a-second-pass-does-not-resend-the-captioned-message",
          r_cap2["captioned"] == [] and r_cap2["already"] == [cap_rel]
          and len(cap_photo_calls) == 1, r_cap2["already"])

    # THE OVERFLOW CASE, THE ONE THAT MATTERS. "answer" carries NO word cap,
    # so this is a legal test request that still overflows the caption.
    long_cap_rel = "%s/2026-09-07-play-the-street-long.answer.md" % OUTBOX_DIR
    long_text = good_text.strip() + ("\nword " * 250) + "\n"
    check("accept/the-overflow-fixture-actually-overflows-the-cap",
          len(long_text.strip()) > CAPTION_CAP,
          "%d char(s), cap is %d" % (len(long_text.strip()), CAPTION_CAP))
    _commit(repo, long_cap_rel, long_text, when=commit_at)
    _write(repo, photo_ref_rel(long_cap_rel), "photo: %s\n" % cap_photo_rel)
    calls_before, photo_calls_before = len(calls), len(cap_photo_calls)
    r_long = sweep(repo, sender, now=sent_at + 720, only=long_cap_rel,
                  photo_sender=cap_photo_sender)
    long_clause = r_long["refused"][0][1] if r_long["refused"] else ""
    check("reject/an-over-cap-captioned-message-is-refused-not-truncated",
          r_long["captioned"] == [] and len(r_long["refused"]) == 1
          and len(cap_photo_calls) == photo_calls_before
          and len(calls) == calls_before
          and str(CAPTION_CAP) in long_clause and "over it" in long_clause
          and "Refused rather than sent truncated" in long_clause,
          long_clause)

    # A SIDECAR NAMES A PICTURE AND THIS PASS HAS NO photo_sender WIRED IN:
    # must not fall back to sending as bare text (the whole point of the
    # ruling).
    nosender_rel = ("%s/2026-09-07-play-the-street-nosender.answer.md"
                    % OUTBOX_DIR)
    _commit(repo, nosender_rel, good_text, when=commit_at)
    _write(repo, photo_ref_rel(nosender_rel), "photo: %s\n" % cap_photo_rel)
    calls_before = len(calls)
    r_ns = sweep(repo, sender, now=sent_at + 780, only=nosender_rel)
    ns_clause = r_ns["refused"][0][1] if r_ns["refused"] else ""
    check("reject/no-photo-sender-wired-in-refuses-rather-than-sends-bare-text",
          r_ns["captioned"] == [] and r_ns["sent"] == []
          and len(r_ns["refused"]) == 1 and len(calls) == calls_before
          and "no photo sender" in ns_clause, ns_clause)

    # A SIDECAR NAMING A PICTURE THAT IS NOT ON DISK.
    missing_rel = ("%s/2026-09-07-play-the-street-missing.answer.md"
                   % OUTBOX_DIR)
    _commit(repo, missing_rel, good_text, when=commit_at)
    _write(repo, photo_ref_rel(missing_rel), "photo: no-such-picture.jpg\n")
    r_miss = sweep(repo, sender, now=sent_at + 840, only=missing_rel,
                  photo_sender=cap_photo_sender)
    miss_clause = r_miss["refused"][0][1] if r_miss["refused"] else ""
    check("reject/a-sidecar-naming-a-picture-not-on-disk-is-refused",
          r_miss["captioned"] == [] and len(r_miss["refused"]) == 1
          and "not on this disk" in miss_clause, miss_clause)

    # A SIDECAR NAMING A PICTURE OVER THE SIZE LIMIT, proven by planting the
    # condition (the floor stays untouched): PHOTO_MAX_BYTES is lowered for
    # one call, exactly as the frame tests below do.
    oversize_rel = ("%s/2026-09-07-play-the-street-oversized.answer.md"
                    % OUTBOX_DIR)
    _commit(repo, oversize_rel, good_text, when=commit_at)
    _write(repo, photo_ref_rel(oversize_rel), "photo: %s\n" % cap_photo_rel)
    real_photo_max = PHOTO_MAX_BYTES
    globals()["PHOTO_MAX_BYTES"] = 16
    r_over = sweep(repo, sender, now=sent_at + 900, only=oversize_rel,
                  photo_sender=cap_photo_sender)
    globals()["PHOTO_MAX_BYTES"] = real_photo_max
    over_clause = r_over["refused"][0][1] if r_over["refused"] else ""
    check("reject/a-sidecar-naming-an-oversized-picture-is-refused-with-its-size",
          r_over["captioned"] == [] and len(r_over["refused"]) == 1
          and "byte(s)" in over_clause, over_clause)

    # A SIDECAR THAT EXISTS BUT CARRIES NO `photo:` LINE.
    broken_rel = ("%s/2026-09-07-play-the-street-broken-sidecar.answer.md"
                  % OUTBOX_DIR)
    _commit(repo, broken_rel, good_text, when=commit_at)
    _write(repo, photo_ref_rel(broken_rel), "note: not a photo line\n")
    calls_before = len(calls)
    r_broken = sweep(repo, sender, now=sent_at + 960, only=broken_rel)
    broken_clause = r_broken["refused"][0][1] if r_broken["refused"] else ""
    check("reject/a-sidecar-with-no-photo-line-is-refused-not-sent-as-text",
          r_broken["captioned"] == [] and r_broken["sent"] == []
          and len(calls) == calls_before
          and "carries no photo" in broken_clause, broken_clause)

    # ---- THE PICTURE ----------------------------------------------------
    print("")
    stdout = ("NOW   %s/game-design/sim-shots/review_day1_noon.jpg\n"
              "      from cb4767e - verdict\n"
              "BEFORE /tmp/before_152198e_review_day1_noon.jpg\n"
              "      from 152198e - verdict\n" % repo)
    fr = parse_frames(0, stdout)
    check("accept/two-candidates-parsed-with-their-shas",
          fr["ok"] and len(fr["candidates"]) == 2
          and fr["candidates"][0]["sha"] == "cb4767e"
          and fr["candidates"][1]["role"] == "before", fr["candidates"])

    shot = os.path.join(repo, *(SHOTS_DIR + "/review_day1_noon.jpg").split("/"))
    os.makedirs(os.path.dirname(shot), exist_ok=True)
    with open(shot, "wb") as fh:
        fh.write(b"\xff\xd8\xff" + b"x" * 400)
    before = os.path.join(tmp, "before_152198e_review_day1_noon.jpg")
    with open(before, "wb") as fh:
        fh.write(b"\xff\xd8\xff" + b"y" * 300)
    fr["candidates"][1]["path"] = before
    check("accept/the-before-frame-is-named-for-the-frame-not-the-temp-file",
          fr["candidates"][1]["frame"] == "review_day1_noon.jpg",
          fr["candidates"][1]["frame"])

    photo_calls = []

    def photo_sender(path, caption):
        photo_calls.append((path, caption))
        return {"message_id": 8123,
                "photo": [{"width": 90, "height": 67, "file_size": 1200},
                          {"width": 800, "height": 600, "file_size": 40000}]}

    def text_sender(text):
        calls.append(text)
        return {"message_id": 9001}

    fres = send_frames(repo, photo_sender, text_sender, now=sent_at,
                       frames=fr)
    check("accept/both-frames-arrive-as-photos",
          fres["sent"] == ["review_day1_noon.jpg", "review_day1_noon.jpg"]
          and len(photo_calls) == 2, fres["sent"])
    cap_text = photo_calls[0][1] if photo_calls else ""
    check("accept/the-caption-is-exactly-one-line",
          "\n" not in cap_text and cap_text.count("http") == 1, cap_text)
    check("accept/the-caption-names-the-frame-and-the-sha",
          "review_day1_noon" in cap_text and "cb4767e" in cap_text, cap_text)
    print("      caption: %s" % cap_text)
    prec = _read(repo, photo_receipt_rel("review_day1_noon.jpg", "cb4767e",
                                         "now"))
    check("accept/the-receipt-carries-the-photo-descriptor",
          prec and "photoSizes: 90x67/800x600" in prec
          and "photoSizeCount: 2" in prec and "messageId: 8123" in prec,
          (prec or "")[:120])
    print("      says: %s" % frames_done_line(fres))
    check("accept/imagesSent-carries-its-denominator",
          "imagesSent=2/2" in frames_done_line(fres), frames_done_line(fres))

    long_sha = "x" * (CAPTION_CAP + 50)
    capped, was, dropped = caption_for("review_day1_noon.jpg", "now", long_sha)
    check("accept/the-caption-cap-announces-itself",
          was and len(capped) <= CAPTION_CAP
          and "more character(s) not shown" in capped, len(capped))
    check("accept/a-short-caption-is-not-capped",
          not caption_for("review_day1_noon.jpg", "now", "cb4767e")[1])

    # Rejecting: report-frame withheld.
    wf = parse_frames(1, "report-frame: no commit in the last 40 touching "
                         "review_day1_noon.jpg came from a run that measured "
                         "anything")
    said = []
    wres = send_frames(repo, photo_sender, lambda t: said.append(t)
                       or {"message_id": 1}, now=sent_at, frames=wf)
    check("reject/a-withheld-frame-sends-no-image-and-says-nothing-measured",
          wres["sent"] == [] and len(photo_calls) == 2 and len(said) == 1
          and "nothing measured" in said[0]
          and "imagesSent=0/0" in frames_done_line(wres),
          frames_done_line(wres))
    check("reject/and-the-refusal-reaches-him-in-report-frames-own-words",
          said and "measured anything" in said[0],
          (said[0][:90] if said else "SILENT"))

    # Rejecting: a named candidate whose file is absent.
    gone = {"ok": True, "candidates": [
        {"role": "now", "path": os.path.join(repo, "no-such-frame.jpg"),
         "sha": "cb4767e", "frame": "no-such-frame.jpg"}]}
    gres = send_frames(repo, photo_sender, text_sender, now=sent_at,
                       frames=gone)
    check("reject/an-absent-frame-is-reported-by-name",
          gres["sent"] == [] and len(gres["refused"]) == 1
          and "no-such-frame.jpg" in gres["refused"][0][0]
          and "imagesSent=0/1" in frames_done_line(gres),
          frames_done_line(gres))

    # Rejecting: oversized.
    big = os.path.join(repo, "big.jpg")
    with open(big, "wb") as fh:
        fh.write(b"\x00" * 32)
    real_max = PHOTO_MAX_BYTES
    globals()["PHOTO_MAX_BYTES"] = 16
    bres = send_frames(repo, photo_sender, text_sender, now=sent_at,
                       frames={"ok": True, "candidates": [
                           {"role": "now", "path": big, "sha": "cb4767e",
                            "frame": "big.jpg"}]})
    globals()["PHOTO_MAX_BYTES"] = real_max
    check("reject/an-oversized-file-is-refused-with-its-measured-size",
          bres["sent"] == [] and len(bres["refused"]) == 1
          and "32 byte(s)" in bres["refused"][0][1], bres["refused"])

    # Rejecting: the platform filed it as a document, so no descriptor.
    dres = send_frames(repo, lambda p, c: {"message_id": 5},
                       text_sender, now=sent_at,
                       frames={"ok": True, "candidates": [
                           {"role": "now", "path": shot, "sha": "cb4767e",
                            "frame": "review_day1_noon.jpg"}]})
    check("reject/no-photo-descriptor-means-it-did-not-arrive-as-a-photo",
          dres["sent"] == [] and len(dres["refused"]) == 1
          and "document" in dres["refused"][0][1], dres["refused"])

    # ---- RULING 1, 2026-09-07: THE CLIP -----------------------------------
    # "the clip goes to Telegram with a one-line verdict." Built the same
    # way the picture is: size checked before any upload, ACCEPTING CASE
    # FIRST, then every failure planted rather than assumed.
    print("")
    clip_path = os.path.join(repo, "playtest-selftest.mp4")
    with open(clip_path, "wb") as fh:
        fh.write(b"\x00\x00\x00\x18ftypmp42" + b"m" * 400)

    check("accept/a-clip-under-the-limit-passes-video-refusal",
          video_refusal(clip_path) == (True, "", os.path.getsize(clip_path)),
          video_refusal(clip_path))

    real_video_max = VIDEO_MAX_BYTES
    globals()["VIDEO_MAX_BYTES"] = 16
    vok, vwhy, vsize = video_refusal(clip_path)
    globals()["VIDEO_MAX_BYTES"] = real_video_max
    check("reject/a-clip-over-the-limit-is-refused-with-its-measured-size",
          not vok and "byte(s)" in vwhy and str(vsize) in vwhy
          and vsize == os.path.getsize(clip_path), (vwhy, vsize))

    mvok, mvwhy, _mvsize = video_refusal(os.path.join(repo, "no-clip.mp4"))
    check("reject/a-missing-clip-is-named-not-guessed",
          not mvok and "not on this disk" in mvwhy, mvwhy)

    short_cap, short_capped, _sd = cap_caption("street ok, 5/5 checks passed")
    check("accept/a-short-verdict-caption-is-not-capped",
          not short_capped and short_cap == "street ok, 5/5 checks passed",
          short_cap)
    long_cap, long_capped, long_dropped = cap_caption("x" * (CAPTION_CAP + 40))
    check("reject/an-over-cap-verdict-caption-is-capped-and-announces-it",
          long_capped and len(long_cap) <= CAPTION_CAP
          and "more character(s) not shown" in long_cap
          and long_dropped == 40, (len(long_cap), long_dropped))

    video_calls = []

    def video_sender(path, caption):
        video_calls.append((path, caption))
        return {"message_id": 7001,
                "video": {"width": 1280, "height": 720, "duration": 12,
                          "file_size": os.path.getsize(clip_path)}}

    def video_text_sender(text):
        calls.append(text)
        return {"message_id": 9101}

    # NOT JUST video_refusal IN ISOLATION: send_video ITSELF must refuse
    # BEFORE any upload is attempted. A spy sender proves it is never
    # called, which video_refusal alone cannot show.
    over_video_calls = []

    def over_video_sender(path, caption):
        over_video_calls.append(path)
        return {"message_id": 9999, "video": {"width": 1, "height": 1}}

    globals()["VIDEO_MAX_BYTES"] = 16
    r_over_clip = send_video(repo, over_video_sender, video_text_sender,
                             clip_path, "oversized clip verdict",
                             role="oversized-check", run_sha="abc1234",
                             now=sent_at)
    globals()["VIDEO_MAX_BYTES"] = real_video_max
    check("reject/send_video-refuses-an-oversized-clip-before-any-upload",
          r_over_clip["sent"] == [] and len(r_over_clip["refused"]) == 1
          and len(over_video_calls) == 0
          and "byte(s)" in r_over_clip["refused"][0][1]
          and str(os.path.getsize(clip_path)) in r_over_clip["refused"][0][1],
          r_over_clip["refused"])

    r_vid = send_video(repo, video_sender, video_text_sender, clip_path,
                       "The street textured, the walking camera worked, "
                       "collision held: 5/5.", role="clip", run_sha="abc1234",
                       now=sent_at)
    check("accept/a-clip-under-the-limit-is-sent-as-a-video",
          r_vid["sent"] == [clip_path] and len(video_calls) == 1
          and r_vid["withheld"] == "" and not r_vid["refused"], r_vid["sent"])
    vid_rec_rel = video_receipt_rel(clip_path, "abc1234", "clip")
    vid_rec = _read(repo, vid_rec_rel)
    check("accept/the-video-receipt-carries-the-platforms-descriptor",
          vid_rec and "receipt: video" in vid_rec
          and "descriptorKind: video" in vid_rec
          and "videoDescriptor: 1280x720/12s" in vid_rec
          and "messageId: 7001" in vid_rec, (vid_rec or "")[:160])
    check("accept/the-video-receipt-is-readable-by-receipt-is-valid",
          receipt_is_valid(vid_rec or "") == (True, 7001),
          receipt_is_valid(vid_rec or ""))
    print("      says: %s" % video_done_line(r_vid))
    check("accept/video-done-line-carries-its-denominator",
          "sent=1/1" in video_done_line(r_vid), video_done_line(r_vid))

    # ACCEPT: sendAnimation's own descriptor key is recognised too, under
    # ITS OWN NAME (descriptorKind), never guessed as `video`.
    def anim_sender(path, caption):
        return {"message_id": 7002,
                "animation": {"width": 640, "height": 360, "duration": 8}}

    r_anim = send_video(repo, anim_sender, video_text_sender, clip_path,
                        "anim verdict", role="anim-check", run_sha="abc1234",
                        now=sent_at)
    anim_rec = _read(repo, video_receipt_rel(clip_path, "abc1234",
                                             "anim-check"))
    check("accept/sendAnimations-own-descriptor-key-is-recognised",
          r_anim["sent"] == [clip_path]
          and anim_rec and "descriptorKind: animation" in anim_rec
          and "videoDescriptor: 640x360/8s" in anim_rec, (anim_rec or "")[:160])

    # REJECT: neither key populated, the platform filed it as a document.
    r_doc = send_video(repo, lambda p, c: {"message_id": 8}, video_text_sender,
                       clip_path, "doc verdict", role="doc-check",
                       run_sha="abc1234", now=sent_at)
    check("reject/no-video-or-animation-descriptor-means-no-receipt",
          r_doc["sent"] == [] and len(r_doc["refused"]) == 1
          and "document" in r_doc["refused"][0][1], r_doc["refused"])

    # REJECT then ACCEPT: a dead uplink leaves it unsent and retryable.
    def video_sender_down(path, caption):
        raise SendFailed("Could not reach Telegram at all (URLError)")

    r_vid_down = send_video(repo, video_sender_down, video_text_sender,
                            clip_path, "down verdict", role="down-check",
                            run_sha="abc1234", now=sent_at)
    check("reject/a-dead-uplink-leaves-the-clip-unsent-and-retryable",
          r_vid_down["sent"] == [] and len(r_vid_down["failed"]) == 1,
          r_vid_down["failed"])
    r_vid_retry = send_video(repo, video_sender, video_text_sender, clip_path,
                             "down verdict", role="down-check",
                             run_sha="abc1234", now=sent_at)
    check("accept/and-the-next-pass-sends-it",
          r_vid_retry["sent"] == [clip_path], r_vid_retry["sent"])

    # ACCEPT then REJECT: no clip this run travels as WORDS, never an old
    # clip reused.
    text_before = len(calls)
    r_withheld = send_video(repo, video_sender, video_text_sender, None,
                            "it did not launch: no clip this run",
                            role="clip", run_sha="abc1234", now=sent_at)
    check("accept/no-clip-is-sent-as-words-not-an-old-clip-reused",
          r_withheld["sent"] == [] and r_withheld["withheld"]
          and len(calls) == text_before + 1
          and "nothing measured" in calls[-1], calls[-1][:80])
    check("reject/video-done-line-marks-a-withheld-run",
          "withheld=1" in video_done_line(r_withheld),
          video_done_line(r_withheld))

    def dead_text_sender(text):
        raise SendFailed("Could not reach Telegram at all (URLError)")

    r_withheld_down = send_video(repo, video_sender, dead_text_sender, None,
                                 "it did not launch", role="clip",
                                 run_sha="abc1234", now=sent_at)
    check("reject/a-withheld-note-that-fails-to-send-is-counted-failed",
          r_withheld_down["sent"] == [] and len(r_withheld_down["failed"]) == 1,
          r_withheld_down["failed"])

    # ---- WHAT THE CONTAINER READS BACK ----------------------------------
    print("")
    records = {}
    for rel in inbox.outbound_files(repo):
        records[rel] = _read(repo, rel)
    summary = outbound_summary(records)
    lines = outbound_lines(summary)
    check("accept/the-container-side-counts-sent-and-refused",
          summary["records"] == len(records) and len(summary["sent"]) >= 2
          and len(summary["refused"]) >= 3 and not summary["unreadable"],
          "%d record(s)" % summary["records"])
    check("accept/and-prints-refused-K-with-its-denominator",
          any(("refused=%d" % len(summary["refused"])) in l
              and ("records=%d" % summary["records"]) in l for l in lines),
          lines[-1])
    print("      says: %s" % lines[-1])
    check("accept/and-a-refused-line-carries-the-clause",
          any(l.startswith("  outbound REFUSED") and "clause=" in l
              for l in lines), lines[:2])
    empty = outbound_lines(outbound_summary({}))
    check("reject/no-records-at-all-says-nothing-measured",
          any("nothing measured" in l for l in empty), empty)

    # RULING 5 and RULING 1 READ BACK: a captioned message and a clip are
    # NEITHER a plain "sent" text message NOR a sim-shot "photo", so each
    # gets its own bucket and its own count rather than being folded into
    # `sent` (which would silently change what `sent=` has meant since
    # queue 089) or into `photos`.
    check("accept/the-container-side-buckets-a-captioned-message-apart",
          len(summary.get("captioned") or []) == 1
          and summary["captioned"][0].get("messageId") == "6001"
          and summary["captioned"][0].get("receipt") == "sent-with-photo",
          summary.get("captioned"))
    check("accept/a-captioned-message-does-not-inflate-plain-sent",
          not any(f.get("messageId") == "6001" for f in summary["sent"]),
          [f.get("messageId") for f in summary["sent"]])
    check("accept/the-container-side-buckets-a-video-apart",
          len(summary.get("videos") or []) == 3
          and {f.get("messageId") for f in summary["videos"]} == {"7001",
                                                                  "7002"},
          summary.get("videos"))
    check("accept/videos-do-not-land-in-photos-or-sent",
          not any(f.get("messageId") in ("7001", "7002")
                  for f in summary["photos"] + summary["sent"]),
          [f.get("messageId") for f in summary["photos"] + summary["sent"]])
    check("accept/the-tally-line-carries-captioned-and-videos-with-their-"
          "own-counts",
          ("captioned=%d" % len(summary.get("captioned") or [])) in lines[-1]
          and ("videos=%d" % len(summary.get("videos") or [])) in lines[-1],
          lines[-1])
    print("      says: %s" % lines[-1])
    check("accept/nothing-in-the-new-buckets-is-unreadable",
          not summary["unreadable"], summary["unreadable"])

    # ---- A4: A BOT REPLY IS NOT A PRODUCER MESSAGE ----------------------
    # Ruled 2026-09-07. `sent=` is what queue 089 defined as messages the
    # studio composed and that reached his phone. Every bot reply now writes
    # a receipt of the same shape, so without this split one key would mean
    # two things and `sent=` would count every hello and every read-back.
    sent_before = len(summary["sent"])
    with_reply = dict(records)
    with_reply["production/outbound/2026-09-07T101010Z-reply-60677.receipt.txt"] = (
        "receipt: sent\nfile: production/outbound/x\n"
        "kind: bot-message\nfileCommit: none\n"
        "sent: 2026-09-07T10:10:10Z\nsentEpoch: 1788000610\n"
        "messageId: 60677\nchars: 12\noutboundLatencySec: nothing-measured\n")
    s2 = outbound_summary(with_reply)
    l2 = outbound_lines(s2)
    check("accept/a4-a-bot-reply-is-counted-as-a-reply",
          len(s2["replies"]) == 1 and s2["replies"][0]["messageId"] == "60677",
          s2["replies"])
    check("reject/a4-and-is-NOT-counted-as-a-producer-message",
          len(s2["sent"]) == sent_before, "sent=%d was %d"
          % (len(s2["sent"]), sent_before))
    check("accept/a4-the-done-line-carries-both-keys",
          ("sent=%d" % sent_before) in l2[-1] and "replies=1" in l2[-1],
          l2[-1])
    check("accept/a4-the-replies-tally-is-one-line-with-the-newest-id",
          sum(1 for l in l2 if "outbound replies" in l) == 1
          and any("newestMessageId=60677" in l for l in l2),
          [l for l in l2 if "outbound replies" in l])


def selftest():
    """The whole suite, and it REPORTS ON EVERY PATH.

    Exit 0 every case passed, 3 a case failed, 4 the suite itself raised. The
    count line is printed by `run_selftest` before this function sees the
    code, so a crash below still reaches ledger/verify.py as numbers plus a
    distinct exit rather than as no line at all.
    """
    code, ok, bad, state = run_selftest(
        "outbox", _selftest_cases,
        "THE WIRE IS NOT COVERED: every send above went to a scripted "
        "stand-in, so the Telegram half is unverifiable until it runs on "
        "the PC.")
    print("fixture: %s"
          % (("%s (left on disk for reading)" % state["fixture"])
             if state.get("fixture")
             else "nothing measured, the suite ended before one was made"))
    print("outbox selftest exit=%d meaning=%s casesRun=%d casesFailed=%d"
          % (code, SELFTEST_MEANING[code], len(ok) + len(bad), len(bad)))
    return code


if __name__ == "__main__":
    # A correct run that ends in a BrokenPipeError traceback costs twenty
    # minutes before anybody notices it worked, and this file is read through
    # `| head` more often than not.
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    sys.exit(selftest() if "--selftest" in sys.argv else selftest())
