#!/usr/bin/env python3
"""Run a NAMED Blender recipe headlessly, or refuse by name.

    python3 tools/art-recipes/run-recipe.py <recipe> --out DIR [recipe args]
    python3 tools/art-recipes/run-recipe.py <recipe> --plan   plan only, no Blender
    python3 tools/art-recipes/run-recipe.py --list            what recipes exist
    python3 tools/art-recipes/run-recipe.py --selftest        offline, no Blender

WHY THIS EXISTS. The Blender invocation is four flags, a bare `--` and an
argument order that has to be exactly right, and it is currently written down
in precisely one place: a PowerShell step inside
`.github/workflows/ledger-art-blender-preview.yml`. A person who wants a
preview, or any job that is not that workflow, should not have to read a
workflow file to find out how to ask. This wrapper takes a NAME and does the
rest, and the argument line it builds is the same one the workflow builds.

THE TWO REFUSALS, and they are the point rather than error handling. A recipe
that does not resolve and a Blender that is not installed both come back as a
REFUSAL NAMING WHAT WAS ASKED FOR, never as a quiet success: `NO-RECIPE
recipeAsked=<name>` and `NO-BLENDER candidatesTried=<n>`. The workflow already
takes that shape for the same two cases, on purpose, because on an art branch
an empty success reads as "the recipe ran and drew nothing".

WHAT IS COVERED AND WHAT IS NOT, said plainly. BLENDER IS NOT INSTALLED IN THIS
CONTAINER: `blender` is not on PATH and `bpy` does not import, both checked
rather than assumed. So neither this wrapper's subprocess call nor any recipe's
render has ever run here. `--selftest` covers what can be covered without it:
recipe resolution, both refusals, the argument construction character by
character, the PNG-count verdict, and the whole pure layer of the shipped
recipe run against the real piece file. The render itself is UNCOVERED, and the
first real run on the Windows runner is the first time those lines execute.
"""
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RECIPE_DIR_REL = "tools/art-recipes"
#: This wrapper is itself in the recipe directory and is not a recipe.
NOT_RECIPES = ("run-recipe",)
#: A recipe name is a NAME, not a path. Anything outside this alphabet is
#: refused before it is joined to a directory, so no caller can walk out of
#: tools/art-recipes with a name.
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

#: THE SAME LIST THE WORKFLOW WALKS, in the same order, so this wrapper and the
#: workflow pick the same binary on the runner. The two Windows paths are
#: copied from the render step; `blender` on PATH is its third candidate. The
#: three after them are for the machines the workflow does not run on, and they
#: are LAST so they can never change the runner's answer. $BLENDER overrides
#: everything, which is how a runner with an unusual install is told once.
BLENDER_CANDIDATES = (
    r"%ProgramFiles%\Blender Foundation\Blender 4.2\blender.exe",
    r"%ProgramFiles%\Blender Foundation\Blender 4.1\blender.exe",
    "blender",
    "/usr/bin/blender",
    "/snap/bin/blender",
    "/Applications/Blender.app/Contents/MacOS/Blender",
)


# ---------------------------------------------------------------------------
# PURE. Everything a selftest can drive, with the filesystem and the subprocess
# injected rather than assumed.
# ---------------------------------------------------------------------------


def clean_name(asked):
    """(name, error). A recipe name, or a refusal that quotes what was asked.

    A trailing `.py` is accepted and stripped, because a person who tab
    completes a filename should not be told off for it. Everything else that is
    not a plain name is refused: a separator, a parent reference, an absolute
    path, an empty string.
    """
    name = (asked or "").strip()
    if name.endswith(".py"):
        name = name[:-3]
    if not name:
        return "", "empty-recipe-name"
    if not NAME_RE.match(name) or ".." in name:
        return "", "not-a-plain-recipe-name/" + name.replace(" ", "~")
    if name in NOT_RECIPES:
        return "", "that-is-the-wrapper-not-a-recipe/" + name
    return name, ""


def recipe_path(root, name):
    return os.path.join(root, RECIPE_DIR_REL, name + ".py")


def list_recipes(root, listdir=None):
    """Every recipe in the directory, by name, sorted. The wrapper excluded."""
    listdir = listdir or os.listdir
    d = os.path.join(root, RECIPE_DIR_REL)
    try:
        names = listdir(d)
    except OSError:
        return []
    return sorted(n[:-3] for n in names
                  if n.endswith(".py") and n[:-3] not in NOT_RECIPES)


