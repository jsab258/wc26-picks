#!/usr/bin/env python3
"""Every measurement the verdict is supposed to carry is still in it.

    python3 tools/verdict-keys.py            # check the committed verdict
    python3 tools/verdict-keys.py --learn    # add any NEW keys to the manifest

WHY THIS EXISTS.

`game-design/sim-shots/verdict.txt` is the only channel out of CI this
environment can read, and it is assembled by a grep in the workflow over a log
the sim prints. Every link in that chain can break QUIETLY:

  - a `Debug.Log` line gets reworded and the grep stops matching it
  - a metric is dropped from the done-line during a refactor
  - a gate stops being evaluated and its clause vanishes with it
  - the grep pattern is edited and loses an alternation

In every one of those cases the verdict still arrives, still says `pass=True`,
and is simply missing the number that would have said otherwise. Nothing about
it looks wrong. That is the exact shape of the faults this project keeps
finding — a success recorded because the thing that would have failed was never
asked.

So the keys are COMMITTED and compared. A key that disappears fails the build;
a key that is added is offered to the manifest with `--learn` rather than
silently accepted, so growth is a decision and loss is an error.

THIS DOES NOT CHECK THE VALUES. `pass=True` is the sim's job and the gates'
job. This checks only that the questions are still being ASKED — which is the
half nobody was checking, and the half that cannot be noticed by reading a
verdict that looks complete.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
VERDICT = ROOT / "game-design" / "sim-shots" / "verdict.txt"
MANIFEST = ROOT / "game-design" / "sim-shots" / "verdict-keys.json"

# Keys whose absence is expected in some runs and is not a fault. FAILING GATES
# only appears when something failed, and the per-shot drift lines only appear
# once a previous ledger exists.
OPTIONAL = {"FAILING GATES"}


def keys_in(text):
    """Every `name=` in the verdict, plus the distinctive line prefixes.

    The `name=` form covers the done-line and the gate labels, which is where
    the measurements live. The prefixes cover the lines that carry no `=` of
    their own and would otherwise vanish without trace.
    """
    found = set(re.findall(r"([A-Za-z][A-Za-z0-9_]*)=", text))
    for prefix in ("SimDirector: done.", "SimDirector: sky ", "SimDirector: glyphs ",
                   "SimDirector: windowGlow", "SceneAudit:", "Traffic: wheels ",
                   "CharacterAudit:", "CharacterPrefab:", "FrameDrift:",
                   "brandished a cosh"):
        if prefix in text:
            found.add(prefix)
    return found


def main():
    learn = "--learn" in sys.argv
    if not VERDICT.exists():
        print("verdict-keys: no verdict.txt yet — nothing to check")
        return 0

    text = VERDICT.read_text(encoding="utf-8", errors="replace")
    present = keys_in(text)

    if not MANIFEST.exists():
        MANIFEST.write_text(json.dumps(sorted(present), indent=1) + "\n", encoding="utf-8")
        print(f"verdict-keys: manifest seeded with {len(present)} key(s)")
        return 0

    required = set(json.loads(MANIFEST.read_text(encoding="utf-8")))
    missing = sorted(k for k in required - present if k not in OPTIONAL)
    added = sorted(present - required)

    if learn:
        # RECONCILE, DO NOT ONLY ADD. The first version unioned the manifest
        # with what it saw, so a key that was RENAMED stayed required for ever
        # and the check went permanently red for a rename it could never
        # forgive. Caught on its first real encounter: the window probe's `rgb=`
        # became `all=`/`face=`, which is exactly a rename.
        #
        # `--learn` means "this verdict is the new baseline", so the manifest
        # becomes what is actually present. The protection is that it is
        # explicit and manual — nothing learns on its own, and an accidental
        # loss still fails until somebody decides otherwise.
        MANIFEST.write_text(json.dumps(sorted(present), indent=1) + "\n",
                            encoding="utf-8")
        note = []
        if added:
            note.append(f"+{len(added)} new ({', '.join(added[:5])})")
        if missing:
            note.append(f"-{len(missing)} dropped ({', '.join(missing[:5])})")
        print("verdict-keys: rebaselined — " + ("; ".join(note) if note else "no change"))
        return 0

    print(f"verdict-keys: {len(present)} present, {len(required)} required, "
          f"{len(missing)} missing, {len(added)} new")
    for k in added:
        # NEW IS NOT AN ERROR, it is an unrecorded decision. Printed so somebody
        # runs --learn on purpose rather than the manifest drifting behind.
        print(f"  new  {k}  (run --learn to record it)")
    for k in missing:
        print(f"  GONE {k}")
    if missing:
        print(f"{len(missing)} measurement(s) STOPPED BEING REPORTED — a verdict "
              "missing a number reads exactly like one where the number was fine.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
