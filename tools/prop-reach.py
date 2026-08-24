#!/usr/bin/env python3
"""WHICH FETCHED PROP MODELS THE WORLD ACTUALLY ASKS FOR.

    python3 tools/prop-reach.py              # the report
    python3 tools/prop-reach.py --selftest   # check the instrument

WHY. `Assets/Props` holds 213 model files and `PropPrefab` turns EVERY one of
them into a `Resources/Props/Prop_<key>` prefab at build time, so all 213 are
reachable — the pipeline is not the constraint and never was. What decides
whether a model is in the game is whether some line of the Game layer names its
key, and nothing counted that.

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
under `Assets/Props` it is 213 and 39. Both numbers are true and they are
answers to different questions, so this prints per kit and never one total on
its own.
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


def models():
    """{key: (kit, stem)} for every model file on disk.

    The kit is the FIRST directory under `Assets/Props`, matching
    `PropPrefab.BuildOne`, so `oga-vehicles/free-low-poly-vehicles-pack/x.fbx`
    is `oga_vehicles_x` and not `free_low_poly_vehicles_pack_x`.
    """
    out = {}
    if not SRC.exists():
        return out
    for p in sorted(SRC.rglob("*")):
        if p.suffix.lower() not in EXTS:
            continue
        rel = p.relative_to(SRC)
        kit = rel.parts[0] if len(rel.parts) > 1 else "misc"
        out[norm(kit + "_" + p.stem)] = (kit, p.stem)
    return out


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
    keys = models()
    if not keys:
        print("prop-reach: no models under ledger/Assets/Props — nothing fetched yet")
        return 0
    lits = literals()
    route = classify(keys, lits)
    reached = {k for k, r in route.items() if r != "none"}

    print(f"prop-reach: {len(keys)} model(s) on disk, {len(reached)} named by the "
          f"Game layer, {len(keys) - len(reached)} with no name match "
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


def selftest():
    ok, fails = 0, []

    def check(label, cond):
        nonlocal ok
        if cond:
            ok += 1
        else:
            fails.append(label)

    check("normalises dashes and case", norm("City-Kit Roads") == "city_kit_roads")
    keys = models()
    check("finds models on disk", len(keys) > 100)
    check("kit is the first directory", "oga_vehicles_bus" in keys)
    lits = literals()
    check("reads Game literals", len(lits) > 1000)
    route = classify(keys, lits)

    # ACCEPTING FIRST. The expensive failure is a reach tool that calls
    # everything unreached, which reads exactly like a project that uses none of
    # its assets — and would send the next session at work already done.
    check("an exact literal is reached", route.get("city_kit_roads_light_curved") == "exact")
    check("a stem in an array is reached", route.get("base_mesh_park_bench") in ("exact", "stem"))
    check("not everything is unreached",
          sum(1 for r in route.values() if r != "none") > 20)
    # REJECTING. A kit nobody names must not be quietly counted as used.
    check("an unnamed model is unreached", route.get("city_kit_industrial_building_a") == "none")
    check("not everything is reached",
          sum(1 for r in route.values() if r == "none") > 20)

    # THE ACCEPTING CASE THAT CANNOT BE FOOLED BY A FIXTURE: every key the sim
    # demonstrably instantiated must be reported reached.
    placed = verdict_keys()
    if placed is None:
        print("prop-reach selftest: NO LANDED VERDICT — the strongest check did "
              "not run, and that is not the same as it passing")
    else:
        bad = [k for k in placed if route.get(k) == "none"]
        check(f"no key the sim placed is called unreached ({len(placed)} checked)",
              not bad)
        for k in bad:
            print("  FALSE NEGATIVE " + k)

    print(f"prop-reach selftest: {ok} passed, {len(fails)} failed")
    for f in fails:
        print("  FAILED " + f)
    return 1 if fails else 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    return report()


if __name__ == "__main__":
    sys.exit(main())
