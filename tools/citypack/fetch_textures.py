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


def dig(node, *keys):
    """Walk nested dicts without assuming a shape.

    `d.get("k", {})` returns NONE, not `{}`, when the key is present with a
    null value — so the obvious chain of `.get(...)` calls raises
    AttributeError on the first asset whose `downloadFolders` is null. The
    catalogue run died on exactly that and wrote no file at all, which meant a
    five-minute run produced nothing to read: no catalogue, no candidate list,
    and an artefact upload with nothing to upload.

    The per-term inventory has the same chain and survived only because the
    query-filtered results happened not to contain a null."""
    for k in keys:
        if not isinstance(node, dict):
            return None
        node = node.get(k)
    return node


def sizes_of(asset):
    """Which download sizes this asset publishes. Empty when it publishes none,
    which is a fact about the asset rather than an error."""
    zips = dig(asset, "downloadFolders", "default",
               "downloadFiletypeCategories", "zip", "downloads")
    if not isinstance(zips, list):
        return []
    return sorted({z.get("attribute") for z in zips
                   if isinstance(z, dict) and z.get("attribute")})


def link_for(asset, resolution):
    zips = dig(asset, "downloadFolders", "default",
               "downloadFiletypeCategories", "zip", "downloads")
    if not isinstance(zips, list):
        return None
    for z in zips:
        if isinstance(z, dict) and z.get("attribute") == resolution:
            return z.get("downloadLink")
    return None


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
    out, offset, limit, note = [], 0, 200, "complete"
    seen = set()
    print("catalogue — every material, metadata only\n")
    try:
        while offset < 4000:
            url = (API + f"?type=Material&limit={limit}&offset={offset}"
                   + "&include=downloadData")
            try:
                data = json.loads(get(url))
            except Exception as e:                               # noqa: BLE001
                note = f"stopped at offset {offset}: {type(e).__name__}: {e}"
                print("  " + note)
                break
            assets = data.get("foundAssets") if isinstance(data, dict) else None
            if not assets:
                note = f"catalogue ended at offset {offset}"
                break
            fresh = 0
            for a in assets:
                aid = a.get("assetId") if isinstance(a, dict) else None
                if not aid or aid in seen:
                    continue
                seen.add(aid)
                fresh += 1
                # AND THE DOWNLOAD LINK, so a later fetch never has to ask a
                # second endpoint what this asset's zip is called. Recording it
                # here is what turns `--fetch` into twelve downloads from
                # committed data instead of twelve queries that can lie.
                out.append({"id": aid, "sizes": sizes_of(a),
                            "link": link_for(a, RESOLUTION)})
            print(f"  offset {offset:5d}  +{len(assets)} ({fresh} new) -> {len(out)} total")
            # AN API THAT IGNORES `offset` WOULD LOOP FOREVER returning the same
            # page. Nothing new means stop, whatever the page length says.
            if fresh == 0 or len(assets) < limit:
                note = ("offset appears to be ignored — the same page came back"
                        if fresh == 0 else "complete")
                break
            offset += limit
    except Exception as e:                                       # noqa: BLE001
        # WRITE WHAT WE HAVE REGARDLESS. The first attempt died on an
        # AttributeError mid-walk and produced no file at all, so a five-minute
        # run left nothing to read. A partial catalogue is worth having; an
        # exception that eats the evidence is not.
        note = f"aborted: {type(e).__name__}: {e}"
        print("  " + note)

    path = HERE / "catalogue.json"
    path.write_text(json.dumps({"resolution": RESOLUTION, "note": note,
                                "assets": out}, indent=1), encoding="utf-8")
    usable = sum(1 for a in out if RESOLUTION in a["sizes"])
    print(f"\n{len(out)} material(s), {usable} publish {RESOLUTION}")
    print(f"wrote {path.relative_to(ROOT)}")
    if usable == 0:
        print("NOTHING USABLE — the catalogue answered and had nothing at this "
              "resolution. A finding, not a pass.")
        return 1
    return 0


