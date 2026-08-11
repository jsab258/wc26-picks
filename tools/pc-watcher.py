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
import os
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
    # THE WHOLE ROUND TRIP AS ONE REQUEST, for the reason the Windows build is
    # batched: the wait costs the same whether it carries one step or four,
    # and Jafar's machine is the only one with the model on it. A graph fix
    # that needs HEARING is export, audit and speak — asking for those as
    # three requests is three waits and two chances to forget the next one.
    "export-and-hear": [["PY", "tools/voice-live/export-for-game.py"],
                        ["PY", "tools/voice-live/export-decode.py"],
                        ["PY", "tools/voice-live/check-graphs.py"],
                        ["PY", "tools/voice-live/time-a-line.py"]],
    "time-the-shape": [["PY", "tools/voice-live/time-the-shape.py"]],
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
    # ON WINDOWS ONLY, which it should always have said. The accidental
    # commit put `env-export/Scripts/python.exe` into the repository, so this
    # container — Linux — pulled it, found it, and would have tried to run a
    # Windows binary. The selftest caught it, which is the check doing its job
    # on a fault nobody was looking for.
    if os.name != "nt":
        return sys.executable
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


def tree_is_safe(root, say):
    """Refuse to do anything if the working tree carries surprises.

    The environment was destroyed because a wide `add` swept up files nobody
    meant to touch and a later git operation threw them away. Both halves are
    gone now — the add is scoped and the merge cannot rewrite — but the
    durable guard is this one: if anything is here that this watcher did not
    produce, it stops and says so rather than proceeding over the top of it.

    A machine I cannot see is exactly where "it was probably fine" is worth
    the least.
    """
    rc, out = git("status", "--porcelain", cwd=root)
    if rc != 0:
        say(f"  cannot read the working tree: {out[:150]}")
        return False
    mine = {RESULT.relative_to(ROOT).as_posix(), REQUEST.relative_to(ROOT).as_posix(),
            "game-design/voice-live/speed-report.txt",
            "game-design/voice-live/spoken.wav",
            "game-design/voice-live/export-report.txt",
            "game-design/voice-live/shape-report.txt"}
    stray = [l[3:].strip().strip('"') for l in out.splitlines()
             if l[3:].strip().strip('"') not in mine]
    if stray:
        say(f"  the working tree has {len(stray)} change(s) this watcher did "
            f"not make — stopping. First: {stray[0]}")
        return False
    return True


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


