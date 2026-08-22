#!/usr/bin/env python3
"""M17.10 visual-bar fetches: street furniture, the grime layer, the skies.

The sources and every verification tag are in
`game-design/visual-bar-sources.md` — this script downloads the curated
subset of that table. Three classes, three destinations:

  ledger/Assets/Props/base-mesh/   ~30 CC0 GLBs from The Base Mesh (via the
                                   M3-org GitHub mirror — the ONE host that
                                   was fetch-verified from the dev container
                                   itself): bollards, bins, a builder's
                                   skip, benches, pallets, chimney pots,
                                   awnings, drain covers, fingerposts.
  ledger/Assets/StreamingAssets/Decals/ambientcg/
                                   the V2 grime layer: leaking stains, worn
                                   road lines, manhole covers, asphalt
                                   damage, imperfection/scratch masks, moss.
                                   StreamingAssets because DecalLayer reads
                                   them at RUNTIME via File IO + LoadImage,
                                   the CityPack pattern.
  ledger/Assets/Sky/polyhaven/     four 2k HDRIs, one per hour of the day
                                   the sim photographs.

EVERY RULE HERE IS INHERITED FROM fetch_props.py AND THE VOICE PIPELINE:
fail soft per item and loudly at the end; the run prints what it decided;
nothing is deleted; a haul of zero exits non-zero because a fetch that
banked nothing must not read as green; attribution is written beside the
files in the same run that fetches them.

CC0 ONLY in this script. The one CC-BY source in the research (Poly Pizza's
Google Poly archive) is deliberately NOT fetched here — per-item licence
reads need eyes, not a loop.
"""
import io
import json
import pathlib
import sys
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
HERE = pathlib.Path(__file__).resolve().parent

BASE_MESH_DIR = ROOT / "ledger" / "Assets" / "Props" / "base-mesh"
DECALS_DIR = ROOT / "ledger" / "Assets" / "StreamingAssets" / "Decals" / "ambientcg"
SKY_DIR = ROOT / "ledger" / "Assets" / "Sky" / "polyhaven"

RAW = "https://raw.githubusercontent.com/M3-org/base-meshes/main/models"

#: The Base Mesh picks — untextured real-scale GLBs; SurfaceSpec tints them
#: like everything else, which is why untextured is a feature here.
BASE_MESH = [
    "decorative_bollard_01", "decorative_bollard_02", "rounded_concrete_bollard",
    "wooden_square_bollard", "outdoor_bin", "mesh_bin", "swing_bin",
    "cigarette_bin", "skip", "park_bench", "garden_bench_01", "ornate_bench",
    "curved_stone_bench", "lamp_post_01", "traffic_cone_01", "traffic_cone_02",
    "pavement_sign", "finger_post_sign_01", "finger_post_sign_02",
    "finger_post_sign_03", "drain_cover_01", "drainage_grate_01",
    "crowd_control_barrier", "pallet", "small_pallet", "large_pallet",
    "oil_barrel", "wood_barrel", "wooden_crate_01", "wooden_crate_02",
    "roll_top_chimney", "weathertop_chimney", "awning_01", "awning_02",
    "trunk_protection_railing", "poster", "framed_poster",
]

#: ambientCG ids, fetched as `get?file=<ID>_2K-<FMT>.zip`. Decals ship PNG
#: (colour + opacity); the imperfection/scratch masks and moss ship JPG.
#: Both formats are tried in the order given, per item.
AMBIENTCG = [
    ("Leaking005", ["PNG", "JPG"]),
    ("LeakingSubstance001", ["PNG", "JPG"]),
    ("RoadLines001", ["PNG", "JPG"]),
    ("RoadLines004", ["PNG", "JPG"]),
    ("RoadLines007", ["PNG", "JPG"]),
    ("RoadLines010", ["PNG", "JPG"]),
    ("RoadLines011", ["PNG", "JPG"]),
    ("RoadLines018", ["PNG", "JPG"]),
    ("ManholeCover011", ["PNG", "JPG"]),
    ("AsphaltDamageSet001", ["PNG", "JPG"]),
    ("Sticker001", ["PNG", "JPG"]),
    ("SurfaceImperfections001", ["JPG", "PNG"]),
    ("SurfaceImperfections003", ["JPG", "PNG"]),
    ("SurfaceImperfections007", ["JPG", "PNG"]),
    ("SurfaceImperfections012", ["JPG", "PNG"]),
    ("Scratches003", ["JPG", "PNG"]),
    ("Moss001", ["JPG", "PNG"]),
]

