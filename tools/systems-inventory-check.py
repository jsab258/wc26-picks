#!/usr/bin/env python3
"""The player-facing systems inventory, and the check that it is not fiction.

WHAT THIS IS. `production/systems-inventory.json` is Jafar's item 4 of the
2026-09-05 standing order as DATA: one entry per player-facing system, with
the six fields he named (name, area, status, class, phase, blocker) plus a
seventh the director kept, `evidence`, because a status word nobody can check
is the fault this project keeps repeating. 37 props and 14 decals were counted
as progress while `grep -c "base-mesh|BaseMesh"` returned 0 in both street
scripts, so here "exists" means a path that resolves and, where a token is
given, a token that is IN that path. The check proves it on every run.

WHY JSON, and not YAML, TOML, a table or key=value lines. Two tools consume
this file and neither may guess: queue 099 renders the map view from it and
queue 100 folds the phase field into the roadmap. JSON parses with the Python
standard library on both the container and the PC runner, it fails LOUDLY on a
malformed file rather than half-parsing it, it nests the evidence list without
a quoting convention somebody has to remember, and it embeds into the map
page's HTML with zero external references (queue 099's own bar). YAML was the
near miss and was rejected on one concrete hazard: the blocker field's legal
value `none` is a string in JSON and `no`/`yes`/`on` are booleans in YAML 1.1,
so a blocker word would change type on the way in. A flat key=value channel
cannot carry the evidence list at all.

THE DENOMINATOR IS NOT SELF-SUPPLIED. Coverage is measured against the 27
names pinned in `production/queue/098-*.md`, which copied them from the
standing order and recorded the count discrepancy (the resident's brief said
28; splitting Jafar's sentence on its commas gives 27). Reading the names from
the inventory itself would make `covered=27/27` a tautology: the file would
grade its own homework. A name with no entry is printed BY NAME.

WHAT THE NUMBERS ARE STATISTICS OF. Everything printed here is a WHOLE-FILE
CENSUS at the moment of the run: counts over all entries, not a sample, not a
peak, not a running total. `covered=N/27` is a set intersection; `resolved=N/M`
is a count of evidence references whose path (and token, when given) was found
on disk in this checkout, with M the number examined in the same pass.

EXIT CODES, distinct per outcome so a caller can tell them apart:
  0  accepted
  1  refused: at least one problem, every problem printed
  2  nothing measured: the inventory is missing, unreadable or empty
  3  the tool could not run (bad argument, no names file)

SELFTEST: `--selftest` runs the accepting case FIRST (the live inventory, the
live queue file: the codebase is the accepting fixture) and then four planted
rejecting fixtures, each synthetic, so that doing the work this tool asks for
can never break the tool.
"""

import argparse
import json
import os
import re
import signal
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The fixed sets, ruled in production/queue/098. Consumers (099, 100) import
# these rather than writing a second copy: one implementation per idea.
AREAS = ("moat", "world", "player-facing", "content", "studio")
STATUSES = ("exists", "partial", "absent")
CLASSES = ("cheap-to-author", "taste-bound", "moat-adjacent")
PHASES = ("R", "0", "1", "2", "3", "4", "5", "6")
REQUIRED = ("name", "area", "status", "class", "phase", "blocker")
EVIDENCE_STATUSES = ("exists", "partial")

INVENTORY = os.path.join(ROOT, "production", "systems-inventory.json")
# The names file may move to the done/ folder when the item closes, so both
# locations are tried and the one used is printed.
ORDER_CANDIDATES = (
    os.path.join(ROOT, "production", "queue",
                 "098-the-player-facing-systems-inventory-as-data.md"),
    os.path.join(ROOT, "production", "queue", "done",
                 "098-the-player-facing-systems-inventory-as-data.md"),
)
EXPECTED_NAMES = 27          # Jafar's sentence, split on commas. Not a target.
CAP = 10                     # every cap announces itself when it bites

NOTHING = "nothing measured"


def rel(path):
    """Repo-relative when it IS in the repo, absolute otherwise: a printed
    `../../../tmp/x` reads as a repo path to a grep and is not one."""
    p = os.path.abspath(path)
    if p == ROOT or p.startswith(ROOT + os.sep):
        return os.path.relpath(p, ROOT).replace(os.sep, "/")
    return p.replace(os.sep, "/")


