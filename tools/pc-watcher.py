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
# WHERE RESULTS GO, AND IT IS NOT THE BRANCH ABOVE. One writer per branch
# is the whole redesign: this machine only ever READS `BRANCH` and only
# ever WRITES `RESULTS`, so no push it makes can collide with a push I
# make, and no state it gets into needs reconciling with mine.
RESULTS = "pc-results"

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
    # FOUR SOLVER STEPS INSTEAD OF TEN, AND THEN LISTEN TO IT.
    #
    # The flow solver's loop is unrolled into the traced graph, so ten steps
    # is ten copies of the estimator — it sets the file size, the ~200 seconds
    # a session takes to open, and the seconds a line takes to decode, all at
    # once. Nothing measures whether the tenth step is audible. This exports
    # at four, times a line, and speaks one, so the question goes to ears.
    "try-fewer-steps": [["PY", "tools/voice-live/export-decode.py",
                         "--steps", "4", "--force"],
                        ["PY", "tools/voice-live/time-a-line.py"]],
    # AND BACK, because a faster graph that sounds worse has to be one job
    # away from being undone rather than a thing to remember how to reverse.
    "back-to-ten-steps": [["PY", "tools/voice-live/export-decode.py",
                           "--steps", "10", "--force"],
                          ["PY", "tools/voice-live/time-a-line.py"]],
    # ONE ROW INSTEAD OF TWO — the last big lever in the text stage, which is
    # two thirds of a line. Every step currently runs the model twice, once on
    # the sentence and once on the sentence with its conditioning stripped
    # out, and subtracts the second from the first to steer it. Dropping that
    # halves the work and removes what the model leans on to say the right
    # words rather than mumble in the right voice. Ends in audio because
    # nothing else can answer it.
    "try-no-guidance": [["PY", "tools/voice-live/export-for-game.py",
                         "--rows", "1", "--force"],
                        ["PY", "tools/voice-live/time-a-line.py"]],
    "back-to-guidance": [["PY", "tools/voice-live/export-for-game.py",
                          "--rows", "2", "--force"],
                         ["PY", "tools/voice-live/time-a-line.py"]],
    # ONE LINE IN ONE VOICE IS ONE SAMPLE. Jafar approved the no-guidance
    # graph off a single sentence spoken by Rocco, and the failure it is
    # supposed to reveal — the model wandering off the words without its
    # second opinion — is exactly the kind that shows up on the fourth line
    # rather than the first. This speaks several, in more than one voice, so
    # the decision rests on a denominator.
    "hear-a-few": [["PY", "tools/voice-live/speak-a-few.py"]],
    # EXPERIMENT 1 OF THE LATENCY PLAN: which card, does the step grow with
    # position, can python bind the cache on-device, and what does decoding
    # beside the loop cost. Reads graphs, changes nothing.
    # SPLIT AFTER THE FIRST RUN HUNG FOR ITS FULL HOUR AND DIED MUTE. The
    # safe half (card name, position slope) is minutes of plain session runs
    # and cannot hang; the risky half (io-binding, two sessions on one DML
    # device) is exactly where an hour can go. One half failing must not
    # silence the other.
    "probe-step-costs": [["PY", "tools/voice-live/probe-step-costs.py",
                          "--sections", "safe"]],
    # CLOSED 12 AUG, BOTH OF THEM, BY THE SAME ACCESS VIOLATION. io-binding
    # crashes allocating device values; contention crashes the moment two
    # sessions Run() concurrently from two threads — on a stack where running
    # them sequentially has worked hundreds of times. Neither is scheduled
    # again; the finding is the streaming design itself: ONE thread, strictly
    # interleaved, never overlapped. Kept only for future onnxruntime builds.
    "probe-contention": [["PY", "tools/voice-live/probe-step-costs.py",
                          "--sections", "contention"]],
    # LEVER B: halve the text graphs, then time and SPEAK through them in one
    # job — the sampler reads relative odds, and fp16 noise that looks tiny
    # in a norm can still reorder near-ties, so the wav travels with the
    # timing every time.
    "try-fp16": [["PY", "tools/voice-live/convert-fp16.py"],
                 ["PY", "tools/voice-live/time-a-line.py", "--fp16"]],
    # THE FIVE-LINE EARS TEST THROUGH THE HALVES — fp16's real listen. One
    # line said "a bit fast"; five lines and two voices say whether that is
    # this seed's delivery or the precision's habit.
    "hear-fp16": [["PY", "tools/voice-live/convert-fp16.py"],
                  ["PY", "tools/voice-live/speak-a-few.py", "--fp16"]],
    # THE EARLY-STOP RATE, PER PRECISION. fp16 rendered a nine-word line as
    # four tokens once; ten seeds of the same line in each precision turn
    # that anecdote into two rates, and the difference between the rates is
    # lever B's verdict.
    "probe-early-stop": [["PY", "tools/voice-live/convert-fp16.py"],
                         ["PY", "tools/voice-live/speak-a-few.py",
                          "--fp16", "--line", "2", "--seeds", "10"],
                         ["PY", "tools/voice-live/speak-a-few.py",
                          "--line", "2", "--seeds", "10"]],
    # STREAMING'S DECODE HALF: re-export the decode pair (the chunk graph
    # rides beside the whole-line one now), then render the sweep's line
    # whole and in chunks into ONE wav so ears judge the seams — the seam
    # cache is proven consumed by selftest, but "consumed" and "inaudible"
    # are different claims and only the second one matters.
    "export-and-hear-chunks": [["PY", "tools/voice-live/export-decode.py"],
                               ["PY", "tools/voice-live/convert-fp16.py",
                                "--only", "s3gen"],
                               ["PY", "tools/voice-live/hear-chunks.py"]],
    # LEVER A: does the cache staying on the card pay, and does the bound
    # path speak the same numbers. The python preview of residency DIED in
    # the DML provider (0xC0000005, twice), so the C# path must be run on
    # this machine before any Unity build trusts it — the bench is the
    # game's own backend classes in a console shell, logits compared
    # float-for-float before anything is timed. Needs the .NET SDK; the
    # driver checks first and says exactly what to install if it is absent.
    # RE-EXPORT FIRST, THEN SPEAK. The prefill graph now carries its own
    # row count (`ledger.rows`), and the graphs on this machine predate
    # that stamp — so the bench would keep guessing at a number the file
    # is now able to state. The export is ~30s for the text pair and its
    # fingerprint changes with the exporter, so this re-runs exactly when
    # it should and skips when nothing moved.
    "time-the-binding": [["PY", "tools/voice-live/export-for-game.py"],
                         ["PY", "tools/voice-live/bench-binding.py"]],
    # EXPERIMENT 2: the no-guidance retest, FAIRLY this time. The first one
    # ran Ada to the ceiling with a sampler that had no repetition penalty —
    # the crude sampler now shares the penalised one — so this exports one
    # row, listens across voices, and RESTORES the guided graphs afterwards
    # whatever happens, so the machine never sits on an unapproved export.
    "retest-no-guidance": [["PY", "tools/voice-live/export-for-game.py",
                            "--rows", "1", "--force"],
                           ["PY", "tools/voice-live/speak-a-few.py"],
                           ["PY", "tools/voice-live/export-for-game.py",
                            "--rows", "2", "--force"]],
    # THE FOUR PRINCIPALS NOBODY COULD CAST, because until 13 August they had
    # no entry in the fetcher at all and each drew a crowd voice in silence.
    # The corpus is unreachable from the container (403 through the proxy), so
    # the fetch has to happen here — and it is the half that does not need
    # Jafar. It leaves him the half that does: opening the page and listening.
    #
    # `--no-open` because a job that steals focus on somebody's desktop is a
    # job they learn to dread, and the page is a file he opens when he wants
    # it. `--yes` because the fetcher builds its OWN `.venv-voices` beside
    # itself rather than installing into `env-export`, so approving that is
    # approving a directory this job created and nothing the live-speech work
    # depends on.
    # `--source vctk` IS THE CONSISTENCY REQUIREMENT, NOT A FALLBACK. Every
    # voice already in this game is VCTK — the picked clips are named
    # `ada.p276`, `crowd_m1.p287`, and `pNNN` is VCTK's speaker id. The
    # fetcher's default is `commonvoice`, so the first attempt at these four
    # asked for a corpus none of their nineteen colleagues came from, could
    # not open it, and refused to substitute — correctly, because a shortlist
    # from the wrong corpus costs a listening pass to discover. Casting four
    # principals out of a different recording chain from the rest of the
    # street would have been audible. Consent is unchanged either way: VCTK
    # speakers were recruited and recorded for speech-technology research,
    # which is the standard that put Common Voice first rather than a
    # relaxation of it.
    "fetch-four-voices": [["PY", "tools/voice-fetch/ledger_voice_fetch.py",
                           "--who", "aldous,danny,june,zlata",
                           "--source", "vctk",
                           "--yes", "--no-open"]],
    # THE SAME SENTENCE, THREE WAYS, so "slightly robotic" stops being a
    # matter of memory. Jafar judged `bench-spoke.wav` — the C# path — against
    # a recollection of a DIFFERENT line rendered days earlier, which is not a
    # comparison anybody can make fairly. `speak.py` renders one line twice:
    # chatterbox's own `generate()` as the control, and our Python loop and
    # sampler. Give it the bench's exact text and voice and there are three
    # takes of one sentence, which localises the fault instead of describing
    # it: control clean and both ours poor is our sampler, all three alike is
    # the model's ceiling for this voice, and only the C# one poor is the C#
    # path. Nothing here re-exports, so the graphs it judges are the ones the
    # bench used.
    # WHATEVER THE BANK IS SHORT, WHICH TODAY IS NOTHING. Written when four
    # bark lines had drifted and 24 clips were missing; the fix turned out to
    # be removing the em dashes from `StreetVoice` rather than rendering text
    # that breaks the house style, so the shortfall closed without this
    # running. Kept because `barks_current` can go red again for a legitimate
    # reason — a line genuinely reworded — and then this is the recovery.
    # `--all` SKIPS what is already on disk, so it renders the gap and
    # nothing else and cannot touch what Jafar has already heard.
    "render-the-drift": [["PY", "tools/voice-gen/ledger_voice_gen.py", "--all"]],
    "ab-the-same-line": [["PY", "tools/voice-live/speak.py",
                          "--voice", "rocco",
                          "--text",
                          "Seen the van again. Thursday, same as last Thursday."]],
    # EVERYTHING JAFAR NEEDS TO SETTLE "SLIGHTLY ROBOTIC", IN ONE ROUND TRIP.
    #
    # The batching rule: a wait costs the same whether it carries one step or
    # three, and asking for these separately is three waits and two chances to
    # forget the next one. The bench speaks five awkward lines across three
    # voices, then `speak.py` renders one of those same lines twice more —
    # chatterbox's own generate() as the control, and our python loop. Seven
    # takes, one listen, and the comparison is against files rather than
    # against a memory of a different sentence from days ago.
    #
    # NO EXPORT STEP, deliberately. The graphs on that machine are the ones
    # the last bench used and the ones `ledger.rows` is stamped into;
    # re-exporting would change the thing being judged in the same run that
    # judges it.
    # RE-RENDER THE PAGE, NOTHING ELSE. The listening page is a file that
    # was generated once; fixing the renderer here changed nothing on the
    # machine holding it, and Jafar refreshed and saw the same 23. A fetch
    # would rebuild it and cost 29 minutes of corpus scanning for candidates
    # already on his disk, so this reads them back out of the page and
    # renders again. Seconds, no network.
    "rebuild-the-page": [["PY", "tools/voice-fetch/ledger_voice_fetch.py",
                          "--rebuild-page"]],
    "judge-the-voice": [["PY", "tools/voice-live/bench-binding.py"],
                        ["PY", "tools/voice-live/speak.py",
                         "--voice", "rocco",
                         "--text",
                         "Seen the van again. Thursday, same as last Thursday."]],
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
        except subprocess.TimeoutExpired as e:
            say(f"  TIMED OUT after {timeout}s")
            # THE PARTIAL OUTPUT TRAVELS. "Timed out" alone says only that
            # time passed; WHICH section hung is in the tail the process had
            # already printed, and python attaches that to the exception. It
            # arrives as bytes even in text mode on some versions, so both
            # are handled rather than assumed.
            for stream in (e.stdout, e.stderr):
                if not stream:
                    continue
                text = (stream.decode("utf-8", "replace")
                        if isinstance(stream, bytes) else stream)
                tail = text.strip().splitlines()[-25:]
                if tail:
                    say(f"  last {len(tail)} line(s) before the kill:")
                    for line in tail:
                        say("  " + line)
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


