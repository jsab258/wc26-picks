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


def card_id(heading):
    """8 hex of sha1 over the heading with whitespace normalised.

    NORMALISED, so that a heading reflowed by an editor still rules the same
    card. Not a secret: it identifies a public card in a public file.
    """
    key = " ".join((heading or "").split()).lower()
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]


def parse_queue(text):
    """The whole file to a list of cards. PURE: no file IO, no clock.

    A card is a `###` heading and every line under it up to the next `###` or
    `##`. `section` is the `##` it sits under, so WAITING and RULED THIS WEEK
    are told apart by position rather than by guessing from the wording.
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
        opt = OPTION_RE.match(line)
        if opt:
            cur["options"].append((opt.group(1), opt.group(2).strip()))
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
    return cards


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
    a long option is readable on a phone."""
    return {"inline_keyboard": [
        [{"text": button_face(letter, body),
          "callback_data": callback_data(card["id"], letter)}]
        for letter, body in card["options"]]}


def sendable(card):
    """(ok, why). The reason is what gets printed when a card is skipped."""
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
    for letter, body in card["options"]:
        if len(callback_data(card["id"], letter).encode("utf-8")) > CALLBACK_CAP:
            return False, "option %s does not fit Telegram's callback cap" % letter
    return True, ""


def card_message(card):
    """What one card reads as in the chat, above its buttons."""
    lines = ["%s" % card["heading"], "CLASS: %s" % card["cls"], ""]
    for letter, body in card["options"]:
        lines.append("%s. %s" % (letter, body))
    lines.append("")
    lines.append("Tap one. The tap is filed as a ruling record on the PC and "
                 "the studio folds it into the decision queue; nothing else "
                 "in the card is rewritten.")
    return "\n".join(lines)


def cards_done_line(res):
    """The sender's whole-pass tally. Every count against its own set."""
    return ("cards-sent: cardsSent=%d/%d waiting skipped=%d/%d failed=%d/%d "
            "waitingTotal=%d file=%s"
            % (len(res["sent"]), res["waiting"], len(res["skipped"]),
               res["waiting"], len(res["failed"]), res["waiting"],
               res["waiting"], QUEUE_REL))


def cards_nothing_line(res):
    """The words, scoped, when this pass measured nothing."""
    if res["waiting"] == 0:
        return ("  cards: nothing measured, 0 card(s) under %s in %s, so "
                "nothing was sent and nothing is known about what is waiting."
                % (WAITING, QUEUE_REL))
    return ""


def send_cards(text, sender, say=None):
    """Send every pushable WAITING card. `sender(text, keyboard)` does the
    wire; this function does the choosing, the counting and the strings.

    NO DEDUPE, AND IT IS SAID OUT LOUD: every run sends every pushable WAITING
    card again. The receipt-keyed dedupe is queue 093's half, and inventing a
    half of it here would be a second source of truth for what he has seen.
    """
    say = say or (lambda _s: None)
    cards = waiting_cards(parse_queue(text))
    res = {"waiting": len(cards), "sent": [], "skipped": [], "failed": []}
    for card in cards:
        ok, why = sendable(card)
        if not ok:
            res["skipped"].append((card["heading"], why))
            say("  card NOT SENT: \"%s\" %s" % (card["heading"], why))
            continue
        try:
            sender(card_message(card), keyboard_for(card))
        except Exception as e:                                # noqa: BLE001
            res["failed"].append((card["heading"], type(e).__name__))
            say("  card FAILED to send: \"%s\" (%s)"
                % (card["heading"], type(e).__name__))
            continue
        res["sent"].append(card["heading"])
        say("  card sent: \"%s\" cardId=%s options=%d"
            % (card["heading"], card["id"], len(card["options"])))
    say(cards_done_line(res))
    note = cards_nothing_line(res)
    if note:
        say(note)
    return res


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
- B. 1.0 m. Normal British pavement distance between strangers.
- C. 1.4 m. Reserved, wary.

RECOMMENDATION B.
DEFAULT B if unruled by 2026-09-07.

### A card with one option only
CLASS: DECISION

- A. The only thing on offer.

### A card with no class line

- A. One.
- B. Two.

### A quiet card
CLASS: FYI

- A. One.
- B. Two.

---
## RULED THIS WEEK

