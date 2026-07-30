#!/usr/bin/env python3
"""Run the local checks and print the footer that goes in a commit message.

    python3 ledger/verify.py                  # everything
    python3 ledger/verify.py --breaks voice   # and a break spec too

WHY THIS EXISTS, and it is not tidiness.

Twice in one night I ended a commit message with a check count I had not
read — "2764 CoreTests" when it was 2742, "2877" when it was 2883. Both
times the work was fine and the claim was decoration typed from memory, and
both times I only noticed because I happened to run the suite again
afterwards.

That is the same defect this project keeps finding in its own code: a
success recorded before the success happened. A number in a commit message
is a claim about a measurement, and the fix for an unreliable measurement is
never "be more careful" — it is to take the reading from the instrument
instead of from memory.

So the footer comes from here, and if a check is red this prints the failure
instead of a number.
"""
import argparse
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def core_tests():
    code, out = run(["dotnet", "run", "-c", "Release", "--project", str(ROOT / "CoreTests")])
    m = re.search(r"All (\d+) checks passed", out)
    if m:
        return True, "%s CoreTests" % m.group(1)
    fails = [l.strip() for l in out.splitlines() if l.strip().startswith("FAILED")]
    if fails:
        return False, "CoreTests RED: " + fails[0][:120]
    return False, "CoreTests did not report a count (build failure?)"


def shape():
    # NO `--nologo`. It is not a `dotnet run` option, so it is forwarded to
    # the APP — where it becomes args[0] and ShapeCheck dutifully tries to
    # enumerate a directory called "--nologo". The exception it threw was
    # reported here as "did not report", which is this script working exactly
    # as intended: it refused to print a green footer for a check that had
    # not actually run. First use, first catch.
    code, out = run(["dotnet", "run", "-c", "Release", "--project", str(ROOT / "ShapeCheck"),
                     "--", str(ROOT / "Assets" / "Scripts")])
    m = re.search(r"checked (\d+) files, (\d+) shape error", out)
    if not m:
        return False, "ShapeCheck did not report (build failure?)"
    return m.group(2) == "0", "%s shape errors (%s files)" % (m.group(2), m.group(1))


def lint():
    code, out = run(["python3", str(ROOT / "lint-usings.py"), str(ROOT / "Assets" / "Scripts")])
    m = re.search(r"checked (\d+) files, (\d+) missing-using", out)
    if not m:
        return False, "lint did not report"
    return m.group(2) == "0", "%s lint errors" % m.group(2)


def breaks(spec):
    path = ROOT / "breaks" / (spec if spec.endswith(".json") else spec + ".json")
    if not path.exists():
        return False, "no such break spec: %s" % path.name
    code, out = run(["python3", "breakrun.py", str(path)])
    m = re.search(r"(\d+) breaks, (\d+) survived", out)
    if not m:
        return False, "break run did not report (baseline red?)"
    stale = out.count("ANCHOR MATCHES")
    label = "%s/%s breaks RED" % (int(m.group(1)) - int(m.group(2)), m.group(1))
    if stale:
        label += ", %d STALE ANCHOR(S)" % stale
    return m.group(2) == "0" and stale == 0, "%s: %s" % (path.stem, label)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--breaks", action="append", default=[],
                    help="also run this break spec (repeatable)")
    args = ap.parse_args()

    parts, all_ok = [], True
    for fn in (lint, shape, core_tests):
        ok, text = fn()
        all_ok &= ok
        parts.append(text)
    for spec in args.breaks:
        ok, text = breaks(spec)
        all_ok &= ok
        parts.append(text)

    print()
    print("--- verification footer ---")
    print(", ".join(parts) + ".")
    print("---------------------------")
    if not all_ok:
        print("NOT GREEN — do not paste this into a commit message as if it were.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
