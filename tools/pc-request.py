#!/usr/bin/env python3
"""ASK JAFAR'S MACHINE FOR A JOB, WITHOUT SILENTLY DISCARDING THE LAST ONE.

    python3 tools/pc-request.py cast-and-prepare four-voices-1
    python3 tools/pc-request.py short-lines run-2 --force
    python3 tools/pc-request.py --selftest

WHY THIS EXISTS, AND IT COST JAFAR HIS CASTING.

`game-design/pc-jobs/request.json` holds exactly one job. Writing a new one
REPLACES whatever was there, and if the machine has not picked the old one up
yet — asleep, watcher not running, busy with something long — that job simply
never happens. Nothing reports it. The file looks the same either way.

On 14 August I queued `cast-and-prepare` with his four voice picks in it, then
queued two experiments over the top of it within the hour. He typed four
casting decisions, I recorded them, and the job that would have installed them
was thrown away twice without a word. It surfaced only because he asked "now
what?" and I went looking for it: `speaker=None` on all four, meaning the
install had never run.

The check is the one the results branch already makes possible. `pc-results`
carries the id of the last job that machine actually RAN, so "is the pending
request still waiting" is a comparison, not a guess.

WHAT IT WILL NOT DO. It will not decide for you. A request that is genuinely
finished with is replaced with `--force`, which prints what it is dropping
first — the same shape as every other destructive step in this repository:
look at what is there, name it, then act.
"""
import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUEST = ROOT / "game-design" / "pc-jobs" / "request.json"
RESULTS = "pc-results"


def pending():
    """The job asked for and not yet answered, or None."""
    if not REQUEST.exists():
        return None
    try:
        return json.loads(REQUEST.read_text(encoding="utf-8"))
    except ValueError:
        return None


def last_run(fetch=True):
    """The id of the last job that machine actually ran, or None.

    Reads the RESULTS branch rather than anything local, because the local
    working tree never learns what the other machine did.
    """
    try:
        if fetch:
            subprocess.run(["git", "fetch", "-q", "origin", RESULTS],
                           cwd=str(ROOT), capture_output=True, timeout=120)
        out = subprocess.run(
            ["git", "show", f"FETCH_HEAD:game-design/pc-jobs/result.txt"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=60)
        if out.returncode != 0:
            return None
        for line in out.stdout.splitlines():
            if line.startswith("id:"):
                return line.split(":", 1)[1].strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def would_clobber(current, ran):
    """True when replacing `current` would discard work never done.

    UNKNOWN COUNTS AS UNRUN, deliberately. If the results branch cannot be
    read, the honest answer is "I do not know whether that job happened",
    and the safe reading of that is to stop — the failure this exists to
    prevent is losing something silently, and a network hiccup must not
    become permission to overwrite.
    """
    if not current or not current.get("id"):
        return False
    return current["id"] != ran


def write(job, ident):
    REQUEST.parent.mkdir(parents=True, exist_ok=True)
    REQUEST.write_text(json.dumps({"job": job, "id": ident}, indent=1) + "\n",
                       encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job", nargs="?")
    ap.add_argument("id", nargs="?")
    ap.add_argument("--force", action="store_true",
                    help="replace a request the machine has not run yet")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.job or not a.id:
        cur = pending()
        ran = last_run()
        print(f"pending: {cur}")
        print(f"last run on the machine: {ran}")
        print("waiting" if would_clobber(cur, ran) else "nothing outstanding")
        return 0

    # THE TABLE IS THE SET OF THINGS THAT CAN BE ASKED FOR. A typo here would
    # otherwise sit in the file until somebody wondered why nothing happened.
    sys.path.insert(0, str(ROOT / "tools"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("pcw", ROOT / "tools" / "pc-watcher.py")
    pcw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pcw)
    if a.job not in pcw.TABLE:
        print(f"no such job '{a.job}'. Known: {', '.join(sorted(pcw.TABLE))}")
        return 2

    cur = pending()
    ran = last_run()
    if would_clobber(cur, ran) and not a.force:
        print(f"REFUSING: '{cur['job']}' (id {cur['id']}) is still waiting — "
              f"the machine's last run was {ran or 'unreadable'}.")
        print("That job has not happened yet, and writing over it would mean")
        print("it never does. Wait for it, or pass --force to drop it.")
        return 1
    if would_clobber(cur, ran) and a.force:
        print(f"dropping unrun request: {cur['job']} (id {cur['id']})")
    write(a.job, a.id)
    print(f"asked for {a.job} (id {a.id})")
    return 0


def selftest():
    ok = fails = 0

    def check(cond, what, detail=""):
        nonlocal ok, fails
        if cond:
            ok += 1
            print(f"  ok   {what}")
        else:
            fails += 1
            print(f"  FAIL {what}" + (f" — {detail}" if detail else ""))

    print("pc-request — the queue of one, and what replacing it costs:")
    # The ACCEPTING case first: a finished request is replaceable.
    check(not would_clobber({"job": "a", "id": "x1"}, "x1"),
          "A REQUEST THE MACHINE HAS ALREADY RUN IS FREE TO REPLACE")
    check(not would_clobber(None, "x1"),
          "and so is no request at all")
    check(not would_clobber({}, "x1"),
          "and so is a malformed one, which cannot be lost work")
    # Then the one that cost the casting.
    check(would_clobber({"job": "cast-and-prepare", "id": "four-voices-1"}, "page-knows-cast-1"),
          "AND A REQUEST STILL WAITING IS NOT — this is the exact pair that "
          "threw away four voice picks")
    check(would_clobber({"job": "a", "id": "x2"}, None),
          "and an unreadable results branch counts as unrun, because "
          "'I do not know' must not become permission to overwrite")
    print(f"\npc-request --selftest: {'PASS' if not fails else str(fails) + ' FAILED'} "
          f"— {ok + fails} checks")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
