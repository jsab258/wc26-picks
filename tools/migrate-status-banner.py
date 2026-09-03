#!/usr/bin/env python3
"""THE STATUS BANNER, FROM THE EM-DASH FORM TO THE COLON FORM, ONCE, BY SCRIPT.

    python3 tools/migrate-status-banner.py --dry-run     # print, change nothing
    python3 tools/migrate-status-banner.py               # rewrite in place
    python3 tools/migrate-status-banner.py --selftest    # accepting case FIRST

WHY IT EXISTS. `tools/docs-check.py` demanded `**STATUS - LIVE` with an
EM-DASH while constitution law 11 bans em-dashes anywhere, so every document
in `game-design/` carried a deliberate law violation BECAUSE THE CHECKER
DEMANDED IT. Two separate roles lost time to it on 2026-09-03: the resident
wrote the colon form and was rejected, and an hour later the director's own
ruling file was rejected the same way. Jafar ruled the colon form in and the
em-dash form OUT.

WHY A SCRIPT AND NOT A HAND EDIT. 135 documents. A hand edit is a half
migration with no record of which half, and the checker goes red on whatever
was missed with no way to tell "missed" from "written wrong today". This runs
once, prints both numbers, and is IDEMPOTENT: a second run changes 0 files and
says so against the same denominator.

WHAT IT WILL NOT TOUCH, said out loud rather than skipped.
  - Only a banner AT THE START OF A LINE (after an optional blockquote mark or
    heading hashes). An inline mention inside prose is usually a QUOTE of the
    old form in a dated report, and rewriting a quotation makes a historical
    document lie about what it quoted. Seven of those exist under
    `game-design/` and this leaves every one of them alone.
  - Only the roots given (default `game-design`). `legacy/` carries three
    banners and is deliberately NOT walked: it is superseded text that
    `docs-check.py` does not read, and the formatting law corrects old text
    opportunistically rather than by sweep. The unwalked roots are NAMED in
    the report so a clean number cannot read as full coverage.

EXIT CODES, distinct per outcome. 0 done (including "already migrated,
0 changed"). 1 a file could not be read or written, and it is named.
2 nothing measured: no root existed, or no markdown file was found under any
of them, which is not a pass. 3 the selftest failed.
"""
import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

# THE OLD FORM, AT BANNER POSITION ONLY: line start, an optional blockquote
# mark, optional heading hashes, optional bold marks. The em-dash is the
# character this migration exists to remove; the bold marks are not em-dashes
# and are carried through untouched.
#
# THE BOLD MARKS ARE OPTIONAL ON BOTH SIDES. `docs-check.py` accepts
# `STATUS: LIVE` without them, so the retired form must be recognised without
# them too, or one punctuation stays legal in exactly the shape nobody
# migrated. Found by the checker's own rejecting fixture rather than by
# reading: the first version of this regex required `**` and the fixture
# `STATUS - SPEC` came back as "no banner" instead of "the retired form".
OLD_RE = re.compile(
    r"(?m)^([ \t]*(?:>[ \t]*)?(?:#+[ \t]*)?)(\*\*)?STATUS[ \t]*—[ \t]*")

# IMPORTED BY tools/docs-check.py AS ITS DEFINITION OF THE RETIRED FORM.
# Deleting this file turns docs-check red (exit 4) and verify.py with it;
# queue 075 moves the definition to the checker and inverts the import.

DEFAULT_ROOTS = ("game-design",)
NOT_WALKED = ("legacy", "production", "ledger-v2")


def migrate_text(text):
    """(new_text, hits). PURE, and the only place the rewrite is defined, so
    the selftest drives exactly the code the sweep runs."""
    new, hits = OLD_RE.subn(
        lambda m: m.group(1) + (m.group(2) or "") + "STATUS: ", text)
    return new, hits


def walk(roots):
    out = []
    for r in roots:
        p = pathlib.Path(r)
        if not p.is_absolute():
            p = REPO / r
        if p.is_dir():
            out.extend(sorted(p.rglob("*.md")))
    return out


def sweep(roots, dry_run=False):
    files = walk(roots)
    changed, hits, errors = [], 0, []
    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception as e:                                   # noqa: BLE001
            errors.append("%s unreadable: %s" % (p, e))
            continue
        new, n = migrate_text(text)
        if n:
            hits += n
            changed.append(p)
            if not dry_run:
                try:
                    p.write_text(new, encoding="utf-8")
                except Exception as e:                           # noqa: BLE001
                    errors.append("%s unwritable: %s" % (p, e))
    return files, changed, hits, errors


def emdashes(roots):
    """Total em-dash CHARACTERS under the roots, over the same file set the
    sweep walks. The before/after pair is one reading taken twice, so it is
    counted here rather than by a shell command whose file set could differ
    from the sweep's by a glob."""
    total, files = 0, walk(roots)
    for p in files:
        try:
            total += p.read_text(encoding="utf-8").count("—")
        except Exception:                                        # noqa: BLE001
            pass
    return total, len(files)


# ------------------------------------------------------------------- selftest

