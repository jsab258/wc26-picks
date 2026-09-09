#!/usr/bin/env python3
"""A WAKE DELIVERED MID-TURN IS LOST. A DUE RECORD ON DISK IS NOT.

    python3 tools/wake-queue.py arm --due 2026-09-10T04:00Z \
            --by director/daily --instruction "Plan the day, write the brief"
    python3 tools/wake-queue.py due                  # what is owed right now
    python3 tools/wake-queue.py discharge 7f3c1a2b   # one done, with the instant
    python3 tools/wake-queue.py series               # the printer a bound comes from
    python3 tools/wake-queue.py drain --hook         # the Stop hook calls this
    python3 tools/wake-queue.py --selftest           # accepting case FIRST

THE FAULT, read off the scheduler's own record for trigger
`trig_013itgDeay6t41BHEmaYFbAj` ("LEDGER daily: wake, plan the day, produce
the brief", cron `0 4 * * *`, bound to the session with persist_session):

    last_run.status       ROUTINE_RUN_STATUS_SUCCEEDED
    last_run.fired_at     2026-09-09T04:09:00.554885534Z
    last_run.finished_at  2026-09-09T04:09:00.567166Z

TWELVE AND A HALF MILLISECONDS, reported SUCCEEDED. No brief was written in
12 ms and none was sent. SUCCEEDED means THE WAKE WAS DELIVERED TO THE
SESSION, not that the work happened: the session was mid-turn, the injected
user turn was absorbed into the turn already running, and the day's brief
never existed. It has cost a brief at least twice; the other instance is
`trig_01Lb3XS3RcsAEDTgTfXpwmma`, fired 2026-09-09T04:00:57Z, filed as
`production/queue/174-an-armed-trigger-is-half-a-promise.md`. It is the same
shape `.claude/rules/ci.md` already has a rule for on another surface: verify
a job's EFFECTS, not its exit code.

WHAT CANNOT BE FIXED FROM INSIDE THIS REPOSITORY, and is not pretended
otherwise anywhere below: the scheduler's delivery semantics. Nothing here can
make the platform hold a turn. So the repair is not "stop losing the wake", it
is STOP THE WAKE BEING THE ONLY DELIVERY. The wake becomes a durable due
record on disk at the moment it is armed, and the TURN BOUNDARY is where it is
read and drained (`.claude/hooks/wake-drain.sh`, registered as the Stop hook in
`.claude/settings.json`). A wake that lands mid-turn then changes nothing: the
record was already on disk before the trigger fired, and it is still due at the
end of whatever turn absorbed it.

WHERE THE RECORDS LIVE, AND WHY THERE. `production/wakes/`, TRACKED IN GIT.
Not under `tools/` (that tree is instruments, not state) and not inside any
directory a workflow writes to, because a trigger living inside an output
directory is the shape where a run's own output re-fires its producer: the
comment at the top of `.github/workflows/ledger-imagegen.yml` is that trap
written out in full. Checked rather than assumed before choosing: no workflow
under `.github/workflows/` names `production/wakes`, and `.gitignore` ignores
`production/logs/` and `production/scratch/` and nothing else under
`production/`. Tracked because the container is ephemeral and reclaimed after
inactivity, so a queue in /tmp is a queue that dies with the machine, which is
the failure this file exists to remove.

A DISCHARGED RECORD IS KEPT, NOT DELETED. The history is the evidence that the
mechanism worked: `armedAt` / `due` / `dischargedAt` on one line of one file is
the paired reading that says a wake was served, and deleting it would leave the
same empty directory as a wake that was never armed.

HOW THE DIRECTORY IS BOUNDED: IT IS NOT, AND THAT IS DELIBERATE (rule 2).
There is no series. Zero records existed when this was written, so nothing here
invents a sweep threshold: `series` is the printer, it prints records per UTC
day and total bytes, and a bound is set from what it prints after real runs.
The arithmetic meanwhile: one daily trigger is 1 record/day at about 300 bytes,
which is 0.1 MB a year. That is a reason not to be in a hurry, not a measured
bound, and it is not written anywhere as one.

CLOCK DISCIPLINE. Every instant is UTC and carries the Z. A naive instant is
REFUSED by `arm` rather than guessed at, because a local-time record is a wake
that fires an hour out twice a year. An offset-bearing instant is converted and
the conversion is printed. Sub-second digits are dropped, which moves a due
instant EARLIER by under a second: a wake is never made later than it was
asked for. `now` is an injectable parameter everywhere, so the selftest plants
instants in the past and in the future and watches both outcomes instead of
sleeping.

THE LOOP HAZARD, AND IT IS REAL. A Stop hook that always blocks makes a
session that can never stop. Three things bound it, and the first two were read
off the Claude Code binary at /opt/claude-code/bin/claude on 2026-09-09 rather
than remembered:

  1. `stop_hook_active` in the Stop payload. The binary's own words: "For
     Stop/SubagentStop hooks, check stop_hook_active in the input and return
     success while it's true." Honoured here: exit 13, permit, and the line
     names what stays due.
  2. THE PLATFORM'S OWN CAP IS 8 CONSECUTIVE BLOCKS, and that is a measurement:
     `let Ad=a.CLAUDE_CODE_STOP_HOOK_BLOCK_CAP??8; if(Ad>0&&_c>Ad)` ... "A hook
     blocked the turn from ending ${_c} consecutive times - overriding and
     ending turn". Its notice goes to the transcript and to nowhere a later
     session can read.
  3. BLOCK_CAP below, which is THE NUMBER THIS FILE OWNS, and it is 3 because
     of 2: ours has to bite FIRST so the notice lands in a tracked record
     (`capBitAt`) instead of only in a transcript nobody can grep. Note which
     statistic each cap is OF, because they are not the same one: the
     platform's 8 is CONSECUTIVE blocks in one chain, `blocks` here is
     CUMULATIVE PER RECORD over that record's whole life. Cumulative per
     record is the more conservative of the two in a loop (a loop re-blocks
     the same record, so it rises monotonically and reaches 3 long before the
     platform's 8), and it is also the one that survives a container reclaim,
     because it lives in the record rather than in the client.

And the fourth thing, which is the real loop-breaker: THE WORK DISCHARGES ITS
OWN RECORD, so the next boundary finds nothing due.

WHAT THIS HOOK DOES NOT DO, said out loud because a Stop hook here has a
history (`ledger-v2/studio-v2/learning.md` L32, `production/queue/014`): it
never asks for a commit, never looks at the working tree, and never mentions a
clean tree. It drains wakes. Nothing else.

EXIT CODES, DISTINCT PER OUTCOME, because a reader piping this into a decision
must not have to parse prose:

    0   it ran: armed / discharged / records examined and none due
    2   NOTHING MEASURED: the directory holds no wake record at all
    3   the selftest failed
    4   REFUSED: an id already armed, or a discharge of an unknown or
        already-discharged id. The file is left BYTE-UNCHANGED.
    10  BLOCK: at least one record is due. The ONLY code the hook blocks on.
    11  permit, LOUD: the per-record block cap bit and the record says so
    12  permit, LOUD: the payload on stdin could not be read (fail open)
    13  permit: `stop_hook_active` was true, a platform chain is in progress
    14  permit, LOUD: the records directory could not be read (fail open)

FAIL OPEN, DELIBERATELY AND OUT LOUD. Every failure of this instrument permits
the stop. A broken drain that blocks is a session that can never end; a broken
drain that permits delays a wake whose record is still on disk and still due.
Recoverable against unrecoverable, the same trade `.claude/hooks/verify-gate.sh`
names for a cross-repository commit.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from capsay import cap, NOTHING_MEASURED                          # noqa: E402

#: Where the records live, repo-relative. The docstring says why here and
#: nowhere else.
WAKE_DIR_REL = "production/wakes"

#: A wake record, and NOTHING else: `2026-09-10T0400Z-7f3c1a2b.wake.txt`.
#: The same denominator discipline as `tools/runner/inbox.py:NAME_RE` and for
#: the same reason: a README dropped in that folder is outside every count,
#: rather than counted as a record this tool cannot read.
#:
#: `.txt` RATHER THAN A NEW SUFFIX, and that was measured rather than assumed.
#: `tools/attribution-check.py` sweeps the whole repository and FAILS on any
#: suffix in neither ASSET_SUFFIXES nor NOT_ASSET_SUFFIXES, so a `.wake` file
#: would have turned `ledger/verify.py` red on its first run. `.txt` is already
#: on the not-an-asset list. `.md` would have put these files in front of
#: `tools/docs-check.py` and `tools/producer-check.py`, which is the mistake
#: `inbox.py` records having already made once.
NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{4}Z-[0-9a-f]{8}\.wake\.txt$")

#: THE FIELD ORDER IN A RECORD, FIXED. A stable order is what makes a diff
#: readable, and a record whose keys move is a record every future reader has
#: to sort before comparing.
FIELDS = ("id", "due", "armedAt", "armedBy", "blocks", "dischargedAt",
          "capBitAt")

#: THE ONE SPELLING OF "THIS HAS NOT HAPPENED YET" in a record. One field per
#: fact, never a `discharged: no` beside a `dischargedAt:` that can disagree
#: with it: two fields for one fact is one fact twice, and the copy nobody
#: updates is the one somebody reads.
UNSET = "-"

#: CUMULATIVE PER RECORD, not consecutive per chain, and the docstring says why
#: that distinction is the whole safety argument. 3 because the platform
#: overrides at 8 (CLAUDE_CODE_STOP_HOOK_BLOCK_CAP, default read off the binary
#: 2026-09-09) and ours must bite first so the notice reaches a tracked file.
#: THIS IS NOT A MEASURED DISTRIBUTION: no drain had ever run when it was set.
#: `series` prints `blocksBeforeDischarge` per record, and that is what may
#: argue for moving it.
BLOCK_CAP = 3

#: How many due instructions the block reason carries in full. The cap
#: announces itself through `capsay.cap`, so a sixth due wake is never
#: silently dropped from the reason that is supposed to carry it.
REASON_KEEP = 5

#: PER-ITEM WIDTH FOR THE BLOCK REASON, and it exists because of a measured
#: failure rather than a worry: `capsay.cap` defaults to 90 characters per
#: item, which cut an entry down to
#:     [53ab1f03] due 2026-09-09T04:09:00Z, armed ..., b...
#: and took the instruction AND the discharge command off the end of the only
#: message that reaches the model. The `...` announced the cut, so it was a cap
#: that bit honestly on the content it exists to deliver. 2000 is about six
#: times the longest instruction this project has written; when it does bite,
#: `capsay` marks it.
REASON_WIDTH = 2000

# Exit codes. Named once, used everywhere, and listed in the docstring.
EXIT_OK = 0
EXIT_NOTHING_MEASURED = 2
EXIT_SELFTEST_FAILED = 3
EXIT_REFUSED = 4
EXIT_BLOCK = 10
EXIT_CAP_BIT = 11
EXIT_BAD_PAYLOAD = 12
EXIT_STOP_HOOK_ACTIVE = 13
EXIT_DIR_UNREADABLE = 14
#: A USAGE ERROR MAY NOT WEAR A MEASUREMENT'S CLOTHES. argparse exits 2 on a
#: bad flag, and 2 here means NOTHING MEASURED, so the hook would have read
#: "you called me wrong" as "the queue is empty" and permitted every stop for
#: ever while printing a usage message nobody reads. Measured, not reasoned:
#: the first run of the selftest did exactly that, because the hook passes
#: `--dir` AFTER the subcommand and argparse rejected it. 64 is EX_USAGE from
#: sysexits.h, and it is outside every code the hook models, so the hook's
#: unmodelled branch announces it instead of swallowing it.
EXIT_USAGE = 64


# ------------------------------------------------------------------ the clock

def parse_instant(text):
    """(aware datetime in UTC, None) or (None, reason).

    REFUSES A NAIVE INSTANT. `2026-09-10T04:00` carries no zone, and the
    machine that wrote it is not the machine that reads it: a local-time record
    is a wake that fires an hour out twice a year, and in this project the PC
    and the container do not even agree on a clock (`inbox-read` prints a
    NEGATIVE latency when they drift). So the refusal names the hazard.
    """
    s = (text or "").strip()
    if not s:
        return None, "no instant given"
    if " " in s:
        return None, ("the instant %r carries a space; every channel here "
                      "splits on whitespace" % s)
    iso = s[:-1] + "+00:00" if s.endswith("Z") else s
    try:
        dt = datetime.datetime.fromisoformat(iso)
    except ValueError:
        return None, ("%r is not an ISO instant (wanted "
                      "2026-09-10T04:00:00Z)" % s)
    if dt.tzinfo is None:
        return None, ("%r carries no zone. Every instant here is UTC and "
                      "carries the Z: a local-time record is a wake that "
                      "fires an hour out twice a year" % s)
    return dt.astimezone(datetime.timezone.utc), None


def iso_z(dt):
    """The one spelling of an instant in this file: seconds, UTC, Z.

    Sub-second digits are DROPPED, not rounded, so a due instant can only move
    EARLIER by under a second. A wake is never made later than it was asked
    for.
    """
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compact_z(dt):
    """`2026-09-10T0400Z`, the filename half of an instant. Same shape as
    `tools/runner/inbox.py:message_name` so the two folders sort alike."""
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H%MZ")


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


# ----------------------------------------------------------------- the record

def no_space(text):
    """A header VALUE with no whitespace in it. Header values are a `key: value`
    channel and every reader of one in this project splits on whitespace, so a
    space becomes a truncation nobody is told about. The INSTRUCTION is not a
    header value: it is the body, after the blank line, and may say anything."""
    return re.sub(r"\s+", "/", (text or "").strip()) or "unnamed"


def wake_id(due_iso, armed_by, instruction):
    """DETERMINISTIC, so arming the same wake twice is a refusal rather than a
    second copy of one obligation. 8 hex of sha1 over the three fields that
    make a wake what it is."""
    h = hashlib.sha1()
    h.update(("%s\x00%s\x00%s" % (due_iso, armed_by, instruction))
             .encode("utf-8"))
    return h.hexdigest()[:8]


def record_name(due_dt, wid):
    return "%s-%s.wake.txt" % (compact_z(due_dt), wid)


def render(rec):
    """The whole file. Header lines in FIELDS order, one blank line, the
    instruction.

    THE SHAPE IS `tools/runner/inbox.py`'s ON PURPOSE (header `key: value`
    lines, a blank line, then a body), so anybody who has read one of these
    folders can read the other. THE PARSER IS NOT SHARED, and that is a
    deliberate second implementation rather than an oversight: `parse_message`
    REQUIRES `sentEpoch` and returns Telegram fields, so reusing it would mean
    writing a fake Telegram epoch into a wake record to satisfy a validator
    that knows nothing about due instants. Grepped before writing this:
    `parse_message` is the only header parser in `tools/`, and it has one
    caller family, the inbox pair.
    """
    head = "".join("%s: %s\n" % (k, rec[k]) for k in FIELDS)
    body = (rec.get("instruction") or "").replace("\r\n", "\n").replace(
        "\r", "\n").strip()
    return head + "\n" + body + "\n"


def parse(content):
    """(rec, None) or (None, reason).

    The header is the lines BEFORE THE FIRST BLANK ONE, so an instruction that
    itself contains a blank line, or a line reading `due: tomorrow`, cannot be
    mistaken for a header.
    """
    if not content or not content.strip():
        return None, "the file is empty"
    parts = content.replace("\r\n", "\n").replace("\r", "\n").split("\n\n", 1)
    head, body = parts[0], (parts[1] if len(parts) > 1 else "")
    rec = {}
    for line in head.split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            rec[k.strip()] = v.strip()
    missing = [k for k in FIELDS if k not in rec]
    if missing:
        return None, ("no %s line in the %d header line(s)"
                      % ("/".join(missing), len(head.split("\n"))))
    for k in ("due", "armedAt"):
        dt, why = parse_instant(rec[k])
        if why:
            return None, "%s: %s" % (k, why)
        rec[k + "Dt"] = dt
    for k in ("dischargedAt", "capBitAt"):
        if rec[k] != UNSET:
            dt, why = parse_instant(rec[k])
            if why:
                return None, "%s: %s" % (k, why)
            rec[k + "Dt"] = dt
        else:
            rec[k + "Dt"] = None
    try:
        rec["blocks"] = int(rec["blocks"])
    except ValueError:
        # NOT defaulted to 0. A 0 would read as "this record has never blocked",
        # which is a finding; the truth is that the file cannot be read, and
        # those two must never print alike (rule 3b).
        return None, "blocks is not a whole number: %r" % rec["blocks"]
    rec["instruction"] = body.strip()
    if not rec["instruction"]:
        return None, "no instruction after the blank line"
    return rec, None


def is_discharged(rec):
    return rec["dischargedAt"] != UNSET


def cap_bit(rec):
    return rec["capBitAt"] != UNSET


# ------------------------------------------------------------- the directory

def resolve_dir(dir_arg):
    """A relative --dir is resolved against THE REPOSITORY, not the cwd.

    The Stop hook is handed whatever working directory the session happens to
    be standing in, and a records directory that moves with the cwd is a queue
    that silently splits in two.
    """
    p = pathlib.Path(dir_arg or WAKE_DIR_REL)
    return p if p.is_absolute() else (REPO / p)


def read_dir(dirpath):
    """Everything about the directory in one read, at one instant.

    Returns a dict. `examined` COUNTS the files whose name matches NAME_RE and
    nothing else, so it is the denominator of records and not of files:
    `skippedByName` is printed beside it, because a denominator larger than the
    set examined turns a clean result into a false claim with a number on it.
    """
    r = {"dir": str(dirpath), "exists": dirpath.is_dir(), "readable": True,
         "error": None, "records": [], "unreadable": [], "skipped": [],
         "examined": 0, "bytes": 0}
    if not r["exists"]:
        return r
    try:
        names = sorted(p.name for p in dirpath.iterdir() if p.is_file())
    except OSError as e:
        r["readable"] = False
        r["error"] = str(e)
        return r
    for name in names:
        if not NAME_RE.match(name):
            r["skipped"].append(name)
            continue
        r["examined"] += 1
        p = dirpath / name
        try:
            text = p.read_text(encoding="utf-8")
        except OSError as e:
            r["unreadable"].append((name, str(e)))
            continue
        r["bytes"] += len(text.encode("utf-8"))
        rec, why = parse(text)
        if why:
            r["unreadable"].append((name, why))
            continue
        rec["name"] = name
        rec["path"] = p
        r["records"].append(rec)
    # STABLE SORT, and by the due instant first: the order a reader wants is
    # the order things came due, and the id breaks a tie so two runs never
    # print the same set in two orders.
    r["records"].sort(key=lambda x: (x["dueDt"], x["id"]))
    return r


def due_now(records, now):
    """The set this whole file exists for: armed, not discharged, due instant
    passed. `now` is a parameter, never a hidden clock read."""
    return [r for r in records
            if not is_discharged(r) and r["dueDt"] <= now]


def waiting(records, now):
    return [r for r in records
            if not is_discharged(r) and r["dueDt"] > now]


def counts(reading, now):
    """Every number the done line carries, taken from ONE read of the
    directory at ONE instant, so no two of them are from different moments."""
    recs = reading["records"]
    n = reading["examined"]
    return {"examined": n,
            "due": len(due_now(recs, now)),
            "waiting": len(waiting(recs, now)),
            "discharged": len([r for r in recs if is_discharged(r)]),
            "unreadable": len(reading["unreadable"]),
            "skipped": len(reading["skipped"])}


def counts_text(reading, now, extra=""):
    """THE WHOLE-RUN NUMBERS AS ONE STRING, ONE IMPLEMENTATION. Every caller
    (arm, due, discharge, drain, series) prints this same string, so no two of
    them can come to disagree about what `wakesDue` is a fraction of.

    Per-record numbers go on the per-record lines; these are the run's, and
    they are never split across two lines a grep would merge into one moment.

    THREE OUTCOMES, THREE DIFFERENT STRINGS, which is the whole of rule 3b on
    this surface: a directory that could not be read, a directory holding no
    record at all, and a directory holding records none of which is due.
    """
    c = counts(reading, now)
    where = "dir=%s" % no_space(reading["dir"])
    if not reading["readable"]:
        return ("wakesDue=%s %s COULD-NOT-READ-THE-DIRECTORY: %s"
                % (NOTHING_MEASURED, where,
                   no_space(reading["error"] or "unknown")))
    if c["examined"] == 0:
        return ("wakesDue=%s 0 record(s) under %s/ (nothing has ever been "
                "armed here, or every record was swept; %d non-record file(s) "
                "skipped by name) now=%s%s"
                % (NOTHING_MEASURED, reading["dir"], c["skipped"], iso_z(now),
                   extra))
    return ("wakesDue=%d/%d records examined, notYetDue=%d/%d "
            "discharged=%d/%d unreadable=%d/%d skippedByName=%d %s now=%s%s"
            % (c["due"], c["examined"], c["waiting"], c["examined"],
               c["discharged"], c["examined"], c["unreadable"], c["examined"],
               c["skipped"], where, iso_z(now), extra))


def done_line(kind, reading, now, extra=""):
    """The run's line for a human-run subcommand."""
    return "wake-queue %s done %s" % (kind, counts_text(reading, now, extra))