def resync(root, say):
    """Make this checkout EXACTLY the branch. Never merge, never rebase.

    THE REDESIGN, AND IT IS THE WHOLE POINT. This machine used to be a second
    author on a shared branch: it committed results where I commit code, so
    every job risked a divergence, and a divergence needed a rebase, and a
    rebase needed a clean tree and an unlocked file and a conflict rule. Four
    days of failures, every one of them downstream of that one decision.

    Nothing in this checkout is worth keeping. Its job outputs are FILES,
    published separately below, and its source is mine. So the sync is a
    discard: whatever state this repository is in — half-finished rebase,
    stranded commit, diverged branch, detached head — it becomes the branch,
    and none of those states need a rule of their own.

    UNTRACKED FILES ARE NOT TOUCHED, which is what makes the discard safe.
    The Python environment, the exported graphs and this watcher's own memory
    are all untracked and all survive a hard reset. That is not luck; it is
    why those four .gitignore lines had to land first.
    """
    rc, out = git("fetch", "-q", "origin", BRANCH, cwd=root)
    if rc != 0:
        say(f"  cannot reach GitHub: {out[:150]}")
        return False
    # ANY HALF-FINISHED OPERATION, ENDED. These fail harmlessly when there is
    # nothing to end, and one of them left this machine unable to do anything
    # for an afternoon.
    for op in ("rebase", "merge", "cherry-pick", "am"):
        git(op, "--abort", cwd=root)
    rc, out = git("reset", "--hard", "FETCH_HEAD", cwd=root)
    if rc != 0:
        say(f"  could not match the branch: {out[:200]}")
        return False
    return True


