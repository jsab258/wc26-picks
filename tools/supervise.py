#!/usr/bin/env python3
"""ONE WINDOW. Starts every daemon this PC needs and keeps them running.

    python3 tools/supervise.py             # the loop, started by the .bat
    python3 tools/supervise.py --selftest  # policy only, no processes

WHAT THIS IS. The decision half of "START EVERYTHING.bat". Every choice the
supervisor makes lives here rather than in the .bat, for the reason the rest
of this project's launchers give: there is no Windows in the container this
was written in, so a decision written in cmd.exe ships UNRUN. What is left in
the .bat is find the project, find a python, and hand over.

THE TWO DAEMONS, and the survey that says they are the only two:

  studio-watcher   tools/pc-watcher.py, an infinite loop with a sleep in it
                   (`while True: ... time.sleep(...)`), one pass a minute.
                   It is what does GPU and model work on this machine.
  telegram-bot     tools/runner/telegram-bot.py, an infinite poll loop
                   (`poll_forever`). It is the ONLY process in this
                   repository that sends anything to Jafar's phone, and the
                   only one that reads what he types back.

Everything else with a .bat at the top of the project does a thing and exits:
"UPDATE FROM CLAUDE.bat" pulls and stops, "open-dashboard.bat" rebuilds a
page and stops (its repeat is a Windows scheduled task it registers, not a
process that must stay up), and "RUN THE STRANGER TEST.bat" runs one play
session. None of them is supervised here and none of them needs to be.

WHY THE BOT IS THE URGENT ONE. `production/outbox/` is how a written message
reaches his phone, and the sweep that sends it lives inside the bot's poll
loop (`Bot.sweep_outbox`, called from `poll_forever`). NOTHING ELSE CALLS IT.
`tools/pc-watcher.py` contains no reference to the outbox or to Telegram at
all. So: no bot process on the PC, no message on the phone, whatever is
written and committed here.

THE NUMBERS BELOW ARE NOT MEASURED, and rule 2 means saying so rather than
implying otherwise. Nobody has ever watched either of these daemons crash, so
there is no series to set a bound from. They are chosen to bound the damage of
a crash loop, and every restart PRINTS its interval and its uptime so the
series exists after the first week and the numbers can then be set from it.

WHAT HAS NEVER RUN WHERE IT WAS WRITTEN. The process half: spawning a child,
reading its output, killing it. There is no Windows here, and the container
has no config.local, so the first double-click on the PC is this file's
accepting case, per rule 5b. `--selftest` covers the POLICY (backoff ladder,
the give-up rule, the status strings, the autostart write and its read-back),
which is every decision that can be wrong in a way words cannot show.

IT NEVER READS tools/runner/config.local. It asks whether the file EXISTS and
says only that. The token and the chat id are never opened, never printed and
never passed on, here or anywhere.
"""
import collections
import os
import queue
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RUNNER = os.path.join(HERE, "runner")
if RUNNER not in sys.path:
    sys.path.insert(0, RUNNER)

# --------------------------------------------------------------------------
# THE POLICY NUMBERS. Unmeasured, and named as such above.
# --------------------------------------------------------------------------
#: First wait after a crash, in seconds, then multiplied by BACKOFF_FACTOR.
BACKOFF_FIRST = 5
BACKOFF_FACTOR = 3
#: The ladder stops here: 5, 15, 45, 120, 120, ... A longer wait would only
#: make a recovered daemon take longer to come back.
BACKOFF_CAP = 120

#: A child that stayed up this long did not crash-loop, so the ladder resets
#: to the bottom. It does NOT clear the give-up window: a daemon that dies
#: every six minutes for half an hour is broken, however healthy each stretch
#: looked on its own.
MIN_UPTIME_SEC = 300

#: THE GIVE-UP RULE. N exits inside M seconds and this child is STOPPED, by
#: name, with its own last words quoted. A supervisor that restarts a
#: permanently broken process for ever is worse than one that stops and says
#: so, because the window then reads as healthy while nothing works.
GIVE_UP_AFTER = 5
GIVE_UP_WINDOW_SEC = 1800

#: How often the window repeats what is running. Every state CHANGE prints at
#: once as well, so this is the floor on how stale the window can look, not
#: the only time it speaks.
STATUS_EVERY_SEC = 60

#: The child's own last words, kept so a give-up can quote them. The bot
#: scrubs the token and the chat id out of every line it prints before it
#: prints it, which is what makes echoing a child's output safe here.
LAST_WORDS = 8

#: Where the answer goes for a reader who is not at the keyboard. The window
#: is not a channel anybody but Jafar can read.
STATUS_REL = "game-design/pc-jobs/supervisor-status.txt"

