#!/usr/bin/env python3
"""Does the checkout a CI step is about to SEND FROM contain this run's commit?

    python3 tools/runner/checkout-contains.py --run-sha $GITHUB_SHA \
        --repo C:\\Users\\Jafar\\wc26-picks --run-repo . \
        --key-prefix sweepCheckout --out production/pc-ops/outbox-sweep.txt \
        --wait-sec 90 --poll-sec 5
    python3 tools/runner/checkout-contains.py --selftest

WHY THIS EXISTS, QUEUE 189, MEASURED OFF THE COMMITTED FILES. On 2026-09-09
the first real decision-cards pass sent six cards read out of his checkout as
it stood BEFORE the push that started the run: card 803a6f77, which that same
push had just moved from WAITING to ON US, went to his phone, and the two
cards the push added did not. `cards-send.txt` says `waitingTotal=6` and
`cardsSent=6/6`; the queue at the run's commit held 7 waiting cards, counted
with `cards.waiting_cards` itself. The same run's sweep printed
`outboxFiles=15` where the branch carried 16 message files.

Both files said `- 3cf3731` on line 1 and that was TRUE and MISLEADING at
once: 3cf3731 is the commit CI was started FOR (committed 08:41:51Z), and the
commit his checkout was AT was 650f0755 (06:27:03Z), one commit and 8088
seconds of committer time behind. The pair was already in the tree and nobody
had compared it: `inbox-flush.txt` has printed `flushRepoHead=650f0755c`
beside that line 1 since 2026-09-08. Five flush files carry both halves; four
of the five have head exactly equal to the run's commit, and the fifth is the
one above, so the race is a minority of runs rather than every run.

THE CAUSE IS A DEFERRAL AND THE DEFERRAL IS CORRECT.
`tools/runner/install-scheduled-task.ps1` skips its CI resync while a
supervisor or a bare pc-watcher is running, because two writers on one git
index cost this project four days. That leaves the checkout's freshness as
another process's property on another process's timer: `tools/pc-watcher.py`
resyncs at the top of every pass and sleeps `max(10, 60)` between passes, so a
step that runs 35 seconds after a push can read a checkout the watcher has not
come round to yet. Nothing asserted it had.

WHAT THIS ASKS, AND WHY IT IS CONTAINS AND NOT EQUALS.
`git merge-base --is-ancestor <runSha> HEAD` is "is runSha contained in HEAD",
and a commit is its own ancestor, so an exact match answers yes with no special
case. His PC legitimately commits its own evidence, so a checkout AHEAD of the
run's commit is fine and `AheadCommits` above 0 is normal. Exit codes measured
on a real fixture rather than assumed: 0 contains, 1 does not, 128 the object
is not in that repository at all. 128 is a third answer, not the second one:
a checkout that has never fetched the commit cannot contain it, so it refuses,
but it refuses with a different reason and no commit distance, because
`rev-list --count` also fails 128 on a revision it cannot resolve.

NOTHING HERE WRITES TO THE REPOSITORY IT IS ASKING ABOUT. Every call is a read
(`rev-parse`, `cat-file -e`, `merge-base`, `rev-list --count`, `show -s`), and
`GIT_OPTIONAL_LOCKS=0` stops git taking the index lock opportunistically, so
this can never become the second writer the deferral above exists to prevent.
The selftest asserts it: the fixture's HEAD and its `.git/index` mtime are
unchanged by a run.

THE ARITHMETIC AND THE STRINGS LIVE HERE, NOT IN THE WORKFLOW, because pwsh on
his runner cannot be run from this container at all, and an unrun formatter
printing a plausible string is the silent-instrument failure
(`.claude/rules/instruments.md`). The pwsh caller supplies two paths and a
prefix and reads an exit code; every number, every key and every word of the
refusal is written and tested here.

EXIT CODES, WHICH ARE THE CALLER'S WHOLE INTERFACE:
    0  CONTAINS       the checkout contains the run's commit; the caller sends
    3  REFUSE         it does not (behind, diverged, or the object is absent)
    4  UNDETERMINED   the question could not be asked; the caller refuses too
    2  usage          a bad argument, which is also a refusal for the caller
Anything non-zero means DO NOT SEND. 3 and 4 are split so the evidence file can
tell "his checkout is stale" from "this gate could not read his checkout".
"""

