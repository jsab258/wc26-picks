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

# THE RATCHET, AND IT WENT UP ON 26 AUG BECAUSE THE SET IT COUNTS WAS WRONG.
#
# It was 18, measured 24 Aug, and the tool passed at 18 of 18 every run since.
# Measured properly against the gate table itself: **31 bare of 71 entries.**
# THIRTEEN bare gates matched neither pattern and were silently dropped —
# `jobRan`, `beats`, `discredit`, `disguise`, `knowledge`, `lamps`, `launder`,
# `noErrors`, `npcsMoved`, `screenshots`, `secretReachedDay`, `takingsBanked`,
# `verdictSane`.
#
# `BARE` required the second tuple element to be an identifier ending in `Ok`,
# so `("jobRan", jobRan)` and `("noErrors", _errors.Count == 0)` were invisible
# — and `jobRan` is the THIRD most common failure in the project's history
# (73 reds, 22.6%, `gates.py --flaky`). The tool exists because this file's own
# docstring says the SECOND most common one went undiagnosed for months for
# want of operands, and the third was sitting in its blind spot the whole time.
#
# THIS IS NOT A BOUND MOVED TO MAKE RED GO AWAY. Nothing was red; the tool
# passed. The DENOMINATOR was wrong, so the numerator counted a subset and the
# ratchet had thirteen gates it could not ratchet. Raising the integer to the
# measured truth makes the guard STRICTER — a fourteenth bare gate written in
# the unmatched form is now refused, where before it was uncountable. The rule
# is unchanged: lower it when a gate gains its operands, never raise it again
# without a measurement printed beside the change.
CEILING = 31

# WHERE THE GATES ARE. Scanning the whole 17,000-line file was safe only by
# accident of `BARE` being narrow; widening it makes any `("x", y)` tuple in
# the file a false gate. It was already leaking the other way — `render` was
# counted as DETAILED from outside the table, which is why "41 detailed" was
# one more than the 40 that exist.
TABLE_ANCHOR = "var gates = new (string name, bool ok)[]"

# A PLAIN string literal names a gate that can only say its own name.
# An INTERPOLATED one carrying a bracket is a gate that prints its operands.
# The discriminator is the `$`, which is the actual question being asked —
# not whether somebody happened to name a variable `somethingOk`.
#
# `(?<![\w])` BECAUSE A METHOD CALL IS ALSO AN OPEN PAREN AND A STRING. The
# table contains `$"samScars={_game.Harm.ScarsOf("Sam")} "`, and without this
# the sweep reported a gate called `Sam`. A permanent false positive in the
# unclassified bucket is worse than none: it is the one bucket that must be
# believed when it is non-empty, and a reader who learns to skip `Sam` skips
# the fourteenth real one too. An entry opens after a delimiter, never after
# an identifier character.
BARE = re.compile(r'(?<![\w])\(\s*"([A-Za-z]\w*)"\s*,')
DETAILED = re.compile(r'(?<![\w])\(\s*\$"([A-Za-z]\w*)\[')
# Anything else that opens an entry with a string: counted and NAMED, never
# dropped. A third shape nobody thought of is exactly what an allow-list eats.
ANY_ENTRY = re.compile(r'(?<![\w])\(\s*\$?"([A-Za-z]\w*)')


def table_of(text):
    """The gate table block, or None. NONE IS AN ERROR, NOT AN EMPTY SCAN.

    If the anchor is renamed this must say so in words. A scan that silently
    walks nothing prints `0 bare` and reads as the best possible result —
    rule 3b, and the reason `lint-static` printed 560 over 29.
    """
    if TABLE_ANCHOR not in text:
        return None
    i = text.index("{", text.index(TABLE_ANCHOR))
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
    return None


def scan(text):
    """`(bare, detailed, other)` over the gate table — three buckets, no drop.

    `other` is the denominator's honesty: an entry this tool cannot classify is
    reported by name rather than folded into the total or ignored.
    """
    bare = sorted(set(BARE.findall(text)))
    det = sorted(set(DETAILED.findall(text)))
    other = sorted(set(ANY_ENTRY.findall(text)) - set(bare) - set(det))
    return bare, det, other


