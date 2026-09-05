#!/usr/bin/env python3
"""THE MORNING BRIEF, GENERATED FROM REPO STATE. No model call, one writer.

    python3 tools/morning-brief.py                 # write production/briefs/<today>.md
    python3 tools/morning-brief.py --dry-run       # compose and print, write nothing
    python3 tools/morning-brief.py --date 2026-09-05
    python3 tools/morning-brief.py --root DIR      # read a planted tree instead
    python3 tools/morning-brief.py --selftest      # both outcomes, accepting first

WHY IT EXISTS. Jafar's standing order of 2026-09-05, item 1c: the brief is
GENERATED FROM REPO STATE BY A TOOL and pushed by the bot every morning, not
written by hand in a session. A hand-written brief costs a spawn, arrives when
the studio happens to be awake, and carries whatever the writer remembered.

IT IS THE ONE BRIEF WRITER, ruled 2026-09-05 (section 7(b) of
game-design/decision-2026-09-05-ruling-standing-order-refill-and-the-wake-half.md).
`tools/runner/run-night.ps1` used to write a mechanical fallback brief of its
own, carrying none of the register's shape, so the first night that committed
one would have put the tree in a state `producer-check --gate` refuses. That
block is gone and the night calls this program instead.

WHAT IT READS, and every number it prints names the file it came from on the
tool's own provenance lines below the message:
  - production/queue/, through tools/queue-check.py's count_queue(), which is
    the ONE queue counter in this repository (ledger/verify.py reads the same
    numbers, so the brief and the verification footer cannot disagree);
  - production/decision-queue.md, the WAITING cards;
  - production/budget.md, the newest row that is a READING, with its age;
  - .claude/agent-log.tsv, for the studio-versus-game split, classified by
    ledger/verify.py's GAME_AGENTS so the set has one definition;
  - git, for what landed since the previous brief;
  - tools/report-frame.py, for the picture, which it withholds when the last
    build measured nothing.

THE MESSAGE CARRIES NO DIGITS, AND THAT IS THE REGISTER, NOT AN OVERSIGHT.
Jafar ruled bare counts, file paths and verdict keys out of anything he reads
(tools/producer-check.py, the brief register). So every quantity in the message
is written in words, and every number with its source path is printed on this
program's own lines, where a machine reads them and the register does not
apply. `splitBasis=` therefore appears on the done line and NOWHERE in the
message, which is section 6 of the same ruling.

IT SELF-CHECKS BEFORE IT WRITES. The composed text goes through
producer-check's brief register in this process, and a composition with any
finding is REFUSED rather than written: the one brief writer must never be the
thing that reddens the gate. A source it cannot read is also a refusal, named,
rather than a brief with a hole in it.

EXIT CODES, distinct per outcome. 0 written (or composed under --dry-run). 1
REFUSED: a source could not be read, or the composed brief fails its own
register; nothing was written. 2 nothing measured: no queue directory under the
root given. 3 the selftest failed. 4 a tool this one is built on could not be
imported, which is not a pass.
"""
import argparse
import datetime
import importlib.util
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent


def _load(path, name):
    try:
        spec = importlib.util.spec_from_file_location(name, str(path))
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:                                            # noqa: BLE001
        return None


# ONE IMPLEMENTATION PER IDEA, three times over: the register, the queue
# counter and the game-agent set all already exist and are imported, never
# re-typed. A second copy is the site nobody looks at when the first is fixed.
pc = _load(HERE / "producer-check.py", "producer_check")
qc = _load(HERE / "queue-check.py", "queue_check")
vf = _load(REPO / "ledger" / "verify.py", "ledger_verify")
_missing = [n for n, m in (("tools/producer-check.py", pc),
                           ("tools/queue-check.py", qc),
                           ("ledger/verify.py", vf)) if m is None]
if _missing:
    sys.stderr.write("morning-brief: could not import %s; refusing to write a "
                     "brief with no register, no counter or no agent set "
                     "behind it\n" % ", ".join(_missing))
    sys.exit(4)

BRIEFS_REL = "production/briefs"
DECISIONS_REL = "production/decision-queue.md"
BUDGET_REL = "production/budget.md"
QUEUE_REL = qc.QUEUE_REL
AGENT_LOG_REL = vf.DIRECTOR_LOG

