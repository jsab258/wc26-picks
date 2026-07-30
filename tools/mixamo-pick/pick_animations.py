#!/usr/bin/env python3
"""LEDGER — pick the clips we actually need out of a bulk Mixamo harvest.

WHY THIS EXISTS. A full harvest is roughly 2,500 animations per character,
which is on the order of a gigabyte of FBX and cannot go into the repository.
What the game needs is about twenty-five clips. This walks the harvest, finds
the best match for each thing the roadmap asks for, copies only those into
`ledger/Assets/Characters/`, and — the important part — writes down what it
could NOT find rather than quietly shipping twenty-two of twenty-five.

It also writes the complete catalogue listing, which is worth more than the
clips on the first run: every animation name I have used so far has been
guessed from memory, and one text file replaces all of that guessing with the
real thing.

Usage (from this folder):

    python pick_animations.py --harvest "C:\\path\\to\\MixamoHarvester\\animations"

Nothing is deleted and nothing is moved. The harvest stays where it is.
"""

import argparse
import glob
import json
import os
import re
import shutil
import sys
from collections import OrderedDict

# ---------------------------------------------------------------------------
# WHAT THE GAME NEEDS
# ---------------------------------------------------------------------------
#
# Each entry is (slot, tier, [patterns]) where the patterns are tried IN ORDER
# and the first hit wins. Patterns are matched case-insensitively against the
# animation name with punctuation flattened, so "Standing React Small From
# Front" and "standing_react_small_from_front" are the same string here.
#
# NO `$` ANCHORS. MixamoHarvester names files `{animation}_{character_id}`,
# so "Walking" arrives as `walking x bot` and `^walking$` can never match —
# which made the test report two exact hits as substitutes. Anchor the front,
# never the back, and let the shortest-name tiebreak below do the rest.
#
# ORDER IS THE PREFERENCE. The first pattern is the clip I actually want; the
# ones after it are progressively worse substitutes that are still better than
# a missing slot. A substitute is reported as such — "found something" and
# "found the right thing" are different claims and the report keeps them apart.

