#!/usr/bin/env python3
"""Every design doc must say what it is, at the top, before anybody reads it.

WHY THIS EXISTS. Jafar asked for the project's high-level state. I answered
from `roadmap.md`'s "STILL OPEN — the honest list", told him the Mixamo
character drop was the single biggest blocker in the project, and recommended
he go and do it. It had shipped the day before — 41 clips and two bodies, in
the repo, with a whole roadmap section describing them. The list I quoted was
dated three days earlier and said so at the top of a 1400-line file, hundreds
of lines above the part I read.

That is not a mistake you fix by being more careful. A file is read from
wherever the grep landed, and a date at the top of a long document is invisible
from the middle of it. So every doc now declares its own status in its first
few lines, where any excerpt of it starts:

  LIVE  — kept current, and wrong is a bug
  SPEC  — the intent; build state lives in the roadmap
  LOG   — true on one dated day, explicitly NOT the present

    python tools/docs-check.py
"""
import pathlib
import re
import sys

DOCS = pathlib.Path(__file__).resolve().parent.parent / "game-design"
KINDS = ("LIVE", "SPEC", "LOG")
# A banner has to be near the top or it does not do its job.
WITHIN_LINES = 8

_fails = []


def check(ok, what, got=""):
    print(("  ok   " if ok else "  FAIL ") + what + ("" if ok else f" — {got}"))
    if not ok:
        _fails.append(what)


def main():
    docs = sorted(DOCS.glob("*.md"))
    print(f"docs-check — {len(docs)} documents in game-design/")
    seen = {k: 0 for k in KINDS}

    for p in docs:
        head = p.read_text(encoding="utf-8").split("\n")[:WITHIN_LINES]
        m = re.search(r"\*\*STATUS — (LIVE|SPEC|LOG)", "\n".join(head))
        if not m:
            check(False, f"{p.name} declares a status in its first {WITHIN_LINES} lines",
                  "no STATUS banner")
            continue
        kind = m.group(1)
        seen[kind] += 1

        if kind == "LOG":
            # A log without its date is the exact trap this file exists for.
            dated = re.search(r"\*\*STATUS — LOG, (\d{4}-\d{2}(-\d{2})?)", "\n".join(head))
            check(bool(dated), f"{p.name} — LOG entry carries its date", "undated LOG")
            check("NOT CURRENT" in "\n".join(head),
                  f"{p.name} — LOG entry says it is not current")
        if kind == "LIVE":
            # A live doc that has not been verified is just a log nobody
            # relabelled, which is how this went wrong the first time.
            check(bool(re.search(r"verified \d{4}-\d{2}-\d{2}", "\n".join(head))),
                  f"{p.name} — LIVE doc carries a verified date")

    print(f"\n  {seen['LIVE']} live, {seen['SPEC']} spec, {seen['LOG']} log")
    # The roadmap is the tiebreak and has to say so, because two docs
    # disagreeing is the normal state of a project this size.
    road = (DOCS / "roadmap.md").read_text(encoding="utf-8")[:600]
    check("this wins" in road or "wins" in road,
          "roadmap.md claims precedence over other docs")

    print(f"\n{len(docs) * 0 + sum(1 for _ in docs) - len(_fails)}/{len(docs)} clean"
          if not _fails else f"\n{len(_fails)} problem(s)")
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
