#!/usr/bin/env python3
"""DECISION CARDS: read them, put buttons on them, fold a tap back into the
queue. Standard library only, and no network anywhere in this file.

    python3 tools/runner/cards.py --selftest     offline, no network

TWO ENDS, ONE FORMAT. The bot on Jafar's PC imports this to turn a WAITING
card into an inline keyboard, one button per option. The container imports it
from `tools/inbox-read.py` to fold the tap back into
`production/decision-queue.md`. One implementation of the card format, read by
both ends, for the same reason `inbox.py` is shared.

WHY A TAP IS NOT A TYPED LETTER (queue 090, mechanism fact 1). A reply
keyboard sends plain text, so a tapped "A" and a typed "A" are the same bytes
and both collide with an open budget question. An inline keyboard sends a
`callback_query` carrying `callback_data`, which is where the CARD IDENTITY
rides. A ruling that does not say which card it rules is not a ruling.

THE CARD ID IS DERIVED, NOT STORED. Telegram caps `callback_data` at 64
bytes, and a heading does not fit. The id is the first 8 hex of the sha1 of
the heading with its whitespace normalised, computed the same way at both
ends, so a tap that arrives after the bot restarted still names its card. It
is not a secret and it identifies no chat.

TWO WRITERS ON ONE FILE (mechanism fact 2). The PC never edits
`production/decision-queue.md`. It writes a RULING RECORD onto the `pc-inbox`
branch (`inbox.write_ruling`) and this file's `fold` applies records to the
queue in the container, deterministically, refusing rather than guessing.

WHAT THE FOLD WILL NOT DO. It never edits a card's text, never invents a
CLASS, never rules a card that is not in WAITING, and never rules a card whose
record names an option letter that card does not offer. Every refusal comes
back with its reason, because a refusal nobody can read is a silent drop.

APPLIED IS A FACT IN THE FILE, NOT A SIDE LEDGER. The inserted ruling carries
`<!--TAP record=... cardId=...-->`, so "have I already folded this record" is
answered by the file the fold writes and by nothing else. The comment is
invisible in rendered markdown and it is deliberately NOT the `<!--RULING
spawn=...-->` stamp the studio's director cadence greps for.

WHAT ONE MESSAGE NAMES, RULED BY JAFAR 2026-09-09, VERBATIM: "Every 'needs
you' is its own message naming the exact question, its options, the
recommendation, the default, the deadline, and a link to that one card and
nothing else; with tap buttons." Six things, in that order, and
`card_message` renders all six or the card is NOT SENT with the missing field
named. Before that ruling this file rendered three of the six: the heading,
the CLASS and the options. The recommendation, the default, the deadline and
the link were all sitting in the queue file unread, which is the fault the
ruling names: a message he cannot act on without opening a laptop.

THE SENDING HALF IS RETIRED, RULED BY JAFAR 2026-09-09, VERBATIM: "The brief
generator, the cards pass and the page notifier are retired." `send_cards` below RAISES
`SendingRetired`, and its two printers (`cards_done_line`,
`cards_nothing_line`) have no caller left; `--send-cards` and `Bot.sweep_cards` in
tools/runner/telegram-bot.py refuse the same way, and the CI step that ran them
is gone. Nothing deletes them: the code is the record of what was measured.

WHAT STAYS, AND IT IS MOST OF THIS FILE. The PARSER: `parse_queue`,
`waiting_cards`, `find_card`, `card_message`, `keyboard_for`, `fold` and
`fold_from_disk`. tools/glance.py imports the parser to render the cards page,
tools/inbox-read.py calls the fold, and a card already on his phone can still
be tapped, so the tap half stays wired. Only the SENDING goes.

AND THE NORMAL CASE IS NOW THAT NOTHING NEEDS HIM, ruled 2026-09-09: the studio
takes every decision that carries a recommendation and a default and logs it
under `## TAKEN BY THE STUDIO`, so WAITING is empty by construction and a card
is written at most once a week, only when the studio cannot form a
recommendation. A reader of this file that treats a WAITING card as the ordinary
case has it backwards.

WHAT THE RETIRED SENDER MEASURED BEFORE IT WENT, because the measurement is why
the ruling is right rather than a waste: on 2026-09-09 at 10:42 local it sent
six cards in two seconds, six of six waiting, one of them already withdrawn by
the studio. The receipts are production/pc-ops/cards-send.txt.

AND A CARD IS SENT ONCE, NOT EVERY PASS. The dedupe this file deliberately
did not have is here now, because the sender has a caller now: one receipt
per (cardId, fingerprint of the card's content), asked of the SAME receipt
mechanism `tools/runner/outbox.py` already uses for Producer messages rather
than a scheme of its own. A card whose question, options, recommendation,
default or deadline CHANGES is a different card to read and is sent again; an
unchanged one is sent once. The receipts are INJECTED as a store (see
`send_cards`), so every case below runs without a repository.

AND A PASS WITH NOTHING FOR HIM SAYS SO, ONCE A DAY. `NOTHING_NEEDS_YOU` is
the whole body of that message: no counts, no shas, no metrics, because the
ruling says "and nothing more". It is receipt-backed the same way, keyed by
the UTC day, so a pass every two minutes cannot repeat it.
"""
import datetime
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import inbox                                                  # noqa: E402

#: The queue, repository relative. One file, one shape, both ends.
QUEUE_REL = "production/decision-queue.md"

WAITING = "WAITING"
RULED = "RULED THIS WEEK"

#: An option line, exactly as `production/decision-queue.md` writes them.
#: Anchored so a sentence starting with a dash inside a card body cannot be
#: mistaken for an option.
OPTION_RE = re.compile(r"^- ([A-Z])\. +(\S.*)$")
CLASS_RE = re.compile(r"^CLASS: *(.+?) *$")
SECTION_RE = re.compile(r"^## +(.+?) *$")
CARD_RE = re.compile(r"^### +(.+?) *$")
TAP_RE = re.compile(r"<!--TAP record=(\S+) cardId=([0-9a-f]{8})-->")

#: A WRAPPED LINE UNDER AN OPTION BELONGS TO THAT OPTION. Markdown's own list
#: continuation rule: indented and non-empty. Without this the message and the
#: button carried only an option's FIRST LINE and said nothing about the cut,
#: so "A. Free house, owned outright. The Beer Orders are WEATHER around you:"
#: read as the whole option when three lines of it were missing. Measured on
#: the live queue before this existed: 25 options over 10 distinct WAITING
#: headings, first lines 40 to 77 characters, full texts 40 to 290.
OPTION_CONT_RE = re.compile(r"^\s+\S")

#: THE THREE FIELDS THE RULING OF 2026-09-09 ADDS TO A MESSAGE. Anchored at
#: the line start, because a sentence mentioning a default inside a card body
#: is not the DEFAULT line. Present on every one of the 10 distinct WAITING
#: headings this file has carried (RECOMMENDATION 10/10, DEFAULT 10/10,
#: DEADLINE as its own line 4/10, which is why `deadline_of` below reads the
#: DEFAULT line's own date as the second source rather than refusing six
#: cards that state a deadline perfectly well).
#:
#: NOT THE SAME PARSER AS `tools/producer-check.py:needs_you_items`, AND THE
#: TWO ARE NOT DUPLICATES: that one reads the NEEDS YOU section of a Producer
#: MESSAGE, where presence of a single line is all the register asks; this
#: one reads `production/decision-queue.md`, where a field WRAPS across lines
#: and has to be rendered back as written. Different files, different
#: questions, and a shared parser would have to serve both badly.
FIELD_RES = (("recommendation", re.compile(r"^RECOMMENDATION\b")),
             ("default", re.compile(r"^DEFAULT\b")),
             ("deadline", re.compile(r"^DEADLINE\b")))

#: An ISO date anywhere in a field's text. The DEFAULT line's own wording is
#: "DEFAULT A if unruled by 2026-09-11."
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

#: When the card says it was added, which is what `send_order` sorts on.
ADDED_RE = re.compile(r"^added\s+(\d{4}-\d{2}-\d{2})\b")

#: THE ROUTING IS DATA, NOT A JUDGEMENT AT SEND TIME.
#: `production/interrupt-classes.md` defines these four. BLOCKING pushes now,
#: DECISION rides the morning brief, REVIEW waits for the weekly, FYI is never
#: pushed. A card with no CLASS line is UNCLASSIFIED and is REPORTED as such,
#: never routed as FYI by default: a default route is how a Blocking item
#: lands on a page nobody opened.
PUSH_CLASSES = ("BLOCKING", "DECISION")
KNOWN_CLASSES = ("BLOCKING", "DECISION", "REVIEW", "FYI")
UNCLASSIFIED = "UNCLASSIFIED"

#: Telegram's own cap on `callback_data`, in bytes. Asserted in the selftest
#: rather than trusted, because the failure mode is the platform rejecting the
#: whole keyboard and Jafar seeing a card with no buttons.
CALLBACK_CAP = 64

#: How much option text rides on a button face. Telegram will render a long
#: label badly rather than refusing it, so this is a legibility bound, and it
#: announces itself the way every other cap here does.
BUTTON_CAP = 48

