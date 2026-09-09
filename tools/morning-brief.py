#!/usr/bin/env python3
"""RETIRED 2026-09-09. NOTHING CALLS THIS AND IT NO LONGER WRITES THE MESSAGE.

RULED BY JAFAR, 2026-09-09, VERBATIM: "The channel fails because nobody with
judgment sits in it. Replace the machinery with one judgment step. One Producer
turn a day writes the single message. It reads the queue, findings, decision
queue, receipts and ladder, and decides what I see and what I never see. The
brief generator, the cards pass and the page notifier are retired; the register
stays as a format check after the Producer writes."

THIS IS THE BRIEF GENERATOR. WHAT REPLACED IT:
  - tools/producer-day.py gathers the five sources he named for one Producer
    turn, and prints the consecutive readable count.
  - The Producer writes production/briefs/<YYYY-MM-DD>.md in its own words.
    No template, no headline function, no ranking.
  - tools/producer-check.py checks that file AFTER it is written.
  - tools/runner/telegram-bot.py --send-brief sends it with two buttons on it,
    readable and unreadable, and the tap comes back as a record.

ITS LAST CALLER WAS tools/runner/run-night.ps1 AND THAT CALL IS GONE. Nothing
in the repository runs this program; a grep for its name finds this banner, the
records that describe it and the comments in other files that name it as the
thing that was retired.

NOT DELETED, DELIBERATELY. Its composition rules, its provenance lines and its
refusals are the record of what a generated brief could and could not do, and
the reason the ruling above is right: it could compose a shape and it could
not decide what he never sees.

WHAT IT DID, KEPT BELOW AS WRITTEN, so the retirement is readable rather than
a blank file. Everything after this line describes the retired program.

THE MORNING BRIEF, GENERATED FROM REPO STATE. No model call, one writer.

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
    build measured nothing;
  - tools/gallery.py's find_pictures(), for how many pictures are newer than
    the previous brief AND for which picture is the newest of its kind;
  - production/ladder.md, the visual ladder Jafar ruled on 2026-09-09, for the
    CURRENT RUNG, which is where the project stands;
  - the landed verdicts under production/d1-probe/ and game-design/sim-shots/,
    for their own status words, which is the only place in this repository
    that records what the GAME did;
  - production/next-three.json, through tools/map.py's next_three(), so a
    finished step is proved by the same evidence keys his page proves it by
    and never by a second reader written here.

WHY THE HEADLINE IS AN OUTCOME AND NOT A COUNT, ruled by Jafar 2026-09-06 and
measured as broken on 2026-09-09 (queue 179). The generator read counts only,
so its headline was "Eighteen new pictures of the street since the previous
brief, and six decisions are waiting for you". Eighteen pictures is what was
engineered. On the night it was measured, the town had composed its own
sentence about a broken window and nothing the tool read could have told it.
So the headline now comes from a verdict's own status words and from the
ladder's current rung, and A HEADLINE THAT CANNOT BE EARNED IS NOT INVENTED:
with no outcome named in the window the brief says nothing was measured about
what changed for the game, in those words, and never falls back to a count to
fill the line. "Nothing happened for the game since the last brief" is a
legitimate and useful thing for this brief to say.

THE WORD CAP IS A TRIM LADDER AND EVERY RUNG ANNOUNCES ITSELF. The spoken line
the game composed is worth more than anything else in the message and is also
the longest thing in it, so the composition drops optional clauses in one fixed
order until the register's cap is cleared, and prints which rungs it dropped
(`trimmed=`). A cap that bit in silence would read as a brief that had nothing
to say.

THE PICTURES ARE OF THE STREET AND THE BRIEF SAYS STREET. Measured 2026-09-06:
every walked directory holds frames of the one D1 street, and the newest of
them (production/d1-probe/ue-vign_camA_day.png) was opened by a director and is
a grey checker blockout. None of them holds Meridian yet. "Pictures of the
town" is a claim the picture does not support, and a brief that oversells the
frame is the one thing this generator must never do, because he opens the
picture straight after reading it.

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
# SOFT, and named as such: the picture dates come from tools/gallery.py's
# find_pictures(), which is the one implementation of "which frames are the
# latest" in this repository. If it cannot be imported the brief still writes
# and says "nothing measured" about pictures, the way git does. A hard refusal
# here would let a missing sibling stop the morning.
# SOFT, AND NAMED: tools/map.py owns the one proof that a next-three.json
# `done` step really finished (it opens each named evidence file and looks for
# the exact key=value token). A second copy of that proof here is how his page
# and his phone come to disagree about what is done. If map.py cannot be
# imported the steps read "nothing measured" and the brief still writes.
# tools/runner/outbox.py is imported for TWO CONSTANTS ONLY, its Telegram
# caption cap and its sidecar suffix, so this program can print whether the
# brief would fit as a captioned photo rather than carry a second copy of 1024.
gal = _load(HERE / "gallery.py", "gallery")
mp = _load(HERE / "map.py", "ledger_map")
ob = _load(HERE / "runner" / "outbox.py", "ledger_outbox")
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
LADDER_REL = "production/ladder.md"
STEPS_REL = "production/next-three.json"
QUEUE_REL = qc.QUEUE_REL
AGENT_LOG_REL = vf.DIRECTOR_LOG

# WHERE A LANDED VERDICT LIVES. The two directories CI commits verdicts into,
# named rather than walked from the root, because a glob over the tree would
# find the fixtures, the specs and the documents that quote a key.
VERDICT_DIRS = ("production/d1-probe", "game-design/sim-shots")
# Line 1 of every verdict in this repository names the commit it was measured
# on and the instant it was measured at (.claude/rules/ci.md, the verdict
# format). That instant is the only honest date for an outcome: a file time in
# a checkout is the moment of the clone, and a commit date is when the file
# landed rather than when the game did the thing.
VERDICT_STAMP_RE = re.compile(r"@(\d{9,12})\b")

# WHERE A LINK MAY POINT, RULED BY JAFAR 2026-09-06: at most two links per
# message, and only to the glance, the map or the gallery. Never to a
# repository markdown file, and a picture reaches him as a Telegram image
# rather than as a link. This brief used to carry three blob URLs on the work
# branch, which is exactly what the ruling refuses.
#
# THE URLS COME FROM tools/producer-check.py's OWN LIST. A second copy here is
# how the writer and the checker come to disagree about what the site is: the
# checker would refuse a URL the writer believes in, every morning, with
# nobody able to see which of the two was wrong.
def site_url(path):
    """One ruled destination, by its path, out of the register's list."""
    for name, _label in pc.SITE_PAGES:
        if name == path:
            return pc.SITE_ORIGIN + name
    raise KeyError("%r is not one of the ruled destinations: %s"
                   % (path, "/".join(n or "(the glance)"
                                     for n, _ in pc.SITE_PAGES)))

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


def _lower_first(s):
    """Somebody else's heading spliced into the middle of a sentence: the first
    letter drops and a trailing full stop goes, because "a door that opens.;
    when is unknown" is what happens when it does not."""
    s = s.strip().rstrip(".")
    return (s[0].lower() + s[1:]) if s else s


def in_date_words(epoch):
    """A picture's or a verdict's instant as a date a person reads, and NOT a
    bare count: tools/producer-check.py's numeral scrub names "9 September" a
    named-month date and lets it through the ban on quantities, which is why
    the date can be in the message at all. UTC, because every verdict stamp and
    every commit date in this project is."""
    d = datetime.datetime.fromtimestamp(int(epoch),
                                        datetime.timezone.utc).date()
    return d.strftime("%d %B").lstrip("0")


# HOW LONG A RUNG'S OWN "done looks like" SENTENCE MAY BE before the brief uses
# the rung's NAME instead. THE SERIES CAME FIRST (production/ladder.md,
# 2026-09-09, printed by --selftest): 34, 28, 19, 14, 11, 12, 5 words for the
# seven rungs, peak 34 and median 14. A 34-word section is a fifth of a
# 150-word message, so the bound admits the median and refuses the peak.
DETAIL_MAX_WORDS = 20
# WHAT GETS DROPPED WHEN THE CAP BITES, IN THIS ORDER, AND THE ORDER IS WORTH
# LEAST FIRST. Measured on the live tree 2026-09-09: with every clause in, the
# message runs 178 words against a cap of 150, so something goes, and the order
# decides what he reads. THE QUOTE GOES BEFORE ANY OUTCOME SENTENCE, ruled by
# the director 2026-09-09 in these words: "if the word budget is fighting you,
# cut the quote rather than the outcome; the quote is a nicety and the headline
# is the whole ruling". It is also the biggest single clause at thirty words, so
# dropping it once is usually the only drop the cap needs. Every drop is named
# on the done line with the words it saved.
TRIM_ORDER = ("detail", "quote", "second", "picture")
# AND WHAT CHANGED IS NEVER EMPTY. The first version of the ladder above could
# drop every clause in that section and printed `WHAT CHANGED:` with nothing
# after it, which reads as a morning where nothing happened rather than as a
# message that ran out of room. This is the floor under it.
CHANGED_FLOOR = "The gallery has the newest picture of the street."


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


