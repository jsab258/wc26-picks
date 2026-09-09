#!/usr/bin/env python3
"""THE ONE DAILY MESSAGE, ITS TWO BUTTONS, AND THE COUNT THAT IS THE ONLY
MEASURE OF THE CHANNEL. Standard library only, no network in this file.

    python3 tools/runner/brief.py --selftest    offline, no repository needed

RULED BY JAFAR 2026-09-09, VERBATIM: "The channel fails because nobody with
judgment sits in it. Replace the machinery with one judgment step." And:
"One Producer turn a day writes the single message. It reads the queue,
findings, decision queue, receipts and ladder, and decides what I see and
what I never see. The brief generator, the cards pass and the page notifier
are retired; the register stays as a format check after the Producer writes."
And: "Every brief carries two buttons, readable and unreadable. Unreadable
means tomorrow's is written differently, and the Producer says what it
changed. This is the only measure of the channel: seven consecutive readable
briefs, tapped by me, is the acceptance. Selftests do not count."

WHAT THIS FILE IS AND IS NOT. It is the harness: where the message sits, how
it is sent, how a tap comes back, and the arithmetic of the streak. IT WRITES
NO PROSE AND RANKS NOTHING. There is no headline function here, no template,
no summariser and no chooser, because those are the machinery that ruling
retires. The words are the Producer's and arrive as a file this sends
unchanged.

THE ONE MESSAGE A DAY LIVES AT production/briefs/<YYYY-MM-DD>.md, AND THE
FOLDER IS A DELIBERATE CHOICE, not the outbox. `tools/runner/outbox.py:sweep`
walks production/outbox/ and sends anything it finds there through a
`sender(text)` that has nowhere to put a keyboard, and the bot's own loop
sweeps every 120 seconds: a brief written into that tree would be sent with no
buttons by whichever sweep got there first, which is the one thing the ruling
says must never happen. production/briefs/ is already the documented home of a
brief (see .claude/agents/producer.md) and `producer-check --gate` already
checks every file in it as a brief, so the format check is unchanged by this.

THE TWO BUTTONS REUSE THE PROVEN TAP PATH AND DO NOT BUILD A SECOND ONE. An
inline keyboard arrives back as a `callback_query`, which
`telegram-bot.py:handle_callback` already receives, already answers so his
phone stops spinning, and already turns into a record pushed on the pc-inbox
branch by `inbox.push_pending`. What is new here is one more record KIND on
that same transport, in its own folder with its own pattern, for the reason
`inbox.RULING_DIR` is its own folder rather than sharing the outbound one: a
record a reader cannot classify prints as unreadable and turns a working
channel into a fault report. Separate folder, separate pattern, separate
denominator.

WHY THE STREAK ARITHMETIC IS HERE AND NOT IN THE CONTAINER TOOL THAT PRINTS
IT. The instruments rule of 25 August: the tally, the maths and the string
live where the tests run. `tools/producer-day.py` supplies the files and the
day; every count below is computed and formatted here, under --selftest.

WHAT THE STREAK COUNTS, SAID BEFORE ANY NUMBER IS PRINTED (rule 2):
  - briefStreakReadable is a RUN LENGTH, counted backwards from the newest
    tapped day while the verdict is readable. It is not a total and not a
    rate. One unreadable tap resets it to 0, which is Jafar's ruling.
  - A day with two taps is LAST WINS by the tap's own instant, and the number
    of superseded taps is printed beside it so a reader can see it happened.
  - briefsSentInRun is the denominator captured AT THE SAME INSTANT as the
    run: how many briefs were actually sent across the days the run spans.
    briefsUntappedInRun is the gap between the two, printed because a run of
    seven readable taps over twelve sent briefs is not the same fact as seven
    out of seven, AND BECAUSE WHETHER A GAP BREAKS THE RUN IS JAFAR'S TO RULE
    AND HE HAS NOT. This file does not decide it: it prints both numbers and
    says so in words.
  - With no taps at all the words are "0 of 7 consecutive, no tap has ever
    been recorded", never a bare 0.

EXIT CODES. 0 the selftest passed. 3 it failed. Nothing else runs from here:
the senders and the record writers are called by the bot and by
tools/producer-day.py.
"""
import datetime
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import inbox                                                  # noqa: E402

#: Where the one message a day sits, repository relative. Same string as
#: `producer-check.py:GATE_TREES[1]` and as producer.md's own convention: the
#: gate already checks everything here as a brief.
BRIEFS_DIR = "production/briefs"

#: The name of the one message a day. A date and nothing else, so the day is
#: the identity: two briefs for one day is not a case this channel has, and a
#: slug would let two files claim the same day.
BRIEF_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")

#: HIS TWO WORDS, AS THE BUTTONS SAY THEM. Not "yes/no", not an emoji: the
#: ruling names the buttons "readable" and "unreadable" and a reader of his
#: phone should see the word he used.
READABLE = "readable"
UNREADABLE = "unreadable"
LETTER = {"R": READABLE, "U": UNREADABLE}
BUTTON_FACE = {"R": "Readable", "U": "Unreadable"}

#: THE ACCEPTANCE, IN HIS WORDS, AS A CONSTANT SO NOBODY HAS TO REMEMBER IT.
#: "seven consecutive readable briefs, tapped by me, is the acceptance."
WANT_CONSECUTIVE = 7

