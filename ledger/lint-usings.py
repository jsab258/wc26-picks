#!/usr/bin/env python3
"""Catch the one compile error a parse-only check cannot see.

Unity is the only thing that semantically compiles the Assets/Scripts tree —
CoreTests compiles Core, and the Roslyn syntax checker only parses. So a file
that uses LINQ in extension form without importing System.Linq parses
perfectly, reads perfectly, and fails only on a CI runner twenty minutes
later. That happened on run 30218023272, in a file that deliberately does not
import System.Linq and fully-qualifies instead, where two new lines used
`.Count(lambda)` — which to a reader looks like the Count PROPERTY and to the
compiler is a missing extension method.

Cheap, exact, and it runs in under a second:

    python3 ledger/lint-usings.py ledger/Assets/Scripts

Exit code 0 = clean.
"""
import re
import sys
import pathlib

# Extension-form LINQ that only resolves with `using System.Linq`. Each needs a
# lambda or an empty call, so `.Count` (the property) and `.Any` on a HashSet
# are not caught by accident.
LINQ = re.compile(
    r"\.(Any|All|Count|Sum|Min|Max|Average|Where|Select|SelectMany|First|"
    r"FirstOrDefault|Last|LastOrDefault|Single|SingleOrDefault|OrderBy|"
    r"OrderByDescending|ThenBy|ThenByDescending|Skip|Take|Distinct|Concat|"
    r"Except|Intersect|Union|Reverse|GroupBy|Zip|ToList|ToArray|ToDictionary|"
    r"ToHashSet|Cast|OfType|SequenceEqual|Aggregate|TakeWhile|SkipWhile|"
    r"Prepend|ElementAt|ElementAtOrDefault|DefaultIfEmpty|ToLookup|MaxBy|"
    r"MinBy|Chunk)\s*[(<]"
)

# `.ToList()` etc. also exist on some non-LINQ types, and List<T> has its own
# ConvertAll/Find. These are the names that are ALWAYS LINQ in this codebase.
ALWAYS_LINQ = {
    "Any", "All", "Where", "Select", "SelectMany", "FirstOrDefault",
    "LastOrDefault", "SingleOrDefault", "OrderBy", "OrderByDescending",
    "ThenBy", "ThenByDescending", "Skip", "Take", "Distinct", "Except",
    "Intersect", "Union", "GroupBy", "Zip", "ToDictionary", "Cast", "OfType",
    "SequenceEqual", "Aggregate", "Sum", "Average",
    # audit 2026-07-27: always-LINQ names the list missed. (Append and
    # Contains stay out — the regex is receiver-blind and StringBuilder
    # .Append / List.Contains would false-positive constantly.)
    "TakeWhile", "SkipWhile", "Prepend", "ElementAt", "ElementAtOrDefault",
    "DefaultIfEmpty", "ToLookup", "MaxBy", "MinBy", "Chunk",
}

# A member call whose receiver is `System.Linq.Enumerable` is already qualified.
QUALIFIED = re.compile(r"System\.Linq\.Enumerable\s*\.")


# Parameterless call = LINQ for these: no common BCL receiver in this
# codebase has the empty-arg method (List<T>.Count is a property, ToArray/
# Reverse/Contains exist on List<T> and are deliberately absent here).
EMPTY_CALL_LINQ = {
    "Count", "ToList", "First", "FirstOrDefault", "Last", "LastOrDefault",
    "Single", "SingleOrDefault", "Min", "Max", "Sum", "Average", "Distinct",
    "ToHashSet",
}


CONTAINERS = re.compile(r"\b(List|Dictionary|HashSet|Queue|Stack)\s*<")
GENERIC_USING = re.compile(r"^\s*using\s+System\.Collections\.Generic\s*;", re.MULTILINE)


