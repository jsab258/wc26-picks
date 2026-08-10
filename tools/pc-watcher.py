#!/usr/bin/env python3
"""RUN A NAMED JOB ON JAFAR'S MACHINE, ASKED FOR THROUGH THE REPOSITORY.

    python3 tools/pc-watcher.py            # the loop
    python3 tools/pc-watcher.py --once     # one pass, then stop
    python3 tools/pc-watcher.py --selftest # no git, no network

WHAT THIS REPLACES. Every measurement that needs the graphics card or the
4.5 GB of models has to run on one desktop, and the only way to start one has
been "Jafar, please double-click this". That works and it costs a message and
a wait each time, and twice today the answer came back hours after it was
useful.

THE ASK TRAVELS THE WAY THE ANSWER ALREADY DOES. `game-design/pc-jobs/` holds
a request; the watcher notices, runs it, and pushes the result back — the same
channel as the export report and the sim verdict, for the same reason. No new
service, no port, no account.

A NAME, NOT A COMMAND. The request file says `time-a-line`, and the watcher
looks that up in a table it holds. It does not execute a string from the file.
That distinction is the whole security story: the set of things this can do is
fixed by the code, so a request can choose among them and cannot invent one.

WHAT IT DOES NOT PROTECT AGAINST, said plainly rather than left implied: the
table lives in this repository, so anyone who can commit here can add to it.
That is the same trust Jafar already extends by running the bats — this
changes WHEN my code runs on his machine, not WHETHER. What it deliberately
does not do is what a self-hosted CI runner would: this repository is public,
and a runner on a public repository lets a stranger's pull request execute on
the machine. A polling watcher has no such door.

PYTHON RATHER THAN POWERSHELL, and that is today's lesson rather than taste.
The nuget fetch step was written in PowerShell, could only run inside a
28-minute Windows job, shipped unexercised, and was wrong three ways at once.
Anything that cannot be run here gets written where it can be.
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
JOBS = ROOT / "game-design" / "pc-jobs"
REQUEST = JOBS / "request.json"
# The reason string that means "nothing to do", not "something is wrong".
IDLE = "idle"
RESULT = JOBS / "result.txt"
STATE = ROOT / ".pc-watcher-state.json"          # gitignored; local memory
BRANCH = "claude/game-dev-ai-automation-2h67ix"

# THE ONLY THINGS THIS CAN RUN. Each is a list of arguments, never a string
# handed to a shell, so nothing in the request can smuggle an argument. `PY`
# is replaced with the environment's interpreter at call time.
TABLE = {
    "time-a-line": [["PY", "tools/voice-live/time-a-line.py"]],
    "check-graphs": [["PY", "tools/voice-live/check-graphs.py"]],
    "export-graphs": [["PY", "tools/voice-live/export-for-game.py"],
                      ["PY", "tools/voice-live/export-decode.py"],
                      ["PY", "tools/voice-live/check-graphs.py"]],
    "prepare-voices": [["PY", "tools/voice-live/precompute-voices.py"]],
    "hear-it-speak": [["PY", "tools/voice-live/speak.py"]],
}

# Where the Windows environment's python lives, relative to the repository.
WIN_PY = pathlib.Path("tools") / "voice-live" / "env-export" / "Scripts" / "python.exe"


def git(*args, cwd=None, timeout=600):
    p = subprocess.run(["git"] + list(args), cwd=str(cwd or ROOT),
                       capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr).strip()


def interpreter(root):
    """The environment's python if it is there, else this one.

    NAMED RATHER THAN ASSUMED. On Jafar's machine the tools need
    `env-export`, which has torch and onnxruntime in it; the system python
    has neither and would fail with an import error that reads like a code
    fault rather than a wiring one.
    """
    win = root / WIN_PY
    return str(win) if win.exists() else sys.executable


def read_request(text):
    """The request, or None with a reason. Never throws on bad input."""
    try:
        d = json.loads(text)
    except Exception as e:
        return None, f"the request is not JSON ({type(e).__name__})"
    if not isinstance(d, dict):
        return None, "the request is not an object"
    job, rid = d.get("job"), str(d.get("id", ""))
    # IDLE IS NOT A REFUSAL. The slot has to hold something between jobs, and
    # the first placeholder was `"none"` — which the watcher then rejected
    # once a minute, printing a line that looks exactly like a real refusal.
    # A warning that repeats while nothing is wrong is how a reader learns to
    # skip warnings, which is the one habit this whole channel depends on not
    # forming.
    # AN EXPLICIT SENTINEL IS IDLE. A MISSING KEY IS A TYPO. Folding the two
    # together would let `{"jobb": "time-a-line"}` sit there doing nothing for
    # ever and look exactly like waiting — a silence that reads as fine, which
    # is the fault this project keeps finding. So only a job that SAYS it is
    # nothing counts as nothing.
    if job in ("", "none"):
        return None, IDLE
    if job is None:
        return None, "the request names no job"
    if job not in TABLE:
        return None, (f"'{job}' is not a job this watcher knows — "
                      f"it can run: {', '.join(sorted(TABLE))}")
    if not rid:
        return None, "the request has no id, so it could never stop repeating"
    return {"job": job, "id": rid}, None


def already_done(state_text, rid):
    """Has this exact request already run here.

    THE ID IS WHAT STOPS A LOOP. Without it the watcher would see the same
    request every minute and run it for ever — which is not a hypothetical,
    it is what any polling loop does by default.
    """
    try:
        return json.loads(state_text).get("last") == rid
    except Exception:
        return False


def run_job(job, root, say, timeout=3600):
    py = interpreter(root)
    ok = True
    for step in TABLE[job]:
        cmd = [py if a == "PY" else a for a in step]
        say(f"  $ {' '.join(cmd[1:])}")
        try:
            p = subprocess.run(cmd, cwd=str(root), capture_output=True,
                               text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            say(f"  TIMED OUT after {timeout}s")
            return False
        out = (p.stdout + p.stderr).strip().splitlines()
        # THE TAIL, AND A COUNT OF WHAT WAS DROPPED. A cap nobody is told
        # about is indistinguishable from a finding — the `head -3` that hid
        # fourteen character lines cost a morning.
        keep = out[-60:]
        if len(out) > len(keep):
            say(f"  ({len(out) - len(keep)} earlier lines not shown)")
        for line in keep:
            say("  " + line)
        if p.returncode != 0:
            say(f"  exit {p.returncode}")
            ok = False
            break
    return ok


def one_pass(root, say):
    """Fetch, decide, maybe run, push. Returns what happened, as a word."""
    rc, out = git("fetch", "-q", "origin", BRANCH, cwd=root)
    if rc != 0:
        say(f"  fetch failed: {out[:200]}")
        return "offline"
    rc, text = git("show", f"FETCH_HEAD:{REQUEST.relative_to(ROOT).as_posix()}",
                   cwd=root)
    if rc != 0:
        return "no-request"
    req, why = read_request(text)
    if req is None:
        if why == IDLE:
            return "idle"
        say(f"  ignoring the request: {why}")
        return "bad-request"
    state = STATE.read_text(encoding="utf-8") if STATE.exists() else "{}"
    if already_done(state, req["id"]):
        return "already-done"

    say(f"  running '{req['job']}' (id {req['id']})")
    git("pull", "-q", "--rebase", "origin", BRANCH, cwd=root)
    lines = [f"job: {req['job']}", f"id: {req['id']}", ""]
    ok = run_job(req["job"], root, lines.append)
    lines.append("")
    lines.append("RESULT: finished" if ok else "RESULT: FAILED")

    (root / RESULT.relative_to(ROOT)).parent.mkdir(parents=True, exist_ok=True)
    (root / RESULT.relative_to(ROOT)).write_text("\n".join(lines) + "\n",
                                                 encoding="utf-8")
    STATE.write_text(json.dumps({"last": req["id"]}), encoding="utf-8")

    git("add", "-A", cwd=root)
    git("commit", "-m", f"pc-watcher: {req['job']}", cwd=root)
    git("pull", "-q", "--rebase", "origin", BRANCH, cwd=root)
    rc, out = git("push", "origin", f"HEAD:{BRANCH}", cwd=root)
    say("  pushed" if rc == 0 else f"  push failed: {out[:200]}")
    return "ran" if ok else "failed"


def selftest():
    fails, ran = [], []

    def check(ok, what, got=""):
        print(("  ok    " if ok else "  FAIL  ") + what + (f"   [{got}]" if got else ""))
        ran.append(what)
        if not ok:
            fails.append(what)

    good, why = read_request(json.dumps({"job": "time-a-line", "id": "abc"}))
    check(good == {"job": "time-a-line", "id": "abc"},
          "a well-formed request is accepted", why or str(good))

    # THE REJECTING CASES, and the first is the one that matters: a job the
    # table does not hold must be refused by NAME, not attempted.
    for text, expect in (
            (json.dumps({"job": "rm -rf /", "id": "1"}), "is not a job"),
            (json.dumps({"job": "time-a-line"}), "no id"),
            (json.dumps({"id": "1"}), "names no job"),
            ("{not json", "not JSON"),
            (json.dumps(["a", "list"]), "not an object")):
        got, why = read_request(text)
        check(got is None and why and expect in why,
              f"and a request that {expect.replace('is ', '')} is refused",
              why or "ACCEPTED")

    # IDLE IS ITS OWN ANSWER, distinct from a refusal. The placeholder sat in
    # the slot printing a refusal once a minute while nothing was wrong.
    for text in (json.dumps({"job": "none", "id": "none"}),
                 json.dumps({"job": "", "id": "x"})):
        got, why = read_request(text)
        check(got is None and why == IDLE,
              "an empty slot reads as idle rather than as a bad request", why)

    check(already_done(json.dumps({"last": "abc"}), "abc")
          and not already_done(json.dumps({"last": "abc"}), "xyz")
          and not already_done("garbage", "abc"),
          "an id that already ran is not run again, and a missing or damaged "
          "memory re-runs rather than skipping — the safer direction")

    # EVERY JOB IN THE TABLE POINTS AT A FILE THAT EXISTS. A table entry
    # naming a script nobody wrote fails on Jafar's machine, minutes away,
    # rather than here.
    missing = [f"{name}:{step[1]}" for name, steps in TABLE.items()
               for step in steps if not (ROOT / step[1]).exists()]
    check(not missing, f"all {sum(len(v) for v in TABLE.values())} steps across "
          f"{len(TABLE)} jobs point at files that exist", ", ".join(missing))

    check(interpreter(ROOT) == sys.executable,
          "and with no Windows environment present it falls back to this "
          "interpreter rather than a path that does not exist")

    print(f"\npc-watcher --selftest: "
          f"{'PASS' if not fails else str(len(fails)) + ' FAILED'} — {len(ran)} checks")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--seconds", type=int, default=60)
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    print(f"pc-watcher: watching {BRANCH} every {a.seconds}s")
    print(f"  jobs it can run: {', '.join(sorted(TABLE))}")
    print("  close this window to stop it.\n")
    last = None
    while True:
        try:
            what = one_pass(ROOT, print)
        except Exception as e:
            # A WATCHER THAT DIES ON ONE BAD PASS IS A WATCHER NOBODY TRUSTS.
            print(f"  pass failed: {type(e).__name__}: {e}")
            what = "error"
        # SAY IT ONCE. Every state here can persist for hours, and a line
        # per minute is a log nobody reads by the time it matters.
        if what != last and what in ("no-request", "already-done", "idle",
                                     "offline"):
            print(f"  ({what}; quiet until something changes)")
        last = what
        if a.once:
            return 0
        time.sleep(max(10, a.seconds))


if __name__ == "__main__":
    sys.exit(main())
