#!/usr/bin/env python3
"""Has the container rolled the working tree back, and put it right if so.

WHY THIS EXISTS. Three times on 19 August the container reset this checkout to
`cacebe2` — the same commit each time — while origin held eight commits more.
Nothing was ever lost, because everything here is pushed as soon as it is green.
What it costs is the DIAGNOSIS, and that is not cheap, because a rollback does
not announce itself as one:

  * `gamecheck` reported 168 files where it had said 172 twenty minutes
    earlier, with no deletions anywhere in git;
  * `git status` showed `queue.md` as MODIFIED, carrying twenty-four lines of
    retired content dated six days back that nobody had written today;
  * a grep for a queue item added an hour before came back empty.

Every one of those reads as a code problem first. Four files vanishing from a
compile is alarming; a document quietly reverting is alarming; and both are
completely explained by the checkout having moved under the process. The first
occurrence cost the best part of an hour before the cause was even suspected.

SO THE POINT IS THE HEADLINE, NOT THE FIX. The fix is one line of git that
anybody would find. What is worth having is a single command that says ROLLED
BACK in the first line of its output, before any time goes into the wrong
theory.

  python3 tools/resync.py            # report only
  python3 tools/resync.py --fix      # and reset --hard to origin

IT REFUSES TO DISCARD WORK IT DOES NOT UNDERSTAND. `--fix` resets hard, which
is exactly right when the tree has been rolled back to an old commit and wrong
in every other situation. So it only ever acts when HEAD is a strict ANCESTOR
of origin — the signature of a rollback, and a state in which reset can lose
nothing that was not already pushed. If HEAD has commits origin does not, it
says so and stops: that is unpushed work, and the answer there is to push it,
not to throw it away. Rule 5 — look before you destroy, and make the guard know
the difference between a regression and an improvement.
"""

import argparse
import subprocess
import sys

BRANCH = "claude/game-dev-ai-automation-2h67ix"


def git(*args, check=False):
    p = subprocess.run(("git",) + args, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise SystemExit(f"resync: git {' '.join(args)} failed:\n{p.stderr.strip()}")
    return p.returncode, p.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fix", action="store_true",
                    help="reset --hard to origin when a rollback is detected")
    ap.add_argument("--branch", default=BRANCH)
    a = ap.parse_args()

    # Fetch first or the comparison is against a stale remote ref, which is the
    # one way this tool could report "fine" during an actual rollback.
    code, err = git("fetch", "-q", "origin", a.branch)
    if code != 0:
        print("resync: COULD NOT FETCH — this says nothing about the tree.")
        print(f"  {err}")
        return 2

    _, head = git("rev-parse", "HEAD")
    _, remote = git("rev-parse", f"origin/{a.branch}")
    if head == remote:
        _, dirty = git("status", "--porcelain")
        n = len([l for l in dirty.split("\n") if l.strip()])
        print(f"resync: in sync with origin/{a.branch} at {head[:7]}"
              + (f", {n} uncommitted file(s)" if n else ", clean"))
        return 0

    behind = git("merge-base", "--is-ancestor", head, remote)[0] == 0
    ahead = git("merge-base", "--is-ancestor", remote, head)[0] == 0
    _, count = git("rev-list", "--count", f"{head}..{remote}")

    if ahead and not behind:
        print(f"resync: AHEAD of origin by {git('rev-list', '--count', f'{remote}..{head}')[1]}"
              " commit(s) — this is UNPUSHED WORK, not a rollback.")
        print("  Push it. --fix will not touch this.")
        return 1

    if not behind:
        print("resync: DIVERGED — local and origin both have commits the other "
              "does not.")
        print("  Not a rollback and not safe to reset. Resolve by hand.")
        return 1

    # HEAD is a strict ancestor of origin: the rollback signature.
    _, subject = git("log", "-1", "--format=%s", head)
    print(f"resync: ROLLED BACK — HEAD is {count} commit(s) behind "
          f"origin/{a.branch}.")
    print(f"  HEAD   {head[:7]}  {subject[:60]}")
    _, rsub = git("log", "-1", "--format=%s", remote)
    print(f"  origin {remote[:7]}  {rsub[:60]}")
    print("  Nothing is lost — everything here is pushed when it goes green.")

    if not a.fix:
        print("  Run with --fix to reset --hard to origin.")
        return 1

    code, out = git("reset", "--hard", f"origin/{a.branch}")
    if code != 0:
        print(f"  reset FAILED: {out}")
        return 2
    _, now = git("rev-parse", "HEAD")
    print(f"  reset --hard done; HEAD is now {now[:7]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