# WHERE A LINK MAY POINT. The register's link floor accepts github.com only
# (there is no hosted console yet), so the brief's evidence links are blob URLs
# on the work branch. Checked against the origin remote when git can read it;
# a link to the wrong repository is evidence pointing nowhere.
LINK_OWNER_REPO = "jsab258/wc26-picks"
LINK_BRANCH = "claude/game-dev-ai-automation-2h67ix"
LINK_BASE = "https://github.com/%s/blob/%s" % (LINK_OWNER_REPO, LINK_BRANCH)

# THE BUDGET STALENESS BOUND, and it is Jafar's, not this program's:
# production/budget.md, stop condition 2, "with no reading newer than 48 hours,
# do only work that costs no model time". The table's granularity is a DATE,
# not an instant, so 48 hours is read as two days and the comparison is the
# conservative one: a row dated two days back is between 24 and 72 hours old
# and is called stale. The age in days is printed beside the verdict.
BUDGET_STALE_DAYS = 2

ONES = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen")
TENS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
        "eighty", "ninety")


def in_words(n):
    """A count as words, because the brief register bans bare quantities and
    Jafar ruled it. 0 reads as "no", which is a zero WITH its denominator in
    the sentence around it, never a bare nought."""
    n = int(n)
    if n < 0:
        return "an unreadable number of"
    if n < 20:
        return ONES[n]
    if n < 100:
        t, o = divmod(n, 10)
        return TENS[t] + ("-" + ONES[o] if o else "")
    if n < 1000:
        h, rest = divmod(n, 100)
        return ONES[h] + " hundred" + (" and " + in_words(rest) if rest else "")
    return "over nine hundred"


def plural(n, one, many):
    return one if int(n) == 1 else many


# ------------------------------------------------------------------ the reads
# Each returns (value-dict, ok, why). A source that cannot be READ is a
# refusal; a source that read cleanly and found nothing prints the words
# "nothing measured" and is NOT a refusal, because those are different facts.

def read_queue(root):
    c = qc.count_queue(root)
    if not c["exists"]:
        return c, False, "no %s/ under %s" % (QUEUE_REL, root)
    return c, True, "%s/" % QUEUE_REL


def read_cards(root):
    """The WAITING cards in the decision queue: how many, and the top one's
    heading. Counted under the `## WAITING` section only; a ruled card has left
    it. The heading is used only if it survives the register on its own."""
    p = pathlib.Path(root) / DECISIONS_REL
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:                                       # noqa: BLE001
        return {}, False, "%s could not be read (%s)" % (DECISIONS_REL,
                                                         type(e).__name__)
    body, keep = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            keep = line.strip().upper().startswith("## WAITING")
            continue
        if keep:
            body.append(line)
    heads = [l.lstrip("# ").strip() for l in body if l.startswith("### ")]
    return ({"waiting": len(heads), "top": heads[0] if heads else "",
             "scanned": len([l for l in text.splitlines()
                             if l.startswith("### ")])},
            True, DECISIONS_REL)


BUDGET_ROW_RE = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|([^|]*)\|([^|]*)\|"
                           r"([^|]*)\|")
PCT_RE = re.compile(r"(\d{1,3})\s*%")


def read_budget(root, today):
    """The newest row of production/budget.md THAT IS A READING, with its age.

    LAST-WINS over the table in file order, which is chronological. A row with
    no percentage on either meter is NOT a reading and the file says so in its
    own words (the limit-event rows of 3 and 5 September); counting one would
    be inventing a measurement. The governing meter is the HIGHER of the two,
    ruled 2026-09-03.
    """
    p = pathlib.Path(root) / BUDGET_REL
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:                                       # noqa: BLE001
        return {}, False, "%s could not be read (%s)" % (BUDGET_REL,
                                                         type(e).__name__)
    rows, skipped = [], 0
    for line in text.splitlines():
        m = BUDGET_ROW_RE.match(line.strip())
        if not m:
            continue
        pcts = [int(x.group(1)) for col in (m.group(3), m.group(4))
                for x in [PCT_RE.search(col)] if x]
        if not pcts:
            skipped += 1
            continue
        rows.append((m.group(1), max(pcts)))
    if not rows:
        return ({"reading": None, "rows": 0, "not_readings": skipped,
                 "age_days": None, "stale": True}, True, BUDGET_REL)
    day, pct = rows[-1]
    age = (today - datetime.date.fromisoformat(day)).days
    return ({"reading": pct, "day": day, "age_days": age, "rows": len(rows),
             "not_readings": skipped, "stale": age >= BUDGET_STALE_DAYS},
            True, BUDGET_REL)


