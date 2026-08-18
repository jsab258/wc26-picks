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
import hashlib
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
    # `Shoved` FIRST, and the reason is a duplicate nobody could have seen
    # from a filename. The harvest holds `Shove Reaction` and `Talking` as two
    # differently-named files with IDENTICAL BYTES — `tools/clip-motion.py`
    # found it by hashing what shipped — so one of those two slots has been
    # playing the other's animation. Which one cannot be told from here, and
    # `Shoved` is a third name in the catalogue for the same motion, so taking
    # it sidesteps the collision without a re-download. The content check
    # below is the general fix; this is the specific one.
    #
    # THE FIRST VERSION OF THIS LINE WAS `^shoved$` AND MATCHED NOTHING, with
    # the paragraph forty lines above it explaining why. The `--catalogue`
    # check now refuses a pattern that cannot match, so the next one fails
    # here rather than on Jafar's machine.
    ("shoved",       "A", [r"^shoved\b", r"\bshove reaction\b",
                           r"\bshoved reaction\b"]),
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
    # EXACT PHRASE FIRST, or the catwalk wins. `\bwalk(ing)? start\b`
    # matches "Catwalk Walk Start Turn 180 Left" — "catwalk" ENDS in
    # "walk", so the word boundary passes — and pattern order decided the
    # pick before "Start Walking" was ever tried. Depth 0 then recorded it
    # `exact: true`, so a fashion-runway sashay shipped as the town's
    # walk-start with nothing flagging it. Anchored plain forms go first;
    # the loose form stays as the fallback it should have been.
    ("walk_start",   "B", [r"^start walking\b", r"\bstart walking\b",
                           r"\bwalk(ing)? start\b"]),
    ("walk_stop",    "B", [r"^stop walking\b", r"\bstop walking\b",
                           r"\bwalk(ing)? stop\b"]),
    ("stairs_up",    "B", [r"\bascending stairs\b"]),
    ("stairs_down",  "B", [r"\bdescending stairs\b"]),

    # ---- TIER B2: the street stops walking in lockstep (playtest push).
    # Every name below was verified present in `_catalogue.txt` on 15 Aug
    # before being asked for — these are reads of the harvest, not guesses.
    ("walk_old",     "B", [r"^old man walk\b"]),
    ("idle_old",     "B", [r"^old man idle\b"]),
    ("walk_start_f", "B", [r"^female start walking\b"]),
    ("walk_stop_f",  "B", [r"^female stop walking\b"]),
    ("lean_wall",    "B", [r"^leaning on a wall\b", r"\bone shoulder lean\b"]),
    ("carry",        "B", [r"^carrying\b"]),
    ("carry_bag",    "B", [r"^walking with shopping bag\b"]),
    ("idle_bored",   "B", [r"^bored\b"]),
    ("idle_2",       "B", [r"^standing idle 0?1\b", r"^neutral idle\b"]),
    ("argue",        "B", [r"^standing arguing\b"]),
    # Payphones exist in this world; pocket phones do not. The pattern is
    # anchored so "Talking On A Cell Phone" and "Texting" can never match.
    ("phone_box",    "B", [r"^talking on phone\b"]),

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

    # ---- TIER B3: HALF THIS TOWN IS WOMEN AND ALL OF THEM WALK LIKE A MAN.
    #
    # `walk_f` is the one that matters and it is the cheapest fix in the
    # project: `Female Walk` has been sitting in the harvest since the first
    # run, the catalogue lists it at line 717, and nothing ever asked for it.
    # The archetype that consumes it already exists in `CharacterPrefab` —
    # `walk_old`/`idle_old` proved the shape — so this is a WANTS line and a
    # name, not a system.
    #
    # `jog` fills a real hole rather than adding variety: the locomotion blend
    # tree runs idle at 0, walk at 1.4 and run at 4.0, so everything between a
    # stroll and a sprint is a walk cycle played fast. An escort hurrying at
    # 2.6 m/s is exactly that case and it is on the street every run.
    #
    # Every name below was checked against `_catalogue.txt` before being
    # asked for, which is the rule that stopped the guessed list.
    ("walk_f",       "B", [r"^female walk\b"]),
    ("jog",          "B", [r"^jog forward\b", r"^jogging\b"]),

    # ---- TIER D: what a person is DOING when they are not travelling.
    #
    # The activity layer already has fourteen states and reaches five at its
    # peak, so the ceiling is choice, not wiring. These are the gestures a
    # street actually contains: giving directions, refusing, waiting, going
    # through your pockets, glancing behind you. Every one is a read of the
    # catalogue.
    #
    # THEY ARRIVE BEFORE THEIR CONSUMERS ON PURPOSE, and that is rule 6 with
    # its eyes open: Jafar is away from the Windows machine until Friday and
    # the harvest only exists there, so the choice is clips-then-wiring or
    # three days of neither. The wiring is mine and it is not blocked.
    ("wave",         "D", [r"^waving\b", r"^waving gesture\b"]),
    ("shake_hands",  "D", [r"^shaking hands 1\b", r"^shaking hands\b"]),
    ("point",        "D", [r"^pointing\b", r"^pointing gesture\b"]),
    ("thinking",     "D", [r"^thinking\b"]),
    ("laugh",        "D", [r"^laughing\b"]),
    ("yell",         "D", [r"^yelling\b", r"^yelling while standing\b"]),
    ("head_no",      "D", [r"^shaking head no\b"]),
    ("glance",       "D", [r"^look over shoulder\b"]),
    ("pockets",      "D", [r"^searching pockets\b"]),
    ("rummage",      "D", [r"^rummaging\b"]),
    ("lift",         "D", [r"^lifting object\b", r"^lifting\b"]),
    ("sit_talk",     "D", [r"^sitting talking\b"]),
    ("sit_drink",    "D", [r"^sitting drinking\b"]),
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


