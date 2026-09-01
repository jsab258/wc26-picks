#!/usr/bin/env python3
"""LEDGER prop viewer, the half that can be tested: find, measure, lay out.

WHAT THIS IS FOR. Jafar double-clicks "3 LOOK AT THE PROPS.bat" and Blender
opens showing every prop the pipeline made, side by side, labelled. Nobody
types a path. This file is the part of that which is not Blender: it finds the
props on disk, measures each one from the file's own numbers, and computes a
grid that cannot self-intersect. It runs in two places and is the same code in
both, so the two phases can never disagree about what is there or where it goes:

  1. THE PREFLIGHT, before any window opens, run through Blender's own Python
     (`blender --background --factory-startup --python propview.py -- ...`).
     Blender is already located by then, so this costs no second tool search
     and no system Python. It prints the count and writes a one-line status
     file the .bat reads.
  2. INSIDE THE VIEWER, imported by blender/view_props.py, which asks it for
     the same order and the same cells and then places real geometry.

WHY THE STATUS FILE AND NOT AN EXIT CODE. Blender exits 0 when a --python
script raises after its last operator, and exits 0 having done nothing at all
in several other cases. clean_lod.py learned this first and writes a result
file for the same reason; the caller reads the file.

WHAT IT NEVER DOES. It does not write into content/props, does not save a
.blend, does not touch a GLB. Everything it writes goes to the workspace path
it is handed (%USERPROFILE%\\ledger-meshgen), which is where the grinder
already puts its scratch.

UNRUN ON THE MACHINE THAT MATTERS. There is no Blender, no Windows and no
PowerShell in the container this was written in. What IS checked here, by
`--selftest`: the discovery rule, the layout arithmetic against the REAL 37
measured props in content/props/manifest.json (no pair of them overlaps), the
seam between the .bat and both Python scripts (every flag the .bat passes is a
flag the parser accepts), and the read-only guard over the Blender script.
"""
import json
import math
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

# glb_stats is the pipeline's own GLB reader: stdlib, composes node transforms
# (fourteen of the 37 base meshes carry their scale on the node, and reading
# accessor min/max naively reports a traffic cone as 3 mm). Imported rather
# than reimplemented; a second bounds reader is a second set of its bugs.
sys.path.insert(0, str(HERE))
try:
    from meshgen import glb_stats
except Exception as _e:                                          # noqa: BLE001
    glb_stats = None
    _GLB_IMPORT_ERROR = "%s: %s" % (type(_e).__name__, _e)
else:
    _GLB_IMPORT_ERROR = ""

LOD_RE = re.compile(r"^(?P<id>.+)_LOD(?P<n>\d+)$", re.I)

#: The gap between cells, DERIVED FROM THE BATCH rather than picked. Read off
#: the real series (37 props, content/props/manifest.json, 1 Sep): footprint
#: max-extent min 0.100 m, median 0.674 m, mean 0.976 m, max 3.308 m. Half the
#: median puts the gap at 0.34 m for this batch, which is a third of the mean
#: prop and about 4% of the whole grid's width, so neighbours read as separate
#: without the grid becoming mostly air.
GAP_FRACTION_OF_MEDIAN = 0.5
#: The floor is a LEGIBILITY JUDGEMENT, not a measurement, and is said so out
#: loud. It only binds for a batch whose median prop is under 0.6 m across (a
#: batch of nothing but bollards and drain covers), where half the median would
#: be a few centimetres and the props would read as one smear.
GAP_FLOOR_M = 0.30
#: The cell for a prop whose bounds could not be read at all. Never zero: a
#: prop of unknown size must not be given a cell of no size, because that is
#: the one value guaranteed to intersect its neighbours.
UNMEASURED_CELL_M = 1.0


# ---------------------------------------------------------------------------
# DISCOVERY. One rule about what a prop is, used by the preflight and by the
# viewer.
# ---------------------------------------------------------------------------
def discover(props_dir, lod="LOD0"):
    """Every prop under props_dir, one entry each, best LOD chosen.

    Returns (props, notes). `props` is sorted by id, which is the order the
    grid is laid out in and therefore what "the third one" means. A prop is a
    directory holding <id>_LOD<n>.glb files, or a bare .glb sitting in
    props_dir. Nothing is opened here.
    """
    props, notes = [], []
    root = pathlib.Path(props_dir)
    if not root.is_dir():
        notes.append("no directory at %s" % root)
        return props, notes

    groups = {}
    files_seen = 0
    for path in sorted(root.rglob("*.glb")):
        files_seen += 1
        stem = path.stem
        m = LOD_RE.match(stem)
        pid, n = (m.group("id"), int(m.group("n"))) if m else (stem, None)
        groups.setdefault(pid, []).append((n, path))

    for pid in sorted(groups):
        entries = groups[pid]
        want = None
        if lod:
            want = next((p for n, p in entries
                         if n is not None and ("LOD%d" % n).upper() == lod.upper()), None)
        if want is None:
            numbered = sorted([(n, p) for n, p in entries if n is not None])
            if numbered:
                want = numbered[0][1]
                notes.append("%s has no %s, showing %s instead"
                             % (pid, lod, numbered[0][1].name))
            else:
                want = entries[0][1]
        props.append({
            "id": pid,
            "path": str(want),
            "file": want.name,
            "lods": sorted([("LOD%d" % n) for n, _ in entries if n is not None]),
            "files": len(entries),
        })
    return props, notes


