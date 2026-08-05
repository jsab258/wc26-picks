#!/usr/bin/env python3
"""COMPILE THE GAME LAYER LOCALLY, IN SECONDS INSTEAD OF TWENTY-EIGHT MINUTES.

    python3 tools/gamecheck.py

WHY THIS EXISTS, AND IT IS THE MOST EXPENSIVE STRUCTURAL FACT IN THE PROJECT.

The Game layer has never had a compiler here. Its first compiler was the Windows
CI build, so a wrong type name cost a ~28-minute round trip — and CLAUDE.md
records one that rode 18 commits and killed 4 consecutive builds, each of which
had been dispatched to answer a different live question. Every one came back
`NO PLAYER LOG` and answered nothing.

Everything downstream followed from that latency. Five separate lint tools
(`lint-shadow`, `lint-nested`, `lint-static`, `lint-filetype`,
`lint-namespace`) exist purely to APPROXIMATE five specific compiler errors by
matching names, because `ShapeCheck` is reference-independent and cannot resolve
a name. Each was written twice, because a name-matcher's first version always
flags code that compiles perfectly. That is a lot of machinery standing in for a
compiler nobody had.

WHAT CHANGED: Unity publishes its own reference assemblies to NuGet as
`UnityEngine.Modules`, and NuGet is reachable from this container. Compiling
Core + Game against the REAL Unity signatures produced 114 errors, and every
single one was a `UnityEngine.UI` type — uGUI ships as a separate Unity package
and is not in the modules feed. Four shim types in `GameCheck/Shims` close that,
and after them exactly ONE error remains, below.

THE ALLOW-LIST IS THE DANGEROUS PART AND IT IS BUILT TO FAIL BOTH WAYS.
CLAUDE.md: "An allow-list silently discards everything nobody thought of, and it
looks identical to a clean result." So this one is not a class of error, it is a
set of EXACT strings — and a known error that STOPS appearing fails the check
too, because that means the reason has expired and the entry is now hiding
whatever appears next in its place. An allow-list that cannot go stale is the
only kind worth having.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJ = ROOT / "ledger" / "GameCheck"

# ERRORS THAT ARE FALSE BECAUSE THE REFERENCE ASSEMBLIES ARE OLDER THAN THE
# EDITOR. Unity's newest published reference set is 2021.3.33; this project is
# on Unity 6, so an API renamed after 2021.3 reads as missing here while being
# correct in the real build.
#
# Each entry is the exact compiler text, and each needs a reason naming the
# Unity version that moved it. Anything else is a real error.
KNOWN = {
    "'RenderSettings' does not contain a definition for 'customReflectionTexture'":
        "renamed from `customReflection` in Unity 2022.1; correct for Unity 6 "
        "and absent from the 2021.3 reference assemblies",
}

ERR = re.compile(r"error (CS\d+): (.*?)(?: \[/|$)")


def main():
    if not PROJ.exists():
        print("gamecheck: no GameCheck project — nothing to compile")
        return 1

    r = subprocess.run(["dotnet", "build", "-v", "q", "--nologo"],
                       cwd=PROJ, capture_output=True, text=True, timeout=900)
    out = r.stdout + r.stderr

    seen, unexpected = set(), []
    for line in out.splitlines():
        m = ERR.search(line)
        if not m:
            continue
        text = m.group(2).strip()
        # Trim the "(are you missing ...)" tail so an entry is stable.
        text = re.sub(r"\s*\(are you missing[^)]*\)\s*$", "", text).strip()
        if text in KNOWN:
            seen.add(text)
            continue
        # DEDUPED, because msbuild reports each diagnostic once per target it
        # walks and a doubled list reads as twice the damage.
        where = re.sub(r"^.*?Scripts/", "", line.strip())
        where = re.sub(r"\s*\[/.*?\.csproj\]\s*$", "", where)
        if where not in unexpected:
            unexpected.append(where)

    # THE DENOMINATOR, because "no errors" and "nothing compiled" look
    # identical otherwise — rule 3b, and this check would be the third tool in
    # this project to report a clean zero having examined nothing.
    files = len(list((ROOT / "ledger/Assets/Scripts/Game").rglob("*.cs"))) \
        + len(list((ROOT / "ledger/Assets/Scripts/Core").rglob("*.cs")))

    ok = True
    if unexpected:
        ok = False
        print(f"gamecheck: {len(unexpected)} REAL compile error(s) in the Game layer:\n")
        for line in unexpected[:25]:
            print("  " + line)
        if len(unexpected) > 25:
            print(f"  (+{len(unexpected) - 25} more)")
        print()

    # A KNOWN ERROR THAT STOPPED HAPPENING IS ALSO A FAILURE. It means the API
    # gap closed — a newer reference assembly, or the call site changed — and
    # the entry is now a hole that will swallow the next error to land on that
    # exact text.
    expired = set(KNOWN) - seen
    if expired:
        ok = False
        print("gamecheck: allow-listed error(s) NO LONGER OCCUR — delete them:\n")
        for e in sorted(expired):
            print(f"  {e}\n    was: {KNOWN[e]}")
        print()

    if ok:
        print(f"gamecheck: Game layer compiles — {files} files, "
              f"{len(KNOWN)} known reference-assembly gap(s)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
