#!/usr/bin/env python3
"""The systems inventory, and the check that a TYPED state is attributable.

WHAT THIS IS. `production/systems-inventory.json` is the data behind the
heatmap Jafar approved on 31 August: every system a tile, in five areas, in
his order, coloured exists, partial or absent. One entry per system with the
six fields he named (name, area, status, class, phase, blocker), a one-line
note he reads, an optional evidence list, and the two attribution fields the
contract below turns on.

THE CONTRACT CHANGED ON 2026-09-09, AND THIS TOOL CHANGED WITH IT. Jafar:
"ON THIS PAGE, TYPED IS THE STANDARD: a director's overview is a human's
judgement of state, ruled by me and updated by rulings; measured evidence sits
one tap below and never on the first screen."

WHAT THE OLD RULE WAS AND WHY IT WAS NOT STUPID. Until that ruling, `status`
was "evidenced, never guessed": every `exists` and every `partial` had to carry
a path that resolves in this checkout, and an entry without one was REFUSED.
It existed because of a real incident: 37 props and 14 decals were counted as
progress while `grep -c "base-mesh|BaseMesh"` returned 0 in both street
scripts. A tile painted green on a hope is the fault this project keeps
repeating, and that risk does not go away because the contract moved.

WHAT REPLACES IT, AND IT IS THE WHOLE POINT OF THIS FILE NOW. A typed state is
ATTRIBUTABLE. Every entry carries `typedBy` (role/name, role one of jafar,
director, builder, producer) and `typedOn` (the date it was last typed), so a
wrong tile is somebody's wrong judgement with a date on it rather than an
anonymous colour. Evidence stays where it exists and becomes provenance for the
audit view one tap down: still checked for SHAPE where present, never required,
and never again the thing that licenses the state.

TWO FIELDS RULED IN ON 2026-09-09, and the ruling is
`game-design/decision-2026-09-09-ruling-typed-systems-inventory.md` section 4.

`where` is WHICH CODEBASE THIS TILE'S COLOUR IS ABOUT: one of
core-csharp | ue-probe | both | repo, REQUIRED when `status` is exists or
partial and FORBIDDEN when it is absent. The asymmetry is the one `evidence`
already carries and the logic is the same: a system that is nowhere cannot be
somewhere, and a tile naming an engine for a thing that does not exist is a
claim with a location on it. `both` is EARNED by a golden parity row or a
printed key on each side and never by a ported header, which is the
type-the-lower-state-when-unsure rule the data already carries. The field
exists because 26 green tiles green in a codebase Jafar is not looking at, with
D1 still open, is the page that flatters.

`short` is the optional display label a tile uses when the name does not fit:
a non-empty single line, no edge whitespace, STRICTLY shorter than `name`, and
unique across the file. NO LENGTH BOUND IS SET HERE and that is deliberate: no
rendered width has been measured at 360px in any session, so the tool prints
the character series (short and name, min..max/median over n) and a later
session sets a trigger from a pixel measurement instead of from a gap in a
character distribution. The page shows the full name WRAPPED when no `short` is
typed, never clipped.

WHY JSON, unchanged from the first version. Two tools consume this file and
neither may guess: the map view renders it and the roadmap fold reads the phase
field. JSON parses with the Python standard library on both the container and
the PC runner, fails LOUDLY on a malformed file rather than half-parsing it,
nests the evidence list without a quoting convention somebody has to remember,
and embeds into the map page with zero external references. YAML was the near
miss and was rejected on one concrete hazard: the blocker value `none` is a
string in JSON and `no`/`yes`/`on` are booleans in YAML 1.1, so a blocker word
would change type on the way in. A flat key=value channel cannot carry the
evidence list at all.

THE DENOMINATOR IS NOT SELF-SUPPLIED. Coverage is measured against the 27 names
pinned in `production/queue/098-*.md`, which copied them from the standing
order and recorded the count discrepancy (the resident's brief said 28;
splitting Jafar's sentence on its commas gives 27). Reading the names from the
inventory itself would make `covered=27/27` a tautology: the file would grade
its own homework. A name with no entry is printed BY NAME. The order says "At
minimum", so the file may hold MORE entries than names and today does.

WHAT THE NUMBERS ARE STATISTICS OF. Everything printed here is a WHOLE-FILE
CENSUS at the moment of the run: counts over all entries, not a sample, not a
peak, not a running total. `covered=N/27` is a set intersection. `resolved=N/M`
counts evidence references whose path (and token, when given) was found on disk
in this checkout, with M the number examined in the same pass. `noteChars` is a
printed series (min, median, max over n notes) and NOT a bound: no length is
enforced, because no length has been measured across enough real runs to set
one. `blockerStale` is likewise a printed series and not a refusal.

EXIT CODES, distinct per outcome so a caller can tell them apart:
  0  accepted
  1  refused: at least one problem, every problem printed
  2  nothing measured: the inventory is missing, unreadable or empty
  3  the tool could not run (bad argument, no names file)

SELFTEST: `--selftest` runs the ACCEPTING CASES FIRST (the live inventory and
the live queue file, because the codebase is the accepting fixture, then a
planted entry typed `exists` with no evidence at all, which the old contract
refused and this one must accept), and then the planted refusals. Every
rejecting fixture is synthetic, so doing the work this tool asks for can never
break the tool.
"""

