#!/usr/bin/env python3
"""ONE PRODUCER TURN A DAY: the five sources, gathered, and the only measure of
the channel, printed.

    python3 tools/producer-day.py                 # gather for today, UTC
    python3 tools/producer-day.py --day 2026-09-10
    python3 tools/producer-day.py --print         # to stdout, write nothing
    python3 tools/producer-day.py --streak        # the count alone
    python3 tools/producer-day.py --root DIR      # read a planted tree
    python3 tools/producer-day.py --selftest      # accepting case FIRST

RULED BY JAFAR 2026-09-09, VERBATIM: "One Producer turn a day writes the single
message. It reads the queue, findings, decision queue, receipts and ladder, and
decides what I see and what I never see. The brief generator, the cards pass
and the page notifier are retired; the register stays as a format check after
the Producer writes."

WHAT THIS IS. The HARNESS for that turn and nothing more: it puts the five
sources he named in one place a Producer agent can read, and it prints the
consecutive readable count. THE JUDGMENT IS NOT HERE. This program does not
rank, does not score, does not summarise, does not choose what he sees and
writes no prose. There is no headline function in this file, deliberately: that
is the machinery the ruling retires, and it lived in tools/morning-brief.py,
which is retired with a banner on it.

WHAT IT DOES WITH EACH SOURCE, SO NOBODY HAS TO GUESS WHETHER IT JUDGED:
  - the queue: counted by tools/queue-check.py's `count_queue`, which is the
    ONE queue counter in this repository, and the ready and blocked names as
    that counter returns them. No ordering of its own.
  - the findings: the entries NEWER THAN THE BOUNDARY, verbatim, newest last,
    with the cap announcing itself. Chronology, not ranking.
  - the decision queue: parsed by tools/runner/cards.py's parser, which is the
    one reader of that file. THE NORMAL CASE IS NOW THAT NOTHING NEEDS HIM:
    ruled 2026-09-09, the studio takes every decision carrying a recommendation
    and a default, logs it under TAKEN BY THE STUDIO, and a card is written at
    most once a week, only when no recommendation can be formed. An empty
    WAITING section is printed with its denominator and is not a fault.
  - the receipts: classified by tools/runner/outbox.py's `outbound_summary`,
    the one classifier of that folder. 500 files cannot be read by an agent
    with Grep; the classification is what makes them legible, and it adds no
    judgment of its own.
  - the ladder: production/ladder.md, the rung table verbatim.
  - AND THE CHANNEL ITSELF: yesterday's brief, whether he tapped it readable or
    unreadable, the reason if he gave one, his messages since that tap, and the
    consecutive readable run.

THE BOUNDARY IS THE NEWEST BRIEF BEFORE THIS DAY, and it is stated on the done
line, because "since the last message he read" is the register's own phrase and
a boundary nobody states is a boundary every reader assumes differently. With
no earlier brief the boundary is the words nothing measured and every source is
reported in full.

WHAT THE COUNT IS A STATISTIC OF. briefStreakReadable is a RUN LENGTH, counted
backwards from the newest tapped day while the verdict is readable, last-wins
within a day. Not a peak, not a median, not a total. The arithmetic is
tools/runner/brief.py's and is covered by its selftest; this program supplies
the files and prints what it returns. TODAY, on this tree, it reads 0 of 7
consecutive with no tap ever recorded, and those are the words it prints: a
selftest cannot move that number and is not allowed to claim it.

EXIT CODES, distinct per outcome. 0 it gathered. 2 a source could not be read
and is named (nothing measured, not a clean gather). 3 the selftest failed.
"""
import argparse
import datetime
import importlib.util
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
RUNNER = HERE / "runner"
if str(RUNNER) not in sys.path:
    sys.path.insert(0, str(RUNNER))
import brief                                                   # noqa: E402
import cards                                                   # noqa: E402
import inbox                                                   # noqa: E402
import outbox                                                  # noqa: E402


def _load(path, name):
    """Import a tool whose filename carries a dash. One implementation per
    idea: the queue counter is tools/queue-check.py's and is imported, never
    re-typed."""
    try:
        spec = importlib.util.spec_from_file_location(name, str(path))
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:                                          # noqa: BLE001
        return None


_queue_check = _load(HERE / "queue-check.py", "queue_check")