#: Reused, not reinvented: the exact file "START THE STUDIO MACHINE.bat"
#: writes. Same folder AND same name, so there can never be two autostart
#: entries opening two watchers that fight over one git index.
HOOK_NAME = "LEDGER studio machine.bat"
LAUNCHER = "START EVERYTHING.bat"


def backoff_for(step):
    """Seconds to wait before restart number `step` (0-based). Series, not a
    single number: 5, 15, 45, 120, 120, ..."""
    wait = BACKOFF_FIRST * (BACKOFF_FACTOR ** max(0, step))
    return min(BACKOFF_CAP, wait)


# --------------------------------------------------------------------------
# One supervised daemon. No processes in here: this is the part that is
# tested, and the clock is injected so the selftest can drive a week in a
# millisecond.
# --------------------------------------------------------------------------
class Child(object):
    """State and policy for one daemon. `spawn` is injected."""

    def __init__(self, name, what, argv, precondition=None):
        self.name = name
        self.what = what                  # one plain line: what it is for
        self.argv = argv
        self.precondition = precondition  # () -> (ok, why-not) or None
        self.proc = None
        self.started_at = None
        self.state = "starting"           # starting/running/waiting/stopped
        self.starts = 0
        self.failures = 0
        self.last_exit = None
        self.last_why = ""
        self.step = 0                     # position on the backoff ladder
        self.retry_at = 0.0
        self.recent = collections.deque()  # failure instants, newest last
        self.words = collections.deque(maxlen=LAST_WORDS)
        self.gave_up_why = ""

    # -- the two transitions that carry every decision --------------------
    def note_start(self, now):
        self.starts += 1
        self.started_at = now
        self.state = "running"

    def note_exit(self, now, code, detail=""):
        """Record an exit and decide what happens next. Returns one of
        'retry' or 'gaveup', plus the words for the window."""
        up = 0 if self.started_at is None else int(now - self.started_at)
        self.last_exit = code
        self.failures += 1
        self.recent.append(now)
        while self.recent and now - self.recent[0] > GIVE_UP_WINDOW_SEC:
            self.recent.popleft()
        # A LONG RUN RESETS THE LADDER, NOT THE WINDOW.
        if up >= MIN_UPTIME_SEC:
            self.step = 0
        if len(self.recent) >= GIVE_UP_AFTER:
            self.state = "gaveup"
            self.gave_up_why = (
                "it stopped %d time(s) inside %d minute(s), which is the "
                "give-up rule. Last exit code %s, last run lasted %ds.%s"
                % (len(self.recent), GIVE_UP_WINDOW_SEC // 60, code, up,
                   (" Last reason: %s" % detail) if detail else ""))
            return "gaveup", self.gave_up_why
        wait = backoff_for(self.step)
        self.step += 1
        self.retry_at = now + wait
        self.state = "waiting"
        self.last_why = detail
        return "retry", ("stopped with exit code %s after %ds%s. Restart %d "
                         "in %ds." % (code, up,
                                      (" (%s)" % detail) if detail else "",
                                      self.starts + 1, wait))

    def due(self, now):
        return self.state == "waiting" and now >= self.retry_at

    def uptime(self, now):
        if self.state != "running" or self.started_at is None:
            return None
        return int(now - self.started_at)

    # -- what the window says about this one ------------------------------
    def status_line(self, now):
        if self.state == "running":
            state, extra = "RUNNING", "up %s" % human_secs(self.uptime(now))
        elif self.state == "waiting":
            state = "RESTARTING"
            extra = "in %s" % human_secs(max(0, int(self.retry_at - now)))
        elif self.state == "gaveup":
            state, extra = "STOPPED", "given up on"
        else:
            state, extra = "STARTING", "first start"
        return ("  %-16s %-11s %-14s starts %d  stops %d  last exit %s"
                % (self.name, state, extra, self.starts, self.failures,
                   "none" if self.last_exit is None else self.last_exit))

    def key_values(self, now):
        """No spaces inside any value: every reader in this project splits on
        whitespace and truncates silently."""
        return ("%s=%s %sUptimeSec=%s %sStarts=%d %sStops=%d %sLastExit=%s"
                % (self.name, self.state, self.name,
                   "nothing-measured" if self.uptime(now) is None
                   else self.uptime(now),
                   self.name, self.starts, self.name, self.failures,
                   self.name, "none" if self.last_exit is None
                   else self.last_exit))


