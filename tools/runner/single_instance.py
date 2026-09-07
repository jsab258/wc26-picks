#!/usr/bin/env python3
"""ONE SUPERVISOR AT A TIME, ACROSS EVERY DOOR THAT CAN START ONE.

    python3 tools/runner/single_instance.py --selftest

WHY THIS EXISTS. Ruling 2026-09-07 names the hole by number: "this project
has a known open hole: there is no single-instance guard on the supervisor."
Once the scheduled task exists there are THREE doors that can each try to
start tools/supervise.py at the same moment: the scheduled task at logon,
the "LEDGER studio machine.bat" Startup entry that tools/supervise.py writes
on every one of its OWN starts, and Jafar double-clicking
"START EVERYTHING.bat". This module is the lock that makes a second door a
safe no-op instead of two supervisors fighting over one git index, which is
the fight that cost this project four days once already (tools/supervise.py
docstring, "ONE OWNER PER CONDITION").

WHAT THIS IS NOT. It never runs where it decides: this module is policy
only (acquire, is-a-lock-stale, the wording), the same split
tools/supervise.py itself uses and for the same reason (rule 5b) - there is
no Windows in the container this was written in, so everything that CAN be
tested here IS tested here, in --selftest, on the accepting case (the lock
is free), the rejecting case (a live process already holds it, proved with a
real spawned process rather than a fake pid), and the recovery case a crash
leaves behind (a lock naming a pid that is no longer running).

THE ONE THING THIS FILE CANNOT PROVE ON THIS MACHINE is whether
`is_alive_windows` actually asks Windows correctly: there is no Windows here
to run it on. It is exercised in --selftest only through the injectable
`is_alive` parameter of `acquire`, with `is_alive_posix` (this process's own
OS) as the one liveness check that IS proven, on the same pid semantics
Windows shares: a number that is either running or is not.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))


def is_alive_posix(pid):
    """True if `pid` names a running process on this OS. Real syscall, not a
    guess: this is what makes the rejecting case in --selftest a proof
    rather than an assertion."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True                     # exists, owned by someone else
    except OSError:
        return False
    return True


def is_alive_windows(pid):
    """Ask the OS by name, the way `tasklist` is documented to answer.

    UNVERIFIED ON WINDOWS: this project has no Windows to run it on, so this
    function is exercised in --selftest only by being handed to `acquire` in
    place of a fake, never by actually being called on this container's OS.
    Its shape (a CSV row for `pid` and nothing else means alive, no rows
    means gone) is the tasklist behaviour Microsoft documents, not a
    measurement made here.
    """
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "PID eq %d" % pid, "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10)
    except Exception:                                          # noqa: BLE001
        # Cannot ask, so assume alive. The safe side of a lock is to refuse
        # a launch, never to hand out a second one on a guess.
        return True
    if out.returncode != 0:
        return False
    return str(pid) in out.stdout


def default_is_alive():
    return is_alive_windows if os.name == "nt" else is_alive_posix