def drain_line(verdict, reading, now, extra=""):
    """THE HOOK'S LINE, and every outcome of the hook prints one: a reader
    grepping `wake-drain:` across a day gets one line per turn boundary,
    whichever way the boundary went."""
    return "wake-drain: %s %s" % (verdict, counts_text(reading, now, extra))


def record_line(rec, now):
    """THE PER-RECORD LINE: this record's own numbers and nothing the run
    aggregated. `blocks` is cumulative over this record's life."""
    if is_discharged(rec):
        state = "discharged"
    elif cap_bit(rec):
        state = "CAPPED"
    elif rec["dueDt"] <= now:
        state = "DUE"
    else:
        state = "waiting"
    return ("  %-10s id=%s due=%s armedAt=%s armedBy=%s blocks=%d/%d "
            "dischargedAt=%s capBitAt=%s"
            % (state, rec["id"], rec["due"], rec["armedAt"], rec["armedBy"],
               rec["blocks"], BLOCK_CAP, rec["dischargedAt"], rec["capBitAt"]))


def write_atomic(path, text):
    """Temp file then replace, so a record is never half-written: a crash
    between two writes would otherwise leave a record this tool counts as
    unreadable, and an unreadable record is a wake nobody can serve."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / (path.name + ".tmp-%d" % os.getpid())
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(str(tmp), str(path))


# ----------------------------------------------------------------------- arm

def arm(dirpath, due_text, instruction, armed_by, now):
    """(rec, None) or (None, (reason, code)). Writes one record.

    IDEMPOTENT BY CONSTRUCTION. The id is a hash of the due instant, the armer
    and the instruction, so arming the same wake twice REFUSES and leaves the
    file byte-unchanged rather than filing one obligation twice.
    """
    due, why = parse_instant(due_text)
    if why:
        return None, ("REFUSED: --due %s" % why, EXIT_REFUSED)
    instruction = (instruction or "").strip()
    if not instruction:
        return None, ("REFUSED: an empty instruction is a wake nobody can "
                      "serve", EXIT_REFUSED)
    by = no_space(armed_by)
    due_iso = iso_z(due)
    wid = wake_id(due_iso, by, instruction)
    rec = {"id": wid, "due": due_iso, "armedAt": iso_z(now), "armedBy": by,
           "blocks": 0, "dischargedAt": UNSET, "capBitAt": UNSET,
           "instruction": instruction}
    path = dirpath / record_name(due, wid)
    if path.exists():
        old, bad = parse(path.read_text(encoding="utf-8"))
        if bad:
            return None, ("REFUSED: %s already exists and cannot be read (%s). "
                          "Nothing was written." % (path.name, bad),
                          EXIT_REFUSED)
        if old["instruction"] != instruction or old["armedBy"] != by:
            # A COLLISION IS NOT A DUPLICATE, and a tool that prints the same
            # sentence for both sends the reader looking for the wrong thing.
            return None, ("REFUSED: id %s is taken by a DIFFERENT wake "
                          "(armedBy=%s). 8 hex of sha1 collided; change the "
                          "instruction or the due minute. Nothing was "
                          "written." % (wid, old["armedBy"]), EXIT_REFUSED)
        return None, ("REFUSED: already armed as %s (armedAt=%s, "
                      "dischargedAt=%s). The file is byte-unchanged."
                      % (path.name, old["armedAt"], old["dischargedAt"]),
                      EXIT_REFUSED)
    write_atomic(path, render(rec))
    # READ IT BACK THROUGH THE PARSER, and that is not ceremony. A dict built
    # here carries no `dueDt`, and every reporting function in this file works
    # on a PARSED record: the first version returned the hand-built dict and
    # `arm` ended in a KeyError traceback AFTER writing the file correctly,
    # which is the shape that costs twenty minutes before somebody notices it
    # worked. Reading it back also means `arm` proves the round trip on every
    # real run, not only in the selftest.
    back, why = parse(path.read_text(encoding="utf-8"))
    if why:
        return None, ("WROTE %s AND COULD NOT READ IT BACK: %s. The file is on "
                      "disk; this tool cannot parse it." % (path.name, why),
                      EXIT_REFUSED)
    back["name"] = path.name
    back["path"] = path
    return back, None


def report_arm(dirpath, due_text, instruction, armed_by, now, say=print):
    rec, err = arm(dirpath, due_text, instruction, armed_by, now)
    if err:
        say("wake-queue arm " + err[0])
        reading = read_dir(dirpath)
        say(done_line("arm", reading, now))
        return err[1]
    reading = read_dir(dirpath)
    say("wake-queue arm WROTE %s/%s" % (reading["dir"], rec["name"]))
    say(record_line(rec, now))
    say("  instruction: %s" % rec["instruction"].replace("\n", " / "))
    say(done_line("arm", reading, now))
    return EXIT_OK


# ----------------------------------------------------------------- discharge

def discharge(dirpath, wid, now):
    """(rec, None) or (None, (reason, code)).

    TWO REFUSALS, AND THEY SAY WHICH: an id that does not exist, and an id
    already discharged. Both leave every file BYTE-UNCHANGED, which the
    selftest asserts by comparing bytes and not by reading the message.
    """
    reading = read_dir(dirpath)
    if not reading["readable"]:
        return None, ("REFUSED: %s cannot be read (%s)"
                      % (reading["dir"], reading["error"]), EXIT_REFUSED)
    hit = [r for r in reading["records"] if r["id"] == wid]
    if not hit:
        known = [r["id"] for r in reading["records"]]
        return None, ("REFUSED: no record with id %s among %d examined (%s). "
                      "Nothing was written."
                      % (wid, reading["examined"],
                         cap(known, keep=6, sep=",",
                             tail="the directory holds no record at all")),
                      EXIT_REFUSED)
    rec = hit[0]
    if is_discharged(rec):
        return None, ("REFUSED: %s was already discharged at %s. The file is "
                      "byte-unchanged." % (wid, rec["dischargedAt"]),
                      EXIT_REFUSED)
    rec["dischargedAt"] = iso_z(now)
    write_atomic(rec["path"], render(rec))
    return rec, None


def report_discharge(dirpath, wid, now, say=print):
    rec, err = discharge(dirpath, wid, now)
    reading = read_dir(dirpath)
    if err:
        say("wake-queue discharge " + err[0])
        say(done_line("discharge", reading, now))
        return err[1]
    say("wake-queue discharge DONE %s at %s (armed %s, due %s, blocks=%d "
        "cumulative)" % (rec["id"], rec["dischargedAt"], rec["armedAt"],
                         rec["due"], rec["blocks"]))
    say(done_line("discharge", reading, now))
    return EXIT_OK


# ----------------------------------------------------------------------- due

def report_due(dirpath, now, say=print):
    """The listing. Per-record lines, then the run's done line.

    EXIT CODES ARE THE POINT HERE: 0 records were examined and none is due,
    2 nothing was measured, 10 something is due, 14 the directory refused to be
    read. A caller can branch without parsing a sentence.
    """
    reading = read_dir(dirpath)
    if not reading["readable"]:
        say(done_line("due", reading, now))
        return EXIT_DIR_UNREADABLE
    for name, why in reading["unreadable"]:
        say("  UNREADABLE %s: %s" % (name, why))
    for rec in reading["records"]:
        say(record_line(rec, now))
        if rec["dueDt"] <= now and not is_discharged(rec):
            say("             instruction: %s"
                % rec["instruction"].replace("\n", " / "))
    say(done_line("due", reading, now))
    if reading["examined"] == 0:
        return EXIT_NOTHING_MEASURED
    return EXIT_BLOCK if due_now(reading["records"], now) else EXIT_OK


# --------------------------------------------------------------------- drain

def session_crons(payload):
    """COUNT of session-scoped cron tasks the platform reports in THIS Stop
    payload. Last-wins at this boundary, not cumulative and not a peak.

    The field is `session_crons` and it is OPTIONAL: its schema in the Claude
    Code binary reads "Session-scoped cron tasks (CronCreate, ScheduleWakeup,
    /loop) that will wake this session later. Empty array when none are
    scheduled." So an ABSENT field and an EMPTY array are different facts and
    print differently: the words when absent, 0 when the platform said zero.
    This is the paired half of `wakesDue`: what the platform thinks is armed,
    beside what disk thinks is owed. On the morning of the incident the first
    was 1 and the second was 0, and nothing anywhere printed both.
    """
    if not isinstance(payload, dict) or "session_crons" not in payload:
        return None
    v = payload.get("session_crons")
    return len(v) if isinstance(v, list) else None


def drain(payload_text, dirpath, now):
    """THE TURN BOUNDARY. (code, lines, reason).

    `lines` is what goes to stdout on every outcome. `reason` is non-empty ONLY
    for EXIT_BLOCK, and it is what the hook puts on stderr for the model to
    read.

    WRITES: on a block it increments `blocks` on each record named in the
    reason, and when the cap bites it stamps `capBitAt`. Both live in the
    record, so the guard's state survives the container that is about to be
    reclaimed.
    """
    lines = []
    try:
        payload = json.loads(payload_text) if (payload_text or "").strip() \
            else None
    except ValueError:
        payload = None
    if not isinstance(payload, dict):
        lines.append("wake-drain: PERMIT-UNASSESSED reason=payload-unreadable "
                     "the-stop-payload-on-stdin-was-not-a-JSON-object. It "
                     "permits rather than block a turn it cannot assess; any "
                     "due record is still on disk and still due at the next "
                     "boundary.")
        return EXIT_BAD_PAYLOAD, lines, ""

    crons = session_crons(payload)
    active = payload.get("stop_hook_active") is True
    extra = (" sessionCrons=%s stopHookActive=%s"
             % (NOTHING_MEASURED if crons is None else crons,
                "true" if active else "false"))

    reading = read_dir(dirpath)
    if not reading["readable"]:
        lines.append(drain_line("PERMIT-UNASSESSED", reading, now, extra))
        return EXIT_DIR_UNREADABLE, lines, ""
    if reading["examined"] == 0:
        lines.append(drain_line("PERMIT", reading, now, extra))
        return EXIT_NOTHING_MEASURED, lines, ""

    owed = due_now(reading["records"], now)
    if not owed:
        lines.append(drain_line("PERMIT", reading, now, extra))
        return EXIT_OK, lines, ""

    if active:
        # THE PLATFORM'S OWN FLAG, HONOURED. Its words: return success while
        # it is true. Nothing is incremented and nothing is stamped, because
        # no block is being issued.
        lines.append("wake-drain: PERMIT reason=stop_hook_active a platform "
                     "continuation chain is already running; %d record(s) "
                     "stay due and the next clean boundary serves them: %s"
                     % (len(owed), cap([r["id"] for r in owed], keep=REASON_KEEP,
                                       sep=",", tail=NOTHING_MEASURED)))
        lines.append(drain_line("PERMIT", reading, now, extra))
        return EXIT_STOP_HOOK_ACTIVE, lines, ""

    capped = [r for r in owed if r["blocks"] >= BLOCK_CAP]
    serveable = [r for r in owed if r["blocks"] < BLOCK_CAP]

    if not serveable:
        # THE CAP BIT, AND IT SAYS SO ON THREE CHANNELS: this line, the
        # record's own capBitAt, and the next `due` listing's CAPPED state. A
        # cap that does not announce when it bit reads as a finding.
        for rec in capped:
            if not cap_bit(rec):
                rec["capBitAt"] = iso_z(now)
                write_atomic(rec["path"], render(rec))
        lines.append("wake-drain: PERMIT-CAP-BIT the per-record block cap of "
                     "%d bit on %d of %d due record(s): %s. It permits the "
                     "stop rather than loop. THE WAKE IS NOT LOST: the "
                     "record(s) stay undischarged on disk and carry capBitAt. "
                     "Something in the work is not discharging them."
                     % (BLOCK_CAP, len(capped), len(owed),
                        cap(["%s(blocks=%d)" % (r["id"], r["blocks"])
                             for r in capped], keep=REASON_KEEP, sep=",",
                            tail=NOTHING_MEASURED)))
        lines.append(drain_line("PERMIT", reading, now, extra))
        return EXIT_CAP_BIT, lines, ""

    for rec in serveable:
        rec["blocks"] += 1
        write_atomic(rec["path"], render(rec))

    shown = []
    for rec in serveable:
        shown.append("[%s] due %s, armed %s by %s, blocks=%d/%d\n      %s\n"
                     "      discharge it: python3 tools/wake-queue.py "
                     "discharge %s"
                     % (rec["id"], rec["due"], rec["armedAt"], rec["armedBy"],
                        rec["blocks"], BLOCK_CAP,
                        rec["instruction"].replace("\n", "\n      "),
                        rec["id"]))
    reason = [
        "WAKE DUE AT THE TURN BOUNDARY. This turn either absorbed a scheduled "
        "wake or one came due while it ran, which is the 2026-09-09T04:09 "
        "fault: a trigger reports SUCCEEDED when the wake is DELIVERED, not "
        "when the work happens.",
        "",
        "%d of %d record(s) under %s/ is/are due and undischarged. Do the work "
        "below, then discharge each record so the next boundary is silent."
        % (len(serveable), reading["examined"], reading["dir"]),
        "",
        "  " + cap(shown, keep=REASON_KEEP, width=REASON_WIDTH, sep="\n  ",
                   tail=NOTHING_MEASURED),
    ]
    if capped:
        reason += ["", "AND %d due record(s) are NOT in the list above: the "
                       "per-record block cap of %d has already bitten on them "
                       "(%s). They stay on disk; nothing will block for them "
                       "again." % (len(capped), BLOCK_CAP,
                                   cap([r["id"] for r in capped],
                                       keep=REASON_KEEP, sep=",",
                                       tail=NOTHING_MEASURED))]
    reason += ["",
               "This hook does not ask for a commit and does not look at the "
               "working tree. If an instruction is obsolete, discharge it and "
               "say so in the record's own history rather than editing it out."]
    lines.append(drain_line("BLOCK", reading, now, extra))
    return EXIT_BLOCK, lines, "\n".join(reason)


def report_drain(dirpath, now, payload_text, say=print, err=None):
    """Prints the one `wake-drain:` line, then the reason when there is one.

    TWO CHANNELS, AND THE SPLIT IS THE CONTRACT. The one-line verdict with its
    denominators goes to STDOUT on every outcome, so a reader greps one line
    per turn boundary whichever way the boundary went. The BLOCK reason goes to
    `err`, which the hook leaves as stderr because stderr is what Claude Code
    feeds back to the model for a Stop hook. Run by hand without `--hook`,
    `err` is stdout too, so a person reads it in order.
    """
    code, lines, reason = drain(payload_text, dirpath, now)
    for l in lines:
        say(l)
    if reason:
        (err or say)(reason)
    return code


# -------------------------------------------------------------------- series

def _median(xs):
    if not xs:
        return None
    s = sorted(xs)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2.0


def report_series(dirpath, now, say=print):
    """THE PRINTER A BOUND COMES FROM, and it sets none (rule 2).

    Three series, each named for the statistic it is: records ARMED per UTC
    day, blocks BEFORE DISCHARGE per record, and the directory's total bytes.
    Nothing here is a threshold. When a sweep bound is eventually wanted, it
    comes from what this printed over real runs, in that order.
    """
    reading = read_dir(dirpath)
    if not reading["readable"]:
        say(done_line("series", reading, now))
        return EXIT_DIR_UNREADABLE
    if reading["examined"] == 0:
        say(done_line("series", reading, now))
        say("  NO SWEEP BOUND IS SET and none is invented here. When this has "
            "printed real days, a bound may be argued from them.")
        return EXIT_NOTHING_MEASURED

    per_day = {}
    for rec in reading["records"]:
        day = rec["armedAt"][:10]
        d = per_day.setdefault(day, {"armed": 0, "discharged": 0,
                                     "blocks": 0})
        d["armed"] += 1
        d["discharged"] += 1 if is_discharged(rec) else 0
        d["blocks"] += rec["blocks"]
    for day in sorted(per_day):
        d = per_day[day]
        say("  day=%s armed=%d dischargedOfThoseArmed=%d blocksSum=%d"
            % (day, d["armed"], d["discharged"], d["blocks"]))

    armed_counts = [per_day[d]["armed"] for d in per_day]
    peak_day = max(per_day, key=lambda d: per_day[d]["armed"])
    blocks_done = [r["blocks"] for r in reading["records"]
                   if is_discharged(r)]
    # PAIRED READING: the value and where it peaked, one entry, never two keys
    # whose relationship the reader has to remember.
    say("  armedPerDayPeak=%d@%s armedPerDayMedian=%s over %d day(s) holding "
        "any record" % (per_day[peak_day]["armed"], peak_day,
                        _median(armed_counts), len(per_day)))
    if blocks_done:
        worst = max(reading["records"],
                    key=lambda r: (r["blocks"] if is_discharged(r) else -1))
        say("  blocksBeforeDischargePeak=%d@%s blocksBeforeDischargeMedian=%s "
            "over %d discharged record(s) of %d examined. Cap in force is %d "
            "per record, CUMULATIVE."
            % (worst["blocks"], worst["id"], _median(blocks_done),
               len(blocks_done), reading["examined"], BLOCK_CAP))
    else:
        say("  blocksBeforeDischargePeak=%s blocksBeforeDischargeMedian=%s "
            "0 of %d examined record(s) has been discharged yet, so the cap "
            "has no series behind it and stays at its arithmetic value %d."
            % (NOTHING_MEASURED, NOTHING_MEASURED, reading["examined"],
               BLOCK_CAP))
    say("  bytes=%d over %d record(s). NO SWEEP BOUND IS SET: this is the "
        "series, and a bound comes from it rather than before it."
        % (reading["bytes"], reading["examined"]))
    say(done_line("series", reading, now))
    return EXIT_OK


# ----------------------------------------------------- is the hook REGISTERED

#: The registration this mechanism is nothing without. `rule 6`: built is not
#: running, and a drain nothing calls is a drain that runs never.
HOOK_REL = ".claude/hooks/wake-drain.sh"
HOOK_EVENT = "Stop"
HOOK_ENV = "WAKE_DIR"


def settings_reading(settings, repo=REPO):
    """(ok, detail) from a PARSED settings object. PURE, so the accepting
    fixture can be THE LIVE `.claude/settings.json` and the rejecting one a
    synthetic dict naming a hook that exists nowhere.

    That asymmetry is the instruments rule: pinning the rejecting case to a
    real asset would mean doing the work this tool asks for breaks the test.
    """
    if not isinstance(settings, dict):
        return False, "settings is not an object"
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return False, "no hooks block"
    entries = hooks.get(HOOK_EVENT)
    if not entries:
        return False, ("NO %s HOOK REGISTERED, so nothing drains the queue at "
                       "a turn boundary and every wake waits for somebody to "
                       "look. Registered events: %s"
                       % (HOOK_EVENT,
                          cap(sorted(hooks), keep=8, sep=",",
                              tail="none at all")))
    cmds = []
    for entry in entries if isinstance(entries, list) else []:
        for h in (entry or {}).get("hooks", []):
            cmds.append(str((h or {}).get("command", "")))
    named = [c for c in cmds if HOOK_REL in c]
    if not named:
        return False, ("the %s hook(s) registered do not name %s: %s"
                       % (HOOK_EVENT, HOOK_REL,
                          cap(cmds, keep=3, tail="no command at all")))
    withenv = [c for c in named if (HOOK_ENV + "=") in c]
    if not withenv:
        return False, ("%s is registered but no command sets %s=, so the hook "
                       "falls back to its own default instead of reading the "
                       "path settings.json names (the house pattern in "
                       "verify-gate.sh and session-start.sh): %s"
                       % (HOOK_REL, HOOK_ENV, cap(named, keep=3)))
    if not (pathlib.Path(repo) / HOOK_REL).exists():
        return False, ("%s is registered and MISSING FROM DISK, which is the "
                       "one shape that fails silently: the event fires, the "
                       "command is not found, and nothing drains."
                       % HOOK_REL)
    return True, ("%s -> %s with %s set (%d %s command(s) registered)"
                  % (HOOK_EVENT, HOOK_REL, HOOK_ENV, len(cmds), HOOK_EVENT))


#: THE OTHER HALF OF RULE 6, and it is weaker than the one above on purpose:
#: if the row is ever deleted from `ledger/verify.py`, verify stops running
#: this suite and therefore stops seeing this check go red. It is here because
#: it still catches the case somebody runs the tool by hand, and because three
#: lines is a cheap place to say out loud which guard cannot watch itself.
TOOL_ROW = "tools/wake-queue.py"


def registered_in_verify(verify_text):
    """Does `ledger/verify.py` name this tool at all? PURE: the live file is
    the accepting fixture, a synthetic register string the rejecting one."""
    return TOOL_ROW in (verify_text or "")


# ------------------------------------------------------------------ selftest
#
# ACCEPTING CASE FIRST, AND THE FIRST ONE IS THE EXPENSIVE DIRECTION. The
# failure that costs the project a day is not a drain that misses a wake; it is
# a Stop hook that blocks when nothing is due, because then the session can
# never end and the only way out is a human noticing. So case 1 is "the hook
# permits the stop", run as the hook, through bash, with the real payload shape
# on stdin.
#
# WHAT IS NOT COVERED, said here rather than discovered later: nothing in this
# suite talks to the scheduler. Whether the platform delivers a wake mid-turn
# is the fault being worked around and cannot be asserted from inside the
# repository; what IS asserted is that a record armed before a boundary is
# found AT that boundary by the hook as registered.

STOP_PAYLOAD = {
    "session_id": "selftest-session",
    "transcript_path": "/dev/null",
    "cwd": "/home/user/wc26-picks",
    "hook_event_name": "Stop",
    "stop_hook_active": False,
    "last_assistant_message": "done for now",
    "session_crons": [{"id": "trig_013itgDeay6t41BHEmaYFbAj",
                       "schedule": "0 4 * * *", "recurring": True,
                       "prompt": "LEDGER daily: wake, plan the day"}],
}


def _payload(**over):
    d = dict(STOP_PAYLOAD)
    d.update(over)
    return json.dumps(d)


def selftest():
    passed, failed = [], []

    def ok(label, cond, got=""):
        if cond:
            passed.append(label)
            print("  ok   %s" % label)
        else:
            failed.append(label)
            print("  FAIL %s  got: %s" % (label, got))

    work = pathlib.Path(tempfile.mkdtemp(prefix="wake-queue-selftest-"))
    try:
        return _selftest_body(work, ok, passed, failed)
    finally:
        # REGISTERED, not hoped for: a selftest that leaves a tree behind is a
        # selftest that dirties the repository it is about to be committed
        # from.
        shutil.rmtree(str(work), ignore_errors=True)


def _run_hook(wake_dir, payload_text):
    """The hook AS THE HOOK: bash, the real JSON shape on stdin, the env var
    settings.json names. Not an import of this module, because what is being
    proven is the registration and the exit-code contract, and an import
    proves neither."""
    hook = REPO / HOOK_REL
    p = subprocess.run(["bash", str(hook)], input=payload_text,
                       capture_output=True, text=True,
                       env=dict(os.environ, WAKE_DIR=str(wake_dir)),
                       cwd=str(REPO), timeout=60)
    return p.returncode, p.stdout, p.stderr


def _selftest_body(work, ok, passed, failed):
    # TWO CLOCKS, NAMED, because one of them cannot be injected.
    #
    # `t0` and `noon` are FIXED instants, used wherever a function is called
    # directly with an injected `now`. They are stable for ever: the same
    # fixture gives the same verdict on every day this suite is ever run.
    #
    # `past` and `future` are RELATIVE TO THE WALL CLOCK, and they are only
    # used for records the HOOK has to judge, because the hook reads the real
    # clock and nothing here may tell it otherwise. A hook with an injectable
    # clock is a hook that can be handed the wrong time, and the whole fault
    # this file is about is a wake judged against the wrong moment. The first
    # version of this suite planted 11:00 and ran at 08:03, and the case that
    # should have blocked quietly permitted.
    t0 = datetime.datetime(2026, 9, 9, 3, 0, tzinfo=datetime.timezone.utc)
    noon = datetime.datetime(2026, 9, 9, 12, 0, tzinfo=datetime.timezone.utc)
    real = now_utc()
    past = iso_z(real - datetime.timedelta(hours=1))
    future = iso_z(real + datetime.timedelta(days=400))
    empty = work / "empty"
    empty.mkdir()

    print("wake-queue selftest - ACCEPTING CASES FIRST. The expensive failure "
          "is a Stop hook that\nblocks when nothing is due, because then the "
          "session can never end.\n")

    # ---- 1. THE HOOK MUST NOT INTERFERE. Run as the hook, nothing due.
    code, out, err = _run_hook(empty, _payload())
    ok("accept/hook-with-an-empty-queue-PERMITS-the-stop", code == 0,
       (code, out, err))
    ok("accept/and-says-nothing-measured-rather-than-a-clean-zero",
       NOTHING_MEASURED in out and "0 record(s)" in out, out)
    ok("accept/and-writes-nothing-on-stderr-when-it-permits",
       err.strip() == "", err)

    # ---- 2. THE 2026-09-09T04:09 INCIDENT, as a record.
    #
    # The wake is ARMED before the turn, DUE during it, and NOBODY READS IT
    # between those two moments: that absence of a read IS the absorbed
    # injected turn. Then the boundary drains, and the record is still there.
    live = work / "wakes"
    live.mkdir()
    rec, err2 = arm(live, "2026-09-09T04:09:00Z",
                    "Wake, plan the day, produce the brief and send it "
                    "through the Producer.", "director/daily-brief", t0)
    ok("accept/arming-before-the-turn-writes-one-record", err2 is None
       and rec is not None, err2)
    ok("accept/the-record-is-on-disk-under-a-due-sorted-name",
       (live / ("2026-09-09T0409Z-%s.wake.txt" % rec["id"])).exists(),
       sorted(p.name for p in live.iterdir()))
    round_trip, why = parse((live / rec["name"]).read_text(encoding="utf-8"))
    ok("accept/it-round-trips-through-its-own-parser", why is None
       and round_trip["instruction"] == rec["instruction"]
       and round_trip["blocks"] == 0, why)
    ok("accept/every-header-value-carries-no-space",
       all(" " not in l.split(": ", 1)[1]
           for l in render(rec).split("\n\n", 1)[0].splitlines()),
       render(rec).split("\n\n", 1)[0])

    # NOBODY LOOKS between arm and boundary. The next statement is the
    # boundary. The due instant is the incident's own 04:09, which is in the
    # past at every moment from then on, so this fixture cannot rot.
    code, out, err = _run_hook(live, _payload())
    ok("accept/2026-09-09T0409-INCIDENT-the-absorbed-wake-is-found-at-the-"
       "boundary", code == 2, (code, out, err))
    ok("accept/INCIDENT-the-block-reason-reaches-the-model-on-STDERR",
       "produce the brief" in err, err)
    ok("accept/INCIDENT-the-reason-carries-the-discharge-command",
       ("discharge %s" % rec["id"]) in err, err)
    ok("accept/INCIDENT-the-verdict-line-stays-on-stdout-with-denominators",
       "wake-drain: BLOCK" in out and "wakesDue=1/1" in out, out)
    ok("accept/INCIDENT-the-platform-cron-count-rides-beside-the-disk-count",
       "sessionCrons=1" in out, out)
    after, _ = parse((live / rec["name"]).read_text(encoding="utf-8"))
    ok("accept/the-block-is-counted-in-the-record-itself",
       after["blocks"] == 1, after["blocks"])

    # ---- 3. DISCHARGE BREAKS THE LOOP, which is the whole bound on it.
    done, derr = discharge(live, rec["id"], noon)
    ok("accept/discharge-stamps-the-instant", derr is None
       and done["dischargedAt"] == "2026-09-09T12:00:00Z", derr)
    code, out, err = _run_hook(live, _payload())
    ok("accept/and-the-next-boundary-PERMITS-the-stop", code == 0,
       (code, out, err))
    ok("accept/and-the-discharged-record-is-KEPT-as-the-evidence",
       (live / rec["name"]).exists() and "discharged=1/1" in out, out)

    # ---- 4. A RECORD NOT YET DUE IS NOT A DUE RECORD, and the two zeros
    #         print differently (rule 3b).
    later, _ = arm(live, future, "Tomorrow's brief.",
                   "director/daily-brief", noon)
    code, out, err = _run_hook(live, _payload())
    ok("accept/a-future-record-does-not-block", code == 0, (code, out, err))
    ok("accept/and-0-of-2-reads-differently-from-nothing-measured",
       "wakesDue=0/2" in out and "notYetDue=1/2" in out
       and NOTHING_MEASURED not in out, out)

    # ---- 5. STOP_HOOK_ACTIVE IS HONOURED, the platform's own instruction.
    due2, _ = arm(live, past, "An earlier obligation.", "resident", noon)
    code, out, err = _run_hook(live, _payload(stop_hook_active=True))
    ok("accept/stop_hook_active-true-PERMITS-rather-than-chain", code == 0,
       (code, out, err))
    ok("accept/and-names-what-stays-due-instead-of-going-quiet",
       due2["id"] in out and "stopHookActive=true" in out, out)
    still, _ = parse((live / due2["name"]).read_text(encoding="utf-8"))
    ok("accept/and-counts-no-block-because-none-was-issued",
       still["blocks"] == 0, still["blocks"])

    # ---- 6. REJECTING: the refusals, byte-unchanged.
    before = (live / rec["name"]).read_bytes()
    r1, e1 = discharge(live, rec["id"], noon)
    ok("reject/discharging-twice-is-refused", r1 is None
       and e1[1] == EXIT_REFUSED and "already discharged" in e1[0], e1)
    ok("reject/and-leaves-the-file-BYTE-unchanged",
       (live / rec["name"]).read_bytes() == before)
    sizes = {p.name: p.read_bytes() for p in live.iterdir()}
    r2, e2 = discharge(live, "deadbeef", noon)
    ok("reject/discharging-an-unknown-id-is-refused", r2 is None
       and e2[1] == EXIT_REFUSED and "no record with id deadbeef" in e2[0], e2)
    ok("reject/and-names-the-denominator-it-searched",
       "among 3 examined" in e2[0], e2[0])
    ok("reject/and-writes-to-no-file-at-all",
       {p.name: p.read_bytes() for p in live.iterdir()} == sizes)
    r3, e3 = arm(live, future, "Tomorrow's brief.",
                 "director/daily-brief", noon)
    ok("reject/arming-the-same-wake-twice-is-refused", r3 is None
       and e3[1] == EXIT_REFUSED and "already armed" in e3[0], e3)
    ok("reject/and-the-first-record-is-byte-unchanged",
       (live / later["name"]).read_bytes() == sizes[later["name"]])

    # ---- 7. REJECTING: the clock.
    r4, e4 = arm(live, "2026-09-10T04:00:00", "No zone.", "resident", noon)
    ok("reject/a-naive-instant-is-refused-not-guessed", r4 is None
       and "carries no zone" in e4[0], e4)
    r5, e5 = arm(live, "not-an-instant", "Nonsense.", "resident", noon)
    ok("reject/a-non-instant-is-refused", r5 is None
       and "is not an ISO instant" in e5[0], e5)
    r6, e6 = arm(live, "2026-09-10T06:00:00+02:00", "An offset instant.",
                 "resident", noon)
    ok("accept/an-offset-instant-is-converted-to-Z", r6 is not None
       and r6["due"] == "2026-09-10T04:00:00Z", e6 or r6)
    r7, e7 = arm(live, "2026-09-11T04:00:00Z", "", "resident", noon)
    ok("reject/an-empty-instruction-is-refused", r7 is None
       and "empty instruction" in e7[0], e7)
    r8, e8 = arm(live, "2026-09-12T04:00:00Z", "Spaced armer.",
                 "a name with spaces", noon)
    ok("accept/an-armedBy-with-spaces-is-slugged-not-truncated",
       r8 is not None and r8["armedBy"] == "a/name/with/spaces", e8 or r8)

    # ---- 8. THE CAP BITES, AND IT SAYS SO. Planted, not loosened: the
    #         condition the guard asserts CAN happen is made to happen.
    loop = work / "loop"
    loop.mkdir()
    stuck, _ = arm(loop, past, "A wake nothing discharges.",
                   "director/daily-brief", t0)
    codes = []
    for _ in range(BLOCK_CAP):
        c, _o, _e = _run_hook(loop, _payload())
        codes.append(c)
    ok("accept/the-cap-blocks-up-to-its-bound-and-no-further",
       codes == [2] * BLOCK_CAP, codes)
    code, out, err = _run_hook(loop, _payload())
    ok("accept/and-then-PERMITS-rather-than-loop-forever", code == 0,
       (code, out, err))
    ok("accept/and-SAYS-the-cap-bit-with-its-number",
       "PERMIT-CAP-BIT" in out and ("cap of %d" % BLOCK_CAP) in out, out)
    ok("accept/and-says-the-wake-is-not-lost", "NOT LOST" in out, out)
    capped, _ = parse((loop / stuck["name"]).read_text(encoding="utf-8"))
    ok("accept/and-stamps-capBitAt-in-the-record-that-outlives-the-container",
       capped["capBitAt"] != UNSET and capped["blocks"] == BLOCK_CAP, capped)
    ok("accept/our-cap-bites-before-the-platforms-8-consecutive-blocks",
       BLOCK_CAP < 8)

    # ---- 9. REJECTING: a payload the hook cannot read FAILS OPEN, loudly.
    code, out, err = _run_hook(loop, "{ not json")
    ok("reject/an-unreadable-payload-permits-rather-than-wedge-the-session",
       code == 0, (code, out, err))
    ok("reject/and-says-PERMIT-UNASSESSED-rather-than-printing-a-clean-pass",
       "PERMIT-UNASSESSED" in out, out)
    (work / "not-a-dir.txt").write_text("I am a file.\n", encoding="utf-8")
    code, out, err = _run_hook(work / "not-a-dir.txt", _payload())
    ok("reject/a-records-path-that-is-a-file-permits-and-says-nothing-"
       "measured", code == 0 and NOTHING_MEASURED in out, (code, out))
    # AND THE ONE BRANCH THIS SUITE CANNOT PLANT: a directory that refuses to
    # be listed. It needs a permission this process does not lack (the suite
    # runs as root here, and root bypasses the mode bits that would plant it),
    # so what is asserted is the WORDING of that outcome, from a synthetic
    # reading, and the gap is named in the NOT COVERED sentence below rather
    # than left for somebody to assume it was tested.
    unreadable = {"dir": "/nowhere", "exists": True, "readable": False,
                  "error": "Permission denied", "records": [],
                  "unreadable": [], "skipped": [], "examined": 0, "bytes": 0}
    ok("accept/an-unreadable-directory-reads-as-nothing-measured-not-clean",
       NOTHING_MEASURED in counts_text(unreadable, noon)
       and "COULD-NOT-READ-THE-DIRECTORY" in counts_text(unreadable, noon),
       counts_text(unreadable, noon))

    # AND THE FAULT THE FIRST RUN OF THIS SUITE FOUND, kept as a case rather
    # than fixed and forgotten: the hook passes `--dir` AFTER the subcommand,
    # argparse rejected it, and argparse exits 2, which is this tool's code for
    # NOTHING MEASURED. Every boundary would have permitted while printing a
    # usage message into a channel nobody greps.
    p = subprocess.run(["python3", str(pathlib.Path(__file__).resolve()),
                        "drain", "--hook", "--dir", str(loop), "--nonsense"],
                       input=_payload(), capture_output=True, text=True,
                       timeout=60)
    ok("reject/a-usage-error-exits-64-and-never-2", p.returncode == EXIT_USAGE,
       (p.returncode, p.stderr))
    ok("reject/and-says-it-is-not-a-measurement",
       "NOT a measurement" in p.stderr, p.stderr)
    ok("accept/--dir-AFTER-the-subcommand-is-the-shape-the-hook-uses",
       subprocess.run(["python3", str(pathlib.Path(__file__).resolve()),
                       "due", "--dir", str(empty)], capture_output=True,
                      text=True, timeout=60).returncode
       == EXIT_NOTHING_MEASURED)

    # ---- 10. AN UNREADABLE RECORD IS NOT A MISSING ONE.
    broken = work / "broken"
    broken.mkdir()
    (broken / "2026-09-09T0400Z-aaaaaaaa.wake.txt").write_text(
        "id: aaaaaaaa\nthis is not a record\n", encoding="utf-8")
    (broken / "README.md").write_text("# not a record\n", encoding="utf-8")
    reading = read_dir(broken)
    ok("accept/a-malformed-record-is-counted-as-unreadable-not-dropped",
       reading["examined"] == 1 and len(reading["unreadable"]) == 1
       and len(reading["records"]) == 0, reading["unreadable"])
    ok("accept/a-README-is-outside-the-denominator-by-name",
       reading["skipped"] == ["README.md"], reading["skipped"])
    lines = []
    rc = report_due(broken, noon, say=lines.append)
    ok("accept/and-the-due-report-prints-it-with-its-denominator",
       rc == EXIT_OK and any("unreadable=1/1" in l for l in lines),
       lines[-1:])

    # ---- 11. EXIT CODES ARE DISTINCT PER OUTCOME, so a caller branches
    #          without parsing a sentence.
    ok("accept/due-on-an-empty-directory-exits-nothing-measured",
       report_due(empty, noon, say=lambda *a: None) == EXIT_NOTHING_MEASURED)
    # THE CLOCK MUST BE THE ONE THE FIXTURE WAS ARMED ON, and this line read
    # the other one until 2026-09-09. `loop` is armed at `past`, which is REAL
    # now minus an hour, while `noon` is frozen at 12:00Z. The two agree only
    # while the real clock is before 13:00Z, so this case passed every morning
    # and turned red at one in the afternoon with nothing changed. It is the
    # mirror of the fault the comment at the top of this section records: that
    # one planted a fixed hour and judged it against the real clock, and the
    # repair introduced this one by making the fixture real and leaving the
    # assertion frozen. TWO CLOCKS AND ONE FIXTURE.
    ok("accept/due-with-something-due-exits-10",
       report_due(loop, real, say=lambda *a: None) == EXIT_BLOCK)
    future = work / "future"
    future.mkdir()
    arm(future, "2027-01-01T04:00:00Z", "Next year.", "resident", noon)
    ok("accept/due-with-a-record-that-is-not-due-yet-exits-0",
       report_due(future, noon, say=lambda *a: None) == EXIT_OK)
    ok("accept/the-seven-outcome-codes-are-seven-different-numbers",
       len({EXIT_OK, EXIT_NOTHING_MEASURED, EXIT_BLOCK, EXIT_CAP_BIT,
            EXIT_BAD_PAYLOAD, EXIT_STOP_HOOK_ACTIVE, EXIT_DIR_UNREADABLE})
       == 7)

    # ---- 12. THE SERIES PRINTS, AND SETS NO BOUND.
    lines = []
    rc = report_series(live, noon, say=lines.append)
    ok("accept/the-series-prints-per-day-rows-with-a-peak-and-its-position",
       rc == EXIT_OK and any(re.search(r"armedPerDayPeak=\d+@\d{4}-\d\d-\d\d",
                                       l) for l in lines), lines)
    ok("accept/and-says-plainly-that-no-sweep-bound-is-set",
       any("NO SWEEP BOUND IS SET" in l for l in lines), lines[-2:])
    lines = []
    report_series(empty, noon, say=lines.append)
    ok("accept/and-an-empty-directory-prints-the-words-not-a-zero-series",
       any(NOTHING_MEASURED in l for l in lines), lines)

    # ---- 13. THE HOOK IS REGISTERED. The LIVE settings.json is the accepting
    #          fixture; the rejecting one names a hook that exists nowhere, so
    #          doing the work this tool asks for can never break the test.
    live_settings = REPO / ".claude" / "settings.json"
    try:
        parsed = json.loads(live_settings.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        parsed, why = None, str(e)
        ok("accept/the-live-settings-json-parses", False, why)
    else:
        ok("accept/the-live-settings-json-parses", True)
    good, detail = settings_reading(parsed if isinstance(parsed, dict) else {})
    ok("accept/THE-LIVE-settings.json-REGISTERS-THIS-HOOK-rule-6", good,
       detail)
    bad, why = settings_reading({"hooks": {"Stop": [{"hooks": [{
        "command": "bash .claude/hooks/no-such-hook-ffffffff.sh"}]}]}})
    ok("reject/a-synthetic-registration-naming-a-hook-that-exists-nowhere",
       not bad and "do not name" in why, why)
    bad2, why2 = settings_reading({"hooks": {"SessionStart": []}})
    ok("reject/a-settings-with-no-Stop-event-at-all", not bad2
       and "NO STOP HOOK REGISTERED" in why2.upper(), why2)
    bad3, why3 = settings_reading({"hooks": {"Stop": [{"hooks": [{
        "command": "bash " + HOOK_REL}]}]}})
    ok("reject/a-registration-that-sets-no-env-var-is-refused", not bad3
       and HOOK_ENV in why3, why3)

    # ---- 14. AND THE PROOF RUNS AT EVERY COMMIT, or it decays. The live
    #          `ledger/verify.py` is the accepting fixture; the rejecting one
    #          is a synthetic register that does not name this tool.
    vtext = (REPO / "ledger" / "verify.py").read_text(encoding="utf-8")
    ok("accept/ledger-verify.py-RUNS-this-selftest-at-every-commit-rule-6",
       registered_in_verify(vtext),
       "no row under TOOL_SELFTESTS names this tool, so nothing runs this "
       "suite and it decays")
    ok("reject/a-synthetic-register-that-omits-the-row-is-refused",
       not registered_in_verify(
           "TOOL_SELFTESTS = (\n    ('inbox', 'tools/runner/inbox.py'),\n)\n"))

    print("\nwake-queue selftest: %d passed, %d failed, %d case(s) run. "
          "NOT COVERED, named rather than left to be assumed: (1) nothing here "
          "talks to the scheduler, which is the fault being worked around and "
          "cannot be asserted from inside this repository; (2) the "
          "could-not-list-the-directory branch is asserted at its wording "
          "only, because this process runs as root and root cannot plant an "
          "unreadable directory. What IS asserted end to end is that a record "
          "armed before a boundary is found AT the boundary by the hook as "
          "registered, through bash, on the real payload shape."
          % (len(passed), len(failed), len(passed) + len(failed)))
    if failed:
        print("failed: " + cap(failed, keep=8, sep=", "))
    return EXIT_SELFTEST_FAILED if failed else EXIT_OK


# ---------------------------------------------------------------------- main

class UsageIsNotAMeasurement(argparse.ArgumentParser):
    """argparse exits 2 on a bad flag and 2 here means NOTHING MEASURED.

    Left alone, a mistyped call reads to the Stop hook as an empty queue: it
    permits the stop, prints a usage message into a channel nobody greps, and
    every wake waits for ever. This exits EXIT_USAGE instead, which is outside
    every code the hook models, so the hook says PERMIT-UNASSESSED out loud.
    """

    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write("wake-queue USAGE ERROR (exit %d, which is NOT a "
                         "measurement and not an empty queue): %s\n"
                         % (EXIT_USAGE, message))
        sys.exit(EXIT_USAGE)


def main(argv):
    # `--selftest` AS WELL AS THE SUBCOMMAND, because `ledger/verify.py` runs
    # every tool in TOOL_SELFTESTS as `<tool> --selftest` through ONE helper.
    # A tool that accepted only a subcommand would need a second runner there,
    # which is the one-idea-two-implementations shape this project pays for.
    if "--selftest" in argv:
        return selftest()

    # `--dir` AND `--now` WORK ON EITHER SIDE OF THE SUBCOMMAND, and that is
    # not a convenience: the hook's call is `drain --hook --dir <path>`, which
    # a top-level-only option rejects with a usage error. One shared parent
    # parser rather than the same two flags copied onto six subparsers.
    # `SUPPRESS` is load-bearing: without it a subparser writes its own default
    # over a value the top level already parsed, silently, and `--dir X drain`
    # would quietly drain the default directory instead.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dir", default=argparse.SUPPRESS,
                        help="records directory; a relative path is resolved "
                             "against the repository, never the cwd "
                             "(default %s)" % WAKE_DIR_REL)
    common.add_argument("--now", default=argparse.SUPPRESS,
                        help="the instant to read the queue AT, UTC with a Z. "
                             "Injectable so a test can plant a due instant in "
                             "the past or the future without sleeping.")

    ap = UsageIsNotAMeasurement(
        description=__doc__.splitlines()[0], parents=[common],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", parser_class=UsageIsNotAMeasurement)

    p_arm = sub.add_parser("arm", parents=[common],
                           help="write one durable due record")
    p_arm.add_argument("--due", required=True,
                       help="when it comes due, UTC with a Z")
    p_arm.add_argument("--instruction", required=True,
                       help="what the turn boundary must make happen")
    p_arm.add_argument("--by", default="unnamed",
                       help="who armed it; spaces become /")

    sub.add_parser("due", parents=[common],
                   help="records whose due instant has passed")
    p_dis = sub.add_parser("discharge", parents=[common],
                           help="mark one done, with the instant")
    p_dis.add_argument("id")
    p_drain = sub.add_parser("drain", parents=[common],
                             help="the Stop hook's decision")
    p_drain.add_argument("--hook", action="store_true",
                         help="read the Stop payload on stdin")
    sub.add_parser("series", parents=[common],
                   help="the printed series a bound comes from")
    sub.add_parser("selftest", parents=[common],
                   help="both outcomes, accepting case first")

    args = ap.parse_args(argv)
    if args.cmd in (None,):
        ap.print_help()
        return EXIT_OK
    if args.cmd == "selftest":
        return selftest()

    now_arg = getattr(args, "now", None)
    if now_arg:
        now, why = parse_instant(now_arg)
        if why:
            print("wake-queue REFUSED: --now %s" % why)
            return EXIT_REFUSED
    else:
        now = now_utc()
    dirpath = resolve_dir(getattr(args, "dir", WAKE_DIR_REL))

    if args.cmd == "arm":
        return report_arm(dirpath, args.due, args.instruction, args.by, now)
    if args.cmd == "due":
        return report_due(dirpath, now)
    if args.cmd == "discharge":
        return report_discharge(dirpath, args.id, now)
    if args.cmd == "series":
        return report_series(dirpath, now)
    if args.cmd == "drain":
        # WITHOUT `--hook` THE PAYLOAD IS AN EMPTY OBJECT, not an empty
        # string: a person running this by hand is asking what the boundary
        # would do, and answering "the payload was unreadable" to a question
        # nobody asked would send them looking for a fault that is not there.
        # It still COUNTS A BLOCK exactly as the hook would; `due` is the
        # read-only half and is the one to use for looking.
        payload = sys.stdin.read() if args.hook else "{}"

        def to_stderr(text):
            sys.stderr.write(text + "\n")

        return report_drain(dirpath, now, payload,
                            err=to_stderr if args.hook else print)
    ap.print_help()
    return EXIT_OK


if __name__ == "__main__":
    # A correct run that ends in a BrokenPipeError traceback costs twenty
    # minutes before anybody notices it worked.
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    sys.exit(main(sys.argv[1:]))