def run_job(job, root, say, timeout=3600, beat=print):
    """Run the steps, saying out loud that they are alive.

    A JOB THAT TAKES TWENTY MINUTES AND A JOB THAT HUNG LOOKED IDENTICAL, from
    the window and from the branch alike, and half an hour went into telling
    them apart by guesswork. The step announces itself with a clock so the
    difference is visible from the first minute.
    """
    py = interpreter(root)
    ok = True
    for n, step in enumerate(TABLE[job], 1):
        cmd = [py if a == "PY" else a for a in step]
        say(f"  $ {' '.join(cmd[1:])}")
        beat(f"  step {n} of {len(TABLE[job])}: {pathlib.PurePath(step[1]).name} "
             f"— started, output comes when it finishes")
        started = time.time()
        try:
            p = subprocess.run(cmd, cwd=str(root), capture_output=True,
                               text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            say(f"  TIMED OUT after {timeout}s")
            beat(f"  step {n} TIMED OUT after {timeout}s")
            return False
        beat(f"  step {n} finished in {time.time() - started:.0f}s "
             f"(exit {p.returncode})")
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
    # ANOTHER GIT IS RUNNING — most likely one of the bats. Two git processes
    # in one repository collide on the index lock and fail in a way that reads
    # like anything but a race.
    if (root / ".git" / "index.lock").exists():
        return "busy"
    rc, out = git("fetch", "-q", "origin", BRANCH, cwd=root)
    if rc != 0:
        say(f"  fetch failed: {out[:200]}")
        return "offline"
    # PULL EVERY PASS, NOT ONLY WHEN A JOB ARRIVES. The first version pulled
    # inside the run branch, so a watcher left open ran the code it started
    # with for ever — every fix I pushed today would have needed Jafar to
    # close the window and reopen it, and nothing would have said so.
    # FAST-FORWARD OR NOTHING. `pull --rebase` RESETS THE WORKING TREE, and
    # that is what destroyed Jafar's Python environment: files staged by an
    # `add -A` and never committed do not survive a reset. A fast-forward
    # cannot rewrite anything — it either moves the branch pointer or it
    # refuses, and refusing is a state I can read rather than a folder I
    # cannot get back.
    if not tree_is_safe(root, say):
        return "dirty"
    mine = pathlib.Path(__file__).read_bytes()
    rc, out = git("merge", "--ff-only", "FETCH_HEAD", cwd=root)
    if rc != 0:
        say(f"  cannot fast-forward — stopping rather than forcing: {out[:200]}")
        return "diverged"
    if pathlib.Path(__file__).read_bytes() != mine:
        # RESTART INTO THE NEW CODE. A long-lived process that pulls its own
        # source and keeps running the old copy is the same fault as a bat
        # that copies itself to TEMP before pulling — which cost a run today.
        say("  this watcher was updated; restarting into the new version")
        os.execv(sys.executable, [sys.executable] + sys.argv)

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
    lines = [f"job: {req['job']}", f"id: {req['id']}", ""]
    ok = run_job(req["job"], root, lines.append)
    lines.append("")
    lines.append("RESULT: finished" if ok else "RESULT: FAILED")

    (root / RESULT.relative_to(ROOT)).parent.mkdir(parents=True, exist_ok=True)
    (root / RESULT.relative_to(ROOT)).write_text("\n".join(lines) + "\n",
                                                 encoding="utf-8")
    STATE.write_text(json.dumps({"last": req["id"]}), encoding="utf-8")

    # THE EFFECT, NOT THE EXIT CODE. The first version printed "pushed" off
    # `git push` returning 0 — and `push` returns 0 for "Everything
    # up-to-date". The commit had silently failed, nothing landed, and the
    # watcher reported success to a window Jafar was watching while I read an
    # empty branch and could not tell a slow job from a stuck one. Straight
    # out of this project's own rule: verify a workflow's EFFECTS.
    before, _ = git("rev-parse", "HEAD", cwd=root)
    # ONLY WHAT THIS JOB PRODUCED. `git add -A` from the repository root
    # staged Jafar's Python virtual environment — it lives inside the repo at
    # `tools/voice-live/env-export/` and was never ignored — and the watcher
    # committed a piece of it. Scope a destructive or wide command to exactly
    # what the operation made; this repository has that rule from an `rm -rf`
    # in CI that deleted sixteen characters' voice clips.
    # NAMED OUTPUTS, STILL NOT A WILDCARD. A job may leave more than its log —
    # the timing one now writes the spoken waveform — so the list is explicit
    # and lives here rather than being inferred from whatever changed. That
    # inference is what `add -A` was.
    produced = [RESULT.relative_to(ROOT).as_posix(),
                "game-design/voice-live/speed-report.txt",
                "game-design/voice-live/spoken.wav",
                "game-design/voice-live/export-report.txt",
                "game-design/voice-live/shape-report.txt"]
    here = [f for f in produced if (root / f).exists()]
    rc, add_out = git("add", "--", *here, cwd=root)
    rc, commit_out = git("commit", "-m", f"pc-watcher: {req['job']}", cwd=root)
    after, head = git("rev-parse", "HEAD", cwd=root)
    if rc != 0:
        # Git's own words, kept. "Nothing to commit" and "who are you" want
        # completely different fixes and both were invisible before.
        say(f"  COMMIT FAILED: {commit_out[:300]}")
        return "failed"

    git("fetch", "-q", "origin", BRANCH, cwd=root)
    git("merge", "--ff-only", "FETCH_HEAD", cwd=root)
    rc, push_out = git("push", "origin", f"HEAD:{BRANCH}", cwd=root)
    if rc != 0:
        say(f"  PUSH FAILED: {push_out[:300]}")
        return "failed"
    # And confirm the remote actually carries it, because a push can succeed
    # having sent nothing at all.
    git("fetch", "-q", "origin", BRANCH, cwd=root)
    rc, _ = git("merge-base", "--is-ancestor", head, "FETCH_HEAD", cwd=root)
    if rc != 0:
        say(f"  PUSH SENT NOTHING — {head[:7]} is not on the branch. "
            f"add: {add_out[:120]}")
        return "failed"
    say(f"  pushed {head[:7]} and confirmed on the branch")
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
                                     "offline", "busy", "dirty", "diverged"):
            print(f"  ({what}; quiet until something changes)")
        last = what
        if a.once:
            return 0
        time.sleep(max(10, a.seconds))


if __name__ == "__main__":
    sys.exit(main())