def capped(items):
    """Print at most CAP items and SAY SO when the cap bites."""
    shown = [str(i) for i in items[:CAP]]
    if len(items) > CAP:
        shown.append("(+%d more not shown)" % (len(items) - CAP))
    return shown


# ---------------------------------------------------------------- the names

def order_names(path=None):
    """The 27 names, parsed from the numbered list in the queue file.

    Returns (names, path_used, error). Never re-derives them from NOW.md:
    the queue file is the pinned copy and the only place a director changes
    the count.
    """
    paths = [path] if path else list(ORDER_CANDIDATES)
    for p in paths:
        if p and os.path.exists(p):
            names, seen_heading = [], False
            for line in open(p, encoding="utf-8"):
                if line.startswith("## "):
                    # The numbered list lives under the names heading only.
                    seen_heading = line.startswith("## The names")
                    continue
                m = re.match(r"^\s*(\d+)\.\s+(\S.*?)\s*$", line)
                if seen_heading and m:
                    names.append(m.group(2))
            return names, p, None
    return [], None, "no names file at " + " or ".join(rel(p) for p in paths)


# ------------------------------------------------------------- loading data

def load(path):
    """Returns (entries, error). An unreadable or empty file is an ERROR and
    never an empty success: a zero with no denominator cannot tell nothing
    from fine."""
    if not os.path.exists(path):
        return None, "file does not exist: " + rel(path)
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (ValueError, OSError) as exc:
        return None, "unreadable (%s)" % str(exc).replace(" ", "_")[:80]
    if isinstance(doc, list):
        entries = doc
    elif isinstance(doc, dict):
        entries = doc.get("systems")
    else:
        return None, "top level is neither a list nor an object"
    if entries is None:
        return None, "no 'systems' key"
    if not isinstance(entries, list):
        return None, "'systems' is not a list"
    return entries, None


# --------------------------------------------------------------- the checks

def check_evidence_ref(ref):
    """One evidence reference: 'path' or 'path#token'. Returns (ok, why).

    The token half is what catches BUILT IS NOT RUNNING: a file existing
    proves a file exists, and a token inside it is the nearest thing to a
    call site this tool can prove without a compiler.
    """
    if not isinstance(ref, str) or not ref.strip():
        return False, "empty"
    if any(c.isspace() for c in ref):
        return False, "contains_whitespace"
    path, _, token = ref.partition("#")
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return False, "path_missing"
    if token:
        if os.path.isdir(full):
            return False, "token_on_a_directory"
        try:
            with open(full, encoding="utf-8", errors="replace") as fh:
                if token not in fh.read():
                    return False, "token_absent"
        except OSError:
            return False, "unreadable"
    return True, "ok"


