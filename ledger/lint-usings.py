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
    r"ToHashSet|Cast|OfType|SequenceEqual|Aggregate)\s*[(<]"
)

# `.ToList()` etc. also exist on some non-LINQ types, and List<T> has its own
# ConvertAll/Find. These are the names that are ALWAYS LINQ in this codebase.
ALWAYS_LINQ = {
    "Any", "All", "Where", "Select", "SelectMany", "FirstOrDefault",
    "LastOrDefault", "SingleOrDefault", "OrderBy", "OrderByDescending",
    "ThenBy", "ThenByDescending", "Skip", "Take", "Distinct", "Except",
    "Intersect", "Union", "GroupBy", "Zip", "ToDictionary", "Cast", "OfType",
    "SequenceEqual", "Aggregate", "Sum", "Average",
}

# A member call whose receiver is `System.Linq.Enumerable` is already qualified.
QUALIFIED = re.compile(r"System\.Linq\.Enumerable\s*\.")


def check(path: pathlib.Path) -> list:
    text = path.read_text(encoding="utf-8", errors="replace")
    if re.search(r"^\s*using\s+System\.Linq\s*;", text, re.MULTILINE):
        return []

    problems = []
    for lineno, line in enumerate(text.splitlines(), 1):
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
                if "=>" not in after[:120]:
                    continue
            problems.append((lineno, name, stripped))
    return problems


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ledger/Assets/Scripts")
    bad = 0
    files = 0
    for path in sorted(root.rglob("*.cs")):
        if "/obj/" in str(path) or "/bin/" in str(path):
            continue
        files += 1
        for lineno, name, line in check(path):
            bad += 1
            print(f"{path}:{lineno}: .{name}(...) needs 'using System.Linq;' "
                  f"or System.Linq.Enumerable.{name}(...)\n    {line}")
    print(f"checked {files} files, {bad} missing-using error(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