import argparse
import datetime
import json
import os
import re
import signal
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The fixed sets. Consumers (the map view, the roadmap fold) import these
# rather than writing a second copy: one implementation per idea.
AREAS = ("moat", "world", "player-facing", "content", "studio")
STATUSES = ("exists", "partial", "absent")
CLASSES = ("cheap-to-author", "taste-bound", "moat-adjacent")
PHASES = ("R", "0", "1", "2", "3", "4", "5", "6")
# WHICH CODEBASE A TILE'S COLOUR IS ABOUT, ruled 2026-09-09 section 4b. It is
# in the same fixed-set loop as the four above, so there is one implementation
# of the idea rather than a second copy that drifts.
#   core-csharp  a reading of the C# game under ledger/, and nothing on the
#                Unreal side has been measured for this statement
#   ue-probe     the Unreal probe only
#   both         EARNED by a golden parity row or a printed key on EACH side,
#                never by a ported header
#   repo         files and process, neither engine
WHERES = ("core-csharp", "ue-probe", "both", "repo")
# WHO MAY TYPE A STATE. The judgement is Jafar's and a director's; a builder
# may type one and says so, which is the point of recording the role.
ROLES = ("jafar", "director", "builder", "producer")
# `note` and the two attribution fields are REQUIRED under the typed contract:
# a tile with no words and no owner is the anonymous colour the ruling replaced.
REQUIRED = ("name", "area", "status", "class", "phase", "blocker",
            "typedBy", "typedOn", "note")
SCHEMA = "systems-inventory/v2"

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
    """Returns (doc, entries, error). An unreadable or empty file is an ERROR
    and never an empty success: a zero with no denominator cannot tell nothing
    from fine. The whole doc comes back because the header (schema, areas) is
    load-bearing under the typed contract."""
    if not os.path.exists(path):
        return None, None, "file does not exist: " + rel(path)
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (ValueError, OSError) as exc:
        return None, None, "unreadable (%s)" % str(exc).replace(" ", "_")[:80]
    if isinstance(doc, list):
        entries = doc
    elif isinstance(doc, dict):
        entries = doc.get("systems")
    else:
        return None, None, "top level is neither a list nor an object"
    if entries is None:
        return None, None, "no 'systems' key"
    if not isinstance(entries, list):
        return None, None, "'systems' is not a list"
    return doc, entries, None


# --------------------------------------------------------------- the checks

def check_evidence_ref(ref):
    """One evidence reference: 'path' or 'path#token'. Returns (ok, why).

    PROVENANCE, NOT A LICENCE, since 2026-09-09: this no longer decides whether
    a status may be claimed. It decides whether the audit view one tap down
    shows a reader something real. The token half is what catches BUILT IS NOT
    RUNNING: a file existing proves a file exists, and a token inside it is the
    nearest thing to a call site this tool can prove without a compiler.

    IT IS BRANCH-LOCAL and that is a known blind spot, named in the data's own
    howToRead: work on another branch (the art deliveries on art/atlas-01)
    cannot be cited here at all.
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


def queue_files(num):
    """Every queue file whose name starts with this number, open or done."""
    hits = []
    for d in ("queue", "queue/done"):
        folder = os.path.join(ROOT, "production", d)
        if os.path.isdir(folder):
            hits += [os.path.join(folder, f) for f in os.listdir(folder)
                     if f.startswith(num + "-")]
    return hits


# THE TWO STATUS PARSERS ARE PURE, and they are pure for the reason the
# standing rule gives: measurement arithmetic and string parsing live where the
# tests can reach them. Both were wrong once. The selftest pins each on
# synthetic text, including the exact shape that fooled the first version.
def queue_status_word(text):
    """The first line whose FIRST token is status:, which is the queue row
    law's own shape. Returns the word, upper case, or None."""
    for line in text.splitlines():
        if line.lower().startswith("status:"):
            rest = line.split(":", 1)[1].strip()
            if rest:
                return rest.split()[0].upper().strip(".,;")
    return None