import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

NOTHING = "nothing-measured"
SHORT = 10          # characters of a sha in the SERIES, which is a trail for
                    # a human eye, never a comparison: the keys above carry
                    # the full 40 and the comparison is git's.
SERIES_CAP = 8      # distinct heads shown; the cap announces itself in
                    # {P}SeriesShown, never by trimming in silence.
GIT_TIMEOUT = 20    # seconds per call. A wedged git must refuse, not hang:
                    # the step that calls this has a 6 minute ceiling and a
                    # hang inside it loses every line the step would print.

# Every call goes through this so no path can pick up a credential helper, a
# pager, an editor or a terminal prompt. None of these calls touch the network.
GIT_ENV = {
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_ASKPASS": "echo",
    "GIT_PAGER": "cat",
    "GIT_EDITOR": "true",
    "GCM_INTERACTIVE": "never",
    "LC_ALL": "C",
}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PREFIX_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")


def git(repo, *args):
    """(exit code, stdout+stderr stripped). 127 when git is not installed,
    126 when it did not answer inside GIT_TIMEOUT. Both are distinct from
    git's own 128 so the reason can say which happened."""
    env = dict(os.environ)
    env.update(GIT_ENV)
    cmd = ["git", "-c", "safe.directory=*", "-C", str(repo)] + [str(a) for a in args]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, env=env,
                           timeout=GIT_TIMEOUT)
    except FileNotFoundError:
        return 127, "no git on PATH"
    except subprocess.TimeoutExpired:
        return 126, "git did not answer in %ds" % GIT_TIMEOUT
    return p.returncode, (p.stdout + p.stderr).strip()


def _count(repo, rng):
    rc, out = git(repo, "rev-list", "--count", rng)
    return int(out) if rc == 0 and out.isdigit() else None


def read_facts(repo, run_sha, run_repo):
    """Every fact the decision and the lines are made of, as plain data.

    Separated from `decide` and `lines` on purpose: those two are pure and the
    selftest drives them with dictionaries, so the wording and the arithmetic
    are tested without needing a repository in every case.
    """
    f = {"runSha": run_sha, "pcHead": None, "contains": None,
         "behindCommits": None, "aheadCommits": None, "behindSec": None,
         "pcHeadIso": None, "why": ""}
    if not SHA_RE.match(run_sha or ""):
        f["why"] = "run-sha-is-not-a-40-hex-commit-id"
        return f
    if not (pathlib.Path(repo) / ".git").exists():
        f["why"] = "no-git-checkout-at-that-path"
        return f
    rc, head = git(repo, "rev-parse", "--verify", "--quiet", "HEAD^{commit}")
    if rc == 127 or rc == 126:
        f["why"] = out_token(head)
        return f
    if rc != 0 or not SHA_RE.match(head):
        # rc 1 with no output is an unborn HEAD; 128 is a repository git
        # refused to read. Neither can be compared, and neither may pass.
        f["why"] = ("checkout-head-unreadable/rc%d/%s" % (rc, out_token(head)))
        return f
    f["pcHead"] = head
    rc, iso = git(repo, "show", "-s", "--format=%cI", head)
    f["pcHeadIso"] = iso if rc == 0 and iso else None
    present = git(repo, "cat-file", "-e", "%s^{commit}" % run_sha)[0] == 0
    if not present:
        # PROVEN no, not unknown: a repository cannot contain a commit whose
        # object it does not have. The distances stay unmeasured because every
        # rev-list over an absent revision exits 128.
        f["contains"] = False
        f["why"] = "run-sha-not-in-that-checkouts-objects"
    else:
        rc, _ = git(repo, "merge-base", "--is-ancestor", run_sha, head)
        if rc == 0:
            f["contains"] = True
        elif rc == 1:
            f["contains"] = False
        else:
            f["why"] = "merge-base-failed/rc%d" % rc
            return f
        f["behindCommits"] = _count(repo, "%s..%s" % (head, run_sha))
        f["aheadCommits"] = _count(repo, "%s..%s" % (run_sha, head))
    # THE SECONDS COME FROM TWO REPOSITORIES ON PURPOSE. His checkout may not
    # have the run's commit at all, and the runner's own workspace always does
    # even at depth 1, because the commit it checked out is the commit itself.
    rc, run_ct = git(run_repo, "show", "-s", "--format=%ct", run_sha)
    rc2, head_ct = git(repo, "show", "-s", "--format=%ct", head)
    if rc == 0 and rc2 == 0 and run_ct.isdigit() and head_ct.isdigit():
        f["behindSec"] = int(run_ct) - int(head_ct)
    return f