def content(path, cache):
    """SHA256 of one harvest file, remembered. Only candidates get hashed —
    hashing the whole harvest would read a gigabyte to answer a question
    about forty files."""
    if path not in cache:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        cache[path] = h.hexdigest()
    return cache[path]


#: THE POSTURE CHECK, AND IT ASSERTS ONLY WHAT THE DISTRIBUTION SUPPORTS.
#:
#: On 18 August the contact sheet showed ten clips playing something other than
#: their name, and the picker was cleared of blame: every file carried the right
#: Mixamo title and the dryrun read 65 exact / 2 substitute / 0 missing. The
#: mismatch is between a harvest file's NAME and its CONTENTS, which no
#: name-based check can ever see — the same shape as the duplicate-bytes fault
#: above, one layer deeper.
#:
#: What a FILE can prove is where the hips are. Printing the median hip height
#: of all 67 shipped clips, sorted, gives one clean gap and one crowded band:
#:
#:     7 jog · 9 get_up · 14 knockdown · 18 sit_drink        <- on the floor
#:        ...nothing at all between 18 and 60...
#:     60 carry_bag · 64 idle_bored · 68 guard_exit · 69 head_no · 72 thinking
#:     73 turn_right · 74 block_broken · 74 RUN · 76 walk_stop
#:     80..103 everything else
#:
#: So FLOOR_CM sits at 39, in the middle of a 42cm gap with nothing in it. That
#: is the only bound the evidence carries.
#:
#: IT DELIBERATELY DOES NOT POLICE THE CROUCH BAND. `run` reads 74 and is
#: correct; `walk_stop` reads 76 and looks wrong on the sheet. Any bound that
#: separates them rejects a correct clip, which is rule 5b's ratchet, so those
#: stay a person's judgement. This catches `jog` (7, a body on the floor),
#: `lie_still` (96, an upright stride) and `collapse` (103 flat, a death that
#: never falls) and honestly catches nothing else.
FLOOR_CM = 39.0