#: `callback_data` is capped at 64 bytes by the platform. This form is 14
#: bytes and carries the day, so a tap that arrives after the bot restarted
#: still names the brief it is about. The leading letter is what tells it
#: apart from a decision-card ruling tap (`cards.callback_data`, prefix "r"),
#: and the bot tries this parser first.
CB_PREFIX = "b"

#: A tap record, and nothing else, in the folder below. The pattern IS the
#: denominator: a README dropped in that folder is outside every count, the
#: same discipline as `inbox.NAME_RE` and `inbox.RULING_RE`.
TAP_RE = inbox.BRIEF_TAP_RE
TAP_DIR = inbox.BRIEF_TAP_DIR

#: HOW MUCH OF A REASON IS WRITTEN DOWN. He can type anything; the record
#: carries one line, and the cap announces when it bites. The whole of what he
#: typed is in production/inbox/ as well, filed by the ordinary message path,
#: so nothing is lost by this cap.
REASON_CAP = 280

#: What the reply says when he taps. One sentence, no key=value, no path, no
#: studio vocabulary: his phone is not a console.
THANKS_READABLE = ("Noted: readable. Tomorrow's comes the same way.")
THANKS_UNREADABLE = ("Noted: unreadable. Tomorrow's is written differently "
                     "and it will say what changed. If you want to say what "
                     "went wrong, type it now and it goes straight to the "
                     "writer.")


# --------------------------------------------------------------------------
# Where the message sits
# --------------------------------------------------------------------------
def brief_rel(day):
    """The repository-relative path of one day's brief."""
    return "%s/%s.md" % (BRIEFS_DIR, day)


def brief_slot(day):
    """The stem this day's receipt is named from.

    `brief-<day>` rather than the bare stem `outbox.record_base` would give,
    so the name in production/outbound says what the record is about. The
    record's own `file:` line still carries the real path, and
    `outbox.outbound_summary` classifies it by its `receipt:` line, which is
    the ordinary `sent`, because a brief that reached him IS a Producer
    message that reached him.
    """
    return "brief-%s" % day


def day_of(rel):
    """The day a brief path is for, or None if the name is not one."""
    m = BRIEF_NAME_RE.match(str(rel).rsplit("/", 1)[-1])
    return m.group(1) if m else None


def briefs_on_disk(repo):
    """{day: repo-relative path} for every brief in the tree, pattern matched.

    README.md and latest.md are outside this by construction: the pattern is a
    date, so the denominator is briefs and not files.
    """
    d = os.path.join(repo, *BRIEFS_DIR.split("/"))
    out = {}
    if not os.path.isdir(d):
        return out
    for n in sorted(os.listdir(d)):
        day = day_of(n)
        if day:
            out[day] = "%s/%s" % (BRIEFS_DIR, n)
    return out


def today(now=None):
    """The UTC day, as the brief names it."""
    t = datetime.datetime.fromtimestamp(int(now) if now is not None
                                        else int(__import__("time").time()),
                                        datetime.timezone.utc)
    return t.strftime("%Y-%m-%d")


# --------------------------------------------------------------------------
# The two buttons
# --------------------------------------------------------------------------
def callback_data(day, letter):
    return "%s|%s|%s" % (CB_PREFIX, day, str(letter).upper())


def parse_callback(data):
    """(day, verdict, why). `why` is set only when this is not one of ours.

    A tap that is not ours returns (None, None, why) and the bot then tries
    the decision-card parser, so one callback channel carries both kinds
    without either guessing at the other's bytes.
    """
    bits = (data or "").split("|")
    if len(bits) != 3 or bits[0] != CB_PREFIX:
        return None, None, "callback data is not a brief tap"
    day, letter = bits[1].strip(), bits[2].strip().upper()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
        return None, None, "callback data carries no brief day"
    if letter not in LETTER:
        return None, None, "callback data carries no readable verdict"
    return day, LETTER[letter], ""


def keyboard(day):
    """The two buttons, readable first, one row each.

    ROWS RATHER THAN A PAIR SIDE BY SIDE, for the reason `cards.keyboard_for`
    gives: a phone renders two half-width buttons small, and this is the only
    thing he is ever asked to tap about the channel.
    """
    return {"inline_keyboard": [[{"text": BUTTON_FACE[k],
                                 "callback_data": callback_data(day, k)}]
                               for k in ("R", "U")]}