def read_split(root, since_day, until_day):
    """The studio-versus-game split, COUNTED IN SESSIONS over one named window.

    A session here is one row of .claude/agent-log.tsv, which is one spawn. It
    is NOT points: production/budget.md line 87 rules that the turns-to-points
    conversion is unmeasured and that no per-tier points figure enters that
    file until two paired readings exist (queue 076). So the message says
    sessions and says why, and this program never multiplies.

    CUMULATIVE over the window, not a peak and not a rate.
    """
    p = pathlib.Path(root) / AGENT_LOG_REL
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:                                       # noqa: BLE001
        return {}, False, "%s could not be read (%s)" % (AGENT_LOG_REL,
                                                         type(e).__name__)
    game, studio, unparsed = 0, 0, 0
    for line in text.splitlines():
        if not line.strip():
            continue
        cols = line.split("\t")
        if cols[0].strip() == "when":
            continue
        day = cols[0].strip()[:10]
        agent = cols[1].strip().lower() if len(cols) > 1 else ""
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
            unparsed += 1
            continue
        if not (since_day <= day <= until_day):
            continue
        if agent in vf.GAME_AGENTS:
            game += 1
        else:
            studio += 1
    return ({"game": game, "studio": studio, "total": game + studio,
             "unparsed": unparsed, "since": since_day, "until": until_day},
            True, AGENT_LOG_REL)


def read_landed(root, since_day):
    """How many changes landed since the previous brief.

    Git is a MEASURED-ABSENT source, not a required one: a tree that is not a
    repository (every planted fixture) yields the words "nothing measured"
    rather than a refusal, because "I could not look" and "I looked and the
    file is broken" are different facts and only the second is a hole.
    """
    try:
        p = subprocess.run(["git", "-C", str(root), "log",
                            "--since=%sT00:00:00Z" % since_day,
                            "--format=%H"],
                           capture_output=True, text=True, timeout=30)
    except Exception as e:                                       # noqa: BLE001
        return {"n": None, "why": type(e).__name__}, True, "git(unavailable)"
    if p.returncode != 0:
        return {"n": None, "why": "not a git checkout"}, True, "git(no-history)"
    return ({"n": len([l for l in p.stdout.split() if l.strip()]),
             "why": ""}, True, "git-log-since-%s" % since_day)


def read_frame(root):
    """The picture, or the reason there is none.

    tools/report-frame.py withholds a frame when the last build measured
    nothing, and that withholding is the whole point of it: on 4 August a build
    committed six stills it could not have rendered. Its lookup reads the live
    checkout, so under a planted root this reports withheld with that reason
    rather than reaching into the real tree and reporting somebody else's
    picture as this tree's.
    """
    if pathlib.Path(root).resolve() != REPO:
        return ({"rel": None,
                 "why": "the frame lookup reads the live checkout only"},
                True, "tools/report-frame.py(not-run)")
    try:
        p = subprocess.run(["python3", str(HERE / "report-frame.py")],
                           capture_output=True, text=True, timeout=60)
    except Exception as e:                                       # noqa: BLE001
        return ({"rel": None, "why": type(e).__name__}, True,
                "tools/report-frame.py(unavailable)")
    if p.returncode != 0:
        return ({"rel": None, "why": "the last build measured nothing"}, True,
                "tools/report-frame.py(withheld)")
    m = re.search(r"^NOW\s+(\S+)", p.stdout, re.M)
    if not m:
        return ({"rel": None, "why": "no frame line in the lookup's output"},
                True, "tools/report-frame.py(no-frame)")
    try:
        rel = pathlib.Path(m.group(1)).resolve().relative_to(REPO).as_posix()
    except ValueError:
        return ({"rel": None, "why": "the frame sits outside the checkout"},
                True, "tools/report-frame.py(outside)")
    return {"rel": rel, "why": ""}, True, "tools/report-frame.py"