def read_pictures(root, since_day):
    """How many pictures are newer than the previous brief, out of how many,
    AND WHICH ONE IS THE NEWEST, with the date it carries.

    ONE IMPLEMENTATION OF "WHICH FRAMES ARE THE LATEST": tools/gallery.py dates
    every picture by the commit that touched it (file times in a checkout are
    all the moment of the clone), and this reads its find_pictures() rather
    than a second walk. MEASURED-ABSENT, not required: a tree with no gallery
    tool yields the words nothing measured instead of a refusal.

    THE NEWEST ONE IS HERE BECAUSE OF JAFAR'S RULING OF 2026-09-09: "every
    image or clip sent is the newest of its kind, dated in its caption". The
    brief is what the sender turns into the caption, so the DATE has to be in
    the message and the CHOICE has to be the newest rather than a name typed
    into a tool years ago. `newestDated` says commit or mtime and is never
    silent: an mtime in a fresh checkout is the clone's time, which is not a
    date anything happened on.
    """
    blank = {"n": None, "total": 0, "newest": None, "newestWhen": None,
             "newestDated": None}
    if gal is None:
        blank["why"] = "the picture dater could not be imported"
        return blank, True, "tools/gallery.py(unavailable)"
    try:
        shots, reading = gal.find_pictures(root)
    except Exception as e:                                       # noqa: BLE001
        blank["why"] = type(e).__name__
        return blank, True, "tools/gallery.py(failed)"
    cut = datetime.datetime.fromisoformat(
        since_day + "T00:00:00").replace(
            tzinfo=datetime.timezone.utc).timestamp()
    # NEWER THAN THE LEFT EDGE OF THE SAME WINDOW read_landed uses, so the two
    # counts in one brief describe one period. Two windows with one name is the
    # fault this file's previous_brief_day() docstring already names.
    fresh = [s for s in shots if s["when"] >= cut]
    # find_pictures() returns NEWEST FIRST, so the newest of its kind is the
    # head of its list and not a second sort written here.
    top = shots[0] if shots else None
    return ({"n": len(fresh), "total": len(shots), "why": "",
             "newest": top["rel"] if top else None,
             "newestWhen": top["when"] if top else None,
             "newestDated": top["dated"] if top else None,
             "dirs": reading["dirsWalked"], "dirsNamed": reading["dirsNamed"],
             "clips": reading["clipsFound"]},
            True, "tools/gallery.py(find_pictures,since-%s)" % since_day)


# ------------------------------------------------- what the GAME did, and when
# AN OUTCOME IS A THING THE GAME DID, so this reads the only files in the
# repository that record one: the verdicts CI commits. Each row is
#
#     (key=value token, the sentence a person would say, )
#
# and THE ORDER IS THE RANK, highest first. The rank is not invented here: it
# is the moat order of CLAUDE.md section 0, "the moat is social memory,
# consequence persistence and information... Everything else is in service of
# it". So somebody hearing a rumour outranks the rumour moving, which outranks
# the crime being seen, which outranks the street being walkable.
#
# WHAT IS NOT IN THIS TABLE IS AS DELIBERATE AS WHAT IS. `grateRectStatus` is
# not here, and the reason is NOT that the grate missed the frame. Read the
# whole key set before quoting one of them: the live run says
# grateShotStatus=AIMED, grateOccluded=no, grateBlocker=none, and its subject
# rectangle sits on the frame at 0.4615 to 0.6835 of the height. The grate is
# in the picture and its diagonal slots are legible in it.
# grateRectStatus=OFF-FRAME describes THE RECTANGLE PAIR, not the piece: the
# CONTROL rectangle's own fractions are NEGATIVE
# (grateControlRectFrac=0.4329/-0.2575/0.5671/-0.0354), so the control sits off
# the top of the frame and the subject-against-control comparison cannot be
# made. That is queue 177 and it is a measurement fault, not a render one.
# IT IS OUT OF THIS TABLE BECAUSE IT IS NOT AN OUTCOME. A rectangle's status
# says nothing about social memory, consequence or information, which is what
# this table ranks.
# The separate and true observation: the word MEASURED appears in that file
# only on a COMMENT line describing what the ruling asked for, so reading that
# comment as a measurement would be queue 064's "a comment may not write a
# key", which is why read_verdict_outcomes() skips every line starting with a
# hash and counts how many it skipped.
#
# NO BANNED WORD MAY ENTER A SENTENCE HERE. `commit` and everything like it is
# on tools/producer-check.py's run-internals list, so crimeStatus=COMMITTED
# reads as a window going in rather than as a crime being committed. The
# selftest runs every sentence through the register's own ban list, so a new
# row cannot quietly redden the morning.
OUTCOMES = (
    ("overheardStatus=HEARD",
     "you overheard two people on the street talking about the crime"),
    ("gossipStatus=REAL",
     "what one of them saw passed by word of mouth to the next person"),
    ("witnessStatus=REAL",
     "somebody standing on the street saw the crime and remembered it"),
    ("crimeStatus=COMMITTED",
     "a shop window went in on the street you can walk down"),
    ("collisionStatus=REAL",
     "a wall on the street stopped you walking through it"),
    ("launchStatus=LAUNCHED",
     "the game started up and played on your own machine"),
    ("sceneStatus=WHOLE",
     "the street built whole, every piece of it standing"),
)
# The spoken line the game composed, read out of the SAME file the chosen
# outcome came from. Spaces are dashes inside a verdict value and tildes inside
# a capped list, and the verdict says so itself
# (overheardTextNote=spaces-become-dashes-in-a-value), so undoing both is the
# inverse of a transform the source names rather than a guess about it.
QUOTE_KEY = "overheardTellText"


def _undash(value):
    """A verdict value back into prose. Named so because it is lossy in one
    direction only: a genuine hyphen in the source would already have been
    written as one and is indistinguishable from a space here, which is the
    emitter's convention and not this reader's choice."""
    return re.sub(r"\s+", " ", value.replace("~", " ").replace("-", " ")).strip()


def read_verdict_outcomes(root, since_day, until_day):
    """Every outcome named by a verdict, with the instant the verdict was
    measured at, newest-and-highest-ranked first.

    THE WINDOW IS THE BRIEF'S WINDOW. A verdict measured before the previous
    brief is not news, and a verdict with no `@epoch` on line 1 CANNOT BE
    DATED, which is counted as its own number rather than folded into either
    answer. MEASURED-ABSENT: no verdict directory yields "nothing measured"
    about outcomes and is never a refusal, because a tree with no build is not
    a broken tree.
    """
    lo = datetime.datetime.fromisoformat(since_day + "T00:00:00").replace(
        tzinfo=datetime.timezone.utc).timestamp()
    hi = (datetime.datetime.fromisoformat(until_day + "T00:00:00").replace(
        tzinfo=datetime.timezone.utc) + datetime.timedelta(days=1)).timestamp()
    walked, dated, undated, comment_lines, contradicted = 0, 0, 0, 0, []
    hits, newest = [], None
    dirs_present = [d for d in VERDICT_DIRS
                    if (pathlib.Path(root) / d).is_dir()]
    for d in dirs_present:
        for p in sorted((pathlib.Path(root) / d).glob("*.txt")):
            if "verdict" not in p.name.lower():
                continue
            walked += 1
            try:
                lines = p.read_text(encoding="utf-8",
                                    errors="replace").splitlines()
            except Exception:                                    # noqa: BLE001
                continue
            m = VERDICT_STAMP_RE.search(lines[0] if lines else "")
            if not m:
                undated += 1
                continue
            dated += 1
            when = int(m.group(1))
            if newest is None or when > newest[0]:
                newest = (when, p.relative_to(root).as_posix())
            if not (lo <= when < hi):
                continue
            # A COMMENT MAY NOT WRITE A KEY (queue 064). Every hash line is
            # skipped and the skips are counted, because the one place
            # `grateRectStatus=MEASURED` appears in this repository is a
            # comment describing what a ruling asked for, and reading it would
            # have put a claim in the brief that the live key contradicts.
            body = []
            for line in lines:
                if line.lstrip().startswith("#"):
                    comment_lines += 1
                    continue
                body.append(line)
            tokens = set()
            for line in body:
                tokens.update(line.split())
            rel = p.relative_to(root).as_posix()
            quote = ""
            for tok in tokens:
                if tok.startswith(QUOTE_KEY + "="):
                    quote = _undash(tok.split("=", 1)[1])
            for rank, (token, sentence) in enumerate(OUTCOMES):
                if token not in tokens:
                    continue
                key = token.split("=", 1)[0]
                others = sorted(t for t in tokens
                                if t.startswith(key + "=") and t != token)
                if others:
                    # THE SAME KEY WITH A DIFFERENT VALUE IN THE SAME FILE IS
                    # NOT AN OUTCOME. Two answers under one name is the
                    # instrument disagreeing with itself, and the honest
                    # reading is to drop the claim and say it was dropped.
                    contradicted.append("%s/by=%s" % (token, others[0]))
                    continue
                hits.append({"token": token, "sentence": sentence,
                             "rank": rank, "when": when, "file": rel,
                             "quote": quote})
    # RANK FIRST (the moat order above), THEN THE NEWER VERDICT. Both halves
    # are named so a reader never has to guess which one chose the headline.
    hits.sort(key=lambda h: (h["rank"], -h["when"]))
    return ({"hits": hits, "walked": walked, "dated": dated,
             "undated": undated, "commentLines": comment_lines,
             "contradicted": contradicted,
             "dirs": len(dirs_present), "dirsNamed": len(VERDICT_DIRS),
             "newestWhen": newest[0] if newest else None,
             "newestFile": newest[1] if newest else None,
             "chosenBy": "moat-rank-then-newest-instant"},
            True, "%s(%d-dir(s),since-%s)" % ("+".join(VERDICT_DIRS),
                                              len(dirs_present), since_day))


