#!/usr/bin/env python3
"""A PRODUCER MESSAGE, AGAINST THE RULED REGISTER, BEFORE IT REACHES JAFAR.

    python3 tools/producer-check.py MESSAGE.md          # unprompted, 120 words
    python3 tools/producer-check.py --kind brief FILE    # morning brief, 150
    python3 tools/producer-check.py --kind answer FILE   # he asked; length follows
    python3 tools/producer-check.py -                    # read stdin
    python3 tools/producer-check.py --selftest           # accepting case FIRST

WHY IT EXISTS. Jafar ruled on 2026-09-03 that the Producer is the only voice
that addresses him, and ruled its register. A register that lives only in an
agent file is a preference: the next session writes a 400 word message with
four file paths in it, nothing objects, and the rule quietly stops existing.
This is the half that objects.

WHAT IT CAN AND CANNOT SEE, said out loud rather than skipped, because a check
whose silence reads as a clean bill is the fault this project keeps paying
for. It is MECHANICAL. It counts words, matches tokens, and decides whether a
sentence has the SHAPE of a claim. It cannot tell whether a claim is TRUE,
whether the link behind it actually shows what the sentence says, or whether
the recommendation is any good. Those need the director. The report says so at
the bottom rather than implying the absence of a finding is approval.

THE LINK BAND, ruled by Jafar 2026-09-06 after a message with ten repository
links passed this check: ONE link at least (constitution law 12), TWO at most,
and the only destinations are the glance, the map and the gallery. A picture
goes to him as a Telegram image, never as a link. Rules ruled after a message
was written do not apply to it, and the mechanism is a FROZEN LIST OF NAMES
(see LEGACY_LINK_RULES), never the date in a filename: the date at the front of
a name is typed by the writer, so a date switch lets the specimen choose its
own rulebook. The three already-sent messages are named; today's is not.

THE REGISTERS. UNPROMPTED and BRIEF get the shape, the cap, the ban list and
the link floor. ANSWER gets the ban list and the link rules only, because
Jafar's question sets the length and a question asking for a number is
answered with the number. Every register PRINTS the rules it did not enforce,
by name: a skipped check that prints nothing is indistinguishable from a
passing one.

EXIT CODES, distinct per outcome. 0 the message may be sent. 1 it may not, and
every finding is named. 2 there was no message to read (missing file, empty
stdin), which is not a pass. 3 the selftest failed. 4 tools/capsay.py could not
be imported: this program refuses to report a truncated finding list without
the one implementation of the truncation notice.
"""
import argparse
import datetime
import importlib.util
import pathlib
import re
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


# ONE IMPLEMENTATION PER IDEA. The truncation notice already exists in this
# repo and is imported, never re-typed.
_capsay = _load(REPO / "tools" / "capsay.py", "capsay")
if _capsay is None:
    sys.stderr.write("producer-check: tools/capsay.py could not be imported; "
                     "refusing to print a finding list with no truncation "
                     "notice behind it\n")
    sys.exit(4)
cap, NOTHING = _capsay.cap, _capsay.NOTHING_MEASURED

FINDINGS_SHOWN = 3      # per rule. cap() announces when it bites.

# ---------------------------------------------------------------- the register

CAP_UNPROMPTED = 120
CAP_BRIEF = 150
MIN_DEADLINE_HOURS = 24
MIN_OPTIONS, MAX_OPTIONS = 2, 4

SECTIONS = ["HEADLINE", "WHAT CHANGED", "NEEDS YOU", "NEXT VISIBLE THING",
            "BUDGET"]

# The rules, by name, so a register can say which of them it enforces and the
# report can print the ones it did not.
RULES = ["wordcap", "shape", "options", "deadline", "nextvisible",
         "banned", "linkfloor", "linkcap", "linkdest", "split"]
# THE SPLIT IS THE BRIEF'S ALONE. Jafar's standing order of 2026-09-05 says
# EVERY BRIEF reports the studio versus game split; it says nothing about an
# unprompted message or an answer, and a rule applied where it was not ruled is
# a rule somebody switches off. Named in `not_enforced` in the other two
# registers rather than silently absent.
RULES_BRIEF_ONLY = ("split",)
REGISTERS = {
    "unprompted": (CAP_UNPROMPTED,
                   [r for r in RULES if r not in RULES_BRIEF_ONLY]),
    "brief": (CAP_BRIEF, RULES),
    # ANSWER: his question sets the length, so the cap and the shape are not
    # enforced and are NAMED as not enforced. The ban list and the link floor
    # still bind, minus counts: a question asking how many is answered with
    # how many.
    # THE TWO LINK RULES BIND IN EVERY REGISTER. Jafar ruled them of "a
    # message", not of a kind: "at most two links per message, and never to a
    # repo markdown file". A cap that an answer could escape is a cap the next
    # long answer escapes.
    "answer": (None, ["banned", "linkfloor", "linkcap", "linkdest"]),
}
# THE THREE MESSAGES WRITTEN BEFORE THE LINK BAND WAS RULED, BY NAME.
#
# Jafar ruled the band on 2026-09-06. Three messages were already written and
# sent under the register as it stood, whose destination rule was a host
# allowlist. Grading them against a rule that did not exist would turn them red
# in ledger/verify.py, delete the footer and block every commit until somebody
# edited a message that was correct when it was sent, which is queue item 077's
# failure one rule further on.
#
# WHY A NAME AND NOT A DATE, ruled 2026-09-06 after the first version of this
# used the ISO date at the front of the filename as the switch. THE GATE WOULD
# HAVE READ ITS RULEBOOK OFF THE SPECIMEN: that date is typed by the writer, so
# a file named 2026-09-05-x.unprompted.md written next week would be graded with
# no link cap and the retired host list. The defence offered for it ("changing a
# filename takes a reviewed diff") does not hold, because outbox messages commit
# on the resident's read under the narrowing of 2026-09-06. The same argument is
# already written down at PRE_REGISTER below, for the same reason.
#
# THIS TUPLE MAY NEVER GAIN A MEMBER WHOSE FILENAME DATE IS ON OR AFTER
# 2026-09-06, and it widens only in a reviewed diff. The selftest asserts the
# first half on every run. No marker line goes inside these messages: they are
# the record of what was written, and the gate's own per-file line
# (pass-legacy-links) is the reader-visible half.
LEGACY_LINK_RULES = (
    "production/outbox/2026-09-03-batch-landed-and-the-wait.unprompted.md",
    "production/outbox/2026-09-05-the-console-run.unprompted.md",
    "production/briefs/2026-09-05.md",
)

# DOCUMENTATION, AND IT SELECTS NO RULE. The band was ruled on this date; the
# only code that reads it is the selftest assertion that no name above is dated
# on or after it. Nothing in check() or gate() branches on a date.
LINK_BAND_RULED_ON = datetime.date(2026, 9, 6)

# ENFORCED IN EVERY REGISTER WHEN A NEEDS YOU SECTION IS PRESENT, ruled
# 2026-09-03. An answer has no cap and no required shape, but the moment it
# carries a decision it carries Jafar's floor with it: two to four options, a
# recommendation, a default, and a deadline no shorter than 24 hours. Without
# this a decision buried in a long answer escapes the default and the floor,
# which is the failure the decision queue exists to end.
RULES_IF_NEEDS_YOU = ["options", "deadline"]
# THE TWO RULES THE LINK BAND ADDED on 2026-09-06, named once so the legacy
# switch and the report cannot come to disagree about which rules it covers.
LINK_BAND_RULES = ("linkcap", "linkdest")
# Counts are legitimate in an answer and only there. Named as its own set
# rather than hidden inside the register tuple, so the exemption is greppable.
COUNTS_ALLOWED_IN = {"answer"}

# WHERE A LINK MAY POINT, RULED BY JAFAR 2026-09-06, verbatim: "images are
# sent as Telegram images, never as links; at most two links per message, and
# never to a repo markdown file, only to the glance, map or gallery".
#
# SO THE ALLOWLIST IS THREE PAGES, NOT A HOST. It used to be a host list, and
# that is exactly the hole: production/outbox/2026-09-05-the-console-run.
# unprompted.md carried fifteen URLs, thirteen of them to github.com and eight
# of those to repository markdown files, and this program printed SEND. That
# pass is the measurement this rule was written from, taken 2026-09-06 before
# the change: urls=15 goodLinks=13 findings=0.
#
# AN IMAGE IS NOT A LINK EITHER. A blob link to a .png is still a link to the
# repository, so it fails `linkdest` like any other; the picture goes to him as
# a Telegram image, which is the sender's job and not this program's.
SITE_ORIGIN = "https://jsab258.github.io/wc26-picks/"
# (path under the origin, what to call it in a finding). The empty path is the
# glance itself. Adding a page here is the ONE place the allowlist grows.
SITE_PAGES = (("", "the-glance"),
              ("map.html", "the-map"),
              ("gallery.html", "the-gallery"))
# THE BAND, not a floor: one link at least (constitution law 12, evidence) and
# two at most (Jafar, 2026-09-06). Both ends are his, neither is measured, and
# both are cited rather than chosen.
LINK_MIN, LINK_MAX = 1, 2

# THE RETIRED DESTINATION LIST, kept because the link FLOOR is older than the
# band and the three named messages satisfied the floor with the destinations
# that existed when they were written. It governs ONLY the files named in
# LEGACY_LINK_RULES and it can never widen. Without it, changing what "an
# allowed link" MEANS would fail those three through the oldest rule in the
# file rather than through the new one.
LEGACY_LINK_HOSTS = ("github.com", "raw.githubusercontent.com")
LINK_RE = re.compile(r"https?://[^\s<>()\[\]]+")
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")

# ------------------------------------------------------------------- banned
# Each pattern runs over the SCRUBBED text (links removed), because the links
# are the evidence floor and a path check that fires on a required URL would
# make the two rules contradict each other.

KNOWN_DIRS = ("production", "tools", "ledger", "ledger-v2", "game-design",
              ".claude", "research", "legacy", "docs", "assets")
EXT_RE = re.compile(r"\.(md|py|cs|json|txt|html?|ya?ml|jpe?g|png|bat|sh|tsv|"
                    r"csv|uasset|umap)\b", re.I)
SLASHED_RE = re.compile(r"(?<![\w/])(?:[\w.@#-]+/)+[\w.@#-]+")


def find_paths(text):
    """File paths and directory names. A slashed token counts as a path when it
    carries a file extension, or has two or more slashes, or begins with a
    directory this repo actually has. `and/or` and `24/7` are neither, and a
    check that flagged them would be overruled by its second user."""
    out = []
    for m in SLASHED_RE.finditer(text):
        tok = m.group(0)
        if (EXT_RE.search(tok) or tok.count("/") >= 2
                or tok.split("/")[0].lower() in KNOWN_DIRS):
            out.append(tok)
    for m in re.finditer(r"(?<![\w/])[\w.-]*" + EXT_RE.pattern, text, re.I):
        tok = m.group(0)
        if tok not in out:
            out.append(tok)
    return out


