#!/usr/bin/env python3
"""Which gates are failing, across every verdict that has landed.

    python3 tools/gates.py          # the last 12 runs, newest commit first
    python3 tools/gates.py 30       # the last 30

WHY THIS EXISTS.

`landed.py` answers "did this commit come back". It does not answer the
question that actually matters at the end of a night: **of the runs that came
back, which ones are red and what is red about them.**

Six builds ran concurrently on 3 August. Reading six verdicts by hand means six
greps for `FAILING GATES`, in commit order worked out from a separate `git log`,
and the report rule this serves — *"check what LANDED, not what reported
success"* and *"lead with anything visibly broken"* — has to be obeyed at the
exact hour when doing six of anything by hand gets skipped.

It orders by COMMIT, not by file time. `verdict.txt` is the last run to LAND and
not the newest commit, and the same is true of the runs directory: a build
dispatched earlier on an older commit routinely finishes second. Sorting by
mtime would put a stale answer at the top of the list, which is the mistake this
repo keeps paying for in a new place each time.

It reports the gate NAMES verbatim, because they carry their own numbers. That
is deliberate in `SimDirector` — a gate that can only say its own name costs a
twenty-minute round trip to learn why — and it means this tool needs no
knowledge of what any gate means.

Exit status is 0 whatever it finds. A red run is a thing to read, not a thing to
fail a commit on: the commit that FIXES a red run would be blocked by it.
"""

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNS = ROOT / "game-design" / "sim-shots" / "runs"

# What the job writes when the build produced no player. Quoted, not
# paraphrased — see tools/verdict-keys.py, which matches the same marker.
NO_SIM = "NO PLAYER LOG"

FAILING = re.compile(r"FAILING GATES:\s*(.+)")
PASS = re.compile(r"\bpass=(True|False)\b")


def read(path):
    # errors="replace": these are written by a Windows runner and carry bytes
    # this side does not assume. A tool that throws on its own input is a tool
    # nobody runs twice.
    return path.read_text(encoding="utf-8", errors="replace")


def split_gates(line):
    """Split a FAILING GATES list on commas that separate gates.

    Gate names embed their own numbers in brackets — `law[denounced=2 marks=2]`
    — and those brackets contain commas. Splitting naively cuts a gate in half
    and reports two gates that do not exist, which is worse than not splitting
    at all.
    """
    out, depth, cur = [], 0, []
    for ch in line:
        if ch in "[(":
            depth += 1
        elif ch in "])":
            depth -= 1
        if ch == "," and depth <= 0:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur).strip())
    return [g for g in out if g]


def ordered_runs():
    """Every kept run, NEWEST COMMIT FIRST.

    `glob` returns files in whatever order the filesystem gives, and sorting
    those by name sorts by sha, which is sorting by nothing. Commit order is
    the only order in which "how long ago" means anything, so it is built once
    here and both readers use it.

    Runs whose commit is older than the log window are appended at the end,
    oldest-ish, rather than dropped — a run that fell off the log is still
    evidence about the past, and silently discarding it would make the counts
    disagree with the runs directory for no visible reason.
    """
    have = {p.stem: p for p in RUNS.glob("*.txt")}
    log = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%h", "-400"],
                         capture_output=True, text=True).stdout.split()
    out, seen = [], set()
    for sha in log:
        if sha in have:
            out.append((sha, have[sha]))
            seen.add(sha)
    out.extend((s, p) for s, p in sorted(have.items()) if s not in seen)
    # A BUILD THAT NEVER RAN A SIM IS NOT A RUN, and counting it as one makes
    # every gate look quieter than it is.
    #
    # Five builds on 4 August produced an eleven-line verdict — two on a Unity
    # licence seat, three on a compile error — and each one says so in words.
    # They have no gates in them, so they can never contribute a failure, and
    # leaving them in pushes "last N runs ago" up by one apiece and dilutes
    # every rate in the table. The first reading after those five showed the
    # live section EMPTY, which is a pleasant thing to be told by an instrument
    # that had just been handed five blanks.
    #
    # Exactly the repair made to `verdict-keys` an hour earlier, in this same
    # session, for the same reason — and rule 1's corollary says to grep for the
    # claim you have just falsified elsewhere, which I did not.
    return [(s, p) for s, p in out if NO_SIM not in read(p)]


