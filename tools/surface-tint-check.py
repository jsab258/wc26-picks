#!/usr/bin/env python3
"""THE GUARD A COMMENT PROMISED AND NOBODY HAD WRITTEN.

    python3 tools/surface-tint-check.py
    python3 tools/surface-tint-check.py --selftest

WHY IT EXISTS. ue-probe/Source/LedgerProbe/Public/SurfaceBind.h carries a
SECOND COPY of the procedural surface tints, whose first copy is the switch
in ledger/Assets/Scripts/Game/AssetLibrary.cs. The comment beside the copy
says, in its own words, that this tool "parses both files and refuses any
disagreement" and that the check "is the only thing that makes this table
trustworthy; a copied constant with no check over it is a constant that
drifts". THE TOOL DID NOT EXIST. The builder that added the table said so
plainly rather than leaving it, which is the only reason it is here.

A COMMENT PROMISING A GUARD IS NOT A GUARD. Until this ran, the two copies
of 0.18/0.13/0.08 and 0.78/0.66/0.18 were unguarded while the file claimed
they were guarded, which is worse than an ordinary duplicate: a reader who
believed the comment would not check.

WHICH SIDE IS AUTHORITATIVE. Unity's switch. D1 is a comparison between two
engines and the Unity street is the one that has shipped, so the C# value is
the fact and the C++ table is the copy. A disagreement is therefore reported
as the UE table being wrong, whichever was edited last.

WHAT IT DOES NOT CHECK, said so nobody reads more into a pass than is there:
only the TINTS of the procedural surfaces. Smoothness, emission, tiling and
pattern are copied too and are not compared here; the same shape of check
would cover them and the next hand to touch this file should widen it rather
than trust a green line about a narrower thing.
"""
import argparse
import pathlib
import re
import sys

# PATHS RESOLVE AGAINST THE REPOSITORY, NEVER THE WORKING DIRECTORY, and this
# file is the reason the rule is written down twice in this project. The first
# wiring of this tool into ledger/verify.py failed instantly with NOTHING
# MEASURED, because verify runs it from a different cwd and these were relative
# strings. The gate caught the tool's own bug the hour the tool was wired, which
# is the argument for wiring a guard immediately rather than "next session".
ROOT = pathlib.Path(__file__).resolve().parent.parent
UE = "ue-probe/Source/LedgerProbe/Public/SurfaceBind.h"
UNITY = "ledger/Assets/Scripts/Game/AssetLibrary.cs"
# The C# names are CamelCase, the C++ names are the spec's snake_case. The
# mapping is stated here rather than derived because it is the one thing the
# two files legitimately spell differently.
NAME_MAP = {"Interior": "interior", "PaintYellow": "paint_yellow"}


def parse_ue(text):
    """The C++ copy: an index-to-name array and a parallel tint table."""
    names = re.search(r'ProceduralSurfaceName\(int I\).*?\{.*?\{(.*?)\}',
                      text, re.S)
    tints = re.search(r'ProceduralSurfaceTint\(.*?const double T\[\d+\]\[3\]'
                      r'\s*=\s*\{(.*?)\};', text, re.S)
    if not names or not tints:
        return None, "the UE table did not parse"
    order = re.findall(r'"([a-z_]+)"', names.group(1))
    rows = re.findall(r'\{\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\}',
                      tints.group(1))
    if len(order) != len(rows):
        return None, ("the UE name list and tint table are different lengths: "
                      "%d name(s) against %d row(s)" % (len(order), len(rows)))
    return {n: tuple(float(v) for v in r) for n, r in zip(order, rows)}, None


def parse_unity(text):
    """The C# original: one case per surface, the tint its first Color."""
    out = {}
    for cs_name, spec_name in NAME_MAP.items():
        m = re.search(r'case\s+AssetLibrary\.' + cs_name +
                      r'\s*:.*?Make\(\s*new\s+Color\(\s*([0-9.]+)f\s*,\s*'
                      r'([0-9.]+)f\s*,\s*([0-9.]+)f\s*\)', text, re.S)
        if m:
            out[spec_name] = tuple(float(g) for g in m.groups())
    return out