#: Where the gathered dossier goes. ONE FILE PER DAY, and it is an INPUT to a
#: Producer turn rather than a page, a report or a tally: the Producer agent has
#: Read and Grep and no Bash, so it cannot run this program, and the director
#: that spawns it names this path in the brief.
DOSSIER_DIR = "production/brief-input"

#: The five sources Jafar named, by path, in his own order. Named once so the
#: done line and the dossier cannot come to disagree about what was read.
SOURCES = (("queue", "production/queue"),
           ("findings", "production/findings.txt"),
           ("decisions", cards.QUEUE_REL),
           ("receipts", inbox.OUTBOUND_DIR),
           ("ladder", "production/ladder.md"))

#: HOW MUCH OF EACH SOURCE IS INLINED. Every one of these announces when it
#: bites, with the count of what it hid, because a cap that does not say it bit
#: reads as a finding. They are not thresholds on anything measured: they are
#: the size of one agent's read, and the whole of every source stays one Read
#: away at the path printed beside it.
FINDINGS_ENTRIES = 6
INBOX_MESSAGES = 8
QUEUE_NAMES = 12
RECEIPT_LINES = 12

#: A findings entry starts at one of these rulers. The file carries two
#: styles, both live: dashes from 2026-09-07 and equals from 2026-09-09.
FINDINGS_RULER = re.compile(r"^(-{20,}|={20,})\s*$")
ISO = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


def utc_today():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def read_text(root, rel):
    """(text, why-not). A source that cannot be read is NAMED, never treated
    as empty: an empty findings file and an unreadable one are different
    facts."""
    try:
        with open(os.path.join(str(root), *rel.split("/")), "r",
                  encoding="utf-8", errors="replace") as fh:
            return fh.read(), ""
    except OSError as e:
        return None, "%s could not be read (%s)" % (rel, type(e).__name__)


# --------------------------------------------------------------------------
# The boundary
# --------------------------------------------------------------------------
def boundary(root, day):
    """(the newest brief day strictly before `day`, its path) or (None, why).

    "Since the last message he read" is the register's own phrase, so the
    boundary is the last brief that exists, not a fixed window.
    """
    here = brief.briefs_on_disk(root)
    earlier = sorted(d for d in here if d < day)
    if not earlier:
        return None, ("nothing measured: %d brief(s) in the tree and none "
                      "dated before %s" % (len(here), day))
    return earlier[-1], here[earlier[-1]]


# --------------------------------------------------------------------------
# The five sources. NO RANKING, NO SUMMARISING, CHRONOLOGY ONLY.
# --------------------------------------------------------------------------
def queue_section(root):
    """The ONE queue counter's answer, plus the names it returns."""
    if _queue_check is None:
        return (["queue: NOTHING MEASURED, tools/queue-check.py could not be "
                 "imported, so no queue number here is trustworthy."], True)
    c = _queue_check.count_queue(root)
    if not c["exists"]:
        return (["queue: NOTHING MEASURED, there is no %s under this tree."
                 % c["queue_dir"]], True)
    lines = ["queue (counted by tools/queue-check.py, the one counter): "
             "ready=%d blocked=%d landed=%d unstatused=%d of walked=%d, "
             "exempt=%d" % (c["ready"], c["blocked"], c["landed"],
                            c["unstatused"], c["walked"], c["exempt"])]
    for label, names in (("ready", c["ready_names"]),
                         ("blocked", c["blocked_names"])):
        shown = names[:QUEUE_NAMES]
        lines.append("  %s, %d of %d shown:" % (label, len(shown), len(names))
                     if names else
                     "  %s: none, of %d item(s) walked" % (label, c["walked"]))
        lines += ["    %s" % n for n in shown]
        if len(names) > len(shown):
            lines.append("    (+%d more not shown)" % (len(names) - len(shown)))
    return lines, False


def findings_entries(text):
    """The file split into entries, oldest first, each with its own date.

    THE FILE SAYS "Newest first" IN ITS OWN HEADER AND IT IS NOT: measured
    2026-09-09, the first entry is dated 2026-09-08 and the last 2026-09-09.
    This reader therefore sorts by nothing and trusts nothing: it returns the
    entries in FILE ORDER with whatever date each one carries, and the caller
    selects by date rather than by position.
    """
    lines = (text or "").splitlines()
    out, cur = [], []
    for i, line in enumerate(lines):
        if FINDINGS_RULER.match(line):
            head = lines[i + 1] if i + 1 < len(lines) else ""
            if ISO.search(head) or ISO.search(line):
                if cur:
                    out.append(cur)
                cur = [line]
                continue
        if cur:
            cur.append(line)
    if cur:
        out.append(cur)
    res = []
    for block in out:
        m = ISO.search("\n".join(block[:3]))
        res.append({"day": m.group(1) if m else "", "text": "\n".join(block)})
    return res


