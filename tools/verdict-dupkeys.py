#!/usr/bin/env python3
"""One key, two values, two lines — the fault that cost an afternoon.

WHY THIS EXISTS
---------------
`verdict.txt` is space-separated `key=value` and everything that reads it
assumes a key means one thing.  `tools/verdict-read.py` already refuses when
the keys you ASK FOR do not share a line — that is the read-time guard, and it
was written after `grep -o` happily returned two values for `nameTagsOffered`
from two different lines and four builds were spent explaining the
"impossibility".

This is the other half: the WRITE-time guard.  `verdict-read.py` can only
protect a read somebody thought to route through it; nothing was looking at the
file as a whole and asking which keys are ambiguous before anyone greps them.

MEASURED, on the verdict landed at the time of writing: `collidingWorldText`
read **5** on the `SimDirector: glyphs` line and **9** on the `SimDirector:
done.` line of the same run.  Both honest — the glyphs line is emitted on day 2
and the shot-time samples keep raising the counter for another fifteen days —
and a `grep -o collidingWorldText=` returns whichever it reaches first, with no
sign it had a choice.  Eleven other keys had the same shape.  Nothing had ever
looked.

HOW A ROW FAMILY IS TOLD FROM A COLLISION, WITHOUT AN ALLOW-LIST
---------------------------------------------------------------
Most repeated keys in this file are legitimate: `ambSky` appears on
twenty-seven `SimDirector: sky dayN_*` lines, `diameter` on one row per vehicle
kind, `brightPct` on one row per frame.  Those SHOULD differ per line.

The signal that separates them needs no list of blessed prefixes, and matching
on the prefix does not work anyway (every sky row has its own prefix, so each
one looks like its own family).  A row family is a set of lines with the SAME
SHAPE — the same set of key names — so:

    family(line) = the sorted tuple of key names appearing on it

A key is ambiguous when it takes different values under two different
FAMILIES.  Twenty-seven sky rows share one family and are silent; `glyphs` and
`done.` have wildly different key-sets and are flagged.  Nothing to maintain and
nothing to forget to add, which is the property `SyntaxTree.GetDiagnostics()`
has over ShapeCheck's old allow-list.

THE TWO PROSE LINES ARE EXCLUDED, AND THAT IS A JUDGEMENT, SAID OUT LOUD
-----------------------------------------------------------------------
`SimDirector: ALL GATES:` and `SimDirector: FAILING GATES:` are not key=value
records.  They are sentences, and gate detail strings embed things that LOOK
like keys — `dressing[229 near=149/263 far=80/541]` yields `near`, `far`.
Reading those as verdict keys produces twenty false positives and no true ones.
It is the same distinction `lint-shadow` had to learn between a plain string
(prose) and an interpolated one (code), arrived at from the opposite side.

This IS an exclusion and exclusions are how allow-lists hide things, so it is
narrow, named, and printed: the tool reports how many lines it skipped, so
"nothing to report" cannot be confused with "nothing was examined" (rule 3b).

REPORT, NOT GATE — FOR NOW, AND FOR A STATED REASON
---------------------------------------------------
The landed verdict this ships beside still HAS the `collidingWorldText`
collision, because it came from the build before the fix.  A gate would
therefore go red on arrival and block every commit until a Windows round trip
landed — rule 5b's corollary exactly: a guard whose accepting case cannot be
produced yet.  So it prints and exits 0, and turns into a gate once a verdict
lands clean.  That decision is in `game-design/queue.md` rather than left to be
remembered.

Usage:
    tools/verdict-dupkeys.py [path]      default: game-design/sim-shots/verdict.txt
    tools/verdict-dupkeys.py --selftest
"""

import collections
import re
import sys

DEFAULT = "game-design/sim-shots/verdict.txt"

# Prose, not records. See the docstring — narrow, named, and counted.
PROSE_MARKERS = ("SimDirector: ALL GATES:", "SimDirector: FAILING GATES:")

KV = re.compile(r"([A-Za-z]\w*)=(\S*)")


def same_line(lines):
    """A key appearing TWICE ON ONE LINE with two values — the stronger fault.

    The cross-family test below is structurally blind to this: both copies sit
    on the same line, so they share a family and cancel out. It took a
    SEPARATE key (`SceneAudit: clean=True`) colliding with one of them to make
    the pair visible at all, which is luck, not a check.

    MEASURED: the done line carries `clean=310 dirty=0` from the purse and
    `[... crew=2 clean=0 dirty=251]` from the Act III snapshot — the same two
    names, one line, taken at different moments. `grep -o clean=` returned 310;
    it could as easily have returned 0.

    There is no legitimate reason for this. A reader that splits on whitespace
    keeps the last one, a reader using a regex keeps the first, and nothing
    warns either of them.
    """
    out = []
    for n, line in enumerate(lines, 1):
        if any(m in line for m in PROSE_MARKERS):
            continue
        by_key = collections.defaultdict(list)
        for k, v in KV.findall(line):
            if len(k) > 1:
                by_key[k].append(v)
        for k, vs in sorted(by_key.items()):
            if len(vs) > 1:
                out.append((n, k, vs))
    return out