def resolve(root, asked, exists=None):
    """(path, error). Refusal always carries the name that was asked for."""
    exists = exists or os.path.exists
    name, err = clean_name(asked)
    if err:
        return "", err
    path = recipe_path(root, name)
    if not exists(path):
        return "", "no-recipe-file/" + RECIPE_DIR_REL + "/" + name + ".py"
    return path, ""


def blender_candidates(env=None):
    """The candidate list with %ProgramFiles% expanded from the environment.

    Expanded here rather than at import so a test can hand in an environment
    and read back exactly what a runner would try.
    """
    env = env if env is not None else os.environ
    out = []
    override = env.get("BLENDER")
    if override:
        out.append(override)
    program_files = env.get("ProgramFiles", r"C:\Program Files")
    for c in BLENDER_CANDIDATES:
        out.append(c.replace("%ProgramFiles%", program_files))
    return out


def find_blender(candidates, exists, probe):
    """(chosen, tried). The workflow's own two-step: a path test, then a probe.

    `exists` answers for a full path; `probe` runs `<candidate> --version` and
    answers whether it worked, which is the only way to find a `blender` that
    lives on PATH. Both are injected so the selftest can walk this with no
    Blender anywhere and with a fake one everywhere.
    """
    tried = []
    for c in candidates:
        tried.append(c)
        if os.sep in c or "/" in c or "\\" in c:
            if exists(c):
                return c, tried
            continue
        if probe(c):
            return c, tried
    return "", tried


def build_argv(blender, recipe, out_dir, extra=()):
    """THE COMMAND, and it is the workflow's line with the same order.

    Workflow render step, quoted:

        & $blender --background --factory-startup --python $recipe -- --out $outDir

    `--background` first so no window is ever opened, `--factory-startup` so a
    stray preference on the runner cannot change a render, then the script,
    then the bare `--` that hands everything after it to the script rather than
    to Blender. Recipe arguments go AFTER `--out DIR`, never before it.
    """
    argv = [blender, "--background", "--factory-startup", "--python", recipe,
            "--", "--out", out_dir]
    argv.extend(extra)
    return argv


def png_count(directory, listdir=None):
    """How many PNGs are in a directory now. Missing directory counts as zero."""
    listdir = listdir or os.listdir
    try:
        return sum(1 for n in listdir(directory) if n.lower().endswith(".png"))
    except OSError:
        return 0


def png_verdict(before, after, exit_code):
    """(ok, status). The workflow's own rule, so the two cannot disagree.

    The workflow fails when the exit code is non-zero OR the PNG count did not
    rise. Both halves matter and they catch different failures: a recipe can
    exit 0 having drawn nothing, and a recipe can draw four frames of five and
    exit 8. THE COUNT IS THE EFFECT and the exit code is only the claim.
    """
    if exit_code != 0 and after > before:
        return False, "PARTIAL/exit%d/but%d-new-png(s)" % (exit_code, after - before)
    if exit_code != 0:
        return False, "FAILED/exit%d/no-new-png" % exit_code
    if after <= before:
        return False, "EMPTY-SUCCESS/exit0/no-new-png"
    return True, "RAN"


def done_line(status, asked, recipe, blender, tried, out_dir,
              before, after, exit_code, seconds):
    """The wrapper's whole-run line. No spaces inside a value, every zero with
    its denominator, and the recipe NAMED in every outcome including refusals."""
    return ("run-recipe done: status=%s recipeAsked=%s recipePath=%s "
            "blender=%s blenderCandidatesTried=%d/%d outDir=%s "
            "pngsBefore=%d pngsAfter=%d pngsNew=%d blenderExit=%s elapsedSeconds=%.1f"
            % (status,
               (asked or "none").replace(" ", "~"),
               (recipe or "unresolved").replace(" ", "~"),
               (blender or "none").replace(" ", "~"),
               len(tried), len(tried) or 0,
               (out_dir or "none").replace(" ", "~"),
               before, after, max(0, after - before),
               "not-run" if exit_code is None else exit_code, seconds))


# ---------------------------------------------------------------------------
# IMPURE. The filesystem, the clock and the subprocess.
# ---------------------------------------------------------------------------