def check_containers(path: pathlib.Path, text: str) -> list:
    """A BCL container without its using dies in Unity's compiler, not here —
    two CI builds proved it (2026-07-28). Textual, so it needs no references."""
    if GENERIC_USING.search(text):
        return []
    problems = []
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("///"):
            continue
        if "System.Collections.Generic" in line:
            continue
        m = CONTAINERS.search(line)
        if m:
            problems.append((lineno, "generic:" + m.group(1), stripped))
    return problems


def check(path: pathlib.Path) -> list:
    text = path.read_text(encoding="utf-8", errors="replace")
    problems = check_containers(path, text)
    if re.search(r"^\s*using\s+System\.Linq\s*;", text, re.MULTILINE):
        return problems

    lines = text.splitlines()
    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("///"):
            continue
        # Strip already-qualified calls so they do not look like extensions.
        scrubbed = QUALIFIED.sub("QUALIFIED_", line)
        for m in LINQ.finditer(scrubbed):
            name = m.group(1)
            # `.Count(` and `.ToList(` are ambiguous — List<T> has neither as a
            # method, but other types might. Flag them only with a lambda.
            if name not in ALWAYS_LINQ:
                after = scrubbed[m.end():]
                # audit 2026-07-27: the docstring promised "a lambda or an
                # empty call", and the empty-call half was never implemented.
                # Only names where no common BCL receiver has the parameterless
                # method (List.Count is a property; .Count() is LINQ).
                if name in EMPTY_CALL_LINQ and after.lstrip().startswith(")"):
                    problems.append((lineno, name, stripped))
                    continue
                # The lambda may sit on the NEXT line — normal formatting for a
                # long predicate — but only when the call's argument list is
                # still open at the line break. Same-line-only scanning let
                # those through; unconditional look-ahead flagged Math.Max next
                # to any expression-bodied member (audit 2026-07-27).
                spans_lines = after.count("(") + 1 > after.count(")")
                lookahead = after if not spans_lines else after + " " + " ".join(lines[lineno:lineno + 2])
                if "=>" not in lookahead[:200]:
                    continue
            problems.append((lineno, name, stripped))
    return problems


# ---------------------------------------------------------------------------
# COLLISION CHECK: a Core type must not be named after a UnityEngine one.
#
# Neither of the other two gates can see this. lint-usings is textual, and
# ShapeCheck compiles WITHOUT reference assemblies, so neither of them knows
# that UnityEngine has a type called Space — only the real Unity compiler
# does, which means the first thing that ever notices is a red CI build
# eighteen minutes in.
#
# That is exactly what happened: Core got an enum called `Space`, every local
# suite went green, and the player build died on
#   CS0104: 'Space' is an ambiguous reference between 'Ledger.Core.Space'
#           and 'UnityEngine.Space'
# because every Game file carries `using UnityEngine;` AND `using Ledger.Core;`.
#
# The list is curated rather than complete — we cannot enumerate UnityEngine
# from here — but it covers the names anyone would plausibly reach for when
# naming a simulation type, which is the whole risk surface. Add to it when
# the compiler teaches us a new one.
ENGINE_TYPES = {
    "Animation", "Animator", "Application", "AudioClip", "AudioSource", "Bounds",
    "Camera", "Collider", "Collision", "Color", "Component", "Cursor", "Debug",
    "Display", "Event", "Font", "Gradient", "Input", "Joint", "Keyframe", "Light",
    "LightType", "Material", "Mathf", "Matrix4x4", "Mesh", "Motion", "Object",
    "Physics", "Plane", "Pose", "Quaternion", "Random", "Range", "Ray", "Rect",
    "RectTransform", "Renderer", "Resolution", "Resources", "Rigidbody", "Screen",
    "Shader", "Space", "Sprite", "State", "SystemInfo", "Texture", "Time",
    "Tooltip", "Transform", "Vector2", "Vector3", "Vector4",
    # System, for the same reason: Core has `using System;` everywhere.
    "Console", "Environment", "Exception", "Path", "Task", "Timer", "Type",
}