LADDER_ROW_RE = re.compile(r"^\|(.+)\|\s*$")
LADDER_STATUSES = ("done", "current", "next", "later")


def read_ladder(root):
    """The visual ladder's rungs and the ONE that is current.

    production/ladder.md is LIVE and Jafar ruled it on 2026-09-09. Its table is
    a contract in its own words: columns rung, name, status, "done looks like",
    status exactly one of done/current/next/later, EXACTLY ONE ROW CURRENT. So
    this reads the contract and never guesses: zero current rows or two are
    both "nothing measured" about where the project stands, with the count
    printed, rather than a rung picked by position.

    THIS IS THE FIRST READER OF THAT TABLE IN THE REPOSITORY, measured
    2026-09-09: the file says tools/map.py renders it and map.py contains no
    reference to it, so the claim in the file is ahead of the code. If a second
    reader is ever added, it imports this one.
    """
    p = pathlib.Path(root) / LADDER_REL
    blank = {"rows": [], "current": None, "total": 0, "why": "",
             "counts": {s: 0 for s in LADDER_STATUSES}, "unknown": 0}
    if not p.is_file():
        blank["why"] = "no-%s-in-this-checkout" % LADDER_REL
        return blank, True, "%s(absent)" % LADDER_REL
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:                                       # noqa: BLE001
        return {}, False, "%s could not be read (%s)" % (LADDER_REL,
                                                         type(e).__name__)
    rows, counts, unknown = [], {s: 0 for s in LADDER_STATUSES}, 0
    for line in text.splitlines():
        m = LADDER_ROW_RE.match(line.strip())
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if len(cells) < 4 or not re.match(r"^\d+$", cells[0]):
            continue                      # the header and its dashed rule
        status = cells[2].lower()
        if status in counts:
            counts[status] += 1
        else:
            unknown += 1
        rows.append({"rung": int(cells[0]), "name": cells[1],
                     "status": status, "done_looks_like": cells[3]})
    current = [r for r in rows if r["status"] == "current"]
    out = dict(blank, rows=rows, total=len(rows), counts=counts,
               unknown=unknown)
    if len(current) == 1:
        out["current"] = current[0]
    else:
        out["why"] = ("%d-of-%d-rows-say-current/the-files-own-contract-is-"
                      "exactly-one" % (len(current), len(rows)))
    return out, True, LADDER_REL


def read_steps(root, since_day, until_day):
    """The finished steps of production/next-three.json, PROVED by tools/map.py.

    ONE IMPLEMENTATION OF "IS THIS STEP REALLY DONE": map.py's next_three()
    opens every named evidence file and looks for the exact key=value token,
    and his page is rendered from that same answer. A second proof written here
    would let the brief and the page disagree with nobody able to see which was
    wrong. SOFT: no map.py means nothing measured about steps, not a refusal.
    """
    if mp is None:
        return ({"done": [], "inWindow": [], "proven": 0, "claimed": 0,
                 "keysFound": 0, "keysAsked": 0,
                 "why": "the step prover could not be imported"},
                True, "tools/map.py(unavailable)")
    try:
        _items, reading = mp.next_three(root)
    except Exception as e:                                       # noqa: BLE001
        return ({"done": [], "inWindow": [], "proven": 0, "claimed": 0,
                 "keysFound": 0, "keysAsked": 0, "why": type(e).__name__},
                True, "tools/map.py(failed)")
    done = reading.get("done") or []
    in_window = [d for d in done
                 if d.get("proven") and since_day <= str(d.get("doneOn", ""))
                 <= until_day]
    return ({"done": done, "inWindow": in_window,
             "proven": reading.get("doneProven", 0),
             "claimed": reading.get("doneNamed", 0),
             "keysFound": reading.get("doneKeysFound", 0),
             "keysAsked": reading.get("doneKeysAsked", 0),
             "refusal": reading.get("doneRefusal"), "why": ""},
            True, "%s(via-tools/map.py,since-%s)" % (STEPS_REL, since_day))


# WHAT THE HEADLINE MUST LEAD WITH, ruled by Jafar 2026-09-06: "lead with
# where the project stands and what changed for the game, not with what was
# engineered". Mechanical and narrow on purpose: it reads the first line's
# words. It cannot tell whether the sentence is any good, and the selftest runs
# it on the shape he rejected as well as on the one it writes, because a rule
# only checked against the text it was written for is a ratchet.
#
# WHY THIS GUARD LET A COUNT HEADLINE THROUGH, measured 2026-09-09 (queue 179).
# It had two readings, both of them about VOCABULARY: no engineering word, at
# least one word of his. "Eighteen new pictures of the street since the previous
# brief, and six decisions are waiting for you" carries no engineering word and
# three of his (street, picture, decision), so it passed with both readings
# green. The thing Jafar ruled against was never a word, it was the SHAPE: a
# quantity of a studio artifact standing as the subject of the sentence. So the
# third reading below counts that shape directly, and the rejected headline is
# now refused by the pair `eighteen..pictures`/`six..decisions`.
ENGINEERING_WORDS = ("queue", "work list", "items are ready", "landed",
                     "pipeline")
GAME_WORDS = ("street", "town", "picture", "decision", "look", "game",
              "overheard", "saw", "remembered", "window", "walk", "ladder",
              "stands", "played", "talking")
# THE NOUNS THAT MAKE A QUANTITY A COUNT OF WHAT WAS ENGINEERED. A count of
# things in the WORLD is not what he ruled against and is often the best thing
# in the message ("two people on the street were overheard"), so this list is
# studio artifacts only and nothing that exists in Meridian.
COUNTED_NOUNS = ("picture", "pictures", "commit", "commits", "change",
                 "changes", "session", "sessions", "item", "items", "card",
                 "cards", "decision", "decisions", "file", "files", "frame",
                 "frames", "task", "tasks", "gate", "gates", "build", "builds",
                 "run", "runs", "spawn", "spawns", "point", "points", "step",
                 "steps", "rung", "rungs", "line", "lines", "word", "words",
                 "percent")
# in_words() writes "twenty-one" and "one hundred and fifteen", so the
# quantities to look for are exactly the words it can produce, plus a digit.
# ONES[0] is "no", which is deliberate: "No new pictures this morning" is the
# same shape with a zero in it and is no better a headline than eighteen.
QUANTITY_WORDS = frozenset([w for w in ONES] + [w for w in TENS if w]
                           + ["hundred", "dozen"])
# HOW FAR A QUANTITY REACHES TO ITS NOUN, in words. Three covers "eighteen new
# pictures" (two), "ninety-two changes have landed" (one, because the hyphen
# splits) and "six of the sixteen cards" (three). It is a window and not a
# sentence parser, and when it bites short the headline simply passes, which is
# why the accepting fixture is checked first and on real text.
COUNT_WINDOW = 3


def counted_artifacts(headline):
    """Every place this headline COUNTS a studio artifact, as
    `<quantity>..<noun>` with no space in it so a done line can carry it."""
    words = re.findall(r"[a-z0-9]+", headline.lower())
    out = []
    for i, w in enumerate(words):
        if not (w in QUANTITY_WORDS or w.isdigit()):
            continue
        for j in range(i + 1, min(i + 1 + COUNT_WINDOW, len(words))):
            if words[j] in COUNTED_NOUNS:
                out.append("%s..%s" % (w, words[j]))
                break
    return out


def leads_with_the_game(headline):
    """(verdict, reading). THREE READINGS, ALL PRINTED, so a failure says which
    half broke: `engineered` is the words of the studio's own paperwork,
    `counted` is the shape of a count of them, and `game` is whether anything
    in the line is his at all."""
    low = headline.lower()
    reading = {"engineered": [w for w in ENGINEERING_WORDS if w in low],
               "counted": counted_artifacts(headline),
               "game": [w for w in GAME_WORDS if w in low]}
    ok = (not reading["engineered"] and not reading["counted"]
          and bool(reading["game"]))
    return ok, reading


