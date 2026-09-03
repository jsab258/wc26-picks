#!/usr/bin/env python3
"""Build the studio status dashboard: a read-only lens over repo state.

    python3 tools/dashboard/build-dashboard.py            # write the two artifacts
    python3 tools/dashboard/build-dashboard.py --selftest  # accepting case first
    python3 tools/dashboard/build-dashboard.py --print     # STATUS.md to stdout, write nothing
    python3 tools/dashboard/build-dashboard.py --emit-json       # + the live document
    python3 tools/dashboard/build-dashboard.py --emit-live-page  # + the live page

WHAT IT IS. Deterministic, zero model calls. It reads repo files and writes
exactly two artifacts: dashboard.html and STATUS.md at the repo root. It is
NEVER a second source of truth: if a number here is wrong, the source file or
this generator is wrong, and this page is not the place to fix it.

AND TWO OPT-IN OUTPUTS, ADDED 2026-09-01 BECAUSE THE HOSTED PAGE WAS A
SNAPSHOT. It froze at publish time and went on looking current, which is worse
than no page at all. --emit-json writes the same model as one JSON document
and --emit-live-page writes a page that renders that document out of the
artifact document store, subscribing with onSnapshot so it updates in front of
a reader with no reload and no republish. Neither is written by a bare run.
The live page contains NO READINGS: render_live_page() takes no model, so
there is no argument for a number to arrive through, and the selftest asserts
not one of the live repository's readings appears in its bytes. A page that
fell back to numbers frozen at publish time would be the same snapshot fault
wearing a fallback's clothes, and frozen numbers look exactly like fresh ones.

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
writes anything, and it refuses any filename outside the four it knows. The
selftest proves that statically (an AST walk over this file: every write call
site is either that function or the selftest's own temp fixture) and at run
time: a generation into a temp directory with no flags creates exactly two
files, the same generation with both flags creates exactly those two plus the
two named live outputs, and neither leaves anything in the repo it read.
Weekly process audit check 9 asks for that proof.

EXIT CODES. 0 wrote the artifacts (or --print). 1 selftest failed. 2 a write
failed. 3 the repo root does not look like this repo. 4 a helper module this
program refuses to run without (tools/capsay.py) could not be imported: a
truncation notice that silently stops announcing is the fault this whole file
is about, so it stops rather than carrying on without one. 5 the live document
is over the store's per-document byte cap, so db.set() would reject it: it
refuses rather than leaving a file on disk that looks ready to publish.
"""
import argparse
import ast
import datetime
import html
import importlib.util
import json
import pathlib
import re
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent

HTML_NAME = "dashboard.html"
STATUS_NAME = "STATUS.md"
ARTIFACTS = (HTML_NAME, STATUS_NAME)

# THE TWO OPT-IN OUTPUTS. Neither is written by a bare run: the spec says the
# generator writes exactly two files, and the selftest asserts that in both
# directions (no flag -> 2 files on disk; both flags -> those 2 plus these 2,
# by name). They exist because the hosted page was a SNAPSHOT: it froze at
# publish time and went on looking current, which is the exact fault this whole
# file is written against, wearing a web page's clothes.
LIVE_PAGE_NAME = "live-dashboard.html"
LIVE_JSON_NAME = "live-dashboard.json"
LIVE_OUTPUTS = (LIVE_PAGE_NAME, LIVE_JSON_NAME)
WRITABLE = ARTIFACTS + LIVE_OUTPUTS

# THE CONTRACT BETWEEN THE TWO. The page carries the schema string; the JSON
# carries it too, and the page REFUSES to render a document whose schema it
# does not know rather than painting a wall of blanks that read as zeros. Bump
# this whenever a key the page reads changes shape, and the old page then says
# "this document is newer than this page" instead of lying quietly.
LIVE_SCHEMA = "ledger-status/1"
LIVE_DOC_PATH = "status/current"        # even segment count: collection/doc

REFRESH_SECONDS = 300
# The local page's rebuild cadence and the age at which it calls itself stale.
# NOT a measured series: 15 is what open-dashboard.bat /register schedules, and
# 20 is that interval plus a margin. Both numbers are PRINTED on the page next
# to the age, with the sentence naming where they come from, so a reader can
# see the bound rather than infer one. They live here as constants because the
# local page and the live page must not drift into two different rules.
REBUILD_MINUTES = 15
STALE_AFTER_MINUTES = 20
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
    "decisions": "production/decision-queue.md",
    "register": "ledger-v2/respec/decision-register",
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


# THE QUEUE'S OWN SECTIONS. WAITING is the needs-you section and nothing else
# is: a card under RULED has been decided and counting it as waiting would put
# a settled question back on Jafar's glance. Named here rather than matched
# loosely, so a new section heading in that file shows up as an unread section
# below rather than as a silent re-bucketing.
QUEUE_WAITING = "WAITING"
QUEUE_RULED = "RULED"
CLASS_LINE = re.compile(r"^\s*CLASS:\s*([A-Za-z]+)", re.M)
INTERRUPT_CLASSES = ("BLOCKING", "DECISION", "REVIEW", "FYI")


def queue_sections(text):
    """PURE. {section-name: [card-heading, ...]} for a decision-queue file, one
    entry per '### ' heading, plus each card's own body so the CLASS field can
    be read off it. Sections are '## ' headings; a card before any of them is
    kept under the empty name and reported rather than dropped."""
    out, name, card = {}, "", None
    for line in (text or "").splitlines():
        if line.startswith("## "):
            name = plain(line[3:]).upper()
            out.setdefault(name, [])
            card = None
            continue
        if line.startswith("### "):
            card = {"title": plain(line[4:]), "body": []}
            out.setdefault(name, []).append(card)
            continue
        if card is not None:
            card["body"].append(line)
    return out


def card_class(card):
    """The routing class of one card, or None. Missing is NOT FYI and not any
    other default: production/interrupt-classes.md says a card with no CLASS
    line is unclassified, because a default route is how a Blocking item lands
    on a page nobody opened."""
    m = CLASS_LINE.search("\n".join(card["body"]))
    if not m:
        return None
    got = m.group(1).upper()
    return got if got in INTERRUPT_CLASSES else "UNKNOWN:" + got


def read_decisions(repo):
    """The decision inbox: WAITING for needs-you, the register for decided.

    TWO SOURCES, TWO DIFFERENT QUESTIONS, and they are kept apart on purpose.
    WAITING answers "what is on Jafar right now". The register answers "what
    has been settled", and it lives in two places by the queue file's own rule:
    a D-record under the register directory when a ruling touches architecture
    or identity, a lighter RULED entry in the queue file otherwise. Both halves
    are counted and BOTH denominators are printed, because a decided count that
    quietly read one half would fall the day a ruling went to the other.

    The CLASS field is read off each waiting card so routing is data rather
    than judgement. A card with no CLASS is counted as unclassified and NAMED;
    it is never folded into FYI, which is the one class that is never pushed.
    """
    text = read(src(repo, "decisions"))
    reg = src(repo, "register")
    dfiles = sorted(p.name for p in reg.glob("D*.md")) if reg.is_dir() else []
    if text is None:
        return {"count": Reading.unavailable(
            "open decisions", "%s does not exist" % SOURCES["decisions"],
            [SOURCES["decisions"]]), "items": [], "verified": None,
            "decided": Reading.unavailable(
                "decided", "%s does not exist, so the RULED half of the "
                "register could not be read; the register directory holds %d "
                "D-record file(s)" % (SOURCES["decisions"], len(dfiles)),
                [SOURCES["decisions"], SOURCES["register"]]),
            "classes": {}, "unclassified": []}

    sections = queue_sections(text)
    waiting = sections.get(QUEUE_WAITING, [])
    ruled = [c for name, cards in sections.items() if name.startswith(QUEUE_RULED)
             for c in cards]
    other = [name for name in sections
             if name and name != QUEUE_WAITING and not name.startswith(QUEUE_RULED)]
    items = [c["title"] for c in waiting]

    classes, unclassified = {}, []
    for c in waiting:
        k = card_class(c)
        if k is None:
            unclassified.append(c["title"])
        else:
            classes[k] = classes.get(k, 0) + 1
    class_part = ("; every waiting card carries a CLASS (%s)"
                  % ",".join("%s=%d" % (k, v) for k, v in sorted(classes.items()))
                  if classes and not unclassified else
                  "; %d waiting card(s) carry no CLASS line and are "
                  "UNCLASSIFIED, never routed as FYI by default: %s"
                  % (len(unclassified), cap(unclassified, keep=2, sep=", "))
                  if unclassified else
                  "; no waiting card to take a CLASS from")

    v = re.search(r"verified (\d{4}-\d{2}-\d{2})", text)
    count = Reading.measured(
        "open decisions", len(items),
        "'### ' cards under '## %s' in %s, which is one per card%s%s%s" % (
            QUEUE_WAITING, SOURCES["decisions"], class_part,
            "; the file states it was verified " + v.group(1) if v else "",
            "; %d section(s) in the file are neither WAITING nor RULED and "
            "were not counted: %s" % (len(other), cap(other, keep=3, sep=", "))
            if other else ""),
        [SOURCES["decisions"]],
        "%d '### ' card(s) in the whole file across %d section(s), of which "
        "%d sit under %s" % (sum(len(c) for c in sections.values()),
                             len(sections), len(items), QUEUE_WAITING))
    decided = Reading.measured(
        "decided", len(ruled) + len(dfiles),
        "the register in BOTH its halves: %d lighter RULED entr(y/ies) in %s "
        "plus %d D-record file(s) in %s. A ruling goes to one half or the "
        "other by the queue file's own rule, so a count of either alone would "
        "understate it" % (len(ruled), SOURCES["decisions"], len(dfiles),
                           SOURCES["register"]),
        [SOURCES["decisions"], SOURCES["register"]],
        "%d RULED card(s) read plus %d file(s) matching D*.md%s"
        % (len(ruled), len(dfiles),
           "" if reg.is_dir() else " (the register directory does not exist)"))
    return {"count": count, "items": items, "verified": v.group(1) if v else None,
            "decided": decided, "classes": classes,
            "unclassified": unclassified}


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


# --------------------------------------------------------- the checkout's age
# WHY THIS IS ON THE PAGE, 2 Sep. The page said how old THE PAGE was and could
# not say how old THE CHECKOUT was, and those are different facts. A decision
# card was written, committed and pushed, the resident said it was on the
# dashboard, and Jafar's copy had never seen the commit: nothing on his screen
# could have told him which of the two was true. Told to run a .bat, he said:
# "not running a bat to update a dashboard. your job is to keep it up to date
# all the time, that's the whole point."
#
# WHAT MAY TOUCH THE TREE AND WHAT MAY NOT. `git pull --ff-only` advances the
# branch pointer or refuses; it cannot make a merge commit and cannot open an
# editor, which is the 26 Aug incident behind open-dashboard.bat's old "no git
# here" rule. The rule worth keeping from that incident is NEVER MERGE
# UNATTENDED, and this keeps it: a refused fast-forward is REPORTED, never
# resolved, and changes nothing at all.
#
# AND ZERO IS A MEASUREMENT, NOT A SHRUG. Level with origin is measured. A
# fetch that failed is UNAVAILABLE with its reason, because "I could not find
# out" printing as "fine" is the exact fault this page exists to refuse, and
# it would be arriving inside the honesty machinery itself.

CHECKOUT_LABEL = "checkout age"

