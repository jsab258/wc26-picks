#!/usr/bin/env python3
"""The studio's Telegram channel, running on Jafar's PC. Standard library only.

    START THE TELEGRAM BOT.bat                 what Jafar double-clicks
    python3 tools/runner/telegram-bot.py       the same thing, from a shell
    python3 tools/runner/telegram-bot.py --send "text"    one unprompted push
    python3 tools/runner/telegram-bot.py --send-file PATH  one CHECKED message
    python3 tools/runner/telegram-bot.py --send-outbox     sweep the outbox
    python3 tools/runner/telegram-bot.py --send-frame      one verified picture
    python3 tools/runner/telegram-bot.py --send-cards      the WAITING cards
    python3 tools/runner/telegram-bot.py --selftest       offline, no network

WHAT IT DOES TODAY, and the list is short on purpose (queue 067, narrowed to
one builder pass): it starts and keeps running, it reads the credentials out
of tools/runner/config.local, it answers anything Jafar types, it PUSHES a
message he did not ask for, and it asks for BOTH budget meters. Gallery
images, notes and voice memos are still Monday's work and are deliberately
absent rather than half-present.

BUTTONS FOR RULINGS, TYPED DIGITS FOR MEASUREMENTS, and that distinction is
the point rather than a style. RULED 2026-09-05 (queue 104): a preset grid on
a meter question turns a reading he SAW into a reading he ROUNDED, and near
the ceiling that difference is the difference between stopping and carrying
on. So the meter questions carry no keyboard at all, they take the number as
typed, and anything that is not a whole number from 0 to 100 is REFUSED with
a message rather than rounded or coerced. Queue 090's decision cards keep
their buttons, because choosing among named options is exactly what a preset
is for.

AND SINCE QUEUE 090, A TAP IS A RULING. A WAITING card in
production/decision-queue.md is sent with one inline button per option; a tap
arrives as a `callback_query`, is answered so his phone stops spinning, and is
written as a RULING RECORD onto the same branch as the inbox. The PC never
edits the decision queue itself: `tools/inbox-read.py` folds the records into
it in the container, where one writer owns that file. The card format, the
buttons and the fold are all `tools/runner/cards.py`.

AND SINCE QUEUE 088, THE INBOUND HALF: every message he types that is not a
command is written to `production/inbox/` and pushed to the `pc-inbox`
branch, and the reply says whether the studio is awake and, if it is asleep,
when it next wakes. The transport is `tools/runner/inbox.py` and every rule
it obeys about not disturbing `tools/pc-watcher.py` is in that file's
docstring. A push that fails keeps the message on this PC and retries; it is
never dropped.
A message that arrives while this bot is NOT running is the other case, and
since queue 090 it is no longer lost: `skip_backlog` FILES the backlog's text
messages from the configured chat, each with its own Telegram date, replies
once with the count, and applies none of them as budget answers. It does not
answer them one by one, because three days of history shouted back at him is
what that call was written to avoid.

AND SINCE QUEUE 089 AND 091, THE OUTBOUND HALF: every two minutes it sweeps
`production/outbox/`, runs `tools/producer-check.py --kind <kind>` HERE on the
sending side, sends only on a pass, and writes a receipt carrying the message
id the platform returned back onto the `pc-inbox` branch. A refused message is
never sent and its failing clause travels back to the studio as a record.
`--send-frame` carries `tools/report-frame.py`'s answer as a PHOTO with one
caption line, including the answer "nothing measured", which arrives as those
words rather than as an old frame reused. The module is
`tools/runner/outbox.py`.

THE CHECK IS WIRED ON THE PRODUCER CONTENT CLASS, NOT INSIDE `send()`. The
bot's own chrome (the opening line, the budget question) fails the register by
construction, so `--send-file` and the outbox sweep are checked and `send()`
is not. Ruled 2026-09-05.

NO DEPENDENCY. The Telegram bot API is HTTP with JSON, and urllib does it, so
nothing new enters the licence allowlist for this. The photo upload is a
multipart body built by hand in `multipart()` for that reason.

THE CREDENTIAL RULE. Every line this program prints goes through
`botconfig.redact`, because the token travels inside every API URL and one
unscrubbed traceback would burn it and cost Jafar a trip to BotFather. There
is no logging of the config file, no length of it, no prefix of it.

WHAT IT CANNOT BE TESTED AGAINST HERE. Every external host is blocked from
the build container, so the network half of this file has never run where it
was written. UNVERIFIABLE UNTIL THE PC. `--selftest` covers the halves that
do not need a network: the config reader and the message arithmetic. The
first double-click on Jafar's PC is the accepting case.

EXIT CODES. 0 stopped cleanly. 1 it could not start or it crashed; the window
says which. 3 selftest failed.
"""
import datetime
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import botconfig                                              # noqa: E402
import cards                                                  # noqa: E402
import inbox                                                  # noqa: E402
import outbox                                                 # noqa: E402

API = "https://api.telegram.org/bot%s/%s"

#: THE CEILING IS NOT INVENTED HERE. 80 percent is the number
#: production/NOW.md carries as the spend ceiling, and the rule that goes with
#: it is that the HIGHER of the two meters governs, which is why this asks for
#: both rather than one. If Jafar moves the ceiling, this constant moves with
#: the document and not before it.
CEILING_PCT = 80

#: THE PRESET GRID IS GONE, RULED 2026-09-05 (queue 104). It was 15 buttons
#: spanning 0 to 100 in steps of 5 and 10, and the meter reports integers, so
#: every button that was not the exact reading was a rounding recorded as a
#: measurement. Jafar: "no preset buttons. Ask for the exact number and take
#: it as typed, reject anything that is not an integer rather than rounding
#: it. Presets are for rulings, never for measurements."
#:
#: THIS IS WHAT GOES IN ITS PLACE, and it is not the absence of a keyboard.
#: A `one_time_keyboard` sent before this change can still be sitting on his
#: phone, and not sending a new one does not take it away; removing it is an
#: explicit parameter. Every meter question carries it.
REMOVE_KEYBOARD = {"remove_keyboard": True}

#: NO NUMERIC KEYPAD IS AVAILABLE TO A BOT, and this line is the honest answer
#: rather than a comment claiming one. Read against the Bot API: the fields a
#: bot may set on an outgoing message are `reply_markup` (inline keyboard,
#: reply keyboard, keyboard removal, force reply) and, inside a reply keyboard
#: or a ForceReply, `input_field_placeholder`. A reply keyboard's buttons can
#: request a contact, a location, a poll, a user, a chat or a web app. NOTHING
#: in that list selects the phone's keyboard type, so "numeric keypad where
#: the platform allows" resolves to: the platform does not allow it. The
#: placeholder is the whole of what can be asked for, and it says what is
#: wanted in words.
NUMERIC_PLACEHOLDER = "a whole number from 0 to 100"

#: The meter reads whole percent, so the bound is a whole number and the
#: refusal names it. Both ends inclusive.
READING_MIN, READING_MAX = 0, 100

REPLY_CAP = 200        # characters of his own text echoed back, cap announced


class ApiError(Exception):
    """kind is one of token, chat, network, telegram. The kind is what tells
    Jafar which of three completely different problems he has, from the window
    alone, without sending anything sensitive to anyone."""

    def __init__(self, kind, message):
        Exception.__init__(self, message)
        self.kind = kind


class Console(object):
    """Everything printed goes through here, and here is where the scrubbing
    is. One printer, one place to get the redaction right."""

    def __init__(self):
        self.secrets = []

    def guard(self, secrets):
        self.secrets = list(secrets)

    def say(self, text=""):
        line = botconfig.redact(text, self.secrets)
        stamp = datetime.datetime.now().strftime("%H:%M:%S")
        print("%s  %s" % (stamp, line) if line else "")
        sys.stdout.flush()


OUT = Console()


# --------------------------------------------------------------------------
# The wire
# --------------------------------------------------------------------------
def _post(token, method, data, headers=None, timeout=40):
    """One POST to the API. Raises ApiError with a kind and a message that
    never contains the URL, because the URL contains the token.

    FACTORED OUT for queue 091 so that the photo upload and the text send
    fail in exactly the same words. Two error-handling arms would be two
    places for the token to leak from, and only one of them would be tested.
    """
    req = urllib.request.Request(API % (token, method), data=data)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as fh:
            body = fh.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            desc = json.loads(e.read().decode("utf-8", "replace")).get(
                "description", "")
        except Exception:                                     # noqa: BLE001
            desc = ""
        if e.code in (401, 404):
            raise ApiError("token", "Telegram refused the token (HTTP %d). "
                                    "The token in config.local is wrong, "
                                    "truncated, or was revoked." % e.code)
        if "chat not found" in desc.lower() or "chat_id" in desc.lower():
            raise ApiError("chat", "Telegram accepted the token and refused "
                                   "the chat id (HTTP %d: %s). The chat id in "
                                   "config.local is wrong, or you have not "
                                   "pressed Start in the chat with the bot."
                                   % (e.code, desc or "no description"))
        raise ApiError("telegram", "Telegram said no (HTTP %d: %s)"
                       % (e.code, desc or "no description"))
    except (urllib.error.URLError, socket.timeout, socket.error, OSError) as e:
        raise ApiError("network", "Could not reach Telegram at all (%s). "
                                  "This is the network, not the token."
                       % type(e).__name__)
    try:
        payload = json.loads(body)
    except ValueError:
        raise ApiError("telegram", "Telegram sent something that is not JSON "
                                   "(%d byte(s))" % len(body))
    if not payload.get("ok"):
        raise ApiError("telegram", "Telegram said no (%s)"
                       % payload.get("description", "no description"))
    return payload.get("result")