def flaky():
    """Which gates have gone red, how often, and HOW LONG AGO.

    WHY. Four gates went red on one run each while passing on either side, and
    each time the first question was "is this new, or has it done this before?"
    — answered three separate times by hand-grepping the runs directory. A
    question asked three times in one night is a command.

    It matters more than it sounds. A gate that fails rarely for a reason
    nobody has named is worse than one that fails always: it trains everybody
    to read red as noise, and that is how a real failure walks through.

    THE FIRST VERSION HAD NO TIME AXIS AND THAT MADE IT LIE. It reported
    `bodies 6/64, 9.4%` beside `claims 22/64` and I wrote "bodies is the
    biggest untouched one" onto the queue off the back of it. All six `bodies`
    failures are from a hundred-minute window on 3 August — the runs during
    which the upside-down player was being diagnosed and repaired — and every
    one of the forty-odd runs since has passed it. It is not the most neglected
    gate in the project; it is the most thoroughly fixed thing in it.

    A rate with no recency is a claim about the present made entirely out of
    the past, and it pointed me at a solved problem while `claims` was failing
    on the newest run in the directory. So every gate now carries how many runs
    have passed since it last went red, and the ones that have gone quiet say
    so in words rather than being ranked as though they were live.

    Reports rates and recency, not verdicts. One in sixty may be a world state
    the probe does not guarantee or a real bug that needs sixty runs to show —
    this cannot tell those apart and does not pretend to.
    """
    if not RUNS.is_dir():
        print("gates: no runs directory yet")
        return 0
    runs = ordered_runs()
    if not runs:
        print("gates: no run files yet")
        return 0

    total = len(runs)
    counts, newest, ago = {}, {}, {}
    for i, (sha, path) in enumerate(runs):        # i == runs since, newest first
        m = FAILING.search(read(path))
        if not m:
            continue
        for g in split_gates(m.group(1)):
            name = g.split("[", 1)[0].strip()
            counts[name] = counts.get(name, 0) + 1
            if name not in newest:
                newest[name] = sha
                ago[name] = i

    if not counts:
        print(f"gates: no failures in {total} kept run(s)")
        return 0

    # QUIET IS A JUDGEMENT AND IT NEEDS A NUMBER. Ten clean runs is roughly a
    # night's dispatching here, which is long enough that a gate still failing
    # for a live reason would have shown it. It is a reading aid, not a
    # threshold anything depends on — nothing branches on it but the wording.
    QUIET = 10
    live = {k: v for k, v in counts.items() if ago[k] < QUIET}
    quiet = {k: v for k, v in counts.items() if ago[k] >= QUIET}

    print(f"gate failures across {total} kept run(s), newest commit first:")
    for name, n in sorted(live.items(), key=lambda kv: -kv[1]):
        pct = 100.0 * n / total
        when = "the newest run" if ago[name] == 0 else f"{ago[name]} run(s) ago"
        note = "  <- rare, and rare is the dangerous kind" if n <= 2 else ""
        print(f"  {n:3}/{total}  {pct:5.1f}%  {name:14} last {when}, e.g. {newest[name]}{note}")

    if quiet:
        print(f"\n  quiet — nothing red in the last {QUIET}+ runs. Fixed, or the "
              f"condition has not recurred:")
        for name, n in sorted(quiet.items(), key=lambda kv: ago[kv[0]]):
            pct = 100.0 * n / total
            print(f"  {n:3}/{total}  {pct:5.1f}%  {name:14} "
                  f"last {ago[name]} run(s) ago, at {newest[name]}")
    return 0


def main():
    if "--flaky" in sys.argv:
        return flaky()
    count = 12
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            print(f"gates: '{sys.argv[1]}' is not a number of runs")
            return 2

    if not RUNS.is_dir():
        print("gates: no runs directory yet")
        return 0
    have = {p.stem: p for p in RUNS.glob("*.txt")}
    if not have:
        print("gates: no run files yet")
        return 0

    log = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%h\t%s", "-400"],
                         capture_output=True, text=True).stdout.splitlines()

    shown = 0
    red = 0
    for entry in log:
        sha, _, subject = entry.partition("\t")
        if sha not in have:
            continue
        text = read(have[sha])
        # NAMED, NOT SKIPPED — the opposite of what `flaky()` does with the
        # same file, and on purpose.
        #
        # A build whose sim never ran dilutes a RATE, so the flakiness table
        # drops it. But "this commit's build never produced a sim" is exactly
        # what you want to be told when reading the last few runs, and the
        # first version of this loop printed it as `??? ` — indistinguishable
        # from a verdict this tool failed to parse. Two of those in a row is
        # how ninety minutes went into diagnosing a licence failure as a
        # compile error.
        #
        # Third site of one blindness tonight, and found by grepping for it
        # rather than by tripping over it, which is the corollary working.
        if NO_SIM in text:
            print(f"NOSIM {sha}  {subject[:58]}")
            print("        the build produced no player — licence or compile, see the verdict")
            shown += 1
            if shown >= count:
                break
            continue
        m = PASS.search(text)
        verdict = m.group(1) if m else "?"
        fails = FAILING.search(text)
        mark = "PASS" if verdict == "True" else "RED " if verdict == "False" else "??? "
        if verdict != "True":
            red += 1
        print(f"{mark} {sha}  {subject[:58]}")
        if fails:
            for g in split_gates(fails.group(1)):
                print(f"        {g}")
        shown += 1
        if shown >= count:
            break

    if shown == 0:
        print("gates: none of the recent commits has a verdict")
        return 0
    print()
    print(f"{shown} run(s) read, {red} not green. Newest commit first — NOT newest to land.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
