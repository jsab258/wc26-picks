#!/usr/bin/env python3
"""The studio's Telegram channel, running on Jafar's PC. Standard library only.

    START THE TELEGRAM BOT.bat                 what Jafar double-clicks
    python3 tools/runner/telegram-bot.py       the same thing, from a shell
    python3 tools/runner/telegram-bot.py --send "text"    one unprompted push
    python3 tools/runner/telegram-bot.py --selftest       offline, no network

WHAT IT DOES TODAY, and the list is short on purpose (queue 067, narrowed to
one builder pass): it starts and keeps running, it reads the credentials out
of tools/runner/config.local, it answers anything Jafar types, it PUSHES a
message he did not ask for, and it asks for the budget reading with numeric
quick-replies for BOTH meters. Gallery images, decision cards that write
rulings, notes and voice memos are Monday's work and are deliberately absent
rather than half-present.

AND SINCE QUEUE 088, THE INBOUND HALF: every message he types that is not a
command is written to `production/inbox/` and pushed to the `pc-inbox`
branch, and the reply says whether the studio is awake and, if it is asleep,
when it next wakes. The transport is `tools/runner/inbox.py` and every rule
it obeys about not disturbing `tools/pc-watcher.py` is in that file's
docstring. A push that fails keeps the message on this PC and retries; it is
never dropped.
A message that arrives while this bot is NOT running is the other case:
`skip_backlog` counts it at the next start and does not file it, so it is
lost to the inbox until the fold in queue 090's pass lands.

NO DEPENDENCY. The Telegram bot API is HTTP with JSON, and urllib does it, so
nothing new enters the licence allowlist for this.

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
import inbox                                                  # noqa: E402

API = "https://api.telegram.org/bot%s/%s"

#: THE CEILING IS NOT INVENTED HERE. 80 percent is the number
#: production/NOW.md carries as the spend ceiling, and the rule that goes with
#: it is that the HIGHER of the two meters governs, which is why this asks for
#: both rather than one. If Jafar moves the ceiling, this constant moves with
#: the document and not before it.
CEILING_PCT = 80

#: The quick-reply grid. It spans 0 to 100 because the first run is on Monday
#: just after the reset, when the honest reading is near zero, and a keyboard
#: that only offered the crowded end would have forced typing on its first
#: use. He can still type any number, including a decimal.
BUDGET_KEYS = [["0", "5", "10", "20"],
               ["30", "40", "50", "60"],
               ["70", "75", "80", "85"],
               ["90", "95", "100"]]

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
def call(token, method, params, timeout=40):
    """One API call. Raises ApiError with a kind and a message that never
    contains the URL, because the URL contains the token."""
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(API % (token, method), data=data)
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


def send(token, chat_id, text, keyboard=None):
    params = {"chat_id": chat_id, "text": text,
              "disable_web_page_preview": "true"}
    if keyboard is not None:
        params["reply_markup"] = json.dumps({
            "keyboard": keyboard, "one_time_keyboard": True,
            "resize_keyboard": True,
            "input_field_placeholder": "or type the exact number"})
    return call(token, "sendMessage", params)


# --------------------------------------------------------------------------
# The arithmetic and the strings, which live HERE because here is where the
# tests run (the instruments rule: an unrun formatter printing a plausible
# string is the silent-instrument failure).
# --------------------------------------------------------------------------
def parse_percent(text):
    """A percent reading, or None. Accepts 77, 77%, 77 percent, 76,5."""
    t = (text or "").strip().lower()
    for junk in ("percent", "per cent", "%"):
        t = t.replace(junk, "")
    t = t.replace(",", ".").strip()
    try:
        v = float(t)
    except ValueError:
        return None
    if v < 0 or v > 100:
        return None
    return v


def fmt_pct(v):
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
    line = ("budgetTotalPct=%s budgetFablePct=%s governing=%s "
            "governingPct=%s ceilingPct=%d headroomPct=%s"
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
        "/budget  the two meter readings, with buttons\n"
        "/ping    am I still alive\n"
        "/help    this\n\n"
        "Working today: anything you type that is not one of those commands "
        "is FILED for the studio, and I tell you whether the studio is awake "
        "and, if not, when it next wakes. I can also send you something you "
        "did not ask for.\n"
        "Not built yet: gallery pictures, decision cards with buttons that "
        "write the ruling, and voice memos.\n"
        "To stop me, close the black window on the PC.")

OPENING = ("LEDGER studio channel is open.\n"
           "You did not ask for this message, which is the part a Blocking "
           "item needs.\n"
           "Send me anything and I will file it for the studio and answer "
           "you, which proves the other direction. /help lists what works "
           "today.")

BUDGET_Q = ("Budget reading, please. Two numbers, and the studio needs both "
            "because the higher one governs.\n"
            "1 of 2: the TOTAL meter, percent used.")
BUDGET_Q2 = "2 of 2: the FABLE meter, percent used."


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
        self.readings = 0
        self.pending = None    # None, "total" or "fable"
        self.total = None
        self.started = time.time()
        # THE INBOX HALF. `repo` is a parameter so the selftest can point the
        # whole path at a throwaway repository instead of this one.
        self.repo = repo or REPO
        self.filed = 0         # messages written to production/inbox
        self.pushed = 0        # of those, that reached the branch
        self.push_fails = 0    # cumulative, whole run
        self.last_flush = 0.0  # when the retry last ran, a wall clock

    # -- startup ----------------------------------------------------------
    def hello(self):
        me = call(self.token, "getMe", {})
        name = "@" + str(me.get("username", "unknown"))
        OUT.say("connected to Telegram as %s" % name)
        return name

    def skip_backlog(self):
        """Anything sent before this run started is old news, and replying to
        it would be the bot shouting three days of history at him. Counted
        rather than silently dropped, so the number is visible."""
        try:
            updates = call(self.token, "getUpdates", {"timeout": 0}, timeout=30)
        except ApiError as e:
            if e.kind == "network":
                raise
            updates = []
        n = len(updates or [])
        if n:
            self.offset = updates[-1]["update_id"] + 1
        OUT.say("skipped %d message(s) that arrived before this run started "
                "(%d read, %d skipped)" % (n, n, n))
        return n

    # -- handling ---------------------------------------------------------
    def reply(self, text, keyboard=None):
        send(self.token, self.chat, text, keyboard)

    def ask_budget(self):
        self.pending = "total"
        self.total = None
        self.reply(BUDGET_Q, BUDGET_KEYS)
        OUT.say("asked for the budget reading, meter 1 of 2")

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
            v = parse_percent(text)
            if v is None:
                # HIS WORDS BACK ANYWAY. On the first run the budget question
                # is already open, so a plain hello would otherwise be met
                # with a demand and no proof that the channel carried what he
                # actually said. Both facts, one reply.
                #
                # AND IT IS FILED, because a message that is not a number is
                # a message for the studio and the open budget question is
                # not a reason to drop it. Filing first, nagging second.
                return self.reply(echo_reply(
                    text, "%s\nI am still waiting for the %s meter, a number "
                          "from 0 to 100: press a button, type it, or send "
                          "/help to stop being asked."
                          % (self.file_message(text, sent_epoch, update_id),
                             self.pending.upper())))
            if self.pending == "total":
                self.total = v
                self.pending = "fable"
                OUT.say("budget: total meter read")
                return self.reply(BUDGET_Q2, BUDGET_KEYS)
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

    def handle(self, update):
        self.seen += 1
        self.offset = update["update_id"] + 1
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
            return self.reply("I can only read typed text today. Photos, "
                              "voice memos and buttons that write rulings are "
                              "Monday's work.")
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
                "networkErrors=%d inboxFiled=%d inboxPushed=%d/%d "
                "inboxPushFailures=%d inboxPending=%s"
                % (int((time.time() - self.started) / 60), self.seen,
                   self.mine, self.seen, self.other, self.seen,
                   self.nontext, self.mine, self.readings, self.net_errors,
                   self.filed, self.pushed, self.filed, self.push_fails,
                   "unreadable" if waiting < 0 else waiting))


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

    check("accept/percent-77", parse_percent("77") == 77)
    check("accept/percent-with-sign", parse_percent(" 77% ") == 77)
    check("accept/percent-worded", parse_percent("77 percent") == 77)
    check("accept/percent-comma-decimal", parse_percent("76,5") == 76.5)
    check("reject/percent-over-100", parse_percent("101") is None)
    check("reject/percent-negative", parse_percent("-3") is None)
    check("reject/percent-words", parse_percent("about half") is None)
    check("reject/percent-empty", parse_percent("") is None)

    long_text = "x" * (REPLY_CAP + 25)
    r = echo_reply(long_text)
    check("accept/cap-announces-itself",
          "(+25 more character(s) not shown)" in r, r[-60:])
    check("accept/short-text-not-capped", "not shown" not in echo_reply("hi"))

    kb = json.loads(json.dumps({"keyboard": BUDGET_KEYS}))
    flat = [b for row in kb["keyboard"] for b in row]
    check("accept/keyboard-is-numeric-and-spans",
          len(flat) == 15 and flat[0] == "0" and flat[-1] == "100"
          and all(b.isdigit() for b in flat), "%d button(s)" % len(flat))

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

        def reply(self, text, keyboard=None):
            self.said.append(text)

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
    b4.pending, b4.total = "fable", 40.0
    b4.handle(update("62", 4132))
    check("reject/inbox-a-budget-answer-is-not-filed",
          b4.filed == 0 and "fable at 62" in b4.said[-1],
          b4.said[-1][:60] if b4.said else "SILENT")

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
        try:
            with open(args[i + 1], "r", encoding="utf-8") as fh:
                body = fh.read().strip()
        except OSError:
            OUT.say("could not read %s" % args[i + 1])
            return 1
        if not body:
            OUT.say("%s is empty, so there is nothing to send" % args[i + 1])
            return 1
        return run_send(body)
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