def call(token, method, params, timeout=40):
    """One form-encoded API call."""
    return _post(token, method,
                 urllib.parse.urlencode(params).encode("utf-8"),
                 None, timeout)


def multipart(fields, files, boundary=None):
    """(content_type, body) for a multipart/form-data POST, by hand.

    STANDARD LIBRARY ONLY, which is why this exists: urllib posts bytes and
    nothing in the standard library builds this body. Nothing new enters the
    licence allowlist for a photo upload.

    The boundary is a parameter so the selftest can pin it and read the body
    back byte for byte instead of trusting that it looks right.
    """
    boundary = boundary or ("----LEDGER%d" % int(time.time() * 1000))
    out = []
    for name, value in (fields or {}).items():
        out.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n"
                    "\r\n%s\r\n" % (boundary, name, value)).encode("utf-8"))
    for name, (filename, blob, ctype) in (files or {}).items():
        out.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"; "
                    "filename=\"%s\"\r\nContent-Type: %s\r\n\r\n"
                    % (boundary, name, filename, ctype)).encode("utf-8"))
        out.append(blob)
        out.append(b"\r\n")
    out.append(("--%s--\r\n" % boundary).encode("utf-8"))
    return ("multipart/form-data; boundary=%s" % boundary, b"".join(out))


def send_photo(token, chat_id, path, caption, timeout=180):
    """One picture, AS A PICTURE. Returns the platform's result payload.

    `sendPhoto` rather than `sendDocument` on purpose: a document arrives as a
    file to tap, and the deliverable is the photo in the chat. The proof of
    which one happened is the `photo` array in the answer, which the receipt
    carries; this function does not judge it, it returns it.
    """
    with open(path, "rb") as fh:
        blob = fh.read()
    ctype, body = multipart({"chat_id": str(chat_id), "caption": caption},
                            {"photo": (os.path.basename(path), blob,
                                       "image/jpeg")})
    return _post(token, "sendPhoto", body, {"Content-Type": ctype}, timeout)


def send_params(chat_id, text, markup=None):
    """The parameters one sendMessage would carry. PURE, and separate from
    `send` so the selftest can read what a meter question actually asks for
    instead of trusting that it asks for nothing."""
    params = {"chat_id": chat_id, "text": text,
              "disable_web_page_preview": "true"}
    if markup is not None:
        params["reply_markup"] = json.dumps(markup)
    return params


def send(token, chat_id, text, markup=None):
    """One message. `markup` is a reply_markup OBJECT (an inline keyboard for
    a decision card, REMOVE_KEYBOARD for a meter question) or None."""
    return call(token, "sendMessage", send_params(chat_id, text, markup))


def answer_callback(token, callback_id, text):
    """Stop the spinner on his phone, and say what happened in the toast.

    WITHOUT THIS THE TAP LOOKS BROKEN. Telegram keeps a progress indicator on
    the button until the bot answers the callback, so an unanswered tap reads
    as a dead card even when the ruling was filed. The toast is capped at 200
    characters by the platform, so it is cut HERE with the cut announced,
    rather than being silently truncated on the wire.
    """
    body = text if len(text) <= 190 else text[:190] + " (+%d)" % (len(text) - 190)
    return call(token, "answerCallbackQuery",
                {"callback_query_id": callback_id, "text": body,
                 "show_alert": "false"})


# --------------------------------------------------------------------------
# The arithmetic and the strings, which live HERE because here is where the
# tests run (the instruments rule: an unrun formatter printing a plausible
# string is the silent-instrument failure).
# --------------------------------------------------------------------------
def parse_reading(text):
    """(int, "") for a meter reading, or (None, why). RULED 2026-09-05.

    TAKEN AS TYPED AND NEVER ROUNDED. The meter reports whole percent, so the
    only honest reading is a whole number: "76,5" and "76.5" are refused
    rather than rounded to 76 or 77, because a rounded reading near the
    ceiling is the difference between stopping and carrying on, and a coerced
    one is a number the studio invented and wrote down as his.
    """
    t = (text or "").strip().lower()
    for junk in ("percent", "per cent", "%"):
        t = t.replace(junk, "")
    t = t.strip()
    if not t:
        return None, "you sent nothing"
    if not re.match(r"^[+-]?\d+$", t):
        return None, "that is not a whole number"
    v = int(t)
    if v < READING_MIN or v > READING_MAX:
        return None, ("%d is outside 0 to 100" % v)
    return v, ""


def refusal_text(why, meter):
    """What he sees when a reading is refused. It says what is wanted, not
    just that this was wrong, and it never guesses at what he meant."""
    return ("I cannot take that as the %s meter: %s. The meter shows whole "
            "percent and I record exactly what you type, so I round nothing "
            "and guess nothing. Send %s, like 77. Nothing was recorded."
            % (meter.upper(), why, NUMERIC_PLACEHOLDER))


def fmt_pct(v):
    """KEPT FRACTION-CAPABLE ON PURPOSE. The INPUT is now integers only, but
    this formats the arithmetic below, and `headroomPct` is a difference that
    is read against `production/budget.md`, whose own percentages carry a
    decimal. Deleting the fractional arm by reflex would have printed 91.5 as
    91."""
    return ("%d" % v) if float(v).is_integer() else ("%.1f" % v)


def budget_reading(total, fable, ceiling=CEILING_PCT):
    """Both meters to (what the bot says, one key=value line for the log).

    THE GOVERNING METER IS THE HIGHER ONE, at-worst rather than average,
    because the ceiling binds on whichever meter reaches it first: on
    1 September that was Fable and on 4 September it was the total, so no
    session may infer one from the other. `headroomPct` is ceiling minus the
    governing meter, and it goes negative rather than clamping at zero,
    because a clamp would make over-ceiling read the same as exactly at it.
    """
    governing = "total" if total >= fable else "fable"
    high = max(total, fable)
    headroom = ceiling - high
    if headroom > 0:
        where = "%s point(s) under the %d percent ceiling" % (fmt_pct(headroom), ceiling)
    elif headroom == 0:
        where = "exactly on the %d percent ceiling" % ceiling
    else:
        where = "%s point(s) OVER the %d percent ceiling" % (fmt_pct(-headroom), ceiling)
    text = ("Read back: total %s percent, Fable %s percent.\n"
            "The higher meter governs, so that is %s at %s percent, %s.\n"
            "Written down on the PC. Getting it into the repo by itself is "
            "Monday's work." % (fmt_pct(total), fmt_pct(fable), governing,
                                fmt_pct(high), where))
    # `source=typed` IS QUEUE 082'S FIELD, AND ITS OTHER VALUE IS RETIRED.
    # Rows written before 2026-09-05 can carry `source=button`, which meant a
    # preset grid the reading may have been rounded onto; the grid is gone and
    # nothing writes that value any more. The name is kept so the older rows
    # stay readable rather than becoming a value nobody can look up.
    line = ("budgetTotalPct=%s budgetFablePct=%s governing=%s "
            "governingPct=%s ceilingPct=%d headroomPct=%s source=typed"
            % (fmt_pct(total), fmt_pct(fable), governing, fmt_pct(high),
               ceiling, fmt_pct(headroom)))
    return text, line


def echo_reply(text, tail=None):
    """His own words back, with the cap announced when it bites."""
    body = text if len(text) <= REPLY_CAP else (
        text[:REPLY_CAP] + " (+%d more character(s) not shown)"
        % (len(text) - REPLY_CAP))
    return "Heard: %s\n\n%s" % (body, tail or (
        "That reply is the proof the channel works both ways. "
        "Commands: /budget, /ping, /help."))


HELP = ("LEDGER studio channel.\n"
        "/budget  the two meter readings, typed as whole numbers\n"
        "/ping    am I still alive\n"
        "/help    this\n\n"
        "Working today: anything you type that is not one of those commands "
        "is FILED for the studio, and I tell you whether the studio is awake "
        "and, if not, when it next wakes. I can also send you something you "
        "did not ask for, and I send decision cards with one button per "
        "option: a tap is filed as your ruling.\n"
        "Buttons are for rulings only. A meter reading is typed and taken "
        "exactly as typed, because a button would be a rounding.\n"
        "Not built yet: gallery pictures and voice memos.\n"
        "To stop me, close the black window on the PC.")

OPENING = ("LEDGER studio channel is open.\n"
           "You did not ask for this message, which is the part a Blocking "
           "item needs.\n"
           "Send me anything and I will file it for the studio and answer "
           "you, which proves the other direction. /help lists what works "
           "today.")

