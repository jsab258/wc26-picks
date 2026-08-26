#!/usr/bin/env python3
"""WHICH FETCHED PROP MODELS THE WORLD ACTUALLY ASKS FOR.

    python3 tools/prop-reach.py              # the report
    python3 tools/prop-reach.py --selftest   # check the instrument

WHY. `Assets/Props` holds 228 model FILES minting 213 distinct KEYS, and
`PropPrefab` turns every key into a `Resources/Props/Prop_<key>` prefab at build
time, so 213 are reachable and 15 are not reachable by any name at all — two
files claiming one key resolve last-wins. The pipeline is not the constraint and
never was. What decides whether a model is in the game is whether some line of
the Game layer names its key, and nothing counted that.

THE HEADLINE USED TO SAY "213 model(s) on disk" AND THAT WAS A KEY COUNT
WEARING A FILE COUNT'S NAME (fixed 26 Aug) — rule 3b's second half: a
denominator can describe something other than the set examined, and 15 files
were invisible in a report whose whole subject is which files are invisible.

This is rule 6 pointed at art instead of at code. `Brandish`, `MayFrisk`,
`Acquire` and `Misattribute` were built, tested and called by nothing; 25
industrial buildings sitting on disk for a town whose identity is its docks are
the same fault with a different file extension, and the ladder in `queue.md`
calls it out by name — a pipeline that CAN ingest better assets is not the same
as better assets ingested.

NAME-MATCHING, NOT TYPE-RESOLVING, and that is a real limit rather than a
disclaimer. `TryInstantiateProp` normalises its argument — lowercase, spaces and
dashes to underscores — and callers build keys three ways: a whole literal
(`"city_kit_roads_light_curved"`), a literal stem picked out of an array, and a
prefix concatenated with a stem (`"car_kit_" + stem`). So this looks for the
normalised key, then the normalised stem, then a prefix-plus-stem pair. A key
composed from parts that are themselves computed would be missed.

WHICH IS WHY THE ACCEPTING CASE IS THE LANDED VERDICT AND NOT A FIXTURE.
`kitAlbedo` names every distinct key the sim actually instantiated, so any key
in it that this tool calls unreached is a false negative, demonstrably. That
check runs in `--selftest` whenever a verdict is present — it cannot be fooled
by a fixture I wrote, which is the same argument the CS0426 lint's "run it
against the whole repository" rule is built on.

AND THE COUNT THAT WAS QUOTED AT ME WAS SCOPED, WHICH I NEARLY REPEATED WRONG.
`queue.md` said "89 fetched models on disk, six referenced". Six is right — for
the four CITY KITS alone, which is what that item was about. Across everything
under `Assets/Props` it is 228 files / 213 keys, 74 of them named (26 Aug; it
read 39 named when this paragraph was written, and the sentence decayed exactly
as rule 1's second corollary says a number in a comment does). Both scopes are
true and they answer different questions, so this prints per kit and never one
total on its own.
"""
import collections
import pathlib
import re
import sys

EXTS = {".fbx", ".obj", ".glb", ".gltf"}
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "ledger" / "Assets" / "Props"
GAME = ROOT / "ledger" / "Assets" / "Scripts" / "Game"
VERDICT = ROOT / "game-design" / "sim-shots" / "verdict.txt"


def norm(s):
    """`PropPrefab.Key`'s rule and `TryInstantiateProp`'s, which are the same
    rule written twice — the shape this project keeps finding wrong on the copy
    nobody looks at. If they ever diverge the miss falls through to primitive
    geometry rather than to an error, so nothing would report it."""
    return s.lower().replace(" ", "_").replace("-", "_")