# --------------------------------------------------------------------------
# Sending it. THE WORDS ARE NOT TOUCHED HERE.
# --------------------------------------------------------------------------
def send_brief(day, text, sender, store, check=None, say=None):
    """Send one day's brief with its two buttons. Returns a result dict.

    `sender(text, keyboard)` is the wire, injected so every case below runs
    with no network. `store` is the receipt store (`BriefReceipts`), injected
    so they run with no repository either. `check(rel)` is
    tools/producer-check.py, injected for the same reason AND because its
    place in the order is the ruling: the check runs AFTER the Producer wrote
    and BEFORE the send, as a check on the written message, never as a thing
    that shapes it.

    THE TEXT IS SENT BYTE FOR BYTE. No prefix, no footer, no headline, no
    trailing provenance line. Whatever the Producer wrote is what his phone
    shows; the only thing this adds is the keyboard.
    """
    say = say or (lambda _s: None)
    # ONE CHARACTER COUNT, OF THE BYTES THAT GO ON THE WIRE. It was len() of
    # the file before stripping, which printed briefChars=868 on the done line
    # beside chars=867 in the receipt for the same message: two numbers for one
    # thing, from one variable, which is the instrument fault this project has
    # a casebook about. Caught by reading the rehearsal output rather than by a
    # case, so here is the case: the selftest asserts the two agree.
    body = (text or "").strip()
    res = {"day": day, "rel": brief_rel(day), "chars": len(body),
           "sent": None, "already": None, "refused": None, "clause": "",
           "messageId": None, "records": [], "checked": False,
           "buttons": 0}
    if not body:
        res["refused"] = "the brief for %s is empty, so there is nothing to " \
                         "send" % day
        say("  brief: REFUSED %s: %s" % (res["rel"], res["refused"]))
        return res
    state, detail = store.state(day)
    if state == "sent":
        res["already"] = detail
        say("  brief: ALREADY SENT %s (%s), so nothing was sent this pass"
            % (res["rel"], detail))
        return res
    if state == "held":
        res["refused"] = detail
        say("  brief: HELD %s: %s" % (res["rel"], detail))
        return res
    if check is not None:
        res["checked"] = True
        ok, clause, _out = check(res["rel"])
        if not ok:
            res["refused"] = clause
            res["clause"] = clause
            rec = store.hold(day, clause)
            if rec:
                res["records"].append(rec)
            say("  brief: REFUSED BY THE REGISTER %s: %s"
                % (res["rel"], clause))
            return res
    mark = keyboard(day)
    result = sender(body, mark)
    mid = (result or {}).get("message_id")
    res["messageId"] = mid
    res["buttons"] = len(mark["inline_keyboard"])
    res["sent"] = res["rel"]
    rec = store.sent(day, len(body), mid)
    if rec:
        res["records"].append(rec)
    say("  brief sent: %s chars=%d buttons=%d messageId=%s"
        % (res["rel"], len(body), res["buttons"],
           "none" if mid is None else mid))
    return res


def brief_done_line(res):
    """The whole pass, on one line, every zero beside its denominator.

    WHOLE-PASS NUMBERS ONLY. The per-brief numbers are on the `brief sent:`
    line above, because a reader grepping across lines would otherwise read
    two moments as one.
    """
    day = res.get("day") or "nothing-measured"
    return ("brief-send done: briefDay=%s briefSent=%d/1 briefAlready=%d/1 "
            "briefRefused=%d/1 briefChecked=%s briefButtons=%d "
            "briefChars=%d messageId=%s records=%d clause=%s"
            % (day, 1 if res.get("sent") else 0,
               1 if res.get("already") else 0,
               1 if res.get("refused") else 0,
               "yes" if res.get("checked") else "no",
               res.get("buttons") or 0, res.get("chars") or 0,
               res.get("messageId") if res.get("messageId") else "none",
               len(res.get("records") or []),
               (res.get("refused") or "none").replace(" ", "-")[:90]))


class BriefReceipts:
    """Has this day's brief already been sent, asked of the files on disk.

    THE SAME RECEIPT SHAPE AS EVERY OTHER PRODUCER MESSAGE, through
    `outbox.py`'s own functions rather than a scheme of its own:
    `receipt_rel`, `receipt_is_valid`, `holds_for`, `render_receipt` and
    `render_refusal` are all called, none are copied. That is what makes the
    record readable by `outbox.outbound_summary` and deliverable by
    `tools/inbox-read.py` with nothing added to either.

    WRITING IS FOUR LINES HERE RATHER THAN A CALL TO `outbox._write`, because
    reaching into another module's private name is how two files come to share
    a contract neither states.
    """

    def __init__(self, repo, now=None, outbox_mod=None):
        self.repo = repo
        self.now = now
        if outbox_mod is None:
            import outbox as outbox_mod                       # noqa: PLC0415
        self.outbox = outbox_mod

    def _when(self):
        import time                                           # noqa: PLC0415
        return int(self.now if self.now is not None else time.time())

    def _write(self, rel, text):
        full = os.path.join(self.repo, *rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text if text.endswith("\n") else text + "\n")
        return rel

    def _read(self, rel):
        try:
            with open(os.path.join(self.repo, *rel.split("/")), "r",
                      encoding="utf-8") as fh:
                return fh.read()
        except OSError:
            return None

    def state(self, day):
        """("sent"|"held"|"unsent", detail). A receipt with no message id does
        not prove a send and HOLDS the day rather than sending it twice, which
        is the rule a Producer message already follows."""
        slot = brief_slot(day)
        rel = self.outbox.receipt_rel(slot)
        have = self._read(rel)
        if have is not None:
            good, detail = self.outbox.receipt_is_valid(have)
            if good:
                return "sent", "messageId=%s" % detail
            return "held", ("the receipt for %s does not prove a send (%s), so "
                            "it is held rather than sent again: delete %s once "
                            "you know whether it arrived" % (day, detail, rel))
        held = self.outbox.holds_for(self.repo, slot)
        if held:
            return "held", ("a hold record is on this brief (%s); delete it "
                            "once you know whether it arrived" % held[-1])
        return "unsent", ""

    def sent(self, day, chars, message_id):
        rel = brief_rel(day)
        slot = brief_slot(day)
        commit, epoch = None, None
        try:
            commit, epoch = self.outbox.commit_epoch(self.repo, rel)
        except Exception:                                     # noqa: BLE001
            commit, epoch = None, None
        when = self._when()
        latency = None if epoch is None else when - int(epoch)
        return self._write(
            self.outbox.receipt_rel(slot),
            self.outbox.render_receipt(rel, "brief", when, message_id or 0,
                                       chars, commit, epoch, latency,
                                       "" if epoch is not None
                                       else "the brief is not committed yet"))

    def hold(self, day, clause):
        slot = brief_slot(day)
        return self._write(
            self.outbox.refusal_rel(slot, clause),
            self.outbox.render_refusal(brief_rel(day), "brief", clause,
                                       self._when(), True))