def previous_brief_day(root, today):
    """The ISO date of the newest dated brief before today, or None.

    It is the left edge of every window this brief reports, so it is read once
    and named once: two windows with one name is the fault this project keeps
    paying for."""
    d = pathlib.Path(root) / BRIEFS_REL
    days = []
    if d.is_dir():
        for p in d.glob("*.md"):
            m = re.match(r"^(\d{4}-\d{2}-\d{2})", p.name)
            if m and m.group(1) < today.isoformat():
                days.append(m.group(1))
    return max(days) if days else None


# --------------------------------------------------------------- composition

def compose(root, today):
    """(text, facts). PURE-ISH: reads, writes nothing, returns the message and
    every number behind it with the path it was read from."""
    facts = {"sources": [], "failed": []}

    def source(name, res):
        val, ok, why = res
        facts["sources"].append((name, why, ok))
        if not ok:
            facts["failed"].append((name, why))
        return val

    prev = previous_brief_day(root, today)
    since = prev or today.isoformat()
    q = source("queue", read_queue(root))
    cards = source("cards", read_cards(root))
    budget = source("budget", read_budget(root, today))
    split = source("split", read_split(root, since, today.isoformat()))
    landed = source("landed", read_landed(root, since))
    frame = source("frame", read_frame(root))
    facts.update({"queue": q, "cards": cards, "budget": budget,
                  "split": split, "landed": landed, "frame": frame,
                  "window_since": since, "window_until": today.isoformat(),
                  "prev_brief": prev})
    if facts["failed"]:
        return None, facts

    queue_url = "%s/%s" % (LINK_BASE, QUEUE_REL)
    cards_url = "%s/%s" % (LINK_BASE, DECISIONS_REL)
    frame_url = "%s/%s" % (LINK_BASE, frame["rel"]) if frame["rel"] else None

    ready, blocked, done = q["ready"], q["blocked"], q["done"]
    lines = []
    lines.append("HEADLINE: %s queue %s ready to start this morning, and %s "
                 "blocked." % (in_words(ready).capitalize(),
                               plural(ready, "item is", "items are"),
                               in_words(blocked)))
    lines.append("")

    if landed["n"] is None:
        changed = ("Nothing measured for what landed since the previous "
                   "brief, because no history was readable here.")
    elif landed["n"] == 0:
        changed = ("Nothing landed since the previous brief.")
    else:
        changed = ("%s %s landed since the previous brief."
                   % (in_words(landed["n"]).capitalize(),
                      plural(landed["n"], "change has", "changes have")))
    changed += (" %s finished %s now sit in the done pile."
                % (in_words(done).capitalize(), plural(done, "item", "items")))
    lines.append("WHAT CHANGED: " + changed)
    if frame_url:
        lines.append("[the newest picture the studio has](%s)" % frame_url)
    else:
        lines.append("There is no new picture this morning: %s."
                     % frame["why"])
    lines.append("[the work list](%s)" % queue_url)
    lines.append("")

    if cards["waiting"]:
        needs = ("%s %s waiting for you."
                 % (in_words(cards["waiting"]).capitalize(),
                    plural(cards["waiting"], "card is", "cards are")))
        top = cards["top"]
        # THE CARD'S OWN HEADING, USED ONLY IF IT SURVIVES THE REGISTER. A
        # heading carrying a path or a bare count would fail the whole brief,
        # and a brief that refuses to write itself over somebody else's wording
        # is worse than one that says how many are waiting. Counted either way
        # on the done line.
        # THE BAN LIST ONLY, never the link floor: the floor is a property of
        # the whole message (which carries two links), and applying it to a
        # fragment would refuse every heading ever written.
        title_findings = [f for f in pc.check(top, "answer")["findings"]
                          if f.rule != "linkfloor"]
        if top and not title_findings and "?" in top:
            needs += " The first one asks: %s" % top
            facts["card_title_used"] = 1
        else:
            facts["card_title_used"] = 0
    else:
        needs = "Nothing needs you this morning."
        facts["card_title_used"] = 0
    lines.append("NEEDS YOU: " + needs)
    lines.append("[the decision queue](%s)" % cards_url)
    lines.append("")

    lines.append("NEXT VISIBLE THING: unknown until the day is planned "
                 "against your order; this brief reports state and does not "
                 "promise one.")
    lines.append("")

    if budget["reading"] is None or budget["stale"]:
        money = ("Nothing measured on the budget: no reading newer than two "
                 "days, so today's spend is unknown and an unknown budget is "
                 "not permission.")
    else:
        money = ("Your newest reading was %s percent on the meter that "
                 "governs, taken %s."
                 % (in_words(budget["reading"]),
                    "today" if budget["age_days"] == 0 else "yesterday"))
    # THE SPLIT SENTENCE. Required by the standing order over every brief, in
    # WORDS, in this section, COUNTED IN SESSIONS, with the reason it is not
    # points. producer-check --kind brief refuses a brief without it.
    money += (" %s %s went to the studio and %s to the game since the "
              "previous brief, counted in sessions and not points until the "
              "rate is measured."
              % (in_words(split["studio"]).capitalize(),
                 plural(split["studio"], "session", "sessions"),
                 in_words(split["game"])))
    lines.append("BUDGET: " + money)
    return "\n".join(lines) + "\n", facts


