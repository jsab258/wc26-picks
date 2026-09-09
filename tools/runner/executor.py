#!/usr/bin/env python3
"""THE THIRD DAEMON: a Telegram instruction becomes a real session, and the
answer comes back on Telegram.

    python3 tools/runner/executor.py             # the loop, started by the supervisor
    python3 tools/runner/executor.py --once      # one pass, then exit (debugging)
    python3 tools/runner/executor.py --selftest  # policy and wording only, no session

WHAT THIS CLOSES. Both ends of the Telegram loop were already built and
neither reached the middle. Inbound: the bot writes Jafar's message to
production/inbox/ and pushes it to pc-inbox. Outbound: the bot sweeps
production/outbox/, runs the register check and sends. What was missing is the
part that reads an instruction and DOES it: tools/runner/run-night.ps1 takes
its prompt from a static file (tools/runner/dispatch.md), never reads the
inbox, and nothing whatever starts it. So an instruction sent from a phone sat
in a folder for ever.

THE ROUTE, HOP BY HOP, so a failure names its own stage:

  1. Jafar types on Telegram.
  2. telegram-bot.py files it as production/inbox/<stamp>-<update>.md in THIS
     checkout (untracked here, which is what makes it survive the watcher's
     hard reset) and pushes it to the pc-inbox branch.
  3. THIS daemon, one directory away on the same PC, reads that folder off
     disk every POLL_SEC seconds. It does NOT fetch pc-inbox: the file is
     already local, and a fetch in this checkout is the FETCH_HEAD race
     tools/runner/inbox.py refuses to run for (pc-watcher.resync fetches and
     then reads FETCH_HEAD as two separate processes).
  4. It takes ONE unhandled instruction, oldest first, writes `taken` to the
     journal BEFORE starting anything, and runs `claude -p` in ITS OWN
     WORKTREE with a turn bound and a wall clock.
  5. The session's final message is composed into an answer file and checked
     against the answer register HERE, before it is placed anywhere.
  6. The answer file is written into this checkout's production/outbox/, where
     the bot's sweep finds it within its two minute rhythm, sends it, and
     writes a receipt under production/outbound/.
  7. The record commit (the journal AND every answer file this instruction
     delivered) plus whatever the session committed is pushed as
     exec/<stamp>-<update>, so the studio in the container can read what
     happened AND what he was told, without anybody being at the PC.

CHECKOUT OWNERSHIP, WHICH IS THE NAMED HAZARD AND NOT A TIDINESS POINT.
tools/pc-watcher.py hard-resets THIS checkout roughly once a minute. A coding
session writing here would have its work discarded mid-edit, and worse, a
`git fetch` here can land between the watcher's fetch and its `rev-parse
FETCH_HEAD` and reset Jafar's checkout onto the wrong tree. So:

  THIS CHECKOUT (the repository root)   owned by pc-watcher.py. This file
                                        READS production/inbox/ and production/
                                        STOP from it, and WRITES only
                                        UNTRACKED files into it: the answer in
                                        production/outbox/, a pause note under
                                        its OWN name beside it when a session
                                        limit stops the work part way (one name
                                        carries one message: `answer_name`),
                                        and the status mirror in
                                        game-design/pc-jobs/. It runs
                                        NO git here, ever, and `git_call`
                                        refuses by path if anyone tries.
  ../ledger-exec                        a linked git worktree, owned by this
                                        file alone. Every session runs here.
                                        Measured 2026-09-06 on git 2.43: a
                                        fetch in a linked worktree writes the
                                        worktree's own FETCH_HEAD and not the
                                        main one, so the race above cannot
                                        reach the watcher from here. Git also
                                        refuses to check out in a worktree a
                                        branch the main checkout holds, so the
                                        sessions stay on a detached head and
                                        push HEAD to a named branch.
  ../ledger-exec-state                  the journal and the lock, OUTSIDE both
                                        checkouts so that neither a hard reset
                                        nor a session's own `git clean` can
                                        reach the one record that says what
                                        already ran.
  the GitHub Actions runner             untouched. Nothing here looks at it.

WHY THIS IS PYTHON AND NOT A FLAG ON run-night.ps1. Every DECISION below can
be wrong in a way that reads as working: which instruction is next, whether a
crash resumes or repeats, whether an exit was a session limit or a fault, how
long to wait, what the answer says when nothing came back. There is no
PowerShell in the container this was written in, so a decision written there
ships UNRUN, which is the standing rule in .claude/rules/instruments.md about
measurement arithmetic living where the tests run. What run-night.ps1 actually
contributes to the invocation is one line, `claude -p <prompt> --max-turns N`,
and that line is reproduced here with the same shape. The rest of run-night
(the queue walk, the nightly branch, the dashboard, the brief) belongs to a
different job and is left alone.

WHAT HAS NEVER RUN WHERE IT WAS WRITTEN, said here rather than implied. There
is no `claude` CLI, no PowerShell and no Windows in this container. So the
session invocation, the process kill on timeout, the worktree creation and the
push have never executed anywhere. `--selftest` covers the policy, the
arithmetic and every string that reaches Jafar's phone, including running the
real register checker over the fallback wordings. The first double-click on
his PC is the accepting case for the rest, per rule 5b.

IT NEVER READS tools/runner/config.local. It does not send anything itself:
the bot is the only sender in this project, and this file reaches it by
leaving a file in the outbox exactly as the Producer does.
"""
import datetime
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import inbox                                                   # noqa: E402
import outbox                                                  # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))

# --------------------------------------------------------------------------
# THE POLICY NUMBERS. NONE OF THEM IS MEASURED, and rule 2 means saying so
# rather than implying otherwise: nobody has ever watched this loop run, so
# there is no series to set a bound from. Every one of them is chosen to bound
# damage, every one PRINTS itself when it bites, and the journal carries the
# reading so the numbers can be set from evidence after the first week.
# --------------------------------------------------------------------------
#: How often the inbox folder is read. A directory listing, no network.
POLL_SEC = 15

#: The wall clock on one session. When it bites, the answer is whatever the
#: session had already printed plus a plain sentence saying it stopped.
SESSION_WALL_SEC = 30 * 60

#: How often the wait on a running session wakes up. NOT a bound on anything:
#: it is what keeps the lock's heartbeat alive and the stop file read WHILE a
#: session runs. The session used to be one blocking wait of up to
#: SESSION_WALL_SEC, so for all but the first LOCK_STALE_SEC (135) of every
#: session the lock read as dead, a second double-click could take it, close
#: the running instruction as interrupted, tell him so and start a second
#: session in the same worktree. Any value comfortably under LOCK_STALE_SEC
#: does; 30 is the slice `sleep_through` already used.
SESSION_SLICE_SEC = 30

#: The turn bound, the same instrument run-night.ps1 uses (it passes 200 for a
#: whole night of queue work; this is one instruction, not a night).
SESSION_TURNS = 60

#: An instruction older than this at pickup is recorded and NOT run. It stops
#: a week of backlog stampeding through the machine after a long outage.
MAX_AGE_SEC = 24 * 3600

#: THE SESSION LIMIT LADDER, used only when the notice carries no reset time
#: we can parse. 30, 60, 120, 240 minutes and then 240 for ever.
LIMIT_BACKOFF_MIN = (30, 60, 120, 240)

#: How many times one instruction may be paused by a session limit before it
#: is given up on with a message. Without a cap, an account that never
#: refills would hold one instruction for ever and never say so.
LIMIT_MAX_PAUSES = 5

#: A parsed reset time is CLAMPED into this band. A misread timezone then
#: costs a few hours of lateness and can never produce an instant in the past
#: (a spin) or a wait measured in days (a silent stall).
LIMIT_SLEEP_MIN_SEC = 5 * 60
LIMIT_SLEEP_MAX_SEC = 6 * 3600

#: Attempts at the answer register: the first draft, then one repair pass
#: carrying the exact clause it was refused on. A third would cost more of the
#: allowance than the answer is worth; after two the fallback wording goes.
REGISTER_ATTEMPTS = 2

#: Telegram rejects a sendMessage over 4096 characters, and nothing in
#: outbox.sweep splits a long message: a refusal on the wire is a SendFailed,
#: which retries every two minutes for ever. So the cut happens HERE, with the
#: cut announced in the message itself.
TELEGRAM_TEXT_MAX = 4096
ANSWER_CHAR_CAP = 3800

#: How much of a session's output is kept for the journal when something goes
#: wrong. The cap announces itself wherever it is used.
TAIL_CHARS = 1200

#: A lock whose heartbeat is older than this is stale and is taken over. Two
#: executors would run two sessions on one worktree, which is the one thing
#: this daemon must never do.
LOCK_STALE_SEC = 5 * POLL_SEC + 60

#: THE EVIDENCE LINK. Same string as `tools/producer-check.py:SITE_ORIGIN`,
#: and the selftest reads that file and asserts the two agree rather than
#: trusting this copy: a drifted link would fail the link floor on every
#: answer this daemon ever writes.
SITE_LINK = "https://jsab258.github.io/wc26-picks/"

#: Where the worktree and the record live. Siblings of the repository, for the
#: ownership reasons in the module docstring. Named here so there is one place
#: to re-point and one comment saying why not to.
WORKTREE_DIR = os.path.join(os.path.dirname(REPO), "ledger-exec")
STATE_DIR = os.path.join(os.path.dirname(REPO), "ledger-exec-state")

#: The human-at-the-PC mirror, beside the supervisor's own status file, and
#: untracked for the same reason: the watcher's hard reset cannot delete it.
STATUS_REL = "game-design/pc-jobs/executor-status.txt"

#: The kill switch run-night.ps1 already honours. Same file, same meaning.
STOP_REL = "production/STOP"

#: Optional, absent in the normal case: one command line argument per line,
#: added to the `claude` invocation. It exists so that if the CLI on his PC
#: needs a flag nobody here can know about, the fix is a text file on that
#: machine rather than a round trip to change code.
CLI_ARGS_FILE = "claude-args.txt"

#: THE STOP-HOOK OPT-OUT (ruling 2026-09-09, section 8, A1). `.claude/
#: settings.json` travels with the repository, so the `claude -p` this daemon
#: runs drains THE SAME wake records as every other session in every checkout.
#: If the container's daily-brief record is due and undischarged at that
#: moment, which is the normal state for hours after an absorbed 04:09 wake,
#: this session's first Stop is BLOCKED and the model answering the question
#: Jafar sent from his phone is told to produce the day's brief instead: wrong
#: session, wrong work, his answer delayed or bent. `.claude/hooks/
#: wake-drain.sh` honours this variable, PERMITS, and prints
#: `reason=opted-out` with the count it did not block on, so the opt-out is
#: never silent. THE VALUE IS EXACT AND LOWER CASE: the parser is
#: `tools/wake-queue.py:is_opted_out`, which is deliberately strict because
#: this string turns a guard off, and `OFF` or `0` or `false` all block.
WAKE_DRAIN_ENV = "WAKE_DRAIN"
WAKE_DRAIN_OFF = "off"

#: The words rather than a blank, for a run where THIS process did not build
#: the child's environment (an injected spawn in the suite). Spelled here
#: rather than imported from `tools/capsay.py`, which owns the spelling: this
#: daemon starts on a PC where anything outside `tools/runner/` may be
#: missing, and an ImportError at start is a daemon that never runs at all.
NOTHING_MEASURED = "nothing-measured"

#: WHAT A SESSION LIMIT LOOKS LIKE, AND THIS LIST IS A GUESS. No session limit
#: has ever been observed from this CLI by anything in this repository, so
#: these are patterns to recognise, not a measurement. That is exactly why
#: `journal` records the raw first line of any non-zero exit: the first real
#: limit teaches the exact wording, and then this list is set from evidence
#: instead of from a guess.
LIMIT_PATTERNS = (
    ("usage-limit-reached", r"usage limit reached"),
    ("hour-limit-reached", r"\b(?:\d+|five|four)[\s-]hour limit reached"),
    ("limit-will-reset", r"\blimit will reset\b"),
    ("reached-your-limit", r"you(?:'ve| have)?\s*(?:reached|hit)\s+your\s+"
                           r"[\w\s]{0,30}limit"),
    ("out-of-allowance", r"\b(?:out of|no remaining)\s+"
                         r"(?:credit|credits|usage|allowance|quota)\b"),
    ("upgrade-to-continue", r"upgrade (?:your plan )?to continue"),
)

#: The words the answer register bans, in the form a session can obey. This is
#: a PROMPT, not the rule: `tools/producer-check.py:BANNED` is the rule. The
#: selftest asserts every word here is actually refused by that program, so
#: this list cannot drift into telling a session to avoid words that are fine
#: while missing words that are not.
PROMPT_BANNED_WORDS = ("commit", "branch", "repository", "workflow", "runner",
                       "dispatch", "verdict", "gate", "job", "selftest",
                       "grep", "pull request", "exit code")


# --------------------------------------------------------------------------
# Small pure helpers. Every one of these is tested.
# --------------------------------------------------------------------------
def oneword(value):
    """A value fit for a key=value line: no whitespace, ever.

    Every reader in this project splits on whitespace and truncates silently,
    so a Windows path with a space in it would otherwise cut a status line in
    half and the half that survived would look like a complete reading.
    """
    text = str(value)
    if not text:
        return "none"
    return "_".join(text.split())


def stamp(now=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ",
                         time.gmtime(now if now is not None else time.time()))


def cap_text(text, keep, what="character"):
    """Cut with the cut announced. A silent truncation is the instrument
    failure this project has already paid for twice."""
    text = text or ""
    if len(text) <= keep:
        return text
    return text[:keep] + ("\n(+%d more %s(s) not shown)"
                          % (len(text) - keep, what))


def tail_of(text, keep=TAIL_CHARS):
    text = (text or "").strip()
    if len(text) <= keep:
        return text
    return ("(+%d earlier character(s) not shown)\n" % (len(text) - keep)
            + text[-keep:])