# --------------------------------------------------------------------------
# The tap coming back
# --------------------------------------------------------------------------
def tap_name(day, tapped_epoch, update_id, kind="tap"):
    """`2026-09-10T1830Z-5001.brieftap.txt`, from Telegram's own clock.

    THE INSTANT IN THE NAME IS THE TAP'S, NOT THE BRIEF'S DAY, so two taps on
    one brief are two files and neither overwrites the other. The day is a
    field inside.
    """
    t = datetime.datetime.fromtimestamp(int(tapped_epoch),
                                        datetime.timezone.utc)
    return "%sT%sZ-%s-%s.brieftap.txt" % (t.strftime("%Y-%m-%d"),
                                          t.strftime("%H%M"), int(update_id),
                                          kind)


def render_tap(day, verdict, tapped_epoch, update_id):
    """The whole content of one tap. The day, the verdict, the instant.

    NO CHAT ID AND NO MESSAGE ID FROM THE CHAT, the same credential rule
    `inbox.render_ruling_record` obeys.
    """
    return ("record: tap\nbriefDay: %s\nverdict: %s\ntapped: %s\n"
            "tappedEpoch: %d\nupdate: %d\n"
            % (day, verdict, inbox.iso_utc(tapped_epoch), int(tapped_epoch),
               int(update_id)))


def render_reason(day, text, when_epoch, update_id):
    """WHY IT WAS UNREADABLE, IN HIS OWN WORDS, capped with the cap announced.

    A SECOND RECORD RATHER THAN A FIELD ON THE TAP, because the reason arrives
    after the tap: he taps, the reply asks, he types. Its `record:` line is
    what keeps it out of the tap denominator, so a day with a verdict and a
    reason is one tap and not two.
    """
    one = " ".join((text or "").split())
    if len(one) > REASON_CAP:
        one = one[:REASON_CAP].rstrip() + " (+%d more not shown)" % (
            len(one) - REASON_CAP)
    return ("record: reason\nbriefDay: %s\nreason: %s\nsaid: %s\n"
            "saidEpoch: %d\nupdate: %d\n"
            % (day, one, inbox.iso_utc(when_epoch), int(when_epoch),
               int(update_id)))


def parse_tap(content):
    """(fields, None) or (None, reason). SHAPE CHECKED HERE, so the reader in
    the container never guesses what a malformed record meant."""
    if not content or not content.strip():
        return None, "the file is empty"
    fields = {}
    for line in content.replace("\r\n", "\n").split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    kind = fields.get("record")
    if kind not in ("tap", "reason"):
        return None, "the record: line is neither tap nor reason"
    day = fields.get("briefDay", "")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
        return None, "briefDay is not a date"
    if kind == "tap":
        if fields.get("verdict") not in (READABLE, UNREADABLE):
            return None, "verdict is neither readable nor unreadable"
        try:
            epoch = int(fields.get("tappedEpoch", ""))
        except ValueError:
            return None, "tappedEpoch is not a whole number of seconds"
    else:
        if not fields.get("reason"):
            return None, "a reason record carries no reason"
        try:
            epoch = int(fields.get("saidEpoch", ""))
        except ValueError:
            return None, "saidEpoch is not a whole number of seconds"
    try:
        update = int(fields.get("update", "-1"))
    except ValueError:
        update = -1
    return {"record": kind, "briefDay": day,
            "verdict": fields.get("verdict", ""),
            "reason": fields.get("reason", ""), "epoch": epoch,
            "update": update}, None


def write_tap(repo, day, verdict, tapped_epoch, update_id):
    """Write the tap record, return its repository-relative path."""
    return _write_record(repo, tap_name(day, tapped_epoch, update_id, "tap"),
                         render_tap(day, verdict, tapped_epoch, update_id))


def write_reason(repo, day, text, when_epoch, update_id):
    """Write the reason record, return its repository-relative path."""
    return _write_record(repo,
                         tap_name(day, when_epoch, update_id, "reason"),
                         render_reason(day, text, when_epoch, update_id))