def brief_path(root, today):
    return pathlib.Path(root) / BRIEFS_REL / ("%s.md" % today.isoformat())


def provenance(facts):
    """Every number in this brief, with the file it was read from, one per
    line. It lives HERE and not in the message because the brief register bans
    counts and paths in anything Jafar reads; the pair still has to exist
    somewhere a reader can audit, and this is that somewhere."""
    q, b, s, l = (facts["queue"], facts["budget"], facts["split"],
                  facts["landed"])
    out = [
        "queueReady=%d %s/" % (q["ready"], QUEUE_REL),
        "queueBlocked=%d %s/" % (q["blocked"], QUEUE_REL),
        "queueDone=%d %s/done/" % (q["done"], QUEUE_REL),
        "queueWalked=%d %s/" % (q["walked"], QUEUE_REL),
        "cardsWaiting=%d/%d %s" % (facts["cards"]["waiting"],
                                   facts["cards"]["scanned"], DECISIONS_REL),
        "budgetNewestReadingPct=%s %s" % (
            b["reading"] if b["reading"] is not None else "nothing-measured",
            BUDGET_REL),
        "budgetAgeDays=%s %s" % (
            b["age_days"] if b["age_days"] is not None else "nothing-measured",
            BUDGET_REL),
        "budgetRowsThatAreReadings=%d/%d %s"
        % (b["rows"], b["rows"] + b["not_readings"], BUDGET_REL),
        "splitStudio=%d/%d %s" % (s["studio"], s["total"], AGENT_LOG_REL),
        "splitGame=%d/%d %s" % (s["game"], s["total"], AGENT_LOG_REL),
        "landed=%s git-log-since-%s"
        % (l["n"] if l["n"] is not None else "nothing-measured",
           facts["window_since"]),
    ]
    return out