def decision_status_word(text):
    """A decision record's status word. NOT ANCHORED TO LINE START, and that
    was an instrument fault caught by reading this tool's own first series:
    D1's line is "Date: 2026-08-31. Status: OPEN, probe authorized.", so an
    anchored pattern missed it and the series read decisionSettled=33/33 with
    the one OPEN record in the project counted as settled."""
    m = re.search(r"(?i)status[:\s]+([A-Za-z]+)", text)
    return m.group(1).upper() if m else None


def says_landed(text):
    return queue_status_word(text) in ("LANDED", "DONE")


def says_open(text):
    return decision_status_word(text) == "OPEN"


def queue_is_landed(num):
    """True when a queue item's own status line says LANDED or DONE.

    A PRINTED SERIES AND NOT A REFUSAL. A blocker naming a landed item is the
    decay this file exists to show (one entry pointed at queue 046, landed on
    2 September; this rewrite pointed two at items that landed on the 7th and
    the 9th), but no bound is set here: the count prints with its denominator
    and a director decides whether it should ever refuse.
    """
    for p in queue_files(num):
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                return says_landed(fh.read())
        except OSError:
            continue
    return False


def decision_records(ident):
    reg = os.path.join(ROOT, "ledger-v2", "respec", "decision-register")
    if not os.path.isdir(reg):
        return []
    return [os.path.join(reg, f) for f in os.listdir(reg)
            if f.startswith(ident + "-")]


def decision_is_open(ident):
    """True when the record's status line says OPEN. Same deal as above: a
    blocker naming a settled decision is printed, never refused."""
    for p in decision_records(ident):
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                return says_open(fh.read(4000))
        except OSError:
            continue
    return False


def check_header(doc, problems):
    """The schema pin and the areas block. Returns the areas seen.

    THE SCHEMA PIN IS NOT DECORATION: a v1 file has no attribution on any
    entry, so it would pass every other check here while carrying exactly the
    anonymous colours the 2026-09-09 ruling replaced. It must be refused by
    name rather than silently accepted.
    """
    if not isinstance(doc, dict):
        problems.append("top level is a bare list: the typed contract needs a "
                        "header carrying schema=%s and the areas block" % SCHEMA)
        return []
    got = doc.get("schema")
    if got != SCHEMA:
        problems.append("schema=%r is not %r; the typed contract of 2026-09-09 "
                        "requires the header and the attribution fields"
                        % (got, SCHEMA))
    areas = doc.get("areas")
    if not isinstance(areas, list) or not areas:
        problems.append("no 'areas' block: the page renders Jafar's labels "
                        "from it, so the five areas declare their label and "
                        "order here rather than in the renderer")
        return []
    keys, orders = [], []
    for i, a in enumerate(areas):
        if not isinstance(a, dict):
            problems.append("areas[%d] is not an object" % i)
            continue
        k, lab, order = a.get("key"), a.get("label"), a.get("order")
        keys.append(k)
        if k not in AREAS:
            problems.append("areas[%d] key=%r is not one of %s"
                            % (i, k, "|".join(AREAS)))
        if not isinstance(lab, str) or not lab.strip():
            problems.append("areas[%r] has no label; the page shows the label, "
                            "never the key" % (k,))
        if not isinstance(order, int):
            problems.append("areas[%r] order=%r is not an integer" % (k, order))
        else:
            orders.append(order)
    for k in AREAS:
        if k not in keys:
            problems.append("the areas block does not declare %r; all five of "
                            "%s are declared or the page cannot group them"
                            % (k, "|".join(AREAS)))
    if len(set(orders)) != len(orders):
        problems.append("two areas share an order value: %s"
                        % "/".join(str(o) for o in orders))
    return keys