#: Poly Haven 2k HDRIs — the four hours the sim photographs. The overcast
#: primary is literally shot near Belfast, which is the palette.
HDRIS = [
    "belfast_open_field",
    "industrial_sunset_puresky",
    "kloppenheim_04",
    "misty_farm_road",
]
HDRI_URL = "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/{slug}_2k.hdr"

VEHICLES_DIR = ROOT / "ledger" / "Assets" / "Props" / "oga-vehicles"

#: OpenGameArt pages holding the two vehicle kinds no owned kit has (the
#: bus and, per its page listing, further body styles the era needs). Both
#: PAGE-CONFIRMED CC0 in `visual-bar-sources.md` §C — and confirmed AGAIN
#: at fetch time below: nothing from a page is banked unless the page's
#: own licence block links CC0, so a relicensed page refuses itself.
OGA_VEHICLE_PAGES = [
    ("free-low-poly-vehicles-pack",
     "https://opengameart.org/content/free-low-poly-vehicles-pack"),
    ("lowpoly-public-transport",
     "https://opengameart.org/content/lowpoly-public-transport"),
]
CC0_MARK = "creativecommons.org/publicdomain/zero"

#: What leaves an archive: the formats PropPrefab enumerates (plus .mtl,
#: which an .obj is blind without) and the textures they reference.
MODEL_EXTS = (".glb", ".gltf", ".fbx", ".obj", ".mtl", ".bin",
              ".png", ".jpg", ".jpeg")


def fetch_oga_vehicles(manifest: dict, failures: list) -> int:
    """Scrape the confirmed OGA pages, bank their archives' model files.

    Same pact as every stage here: per-item fail-soft, loud totals, the
    page's attachment list printed IN FULL so an archive this code cannot
    extract (rar/7z) is a named finding rather than a silent absence —
    the `head -3` lesson, one layer up.
    """
    import re
    banked = 0
    VEHICLES_DIR.mkdir(parents=True, exist_ok=True)
    for pack, page_url in OGA_VEHICLE_PAGES:
        dest_dir = VEHICLES_DIR / pack
        if dest_dir.exists() and any(dest_dir.iterdir()):
            n = len(list(dest_dir.rglob("*")))
            print(f"  have    {pack} ({n} file(s))")
            manifest["oga-vehicles"].append(pack)
            continue
        try:
            html = fetch(page_url).decode("utf-8", "replace")
        except Exception as e:
            failures.append(f"oga-vehicles/{pack}: page fetch: {e}")
            print(f"  FAILED  {pack}: page fetch: {e}")
            continue
        # The licence gate. A page can be re-licensed after the research
        # that confirmed it, so the run re-reads the licence block every
        # time and refuses the whole page on a miss.
        if CC0_MARK not in html:
            failures.append(f"oga-vehicles/{pack}: page shows no CC0 licence "
                            "mark — REFUSED, re-check the page by eye")
            print(f"  REFUSED {pack}: no CC0 mark on page")
            continue
        atts = sorted(set(re.findall(
            r'https://opengameart\.org/sites/default/files/[^"\'<>\s]+', html)))
        arch = [a for a in atts if a.lower().endswith(".zip")]
        other = [a for a in atts if not a.lower().endswith(
            (".zip", ".png", ".jpg", ".jpeg", ".gif"))]
        print(f"  {pack}: {len(atts)} attachment link(s), "
              f"{len(arch)} zip(s), {len(other)} non-zip archive-ish")
        for a in other:
            print(f"    NOT EXTRACTABLE HERE: {a}")
        got = 0
        for url in arch:
            try:
                blob = fetch(url)
                zf = zipfile.ZipFile(io.BytesIO(blob))
                kept = 0
                for zn in zf.namelist():
                    base = pathlib.Path(zn).name
                    if not base or zn.endswith("/"):
                        continue
                    if not base.lower().endswith(MODEL_EXTS):
                        continue
                    # Flatten to <pack>/<basename>: PropPrefab keys on
                    # kit+stem, and zip paths full of spaces and unicode
                    # have burnt the importer before.
                    safe = base.replace(" ", "_")
                    (dest_dir / safe).parent.mkdir(parents=True, exist_ok=True)
                    (dest_dir / safe).write_bytes(zf.read(zn))
                    kept += 1
                got += kept
                print(f"    banked {kept} file(s) from {pathlib.Path(url).name} "
                      f"({len(blob) / 1e6:.1f} MB)")
            except Exception as e:
                failures.append(f"oga-vehicles/{pack}/{pathlib.Path(url).name}: {e}")
                print(f"    FAILED {pathlib.Path(url).name}: {e}")
        if got:
            manifest["oga-vehicles"].append(pack)
            banked += got
        else:
            failures.append(f"oga-vehicles/{pack}: nothing banked from "
                            f"{len(arch)} zip(s)")
    return banked


