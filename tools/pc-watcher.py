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
    # TRACKED FILES ONLY, AND THAT IS A LOOSENING WITH A REASON.
    #
    # This counted untracked files, so thirteen files pip wrote into the
    # Python environment would have stopped every pass — a watcher any
    # package install can switch off, silently, for a hazard that no longer
    # exists. The original worry was a wide `git add` sweeping the
    # environment into a commit; that is fixed in the add, which names its
    # files. Nothing here stages, moves or deletes an untracked file.
    #
    # What is still refused is an edit to a file git is FOLLOWING, because
    # that is what a replay can trample.
    rc, out = git("status", "--porcelain", "--untracked-files=no", cwd=root)
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


def stamp():
    """A time a human can read, in UTC so two machines agree."""
    from datetime import datetime, timezone
    return f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC"


def write_result(root, lines):
    dest = root / RESULT.relative_to(ROOT)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def replay(root, say, what):
    """Get onto the tip of the branch, keeping any local commit.

    Fast-forward if it can. If it cannot, that is because this machine has
    made a commit of its own, and the answer is to replay it on top rather
    than to stop — but ONLY when nothing is uncommitted, which every caller
    checks first. A rebase with a dirty tree is refused by git, and a rebase
    that goes wrong is aborted here rather than left half-applied.
    """
    # FETCHED HERE, not left to whatever the caller last did. `land` runs at
    # the END of a job that may have taken an hour, and the pass's own fetch
    # happened before it started — so FETCH_HEAD would name a commit from
    # before the work, which is exactly the state this function exists to
    # escape. The first version of this fix inherited that stale reference and
    # would have replayed onto the wrong tip.
    rc, out = git("fetch", "-q", "origin", BRANCH, cwd=root)
    if rc != 0:
        say(f"  cannot reach the branch to replay onto it: {out[:150]}")
        return False
    rc, out = git("merge", "--ff-only", "FETCH_HEAD", cwd=root)
    if rc == 0:
        return True

    # WHAT DO THE LOCAL COMMITS TOUCH? Asked before the rebase, because it
    # decides whether a clash has a right answer.
    #
    # Everything a job produces lands in two folders and nowhere else. Those
    # files are pure OUTPUT, and when both sides have written one the branch's
    # copy is the newer BY CONSTRUCTION — the branch moved on while this
    # machine was working. So `-X ours` is not "pick a winner and hope": it is
    # the only ordering that can be true. During a rebase "ours" is the side
    # already applied, which is the branch.
    #
    # A file only this machine has is not a clash and survives untouched, so a
    # report the branch has never seen is never the thing being dropped.
    rc, changed = git("diff", "--name-only", "FETCH_HEAD...HEAD", cwd=root)
    foreign = [f for f in changed.splitlines() if f.strip() and not f.startswith(
        ("game-design/pc-jobs/", "game-design/voice-live/"))]
    if foreign:
        say(f"  a commit here changes {foreign[0]}, which is not a job result — "
            f"stopping rather than guessing which side wins")
        return False
    rc, out = git("rebase", "-X", "ours", "FETCH_HEAD", cwd=root)
    if rc != 0:
        git("rebase", "--abort", cwd=root)
        say(f"  could not replay {what} onto the branch, and nothing was "
            f"forced: {out[:200]}")
        return False
    say(f"  the branch had moved; replayed {what} on top of it")
    return True


