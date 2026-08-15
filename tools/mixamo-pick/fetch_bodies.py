#!/usr/bin/env python3
"""Download the CHARACTER BODIES themselves — the thing the harvest never got.

WHY THIS EXISTS, and it is the largest visible gap in the project.

`Assets/Characters/` holds 44 FBX. Forty-two are animations. The only two
BODIES are `X Bot.fbx` and `Y Bot.fbx`, which are the grey featureless
mannequins Mixamo hands you as a preview. The player has been one of them for
weeks: `CharacterPrefab.BodyModel` names X Bot, and `review_day1_noon.jpg`
shows exactly what that looks like — a pale figure with no face and a blue hip
band, standing in a city that is otherwise trying to be a place.

TWO THINGS CAUSED IT AND BOTH ARE IN THIS FOLDER.

First, `choose_characters.py` defaults to `--count 2` and its `PREFERRED` list
begins `["x bot", "y bot", "michelle", "remy"]`. It pins the first two matches
and stops. So it pinned the two placeholders and never reached a real body —
working exactly as written, choosing exactly the wrong thing.

Second, and the reason nothing caught it: MixamoHarvester downloads ANIMATIONS.
An animation export carries a skeleton, not necessarily a skin, and the pick
step copies clips. Nothing in the pipeline has ever asked for a character's own
T-pose mesh, so no amount of re-running the harvest would have produced one.

WHAT THIS DOES. For each chosen character it asks Mixamo to export the
character itself — T-pose, with skin — waits for the job, and writes the FBX
into the repository beside the clips. That is the whole of it.

    python fetch_bodies.py --harvester "C:\\path\\to\\MixamoHarvester" \\
                           --out "C:\\path\\to\\wc26-picks\\ledger\\Assets\\Characters"

HONESTY ABOUT WHAT IS NOT VERIFIED HERE. Mixamo's API is undocumented and this
container cannot reach it — `curl https://www.mixamo.com/` fails outright, so
none of these calls have been executed. The request shapes follow the ones the
existing `choose_characters.py` already uses successfully against this account
(bearer token, `X-Api-Key: mixamo2`) and the export/monitor pair that
MixamoHarvester itself drives.

Because of that, every unexpected response is PRINTED IN FULL rather than
swallowed. If a field name is wrong, the run says what came back instead, and
it is fixed in one pass rather than guessed at across three. A tool that fails
with "could not download" tells you nothing; one that shows the JSON tells you
everything.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://www.mixamo.com/api/v1"

# REAL PEOPLE, AND THE BOTS ARE DELIBERATELY ABSENT.
#
# These are Mixamo's free rigged humans in ordinary clothes. Neutral matters
# more than striking: no armour, no capes, no stylised proportions, because
# LEDGER is a LATE-ANALOG (1980s/90s) British port town — the decade in
# this comment steered picks toward the wrong century once already, and
# CLAUDE.md section 0 exists because of it. A silhouette has to read as a person in a
# coat. Zombies, mutants and the sci-fi soldiers are skipped for the same
# reason.
#
# Four, not two, because the town needs to look like it has more than one
# family in it and four bodies across sixty-odd named characters is already a
# heavy re-use. `--names` overrides this entirely.
DEFAULT_BODIES = ["michelle", "remy", "sophie", "shae"]

# WITH SKIN. The single most important line in the file: `skin: false` returns
# a skeleton, which is precisely the thing the project already has forty-two of.
EXPORT_PREFS = {
    "format": "fbx7_2019",
    "skin": "true",
    "fps": "30",
    "reducekf": "0",
}


def api(url, token, data=None, timeout=60):
    """One request shape for every call, so a header cannot go missing on one."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Api-Key": "mixamo2",
        "Accept": "application/json",
    }
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as fh:
        raw = fh.read().decode("utf-8", "replace")
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # NOT AN EXCEPTION SWALLOWED. Mixamo returns HTML on some auth
        # failures, and "Expecting value: line 1 column 1" is the least
        # useful sentence in software.
        print(f"  Mixamo returned something that is not JSON, from {url}:")
        print("  " + raw[:400].replace("\n", "\n  "))
        raise SystemExit(2)


def characters(token, pages=4):
    out = []
    for page in range(1, pages + 1):
        data = api(f"{BASE}/products?page={page}&limit=96&type=Character", token)
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


