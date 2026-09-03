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

THE REGISTERS. UNPROMPTED and BRIEF get the shape, the cap, the ban list and
the link floor. ANSWER gets the ban list and the link floor only, because
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
         "banned", "linkfloor"]
REGISTERS = {
    "unprompted": (CAP_UNPROMPTED, RULES),
    "brief": (CAP_BRIEF, RULES),
    # ANSWER: his question sets the length, so the cap and the shape are not
    # enforced and are NAMED as not enforced. The ban list and the link floor
    # still bind, minus counts: a question asking how many is answered with
    # how many.
    "answer": (None, ["banned", "linkfloor"]),
}
# ENFORCED IN EVERY REGISTER WHEN A NEEDS YOU SECTION IS PRESENT, ruled
# 2026-09-03. An answer has no cap and no required shape, but the moment it
# carries a decision it carries Jafar's floor with it: two to four options, a
# recommendation, a default, and a deadline no shorter than 24 hours. Without
# this a decision buried in a long answer escapes the default and the floor,
# which is the failure the decision queue exists to end.
RULES_IF_NEEDS_YOU = ["options", "deadline"]
# Counts are legitimate in an answer and only there. Named as its own set
# rather than hidden inside the register tuple, so the exemption is greppable.
COUNTS_ALLOWED_IN = {"answer"}

# WHERE A LINK MAY POINT. The console has no hosted URL as this is written:
# tools/dashboard/build-dashboard.py writes a local page and an opt-in live
# page, and no host for it appears anywhere in this repo. So today the only
# link that can satisfy the floor is a GitHub one, and the report SAYS that
# rather than letting a pass read as "the console link was checked".
GITHUB_HOSTS = ("github.com", "raw.githubusercontent.com")
CONSOLE_HOSTS = ()          # add the console host the day it is hosted
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


def link_ok(url):
    host = re.sub(r"^https?://", "", url).split("/")[0].lower()
    return host in GITHUB_HOSTS or host in CONSOLE_HOSTS


def count_words(text):
    """Words = whitespace-separated tokens of the body, with URLs removed
    first. The cap must not charge the writer for the link the floor demands,
    or the two rules trade against each other and evidence loses."""
    stripped = MD_LINK_RE.sub(lambda m: m.group(1), text)
    stripped = LINK_RE.sub(" ", stripped)
    stripped = re.sub(r"^[\s#*>-]+", " ", stripped, flags=re.M)
    return [w for w in stripped.split() if re.search(r"\w", w)]


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