def land(root, say, message):
    """Stage what this job produced, commit it, push it, and PROVE it landed.

    THE EFFECT, NOT THE EXIT CODE. The first version printed "pushed" off
    `git push` returning 0 — and `push` returns 0 for "Everything
    up-to-date". The commit had silently failed, nothing landed, and the
    watcher reported success to a window Jafar was watching while I read an
    empty branch and could not tell a slow job from a stuck one. Straight out
    of this project's own rule: verify a workflow's EFFECTS.

    ONE COPY, CALLED TWICE. This is called once to announce a job has started
    and once to deliver what it made, and writing the sequence out twice is
    how the second copy quietly loses the ancestry check.
    """
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
    rc, commit_out = git("commit", "-m", message, cwd=root)
    if rc != 0:
        # Git's own words, kept. "Nothing to commit" and "who are you" want
        # completely different fixes and both were invisible before.
        say(f"  COMMIT FAILED: {commit_out[:300]}")
        return False

    # AND NOW THE BRANCH HAS ALMOST CERTAINLY MOVED. A job runs for twenty
    # minutes or more, and the other end of this arrangement pushes several
    # times an hour. So by the time a result exists, the remote is ahead —
    # which means the local commit is not a fast-forward BY CONSTRUCTION, and
    # `merge --ff-only` here could never once have succeeded in that case.
    #
    # It was called anyway, with its return code ignored, and the push that
    # followed was rejected. That left a commit stranded locally, and from the
    # next pass onward the watcher could not fast-forward EITHER, so it printed
    # "cannot fast-forward" once a minute for an hour with a finished
    # measurement sitting in it. The rule it was obeying — never rebase, a
    # rebase resets the working tree — is right at the TOP of a pass, where
    # there may be uncommitted work to lose. Here there is nothing uncommitted
    # left: this line is three statements after the commit that took it all.
    if not replay(root, say, "this job's commit"):
        return False
    _, head = git("rev-parse", "HEAD", cwd=root)   # the rebase changed it
    rc, push_out = git("push", "origin", f"HEAD:{BRANCH}", cwd=root)
    if rc != 0:
        say(f"  PUSH FAILED: {push_out[:300]}")
        return False
    # And confirm the remote actually carries it, because a push can succeed
    # having sent nothing at all.
    git("fetch", "-q", "origin", BRANCH, cwd=root)
    rc, _ = git("merge-base", "--is-ancestor", head, "FETCH_HEAD", cwd=root)
    if rc != 0:
        say(f"  PUSH SENT NOTHING — {head[:7]} is not on the branch. "
            f"add: {add_out[:120]}")
        return False
    say(f"  pushed {head[:7]} and confirmed on the branch")
    return True


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
    # A STRANDED COMMIT USED TO END THE WATCHER PERMANENTLY. This said
    # "cannot fast-forward, stopping rather than forcing" and returned, once a
    # minute, for ever — and the fix for it could never arrive, because the
    # self-update check is three lines BELOW here and the update is what this
    # refused to take. An hour of that, with a finished measurement sitting in
    # the local commit nobody could see.
    #
    # `tree_is_safe` has already run, so there is nothing uncommitted to lose
    # and replaying is safe. Nothing is forced and nothing is discarded: the
    # local commit is put on top, and then PUSHED, which is what it was
    # waiting for.
    if not replay(root, say, "this machine's own commit"):
        return "diverged"
    rc, _ = git("merge-base", "--is-ancestor", "HEAD", "FETCH_HEAD", cwd=root)
    if rc != 0:
        rc, out = git("push", "origin", f"HEAD:{BRANCH}", cwd=root)
        say("  and pushed the commit that had been stranded here"
            if rc == 0 else f"  the stranded commit still will not push: {out[:150]}")
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
    # SAY IT HAS STARTED, ON THE BRANCH, BEFORE DOING ANY OF IT.
    #
    # A job's only trace was the result it pushed at the end, so from the
    # other side of the internet "running for twenty minutes" and "never
    # picked it up" looked exactly the same: an unchanged branch. That cost a
    # wait for a measurement job with nothing to read and nothing to conclude
    # from — the same shape as rule 3b, where a zero with no denominator
    # cannot say whether anything was examined.
    #
    # Best effort on purpose. A marker that failed to land must not stop the
    # work it was announcing; it is a courtesy to the reader, not a step.
    write_result(root, [f"job: {req['job']}", f"id: {req['id']}", "",
                        f"RESULT: STARTED at {stamp()} — still running here"])
    if not land(root, say, f"pc-watcher: {req['job']} (started)"):
        say("  (could not announce the start; running it anyway)")

    lines = [f"job: {req['job']}", f"id: {req['id']}", ""]
    ok = run_job(req["job"], root, lines.append)
    lines.append("")
    lines.append("RESULT: finished" if ok else "RESULT: FAILED")

    write_result(root, lines)
    # WRITTEN ONLY NOW. If the machine dies mid-job the id is not recorded, so
    # the next start runs it again — and the branch still carries the STARTED
    # marker saying which job never came back. Both halves of that are
    # deliberate: re-running is the safer direction, and a job that vanished
    # leaves evidence it existed.
    STATE.write_text(json.dumps({"last": req["id"]}), encoding="utf-8")
    if not land(root, say, f"pc-watcher: {req['job']}"):
        return "failed"
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

    # A STARTED JOB AND A FINISHED ONE MUST NOT READ THE SAME. The whole point
    # of the marker is that an unchanged branch used to mean either "running
    # for twenty minutes" or "never picked it up", and those want opposite
    # next moves. Written to a throwaway root so the check cannot scribble on
    # a real result.
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp())
    write_result(tmp, ["job: x", "id: y", "",
                       f"RESULT: STARTED at {stamp()} — still running here"])
    started = (tmp / RESULT.relative_to(ROOT)).read_text(encoding="utf-8")
    check("RESULT: STARTED" in started and "UTC" in started and "id: y" in started,
          "a started marker names the job, its id and the time, and does not "
          "claim an outcome", started.replace("\n", " ")[:70])
    write_result(tmp, ["job: x", "id: y", "", "RESULT: finished"])
    done = (tmp / RESULT.relative_to(ROOT)).read_text(encoding="utf-8")
    check("STARTED" not in done and "RESULT: finished" in done,
          "and the outcome REPLACES it rather than being appended, so the last "
          "word on the branch is what happened", done.replace("\n", " ")[:70])

    # ---- THE PUSH PATH, ON REAL REPOSITORIES ----------------------------
    #
    # THE HALF THAT HAD NEVER BEEN RUN. Everything above tests decisions made
    # from strings. The part that actually failed was git: a job commits its
    # result, the branch has moved while it ran, `merge --ff-only` cannot
    # succeed by construction, its return code was ignored, and the push was
    # rejected — stranding the commit and bricking every later pass. None of
    # that needs a GPU or a network. Three local repositories reproduce it in
    # under a second, and not building them is why an hour went missing.
    def repos():
        import tempfile as tf
        home = pathlib.Path(tf.mkdtemp())
        far = home / "origin.git"
        git("init", "-q", "--bare", str(far))
        for name in ("watcher", "other"):
            git("clone", "-q", str(far), str(home / name))
            git("config", "user.email", "t@example.com", cwd=home / name)
            git("config", "user.name", "T", cwd=home / name)
        w = home / "watcher"
        (w / "seed.txt").write_text("seed\n", encoding="utf-8")
        git("add", "seed.txt", cwd=w)
        git("commit", "-q", "-m", "seed", cwd=w)
        git("checkout", "-q", "-b", BRANCH, cwd=w)
        git("push", "-q", "origin", f"HEAD:{BRANCH}", cwd=w)
        o = home / "other"
        git("fetch", "-q", "origin", BRANCH, cwd=o)
        git("checkout", "-q", "-B", BRANCH, "FETCH_HEAD", cwd=o)
        return w, o

    def result_in(root, text):
        write_result(root, [text])

    def moved(other, text):
        """Somebody else pushes while the job is running — the normal case."""
        (other / "elsewhere.txt").write_text(text, encoding="utf-8")
        git("add", "elsewhere.txt", cwd=other)
        git("commit", "-q", "-m", text, cwd=other)
        git("push", "-q", "origin", f"HEAD:{BRANCH}", cwd=other)

    # THE ACCEPTING CASE FIRST: nobody else pushed, so it fast-forwards.
    watcher, other = repos()
    result_in(watcher, "quiet run")
    quiet = []
    ok_quiet = land(watcher, quiet.append, "pc-watcher: quiet")
    check(ok_quiet, "a result lands when nothing else has pushed",
          " ".join(quiet)[:90])

    # AND THE ONE THAT WAS FAILING IN THE FIELD.
    watcher, other = repos()
    result_in(watcher, "the measurement")
    moved(other, "a push that happened while the job ran")
    said = []
    ok_race = land(watcher, said.append, "pc-watcher: raced")
    check(ok_race, "and it STILL lands when the branch moved underneath it — "
          "which is the normal case, not the rare one, because a job runs for "
          "half an hour", " ".join(said)[:110])
    rc, log = git("log", "--oneline", f"origin/{BRANCH}", cwd=other)
    _ = git("fetch", "-q", "origin", BRANCH, cwd=other)
    rc, remote = git("show", f"FETCH_HEAD:{RESULT.relative_to(ROOT).as_posix()}",
                     cwd=other)
    check(rc == 0 and "the measurement" in remote,
          "and the result is readable on the branch afterwards, not stranded "
          "in a local commit", remote[:60])
    rc, both = git("log", "--format=%s", "FETCH_HEAD", cwd=other)
    check("raced" in both and "a push that happened while the job ran" in both,
          "with the other machine's commit kept rather than overwritten",
          both.replace("\n", " | ")[:90])

    # AND A PASS THAT OPENS ON A STRANDED COMMIT RECOVERS INSTEAD OF PRINTING
    # THE SAME REFUSAL FOR EVER. This is the state Jafar's machine sat in.
    watcher, other = repos()
    result_in(watcher, "stranded")
    git("add", "--", RESULT.relative_to(ROOT).as_posix(), cwd=watcher)
    git("commit", "-q", "-m", "pc-watcher: stranded", cwd=watcher)
    moved(other, "and then the branch moved")
    stuck = []
    git("fetch", "-q", "origin", BRANCH, cwd=watcher)
    check(replay(watcher, stuck.append, "the stranded commit"),
          "a stranded commit is replayed onto the moved branch rather than "
          "ending the watcher", " ".join(stuck)[:90])

    # TWO JOB RESULTS CLASHING HAVE A RIGHT ANSWER, AND THIS IS IT. Both sides
    # wrote result.txt. The branch's copy is newer by construction, because the
    # branch moved on while this machine was working — so the clash resolves to
    # the branch rather than stopping the watcher, which is what it did until a
    # stale `time-a-line` result blocked a whole afternoon.
    watcher, other = repos()
    result_in(watcher, "the older run")
    git("add", "--", RESULT.relative_to(ROOT).as_posix(), cwd=watcher)
    git("commit", "-q", "-m", "older", cwd=watcher)
    (watcher / "game-design" / "voice-live").mkdir(parents=True, exist_ok=True)
    (watcher / "game-design" / "voice-live" / "shape-report.txt").write_text(
        "a report only this machine has\n", encoding="utf-8")
    git("add", "--", "game-design/voice-live/shape-report.txt", cwd=watcher)
    git("commit", "-q", "-m", "a measurement nobody else has", cwd=watcher)
    result_in(other, "the newer run")
    git("add", "--", RESULT.relative_to(ROOT).as_posix(), cwd=other)
    git("commit", "-q", "-m", "newer", cwd=other)
    git("push", "-q", "origin", f"HEAD:{BRANCH}", cwd=other)
    settled = []
    git("fetch", "-q", "origin", BRANCH, cwd=watcher)
    ok_settle = replay(watcher, settled.append, "two job results")
    got = (watcher / RESULT.relative_to(ROOT)).read_text(encoding="utf-8")
    kept = (watcher / "game-design" / "voice-live" / "shape-report.txt")
    check(ok_settle and "the newer run" in got and kept.exists(),
          "two job results clashing settle on the branch's copy, and a report "
          "only this machine has SURVIVES rather than being dropped with it",
          f"result={got.strip()[:22]} kept={kept.exists()}")

    # AND WHEN THE CLASH IS NOT A JOB RESULT, NOTHING IS FORCED. Taking the
    # branch's side is only defensible for output whose ordering is known; for
    # anything else it is picking a winner, which is not this tool's to do.
    watcher, other = repos()
    (watcher / "seed.txt").write_text("mine\n", encoding="utf-8")
    git("commit", "-qam", "mine", cwd=watcher)
    (other / "seed.txt").write_text("theirs\n", encoding="utf-8")
    git("commit", "-qam", "theirs", cwd=other)
    git("push", "-q", "origin", f"HEAD:{BRANCH}", cwd=other)
    refused = []
    git("fetch", "-q", "origin", BRANCH, cwd=watcher)
    beaten = replay(watcher, refused.append, "a source change")
    rc, state = git("status", "--porcelain", cwd=watcher)
    check(not beaten and any("not a job result" in s for s in refused)
          and not state.strip(),
          "a commit touching anything else is refused by NAME before a rebase "
          "starts, and leaves a clean tree",
          (" ".join(refused)[:70] + " | tree: " + (state or "clean")[:24]))

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
