#!/usr/bin/env python3
"""THE INBOX: a message from Jafar's phone becomes a file on a branch of its own.

    python3 tools/runner/inbox.py --selftest    # offline, builds local repos

WHAT THIS IS. The PC half of the inbound path. `telegram-bot.py` calls
`file_and_push`, which writes the message to `production/inbox/` and puts it
on the `pc-inbox` branch. The container half is `tools/inbox-read.py`, which
reads that branch and prints the messages with their latency. This module
holds the format, the arithmetic and the strings so that BOTH halves parse
one implementation and both get tested where the tests run.

WHY A BRANCH OF ITS OWN, AND NOT `pc-results`. `pc-results` is force-pushed
by `tools/pc-watcher.py:publish` from a tree that is the work branch plus a
NAMED list of produced paths, so a file that reached it by any other route
disappears at the next job. The inbox would therefore vanish exactly when the
PC was busy. `pc-inbox` has one writer, this file, and a disposable history.

WHY A TEMP INDEX, AND NOT A SECOND CLONE. The queue asked for the choice to be
stated. A second clone costs a download, a second credential path and a second
thing that can be stale on Jafar's disk. This writes its commit with git's
plumbing under `GIT_INDEX_FILE`, so it never touches the working tree, the
real index or HEAD, and the watcher's `resync` (a hard reset) and
`deliver_before_discard` (which reads HEAD) cannot see that it happened. The
message file itself is UNTRACKED in that checkout, and untracked files survive
a hard reset. Verified in `--selftest`, both facts, on a real repository.

THE ONE NETWORK CALL IS `git push`, AND THAT IS A DESIGN CONSTRAINT RATHER
THAN A SIDE EFFECT. `pc-watcher.resync` does `git fetch origin <branch>` and
then `git rev-parse FETCH_HEAD` as two separate processes, and it hard-resets
the checkout to whatever the second one reads. A fetch from this file landing
between those two would reset Jafar's checkout to the INBOX tree and then
force-push that onto `pc-results` on the following pass. So this file never
fetches: `git_call` refuses any subcommand not on `ALLOWED`, and the accepting
and refusing sides of that guard are both in the selftest. The parent commit
comes from a local ref this file writes itself, and the push is verified with
`ls-remote`, which reads the remote without writing FETCH_HEAD or any local
ref.

NO DEPENDENCY, standard library only, like the bot it is called from.
"""
import datetime
import os
import re
import subprocess
import sys
import time

#: The work branch, whose newest commit is the awake/asleep proxy. Same
#: string as `tools/pc-watcher.py:BRANCH`.
WORK_BRANCH = "claude/game-dev-ai-automation-2h67ix"

#: One writer (this file), disposable history, named beside `pc-results` so
#: the pair reads as what it is: one branch out of the PC, one branch in.
INBOX_BRANCH = "pc-inbox"

#: Where a message lands, in the repository and on the branch.
INBOX_DIR = "production/inbox"

#: WHERE THE OUTBOUND RECORDS LAND, added for queue 089. A receipt for a sent
#: Producer message and a record of a refused one are the same class of thing:
#: something the PC learned that the studio cannot see from the container. They
#: ride the same branch as the inbox for the same reason it exists, and one
#: transport is the whole point of reusing this file rather than writing a
#: second one.
#:
#: NOT UNDER production/outbox/. `tools/producer-check.py:gate` walks that tree
#: recursively for `*.md` and refuses any name carrying no register suffix, so
#: a receipt written there would turn `ledger/verify.py` red and block every
#: commit. Verified by reading GATE_TREES and the rglob in that file, not
#: assumed.
OUTBOUND_DIR = "production/outbound"

#: WHERE A TAPPED RULING LANDS, added for queue 090. Its own folder rather
#: than OUTBOUND_DIR, because `outbox.outbound_summary` classifies every file
#: it finds there as a receipt or a refusal and a ruling is neither: a record
#: it cannot classify would print as `unreadable` and turn a working channel
#: into a fault report. Separate folder, separate pattern, separate
#: denominator. `.txt` for the same reason the outbound records are `.txt`:
#: `tools/producer-check.py` walks `*.md` and would check it against a message
#: register.
RULING_DIR = "production/rulings"

#: THE PARENT POINTER, LOCAL AND PRIVATE. Written by this file after a push
#: so the next commit can chain without a fetch. Nothing else in the studio
#: looks at `refs/ledger-inbox/`: `pc-watcher` reads HEAD, `refs/heads/*` and
#: `FETCH_HEAD` and none of them are this.
TIP_REF = "refs/ledger-inbox/tip"

#: A message file, and nothing else. The reader's denominator is defined by
#: this pattern, so a README or a stray note in the folder cannot inflate it.
NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{4}Z-\d+\.md$")

#: An outbound record, and nothing else. `.txt` rather than `.md` so that the
#: producer-check gate, which walks `*.md`, can never be handed a receipt to
#: check against a message register. Same denominator discipline as NAME_RE: a
#: README dropped in that folder is outside every count.
OUTBOUND_RE = re.compile(
    r"^[A-Za-z0-9._-]+\.(receipt|refused-[0-9a-f]{8}|photo-receipt)\.txt$")

#: A ruling record, and nothing else. Same denominator discipline again.
RULING_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{4}Z-\d+\.ruling\.txt$")

#: THE SUBCOMMANDS THIS FILE MAY RUN. `fetch` and `pull` are absent on
#: purpose and the docstring above says why. Anything not here comes back as
#: rc 126 with the reason, rather than running.
ALLOWED = ("hash-object", "read-tree", "update-index", "write-tree",
           "commit-tree", "update-ref", "rev-parse", "ls-tree", "ls-remote",
           "push", "log", "cat-file", "show")

