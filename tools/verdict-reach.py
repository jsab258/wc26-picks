#!/usr/bin/env python3
"""Which lines the sim prints that the verdict throws away.

    python3 tools/verdict-reach.py          # the ones that never arrive
    python3 tools/verdict-reach.py --all    # and the ones that do

WHY THIS EXISTS.

The Windows job builds `verdict.txt` by grepping the player log through an
ALLOWLIST. A line the sim prints that matches nothing in that pattern is
dropped, silently, with every step reporting success — and `verdict.txt` is the
only channel out of CI this environment can read.

It has now cost three separate pieces of work:

  - `windowWarmth` swept the source colour the window investigation had been
    parked on for want of it. Filtered out.
  - `ringGrowth` measured the radius at which a noise ring stops reading as a
    ring. Filtered out.
  - `ALL GATES` — the repair that makes every gate's label readable on a GREEN
    run, which is where 35 of this game's 39 gate-label diagnostics live. Built,
    run, green, and not in the verdict. Written two hours after reading the
    workflow comment describing the first two.

Each time the fix was the same one-word edit to the allowlist, and each time it
was found by noticing a number was missing rather than by asking.

WHAT IT DOES. Reads the `grep -E` allowlist straight out of the workflow — not a
copy of it, because a copy is a second implementation that goes stale, which is
the fault this repository keeps paying for — and matches it against every
`Debug.Log` prefix in `SimDirector`.

WHAT IT DOES NOT DO. It does not fail anything, and it must not. Most of the
dropped lines SHOULD be dropped: "staging a loiter beside the market" is
narration, and a verdict full of narration is a log again. The judgement about
which ones matter is a person's, and this only makes the list cheap to read.

A number that is also on the `done.` line is not lost, either — this cannot see
that, and says so rather than pretending the list is a list of faults.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "ledger-build-windows.yml"
SIM = ROOT / "ledger" / "Assets" / "Scripts" / "Game" / "SimDirector.cs"

# The allowlist is a `grep -E "..."` line followed by the log path on the next
# line. Anchored on the path so a different grep in the same file cannot be
# picked up by accident.
ALLOWLIST = re.compile(r'grep -E "([^"]+)"\s*\\\s*\n\s*sim-run/player\.log')

# THE WHOLE STRING LITERAL, not the head up to the first interpolation.
#
# The first version stopped at `{`, and reported `SimDirector: <section> places`
# as DROPPED when it plainly arrives in every verdict: the allowlist matches it
# on `alley eyes=`, which sits deeper in that line than the head, past two
# interpolations. The workflow's own comment says it matches "on distinctive
# ASCII substrings rather than on a prefix" — and I wrote a checker that could
# only see prefixes, twenty minutes after writing it to suspect a different
# instrument.
#
# Interpolations stay in as `{...}` and cannot match a pattern, which is
# correct: whether an allowlist entry matches inside a computed value is not
# something this can promise, and claiming it would be the same overreach.
LOGGED = re.compile(r'Debug\.Log(?:Error)?\(\s*\$?"((?:[^"\\]|\\.){0,400})"')


def allow_patterns():
    m = ALLOWLIST.search(WORKFLOW.read_text(encoding="utf-8"))
    if not m:
        return None
    # Alternation, with grep's backslash escapes removed: `done\.` matches the
    # literal "done." and comparing substrings is what this needs.
    return [a.replace("\\", "").strip() for a in m.group(1).split("|") if a.strip()]


def main():
    if not WORKFLOW.is_file() or not SIM.is_file():
        print("verdict-reach: workflow or SimDirector not found")
        return 0
    allow = allow_patterns()
    if allow is None:
        # THE INSTRUMENT SAYS SO RATHER THAN REPORTING ZERO. An empty allowlist
        # would make every line look dropped; a failed parse reporting "nothing
        # is dropped" would be worse, and is the shape of every quiet failure
        # this repo has chased.
        print("verdict-reach: could not find the allowlist in the workflow — "
              "the grep may have been reformatted. NOT reporting a result.")
        return 0

    src = SIM.read_text(encoding="utf-8")
    # THE WHOLE CALL, NOT THE FIRST LITERAL IN IT.
    #
    # Second correction to this tool in ten minutes, and the same fault twice:
    # it kept reporting the places line as dropped when it arrives in every
    # verdict. Widening from "up to the first interpolation" to "the whole
    # string literal" was not enough either, because that line is built by
    # CONCATENATING literals and `alley eyes=` lives in a later fragment of the
    # same `Debug.Log(...)`.
    #
    # So the window is the call: from the head, forward through the source far
    # enough to cover the concatenation. Crude, and honest about being crude —
    # it can only over-report a line as REACHING, never as dropped, which is
    # the safe direction for a tool whose output is a to-do list.
    seen = {}
    for m in LOGGED.finditer(src):
        head = m.group(1)
        if not head.startswith("SimDirector: "):
            continue
        window = src[m.start():m.start() + 900]
        seen[head] = seen.get(head, False) or any(a in window for a in allow)
    kept = sorted(h for h, ok in seen.items() if ok)
    dropped = sorted(h for h, ok in seen.items() if not ok)
    heads = kept + dropped

    show_all = "--all" in sys.argv
    print(f"verdict-reach: {len(heads)} distinct SimDirector log prefixes, "
          f"{len(kept)} reach the verdict, {len(dropped)} do not.")
    print(f"  allowlist ({len(allow)} patterns): {', '.join(allow)}")
    if show_all and kept:
        print("\n  reaches the verdict:")
        for h in kept:
            print(f"    ok   {h}")
    print("\n  dropped by the allowlist — most of these SHOULD be, and a number "
          "also on the `done.` line is not lost:")
    for h in dropped:
        print(f"    ..   {h}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
