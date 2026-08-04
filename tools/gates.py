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


def flaky():
    """Which gates have EVER gone red, and how often, across every kept run.

    WHY. Four gates went red tonight on one run each while passing on either
    side, and each time the first question was "is this new, or has it done
    this before?" — answered three separate times by hand-grepping the runs
    directory. A question asked three times in one night is a command.

    It matters more than it sounds. A gate that fails rarely for a reason
    nobody has named is worse than one that fails always: it trains everybody
    to read red as noise, and that is how a real failure walks through. Rarity
    is exactly what makes it dangerous, and rarity is what this counts.

    Reports the FAILING RATE, not a verdict. One in sixty may be a world state
    the probe does not guarantee, or a real bug that needs sixty runs to show
    — this cannot tell those apart and does not pretend to.
    """
    if not RUNS.is_dir():
        print("gates: no runs directory yet")
        return 0
    files = sorted(RUNS.glob("*.txt"))
    if not files:
        print("gates: no run files yet")
        return 0
    counts, examples = {}, {}
    for f in files:
        m = FAILING.search(read(f))
        if not m:
            continue
        for g in split_gates(m.group(1)):
            name = g.split("[", 1)[0].strip()
            counts[name] = counts.get(name, 0) + 1
            examples.setdefault(name, f.stem)
    if not counts:
        print(f"gates: no failures in {len(files)} kept run(s)")
        return 0
    print(f"gate failures across {len(files)} kept run(s):")
    for name, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        pct = 100.0 * n / len(files)
        note = "  <- rare, and rare is the dangerous kind" if n <= 2 else ""
        print(f"  {n:3}/{len(files)}  {pct:5.1f}%  {name:14} e.g. {examples[name]}{note}")
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