def probe_bicycles() -> None:
    """Report-only: what does OGA hold for 'bicycle'? No download.

    The bicycle has no confirmed source anywhere in the research — every
    candidate pack was bus-and-cars. This runner can search where the dev
    container cannot, so the search result becomes printed evidence for
    the next curation pass (which PAGE-CONFIRMS a pick by eye before any
    fetch list grows — licence per item needs eyes, not a loop).
    """
    import re
    try:
        html = fetch("https://opengameart.org/art-search-advanced?keys=bicycle"
                     ).decode("utf-8", "replace")
        slugs = []
        for m in re.findall(r'href="/content/([a-z0-9\-]+)"', html):
            if m not in slugs:
                slugs.append(m)
        print(f"\n=== bicycle probe: {len(slugs)} result slug(s) on page 1 ===")
        for s in slugs[:20]:
            print(f"  candidate: opengameart.org/content/{s}")
        if len(slugs) > 20:
            print(f"  (+{len(slugs) - 20} more not shown)")
        if not slugs:
            print("  page fetched, zero /content/ links found — selector "
                  "may be stale, say so rather than 'no bicycles exist'")
        # COMMITTED, NOT ONLY PRINTED (rule 12): the job log is a fixed
        # 4KB tail this environment cannot read past, so the first probe's
        # answer evaporated with its run. The same move as the mirror
        # inventory — the runner can ask, the repo can remember.
        (HERE / "oga_probe.txt").write_text(
            "# OGA search results for 'bicycle', page 1 — written by the\n"
            "# fetch runner. Curation stays by eye: PAGE-CONFIRM licence\n"
            "# before any slug graduates to the fetch list.\n"
            + "\n".join(f"opengameart.org/content/{s}" for s in slugs) + "\n")
    except Exception as e:
        print(f"\n=== bicycle probe FAILED (haul unaffected): {e} ===")


def fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 LEDGER-visual-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def run() -> int:
    banked = 0
    failures: list[str] = []
    manifest: dict[str, list[str]] = {"base-mesh": [], "ambientcg": [],
                                      "polyhaven": [], "oga-vehicles": []}

    print("=== The Base Mesh (CC0, M3-org mirror) ===", flush=True)
    BASE_MESH_DIR.mkdir(parents=True, exist_ok=True)
    for name in BASE_MESH:
        dest = BASE_MESH_DIR / f"{name}.glb"
        if dest.exists():
            print(f"  have    {name}.glb")
            manifest["base-mesh"].append(dest.name)
            continue
        try:
            blob = fetch(f"{RAW}/{name}/{name}.glb")
            # glTF-binary magic, so an HTML error page cannot land as a mesh.
            if blob[:4] != b"glTF":
                raise ValueError(f"not a GLB ({blob[:12]!r})")
            dest.write_bytes(blob)
            banked += 1
            manifest["base-mesh"].append(dest.name)
            print(f"  fetched {name}.glb ({len(blob) / 1024:.0f} KB)")
        except Exception as e:
            failures.append(f"base-mesh/{name}: {e}")
            print(f"  FAILED  {name}: {e}")

    print("\n=== ambientCG decals + masks (CC0) ===", flush=True)
    DECALS_DIR.mkdir(parents=True, exist_ok=True)
    for aid, fmts in AMBIENTCG:
        dest_dir = DECALS_DIR / aid
        if dest_dir.exists() and any(dest_dir.iterdir()):
            n = len(list(dest_dir.iterdir()))
            print(f"  have    {aid} ({n} file(s))")
            manifest["ambientcg"].append(aid)
            continue
        got = False
        for fmt in fmts:
            url = f"https://ambientcg.com/get?file={aid}_2K-{fmt}.zip"
            try:
                blob = fetch(url)
                zf = zipfile.ZipFile(io.BytesIO(blob))
                dest_dir.mkdir(parents=True, exist_ok=True)
                kept = 0
                for zn in zf.namelist():
                    base = pathlib.Path(zn).name
                    if not base or zn.endswith("/"):
                        continue
                    if not base.lower().endswith((".png", ".jpg", ".jpeg")):
                        continue
                    (dest_dir / base).write_bytes(zf.read(zn))
                    kept += 1
                if kept == 0:
                    raise ValueError("zip held no images")
                banked += kept
                manifest["ambientcg"].append(aid)
                print(f"  fetched {aid} ({fmt}, {kept} image(s), "
                      f"{len(blob) / 1e6:.1f} MB)")
                got = True
                break
            except Exception as e:
                print(f"    {fmt} miss: {e}")
        if not got:
            failures.append(f"ambientcg/{aid}: no format worked")
            print(f"  FAILED  {aid}")

    print("\n=== Poly Haven HDRIs (CC0) ===", flush=True)
    SKY_DIR.mkdir(parents=True, exist_ok=True)
    for slug in HDRIS:
        dest = SKY_DIR / f"{slug}_2k.hdr"
        if dest.exists():
            print(f"  have    {dest.name}")
            manifest["polyhaven"].append(dest.name)
            continue
        try:
            blob = fetch(HDRI_URL.format(slug=slug))
            # Radiance-HDR magic.
            if not blob.startswith(b"#?"):
                raise ValueError(f"not a Radiance HDR ({blob[:12]!r})")
            dest.write_bytes(blob)
            banked += 1
            manifest["polyhaven"].append(dest.name)
            print(f"  fetched {dest.name} ({len(blob) / 1e6:.1f} MB)")
        except Exception as e:
            failures.append(f"polyhaven/{slug}: {e}")
            print(f"  FAILED  {slug}: {e}")

    print("\n=== OGA vehicle packs (CC0, licence re-read per page) ===", flush=True)
    banked += fetch_oga_vehicles(manifest, failures)
    probe_bicycles()

    (HERE / "visual_manifest.json").write_text(json.dumps(manifest, indent=1))
    write_attribution(manifest)
    write_inventory()

    print(f"\nTOTAL banked this run: {banked} file(s); {len(failures)} failure(s)")
    for f in failures:
        print(f"  FAILED: {f}")
    have_any = (any(BASE_MESH_DIR.glob("*.glb"))
                or any(DECALS_DIR.glob("*/*"))
                or any(SKY_DIR.glob("*.hdr"))
                or (VEHICLES_DIR.exists() and any(VEHICLES_DIR.rglob("*"))))
    if banked == 0 and not have_any:
        print("NOTHING BANKED AND NOTHING ON DISK — this run says so.")
        return 1
    return 0


