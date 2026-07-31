#!/usr/bin/env python3
"""A typeface the game ships, instead of one it borrows.

M17.9 / M22.4. `UiTheme.LoadFont` asks the OS for Segoe UI and falls back to
Arial, so the game ships no font at all. That is wrong in two ways that both
look like nothing:

  Segoe UI is Microsoft-licensed and not redistributable. The game does not
  redistribute it — it asks the OS — which is legal, and is also why THE
  TYPOGRAPHY DIFFERS PER MACHINE. On macOS and Linux it lands on Arial or
  Unity's legacy face, so every measurement `Core/Typography` makes about line
  length and contrast is a measurement of a font that may not be on screen.

  And the credits cannot name a typeface, because there isn't one.

Font hosts answer 000 through this container's proxy, exactly like every texture
host, so this runs in CI for the same reason `fetch_textures.py` does — and
inherits the same rules: ask before taking, take only what the asking found,
write the licence beside the file, and never delete anything.

    python3 tools/citypack/fetch_font.py --inventory   # list what exists
    python3 tools/citypack/fetch_font.py --fetch       # take a listed file

THE FIRST VERSION GUESSED A URL AND WAS WRONG. It asked
`fonts.google.com/download?family=X` for a zip and all three candidates failed
identically with `BadZipFile: File is not a zip file`. One cheap inventory run
found that before any fetch run was spent on it, which is the entire argument
for asking first.

The repair is NOT a better guess. `--inventory` now lists the family directories
in the google/fonts repository and records which files are actually there —
the same move the texture catalogue made after a search endpoint reported zero
`PavingStones` while the library held 162.

THE CHOICE, AND WHY. A period street sign, a ledger's ruled columns and a
caption bar are three different jobs, and the art direction asks for coherence
rather than character: the type should be legible and get out of the way. Every
candidate is under the SIL Open Font Licence or Apache 2.0, both of which permit
shipping inside a product — and the licence file is written next to the font
rather than promised, because that is what the obligation actually is.
"""
import argparse
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DEST = ROOT / "ledger" / "Assets" / "Resources"
HERE = pathlib.Path(__file__).resolve().parent

# THE FIRST VERSION ASKED `fonts.google.com/download?family=X` FOR A ZIP and got
# back something that is not a zip — all three candidates failed identically
# with `BadZipFile: File is not a zip file`. The endpoint has changed or now
# answers with a page.
#
# The obvious repair is to guess a different URL, which is the same mistake the
# texture search taught: `PavingStones` returned zero from a search endpoint
# while the catalogue held 162 of them. So this LISTS instead of guessing. The
# google/fonts repository is the canonical source and its directory contents are
# readable through an API that says what is actually there, which makes the
# question "which static regular exists for this family" a lookup rather than an
# experiment.
CONTENTS = "https://api.github.com/repos/google/fonts/contents/{path}"

# Where each candidate lives in that repository, in preference order. The
# licence directory IS the licence: `ofl/` is SIL Open Font Licence 1.1 and
# `apache/` is Apache 2.0, both of which permit shipping inside a product.
CANDIDATES = [
    ("ofl/inter", "Inter", "neutral, superb at small sizes, the safest caption face"),
    ("ofl/sourcesans3", "Source Sans 3", "slightly warmer, Adobe's, wide weight range"),
    ("apache/robotocondensed", "Roboto Condensed", "condensed, which suits a ruled ledger column"),
    ("ofl/librefranklin", "Libre Franklin", "a period-plausible grotesque, if the others are variable-only"),
    ("ofl/ptsans", "PT Sans", "ships static faces, and a dependable fallback"),
]

# What the game asks `Resources.Load<Font>` for. The file has to be named this
# or `UiTheme.ShippedFont` finds nothing and silently falls back.
INSTALL_AS = "LedgerSans"


def get(url, timeout=120):
    headers = {"User-Agent": "ledger-font/1"}
    # CI has a token; using it lifts the anonymous rate limit from 60/hour.
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def listing(path):
    """What files are actually in this directory of google/fonts."""
    data = json.loads(get(CONTENTS.format(path=urllib.parse.quote(path))))
    if not isinstance(data, list):
        return []
    return [{"name": e.get("name"), "size": e.get("size"),
             "url": e.get("download_url")} for e in data if e.get("type") == "file"]


