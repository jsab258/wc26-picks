#!/usr/bin/env python3
"""READ NUMBERS OUT OF A VERDICT, AND REFUSE TO COMPARE TWO FROM DIFFERENT LINES.

    python3 tools/verdict-read.py nameTagsOffered namesDistinctPeak
    python3 tools/verdict-read.py --run d05e8cd ikDropMedian ikPlantedDropMedian

WHY THIS EXISTS, AND IT IS THE MOST EXPENSIVE HOUR OF 4 AUGUST.

I spent an afternoon calling one pair of nameplate numbers an arithmetic
impossibility — 42 against 13, then 40 against 9 — publishing four explanations
across four builds, disproving each with the next, and finally DELETING a
counter that was never broken.

They were on different log lines. One is written on the done line at the end of
the run; the other on the `glyphs` line, which is emitted on every screenshot.
Same counters, two moments, and the peaks go on climbing after the last shot.
Nothing ever contradicted anything.

The tool was the cause. `grep -o 'a=[0-9]*\\|b=[0-9]*' verdict.txt` happily
returns one value from line 19 and another from line 69 and gives NO SIGN that
it has done so — the output looks exactly like two numbers from one reading.
That is rule 3 in its purest form: when a result is surprising, check the ruler
before the reading, and here the ruler was a shell one-liner.

CLAUDE.md already said a peak's denominator must come from the same INSTANT as
its numerator, and five sites had been fixed for the frame version of that.
Nobody noticed that the LOG LINE is part of the instant too. This makes that
mechanical instead of remembered.

WHAT IT REFUSES. If the keys asked for do not all appear on one line, it says
so, names the lines, and exits 2 — because the answer to "are these two
comparable" is no, and printing them side by side would be the exact mistake
this file exists to stop.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "game-design" / "sim-shots"


def newest_measuring_run():
    """The newest per-run verdict whose sim actually ran.

    A build that dies on a licence seat or a compile error still commits a
    verdict, so "newest file" and "newest answer" are different questions —
    the same distinction `landed.py` had to learn.
    """
    runs = sorted((SHOTS / "runs").glob("*.txt"),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    for p in runs:
        if "NO PLAYER LOG" not in p.read_text(encoding="utf-8", errors="replace"):
            return p
    return None


def main():
    argv = sys.argv[1:]
    run = None
    if "--run" in argv:
        i = argv.index("--run")
        run = SHOTS / "runs" / f"{argv[i + 1]}.txt"
        del argv[i:i + 2]
    keys = argv
    if not keys:
        print(__doc__.strip().split("\n\n")[1])
        return 2

    if run is None:
        run = newest_measuring_run()
    if run is None or not run.exists():
        print("verdict-read: no run has measured anything — nothing to read")
        return 1

    text = run.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")

    # WHERE EACH KEY IS, not just what it says. `key=` anchored on a word
    # boundary so `notoriety` does not match `notorietyPeak` — a substring hit
    # would reintroduce exactly the class of quiet wrong answer this exists to
    # stop, one layer down.
    found = {}
    for n, line in enumerate(lines, 1):
        for k in keys:
            m = re.search(r"(?<![\w])" + re.escape(k) + r"=(\[[^\]]*\]|\S+)", line)
            if m:
                found.setdefault(k, []).append((n, m.group(1)))

    missing = [k for k in keys if k not in found]
    for k in missing:
        print(f"MISSING  {k}  — not in {run.name}")

    print(f"# {run.name}: {lines[0]}")
    for k in keys:
        for n, v in found.get(k, []):
            print(f"  line {n:>4}  {k}={v}")

    # THE WHOLE POINT. Two numbers from two lines are two readings, and the
    # only honest thing to do with them is refuse to put them side by side.
    where = {k: {n for n, _ in v} for k, v in found.items()}
    shared = set.intersection(*where.values()) if len(where) == len(keys) and where else set()
    if missing:
        return 1
    if len(keys) > 1 and not shared:
        print()
        print("NOT COMPARABLE: these keys never appear together on one line.")
        print("A verdict carries several log statements written at different")
        print("moments — the done line once at the end of the run, the glyphs")
        print("line on every screenshot. Peaks keep climbing between them, so")
        print("two values from two lines are two readings and their difference")
        print("means nothing. This is the exact mistake that cost 4 August an")
        print("afternoon and a deleted counter.")
        return 2
    if len(keys) > 1:
        print(f"\ncomparable: all {len(keys)} keys share line {sorted(shared)[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
