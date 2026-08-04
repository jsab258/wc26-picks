#!/usr/bin/env python3
"""A Game-layer member must not be named after a Core type the file uses.

    python3 tools/lint-shadow.py

WHY THIS EXISTS.

On 4 August the Windows build failed three times over about ninety minutes on
one line:

    EvidenceHost.cs(229,21): error CS0119: 'EvidenceHost.Watched(Vector3,
    IEnumerable<NpcWalker>)' is a method, which is not valid in the given context

`Ledger.Core.Watched` is a type. `EvidenceHost` calls `Watched.WouldTalkToPolice`
eighty lines below. Adding a public static method called `Watched` to that class
shadowed the type inside it, and the error landed on a line nobody had touched.

The cost is the point. **Only `Core` compiles in this container** — the Game
layer's first compiler is a Windows CI runner twenty-five minutes away — so a
name collision that any IDE would underline in red instead consumed three round
trips, two of which were spent misdiagnosing it as a Unity licence failure
because the verdict for a failed build said nothing about why.

The verdict carries compile errors now, which turns the next one into a
two-minute fix. This is the other half: catching it here costs nothing at all.

WHAT IT CHECKS, AND WHAT IT DELIBERATELY DOES NOT.

C# name resolution is genuinely complicated and this is a lint, not a compiler.
It flags exactly one pattern, the one that has actually cost time:

    a Game file declares a member (method, property or field) whose bare name
    equals a Core TYPE name, and that same file uses that name as a qualifier
    — `Watched.Something` — somewhere in its text.

Both halves are required. A Game member named `Traces` in a file that never
writes `Traces.` is legal and harmless; a file that only uses `Traces.Acquire`
and declares nothing of that name is the normal case and by far the commonest.
Requiring the collision AND the use keeps this from becoming a rename tax on
every sensible identifier in the project.

It reads text rather than parsing C#. ShapeCheck already owns real syntax, and a
regex that is honest about being a regex beats a half-parser that is not.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORE = ROOT / "ledger" / "Assets" / "Scripts" / "Core"
GAME = ROOT / "ledger" / "Assets" / "Scripts" / "Game"

# `public sealed class Foo`, `static class Foo`, `enum Foo`, `struct Foo`.
TYPE_DECL = re.compile(
    r"^\s*(?:public|internal)?\s*(?:static\s+|sealed\s+|abstract\s+|partial\s+)*"
    r"(?:class|struct|enum|interface)\s+([A-Z][A-Za-z0-9_]*)",
    re.M,
)

# METHODS ONLY, AND THE NARROWING IS THE WHOLE CORRECTNESS OF THIS TOOL.
#
# The first version flagged any member and reported six on a tree that has
# compiled hundreds of times: `public Wallet Wallet { get; }`, `public Campaign
# Campaign { get; }`, `public readonly FramedBeat Beat`. All legal. A field or
# property shadowing a type still resolves — the simple name binds to the
# member, and `Wallet.Balance` reaches the same member it would have anyway
# (C#'s "Color Color" rule), while `Beat.Abort()` reaches `FramedBeat.Abort`.
#
# A METHOD cannot. `Watched` as a method makes the simple name a method GROUP,
# and a method group cannot be dotted at all — so `Watched.WouldTalkToPolice` is
# CS0119 with no exception and no ambiguity. That is the only case this can
# prove without a compiler, so it is the only case it flags.
#
# Rule 5b, and it nearly went out wrong: the reject case passed on the first
# run and I was one commit from shipping a guard that blocked six good files.
# "Refuse unless perfect" is the ratchet, and a lint that fails a tree which
# demonstrably builds is exactly that.
MEMBER_DECL = re.compile(
    r"^\s*(?:public|internal|protected)\s+(?:static\s+|virtual\s+|override\s+|"
    r"abstract\s+|new\s+|async\s+|sealed\s+)*"
    r"[A-Za-z_][A-Za-z0-9_<>,\[\]\.\?]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
    re.M,
)


def strip_comments(text):
    """Comments mention type names constantly and none of it is code.

    Without this, every paragraph in this project explaining why `Watched` is
    called `Watched` would read as a use of it. Strings go too: a verdict line
    with `Traces.` in it is prose that happens to be quoted.
    """
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"^\s*///.*$", " ", text, flags=re.M)
    text = re.sub(r"//.*$", " ", text, flags=re.M)
    # PLAIN strings only. `$"..."` IS CODE and throwing it away made this check
    # blind to the place the mistake actually happens.
    #
    # The docstring above says "a verdict line with `Traces.` in it is prose
    # that happens to be quoted". True of a plain string; FALSE of an
    # interpolated one, and `SimDirector`'s done-line is a single interpolated
    # string hundreds of expressions long — the largest concentration of
    # Game-layer static reads in the project. Every CS0119 in it was invisible
    # here.
    #
    # Found on 4 August while writing `lint-filetype`, which scored zero on the
    # very line that prompted it for exactly this reason, and then found the
    # same fault sitting in this file. One idea, two implementations.
    text = re.sub(r'\$"(?:\\.|[^"\\])*"',
                  lambda m: " ".join(re.findall(r"\{([^{}]*)\}", m.group(0))),
                  text, flags=re.S)
    text = re.sub(r'(?<!\$)"(?:\\.|[^"\\])*"', '""', text)
    return text


def core_types():
    found = set()
    if not CORE.is_dir():
        return found
    for path in sorted(CORE.rglob("*.cs")):
        for name in TYPE_DECL.findall(strip_comments(path.read_text(encoding="utf-8", errors="replace"))):
            found.add(name)
    return found


def main():
    types = core_types()
    if not types:
        print("lint-shadow: no Core types found — check the paths")
        return 2
    if not GAME.is_dir():
        print("lint-shadow: no Game directory")
        return 0

    bad = []
    for path in sorted(GAME.rglob("*.cs")):
        code = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
        members = set(MEMBER_DECL.findall(code))
        clash = members & types
        if not clash:
            continue
        for name in sorted(clash):
            # ...and the file has to actually USE it as a qualifier, or the
            # shadowing is invisible and harmless.
            if re.search(r"(?<![A-Za-z0-9_.])" + re.escape(name) + r"\s*\.", code):
                bad.append((path.relative_to(ROOT), name))

    if bad:
        print(f"lint-shadow: {len(bad)} Game member(s) shadow a Core type the same file uses:")
        for path, name in bad:
            print(f"  {path}: declares `{name}`, and uses `{name}.` — CS0119 waiting to happen")
        print("  Rename the Game member. Only Core compiles here; this is a")
        print("  twenty-five minute round trip if it reaches CI.")
        return 1

    print(f"lint-shadow: 0 shadowed Core types ({len(types)} type(s), "
          f"{len(list(GAME.rglob('*.cs')))} Game file(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