#: THE PLATFORM'S OWN CEILING on one sendMessage, and the same number as
#: `tools/runner/executor.py:TELEGRAM_TEXT_MAX`. Not a chosen bound: Telegram
#: rejects a longer message outright, and a rejection on the wire would come
#: back as a send failure retried for ever. The selftest reads executor.py's
#: source and asserts the two agree, and it also builds the WORST message
#: this file can emit (the caps below, all biting at once) and asserts that it
#: fits, so the cap cannot be reached by construction rather than by hope.
TELEGRAM_TEXT_MAX = 4096

#: THE THREE CAPS ON A MESSAGE'S PARTS, SET FROM THE PRINTED SERIES AND NOT
#: FROM TASTE (rule 2). Measured over every WAITING card this file has ever
#: carried: 35 card revisions across 11 commits plus the working tree, 10
#: distinct headings. Observed maxima, in characters: heading 69, one option's
#: full text 290, recommendation 289, default 369, deadline 129. Options per
#: card: at most 3, and the queue's own rule caps it at 4.
#:
#: So each cap sits above everything ever seen (heading 2.9x, option 1.3x,
#: field 1.5x), and the sum FITS THE PLATFORM CEILING ABOVE BY CONSTRUCTION:
#: 200 + 4x380 + 3x540 = 3340, plus the eight truncation notices themselves,
#: the CLASS line, the link and the footer. The first numbers tried here were
#: 420 and 600 and the worst-case case below measured 4174 characters, 78 over
#: the ceiling, which is why the bound is read off a printed length and not
#: off this arithmetic. Each cap announces itself when it bites.
HEADING_CAP = 200
OPTION_TEXT_CAP = 380
FIELD_CAP = 540

#: WHERE THE ONE LINK POINTS (Jafar, 2026-09-09: "a link to that one card and
#: nothing else").
#:
#: THE ANCHOR ID IS `card_id(heading)` AND NOTHING ELSE. tools/glance.py
#: renders every WAITING card with an HTML anchor whose id is `card-` plus
#: that same id, computed by calling THIS function, so the two ends cannot
#: drift: if the id ever changes it changes in `card_id` and both ends follow.
#: Nothing here parses HTML and nothing there computes an id of its own.
#:
#: THE ORIGIN IS THE ONE THE PRODUCER'S REGISTER ALLOWS, the same string as
#: `tools/producer-check.py:SITE_ORIGIN`, and the same origin
#: `tools/map.py:pages_url` derives from this clone's git remote. It is not
#: imported from either: map.py imports tools/glance.py at module level and
#: raises ImportError if that fails, and this module is imported by the bot on
#: Jafar's PC, where a page generator that cannot import must never be able to
#: silence the channel. The selftest reads producer-check.py's own source and
#: asserts the two strings agree, which is how
#: `tools/runner/executor.py:SITE_LINK` holds the same line.
#:
#: AND THE MESSAGE DOES NOT DEPEND ON IT RESOLVING. Measured 2026-09-09:
#: publish runs 41 to 48 all failed, so nothing has been served from this
#: branch yet and this URL may 404 today. That is why the message carries the
#: question, the options, the recommendation, the default and the deadline IN
#: FULL: the link is a convenience, the message is the payload, and no wording
#: here promises the link works.
SITE_ORIGIN = "https://jsab258.github.io/wc26-picks/"
CARDS_PAGE = "index.html"
CARD_ANCHOR_PREFIX = "card-"

#: THE WHOLE BODY OF THE MESSAGE A PASS WITH NOTHING FOR HIM SENDS. "A message
#: with nothing for him says 'nothing needs you' and nothing more" (Jafar,
#: 2026-09-09), so there is no count, no commit sha and no metric in it: the
#: selftest asserts it carries no digit and no link.
NOTHING_NEEDS_YOU = "Nothing needs you."

#: WHY THE SENDER REFUSES, IN JAFAR'S OWN WORDS, IN ONE PLACE. Both refusals
#: (here and in tools/runner/telegram-bot.py) read this string, so the two
#: cannot come to say different things about the same ruling.
RETIREMENT = (
    "the cards pass is RETIRED, ruled by Jafar 2026-09-09: \"The channel "
    "fails because nobody with judgment sits in it. Replace the machinery "
    "with one judgment step.\" One Producer turn a day writes one message, "
    "with two buttons on it: tools/runner/brief.py and telegram-bot.py "
    "--send-brief. This parser stays; the sending does not.")


class SendingRetired(Exception):
    """Raised by the retired sending half, so a caller that comes back is
    LOUD rather than quietly sending stale cards to his phone.

    A comment saying retired is a comment. This is the half that makes rule 6
    mechanical in reverse: nothing calls it, and if something does, it stops.
    """

#: THE TWO CLASSES THAT ARE NOT PUSHED BY DESIGN, as opposed to the ones that
#: are not pushed because something is wrong with the card.
#: `production/interrupt-classes.md` rules REVIEW to the weekly and FYI to
#: nothing, so a queue holding only those has nothing for him and the nothing
#: message is true. A card that is UNCLASSIFIED, carries the wrong number of
#: options or states no default is a STUDIO fault on a card meant for him, and
#: it WITHHOLDS the nothing message: "nothing needs you" printed over a card
#: the studio broke is the one lie this half must never tell.
NOT_PUSHED_BY_DESIGN = ("REVIEW", "FYI")


def card_id(heading):
    """8 hex of sha1 over the heading with whitespace normalised.

    NORMALISED, so that a heading reflowed by an editor still rules the same
    card. Not a secret: it identifies a public card in a public file.
    """
    key = " ".join((heading or "").split()).lower()
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]


def _one_line(parts):
    """The lines of one wrapped field or option as a single line. The file
    wraps at about 79 columns for a human reading the diff; a phone wraps on
    its own, so the file's own line breaks are dropped rather than carried."""
    return " ".join(" ".join(parts).split())


def _caps_word(token):
    """True for a word written in capitals, ignoring trailing punctuation.
    "A", "THE", "EVIDENCE:" are capitals; "Until", "the", "0" are not."""
    body = token.rstrip(":,.;")
    return bool(body) and body[0].isalpha() and body == body.upper()


def starts_a_new_block(line):
    """True when this line BEGINS A NEW BLOCK rather than continuing the field
    above it, which is where a field's capture stops.

    THE RULE, AND THE ONE THAT PAID FOR IT. A field ends at a blank line, an
    option, or a line that opens with a label: either one capitals word
    followed by a colon ("EVIDENCE:"), or two capitals words in a row ("FOLDED
    IN UNLESS...", "THE DEADLINE PASSED...", "A HAS NOW BEEN EXECUTED..."). A
    first version stopped only at a colon label and swallowed 414 characters
    of the grate card's later paragraph into its DEFAULT, which would have
    reached his phone as the default it is not. Checked over 35 card revisions
    of the live queue: 0 captured fields contain a following label.
    """
    toks = line.split()
    if not toks:
        return True
    if toks[0].endswith(":") and _caps_word(toks[0]):
        return True
    return len(toks) >= 2 and _caps_word(toks[0]) and _caps_word(toks[1])


def _parse_options(body):
    """[(letter, first-line label)], [(letter, full text)] for one card body.

    TWO FORMS OF THE SAME OPTION, DELIBERATELY KEPT APART. The label is the one
    line the author wrote after "- A. ", which is what the fold writes into
    the queue's own RULED heading (a heading is one line). The full text is
    every wrapped line of it, which is what his phone gets.
    """
    labels, full, i = [], [], 0
    while i < len(body):
        opt = OPTION_RE.match(body[i])
        if not opt:
            i += 1
            continue
        letter, first = opt.group(1), opt.group(2).strip()
        parts, j = [first], i + 1
        while (j < len(body) and OPTION_CONT_RE.match(body[j])
               and not OPTION_RE.match(body[j])):
            parts.append(body[j].strip())
            j += 1
        labels.append((letter, first))
        full.append((letter, _one_line(parts)))
        i = j
    return labels, full


def _parse_fields(body):
    """{name: text as written} for the recommendation, default and deadline.

    FIRST OCCURRENCE WINS, and the text keeps its own label ("RECOMMENDATION
    A, because...") so the message reads back exactly what the card says
    rather than a reassembled sentence.
    """
    got = {}
    for i, line in enumerate(body):
        for name, rx in FIELD_RES:
            if name in got or not rx.match(line):
                continue
            parts, j = [line.strip()], i + 1
            while (j < len(body) and body[j].strip()
                   and not starts_a_new_block(body[j])
                   and not OPTION_RE.match(body[j])):
                parts.append(body[j].strip())
                j += 1
            got[name] = _one_line(parts)
    return got