def write_inventory() -> None:
    """The mirror's FULL model list, committed as a file in the repo.

    Rule 12: the dev container cannot enumerate the mirror — the GitHub
    API and the Pages index are both unreachable from there, and probing
    model names one guess at a time produced five 404s for "bicycle" on
    21 Aug. This runner CAN ask, so the answer becomes a file anything
    can read. The immediate customer is the vehicle gap (`vehicleFellBack
    =[bus,bike x6]`): whether the mirror holds a bicycle or a bus is
    decided by this list, not by another round of guessing.

    Fails soft like everything else here — an inventory miss must never
    cost the fetch its haul.
    """
    try:
        blob = fetch("https://api.github.com/repos/M3-org/base-meshes/contents/models")
        entries = json.loads(blob)
        names = sorted(e["name"] for e in entries if isinstance(e, dict) and "name" in e)
        (HERE / "base_mesh_inventory.txt").write_text("\n".join(names) + "\n")
        wheels = [n for n in names
                  if any(k in n.lower() for k in
                         ("bike", "bicycle", "bus", "cycle", "moto", "cart",
                          "van", "truck", "vehicle", "scooter"))]
        print(f"\n=== mirror inventory: {len(names)} model dir(s) written to "
              f"base_mesh_inventory.txt ===")
        print(f"  vehicle-ish: {', '.join(wheels) if wheels else 'none in the mirror'}")
    except Exception as e:
        print(f"\n=== mirror inventory FAILED (haul unaffected): {e} ===")


def write_attribution(manifest: dict) -> None:
    """Human-readable rows beside the files, same pact as fetch_props."""
    BASE_MESH_DIR.mkdir(parents=True, exist_ok=True)
    (BASE_MESH_DIR / "THIRD-PARTY.md").write_text(
        "# Third-party models — The Base Mesh\n\n"
        "Every .glb in this directory is CC0 1.0 from The Base Mesh\n"
        "(https://thebasemesh.com), fetched via the M3-org GitHub mirror\n"
        "(https://github.com/M3-org/base-meshes) by tools/props/fetch_visual.py.\n"
        f"\n{len(manifest['base-mesh'])} file(s) at last fetch.\n")
    DECALS_DIR.parent.mkdir(parents=True, exist_ok=True)
    (DECALS_DIR.parent / "THIRD-PARTY.md").write_text(
        "# Third-party decal textures — ambientCG\n\n"
        "Every image under ambientcg/ is CC0 1.0 from ambientCG\n"
        "(https://ambientcg.com), fetched by tools/props/fetch_visual.py.\n"
        f"\nSets at last fetch: {', '.join(manifest['ambientcg']) or 'none'}.\n")
    SKY_DIR.parent.mkdir(parents=True, exist_ok=True)
    (SKY_DIR.parent / "THIRD-PARTY.md").write_text(
        "# Third-party skies — Poly Haven\n\n"
        "Every .hdr under polyhaven/ is CC0 1.0 from Poly Haven\n"
        "(https://polyhaven.com), fetched by tools/props/fetch_visual.py.\n"
        f"\nFiles at last fetch: {', '.join(manifest['polyhaven']) or 'none'}.\n")
    if manifest.get("oga-vehicles"):
        VEHICLES_DIR.mkdir(parents=True, exist_ok=True)
        (VEHICLES_DIR / "THIRD-PARTY.md").write_text(
            "# Third-party vehicle models — OpenGameArt\n\n"
            "Every model under this directory is CC0 1.0, fetched from the\n"
            "OpenGameArt pages below by tools/props/fetch_visual.py, which\n"
            "verifies the CC0 licence mark on each page at fetch time:\n\n"
            + "".join(f"- https://opengameart.org/content/{p}\n"
                      for p in manifest["oga-vehicles"]))


if __name__ == "__main__":
    sys.exit(run())
