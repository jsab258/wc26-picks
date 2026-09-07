#!/usr/bin/env python3
"""THE ONE DOOR EVERY LAUNCH OF THE SUPERVISOR GOES THROUGH.

    python3 tools/runner/launch-supervisor.py <who>
    python3 tools/runner/launch-supervisor.py --selftest

WHY THIS EXISTS. Ruling 2026-09-07 installs tools/supervise.py as a Windows
scheduled task so it survives a closed window and a reboot, and names the
consequence directly: once that task exists there are THREE doors that can
each try to start a supervisor at the same moment - the scheduled task at
logon, the "LEDGER studio machine.bat" Startup entry tools/supervise.py
writes on every one of its own starts, and Jafar double-clicking
"START EVERYTHING.bat". This file is what all three call instead of
tools/supervise.py directly, so all three share ONE lock
(tools/runner/single_instance.py) and only one supervisor is ever actually
running. `<who>` names which door called, purely for the words in a refusal.

A REFUSED LAUNCH IS NOT SILENT. It prints why, and appends the same
sentence to game-design/pc-jobs/supervisor-refused.txt, beside
tools/supervise.py's own status file, so a reader who is not at the
keyboard can tell "a second launch was safely refused" from "the supervisor
never started at all" - two facts a closed window would otherwise make
look identical.

NEVER REWRITES tools/supervise.py. This wraps it, unmodified, as a CHILD
PROCESS (never `os.exec*`, which Python only simulates on Windows by
spawning a new process and exiting the old one - that would swap the pid
holding the lock out from under it mid-run) and forwards its exit code
unchanged, so nothing about restart-on-failure - the scheduled task's or
Windows' own - is any different from watching tools/supervise.py directly.

B2, FOUND ON REVIEW: UNDER pythonw.exe, sys.stdout AND sys.stderr ARE
None. The installer picks pythonw.exe deliberately, so no console opens
(the whole point of a headless task); CPython's own response to that is to
set sys.stdout, sys.stderr and sys.stdin to None on a windowless
interpreter, because there is no console to write a Python-level stream
to. `print(...)` and `sys.stdout.write(...)` both raise on their very
first call against None, in THIS process and, if left to inherit the same
None handles the ordinary way, in tools/supervise.py the moment it prints
its own banner. Task Scheduler would then restart a process that dies on
line one, once a minute, for ever, while `install-scheduled-task.ps1`'s
own read-back still reports taskExists=True: silence, reported as success,
exactly the failure ruling 2026-09-07 exists to end. So every line this
file prints, and every line tools/supervise.py's child process prints,
goes to a real file this module opens itself
(game-design/pc-jobs/launch-supervisor.log) rather than to whatever
sys.stdout happens to be - which under a console IS mirrored there too,
but is never assumed to exist.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import single_instance                                        # noqa: E402

LOCK_REL = os.path.join("game-design", "pc-jobs", "supervisor.lock")
REFUSED_REL = os.path.join("game-design", "pc-jobs", "supervisor-refused.txt")
LOG_REL = os.path.join("game-design", "pc-jobs", "launch-supervisor.log")


def open_log(repo):
    """A real, writable file, never None - the fix for B2. Falls back to a
    temp file only if the usual path cannot even be created, so a launch
    still has SOME channel rather than crashing on the first write either
    way. Returns (file object, path actually used)."""
    path = os.path.join(repo, LOG_REL)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return open(path, "a", encoding="utf-8", newline="\n"), path
    except OSError:
        import tempfile
        fd, fallback = tempfile.mkstemp(prefix="launch-supervisor-",
                                        suffix=".log")
        os.close(fd)
        return open(fallback, "a", encoding="utf-8", newline="\n"), fallback


def say(log, line):
    """Writes to `log`, always. Mirrors to a console too, but ONLY when one
    exists: under pythonw.exe sys.stdout is None (B2), and print() raises
    on a None stream on its very first call, so that mirror is never
    assumed."""
    stamped = "%s  %s" % (time.strftime("%H:%M:%S"), line)
    log.write(stamped + "\n")
    log.flush()
    if sys.stdout is not None:
        try:
            print(stamped)
        except Exception:                                     # noqa: BLE001
            pass


def record_refusal(repo, line):
    """Append-only, so a reader sees every refusal that happened, not only
    the last one - the same reason tools/supervise.py's own status file
    prints a series rather than a single number where rule 2 applies."""
    path = os.path.join(repo, REFUSED_REL)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def main(repo, who, spawn=None):
    """`spawn` is injected so --selftest never actually runs
    tools/supervise.py; production always passes None and gets the real
    subprocess call, with the child's stdout AND stderr pointed at the same
    log file this process writes to (B2) rather than inherited - inherited
    would carry forward the None that pythonw.exe hands this very process,
    and tools/supervise.py's own first print would crash on it."""
    log, log_path = open_log(repo)
    try:
        lock = os.path.join(repo, LOCK_REL)
        ok, why = single_instance.acquire(lock, who=who)
        if not ok:
            line = ("REFUSED: %s did not start a second supervisor: %s"
                    % (who, why))
            say(log, line)
            record_refusal(repo, "%s  %s"
                           % (time.strftime("%Y-%m-%dT%H:%M:%S"), line))
            return 0
        say(log, "lock acquired (%s), starting tools/supervise.py, output "
                 "going to %s" % (who, log_path))
        supervise = os.path.join(repo, "tools", "supervise.py")
        if spawn is not None:
            return spawn([sys.executable, supervise], repo, log)
        proc = subprocess.run([sys.executable, supervise], cwd=repo,
                              stdin=subprocess.DEVNULL,
                              stdout=log, stderr=log)
        return proc.returncode
    finally:
        try:
            log.close()
        except Exception:                                     # noqa: BLE001
            pass


