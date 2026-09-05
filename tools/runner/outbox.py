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
    rc, out = inbox.git_call(["log", "-1", "--format=%H %ct", "--", rel], repo)
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


def sweep(repo, sender, now=None, say=None, only=None):
    """Check and send every unsent file in the outbox. Returns a dict.

    `sender(text)` is the wire, injected so the selftest can drive every path
    without a network. It returns the platform's result payload, or raises
    SendFailed.
    """
    say = say or (lambda _s: None)
    now = int(now if now is not None else time.time())
    res = {"files": [], "sent": [], "refused": [], "already": [],
           "held": [], "failed": [], "bad_receipt": [], "records": [],
           "samples": []}
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
    """
    n = len(res["files"])
    sent, ref = len(res["sent"]), len(res["refused"])
    already, held = len(res["already"]), len(res["held"])
    failed, bad = len(res["failed"]), len(res["bad_receipt"])
    unsent = n - sent - already
    return ("outbox done: outboxFiles=%d sent=%d refused=%d unsent=%d "
            "alreadySent=%d held=%d sendFailed=%d receiptRefused=%d "
            "recordsWritten=%d latencySamples=%d/%d outboundLatencySecAtWorst=%s"
            % (n, sent, ref, unsent, already, held, failed, bad,
               len(res["records"]), len(res["samples"]), sent,
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
    line = " ".join(line.split())
    if len(line) <= CAPTION_CAP:
        return line, False, 0
    dropped = len(line) - CAPTION_CAP
    tail = " (+%d more character(s) not shown)" % dropped
    return line[:CAPTION_CAP - len(tail)] + tail, True, dropped


def photo_refusal(repo, path):
    """(ok, why, bytes). A missing file is named; an oversized one carries its
    MEASURED size rather than a guess or a truncation."""
    try:
        size = os.path.getsize(path)
    except OSError:
        return False, ("the file report-frame named is not on this disk: %s"
                       % path), None
    if size > PHOTO_MAX_BYTES:
        return False, ("%s is %d byte(s), over the %d byte photo limit, so it "
                       "is refused rather than truncated"
                       % (os.path.basename(path), size, PHOTO_MAX_BYTES)), size
    if size == 0:
        return False, "%s is 0 byte(s) on this disk" % os.path.basename(path), 0
    return True, "", size


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
# What the container reads back off the branch
# --------------------------------------------------------------------------
def outbound_summary(records):
    """{name: content} off the branch to a summary. The arithmetic lives here
    because here is where the tests run.

    Returns counts and the lines to print. `refused=K` is the number the
    container side owes queue 089: a Producer message that could not be sent
    is a fact the studio has to learn without walking the PC's disk.
    """
    out = {"records": len(records), "sent": [], "refused": [], "photos": [],
           "unreadable": []}
    for name in sorted(records):
        fields, why = parse_record(records[name] or "")
        if fields is None:
            out["unreadable"].append((name, why))
            continue
        if fields.get("receipt") == "sent":
            out["sent"].append(fields)
        elif fields.get("receipt") == "photo":
            out["photos"].append(fields)
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
    for f in summary["photos"]:
        lines.append("  outbound photo  frame=%s role=%s runSha=%s "
                     "messageId=%s photoSizes=%s"
                     % (f.get("frame", "?"), f.get("role", "?"),
                        f.get("runSha", "?"), f.get("messageId", "?"),
                        f.get("photoSizes", "none")))
    for f in summary["refused"]:
        lines.append("  outbound REFUSED file=%s kind=%s hold=%s clause=%s"
                     % (f.get("file", "?"), f.get("kind", "?"),
                        f.get("hold", "?"), f.get("clause", "?")))
    for name, why in summary["unreadable"]:
        lines.append("  outbound UNREADABLE %s (%s)" % (name, why))
    lines.append("outbound: records=%d sent=%d refused=%d photos=%d "
                 "unreadable=%d"
                 % (summary["records"], len(summary["sent"]),
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


def selftest():
    import tempfile
    ok, bad = [], []

    def check(name, cond, detail=""):
        (ok if cond else bad).append(name)
        print("  %-46s %s%s" % (name, "pass" if cond else "FAIL",
                                (" : " + str(detail)) if not cond else ""))

    pc = _load_producer_check()
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
    repo = _fixture_repo(tmp)
    good_rel = "%s/2026-09-05-a-good-one.unprompted.md" % OUTBOX_DIR
    commit_at = 1788600000
    _commit(repo, good_rel, pc.GOOD, when=commit_at)
    sent_at = commit_at + 42

    calls = []

    def sender(text):
        calls.append(text)
        return {"message_id": 4711, "date": sent_at}

    r = sweep(repo, sender, now=sent_at)
    check("accept/a-good-message-is-checked-and-sent",
          r["sent"] == [good_rel] and len(calls) == 1
          and pc.GOOD.strip()[:20] in calls[0],
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
    over_rel = "%s/2026-09-05-far-too-long.unprompted.md" % OUTBOX_DIR
    _commit(repo, over_rel, pc.GOOD + ("\nword " * 200) + "\n",
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
    _commit(repo, nokind_rel, pc.GOOD, when=commit_at)
    r4 = sweep(repo, sender, now=sent_at + 240, only=nokind_rel)
    nk = r4["refused"][0][1] if r4["refused"] else ""
    check("reject/a-name-with-no-kind-is-refused-not-guessed",
          r4["sent"] == [] and ".unprompted.md" in nk and ".answer.md" in nk
          and ".brief.md" in nk, nk)

    noid_rel = "%s/2026-09-05-no-id-back.unprompted.md" % OUTBOX_DIR
    _commit(repo, noid_rel, pc.GOOD, when=commit_at)

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
    _commit(repo, bad_rel, pc.GOOD, when=commit_at)
    _write(repo, receipt_rel(bad_rel), "receipt: sent\nfile: %s\n" % bad_rel)
    r6 = sweep(repo, sender, now=sent_at + 420, only=bad_rel)
    check("reject/a-receipt-with-no-id-is-refused",
          r6["sent"] == [] and len(r6["bad_receipt"]) == 1
          and "messageId" in r6["bad_receipt"][0][1]
          and "receiptRefused=1" in done_line(r6), done_line(r6))

    def sender_down(text):
        raise SendFailed("Could not reach Telegram at all (URLError)")

    down_rel = "%s/2026-09-05-uplink-down.unprompted.md" % OUTBOX_DIR
    _commit(repo, down_rel, pc.GOOD, when=commit_at)
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

    print("\noutbox selftest: %d passed, %d failed (%d case(s) run). "
          "THE WIRE IS NOT COVERED: every send above went to a scripted "
          "stand-in, so the Telegram half is unverifiable until it runs on "
          "the PC." % (len(ok), len(bad), len(ok) + len(bad)))
    print("fixture: %s (left on disk for reading)" % tmp)
    return 3 if bad else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else selftest())