WANTS = [
    # ---- TIER A: unblocks combat Phase 3 and the draw -------------------
    ("guard",        "A", [r"\bfight idle\b", r"\bfighting idle\b",
                           r"\bstanding block idle\b", r"\bboxing\b"]),
    ("guard_enter",  "A", [r"\bstanding idle to fight idle\b",
                           r"\bfight idle to action idle\b"]),
    ("guard_exit",   "A", [r"\bfight idle to standing idle\b"]),
    ("block_start",  "A", [r"\bstanding block start\b", r"\bstanding block\b"]),
    ("block_hold",   "A", [r"\bstanding block idle\b"]),
    ("block_end",    "A", [r"\bstanding block end\b"]),
    ("block_broken", "A", [r"\bstanding block react large\b"]),
    ("strike",       "A", [r"\bcross punch\b", r"\bcombo punch\b", r"\bjab\b"]),
    ("strike_alt",   "A", [r"\bbody jab cross\b", r"\belbow punch\b",
                           r"\bhook punch\b"]),
    ("shove",        "A", [r"^push\b", r"\bpush(ing)?\b", r"\bshove\b"]),
    ("shoved",       "A", [r"\bshove reaction\b", r"\bshoved reaction\b"]),
    ("take_hit",     "A", [r"\bstanding react small from front\b",
                           r"\bhit reaction\b", r"\breact(ion)? small\b"]),
    ("stagger",      "A", [r"\bstanding react large\b", r"\bstumbl(e|ing)\b"]),
    ("knockdown",    "A", [r"\bknocked out\b", r"\bfalling back death\b"]),
    ("get_up",       "A", [r"\bstand(ing)? up\b", r"\bgetting up\b", r"\bget up\b"]),
    ("draw_reach",   "A", [r"\bunarmed equip underarm\b", r"\bdraw sword 1\b",
                           r"\bdraw(ing)? sword\b"]),
    ("draw_holster", "A", [r"\bsheath sword 1\b", r"\bsheathing sword\b",
                           r"\bsheath"]),
    ("draw_gun",     "A", [r"\bdrawing gun\b"]),
    ("idle",         "A", [r"\bbreathing idle\b", r"\bstanding idle\b"]),
    ("walk",         "A", [r"^walking\b", r"\bwalk(ing)? forward\b"]),
    ("run",          "A", [r"^running\b", r"\brun(ning)? forward\b"]),

    # ---- TIER B: makes the perception layer read properly ---------------
    ("turn_left",    "B", [r"\bstanding turn left 90\b", r"\bleft turn\b"]),
    ("turn_right",   "B", [r"\bstanding turn right 90\b", r"\bright turn\b"]),
    ("look_around",  "B", [r"^look around\b", r"\blook(ing)? around\b"]),
    ("talk",         "B", [r"^talking\b", r"\btalk(ing)?\b"]),
    ("greet",        "B", [r"\bstanding greeting\b", r"\bwav(e|ing)\b"]),
    ("flinch",       "B", [r"^scared\b", r"\bterrified\b", r"\bflinch\b"]),
    # NO "SURRENDER" AND NO "HANDS UP" IN THE CATALOGUE - checked, not
    # guessed. `Defeat` is the nearest honest thing: a man who has stopped
    # resisting. Recorded as a substitute so it is never mistaken for the
    # clip that was asked for.
    ("hands_up",     "B", [r"\bsurrender\b", r"\bhands up\b", r"^defeat\b",
                           r"\bdefeated\b"]),
    ("back_away",    "B", [r"\bwalk(ing)? backward", r"\bstanding dodge backward\b"]),
    ("walk_start",   "B", [r"\bwalk(ing)? start\b", r"\bstart walking\b"]),
    ("walk_stop",    "B", [r"\bwalk(ing)? stop\b", r"\bstop walking\b"]),
    ("stairs_up",    "B", [r"\bascending stairs\b"]),
    ("stairs_down",  "B", [r"\bdescending stairs\b"]),

    # ---- TIER C: life, and the end -------------------------------------
    ("sit",          "C", [r"\bsitting idle\b", r"^sitting\b"]),
    ("lean",         "C", [r"\blean(ing)? against wall\b", r"^leaning\b"]),
    ("drink",        "C", [r"^drinking\b", r"\bdrink(ing)?\b"]),
    ("smoke",        "C", [r"^smoking\b", r"\bsmok(e|ing)\b"]),
    # Tom Novak runs a bar. `Bartending` is a real clip and a far better
    # answer than the `Typing` the guessed list settled for.
    ("work_counter", "C", [r"\bbartending\b", r"\bcounter\b", r"\btyping\b"]),
    ("collapse",     "C", [r"^dying\b", r"\bfalling back death\b"]),
    # THE FALL is an authored beat in this game, so it gets the clip that
    # actually depicts losing your footing rather than a generic drop.
    ("fall_stairs",  "C", [r"\bfalling from losing balance\b",
                           r"\bfall(ing)? down stairs\b", r"\bfalling down\b"]),
    ("lie_still",    "C", [r"\blying down\b", r"\blying\b", r"\bdead\b"]),
]

FLAT = re.compile(r"[^a-z0-9]+")


def flatten(name):
    """Lower-case, punctuation to single spaces. `Walk_Start.fbx` -> `walk start`."""
    return FLAT.sub(" ", name.lower()).strip()


def catalogue(harvest):
    """Every fbx under the harvest, as (flattened name, full path)."""
    found = []
    for root, _dirs, files in os.walk(harvest):
        for f in files:
            if f.lower().endswith(".fbx"):
                stem = os.path.splitext(f)[0]
                found.append((flatten(stem), stem, os.path.join(root, f)))
    return found