def check(text, kind="unprompted", now=None):
    """Every reading this program takes, as data. PURE: takes text, returns a
    dict, touches no file. The selftest drives it with synthetic fixtures and
    the report function only formats what comes out of here.
    """
    now = now or datetime.datetime.now()
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
    words = count_words(text)
    scrubbed = scrub_links(text)
    found, notes = [], []
    urls = links_in(text)
    good_links = [u for u in urls if link_ok(u)]

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
        if not good_links:
            where = "; ".join(u for u in urls[:2]) or "no URL at all"
            found.append(Finding(
                "linkfloor",
                "no link to the console or to GitHub (%s). %d sentence(s) read "
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
                       if any(link_ok(u) for t in ss for u in links_in(t))}
    # links live on the LINE, not the sentence, so re-derive from lines
    linked_sections = set()
    cur = "(before any section)"
    for line in text.splitlines():
        head = section_label(line)
        if head:
            cur = head
        if any(link_ok(u) for u in links_in(line)):
            linked_sections.add(cur)
    unlinked_claims = [c for c in claims if c[1] not in linked_sections]

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

    return {
        "kind": kind, "cap": word_cap, "words": len(words),
        "sentences": len(sents), "claims": len(claims),
        "unlinked_claims": len(unlinked_claims),
        "unlinked_examples": [c[0] for c in unlinked_claims],
        "sections_found": [s for s in SECTIONS if s in bodies],
        "items": len(items), "urls": urls, "good_links": good_links,
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
    print("  links: %d URL(s), %d of them to GitHub or the console. The "
          "console has no hosted URL yet, so a GitHub link is the only one "
          "that can satisfy the floor today"
          % (len(r["urls"]), len(r["good_links"])))
    print("  claim-shaped means: not a question, the line does not begin with "
          "a section label or an option / recommendation / default / deadline "
          "marker, and the sentence carries a finite assertion verb")
    if r["banned_checked"]:
        print("  ban list: %d pattern(s) run over the message with URLs "
              "removed" % r["banned_checked"])
    for n in r["notes"]:
        print("  note: %s" % n)
    if r["not_enforced"]:
        print("  NOT ENFORCED in this register, named rather than skipped in "
              "silence: %s" % ", ".join(r["not_enforced"]))

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
[the street](https://github.com/jsab258/wc26-picks/blob/main/game-design/x.jpg)

NEEDS YOU: how close should strangers stand on a pavement?
A. Almost touching, a crowded market.
B. Normal British pavement distance.
C. Reserved, a town that keeps its distance.
RECOMMENDATION B, a working port town rather than a festival.
DEFAULT B if you say nothing.
DEADLINE 2026-09-07.
[the card](https://github.com/jsab258/wc26-picks/blob/main/production/q.md)

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
    "shape": GOOD.replace("BUDGET:", "MONEY:"),
    "options": GOOD.replace("B. Normal British pavement distance.\n", "")
                   .replace("C. Reserved, a town that keeps its distance.\n", ""),
    "deadline": GOOD.replace("DEADLINE 2026-09-07.", "DEADLINE 2026-09-03."),
    "nextvisible": GOOD.replace("a walk through that street, tomorrow evening.",
                                "something good, soon, you will like it."),
}

# The date the fixtures are checked against. Fixed, because a deadline fixture
# that reads the wall clock passes in September and fails in October, and a
# test whose result depends on the day it runs is not a test.
FIXTURE_NOW = datetime.datetime(2026, 9, 3, 12, 0)


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
              "https://github.com/jsab258/wc26-picks/blob/main/x.md " +
              "The remaining ones are small and none of them is in shot. " * 12)
    ra = check(answer, "answer", FIXTURE_NOW)
    ok("a long ANSWER carrying a count passes (%d words, no cap)" % ra["words"],
       not ra["findings"], [str(f) for f in ra["findings"]])
    ok("and the answer register NAMES the rules it did not enforce",
       set(ra["not_enforced"]) == {"wordcap", "shape", "options", "deadline",
                                   "nextvisible"}, ra["not_enforced"])

    # ACCEPTING, third: a message with nothing needing him is not forced to
    # invent an item.
    empty = GOOD.replace(GOOD[GOOD.index("NEEDS YOU"):GOOD.index("NEXT VISIBLE")],
                         "NEEDS YOU: nothing today.\n\n")
    re_ = check(empty, "unprompted", FIXTURE_NOW)
    ok("an empty NEEDS YOU is accepted rather than forcing an invented item",
       not re_["findings"], [str(f) for f in re_["findings"]])

    print("\n  REJECTING FIXTURES, one per rule, all synthetic:\n")
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
        rules = {f.rule for f in check(text, "unprompted", FIXTURE_NOW)["findings"]}
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

    print("\nproducer-check --selftest: %s. %d passed, %d failed, %d rejecting "
          "fixture(s) over %d rule(s)"
          % ("PASS" if not failed else "FAILED", passed, len(failed), len(BAD),
             len(RULES)))
    for f in failed:
        print("  " + f)
    return 0 if not failed else 3


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", nargs="?", help="message file, or - for stdin")
    ap.add_argument("--kind", default="unprompted", choices=sorted(REGISTERS))
    ap.add_argument("--now", help="ISO datetime the deadlines are measured "
                                  "against (default: now)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
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
