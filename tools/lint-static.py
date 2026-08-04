#!/usr/bin/env python3
"""A static method in a partial class reaching an instance member of it: CS0120.

    python3 tools/lint-static.py
    python3 tools/lint-static.py --self-test

WHY THIS EXISTS.

    Assets\\Scripts\\Game\\PopulationHost.cs(129,17): error CS0120:
    An object reference is required for the non-static field, method, or
    property 'GameController.Populace'

`GameController` is spread across a dozen partial files. A method written in
one of them cannot see, from that file alone, whether the members it touches
are static — and `static` is the reflex modifier for anything that looks like a
pure mapping. `ApplyDetailToCrowd` looked exactly like one: a settings value in,
a cap out. The one thing it touches is the instance's own population.

THE THIRD REFERENCE-RESOLUTION ERROR IN ONE MORNING, after CS0119 (a Game
method shadowing a Core type) and CS0426 (a Core type qualified by another).
All three are invisible to ShapeCheck for the same structural reason: it runs
reference-independent diagnostics, which is exactly what lets it run at all on
a side with no Unity assemblies. All three cost a twenty-eight-minute round
trip, and each one blocked every build dispatched after it.

WHAT IT DOES. Collects the instance members declared across every partial of a
class, then flags a `static` method in the same class that names one of them.

WHAT IT CANNOT DO, said plainly because a checker that overclaims is worse than
none: it matches NAMES, not symbols. A local variable, a parameter, or an
unrelated type's member with the same name reads identically. So it only
considers members whose names are distinctive enough to be worth the risk —
and the live codebase is the proof, because today's code compiles and therefore
every hit on it is a false positive by definition. That is the accepting case
the two earlier lints of this family each failed before passing.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME = ROOT / "ledger" / "Assets" / "Scripts" / "Game"

PARTIAL = re.compile(r"\bpublic\s+partial\s+class\s+(\w+)")
LINE_COMMENT = re.compile(r"//.*")
# An instance member: public/internal, NOT static, a type, then a name.
INSTANCE = re.compile(
    r"^\s*public\s+(?!static\b)(?!partial\b)(?!class\b)(?!enum\b)(?!struct\b)"
    r"(?:readonly\s+)?[\w<>,\[\]\?\.]+\s+(\w+)\s*(?:\{|=|;)")
STATIC_METHOD = re.compile(
    r"^\s*(?:public|internal|private|protected)?\s*static\s+"
    r"[\w<>,\[\]\?\.]+\s+(\w+)\s*\(")


def strip_comments(text):
    return "\n".join(LINE_COMMENT.sub("", l) for l in text.split("\n"))


def collect(files):
    """(class -> instance member names, class -> files declaring it).

    A file declaring TWO partial classes is skipped rather than guessed at:
    members would be attributed to whichever was declared first, and a wrong
    member list is how a name-matching checker starts flagging correct code.
    No Game file does this today; this is here so that the day one does, the
    tool says so instead of going quietly wrong.
    """
    members, owners = {}, {}
    for f in files:
        text = strip_comments(f.read_text(encoding="utf-8"))
        names = set(PARTIAL.findall(text))
        if len(names) != 1:
            if names:
                print(f"lint-static: {f.name} declares {len(names)} partial classes "
                      f"— skipped, member attribution would be a guess")
            continue
        cls = names.pop()
        owners.setdefault(cls, []).append(f)
        for line in text.split("\n"):
            hit = INSTANCE.match(line)
            if hit:
                members.setdefault(cls, set()).add(hit.group(1))
    return members, owners


def named_in(text, names):
    """Which of `names` this text uses UNQUALIFIED.

    `Foo.Bar` is somebody else's Bar; a bare `Bar` is ours.
    """
    return [n for n in names
            if re.search(r"(?<![\w.])" + re.escape(n) + r"\b", text)]


def body_of(line):
    """The part of a method's opening line that is already its body.

    A ONE-LINE BODY IS STILL A BODY, and the first version of this file could
    not see one: it noted the method, added the line's braces — which for
    `static void Wrong() { Populace.X = 3; }` net to zero — and `continue`d
    past the only line that mattered. The self-test's rejecting case said
    `nothing` where it should have said `Populace`.

    Both single-line shapes start after a token: a block body after `{`, an
    expression body after `=>`. Parameters are deliberately NOT scanned — a
    parameter named after an instance member shadows it, which compiles.
    """
    if "{" in line:
        return line[line.index("{") + 1:]
    if "=>" in line:
        return line[line.index("=>") + 2:]
    return ""


def static_bodies(f):
    """How many static method bodies this file has, for the coverage line.

    A checker that scans NOTHING also reports zero. `lint-nested` prints the
    count of types it considered for the same reason: without it the clean
    result and the broken result are the same sentence.
    """
    n = 0
    for line in strip_comments(f.read_text(encoding="utf-8")).split("\n"):
        if STATIC_METHOD.match(line) and not (
                "{" not in line and "=>" not in line and line.rstrip().endswith(";")):
            n += 1
    return n


def scan_file(f, cls, names):
    """Every unqualified use of `names` inside a static method body.

    THE BRACE IS NOT ON THE SIGNATURE LINE. This codebase is Allman, so
    `public static void ApplyDetailToCrowd()` carries no `{` at all — the
    first version compared depth against itself on that line, found them
    equal, and closed the body before it had opened. It reported zero
    against the exact file that produced the CS0120.

    So the state is two things, not one: the depth OUTSIDE the method, and
    whether the body has actually opened yet. Only once it has can a
    depth comparison mean anything.
    """
    lines = strip_comments(f.read_text(encoding="utf-8")).split("\n")
    hits = []
    brace = 0
    outside = None      # brace depth outside the static method; None when not in one
    opened = False      # has the method's `{` been seen
    expr = False        # an `=>` body, which ends at its first `;` and has no braces
    for n, line in enumerate(lines, 1):
        moved = line.count("{") - line.count("}")
        if outside is None:
            if not STATIC_METHOD.match(line):
                brace += moved
                continue
            # `static extern void Foo();` and friends have no body at all.
            # Entering one would scan the whole rest of the file as if inside it.
            if "{" not in line and "=>" not in line and line.rstrip().endswith(";"):
                brace += moved
                continue
            outside = brace
            opened = "{" in line
            expr = "=>" in line and not opened
            text = body_of(line)
        else:
            text = line
            if not opened and "{" in line:
                opened = True
        for name in named_in(text, names):
            hits.append((f.name, n, cls, name))
        brace += moved
        if expr:
            if ";" in text:
                outside, expr = None, False
        elif opened and brace <= outside:
            outside = None
    return hits


def scan(files):
    members, owners = collect(files)
    bad = []
    for cls, fs in owners.items():
        names = members.get(cls, set())
        if not names:
            continue
        for f in fs:
            bad.extend(scan_file(f, cls, names))
    return bad


def self_test():
    """BOTH OUTCOMES, accepting first (rule 5b).

    THE FIXTURES ARE ALLMAN BECAUSE THE CODEBASE IS. The first version of this
    self-test wrote every method on one line, passed all three cases, and
    reported zero against the file that had produced the CS0120 an hour
    earlier — the brace-on-the-next-line shape was the entire bug and no case
    contained it. So the rejecting case below is `ApplyDetailToCrowd` as it
    was actually written, and the one-line form is a SEPARATE case rather
    than the only one.
    """
    good = [_Fake("A.cs", """
