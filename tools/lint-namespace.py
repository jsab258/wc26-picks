#!/usr/bin/env python3
"""A NAMESPACE CANNOT BE COMPARED TO NULL, and twice today one was.

WHY THIS EXISTS. `ViolenceHost` is a static class with no game in scope, and it
contained `if (Game != null && Game.Campaign != null)`. Inside
`namespace Ledger.Game` the bare identifier `Game` resolves to that NAMESPACE,
so the compiler read the sentence as a namespace being used as a value and the
build came back `CS0118: 'Ledger.Game' is a namespace but is used like a
variable`, twice, on two commits, each `NO PLAYER LOG`.

WHY NOTHING LOCAL CAUGHT IT. CS0118 is a name-RESOLUTION error and ShapeCheck
runs reference-independent diagnostics only — the fifth member of the family
that already cost a round trip each for CS0119 (`lint-shadow`), CS0426
(`lint-nested`), CS0120 (`lint-static`) and CS0103 (`lint-filetype`).

WHY IT LOOKS NORMAL, WHICH IS THE POINT. `PlayerController` really does have
`public GameController Game;` and uses `Game.Harm` and `Game.Now` correctly on
three lines. The shape is idiomatic in this codebase. What makes it an error in
one file and not another is whether the ENCLOSING TYPE has a member of that
name, and that is a per-file fact a reader will not check.

THE TELL, AND WHY IT NEEDS NO TYPE RESOLUTION. A namespace can never be
compared to null, tested with `?.`, or assigned. `Game.Campaign` on its own is
ambiguous without the compiler — it could be a namespace qualifier, and
`Ledger.Core.Violence` is exactly that. `Game != null` is not ambiguous in any
context. So the check reads only the unambiguous positions and ignores the
qualifier form entirely, which is the difference between a lint people trust
and one they learn to skip.

RULE 5b: THE LIVE CODEBASE IS THE ACCEPTING CASE, and here it is a strong one
because it contains the legitimate use. `PlayerController` must pass. Run it
over everything, expect zero, and only then trust a red.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN = [ROOT / "ledger" / "Assets" / "Scripts", ROOT / "ledger" / "Assets" / "Editor"]

NAMESPACE = re.compile(r"^\s*namespace\s+([A-Za-z_][\w.]*)", re.M)

COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
PLAIN = re.compile(r'(?<!\$)"(?:[^"\\]|\\.)*"')
INTERP = re.compile(r'\$"(?:[^"\\]|\\.)*"', re.S)
BRACED = re.compile(r"\{([^{}]*)\}")


def code_only(text):
    """Comments and plain strings blanked; interpolated-string EXPRESSIONS kept,
    because they compile — the blind spot that made `lint-filetype` v1 score
    zero on the very line that prompted it."""
    text = COMMENT.sub(" ", text)
    text = INTERP.sub(lambda m: " ".join(BRACED.findall(m.group(0))), text)
    return PLAIN.sub(" ", text)


def sources():
    for root in SCAN:
        if root.exists():
            yield from sorted(root.rglob("*.cs"))


def main():
    files = list(sources())

    # EVERY SEGMENT OF EVERY NAMESPACE, because `Ledger.Game` puts BOTH
    # `Ledger` and `Game` into scope as bare names, and the one that bit was
    # the inner segment.
    segments = set()
    for f in files:
        for ns in NAMESPACE.findall(f.read_text(encoding="utf-8", errors="replace")):
            segments.update(ns.split("."))
    if not segments:
        print("lint-namespace: NO NAMESPACES FOUND — the check did not run")
        return 1

    checks = []
    for seg in sorted(segments):
        # THE UNAMBIGUOUS POSITIONS ONLY. `Seg.Member` is deliberately absent:
        # that is what a namespace qualifier looks like, and flagging it would
        # condemn every `Ledger.Core.Violence` in the project.
        checks.append((seg, re.compile(
            r"(?<![\w.])" + re.escape(seg) + r"\s*(?:[!=]=|\?\.|\?\[|\+\+|--)")))

    bad = []
    for f in files:
        text = code_only(f.read_text(encoding="utf-8", errors="replace"))
        for seg, use in checks:
            # DECLARED ANYWHERE IN THE FILE IS ENOUGH TO SKIP IT, and that is
            # the deliberate direction of the trade. A member, parameter or
            # local of this name makes the bare identifier legal, and working
            # out WHICH scope it is in needs the compiler this file exists to
            # do without. Conservative costs a missed error; the other way
            # costs trust, and a lint nobody trusts is not run.
            declared = re.search(
                r"(?:\b[A-Za-z_][\w<>\[\],?.]*|\bvar)\s+" + re.escape(seg)
                + r"\s*(?:[;=,){]|=>)", text)
            if declared:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if use.search(line):
                    bad.append((f.relative_to(ROOT), i, seg))

    for path, line, seg in bad:
        print(f"{path}:{line}: `{seg}` here is a NAMESPACE, not a value — "
              f"the enclosing type declares no member of that name (CS0118)")

    print(f"lint-namespace: {len(bad)} namespace-as-value error(s) "
          f"({len(files)} file(s) scanned, {len(segments)} namespace segment(s) "
          f"in scope: {', '.join(sorted(segments))})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