def run_once(root, today, dry_run=False, write_latest=False, quiet=False):
    """Compose, self-check, write. Returns (exit code, text or None, facts)."""
    def say(*a):
        if not quiet:
            print(*a)

    text, facts = compose(root, today)
    if text is None:
        say("morning-brief: REFUSED to write. %d of %d source(s) could not be "
            "read, and a brief with a hole in it is worse than no brief:"
            % (len(facts["failed"]), len(facts["sources"])))
        for name, why in facts["failed"]:
            say("    %s: %s" % (name, why))
        say("morning-brief: REFUSED sourcesRead=%d/%d briefWritten=0/1"
            % (len(facts["sources"]) - len(facts["failed"]),
               len(facts["sources"])))
        return 1, None, facts

    # THE SELF-CHECK, in this process, against the same register the gate runs.
    # The one brief writer must never be the thing that reddens the tree.
    res = pc.check(text, "brief",
                   datetime.datetime.combine(today, datetime.time(0, 0)))
    facts["check"] = res
    if res["findings"]:
        say("morning-brief: REFUSED to write. The composed brief fails its own "
            "register, %d finding(s) over %d rule(s):"
            % (len(res["findings"]), len(res["enforced"])))
        for f in res["findings"]:
            say("    %s" % f)
        say("morning-brief: REFUSED registerFindings=%d words=%d/%d "
            "briefWritten=0/1"
            % (len(res["findings"]), res["words"], res["cap"]))
        return 1, text, facts

    p = brief_path(root, today)
    wrote_latest = 0
    if not dry_run:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        if write_latest:
            # latest.md IS A MOVING NAME ON A FROZEN LIST (queue 074). While it
            # sits in producer-check's PRE_REGISTER it must carry the exempt
            # marker, and a generated file carrying a marker that says it
            # predates the register would be a false record. So this refuses to
            # touch it and says why; the day 074 takes it off that list, this
            # starts working with no change here.
            rel = "%s/latest.md" % BRIEFS_REL
            if rel in pc.PRE_REGISTER:
                say("  latest.md NOT written: it is on the frozen "
                    "PRE_REGISTER list in tools/producer-check.py and would go "
                    "red at the gate as a listed file with no marker. Queue "
                    "074 owns that hole.")
            else:
                (pathlib.Path(root) / rel).write_text(text, encoding="utf-8")
                wrote_latest = 1

    say("morning-brief: %s" % ("composed (nothing written)" if dry_run
                               else "wrote %s" % p.relative_to(root)))
    say("  numbers and the file each was read from, one per line, because the "
        "message may carry no digits:")
    for line in provenance(facts):
        say("    " + line)
    say("  window: %s..%s (from the previous dated brief, %s)"
        % (facts["window_since"], facts["window_until"],
           facts["prev_brief"] or "none found, so the window is today only"))
    say("  sources read: %s"
        % ", ".join("%s<-%s" % (n, w) for n, w, ok in facts["sources"]))
    s = facts["split"]
    say("morning-brief: %s sourcesRead=%d/%d words=%d/%d registerFindings=0 "
        "queueReady=%d/%d queueBlocked=%d/%d queueDone=%d cardsWaiting=%d/%d "
        "splitStudio=%d/%d splitGame=%d/%d splitBasis=spawns "
        "splitSource=%s splitWindow=%s..%s budgetAgeDays=%s "
        "cardTitleUsed=%d/%d frame=%s briefWritten=%d/1 latestWritten=%d/1 "
        "generatedAt=%s"
        % ("DRY-RUN" if dry_run else "WROTE",
           len(facts["sources"]), len(facts["sources"]),
           res["words"], res["cap"],
           facts["queue"]["ready"], facts["queue"]["walked"],
           facts["queue"]["blocked"], facts["queue"]["walked"],
           facts["queue"]["done"],
           facts["cards"]["waiting"], facts["cards"]["scanned"],
           s["studio"], s["total"], s["game"], s["total"],
           AGENT_LOG_REL, facts["window_since"], facts["window_until"],
           facts["budget"]["age_days"] if facts["budget"]["age_days"]
           is not None else "nothing-measured",
           facts.get("card_title_used", 0), 1 if facts["cards"]["waiting"] else 0,
           facts["frame"]["rel"] or "withheld",
           0 if dry_run else 1, wrote_latest,
           datetime.datetime.now(datetime.timezone.utc)
           .strftime("%Y-%m-%dT%H:%M:%SZ")))
    return 0, text, facts


# ------------------------------------------------------------------ selftest

def _tree(files):
    import atexit
    import shutil
    import tempfile
    d = pathlib.Path(tempfile.mkdtemp(prefix="morning-brief-"))
    atexit.register(shutil.rmtree, str(d), True)
    for rel, text in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return d


