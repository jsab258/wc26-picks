#!/usr/bin/env python3
"""Fetch CC0 low-poly model kits so cars, benches and bins stop being boxes.

Jafar, 16 Aug: "textures and models have to come before playtest... max
polish." The character pipeline covers people; this covers everything
else the street is made of. Every model here is CC0 from Kenney
(kenney.nl) — free, no account, no purchase, which is the project's
hard rule on assets.

WHY THIS IS A CI JOB AND NOT A SCRIPT RUN IN THE DEV CONTAINER: every
asset host is blocked from the container (kenney.nl, poly.pizza,
ambientcg.com and quaternius.com all read 000 through the proxy,
measured 16 Aug). Same shape as the voice and texture pipelines.

AND IT INHERITS THE VOICE PIPELINE'S MOST EXPENSIVE LESSON: one run
must answer every question. Kenney has no query API, so the inventory
IS the download — this script downloads each kit once, writes the FULL
file listing of every kit to `tools/props/listings.json` (committed),
extracts only the models matching this run's chosen patterns, and
prints everything it decided. Round two picks additional props BY NAME
from the committed listings, locally, in seconds, without another
guessing round.

THE ZIP URL IS PARSED FROM THE ASSET PAGE, NOT GUESSED. Kenney's
download links carry a content hash in the path, so a hardcoded URL is
a URL that is already stale. If the parse finds nothing, every link on
the page is printed — a run that fails must say what it saw, not just
that it failed.

DESTRUCTIVE OPERATIONS ARE SCOPED TO WHAT THIS RUN PRODUCED. Nothing
here removes a file it did not just write. A run that extracts zero
models exits non-zero — a fetch that banked nothing must not read as
green (the voice pipeline's invariant 7).
"""
import argparse
import io
import json
import pathlib
import re
import sys
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
HERE = pathlib.Path(__file__).resolve().parent
PROPS = ROOT / "ledger" / "Assets" / "Props"

# The kits, by page slug. Car Kit is the certain need (28 vehicles on
# screen at once); the city kits are prospected for street furniture —
# their listings tell round two what exists.
KITS = [
    "car-kit",
    "city-kit-commercial",
    "city-kit-suburban",
    "city-kit-roads",
]

# What gets EXTRACTED this run, per kit, as filename regexes matched
# against the basename (case-insensitive). Car Kit: every vehicle model
# plus its textures. City kits: the street furniture the game already
# builds as primitives, so a match drops straight into an existing spot.
WANT = {
    "car-kit": [r"\.fbx$", r"\.png$"],
    "city-kit-commercial": [
        r"bench", r"bin\b", r"trash", r"lamp", r"light.*post", r"streetlight",
        r"phone", r"post.?box", r"crate", r"barrel", r"fence", r"hydrant",
        r"awning", r"sign", r"\.png$",
    ],
    "city-kit-suburban": [
        r"bench", r"bin\b", r"trash", r"lamp", r"streetlight", r"fence",
        r"hydrant", r"planter", r"\.png$",
    ],
    "city-kit-roads": [
        r"lamp", r"light", r"barrier", r"cone", r"sign", r"\.png$",
    ],
}

# Only files under the kit's FBX model directory (plus textures beside
# them) are worth extracting — kits ship OBJ and glTF copies of every
# model, and three copies of a mesh is two chances for Unity to import
# the wrong one.
MODEL_DIR_HINT = re.compile(r"(models?[/\\](fbx|FBX)|fbx( format)?[/\\])", re.I)


def page_url(slug: str) -> str:
    return f"https://kenney.nl/assets/{slug}"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "LEDGER-props-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def find_zip_url(html: str, slug: str) -> str | None:
    # The download button links a hashed path under /media/pages/assets/.
    m = re.search(r"https://kenney\.nl/media/pages/assets/[^\"'\s]+?\.zip", html)
    if m:
        return m.group(0)
    m = re.search(r"href=\"(/media/pages/assets/[^\"]+?\.zip)\"", html)
    if m:
        return "https://kenney.nl" + m.group(1)
    return None