def _write_record(repo, name, body):
    rel = "%s/%s" % (TAP_DIR, name)
    full = os.path.join(repo, *rel.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    return rel


def tap_and_push(repo, day, verdict, tapped_epoch, update_id, say=None,
                 now=None):
    """Write the tap, push it, and return what the reply needs.

    THE SAME TRANSPORT AS A MESSAGE AND A RULING, deliberately: one branch out
    of the PC, one push, one retry path. A tap held by a dead uplink is held on
    disk with everything else and `--flush-inbox` clears it, so it is never
    lost to a wobble.
    """
    say = say or (lambda _s: None)
    import time                                               # noqa: PLC0415
    now = int(now if now is not None else time.time())
    rel = write_tap(repo, day, verdict, tapped_epoch, update_id)
    res = inbox.push_pending(repo, say)
    newest, basis = inbox.newest_work_commit(repo)
    state, age = inbox.studio_state(newest, now)
    res.update(file=rel, day=day, verdict=verdict, state=state, age=age,
               basis=basis, now=now)
    say("  brieftap: file=%s briefDay=%s verdict=%s tapPushed=%s %s"
        % (rel, day, verdict, "yes" if res["ok"] else "NO",
           inbox.studio_key(state, age, basis)))
    return res


def reason_and_push(repo, day, text, when_epoch, update_id, say=None):
    """The same, for the sentence he types after an unreadable tap."""
    say = say or (lambda _s: None)
    rel = write_reason(repo, day, text, when_epoch, update_id)
    res = inbox.push_pending(repo, say)
    res.update(file=rel, day=day)
    say("  briefreason: file=%s briefDay=%s reasonChars=%d reasonPushed=%s"
        % (rel, day, len(" ".join((text or "").split())),
           "yes" if res["ok"] else "NO"))
    return res


def tap_reply_text(res):
    """What he sees in the chat after a tap. No path, no key, no count.

    THE DIRECTOR TEST APPLIES TO THIS TOO. The ruling's words are "no numbers
    with units, no coordinates, no file names, no studio vocabulary", and a
    read-back that said "filed as production/brief-taps/..." would break three
    of the four in one sentence. The ruling record's own path goes to the
    window on the PC through `say`, never to his phone.
    """
    first = (THANKS_READABLE if res.get("verdict") == READABLE
             else THANKS_UNREADABLE)
    if res.get("ok"):
        return first
    return ("%s It is saved here and has not reached the writer yet; the PC "
            "keeps retrying." % first)


# --------------------------------------------------------------------------
# THE ONLY MEASURE OF THE CHANNEL
# --------------------------------------------------------------------------
def taps_from(records):
    """{path: content} to (taps-by-day, reasons-by-day, unreadable-records).

    LAST WINS WITHIN A DAY, by the tap's own instant, and the superseded count
    is carried out so the printer can say it happened rather than hiding it.
    """
    by_day, reasons, bad, superseded = {}, {}, [], 0
    for path in sorted(records):
        fields, why = parse_tap(records[path] or "")
        if fields is None:
            bad.append((path, why))
            continue
        day = fields["briefDay"]
        if fields["record"] == "reason":
            prev = reasons.get(day)
            if prev is None or fields["epoch"] >= prev["epoch"]:
                reasons[day] = fields
            continue
        prev = by_day.get(day)
        if prev is None:
            by_day[day] = fields
        else:
            superseded += 1
            if fields["epoch"] >= prev["epoch"]:
                by_day[day] = fields
    return {"byDay": by_day, "reasons": reasons, "unreadableRecords": bad,
            "superseded": superseded, "records": len(records)}


def sent_days_from_receipts(records):
    """Which days a brief was actually SENT, from the receipts on disk.

    READ OFF THE SAME RECEIPTS THE REST OF THE CHANNEL USES, by their `kind:
    brief` line and a `file:` under production/briefs, so this cannot drift
    from what `outbox.outbound_summary` counts as sent.

    WHAT IT DOES NOT COUNT, NAMED SO THE ZERO IS READABLE: the briefs sent
    before 2026-09-09 out of production/outbox/ as `<date>-<slug>.brief.md`.
    Their receipts exist and they reached him, but they carry no day in the
    shape this path identifies a brief by, and there were no buttons on them
    to tap. So `briefsSentEver` means "sent down the daily path that has
    buttons", which is the only population the acceptance can be measured
    over, and it reads 0 until the first one goes.
    """
    days = {}
    for path in sorted(records):
        body = records[path] or ""
        fields = {}
        for line in body.replace("\r\n", "\n").split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                fields[k.strip()] = v.strip()
        if fields.get("receipt") != "sent" or fields.get("kind") != "brief":
            continue
        day = day_of(fields.get("file", ""))
        if day:
            days[day] = fields.get("sent", "")
    return days


def streak(taps, sent_days=None, want=WANT_CONSECUTIVE):
    """The consecutive readable run, and the denominators it was read with.

    `taps` is `taps_from`'s result. `sent_days` is `sent_days_from_receipts`'s,
    or None when nothing is known about what was sent, which prints as
    nothing measured rather than as zero.

    WHAT THIS IS A STATISTIC OF, named because rule 2 asks: a RUN LENGTH
    counted backwards from the newest tapped day, last-wins within a day. Not
    a peak, not a median, not a total.
    """
    by_day = taps.get("byDay") or {}
    days = sorted(by_day)
    run, run_days = 0, []
    for day in reversed(days):
        if by_day[day]["verdict"] != READABLE:
            break
        run += 1
        run_days.append(day)
    run_days.reverse()
    last_day = days[-1] if days else None
    sent = dict(sent_days or {})
    # THE DENOMINATOR AT THE SAME INSTANT AS THE NUMERATOR: the briefs sent
    # across the span the run covers, so "7 of 7" and "7 readable taps over 12
    # briefs" cannot read as the same fact.
    in_run = [d for d in sent
              if run_days and run_days[0] <= d <= run_days[-1]]
    return {"readableRun": run, "want": want, "runDays": run_days,
            "daysTapped": len(days), "tapsEver": taps.get("records", 0),
            "superseded": taps.get("superseded", 0),
            "lastDay": last_day,
            "lastVerdict": by_day[last_day]["verdict"] if last_day else None,
            "lastReason": (taps.get("reasons") or {}).get(last_day, {}).get(
                "reason", ""),
            "unreadableDays": [d for d in days
                               if by_day[d]["verdict"] == UNREADABLE],
            "briefsSentKnown": sent_days is not None,
            "briefsSentEver": len(sent),
            "briefsSentInRun": len(in_run) if run_days else 0,
            "briefsUntappedInRun": (max(0, len(in_run) - run)
                                    if run_days else 0),
            "met": run >= want}


def streak_line(s):
    """The key=value line. No spaces in any value, every zero with its
    denominator, and the words nothing measured where nothing was."""
    return ("brief-streak: briefStreakReadable=%d/%d briefDaysTapped=%d "
            "briefTapRecords=%d briefTapsSuperseded=%d briefLastDay=%s "
            "briefLastVerdict=%s briefUnreadableDays=%d briefsSentEver=%s "
            "briefsSentInRun=%s briefsUntappedInRun=%s briefAccepted=%s"
            % (s["readableRun"], s["want"], s["daysTapped"], s["tapsEver"],
               s["superseded"], s["lastDay"] or "nothing-measured",
               s["lastVerdict"] or "nothing-measured",
               len(s["unreadableDays"]),
               s["briefsSentEver"] if s["briefsSentKnown"]
               else "nothing-measured",
               s["briefsSentInRun"] if s["briefsSentKnown"]
               else "nothing-measured",
               s["briefsUntappedInRun"] if s["briefsSentKnown"]
               else "nothing-measured",
               "yes" if s["met"] else "no"))


def streak_words(s):
    """The same number in the words Jafar's ruling uses, because the line
    above is for a grep and this is for a reader.

    THE NEVER-RAN CASE IS THE WORDS HE ASKED FOR AND NOT A BARE ZERO, so a
    channel nobody has ever tapped cannot read as a channel that is fine.
    """
    if not s["tapsEver"]:
        return ("%d of %d consecutive, no tap has ever been recorded."
                % (s["readableRun"], s["want"]))
    head = ("%d of %d consecutive readable, last tap %s on %s"  # noqa: E501
            % (s["readableRun"], s["want"], s["lastVerdict"], s["lastDay"]))
    if s["briefsSentKnown"] and s["briefsUntappedInRun"]:
        head += (", over %d brief(s) sent in that span, so %d sent brief(s) "
                 "in the run were never tapped either way"
                 % (s["briefsSentInRun"], s["briefsUntappedInRun"]))
    if s["superseded"]:
        head += (", and %d tap(s) were superseded by a later tap on the same "
                 "day (last wins)" % s["superseded"])
    if s["lastVerdict"] == UNREADABLE:
        head += (". Tomorrow's is written differently and says what changed"
                 + (": %s" % s["lastReason"] if s["lastReason"]
                    else "; he gave no reason"))
    return head + "."


# --------------------------------------------------------------------------
# SELFTEST. No network, no repository, ACCEPTING CASE FIRST.
# --------------------------------------------------------------------------
class _FakeStore:
    """The receipt store, in memory. The disk half is BriefReceipts and is
    covered by tools/runner/outbox.py's own suite through the four functions
    it calls."""

    def __init__(self, state="unsent", detail=""):
        self._state, self._detail = state, detail
        self.sent_days, self.holds = [], []

    def state(self, _day):
        return self._state, self._detail

    def sent(self, day, chars, mid):
        self.sent_days.append((day, chars, mid))
        self._state, self._detail = "sent", "messageId=%s" % mid
        return "production/outbound/%s.receipt.txt" % brief_slot(day)

    def hold(self, day, clause):
        self.holds.append((day, clause))
        return "production/outbound/%s.refused.txt" % brief_slot(day)


def _tap_records(rows):
    """{path: content} for a list of (day, verdict, epoch, update)."""
    out = {}
    for day, verdict, epoch, upd in rows:
        out["%s/%s" % (TAP_DIR, tap_name(day, epoch, upd))] = \
            render_tap(day, verdict, epoch, upd)
    return out


def _receipts(days, kind="brief"):
    out = {}
    for i, day in enumerate(days):
        out["production/outbound/%s.receipt.txt" % brief_slot(day)] = (
            "receipt: sent\nfile: %s\nkind: %s\nsentEpoch: %d\n"
            "messageId: %d\n" % (brief_rel(day), kind, 1757000000 + i, 40 + i))
    return out


def _selftest():
    passed, failed, bad = 0, 0, []

    def check(name, cond, detail=""):
        nonlocal passed, failed
        if cond:
            passed += 1
            print("  ok   %s" % name)
        else:
            failed += 1
            bad.append(name)
            print("  FAIL %s %s" % (name, detail))

    print("brief selftest: the accepting case first, then the refusals.")

    # ---- ACCEPTING: one brief goes out, unchanged, with two buttons -------
    wire, store = [], _FakeStore()
    body = ("HEADLINE: The street is standing.\n\nWHAT CHANGED: Rain on it.\n")
    r1 = send_brief("2026-09-10", body, lambda t, k: (
        wire.append((t, k)) or {"message_id": 501}), store,
        check=lambda _rel: (True, "", ""), say=lambda _s: None)
    check("accept/the-brief-is-sent-byte-for-byte-with-two-buttons",
          len(wire) == 1 and wire[0][0] == body.strip()
          and [b[0]["text"] for b in wire[0][1]["inline_keyboard"]]
          == ["Readable", "Unreadable"]
          and r1["sent"] == "production/briefs/2026-09-10.md"
          and r1["messageId"] == 501, (r1, wire[:1]))
    check("accept/nothing-was-added-to-his-words",
          "brief" not in wire[0][0].lower()
          and wire[0][0].count("\n") == body.strip().count("\n"),
          wire[0][0][:80])
    check("accept/the-receipt-was-written-for-that-day",
          store.sent_days == [("2026-09-10", len(body.strip()), 501)],
          str(store.sent_days))
    check("accept/one-character-count-for-the-done-line-and-the-receipt",
          r1["chars"] == len(body.strip())
          and ("briefChars=%d" % len(body.strip())) in brief_done_line(r1)
          and store.sent_days[0][1] == r1["chars"],
          brief_done_line(r1))
    check("accept/the-done-line-carries-every-zero-with-its-denominator",
          "briefSent=1/1" in brief_done_line(r1)
          and "briefAlready=0/1" in brief_done_line(r1)
          and "briefRefused=0/1" in brief_done_line(r1)
          and " " not in brief_done_line(r1).split("briefDay=")[1].split()[0],
          brief_done_line(r1))
    # THE TAP ROUND TRIP, still accepting.
    data = wire[0][1]["inline_keyboard"][0][0]["callback_data"]
    day, verdict, why = parse_callback(data)
    check("accept/the-readable-button-parses-back-to-its-day-and-verdict",
          (day, verdict, why) == ("2026-09-10", READABLE, "")
          and len(data.encode("utf-8")) <= 64, (data, day, verdict, why))
    rec = render_tap("2026-09-10", READABLE, 1757500000, 7001)
    fields, why = parse_tap(rec)
    check("accept/a-tap-record-round-trips-through-its-own-parser",
          why is None and fields["briefDay"] == "2026-09-10"
          and fields["verdict"] == READABLE and fields["record"] == "tap",
          (fields, why))
    check("accept/the-record-name-matches-the-transport-pattern",
          bool(TAP_RE.match(tap_name("2026-09-10", 1757500000, 7001))),
          tap_name("2026-09-10", 1757500000, 7001))
    check("accept/and-the-reply-he-sees-carries-no-path-no-key-no-count",
          all(ch not in tap_reply_text({"verdict": READABLE, "ok": True})
              for ch in "=/")
          and not any(c.isdigit()
                      for c in tap_reply_text({"verdict": READABLE,
                                               "ok": True})),
          tap_reply_text({"verdict": READABLE, "ok": True}))

    # ---- THE STREAK, ON THE CASE IT MUST COUNT ---------------------------
    seven = [("2026-09-%02d" % (10 + i), READABLE, 1757500000 + i * 86400,
              7000 + i) for i in range(7)]
    s7 = streak(taps_from(_tap_records(seven)),
                sent_days_from_receipts(_receipts([d for d, _, _, _ in seven])))
    check("accept/seven-readable-taps-in-a-row-is-the-acceptance",
          s7["readableRun"] == 7 and s7["met"] is True
          and s7["briefsSentInRun"] == 7 and s7["briefsUntappedInRun"] == 0
          and "briefStreakReadable=7/7" in streak_line(s7)
          and "briefAccepted=yes" in streak_line(s7), streak_line(s7))
    gapped = streak(taps_from(_tap_records(seven[:3] + seven[5:])),
                    sent_days_from_receipts(
                        _receipts([d for d, _, _, _ in seven])))
    check("accept/five-taps-over-seven-sent-briefs-says-both-numbers",
          gapped["readableRun"] == 5 and gapped["briefsSentInRun"] == 7
          and gapped["briefsUntappedInRun"] == 2
          and "never tapped either way" in streak_words(gapped),
          streak_words(gapped))

    # ---- REJECTING: one unreadable resets it, and says so ----------------
    broken = streak(taps_from(_tap_records(
        seven[:6] + [("2026-09-16", UNREADABLE, 1757500000 + 6 * 86400,
                      7006)])))
    check("reject/one-unreadable-tap-resets-the-run-to-zero",
          broken["readableRun"] == 0 and broken["met"] is False
          and broken["lastVerdict"] == UNREADABLE
          and "briefStreakReadable=0/7" in streak_line(broken),
          streak_line(broken))
    check("reject/and-the-words-say-tomorrow-is-written-differently",
          "written differently" in streak_words(broken)
          and "he gave no reason" in streak_words(broken),
          streak_words(broken))
    # THE NEVER-RAN CASE, WHICH MUST NOT READ AS CLEAN.
    empty = streak(taps_from({}), sent_days_from_receipts({}))
    check("reject/no-tap-ever-prints-the-words-and-not-a-bare-zero",
          streak_words(empty)
          == "0 of 7 consecutive, no tap has ever been recorded."
          and "briefLastDay=nothing-measured" in streak_line(empty),
          streak_words(empty))
    check("reject/and-nothing-known-about-sends-prints-nothing-measured",
          "briefsSentEver=nothing-measured"
          in streak_line(streak(taps_from({}), None)),
          streak_line(streak(taps_from({}), None)))
    # LAST WINS WITHIN A DAY, AND THE SUPERSEDED TAP IS COUNTED.
    twice = streak(taps_from(_tap_records(
        [("2026-09-10", UNREADABLE, 1757500000, 7001),
         ("2026-09-10", READABLE, 1757500060, 7002)])))
    check("reject/two-taps-on-one-day-are-last-wins-and-the-first-is-counted",
          twice["readableRun"] == 1 and twice["superseded"] == 1
          and "briefTapsSuperseded=1" in streak_line(twice),
          streak_line(twice))
    # A REASON REACHES TOMORROW'S WRITER.
    with_reason = dict(_tap_records(
        [("2026-09-10", UNREADABLE, 1757500000, 7001)]))
    with_reason["%s/%s" % (TAP_DIR, tap_name("2026-09-10", 1757500100, 7002,
                                            "reason"))] = render_reason(
        "2026-09-10", "too many words about the studio", 1757500100, 7002)
    sr = streak(taps_from(with_reason))
    check("reject/the-reason-he-typed-is-carried-to-tomorrows-writer",
          sr["lastReason"] == "too many words about the studio"
          and sr["readableRun"] == 0
          and "too many words about the studio" in streak_words(sr),
          streak_words(sr))
    check("reject/a-long-reason-announces-the-cut",
          "(+%d more not shown)" % 20
          in render_reason("2026-09-10", "x" * (REASON_CAP + 20), 1, 2),
          render_reason("2026-09-10", "x" * (REASON_CAP + 20), 1, 2)[-60:])

    # ---- REJECTING: the send path refuses rather than guessing -----------
    empty_store = _FakeStore()
    r_empty = send_brief("2026-09-11", "   ", lambda t, k: {"message_id": 1},
                         empty_store)
    check("reject/an-empty-brief-is-not-sent",
          r_empty["sent"] is None and "is empty" in r_empty["refused"]
          and "briefSent=0/1" in brief_done_line(r_empty),
          brief_done_line(r_empty))
    again = send_brief("2026-09-10", body, lambda t, k: {"message_id": 2},
                       store)
    check("reject/a-day-already-sent-is-not-sent-twice",
          again["sent"] is None and again["already"]
          and "briefAlready=1/1" in brief_done_line(again),
          brief_done_line(again))
    refused_wire, rstore = [], _FakeStore()
    r_ref = send_brief("2026-09-12", body,
                       lambda t, k: refused_wire.append(t), rstore,
                       check=lambda _rel: (False, "the brief runs to 180 "
                                                  "words of 150", ""))
    check("reject/a-brief-the-register-refuses-never-reaches-the-wire",
          not refused_wire and r_ref["sent"] is None
          and r_ref["clause"].startswith("the brief runs")
          and rstore.holds and "briefRefused=1/1" in brief_done_line(r_ref),
          brief_done_line(r_ref))
    held = send_brief("2026-09-13", body, lambda t, k: {"message_id": 3},
                      _FakeStore("held", "a hold record is on this brief"))
    check("reject/a-held-day-is-not-sent-either",
          held["sent"] is None and "hold record" in held["refused"],
          held["refused"])
    # AND A CALLBACK THAT IS NOT OURS IS HANDED BACK, NOT GUESSED AT.
    d2, v2, w2 = parse_callback("r|85bff034|B")
    check("reject/a-decision-card-tap-is-not-read-as-a-brief-tap",
          d2 is None and v2 is None and "not a brief tap" in w2, w2)
    for data, what in (("b|nope|R", "no brief day"),
                       ("b|2026-09-10|Z", "no readable verdict"),
                       ("", "not a brief tap")):
        d3, _v3, w3 = parse_callback(data)
        check("reject/%s" % what.replace(" ", "-"),
              d3 is None and what in w3, (data, w3))
    f_bad, why_bad = parse_tap("record: tap\nbriefDay: 2026-09-10\n"
                               "verdict: maybe\ntappedEpoch: 1\nupdate: 1\n")
    check("reject/a-record-with-an-invented-verdict-is-refused",
          f_bad is None and "neither readable nor unreadable" in why_bad,
          why_bad)
    f_bad2, why_bad2 = parse_tap("hello\n")
    check("reject/a-record-that-is-not-one-is-refused-with-a-reason",
          f_bad2 is None and why_bad2, why_bad2)
    taps_bad = taps_from({"%s/x.brieftap.txt" % TAP_DIR: "hello\n"})
    check("reject/an-unreadable-record-is-counted-not-dropped",
          len(taps_bad["unreadableRecords"]) == 1
          and taps_bad["records"] == 1, taps_bad["unreadableRecords"])

    print("brief selftest: %d passed, %d failed, %d checks run%s"
          % (passed, failed, passed + failed,
             "" if not bad else " FAILED: " + ", ".join(bad[:4])))
    return 0 if not failed else 3


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv[1:] else
             (print(__doc__.strip()) or 0))