def findings_section(root, since):
    entries = None
    text, why = read_text(root, "production/findings.txt")
    if text is None:
        return ["findings: NOTHING MEASURED, %s." % why], True
    entries = findings_entries(text)
    fresh = [e for e in entries if not since or e["day"] >= since]
    shown = fresh[-FINDINGS_ENTRIES:]
    lines = ["findings (production/findings.txt, %d entry/entries in the file, "
             "%d dated %s or later, %d shown verbatim):"
             % (len(entries), len(fresh), since or "any day", len(shown))]
    if len(fresh) > len(shown):
        lines.append("  (+%d more not shown; the whole file is at the path "
                     "above)" % (len(fresh) - len(shown)))
    if not entries:
        lines.append("  nothing measured: the file parsed to 0 entry/entries, "
                     "which is a reader fault rather than an empty file if "
                     "the file is not empty.")
    for e in shown:
        lines.append("")
        lines += ["  " + l for l in e["text"].splitlines()]
    return lines, False


def decisions_section(root):
    text, why = read_text(root, cards.QUEUE_REL)
    if text is None:
        return ["decisions: NOTHING MEASURED, %s." % why], True
    parsed = cards.parse_queue(text)
    waiting = cards.waiting_cards(parsed)
    sections = {}
    for c in parsed:
        sections[c["section"]] = sections.get(c["section"], 0) + 1
    lines = ["decisions (%s, read by the one parser): waiting=%d of %d card(s) "
             "in the file" % (cards.QUEUE_REL, len(waiting), len(parsed))]
    lines.append("  sections: %s"
                 % ("; ".join("%s=%d" % (k, v)
                              for k, v in sorted(sections.items()))
                    or "none"))
    if not waiting:
        lines.append("  NOTHING NEEDS HIM, and that is the normal case since "
                     "2026-09-09: the studio takes every decision carrying a "
                     "recommendation and a default. 0 waiting of %d card(s) "
                     "walked is a reading, not a fault." % len(parsed))
    for c in waiting:
        lines.append("")
        lines.append("  WAITING: %s" % c["heading"])
        lines.append("    class=%s added=%s options=%d"
                     % (c.get("cls") or "none", c.get("added") or "none",
                        len(c.get("options") or [])))
        for key in ("recommendation", "default", "deadlineText"):
            if c.get(key):
                lines.append("    %s" % c[key])
    return lines, False