def publish(root, say, message):
    """Put what this job produced on a branch only this machine writes.

    FORCE, ONTO A BRANCH NOBODY ELSE TOUCHES. A shared branch is what made
    every push a negotiation; this one has a single writer, so its history is
    disposable and a force push can never destroy somebody else's work. Each
    push carries the newest result, on top of whatever the main branch was at
    the time, so it is always readable as "this ran against that".

    The commit is made on a detached head so the local branch is left exactly
    matching the main one — the next pass starts from a clean discard rather
    than from something this function invented.
    """
    produced = [RESULT.relative_to(ROOT).as_posix(),
                "game-design/voice-live/speed-report.txt",
                "game-design/voice-live/spoken.wav",
                "game-design/voice-live/bench-spoke.wav",
                "game-design/voice-live/control-model.wav",
                "game-design/voice-live/control-ours.wav",
                "game-design/voice-live/chunked.wav",
                "game-design/voice-live/chunk-report.txt",
                "game-design/voice-live/export-report.txt",
                "game-design/voice-live/shape-report.txt",
                "game-design/voice-live/step-report.txt",
                # THE BANK ITSELF, and it is a directory rather than a file
                # because a render produces clips whose NAMES are hashes of
                # the words — so nobody can list them in advance, which is the
                # whole point of naming a clip after what it says. It is
                # tracked, it holds nothing but bank output, and `git add` on
                # a path is not the wildcard the comment below forbids: that
                # incident was `git add -A` from the repository ROOT, which
                # swept up an untracked Python environment.
                "ledger/Assets/StreamingAssets/Audio/Voice"]
    here = [f for f in produced if (root / f).exists()]
    if not here:
        say("  the job produced none of the files it can publish")
        return False
    # NAMED FILES, NEVER A WILDCARD. `git add -A` from the root staged Jafar's
    # Python environment once and the next reset took the folder with it.
    # `-f` because some of these now sit under an ignored directory and an
    # ignore rule must not be able to silence a result.
    rc, add_out = git("add", "-f", "--", *here, cwd=root)
    rc, commit_out = git("commit", "-m", message, cwd=root)
    if rc != 0:
        say(f"  COMMIT FAILED: {commit_out[:250]}")
        return False
    _, head = git("rev-parse", "HEAD", cwd=root)
    rc, push_out = git("push", "--force", "origin", f"HEAD:{RESULTS}", cwd=root)
    if rc != 0:
        say(f"  PUSH FAILED: {push_out[:250]}")
        return False
    # THE EFFECT, NOT THE EXIT CODE — `push` returns 0 for "everything
    # up-to-date", and this watcher once reported success having sent nothing.
    git("fetch", "-q", "origin", RESULTS, cwd=root)
    rc, remote = git("rev-parse", "FETCH_HEAD", cwd=root)
    if rc != 0 or remote.strip() != head.strip():
        say(f"  PUSH SENT NOTHING — {head[:7]} is not what {RESULTS} holds. "
            f"add: {add_out[:100]}")
        return False
    say(f"  published {head[:7]} to {RESULTS}")
    return True