BANNED = [
    ("verdict key",
     lambda t: [m.group(0) for m in
                re.finditer(r"(?<![\w=])[A-Za-z][\w-]*=[^\s]+", t)]),
    ("run internals",
     lambda t: [m.group(0) for m in re.finditer(
         r"\b(workflow|workflows|runner|runners|dispatch\w*|sha|shas|commit\w*|"
         r"branch\w*|CI\b|job|jobs|verdict\w*|gate|gates|exit code|selftest\w*|"
         r"stack trace|pull request|PR\b|repo|repository|grep\w*|log file|"
         r"artifact ID)\b", t, re.I)]),
    ("tool narration",
     lambda t: [m.group(0) for m in re.finditer(
         r"\b(I (?:ran|checked|opened|grepped|read|looked at|verified|re-ran|"
         r"rebuilt|kicked off)|let me\b|I'?ll now\b|I have (?:run|checked)|"
         r"I am (?:running|checking))", t, re.I)]),
    ("heartbeat",
     lambda t: [m.group(0) for m in re.finditer(
         r"\b(still working|still going|quick update|status update|"
         r"checking in|just a moment|no news|nothing to report|as promised|"
         r"as an update|touching base)\b", t, re.I)]),
    ("self-correction",
     lambda t: [m.group(0) for m in re.finditer(
         r"\b(I was wrong|my mistake|apolog\w+|sorry\b|earlier I said|"
         r"correction:|to correct|it turns out I|I had assumed|I misread|"
         r"I should have)\b", t, re.I)]),
    ("file path", find_paths),
]

# ------------------------------------------------------- counts, and the forms
# that are NOT counts. Order matters: each scrub removes a legitimate numeral
# form before the next one looks, so what survives to the end is a count.
PRODUCT_NUMERALS = (r"\bGTA\s?6\b", r"\bGTA\s?5\b", r"\bKCD\s?2\b")
NUMERAL_OK = [
    ("ISO date", r"\b\d{4}-\d{2}-\d{2}\b"),
    ("clock time", r"\b\d{1,2}[:.]\d{2}\s?(?:am|pm)?\b"),
    ("named-month date", r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|"
                        r"March|April|May|June|July|August|September|October|"
                        r"November|December)\b"),
    ("month-named date", r"\b(?:January|February|March|April|May|June|July|"
                         r"August|September|October|November|December)\s+"
                         r"\d{1,2}(?:st|nd|rd|th)?\b"),
    ("money", r"[£$€]\s?\d[\d,]*(?:\.\d+)?k?\b|\b\d+\s?(?:pounds?|quid)\b"),
    ("duration", r"\b\d+(?:\.\d+)?\s?(?:minute|hour|day|week|month|year)s?\b"),
    ("list label", r"(?m)^\s*\d{1,2}[.)]\s"),
    ("product name", "|".join(PRODUCT_NUMERALS)),
]
NUMERAL_RE = re.compile(r"(?<![\w-])\d[\d,]*(?:\.\d+)?%?(?![\w])")


def find_counts(text):
    """Bare quantities. Dates, clock times, money, durations, numbered list
    labels and product names carry digits and are not counts; what is left
    after those are scrubbed is '563 of 593' and '72 gates', which are the
    shape Jafar ruled out of his messages."""
    t = text
    # A PATH IS ONE VIOLATION, NOT TWO. `production/queue/062-uv.md` was being
    # reported as a path AND as the count 062, which trains a reader to skim
    # the finding list. The path rule owns it.
    for tok in find_paths(t):
        t = t.replace(tok, " " * len(tok))
    for _, pat in NUMERAL_OK:
        t = re.sub(pat, lambda m: " " * len(m.group(0)), t, flags=re.I)
    return [m.group(0) for m in NUMERAL_RE.finditer(t)]


# ------------------------------------------------------------- claim detection
ASSERTION_RE = re.compile(
    r"\b(is|are|was|were|isn'?t|aren'?t|has|have|had|does|did|"
    r"landed|shipped|works|working|failed|passed|broke|broken|fixed|added|"
    r"removed|started|stopped|finished|stalled|runs|ran|renders|rendered|"
    r"built|wired|measured|chose|ruled|holds|stands|sits)\b", re.I)
# Lines that propose, label or structure rather than assert. A recommendation
# is an argument for a choice, not a claim about the world, and a check that
# demanded a link on `DEFAULT B if unruled` would teach link-stuffing.
NON_CLAIM_PREFIX = re.compile(
    r"^\s*(?:[-*>]\s*)?(?:%s|RECOMMENDATION|RECOMMEND|DEFAULT|DEADLINE|"
    r"OPTION|[A-D][.)]\s|\d{1,2}[.)]\s|#)" % "|".join(SECTIONS), re.I)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def sentences(text):
    """(line-relative sentence, its section) for every sentence in the body."""
    out, section = [], "(before any section)"
    for line in text.splitlines():
        head = section_label(line)
        if head:
            section = head
            # THE PREFIX CONTEXT IS THE LINE MINUS ITS LABEL. Passing the whole
            # line made every section-opening sentence non-claim-shaped,
            # because the label itself matched the non-claim prefix: HEADLINE
            # carries the headline, which is the most claim-shaped sentence in
            # the message, and the first selftest run caught 1 claim in 18
            # sentences because of it.
            body = line.split(":", 1)[1] if ":" in line else ""
        else:
            body = line
        for s in SENTENCE_SPLIT.split(body):
            s = s.strip()
            if s:
                out.append((s, section, body))
    return out


def section_label(line):
    """The section this line OPENS, or None. A label is the line's start, in
    capitals, optionally after a markdown heading or bullet mark."""
    t = re.sub(r"^[\s#*>-]+", "", line).strip()
    for name in SECTIONS:
        if t.upper().startswith(name):
            return name
    return None


def claim_shaped(sentence, whole_line):
    """Does this sentence ASSERT something about the world?

    Mechanical, and the definition is printed in the report so nobody has to
    read this function to audit a finding. A sentence is claim-shaped when all
    three hold: it is not a question, its line does not begin with a section
    label or an option / recommendation / default / deadline marker, and it
    contains a finite assertion verb from the list above. Everything else is a
    proposal, a label or a fragment, and none of those is a claim.
    """
    if sentence.rstrip().endswith("?"):
        return False
    if NON_CLAIM_PREFIX.match(whole_line):
        return False
    return bool(ASSERTION_RE.search(sentence))


# ------------------------------------------------------------------- the check

class Finding:
    def __init__(self, rule, what, where=""):
        self.rule, self.what, self.where = rule, what, where

    def __str__(self):
        return "%s: %s%s" % (self.rule, self.what,
                             (" [%s]" % self.where) if self.where else "")


def scrub_links(text):
    """Text with every URL and markdown link target replaced by a spacer of
    the same length, so offsets stay honest and no ban pattern fires on the
    evidence the link floor REQUIRES."""
    t = MD_LINK_RE.sub(lambda m: "[%s](%s)" % (m.group(1),
                                               " " * len(m.group(2))), text)
    return LINK_RE.sub(lambda m: " " * len(m.group(0)), t)


def links_in(text):
    return LINK_RE.findall(text)


def site_page(url):
    """Which of the three published pages this URL IS, or None.

    Whole-URL matching, not host matching. `https://github.com/...blob/....md`
    and `https://jsab258.github.io/wc26-picks/map.html` differ only in the part
    a host check throws away, and throwing it away is what let ten repository
    links through on 2026-09-05."""
    u = url.split("#", 1)[0].rstrip("/")
    base = SITE_ORIGIN.rstrip("/")
    if u != base and not u.startswith(base + "/"):
        return None
    rest = u[len(base):].lstrip("/")
    for name, label in SITE_PAGES:
        if rest == name.rstrip("/"):
            return label
    return None


def link_ok(url, legacy_links=False):
    """May this URL appear? `legacy_links` is MEMBERSHIP OF A NAMED LIST, never
    a date: see LEGACY_LINK_RULES for why the specimen may not choose.

    ONE FUNCTION, TWO GENERATIONS. The retired generation is a SUPERSET: the
    ruling of 2026-09-06 REMOVED repository links, it did not remove the site,
    so anything allowed today was allowed before and the tightening is
    monotone. False is the default, which is what every caller with no entry on
    the list must get."""
    if site_page(url) is not None:
        return True
    if legacy_links:
        host = re.sub(r"^https?://", "", url).split("/")[0].lower()
        return host in LEGACY_LINK_HOSTS
    return False


def link_rule_generation(legacy_links):
    """Which destination list applied, in words, for the report."""
    site = "-or-".join(lbl for _, lbl in SITE_PAGES)
    if legacy_links:
        return "legacy-by-name/%s-or-%s" % (site, "-or-".join(LEGACY_LINK_HOSTS))
    return "ruled-2026-09-06/%s-only" % site


def count_words(text):
    """Words = whitespace-separated tokens of the body, with URLs removed
    first. The cap must not charge the writer for the link the floor demands,
    or the two rules trade against each other and evidence loses."""
    stripped = MD_LINK_RE.sub(lambda m: m.group(1), text)
    stripped = LINK_RE.sub(" ", stripped)
    stripped = re.sub(r"^[\s#*>-]+", " ", stripped, flags=re.M)
    return [w for w in stripped.split() if re.search(r"\w", w)]


# NO INSTANT TO MEASURE FROM. Passed as `now` by the gate for a file whose
# name carries no date. It is a sentinel and not a datetime on purpose: a
# missing instant must reach the deadline rule as "unreadable" and come out as
# a finding, never as a quietly substituted wall clock.
UNPINNED = object()


def deadline_hours(line, now):
    """Hours from `now` to the deadline this line states, or None when no
    deadline form parses. None is reported as unparseable, never as fine."""
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", line)
    if m:
        try:
            d = datetime.date.fromisoformat(m.group(1))
        except ValueError:
            return None
        return (datetime.datetime.combine(d, datetime.time(9, 0))
                - now).total_seconds() / 3600.0
    m = re.search(r"\b(\d+(?:\.\d+)?)\s?(hour|day|week)s?\b", line, re.I)
    if m:
        mult = {"hour": 1, "day": 24, "week": 168}[m.group(2).lower()]
        return float(m.group(1)) * mult
    if re.search(r"\btomorrow\b", line, re.I):
        return 24.0
    return None


TIME_FORMS = re.compile(
    r"\b(unknown|tonight|tomorrow|\d{4}-\d{2}-\d{2}|"
    r"\d+\s?(?:minute|hour|day|week)s?|monday|tuesday|wednesday|thursday|"
    r"friday|saturday|sunday|this evening|this week|next week)\b", re.I)


# ------------------------------------------------------- the split sentence
# REQUIRED IN EVERY BRIEF, ruled by Jafar 2026-09-05 ("every brief reports the
# STUDIO VERSUS GAME split") and given its unit by the director ruling of the
# same day, section 6: the split is COUNTED IN SESSIONS and says so, because
# production/budget.md line 87 rules the turns-to-points conversion UNMEASURED
# and queue 076 is the rate that would fix it. A split in a unit nobody has
# measured is one number twice.
#
# WHY IT IS FIVE PARTS AND NOT ONE REGEX OVER A SENTENCE: a brief that names
# the studio and the game but calls the count points is exactly the failure the
# ruling refuses, and a single pattern that missed it would report the rule as
# passing. Each part is named in the finding, so a writer is told which half is
# missing rather than that "the split sentence" is wrong.
#
# `splitBasis=` IS A VERDICT KEY AND STAYS OUT OF THE MESSAGE. The ban list
# already refuses it; this rule requires the words, and tools/morning-brief.py
# prints the key on its own done line. Both halves ruled together, 2026-09-05.
SPLIT_PARTS = (
    ("the studio", re.compile(r"\bstudio\b", re.I)),
    ("the game", re.compile(r"\bgames?\b", re.I)),
    ("the unit, sessions", re.compile(r"\bsessions?\b", re.I)),
    ("the words 'not points'", re.compile(r"\bnot\s+points\b", re.I)),
    ("what makes it points later, 'measured'",
     re.compile(r"\bmeasured\b", re.I)),
)