TYPE_DECL = re.compile(
    r"^\s*public\s+(?:sealed\s+|abstract\s+|static\s+|partial\s+|readonly\s+)*"
    r"(?:class|struct|enum|interface|record)\s+([A-Za-z_]\w*)")


def check_collisions(path):
    """Public Core type names that a Game file could not disambiguate."""
    out = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return out
    for lineno, line in enumerate(lines, 1):
        m = TYPE_DECL.match(line)
        if m and m.group(1) in ENGINE_TYPES:
            out.append((lineno, m.group(1), line.strip()))
    return out


CORE_USING = re.compile(r"^\s*using\s+Ledger\.Core\s*;", re.MULTILINE)

# Comments and string literals, stripped WHOLE-FILE rather than line by line.
#
# The line-by-line version of this was wrong and I only found out by feeding
# it a probe: the character cards in CastSetup and friends are multi-line
# `@"..."` blocks, so any prose in one that happened to say `Combat.Resolve(`
# read as code and the gate cried wolf. A gate that cries wolf is a gate
# people turn off, which is worse than not having it.
#
# One alternation, in this order, so a `//` inside a string is not a comment
# and a quote inside a comment does not open a string. Verbatim forms come
# before the ordinary one because `@"a\"` is not an escape.
NOISE = re.compile(
    r'/\*.*?\*/'                    # block comment, multi-line
    r"|//[^\n]*"                     # line comment
    r'|[$@]{1,2}"(?:[^"]|"")*"'      # @"..", $@"..", @$".." — multi-line, "" escapes
    r'|"(?:[^"\\\n]|\\.)*"'         # ordinary string
    r"|'(?:[^'\\\n]|\\.)*'",        # char literal
    re.S)


def scrub(text: str) -> str:
    """Blank out comments and literals, PRESERVING NEWLINES so the line
    numbers this reports still point at the real line."""
    return NOISE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def core_type_names(root: pathlib.Path) -> set:
    """Every public type Core declares. Read from the tree rather than listed,
    because a list goes stale the day somebody adds a type."""
    names = set()
    for path in sorted(root.rglob("*.cs")):
        if path.parts[-2] != "Core":
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = TYPE_DECL.match(line)
            if m:
                names.add(m.group(1))
    return names


def check_core_using(path: pathlib.Path, core_names: set) -> list:
    """A Game file that names a Core type without importing Ledger.Core.

    This is CS0103 at player-build time and NOTHING before it can see it:
    CoreTests compiles Core alone so the name always resolves there, the
    Roslyn check has no reference assemblies so it discards CS0103 wholesale,
    and this lint used to look only at LINQ and container usings. Cost of
    finding out the other way: a twenty-minute round trip on a CI runner,
    which is exactly what `Menus` in OptionsScreen.cs cost on run
    30391686667.
    """
    out = []
    raw = path.read_text(encoding="utf-8", errors="replace")
    if CORE_USING.search(raw):
        return out
    # Types the file declares itself shadow the Core name legitimately.
    own = {m.group(1) for m in (TYPE_DECL.match(l) for l in raw.splitlines()) if m}
    lines = raw.splitlines()
    for lineno, code in enumerate(scrub(raw).splitlines(), 1):
        line = lines[lineno - 1] if lineno <= len(lines) else code
        if re.match(r"\s*using\s", code):
            continue
        for name in core_names:
            if name in own:
                continue
            # Not preceded by a dot: `foo.Menus` is a member, not the type.
            if re.search(r"(?<![\w.])" + re.escape(name) + r"\s*[.(<]", code):
                out.append((lineno, name, line.strip()))
                break
    return out