def _fixture_files(budget_day, extra=None):
    """A planted tree: a queue, a decision queue, a budget table and an agent
    log. Synthetic to the last file; nothing here is pinned to a real asset, so
    doing the work this tool reports can never break its own test."""
    files = {
        "production/queue/README.md": "# docs\n",
        "production/queue/900-process-audit.md": qc._item("READY 2026-09-05"),
        "production/queue/001-a.md": qc._item("READY 2026-09-05"),
        "production/queue/002-b.md": qc._item("READY 2026-09-05"),
        "production/queue/003-c.md": qc._item("WAITS 2026-09-05 behind 001"),
        "production/queue/done/000-old.md": qc._item("LANDED 2026-09-01"),
        "production/decision-queue.md":
            "# cards\n\n## WAITING\n\n### Which way should the street lean?\n"
            "CLASS: DECISION\n\n## RULED\n\n### An older one\n",
        "production/budget.md":
            "| date | period | total | fable | note |\n"
            "|---|---|---|---|---|\n"
            "| 2026-09-01 | a | 34% | 41% | a reading |\n"
            "| " + budget_day + " | b | not read | not read | NOT A READING |\n"
            "| " + budget_day + " | c | 12% | 14% | a reading |\n",
        ".claude/agent-log.tsv":
            "when\tagent\n"
            "2026-09-05T01:00:00Z\tinstrument-builder\n"
            "2026-09-05T02:00:00Z\tsystems-builder\n"
            "2026-09-05T03:00:00Z\tstudio-director\n",
    }
    files.update(extra or {})
    return files