def model_files(root=None):
    """[(key, (kit, stem), path)] for EVERY model file on disk, sorted.

    ONE WALK, and `models()` is built from it, so the FILE count and the KEY
    count are taken at the same instant and may therefore be divided. They are
    not the same number: measured 26 Aug, **228 files on disk mint 213 distinct
    keys**, because twelve keys are claimed by more than one file and the later
    path wins — exactly the last-wins resolution `prop-dimensions.kit_key_paths`
    documents for Unity's own enumeration. Fifteen files are unreachable in the
    game no matter what names them, and this tool called all 228 of them "213
    model(s) on disk", which is rule 3b's question — what did the denominator
    COUNT — answered wrong in the headline of the report.
    """
    root = pathlib.Path(root) if root else SRC
    out = []
    if not root.exists():
        return out
    for p in sorted(root.rglob("*")):
        if p.suffix.lower() not in EXTS:
            continue
        rel = p.relative_to(root)
        kit = rel.parts[0] if len(rel.parts) > 1 else "misc"
        out.append((norm(kit + "_" + p.stem), (kit, p.stem), p))
    return out


def models(root=None):
    """{key: (kit, stem)} for every model file on disk. LAST PATH WINS.

    The kit is the FIRST directory under `Assets/Props`, matching
    `PropPrefab.BuildOne`, so `oga-vehicles/free-low-poly-vehicles-pack/x.fbx`
    is `oga_vehicles_x` and not `free_low_poly_vehicles_pack_x`.

    `root` is a PARAMETER so the selftest can hand it a tree it built itself.
    The accepting fixture used to be `"oga_vehicles_bus" in keys` — a real
    shipped asset, asserting by name that it stays on disk under that kit,
    which a re-org or a prune breaks while saying the WALK is broken.
    """
    return {k: v for k, v, _p in model_files(root)}


def collisions(files=None):
    """{key: [path, ...]} for every key more than one file claims.

    A collision is not cosmetic: `PropPrefab` mints one prefab per KEY, so the
    shadowed files cannot be instantiated by any name at all. Reported rather
    than gated — which file wins is Unity's enumeration order, and a kit that
    ships two `Bus.fbx` is a fetch decision, not a fault this tool can rule on.
    """
    files = model_files() if files is None else files
    by = collections.defaultdict(list)
    for key, _ks, path in files:
        by[key].append(path)
    return {k: v for k, v in by.items() if len(v) > 1}


def literals(where=None):
    """Every normalised string literal in the Game layer.

    INTERPOLATED STRINGS INCLUDED, deliberately. `lint-shadow` threw all of
    `$"..."` away for a year with a docstring approving of it, and the done line
    — the largest concentration of Game-layer static reads in the project — went
    unchecked because of it. Here the risk runs the other way: a key named only
    inside an interpolation would read as unreached, which is a false alarm
    rather than a silent miss, but it is just as wrong.
    """
    where = where or GAME
    lits = set()
    for f in sorted(pathlib.Path(where).glob("*.cs")):
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in re.findall(r'"([^"\\\n]*)"', text):
            if m.strip():
                lits.add(norm(m))
    return lits


def classify(keys, lits):
    """{key: route}, route in exact/stem/prefix/none."""
    prefixes = {l for l in lits if l.endswith("_")}
    out = {}
    for key, (_kit, stem) in keys.items():
        if key in lits:
            out[key] = "exact"
        elif norm(stem) in lits:
            out[key] = "stem"
        elif any(key.startswith(p) and key[len(p):] in lits for p in prefixes):
            out[key] = "prefix"
        else:
            out[key] = "none"
    return out


def verdict_keys(path=None):
    """Distinct prop keys the last landed run actually instantiated.

    Reads `kitAlbedo=[key:albedo/...]`. The `+Nmore` tail is a CAP and it is
    dropped rather than parsed — a truncation read as a name is exactly the
    `head -3` fault, and the caller is told how many were legible.
    """
    path = pathlib.Path(path) if path else VERDICT
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"kitAlbedo=\[([^\]]*)\]", text)
    if not m:
        return None
    got = set()
    for part in m.group(1).split("/"):
        if ":" not in part:
            continue
        name = part.split(":")[0]
        if name.endswith("more"):
            continue
        got.add(norm(name))
    return got