def validate(entries, names):
    """Whole-file census. Returns (problems, stats). Every entry is examined;
    `checks` is the denominator for `problems`."""
    problems, checks = [], 0
    seen = {}
    ev_refs = ev_ok = 0
    need_ev = 0

    for i, e in enumerate(entries):
        tag = "entry[%d]" % i
        if not isinstance(e, dict):
            problems.append("%s is not an object" % tag)
            checks += 1
            continue
        name = e.get("name")
        if isinstance(name, str) and name:
            tag = "'%s'" % name
        for field in REQUIRED:
            checks += 1
            if field not in e or e[field] in (None, ""):
                problems.append("%s missing required field '%s'" % (tag, field))
        checks += 1
        if isinstance(name, str) and name in seen:
            problems.append("%s duplicate name (also entry[%d])" % (tag, seen[name]))
        elif isinstance(name, str):
            seen[name] = i

        for field, allowed in (("area", AREAS), ("status", STATUSES),
                               ("class", CLASSES), ("phase", PHASES)):
            checks += 1
            val = e.get(field)
            if val is not None and str(val) not in allowed:
                problems.append("%s %s=%r is not one of %s"
                                % (tag, field, val, "|".join(allowed)))

        checks += 1
        blocker = e.get("blocker")
        if isinstance(blocker, str) and any(c.isspace() for c in blocker):
            problems.append("%s blocker=%r contains whitespace; use / and .."
                            % (tag, blocker))
        checks += 1
        if isinstance(blocker, str) and blocker.startswith("queue-"):
            num = blocker[len("queue-"):]
            hits = []
            for d in ("queue", "queue/done"):
                folder = os.path.join(ROOT, "production", d)
                if os.path.isdir(folder):
                    hits += [f for f in os.listdir(folder) if f.startswith(num + "-")]
            if not hits:
                problems.append("%s blocker=%s names no queue file" % (tag, blocker))
        checks += 1
        if isinstance(blocker, str) and re.match(r"^D\d+$", blocker):
            reg = os.path.join(ROOT, "ledger-v2", "respec", "decision-register")
            hits = [f for f in os.listdir(reg)] if os.path.isdir(reg) else []
            if not any(f.startswith(blocker + "-") for f in hits):
                problems.append("%s blocker=%s names no decision record in %s"
                                % (tag, blocker, rel(reg)))

        status = e.get("status")
        ev = e.get("evidence", [])
        checks += 1
        if not isinstance(ev, list):
            problems.append("%s evidence is not a list" % tag)
            ev = []
        if status in EVIDENCE_STATUSES:
            need_ev += 1
            if not ev:
                problems.append("%s status=%s with no evidence; the honest "
                                "status is absent" % (tag, status))
        elif status == "absent" and ev:
            problems.append("%s status=absent must carry no evidence" % tag)
        for ref in ev:
            ev_refs += 1
            checks += 1
            ok, why = check_evidence_ref(ref)
            if ok:
                ev_ok += 1
            else:
                problems.append("%s evidence %r does not resolve (%s)"
                                % (tag, ref, why))

        note = e.get("note")
        checks += 1
        if note is not None and (not isinstance(note, str) or "\n" in note):
            problems.append("%s note must be a single-line string" % tag)

    covered = [n for n in names if n in seen]
    missing = [n for n in names if n not in seen]
    extra = [n for n in seen if n not in names]

    stats = {
        "checks": checks,
        "covered": covered,
        "missing": missing,
        "extra": sorted(extra),
        "evRefs": ev_refs,
        "evOk": ev_ok,
        "needEv": need_ev,
        "tally": {
            "status": tally(entries, "status", STATUSES),
            "area": tally(entries, "area", AREAS),
            "class": tally(entries, "class", CLASSES),
            "phase": tally(entries, "phase", PHASES),
        },
    }
    return problems, stats


def tally(entries, field, allowed):
    counts = {k: 0 for k in allowed}
    for e in entries:
        if isinstance(e, dict):
            v = str(e.get(field))
            if v in counts:
                counts[v] += 1
    return counts


def fmt_tally(counts, total):
    """Every count ships the denominator it was drawn from."""
    return " ".join("%s=%d/%d" % (k, v, total) for k, v in counts.items())


# ---------------------------------------------------------------- reporting

def run(path, names_path=None, out=sys.stdout, emit=False):
    """Validate and report. With emit=True the report goes to stderr and the
    VALIDATED entries go to stdout as JSON, so queue 099's renderer and queue
    100's fold consume this file through the check rather than around it: one
    parser, one set of fixed values, one refusal path. Exit code is unchanged,
    so a refusal cannot be rendered as a page."""
    if emit:
        out = sys.stderr
    names, used, err = order_names(names_path)
    if err:
        print("systems-inventory: CANNOT RUN, %s" % err, file=out)
        return 3
    if len(names) != EXPECTED_NAMES:
        print("systems-inventory: CANNOT RUN, namesFromOrder=%d expected=%d "
              "in %s; the count is Jafar's or a director's to change, never a "
              "builder's" % (len(names), EXPECTED_NAMES, rel(used)), file=out)
        return 3

    entries, err = load(path)
    if err is not None or not entries:
        why = err or "zero entries"
        print("systems-inventory: %s entries=0 namesFromOrder=%d covered=0/%d "
              "reason=%s file=%s"
              % (NOTHING, len(names), len(names), why.replace(" ", "_"),
                 rel(path)), file=out)
        return 2

    problems, st = validate(entries, names)
    n = len(entries)
    print("systems-inventory: entries=%d namesFromOrder=%d covered=%d/%d "
          "file=%s order=%s"
          % (n, len(names), len(st["covered"]), len(names), rel(path), rel(used)),
          file=out)
    # Whole-run censuses, all four on their own lines with their denominator.
    print("  byStatus: " + fmt_tally(st["tally"]["status"], n), file=out)
    print("  byClass:  " + fmt_tally(st["tally"]["class"], n), file=out)
    print("  byArea:   " + fmt_tally(st["tally"]["area"], n), file=out)
    print("  byPhase:  " + fmt_tally(st["tally"]["phase"], n), file=out)
    absent = st["tally"]["status"]["absent"]
    print("  evidence: refs=%d resolved=%d/%d entriesNeedingEvidence=%d/%d "
          "absentCarryNone=%d (%s for those)"
          % (st["evRefs"], st["evOk"], st["evRefs"], st["needEv"], n, absent,
             NOTHING), file=out)
    if st["missing"]:
        print("  UNCOVERED %d/%d names have no entry: %s"
              % (len(st["missing"]), len(names),
                 ", ".join(capped(st["missing"]))), file=out)
    else:
        print("  uncovered: 0/%d names have no entry" % len(names), file=out)
    print("  beyondTheNamedNames: %d (%s)"
          % (len(st["extra"]), ", ".join(capped(st["extra"])) if st["extra"]
             else "none"), file=out)

    if problems:
        print("  REFUSED problems=%d/checks=%d" % (len(problems), st["checks"]),
              file=out)
        for line in capped(problems):
            print("    - " + line, file=out)
        return 1
    print("  accepted problems=0/checks=%d" % st["checks"], file=out)
    if emit:
        json.dump(entries, sys.stdout, indent=1)
        sys.stdout.write("\n")
    return 0


