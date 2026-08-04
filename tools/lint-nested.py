#!/usr/bin/env python3
"""A Core type qualified by another Core type, which is CS0426.

    python3 tools/lint-nested.py
    python3 tools/lint-nested.py --self-test

WHY THIS EXISTS.

    Assets\\Scripts\\Game\\Audio.cs(52,43): error CS0426:
    The type name 'Bus' does not exist in the type 'Mixing'

`Bus` is declared BESIDE `Mixing` in `Ledger.Core`, not inside it. I wrote
`Mixing.Bus` five times because the enum is documented in `Mixing.cs`, sits
twenty lines above the class, and is only ever used with it — every reason to
believe it is nested except the one that counts.

WHY NOTHING ELSE CATCHES IT. `ShapeCheck` runs Roslyn with reference-independent
diagnostics only, which is what makes it able to run at all on a side where the
Unity assemblies do not exist. CS0426 is type RESOLUTION and needs those
references, so it is structurally invisible here — this is the class of fault
CLAUDE.md names as the one the Windows build is the first compiler for.

That makes it a twenty-eight-minute round trip, and the cost is not the error.
Three commits went out on top of this one before the verdict came back, so
every build dispatched in that window carried a Game layer that could not
compile and three separate answers moved a round trip further away.

The same shape as `lint-shadow.py`, which exists because CS0119 cost a round
trip in the same way. Both are cheap, mechanical, reference-free checks for
mistakes Roslyn can only report with references it does not have here.

WHAT IT IS NOT. It cannot resolve types either — it matches NAMES. So it only
looks at pairs where BOTH sides are top-level Core types, which is the exact
shape of the mistake and is not a shape legal C# produces: a real nested type
is not also declared at top level.

NESTED TYPES ARE EXCLUDED BY BRACE DEPTH, and that matters — `Perception` has a
nested `Attention` struct, so `Perception.Attention` is correct and must not be
flagged. Only depth-1 declarations (directly inside the namespace) count.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORE = ROOT / "ledger" / "Assets" / "Scripts" / "Core"
GAME = ROOT / "ledger" / "Assets" / "Scripts" / "Game"

DECL = re.compile(
    r"^\s*(?:public|internal)?\s*(?:static\s+|sealed\s+|abstract\s+|partial\s+)*"
    r"(?:class|struct|enum|interface)\s+([A-Z]\w*)")
LINE_COMMENT = re.compile(r"//.*")
# TYPE POSITION ONLY, and the first version's 13 false positives are why.
#
# Matching every `X.Y` where both names are Core types flagged `Campaign.Verdict`,
# `Pressures.Rumor`, `Effects.Rumor` and `KeyKind.Payment` — all of which COMPILE
# TODAY, so all of which are members that happen to share a name with a type.
# A name-only check cannot tell those apart, and the whole live codebase
# compiling makes every hit a false positive by definition. That is the shape
# rule 5b warns about: a checker whose false positives read exactly like the
# thing it was written to find.
#
# The mistake itself only ever occurs where a TYPE is expected, because that is
# the only place a type name can appear. Three such places, and the false
# positives are in none of them:
#
#   <Mixing.Bus, int>     a generic argument
#   Mixing.Bus bus        a parameter or variable declaration
#   Mixing.Bus.Foley      a member reached THROUGH the mis-qualified type
#
# whereas `= Campaign.Verdict` and `== Pressures.Rumor` are values.
QUALIFIED = re.compile(
    # A GENERIC ARGUMENT, WHICH IS NOT THE SAME AS A CALL ARGUMENT. The first
    # narrowing accepted `(` as an opener and flagged `new AccessKey(
    # KeyKind.Payment, 60)` — an enum member in an ordinary method call. So the
    # bracket has to actually be an angle one at one end or the other:
    # `<X.Y, int>` opens with `<`, `<int, X.Y>` closes with `>`.
    r"<\s*([A-Z]\w*)\.([A-Z]\w*)\s*[,>]"
    r"|,\s*([A-Z]\w*)\.([A-Z]\w*)\s*>"
    r"|\b([A-Z]\w*)\.([A-Z]\w*)\s+[a-z_]\w*\s*[,)=;]"  # declaration
    r"|\b([A-Z]\w*)\.([A-Z]\w*)\.[A-Z]")                # member through it


def pairs(line):
    """Every (outer, inner) the pattern found, whichever alternative matched."""
    out = []
    for m in QUALIFIED.finditer(line):
        g = m.groups()
        for i in range(0, len(g), 2):
            if g[i] and g[i + 1]:
                out.append((g[i], g[i + 1]))
    return out


def top_level_types(text):
    """Type names declared directly inside the namespace, by brace depth.

    Depth 1 is inside `namespace Ledger.Core {`. Anything deeper is nested and
    IS reachable as `Outer.Inner`, so including it would flag correct code —
    `Perception.Attention` being the live example.
    """
    names, depth = set(), 0
    for raw in text.split("\n"):
        line = LINE_COMMENT.sub("", raw)
        m = DECL.match(line)
        if m and depth == 1:
            names.add(m.group(1))
        depth += line.count("{") - line.count("}")
    return names


def scan(core_files, game_files):
    top = set()
    for f in core_files:
        top |= top_level_types(f.read_text(encoding="utf-8"))

    bad = []
    for f in game_files:
        for n, raw in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
            line = LINE_COMMENT.sub("", raw)
            for outer, inner in pairs(line):
                if outer in top and inner in top and outer != inner:
                    bad.append((f.name, n, f"{outer}.{inner}", inner))
    return top, bad


def self_test():
    """BOTH OUTCOMES, and the accepting one first (rule 5b).

    The expensive failure for a name-matching check is flagging correct code:
    it would be switched off within a day, and take the real catch with it.
    """
    core = [_Fake("Mixing.cs", """