def report():
    files = model_files()
    keys = models()
    if not keys:
        print("prop-reach: no models under ledger/Assets/Props — nothing fetched yet")
        return 0
    lits = literals()
    route = classify(keys, lits)
    reached = {k for k, r in route.items() if r != "none"}
    coll = collisions(files)
    shadowed = sum(len(v) - 1 for v in coll.values())

    # BOTH DENOMINATORS, BECAUSE THEY ARE NOT THE SAME NUMBER and the
    # difference is 15 files that no name can reach.
    print(f"prop-reach: {len(files)} model file(s) on disk minting {len(keys)} "
          f"key(s) ({shadowed} shadowed by {len(coll)} key collision(s), last "
          f"path wins), {len(reached)} key(s) named by the Game layer, "
          f"{len(keys) - len(reached)} with no name match "
          f"({len(lits)} literal(s) scanned)")

    per = collections.defaultdict(lambda: [0, 0])
    for key, (kit, _stem) in keys.items():
        per[kit][0] += 1
        if key in reached:
            per[kit][1] += 1
    print(f"\n  {'kit':<24}{'models':>8}{'named':>8}{'unused':>8}")
    for kit in sorted(per, key=lambda k: (per[k][1] - per[k][0], k)):
        total, hit = per[kit]
        print(f"  {kit:<24}{total:>8}{hit:>8}{total - hit:>8}")

    # THE KITS NOBODY HAS TOUCHED AT ALL, named, because "25 unused" and "an
    # entire kit unused" are different findings and only the second one says
    # a whole idea never landed.
    whole = [k for k in sorted(per) if per[k][1] == 0]
    if whole:
        print("\n  ENTIRE KIT UNREACHED: " + ", ".join(whole))

    # WHICH ROUTE EACH KEY TOOK — a COUNT over keys, printed as a series
    # rather than summarised, because `prefix` reading 0 is the interesting
    # entry and no total can show it. Measured 26 Aug: exact=63 stem=11
    # prefix=0 none=139. The prefix branch has never fired on this corpus and
    # structurally almost cannot: the remainder after a `kit_` prefix IS the
    # normalised stem, which the stem branch matched one line earlier. It is
    # kept because `classify` is name-matching and a kit whose directory name
    # is a prefix of another's would reach it — but it is not coverage, and a
    # reader counting four branches as four tested paths would be wrong.
    counts = collections.Counter(route.values())
    print("\n  routes (count of keys): "
          + " ".join("%s=%d" % (r, counts.get(r, 0))
                     for r in ("exact", "stem", "prefix", "none")))

    # THE SHADOWED FILES, NAMED. A key collision is silent everywhere else:
    # the prefab exists, the name resolves, and the file that lost is simply
    # never in the game. The cap announces itself.
    if coll:
        print(f"\n  KEY COLLISIONS — {len(coll)} key(s) claimed by 2+ files, "
              f"{shadowed} file(s) unreachable by any name:")
        shown = sorted(coll.items())[:5]
        for key, paths in shown:
            rels = [str(p.relative_to(SRC)) for p in paths]
            print(f"    {key}: {len(paths)} files, wins={rels[-1]}, "
                  f"shadowed={', '.join(rels[:-1])}")
        if len(coll) > 5:
            print(f"    (+{len(coll) - 5} more of {len(coll)} not shown)")

    placed = verdict_keys()
    if placed is None:
        print("\n  no landed verdict to check against — the static read stands alone")
    else:
        false_neg = sorted(k for k in placed if route.get(k) == "none")
        print(f"\n  cross-checked against the landed verdict: {len(placed)} key(s) "
              f"the sim actually placed, {len(false_neg)} of them called unreached")
        for k in false_neg:
            print("    FALSE NEGATIVE " + k)
    return 0