def compare(ue, unity):
    """Findings, and the denominator is what was COMPARED, not what exists."""
    findings, compared = [], 0
    for name, u in sorted(unity.items()):
        if name not in ue:
            findings.append("%s: in the Unity switch and NOT in the UE table"
                            % name)
            continue
        compared += 1
        if ue[name] != u:
            findings.append(
                "%s: unity=%s ue=%s -- the UE table is the copy and is wrong"
                % (name, "/".join("%.4f" % v for v in u),
                   "/".join("%.4f" % v for v in ue[name])))
    for name in sorted(ue):
        if name not in unity:
            findings.append("%s: in the UE table and NOT in the Unity switch"
                            % name)
    return findings, compared


def run(root=None):
    root = pathlib.Path(root) if root else ROOT
    up, np_ = root / UE, root / UNITY
    for p in (up, np_):
        if not p.exists():
            print("surface-tint-check: NOTHING MEASURED, %s is not on disk" % p)
            return 2
    ue, err = parse_ue(up.read_text(encoding="utf-8"))
    if err:
        print("surface-tint-check: NOTHING MEASURED, %s" % err)
        return 2
    unity = parse_unity(np_.read_text(encoding="utf-8"))
    if not unity:
        print("surface-tint-check: NOTHING MEASURED, the Unity switch did not "
              "parse")
        return 2
    findings, compared = compare(ue, unity)
    if findings:
        print("surface-tint-check: FAIL %d disagreement(s) over %d surface(s) "
              "compared" % (len(findings), compared))
        for f in findings:
            print("   ", f)
        return 1
    print("surface-tint-check: ok - %d surface(s) compared, 0 disagreement(s), "
          "tintsOnly=yes/smoothness-emission-tiling-pattern-not-compared"
          % compared)
    return 0


def selftest():
    checks, fails = 0, []

    def ck(name, ok, why=""):
        nonlocal checks
        checks += 1
        if not ok:
            fails.append("%s: %s" % (name, why))

    # ACCEPTING CASE FIRST, and the live repository is the fixture, so doing
    # the work this tool prompts can never break the tool.
    rc = run()
    ck("accept/the live tree agrees", rc == 0, "run() returned %d" % rc)

    live_ue, err = parse_ue((ROOT / UE).read_text(encoding="utf-8"))
    ck("accept/the UE table parses", err is None and live_ue, err or "empty")
    live_unity = parse_unity((ROOT / UNITY).read_text(encoding="utf-8"))
    ck("accept/the Unity switch parses", len(live_unity) == len(NAME_MAP),
       "got %d of %d" % (len(live_unity), len(NAME_MAP)))

    # REJECTING CASES, synthetic, so the fixture cannot be broken by real work.
    bad = dict(live_unity)
    first = sorted(bad)[0]
    bad[first] = (bad[first][0] + 0.01, bad[first][1], bad[first][2])
    f, c = compare(live_ue, bad)
    ck("reject/a drifted tint is caught", len(f) == 1 and "wrong" in f[0],
       "findings=%r" % f)
    ck("reject/the denominator counts what was compared", c == len(NAME_MAP),
       "compared=%d" % c)

    f, _ = compare({}, live_unity)
    ck("reject/a surface missing from the UE table is caught",
       len(f) == len(live_unity), "findings=%r" % f)
    f, _ = compare(live_unity, {})
    ck("reject/a surface missing from the Unity switch is caught",
       len(f) == len(live_unity), "findings=%r" % f)

    ue2, err2 = parse_ue("nothing that looks like the table")
    ck("reject/an unparseable UE table says nothing measured",
       ue2 is None and err2, "err=%r" % err2)

    print("surface-tint-check selftest: %d ok, %d failed, over %d check(s) "
          "(accepting first: 3 of them)"
          % (checks - len(fails), len(fails), checks))
    for f in fails:
        print("  FAIL", f)
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else run())