def inventory():
    """List what each family directory actually contains. Downloads no font.

    A STATIC REGULAR IS WHAT MATTERS. Unity's dynamic font path does not read
    variable axes, so a file like `Inter[opsz,wght].ttf` would install cleanly
    and render one arbitrary weight — which looks like success and is not. The
    listing separates the two so the choice is made knowing which it is."""
    out = {}
    for path, family, why in CANDIDATES:
        try:
            files = listing(path)
            statics = [f for f in files
                       if f["name"].lower().endswith((".ttf", ".otf"))
                       and "[" not in f["name"]]
            variable = [f["name"] for f in files if "[" in f["name"]]
            lic = [f for f in files
                   if "OFL" in f["name"].upper() or "LICEN" in f["name"].upper()]
            # Most families keep their static cuts in a `static/` subdirectory.
            if not statics:
                try:
                    sub = listing(path + "/static")
                    statics = [f for f in sub
                               if f["name"].lower().endswith((".ttf", ".otf"))]
                except Exception:                                # noqa: BLE001
                    pass
            out[family] = {
                "path": path, "why": why,
                "licenceDir": path.split("/")[0],
                "static": sorted(f["name"] for f in statics)[:24],
                "variable": sorted(variable),
                "licenceFiles": [f["name"] for f in lic],
                "regular": next((f["url"] for f in statics
                                 if "regular" in f["name"].lower()
                                 and "italic" not in f["name"].lower()), None),
            }
            print(f"  {family:<18} {len(statics):3d} static, {len(variable)} variable, "
                  f"{len(lic)} licence file(s)"
                  + ("  REGULAR FOUND" if out[family]["regular"] else "  no static regular"))
            for n in sorted(f["name"] for f in statics)[:4]:
                print(f"      {n}")
        except Exception as e:                                   # noqa: BLE001
            out[family] = {"path": path, "why": why, "error": f"{type(e).__name__}: {e}"}
            print(f"  {family:<18} FAILED: {type(e).__name__}: {e}")

    path = HERE / "font-candidates.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nwrote {path.relative_to(ROOT)}")
    ok = sum(1 for v in out.values() if v.get("regular"))
    print(f"{ok} of {len(CANDIDATES)} families publish a static regular")
    if ok == 0:
        print("NO STATIC REGULAR ANYWHERE — a finding, not a pass. Unity cannot "
              "use a variable font through the dynamic path.")
        return 1
    return 0


def fetch():
    """Install the first candidate that publishes a static regular, and write
    its licence beside it.

    ONE FACE, NOT A FAMILY. `UiTheme` uses a single family with weights done
    through rich text — the Two Books way, already the project's decision — so
    shipping eight weights would be megabytes for nothing.

    DRIVEN BY THE COMMITTED LISTING, not by a guessed URL. Whatever
    `--inventory` recorded as that family's static regular is what gets taken,
    so the fetch cannot ask for a file the repository does not have."""
    DEST.mkdir(parents=True, exist_ok=True)
    listing_path = HERE / "font-candidates.json"
    known = json.loads(listing_path.read_text(encoding="utf-8")) if listing_path.exists() else {}
    if not known:
        print("no font-candidates.json — run --inventory first")
        return 1

    for path, family, why in CANDIDATES:
        entry = known.get(family) or {}
        url = entry.get("regular")
        if not url:
            print(f"  {family}: no static regular in the listing — skipping")
            continue
        try:
            data = get(url)
            licence_text = ""
            for lic in entry.get("licenceFiles", []):
                try:
                    licence_text = get(
                        f"https://raw.githubusercontent.com/google/fonts/main/{path}/{lic}"
                    ).decode("utf-8", "replace")
                    break
                except Exception:                                # noqa: BLE001
                    continue
        except Exception as e:                                   # noqa: BLE001
            print(f"  {family}: FAILED {type(e).__name__}: {e}")
            continue

        # AND IT HAS TO BE A FONT. A 404 page is bytes too, and installing one
        # would leave `UsingShippedFont` true while nothing renders.
        if data[:4] not in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"ttcf"):
            print(f"  {family}: what came back is not a font ({data[:16]!r})")
            continue

        ext = ".ttf" if data[:4] != b"OTTO" else ".otf"
        dest = DEST / (INSTALL_AS + ext)
        dest.write_bytes(data)
        (DEST / (INSTALL_AS + ".LICENCE.txt")).write_text(
            licence_text or f"{family}, from google/fonts {path}. The licence "
                            "file could not be fetched; get it before shipping.",
            encoding="utf-8")
        (HERE / "font-installed.json").write_text(json.dumps({
            "family": family, "why": why, "source": url,
            "installedAs": dest.name, "bytes": len(data),
            "licence": "SIL Open Font License 1.1" if path.startswith("ofl/")
                       else "Apache License 2.0",
            "licenceFileShipped": bool(licence_text),
        }, indent=1), encoding="utf-8")
        print(f"  {family}: -> {dest.name} ({len(data) // 1024} KiB), "
              f"licence {'shipped' if licence_text else 'MISSING'}")
        return 0 if licence_text else 1

    print("NO FAMILY INSTALLED — this run failed whatever is on disk.")
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", action="store_true")
    ap.add_argument("--fetch", action="store_true")
    args = ap.parse_args()
    if args.inventory:
        return inventory()
    if args.fetch:
        return fetch()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