def first_line(text, cap=200):
    """The first non-empty line, capped, as one word-safe line for a journal.

    This is what turns an unrecognised failure into evidence: the exact words
    the CLI used, kept where the next reader can set a pattern from them.
    """
    for line in (text or "").splitlines():
        if line.strip():
            return inbox.one_line(line.strip(), cap)
    return "it-printed-nothing"


def is_instruction(text):
    """(True, "") or (False, why-not). What is worth starting a session for.

    THE BOT ALREADY FILTERS MOST OF THIS. `/ping`, `/help`, `/start`,
    `/budget` and a budget reading that parses are answered in the bot and
    never filed, read out of `telegram-bot.py:handle_text` rather than
    assumed. This is the second line: a command the bot learns later, or an
    empty message, must not cost a whole session.
    """
    body = (text or "").strip()
    if not body:
        return False, "empty"
    if body.startswith("/"):
        return False, "a-command-the-bot-answers-itself"
    if len(body) < 3:
        return False, "shorter-than-three-characters"
    return True, ""


def answer_name(stem, tag=""):
    """The outbox name for ONE message about one instruction.

    ONE NAME CARRIES ONE MESSAGE, and the tag is the whole reason:
    `outbox.sweep` skips any file whose receipt already exists, and it names
    the receipt from the FILE NAME. So a pause note and the answer written to
    one name meant the pause note was sent, a receipt was written under that
    name, and THE ANSWER WAS NEVER SENT: he is told it starts again by itself
    and then never hears anything, on the exact path the limit handling exists
    for. `<stem>.answer.md` is therefore reserved for the message that ENDS an
    instruction, and anything sent before it takes `<stem>.<tag>.answer.md`.

    Both names still carry the register, because `outbox.kind_of_name` matches
    on the `.answer.md` suffix; and `outbox.record_base` reads the whole file
    name, so the two can never share a receipt.
    """
    if tag:
        return "%s.%s.answer.md" % (stem, oneword(tag))
    return "%s.answer.md" % stem


def outbox_rel(stem, tag=""):
    return "%s/%s" % (outbox.OUTBOX_DIR, answer_name(stem, tag))


def count_links(text):
    """(total URLs, URLs pointing at the site the register allows)."""
    urls = re.findall(r"https?://[^\s<>()\[\]]+", text or "")
    site = [u for u in urls if u.startswith(SITE_LINK.rstrip("/"))]
    return len(urls), len(site)


def compose_answer(session_text, cut_at=ANSWER_CHAR_CAP, note=""):
    """The message body, from what the session printed. PURE.

    THREE THINGS HAPPEN HERE AND ALL THREE ARE VISIBLE IN THE RESULT. The text
    is cut to something Telegram will accept, with the cut announced. A note
    (the timeout sentence, say) is appended. And the evidence link is added
    when the text carries none, because the answer register enforces the link
    floor of constitution law 12 and a session writing prose will not think of
    it. The link is added AFTER the cut so it can never be the thing cut off.
    """
    body = (session_text or "").strip()
    if not body:
        return ""
    if note:
        body = body + "\n\n" + note.strip()
    total, site = count_links(body)
    link_line = "" if site else ("\n\nThe board: %s" % SITE_LINK)
    # Adding a link where two already sit would break the cap of two, so the
    # register refuses it and the repair pass gets the clause. Not adding is
    # the wrong fix either way; it is said out loud rather than done quietly.
    if link_line and total >= 2:
        link_line = ""
    room = max(200, cut_at - len(link_line))
    return cap_text(body, room) + link_line


#: THE THREE WORDINGS THAT MUST NEVER FAIL THE REGISTER, because they are what
#: Jafar hears when everything else has failed. Each is run through the real
#: `producer-check.py` in the selftest, which is the accepting case for them.
def fallback_refused(clause_free_reason=""):
    return ("I could not put the answer to your message into the form this "
            "channel accepts, so it is being held on the machine rather than "
            "sent as it stands. Nothing you asked for was lost. Ask again, or "
            "ask for it a different way, and it will be tried once more."
            + (" " + clause_free_reason if clause_free_reason else "")
            + "\n\nThe board: %s" % SITE_LINK)


def fallback_no_cli(state_words="not available on this machine right now"):
    return ("The machine cannot start the work you asked for: the tool it "
            "needs is %s. Nothing you asked for was lost, and nothing was "
            "started. It will work once somebody has looked at the machine."
            "\n\nThe board: %s" % (state_words, SITE_LINK))


def fallback_limit(when_words):
    return ("The work you asked for is paused: the allowance on the account "
            "ran out part way through. It starts again by itself %s, and you "
            "do not need to do anything. Nothing you asked for was lost."
            "\n\nThe board: %s" % (when_words, SITE_LINK))


def fallback_limit_gaveup():
    return ("The work you asked for was paused several times waiting for the "
            "allowance to come back, and it has now been put down rather than "
            "held any longer. Nothing you asked for was lost. Ask again when "
            "the allowance is healthy."
            "\n\nThe board: %s" % SITE_LINK)


def fallback_interrupted():
    return ("The work you asked for was cut off part way through, most likely "
            "because the machine restarted. Nothing you asked for was lost, "
            "and nothing was half-sent. Ask again and it will start from the "
            "beginning."
            "\n\nThe board: %s" % SITE_LINK)


TIMEOUT_NOTE = ("That is as far as it got: it reached the time limit set for "
                "one piece of work and was stopped there.")
EMPTY_NOTE = ("The work ran but produced no answer to send, so there is "
              "nothing here to read. Ask again and it will be tried once "
              "more.")


# --------------------------------------------------------------------------
# The session limit: recognising one, and reading the reset time out of it.
# --------------------------------------------------------------------------
def looks_like_limit(text, exit_code):
    """(True, pattern-name) or (False, why-not). A LIMIT IS NOT A CRASH.

    The distinction the project keeps getting wrong. A limit means: stop,
    record it, wait, and do the same instruction again when the allowance is
    back. A crash means: this instruction is done with, answer with what there
    is. Retrying a limit in a loop burns the allowance the moment it returns,
    which is the failure mode this function exists to prevent.

    EXIT 0 IS NEVER A LIMIT, and length is not a disambiguation. A session
    that SUCCEEDS and prints a short true sentence about limits ("You have not
    reached your usage limit.") is an answer to a question he can well ask,
    and treating it as a notice paused it 30, 60, 120, 240 and 240 minutes,
    produced the same answer five more times, threw all six away, and closed
    the instruction after eleven and a half hours with a message stating as
    fact that the allowance on his account had run out. Against that, the case
    the length rule protected: a CLI that prints a REAL limit and exits 0.
    That case now falls through to the ordinary path, where the notice itself
    becomes the answer and the journal records `code=0` with the exact first
    line, which is noisy, truthful, and the evidence that would set this rule
    from a measurement instead of a guess.
    """
    body = (text or "")
    if exit_code == 0:
        return False, "it-exited-0-so-a-limit-phrase-is-prose"
    for name, pattern in LIMIT_PATTERNS:
        if re.search(pattern, body, re.I):
            return True, name
    return False, "no-limit-wording-in-the-output"


def parse_reset_epoch(text, now):
    """(epoch, how) or (None, why-not). Read the reset instant out of a notice.

    FOUR FORMS, TRIED IN ORDER OF HOW LITTLE THEY ASSUME: a whole epoch, an
    ISO instant, a relative "in N minutes", and a clock time. The clock form
    is the one that can be wrong, because a notice naming a bare hour names it
    in a timezone this program cannot see; UTC is honoured when it is written
    down and local assumed otherwise, and the CLAMP in `limit_sleep` is what
    makes a wrong guess cost hours rather than days.
    """
    body = text or ""
    m = re.search(r"\b(1[6-9]\d{8})\b", body)
    if m:
        return int(m.group(1)), "epoch-in-the-notice"
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})", body)
    if m:
        y, mo, d, h, mi = (int(g) for g in m.groups())
        try:
            when = datetime.datetime(y, mo, d, h, mi,
                                     tzinfo=datetime.timezone.utc)
            return int(when.timestamp()), "iso-instant-read-as-utc"
        except ValueError:
            pass
    m = re.search(r"\bresets?\s+in\s+(\d+)\s*(second|minute|hour)s?\b",
                  body, re.I)
    if m:
        n, unit = int(m.group(1)), m.group(2).lower()
        mult = {"second": 1, "minute": 60, "hour": 3600}[unit]
        return int(now) + n * mult, "relative-in-%s%ss" % (n, unit)
    m = re.search(r"\breset[s]?\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*"
                  r"(am|pm)?\s*\(?([A-Za-z][A-Za-z/_+-]{1,15})?\)?", body, re.I)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        half = (m.group(3) or "").lower()
        zone = (m.group(4) or "").upper()
        if half == "pm" and hour < 12:
            hour += 12
        if half == "am" and hour == 12:
            hour = 0
        if hour > 23 or minute > 59:
            return None, "the-clock-time-did-not-parse"
        utc = zone in ("UTC", "GMT", "Z", "ZULU")
        return _next_clock(now, hour, minute, utc), (
            "clock-time-read-as-%s" % ("utc" if utc else "local"))
    return None, "no-reset-time-in-the-notice"


def _next_clock(now, hour, minute, utc):
    """The next instant with that clock reading, at or after `now`."""
    base = (datetime.datetime.fromtimestamp(int(now), datetime.timezone.utc)
            if utc else datetime.datetime.fromtimestamp(int(now)))
    when = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if when <= base:
        when = when + datetime.timedelta(days=1)
    return int(when.timestamp())


def limit_backoff_sec(pause_index):
    """The ladder for a notice with no readable reset time. A SERIES, printed
    when it bites: 30, 60, 120, 240, 240, ... minutes."""
    i = min(max(0, pause_index), len(LIMIT_BACKOFF_MIN) - 1)
    return LIMIT_BACKOFF_MIN[i] * 60


def limit_sleep(reset_epoch, now, pause_index):
    """(seconds, why). How long to wait, and the clamp that bounds a misread.

    A parsed instant in the past would be a spin, and an instant days away
    would be a stall nobody can tell from a hang. Both ends are named in the
    answer so the journal says which one bit.
    """
    if reset_epoch is None:
        return limit_backoff_sec(pause_index), "backoff-ladder-no-reset-time"
    raw = int(reset_epoch) - int(now)
    if raw < LIMIT_SLEEP_MIN_SEC:
        return LIMIT_SLEEP_MIN_SEC, "clamped-up-to-the-floor"
    if raw > LIMIT_SLEEP_MAX_SEC:
        return LIMIT_SLEEP_MAX_SEC, "clamped-down-to-the-ceiling"
    return raw, "from-the-reset-time-in-the-notice"


def human_wait(seconds):
    """Plain words for a wait, for a message that goes to a phone."""
    seconds = max(0, int(seconds))
    if seconds < 90:
        return "in a minute or so"
    if seconds < 5400:
        return "in about %d minutes" % max(1, round(seconds / 60.0))
    return "in about %d hours" % max(1, round(seconds / 3600.0))


# --------------------------------------------------------------------------
# The journal. Append-only, outside every checkout, and the ONLY thing that
# decides what has already been handled.
# --------------------------------------------------------------------------
#: The states an instruction can end in. TERMINAL means never run again.
TERMINAL = ("answered", "failed", "interrupted", "not-an-instruction",
            "too-old", "backlog-skipped", "no-cli", "limit-gaveup")


class Journal(object):
    """What already happened, on disk, in key=value lines.

    DERIVED, NEVER GUESSED. `handled()` reads the file every time rather than
    keeping a set in memory, so a crash mid-instruction, a restart and a
    second process all reach the same answer. `taken` is written BEFORE the
    session starts, which is what makes a crash resume rather than repeat: the
    entry is there with no terminal state, and the next start closes it as
    `interrupted` instead of running it again.
    """

    def __init__(self, path):
        self.path = path
        self.lines = []

    def load(self):
        self.lines = []
        try:
            with open(self.path, "r", encoding="utf-8",
                      errors="replace") as fh:
                self.lines = [l.rstrip("\n") for l in fh]
        except OSError:
            self.lines = []
        return self

    def exists(self):
        return os.path.isfile(self.path)

    def append(self, event, **kv):
        """One line. Every value goes through `oneword`, without exception."""
        parts = ["%s event=%s" % (stamp(), oneword(event))]
        for k in sorted(kv):
            parts.append("%s=%s" % (k, oneword(kv[k])))
        line = " ".join(parts)
        self.lines.append(line)
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(line + "\n")
        except OSError:
            pass
        return line

    def _field(self, line, key):
        for tok in line.split():
            if tok.startswith(key + "="):
                return tok[len(key) + 1:]
        return None

    def states(self):
        """{message-stem: newest state}. Last write wins, which is what an
        append-only log means."""
        out = {}
        for line in self.lines:
            msg = self._field(line, "msg")
            event = self._field(line, "event")
            if msg and event in ("taken",) + TERMINAL:
                out[msg] = event
        return out

    def handled(self):
        """Stems that must never be started again."""
        st = self.states()
        return {m for m, s in st.items() if s in TERMINAL}

    def unclosed(self):
        """Stems that were taken and never closed: a crash happened here."""
        st = self.states()
        return sorted(m for m, s in st.items() if s == "taken")

    def counts(self):
        """(handled, answered, failed) with the denominator named by the
        caller. Every zero here ships the set it came from."""
        st = self.states()
        handled = len([1 for s in st.values() if s in TERMINAL])
        answered = len([1 for s in st.values() if s == "answered"])
        return handled, answered, len(st)


# --------------------------------------------------------------------------
# Git, with the ownership guard made mechanical rather than written down.
# --------------------------------------------------------------------------
class WrongCheckout(Exception):
    """Raised when git is asked to run where the watcher is the owner."""


