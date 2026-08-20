#!/usr/bin/env python3
"""`AvenuesX`/`AvenuesZ` are unscaled source data. Reading them raw is a bug.

WHY THIS EXISTS
---------------
`StreetMap.WideBlocks` scales the whole city about the origin by `StretchX`
(2.15) and `StretchZ` (1.15). The `District.AvenuesX`/`AvenuesZ` arrays are the
UNSCALED input to that transform, so a coordinate taken straight out of them
describes a city that was never built.

FIVE places read them raw, and every one was wrong in the same direction:

  DistrictAt                   four districts looked 136-184m from their own
                               buildings; 38 of 52 block centres were in no
                               district and four districts contained none
  SimDirector.DistrictTour     aimed four of seven cameras at bare ground, and
                               the photographs were read for days as "the outer
                               districts look unbuilt"
  Population.Place             spawned four districts' residents off their own
                               district
  WorldBuilder ground extent   sized the ground plane -200..160 while blocks
                               reach -426..340, so the outer districts stand
                               off the edge of it

One idea, five implementations, and the four nobody looked at were the four
missing a line. `BoundsOf` and `CentreOf` now exist so the scaling cannot be
forgotten, and this refuses the raw read that would bypass them.

WHY A LINT RATHER THAN A RULE
-----------------------------
The rule "remember to scale" was available the whole time — `ScaleAbout`'s own
docstring says it exists so the grid, the blocks and the addresses "cannot
disagree, which is the failure this project finds in pairs more than any
other". It was written by the same hand that then read the arrays raw in four
other files. A rule that depends on remembering is a rule that decays.

WHAT IS ALLOWED
---------------
`StreetMap.cs` itself — it is where the transform lives and where the arrays
must be read to apply it. Declarations of the field. And the null/length guards
(`d.AvenuesX == null`, `.Length == 0`), which read no coordinate.

Usage:
    tools/lint-avenues.py            # walk the tree
    tools/lint-avenues.py --selftest
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCAN = ROOT / "ledger" / "Assets" / "Scripts"
OWNER = "StreetMap.cs"          # the transform lives here; it may read raw

# A raw coordinate read: the array indexed, or handed somewhere as a value.
INDEXED = re.compile(r"\bAvenues[XZ]\s*\[")
# Guards that touch no coordinate.
SAFE = re.compile(r"Avenues[XZ]\s*(==\s*null|!=\s*null|\.Length)")


def offenders(text, filename):
    """Return [(lineno, line)] for raw coordinate reads."""
    if filename == OWNER:
        return []
    out = []
    for n, line in enumerate(text.split("\n"), 1):
        stripped = line.strip()
        if stripped.startswith("///") or stripped.startswith("//"):
            continue                      # prose about the fault is not the fault
        if not INDEXED.search(line):
            continue
        # `d.AvenuesX.Length` is a guard; `d.AvenuesX[0]` is a coordinate.
        # A line may hold both, so remove the guards and look again.
        if not INDEXED.search(SAFE.sub("", line)):
            continue
        out.append((n, stripped))
    return out


def selftest():
    """Both directions, on the real strings this was written for."""
    bad = "                    float cx = (float)d.AvenuesX[d.AvenuesX.Length / 2];"
    hits = offenders(bad, "SimDirector.cs")
    assert len(hits) == 1, hits
    print("  selftest: rejects the tour camera's raw read")

    guard = "                    if (d?.AvenuesX == null || d.AvenuesZ == null) continue;"
    assert offenders(guard, "SimDirector.cs") == [], offenders(guard, "SimDirector.cs")
    print("  selftest: accepts a null guard")

    length = "                    if (d.AvenuesX.Length == 0 || d.AvenuesZ.Length == 0) continue;"
    assert offenders(length, "SimDirector.cs") == [], offenders(length, "SimDirector.cs")
    print("  selftest: accepts a length guard")

    prose = "        /// `AvenuesX`/`AvenuesZ` are UNSCALED. Never read d.AvenuesX[0] raw."
    assert offenders(prose, "SimDirector.cs") == [], offenders(prose, "SimDirector.cs")
    print("  selftest: accepts a comment that quotes the fault")

    own = "            minX = ScaleAbout(d.AvenuesX[0], 0, kx);"
    assert offenders(own, OWNER) == [], offenders(own, OWNER)
    print(f"  selftest: accepts a raw read inside {OWNER}, which owns the transform")

    print("lint-avenues: selftest ok (5 checks)")
    return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()

    files = sorted(SCAN.rglob("*.cs"))
    bad, scanned = [], 0
    for path in files:
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for n, line in offenders(text, path.name):
            bad.append((path.relative_to(ROOT), n, line))

    # THE DENOMINATOR (rule 3b): "0 raw reads" and "the walker found no files"
    # must not print the same way.
    if bad:
        print(f"lint-avenues: {len(bad)} raw avenue read(s) over {scanned} file(s):")
        for rel, n, line in bad:
            print(f"  {rel}:{n}: {line[:100]}")
        print("  Use StreetMap.BoundsOf / StreetMap.CentreOf — the arrays are unscaled.")
        return 1
    print(f"lint-avenues: 0 raw avenue reads ({scanned} files walked, "
          f"{OWNER} exempt as the owner of the transform)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
