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
                     "--", str(ROOT / "Assets" / "Scripts"),
                     str(ROOT / "Assets" / "Editor")])
    m = re.search(r"checked (\d+) files, (\d+) shape error", out)
    if not m:
        return False, "ShapeCheck did not report (build failure?)"
    return m.group(2) == "0", "%s shape errors (%s files)" % (m.group(2), m.group(1))


def lint():
    # ASSETS/EDITOR TOO. It was checked by nothing: lint and ShapeCheck both
    # scanned only Assets/Scripts, so `CiBuild.cs` — the entry point the whole
    # Windows pipeline runs through — had never been linted or shape-checked,
    # and a typo in it costs a full twenty-eight-minute round trip to find.
    code, out = run(["python3", str(ROOT / "lint-usings.py"),
                     str(ROOT / "Assets" / "Scripts"), str(ROOT / "Assets" / "Editor")])
    m = re.search(r"checked (\d+) files, (\d+) missing-using", out)
    if not m:
        return False, "lint did not report"
    return m.group(2) == "0", "%s lint errors" % m.group(2)


def reach():
    """Layer 1 of the testing system: does anything actually call it.

    The gap analysis that found `Brandish` 0, `MayFrisk` 0 and `Misattribute` 0
    was done by hand, once, in an afternoon. This is it in a second, as a graph
    walk from every Core member the Game names — so a helper called by a
    running method counts as running, which the first version got wrong.

    The ledger in `ReachCheck/allow.json` carries a typed reason per entry and
    only counts down: wiring an API without deleting its entry fails too."""
    code, out = run(["dotnet", "run", "-c", "Release", "--project", str(ROOT / "ReachCheck"),
                     "--", str(ROOT / "Assets" / "Scripts" / "Core"),
                     str(ROOT / "Assets" / "Scripts" / "Game"),
                     "--tests", str(ROOT / "CoreTests"),
                     "--tests", str(ROOT / "SimHarness"),
                     "--tests", str(ROOT / "BalanceLab"),
                     "--tests", str(ROOT / "BarkGen"),
                     "--tests", str(ROOT / "Tier2Gen"),
                     "--allow", str(ROOT / "ReachCheck" / "allow.json")])
    m = re.search(r"reach ok — (\d+) on the ledger", out)
    if m:
        return True, "%s on the reach ledger" % m.group(1)
    m = re.search(r"reach FAILED — .*", out)
    return False, m.group(0) if m else "reach-check did not report (build failure?)"


def tools_tracked():
    """Every tool project CI runs is actually committed.

    THE TOOL WAS RIGHT AND THE REPOSITORY WAS EMPTY. `ledger/.gitignore` held
    `*.csproj` plus a hand-kept allowlist of four negations, so `ReachCheck`,
    `BalanceLab` and `BarkGen` were written, built and tested here and never
    committed. CI ran `dotnet run --project ledger/ReachCheck` against a
    directory with a Program.cs and no project and went red with "Couldn't find
    a project to run" — a build failure that says nothing about the build.

    Local green and CI red with no code difference between them is the worst
    shape a failure can take, and it cost every core-tests run for an evening.
    The ignore rule is now anchored so it cannot swallow a subdirectory; this
    checks the outcome rather than trusting the rule, because verifying the
    rule is verifying my own comment."""
    missing = []
    for proj in sorted(ROOT.glob("*/*.csproj")):
        code, out = run(["git", "ls-files", "--error-unmatch", str(proj)], cwd=str(ROOT))
        if code != 0:
            missing.append(proj.parent.name)
    if missing:
        return False, "UNTRACKED TOOL PROJECT(S): " + ", ".join(missing)
    n = len(list(ROOT.glob("*/*.csproj")))
    return True, "%d tool project(s) tracked" % n