# Names that exist in BOTH System and UnityEngine. A file carrying both
# usings and referring to any of them bare is CS0104 — and this is the
# hardest of the three to see coming, because the file compiles fine right
# up until somebody adds `using System;` for one call to Math.Abs.
#
# Which is exactly what happened: `using System;` went onto Audio.cs, which
# has used bare `Object.DontDestroyOnLoad` and `Random.Range` since it was
# written. ShapeCheck could not see it — its Unity stubs have no
# UnityEngine.Object or UnityEngine.Random for System's to collide with —
# and the failure surfaced as an eighteen-second Unity build with the error
# already scrolled out of the log window.
# ONLY THESE TWO, and getting the list right matters more than having one.
#
# The first version also listed Debug and Array and immediately reported
# fourteen files that compile perfectly. `using System;` imports the System
# NAMESPACE, not System.Diagnostics — so there is no `System.Debug` for
# UnityEngine.Debug to collide with, and `System.Array` has no UnityEngine
# counterpart at all. Only Object and Random genuinely exist in both.
#
# A gate that flags working code is a gate people switch off, which is worse
# than not having one. This file already carries that lesson once, from the
# multi-line verbatim strings a few functions down.
AMBIGUOUS = ("Object", "Random")
SYSTEM_USING = re.compile(r"^\s*using\s+System\s*;", re.MULTILINE)
ENGINE_USING = re.compile(r"^\s*using\s+UnityEngine\s*;", re.MULTILINE)


def check_ambiguous(path: pathlib.Path) -> list:
    """Bare uses of a name that both System and UnityEngine define, in a file
    that imports both namespaces."""
    out = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return out
    if not (SYSTEM_USING.search(text) and ENGINE_USING.search(text)):
        return out
    code = scrub(text)
    lines = code.splitlines()
    for name in AMBIGUOUS:
        # `Name.` or `Name)` or `Name ` used as a type — but NOT when it is
        # already qualified (`System.Object`, `UnityEngine.Random`) and not
        # when it is part of a longer identifier (`RandomWalk`, `_object`).
        pat = re.compile(r"(?<![.\w])" + name + r"\s*\.")
        for lineno, line in enumerate(lines, 1):
            if pat.search(line):
                out.append((lineno, name, line.strip()))
    return out


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ledger/Assets/Scripts")
    core_names = core_type_names(root)
    bad = 0
    files = 0
    for path in sorted(root.rglob("*.cs")):
        if "/obj/" in str(path) or "/bin/" in str(path):
            continue
        files += 1
        if path.parts[-2] != "Core":
            for lineno, name, line in check_core_using(path, core_names):
                bad += 1
                print(f"{path}:{lineno}: uses Core type '{name}' without "
                      f"'using Ledger.Core;'. That is CS0103 at player-build time and "
                      f"nothing before it can see it — CoreTests compiles Core alone, "
                      f"and ShapeCheck has no reference assemblies so it discards "
                      f"CS0103 wholesale.\n    {line}")
        if path.parts[-2] == "Core":
            for lineno, name, line in check_collisions(path):
                bad += 1
                print(f"{path}:{lineno}: Core type '{name}' collides with a UnityEngine/System type "
                      f"of the same name. Every Game file carries both usings, so this is "
                      f"CS0104 at player-build time and nothing before it can see it. "
                      f"Rename it — '{name}Kind' matches the StanceKind convention.\n    {line}")
        for lineno, name, line in check_ambiguous(path):
            bad += 1
            print(f"{path}:{lineno}: bare '{name}.' with BOTH 'using System;' and "
                  f"'using UnityEngine;' — CS0104, because both namespaces define "
                  f"{name}. Drop 'using System;' and spell out System.Math etc, or "
                  f"qualify this use. ShapeCheck cannot see it: its Unity stubs have "
                  f"no UnityEngine.{name} to collide with.\n    {line}")
        for lineno, name, line in check(path):
            bad += 1
            if name.startswith("generic:"):
                print(f"{path}:{lineno}: {name[8:]}<> needs 'using System.Collections.Generic;'\n    {line}")
            else:
                print(f"{path}:{lineno}: .{name}(...) needs 'using System.Linq;' "
                      f"or System.Linq.Enumerable.{name}(...)\n    {line}")
    print(f"checked {files} files, {bad} missing-using/collision error(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