def receipts_section(root):
    """What actually reached his phone, classified by the one classifier."""
    d = os.path.join(str(root), *inbox.OUTBOUND_DIR.split("/"))
    if not os.path.isdir(d):
        return (["receipts: NOTHING MEASURED, there is no %s under this tree, "
                 "so nothing is known about what reached him."
                 % inbox.OUTBOUND_DIR], True)
    records = {}
    for n in sorted(os.listdir(d)):
        if not inbox.OUTBOUND_RE.match(n):
            continue
        try:
            with open(os.path.join(d, n), "r", encoding="utf-8",
                      errors="replace") as fh:
                records["%s/%s" % (inbox.OUTBOUND_DIR, n)] = fh.read()
        except OSError:
            records["%s/%s" % (inbox.OUTBOUND_DIR, n)] = ""
    summary = outbox.outbound_summary(records)
    lines = ["receipts (%s, %d record(s) walked, classified by "
             "tools/runner/outbox.py): sent=%d refused=%d replies=%d "
             "photos=%d cards=%d unreadable=%d"
             % (inbox.OUTBOUND_DIR, summary["records"], len(summary["sent"]),
                len(summary["refused"]), len(summary["replies"]),
                len(summary["photos"]), len(summary["cards"]),
                len(summary["unreadable"]))]
    if not records:
        lines.append("  nothing measured: 0 record(s) matched the receipt "
                     "pattern in that folder.")
        return lines, False
    # THE DELIVERIES, NEWEST LAST, BY THE RECEIPT'S OWN INSTANT. Chronology
    # and not ranking. The first version of this printed the LAST dozen lines
    # of the classifier's output, and on the live tree that was ten
    # near-identical refusals of one message from 3 September: 483 of the 506
    # records are refusals of two files, they sort before everything else by
    # name, and the tail slice therefore hid every delivery. Read off the live
    # output, not reasoned about.
    def when(f):
        try:
            return int(f.get("sentEpoch", 0))
        except ValueError:
            return 0
    sent = sorted(summary["sent"], key=when)
    shown = sent[-RECEIPT_LINES:]
    if len(sent) > len(shown):
        lines.append("  (+%d earlier delivery/deliveries not shown)"
                     % (len(sent) - len(shown)))
    for f in shown:
        lines.append("  delivered %s kind=%s sent=%s messageId=%s"
                     % (f.get("file", "?"), f.get("kind", "?"),
                        f.get("sent", "?"), f.get("messageId", "?")))
    # AND THE REFUSALS, ONE LINE PER FILE WITH ITS COUNT, because 483 records
    # name two files: a message refused once and a message refused 400 times
    # are the same fact about the channel and printing each is noise that
    # hides everything else.
    byfile = {}
    for f in summary["refused"]:
        byfile.setdefault(f.get("file", "?"), []).append(f)
    lines.append("  refusals: %d record(s) over %d distinct file(s)"
                 % (len(summary["refused"]), len(byfile)))
    for rel in sorted(byfile):
        one = byfile[rel][-1]
        # THE CLAUSE IS THE `clause:` FIELD, NOT THE `refused:` ONE. `refused:`
        # carries check or hold, which printed as newestClause=check and said
        # nothing at all: read off the record rather than assumed from the
        # bucket's name.
        clause = " ".join(str(one.get("clause", "")).split())
        lines.append("    %s refusedRecords=%d hold=%s newestClause=%s"
                     % (rel, len(byfile[rel]), one.get("hold", "?"),
                        (clause[:200] + " (+%d more not shown)"
                         % (len(clause) - 200)) if len(clause) > 200
                        else (clause or "nothing-measured")))
    return lines, False


def ladder_section(root):
    text, why = read_text(root, "production/ladder.md")
    if text is None:
        return ["ladder: NOTHING MEASURED, %s." % why], True
    rows = [l for l in text.splitlines() if l.startswith("|")]
    current = [l for l in rows if "| current |" in l]
    lines = ["ladder (production/ladder.md, %d table row(s), %d marked "
             "current):" % (len(rows), len(current))]
    lines += ["  " + l for l in rows]
    if not rows:
        lines.append("  nothing measured: the file carries no table row.")
    return lines, False


# --------------------------------------------------------------------------
# The channel's own state, which is the half the ruling measures
# --------------------------------------------------------------------------
def tap_records(root):
    d = os.path.join(str(root), *inbox.BRIEF_TAP_DIR.split("/"))
    out = {}
    if not os.path.isdir(d):
        return out
    for n in sorted(os.listdir(d)):
        if not inbox.BRIEF_TAP_RE.match(n):
            continue
        try:
            with open(os.path.join(d, n), "r", encoding="utf-8") as fh:
                out["%s/%s" % (inbox.BRIEF_TAP_DIR, n)] = fh.read()
        except OSError:
            out["%s/%s" % (inbox.BRIEF_TAP_DIR, n)] = ""
    return out


def brief_receipts(root):
    """{path: content} for the receipts, or None when the folder is absent.

    None RATHER THAN AN EMPTY DICT, so "no brief was ever sent" and "nothing is
    known about what was sent" print differently. `brief.streak` turns the
    second into the words nothing measured.
    """
    d = os.path.join(str(root), *inbox.OUTBOUND_DIR.split("/"))
    if not os.path.isdir(d):
        return None
    out = {}
    for n in sorted(os.listdir(d)):
        if not inbox.OUTBOUND_RE.match(n):
            continue
        try:
            with open(os.path.join(d, n), "r", encoding="utf-8") as fh:
                out["%s/%s" % (inbox.OUTBOUND_DIR, n)] = fh.read()
        except OSError:
            continue
    return out