#: Slots whose posture is unambiguous. Everything absent is unchecked ON
#: PURPOSE — the sitting slots because the evidence is contradictory
#: (`sit_drink` reads 18 against `sit_talk` at 94 and nothing says which is
#: right), and `get_up`, `shoved`, `take_hit` and `stagger` because they are
#: transitions that may legitimately be anywhere.
POSTURE = {
    # Must spend most of the clip DOWN.
    "lie_still": "floor",
    # Must START upright and REACH the floor. A death or a knockdown that
    # never goes down is the exact fault found on 18 August.
    "collapse": "falls", "knockdown": "falls", "fall_stairs": "falls",
    # Must never be on the floor.
    "walk": "upright", "walk_f": "upright", "walk_old": "upright",
    "walk_start": "upright", "walk_start_f": "upright",
    "walk_stop": "upright", "walk_stop_f": "upright",
    "run": "upright", "jog": "upright", "back_away": "upright",
    "idle": "upright", "idle_2": "upright", "idle_old": "upright",
    "idle_bored": "upright", "talk": "upright", "argue": "upright",
    "greet": "upright", "wave": "upright", "point": "upright",
    "thinking": "upright", "glance": "upright", "head_no": "upright",
    "laugh": "upright", "yell": "upright", "smoke": "upright",
    "drink": "upright", "lean": "upright", "lean_wall": "upright",
    "pockets": "upright", "rummage": "upright", "lift": "upright",
    "carry": "upright", "carry_bag": "upright", "work_counter": "upright",
    "phone_box": "upright", "shake_hands": "upright", "shove": "upright",
    "look_around": "upright", "turn_left": "upright", "turn_right": "upright",
    "stairs_up": "upright", "stairs_down": "upright", "hands_up": "upright",
    "guard": "upright", "guard_enter": "upright", "guard_exit": "upright",
    "block_start": "upright", "block_hold": "upright", "block_end": "upright",
    "block_broken": "upright", "strike": "upright", "strike_alt": "upright",
    "draw_gun": "upright", "draw_holster": "upright", "draw_reach": "upright",
}