def read_manifest(props_dir):
    """The pipeline's own record of what it made, or None. Used only to CHECK
    what is on disk, never as a substitute for it: a manifest travels in git
    and the meshes do not, so a clone can hold a manifest naming 37 props and
    no mesh at all, and that case must not read as an empty batch."""
    p = pathlib.Path(props_dir) / "manifest.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:                                            # noqa: BLE001
        return None


def manifest_dims(man):
    """{id: (w, d, h)} in metres, from the manifest's measured block.

    THE AXES ARE glTF's, Y-up: dims_m is [x, y(up), z]. The grid works in
    Blender's Z-up, where the footprint is (x, z) and the height is y. The
    swap happens here, once, and nowhere else."""
    out = {}
    for it in ((man or {}).get("items") or []):
        meas = it.get("measured") or {}
        key = "LOD0" if "LOD0" in meas else (sorted(meas)[0] if meas else None)
        d = (meas.get(key) or {}).get("dims_m") if key else None
        if d and len(d) >= 3:
            out[it.get("id")] = (float(d[0]), float(d[2]), float(d[1]))
    return out


def measure(props, fallback_dims=None):
    """Fill in w/d/h for each prop FROM THE FILE'S OWN NUMBERS.

    Falls back to the manifest only when the file cannot be read, and says
    which of the two every size came from. A size nobody could get is left as
    None rather than defaulted, so the count of measured props can ship its
    denominator."""
    fallback_dims = fallback_dims or {}
    notes = []
    measured = unread = 0
    for p in props:
        p["w"] = p["d"] = p["h"] = None
        p["size_from"] = "nothing"
        st = None
        if glb_stats is not None:
            try:
                st = glb_stats(p["path"])
            except Exception as e:                               # noqa: BLE001
                notes.append("%s could not be read (%s: %s)"
                             % (p["file"], type(e).__name__, e))
        if st and st.get("dims_m"):
            dm = st["dims_m"]
            p["w"], p["d"], p["h"] = float(dm[0]), float(dm[2]), float(dm[1])
            p["verts"], p["tris"] = st.get("verts"), st.get("tris")
            p["size_from"] = "the file"
            measured += 1
            continue
        if p["id"] in fallback_dims:
            p["w"], p["d"], p["h"] = fallback_dims[p["id"]]
            p["size_from"] = "the manifest"
            measured += 1
            notes.append("%s: bounds came from the manifest, not from the file"
                         % p["id"])
            continue
        unread += 1
        notes.append("%s: no bounds from the file and none in the manifest, so "
                     "it gets the default %.2f m cell" % (p["id"], UNMEASURED_CELL_M))
    return measured, unread, notes


# ---------------------------------------------------------------------------
# THE GRID. Pure arithmetic, no Blender, and the only part of the placement
# that can be checked before the first run.
# ---------------------------------------------------------------------------
def median(xs):
    xs = sorted(xs)
    if not xs:
        return 0.0
    mid = len(xs) // 2
    return xs[mid] if len(xs) % 2 else (xs[mid - 1] + xs[mid]) / 2.0