# THE SPLIT COVERAGE GATE, and it is not the register's split rule.
# tools/producer-check.py already refuses a brief whose BUDGET section does not
# carry the five parts of the sentence (studio, game, sessions, "not points",
# "measured"); what nothing checked until 2026-09-09 is whether the sentence
# carries the DENOMINATOR. "Sixty-one sessions went to the studio" and
# "sixty-one of one hundred and twelve" are different facts, and a reader
# completes the first one by guessing. The standing order in the daily wake is
# "every brief reports the studio versus game split", so this is the half that
# makes the report a measurement rather than a number.
def split_in_words(text, split):
    """(verdict, reading). The reading names every part it looked for, so a
    failure says which half broke rather than only that one did."""
    bodies, _order = pc.split_sections(text)
    body = " ".join(bodies.get("BUDGET", [])).strip()
    register = [f for f in pc.check(text, "brief")["findings"]
                if f.rule == "split"]
    total = in_words(split["total"])
    # THE DENOMINATOR IS LOOKED FOR AS THE WORDS BEFORE THE UNIT, not as a
    # substring. in_words(0) is "no", and a plain `"no" in body` passed on the
    # "not points" three words later, so the zero case certified itself.
    denom = re.compile(r"\b%s\s+sessions?\b" % re.escape(total), re.I)
    parts = {
        "theRegistersFiveParts": not register,
        "theDenominatorInWords": bool(body) and bool(denom.search(body)),
        "theBasisIsNamedAsSessions": "sessions" in body.lower(),
    }
    return all(parts.values()), {"parts": parts, "denominator": total,
                                 "registerFindings": [str(f) for f in register]}


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
    until = today.isoformat()
    q = source("queue", read_queue(root))
    cards = source("cards", read_cards(root))
    budget = source("budget", read_budget(root, today))
    split = source("split", read_split(root, since, until))
    landed = source("landed", read_landed(root, since))
    frame = source("frame", read_frame(root))
    pics = source("pictures", read_pictures(root, since))
    ladder = source("ladder", read_ladder(root))
    outcomes = source("outcomes", read_verdict_outcomes(root, since, until))
    steps = source("steps", read_steps(root, since, until))
    facts.update({"queue": q, "cards": cards, "budget": budget,
                  "split": split, "landed": landed, "frame": frame,
                  "pictures": pics, "ladder": ladder, "outcomes": outcomes,
                  "steps": steps,
                  "window_since": since, "window_until": until,
                  "prev_brief": prev})
    if facts["failed"]:
        return None, facts

    # TWO LINKS, THE MAXIMUM HE RULED, and both to the site. The gallery sits
    # under WHAT CHANGED because that is where the pictures are talked about,
    # and the glance under NEEDS YOU because that is where the decision lives.
    gallery_url = site_url("gallery.html")
    glance_url = site_url("")

    waiting = cards["waiting"]

    # ------------------------------------------------------------- the parts
    # WHERE THE PROJECT STANDS: the ladder's current rung, and nothing else.
    # Jafar wrote production/ladder.md on 2026-09-09 to be exactly this answer,
    # with the contract that exactly one row says current. Zero rows or two is
    # "nothing measured", never a rung chosen by position: a ladder that
    # invents its own place is the failure its own last paragraph forbids.
    rung = ladder.get("current")
    if rung:
        stands = ("the ladder's current rung is %s"
                  % _lower_first(rung["name"]))
    else:
        stands = "nothing measured about where the ladder stands"

    # WHAT CHANGED FOR THE GAME: a verdict's own status words, ranked by the
    # moat. AN UNEARNED HEADLINE IS NOT INVENTED: with nothing in the window
    # the lead says so in those words, and a count never fills the line.
    hits = outcomes["hits"]
    first, second = (hits[0] if hits else None), (hits[1] if len(hits) > 1
                                                  else None)
    if first:
        lead = first["sentence"][0].upper() + first["sentence"][1:]
    else:
        lead = ("Nothing measured about what changed for the game since the "
                "previous brief")
    quote = (first or {}).get("quote") or ""
    # THE SPOKEN LINE, AND IT IS CHECKED BEFORE IT IS QUOTED. The game composed
    # it, so nothing here knows what is in it: a register finding inside a
    # quotation would refuse the whole morning over a sentence a person said.
    # Checked on the ban list only, for the reason the card heading is.
    if quote:
        quote_findings = [f for f in pc.check(quote, "answer")["findings"]
                          if f.rule != "linkfloor"]
        quote_why = "/".join(sorted(set(f.rule for f in quote_findings))) \
            or "none"
    else:
        quote_findings, quote_why = [], "no-%s-in-the-chosen-verdict" % QUOTE_KEY
    facts["quote_ok"] = 1 if (quote and not quote_findings) else 0
    facts["quote_why"] = quote_why

    # THE PICTURE CLAUSE CARRIES THE NEWEST ONE'S DATE, ruled by Jafar
    # 2026-09-09: "every image or clip sent is the newest of its kind, dated in
    # its caption". tools/runner/outbox.py makes the message body the caption of
    # the attachment it carries, so the date belongs in the message.
    #
    # AND IT PROMISES HIM NO PAGE. It used to say the pictures are "in the
    # gallery", which is a claim that a site he can open holds them. THE
    # ACCURATE STATEMENT IS STALENESS, NOT ABSENCE, and the first draft of this
    # comment got it wrong: of 48 publish runs FOUR SUCCEEDED, the last on
    # 2026-09-07 at 20:23Z on commit 45de6c21 (the pageCommit in
    # production/map-notified.json), and every run since failed, 41 to 48 on the
    # morning of 2026-09-09 among them. So a page he opens EXISTS and shows an
    # older day. That is subtler than a 404 and worse: a 404 tells him something
    # is wrong and a stale page does not. The brief says when the newest picture
    # was taken, which is true of the repository, and the attachment on the done
    # line is what actually reaches his phone.
    if pics["n"] is None:
        picture = "Nothing measured about new pictures this morning."
    elif pics["n"] and pics["newest"]:
        picture = ("The newest picture of the street is from %s."
                   % in_date_words(pics["newestWhen"]))
    elif pics["newest"]:
        picture = ("No new picture since the previous brief; the newest is "
                   "still from %s." % in_date_words(pics["newestWhen"]))
    else:
        picture = "There is no picture of the street at all."

    # THE NEXT THING HE WILL SEE is the current rung's own "done looks like"
    # column when it survives two measured bounds, and the rung's NAME when it
    # does not. THE BOUNDS COME FROM THE PRINTED SERIES, not from taste: the
    # seven rungs' first sentences measure 34/28/19/14/11/12/5 words
    # (2026-09-09, printed by --selftest), and two of the seven carry a file
    # path that the register bans outright. DETAIL_MAX_WORDS admits the short
    # ones and refuses the two longest, because one section may not eat a fifth
    # of a 150-word message.
    detail, detail_words = "", 0
    if rung:
        detail = re.split(r"(?<=[.!?])\s+", rung["done_looks_like"])[0].strip()
        detail_words = len(detail.split())
        bad = [f for f in pc.check(detail or "x", "answer")["findings"]
               if f.rule != "linkfloor"]
        if bad or detail_words > DETAIL_MAX_WORDS:
            detail = ""
    facts["rung_detail_words"] = detail_words
    facts["rung_detail_used"] = 1 if detail else 0

    if budget["reading"] is None or budget["stale"]:
        money = ("Nothing measured on the budget: no reading newer than two "
                 "days, so today's spend is unknown and an unknown budget is "
                 "not permission.")
    else:
        money = ("Your newest reading was %s percent on the meter that "
                 "governs, taken %s."
                 % (in_words(budget["reading"]),
                    "today" if budget["age_days"] == 0 else "yesterday"))
    # THE SPLIT SENTENCE, REQUIRED IN EVERY BRIEF by the standing order in the
    # daily wake, in WORDS, in this section, COUNTED IN SESSIONS, WITH ITS
    # DENOMINATOR, and with the reason it is not points. "Fifty-seven" and
    # "fifty-seven of one hundred and seven" are different facts, and the first
    # one is the fact a reader completes by guessing.
    # producer-check --kind brief refuses a brief without the five parts; this
    # program's own gate refuses one without the denominator.
    if split["total"]:
        money += (" Of %s %s since the previous brief, %s went to the studio "
                  "and %s to the game, in sessions not points until the rate "
                  "is measured."
                  % (in_words(split["total"]),
                     plural(split["total"], "session", "sessions"),
                     in_words(split["studio"]), in_words(split["game"])))
    else:
        money += (" No sessions at all since the previous brief, so the studio "
                  "and the game both read nothing, in sessions not points "
                  "until the rate is measured.")
    # THE ART SHARE IS A THIRD QUANTITY AND IS NOT THE SPLIT. Jafar ruled on
    # 2026-09-08 that the art line takes at most a quarter of the WEEK'S POINTS,
    # and the hand-written brief of 2026-09-09 reported the art share where the
    # standing order asks for the studio-versus-game split, which is a different
    # question answered in a different unit. This program cannot compute the art
    # share honestly: .claude/agent-log.tsv carries two columns, a time and an
    # agent name, no agent name in it is the art line, and production/budget.md
    # says the turns-to-points conversion is UNMEASURED. So it says that,
    # rather than letting the split stand in for it.
    money += " The art share is not measured here."

    if waiting:
        needs = ("%s %s waiting for you."
                 % (in_words(waiting).capitalize(),
                    plural(waiting, "card is", "cards are")))
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
            needs = ("%s%s" % (top, "" if waiting == 1
                               else " That is the first of them."))
            facts["card_title_used"] = 1
        else:
            facts["card_title_used"] = 0
    else:
        needs = "Nothing needs you this morning."
        facts["card_title_used"] = 0

    # ------------------------------------------------------------ the render
    # THE TRIM LADDER. Optional clauses, dropped in this order until the
    # register's word cap is clear, each drop announced on the done line. The
    # spoken line is the most valuable thing in the message and also the
    # longest, so it is the first thing dropped rather than the thing that
    # refuses the morning.
    def render(on):
        out = ["HEADLINE: %s, and %s." % (lead, stands), ""]
        changed = []
        if "quote" in on and quote and not quote_findings:
            changed.append('One of them said: "%s"' % quote)
        if "second" in on and second:
            changed.append(second["sentence"][0].upper()
                           + second["sentence"][1:] + ".")
        if not changed and not first:
            changed.append("Nothing measured about what the game did since "
                           "the previous brief.")
        if "picture" in on:
            changed.append(picture)
        out.append("WHAT CHANGED: " + " ".join(changed or [CHANGED_FLOOR]))
        out.append("[the gallery](%s)" % gallery_url)
        out.append("")
        out.append("NEEDS YOU: " + needs)
        # THE LABEL IS "the console" AND NOT "where it all stands", corrected
        # 2026-09-09. Of 48 publish runs four succeeded, the last at
        # 2026-09-07T20:23:12Z, so the page a link opens EXISTS and is about 36
        # hours stale. "Where it all stands" promises currency that page does
        # not have; the destination is unchanged and still one of the three
        # Jafar ruled.
        out.append("[the console](%s)" % glance_url)
        out.append("")
        if "detail" in on and detail:
            out.append("NEXT VISIBLE THING: %s; when is unknown until it "
                       "starts." % _lower_first(detail))
        elif rung:
            out.append("NEXT VISIBLE THING: %s; when is unknown until it "
                       "starts." % _lower_first(rung["name"]))
        else:
            out.append("NEXT VISIBLE THING: unknown, because nothing names it.")
        out.append("")
        out.append("BUDGET: " + money)
        return "\n".join(out) + "\n"

    # A RUNG THAT CANNOT CONTRIBUTE IS NOT A RUNG THAT WAS DROPPED. Dropping an
    # absent clause would put a name in `trimmed=` that saved nothing, and a
    # reader would read the cap as biting twice as hard as it did.
    contributes = {"quote": bool(quote and not quote_findings),
                   "second": bool(second), "detail": bool(detail),
                   "picture": True}
    on, dropped = set(k for k in TRIM_ORDER if contributes[k]), []
    text = render(on)
    for part in TRIM_ORDER:
        res = pc.check(text, "brief")
        if res["words"] <= res["cap"]:
            break
        if part not in on:
            continue
        before = res["words"]
        on.discard(part)
        text = render(on)
        after = pc.check(text, "brief")["words"]
        dropped.append("%s..%d-words-over..saved-%d"
                       % (part, before - res["cap"], before - after))
    facts["trimmed"] = dropped
    facts["trim_order"] = [k for k in TRIM_ORDER if contributes[k]]
    # THE HEADLINE GUARD RUNS ON EVERY MORNING, not only in the selftest. A
    # guard nothing calls is decoration (CLAUDE.md rule 6), and this one let a
    # count headline through for three days while passing its own test.
    ok, lead_reading = leads_with_the_game(text.splitlines()[0])
    facts["lead_ok"], facts["lead_reading"] = ok, lead_reading
    facts["split_ok"], facts["split_reading"] = split_in_words(text, split)
    return text, facts