#: THE SYNTHETIC WORLD — a props tree and a Game file, both written by the
#: selftest, covering every route `classify` can take. Nothing here exists on
#: disk in the project, so doing the work this tool prompts (naming a fetched
#: model, pruning one, re-dressing a street) cannot make any of it move.
#:
#:   path under the fake Props root      expected key            expected route
_SYNTH_TREE = (
    ("synthkit/Alpha.fbx",               "synthkit_alpha",       "exact"),
    # COLLIDES with Alpha.fbx above, and the STEM CASE DIFFERS ON PURPOSE:
    # the value `models()` keeps is (kit, stem), so two files with identical
    # stems make last-wins unobservable — which is how the first version of
    # this rung passed a break test that reversed the resolution order.
    ("synthkit/sub/alpha.obj",           "synthkit_alpha",       "exact"),
    ("synthkit/Gamma-Three.glb",         "synthkit_gamma_three", "stem"),
    ("synthkit/nested/Beta Two.obj",     "synthkit_beta_two",    "none"),
    ("synth/kit_Delta.fbx",              "synth_kit_delta",      "prefix"),
    ("synthkit/Zeta.fbx",                "synthkit_zeta",        "exact"),   # named in $"..."
    ("Loose.fbx",                        "misc_loose",           "none"),
    ("synthkit/notes.txt",               None,                   None),      # not a model
)

#: The fake Game file. Each literal is the composition shape it stands for,
#: written the way the real callers write it — including the interpolated one,
#: which is the case `lint-shadow` threw away for a year.
_SYNTH_CS = '''// synthetic — no such kit exists anywhere in this project
void Dress()
{
    TryInstantiateProp("synthkit_alpha");                 // whole key
    foreach (var stem in new[] { "gamma_three" })         // stem in an array
        TryInstantiateProp("synthkit_" + stem);
    TryInstantiateProp("synth_kit_" + "delta");           // prefix + stem
    TryInstantiateProp($"synthkit_zeta");                 // inside an interpolation
    // synthkit_beta_two is named NOWHERE that counts.
}
'''