def his_messages_since(root, since_epoch, cap=INBOX_MESSAGES):
    """What he typed since the boundary, verbatim, newest last."""
    out = []
    for rel in inbox.message_files(str(root)):
        try:
            with open(os.path.join(str(root), *rel.split("/")), "r",
                      encoding="utf-8") as fh:
                fields, _why = inbox.parse_message(fh.read())
        except OSError:
            continue
        if not fields:
            continue
        if since_epoch is None or fields["sentEpoch"] >= since_epoch:
            out.append((fields["sentEpoch"], rel, fields["text"]))
    out.sort()
    return out[-cap:], len(out)


def channel_state(root, day):
    """Everything about the channel itself, in one dict."""
    taps = brief.taps_from(tap_records(root))
    receipts = brief_receipts(root)
    sent_days = (None if receipts is None
                 else brief.sent_days_from_receipts(receipts))
    s = brief.streak(taps, sent_days)
    last_day, last_path = boundary(root, day)
    since_epoch = None
    if s["lastDay"]:
        try:
            since_epoch = int(datetime.datetime.strptime(
                s["lastDay"], "%Y-%m-%d").replace(
                    tzinfo=datetime.timezone.utc).timestamp())
        except ValueError:
            since_epoch = None
    msgs, msgs_total = his_messages_since(root, since_epoch)
    return {"streak": s, "taps": taps, "lastBriefDay": last_day,
            "lastBriefPath": last_path, "messages": msgs,
            "messagesTotal": msgs_total, "day": day}


def channel_lines(st):
    s = st["streak"]
    lines = ["THE CHANNEL, AND THIS IS THE ONLY MEASURE OF IT (ruled "
             "2026-09-09):",
             "  %s" % brief.streak_words(s),
             "  %s" % brief.streak_line(s)]
    if not s["tapsEver"]:
        lines.append("  NO TAP HAS EVER BEEN RECORDED. %d of %d "
                     "consecutive, over %s brief(s) sent down the daily path "
                     "that HAS buttons (the briefs sent before 2026-09-09 out "
                     "of the outbox had none to tap and are outside this "
                     "denominator). Nothing here can be moved by a selftest: "
                     "only a tap on his phone moves it."
                     % (s["readableRun"], s["want"],
                        s["briefsSentEver"] if s["briefsSentKnown"]
                        else "nothing-measured"))
    if s["lastVerdict"] == brief.UNREADABLE:
        lines.append("  YESTERDAY WAS UNREADABLE, SO TODAY'S IS WRITTEN "
                     "DIFFERENTLY AND SAYS WHAT CHANGED. His reason: %s"
                     % (s["lastReason"] or "he gave none"))
    if st["taps"]["unreadableRecords"]:
        lines.append("  %d tap record(s) could not be read and are counted "
                     "rather than dropped: %s"
                     % (len(st["taps"]["unreadableRecords"]),
                        "; ".join("%s (%s)" % (p, w) for p, w
                                  in st["taps"]["unreadableRecords"][:3])))
    lines.append("  the brief before today: %s"
                 % (st["lastBriefPath"] or "nothing measured, there is none"))
    shown, total = st["messages"], st["messagesTotal"]
    lines.append("  what he typed since the last tap: %d of %d shown"
                 % (len(shown), total) if total else
                 "  what he typed since the last tap: none, of %d message(s) "
                 "in the tree" % total)
    for _epoch, rel, text in shown:
        lines.append("    %s: %s" % (rel.rsplit("/", 1)[-1],
                                     " ".join(text.split())[:300]))
    return lines


# --------------------------------------------------------------------------
# The dossier
# --------------------------------------------------------------------------
def gather(root, day):
    """Every section, plus what could not be read. Returns a dict."""
    since, why_no_since = boundary(root, day)
    blocks, unreadable = [], []
    for name, fn in (("queue", lambda: queue_section(root)),
                     ("findings", lambda: findings_section(root, since)),
                     ("decisions", lambda: decisions_section(root)),
                     ("receipts", lambda: receipts_section(root)),
                     ("ladder", lambda: ladder_section(root))):
        lines, bad = fn()
        blocks.append((name, lines))
        if bad:
            unreadable.append(name)
    st = channel_state(root, day)
    return {"day": day, "since": since, "whyNoSince": why_no_since,
            "blocks": blocks, "unreadable": unreadable, "channel": st,
            "root": str(root)}