def check_attribution(e, tag, problems, today):
    """typedBy and typedOn, the guard that replaced the evidence gate."""
    by = e.get("typedBy")
    if isinstance(by, str) and by:
        if any(c.isspace() for c in by):
            problems.append("%s typedBy=%r contains whitespace; use role/name"
                            % (tag, by))
        else:
            role = by.split("/", 1)[0]
            if role not in ROLES:
                problems.append("%s typedBy=%r names role %r, not one of %s; a "
                                "typed state is somebody's judgement and the "
                                "roles are fixed"
                                % (tag, by, role, "|".join(ROLES)))
    on = e.get("typedOn")
    if isinstance(on, str) and on:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", on):
            problems.append("%s typedOn=%r is not a plain YYYY-MM-DD date"
                            % (tag, on))
        elif on > today:
            problems.append("%s typedOn=%s is after today (%s): nobody types "
                            "tomorrow's judgement" % (tag, on, today))


def validate(doc, entries, names, today=None):
    """Whole-file census. Returns (problems, stats). Every entry is examined;
    `checks` is the denominator for `problems`."""
    today = today or datetime.date.today().isoformat()
    problems, checks = [], 0
    seen = {}
    shorts = {}                  # label -> first entry index, for uniqueness
    wheres = {}                  # where value -> count, 'none' counted too
    short_lens, name_lens = [], []
    ev_refs = ev_ok = 0
    with_ev = 0
    note_lens = []
    roles = {}
    dates = []
    q_blockers = d_blockers = 0
    q_landed, d_settled = [], []

    checks += 1
    check_header(doc, problems)

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
                               ("class", CLASSES), ("phase", PHASES),
                               ("where", WHERES)):
            checks += 1
            val = e.get(field)
            if val is not None and str(val) not in allowed:
                problems.append("%s %s=%r is not one of %s"
                                % (tag, field, val, "|".join(allowed)))

        # `where` IS REQUIRED WHEN THE SYSTEM IS SOMEWHERE AND FORBIDDEN WHEN
        # IT IS NOWHERE, and these are TWO rungs because they fail apart: the
        # first catches a tile whose colour names no codebase, the second a
        # tile that names an engine for a thing that does not exist. Same
        # asymmetry as `evidence`, same reason.
        st = e.get("status")
        wh = e.get("where")
        checks += 1
        if st in ("exists", "partial") and not (isinstance(wh, str) and wh):
            problems.append("%s status=%s carries no 'where'; which codebase "
                            "is this colour a reading of (%s)?"
                            % (tag, st, "|".join(WHERES)))
        checks += 1
        if st == "absent" and wh not in (None, ""):
            problems.append("%s status=absent must carry no 'where' (got %r): "
                            "a system that is nowhere cannot be somewhere"
                            % (tag, wh))

        # `short`, THE OPTIONAL DISPLAY LABEL, four shape rungs and NO LENGTH
        # BOUND. No rendered width has been measured at 360px in any session,
        # so the instrument prints the character series and sets no threshold.
        # It must be a single-line string with no edge whitespace, STRICTLY
        # shorter than the name it stands in for, and unique across the file:
        # two tiles reading the same label is worse than one tile reading long.
        sh = e.get("short")
        if sh is not None:
            checks += 1
            if not isinstance(sh, str) or not sh.strip() or "\n" in sh:
                problems.append("%s short=%r must be a non-empty single-line "
                                "string" % (tag, sh))
            else:
                checks += 1
                if sh != sh.strip():
                    problems.append("%s short=%r has leading or trailing "
                                    "space" % (tag, sh))
                checks += 1
                if isinstance(name, str) and len(sh) >= len(name):
                    problems.append("%s short=%r is %d chars and the name is "
                                    "%d: a label that is not shorter than the "
                                    "name it replaces has no reason to exist"
                                    % (tag, sh, len(sh), len(name)))
                checks += 1
                if sh in shorts:
                    problems.append("%s short=%r is also entry[%d]'s label; "
                                    "two tiles reading the same label is "
                                    "worse than one tile reading long"
                                    % (tag, sh, shorts[sh]))
                else:
                    shorts[sh] = i
                short_lens.append(len(sh))
        if isinstance(name, str):
            name_lens.append(len(name))
        wheres[str(wh) if wh else "none"] = \
            wheres.get(str(wh) if wh else "none", 0) + 1

        checks += 2
        check_attribution(e, tag, problems, today)
        by = e.get("typedBy")
        if isinstance(by, str) and by:
            roles[by.split("/", 1)[0]] = roles.get(by.split("/", 1)[0], 0) + 1
        on = e.get("typedOn")
        if isinstance(on, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", on):
            dates.append(on)

        checks += 1
        blocker = e.get("blocker")
        if isinstance(blocker, str) and any(c.isspace() for c in blocker):
            problems.append("%s blocker=%r contains whitespace; use / and .."
                            % (tag, blocker))
        checks += 1
        if isinstance(blocker, str) and blocker.startswith("queue-"):
            num = blocker[len("queue-"):]
            q_blockers += 1
            if not queue_files(num):
                problems.append("%s blocker=%s names no queue file" % (tag, blocker))
            elif queue_is_landed(num):
                q_landed.append(pair(name, blocker))
        checks += 1
        if isinstance(blocker, str) and re.match(r"^D\d+$", blocker):
            d_blockers += 1
            if not decision_records(blocker):
                problems.append("%s blocker=%s names no decision record in %s"
                                % (tag, blocker,
                                   rel(os.path.join(ROOT, "ledger-v2", "respec",
                                                    "decision-register"))))
            elif not decision_is_open(blocker):
                d_settled.append(pair(name, blocker))

        status = e.get("status")
        ev = e.get("evidence", [])
        checks += 1
        if not isinstance(ev, list):
            problems.append("%s evidence is not a list" % tag)
            ev = []
        if ev:
            with_ev += 1
        # EVIDENCE IS NO LONGER REQUIRED for exists or partial: the state is
        # typed and attributed instead. The one rule kept is that an entry
        # typed absent may not cite paths that say otherwise.
        checks += 1
        if status == "absent" and ev:
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
        elif isinstance(note, str):
            note_lens.append(len(note))

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
        "withEv": with_ev,
        "noteLens": sorted(note_lens),
        "wheres": wheres,
        "shortLens": sorted(short_lens),
        "nameLens": sorted(name_lens),
        "notAbsent": sum(1 for e in entries if isinstance(e, dict)
                         and e.get("status") in ("exists", "partial")),
        "roles": roles,
        "dates": sorted(dates),
        "qBlockers": q_blockers,
        "dBlockers": d_blockers,
        "qLanded": sorted(q_landed),
        "dSettled": sorted(d_settled),
        "tally": {
            "status": tally(entries, "status", STATUSES),
            "area": tally(entries, "area", AREAS),
            "class": tally(entries, "class", CLASSES),
            "phase": tally(entries, "phase", PHASES),
        },
    }
    return problems, stats


