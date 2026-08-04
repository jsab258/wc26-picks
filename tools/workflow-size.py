#!/usr/bin/env python3
"""Is any workflow step too big for GitHub to accept?

    python3 tools/workflow-size.py          # every workflow, largest step each
    python3 tools/workflow-size.py --self-test

WHY THIS EXISTS. A comment made `workflow_dispatch` fail outright:

    422 Invalid Argument - failed to parse workflow:
    (Line: 269, Col: 14): Exceeded max expression length 21000

Line 269 col 14 is where a `run: |` block begins. GitHub applies an expression
length limit to the whole block, comments included — so the sim's build step,
which carries a long written record of why each thing in it is there, has been
growing toward a hard ceiling for weeks with nothing watching.

The failure is worse than an error message. NOTHING CAN BE DISPATCHED: the
Windows build is the only way to compile the Game layer at all, and the only
channel out of CI this environment can read. Twenty-eight minutes of round trip
becomes zero, and the error arrives at dispatch time rather than at commit time
— so the commit that breaks it looks green, lands, and the breakage is found by
whoever next tries to build.

THE BOUND IS MEASURED, NOT THE ONE IN THE ERROR. GitHub says 21000 and the
block that dispatched perfectly an hour before the break measures 23184 by the
count below, so their accounting is not this one — probably trimming
indentation, or counting the parsed scalar rather than the raw lines. Guessing
at their formula would be inventing a threshold (rule 2). What is actually
known is two data points:

    23184  dispatched fine, repeatedly, all morning
    24868  422, max expression length

so the bound is the largest block that has ever been ACCEPTED. Anything above
it is untested ground, and the message says so rather than claiming to know
where the cliff is.

It counts raw lines including the newline, which is deliberately the most
pessimistic reading — the real limit cannot be smaller than what has shipped.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"

# The largest `run:` block that has ever been accepted by workflow_dispatch,
# measured by the function below. Evidence, not a guess — see the docstring.
KNOWN_GOOD = 23184

# `- run: |` as well as `run: |`. The self-test caught this on its FIRST run:
# the fixture used the list form, the live workflow uses the mapping form, and
# a check that only sees the form its own repository happens to use is a check
# that reports "all clear" on a file it cannot read. Exactly why rule 5b says
# to run the accepting case — the rejecting case passed while blind.
#
# The dash counts toward the indent for the continuation test, which is what
# YAML does too: the block's content must out-indent the `-`.
RUN_START = re.compile(r"^(\s+(?:- )?)run: [|>]")


def blocks(text):
    """Every `run:` block, as (start_line, char_count).

    A block runs until a line that is neither blank nor more-indented than the
    `run:` key itself. Blank lines inside a block are kept, because they are
    characters GitHub has to carry too.
    """
    lines = text.split("\n")
    out = []
    for i, line in enumerate(lines):
        m = RUN_START.match(line)
        if not m:
            continue
        indent = len(m.group(1))
        j, n = i + 1, 0
        while j < len(lines):
            s = lines[j]
            if s.strip() and (len(s) - len(s.lstrip())) <= indent:
                break
            n += len(s) + 1
            j += 1
        out.append((i + 1, n))
    return out


def check(paths):
    worst_over = []
    report = []
    for p in sorted(paths):
        found = blocks(p.read_text(encoding="utf-8"))
        if not found:
            continue
        line, size = max(found, key=lambda b: b[1])
        report.append((p.name, line, size))
        if size > KNOWN_GOOD:
            worst_over.append((p.name, line, size))
    return report, worst_over


def self_test():
    """BOTH OUTCOMES, and the accepting one first (rule 5b).

    The expensive failure for a size guard is not letting a big file through —
    it is refusing every ordinary one, because a check that cannot pass gets
    switched off within a day and takes the real catch with it.
    """
    small = "jobs:\n  a:\n    steps:\n      - run: |\n          echo hello\n          echo again\n"
    r, over = check([_Fake("small.yml", small)])
    ok1 = r and r[0][2] < 100 and not over
    print(f"  {'ok  ' if ok1 else 'FAIL'} an ordinary step passes and is measured "
          f"({r[0][2] if r else '?'} chars)")

    big = "jobs:\n  a:\n    steps:\n      - run: |\n" + "          # x\n" * 3000
    r, over = check([_Fake("big.yml", big)])
    ok2 = len(over) == 1 and over[0][2] > KNOWN_GOOD
    print(f"  {'ok  ' if ok2 else 'FAIL'} a step past the largest ever accepted is caught "
          f"({over[0][2] if over else '?'} chars)")

    # A file with no `run:` at all must not crash and must not be reported.
    r, over = check([_Fake("none.yml", "on: push\n")])
    ok3 = not r and not over
    print(f"  {'ok  ' if ok3 else 'FAIL'} a workflow with no run block is skipped, not crashed")
    return 0 if (ok1 and ok2 and ok3) else 1


class _Fake:
    """A path-like with inline text, so the self-test needs no files on disk."""
    def __init__(self, name, text):
        self.name = name
        self._text = text

    def read_text(self, encoding=None):
        return self._text

    def __lt__(self, other):
        return self.name < other.name


def main():
    if "--self-test" in sys.argv:
        return self_test()
    if not WORKFLOWS.is_dir():
        print("workflow-size: no .github/workflows")
        return 0
    report, over = check(list(WORKFLOWS.glob("*.yml")) + list(WORKFLOWS.glob("*.yaml")))
    if not report:
        print("workflow-size: no run blocks found")
        return 0
    biggest = max(r[2] for r in report)
    if over:
        print(f"workflow-size: {len(over)} step(s) LARGER THAN ANYTHING THAT HAS "
              f"EVER DISPATCHED ({KNOWN_GOOD} chars):")
        for name, line, size in over:
            print(f"  {name}:{line}  {size} chars, {size - KNOWN_GOOD} over")
        print("  A 422 at dispatch time means NO Windows build at all — and it is")
        print("  raised when you try to build, not when you commit. Shorten the step.")
        return 1
    print(f"workflow-size: {len(report)} workflow(s), largest step {biggest} chars "
          f"({KNOWN_GOOD - biggest} under the largest ever accepted)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