def inventory():
    """Per-term search. SUPERSEDED BY `--catalogue`, AND NOT TO BE TRUSTED.

    This asks `q=<term>`, and that endpoint has now been wrong three times: zero
    `PavingStones` against 162 in the catalogue, zero `RoofingTiles` against 31,
    and then twelve exact-id lookups that matched nothing at all. `--catalogue`
    answers the same questions from the list endpoint, which has never been
    wrong here, and `choices.json` is made from that.

    It stays because a search that disagrees with the catalogue is itself worth
    seeing, and it is cheap. But `candidates.json` is a record of what the
    search SAID, not of what the library HOLDS, and the file says so."""
    wanted = sorted({t for terms in SURFACES.values() for t in terms})
    out = {"resolution": RESOLUTION,
           "_": "WHAT THE SEARCH ENDPOINT SAID, which has disagreed with the "
                "library three times. catalogue.json is the evidence; this is "
                "a second opinion from a witness with a record.",
           "terms": {}}
    print(f"inventory — {len(wanted)} category term(s), metadata only")
    print("NOTE: the q= endpoint has been wrong three times; "
          "catalogue.json is the source of truth\n")
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
            has = sizes_of(a)
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


def links_for(ids):
    """Download links for exactly these asset ids, from the LIST endpoint.

    THE SEARCH ENDPOINT LIED FOR THE THIRD TIME. `--fetch` used to resolve each
    choice with `?q=<assetId>` and take the entry whose `assetId` matched. Every
    one of the twelve raised a bare `StopIteration` — no match in the results —
    in six seconds flat, so the queries answered promptly and answered with the
    wrong thing. The same endpoint had already reported zero `PavingStones` when
    the catalogue held 162, and zero `RoofingTiles` against 31.

    Twice is a coincidence; three times is a rule. Nothing in the fetch path
    asks `q=` any more.

    The list endpoint — `type=Material&limit&offset&include=downloadData`, with
    no query — is the call that produced all 2,005 materials, so it is the one
    that gets used. It costs about eleven pages, which is a minute of a job that
    already budgets thirty.

    AND IT SAYS WHAT IT DID NOT FIND. A bare `StopIteration` with no message is
    why the first failure needed a CI log dug out of a truncated window to
    diagnose at all."""
    want, found = set(ids), {}
    offset, limit = 0, 200
    print(f"  resolving {len(want)} link(s) from the list endpoint")
    while offset < 4000 and len(found) < len(want):
        url = (API + f"?type=Material&limit={limit}&offset={offset}"
               + "&include=downloadData")
        try:
            data = json.loads(get(url))
        except Exception as e:                                   # noqa: BLE001
            print(f"    offset {offset}: {type(e).__name__}: {e} — stopping")
            break
        assets = data.get("foundAssets") if isinstance(data, dict) else None
        if not assets:
            break
        for a in assets:
            aid = a.get("assetId") if isinstance(a, dict) else None
            if aid in want and aid not in found:
                link = link_for(a, RESOLUTION)
                if link:
                    found[aid] = link
        offset += limit
        if len(assets) < limit:
            break
    print(f"    {len(found)}/{len(want)} resolved")
    for aid in sorted(want - set(found)):
        print(f"    NOT FOUND in the list endpoint: {aid}")
    return found


