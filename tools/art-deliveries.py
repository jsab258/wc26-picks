#!/usr/bin/env python3
"""Find new art deliveries on art/* branches and file an integration task.

    python3 tools/art-deliveries.py            list and file
    python3 tools/art-deliveries.py --dry-run  list only, file nothing
    python3 tools/art-deliveries.py --selftest offline, no network

WHAT THIS IS, AND IT IS THE HALF THAT RUNS. game-design/art-collaboration.md
records a convention; this file is the only part of it that produces a
reading. Ruled by Jafar 2026-09-08: the existing daily wake reads art branches
for new deliveries and files an integration task.

WHAT IT DOES NOT DO, said here so nobody looks for it: it does not check what
is IN a delivery, and it does not check that the art branch left the studio's
do-not-touch list alone. The file's presence is the whole signal. A convention
with no validator is still a convention, and pretending otherwise is the decay
this docstring exists to prevent.

DENOMINATORS ON EVERY LINE, per .claude/rules/instruments.md: branches walked,
deliveries found, already filed, filed now. A zero here means "none of the N
examined", never "nothing was looked at"; when nothing was looked at it says
the words `nothing measured` with the reason.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART_PREFIX = "art/"
DELIVERY_REL = "production/art/%s/DELIVERY.md"
QUEUE_DIR = "production/queue"
#: The task file a delivery becomes. The commission is in the NAME, which is
#: how "already filed" is answered without a state file that can go stale.
TASK_NAME = "art-%s-integration.md"


def git(args, repo, timeout=30):
    """(rc, out, err). Read-only by construction: see ALLOWED."""
    allowed = ("ls-remote", "for-each-ref", "show", "rev-parse", "cat-file")
    if not args or args[0] not in allowed:
        return 126, "", "art-deliveries.py refuses 'git %s'" % (
            args[0] if args else "")
    env = dict(os.environ)
    env.update({"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never",
                "GIT_ASKPASS": "echo", "GIT_PAGER": "cat"})
    try:
        p = subprocess.run(["git"] + list(args), cwd=repo, env=env,
                           stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, "", "git %s did not finish in %ds" % (args[0], timeout)
    except OSError as e:
        return 125, "", "could not run git (%s)" % type(e).__name__
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def art_branches(repo):
    """Every art/<commission> ref this checkout can see, newest name order.

    READ FROM REFS, NOT FROM A LIST SOMEBODY MAINTAINS. A commission that
    exists only in art-collaboration.md's table and has no branch is not a
    delivery route, and a branch nobody wrote down is still real.
    """
    rc, out, err = git(["for-each-ref", "--format=%(refname:short)",
                        "refs/remotes/origin/" + ART_PREFIX + "*",
                        "refs/heads/" + ART_PREFIX + "*"], repo)
    if rc != 0:
        return None, err or "for-each-ref failed"
    names = []
    for line in out.splitlines():
        ref = line.strip()
        if not ref:
            continue
        short = ref[len("origin/"):] if ref.startswith("origin/") else ref
        if short.startswith(ART_PREFIX) and short not in names:
            names.append(short)
    return sorted(names), ""


def commission_of(branch):
    return branch[len(ART_PREFIX):]


def delivery_on(repo, branch, commission):
    """The delivery blob on that branch, or None. Never checks out."""
    rc, out, _e = git(["cat-file", "-e",
                       "%s:%s" % (branch, DELIVERY_REL % commission)], repo)
    if rc != 0:
        rc, out, _e = git(["cat-file", "-e",
                           "origin/%s:%s"
                           % (branch, DELIVERY_REL % commission)], repo)
    return rc == 0


def already_filed(repo, commission):
    return os.path.exists(os.path.join(repo, QUEUE_DIR,
                                       TASK_NAME % commission))


def file_task(repo, commission, branch):
    """Write the integration task. Returns its repo-relative path."""
    rel = os.path.join(QUEUE_DIR, TASK_NAME % commission)
    body = (
        "line: art integration (%s)\n"
        "spec: a delivery landed on %s. Jafar ruled 2026-09-08 that the daily\n"
        "  wake reads art branches for new deliveries and files an integration\n"
        "  task. This is that task, filed by tools/art-deliveries.py.\n"
        "acceptance: the delivery is reviewed and the review is committed to\n"
        "  production/art/%s/REVIEW.md on the studio branch, and whatever the\n"
        "  review accepts is wired to a call site with a number that proves the\n"
        "  call happened\n"
        "max_sessions: 1\n"
        "status: READY %s. FILED BY A TOOL, NOT BY A PERSON, so nothing here\n"
        "  has read the delivery yet. The tool checks only that\n"
        "  %s exists on that branch; it does not\n"
        "  read it, and it does not check the branch left the studio's\n"
        "  do-not-touch list alone.\n"
        "\n"
        "## What to do\n"
        "\n"
        "Read the delivery, review it, and write the review where section 4 of\n"
        "game-design/art-collaboration.md says it goes. Taste questions are\n"
        "Jafar's and go to him as Telegram cards, never in the review file.\n"
        % (commission, branch, commission,
           __import__("time").strftime("%Y-%m-%d"),
           DELIVERY_REL % commission))
    path = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    return rel


def sweep(repo, dry_run=False, out=print):
    branches, why = art_branches(repo)
    if branches is None:
        out("art-deliveries: nothing measured, could not list refs (%s)" % why)
        return {"branches": None, "found": 0, "filed": 0, "already": 0}
    found = filed = already = 0
    for b in branches:
        c = commission_of(b)
        if not delivery_on(repo, b, c):
            out("  art: %s has no delivery yet" % b)
            continue
        found += 1
        if already_filed(repo, c):
            already += 1
            out("  art: %s delivered, already filed" % b)
            continue
        if dry_run:
            out("  art: %s delivered, WOULD file" % b)
            continue
        rel = file_task(repo, c, b)
        filed += 1
        out("  art: %s delivered, filed %s" % (b, rel))
    out("art-deliveries done: branchesWalked=%d deliveriesFound=%d/%d-branches "
        "alreadyFiled=%d/%d-found filedNow=%d/%d-found dryRun=%s"
        % (len(branches), found, len(branches), already, found, filed, found,
           "yes" if dry_run else "no"))
    if not branches:
        out("art-deliveries: 0 of 0, and that is NO ART BRANCHES AT ALL rather "
            "than art branches with nothing on them")
    return {"branches": branches, "found": found, "filed": filed,
            "already": already}


def _selftest():
    import shutil
    import tempfile
    passed, failed = [], []

    def check(name, cond, detail=""):
        (passed if cond else failed).append(name)
        print("  %-58s %s%s" % (name, "pass" if cond else "FAIL",
                                (" : " + str(detail)) if not cond else ""))

    home = tempfile.mkdtemp(prefix="art-deliveries-selftest-")
    repo = os.path.join(home, "studio")
    os.makedirs(os.path.join(repo, QUEUE_DIR))

    def g(args):
        subprocess.run(["git"] + args, cwd=repo, capture_output=True,
                       text=True, check=False)
    g(["init", "-q", "-b", "studio"])
    g(["config", "user.email", "s@x"])
    g(["config", "user.name", "s"])
    with open(os.path.join(repo, "seed.txt"), "w") as fh:
        fh.write("seed\n")
    g(["add", "-A"])
    g(["commit", "-qm", "seed"])

    # ---- THE ACCEPTING CASE FIRST: a real branch with a real delivery ----
    g(["checkout", "-q", "-b", "art/atlas-01"])
    d = os.path.join(repo, "production", "art", "atlas-01")
    os.makedirs(d)
    with open(os.path.join(d, "DELIVERY.md"), "w") as fh:
        fh.write("# atlas-01\nfour sheets\n")
    g(["add", "-A"])
    g(["commit", "-qm", "delivery"])
    g(["checkout", "-q", "studio"])
    # the delivery must NOT be on the studio branch: that is the whole point
    check("accept/the-delivery-is-not-on-the-studio-branch",
          not os.path.exists(os.path.join(repo, "production", "art",
                                          "atlas-01", "DELIVERY.md")))
    res = sweep(repo, out=lambda s: None)
    check("accept/a-delivery-on-an-art-branch-is-found-without-checkout",
          res["found"] == 1 and res["filed"] == 1, res)
    task = os.path.join(repo, QUEUE_DIR, TASK_NAME % "atlas-01")
    check("accept/and-the-integration-task-is-on-disk-with-the-branch-named",
          os.path.exists(task)
          and "art/atlas-01" in open(task, encoding="utf-8").read(), task)

    # ---- AND IT IS NOT FILED TWICE ----
    res2 = sweep(repo, out=lambda s: None)
    check("accept/a-second-run-files-nothing-and-says-it-was-already-filed",
          res2["found"] == 1 and res2["filed"] == 0 and res2["already"] == 1,
          res2)

    # ---- A BRANCH WITH NO DELIVERY IS NOT A FIND ----
    g(["checkout", "-q", "-b", "art/empty-02"])
    g(["checkout", "-q", "studio"])
    res3 = sweep(repo, dry_run=True, out=lambda s: None)
    check("reject/a-branch-with-no-delivery-is-counted-but-not-found",
          len(res3["branches"]) == 2 and res3["found"] == 1, res3)
    check("reject/dry-run-files-nothing", res3["filed"] == 0, res3)

    # ---- A NON-ART BRANCH IS INVISIBLE ----
    g(["checkout", "-q", "-b", "claude/not-art"])
    g(["checkout", "-q", "studio"])
    res4 = sweep(repo, dry_run=True, out=lambda s: None)
    check("reject/a-branch-outside-the-art-prefix-is-not-walked",
          len(res4["branches"]) == 2
          and all(b.startswith(ART_PREFIX) for b in res4["branches"]),
          res4["branches"])

    # ---- A ZERO THAT IS NOT A SILENCE ----
    bare = os.path.join(home, "bare")
    os.makedirs(os.path.join(bare, QUEUE_DIR))
    subprocess.run(["git", "init", "-q", "-b", "studio"], cwd=bare,
                   capture_output=True, check=False)
    lines = []
    sweep(bare, dry_run=True, out=lines.append)
    check("reject/no-art-branches-says-so-rather-than-printing-a-bare-zero",
          any("NO ART BRANCHES AT ALL" in l for l in lines)
          and any("branchesWalked=0" in l for l in lines), lines)

    # ---- THE READ-ONLY GUARD ----
    rc_w, _o, err_w = git(["push"], repo)
    check("reject/a-write-command-is-refused-by-name",
          rc_w == 126 and "refuses" in err_w, err_w)

    shutil.rmtree(home, ignore_errors=True)
    print("art-deliveries selftest: %d passed, %d failed (of %d case(s))"
          % (len(passed), len(failed), len(passed) + len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    sys.exit(0 if sweep(ROOT, dry_run="--dry-run" in sys.argv[1:]) else 0)