#: WHEN THE STUDIO COUNTS AS AWAKE, FROM A SERIES AND NOT FROM A GUESS
#: (rule 2). Measured 2026-09-05 over the 399 gaps between the newest 400
#: commits on the work branch: median 10.7 min, p75 18.4, p90 55.8, p95 90.3,
#: max 7864.6. 324 of 399 gaps (81 percent) are 30 minutes or shorter, so a
#: work branch that has been silent for longer than that is outside four
#: fifths of its own working rhythm.
#:
#: THIRTY RATHER THAN NINETY BECAUSE THE TWO ERRORS ARE NOT THE SAME SIZE.
#: Saying ASLEEP while a turn is in fact running costs Jafar nothing: he is
#: told the worst case and hears sooner. Saying AWAKE while the studio sleeps
#: is the failure this reply exists to prevent, because he then waits minutes
#: for something that arrives in hours. The bound is set to make the cheap
#: error the common one. The gap series is a proxy for commit AGE, which is
#: not the same distribution, and 094 replaces this proxy with the studio
#: saying so itself.
AWAKE_WITHIN_MIN = 30

#: The only live trigger, `trig_013itgDeay6t41BHEmaYFbAj`, 04:00 UTC daily
#: (production/NOW.md item 1d). If that cron changes, this constant changes
#: with it, and the bot starts telling Jafar the wrong hour if it does not.
DAILY_WAKE_HOUR_UTC = 4

#: Who the inbox commits are by. Set explicitly so this never depends on, and
#: never writes to, the git config of the clone it runs in.
COMMIT_NAME = "LEDGER inbox bot"
COMMIT_EMAIL = "ledger-bot@users.noreply.github.com"

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --------------------------------------------------------------------------
# git, on a short leash
# --------------------------------------------------------------------------
def one_line(text, cap=160):
    """git's output as one line, capped, with the cap announced.

    A multi-line `fatal:` block reads badly on a phone and worse inside a
    `key=value` line. This keeps the first thing git said, which is the
    diagnosis, and says how much it dropped.
    """
    flat = " ".join(str(text).split())
    return flat if len(flat) <= cap else (
        flat[:cap] + " (+%d more character(s) not shown)" % (len(flat) - cap))