def git_call(args, cwd, timeout=180):
    """One git command in a checkout THIS FILE OWNS. (rc, output).

    THE GUARD IS THE POINT. `tools/pc-watcher.py` hard-resets the repository
    root every pass and reads FETCH_HEAD there, so a git command from this
    daemon in that directory is the four-day incident waiting to happen again.
    Rather than a comment asking the next person not to, this refuses by path:
    the repository root and anything inside it is not a place this file runs
    git. rc 126 is that refusal, 127 is git missing, 124 is a timeout.
    """
    real_cwd = os.path.realpath(cwd)
    real_repo = os.path.realpath(REPO)
    if real_cwd == real_repo or real_cwd.startswith(real_repo + os.sep):
        raise WrongCheckout(
            "the executor refuses to run git inside the checkout pc-watcher "
            "owns; sessions and their git live in the worktree at %s"
            % WORKTREE_DIR)
    env = dict(os.environ)
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_EDITOR": "true",
                "GIT_MERGE_AUTOEDIT": "no", "GIT_PAGER": "cat"})
    try:
        p = subprocess.run(["git"] + list(args), cwd=cwd, env=env,
                           capture_output=True, text=True, errors="replace",
                           timeout=timeout)
    except FileNotFoundError:
        return 127, "git is not on PATH on this PC"
    except subprocess.TimeoutExpired:
        return 124, "git %s did not finish within %d second(s)" % (
            args[0] if args else "?", timeout)
    except OSError as e:
        return 125, "could not run git (%s)" % type(e).__name__
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()


def worktree_ready(repo, worktree, say):
    """(ok, detail). Make sure the worktree exists, creating it once.

    `git worktree add` is the ONE git command this file runs in the
    repository root, and it is run through subprocess directly rather than
    through `git_call`, which refuses that directory on purpose. It writes
    .git/worktrees metadata and a new directory somewhere else; it does not
    touch the index, the working tree or any ref the watcher reads. Said out
    loud here because it is the single exception to the rule above.
    """
    if os.path.isdir(os.path.join(worktree, ".git")) or \
            os.path.isfile(os.path.join(worktree, ".git")):
        return True, "already-there"
    if os.path.exists(worktree) and os.listdir(worktree):
        return False, "the-worktree-path-exists-and-is-not-a-worktree"
    env = dict(os.environ)
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_EDITOR": "true"})
    try:
        p = subprocess.run(["git", "worktree", "add", "--detach", worktree,
                            "HEAD"], cwd=repo, env=env, capture_output=True,
                           text=True, errors="replace", timeout=300)
    except FileNotFoundError:
        return False, "git-is-not-on-PATH"
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, "could-not-create-the-worktree-%s" % type(e).__name__
    if p.returncode != 0:
        say("worktree: could not be created: %s"
            % inbox.one_line((p.stdout or "") + (p.stderr or ""), 200))
        return False, "git-refused-to-create-it"
    return True, "created"


def prepare_worktree(worktree, branch, say):
    """(ok, head, detail). Put the worktree on the tip of the work branch.

    DETACHED, ALWAYS. Git refuses to check out in a linked worktree a branch
    the main checkout holds (measured), and staying detached means this can
    never race with what the watcher has checked out. The push at the end
    names the branch instead.

    A FETCH THAT FAILS IS NOT FATAL. The session then runs on whatever this
    worktree already had, which is older but real, and the journal says so.
    """
    rc, out = git_call(["fetch", "--no-tags", "-q", "origin", branch],
                       worktree)
    fetched = rc == 0
    if not fetched:
        say("worktree: could not fetch (%s). The work starts from whatever "
            "this worktree already had." % inbox.one_line(out, 120))
    ref = "FETCH_HEAD" if fetched else "HEAD"
    rc, out = git_call(["checkout", "-f", "--detach", ref], worktree)
    if rc != 0:
        return False, None, "could-not-detach-onto-%s" % ref
    rc, head = git_call(["rev-parse", "--short", "HEAD"], worktree)
    return True, (head.strip() if rc == 0 else "unknown"), (
        "fetched" if fetched else "offline")


def commit_record(worktree, rel, body, message, say, extra_rels=()):
    """Commit the record and what he was told, in the worktree. (ok, detail,
    staged).

    STAGED BY NAME, never `git add <directory>`: a run that failed would
    otherwise commit its stale checkout's files as its own evidence
    (.claude/rules/ci.md). Whatever the session itself committed is already in
    the history; this only adds the record on top.

    THE ANSWER FILES RIDE WITH IT (A5). `place_answer` says its worktree copy
    "is committed and pushed, which is the only route the studio in the
    container has to read what was said", and nothing staged it: the branch
    carried `answer-placed ... chars=N` and never one word of the text. Every
    rel in `extra_rels` that EXISTS in this worktree is staged beside the
    record, and `staged` is the count, so a missing file cannot quietly turn
    into a record commit that claims to carry an answer.
    """
    full = os.path.join(worktree, *rel.split("/"))
    try:
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
    except OSError as e:
        return False, "could-not-write-the-record-%s" % type(e).__name__, 0
    names = [rel]
    for extra in extra_rels:
        if extra in names:
            continue
        if os.path.isfile(os.path.join(worktree, *extra.split("/"))):
            names.append(extra)
        else:
            say("record: %s is not in the worktree, so it is not staged. The "
                "record commit carries what is there and says how many."
                % extra)
    rc, out = git_call(["add", "--"] + names, worktree)
    if rc != 0:
        return False, "could-not-stage-the-record", 0
    rc, _out = git_call(["-c", "user.name=LEDGER executor",
                         "-c", "user.email=ledger-bot@users.noreply.github.com",
                         "commit", "-q", "-m", message], worktree)
    if rc != 0:
        say("record: nothing to commit or the commit refused (%s)"
            % inbox.one_line(out, 120))
        return False, "commit-refused", 0
    return True, "committed", len(names)


def push_branch(worktree, branch, say):
    """(ok, detail). Push the detached head to a named branch on origin.

    NEVER FORCED. One branch per instruction means the second push of the same
    instruction (a limit pause, then the answer) is a fast forward, and no
    push this daemon makes can ever destroy anything.
    """
    rc, out = git_call(["push", "-q", "origin",
                        "HEAD:refs/heads/%s" % branch], worktree, timeout=300)
    if rc != 0:
        say("record: the push did not land (%s). Everything is still on this "
            "PC." % inbox.one_line(out, 160))
        return False, "push-failed"
    return True, "pushed"


# --------------------------------------------------------------------------
# The session itself. NEVER RUN WHERE IT WAS WRITTEN.
# --------------------------------------------------------------------------
def build_prompt(instruction, stem):
    """The whole dispatch for one instruction. PURE, so it is readable in a
    test rather than only in a log on a machine nobody is at.

    THE REGISTER IS IN THE PROMPT because the answer has to pass it. A session
    writing engineering prose fails `banned` on its first sentence, and a
    refused answer means Jafar hears the fallback instead of the answer he
    asked for. The words come from PROMPT_BANNED_WORDS, which the selftest
    holds against the real checker.

    NO ANGLE BRACKET IS WRITTEN INTO THIS PROMPT (A6). On Windows the CLI is
    an npm `.cmd` shim, and a `.cmd` has its command line re-parsed by
    cmd.exe, which reads `<` and `>` as redirection. The markers used to be
    a dashed cut mark with an angle bracket in the middle of it. They are
    letters and `=` now, and the selftest asserts
    that the only angle bracket the prompt can carry is one HE typed. What his
    own text does to that shim (`%` and `!` in particular) is a first-run
    reading nothing in this container can take.

    THE CHECKOUT ONE LEVEL UP IS NAMED (A7). `git_call` refuses by path, but
    that guard cannot see the session's own git client, and the session sits
    one directory below the checkout pc-watcher.py hard-resets every minute.
    The sentence is not a guard. It is the only thing there is.
    """
    return (
        "You are one bounded worker session in the LEDGER studio, started by "
        "the PC because Jafar sent an instruction from his phone. The "
        "repository you are in is the memory; you are not. Read CLAUDE.md "
        "first, then canon.md if the instruction touches the world.\n"
        "\n"
        "HIS INSTRUCTION, VERBATIM, BETWEEN THE MARKERS:\n"
        "===== BEGIN INSTRUCTION =====\n"
        "%s\n"
        "===== END INSTRUCTION =====\n"
        "\n"
        "DO THE ONE THING HE ASKED. If it is a question, answer it from "
        "evidence you have just read, not from memory. If it is work, do it "
        "here: you are on a detached head in a worktree that belongs to you "
        "alone, so commit what you change, with a real message. The folder "
        "one level up, the project checkout, belongs to another process that "
        "resets it every minute. Never read from it, write into it, or run "
        "anything inside it. Do not push "
        "and do not open a pull request; the machine pushes for you when you "
        "exit. Do not start a second piece of work, however obvious it looks. "
        "Never wait for input and never ask a question back.\n"
        "\n"
        "YOUR FINAL MESSAGE IS WHAT HE READS ON HIS PHONE, and nothing else "
        "you print reaches him. Write it for him and not for an engineer:\n"
        "  - plain English, under three thousand characters, no headings.\n"
        "  - no file paths, no file names, no key=value pairs, no code.\n"
        "  - do not use these words: %s.\n"
        "  - do not narrate what you did (no 'I checked', no 'let me'), do "
        "not apologise, and do not say you are still working.\n"
        "  - say what is true and what it means for him.\n"
        "The machine adds one link for you, so do not add links yourself.\n"
        % (instruction.strip(), ", ".join(PROMPT_BANNED_WORDS)))


def repair_prompt(draft, clause):
    """The second and last attempt: same answer, wording the register takes."""
    return (
        "Rewrite the message below so it passes the studio's message rules. "
        "Keep every fact and every number; change only the wording. Do not "
        "add anything new and do not add a link.\n"
        "\n"
        "WHAT THE CHECK REFUSED IT ON:\n%s\n"
        "\n"
        "THE RULES: plain English for a non-technical reader, no file paths, "
        "no file names, no key=value pairs, no code, none of these words: "
        "%s. No narration of what was done, no apology.\n"
        "\n"
        "PRINT THE REWRITTEN MESSAGE AND NOTHING ELSE.\n"
        "\n"
        "===== THE MESSAGE =====\n%s\n"
        % (inbox.one_line(clause, 400), ", ".join(PROMPT_BANNED_WORDS),
           draft))


def cli_extra_args(state_dir):
    """Extra arguments for the CLI, from a plain file, or none.

    WHY THIS EXISTS. Nothing here can know whether the CLI on his PC needs a
    flag to run unattended: there is no CLI in this container. run-night.ps1
    passes none, so this passes none by default and the file is the escape
    hatch that makes a first-run fix a text file rather than a round trip.
    """
    path = os.path.join(state_dir, CLI_ARGS_FILE)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return [l.strip() for l in fh if l.strip()
                    and not l.strip().startswith("#")]
    except OSError:
        return []


def claude_argv(prompt, turns=SESSION_TURNS, extra=()):
    """The invocation. ONE LINE, THE SAME ONE run-night.ps1 USES.

    `claude -p <prompt> --max-turns N`, read out of
    tools/runner/run-night.ps1 line 40 rather than invented here. Kept as its
    own function so there is one place to change it and one place to read it
    in a test, and so the two invokers cannot drift apart silently.
    """
    return ["claude", "-p", prompt, "--max-turns", str(int(turns))] + list(extra)


def session_env(base=None):
    """The environment the `claude -p` child runs in: this one, plus the
    Stop-hook opt-out. PURE, so the suite reads what it sets instead of
    trusting a comment.

    WHY THE ENVIRONMENT AND NOT AN ARGUMENT. Nothing on the CLI can say "do
    not run the Stop hook", and nothing should: the hook is registered in
    `.claude/settings.json`, which travels with the checkout the worktree is
    made from, so the drain is going to run. What the environment can say is
    WHICH session it is running in, and that is the whole decision.

    THAT STOP FIRES AT ALL UNDER `claude -p` was read off /opt/claude-code/
    bin/claude on 2026-09-09 (version 2.1.266) rather than remembered, and the
    reading is quoted in full in `tools/wake-queue.py`'s docstring beside the
    block cap. In short: the one mode that turns hooks off names itself
    ("hooks are disabled in this mode (--bare)"), print mode is not it, and
    the Stop payload is built in the same turn-end branch that enforces
    `--max-turns`, which is the flag `claude_argv` above passes. NOT OBSERVED:
    no `claude -p` has run here or anywhere in this repository.
    """
    env = dict(os.environ if base is None else base)
    env[WAKE_DRAIN_ENV] = WAKE_DRAIN_OFF
    return env


def kill_tree(proc):
    """Stop a session and everything it started. UNVERIFIED ON WINDOWS.

    A timeout that kills only the parent leaves the child holding the
    allowance and the worktree, which is a stall nobody can see. On Windows
    that needs taskkill with /T; on POSIX it needs the process group. Neither
    branch has run on the machine that matters.
    """
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           capture_output=True, timeout=60)
        else:
            proc.terminate()
    except Exception:                                         # noqa: BLE001
        pass
    try:
        proc.wait(timeout=30)
    except Exception:                                         # noqa: BLE001
        try:
            proc.kill()
        except Exception:                                     # noqa: BLE001
            pass


def read_log(log_path):
    """What the session actually printed, read back off disk. (text, why).

    THE READING IS THE FILE, not a pipe this process held: the child writes
    straight into the log, so a session killed mid-sentence still leaves every
    byte it had written, and there is one copy rather than two that can
    disagree.
    """
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(), ""
    except OSError as e:
        return "", "the-session-log-could-not-be-read-back-%s" % (
            type(e).__name__)


def _not_started(why):
    # `wakeDrain` IS THE WORDS HERE, not "off": no child was started, so no
    # environment was handed to one, and a journal line claiming the opt-out
    # was set on a session that never existed is a false reading with a value
    # on it.
    return {"rc": None, "out": "", "elapsed": 0, "timedout": False,
            "stopped": False, "started": False, "why": why,
            "wakeDrain": NOTHING_MEASURED}


