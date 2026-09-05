#!/usr/bin/env python3
"""THE ONE COUNTER OF THE WORK QUEUE. Ready, blocked, done, from one directory.

    python3 tools/queue-check.py            # count production/queue/ and report
    python3 tools/queue-check.py --root DIR # count a planted tree instead
    python3 tools/queue-check.py --selftest # both outcomes, accepting first

WHY THIS EXISTS.

`game-design/queue.md` was written on 3 August to stop a specific failure: four
idle gaps of 20, 32, 19 and 28 minutes, each one immediately after dispatching a
build, because the moment after a dispatch is a decision point and re-deriving
priorities from a 400-line roadmap is enough friction to lose to.

It worked, for an hour. Eighteen commits, longest gap eight minutes. Then three
more gaps, 21, 28 and 28, and the cause was not that the rule was forgotten. THE
QUEUE HAD RUN OUT. Every non-CI item had been done, and what remained was
waiting on a build or waiting on Jafar.

WHY IT WAS REPOINTED, 2026-09-05, queue 079 under the ruling of that date,
section 7(d). The v2 respec retired `game-design/queue.md` on 31 August and the
live queue became `production/queue/`. This program went on reading the retired
file, so `ledger/.verify-footer` printed "22 queue items ready" through three
separate commits that added sixteen files, then one, then more. A COUNT THAT
CANNOT MOVE IS NOT A MEASUREMENT, and that one sat in the single channel every
session and every director reads. The selftest below adds a file to a planted
tree and asserts the number moves, which is the case the old reading could not
have passed.

ONE IMPLEMENTATION PER IDEA. `count_queue()` is the only queue counter in this
repository: `ledger/verify.py` reads this program's done line for the footer,
and `tools/morning-brief.py` imports `count_queue` directly, so the brief and
the footer can never print two different numbers for one directory.

WHAT IT COUNTS, and the classification is mechanical and printed. Every `*.md`
at the top of `production/queue/` is an item, README.md excepted BY NAME and
counted as exempt. Each item is classed by the FIRST WORD of its `status:`
line: BLOCKED, WAITS or WAITING is blocked; LANDED is landed-in-place (done
work whose file has not moved yet, and NOT ready); anything else, including a
file carrying no status line at all, is ready. Files under `blocked/` and
`done/` are counted from their directories. A file with no status line is
counted as ready AND printed under its own count, because an item nobody has
statused is exactly the item a reader should look at.

EXIT CODES, distinct per outcome. 0 the queue is deep enough. 1 it is too thin
or the standing track is missing. 2 nothing measured: the queue directory does
not exist, which is not the same as an empty queue and must never read as one.
3 the selftest failed.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# THE LIVE QUEUE, and the retired file that is NOT read. The retired path is
# named in the output on every run rather than left out, because the fault this
# repoint fixes was invisible precisely because nothing printed which file the
# number came from.
QUEUE_REL = "production/queue"
RETIRED_REL = "game-design/queue.md"
RETIRED_ON = "2026-08-31, by the v2 respec"

# Documentation, not an item. Named rather than pattern-matched, and counted.
EXEMPT_NAMES = ("README.md",)

# THE STANDING TASK, named by production/queue/README.md: a recurring item that
# re-enqueues itself, so "no short work left" is never the same sentence as "no
# work left". Named as a filename rather than sniffed, so its absence is a
# finding and not a guess.
STANDING_NAME = "900-process-audit.md"

# Classification by the first word of the status line. Extra words after the
# first are ignored on purpose: `status: BLOCKED 2026-09-01. Hardware, not
# effort` and `status: WAITS 2026-09-02 behind 027` are the two live forms.
BLOCKED_WORDS = ("BLOCKED", "WAITS", "WAITING")
LANDED_WORDS = ("LANDED",)

STATUS_RE = re.compile(r"^status:\s*(\S+)", re.M | re.I)

# BELOW THIS, REFILL BEFORE DISPATCHING. Three is not a measured optimum and is
# not presented as one: it is one item to work on plus two behind it, which is
# the smallest number that survives discovering the first is blocked. Rule 2
# says do not invent thresholds; this is a floor on a COUNT rather than a bound
# on a measurement, and the failure it guards is "zero", which needs no
# calibration.
FLOOR = 3

STATUS_WORDS_SHOWN = 6      # cap; announces when it bites, below.


def _md_files(d):
    return sorted(p for p in d.glob("*.md") if p.is_file())


def count_queue(root=ROOT):
    """Every number this repository prints about the queue, from one walk.

    PURE-ISH: reads files, writes nothing, returns data. The report function
    formats and the selftest drives it with planted trees. Returns None for
    `walked` when the queue directory is absent, which is the nothing-measured
    case and is never reported as an empty queue.
    """
    root = pathlib.Path(root)
    qdir = root / QUEUE_REL
    c = {
        "queue_dir": QUEUE_REL, "exists": qdir.is_dir(),
        "walked": 0, "exempt": 0, "ready": 0, "blocked": 0, "landed": 0,
        "unstatused": 0, "done": 0,
        "blocked_dir": False, "done_dir": False,
        "status_words": {}, "ready_names": [], "blocked_names": [],
        # The retired file is NOT read. Its presence is reported so that a
        # reader can see the tool knows about it and chose not to open it.
        "retired": RETIRED_REL,
        "retired_present": (root / RETIRED_REL).is_file(),
        "standing": False,
    }
    if not c["exists"]:
        return c
    for p in _md_files(qdir):
        if p.name in EXEMPT_NAMES:
            c["exempt"] += 1
            continue
        c["walked"] += 1
        if p.name == STANDING_NAME:
            c["standing"] = True
        text = p.read_text(encoding="utf-8", errors="replace")
        m = STATUS_RE.search(text)
        word = m.group(1).strip(".,:").upper() if m else ""
        if not word:
            c["unstatused"] += 1
        c["status_words"][word or "(no status line)"] = (
            c["status_words"].get(word or "(no status line)", 0) + 1)
        if word in BLOCKED_WORDS:
            c["blocked"] += 1
            c["blocked_names"].append(p.name)
        elif word in LANDED_WORDS:
            c["landed"] += 1
        else:
            c["ready"] += 1
            c["ready_names"].append(p.name)
    bdir = qdir / "blocked"
    if bdir.is_dir():
        c["blocked_dir"] = True
        moved = _md_files(bdir)
        c["blocked"] += len(moved)
        c["blocked_names"] += [p.name for p in moved]
    ddir = qdir / "done"
    if ddir.is_dir():
        c["done_dir"] = True
        c["done"] = len(_md_files(ddir))
    return c


def cap_list(items, keep=STATUS_WORDS_SHOWN, sep=", "):
    """A capped list that SAYS when the cap bit. A truncation that stays quiet
    reads as a finding."""
    items = list(items)
    if len(items) <= keep:
        return sep.join(items) if items else "nothing measured"
    return "%s (+%d more not shown of %d)" % (sep.join(items[:keep]),
                                              len(items) - keep, len(items))


def report(c, floor=FLOOR):
    """Every zero here ships the denominator that produced it."""
    if not c["exists"]:
        print("queue-check: nothing measured, no directory at %s/ under the "
              "root given. An absent queue is not an empty queue and this "
              "program refuses to print zero as if it were one."
              % c["queue_dir"])
        return 2
    # LINE ONE, HUMAN, and its shape is what ledger/verify.py has parsed since
    # 3 August. `item(s)` counts the top-level files only; `done` comes from
    # done/ and is not part of that total.
    print("queue-check: %d item(s), %d ready to start now, %d blocked, "
          "%d done, standing track %s"
          % (c["walked"], c["ready"], c["blocked"], c["done"],
             "present" if c["standing"] else "MISSING"))
    print("  counted under %s/: top-level files for ready and blocked-in-place,"
          " blocked/ and done/ for the moved ones. %d file(s) exempt by name "
          "(%s)." % (c["queue_dir"], c["exempt"], ", ".join(EXEMPT_NAMES)))
    print("  NOT READ: %s, retired %s. This program does not open it; the "
          "number above cannot come from it. Present in the tree: %s."
          % (c["retired"], RETIRED_ON, "yes" if c["retired_present"] else "no"))
    print("  status words, first word of each status line: %s"
          % cap_list("%s=%d" % (w, n) for w, n
                     in sorted(c["status_words"].items(),
                               key=lambda kv: (-kv[1], kv[0]))))
    print("  %d item(s) carry no status line at all and are counted as ready; "
          "%d carry LANDED in place and are counted as neither ready nor "
          "blocked" % (c["unstatused"], c["landed"]))
    if not c["blocked_dir"]:
        print("  %s/blocked/ does not exist, so every blocked item counted "
              "above is blocked IN PLACE by its status line" % c["queue_dir"])
    if not c["done_dir"]:
        print("  %s/done/ does not exist: nothing measured for done"
              % c["queue_dir"])

    problems = []
    if c["ready"] < floor:
        problems.append("only %d item(s) can be started now (want %d): refill "
                        "from the roadmap BEFORE the next dispatch"
                        % (c["ready"], floor))
    if not c["standing"]:
        problems.append("no standing task (%s): nothing to fall back on when "
                        "the short items run out, which is how the queue "
                        "emptied on 3 Aug" % STANDING_NAME)
    for p in problems:
        print("  " + p)
    # THE DONE LINE. Whole-walk numbers only, no spaces inside any value, one
    # instant: everything here comes from the single walk above.
    print("queue-check: %s queueReady=%d/%d queueBlocked=%d/%d queueDone=%d "
          "queueLanded=%d/%d queueUnstatused=%d/%d queueExempt=%d queueFloor=%d "
          "retiredNotRead=%s"
          % ("PASS" if not problems else "THIN",
             c["ready"], c["walked"], c["blocked"], c["walked"], c["done"],
             c["landed"], c["walked"], c["unstatused"], c["walked"],
             c["exempt"], floor, c["retired"]))
    return 1 if problems else 0


def _tree(files):
    """A throwaway root holding exactly `files`. Cleanup is REGISTERED rather
    than left to the reader: this runs inside ledger/verify.py."""
    import atexit
    import shutil
    import tempfile
    d = pathlib.Path(tempfile.mkdtemp(prefix="queue-check-"))
    atexit.register(shutil.rmtree, str(d), True)
    for rel, text in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return d


def _item(status):
    return "line: test\nspec: none\nacceptance: none\nmax_sessions: 1\n%s\n" % (
        ("status: " + status) if status else "")


def selftest():
    """Both outcomes, ACCEPTING CASE FIRST. The live repository is the
    accepting fixture, because this tool checks this project and doing the work
    it prompts must never break it; the rejecting fixtures are planted trees
    with names that exist nowhere."""
    passed, failed = 0, []

    def ok(name, cond, got=""):
        nonlocal passed
        if cond:
            passed += 1
            print("  ok   %s" % name)
        else:
            failed.append(name)
            print("  FAIL %s\n         got: %s" % (name, got))

    print("queue-check --selftest: ACCEPTING CASE FIRST\n")
    live = count_queue(ROOT)
    ok("the live queue directory exists and is walked (%d item(s))"
       % live["walked"], live["exists"] and live["walked"] > 0, live["walked"])
    ok("the live queue has at least the floor ready (%d of %d, floor %d)"
       % (live["ready"], live["walked"], FLOOR), live["ready"] >= FLOOR,
       live["ready"])
    ok("the standing task is present (%s)" % STANDING_NAME, live["standing"])
    ok("ready, blocked and landed account for every walked item (%d+%d+%d=%d)"
       % (live["ready"], live["blocked_dir"] and 0 or live["blocked"],
          live["landed"], live["walked"]),
       live["ready"] + live["landed"]
       + sum(1 for n in live["blocked_names"]
             if (ROOT / QUEUE_REL / n).is_file()) == live["walked"],
       (live["ready"], live["blocked"], live["landed"], live["walked"]))
    ok("the retired file is named and NOT opened (%s, present=%s)"
       % (live["retired"], live["retired_present"]),
       live["retired"] == RETIRED_REL)

    # THE CASE THE OLD READING COULD NOT PASS, and the whole reason for queue
    # 079: A COUNT THAT CANNOT MOVE. One planted tree, one contributor toggled
    # (a file added), both rungs read in this run from the same vantage.
    base = {"production/queue/README.md": "# docs\n",
            "production/queue/900-process-audit.md": _item("READY 2026-09-05"),
            "production/queue/001-a.md": _item("READY 2026-09-05"),
            "production/queue/002-b.md": _item("READY 2026-09-05"),
            "production/queue/003-c.md": _item("WAITS 2026-09-05 behind 001"),
            "production/queue/004-d.md": _item("LANDED 2026-09-05"),
            "production/queue/005-e.md": _item(""),
            "production/queue/done/000-old.md": _item("LANDED 2026-09-01")}
    t = _tree(base)
    before = count_queue(t)
    ok("a planted tree counts ready/blocked/done/landed exactly "
       "(%d/%d/%d/%d of %d walked, %d exempt)"
       % (before["ready"], before["blocked"], before["done"], before["landed"],
          before["walked"], before["exempt"]),
       (before["ready"], before["blocked"], before["done"], before["landed"],
        before["walked"], before["exempt"], before["unstatused"])
       == (4, 1, 1, 1, 6, 1, 1),
       (before["ready"], before["blocked"], before["done"], before["landed"],
        before["walked"], before["exempt"], before["unstatused"]))
    (t / "production/queue/006-f.md").write_text(_item("READY 2026-09-05"),
                                                 encoding="utf-8")
    after = count_queue(t)
    ok("THE COUNT MOVES when a file is added: ready %d then %d, walked %d "
       "then %d" % (before["ready"], after["ready"], before["walked"],
                    after["walked"]),
       after["ready"] == before["ready"] + 1
       and after["walked"] == before["walked"] + 1,
       (before["ready"], after["ready"]))
    # AND IT MOVES DOWNWARD TOO, so the guard can tell a regression from an
    # improvement rather than ratcheting one way.
    (t / "production/queue/006-f.md").write_text(_item("BLOCKED 2026-09-05"),
                                                 encoding="utf-8")
    moved = count_queue(t)
    ok("and it moves back when that file goes blocked: ready %d, blocked %d"
       % (moved["ready"], moved["blocked"]),
       moved["ready"] == before["ready"] and moved["blocked"]
       == before["blocked"] + 1, (moved["ready"], moved["blocked"]))

    print("\n  REJECTING FIXTURES, all planted, none pinned to a real file:\n")
    thin = _tree({"production/queue/README.md": "# docs\n",
                  "production/queue/900-process-audit.md":
                      _item("READY 2026-09-05"),
                  "production/queue/001-a.md": _item("BLOCKED 2026-09-05")})
    c_thin = count_queue(thin)
    ok("a queue with %d ready is refused against the floor of %d"
       % (c_thin["ready"], FLOOR), c_thin["ready"] < FLOOR, c_thin["ready"])
    nostanding = _tree({"production/queue/README.md": "# docs\n",
                        "production/queue/001-a.md": _item("READY"),
                        "production/queue/002-b.md": _item("READY"),
                        "production/queue/003-c.md": _item("READY")})
    c_ns = count_queue(nostanding)
    ok("a queue with no standing task is refused even with %d ready"
       % c_ns["ready"], c_ns["ready"] >= FLOOR and not c_ns["standing"],
       (c_ns["ready"], c_ns["standing"]))
    gone = _tree({"production/notes.md": "hello\n"})
    c_gone = count_queue(gone)
    ok("a MISSING queue directory is nothing measured, never an empty queue",
       not c_gone["exists"] and c_gone["walked"] == 0, c_gone)
    ok("and it exits 2, distinct from thin (1) and deep enough (0)",
       report(c_gone) == 2)
    ok("a retired-queue tree is still not read: a planted %s changes nothing"
       % RETIRED_REL,
       count_queue(_tree(dict(base, **{RETIRED_REL: "1. **x** ready\n"})))
       ["ready"] == before["ready"],
       "the counter opened the retired file")

    print("\nqueue-check --selftest: %s. %d passed, %d failed, over %d planted "
          "tree(s) and 1 live tree"
          % ("PASS" if not failed else "FAILED", passed, len(failed), 5))
    for f in failed:
        print("  " + f)
    return 0 if not failed else 3


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(ROOT),
                    help="repository root to count (default: this repo)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    return report(count_queue(a.root))


if __name__ == "__main__":
    # A correct run that ends in a BrokenPipeError traceback costs twenty
    # minutes before anybody notices it worked.
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    sys.exit(main())