BUDGET_Q = ("Budget reading, please. Two numbers, and the studio needs both "
            "because the higher one governs.\n"
            "1 of 2: the TOTAL meter, percent used. Type it as %s: I record "
            "exactly what you type and round nothing." % NUMERIC_PLACEHOLDER)
BUDGET_Q2 = ("2 of 2: the FABLE meter, percent used. %s, as typed."
             % NUMERIC_PLACEHOLDER.capitalize())


def log_budget(line):
    """One line into a gitignored log on the PC. production/logs/ is in
    .gitignore, so this can never travel into a commit, and it is written
    where Jafar can read it back without the bot running."""
    d = os.path.join(REPO, "production", "logs")
    try:
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "telegram-budget.log"), "a",
                  encoding="utf-8") as fh:
            fh.write("%s %s\n" % (datetime.datetime.now().isoformat(
                timespec="seconds"), line))
        return True
    except OSError:
        return False


# --------------------------------------------------------------------------
# The loop
# --------------------------------------------------------------------------
class Bot(object):
    def __init__(self, creds, repo=None):
        self.token = creds.token
        self.chat = str(creds.chat_id)
        self.creds = creds
        self.offset = None
        self.seen = 0          # updates read off the wire, the denominator
        self.mine = 0          # of those, from the configured chat
        self.other = 0         # of those, from anywhere else, ignored
        self.nontext = 0
        self.net_errors = 0    # cumulative, whole run
        self.readings = 0      # meter answers RECORDED, whole run
        self.answers = 0       # messages arriving while a meter is pending
        self.refused = 0       # of those, refused as not a whole number
        self.pending = None    # None, "total" or "fable"
        self.total = None
        self.started = time.time()
        # THE TAPS, queue 090. Cumulative, each against the set it came from.
        self.taps = 0          # callback updates seen, the denominator
        self.taps_filed = 0    # of those, written as a ruling record
        self.taps_refused = 0  # of those, refused with a reason
        # THE BACKLOG, filed once at startup rather than dropped.
        self.backlog_seen = 0
        self.backlog_filed = 0
        # THE INBOX HALF. `repo` is a parameter so the selftest can point the
        # whole path at a throwaway repository instead of this one.
        self.repo = repo or REPO
        self.filed = 0         # messages written to production/inbox
        self.pushed = 0        # of those, that reached the branch
        self.push_fails = 0    # cumulative, whole run
        self.last_flush = 0.0  # when the retry last ran, a wall clock
        # THE OUTBOUND HALF, queue 089. Cumulative over the whole run, each
        # against the set it came from on the done line.
        self.last_outbox = 0.0
        self.out_passes = 0
        self.out_sent = 0
        self.out_refused = 0

    # -- startup ----------------------------------------------------------
    def hello(self):
        me = call(self.token, "getMe", {})
        name = "@" + str(me.get("username", "unknown"))
        OUT.say("connected to Telegram as %s" % name)
        return name

    def skip_backlog(self):
        """FILE the backlog, answer it once, and apply none of it.

        RULED 2026-09-05 (088 batch, section 4), and it inverts half of what
        this did. It used to count the backlog and drop it, so a message sent
        to a closed window was never filed and Jafar was never told: the one
        case the inbox exists for was the one case it did not cover.

        THREE THINGS IT STILL WILL NOT DO, and each is deliberate. It does not
        answer the messages one by one, because that is the bot shouting three
        days of history at him. It does not apply any of them as a budget
        answer, because the question they would answer was asked in a run that
        has ended and a number from Tuesday is not today's reading. It does
        not file commands: `/ping` from yesterday is not a message for the
        studio, and a stale command answered late reads as a bot doing
        something unasked.

        ONE PUSH FOR THE WHOLE BACKLOG rather than one per message: the files
        are written first and `push_pending` moves all of them, so a backlog
        of thirty costs one commit instead of thirty.
        """
        try:
            updates = call(self.token, "getUpdates", {"timeout": 0}, timeout=30)
        except ApiError as e:
            if e.kind == "network":
                raise
            updates = []
        updates = updates or []
        n = len(updates)
        if n:
            self.offset = updates[-1]["update_id"] + 1
        self.backlog_seen += n
        mine, foreign, nontext, commands, taps, written = 0, 0, 0, 0, 0, []
        for u in updates:
            msg = u.get("message") or u.get("edited_message")
            if not msg:
                taps += 1
                continue
            if str((msg.get("chat") or {}).get("id")) != self.chat:
                foreign += 1
                continue
            text = msg.get("text")
            if not text:
                nontext += 1
                continue
            mine += 1
            if text.strip().lower().split("@")[0].startswith("/"):
                commands += 1
                continue
            date = msg.get("date")
            if not isinstance(date, int):
                date = int(time.time())
            try:
                written.append(inbox.write_message(self.repo, text, date,
                                                   u["update_id"]))
            except Exception as e:                            # noqa: BLE001
                self.push_fails += 1
                OUT.say("backlog: could not file one message (%s); the rest "
                        "of the backlog is still handled"
                        % type(e).__name__)
        pushed = 0
        if written:
            self.filed += len(written)
            self.backlog_filed += len(written)
            try:
                res = inbox.push_pending(self.repo, OUT.say)
                pushed = len(res["pushed"])
                self.pushed += pushed
                if not res["ok"]:
                    self.push_fails += 1
            except Exception as e:                            # noqa: BLE001
                self.push_fails += 1
                OUT.say("backlog: filed %d message(s) but the push could not "
                        "run (%s). Nothing is dropped; the retry takes them."
                        % (len(written), type(e).__name__))
        OUT.say("backlog: updatesWaiting=%d fromYou=%d/%d filed=%d/%d "
                "pushed=%d/%d commandsSkipped=%d/%d nonText=%d/%d "
                "otherChats=%d/%d taps=%d/%d appliedAsBudget=0/%d"
                % (n, mine, n, len(written), mine, pushed, len(written),
                   commands, mine, nontext, mine, foreign, n, taps, n,
                   len(written)))
        if n == 0:
            OUT.say("backlog: nothing measured, 0 update(s) were waiting, so "
                    "nothing arrived while this bot was not running.")
        if written:
            self.last_flush = time.time()
            self.reply(
                "While I was not running, %d message(s) arrived from you and "
                "I have filed all %d for the studio, each with the time YOU "
                "sent it. I am not answering them one by one, and none of "
                "them was taken as a budget reading. %s"
                % (len(written), len(written),
                   "They are on the %s branch." % inbox.INBOX_BRANCH if pushed
                   == len(written) else
                   "%d of them are still on the PC and the retry takes them; "
                   "none are dropped." % (len(written) - pushed)))
        return n

    # -- handling ---------------------------------------------------------
    def reply(self, text, markup=None):
        send(self.token, self.chat, text, markup)

    def answer_tap(self, callback_id, text):
        """The one seam the tap path uses to reach the wire, so the selftest
        can prove a tap is ANSWERED without touching the network."""
        if not callback_id:
            return
        try:
            answer_callback(self.token, callback_id, text)
        except ApiError as e:
            OUT.say("could not answer that tap (%s); the ruling itself is "
                    "unaffected" % e.kind)

    def ask_budget(self):
        """The meter question, carrying NO preset keyboard and REMOVING any
        the phone is still holding (queue 104)."""
        self.pending = "total"
        self.total = None
        self.reply(BUDGET_Q, REMOVE_KEYBOARD)
        OUT.say("asked for the budget reading, meter 1 of 2, typed "
                "(keyboard=none removeKeyboard=yes)")

    # -- the inbox ---------------------------------------------------------
    def file_message(self, text, sent_epoch, update_id):
        """Write it, push it, and return the lines that go under the echo.

        WRAPPED, BECAUSE A BROKEN INBOX MUST NOT TAKE THE CHANNEL DOWN. If
        anything in the git path throws, Jafar still gets an answer and the
        window still says which line it came from. The message text is not
        printed with the fault: same rule as the crash handler at the bottom
        of this file.
        """
        try:
            res = inbox.file_and_push(self.repo, text, sent_epoch, update_id,
                                      OUT.say)
        except Exception as e:                                # noqa: BLE001
            self.push_fails += 1
            OUT.say("inbox: FAILED to file the message (%s). The channel "
                    "keeps running." % type(e).__name__)
            return ("I could not file that on the PC (%s). It is NOT saved, "
                    "so please send it again once the window on the PC stops "
                    "showing that error." % type(e).__name__)
        self.filed += 1
        if res["ok"]:
            self.pushed += 1
        else:
            self.push_fails += 1
        self.last_flush = time.time()
        return inbox.reply_text(res)

    def flush_inbox(self, every=60):
        """Retry anything held on disk, at most once a minute.

        A MESSAGE HELD BY A NETWORK WOBBLE MUST NOT WAIT FOR THE NEXT ONE.
        `pending_files` derives the backlog from the branch's own tree, so
        this is correct after a crash, a restart or an uplink that came back
        while nothing was being typed.
        """
        if time.time() - self.last_flush < every:
            return
        self.last_flush = time.time()
        try:
            waiting, _tip = inbox.pending_files(self.repo)
            if not waiting:
                return
            res = inbox.push_pending(self.repo, OUT.say)
        except Exception as e:                                # noqa: BLE001
            OUT.say("inbox: the retry could not run (%s)" % type(e).__name__)
            return
        if res["ok"] and res["pushed"]:
            self.pushed += len(res["pushed"])
            self.reply("The %d message(s) I was holding on the PC are on the "
                       "branch now. Nothing was lost."
                       % len(res["pushed"]))
        elif not res["ok"]:
            OUT.say("inbox: still holding %d message(s): %s"
                    % (len(res["pending"]), res["detail"]))

    def sweep_outbox(self, every=120):
        """Send anything the Producer left in the outbox, at most every two
        minutes.

        THE SAME PASS RHYTHM AS THE INBOUND WATCHER, and wrapped for the same
        reason `file_message` is: a broken outbox must not take the channel
        down. A quiet outbox costs one directory walk per pass, and every file
        that is already sent is skipped on its receipt without running the
        check again.
        """
        if time.time() - self.last_outbox < every:
            return
        self.last_outbox = time.time()
        try:
            res = outbox_pass(self.creds, self.repo, OUT.say)
        except Exception as e:                                # noqa: BLE001
            OUT.say("outbox: the sweep could not run (%s). The channel keeps "
                    "running." % type(e).__name__)
            return
        self.out_passes += 1
        self.out_sent += len(res["sent"])
        self.out_refused += len(res["refused"])

    def handle_text(self, text, sent_epoch=None, update_id=None):
        cmd = text.strip().lower().split("@")[0]
        if cmd in ("/start", "/help"):
            self.pending = None
            return self.reply(HELP)
        if cmd == "/ping":
            up = int((time.time() - self.started) / 60)
            return self.reply("Alive. Up %d minute(s), %d message(s) from you "
                              "handled, %d network wobble(s) recovered from."
                              % (up, self.mine, self.net_errors))
        if cmd == "/budget":
            return self.ask_budget()
        if self.pending:
            self.answers += 1
            v, why = parse_reading(text)
            if v is None:
                # REFUSED, NOT ROUNDED AND NOT COERCED (queue 104). The
                # counter does not move, so a refusal that quietly recorded
                # anyway would show up as readings climbing without a
                # read-back.
                #
                # HIS WORDS BACK ANYWAY, AND FILED. On the first run the
                # budget question is already open, so a plain hello would
                # otherwise be met with a demand and no proof that the channel
                # carried what he actually said. A message that is not a
                # reading is a message for the studio, and an open question is
                # not a reason to drop it. Filing first, refusing second.
                self.refused += 1
                OUT.say("budget: REFUSED an answer for the %s meter (%s). "
                        "refused=%d/%d answer(s) seen, readings=%d unchanged"
                        % (self.pending.upper(), why, self.refused,
                           self.answers, self.readings))
                return self.reply(echo_reply(
                    text, "%s\n%s"
                          % (self.file_message(text, sent_epoch, update_id),
                             refusal_text(why, self.pending))))
            if self.pending == "total":
                self.total = v
                self.pending = "fable"
                OUT.say("budget: total meter read as typed (%d)" % v)
                return self.reply(BUDGET_Q2, REMOVE_KEYBOARD)
            self.pending = None
            self.readings += 1
            text_out, line = budget_reading(self.total, v)
            wrote = log_budget(line)
            OUT.say("budget reading %d: %s (log written: %s)"
                    % (self.readings, line, "yes" if wrote else
                       "NO, production/logs is not writable"))
            return self.reply(text_out if wrote else
                              text_out + "\n(The PC could not write its own "
                                          "log file, so this reading only "
                                          "exists in this chat.)")
        return self.reply(echo_reply(
            text, "%s\nCommands: /budget, /ping, /help."
                  % self.file_message(text, sent_epoch, update_id)))

    def handle_callback(self, cq, update_id):
        """A TAPPED OPTION BECOMES A RULING (queue 090).

        THIS BRANCH IS THE WHOLE REASON A TAP CAN BE A RULING. Until it
        existed, an inline keyboard tap arrived as a `callback_query`, which
        is neither `message` nor `edited_message`, so it was counted as
        `other` and dropped: the card could be sent and the button could be
        pressed and nothing whatever happened.

        ANSWERED FIRST, ALWAYS. His phone shows a spinner on the button until
        the bot answers the callback, so every path out of here answers it,
        including the refusals. An unanswered tap reads as a dead card even
        when the ruling was filed.

        THE CHAT IS CHECKED AND NO ID IS PRINTED, same rule as `handle`.
        """
        self.taps += 1
        cid_q = cq.get("id")
        chat = str(((cq.get("message") or {}).get("chat") or {}).get("id"))
        if chat != self.chat:
            self.taps_refused += 1
            self.other += 1
            OUT.say("ignored a tap from a chat that is not the configured one "
                    "(%d refused of %d tap(s), %d ignored of %d update(s) "
                    "seen)" % (self.taps_refused, self.taps, self.other,
                               self.seen))
            self.answer_tap(cid_q, "This chat is not the one this bot is "
                                   "configured for, so nothing was recorded.")
            return
        self.mine += 1
        card_id, letter, why = cards.parse_callback(cq.get("data"))
        heading = None
        if card_id is None:
            self.taps_refused += 1
            note = ("I could not read that tap: %s. Nothing was recorded."
                    % why)
            OUT.say("tap REFUSED: %s (%d refused of %d tap(s))"
                    % (why, self.taps_refused, self.taps))
        else:
            heading = self.card_heading(card_id)
            try:
                res = inbox.ruling_and_push(self.repo, card_id, letter,
                                            self.tap_epoch(cq), update_id,
                                            OUT.say)
            except Exception as e:                            # noqa: BLE001
                self.taps_refused += 1
                self.push_fails += 1
                note = ("I could not file that ruling on the PC (%s). It is "
                        "NOT recorded, so please tap it again once the window "
                        "on the PC stops showing that error."
                        % type(e).__name__)
                OUT.say("tap FAILED to file (%s). The channel keeps running."
                        % type(e).__name__)
            else:
                self.taps_filed += 1
                if res["ok"]:
                    self.pushed += len(res["pushed"])
                else:
                    self.push_fails += 1
                self.last_flush = time.time()
                note = inbox.ruling_reply_text(res, heading)
                OUT.say("tap filed as a ruling (%d filed of %d tap(s))"
                        % (self.taps_filed, self.taps))
        self.answer_tap(cid_q, note.split("\n")[0])
        self.reply(note)

    def tap_epoch(self, cq):
        """TELEGRAM'S OWN CLOCK for the tap, from the message the button sits
        on, with this PC's clock as the named fallback. A ruling stamped from
        the wrong end is a ruling with a made-up instant on it."""
        date = ((cq.get("message") or {}).get("date"))
        if isinstance(date, int):
            return date
        OUT.say("telegramDateMissing=1: stamping this tap with the PC's own "
                "clock, so its instant is not a phone-side measurement")
        return int(time.time())

    def card_heading(self, card_id):
        """The card's own heading, read from the queue in this checkout, or
        None. Only ever used to say back which card he ruled: the fold in the
        container resolves the id itself and does not trust this."""
        try:
            with open(os.path.join(self.repo,
                                   *cards.QUEUE_REL.split("/")), "r",
                      encoding="utf-8") as fh:
                card = cards.find_card(cards.parse_queue(fh.read()), card_id)
            return card["heading"] if card else None
        except OSError:
            return None

    def handle(self, update):
        self.seen += 1
        self.offset = update["update_id"] + 1
        cq = update.get("callback_query")
        if cq:
            return self.handle_callback(cq, update["update_id"])
        msg = update.get("message") or update.get("edited_message")
        if not msg:
            self.other += 1
            return
        if str((msg.get("chat") or {}).get("id")) != self.chat:
            # NO IDS PRINTED. The configured one is a credential, and the
            # comparison being wrong is exactly when it would get printed.
            self.other += 1
            OUT.say("ignored a message from a chat that is not the configured "
                    "one (%d ignored of %d seen)" % (self.other, self.seen))
            return
        self.mine += 1
        text = msg.get("text")
        if not text:
            self.nontext += 1
            OUT.say("a non-text message arrived (%d of %d from you)"
                    % (self.nontext, self.mine))
            return self.reply("I can only read typed text today. Photos "
                              "and voice memos are still Monday's work. "
                              "Decision cards do work: tap a button on one "
                              "and I file the ruling.")
        OUT.say("message %d from you: %s" % (self.mine, text[:80] + (
            " (+%d more character(s) not shown)" % (len(text) - 80)
            if len(text) > 80 else "")))
        # TELEGRAM'S OWN CLOCK, WHICH IS ONE OF THE TWO ENDS OF
        # `inboundLatencySec`. If the field were ever missing, the PC's clock
        # stands in and the window says so, because a latency measured from
        # the wrong end reads as a fast channel.
        date = msg.get("date")
        if not isinstance(date, int):
            OUT.say("telegramDateMissing=1: using this PC's clock as the "
                    "sent time, so the latency for this one is not a "
                    "phone-to-repo measurement")
            date = int(time.time())
        self.handle_text(text, date, update["update_id"])

    # -- run --------------------------------------------------------------
    def poll_forever(self):
        backoff, since_ok = 5, 0
        while True:
            try:
                params = {"timeout": 25}
                if self.offset is not None:
                    params["offset"] = self.offset
                updates = call(self.token, "getUpdates", params, timeout=45)
                if since_ok:
                    OUT.say("back in touch with Telegram after %d error(s)"
                            % since_ok)
                    since_ok, backoff = 0, 5
                for u in updates or []:
                    self.handle(u)
                # AFTER THE MESSAGES, NOT INSTEAD OF THEM. This is a no-op
                # unless something is held on disk, and it is rate-limited to
                # once a minute, so a quiet bot costs one `rev-parse` and one
                # directory listing per poll.
                self.flush_inbox()
                # AND THE OUTBOUND HALF, in the same rhythm. After the
                # messages, never instead of them: a message from him is the
                # thing that must not wait.
                self.sweep_outbox()
            except ApiError as e:
                if e.kind != "network":
                    OUT.say("STOPPING: %s" % e)
                    return 1
                self.net_errors += 1
                since_ok += 1
                OUT.say("network error %d (%d in a row): %s. Retrying in %d "
                        "second(s); the bot keeps running."
                        % (self.net_errors, since_ok, e, backoff))
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
            except KeyboardInterrupt:
                OUT.say("stopped from the keyboard")
                return 0

    def done_line(self):
        """The whole run's tally. Every count against the set it came from.

        `inboxPending` is read from disk at this instant rather than
        remembered, so it is the number of messages still on this PC when the
        window closed, which is the number that matters to whoever reads it.
        """
        try:
            waiting = len(inbox.pending_files(self.repo)[0])
        except Exception:                                     # noqa: BLE001
            waiting = -1
        return ("telegram-bot done: uptimeMin=%d updatesSeen=%d fromYou=%d/%d "
                "ignoredOtherChats=%d/%d nonText=%d/%d budgetReadings=%d "
                "budgetAnswersSeen=%d budgetRefused=%d/%d readingSource=typed "
                "taps=%d/%d tapsFiled=%d/%d tapsRefused=%d/%d "
                "backlogFiled=%d/%d networkErrors=%d inboxFiled=%d "
                "inboxPushed=%d/%d inboxPushFailures=%d inboxPending=%s "
                "outboxPasses=%d outboxSent=%d outboxRefused=%d"
                % (int((time.time() - self.started) / 60), self.seen,
                   self.mine, self.seen, self.other, self.seen,
                   self.nontext, self.mine, self.readings, self.answers,
                   self.refused, self.answers, self.taps, self.seen,
                   self.taps_filed, self.taps, self.taps_refused, self.taps,
                   self.backlog_filed, self.backlog_seen, self.net_errors,
                   self.filed, self.pushed, self.filed, self.push_fails,
                   "unreadable" if waiting < 0 else waiting, self.out_passes,
                   self.out_sent, self.out_refused))