def load_choices():
    """The decisions, made locally from `candidates.json`, committed as data."""
    path = HERE / "choices.json"
    if not path.exists():
        print(f"no {path.relative_to(ROOT)} — run --inventory first, then choose")
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def validate():
    """Every chosen id exists and publishes the wanted size — checked against
    the committed catalogue, with no network at all.

    This is the whole payoff of pulling the catalogue once. A typo in
    `choices.json` used to be discoverable only by spending a CI run and
    reading which surface came back empty; now it is a local command that takes
    a second, and the fetch refuses to start without it."""
    choices = load_choices()
    if choices is None:
        return 1
    path = HERE / "catalogue.json"
    if not path.exists():
        print("no catalogue.json — run --catalogue first; skipping validation")
        return 0
    cat = {a["id"]: a.get("sizes", [])
           for a in json.loads(path.read_text(encoding="utf-8")).get("assets", [])}
    want = choices.get("resolution", RESOLUTION)
    bad = []
    for surface, aid in sorted(choices.get("surfaces", {}).items()):
        if aid not in cat:
            bad.append(f"{surface}: {aid} is not in the catalogue")
        elif want not in cat[aid]:
            bad.append(f"{surface}: {aid} does not publish {want} ({cat[aid]})")
        else:
            print(f"  ok  {surface:<12} {aid}")
    for b in bad:
        print("  FAIL " + b)
    missing = [s for s in SURFACES if s not in choices.get("surfaces", {})]
    if missing:
        bad.append("no choice for: " + ", ".join(missing))
        print("  FAIL no choice for: " + ", ".join(missing))
    print(f"{len(choices.get('surfaces', {})) - len(bad)}/{len(SURFACES)} surfaces "
          "chosen, existing, and available at the wanted size")
    return 1 if bad else 0


def fetch():
    choices = load_choices()
    if choices is None:
        return 1
    # REFUSE TO START ON A BAD LIST. A typo here costs a CI run and comes back
    # as a surface that silently did not arrive, which is the failure mode the
    # catalogue exists to remove.
    if validate() != 0:
        print("choices.json does not validate — not fetching anything")
        return 1
    textures = PACK / "textures"
    materials = PACK / "materials"
    textures.mkdir(parents=True, exist_ok=True)
    materials.mkdir(parents=True, exist_ok=True)

    wanted = {logical: aid
              for logical, aid in sorted(choices.get("surfaces", {}).items())
              if logical in SURFACES}

    # THE LINKS FIRST, ALL OF THEM, BEFORE ANY DOWNLOAD. A catalogue pulled
    # after this change already carries `link` per asset, in which case this
    # costs nothing; the committed one predates it, so the list endpoint fills
    # the gap. Either way the fetch loop below only ever downloads a URL the
    # library itself handed over.
    cat_path = HERE / "catalogue.json"
    links = {}
    if cat_path.exists():
        for a in json.loads(cat_path.read_text(encoding="utf-8")).get("assets", []):
            if a.get("id") in set(wanted.values()) and a.get("link"):
                links[a["id"]] = a["link"]
        if links:
            print(f"  {len(links)} link(s) came from the committed catalogue")
    unresolved = set(wanted.values()) - set(links)
    if unresolved:
        links.update(links_for(unresolved))

    written, failed, attribution = [], [], {}
    for logical, asset_id in wanted.items():
        link = links.get(asset_id)
        if not link:
            print(f"  {logical:<12} FAILED {asset_id}: no {RESOLUTION} download "
                  "link — the library did not offer one")
            failed.append(logical)
            continue
        try:
            blob = get(link, timeout=180)
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
                inside = z.namelist()
                # NAMED, NOT `next()`. A bare `next()` raises StopIteration with
                # an EMPTY message, which is how twelve identical failures
                # reached the log saying only "StopIteration:" and cost a CI
                # round trip to identify. If no colour map is in there, the
                # useful thing to print is what WAS.
                name = None
                for n in inside:
                    if n.lower().endswith((".jpg", ".png")) and "color" in n.lower():
                        name = n
                        break
                if name is None:
                    raise ValueError("no colour map among " + ", ".join(inside[:8]))
                img = z.read(name)
        except Exception as e:                                   # noqa: BLE001
            print(f"  {logical:<12} FAILED to read colour map from {asset_id}: "
                  f"{type(e).__name__}: {e}")
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
    ap.add_argument("--validate", action="store_true",
                    help="check choices.json against the catalogue; no network")
    ap.add_argument("--fetch", action="store_true",
                    help="download the assets named in choices.json")
    args = ap.parse_args()
    if args.catalogue:
        return catalogue()
    if args.validate:
        return validate()
    if args.inventory:
        return inventory()
    if args.fetch:
        return fetch()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
