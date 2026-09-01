#!/usr/bin/env python3
"""The goal block at the top of CLAUDE.md must match its source VERBATIM.

WHY THIS IS A TOOL AND NOT A LINE IN A CHECKLIST. Jafar's instruction was
that a mismatch is a violation. A violation nobody can detect is a wish, and
comparing a paragraph inside a 15,000-word file against another file by eye,
once a week, is the kind of check this project has watched decay repeatedly.
The comparison is mechanical, so it should be done mechanically.

WHAT IT COMPARES. The `## The goal` and `## The Meridian Test` sections of
ledger-v2/respec/vision-pillars-v2.md, which is the SOURCE, against the copy
under the goal heading at the top of CLAUDE.md. Whitespace at line ends is
normalised because an editor can add it invisibly; nothing else is.

DIRECTION MATTERS. The source wins. This tool never tells you CLAUDE.md is
right and the source is wrong, because the copy is a copy.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "ledger-v2", "respec", "vision-pillars-v2.md")
DST = os.path.join(REPO, "CLAUDE.md")
HEADING = "# THE GOAL (read nothing else if you read nothing else)"
START = "## The goal"
END = "\n## Pillars"


def norm(text):
    return "\n".join(line.rstrip() for line in text.strip().split("\n"))


def extract_source(path=SRC):
    if not os.path.exists(path):
        return None, "the source %s does not exist" % os.path.relpath(path, REPO)
    s = open(path, encoding="utf-8").read()
    if START not in s or END not in s:
        return None, "the source has no '%s' section ending at '## Pillars'" % START
    return norm(s[s.index(START):s.index(END)]), "read the source"


def extract_copy(path=DST):
    if not os.path.exists(path):
        return None, "%s does not exist" % os.path.relpath(path, REPO)
    s = open(path, encoding="utf-8").read()
    if not s.startswith(HEADING):
        return None, ("CLAUDE.md does not OPEN with the goal heading. Jafar's "
                      "instruction was that it comes before any other content.")
    body = s[len(HEADING):]
    if START not in body:
        return None, "no '%s' section under the goal heading" % START
    body = body[body.index(START):]
    cut = body.find("\n---")
    if cut == -1:
        return None, "the goal block is not closed by a '---' rule"
    return norm(body[:cut]), "read the copy"


def check():
    src, why_src = extract_source()
    dst, why_dst = extract_copy()
    if src is None:
        return 2, "goal block NOT CHECKED: %s" % why_src
    if dst is None:
        return 1, "goal block VIOLATION: %s" % why_dst
    if src == dst:
        return 0, ("goal block matches its source verbatim (%d chars, %d lines "
                   "compared)" % (len(src), len(src.split("\n"))))
    s_lines, d_lines = src.split("\n"), dst.split("\n")
    first = next((i for i in range(max(len(s_lines), len(d_lines)))
                  if s_lines[i:i + 1] != d_lines[i:i + 1]), 0)
    return 1, ("goal block VIOLATION: CLAUDE.md's copy differs from "
               "vision-pillars-v2.md at line %d of the block.\n"
               "  source: %s\n"
               "  copy  : %s\n"
               "  THE SOURCE WINS. Edit vision-pillars-v2.md, then re-copy."
               % (first + 1,
                  (s_lines[first] if first < len(s_lines) else "(source ends)")[:90],
                  (d_lines[first] if first < len(d_lines) else "(copy ends)")[:90]))


def selftest():
    ok = fail = 0

    def c(name, cond):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print("  FAIL %s" % name)

    # ACCEPTING CASE FIRST, and it is the live tree: the two really do match
    # today, so this fixture cannot be fooled by one I wrote.
    code, msg = check()
    c("ACCEPTING: the live CLAUDE.md matches the live source", code == 0)
    c("ACCEPTING: it says what it compared", "chars" in msg and "lines" in msg)

    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "c.md")
        # REJECTING: a copy that does not open the file.
        open(p, "w").write("# something else\n\n" + HEADING + "\n## The goal\nx\n\n---\n")
        c("rejecting: goal block not at the very top", extract_copy(p)[0] is None)
        # REJECTING: opens correctly but is never closed.
        open(p, "w").write(HEADING + "\n\n## The goal\nx\n")
        c("rejecting: block with no closing rule", extract_copy(p)[0] is None)
        # ACCEPTING: the minimal well-formed shape.
        open(p, "w").write(HEADING + "\n\n## The goal\nx\n\n---\nrest\n")
        c("ACCEPTING: a well-formed minimal block is read", extract_copy(p)[0] == "## The goal\nx")
        # REJECTING: a missing source is NOT CHECKED, never a pass.
        c("rejecting: absent source returns None, not equality",
          extract_source(os.path.join(d, "gone.md"))[0] is None)

    print("goal-block-check selftest: %d ok, %d failed" % (ok, fail))
    return 1 if fail else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    code, msg = check()
    print(msg)
    sys.exit(code)