def selftest():
    ok, fails = 0, []

    def check(label, cond, got=""):
        """PRINTS THE NUMBER ON THE PASS AS WELL AS THE FAIL. This printed
        only `N passed, M failed` until 26 Aug, so every green rung was a word
        with no measurement under it and "the corpus has models" could not be
        told from "the corpus has one"."""
        nonlocal ok
        print(("  ok   " if cond else "  FAIL ") + label + (" — " + got if got else ""))
        if cond:
            ok += 1
        else:
            fails.append(label)

    check("normalises dashes and case", norm("City-Kit Roads") == "city_kit_roads",
          "City-Kit Roads -> " + norm("City-Kit Roads"))

    # -- ACCEPTING FIRST, ON A WORLD THIS FILE BUILT -------------------
    #
    # WHAT THIS REPLACES, kept in words because all three read as careful:
    #
    #     check("finds models on disk", len(keys) > 100)
    #     check("kit is the first directory", "oga_vehicles_bus" in keys)
    #     check("an exact literal is reached",
    #           route.get("city_kit_roads_light_curved") == "exact")
    #     check("a stem in an array is reached",
    #           route.get("base_mesh_park_bench") in ("exact", "stem"))
    #     check("not everything is unreached", ... != "none" > 20)
    #     check("the real corpus still has unreached models", ... == "none" > 20)
    #
    # Every one of those is an ACCEPTING fixture asserting a value of an
    # artifact this project intends to keep changing. Three name a shipped
    # asset and require it to stay on disk AND stay referenced, so a
    # re-dressing pass that stops placing a bench turns the reach TOOL red.
    # The floor of 100 forbids ever pruning the corpus. And the last one is an
    # INVERSE RATCHET: it requires at least 21 fetched models to stay unplaced
    # for ever, which is the exact opposite of what M17.10 is for — sitting
    # ten lines under this file's own paragraph explaining why the REJECTING
    # case was made synthetic, in these words: "a rejecting case pinned to a
    # real asset asserts that the asset stays UNUSED, which is the opposite of
    # what this project wants to be true". The same assertion in aggregate,
    # under its own refutation.
    #
    # The world below is written into a temporary directory instead, so the
    # accepting cases test the READERS and the CLASSIFIER rather than today's
    # corpus — and the live corpus keeps the one accepting case that cannot be
    # fooled by anything written here: the landed verdict, at the bottom.
    import tempfile
    with tempfile.TemporaryDirectory() as td:                 # cleanup registered
        root = pathlib.Path(td) / "Props"
        for rel, _key, _route in _SYNTH_TREE:
            f = root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("synthetic", encoding="utf-8")
        gamedir = pathlib.Path(td) / "Game"
        gamedir.mkdir()
        (gamedir / "SynthHost.cs").write_text(_SYNTH_CS, encoding="utf-8")

        want_files = [t for t in _SYNTH_TREE if t[1]]
        want_keys = {t[1] for t in want_files}
        sfiles = model_files(root)
        skeys = models(root)
        scoll = collisions(sfiles)
        check("SYNTHETIC — the walk mints a key per model file and ignores the rest",
              len(sfiles) == len(want_files) and set(skeys) == want_keys,
              "%d file(s) -> %d key(s), wanted %d -> %d"
              % (len(sfiles), len(skeys), len(want_files), len(want_keys)))
        check("SYNTHETIC — kit is the FIRST directory, however deep the file sits",
              skeys.get("synthkit_beta_two", ("", ""))[0] == "synthkit"
              and "misc_loose" in skeys,
              "nested/Beta Two.obj -> synthkit_beta_two; a loose file -> misc_*")
        # THE COLLISION COUNTER, WITH ITS OWN ACCEPTING CASE. Two files claim
        # `synthkit_alpha` and the later path must win, which is the fault the
        # live corpus has 12 of and the report never mentioned.
        # AND THE WINNER IS READ OUT OF `models()`, NOT OUT OF THE COLLISION
        # LIST. The first version asserted `scoll[key][-1].name`, which is
        # sorted by construction and therefore says "last wins" no matter what
        # `models()` does — it passed a break test that reversed the
        # resolution outright. Suspect your own probe: the assertion has to
        # read the value the rest of the tool actually uses.
        check("SYNTHETIC — two files claiming one key collide, and the LAST "
              "path is the one models() keeps",
              len(scoll) == 1 and len(scoll.get("synthkit_alpha", [])) == 2
              and skeys.get("synthkit_alpha") == ("synthkit", "alpha"),
              "%d collision(s), models() kept stem %r, sorted-last file is %s"
              % (len(scoll), (skeys.get("synthkit_alpha") or ("?", "?"))[1],
                 scoll.get("synthkit_alpha", ["?"])[-1].name))

        slits = literals(gamedir)
        check("SYNTHETIC — the literal reader finds every composition shape",
              {"synthkit_alpha", "gamma_three", "synthkit_", "synth_kit_",
               "delta", "synthkit_zeta"} <= slits,
              "%d literal(s) read from one synthetic file" % len(slits))

        # THE LADDER: every route in one run, over one world, from one vantage.
        # A rung on its own says nothing — "exact" passing proves nothing unless
        # the key nothing names comes back "none" in the same classification.
        sroute = classify(skeys, slits)
        # UNIQUE KEYS, not files: two of the fixture files mint one key on
        # purpose, and checking it twice would inflate the passed count with
        # the same reading — a denominator counting something other than what
        # was examined, which is the fault this whole batch is about.
        seen = []
        for _rel, key, want in _SYNTH_TREE:
            if key is None or key in seen:
                continue
            seen.append(key)
            check("SYNTHETIC ROUTE — %s is %s" % (key, want),
                  sroute.get(key) == want, "got %s" % sroute.get(key))
        # REJECTING, and synthetic for the reason this file already gives: a
        # key on no disk anywhere can never be reached by anyone.
        fake = {"nosuchkit_nosuchmodel_zzz": ("nosuchkit", "nosuchmodel-zzz")}
        check("SYNTHETIC REJECTING — a key nothing names is unreached",
              classify(fake, slits)["nosuchkit_nosuchmodel_zzz"] == "none",
              "nosuchkit_nosuchmodel_zzz -> "
              + classify(fake, slits)["nosuchkit_nosuchmodel_zzz"])
        # AND THE RUNGS MUST STAND APART: a classifier that answered "exact"
        # for everything would pass four of the rungs above. Both extremes are
        # what the pair of live floors (>20 reached, >20 unreached) was reaching
        # for, and this asks it of a world that cannot be improved.
        got = collections.Counter(sroute.values())
        check("SYNTHETIC LADDER — the routes are not all one answer",
              len([r for r in got if got[r]]) >= 3,
              "distribution " + " ".join("%s=%d" % (r, got.get(r, 0))
                                         for r in ("exact", "stem", "prefix", "none")))

    # -- THE LIVE CORPUS, AS READINGS -------------------------------------
    #
    # NOT BOUNDS. Every one of these numbers moves when the project does its
    # job — fetching, pruning, dressing a street — so they are printed with
    # their denominators and gated only where a number means the INSTRUMENT
    # examined nothing, which is rule 3b rather than a ratchet.
    files = model_files()
    keys = models()
    lits = literals()
    route = classify(keys, lits)
    counts = collections.Counter(route.values())
    coll = collisions(files)
    print("  .. live corpus reading, NOT a bound: %d file(s) -> %d key(s) "
          "(%d shadowed by %d collision(s)); routes %s; %d Game literal(s)"
          % (len(files), len(keys), sum(len(v) - 1 for v in coll.values()), len(coll),
             " ".join("%s=%d" % (r, counts.get(r, 0))
                      for r in ("exact", "stem", "prefix", "none")),
             len(lits)))
    if not files:
        print("  .. NO MODELS ON DISK — the live rungs measured nothing, and "
              "that is not the same as them passing. The synthetic rungs above "
              "still ran.")
    else:
        check("LIVE — the walk turned files into keys (a zero here is the "
              "instrument, not the corpus)",
              len(keys) > 0, "%d file(s) -> %d key(s)" % (len(files), len(keys)))
        check("LIVE — there are Game literals to match against (zero would "
              "report the whole corpus unreached)",
              len(lits) > 0, "%d literal(s)" % len(lits))

    # THE ACCEPTING CASE THAT CANNOT BE FOOLED BY A FIXTURE: every key the sim
    # demonstrably instantiated must be reported reached. It is the only live
    # assertion here, and it is safe to be one because it compares this tool
    # against the GAME rather than against an asset — improving the art can
    # only add keys to it.
    placed = verdict_keys()
    if placed is None:
        print("prop-reach selftest: NO LANDED VERDICT — the strongest check did "
              "not run, and that is not the same as it passing")
    else:
        bad = [k for k in placed if route.get(k) == "none"]
        check("LIVE — no key the sim placed is called unreached (%d checked)"
              % len(placed), not bad, "%d false negative(s)" % len(bad))
        for k in bad:
            print("  FALSE NEGATIVE " + k)

    print(f"prop-reach selftest: {ok} passed, {len(fails)} failed "
          f"({len(_SYNTH_TREE)} synthetic file(s) + 1 synthetic Game file, "
          f"built here, no asset)")
    for f in fails:
        print("  FAILED " + f)
    return 1 if fails else 0


def main():
    # `| head` closes the pipe and Python turns that into a traceback, which in
    # this project is not a cosmetic problem: a tool that prints a stack trace
    # after a correct run is a tool somebody spends twenty minutes on before
    # noticing it worked. Same reason every other instrument here says what it
    # did rather than only what it found.
    import signal
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (AttributeError, ValueError):
        pass                      # not POSIX, or not on the main thread
    if "--selftest" in sys.argv:
        return selftest()
    return report()


if __name__ == "__main__":
    sys.exit(main())