def collisions(lines):
    """Return (findings, examined, skipped).

    findings: list of (key, {family: (sorted values, sorted line numbers)})
    examined: how many lines carried at least one key=value pair
    skipped:  how many were skipped as prose
    """
    seen = collections.defaultdict(lambda: collections.defaultdict(set))
    examined = skipped = 0
    for n, line in enumerate(lines, 1):
        if any(m in line for m in PROSE_MARKERS):
            skipped += 1
            continue
        pairs = KV.findall(line)
        if not pairs:
            continue
        examined += 1
        # A single-letter key is a fragment of something bracketed, never a
        # verdict key. `r=0.31` inside `[r=0.31 g=0.32]` is a colour channel.
        pairs = [(k, v) for k, v in pairs if len(k) > 1]
        family = tuple(sorted({k for k, _ in pairs}))
        for k, v in pairs:
            seen[k][family].add((v, n))

    out = []
    for key, by_family in seen.items():
        if len(by_family) < 2:
            continue
        values = {f: {v for v, _ in s} for f, s in by_family.items()}
        if len({frozenset(v) for v in values.values()}) < 2:
            continue  # same values everywhere: repeated, not ambiguous
        out.append((key, {
            f: (sorted(v), sorted({n for _, n in by_family[f]}))
            for f, v in values.items()
        }))
    out.sort()
    return out, examined, skipped


def selftest():
    """Both directions, because a guard nobody watched accept is half-shipped.

    The rejecting case is the REAL pair that prompted this, values and all.
    The accepting case is the row-family shape that must stay silent — three
    rows of one family with three different values, which a naive
    "same key, different value" check would flag and this one must not.
    """
    bad = [
        "SimDirector: glyphs labels=42 collidingWorldText=5 textWalked=391",
        "SimDirector: done. errors=0 collidingWorldText=9 lastDay=17",
    ]
    found, examined, _ = collisions(bad)
    assert examined == 2, examined
    assert [k for k, _ in found] == ["collidingWorldText"], found
    print("  selftest: rejects the real glyphs/done pair (collidingWorldText 5 vs 9)")

    good = [
        "SimDirector: sky day1_noon ambSky=0.520 density=0.0127",
        "SimDirector: sky day2_noon ambSky=0.610 density=0.0085",
        "SimDirector: sky day3_noon ambSky=0.480 density=0.0202",
    ]
    found, examined, _ = collisions(good)
    assert examined == 3, examined
    assert found == [], found
    print("  selftest: accepts 3 sky rows with 3 different values (one family)")

    prose = [
        "SimDirector: ALL GATES: ok lamps | ok dressing[229 near=149/263]",
        "SimDirector: done. near=12 lastDay=17",
    ]
    found, examined, skipped = collisions(prose)
    assert skipped == 1, skipped
    assert found == [], found
    print("  selftest: gate prose is skipped, and says it skipped 1 line")

    # AND THE EXCLUSION MUST NOT SWALLOW A REAL PAIR THAT MERELY MENTIONS A
    # GATE NAME. Only the two prose lines are skipped; a collision between two
    # ordinary record lines survives even when one of them names a gate.
    near_miss = [
        "SimDirector: glyphs lamps=3 textWalked=391",
        "SimDirector: done. lamps=9 lastDay=17",
    ]
    found, examined, skipped = collisions(near_miss)
    assert skipped == 0, skipped
    assert [k for k, _ in found] == ["lamps"], found
    print("  selftest: a real pair is still caught when it names a gate")

    # THE SAME-LINE CHECK, BOTH WAYS. The rejecting case is the real pair off
    # the landed done line; the accepting case is the same key on two lines,
    # which this check must NOT claim (that is the other function's job).
    twice = ["SimDirector: done. clean=310 dirty=0 crew=2 clean=0 dirty=251"]
    hits = same_line(twice)
    assert [(k, vs) for _, k, vs in hits] == [
        ("clean", ["310", "0"]), ("dirty", ["0", "251"])], hits
    print("  selftest: catches clean=/dirty= twice on one done line")

    assert same_line([
        "SimDirector: glyphs clean=1",
        "SimDirector: done. clean=2",
    ]) == [], "same-line check must not claim a cross-line pair"
    print("  selftest: and stays quiet on a cross-line pair")

    print("verdict-dupkeys: selftest ok (6 checks)")
    return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    path = next((a for a in argv[1:] if not a.startswith("-")), DEFAULT)
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
    except OSError as exc:
        print(f"verdict-dupkeys: cannot read {path}: {exc}")
        return 0

    found, examined, skipped = collisions(lines)
    twice = same_line(lines)
    # THE DENOMINATOR, ALWAYS. "0 ambiguous keys" and "the file was empty" must
    # not print the same way (rule 3b).
    print(f"verdict-dupkeys: {len(twice)} same-line and {len(found)} cross-line "
          f"ambiguous key(s) over {examined} record line(s), "
          f"{skipped} prose line(s) skipped")
    for n, key, values in twice:
        print(f"  {key} TWICE on line {n} -> {values}")
    for key, families in found:
        print(f"  {key}")
        for _, (values, where) in sorted(families.items(), key=lambda x: x[1][1]):
            print(f"    line(s) {where} -> {values}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