def run_session(prompt, cwd, log_path, turns=SESSION_TURNS,
                wall=SESSION_WALL_SEC, extra=(), say=None, spawn=None,
                which=None, beat=None, stop=None, slice_sec=SESSION_SLICE_SEC):
    """Run one session. Returns a dict, never raises for a session's failure.

    Keys: rc, out, elapsed, timedout, stopped, started (bool), why (when it
    never started). The output goes to `log_path` as the child writes it and
    is read back from there, so a session that produced something unreadable
    still leaves the something.

    IT WAKES UP (A2). The wait used to be a single blocking read of the
    child's pipe for the whole session: nothing beat the lock for up to thirty
    minutes against a stale window of 135 seconds, so the lock read as dead
    for all but the first two minutes of every session, and the stop file was
    read only between instructions. Now the wait is a loop of `slice_sec`, and
    on every slice it calls `beat()` (the lock heartbeat) and `stop()` (the
    stop file). Both are injected so the container can drive them with no
    machine, no CLI and no lock.

    ARGV[0] IS THE RESOLVED PATH (A6). On Windows the CLI is an npm `.cmd`
    shim: `shutil.which` finds it because it honours PATHEXT, and `Popen` with
    the bare name does not. That combination reported the tool FOUND in the
    status line and then answered every instruction with the note saying the
    tool is not on the machine. `claude_argv` is left alone so the comparison
    with run-night.ps1 still holds; the resolution happens here. UNVERIFIABLE
    IN THIS CONTAINER: there is no Windows and no `claude` here.
    """
    say = say or (lambda _s: None)
    which = which or shutil.which
    beat = beat or (lambda: None)
    stop = stop or (lambda: False)
    started = time.time()
    argv = claude_argv(prompt, turns, extra)
    resolved = which(argv[0])
    if resolved:
        argv = [resolved] + argv[1:]
    elif spawn is None:
        return _not_started("the claude command is not on PATH on this PC")
    child_env = None
    if spawn is None:
        # THE STOP-HOOK OPT-OUT GOES IN HERE (A1), at the ONE place this
        # process builds the child's environment. An injected spawn leaves
        # `child_env` None and the reading below says the words rather than
        # claiming an opt-out this process did not set.
        child_env = session_env()

        def spawn(a, c, out_fh):
            kw = {}
            if os.name != "nt":
                kw["start_new_session"] = True
            return subprocess.Popen(a, cwd=c, stdin=subprocess.DEVNULL,
                                    stdout=out_fh, stderr=subprocess.STDOUT,
                                    env=child_env, **kw)
    try:
        if os.path.dirname(log_path):
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
        log_fh = open(log_path, "w", encoding="utf-8", newline="\n")
    except OSError as e:
        # The log lives in the state directory, which is also where the
        # journal lives: if this cannot be written, nothing here can record
        # anything either. Named rather than swallowed.
        return _not_started("the session log could not be opened (%s)"
                            % type(e).__name__)
    timedout = stopped = False
    try:
        try:
            proc = spawn(argv, cwd, log_fh)
        except OSError as e:
            return _not_started("the session would not start (%s)"
                                % type(e).__name__)
        deadline = started + wall
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                timedout = True
                say("session: the wall clock of %d minute(s) bit; stopping it."
                    % (wall // 60))
                kill_tree(proc)
                break
            try:
                proc.wait(timeout=max(0.05, min(slice_sec, remaining)))
                break
            except subprocess.TimeoutExpired:
                pass
            beat()
            if stop():
                stopped = True
                say("session: the stop file is there; stopping the session "
                    "rather than letting it finish.")
                kill_tree(proc)
                break
    finally:
        try:
            log_fh.close()
        except OSError:
            pass
    out, why_log = read_log(log_path)
    if why_log:
        say("session: %s" % why_log)
    return {"rc": proc.returncode, "out": out,
            "elapsed": int(time.time() - started), "timedout": timedout,
            "stopped": stopped, "started": True, "why": "",
            # WHAT WAS ACTUALLY HANDED TO THE CHILD, read back out of the
            # environment this process built rather than asserted from the
            # constant, so the journal line is a reading and not a claim.
            "wakeDrain": (child_env or {}).get(WAKE_DRAIN_ENV,
                                               NOTHING_MEASURED)}


# --------------------------------------------------------------------------
# Placing the answer where the bot will send it.
# --------------------------------------------------------------------------
def check_answer(repo, text, tmp_dir):
    """(ok, clause). The answer register, run HERE, before anything is placed.

    THE SAME PROGRAM THE BOT WILL RUN. `outbox.run_check` shells out to
    tools/producer-check.py, so this is not a second opinion about the rules;
    it is the rules, asked early enough that a refusal can still be repaired
    instead of arriving as silence.
    """
    probe = os.path.join(tmp_dir, "probe.answer.md")
    try:
        os.makedirs(tmp_dir, exist_ok=True)
        with open(probe, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    except OSError as e:
        return False, "the answer could not be written for checking (%s)" \
            % type(e).__name__
    ok, clause, _out = outbox.run_check(repo, "answer", probe)
    return ok, clause


def place_answer(repo, worktree, stem, text, say, tag=""):
    """Write the answer where the bot sweeps, and where the record keeps it.

    (rel, copies, where). `where` names which copies exist and what was
    skipped, as one word, so a count of 1 can never read as a count of 2 with
    something missing.

    TWO COPIES, ON PURPOSE, AND THEY ARE DIFFERENT FACTS. The copy in this
    checkout is UNTRACKED, which is what lets it survive the watcher's hard
    reset and be found by the bot's next sweep; it is the only route to his
    phone. The copy in the worktree is committed and pushed by `push_record`,
    which is the only route the studio in the container has to read what was
    said. Neither is a substitute for the other, and the receipt written later
    names the sent one.

    THE WORKTREE COPY IS WRITTEN ONLY INTO A REAL WORKTREE (A4). This used to
    `makedirs` its way into `<worktree>/production/outbox/` whatever was
    there, and it is called before any worktree exists: from
    `close_unfinished` at start, and from every no-cli and failed path,
    including the one where `worktree_ready` has JUST refused. Since
    `worktree_ready` refuses for ever a path that exists, is non-empty and has
    no `.git`, one first run in the wrong order (git not yet on PATH) left
    plain directories at that path and permanently disabled the worktree:
    every instruction after it answered "not set up on this machine yet".
    """
    rel = outbox_rel(stem, tag)
    body = text.rstrip() + "\n"
    roots = [("outbox", repo)]
    skipped = []
    if os.path.exists(os.path.join(worktree, ".git")):
        roots.append(("worktree", worktree))
    else:
        skipped.append("worktree-does-not-exist-yet")
        say("answer: the studio's copy is NOT written: %s is not a worktree "
            "yet, so there is nothing to commit it to and nothing may be "
            "created there." % worktree)
    wrote = []
    for label, root in roots:
        full = os.path.join(root, *rel.split("/"))
        try:
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(body)
            wrote.append(label)
        except OSError as e:
            skipped.append("%s-%s" % (label, type(e).__name__))
            say("answer: could not be written under %s (%s)"
                % (os.path.basename(root), type(e).__name__))
    where = "+".join(wrote) if wrote else "nothing-written"
    if skipped:
        where = "%s/skipped:%s" % (where, "+".join(skipped))
    return rel, len(wrote), where


# --------------------------------------------------------------------------
# The status file: the same answer where somebody not at the keyboard reads it
# --------------------------------------------------------------------------
def status_lines(state):
    """key=value lines, every value one word. PURE."""
    order = ("executor", "handledTotal", "answeredTotal", "seenTotal",
             "pendingNow", "backlogSkippedAtFirstStart", "lastMsg",
             "lastOutcome", "lastElapsedSec", "limitPausesThisInstruction",
             "limitResumeIn", "cli", "worktree", "stopFile", "written")
    out = []
    for key in order:
        if key in state:
            out.append("%s=%s" % (key, oneword(state[key])))
    for key in sorted(state):
        if key not in order:
            out.append("%s=%s" % (key, oneword(state[key])))
    return out


def write_status(repo, state):
    path = os.path.join(repo, *STATUS_REL.split("/"))
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(status_lines(state)) + "\n")
        return True
    except OSError:
        return False


def read_status(repo):
    """{key: value} or {}. What the supervisor's window reads, so that the
    status of this daemon is not a second implementation over there."""
    path = os.path.join(repo, *STATUS_REL.split("/"))
    out = {}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    out[k] = v
    except OSError:
        return {}
    return out


def status_sentence(repo):
    """One line for the supervisor window. Every zero ships its denominator.

    NOTHING MEASURED IS SAID IN WORDS. A daemon that has never handled
    anything and a daemon whose status file cannot be read are different
    facts, and a bare zero cannot tell them apart.
    """
    st = read_status(repo)
    if not st:
        return ("executor: nothing measured, no status written yet, so it has "
                "not finished a pass since it started.")
    handled = st.get("handledTotal", "unreadable")
    seen = st.get("seenTotal", "unreadable")
    pending = st.get("pendingNow", "unreadable")
    tail = ""
    if st.get("limitResumeIn", "none") not in ("none", "", "unreadable"):
        tail = (" PAUSED on the account allowance, back %s."
                % st.get("limitResumeIn"))
    if st.get("cli") == "missing":
        tail += (" The claude command is NOT on this PC, so nothing can be "
                 "run: instructions are answered with a note saying so.")
    return ("executor: %s of %s instruction(s) handled, %s waiting now, "
            "state %s.%s" % (handled, seen, pending, st.get("executor", "?"),
                             tail))


# --------------------------------------------------------------------------
# The lock. One executor, or none.
# --------------------------------------------------------------------------
def lock_take(state_dir, now=None, stale=LOCK_STALE_SEC):
    """(ok, why). A heartbeat file, because process liveness is not portable.

    A pid check is a Windows question this container cannot answer, so the
    lock carries an instant instead: a heartbeat older than the stale window
    is a dead executor and the lock is taken over. A FRESH lock means a second
    copy is genuinely running, and the second copy exits saying so rather than
    running a second session on one worktree.
    """
    now = int(now if now is not None else time.time())
    path = os.path.join(state_dir, "executor.lock")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            beat = int((fh.read().split("heartbeat=")[-1] or "0").split()[0])
        if now - beat < stale:
            return False, ("another executor is running on this PC (its last "
                           "heartbeat was %d second(s) ago). Only one may run."
                           % (now - beat))
    except (OSError, ValueError, IndexError):
        pass
    return lock_beat(state_dir, now), ""


def lock_beat(state_dir, now=None):
    now = int(now if now is not None else time.time())
    path = os.path.join(state_dir, "executor.lock")
    try:
        os.makedirs(state_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("pid=%d heartbeat=%d\n" % (os.getpid(), now))
        return True
    except OSError:
        return False


# --------------------------------------------------------------------------
# Reading what is waiting
# --------------------------------------------------------------------------
def stem_of(rel):
    name = rel.rsplit("/", 1)[-1]
    return name[:-3] if name.endswith(".md") else name


def pending_instructions(repo, handled):
    """[(stem, rel, fields)] oldest first, for everything not yet handled.

    ONE IMPLEMENTATION OF THE FORMAT. `inbox.message_files` and
    `inbox.parse_message` are the bot's own, so the reader and the writer
    cannot disagree about what a message file is; a README or a note dropped
    in that folder is outside the pattern and outside every count here.
    """
    out = []
    for rel in inbox.message_files(repo):
        st = stem_of(rel)
        if st in handled:
            continue
        try:
            with open(os.path.join(repo, *rel.split("/")), "r",
                      encoding="utf-8", errors="replace") as fh:
                fields, why = inbox.parse_message(fh.read())
        except OSError as e:
            fields, why = None, "could not be read (%s)" % type(e).__name__
        out.append((st, rel, fields, why if fields is None else ""))
    out.sort(key=lambda row: (row[2]["sentEpoch"] if row[2] else 0, row[0]))
    return out


def say(line):
    sys.stdout.write("%s  %s\n" % (time.strftime("%H:%M:%S"), line))
    sys.stdout.flush()


# --------------------------------------------------------------------------
# The daemon
# --------------------------------------------------------------------------
class Executor(object):
    """The loop. One instruction at a time, and never two of anything."""

    def __init__(self, repo=REPO, worktree=WORKTREE_DIR, state=STATE_DIR,
                 branch=None):
        self.repo = repo
        self.worktree = worktree
        self.state_dir = state
        self.branch = branch or inbox.WORK_BRANCH
        self.journal = Journal(os.path.join(state, "journal.log"))
        self.backlog_skipped = 0
        self.status = {"executor": "starting", "cli": "unknown",
                       "worktree": "unknown", "stopFile": "absent",
                       "limitResumeIn": "none",
                       "limitPausesThisInstruction": 0}

    # -- the record ------------------------------------------------------
    def beat(self):
        """Keep the lock alive across anything that blocks (A2).

        The heartbeat IS the liveness reading: `lock_take` gives the worktree
        to a second executor when the beat is older than LOCK_STALE_SEC, and a
        second executor closes the running instruction as interrupted, tells
        him so, and starts another session in the same worktree. So every wait
        long enough to matter beats: the session loop, the limit pause, and
        each stage of an instruction between them. WHAT STILL DOES NOT BEAT,
        said out loud rather than implied: a single git call, whose own
        timeouts (180 fetch, 300 push) are longer than the stale window.
        """
        lock_beat(self.state_dir)

    def record(self, event, **kv):
        line = self.journal.append(event, **kv)
        say(line.split(" ", 1)[-1])
        return line

    def publish_status(self, extra=None):
        handled, answered, seen = self.journal.counts()
        pending = len(pending_instructions(self.repo, self.journal.handled()))
        self.status.update({"handledTotal": handled, "answeredTotal": answered,
                            "seenTotal": seen, "pendingNow": pending,
                            "backlogSkippedAtFirstStart": self.backlog_skipped,
                            "written": stamp()})
        if extra:
            self.status.update(extra)
        write_status(self.repo, self.status)

    # -- the first start -------------------------------------------------
    def first_start_backlog(self):
        """On a machine with no journal at all, everything already on disk is
        old news. It is RECORDED, with its count, and not run.

        The alternative is a first double-click that starts a session for
        every message ever filed on that PC, in order, which is the opposite
        of bounded background work.
        """
        if self.journal.exists():
            return 0
        rows = pending_instructions(self.repo, set())
        for stemname, rel, _fields, _why in rows:
            self.journal.append("backlog-skipped", msg=stemname, file=rel)
        self.backlog_skipped = len(rows)
        if rows:
            say("first start: %d message(s) were already on this PC and are "
                "recorded as old news rather than run. Anything you send from "
                "now on is picked up." % len(rows))
        else:
            say("first start: nothing measured, 0 message(s) were waiting.")
        return len(rows)

    def close_unfinished(self):
        """A crash RESUMES, it does not repeat. Anything left `taken` is
        closed as interrupted, with a message, and never started again.

        THE RECORD GOES OUT WITH IT WHEN THERE IS A WORKTREE TO PUSH FROM
        (A5). That worktree still holds whatever the killed session had
        committed, and the interrupted note is the last thing said about the
        instruction, so both ride the instruction's own branch. With no
        worktree there is nothing to commit from, nothing was written there
        either, and nothing is pushed.
        """
        closed = 0
        for stemname in self.journal.unclosed():
            self.record("interrupted", msg=stemname,
                        why="the-machine-stopped-part-way-through")
            rel, _copies = self.deliver(stemname, fallback_interrupted(),
                                        "interrupted")
            if rel and os.path.exists(os.path.join(self.worktree, ".git")):
                self.push_record("exec/%s" % stemname,
                                 "The machine stopped part way through",
                                 [rel])
            closed += 1
        return closed

    # -- delivering --------------------------------------------------------
    def deliver(self, stemname, text, outcome, tag=""):
        """Put a message in the outbox for the bot, checking it first.
        (rel, copies), and `rel` is None when NOTHING SENDABLE WAS WRITTEN.

        A FALLBACK IS CHECKED TOO. The wordings in this file are held against
        the real checker in the selftest, but a checker that changes tomorrow
        must not turn a fallback into silence, so this runs it every time and
        says out loud when it refuses.

        THE TAG IS WHICH MESSAGE THIS IS (A1). Empty for the message that ENDS
        the instruction, `paused` for the note sent before a limit wait. One
        name, one message, one receipt: see `answer_name`.

        AND THE RETURN IS READ BACK OFF DISK, not believed. The caller decides
        `answered` from it, so a message that never reached the folder the bot
        sweeps must never come back as a file name: that is how a journal
        comes to say `answered` about something nobody could ever have sent.
        """
        self.beat()
        ok, clause = check_answer(self.repo, text,
                                  os.path.join(self.state_dir, "probe"))
        self.beat()
        if not ok:
            self.record("register-refused-the-message", msg=stemname,
                        outcome=outcome, tag=tag or "final",
                        clause=inbox.one_line(clause, 160))
            return None, 0
        rel, copies, where = place_answer(self.repo, self.worktree, stemname,
                                          text, say, tag)
        sendable = os.path.isfile(os.path.join(self.repo, *rel.split("/")))
        self.record("answer-placed", msg=stemname, file=rel, copies=copies,
                    where=where, chars=len(text), outcome=outcome,
                    tag=tag or "final", sendable=sendable)
        if not sendable:
            self.record("nothing-to-send", msg=stemname, outcome=outcome,
                        tag=tag or "final", where=where,
                        why="the-copy-the-bot-sweeps-was-not-written")
            return None, copies
        return rel, copies

    # -- one instruction ---------------------------------------------------
    def handle(self, stemname, rel, fields):
        """Everything that happens to one instruction. Returns the outcome.

        `delivered` is every answer file this instruction actually placed, in
        order, and it is what `push_record` stages beside the journal (A5).
        """
        instruction = (fields or {}).get("text", "")
        self.record("taken", msg=stemname, file=rel, chars=len(instruction))
        self.publish_status({"executor": "working", "lastMsg": stemname})
        branch = "exec/%s" % stemname
        delivered = []
        self.beat()
        ok, detail = worktree_ready(self.repo, self.worktree, say)
        self.beat()
        self.status["worktree"] = "ready" if ok else detail
        if not ok:
            self.record("no-cli", msg=stemname, why="worktree-%s" % detail)
            self.deliver(stemname, fallback_no_cli(
                "not set up on this machine yet"), "no-cli")
            return "no-cli"
        ok, head, why = prepare_worktree(self.worktree, self.branch, say)
        self.beat()
        if not ok:
            self.record("failed", msg=stemname, why=why)
            self.deliver(stemname, fallback_no_cli(
                "not ready on this machine right now"), "failed")
            return "failed"
        self.record("session-start", msg=stemname, head=head, base=why,
                    turnBound=SESSION_TURNS, wallBoundSec=SESSION_WALL_SEC)

        pauses = 0
        extra = cli_extra_args(self.state_dir)
        prompt = build_prompt(instruction, stemname)
        while True:
            log = os.path.join(self.state_dir, "logs",
                               "%s-try%d.log" % (stemname, pauses + 1))
            res = run_session(prompt, self.worktree, log, extra=extra, say=say,
                              beat=self.beat, stop=self.stopped)
            self.beat()
            if not res["started"]:
                self.status["cli"] = "missing"
                self.record("no-cli", msg=stemname,
                            why=oneword(res["why"]))
                self.deliver(stemname, fallback_no_cli(), "no-cli")
                return "no-cli"
            self.status["cli"] = "found"
            if res["stopped"]:
                # THE STOP FILE IS A KILL SWITCH MID-SESSION NOW (A2), so it
                # ends the instruction rather than being noticed after it.
                self.record("failed", msg=stemname,
                            why="the-stop-file-appeared-during-the-session",
                            elapsedSec=res["elapsed"])
                fb, _c = self.deliver(stemname, fallback_interrupted(),
                                      "stopped")
                if fb:
                    delivered.append(fb)
                self.push_record(branch, "Stopped by the stop file", delivered)
                self.publish_status({"executor": "stopped-by-the-stop-file"})
                return "failed"
            is_limit, pattern = looks_like_limit(res["out"], res["rc"])
            # `wakeDrain` IS PER SESSION AND LAST-WINS, on the line for the
            # session it describes: it is the value this process put in THAT
            # child's environment, `off` when the opt-out was set and the
            # words when no environment was built here. It rides the
            # session-exit line rather than a line of its own so a reader
            # never has to join two lines to learn which session was opted
            # out (A1, ruling 2026-09-09).
            self.record("session-exit", msg=stemname, code=res["rc"],
                        elapsedSec=res["elapsed"], timedOut=res["timedout"],
                        outChars=len(res["out"]), limitLooking=is_limit,
                        limitPattern=pattern, wakeDrain=res["wakeDrain"],
                        firstLine=first_line(res["out"]))
            if not is_limit:
                break
            # A SESSION LIMIT IS NOT A CRASH, and this is the whole branch
            # that makes it not one: nothing is retried in a loop, the
            # instruction is NOT consumed, and the wait is recorded.
            pauses += 1
            if pauses > LIMIT_MAX_PAUSES:
                self.record("limit-gaveup", msg=stemname, pauses=pauses - 1,
                            cap=LIMIT_MAX_PAUSES)
                fb, _c = self.deliver(stemname, fallback_limit_gaveup(),
                                      "limit-gaveup")
                if fb:
                    delivered.append(fb)
                self.push_record(branch, "Allowance ran out repeatedly",
                                 delivered)
                return "limit-gaveup"
            now = time.time()
            reset, how = parse_reset_epoch(res["out"], now)
            wait, whyw = limit_sleep(reset, now, pauses - 1)
            self.record("limit-paused", msg=stemname, pattern=pattern,
                        resetRead=how, sleepSec=int(wait), why=whyw,
                        pause="%d/%d" % (pauses, LIMIT_MAX_PAUSES),
                        resumeAt=stamp(now + wait))
            self.publish_status({"executor": "paused-on-allowance",
                                 "limitPausesThisInstruction": pauses,
                                 "limitResumeIn": human_wait(wait)})
            if pauses == 1:
                # ITS OWN NAME (A1). The answer is still to come and it takes
                # `<stem>.answer.md`; this note may never occupy that name or
                # the receipt written for it silences the answer for ever.
                pn, _c = self.deliver(stemname, fallback_limit(
                    human_wait(wait)), "limit-paused", tag="paused")
                if pn:
                    delivered.append(pn)
            self.push_record(branch, "Allowance ran out, waiting", delivered)
            go_on, whyp = self.wait_for_allowance(wait)
            if not go_on:
                self.record("stopped-during-pause", msg=stemname, why=whyp,
                            pause="%d/%d" % (pauses, LIMIT_MAX_PAUSES))
                self.record("failed", msg=stemname, why=whyp,
                            elapsedSec=res["elapsed"])
                fb, _c = self.deliver(stemname, fallback_interrupted(),
                                      "stopped-during-pause")
                if fb:
                    delivered.append(fb)
                self.push_record(branch, "Stopped by the stop file",
                                 delivered)
                self.publish_status({"executor": "stopped-by-the-stop-file",
                                     "limitResumeIn": "none"})
                return "failed"
            self.record("limit-resume", msg=stemname,
                        pause="%d/%d" % (pauses, LIMIT_MAX_PAUSES),
                        sleptSec=int(wait))
            self.publish_status({"executor": "working",
                                 "limitResumeIn": "none"})

        # THE ANSWER. What it got, whatever happened, plus a plain sentence
        # when what happened needs one.
        note = TIMEOUT_NOTE if res["timedout"] else ""
        draft = compose_answer(res["out"], note=note)
        outcome = "answered"
        if not draft.strip():
            draft = compose_answer(EMPTY_NOTE)
            outcome = "failed"
        placed = None
        for attempt in range(1, REGISTER_ATTEMPTS + 1):
            self.beat()
            ok, clause = check_answer(self.repo, draft,
                                      os.path.join(self.state_dir, "probe"))
            self.record("register", msg=stemname,
                        attempt="%d/%d" % (attempt, REGISTER_ATTEMPTS),
                        passed=ok, clause=inbox.one_line(clause, 160)
                        if clause else "none")
            if ok:
                placed, _copies = self.deliver(stemname, draft, outcome)
                break
            if attempt == REGISTER_ATTEMPTS:
                break
            rlog = os.path.join(self.state_dir, "logs",
                                "%s-repair.log" % stemname)
            rep = run_session(repair_prompt(draft, clause), self.worktree,
                              rlog, turns=10, wall=600, extra=extra, say=say,
                              beat=self.beat, stop=self.stopped)
            self.beat()
            # A REPAIR THAT FAILED IS NOT AN ANSWER (A3). On a non-zero exit
            # what it printed is a notice or a stack trace, and that must
            # never become the message on his phone: the fallback goes.
            if not rep["started"] or rep["rc"] != 0 \
                    or not (rep["out"] or "").strip():
                self.record("repair-not-used", msg=stemname,
                            started=rep["started"], code=rep["rc"],
                            outChars=len(rep["out"] or ""))
                break
            draft = compose_answer(rep["out"])
        if placed is None:
            fb, _copies = self.deliver(stemname, fallback_refused(),
                                       "register-refused")
            self.record("fallback-sent", msg=stemname,
                        why="the-register-refused-both-attempts",
                        placed=fb or "nothing")
            placed = fb
        if placed is None:
            # NOTHING REACHED THE FOLDER THE BOT SWEEPS, so nothing can reach
            # his phone, and the journal may NOT say `answered` about it (A1).
            # The session log on this PC is the only copy of what was said.
            outcome = "failed"
        else:
            delivered.append(placed)
        self.record(outcome, msg=stemname, elapsedSec=res["elapsed"],
                    timedOut=res["timedout"],
                    answerFile=placed or "none-nothing-was-placed")
        self.push_record(branch, "Answered his message", delivered)
        return outcome

    def push_record(self, branch, why, rels=()):
        """The journal AND what he was told, committed and pushed (A5).

        PUSHED AT THE PAUSE AS WELL AS AT THE END. A pause that is only
        visible on his PC is a pause nobody in the studio can see, and being
        able to see a limit pause and the resume after it is the thing that
        was asked for.

        THE ANSWER TEXT RIDES WITH IT. Until this took `rels`, the branch
        carried `answer-placed ... chars=N` and not one word of what he was
        told, while `place_answer` said in its own docstring that the copy is
        committed and pushed. Every rel already delivered for this instruction
        is offered on every push, so the pause note lands with the pause and
        the answer lands with the answer; `commit_record` stages only the ones
        that are really in the worktree and says how many.
        """
        body = ("# What the PC did with the instructions from the phone.\n"
                "# Append-only, written by tools/runner/executor.py.\n"
                "# %s\n\n%s\n" % (why, "\n".join(self.journal.lines[-400:])))
        rel = "production/executor/journal.log"
        staged = 0
        try:
            ok, detail, staged = commit_record(
                self.worktree, rel, body, "Executor record: %s" % why, say,
                extra_rels=list(rels))
            if ok:
                ok, detail = push_branch(self.worktree, branch, say)
            self.journal.append("record", branch=branch, result=detail,
                                filesStaged="%d/%d" % (staged,
                                                       1 + len(list(rels))))
        except WrongCheckout as e:
            self.journal.append("record", branch=branch,
                                result="refused-wrong-checkout",
                                why=oneword(str(e)[:80]))
        finally:
            self.beat()

    def wait_for_allowance(self, seconds):
        """(go on?, why). The wait between limit retries, STOP HONOURED (A2).

        `sleep_through` has always returned False when the stop file appears
        and the caller threw that value away, so a STOP placed to protect the
        allowance ENDED the pause and re-ran the session at once, up to five
        times in quick succession: the file that means stop spent the thing it
        was there to protect. This is the one place that value is read.
        """
        if self.sleep_through(seconds):
            return True, "the-pause-finished"
        return False, "the-stop-file-appeared-during-the-pause"

    def sleep_through(self, seconds, slice_sec=30):
        """A long wait that still notices the stop file and still beats."""
        end = time.time() + seconds
        while time.time() < end:
            lock_beat(self.state_dir)
            if self.stopped():
                return False
            time.sleep(min(slice_sec, max(1, end - time.time())))
        return True

    def stopped(self):
        return os.path.exists(os.path.join(self.repo, *STOP_REL.split("/")))

    # -- the loop ----------------------------------------------------------
    def pass_once(self):
        """One look at the inbox. Returns what it did, as a word."""
        self.journal.load()
        if self.stopped():
            self.status["stopFile"] = "present"
            self.publish_status({"executor": "stopped-by-the-stop-file"})
            return "stopped"
        self.status["stopFile"] = "absent"
        rows = pending_instructions(self.repo, self.journal.handled())
        if not rows:
            self.publish_status({"executor": "idle"})
            return "idle"
        stemname, rel, fields, why = rows[0]
        if fields is None:
            self.record("failed", msg=stemname, why=oneword(why))
            self.publish_status({"executor": "idle"})
            return "unreadable"
        ok, whynot = is_instruction(fields.get("text", ""))
        if not ok:
            self.record("not-an-instruction", msg=stemname, why=whynot)
            self.publish_status({"executor": "idle"})
            return "skipped"
        age = int(time.time()) - int(fields.get("sentEpoch", 0))
        if age > MAX_AGE_SEC:
            self.record("too-old", msg=stemname, ageSec=age,
                        capSec=MAX_AGE_SEC)
            self.publish_status({"executor": "idle"})
            return "too-old"
        outcome = self.handle(stemname, rel, fields)
        self.publish_status({"executor": "idle", "lastOutcome": outcome,
                             "lastMsg": stemname})
        return outcome

    def run(self, once=False):
        print("")
        print("  LEDGER executor. Your instructions from the phone become "
              "real sessions here.")
        print("  project  : %s" % self.repo)
        print("  worktree : %s  (this daemon's own checkout; the watcher "
              "never touches it)" % self.worktree)
        print("  record   : %s" % self.state_dir)
        print("")
        ok, why = lock_take(self.state_dir)
        if not ok:
            say("NOT STARTING: %s" % why)
            return 3
        self.journal.load()
        self.first_start_backlog()
        self.journal.load()
        self.status["cli"] = "found" if shutil.which("claude") else "missing"
        if self.status["cli"] == "missing":
            say("the claude command is NOT on PATH on this PC. Instructions "
                "will be answered with a note saying so, rather than "
                "silently doing nothing. Nothing else here is affected.")
        self.close_unfinished()
        self.publish_status({"executor": "idle"})
        say("watching for instructions, one at a time, every %d second(s)."
            % POLL_SEC)
        while True:
            lock_beat(self.state_dir)
            try:
                what = self.pass_once()
            except WrongCheckout as e:
                say("REFUSED: %s" % e)
                what = "refused"
            except Exception as e:                            # noqa: BLE001
                say("the pass could not run (%s). The loop keeps going."
                    % type(e).__name__)
                what = "error"
            if once:
                say("one pass only, as asked: %s" % what)
                return 0
            time.sleep(POLL_SEC)


# --------------------------------------------------------------------------
# Selftest: the policy and every string, accepting case first.
# --------------------------------------------------------------------------
def selftest():                                               # noqa: C901
    import tempfile
    ok, bad = [], []

    def check(name, cond, detail=""):
        (ok if cond else bad).append(name)
        print("  %-6s %s%s" % ("ok" if cond else "FAILED", name,
                               "" if cond else "  <- %s" % (detail,)))

    tmp = tempfile.mkdtemp()

    # -- ACCEPTING CASE FIRST: an ordinary instruction is one to run --------
    good, why = is_instruction("check the weather in the town and tell me")
    check("accept/an-ordinary-sentence-is-an-instruction", good and not why,
          (good, why))
    for text, label in (("/ping", "a-command-the-bot-answers-itself"),
                        ("", "an-empty-message"), ("   ", "a-blank-message"),
                        ("ok", "a-two-character-message")):
        got, gotwhy = is_instruction(text)
        check("reject/%s-is-not-run" % label, got is False, (text, gotwhy))

    # -- the answer, composed -----------------------------------------------
    a = compose_answer("The town has four streets and they all look wet.")
    check("accept/a-plain-answer-keeps-its-words",
          "four streets" in a, a)
    check("accept/and-the-evidence-link-is-added-because-the-floor-needs-one",
          a.count(SITE_LINK) == 1, a)
    a2 = compose_answer("Look here: %s and nowhere else." % SITE_LINK)
    check("accept/an-answer-that-already-links-the-board-gets-no-second-one",
          a2.count(SITE_LINK) == 1, a2)
    a3 = compose_answer("x" * (ANSWER_CHAR_CAP * 2))
    check("accept/a-long-answer-is-cut-under-what-telegram-accepts",
          len(a3) < TELEGRAM_TEXT_MAX, len(a3))
    check("accept/and-the-cut-announces-itself-with-the-count",
          "more character(s) not shown" in a3, a3[-90:])
    check("accept/and-the-link-survives-the-cut-because-it-is-added-after",
          a3.endswith(SITE_LINK), a3[-60:])
    a4 = compose_answer("It ran out of time.", note=TIMEOUT_NOTE)
    check("accept/a-timeout-answer-carries-what-it-got-and-says-it-stopped",
          "ran out of time" in a4 and "time limit" in a4, a4)
    check("reject/an-empty-session-composes-to-nothing-not-to-a-link",
          compose_answer("") == "" and compose_answer(None) == "", "")

    # -- THE WORDINGS, AGAINST THE REAL CHECKER. This is the accepting case
    # for every sentence that can reach his phone, and it runs the same
    # program the bot will run.
    wordings = (("the-answer-shape", compose_answer(
        "The four streets are done and the wet look is holding up in the "
        "evening light. Nothing needs you today.")),
        ("the-timeout-answer", compose_answer(
            "It got as far as the first two streets.", note=TIMEOUT_NOTE)),
        ("the-empty-answer", compose_answer(EMPTY_NOTE)),
        ("the-register-fallback", fallback_refused()),
        ("the-no-tool-fallback", fallback_no_cli()),
        ("the-limit-pause-note", fallback_limit(human_wait(3 * 3600))),
        ("the-limit-gave-up-note", fallback_limit_gaveup()),
        ("the-interrupted-note", fallback_interrupted()))
    for label, text in wordings:
        passed, clause = check_answer(REPO, text, os.path.join(tmp, "probe"))
        check("accept/%s-passes-the-real-answer-register" % label, passed,
              inbox.one_line(clause, 200))

    # The prompt tells a session to avoid words the register actually bans.
    # Without this the prompt drifts into folklore and the answers start
    # failing for words it never mentioned.
    missed = []
    for word in PROMPT_BANNED_WORDS:
        probe = ("Everything is fine and the %s is done. The board: %s"
                 % (word, SITE_LINK))
        passed, _clause = check_answer(REPO, probe, os.path.join(tmp, "probe"))
        if passed:
            missed.append(word)
    check("accept/every-word-the-prompt-bans-is-really-banned",
          not missed, missed)
    check("accept/and-the-prompt-carries-the-instruction-verbatim",
          "paint the door red" in build_prompt("paint the door red", "s"),
          "")
    check("accept/and-tells-the-session-its-last-message-is-what-he-reads",
          "FINAL MESSAGE IS WHAT HE READS" in build_prompt("x", "s"), "")

    # A7. THE ONE SENTENCE THE PROMPT WAS MISSING. `git_call` refuses by path,
    # and that guard cannot see the session's own git client sitting one
    # directory below the checkout pc-watcher.py hard-resets every minute.
    off_limits = ("The folder one level up, the project checkout, belongs to "
                  "another process that resets it every minute. Never read "
                  "from it, write into it, or run anything inside it.")
    check("accept/the-prompt-names-the-checkout-one-level-up-as-off-limits",
          off_limits in build_prompt("do the thing", "s"),
          build_prompt("do the thing", "s")[:120])
    nosy = "look in the folder one level up and tell me what is in it"
    check("reject/and-nothing-he-types-can-remove-that-sentence",
          off_limits in build_prompt(nosy, "s").replace(nosy, ""), "")

    # A6. NOTHING cmd.exe WOULD READ AS A REDIRECTION. On Windows the CLI is
    # an npm .cmd shim, whose command line cmd.exe re-parses; the markers used
    # to be a dashed cut mark with an angle bracket in it. His own text is the
    # one exception and stays
    # verbatim, and what `%` or `!` in it do to that shim is a first-run
    # reading nothing in this container can take.
    plain = build_prompt("do the thing", "s")
    check("accept/the-prompt-carries-no-character-cmd-would-redirect-on",
          "<" not in plain and ">" not in plain, plain[:160])
    angled = "is a<b or is a>b, in the town's own terms?"
    check("reject/and-the-only-angle-brackets-possible-are-the-ones-he-typed",
          angled in build_prompt(angled, "s")
          and "<" not in build_prompt(angled, "s").replace(angled, "")
          and ">" not in build_prompt(angled, "s").replace(angled, ""),
          build_prompt(angled, "s")[:160])
    rp = repair_prompt("a draft that was refused", "a clause")
    check("accept/and-the-repair-prompt-carries-none-either",
          "<" not in rp and ">" not in rp, rp[:160])

    # The link this file adds is the one the checker allows. Read out of the
    # checker's own source, so the two cannot drift.
    with open(os.path.join(REPO, "tools", "producer-check.py"),
              encoding="utf-8") as fh:
        src = fh.read()
    check("accept/the-link-is-the-one-the-register-allows",
          ('SITE_ORIGIN = "%s"' % SITE_LINK) in src, SITE_LINK)

    # -- the invocation ------------------------------------------------------
    argv = claude_argv("do the thing", 60)
    check("accept/the-invocation-is-the-one-run-night-uses",
          argv[:2] == ["claude", "-p"] and argv[2] == "do the thing"
          and argv[3:5] == ["--max-turns", "60"], argv)
    with open(os.path.join(REPO, "tools", "runner", "run-night.ps1"),
              encoding="utf-8") as fh:
        ps = fh.read()
    check("accept/and-run-night-still-invokes-it-that-way",
          "claude -p $dispatch --max-turns" in ps,
          "run-night.ps1 no longer calls claude the way this file copies")
    check("accept/extra-arguments-are-appended-when-a-file-asks-for-them",
          claude_argv("x", 5, ["--flag"])[-1] == "--flag", "")
    check("accept/and-there-are-none-when-the-file-is-absent",
          cli_extra_args(os.path.join(tmp, "nothing-here")) == [], "")
    args_dir = os.path.join(tmp, "args")
    os.makedirs(args_dir)
    with open(os.path.join(args_dir, CLI_ARGS_FILE), "w") as fh:
        fh.write("# a comment\n--permission-mode\nacceptEdits\n\n")
    check("accept/a-plain-file-on-that-PC-can-add-a-flag-with-no-code-change",
          cli_extra_args(args_dir) == ["--permission-mode", "acceptEdits"],
          cli_extra_args(args_dir))

    # -- A SESSION LIMIT IS NOT A CRASH -------------------------------------
    hit, pattern = looks_like_limit(
        "Claude usage limit reached. Your limit will reset at 3pm.", 1)
    check("accept/a-usage-limit-notice-reads-as-a-limit",
          hit and pattern == "usage-limit-reached", (hit, pattern))
    for notice in ("5-hour limit reached",
                   "You have reached your weekly usage limit",
                   "Out of credit. Upgrade to continue."):
        hit2, p2 = looks_like_limit(notice, 1)
        check("accept/limit-wording-%s-is-recognised" % oneword(notice[:18]),
              hit2, (notice, p2))
    hit3, why3 = looks_like_limit("It crashed with a stack trace.", 1)
    check("reject/an-ordinary-failure-is-NOT-a-limit-and-says-why",
          not hit3 and "no-limit-wording" in why3, why3)
    # A3. EXIT 0 IS NEVER A LIMIT. A short, true, successful answer about
    # limits used to be paused 30, 60, 120, 240 and 240 minutes and closed
    # eleven and a half hours later with a message telling him the allowance
    # on his account had run out. Length was never the disambiguation; the
    # exit code is.
    #
    # CHECKED, NOT ASSUMED: the sentence the ruling names, "You have not
    # reached your usage limit", matches NO pattern in the list today, because
    # `reached-your-limit` wants "reached" straight after "you have" and the
    # "not" breaks it. It is kept as a row because it is the sentence in the
    # record, and the one under it is the load-bearing case: it really does
    # match `usage-limit-reached`, and it answers the question about last
    # night that he is most likely to ask.
    check("reject/the-sentence-in-the-record-is-not-a-limit-on-exit-0",
          looks_like_limit("You have not reached your usage limit.", 0)
          == (False, "it-exited-0-so-a-limit-phrase-is-prose"),
          looks_like_limit("You have not reached your usage limit.", 0))
    true_answer = ("Nothing stopped last night: there is no usage limit "
                   "reached notice anywhere in what it printed.")
    hit4, why4 = looks_like_limit(true_answer, 0)
    check("reject/a-true-short-answer-about-limits-on-exit-0-is-never-a-limit",
          not hit4 and why4 == "it-exited-0-so-a-limit-phrase-is-prose",
          (hit4, why4))
    hit5, why5 = looks_like_limit(
        "Claude usage limit reached. Your limit will reset at 3pm.", 0)
    check("reject/and-even-the-exact-notice-wording-on-exit-0-is-prose",
          not hit5 and "exited-0" in why5, (hit5, why5))
    long_answer = ("The usage limit reached question you asked about is a "
                   "thing the machine says when it runs out. " + "x" * 900)
    hit6, why6 = looks_like_limit(long_answer, 0)
    check("reject/a-long-successful-answer-mentioning-limits-is-not-one-either",
          not hit6 and "exited-0" in why6, why6)
    hit7, _p7 = looks_like_limit(long_answer, 1)
    check("accept/but-the-same-words-on-a-FAILED-exit-are-treated-as-one",
          hit7, "a non-zero exit is the disambiguation")
    hit8, p8 = looks_like_limit(true_answer, 1)
    check("accept/and-that-same-true-sentence-on-a-FAILED-exit-is-one-again",
          hit8 and p8 == "usage-limit-reached", (hit8, p8))

    # -- reading the reset time ---------------------------------------------
    now = 1757000000
    e1, h1 = parse_reset_epoch("resets in 45 minutes", now)
    check("accept/a-relative-reset-time-is-read", e1 == now + 45 * 60, (e1, h1))
    e2, h2 = parse_reset_epoch("limit will reset at 2026-09-06T21:00Z", now)
    check("accept/an-iso-reset-time-is-read", e2 is not None
          and "iso" in h2, (e2, h2))
    e3, h3 = parse_reset_epoch("resets at 3pm (UTC)", now)
    check("accept/a-clock-time-with-a-zone-is-read-in-that-zone",
          e3 is not None and h3 == "clock-time-read-as-utc", (e3, h3))
    check("accept/and-a-clock-time-is-always-in-the-future",
          e3 > now, (e3, now))
    e4, h4 = parse_reset_epoch("something went wrong", now)
    check("reject/no-reset-time-says-so-rather-than-guessing-one",
          e4 is None and "no-reset-time" in h4, h4)
    check("the-limit-ladder-is-30-60-120-240-minutes-and-stops-there",
          [limit_backoff_sec(i) // 60 for i in range(5)]
          == [30, 60, 120, 240, 240],
          [limit_backoff_sec(i) // 60 for i in range(5)])
    w1, y1 = limit_sleep(now + 3600, now, 0)
    check("accept/a-readable-reset-time-is-waited-for-exactly",
          w1 == 3600 and "from-the-reset-time" in y1, (w1, y1))
    w2, y2 = limit_sleep(now - 500, now, 0)
    check("reject/a-reset-time-in-the-past-can-never-become-a-spin",
          w2 == LIMIT_SLEEP_MIN_SEC and "floor" in y2, (w2, y2))
    w3, y3 = limit_sleep(now + 90 * 3600, now, 0)
    check("reject/a-reset-time-days-away-is-clamped-not-obeyed",
          w3 == LIMIT_SLEEP_MAX_SEC and "ceiling" in y3, (w3, y3))
    w4, y4 = limit_sleep(None, now, 2)
    check("accept/no-reset-time-falls-back-to-the-ladder-at-the-right-rung",
          w4 == 120 * 60 and "ladder" in y4, (w4, y4))
    check("accept/a-wait-is-said-in-words-a-phone-can-read",
          human_wait(3 * 3600) == "in about 3 hours"
          and human_wait(20) == "in a minute or so", human_wait(3 * 3600))

    # -- the journal: never twice, and a crash resumes -----------------------
    jpath = os.path.join(tmp, "state", "journal.log")
    j = Journal(jpath)
    check("accept/a-fresh-journal-has-nothing-in-it-and-says-so",
          j.load().counts() == (0, 0, 0) and not j.exists(), j.counts())
    j.append("taken", msg="m1", file="production/inbox/m1.md")
    j.append("answered", msg="m1")
    j.append("taken", msg="m2")
    j.load()
    check("accept/an-answered-instruction-is-never-run-again",
          "m1" in j.handled(), j.handled())
    check("accept/and-one-taken-and-not-closed-is-the-crash-that-resumes",
          j.unclosed() == ["m2"] and "m2" not in j.handled(), j.unclosed())
    j.append("interrupted", msg="m2")
    j.load()
    check("accept/and-once-closed-it-is-never-started-again-either",
          j.unclosed() == [] and j.handled() == {"m1", "m2"}, j.handled())
    handled, answered, seen = j.counts()
    check("accept/the-counts-carry-their-own-denominator",
          (handled, answered, seen) == (2, 1, 2), (handled, answered, seen))
    check("accept/every-journal-value-is-one-word",
          all(" " not in tok.split("=", 1)[1]
              for line in j.lines for tok in line.split()[2:] if "=" in tok),
          j.lines[-1])
    spacey = j.append("note", why="a reason with spaces in it")
    check("accept/and-a-value-with-spaces-in-it-is-made-one-word",
          "why=a_reason_with_spaces_in_it" in spacey, spacey)

    # -- the ownership guard, MECHANICAL --------------------------------------
    raised = False
    try:
        git_call(["status"], REPO)
    except WrongCheckout as e:
        raised = "refuses to run git" in str(e)
    check("reject/git-in-the-watcher-s-checkout-is-REFUSED-by-path", raised,
          "a git command in the repository root was not refused")
    raised2 = False
    try:
        git_call(["status"], os.path.join(REPO, "tools"))
    except WrongCheckout:
        raised2 = True
    check("reject/and-so-is-anywhere-inside-it", raised2, "")
    fake_wt = os.path.join(tmp, "wt")
    os.makedirs(fake_wt)
    rc, _out = git_call(["rev-parse", "--is-inside-work-tree"], fake_wt)
    check("accept/but-a-checkout-this-file-owns-is-allowed-to-run-git",
          rc in (0, 128, 127), rc)

    # -- the lock: one executor, or none --------------------------------------
    lock_dir = os.path.join(tmp, "lock")
    got, whyl = lock_take(lock_dir, now=1000)
    check("accept/the-first-executor-takes-the-lock", got and not whyl, whyl)
    got2, why2 = lock_take(lock_dir, now=1000)
    check("reject/a-second-one-does-not-start-and-names-the-reason",
          not got2 and "another executor" in why2, why2)
    got3, _w3 = lock_take(lock_dir, now=1000 + LOCK_STALE_SEC + 1)
    check("accept/and-a-dead-executor-s-stale-lock-is-taken-over", got3, "")

    # -- the status file, and what the supervisor reads off it ---------------
    st_repo = os.path.join(tmp, "statusrepo")
    os.makedirs(st_repo)
    check("reject/no-status-file-yet-prints-the-words-nothing-measured",
          "nothing measured" in status_sentence(st_repo),
          status_sentence(st_repo))
    write_status(st_repo, {"executor": "idle", "handledTotal": 3,
                           "answeredTotal": 3, "seenTotal": 4,
                           "pendingNow": 0, "cli": "found",
                           "worktree": os.path.join("C:", "a b", "ledger"),
                           "limitResumeIn": "none"})
    line = status_sentence(st_repo)
    check("accept/a-written-status-reads-back-with-both-numbers",
          "3 of 4 instruction(s) handled" in line and "0 waiting" in line,
          line)
    back = read_status(st_repo)
    check("accept/and-a-path-with-a-space-in-it-cannot-cut-a-line-in-half",
          " " not in back.get("worktree", " "), back.get("worktree"))
    write_status(st_repo, {"executor": "paused-on-allowance",
                           "handledTotal": 1, "seenTotal": 2, "pendingNow": 1,
                           "limitResumeIn": "in about 3 hours"})
    check("accept/a-limit-pause-is-visible-in-the-one-line-a-human-reads",
          "PAUSED on the account allowance" in status_sentence(st_repo),
          status_sentence(st_repo))
    write_status(st_repo, {"executor": "idle", "handledTotal": 0,
                           "seenTotal": 0, "pendingNow": 0, "cli": "missing",
                           "limitResumeIn": "none"})
    check("accept/and-a-missing-tool-is-named-rather-than-read-as-idle",
          "claude command is NOT on this PC" in status_sentence(st_repo),
          status_sentence(st_repo))

    # -- reading the inbox: the format comes from the bot's own module -------
    fake_repo = os.path.join(tmp, "inboxrepo")
    os.makedirs(os.path.join(fake_repo, *inbox.INBOX_DIR.split("/")))

    def plant(name, text, epoch, update):
        with open(os.path.join(fake_repo, *inbox.INBOX_DIR.split("/"),
                               name), "w", encoding="utf-8") as fh:
            fh.write(inbox.render_message(text, epoch, update))

    plant(inbox.message_name(1757000100, 22), "second thing", 1757000100, 22)
    plant(inbox.message_name(1757000000, 21), "first thing", 1757000000, 21)
    with open(os.path.join(fake_repo, *inbox.INBOX_DIR.split("/"),
                           "README.md"), "w") as fh:
        fh.write("not a message\n")
    rows = pending_instructions(fake_repo, set())
    check("accept/both-messages-are-found-and-the-README-is-not-one-of-them",
          len(rows) == 2, [r[0] for r in rows])
    check("accept/and-the-oldest-is-taken-first",
          rows[0][2]["text"] == "first thing", rows[0][2])
    rows2 = pending_instructions(fake_repo, {rows[0][0]})
    check("accept/and-a-handled-one-is-never-offered-again",
          len(rows2) == 1 and rows2[0][2]["text"] == "second thing",
          [r[0] for r in rows2])
    check("accept/the-answer-name-carries-the-register-the-sweep-demands",
          outbox.kind_of_name(answer_name(rows[0][0]))[0] == "answer",
          answer_name(rows[0][0]))
    check("accept/and-the-answer-sits-where-the-sweep-actually-looks",
          outbox_rel("x").startswith(outbox.OUTBOX_DIR + "/"),
          outbox_rel("x"))

    # -- the first start skips the backlog, and only the first start ---------
    ex = Executor(repo=fake_repo, worktree=os.path.join(tmp, "wt2"),
                  state=os.path.join(tmp, "state2"))
    n = ex.first_start_backlog()
    ex.journal.load()
    check("accept/a-first-start-records-the-backlog-and-runs-none-of-it",
          n == 2 and ex.journal.handled() == {rows[0][0], rows[1][0]},
          (n, ex.journal.handled()))
    plant(inbox.message_name(1757009999, 23), "a new thing", 1757009999, 23)
    check("accept/and-anything-sent-after-that-is-picked-up",
          [r[2]["text"] for r in
           pending_instructions(fake_repo, ex.journal.handled())]
          == ["a new thing"], "")
    check("reject/a-second-start-does-not-skip-anything",
          ex.first_start_backlog() == 0, "")

    # -- placing the answer: two copies, two different facts -----------------
    stem23 = "2026-09-06T1830Z-23"
    wt = os.path.join(tmp, "wtplace")
    os.makedirs(wt)
    with open(os.path.join(wt, ".git"), "w", encoding="utf-8") as fh:
        fh.write("gitdir: elsewhere\n")   # what a linked worktree carries
    rel, copies, where = place_answer(fake_repo, wt, stem23, "The answer.",
                                      lambda _s: None)
    check("accept/the-answer-is-written-where-the-bot-sweeps",
          os.path.isfile(os.path.join(fake_repo, *rel.split("/")))
          and copies == 2, (rel, copies, where))
    check("accept/and-a-second-copy-goes-where-the-studio-can-read-it",
          os.path.isfile(os.path.join(wt, *rel.split("/"))), rel)
    check("accept/and-the-reading-names-which-copies-exist",
          where == "outbox+worktree", where)
    found = outbox.outbox_files(fake_repo)
    check("accept/and-the-sweep-that-sends-it-finds-exactly-that-file",
          found == [rel], found)

    # A4. A PATH THAT IS NOT A WORKTREE GETS NOTHING WRITTEN INTO IT. Making
    # directories there is exactly what `worktree_ready` refuses for ever
    # after, so one first run in the wrong order (git not yet on PATH, the
    # no-tool note delivered) disabled the worktree permanently and every
    # instruction after it was answered "not set up on this machine yet".
    bare = os.path.join(tmp, "notaworktree")
    os.makedirs(bare)
    rel2, copies2, where2 = place_answer(fake_repo, bare,
                                         "2026-09-06T1831Z-24",
                                         "The answer.", lambda _s: None)
    check("reject/no-worktree-yet-means-one-copy-and-the-reading-says-so",
          copies2 == 1 and "skipped:worktree-does-not-exist-yet" in where2,
          (copies2, where2))
    check("reject/and-not-one-directory-is-created-at-that-path",
          os.listdir(bare) == [], os.listdir(bare))
    check("accept/but-his-own-copy-is-still-written-so-he-still-hears",
          os.path.isfile(os.path.join(fake_repo, *rel2.split("/"))), rel2)
    ok_wt, why_wt = worktree_ready(fake_repo, bare, lambda _s: None)
    check("accept/so-the-worktree-can-still-be-created-there-afterwards",
          ok_wt or "exists-and-is-not-a-worktree" not in why_wt,
          (ok_wt, why_wt))

    # -- A1: ONE NAME CARRIES ONE MESSAGE ------------------------------------
    # `deliver` wrote every message for an instruction to `<stem>.answer.md`,
    # and `outbox.sweep` skips any name whose receipt already exists. So on a
    # real limit: the pause note went, a receipt was written under that name,
    # the session resumed, the answer was written to the same name and WAS
    # NEVER SENT, while the journal said `answered`. He is told it starts
    # again by itself and then hears nothing, ever.
    check("accept/the-message-that-ends-an-instruction-keeps-the-plain-name",
          answer_name(stem23) == stem23 + ".answer.md", answer_name(stem23))
    check("accept/and-a-pause-note-takes-a-name-of-its-own",
          answer_name(stem23, "paused") == stem23 + ".paused.answer.md",
          answer_name(stem23, "paused"))
    check("accept/and-that-name-still-carries-the-answer-register",
          outbox.kind_of_name(answer_name(stem23, "paused"))[0] == "answer",
          outbox.kind_of_name(answer_name(stem23, "paused")))
    check("reject/a-pause-note-can-never-take-the-receipt-the-answer-needs",
          outbox.receipt_rel(outbox_rel(stem23, "paused"))
          != outbox.receipt_rel(outbox_rel(stem23)),
          outbox.receipt_rel(outbox_rel(stem23, "paused")))

    # AND THE SWEEP ITSELF WALKS THE SEQUENCE, with the wire injected and the
    # real register: pause note sent and receipted, then the answer written,
    # and the answer must still be sent. Put both messages back under one name
    # and this row goes red with the answer in `already` and nothing sent.
    sweep_repo = os.path.join(tmp, "sweeprepo")
    os.makedirs(os.path.join(sweep_repo, "tools"))
    for tool in ("producer-check.py", "capsay.py"):
        shutil.copy(os.path.join(REPO, "tools", tool),
                    os.path.join(sweep_repo, "tools", tool))
    place_answer(sweep_repo, os.path.join(tmp, "nowhere"), stem23,
                 fallback_limit(human_wait(3 * 3600)), lambda _s: None,
                 tag="paused")
    sent_ids = []

    def wire(_text):
        sent_ids.append(len(sent_ids) + 1)
        return {"message_id": sent_ids[-1]}

    first = outbox.sweep(sweep_repo, wire)
    check("accept/the-pause-note-is-sent-and-gets-a-receipt-of-its-own",
          first["sent"] == [outbox_rel(stem23, "paused")],
          (first["sent"], first["refused"]))
    place_answer(sweep_repo, os.path.join(tmp, "nowhere"), stem23,
                 compose_answer("The four streets are done and it is holding "
                                "up in the evening light."), lambda _s: None)
    second = outbox.sweep(sweep_repo, wire)
    check("reject/the-answer-after-a-pause-note-is-still-sent-not-skipped",
          second["sent"] == [outbox_rel(stem23)],
          (second["sent"], second["already"], second["refused"]))
    check("accept/and-the-note-already-sent-is-not-sent-a-second-time",
          second["already"] == [outbox_rel(stem23, "paused")],
          second["already"])

    # A1, THE OTHER HALF: the journal may not say `answered` about a message
    # nobody could ever have sent. A file where the outbox directory belongs
    # is how the write is made to fail without touching anything else.
    stuck = os.path.join(tmp, "stuckrepo")
    os.makedirs(os.path.join(stuck, "tools"))
    os.makedirs(os.path.join(stuck, "production"))
    for tool in ("producer-check.py", "capsay.py"):
        shutil.copy(os.path.join(REPO, "tools", tool),
                    os.path.join(stuck, "tools", tool))
    with open(os.path.join(stuck, "production", "outbox"), "w",
              encoding="utf-8") as fh:
        fh.write("a file where the folder belongs\n")
    ex_stuck = Executor(repo=stuck, worktree=os.path.join(tmp, "wt3"),
                        state=os.path.join(tmp, "state3"))
    stuck_rel, stuck_copies = ex_stuck.deliver("2026-09-06T1832Z-25",
                                               fallback_interrupted(),
                                               "interrupted")
    ex_stuck.journal.load()
    check("reject/a-message-that-could-not-be-placed-comes-back-as-nothing",
          stuck_rel is None and stuck_copies == 0,
          (stuck_rel, stuck_copies))
    check("reject/and-the-record-says-nothing-to-send-and-sendable-False",
          any("event=nothing-to-send" in ln for ln in ex_stuck.journal.lines)
          and any("sendable=False" in ln for ln in ex_stuck.journal.lines)
          and not any("sendable=True" in ln for ln in ex_stuck.journal.lines),
          ex_stuck.journal.lines[-2:])

    # -- A5: the record commit carries what he was TOLD, not just that he was
    # told. A real repository, because staging is git's opinion and not this
    # file's. `leftover.txt` is the ci.md rule made a case: stage by name.
    rec_wt = os.path.join(tmp, "recwt")
    os.makedirs(rec_wt)
    rc_init, init_out = git_call(["init", "-q"], rec_wt)
    answer_rel = outbox_rel("2026-09-06T1833Z-26")
    missing_rel = outbox_rel("2026-09-06T1834Z-27")
    full_answer = os.path.join(rec_wt, *answer_rel.split("/"))
    os.makedirs(os.path.dirname(full_answer))
    with open(full_answer, "w", encoding="utf-8") as fh:
        fh.write("What he was told.\n")
    with open(os.path.join(rec_wt, "leftover.txt"), "w",
              encoding="utf-8") as fh:
        fh.write("a previous session's untracked leftover\n")
    ok_rec, detail_rec, staged = commit_record(
        rec_wt, "production/executor/journal.log", "the journal\n",
        "Executor record: a test", lambda _s: None,
        extra_rels=[answer_rel, missing_rel])
    rc_show, shown = git_call(["show", "--name-only", "--format=", "HEAD"],
                              rec_wt)
    in_commit = sorted(ln.strip() for ln in shown.splitlines() if ln.strip())
    check("accept/the-record-commit-carries-the-journal-and-what-he-was-told",
          ok_rec and in_commit == sorted(["production/executor/journal.log",
                                          answer_rel]),
          (rc_init, init_out, ok_rec, detail_rec, in_commit))
    check("accept/and-the-count-says-how-many-files-it-staged",
          staged == 2, staged)
    check("reject/an-answer-that-is-not-in-the-worktree-cannot-be-staged",
          missing_rel not in in_commit, in_commit)
    check("reject/and-no-untracked-leftover-is-ever-swept-into-the-record",
          "leftover.txt" not in in_commit, in_commit)

    # -- A2: the stop file during a limit pause is HONOURED ------------------
    # `sleep_through` always returned False on STOP and the caller threw the
    # value away, so a STOP placed to protect the allowance ended the pause
    # and re-ran the session at once, up to five times.
    pause_repo = os.path.join(tmp, "pauserepo")
    os.makedirs(os.path.join(pause_repo, "production"))
    ex_pause = Executor(repo=pause_repo, worktree=os.path.join(tmp, "wt4"),
                        state=os.path.join(tmp, "state4"))
    go1, whyp1 = ex_pause.wait_for_allowance(0)
    check("accept/a-pause-that-finishes-says-carry-on",
          go1 is True and whyp1 == "the-pause-finished", (go1, whyp1))
    with open(os.path.join(pause_repo, *STOP_REL.split("/")), "w",
              encoding="utf-8") as fh:
        fh.write("stop\n")
    before_stop = time.time()
    go2, whyp2 = ex_pause.wait_for_allowance(6 * 3600)
    check("reject/a-stop-during-a-limit-pause-is-honoured-not-discarded",
          go2 is False and "stop-file" in whyp2
          and time.time() - before_stop < 5, (go2, whyp2))

    # -- the session runner, WITH A REAL PROCESS (not the CLI, the plumbing)
    # The child writes STRAIGHT INTO THE LOG now and the log is read back, so
    # these fixtures hand it the file the way the real spawn does.
    def child(code, cwd, out_fh):
        return subprocess.Popen([sys.executable, "-c", code], cwd=cwd,
                                stdin=subprocess.DEVNULL, stdout=out_fh,
                                stderr=subprocess.STDOUT)

    log = os.path.join(tmp, "logs", "probe.log")
    res = run_session("ignored", tmp, log, spawn=lambda a, c, f: child(
        "import sys; sys.stdout.write('hello from the session'); "
        "sys.exit(0)", c, f))
    check("accept/a-real-child-s-output-is-captured-as-the-answer",
          res["started"] and res["out"] == "hello from the session"
          and res["rc"] == 0, res)
    check("accept/and-the-same-output-is-left-in-a-log-on-that-PC",
          os.path.isfile(log) and open(log).read() == res["out"], log)
    res2 = run_session("ignored", tmp, os.path.join(tmp, "logs", "slow.log"),
                       wall=1, spawn=lambda a, c, f: child(
                           "import time; print('got this far', flush=True); "
                           "time.sleep(60)", c, f))
    check("accept/the-wall-clock-stops-a-session-and-says-it-did",
          res2["timedout"] is True and res2["stopped"] is False, res2)
    check("accept/and-the-answer-is-what-it-got-plus-a-plain-sentence",
          "got this far" in compose_answer(res2["out"], note=TIMEOUT_NOTE)
          and "time limit" in compose_answer(res2["out"], note=TIMEOUT_NOTE),
          res2["out"])
    res3 = run_session("ignored", tmp, os.path.join(tmp, "logs", "no.log"),
                       spawn=lambda a, c, f: (_ for _ in ()).throw(
                           OSError("no such tool")))
    check("reject/a-CLI-that-will-not-start-is-a-named-answer-not-a-crash",
          res3["started"] is False and "would not start" in res3["why"],
          res3)

    # A2. THE HEARTBEAT RUNS WHILE THE SESSION RUNS. It used to be one
    # blocking wait for the whole session, so with a stale window of 135
    # seconds the lock read as DEAD for all but the first two minutes of every
    # session: a second double-click took it, closed the running instruction
    # as interrupted, told him so, and started a second session in the same
    # worktree.
    beats = []
    res4 = run_session("ignored", tmp, os.path.join(tmp, "logs", "beat.log"),
                       wall=3, slice_sec=1, beat=lambda: beats.append(1),
                       spawn=lambda a, c, f: child(
                           "import time; time.sleep(60)", c, f))
    check("accept/a-session-longer-than-one-slice-keeps-beating-the-lock",
          len(beats) >= 2 and res4["timedout"] is True, (len(beats), res4))
    stop_calls = []

    def stop_on_the_second_look():
        stop_calls.append(1)
        return len(stop_calls) >= 2

    res5 = run_session("ignored", tmp, os.path.join(tmp, "logs", "stop.log"),
                       wall=600, slice_sec=1, stop=stop_on_the_second_look,
                       spawn=lambda a, c, f: child(
                           "import time; print('got this far', flush=True); "
                           "time.sleep(600)", c, f))
    check("accept/and-the-stop-file-mid-session-stops-it-and-says-stopped",
          res5["stopped"] is True and res5["timedout"] is False
          and res5["elapsed"] < 60, res5)
    check("accept/and-what-it-had-printed-before-the-stop-is-still-there",
          "got this far" in res5["out"], res5["out"])

    # A6. argv[0] IS THE RESOLVED PATH. `shutil.which` honours PATHEXT and
    # finds an npm `claude.cmd`; `Popen` with the bare name does not, so that
    # install reported the tool FOUND in its status line and answered every
    # instruction with the note saying the tool is not on the machine.
    # UNVERIFIABLE HERE: there is no Windows and no CLI in this container.
    spawned = {}

    def recording_spawn(a, c, f):
        spawned["argv"] = list(a)
        return child("print('ok')", c, f)

    shim = os.path.join(tmp, "npm", "claude.cmd")
    res6 = run_session("do the thing", tmp,
                       os.path.join(tmp, "logs", "which.log"),
                       spawn=recording_spawn, which=lambda _n: shim)
    check("accept/the-session-is-spawned-by-the-path-the-resolver-found",
          spawned.get("argv", [None])[0] == shim, spawned.get("argv"))
    check("accept/and-every-other-argument-is-the-one-run-night-passes",
          spawned.get("argv", [])[1:] == claude_argv("do the thing")[1:],
          spawned.get("argv"))
    res7 = run_session("x", tmp, os.path.join(tmp, "logs", "nocli.log"),
                       which=lambda _n: None)
    check("reject/a-CLI-the-resolver-cannot-find-is-never-spawned",
          res7["started"] is False and "not on PATH" in res7["why"], res7)

    # A1 (ruling 2026-09-09, section 8). THE STOP-HOOK OPT-OUT REACHES THE
    # CHILD. Without it the first Stop of the session answering Jafar's
    # question is blocked by a due daily-brief record and that session is told
    # to write the brief instead: wrong session, wrong work.
    check("accept/the-child-environment-carries-the-stop-hook-opt-out",
          session_env({"PATH": "/x"})[WAKE_DRAIN_ENV] == WAKE_DRAIN_OFF,
          session_env({"PATH": "/x"}))
    check("accept/and-carries-everything-else-it-was-given",
          session_env({"PATH": "/x"})["PATH"] == "/x",
          session_env({"PATH": "/x"}))
    check("accept/and-the-value-is-the-exact-string-the-drain-parses",
          WAKE_DRAIN_OFF == "off" and WAKE_DRAIN_ENV == "WAKE_DRAIN",
          (WAKE_DRAIN_ENV, WAKE_DRAIN_OFF))
    # AND END TO END, THROUGH THE SPAWN PRODUCTION ACTUALLY USES: `spawn` is
    # NOT injected here, so this runs the default closure inside run_session,
    # with a stand-in for the CLI that prints what it was handed. An injected
    # spawn would have proven the fixture and nothing else.
    if os.name != "nt":
        fake_cli = os.path.join(tmp, "fake-claude.sh")
        with open(fake_cli, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("#!/bin/sh\n"
                     "printf 'WAKE_DRAIN=%s\\n' \"${WAKE_DRAIN-(unset)}\"\n")
        os.chmod(fake_cli, 0o755)
        res8 = run_session("do the thing", tmp,
                           os.path.join(tmp, "logs", "wakedrain.log"),
                           which=lambda _n: fake_cli)
        check("accept/the-REAL-spawn-hands-WAKE_DRAIN=off-to-the-child",
              res8["started"] and res8["out"].strip() == "WAKE_DRAIN=off",
              res8)
        check("accept/and-the-journal-reading-is-what-the-child-got",
              res8["wakeDrain"] == WAKE_DRAIN_OFF, res8["wakeDrain"])
    else:
        # A SKIPPED CASE SAYS SO. Silence here would read as a pass.
        print("  NOT RUN on this OS (nothing measured): the end-to-end "
              "opt-out case needs a POSIX shell stand-in for the CLI")
    check("reject/a-session-that-never-started-reports-nothing-measured",
          _not_started("no cli")["wakeDrain"] == NOTHING_MEASURED
          and res7["wakeDrain"] == NOTHING_MEASURED, res7["wakeDrain"])

    print("executor selftest: %d passed, %d failed (of %d case(s))"
          % (len(ok), len(bad), len(ok) + len(bad)))
    return 1 if bad else 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    return Executor().run(once="--once" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
