#!/usr/bin/env python3
"""A FILENAME IS NOT A TYPE NAME, and in this project it usually is not.

WHY THIS EXISTS. `SimDirector` referenced `TrafficHost.BrakeLampsPeak`. There is
no type called `TrafficHost` anywhere in the codebase: `TrafficHost.cs` declares
`partial class GameController`, like thirteen other files in the Game layer.
The build came back NO PLAYER LOG with `CS0103: The name 'TrafficHost' does not
exist in the current context`, and by then three more commits were sitting on
top of it.

WHY NOTHING LOCAL CAUGHT IT. CS0103 is a name-RESOLUTION error, and ShapeCheck
runs reference-independent diagnostics only — the same blind spot that already
cost a round trip each for CS0119 (`lint-shadow`), CS0426 (`lint-nested`) and
CS0120 (`lint-static`). This is the fourth member of that family and the
cheapest to check, because it needs no type resolution at all: it is a set
difference between the filenames somebody might mistake for types and the type
names that actually exist.

MEASURED BEFORE BEING WRITTEN, so this is a real trap and not a tidy rule.
Fourteen of the Game layer's files declare no type of their own name —
AccessHost, ActOne, ActThreeHost, DirectorHost, IntentBridge, OperationHost,
OsseiSetup, PhoneSetup, PhoneUI, PlanUI, PopulationHost, PurseSetup,
TrafficHost, UiSmokeTest. Every one of them is a `GameController` partial or a
class under another name, and every one of them reads like a type at a call
site.

SCOPE, AND IT IS DELIBERATELY NARROW. Only identifiers that ARE a filename stem
somewhere in the project and are NOT a declared type anywhere. That is the exact
mistake being made. A wider check — "every capitalised identifier must resolve"
— would need the compiler this file exists to work without, and would drown in
Unity's own types.

RULE 5b: THE LIVE CODEBASE IS THE ACCEPTING CASE. Every hit on today's code is
a false positive by definition, because the project compiles in CI. Run it over
everything, expect zero, and only then trust a red.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN = [ROOT / "ledger" / "Assets" / "Scripts", ROOT / "ledger" / "Assets" / "Editor"]

# Any type declaration. `partial` and access modifiers are skipped by the
# pattern rather than enumerated, so a new modifier does not silently disable
# the check.
DECL = re.compile(r"\b(?:class|struct|interface|enum|record)\s+([A-Za-z_]\w*)")

# `Foo.Bar` where Foo starts with a capital — a static access or a type
# qualifier. The negative lookbehind drops `something.Foo.Bar`, which is a
# member chain and not a type reference.
USE = re.compile(r"(?<![\w.])([A-Z]\w*)\s*\.\s*[A-Za-z_]\w*")

# Comments and plain strings carry type names in prose constantly — every
# paragraph in this project does — and none of them compile.
COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
PLAIN = re.compile(r'(?<!\$)"(?:[^"\\]|\\.)*"')

# INTERPOLATED STRINGS ARE CODE, AND THE FIRST VERSION OF THIS THREW THEM AWAY.
#
# The lint scored zero on the very line that prompted it. `TrafficHost` was in
# the trap set, the regex was right, and the reference never reached either —
# because it lives inside `$"...{TrafficHost.BrakeLampsPeak}..."` and the
# stripper removed every double-quoted run wholesale.
#
# That is not a corner. `SimDirector`'s done-line is one interpolated string
# hundreds of expressions long, and it is where most of this project's
# Game-layer statics are read. A check blind to `$"..."` is blind to the place
# the mistake actually happens.
#
# Caught only because rule 5b was applied: the accepting case passed, and the
# REJECTING case — the real error, put back — passed too. A lint that returns
# zero on everything is not a lint.
INTERP = re.compile(r'\$"(?:[^"\\]|\\.)*"', re.S)
BRACED = re.compile(r"\{([^{}]*)\}")


def code_only(text):
    """Comments and plain string literals blanked; the EXPRESSIONS inside
    interpolated strings kept, because they are compiled."""
    text = COMMENT.sub(" ", text)
    text = INTERP.sub(lambda m: " ".join(BRACED.findall(m.group(0))), text)
    return PLAIN.sub(" ", text)

# A property, field or method DECLARATION — `public static Foo Bar` / `Bar =>` /
# `Bar {`. Deliberately loose: this set is only ever used to EXCLUDE, so a false
# member costs a missed error and a missed member costs a false alarm, and the
# second is far more expensive in a check people have to trust.
MEMBER = re.compile(
    r"\b(?:public|internal|protected|private)\s+(?:static\s+|readonly\s+|"
    r"virtual\s+|override\s+|abstract\s+|partial\s+|const\s+|new\s+)*"
    r"[\w<>\[\],?\.]+\s+([A-Z]\w*)\s*(?:=>|\{|;|=|\()")


def IS_CORE(path):
    """Core filenames collide with `GameController` property names constantly —
    `Empire`, `Harm`, `Suspicion`, `Traffic` and fourteen others. Excluding the
    folder is cruder than resolving the name and is the honest trade: this check
    is worth having only if it never cries wolf."""
    return "Core" in path.parts


def sources():
    for root in SCAN:
        if root.exists():
            yield from sorted(root.rglob("*.cs"))


def main():
    files = list(sources())
    declared, stems = set(), {}
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        declared.update(DECL.findall(text))
        stems.setdefault(f.stem, f)

    # THE TRAP SET, AND THE FIRST VERSION OF IT WAS WRONG — which the live
    # codebase said immediately, exactly as rule 5b promises.
    #
    # v1 took every filename that is not a type. That flagged hundreds of lines
    # that compile perfectly, because C# capitalises PROPERTIES too: `Suspicion`,
    # `Empire`, `ActThree`, `Harm` and fourteen more are Core filenames AND
    # `GameController` property names, so `Empire.Businesses` is a property
    # chain and not a type reference. A capitalised identifier before a dot
    # cannot be told from a type without resolution, which is the thing this
    # file exists to work without.
    #
    # So the set is narrowed to what the actual mistake was: a GAME-LAYER file
    # named like a type, that declares no type, whose name is also not a member
    # anywhere. Those fourteen — AccessHost, TrafficHost, PhoneUI and the rest —
    # are `GameController` partials and there is nothing they could legitimately
    # qualify. Core filenames are excluded outright, because that is where the
    # property collisions live.
    #
    # Printed even when zero, because it is the DENOMINATOR: "0 errors" over an
    # empty trap set means the convention changed, not that the code is clean,
    # and those look identical without the number.
    members = set()
    for f in files:
        text = code_only(f.read_text(encoding="utf-8", errors="replace"))
        members.update(MEMBER.findall(text))
    traps = {
        s for s, f in stems.items()
        if s not in declared and s not in members and not IS_CORE(f)
    }

    bad = []
    for f in files:
        text = code_only(f.read_text(encoding="utf-8", errors="replace"))
        for i, line in enumerate(text.splitlines(), 1):
            for name in USE.findall(line):
                if name in traps:
                    bad.append((f.relative_to(ROOT), i, name, stems[name].name))

    for path, line, name, owner in bad:
        print(f"{path}:{line}: `{name}.` is not a type — {owner} declares no "
              f"type of that name (CS0103)")

    print(f"lint-filetype: {len(bad)} filename-as-type error(s) "
          f"({len(files)} file(s) scanned, {len(declared)} type(s) declared, "
          f"{len(traps)} filename(s) that are not types)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