def git_call(args, repo, timeout=60, extra_env=None):
    """One git command. Returns (rc, output). Never raises, never prompts.

    THE WHITELIST IS THE GUARD, not a tidiness rule: see the module docstring
    for the FETCH_HEAD race it exists to make impossible. rc 126 is this
    file refusing; rc 127 is git missing; rc 124 is a timeout.
    """
    if not args or args[0] not in ALLOWED:
        return 126, ("inbox.py refuses to run 'git %s': only %s are allowed "
                     "in the watcher's checkout"
                     % (args[0] if args else "", "/".join(ALLOWED)))
    env = dict(os.environ)
    env.update({
        # No editor, no credential prompt, no pager. This runs in a window
        # nobody is watching, which is the 26 August incident exactly.
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_EDITOR": "true",
        "GIT_MERGE_AUTOEDIT": "no",
        "GIT_PAGER": "cat",
        "GIT_AUTHOR_NAME": COMMIT_NAME,
        "GIT_AUTHOR_EMAIL": COMMIT_EMAIL,
        "GIT_COMMITTER_NAME": COMMIT_NAME,
        "GIT_COMMITTER_EMAIL": COMMIT_EMAIL,
    })
    if extra_env:
        env.update(extra_env)
    try:
        p = subprocess.run(["git"] + list(args), cwd=repo, env=env,
                           capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return 127, "git is not on PATH on this PC"
    except subprocess.TimeoutExpired:
        return 124, "git %s did not finish within %d second(s)" % (args[0],
                                                                   timeout)
    except OSError as e:
        return 125, "could not run git (%s)" % type(e).__name__
    return p.returncode, (p.stdout + p.stderr).strip()


# --------------------------------------------------------------------------
# The format. One implementation, read by the bot and by the container.
# --------------------------------------------------------------------------
def message_name(sent_epoch, update_id):
    """`2026-09-05T1830Z-4127.md`, from the Telegram date in UTC."""
    t = datetime.datetime.fromtimestamp(int(sent_epoch), datetime.timezone.utc)
    return "%sT%sZ-%s.md" % (t.strftime("%Y-%m-%d"), t.strftime("%H%M"),
                             int(update_id))


def iso_utc(epoch):
    return datetime.datetime.fromtimestamp(
        int(epoch), datetime.timezone.utc).isoformat()


def render_message(text, sent_epoch, update_id):
    """The file's whole content.

    THE TEXT, THE TELEGRAM DATE AND THE UPDATE ID, AND NOTHING ELSE. No
    token, no chat id, no config path, no file name of the config: the
    credential rule ruled 2026-09-04 applies to what this writes into git
    exactly as it applies to what the bot prints.
    """
    body = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    return ("sent: %s\nsentEpoch: %d\nupdate: %d\n\n%s\n"
            % (iso_utc(sent_epoch), int(sent_epoch), int(update_id), body))


def parse_message(content):
    """(fields, None) or (None, reason). The header is the lines before the
    first blank one, so a body that itself starts with `sent:` cannot be
    mistaken for a header."""
    if not content or not content.strip():
        return None, "the file is empty"
    parts = content.replace("\r\n", "\n").split("\n\n", 1)
    head, body = parts[0], (parts[1] if len(parts) > 1 else "")
    fields = {}
    for line in head.split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    if "sentEpoch" not in fields:
        return None, ("no sentEpoch line in the first %d header line(s)"
                      % len(head.split("\n")))
    try:
        epoch = int(fields["sentEpoch"])
    except ValueError:
        return None, "sentEpoch is not a whole number of seconds"
    try:
        update = int(fields.get("update", "-1"))
    except ValueError:
        update = -1
    return {"sentEpoch": epoch, "sent": fields.get("sent", iso_utc(epoch)),
            "update": update, "text": body.strip()}, None


def message_files(repo):
    """Repository-relative paths of the message files on this disk, sorted.

    Pattern-matched rather than globbed for `*.md`, so the folder's README
    and anything a human drops there are outside every count this file
    prints.
    """
    d = os.path.join(repo, *INBOX_DIR.split("/"))
    if not os.path.isdir(d):
        return []
    return sorted("%s/%s" % (INBOX_DIR, n) for n in os.listdir(d)
                  if NAME_RE.match(n))


def outbound_files(repo):
    """Repository-relative paths of the outbound records on this disk, sorted.

    Same shape as `message_files`, pattern-matched against OUTBOUND_RE for the
    same reason: the count printed beside a zero must be the count of what was
    actually examined.
    """
    d = os.path.join(repo, *OUTBOUND_DIR.split("/"))
    if not os.path.isdir(d):
        return []
    return sorted("%s/%s" % (OUTBOUND_DIR, n) for n in os.listdir(d)
                  if OUTBOUND_RE.match(n))


def ruling_files(repo):
    """Repository-relative paths of the ruling records on this disk, sorted."""
    d = os.path.join(repo, *RULING_DIR.split("/"))
    if not os.path.isdir(d):
        return []
    return sorted("%s/%s" % (RULING_DIR, n) for n in os.listdir(d)
                  if RULING_RE.match(n))


def tracked_files(repo):
    """Everything this transport carries: inbound messages, outbound records
    and tapped rulings. One list, because one push moves all three."""
    return message_files(repo) + outbound_files(repo) + ruling_files(repo)


def ruling_name(tapped_epoch, update_id):
    """`2026-09-05T1830Z-5001.ruling.txt`, from Telegram's own clock."""
    t = datetime.datetime.fromtimestamp(int(tapped_epoch),
                                        datetime.timezone.utc)
    return "%sT%sZ-%s.ruling.txt" % (t.strftime("%Y-%m-%d"),
                                     t.strftime("%H%M"), int(update_id))


def render_ruling_record(card_id, option, tapped_epoch, update_id):
    """The whole content of a tapped ruling.

    THE CARD, THE LETTER, THE INSTANT, AND NOTHING ELSE. No chat id, no
    message id from the chat, no card text: the card text is already in
    `production/decision-queue.md` in the container, and the fold reads it
    from there. Same credential rule as `render_message`.
    """
    return ("tapped: %s\ntappedEpoch: %d\ncardId: %s\noption: %s\n"
            "update: %d\n"
            % (iso_utc(tapped_epoch), int(tapped_epoch), card_id,
               str(option).upper(), int(update_id)))


def parse_ruling_record(content):
    """(fields, None) or (None, reason). Every field is checked for SHAPE
    here, so the fold in the container never has to guess what a malformed
    record meant."""
    if not content or not content.strip():
        return None, "the file is empty"
    fields = {}
    for line in content.replace("\r\n", "\n").split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    if "cardId" not in fields:
        return None, "no cardId line"
    if not re.match(r"^[0-9a-f]{8}$", fields["cardId"]):
        return None, "cardId is not 8 hex characters"
    if not re.match(r"^[A-Z]$", fields.get("option", "")):
        return None, "option is not a single letter"
    try:
        epoch = int(fields.get("tappedEpoch", ""))
    except ValueError:
        return None, "tappedEpoch is not a whole number of seconds"
    try:
        update = int(fields.get("update", "-1"))
    except ValueError:
        update = -1
    return {"cardId": fields["cardId"], "option": fields["option"],
            "tappedEpoch": epoch, "update": update,
            "tapped": fields.get("tapped", iso_utc(epoch))}, None


def write_ruling(repo, card_id, option, tapped_epoch, update_id):
    """Write the record, return its repository-relative path."""
    rel = "%s/%s" % (RULING_DIR, ruling_name(tapped_epoch, update_id))
    full = os.path.join(repo, *rel.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_ruling_record(card_id, option, tapped_epoch,
                                      update_id))
    return rel


def write_message(repo, text, sent_epoch, update_id):
    """Write the file, return its repository-relative path.

    newline="\\n" because this file is read back on Linux from a branch. A
    Windows default would put CRLF into git and the two halves would differ
    in bytes for no reason anybody could see.
    """
    rel = "%s/%s" % (INBOX_DIR, message_name(sent_epoch, update_id))
    full = os.path.join(repo, *rel.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_message(text, sent_epoch, update_id))
    return rel


# --------------------------------------------------------------------------
# Awake or asleep, and when it next wakes
# --------------------------------------------------------------------------
def newest_work_commit(repo):
    """(epoch, basis) for the newest commit on the work branch, or (None, why).

    THE REMOTE-TRACKING REF FIRST, AND THE REASON IS THIS MACHINE'S OWN
    COMMITS. `pc-watcher.publish` commits onto the LOCAL work-branch ref and
    leaves it one ahead until the next pass resets it, and during a long job
    that can stand for hours. Reading the local ref would then report the
    PC's own publish as studio activity, which is the false-AWAKE direction
    this whole reply exists to avoid. `refs/remotes/origin/...` only moves
    when a fetch brings something down from GitHub.
    """
    for ref, basis in (("refs/remotes/origin/" + WORK_BRANCH,
                        "origin/" + WORK_BRANCH),
                       ("refs/heads/" + WORK_BRANCH,
                        "local/" + WORK_BRANCH + "/may-include-this-PCs-own")):
        rc, out = git_call(["log", "-1", "--format=%ct", ref], repo)
        if rc == 0 and out.strip().isdigit():
            return int(out.strip()), basis
    return None, "no-work-branch-ref-in-this-checkout"


def studio_state(newest_epoch, now_epoch):
    """("awake"|"asleep"|"unknown", age_seconds or None). No clamping: a
    newest commit in the future (a clock disagreement) comes back negative
    rather than as zero, because zero would read as normal."""
    if newest_epoch is None:
        return "unknown", None
    age = int(now_epoch) - int(newest_epoch)
    return ("awake" if age <= AWAKE_WITHIN_MIN * 60 else "asleep"), age


def next_wake_epoch(now_epoch):
    """The next 04:00 UTC strictly after now."""
    now = datetime.datetime.fromtimestamp(int(now_epoch),
                                          datetime.timezone.utc)
    wake = now.replace(hour=DAILY_WAKE_HOUR_UTC, minute=0, second=0,
                       microsecond=0)
    if wake <= now:
        wake += datetime.timedelta(days=1)
    return int(wake.timestamp())


def human_duration(seconds):
    """`9h 32m`, `45m`, `0m`. Negative is printed with its sign rather than
    hidden, because a negative age means two clocks disagree."""
    s = int(seconds)
    sign = "-" if s < 0 else ""
    s = abs(s)
    h, m = s // 3600, (s % 3600) // 60
    return "%s%dh %dm" % (sign, h, m) if h else "%s%dm" % (sign, m)


def wake_sentence(now_epoch):
    """When the studio next wakes, in UTC and on this PC's own clock.

    THE LOCAL HOUR IS READ FROM THE MACHINE, NOT ASSUMED TO BE CEST. NOW.md
    says 04:00 UTC is 06:00 CEST, which is true in summer and wrong from
    late October. `time.localtime` on Jafar's PC is the measurement.
    """
    wake = next_wake_epoch(now_epoch)
    local = time.strftime("%H:%M", time.localtime(wake))
    return ("It next wakes at %02d:00 UTC (%s on this PC's clock), in %s."
            % (DAILY_WAKE_HOUR_UTC, local, human_duration(wake - now_epoch)))


def studio_sentence(state, age_seconds, now_epoch):
    """What the bot tells Jafar about when this will be read.

    EVERY BRANCH NAMES THE NEXT WAKE, INCLUDING THE AWAKE ONE. Ruled
    2026-09-05 (088 batch, section 8) and it inverts what this used to do.
    AWAKE is read from a commit that is up to AWAKE_WITHIN_MIN minutes old, so
    the turn it infers may already have ended: "minutes to an hour" was then
    the only number he had, and it was the optimistic one. He now gets both,
    the likely case and the worst case, which is the same shape the other two
    branches already used.
    """
    basis = ("Awake or asleep is read from the newest commit on the work "
             "branch, which is a proxy until the studio can say so itself.")
    if state == "awake":
        return ("The studio looks AWAKE: the work branch has a commit from %s "
                "ago. It reads the inbox at the start of a turn and at every "
                "spawn boundary, so this reaches it in minutes to an hour. "
                "Worst case, if that turn has in fact ended, it reads this at "
                "the next wake. %s\n%s"
                % (human_duration(age_seconds), wake_sentence(now_epoch),
                   basis))
    if state == "asleep":
        return ("The studio looks ASLEEP: no commit on the work branch for "
                "%s. %s If it is only mid-step you will hear sooner.\n%s"
                % (human_duration(age_seconds), wake_sentence(now_epoch),
                   basis))
    return ("I cannot tell whether the studio is awake from this PC: there is "
            "no work-branch reference in this checkout. Worst case it reads "
            "this at the next wake. %s\n%s"
            % (wake_sentence(now_epoch), basis))


def studio_key(state, age_seconds, basis):
    """The console line's half. No spaces inside a value."""
    return ("studioState=%s workBranchAgeSec=%s awakeWithinSec=%d "
            "awakeBasis=%s"
            % (state, "unknown" if age_seconds is None else age_seconds,
               AWAKE_WITHIN_MIN * 60, basis))


# --------------------------------------------------------------------------
# The push
# --------------------------------------------------------------------------
def tip_sha(repo):
    """The local parent pointer, or None. Verifies the OBJECT is here, not
    just the ref: a ref pointing at a pruned object would fail inside
    commit-tree with a message about a bad revision."""
    rc, out = git_call(["rev-parse", "--verify", "--quiet", TIP_REF + "^{commit}"],
                       repo)
    sha = out.strip()
    if rc != 0 or not re.match(r"^[0-9a-f]{40}$", sha):
        return None
    return sha


def tree_paths(repo, sha):
    """Every path in that commit's tree under the three folders it carries.

    RULING_DIR IS IN THIS LIST, and it has to be: `pending_all` subtracts this
    set from what is on disk, so a folder missing here is a file the bot
    pushes again on every pass and reports as pending for ever.
    """
    rc, out = git_call(["ls-tree", "-r", "--name-only", sha, "--", INBOX_DIR,
                        OUTBOUND_DIR, RULING_DIR], repo)
    if rc != 0:
        return set()
    return {p.strip() for p in out.splitlines() if p.strip()}


def pending_files(repo):
    """Message files on this disk that the inbox branch does not carry.

    DERIVED, NEVER REMEMBERED. A state file would go stale exactly when the
    bot crashed mid-push, which is the one moment it has to be right. The
    tip's own tree is the record, so a restart, a crash or a second bot all
    reach the same answer.
    """
    here = message_files(repo)
    sha = tip_sha(repo)
    if sha is None:
        return here, None
    there = tree_paths(repo, sha)
    return [f for f in here if f not in there], sha


def pending_all(repo):
    """Everything of either kind that the branch does not carry yet.

    `pending_files` stays MESSAGES ONLY because the bot's `inboxPending`
    counter and its denominator are about Jafar's messages, and folding
    receipts into that number would make one key mean two things. The push
    moves both, so it asks this one.
    """
    here = tracked_files(repo)
    sha = tip_sha(repo)
    if sha is None:
        return here, None
    there = tree_paths(repo, sha)
    return [f for f in here if f not in there], sha


def push_pending(repo, say=None, timeout=120):
    """Put every unsent message on `pc-inbox`. Returns a result dict.

    Keys: ok, pushed (list), pending (list), commit, replaced, detail.
    A failure returns ok False with everything still on disk and named in
    `pending`, which is the whole reason this is a separate step from the
    write.
    """
    say = say or (lambda _s: None)
    out = {"ok": True, "pushed": [], "pending": [], "commit": None,
           "replaced": False, "detail": ""}
    pending, tip = pending_all(repo)
    if not pending:
        out["detail"] = "nothing to push"
        return out
    # THE TREE: the tip's tree plus the new files when the parent is here,
    # and the whole local folder when it is not. The second case only
    # happens in a checkout that has never pushed an inbox commit, which
    # after a re-clone means the branch is rewritten from what this disk
    # holds. Said out loud rather than done quietly.
    index = os.path.join(repo, ".git", "ledger-inbox-index")
    try:
        if os.path.exists(index):
            os.remove(index)
    except OSError:
        pass
    env = {"GIT_INDEX_FILE": index}
    if tip:
        rc, msg = git_call(["read-tree", tip], repo, extra_env=env)
    else:
        out["replaced"] = True
        pending = tracked_files(repo)
        rc, msg = git_call(["read-tree", "--empty"], repo, extra_env=env)
    if rc != 0:
        out.update(ok=False, pending=pending,
                   detail="could not build the temporary index (%s)"
                          % one_line(msg, 120))
        return out
    for rel in pending:
        full = os.path.join(repo, *rel.split("/"))
        rc, blob = git_call(["hash-object", "-w", "--path", rel, "--", full],
                            repo, extra_env=env)
        if rc != 0 or not re.match(r"^[0-9a-f]{40}$", blob.strip()):
            out.update(ok=False, pending=pending,
                       detail="could not store %s (%s)" % (rel, one_line(blob, 120)))
            return out
        rc, msg = git_call(["update-index", "--add", "--cacheinfo",
                            "100644,%s,%s" % (blob.strip(), rel)], repo,
                           extra_env=env)
        if rc != 0:
            out.update(ok=False, pending=pending,
                       detail="could not index %s (%s)" % (rel, one_line(msg, 120)))
            return out
    rc, tree = git_call(["write-tree"], repo, extra_env=env)
    if rc != 0:
        out.update(ok=False, pending=pending,
                   detail="could not write the tree (%s)" % one_line(tree, 120))
        return out
    names = ", ".join(os.path.basename(p) for p in pending[:3])
    if len(pending) > 3:
        names += " (+%d more not named)" % (len(pending) - 3)
    msgs = len([p for p in pending if p.startswith(INBOX_DIR + "/")])
    outs = len(pending) - msgs
    args = ["commit-tree", tree.strip(), "-m",
            "inbox: %d file(s) from the PC, %d message(s) and %d outbound "
            "record(s) (%s)" % (len(pending), msgs, outs, names)]
    if tip:
        args += ["-p", tip]
    rc, commit = git_call(args, repo, extra_env=env)
    if rc != 0 or not re.match(r"^[0-9a-f]{40}$", commit.strip()):
        out.update(ok=False, pending=pending,
                   detail="could not make the commit (%s)" % one_line(commit, 120))
        return out
    commit = commit.strip()
    # FORCE, LIKE `pc-results`, AND FOR THE SAME REASON: one writer, so the
    # history is disposable and a force push can destroy nobody's work. It
    # is also what makes the rewrite case above land at all.
    rc, msg = git_call(["push", "--force", "origin",
                        "%s:refs/heads/%s" % (commit, INBOX_BRANCH)], repo,
                       timeout=timeout)
    if rc != 0:
        out.update(ok=False, pending=pending,
                   detail="the push failed (%s)" % one_line(msg))
        return out
    # THE EFFECT, NOT THE EXIT CODE (the CI rule, and pc-watcher's own scar:
    # `push` returns 0 for "everything up-to-date"). `ls-remote` asks the
    # remote what it now holds and, unlike a fetch, writes no FETCH_HEAD and
    # no local ref, so it cannot race the watcher.
    rc, remote = git_call(["ls-remote", "origin",
                           "refs/heads/" + INBOX_BRANCH], repo, timeout=timeout)
    seen = remote.split()[0] if rc == 0 and remote.strip() else ""
    if seen != commit:
        out.update(ok=False, pending=pending,
                   detail=("the push sent nothing: %s is not what %s holds "
                           "(%s)" % (commit[:7], INBOX_BRANCH,
                                     (seen[:7] or "no such branch"))))
        return out
    git_call(["update-ref", TIP_REF, commit], repo)
    try:
        os.remove(index)
    except OSError:
        pass
    out.update(pushed=pending, commit=commit,
               detail="pushed %d file(s) as %s" % (len(pending), commit[:7]))
    say("  inbox: %s to %s%s"
        % (out["detail"], INBOX_BRANCH,
           (" (no local tip pointer, so this push SETS the branch to the %d "
            "message file(s) on this PC rather than adding to it)"
            % len(pending)) if out["replaced"] else ""))
    return out


# --------------------------------------------------------------------------
# What the bot calls, and what it says back
# --------------------------------------------------------------------------
def file_and_push(repo, text, sent_epoch, update_id, say=None, now=None):
    """Write the message, push it, and return everything the reply needs."""
    say = say or (lambda _s: None)
    now = int(now if now is not None else time.time())
    rel = write_message(repo, text, sent_epoch, update_id)
    res = push_pending(repo, say)
    newest, basis = newest_work_commit(repo)
    state, age = studio_state(newest, now)
    res.update(file=rel, state=state, age=age, basis=basis, now=now)
    if not res["ok"]:
        say("  inbox: NOT PUSHED, %s. inboxPending=%d, nothing dropped"
            % (res["detail"], len(res["pending"])))
    say("  inbox: file=%s inboxPushed=%d/%d inboxPending=%d %s"
        % (rel, len(res["pushed"]), len(res["pushed"]) + len(res["pending"]),
           len(res["pending"]), studio_key(state, age, basis)))
    return res


def ruling_and_push(repo, card_id, option, tapped_epoch, update_id, say=None,
                    now=None):
    """Write the tapped ruling, push it, and return what the reply needs.

    THE SAME TRANSPORT AS A MESSAGE, deliberately: one branch out of the PC,
    one push, one retry path. A ruling held by a dead uplink is held on disk
    with everything else and `flush_inbox` clears it, so a tap is never lost
    to a wobble either.
    """
    say = say or (lambda _s: None)
    now = int(now if now is not None else time.time())
    rel = write_ruling(repo, card_id, option, tapped_epoch, update_id)
    res = push_pending(repo, say)
    newest, basis = newest_work_commit(repo)
    state, age = studio_state(newest, now)
    res.update(file=rel, state=state, age=age, basis=basis, now=now,
               option=str(option).upper(), cardId=card_id)
    say("  ruling: file=%s option=%s cardId=%s rulingPushed=%s %s"
        % (rel, res["option"], card_id, "yes" if res["ok"] else "NO",
           studio_key(state, age, basis)))
    return res


def ruling_reply_text(res, heading=None):
    """What he sees in the chat after a tap. The card is named back to him
    because a tap with no read-back is indistinguishable from a lost one."""
    what = ("Ruled %s on \"%s\"." % (res["option"], heading) if heading
            else "Ruled %s." % res["option"])
    if res["ok"]:
        first = ("%s Filed as %s and pushed to the %s branch. The studio "
                 "folds it into the decision queue when it next reads the "
                 "inbox; nothing else in the card is rewritten."
                 % (what, res["file"], INBOX_BRANCH))
    else:
        first = ("%s Kept on the PC as %s but NOT pushed yet: %s. %d file(s) "
                 "are waiting on disk and none are dropped; the next message "
                 "or the next minute retries them."
                 % (what, res["file"], res["detail"], len(res["pending"])))
    return "%s\n%s" % (first, studio_sentence(res["state"], res["age"],
                                              res["now"]))


def reply_text(res):
    """The message Jafar sees. Filed or held, then awake or asleep, always."""
    if res["ok"]:
        first = ("Filed as %s and pushed to the %s branch."
                 % (res["file"], INBOX_BRANCH))
    else:
        first = ("Kept on the PC as %s but NOT pushed yet: %s. %d message(s) "
                 "are waiting on disk and none are dropped; the next message "
                 "or the next minute retries them."
                 % (res["file"], res["detail"], len(res["pending"])))
    return "%s\n%s" % (first, studio_sentence(res["state"], res["age"],
                                              res["now"]))


# --------------------------------------------------------------------------
# SELFTEST. Local repositories, no network, accepting case first.
# --------------------------------------------------------------------------
def _fixture_git(args, cwd):
    """Fixture construction only. Deliberately NOT `git_call`: the whitelist
    is the thing under test, so the scaffolding must not go through it."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_EDITOR="true",
               GIT_AUTHOR_NAME="T", GIT_AUTHOR_EMAIL="t@example.com",
               GIT_COMMITTER_NAME="T", GIT_COMMITTER_EMAIL="t@example.com")
    p = subprocess.run(["git"] + list(args), cwd=cwd, env=env,
                       capture_output=True, text=True, timeout=120)
    return p.returncode, (p.stdout + p.stderr).strip()


def _repos():
    """A bare origin, a `watcher` clone standing on the work branch, and a
    `reader` clone. The shape Jafar's PC and this container are actually in."""
    import atexit
    import shutil
    import tempfile
    home = tempfile.mkdtemp()
    atexit.register(shutil.rmtree, home, True)
    far = os.path.join(home, "origin.git")
    _fixture_git(["init", "-q", "--bare", far], home)
    w = os.path.join(home, "watcher")
    _fixture_git(["clone", "-q", far, w], home)
    with open(os.path.join(w, "seed.txt"), "w", encoding="utf-8") as fh:
        fh.write("seed\n")
    _fixture_git(["add", "seed.txt"], w)
    _fixture_git(["commit", "-q", "-m", "seed"], w)
    _fixture_git(["checkout", "-q", "-b", WORK_BRANCH], w)
    _fixture_git(["push", "-q", "origin", "HEAD:" + WORK_BRANCH], w)
    _fixture_git(["fetch", "-q", "origin", WORK_BRANCH], w)
    r = os.path.join(home, "reader")
    _fixture_git(["clone", "-q", far, r], home)
    return home, far, w, r


def _selftest():
    passed, failed = [], []

    def check(name, cond, detail=""):
        (passed if cond else failed).append(name)
        print("  %-44s %s%s" % (name, "pass" if cond else "FAIL",
                                ("  : " + str(detail)) if not cond else ""))

    # ---- the format, both directions -----------------------------------
    epoch = 1788633012                       # 2026-09-05T18:30:12Z
    name = message_name(epoch, 4127)
    check("accept/name-is-dated-and-numbered",
          name == "2026-09-05T1830Z-4127.md", name)
    check("accept/name-matches-the-readers-pattern",
          bool(NAME_RE.match(name)), name)
    body = render_message("Seen the van again.\nThursday.", epoch, 4127)
    got, why = parse_message(body)
    check("accept/round-trips-through-the-parser",
          got and got["sentEpoch"] == epoch and got["update"] == 4127
          and got["text"] == "Seen the van again.\nThursday.", why or got)
    check("accept/carries-no-chat-id-and-no-token",
          "chat" not in body.lower() and "token" not in body.lower(), body[:60])
    tricky, _ = parse_message(render_message("sent: not a header\n\nreally",
                                             epoch, 1))
    check("accept/a-body-that-looks-like-a-header-is-body",
          tricky and tricky["sentEpoch"] == epoch
          and tricky["text"].startswith("sent: not a header"), tricky)
    for bad, expect in ((" ", "empty"), ("hello\n\nworld", "no sentEpoch"),
                        ("sentEpoch: soon\n\nx", "not a whole number")):
        got, why = parse_message(bad)
        check("reject/%s" % expect.replace(" ", "-"),
              got is None and why and expect in why, why or "ACCEPTED")

    # ---- the awake arithmetic, from planted clocks ----------------------
    now = 1788633012
    check("accept/fresh-commit-is-awake",
          studio_state(now - 240, now) == ("awake", 240))
    check("accept/exactly-on-the-bound-is-awake",
          studio_state(now - AWAKE_WITHIN_MIN * 60, now)[0] == "awake")
    check("reject/one-second-past-the-bound-is-asleep",
          studio_state(now - AWAKE_WITHIN_MIN * 60 - 1, now)[0] == "asleep")
    check("reject/no-ref-at-all-is-unknown",
          studio_state(None, now) == ("unknown", None))
    check("accept/a-future-commit-keeps-its-sign",
          studio_state(now + 90, now)[1] == -90, studio_state(now + 90, now))
    at_four = int(datetime.datetime(2026, 9, 5, 4, 0, 0,
                                    tzinfo=datetime.timezone.utc).timestamp())
    check("accept/next-wake-is-strictly-future",
          next_wake_epoch(at_four) == at_four + 86400)
    check("accept/next-wake-is-today-when-before-four",
          next_wake_epoch(at_four - 3600) == at_four)
    check("accept/duration-reads-as-hours-and-minutes",
          human_duration(34320) == "9h 32m" and human_duration(2700) == "45m"
          and human_duration(-90) == "-1m", human_duration(34320))
    asleep = studio_sentence("asleep", 11520, at_four - 3600)
    check("accept/asleep-says-asleep-and-names-the-next-wake",
          "ASLEEP" in asleep and "04:00 UTC" in asleep and "in 1h 0m" in asleep,
          asleep)
    check("accept/asleep-names-its-basis",
          "newest commit on the work branch" in asleep, asleep)
    awake = studio_sentence("awake", 240, at_four)
    # INVERTED 2026-09-05 BY THE 088 RULING. This asserted that the AWAKE
    # branch does NOT name a wake; it now asserts that it does, so the old
    # behaviour is what fails. A guard that cannot tell the two apart would
    # have let the optimistic-only reply come back unnoticed.
    check("accept/awake-says-awake-and-names-the-worst-case",
          "AWAKE" in awake and "04:00 UTC" in awake
          and "Worst case" in awake, awake)
    unknown = studio_sentence("unknown", None, at_four)
    check("accept/unknown-still-names-the-worst-case",
          "cannot tell" in unknown and "04:00 UTC" in unknown, unknown)
    check("accept/no-spaces-in-key-values",
          all(" " not in kv.split("=", 1)[1]
              for kv in studio_key("asleep", 900, "origin/x").split()),
          studio_key("asleep", 900, "origin/x"))

    # ---- the git guard, both outcomes ----------------------------------
    home, far, watcher, reader = _repos()
    rc, out = git_call(["rev-parse", "HEAD"], watcher)
    check("accept/an-allowed-subcommand-runs", rc == 0 and len(out) == 40, out)
    rc, out = git_call(["fetch", "origin"], watcher)
    check("reject/fetch-is-refused-before-it-runs",
          rc == 126 and "refuses" in out and "fetch" in out, out)
    rc, out = git_call(["pull"], watcher)
    check("reject/pull-is-refused-too", rc == 126, out)
    check("accept/fetch-is-not-on-the-whitelist-at-all",
          "fetch" not in ALLOWED and "pull" not in ALLOWED,
          "/".join(ALLOWED))

    # ---- the push, on a real repository --------------------------------
    before_head, _ = _fixture_git(["rev-parse", "HEAD"], watcher)
    _, head_before = _fixture_git(["rev-parse", "HEAD"], watcher)
    _, status_before = _fixture_git(["status", "--porcelain"], watcher)
    res = file_and_push(watcher, "Seen the van again.", epoch, 4127,
                        now=epoch + 5)
    check("accept/a-message-is-filed-and-pushed",
          res["ok"] and res["pushed"] == ["production/inbox/" + name]
          and res["pending"] == [], res["detail"])
    _, head_after = _fixture_git(["rev-parse", "HEAD"], watcher)
    check("accept/HEAD-did-not-move",
          head_after == head_before, "%s -> %s" % (head_before[:7],
                                                   head_after[:7]))
    _, status_after = _fixture_git(["status", "--porcelain"], watcher)
    # NOTHING STAGED AND NOTHING MODIFIED: every line the push added is an
    # untracked one. `git status` collapses an untracked directory, so the
    # assertion is on the STATUS CODE of the new lines rather than on the
    # path text, which would have been an assertion about git's display.
    new_lines = [l for l in status_after.splitlines()
                 if l not in status_before.splitlines()]
    check("accept/the-index-is-untouched-and-the-file-is-untracked",
          new_lines and all(l.startswith("??") for l in new_lines),
          status_after)
    check("accept/no-index-lock-was-left-behind",
          not os.path.exists(os.path.join(watcher, ".git", "index.lock")))
    # THE WATCHER'S OWN SHORT CIRCUIT, ASSERTED RATHER THAN ASSUMED.
    # `pc-watcher.deliver_before_discard` returns early when HEAD equals the
    # fetched branch sha, and stops the whole pass otherwise. HEAD unchanged
    # is exactly that condition.
    _, branch_sha = _fixture_git(["rev-parse", "refs/remotes/origin/"
                                  + WORK_BRANCH], watcher)
    check("accept/the-watchers-deliver-check-still-short-circuits",
          head_after == branch_sha, "%s vs %s" % (head_after[:7],
                                                  branch_sha[:7]))
    _, on_branch = _fixture_git(["ls-remote", far, "refs/heads/" + INBOX_BRANCH],
                                watcher)
    check("accept/the-branch-exists-on-the-remote",
          res["commit"] and on_branch.split()[0] == res["commit"], on_branch)
    check("accept/the-work-branch-did-not-move",
          _fixture_git(["ls-remote", far, "refs/heads/" + WORK_BRANCH],
                       watcher)[1].split()[0] == branch_sha)

    # A SECOND MESSAGE CHAINS ONTO THE FIRST rather than replacing it.
    res2 = file_and_push(watcher, "And again Thursday.", epoch + 600, 4128,
                         now=epoch + 605)
    check("accept/a-second-message-chains-and-keeps-the-first",
          res2["ok"] and not res2["replaced"]
          and len(tree_paths(watcher, res2["commit"])) == 2,
          sorted(tree_paths(watcher, res2["commit"])))
    check("accept/nothing-is-pending-after-a-good-push",
          pending_files(watcher)[0] == [], pending_files(watcher)[0])

    # ---- the rejecting case that matters: the push cannot happen -------
    _fixture_git(["remote", "set-url", "--push", "origin",
                  os.path.join(home, "no-such-remote.git")], watcher)
    res3 = file_and_push(watcher, "While the uplink is down.", epoch + 1200,
                         4129, now=epoch + 1205)
    held = os.path.join(watcher, "production", "inbox",
                        message_name(epoch + 1200, 4129))
    check("reject/a-failed-push-keeps-the-message-on-disk",
          not res3["ok"] and os.path.exists(held)
          and res3["pending"] == ["production/inbox/"
                                  + message_name(epoch + 1200, 4129)],
          res3["detail"])
    check("reject/and-says-how-many-are-waiting",
          "inboxPending" not in res3["detail"] and len(res3["pending"]) == 1
          and "waiting on disk" in reply_text(res3), reply_text(res3)[:90])
    check("reject/and-still-says-awake-or-asleep",
          any(w in reply_text(res3) for w in ("AWAKE", "ASLEEP",
                                              "cannot tell")),
          reply_text(res3)[-80:])
    check("reject/a-failed-push-leaves-no-index-lock",
          not os.path.exists(os.path.join(watcher, ".git", "index.lock")))
    _, head_now = _fixture_git(["rev-parse", "HEAD"], watcher)
    check("reject/and-HEAD-is-still-where-the-watcher-left-it",
          head_now == head_before, head_now[:7])

    # AND IT RECOVERS: the uplink comes back and the held message goes.
    _fixture_git(["remote", "set-url", "--push", "origin", far], watcher)
    res4 = push_pending(watcher)
    check("accept/the-held-message-goes-when-the-uplink-returns",
          res4["ok"] and len(res4["pushed"]) == 1
          and len(tree_paths(watcher, res4["commit"])) == 3, res4["detail"])

    # ---- the denominator ------------------------------------------------
    with open(os.path.join(watcher, "production", "inbox", "README.md"), "w",
              encoding="utf-8") as fh:
        fh.write("not a message\n")
    check("accept/a-readme-in-the-folder-is-not-counted-as-a-message",
          len(message_files(watcher)) == 3 and pending_files(watcher)[0] == [],
          message_files(watcher))
    check("accept/an-empty-checkout-counts-zero-of-zero",
          message_files(os.path.join(home, "nowhere")) == [])

    # ---- the tapped ruling, queue 090 ----------------------------------
    body = render_ruling_record("3f2a1b9c", "b", epoch, 5001)
    got, why = parse_ruling_record(body)
    check("accept/a-ruling-record-round-trips-uppercased",
          got and got["cardId"] == "3f2a1b9c" and got["option"] == "B"
          and got["tappedEpoch"] == epoch and got["update"] == 5001,
          why or got)
    check("accept/a-ruling-record-carries-no-chat-and-no-token",
          "chat" not in body.lower() and "token" not in body.lower(), body)
    check("accept/the-ruling-name-is-dated-and-matches-the-readers-pattern",
          ruling_name(epoch, 5001) == "2026-09-05T1830Z-5001.ruling.txt"
          and bool(RULING_RE.match(ruling_name(epoch, 5001))),
          ruling_name(epoch, 5001))
    for bad, expect in ((" ", "empty"), ("option: B\n", "no cardId"),
                        ("cardId: nothex1\noption: B\ntappedEpoch: 1\n",
                         "8 hex"),
                        ("cardId: 3f2a1b9c\noption: BB\ntappedEpoch: 1\n",
                         "single letter"),
                        ("cardId: 3f2a1b9c\noption: B\ntappedEpoch: soon\n",
                         "whole number")):
        got, why = parse_ruling_record(bad)
        check("reject/ruling-record-%s" % expect.replace(" ", "-"),
              got is None and why and expect in why, why or "ACCEPTED")
    res5 = ruling_and_push(watcher, "3f2a1b9c", "B", epoch + 1800, 5001,
                           now=epoch + 1805)
    rel5 = "%s/%s" % (RULING_DIR, ruling_name(epoch + 1800, 5001))
    check("accept/a-tap-is-filed-and-pushed-on-the-same-branch",
          res5["ok"] and res5["pushed"] == [rel5]
          and rel5 in tree_paths(watcher, res5["commit"]), res5["detail"])
    check("accept/the-tap-reply-names-the-option-and-the-file",
          "Ruled B" in ruling_reply_text(res5, "How close?")
          and rel5 in ruling_reply_text(res5, "How close?")
          and "How close?" in ruling_reply_text(res5, "How close?"),
          ruling_reply_text(res5, "How close?")[:100])
    check("accept/a-ruling-is-outside-the-message-denominator",
          len(ruling_files(watcher)) == 1
          and rel5 not in message_files(watcher)
          and rel5 in tracked_files(watcher),
          "%d ruling(s), %d message(s)" % (len(ruling_files(watcher)),
                                           len(message_files(watcher))))
    with open(os.path.join(watcher, "production", "rulings", "README.md"), "w",
              encoding="utf-8") as fh:
        fh.write("not a ruling\n")
    check("reject/a-readme-in-the-rulings-folder-is-not-a-record",
          len(ruling_files(watcher)) == 1, ruling_files(watcher))

    print("\ninbox --selftest: %s, %d passed, %d failed, %d case(s) run. "
          "THE TELEGRAM HALF IS NOT COVERED: no case here touches the "
          "network, and the push above went to a local bare repository."
          % ("PASS" if not failed else "FAILED", len(passed), len(failed),
             len(passed) + len(failed)))
    if failed:
        print("failed: " + ", ".join(failed))
    return 3 if failed else 0


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv[1:] else
             (print(__doc__) or 0))
