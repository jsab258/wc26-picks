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

    # ---------------------------------------------------------- THE GATE
    # ACCEPTING FIRST, and twice: the LIVE REPOSITORY is the accepting fixture
    # for a tool that checks this project (doing the work the gate prompts can
    # never break the gate), and a synthetic tree covers the shapes the live
    # repo does not currently hold. The rejecting fixtures are synthetic to
    # the last file: a rejecting case pinned to a real brief breaks the day
    # somebody rewrites the brief.
    print("\n  THE GATE, ACCEPTING CASES FIRST:\n")
    good_tree = _gate_tree({
        "production/outbox/README.md": "# documentation, not a message\n",
        "production/outbox/2026-09-03-street.unprompted.md": GOOD,
        "production/briefs/2026-09-02.md":
            "PRODUCER-REGISTER-EXEMPT: a director brief, written before the "
            "register was ruled.\n\n" + ("word " * 400),
    })
    g = gate(good_tree, FIXTURE_NOW,
             pre_register=("production/briefs/2026-09-02.md",))
    ok("a compliant outbox message passes the gate", not g["failed"],
       g["failed"])
    ok("and the README is exempt BY NAME, counted, not skipped in silence",
       g["exempt"] == 2 and g["walked"] == 3 and g["checked"] == 1,
       (g["exempt"], g["walked"], g["checked"]))
    ok("a marked file on the frozen list is exempt however badly it reads",
       any(s == "exempt" and "pre-register" in w
           for _, s, w in g["results"]), g["results"])
    ok("the live repository passes the gate it was written against",
       not gate(REPO, FIXTURE_NOW)["failed"],
       cap([f[0] for f in gate(REPO, FIXTURE_NOW)["failed"]], keep=3))

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
    }
    for name, (files, frozen) in gate_bad.items():
        gr = gate(_gate_tree(files), FIXTURE_NOW, pre_register=frozen)
        ok("%-52s is refused" % name, bool(gr["failed"]),
           "walked %d, failed %d" % (gr["walked"], len(gr["failed"])))
    # THE TREE THAT DOES NOT EXIST. Jafar's warning made flesh: this project
    # retired a file this morning that three readers were still pointed at.
    empty_root = _gate_tree({"production/notes.md": "hello\n"})
    ge = gate(empty_root, FIXTURE_NOW, pre_register=())
    ok("a MISSING outbox tree is red, never an empty walk reading as clean",
       len(ge["missing_trees"]) == 2, ge["missing_trees"])
    # THE FROZEN LIST CANNOT ROT IN SILENCE.
    gm = gate(good_tree, FIXTURE_NOW,
              pre_register=("production/briefs/2026-09-02.md",
                            "production/briefs/gone.md"))
    ok("a frozen entry that no longer exists prints as a note, not a red",
       gm["listed_absent"] == ["production/briefs/gone.md"] and not gm["failed"],
       (gm["listed_absent"], gm["failed"]))

    print("\nproducer-check --selftest: %s. %d passed, %d failed, %d rejecting "
          "fixture(s) over %d rule(s), %d gate fixture(s)"
          % ("PASS" if not failed else "FAILED", passed, len(failed), len(BAD),
             len(RULES), len(gate_bad) + 3))
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


def gate(root, now=None, pre_register=PRE_REGISTER, trees=GATE_TREES):
    """Every message file under the ruled trees, against its own register.

    PURE-ISH: reads files, touches nothing, returns data. The report function
    formats; the selftest drives this with throwaway trees.
    """
    root = pathlib.Path(root)
    now = now or datetime.datetime.now()
    r = {"missing_trees": [], "walked": 0, "checked": 0, "exempt": 0,
         "failed": [], "notes": [], "listed_absent": [], "results": []}
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
            res = check(text, kind, now)
            r["checked"] += 1
            if res["findings"]:
                r["failed"].append(
                    (rel, "%s: %s" % (kind,
                                      cap([str(f) for f in res["findings"]],
                                          keep=GATE_FINDINGS_SHOWN, width=90,
                                          sep=" | "))))
                r["results"].append((rel, "fail", "%s, %d finding(s)"
                                     % (kind, len(res["findings"]))))
            else:
                r["results"].append((rel, "pass", "%s, %d of %s word(s)"
                                     % (kind, res["words"],
                                        res["cap"] if res["cap"] else "no-cap")))
    # A FROZEN ENTRY THAT NO LONGER EXISTS IS A NOTE, NOT A RED. Deleting an
    # old brief is legitimate; leaving the rot invisible is not, so it prints
    # with its own count on every run.
    r["listed_absent"] = sorted(rel for rel in frozen if rel not in seen)
    return r


GATE_EXIT_OK, GATE_EXIT_FAIL, GATE_EXIT_NOTHING = 0, 1, 2


def gate_report(r):
    """Every zero here ships the denominator that produced it."""
    print("producer-check --gate: trees=%s" % "/".join(GATE_TREES))
    for rel, state, why in r["results"]:
        print("  %-5s %-58s %s" % (state, rel, why))
    if r["missing_trees"]:
        print("  MISSING TREE(S), which is red rather than an empty walk: %s. "
              "A gate reading a path nobody writes to reports clean for ever."
              % ", ".join(r["missing_trees"]))
    if r["listed_absent"]:
        print("  note: %d frozen PRE_REGISTER entry/entries no longer exist: "
              "%s" % (len(r["listed_absent"]),
                      cap(r["listed_absent"], keep=3, width=60, sep=", ")))
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
        print("\nproducer-check --gate: PASS filesChecked=%s filesExempt=%d "
              "filesWalked=%d"
              % (r["checked"] if r["checked"] else "0/" + NOTHING,
                 r["exempt"], r["walked"]))
        return GATE_EXIT_OK
    print("  %d file(s) failed:" % len(r["failed"]))
    for rel, why in r["failed"][:5]:
        print("    %s: %s" % (rel, why))
    if len(r["failed"]) > 5:
        print("    (+%d more not shown of %d)"
              % (len(r["failed"]) - 5, len(r["failed"])))
    print("\nproducer-check --gate: FAIL filesFailed=%d filesChecked=%d "
          "filesExempt=%d filesWalked=%d"
          % (len(r["failed"]), r["checked"], r["exempt"], r["walked"]))
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