def layout(props, gap=None, cols=None):
    """Place each prop in its own cell. Nothing can intersect, by construction.

    ROWS OF A FIXED COUNT, PACKED TIGHT ACROSS. Each row holds `cols` props, so
    counting along a row to "the third one" works; within a row each prop gets
    exactly its own width plus the gap, and the row is centred. Row depth is the
    deepest prop in that row.

    MEASURED, NOT ASSUMED, on the real 37 (1 Sep). The footprint spread is 33x
    (0.10 m to 3.31 m). A uniform cell would have put a drain cover in a 3.31 m
    box. Aligning columns as well (column width = widest prop in the column) was
    tried and measured: 15.67 x 11.66 m with the props filling 28% of it,
    against 12.19 x 11.66 m packed tight. That is 22% off the width for nothing
    but column alignment, and 22% is exactly the legibility of the smallest
    props at framing distance, which are the hardest ones to judge.

    Returns a dict. `placements` carries a centre (x, y) per prop in Blender
    axes with +Y away from the viewer, the grid centred on the origin, and row
    0 nearest. The order is the order of `props`, which is sorted by id.
    """
    n = len(props)
    sizes = [max(p["w"], p["d"]) for p in props
             if p.get("w") and p.get("d")]
    med = median(sizes) if sizes else UNMEASURED_CELL_M
    if gap is None:
        gap = max(GAP_FLOOR_M, GAP_FRACTION_OF_MEDIAN * med)
    if n == 0:
        return {"placements": [], "cols": 0, "rows": 0, "gap": gap,
                "median_footprint": med, "extent": (0.0, 0.0)}
    if not cols:
        cols = max(1, int(math.ceil(math.sqrt(n))))
    cols = min(cols, n)
    rows = int(math.ceil(float(n) / cols))

    def wd(p):
        w = p.get("w") or UNMEASURED_CELL_M
        d = p.get("d") or UNMEASURED_CELL_M
        return max(w, 1e-3), max(d, 1e-3)

    rowd = [0.0] * rows
    roww = [0.0] * rows
    for i, p in enumerate(props):
        w, d = wd(p)
        r = i // cols
        rowd[r] = max(rowd[r], d)
        roww[r] += w + (gap if roww[r] > 0 else 0.0)

    ys, acc = [], 0.0
    for r in range(rows):
        ys.append(acc + rowd[r] / 2.0)
        acc += rowd[r] + gap
    total_d = acc - gap if rows else 0.0
    total_w = max(roww) if roww else 0.0

    placements = []
    run = [0.0] * rows           # how far along its row each prop starts
    for i, p in enumerate(props):
        r, c = i // cols, i % cols
        w, d = wd(p)
        x = -roww[r] / 2.0 + run[r] + w / 2.0
        run[r] += w + gap
        placements.append({
            "id": p["id"], "index": i + 1, "row": r, "col": c,
            "x": x, "y": ys[r] - total_d / 2.0,
            # The cell IS the prop plus its share of the gap. The Blender side
            # compares its own measured bounds against this, so it must be the
            # real free space and not an aligned column that flatters it.
            "cell_w": w, "cell_d": rowd[r], "w": w, "d": d,
            "h": p.get("h"), "path": p.get("path"), "file": p.get("file"),
            "size_from": p.get("size_from", "unknown"),
        })
    return {"placements": placements, "cols": cols, "rows": rows, "gap": gap,
            "median_footprint": med, "extent": (total_w, total_d)}


def overlaps(placements, slack=1e-6):
    """(bad pairs, pairs checked). The denominator ships with the zero: "no
    overlaps" over an empty list is not a result about a grid."""
    bad = []
    checked = 0
    for i in range(len(placements)):
        a = placements[i]
        for j in range(i + 1, len(placements)):
            b = placements[j]
            checked += 1
            dx = abs(a["x"] - b["x"]) - (a["w"] + b["w"]) / 2.0
            dy = abs(a["y"] - b["y"]) - (a["d"] + b["d"]) / 2.0
            if dx < -slack and dy < -slack:
                bad.append((a["id"], b["id"]))
    return bad, checked


# ---------------------------------------------------------------------------
# THE REPORT. What he reads in the window before anything opens.
# ---------------------------------------------------------------------------
def report(props_dir, props, plan, man, disc_notes, meas_notes,
           measured, unread, glb_files):
    L = []
    add = L.append
    add("  props directory : %s" % props_dir)
    if not props:
        add("")
        # THE TWO EMPTY CASES ARE NOT THE SAME ANSWER and must not read alike.
        # A missing directory usually means this .bat is sitting outside the
        # project; an empty one means the batch has not been ground yet.
        if not pathlib.Path(props_dir).is_dir():
            add("  THERE IS NO PROPS DIRECTORY AT ALL at that path, so this is")
            add("  probably not the project folder rather than an empty batch.")
        else:
            add("  NO PROPS ON THIS PC. 0 mesh file(s) under that directory.")
        if man:
            n = len(man.get("items") or [])
            add("  The manifest there names %d item(s) made on %s, but the "
                % (n, man.get("written", "an unknown date")))
            add("  meshes themselves are NOT stored in git, so a fresh copy of")
            add("  the project has the record and not the files.")
        add("  Make them here: double-click  1 MAKE THE PROPS.bat  in this")
        add("  same folder. It runs unattended and skips anything already done.")
        return L

    bad, checked = overlaps(plan["placements"])
    heights = [p["h"] for p in props if p.get("h")]
    foots = [max(p["w"], p["d"]) for p in props if p.get("w") and p.get("d")]
    add("  %d prop(s) found, from %d GLB file(s) (the LOD0 of each is what "
        "opens)" % (len(props), glb_files))
    if man is not None:
        claimed = {it.get("id") for it in (man.get("items") or [])}
        found = {p["id"] for p in props}
        missing = sorted(claimed - found)
        extra = sorted(found - claimed)
        add("  manifest        : names %d item(s); %d of them are on disk, "
            "%d are not" % (len(claimed), len(claimed & found), len(missing)))
        if missing:
            add("    not on disk   : %s" % ", ".join(missing[:8])
                + (" (+%d more not shown)" % (len(missing) - 8) if len(missing) > 8 else ""))
        if extra:
            add("    on disk only  : %s" % ", ".join(extra[:8])
                + (" (+%d more not shown)" % (len(extra) - 8) if len(extra) > 8 else ""))
    else:
        add("  manifest        : none at that directory, so there is nothing "
            "to check the files against")
    # A ZERO HERE WOULD BE A LIE, not a measurement: "largest 0.00 m" reads as
    # a fact about the props when it means nothing could be read at all.
    add("  sizes           : %d measured, %d could not be measured; %s"
        % (measured, unread,
           ("footprint median %.2f m, largest %.2f m; tallest %.2f m"
            % (plan["median_footprint"], max(foots), max(heights) if heights else 0.0))
           if foots else
           "NOTHING MEASURED, so every cell below is the %.2f m default"
           % UNMEASURED_CELL_M))
    # WHICH RULE SET THE GAP is said, because two rules can produce it and the
    # floor binding is a fact about the batch (everything in it is tiny).
    why_gap = ("half the median footprint"
               if plan["gap"] > GAP_FLOOR_M + 1e-9 else
               "the %.2f m legibility floor, because half the median is smaller"
               % GAP_FLOOR_M)
    add("  grid            : %d column(s) x %d row(s), %.2f m gap (%s), "
        "%.1f x %.1f m overall"
        % (plan["cols"], plan["rows"], plan["gap"], why_gap,
           plan["extent"][0], plan["extent"][1]))
    add("  intersections   : %d overlapping pair(s) of %d pair(s) checked"
        % (len(bad), checked))
    for a, b in bad[:6]:
        add("    OVERLAP: %s and %s" % (a, b))
    add("")
    add("  The order below is left to right, front row first. It is what a")
    add("  number means when you say \"the third one is wrong\".")
    for pl in plan["placements"]:
        add("    %02d %-28s %5.2f x %5.2f x %5.2f m   (%s)"
            % (pl["index"], pl["id"], pl["w"], pl["d"], pl["h"] or 0.0,
               pl["size_from"]))
    for note in disc_notes + meas_notes:
        add("  note: %s" % note)
    return L