namespace Ledger.Core
{
    public enum Bus { Voice, Foley }
    public static class Mixing { public static int Budget(Bus b) => 4; }
    public static class Perception
    {
        public struct Attention { public double Seconds; }
    }
}
""")]

    ok_game = [_Fake("Good.cs", "var b = Bus.Foley;\nvar a = new Perception.Attention();\n")]
    top, bad = scan(core, ok_game)
    ok1 = "Bus" in top and "Mixing" in top and "Attention" not in top and not bad
    print(f"  {'ok  ' if ok1 else 'FAIL'} correct code passes, and a genuinely NESTED type "
          f"is not mistaken for a sibling")

    bad_game = [_Fake("Bad.cs", "static Dictionary<Mixing.Bus, int> x;\n")]
    _, bad2 = scan(core, bad_game)
    ok2 = len(bad2) == 1 and bad2[0][2] == "Mixing.Bus"
    print(f"  {'ok  ' if ok2 else 'FAIL'} a sibling qualified by another type is caught "
          f"({bad2[0][2] if bad2 else 'nothing'})")

    # A COMMENT EXPLAINING THE MISTAKE MUST NOT BE THE MISTAKE. The fix for
    # this very bug left `Mixing.Bus` in a comment saying not to write it.
    cmt = [_Fake("Note.cs", "// `Bus`, NOT `Mixing.Bus`. The enum is a sibling.\n")]
    _, bad3 = scan(core, cmt)
    ok3 = not bad3
    print(f"  {'ok  ' if ok3 else 'FAIL'} and a comment warning about it is not flagged as it")
    return 0 if (ok1 and ok2 and ok3) else 1


class _Fake:
    def __init__(self, name, text):
        self.name = name
        self._t = text

    def read_text(self, encoding=None):
        return self._t


def main():
    if "--self-test" in sys.argv:
        return self_test()
    if not CORE.is_dir() or not GAME.is_dir():
        print("lint-nested: Core or Game not found")
        return 0
    top, bad = scan(sorted(CORE.rglob("*.cs")), sorted(GAME.rglob("*.cs")))
    if bad:
        print(f"lint-nested: {len(bad)} Core type(s) qualified by another Core type "
              f"— this is CS0426 and the Windows build is where you will find out:")
        for name, line, what, inner in bad:
            print(f"  {name}:{line}  {what}  — '{inner}' is a SIBLING of that type, "
                  f"write '{inner}' on its own")
        return 1
    print(f"lint-nested: 0 nested-type errors ({len(top)} top-level Core types checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