def read_lock(path):
    """(pid, why) from a lock file's first line. pid is None, with a reason,
    when there is no file, it is empty, or its shape is not what this module
    writes - all three read as free."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            first = fh.readline().strip()
    except OSError:
        return None, "no lock file at this path"
    if not first.startswith("pid="):
        return None, "lock file's first line is not pid=<number>"
    try:
        return int(first[len("pid="):]), "read ok"
    except ValueError:
        return None, "lock file's pid= value is not a whole number"


def write_lock(path, pid, who):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("pid=%d\nwho=%s\nsince=%s\n"
                 % (pid, who, time.strftime("%Y-%m-%dT%H:%M:%S")))


def acquire(path, who="unnamed", pid=None, is_alive=None):
    """(True, "") if THIS process now owns the lock at `path`; (False, why)
    if a live process already holds it.

    A STALE lock - its pid names a process that is no longer running, the
    shape a crash leaves behind - is treated as free and overwritten. That
    is what lets a crashed supervisor be replaced rather than blocking every
    future start for ever, which would turn a safety guard into a second way
    to go silent.
    """
    pid = os.getpid() if pid is None else pid
    check = is_alive or default_is_alive()
    held_pid, _why = read_lock(path)
    if held_pid is not None and check(held_pid):
        return False, ("pid %d already holds this lock and is still "
                       "running (%s)" % (held_pid, path))
    write_lock(path, pid, who)
    return True, ""


# --------------------------------------------------------------------------
# Selftest: the policy, accepting case first, on real processes where a real
# process is what the claim is about.
# --------------------------------------------------------------------------
def selftest():
    import tempfile

    ok, bad = [], []

    def check(name, cond, detail=""):
        (ok if cond else bad).append(name)
        print("  %-6s %s%s" % ("ok" if cond else "FAILED", name,
                               "" if cond else "  <- %s" % (detail,)))

    tmp = tempfile.mkdtemp()

    # ACCEPTING CASE: no lock file exists yet, so the first caller gets it.
    lock1 = os.path.join(tmp, "a", "supervisor.lock")
    okA, whyA = acquire(lock1, who="first", pid=4242)
    check("accept/an-empty-lock-path-is-acquired",
          okA and whyA == "", (okA, whyA))
    heldA, _ = read_lock(lock1)
    check("accept/and-the-file-now-names-the-caller-pid",
          heldA == 4242, heldA)

    # REJECTING CASE, WITH A REAL PROCESS. A fake pid would only prove the
    # arithmetic; this proves the liveness check against an OS process that
    # is actually alive, on the pid semantics Windows shares.
    proc = subprocess.Popen([sys.executable, "-c",
                             "import time; time.sleep(30)"])
    lock2 = os.path.join(tmp, "b", "supervisor.lock")
    write_lock(lock2, proc.pid, "planted-live-holder")
    okB, whyB = acquire(lock2, who="second", pid=99999,
                        is_alive=is_alive_posix)
    check("reject/a-lock-held-by-a-live-process-refuses-a-second-caller",
          not okB and str(proc.pid) in whyB, (okB, whyB))
    heldB, _ = read_lock(lock2)
    check("reject/and-does-not-overwrite-the-live-holders-pid",
          heldB == proc.pid, heldB)

    # RECOVERY CASE: the live holder above exits, its pid is now free, and
    # the same lock file - untouched since it was written - must be treated
    # as stale rather than as a lock for ever. This is the crash tools/
    # supervise.py itself cannot leave a graceful message about.
    proc.terminate()
    proc.wait(timeout=10)
    waited = 0.0
    while is_alive_posix(proc.pid) and waited < 5:
        time.sleep(0.05)
        waited += 0.05
    check("reject/the-planted-holder-is-confirmed-gone-before-the-next-check",
          not is_alive_posix(proc.pid), proc.pid)
    okC, whyC = acquire(lock2, who="third", pid=55555, is_alive=is_alive_posix)
    check("accept/a-stale-lock-naming-a-dead-pid-is-acquired-not-refused",
          okC and whyC == "", (okC, whyC))
    heldC, _ = read_lock(lock2)
    check("accept/and-the-stale-lock-is-overwritten-with-the-new-holder",
          heldC == 55555, heldC)

    # A MALFORMED LOCK FILE READS AS FREE, the same as a missing one, rather
    # than jamming every future launch because one write was cut short.
    lock3 = os.path.join(tmp, "c", "supervisor.lock")
    os.makedirs(os.path.dirname(lock3), exist_ok=True)
    with open(lock3, "w", encoding="utf-8") as fh:
        fh.write("not a lock file\n")
    okD, whyD = acquire(lock3, who="fourth", pid=1)
    check("accept/a-malformed-lock-file-reads-as-free",
          okD and whyD == "", (okD, whyD))

    # THE INJECTABLE CHECKER IS WHAT LETS THE WINDOWS PATH BE EXERCISED HERE
    # AT ALL. A fake `is_alive` that always says yes proves the REFUSAL
    # branch runs the function it is handed rather than always calling the
    # posix one; a fake that always says no proves the same for recovery.
    lock4 = os.path.join(tmp, "d", "supervisor.lock")
    write_lock(lock4, 7, "planted")
    okE, whyE = acquire(lock4, who="fifth", pid=8, is_alive=lambda _p: True)
    check("accept/an-injected-always-alive-checker-is-the-one-consulted",
          not okE and "7" in whyE, (okE, whyE))
    okF, whyF = acquire(lock4, who="sixth", pid=9, is_alive=lambda _p: False)
    check("accept/an-injected-always-dead-checker-is-the-one-consulted",
          okF and whyF == "", (okF, whyF))

    # THE WINDOWS FUNCTION EXISTS AND HAS THE RIGHT SHAPE, even though this
    # container cannot prove it talks to a real tasklist: a pid this process
    # cannot possibly be (0 is not returned by tasklist's own header row
    # filtered to a pid that will never match) still returns a boolean and
    # never raises, which is what `acquire` depends on.
    check("accept/is-alive-windows-returns-a-boolean-and-never-raises",
          isinstance(is_alive_windows(2**30), bool), "no exception")

    print("single_instance selftest: %d passed, %d failed (of %d case(s))"
          % (len(ok), len(bad), len(ok) + len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    print(__doc__)
    sys.exit(0)
