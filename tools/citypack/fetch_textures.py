#!/usr/bin/env python3
"""Fetch a CC0 texture set for the surfaces `AssetLibrary` already asks for.

M17.6. The completeness audit on 2026-07-31 found zero image files in the
project: every surface in the game is a small tiling noise pattern generated at
runtime. `AssetLibrary` has resolved a real pack from
`StreamingAssets/CityPack` since it was written, with a procedural fallback, so
**a pack drops in with no code change** — the hook was built months ago and
nothing was ever put in it.

WHY THIS IS A CI JOB AND NOT A SCRIPT I RUN HERE. Every asset host is blocked
from the dev container, exactly like HuggingFace:

    ambientcg.com   000    api.polyhaven.com  000
    cc0textures.com 000    fonts.google.com   000

So this has the same shape as the voice pipeline, and it inherits that
pipeline's most expensive lesson. Fifteen CI runs went into guessing at a corpus
because I had no way to ASK it anything; the day was fixed by building an
`--inventory` mode that answered every question at once and cost one run.

    python3 tools/citypack/fetch_textures.py --inventory   # ask, decide later
    python3 tools/citypack/fetch_textures.py --fetch       # take the decisions

`--inventory` reads the catalogue and writes `tools/citypack/candidates.json`
without downloading a single image. Then the choice is made HERE, locally, in
seconds, from evidence — and `--fetch` takes named assets rather than sweeping.

DESTRUCTIVE OPERATIONS ARE SCOPED TO WHAT THIS RUN PRODUCED. A CI job on this
project once deleted 24 clips Jafar had already listened to and reported
success. Nothing here removes a file it did not just write, and a run that fills
none of its targets exits non-zero — the voice pipeline's invariant 7, which was
open for a day because a `--who` run that banked nothing still saw everybody
else's clips on disk and called itself green.
"""
import argparse
import io
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PACK = ROOT / "ledger" / "Assets" / "StreamingAssets" / "CityPack"
HERE = pathlib.Path(__file__).resolve().parent

API = "https://ambientcg.com/api/v2/full_json"

# The twelve logical surfaces `AssetLibrary` asks for, and what each one is in
# the language of a texture library. Search terms rather than asset ids on
# purpose: an id I typed from memory is an id that is wrong, and the whole point
# of the inventory pass is that the catalogue tells us what exists.
SURFACES = {
    "asphalt":    ["Asphalt"],
    "sidewalk":   ["PavingStones", "Concrete"],
    "kerb":       ["Concrete", "Rock"],
    "brick_red":  ["Bricks"],
    "brick_grey": ["Bricks", "Concrete"],
    "plaster":    ["Plaster"],
    "concrete":   ["Concrete"],
    "wood":       ["Planks", "Wood"],
    "roof":       ["RoofingTiles"],
    "metal":      ["Metal"],
    "glass":      ["Glass", "Metal"],
    "window":     ["Glass", "Metal"],
}

# 1K is the right size and this is a decision rather than a default. Seven
# districts of buildings at 2K is a download and a memory budget bought for
# detail nobody sees: the art direction is fog, rain and restricted palette
# doing the heavy lifting, and the camera is a street-level third person. 1K
# tiling at the tiling rates in `SurfaceSpec` reads correctly at that distance.
RESOLUTION = "1K-JPG"


def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "ledger-citypack/1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def catalogue():
    """THE WHOLE CATALOGUE, ONCE. Every material id and the sizes it publishes.

    The first inventory run was already the right idea and it was still too
    narrow: it asked eleven search terms, and two of them — `PavingStones` and
    `RoofingTiles` — came back with ZERO assets. Sidewalk and roof would have
    silently had no texture, which is precisely the class of surprise a blind
    fetch produces and the reason the voice pipeline burned fifteen runs.

    Guessing a better search term is the same mistake one notch smaller. So:
    pull the entire material list once, write it down, and every question after
    that — what is paving called here, is there a roof at all, which brick — is
    answered locally in seconds with no run at all.

    Metadata only. No image is downloaded."""
    out, offset, limit = [], 0, 200
    print("catalogue — every material, metadata only\n")
    while offset < 4000:
        url = (API + f"?type=Material&limit={limit}&offset={offset}"
               + "&include=downloadData")
        try:
            data = json.loads(get(url))
        except Exception as e:                                   # noqa: BLE001
            print(f"  FAILED at offset {offset}: {type(e).__name__}: {e}")
            break
        assets = data.get("foundAssets", [])
        if not assets:
            break
        for a in assets:
            aid = a.get("assetId")
            if not aid:
                continue
            zips = (a.get("downloadFolders", {}).get("default", {})
                     .get("downloadFiletypeCategories", {})
                     .get("zip", {}).get("downloads", []))
            out.append({"id": aid,
                        "sizes": sorted({z.get("attribute") for z in zips if z.get("attribute")})})
        print(f"  offset {offset:5d}  +{len(assets)} -> {len(out)} total")
        if len(assets) < limit:
            break
        offset += limit

    path = HERE / "catalogue.json"
    path.write_text(json.dumps({"resolution": RESOLUTION, "assets": out}, indent=1),
                    encoding="utf-8")
    usable = sum(1 for a in out if RESOLUTION in a["sizes"])
    print(f"\n{len(out)} material(s), {usable} publish {RESOLUTION}")
    print(f"wrote {path.relative_to(ROOT)}")
    if usable == 0:
        print("NOTHING USABLE — the catalogue answered and had nothing at this "
              "resolution. A finding, not a pass.")
        return 1
    return 0


