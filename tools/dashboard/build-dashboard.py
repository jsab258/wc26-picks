#!/usr/bin/env python3
"""Build the studio status dashboard: a read-only lens over repo state.

    python3 tools/dashboard/build-dashboard.py            # write the two artifacts
    python3 tools/dashboard/build-dashboard.py --selftest  # accepting case first
    python3 tools/dashboard/build-dashboard.py --print     # STATUS.md to stdout, write nothing

WHAT IT IS. Deterministic, zero model calls. It reads repo files and writes
exactly two artifacts: dashboard.html and STATUS.md at the repo root. It is
NEVER a second source of truth: if a number here is wrong, the source file or
this generator is wrong, and this page is not the place to fix it.

WHY IT IS DANGEROUS, which is why the honesty machinery below is not
decoration. A dashboard is read at a GLANCE, so it is the highest-leverage
place in this project to print the fault this project keeps paying for: a zero
that means "I could not find out" reading as a zero that means "fine". So:

  * Every number is a Reading. A Reading is either MEASURED, carrying the
    one-line derivation and the denominator that were used to produce it, or
    UNAVAILABLE, carrying the reason. There is no third state, and an
    unavailable Reading cannot render as a number.
  * Reading.measured refuses a zero with no denominator, at construction. The
    rule stops being a thing somebody remembers.
  * A source that does not exist yet (night logs, a calibrated judge, a money
    spend ledger) renders as "not yet applicable" with the reason and the list
    of paths that were checked. Never as 0.
  * A truncated list says so, through tools/capsay.py, which is the one
    implementation of that idea in this repo. This file adds no second one.
  * Text echoed from a source is displayed with em dashes replaced, because
    the formatting law binds what this program WRITES. The source is never
    touched.

THE SINGLE WRITE PATH. write_artifact() is the only function in this file that
writes anything, and it refuses any filename other than the two artifacts. The
selftest proves that statically (an AST walk over this file: every write call
site is either that function or the selftest's own temp fixture) and at run
time (a generation into a temp directory creates exactly two files and leaves
the repo it read untouched). Weekly process audit check 9 asks for that proof.

EXIT CODES. 0 wrote both artifacts (or --print). 1 selftest failed. 2 a write
failed. 3 the repo root does not look like this repo. 4 a helper module this
program refuses to run without (tools/capsay.py) could not be imported: a
truncation notice that silently stops announcing is the fault this whole file
is about, so it stops rather than carrying on without one.
"""
import argparse
import ast
import datetime
import html
import importlib.util
import pathlib
import re
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent

HTML_NAME = "dashboard.html"
STATUS_NAME = "STATUS.md"
ARTIFACTS = (HTML_NAME, STATUS_NAME)

REFRESH_SECONDS = 300
FOOTER_LINE = "Derived from repo state. If wrong, fix the source, never this page."

# TWO CAPS, BOTH SET FROM A PRINTED SERIES RATHER THAN FROM TASTE, and both
# announce through capsay when they bite.
#
# GATE_KEEP: the gate strip is as long as the sim's ALL GATES line. Measured
# over every kept run in game-design/sim-shots/runs/: 358 files, 244 carrying
# an ALL GATES line, and the pill count is 72 in every single one of them
# (min = median = max = 72; the other 114 files carry no gate line at all).
# 120 sits well above that so the cap does not bite on any run this project
# has ever produced, while still bounding a page that would otherwise grow
# without limit. The same sweep found 7 bracketed continuations across those
# 244 runs and 0 unparsed fragments, which is why parse_gate_line counts
# continuations instead of dropping them.
#
# INFLIGHT_KEEP: the list is NOW.md's own bullets plus started queue tasks
# plus two fixed rows. Today that is 6 (2 bullets, 2 started tasks, D1, the
# night runner). 12 is double the only reading there is, which is stated
# plainly rather than dressed up as a measurement.
INFLIGHT_KEEP = 12
GATE_KEEP = 120


def _load(path, name):
    """Import a hyphenated tool module by path. None when it is not there."""
    try:
        spec = importlib.util.spec_from_file_location(name, str(path))
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:                                            # noqa: BLE001
        return None


# ONE IMPLEMENTATION PER IDEA. The truncation notice, the "did this verdict
# carry a gate outcome at all" test, the NO PLAYER LOG marker and the verdict
# header stamp all already exist in this repo. They are imported, never
# re-typed: a second copy is the site nobody looks at when the first is fixed.
_capsay = _load(REPO / "tools" / "capsay.py", "capsay")
_gates = _load(REPO / "tools" / "gates.py", "ledger_gates")
_vread = _load(REPO / "tools" / "verdict-read.py", "ledger_verdict_read")

REUSED = []
if _capsay:
    cap, NOTHING = _capsay.cap, _capsay.NOTHING_MEASURED
    REUSED.append("tools/capsay.py cap(),NOTHING_MEASURED")
else:
    cap, NOTHING = None, "nothing-measured"
NO_SIM = _gates.NO_SIM if _gates else "NO PLAYER LOG"
if _gates:
    REUSED.append("tools/gates.py gate_verdict(),NO_SIM")
if _vread:
    REUSED.append("tools/verdict-read.py run_stamp_of_text()")

NOT_APPLICABLE = "not yet applicable"


def plain(text):
    """Source text on its way into an artifact this program writes.

    The formatting law (no em dashes) binds what is written here; the sources
    are read-only and several of them (every sim verdict header, for one)
    carry em dashes. Replacing on the way out keeps the law without editing a
    single byte of anybody else's file. Newlines and runs of space collapse
    because these strings land in table cells and one-line captions.
    """
    t = (text or "").replace("\u2014", " - ").replace("\u2013", "-")
    return re.sub(r"\s+", " ", t).strip()


def clip(text, width):
    """A LENGTH CAP THAT SAYS IT BIT. Every display string on this page passes
    through here rather than through a bare slice: `head[:70]` silently turns
    "waiting for his double-click" into "waiting for his double-", which reads
    as a finding rather than as a truncation. Delegates to capsay so there is
    still exactly one implementation of the idea; this only spares the call
    sites a list literal."""
    return cap([text], keep=1, width=width)