# ----------------------------------------------------------------- selftest

GOOD = {
    "name": "planted", "area": "studio", "status": "absent",
    "class": "cheap-to-author", "phase": "0", "blocker": "none",
}


def _fixture(tmp, entries):
    p = os.path.join(tmp, "fixture.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump({"systems": entries}, fh)
    return p


def selftest():
    """Accepting case FIRST, then the planted refusals. The accepting fixture
    is the LIVE inventory and the LIVE queue file, so doing the work this tool
    asks for cannot break the tool; every rejecting fixture is synthetic."""
    rungs, ok = [], True

    print("== rung 1 ACCEPTING: the live inventory and the live names file ==")
    code = run(INVENTORY)
    rungs.append(("accept/live-inventory", 0, code))

    with tempfile.TemporaryDirectory() as tmp:
        planted = [
            ("refuse/exists-with-unresolvable-evidence", 1, [dict(
                GOOD, name="planted-ghost", status="exists",
                evidence=["ledger/Assets/Scripts/Game/NoSuchFile.cs"])]),
            ("refuse/exists-with-token-that-exists-nowhere", 1, [dict(
                GOOD, name="planted-token", status="partial",
                evidence=["ledger/Assets/Scripts/Game/GameController.cs"
                          "#ZzQqSyntheticTokenThatExistsNowhere"])]),
            ("refuse/area-outside-the-five", 1, [dict(
                GOOD, name="planted-area", area="vibes")]),
            ("refuse/missing-required-field", 1,
             [{k: v for k, v in GOOD.items() if k != "phase"}]),
            ("refuse/exists-with-no-evidence-at-all", 1, [dict(
                GOOD, name="planted-bare", status="exists")]),
            ("refuse/blocker-names-no-decision-record", 1, [dict(
                GOOD, name="planted-blocker", blocker="D9999")]),
            ("refuse/duplicate-name", 1, [dict(GOOD), dict(GOOD)]),
        ]
        for label, want, entries in planted:
            print("\n== rung: %s (expect exit %d) ==" % (label, want))
            code = run(_fixture(tmp, entries))
            rungs.append((label, want, code))

        print("\n== rung: nothing-measured/empty-file (expect exit 2) ==")
        code = run(_fixture(tmp, []))
        rungs.append(("nothing-measured/empty-file", 2, code))

    print("\n== selftest done ==")
    for label, want, got in rungs:
        good = want == got
        ok = ok and good
        print("  %-45s want=%d got=%d %s" % (label, want, got,
                                             "PASS" if good else "FAIL"))
    passed = sum(1 for l, w, g in rungs if w == g)
    print("  selftest: passed=%d/%d rungs (accepting first)" % (passed, len(rungs)))
    return 0 if ok else 1


def main():
    # Fail readable: a report ending in a stack trace after a correct run
    # costs twenty minutes before anyone notices it worked.
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", default=INVENTORY, help="inventory to validate")
    ap.add_argument("--names", default=None, help="queue file holding the names")
    ap.add_argument("--selftest", action="store_true",
                    help="accepting case then the planted refusals")
    ap.add_argument("--emit-json", action="store_true",
                    help="report on stderr, validated entries on stdout "
                         "(for queue 099's map view and queue 100's fold)")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return run(args.file, args.names, emit=args.emit_json)


if __name__ == "__main__":
    sys.exit(main())
