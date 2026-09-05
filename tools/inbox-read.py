#!/usr/bin/env python3
"""READ WHAT JAFAR SENT HIS BOT. The container half of the inbound path.

    python3 tools/inbox-read.py              # at the top of a turn, at every
                                             # spawn or dispatch boundary
    python3 tools/inbox-read.py --no-fetch   # read the last fetched copy
    python3 tools/inbox-read.py --selftest   # local repositories, no network

WHAT IT DOES. Fetches the `pc-inbox` branch, writes any message it has not
seen into `production/inbox/` in this checkout, prints it, and prints how long
it took to get here. `tools/runner/inbox.py` is the other half, running on
Jafar's PC inside the Telegram bot, and this file imports it so that one
implementation of the file format is read by both ends.

WHAT `inboundLatencySec` IS, WITH BOTH ENDS NAMED, because a latency with
unnamed endpoints is not a measurement. It is the PC's COMMIT INSTANT (the
committer date of the commit that first added that file to `pc-inbox`) minus
TELEGRAM'S `date` FIELD for the message (the instant Telegram stamped it,
carried in the file as `sentEpoch`). It therefore covers the phone-to-Telegram
hop, the bot's poll wait and the push, and it does NOT cover the wait from the
push until this program runs. That last stretch is the wake half, which is not
built (queue 092), and it is the reason a filed message can sit for hours: see
`production/queue/088`.

IT CAN GO NEGATIVE, and that is left visible. A negative latency means the
PC's clock is behind Telegram's, not that a message arrived before it was
sent.

WHY THIS MAY FETCH WHEN `tools/runner/inbox.py` MAY NOT. That file runs inside
the watcher's checkout on Jafar's PC, where `pc-watcher.resync` reads
`FETCH_HEAD` between two processes and hard-resets to whatever it finds. This
one runs in the container, where no watcher exists; it still fetches with an
explicit refspec into a named remote-tracking ref and reads THAT, never
`FETCH_HEAD`.

EXIT CODES. 0 it ran, whether or not anything arrived. 2 it could not run
(not a git checkout, or git is missing). 3 the selftest failed.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RUNNER = os.path.join(HERE, "runner")
if RUNNER not in sys.path:
    sys.path.insert(0, RUNNER)
import inbox                                                   # noqa: E402

#: The tracking ref this reads. Named rather than `FETCH_HEAD`, which is
#: whichever ref was fetched last by anything in this checkout.
TRACKING = "refs/remotes/origin/" + inbox.INBOX_BRANCH

#: How much of one message is printed inline. The whole thing is always in
#: the file; the cap announces itself when it bites (the instruments rule).
TEXT_CAP = 2000


def git_run(args, repo, timeout=120):
    """git, without the whitelist that `inbox.py` runs under, and the module
    docstring says why. Still no editor and no credential prompt."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_EDITOR="true",
               GIT_MERGE_AUTOEDIT="no", GIT_PAGER="cat")
    try:
        p = subprocess.run(["git"] + list(args), cwd=repo, env=env,
                           capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return 127, "git is not on PATH"
    except subprocess.TimeoutExpired:
        return 124, "git %s did not finish within %ds" % (args[0], timeout)
    return p.returncode, (p.stdout + p.stderr).strip()


def fetch_branch(repo, remote="origin", branch=None):
    """(state, detail). state is ok, no-branch or unreachable."""
    branch = branch or inbox.INBOX_BRANCH
    rc, out = git_run(["fetch", "-q", remote,
                       "+refs/heads/%s:%s" % (branch, TRACKING)], repo)
    if rc == 0:
        return "ok", ""
    # TWO FAILURES THAT LOOK THE SAME IN AN EXIT CODE AND WANT DIFFERENT
    # NEXT MOVES: nobody has ever sent a message, versus this container
    # cannot reach GitHub. The first is normal, the second is a fault.
    if "couldn't find remote ref" in out or "not our ref" in out:
        return "no-branch", out.strip().splitlines()[-1][:120] if out else ""
    return "unreachable", (out.strip().splitlines() or [""])[-1][:160]


def branch_files(repo, ref=TRACKING):
    """Message files carried by the branch, sorted. The pattern is
    `inbox.NAME_RE`, so the folder's README is not in the denominator."""
    rc, out = git_run(["ls-tree", "-r", "--name-only", ref, "--",
                       inbox.INBOX_DIR], repo)
    if rc != 0:
        return None
    return sorted(p for p in out.split()
                  if inbox.NAME_RE.match(os.path.basename(p)))


def added_at(repo, ref=TRACKING):
    """{path: (sha, iso, epoch)} for the commit that FIRST added each file.

    `--reverse` walks oldest first and `setdefault` keeps that first landing,
    so a file added, removed and re-added reports when it actually arrived.
    The one case this reads late is a branch whose history was replaced from
    the PC's disk (`inbox.push_pending`, no local tip pointer), where every
    file's introducing commit becomes the rewrite. That case announces itself
    on the PC side.
    """
    rc, out = git_run(["log", "--reverse", "--format=%x00%H %ct %cI",
                       "--name-only", "--diff-filter=A", ref, "--",
                       inbox.INBOX_DIR], repo)
    if rc != 0:
        return {}
    at, cur = {}, None
    for line in out.splitlines():
        if line.startswith("\x00"):
            bits = line[1:].split()
            cur = (bits[0], bits[2], int(bits[1])) if len(bits) >= 3 else None
        elif line.strip() and cur:
            at.setdefault(line.strip(), cur)
    return at


def median(values):
    v = sorted(values)
    n = len(v)
    if not n:
        return None
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


def num(x):
    """A number with no space in it, for a key=value."""
    if x is None:
        return "nothing-measured"
    return "%d" % x if float(x).is_integer() else "%.1f" % x


def cap(text):
    if len(text) <= TEXT_CAP:
        return text
    return (text[:TEXT_CAP] + "\n    (+%d more character(s) not shown; the "
            "whole message is in the file)" % (len(text) - TEXT_CAP))


def read_inbox(repo, do_fetch=True, remote="origin", branch=None):
    """Deliver and measure. Returns a dict; prints nothing."""
    branch = branch or inbox.INBOX_BRANCH
    res = {"fetch": "skipped", "detail": "", "seen": 0, "delivered": [],
           "already": [], "samples": [], "branch": branch, "messages": []}
    if do_fetch:
        res["fetch"], res["detail"] = fetch_branch(repo, remote, branch)
    files = branch_files(repo)
    if files is None:
        # No tracking ref at all. Either nothing was ever pushed, or the
        # fetch failed on a checkout that had never fetched it before.
        res["files_state"] = "no-ref"
        return res
    res["files_state"] = "ok"
    res["seen"] = len(files)
    at = added_at(repo)
    here = set(inbox.message_files(repo))
    for rel in files:
        if rel in here:
            res["already"].append(rel)
            continue
        rc, body = git_run(["show", "%s:%s" % (TRACKING, rel)], repo)
        if rc != 0:
            res["messages"].append({"file": rel, "error": body[:120]})
            continue
        fields, why = inbox.parse_message(body)
        full = os.path.join(repo, *rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body if body.endswith("\n") else body + "\n")
        res["delivered"].append(rel)
        item = {"file": rel, "fields": fields, "why": why}
        sha, iso, epoch = at.get(rel, (None, None, None))
        item["commitIso"], item["commitSha"] = iso, sha
        if fields and epoch is not None:
            item["latency"] = epoch - fields["sentEpoch"]
            res["samples"].append(item["latency"])
        res["messages"].append(item)
    return res


def report(res, say=print):
    """Print it. Every zero ships its denominator; every cap announces."""
    m = res["seen"]
    say("inbox-read: branch=%s ref=%s fetch=%s%s"
        % (res["branch"], TRACKING, res["fetch"],
           (" detail=" + res["detail"].replace(" ", "_")) if res["detail"]
           else ""))
    if res["fetch"] == "unreachable" and res.get("files_state") == "ok":
        say("  NOTE: the fetch failed, so this is the last copy fetched into "
            "%s, not a fresh read." % TRACKING)
    for i, item in enumerate(res["messages"], 1):
        if item.get("error"):
            say("  message %d/%d  file=%s COULD-NOT-READ %s"
                % (i, len(res["messages"]), item["file"], item["error"]))
            continue
        f = item.get("fields") or {}
        lat = item.get("latency")
        say("  message %d/%d  file=%s update=%s inboundLatencySec=%s "
            "inboundLatencySecFrom=telegramMessageDate/%s "
            "inboundLatencySecTo=pcCommitInstant/%s"
            % (i, len(res["messages"]), item["file"], f.get("update", "?"),
               num(lat), f.get("sent", "unknown"),
               item.get("commitIso") or "unknown"))
        if item.get("why"):
            say("    THE FILE DID NOT PARSE: %s" % item["why"])
        for line in cap(f.get("text", "")).splitlines():
            say("    " + line)
    n, k = len(res["delivered"]), len(res["already"])
    lat = res["samples"]
    say("inbox-read done: seen=%d delivered=%d/%d alreadyHere=%d/%d "
        "latencySamples=%d/%d inboundLatencySecMedian=%s "
        "inboundLatencySecAtWorst=%s "
        "inboundLatencySecFrom=telegramMessageDate "
        "inboundLatencySecTo=pcCommitInstant branch=%s fetch=%s"
        % (m, n, m, k, m, len(lat), n, num(median(lat)),
           num(max(lat) if lat else None), res["branch"], res["fetch"]))
    if m == 0:
        if res["fetch"] == "unreachable":
            say("  nothing measured: the %s branch could not be fetched from "
                "here (%s), so this run read 0 message(s) and proves nothing "
                "about what Jafar has sent." % (res["branch"], res["detail"]))
        else:
            say("  nothing measured: no message has ever arrived on %s "
                "(0 file(s) on the branch, 0 read). This is the normal state "
                "before he sends one." % res["branch"])
    elif n == 0:
        say("  nothing new: all %d message(s) on the branch are already in "
            "this checkout, so no latency was measured this run." % m)
    if n:
        say("  the delivered file(s) are UNTRACKED in this checkout until "
            "somebody commits them; that is the record of what he said.")


def main(argv):
    if "--selftest" in argv:
        return selftest()
    repo = REPO
    if not os.path.isdir(os.path.join(repo, ".git")):
        print("inbox-read: %s is not a git checkout, so there is nothing to "
              "read. NOTHING MEASURED." % repo)
        return 2
    rc, _ = git_run(["--version"], repo)
    if rc == 127:
        print("inbox-read: git is not on PATH. NOTHING MEASURED.")
        return 2
    report(read_inbox(repo, do_fetch="--no-fetch" not in argv))
    return 0


# --------------------------------------------------------------------------
# SELFTEST. Real repositories on this disk, planted clocks, no network.
# --------------------------------------------------------------------------
def selftest():
    passed, failed = [], []

    def check(name, cond, detail=""):
        (passed if cond else failed).append(name)
        print("  %-46s %s%s" % (name, "pass" if cond else "FAIL",
                                ("  : " + str(detail)) if not cond else ""))

    home, far, watcher, reader = inbox._repos()
    lines = []

    # THE EMPTY CASE FIRST, because it is the state this repository is in
    # until Jafar sends something, and "no messages" must not read like
    # "the reader is broken".
    res = read_inbox(reader, remote=far)
    report(res, lines.append)
    done = [l for l in lines if l.startswith("inbox-read done")][0]
    check("accept/an-empty-branch-says-nothing-measured",
          "delivered=0/0" in done and "seen=0" in done
          and any("nothing measured" in l for l in lines), done)
    check("accept/and-the-latency-keys-say-nothing-measured",
          "inboundLatencySecMedian=nothing-measured" in done
          and "latencySamples=0/0" in done, done)
    check("accept/and-it-names-both-clocks-anyway",
          "inboundLatencySecFrom=telegramMessageDate" in done
          and "inboundLatencySecTo=pcCommitInstant" in done, done)

    # THE ACCEPTING CASE: a message written by the PC half, with a PLANTED
    # commit clock, read back by this half. Both files, one format.
    sent = 1788633012                                # 2026-09-05T18:30:12Z
    inbox.file_and_push(watcher, "Seen the van again.\nThursday.", sent, 4127,
                        now=sent + 5)
    # The commit instant is the PC's clock at push time, which in this test
    # is now. Re-date it so the subtraction has a KNOWN answer rather than a
    # coincidental one: 63 seconds after Telegram stamped the message.
    _, tip = inbox._fixture_git(["rev-parse", inbox.TIP_REF], watcher)
    os.environ["GIT_COMMITTER_DATE"] = "%d +0000" % (sent + 63)
    os.environ["GIT_AUTHOR_DATE"] = "%d +0000" % (sent + 63)
    _, redated = inbox._fixture_git(["commit-tree", tip.strip() + "^{tree}",
                                     "-m", "planted clock"], watcher)
    inbox._fixture_git(["push", "-q", "--force", far,
                        redated.strip() + ":refs/heads/" + inbox.INBOX_BRANCH],
                       watcher)
    for k in ("GIT_COMMITTER_DATE", "GIT_AUTHOR_DATE"):
        os.environ.pop(k, None)

    lines = []
    res = read_inbox(reader, remote=far)
    report(res, lines.append)
    done = [l for l in lines if l.startswith("inbox-read done")][0]
    rel = "production/inbox/" + inbox.message_name(sent, 4127)
    check("accept/the-message-lands-in-the-checkout",
          os.path.exists(os.path.join(reader, *rel.split("/"))), rel)
    check("accept/delivered-ships-its-denominator",
          "seen=1" in done and "delivered=1/1" in done
          and "alreadyHere=0/1" in done, done)
    check("accept/the-latency-is-the-planted-63-seconds",
          "inboundLatencySecMedian=63" in done
          and "inboundLatencySecAtWorst=63" in done, done)
    check("accept/the-sample-line-names-both-clocks-with-instants",
          any("inboundLatencySecFrom=telegramMessageDate/2026-09-05T18:30:12"
              in l and "inboundLatencySecTo=pcCommitInstant/" in l
              for l in lines), lines[1] if len(lines) > 1 else lines)
    check("accept/his-words-are-printed",
          any(l.strip() == "Seen the van again." for l in lines)
          and any(l.strip() == "Thursday." for l in lines), lines)
    check("accept/the-file-on-disk-round-trips",
          inbox.parse_message(open(os.path.join(reader, *rel.split("/")),
                                   encoding="utf-8").read())[0]["text"]
          == "Seen the van again.\nThursday.")

    # AND THE SECOND RUN IS NOT A SECOND DELIVERY.
    lines = []
    report(read_inbox(reader, remote=far), lines.append)
    done = [l for l in lines if l.startswith("inbox-read done")][0]
    check("reject/a-second-run-delivers-nothing-twice",
          "delivered=0/1" in done and "alreadyHere=1/1" in done
          and "latencySamples=0/0" in done, done)
    check("reject/and-says-nothing-new-rather-than-nothing-measured",
          any("nothing new" in l for l in lines)
          and not any("nothing measured" in l for l in lines), lines[-2:])

    # AND AN UNREACHABLE REMOTE IS NOT AN EMPTY INBOX.
    lines = []
    res = read_inbox(reader, remote=os.path.join(home, "no-such-remote.git"))
    report(res, lines.append)
    done = [l for l in lines if l.startswith("inbox-read done")][0]
    check("reject/an-unreachable-remote-says-so-and-reads-the-last-copy",
          res["fetch"] == "unreachable" and "seen=1" in done
          and any("last copy fetched" in l for l in lines), done)

    # AND A CAP THAT BITES SAYS SO.
    long_text = "y" * (TEXT_CAP + 40)
    check("accept/the-print-cap-announces-itself",
          "(+40 more character(s) not shown" in cap(long_text))
    check("accept/a-short-message-is-not-capped",
          "not shown" not in cap("short"))
    check("accept/median-and-at-worst-are-different-statistics",
          median([1, 2, 30]) == 2 and max([1, 2, 30]) == 30)
    check("accept/median-of-nothing-is-nothing-measured",
          num(median([])) == "nothing-measured")

    print("\ninbox-read --selftest: %s, %d passed, %d failed, %d case(s) run. "
          "NOT COVERED: nothing here touches Telegram or GitHub; the branch "
          "was a local bare repository and the commit clock was planted."
          % ("PASS" if not failed else "FAILED", len(passed), len(failed),
             len(passed) + len(failed)))
    if failed:
        print("failed: " + ", ".join(failed))
    return 3 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