def parse_queue(text):
    """The whole file to a list of cards. PURE: no file IO, no clock.

    A card is a `###` heading and every line under it up to the next `###` or
    `##`. `section` is the `##` it sits under, so WAITING, RULED THIS WEEK and
    ON US, NOT ON HIM are told apart by position rather than by guessing from
    the wording. A section added to that file reaches this parser as itself:
    only the one named WAITING is ever sent.
    """
    lines = (text or "").splitlines()
    cards, section, cur = [], "", None
    for i, line in enumerate(lines):
        sec = SECTION_RE.match(line)
        if sec:
            if cur:
                cur["end"] = i
                cards.append(cur)
                cur = None
            section = sec.group(1).strip()
            continue
        head = CARD_RE.match(line)
        if head:
            if cur:
                cur["end"] = i
                cards.append(cur)
            cur = {"heading": head.group(1).strip(), "section": section,
                   "start": i, "end": len(lines), "options": [],
                   "cls": UNCLASSIFIED, "taps": []}
            cur["id"] = card_id(cur["heading"])
            continue
        if cur is None:
            continue
        cls = CLASS_RE.match(line)
        if cls and cur["cls"] == UNCLASSIFIED:
            got = cls.group(1).strip().upper()
            cur["cls"] = got if got in KNOWN_CLASSES else got
        tap = TAP_RE.search(line)
        if tap:
            cur["taps"].append(tap.group(1))
    if cur:
        cur["end"] = len(lines)
        cards.append(cur)
    # THE BODY PASS. Options and fields both need the LINES AFTER their own
    # line, so they are read per card from its own slice rather than in the
    # loop above: a lookahead inside that loop is how the first version of
    # the option reader silently kept only first lines.
    for c in cards:
        body = lines[c["start"]:c["end"]]
        c["options"], c["optionsFull"] = _parse_options(body)
        fields = _parse_fields(body)
        c["recommendation"] = fields.get("recommendation", "")
        c["default"] = fields.get("default", "")
        c["deadline"] = fields.get("deadline", "")
        c["added"] = ""
        for line in body:
            m = ADDED_RE.match(line)
            if m:
                c["added"] = m.group(1)
                break
        c["deadlineText"], c["deadlineDate"], c["deadlineFrom"] = \
            deadline_of(c)
    return cards


def deadline_of(card):
    """(text, iso date or "", where it came from) for ONE card's deadline.

    TWO SOURCES, IN THIS ORDER, BECAUSE THE FILE USES BOTH. A card may carry
    its own DEADLINE line (4 of the 10 distinct WAITING headings this file has
    held), or state the deadline inside the DEFAULT line as "DEFAULT A if
    unruled by 2026-09-11" (the other 6). Reading only the first would refuse
    six cards that name their deadline perfectly clearly.

    `text` IS EMPTY ONLY WHEN THE CARD STATES NEITHER, which is the case
    `sendable` refuses. A DEADLINE line with no date in it ("DEADLINE: none
    set.") is a stated deadline and is sent as written: the date is "" and
    `deadlineFrom` says `deadline-line/no-date`, so a reader can tell that
    apart from a date nobody wrote down.
    """
    line = card.get("deadline") or ""
    if line:
        m = DATE_RE.search(line)
        return (line, m.group(1) if m else "",
                "deadline-line" if m else "deadline-line/no-date")
    m = DATE_RE.search(card.get("default") or "")
    if m:
        return ("DEADLINE %s, which is the date the DEFAULT line above takes "
                "effect; this card states no separate deadline."
                % m.group(1), m.group(1), "default-line")
    return "", "", "none"


def waiting_cards(cards):
    return [c for c in cards if c["section"] == WAITING]


def find_card(cards, cid, section=None):
    for c in cards:
        if c["id"] == cid and (section is None or c["section"] == section):
            return c
    return None


def applied_records(text):
    """Every record name the file says has already been folded."""
    return set(m.group(1) for m in TAP_RE.finditer(text or ""))


# --------------------------------------------------------------------------
# The buttons
# --------------------------------------------------------------------------
def callback_data(cid, letter):
    return "r|%s|%s" % (cid, letter)


def parse_callback(data):
    """(cardId, letter, why). `why` is set only when it is not one of ours."""
    bits = (data or "").split("|")
    if len(bits) != 3 or bits[0] != "r":
        return None, None, "callback data is not a ruling tap"
    cid, letter = bits[1].strip(), bits[2].strip().upper()
    if not re.match(r"^[0-9a-f]{8}$", cid):
        return None, None, "callback data carries no card id"
    if not re.match(r"^[A-Z]$", letter):
        return None, None, "callback data carries no option letter"
    return cid, letter, ""


def button_face(letter, option_text):
    body = option_text
    if len(body) > BUTTON_CAP:
        body = body[:BUTTON_CAP].rstrip() + " (+%d more)" % (
            len(option_text) - BUTTON_CAP)
    return "%s. %s" % (letter, body)


def keyboard_for(card):
    """One button per option, one option per row. Rows rather than a grid so
    a long option is readable on a phone.

    THE FACE IS CUT FROM THE FULL OPTION TEXT, not from its first line, so the
    "(+N more)" on the button counts what the button is actually hiding. The
    message above the buttons carries all of it.
    """
    return {"inline_keyboard": [
        [{"text": button_face(letter, body),
          "callback_data": callback_data(card["id"], letter)}]
        for letter, body in card.get("optionsFull") or card["options"]]}


def card_link(card):
    """THE ONE LINK, to that one card. See CARD_ANCHOR_PREFIX for the contract
    with tools/glance.py, which renders the anchor this points at."""
    return "%s%s#%s%s" % (SITE_ORIGIN, CARDS_PAGE, CARD_ANCHOR_PREFIX,
                          card["id"])


def card_fingerprint(card):
    """8 hex of sha1 over the card's SENDABLE CONTENT: heading, every option
    letter with its full text, the recommendation, the default, the deadline.

    WHAT THE RECEIPT IS KEYED ON, so "has he already been sent this" means
    "has he been sent this CARD AS IT NOW READS". A card whose question or
    options change is a different thing to decide and goes again; an unchanged
    one goes once, however often the pass runs.

    DELIBERATELY NOT A HASH OF THE RENDERED MESSAGE: rewording this file's own
    footer would then re-send every waiting card once, and the question the
    receipt answers is about the card, not about our prose.
    """
    parts = [card["heading"]]
    for letter, body in card.get("optionsFull") or card["options"]:
        parts.append("%s.%s" % (letter, body))
    parts += [card.get("recommendation") or "", card.get("default") or "",
              card.get("deadlineText") or ""]
    key = "\x1f".join(" ".join(p.split()) for p in parts)
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]


def send_order(cards):
    """The cards in the order they go out: OLDEST CARD FIRST.

    WHY THE ORDER IS STATED AT ALL. The first live pass sends one message per
    waiting card, which is six messages today, and an order nobody chose is
    hash order. Oldest first means the thing that has waited longest arrives
    first; `added YYYY-MM-DD` is on 10 of the 10 distinct WAITING cards this
    file has ever held, so it is read from the card rather than invented. A
    card with no `added` line sorts LAST and is counted on the done line, so
    an undated card cannot quietly take the front.

    Ties and undated cards keep the file's own order (`start`), so the order
    is deterministic on one file and does not depend on dictionary iteration.
    """
    return sorted(cards, key=lambda c: (c.get("added") or "9999-99-99",
                                        c.get("start", 0)))


def sendable(card):
    """(ok, why). The reason is what gets printed when a card is skipped.

    TWO ARGUMENTS AND NOTHING MORE, because tools/glance.py calls this as
    `pushable, why = cards_mod.sendable(c)` to list what it will not push. A
    third return value here changes that file too.
    """
    if len(card["options"]) < 2:
        return False, ("carries %d option(s) and the queue's own rule is two "
                       "to four, so there is nothing to choose between"
                       % len(card["options"]))
    if len(card["options"]) > 4:
        return False, ("carries %d option(s) and the queue's own rule is two "
                       "to four" % len(card["options"]))
    if card["cls"] == UNCLASSIFIED:
        return False, ("carries no CLASS line, so it is UNCLASSIFIED and is "
                       "reported rather than routed")
    if card["cls"] not in KNOWN_CLASSES:
        return False, ("carries CLASS %s, which is not one of the four in "
                       "production/interrupt-classes.md" % card["cls"])
    if card["cls"] not in PUSH_CLASSES:
        return False, ("is CLASS %s, which is not pushed to the phone"
                       % card["cls"])
    # THE SIX THINGS OR IT DOES NOT GO, ruled 2026-09-09. A message that names
    # the question and the options but not what the studio advises, what
    # happens if he says nothing, or when that happens is a message he cannot
    # act on from his phone, which is the whole complaint the ruling answers.
    # Each reason names the FIELD, and the caller prints it with the heading,
    # so the fix is one line in production/decision-queue.md.
    if not card.get("recommendation"):
        return False, ("states no RECOMMENDATION line, so the message could "
                       "not say what the studio advises or why")
    if not card.get("default"):
        return False, ("states no DEFAULT line, so the message could not say "
                       "what happens if he says nothing")
    if not (card.get("deadlineText") or deadline_of(card)[0]):
        return False, ("states no DEADLINE line and no date in its DEFAULT "
                       "line, so the message could not say when the default "
                       "takes effect")
    for letter, body in card["options"]:
        if len(callback_data(card["id"], letter).encode("utf-8")) > CALLBACK_CAP:
            return False, "option %s does not fit Telegram's callback cap" % letter
    return True, ""