# ---------------------------------------------------------------------------
# CLI. Hand-rolled parsing on purpose: argparse's error path calls sys.exit,
# and inside Blender that means no status file and therefore no diagnosis.
# ---------------------------------------------------------------------------
KNOWN_FLAGS = {"props": None, "status": None, "report": None, "lod": "LOD0",
               "max-cols": None, "selftest": None}


def parse_args(argv):
    args = dict(KNOWN_FLAGS)
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            key = a[2:]
            if key not in args:
                raise ValueError("unknown flag --%s. Known: %s"
                                 % (key, ", ".join("--" + k for k in sorted(args))))
            nxt = argv[i + 1] if i + 1 < len(argv) else None
            if nxt is None or nxt.startswith("--"):
                args[key] = "1"
                i += 1
            else:
                args[key] = nxt
                i += 2
        else:
            i += 1
    return args


def script_argv(argv=None):
    """Blender hands the script everything after `--`; a bare python run has
    no `--` at all. Both must work, because the selftest is the second one."""
    argv = list(sys.argv if argv is None else argv)
    return argv[argv.index("--") + 1:] if "--" in argv else argv[1:]


def plan_for(props_dir, lod="LOD0", max_cols=None):
    """Everything the viewer and the preflight both need, in one call."""
    props, disc_notes = discover(props_dir, lod=lod)
    man = read_manifest(props_dir)
    measured, unread, meas_notes = measure(props, manifest_dims(man))
    plan = layout(props, cols=max_cols)
    glb_files = sum(p["files"] for p in props)
    return {"props": props, "plan": plan, "manifest": man,
            "disc_notes": disc_notes, "meas_notes": meas_notes,
            "measured": measured, "unread": unread, "glb_files": glb_files}


