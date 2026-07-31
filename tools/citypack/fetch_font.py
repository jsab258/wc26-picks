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

`fonts.google.com` answers 000 through this container's proxy, exactly like
every texture host, so this runs in CI for the same reason `fetch_textures.py`
does — and inherits the same rules: ask before taking, validate offline, write
the attribution with the file, and never delete anything.

    python3 tools/citypack/fetch_font.py --inventory   # what the family offers
    python3 tools/citypack/fetch_font.py --fetch       # take it

THE CHOICE, AND WHY. A period British street sign, a ledger's ruled columns and
a caption bar are three different jobs, and the art direction asks for coherence
rather than character: the type should be legible, slightly condensed, and get
out of the way. The families below are all SIL Open Font Licence 1.1, which
permits shipping inside a product with no attribution requirement beyond keeping
the licence file — and the licence file is written next to the font rather than
promised, because that is the obligation.
"""
import argparse
import io
import json
import pathlib
import sys
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DEST = ROOT / "ledger" / "Assets" / "Resources"
HERE = pathlib.Path(__file__).resolve().parent

# Google Fonts serves a zip per family from a stable endpoint that needs no key.
FAMILY_ZIP = "https://fonts.google.com/download?family={family}"

# In preference order, with the reason. All SIL OFL 1.1.
CANDIDATES = [
    ("Inter", "neutral, superb at small sizes, the safest possible caption face"),
    ("Source Sans 3", "slightly warmer, Adobe's, wide weight range"),
    ("Roboto Condensed", "condensed, which suits a ruled ledger column"),
]

# What the game asks `Resources.Load<Font>` for. The file has to be named this
# or `UiTheme.ShippedFont` finds nothing and silently falls back.
INSTALL_AS = "LedgerSans"


def get(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "ledger-font/1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def inventory():
    """Which families actually download, and what is in the zip. No install."""
    out = {}
    for family, why in CANDIDATES:
        url = FAMILY_ZIP.format(family=family.replace(" ", "%20"))
        try:
            blob = get(url)
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                names = [n for n in z.namelist()
                         if n.lower().endswith((".ttf", ".otf"))]
                lic = [n for n in z.namelist() if "OFL" in n.upper() or "LICEN" in n.upper()]
            out[family] = {"why": why, "faces": sorted(names)[:20],
                           "licence": lic, "bytes": len(blob)}
            print(f"  {family:<20} {len(names):3d} face(s), "
                  f"{len(lic)} licence file(s), {len(blob) // 1024} KiB")
            for n in sorted(names)[:4]:
                print(f"      {n}")
        except Exception as e:                                   # noqa: BLE001
            out[family] = {"why": why, "error": f"{type(e).__name__}: {e}"}
            print(f"  {family:<20} FAILED: {type(e).__name__}: {e}")

    path = HERE / "font-candidates.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nwrote {path.relative_to(ROOT)}")
    ok = sum(1 for v in out.values() if v.get("faces"))
    if ok == 0:
        print("NO FAMILY DOWNLOADED — a finding, not a pass.")
        return 1
    return 0


def fetch():
    """Take the first candidate that works, install one regular face, and write
    its licence beside it.

    ONE FACE, NOT A FAMILY. `UiTheme` uses a single family with weights done
    through rich text — the Two Books way, already the project's decision — so
    shipping eight weights would be megabytes for nothing."""
    DEST.mkdir(parents=True, exist_ok=True)
    for family, why in CANDIDATES:
        url = FAMILY_ZIP.format(family=family.replace(" ", "%20"))
        try:
            blob = get(url)
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                faces = [n for n in z.namelist() if n.lower().endswith((".ttf", ".otf"))]
                # A static regular, not a variable font: Unity's dynamic font
                # path does not read variable axes, so a variable file would
                # install cleanly and render one arbitrary weight.
                regular = next((n for n in faces
                                if "regular" in n.lower() and "italic" not in n.lower()
                                and "[" not in n), None)
                if regular is None:
                    regular = next((n for n in faces if "[" not in n), None)
                if regular is None:
                    print(f"  {family}: no static face in the zip")
                    continue
                data = z.read(regular)
                licence = next((n for n in z.namelist()
                                if "OFL" in n.upper() or "LICEN" in n.upper()), None)
                licence_text = z.read(licence).decode("utf-8", "replace") if licence else ""
        except Exception as e:                                   # noqa: BLE001
            print(f"  {family}: FAILED {type(e).__name__}: {e}")
            continue

        ext = pathlib.Path(regular).suffix.lower()
        dest = DEST / (INSTALL_AS + ext)
        dest.write_bytes(data)
        # THE LICENCE SHIPS WITH THE FILE. Not a promise in a document that
        # somebody has to remember to update — the OFL requires the licence
        # travel with the font, and a copy next to it is the only version of
        # that which cannot drift.
        (DEST / (INSTALL_AS + ".LICENCE.txt")).write_text(
            licence_text or f"{family} is licensed under the SIL Open Font "
                            "License 1.1. The zip carried no licence file; "
                            "fetch it before shipping.", encoding="utf-8")
        (HERE / "font-installed.json").write_text(json.dumps({
            "family": family, "why": why, "sourceFile": regular,
            "installedAs": dest.name, "bytes": len(data),
            "licence": "SIL Open Font License 1.1",
            "licenceFileShipped": bool(licence_text),
        }, indent=1), encoding="utf-8")
        print(f"  {family}: {regular} -> {dest.name} ({len(data) // 1024} KiB), "
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