#: The last line of a card message. It explains what a tap DOES, which is the
#: one thing in the message that is not on the card.
TAP_FOOTER = ("Tap one. The tap is filed as a ruling record on the PC and the "
              "studio folds it into the decision queue; nothing else in the "
              "card is rewritten.")


def _capped(body, cap):
    """(text, bitten). Every cap announces itself, in the same shape
    `button_face` uses, so a cut reads as a cut and never as the end of a
    sentence the author wrote."""
    if len(body or "") <= cap:
        return body or "", False
    return (body[:cap].rstrip()
            + " (+%d character(s) not shown)" % (len(body) - cap)), True


def card_message(card):
    """What one card reads as in the chat, above its buttons.

    THE SIX THINGS, IN THE ORDER JAFAR RULED THEM on 2026-09-09: the exact
    question as the card writes it, its lettered options as they are written,
    the recommendation with its reason, the default and the date it takes
    effect, the deadline, and ONE link, to that card and nothing else.

    CLASS STAYS, above the options, because it is the routing fact and it was
    already here. The footer stays because it says what a tap does, which is
    the only thing in the message that is not on the card.

    THE MESSAGE IS THE PAYLOAD AND THE LINK IS A CONVENIENCE. Nothing is left
    out on the reasoning that the link carries it: measured 2026-09-09, the
    site has never published from this branch, so a message that leaned on the
    link would be a message with a hole in it.

    PURE, and it takes no clock: the deadline is rendered as the DATE the card
    names and never as "2 days left", which would be a true sentence at the
    instant of sending and a false one in his chat the next morning.
    """
    heading, _bit = _capped(card["heading"], HEADING_CAP)
    lines = [heading, "CLASS: %s" % card["cls"], ""]
    for letter, body in card.get("optionsFull") or card["options"]:
        lines.append("%s. %s" % (letter, _capped(body, OPTION_TEXT_CAP)[0]))
    lines.append("")
    for field in (card.get("recommendation"), card.get("default"),
                  card.get("deadlineText") or deadline_of(card)[0]):
        if field:
            lines.append(_capped(field, FIELD_CAP)[0])
    lines += ["", "The card: %s" % card_link(card), "", TAP_FOOTER]
    return "\n".join(lines)


def message_caps_that_bit(card):
    """(bitten, parts) for one card's message: how many caps announced
    themselves and on which parts. PER-CARD, so it goes on the card's own
    sample line and never on the pass's done line."""
    parts = []
    if _capped(card["heading"], HEADING_CAP)[1]:
        parts.append("heading")
    for letter, body in card.get("optionsFull") or card["options"]:
        if _capped(body, OPTION_TEXT_CAP)[1]:
            parts.append("option%s" % letter)
    for name, field in (("recommendation", card.get("recommendation")),
                        ("default", card.get("default")),
                        ("deadline", card.get("deadlineText"))):
        if field and _capped(field, FIELD_CAP)[1]:
            parts.append(name)
    return len(parts), parts


def cards_done_line(res):
    """The sender's whole-pass tally. Every count against its own set.

    EVERY NUMBER HERE IS WHOLE-PASS, which is why it is on this line and not on
    a card's line: `cardsSent` is this pass's sends, `cardsAlreadySent` is the
    cards a receipt already covered, and both are counted against `waiting`,
    the number of cards under WAITING in the file this pass read. A card's own
    numbers (its id, its fingerprint, its character count, the message id the
    platform returned) are on the card's own sample line.
    """
    m = res["waiting"]
    return ("cards-sent: cardsSent=%d/%d waiting cardsAlreadySent=%d/%d "
            "cardsPushable=%d/%d skipped=%d/%d heldNoReceipt=%d/%d "
            "failed=%d/%d noMessageId=%d/%d waitingTotal=%d undatedCards=%d/%d "
            "order=oldestAddedFirst nothingNeedsYou=%s dayUtc=%s file=%s"
            % (len(res["sent"]), m, len(res["already"]), m,
               len(res["pushable"]), m, len(res["skipped"]), m,
               len(res["held"]), m, len(res["failed"]), m, len(res["noid"]), m,
               m, res["undated"], m, res["nothing"], res["day"], QUEUE_REL))


def cards_nothing_line(res):
    """The words, scoped, when this pass measured nothing."""
    if res["waiting"] == 0:
        return ("  cards: nothing measured, 0 card(s) under %s in %s, so "
                "nothing was sent and nothing is known about what is waiting."
                % (WAITING, QUEUE_REL))
    return ""


def blockers_for_the_nothing_message(cards):
    """The waiting cards that STOP "nothing needs you" being true.

    Everything under WAITING that is not explicitly REVIEW or FYI. A card the
    studio could not send (no CLASS, one option, no default) is still a card
    for him, so it withholds the message rather than being counted as quiet.
    """
    return [c for c in cards if c["cls"] not in NOT_PUSHED_BY_DESIGN]


def send_cards(text, sender, store, say=None, today=None):
    """Send every pushable WAITING card he has not already been sent.

    `sender(text, keyboard)` does the wire and returns the platform's own
    result payload; `store` answers what has already reached him. This
    function does the choosing, the ordering, the counting and the strings,
    because this is where the tests run.

    THE STORE IS A REQUIRED ARGUMENT AND NOT AN OPTION. It carries six
    methods, implemented on disk by `outbox.CardReceipts` and faked in the
    selftest:

        card_state(cardId, fingerprint) -> ("sent"|"held"|"unsent", detail)
        card_sent(card, fingerprint, chars, messageId) -> receipt path
        card_hold(card, fingerprint, clause)           -> hold record path
        nothing_state(dayUtc) -> ("sent"|"held"|"unsent", detail)
        nothing_sent(dayUtc, chars, messageId)         -> receipt path
        nothing_hold(dayUtc, clause)                   -> hold record path

    A DEFAULT OF None WOULD BE A TRAP: the loop that calls this runs every two
    minutes, and a caller who forgot the store would send six messages a pass
    for ever. There is no way to call this without saying what he has seen.

    THE RECEIPT SCHEME IS OUTBOX.PY'S, NOT A SECOND ONE. Same directory, same
    `.receipt.txt` suffix that `inbox.OUTBOUND_RE` already carries back to the
    studio, same "a receipt with no message id is not a receipt" rule. A card
    that was sent and whose platform answer carried no message id is HELD, not
    sent again, for the reason outbox.py gives: a duplicate in his chat is
    worse than a late message.

    RETIRED 2026-09-09. Everything above is what it DID; the raise below is
    what it does now. The body is kept unrun, under the raise, because it is
    the record of a mechanism that was measured and ruled against, and because
    the decision-queue parsing it sits on top of is still live.
    """
    raise SendingRetired(RETIREMENT)
    # THE DAY IS UTC, NAMED AS SUCH EVERYWHERE IT IS PRINTED (`dayUtc=`), the
    # same clock every record in production/outbound/ is stamped with by
    # `inbox.iso_utc`. A once-a-day guard on two different clocks is a guard
    # that fires twice in one evening.
    day = today or datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%d")
    cards = waiting_cards(parse_queue(text))
    res = {"waiting": len(cards), "pushable": [], "sent": [], "already": [],
           "held": [], "skipped": [], "failed": [], "noid": [], "records": [],
           "undated": len([c for c in cards if not c.get("added")]),
           "nothing": "not-looked-at", "day": day}
    for card in send_order(cards):
        ok, why = sendable(card)
        if not ok:
            res["skipped"].append((card["heading"], why))
            say("  card NOT SENT: \"%s\" %s" % (card["heading"], why))
            continue
        res["pushable"].append(card["heading"])
        fp = card_fingerprint(card)
        state, detail = store.card_state(card["id"], fp)
        if state == "sent":
            res["already"].append((card["heading"], fp))
            say("  card already sent, not sent again: \"%s\" cardId=%s "
                "fingerprint=%s %s" % (card["heading"], card["id"], fp,
                                       detail))
            continue
        if state == "held":
            res["held"].append((card["heading"], detail))
            say("  card HELD, not sent again: \"%s\" cardId=%s fingerprint=%s "
                "%s" % (card["heading"], card["id"], fp, detail))
            continue
        body, keyboard = card_message(card), keyboard_for(card)
        try:
            result = sender(body, keyboard)
        except Exception as e:                                # noqa: BLE001
            res["failed"].append((card["heading"], type(e).__name__))
            say("  card FAILED to send: \"%s\" (%s). It stays unsent and the "
                "next pass tries again." % (card["heading"], type(e).__name__))
            continue
        mid = (result or {}).get("message_id")
        if not mid:
            clause = ("the platform returned no message id, so whether this "
                      "card arrived is unknown")
            rec = store.card_hold(card, fp, clause)
            res["noid"].append((card["heading"], clause))
            res["records"].append(rec)
            say("  card NO RECEIPT: \"%s\" %s. It is HELD, not sent again: "
                "delete %s once you know whether it arrived."
                % (card["heading"], clause, rec))
            continue
        rec = store.card_sent(card, fp, len(body), mid)
        res["sent"].append(card["heading"])
        res["records"].append(rec)
        bitten, parts = message_caps_that_bit(card)
        say("  card sent: \"%s\" cardId=%s fingerprint=%s options=%d chars=%d "
            "messageId=%d capsThatBit=%d/%d added=%s deadline=%s "
            "deadlineFrom=%s receipt=%s"
            % (card["heading"], card["id"], fp,
               len(card.get("optionsFull") or card["options"]), len(body), mid,
               # THE DENOMINATOR IS THE NUMBER OF PARTS THAT CAN BE CAPPED and
               # nothing else: the heading, each option, and the three fields.
               # One larger than the set examined would make a clean reading a
               # false claim with a number on it (rule 3b).
               bitten, 1 + len(card["options"]) + 3,
               card.get("added") or "nothing-measured",
               card.get("deadlineDate") or "nothing-measured",
               card.get("deadlineFrom") or "none", rec))
        if parts:
            say("    caps that announced themselves on this card: %s"
                % "/".join(parts))
    _nothing_pass(res, cards, sender, store, day, say)
    say(cards_done_line(res))
    note = cards_nothing_line(res)
    if note:
        say(note)
    return res