def dossier(res):
    """The file the Producer turn reads. NO PROSE ABOUT THE PROJECT IS WRITTEN
    HERE: every line is either a source's own text, a count with its
    denominator, or an instruction about where to write."""
    day = res["day"]
    out = ["# The day's sources, for one Producer turn. %s" % day,
           "",
           "GATHERED BY tools/producer-day.py. Nothing here is a draft, a "
           "headline or a recommendation: the five sources Jafar named are "
           "below as they read, and the judgment is yours. Ruled 2026-09-09: "
           "you decide what he sees and what he never sees.",
           "",
           "BOUNDARY: %s. Everything dated after it is new since the last "
           "brief." % (res["since"] or res["whyNoSince"]),
           ""]
    out += channel_lines(res["channel"])
    out.append("")
    out.append("WHERE TO WRITE IT, AND WHAT HAPPENS NEXT:")
    out.append("  write %s, in your own words, to the register in "
               ".claude/agents/producer.md" % brief.brief_rel(day))
    out.append("  then `python3 tools/producer-check.py --kind brief %s` "
               "checks the FORMAT of what you wrote. It does not shape it and "
               "it cannot read whether a claim is true."
               % brief.brief_rel(day))
    out.append("  the send path puts two buttons on it, readable and "
               "unreadable. An unreadable tap means tomorrow's is written "
               "differently AND says what changed.")
    out.append("  Jafar's own four, for the message itself: no numbers with "
               "units, no coordinates, no file names, no studio vocabulary.")
    if res["unreadable"]:
        out.append("")
        out.append("SOURCES THAT COULD NOT BE READ, so this gather is "
                   "incomplete and says so: %s" % ", ".join(res["unreadable"]))
    for name, lines in res["blocks"]:
        out.append("")
        out.append("## %s" % name)
        out += lines
    return "\n".join(out) + "\n"


def done_line(res):
    st = res["channel"]["streak"]
    return ("producer-day done: day=%s boundary=%s sourcesRead=%d/%d "
            "sourcesUnreadable=%d dossier=%s %s"
            % (res["day"], res["since"] or "nothing-measured",
               len(res["blocks"]) - len(res["unreadable"]), len(res["blocks"]),
               len(res["unreadable"]),
               res.get("writtenTo") or "not-written",
               brief.streak_line(st).split(": ", 1)[1]))