# ACCEPTING FIRST: text this migration must leave EXACTLY as it found it. The
# expensive failure is a sweep that rewrites everything it touches, and that
# failure is invisible in a diff of 135 files.
KEEP = [
    ("already migrated", "> **STATUS: LIVE, verified 2026-09-03.**\n"),
    ("a plain colon banner with no bold",
     "STATUS: LOG, 2026-09-03. NOT CURRENT.\n"),
    ("an inline quotation of the old form",
     "`tools/docs-check.py` matches `\\*\\*STATUS — LOG, ...`. That is\n"),
    ("an em-dash in ordinary prose",
     "The street — wet, overcast — paints properly now.\n"),
    ("a bolded word that is not the banner",
     "**STATUSES** — all of them are fine.\n"),
]
FLIP = [
    ("blockquote banner",
     "> **STATUS — LIVE, verified 2026-08-21.**\n",
     "> **STATUS: LIVE, verified 2026-08-21.**\n"),
    ("bare banner",
     "**STATUS — SPEC, 2026-08-25.**\n",
     "**STATUS: SPEC, 2026-08-25.**\n"),
    ("log banner keeps its date and its NOT CURRENT",
     "> **STATUS — LOG, 2026-07-30. NOT CURRENT.** A record of\n",
     "> **STATUS: LOG, 2026-07-30. NOT CURRENT.** A record of\n"),
    ("heading banner",
     "## **STATUS — LIVE, verified 2026-08-04.**\n",
     "## **STATUS: LIVE, verified 2026-08-04.**\n"),
    ("banner with no bold marks at all",
     "STATUS — LIVE, verified 2026-08-21.\n",
     "STATUS: LIVE, verified 2026-08-21.\n"),
]


def selftest():
    passed, failed = 0, []

    def ok(name, cond, got=""):
        nonlocal passed
        if cond:
            passed += 1
            print("  ok   %s" % name)
        else:
            failed.append(name)
            print("  FAIL %s\n         got: %r" % (name, got))

    print("migrate-status-banner --selftest: ACCEPTING CASES FIRST (text this")
    print("sweep must leave byte-identical)\n")
    for name, text in KEEP:
        new, n = migrate_text(text)
        ok("%-38s untouched" % name, new == text and n == 0, (new, n))

    print("\n  THE FORM BEING RETIRED, one fixture per banner position:\n")
    for name, before, after in FLIP:
        new, n = migrate_text(before)
        ok("%-38s rewritten" % name, new == after and n == 1, (new, n))

    print("\n  IDEMPOTENCE, which is the whole claim of a once-run script:\n")
    twice, n2 = migrate_text(migrate_text(FLIP[0][1])[0])
    ok("a second pass changes nothing", twice == FLIP[0][2] and n2 == 0,
       (twice, n2))
    joined = "".join(b for _, b, _ in FLIP)
    _, nj = migrate_text(joined)
    ok("%d banners in one file count as %d hits (got %d)"
       % (len(FLIP), len(FLIP), nj), nj == len(FLIP), nj)

    print("\nmigrate-status-banner --selftest: %s. %d passed, %d failed, "
          "%d accepting fixture(s), %d rejecting fixture(s)"
          % ("PASS" if not failed else "FAILED", passed, len(failed),
             len(KEEP), len(FLIP)))
    for f in failed:
        print("  " + f)
    return 0 if not failed else 3


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("roots", nargs="*", default=list(DEFAULT_ROOTS))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    roots = args.roots or list(DEFAULT_ROOTS)
    before, _ = emdashes(roots)
    files, changed, hits, errors = sweep(roots, args.dry_run)
    after, _ = emdashes(roots)

    print("migrate-status-banner: roots=%s dryRun=%s"
          % ("/".join(roots), "yes" if args.dry_run else "no"))
    if not files:
        print("  nothing measured: no markdown file under %s" % "/".join(roots))
        return 2
    print("  %d file(s) changed of %d markdown file(s) examined, %d banner(s) "
          "rewritten" % (len(changed), len(files), hits))
    # THE PAIRED READING, one entry carrying both moments: the em-dash total
    # over the SAME file set, before and after this sweep, in this run.
    print("  em-dashes under %s: %d before, %d after (a dry run leaves them "
          "equal by construction)" % ("/".join(roots), before, after))
    for p in changed[:5]:
        print("    changed %s" % p.relative_to(REPO))
    if len(changed) > 5:
        print("    (+%d more not shown of %d)" % (len(changed) - 5,
                                                  len(changed)))
    missing = [r for r in NOT_WALKED if (REPO / r).is_dir()
               and r not in roots]
    if missing:
        print("  NOT WALKED, named rather than left implied: %s. Those trees "
              "are not read by docs-check.py and old text is corrected "
              "opportunistically, never by sweep." % ", ".join(missing))
    if errors:
        print("  %d file(s) failed:" % len(errors))
        for e in errors[:3]:
            print("    " + e)
        if len(errors) > 3:
            print("    (+%d more not shown of %d)" % (len(errors) - 3,
                                                      len(errors)))
        return 1
    return 0


if __name__ == "__main__":
    # A correct run that ends in a BrokenPipeError traceback costs twenty
    # minutes before anybody notices it worked.
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    sys.exit(main())