def human_secs(n):
    if n is None:
        return "not-running"
    if n < 90:
        return "%ds" % n
    if n < 5400:
        return "%dm" % (n // 60)
    return "%dh%02dm" % (n // 3600, (n % 3600) // 60)


# --------------------------------------------------------------------------
# What is waiting to be sent. The at-a-glance half of the send path.
# --------------------------------------------------------------------------
def outbox_counts(repo):
    """(waiting, receipts, refusals, sentence). Every zero ships its
    denominator.

    A count, not a verdict: the bot's own `outbox done:` line is the
    authority, and this only tells the window whether there is anything for it
    to be the authority about.

    THE TWO SUFFIXES ARE ASKED FOR, NOT TYPED. The first version of this
    function looked for ".sent-" in a record name, which is not what
    `outbox.receipt_rel` produces, so it would have printed "0 receipt(s)" for
    ever, including after a send that worked. A counter that cannot move is
    the silent-instrument failure, so the names come from the module that
    writes them and drift is impossible.
    """
    try:
        import inbox as _inbox
        import outbox as _outbox
        files = _outbox.outbox_files(repo)
        records = _inbox.outbound_files(repo)
        stem = "X"
        got = _outbox.receipt_rel(stem + ".md").rsplit("/", 1)[-1]
        receipt_suffix = got[len(stem):]                       # .receipt.txt
        got = _outbox.refusal_rel(stem + ".md", "c").rsplit("/", 1)[-1]
        refusal_mark = got[len(stem):].split("-")[0] + "-"     # .refused-
    except Exception as e:                                    # noqa: BLE001
        return (None, None, None,
                "outbox: could not be counted (%s). The bot's own outbox-done "
                "line is the authority." % type(e).__name__)
    names = [r.rsplit("/", 1)[-1] for r in records]
    receipts = len([n for n in names if n.endswith(receipt_suffix)])
    refusals = len([n for n in names if refusal_mark in n])
    if not files:
        return (0, receipts, refusals,
                "outbox: nothing measured, 0 file(s) in production/outbox, so "
                "there is nothing waiting to send.")
    tail = ""
    if refusals:
        tail = (" %d refusal record(s): those will NOT send until the message "
                "is fixed." % refusals)
    return (len(files), receipts, refusals,
            "outbox: %d message file(s), %d receipt(s) written on this PC. A "
            "message with no receipt has not been sent.%s"
            % (len(files), receipts, tail))


# --------------------------------------------------------------------------
# Start at sign-in. THE SAME FILE the studio machine writes, on purpose.
# --------------------------------------------------------------------------
def install_autostart(startup_dir, repo, launcher=LAUNCHER, hook=HOOK_NAME):
    """(state, why, path). state is 'installed' or 'not-installed'.

    THE EFFECT, NOT THE EXIT CODE: the file is read back, because a redirect
    that wrote nothing reports success and this project has been told a step
    succeeded while it produced an empty file.

    ONE ENTRY, NOT TWO. This writes the same name "START THE STUDIO
    MACHINE.bat" writes, so installing this cannot leave two autostart entries
    opening two watchers that fight over one git index. It REPLACES that hook.
    """
    path = os.path.join(startup_dir, hook)
    if not os.path.isdir(startup_dir):
        return "not-installed", "the Startup folder is not there", path
    body = ("@echo off\r\n"
            "REM  Written by \"%s\". Delete this file to stop the studio\r\n"
            "REM  starting when you sign in. It replaced the entry that\r\n"
            "REM  \"START THE STUDIO MACHINE.bat\" used to write, so that\r\n"
            "REM  only one thing can start the watcher.\r\n"
            "cd /d \"%s\"\r\n"
            "start \"\" \"%s\"\r\n" % (launcher, repo,
                                       os.path.join(repo, launcher)))
    try:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(body)
    except OSError as e:
        return ("not-installed",
                "the Startup folder is there but the file could not be "
                "written (%s)" % type(e).__name__, path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            back = fh.read()
    except OSError as e:
        return ("not-installed",
                "the file was written but could not be read back (%s)"
                % type(e).__name__, path)
    if launcher not in back:
        return ("not-installed",
                "the file was written but does not name the launcher, so it "
                "would start nothing", path)
    return "installed", "none", path


# --------------------------------------------------------------------------
# Bringing the checkout current, ONCE, before any child starts.
# --------------------------------------------------------------------------
def git_env():
    """GIT MUST NEVER OPEN AN EDITOR AND MUST NEVER WAIT FOR A PASSWORD.
    Set on the child as well as in the .bat, because this process spawns git
    itself and an unattended prompt waits for ever."""
    env = dict(os.environ)
    env["GIT_EDITOR"] = "true"
    env["GIT_MERGE_AUTOEDIT"] = "no"
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def resync_once(repo, branch, say, run=None):
    """Make this checkout the branch, once, before anything is spawned.

    WHY IT MUST HAPPEN AND WHY ONLY ONCE. The bot deliberately runs no git,
    so it runs whatever code was on disk when it started, and the outbox sweep
    landed in this repository on 2026-09-06: a bot started from an older
    checkout cannot send anything, however long it stays up. So the checkout
    is made current BEFORE the bot is spawned.

    ONE OWNER PER CONDITION. After this returns, the git index in this
    checkout belongs to the watcher child (`pc-watcher.resync` hard-resets it
    every pass) and this process never touches it again. Two writers on one
    index is the fight that cost this project four days.

    A DISCARD, NOT A MERGE, the same one the watcher makes. Untracked files
    are not touched, which is what keeps the python environment, the meshes
    and the outbound receipts safe.
    """
    run = run or (lambda args: subprocess.run(
        ["git", "--no-pager"] + args, cwd=repo, env=git_env(),
        capture_output=True, text=True, timeout=180))
    try:
        p = run(["fetch", "-q", "origin", branch])
    except Exception as e:                                    # noqa: BLE001
        return False, "could not run git (%s)" % type(e).__name__
    if p.returncode != 0:
        return False, "could not reach GitHub"
    try:
        p = run(["rev-parse", "FETCH_HEAD"])
        sha = (p.stdout or "").strip()
        if p.returncode != 0 or not sha:
            return False, "could not read the branch"
        for op in ("rebase", "merge", "cherry-pick", "am"):
            run([op, "--abort"])
        p = run(["reset", "--hard", sha])
    except Exception as e:                                    # noqa: BLE001
        return False, "could not run git (%s)" % type(e).__name__
    if p.returncode != 0:
        return False, "could not match the branch"
    return True, sha[:8]


# --------------------------------------------------------------------------
# The window
# --------------------------------------------------------------------------
def say(line):
    sys.stdout.write("%s  %s\n" % (time.strftime("%H:%M:%S"), line))
    sys.stdout.flush()


def status_block(children, repo, now):
    out = ["", "  ------------------------------------------------------"
                "-----------"]
    for c in children:
        out.append(c.status_line(now))
    _w, _r, _x, sentence = outbox_counts(repo)
    out.append("  " + sentence)
    running = [c for c in children if c.state == "running"]
    gone = [c for c in children if c.state == "gaveup"]
    down = [c for c in children if c.state not in ("running", "gaveup")]
    # "NOTHING NEEDS YOU" IS SAID ONLY WHEN EVERY DAEMON IS UP. The first
    # version of this line said it whenever nothing had been given up on yet,
    # so a window with one daemon dead read as healthy, which is the failure
    # this block exists to prevent. Caught by looking at the rendered block
    # rather than at the code.
    if not running:
        out.append("  NOTHING IS RUNNING. %d of %d daemon(s) given up on, "
                   "%d still trying." % (len(gone), len(children), len(down)))
    elif gone or down:
        out.append("  %d of %d daemon(s) running.%s%s"
                   % (len(running), len(children),
                      (" GIVEN UP ON: %s."
                       % ", ".join(c.name for c in gone)) if gone else "",
                      (" NOT UP YET: %s."
                       % ", ".join(c.name for c in down)) if down else ""))
    else:
        out.append("  all %d daemon(s) running. Nothing needs you."
                   % len(children))
    out.append("  -------------------------------------------------------"
               "----------")
    return "\n".join(out)


def write_status_file(repo, children, now, autostart, resync):
    """The same answer where somebody who is not at the keyboard can read it.
    Untracked, so the watcher's hard reset cannot delete it."""
    path = os.path.join(repo, *STATUS_REL.split("/"))
    waiting, receipts, refusals, _s = outbox_counts(repo)
    lines = ["supervisor=running",
             "daemons=%d" % len(children),
             "running=%d" % len([c for c in children
                                 if c.state == "running"]),
             "gaveUp=%d" % len([c for c in children if c.state == "gaveup"]),
             "autostart=%s" % autostart,
             "resync=%s" % resync,
             "outboxFiles=%s" % ("unreadable" if waiting is None else waiting),
             "outboxReceipts=%s" % ("unreadable" if receipts is None
                                    else receipts),
             "outboxRefusals=%s" % ("unreadable" if refusals is None
                                    else refusals),
             "written=%s" % time.strftime("%Y-%m-%dT%H:%M:%S")]
    for c in children:
        lines.append(c.key_values(now))
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
    except OSError:
        pass


# --------------------------------------------------------------------------
# The process half. NEVER RUN WHERE IT WAS WRITTEN.
# --------------------------------------------------------------------------
def pick_python(repo, want_voice):
    """The voice environment for the watcher when it is there, this
    interpreter otherwise. Same ORDER and same reason as
    "START THE STUDIO MACHINE.bat": the voice jobs import torch and fail on
    any other interpreter, and the prop and picture jobs are stdlib only."""
    if want_voice:
        cand = os.path.join(repo, "tools", "voice-live", "env-export",
                            "Scripts", "python.exe")
        if os.path.isfile(cand):
            return cand, True
    return sys.executable, False


def config_present(repo):
    """EXISTENCE ONLY. This function never opens the file, so nothing it
    returns can carry any part of the token or the chat id."""
    return os.path.isfile(os.path.join(repo, "tools", "runner",
                                       "config.local"))


def make_children(repo):
    watcher_py, voice = pick_python(repo, True)
    any_py, _ = pick_python(repo, False)

    def bot_ok():
        if config_present(repo):
            return True, ""
        return False, ("tools/runner/config.local is not on this PC, so the "
                       "bot has nothing to log in with. Nothing about what is "
                       "in that file is read or printed here.")

    return [
        Child("studio-watcher",
              "does the GPU and model work this PC is for",
              [watcher_py, os.path.join(repo, "tools", "pc-watcher.py")]),
        Child("telegram-bot",
              "the ONLY thing that sends to your phone and reads your replies",
              [any_py, os.path.join(repo, "tools", "runner",
                                    "telegram-bot.py")],
              precondition=bot_ok),
    ], voice


def spawn(child, repo):
    child.proc = subprocess.Popen(
        child.argv, cwd=repo, env=git_env(),
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, errors="replace", bufsize=1)
    return child.proc


def drain(children, q, echo=True, cap=200):
    """Move whatever the children have said into their own last-words buffer,
    and onto the window. Returns how many lines moved.

    THE CAP ANNOUNCES ITSELF. A child that floods would otherwise starve the
    liveness check in the same loop, and a silent cap here would read as a
    quiet daemon.
    """
    moved = 0
    by_name = dict((c.name, c) for c in children)
    while moved < cap:
        try:
            name, line = q.get_nowait()
        except queue.Empty:
            return moved
        moved += 1
        c = by_name.get(name)
        if c is not None:
            c.words.append(line)
        if echo:
            print("  [%s] %s" % (name, line))
    if echo:
        print("  (%d line(s) shown this pass, the cap; more are still "
              "queued and will print next pass)" % cap)
    return moved


def pump(child, q):
    try:
        for line in child.proc.stdout:
            q.put((child.name, line.rstrip("\r\n")))
    except Exception:                                         # noqa: BLE001
        pass


def run():
    repo = REPO
    try:
        import inbox as _inbox
        branch = _inbox.WORK_BRANCH
    except Exception:                                         # noqa: BLE001
        branch = "claude/game-dev-ai-automation-2h67ix"

    print("")
    print("  LEDGER supervisor. One window, every daemon, restarted when it")
    print("  stops. Minimise it; do not close it.")
    print("  project : %s" % repo)
    print("")

    ok, detail = resync_once(repo, branch, say)
    resync = "ok/%s" % detail if ok else "failed/%s" % detail.replace(" ", "_")
    if ok:
        say("checkout brought up to date at %s. Nothing below runs older "
            "code." % detail)
    else:
        say("COULD NOT UPDATE THE CHECKOUT (%s). Everything below still "
            "starts, running the code already on this PC. If the bot behaves "
            "like an older version, that is why." % detail)

    startup = os.path.join(os.environ.get("APPDATA", ""), "Microsoft",
                           "Windows", "Start Menu", "Programs", "Startup")
    auto, why, hook = install_autostart(startup, repo)
    print("")
    print("  ============================================================")
    if auto == "installed":
        print("  STARTS AT SIGN-IN: YES, read back from the file rather than")
        print("  assumed. It replaced the entry the studio machine used to")
        print("  write, so only one thing starts the watcher.")
        print("    %s" % hook)
        print("  Delete that one file to stop it. No admin was needed.")
        print("  It starts when you SIGN IN, not when the PC boots.")
    else:
        print("  STARTS AT SIGN-IN: NO. This run is start-once only.")
        print("    reason: %s" % why)
        print("  Everything below works while this window is open. If the PC")
        print("  restarts, double-click the file again.")
        print("  SEND BACK: this box. It is the only thing that says which")
        print("  of the two happened.")
    print("  ============================================================")
    print("")
    if not config_present(repo):
        say("tools/runner/config.local is NOT on this PC. The Telegram bot "
            "cannot start without it and nothing else is affected. Nothing "
            "in that file is read or printed by this window.")

    children, voice = make_children(repo)
    if not voice:
        say("note: the watcher is NOT running under the voice environment, "
            "so voice jobs will fail on an import. Prop and picture jobs are "
            "stdlib only and will run.")
    for c in children:
        say("%s: %s" % (c.name, c.what))

    q = queue.Queue()
    now = time.time()
    for c in children:
        start_child(c, repo, q, now)
    last_status = 0.0
    try:
        while True:
            now = time.time()
            drain(children, q)
            sys.stdout.flush()
            changed = False
            for c in children:
                if c.state == "running" and c.proc is not None \
                        and c.proc.poll() is not None:
                    what, words = c.note_exit(now, c.proc.returncode)
                    changed = True
                    if what == "gaveup":
                        announce_giveup(c)
                    else:
                        say("%s %s" % (c.name, words))
                    c.proc = None
                elif c.due(now):
                    start_child(c, repo, q, now)
                    changed = True
            if changed or now - last_status >= STATUS_EVERY_SEC:
                print(status_block(children, repo, now))
                write_status_file(repo, children, now, auto, resync)
                last_status = now
            time.sleep(1)
    except KeyboardInterrupt:
        say("stopping every daemon, because this window is closing.")
        for c in children:
            if c.proc is not None:
                try:
                    c.proc.terminate()
                except Exception:                             # noqa: BLE001
                    pass
        return 0


def start_child(child, repo, q, now):
    if child.precondition is not None:
        ok, why = child.precondition()
        if not ok:
            what, words = child.note_exit(now, "not-startable", why)
            if what == "gaveup":
                announce_giveup(child)
            else:
                say("%s cannot start: %s Retrying: %s"
                    % (child.name, why, words))
            return
    try:
        spawn(child, repo)
    except OSError as e:
        what, words = child.note_exit(now, "could-not-spawn",
                                      type(e).__name__)
        if what == "gaveup":
            announce_giveup(child)
        else:
            say("%s would not start (%s). %s" % (child.name,
                                                 type(e).__name__, words))
        return
    child.note_start(now)
    say("%s started (start number %d)." % (child.name, child.starts))
    t = threading.Thread(target=pump, args=(child, q), daemon=True)
    t.start()


def announce_giveup(child):
    print("")
    print("  ***********************************************************")
    print("  GIVEN UP ON: %s" % child.name)
    print("  what it was for: %s" % child.what)
    print("  why: %s" % child.gave_up_why)
    print("  It will NOT be restarted again by this window. Everything")
    print("  else here keeps running.")
    if child.words:
        print("  Its own last words, exactly as it printed them:")
        for w in child.words:
            print("    %s" % w)
    else:
        print("  It printed nothing at all before stopping, which is itself")
        print("  the finding: it did not get as far as saying anything.")
    print("  SEND THIS BOX TO CLAUDE. It contains nothing secret: the bot")
    print("  removes the token and the chat id from every line it prints.")
    print("  To try again, close this window and double-click %s" % LAUNCHER)
    print("  ***********************************************************")
    print("")
    sys.stdout.flush()


# --------------------------------------------------------------------------
# Selftest: the policy, accepting case first.
# --------------------------------------------------------------------------
def selftest():
    ok, bad = [], []

    def check(name, cond, detail=""):
        (ok if cond else bad).append(name)
        print("  %-6s %s%s" % ("ok" if cond else "FAILED", name,
                               "" if cond else "  <- %s" % (detail,)))

    # ACCEPTING CASE FIRST: a daemon that stays up is never given up on and
    # is never restarted.
    c = Child("accepting", "stays up", ["true"])
    c.note_start(0)
    check("accept/a-daemon-that-stays-up-is-left-alone",
          c.state == "running" and c.uptime(3600) == 3600
          and not c.due(3600), c.state)
    check("accept/and-its-status-line-says-running",
          "RUNNING" in c.status_line(3600)
          and "up 60m" in c.status_line(3600), c.status_line(3600))

    # One crash: restarted, on the bottom of the ladder.
    c2 = Child("one-crash", "crashes once", ["false"])
    c2.note_start(0)
    what, words = c2.note_exit(10, 1)
    check("accept/one-crash-is-a-restart-not-a-give-up",
          what == "retry" and c2.state == "waiting"
          and c2.retry_at == 10 + BACKOFF_FIRST, (what, c2.retry_at))
    check("accept/and-the-restart-is-due-when-the-wait-is-up",
          not c2.due(10 + BACKOFF_FIRST - 1) and c2.due(10 + BACKOFF_FIRST),
          c2.retry_at)
    check("accept/the-restart-line-names-the-exit-code-and-the-wait",
          "exit code 1" in words and "in 5s" in words, words)

    # The ladder is a series, and it is capped.
    check("the-backoff-ladder-is-5-15-45-120-and-stops-there",
          [backoff_for(i) for i in range(5)] == [5, 15, 45, 120, 120],
          [backoff_for(i) for i in range(5)])

    # THE REJECTING CASE: crash-loop, planted, and the bound is not loosened.
    c3 = Child("loop", "crashes for ever", ["false"])
    outcomes = []
    t = 0.0
    for _ in range(GIVE_UP_AFTER):
        c3.note_start(t)
        t += 1
        outcomes.append(c3.note_exit(t, 3)[0])
        t = max(t, c3.retry_at)
    check("reject/give-up-fires-on-the-Nth-failure-and-not-before",
          outcomes[:-1] == ["retry"] * (GIVE_UP_AFTER - 1)
          and outcomes[-1] == "gaveup", outcomes)
    check("reject/and-the-reason-names-the-count-the-window-and-the-code",
          "5 time(s)" in c3.gave_up_why and "30 minute(s)" in c3.gave_up_why
          and "exit code 3" in c3.gave_up_why, c3.gave_up_why)
    check("reject/and-a-given-up-child-is-never-due-again",
          not c3.due(t + 10 ** 6) and "STOPPED" in c3.status_line(t),
          c3.status_line(t))

    # A daemon that runs a long time between crashes resets the LADDER but
    # still trips the give-up rule, which is the slow crash loop.
    c4 = Child("slow", "dies every ten minutes", ["false"])
    c4.note_start(0)
    c4.note_exit(MIN_UPTIME_SEC + 1, 1)
    check("accept/a-long-run-resets-the-ladder-to-the-bottom",
          c4.step == 1 and c4.retry_at == MIN_UPTIME_SEC + 1 + BACKOFF_FIRST,
          (c4.step, c4.retry_at))

    # The window's own strings.
    kids = [Child("a", "x", ["true"]), Child("b", "y", ["true"])]
    kids[0].note_start(0)
    kids[1].note_start(0)
    block = status_block(kids, REPO, 30)
    check("accept/all-up-says-so-and-only-then-says-nothing-needs-you",
          "all 2 daemon(s) running" in block
          and "Nothing needs you" in block, block)
    kids[1].state = "waiting"
    check("reject/one-daemon-down-never-reads-as-nothing-needs-you",
          "Nothing needs you" not in block_of(kids, 30)
          and "NOT UP YET: b" in block_of(kids, 30), block_of(kids, 30))
    kids[1].state = "gaveup"
    check("reject/and-names-the-one-it-gave-up-on",
          "GIVEN UP ON: b" in block_of(kids, 30), block_of(kids, 30))
    kids[0].state = "gaveup"
    check("reject/and-says-NOTHING-IS-RUNNING-when-that-is-true",
          "NOTHING IS RUNNING" in block_of(kids, 30), block_of(kids, 30))

    # No spaces inside a key=value value, because every reader here splits on
    # whitespace and truncates silently.
    kv = kids[0].key_values(30)
    check("every-key-value-value-is-one-word",
          all("=" in tok and " " not in tok for tok in kv.split()), kv)

    # The outbox counter, against this repository, which is the accepting
    # fixture: it has messages in it right now.
    waiting, receipts, refusals, sentence = outbox_counts(REPO)
    check("accept/the-outbox-counter-reads-this-repository",
          waiting is not None and waiting >= 1, (waiting, receipts))
    check("accept/and-a-count-with-no-receipt-says-so-in-words",
          "has not been sent" in sentence, sentence)
    empty = os.path.join(REPO, "tools", "runner", "__pycache__")
    w2, _r2, _x2, s2 = outbox_counts(empty)
    check("reject/an-empty-outbox-prints-the-words-nothing-measured",
          w2 == 0 and "nothing measured" in s2, s2)

    import tempfile
    tmp = tempfile.mkdtemp()
    import inbox as _inbox
    import outbox as _outbox
    planted = os.path.join(tmp, "counted")
    msg = "%s/2026-09-06-planted.unprompted.md" % _outbox.OUTBOX_DIR
    os.makedirs(os.path.dirname(os.path.join(planted, *msg.split("/"))))
    open(os.path.join(planted, *msg.split("/")), "w").write("body\n")
    w3, r3, x3, s3 = outbox_counts(planted)
    check("accept/a-message-with-no-record-counts-as-waiting-and-unsent",
          (w3, r3, x3) == (1, 0, 0) and "has not been sent" in s3,
          (w3, r3, x3))
    for rel in (_outbox.receipt_rel(msg),
                _outbox.refusal_rel("%s/other.unprompted.md"
                                    % _outbox.OUTBOX_DIR, "a clause")):
        full = os.path.join(planted, *rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, "w").write("x\n")
    w4, r4, x4, s4 = outbox_counts(planted)
    check("accept/a-PLANTED-receipt-is-counted-so-the-counter-can-move",
          (r4, x4) == (1, 1) and w4 == 1, (w4, r4, x4))
    check("accept/and-a-refusal-is-named-as-something-that-will-not-send",
          "will NOT send" in s4, s4)

    # Autostart: written, read back, and the failure case named.
    good = os.path.join(tmp, "Startup")
    os.makedirs(good)
    state, why, path = install_autostart(good, tmp)
    check("accept/autostart-is-installed-and-verified-by-reading-it-back",
          state == "installed" and why == "none" and os.path.isfile(path),
          (state, why))
    body = open(path, encoding="utf-8").read()
    check("accept/and-the-entry-calls-the-launcher-in-the-project",
          LAUNCHER in body and tmp in body, body[:120])
    check("accept/and-it-uses-the-name-the-studio-machine-already-writes",
          os.path.basename(path) == HOOK_NAME, path)
    state2, why2, _p = install_autostart(os.path.join(tmp, "nope"), tmp)
    check("reject/a-missing-startup-folder-is-not-installed-and-says-why",
          state2 == "not-installed" and "not there" in why2, why2)

    # config.local: EXISTENCE ONLY, proved rather than asserted. The
    # fixture is synthetic, in a temporary directory, and carries a sentinel
    # that exists nowhere else; if any answer this module gives ever carries
    # it, the file was opened.
    fake = os.path.join(tmp, "fakerepo", "tools", "runner")
    os.makedirs(fake)
    sentinel = "SUPERVISE-SELFTEST-SENTINEL-NOT-A-REAL-CREDENTIAL"
    with open(os.path.join(fake, "config.local"), "w", encoding="utf-8") as fh:
        fh.write("TELEGRAM_TOKEN=%s\nCHAT_ID=%s\n" % (sentinel, sentinel))
    fakerepo = os.path.join(tmp, "fakerepo")
    check("accept/a-present-config-local-reads-as-present",
          config_present(fakerepo) is True, config_present(fakerepo))
    kid, _v = make_children(fakerepo)
    bot = [c for c in kid if c.name == "telegram-bot"][0]
    said = [bot.what, bot.status_line(0), bot.key_values(0),
            str(bot.precondition()), " ".join(bot.argv),
            status_block(kid, fakerepo, 0)]
    check("accept/and-nothing-this-module-says-carries-what-is-inside-it",
          not any(sentinel in t for t in said),
          "a value from config.local reached an output string")
    check("reject/an-absent-config-local-stops-the-bot-and-names-the-file",
          config_present(REPO) is False
          and "config.local is not on this PC"
          in make_children(REPO)[0][1].precondition()[1],
          make_children(REPO)[0][1].precondition())

    # THE PROCESS HALF, WITH REAL PROCESSES. Not the Windows specifics, but
    # spawn, capture, notice the exit, and restart are the same code path on
    # both, and they were the part that had never run anywhere at all.
    q = queue.Queue()
    live = Child("probe", "says one line and exits 7",
                 [sys.executable, "-c",
                  "import sys; print('probe line'); "
                  "print(len(sys.stdin.read())); sys.exit(7)"])
    start_child(live, REPO, q, time.time())
    check("accept/a-real-child-is-spawned-and-reads-as-running",
          live.state == "running" and live.proc is not None, live.state)
    waited = 0.0
    while live.proc.poll() is None and waited < 20:
        time.sleep(0.05)
        waited += 0.05
    time.sleep(0.3)
    moved = drain([live], q, echo=False)
    check("accept/its-output-is-captured-into-its-own-last-words",
          moved >= 1 and "probe line" in list(live.words), list(live.words))
    check("accept/and-its-stdin-is-closed-so-a-pause-cannot-hang-for-ever",
          "0" in list(live.words), list(live.words))
    check("accept/the-real-exit-code-is-noticed-and-carried",
          live.proc.poll() == 7, live.proc.poll())
    what, words = live.note_exit(time.time(), live.proc.returncode)
    check("accept/and-a-real-exit-schedules-a-real-restart",
          what == "retry" and "exit code 7" in words, words)

    # A child that cannot be spawned at all is a failure with a NAME, not a
    # traceback out of the supervisor.
    ghost = Child("ghost", "does not exist",
                  [os.path.join(REPO, "no-such-program-at-all")])
    start_child(ghost, REPO, queue.Queue(), 0)
    check("reject/an-unspawnable-child-is-a-counted-failure-not-a-crash",
          ghost.state == "waiting" and ghost.failures == 1
          and ghost.last_exit == "could-not-spawn", ghost.state)

    # THE SHAPE `ledger/verify.py:TOOL_COUNT_RE` READS. A tool that stops
    # printing it goes RED there rather than silently passing, which is the
    # point: this suite is in that table, so it runs at every commit rather
    # than once, by hand, by whoever wrote it.
    print("supervise selftest: %d passed, %d failed (of %d case(s))"
          % (len(ok), len(bad), len(ok) + len(bad)))
    return 1 if bad else 0


def block_of(kids, now):
    return status_block(kids, REPO, now)


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    sys.exit(run())
