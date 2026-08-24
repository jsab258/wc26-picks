#!/usr/bin/env python3
"""A gate that can only say its own name cannot be diagnosed.

WHY THIS EXISTS. `dayJob` failed 84 times across 308 runs — the second most
common failure in the project — and not one of those reds printed a reason,
because its entry in the gate table is the bare tuple `("dayJob", dayJobOk)`.
It went undiagnosed for months not through neglect but because there was
nothing to read. The moment it was given its three operands, the tracer beside
it named the cause in one landing.

SimDirector's own gate table carries the argument already, written for ONE
gate: "a gate that can only say its own name costs a twenty-minute round trip
to learn WHY, which is what this one cost the first time it fired." That
comment was applied to that gate and twenty others were left as they were.

A RATCHET ON A COUNT, NOT A LIST OF BLESSED NAMES. The eighteen that remain are
real debt and fixing them is a judgement per gate — each needs its condition
read and its operands chosen, which is work, not a rename. So this does not
demand they be fixed. It refuses a NINETEENTH.

A count rather than a baseline list because a list of names decays: it needs
editing whenever a gate is renamed, and an entry nobody re-reads is exactly the
failure the reach ledger keeps having. A single integer cannot go stale, and it
can only be lowered.

Usage:
    tools/gate-detail.py            # check
    tools/gate-detail.py --selftest
"""

import pathlib
import re
import sys

SRC = (pathlib.Path(__file__).resolve().parent.parent
       / "ledger" / "Assets" / "Scripts" / "Game" / "SimDirector.cs")

# Measured 24 Aug. Lower this when a gate is given its operands; it must never
# rise. `perf`, `dayJob` and `claims` came off it the day it was written.
CEILING = 18

BARE = re.compile(r'\("([A-Za-z]\w*)",\s*\w+Ok\)')
DETAILED = re.compile(r'\(\$"([A-Za-z]\w*)\[')


def scan(text):
    return sorted(set(BARE.findall(text))), sorted(set(DETAILED.findall(text)))


def selftest():
    # ACCEPTING CASE FIRST (rule 5b): a detailed gate is not counted as bare.
    ok = '($"places[alley={a} market={b}]", placesOk),'
    bare, det = scan(ok)
    assert bare == [] and det == ["places"], (bare, det)

    # REJECTING CASE: a bare tuple is seen.
    bad = '("dayJob", dayJobOk),'
    bare, det = scan(bad)
    assert bare == ["dayJob"] and det == [], (bare, det)

    # A gate must never be counted in BOTH — that would list it twice in the
    # table, which is a real mistake made once today: adding a detailed `perf`
    # while leaving the bare one in place.
    both = '("perf", perfOk),\n($"perf[samples={n}]", perfOk),'
    bare, det = scan(both)
    assert set(bare) & set(det) == {"perf"}, "selftest cannot see a doubled gate"

    print("gate-detail: selftest ok (3 checks, accepting case first)")
    return 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if not SRC.exists():
        print(f"gate-detail: {SRC} not found")
        return 1
    bare, det = scan(SRC.read_text(encoding="utf-8"))
    doubled = sorted(set(bare) & set(det))
    if doubled:
        print(f"gate-detail: GATE LISTED TWICE — {', '.join(doubled)} appears "
              f"both bare and detailed, so the table reports it twice")
        return 1
    if len(bare) > CEILING:
        added = ", ".join(bare)
        print(f"gate-detail: {len(bare)} gates cannot name their own failure, "
              f"ceiling is {CEILING}. A new one was added without its operands. "
              f"Bare: {added}")
        return 1
    note = "" if len(bare) == CEILING else f" — lower CEILING to {len(bare)}"
    print(f"gate-detail: {len(bare)} bare / {len(det)} detailed, "
          f"ceiling {CEILING}{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