def split_sections(text):
    """{label: body-lines} plus the order the labels appeared in."""
    bodies, order, current = {}, [], None
    for line in text.splitlines():
        head = section_label(line)
        if head:
            current = head
            order.append(head)
            rest = line.split(":", 1)[1] if ":" in line else ""
            bodies.setdefault(head, [])
            if rest.strip():
                bodies[head].append(rest.strip())
            continue
        if current:
            bodies[current].append(line)
    return bodies, order


def check(text, kind="unprompted", now=None, legacy_links=False):
    """Every reading this program takes, as data. PURE: takes text, returns a
    dict, touches no file. The selftest drives it with synthetic fixtures and
    the report function only formats what comes out of here.
    """
    # `now` may be a datetime, None (meaning the wall clock, which is what the
    # SINGLE-FILE check wants) or UNPINNED (no instant at all, which is what
    # the GATE passes for a file whose name carries no date). Written as an
    # identity test rather than `now or ...` so the sentinel cannot be
    # swallowed by a truthiness change later.
    if now is None:
        now = datetime.datetime.now()
    word_cap, enforced = REGISTERS[kind]
    # A DECISION CARRIES ITS FLOOR INTO ANY REGISTER. The answer register has
    # no cap and no required shape, but the moment a message carries a NEEDS
    # YOU section it carries Jafar's options-and-deadline floor with it, or a
    # decision buried in a long answer escapes the 24-hour default he ruled.
    # Read off the same section parser the rest of this function uses, so the
    # trigger cannot drift from what the reader sees.
    _bodies_probe, _ = split_sections(text)
    needs_you_present = bool(_bodies_probe.get("NEEDS YOU"))
    if needs_you_present:
        enforced = list(enforced) + [r for r in RULES_IF_NEEDS_YOU
                                     if r not in enforced]
    # THE LINK BAND DOES NOT APPLY TO THE THREE MESSAGES WRITTEN BEFORE IT WAS
    # RULED, and membership of that list is decided BY NAME by the caller (the
    # gate) rather than by anything inside the text. `now` selects no rule at
    # all: it measures deadlines and nothing else.
    if legacy_links:
        enforced = [r for r in enforced if r not in LINK_BAND_RULES]
    words = count_words(text)
    scrubbed = scrub_links(text)
    found, notes = [], []
    urls = links_in(text)
    # EVERY DESTINATION TEST IN THIS FUNCTION READS THE SAME INSTANT. A second
    # call site using today's list while the first used the dated one would
    # report a message as both compliant and not.
    good_links = [u for u in urls if link_ok(u, legacy_links)]

    # 1. THE WORD CAP.
    if "wordcap" in enforced and len(words) > word_cap:
        found.append(Finding("wordcap", "%d words over the %d cap (%d words)"
                             % (len(words) - word_cap, word_cap, len(words))))

    # 2. THE BANNED TOKENS.
    banned_checked = 0
    if "banned" in enforced:
        rules = list(BANNED)
        if kind not in COUNTS_ALLOWED_IN:
            rules.append(("count", find_counts))
        else:
            notes.append("counts are permitted in the %s register (his "
                         "question sets what is answered), so that pattern "
                         "did not run" % kind)
        banned_checked = len(rules)
        for label, fn in rules:
            hits = fn(scrubbed)
            if hits:
                found.append(Finding("banned:" + label,
                                     cap(hits, keep=FINDINGS_SHOWN, width=40,
                                         sep=", ")))

    # 3. THE LINK FLOOR.
    sents = sentences(text)
    claims = [(s, sec, ln) for s, sec, ln in sents if claim_shaped(s, ln)]
    if "linkfloor" in enforced:
        # UNCONDITIONAL for the unprompted and brief registers, ruled
        # 2026-09-03. It used to fire only `if claims and not good_links`, so
        # the one rule carrying constitution law 12 was the PERMISSIVE one
        # while the stylistic bans were aggressive: a message whose claims the
        # verb list failed to recognise sailed through with no link at all.
        # Claim detection under-flags by construction (a closed verb list
        # cannot see "the street looks right"), so hanging the evidence floor
        # off it inherited that blindness. The floor now asks only whether a
        # message that says anything carries a link.
        if len(good_links) < LINK_MIN:
            where = "; ".join(u for u in urls[:2]) or "no URL at all"
            found.append(Finding(
                "linkfloor",
                "no link to the glance, the map or the gallery (%s). %d "
                "sentence(s) read "
                "as claim-shaped, and the floor does NOT depend on that count: "
                "law 12 requires the evidence behind any message that speaks. "
                "First claim, if any: %s" % (
                    where, len(claims),
                    cap([claims[0][0]], keep=1, width=60) if claims
                    else "none recognised, which is not the same as none")))
    # ADVISORY, never a rejection: the ruled floor is one link in the message.
    # Per-section linkage is the stronger reading of "every claim links", and
    # it is printed with its denominator so a bound can be read off real
    # messages later rather than guessed at now.
    linked_sections = {sec for sec, in [(s,) for s in []]}
    by_section = {}
    for s, sec, ln in sents:
        by_section.setdefault(sec, []).append(s)
    linked_sections = {sec for sec, ss in by_section.items()
                       if any(link_ok(u, legacy_links) for t in ss
                              for u in links_in(t))}
    # links live on the LINE, not the sentence, so re-derive from lines
    linked_sections = set()
    cur = "(before any section)"
    for line in text.splitlines():
        head = section_label(line)
        if head:
            cur = head
        if any(link_ok(u, legacy_links) for u in links_in(line)):
            linked_sections.add(cur)
    unlinked_claims = [c for c in claims if c[1] not in linked_sections]

    # 3b. THE LINK BAND AND THE DESTINATION, ruled 2026-09-06. The floor above
    # counts SITE links; these two count every URL in the message, because "at
    # most two links" is about what he has to read past, not about which of
    # them are good ones.
    if "linkcap" in enforced and len(urls) > LINK_MAX:
        found.append(Finding(
            "linkcap",
            "%d link(s), %d over the ruled cap of %d per message. Ruled "
            "2026-09-06: at most two links, everything else said in plain "
            "words. Over the cap: %s"
            % (len(urls), len(urls) - LINK_MAX, LINK_MAX,
               cap(urls[LINK_MAX:], keep=FINDINGS_SHOWN, width=60, sep=" | "))))
    if "linkdest" in enforced:
        offsite = [u for u in urls if not link_ok(u, legacy_links)]
        if offsite:
            found.append(Finding(
                "linkdest",
                "%d of %d link(s) point somewhere other than the glance, the "
                "map or the gallery. Ruled 2026-09-06: never to a repository "
                "markdown file, and a picture goes to him as a Telegram image "
                "rather than as a link. Offending: %s"
                % (len(offsite), len(urls),
                   cap(offsite, keep=FINDINGS_SHOWN, width=60, sep=" | "))))

    # 4. THE SHAPE.
    bodies, order = split_sections(text)
    if "shape" in enforced:
        missing = [s for s in SECTIONS if s not in bodies]
        if missing:
            found.append(Finding("shape", "missing section(s): %s"
                                 % cap(missing, keep=5, sep=", ")))
        seen = [s for s in order if s in SECTIONS]
        first_seen = []
        for s in seen:
            if s not in first_seen:
                first_seen.append(s)
        wanted = [s for s in SECTIONS if s in first_seen]
        if first_seen != wanted:
            found.append(Finding("shape", "sections out of order: got %s, "
                                          "ruled order is %s"
                                 % ("/".join(first_seen), "/".join(wanted))))

    # 5. THE NEEDS YOU ITEMS.
    items = needs_you_items(bodies.get("NEEDS YOU", []))
    if "options" in enforced:
        for i, item in enumerate(items, 1):
            n = len(item["options"])
            if not (MIN_OPTIONS <= n <= MAX_OPTIONS):
                found.append(Finding("options", "item %d has %d option(s), "
                                     "ruled range is %d..%d"
                                     % (i, n, MIN_OPTIONS, MAX_OPTIONS)))
            for need in ("recommendation", "default"):
                if not item[need]:
                    found.append(Finding("options", "item %d states no %s"
                                         % (i, need)))
    if "deadline" in enforced:
        for i, item in enumerate(items, 1):
            if not item["deadline"]:
                found.append(Finding("deadline", "item %d states no deadline"
                                     % i))
                continue
            if now is UNPINNED:
                # A DEADLINE NOBODY CAN MEASURE IS NOT A DEADLINE THAT PASSED.
                # The gate pins its clock to the date in the filename; a name
                # with no date leaves it nothing to measure from, and the
                # honest outcome is a finding naming the fix rather than a
                # silent skip. This is what stops "drop the date from the
                # filename" becoming the way round the floor.
                found.append(Finding("deadline", "item %d states a deadline "
                                     "and this file's name carries no date to "
                                     "measure it from, so the %d-hour floor "
                                     "could not be read at all. Name the file "
                                     "<YYYY-MM-DD>-<slug>.<kind>.md"
                                     % (i, MIN_DEADLINE_HOURS)))
                continue
            hrs = deadline_hours(item["deadline"], now)
            if hrs is None:
                found.append(Finding("deadline", "item %d states a deadline "
                                     "this check cannot parse: %s"
                                     % (i, cap([item["deadline"]], keep=1,
                                               width=50))))
            elif hrs < MIN_DEADLINE_HOURS:
                found.append(Finding("deadline", "item %d gives %.1f hour(s), "
                                     "under the ruled %d"
                                     % (i, hrs, MIN_DEADLINE_HOURS)))

    # 6. NEXT VISIBLE THING: a measured time, or the word unknown. Never a
    # padded guess, and never a blank, which reads as unknown without saying so.
    if "nextvisible" in enforced:
        body = " ".join(bodies.get("NEXT VISIBLE THING", [])).strip()
        if "NEXT VISIBLE THING" in bodies and not TIME_FORMS.search(body):
            found.append(Finding("nextvisible",
                                 "neither a time nor the word unknown: %s"
                                 % (cap([body], keep=1, width=60) if body
                                    else "the section is empty")))

    # 7. THE STUDIO VERSUS GAME SPLIT, in the BUDGET section, in words. Brief
    # register only. Every zero here ships its denominator: the finding names
    # how many of the five required parts were found and which are missing.
    split_found, split_missing = 0, [name for name, _ in SPLIT_PARTS]
    if "split" in enforced:
        budget_body = " ".join(bodies.get("BUDGET", [])).strip()
        split_missing = [name for name, rx in SPLIT_PARTS
                         if not rx.search(budget_body)]
        split_found = len(SPLIT_PARTS) - len(split_missing)
        if split_missing:
            found.append(Finding(
                "split",
                "the BUDGET section carries %d of %d required part(s) of the "
                "studio-versus-game split: missing %s. Jafar's standing order "
                "of 2026-09-05 requires the split in every brief, in words, "
                "counted in sessions, saying it is sessions and not points "
                "until the rate is measured"
                % (split_found, len(SPLIT_PARTS),
                   cap(split_missing, keep=5, sep=", ")),
                "BUDGET" if budget_body else "the section is empty"))

    return {
        # WHICH CLOCK PRODUCED THE DEADLINE READING, carried out of the pure
        # function so the report never has to guess which of the two callers
        # it is serving.
        "now": "unpinned/no-date-in-filename" if now is UNPINNED
               else now.isoformat(timespec="minutes"),
        "kind": kind, "cap": word_cap, "words": len(words),
        "sentences": len(sents), "claims": len(claims),
        "unlinked_claims": len(unlinked_claims),
        "unlinked_examples": [c[0] for c in unlinked_claims],
        "sections_found": [s for s in SECTIONS if s in bodies],
        "items": len(items), "urls": urls, "good_links": good_links,
        "link_min": LINK_MIN, "link_max": LINK_MAX,
        "offsite_links": [u for u in urls if not link_ok(u, legacy_links)],
        "link_generation": link_rule_generation(legacy_links),
        # WHICH of the three pages this message actually links, named. A
        # link accepted under the OLDER generation is not one of them, so it
        # contributes no label and is counted in `good_links` only.
        "site_labels": sorted({site_page(u) for u in good_links
                               if site_page(u) is not None}),
        # THE LINK BAND'S TWO RULES DID NOT APPLY TO THIS FILE, because it is
        # named in LEGACY_LINK_RULES. Printed, never silent: a rule skipped in
        # silence is indistinguishable from a rule that passed.
        "legacy_links": legacy_links,
        "split_found": split_found, "split_of": len(SPLIT_PARTS),
        "split_missing": split_missing,
        "banned_checked": banned_checked,
        "enforced": list(enforced),
        "not_enforced": [r for r in RULES if r not in enforced],
        "findings": found, "notes": notes,
    }