def pair(name, blocker):
    """One entry carrying both halves, and NO SPACES IN A VALUE: every reader
    of a key=value channel splits on whitespace and truncates silently, so a
    system name with spaces goes in with underscores."""
    return "%s->%s" % (re.sub(r"\s+", "_", str(name)), blocker)


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


def series(vals):
    """min/median/max over n, the printed series a bound would come FROM."""
    if not vals:
        return NOTHING.replace(" ", "_") + "/n=0"
    n = len(vals)
    return "%d..%d/med%d/n=%d" % (vals[0], vals[-1], vals[n // 2], n)


# ---------------------------------------------------------------- reporting

def run(path, names_path=None, out=sys.stdout, emit=False, today=None):
    """Validate and report. With emit=True the report goes to stderr and the
    VALIDATED entries go to stdout as JSON, so the map view and the roadmap
    fold consume this file through the check rather than around it: one parser,
    one set of fixed values, one refusal path. Exit code is unchanged, so a
    refusal cannot be rendered as a page."""
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

    doc, entries, err = load(path)
    if err is not None or not entries:
        why = err or "zero entries"
        print("systems-inventory: %s entries=0 namesFromOrder=%d covered=0/%d "
              "reason=%s file=%s"
              % (NOTHING, len(names), len(names), why.replace(" ", "_"),
                 rel(path)), file=out)
        return 2

    problems, st = validate(doc, entries, names, today=today)
    n = len(entries)
    print("systems-inventory: entries=%d namesFromOrder=%d covered=%d/%d "
          "file=%s order=%s"
          % (n, len(names), len(st["covered"]), len(names), rel(path), rel(used)),
          file=out)
    # Whole-file censuses, each on its own line with its denominator.
    print("  byStatus: " + fmt_tally(st["tally"]["status"], n), file=out)
    print("  byClass:  " + fmt_tally(st["tally"]["class"], n), file=out)
    print("  byArea:   " + fmt_tally(st["tally"]["area"], n), file=out)
    print("  byPhase:  " + fmt_tally(st["tally"]["phase"], n), file=out)
    # WHICH CODEBASE THE COLOURS ARE ABOUT, a whole-file census at this run.
    # `none` is the absent tiles, which may not carry one; `missing` is the
    # fault, and it prints its denominator either way so a clean run cannot be
    # confused with a run that examined nothing.
    missing_where = sum(1 for e in entries if isinstance(e, dict)
                        and e.get("status") in ("exists", "partial")
                        and not e.get("where"))
    print("  byWhere:  %s none=%d/%d-absent missingWhere=%d/%d-not-absent"
          % (" ".join("%s=%d/%d" % (k, st["wheres"].get(k, 0), n)
                      for k in WHERES),
             st["wheres"].get("none", 0), n, missing_where, st["notAbsent"]),
          file=out)
    # THE LABEL SERIES, AND NO BOUND. 4a set no length threshold because no
    # rendered width has been measured at 360px; this is the series a bound
    # would come FROM, in characters, min..max/median over n.
    print("  labels:   short=%d/%d shortChars=%s nameChars=%s "
          "(series, no length bound set anywhere)"
          % (len(st["shortLens"]), n, series(st["shortLens"]),
             series(st["nameLens"])), file=out)
    absent = st["tally"]["status"]["absent"]
    # TYPED, AND BY WHOM. The zero that matters here is untypedBy: a tile with
    # no owner is the anonymous colour the ruling replaced.
    print("  typedBy:  %s untyped=%d/%d typedOn=%s..%s (oldest..newest of %d)"
          % ("/".join("%s.%d" % (r, c) for r, c in sorted(st["roles"].items()))
             or NOTHING.replace(" ", "_"),
             n - sum(st["roles"].values()), n,
             st["dates"][0] if st["dates"] else NOTHING.replace(" ", "_"),
             st["dates"][-1] if st["dates"] else NOTHING.replace(" ", "_"),
             len(st["dates"])), file=out)
    print("  evidence: refs=%d resolved=%d/%d entriesWithEvidence=%d/%d "
          "absentCarryNone=%d (%s for those) evidenceIsProvenanceNotTheGate=true"
          % (st["evRefs"], st["evOk"], st["evRefs"], st["withEv"], n, absent,
             NOTHING), file=out)
    # PRINTED SERIES, NOT BOUNDS. Neither line refuses anything today; both
    # exist so a director can read real runs before any number is set.
    print("  noteChars: %s (series, no bound set)" % series(st["noteLens"]),
          file=out)
    print("  blockerStale: queueLanded=%d/%d decisionSettled=%d/%d "
          "(series, no bound set) landed=%s settled=%s"
          % (len(st["qLanded"]), st["qBlockers"], len(st["dSettled"]),
             st["dBlockers"],
             ",".join(capped(st["qLanded"])) or "none",
             ",".join(capped(st["dSettled"])) or "none"), file=out)
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
    "typedBy": "builder/tier3", "typedOn": "2026-09-09",
    "note": "A synthetic entry that exists nowhere in the project.",
}
HEADER = {
    "schema": SCHEMA,
    "areas": [{"key": k, "label": k, "order": i + 1}
              for i, k in enumerate(AREAS)],
}


def _fixture(tmp, entries, header=None, tag="fixture"):
    p = os.path.join(tmp, tag + ".json")
    doc = dict(HEADER if header is None else header)
    doc["systems"] = entries
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    return p


def selftest_parsers():
    """The two status parsers, on SYNTHETIC text only, so no real queue item or
    decision record can break this rung by being worked on. Returned in the
    exit-code convention (0 means the parser answered as it should) so these
    fold into the same rung table as the file cases."""
    cases = [
        ("accept/queue-status-LANDED-is-landed",
         says_landed("status: LANDED 2026-09-05, commit c1311ea7"), True),
        ("accept/queue-status-DONE-is-landed",
         says_landed("status: DONE 2026-09-07. Jafar allowed the branch"), True),
        ("accept/queue-status-READY-is-not-landed",
         says_landed("status: READY 2026-09-08. Filed by the ruling"), False),
        ("accept/queue-status-BLOCKED-is-not-landed",
         says_landed("status: BLOCKED 2026-09-09 behind rung 1"), False),
        ("accept/no-status-line-is-not-landed",
         says_landed("line: production\nspec: nothing\n"), False),
        # THE REGRESSION PIN for the fault this tool's own first series found.
        ("accept/decision-status-mid-line-is-open",
         says_open("Date: 2026-08-31. Status: OPEN, probe authorized."), True),
        ("accept/decision-status-DECIDED-is-not-open",
         says_open("STATUS: DECIDED 2026-09-02 by Jafar, recorded"), False),
        ("accept/decision-status-APPROVED-is-not-open",
         says_open("Date: 2026-09-08. Status: APPROVED (Jafar, in session)"),
         False),
    ]
    return [(label, 0, 0 if got == want else 1) for label, got, want in cases]


def selftest():
    """Accepting cases FIRST, then the planted refusals. The first accepting
    fixture is the LIVE inventory and the LIVE queue file, so doing the work
    this tool asks for cannot break the tool; every rejecting fixture is
    synthetic."""
    rungs, ok = [], True

    print("== rung 1 ACCEPTING: the live inventory and the live names file ==")
    code = run(INVENTORY)
    rungs.append(("accept/live-inventory", 0, code))

    print("\n== rungs ACCEPTING: the two status parsers on synthetic text ==")
    for row in selftest_parsers():
        print("  %-48s %s" % (row[0], "PASS" if row[1] == row[2] else "FAIL"))
        rungs.append(row)

    with tempfile.TemporaryDirectory() as tmp:
        # RUNG 2 IS THE CONTRACT REVERSAL ITSELF. Under the old rule this exact
        # entry was refused ("status=exists with no evidence; the honest status
        # is absent"). Jafar's 2026-09-09 ruling makes it legal, so it is an
        # ACCEPTING case and sits before every refusal.
        print("\n== rung 2 ACCEPTING: typed exists with no evidence at all "
              "(the reversal) ==")
        code = run(_fixture(tmp, [dict(GOOD, name="planted-typed-only",
                                       status="exists",
                                       where="core-csharp")],
                            tag="typedonly"))
        rungs.append(("accept/typed-exists-with-no-evidence", 0, code))

        # RUNG 3 ACCEPTING: THE TWO FIELDS RULED IN ON 2026-09-09, in the
        # shapes the ruling dictates, so the accepting side of every new rung
        # below is run before any refusal. The live inventory above is the
        # other accepting fixture and it carries all four `where` values.
        print("\n== rung 3 ACCEPTING: where on an exists entry and a short "
              "shorter than its name ==")
        code = run(_fixture(tmp, [
            dict(GOOD, name="planted-with-where-and-short", status="partial",
                 where="both", short="planted"),
            dict(GOOD, name="planted-absent-with-no-where")], tag="wheresh"))
        rungs.append(("accept/where-on-exists-and-absent-with-none", 0, code))

        planted = [
            ("refuse/schema-from-the-retired-contract", 1,
             [dict(GOOD)], dict(HEADER, schema="systems-inventory/v1")),
            ("refuse/areas-block-missing-one-of-the-five", 1, [dict(GOOD)],
             {"schema": SCHEMA,
              "areas": [{"key": k, "label": k, "order": i + 1}
                        for i, k in enumerate(AREAS) if k != "studio"]}),
            ("refuse/no-typedBy", 1,
             [{k: v for k, v in GOOD.items() if k != "typedBy"}], None),
            ("refuse/typedBy-role-that-is-nobody", 1,
             [dict(GOOD, typedBy="wizard/zz")], None),
            ("refuse/typedBy-with-a-space-in-it", 1,
             [dict(GOOD, typedBy="builder tier3")], None),
            ("refuse/typedOn-not-a-date", 1,
             [dict(GOOD, typedOn="yesterday")], None),
            ("refuse/typedOn-in-the-future", 1,
             [dict(GOOD, typedOn="2099-01-01")], None),
            ("refuse/no-note", 1,
             [{k: v for k, v in GOOD.items() if k != "note"}], None),
            ("refuse/absent-carrying-evidence", 1,
             [dict(GOOD, name="planted-absent-cited", status="absent",
                   evidence=["ledger/verify.py"])], None),
            ("refuse/evidence-path-that-does-not-resolve", 1,
             [dict(GOOD, name="planted-ghost", status="exists",
                   evidence=["ledger/Assets/Scripts/Game/NoSuchFile.cs"])], None),
            ("refuse/evidence-token-that-exists-nowhere", 1,
             [dict(GOOD, name="planted-token", status="partial",
                   evidence=["ledger/Assets/Scripts/Game/GameController.cs"
                             "#ZzQqSyntheticTokenThatExistsNowhere"])], None),
            ("refuse/area-outside-the-five", 1,
             [dict(GOOD, name="planted-area", area="vibes")], None),
            # THE FIVE THE RULING NAMES, then three more that keep each shape
            # rung from being a ratchet. Every fixture is synthetic.
            ("refuse/where-outside-the-four", 1,
             [dict(GOOD, name="planted-where", status="exists",
                   where="unity")], None),
            ("refuse/exists-with-no-where", 1,
             [dict(GOOD, name="planted-nowhere", status="exists")], None),
            ("refuse/absent-carrying-where", 1,
             [dict(GOOD, name="planted-absent-somewhere",
                   where="core-csharp")], None),
            ("refuse/short-longer-than-its-name", 1,
             [dict(GOOD, name="planted", status="exists",
                   where="repo",
                   short="a label longer than the name it stands for")], None),
            ("refuse/two-entries-sharing-a-short", 1,
             [dict(GOOD, name="planted-one", short="shared"),
              dict(GOOD, name="planted-two", short="shared")], None),
            ("refuse/short-as-long-as-its-name", 1,
             [dict(GOOD, name="planted-equal", short="planted-equal")], None),
            ("refuse/short-that-is-blank", 1,
             [dict(GOOD, name="planted-blank-short", short="   ")], None),
            ("refuse/short-with-a-trailing-space", 1,
             [dict(GOOD, name="planted-padded-short", short="padded ")], None),
            ("refuse/missing-required-field", 1,
             [{k: v for k, v in GOOD.items() if k != "phase"}], None),
            ("refuse/blocker-names-no-decision-record", 1,
             [dict(GOOD, name="planted-blocker", blocker="D9999")], None),
            ("refuse/blocker-names-no-queue-file", 1,
             [dict(GOOD, name="planted-queue", blocker="queue-99999")], None),
            ("refuse/duplicate-name", 1, [dict(GOOD), dict(GOOD)], None),
            ("refuse/bare-list-with-no-header", 1, None, None),
        ]
        for label, entries, header in [(l, e, h) for l, _, e, h in planted]:
            want = 1
            print("\n== rung: %s (expect exit %d) ==" % (label, want))
            if entries is None:
                p = os.path.join(tmp, "bare.json")
                with open(p, "w", encoding="utf-8") as fh:
                    json.dump([dict(GOOD)], fh)
            else:
                p = _fixture(tmp, entries, header,
                             tag=re.sub(r"[^A-Za-z0-9]+", "-", label))
            code = run(p)
            rungs.append((label, want, code))

        print("\n== rung: nothing-measured/empty-file (expect exit 2) ==")
        code = run(_fixture(tmp, [], tag="empty"))
        rungs.append(("nothing-measured/empty-file", 2, code))

        print("\n== rung: could-not-run/no-names-file (expect exit 3) ==")
        code = run(INVENTORY,
                   names_path=os.path.join(tmp, "no-such-names-file.md"))
        rungs.append(("could-not-run/no-names-file", 3, code))

    print("\n== selftest done ==")
    for label, want, got in rungs:
        good = want == got
        ok = ok and good
        print("  %-48s want=%d got=%d %s" % (label, want, got,
                                             "PASS" if good else "FAIL"))
    passed = sum(1 for l, w, g in rungs if w == g)
    print("  selftest: passed=%d/%d rungs (accepting first: %d of them)"
          % (passed, len(rungs),
             sum(1 for l, w, g in rungs if l.startswith("accept/"))))
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
                    help="accepting cases then the planted refusals")
    ap.add_argument("--emit-json", action="store_true",
                    help="report on stderr, validated entries on stdout "
                         "(for the map view and the roadmap fold)")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return run(args.file, args.names, emit=args.emit_json)


if __name__ == "__main__":
    sys.exit(main())