def selftest():
    # ACCEPTING CASE FIRST (rule 5b): a detailed gate is not counted as bare.
    ok = '($"places[alley={a} market={b}]", placesOk),'
    bare, det, other = scan(ok)
    assert bare == [] and det == ["places"] and other == [], (bare, det, other)

    # REJECTING CASE: a bare tuple is seen.
    bad = '("dayJob", dayJobOk),'
    bare, det, other = scan(bad)
    assert bare == ["dayJob"] and det == [] and other == [], (bare, det, other)

    # THE THIRTEEN THAT WERE INVISIBLE, 26 Aug. `BARE` demanded the second
    # element be an identifier ending in `Ok`, so a gate whose condition is a
    # plain variable or an expression was not counted as bare and could not be
    # counted as detailed either — it simply left the arithmetic. `jobRan` is
    # the real one and it is the third most common failure in the project.
    missed = ('("jobRan", jobRan), ("noErrors", _errors.Count == 0),\n'
              '("lamps", WorldBuilder.LampToggleCount >= 2),')
    bare, det, other = scan(missed)
    assert bare == ["jobRan", "lamps", "noErrors"], bare
    assert det == [] and other == [], (det, other)

    # A gate must never be counted in BOTH — that would list it twice in the
    # table, which is a real mistake made once today: adding a detailed `perf`
    # while leaving the bare one in place.
    both = '("perf", perfOk),\n($"perf[samples={n}]", perfOk),'
    bare, det, _ = scan(both)
    assert set(bare) & set(det) == {"perf"}, "selftest cannot see a doubled gate"

    # AN ENTRY IN NEITHER SHAPE IS NAMED, NOT DROPPED. This is the bucket that
    # did not exist and is why 13 gates could go missing without a line.
    odd = '($"weird={x}", weirdOk),'
    bare, det, other = scan(odd)
    assert bare == [] and det == [] and other == ["weird"], (bare, det, other)

    # A METHOD CALL IS NOT A GATE ENTRY. Real line from the table; without the
    # lookbehind this reported a gate named `Sam`.
    # The claim is precisely that the NESTED `("Sam")` is not read as an entry;
    # the outer `($"samScars=...` legitimately is one, and lands in `other`
    # because it carries no bracket. Asserting `other == []` here would be
    # asserting the wrong thing — the first version of this fixture did.
    call = '($"samScars={_game.Harm.ScarsOf("Sam")}", scarsOk),'
    bare, det, other = scan(call)
    assert "Sam" not in bare + det + other, (
        "a method call's string argument was read as a gate entry", bare, other)
    assert bare == [] and other == ["samScars"], (bare, other)

    # THE TABLE LOCATOR: found, and MISSING SAYS SO rather than scanning zero.
    assert table_of('var gates = new (string name, bool ok)[]\n{ ("a", aOk), }'
                    ).strip().startswith("{"), "the anchor did not locate"
    assert table_of("no table here at all") is None, (
        "a missing table must be None, not an empty scan that prints 0 bare")

    print("gate-detail: selftest ok (8 checks, accepting case first)")
    return 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if not SRC.exists():
        print(f"gate-detail: {SRC} not found")
        return 1
    table = table_of(SRC.read_text(encoding="utf-8"))
    if table is None:
        print(f"gate-detail: nothing measured — the gate table anchor "
              f"`{TABLE_ANCHOR}` is not in {SRC.name}. This is not a clean "
              f"result; the scan walked no entries.")
        return 2
    bare, det, other = scan(table)
    doubled = sorted(set(bare) & set(det))
    if doubled:
        print(f"gate-detail: GATE LISTED TWICE — {', '.join(doubled)} appears "
              f"both bare and detailed, so the table reports it twice")
        return 1
    if len(bare) > CEILING:
        added = ", ".join(bare)
        print(f"gate-detail: {len(bare)} gates cannot name their own failure, "
              f"ceiling is {CEILING}. A new one was added without its operands. "
              f"Bare: {added} [arithmetic: {len(bare)}+{len(det)}+{len(other)}"
              f"={len(bare) + len(det) + len(other)} table entries walked]")
        return 1
    note = "" if len(bare) == CEILING else f" — lower CEILING to {len(bare)}"
    # THE ARITHMETIC, CHECKABLE ON THE LINE. `18 bare / 41 detailed` described
    # 59 of 71 entries and said nothing about the other 12, which is how the
    # thirteen stayed lost. Every entry now lands in exactly one bucket and the
    # sum is printed so a reader can see it does.
    unc = f", {len(other)} unclassified ({', '.join(other)})" if other else ""
    print(f"gate-detail: {len(bare)} bare / {len(det)} detailed{unc}, "
          f"ceiling {CEILING}{note} "
          f"[arithmetic: {len(bare)}+{len(det)}+{len(other)}="
          f"{len(bare) + len(det) + len(other)} table entries walked]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