### 2026-09-03: an older ruling
CLASS: DECISION
RULED BY JAFAR. Option A.

---

## RETIRED

Nothing.
"""


def _record(cid, letter, epoch, update):
    return inbox.render_ruling_record(cid, letter, epoch, update)


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
    check("accept/waiting-is-counted-and-ruled-is-not-in-it",
          len(waiting_cards(cards)) == 4 and len(cards) == 5,
          "%d waiting of %d card(s)" % (len(waiting_cards(cards)), len(cards)))
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

    ok, why = sendable(live)
    check("accept/a-two-to-four-option-decision-card-is-sendable", ok, why)
    for heading, expect in (("A card with one option only", "1 option(s)"),
                            ("A card with no class line", "no CLASS line"),
                            ("A quiet card", "CLASS FYI")):
        c = find_card(cards, card_id(heading))
        ok, why = sendable(c)
        check("reject/not-sent-%s" % expect.split()[-1].replace(" ", "-"),
              not ok and expect in why, "%s : %s" % (heading, why))

    sent = []
    res = send_cards(FIXTURE, lambda t, k: sent.append((t, k)),
                     say=lambda _s: None)
    check("accept/the-sender-sends-only-the-sendable-card",
          len(sent) == 1 and len(res["sent"]) == 1 and len(res["skipped"]) == 3
          and "How close" in sent[0][0], [h for h, _w in res["skipped"]])
    check("accept/the-done-line-counts-sent-against-waiting",
          "cardsSent=1/4" in cards_done_line(res)
          and "skipped=3/4" in cards_done_line(res), cards_done_line(res))
    empty = send_cards("# nothing\n\n## WAITING\n\n## RULED THIS WEEK\n",
                       lambda t, k: sent.append((t, k)), say=lambda _s: None)
    check("accept/an-empty-queue-says-nothing-measured",
          "nothing measured" in cards_nothing_line(empty)
          and "cardsSent=0/0" in cards_done_line(empty),
          cards_nothing_line(empty))
    check("accept/no-spaces-inside-any-key-value",
          all(" " not in kv.split("=", 1)[1]
              for kv in cards_done_line(res).split()
              if "=" in kv and not kv.startswith("file=")),
          cards_done_line(res))

    # ---- THE FOLD, accepting case first --------------------------------
    epoch = 1788633012                              # 2026-09-05T18:30:12Z
    rec = "2026-09-05T1830Z-5001.ruling.txt"
    after, res = fold(FIXTURE, {rec: _record(live["id"], "B", epoch, 5001)})
    check("accept/the-tap-moves-the-card-and-names-the-option",
          len(res["applied"]) == 1 and res["changed"]
          and "### RULED 2026-09-05 BY JAFAR: B. 1.0 m." in after,
          res["refused"] or res["unreadable"])
    check("accept/the-waiting-count-falls-by-exactly-one",
          res["waitingBefore"] == 4 and res["waitingAfter"] == 3,
          "%s then %s" % (res["waitingBefore"], res["waitingAfter"]))
    moved = find_card(parse_queue(after), live["id"])
    check("accept/the-card-now-sits-under-ruled-this-week",
          moved is not None and moved["section"] == RULED, moved)
    check("accept/the-cards-own-text-is-not-rewritten",
          "Body text that must survive the move byte for byte." in after
          and "- B. 1.0 m. Normal British pavement distance between "
              "strangers." in after
          and after.count("How close should strangers stand?") == 1)
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
        check("accept/the-live-queue-parses-and-has-a-waiting-card",
              len(w) >= 1 and all(c["id"] for c in live_cards),
              "%d waiting of %d card(s)" % (len(w), len(live_cards)))
        sendables = [c for c in w if sendable(c)[0]]
        check("accept/at-least-one-live-waiting-card-is-sendable",
              len(sendables) >= 1,
              "%d sendable of %d waiting" % (len(sendables), len(w)))
        check("accept/the-live-queue-has-a-ruled-this-week-section",
              _insert_at(live_text.splitlines()) is not None, RULED)

    print("\ncards selftest: %d passed, %d failed (%d case(s) run). No case "
          "here touches the network or Telegram; what a real tap looks like "
          "on the wire is unverifiable until it runs on the PC."
          % (len(passed), len(failed), len(passed) + len(failed)))
    return 3 if failed else 0


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv[1:] else _selftest())