OPTION_RE = re.compile(r"^\s*(?:[-*]\s*)?([A-D])[.)]\s+\S")
REC_RE = re.compile(r"^\s*(?:[-*]\s*)?RECOMMEND", re.I)
DEF_RE = re.compile(r"^\s*(?:[-*]\s*)?DEFAULT", re.I)
DEAD_RE = re.compile(r"^\s*(?:[-*]\s*)?DEADLINE", re.I)


def needs_you_items(lines):
    """The NEEDS YOU section as items. An item ENDS at its DEADLINE line, which
    is the ruled last part of one; a trailing chunk with no deadline is still
    an item and is reported as missing one rather than dropped. A section whose
    body carries no option, no recommendation and no deadline is an EMPTY
    needs-you (the honest 'nothing needs you today') and yields no items."""
    items, cur = [], None

    def fresh():
        return {"options": [], "recommendation": None, "default": None,
                "deadline": None, "lines": []}

    for line in lines:
        if not line.strip():
            continue
        if cur is None:
            cur = fresh()
        cur["lines"].append(line)
        m = OPTION_RE.match(line)
        if m:
            cur["options"].append(m.group(1))
        if REC_RE.match(line):
            cur["recommendation"] = line.strip()
        if DEF_RE.match(line):
            cur["default"] = line.strip()
        if DEAD_RE.match(line):
            cur["deadline"] = line.strip()
            items.append(cur)
            cur = None
    if cur and (cur["options"] or cur["recommendation"] or cur["default"]):
        items.append(cur)
    return items


# ------------------------------------------------------------------- reporting

def report(r):
    """The report. Every zero here ships the denominator that produced it."""
    print("producer-check: register=%s" % r["kind"])
    if r["cap"] is None:
        print("  words: %d (no cap in this register; his question sets the "
              "length)" % r["words"])
    else:
        print("  words: %d of %d (URLs excluded from the count: the link floor "
              "requires them)" % (r["words"], r["cap"]))
    print("  examined: %d sentence(s), %d claim-shaped, %d NEEDS YOU item(s), "
          "%d section(s) of %d found (%s)"
          % (r["sentences"], r["claims"], r["items"], len(r["sections_found"]),
             len(SECTIONS), "/".join(r["sections_found"]) or NOTHING))
    print("  links: %d URL(s) of the ruled %d..%d, %d to the site (%s), %d "
          "elsewhere. The only three destinations allowed are %s under %s; a "
          "picture is sent as a Telegram image and never as a link"
          % (len(r["urls"]), r["link_min"], r["link_max"], len(r["good_links"]),
             "/".join(l for l in r["site_labels"] if l) or NOTHING,
             len(r["offsite_links"]),
             "/".join(lbl for _, lbl in SITE_PAGES), SITE_ORIGIN))
    print("  destination list applied: %s (the list is dated because the "
          "floor is older than today's ruling)" % r["link_generation"])
    print("  claim-shaped means: not a question, the line does not begin with "
          "a section label or an option / recommendation / default / deadline "
          "marker, and the sentence carries a finite assertion verb")
    if r["banned_checked"]:
        print("  ban list: %d pattern(s) run over the message with URLs "
              "removed" % r["banned_checked"])
    if "split" in r["enforced"]:
        print("  studio-versus-game split: %d of %d required part(s) found in "
              "BUDGET (%s). Ruled 2026-09-05: in words, counted in sessions, "
              "and not points until the rate is measured"
              % (r["split_found"], r["split_of"],
                 ", ".join(n for n, _ in SPLIT_PARTS)))
    if "deadline" in r["enforced"]:
        # TWO CALLERS, TWO CLOCKS, so neither may leave its instant implicit.
        # This path is the SINGLE-FILE check and its clock is the wall clock:
        # the question before sending is "is this deadline far enough away to
        # send", which is a question about now. The gate's clock is the date in
        # the file's own name, and it says so on its own line.
        print("  deadlines measured from %s, the wall clock unless --now was "
              "given: before sending, the question is about now" % r["now"])
    for n in r["notes"]:
        print("  note: %s" % n)
    if r["not_enforced"]:
        print("  NOT ENFORCED in this register, named rather than skipped in "
              "silence: %s%s"
              % (", ".join(r["not_enforced"]),
                 (" (%s: legacy link rules by name, this file is one of the "
                  "%d on the frozen LEGACY_LINK_RULES list in "
                  "tools/producer-check.py, written before the band was "
                  "ruled)" % (" and ".join(LINK_BAND_RULES),
                              len(LEGACY_LINK_RULES)))
                 if r["legacy_links"] else ""))

    if r["claims"]:
        print("  advisory, not a rejection: %d of %d claim-shaped sentence(s) "
              "sit in a section carrying no link (%s). The ruled floor is one "
              "link in the message; this is the series a stricter bound would "
              "be read off later"
              % (r["unlinked_claims"], r["claims"],
                 cap(r["unlinked_examples"], keep=2, width=40, sep=" | ")))
    else:
        print("  advisory: %s for per-section linkage, because no sentence in "
              "this message is claim-shaped" % NOTHING)

    print("")
    if not r["findings"]:
        print("  0 finding(s) over %d rule(s) enforced (%s) and %d word(s) "
              "examined" % (len(r["enforced"]), ",".join(r["enforced"]),
                            r["words"]))
        print("  MECHANICAL ONLY: nothing here read whether a claim is TRUE, "
              "whether the link shows what the sentence says, or whether the "
              "recommendation is any good. That is the director's read.")
        print("\nproducer-check: SEND register=%s rulesEnforced=%d/%d"
              % (r["kind"], len(r["enforced"]), len(RULES)))
        return 0
    shown = {}
    for f in r["findings"]:
        shown.setdefault(f.rule, []).append(str(f.what))
    print("  %d finding(s) over %d rule(s) enforced:" % (len(r["findings"]),
                                                         len(r["enforced"])))
    for rule in sorted(shown):
        print("    %-18s %s" % (rule, cap(shown[rule], keep=FINDINGS_SHOWN,
                                          width=110, sep=" | ")))
    print("\nproducer-check: DO NOT SEND register=%s rulesEnforced=%d/%d"
          % (r["kind"], len(r["enforced"]), len(RULES)))
    return 1


# ------------------------------------------------------------------- selftest

# THE ACCEPTING FIXTURE: a real compliant message about this project's real
# state on 2026-09-03, written in the ruled register. It is first, and it is
# the case that matters: the expensive failure here is a register check nothing
# survives, which would push every future message back to being written with no
# check at all.
GOOD = """HEADLINE: the town has textures again, and the street is worth a look.

WHAT CHANGED: the grey street now paints properly, and the first picture of it
is up. Everything else waited on that.
[the gallery](https://jsab258.github.io/wc26-picks/gallery.html)

NEEDS YOU: how close should strangers stand on a pavement?
A. Almost touching, a crowded market.
B. Normal British pavement distance.
C. Reserved, a town that keeps its distance.
RECOMMENDATION B, a working port town rather than a festival.
DEFAULT B if you say nothing.
DEADLINE 2026-09-07.
[where things stand](https://jsab258.github.io/wc26-picks/)

NEXT VISIBLE THING: a walk through that street, tomorrow evening.

BUDGET: £0 spent, well inside the month.
"""

# THE REJECTING FIXTURES ARE SYNTHETIC, every one of them, and none quotes a
# real message. A rejecting case pinned to a real asset breaks the day somebody
# fixes the asset.
BAD = {
    "banned:file path":
        GOOD.replace("the grey street now paints properly",
                     "production/queue/062-uv-chain.md is the blocker"),
    "banned:verdict key":
        GOOD.replace("Everything else waited on that.", "probeTest=PASS now."),
    "banned:count":
        GOOD.replace("Everything else waited on that.",
                     "563 of 593 objects carry textures."),
    "banned:run internals":
        GOOD.replace("Everything else waited on that.",
                     "The workflow went green on the runner."),
    "banned:tool narration":
        GOOD.replace("Everything else waited on that.",
                     "I checked the street myself."),
    "banned:heartbeat":
        GOOD.replace("Everything else waited on that.",
                     "Still working, quick update for you."),
    "banned:self-correction":
        GOOD.replace("Everything else waited on that.",
                     "My mistake, earlier I said it was done."),
    "wordcap":
        GOOD.replace("Everything else waited on that.",
                     "Everything else waited on that. " + ("and " * 130)),
    "linkfloor": re.sub(r"\[[^\]]*\]\([^)]*\)\n?", "", GOOD),
    # ONE MORE LINK THAN THE CAP, and it is a legal destination: the cap is
    # about how much he has to read past, not about where the links go, and a
    # fixture that broke both rules would prove neither.
    "linkcap": GOOD.replace(
        "NEXT VISIBLE THING: a walk through that street, tomorrow evening.",
        "NEXT VISIBLE THING: a walk through that street, tomorrow evening.\n"
        "[the map](https://jsab258.github.io/wc26-picks/map.html)"),
    # A REPOSITORY MARKDOWN LINK, which is exactly what Jafar rejected. The
    # other site link stays, so the floor is satisfied and only the
    # destination rule can fire.
    "linkdest": GOOD.replace(
        "[the gallery](https://jsab258.github.io/wc26-picks/gallery.html)",
        "[the card](https://github.com/jsab258/wc26-picks/blob/main/q.md)"),
    "shape": GOOD.replace("BUDGET:", "MONEY:"),
    "options": GOOD.replace("B. Normal British pavement distance.\n", "")
                   .replace("C. Reserved, a town that keeps its distance.\n", ""),
    "deadline": GOOD.replace("DEADLINE 2026-09-07.", "DEADLINE 2026-09-03."),
    "nextvisible": GOOD.replace("a walk through that street, tomorrow evening.",
                                "something good, soon, you will like it."),
}