def selftest():
    """Both outcomes, ACCEPTING CASE FIRST. The live repository is the
    accepting fixture; every rejecting fixture is a planted tree."""
    passed, failed = 0, []

    def ok(name, cond, got=""):
        nonlocal passed
        if cond:
            passed += 1
            print("  ok   %s" % name)
        else:
            failed.append(name)
            print("  FAIL %s\n         got: %s" % (name, got))

    today = datetime.date(2026, 9, 5)
    print("morning-brief --selftest: ACCEPTING CASE FIRST, the live tree\n")
    text, facts = compose(REPO, today)
    ok("the live checkout composes a brief with every source read (%d of %d)"
       % (len(facts["sources"]) - len(facts["failed"]), len(facts["sources"])),
       text is not None, facts["failed"])
    if text is None:
        print("\nmorning-brief --selftest: FAILED, %d passed, %d failed"
              % (passed, len(failed)))
        return 3
    res = pc.check(text, "brief",
                   datetime.datetime.combine(today, datetime.time(0, 0)))
    ok("and it passes the brief register with no finding (%d word(s) of %d)"
       % (res["words"], res["cap"]), not res["findings"],
       [str(f) for f in res["findings"]])
    ok("its five sections are all found, in the ruled order",
       res["sections_found"] == pc.SECTIONS, res["sections_found"])
    ok("the split rule is ENFORCED in this register and found the sentence",
       "split" in res["enforced"] and not [f for f in res["findings"]
                                           if f.rule == "split"],
       res["enforced"])
    # NO DIGIT IN THE PROSE, and the URLs are scrubbed first because the link
    # floor REQUIRES them and a branch name carrying digits is not a count.
    # This is the same scrub the register itself runs before the ban list.
    prose = pc.scrub_links(text)
    ok("the message carries no `splitBasis=` and no digit outside a link",
       "splitBasis" not in prose and not re.search(r"\d", prose),
       re.findall(r"\S*\d\S*", prose)[:4])
    text2, _ = compose(REPO, today)
    ok("two composes on one checkout are byte-identical (%d bytes)"
       % len(text.encode("utf-8")), text == text2,
       "they differ")

    # THE GATE ITSELF, over a tree holding this brief. The register check above
    # is the same function the gate calls, but the gate adds the filename
    # clock and the exempt walk, and only running it proves the file this tool
    # writes can be committed.
    g = pc.gate(_tree({"production/outbox/README.md": "# docs\n",
                       "production/briefs/%s.md" % today.isoformat(): text}),
                datetime.datetime(2026, 9, 5, 12, 0), pre_register=())
    ok("the composed brief passes producer-check --gate (%d checked, %d failed)"
       % (g["checked"], len(g["failed"])),
       g["checked"] == 1 and not g["failed"], g["failed"])

    # THE OTHER HALF OF THE SPLIT GUARD, so it can tell a regression from an
    # improvement rather than passing everything: the SAME brief with the
    # sentence removed must be refused, by the split rule and by name.
    stripped = re.sub(r" [A-Za-z-]+ sessions? went to the studio.*?measured\.",
                      "", text, flags=re.S)
    rs = pc.check(stripped, "brief",
                  datetime.datetime.combine(today, datetime.time(0, 0)))
    ok("the same brief with the split sentence removed is REFUSED by the "
       "split rule", any(f.rule == "split" for f in rs["findings"]),
       [str(f) for f in rs["findings"]] or "nothing")

    print("\n  REJECTING AND NOTHING-MEASURED FIXTURES, all planted:\n")
    # ACCEPTING HALF OF THE STALENESS BOUND FIRST: a reading from today must
    # reach the message, or a bound that always says "stale" would pass the
    # rejecting case while measuring nothing.
    fresh = _tree(_fixture_files(today.isoformat()))
    code_f, tf, ff = run_once(fresh, today, dry_run=True, quiet=True)
    ok("a budget row dated today reaches the message as a reading (age %s "
       "day(s))" % ff["budget"]["age_days"],
       code_f == 0 and "newest reading" in tf and not ff["budget"]["stale"],
       (code_f, ff["budget"]))
    stale_day = (today - datetime.timedelta(days=3)).isoformat()
    stale = _tree(_fixture_files(stale_day))
    code_s, ts, fs = run_once(stale, today, dry_run=True, quiet=True)
    ok("a budget row three days old reads as nothing measured, and the stale "
       "figure is NOT carried as current (age %s day(s))"
       % fs["budget"]["age_days"],
       code_s == 0 and "Nothing measured on the budget" in ts
       and "twelve percent" not in ts, (code_s, ts))
    ok("and the stale tree still carries the split sentence in words",
       "sessions and not points until the rate is measured" in ts, ts)
    ok("a tree with no history reports landed as nothing measured, not zero",
       "Nothing measured for what landed" in ts, ts)

    # A SOURCE THAT CANNOT BE READ: refuse, name it, write nothing.
    broken = _tree(_fixture_files(today.isoformat()))
    (broken / DECISIONS_REL).unlink()
    (broken / DECISIONS_REL).mkdir()          # a directory where a file must be
    code_b, tb, fb = run_once(broken, today, quiet=True)
    ok("an unreadable decision queue REFUSES the whole brief and names the "
       "source", code_b == 1 and tb is None
       and any(n == "cards" for n, _ in fb["failed"]), fb["failed"])
    ok("and nothing was written when it refused",
       not brief_path(broken, today).exists(),
       "a brief file exists after a refusal")
    noqueue = _tree({"production/notes.md": "hello\n"})
    code_n, tn, fn = run_once(noqueue, today, quiet=True)
    ok("a tree with no queue directory refuses too, naming the queue",
       code_n == 1 and any(n == "queue" for n, _ in fn["failed"]),
       fn["failed"])

    # WORDS, both ends, because the whole message is built out of this.
    ok("counts read as words: %s / %s / %s / %s"
       % (in_words(0), in_words(1), in_words(21), in_words(115)),
       (in_words(0), in_words(1), in_words(21), in_words(115))
       == ("no", "one", "twenty-one", "one hundred and fifteen"),
       (in_words(0), in_words(21), in_words(115)))

    print("\nmorning-brief --selftest: %s. %d passed, %d failed, over 1 live "
          "tree and 5 planted tree(s)"
          % ("PASS" if not failed else "FAILED", passed, len(failed)))
    for f in failed:
        print("  " + f)
    return 0 if not failed else 3


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(REPO))
    ap.add_argument("--date", help="the brief's date, ISO (default: today UTC)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--latest", action="store_true",
                    help="also write production/briefs/latest.md, which is "
                         "refused while that path is on the frozen list")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    today = (datetime.date.fromisoformat(a.date) if a.date
             else datetime.datetime.now(datetime.timezone.utc).date())
    root = pathlib.Path(a.root).resolve()
    if not (root / QUEUE_REL).is_dir():
        print("morning-brief: nothing measured, no %s/ under %s"
              % (QUEUE_REL, root))
        return 2
    code, _, _ = run_once(root, today, dry_run=a.dry_run, write_latest=a.latest)
    return code


if __name__ == "__main__":
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    sys.exit(main())