def shape_files():
    """Layer 2 of the testing system, for the half that lives in files.

    `TextShape` covers every line the game generates and CoreTests sweeps it.
    This covers the clips and the manifests, where a fault is never a compile
    error and never a failing assertion — it is a clip that plays as silence,
    or two characters cast with the same throat."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "shape-check.py")])
    if "shape ok" in out:
        return True, "shape ok (clips, barks, manifests)"
    m = re.search(r"(\d+) problem\(s\)", out)
    bad = [l.strip() for l in out.splitlines() if l.strip().startswith("FAIL")]
    return False, "SHAPE: %s%s" % (m.group(1) + " problem(s): " if m else "",
                                   bad[0][:90] if bad else "did not report")


def voice_cast():
    """M17.3: a principal whose cast voice cannot reach them.

    `VoiceBank.VoiceFor` falls back to the crowd pool for an unknown id rather
    than throwing, which is right for robustness and means a MISCAST principal
    is an entirely silent bug. Two were found this way — `# Hal` carrying id
    `halvard` against a cast voice named `hal`, and `# Sera Kest` carrying id
    `sera` against `kest`. Both clips had been fetched weeks earlier and could
    never play.

    Fails on breakage (an alias pointing at no voice, a cast voice with no
    clip). REPORTS the not-yet-cast, because that is M17.3's remaining work and
    a check that is red for a known reason is one people learn to skip."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "voice-cast-check.py")])
    m = re.search(r"(\d+) principal\(s\) not cast yet", out)
    todo = m.group(1) if m else "0"
    if code == 0:
        return True, "voice cast ok (%s uncast principal(s))" % todo
    bad = [l.strip() for l in out.splitlines() if l.strip().startswith("- ")]
    return False, "VOICE CAST: " + (bad[-1][:90] if bad else "did not report")


def frame_drift():
    """Layer 3 of the testing system: the instrument that reads the render.

    SUSPECT THE INSTRUMENT FIRST. `tools/frame-drift.py` answers "what moved in
    the picture since the last build", and the expected answer is "nothing much"
    — which is also exactly what it would print if it were broken, if the sim
    had written no ledger, or if it were comparing the new file against itself.
    A tool whose failure mode is indistinguishable from its success mode gets
    believed, so its self-test is run here rather than trusted.

    Twenty-one checks, and the ones that matter are the negative space: a
    missing new ledger must be an ERROR and not a quiet zero, a dropped shot
    must be named, and a change of one part in twenty-five must survive the
    formatting."""
    code, out = run(["python3", str(ROOT.parent / "tools" / "frame-drift.py"), "--selftest"])
    m = re.search(r"selftest: (\d+) passed, (\d+) failed", out)
    if not m:
        return False, "frame-drift selftest did not report"
    return m.group(2) == "0", "%s frame-drift checks (%s failed)" % (m.group(1), m.group(2))


def stale_anchors():
    """Every break's anchor, checked for a single exact match.

    NEARLY FREE, and it finds the thing a break run reports as a survivor and
    nobody looks twice at. An anchor whose source has moved on matches zero
    times, so the break never runs — and `breakrun.py` counts that as a
    survivor in a list of survivors, which is where it goes to die.

    Sweeping all of them after the harness fix found three, in specs nobody
    had reason to suspect: two in `exposure` where the aperture line gained a
    daytime term, one in `perception` where a literal 0.35 became
    `StillBelow`. Both changes were right; the specs had simply rotted around
    them. That is three checks the project believed it had."""
    import json
    bad = []
    for spec in sorted((ROOT / "breaks").glob("*.json")):
        try:
            entries = json.loads(spec.read_text(encoding="utf-8"))
        except ValueError as e:                       # noqa: BLE001
            bad.append("%s unparseable: %s" % (spec.name, e))
            continue
        for i, b in enumerate(entries):
            src = ROOT / b["file"]
            n = src.read_text(encoding="utf-8").count(b["old"]) if src.exists() else 0
            if n != 1:
                bad.append("%s[%d] matches %dx" % (spec.name, i, n))
    if bad:
        return False, "STALE ANCHORS: " + "; ".join(bad[:4])
    return True, "0 stale anchors"


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
    for fn in (lint, shape, tools_tracked, reach, shape_files, voice_cast,
               frame_drift, stale_anchors, core_tests):
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