# THE BRIEF FIXTURES. A brief is the same shape with a BUDGET section that
# carries the studio-versus-game split IN WORDS: no digits, because the ban
# list refuses bare counts in anything Jafar reads, and no `splitBasis=`,
# because that is a verdict key and lives on the tool's done line.
BRIEF_SPLIT = ("BUDGET: your newest reading was seven percent on the meter "
               "that governs, taken today. Nine sessions went to the studio "
               "and two to the game since the previous brief, counted in "
               "sessions and not points until the rate is measured.")
GOOD_BRIEF = GOOD.replace("BUDGET: £0 spent, well inside the month.",
                          BRIEF_SPLIT)

BAD_BRIEF = {
    "a brief with no split sentence at all":
        GOOD_BRIEF.replace(BRIEF_SPLIT, "BUDGET: comfortably inside the "
                                        "month, with nothing bought."),
    "a split that names no unit":
        GOOD_BRIEF.replace("Nine sessions went to the studio and two to the "
                           "game since the previous brief, counted in "
                           "sessions and not points until the rate is "
                           "measured.",
                           "Most of the work went to the studio and a little "
                           "to the game."),
    "a split counted in points rather than sessions":
        GOOD_BRIEF.replace("counted in sessions and not points until the rate "
                           "is measured", "counted in points"),
    "a split sitting outside the BUDGET section":
        GOOD_BRIEF.replace(BRIEF_SPLIT, "BUDGET: comfortably inside the "
                                        "month, with nothing bought.")
                  .replace("NEXT VISIBLE THING: a walk through that street, "
                           "tomorrow evening.",
                           "NEXT VISIBLE THING: a walk through that street, "
                           "tomorrow evening. Nine sessions went to the "
                           "studio and two to the game, counted in sessions "
                           "and not points until the rate is measured."),
}

# The date the fixtures are checked against. Fixed, because a deadline fixture
# that reads the wall clock passes in September and fails in October, and a
# test whose result depends on the day it runs is not a test.
FIXTURE_NOW = datetime.datetime(2026, 9, 3, 12, 0)


def _gate_tree(files):
    """A throwaway repository root holding exactly `files`.

    SYNTHETIC ON PURPOSE. A rejecting fixture pinned to a real brief goes red
    the day somebody rewrites the brief, and a guard that reddens when the
    project improves is a guard somebody switches off. The cleanup is
    REGISTERED rather than left to the reader: these run on every verify.
    """
    import atexit
    import shutil
    import tempfile
    d = pathlib.Path(tempfile.mkdtemp(prefix="producer-gate-"))
    atexit.register(shutil.rmtree, str(d), True)
    for rel, text in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return d