#: Why a rebuild did not check. The launcher supplies MEMBERSHIP (which key);
#: every sentence lives here, in the layer the selftest runs, because a string
#: written in the .bat ships unrun on a machine that has no cmd.
CHECKOUT_SKIPPED = {
    "skip-not-asked":
        "this rebuild did not check. It ran without `--checkout refresh`, so "
        "nothing here spoke to the remote and how far behind this clone is "
        "was not measured. The registered task checks every %d minutes"
        % REBUILD_MINUTES,
    "skip-no-working-copy":
        "the launcher could not stage a working copy of itself, so it rebuilt "
        "in place and did not pull. A pull can rewrite a running .bat while "
        "cmd.exe is still reading it by byte offset, which is a real failure "
        "on this machine, so no-copy means no-pull",
}

#: Passed to every git child. GIT_EDITOR and GIT_MERGE_AUTOEDIT are the 26 Aug
#: guards that tools/lint-bat-editor.py asks of any .bat running git, set here
#: as well because the child is what git reads. GIT_TERMINAL_PROMPT and
#: GIT_ASKPASS are the UNATTENDED ones: a credential prompt inside a scheduled
#: task with no window waits for ever, and a refresh that hangs is a page that
#: silently stops being rebuilt. Both make an unauthenticated fetch FAIL, which
#: this page can print, rather than wait, which it cannot.
GIT_GUARD_ENV = {"GIT_EDITOR": "true", "GIT_MERGE_AUTOEDIT": "no",
                 "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "echo"}

#: A path component that means the CI runner owns this tree. See
#: runner_work_tree() for the evidence and why it is a check and not a comment.
RUNNER_WORK_MARKERS = ("_work", "actions-runner")

#: The self-hosted runner keeps Runner.Listener.exe up for ever and spawns ONE
#: Runner.Worker.exe per job, so the worker is the process that means a job is
#: running right now.
RUNNER_WORKER_PROCESS = "Runner.Worker.exe"


def runner_work_tree(repo_path):
    """The CI runner's own checkout, or None. PURE, takes a path.

    THE EVIDENCE, QUOTED RATHER THAN ASSUMED. ledger-pc is Jafar's PC and it is
    also the self-hosted GitHub Actions runner, so the two clones could in
    principle be one clone. On the evidence they are not: the runner is
    installed at C:/actions-runner-ledger (tools/runner/1 SET UP THE BUILD
    RUNNER.bat sets RUNNERDIR to exactly that, and tools/runner/README.md names
    it), and every path a real job has printed sits under its own _work tree,
    for instance C:/actions-runner-ledger/_work/wc26-picks/wc26-picks/ue-probe/
    in the committed UE verdict. The dashboard's clone is
    %USERPROFILE%/wc26-picks, which "UPDATE FROM CLAUDE.bat" sets REPO to and
    open-dashboard.bat falls back to.

    This function is what stops that evidence being an ASSUMPTION. If the page
    is ever generated from inside a work tree, no git runs at all: not even a
    fetch, because a fetch takes the same index and ref locks a running job's
    git commands take.
    """
    parts = [p.lower() for p in pathlib.Path(repo_path).parts]
    for p in parts:
        for m in RUNNER_WORK_MARKERS:
            if p == m or p.startswith(m):
                return p
    return None


def checkout_plan(repo_path, build_running):
    """PURE. (may_fetch, may_pull, hold): what this refresh may do, and why not.

    build_running is True, False, or None for could-not-tell. None is treated
    as not-running ON PURPOSE and the reason is structural rather than
    optimistic: the only way a pull here can move files under a job is if the
    two trees are the same tree, and the first clause settles that from the
    path without needing the process check at all. The process check is the
    belt on top of those braces, and it is Windows-only.
    """
    work = runner_work_tree(repo_path)
    if work:
        return False, False, (
            "held: this checkout is inside the CI runner's own work tree (a "
            "path component named '%s'), and a job's files must never move "
            "under it. No git ran, so the age was not measured" % work)
    if build_running:
        return True, False, ("held: a build is running on this PC (%s), so "
                             "nothing was pulled" % RUNNER_WORKER_PROCESS)
    return True, True, None


def build_running():
    """True, False, or None for could-not-tell. IMPURE: asks the OS.

    Windows only. Anywhere else this returns None and the page says the check
    did not run, rather than saying nothing is running, which is a different
    claim and one this cannot make.
    """
    if not sys.platform.startswith("win"):
        return None
    rc, out = _run(["tasklist", "/FI",
                    "IMAGENAME eq %s" % RUNNER_WORKER_PROCESS, "/NH"], None, 30)
    if rc != 0:
        return None
    return RUNNER_WORKER_PROCESS.lower() in (out or "").lower()


def _run(argv, cwd, timeout):
    """THE ONLY DOOR TO A SUBPROCESS in this program other than the live-page
    harness, and the write guard's AST walk is what keeps that true.

    Returns (rc, text) and never raises: a missing binary, a timeout and a
    refusal are all READINGS here, not crashes. rc 127 means the program is not
    on PATH and 124 means it did not finish, both distinct from any rc git
    itself returns.
    """
    import os
    import subprocess
    env = dict(os.environ)
    env.update(GIT_GUARD_ENV)
    try:
        r = subprocess.run(argv, capture_output=True, text=True,
                           timeout=timeout, cwd=cwd, env=env)
    except FileNotFoundError:
        return 127, "%s is not on PATH" % argv[0]
    except subprocess.TimeoutExpired:
        return 124, "%s did not finish inside %ds" % (" ".join(argv[:2]), timeout)
    except OSError as e:
        return 126, str(e)
    # ON SUCCESS, STDOUT ONLY. git writes advice and warnings to stderr even
    # when it worked, and this text is PARSED: a "warning: ..." line glued onto
    # a commit count is a number that reads as something else entirely. On a
    # failure both streams come back, because that is where the reason is.
    if r.returncode == 0:
        return 0, (r.stdout or "").strip()
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()


def _git(repo, args, timeout=120):
    """git, run in `repo`, with the guard env and no editor anywhere."""
    return _run(["git", "-C", str(repo)] + list(args), None, timeout)


def probe_checkout(repo, now, running=None):
    """Bring this checkout current, then say how current it is. Returns FACTS.

    THE ORDER IS THE POINT: pull first, then let build_model() read the tree, so
    the page is rendered from the files the pull brought in. Rendering first and
    pulling after would print a "level with origin" beside yesterday's content,
    which is a worse lie than the one this replaces.

    No sentence is built here. checkout_reading() turns these facts into the
    Reading, so the whole of the wording and the arithmetic can be driven by the
    selftest with no network and no remote.
    """
    f = {"repo": str(repo), "branch": None, "hold": None, "gitWhy": None,
         "fetchWhy": None, "behindBefore": None, "behind": None,
         "pulled": 0, "ffRefused": None, "before": None, "after": None,
         "at": now.strftime("%H:%M"), "buildRunning": running}
    rc, out = _git(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
    if rc != 0:
        f["gitWhy"] = out
        return f
    f["branch"] = out.strip().splitlines()[-1] if out.strip() else ""
    if f["branch"] in ("", "HEAD"):
        f["gitWhy"] = ("this clone is not on a branch (detached HEAD), so "
                       "there is no origin branch to count against")
        f["branch"] = None
        return f
    rc, before = _git(repo, ["rev-parse", "HEAD"])
    f["before"] = f["after"] = before.strip()[:12] if rc == 0 else None

    may_fetch, may_pull, f["hold"] = checkout_plan(repo, running)
    if not may_fetch:
        return f

    branch = f["branch"]
    rc, out = _git(repo, ["fetch", "--quiet", "origin", branch])
    if rc != 0:
        f["fetchWhy"] = out or "git fetch exited %d and said nothing" % rc
        return f
    rc, out = _git(repo, ["rev-list", "--count", "HEAD..origin/%s" % branch])
    if rc != 0 or not out.strip().isdigit():
        f["fetchWhy"] = ("the fetch succeeded but the count did not: %s"
                         % (out or "git rev-list exited %d silently" % rc))
        return f
    f["behind"] = f["behindBefore"] = int(out.strip())

    if f["behind"] and may_pull:
        rc, out = _git(repo, ["pull", "--ff-only", "origin", branch])
        f["ffRefused"] = rc != 0
        if rc != 0:
            f["fastForwardWhy"] = out
        rc, out = _git(repo, ["rev-list", "--count", "HEAD..origin/%s" % branch])
        if rc == 0 and out.strip().isdigit():
            f["behind"] = int(out.strip())
        else:
            # THE COUNT AFTER THE PULL IS THE ONLY ONE THAT DESCRIBES THE TREE
            # THE PAGE IS ABOUT TO READ. Without it, keeping the count from
            # before would print a number for a tree that has since moved.
            f["behind"] = None
            f["fetchWhy"] = ("the pull ran but the count after it did not: %s"
                             % (out or "git rev-list exited %d silently" % rc))
            return f
        f["pulled"] = max(0, f["behindBefore"] - f["behind"])
        rc, after = _git(repo, ["rev-parse", "HEAD"])
        f["after"] = after.strip()[:12] if rc == 0 else f["after"]
    return f


def checkout_reading(f, sources=(".git",)):
    """PURE: the facts from probe_checkout() as the Reading the page prints.

    Every branch that could not find out returns Reading.unavailable, so the
    one thing this can never render is a bare 0 standing for "unknown".
    """
    sources = list(sources)
    if f.get("gitWhy"):
        return Reading.unavailable(CHECKOUT_LABEL, f["gitWhy"], sources)
    if f.get("hold") and f.get("behind") is None:
        return Reading.unavailable(CHECKOUT_LABEL, f["hold"], sources)
    if f.get("fetchWhy"):
        return Reading.unavailable(
            CHECKOUT_LABEL,
            "the fetch failed, and this reading will not guess from a stale "
            "ref: %s" % clip(plain(f["fetchWhy"]), 160), sources)
    if f.get("behind") is None:
        return Reading.unavailable(
            CHECKOUT_LABEL, "nothing was measured and no reason was recorded, "
            "which is a fault in this instrument rather than in the checkout",
            sources)

    branch, n = f["branch"], f["behind"]
    value = ("level with origin/%s (0 commit(s) behind)" % branch if n == 0
             else "%d commit(s) behind origin/%s" % (n, branch))
    if f.get("ffRefused"):
        how = ("`git pull --ff-only origin %s` at %s was REFUSED and changed "
               "nothing (%s). A fast-forward is refused when this clone holds "
               "commits origin does not; it is reported here, never resolved "
               "unattended" % (branch, f["at"],
                               clip(plain(f.get("fastForwardWhy") or ""), 120)))
    elif f.get("pulled"):
        how = ("`git pull --ff-only origin %s` at %s advanced this clone by %d "
               "commit(s), from %s to %s" % (branch, f["at"], f["pulled"],
                                             f.get("before"), f.get("after")))
    elif f.get("hold"):
        how = ("`git fetch origin %s` at %s, then `git rev-list --count "
               "HEAD..origin/%s`; %s" % (branch, f["at"], branch, f["hold"]))
    else:
        how = ("`git fetch origin %s` at %s, then `git rev-list --count "
               "HEAD..origin/%s`; there was nothing to pull"
               % (branch, f["at"], branch))
    den = ("1 clone on branch %s, counted against origin/%s after the fetch at "
           "%s" % (branch, branch, f["at"]))
    return Reading.measured(CHECKOUT_LABEL, value, how, sources, den)


# -------------------------------------------------------------------- model

def build_model(repo, now, checkout=None):
    """One model, read once, rendered twice. The HTML and STATUS.md cannot
    disagree with each other because neither reads a source of its own.

    `checkout` arrives already measured because measuring it CHANGES THE FILES
    every reader below is about to read: main() refreshes first and builds
    second. A rebuild that was not asked to check says so, and says it in
    CHECKOUT_SKIPPED's words rather than in a zero.
    """
    today = now.date()
    phases = read_phases(repo)
    decisions = read_decisions(repo)
    return {
        "generated": now,
        "today": today,
        "repo": repo,
        "checkout": checkout or Reading.unavailable(
            CHECKOUT_LABEL, CHECKOUT_SKIPPED["skip-not-asked"], [".git"]),
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
           model["decisions"]["decided"],
           model["throughput"], model["judge"], model["checkout"]]
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

# THE TOKENS ARE WRITTEN ONCE. The live page needs the same two palettes for
# its [data-theme] rules, and a second copy of a colour set is the site nobody
# updates when the first is corrected. CSS below is assembled from them and is
# byte-identical to the string that used to be typed out here; the selftest
# pins that, because "same tokens" is only true if it is checked.
LIGHT_VARS = """  --bg:#fbfbfa; --fg:#1b1b1a; --dim:#5d5d58; --line:#dedcd6; --card:#ffffff;
  --amber:#8a5a00; --amberbg:#fff5e0; --pass:#1d6b3a; --passbg:#e4f3e9;
  --fail:#9a2020; --failbg:#fbe6e6; --na:#5d5d58; --nabg:#eeedea;"""

DARK_VARS = """  --bg:#15161a; --fg:#e9e8e4; --dim:#a3a19a; --line:#2e3038; --card:#1d1f25;
  --amber:#f0c060; --amberbg:#2f2612; --pass:#7fd4a0; --passbg:#16301f;
  --fail:#ff9a9a; --failbg:#331717; --na:#a3a19a; --nabg:#24262c;"""

CSS = "\n:root { color-scheme: light dark;\n" + LIGHT_VARS + " }\n" \
      "@media (prefers-color-scheme: dark) { :root {\n" + DARK_VARS + " } }\n" + """* { box-sizing:border-box; }
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

# ONE IMPLEMENTATION OF THE STALENESS RULE. The two numbers used to be typed
# into this script; the live page needs the same rule, and a second copy is the
# site nobody looks at when the first is fixed. Substituted rather than
# rewritten, so the rendered local page is byte-identical to the one that
# shipped: the selftest pins that sentence verbatim.
AGE_JS = """
(function(){var e=document.getElementById("age");if(!e)return;
var t=new Date(e.getAttribute("data-gen"));
var m=Math.round((Date.now()-t.getTime())/60000);
e.textContent=(m<1?"just now":m+" min ago");
if(m>%d){e.className="stale";
e.textContent=m+" min ago, older than the %d minute regeneration interval: "+
"treat every number below as that old, the regenerator may not be running";}})();
""" % (STALE_AFTER_MINUTES, REBUILD_MINUTES)


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
    # THE PAGE'S AGE AND THE CHECKOUT'S AGE, ONE UNDER THE OTHER. They are
    # different facts and the whole finding behind this line is that a page
    # regenerated thirty seconds ago from a six-hour-old pull reads as current.
    co = model["checkout"]
    a('<p class="sub">Files this page read: <b>%s</b>. <span class="why">%s'
      "</span></p>" % (esc(co.text), esc(co.note)))

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
    d = dec["decided"]
    a('<p class="why">Decided (the register, both halves): %s. %s</p>'
      % (esc(d.text), esc(d.note)))

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
    a("Files this page read: %s" % model["checkout"].text)
    a("(%s)" % model["checkout"].note)
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
    a("- %s: %s. %s" % (dec["decided"].label, dec["decided"].text,
                        dec["decided"].note))
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


# --------------------------------------------------- the live document (JSON)
# WHY THIS EXISTS. The hosted page was a SNAPSHOT: it froze at publish time and
# went on looking current, which is worse than no page. The repair is a
# document store the page subscribes to, and a JSON document the resident
# writes into it whenever this generator runs.
#
# ONE COMPUTATION, THREE RENDERINGS. build_model() is read once; render_html,
# render_status and build_json all take that model and none of them opens a
# source of its own. The JSON is therefore not a second set of numbers, and
# the selftest asserts every reading's text and note are identical across the
# markdown and the document.
#
# EVERY DISPLAY STRING IS FORMATTED HERE, in the layer the tests run. The page
# prints `text` and `note` verbatim and computes exactly one thing: how many
# minutes ago the stamp beside them was written. A formatter written in the
# page's JavaScript would ship unrun, and an unrun formatter printing a
# plausible string is the silent-instrument failure.

GATE_DETAIL_WIDTH = 220        # the width both renderings clip a pill title to
DOC_BYTE_CAP = 256 * 1024      # the store's own per-document cap (db.d.ts)


def aware(dt):
    """A timestamp that names its own offset.

    THE FAULT THIS EXISTS FOR, and it is the sharpest one on this page.
    datetime.now() is NAIVE, and a browser reads a naive ISO string as the
    VIEWER's local time. Writer in UTC, viewer at +02:00, and a document
    written two hours ago reads as written two hours in the FUTURE: the age
    goes negative, "just now" prints, and a feed that has stopped looks live
    for exactly as long as the offset between the two clocks. The live page
    does its arithmetic on the epoch integer beside this string, never on the
    string, and the string carries its offset so a human is not misled either.
    """
    return dt if dt.tzinfo else dt.astimezone()


def reading_json(r):
    """One Reading as the live document carries it.

    text and note are what the page prints. value, derivation, denominator and
    reason ride along for an auditor reading the raw document; nothing
    recomputes text from them.
    """
    return {"label": r.label, "text": r.text, "note": r.note,
            "available": bool(r.available),
            "value": None if r.value is None else str(r.value),
            "derivation": r.derivation, "denominator": r.denominator,
            "reason": r.reason}


def build_json(model):
    """The whole page as one plain-JSON object: the document the page reads."""
    g = aware(model["generated"])
    q, b = model["queue"], model["budget"]
    gates, dec, ph = model["gates"], model["decisions"], model["phases"]
    rows, clause = inflight_shown(model)
    return {
        "schema": LIVE_SCHEMA,
        "generator": "tools/dashboard/build-dashboard.py",
        "docPath": LIVE_DOC_PATH,
        "repo": str(model["repo"]),
        # THREE FIELDS FOR ONE INSTANT, and they are one instant: g is bound
        # once above. The text is for a human, the epoch is for the arithmetic,
        # the ISO carries the offset so neither can be read in the wrong zone.
        "generatedAt": g.isoformat(),
        "generatedAtEpochMs": int(g.timestamp() * 1000),
        "generatedAtText": g.strftime("%Y-%m-%d %H:%M %z"),
        "staleAfterMinutes": STALE_AFTER_MINUTES,
        "rebuildMinutes": REBUILD_MINUTES,
        "cadenceNote": (
            "This feed carries whatever the last regeneration wrote into the "
            "store; it does not poll the repository. The registered rebuild "
            "runs every %d minutes, so an age past %d minutes means the WRITER "
            "has stopped, not that the project is quiet."
            % (REBUILD_MINUTES, STALE_AFTER_MINUTES)),
        "phase": reading_json(ph["current"]),
        "phaseRows": [{"phase": p, "milestone": clip(plain(mst), 110),
                       "state": st, "why": why}
                      for p, mst, st, why in ph["rows"]],
        "phaseRule": ph["rule"],
        "decisions": {"count": reading_json(dec["count"]),
                      "items": list(dec["items"]),
                      "verified": dec["verified"]},
        "queue": {"cards": [reading_json(c) for c in q["cards"]],
                  "rule": q["rule"],
                  "unclassifiedText": (cap(q["unclassified"], keep=4)
                                       if q["unclassified"] else None),
                  "misfiledText": (cap(q["misfiled"], keep=4)
                                   if q["misfiled"] else None)},
        "inflight": {"rows": [{"name": r["name"], "status": r["status"],
                               "note": r["note"],
                               "available": bool(r["available"])}
                              for r in rows],
                     "capText": clause},
        "budget": {k: reading_json(b[k])
                   for k in ("monthly", "oneoff", "spend", "usage")},
        "gates": {"pills": [{"name": n, "state": s,
                             "detail": clip(d, GATE_DETAIL_WIDTH)}
                            for n, s, d in gates["pills"]],
                  "notes": list(gates["notes"]),
                  "overflowText": gates["overflow"]},
        "verification": {"throughput": reading_json(model["throughput"]),
                         "judge": reading_json(model["judge"])},
        "readings": [reading_json(r) for r in all_readings(model)],
        "sourcesText": ", ".join("%s%s" % (p, "" if ok else " (ABSENT)")
                                 for _, p, ok in model["sources"]),
        "reusedText": ", ".join(model["reused"]) or NOTHING,
        "footer": FOOTER_LINE,
    }


def doc_bytes(doc):
    """What the STORE will measure: the compact serialization, not the file."""
    return len(json.dumps(doc, separators=(",", ":")).encode("utf-8"))


def doc_size_fault(doc):
    """None, or the sentence to refuse with. A document over the store's cap
    would be rejected by db.set() at write time, and a file sitting on disk
    looking ready to publish is the wrong place to find that out."""
    n = doc_bytes(doc)
    if n <= DOC_BYTE_CAP:
        return None
    return ("the live document is %d bytes compact, over the store's %d byte "
            "per-document cap; db.set() would reject it with invalid_argument"
            % (n, DOC_BYTE_CAP))


# ------------------------------------------------------------- the live page
# THE ONE RULE THIS PAGE IS BUILT AROUND: it contains NO READINGS. render_live
# _page() takes no model, so there is nothing for a number to be baked from -
# the fault is structurally unreachable rather than guarded against. A page
# that fell back to numbers frozen at publish time would be the snapshot fault
# wearing a fallback's clothes, and it would be invisible: frozen numbers look
# exactly like fresh ones.
#
# It is published by the Artifact tool, which supplies its own skeleton, so
# there is no doctype, html, head or body tag here: title, style, content.

LIVE_THEME_CSS = ("\n/* The host's explicit viewer choice must beat the OS "
                  "setting. These sit AFTER the\n   prefers-color-scheme block "
                  "and match its specificity, so source order decides\n   and "
                  "the later rule wins. Custom properties inherit, so the "
                  "attribute works\n   on the html element or on the body element. */\n"
                  '[data-theme="light"] {\n' + LIGHT_VARS + " }\n"
                  '[data-theme="dark"] {\n' + DARK_VARS + " }\n"
                  """body { padding:0; }
.wrap { max-width:760px; margin-inline:auto; padding:14px; }
.feed { border:1px solid var(--line); background:var(--card); border-radius:6px;
  padding:9px 11px; margin:10px 0 2px; font-size:12.5px; color:var(--dim); }
.feed b { color:var(--fg); font-size:13.5px; }
.feed.stopped { border-color:var(--fail); background:var(--failbg); color:var(--fail); }
.feed.stopped b { color:var(--fail); }
.note { border:1px solid var(--amber); background:var(--amberbg); color:var(--amber);
  border-radius:6px; padding:11px 13px; margin:12px 0; font-size:13px; }
.note b { display:block; margin-bottom:4px; font-size:14px; }
.note.calm { border-color:var(--line); background:var(--card); color:var(--dim); }
.note code { background:var(--nabg); padding:1px 4px; border-radius:3px; }
.pending { color:var(--dim); font-size:12.5px; }
""")

# Every string the page can print while it has no document. They live in
# Python because that is where they are read by a test; the page prints them
# and composes none of them. No newlines in any of them: they are carried into
# the script as JSON, and a literal backslash-n inside a script block is a
# fault this repo has shipped before and now checks for.
LIVE_TEXT = {
    "connecting": "Connecting to the live store.",
    "connectingWhy":
        "The db capability resolves asynchronously and can take up to 10 "
        "seconds when the host does not answer. No numbers are shown until a "
        "document arrives, because every number on this page comes from the "
        "store and this page has none of its own.",
    "noHostTitle": "This page is not running inside the artifact host.",
    "noHostWhy":
        "window.claude is absent, so there is no capability to reach the "
        "store through. That happens to a saved copy of this file or a copy "
        "served from another host. Nothing is shown, because a page with no "
        "feed has no numbers.",
    "noDbTitle": "The live data store is not available in this view.",
    "noDbWhy":
        "The db capability resolved null, which means it is not served on "
        "this view, was not granted at initialization, or its module failed "
        "to load. Those three are indistinguishable by design, so this page "
        "cannot say which. Nothing is shown: the only numbers this page has "
        "ever had come from that store.",
    "emptyTitle": "The live store has no status document yet.",
    "emptyWhy":
        "Nothing has ever been written to this feed, which is a different "
        "fact from the project having nothing to report. What puts data "
        "there: run the generator with --emit-json and write the resulting "
        "document into the store at the path above.",
    "schemaTitle": "This page cannot read the document in the store.",
    "schemaWhy":
        "The document carries a schema this page does not know, so its fields "
        "may have moved. Rendering it would print blanks that read as zeros. "
        "Republish this page from the generator that wrote the document.",
    "noStampTitle": "The document carries no write time.",
    "noStampWhy":
        "generatedAtEpochMs is missing or not a number, so this page cannot "
        "say how old the numbers below are. Treat their age as UNKNOWN, which "
        "is not the same as fresh.",
    "deadTitle": "The live feed has stopped and this page is now frozen.",
    "deadWhy":
        "The subscription ended with a terminal error, so nothing below can "
        "update again on this page load. The stamp on the feed line is when "
        "the numbers were read, and it is the last one this page will ever "
        "see. Reload to reconnect.",
    "futureWarn":
        "The stamp is AHEAD of this browser's clock, so the age is not "
        "trustworthy: one of the two clocks is wrong.",
    "cachedNote":
        "This delivery is a cached view and is not yet server-definitive; a "
        "definitive one follows on its own.",
    "footerLive":
        "Live from the artifact document store. Numbers change in front of "
        "you when the writer writes; nothing here is baked into the page.",
}

LIVE_JS = r"""
(function(){
var K = __LIVE_CONSTANTS__;
function $(id){ return document.getElementById(id); }
function esc(s){ return String(s === null || s === undefined ? "" : s)
  .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
  .replace(/"/g,"&quot;"); }
function why(t){ return t ? '<p class="why">' + esc(t) + '</p>' : ""; }
function note(cls, title, body){ return '<div class="note ' + cls + '"><b>'
  + esc(title) + '</b>' + esc(body) + '</div>'; }

/* THE ONLY STATE, AND IT IS ONE ASSIGNMENT. The body and the stamp are taken
   from the same snapshot in the same statement, so the age line can never
   describe a different document from the numbers under it. */
var doc = null, stampMs = 0, dead = false;

function card(r){
  if(!r){ return '<div class="card"><div class="num none">' + esc(K.nothing)
    + '</div><div class="lab">absent</div><div class="why">'
    + esc(K.missingField) + '</div></div>'; }
  return '<div class="card"><div class="' + (r.available ? "num" : "num none")
    + '">' + esc(r.text) + '</div><div class="lab">' + esc(r.label)
    + '</div><div class="why">' + esc(r.note) + '</div></div>';
}
function pill(name, state, title){
  return '<span class="pill ' + esc(state) + '" title="' + esc(title) + '">'
    + esc(name) + '</span>';
}
function section(id, html){ var e = $(id); if(e){ e.innerHTML = html; } }
function blank(msg){
  var ids = K.sectionIds, i;
  for(i = 0; i < ids.length; i++){ section(ids[i], why(msg)); }
  var p = $("phase"); if(p){ p.textContent = msg; }
}
function stop(title, body){
  blank(K.nothing + ": " + title);
  $("state").innerHTML = note("", title, body);
  var f = $("feed"); if(f){ f.className = "feed"; f.innerHTML = esc(K.nothing)
    + ": nothing has been read from the store on this page load."; }
}

function ageText(mins){
  if(mins < -1){ return Math.abs(mins) + " min IN THE FUTURE. " + K.futureWarn; }
  if(mins < 1){ return "less than a minute ago"; }
  return mins + " min ago";
}
/* Recomputed on a timer as well as on delivery: a feed that has stopped must
   go on ageing in front of the reader rather than sitting at whatever it said
   when the last document arrived. */
function paintAge(){
  var f = $("feed"); if(!f || !doc){ return; }
  if(!stampMs){
    f.className = "feed stopped";
    f.innerHTML = "<b>" + esc(K.noStampTitle) + "</b> " + esc(K.noStampWhy);
    return;
  }
  var mins = Math.round((Date.now() - stampMs) / 60000);
  var lim = (typeof doc.staleAfterMinutes === "number")
    ? doc.staleAfterMinutes : K.staleAfterMinutes;
  var stopped = dead || mins > lim;
  f.className = stopped ? "feed stopped" : "feed";
  f.innerHTML = "<b>" + esc(dead ? "FEED DEAD" : (stopped ? "FEED STOPPED"
    : "Live")) + "</b> " + esc("Repo read " + (doc.generatedAtText || "?")
    + ", " + ageText(mins) + ". ") + esc(doc.cadenceNote || "")
    + (dead ? " " + esc(K.deadWhy) : "");
}

function paint(d, meta){
  var i, h;
  var p = $("phase");
  if(p){ p.textContent = "Current phase: "
    + ((d.phase && d.phase.text) || K.nothing)
    + ((d.phase && d.phase.note) ? ". " + d.phase.note : ""); }

  var dc = d.decisions || {};
  var n = dc.count;
  if(!n){ section("sec-decisions", why(K.missingField)); }
  else if(!n.available){
    section("sec-decisions", note("", "Decision inbox: " + n.text, n.note)); }
  else if(String(n.value) === "0"){
    section("sec-decisions", note("calm",
      "Decision inbox: nothing waiting on Jafar.", n.note)); }
  else {
    h = "";
    for(i = 0; i < (dc.items || []).length; i++){
      h += "<li>" + esc(dc.items[i]) + "</li>"; }
    section("sec-decisions", '<div class="note"><b>'
      + esc("Decision inbox: " + n.text + " waiting on Jafar")
      + "</b><ol>" + h + "</ol>" + why(n.note) + "</div>"); }

  var rows = d.phaseRows || [];
  h = '<div class="pills">';
  for(i = 0; i < rows.length; i++){
    h += pill(rows[i].phase + " " + rows[i].state, rows[i].state,
      rows[i].milestone + " | " + rows[i].why); }
  h += "</div>" + why(d.phaseRule);
  section("sec-phases", rows.length ? h : why(K.missingField));

  var q = d.queue || {};
  h = '<div class="cards">';
  for(i = 0; i < (q.cards || []).length; i++){ h += card(q.cards[i]); }
  h += "</div>" + why(q.rule ? q.rule + "." : "");
  if(q.unclassifiedText){ h += why("unclassified status word(s), counted in no card: "
    + q.unclassifiedText); }
  if(q.misfiledText){ h += why("carrying a DONE status but still in queue/: "
    + q.misfiledText); }
  section("sec-queue", (q.cards || []).length ? h : why(K.missingField));

  var fl = d.inflight || {};
  h = "";
  for(i = 0; i < (fl.rows || []).length; i++){
    var r = fl.rows[i];
    h += '<div class="row' + (r.available ? "" : " na") + '"><div class="nm">'
      + esc(r.name) + '</div><div class="st">' + esc(r.status)
      + '</div><div class="why">' + esc(r.note) + "</div></div>"; }
  if(fl.capText){ h += why("(+ not shown) " + fl.capText); }
  section("sec-inflight", h || why(K.missingField));

  var b = d.budget || {};
  h = '<div class="cards">' + card(b.monthly) + card(b.oneoff) + "</div>";
  h += (b.spend && b.spend.available)
    ? '<div class="bar"><div style="width:0"></div></div>'
    : '<div class="bar none"></div>';
  if(b.spend){ h += '<p class="why"><b>' + esc("Spend to date: " + b.spend.text
    + ".") + "</b> " + esc(b.spend.note) + "</p>"; }
  if(b.usage){ h += why(b.usage.label + ": " + b.usage.text + ". "
    + b.usage.note); }
  section("sec-budget", h);

  var g = d.gates || {};
  h = "";
  for(i = 0; i < (g.notes || []).length; i++){ h += why(g.notes[i]); }
  if((g.pills || []).length){
    h += '<div class="pills">';
    for(i = 0; i < g.pills.length; i++){
      h += pill(g.pills[i].name, g.pills[i].state, g.pills[i].detail); }
    h += "</div>";
  } else { h += why(K.nothing); }
  if(g.overflowText){ h += why("(+ not shown) " + g.overflowText); }
  section("sec-gates", h);

  var v = d.verification || {};
  section("sec-verification", '<div class="cards">' + card(v.throughput)
    + card(v.judge) + "</div>");

  h = "<table><tr><th>reading</th><th>value</th><th>derivation</th></tr>";
  for(i = 0; i < (d.readings || []).length; i++){
    var rr = d.readings[i];
    h += "<tr><td>" + esc(rr.label) + "</td><td>" + esc(rr.text) + "</td><td>"
      + esc(rr.note) + "</td></tr>"; }
  h += "</table>" + why("Sources opened under " + (d.repo || "?") + ": "
    + (d.sourcesText || K.nothing))
    + why("Reused rather than reimplemented: " + (d.reusedText || K.nothing))
    + why(d.footer || "");
  section("sec-derivations", (d.readings || []).length ? h : why(K.missingField));

  $("state").innerHTML = (meta && meta.fromCache) ? why(K.cachedNote) : "";
}

function onDoc(snap){
  if(!snap || !snap.exists){ stop(K.emptyTitle, K.emptyWhy + " Path: "
    + K.docPath + ". Command: " + K.emitCmd); return; }
  var d = snap.data();
  if(!d){ stop(K.emptyTitle, K.emptyWhy + " Path: " + K.docPath
    + ". Command: " + K.emitCmd); return; }
  if(d.schema !== K.schema){ stop(K.schemaTitle, K.schemaWhy
    + " This page reads " + K.schema + "; the document says "
    + (d.schema || "nothing at all") + "."); return; }
  doc = d; stampMs = (typeof d.generatedAtEpochMs === "number")
    ? d.generatedAtEpochMs : 0;
  paint(d, snap.metadata);
  paintAge();
}

function onErr(e){
  dead = true;
  var code = (e && e.code) ? e.code : "unknown";
  if(doc){ paintAge(); $("state").innerHTML = note("", K.deadTitle,
    K.deadWhy + " Error code: " + code + "."); }
  else { stop(K.deadTitle, K.deadWhy + " Error code: " + code + "."); }
}

function boot(){
  if(typeof window === "undefined" || !window.claude
     || typeof window.claude.use !== "function"){
    stop(K.noHostTitle, K.noHostWhy); return; }
  $("state").innerHTML = note("calm", K.connecting, K.connectingWhy);
  window.claude.use("db").then(function(db){
    if(!db){ stop(K.noDbTitle, K.noDbWhy); return; }
    var ref;
    try { ref = db.doc(K.docPath); }
    catch(err){ stop(K.schemaTitle, "The document path " + K.docPath
      + " is not valid: " + (err && err.message) + "."); return; }
    ref.onSnapshot(onDoc, onErr);
    setInterval(paintAge, 15000);
  }, function(){ stop(K.noDbTitle, K.noDbWhy); });
}
boot();
})();
"""

LIVE_SECTION_IDS = ["sec-decisions", "sec-phases", "sec-queue", "sec-inflight",
                    "sec-budget", "sec-gates", "sec-verification",
                    "sec-derivations"]


def live_constants():
    """Every literal the page needs, assembled here so the page composes none
    of them. Carried into the script as one JSON object."""
    k = dict(LIVE_TEXT)
    k.update({
        "schema": LIVE_SCHEMA,
        "docPath": LIVE_DOC_PATH,
        "emitCmd": "python3 tools/dashboard/build-dashboard.py --emit-json",
        "nothing": NOTHING,
        "staleAfterMinutes": STALE_AFTER_MINUTES,
        "sectionIds": LIVE_SECTION_IDS,
        "missingField": (NOTHING + ": the live document has no data for this "
                         "panel. The writer and this page are out of step."),
    })
    return k


def render_live_page():
    """The live page. TAKES NO MODEL, ON PURPOSE.

    There is no argument here for a reading to arrive through, so the page
    cannot carry a number frozen at publish time even by accident. Its output
    is a function of this file's constants alone, which the selftest checks the
    hard way: it renders once against the live repository's readings and
    asserts not one of them appears in the bytes.

    No doctype, html, head or body tag: the Artifact tool supplies the
    skeleton and this is the content that goes inside it.
    """
    head = ["<title>LEDGER studio status (live)</title>",
            "<style>%s</style>" % (CSS + LIVE_THEME_CSS)]
    a = head.append
    a('<div class="wrap">')
    a("<h1>LEDGER studio status</h1>")
    a('<p class="sub" id="phase">Current phase: waiting for the live store.</p>')
    a('<div class="feed" id="feed">%s</div>'
      % esc(NOTHING + ": nothing has been read from the store yet."))
    a('<div id="state"></div>')
    a('<div id="sec-decisions" class="pending">Decision inbox: waiting for the '
      "live store.</div>")
    for title, ident in (("Phases", "sec-phases"), ("Queue", "sec-queue"),
                         ("In flight", "sec-inflight"), ("Budget", "sec-budget"),
                         ("Gates", "sec-gates"),
                         ("Verification", "sec-verification"),
                         ("Where every number came from", "sec-derivations")):
        a("<h2>%s</h2>" % esc(title))
        a('<div id="%s" class="pending">waiting for the live store.</div>'
          % ident)
    a("<footer>%s %s Document: %s. Page schema: %s.</footer>"
      % (esc(FOOTER_LINE), esc(LIVE_TEXT["footerLive"]), esc(LIVE_DOC_PATH),
         esc(LIVE_SCHEMA)))
    a("</div>")
    a("<script>%s</script>" % LIVE_JS.replace(
        "__LIVE_CONSTANTS__", json.dumps(live_constants(), sort_keys=True)))
    return "\n".join(head) + "\n"


def live_page_faults(page, forbidden=()):
    """OPEN THE ARTIFACT, for the page nobody in this container can render.

    THERE IS NO BROWSER HERE and there is no artifact host here either, so the
    first load on Jafar's machine is this page's real accepting case and that
    is said out loud rather than implied. What a parser CAN settle is every
    fault this contract makes cheap to ship: a skeleton tag the host also
    emits, a capability member that does not exist (window.claude.db), a page
    that never subscribes, and above all a reading baked into the bytes.

    `forbidden` is the live repository's own readings. Returns findings, so it
    runs against a deliberately broken page as well as the real one.
    """
    found = tag_balance(page)
    for tag in ("<!doctype", "<html", "<head", "<body"):
        if tag in page.lower():
            found.append("carries %s, which the artifact host also emits" % tag)
    if not page.startswith("<title>"):
        found.append("does not open with the title element")
    if "<style>" not in page.split("<div", 1)[0]:
        found.append("the style block is not above the content")
    if 'claude.use("db")' not in page:
        found.append("never calls claude.use(\"db\")")
    if "onSnapshot" not in page:
        found.append("never subscribes: onSnapshot is not called, so the page "
                     "reads once and is a snapshot again")
    if re.search(r"claude\s*\.\s*db\b", page):
        found.append("reads window.claude.db, which this contract says is "
                     "undefined at every moment")
    if "[data-theme=" not in page:
        found.append("no [data-theme] rules: an explicit viewer choice cannot "
                     "beat the OS setting")
    if "prefers-color-scheme" not in page:
        found.append("no prefers-color-scheme block")
    if "position:fixed" in page.replace(" ", ""):
        found.append("a fixed element can sit on top of the content under it")
    for m in re.finditer(r"(?<![-a-z])width:\s*(\d+)px", page):
        if int(m.group(1)) > PHONE_WIDTH:
            found.append("a %spx fixed width scrolls a %dpx phone sideways"
                         % (m.group(1), PHONE_WIDTH))
    body = (page.split("<script>", 1)[-1].split("</script>", 1)[0]
            if "<script>" in page else "")
    if not body:
        found.append("no script at all, so nothing can ever read the store")
    if "\\n" in body:
        found.append("a literal backslash-n inside the script: the listening "
                     "page shipped one and it killed every control")
    if "src=" in body or "http://" in body or "https://" in body:
        found.append("the script reaches outside the file")
    baked = [f for f in forbidden if f and len(str(f)) >= 5 and str(f) in page]
    if baked:
        found.append("BAKED READING(S) in the page, which is the snapshot "
                     "fault wearing a fallback's clothes: %s"
                     % cap(baked, keep=3, sep=", ", width=60))
    return found


# ----------------------------------------------- running the page's own script
# RULE 4: OPEN THE ARTIFACT YOU ARE SHIPPING. There is no browser here and no
# artifact host either, so the rendered PIXELS stay unverified and that is said
# out loud in the selftest's closing note. Its LOGIC does not have to stay
# unverified: node is a JavaScript engine, the script in the page is ordinary
# script, and a DOM shim of four methods is enough to drive it through every
# state it can be in. Six of the seven states below can never be produced by
# hand on the real page - nobody can make claude.use() return null on demand -
# so without this they would ship having been reasoned about and never run,
# which is the shape of every guard in rule 5b that blocked the good case.
#
# The harness supplies the fakes; the assertions live in Python beside every
# other assertion in this file. If node is absent it reports NOT MEASURED with
# its reason and passes nothing: a checker that quietly skips is the zero with
# no denominator.

LIVE_HARNESS_JS = r"""
var fs = require("fs");
var page = fs.readFileSync(process.argv[2], "utf8");
var doc = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
var src = page.split("<script>")[1].split("</scr" + "ipt>")[0];
var ids = (page.match(/id="[^"]+"/g) || []).map(function(s){
  return s.slice(4, -1); });

globalThis.setInterval = function(){ return 0; };

function mkdom(){
  var els = {};
  ids.forEach(function(id){
    els[id] = { innerHTML: "", textContent: "", className: "" }; });
  globalThis.document = { getElementById: function(id){
    return Object.prototype.hasOwnProperty.call(els, id) ? els[id] : null; } };
  return els;
}
function dump(els){
  return Object.keys(els).map(function(k){
    return k + " >> " + els[k].className + " >> " + els[k].innerHTML + " "
      + els[k].textContent; }).join("\n");
}
function fakeDb(plan){
  return { doc: function(){ return { onSnapshot: function(next, err){
    if(plan.snap){ next(plan.snap); }
    if(plan.err){ err(plan.err); }
    return function(){}; } }; } };
}
function snap(body, fromCache){
  return { exists: body !== null, data: function(){ return body; },
           metadata: { fromCache: !!fromCache, hasPendingWrites: false } };
}
function copy(o){ return JSON.parse(JSON.stringify(o)); }

function run(win){
  var els = mkdom();
  globalThis.window = win;
  (0, eval)(src);
  return new Promise(function(res){
    setTimeout(function(){ setTimeout(function(){ res(dump(els)); }, 1); }, 1);
  });
}
function withDb(plan){
  return { claude: { use: function(){ return Promise.resolve(fakeDb(plan)); } } };
}

var now = Date.now();
var fresh = copy(doc); fresh.generatedAtEpochMs = now - 60000;
var stale = copy(doc); stale.generatedAtEpochMs = now - 3600000;
var future = copy(doc); future.generatedAtEpochMs = now + 10800000;
var nostamp = copy(doc); delete nostamp.generatedAtEpochMs;
var wrongschema = copy(doc); wrongschema.schema = "something-else/9";

var plan = [
  ["noHost", function(){ return run({}); }],
  ["noDb", function(){ return run({ claude: { use: function(){
      return Promise.resolve(null); } } }); }],
  ["useThrows", function(){ return run({ claude: { use: function(){
      return Promise.reject(new Error("boom")); } } }); }],
  ["empty", function(){ return run(withDb({ snap: snap(null) })); }],
  ["wrongSchema", function(){ return run(withDb({ snap: snap(wrongschema) })); }],
  ["fresh", function(){ return run(withDb({ snap: snap(fresh) })); }],
  ["stale", function(){ return run(withDb({ snap: snap(stale) })); }],
  ["future", function(){ return run(withDb({ snap: snap(future) })); }],
  ["noStamp", function(){ return run(withDb({ snap: snap(nostamp) })); }],
  ["cached", function(){ return run(withDb({ snap: snap(fresh, true) })); }],
  ["deadCold", function(){ return run(withDb({ err: { code: "revoked",
      message: "grant withdrawn" } })); }],
  ["deadAfterDoc", function(){ return run(withDb({ snap: snap(fresh),
      err: { code: "revoked", message: "grant withdrawn" } })); }]
];

(async function(){
  var out = {};
  for(var i = 0; i < plan.length; i++){
    try { out[plan[i][0]] = await plan[i][1](); }
    catch(e){ out[plan[i][0]] = "THREW: " + (e && e.stack ? e.stack : e); }
  }
  process.stdout.write(JSON.stringify(out));
})();
"""


def run_live_harness(harness_path, page_path, doc_path):
    """(results, reason). results is None when node is not here, and the reason
    says so rather than a caller inferring a clean run from an empty dict."""
    import subprocess
    try:
        r = subprocess.run(["node", str(harness_path), str(page_path),
                            str(doc_path)], capture_output=True, timeout=60)
    except (OSError, ValueError) as e:
        return None, "node could not be started (%s)" % e
    except Exception as e:                                       # noqa: BLE001
        return None, "node did not finish (%s)" % e
    if r.returncode != 0:
        return None, "node exited %d: %s" % (
            r.returncode, r.stderr.decode("utf-8", "replace")[-400:])
    try:
        return json.loads(r.stdout.decode("utf-8", "replace")), ""
    except ValueError as e:
        return None, "node printed something that is not JSON (%s): %s" % (
            e, r.stdout.decode("utf-8", "replace")[:200])


# ------------------------------------------------------------- the only write

def write_artifact(path, text):
    """THE ONLY FUNCTION IN THIS PROGRAM THAT WRITES ANYTHING.

    It refuses any name outside WRITABLE, so "this generator is read-only apart
    from its named outputs" is enforced here and provable by the selftest's AST
    walk rather than asserted in a comment. A dashboard that repaired,
    normalised or wrote back to a source would be a second source of truth,
    which is the one thing it must never become.

    WRITABLE IS FOUR NAMES AND A BARE RUN STILL WRITES TWO. The two live
    outputs are opt-in and this function is not what keeps them opt-in -
    generate() is, and the selftest counts the files a real run leaves on disk
    in both directions rather than trusting either.
    """
    if path.name not in WRITABLE:
        raise ValueError("write_artifact refuses %r: this program writes only "
                         "%s, and the last two only when asked for by name"
                         % (path.name, ", ".join(WRITABLE)))
    path.write_text(text, encoding="utf-8")
    return len(text)


def generate(model, out_dir, live_dir=None, live_page=False, emit_json=False):
    """THE ONE WRITE SEQUENCE. main() calls it and so does the selftest.

    Returns [(path, bytes)] in write order, and a (path, fault) pair is never
    returned: a refusal raises. The selftest drives THIS rather than a copy of
    it, because a second implementation of the run is exactly how a file-count
    assertion comes to describe something the tool never does.

    THE DEFAULT RUN WRITES TWO FILES. Each live output is added only by its own
    flag, and each has one fixed name, so "exactly two artifacts" stays a
    checkable sentence rather than a remembered one.
    """
    out_dir = pathlib.Path(out_dir)
    live_dir = pathlib.Path(live_dir) if live_dir else HERE
    made = []
    for name, text in ((HTML_NAME, render_html(model)),
                       (STATUS_NAME, render_status(model))):
        made.append((out_dir / name, write_artifact(out_dir / name, text)))
    if emit_json:
        doc = build_json(model)
        fault = doc_size_fault(doc)
        if fault:
            raise ValueError(fault)
        p = live_dir / LIVE_JSON_NAME
        made.append((p, write_artifact(
            p, json.dumps(doc, indent=1, sort_keys=False) + "\n")))
    if live_page:
        p = live_dir / LIVE_PAGE_NAME
        made.append((p, write_artifact(p, render_live_page())))
    return made


# ------------------------------------------------------------------ selftest

# Names that mutate a filesystem. `replace` is deliberately NOT here: at the
# AST level str.replace and Path.replace are the same word, and plain() uses
# the string one. The run-time guard covers what this cannot see, because
# write_artifact refuses any name but the two artifacts and the scope test
# below counts what a whole generation actually created on disk.
WRITE_NAMES = {"write_text", "write_bytes", "mkdir", "makedirs", "unlink",
               "rmdir", "remove", "rename", "touch", "symlink_to", "rmtree",
               "mkdtemp", "mkstemp", "system", "chmod", "open",
               # THE SECOND DOOR, ADDED 2 SEP WITH THE CHECKOUT REFRESH. A
               # `git pull --ff-only` changes the working tree without going
               # anywhere near write_artifact, so the same guard is put on the
               # only two functions allowed to start a process at all: any new
               # subprocess anywhere else in this file trips this walk.
               "run", "check_output", "check_call", "Popen"}
WRITE_ALLOWED_IN = {"write_artifact", "selftest", "_run", "run_live_harness"}

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


def tag_balance(page):
    """Unclosed and out-of-order tags. ONE IMPLEMENTATION: both page checkers
    call this rather than carrying a parser each, because the copy nobody looks
    at is the one that stops catching things."""
    import html.parser as _hp

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
    found = list(b.bad)
    if b.stack:
        found.append("never closed: " + cap(b.stack, keep=3, sep=","))
    return found


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
    found = tag_balance(page)
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
    # Checks that could NOT run here, with the reason. A skipped check
    # that prints nothing is indistinguishable from a passing one.
    unrun = []

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
    ok("open decisions counts the WAITING section of the decision queue, not "
       "the retired file", "decision-queue.md" in live["decisions"]["count"].note
       and "WAITING" in live["decisions"]["count"].note,
       live["decisions"]["count"].note)
    ok("decided reads BOTH halves of the register and says so",
       live["decisions"]["decided"].available
       and "D-record file(s)" in live["decisions"]["decided"].note
       and "RULED" in live["decisions"]["decided"].note,
       live["decisions"]["decided"].note)
    ok("every waiting card on the live queue carries a routing CLASS",
       not live["decisions"]["unclassified"],
       live["decisions"]["unclassified"])

    # SYNTHETIC QUEUE TEXT, existing nowhere, so writing a real card can never
    # break these.
    fake = ("# q\n\n## WAITING\n\n### synthetic card one\nCLASS: BLOCKING\n"
            "body\n\n### synthetic card two\nbody with no class line\n\n"
            "## RULED THIS WEEK\n\n### synthetic ruled card\nRULED.\n\n"
            "## RETIRED\n\n### synthetic retired card\n")
    sec = queue_sections(fake)
    ok("a RULED card is NOT counted as waiting",
       len(sec["WAITING"]) == 2 and len(sec["RULED THIS WEEK"]) == 1,
       {k: len(v) for k, v in sec.items()})
    ok("a card with no CLASS line is unclassified, never defaulted to FYI",
       card_class(sec["WAITING"][0]) == "BLOCKING"
       and card_class(sec["WAITING"][1]) is None,
       [card_class(c) for c in sec["WAITING"]])
    ok("a CLASS outside the four is reported as UNKNOWN, never folded",
       card_class({"body": ["CLASS: MARINATING"]}) == "UNKNOWN:MARINATING",
       card_class({"body": ["CLASS: MARINATING"]}))
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

    # ------------------------------------------------------------------ live
    # C. THE LIVE DOCUMENT AND THE LIVE PAGE, accepting case first again: the
    # live repository's own model must serialise, and the page rendered here
    # must carry none of it.
    print("\nC. the live document and the live page, ACCEPTING CASE FIRST")
    doc = build_json(live)
    ok("the live document round-trips as strict JSON (%d key(s))" % len(doc),
       json.loads(json.dumps(doc, allow_nan=False)) == doc)
    ok("it names its schema so a page can refuse a shape it cannot read",
       doc["schema"] == LIVE_SCHEMA, doc.get("schema"))
    ok("its stamp carries an OFFSET, so no browser can read it in the wrong "
       "zone (%s)" % doc["generatedAt"],
       bool(re.search(r"(\+|-)\d{2}:\d{2}$|Z$", doc["generatedAt"])),
       doc["generatedAt"])
    ok("and an epoch integer beside it, which is what the age is computed "
       "from (%d)" % doc["generatedAtEpochMs"],
       isinstance(doc["generatedAtEpochMs"], int)
       and abs(doc["generatedAtEpochMs"] / 1000.0
               - aware(live["generated"]).timestamp()) < 1.0,
       doc["generatedAtEpochMs"])
    # THE REJECTING HALF OF THE SAME IDEA. A naive timestamp is the fault:
    # a browser reads it as ITS OWN local time, so a stopped feed can read as
    # fresh for exactly the offset between the two clocks.
    naive = datetime.datetime(2026, 9, 1, 12, 0, 0)
    ok("a naive timestamp has no offset, which is the fault aware() exists for",
       not re.search(r"(\+|-)\d{2}:\d{2}$", naive.isoformat()), naive.isoformat())
    ok("and aware() gives it one", bool(re.search(
        r"(\+|-)\d{2}:\d{2}$", aware(naive).isoformat())), aware(naive).isoformat())

    # ONE COMPUTATION, THREE RENDERINGS. Not asserted about the code: checked
    # value by value, because "the JSON and the HTML cannot disagree" is only
    # true while nothing has grown a second parser.
    by_label = {r["label"]: r for r in doc["readings"]}
    drift = []
    for r in all_readings(live):
        j = by_label.get(r.label)
        if not j or j["text"] != r.text or j["note"] != r.note:
            drift.append(r.label)
        elif r.text not in status:
            drift.append(r.label + " (absent from STATUS.md)")
    ok("every one of the %d reading(s) is identical in the document and the "
       "markdown" % len(all_readings(live)), not drift, drift)
    ok("the document carries the same %d gate pill(s) as the page"
       % len(doc["gates"]["pills"]),
       len(doc["gates"]["pills"]) == len(live["gates"]["pills"]))

    n_doc = doc_bytes(doc)
    ok("the document fits the store's per-document cap (%d bytes compact, "
       "%.1f%% of %d)" % (n_doc, 100.0 * n_doc / DOC_BYTE_CAP, DOC_BYTE_CAP),
       doc_size_fault(doc) is None, doc_size_fault(doc))
    big = dict(doc)
    big["padding"] = "y" * (DOC_BYTE_CAP + 10)
    ok("and an over-cap document is REFUSED rather than written",
       doc_size_fault(big) is not None and "cap" in (doc_size_fault(big) or ""),
       doc_size_fault(big))

    live_page = render_live_page()
    # The forbidden set is the live repository's own readings. `text` is not
    # used for unavailable ones: their text is the words nothing-measured,
    # which the page prints legitimately as its empty state.
    forbidden = []
    for r in all_readings(live):
        if r.available:
            forbidden.append(str(r.value))
        forbidden += [r.derivation, r.denominator or ""]
    forbidden += [p[0] for p in live["gates"]["pills"]]
    forbidden += [r["name"] for r in live["inflight"]]
    forbidden += list(live["decisions"]["items"])
    lfaults = live_page_faults(live_page, forbidden)
    ok("THE LIVE PAGE CARRIES NO READING AT ALL: %d candidate string(s) from "
       "today's repo, none of them in its bytes" % len(forbidden), not lfaults,
       lfaults)
    ok("it opens with a title and a style block and carries no host skeleton "
       "tag", live_page.startswith("<title>")
       and not re.search(r"<(!doctype|html|head|body)\b", live_page, re.I))
    ok("it reaches the store the one documented way: claude.use(\"db\")",
       'claude.use("db")' in live_page)
    ok("and never reads window.claude.db, which the contract says is undefined",
       not re.search(r"claude\s*\.\s*db\b", live_page))
    ok("it SUBSCRIBES rather than reading once (onSnapshot)",
       "onSnapshot" in live_page)
    ok("it re-times the age on a clock too, so a stopped feed goes on ageing",
       "setInterval" in live_page and "paintAge" in live_page)
    ok("an explicit viewer theme beats the OS setting ([data-theme] after the "
       "media query)",
       live_page.index('[data-theme="dark"]') > live_page.index(
           "prefers-color-scheme"))
    ok("the same two palettes, written once and used twice each",
       live_page.count(LIGHT_VARS) == 2 and live_page.count(DARK_VARS) == 2,
       (live_page.count(LIGHT_VARS), live_page.count(DARK_VARS)))
    lpos = [live_page.find(s) for s in SECTIONS]
    ok("the live page carries all %d sections in the specified order"
       % len(SECTIONS), all(p >= 0 for p in lpos) and lpos == sorted(lpos), lpos)
    ok("db unavailable says so plainly and shows nothing",
       LIVE_TEXT["noDbTitle"] in live_page and LIVE_TEXT["noDbWhy"] in live_page)
    ok("the empty store says the feed has never been written and names what "
       "would write it", LIVE_TEXT["emptyTitle"] in live_page
       and "--emit-json" in live_page and LIVE_DOC_PATH in live_page)
    ok("a dead subscription says the numbers are frozen",
       LIVE_TEXT["deadTitle"] in live_page)
    ok("a document with no write time refuses to claim an age",
       LIVE_TEXT["noStampTitle"] in live_page)
    ok("a stamp ahead of the browser's clock is called out, not printed as "
       "just now", LIVE_TEXT["futureWarn"] in live_page
       and "IN THE FUTURE" in live_page)
    ok("no em dash in the live page or the live document", dash not in live_page
       and dash not in json.dumps(doc))

    print("\nD. the live page's rejecting cases, all synthetic")
    baked = live_page.replace("</footer>", "queued: 8 tasks</footer>")
    bf = live_page_faults(baked, ["queued: 8 tasks"])
    ok("A BAKED READING IS CAUGHT, which is the whole point of the page",
       any("BAKED" in f for f in bf), bf)
    ok("and the same page WITHOUT it is accepted, so the check is not simply "
       "refusing everything", not live_page_faults(live_page, ["queued: 8 tasks"]))
    snapshot = live_page.replace("onSnapshot", "getOnce")
    ok("a page that reads once instead of subscribing is caught",
       any("snapshot again" in f for f in live_page_faults(snapshot)),
       live_page_faults(snapshot))
    memberbug = live_page.replace('window.claude.use("db")', "window.claude.db")
    ok("a page reading window.claude.db is caught",
       any("undefined at every moment" in f
           for f in live_page_faults(memberbug)))
    skeleton = "<!doctype html><html><body>" + live_page + "</body></html>"
    ok("a page carrying the host's own skeleton tags is caught",
       len([f for f in live_page_faults(skeleton) if "host also emits" in f]) >= 3,
       live_page_faults(skeleton))
    ok("and a page with no script at all is caught",
       any("no script at all" in f for f in live_page_faults("<title>x</title>")))

    print("\nE. the write scope, in both directions")
    live_out = pathlib.Path(tempfile.mkdtemp(prefix="dash-live-"))
    made = generate(blank, live_out, live_out)
    ok("a run with NO flags still writes exactly the two artifacts",
       sorted(p.name for p in live_out.iterdir()) == sorted(ARTIFACTS),
       [p.name for p in live_out.iterdir()])
    both = pathlib.Path(tempfile.mkdtemp(prefix="dash-both-"))
    made = generate(live, both, both, live_page=True, emit_json=True)
    ok("and a run with both flags writes those two plus the two named live "
       "outputs, and nothing else",
       sorted(p.name for p in both.iterdir()) == sorted(WRITABLE),
       [p.name for p in both.iterdir()])
    ok("generate() reports every file it wrote with its size (%d)" % len(made),
       len(made) == 4 and all(n > 0 for _, n in made), made)
    try:
        write_artifact(both / "notes.txt", "x")
        ok("write_artifact still refuses a name outside the four", False,
           "it accepted one")
    except ValueError as e:
        ok("write_artifact still refuses a name outside the four",
           "refuses" in str(e))

    print("\nF. the page's own script, RUN, through every state it can be in")
    hdir = pathlib.Path(tempfile.mkdtemp(prefix="dash-node-"))
    (hdir / "harness.js").write_text(LIVE_HARNESS_JS, encoding="utf-8")
    (hdir / "page.html").write_text(live_page, encoding="utf-8")
    (hdir / "doc.json").write_text(json.dumps(doc), encoding="utf-8")
    res, why_not = run_live_harness(hdir / "harness.js", hdir / "page.html",
                                    hdir / "doc.json")
    if res is None:
        unrun.append("the %d live-page state(s) the node harness drives: %s"
                     % (12, why_not))
        print("  NOT MEASURED  the live page's script did not run here: %s"
              % why_not)
    else:
        threw = [k for k, v in res.items() if v.startswith("THREW")]
        ok("the script runs without throwing in any of the %d states"
           % len(res), not threw, [res[k][:200] for k in threw])
        # THE ACCEPTING CASE FIRST, and it is the one that matters: with a
        # document in the store the page must actually PRINT the numbers.
        sample = [r.text for r in all_readings(live) if r.available
                  and len(str(r.text)) >= 3][:6]
        shown = [t for t in sample if t in res.get("fresh", "")]
        ok("with a document in the store the page renders the readings (%d of "
           "%d sampled found in the DOM it built)" % (len(shown), len(sample)),
           len(shown) == len(sample), [t for t in sample if t not in shown])
        ok("and the gate pills come from the document, not from the page",
           all(p["name"] in res.get("fresh", "")
               for p in doc["gates"]["pills"][:5]))
        ok("a fresh document reads Live, with the stamp and the age beside it",
           "Live" in res["fresh"] and doc["generatedAtText"] in res["fresh"]
           and "min ago" in res["fresh"], res["fresh"][:200])
        ok("an hour-old document reads FEED STOPPED", "FEED STOPPED"
           in res["stale"] and "FEED STOPPED" not in res["fresh"],
           res["stale"][:200])
        ok("a cached delivery says it is not yet server-definitive",
           LIVE_TEXT["cachedNote"] in res["cached"])
        ok("no db means the words, no numbers, and no empty panels",
           LIVE_TEXT["noDbTitle"] in res["noDb"]
           and not [t for t in sample if t in res["noDb"]],
           [t for t in sample if t in res["noDb"]])
        ok("a rejected use() lands in the same place rather than hanging",
           LIVE_TEXT["noDbTitle"] in res["useThrows"])
        ok("no host at all says so plainly",
           LIVE_TEXT["noHostTitle"] in res["noHost"])
        ok("an empty store names the path and the command that would fill it",
           LIVE_TEXT["emptyTitle"] in res["empty"]
           and LIVE_DOC_PATH in res["empty"] and "--emit-json" in res["empty"])
        ok("a document this page cannot read is REFUSED, not rendered blank",
           LIVE_TEXT["schemaTitle"] in res["wrongSchema"]
           and not [t for t in sample if t in res["wrongSchema"]])
        ok("a stamp in the future is called out rather than read as just now",
           "IN THE FUTURE" in res["future"], res["future"][:200])
        ok("a document with no stamp refuses to claim an age",
           LIVE_TEXT["noStampTitle"] in res["noStamp"])
        # TWO WAYS A SUBSCRIPTION DIES, AND THEY LOOK NOTHING ALIKE. Dying
        # before any document arrived leaves an empty page, which is easy.
        # Dying AFTER one arrived leaves the numbers sitting on screen with
        # nothing behind them, which is this whole page's failure mode: it is
        # the snapshot fault, reached at run time instead of at publish time.
        # The first version of this test asserted only the cold case and
        # called it covered.
        ok("a terminal error before any document says so and shows no numbers",
           LIVE_TEXT["deadTitle"] in res["deadCold"]
           and "revoked" in res["deadCold"]
           and not [t for t in sample if t in res["deadCold"]],
           res["deadCold"][:200])
        ok("a terminal error AFTER a document keeps the numbers and marks the "
           "feed FEED DEAD, so a frozen page cannot read as a live one",
           "FEED DEAD" in res["deadAfterDoc"]
           and LIVE_TEXT["deadTitle"] in res["deadAfterDoc"]
           and "revoked" in res["deadAfterDoc"]
           and len([t for t in sample if t in res["deadAfterDoc"]]) == len(sample)
           and ">Live</b>" not in res["deadAfterDoc"],
           res["deadAfterDoc"][:300])

    # THE LOCAL PAGE MUST NOT HAVE MOVED. The staleness numbers were pulled out
    # into constants so the live page could share the rule; that is exactly the
    # kind of refactor that changes an output by one byte and nobody notices.
    ok("the local page's staleness sentence is unchanged, word for word",
       "older than the 15 minute regeneration interval" in page
       and "if(m>20)" in page)
    ok("and the local page still carries no [data-theme] rules, because it was "
       "not restyled", "[data-theme=" not in page)

    # THE CHECKOUT'S AGE. Two fixtures the queue item asks for by name, plus
    # the two failures that must never render as a zero. Every one of them is a
    # REAL clone against a REAL origin made here in a temp directory: the thing
    # under test is what git actually does with --ff-only, and a fake would be
    # testing my idea of it. No network: the origin is a directory.
    print("\nG. the checkout's age, ACCEPTING CASE FIRST (a clone level with "
          "its origin)")
    rcv, gver = _run(["git", "--version"], None, 30)
    if rcv != 0:
        unrun.append("every checkout-age fixture: %s, so no clone could be "
                     "made here and neither case ran" % gver)
    else:
        def gitc(where, *args):
            """git in `where`, with an identity, so a commit cannot stop to ask
            for one on a machine that has no global config."""
            return _run(["git", "-C", str(where),
                         "-c", "user.name=dashboard-selftest",
                         "-c", "user.email=selftest@local",
                         "-c", "commit.gpgsign=false"] + list(args), None, 60)

        def commit_in(where, name, body):
            (where / name).write_text(body, encoding="utf-8")
            gitc(where, "add", name)
            return gitc(where, "commit", "-q", "-m", "add " + name)

        def clone_fixture(tag):
            """(root, origin, clone), the clone level with the origin."""
            root = pathlib.Path(tempfile.mkdtemp(prefix="dash-git-%s-" % tag))
            origin = root / "origin"
            origin.mkdir()
            _run(["git", "-c", "init.defaultBranch=main", "init", "-q",
                  str(origin)], None, 60)
            commit_in(origin, "one.txt", "first\n")
            _run(["git", "clone", "-q", str(origin), str(root / "clone")],
                 None, 90)
            return root, origin, root / "clone"

        stamp = datetime.datetime(2026, 9, 2, 9, 0, 0)
        root, origin, clone = clone_fixture("level")
        level = probe_checkout(clone, stamp, running=False)
        rlevel = checkout_reading(level)
        ok("ACCEPTING: a clone level with its origin MEASURES as level, and 0 "
           "behind is a measurement rather than a shrug (%s)" % rlevel.text,
           rlevel.available and "level with origin/" in str(rlevel.value)
           and "0 commit(s) behind" in str(rlevel.value)
           and bool(rlevel.denominator),
           "%s | %s" % (rlevel.text, rlevel.note))
        ok("and it moved nothing: HEAD before and after are the same commit",
           level["before"] == level["after"] and level["pulled"] == 0,
           "%s -> %s" % (level["before"], level["after"]))

        # REJECTING, in the sense that matters here: a checkout that IS behind
        # must not read as current. It must see the gap AND close it, because
        # closing it with no click is the whole deliverable.
        commit_in(origin, "two.txt", "second\n")
        behind = probe_checkout(clone, stamp, running=False)
        rbehind = checkout_reading(behind)
        ok("REJECTING: a clone deliberately put 1 commit behind SEES the gap "
           "(behind before the pull: %s)" % behind["behindBefore"],
           behind["behindBefore"] == 1, behind)
        ok("and the fast-forward closes it, which is the deliverable: the "
           "files the page then reads are the ones origin has",
           behind["pulled"] == 1 and behind["behind"] == 0
           and (clone / "two.txt").exists()
           and rbehind.available and "level with origin/" in str(rbehind.value),
           "%s | %s" % (rbehind.text, rbehind.note))
        ok("and the derivation names the exact command that moved the tree",
           "git pull --ff-only origin main" in rbehind.note
           and "advanced this clone by 1 commit(s)" in rbehind.note,
           rbehind.note)

        # A REFUSED FAST-FORWARD IS REPORTED, NEVER RESOLVED. This is the
        # branch the 26 Aug incident is about: the clone holds a commit origin
        # does not, so a bare `git pull` would MERGE here. --ff-only refuses.
        r2, o2, c2 = clone_fixture("diverged")
        commit_in(o2, "theirs.txt", "theirs\n")
        commit_in(c2, "mine.txt", "mine\n")
        head_before = _git(c2, ["rev-parse", "HEAD"])[1].strip()
        div = probe_checkout(c2, stamp, running=False)
        rdiv = checkout_reading(div)
        head_after = _git(c2, ["rev-parse", "HEAD"])[1].strip()
        ok("a refused fast-forward is still a MEASUREMENT of how far behind "
           "this clone is (%s)" % rdiv.text,
           rdiv.available and "1 commit(s) behind origin/main" == str(rdiv.value),
           "%s | %s" % (rdiv.text, rdiv.note))
        ok("and it says REFUSED, and says it is never resolved unattended",
           div["ffRefused"] is True and "REFUSED" in rdiv.note
           and "never resolved" in rdiv.note, rdiv.note)
        ok("and it changed NOTHING: same HEAD, no merge left half-finished, "
           "no local file lost",
           head_before == head_after and not (c2 / ".git" / "MERGE_HEAD").exists()
           and (c2 / "mine.txt").exists() and not (c2 / "theirs.txt").exists(),
           "%s -> %s" % (head_before[:12], head_after[:12]))

        # A FETCH THAT CANNOT REACH ITS ORIGIN. No network on the machine, a
        # remote that has moved, a credential prompt refused by
        # GIT_TERMINAL_PROMPT: they all arrive here, and the one thing none of
        # them may print is 0.
        _git(clone, ["remote", "set-url", "origin", str(root / "gone")])
        gone_head = _git(clone, ["rev-parse", "HEAD"])[1].strip()
        gone = probe_checkout(clone, stamp, running=False)
        rgone = checkout_reading(gone)
        ok("a fetch that fails is UNAVAILABLE with git's own reason, and "
           "carries no number at all",
           not rgone.available and rgone.value is None
           and "the fetch failed" in (rgone.reason or "")
           and "0" not in rgone.text, "%s | %s" % (rgone.text, rgone.reason))
        ok("and a failed fetch moves nothing either",
           gone_head == _git(clone, ["rev-parse", "HEAD"])[1].strip())

        # THE TWO GATES, PURE, BOTH DIRECTIONS. ledger-pc is Jafar's PC and
        # also the self-hosted runner, so the question "could this pull move
        # files under a running job" is answered by code and not by a comment.
        may_f, may_p, hold = checkout_plan(
            "C:/actions-runner-ledger/_work/wc26-picks/wc26-picks", False)
        ok("a checkout inside the runner's _work tree gets NO git at all, not "
           "even a fetch", not may_f and not may_p and "held:" in (hold or ""),
           hold)
        may_f, may_p, hold = checkout_plan("/home/jafar/wc26-picks", True)
        ok("a build running on this PC holds the PULL but still allows the "
           "FETCH, so the number stays measured while the tree stays still",
           may_f and not may_p
           and (hold or "").startswith("held: a build is running"), hold)
        may_f, may_p, hold = checkout_plan("/home/jafar/wc26-picks", None)
        ok("and an ordinary clone with no job running may do both",
           may_f and may_p and hold is None, hold)
        ok("the repo this selftest is running in is NOT a runner work tree, "
           "which is why the live page is allowed to refresh itself",
           runner_work_tree(repo) is None, runner_work_tree(repo))
        held = checkout_reading({"hold": "held: a build is running on this PC",
                                 "behind": None, "branch": "main"})
        ok("a held refresh renders as a Reading with its reason, not as "
           "silence and not as zero",
           not held.available and "a build is running" in (held.reason or "")
           and "0" not in held.text, held.text + " | " + str(held.reason))

    unrun.append("the live %s probe: this container is %s, not Windows, so "
                 "build_running() returned None here and only the PURE gate "
                 "above was exercised" % (RUNNER_WORKER_PROCESS, sys.platform))

    # THE LAUNCHER AND THIS PROGRAM MUST AGREE, and nothing on this machine can
    # run the launcher: no Windows, no cmd. What CAN be checked here is that
    # every string the .bat hands over is one this program accepts, because a
    # flag renamed on one side of that line fails on his PC and nowhere else.
    bat = read(repo / "open-dashboard.bat") or ""
    # EVERY MODE WORD THE LAUNCHER CAN HAND OVER, against the ones this
    # program accepts. A flag renamed on one side of that line fails on his PC
    # and nowhere else, so the agreement is checked here where it can run.
    accepts = ["refresh"] + sorted(CHECKOUT_SKIPPED)
    found = re.findall(r'set\s+"CHECKOUT=([^"]+)"', bat)
    # A cmd variable passed straight through (%~4) is not a word to check, it
    # is the OUTER invocation's word arriving; it is counted here rather than
    # dropped, so the denominator says how much of the file this check saw.
    handed = [h for h in found if not h.startswith("%")]
    passed_through = len(found) - len(handed)
    ok("the launcher passes --checkout, and all %d literal mode word(s) it "
       "can hand over are ones this program accepts (%s; %d pass-through(s) "
       "of an outer word, which is one of these)"
       % (len(handed), ", ".join(handed) or "none found", passed_through),
       "--checkout" in bat and handed
       and all(h in accepts for h in handed),
       "%s against %s" % (handed, accepts))
    ok("and one of them is the refresh, so the scheduled task actually asks "
       "for the pull", "refresh" in handed, handed)
    ok("and it names the skip this program knows for a launcher that could "
       "not stage a working copy",
       "skip-no-working-copy" in handed, handed)
    ok("and sets both 26 Aug editor guards, which is what "
       "tools/lint-bat-editor.py asks of any .bat that reaches git",
       "GIT_EDITOR=true" in bat and "GIT_MERGE_AUTOEDIT=no" in bat)
    # COMMENTS ARE NOT COMMANDS, and this file's header discusses the bare
    # pull it must never run. Strip REM lines before looking, or the check
    # fails on the sentence explaining why it exists.
    bat_cmds = "\n".join(l for l in bat.splitlines()
                         if not l.strip().upper().startswith("REM"))
    ok("and never RUNS a bare `git pull`, which is the command that made the "
       "merge nobody was watching (%d command line(s) read, %d comment line(s) "
       "skipped)" % (len(bat_cmds.splitlines()),
                     len(bat.splitlines()) - len(bat_cmds.splitlines())),
       not re.search(r"git\s+pull(?!\s+--ff-only)", bat_cmds),
       [l for l in bat_cmds.splitlines() if "git pull" in l])

    print("\ndashboard selftest: %d passed, %d failed, %d check(s) not run "
          "here" % (passed, len(failed), len(unrun)))
    for f in failed:
        print("  FAILED: %s" % f)
    for u in unrun:
        print("  NOT RUN: %s" % u)
    print("  NOT COVERED HERE, and it is the half that runs elsewhere: "
          "open-dashboard.bat and the Windows scheduled task never execute in "
          "this container (no Windows, no cmd), and the SessionStart hook and "
          "the night runner's per-iteration call are first-run questions. "
          "Their accepting case is the first run on the machine that has them.")
    print("  AND THE LIVE PAGE'S PIXELS ARE UNVERIFIED. Section F runs its "
          "SCRIPT against a DOM shim in node, which settles what it decides "
          "and what it writes; nothing here renders it, so layout, contrast, "
          "the [data-theme] cascade against the host's real attribute, and "
          "the real db capability are all first-load questions on the "
          "published artifact.")
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
    ap.add_argument("--checkout", default="skip-not-asked",
                    choices=["refresh"] + sorted(CHECKOUT_SKIPPED),
                    help="refresh: fetch and `git pull --ff-only` FIRST, then "
                         "build from the files that brought in, and print how "
                         "far behind origin this clone is. The skip-* values "
                         "are the launcher naming WHY it did not ask; the "
                         "sentence for each lives here, not in the .bat")
    ap.add_argument("--now", default=None,
                    help="ISO timestamp to treat as now (tests and reruns)")
    ap.add_argument("--emit-json", action="store_true",
                    help="ALSO write %s: the same readings as one JSON "
                         "document, the shape the live page reads" % LIVE_JSON_NAME)
    ap.add_argument("--emit-live-page", action="store_true",
                    help="ALSO write %s: the page that renders from the "
                         "document store, with no numbers in it" % LIVE_PAGE_NAME)
    ap.add_argument("--live-dir", default=None,
                    help="where those two opt-in outputs go (default: %s)" % HERE)
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
    # BEFORE build_model, NOT AFTER: the pull changes the files every reader
    # below is about to read. A refused fast-forward, a failed fetch and a held
    # refresh all land here as a Reading and none of them stops the rebuild:
    # the page must still be written, carrying the reason.
    if args.checkout == "refresh":
        checkout = checkout_reading(probe_checkout(repo, now, build_running()))
    else:
        checkout = Reading.unavailable(
            CHECKOUT_LABEL, CHECKOUT_SKIPPED[args.checkout], [".git"])
    # QUIET ONLY FOR THE DEFAULT SKIP, which the page states anyway. A
    # refresh, and a launcher that had to skip for a reason of its own, both
    # say so in the window that ran them.
    if args.checkout != "skip-not-asked":
        print("dashboard: %s %s (%s)"
              % (CHECKOUT_LABEL, checkout.text, checkout.note))
    model = build_model(repo, now, checkout)
    if args.show:
        print(render_status(model))
        return 0
    out = pathlib.Path(args.out_dir).resolve() if args.out_dir else repo
    live_dir = pathlib.Path(args.live_dir).resolve() if args.live_dir else HERE
    try:
        made = generate(model, out, live_dir, live_page=args.emit_live_page,
                        emit_json=args.emit_json)
    except ValueError as e:                 # the document is over the store cap
        print("REFUSING TO WRITE: %s" % e, file=sys.stderr)
        return 5
    except OSError as e:
        print("WRITE FAILED: %s" % e, file=sys.stderr)
        return 2
    unavailable = [r.label for r in all_readings(model) if not r.available]
    # EVERY ZERO SHIPS ITS DENOMINATOR, including this line's: it names how
    # many files it wrote AND how many readings it had, so a run that measured
    # nothing cannot print the same sentence as a clean one.
    print("dashboard: wrote %d file(s) [%s] from %d source(s), "
          "%d of %d reading(s) not yet applicable%s"
          % (len(made), ", ".join("%s %d bytes" % (p.name, n) for p, n in made),
             len(model["sources"]), len(unavailable), len(all_readings(model)),
             (": " + cap(unavailable, keep=3, sep=", ")) if unavailable else ""))
    if args.emit_json:
        doc = build_json(model)
        n = doc_bytes(doc)
        print("dashboard: live document %s carries %d reading(s), %d gate "
              "pill(s), %d in-flight row(s); %d bytes compact against the "
              "store's %d byte cap (%.1f%% of it). Written at %s. Write it to "
              "the store at %s."
              % (LIVE_JSON_NAME, len(doc["readings"]), len(doc["gates"]["pills"]),
                 len(doc["inflight"]["rows"]), n, DOC_BYTE_CAP,
                 100.0 * n / DOC_BYTE_CAP, doc["generatedAtText"], LIVE_DOC_PATH))
    return 0


if __name__ == "__main__":
    sys.exit(main())
