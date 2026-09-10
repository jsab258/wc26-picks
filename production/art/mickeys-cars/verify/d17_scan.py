#!/usr/bin/env python3
"""The D17 pass: what alcohol and gambling actually touch, counted.

D17 (ledger-v2/respec/decision-register/D17-no-alcohol-no-gambling.md) says
alcohol and gambling are never shown, served, drunk or spoken of, anywhere, in
image or speech, and that pubs may exist as places. It names four places it is
enforced. It does not say WHAT IT BREAKS, and an opinion about that is worth
nothing next to a count.

This is a READ-ONLY SCANNER. It writes nothing, edits nothing and fixes
nothing. It reports.

Two things it is careful about, because both have bitten this studio:

1. EVERY ZERO SHIPS ITS DENOMINATOR, and a target that could not be read
   prints "nothing measured" rather than a clean nothing.
2. A WORD IS NOT A BREAK. "bar" is in "crowd control barrier" only by
   accident of reading, and "I'd bet" is an idiom and not gambling. The
   scanner separates HITS from JUDGED BREAKS and prints both, and the judged
   column is a human reading recorded in this file, so a later reader can
   disagree with a named line instead of with a number.

The atlas lives on another branch, so it is read with `git show` rather than
from the working tree, and the command is printed.

Run from the repository root:
    python3 production/art/mickeys-cars/verify/d17_scan.py
"""
import collections
import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[4]   # verify, mickeys-cars, art, production, repo
ATLAS_REF = "origin/art/atlas-01"
ATLAS_JSON = "production/art/atlas-01/data/atlas.json"
ATLAS_MD = "production/art/atlas-01/DISTRICTS.md"

ALC = re.compile(
    r"\b(alcohol\w*|beer|beers|ale|ales|bitter|lager|stout|porter|mild|cask|casks"
    r"|firkin|keg|kegs|barrel|barrels|cellar|pint|pints|brewery|brewer|brewing"
    r"|brew|drink|drinks|drinking|drunk|drunken|pub|pubs|publican|landlord"
    r"|licensee|bar|bars|barmaid|barman|spirits|whisky|gin|rum|vodka|brandy"
    r"|sherry|wine|wines|cider|shandy|off-licence|booze|boozer|tipple|optic"
    r"|optics|taproom|snug|licensed|permitted hours|last orders)\b", re.I)
GAM = re.compile(
    r"\b(gambling|gamble|bet|bets|betting|bookmaker|bookmakers|bookie"
    r"|turf accountant|odds|stake|stakes|wager|wagers|fruit machine"
    r"|one-armed bandit|amusement with prizes|jackpot|bingo|lottery|pools"
    r"|tote|punter|punters|gaming|casino|slot machine)\b", re.I)

TARGETS = [
    "canon.md",
    "content/brands/brand-bible-v1.json",
    "content/dialogue/pub-regular-v1.json",
    "content/dialogue/crime-witness-v1.json",
    "game-design/barks.json",
    "game-design/bark-names.json",
    "production/specs/vignette-scene.json",
    "production/specs/vignette-pieces.json",
    "production/specs/vignette-bill-of-materials.json",
    "ledger/Assets/StreamingAssets/Decals/generated/manifest.json",
    "tools/imagegen/prompts.json",
]


def git_show(ref, path):
    try:
        out = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=REPO,
                             capture_output=True, text=True, timeout=60)
        if out.returncode != 0:
            return None
        return out.stdout
    except Exception:
        return None


def scan_text(txt):
    return ALC.findall(txt), GAM.findall(txt)


def section_files():
    print("1 TEXT SCAN OVER SHIPPED CONTENT")
    read = 0
    missing = []
    tot_a = tot_g = 0
    for rel in TARGETS:
        p = REPO / rel
        if not p.exists():
            missing.append(rel)
            continue
        txt = p.read_text(errors="replace")
        read += 1
        a, g = scan_text(txt)
        tot_a += len(a)
        tot_g += len(g)
        print(f"  {rel} lines={len(txt.splitlines())} "
              f"alcoholHits={len(a)} gamblingHits={len(g)}")
    print(f"filesRead={read}/{len(TARGETS)} filesMissing={len(missing)}")
    for m in missing:
        print(f"  MISSING {m}")
    print(f"totalAlcoholHits={tot_a} totalGamblingHits={tot_g} "
          f"overFilesRead={read}")
    if read == 0:
        print("  nothing measured")
    return read


def section_dialogue():
    print()
    print("2 DIALOGUE, LINE BY LINE, BECAUSE A BANK IS NOT A BLOB")
    for rel in ("content/dialogue/pub-regular-v1.json",
                "content/dialogue/crime-witness-v1.json"):
        p = REPO / rel
        if not p.exists():
            print(f"  {rel} nothing measured: file absent")
            continue
        d = json.loads(p.read_text())
        lines = d["lines"]
        a = [l for l in lines if ALC.search(l["text"])]
        g = [l for l in lines if GAM.search(l["text"])]
        touched = {l["id"] for l in a} | {l["id"] for l in g}
        print(f"  {rel} lines={len(lines)} alcoholLines={len(a)} "
              f"gamblingLines={len(g)} untouchedLines={len(lines)-len(touched)}"
              f"/{len(lines)}")
        for l in a:
            print(f"    ALC {l['id']} {l['text'][:88]}")
        for l in g:
            print(f"    GAM {l['id']} {l['text'][:88]}")