def selftest():
    """Both outcomes, ACCEPTING CASE FIRST, and each rejecting fixture must be
    refused BY ITS OWN RULE. A suite that only asserted 'rejected' would pass a
    check that rejects everything, which is the validator nothing survives."""
    passed, failed = 0, []

    def ok(name, cond, got=""):
        nonlocal passed
        if cond:
            passed += 1
            print("  ok   %s" % name)
        else:
            failed.append(name)
            print("  FAIL %s\n         got: %s" % (name, got))

    print("producer-check --selftest: ACCEPTING CASE FIRST\n")
    r = check(GOOD, "unprompted", FIXTURE_NOW)
    ok("a real compliant message passes with no finding at all",
       not r["findings"], [str(f) for f in r["findings"]])
    ok("and it carries %d link(s), inside the ruled band of %d..%d, both to "
       "the site (%s)" % (len(r["urls"]), LINK_MIN, LINK_MAX,
                          "/".join(r["site_labels"]) or NOTHING),
       LINK_MIN <= len(r["urls"]) <= LINK_MAX
       and len(r["good_links"]) == len(r["urls"]),
       (r["urls"], r["good_links"]))
    # THE LADDER: ONE MESSAGE, TWO RULEBOOKS, ONE RUN. The rung is membership
    # of LEGACY_LINK_RULES and nothing else, and the ruled property is that
    # this rung differs from the one above in nothing: the band only REMOVED
    # destinations, so a message legal today was legal before it.
    r_legacy = check(GOOD, "unprompted", FIXTURE_NOW, legacy_links=True)
    ok("the same message passes under the retired destination list too (%s), "
       "because the ruling of 2026-09-06 only REMOVED destinations"
       % r_legacy["link_generation"],
       not r_legacy["findings"], [str(f) for f in r_legacy["findings"]])
    ok("and on that rung the band's two rules are named as NOT ENFORCED "
       "rather than skipped in silence (%s)"
       % ",".join(sorted(set(r_legacy["not_enforced"]) & set(LINK_BAND_RULES))),
       set(LINK_BAND_RULES) <= set(r_legacy["not_enforced"])
       and not (set(LINK_BAND_RULES) & set(r["not_enforced"])),
       (r_legacy["not_enforced"], r["not_enforced"]))
    # THE LIST ITSELF, ON EVERY RUN. A grandfathering list that could gain a
    # member written after the rule would be the date switch again, wearing a
    # tuple: the specimen would choose its rulebook by being added to it.
    late = [rel for rel in LEGACY_LINK_RULES
            if (FILENAME_DATE_RE.match(rel.rsplit("/", 1)[-1]) or [None])
            and FILENAME_DATE_RE.match(rel.rsplit("/", 1)[-1])
            and datetime.date.fromisoformat(
                FILENAME_DATE_RE.match(rel.rsplit("/", 1)[-1]).group(1))
            >= LINK_BAND_RULED_ON]
    ok("every one of the %d frozen LEGACY_LINK_RULES name(s) is dated before "
       "the band was ruled on %s" % (len(LEGACY_LINK_RULES),
                                     LINK_BAND_RULED_ON.isoformat()),
       not late and len(LEGACY_LINK_RULES) == 3, late)
    ok("and it is under the ruled cap (%d of %d words)"
       % (r["words"], CAP_UNPROMPTED), r["words"] <= CAP_UNPROMPTED, r["words"])
    ok("its five sections are all found, in order",
       r["sections_found"] == SECTIONS, r["sections_found"])
    ok("its one NEEDS YOU item parses as one item with three options",
       r["items"] == 1, r["items"])
    ok("its claims are seen as claims (%d of %d sentences)"
       % (r["claims"], r["sentences"]), r["claims"] >= 2,
       (r["claims"], r["sentences"]))

    # ACCEPTING, second register: a long answer carrying a number passes,
    # because his question sets the length and asks for the number.
    answer = ("You asked how many objects carry textures. Nearly all of them: "
              "563 of 593. The rest are the wet ground. "
              "https://jsab258.github.io/wc26-picks/gallery.html " +
              "The remaining ones are small and none of them is in shot. " * 12)
    ra = check(answer, "answer", FIXTURE_NOW)
    ok("a long ANSWER carrying a count passes (%d words, no cap)" % ra["words"],
       not ra["findings"], [str(f) for f in ra["findings"]])
    ok("and the answer register NAMES the rules it did not enforce",
       set(ra["not_enforced"]) == {"wordcap", "shape", "options", "deadline",
                                   "nextvisible", "split"}, ra["not_enforced"])

    # ACCEPTING, third: a message with nothing needing him is not forced to
    # invent an item.
    empty = GOOD.replace(GOOD[GOOD.index("NEEDS YOU"):GOOD.index("NEXT VISIBLE")],
                         "NEEDS YOU: nothing today.\n\n")
    re_ = check(empty, "unprompted", FIXTURE_NOW)
    ok("an empty NEEDS YOU is accepted rather than forcing an invented item",
       not re_["findings"], [str(f) for f in re_["findings"]])

    # ACCEPTING, fourth: THE BRIEF REGISTER AND ITS SPLIT SENTENCE, which is
    # the register Jafar's morning brief is written to and the one
    # tools/morning-brief.py composes against. Accepting case FIRST: a brief
    # carrying the split in words passes with no finding at all.
    rb = check(GOOD_BRIEF, "brief", FIXTURE_NOW)
    ok("a brief carrying the split sentence passes (%d of %d part(s) found, "
       "%d word(s) of %d)" % (rb["split_found"], rb["split_of"], rb["words"],
                              rb["cap"]),
       not rb["findings"] and rb["split_found"] == rb["split_of"],
       [str(f) for f in rb["findings"]])
    ok("and `split` is enforced in the brief register and named as NOT "
       "enforced in the unprompted one",
       "split" in REGISTERS["brief"][1]
       and "split" not in REGISTERS["unprompted"][1],
       (REGISTERS["brief"][1], REGISTERS["unprompted"][1]))

    print("\n  REJECTING FIXTURES, one per rule, all synthetic:\n")
    # THE SPLIT, REJECTING, four ways, because a guard that only knows
    # "absent" cannot tell a brief that calls the count POINTS from one that
    # says sessions, which is the exact failure the ruling of 2026-09-05
    # refuses. Each fixture differs from GOOD_BRIEF in ONE part.
    for want, text in BAD_BRIEF.items():
        rr = check(text, "brief", FIXTURE_NOW)
        rules = {f.rule for f in rr["findings"]}
        ok("%-46s is refused by the split rule" % want,
           "split" in rules and rules == {"split"},
           "found %s; missing %s" % (sorted(rules) or "nothing",
                                     rr["split_missing"]))

    for want, text in BAD.items():
        rr = check(text, "unprompted", FIXTURE_NOW)
        rules = {f.rule for f in rr["findings"]}
        ok("%-22s is refused, and by its own rule" % want,
           want in rules,
           "found %s" % (sorted(rules) or "nothing"))

    # THE FIXTURES MUST DIFFER FROM THE ACCEPTING ONE IN ONE THING ONLY. A
    # fixture that trips three rules proves the check is loud, not that it is
    # right, and the day one rule stops working the fixture still goes red.
    noisy = []
    for want, text in BAD.items():
        rules = {f.rule for f in
                 check(text, "unprompted", FIXTURE_NOW)["findings"]}
        if len(rules) > 1:
            noisy.append("%s->%s" % (want, "/".join(sorted(rules))))
    ok("each rejecting fixture trips exactly one rule (%d of %d clean)"
       % (len(BAD) - len(noisy), len(BAD)), not noisy,
       cap(noisy, keep=4, sep=", "))

    ok("the word cap does not charge for a required link",
       count_words("hello https://github.com/a/b there") == ["hello", "there"],
       count_words("hello https://github.com/a/b there"))
    ok("a URL is never read as a file path",
       not find_paths(scrub_links("see https://github.com/a/b/c.md")),
       find_paths(scrub_links("see https://github.com/a/b/c.md")))
    ok("and/or and 24/7 are not file paths",
       not find_paths("and/or 24/7"), find_paths("and/or 24/7"))
    ok("a date, a duration and a price are not counts",
       not find_counts("by 2026-09-07, within 24 hours, £250 left"),
       find_counts("by 2026-09-07, within 24 hours, £250 left"))
    ok("a bare quantity IS a count", find_counts("72 gates pass") == ["72"],
       find_counts("72 gates pass"))
    ok("a question is not claim-shaped",
       not claim_shaped("Is the street done?", "Is the street done?"))
    ok("a recommendation line is not claim-shaped",
       not claim_shaped("RECOMMENDATION B, it is a port town.",
                        "RECOMMENDATION B, it is a port town."))
    ok("a plain assertion IS claim-shaped",
       claim_shaped("The street has textures.", "The street has textures."))

    # ---------------------------------------------------------- THE GATE
    # ACCEPTING FIRST, and twice: the LIVE REPOSITORY is the accepting fixture
    # for a tool that checks this project (doing the work the gate prompts can
    # never break the gate), and a synthetic tree covers the shapes the live
    # repo does not currently hold. The rejecting fixtures are synthetic to
    # the last file: a rejecting case pinned to a real brief breaks the day
    # somebody rewrites the brief.
    print("\n  THE GATE, ACCEPTING CASES FIRST:\n")
    # EVERY GATE RUN THIS SUITE MAKES, COUNTED. The summary line used to add a
    # hand-maintained +3 to the fixture count, which is a denominator that
    # drifts the first time somebody adds a case.
    gate_runs = []

    def gate_run(*a, **kw):
        g = gate(*a, **kw)
        gate_runs.append(g)
        return g

    good_tree = _gate_tree({
        "production/outbox/README.md": "# documentation, not a message\n",
        "production/outbox/2026-09-03-street.unprompted.md": GOOD,
        "production/briefs/2026-09-02.md":
            "PRODUCER-REGISTER-EXEMPT: a director brief, written before the "
            "register was ruled.\n\n" + ("word " * 400),
    })
    g = gate_run(good_tree, FIXTURE_NOW,
                 pre_register=("production/briefs/2026-09-02.md",))
    ok("a compliant outbox message passes the gate", not g["failed"],
       g["failed"])
    ok("and the README is exempt BY NAME, counted, not skipped in silence",
       g["exempt"] == 2 and g["walked"] == 3 and g["checked"] == 1,
       (g["exempt"], g["walked"], g["checked"]))
    ok("a marked file on the frozen list is exempt however badly it reads",
       any(s == "exempt" and "pre-register" in w
           for _, s, w in g["results"]), g["results"])
    # THE LIVE REPOSITORY, WITH THE GRANDFATHERING READING NAMED. "0 failed"
    # alone cannot tell a clean tree from one where every file was let through
    # the link band by the legacy list, so the numerator and its denominator
    # are asserted together on this line.
    g_live = gate_run(REPO, FIXTURE_NOW)
    ok("the live repository passes the gate it was written against "
       "(filesChecked=%d filesLegacyLinks=%d/%d)"
       % (g_live["checked"], g_live["legacy_links"], g_live["checked"]),
       not g_live["failed"] and g_live["legacy_links"] == 3
       and g_live["checked"] == 4,
       cap([f[0] for f in g_live["failed"]], keep=3))

    # THE CASE QUEUE ITEM 077 WAS FILED FOR, and it is an ACCEPTING one. The
    # live message dated 2026-09-03 carries DEADLINE 2026-09-06; at a simulated
    # now of 2026-09-08 that deadline has been served. A served deadline is a
    # historical fact, not a quality fault. Before the fix this case failed,
    # and because ledger/verify.py runs this gate it would have deleted the
    # verification footer and blocked every commit from 2026-09-05T09:01 with
    # nobody having touched the tree.
    served = datetime.datetime(2026, 9, 8, 12, 0)
    g_served = gate_run(REPO, served)
    ok("the live repo passes with its own deadline SERVED (simulated now %s, "
       "%d file(s) actually checked, %d of them date-pinned)"
       % (served.date().isoformat(), g_served["checked"],
          g_served["date_pinned"]),
       not g_served["failed"] and g_served["checked"] >= 1,
       cap(["%s: %s" % f for f in g_served["failed"]], keep=2, width=90)
       if g_served["failed"] else "checked=%d" % g_served["checked"])

    # THE LADDER: one tree, one vantage, three instants, all in this run.
    # Differences between rungs are the only reading a ladder yields, and the
    # ruled property here is that there are none. A rung taken in a later run
    # would be a different photograph, so all three are taken together.
    rungs = [datetime.datetime(2026, 9, 3, 12, 0),
             datetime.datetime(2026, 9, 8, 12, 0),
             datetime.datetime(2027, 1, 1, 12, 0)]
    verdicts = [tuple(sorted(f[0] for f in gate_run(REPO, t)["failed"]))
                for t in rungs]
    ok("the gate's verdict does not move with the run's clock (%d rung(s): %s)"
       % (len(rungs), "/".join(t.date().isoformat() for t in rungs)),
       len(set(verdicts)) == 1,
       "/".join(str(len(v)) + "-failed" for v in verdicts))

    ok("a file's clock is midnight of the ISO date in its own name",
       gate_clock("production/outbox/2026-09-03-x.unprompted.md")[0]
       == datetime.datetime(2026, 9, 3, 0, 0),
       gate_clock("production/outbox/2026-09-03-x.unprompted.md")[0])

    # THE WALL-CLOCK REGRESSION DETECTOR, and the reason its dates are built
    # from today rather than written down: the DIFFERENCE is the fixture, not
    # the date. Named two days ago, deadline today, so the pinned reading is
    # always 57.0 hours (a pass) and the wall-clock reading is always 9.0 hours
    # or less (a refusal). It is armed on every day it ever runs.
    wall = datetime.datetime.now()
    named_day = (wall.date() - datetime.timedelta(days=2)).isoformat()
    pinned_tree = _gate_tree({
        "production/outbox/README.md": "# docs\n",
        "production/outbox/%s-served.unprompted.md" % named_day:
            GOOD.replace("DEADLINE 2026-09-07.",
                         "DEADLINE %s." % wall.date().isoformat()),
    })
    gp = gate_run(pinned_tree, wall)
    ok("a deadline 57h after its file's own date passes at the REAL wall "
       "clock, where the same deadline is under 9h (%d of %d checked file(s) "
       "date-pinned)" % (gp["date_pinned"], gp["checked"]),
       not gp["failed"] and gp["date_pinned"] == 1 and gp["checked"] == 1,
       "%s checked=%d" % (cap(["%s: %s" % f for f in gp["failed"]], keep=1,
                              width=90), gp["checked"]))

    # THE LADDER: ONE MESSAGE TEXT, ONE FILENAME, ONE DATE, TWO RULEBOOKS, ONE
    # RUN. Only membership of the frozen name list changes between the rungs,
    # and BOTH rungs carry the same 2026-09-05 date in the name. That is the
    # whole reading: the date cannot decide, so a message written next week
    # under a 2026-09-05 name cannot buy itself the retired rules. The text is
    # the shape Jafar rejected, ten repository links.
    ten_links = GOOD
    for i in range(10):
        ten_links = ten_links.replace(
            "Everything else waited on that.",
            "Everything else waited on that. [q%d](https://github.com/jsab258/"
            "wc26-picks/blob/main/production/q%d.md)" % (i, i), 1)
    rung_name = "production/outbox/2026-09-05-links.unprompted.md"
    rung_tree = _gate_tree({"production/outbox/README.md": "# docs\n",
                            rung_name: ten_links})
    listed = gate_run(rung_tree, FIXTURE_NOW, legacy_links=(rung_name,))
    unlisted = gate_run(rung_tree, FIXTURE_NOW,
                        legacy_links=LEGACY_LINK_RULES)
    unlisted_why = " ".join(w for _, w in unlisted["failed"])
    ok("the SAME text under the SAME name dated 2026-09-05 passes when the "
       "name is LISTED (failed=%d, filesLegacyLinks=%d/%d) and is refused when "
       "it is not (failed=%d), by linkcap and linkdest"
       % (len(listed["failed"]), listed["legacy_links"], listed["checked"],
          len(unlisted["failed"])),
       not listed["failed"] and listed["legacy_links"] == 1
       and len(unlisted["failed"]) == 1 and unlisted["legacy_links"] == 0
       and "linkcap" in unlisted_why and "linkdest" in unlisted_why,
       cap([unlisted_why], keep=1, width=140))

    print("\n  THE GATE, REJECTING FIXTURES, all synthetic:\n")
    gate_bad = {
        "a message that breaks its register":
            ({"production/outbox/README.md": "# docs\n",
              "production/outbox/2026-09-03-x.unprompted.md":
                  BAD["banned:file path"]}, ()),
        "a filename carrying no register":
            ({"production/outbox/README.md": "# docs\n",
              "production/outbox/2026-09-03-x.md": GOOD}, ()),
        "the exempt marker on a file the frozen list does not name":
            ({"production/outbox/README.md": "# docs\n",
              "production/briefs/2026-09-04.md":
                  "PRODUCER-REGISTER-EXEMPT: let me through\n" +
                  ("word " * 400)}, ()),
        "a file on the frozen list that carries no marker":
            ({"production/outbox/README.md": "# docs\n",
              "production/briefs/2026-09-02.md": ("word " * 400)},
             ("production/briefs/2026-09-02.md",)),
        "an empty message file":
            ({"production/outbox/README.md": "# docs\n",
              "production/outbox/2026-09-03-x.answer.md": "   \n"}, ()),
        # THE FAILURE MODE THE FIX MUST NOT HAVE. Pinning the clock to the
        # filename date could have disabled the deadline rule instead of
        # repairing it, and a suite where both the served deadline and the
        # short one pass would not be able to tell the difference. This file's
        # deadline falls on the same day as its name, which is 9.0 hours from
        # the midnight pin, and it is refused at any run clock.
        "a same-day deadline, which the filename pin must NOT excuse":
            ({"production/outbox/README.md": "# docs\n",
              "production/outbox/2026-09-03-x.unprompted.md":
                  GOOD.replace("DEADLINE 2026-09-07.",
                               "DEADLINE 2026-09-03.")}, ()),
        # AND THE OTHER WAY ROUND THE FLOOR: no date in the name, so no instant
        # to measure from. It is a finding rather than a skip, or dropping the
        # date prefix would be the new escape hatch.
        "a deadline in a file whose name carries no date to pin to":
            ({"production/outbox/README.md": "# docs\n",
              "production/outbox/street.unprompted.md": GOOD}, ()),
        # THE SHAPE JAFAR REJECTED: a link to a repository markdown file, in
        # a file the frozen legacy list does not name.
        "a repository markdown link in a message no legacy list names":
            ({"production/outbox/README.md": "# docs\n",
              "production/outbox/2026-09-06-x.unprompted.md":
                  BAD["linkdest"]}, ()),
        "three links in a message no legacy list names":
            ({"production/outbox/README.md": "# docs\n",
              "production/outbox/2026-09-06-y.unprompted.md":
                  BAD["linkcap"]}, ()),
    }
    # WHICH RULE REFUSED IT, for the fixtures where the reason is the point. A
    # clock fixture refused for a shape fault would pass this loop while
    # proving nothing about the clock, which is the shape of a validator that
    # rejects everything.
    gate_bad_reason = {
        "a same-day deadline, which the filename pin must NOT excuse":
            "deadline: item 1 gives 9.0 hour(s)",
        "a deadline in a file whose name carries no date to pin to":
            "carries no date to measure it from",
        "a repository markdown link in a message no legacy list names":
            "linkdest: 1 of 2 link(s) point somewhere other than",
        "three links in a message no legacy list names":
            "linkcap: 3 link(s), 1 over the ruled cap of 2",
    }
    for name, (files, frozen) in gate_bad.items():
        gr = gate_run(_gate_tree(files), FIXTURE_NOW, pre_register=frozen)
        want = gate_bad_reason.get(name)
        why = " ".join(w for _, w in gr["failed"])
        ok("%-52s is refused%s" % (name, (", by its own rule" if want else "")),
           bool(gr["failed"]) and (want is None or want in why),
           "walked %d, failed %d: %s" % (gr["walked"], len(gr["failed"]),
                                         cap([why], keep=1, width=90)))
    # THE TREE THAT DOES NOT EXIST. Jafar's warning made flesh: this project
    # retired a file this morning that three readers were still pointed at.
    empty_root = _gate_tree({"production/notes.md": "hello\n"})
    ge = gate_run(empty_root, FIXTURE_NOW, pre_register=())
    ok("a MISSING outbox tree is red, never an empty walk reading as clean",
       len(ge["missing_trees"]) == 2, ge["missing_trees"])
    # THE FROZEN LIST CANNOT ROT IN SILENCE.
    gm = gate_run(good_tree, FIXTURE_NOW,
                  pre_register=("production/briefs/2026-09-02.md",
                                "production/briefs/gone.md"))
    ok("a frozen entry that no longer exists prints as a note, not a red",
       gm["listed_absent"] == ["production/briefs/gone.md"] and not gm["failed"],
       (gm["listed_absent"], gm["failed"]))
    # THE SAME ROT CHECK ON THE OTHER FROZEN LIST. Every name on the live
    # LEGACY_LINK_RULES exists today, so without this the branch would never
    # run and could be broken for months without a red.
    gz = gate_run(good_tree, FIXTURE_NOW,
                  pre_register=("production/briefs/2026-09-02.md",),
                  legacy_links=("production/outbox/never-existed.md",))
    ok("a LEGACY_LINK_RULES entry that no longer exists prints as a note, not "
       "a red (legacyAbsent=%d of %d listed)"
       % (len(gz["legacy_absent"]), 1),
       gz["legacy_absent"] == ["production/outbox/never-existed.md"]
       and not gz["failed"] and gz["legacy_links"] == 0,
       (gz["legacy_absent"], gz["failed"]))

    # ------------------------------------------- THE OTHER CLOCK, REJECTING
    # The gate is pinned; the SINGLE-FILE check is not, and must not be. Its
    # question is "is this deadline far enough away to SEND", which is a
    # question about now, and these two cases are what prove the fix repaired
    # the rule rather than disabling it.
    print("\n  THE SINGLE-FILE CHECK KEEPS THE WALL CLOCK, REJECTING:\n")
    wall_now = datetime.datetime.now()
    four_hours = GOOD.replace("DEADLINE 2026-09-07.", "DEADLINE in 4 hours.")
    r4 = check(four_hours, "unprompted", None)      # None means the wall clock
    ok("a four-hour deadline is refused by the single-file check at the real "
       "wall clock (%s), and the finding names the rule" % r4["now"],
       any(f.rule == "deadline" for f in r4["findings"]),
       cap([str(f) for f in r4["findings"]], keep=2, width=90))
    today_iso = wall_now.date().isoformat()
    dated_today = GOOD.replace("DEADLINE 2026-09-07.", "DEADLINE %s."
                               % today_iso)
    rt = check(dated_today, "unprompted", None)
    ok("a message dated today with a deadline of today (%s) is refused too: "
       "09:00 today is at most 9.0 hours from any instant inside it" % today_iso,
       any(f.rule == "deadline" for f in rt["findings"]),
       cap([str(f) for f in rt["findings"]], keep=2, width=90))
    # AND THE SAME MESSAGE, UNPINNED, is refused for a different reason: the
    # deadline could not be read at all. Distinct from "too soon", so the two
    # outcomes cannot be confused in a finding list.
    ru = check(GOOD, "unprompted", UNPINNED)
    ok("an UNPINNED check refuses a deadline it cannot measure, rather than "
       "passing it",
       any(f.rule == "deadline" and "no date" in str(f.what)
           for f in ru["findings"]),
       cap([str(f) for f in ru["findings"]], keep=2, width=90))

    print("\nproducer-check --selftest: %s. %d passed, %d failed, %d rejecting "
          "fixture(s) over %d rule(s), %d rejecting gate fixture(s) in %d "
          "measured gate run(s)"
          % ("PASS" if not failed else "FAILED", passed, len(failed), len(BAD),
             len(RULES), len(gate_bad), len(gate_runs)))
    for f in failed:
        print("  " + f)
    return 0 if not failed else 3


