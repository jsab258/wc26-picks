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
    # ONE LEVEL WAS NEVER THE SCOPE, it was the shape of the directory the
    # day this was written. `game-design/agent-reports/` arrived on 24 Aug and
    # nothing examined it: adding a report left the count at 61/61 clean, so
    # the check could not tell "examined and fine" from "never looked" —
    # rule 3b, in the checker rather than in a metric. Its own convention
    # decayed inside one day: the first report carried the banner, the four
    # written the next night did not, because nothing enforced it.
    docs = sorted(DOCS.rglob("*.md"))
    print(f"docs-check — {len(docs)} documents under game-design/ (recursive)")
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

    # A LIVE DOC THAT HAS GROWN A CHRONOLOGY IS NOT LIVE ANY MORE.
    #
    # The roadmap reached 1,525 lines of which ~85% was dated: thirteen
    # "BUILD STATE — <date>" sections interleaved with milestone definitions,
    # a 219-line "STILL OPEN" list four days stale, a 337-line re-sequencing.
    # The first pass of this checker gave it a LIVE banner and called it clean,
    # because a banner says what a document CLAIMS to be and nothing about
    # whether it still is. Jafar read it and said so.
    #
    # Two cheap shapes catch it: length, and dated headings. A live doc that
    # wants to be read has to stay short, and history belongs in a LOG.
    for p2 in docs:
        head = p2.read_text(encoding="utf-8").split("\n")[:WITHIN_LINES]
        if not re.search(r"\*\*STATUS — LIVE", "\n".join(head)):
            continue
        # splitlines, NOT split("\n"): every text file here ends in a newline,
        # so split leaves a phantom empty final element and the count printed
        # in the failure message is one more than wc -l says. That made the
        # 400-line cap really a 399-line cap and sent me hunting for a line
        # that was not there — the instrument disagreeing with every other
        # line-counting tool in the project (rule 3).
        body = p2.read_text(encoding="utf-8").splitlines()
        # NARROWED, DELIBERATELY, after the first version flagged three docs
        # of which only one was really guilty. "§7.1 Streets and the car (M12,
        # built 2026-07-26)" is a design section carrying its provenance and is
        # good practice; "BUILD STATE — 2026-07-29" and "What changed on
        # 2026-07-29" are a diary. A date in a heading does not distinguish
        # them, so the check now looks for the diary markers rather than for
        # dates, and asserts only what it can actually tell.
        diary = [l for l in body
                 if re.match(r"^#{2,3} .*(BUILD STATE|[Ww]hat changed on|"
                             r"[Tt]he night of|[Oo]vernight|— round \d)", l)]
        check(not diary, f"{p2.name} — a live doc is not a diary",
              "; ".join(x.strip()[:44] for x in diary[:2]))
        # LENGTH IS FOR PLANS AND QUEUES, NOT FOR SPECIFICATIONS. A founding
        # design document is long by nature; a roadmap that is long has failed.
        # The doc says which it is rather than this file keeping a list.
        reference = "reference" in "\n".join(head)
        if not reference:
            check(len(body) <= 400,
                  f"{p2.name} — a live plan stays scannable (<=400 lines)",
                  f"{len(body)} lines — mark it `reference` if it is a specification")
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