def _probe(cmd, timeout=30):
    """Does `<cmd> --version` work? The only way to find a Blender on PATH."""
    if shutil.which(cmd) is None:
        return False
    try:
        p = subprocess.run([cmd, "--version"], capture_output=True,
                           text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return False
    return p.returncode == 0


def load_recipe_module(path, name="recipe_under_test"):
    """Import a recipe file WITHOUT running it, to reach its pure layer.

    Every recipe here guards its entry point so that an import with no bpy in
    the process does nothing. That is what makes a recipe's arithmetic testable
    on a machine with no Blender on it, which is every machine the studio
    session runs on.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        return None, "cannot-load/" + os.path.basename(path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except BaseException as exc:  # SystemExit included, on purpose
        return None, "recipe-ran-on-import/" + type(exc).__name__
    return module, ""


def plan_only(root, asked, extra, out=print):
    """Run the recipe's own pure planner in this process. No Blender needed."""
    path, err = resolve(root, asked)
    if err:
        out("run-recipe refused: status=NO-RECIPE recipeAsked=%s reason=%s "
            "nothing measured" % ((asked or "none").replace(" ", "~"), err))
        return 1
    module, err = load_recipe_module(path)
    if err:
        out("run-recipe refused: status=UNIMPORTABLE-RECIPE recipeAsked=%s "
            "reason=%s nothing measured" % (asked, err))
        return 1
    if not hasattr(module, "main"):
        out("run-recipe refused: status=RECIPE-HAS-NO-MAIN recipeAsked=%s "
            "nothing measured" % asked)
        return 1
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = module.main([path, "--dry-run", "--root", root] + list(extra))
    for line in buf.getvalue().splitlines():
        out(line)
    out("run-recipe done: status=PLAN-ONLY/no-blender-asked recipeAsked=%s "
        "recipePath=%s recipeExit=%d pngsWritten=0/0-asked-in-plan-mode"
        % (asked, os.path.relpath(path, root), rc))
    return rc


def run(root, asked, out_dir, extra, env=None, out=print):
    """Resolve, find Blender, run it, and report the EFFECT rather than the exit."""
    import time
    started = time.time()
    path, err = resolve(root, asked)
    if err:
        out("run-recipe refused: status=NO-RECIPE recipeAsked=%s reason=%s "
            "nothing measured" % ((asked or "none").replace(" ", "~"), err))
        return 1
    candidates = blender_candidates(env)
    blender, tried = find_blender(candidates, os.path.exists, _probe)
    if not blender:
        out("run-recipe refused: status=NO-BLENDER recipeAsked=%s "
            "candidatesTried=%d/%d first=%s nothing measured"
            % (asked, len(tried), len(candidates),
               (tried[0] if tried else "none").replace(" ", "~")))
        return 1
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        out("run-recipe refused: status=NO-OUTDIR recipeAsked=%s reason=%s "
            "nothing measured" % (asked, type(exc).__name__))
        return 1
    before = png_count(out_dir)
    argv = build_argv(blender, path, out_dir, extra)
    out("run-recipe exec: " + " ".join(argv))
    try:
        p = subprocess.run(argv, cwd=root, stdin=subprocess.DEVNULL)
        code = p.returncode
    except (OSError, subprocess.SubprocessError) as exc:
        out("run-recipe refused: status=BLENDER-WOULD-NOT-START recipeAsked=%s "
            "reason=%s nothing measured" % (asked, type(exc).__name__))
        return 1
    after = png_count(out_dir)
    ok, status = png_verdict(before, after, code)
    out(done_line(status, asked, os.path.relpath(path, root), blender, tried,
                  out_dir, before, after, code, time.time() - started))
    return 0 if ok else 1


# ---------------------------------------------------------------------------


def _selftest(root=ROOT):
    """THE ACCEPTING CASE FIRST, then the refusals, then the recipe's own maths.

    The live codebase is the accepting fixture, per .claude/rules/instruments.md:
    the recipe this repository actually ships is the one resolved, imported and
    planned, so doing the work the wrapper prompts can never break the wrapper.
    The rejecting fixtures are synthetic names that exist nowhere.
    """
    passed, failed = [], []

    def check(name, cond, detail=""):
        (passed if cond else failed).append(name)
        print("  %-64s %s%s" % (name, "pass" if cond else "FAIL",
                                (" : " + str(detail)) if not cond else ""))

    shipped = "quay-street-mickeys-walk"

    # ---- ACCEPT: the shipped recipe resolves by name ----
    path, err = resolve(root, shipped)
    check("accept/the-shipped-recipe-resolves-by-name", path and not err,
          err or path)
    check("accept/and-it-resolves-inside-tools-art-recipes",
          path.startswith(os.path.join(root, RECIPE_DIR_REL)), path)
    check("accept/a-trailing-.py-is-accepted-and-stripped",
          resolve(root, shipped + ".py")[0] == path)
    check("accept/--list-finds-it-and-not-this-wrapper",
          shipped in list_recipes(root) and "run-recipe" not in list_recipes(root),
          list_recipes(root))

    # ---- ACCEPT: the argument line is the workflow's, character for character ----
    argv = build_argv("blender", "tools/art-recipes/x.py", "out/dir")
    check("accept/the-command-is-the-workflow's-line-in-the-workflow's-order",
          argv == ["blender", "--background", "--factory-startup", "--python",
                   "tools/art-recipes/x.py", "--", "--out", "out/dir"], argv)
    check("accept/there-is-exactly-one-bare----and---out-follows-it",
          argv.count("--") == 1 and argv[argv.index("--") + 1] == "--out", argv)
    argv2 = build_argv("b", "r.py", "o", ["--bay", "3"])
    check("accept/recipe-arguments-land-after---out-never-before-it",
          argv2[-4:] == ["--out", "o", "--bay", "3"], argv2)

    # ---- ACCEPT: a Blender that exists is chosen, in the workflow's order ----
    cands = blender_candidates({"ProgramFiles": r"C:\Program Files"})
    chosen, tried = find_blender(
        cands, exists=lambda p: p.endswith("Blender 4.1\\blender.exe"),
        probe=lambda c: False)
    check("accept/an-installed-blender-is-found-by-path",
          chosen.endswith(r"Blender 4.1\blender.exe"), chosen)
    check("accept/and-4.2-was-tried-before-4.1", len(tried) == 2, tried)
    chosen2, tried2 = find_blender(cands, exists=lambda p: False,
                                   probe=lambda c: c == "blender")
    check("accept/a-blender-on-PATH-is-found-by-probing-it",
          chosen2 == "blender" and len(tried2) == 3, (chosen2, tried2))
    check("accept/$BLENDER-overrides-and-is-tried-first",
          blender_candidates({"BLENDER": "/x/b"})[0] == "/x/b")

    # ---- ACCEPT: the count verdict passes the case it should pass ----
    check("accept/exit-0-with-five-new-pngs-is-RAN",
          png_verdict(0, 5, 0) == (True, "RAN"), png_verdict(0, 5, 0))
    check("accept/a-directory-that-already-had-pngs-counts-only-the-new-ones",
          png_verdict(5, 10, 0)[0] is True)

    # ---- ACCEPT: the shipped recipe's own pure layer, on the real piece file ----
    module, err = load_recipe_module(path)
    check("accept/the-recipe-imports-without-blender-and-without-running",
          module is not None, err)
    lines = []
    rc = plan_only(root, shipped, [], out=lines.append)
    check("accept/--plan-runs-the-recipe's-planner-and-exits-0", rc == 0, rc)
    cams = [l for l in lines if l.startswith("walkCam ")]
    bays = [l for l in lines if l.startswith("walkBay ")]
    done = [l for l in lines if " done: " in l and l.startswith(shipped)]
    check("accept/five-cameras-are-planned", len(cams) == 5, len(cams))
    check("accept/one-line-per-shopfront-bay", len(bays) == 6, len(bays))
    check("accept/there-is-exactly-one-recipe-done-line", len(done) == 1, done)

    if cams and done:
        xs = [float(re.search(r"x_m=(-?[\d.]+)", l).group(1)) for l in cams]
        ys = {re.search(r"y_m=(-?[\d.]+)", l).group(1) for l in cams}
        yaws = {re.search(r"yaw_deg=(-?[\d.]+)", l).group(1) for l in cams}
        steps = {round(xs[i + 1] - xs[i], 3) for i in range(len(xs) - 1)}
        check("accept/the-walk-moves-monotonically-down-the-street",
              xs == sorted(xs) and len(set(xs)) == 5, xs)
        check("accept/at-one-constant-step-which-is-one-bay-pitch",
              steps == {6.0}, steps)
        check("accept/at-one-eye-height-and-one-heading-so-it-reads-as-a-walk",
              len(ys) == 1 and len(yaws) == 1, (ys, yaws))
        check("accept/the-eye-height-is-the-file's-1.6m-over-its-own-footway",
              ys == {"1.6719"}, ys)
        d = done[0]
        check("accept/every-bay-is-in-at-least-one-frame",
              "baysInAnyFrame=6/6" in d, d[-200:])
        check("accept/and-the-run-is-covered-rather-than-one-bay-fixated-on",
              "baysLegibleAtSpan0.10=6/6" in d)
        check("accept/the-bay-used-is-printed-with-where-the-default-came-from",
              "mickeysBay=0/6-bays" in d and "bayDefaultFrom=fascia-decal/" in d)
        check("accept/and-the-two-hints-in-the-file-are-reported-as-conflicting",
              "bayHintConflict=bar-back-card-at-bay2" in d)
        # THESE THREE READ THE COUNT RATHER THAN PINNING IT, 2026-09-10. They
        # said 593 pieces and 16 mesh assets, and the fascia package moved the
        # street to 610 and 18, so three checks went red on a layout change
        # that was correct. What they are FOR is that nothing is silently
        # skipped and nothing named is missing, and neither of those is a
        # number: both are an equality between two numbers the recipe itself
        # printed. Read as a relation they also keep holding as the street
        # grows, where a literal has to be re-typed by whoever grows it and
        # every re-typing is a chance to widen a guard by accident.
        # AND THE DENOMINATOR COMES FROM THE DATA, NOT FROM THE RECIPE.
        # Without this line the pair above is self-consistent and blind to the
        # one failure the old literal could see: a recipe that reads 606 of 610
        # pieces and reports 606/606-read is internally honest and externally
        # wrong. Two numbers derived from one variable are one number twice, so
        # the third number is read off the spec file here, independently.
        spec_pieces = None
        try:
            with open(os.path.join(root, "production", "specs",
                                   "vignette-pieces.json"), "r", encoding="utf-8") as fh:
                spec_pieces = int(json.load(fh)["counts"]["pieces"])
        except (OSError, ValueError, KeyError, TypeError):
            spec_pieces = None
        planned = re.search(r"piecesPlanned=(\d+)/(\d+)-read", d)
        check("accept/the-recipe-read-every-piece-the-spec-file-says-it-has",
              spec_pieces is not None and planned is not None
              and int(planned.group(2)) == spec_pieces,
              "specCountsPieces=%s recipeRead=%s"
              % (spec_pieces if spec_pieces is not None else "nothing-measured",
                 planned.group(2) if planned else "no-piecesPlanned-key"))
        skipped = re.search(r"piecesSkipped=(\d+)/(\d+)-read", d)
        check("accept/every-piece-the-recipe-read-is-planned-with-no-silent-skip",
              planned is not None and skipped is not None
              and planned.group(1) == planned.group(2)
              and int(planned.group(1)) > 0
              and skipped.group(1) == "0" and skipped.group(2) == planned.group(2),
              "%s | %s" % (planned.group(0) if planned else "no-piecesPlanned-key",
                           skipped.group(0) if skipped else "no-piecesSkipped-key"))
        meshes = re.search(r"meshAssetsFound=(\d+)/(\d+)-named", d)
        check("accept/every-named-mesh-asset-is-found-on-disk",
              meshes is not None and meshes.group(1) == meshes.group(2)
              and int(meshes.group(1)) > 0,
              meshes.group(0) if meshes else "no-meshAssetsFound-key")
        check("accept/the-camera-height-agrees-with-the-slab-geometry",
              re.search(r"groundCrossCheck=agree/0\.\d+mm", d) is not None,
              re.search(r"groundCrossCheck=\S+", d).group(0))

        # THE FORMATTING LAW OF key=value, checked on the real string rather
        # than asserted in a comment: every reader in this project splits on
        # whitespace, so a value with a space in it truncates in silence.
        pairs = [t for t in d.split() if "=" in t]
        check("accept/no-key=value-token-contains-a-space",
              all(" " not in t for t in pairs), len(pairs))
        zeros = [t for t in pairs if re.match(r"^[A-Za-z]+=0(?!\.)", t)]
        check("accept/every-zero-on-the-done-line-carries-a-denominator",
              all("/" in t for t in zeros), zeros)
        built = re.search(r"piecesBuilt=(\d+)/(\d+)-planned", d)
        check("accept/a-plan-that-rendered-nothing-says-nothing-was-built",
              built is not None and built.group(1) == "0"
              and planned is not None and built.group(2) == planned.group(2)
              and "nothing-built" in d,
              (built.group(0) if built else "no-piecesBuilt-key") + " | " + d[:120])

    # ---- REJECT: a recipe nobody wrote is refused BY NAME ----
    p_missing, e_missing = resolve(root, "no-such-recipe-anywhere")
    check("reject/a-recipe-that-does-not-exist-is-refused",
          not p_missing and "no-recipe-file/" in e_missing, e_missing)
    check("reject/and-the-refusal-quotes-the-name-that-was-asked-for",
          "no-such-recipe-anywhere" in e_missing, e_missing)
    lines = []
    rc = plan_only(root, "no-such-recipe-anywhere", [], out=lines.append)
    check("reject/the-refusal-is-non-zero-and-says-nothing-measured",
          rc == 1 and any("NO-RECIPE" in l and "nothing measured" in l
                          for l in lines), lines)

    # ---- REJECT: a name that is a path is refused before it is joined ----
    for bad in ("../../etc/passwd", "sub/dir", "/abs/path", "", "  ",
                "run-recipe"):
        _p, e = resolve(root, bad)
        check("reject/a-name-that-is-not-a-plain-name-is-refused/%s"
              % (bad.strip() or "empty"), bool(e), e)

    # ---- REJECT: no Blender anywhere ----
    chosen3, tried3 = find_blender(cands, exists=lambda p: False,
                                   probe=lambda c: False)
    check("reject/no-blender-anywhere-returns-nothing-and-names-what-it-tried",
          chosen3 == "" and len(tried3) == len(cands), (chosen3, tried3))

    # ---- REJECT: the empty success this whole file exists to prevent ----
    check("reject/exit-0-with-no-new-png-is-an-EMPTY-SUCCESS-not-a-pass",
          png_verdict(3, 3, 0) == (False, "EMPTY-SUCCESS/exit0/no-new-png"),
          png_verdict(3, 3, 0))
    check("reject/a-non-zero-exit-fails-even-when-frames-landed",
          png_verdict(0, 4, 8)[0] is False, png_verdict(0, 4, 8))
    check("reject/a-missing-out-directory-counts-zero-rather-than-throwing",
          png_count(os.path.join(root, "no", "such", "dir")) == 0)

    # ---- THE BOUND THIS CANNOT COVER, ASSERTED SO IT CANNOT BE FORGOTTEN ----
    have_blender = find_blender(blender_candidates(), os.path.exists, _probe)[0]
    print("  %-64s %s" % ("note/blender-in-this-container",
                          have_blender or "NOT-INSTALLED/render-path-is-uncovered"))
    print("run-recipe selftest: %d passed, %d failed (of %d case(s)); "
          "the render itself is not among them"
          % (len(passed), len(failed), len(passed) + len(failed)))
    return 1 if failed else 0


def _usage():
    print(__doc__.strip().splitlines()[0])
    print("  python3 tools/art-recipes/run-recipe.py <recipe> --out DIR [args]")
    print("  python3 tools/art-recipes/run-recipe.py <recipe> --plan")
    print("  python3 tools/art-recipes/run-recipe.py --list")
    print("  python3 tools/art-recipes/run-recipe.py --selftest")
    print("  recipes here: " + (", ".join(list_recipes(ROOT)) or "none/0-found"))


def main(argv):
    args = argv[1:]
    if "--selftest" in args:
        return _selftest()
    if "--list" in args or not args:
        _usage()
        return 0 if args else 2
    asked = args[0]
    rest = args[1:]
    if "--plan" in rest:
        rest = [a for a in rest if a != "--plan"]
        return plan_only(ROOT, asked, rest)
    out_dir = ""
    extra = []
    i = 0
    while i < len(rest):
        if rest[i] == "--out" and i + 1 < len(rest):
            out_dir = rest[i + 1]
            i += 2
            continue
        extra.append(rest[i])
        i += 1
    if not out_dir:
        print("run-recipe refused: status=NO-OUTDIR recipeAsked=%s "
              "reason=missing-flag/--out nothing measured" % asked)
        return 2
    return run(ROOT, asked, out_dir, extra)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