# ----------------------------------------------------------------- the gate
# WIRED INTO `ledger/verify.py`, ruled by Jafar 2026-09-03: "any file under
# production/briefs/ or the Producer's outbox must pass the check for its kind
# before it can be committed. The sender still runs it before sending; the gate
# makes skipping it impossible."
#
# The tool existed, passed its own selftest, and NOTHING CALLED IT, which is
# rule 6 pointed at an instrument: built, tested, plausible, never once running
# where it mattered. `docs_shape` in verify.py carries the same story about
# tools/docs-check.py, one tool and three weeks earlier.

GATE_TREES = ("production/outbox", "production/briefs")

# The outbox names its kind in the filename because the three registers
# enforce different rules, and a gate that GUESSES the kind checks a message
# against rules its writer never agreed to. Longest suffix first: `.brief.md`
# and `.md` must not race.
KIND_SUFFIX = ((".unprompted.md", "unprompted"),
               (".answer.md", "answer"),
               (".brief.md", "brief"))

# Everything in production/briefs/ is a brief. The directory IS the kind
# there, which is why the outbox needs a suffix and this tree does not.
TREE_DEFAULT_KIND = {"production/briefs": "brief"}

# Documentation, not a message. Named rather than pattern-matched, and the
# count is printed, so an exemption cannot grow quietly into a hole.
GATE_EXEMPT_NAMES = ("README.md",)

EXEMPT_MARKER = "PRODUCER-REGISTER-EXEMPT"
EXEMPT_WITHIN_LINES = 8

# THE FROZEN LIST. Four files predate the register (2026-09-03): three
# director briefs and one step-1 report, none of them a Producer message, all
# of them failing the register badly. Jafar ruled they must not be SILENTLY
# exempt, so the exemption exists in two places that must agree: this list,
# and the marker line inside each file. A marker on a file this list does not
# name is a FAILURE, which is what stops the marker being an escape hatch any
# future session can type at the top of a 600-word message.
PRE_REGISTER = (
    "production/briefs/2026-08-31.md",
    "production/briefs/2026-09-02.md",
    "production/briefs/latest.md",
    "production/briefs/2026-09-03-directors-console-step-1.md",
)

GATE_FINDINGS_SHOWN = 2      # per file. cap() announces when it bites.


# THE GATE'S CLOCK IS NOT THE WALL CLOCK, ruled 2026-09-03 in
# production/queue/077-a-sent-message-goes-red-by-the-clock.md. The gate used
# to re-measure every deadline against the moving wall clock, so the live
# message dated 2026-09-03 carrying DEADLINE 2026-09-06 was 64 hours away when
# written and read -51 hours five days later. The gate runs inside
# ledger/verify.py, so a served deadline would have deleted the footer and
# blocked every commit until somebody edited a message that was correct when it
# was written, with nobody having touched the tree.
#
# TWO CALLERS, TWO CLOCKS, on purpose:
#   - the SINGLE-FILE check keeps the wall clock. "Is this deadline far enough
#     away to send" is a question about now, and that is where the floor bites.
#   - the GATE pins each file to the ISO date its own filename carries. "Was
#     this message correct when it was written" has one answer for ever, which
#     makes the gate idempotent over time by construction rather than by
#     anybody remembering to re-date a file.
#
# MIDNIGHT of that date, not 09:00 and not noon: it is the most permissive
# instant inside the day the file claims, so the gate can never retroactively
# refuse a message the send check accepted at some hour of that same day. The
# floor itself is untouched at MIN_DEADLINE_HOURS: a file dated D whose
# deadline is D 09:00 still reads 9.0 hours and is still refused.
#
# PRODUCTION/BRIEFS GETS THE SAME RULE, not a special case. Three of the four
# briefs already carry an ISO date at the front of the name, so they pin like
# any message; latest.md carries none and comes out UNPINNED. UNPINNED is not
# a pass and not the wall clock: a deadline that cannot be measured is a
# finding naming the fix (put the date in the name). That is what stops a
# dateless brief becoming the next landmine in either direction, and all four
# of these files are exempt from the register anyway, so today nothing rides
# on it.
FILENAME_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})(?!\d)")


def gate_clock(rel):
    """(instant, why) the deadline rule measures this file from.

    The ISO date at the front of the filename, at midnight. UNPINNED when the
    name carries none, because the gate refuses to guess an instant: a
    wall-clock fallback here is exactly the landmine this function exists to
    remove."""
    name = rel.rsplit("/", 1)[-1]
    m = FILENAME_DATE_RE.match(name)
    if not m:
        return UNPINNED, "the name carries no date to pin a deadline to"
    try:
        d = datetime.date.fromisoformat(m.group(1))
    except ValueError:
        return UNPINNED, "the date in the name is not a real date: %s" % m.group(1)
    return (datetime.datetime.combine(d, datetime.time(0, 0)),
            "pinned to the date in its own name")


def gate_kind(rel):
    """(kind, why) for a repo-relative path, or (None, why-not)."""
    name = rel.rsplit("/", 1)[-1]
    for suffix, kind in KIND_SUFFIX:
        if name.endswith(suffix):
            return kind, "filename suffix %s" % suffix
    for tree, kind in TREE_DEFAULT_KIND.items():
        if rel.startswith(tree + "/"):
            return kind, "everything under %s/ is a brief" % tree
    return None, ("the name carries no register: end it %s"
                  % "/".join(s for s, _ in KIND_SUFFIX))