def run(root, day, write=True, say=print):
    res = gather(root, day)
    text = dossier(res)
    if write:
        rel = "%s/%s.md" % (DOSSIER_DIR, day)
        full = os.path.join(str(root), *rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        res["writtenTo"] = rel
        say("producer-day: the five sources for %s are in %s. Give that path "
            "to the Producer turn." % (day, rel))
    else:
        say(text)
    say(brief.streak_words(res["channel"]["streak"]))
    say(done_line(res))
    return (2 if res["unreadable"] else 0), res


# --------------------------------------------------------------------------
# SELFTEST. The live tree is the accepting fixture; the rejecting one is
# synthetic, so doing the work this asks for can never break it.
# --------------------------------------------------------------------------
def _selftest():
    import tempfile
    passed, failed, bad = 0, 0, []

    def check(name, cond, detail=""):
        nonlocal passed, failed
        if cond:
            passed += 1
            print("  ok   %s" % name)
        else:
            failed += 1
            bad.append(name)
            print("  FAIL %s  %s" % (name, detail))

    print("producer-day selftest: the live repository first, then a planted "
          "tree that is missing every source.")

    # ---- ACCEPTING: the live tree, which is the fixture ------------------
    said = []
    code, res = run(REPO, utc_today(), write=False, say=said.append)
    body = "\n".join(said)
    check("accept/the-live-tree-gathers-all-five-sources",
          code == 0 and not res["unreadable"]
          and all(("## %s" % n) in body for n, _ in SOURCES),
          "exit=%d unreadable=%s" % (code, res["unreadable"]))
    check("accept/the-queue-count-comes-from-the-one-counter",
          "counted by tools/queue-check.py" in body
          and "walked=" in body, "see the queue section")
    check("accept/the-receipts-are-classified-not-listed-raw",
          "classified by tools/runner/outbox.py" in body, "see receipts")
    check("accept/nothing-in-the-dossier-is-a-headline-or-a-draft",
          "HEADLINE:" not in body and "WHAT CHANGED:" not in body
          and "NEEDS YOU" not in body, "a draft leaked into the harness")
    check("accept/the-done-line-names-its-boundary-and-its-denominators",
          "sourcesRead=5/5" in body and "boundary=" in body
          and "briefStreakReadable=" in body,
          [l for l in said if l.startswith("producer-day done")][-1:])
    # THE LIVE READING, PRINTED AND ASSERTED AS WHAT IT IS TODAY.
    s = res["channel"]["streak"]
    check("accept/the-count-prints-as-words-with-its-denominator",
          brief.streak_words(s).startswith("%d of %d consecutive"
                                          % (s["readableRun"], s["want"])),
          brief.streak_words(s))
    check("accept/and-a-selftest-cannot-move-it",
          s["tapsEver"] == len(tap_records(REPO))
          and s["readableRun"] <= s["daysTapped"],
          brief.streak_line(s))

    # ---- REJECTING: a tree with none of the five sources -----------------
    tmp = tempfile.mkdtemp(prefix="producer-day-selftest-")
    said2 = []
    code2, res2 = run(tmp, "2026-09-10", write=False, say=said2.append)
    body2 = "\n".join(said2)
    check("reject/an-empty-tree-is-nothing-measured-and-not-a-clean-gather",
          code2 == 2 and len(res2["unreadable"]) == 5
          and "sourcesUnreadable=5" in body2, "exit=%d" % code2)
    check("reject/every-missing-source-says-nothing-measured-by-name",
          body2.count("NOTHING MEASURED") >= 5
          and "SOURCES THAT COULD NOT BE READ" in body2, "see above")
    check("reject/and-the-never-tapped-words-are-the-ruled-ones",
          "0 of 7 consecutive, no tap has ever been recorded" in body2,
          [l for l in said2 if "consecutive" in l][:1])
    check("reject/a-tree-with-no-receipts-folder-says-nothing-measured",
          "briefsSentEver=nothing-measured" in body2,
          [l for l in said2 if "briefStreak" in l][:1])
    # AND A PLANTED TAP MOVES IT, WHICH IS THE OTHER HALF A GUARD NEEDS.
    brief.write_tap(tmp, "2026-09-09", brief.READABLE, 1757500000, 9001)
    said3 = []
    _code3, res3 = run(tmp, "2026-09-10", write=False, say=said3.append)
    check("accept/a-planted-readable-tap-moves-the-count-by-one",
          res3["channel"]["streak"]["readableRun"] == 1
          and "briefStreakReadable=1/7" in "\n".join(said3),
          brief.streak_line(res3["channel"]["streak"]))
    brief.write_tap(tmp, "2026-09-10", brief.UNREADABLE, 1757590000, 9002)
    said4 = []
    _code4, res4 = run(tmp, "2026-09-11", write=False, say=said4.append)
    check("reject/and-one-unreadable-tap-puts-it-back-to-zero",
          res4["channel"]["streak"]["readableRun"] == 0
          and "YESTERDAY WAS UNREADABLE" in "\n".join(said4),
          brief.streak_line(res4["channel"]["streak"]))
    # A SYNTHETIC SOURCE NAME THAT EXISTS NOWHERE IS THE REJECTING FIXTURE
    # FOR THE SOURCE LIST, so doing the work can never break this guard.
    check("reject/a-source-that-exists-nowhere-is-not-in-the-ruled-five",
          not any(rel == "production/no-such-source.md" for _n, rel in SOURCES)
          and len(SOURCES) == 5, str([r for _n, r in SOURCES]))

    print("producer-day selftest: %d passed, %d failed, %d checks run%s"
          % (passed, failed, passed + failed,
             "" if not bad else " FAILED: " + ", ".join(bad[:4])))
    return 0 if not failed else 3


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(REPO))
    ap.add_argument("--day", help="ISO day (default: today UTC)")
    ap.add_argument("--print", dest="to_stdout", action="store_true",
                    help="print the dossier, write nothing")
    ap.add_argument("--streak", action="store_true",
                    help="the consecutive readable count alone")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    root = pathlib.Path(a.root).resolve()
    day = a.day or utc_today()
    if a.streak:
        st = channel_state(root, day)
        print(brief.streak_words(st["streak"]))
        print(brief.streak_line(st["streak"]))
        return 0
    code, _res = run(root, day, write=not a.to_stdout)
    return code


if __name__ == "__main__":
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    sys.exit(main())