# --------------------------------------------------------------------------
# Selftest: the door's own policy, never the real supervisor.
# --------------------------------------------------------------------------
def selftest():
    import tempfile

    ok, bad = [], []

    def check(name, cond, detail=""):
        (ok if cond else bad).append(name)
        print("  %-6s %s%s" % ("ok" if cond else "FAILED", name,
                               "" if cond else "  <- %s" % (detail,)))

    tmp = tempfile.mkdtemp()

    calls = []

    def fake_spawn(argv, cwd, log):
        calls.append((argv, cwd))
        log.write("fake-spawn-ran\n")
        return 0

    # ACCEPTING CASE: the lock is free, so this door starts the supervisor.
    rc = main(tmp, "accept-door", spawn=fake_spawn)
    check("accept/a-free-lock-starts-the-supervisor-and-returns-its-code",
          rc == 0 and len(calls) == 1, (rc, calls))
    check("accept/the-spawned-command-names-supervise-py",
          calls[0][0][-1].endswith(os.path.join("tools", "supervise.py")),
          calls[0])
    check("accept/nothing-is-written-to-the-refusal-log-on-a-clean-start",
          not os.path.exists(os.path.join(tmp, REFUSED_REL)), "file present")
    log_text = open(os.path.join(tmp, LOG_REL), encoding="utf-8").read()
    check("accept/the-log-file-carries-the-lock-acquired-line",
          "lock acquired" in log_text, log_text)

    # REJECTING CASE: a live process already holds the lock (the real
    # subprocess single_instance's own selftest already proves the liveness
    # check on; this proves THIS module refuses to spawn a second one and
    # SAYS SO in the refusal log, which is the half this file adds).
    lock = os.path.join(tmp, LOCK_REL)
    os.makedirs(os.path.dirname(lock), exist_ok=True)
    with open(lock, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("pid=%d\nwho=planted\n" % os.getpid())
    calls2 = []
    rc2 = main(tmp, "reject-door",
              spawn=lambda a, c, log: calls2.append((a, c)))
    check("reject/a-lock-held-by-a-live-pid-refuses-to-spawn-a-second-one",
          rc2 == 0 and calls2 == [], (rc2, calls2))
    refused_path = os.path.join(tmp, REFUSED_REL)
    check("reject/and-the-refusal-is-appended-to-a-file-a-closed-window-"
          "cannot-hide", os.path.isfile(refused_path)
          and "reject-door" in open(refused_path, encoding="utf-8").read(),
          refused_path)

    # TWO REFUSALS IN A ROW BOTH LAND: append, never overwrite, so a reader
    # who was not at the keyboard sees the count.
    main(tmp, "reject-door-again",
        spawn=lambda a, c, log: calls2.append((a, c)))
    lines = [l for l in
            open(refused_path, encoding="utf-8").read().splitlines() if l]
    check("accept/repeated-refusals-accumulate-rather-than-overwrite",
          len(lines) == 2, lines)

    # B2, THE REVIEWED FAULT: sys.stdout MONKEYPATCHED TO None, ON BOTH
    # PATHS, ACCEPTING CASE FIRST. Restored in a finally around EACH call,
    # never around the whole test function - a check() print after a leaked
    # None would take the rest of this selftest down with it.
    tmp2 = tempfile.mkdtemp()
    saved_stdout = sys.stdout
    calls3 = []
    sys.stdout = None
    try:
        rc3 = main(tmp2, "accept-door-nostdout",
                  spawn=lambda a, c, log: calls3.append((a, c)) or 0)
    finally:
        sys.stdout = saved_stdout
    check("accept/a-None-sys-stdout-does-not-raise-on-the-accepting-path",
          rc3 == 0 and len(calls3) == 1, (rc3, calls3))
    log_text2 = open(os.path.join(tmp2, LOG_REL), encoding="utf-8").read()
    check("accept/and-the-lock-acquired-line-still-reached-the-log-file",
          "lock acquired" in log_text2, log_text2)

    lock2 = os.path.join(tmp2, LOCK_REL)
    with open(lock2, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("pid=%d\nwho=planted\n" % os.getpid())
    calls4 = []
    sys.stdout = None
    try:
        rc4 = main(tmp2, "reject-door-nostdout",
                  spawn=lambda a, c, log: calls4.append((a, c)))
    finally:
        sys.stdout = saved_stdout
    check("reject/a-None-sys-stdout-does-not-raise-on-the-refusing-path",
          rc4 == 0 and calls4 == [], (rc4, calls4))
    check("reject/the-refusal-still-reached-the-refusal-file-with-None-"
          "stdout", "reject-door-nostdout" in
          open(os.path.join(tmp2, REFUSED_REL), encoding="utf-8").read(),
          "refusal file")

    # THE REAL CASE B2 NAMES: a REAL child process, spawned with the
    # PARENT'S sys.stdout set to None, exactly what pythonw.exe hands this
    # module in production. No fake spawn here - this proves the child's
    # OWN print() lands in the log file rather than crashing on an
    # inherited None, which a faked spawn could never show.
    real_repo = os.path.join(tmp, "realrepo")
    os.makedirs(os.path.join(real_repo, "tools"), exist_ok=True)
    stand_in = os.path.join(real_repo, "tools", "supervise.py")
    with open(stand_in, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("import sys\n"
                 "print('child alive, sys.stdout is', sys.stdout)\n"
                 "sys.exit(0)\n")
    sys.stdout = None
    try:
        rc5 = main(real_repo, "real-child-nostdout")
    finally:
        sys.stdout = saved_stdout
    check("accept/a-real-child-process-runs-under-a-None-parent-stdout-"
          "without-raising", rc5 == 0, rc5)
    real_log = open(os.path.join(real_repo, LOG_REL),
                    encoding="utf-8").read()
    check("accept/the-real-childs-own-print-landed-in-the-log-file",
          "child alive" in real_log, real_log)

    print("launch-supervisor selftest: %d passed, %d failed (of %d case(s))"
          % (len(ok), len(bad), len(ok) + len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    who = sys.argv[1] if len(sys.argv) > 1 else "unnamed-caller"
    sys.exit(main(REPO, who))