def out_token(text):
    """git's words, safe to put in a key=value value: no spaces, one line,
    capped. A reason a reader cannot parse is a reason nobody reads."""
    one = " ".join((text or "").split())[:90]
    return (one.replace(" ", "-") or "no-output")


def decide(f):
    """(outcome, exit code). PURE. Every path that is not `contains` refuses."""
    if f.get("why") and f.get("contains") is None:
        return "undetermined", 4
    if f.get("contains") is True:
        return "contains", 0
    if f.get("why") == "run-sha-not-in-that-checkouts-objects":
        return "absent", 3
    if (f.get("aheadCommits") or 0) > 0 and (f.get("behindCommits") or 0) > 0:
        return "diverged", 3
    return "behind", 3


# The three answers a resync can turn into a send, which is the only reason
# waiting is ever worth his PC's time. Read by `gate` below.
WAITABLE = ("behind", "diverged", "absent")

REASONS = {
    "contains": ("his-checkout-contains-this-runs-commit/"
                 "the-files-this-step-reads-are-at-or-ahead-of-the-push"),
    "behind": ("his-checkout-does-not-contain-this-runs-commit/"
               "nothing-was-sent/it-would-have-read-older-files/"
               "the-next-push-or-the-watchers-next-resync-clears-it"),
    "diverged": ("his-checkout-is-on-a-commit-this-run-does-not-contain/"
                 "nothing-was-sent/somebody-force-pushed-or-committed-there"),
    "absent": ("his-checkout-has-never-fetched-this-runs-commit/"
               "nothing-was-sent/so-it-cannot-be-running-this-runs-files"),
    "undetermined": ("this-gate-could-not-read-his-checkout/"
                     "nothing-was-sent-because-nothing-proved-it-current"),
}


def lines(prefix, f, wait):
    """The evidence, as it is written into the step's own file. PURE.

    `wait` is {"waitedSec", "budgetSec", "polls", "pollSec", "series",
    "distinct"}. The series is one entry per DISTINCT head seen, stamped with
    the elapsed second it was first seen at, which is what says whether waiting
    longer would have helped.
    """
    outcome, code = decide(f)
    p = prefix
    head = f.get("pcHead") or "none"
    yn = {True: "yes", False: "no", None: NOTHING}[f.get("contains")]
    out = [
        "# QUEUE 189 GATE, and the two shas below are DIFFERENT QUESTIONS.",
        "# %sRunSha is the commit CI was started FOR. %sPcHeadSha is the" % (p, p),
        "# commit HIS CHECKOUT was AT when this step read it. Line 1 of this",
        "# file names the first one, which is why it could be true and",
        "# misleading at once (queue 189). CONTAINS, not equals: his PC",
        "# commits its own evidence, so %sAheadCommits above 0 is normal." % p,
        "# %sBehindSecByCommitTime is the run's committer time minus the" % p,
        "# checkout head's, so positive means his files are older.",
        "%sRunSha=%s %sPcHeadSha=%s %sContains=%s %sOutcome=%s %sDecision=%s"
        % (p, f.get("runSha") or "none", p, head, p, yn, p, outcome, p,
           "send" if code == 0 else "refuse"),
        "%sBehindCommits=%s %sAheadCommits=%s %sBehindSecByCommitTime=%s "
        "%sPcHeadCommitIso=%s"
        % (p, num(f.get("behindCommits")), p, num(f.get("aheadCommits")),
           p, num(f.get("behindSec")), p, f.get("pcHeadIso") or NOTHING),
        "%sWaitedSec=%d/%d %sPolls=%d %sPollSec=%d %sSeries=%s %sSeriesShown=%d/%d"
        % (p, wait["waitedSec"], wait["budgetSec"], p, wait["polls"], p,
           wait["pollSec"], p, ",".join(wait["series"][-SERIES_CAP:]) or NOTHING,
           p, min(len(wait["series"]), SERIES_CAP), wait["distinct"]),
        "%sReason=%s" % (p, REASONS[outcome] if not f.get("why")
                         else REASONS[outcome] + "/" + f["why"]),
    ]
    return out