def run(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="download, list, extract")
    args = ap.parse_args(argv)
    if not args.fetch:
        ap.print_help()
        return 2

    listings: dict[str, list[str]] = {}
    extracted_total = 0
    failures: list[str] = []

    for slug in KITS:
        print(f"\n=== {slug} ===", flush=True)
        try:
            html = fetch(page_url(slug)).decode("utf-8", errors="replace")
        except Exception as e:
            failures.append(f"{slug}: page fetch failed: {e}")
            print(f"  PAGE FETCH FAILED: {e}")
            continue

        zip_url = find_zip_url(html, slug)
        if not zip_url:
            failures.append(f"{slug}: no zip url found on page")
            print("  NO ZIP URL FOUND. Every link on the page:")
            for link in sorted(set(re.findall(r"href=\"([^\"]+)\"", html))):
                if "download" in link.lower() or ".zip" in link.lower():
                    print(f"    {link}")
            continue

        print(f"  zip: {zip_url}")
        try:
            blob = fetch(zip_url)
        except Exception as e:
            failures.append(f"{slug}: zip download failed: {e}")
            print(f"  ZIP DOWNLOAD FAILED: {e}")
            continue
        print(f"  downloaded {len(blob) / 1e6:.1f} MB")

        try:
            zf = zipfile.ZipFile(io.BytesIO(blob))
        except zipfile.BadZipFile as e:
            failures.append(f"{slug}: bad zip: {e}")
            continue

        names = zf.namelist()
        listings[slug] = names
        print(f"  {len(names)} entries in the kit")

        wants = [re.compile(p, re.I) for p in WANT.get(slug, [])]
        picked = 0
        for name in names:
            base = pathlib.Path(name).name
            if not base or name.endswith("/"):
                continue
            if not MODEL_DIR_HINT.search(name):
                continue
            if not any(w.search(base) for w in wants):
                continue
            dest = PROPS / slug / base
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(zf.read(name))
            picked += 1
        extracted_total += picked
        print(f"  extracted {picked} file(s) matching this run's patterns "
              f"into {PROPS / slug}")

    HERE.mkdir(parents=True, exist_ok=True)
    (HERE / "listings.json").write_text(json.dumps(listings, indent=1))
    print(f"\nlistings for {len(listings)} kit(s) -> tools/props/listings.json")

    write_attribution()

    # THE DENOMINATOR, and the non-zero exit for an empty haul.
    print(f"\nTOTAL extracted: {extracted_total} file(s); "
          f"{len(failures)} kit failure(s)")
    for f in failures:
        print(f"  FAILED: {f}")
    if extracted_total == 0:
        print("NOTHING EXTRACTED — this run banked nothing and says so.")
        return 1
    return 0


def write_attribution() -> None:
    """One entry per kit directory that exists. CC0, but the project's
    rule is that every third-party file is named regardless of licence —
    tools/attribution-check.py enforces the pair of files agreeing."""
    entries = {}
    for slug in KITS:
        d = PROPS / slug
        if not d.exists():
            continue
        entries[slug] = {
            "source": "Kenney (kenney.nl)",
            "kit": slug,
            "licence": "CC0 1.0 Universal",
            "url": f"https://kenney.nl/assets/{slug}",
            "files": sorted(p.name for p in d.iterdir() if p.is_file()),
        }
    if not entries:
        return
    PROPS.mkdir(parents=True, exist_ok=True)
    (PROPS / "ATTRIBUTION.json").write_text(json.dumps(
        {"note": "Sources for every model in this directory. THIRD-PARTY.md "
                 "is the human-readable copy and both must agree.",
         "kits": entries}, indent=1))
    lines = ["# Third-party models", "",
             "All models below are CC0 1.0 from Kenney (https://kenney.nl).",
             ""]
    for slug, e in entries.items():
        lines.append(f"- **{slug}** — {len(e['files'])} file(s) — {e['url']}")
    (PROPS / "THIRD-PARTY.md").write_text("\n".join(lines) + "\n")
    print(f"attribution written for {len(entries)} kit(s)")


if __name__ == "__main__":
    sys.exit(run())