def export_body(token, cid, name, out_dir, wait_seconds=180):
    """Ask for the T-pose with skin, wait for it, write the FBX. True on success."""
    print(f"  {name}: requesting export...")
    try:
        api(f"{BASE}/animations/export", token, data={
            "character_id": cid,
            "type": "Character",
            "product_name": name,
            "preferences": EXPORT_PREFS,
        })
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        print(f"  {name}: export request refused — {e.code} {e.reason}")
        if detail.strip():
            print("    " + detail.replace("\n", "\n    "))
        return False

    # POLLED, NOT SLEPT-THEN-ASSUMED. The export is a job; a fixed sleep
    # either wastes minutes or reads a URL that is not there yet, and the
    # second failure looks like a bad character rather than an early read.
    deadline = time.time() + wait_seconds
    url = None
    while time.time() < deadline:
        status = api(f"{BASE}/characters/{cid}/monitor", token)
        state = (status.get("status") or "").lower()
        if state == "completed":
            url = status.get("job_result")
            break
        if state in ("failed", "expired"):
            print(f"  {name}: Mixamo reported the job {state}. Full response:")
            print("    " + json.dumps(status)[:400])
            return False
        time.sleep(3)

    if not url:
        print(f"  {name}: timed out after {wait_seconds}s waiting for the export.")
        return False

    # The filename is the CHARACTER NAME, because `CharacterImport` keys off
    # the folder and `CharacterPrefab` names one file — a guid-suffixed name
    # would have to be transcribed by hand into the source.
    safe = "".join(ch for ch in name if ch.isalnum() or ch in " -_").strip()
    dest = os.path.join(out_dir, f"{safe}.fbx")
    with urllib.request.urlopen(url, timeout=300) as src, open(dest, "wb") as fh:
        fh.write(src.read())

    size = os.path.getsize(dest)
    # A BODY IS NOT A SKELETON, AND SIZE IS HOW YOU TELL WITHOUT UNITY.
    #
    # A skinned Mixamo body is megabytes of mesh; a skeleton-only export is
    # tens of kilobytes. If `skin` silently did not take, this is the line
    # that says so — here, now, rather than after a 28-minute CI build shows
    # another invisible man.
    if size < 200_000:
        print(f"  {name}: WROTE ONLY {size:,} BYTES — that is a skeleton, not a body. "
              f"The 'skin' preference did not take.")
        return False
    print(f"  {name}: {size:,} bytes -> {dest}")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvester", required=True, help="the MixamoHarvester folder (for the token)")
    ap.add_argument("--out", required=True, help="ledger/Assets/Characters in the repo")
    ap.add_argument("--token", default=None)
    ap.add_argument("--names", default=None, help="comma-separated, overrides the defaults")
    ap.add_argument("--count", type=int, default=4)
    ap.add_argument("--force", action="store_true",
                    help="re-download bodies that are already present")
    args = ap.parse_args()

    tokfile = args.token or os.path.join(args.harvester, "mixamo_token.txt")
    if not os.path.isfile(tokfile):
        print(f"No token file at {tokfile}")
        return 2
    token = open(tokfile, encoding="utf-8").read().strip().strip('"').strip("'")
    if not token:
        print("The token file is empty.")
        return 2
    if not os.path.isdir(args.out):
        print(f"No such folder: {args.out}")
        return 2

    try:
        chars = characters(token)
    except urllib.error.HTTPError as e:
        print(f"Mixamo said {e.code} {e.reason}.")
        if e.code in (401, 403):
            print("\nThat is an expired token. They are short-lived — get a fresh")
            print("one from the browser console and run this again:")
            print("    localStorage.getItem('access_token')")
        return 2

    print(f"{len(chars)} characters visible to this account.\n")

    wanted = [n.strip().lower() for n in args.names.split(",")] if args.names \
        else DEFAULT_BODIES
    # IF YOU NAMED THEM, YOU GET ALL OF THEM. `--count` defaults to 4 and the
    # picker stops there, so asking for six by name would have silently
    # fetched four and said nothing about the other two — a silent cap, which
    # is the thing this project refuses to ship. The default list is still
    # bounded by --count; an explicit list bounds itself.
    if args.names and args.count < len(wanted):
        args.count = len(wanted)
    chosen, seen = [], set()
    for want in wanted:
        for cid, name in chars:
            if want in name.lower() and cid not in seen:
                chosen.append((cid, name))
                seen.add(cid)
                break
        if len(chosen) >= args.count:
            break

    # NEVER SILENTLY SUBSTITUTE — the same rule `choose_characters.py` learned.
    # A body nobody picked, discovered three days later in a screenshot, is the
    # exact failure this whole folder exists to avoid.
    missing = [w for w in wanted[:args.count]
               if not any(w in n.lower() for _, n in chosen)]
    if missing:
        print(f"Not in this account's catalogue: {', '.join(missing)}")
        print("Names available (first 40):")
        for _, name in chars[:40]:
            print(f"    {name}")
        print()

    if not chosen:
        print("Nothing to download. Pass --names with one of the names above.")
        return 2

    # ALREADY HAVE IT? DO NOT FETCH IT AGAIN.
    #
    # The first real run got three of four — "shae" is not in this account's
    # catalogue — and the obvious next move is to run it again with a
    # different fourth name. Without this that costs a fresh download of the
    # three that already landed: ninety-five megabytes and the better part of
    # an hour of somebody's morning, to end up where they already were.
    #
    # `--force` is there because "skip what exists" is exactly the guard that
    # blocks the good case when a file is half-written or wrong, and rule 5b
    # says a guard needs an escape hatch you can reach without editing it.
    kept = []
    if not args.force:
        fresh = []
        for cid, name in chosen:
            safe = "".join(c for c in name if c.isalnum() or c in " -_").strip()
            if os.path.exists(os.path.join(args.out, f"{safe}.fbx")):
                kept.append(name)
            else:
                fresh.append((cid, name))
        chosen = fresh
    if kept:
        print(f"Already have, skipping: {', '.join(kept)}")
        print("   (pass --force to fetch them again anyway)")
    if not chosen:
        print("Nothing new to download — everything asked for is already here.")
        return 0

    print(f"Downloading {len(chosen)} body/bodies with skin:")
    ok = sum(1 for cid, name in chosen if export_body(token, cid, name, args.out))

    print()
    print(f"{ok} of {len(chosen)} bodies written to {args.out}")
    if ok:
        print()
        print("Next: commit them, and point CharacterPrefab.BodyModel at one.")
        print("PUSH.bat does the commit; the code change is one line and mine.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