def main(argv=None):
    argv = script_argv(argv)
    try:
        a = parse_args(argv)
    except ValueError as e:
        sys.stderr.write("propview: %s\n" % e)
        return 2
    if a["selftest"]:
        return selftest()

    props_dir = a["props"] or str(HERE.parent.parent / "content" / "props")
    if _GLB_IMPORT_ERROR:
        print("  note: the GLB reader could not be imported (%s), so sizes "
              "come from the manifest where there is one" % _GLB_IMPORT_ERROR)
    cols = int(a["max-cols"]) if a["max-cols"] and a["max-cols"] != "1" else None
    r = plan_for(props_dir, lod=a["lod"], max_cols=cols)
    lines = report(props_dir, r["props"], r["plan"], r["manifest"],
                   r["disc_notes"], r["meas_notes"], r["measured"],
                   r["unread"], r["glb_files"])
    print("")
    print("  ---- what is on this PC -------------------------------------")
    for l in lines:
        print(l)
    print("  -------------------------------------------------------------")
    print("")

    state = "OK" if r["props"] else ("NOPROPS" if pathlib.Path(props_dir).is_dir()
                                     else "NODIR")
    if a["status"]:
        # THE CALLER READS THIS FILE, NOT THE EXIT CODE. Blender exits 0 after
        # a raised script. One line, no spaces inside a value, so cmd's
        # `set /p` and a `for /f` tokens split both read it whole.
        try:
            with open(a["status"], "w", encoding="utf-8") as f:
                f.write("%s %d\n" % (state, len(r["props"])))
        except OSError as e:
            sys.stderr.write("propview: could not write the status file: %s\n" % e)
    if a["report"]:
        try:
            with open(a["report"], "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            print("  (this list is also saved at %s, if you want to send it "
                  "back)" % a["report"])
        except OSError as e:
            sys.stderr.write("propview: could not write the report file: %s\n" % e)
    return 0 if r["props"] else 4


# ---------------------------------------------------------------------------
# SELFTEST. Accepting case first in every section, and the accepting case is
# the real batch wherever there is one.
# ---------------------------------------------------------------------------
def code_only(src):
    """`src` with every comment and string literal removed.

    THE GUARD BELOW READ ITS OWN DOCUMENTATION AS CODE. view_props.py's
    docstring names the calls it must never contain (save_as_mainfile,
    export_scene and the rest) so a reader knows what is being promised, and
    a plain grep for those words found them there and reported the viewer as
    writing files. The prose was right and the instrument was wrong.

    This is the mirror of the lesson in CLAUDE.md about `$"..."` being code:
    there, stripping strings hid real statements. Here, NOT stripping them
    turned a sentence into a finding. Either way the answer is to look at
    tokens rather than at characters, which is what tokenize does.
    """
    import io
    import tokenize
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                out.append(" ")
            else:
                out.append(tok.string)
            out.append(" ")
    except (tokenize.TokenError, IndentationError):
        return src            # unparseable: fail loud rather than fail clean
    return "".join(out)


def opens_outside(src, allowed_fn):
    """(open calls outside `allowed_fn`, open calls inside it).

    An ast walk rather than a grep, because the question is about where a call
    sits, and line numbers are the only honest way to answer it. Both halves
    are returned so the caller prints a denominator instead of a bare zero."""
    import ast
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return (-1, -1)
    lo = hi = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == allowed_fn:
            lo, hi = node.lineno, getattr(node, "end_lineno", node.lineno)
    inside = outside = 0
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "open"):
            if lo is not None and lo <= node.lineno <= hi:
                inside += 1
            else:
                outside += 1
    return outside, inside


def _fake_props(spec):
    return [{"id": i, "w": w, "d": d, "h": h, "path": i + ".glb",
             "file": i + ".glb", "size_from": "test"} for i, w, d, h in spec]


