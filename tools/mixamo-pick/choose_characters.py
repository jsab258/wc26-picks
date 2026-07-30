#!/usr/bin/env python3
"""Pin the harvest to two characters instead of every character Mixamo has.

WHY THIS EXISTS, and it is the difference between a two-hour job and a
week-long one. MixamoHarvester's `main()` is:

    characters = get_character_list(bearer_token)
    for character_id in characters:
        process_animations_for_character(...)

with no way to limit it — it fetches every character in the catalogue, on the
order of a hundred, and runs all ~2,500 animations against each. That is a
quarter of a million exports and hundreds of gigabytes, for a game that needs
about thirty clips on two bodies.

But `get_character_list` reads `characters.json` from disk when it exists and
only calls the API when it does not. So writing that file first pins the whole
run. One small request here replaces a change to somebody else's tool.

Usage:
    python choose_characters.py --harvester "C:\\path\\to\\MixamoHarvester"
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

BASE = "https://www.mixamo.com/api/v1"

# Neutral bodies. Neutral matters more than good-looking: no armour, no capes,
# no stylised proportions, because the silhouette gate in the weapons spec is
# about reading a person, not a costume.
PREFERRED = ["x bot", "y bot", "michelle", "remy"]


def fetch_characters(token, limit_pages=4):
    """Every character the account can see, as (id, name)."""
    out = []
    for page in range(1, limit_pages + 1):
        url = f"{BASE}/products?page={page}&limit=96&type=Character"
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {token}",
            "X-Api-Key": "mixamo2",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=60) as fh:
            data = json.load(fh)
        # The API has used both shapes over the years and neither is
        # documented, so accept either rather than crashing on the one I did
        # not expect.
        rows = data.get("results") if isinstance(data, dict) else data
        if not rows:
            break
        for r in rows:
            cid = r.get("id") or r.get("character_id")
            name = r.get("description") or r.get("name") or ""
            if cid:
                out.append((cid, name))
        pag = data.get("pagination") if isinstance(data, dict) else None
        if pag and pag.get("num_pages") and page >= pag["num_pages"]:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvester", required=True, help="the MixamoHarvester folder")
    ap.add_argument("--token", default=None, help="defaults to <harvester>/mixamo_token.txt")
    ap.add_argument("--count", type=int, default=2)
    ap.add_argument("--names", default=None,
                    help="comma-separated names to prefer instead of the defaults")
    args = ap.parse_args()

    tokfile = args.token or os.path.join(args.harvester, "mixamo_token.txt")
    if not os.path.isfile(tokfile):
        print(f"No token file at {tokfile}")
        return 2
    token = open(tokfile, encoding="utf-8").read().strip().strip('"').strip("'")
    if not token:
        print("The token file is empty.")
        return 2

    try:
        chars = fetch_characters(token)
    except urllib.error.HTTPError as e:
        print(f"Mixamo said {e.code} {e.reason}.")
        if e.code in (401, 403):
            print()
            print("That is an expired or mistyped token. They are short-lived —")
            print("get a fresh one from the browser console and run this again:")
            print("    localStorage.getItem('access_token')")
        return 2
    except Exception as e:                      # noqa: BLE001 - report, do not mask
        print(f"Could not reach Mixamo: {e}")
        return 2

    if not chars:
        print("Mixamo returned no characters, which should not happen with a good token.")
        return 2

    print(f"{len(chars)} characters visible to this account.")

    wanted = [n.strip().lower() for n in args.names.split(",")] if args.names else PREFERRED
    chosen = []
    for want in wanted:
        for cid, name in chars:
            if want in name.lower() and cid not in [c[0] for c in chosen]:
                chosen.append((cid, name))
                break
        if len(chosen) >= args.count:
            break

    # NEVER SILENTLY SUBSTITUTE. If the preferred bodies are not there, say so
    # and show what was taken instead — the alternative is a harvest of two
    # characters nobody chose, discovered three days later.
    if len(chosen) < args.count:
        print()
        print(f"Only matched {len(chosen)} of the {args.count} preferred names "
              f"({', '.join(wanted)}).")
        print("Filling the rest from the top of the catalogue:")
        for cid, name in chars:
            if len(chosen) >= args.count:
                break
            if cid not in [c[0] for c in chosen]:
                chosen.append((cid, name))
                print(f"    + {name}")

    dest = os.path.join(args.harvester, "characters.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump([c[0] for c in chosen], fh, indent=2)

    print()
    for cid, name in chosen:
        print(f"  pinned: {name}  ({cid})")
    print(f"wrote {dest}")
    print()
    print("The harvest will now cover these characters only. Delete that file")
    print("if you ever want the whole catalogue back.")

    # And the full list, so a bad match can be fixed without another API call.
    with open(os.path.join(args.harvester, "characters_available.txt"),
              "w", encoding="utf-8") as fh:
        for cid, name in chars:
            fh.write(f"{name}\t{cid}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