def gate(root, now=None, pre_register=PRE_REGISTER, trees=GATE_TREES,
         legacy_links=LEGACY_LINK_RULES):
    """Every message file under the ruled trees, against its own register.

    PURE-ISH: reads files, touches nothing, returns data. The report function
    formats; the selftest drives this with throwaway trees.

    `now` IS THE RUN'S WALL CLOCK AND IT MEASURES NO DEADLINE. It is recorded
    and printed as provenance only; each file's deadlines are measured from
    gate_clock(rel), the date in that file's own name. That is the whole fix
    of queue item 077, and the property it buys is that this function returns
    the same verdict for the same tree on every day for ever.
    """
    root = pathlib.Path(root)
    wall_now = (now if now is not None and now is not UNPINNED
                else datetime.datetime.now())
    r = {"missing_trees": [], "walked": 0, "checked": 0, "exempt": 0,
         "failed": [], "notes": [], "listed_absent": [], "results": [],
         # OF THE FILES CHECKED, how many were graded under the retired
         # destination list because their NAME is on LEGACY_LINK_RULES.
         # Cumulative over the walk, printed beside its denominator.
         "legacy_links": 0, "legacy_absent": [],
         # OF THE FILES CHECKED, how many had an instant to measure from.
         # Cumulative over the walk, printed beside its denominator.
         "date_pinned": 0, "unpinned": 0,
         "wall_now": wall_now.isoformat(timespec="minutes")}
    frozen = set(pre_register)
    seen = set()

    for tree in trees:
        d = root / tree
        if not d.is_dir():
            # A GATE POINTED AT A PATH NOBODY WRITES TO IS THE FAULT THIS
            # CONVENTION WAS CREATED TO AVOID, so a missing tree is red rather
            # than an empty walk that reads as clean.
            r["missing_trees"].append(tree)
            continue
        for p in sorted(d.rglob("*.md")):
            rel = p.relative_to(root).as_posix()
            seen.add(rel)
            r["walked"] += 1
            if p.name in GATE_EXEMPT_NAMES:
                r["exempt"] += 1
                r["results"].append((rel, "exempt", "exempt by name (%s)"
                                     % p.name))
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            head = "\n".join(text.splitlines()[:EXEMPT_WITHIN_LINES])
            marked = EXEMPT_MARKER in head
            listed = rel in frozen
            if marked and listed:
                r["exempt"] += 1
                r["results"].append((rel, "exempt",
                                     "pre-register, marked and on the frozen "
                                     "list"))
                continue
            if marked and not listed:
                r["failed"].append((rel, "the %s marker is on a file the "
                                    "frozen PRE_REGISTER list in "
                                    "tools/producer-check.py does not name. "
                                    "The marker is not an escape hatch: widen "
                                    "the list in a reviewed diff, or write the "
                                    "message to the register."
                                    % EXEMPT_MARKER))
                r["results"].append((rel, "fail", "marker without a listing"))
                continue
            if listed and not marked:
                r["failed"].append((rel, "the frozen PRE_REGISTER list names "
                                    "this file but its first %d lines do not "
                                    "carry the %s marker, so a reader of the "
                                    "file cannot see that it is exempt"
                                    % (EXEMPT_WITHIN_LINES, EXEMPT_MARKER)))
                r["results"].append((rel, "fail", "listed without a marker"))
                continue
            kind, why = gate_kind(rel)
            if kind is None:
                r["failed"].append((rel, why))
                r["results"].append((rel, "fail", "no register in the name"))
                continue
            if not text.strip():
                r["failed"].append((rel, "the file is empty, which is not a "
                                    "pass: nothing measured"))
                r["results"].append((rel, "fail", "empty"))
                continue
            # EACH FILE AT ITS OWN INSTANT, never at the run's. See the
            # gate_clock comment: the wall clock made a sent message go red by
            # sitting still.
            file_now, clock_why = gate_clock(rel)
            if file_now is UNPINNED:
                r["unpinned"] += 1
            else:
                r["date_pinned"] += 1
            as_of = ("asOf=" + file_now.isoformat(timespec="minutes")
                     if file_now is not UNPINNED else "asOf=unpinned")
            # BY NAME, NEVER BY THE DATE IN THE NAME. See LEGACY_LINK_RULES.
            legacy = rel in legacy_links
            if legacy:
                r["legacy_links"] += 1
            res = check(text, kind, file_now, legacy_links=legacy)
            r["checked"] += 1
            if res["findings"]:
                r["failed"].append(
                    (rel, "%s: %s" % (kind,
                                      cap([str(f) for f in res["findings"]],
                                          keep=GATE_FINDINGS_SHOWN, width=90,
                                          sep=" | "))))
                r["results"].append((rel, "fail", "%s, %d finding(s), %s"
                                     % (kind, len(res["findings"]), as_of)))
            else:
                r["results"].append(
                    (rel, "pass-legacy-links" if legacy else "pass",
                     "%s, %d of %s word(s), %s%s"
                     % (kind, res["words"],
                        res["cap"] if res["cap"] else "no-cap", as_of,
                        ", the link band is not enforced on it: written "
                        "before it was ruled and named in LEGACY_LINK_RULES"
                        if legacy else "")))
    # A FROZEN ENTRY THAT NO LONGER EXISTS IS A NOTE, NOT A RED. Deleting an
    # old brief is legitimate; leaving the rot invisible is not, so it prints
    # with its own count on every run.
    r["listed_absent"] = sorted(rel for rel in frozen if rel not in seen)
    # THE SAME ROT CHECK FOR THE OTHER FROZEN LIST. A grandfathering entry
    # whose file is gone is legitimate history and an invisible one is not, so
    # it prints with its own count on every run.
    r["legacy_absent"] = sorted(rel for rel in legacy_links if rel not in seen)
    return r


GATE_EXIT_OK, GATE_EXIT_FAIL, GATE_EXIT_NOTHING = 0, 1, 2


def gate_report(r):
    """Every zero here ships the denominator that produced it."""
    print("producer-check --gate: trees=%s" % "/".join(GATE_TREES))
    for rel, state, why in r["results"]:
        print("  %-17s %-58s %s" % (state, rel, why))
    if r["missing_trees"]:
        print("  MISSING TREE(S), which is red rather than an empty walk: %s. "
              "A gate reading a path nobody writes to reports clean for ever."
              % ", ".join(r["missing_trees"]))
    if r["listed_absent"]:
        print("  note: %d frozen PRE_REGISTER entry/entries no longer exist: "
              "%s" % (len(r["listed_absent"]),
                      cap(r["listed_absent"], keep=3, width=60, sep=", ")))
    if r["legacy_absent"]:
        print("  note: %d frozen LEGACY_LINK_RULES entry/entries no longer "
              "exist: %s" % (len(r["legacy_absent"]),
                             cap(r["legacy_absent"], keep=3, width=60,
                                 sep=", ")))
    if r["checked"]:
        print("  link band: %d of %d checked file(s) graded under the RETIRED "
              "destination list because their name is one of the %d on "
              "LEGACY_LINK_RULES; the other %d were graded under the band "
              "Jafar ruled 2026-09-06. Membership is by name, never by the "
              "date in the name."
              % (r["legacy_links"], r["checked"], len(LEGACY_LINK_RULES),
                 r["checked"] - r["legacy_links"]))
    # WHICH CLOCK READ THE DEADLINES, with its denominator, because "0 failed"
    # from a gate measuring the wrong instant is the fault this line exists to
    # make visible. Cumulative over the walk.
    if r["checked"]:
        print("  deadline clock: %d of %d checked file(s) pinned to the ISO "
              "date in their own name, %d unpinned (no date in the name, and a "
              "deadline in one of those is a finding, not a pass). The run's "
              "wall clock was %s and measured NO deadline: this gate returns "
              "the same verdict on every day."
              % (r["date_pinned"], r["checked"], r["unpinned"], r["wall_now"]))
    else:
        print("  deadline clock: %s, no file reached a register (wall clock "
              "%s, which measures no deadline here)"
              % (NOTHING.replace("-", " "), r["wall_now"]))
    print("  %d file(s) walked: %d checked against a register, %d exempt "
          "(%d by name, %d pre-register), %d failed"
          % (r["walked"], r["checked"], r["exempt"],
             sum(1 for _, s, w in r["results"]
                 if s == "exempt" and "by name" in w),
             sum(1 for _, s, w in r["results"]
                 if s == "exempt" and "pre-register" in w),
             len(r["failed"])))
    if r["missing_trees"]:
        return GATE_EXIT_FAIL
    if not r["walked"]:
        print("  nothing measured: the trees exist and hold no markdown file "
              "at all")
        return GATE_EXIT_NOTHING
    if not r["failed"]:
        # A CLEAN GATE THAT CHECKED NOTHING IS NOT A CLEAN GATE. Today every
        # file in both trees is exempt, so "0 findings" would be true and
        # useless: the words go in the human line AND in the key, because the
        # key is what reaches the verification footer and the footer is what
        # anybody actually reads.
        if not r["checked"]:
            print("  %s against a register: all %d walked file(s) were exempt "
                  "(%d by name, %d pre-register). The gate is running; no "
                  "message has been written to it yet."
                  % (NOTHING.replace("-", " "), r["walked"],
                     sum(1 for _, s, w in r["results"]
                         if s == "exempt" and "by name" in w),
                     sum(1 for _, s, w in r["results"]
                         if s == "exempt" and "pre-register" in w)))
        else:
            print("  0 finding(s) over %d file(s) checked against %d "
                  "register(s) (%s). MECHANICAL ONLY: nothing here read "
                  "whether a claim is TRUE." % (r["checked"], len(REGISTERS),
                                                ",".join(sorted(REGISTERS))))
        print("\nproducer-check --gate: PASS filesChecked=%s "
              "filesLegacyLinks=%d/%d filesExempt=%d filesWalked=%d "
              "filesDatePinned=%d/%d"
              % (r["checked"] if r["checked"] else "0/" + NOTHING,
                 r["legacy_links"], r["checked"], r["exempt"], r["walked"],
                 r["date_pinned"], r["checked"]))
        return GATE_EXIT_OK
    print("  %d file(s) failed:" % len(r["failed"]))
    for rel, why in r["failed"][:5]:
        print("    %s: %s" % (rel, why))
    if len(r["failed"]) > 5:
        print("    (+%d more not shown of %d)"
              % (len(r["failed"]) - 5, len(r["failed"])))
    print("\nproducer-check --gate: FAIL filesFailed=%d filesChecked=%d "
          "filesLegacyLinks=%d/%d filesExempt=%d filesWalked=%d "
          "filesDatePinned=%d/%d"
          % (len(r["failed"]), r["checked"], r["legacy_links"], r["checked"],
             r["exempt"], r["walked"], r["date_pinned"], r["checked"]))
    return GATE_EXIT_FAIL


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", nargs="?", help="message file, or - for stdin")
    ap.add_argument("--kind", default="unprompted", choices=sorted(REGISTERS))
    ap.add_argument("--now", help="ISO datetime the deadlines are measured "
                                  "against (default: now)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--gate", action="store_true",
                    help="walk production/outbox/ and production/briefs/ and "
                         "check every message against its own register")
    ap.add_argument("--root", default=str(REPO),
                    help="repository root the gate walks (default: this repo)")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.gate:
        now = (datetime.datetime.fromisoformat(args.now) if args.now
               else datetime.datetime.now())
        return gate_report(gate(args.root, now))
    if not args.file:
        ap.print_usage()
        print("producer-check: nothing measured, no message given")
        return 2
    if args.file == "-":
        text = sys.stdin.read()
    else:
        p = pathlib.Path(args.file)
        if not p.is_file():
            print("producer-check: nothing measured, no file at %s" % args.file)
            return 2
        text = p.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        print("producer-check: nothing measured, the message is empty")
        return 2
    now = (datetime.datetime.fromisoformat(args.now) if args.now
           else datetime.datetime.now())
    return report(check(text, args.kind, now))


if __name__ == "__main__":
    # A correct run that ends in a BrokenPipeError traceback costs twenty
    # minutes before anybody notices it worked.
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    sys.exit(main())
