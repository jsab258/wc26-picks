#!/usr/bin/env python3
"""Which commits have a verdict, and which were built and never came back.

    python3 tools/landed.py            # the last 25 commits
    python3 tools/landed.py 60         # the last 60
    python3 tools/landed.py --contains <sha>   # exit 0 once a build CARRIES it

`--contains` IS THE ONE A WATCHER SHOULD USE, and the reason is a fault in
CLAUDE.md's own recipe.

The documented watcher waits for `runs/<sha>.txt` naming the sha that was
dispatched. That is a real improvement on watching the branch head — which
fires on my own pushes — and it is still wrong, for a reason that only appears
when the branch is moving:

**`workflow_dispatch` does not pin a commit. It takes a BRANCH, and the runner
checks out whatever that branch points at when it starts.**

In auto mode I push every few minutes, so by the time a runner picks the job up
the branch has moved. Four builds were dispatched on 4 August at aa0e906,
d5b3741, bdcbe3f and 69e03a6. **Not one of those four shas was ever built.**
The runs that came back are named after later commits — including two the CI
job made itself, committing its own stills — so every watcher armed on those
four was waiting for a file that could not appear.

They did not hang visibly, which is the dangerous part. They fired occasionally,
on the runs where HEAD happened not to have moved between dispatch and
checkout: a watcher that works often enough to look correct.

So the question is not "is there a run named X" but "is there a run whose commit
CONTAINS X" — an ancestry test, which is what was always meant. A build of a
descendant carries the change and its verdict is the answer being waited for.

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


def contains(want):
    """Exit 0 once some landed run's commit contains `want`."""
    sha = git("rev-parse", want)
    # `git rev-parse` on an unknown ref writes the complaint to stderr and
    # ECHOES THE ARGUMENT on stdout, so a plain emptiness test passes it
    # straight through — and the first run answered "not yet: no run contains
    # not-a-s", which is a confident wrong answer to a malformed question.
    # A watcher looping on that would poll for fifty minutes over a typo.
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        print(f"landed: '{want}' is not a commit this repository knows")
        return 2
    have = [p.stem for p in RUNS.glob("*.txt")] if RUNS.exists() else []
    if not have:
        print("landed: no runs yet")
        return 1
    # NEWEST FIRST, so the answer names the most recent build that carries the
    # change rather than the oldest one that happens to.
    order = git("log", "--format=%h", "-400").split()
    ranked = [s for s in order if s in have] + sorted(set(have) - set(order))
    for run in ranked:
        # `--is-ancestor X Y` is "X is contained in Y". A commit is its own
        # ancestor, so an exact match answers yes with no special case.
        ok = subprocess.run(["git", "-C", str(ROOT), "merge-base",
                             "--is-ancestor", sha, run],
                            capture_output=True, text=True).returncode == 0
        if not ok:
            continue
        subject = git("log", "-1", "--format=%s", run)[:60]
        print(f"LANDED in {run} — {subject}")
        p = RUNS / f"{run}.txt"
        if p.exists():
            print("  " + p.read_text(encoding="utf-8", errors="replace").split("\n")[0])
        return 0
    print(f"not yet: no run contains {sha[:7]}. "
          f"{len(ranked)} run(s) known, newest {ranked[0] if ranked else 'none'}.")
    return 1


def main():
    if "--contains" in sys.argv:
        i = sys.argv.index("--contains")
        return contains(sys.argv[i + 1] if i + 1 < len(sys.argv) else "HEAD")

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