def _nothing_pass(res, cards, sender, store, day, say):
    """The "nothing needs you" half, at most once per UTC day.

    IT IS GATED ON PUSHABLE CARDS, NOT ON CARDS SENT THIS PASS. Six waiting
    cards he was already sent yesterday are six things that need him, so a
    pass that sends nothing because of its own receipts is NOT a quiet day and
    says nothing. The message goes only when there is nothing pushable AND
    nothing waiting that the studio failed to send.
    """
    if res["pushable"]:
        res["nothing"] = "not-needed/%d-pushable-card(s)" % len(res["pushable"])
        return
    blockers = blockers_for_the_nothing_message(cards)
    if blockers:
        res["nothing"] = ("withheld/%d-of-%d-waiting-card(s)-are-for-him-and-"
                          "could-not-be-sent" % (len(blockers), len(cards)))
        say("  nothing-needs-you WITHHELD: %d of %d waiting card(s) are for "
            "him and could not be sent, so this pass does not tell him the "
            "queue is quiet. The card line(s) above name each one."
            % (len(blockers), len(cards)))
        return
    state, detail = store.nothing_state(day)
    if state == "sent":
        res["nothing"] = "already-today"
        say("  nothing-needs-you already sent today (%s), not sent again. %s"
            % (day, detail))
        return
    if state == "held":
        res["nothing"] = "held"
        say("  nothing-needs-you HELD for today (%s): %s" % (day, detail))
        return
    try:
        result = sender(NOTHING_NEEDS_YOU, None)
    except Exception as e:                                    # noqa: BLE001
        res["nothing"] = "failed/%s" % type(e).__name__
        say("  nothing-needs-you FAILED to send (%s). The next pass tries "
            "again." % type(e).__name__)
        return
    mid = (result or {}).get("message_id")
    if not mid:
        clause = ("the platform returned no message id, so whether the quiet "
                  "day message arrived is unknown")
        rec = store.nothing_hold(day, clause)
        res["nothing"] = "no-message-id"
        res["records"].append(rec)
        say("  nothing-needs-you NO RECEIPT: %s. It is HELD for today: delete "
            "%s once you know whether it arrived." % (clause, rec))
        return
    rec = store.nothing_sent(day, len(NOTHING_NEEDS_YOU), mid)
    res["nothing"] = "sent"
    res["records"].append(rec)
    say("  nothing-needs-you sent: dayUtc=%s chars=%d messageId=%d receipt=%s"
        % (day, len(NOTHING_NEEDS_YOU), mid, rec))


# --------------------------------------------------------------------------
# The fold
# --------------------------------------------------------------------------
def ruling_block(card, letter, option_text, tapped_iso, record_name):
    """The lines that go ABOVE the moved card, in the shape the file already
    uses for "RULED 2026-09-05 BY JAFAR: A. Publish as designed."."""
    return ["### RULED %s BY JAFAR: %s. %s"
            % (tapped_iso[:10], letter, option_text),
            "",
            "Tapped on his phone at %s and folded from the ruling record "
            "the PC pushed. The card below is unchanged, and the option is "
            "the one it offered." % tapped_iso,
            "<!--TAP record=%s cardId=%s-->" % (record_name, card["id"]),
            ""]


def _insert_at(lines):
    """The line index just under `## RULED THIS WEEK` and its blank line, or
    None when the file carries no such section."""
    for i, line in enumerate(lines):
        sec = SECTION_RE.match(line)
        if sec and sec.group(1).strip() == RULED:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            return j
    return None


def fold(text, records):
    """(new_text, result). PURE: no file IO, no clock, no network.

    `records` is {record name: file content}. Applied oldest tap first, so two
    records landing in one pass fold in the order he actually tapped them.

    THE FILE IS RETURNED BYTE-UNCHANGED unless at least one record applies,
    which is what makes every rejecting case checkable by comparing bytes
    rather than by reading the diff.
    """
    res = {"records": len(records), "applied": [], "already": [],
           "refused": [], "unreadable": [],
           "waitingBefore": len(waiting_cards(parse_queue(text))),
           "waitingAfter": None, "changed": False}
    parsed = []
    for name in sorted(records):
        fields, why = inbox.parse_ruling_record(records[name] or "")
        if fields is None:
            res["unreadable"].append((name, why))
            continue
        parsed.append((fields["tappedEpoch"], name, fields))
    for _epoch, name, fields in sorted(parsed, key=lambda r: (r[0], r[1])):
        if name in applied_records(text):
            res["already"].append((name, fields["cardId"]))
            continue
        cards = parse_queue(text)
        card = find_card(cards, fields["cardId"], WAITING)
        if card is None:
            elsewhere = find_card(cards, fields["cardId"])
            if elsewhere is not None:
                res["refused"].append(
                    (name, "card \"%s\" is already under %s, so this record "
                           "would rule it twice" % (elsewhere["heading"],
                                                    elsewhere["section"])))
            else:
                res["refused"].append(
                    (name, "no card with cardId=%s is under %s in %s"
                     % (fields["cardId"], WAITING, QUEUE_REL)))
            continue
        offered = dict(card["options"])
        if fields["option"] not in offered:
            res["refused"].append(
                (name, "card \"%s\" offers %s and the record names option %s"
                 % (card["heading"],
                    "/".join(letter for letter, _b in card["options"]) or
                    "no options", fields["option"])))
            continue
        lines = text.splitlines()
        at = _insert_at(lines)
        if at is None:
            res["refused"].append(
                (name, "%s carries no \"## %s\" section to move the card into"
                 % (QUEUE_REL, RULED)))
            continue
        block = lines[card["start"]:card["end"]]
        while block and not block[-1].strip():
            block.pop()
        rest = lines[:card["start"]] + lines[card["end"]:]
        at = _insert_at(rest)
        new = ruling_block(card, fields["option"], offered[fields["option"]],
                           fields["tapped"], name) + block + [""]
        lines = rest[:at] + new + rest[at:]
        text = "\n".join(lines) + "\n"
        res["applied"].append((name, card["heading"], fields["option"]))
        res["changed"] = True
    res["waitingAfter"] = len(waiting_cards(parse_queue(text)))
    return text, res


def fold_lines(res):
    """The printed block. Every zero ships its denominator; a refusal is
    printed with its reason because that is the whole record of it."""
    lines = []
    m = res["records"]
    for name, heading, letter in res["applied"]:
        lines.append("  ruling applied  record=%s option=%s card=\"%s\""
                     % (name, letter, heading))
    for name, cid in res["already"]:
        lines.append("  ruling already folded, no change  record=%s cardId=%s"
                     % (name, cid))
    for name, why in res["refused"]:
        lines.append("  ruling REFUSED  record=%s : %s" % (name, why))
    for name, why in res["unreadable"]:
        lines.append("  ruling UNREADABLE  record=%s : %s" % (name, why))
    lines.append("rulings-fold: records=%d applied=%d/%d alreadyFolded=%d/%d "
                 "refused=%d/%d unreadable=%d/%d waitingBefore=%d "
                 "waitingAfter=%s fileChanged=%s file=%s"
                 % (m, len(res["applied"]), m, len(res["already"]), m,
                    len(res["refused"]), m, len(res["unreadable"]), m,
                    res["waitingBefore"],
                    "unknown" if res["waitingAfter"] is None
                    else res["waitingAfter"],
                    "yes" if res["changed"] else "no", QUEUE_REL))
    if m == 0:
        lines.append("  rulings: nothing measured, 0 ruling record(s) in this "
                     "checkout, so nothing is known about what he tapped.")
    return lines


def record_files(repo):
    """The ruling records on this disk, repository relative and sorted."""
    d = os.path.join(repo, *inbox.RULING_DIR.split("/"))
    if not os.path.isdir(d):
        return []
    return sorted("%s/%s" % (inbox.RULING_DIR, n) for n in os.listdir(d)
                  if inbox.RULING_RE.match(n))