namespace Ledger.Game
{
    public partial class GameController
    {
        public Population Populace { get; private set; }

        public void Uses()
        {
            Populace.NearCap = 3;
        }
    }
}
"""), _Fake("B.cs", """
namespace Ledger.Game
{
    public partial class GameController
    {
        public static int Pure(int a)
        {
            return a + 1;
        }

        public static int Terse(int a) => a + 1;
    }
}
""")]
    ok1 = not scan(good)
    print(f"  {'ok  ' if ok1 else 'FAIL'} an instance method using an instance member, and two "
          f"static methods using neither, all pass")

    # The real one, verbatim in shape: Allman, and the member reached in the
    # guard clause on the first line of the body.
    bad = good[:1] + [_Fake("C.cs", """
namespace Ledger.Game
{
    public partial class GameController
    {
        public static void ApplyDetailToCrowd()
        {
            if (Populace == null) return;
            Populace.NearCap = 3;
        }
    }
}
""")]
    hits = scan(bad)
    ok2 = len(hits) == 2 and all(h[3] == "Populace" for h in hits)
    print(f"  {'ok  ' if ok2 else 'FAIL'} the real CS0120 — a static Allman method reaching an "
          f"instance member — is caught ({len(hits)} of 2 uses)")

    one_liner = good[:1] + [_Fake("E.cs", """
namespace Ledger.Game
{
    public partial class GameController
    {
        public static void Wrong() { Populace.NearCap = 3; }
        public static void AlsoWrong() => Populace.NearCap = 4;
    }
}
""")]
    hits3 = scan(one_liner)
    ok3 = len(hits3) == 2
    print(f"  {'ok  ' if ok3 else 'FAIL'} and so are the one-line and expression-bodied forms "
          f"({len(hits3)} of 2)")

    # `other.Populace` is somebody else's, and must not be flagged.
    qual = good[:1] + [_Fake("D.cs", """
namespace Ledger.Game
{
    public partial class GameController
    {
        public static void Fine(GameController g)
        {
            g.Populace.NearCap = 3;
        }
    }
}
""")]
    ok4 = not scan(qual)
    print(f"  {'ok  ' if ok4 else 'FAIL'} and one reached THROUGH a reference is not")
    return 0 if (ok1 and ok2 and ok3 and ok4) else 1


class _Fake:
    def __init__(self, name, text):
        self.name = name
        self._t = text

    def read_text(self, encoding=None):
        return self._t


def main():
    if "--self-test" in sys.argv:
        return self_test()
    if not GAME.is_dir():
        print("lint-static: Game not found")
        return 0
    files = sorted(GAME.rglob("*.cs"))
    bad = scan(files)
    if bad:
        print(f"lint-static: {len(bad)} static method(s) reaching an instance member "
              f"— this is CS0120 and the Windows build is where you will find out:")
        for name, line, cls, member in bad:
            print(f"  {name}:{line}  '{member}' is an instance member of {cls}")
        return 1
    members, owners = collect(files)
    print(f"lint-static: 0 static/instance errors "
          f"({sum(len(v) for v in members.values())} instance members across "
          f"{len(owners)} partial class(es), {sum(static_bodies(f) for f in files)} "
          f"static bodies walked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