# --------------------------------------------------------------------------
def banner(creds, path):
    OUT.say("LEDGER Telegram bot")
    OUT.say("repo    : %s" % REPO)
    OUT.say("config  : %s" % path)
    OUT.say("startup : configRead=ok tokenSource=%s chatSource=%s "
            "chatShape=%s lines=%d"
            % (creds.token_source, creds.chat_source, creds.chat_shape,
               creds.lines_read))
    if creds.chat_shape != "ok":
        OUT.say("NOTE: the chat id does not look like a number. If Telegram "
                "says chat not found below, that is why.")


def load_or_explain(path=None):
    try:
        creds = botconfig.load(path)
    except botconfig.ConfigError as e:
        OUT.say("CANNOT START: %s" % e)
        OUT.say("The file is tools\\runner\\config.local on this PC. It wants "
                "two lines:")
        OUT.say("    TELEGRAM_TOKEN=<the token BotFather gave you>")
        OUT.say("    CHAT_ID=<your numeric chat id>")
        OUT.say("Nothing here has printed or will print what is in it.")
        return None
    OUT.guard(creds.secrets())
    return creds


def run():
    path = botconfig.DEFAULT_PATH
    creds = load_or_explain(path)
    if creds is None:
        return 1
    banner(creds, path)
    # THE INBOX'S STATE BEFORE ANY MESSAGE ARRIVES, so the window says what
    # this PC is holding rather than only what happens next. The zero ships
    # its denominator: `of N on disk`.
    try:
        held, _tip = inbox.pending_files(REPO)
        newest, basis = inbox.newest_work_commit(REPO)
        state, age = inbox.studio_state(newest, time.time())
        OUT.say("inbox   : branch=%s inboxPending=%d/%d %s"
                % (inbox.INBOX_BRANCH, len(held),
                   len(inbox.message_files(REPO)),
                   inbox.studio_key(state, age, basis)))
    except Exception as e:                                    # noqa: BLE001
        OUT.say("inbox   : could not be read (%s). Messages will still be "
                "answered; filing may fail and will say so." % type(e).__name__)
    bot = Bot(creds)
    try:
        name = bot.hello()
        bot.skip_backlog()
        bot.reply(OPENING)
        OUT.say("pushed the opening message, unprompted")
        bot.ask_budget()
    except ApiError as e:
        OUT.say("CANNOT START: %s" % e)
        return 1
    bot.flush_inbox(every=0)
    OUT.say("bot %s is listening. Send it something from your phone. Close "
            "this window to stop it." % name)
    code = bot.poll_forever()
    OUT.say(bot.done_line())
    return code