def fold_from_disk(repo, say=None, write=True):
    """Read the records in this checkout, fold them, write the queue back.

    THE ONE PLACE THIS FILE TOUCHES DISK, so everything above it is testable
    without a repository. Returns the result dict; `write` False is the dry
    run the selftest uses to prove a refusal leaves the file byte-unchanged.
    """
    say = say or (lambda _s: None)
    records = {}
    for rel in record_files(repo):
        try:
            with open(os.path.join(repo, *rel.split("/")), "r",
                      encoding="utf-8") as fh:
                records[os.path.basename(rel)] = fh.read()
        except (OSError, UnicodeDecodeError) as e:
            records[os.path.basename(rel)] = "unreadable: %s" % type(e).__name__
    full = os.path.join(repo, *QUEUE_REL.split("/"))
    try:
        with open(full, "r", encoding="utf-8") as fh:
            before = fh.read()
    except OSError as e:
        res = {"records": len(records), "applied": [], "already": [],
               "refused": [], "unreadable": [], "waitingBefore": 0,
               "waitingAfter": None, "changed": False}
        say("rulings-fold: %s could not be read (%s), so %d record(s) were "
            "NOT folded and nothing was written."
            % (QUEUE_REL, type(e).__name__, len(records)))
        return res
    after, res = fold(before, records)
    if res["changed"] and write:
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(after)
    res["bytesBefore"], res["bytesAfter"] = len(before), len(after)
    for line in fold_lines(res):
        say(line)
    return res


# --------------------------------------------------------------------------
# SELFTEST. Offline by construction, accepting case first.
# --------------------------------------------------------------------------
FIXTURE = """# The decision queue

STATUS: LIVE.

---

## WAITING

### How close should strangers stand?
CLASS: DECISION
added 2026-08-04, still open

Body text that must survive the move byte for byte.

- A. 0.7 m. Crowded market street.
- B. 1.0 m. Normal British pavement distance between strangers,
  and a second line of the same option, so the reader that used to keep only
  first lines is tested on one that wraps.
- C. 1.4 m. Reserved, wary.

RECOMMENDATION B, because Meridian is a working port town and not a
festival.
DEFAULT B if unruled by 2026-09-07.
EVIDENCE: a label line that is NOT part of the default above.

### A card with one option only
CLASS: DECISION
added 2026-09-01

- A. The only thing on offer.

### A card with no class line
added 2026-09-01

- A. One.
- B. Two.

### A quiet card
CLASS: FYI
added 2026-09-01

- A. One.
- B. Two.

### A card that advises nothing
CLASS: DECISION
added 2026-09-01

- A. One.
- B. Two.

DEFAULT A if unruled by 2026-09-11.

### A card with no default
CLASS: DECISION
added 2026-09-02

- A. One.
- B. Two.

RECOMMENDATION A, because it is the first one.

### A card whose default names no date and which states no deadline
CLASS: DECISION
added 2026-09-03

- A. One.
- B. Two.

RECOMMENDATION A, because it is the first one.
DEFAULT: the studio waits.

---
## ON US, NOT ON HIM

### A complete card that is not his to rule
CLASS: DECISION
added 2026-09-04

- A. One.
- B. Two.

RECOMMENDATION A, because it is the first one.
DEFAULT A if unruled by 2026-09-11.

---
## RULED THIS WEEK

### 2026-09-03: an older ruling
CLASS: DECISION
RULED BY JAFAR. Option A.

---

## RETIRED

Nothing.
"""

#: HOW MANY CARDS THE FIXTURE HOLDS. THE ONLY PLACE ITS SIZE IS PINNED BY A
#: LITERAL, deliberately and in the same file as the fixture: the case
#: `accept/waiting-is-counted-and-other-sections-are-not-in-it` has to compare
#: the parser's answer against a number the parser did not produce, or it
#: asserts nothing. Every OTHER file that writes this fixture into a checkout
#: must DERIVE the count from it (`len(waiting_cards(parse_queue(FIXTURE)))`):
#: tools/inbox-read.py pinned 4 and 3 here and went red the moment this fixture
#: grew to carry the three new missing-field cases, which is the trap a second
#: literal re-arms rather than removes.
FIXTURE_WAITING = 7
FIXTURE_CARDS = 9


def _record(cid, letter, epoch, update):
    return inbox.render_ruling_record(cid, letter, epoch, update)


class _FakeStore:
    """The receipt store's six methods over two dicts, for the cases above.

    A TEST DOUBLE AND NOT A SECOND SCHEME. The real one is
    `outbox.CardReceipts`, which writes the files and is tested against a
    fixture repository in that file's own selftest; this one exists so the
    pass arithmetic can be checked without a repository on disk. The case
    `accept/the-real-store-answers-the-same-six-methods` below fails if the
    real one is ever renamed out from under this contract.
    """

    def __init__(self):
        self.cards, self.held, self.days = {}, {}, {}

    def card_state(self, cid, fingerprint):
        key = (cid, fingerprint)
        if key in self.cards:
            return "sent", "receipt=%s" % self.cards[key]
        if key in self.held:
            return "held", self.held[key]
        return "unsent", ""

    def card_sent(self, card, fingerprint, chars, message_id):
        rel = "production/outbound/card-%s-%s.receipt.txt" % (card["id"],
                                                             fingerprint)
        self.cards[(card["id"], fingerprint)] = rel
        return rel

    def card_hold(self, card, fingerprint, clause):
        rel = "production/outbound/card-%s-%s.refused.txt" % (card["id"],
                                                              fingerprint)
        self.held[(card["id"], fingerprint)] = clause
        return rel

    def nothing_state(self, day):
        if day in self.days:
            return "sent", "receipt=%s" % self.days[day]
        return "unsent", ""

    def nothing_sent(self, day, chars, message_id):
        rel = "production/outbound/nothing-needs-you-%s.receipt.txt" % day
        self.days[day] = rel
        return rel

    def nothing_hold(self, day, clause):
        return "production/outbound/nothing-needs-you-%s.refused.txt" % day