def _motion():
    """`tools/clip-motion.py`, loaded by path because its filename is not an
    importable identifier.

    THE READER IS NOT REIMPLEMENTED HERE. A first draft of this function
    re-derived the hips from the FBX tree, which is one idea with two
    implementations — the shape CLAUDE.md records as the single most repeated
    fault in this project, where the copy nobody looks at is the one missing a
    line. clip-motion already parses the file, finds `mixamorig:Hips`, refuses
    when the hips are PARENTED (local curves would not be world motion there),
    and reports hipLow/hipCm/hipHigh. This calls that.
    """
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(
        "clip_motion", os.path.join(here, "..", "clip-motion.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_CM = None


def hip_cm(path):
    """(lowest, median, highest) hip height in centimetres, or None.

    None means the file could not be read, and None must NEVER be treated as a
    failed posture — a reader that cannot open a file has not found a fault
    (rule 3b). The caller accepts the candidate in that case.
    """
    global _CM
    try:
        if _CM is None:
            _CM = _motion()
        r = _CM.measure(path)
        if "error" in r or "hipCm" not in r:
            return None
        return r["hipLow"], r["hipCm"], r["hipHigh"]
    except Exception:
        return None


def posture_ok(slot, path):
    """(ok, why). `why` is empty when the candidate is accepted."""
    want = POSTURE.get(slot)
    if want is None:
        return True, ""
    h = hip_cm(path)
    if h is None:
        return True, ""                 # unreadable is not a fault
    lo, md, hi = h
    if want == "floor" and md >= FLOOR_CM:
        return False, f"hips sit at {md:.0f}cm — upright, not on the floor"
    if want == "upright" and md < FLOOR_CM:
        return False, f"hips sit at {md:.0f}cm — on the floor, not upright"
    if want == "falls" and not (lo < FLOOR_CM and hi >= 80.0):
        return False, (f"hips run {lo:.0f}..{hi:.0f}cm — it never goes from "
                       f"standing to the floor")
    return True, ""


def pick(items, patterns, taken=None, cache=None, slot=None):
    """First pattern with a hit wins; within a pattern, the SHORTEST name wins.

    Shortest because Mixamo names extra variants by suffixing — "Walking",
    "Walking Backwards", "Walking While Texting" — so the bare name is nearly
    always the plain version of the motion, and the plain version is the one a
    game blends from.

    AND A CANDIDATE WHOSE BYTES ARE ALREADY IN ANOTHER SLOT IS SKIPPED, which
    is a fix for a fault upstream of this script. The harvester downloaded
    `Shove Reaction` and `Talking` as two names over one file, and every check
    in this pipeline was name-based, so both slots reported `exact: true`
    against two different patterns and one of them shipped the wrong motion
    for weeks. A name cannot detect that; only the content can. Skipping to
    the next candidate is the right response rather than failing, because the
    catalogue usually holds another name for the same motion — and when it
    does not, the slot goes MISSING, which is a report rather than a silent
    wrong answer.
    """
    for depth, pat in enumerate(patterns):
        rx = re.compile(pat)
        hits = [it for it in items if rx.search(it[0])]
        hits.sort(key=lambda it: (len(it[0]), it[0]))
        for hit in hits:
            if taken is None:
                return hit, depth, None
            digest = content(hit[2], cache)
            if digest in taken:
                print(f"    duplicate content: {hit[1]} is byte-identical to "
                      f"the clip already taken for '{taken[digest]}' — skipping")
                continue
            ok, why = posture_ok(slot, hit[2])
            if not ok:
                print(f"    wrong posture: {hit[1]} — {why} — skipping")
                continue
            return hit, depth, digest
    return None, -1, None


#: Where the last real harvest's listing lives once it has been committed.
#: This is the whole catalogue as MixamoHarvester named it, 2,846 lines, and
#: it is the only description of the harvest that exists on this side.
CATALOGUE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "..", "ledger", "Assets", "Characters",
                         "_catalogue.txt")


def dryrun(catalogue_path=CATALOGUE, verbose=True):
    """WHICH SLOTS WOULD FIND A CLIP, checked against the committed listing
    rather than against the harvest — which lives on a machine this container
    never sees.

    WHY THIS EXISTS, and it is the most expensive lesson in this file. On 18
    August I added seventeen slots, wrote every pattern with a `$` anchor, and
    Jafar ran the pick. Fourteen came back MISSING. The paragraph forbidding
    `$` anchors is at the top of THIS FILE, thirty lines above the block I was
    typing into, and I had read it that morning — MixamoHarvester appends the
    character id to every name, so `^waving$` cannot match `waving 2dee24f8...`
    and never could.

    The fix is not remembering. The catalogue has been committed since the
    first run, so every pattern can be tried against real names HERE, in
    milliseconds, with no harvest and no Windows machine. A slot that cannot
    match is a bug in the pattern, and it is now caught before anybody runs
    anything.

    Returns (missing, substituted, matched) as lists of (slot, name)."""
    if not os.path.isfile(catalogue_path):
        return None, None, None
    items = []
    with open(catalogue_path, encoding="utf-8") as fh:
        for line in fh:
            stem = line.strip()
            if stem:
                items.append((flatten(stem), stem, None))

    missing, substituted, matched = [], [], []
    for slot, _tier, patterns in WANTS:
        hit, depth, _digest = pick(items, patterns)
        if hit is None:
            missing.append((slot, patterns))
        elif depth == 0:
            matched.append((slot, hit[1]))
        else:
            substituted.append((slot, hit[1]))
    if verbose:
        for slot, patterns in missing:
            print("  WOULD MISS  %-14s — none of %d pattern(s) match any of "
                  "the %d catalogued names" % (slot, len(patterns), len(items)))
        for slot, name in substituted:
            print("  substitute  %-14s <- %s" % (slot, name))
        print("catalogue %d names: %d exact, %d substitute, %d missing"
              % (len(items), len(matched), len(substituted), len(missing)))
    return missing, substituted, matched


def matching_enough(matched):
    """A ZERO NEEDS A DENOMINATOR (rule 3b). "No slot is missing" is also what
    an empty catalogue and a broken reader both print, so the dry run has to
    say how many slots it positively MATCHED before its silence means
    anything. Two thirds is a floor, not a target: the list legitimately
    carries substitutes, and this exists to catch "nothing was tried"."""
    return len(matched) >= (2 * len(WANTS)) // 3


def selftest():
    """BOTH OUTCOMES OF THE CONTENT CHECK, on a harvest built here.

    Rule 5b: a guard is shipped only when the case it must ACCEPT has been
    watched run, not just the case it must reject. The accepting case is
    the one that goes unrun and the one that costs a day — a picker that
    refuses everything and a picker that works are the same summary line.
    """
    import tempfile

    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        def write(name, body):
            p = os.path.join(tmp, name + ".fbx")
            with open(p, "wb") as fh:
                fh.write(body)
            return p

        # Two names over one file is exactly what the harvester did, and a
        # third name carries the same motion honestly.
        write("Talking", b"CLIP-ONE")
        write("Shove Reaction", b"CLIP-ONE")
        write("Shoved", b"CLIP-TWO")
        write("Walking", b"CLIP-THREE")
        items = catalogue(tmp)

        taken, cache = {}, {}

        # ACCEPTING: an uncontested slot picks its clip, first pattern.
        hit, depth, digest = pick(items, [r"^walking\b"], taken, cache)
        if hit is None or hit[1] != "Walking" or depth != 0:
            failures.append("an uncontested slot did not pick its own clip")
        else:
            taken[digest] = "walk"

        # ACCEPTING: the first claimant of a shared file still gets it.
        hit, depth, digest = pick(items, [r"^talking\b"], taken, cache)
        if hit is None or hit[1] != "Talking":
            failures.append("the first claimant of a duplicate was refused")
        else:
            taken[digest] = "talk"

        # REJECTING: the second claimant is skipped onto the next candidate
        # rather than shipping the same bytes under another name.
        hit, depth, digest = pick(
            items, [r"^shoved$", r"\bshove reaction\b"], taken, cache)
        if hit is None:
            failures.append("the duplicate skip left the slot empty when an "
                            "alternative existed")
        elif hit[1] != "Shoved":
            failures.append("the second claimant took %r, the duplicate"
                            % hit[1])

        # REJECTING, with no way out: a slot whose ONLY candidate is already
        # taken must report MISSING rather than duplicate it silently.
        hit, _depth, _digest = pick(items, [r"\bshove reaction\b"], taken, cache)
        if hit is not None:
            failures.append("a slot with only a duplicate candidate was "
                            "given it anyway")

        # THE POSTURE CHECK, BOTH WAYS, against the clips actually shipped.
        # A fixture proves nothing here: the whole point is that a file's
        # CONTENTS disagree with its name, and only a real harvest file has
        # contents. Accepting cases first, and `run` is the important one —
        # it reads 74cm, inside the crouch band, and any bound tightened far
        # enough to catch `walk_stop` at 76 would reject it.
        shipped = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "..", "ledger", "Assets", "Characters")
        def one(slot):
            for folder in ("A", "B", "C", "D"):
                d = os.path.join(shipped, folder)
                if not os.path.isdir(d):
                    continue
                for f in os.listdir(d):
                    if f.startswith(slot + "__") and f.endswith(".fbx"):
                        return os.path.join(d, f)
            return None

        checked = 0
        for slot in ("run", "walk", "knockdown", "walk_stop"):
            f = one(slot)
            if f is None:
                continue
            checked += 1
            ok, why = posture_ok(slot, f)
            if not ok:
                failures.append("posture rejected %s, which is correct: %s"
                                % (slot, why))
        for slot in ("jog", "lie_still", "collapse"):
            f = one(slot)
            if f is None:
                continue
            checked += 1
            ok, _why = posture_ok(slot, f)
            if ok:
                failures.append("posture accepted %s, which the contact sheet "
                                "and the hip height both say is wrong" % slot)
        if checked == 0:
            failures.append("the posture check ran against nothing — no "
                            "shipped clips found, so neither case was tested")

        # AND AN UNREADABLE FILE IS NOT A FAULT (rule 3b): a reader that
        # cannot open something has not found anything.
        ok, _why = posture_ok("walk", os.path.join(tmp, "not-an-fbx.txt"))
        if not ok:
            failures.append("an unreadable file was treated as a bad posture")

        # And the check must not fire on distinct files, or it would empty
        # the harvest one slot at a time.
        if len(set(cache.values())) < 3:
            failures.append("three distinct files did not hash to three values")

    # A `$` ANCHOR CAN NEVER MATCH, so a pattern carrying one is a bug however
    # right it looks. The rule was prose at the top of this file and prose does
    # not run; fourteen slots were lost to it in one afternoon.
    for slot, _tier, patterns in WANTS:
        for pat in patterns:
            if pat.rstrip().endswith("$"):
                failures.append("%s: pattern %r ends in $ — the harvester "
                                "appends the character id, so it cannot match"
                                % (slot, pat))

    # AND EVERY SLOT MUST MATCH A REAL NAME. The `$` rule catches one way of
    # writing an impossible pattern; this catches all of them, including the
    # ones nobody has thought of, by trying them against the 2,846 names the
    # last harvest actually produced.
    missing, _sub, matched = dryrun(verbose=False)
    if missing is None:
        failures.append("no committed catalogue to check the patterns against")
    else:
        for slot, patterns in missing:
            failures.append("%s: no catalogued name matches any of %d "
                            "pattern(s)" % (slot, len(patterns)))
        # The denominator, so "nothing missing" cannot mean "nothing tried".
        if not matching_enough(matched):
            failures.append("only %d slot(s) matched the catalogue — the "
                            "listing or the reader is wrong, not the patterns"
                            % len(matched))

    for f in failures:
        print("  FAIL: %s" % f)
    if failures:
        print("SELFTEST FAILED -- %d failure(s)" % len(failures))
        return 1
    print("SELFTEST PASSED -- duplicate content is skipped, distinct content "
          "is not, and a slot with no alternative reports missing")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true",
                    help="check the picker against a harvest built here")
    ap.add_argument("--dryrun", action="store_true",
                    help="try every pattern against the committed catalogue")
    ap.add_argument("--harvest", default=None,
                    help="the MixamoHarvester 'animations' folder")
    ap.add_argument("--out", default=None,
                    help="where to copy picks (default: ledger/Assets/Characters)")
    ap.add_argument("--tiers", default="ABCD",
                    help="which tiers to copy, e.g. 'A' for combat only")
    args = ap.parse_args()

    if args.dryrun:
        missing, _sub, _matched = dryrun()
        if missing is None:
            print("no committed catalogue at %s" % os.path.normpath(CATALOGUE))
            return 2
        return 1 if missing else 0
    if args.selftest:
        return selftest()
    if not args.harvest:
        print("--harvest is required (or --selftest)")
        return 2
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
    # {content hash: the slot that claimed it}, so a collision can name the
    # other slot rather than just refusing.
    taken, hash_cache = {}, {}
    for slot, tier, patterns in WANTS:
        if tier not in args.tiers:
            continue
        hit, depth, digest = pick(items, patterns, taken, hash_cache, slot=slot)
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
        if digest is not None:
            taken[digest] = slot
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
