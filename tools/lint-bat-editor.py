#!/usr/bin/env python3
"""Every .bat that runs git must stop git opening an EDITOR.

WHY THIS EXISTS, 26 Aug. A `git pull` in `UPDATE FROM CLAUDE.bat` made a merge
commit, git opened vim in Jafar's window to ask for a message, he closed the
window, and the half-finished merge blocked every pull afterwards. The symptom
was "You have not concluded your merge" on a later run - a sentence that names
the state and not the cause, so it read as the pull being broken rather than
as something having waited for a human that nobody knew was waiting.

Swept the same morning: TWENTY-TWO .bat files run `git pull` and NOT ONE
guarded this. One idea, twenty-two implementations, in scripts whose entire
purpose is that nobody is watching the window - which is rule 1's third
corollary at its widest, and the reason this is a lint and not a fix.

WHAT IT ASKS. A file that runs any git command capable of opening an editor
(`pull`, `merge`, `rebase`, or a bare `commit`) must set `GIT_EDITOR` first.
`GIT_MERGE_AUTOEDIT=no` is also checked because it is the one git honours for
the merge-message prompt specifically, and belt-and-braces here costs a line.

THE DENOMINATOR SHIPS WITH THE ZERO (rule 3b): it prints how many .bat files
were read and how many actually run git, so "0 unguarded" cannot read the same
as "the glob matched nothing".
"""
import pathlib
import re
import sys

# `git commit -m` cannot open an editor; a bare `git commit` can.
RISKY = re.compile(r"\bgit\s+(pull|merge|rebase|commit)\b(?![^\n]*-m\s)", re.I)


#: THE REPOSITORY, FROM THIS FILE'S OWN LOCATION rather than from wherever the
#: shell is standing. `verify.py` runs from `ledger/`, so a default of "." made
#: the first live run sweep a directory with no .bat files in it at all.
#: It printed `0 unguarded (0 .bat file(s) read)` and exited 2 — which is the
#: denominator doing its job: a clean-looking zero over an empty set was
#: refused rather than believed. Same fault BarkGen had when it wrote its
#: manifest to whatever directory the shell happened to be in.
REPO = pathlib.Path(__file__).resolve().parent.parent


def main(root=None):
    bats = sorted(pathlib.Path(root or REPO).rglob("*.bat"))
    risky, bad = [], []
    for p in bats:
        try:
            s = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not RISKY.search(s):
            continue
        risky.append(p)
        if "GIT_EDITOR" not in s:
            bad.append(p)
    for p in bad:
        print("%s: runs git but never sets GIT_EDITOR — a merge or commit "
              "prompt will hang this script forever" % p)
    print("lint-bat-editor: %d unguarded (%d .bat file(s) read, %d run a git "
          "command that can open an editor)" % (len(bad), len(bats), len(risky)))
    if not bats:
        print("  NOTHING MEASURED — no .bat files found under %r" % root)
        return 2
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
