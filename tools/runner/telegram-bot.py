#!/usr/bin/env python3
"""The studio's Telegram channel, running on Jafar's PC. Standard library only.

    START THE TELEGRAM BOT.bat                 what Jafar double-clicks
    python3 tools/runner/telegram-bot.py       the same thing, from a shell
    python3 tools/runner/telegram-bot.py --send "text"    one unprompted push
    python3 tools/runner/telegram-bot.py --send-file PATH  one CHECKED message
    python3 tools/runner/telegram-bot.py --send-outbox     sweep the outbox
    python3 tools/runner/telegram-bot.py --send-frame      one verified picture
    python3 tools/runner/telegram-bot.py --send-brief      the ONE daily brief
    python3 tools/runner/telegram-bot.py --send-cards      RETIRED 2026-09-09
    python3 tools/runner/telegram-bot.py --flush-inbox     push the return half
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

AND SINCE QUEUE 090, A TAP IS A RULING. A tap arrives as a `callback_query`,
is answered so his phone stops spinning, and is written as a RECORD onto the
same branch as the inbox. The PC never edits a tracked file itself: the
container folds the records in, where one writer owns each file.

TWO KINDS OF TAP COME BACK THROUGH THAT ONE BRANCH, and `handle_callback`
tries the brief parser first and the card parser second, so neither guesses at
the other's bytes:
  - THE BRIEF'S TWO BUTTONS, readable and unreadable, ruled by Jafar
    2026-09-09 and the ONLY measure of this channel. `tools/runner/brief.py`.
  - A DECISION CARD'S OPTIONS, queue 090. `tools/runner/cards.py`. THE SENDING
    OF CARDS IS RETIRED (see `--send-cards` below); the tap half stays wired
    because cards already on his phone can still be tapped.

THE CARD SENDER IS RETIRED, RULED BY JAFAR 2026-09-09: "The brief generator,
the cards pass and the page notifier are retired." `--send-cards` and
`Bot.sweep_cards` below refuse to run and name the ruling; the loop no longer
calls either. What replaced them is one Producer turn a day writing one
message, sent by `--send-brief` with two buttons on it.

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
says which. 3 selftest failed. 5 a RETIRED entry point was called, which is
its own code so a caller that still exists shows up red rather than green. 6
`--send-brief` found no brief for that day, which is not a failure and is not
a send either.
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
import brief                                                  # noqa: E402
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


def send_photo(token, chat_id, path, caption, timeout=180, markup=None):
    """One picture, AS A PICTURE, optionally WITH BUTTONS ON IT. The payload.

    `sendPhoto` rather than `sendDocument` on purpose: a document arrives as a
    file to tap, and the deliverable is the photo in the chat. The proof of
    which one happened is the `photo` array in the answer, which the receipt
    carries; this function does not judge it, it returns it.

    `markup` IS WHAT MAKES QUEUE 232 ONE MESSAGE AND NOT TWO. `sendPhoto`
    takes the same `reply_markup` field `sendMessage` does, so the daily
    brief's readable/unreadable pair rides the picture it is about rather
    than a second message underneath it. It is the SAME keyboard object
    `send` takes and the same JSON encoding, because two encoders for one
    field is how a button arrives unparseable on one path only. Default None,
    so every caller that predates this sends exactly what it sent before.
    """
    with open(path, "rb") as fh:
        blob = fh.read()
    fields = {"chat_id": str(chat_id), "caption": caption}
    if markup is not None:
        fields["reply_markup"] = json.dumps(markup)
    ctype, body = multipart(fields,
                            {"photo": (os.path.basename(path), blob,
                                       "image/jpeg")})
    return _post(token, "sendPhoto", body, {"Content-Type": ctype}, timeout)


def send_video(token, chat_id, path, caption, timeout=600):
    """One clip, AS A VIDEO. Returns the platform's result payload.

    `sendVideo` rather than `sendDocument` for the same reason `send_photo`
    uses `sendPhoto`: a document arrives as a file to tap, and the
    deliverable is a clip that plays in the chat. The proof of which one
    happened is in the answer, which the receipt carries; this function does
    not judge it, it returns it.

    THE TIMEOUT IS LONGER THAN THE PHOTO'S ON PURPOSE. A still is tens of
    kilobytes and a clip is tens of megabytes over the same domestic uplink,
    so the 180 seconds that is generous for a picture is a coin toss for a
    video. `outbox.VIDEO_MAX_BYTES` refuses anything above the platform's
    own ceiling before this is ever called, so the worst case here is a
    large but legal file on a slow line.

    MP4 IS ASSUMED IN THE CONTENT TYPE ONLY. Telegram sniffs the container
    itself; the type here is a hint, and the extension travels in the name.
    """
    with open(path, "rb") as fh:
        blob = fh.read()
    ctype, body = multipart({"chat_id": str(chat_id), "caption": caption,
                             "supports_streaming": "true"},
                            {"video": (os.path.basename(path), blob,
                                       "video/mp4")})
    return _post(token, "sendVideo", body, {"Content-Type": ctype}, timeout)


def send_animation(token, chat_id, path, caption, timeout=600):
    """One animated clip, AS A CLIP THAT PLAYS. Returns the result payload.

    `sendAnimation` AND NOT `sendVideo`, because the clip this project can
    actually produce is a GIF. Pillow writes GIF and cannot write MP4, and
    adding a stitcher that could would be a new tool; the licence allowlist
    governs model weights and shipped assets rather than build-time
    libraries, but a new dependency still deserves a reason and there is not
    one when Telegram already plays a GIF as a looping clip. Handing a GIF
    to `sendVideo` gets it delivered as a file to tap, which is the outcome
    ruling 1 exists to avoid.

    Same long timeout as `send_video` and for the same reason: a clip is
    orders of magnitude larger than a still on the same domestic uplink.
    """
    with open(path, "rb") as fh:
        blob = fh.read()
    ctype, body = multipart({"chat_id": str(chat_id), "caption": caption},
                            {"animation": (os.path.basename(path), blob,
                                           "image/gif")})
    return _post(token, "sendAnimation", body, {"Content-Type": ctype},
                 timeout)


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
def looks_like_a_reading(text):
    """True when the message is an ATTEMPT at a number and nothing else.

    RULED BY JAFAR 2026-09-07, after the bot answered a question about the
    game with a lecture about whole numbers: "only parse a reading when the
    message is a bare number or answers a reading request."

    WHY IT HAPPENED, because the fix only makes sense against it. The budget
    question is asked once when the bot starts and `pending` then stays set
    for as long as it takes him to answer, which can be hours. Every message
    arriving in that window was fed to `parse_reading`, so a sentence about
    anything at all was refused as a malformed percentage and he was told to
    send a whole number instead. `pending` was being read as "he is answering
    me now" when all it ever meant was "I asked once".

    THE TEST IS THE SHAPE OF HIS MESSAGE, NOT THE STATE OF THE BOT. A decimal
    still counts as an attempt, so "76.5" reaches `parse_reading` and is
    refused there rather than rounded, which keeps the 2026-09-05 ruling
    exactly as it was. Prose is a message for the studio and is filed as one.
    """
    # \d* AND NOT \d+ AFTER THE POINT, so that "77.." survives the single
    # stop this strips and still READS as an attempt at a number. It is then
    # refused by parse_reading rather than filed as prose in silence, which
    # is what the ruling asks for: "77." records 77, "77.." is refused.
    return bool(re.match(r"^[+-]?\d+(?:[.,]\d*)?$", _bare(text)))


def _bare(text):
    """His typed number with the chrome taken off, for both readers.

    ONE TRAILING FULL STOP IS STRIPPED (A1, 2026-09-07). A phone that ends a
    sentence for him turns "77" into "77.", which the shape test read as
    prose and filed in silence with no read-back at all. That is a worse
    outcome than the refusal it replaced, and it is the same class as
    stripping "%": removing punctuation he did not mean is not rounding, and
    the number itself is still taken exactly as typed.
    """
    t = (text or "").strip().lower()
    for junk in ("percent", "per cent", "%"):
        t = t.replace(junk, "")
    t = t.strip()
    # ONE stop, unconditionally. Gating this on there being exactly one
    # dot made "77.." fall through as prose in silence, which is the
    # very outcome A1 exists to prevent. Stripping one leaves "77.",
    # which still reads as an attempt and is then refused out loud.
    return t[:-1].strip() if t.endswith(".") else t


def parse_reading(text):
    """(int, "") for a meter reading, or (None, why). RULED 2026-09-05.

    TAKEN AS TYPED AND NEVER ROUNDED. The meter reports whole percent, so the
    only honest reading is a whole number: "76,5" and "76.5" are refused
    rather than rounded to 76 or 77, because a rounded reading near the
    ceiling is the difference between stopping and carrying on, and a coerced
    one is a number the studio invented and wrote down as his.
    """
    t = _bare(text)
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
        # THE TAPS, queue 090 and the brief's two buttons of 2026-09-09.
        # Cumulative, each against the set it came from.
        self.taps = 0          # callback updates seen, the denominator
        self.taps_filed = 0    # of those, written as a record
        self.taps_refused = 0  # of those, refused with a reason
        self.taps_brief = 0    # of those FILED, ones that were brief taps
        self.reasons_filed = 0  # sentences filed as why a brief was unreadable
        # WHICH BRIEF IS WAITING FOR A REASON, set by an unreadable tap and
        # cleared by the next thing he types. IN MEMORY ONLY AND THAT IS
        # DELIBERATE: a restart loses the invitation, not the reason, because
        # whatever he types is filed as a message either way and
        # tools/producer-day.py shows tomorrow's writer his messages since the
        # tap alongside the reason record. Nothing he says is lost by this.
        self.reason_wanted = None
        # THE BACKLOG, filed once at startup rather than dropped.
        self.backlog_seen = 0
        self.backlog_filed = 0
        # THE INBOX HALF. `repo` is a parameter so the selftest can point the
        # whole path at a throwaway repository instead of this one.
        self.repo = repo or REPO
        self.filed = 0         # messages written to production/inbox
        self.pushed = 0        # of those, that reached the branch
        self.push_fails = 0    # cumulative, whole run
        self.replies = 0       # replies SENT, the denominator
        self.receipted = 0     # of those, ones whose id was written down
        self.last_flush = 0.0  # when the retry last ran, a wall clock
        # THE OUTBOUND HALF, queue 089. Cumulative over the whole run, each
        # against the set it came from on the done line.
        self.last_outbox = 0.0
        self.out_passes = 0
        self.out_sent = 0
        self.out_refused = 0
        # THE CARD COUNTERS ARE GONE WITH THE CARD SENDER, RETIRED 2026-09-09.
        # They counted a pass this loop no longer makes, and a counter that can
        # only ever read zero is a reading nobody can interpret. The brief is
        # NOT counted here either, and that is the honest answer rather than an
        # omission: it is sent by a one-shot `--send-brief` and not by this
        # loop, so this process has nothing to count. Its evidence is the
        # `brief-send done:` line, committed by the step that runs it.
        # RULED BY JAFAR 2026-09-08: "measure whether the bot's own loop
        # sweeps at all, with a per-pass counter in the published status.
        # Report the observed number rather than reasoning about whether it
        # should run." These three counters have existed since queue 089 and
        # went to this process's stdout, which is a window nobody reads: on
        # 2026-09-08 the studio argued for an hour about whether this loop
        # sweeps, with the answer already being printed to a console on his
        # desk. The file below puts them where the supervisor can carry them
        # off the machine.
        self.sweep_note = "no-pass-yet"
        self.write_sweep_status()

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
        """Send it, AND WRITE THE PLATFORM'S MESSAGE ID DOWN.

        THE RESULT USED TO BE DISCARDED, and that is why on 2026-09-07 there
        was no way to answer "report the Telegram message ID of the reply"
        from the container: the id existed for the length of this call and
        was never recorded anywhere the studio can read. A reply nobody can
        point to is indistinguishable from a reply that never went.

        The receipt rides `pc-inbox` with everything else, so it costs no new
        transport. It is written AFTER the send, so a send that throws leaves
        no receipt, which is the direction the error should point.
        """
        result = send(self.token, self.chat, text, markup)
        self.record_reply(text, result)
        return result

    def record_reply(self, text, result):
        """The receipt for one reply. Returns the message id, or None.

        THE KIND IS `bot-message` AND NOT A REPLY (A3): the opening line and
        the meter question are sent before he has said anything, so filing
        every one of these as a reply to a message would name something that
        did not happen. One kind, and `outbox.outbound_summary` keys its
        `replies` bucket on it.

        WRAPPED, LIKE `file_message`: a receipt that cannot be written must
        not take the channel down, because the reply itself has already been
        delivered by the time this runs.
        """
        self.replies += 1
        mid = (result or {}).get("message_id")
        if not mid:
            OUT.say("reply: SENT BUT NOT RECEIPTED, the platform returned no "
                    "message id (%d receipted of %d reply/replies)"
                    % (self.receipted, self.replies))
            return None
        try:
            stamp = datetime.datetime.now(
                datetime.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
            name = "%s-reply-%d.receipt.txt" % (stamp, int(mid))
            d = os.path.join(self.repo, *inbox.OUTBOUND_DIR.split("/"))
            os.makedirs(d, exist_ok=True)
            # A3: THE PLATFORM'S OWN CLOCK WHERE IT GAVE ONE. `date` is
            # when Telegram accepted the message; `time.time()` is this PC's
            # clock, which is a different quantity and drifts.
            # A3: THE PLATFORM'S OWN CLOCK WHERE IT GAVE ONE, and the
            # window says which was used, because a receipt timed by the PC
            # and one timed by Telegram are two different quantities.
            stamped = (result or {}).get("date")
            if isinstance(stamped, int) and not isinstance(stamped, bool):
                when, clock = stamped, "telegram"
            else:
                when, clock = int(time.time()), "this-pc"
            body = outbox.render_receipt(
                inbox.OUTBOUND_DIR + "/" + name, "bot-message",
                when, int(mid), len(text or ""), None, None, None,
                "a reply is not a file committed first, so there is no file "
                "commit instant to measure from.")
            # newline="\n" LIKE EVERY OTHER WRITER ON THIS BRANCH (A3). A
            # file written with the platform default lands with CRLF on
            # Windows, and this batch exists because of what CRLF did here.
            with open(os.path.join(d, name), "w", encoding="utf-8",
                      newline="\n") as fh:
                fh.write(body)
        except Exception as e:                                # noqa: BLE001
            OUT.say("reply: sent as messageId=%d but the receipt could not "
                    "be written (%s). The reply arrived; only the proof is "
                    "missing." % (int(mid), type(e).__name__))
            return int(mid)
        self.receipted += 1
        OUT.say("reply: sent messageId=%d, receipted (%d of %d reply/replies "
                "receipted) sentEpochClock=%s. The next flush carries it, at "
                "most a minute."
                % (int(mid), self.receipted, self.replies, clock))
        return int(mid)

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
        # AND IF THIS IS THE SENTENCE AFTER AN UNREADABLE TAP, IT IS ALSO
        # FILED AS THE REASON, ruled 2026-09-09. A SECOND COPY AND NOT A
        # DIVERSION: whatever he types is a message to the studio first, and
        # the reason record is an extra pointer for tomorrow's writer. Filing
        # first, attributing second, so a broken reason path cannot cost him
        # the message.
        self.file_brief_reason(text, sent_epoch, update_id)
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
            # `pending_all`, NOT `pending_files` (B2, ruled 2026-09-07). A
            # reply receipt is not a message, so a flush that triggers only
            # on messages left every receipt on the disk until he happened
            # to send something else. The window said "it reaches the studio
            # on the next flush" while no flush would ever run for it: built,
            # not running, on the one path it was built for.
            waiting, _tip = inbox.pending_all(self.repo)
            if not waiting:
                return
            res = inbox.push_pending(self.repo, OUT.say)
        except Exception as e:                                # noqa: BLE001
            OUT.say("inbox: the retry could not run (%s)" % type(e).__name__)
            return
        if res["ok"] and res["pushed"]:
            his = inbox.messages_in(res["pushed"])
            tapped = inbox.rulings_in(res["pushed"])
            self.pushed += len(his)
            # THE REPLY IS GATED ON SOMETHING OF HIS BEING IN THE PUSH, and
            # this is the hazard the ruling named rather than a nicety. A
            # reply writes a receipt; a receipt makes the next flush non
            # empty; so a flush that spoke for receipts alone would send him
            # one message a minute for ever. Receipts travel in silence and
            # are reported to the window instead.
            if his or tapped:
                self.reply("The %d message(s) I was holding on the PC are on "
                           "the branch now. Nothing was lost." % len(his))
            else:
                OUT.say("inbox: pushed %d record(s) of the studio's own and "
                        "nothing of his, so nothing was sent to his phone "
                        "(a reply here would write a receipt and loop)"
                        % len(res["pushed"]))
        elif not res["ok"]:
            OUT.say("inbox: still holding %d message(s) and %d file(s) in "
                    "all: %s" % (len(inbox.messages_in(res["pending"])),
                                 len(res["pending"]), res["detail"]))

    #: WHERE THE PER-PASS COUNTER GOES. Beside the supervisor's own status
    #: file, in the same untracked directory, so the watcher's hard reset
    #: cannot delete it and tools/supervise.py can read it without importing
    #: this module.
    SWEEP_STATUS_REL = "game-design/pc-jobs/bot-sweep.txt"

    def write_sweep_status(self):
        """Publish the sweep counters. Called on EVERY path out of a pass.

        WRITTEN ONCE AT STARTUP TOO, with botSweepPasses=0, so the three
        states are distinguishable rather than collapsed into one silence:
        NO FILE means this process never started; passes=0 with a fresh
        botSweepWrittenAt means it started and the loop has not reached the
        sweep; passes>0 means the loop sweeps and the number says how often.
        A missing file and a zero are different facts about the same
        question and the old stdout line could tell neither.
        """
        try:
            path = os.path.join(self.repo,
                                *self.SWEEP_STATUS_REL.split("/"))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            up = int(time.time() - self.started)
            since = (int(time.time() - self.last_outbox)
                     if self.last_outbox else -1)
            lines = [
                "botSweepPasses=%d" % self.out_passes,
                "botSweepSent=%d" % self.out_sent,
                "botSweepRefused=%d" % self.out_refused,
                "botSweepEverySec=120",
                "botSweepSecSinceLast=%s" % (since if since >= 0
                                             else "nothing-measured"),
                "botSweepLastResult=%s" % self.sweep_note.replace(" ", "-"),
                # THE botCards* KEYS ARE GONE, 2026-09-09, with the card
                # sender they measured. A key that can only ever print 0 after
                # a retirement is worse than no key: a reader cannot tell it
                # from a loop that stopped sweeping. The brief has no key here
                # because this loop does not send it (see __init__).
                "botBriefTapsFiled=%d" % self.taps_brief,
                "botBriefReasonsFiled=%d" % self.reasons_filed,
                "botUptimeSec=%d" % up,
                "botSweepWrittenAt=%s"
                % time.strftime("%Y-%m-%dT%H:%M:%S"),
            ]
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(lines) + "\n")
        except OSError:
            pass

    #: RETIRED 2026-09-09 BY JAFAR'S RULING, VERBATIM: "The brief generator,
    #: the cards pass and the page notifier are retired." The interval that was
    #: here measured how often this loop swept the decision cards; the loop no
    #: longer sweeps them at all, so the number is gone rather than left
    #: standing as a setting for something that does not run.
    #:
    #: WHAT REPLACED IT. One Producer turn a day writes one message, and it
    #: carries two buttons. `tools/runner/brief.py` and `--send-brief`.
    #:
    #: WHAT THE RETIRED PASS MEASURED BEFORE IT WENT, because the measurement
    #: is the reason the ruling is right and not a waste: on 2026-09-09 at
    #: 10:42 local it sent six cards from the decision queue in two seconds,
    #: six of six waiting, and one of them was a card the studio had already
    #: withdrawn. The receipts are production/pc-ops/cards-send.txt. Machinery
    #: with nobody's judgment in it sent him stale questions faster than
    #: anybody could stop it.
    def sweep_cards(self, every=None):
        """RETIRED. It raises, so a caller that comes back is loud.

        NOT DELETED, AND NOT A COMMENT EITHER. Rule 6 in reverse: a thing is
        retired when nothing calls it. The loop's call is gone (see
        `poll_forever`), `--send-cards` refuses, and this raise is what catches
        a third caller somebody adds next month without reading either.
        """
        raise cards.SendingRetired(cards.RETIREMENT)

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
            # A PASS THAT RAISED IS STILL A PASS THAT HAPPENED, and it is the
            # one a reader most needs to see, so the counter moves and the
            # note names the failure rather than the file going stale.
            self.out_passes += 1
            self.sweep_note = "raised/%s" % type(e).__name__
            self.write_sweep_status()
            return
        self.out_passes += 1
        self.out_sent += len(res["sent"])
        self.out_refused += len(res["refused"])
        self.sweep_note = ("sent%d/refused%d/of%d"
                           % (len(res["sent"]), len(res["refused"]),
                              len(res.get("files", res["sent"]))))
        self.write_sweep_status()

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
        # THE SHAPE OF THE MESSAGE GATES THIS, NOT `pending` ALONE (ruled
        # 2026-09-07). An open question is not a claim on every sentence he
        # types; prose falls through to the ordinary message path below and
        # is filed, with no refusal and no lecture. The question stays open
        # and `/budget` or a bare number still answers it.
        if self.pending and looks_like_a_reading(text):
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
        # A2: WHEN IT COULD HAVE BEEN MEANT AS A READING, SAY SO ONCE.
        # Prose is filed and never refused, but prose carrying a digit while
        # the meter question is open is the one case where he might think he
        # answered it. One sentence, no demand, and the question stays open.
        # A2, RULED 2026-09-07: the sentence appears if and only if the
        # question is open AND the message carries a digit. Prose with no
        # digit could not have been meant as a reading, and a digit with no
        # question open answers nothing.
        tail = "Commands: /budget, /ping, /help."
        if self.pending and any(c.isdigit() for c in (text or "")):
            tail = ("The budget question is still open; a bare whole number "
                    "answers it. " + tail)
        return self.reply(echo_reply(
            text, "%s\n%s"
                  % (self.file_message(text, sent_epoch, update_id), tail)))

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
        # THE BRIEF'S TWO BUTTONS FIRST, ruled 2026-09-09 and the only measure
        # of this channel. Two callback families share this one door: this
        # parser refuses anything that is not a brief tap and hands it on to
        # the card parser below, so neither ever guesses at the other's bytes.
        b_day, b_verdict, _b_why = brief.parse_callback(cq.get("data"))
        if b_day is not None:
            return self.handle_brief_tap(cq, cid_q, b_day, b_verdict,
                                         update_id)
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

    def handle_brief_tap(self, cq, cid_q, day, verdict, update_id):
        """A TAP ON THE BRIEF BECOMES A RECORD TOMORROW'S WRITER READS.

        ANSWERED FIRST, ALWAYS, like every other path out of `handle_callback`:
        his phone shows a spinner on the button until the bot answers, so an
        unanswered tap reads as a dead message even when the record was filed.

        AND UNREADABLE OPENS ONE QUESTION. Jafar's ruling: "Unreadable means
        tomorrow's is written differently, and the Producer says what it
        changed." The reply invites the reason and the next thing he types is
        filed as one, in ADDITION to being filed as an ordinary message, so
        nothing depends on him answering.
        """
        try:
            res = brief.tap_and_push(self.repo, day, verdict,
                                     self.tap_epoch(cq), update_id, OUT.say)
        except Exception as e:                                # noqa: BLE001
            self.taps_refused += 1
            self.push_fails += 1
            note = ("I could not file that on the PC (%s). It is NOT "
                    "recorded, so please tap it again once the window on the "
                    "PC stops showing that error." % type(e).__name__)
            OUT.say("brief tap FAILED to file (%s). The channel keeps running."
                    % type(e).__name__)
        else:
            self.taps_filed += 1
            self.taps_brief += 1
            if res["ok"]:
                self.pushed += len(res["pushed"])
            else:
                self.push_fails += 1
            self.last_flush = time.time()
            self.reason_wanted = day if verdict == brief.UNREADABLE else None
            note = brief.tap_reply_text(res)
            OUT.say("brief tap filed: briefDay=%s verdict=%s (%d brief tap(s) "
                    "of %d filed tap(s) of %d seen)"
                    % (day, verdict, self.taps_brief, self.taps_filed,
                       self.taps))
        self.answer_tap(cid_q, note.split("\n")[0])
        self.reply(note)

    def file_brief_reason(self, text, sent_epoch, update_id):
        """The sentence after an unreadable tap, written where tomorrow's
        Producer turn reads it. Returns the reason record path or None.

        WRAPPED AND NEVER FATAL: this is an extra copy of something already
        filed as a message, so a failure here must not cost him the message.
        """
        day, self.reason_wanted = self.reason_wanted, None
        if not day:
            return None
        try:
            res = brief.reason_and_push(self.repo, day, text,
                                        int(sent_epoch or time.time()),
                                        int(update_id or 0), OUT.say)
        except Exception as e:                                # noqa: BLE001
            OUT.say("brief reason: could not be filed (%s). His message is "
                    "still filed as a message." % type(e).__name__)
            return None
        self.reasons_filed += 1
        return res["file"]

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
            finally:
                # THE WORK IS NOT DOWNSTREAM OF THE POLL. Ruled from evidence
                # on 2026-09-08. These two lines used to sit inside the `try`
                # AFTER getUpdates, so a poll that raised took the except arm,
                # slept, and looped, and neither of them ever ran. On Jafar's
                # PC that produced a bot with a perfect health report and no
                # work done: it sent its two startup messages before the loop
                # began, then nothing for thirteen hours, twice over, while
                # uptime climbed and the supervisor called it running.
                #
                # A MESSAGE FROM HIM IS STILL THE THING THAT MUST NOT WAIT, so
                # this stays AFTER `handle`; the change is that a broken poll
                # can no longer stop the half of the job that does not need
                # Telegram to answer. Pushing receipts and sending the outbox
                # are local work plus a git push, and neither has any reason
                # to depend on getUpdates succeeding.
                #
                # WRAPPED, because a raise in a finally would replace whatever
                # the try was already doing, including the deliberate returns
                # above it.
                #
                # AND THE CARDS SWEEP IS NOT HERE ANY MORE. It was added to
                # this block on 2026-09-09 at about 10:00 and retired by Jafar
                # the same day, after the pass it enabled sent him six cards
                # off a queue one of whose cards was already withdrawn: "The
                # channel fails because nobody with judgment sits in it.
                # Replace the machinery with one judgment step." The one
                # judgment step is a Producer turn writing one message a day,
                # sent by `--send-brief`, which is a one-shot and deliberately
                # NOT swept from here: two senders on one receipt race, and a
                # duplicate of the one message a day is itself a channel
                # failure.
                try:
                    self.flush_inbox()
                    self.sweep_outbox()
                except Exception as e:                        # noqa: BLE001
                    OUT.say("the offline half could not run this pass (%s). "
                            "The bot keeps polling." % type(e).__name__)

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
                "outboxPasses=%d outboxSent=%d outboxRefused=%d "
                "briefTapsFiled=%d/%d briefReasonsFiled=%d "
                "repliesReceipted=%d/%d"
                % (int((time.time() - self.started) / 60), self.seen,
                   self.mine, self.seen, self.other, self.seen,
                   self.nontext, self.mine, self.readings, self.answers,
                   self.refused, self.answers, self.taps, self.seen,
                   self.taps_filed, self.taps, self.taps_refused, self.taps,
                   self.backlog_filed, self.backlog_seen, self.net_errors,
                   self.filed, self.pushed, self.filed, self.push_fails,
                   "unreadable" if waiting < 0 else waiting, self.out_passes,
                   self.out_sent, self.out_refused,
                   self.taps_brief, self.taps_filed, self.reasons_filed,
                   self.receipted, self.replies))


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

    def photo_sender(path, caption):
        """The wire for a test request that names a picture (ruling 5).

        WITHOUT THIS THE FEATURE IS BUILT AND NOT RUNNING, which is rule 6
        here: `outbox.sweep` refuses a message naming a picture when no photo
        sender is wired in, so every captioned test request would have been
        refused on his PC while every selftest passed in the container. The
        shape is deliberately identical to `frames_pass`'s closure, including
        the OSError arm, because an unreadable file must reach the sweep as a
        refusal it can write down rather than as a traceback.
        """
        try:
            return send_photo(creds.token, str(creds.chat_id), path, caption)
        except ApiError as e:
            raise outbox.SendFailed(str(e))
        except OSError as e:
            raise outbox.SendFailed("could not read the file (%s)"
                                    % type(e).__name__)

    def video_sender(path, caption_text):
        """The wire for a test request that names a CLIP (ruling 1).

        THE SECOND HALF OF THE SAME OMISSION. `photo_sender` was added after
        the sweep was found refusing every captioned request for want of a
        wire; the clip path arrived later and repeated it exactly, so the
        walk clip CI produced had no route to his phone at all: --send-clip
        is a command line, and nothing types on that machine. The extension
        picks sendAnimation or sendVideo here, in one place, because the
        sweep should hand over a path and know nothing of Telegram methods.
        """
        wire = send_animation if str(path).lower().endswith(".gif") \
            else send_video
        try:
            return wire(creds.token, str(creds.chat_id), path, caption_text)
        except ApiError as e:
            raise outbox.SendFailed(str(e))
        except OSError as e:
            raise outbox.SendFailed("could not read the file (%s)"
                                    % type(e).__name__)

    res = outbox.sweep(repo, sender, say=say, photo_sender=photo_sender,
                       video_sender=video_sender)
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
    """RETIRED 2026-09-09. It raises; nothing calls it.

    WHAT IT WAS: the wire, the file and the receipt store for
    `cards.send_cards`. WHY IT IS GONE: Jafar's ruling of 2026-09-09, carried
    verbatim in `cards.RETIREMENT`. The pass ran once, at 10:42 local that
    morning, and sent six cards in two seconds off a queue one of whose cards
    the studio had already withdrawn. That measurement is what the ruling
    rests on, and it is kept in production/pc-ops/cards-send.txt.

    NOT DELETED: the body it replaced is in the history of this file, and the
    thing it called still reads the decision queue for the glance. A raise
    rather than a comment, because a comment does not stop a caller.
    """
    raise cards.SendingRetired(cards.RETIREMENT)


def brief_pass(creds, repo=None, say=None, day=None):
    """THE ONE MESSAGE A DAY, WITH ITS TWO BUTTONS. Ruled 2026-09-09.

    This supplies the wire, the file, the receipt store and the register check;
    every decision, count and string is `brief.send_brief`'s, where the tests
    run. What the Producer wrote is sent byte for byte: nothing here composes,
    ranks, summarises or prefixes anything.

    THE CHECK RUNS HERE, ON THE SENDING SIDE, AFTER THE WRITING AND BEFORE THE
    SEND, which is both the ruling of 2026-09-09 ("the register stays as a
    format check after the Producer writes") and the split producer.md already
    describes: the Producer writes the file, the sender checks it. It is the
    same `tools/producer-check.py` through the same `outbox.run_check`, so a
    brief is graded by the one implementation of the register and not a copy.

    A ONE-SHOT AND DELIBERATELY NOT IN THE POLL LOOP. Two senders sharing one
    receipt race, and a duplicate of the one message a day is itself a channel
    failure. The step that runs this is in
    .github/workflows/ledger-install-supervisor-task.yml and fires on a push
    that touches production/briefs/.
    """
    repo = repo or REPO
    say = say or OUT.say
    day = day or brief.today()
    rel = brief.brief_rel(day)
    try:
        with open(outbox.full_path(repo, rel), "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        # NOT AN ERROR AND NOT A PASS EITHER: no brief for today is a real
        # state of this channel (silence is an acceptable exit) and it prints
        # its denominator rather than a bare zero.
        here = sorted(brief.briefs_on_disk(repo))
        say("brief: NOTHING MEASURED, there is no brief for %s (%s). %d "
            "brief(s) are in the tree, newest %s. Nothing was sent."
            % (day, type(e).__name__, len(here),
               here[-1] if here else "nothing-measured"))
        return {"day": day, "rel": rel, "sent": None, "already": None,
                "refused": None, "clause": "", "messageId": None,
                "records": [], "checked": False, "buttons": 0, "chars": 0,
                "missing": True,
                # NOTHING MEASURED ABOUT A PICTURE EITHER, said in the words
                # rather than left to a default: no brief means nobody looked.
                "photoState": "nothing-measured", "photoRef": None,
                "photoSizes": "", "photoArrived": False, "photoWhy": "",
                "photoOverBy": 0}

    def sender(body, keyboard):
        try:
            return send(creds.token, str(creds.chat_id), body, keyboard)
        except ApiError as e:
            raise outbox.SendFailed(str(e))

    def photo_sender(path, caption, keyboard):
        """THE PICTURE AND THE PAIR IN ONE CALL, queue 232.

        `sendPhoto` with a `reply_markup`, which is the whole mechanism: no
        second message, no album, no link. A wire failure here is NOT retried
        as plain text in the same pass, deliberately: the upload may have
        reached him, and a second send of the one message a day is itself a
        channel failure. It stays unsent and the next pass tries again, which
        is the rule a Producer message already follows.
        """
        try:
            return send_photo(creds.token, str(creds.chat_id), path, caption,
                              markup=keyboard)
        except ApiError as e:
            raise outbox.SendFailed(str(e))
        except OSError as e:
            raise outbox.SendFailed("could not read the picture (%s)"
                                    % type(e).__name__)

    def check(rel_to_check):
        return outbox.run_check(repo, "brief", rel_to_check)

    # WHAT THE DAY ASKS TO CARRY, read off the disk here because here is the
    # sending side; every decision about it is `brief.photo_plan`'s, where the
    # tests run. A day naming nothing is the ordinary case and not an error.
    photo = brief.resolve_photo(repo, day)
    res = brief.send_brief(day, text, sender, brief.BriefReceipts(repo),
                           check=check, say=say, photo=photo,
                           photo_sender=photo_sender)
    say(brief.brief_done_line(res))
    if res["records"]:
        push = inbox.push_pending(repo, say)
        if not push["ok"]:
            say("brief: %d record(s) are written on this PC but NOT pushed "
                "(%s). Nothing he was sent is forgotten: the receipt is on "
                "this disk and the dedupe reads it from there."
                % (len(res["records"]), push["detail"]))
    return res


def video_pass(creds, path, caption, repo=None, say=None, run_sha="unknown"):
    """One clip, or the words that say why there is none (ruling 1).

    The counterpart of `frames_pass` for a video. It supplies only the wire;
    every decision about size, absence and refusal lives in
    `outbox.send_video`, on this machine, where the tests run.

    `path` MAY BE None AND THAT IS A REAL CASE, not a caller bug: a probe
    that crashed before it captured anything has no clip, and the honest
    outcome is the verdict sent as words rather than a refusal about a
    missing file. Only a path expected to exist is passed here.
    """
    repo = repo or REPO
    say = say or OUT.say

    def video_sender(p, caption_text):
        """THE EXTENSION PICKS THE METHOD, not the caller. A GIF handed to
        sendVideo arrives as a file to tap rather than a clip that plays,
        and the caller here is a CI step that knows what it rendered but
        nothing about Telegram's methods."""
        wire = send_animation if str(p).lower().endswith(".gif") else send_video
        try:
            return wire(creds.token, str(creds.chat_id), p, caption_text)
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

    res = outbox.send_video(repo, video_sender, text_sender, path, caption,
                            run_sha=run_sha, say=say)
    say(outbox.video_done_line(res))
    if res.get("records"):
        push = inbox.push_pending(repo, say)
        if not push["ok"]:
            say("clip: the receipt is on this PC but NOT pushed (%s)"
                % push["plain"])
    return res


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
def _selftest_cases(ok, bad, state):
    """Every case, appending to `ok` / `bad`. Run by `outbox.run_selftest`.

    SPLIT FROM `selftest()` 2026-09-06 so a raise anywhere below still reaches
    the count line ledger/verify.py reads. A suite that dies mid-run and a
    suite that runs and reports nothing are different facts with different next
    actions, and the gate can only tell them apart if the dying one still
    prints its numbers and exits on its own code.
    """

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
    # Recorded before any case runs: on a crash the directory to open is the
    # first thing the reader needs, and `selftest()` prints it either way.
    state["fixture"] = home
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
              "production/inbox/" + inbox.message_name(sent, 4128)).split("/"))),
          b.said[-1][:80])
    # AND HE IS NOT LECTURED FOR IT. Ruled 2026-09-07, after the bot met
    # "what is the studio doing" with a demand for a whole number. The
    # question stays open; it just stops answering itself with his prose.
    check("accept/and-prose-is-not-refused-as-a-reading",
          NUMERIC_PLACEHOLDER not in b.said[-1]
          and "I cannot take that" not in b.said[-1]
          and b.refused == 0 and b.answers == 0 and b.pending == "total",
          b.said[-1][:90])

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
    # NUMBER-SHAPED AND WRONG. Each of these is an attempt at the meter, so
    # each is refused rather than rounded, which is the 2026-09-05 ruling
    # unchanged. "about half" is NOT in this list any more: see below.
    for wrong in ("76,5", "76.5", "77.0", "101", "-3"):
        b4b.handle(update(wrong, 4200 + len(b4b.said)))
    check("reject/every-non-integer-is-refused-and-records-nothing",
          b4b.readings == 0 and b4b.refused == 5 and b4b.answers == 5
          and b4b.pending == "fable"
          and "budgetRefused=5/5" in b4b.done_line(), b4b.done_line())
    check("reject/and-the-refusal-tells-him-what-is-wanted",
          NUMERIC_PLACEHOLDER in b4b.said[-1]
          and "Nothing was recorded" in b4b.said[-1], b4b.said[-1][-120:])
    check("accept/a-refused-reading-is-still-filed-for-the-studio",
          b4b.filed == 5 and "inboxFiled=5" in b4b.done_line(),
          b4b.done_line())
    # AND THE PROSE HALF, WHICH IS THE 7 SEPTEMBER RULING ITSELF: a sentence
    # is a message for the studio, not a malformed percentage. It moves
    # neither counter and it leaves the question open.
    before = (b4b.refused, b4b.answers, b4b.filed)
    b4b.handle(update("about half, ask me later", 4260))
    check("accept/prose-during-an-open-question-is-a-message-not-an-answer",
          (b4b.refused, b4b.answers) == before[:2]
          and b4b.filed == before[2] + 1 and b4b.pending == "fable"
          and NUMERIC_PLACEHOLDER not in b4b.said[-1], b4b.said[-1][:90])
    b4b.handle(update("77", 4299))
    check("accept/and-the-next-good-one-is-taken-as-typed",
          b4b.readings == 1 and "fable at 77" in b4b.said[-1]
          and "budgetRefused=5/6" in b4b.done_line(), b4b.done_line())

    # AND A HELD MESSAGE IS REPORTED, NOT DROPPED.
    inbox._fixture_git(["remote", "set-url", "--push", "origin",
                        os.path.join(home, "no-such-remote.git")], watcher)
    b5 = Captured()
    b5.handle(update("while the uplink is down", 4133))
    check("reject/inbox-a-failed-push-holds-the-message-and-says-so",
          b5.filed == 1 and b5.pushed == 0 and b5.push_fails == 1
          and "Saved on the PC" in b5.said[-1]
          and "Nothing is lost" in b5.said[-1]
          and "retrying every minute" in b5.said[-1],
          b5.said[-1][:100] if b5.said else "SILENT")
    # AND NO GIT INTERNALS REACH THE CHAT. This is the half he saw on his
    # phone on 2026-09-07: a sha and a truncated git warning.
    check("reject/and-the-held-message-carries-no-git-internals",
          not any(w in b5.said[-1] for w in ("fatal:", "error:", "warning:",
                                             "not shown", "refs/", "origin")),
          b5.said[-1][:110])
    check("reject/inbox-and-the-done-line-counts-what-is-waiting",
          "inboxPushed=0/1" in b5.done_line()
          and "inboxPending=1" in b5.done_line(), b5.done_line())
    inbox._fixture_git(["remote", "set-url", "--push", "origin", far], watcher)
    b5.flush_inbox(every=0)
    check("accept/inbox-the-retry-clears-the-backlog-and-says-so",
          inbox.pending_files(watcher)[0] == []
          and "holding on the PC are on the branch now" in b5.said[-1],
          b5.said[-1][:90])

    # ---- THE REPLY RECEIPT, added 2026-09-07 because Jafar asked for the
    # message id of a reply and nothing in this file had ever written one
    # down. `Captured` overrides `reply` so the wire is never touched, which
    # means `record_reply` is exercised HERE, directly, or not at all.
    b6 = Captured()
    before6 = len(inbox.outbound_files(watcher))
    got = b6.record_reply("a reply that really went", {"message_id": 60677})
    after6 = inbox.outbound_files(watcher)
    check("accept/a-reply-message-id-is-recorded",
          got == 60677 and b6.receipted == 1 and b6.replies == 1
          and len(after6) == before6 + 1, "%s / %d file(s)" % (got, len(after6)))
    written = os.path.join(watcher, *after6[-1].split("/"))
    with open(written, encoding="utf-8") as _fh6:
        body6 = _fh6.read()
    check("accept/and-the-receipt-carries-the-id-a-reader-can-find",
          "messageId: 60677" in body6, body6.splitlines()[:1])
    check("accept/and-the-receipt-is-a-name-the-reader-accepts",
          inbox.OUTBOUND_RE.match(os.path.basename(after6[-1])) is not None,
          os.path.basename(after6[-1]))
    check("accept/and-it-rides-the-same-branch-as-a-message",
          after6[-1] in inbox.pending_all(watcher)[0],
          inbox.pending_all(watcher)[0][-2:])
    check("accept/and-the-done-line-carries-the-denominator",
          "repliesReceipted=1/1" in b6.done_line(), b6.done_line()[-40:])
    # THE REJECTING HALF: a platform answer with no id writes nothing and
    # says so, rather than inventing a receipt for a reply it cannot prove.
    before7 = len(inbox.outbound_files(watcher))
    none7 = b6.record_reply("a reply the platform did not confirm", {})
    check("reject/no-message-id-writes-no-receipt",
          none7 is None and b6.replies == 2 and b6.receipted == 1
          and len(inbox.outbound_files(watcher)) == before7
          and "repliesReceipted=1/2" in b6.done_line(), b6.done_line()[-40:])

    # ---- B2: THE RECEIPT MUST TRAVEL, AND MUST NOT START A LOOP ------
    # Ruled 2026-09-07. `flush_inbox` used to decide from `pending_files`,
    # which is messages only, so a receipt sat on the disk until he happened
    # to send something else, while the window said it had gone. The two
    # halves are asserted together because fixing one alone is a trap: a
    # flush that also SPOKE for receipts would reply, write a receipt, and
    # send him one message a minute for ever.
    b7 = Captured()
    inbox.push_pending(watcher, lambda _s: None)          # start from clean
    check("accept/b2-the-fixture-starts-with-nothing-waiting",
          inbox.pending_all(watcher)[0] == [], inbox.pending_all(watcher)[0])
    b7.record_reply("a reply, and nothing of his", {"message_id": 60678})
    waiting_now = inbox.pending_all(watcher)[0]
    check("accept/b2-a-receipt-alone-is-a-real-pending-file",
          len(waiting_now) == 1 and not inbox.messages_in(waiting_now),
          waiting_now)
    saidbefore = len(b7.said)
    b7.flush_inbox(every=0)
    check("accept/b2-and-the-flush-actually-takes-it",
          inbox.pending_all(watcher)[0] == [],
          inbox.pending_all(watcher)[0])
    check("reject/b2-but-says-nothing-to-him-about-it",
          len(b7.said) == saidbefore, b7.said[saidbefore:][:1])
    # AND THE OTHER DIRECTION, so this is not a flush that never speaks:
    # something of his in the push still gets the sentence.
    inbox.write_message(watcher, "his own message", sent + 99, 4141)
    b7.flush_inbox(every=0)
    check("accept/b2-but-a-message-of-his-is-still-announced",
          len(b7.said) == saidbefore + 1
          and "1 message(s) I was holding" in b7.said[-1],
          b7.said[-1][:80] if len(b7.said) > saidbefore else "SILENT")

    # ---- A1 and A2: the reading gate's two corrections ----------------
    b8 = Captured()
    b8.pending, b8.total = "fable", 40
    b8.handle(update("77.", 4301))
    check("accept/a1-a-trailing-full-stop-is-still-a-reading",
          b8.readings == 1 and "fable at 77" in b8.said[-1], b8.said[-1][:70])
    # AND THE REJECTING HALF, which is what keeps A1 from being a loosening:
    # one stop is a phone finishing a sentence, two is not a number.
    b8b = Captured()
    b8b.pending, b8b.total = "fable", 40
    b8b.handle(update("77..", 4303))
    check("reject/a1-two-full-stops-are-refused-not-filed-in-silence",
          b8b.readings == 0 and b8b.refused == 1
          and NUMERIC_PLACEHOLDER in b8b.said[-1], b8b.said[-1][-90:])

    # A2's three rows, exactly as ruled: digit with the question open, no
    # digit, and a digit with no question open.
    A2 = "The budget question is still open; a bare whole number answers it."
    b9 = Captured()
    b9.pending, b9.total = "fable", 40
    b9.handle(update("how did run 25 go", 4302))
    check("accept/a2-prose-with-a-digit-while-open-says-the-sentence",
          b9.readings == 0 and b9.refused == 0 and b9.pending == "fable"
          and A2 in b9.said[-1], b9.said[-1][-110:])
    b9.handle(update("and what about the street", 4304))
    check("reject/a2-prose-with-no-digit-does-not",
          A2 not in b9.said[-1], b9.said[-1][-80:])
    b9c = Captured()
    b9c.pending = None
    b9c.handle(update("run 25 looked good", 4305))
    check("reject/a2-a-digit-with-no-open-question-does-not",
          A2 not in b9c.said[-1], b9c.said[-1][-80:])

    # A3: the kind and the platform's own clock, from a planted result.
    bA3 = Captured()
    bA3.record_reply("timed by telegram", {"message_id": 60679,
                                           "date": 1788000123})
    relA3 = inbox.outbound_files(watcher)[-1]
    with open(os.path.join(watcher, *relA3.split("/")), encoding="utf-8") as f3:
        bodyA3 = f3.read()
    check("accept/a3-the-receipt-kind-is-bot-message",
          "kind: bot-message" in bodyA3, bodyA3.splitlines()[2:3])
    check("accept/a3-and-the-epoch-is-the-platforms-not-this-pcs",
          "sentEpoch: 1788000123" in bodyA3,
          [l for l in bodyA3.splitlines() if l.startswith("sentEpoch")])

    # ---- RULING 5 AND RULING 1: THE WIRES ARE ACTUALLY CONNECTED ------
    # These exist because the fault they catch shipped once already today.
    # `outbox.sweep` REFUSES a message naming a picture when no photo sender
    # is wired in, so a captioned test request would have been refused on his
    # PC while every case in outbox.py's own selftest passed here. Built is
    # not running: the module tests the decision, and only these test that
    # anything calls it.
    class _Creds(object):
        token, chat_id = "not-a-real-token", "0"

    seen = {}
    real_sweep, real_sendvid = outbox.sweep, outbox.send_video
    real_photo, real_video = send_photo, send_video
    try:
        # CAPTURE, THEN DELEGATE TO THE REAL FUNCTION. A hand-built return
        # value would be a second implementation of a result shape, and the
        # first thing it did was disagree with the real one.
        def _spy_sweep(repo, sender, **kw):
            seen.update(sweep_kw=kw, sweep_sender=sender)
            return real_sweep(repo, sender, **kw)

        def _spy_video(repo, vs, ts, path, cap, **kw):
            seen.update(vid_sender=vs, vid_path=path, vid_caption=cap)
            return real_sendvid(repo, vs, ts, None, cap, **kw)

        outbox.sweep = _spy_sweep
        outbox.send_video = _spy_video
        outbox_pass(_Creds(), watcher, lambda _s: None)
        video_pass(_Creds(), "/tmp/nothing.mp4", "a verdict", watcher,
                   lambda _s: None)
    finally:
        outbox.sweep, outbox.send_video = real_sweep, real_sendvid

    check("accept/ruling5-the-sweep-is-given-a-photo-sender",
          callable(seen.get("sweep_kw", {}).get("photo_sender")),
          sorted(seen.get("sweep_kw", {})))
    # AND A VIDEO SENDER, which the row above did not cover and which is
    # exactly how the clip half slipped through: a test that asks only about
    # the wire it was written for cannot see the wire added after it.
    check("accept/ruling1-the-sweep-is-given-a-video-sender-too",
          callable(seen.get("sweep_kw", {}).get("video_sender")),
          sorted(seen.get("sweep_kw", {})))
    check("accept/ruling1-send_video-is-given-a-video-sender",
          callable(seen.get("vid_sender"))
          and seen.get("vid_path") == "/tmp/nothing.mp4"
          and seen.get("vid_caption") == "a verdict", seen.get("vid_path"))

    # AND EACH CLOSURE REACHES ITS OWN WIRE, not merely exists. A photo
    # sender that quietly called sendMessage would pass the check above.
    hit = {}
    try:
        globals()["send_photo"] = lambda t, c, path, cap, **k: (
            hit.update(photo=(path, cap)) or {"message_id": 1})
        globals()["send_video"] = lambda t, c, path, cap, **k: (
            hit.update(video=(path, cap)) or {"message_id": 2})
        seen["sweep_kw"]["photo_sender"]("a.jpg", "cap one")
        seen["vid_sender"]("b.mp4", "cap two")
    finally:
        globals()["send_photo"], globals()["send_video"] = real_photo, real_video
    check("accept/ruling5-the-photo-closure-calls-sendPhoto-not-sendMessage",
          hit.get("photo") == ("a.jpg", "cap one"), hit.get("photo"))
    check("accept/ruling1-the-video-closure-calls-sendVideo",
          hit.get("video") == ("b.mp4", "cap two"), hit.get("video"))

    # AND THE VIDEO WIRE ASKS THE PLATFORM FOR A VIDEO. The method name is
    # the whole difference between a clip that plays and a file to tap.
    posted = {}
    real_post = _post
    tmpclip = os.path.join(home, "clip.mp4")
    with open(tmpclip, "wb") as fh:
        fh.write(b"\x00\x00\x00\x18ftypmp42")
    try:
        globals()["_post"] = lambda tok, method, body, hdr, to: (
            posted.update(method=method, size=len(body)) or {"message_id": 3})
        real_video(_Creds.token, _Creds.chat_id, tmpclip, "one line")
    finally:
        globals()["_post"] = real_post
    check("accept/ruling1-the-wire-calls-sendVideo-with-the-bytes",
          posted.get("method") == "sendVideo" and posted.get("size", 0) > 8,
          posted)

    # AND THE PHOTO WIRE CAN CARRY BUTTONS, QUEUE 232. The body is read back
    # byte for byte rather than trusted to look right: `reply_markup` in a
    # multipart field is the whole of what makes the daily brief ONE message
    # with its picture and its pair, and a kwarg that silently went nowhere
    # would leave the picture arriving with no buttons on it.
    shot_posts = []
    tmpshot = os.path.join(home, "one.jpg")
    with open(tmpshot, "wb") as fh:
        fh.write(b"\xff\xd8\xff\xe0 bytes")
    try:
        globals()["_post"] = lambda tok, method, body, hdr, to: (
            shot_posts.append((method, body))
            or {"message_id": 4, "photo": [{"width": 1, "height": 1}]})
        real_photo(_Creds.token, _Creds.chat_id, tmpshot, "one caption",
                   markup=brief.keyboard("2026-09-10"))
        real_photo(_Creds.token, _Creds.chat_id, tmpshot, "one caption")
    finally:
        globals()["_post"] = real_post
    # THE PAIRED READING: the same wire called with the keyboard and without
    # it, both bodies read back, so "it carries buttons" cannot be satisfied
    # by a field that was always there or by one that is never there.
    with_markup = shot_posts[0][1] if len(shot_posts) == 2 else b""
    without_markup = shot_posts[1][1] if len(shot_posts) == 2 else b""
    check("accept/queue232-the-photo-wire-posts-the-keyboard-with-the-bytes",
          len(shot_posts) == 2
          and [m for m, _b in shot_posts] == ["sendPhoto", "sendPhoto"]
          and b"name=\"reply_markup\"" in with_markup
          and b"b|2026-09-10|R" in with_markup
          and b"b|2026-09-10|U" in with_markup
          and b"name=\"photo\"" in with_markup
          and b"name=\"reply_markup\"" not in without_markup,
          str((len(shot_posts), len(with_markup), len(without_markup))))

    # AND A GIF TAKES THE OTHER METHOD. Both arms are asserted because a
    # router with one arm tested is a router nobody has tested: a GIF handed
    # to sendVideo is delivered as a file to tap, not a clip that plays,
    # which is the whole outcome ruling 1 exists to produce.
    real_anim = send_animation
    routed = {}
    try:
        globals()["send_video"] = lambda t, c, path, cap, **k: (
            routed.update(m="sendVideo") or {"message_id": 4})
        globals()["send_animation"] = lambda t, c, path, cap, **k: (
            routed.update(m="sendAnimation") or {"message_id": 5})
        seen["vid_sender"]("walk.gif", "cap")
        gif_went = routed.get("m")
        seen["vid_sender"]("walk.mp4", "cap")
        mp4_went = routed.get("m")
    finally:
        globals()["send_video"], globals()["send_animation"] = (real_video,
                                                                real_anim)
    check("accept/ruling1-a-gif-is-routed-to-sendAnimation",
          gif_went == "sendAnimation", gif_went)
    sweep_routed = {}
    try:
        globals()["send_video"] = lambda t, c, path, cap, **k: (
            sweep_routed.update(m="sendVideo") or {"message_id": 7})
        globals()["send_animation"] = lambda t, c, path, cap, **k: (
            sweep_routed.update(m="sendAnimation") or {"message_id": 8})
        seen["sweep_kw"]["video_sender"]("walk.gif", "cap")
    finally:
        globals()["send_video"], globals()["send_animation"] = (real_video,
                                                                real_anim)
    check("accept/ruling1-the-sweeps-own-closure-routes-a-gif-as-well",
          sweep_routed.get("m") == "sendAnimation", sweep_routed)

    # A1, THE JOIN, AND IT IS THE ONLY ROW THAT PROVES THE FEATURE. Every
    # other row above would still pass with the sweep refusing every clip:
    # one asks whether a kwarg is callable, the other calls the closure by
    # hand. outbox.py's own suite proves sweep reaches a stub sender. NOBODY
    # PROVED THE TWO HALVES MEET, which is exactly how --send-clip came to
    # exist with nothing calling it. This drives a real message with a real
    # clip sidecar all the way through outbox_pass to the wire.
    joined = {}
    gif_rel = "production/d1-probe/selftest-join.gif"
    gif_abs = os.path.join(watcher, *gif_rel.split("/"))
    os.makedirs(os.path.dirname(gif_abs), exist_ok=True)
    with open(gif_abs, "wb") as fh:
        fh.write(b"GIF89a" + b"\x00" * 64)
    # THE REGISTER MUST BE PRESENT IN THE FIXTURE OR THE SWEEP REFUSES
    # before it ever reaches the clip branch, which would make this row pass
    # for the wrong reason later if the refusal were ever ignored. Copied in
    # rather than stubbed, so the message really is checked.
    # capsay.py rides along because producer-check imports it and REFUSES to
    # print a finding list without it, which is the right instinct and would
    # otherwise make this row fail for a reason that has nothing to do with
    # clips.
    for _name in ("producer-check.py", "capsay.py"):
        _dst = os.path.join(watcher, "tools", _name)
        os.makedirs(os.path.dirname(_dst), exist_ok=True)
        with open(os.path.join(REPO, "tools", _name), "rb") as _a, \
                open(_dst, "wb") as _b:
            _b.write(_a.read())
    join_rel = "production/outbox/2026-09-07-join.answer.md"
    join_abs = os.path.join(watcher, *join_rel.split("/"))
    os.makedirs(os.path.dirname(join_abs), exist_ok=True)
    with open(join_abs, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("The street walks.\n\n"
                 "[the map](https://jsab258.github.io/wc26-picks/map.html)\n")
    with open(join_abs[:-3] + ".photo.txt", "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write("clip: %s\n" % gif_rel)
    try:
        globals()["send_animation"] = lambda t, c, path, cap, **k: (
            joined.update(path=path, caption=cap) or
            {"message_id": 9001, "animation": {"file_id": "x"}})
        globals()["send_video"] = lambda t, c, path, cap, **k: (
            joined.update(wrongWire="sendVideo") or {"message_id": 9002})
        res_join = outbox_pass(_Creds(), watcher, lambda _s: None)
    finally:
        globals()["send_animation"], globals()["send_video"] = (real_anim,
                                                                real_video)
    check("accept/ruling1-a-clip-message-reaches-sendAnimation-through-outbox_pass",
          joined.get("path", "").endswith("selftest-join.gif")
          and "wrongWire" not in joined
          and joined.get("caption", "").startswith("The street walks"),
          "%s / refused=%s" % (joined, (res_join or {}).get("refused")))
    check("reject/ruling1-and-a-non-gif-is-not",
          mp4_went == "sendVideo", mp4_went)

    posted2 = {}
    tmpgif = os.path.join(home, "clip.gif")
    with open(tmpgif, "wb") as fh:
        fh.write(b"GIF89a" + b"\x00" * 16)
    try:
        globals()["_post"] = lambda tok, method, body, hdr, to: (
            posted2.update(method=method, size=len(body)) or {"message_id": 6})
        real_anim(_Creds.token, _Creds.chat_id, tmpgif, "one line")
    finally:
        globals()["_post"] = real_post
    check("accept/ruling1-the-animation-wire-calls-sendAnimation",
          posted2.get("method") == "sendAnimation"
          and posted2.get("size", 0) > 16, posted2)

    # ---- A BROKEN POLL MUST NOT STOP THE OFFLINE HALF -----------------
    # THIS ROW IS THE ONE THAT WOULD HAVE CAUGHT THE 2026-09-08 FAULT, and it
    # did not exist because every earlier row asked whether a wire was
    # connected, never whether the work still happened when the wire failed.
    # On his PC the bot sent its two startup messages, then getUpdates raised
    # on every pass for thirteen hours, and flush_inbox and sweep_outbox sat
    # inside the try AFTER it, so neither ever ran. Uptime climbed, the
    # supervisor reported it running, receipts piled up on disk, and nothing
    # moved.
    ran = {"flush": 0, "sweep": 0, "cards": 0}
    bP = Captured()
    bP.flush_inbox = lambda every=60: ran.__setitem__("flush", ran["flush"] + 1)
    bP.sweep_outbox = lambda every=120: ran.__setitem__("sweep", ran["sweep"] + 1)
    # AND THE CARDS COUNTER IS HERE TO PROVE THE OPPOSITE OF WHAT IT PROVED
    # THIS MORNING. It was added at about 10:00 on 2026-09-09 to show the card
    # sender finally had a caller; Jafar retired that pass the same day, so
    # this stub now exists to catch the loop calling it AGAIN. If this counter
    # ever moves, the retirement leaked.
    bP.sweep_cards = lambda every=None: ran.__setitem__("cards",
                                                        ran["cards"] + 1)

    class _Enough(Exception):
        pass

    def _boom(*_a, **_k):
        raise ApiError("network", "planted: the poll cannot reach Telegram")

    def _one_pass(_sec):
        raise _Enough()

    real_call2, real_sleep = call, time.sleep
    try:
        globals()["call"] = _boom
        time.sleep = _one_pass
        try:
            bP.poll_forever()
        except _Enough:
            pass
    finally:
        globals()["call"] = real_call2
        time.sleep = real_sleep

    check("accept/a-failing-poll-still-flushes-and-sweeps",
          ran["flush"] == 1 and ran["sweep"] == 1, ran)
    check("reject/the-loop-no-longer-sweeps-the-retired-cards",
          ran["cards"] == 0, str(ran))
    # AND THE RETIREMENT IS MECHANICAL AND NOT A COMMENT: the method raises,
    # so a caller somebody adds next month stops instead of sending.
    retired_note = None
    try:
        Captured().sweep_cards(every=0)
    except cards.SendingRetired as e:
        retired_note = str(e)
    check("reject/and-the-card-sweep-itself-refuses-to-run",
          retired_note is not None and "RETIRED" in retired_note
          and "--send-brief" in retired_note,
          (retired_note or "IT STILL RUNS")[:80])
    check("accept/and-the-poll-failure-was-real-not-a-vacuous-pass",
          bP.net_errors == 1, "netErrors=%d" % bP.net_errors)

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

    # THE MESSAGE BODY IS THE ONE THAT CANNOT DECAY, `outbox.fixture_message`.
    # It was producer-check's GOOD sample, whose deadline is an absolute date;
    # this door runs the SINGLE-FILE check, which measures deadlines from the
    # wall clock by ruling, so the sample crossed the 24-hour floor at
    # 2026-09-06T09:00 and read 23.6, 23.5 and 23.3 hours over the following
    # seventeen minutes. The accepting case below went red, and then the two
    # rejecting cases after it, with nobody having touched the tree. The
    # floor is untouched and is still proven live, on this same subprocess
    # check, by outbox.py's own case
    # reject/a-deadline-under-the-ruled-floor-is-not-sent.
    pc_repo = outbox._fixture_repo(os.path.join(home, "sendfile"))
    good_body = outbox.fixture_message(outbox._load_producer_check())
    good_rel = "%s/2026-09-05-good.unprompted.md" % outbox.OUTBOX_DIR
    outbox._commit(pc_repo, good_rel, good_body)
    posted = []
    rc, why = send_file_checked(pc_repo, good_rel,
                                lambda t: posted.append(t) or
                                {"message_id": 77}, say=lambda _s: None)
    check("accept/a-checked-producer-file-is-sent", rc == 0 and not why
          and len(posted) == 1, "rc=%d posted=%d %s" % (rc, len(posted), why))
    # EACH REJECTING CASE COUNTS ITS OWN SENDS, before against after, and not
    # the running total. The total was `len(posted) == 1`, which is the
    # ACCEPTING case's side effect: when that case broke, these two reported
    # failures of their own that were nothing of the kind, and one decayed
    # fixture read as three faults in three different rules.
    long_rel = "%s/2026-09-05-too-long.unprompted.md" % outbox.OUTBOX_DIR
    outbox._commit(pc_repo, long_rel, good_body + ("\nword " * 200))
    was = len(posted)
    rc, why = send_file_checked(pc_repo, long_rel,
                                lambda t: posted.append(t) or
                                {"message_id": 78}, say=lambda _s: None)
    check("reject/an-over-cap-file-is-refused-and-not-sent",
          rc == 1 and len(posted) == was and "wordcap" in why,
          "rc=%d posted=%d..%d %s" % (rc, was, len(posted), why))
    was = len(posted)
    rc, why = send_file_checked(pc_repo, "production/outbox/no-kind.md",
                                lambda t: posted.append(t), say=lambda _s: None)
    check("reject/a-file-with-no-register-in-its-name-is-refused",
          rc == 2 and len(posted) == was and ".unprompted.md" in why
          and ".answer.md" in why and ".brief.md" in why,
          "rc=%d posted=%d..%d %s" % (rc, was, len(posted), why))
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

    # ---- AND THE COUNTER LEAVES THE PROCESS, ruled 2026-09-08 -----------
    # The three counters above have existed since queue 089 and went to a
    # console on his desk. ACCEPTING CASE FIRST: after the pass above, the
    # file the supervisor publishes exists and carries the number.
    sweep_file = os.path.join(b6.repo, *Bot.SWEEP_STATUS_REL.split("/"))
    swept = open(sweep_file, encoding="utf-8").read() if \
        os.path.exists(sweep_file) else ""
    check("accept/the-sweep-counter-reaches-the-file-the-supervisor-reads",
          "botSweepPasses=1" in swept and "botSweepWrittenAt=" in swept
          and "botSweepLastResult=" in swept, swept.replace("\n", " ")[:150])
    # AND THE STATE THE RULING EXISTS TO TELL APART: a bot that started and
    # has NOT swept must publish a zero with a fresh timestamp, not nothing,
    # so "the loop never runs" and "the loop runs and sends nothing" are
    # different readings rather than one silence.
    b7 = Captured()
    b7.creds = creds
    fresh = os.path.join(b7.repo, *Bot.SWEEP_STATUS_REL.split("/"))
    zero = open(fresh, encoding="utf-8").read() if os.path.exists(fresh) \
        else ""
    check("accept/a-bot-that-has-not-swept-yet-publishes-zero-not-silence",
          "botSweepPasses=0" in zero
          and "botSweepLastResult=no-pass-yet" in zero, zero.replace("\n", " ")[:150])

    # AND THE EXCEPTION PATH, PLANTED (rule 5b): a sweep that raises is
    # still a pass that happened, and the file must say so rather than
    # freezing on the last good number.
    b8 = Captured()
    b8.creds = creds
    real_pass = outbox_pass
    try:
        globals()["outbox_pass"] = (lambda *a, **k: (_ for _ in ()).throw(
            RuntimeError("planted")))
        b8.sweep_outbox(every=0)
    finally:
        globals()["outbox_pass"] = real_pass
    b8fresh = os.path.join(b8.repo, *Bot.SWEEP_STATUS_REL.split("/"))
    raised = open(b8fresh, encoding="utf-8").read() \
        if os.path.exists(b8fresh) else ""
    check("accept/a-sweep-that-raised-still-counts-and-names-the-raise",
          b8.out_passes == 1 and "botSweepPasses=1" in raised
          and "botSweepLastResult=raised/RuntimeError" in raised,
          raised.replace("\n", " ")[:150])

    # ---- THE BRIEF PASS, END TO END, AGAINST THE FIXTURE REPOSITORY -----
    # THE WIRING ROW, AND IT REPLACES THE CARD PASS'S. `brief.py --selftest`
    # proves the arithmetic, the two buttons, the streak and every refusal;
    # this proves that `brief_pass` reads the file on disk, runs the register
    # check on the sending side, hands the text and the keyboard to a sender,
    # writes the receipt into production/outbound and counts the pass. `send`
    # is swapped for a stand-in returning what Telegram's own payload looks
    # like, so nothing here touches the network; `inbox.push_pending` and
    # `outbox.run_check` are stubbed because the transport and the register
    # each have their own suite.
    day = "2026-09-10"
    brief_rel = os.path.join(b8.repo, *brief.brief_rel(day).split("/"))
    os.makedirs(os.path.dirname(brief_rel), exist_ok=True)
    brief_body = ("HEADLINE: The street is standing in the rain.\n\n"
                  "WHAT CHANGED: You can see it from the corner now.\n")
    with open(brief_rel, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(brief_body)
    b9 = Captured()
    b9.creds = creds
    wired, pushes, checked = [], [], []
    real_send, real_push2, real_check = send, inbox.push_pending, outbox.run_check
    try:
        globals()["send"] = lambda token, chat, text, markup=None: (
            wired.append((text, markup)) or {"message_id": 900 + len(wired)})
        inbox.push_pending = lambda repo, say=None, **k: (
            pushes.append(repo) or {"ok": True, "pushed": [], "pending": [],
                                    "commit": "c" * 40, "replaced": False,
                                    "detail": "stubbed in the selftest",
                                    "plain": ""})
        outbox.run_check = lambda repo, kind, rel, timeout=120: (
            checked.append((kind, rel)) or (True, "", "stubbed"))
        first = brief_pass(creds, b9.repo, lambda _s: None, day)
        second = brief_pass(creds, b9.repo, lambda _s: None, day)
        missing = brief_pass(creds, b9.repo, lambda _s: None, "2026-09-11")
    finally:
        globals()["send"] = real_send
        inbox.push_pending = real_push2
        outbox.run_check = real_check

    check("accept/the-brief-pass-sends-his-words-with-two-buttons",
          len(wired) == 1 and wired[0][0] == brief_body.strip()
          and [b[0]["text"] for b in wired[0][1]["inline_keyboard"]]
          == ["Readable", "Unreadable"]
          and first["messageId"] == 901,
          str([w[0][:40] for w in wired]))
    check("accept/and-the-register-check-ran-on-that-file-before-the-send",
          checked == [("brief", brief.brief_rel(day))], str(checked))
    brief_receipts = [n for n in os.listdir(
        os.path.join(b9.repo, *outbox.OUTBOUND_DIR.split("/")))
        if n.startswith("brief-") and n.endswith(".receipt.txt")]
    check("accept/the-receipt-is-written-where-the-studio-reads-it",
          brief_receipts == ["brief-%s.receipt.txt" % day]
          and len(pushes) == 1, str(brief_receipts))
    check("reject/the-second-pass-sends-nothing-and-says-already",
          len(wired) == 1 and second["sent"] is None and second["already"]
          and "briefSent=0/1" in brief.brief_done_line(second),
          brief.brief_done_line(second))
    check("reject/a-day-with-no-brief-is-nothing-measured-not-a-send",
          missing.get("missing") is True and missing["sent"] is None
          and len(wired) == 1, brief.brief_done_line(missing))

    # ---- THE SAME PASS CARRYING ITS PICTURE, QUEUE 232 -------------------
    # THE WIRING ROW FOR THE HALF THAT WAS MISSING. `brief.py --selftest`
    # proves the decision, the counts and the strings; this proves that
    # `brief_pass` finds the day's sidecar on disk, reaches `sendPhoto` AND
    # NOT `sendMessage`, puts the same two buttons on that one call, and
    # writes the receipt that names both halves. Two days: one whose picture
    # is there, one whose picture is named and absent, because the second is
    # the case that must still send the message with its buttons.
    pday, gday = "2026-09-12", "2026-09-13"
    shot_rel = "game-design/sim-shots/brief_%s.jpg" % pday
    shot_full = os.path.join(b9.repo, *shot_rel.split("/"))
    os.makedirs(os.path.dirname(shot_full), exist_ok=True)
    with open(shot_full, "wb") as fh:
        fh.write(b"\xff\xd8\xff\xe0 not a real jpeg, only bytes with a size")
    for d, ref in ((pday, shot_rel),
                   (gday, "game-design/sim-shots/brief_never_rendered.jpg")):
        with open(os.path.join(b9.repo, *brief.brief_rel(d).split("/")), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(brief_body)
        with open(os.path.join(b9.repo,
                               *brief.brief_photo_ref_rel(d).split("/")), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write("photo: %s\n" % ref)
    shots, texts = [], []
    real_send4, real_photo4 = send, send_photo
    real_push4, real_check4 = inbox.push_pending, outbox.run_check
    try:
        globals()["send"] = lambda token, chat, text, markup=None: (
            texts.append((text, markup)) or {"message_id": 950})
        globals()["send_photo"] = lambda token, chat, path, caption, **k: (
            shots.append((path, caption, k.get("markup")))
            or {"message_id": 960, "photo": [{"width": 90, "height": 51},
                                             {"width": 1280, "height": 720}]})
        inbox.push_pending = lambda repo, say=None, **k: {
            "ok": True, "pushed": [], "pending": [], "commit": "e" * 40,
            "replaced": False, "detail": "stubbed", "plain": ""}
        outbox.run_check = lambda repo, kind, rel, timeout=120: (True, "",
                                                                "stubbed")
        carried = brief_pass(creds, b9.repo, lambda _s: None, pday)
        dropped = brief_pass(creds, b9.repo, lambda _s: None, gday)
    finally:
        globals()["send"], globals()["send_photo"] = real_send4, real_photo4
        inbox.push_pending, outbox.run_check = real_push4, real_check4

    # ONE CALL PER DAY AND THE DAY IS IN THE BUTTONS, which is what tells the
    # two passes apart here: both days carry the same body, so the day inside
    # `callback_data` is the only thing that says which wire each went down.
    # The carried day must appear on the PHOTO call and nowhere else.
    shot_days = [str((s[2] or {}).get("inline_keyboard")) for s in shots]
    text_days = [str((t[1] or {}).get("inline_keyboard")) for t in texts]
    check("accept/the-brief-pass-reaches-sendPhoto-with-the-two-buttons-on-it",
          len(shots) == 1
          and shots[0][0] == shot_full
          and shots[0][1] == brief_body.strip()
          and [b[0]["text"] for b in
               (shots[0][2] or {}).get("inline_keyboard", [])]
          == ["Readable", "Unreadable"]
          and ("b|%s|R" % pday) in shot_days[0]
          and not any(("b|%s|" % pday) in t for t in text_days)
          and carried["messageId"] == 960
          and carried["photoArrived"] is True,
          str((len(shots), len(texts), shot_days, text_days)))
    carried_rec = open(os.path.join(
        b9.repo, *outbox.receipt_rel(brief.brief_slot(pday)).split("/")),
        encoding="utf-8").read()
    check("accept/and-that-receipt-on-disk-names-the-image-and-the-pair",
          "receipt: sent-with-photo" in carried_rec
          and ("photoRef: %s" % shot_rel) in carried_rec
          and "photoSizes: 90x51/1280x720" in carried_rec
          and "buttons: 2/2" in carried_rec
          and "kind: brief" in carried_rec,
          carried_rec.replace("\n", " "))
    check("drop/a-named-picture-that-is-absent-still-sends-with-its-buttons",
          len(shots) == 1 and len(texts) == 1
          and ("b|%s|R" % gday) in text_days[0]
          and texts[0][0] == brief_body.strip()
          and [b[0]["text"] for b in texts[0][1]["inline_keyboard"]]
          == ["Readable", "Unreadable"]
          and dropped["sent"] == brief.brief_rel(gday)
          and dropped["photoState"] == "file-unusable"
          and "briefPhotoCarried=0/1" in brief.brief_done_line(dropped),
          brief.brief_done_line(dropped))
    dropped_rec = open(os.path.join(
        b9.repo, *outbox.receipt_rel(brief.brief_slot(gday)).split("/")),
        encoding="utf-8").read()
    check("drop/and-its-receipt-says-in-words-why-no-picture-rode",
          "receipt: sent\n" in dropped_rec and "buttons: 2/2" in dropped_rec
          and "photoNote: the picture did not ride" in dropped_rec
          and "file-unusable" in dropped_rec
          and "photoSizes" not in dropped_rec,
          dropped_rec.replace("\n", " "))
    # AND BOTH DAYS COUNT IN THE DENOMINATOR THE ACCEPTANCE IS READ OVER.
    outbound_now = {}
    for n in sorted(os.listdir(os.path.join(b9.repo,
                                            *outbox.OUTBOUND_DIR.split("/")))):
        if n.startswith("brief-") and n.endswith(".receipt.txt"):
            outbound_now["%s/%s" % (outbox.OUTBOUND_DIR, n)] = open(
                os.path.join(b9.repo, *outbox.OUTBOUND_DIR.split("/"), n),
                encoding="utf-8").read()
    check("accept/a-captioned-brief-and-a-plain-one-both-count-as-sent",
          sorted(brief.sent_days_from_receipts(outbound_now))
          == [day, pday, gday] and len(outbound_now) == 3,
          sorted(brief.sent_days_from_receipts(outbound_now)))

    # AND THE CALLBACK THAT COMES BACK FROM THOSE BUTTONS IS A RECORD.
    tap_data = wired[0][1]["inline_keyboard"][1][0]["callback_data"]
    bT = Captured()
    bT.creds = creds
    taps_seen = []
    real_push3 = inbox.push_pending
    try:
        inbox.push_pending = lambda repo, say=None, **k: (
            taps_seen.append(repo) or {"ok": True, "pushed": [], "pending": [],
                                       "commit": "d" * 40, "replaced": False,
                                       "detail": "stubbed", "plain": ""})
        bT.handle(tap(tap_data, 8001))
        bT.handle(update("too many words about the studio", 8002))
    finally:
        inbox.push_pending = real_push3
    tapdir = os.path.join(bT.repo, *inbox.BRIEF_TAP_DIR.split("/"))
    written = sorted(os.listdir(tapdir)) if os.path.isdir(tapdir) else []
    check("accept/an-unreadable-tap-is-recorded-with-its-day-and-verdict",
          len(written) == 2 and bT.taps_brief == 1 and bT.reasons_filed == 1
          and all(inbox.BRIEF_TAP_RE.match(n) for n in written),
          str(written))
    tap_bodies = [open(os.path.join(tapdir, n), encoding="utf-8").read()
                  for n in written]
    check("accept/and-the-reason-he-typed-rides-with-it",
          any("verdict: unreadable" in t and "briefDay: %s" % day in t
              for t in tap_bodies)
          and any("record: reason" in t
                  and "too many words about the studio" in t
                  for t in tap_bodies), str([t[:40] for t in tap_bodies]))
    check("accept/the-tap-counters-reach-the-done-line-with-denominators",
          "briefTapsFiled=1/1" in bT.done_line()
          and "briefReasonsFiled=1" in bT.done_line()
          and "cardsSent" not in bT.done_line(), bT.done_line()[-120:])
    check("reject/and-a-second-message-is-not-filed-as-a-second-reason",
          bT.reason_wanted is None, str(bT.reason_wanted))

    # ---- --flush-inbox, ON THE CASE IT MUST PASS --------------------------
    # A DIRECTOR RECORDED, 2026-09-08, that this flag shipped with no case of
    # its own, so the suite's count was consistent with the whole branch never
    # having run. Rule 5b: the accepting case first. main() reaches the branch,
    # the branch calls inbox, and the zero path prints its DENOMINATOR rather
    # than the words "nothing measured", which is rule 3b: a flush that pushed
    # nothing because there was nothing to push is not an unmeasured flush.
    #
    # THE REAL REPO IS NEVER TOUCHED. inbox.pending_all and inbox.push_pending
    # are swapped for stubs and restored in a finally, so a case that fails
    # here cannot leave the module able to push from a later case.
    said = []
    real_say, real_pending, real_push = OUT.say, inbox.pending_all, inbox.push_pending
    try:
        OUT.say = lambda text="": said.append(text)
        inbox.pending_all = lambda repo: ([], "0" * 40)
        inbox.push_pending = lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("push_pending must not run when nothing is waiting"))
        rc_zero = main(["telegram-bot.py", "--flush-inbox"])
        zero_line = next((l for l in said if l.startswith("flush done:")), "")
        check("accept/flush-inbox-is-reached-from-main-and-returns-clean",
              rc_zero == 0 and any(l.startswith("flush: waiting=0") for l in said),
              "rc=%d said=%r" % (rc_zero, said[:2]))
        check("accept/flush-inbox-zero-carries-its-denominator-not-nothing-measured",
              "pushed=0/0" in zero_line and "tracked=" in zero_line
              and "nothing measured" not in zero_line, zero_line or "NO DONE LINE")

        # AND THE OTHER HALF: with something waiting, push_pending IS called
        # and its result reaches the done line. Without this the case above
        # would pass on a branch that could never push anything at all.
        said[:] = []
        waiting = ["production/inbox/a.md", "production/outbound/b.receipt.txt"]
        called = []
        inbox.pending_all = lambda repo: (list(waiting), "a" * 40)
        inbox.push_pending = lambda repo, say=None, **k: (
            called.append(repo) or {"ok": True, "pushed": list(waiting),
                                    "pending": [], "commit": "b" * 40,
                                    "replaced": False,
                                    "detail": "pushed 2 file(s)", "plain": ""})
        rc_work = main(["telegram-bot.py", "--flush-inbox"])
        work_line = next((l for l in said if l.startswith("flush done:")), "")
        check("accept/flush-inbox-actually-calls-the-push-when-work-waits",
              rc_work == 0 and len(called) == 1 and "pushed=2/2" in work_line,
              "rc=%d calls=%d %s" % (rc_work, len(called), work_line))
        check("accept/flush-inbox-names-each-waiting-file",
              sum(1 for l in said if l.startswith("flush: waiting p")) == 2,
              [l for l in said if l.startswith("flush: waiting")])

        # THE REJECTING HALF: a refused push must not report success.
        said[:] = []
        inbox.push_pending = lambda repo, say=None, **k: {
            "ok": False, "pushed": [], "pending": list(waiting), "commit": None,
            "replaced": False, "detail": "the push failed (no such remote)",
            "plain": "the upload to the studio failed"}
        rc_bad = main(["telegram-bot.py", "--flush-inbox"])
        bad_line = next((l for l in said if l.startswith("flush done:")), "")
        check("reject/a-refused-flush-exits-nonzero-and-says-so",
              rc_bad == 1 and "ok=False" in bad_line
              and "pushed=0/2" in bad_line, "rc=%d %s" % (rc_bad, bad_line))
    finally:
        OUT.say, inbox.pending_all, inbox.push_pending = (
            real_say, real_pending, real_push)


def selftest():
    """The whole suite, and it REPORTS ON EVERY PATH.

    Exit 0 every case passed, 3 a case failed (here or in the config reader),
    4 the suite itself raised. `outbox.run_selftest` prints the count line
    before this function sees the code, so a crash still reaches
    ledger/verify.py as numbers plus a distinct exit rather than as no line.
    The config reader runs either way: a crash in the cases above is no reason
    to measure nothing here.
    """
    code, ok, bad, state = outbox.run_selftest(
        "telegram-bot", _selftest_cases,
        "THE NETWORK HALF IS NOT COVERED: every Telegram call in this file "
        "is unverifiable until it runs on the PC.")
    print("fixture: %s"
          % (state["fixture"] if state.get("fixture")
             else "nothing measured, the suite ended before one was made"))
    print("now the config reader:\n")
    rc = botconfig._selftest()
    if rc and code == outbox.SELFTEST_OK:
        code = outbox.SELFTEST_FAILED
    print("telegram-bot selftest exit=%d meaning=%s casesRun=%d "
          "casesFailed=%d configReaderExit=%d"
          % (code, outbox.SELFTEST_MEANING[code], len(ok) + len(bad), len(bad),
             rc))
    return code


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
        # RETIRED 2026-09-09. NO CREDENTIALS ARE LOADED AND NOTHING IS SENT.
        # Exit 5 rather than 0 or 1, so a caller that still exists anywhere
        # shows up as its own red rather than as a working pass or a crash.
        OUT.say("--send-cards: %s" % cards.RETIREMENT)
        OUT.say("--send-cards: nothing was read, nothing was sent, 0 card(s) "
                "left this machine.")
        return 5
    if "--send-brief" in args:
        # THE ONE MESSAGE A DAY. An optional day after the flag, so a brief
        # can be sent for a named date; without it, today in UTC, which is the
        # clock every record in production/outbound is stamped with.
        creds = load_or_explain()
        if creds is None:
            return 1
        i = args.index("--send-brief")
        day = args[i + 1] if i + 1 < len(args) \
            and not args[i + 1].startswith("--") else None
        res = brief_pass(creds, day=day)
        # THREE OUTCOMES, THREE CODES, so the step that runs this cannot read
        # "there was no brief today" as "the brief went". 0 sent or already
        # sent, 1 refused or held, 6 nothing to send.
        if res.get("missing"):
            return 6
        return 1 if res.get("refused") else 0
    if "--send-clip" in args:
        creds = load_or_explain()
        if creds is None:
            return 1
        i = args.index("--send-clip")
        clip = args[i + 1] if i + 1 < len(args) \
            and not args[i + 1].startswith("--") else None
        cap = "Clip from the last run."
        if "--caption" in args:
            j = args.index("--caption")
            if j + 1 < len(args):
                cap = args[j + 1]
        res = video_pass(creds, clip, cap)
        return 1 if (res["refused"] or res["failed"]) else 0
    if "--flush-inbox" in args:
        # THE RETURN HALF, ON DEMAND. The bot pushes his messages and its own
        # receipts back to pc-inbox once a minute, and when that stops the
        # studio goes blind whether or not the sending half works. From
        # 2026-09-07 11:30 UTC both halves were silent; from the 01:18 UTC
        # restart on the 8th the sending half worked and this one still did
        # not, which is why the studio kept calling the channel dead after it
        # was sending. No credentials are loaded here. Nothing is sent.
        waiting, tip = inbox.pending_all(REPO)
        OUT.say("flush: waiting=%d tip=%s"
                % (len(waiting), (tip or "none")[:7]))
        for rel in waiting[:8]:
            OUT.say("flush: waiting %s" % rel)
        if len(waiting) > 8:
            OUT.say("flush: (+%d more not shown)" % (len(waiting) - 8))
        if not waiting:
            OUT.say("flush done: pushed=0/0 waiting=0 tracked=%d, the "
                    "branch already carries every file on this disk"
                    % len(inbox.tracked_files(REPO)))
            return 0
        res = inbox.push_pending(REPO, OUT.say)
        OUT.say("flush done: pushed=%d/%d ok=%s commit=%s replaced=%s "
                "plain=%s detail=%s"
                % (len(res["pushed"]), len(waiting), res["ok"],
                   (res["commit"] or "none")[:7], res["replaced"],
                   (res["plain"] or "none").replace(" ", "~"),
                   (res["detail"] or "none").replace(" ", "~")))
        return 0 if res["ok"] else 1
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