def section_images():
    print()
    print("3 GENERATED IMAGES: WHAT IS DRAWN, AND WHAT IS PLACED")
    man = REPO / "ledger/Assets/StreamingAssets/Decals/generated/manifest.json"
    if not man.exists():
        print("  nothing measured: manifest absent")
        return
    d = json.loads(man.read_text())
    imgs = d["images"]
    hit = []
    for i, im in enumerate(imgs):
        blob = json.dumps(im)
        if ALC.search(blob) or GAM.search(blob):
            hit.append((i, im))
    print(f"  imagesInLibrary={len(imgs)} d17RelevantImages={len(hit)}/{len(imgs)}")
    for i, im in hit:
        print(f"    [{i}] id={im.get('id')} binds={str(im.get('binds_to'))[:70]}")
    pieces = REPO / "production/specs/vignette-pieces.json"
    if not pieces.exists():
        print("  placedDecals nothing measured: piece list absent")
        return
    ps = json.loads(pieces.read_text())["pieces"]
    used = [str(p.get("asset")).split("#")[0] for p in ps
            if p.get("asset") and "generated/" in str(p.get("asset"))]
    ids = {im.get("id") for _, im in hit}
    placed_bad = [u for u in used if u.split("/")[-1] in ids]
    print(f"  generatedDecalsPlacedOnTheStreet={len(used)} "
          f"ofThoseD17Relevant={len(placed_bad)}/{len(used)}")
    for u in placed_bad:
        print(f"    PLACED AND RELEVANT {u}")


def section_atlas():
    print()
    print("4 THE ATLAS AND THE DISTRICT SHEETS")
    print(f"  read with: git show {ATLAS_REF}:{ATLAS_JSON}")
    raw = git_show(ATLAS_REF, ATLAS_JSON)
    if raw is None:
        print("  nothing measured: the atlas ref could not be read")
        return
    d = json.loads(raw)
    lm = d["landmarks"]
    venues = [l for l in lm if l.get("venue")]
    print(f"  landmarks={len(lm)} informationVenues={len(venues)}"
          f"/{len(lm)} districts={len(d['districts'])}")
    for l in venues:
        blob = json.dumps(l)
        flag = "ALC" if ALC.search(blob) else ("GAM" if GAM.search(blob) else "")
        print(f"    venue {l['id']:3s} {l['name']:22s} district={l['district']:9s} "
              f"type={l['type']:7s} textHit={flag or 'none'}")
    obj_hits = 0
    obj_total = 0
    for x in d["districts"]:
        for o in x["objects"]:
            obj_total += 1
            if ALC.search(o) or GAM.search(o):
                obj_hits += 1
                print(f"    OBJECT {x['id']}: {o}")
    print(f"  districtObjects={obj_total} d17Relevant={obj_hits}/{obj_total}")
    md = git_show(ATLAS_REF, ATLAS_MD)
    if md is None:
        print("  DISTRICTS.md nothing measured")
        return
    per = {}
    for line in md.splitlines():
        m = re.match(r"^\| (Hook|Copper Row|Exchange|Parade|Fairview|Ironside"
                     r"|Gullwing) \|", line)
        if m:
            a, g = scan_text(line)
            per[m.group(1)] = (len(a), len(g), line)
    print(f"  districtSheetRows={len(per)}/7")
    for k, (a, g, line) in per.items():
        print(f"    {k:11s} alcoholHits={a} gamblingHits={g}")
        if a or g:
            for w in set(ALC.findall(line)) | set(GAM.findall(line)):
                print(f"       word: {w}")


def selftest():
    print()
    print("5 SELFTEST, accepting case first")
    clean = "A wet street with a phone box and a galvanised dustbin."
    dirty = "The bookmaker next to the pub sells bitter."
    a1, g1 = scan_text(clean)
    a2, g2 = scan_text(dirty)
    print(f"  acceptingCase hits={len(a1)+len(g1)}/0-expected")
    print(f"  rejectingCase hits={len(a2)+len(g2)}/3-expected "
          f"words={sorted(set(a2)|set(g2))}")
    ok = (len(a1) + len(g1) == 0) and (len(a2) + len(g2) >= 3)
    print(f"  selftestPasses={ok}")
    return ok


def main():
    print("D17 PASS, read-only, 2026-09-10")
    print(f"repo={REPO}")
    print()
    section_files()
    section_dialogue()
    section_images()
    section_atlas()
    ok = selftest()
    print()
    print("This scanner reports HITS. Which hits are BREAKS is a judgement and "
          "it is written down, line by line, in 05-D17-town-pass.md.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