def pick(items, patterns):
    """First pattern with a hit wins; within a pattern, the SHORTEST name wins.

    Shortest because Mixamo names extra variants by suffixing — "Walking",
    "Walking Backwards", "Walking While Texting" — so the bare name is nearly
    always the plain version of the motion, and the plain version is the one a
    game blends from.
    """
    for depth, pat in enumerate(patterns):
        rx = re.compile(pat)
        hits = [it for it in items if rx.search(it[0])]
        if hits:
            hits.sort(key=lambda it: (len(it[0]), it[0]))
            return hits[0], depth
    return None, -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harvest", required=True,
                    help="the MixamoHarvester 'animations' folder")
    ap.add_argument("--out", default=None,
                    help="where to copy picks (default: ledger/Assets/Characters)")
    ap.add_argument("--tiers", default="ABC",
                    help="which tiers to copy, e.g. 'A' for combat only")
    args = ap.parse_args()

    if not os.path.isdir(args.harvest):
        print(f"No such folder: {args.harvest}")
        return 2

    here = os.path.dirname(os.path.abspath(__file__))
    out = args.out or os.path.join(here, "..", "..", "ledger", "Assets", "Characters")
    out = os.path.abspath(out)

    items = catalogue(args.harvest)
    print(f"harvest: {len(items)} fbx files under {args.harvest}")
    if not items:
        print("Nothing to pick from — is that the right folder?")
        return 2

    # THE CATALOGUE FIRST, and it is the most valuable output on run one.
    # Every animation name used in the roadmap so far was guessed; this file
    # replaces the guessing with the list.
    os.makedirs(out, exist_ok=True)
    listing = os.path.join(out, "_catalogue.txt")
    with open(listing, "w", encoding="utf-8") as fh:
        for _flat, stem, _path in sorted(items, key=lambda i: i[0]):
            fh.write(stem + "\n")
    print(f"wrote the full catalogue to {listing}")

    report = OrderedDict()
    copied = missing = substituted = 0
    for slot, tier, patterns in WANTS:
        if tier not in args.tiers:
            continue
        hit, depth = pick(items, patterns)
        if hit is None:
            report[slot] = {"tier": tier, "found": None,
                            "tried": patterns}
            missing += 1
            print(f"  MISSING  [{tier}] {slot:14s} — none of {len(patterns)} patterns matched")
            continue
        _flat, stem, path = hit
        dest_dir = os.path.join(out, tier)
        os.makedirs(dest_dir, exist_ok=True)

        # ONE CLIP PER SLOT, ALWAYS. Files are named `{slot}__{clip}.fbx`, so
        # when a slot's answer changes — as four did the moment the real
        # catalogue replaced my guesses — the new file lands beside the old one
        # under a different name and the slot silently has two clips in it.
        # Unity would import both and the wrong one is as likely to play as the
        # right one. Clear the slot first.
        for old_file in glob.glob(os.path.join(out, "*", f"{slot}__*.fbx")):
            if os.path.basename(old_file) != f"{slot}__{stem}.fbx":
                os.remove(old_file)
                print(f"  replaced  [{tier}] {slot:14s} -- removed "
                      f"{os.path.basename(old_file)}")

        dest = os.path.join(dest_dir, f"{slot}__{stem}.fbx")
        shutil.copy2(path, dest)
        copied += 1
        exact = depth == 0
        if not exact:
            substituted += 1
        report[slot] = {"tier": tier, "found": stem, "exact": exact,
                        "pattern": patterns[depth]}
        mark = "ok      " if exact else "SUBSTITUTE"
        print(f"  {mark} [{tier}] {slot:14s} <- {stem}")

    with open(os.path.join(out, "_picks.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    print()
    print(f"copied {copied}, substituted {substituted}, missing {missing}")
    print(f"picks -> {out}")
    print()
    print("Commit and push BOTH the fbx files and _catalogue.txt / _picks.json.")
    print("The catalogue is the part that stops me guessing at clip names.")
    if missing:
        print()
        print("Missing slots are listed in _picks.json. Do not go hunting for")
        print("them by hand — send the catalogue and I will pick the real names.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