def one_pass(root, say):
    """Match the branch, run whatever it asks for, publish the answer.

    THREE STEPS AND NO NEGOTIATION. Everything that used to sit between them
    — the fast-forward test, the divergence rule, the conflict strategy, the
    stranded-commit recovery — existed because this machine wrote to the same
    branch it read from. It does not any more, so none of that is needed and
    none of it can go wrong.
    """
    # ANOTHER GIT IS RUNNING — most likely one of the bats. Two git processes
    # in one repository collide on the index lock and fail in a way that reads
    # like anything but a race.
    if (root / ".git" / "index.lock").exists():
        return "busy"

    mine = pathlib.Path(__file__).read_bytes()
    if not resync(root, say):
        return "offline"
    if pathlib.Path(__file__).read_bytes() != mine:
        # RESTART INTO THE NEW CODE. A long-lived process that pulls its own
        # source and keeps running the old copy is the same fault as a bat
        # that copies itself to TEMP before pulling.
        #
        # AND IT IS REACHABLE NOW, WHICH IT WAS NOT. This check used to sit
        # BELOW a refusal that could latch on for ever, so a stuck watcher
        # refused the very change that would unstick it. The sync above cannot
        # refuse, so a fix always arrives.
        say("  this watcher was updated; restarting into the new version")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    # READ FROM THE TREE, which the sync has just made identical to the
    # branch. Reading through `git show FETCH_HEAD:...` was one more way for
    # the file and the code to disagree about which commit is current.
    try:
        text = (root / REQUEST.relative_to(ROOT)).read_text(encoding="utf-8")
    except OSError:
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
    # SAY IT HAS STARTED, BEFORE DOING ANY OF IT. A job's only trace used to
    # be the result it pushed at the end, so "running for twenty minutes" and
    # "never picked it up" looked identical from the far end: an unchanged
    # branch. That cost a wait with nothing to read and nothing to conclude.
    #
    # Best effort. A marker that failed to publish must not stop the work it
    # was announcing.
    write_result(root, [f"job: {req['job']}", f"id: {req['id']}", "",
                        f"RESULT: STARTED at {stamp()} — still running here"])
    if not publish(root, say, f"pc-watcher: {req['job']} (started)"):
        say("  (could not announce the start; running it anyway)")

    lines = [f"job: {req['job']}", f"id: {req['id']}", ""]
    ok = run_job(req["job"], root, lines.append)
    lines.append("")
    lines.append("RESULT: finished" if ok else "RESULT: FAILED")
    write_result(root, lines)
    # WRITTEN ONLY NOW. If the machine dies mid-job the id is not recorded, so
    # the next start runs it again — and the published STARTED marker still
    # names the job that never came back. Both halves are deliberate:
    # re-running is the safer direction, and a job that vanished should leave
    # evidence it existed.
    STATE.write_text(json.dumps({"last": req["id"]}), encoding="utf-8")
    if not publish(root, say, f"pc-watcher: {req['job']}"):
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

    # ---- THE SYNC AND THE PUBLISH, ON REAL REPOSITORIES ------------------
    #
    # THE HALF THAT HAD NEVER BEEN RUN, and four days of failures lived in it.
    # Everything above tests decisions made from strings. What actually broke
    # was git, and it needed no GPU and no network: local repositories
    # reproduce every one of those states in under a second.
    def repos():
        import tempfile as tf
        home = pathlib.Path(tf.mkdtemp())
        far = home / "origin.git"
        git("init", "-q", "--bare", str(far))
        for name in ("watcher", "mine"):
            git("clone", "-q", str(far), str(home / name))
            git("config", "user.email", "t@example.com", cwd=home / name)
            git("config", "user.name", "T", cwd=home / name)
        w = home / "watcher"
        (w / "seed.txt").write_text("seed\n", encoding="utf-8")
        git("add", "seed.txt", cwd=w)
        git("commit", "-q", "-m", "seed", cwd=w)
        git("checkout", "-q", "-b", BRANCH, cwd=w)
        git("push", "-q", "origin", f"HEAD:{BRANCH}", cwd=w)
        m = home / "mine"
        git("fetch", "-q", "origin", BRANCH, cwd=m)
        git("checkout", "-q", "-B", BRANCH, "FETCH_HEAD", cwd=m)
        return w, m

    def i_push(mine, text):
        (mine / "seed.txt").write_text(text, encoding="utf-8")
        git("commit", "-qam", text, cwd=mine)
        git("push", "-q", "origin", f"HEAD:{BRANCH}", cwd=mine)

    def at(root):
        _, out = git("rev-parse", "HEAD", cwd=root)
        return out.strip()

    # 1. THE ORDINARY CASE.
    watcher, mine = repos()
    i_push(mine, "a change of mine\n")
    said = []
    ok1 = resync(watcher, said.append)
    check(ok1 and at(watcher) == at(mine)
          and (watcher / "seed.txt").read_text(encoding="utf-8") == "a change of mine\n",
          "a quiet machine ends the sync holding exactly the branch",
          " ".join(said)[:70])

    # 2. THE STATE THAT COST FOUR DAYS: this machine has a commit, the branch
    #    has moved, and the two disagree about the same file. There is nothing
    #    to reconcile because nothing here is worth keeping.
    watcher, mine = repos()
    (watcher / "seed.txt").write_text("what this machine did\n", encoding="utf-8")
    git("commit", "-qam", "a result nobody wants", cwd=watcher)
    i_push(mine, "and what the branch did\n")
    said = []
    ok2 = resync(watcher, said.append)
    check(ok2 and at(watcher) == at(mine),
          "a diverged machine with a conflicting commit syncs anyway — the "
          "state that used to end the watcher for ever", " ".join(said)[:70])

    # 3. AND FROM A HALF-FINISHED REBASE, which is where Jafar's machine sat
    #    while every repair script refused to touch it.
    watcher, mine = repos()
    (watcher / "seed.txt").write_text("mine\n", encoding="utf-8")
    git("commit", "-qam", "mine", cwd=watcher)
    i_push(mine, "theirs\n")
    git("fetch", "-q", "origin", BRANCH, cwd=watcher)
    git("rebase", "FETCH_HEAD", cwd=watcher)          # leaves it stuck
    stuck = ((watcher / ".git" / "rebase-merge").exists()
             or (watcher / ".git" / "rebase-apply").exists())
    said = []
    ok3 = resync(watcher, said.append)
    check(stuck and ok3 and at(watcher) == at(mine),
          "and out of a half-finished rebase without a human deciding anything",
          f"was stuck: {stuck}")

    # 4. AND IT MUST NOT TOUCH WHAT GIT IS NOT TRACKING. The Python
    #    environment, the 4.5 GB of exported graphs and this watcher's own
    #    memory all live in the folder untracked, and a sync that swept them
    #    would be worse than the problem it solves.
    watcher, mine = repos()
    (watcher / "env-export").mkdir()
    (watcher / "env-export" / "python.exe").write_text("not really\n", encoding="utf-8")
    i_push(mine, "moved on\n")
    resync(watcher, lambda s: None)
    check((watcher / "env-export" / "python.exe").exists(),
          "and an untracked file — the environment, the graphs, its own memory "
          "— is left alone by the discard")

    # 5. PUBLISHING GOES SOMEWHERE ONLY THIS MACHINE WRITES, so it cannot
    #    collide with anything and needs no permission.
    watcher, mine = repos()
    resync(watcher, lambda s: None)
    write_result(watcher, ["job: x", "id: y", "", "RESULT: finished"])
    out5 = []
    ok5 = publish(watcher, out5.append, "pc-watcher: x")
    git("fetch", "-q", "origin", RESULTS, cwd=mine)
    rc, seen = git("show", f"FETCH_HEAD:{RESULT.relative_to(ROOT).as_posix()}", cwd=mine)
    check(ok5 and rc == 0 and "RESULT: finished" in seen,
          f"a result is published to '{RESULTS}' and readable from another "
          f"machine", " ".join(out5)[:70])

    # 6. AND AGAIN, AFTER THE BRANCH MOVED — the case that used to be a
    #    rejected push and a stranded commit. A branch with one writer has a
    #    disposable history, so this is a force push that can destroy nothing.
    i_push(mine, "the branch moved on\n")
    resync(watcher, lambda s: None)
    write_result(watcher, ["job: x", "id: z", "", "RESULT: finished later"])
    out6 = []
    ok6 = publish(watcher, out6.append, "pc-watcher: x again")
    git("fetch", "-q", "origin", RESULTS, cwd=mine)
    rc, seen6 = git("show", f"FETCH_HEAD:{RESULT.relative_to(ROOT).as_posix()}", cwd=mine)
    check(ok6 and "RESULT: finished later" in seen6,
          "and it publishes again after the branch moved, which is what a "
          "rejected push and a stranded commit used to be", " ".join(out6)[:70])

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