def brief_path(root, today):
    return pathlib.Path(root) / BRIEFS_REL / ("%s.md" % today.isoformat())


def provenance(facts):
    """Every number in this brief, with the file it was read from, one per
    line. It lives HERE and not in the message because the brief register bans
    counts and paths in anything Jafar reads; the pair still has to exist
    somewhere a reader can audit, and this is that somewhere."""
    q, b, s, l = (facts["queue"], facts["budget"], facts["split"],
                  facts["landed"])
    p, o, st = facts["pictures"], facts["outcomes"], facts["steps"]
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
        # THE SPLIT, CUMULATIVE OVER THE WINDOW, WITH ITS BASIS AND ITS
        # DENOMINATOR ON THE SAME LINE AS THE NUMERATOR. `splitUnparsedRows` is
        # the rows the classifier could not read at all (three merge-conflict
        # markers sit in the log as of 2026-09-09): they are in neither answer
        # and would otherwise vanish, which is how a denominator quietly stops
        # counting what it claims to.
        "splitStudio=%d/%d basis=spawns %s" % (s["studio"], s["total"],
                                               AGENT_LOG_REL),
        "splitGame=%d/%d basis=spawns %s" % (s["game"], s["total"],
                                             AGENT_LOG_REL),
        "splitUnparsedRows=%d %s" % (s["unparsed"], AGENT_LOG_REL),
        # THE ART SHARE IS A THIRD QUANTITY AND IS NOT MEASURED HERE. Named on
        # its own line with the reason, because the failure this replaces was a
        # brief reporting the art share WHERE THE SPLIT WAS ASKED FOR.
        "artShareOfTheWeeksPoints=nothing-measured "
        "why=the-log-carries-when-and-agent-only/no-art-line-among-the-agent-"
        "names/points-unmeasured-per-%s" % BUDGET_REL,
        "landed=%s git-log-since-%s"
        % (l["n"] if l["n"] is not None else "nothing-measured",
           facts["window_since"]),
        # PER-WINDOW NUMERATOR WITH THE DENOMINATOR IT CAME FROM, on one line
        # so a reader cannot pair the numerator with the wrong total.
        "picturesSincePreviousBrief=%s/%d-in-the-repository %s"
        % (facts["pictures"]["n"] if facts["pictures"]["n"] is not None
           else "nothing-measured", facts["pictures"]["total"],
           "tools/gallery.py"),
        # WHAT THE SENDER ATTACHES. Jafar ruled 2026-09-06 that images are sent
        # as Telegram images and never as links, so the message no longer
        # carries the frame's URL and the path has to reach the sender
        # somewhere. This line is that somewhere, and it is outside the message
        # because the register bans paths in anything he reads.
        # TWO READINGS, NEVER MERGED. `attachAsTelegramImage` is the NEWEST
        # picture of its kind and the date that goes in its caption, which is
        # Jafar's ruling of 2026-09-09; `frameFromReportFrame` is what
        # tools/report-frame.py offers, which is a fixed Unity frame name and on
        # 2026-09-09 was six days older than the newest picture in the tree.
        # Printing both is how a reader sees them disagree. NOTHING READS EITHER
        # KEY TODAY: the send path takes its attachment from a sidecar file
        # beside a message in production/outbox/, and this brief is written to
        # production/briefs/, so the sidecar named below has to be written by
        # whatever carries the brief to the outbox. Queue 179's report names it.
        "attachAsTelegramImage=%s dated=%s by=%s sidecarWanted=%s"
        % (p["newest"] or "nothing-measured",
           in_date_words(p["newestWhen"]).replace(" ", "-")
           if p["newestWhen"] else "nothing-measured",
           p["newestDated"] or "nothing-measured",
           ("photo:%s" % p["newest"]) if p["newest"] else "none"),
        "frameFromReportFrame=%s tools/report-frame.py"
        % (facts["frame"]["rel"] or "nothing-measured/withheld"),
        # WHAT THE GAME DID, and the denominators under it. outcomeHits is how
        # many of the table's keys were found in the window, NOT how many
        # verdicts carried one.
        "outcomeChosen=%s %s" % (o["hits"][0]["token"].replace("=", "..")
                                 if o["hits"] else "nothing-measured",
                                 o["hits"][0]["file"] if o["hits"]
                                 else "/".join(VERDICT_DIRS)),
        "outcomeChosenAt=%s chosenBy=%s"
        % (datetime.datetime.fromtimestamp(
            o["hits"][0]["when"], datetime.timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ") if o["hits"]
           else "nothing-measured", o["chosenBy"]),
        # TWO NUMERATORS, TWO DENOMINATORS, NEVER CROSSED: the keys found are
        # DISTINCT keys over the table's size, and the hits are key-in-a-file
        # pairs over the verdicts read. The first version of this line divided
        # ten hits by seven keys, which is two populations under one slash.
        "outcomeKeysFound=%d/%d-looked-for outcomeHitsAcrossVerdicts=%d/%d-read "
        "verdictsDated=%d/%d-walked verdictsUndated=%d commentLinesSkipped=%d "
        "contradicted=%d/%s"
        % (len(set(h["token"] for h in o["hits"])), len(OUTCOMES),
           len(o["hits"]), o["dated"], o["dated"], o["walked"],
           o["undated"], o["commentLines"], len(o["contradicted"]),
           o["contradicted"][0] if o["contradicted"] else "none"),
        # THE LADDER: where the project stands, and the pair is rung-over-total
        # on one line so neither half can be read without the other.
        "ladderCurrentRung=%s/%d %s"
        % (facts["ladder"]["current"]["rung"] if facts["ladder"]["current"]
           else "nothing-measured", facts["ladder"]["total"], LADDER_REL),
        "ladderStatuses=%s unknown=%d why=%s"
        % ("/".join("%s..%d" % (k, v)
                    for k, v in facts["ladder"]["counts"].items()),
           facts["ladder"]["unknown"], facts["ladder"]["why"] or "none"),
        # THE FINISHED STEPS, PROVED BY tools/map.py's OWN EVIDENCE READER.
        "stepsProven=%d/%d stepsKeysFound=%d/%d stepsDoneInWindow=%d %s"
        % (st["proven"], st["claimed"], st["keysFound"], st["keysAsked"],
           len(st["inWindow"]), STEPS_REL),
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

    # THE HEADLINE GATE, RUN ON EVERY MORNING AND NOT ONLY IN THE SELFTEST.
    # Jafar ruled the shape on 2026-09-06 and this program went on leading with
    # a count until 2026-09-09 because the only thing that ever ran the rule was
    # a test asserting it passed. A guard nothing calls is decoration, CLAUDE.md
    # rule 6, so this refuses the brief rather than writing it.
    if not facts["lead_ok"]:
        lr = facts["lead_reading"]
        say("morning-brief: REFUSED to write. The headline does not lead with "
            "the game, ruled by Jafar 2026-09-06:")
        say("    %s" % text.splitlines()[0])
        say("    engineering word(s): %s" % (", ".join(lr["engineered"])
                                             or "none"))
        say("    counted artifact(s): %s" % (", ".join(lr["counted"])
                                             or "none"))
        say("    word(s) of his: %s" % (", ".join(lr["game"])
                                        or "none, which is the finding"))
        say("morning-brief: REFUSED leadOk=0 leadEngineered=%d leadCounted=%d "
            "leadGameWords=%d/%d briefWritten=0/1"
            % (len(lr["engineered"]), len(lr["counted"]), len(lr["game"]),
               len(GAME_WORDS)))
        return 1, text, facts

    # THE SPLIT COVERAGE GATE, also on every morning. The standing order in the
    # daily wake makes the split mandatory in EVERY brief and nothing read for
    # coverage until 2026-09-09: the register read for the sentence's shape, and
    # the one brief that went out by hand reported the art share instead, which
    # is a different quantity in a different unit.
    if not facts["split_ok"]:
        sr = facts["split_reading"]
        say("morning-brief: REFUSED to write. The BUDGET section does not "
            "report the studio-versus-game split with its denominator:")
        for part, good in sr["parts"].items():
            say("    %-28s %s" % (part, "found" if good else "MISSING"))
        say("    the denominator looked for: %s" % sr["denominator"])
        for f in sr["registerFindings"]:
            say("    %s" % f)
        say("morning-brief: REFUSED splitReported=0/1 splitPartsFound=%d/%d "
            "briefWritten=0/1"
            % (sum(1 for v in sr["parts"].values() if v), len(sr["parts"])))
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

    if dry_run:
        # THE USAGE LINE SAYS "compose and print" AND IT DID NOT PRINT. Read
        # back on 2026-09-06: --dry-run printed the provenance and the done
        # line and never the message, so the one command for looking at the
        # brief before writing it showed everything except the brief. CLAUDE.md
        # rule 4: open the artifact you are shipping.
        say("  the composed message, %d word(s) of %d, between the rules:"
            % (res["words"], res["cap"]))
        say("  " + "-" * 68)
        for line in text.splitlines():
            say("  | " + line)
        say("  " + "-" * 68)
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
    s, o, lr = facts["split"], facts["outcomes"], facts["lead_reading"]
    lad = facts["ladder"]
    # WHY THE QUOTE IS NOT IN THE MESSAGE, and the two reasons are different
    # facts: the cap took it, or the game never said anything. A single
    # `quoteInBrief=0` with no reason beside it cannot tell them apart.
    quote_trimmed = "quote" in [d.split("..")[0] for d in facts["trimmed"]]
    quote_in = 0 if quote_trimmed else facts["quote_ok"]
    quote_why = ("trimmed-for-the-word-cap" if quote_trimmed
                 else facts["quote_why"])
    # WHOLE-RUN NUMBERS, ONE LINE, and the per-source numbers are on the
    # provenance lines above. A reader greping one line across two moments is
    # the fault this split obeys.
    say("morning-brief: %s sourcesRead=%d/%d words=%d/%d registerFindings=0 "
        "leadOk=%d leadIs=%s leadCounted=%s "
        "outcome=%s outcomeKeysFound=%d/%d ladderRung=%s/%d "
        "quoteInBrief=%d/1 quoteWhy=%s trimmed=%s "
        "queueReady=%d/%d queueBlocked=%d/%d queueDone=%d cardsWaiting=%d/%d "
        "splitStudio=%d/%d splitGame=%d/%d splitBasis=spawns splitReported=1/1 "
        "splitUnparsedRows=%d artShare=nothing-measured "
        "splitSource=%s splitWindow=%s..%s budgetAgeDays=%s "
        "cardTitleUsed=%d/%d attach=%s attachDated=%s frame=%s "
        "briefChars=%d/%s-telegram-caption-cap "
        "briefWritten=%d/1 latestWritten=%d/1 generatedAt=%s"
        % ("DRY-RUN" if dry_run else "WROTE",
           len(facts["sources"]), len(facts["sources"]),
           res["words"], res["cap"],
           1 if facts["lead_ok"] else 0,
           "an-outcome" if o["hits"] else "nothing-measured",
           ",".join(lr["counted"]) or "none",
           o["hits"][0]["token"].replace("=", "..") if o["hits"]
           else "nothing-measured",
           len(set(h["token"] for h in o["hits"])), len(OUTCOMES),
           lad["current"]["rung"] if lad["current"] else "nothing-measured",
           lad["total"],
           quote_in, quote_why, ",".join(facts["trimmed"]) or "none",
           facts["queue"]["ready"], facts["queue"]["walked"],
           facts["queue"]["blocked"], facts["queue"]["walked"],
           facts["queue"]["done"],
           facts["cards"]["waiting"], facts["cards"]["scanned"],
           s["studio"], s["total"], s["game"], s["total"], s["unparsed"],
           AGENT_LOG_REL, facts["window_since"], facts["window_until"],
           facts["budget"]["age_days"] if facts["budget"]["age_days"]
           is not None else "nothing-measured",
           facts.get("card_title_used", 0), 1 if facts["cards"]["waiting"] else 0,
           facts["pictures"]["newest"] or "nothing-measured",
           in_date_words(facts["pictures"]["newestWhen"]).replace(" ", "-")
           if facts["pictures"]["newestWhen"] else "nothing-measured",
           facts["frame"]["rel"] or "withheld",
           len(text), ob.CAPTION_CAP if ob is not None else "nothing-measured",
           0 if dry_run else 1, wrote_latest,
           datetime.datetime.now(datetime.timezone.utc)
           .strftime("%Y-%m-%dT%H:%M:%SZ")))
    return 0, text, facts


# ------------------------------------------------------------------ selftest

# HOW MANY PLANTED TREES THIS RUN ACTUALLY BUILT. The closing line used to
# carry a typed literal ("5 planted trees") that nothing updated when a fixture
# was added, so the one number summarising the test's own coverage was the one
# number in it nobody measured.
_TREES_BUILT = [0]


def _tree(files):
    import atexit
    import shutil
    import tempfile
    _TREES_BUILT[0] += 1
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

    # THE LIVE TREE IS READ AT ITS REAL DATE, not at a pinned one. A pinned
    # 2026-09-05 put the brief's window three days behind the newest verdict, so
    # the accepting case for an OUTCOME headline could never see an outcome and
    # the live tree silently tested the nothing-measured path instead. Every
    # deterministic case below is a planted tree, which is where a fixed date
    # belongs.
    today = datetime.datetime.now(datetime.timezone.utc).date()
    print("morning-brief --selftest: ACCEPTING CASE FIRST, the live tree at %s\n"
          % today.isoformat())
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
    # THE LINK BAND, ruled 2026-09-06. The register enforces it above; this
    # names the reading so a failure says which half broke, and prints the
    # destinations rather than only their count.
    urls = pc.links_in(text)
    dests = [pc.site_page(u) for u in urls]
    ok("it carries %d link(s) of the ruled %d..%d and every one is a ruled "
       "destination (%s)" % (len(urls), pc.LINK_MIN, pc.LINK_MAX,
                             "/".join(d or "OFF-SITE" for d in dests)
                             or "nothing-measured"),
       pc.LINK_MIN <= len(urls) <= pc.LINK_MAX and all(dests), urls)

    # WHAT THE HEADLINE LEADS WITH, ruled 2026-09-06: "lead with where the
    # project stands and what changed for the game, not with what was
    # engineered". Mechanical and therefore narrow: the headline must not open
    # on the work list, and must name something of his (the town, a picture, or
    # a decision waiting). It cannot tell whether the sentence is any good.
    headline = text.splitlines()[0]
    lead_ok, lr = leads_with_the_game(headline)
    ok("the headline leads with the game, not the paperwork (%d engineering "
       "word(s) of %d looked for, %d counted artifact(s), %d game word(s) of "
       "%d found)"
       % (len(lr["engineered"]), len(ENGINEERING_WORDS), len(lr["counted"]),
          len(lr["game"]), len(GAME_WORDS)),
       lead_ok, (headline, lr))
    # THE OUTCOME HALF, on the live tree, and it asserts the PROPERTY rather
    # than today's sentence: the lead either names an outcome a verdict carries
    # or says nothing was measured in those words, and either way it counts no
    # studio artifact. A fixture pinned to today's crime run would break the
    # moment the next run lands, which is the pinning instruments.md forbids.
    lead_is_outcome = facts["outcomes"]["hits"] and (
        facts["outcomes"]["hits"][0]["sentence"].lower() in headline.lower())
    ok("the headline is an OUTCOME a verdict named (%s), or says nothing was "
       "measured (%d key(s) of %d found in the window)"
       % (facts["outcomes"]["hits"][0]["token"] if facts["outcomes"]["hits"]
          else "nothing measured",
          len(set(h["token"] for h in facts["outcomes"]["hits"])),
          len(OUTCOMES)),
       bool(lead_is_outcome)
       or "Nothing measured about what changed for the game" in headline,
       headline)
    ok("and where the project stands comes from the ladder's one current rung "
       "(rung %s of %d)"
       % (facts["ladder"]["current"]["rung"] if facts["ladder"]["current"]
          else "nothing measured", facts["ladder"]["total"]),
       (facts["ladder"]["current"] is not None
        and facts["ladder"]["current"]["name"].lower() in headline.lower())
       or "nothing measured about where the ladder stands" in headline,
       (facts["ladder"]["why"], headline))

    # AND THE OTHER OUTCOME, TWICE, ON THE TWO SHAPES JAFAR REJECTED. Both
    # strings are quoted here rather than read from a file, so repairing the
    # file can never disarm the guard.
    #
    # THE SECOND ONE IS THE MEASUREMENT THAT OPENED QUEUE 179: this program
    # really printed it on 2026-09-09, and the guard as it stood passed it,
    # because its only readings were about vocabulary and that sentence is full
    # of his words. The third reading is what refuses it.
    for name, rejected in (
            ("the queue-count headline of 2026-09-06",
             "HEADLINE: Eighty-three queue items are ready to start this "
             "morning, and eight blocked."),
            ("the picture-count headline this tool printed on 2026-09-09",
             "HEADLINE: Eighteen new pictures of the street since the previous "
             "brief, and six decisions are waiting for you.")):
        bad_lead, bad = leads_with_the_game(rejected)
        ok("and %s is REFUSED by the same rule (engineered:%s counted:%s)"
           % (name, "/".join(bad["engineered"]) or "none",
              "/".join(bad["counted"]) or "none"),
           not bad_lead, rejected)

    # NO BARE COUNT IN THE PROSE, and the URLs are scrubbed first because the
    # link floor REQUIRES them and a branch name carrying digits is not a count.
    # THIS WAS "no digit at all" UNTIL 2026-09-09 and had to loosen by exactly
    # one form: Jafar ruled that every image is "dated in its caption", and the
    # register's own numeral scrub names "9 September" a named-month date rather
    # than a quantity. So the assertion is now the register's own find_counts,
    # plus the stronger half printed beside it: every digit that survives sits
    # inside a date form and the forms are named.
    prose = pc.scrub_links(text)
    counts = pc.find_counts(prose)
    datescrub = prose
    for label, pat in pc.NUMERAL_OK:
        if "date" in label:
            datescrub = re.sub(pat, " ", datescrub, flags=re.I)
    ok("the message carries no `splitBasis=` and no bare count (%d found), and "
       "every digit left in it is a date (%d outside one)"
       % (len(counts), len(re.findall(r"\d", datescrub))),
       "splitBasis" not in prose and not counts
       and not re.search(r"\d", datescrub),
       (counts, re.findall(r"\S*\d\S*", datescrub)[:4]))
    # THE SPLIT COVERAGE GATE, ACCEPTING HALF: the live brief reports the split
    # with its denominator in words.
    sp_ok, sp = split_in_words(text, facts["split"])
    ok("the BUDGET section reports the split with its denominator in words "
       "(%s, basis spawns, denominator %s)"
       % ("/".join(k for k, v in sp["parts"].items() if v) or "nothing",
          sp["denominator"]),
       sp_ok, sp)
    # AND THE REJECTING HALF OF THE SAME GATE: the denominator taken out of the
    # sentence, which the register's own split rule cannot see at all.
    denom_phrase = ("Of %s %s since the previous brief, "
                    % (in_words(facts["split"]["total"]),
                       plural(facts["split"]["total"], "session", "sessions")))
    no_denominator = text.replace(denom_phrase, "")
    nd_ok, nd = split_in_words(no_denominator, facts["split"])
    ok("and the same brief with the denominator removed is REFUSED, while the "
       "register's own split rule still passes it (%d register finding(s) "
       "there, so this gate is not a second copy of that one)"
       % len(nd["registerFindings"]),
       no_denominator != text and not nd_ok and not nd["registerFindings"], nd)
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
    # THE SENTENCE IS REMOVED BY ITS MEANING, NOT BY ITS WORDING: every sentence
    # carrying "not points" goes, line by line so the section structure the
    # register reads survives. The previous version matched the exact phrasing
    # and went quiet the moment the phrasing changed, which is what it did on
    # 2026-09-09 when the denominator entered the sentence.
    stripped = "\n".join(
        " ".join(s for s in re.split(r"(?<=\.) ", line)
                 if "not points" not in s)
        for line in text.splitlines())
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
       "not points until the rate is measured" in ts, ts)
    # THE PROPERTY, NOT THE SENTENCE: the brief must say it could not look, and
    # must NOT say nothing landed. Asserting both halves is what makes this
    # survive a rewording without going quiet: the wording moved on 2026-09-06
    # and again on 2026-09-09 and this assertion caught it both times.
    #
    # WHERE IT MOVED TO, 2026-09-09: the count of what landed is no longer in
    # the message at all. It was a count of commits standing beside the split,
    # which is the same question ("how much work happened") answered twice from
    # two variables, and Jafar ruled counts out of the lead. It lives on the
    # provenance line, which is where a machine reads it.
    prov = "\n".join(provenance(fs))
    ok("a tree with no history reports landed as nothing measured on the "
       "provenance line, not zero, and the message carries no count of it",
       "landed=nothing-measured" in prov and fs["landed"]["n"] is None
       and "landed" not in ts, (prov.splitlines(), ts))

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

    # ------------------------------------------------ the outcome readers
    # A PLANTED STREET THAT DID SOMETHING, ACCEPTING CASE FIRST. Synthetic to
    # the last byte: a made-up status key would be rejected by the table, so the
    # tokens here are real ones, but the FILE, the ladder and the epoch are all
    # invented, which is what stops the live tree's next run from breaking this.
    noon = int(datetime.datetime.combine(
        today, datetime.time(6, 0)).replace(
            tzinfo=datetime.timezone.utc).timestamp())
    played = {
        "production/ladder.md":
            "# planted\n\n| rung | name | status | done looks like |\n"
            "|---|---|---|---|\n"
            "| 1 | A lamp that lights the wall | done | It lights it. |\n"
            "| 2 | A door that opens | current | He walks through the door. |\n"
            "| 3 | A face that moves | next | It moves. |\n",
        "production/d1-probe/made-up-verdict.txt":
            "# planted probe deadbeef @%d\n"
            "# crimeStatus=COMMITTED on a comment line, which may not count\n"
            "sceneStatus=WHOLE piecesEmitted=3/3\n"
            "witnessStatus=REAL overheardStatus=HEARD "
            "overheardTellText=She-saw-him-do-it-and-she-knows-his-face.\n"
            % noon,
    }
    tree = _tree(_fixture_files(today.isoformat(), played))
    code_p, tp, fp = run_once(tree, today, dry_run=True, quiet=True)
    hits = fp["outcomes"]["hits"]
    ok("a planted verdict dated today names an outcome and the brief LEADS with "
       "it (%s, %d key(s) of %d, ranked %s)"
       % (hits[0]["token"] if hits else "nothing measured",
          len(set(h["token"] for h in hits)), len(OUTCOMES),
          fp["outcomes"]["chosenBy"]),
       code_p == 0 and hits and hits[0]["token"] == "overheardStatus=HEARD"
       and hits[0]["sentence"].lower() in tp.splitlines()[0].lower(),
       (code_p, tp))
    ok("and the planted ladder's one current rung is where it says the project "
       "stands (rung %s of %d)"
       % (fp["ladder"]["current"]["rung"] if fp["ladder"]["current"]
          else "nothing measured", fp["ladder"]["total"]),
       fp["ladder"]["current"] is not None
       and "a door that opens" in tp.splitlines()[0], tp.splitlines()[0])
    ok("and the spoken line the planted game composed is quoted, undashed "
       "(quoteInBrief=%d trimmed=%s)"
       % (fp["quote_ok"], ",".join(fp["trimmed"]) or "none"),
       "She saw him do it and she knows his face." in tp, tp)
    # A COMMENT MAY NOT WRITE A KEY. The same planted file carries
    # crimeStatus=COMMITTED on a hash line only, and the crime sentence must be
    # nowhere in the brief: this is queue 064's rule, and the live tree is where
    # it actually bites (grateRectStatus=MEASURED sits on a comment in
    # ue-walk-verdict.txt while the live key says OFF-FRAME, which is the
    # RECTANGLE PAIR's status and not the grate's; see the note above).
    crime = dict(OUTCOMES)["crimeStatus=COMMITTED"]
    ok("an outcome key on a COMMENT line is not an outcome (%d comment line(s) "
       "skipped)" % fp["outcomes"]["commentLines"],
       fp["outcomes"]["commentLines"] >= 2
       and not any(h["token"] == "crimeStatus=COMMITTED" for h in hits)
       and crime not in tp, [h["token"] for h in hits])
    # THE SAME KEY WITH TWO VALUES IN ONE FILE IS NOT AN OUTCOME.
    two = dict(played)
    two["production/d1-probe/made-up-verdict.txt"] = (
        "# planted probe deadbeef @%d\n"
        "witnessStatus=REAL\nwitnessStatus=NOTHING-SEEN\n" % noon)
    t2 = _tree(_fixture_files(today.isoformat(), two))
    code_c, tc, fc = run_once(t2, today, dry_run=True, quiet=True)
    ok("a key carrying two different values in one file is DROPPED and named "
       "(%s)" % (fc["outcomes"]["contradicted"][0]
                 if fc["outcomes"]["contradicted"] else "nothing measured"),
       code_c == 0 and fc["outcomes"]["contradicted"]
       and not fc["outcomes"]["hits"]
       and "Nothing measured about what changed for the game" in tc,
       (fc["outcomes"], tc))
    # TWO CURRENT RUNGS IS THE FILE'S OWN CONTRACT BROKEN, and the honest answer
    # is nothing measured rather than the first of the two.
    broke = dict(played)
    broke["production/ladder.md"] = broke["production/ladder.md"].replace(
        "| 3 | A face that moves | next |", "| 3 | A face that moves | current |")
    t3 = _tree(_fixture_files(today.isoformat(), broke))
    code_l, tl, fl = run_once(t3, today, dry_run=True, quiet=True)
    ok("a ladder with two current rows reads as nothing measured, names the "
       "count, and the brief still writes (%s)" % fl["ladder"]["why"],
       code_l == 0 and fl["ladder"]["current"] is None
       and "nothing measured about where the ladder stands" in tl
       and "2-of-3-rows-say-current" in fl["ladder"]["why"], (code_l, tl))
    # THE TWO NEW GATES ACTUALLY REFUSING, because a gate whose refusal branch
    # nothing ever runs is decoration (CLAUDE.md rule 6) and because the old
    # headline rule's whole failure was that the only thing calling it was a
    # test asserting it passed. THE CONDITION IS PLANTED, never loosened: the
    # composer is wrapped for one call and the wrapper puts the exact headline
    # Jafar rejected back into the message, or takes the denominator out of the
    # split sentence. Both wrappers are removed immediately afterwards.
    real_compose = globals()["compose"]

    def _with(mangle):
        def faked(root, t):
            txt, f = real_compose(root, t)
            txt = mangle(txt)
            f["lead_ok"], f["lead_reading"] = \
                leads_with_the_game(txt.splitlines()[0])
            f["split_ok"], f["split_reading"] = split_in_words(txt, f["split"])
            return txt, f
        return faked

    try:
        globals()["compose"] = _with(
            lambda t: "HEADLINE: Eighteen new pictures of the street since the "
                      "previous brief, and six decisions are waiting for you."
                      + t.split("\n", 1)[1])
        code_h, _th, fh = run_once(tree, today, dry_run=True, quiet=True)
        ok("run_once REFUSES the count headline and writes nothing (exit %d, "
           "%d register finding(s), so it refused at the headline gate and not "
           "before it)" % (code_h, len(fh.get("check", {}).get("findings", []))),
           code_h == 1 and not fh["lead_ok"]
           and not fh.get("check", {}).get("findings"), (code_h, fh["lead_ok"]))
        globals()["compose"] = _with(
            lambda t: re.sub(
                r"\bOf [a-z\- ]+ sessions? since the previous brief, ", "",
                t.replace("No sessions at all since the previous brief, so "
                          "the studio", "The studio")))
        code_d, _td, fd = run_once(tree, today, dry_run=True, quiet=True)
        ok("run_once REFUSES a split sentence with no denominator, which the "
           "register itself passes (exit %d, %d register finding(s))"
           % (code_d, len(fd.get("check", {}).get("findings", []))),
           code_d == 1 and not fd["split_ok"]
           and not fd.get("check", {}).get("findings"),
           (code_d, fd.get("split_reading")))
    finally:
        globals()["compose"] = real_compose
    code_back, _tb, fb2 = run_once(tree, today, dry_run=True, quiet=True)
    ok("and the unwrapped composer passes both gates again (exit %d, leadOk=%s "
       "splitReported=%s)" % (code_back, fb2["lead_ok"], fb2["split_ok"]),
       code_back == 0 and fb2["lead_ok"] and fb2["split_ok"], code_back)

    # THE SERIES BEHIND DETAIL_MAX_WORDS, printed from the LIVE ladder so the
    # bound can be re-read off real rows rather than defended from memory.
    live_rungs = read_ladder(REPO)[0]["rows"]
    series = [len(re.split(r"(?<=[.!?])\s+", r["done_looks_like"])[0].split())
              for r in live_rungs]
    ok("the live ladder's done-looks-like sentences measure %s word(s) against "
       "the bound of %d, so the bound admits %d of %d and refuses %d"
       % ("/".join(str(n) for n in series) or "nothing measured",
          DETAIL_MAX_WORDS, sum(1 for n in series if n <= DETAIL_MAX_WORDS),
          len(series), sum(1 for n in series if n > DETAIL_MAX_WORDS)),
       bool(series) and any(n <= DETAIL_MAX_WORDS for n in series)
       and any(n > DETAIL_MAX_WORDS for n in series), series)
    # EVERY SENTENCE IN THE TABLE, AGAINST THE REGISTER'S OWN BAN LIST. A new
    # row saying "the crime was committed" would redden the morning, because
    # `commit` is on the run-internals list, and the brief would refuse itself.
    bad_rows = [tok for tok, s in OUTCOMES
                if [f for f in pc.check(s, "answer")["findings"]
                    if f.rule != "linkfloor"]]
    ok("all %d outcome sentence(s) survive the register's ban list (%d refused)"
       % (len(OUTCOMES), len(bad_rows)), not bad_rows, bad_rows)

    # WORDS, both ends, because the whole message is built out of this.
    ok("counts read as words: %s / %s / %s / %s"
       % (in_words(0), in_words(1), in_words(21), in_words(115)),
       (in_words(0), in_words(1), in_words(21), in_words(115))
       == ("no", "one", "twenty-one", "one hundred and fifteen"),
       (in_words(0), in_words(21), in_words(115)))

    # THE CLOSING LINE IS SHAPED FOR ledger/verify.py's EXISTING READER, which
    # greps `selftest: (\d+) passed, (\d+) failed` (see its decal-ink check).
    # Nothing in verify.py or CI runs this selftest as of 2026-09-09, which is
    # the rule-6 hole queue 179's report names; this line is so the wiring is a
    # copy of a pattern already in the file rather than a new parser.
    print("\nmorning-brief --selftest: %d passed, %d failed, over 1 live tree "
          "and %d planted tree(s) verdict=%s"
          % (passed, len(failed), _TREES_BUILT[0],
             "PASS" if not failed else "FAILED"))
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
    # RETIRED 2026-09-09, AND THE REFUSAL IS HERE RATHER THAN IN A COMMENT.
    # A banner does not stop a program: this one wrote into
    # production/briefs/, which is where the Producer's own message now goes,
    # so a stray run would put a generated file where a written one belongs
    # and the send path would send whichever it found. Exit 5, its own code,
    # so a caller that still exists reads as red rather than as a working run.
    print("morning-brief: RETIRED 2026-09-09 by Jafar's ruling. Nothing was "
          "read and nothing was written; 0 brief(s) composed. One Producer "
          "turn a day writes production/briefs/<day>.md now: gather with "
          "tools/producer-day.py, check with tools/producer-check.py, send "
          "with tools/runner/telegram-bot.py --send-brief.")
    return 5
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