def num(v):
    """A number, or the words that mean no number was taken. A bare 0 here
    would read as 'measured zero' when it can also mean 'never asked'."""
    return NOTHING if v is None else str(v)


def gate(repo, run_sha, run_repo, prefix, wait_sec, poll_sec, out_path,
         sleeper=time.sleep, clock=time.monotonic):
    """Ask, wait if asked to, write the lines, return the exit code.

    THE WAIT IS BOUNDED AND ITS SERIES IS PRINTED. pc-watcher's period is read
    off its own code (`--seconds` defaults to 60 and supervise.py starts it
    with no flags), which makes a wait a bet that one more pass lands inside
    the budget, and the series is what turns that bet into a measured number
    for whoever sets the bound next.
    """
    t0 = clock()
    polls, series, seen = 0, [], []
    while True:
        f = read_facts(repo, run_sha, run_repo)
        polls += 1
        head = (f.get("pcHead") or "none")[:SHORT]
        if head not in seen:
            seen.append(head)
            series.append("%ds/%s" % (int(clock() - t0), head))
        outcome, code = decide(f)
        elapsed = int(clock() - t0)
        # ONLY WAIT FOR WHAT A RESYNC WOULD FIX. Behind, diverged and absent
        # all become contains the moment pc-watcher's hard reset lands. Every
        # other answer is hopeless by construction: no checkout at that path,
        # a run sha that is not a commit id, no git, a git that hung. Polling
        # those for the whole budget would spend 90 seconds of his one PC to
        # reach the same refusal, so they break out on the first read and the
        # waited/budget pair says the wait was not spent.
        if code == 0 or elapsed >= wait_sec or outcome not in WAITABLE:
            break
        sleeper(min(poll_sec, max(1, wait_sec - elapsed)))
    wait = {"waitedSec": int(clock() - t0), "budgetSec": wait_sec,
            "polls": polls, "pollSec": poll_sec, "series": series,
            "distinct": len(seen)}
    body = lines(prefix, f, wait)
    for l in body:
        print(l)
    if out_path:
        with open(out_path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(body) + "\n")
    return decide(f)[1]


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------
def _fixture(root, name, env):
    d = root / name
    d.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "."], cwd=d, env=env, check=True)
    return d


def _commit(d, env, fname, msg):
    (d / fname).write_text(fname + "\n", encoding="utf-8")
    subprocess.run(["git", "add", fname], cwd=d, env=env, check=True)
    subprocess.run(["git", "commit", "-qm", msg], cwd=d, env=env, check=True)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, env=env,
                          capture_output=True, text=True).stdout.strip()


