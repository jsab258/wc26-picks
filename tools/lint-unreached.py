#!/usr/bin/env python3
"""PUBLIC GAME-LAYER METHODS THAT NOTHING CALLS.

    python3 tools/lint-unreached.py

WHY THIS EXISTS, AND IT IS THE LARGEST THING FOUND ON 4 AUGUST.

`GameController.RecordKilling` is the only path into `HomicideBook`. It has no
callers. So the register is empty in every run, `Pressure` returns zero,
`Stage` returns `Inquiry.None`, and `inquiry=None` in all 131 kept verdicts —
which means the paper naming you, the redirect having anything to relieve,
`Police.ForcesActThree` and `Police.BarsQuietExit` have between them never
executed once in the recorded history of this project.

One missing call, a whole stage of the game, and NOTHING WAS ASKING.
`ReachCheck` answers exactly this question — "does anything actually call it" —
for public CORE APIs, and the reach ledger has thirty-five entries because of
it. `RecordKilling` is Game-layer, so it was never in scope. The ledger is the
Core half of a question nobody asks about the other half, and the biggest hole
turned out to be on the side with no instrument.

WHY IT IS A GREP AND NOT A GRAPH WALK. `ReachCheck` can walk a graph because
the Game layer NAMES the Core members it uses and the roots are obvious. The
Game layer's own roots are not: Unity calls `Awake`, `Update`, `OnDisable` and
a dozen others with no reference anywhere, `SendMessage` and the inspector can
reach anything, and a graph walk that did not know all of them would report
half the codebase as dead. So this asks the narrow question it can answer
honestly — is this NAME mentioned anywhere else in the Game layer — and says
out loud that a name-matcher cannot see reflection.

THE LIVE CODEBASE IS THE ACCEPTING CASE, which is the discipline the five
`lint-*` tools already follow: every hit on today's code is either a real
finding or a false positive worth suppressing by name, and there is no fixture
to be fooled by. Run it, read every hit, and add the Unity lifecycle and the
genuinely-by-design ones to the skip list with a reason.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME = ROOT / "ledger" / "Assets" / "Scripts" / "Game"
EDITOR = ROOT / "ledger" / "Assets" / "Editor"

# UNITY CALLS THESE AND NO SOURCE FILE MENTIONS THEM. Not a suppression list
# for awkward findings — a list of names the engine invokes by convention, which
# is precisely the reflection this tool says it cannot see.
UNITY = {
    "Awake", "Start", "OnEnable", "OnDisable", "OnDestroy", "Update",
    "LateUpdate", "FixedUpdate", "OnGUI", "OnApplicationQuit",
    "OnApplicationFocus", "OnApplicationPause", "OnDrawGizmos",
    "OnTriggerEnter", "OnTriggerExit", "OnCollisionEnter", "OnCollisionExit",
    "OnRenderImage", "OnPreRender", "OnPostRender", "OnValidate", "Reset",
    "OnBecameVisible", "OnBecameInvisible", "OnAnimatorMove", "OnAnimatorIK",
    "OnControllerColliderHit", "OnMouseDown", "OnGizmosSelected",
}

# CALLED BY NAME FROM OUTSIDE THE CODEBASE ENTIRELY. The Windows workflow runs
# `-executeMethod Ledger.Editor.CiBuild.BuildWindows`, which is reflection from
# a YAML file — the exact blind spot this tool declares in its own docstring.
# Named here rather than dropped silently, and PRINTED, because a cap nobody is
# told about is indistinguishable from a finding.
BY_WORKFLOW = {"BuildWindows": "-executeMethod in ledger-build-windows.yml",
               "BuildMac": "-executeMethod in ledger-build-mac.yml"}

DECL = re.compile(
    r"^\s*public\s+(?:static\s+|virtual\s+|override\s+|async\s+|partial\s+|new\s+|"
    r"sealed\s+|unsafe\s+)*[\w<>,\[\]\?\.]+\s+(\w+)\s*\(", re.M)


def sources():
    for d in (GAME, EDITOR):
        if d.exists():
            yield from sorted(d.rglob("*.cs"))


def main():
    files = list(sources())
    text = {p: p.read_text(encoding="utf-8", errors="replace") for p in files}
    joined = "\n".join(text.values())

    declared = {}
    for p, s in text.items():
        for m in DECL.finditer(s):
            name = m.group(1)
            if name in UNITY:
                continue
            line = s.count("\n", 0, m.start()) + 1
            declared.setdefault(name, (p, line))

    unreached = []
    for name, (p, line) in sorted(declared.items()):
        # EVERY MENTION ANYWHERE, minus the declarations themselves. A method
        # called through a local alias, a delegate or an interface still spells
        # its own name somewhere, and one that never appears twice is the
        # shape worth reading.
        hits = len(re.findall(r"(?<![\w])" + re.escape(name) + r"(?![\w])", joined))
        decls = len(re.findall(
            r"^\s*public\s+(?:static\s+|virtual\s+|override\s+|async\s+|partial\s+|new\s+|"
            r"sealed\s+|unsafe\s+)*[\w<>,\[\]\?\.]+\s+" + re.escape(name) + r"\s*\(",
            joined, re.M))
        if hits <= decls:
            unreached.append((name, p.relative_to(ROOT), line))

    excluded = [(n, r, l) for n, r, l in unreached if n in BY_WORKFLOW]
    unreached = [(n, r, l) for n, r, l in unreached if n not in BY_WORKFLOW]
    print(f"lint-unreached: {len(files)} Game-layer files, "
          f"{len(declared)} public methods, {len(unreached)} that nothing else names.")
    for n, r, l in excluded:
        print(f"  (not counted: {n} at {r}:{l} — {BY_WORKFLOW[n]})")
    print("A name-matcher cannot see reflection, SendMessage or an inspector "
          "binding — read each one before believing it.\n")
    for name, rel, line in unreached:
        print(f"  {rel}:{line}: {name}")
    # EXIT 0 WHATEVER IT FINDS. This is a reading, not a gate: the commit that
    # WIRES one of these would be blocked by a check that failed on the list.
    return 0


if __name__ == "__main__":
    sys.exit(main())