def outbox_pass(creds, repo=None, say=None):
    """One sweep of production/outbox/, then push the records back.

    THE CHECK IS INSIDE `outbox.sweep`, on this machine, and this function
    supplies only the wire. `SendFailed` rather than `ApiError` crosses the
    boundary so the sweep can tell a dead uplink (retry next pass) from a
    register refusal (do not send, and say why in the tree).
    """
    repo = repo or REPO
    say = say or OUT.say

    def sender(text):
        try:
            return send(creds.token, str(creds.chat_id), text)
        except ApiError as e:
            raise outbox.SendFailed(str(e))

    res = outbox.sweep(repo, sender, say=say)
    say(outbox.done_line(res))
    note = outbox.nothing_line(res)
    if note:
        say(note.strip())
    if res["records"]:
        push = inbox.push_pending(repo, say)
        if not push["ok"]:
            say("outbox: %d record(s) are written on this PC but NOT pushed "
                "(%s). Nothing is dropped; the next pass retries them."
                % (len(res["records"]), push["detail"]))
    return res


def cards_pass(creds, repo=None, say=None):
    """Send every pushable WAITING card, with one button per option.

    THE CHOOSING, THE COUNTING AND THE STRINGS ARE IN `cards.send_cards`,
    where the tests run; this supplies the wire and the file. A card whose
    options do not fit the queue's own two-to-four rule is named here with
    the reason rather than sent with a keyboard he cannot use.
    """
    repo = repo or REPO
    say = say or OUT.say
    try:
        with open(os.path.join(repo, *cards.QUEUE_REL.split("/")), "r",
                  encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        say("NOT SENT: %s could not be read (%s), so 0 card(s) were sent and "
            "nothing is known about what is waiting."
            % (cards.QUEUE_REL, type(e).__name__))
        return {"waiting": 0, "sent": [], "skipped": [], "failed": []}

    def sender(body, keyboard):
        try:
            return send(creds.token, str(creds.chat_id), body, keyboard)
        except ApiError as e:
            raise outbox.SendFailed(str(e))

    return cards.send_cards(text, sender, say=say)


def frames_pass(creds, repo=None, say=None, extra=None):
    """One picture, or the words that say why there is none."""
    repo = repo or REPO
    say = say or OUT.say

    def photo_sender(path, caption):
        try:
            return send_photo(creds.token, str(creds.chat_id), path, caption)
        except ApiError as e:
            raise outbox.SendFailed(str(e))
        except OSError as e:
            raise outbox.SendFailed("could not read the file (%s)"
                                    % type(e).__name__)

    def text_sender(text):
        try:
            return send(creds.token, str(creds.chat_id), text)
        except ApiError as e:
            raise outbox.SendFailed(str(e))

    res = outbox.send_frames(repo, photo_sender, text_sender, say=say,
                             extra=extra)
    say(outbox.frames_done_line(res))
    note = outbox.frames_nothing_line(res)
    if note:
        say(note.strip())
    if res["records"]:
        push = inbox.push_pending(repo, say)
        if not push["ok"]:
            say("frames: %d receipt(s) written on this PC but NOT pushed (%s)"
                % (len(res["records"]), push["detail"]))
    return res


def send_file_checked(repo, path, sender, say=None):
    """(rc, why) for one Producer message file. THE CHECK IS HERE.

    RULED 2026-09-05, AND THE DIRECTION MATTERS. The check is wired on the
    PRODUCER CONTENT CLASS, which is this door, and NOT inside `send()`: the
    bot's own chrome (the opening line, the budget question, the read-backs)
    goes through `send()` and fails the register by construction, so a check
    inside `send()` would make the bot unusable. `--send-file` is the Producer
    class, so it is checked, and the refusal is loud rather than silent.
    """
    say = say or OUT.say
    kind, why = outbox.kind_of_name(path)
    if kind is None:
        say("NOT SENT: %s" % why)
        return 2, why
    try:
        with open(outbox.full_path(repo, path), "r", encoding="utf-8") as fh:
            body = fh.read().strip()
    except (OSError, UnicodeDecodeError) as e:
        why = "could not read %s as text (%s)" % (path, type(e).__name__)
        say("NOT SENT: %s" % why)
        return 1, why
    if not body:
        why = "%s is empty, so there is nothing to send" % path
        say("NOT SENT: %s" % why)
        return 1, why
    ok, clause, _out = outbox.run_check(repo, kind, path)
    if not ok:
        say("NOT SENT: the %s register refused this message: %s"
            % (kind, clause))
        say("Fix the message, or send it with --send if it is not a Producer "
            "message. Nothing was sent.")
        return 1, clause
    say("the %s register passed it (%d character(s)); sending"
        % (kind, len(body)))
    try:
        result = sender(body)
    except outbox.SendFailed as e:
        say("NOT SENT: %s" % e)
        return 1, str(e)
    mid = (result or {}).get("message_id")
    if not mid:
        say("SENT BUT NOT RECEIPTED: the platform returned no message id, so "
            "whether it arrived is unknown. Nothing is written as proof.")
        return 1, "no message id"
    say("sent 1 message (%d character(s)) messageId=%d" % (len(body), mid))
    return 0, ""


def run_send(text):
    creds = load_or_explain()
    if creds is None:
        return 1
    try:
        send(creds.token, str(creds.chat_id), text)
    except ApiError as e:
        OUT.say("NOT SENT: %s" % e)
        return 1
    OUT.say("sent 1 message (%d character(s))" % len(text))
    return 0


# --------------------------------------------------------------------------
# SELFTEST. Offline by construction: not one case here touches the network,
# because the network is blocked from the container this was written in.
# Accepting case first.
# --------------------------------------------------------------------------
def selftest():
    ok, bad = [], []

    def check(name, cond, detail=""):
        (ok if cond else bad).append(name)
        print("  %-36s %s%s" % (name, "pass" if cond else "FAIL",
                                (" : " + detail) if not cond else ""))

    t, line = budget_reading(40, 62)
    check("accept/fable-governs", "fable at 62" in t and
          "headroomPct=18" in line and "governing=fable" in line, line)
    print("      says: %s" % line)
    t, line = budget_reading(77, 76)
    check("accept/total-governs", "total at 77" in t and
          "governing=total" in line and "headroomPct=3" in line, line)
    t, line = budget_reading(80, 12)
    check("accept/exactly-on-ceiling", "exactly on the 80 percent" in t and
          "headroomPct=0" in line, line)
    t, line = budget_reading(91.5, 12)
    check("accept/over-ceiling-goes-negative",
          "11.5 point(s) OVER" in t and "headroomPct=-11.5" in line, line)
    print("      says: %s" % line)
    check("accept/no-spaces-in-values",
          all(" " not in kv.split("=")[1] for kv in line.split()), line)

    # THE READING IS AN INTEGER OR IT IS REFUSED, ruled 2026-09-05.
    check("accept/reading-77", parse_reading("77") == (77, ""))
    check("accept/reading-with-sign", parse_reading(" 77% ") == (77, ""))
    check("accept/reading-worded", parse_reading("77 percent") == (77, ""))
    check("accept/reading-at-both-bounds",
          parse_reading("0")[0] == 0 and parse_reading("100")[0] == 100)
    check("accept/reading-is-an-int-not-a-float",
          isinstance(parse_reading("77")[0], int)
          and not isinstance(parse_reading("77")[0], float))
    # THE SEVEN REFUSALS QUEUE 104 NAMES, each with a reason he can act on.
    # `wrong` rather than `bad`, which is this selftest's failure list: the
    # loop variable shadowed it and the tally became a string.
    for wrong, expect in (("76,5", "whole number"), ("76.5", "whole number"),
                          ("77.0", "whole number"),
                          ("about half", "whole number"),
                          ("101", "outside 0 to 100"),
                          ("-3", "outside 0 to 100"), ("", "sent nothing")):
        v, why = parse_reading(wrong)
        check("reject/reading-%s" % (wrong or "empty"),
              v is None and expect in why,
              "%r gave %r (%s)" % (wrong, v, why))
    check("accept/the-refusal-says-what-is-wanted",
          NUMERIC_PLACEHOLDER in refusal_text("that is not a whole number",
                                              "total")
          and "TOTAL" in refusal_text("x", "total")
          and "Nothing was recorded" in refusal_text("x", "total"),
          refusal_text("that is not a whole number", "total"))
    check("accept/the-log-line-names-the-reading-as-typed",
          "source=typed" in budget_reading(77, 76)[1], budget_reading(77, 76)[1])

    long_text = "x" * (REPLY_CAP + 25)
    r = echo_reply(long_text)
    check("accept/cap-announces-itself",
          "(+25 more character(s) not shown)" in r, r[-60:])
    check("accept/short-text-not-capped", "not shown" not in echo_reply("hi"))

    # INVERTED 2026-09-05 (queue 104). This asserted a 15-button grid
    # spanning 0 to 100. It now asserts that a meter question carries NO
    # keyboard and REMOVES the one his phone may still be holding, so the
    # grid coming back is what turns this red.
    for name, q in (("meter-1", BUDGET_Q), ("meter-2", BUDGET_Q2)):
        params = send_params("1234", q, REMOVE_KEYBOARD)
        markup = json.loads(params["reply_markup"])
        check("accept/%s-carries-no-preset-keyboard" % name,
              "keyboard" not in markup and "inline_keyboard" not in markup
              and markup.get("remove_keyboard") is True, markup)
        check("accept/%s-asks-for-a-whole-number-in-words" % name,
              NUMERIC_PLACEHOLDER.lower() in q.lower(), q)
    check("reject/a-message-with-no-markup-sends-no-reply-markup",
          "reply_markup" not in send_params("1234", "hello"),
          sorted(send_params("1234", "hello")))
    with open(os.path.abspath(__file__), "r", encoding="utf-8") as fh:
        own_source = fh.read()
    # THE SENTINEL IS BUILT AT RUNTIME so that this assertion does not match
    # itself: written out in full, the check would find its own source and
    # report the grid as present for ever.
    grid = "BUDGET_" + "KEYS = ["
    check("reject/the-preset-grid-is-gone-from-this-file",
          grid not in own_source, "the preset grid is back in this file")

    scrubbed = botconfig.redact("boom in bot123:SECRETVALUE", ["123:SECRETVALUE"])
    check("accept/console-scrubs", "SECRETVALUE" not in scrubbed, scrubbed)

    # ---- THE INBOX WIRING, against a throwaway repository ---------------
    #
    # The transport itself is covered by `inbox.py --selftest`, which builds
    # the repositories and proves the watcher's checkout is untouched. What
    # is proven HERE is the wiring: which messages get filed, which do not,
    # and what the reply carries. `reply` is captured rather than sent, so
    # no case below touches the network.
    home, far, watcher, _reader = inbox._repos()
    creds = botconfig.Credentials(botconfig.FAKE_TOKEN, botconfig.FAKE_CHAT,
                                  "selftest", "selftest", 2)
    sent = 1788633012                                # 2026-09-05T18:30:12Z

    class Captured(Bot):
        def __init__(self):
            Bot.__init__(self, creds, repo=watcher)
            self.said = []
            self.markup = []
            self.answered = []          # (callback id, toast text)

        def answer_tap(self, cid, text):   # the wire, captured
            self.answered.append((cid, text))

        def reply(self, text, markup=None):
            self.said.append(text)
            self.markup.append(markup)

    def update(text, uid, chat=None):
        return {"update_id": uid,
                "message": {"date": sent, "text": text,
                            "chat": {"id": chat or botconfig.FAKE_CHAT}}}

    b = Captured()
    b.pending = None
    b.handle(update("Seen the van again.", 4127))
    rel = "production/inbox/" + inbox.message_name(sent, 4127)
    check("accept/inbox-a-typed-message-is-filed",
          os.path.exists(os.path.join(watcher, *rel.split("/"))), rel)
    check("accept/inbox-the-reply-carries-his-words-and-the-file",
          b.said and "Seen the van again." in b.said[-1]
          and rel in b.said[-1], b.said[-1][:90] if b.said else "SILENT")
    check("accept/inbox-the-reply-says-awake-or-asleep",
          any(w in b.said[-1] for w in ("AWAKE", "ASLEEP", "cannot tell")),
          b.said[-1][-90:] if b.said else "SILENT")
    check("accept/inbox-counted-as-filed-and-pushed",
          b.filed == 1 and b.pushed == 1 and b.push_fails == 0,
          "filed %d pushed %d" % (b.filed, b.pushed))
    check("accept/inbox-the-done-line-carries-the-counters",
          "inboxFiled=1" in b.done_line() and "inboxPushed=1/1" in b.done_line()
          and "inboxPending=0" in b.done_line(), b.done_line())

    # A MESSAGE THAT IS NOT A NUMBER WHILE THE BUDGET QUESTION IS OPEN IS
    # STILL A MESSAGE. It was the first thing the open question would have
    # swallowed on the first evening.
    b.pending = "total"
    b.handle(update("what is the studio doing", 4128))
    check("accept/inbox-filed-even-with-the-budget-question-open",
          os.path.exists(os.path.join(watcher, *(
              "production/inbox/" + inbox.message_name(sent, 4128)).split("/")))
          and "TOTAL meter" in b.said[-1], b.said[-1][:80])

    # THE REJECTING CASES. A foreign chat writes NO file and raises the
    # ignored counter, which is the existing behaviour this must not break.
    before = len(inbox.message_files(watcher))
    b2 = Captured()
    b2.handle(update("from somebody else", 4129, chat="-100999"))
    check("reject/inbox-another-chat-writes-no-file",
          len(inbox.message_files(watcher)) == before and b2.other == 1
          and b2.mine == 0 and not b2.said,
          "%d file(s), other=%d" % (len(inbox.message_files(watcher)),
                                    b2.other))
    check("reject/inbox-and-that-run-filed-nothing",
          b2.filed == 0 and "inboxFiled=0" in b2.done_line(), b2.done_line())

    # A COMMAND IS NOT A MESSAGE FOR THE STUDIO.
    b3 = Captured()
    b3.handle(update("/ping", 4130))
    b3.handle(update("/help", 4131))
    check("reject/inbox-a-command-is-not-filed",
          b3.filed == 0 and len(inbox.message_files(watcher)) == before,
          "%d file(s)" % len(inbox.message_files(watcher)))

    # AND A NUMBER ANSWERING THE BUDGET QUESTION IS NOT FILED EITHER.
    b4 = Captured()
    b4.pending, b4.total = "fable", 40
    b4.handle(update("62", 4132))
    check("reject/inbox-a-budget-answer-is-not-filed",
          b4.filed == 0 and "fable at 62" in b4.said[-1],
          b4.said[-1][:60] if b4.said else "SILENT")
    check("accept/a-typed-reading-is-recorded-once-and-read-back",
          b4.readings == 1 and b4.refused == 0 and b4.answers == 1
          and "budgetReadings=1" in b4.done_line()
          and "budgetRefused=0/1" in b4.done_line(), b4.done_line())
    # AND THE REFUSED HALF, with the counter as the thing that catches a
    # refusal that quietly records anyway.
    b4b = Captured()
    b4b.pending, b4b.total = "fable", 40
    for wrong in ("76,5", "76.5", "77.0", "about half", "101", "-3"):
        b4b.handle(update(wrong, 4200 + len(b4b.said)))
    check("reject/every-non-integer-is-refused-and-records-nothing",
          b4b.readings == 0 and b4b.refused == 6 and b4b.answers == 6
          and b4b.pending == "fable"
          and "budgetRefused=6/6" in b4b.done_line(), b4b.done_line())
    check("reject/and-the-refusal-tells-him-what-is-wanted",
          NUMERIC_PLACEHOLDER in b4b.said[-1]
          and "Nothing was recorded" in b4b.said[-1], b4b.said[-1][-120:])
    check("accept/a-refused-reading-is-still-filed-for-the-studio",
          b4b.filed == 6 and "inboxFiled=6" in b4b.done_line(),
          b4b.done_line())
    b4b.handle(update("77", 4299))
    check("accept/and-the-next-good-one-is-taken-as-typed",
          b4b.readings == 1 and "fable at 77" in b4b.said[-1]
          and "budgetRefused=6/7" in b4b.done_line(), b4b.done_line())

    # AND A HELD MESSAGE IS REPORTED, NOT DROPPED.
    inbox._fixture_git(["remote", "set-url", "--push", "origin",
                        os.path.join(home, "no-such-remote.git")], watcher)
    b5 = Captured()
    b5.handle(update("while the uplink is down", 4133))
    check("reject/inbox-a-failed-push-holds-the-message-and-says-so",
          b5.filed == 1 and b5.pushed == 0 and b5.push_fails == 1
          and "NOT pushed" in b5.said[-1] and "none are dropped" in b5.said[-1],
          b5.said[-1][:100] if b5.said else "SILENT")
    check("reject/inbox-and-the-done-line-counts-what-is-waiting",
          "inboxPushed=0/1" in b5.done_line()
          and "inboxPending=1" in b5.done_line(), b5.done_line())
    inbox._fixture_git(["remote", "set-url", "--push", "origin", far], watcher)
    b5.flush_inbox(every=0)
    check("accept/inbox-the-retry-clears-the-backlog-and-says-so",
          inbox.pending_files(watcher)[0] == []
          and "holding on the PC are on the branch now" in b5.said[-1],
          b5.said[-1][:90])

    # ---- THE TAP, queue 090. A callback_query is not a message, and
    # before this branch existed it was counted as `other` and dropped.
    queue_rel = os.path.join(watcher, *cards.QUEUE_REL.split("/"))
    os.makedirs(os.path.dirname(queue_rel), exist_ok=True)
    with open(queue_rel, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(cards.FIXTURE)
    live_card = cards.find_card(cards.parse_queue(cards.FIXTURE),
                               cards.card_id("How close should strangers "
                                             "stand?"))

    def tap(data, uid, chat=None, cid="cbq%d" % 1):
        return {"update_id": uid,
                "callback_query": {"id": cid, "data": data,
                                   "message": {"date": sent,
                                               "chat": {"id": chat or
                                                        botconfig.FAKE_CHAT}}}}

    b7 = Captured()
    b7.handle(tap(cards.callback_data(live_card["id"], "B"), 5001))
    rel7 = "production/rulings/" + inbox.ruling_name(sent, 5001)
    check("accept/a-tap-is-seen-as-a-tap-and-not-as-other",
          b7.taps == 1 and b7.taps_filed == 1 and b7.other == 0
          and b7.mine == 1, "taps=%d other=%d" % (b7.taps, b7.other))
    check("accept/the-tap-writes-a-ruling-record-naming-card-and-option",
          os.path.exists(os.path.join(watcher, *rel7.split("/"))), rel7)
    got, why = inbox.parse_ruling_record(
        open(os.path.join(watcher, *rel7.split("/")), encoding="utf-8").read())
    check("accept/the-record-carries-the-card-the-letter-and-the-instant",
          got and got["cardId"] == live_card["id"] and got["option"] == "B"
          and got["tappedEpoch"] == sent, why or got)
    check("accept/the-tap-is-answered-so-his-phone-stops-spinning",
          len(b7.answered) == 1 and b7.answered[0][0] == "cbq1"
          and "Ruled B" in b7.answered[0][1], b7.answered)
    check("accept/and-he-is-told-which-card-he-just-ruled",
          "How close should strangers stand?" in b7.said[-1]
          and rel7 in b7.said[-1], b7.said[-1][:120])
    check("accept/the-done-line-counts-taps-against-what-it-saw",
          "taps=1/1" in b7.done_line() and "tapsFiled=1/1" in b7.done_line()
          and "tapsRefused=0/1" in b7.done_line(), b7.done_line())

    before7 = len(cards.record_files(watcher))
    b8 = Captured()
    b8.handle(tap(cards.callback_data(live_card["id"], "B"), 5002,
                  chat="-100999"))
    check("reject/a-tap-from-another-chat-writes-no-record",
          b8.taps == 1 and b8.taps_filed == 0 and b8.taps_refused == 1
          and b8.other == 1 and not b8.said
          and len(cards.record_files(watcher)) == before7,
          "%d record(s), refused=%d" % (len(cards.record_files(watcher)),
                                        b8.taps_refused))
    check("reject/but-it-is-still-answered-and-says-nothing-was-recorded",
          len(b8.answered) == 1 and "nothing was recorded"
          in b8.answered[0][1], b8.answered)
    b9 = Captured()
    b9.handle(tap("62", 5003))
    check("reject/a-callback-that-is-not-a-ruling-tap-writes-no-record",
          b9.taps == 1 and b9.taps_filed == 0 and b9.taps_refused == 1
          and len(cards.record_files(watcher)) == before7
          and "could not read that tap" in b9.said[-1], b9.said[-1][:80])
    check("reject/and-a-tap-is-never-taken-as-a-budget-answer",
          b9.readings == 0 and b9.answers == 0
          and "budgetReadings=0" in b9.done_line(), b9.done_line())

    # ---- THE BACKLOG, queue 090's fold. Both outcomes -------------------
    class Backlogged(Captured):
        def __init__(self, updates):
            Captured.__init__(self)
            self.backlog = updates

        def api(self, updates):
            self.backlog = updates

    def with_backlog(updates):
        b = Backlogged(updates)
        globals()["call"] = lambda tok, method, params, timeout=40: (
            updates if method == "getUpdates" else {})
        try:
            b.skip_backlog()
        finally:
            globals()["call"] = _real_call
        return b

    _real_call = call
    before_b = len(inbox.message_files(watcher))
    b10 = with_backlog([update("sent while you were closed", 6001),
                        update("and this one too", 6002)])
    check("accept/the-backlog-is-filed-rather-than-dropped",
          b10.backlog_filed == 2 and b10.filed == 2
          and len(inbox.message_files(watcher)) == before_b + 2,
          "filed %d of %d seen" % (b10.backlog_filed, b10.backlog_seen))
    check("accept/each-backlog-message-keeps-its-own-telegram-date",
          os.path.exists(os.path.join(watcher, "production", "inbox",
                                      inbox.message_name(sent, 6001))),
          inbox.message_name(sent, 6001))
    check("accept/he-is-told-once-with-the-count",
          len(b10.said) == 1 and "2 message(s) arrived" in b10.said[0]
          and "not answering them one by one" in b10.said[0], b10.said)
    check("accept/and-the-done-line-carries-the-backlog-denominator",
          "backlogFiled=2/2" in b10.done_line(), b10.done_line())

    before_c = len(inbox.message_files(watcher))
    b11 = with_backlog([update("from somebody else", 6003, chat="-100999"),
                        update("/ping", 6004),
                        update("62", 6005),
                        tap(cards.callback_data(live_card["id"], "A"), 6006)])
    check("reject/a-foreign-chat-a-command-and-a-tap-are-not-filed",
          b11.backlog_filed == 1 and b11.backlog_seen == 4
          and len(inbox.message_files(watcher)) == before_c + 1,
          "filed %d of %d" % (b11.backlog_filed, b11.backlog_seen))
    check("reject/and-no-backlog-number-is-applied-as-a-budget-answer",
          b11.readings == 0 and b11.answers == 0 and b11.total is None
          and b11.pending is None
          and "appliedAsBudget=0/1" in "appliedAsBudget=0/1", b11.done_line())
    b12 = with_backlog([])
    check("accept/an-empty-backlog-files-nothing-and-says-so",
          b12.backlog_filed == 0 and not b12.said
          and "backlogFiled=0/0" in b12.done_line(), b12.done_line())

    # ---- THE OUTBOUND WIRING, queue 089 and 091 ------------------------
    #
    # The sweep, the register check, the receipts and the picture are covered
    # by `outbox.py --selftest` against a scripted stand-in. What is proven
    # HERE is the bot's side: the multipart body it builds by hand, which door
    # the check is wired to, and that the loop counts what it sent.
    import inspect                                            # noqa: PLC0415
    ctype, body = multipart({"chat_id": "1234", "caption": "one line"},
                            {"photo": ("f.jpg", b"\xff\xd8\xffJPEGBYTES",
                                       "image/jpeg")},
                            boundary="BOUND")
    check("accept/multipart-names-its-own-boundary",
          ctype == "multipart/form-data; boundary=BOUND", ctype)
    check("accept/multipart-carries-the-caption-and-the-file-bytes",
          b'name="caption"' in body and b"one line" in body
          and b'filename="f.jpg"' in body and b"JPEGBYTES" in body
          and body.endswith(b"--BOUND--\r\n"), len(body))
    check("accept/multipart-sends-it-as-a-photo-field-not-a-document",
          b'name="photo"' in body and b'name="document"' not in body)

    # THE BOUNDARY THAT MAKES THE BOT USABLE, asserted on the code itself:
    # the check belongs on the Producer content class and NOT inside send(),
    # because the chrome below fails the register by construction.
    check("accept/the-check-is-on-the-producer-door",
          "run_check" in inspect.getsource(send_file_checked))
    check("reject/and-is-NOT-inside-send-or-reply",
          "run_check" not in inspect.getsource(send)
          and "run_check" not in inspect.getsource(Bot.reply)
          and "producer-check" not in inspect.getsource(send))

    pc_repo = outbox._fixture_repo(os.path.join(home, "sendfile"))
    good_rel = "%s/2026-09-05-good.unprompted.md" % outbox.OUTBOX_DIR
    outbox._commit(pc_repo, good_rel, outbox._load_producer_check().GOOD)
    posted = []
    rc, why = send_file_checked(pc_repo, good_rel,
                                lambda t: posted.append(t) or
                                {"message_id": 77}, say=lambda _s: None)
    check("accept/a-checked-producer-file-is-sent", rc == 0 and not why
          and len(posted) == 1, "rc=%d %s" % (rc, why))
    long_rel = "%s/2026-09-05-too-long.unprompted.md" % outbox.OUTBOX_DIR
    outbox._commit(pc_repo, long_rel,
                   outbox._load_producer_check().GOOD + ("\nword " * 200))
    rc, why = send_file_checked(pc_repo, long_rel,
                                lambda t: posted.append(t) or
                                {"message_id": 78}, say=lambda _s: None)
    check("reject/an-over-cap-file-is-refused-and-not-sent",
          rc == 1 and len(posted) == 1 and "word" in why, "rc=%d %s" % (rc, why))
    rc, why = send_file_checked(pc_repo, "production/outbox/no-kind.md",
                                lambda t: posted.append(t), say=lambda _s: None)
    check("reject/a-file-with-no-register-in-its-name-is-refused",
          rc == 2 and len(posted) == 1 and ".unprompted.md" in why
          and ".answer.md" in why and ".brief.md" in why, why)
    check("reject/and-the-bots-own-chrome-would-fail-that-check",
          not outbox.run_check(
              pc_repo, "unprompted",
              outbox._commit(pc_repo, "%s/2026-09-05-chrome.unprompted.md"
                             % outbox.OUTBOX_DIR, OPENING))[0],
          "the opening line passed the register, which it must not")

    b6 = Captured()
    b6.creds = creds
    b6.sweep_outbox(every=0)
    check("accept/the-loop-sweeps-the-outbox-and-counts-the-pass",
          b6.out_passes == 1 and b6.out_sent == 0
          and "outboxPasses=1" in b6.done_line()
          and "outboxSent=0" in b6.done_line(), b6.done_line())

    print("\ntelegram-bot selftest: %d passed, %d failed (%d case(s) run). "
          "THE NETWORK HALF IS NOT COVERED: every Telegram call in this file "
          "is unverifiable until it runs on the PC."
          % (len(ok), len(bad), len(ok) + len(bad)))
    print("now the config reader:\n")
    rc = botconfig._selftest()
    return 3 if (bad or rc) else 0


def main(argv):
    args = argv[1:]
    if "--selftest" in args:
        return selftest()
    if "--send" in args:
        i = args.index("--send")
        if i + 1 >= len(args):
            OUT.say("--send needs the message text after it")
            return 1
        return run_send(args[i + 1])
    if "--send-file" in args:
        i = args.index("--send-file")
        if i + 1 >= len(args):
            OUT.say("--send-file needs a path after it")
            return 1
        creds = load_or_explain()
        if creds is None:
            return 1

        def sender(text):
            try:
                return send(creds.token, str(creds.chat_id), text)
            except ApiError as e:
                raise outbox.SendFailed(str(e))

        return send_file_checked(REPO, args[i + 1], sender)[0]
    if "--send-outbox" in args:
        creds = load_or_explain()
        if creds is None:
            return 1
        res = outbox_pass(creds)
        return 1 if (res["refused"] or res["failed"] or res["bad_receipt"]) \
            else 0
    if "--send-cards" in args:
        creds = load_or_explain()
        if creds is None:
            return 1
        res = cards_pass(creds)
        return 1 if res["failed"] else 0
    if "--send-frame" in args:
        creds = load_or_explain()
        if creds is None:
            return 1
        i = args.index("--send-frame")
        extra = []
        if i + 1 < len(args) and not args[i + 1].startswith("--"):
            extra = ["--frame", args[i + 1]]
        res = frames_pass(creds, extra=extra)
        return 1 if (res["refused"] or res["failed"]) else 0
    return run()


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        OUT.say("stopped from the keyboard")
        sys.exit(0)
    except Exception as e:                                    # noqa: BLE001
        # THE LAST NET, ruled 2026-09-04. Without this arm an unexpected
        # exception prints the interpreter's own traceback to stderr, and
        # that printer is not Console.say. http.client.InvalidURL quotes
        # the whole request path, token included, when the token carries
        # a space or a tab; repr escapes a tab, so an exact-match scrub of
        # that message could miss it. The message is therefore withheld:
        # the type and the line are enough to diagnose from.
        tb = e.__traceback__
        while tb.tb_next is not None:
            tb = tb.tb_next
        OUT.say("CRASHED: %s at %s line %d. The message is withheld in "
                "case it carries the token. Send Claude this line as it "
                "is." % (type(e).__name__,
                         os.path.basename(tb.tb_frame.f_code.co_filename),
                         tb.tb_lineno))
        sys.exit(1)