def selftest():
    passed, failed, notes = 0, 0, []

    def check(label, cond, detail=""):
        nonlocal passed, failed
        if cond:
            passed += 1
            print("  ok   %s" % label)
        else:
            failed += 1
            print("  FAILED %s %s" % (label, detail))

    env = dict(os.environ)
    env.update({"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_SYSTEM": os.devnull})
    root = pathlib.Path(tempfile.mkdtemp(prefix="ledger-contains-"))
    no_wait = {"waitedSec": 0, "budgetSec": 0, "polls": 1, "pollSec": 5,
               "series": ["0s/abc"], "distinct": 1}

    # ---------------------------------------------------------------- ACCEPT
    # THE ACCEPTING CASE FIRST, and it is first because it is the one that
    # goes unrun: if this is wrong the channel stops sending entirely, which
    # is worse than the fault this gate exists for (rule 5b).
    repo = _fixture(root, "equal", env)
    a = _commit(repo, env, "a", "A")
    f = read_facts(repo, a, repo)
    out, code = decide(f)
    check("accept/head-IS-the-runs-commit-sends", (out, code) == ("contains", 0),
          "got %s/%s" % (out, code))
    check("accept/equal-case-counts-zero-both-ways",
          f["behindCommits"] == 0 and f["aheadCommits"] == 0,
          "behind=%s ahead=%s" % (f["behindCommits"], f["aheadCommits"]))
    check("accept/the-pair-of-shas-is-printed-and-both-are-40-hex",
          SHA_RE.match(f["runSha"]) and SHA_RE.match(f["pcHead"]))

    # CONTAINS, NOT EQUALS: his PC commits its own evidence, so a checkout
    # one commit AHEAD of the run must still send. This is the case an
    # equality test would have broken, and it would have broken it silently.
    b = _commit(repo, env, "b", "B")
    f2 = read_facts(repo, a, repo)
    check("accept/checkout-AHEAD-of-the-runs-commit-still-sends",
          decide(f2) == ("contains", 0), str(decide(f2)))
    check("accept/ahead-is-counted-not-just-allowed",
          f2["aheadCommits"] == 1 and f2["behindCommits"] == 0,
          "ahead=%s behind=%s" % (f2["aheadCommits"], f2["behindCommits"]))
    check("accept/head-sha-is-the-newer-commit", f2["pcHead"] == b)

    # ---------------------------------------------------------------- REFUSE
    # BEHIND: the measured fault. The checkout knows the commit and does not
    # contain it.
    behind = _fixture(root, "behind", env)
    b1 = _commit(behind, env, "a", "A")
    b2 = _commit(behind, env, "b", "B")
    subprocess.run(["git", "reset", "-q", "--hard", b1], cwd=behind, env=env,
                   check=True)
    f3 = read_facts(behind, b2, behind)
    check("refuse/behind-refuses", decide(f3) == ("behind", 3), str(decide(f3)))
    check("refuse/behind-names-the-distance", f3["behindCommits"] == 1,
          str(f3["behindCommits"]))
    check("refuse/behind-reports-seconds-of-committer-time",
          isinstance(f3["behindSec"], int), str(f3["behindSec"]))
    txt = " ".join(lines("sweepCheckout", f3, no_wait))
    check("refuse/the-refusal-names-BOTH-shas",
          b2 in txt and b1 in txt, "neither sha in the lines")
    check("refuse/the-refusal-says-nothing-was-sent",
          "nothing-was-sent" in txt)

    # ABSENT: a checkout that never fetched the commit. Distinct reason, no
    # distance, still a refusal.
    other = _fixture(root, "other", env)
    o1 = _commit(other, env, "z", "Z")
    f4 = read_facts(behind, o1, other)
    check("refuse/unknown-commit-refuses-as-absent",
          decide(f4) == ("absent", 3), str(decide(f4)))
    check("refuse/absent-prints-no-invented-distance",
          f4["behindCommits"] is None
          and NOTHING in " ".join(lines("p", f4, no_wait)))

    # DIVERGED: neither contains the other.
    div = _fixture(root, "div", env)
    d1 = _commit(div, env, "a", "A")
    subprocess.run(["git", "checkout", "-q", "-b", "side", d1], cwd=div,
                   env=env, check=True)
    d_side = _commit(div, env, "s", "S")
    subprocess.run(["git", "checkout", "-q", "-"], cwd=div, env=env, check=True)
    d_main = _commit(div, env, "m", "M")
    f5 = read_facts(div, d_side, div)
    check("refuse/diverged-refuses-and-says-diverged",
          decide(f5) == ("diverged", 3), str(decide(f5)))
    check("refuse/diverged-counts-both-directions",
          f5["behindCommits"] == 1 and f5["aheadCommits"] == 1,
          "behind=%s ahead=%s" % (f5["behindCommits"], f5["aheadCommits"]))
    check("refuse/diverged-head-is-the-local-one", f5["pcHead"] == d_main)

    # ------------------------------------------------------- UNDETERMINED
    f6 = read_facts(root / "nothing-here", a, repo)
    check("undetermined/no-checkout-at-that-path-refuses",
          decide(f6) == ("undetermined", 4), str(decide(f6)))
    f7 = read_facts(repo, "not-a-sha", repo)
    check("undetermined/a-run-sha-that-is-not-40-hex-refuses",
          decide(f7) == ("undetermined", 4), str(decide(f7)))
    check("undetermined/says-which-question-could-not-be-asked",
          "run-sha-is-not-a-40-hex-commit-id" in
          " ".join(lines("p", f7, no_wait)))
    empty = _fixture(root, "empty", env)
    f8 = read_facts(empty, a, repo)
    check("undetermined/an-unborn-head-refuses-rather-than-passing",
          decide(f8) == ("undetermined", 4), str(decide(f8)))

    # ------------------------------------------------------------ HYGIENE
    for label, fa in (("contains", f), ("behind", f3), ("absent", f4),
                      ("undetermined", f6)):
        body = lines("sweepCheckout", fa, no_wait)
        keys = [t.split("=")[0] for l in body if not l.startswith("#")
                for t in l.split() if "=" in t]
        check("keys/%s-no-duplicate-key" % label,
              len(keys) == len(set(keys)),
              str(sorted(k for k in keys if keys.count(k) > 1)))
        vals = [t.split("=", 1)[1] for l in body if not l.startswith("#")
                for t in l.split() if "=" in t]
        check("keys/%s-no-empty-value" % label, all(vals))
        check("keys/%s-every-line-starts-with-the-prefix-or-a-hash" % label,
              all(l.startswith("#") or l.startswith("sweepCheckout")
                  for l in body))
        check("keys/%s-waited-zero-ships-its-budget" % label,
              "sweepCheckoutWaitedSec=0/0" in " ".join(body))

    # NO SPACE INSIDE ANY VALUE, the rule every reader in this project
    # depends on and the one a git error message would break.
    broken = {"runSha": "0" * 40, "pcHead": "1" * 40, "contains": None,
              "behindCommits": None, "aheadCommits": None, "behindSec": None,
              "pcHeadIso": None, "why": out_token("fatal: not a valid object "
                                                  "name, with spaces")}
    body = lines("p", broken, no_wait)
    bad = [t for l in body if not l.startswith("#") for t in l.split()
           if t.count("=") and t.split("=", 1)[1] == ""]
    check("keys/git-words-with-spaces-become-one-token", not bad and
          all(len(l.split("=")) >= 2 for l in body if not l.startswith("#")))
    check("keys/the-reason-carries-the-git-words",
          "not-a-valid-object-name," in " ".join(body))

    # -------------------------------------------------------------- THE WAIT
    # A wait that cannot be shown to work is a wait nobody should trust. The
    # clock and the sleep are injected, so this runs in no time and still
    # exercises the real loop: the fixture moves forward under it.
    late = _fixture(root, "late", env)
    l1 = _commit(late, env, "a", "A")
    l2 = _commit(late, env, "b", "B")
    subprocess.run(["git", "reset", "-q", "--hard", l1], cwd=late, env=env,
                   check=True)
    ticks = {"t": 0}
    moved = {"done": False}

    def fake_clock():
        return ticks["t"]

    def fake_sleep(n):
        ticks["t"] += n
        if ticks["t"] >= 10 and not moved["done"]:
            subprocess.run(["git", "reset", "-q", "--hard", l2], cwd=late,
                           env=env, check=True)
            moved["done"] = True

    outfile = root / "waited.txt"
    outfile.write_text("# LEDGER one outbox sweep - %s @1\n" % l2[:7],
                       encoding="utf-8")
    code = gate(late, l2, late, "sweepCheckout", 90, 5, str(outfile),
                sleeper=fake_sleep, clock=fake_clock)
    got = outfile.read_text(encoding="utf-8")
    check("wait/a-resync-landing-inside-the-budget-turns-refusal-into-send",
          code == 0, "exit %d" % code)
    check("wait/the-series-shows-BOTH-heads-and-when-each-was-seen",
          ("0s/" + l1[:SHORT]) in got and ("10s/" + l2[:SHORT]) in got,
          [l for l in got.splitlines() if "Series=" in l])
    check("wait/the-series-cap-announces-itself",
          "sweepCheckoutSeriesShown=2/2" in got)
    check("wait/line-1-of-the-step-file-is-untouched",
          got.splitlines()[0].startswith("# LEDGER one outbox sweep - "))
    check("wait/the-gate-appends-rather-than-rewriting",
          got.count("# QUEUE 189 GATE") == 1)

    # A budget of 0 polls exactly once and refuses, which is what the
    # return-half push uses when the sweep has already waited.
    ticks["t"] = 0
    code0 = gate(behind, b2, behind, "flushCheckout", 0, 5, None,
                 sleeper=fake_sleep, clock=fake_clock)
    check("wait/zero-budget-refuses-without-sleeping", code0 == 3 and
          ticks["t"] == 0, "exit %d after %ds" % (code0, ticks["t"]))

    # A HOPELESS ANSWER MUST NOT SPEND THE BUDGET. No checkout at that path
    # cannot become a checkout at that path by waiting, and 90 seconds of his
    # one PC is a real cost.
    ticks["t"] = 0
    code_h = gate(root / "nothing-here", l2, late, "sweepCheckout", 90, 5, None,
                  sleeper=fake_sleep, clock=fake_clock)
    check("wait/a-hopeless-answer-refuses-without-spending-the-budget",
          code_h == 4 and ticks["t"] == 0,
          "exit %d after %ds" % (code_h, ticks["t"]))

    # ------------------------------------------------- IT IS A READER ONLY
    # The deferral this gate exists beside is there because two writers on
    # one git index cost four days. So: no write, proven, not asserted.
    before_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=behind,
                                 env=env, capture_output=True,
                                 text=True).stdout.strip()
    idx = behind / ".git" / "index"
    before_idx = idx.stat().st_mtime_ns if idx.exists() else None
    for _ in range(3):
        read_facts(behind, b2, behind)
    after_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=behind,
                                env=env, capture_output=True,
                                text=True).stdout.strip()
    after_idx = idx.stat().st_mtime_ns if idx.exists() else None
    check("readonly/his-HEAD-is-not-moved", before_head == after_head)
    check("readonly/his-index-is-not-touched", before_idx == after_idx,
          "%s -> %s" % (before_idx, after_idx))
    status = subprocess.run(["git", "status", "--porcelain"], cwd=behind,
                            env=env, capture_output=True, text=True).stdout
    check("readonly/his-tree-is-left-clean", status.strip() == "",
          status[:80])

    notes.append("THE RUNNER IS NOT COVERED: every case above ran on this "
                 "container's git and python. The pwsh that calls this, his "
                 "python, his account's access to that checkout and the "
                 "dubious-ownership path are unverifiable until the first "
                 "real run on ledger-pc.")
    shutil.rmtree(root, ignore_errors=True)
    print("")
    print("checkout-contains selftest: %d passed, %d failed (%d case(s) run)."
          % (passed, failed, passed + failed))
    for n in notes:
        print(n)
    print("checkout-contains selftest exit=%d meaning=%s casesRun=%d "
          "casesFailed=%d"
          % (1 if failed else 0,
             "every-case-passed" if not failed else "at-least-one-case-failed",
             passed + failed, failed))
    return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run-sha", default="")
    ap.add_argument("--repo", default="")
    ap.add_argument("--run-repo", default=".",
                    help="the runner's own checkout, which always has the "
                         "run's commit even at depth 1; used only for that "
                         "commit's timestamp")
    ap.add_argument("--key-prefix", default="checkout")
    ap.add_argument("--out", default="")
    ap.add_argument("--wait-sec", type=int, default=0)
    ap.add_argument("--poll-sec", type=int, default=5)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.repo or not PREFIX_RE.match(a.key_prefix) or a.wait_sec < 0 \
            or a.poll_sec < 1:
        print("checkout-contains: need --repo, an alphanumeric --key-prefix, "
              "--wait-sec >= 0 and --poll-sec >= 1. Refusing, which for the "
              "caller means DO NOT SEND.")
        return 2
    return gate(a.repo, a.run_sha.strip().lower(), a.run_repo, a.key_prefix,
                a.wait_sec, a.poll_sec, a.out or None)


if __name__ == "__main__":
    sys.exit(main())