def read(path):
    """Read a source, or None when it is not there. Never raises: a missing
    source is a READING, not a crash, and the panel says which path it wanted."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


class Reading:
    """One number on the page, with everything needed to audit it.

    MEASURED carries value, derivation and (when the value can be zero) the
    denominator: what was examined to produce it. UNAVAILABLE carries the
    reason and the paths checked, and renders as the words nothing-measured.
    """

    def __init__(self, label, value, derivation, sources, denominator=None,
                 reason=None, available=True):
        self.label = label
        self.value = value
        self.derivation = derivation
        self.sources = list(sources or [])
        self.denominator = denominator
        self.reason = reason
        self.available = available

    @classmethod
    def measured(cls, label, value, derivation, sources, denominator=None):
        # EVERY ZERO SHIPS ITS DENOMINATOR, enforced here rather than
        # remembered. A zero with nothing beside it cannot be told from a walk
        # that examined nothing, and that is the whole failure this page is at
        # risk of printing at a glance.
        if str(value).strip() in ("0", "0.0", "0%") and not denominator:
            raise ValueError(
                "Reading.measured(%r) is zero with no denominator: say what "
                "was examined, or use Reading.unavailable" % label)
        if not derivation:
            raise ValueError("Reading.measured(%r) has no derivation" % label)
        return cls(label, value, derivation, sources, denominator=denominator)

    @classmethod
    def unavailable(cls, label, reason, sources):
        return cls(label, None, "", sources, reason=reason, available=False)

    @property
    def text(self):
        return str(self.value) if self.available else NOTHING

    @property
    def note(self):
        """The line that travels WITH the number. An appendix nobody scrolls
        to is not where a derivation belongs."""
        if not self.available:
            return "%s: %s" % (NOT_APPLICABLE, self.reason)
        if self.denominator:
            return "%s; of %s" % (self.derivation, self.denominator)
        return self.derivation


# --------------------------------------------------------------- pure parsers
# Everything below takes TEXT and returns data, so the selftest can drive each
# one with a synthetic fixture and no files on disk.

STATUS_LINE = re.compile(r"^status:\s*(.*)$", re.M)
ISO_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")

# THE VOCABULARY IS NAMED, AND ANYTHING OUTSIDE IT IS COUNTED, NEVER FOLDED.
# An allow-list that silently drops what nobody thought of looks exactly like a
# clean result: this one reports its leftovers as "unclassified" so a new
# status word shows up as a number rather than as a wrong bucket.
DONE_WORDS = {"DONE", "COMPLETE", "COMPLETED", "CLOSED"}
BLOCKED_WORDS = {"BLOCKED", "BLOCKER"}
ACTIVE_WORDS = {"STARTED", "STEP", "PARTIAL", "CONTINUED", "RESUMED",
                "ACTIVE", "RUNNING", "IN"}


def status_block(text):
    """The status field's whole value: its own line plus indented continuation
    lines. Task 007's status runs to five lines, and the date is not always on
    the first one."""
    lines = (text or "").splitlines()
    for i, line in enumerate(lines):
        m = STATUS_LINE.match(line)
        if not m:
            continue
        out = [m.group(1)]
        for nxt in lines[i + 1:]:
            if nxt.strip() and (nxt[:1] in (" ", "\t")):
                out.append(nxt.strip())
            else:
                break
        return " ".join(out).strip()
    return None


def classify_task(text, in_done_folder):
    """(state, status_value) for one task file.

    Folder wins for done/: the queue README calls the folder the state
    machine. Otherwise the first word of the status field decides, against the
    named vocabulary above. No status line at all means never started, which
    is QUEUED and is a fact about the file rather than a guess.
    """
    value = status_block(text)
    if in_done_folder:
        return "done", value
    if value is None:
        return "queued", None
    first = re.split(r"[^A-Za-z]+", value.strip())[0].upper() if value.strip() else ""
    if first in DONE_WORDS:
        return "done-misfiled", value
    if first in BLOCKED_WORDS:
        return "blocked", value
    if first in ACTIVE_WORDS:
        return "active", value
    return "unclassified", value


def parse_roadmap(text):
    """Rows of the roadmap-v2 phase table: (phase, milestone, exit gate)."""
    rows = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---") or "---|" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() == "phase":
            continue
        rows.append((cells[0], cells[1], cells[2]))
    return rows


def phase_states(rows, canon_approved):
    """A state per roadmap row, and the rule is printed rather than implied.

    THE ONLY EXIT-GATE CLAUSE THIS PROGRAM CAN EVALUATE is one naming canon.md,
    because canon.md states its own approval in its header. Rows are read in
    table order: rows whose gate is evaluable and met are done, the first row
    that is not done is the current one, and everything after it is pending BY
    SEQUENCE, not because any source says so. That distinction is printed on
    the page, because "pending" derived from an ordering is a weaker claim than
    "done" derived from a file.
    """
    out, current_taken = [], False
    for phase, milestone, gate in rows:
        evaluable = "canon.md" in gate
        if evaluable and canon_approved and not current_taken:
            out.append((phase, milestone, "done",
                        "exit gate names canon.md, which reads STATUS: APPROVED"))
            continue
        if not current_taken:
            current_taken = True
            out.append((phase, milestone, "active", "first row not evidenced done, by sequence"))
        else:
            out.append((phase, milestone, "pending", "after the current row, by sequence"))
    return out


GATE_TOKEN = re.compile(r"^(ok|RED)\s+(\S+)")


def parse_gate_line(line):
    """(pills, merged, unparsed) from a SimDirector ALL GATES line.

    Tokens are separated by ' | ' and read 'ok <name>[detail]'. A detail
    bracket can itself contain a pipe (it has, in kept runs), so a fragment
    whose first word is neither ok nor RED is a CONTINUATION of the token
    before it and is counted as merged. A fragment with nothing to continue is
    counted as unparsed and reported. Neither is dropped in silence: an
    allow-list that discards what nobody thought of reads exactly like a clean
    result.
    """
    body = line.split("ALL GATES:", 1)[-1]
    pills, merged, unparsed = [], 0, 0
    for frag in body.split("|"):
        frag = frag.strip()
        if not frag:
            continue
        m = GATE_TOKEN.match(frag)
        if m:
            name = m.group(2).split("[")[0]
            pills.append((name, "pass" if m.group(1) == "ok" else "fail",
                          plain(frag)))
        elif pills:
            merged += 1
            pills[-1] = (pills[-1][0], pills[-1][1], pills[-1][2] + " | " + plain(frag))
        else:
            unparsed += 1
    return pills, merged, unparsed


def verdict_header(text):
    """(sha, epoch) off line 1 of a verdict. SHA-UNKNOWN is the workflow's own
    literal for a header that carries no sha, and is used here rather than a
    blank, because a blank where a sha belongs reads as a sha (lesson L10)."""
    first = (text or "").splitlines()[0] if text else ""
    stamp = _vread.run_stamp_of_text(first) if _vread else 0
    m = re.search(r"([0-9a-f]{7,40})\s+@\d{6,}", first)
    if not m:
        m = re.search(r"\b([0-9a-f]{7,40})\b", first)
    return (m.group(1) if m else "SHA-UNKNOWN"), stamp


def parse_table_rows(text, want_cols):
    """Rows of any pipe table with at least want_cols cells, header dropped."""
    rows = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < want_cols:
            continue
        rows.append(cells)
    return rows[1:] if rows else []


# ------------------------------------------------------------------ sources
# EVERY PATH THIS PROGRAM READS, IN ONE PLACE, so the derivations block can
# print what it wanted and what it found, and so a moved file shows up as an
# absent source rather than as a silent zero.
SOURCES = {
    "queue": "production/queue",
    "queue_done": "production/queue/done",
    "roadmap": "ledger-v2/respec/roadmap-v2.md",
    "canon": "canon.md",
    "d1_plan": "production/d1-probe/plan.md",
    "d1_ruling": "game-design/decision-D1b-rescope.md",
    "now": "production/NOW.md",
    "d6": "ledger-v2/respec/decision-register/D6-spend.md",
    "usage": "production/budget.md",
    "throughput": "production/throughput.md",
    "tokens": "production/token-ledger.md",
    "decisions": "game-design/decisions-pending.md",
    "learning": "ledger-v2/studio-v2/learning.md",
    "brief": "production/briefs/latest.md",
    "verdict_sim": "game-design/sim-shots/verdict.txt",
    "verdict_ue": "production/d1-probe/ue-verdict.txt",
    "verification": "ledger-v2/studio-v2/verification.md",
    "logs": "production/logs",
}

# Money actually spent has no ledger in this repo. The candidate paths are
# named so the panel can say how many places it looked, rather than printing a
# zero that would read as "nothing has been spent".
SPEND_CANDIDATES = ("production/spend.md", "production/spend-ledger.md",
                    "production/purchases.md", "production/budget-spend.md")


def src(repo, key):
    return repo / SOURCES[key]


# ------------------------------------------------------------------ readers

def read_queue(repo, today):
    """The four counts, each from a stated rule over files actually walked.

    THERE ARE NO queued/ active/ blocked/ FOLDERS. production/queue/ holds flat
    task files plus done/, so the counts come from each file's status field
    against the vocabulary above, and the rule is printed on the page. blocked
    is a real zero (a scan of N files, none carrying a BLOCKED status, and no
    blocked/ directory) rather than an unknown, and the page says exactly that
    so nobody reads it as "a blocking process ran and found nothing".
    """
    qdir, ddir = src(repo, "queue"), src(repo, "queue_done")
    bdir = qdir / "blocked"
    if not qdir.is_dir():
        na = lambda label: Reading.unavailable(                  # noqa: E731
            label, "production/queue/ does not exist", [SOURCES["queue"]])
        return {"cards": [na("queued"), na("active"), na("blocked"),
                          na("done today")], "rule": "", "detail": [],
                "unclassified": [], "misfiled": []}

    walked = []
    for p in sorted(qdir.glob("*.md")):
        if p.name.lower() == "readme.md":
            continue
        walked.append((p, False))
    if ddir.is_dir():
        for p in sorted(ddir.glob("*.md")):
            if p.name.lower() == "readme.md":
                continue
            walked.append((p, True))
    # THE blocked/ FOLDER IS WALKED WHETHER OR NOT IT EXISTS TODAY. It does
    # not exist as this is written, and a walk that only visits the folders
    # that happen to be there is how a file lands in blocked/ and counts as
    # nothing at all: the count would sit at zero with a denominator that
    # never looked. Folder wins here exactly as it does for done/.
    blocked_in_folder = []
    if bdir.is_dir():
        for p in sorted(bdir.glob("*.md")):
            if p.name.lower() == "readme.md":
                continue
            blocked_in_folder.append(p.name)
            walked.append((p, False, "blocked"))

    counts = {"queued": [], "active": [], "blocked": [], "done": [],
              "unclassified": [], "done-misfiled": []}
    dated_today, undated_done = [], []
    detail = []
    for entry in walked:
        p, in_done = entry[0], entry[1]
        forced = entry[2] if len(entry) > 2 else None
        state, value = classify_task(read(p) or "", in_done)
        if forced:
            state, value = forced, value or "in the blocked/ folder"
        bucket = "done" if state == "done" else state
        counts.setdefault(bucket, []).append(p.name)
        if state in ("done", "done-misfiled"):
            m = ISO_DATE.search(value or "")
            if m and m.group(1) == today.isoformat():
                dated_today.append(p.name)
            elif not m:
                undated_done.append(p.name)
        detail.append((p.name, "done/" if in_done else "queue/", state,
                       clip(plain(value or ""), 90)))

    n_done = sum(1 for e in walked if e[1])
    n_blocked_dir = len(blocked_in_folder)
    n_root = len(walked) - n_done - n_blocked_dir
    den = ("%d task file(s) walked (%d in queue/, %d in done/, %d in blocked/), "
           "README excluded" % (len(walked), n_root, n_done, n_blocked_dir))
    rule = ("state per file: done/ folder wins; else the first word of the "
            "status: field against DONE/BLOCKED/STARTED-STEP-PARTIAL "
            "vocabularies; no status: line at all means never started (queued); "
            "any other word is counted as unclassified and named, never folded")

    # THE CAPTION IS DERIVED FROM THE COUNT, NOT CHOSEN WHEN SOMEBODY SAW A
    # ZERO. This sentence used to open "no file carries a BLOCKED status" and
    # was printed unconditionally, so the first real blocked task made the page
    # deny its own number in the same row. A caption that asserts anything
    # about a count has to be built from that count, or it is a comment: true
    # when written and quietly false afterwards, which is this project's oldest
    # fault wearing a dashboard's clothes.
    #
    # Three parts, and only the middle one moves: the RULE (always true), the
    # FINDING (what the scan actually found), and the CAVEAT (always true).
    rule_part = ("blocked means a status: field beginning BLOCKED, or any file "
                 "under production/queue/blocked/")
    if bdir.is_dir():
        folder_part = "that folder holds %d file(s)" % n_blocked_dir
    else:
        folder_part = ("that folder does not exist, so nothing has ever been "
                       "moved there")
    names = counts["blocked"]
    finding_part = ("nothing matched" if not names
                    else "matched by %s" % cap(names, keep=3, sep=", "))
    blocked_reason = "%s; %s; %s; this is a scan result, not a blocking " \
                     "process reporting in" % (rule_part, folder_part, finding_part)
    cards = [
        Reading.measured("queued", len(counts["queued"]),
                         "task files in production/queue/ with no status: line",
                         [SOURCES["queue"]], den),
        Reading.measured("active", len(counts["active"]),
                         "status: first word in STARTED/STEP/PARTIAL/CONTINUED/"
                         "RESUMED/ACTIVE/RUNNING/IN", [SOURCES["queue"]], den),
        Reading.measured("blocked", len(counts["blocked"]),
                         blocked_reason, [SOURCES["queue"]], den),
        Reading.measured("done today", len(dated_today),
                         "files in done/ (or a DONE status) whose status date "
                         "is %s; %s" % (today.isoformat(),
                                        "every done file carries a date"
                                        if not undated_done else
                                        "%d done file(s) carry no date and "
                                        "cannot be attributed to a day: %s"
                                        % (len(undated_done),
                                           cap(undated_done, keep=3, sep=", "))),
                         [SOURCES["queue_done"]],
                         "%d done file(s)" % (len(counts["done"]) +
                                              len(counts["done-misfiled"]))),
    ]
    return {"cards": cards, "rule": rule, "detail": detail,
            "unclassified": counts["unclassified"],
            "misfiled": counts["done-misfiled"]}


def read_phases(repo):
    text = read(src(repo, "roadmap"))
    canon = read(src(repo, "canon")) or ""
    approved = bool(re.search(r"STATUS:\s*APPROVED", canon))
    rows = parse_roadmap(text)
    if not rows:
        return {"rows": [], "current": Reading.unavailable(
            "current phase",
            "the roadmap phase table did not parse (%s)" % (
                "file absent" if text is None else "no rows matched"),
            [SOURCES["roadmap"]]), "rule": ""}
    states = phase_states(rows, approved)
    cur = next((r for r in states if r[2] == "active"), None)
    rule = ("done requires an exit gate this program can evaluate: the only "
            "one is a gate naming canon.md, checked against canon.md's own "
            "STATUS: APPROVED line (found: %s). The first row not evidenced "
            "done is the current phase BY SEQUENCE, and later rows are pending "
            "by sequence, not because a source says so"
            % ("yes" if approved else "no"))
    current = (Reading.measured(
        "current phase", "%s: %s" % (cur[0], clip(plain(cur[1]), 60)),
        "first roadmap row not evidenced done, by table order",
        [SOURCES["roadmap"], SOURCES["canon"]],
        "%d roadmap row(s) read" % len(rows))
        if cur else Reading.unavailable(
            "current phase", "every roadmap row reads as done, which no source "
            "asserts; the phase rule needs a look", [SOURCES["roadmap"]]))
    return {"rows": states, "current": current, "rule": rule}


def read_d1(repo, today):
    """Day N of the D1 timebox, from two sources that must agree.

    Both endpoints come from files. When the plan and the ruling disagree about
    the end date, this refuses rather than picking one: an instrument that
    silently prefers a source is how a wrong date rides for a fortnight.
    """
    plan = read(src(repo, "d1_plan"))
    ruling = read(src(repo, "d1_ruling"))
    if plan is None:
        return Reading.unavailable("D1 probe", "%s does not exist" %
                                   SOURCES["d1_plan"], [SOURCES["d1_plan"]])
    m = re.search(r"kicked off (\d{4}-\d{2}-\d{2}), ends (\d{4}-\d{2}-\d{2})", plan)
    if not m:
        return Reading.unavailable(
            "D1 probe", "no 'kicked off <date>, ends <date>' line in %s" %
            SOURCES["d1_plan"], [SOURCES["d1_plan"]])
    start = datetime.date.fromisoformat(m.group(1))
    end = datetime.date.fromisoformat(m.group(2))
    second = re.search(r"[Tt]imebox[^.\n]*ends (\d{4}-\d{2}-\d{2})", ruling or "")
    if second and second.group(1) != end.isoformat():
        return Reading.unavailable(
            "D1 probe", "the two sources disagree about the end date (%s says "
            "%s, %s says %s); nothing here picks a winner" % (
                SOURCES["d1_plan"], end, SOURCES["d1_ruling"], second.group(1)),
            [SOURCES["d1_plan"], SOURCES["d1_ruling"]])
    total = (end - start).days
    day = (today - start).days + 1
    left = (end - today).days
    if day > total:
        value = "day %d of %d, OVER THE BOX by %d day(s)" % (day, total, -left)
    elif day < 1:
        value = "starts in %d day(s) (%s)" % (1 - day, start.isoformat())
    else:
        value = "day %d of %d, %d day(s) left" % (day, total, left)
    return Reading.measured(
        "D1 probe", value,
        "days counted from %s to %s, both read from the sources, against "
        "today %s; the box length is end minus start" % (
            start.isoformat(), end.isoformat(), today.isoformat()),
        [SOURCES["d1_plan"]] + ([SOURCES["d1_ruling"]] if second else []),
        "2 source(s) agreeing on the end date" if second else
        "1 source (the ruling states no end date this program could match)")


def read_inflight(repo, today):
    """The in-flight list: NOW.md's own section, plus started queue tasks, plus
    the D1 countdown and the night runner. Each row names where it came from."""
    rows = []
    now_text = read(src(repo, "now"))
    if now_text is None:
        rows.append({"name": "NOW.md", "status": NOTHING, "source": SOURCES["now"],
                     "available": False,
                     "note": "%s: %s does not exist" % (NOT_APPLICABLE, SOURCES["now"])})
    else:
        section, take = [], False
        for line in now_text.splitlines():
            if line.startswith("## "):
                take = line.strip().lower().startswith("## in flight")
                continue
            if take and line.strip().startswith("- "):
                section.append(line.strip()[2:])
            elif take and section and line.startswith("  ") and line.strip():
                section[-1] += " " + line.strip()
        verified = ISO_DATE.search(now_text)
        for item in section:
            item = plain(item)
            head, _, rest = item.partition(". ")
            rows.append({"name": clip(head, 70),
                         "status": clip(rest or head, 160),
                         "source": SOURCES["now"], "available": True,
                         "note": "bullet under '## In flight' in %s%s" % (
                             SOURCES["now"],
                             ", verified " + verified.group(1) if verified else "")})
        if not section:
            rows.append({"name": "NOW.md in flight", "status": NOTHING,
                         "source": SOURCES["now"], "available": False,
                         "note": "%s: %s has no bullets under '## In flight'"
                                 % (NOT_APPLICABLE, SOURCES["now"])})

    qdir = src(repo, "queue")
    if qdir.is_dir():
        for p in sorted(qdir.glob("*.md")):
            if p.name.lower() == "readme.md":
                continue
            state, value = classify_task(read(p) or "", False)
            if state == "active":
                rows.append({"name": p.name, "status": clip(plain(value), 160),
                             "source": SOURCES["queue"], "available": True,
                             "note": "status: field says started, not finished"})

    d1 = read_d1(repo, today)
    rows.append({"name": "D1 engine probe (timebox)", "status": d1.text,
                 "source": SOURCES["d1_plan"], "available": d1.available,
                 "note": d1.note})

    logs = src(repo, "logs")
    nights = sorted(logs.glob("night-*")) if logs.is_dir() else []
    if nights:
        rows.append({"name": "night runner", "status": "%d night log dir(s), "
                     "newest %s" % (len(nights), nights[-1].name),
                     "source": SOURCES["logs"], "available": True,
                     "note": "directories matching %s/night-*" % SOURCES["logs"]})
    else:
        rows.append({"name": "night runner", "status": NOTHING,
                     "source": SOURCES["logs"], "available": False,
                     "note": "%s: no %s/night-* directory exists, so the night "
                             "runner has never written a log here" % (
                                 NOT_APPLICABLE, SOURCES["logs"])})
    return rows


def read_budget(repo):
    """The D6 range, the one-off allowance, and what has actually been spent.

    D6 states a RANGE and names no currency. Nothing in this repo records money
    spent, so the tally is not a zero: it is a named absence over the paths
    that were checked. production/budget.md is a DIFFERENT quantity (share of
    the weekly Claude usage limit) and is labelled as such rather than folded
    into the same bar.
    """
    d6 = read(src(repo, "d6"))
    if d6 is None:
        monthly = Reading.unavailable("monthly allowance", "%s does not exist" %
                                      SOURCES["d6"], [SOURCES["d6"]])
        oneoff = Reading.unavailable("one-off allowance", "%s does not exist" %
                                     SOURCES["d6"], [SOURCES["d6"]])
    else:
        mm = re.search(r"(\d+)\s*to\s*(\d+)\s*per month", d6)
        mo = re.search(r"(\d+)\s*to\s*(\d+)\s*one-off", d6)
        # "no currency is named" was a claim about the record that nothing
        # checked, printed beside a number: the same shape as the blocked
        # caption. It is a scan now, so the day a symbol appears in D6 the
        # sentence changes with it.
        cur = re.search(r"[\u00a3\u20ac$]|\b(GBP|USD|EUR|pounds?|euros?|dollars?)\b",
                        d6)
        cur_part = ("the record names a currency (%s)" % cur.group(0) if cur
                    else "no currency symbol or name appears in the record")
        monthly = (Reading.measured(
            "monthly allowance", "%s to %s per month" % (mm.group(1), mm.group(2)),
            "the range as written in D6; " + cur_part,
            [SOURCES["d6"]], "1 approved decision record")
            if mm else Reading.unavailable(
                "monthly allowance", "no '<n> to <n> per month' phrase in %s" %
                SOURCES["d6"], [SOURCES["d6"]]))
        oneoff = (Reading.measured(
            "one-off allowance", "%s to %s in year one" % (mo.group(1), mo.group(2)),
            "the one-off range as written in D6", [SOURCES["d6"]],
            "1 approved decision record")
            if mo else Reading.unavailable(
                "one-off allowance", "no '<n> to <n> one-off' phrase in %s" %
                SOURCES["d6"], [SOURCES["d6"]]))

    found = [c for c in SPEND_CANDIDATES if (repo / c).exists()]
    spend = Reading.unavailable(
        "spend to date", "no spend ledger exists at any of the %d candidate "
        "paths (%s), so no money figure is derivable; a bar drawn at zero here "
        "would claim a measurement nobody has taken" % (
            len(SPEND_CANDIDATES), ", ".join(SPEND_CANDIDATES)),
        list(SPEND_CANDIDATES)) if not found else Reading.measured(
        "spend to date", "see %s" % found[0],
        "a spend ledger appeared; this generator reads its existence only and "
        "does not yet parse it", found, "%d candidate path(s) checked" %
        len(SPEND_CANDIDATES))

    usage_text = read(src(repo, "usage"))
    rows = parse_table_rows(usage_text, 4) if usage_text else []
    if rows:
        last = rows[-1]
        usage = Reading.measured(
            "weekly Claude usage", "%s used at %s" % (last[2], last[0]),
            "LAST ROW of the readings table in %s (the file's newest reading "
            "by position, reported by Jafar, not measured here). This is a "
            "DIFFERENT QUANTITY from the D6 money budget above" % SOURCES["usage"],
            [SOURCES["usage"]], "%d reading row(s) in the table" % len(rows))
    else:
        usage = Reading.unavailable(
            "weekly Claude usage", "no reading rows parsed from %s" %
            SOURCES["usage"], [SOURCES["usage"]])
    return {"monthly": monthly, "oneoff": oneoff, "spend": spend, "usage": usage}


def read_gate_pills(repo):
    """Gate pills from the two committed verdict channels.

    A verdict from a build that did not run still exists and still looks like a
    file: NO PLAYER LOG (Unity) and NO RUN (UE) mean the pills are GRAY, not
    green. Nothing-measured must never render as pass, and that is the single
    most important line in this function.
    """
    out = {"pills": [], "notes": [], "overflow": None}
    sim = read(src(repo, "verdict_sim"))
    if sim is None:
        out["notes"].append("%s: %s does not exist" %
                            (NOT_APPLICABLE, SOURCES["verdict_sim"]))
    else:
        sha, stamp = verdict_header(sim)
        when = (datetime.datetime.fromtimestamp(
                    stamp, datetime.timezone.utc).strftime("%Y-%m-%d %H:%MZ")
                if stamp else "no stamp on line 1")
        if NO_SIM in sim:
            out["notes"].append("sim gates %s: %s says %s (commit %s, %s), so "
                                "the sim did not run and no gate was evaluated"
                                % (NOT_APPLICABLE, SOURCES["verdict_sim"],
                                   NO_SIM, sha, when))
        elif _gates and not _gates.gate_verdict(sim):
            out["notes"].append("sim gates %s: %s carries no gate outcome "
                                "(no pass= and no FAILING GATES line), commit "
                                "%s, %s" % (NOT_APPLICABLE,
                                            SOURCES["verdict_sim"], sha, when))
        else:
            line = next((l for l in sim.splitlines() if "ALL GATES:" in l), None)
            if not line:
                out["notes"].append("sim gates %s: no ALL GATES line in %s "
                                    "(commit %s, %s)" % (NOT_APPLICABLE,
                                                         SOURCES["verdict_sim"],
                                                         sha, when))
            else:
                pills, merged, unparsed = parse_gate_line(line)
                for name, state, detail in pills:
                    out["pills"].append(("sim:" + name, state, detail))
                out["notes"].append(
                    "sim gates: %d pill(s) parsed from the ALL GATES line of %s, "
                    "commit %s, measured %s. %d failing. %d bracketed "
                    "continuation(s) merged, %d fragment(s) unparsed. The "
                    "denominator is this line's own tokens; the done line's "
                    "gatesChecked is a DIFFERENT line and is deliberately not "
                    "quoted beside it" % (
                        len(pills), SOURCES["verdict_sim"], sha, when,
                        sum(1 for p in pills if p[1] == "fail"), merged, unparsed))
    ue = read(src(repo, "verdict_ue"))
    if ue is None:
        out["notes"].append("%s: %s does not exist" %
                            (NOT_APPLICABLE, SOURCES["verdict_ue"]))
    else:
        sha, stamp = verdict_header(ue)
        when = (datetime.datetime.fromtimestamp(
                    stamp, datetime.timezone.utc).strftime("%Y-%m-%d %H:%MZ")
                if stamp else "no stamp on line 1")
        if "NO RUN" in ue:
            out["pills"].append(("ue:probeTest", "na", "NO RUN on commit " + sha))
            out["notes"].append("ue gates %s: %s says NO RUN (commit %s, %s)"
                                % (NOT_APPLICABLE, SOURCES["verdict_ue"], sha, when))
        else:
            m = re.search(r"\bprobeTest=(\w+)", ue)
            if not m:
                out["pills"].append(("ue:probeTest", "na", "no probeTest key"))
                out["notes"].append("ue gates %s: no probeTest key in %s "
                                    "(commit %s)" % (NOT_APPLICABLE,
                                                     SOURCES["verdict_ue"], sha))
            else:
                state = "pass" if m.group(1).upper() == "PASS" else "fail"
                out["pills"].append(("ue:probeTest", state,
                                     "probeTest=%s commit %s" % (m.group(1), sha)))
                out["notes"].append("ue gates: 1 pill from probeTest= in %s, "
                                    "commit %s, measured %s" % (
                                        SOURCES["verdict_ue"], sha, when))
    if len(out["pills"]) > GATE_KEEP:
        rest = ["%s(%s)" % (n, s) for n, s, _ in out["pills"][GATE_KEEP:]]
        out["overflow"] = cap(rest, keep=1)
        out["pills"] = out["pills"][:GATE_KEEP]
    return out


def read_throughput(repo, today):
    """Verified pieces. The ledger's unit is a WEEK, so a rolling 7-day figure
    is not derivable from it and this says so rather than inventing one."""
    text = read(src(repo, "throughput"))
    if text is None:
        return Reading.unavailable("verified pieces", "%s does not exist" %
                                   SOURCES["throughput"], [SOURCES["throughput"]])
    rows = parse_table_rows(text, 4)
    iso = today.isocalendar()
    week = "%d-W%02d" % (iso[0], iso[1])
    mine = [r for r in rows if r[0].strip() == week]
    if not rows:
        return Reading.unavailable(
            "verified pieces", "no table rows parsed from %s" %
            SOURCES["throughput"], [SOURCES["throughput"]])
    if not mine:
        return Reading.unavailable(
            "verified pieces", "the ledger has %d row(s) but none for the "
            "current week %s; its unit is a week, so nothing here covers the "
            "last 7 days" % (len(rows), week), [SOURCES["throughput"]])
    total = 0
    for r in mine:
        m = re.match(r"(\d+)", r[2].strip())
        total += int(m.group(1)) if m else 0
    return Reading.measured(
        "verified pieces", total,
        "SUM over the %d row(s) of the current ISO week %s. The ledger's unit "
        "is a WEEK, not a day, so this is that week and not a rolling 7 days"
        % (len(mine), week), [SOURCES["throughput"]],
        "%d ledger row(s), %d in this week" % (len(rows), len(mine)))


def read_judge(repo):
    """Judge agreement, which nothing has measured yet."""
    checked, hits = [], []
    for key in ("brief", "verification", "throughput"):
        p, text = SOURCES[key], read(src(repo, key))
        checked.append(p)
        if text is None:
            continue
        for m in re.finditer(r"\bagreement[^.\n]{0,40}?(\d{1,3})\s*(?:%|percent)", text):
            hits.append((p, m.group(1)))
    thr = None
    vtext = read(src(repo, "verification")) or ""
    mt = re.search(r"(\d{1,3})\s*percent or better held-out agreement", vtext)
    if mt:
        thr = mt.group(1)
    if not hits:
        return Reading.unavailable(
            "judge agreement",
            "no measured agreement figure in any of the %d source(s) checked "
            "(%s); nothing this program reads records one%s" % (
                len(checked), ", ".join(checked),
                ", and the deploy bar in %s is %s percent held-out agreement"
                % (SOURCES["verification"], thr) if thr else ""),
            checked)
    return Reading.measured(
        "judge agreement", "%s%%" % hits[0][1],
        "first 'agreement <n> percent' phrase found, in %s" % hits[0][0],
        checked, "%d source(s) scanned, %d hit(s)" % (len(checked), len(hits)))


def read_decisions(repo):
    """The decision inbox: one entry per '### ' heading in the pending file."""
    text = read(src(repo, "decisions"))
    if text is None:
        return {"count": Reading.unavailable(
            "open decisions", "%s does not exist" % SOURCES["decisions"],
            [SOURCES["decisions"]]), "items": [], "verified": None}
    items = [plain(l[4:]) for l in text.splitlines() if l.startswith("### ")]
    v = re.search(r"verified (\d{4}-\d{2}-\d{2})", text)
    return {"count": Reading.measured(
        "open decisions", len(items),
        "'### ' headings in %s, which is one per card%s" % (
            SOURCES["decisions"],
            "; the file states it was verified " + v.group(1) if v else
            "; the file states no verified date"),
        [SOURCES["decisions"]], "%d heading line(s) read in 1 file, of which "
        "%d are cards" % (len([l for l in text.splitlines()
                                if l.startswith("#")]), len(items))),
        "items": items, "verified": v.group(1) if v else None}


def read_extras(repo):
    """Sources the layout does not give a panel to, reported in the
    derivations block so a reader can see they were opened: the learning index,
    the token ledger and the latest brief."""
    out = []
    learning = read(src(repo, "learning"))
    if learning is None:
        out.append(Reading.unavailable("terminated lessons", "%s does not exist"
                                       % SOURCES["learning"], [SOURCES["learning"]]))
    else:
        rows = [l for l in learning.splitlines() if re.match(r"^\|\s*L\d+\s*\|", l)]
        out.append(Reading.measured(
            "terminated lessons", len(rows), "rows matching '| L<n> |' in the "
            "index of %s" % SOURCES["learning"], [SOURCES["learning"]],
            "1 index table"))
    brief = read(src(repo, "brief"))
    if brief is None:
        out.append(Reading.unavailable("latest brief", "%s does not exist" %
                                       SOURCES["brief"], [SOURCES["brief"]]))
    else:
        m = ISO_DATE.search(brief)
        out.append(Reading.measured(
            "latest brief", m.group(1) if m else "no date in the file",
            "first ISO date in %s, which is its own header date" % SOURCES["brief"],
            [SOURCES["brief"]], "1 file"))
    tokens = read(src(repo, "tokens"))
    if tokens is None:
        out.append(Reading.unavailable("token ledger rows", "%s does not exist"
                                       % SOURCES["tokens"], [SOURCES["tokens"]]))
    else:
        rows = parse_table_rows(tokens, 4)
        out.append(Reading.measured(
            "token ledger rows", len(rows), "table rows in %s (spend estimates "
            "per week and department; the ledger records estimates, it does not "
            "measure)" % SOURCES["tokens"], [SOURCES["tokens"]],
            "1 ledger table") if rows else Reading.unavailable(
            "token ledger rows", "no table rows parsed from %s" %
            SOURCES["tokens"], [SOURCES["tokens"]]))
    return out


# -------------------------------------------------------------------- model

def build_model(repo, now):
    """One model, read once, rendered twice. The HTML and STATUS.md cannot
    disagree with each other because neither reads a source of its own."""
    today = now.date()
    phases = read_phases(repo)
    decisions = read_decisions(repo)
    return {
        "generated": now,
        "today": today,
        "repo": repo,
        "phases": phases,
        "decisions": decisions,
        "queue": read_queue(repo, today),
        "inflight": read_inflight(repo, today),
        "budget": read_budget(repo),
        "gates": read_gate_pills(repo),
        "throughput": read_throughput(repo, today),
        "judge": read_judge(repo),
        "extras": read_extras(repo),
        "sources": [(k, v, (repo / v).exists()) for k, v in sorted(SOURCES.items())],
        "reused": list(REUSED),
    }


def all_readings(model):
    out = [model["phases"]["current"], model["decisions"]["count"],
           model["throughput"], model["judge"]]
    out += model["queue"]["cards"]
    out += [model["budget"][k] for k in ("monthly", "oneoff", "spend", "usage")]
    out += model["extras"]
    return out


def inflight_shown(model):
    """The kept rows and the truncation clause, which comes from capsay so
    there is no second implementation of '(+N more)' in this repo."""
    rows = model["inflight"]
    if len(rows) <= INFLIGHT_KEEP:
        return rows, None
    dropped = ["%s: %s" % (r["name"], r["status"]) for r in rows[INFLIGHT_KEEP:]]
    return rows[:INFLIGHT_KEEP], cap(dropped, keep=1, width=70)


# ----------------------------------------------------------------- rendering

CSS = """
:root { color-scheme: light dark;
  --bg:#fbfbfa; --fg:#1b1b1a; --dim:#5d5d58; --line:#dedcd6; --card:#ffffff;
  --amber:#8a5a00; --amberbg:#fff5e0; --pass:#1d6b3a; --passbg:#e4f3e9;
  --fail:#9a2020; --failbg:#fbe6e6; --na:#5d5d58; --nabg:#eeedea; }
@media (prefers-color-scheme: dark) { :root {
  --bg:#15161a; --fg:#e9e8e4; --dim:#a3a19a; --line:#2e3038; --card:#1d1f25;
  --amber:#f0c060; --amberbg:#2f2612; --pass:#7fd4a0; --passbg:#16301f;
  --fail:#ff9a9a; --failbg:#331717; --na:#a3a19a; --nabg:#24262c; } }
* { box-sizing:border-box; }
body { margin:0; padding:14px; background:var(--bg); color:var(--fg);
  font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  max-width:760px; margin-inline:auto; }
h1 { font-size:19px; margin:0 0 2px; }
h2 { font-size:13px; text-transform:uppercase; letter-spacing:.06em;
  color:var(--dim); margin:22px 0 8px; font-weight:600; }
.sub { color:var(--dim); font-size:12.5px; margin:0 0 2px; }
.stale { color:var(--fail); font-weight:600; }
.banner { border:1px solid var(--amber); background:var(--amberbg);
  color:var(--amber); border-radius:6px; padding:10px 12px; margin:12px 0; }
.banner.calm { border-color:var(--line); background:var(--card); color:var(--dim); }
.banner ol { margin:6px 0 0; padding-left:20px; }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(158px,1fr)); gap:8px; }
.card { border:1px solid var(--line); background:var(--card); border-radius:6px;
  padding:10px 11px; }
.num { font-size:26px; font-weight:600; line-height:1.1; }
.num.none { font-size:15px; color:var(--dim); font-weight:500; }
.lab { font-size:12.5px; color:var(--dim); text-transform:uppercase;
  letter-spacing:.05em; margin-top:2px; }
.why { font-size:11.5px; color:var(--dim); margin-top:6px; }
.pills { display:flex; flex-wrap:wrap; gap:5px; }
.pill { font-size:12px; padding:3px 8px; border-radius:11px; border:1px solid var(--line);
  background:var(--nabg); color:var(--na); }
.pill.pass,.pill.done { background:var(--passbg); color:var(--pass); border-color:var(--pass); }
.pill.fail { background:var(--failbg); color:var(--fail); border-color:var(--fail); }
.pill.active { background:var(--amberbg); color:var(--amber); border-color:var(--amber); }
.row { border:1px solid var(--line); background:var(--card); border-radius:6px;
  padding:9px 11px; margin-bottom:6px; }
.row .nm { font-weight:600; font-size:13.5px; }
.row .st { font-size:13px; }
.row.na .st { color:var(--dim); }
.bar { height:12px; border-radius:6px; border:1px solid var(--line);
  background:var(--nabg); overflow:hidden; margin:8px 0 4px; }
.bar > div { height:100%; background:var(--pass); }
.bar.none { background:repeating-linear-gradient(45deg,var(--nabg),var(--nabg)6px,var(--card)6px,var(--card)12px); }
table { border-collapse:collapse; width:100%; font-size:12px; }
td,th { border-bottom:1px solid var(--line); text-align:left; padding:4px 6px;
  vertical-align:top; }
th { color:var(--dim); font-weight:600; }
code { font-size:11.5px; }
footer { margin-top:26px; padding-top:10px; border-top:1px solid var(--line);
  color:var(--dim); font-size:12px; }
"""

AGE_JS = """
(function(){var e=document.getElementById("age");if(!e)return;
var t=new Date(e.getAttribute("data-gen"));
var m=Math.round((Date.now()-t.getTime())/60000);
e.textContent=(m<1?"just now":m+" min ago");
if(m>20){e.className="stale";
e.textContent=m+" min ago, older than the 15 minute regeneration interval: "+
"treat every number below as that old, the regenerator may not be running";}})();
"""


def esc(s):
    return html.escape(str(s), quote=True)


def card_html(r):
    cls = "num" if r.available else "num none"
    return ('<div class="card"><div class="%s">%s</div>'
            '<div class="lab">%s</div><div class="why">%s</div></div>'
            % (cls, esc(r.text), esc(r.label), esc(r.note)))


def render_html(model):
    g = model["generated"]
    q, b, gates = model["queue"], model["budget"], model["gates"]
    dec = model["decisions"]
    out = []
    a = out.append
    a("<!doctype html>")
    a('<html lang="en"><head><meta charset="utf-8">')
    a('<meta name="viewport" content="width=device-width,initial-scale=1">')
    a('<meta http-equiv="refresh" content="%d">' % REFRESH_SECONDS)
    a("<title>LEDGER status</title>")
    a("<style>%s</style></head><body>" % CSS)

    # 1. header
    a("<h1>LEDGER studio status</h1>")
    a('<p class="sub">Current phase: %s</p>'
      % esc(model["phases"]["current"].text))
    a('<p class="sub">%s. Regenerated %s, <span id="age" data-gen="%s">'
      '</span><noscript>(page age needs script; the stamp beside it is when '
      'this file was written)</noscript></p>' % (
          esc(model["phases"]["current"].note),
          esc(g.strftime("%Y-%m-%d %H:%M")), esc(g.isoformat())))

    # 2. decision inbox
    n = dec["count"]
    if not n.available:
        a('<div class="banner"><b>Decision inbox: %s</b><div class="why">%s</div>'
          "</div>" % (esc(NOTHING), esc(n.note)))
    elif int(n.value) == 0:
        a('<div class="banner calm"><b>Decision inbox: nothing waiting on '
          "Jafar.</b>"
          '<div class="why">%s</div></div>' % esc(n.note))
    else:
        items = "".join("<li>%s</li>" % esc(i) for i in dec["items"])
        a('<div class="banner"><b>Decision inbox: %s waiting on Jafar</b><ol>%s</ol>'
          '<div class="why">%s</div></div>' % (esc(n.value), items, esc(n.note)))

    # 3. phase pill strip
    a("<h2>Phases</h2>")
    if not model["phases"]["rows"]:
        a('<p class="why">%s</p>' % esc(model["phases"]["current"].note))
    else:
        a('<div class="pills">')
        for phase, milestone, state, why in model["phases"]["rows"]:
            a('<span class="pill %s" title="%s">%s %s</span>'
              % (state, esc(clip(plain(milestone), 110) + " | " + why),
                 esc(phase), esc(state)))
        a("</div>")
        a('<p class="why">%s</p>' % esc(model["phases"]["rule"]))

    # 4. four metric cards
    a("<h2>Queue</h2>")
    a('<div class="cards">%s</div>' % "".join(card_html(c) for c in q["cards"]))
    if q["rule"]:
        a('<p class="why">%s.</p>' % esc(q["rule"]))
    if q["unclassified"]:
        a('<p class="why">unclassified status word(s), counted in no card: %s</p>'
          % esc(cap(q["unclassified"], keep=4)))
    if q["misfiled"]:
        a('<p class="why">carrying a DONE status but still in queue/: %s</p>'
          % esc(cap(q["misfiled"], keep=4)))

    # 5. in flight
    a("<h2>In flight</h2>")
    rows, clause = inflight_shown(model)
    for r in rows:
        a('<div class="row%s"><div class="nm">%s</div><div class="st">%s</div>'
          '<div class="why">%s</div></div>' % (
              "" if r["available"] else " na", esc(r["name"]),
              esc(r["status"]), esc(r["note"])))
    if clause:
        a('<p class="why">(+ not shown) %s</p>' % esc(clause))

    # 6. budget
    a("<h2>Budget</h2>")
    a('<div class="cards">%s%s</div>' % (card_html(b["monthly"]),
                                         card_html(b["oneoff"])))
    if b["spend"].available:
        a('<div class="bar"><div style="width:0%%"></div></div>')
    else:
        a('<div class="bar none"></div>')
    a('<p class="why"><b>Spend to date: %s.</b> %s</p>'
      % (esc(b["spend"].text), esc(b["spend"].note)))
    a('<p class="why">%s: %s. %s</p>' % (esc(b["usage"].label),
                                         esc(b["usage"].text), esc(b["usage"].note)))

    # 7. gate pill strip
    # THE PROVENANCE GOES ABOVE THE PILLS, NOT UNDER THEM. A wall of green is
    # the most eye-catching thing on this page and it is a photograph of one
    # commit at one instant: if the sim stops running, the pills stay green
    # for as long as that verdict sits in the tree. Putting the commit and the
    # measured-at line first makes the glance read "as of X" before it reads
    # "all fine", which is the only version of this strip that cannot mislead.
    a("<h2>Gates</h2>")
    for note in gates["notes"]:
        a('<p class="why">%s</p>' % esc(note))
    if gates["pills"]:
        a('<div class="pills">')
        for name, state, detail in gates["pills"]:
            a('<span class="pill %s" title="%s">%s</span>'
              % (state, esc(clip(detail, 220)), esc(name)))
        a("</div>")
    else:
        a('<p class="why">%s</p>' % esc(NOTHING))
    if gates["overflow"]:
        a('<p class="why">(+ not shown) %s</p>' % esc(gates["overflow"]))

    # 8. two metric cards
    a("<h2>Verification</h2>")
    a('<div class="cards">%s%s</div>' % (card_html(model["throughput"]),
                                         card_html(model["judge"])))

    # 9. derivations
    a("<h2>Where every number came from</h2>")
    a("<table><tr><th>reading</th><th>value</th><th>derivation</th></tr>")
    for r in all_readings(model):
        a("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
          % (esc(r.label), esc(r.text), esc(r.note)))
    a("</table>")
    a('<p class="why">Sources opened under %s: %s</p>' % (esc(model["repo"]),
      esc(", ".join(
        "%s%s" % (p, "" if ok else " (ABSENT)") for _, p, ok in model["sources"]))))
    a('<p class="why">Reused rather than reimplemented: %s</p>'
      % esc(", ".join(model["reused"]) or NOTHING))
    a("<footer>%s</footer>" % esc(FOOTER_LINE))
    a("<script>%s</script>" % AGE_JS)
    a("</body></html>")
    return "\n".join(out) + "\n"


def render_status(model):
    g, q, b = model["generated"], model["queue"], model["budget"]
    dec, gates = model["decisions"], model["gates"]
    L = []
    a = L.append
    a("# LEDGER studio status")
    a("")
    a("STATUS: DERIVED. Generated by tools/dashboard/build-dashboard.py at %s."
      % g.strftime("%Y-%m-%d %H:%M"))
    a("Do not hand-edit: the next regeneration overwrites it. If a number here")
    a("is wrong, the source file or the generator is wrong.")
    a("")
    a("Current phase: %s" % model["phases"]["current"].text)
    a("(%s)" % model["phases"]["current"].note)
    a("")
    n = dec["count"]
    a("## Decision inbox")
    a("")
    if not n.available:
        a("- %s. %s" % (NOTHING, n.note))
    elif int(n.value) == 0:
        a("- Nothing waiting on Jafar. %s" % n.note)
    else:
        a("**%s waiting on Jafar.**" % n.value)
        for i in dec["items"]:
            a("1. %s" % i)
        a("")
        a("(%s)" % n.note)
    a("")
    a("## Phases")
    a("")
    if not model["phases"]["rows"]:
        a("- %s. %s" % (NOTHING, model["phases"]["current"].note))
    else:
        a(" | ".join("%s %s" % (p, s) for p, _, s, _ in model["phases"]["rows"]))
        a("")
        a("(%s)" % model["phases"]["rule"])
    a("")
    a("## Queue")
    a("")
    a("| count | value | derivation |")
    a("|---|---|---|")
    for c in q["cards"]:
        a("| %s | %s | %s |" % (c.label, c.text, c.note))
    if q["rule"]:
        a("")
        a("Rule: %s." % q["rule"])
    if q["unclassified"]:
        a("Unclassified status word(s), counted in no card: %s"
          % cap(q["unclassified"], keep=4))
    if q["misfiled"]:
        a("Carrying a DONE status but still in queue/: %s"
          % cap(q["misfiled"], keep=4))
    a("")
    a("## In flight")
    a("")
    rows, clause = inflight_shown(model)
    for r in rows:
        a("- **%s**: %s" % (r["name"], r["status"]))
        a("  (%s)" % r["note"])
    if clause:
        a("- (+ not shown) %s" % clause)
    a("")
    a("## Budget")
    a("")
    a("- D6 monthly allowance: %s. %s" % (b["monthly"].text, b["monthly"].note))
    a("- D6 one-off allowance: %s. %s" % (b["oneoff"].text, b["oneoff"].note))
    a("- Spend to date: %s. %s" % (b["spend"].text, b["spend"].note))
    a("- %s: %s. %s" % (b["usage"].label, b["usage"].text, b["usage"].note))
    a("")
    a("## Gates")
    a("")
    for note in gates["notes"]:
        a("- %s" % note)
        a("")
    if gates["pills"]:
        a(" ".join("%s=%s" % (n2, s) for n2, s, _ in gates["pills"]))
    else:
        a(NOTHING)
    if gates["overflow"]:
        a("")
        a("(+ not shown) %s" % gates["overflow"])
    a("")
    a("## Verification")
    a("")
    a("- %s: %s. %s" % (model["throughput"].label, model["throughput"].text,
                        model["throughput"].note))
    a("- %s: %s. %s" % (model["judge"].label, model["judge"].text,
                        model["judge"].note))
    a("")
    a("## Where every number came from")
    a("")
    a("| reading | value | derivation |")
    a("|---|---|---|")
    for r in all_readings(model):
        a("| %s | %s | %s |" % (r.label, r.text, r.note))
    a("")
    a("Sources opened under %s: %s" % (model["repo"], ", ".join(
        "%s%s" % (p, "" if ok else " (ABSENT)") for _, p, ok in model["sources"])))
    a("")
    a("Reused rather than reimplemented: %s" % (", ".join(model["reused"]) or NOTHING))
    a("")
    a(FOOTER_LINE)
    a("")
    return "\n".join(L)


# ------------------------------------------------------------- the only write

def write_artifact(path, text):
    """THE ONLY FUNCTION IN THIS PROGRAM THAT WRITES ANYTHING.

    It refuses any name other than the two artifacts, so "this generator is
    read-only apart from its two outputs" is enforced here and provable by the
    selftest's AST walk rather than asserted in a comment. A dashboard that
    repaired, normalised or wrote back to a source would be a second source of
    truth, which is the one thing it must never become.
    """
    if path.name not in ARTIFACTS:
        raise ValueError("write_artifact refuses %r: this program writes only "
                         "%s" % (path.name, " and ".join(ARTIFACTS)))
    path.write_text(text, encoding="utf-8")
    return len(text)


# ------------------------------------------------------------------ selftest

# Names that mutate a filesystem. `replace` is deliberately NOT here: at the
# AST level str.replace and Path.replace are the same word, and plain() uses
# the string one. The run-time guard covers what this cannot see, because
# write_artifact refuses any name but the two artifacts and the scope test
# below counts what a whole generation actually created on disk.
WRITE_NAMES = {"write_text", "write_bytes", "mkdir", "makedirs", "unlink",
               "rmdir", "remove", "rename", "touch", "symlink_to", "rmtree",
               "mkdtemp", "mkstemp", "system", "chmod", "open"}
WRITE_ALLOWED_IN = {"write_artifact", "selftest"}

SHIPPED = ("tools/dashboard/build-dashboard.py", "open-dashboard.bat",
           "tools/dashboard/README.md")

SECTIONS = ["LEDGER studio status", "Decision inbox", "Phases", "Queue",
            "In flight", "Budget", "Gates", "Verification",
            "Where every number came from"]


def _write_calls(source):
    """(offending, walked): every filesystem-write call site in this file and
    the function it sits in."""
    tree = ast.parse(source)
    offending, walked = [], 0

    def visit(node, chain):
        nonlocal walked
        for child in ast.iter_child_nodes(node):
            nxt = (chain + [child.name] if isinstance(child, ast.FunctionDef)
                   else chain)
            if isinstance(child, ast.Call):
                f = child.func
                name = (f.attr if isinstance(f, ast.Attribute) else
                        f.id if isinstance(f, ast.Name) else "")
                if name in WRITE_NAMES:
                    walked += 1
                    # ANY enclosing function may be the door, not just the
                    # innermost one: the selftest builds its fixtures in nested
                    # helpers, and flagging those would push the writes back up
                    # into one long function to satisfy the check, which is the
                    # tool shaping the code rather than measuring it.
                    if not any(a in WRITE_ALLOWED_IN for a in chain):
                        offending.append("%s() in %s at line %d"
                                         % (name, ".".join(chain) or "<module>",
                                            child.lineno))
            visit(child, nxt)

    visit(tree, [])
    return offending, walked


PHONE_WIDTH = 390          # the viewport page_check.py drives, kept in step


def page_faults(page):
    """OPEN THE ARTIFACT, as far as this container can open it.

    THERE IS NO BROWSER HERE. tools/voice-fetch/page_check.py drives a real
    Chromium at 390x844; playwright is not installed in this container and
    neither is chromium, so the first open on Jafar's machine is this page's
    real accepting case and that is said out loud in the selftest output.

    What can be checked without one is the shape of the faults the listening
    page actually shipped with: no viewport tag, a fixed bar sitting on top of
    the controls, a page that scrolled sideways, and a stray newline inside a
    script that killed every control on the page. Those are structural and a
    parser can see them. Returns a list of findings, so it can be run against a
    deliberately broken page as well as against the real one.
    """
    import html.parser as _hp
    found = []

    class Balance(_hp.HTMLParser):
        VOID = {"meta", "br", "img", "link", "hr", "input", "source"}

        def __init__(self):
            super().__init__()
            self.stack = []
            self.bad = []

        def handle_starttag(self, tag, attrs):
            if tag not in self.VOID:
                self.stack.append(tag)

        def handle_endtag(self, tag):
            if self.stack and self.stack[-1] == tag:
                self.stack.pop()
            elif tag in self.stack:
                self.bad.append("%s closed out of order" % tag)
                while self.stack and self.stack.pop() != tag:
                    pass
            else:
                self.bad.append("</%s> with nothing open" % tag)

    b = Balance()
    b.feed(page)
    found += b.bad
    if b.stack:
        found.append("never closed: " + cap(b.stack, keep=3, sep=","))
    if "width=device-width" not in page:
        found.append("no viewport tag: the phone renders it at desktop width")
    if "http-equiv=\"refresh\"" not in page:
        found.append("no meta refresh")
    if "position:fixed" in page.replace(" ", ""):
        found.append("a fixed element can sit on top of the content under it")
    # `max-width` is the opposite of the fault: it CONSTRAINS the column and
    # cannot scroll a phone. Only a bare `width:` pins a box wider than the
    # screen, so the lookbehind is load-bearing rather than tidy. The first
    # version of this line flagged this page's own max-width:760px.
    for m in re.finditer(r"(?<![-a-z])width:\s*(\d+)px", page):
        if int(m.group(1)) > PHONE_WIDTH:
            found.append("a %spx fixed width scrolls a %dpx phone sideways"
                         % (m.group(1), PHONE_WIDTH))
    body = page.split("<script>", 1)[-1].split("</script>", 1)[0] if "<script>" in page else ""
    if "\\n" in body:
        found.append("a literal backslash-n inside the script: the listening "
                     "page shipped one and it killed every control")
    if "src=" in body or "http://" in body or "https://" in body:
        found.append("the script reaches outside the file")
    return found


def selftest(repo=None):                                         # noqa: C901
    """Both outcomes, ACCEPTING CASE FIRST.

    The live repository is the accepting fixture: every panel that can be
    derived here must derive, because a dashboard that refuses today's repo is
    the validator nothing survives. The rejecting fixtures are synthetic and
    live nowhere else (an empty directory, a verdict that says the sim did not
    run, two sources disagreeing about a date), so doing the work this page
    describes can never break the test.
    """
    repo = pathlib.Path(repo or REPO)
    passed, failed = 0, []

    def ok(name, cond, got=""):
        nonlocal passed
        if cond:
            passed += 1
            print("  ok   %s" % name)
        else:
            failed.append(name)
            print("  FAIL %s%s" % (name, " - " + str(got)[:200] if got else ""))

    print("dashboard selftest - ACCEPTING CASE FIRST (the live repo)\n")
    print("A. the live repository, which every panel must survive")
    ok("capsay imported, so truncations announce themselves", cap is not None)
    ok("the repo root looks like this repo", (repo / "CLAUDE.md").exists(),
       str(repo))
    now = datetime.datetime(2026, 9, 1, 12, 0, 0)
    live = build_model(repo, datetime.datetime.now())

    q = live["queue"]
    walked = len(q["detail"])
    named = sum(int(c.value) for c in q["cards"][:3])
    done_all = sum(1 for d in q["detail"] if d[2].startswith("done"))
    unclassified = len(q["unclassified"])
    ok("queue counts add up to the files walked (%d + %d done + %d unclassified "
       "= %d)" % (named, done_all, unclassified, walked),
       named + done_all + unclassified == walked,
       [d[2] for d in q["detail"]])
    ok("every queue card carries a denominator",
       all(c.denominator for c in q["cards"]),
       [c.label for c in q["cards"] if not c.denominator])
    ok("the queue derivation rule is printed", bool(q["rule"]))

    ph = live["phases"]
    ok("the roadmap phase table parses (%d rows)" % len(ph["rows"]),
       len(ph["rows"]) >= 2)
    ok("exactly one phase reads as active",
       sum(1 for r in ph["rows"] if r[2] == "active") == 1,
       [r[2] for r in ph["rows"]])
    ok("phase R is evidenced done from canon.md, not from sequence",
       any(r[0] == "R" and r[2] == "done" for r in ph["rows"]),
       [(r[0], r[2]) for r in ph["rows"][:2]])

    d1 = read_d1(repo, datetime.date(2026, 9, 1))
    ok("D1 countdown derives from the real dates: %s" % d1.text,
       d1.available and "day 2 of 14" in d1.text, d1.text + " " + d1.note)

    g = live["gates"]
    ok("gate pills parse from the committed verdict (%d)" % len(g["pills"]),
       len(g["pills"]) >= 2, g["notes"])
    ok("the gate strip states its own denominator and commit",
       any("pill(s) parsed" in n for n in g["notes"]), g["notes"])

    ok("verified pieces derives for the current week",
       live["throughput"].available, live["throughput"].note)
    ok("open decisions derives", live["decisions"]["count"].available,
       live["decisions"]["count"].note)
    ok("judge agreement reads NOT APPLICABLE on this repo, not 0",
       not live["judge"].available and NOTHING in live["judge"].text,
       live["judge"].text)
    ok("spend to date reads NOT APPLICABLE on this repo, not 0",
       not live["budget"]["spend"].available, live["budget"]["spend"].text)
    ok("night runner reads NOT APPLICABLE on this repo, not 0",
       any(r["name"] == "night runner" and not r["available"]
           for r in live["inflight"]),
       [r["name"] for r in live["inflight"]])

    zeros = [r.label for r in all_readings(live)
             if r.available and str(r.value).strip() == "0" and not r.denominator]
    ok("no zero anywhere on the page is missing its denominator", not zeros, zeros)
    unavail = [r for r in all_readings(live) if not r.available]
    ok("every unavailable reading gives a reason (%d of %d readings)"
       % (len(unavail), len(all_readings(live))),
       all(r.reason for r in unavail), [r.label for r in unavail if not r.reason])

    page, status = render_html(live), render_status(live)
    pos = [page.find(s) for s in SECTIONS]
    ok("the page carries all %d sections in the specified order" % len(SECTIONS),
       all(p >= 0 for p in pos) and pos == sorted(pos), pos)
    spos = [status.find(s) for s in SECTIONS]
    ok("STATUS.md is the same sections in the same order",
       all(p >= 0 for p in spos) and spos == sorted(spos), spos)
    ok("the page auto-refreshes every %d seconds" % REFRESH_SECONDS,
       'http-equiv="refresh" content="%d"' % REFRESH_SECONDS in page)
    ok("the page is mobile-first (viewport tag present)",
       "width=device-width" in page)
    ok("both artifacts end with the footer line", FOOTER_LINE in page
       and FOOTER_LINE in status)
    dash = "\u2014"
    ok("neither artifact carries an em dash (source text is passed through "
       "plain())", dash not in page and dash not in status)
    ok("the page says nothing-measured where a source is missing",
       NOTHING in page and NOTHING in status)
    faults = page_faults(page)
    ok("the page survives the structural checks (balanced tags, viewport, "
       "refresh, nothing fixed over the content, no sideways scroll, a script "
       "that reaches nowhere)", not faults, faults)
    ok("a display string too long to fit says it was cut",
       clip("y" * 200, 70).endswith("...") and len(clip("y" * 200, 70)) == 73,
       clip("y" * 200, 70)[-10:])
    ok("and one that fits is left alone", clip("short", 70) == "short")

    absent = [p for p in SHIPPED if not (repo / p).exists()]
    ok("every file this tool ships is present (%d)" % len(SHIPPED), not absent,
       absent)
    dashed = [p for p in SHIPPED if (repo / p).exists()
              and dash in (repo / p).read_text(encoding="utf-8", errors="replace")]
    ok("no em dash in the %d shipped file(s) READ (%d absent, not read)"
       % (len(SHIPPED) - len(absent), len(absent)), not dashed, dashed)

    print("\nB. the rejecting cases, which are synthetic and exist nowhere else")
    empty = pathlib.Path(tempfile.mkdtemp(prefix="dash-empty-"))
    blank = build_model(empty, now)
    readings = all_readings(blank)
    still = [r.label for r in readings if r.available]
    ok("an empty tree makes EVERY reading unavailable (%d readings)"
       % len(readings), not still, still)
    bstatus = render_status(blank)
    ok("and STATUS.md then contains no number-shaped zero",
       not re.search(r"\|\s*0\s*\|", bstatus),
       [l for l in bstatus.splitlines() if re.search(r"\|\s*0\s*\|", l)][:3])
    ok("and every panel says why it is not applicable",
       bstatus.count(NOT_APPLICABLE) >= 8, bstatus.count(NOT_APPLICABLE))
    ok("and the gate strip is empty rather than green",
       not blank["gates"]["pills"], blank["gates"]["pills"])

    out = pathlib.Path(tempfile.mkdtemp(prefix="dash-out-"))
    write_artifact(out / HTML_NAME, render_html(blank))
    write_artifact(out / STATUS_NAME, bstatus)
    made = sorted(p.name for p in out.iterdir())
    ok("a whole generation creates exactly the two artifacts", made ==
       sorted(ARTIFACTS), made)
    ok("and writes nothing at all into the tree it read",
       not list(empty.iterdir()), [p.name for p in empty.iterdir()])
    try:
        write_artifact(out / "notes.txt", "x")
        ok("write_artifact refuses a third filename", False, "it accepted one")
    except ValueError as e:
        ok("write_artifact refuses a third filename", "refuses" in str(e))

    offending, wcalls = _write_calls(pathlib.Path(__file__).read_text(
        encoding="utf-8"))
    ok("no write path outside write_artifact and the selftest (%d write call "
       "site(s) walked)" % wcalls, not offending, offending)
    # THE WRITE GUARD'S OWN TWO OUTCOMES. It was widened to allow a helper
    # nested inside an allowed function, and a guard that has just been
    # loosened is exactly the one to re-run against the case it must still
    # refuse.
    stray, _ = _write_calls("def render():\n    open('x', 'w')\n")
    ok("the write guard still REFUSES a write outside the door",
       len(stray) == 1 and "render" in stray[0], stray)
    nested, _ = _write_calls("def selftest():\n    def fix():\n"
                             "        open('x', 'w')\n")
    ok("and ACCEPTS one nested inside a function that may write", not nested,
       nested)

    try:
        Reading.measured("bogus", 0, "derived from nothing", ["x"])
        ok("a zero with no denominator is refused at construction", False,
           "it was accepted")
    except ValueError:
        ok("a zero with no denominator is refused at construction", True)

    ok("a status word outside the vocabulary is UNCLASSIFIED, never folded",
       classify_task("status: MARINATING since Tuesday", False)[0] == "unclassified",
       classify_task("status: MARINATING since Tuesday", False))
    ok("a BLOCKED status is blocked",
       classify_task("status: BLOCKED on Jafar", False)[0] == "blocked")
    ok("no status line at all is queued", classify_task("line: x\n", False)[0]
       == "queued")
    ok("the done/ folder wins over the status field",
       classify_task("status: STARTED", True)[0] == "done")
    ok("a multi-line status field is read whole",
       "2026-09-01" in (status_block("status: STEP 1 DONE (run 14)\n"
                                     "        landed 2026-09-01 and stopped") or ""))

    # THE CASE THAT WOULD HAVE CAUGHT THE CAPTION FAULT. The blocked caption
    # opened with "no file carries a BLOCKED status" and was printed whatever
    # the count was, so the first genuinely blocked task made the row deny its
    # own number. Both directions are asserted here, because a caption that
    # only ever says "one is blocked" would be the same fault mirrored.
    def queue_fixture(tag, files, blocked_folder=()):
        d = pathlib.Path(tempfile.mkdtemp(prefix="dash-q-" + tag + "-"))
        (d / "production" / "queue" / "done").mkdir(parents=True)
        for name, body in files:
            (d / "production" / "queue" / name).write_text(body, encoding="utf-8")
        if blocked_folder:
            (d / "production" / "queue" / "blocked").mkdir(parents=True)
            for name, body in blocked_folder:
                (d / "production" / "queue" / "blocked" / name).write_text(
                    body, encoding="utf-8")
        return read_queue(d, datetime.date(2026, 9, 1))

    none_blocked = queue_fixture("zero", [("002-a.md", "line: x\n")])
    zero_card = none_blocked["cards"][2]
    ok("with nothing blocked the count is 0 and the caption says so",
       str(zero_card.value) == "0" and "nothing matched" in zero_card.derivation,
       zero_card.derivation)
    ok("and it still carries the rule, the folder finding and the caveat",
       all(x in zero_card.derivation for x in
           ("blocked means", "does not exist", "not a blocking process")),
       zero_card.derivation)
    ok("and it still carries its denominator",
       "task file(s) walked" in (zero_card.denominator or ""),
       zero_card.denominator)

    one_blocked = queue_fixture("one", [
        ("002-a.md", "line: x\n"),
        ("012-trellis.md", "line: content\nstatus: BLOCKED 2026-09-01 no CUDA "
                           "on this machine\n")])
    one_card = one_blocked["cards"][2]
    ok("with one blocked the count is 1", str(one_card.value) == "1",
       one_card.derivation)
    ok("AND THE CAPTION DOES NOT DENY IT: no absence claim beside a count of 1",
       "nothing matched" not in one_card.derivation
       and "no file carries" not in one_card.derivation, one_card.derivation)
    ok("and the caption names what matched",
       "012-trellis.md" in one_card.derivation, one_card.derivation)

    infolder = queue_fixture("folder", [("002-a.md", "line: x\n")],
                             blocked_folder=[("099-stuck.md", "line: y\n")])
    folder_card = infolder["cards"][2]
    ok("a file in production/queue/blocked/ is WALKED, not invisible",
       str(folder_card.value) == "1"
       and "1 in blocked/" in (folder_card.denominator or ""),
       (folder_card.value, folder_card.denominator))
    ok("and the caption reports the folder it found rather than one it assumed",
       "that folder holds 1 file(s)" in folder_card.derivation,
       folder_card.derivation)

    # THE GENERAL SHAPE, not just this row: no card anywhere may pair a
    # non-zero count with the vocabulary of absence.
    # ONLY PHRASES THAT DENY THE COUNT ITSELF. The first version of this list
    # also held "carry no date", and it fired on a TRUE clause: "4 done today,
    # 1 done file carries no date" describes a different subset and is not a
    # contradiction. A sweep that flags true sentences teaches people to delete
    # them, which is the opposite of what this is for.
    absence = ("nothing matched", "no file carries")
    contradictions = []
    for fixture in (none_blocked, one_blocked, infolder, live["queue"]):
        for c in fixture["cards"]:
            if str(c.value).strip() not in ("0", "") and any(
                    w in c.derivation for w in absence):
                contradictions.append("%s=%s says %r" % (c.label, c.value,
                                                         c.derivation[:70]))
    ok("no card in 4 models pairs a non-zero count with a claim of absence",
       not contradictions, contradictions)

    pills, merged, unparsed = parse_gate_line(
        "SimDirector: ALL GATES: ok alpha | RED beta[x=1] | ok gamma")
    ok("a gate line parses ok and RED into pass and fail",
       [p[1] for p in pills] == ["pass", "fail", "pass"], pills)
    pills2, merged2, _ = parse_gate_line(
        "ALL GATES: ok alpha[a=1|b=2] | ok beta")
    ok("a pipe inside a detail bracket merges and is COUNTED, not dropped",
       len(pills2) == 2 and merged2 == 1, (pills2, merged2))

    fake = pathlib.Path(tempfile.mkdtemp(prefix="dash-norun-"))
    (fake / "game-design").mkdir(parents=True)
    (fake / "game-design" / "sim-shots").mkdir(parents=True)
    (fake / "game-design" / "sim-shots" / "verdict.txt").write_text(
        "# Sim verdict abc1234 @1788272785\n%s - the sim did not run on this "
        "commit.\n" % NO_SIM, encoding="utf-8")
    norun = read_gate_pills(fake)
    ok("a verdict from a build that did not run gives NO green pill",
       not [p for p in norun["pills"] if p[1] == "pass"], norun["pills"])
    ok("and says so with the marker and the commit",
       any(NO_SIM in n and "abc1234" in n for n in norun["notes"]), norun["notes"])

    dis = pathlib.Path(tempfile.mkdtemp(prefix="dash-dates-"))
    (dis / "production" / "d1-probe").mkdir(parents=True)
    (dis / "game-design").mkdir(parents=True)
    (dis / "production" / "d1-probe" / "plan.md").write_text(
        "# D1 engine probe: execution plan (kicked off 2026-08-31, ends "
        "2026-09-14)\n", encoding="utf-8")
    (dis / "game-design" / "decision-D1b-rescope.md").write_text(
        "- Timebox: unchanged, ends 2026-09-20. No extension granted.\n",
        encoding="utf-8")
    clash = read_d1(dis, datetime.date(2026, 9, 1))
    ok("two sources disagreeing about the end date REFUSES rather than picking",
       not clash.available and "disagree" in (clash.reason or ""), clash.reason)

    broken = ("<!doctype html><html><head><style>.x{position:fixed;width:900px}"
              "</style></head><body><div><p>hello</body></html>")
    bfaults = page_faults(broken)
    ok("the page checker FINDS the faults the listening page shipped with "
       "(%d on a broken fixture)" % len(bfaults), len(bfaults) >= 4, bfaults)

    noweek = read_throughput(dis, datetime.date(2026, 9, 1))
    ok("a throughput ledger with no current-week row is not a zero",
       not noweek.available, noweek.text)

    print("\ndashboard selftest: %d passed, %d failed" % (passed, len(failed)))
    for f in failed:
        print("  FAILED: %s" % f)
    print("  NOT COVERED HERE, and it is the half that runs elsewhere: "
          "open-dashboard.bat and the Windows scheduled task never execute in "
          "this container (no Windows, no cmd), and the SessionStart hook and "
          "the night runner's per-iteration call are first-run questions. "
          "Their accepting case is the first run on the machine that has them.")
    return 1 if failed else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the studio status dashboard.")
    ap.add_argument("--selftest", action="store_true",
                    help="run the fixtures, accepting case first, and exit")
    ap.add_argument("--print", dest="show", action="store_true",
                    help="print STATUS.md to stdout and write nothing")
    ap.add_argument("--repo", default=None, help="repository root to read")
    ap.add_argument("--out-dir", default=None,
                    help="where the two artifacts go (default: the repo root)")
    ap.add_argument("--now", default=None,
                    help="ISO timestamp to treat as now (tests and reruns)")
    args = ap.parse_args(argv)

    # A correct run that ends in a BrokenPipeError traceback costs twenty
    # minutes before anybody notices it worked.
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass

    if cap is None:
        print("REFUSING TO RUN: tools/capsay.py could not be imported, so no "
              "truncation on this page could announce itself. That is the "
              "exact fault this page exists not to print.", file=sys.stderr)
        return 4
    if args.selftest:
        return selftest(args.repo)

    repo = pathlib.Path(args.repo or REPO).resolve()
    if not (repo / "CLAUDE.md").exists():
        print("REFUSING TO RUN: %s does not look like this repository (no "
              "CLAUDE.md). Nothing was written." % repo, file=sys.stderr)
        return 3
    now = (datetime.datetime.fromisoformat(args.now) if args.now
           else datetime.datetime.now())
    model = build_model(repo, now)
    if args.show:
        print(render_status(model))
        return 0
    out = pathlib.Path(args.out_dir).resolve() if args.out_dir else repo
    try:
        n1 = write_artifact(out / HTML_NAME, render_html(model))
        n2 = write_artifact(out / STATUS_NAME, render_status(model))
    except OSError as e:
        print("WRITE FAILED: %s" % e, file=sys.stderr)
        return 2
    unavailable = [r.label for r in all_readings(model) if not r.available]
    print("dashboard: wrote %s (%d bytes) and %s (%d bytes) from %d source(s), "
          "%d of %d reading(s) not yet applicable%s"
          % (HTML_NAME, n1, STATUS_NAME, n2, len(model["sources"]),
             len(unavailable), len(all_readings(model)),
             (": " + cap(unavailable, keep=3, sep=", ")) if unavailable else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
