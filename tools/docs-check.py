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

  LIVE: kept current, and wrong is a bug
  SPEC: the intent; build state lives in the roadmap
  LOG:  true on one dated day, explicitly NOT the present

    python tools/docs-check.py
    python tools/docs-check.py --selftest    # accepting case FIRST

THE BANNER PUNCTUATION, RULED BY JAFAR 2026-09-03. This checker used to demand
`**STATUS` followed by an EM-DASH, while constitution law 11 bans em-dashes
anywhere: every document in `game-design/` therefore carried a deliberate law
violation because the checker required it, and two separate roles lost time to
it in one day, each writing the lawful colon form and being rejected for it.
The colon form is now the only accepted form and THE OLD ONE IS REFUSED, so
the migration in `tools/migrate-status-banner.py` cannot half-happen and
quietly leave two conventions running.

WHAT "AT BANNER POSITION" MEANS, and why the refusal is anchored. A dated
report may legitimately QUOTE the retired form inside backticks while
carrying a lawful banner of its own; five documents here do. So the refusal
fires on the old form at the START of a line only, and that definition is
IMPORTED from the migration script rather than retyped, because one idea with
two implementations is one implementation nobody fixes.

EXIT CODES, distinct per outcome. 0 clean. 1 at least one document failed, and
each is named. 3 the selftest failed. 4 the migration script could not be
imported, so the retired form has no definition to refuse against; this
program will not report a clean sweep it could not perform.
"""
import argparse
import importlib.util
import pathlib
import re
import sys

DOCS = pathlib.Path(__file__).resolve().parent.parent / "game-design"
KINDS = ("LIVE", "SPEC", "LOG")
# A banner has to be near the top or it does not do its job.
WITHIN_LINES = 8

# ONE IMPLEMENTATION PER IDEA: the retired form at banner position is defined
# by the migration that removed it, and imported here.
_MIG = pathlib.Path(__file__).resolve().parent / "migrate-status-banner.py"


def _load(path, name):
    try:
        spec = importlib.util.spec_from_file_location(name, str(path))
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:                                            # noqa: BLE001
        return None


_mig = _load(_MIG, "migrate_status_banner")
if _mig is None:
    sys.stderr.write("docs-check: tools/migrate-status-banner.py could not be "
                     "imported; refusing to report a banner sweep with no "
                     "definition of the retired form behind it\n")
    sys.exit(4)
RETIRED_RE = _mig.OLD_RE

# THE RULED FORM. The bold marks are optional: `**STATUS: LIVE**` and a plain
# `STATUS: LIVE` are the same declaration, and the second is what both roles
# wrote unprompted on the day this was ruled.
BANNER_RE = re.compile(r"(?:\*\*)?STATUS:[ \t]*(LIVE|SPEC|LOG)")
LOG_DATE_RE = re.compile(r"(?:\*\*)?STATUS:[ \t]*LOG,[ \t]*(\d{4}-\d{2}(-\d{2})?)")


def banner(head):
    """(kind, fault) for a document's first lines. EXACTLY ONE of the two is
    None. `head` is the joined first WITHIN_LINES lines.

    The order is deliberate: a document carrying the retired form at banner
    position is REFUSED even if it also carries a lawful one, because that is
    a half-migrated file and the two conventions must not both run."""
    if RETIRED_RE.search(head):
        return None, "the retired em-dash STATUS banner (ruled out 2026-09-03)"
    m = BANNER_RE.search(head)
    if m:
        return m.group(1), None
    return None, "no STATUS banner"


_fails = []


def check(ok, what, got=""):
    print(("  ok   " if ok else "  FAIL ") + what + ("" if ok else f": {got}"))
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

    retired = 0            # COUNT of documents refused for the old banner
    for p in docs:
        head = "\n".join(p.read_text(encoding="utf-8").split("\n")[:WITHIN_LINES])
        kind, fault = banner(head)
        if kind is None:
            retired += 1 if "retired" in fault else 0
            check(False, f"{p.name} declares a status in its first {WITHIN_LINES} lines",
                  fault)
            continue
        seen[kind] += 1

        if kind == "LOG":
            # A log without its date is the exact trap this file exists for.
            dated = LOG_DATE_RE.search(head)
            check(bool(dated), f"{p.name}: LOG entry carries its date", "undated LOG")
            check("NOT CURRENT" in head,
                  f"{p.name}: LOG entry says it is not current")
        if kind == "LIVE":
            # A live doc that has not been verified is just a log nobody
            # relabelled, which is how this went wrong the first time.
            check(bool(re.search(r"verified \d{4}-\d{2}-\d{2}", head)),
                  f"{p.name}: LIVE doc carries a verified date")

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
        head = "\n".join(p2.read_text(encoding="utf-8").split("\n")[:WITHIN_LINES])
        if banner(head)[0] != "LIVE":
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
        reference = "reference" in head
        if not reference:
            check(len(body) <= 400,
                  f"{p2.name} — a live plan stays scannable (<=400 lines)",
                  f"{len(body)} lines — mark it `reference` if it is a specification")
    # The roadmap is the tiebreak and has to say so, because two docs
    # disagreeing is the normal state of a project this size.
    road = (DOCS / "roadmap.md").read_text(encoding="utf-8")[:600]
    check("this wins" in road or "wins" in road,
          "roadmap.md claims precedence over other docs")

    # THE UNWALKED SET, NAMED. "117/117 clean" reads as full coverage of the
    # project's documents and is nothing of the kind: this checker's root is
    # game-design/ alone, and since the v2 respec landed there are two more
    # markdown trees it has never opened. Saying so out loud costs three lines
    # and stops a clean result being read as a claim about documents nobody
    # examined. Widening the scope is a DECISION, not a tidy-up: the v2
    # package carries its own conventions and would go red on this one.
    root = DOCS.parent
    unwalked = []
    for other in ("production", "ledger-v2", "legacy"):
        d = root / other
        if d.is_dir():
            unwalked.append((other, sum(1 for _ in d.rglob("*.md"))))
    if unwalked:
        print("\nNOT WALKED (this checker's root is game-design/ only): " +
              ", ".join(f"{n}/ {c} doc(s)" for n, c in unwalked) +
              " — those trees carry the v2 conventions and are not checked here.")

    # THE BANNER FIXTURES RUN ON EVERY RUN, not behind a flag. A selftest
    # nobody runs is rule 6 wearing a lab coat, and what these two fixtures
    # guard is SILENT: the day the accepting pattern stops matching, every
    # document goes red at once and reads as 135 broken documents; the day the
    # refusal stops firing, the retired form comes back one file at a time and
    # nothing says a word. They are pure string work and cost no file read.
    fx_pass, fx_fail, fx_lines = banner_fixtures()
    for line in fx_lines:
        print(line)
    if fx_fail:
        check(False, "the banner fixtures agree with this checker",
              f"{fx_fail} of {fx_pass + fx_fail} fixture(s) disagreed")

    print(f"\n  banner form: {seen['LIVE'] + seen['SPEC'] + seen['LOG']} of "
          f"{len(docs)} document(s) carry the ruled colon banner, {retired} "
          f"carry the retired em-dash form (ruled out 2026-09-03), "
          f"{fx_pass}/{fx_pass + fx_fail} synthetic fixture(s) agreed")

    print(f"\n{len(docs) - len(_fails)}/{len(docs)} clean under game-design/"
          if not _fails else f"\n{len(_fails)} problem(s)")
    return 1 if _fails else 0


# ------------------------------------------------------------------- fixtures

# ACCEPTING FIRST, and the accepting fixture that matters most is the LIVE
# CORPUS: `main()` walks 135 real documents and a checker nothing survives
# would show up there before it showed up here. These synthetic pairs cover
# the two things the corpus cannot: the form that no longer exists anywhere
# (so nothing real can exercise the refusal) and the forms nobody has written
# yet.
BANNER_ACCEPT = [
    ("bold colon banner", "> **STATUS: LIVE, verified 2026-09-03.**", "LIVE"),
    ("plain colon banner, what two roles wrote unprompted",
     "STATUS: LOG, 2026-09-03. NOT CURRENT.", "LOG"),
    ("spec banner", "**STATUS: SPEC, 2026-08-25.**", "SPEC"),
    ("a lawful banner beside an inline QUOTATION of the retired form",
     "> **STATUS: LOG, 2026-09-02. NOT CURRENT.**\nIt matched "
     "`\\*\\*STATUS ... LOG` once.", "LOG"),
]
# The rejecting fixtures are synthetic and none of them is a real document:
# a rejecting fixture pinned to a real file breaks the day somebody fixes the
# file, which is the trap of making the work break the tool.
BANNER_REJECT = [
    ("the retired em-dash form", "> **STATUS \u2014 LIVE, verified 2026-09-03.**",
     "retired"),
    ("the retired form with no bold marks", "STATUS \u2014 SPEC, 2026-08-25.",
     "retired"),
    ("a half-migrated file carrying BOTH forms",
     "> **STATUS: LIVE, verified 2026-09-03.**\n> **STATUS \u2014 LIVE.**",
     "retired"),
    ("no banner at all", "# A document with a title and nothing else",
     "no STATUS banner"),
]


def banner_fixtures():
    """(passed, failed, lines). PURE: no file is read, so this is cheap enough
    to run on every invocation."""
    passed, failed, lines = 0, 0, []
    for name, text, want in BANNER_ACCEPT:
        kind, fault = banner(text)
        if kind == want:
            passed += 1
        else:
            failed += 1
            lines.append(f"  FAIL fixture (accepting) {name}: got "
                         f"{kind!r}/{fault!r}, wanted {want}")
    for name, text, want in BANNER_REJECT:
        kind, fault = banner(text)
        if kind is None and fault and want in fault:
            passed += 1
        else:
            failed += 1
            lines.append(f"  FAIL fixture (rejecting) {name}: got "
                         f"{kind!r}/{fault!r}, wanted a fault naming {want!r}")
    return passed, failed, lines


def selftest():
    """The verbose form of the fixtures above, ACCEPTING CASE FIRST."""
    print("docs-check --selftest: ACCEPTING CASES FIRST\n")
    bad = 0
    for name, text, want in BANNER_ACCEPT:
        kind, fault = banner(text)
        good = kind == want
        bad += 0 if good else 1
        print(("  ok   " if good else "  FAIL ") +
              f"{name}: {kind or fault}")
    print("\n  THE RETIRED FORM, refused, and one fixture with no banner:\n")
    for name, text, want in BANNER_REJECT:
        kind, fault = banner(text)
        good = kind is None and fault and want in fault
        bad += 0 if good else 1
        print(("  ok   " if good else "  FAIL ") +
              f"{name}: {fault or ('accepted as ' + str(kind))}")
    n = len(BANNER_ACCEPT) + len(BANNER_REJECT)
    print(f"\ndocs-check --selftest: {'PASS' if not bad else 'FAILED'}. "
          f"{n - bad} passed, {bad} failed, {len(BANNER_ACCEPT)} accepting "
          f"fixture(s), {len(BANNER_REJECT)} rejecting fixture(s). The live "
          f"corpus is the other accepting fixture and is walked by a plain "
          f"run.")
    return 0 if not bad else 3


if __name__ == "__main__":
    # A correct run that ends in a BrokenPipeError traceback costs twenty
    # minutes before anybody notices it worked.
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    _ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    _ap.add_argument("--selftest", action="store_true")
    sys.exit(selftest() if _ap.parse_args().selftest else main())