def inventory():
    """Ask the catalogue what exists, and write it down. No images."""
    wanted = sorted({t for terms in SURFACES.values() for t in terms})
    out = {"resolution": RESOLUTION, "terms": {}}
    print(f"inventory — {len(wanted)} category term(s), metadata only\n")
    for term in wanted:
        url = (API + "?type=Material&limit=60&include=downloadData"
               + "&q=" + urllib.parse.quote(term))
        try:
            data = json.loads(get(url))
        except Exception as e:                                   # noqa: BLE001
            print(f"  {term:<16} FAILED: {type(e).__name__}: {e}")
            out["terms"][term] = {"error": f"{type(e).__name__}: {e}"}
            continue
        assets = data.get("foundAssets", [])
        rows = []
        for a in assets:
            aid = a.get("assetId")
            if not aid:
                continue
            # Only entries that actually publish the size we want, so the fetch
            # step cannot pick something it then cannot download.
            dl = (a.get("downloadFolders", {}).get("default", {})
                   .get("downloadFiletypeCategories", {}))
            zips = dl.get("zip", {}).get("downloads", [])
            has = [z.get("attribute") for z in zips]
            rows.append({"id": aid, "sizes": has,
                         "hasWanted": RESOLUTION in has})
        rows.sort(key=lambda r: (not r["hasWanted"], r["id"]))
        out["terms"][term] = {"count": len(rows), "assets": rows[:40]}
        usable = sum(1 for r in rows if r["hasWanted"])
        print(f"  {term:<16} {len(rows):3d} asset(s), {usable:3d} publish {RESOLUTION}")
        for r in rows[:5]:
            print(f"      {r['id']}")

    path = HERE / "candidates.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nwrote {path.relative_to(ROOT)}")
    # AN INVENTORY THAT FOUND NOTHING IS A FAILED RUN, not an empty one. The
    # voice pipeline shipped a green run that had produced zero clips because
    # the verdict only looked at a total that included everybody else's.
    usable = sum(1 for t in out["terms"].values()
                 for a in t.get("assets", []) if a.get("hasWanted"))
    if usable == 0:
        print("NOTHING USABLE FOUND — the catalogue answered, and it had nothing "
              "at this resolution. That is a finding, not a pass.")
        return 1
    return 0


def load_choices():
    """The decisions, made locally from `candidates.json`, committed as data."""
    path = HERE / "choices.json"
    if not path.exists():
        print(f"no {path.relative_to(ROOT)} — run --inventory first, then choose")
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def fetch():
    choices = load_choices()
    if choices is None:
        return 1
    textures = PACK / "textures"
    materials = PACK / "materials"
    textures.mkdir(parents=True, exist_ok=True)
    materials.mkdir(parents=True, exist_ok=True)

    written, failed, attribution = [], [], {}
    for logical, asset_id in sorted(choices.get("surfaces", {}).items()):
        if logical not in SURFACES:
            print(f"  {logical:<12} SKIP — not a surface AssetLibrary asks for")
            continue
        url = (API + "?type=Material&include=downloadData&q="
               + urllib.parse.quote(asset_id))
        try:
            data = json.loads(get(url))
            asset = next(a for a in data.get("foundAssets", [])
                         if a.get("assetId") == asset_id)
            zips = (asset["downloadFolders"]["default"]
                    ["downloadFiletypeCategories"]["zip"]["downloads"])
            entry = next(z for z in zips if z.get("attribute") == RESOLUTION)
            blob = get(entry["downloadLink"], timeout=180)
        except Exception as e:                                   # noqa: BLE001
            print(f"  {logical:<12} FAILED {asset_id}: {type(e).__name__}: {e}")
            failed.append(logical)
            continue

        # The colour map only. Normal, roughness and AO maps are a second
        # decision and a much larger download, and the Standard shader path in
        # `AssetLibrary` reads albedo — shipping maps nothing samples would be
        # weight for nothing.
        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                name = next(n for n in z.namelist()
                            if n.lower().endswith((".jpg", ".png"))
                            and "color" in n.lower())
                img = z.read(name)
        except Exception as e:                                   # noqa: BLE001
            print(f"  {logical:<12} FAILED to read colour map from {asset_id}: {e}")
            failed.append(logical)
            continue

        ext = ".jpg" if name.lower().endswith(".jpg") else ".png"
        dest = textures / (logical + ext)
        dest.write_bytes(img)
        written.append(dest)
        attribution[logical] = {
            "assetId": asset_id,
            "source": "ambientCG",
            "licence": "CC0 1.0 Universal",
            "url": f"https://ambientcg.com/view?id={asset_id}",
            "resolution": RESOLUTION,
            "file": dest.name,
        }
        print(f"  {logical:<12} ok  {asset_id}  {len(img) // 1024} KiB  -> {dest.name}")

    (PACK / "ATTRIBUTION.json").write_text(
        json.dumps({"note": "Sources for every file in this pack. "
                            "THIRD-PARTY.md is the human-readable copy and both "
                            "must agree; tools/citypack/pack_check.py enforces it.",
                    "surfaces": attribution}, indent=1), encoding="utf-8")

    print(f"\n{len(written)} written, {len(failed)} failed")
    # INVARIANT 7, from the voice pipeline. A run that filled none of its
    # targets must fail even if the directory is full of earlier successes.
    if not written:
        print("NOTHING WAS WRITTEN — this run failed whatever is on disk.")
        return 1
    if failed:
        print("PARTIAL — some surfaces did not arrive: " + ", ".join(failed))
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue", action="store_true",
                    help="pull EVERY material id once; every later question is local")
    ap.add_argument("--inventory", action="store_true",
                    help="ask the catalogue what exists; download nothing")
    ap.add_argument("--fetch", action="store_true",
                    help="download the assets named in choices.json")
    args = ap.parse_args()
    if args.catalogue:
        return catalogue()
    if args.inventory:
        return inventory()
    if args.fetch:
        return fetch()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
