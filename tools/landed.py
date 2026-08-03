#!/usr/bin/env python3
"""Which commits have a verdict, and which were built and never came back.

    python3 tools/landed.py            # the last 25 commits
    python3 tools/landed.py 60         # the last 60

WHY THIS EXISTS.

The overnight failure mode is not stopping. It is working hard on something
that silently is not landing — a build dispatched against a commit that never
produces a verdict, while every step in between reports success and the branch
keeps moving because other work is pushing to it.

The rule for the 07:00 report has always been "check what LANDED, not what
reported success", and it has always been a thing to remember at the exact
moment of the day when remembering is worst. Nine builds were in flight at once
on 3 August; keeping track of which had answered by reading a directory listing
against a git log is precisely the sort of bookkeeping that gets skipped and
then quietly misreported.

WHAT IT CANNOT KNOW, stated because a tool that overclaims is worse than none.
It does not know which commits a build was DISPATCHED for — GitHub holds that
and this runs offline. A commit with no verdict may simply never have been
built, which is completely normal for a docs-only change. So this reports two
lists and does not editorialise: commits with a verdict, and commits without
one. Reading which of the second list you actually dispatched is the human's
half, and it takes seconds once the list is in front of you.

It is deliberately NOT a gate. A commit without a verdict is the normal state
of the newest commit for twenty-eight minutes, and a check that failed on that
would fail on every push.
"""

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNS = ROOT / "game-design" / "sim-shots" / "runs"
VERDICT = ROOT / "game-design" / "sim-shots" / "verdict.txt"


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True, text=True).stdout.strip()


def main():
    count = 25
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            print(f"landed: '{sys.argv[1]}' is not a number of commits")
            return 2

    have = {p.stem for p in RUNS.glob("*.txt")} if RUNS.exists() else set()

    log = git("log", f"-{count}", "--format=%h\t%ct\t%s")
    if not log:
        print("landed: no git history here")
        return 2

    # THE LAST VERDICT TO LAND IS NOT THE NEWEST COMMIT, and this file exists
    # partly because that keeps catching people out. Two builds ran together on
    # 3 August and the one on the OLDER commit finished second, laying its
    # output over the newer one's. Line one carries the sha it was built from,
    # so it is quoted here rather than assumed.
    # ERRORS="replace". The verdict is written by a Windows runner and is not
    # reliably UTF-8 — it carries an en-dash from `cmd.exe` in a code page this
    # side does not assume. A tool that throws on its own input file is a tool
    # nobody runs twice, and the byte in question is in a decorative header.
    head = (VERDICT.read_text(encoding="utf-8", errors="replace").splitlines()[0]
            if VERDICT.exists() else "(none)")
    print(f"verdict.txt says: {head}")
    print()

    answered, silent = [], []
    for line in log.split("\n"):
        sha, when, subject = line.split("\t", 2)
        (answered if sha in have else silent).append((sha, subject))

    print(f"{len(answered)} of the last {count} commit(s) have a verdict:")
    for sha, subject in answered:
        print(f"  {sha}  {subject[:66]}")

    print()
    print(f"{len(silent)} have none — normal for anything not dispatched, and")
    print("the thing to look at for anything that was:")
    for sha, subject in silent:
        print(f"  {sha}  {subject[:66]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