def _selftest():
    passed, failed = [], []

    def check(name, cond, detail=""):
        (passed if cond else failed).append(name)
        print("  %-46s %s%s" % (name, "pass" if cond else "FAIL",
                                ("  : " + str(detail)) if not cond else ""))

    cards = parse_queue(FIXTURE)
    live = find_card(cards, card_id("How close should strangers stand?"))
    check("accept/the-waiting-card-is-found-with-its-options",
          live is not None and live["section"] == WAITING
          and [le for le, _b in live["options"]] == ["A", "B", "C"]
          and live["cls"] == "DECISION", live)
    check("accept/waiting-is-counted-and-other-sections-are-not-in-it",
          len(waiting_cards(cards)) == FIXTURE_WAITING
          and len(cards) == FIXTURE_CARDS,
          "%d waiting of %d card(s)" % (len(waiting_cards(cards)), len(cards)))
    not_his = find_card(cards, card_id("A complete card that is not his to "
                                       "rule"))
    check("reject/a-complete-card-under-another-section-is-never-sent",
          not_his is not None and not_his["section"] == "ON US, NOT ON HIM"
          and not_his not in waiting_cards(cards) and sendable(not_his)[0],
          not_his and not_his["section"])
    check("accept/the-card-id-is-stable-under-reflowed-whitespace",
          card_id("How close  should strangers stand?") == live["id"],
          live["id"])
    check("reject/two-different-headings-do-not-share-an-id",
          card_id("A quiet card") != card_id("A card with no class line"))

    kb = keyboard_for(live)
    flat = [b for row in kb["inline_keyboard"] for b in row]
    check("accept/one-button-per-option-carrying-its-card",
          len(flat) == 3 and flat[1]["callback_data"]
          == callback_data(live["id"], "B")
          and flat[1]["text"].startswith("B. 1.0 m"), flat[1])
    check("accept/every-callback-fits-telegrams-64-byte-cap",
          all(len(b["callback_data"].encode("utf-8")) <= CALLBACK_CAP
              for b in flat),
          max(len(b["callback_data"]) for b in flat))
    check("reject/a-reply-keyboard-shape-is-not-what-a-card-carries",
          "keyboard" not in kb and "inline_keyboard" in kb, sorted(kb))
    cid, letter, why = parse_callback(flat[1]["callback_data"])
    check("accept/the-tap-round-trips-to-card-and-letter",
          cid == live["id"] and letter == "B" and not why, why)
    for bad in ("B", "", "r|zzzz|B", "r|%s|BB" % live["id"], "62"):
        got = parse_callback(bad)
        check("reject/callback-%s" % (bad or "empty"),
              got[0] is None and got[2], got)

    # ---- THE SIX THINGS ONE MESSAGE NAMES, accepting case first ---------
    check("accept/the-wrapped-option-is-read-whole-and-its-label-is-kept",
          dict(live["optionsFull"])["B"].endswith("that wraps.")
          and dict(live["options"])["B"].endswith("strangers,")
          and len(dict(live["optionsFull"])["B"])
          > len(dict(live["options"])["B"]),
          dict(live["optionsFull"])["B"])
    check("accept/the-three-fields-are-read-as-written",
          live["recommendation"].startswith("RECOMMENDATION B, because")
          and live["default"] == "DEFAULT B if unruled by 2026-09-07."
          and live["deadlineDate"] == "2026-09-07"
          and live["deadlineFrom"] == "default-line",
          (live["recommendation"], live["default"], live["deadlineFrom"]))
    check("accept/the-field-capture-stops-at-the-next-label",
          "EVIDENCE" not in live["recommendation"]
          and "EVIDENCE" not in live["default"]
          and "festival." in live["recommendation"],
          live["default"])
    for line, expect in (("EVIDENCE: a file", True),
                         ("A HAS NOW BEEN EXECUTED AND IT LANDED", True),
                         ("THE DEADLINE PASSED", True),
                         ("a clip can exist; if you rule B, A is two", False),
                         ("0 stands and says so on every run.", False),
                         ("Until you rule, the recipe's default", False),
                         ("B is more faithful to the masonry", False)):
        check("%s/new-block-%s" % ("accept" if expect else "reject",
                                   line.split()[0].lower().strip(":.")),
              starts_a_new_block(line) is expect, line)

    body = card_message(live)
    order = [body.index(live["heading"]), body.index("A. 0.7 m"),
             body.index("RECOMMENDATION B,"),
             body.index("DEFAULT B if unruled"),
             body.index("DEADLINE 2026-09-07,"),
             body.index("The card: https://")]
    check("accept/the-message-names-the-six-things-in-the-ruled-order",
          order == sorted(order) and len(set(order)) == 6, order)
    check("accept/the-one-link-is-this-card-and-nothing-else",
          body.count("http") == 1
          and card_link(live) in body
          and card_link(live).endswith("/index.html#card-%s" % live["id"]),
          card_link(live))
    check("accept/the-message-fits-the-platform-cap-with-room",
          len(body) <= TELEGRAM_TEXT_MAX, len(body))
    check("accept/no-cap-bit-on-a-real-card", message_caps_that_bit(live)[0] == 0,
          message_caps_that_bit(live)[1])

    # THE WORST MESSAGE THIS FILE CAN EMIT, PLANTED: four options, every part
    # over its cap, so the caps bite at once and the platform ceiling is
    # checked by construction rather than by hope (rule 5b).
    worst = {"heading": "Q" * 400, "cls": "DECISION", "id": "deadbeef",
             "options": [(le, "x") for le in "ABCD"],
             "optionsFull": [(le, "y" * 900) for le in "ABCD"],
             "recommendation": "RECOMMENDATION A, " + "r" * 900,
             "default": "DEFAULT A if unruled by 2026-09-11. " + "d" * 900,
             "deadline": "DEADLINE 2026-09-11. " + "l" * 900,
             "deadlineText": "DEADLINE 2026-09-11. " + "l" * 900,
             "deadlineDate": "2026-09-11", "deadlineFrom": "deadline-line"}
    wbody = card_message(worst)
    bitten, parts = message_caps_that_bit(worst)
    check("accept/the-worst-case-message-still-fits-the-platform-cap",
          len(wbody) <= TELEGRAM_TEXT_MAX, len(wbody))
    check("accept/and-every-cap-that-bit-announced-itself",
          bitten == 8 and len(parts) == 8
          and wbody.count("character(s) not shown") == 8, (bitten, parts))

    # ---- THE REFUSALS, one per missing field ---------------------------
    ok, why = sendable(live)
    check("accept/a-complete-two-to-four-option-card-is-sendable", ok, why)
    for heading, expect in (("A card with one option only", "1 option(s)"),
                            ("A card with no class line", "no CLASS line"),
                            ("A quiet card", "CLASS FYI"),
                            ("A card that advises nothing",
                             "no RECOMMENDATION line"),
                            ("A card with no default", "no DEFAULT line"),
                            ("A card whose default names no date and which "
                             "states no deadline", "no DEADLINE line")):
        c = find_card(cards, card_id(heading))
        ok, why = sendable(c)
        check("reject/not-sent-%s" % expect.replace(" ", "-"),
              not ok and expect in why, "%s : %s" % (heading, why))

    # ---- THE FINGERPRINT, which decides what "already sent" means -------
    fp = card_fingerprint(live)
    check("accept/the-fingerprint-is-stable-for-an-unchanged-card",
          fp == card_fingerprint(parse_queue(FIXTURE)[0]), fp)
    for what, changed in (
            ("option", dict(live, optionsFull=[("A", "0.8 m")]
                            + live["optionsFull"][1:])),
            ("recommendation", dict(live, recommendation="RECOMMENDATION C.")),
            ("default", dict(live, default="DEFAULT C if unruled by "
                                           "2026-09-30.")),
            ("deadline", dict(live, deadlineText="DEADLINE 2026-09-30.")),
            ("heading", dict(live, heading="How close should they stand?"))):
        check("accept/a-changed-%s-is-a-new-fingerprint" % what,
              card_fingerprint(changed) != fp, card_fingerprint(changed))

    # ---- THE PASS IS RETIRED, AND THIS IS THE CASE THAT SAYS SO --------
    # 2026-09-09. The block that stood here drove `send_cards` through order,
    # dedupe, the quiet-day message and the counts, and it was the reason the
    # sender was trusted. The sender is retired by Jafar's ruling, so the cases
    # that exercised it are gone with it: a suite that keeps a retired path
    # green is how a retirement becomes a comment. What is asserted now is the
    # retirement itself, and that the PARSER the glance and the fold depend on
    # is untouched by it.
    retired = None
    try:
        send_cards(FIXTURE, lambda _t, _k: {"message_id": 1}, _FakeStore(),
                   today="2026-09-12")
    except SendingRetired as e:
        retired = str(e)
    check("accept/the-card-sender-refuses-to-run-and-names-the-ruling",
          retired is not None and "RETIRED" in retired
          and "2026-09-09" in retired and "--send-brief" in retired,
          (retired or "IT STILL SENDS")[:90])
    check("accept/and-the-parser-the-page-and-the-fold-use-is-untouched",
          len(waiting_cards(parse_queue(FIXTURE))) == FIXTURE_WAITING
          and card_message(live)[0]
          and len(keyboard_for(live)["inline_keyboard"]) >= 2,
          "%d waiting in the fixture" % FIXTURE_WAITING)

    # ---- THE FOLD, accepting case first --------------------------------
    epoch = 1788633012                              # 2026-09-05T18:30:12Z
    rec = "2026-09-05T1830Z-5001.ruling.txt"
    after, res = fold(FIXTURE, {rec: _record(live["id"], "B", epoch, 5001)})
    check("accept/the-tap-moves-the-card-and-names-the-option",
          len(res["applied"]) == 1 and res["changed"]
          and "### RULED 2026-09-05 BY JAFAR: B. 1.0 m." in after,
          res["refused"] or res["unreadable"])
    check("accept/the-waiting-count-falls-by-exactly-one",
          res["waitingBefore"] == FIXTURE_WAITING
          and res["waitingAfter"] == FIXTURE_WAITING - 1,
          "%s then %s" % (res["waitingBefore"], res["waitingAfter"]))
    moved = find_card(parse_queue(after), live["id"])
    check("accept/the-card-now-sits-under-ruled-this-week",
          moved is not None and moved["section"] == RULED, moved)
    check("accept/the-cards-own-text-is-not-rewritten",
          "Body text that must survive the move byte for byte." in after
          and "- B. 1.0 m. Normal British pavement distance between "
              "strangers," in after
          and "  and a second line of the same option, so the reader that "
              "used to keep only" in after
          and after.count("How close should strangers stand?") == 1)
    check("accept/the-ruled-heading-carries-the-options-label-not-its-whole-"
          "text",
          "### RULED 2026-09-05 BY JAFAR: B. 1.0 m. Normal British pavement "
          "distance between strangers," in after
          and "and a second line of the same option, so the reader that used "
              "to keep only first lines is tested on one that wraps." not in
          [ln for ln in after.splitlines() if ln.startswith("### RULED")],
          [ln for ln in after.splitlines() if ln.startswith("### RULED")])
    added = [ln for ln in after.splitlines() if ln not in FIXTURE.splitlines()]
    check("accept/the-diff-is-the-move-plus-the-ruling-lines-only",
          all(("RULED 2026-09-05 BY JAFAR" in ln or "Tapped on his phone" in ln
               or "<!--TAP" in ln) for ln in added if ln.strip()), added)
    check("accept/the-ruling-carries-jafar-and-the-record",
          "RULED BY JAFAR" in after.replace("RULED 2026-09-05 BY JAFAR",
                                            "RULED BY JAFAR")
          and ("record=%s" % rec) in after)
    check("reject/and-it-is-not-the-directors-ruling-stamp",
          "<!--RULING spawn=" not in after)
    again, res2 = fold(after, {rec: _record(live["id"], "B", epoch, 5001)})
    check("accept/the-same-record-folded-twice-changes-nothing",
          again == after and len(res2["already"]) == 1 and not res2["changed"],
          res2["refused"])

    # ---- THE REJECTING CASES, each leaving the file byte-unchanged -----
    def refuses(name, records, expect, base=None):
        base = FIXTURE if base is None else base
        out, r = fold(base, records)
        check(name, out == base and len(r["refused"]) == 1
              and expect in r["refused"][0][1] and not r["changed"],
              r["refused"] or "ACCEPTED")

    refuses("reject/a-card-that-is-not-in-waiting",
            {rec: _record(card_id("2026-09-03: an older ruling"), "A", epoch,
                          5002)}, "already under")
    refuses("reject/a-card-that-does-not-exist-at-all",
            {rec: _record("deadbeef", "A", epoch, 5003)}, "no card with")
    refuses("reject/an-option-letter-the-card-does-not-offer",
            {rec: _record(live["id"], "D", epoch, 5004)}, "names option D")
    refuses("reject/a-second-record-for-an-already-ruled-card",
            {"2026-09-05T1900Z-5005.ruling.txt":
             _record(live["id"], "A", epoch + 1800, 5005)},
            "would rule it twice", base=after)
    out, r = fold(FIXTURE, {rec: "this is not a ruling record"})
    check("reject/a-record-that-does-not-parse-is-unreadable-not-applied",
          out == FIXTURE and len(r["unreadable"]) == 1 and not r["changed"],
          r["unreadable"])
    check("accept/every-refusal-carries-its-reason-in-the-printed-block",
          all(":" in ln for ln in fold_lines(r) if "REFUSED" in ln
              or "UNREADABLE" in ln), fold_lines(r))
    check("accept/an-empty-fold-says-nothing-measured",
          any("nothing measured" in ln for ln in fold_lines(fold(FIXTURE, {})[1])),
          fold_lines(fold(FIXTURE, {})[1]))
    check("accept/the-fold-done-line-has-no-spaces-in-its-values",
          all(" " not in kv.split("=", 1)[1]
              for kv in fold_lines(res)[-1].split()
              if "=" in kv and not kv.startswith("file=")),
          fold_lines(res)[-1])

    # ---- ORDER, so two taps in one pass fold as he tapped them ---------
    two = {"b.ruling.txt": _record(live["id"], "C", epoch + 60, 5007),
           "a.ruling.txt": _record(live["id"], "A", epoch, 5006)}
    out, r = fold(FIXTURE, two)
    check("accept/the-earlier-tap-wins-and-the-later-one-is-refused",
          len(r["applied"]) == 1 and r["applied"][0][2] == "A"
          and len(r["refused"]) == 1, (r["applied"], r["refused"]))

    # ---- THE LIVE FILE IS THE ACCEPTING FIXTURE ------------------------
    live_path = os.path.join(inbox.REPO, *QUEUE_REL.split("/"))
    try:
        with open(live_path, "r", encoding="utf-8") as fh:
            live_text = fh.read()
    except OSError:
        live_text = None
    if live_text is None:
        check("accept/the-live-queue-parses", False, "%s is not here"
              % QUEUE_REL)
    else:
        live_cards = parse_queue(live_text)
        w = waiting_cards(live_cards)
        # AN EMPTY WAITING SECTION IS THE NORMAL CASE NOW, RULED 2026-09-09:
        # the studio takes every decision carrying a recommendation and a
        # default and logs it under TAKEN BY THE STUDIO, so a card is written
        # at most once a week and only when no recommendation can be formed.
        # THESE THREE CASES ASSERTED THE OPPOSITE AND WENT RED THE HOUR THAT
        # RULING LANDED, on a tree nobody had broken, which is the trap this
        # project's own instruments rule names: an accepting case pinned to a
        # live asset breaks when somebody does the work. What is asserted now
        # is the property that holds either way, with the reading printed
        # beside it: every card parses to an id, and IF a card is waiting it is
        # sendable and its message names all six things.
        check("accept/the-live-queue-parses-and-every-card-has-an-id",
              len(live_cards) >= 1 and all(c["id"] for c in live_cards),
              "%d waiting of %d card(s)" % (len(w), len(live_cards)))
        sendables = [c for c in w if sendable(c)[0]]
        check("accept/every-live-waiting-card-is-sendable-or-there-are-none",
              len(sendables) == len(w),
              "%d sendable of %d waiting" % (len(sendables), len(w)))
        check("accept/the-live-queue-has-a-ruled-this-week-section",
              _insert_at(live_text.splitlines()) is not None, RULED)
        # EVERY LIVE SENDABLE CARD'S MESSAGE, READ RATHER THAN ASSUMED. The
        # live file is the accepting fixture for the six fields: a card that
        # parses but whose message loses a field would pass every case above.
        bad = []
        for c in sendables:
            m = card_message(c)
            if not (m.startswith(c["heading"][:40])
                    and c["recommendation"][:40] in m
                    and c["default"][:40] in m
                    and (c["deadlineText"] or "none")[:40] in m
                    and m.count("http") == 1 and card_link(c) in m
                    and len(m) <= TELEGRAM_TEXT_MAX):
                bad.append(c["heading"])
        # THE DENOMINATOR IS THE POINT OF THIS ONE. With no live card the
        # answer is nothing measured and NOT a clean pass, printed in those
        # words, and the FIXTURE above is what keeps the six-field rendering
        # covered when the live file is quiet.
        check("accept/every-live-sendable-cards-message-names-all-six",
              not bad,
              "%d of %d live sendable card(s) lost a field: %s"
              % (len(bad), len(sendables), bad[:3]))
        if not sendables:
            print("    live six-field reading: nothing measured, 0 sendable "
                  "card(s) under %s in %s. The ruling of 2026-09-09 makes "
                  "that the normal case; the FIXTURE above carries the "
                  "six-field assertions." % (WAITING, QUEUE_REL))
        chars = [len(card_message(c)) for c in sendables]
        print("    live series: waiting=%d sendable=%d messageChars=%s "
              "longest=%d/%d platformCap capsThatBit=%d/%d"
              % (len(w), len(sendables), sorted(chars),
                 max(chars) if chars else 0, TELEGRAM_TEXT_MAX,
                 sum(message_caps_that_bit(c)[0] for c in sendables),
                 len(sendables)))
        nofields = [(c["heading"], sendable(c)[1]) for c in w
                    if not sendable(c)[0]]
        print("    live refusals: %d of %d waiting card(s)%s"
              % (len(nofields), len(w),
                 ("".join("\n      \"%s\" %s" % (h, y)
                          for h, y in nofields[:4])) or
                 " (nothing measured about a refusal: none happened)"))

    # ---- THE CONSTANTS THIS FILE COPIES, READ OUT OF THEIR OWN SOURCE ---
    # The live codebase is the accepting fixture; the rejecting case is a
    # synthetic string that exists nowhere, so doing the work this guard asks
    # for can never break the guard.
    def source_of(rel):
        try:
            with open(os.path.join(inbox.REPO, *rel.split("/")), "r",
                      encoding="utf-8") as fh:
                return fh.read()
        except OSError:
            return ""

    pc_src = source_of("tools/producer-check.py")
    ex_src = source_of("tools/runner/executor.py")
    check("accept/the-site-origin-is-the-one-the-register-allows",
          bool(pc_src) and ('SITE_ORIGIN = "%s"' % SITE_ORIGIN) in pc_src,
          SITE_ORIGIN if pc_src else "tools/producer-check.py-is-not-here")
    check("reject/a-synthetic-origin-is-not-in-that-file",
          bool(pc_src)
          and 'SITE_ORIGIN = "https://ledger.example.invalid/"' not in pc_src)
    check("accept/the-platform-text-cap-matches-executors-copy",
          bool(ex_src) and ("TELEGRAM_TEXT_MAX = %d" % TELEGRAM_TEXT_MAX)
          in ex_src,
          TELEGRAM_TEXT_MAX if ex_src else "tools/runner/executor.py-is-not-"
                                           "here")
    check("reject/and-not-a-cap-nobody-wrote-down",
          bool(ex_src) and "TELEGRAM_TEXT_MAX = 9999" not in ex_src)

    # ---- THE REAL STORE ANSWERS THE SAME SIX METHODS -------------------
    try:
        import outbox as _outbox                               # noqa: E402
        real = _outbox.CardReceipts(inbox.REPO)
    except Exception as e:                                     # noqa: BLE001
        real, why = None, type(e).__name__
    else:
        why = ""
    need = ("card_state", "card_sent", "card_hold", "nothing_state",
            "nothing_sent", "nothing_hold")
    check("accept/the-real-store-answers-the-same-six-methods",
          real is not None and all(callable(getattr(real, n, None))
                                   for n in need),
          why or [n for n in need if not callable(getattr(real, n, None))])

    print("\ncards selftest: %d passed, %d failed (%d case(s) run). No case "
          "here touches the network or Telegram; what a real tap looks like "
          "on the wire is unverifiable until it runs on the PC."
          % (len(passed), len(failed), len(passed) + len(failed)))
    return 3 if failed else 0


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv[1:] else _selftest())