def selftest():                                                  # noqa: C901
    passed = failed = 0
    notes = []

    def ok(name, cond, got=""):
        nonlocal passed, failed
        if cond:
            passed += 1
            print("  ok   %s" % name)
        else:
            failed += 1
            print("  FAIL %s%s" % (name, (" - " + str(got)) if got else ""))

    def refuses(name, fn, must_say=""):
        nonlocal passed, failed
        try:
            fn()
        except Exception as e:                                   # noqa: BLE001
            if must_say and must_say.lower() not in str(e).lower():
                failed += 1
                print("  FAIL %s - refused but said %r, wanted %r"
                      % (name, str(e), must_say))
            else:
                passed += 1
                print("  ok   %s" % name)
            return
        failed += 1
        print("  FAIL %s - accepted input it must refuse" % name)

    import tempfile
    repo = HERE.parent.parent
    print("propview selftest - accepting case first in every section\n")

    # -- A. the grid, against the REAL batch --------------------------------
    print("A. the grid, on the real 37 measured props")
    man = read_manifest(repo / "content" / "props")
    dims = manifest_dims(man)
    if dims:
        props = _fake_props([(k, v[0], v[1], v[2]) for k, v in sorted(dims.items())])
        plan = layout(props)
        bad, checked = overlaps(plan["placements"])
        ok("the real batch lays out with no intersecting pair (%d pair(s) "
           "checked, %d prop(s))" % (checked, len(props)), not bad, str(bad[:4]))
        ok("every prop got a cell at least as big as it is",
           all(p["cell_w"] >= p["w"] - 1e-9 and p["cell_d"] >= p["d"] - 1e-9
               for p in plan["placements"]))
        ok("the gap came from the batch, not from a constant (%.3f m, half of "
           "the %.3f m median footprint)" % (plan["gap"], plan["median_footprint"]),
           abs(plan["gap"] - max(GAP_FLOOR_M,
                                 GAP_FRACTION_OF_MEDIAN * plan["median_footprint"])) < 1e-9)
        ok("the grid is roughly square, not a 37-wide line (%dx%d)"
           % (plan["cols"], plan["rows"]), plan["cols"] == 7 and plan["rows"] == 6,
           "%dx%d" % (plan["cols"], plan["rows"]))
        ok("it is centred on the origin, so framing needs no offset",
           abs(min(p["x"] - p["cell_w"] / 2 for p in plan["placements"])
               + max(p["x"] + p["cell_w"] / 2 for p in plan["placements"])) < 1e-6)
        ok("the order is by id, which is what an index in the label means",
           [p["id"] for p in plan["placements"]] == sorted(dims))
        # THE COUNTING PROPERTY. "The third one" only means anything if reading
        # a row left to right gives the printed order, so it is asserted rather
        # than assumed from how the loop happens to be written.
        rows_x = {}
        for pl in plan["placements"]:
            rows_x.setdefault(pl["row"], []).append(pl)
        ok("within every row, x increases in printed order (%d row(s))"
           % len(rows_x),
           all([q["x"] for q in r] == sorted(q["x"] for q in r)
               for r in rows_x.values()))
        # THE EDGES, not the centres: a row of a 3 m awning and a 0.1 m drain
        # cover has its outermost CENTRES nowhere near symmetric even when the
        # row itself is exactly centred.
        ok("and every row is centred on x=0, so no row drifts off the framing",
           all(abs(min(q["x"] - q["w"] / 2 for q in r)
                   + max(q["x"] + q["w"] / 2 for q in r)) < 1e-9
               for r in rows_x.values()))
    else:
        notes.append("content/props/manifest.json is absent or carries no "
                     "measured dims - the REAL accepting case was SKIPPED")

    # -- B. the grid's edges ------------------------------------------------
    print("\nB. the grid where it is most likely to be wrong")
    one = layout(_fake_props([("only", 1.0, 1.0, 1.0)]))
    ok("one prop is a 1x1 grid at the origin", one["cols"] == 1
       and one["rows"] == 1 and abs(one["placements"][0]["x"]) < 1e-9)
    ok("no props is not an error and reports no extent",
       layout([])["placements"] == [] and layout([])["extent"] == (0.0, 0.0))
    spread = layout(_fake_props([("huge", 3.31, 3.31, 1.0), ("tiny", 0.1, 0.1, 0.1),
                                 ("thin", 0.65, 0.02, 1.0), ("wide", 3.0, 1.74, 1.3)]))
    bad, checked = overlaps(spread["placements"])
    ok("a 33x size spread still does not intersect (%d pair(s))" % checked, not bad,
       str(bad))
    ok("and the tiny prop's cell is its own 0.10 m, not its neighbour's 3.31 m",
       abs(spread["placements"][1]["cell_w"] - 0.1) < 1e-9,
       str(spread["placements"][1]["cell_w"]))
    unmeasured = layout([{"id": "u", "w": None, "d": None, "h": None}])
    ok("a prop with no bounds gets a real cell, never a zero one",
       unmeasured["placements"][0]["cell_w"] >= UNMEASURED_CELL_M - 1e-9)
    tiny_batch = layout(_fake_props([("a", 0.1, 0.1, 0.1), ("b", 0.12, 0.12, 0.9)]))
    ok("a batch of nothing but tiny props still gets the legibility floor",
       abs(tiny_batch["gap"] - GAP_FLOOR_M) < 1e-9, str(tiny_batch["gap"]))
    # The rejecting case for the overlap check itself: a placement that DOES
    # intersect must be reported, or the zero above means nothing.
    clash = [{"id": "a", "x": 0.0, "y": 0.0, "w": 1.0, "d": 1.0},
             {"id": "b", "x": 0.4, "y": 0.0, "w": 1.0, "d": 1.0}]
    bad, checked = overlaps(clash)
    ok("the overlap check can actually fail (it catches a planted clash)",
       len(bad) == 1 and checked == 1, str(bad))

    # -- C. discovery -------------------------------------------------------
    print("\nC. discovery, and the three things it must tell apart")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        for pid, lods in (("bench_01", (0, 1, 2)), ("bin_02", (0,)),
                          ("crate_03", (1, 2))):
            d = tmp / pid
            d.mkdir()
            for n in lods:
                (d / ("%s_LOD%d.glb" % (pid, n))).write_bytes(b"glTF")
        (tmp / "loose_prop.glb").write_bytes(b"glTF")
        props, dn = discover(tmp)
        ok("one entry per prop, not one per file (4 props from 7 files)",
           len(props) == 4 and sum(p["files"] for p in props) == 7,
           "%d props, %d files" % (len(props), sum(p["files"] for p in props)))
        ok("LOD0 is the one chosen where there is one",
           all(p["file"].endswith("_LOD0.glb")
               for p in props if p["id"] in ("bench_01", "bin_02")))
        ok("a prop with no LOD0 falls back to its lowest LOD and SAYS so",
           any(p["id"] == "crate_03" and p["file"].endswith("_LOD1.glb")
               for p in props)
           and any("crate_03" in n and "LOD1" in n for n in dn), str(dn))
        ok("a bare .glb with no LOD suffix is still a prop",
           any(p["id"] == "loose_prop" for p in props))
        ok("the order is alphabetical by id",
           [p["id"] for p in props] == sorted(p["id"] for p in props))
        empty, en = discover(tmp / "nothing-here")
        ok("a directory that does not exist reads as NODIR, with the path named",
           empty == [] and any("no directory at" in n for n in en), str(en))
        (tmp / "empty").mkdir()
        empty2, _ = discover(tmp / "empty")
        ok("an empty directory reads as no props, which is a different thing",
           empty2 == [])

        # The status file is what the .bat reads, so its three states are
        # checked by running main() the way Blender runs it.
        st = tmp / "status.txt"
        rep = tmp / "report.txt"
        rc = main(["x", "--", "--props", str(tmp), "--status", str(st),
                   "--report", str(rep)])
        text = st.read_text(encoding="utf-8").strip()
        ok("main writes OK and the count for a directory with props",
           rc == 0 and text.startswith("OK 4"), text)
        ok("and the report file it points at exists and names every prop",
           rep.is_file() and rep.read_text(encoding="utf-8").count("\n") > 4)
        rc = main(["x", "--", "--props", str(tmp / "empty"), "--status", str(st)])
        text = st.read_text(encoding="utf-8").strip()
        ok("an empty directory writes NOPROPS 0 and returns non-zero",
           rc != 0 and text == "NOPROPS 0", text)
        rc = main(["x", "--", "--props", str(tmp / "gone"), "--status", str(st)])
        text = st.read_text(encoding="utf-8").strip()
        ok("a missing directory writes NODIR, NOT NOPROPS",
           text == "NODIR 0", text)

    # -- D. the argument parser, both ways ----------------------------------
    print("\nD. the argument parser")
    a = parse_args(["--props", "D", "--status", "S", "--lod", "LOD1"])
    ok("it accepts the real argument list", a["props"] == "D" and a["lod"] == "LOD1")
    ok("Blender's leading arguments are dropped at the -- separator",
       script_argv(["blender", "--background", "--python", "p.py", "--",
                    "--props", "D"]) == ["--props", "D"])
    ok("and a plain python run with no -- still works",
       script_argv(["propview.py", "--props", "D"]) == ["--props", "D"])
    refuses("an unknown flag is refused by name",
            lambda: parse_args(["--nonsense", "x"]), "unknown flag")

    # -- E. the seam with the .bat and the Blender script -------------------
    print("\nE. the seam nobody can execute here")
    bat = HERE / "3 LOOK AT THE PROPS.bat"
    viewer = HERE / "blender" / "view_props.py"
    ps = HERE / "where-blender.ps1"
    for f in (bat, viewer, ps):
        ok("the viewer ships %s" % f.name, f.exists(), "ABSENT")
    if viewer.exists():
        vsrc = viewer.read_text(encoding="utf-8")
        try:
            compile(vsrc, str(viewer), "exec")
            ok("the Blender script compiles", True)
        except SyntaxError as e:
            ok("the Blender script compiles", False, str(e))
        vflags = set(re.findall(r'"(--[a-z-]+)"', vsrc))
        ok("the Blender script accepts the flags it defines for itself",
           vflags <= {"--" + k for k in KNOWN_FLAGS} | {"--background",
                                                        "--factory-startup",
                                                        "--python"},
           str(sorted(vflags)))
        # READ-ONLY, CHECKED RATHER THAN PROMISED. The viewer opens meshes to
        # look at them; a save, an export or a delete in it is the one fault
        # that could cost content. Checked over CODE, not characters: the
        # first version of this read the file's own docstring, which names
        # these calls to say it does not make them, and reported the viewer
        # as writing files.
        WRITES = (r"save_as_mainfile|save_mainfile|export_scene|"
                  r"shutil\.rmtree|os\.remove|os\.unlink")
        forbidden = re.findall(WRITES, code_only(vsrc))
        ok("the Blender script saves, exports and deletes nothing (%d found "
           "over %d characters of code)"
           % (len(forbidden), len(code_only(vsrc))), not forbidden, str(forbidden))
        ok("and the guard can still fail on a planted write",
           bool(re.search(WRITES,
                          code_only("bpy.ops.wm.save_as_mainfile(filepath=x)\n"))))
        ok("and it is the tokens it reads, not the prose: a docstring naming "
           "a write is not a write",
           not re.search(WRITES, code_only('"""never calls save_as_mainfile"""\n')))
        # IT DOES OPEN ONE FILE FOR WRITING, and that is deliberate: the marker
        # the .bat reads after the window closes. So the check is not "no
        # open() anywhere" (a ban a real requirement would force somebody to
        # quietly relax) but "every open() is the marker", which stays true
        # only while that remains the single write.
        opens, marker = opens_outside(vsrc, "write_marker")
        ok("every file it opens for writing is the marker the .bat reads "
           "(%d open call(s), %d of them inside write_marker)"
           % (opens + marker, marker), opens == 0 and marker == 1,
           "%d outside, %d inside" % (opens, marker))
        ok("and that check can fail: an open() anywhere else is caught",
           opens_outside("def write_marker(p):\n    pass\n"
                         "def other():\n    open('x', 'w')\n",
                         "write_marker") == (1, 0))
        ok("it suppresses the save-on-exit prompt", "use_save_prompt" in vsrc)
        ok("it reuses clean_lod's importer rather than writing a second one",
           "clean_lod" in vsrc and "import_any" in vsrc)
    if bat.exists():
        bsrc = bat.read_text(encoding="utf-8", errors="replace")
        for named in ("propview.py", "view_props.py", "where-blender.ps1",
                      "1 MAKE THE PROPS.bat"):
            ok("the .bat names %s" % named, named in bsrc)
        # EVERY FLAG THE .BAT PASSES MUST BE ONE A PARSER ACCEPTS. One renamed
        # flag between two files nobody can run is a whole evening.
        emitted = set()
        for line in bsrc.splitlines():
            if "propview.py" in line or "view_props.py" in line:
                emitted |= set(re.findall(r"(--[a-z-]+)", line))
        emitted -= {"--background", "--factory-startup", "--python"}
        unknown = sorted(f for f in emitted
                         if f[2:] not in KNOWN_FLAGS)
        ok("every flag the .bat passes to Python is one the parser knows "
           "(%d passed)" % len(emitted), not unknown,
           "unknown: %s; known: %s" % (unknown, sorted(KNOWN_FLAGS)))
        ok("the .bat does not run git at all, so it cannot hang on an editor",
           not re.search(r"\bgit\s+(pull|merge|rebase|commit)\b", bsrc))
        ok("and it says WHY it does not, so the next reader does not add one",
           "GIT_EDITOR" in bsrc and "lint-bat-editor" in bsrc)
        ok("it never writes into content\\props",
           not re.search(r">\s*\"?%REPO%\\content", bsrc, re.I))
        ok("it reads the STATUS FILE rather than trusting Blender's exit code",
           "propview-status" in bsrc and "NOPROPS" in bsrc and "NODIR" in bsrc)
        # THE THREE ENDINGS. He has been burned twice by tools reporting
        # success while doing nothing, and out here an empty Blender and a
        # working one look identical, so each outcome must be its own
        # paragraph rather than one closing line that fits them all.
        ok("and it reads a second marker AFTER the window closes, so what was "
           "on the screen is said in words",
           "propview-opened" in bsrc and "PLACED" in bsrc and "NOTHING" in bsrc)
        ok("the empty case names the viewer as the fault, not the props",
           "LOADED NOTHING" in bsrc and "fault in the VIEWER" in bsrc)
        ok("and a missing marker is its own third answer, not folded into "
           "either of the other two",
           "WITHOUT SAYING WHAT IT SHOWED" in bsrc)
        ok("every file it writes goes to the workspace, never the project",
           all(("%WS%" in l) for l in bsrc.splitlines()
               if l.startswith("set \"") and "propview-" in l))
        # THE ONE CMD FAULT THAT CANNOT BE SEEN BY READING. An unbalanced
        # parenthesis in an echo INSIDE an if-block closes the block early,
        # and the rest of the paragraph then runs unconditionally. Balanced
        # pairs are safe, which is why "prop(s)" is allowed and a lone ")"
        # is not.
        unbalanced = [l.strip() for l in bsrc.splitlines()
                      if l.strip().lower().startswith("echo")
                      and l.count("(") != l.count(")")]
        ok("every echo line has balanced parentheses, so no if-block can be "
           "closed early (%d echo line(s) read)"
           % len([l for l in bsrc.splitlines()
                  if l.strip().lower().startswith("echo")]),
           not unbalanced, str(unbalanced[:3]))
        ok("and that check can fail on a planted lone bracket",
           "echo hello)".count("(") != "echo hello)".count(")"))
    if ps.exists():
        psrc = ps.read_text(encoding="utf-8")
        ok("the PowerShell wrapper reuses probe-tools.ps1's Blender search "
           "rather than copying it",
           "probe-tools.ps1" in psrc and "LedgerTools" not in psrc,
           "naming the tool root itself is what a second copy of the search "
           "looks like")

    # -- F. the formatting law ---------------------------------------------
    print("\nF. the formatting law (no em-dashes, binding since 31 Aug)")
    ours = [pathlib.Path(__file__), bat, viewer, ps]
    absent = [p.name for p in ours if not p.exists()]
    dashed = [p.name for p in ours if p.exists()
              and "\u2014" in p.read_text(encoding="utf-8", errors="replace")]
    ok("no em-dashes in the %d file(s) READ (%d absent, not read)"
       % (len(ours) - len(absent), len(absent)), not dashed, str(dashed))

    print("")
    for n in notes:
        print("  note: %s" % n)
    print("\npropview selftest: %d passed, %d failed, %d checks run"
          % (passed, failed, passed + failed))
    print("  NOT COVERED HERE: Blender itself, Windows, PowerShell and the "
          "'3 LOOK AT THE PROPS.bat' control flow never execute in this "
          "container. The first double-click on Jafar's PC is their accepting "
          "case.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
