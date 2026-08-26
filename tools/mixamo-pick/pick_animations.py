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
import contextlib
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
    ("block_hold",   "A", [r"\bstanding block idle\b", r"^blocking\b",
                            r"^standing block\b", r"^block\b", r"^center block\b"]),
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
    # `Grabbing Pistol` FIRST, AND IT IS THE SECOND HARVESTER DUPLICATE.
    #
    # `Unarmed Equip Underarm_4f5d21e1` and `Standing Arguing_4f5d21e1` are
    # byte-identical — the content check found it on the 21 August re-pick and
    # skipped `argue` onto `Angry Gesture`, because tier A runs first and
    # `draw_reach` had already claimed the bytes. So the collision was
    # REPORTED and resolved in favour of the slot that happened to go first,
    # which is not the same as resolved correctly.
    #
    # Which name is right cannot be read out of the bytes, exactly as with
    # `Shove Reaction` / `Talking`. The DURATION can be read, and it says this
    # is not a draw: 20.80s, third longest in the whole set, against a median
    # of 2.00s and a p90 of 7.57s. The only two longer clips are a sitting
    # conversation and a phone call, both loops that are meant to run. Every
    # other one-shot gesture in the set — strike, shove, take_hit, draw_gun —
    # sits near the median. A man reaching under his coat does not take twenty
    # seconds; a man arguing does.
    #
    # `Grabbing Pistol` is a third name for the motion actually wanted, and the
    # game already draws a pistol (`draw_gun` <- `Drawing Gun`). Taking it
    # sidesteps the collision with no re-download, which is the `Shoved` move
    # that worked last time. Verified present in the catalogue — the selftest
    # now names any pattern that matches nothing, so a dead alternative cannot
    # sit here looking like a fallback.
    # AND `Grabbing Pistol` WAS THE WRONG REPLACEMENT, MEASURED ONE RUN LATER.
    # The duplicate half above was right — `argue` took `Standing Arguing`
    # back and it reads 20.80s, 26.84cm of hip motion, 39 degrees of turn,
    # hips 96/97/99, travel 0.00, which is an argument exactly. The clip I
    # sent here instead is a man ON THE FLOOR: hips 46/46/47cm flat for 6.70
    # seconds, against 88-104 for every other upright clip in the set. It is
    # somebody crouching to pick a pistol up off the ground, and it tripped
    # the frozen-root rule because a crouched body holding still is frozen.
    #
    # NOT EXEMPTED, and the temptation to was the whole lesson: a frozen root
    # IS definitional for `lie_still`, and reasoning from what the slot name
    # means would have waved this through on the same argument. The hip
    # reading is what separated them, and it took ten seconds to look at.
    #
    # `Draw Sword 1` instead — the sibling of `Sheath Sword 1`, which
    # `draw_holster` already uses and which reads 52..99cm, a body standing up
    # into a reach. No swords in a British port town; what is wanted is the
    # BODY motion of reaching across yourself, and the neighbouring slot has
    # been getting it from this family since it was picked.
    #
    # `unarmed equip underarm` stays, LAST, so it can never outrank `argue`
    # for those bytes again.
    ("draw_reach",   "A", [r"\bdraw sword 1\b", r"\bdraw(ing)? sword\b",
                           r"\bgrabbing pistol\b", r"\bunarmed equip underarm\b"]),
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
    #
    # AND THAT FIX WAS FOR A DIFFERENT FAULT AND DOES NOT CATCH THIS ONE.
    # `^start walking\b` matches "Start Walking Backwards" — which is what
    # shipped, and what `walk_start` still holds on disk. The exclusion lives
    # in FORWARD_ONLY/`direction_ok` rather than in this regex, because it is
    # the same rule for eleven other slots and a per-pattern lookahead is one
    # idea in fourteen implementations.
    #
    # THE COMMENT THAT STOOD HERE NAMED THE WRONG PATTERN AND THE WRONG COUNT.
    # It said depth 2 was the sashay risk and that "all 8 of its candidates are
    # Catwalk variants". Measured against the 2,846-name catalogue, depth 2's
    # candidates are Female Start Walking, Female Stop And Start Walking and
    # Scary Clown Start Walking — three names, none of them Catwalk. The four
    # Catwalk names are reached by DEPTH 3, `\bwalk(ing)? start\b`, and depth 3
    # in `walk_stop` reaches two Catwalk names and nothing else at all.
    #
    # SO DEPTH 3 IS DELETED FROM BOTH, and it is a measurement rather than a
    # taste: a pattern whose entire candidate set is runway clips has no
    # honest use here. What is left is screened — `gender_ok` refuses the
    # female names and `turn_ok` refuses the turns — so these slots come back
    # EMPTY, which is the answer this file already argues for where it refuses
    # the backwards clip: an empty slot falls back to the locomotion tree, a
    # wrong one does not. The remaining depth-2 name, `Scary Clown Start
    # Walking`, is NAMED AND NOT GUARDED: see `turn_ok` for why a costume
    # screen was written, measured against the shipped clips, and withdrawn.
    ("walk_start",   "B", [r"^start walking\b", r"\bstart walking\b"]),
    ("walk_stop",    "B", [r"^stop walking\b", r"\bstop walking\b"]),
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
    ("argue",        "B", [r"^standing arguing\b", r"^angry gesture\b",
                            r"^angry point\b", r"^standing yell\b", r"^angry\b"]),
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
    ("lie_still",    "C", [r"^laying idle\b", r"^laying\b", r"^laying breathless\b",
                            r"\blying down\b", r"\blying\b", r"\bdead\b"]),

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
    ("pockets",      "D", [r"^searching pockets\b", r"^patting\b"]),
    ("rummage",      "D", [r"^rummaging\b", r"^picking up object\b",
                            r"^picking up\b", r"^digging\b"]),
    ("lift",         "D", [r"^lifting object\b", r"^lifting\b"]),
    ("sit_talk",     "D", [r"^sitting talking\b"]),
    ("sit_drink",    "D", [r"^sitting drinking\b", r"^sitting dazed\b",
                            r"^sitting\b"]),
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


#: DOES IT GO ANYWHERE, WHICH IS THE SECOND AXIS AND THE ONE THAT CATCHES MOST.
#:
#: Hip height answers "upright or on the floor" and closes five slots. Travel
#: answers "does this move", and on 19 August it flagged nineteen — because the
#: harvest's names do not reliably describe its contents, and travel is the
#: cheapest way to see that from a file.
#:
#: I had this backwards first. The travel column read `Walking` 0.00 and
#: `Standing Arguing` 3.75m and I wrote it off as untrustworthy, reasoning that
#: a standing argument cannot travel. It can, if the file called
#: `argue__Standing_Arguing` does not contain a standing argument — and the
#: contact sheet says it does not: `idle` renders mid-stride, `talk` renders as
#: locomotion, `pockets` and `laugh` are people walking, `guard` is a throw, and
#: `walk` is a stationary guard pose. The column was telling the truth about
#: files that lie, and dismissing it cost most of a day.
#:
#: THE BOUNDS ARE THE MEASURED GAP, NOT A GUESS. Every clip that renders as
#: locomotion travels 1.0m or more; every clip that renders stationary and is
#: correct sits at 0.00-0.06m. 0.15 and 0.5 leave that gap wide open on both
#: sides, so a slow shuffle is not called a walk and a gesture that drifts a
#: hand's width is not called a journey.
TRAVELS_MIN = 0.15          # metres, for a slot whose name means locomotion
STILL_MAX = 0.50            # metres, for a slot whose name means standing

#: Slots whose NAME says they go somewhere. Absent slots are unchecked.
GOES = {"walk", "walk_f", "walk_old", "run", "jog", "back_away", "walk_start",
        "walk_start_f", "walk_stop", "walk_stop_f", "stairs_up", "stairs_down",
        "carry_bag"}

#: Slots whose NAME says they stay put. `lie_still` is here as well as in
#: POSTURE: it must be on the floor AND not walk about on it.
STAYS = {"idle", "idle_2", "idle_old", "idle_bored", "talk", "argue", "greet",
         "wave", "point", "thinking", "glance", "head_no", "laugh", "yell",
         "smoke", "drink", "lean", "lean_wall", "pockets", "rummage",
         "work_counter", "phone_box", "shake_hands", "sit", "sit_talk",
         "sit_drink", "block_hold", "block_start", "guard", "lie_still"}


#: WHICH WAY IT GOES — THE THIRD AXIS, AND THE ONLY ONE NO FILE CAN ANSWER.
#:
#: The shipped `walk_start` is `Start Walking Backwards`. Every man in the city
#: would have set off backwards the moment the transitions were wired, and
#: nothing in this tool could see it, because DIRECTION IS NOT IN THE FILE.
#: `clip-motion`'s travel is `hypot(dX, dZ)` — a magnitude — so a walk and its
#: reverse both read 0.94m, and hip height is identical either way. The name is
#: the only witness there is.
#:
#: MEASURED HISTORY, not reconstructed — read from `_picks.json` at three
#: commits and from the dropped clip itself, pulled out of git at `dfe2eb4f`:
#:
#:   30 Jul  367560f7  walk_start <- Catwalk Walk Start Turn 180 Left  (the
#:                     catwalk mis-pick; fixed by anchoring the phrase)
#:   17 Aug  dfe2eb4f  walk_start <- Start Walking                     (CORRECT)
#:   21 Aug  7fdd0951  walk_start <- Start Walking Backwards           (the fault)
#:
#: So the anchored-phrase fix was working. What moved the pick was the TRAVEL
#: screen landing on 21 August: the forward `Start Walking` reads hips
#: 100.1..100.4cm, travel 0.0000m, moved 0.30cm, turned 0.5° — an in-place
#: export with a frozen root — so `motion_ok` refused it as "a locomotion slot
#: holding a clip that stays put", and the next candidate down the same pattern
#: was the backwards clip, which travels 0.94m and passes every screen there
#: was. A screen written to reject a bad clip walked the pick onto a worse one.
#:
#: THE VOCABULARY IS A READ OF THE CATALOGUE, NOT A GUESS: 2,846 names, and
#: `backward`/`backwards` is the only reversal word Mixamo actually uses on a
#: locomotion clip (`Walking Backwards`, `Start Walking Backwards`, `Jog
#: Backward`, `Crouch Walk Backwards Stop`). `reverse`/`mirror`/`inverted` are
#: carried anyway — they cost nothing, they name what the screen is FOR, and
#: `Inverted Double Kick To Kip Up` proves the harvest does reach for that
#: family. A word BOUNDARY, so a name that merely ends in one of them cannot
#: trip it.
REVERSED = re.compile(r"\b(backward|backwards|reverse|reversed|"
                      r"mirror|mirrored|inverted)\b")

#: Slots whose motion is FORWARD by definition. `back_away` IS DELIBERATELY
#: ABSENT and is the accepting case that matters: retreating is its whole job,
#: both its patterns ask for a backward name on purpose, and it holds
#: `Walk Backward` today. A screen that refused it would be rule 5's ratchet —
#: emptying a slot the street plays to fix one that is wrong.
#:
#: `stagger` and `collapse` are absent for the same reason one step out:
#: `Stumble Backwards` is a stagger and `Dying Backwards` is a death, and both
#: sit in those slots' candidate lists honestly.
FORWARD_ONLY = {"walk", "walk_f", "walk_old", "run", "jog", "carry_bag",
                "walk_start", "walk_start_f", "walk_stop", "walk_stop_f",
                "turn_left", "turn_right", "stairs_up", "stairs_down"}


def direction_ok(slot, flat_name):
    """(ok, why). Can a clip with this NAME fill this slot.

    Name-based on purpose, and it is the one screen that can run where there is
    no file to read — the catalogue dryrun here, with the harvest on a machine
    this container never sees. It is also the only screen that CAN answer this:
    see the REVERSED comment, travel is a magnitude.

    `why` is empty when the candidate is accepted, and names the offending word
    when it is not, so a refusal in a run log says which word did it rather
    than leaving the operator to guess at a regex.
    """
    if slot not in FORWARD_ONLY:
        return True, ""
    m = REVERSED.search(flat_name)
    if m is None:
        return True, ""
    return False, ("the name says %r — a forward slot cannot take a reversed "
                   "clip, and no reading of the FILE can tell them apart"
                   % m.group(0))

#: A CLIP WHOSE NAME SAYS FEMALE, FOR THE GENDERED-SLOT SCREEN BELOW.
FEMALE = re.compile(r"\bfemale\b", re.I)

#: Slots that have an `_f` twin in SLOTS. The general one must not eat the
#: twin's clip.
def _twinned_slots():
    names = {row[0] for row in WANTS}
    return {n for n in names if n + "_f" in names}

TWINNED = _twinned_slots()


def gender_ok(slot, flat_name):
    """A general slot may not take a clip whose NAME says female.

    WHY THIS EXISTS, 26 Aug. `walk_start`'s patterns are anchored first
    (`^start walking`) and unanchored second (`\bstart walking\b`). No male
    start clip was in the harvest, so the anchored pattern found nothing, the
    unanchored one matched `Female Start Walking`, and the SAME FILE landed in
    both `walk_start` and `walk_start_f`. `clip-motion` caught it as a
    duplicate — "one slot in each group plays the wrong clip, and the filename
    cannot say which" — and it is the second time a fallback pattern has
    quietly filled a forward slot with the wrong thing, after the reversed
    clip this file already screens for.

    THE SHAPE IS `direction_ok`'S ON PURPOSE: name-based, runnable with no
    file to read, and `why` names the offending word so a refusal in the log
    says which word did it. Only slots with an `_f` twin are screened — a slot
    with no twin has nowhere else for a female clip to go, and refusing it
    there would empty the slot to no benefit.
    """
    if slot not in TWINNED:
        return True, ""
    m = FEMALE.search(flat_name)
    if m is None:
        return True, ""
    return False, ("the name says %r and %s_f exists — the general slot cannot "
                   "take the twin's clip, or both slots play one file"
                   % (m.group(0), slot))


#: A NAME THAT SAYS THE CLIP TURNS. `direction_ok` refuses a clip that goes
#: BACKWARDS; this refuses one that goes ROUND, on the same axis and for the
#: same reason - the name carries a fact about the motion that no reading of
#: the file's hips and travel can recover.
TURNS = re.compile(r"\b(turn(ing)?|twist|180|90|pivot|about face)\b", re.I)


def turn_ok(slot, flat_name):
    """A straight slot may not take a clip whose NAME says it turns.

    WHY THIS EXISTS, 26 Aug, AND WHY IT IS NOT THE GUARD I FIRST WROTE.
    `walk_start` had picked `Catwalk Walk Start Turn 180 Left`, and I read
    that as a COSTUME problem - a runway sashay - and wrote a screen refusing
    names that declare a costumed character. Run against the 65 shipped clips,
    which is the accepting fixture this project already trusts, it refused two:
    the sashay, correctly, and `idle` = `Mutant Breathing Idle`, which is the
    default idle every person in Meridian plays while standing still.

    THE NAME CANNOT ANSWER THE QUESTION I WAS ASKING IT. The catalogue holds
    Mutant Walking / Idle / Run / Jumping and Zombie Walk / Idle / Crawl in
    the SAME SHAPE: a prefix naming the rig the motion was authored on, which
    may or may not mean the motion is styled. A name-based screen cannot tell
    "the motion is a monster's" from "the file was exported off a monster",
    and shipping one would have emptied the most-seen clip in the game to fix
    a slot nobody had looked at. That is the ratchet rule 5 names - a guard
    that cannot tell a regression from an improvement.

    So the guard moved to the axis the fault is actually ON. What is wrong
    with `Catwalk Walk Start Turn 180 Left` in `walk_start` is not the
    catwalk, it is the TURN 180: the slot wants a straight start and the clip
    is a half-circle. That is a motion fact, it is in the name, and it screens
    every one of depth 3's candidates in both slots - two Turn 180s (here),
    two Backwards (already refused by `direction_ok`), two Stop Twists.
    Measured against the shipped 65: it refuses ONE, and that one is the
    sashay.

    NAMED AND NOT GUARDED, because the honest answer is that nothing here can
    settle it: `walk_start`'s remaining depth-2 candidate is `Scary Clown
    Start Walking`, and whether that walk is a clown's or a man's exported off
    a clown rig can only be answered by looking at it. `gender_ok` refuses the
    other two depth-2 names, so with depth 3 deleted the slot comes back EMPTY
    - which this file already argues is the right answer where it refuses the
    backwards clip: an empty slot falls back to the locomotion tree, a wrong
    one does not.

    THE SCREEN CONFIGURES ITSELF FROM `WANTS`, so a slot that asks for a turn
    gets one: if the slot's own patterns name the turn word, the clip passes.
    The selftest asserts both directions.
    """
    m = TURNS.search(flat_name)
    if m is None:
        return True, ""
    word = m.group(0).lower()
    for name, _tier, pats in WANTS:
        if name == slot and any(word in pat.lower() for pat in pats):
            return True, ""            # asked for on purpose
    return False, ("the name says %r — this slot wants a straight motion and "
                   "the clip turns, which no reading of the FILE's hips and "
                   "travel can tell you" % m.group(0))


#: THE REJECTING CASE FOR THE SCREEN, KEPT WHERE A RE-PICK CANNOT REACH IT.
#: Each entry is (file under `known-bad/`, the slot to ask it as, a fragment of
#: `why` that names the branch), one per branch of `posture_ok`.
#:
#: It lives in a fixture directory because the rejecting half used to point at
#: the SHIPPED clips, and that only failed once the guard worked: the 21 August
#: re-pick replaced five of the six bad clips it named, so five assertions went
#: red for the best possible reason. The sixth survived only because
#: `lie_still` found no replacement and its bad file stayed on disk — fix that
#: slot and the rejecting half tests nothing while still printing PASSED, since
#: a loop over absent slots runs zero times. Rule 5b's corollary: plant the
#: condition, do not loosen the bound.
#:
#: Two are asked under a slot that is not their own because `posture_ok` runs
#: the motion axis FIRST, so no clip can reach the hip axis under a slot the
#: motion axis already refuses. See known-bad/README.md.
KNOWN_BAD = [
    ("walk__Walking_2dee24f8-3b49-48af-b735-c6377509eaac.fbx",
     "walk", "clip that stays put"),
    ("laugh__Laughing_2dee24f8-3b49-48af-b735-c6377509eaac.fbx",
     "laugh", "clip that goes somewhere"),
    ("jog__Jog Forward_4f5d21e1-4ccc-41f1-b35b-fb2547bd8493.fbx",
     "hands_up", "not upright"),
    ("walk__Walking_2dee24f8-3b49-48af-b735-c6377509eaac.fbx",
     "lie_still", "not on the floor"),
    ("fall_stairs__Falling From Losing Balance"
     "_2dee24f8-3b49-48af-b735-c6377509eaac.fbx",
     "collapse", "never goes from standing to the floor"),
]


def screens(slot):
    """Which axes `posture_ok` will actually apply to this slot.

    An empty list means the slot is UNCHECKED — it can neither pass nor fail,
    so counting it as an accepting case pads the denominator with a test that
    did not happen. `get_up` sat in the accepting list doing exactly that: it
    reads 8..11cm hips through a clip called Stand Up, and passed every run,
    because it is in neither POSTURE nor GOES/STAYS on purpose.
    """
    axes = []
    if slot in GOES or slot in STAYS:
        axes.append("motion")
    if slot in POSTURE:
        axes.append(POSTURE[slot])
    return axes


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


def travel_m(path):
    """How far the clip goes, first to last, horizontally. None if unreadable."""
    global _CM
    try:
        if _CM is None:
            _CM = _motion()
        r = _CM.measure(path)
        return None if "error" in r or "travel" not in r else r["travel"]
    except Exception:
        return None


def frozen_root(path):
    """(is_frozen, movedCm, turnedDeg). (None, 0, 0) when unreadable.

    THE READING COMES FROM `clip-motion`, NOT FROM A SECOND COPY OF THE RULE.
    Its `measure()` already returns the flag and both bounds, and this module
    already loads it for hips and travel — so asking it one more question costs
    nothing, while re-deriving "moved less than a centimetre and turned less
    than two degrees" here would be the one-idea-two-implementations fault this
    project keeps paying for.
    """
    global _CM
    try:
        if _CM is None:
            _CM = _motion()
        r = _CM.measure(path)
        if "error" in r or "frozen" not in r:
            return None, 0.0, 0.0
        return r["frozen"], r["movedCm"], r["turnedDeg"]
    except Exception:
        return None, 0.0, 0.0


def motion_ok(slot, path):
    """(ok, why). Does the clip go somewhere, when its name says it should.

    WHAT THE TRAVEL READING IS, because the wording here used to overclaim and
    the overclaim was pointed the wrong way. "it walks off" is a statement
    about what a player would SEE, and the game sets `applyRootMotion = false`,
    so the retargeter absorbs most of the hip track: a clip whose hips run
    3.75m measured 0.20m of drift at worst on the contact sheet.

    So the reading is a FINGERPRINT OF WHICH MOTION THE FILE HOLDS, not a
    prediction of how far a body slides — and that is the stronger claim, not
    the weaker one. A file called Smoking whose hips travel 0.68m is not a man
    smoking with a drift problem; it is a different animation under that name,
    which is exactly the fault the screen exists for and which the contact
    sheet confirmed independently for `jog` and `lie_still`.
    """
    goes, stays = slot in GOES, slot in STAYS
    if not goes and not stays:
        return True, ""
    d = travel_m(path)
    if d is None:
        return True, ""                 # unreadable is not a fault
    if goes and d < TRAVELS_MIN:
        return False, (f"hips travel {d:.2f}m — a locomotion slot holding a "
                       f"clip that stays put")
    if stays and d > STILL_MAX:
        return False, (f"hips travel {d:.2f}m — a standing slot holding a "
                       f"clip that goes somewhere")
    return True, ""


def posture_ok(slot, path):
    """(ok, why). `why` is empty when the candidate is accepted.

    Two axes: where the hips ARE (upright or on the floor) and whether the clip
    GOES anywhere. Either can reject; the first to fire says why.
    """
    ok, why = motion_ok(slot, path)
    if not ok:
        return False, why
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


def frozen_but_usable(slot, path):
    """(is_second_best, why). A frozen root is a PREFERENCE, never a refusal.

    `clip-motion` has flagged frozen roots for weeks and the picker never
    asked, so a frozen clip could be chosen and only the post-hoc audit caught
    it — one idea, two implementations, the screening half missing the check.
    It cost a round trip: `draw_reach` took `Grabbing Pistol`, somebody
    crouched on the floor picking a pistol up, hips 46cm flat for 6.70 seconds
    against 88-104 for every other upright clip. `posture_ok` passed it because
    `upright` is anything at or above 39cm.

    THE FIRST VERSION OF THIS WAS A REFUSAL AND WOULD HAVE BEEN A RATCHET.
    Run against the shipped set it also refused `lean` and `block_end` — the
    two entries the debt ledger has carried for days and describes as ARGUABLE,
    because ending a block and leaning are things a body does without its hips
    going anywhere. The catalogue holds no alternate name for either, so
    refusing them empties the slots, and `lean` is one of the fourteen the
    street actually plays. A guard that empties a visible slot to fix one
    nothing calls is rule 5's ratchet wearing a new coat.

    So: a frozen candidate is passed over while a cleaner one might still be
    found, and taken anyway if nothing better exists. `draw_reach` gets
    `Draw Sword 1`; `lean` keeps `Leaning` and stays on the ledger where it
    was already recorded and explained.

    The exemption list is `clip-motion`'s own, read rather than restated, so
    `lie_still` stays legal in both tools by construction.
    """
    frozen, moved, turned = frozen_root(path)
    if not frozen or slot in getattr(_CM, "STILL_BY_DEFINITION", ()):
        return False, ""
    return True, (f"hips move {moved:.2f}cm and turn {turned:.1f}° in the "
                  f"whole clip — animated from the waist up")


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
    fallback = None
    for depth, pat in enumerate(patterns):
        rx = re.compile(pat)
        hits = [it for it in items if rx.search(it[0])]
        hits.sort(key=lambda it: (len(it[0]), it[0]))
        for hit in hits:
            # DIRECTION FIRST, because it is the only screen that runs in both
            # paths. Everything below this line needs a file to read, so the
            # catalogue dryrun skips it — and the dryrun is the check that runs
            # HERE, on the machine with no harvest.
            ok, why = direction_ok(slot, hit[0])
            if ok:
                # The twin screen, same shape and same reason: an unanchored
                # fallback pattern put `Female Start Walking` into BOTH
                # `walk_start` and `walk_start_f` on 26 Aug.
                ok, why = gender_ok(slot, hit[0])
            if ok:
                # The third of the same family: a name that says the clip
                # goes ROUND, where `direction_ok` says it goes BACKWARDS.
                ok, why = turn_ok(slot, hit[0])
            if not ok:
                if taken is not None:
                    print(f"    wrong direction: {hit[1]} — {why} — skipping")
                continue
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
            # HELD BACK, NOT REFUSED. A frozen root is second-best rather than
            # wrong: for `lean` and `block_end` the catalogue offers nothing
            # else and the debt ledger already carries them as arguable, so
            # refusing outright would empty a slot the street plays. The first
            # one seen is kept and used only if every pattern runs dry.
            second, sw = frozen_but_usable(slot, hit[2])
            if second:
                if fallback is None:
                    fallback = (hit, depth, digest, sw)
                print(f"    frozen root: {hit[1]} — {sw} — looking for better")
                continue
            return hit, depth, digest
    if fallback is not None:
        hit, depth, digest, sw = fallback
        print(f"    nothing better than {hit[1]} — taking it ({sw})")
        return hit, depth, digest
    return None, -1, None


def set_aside(out, slot):
    """A slot that found nothing must not keep serving the clip it refused.

    THE FAILURE PATH HAD NO SLOT-CLEARING STEP. The success path clears the
    slot before copying, under a comment saying that two files in one slot
    means the wrong one is as likely to play as the right one. Every word of
    that is worse here: when the pick fails, the file left behind is the ONLY
    one, so it is certain to play, and it is the clip the screen has just
    refused. On 21 August that was eight slots at once — a corpse whose hips
    travel 2.18m, a man smoking who drifts 0.68m — every one reported MISSING
    in `_picks.json` and every one still loading, because the game reads
    filenames and nothing reads the manifest.

    THE TEST IS THE SCREEN, NOT THE PICK. A clip the patterns stopped naming
    may still be a perfectly good clip, and discarding it because a regex moved
    is the ratchet rule 5 forbids — a guard that cannot tell a regression from
    an improvement. Only a clip `posture_ok` REFUSES is set aside.

    AND SET ASIDE RATHER THAN DELETED, because rule 5 is also the 24 clips a
    cancelled CI run destroyed. `.rejected` is not an extension Unity imports,
    so the file leaves the build and stays on the disk.

    Returns the list of (filename, why) moved, so the caller has a denominator.

    AND THE DIRECTION SCREEN RUNS HERE TOO — THE TWIN SITE, WHICH WAS THE WHOLE
    FAULT ONE LAYER DOWN. `posture_ok` reads the FILE, and a backwards walk
    passes every reading in it (hips 144..150cm, travel 0.94m). So adding the
    direction guard to `pick` alone would refuse the backwards clip as a
    candidate and then leave the one already in the slot exactly where it is,
    under this function's own "no pattern names it now, but the screen still
    passes it" branch — the slot reported MISSING while the game went on
    loading a man walking backwards, which is verbatim the failure the
    paragraph above was written for. One idea, two implementations: the name
    the file was copied under is the same evidence as the name it was picked
    by, so the same function reads both.
    """
    moved = []
    for old in sorted(glob.glob(os.path.join(out, "*", f"{slot}__*.fbx"))):
        # `{slot}__{stem}.fbx` — the stem is the Mixamo name it was picked by.
        stem = os.path.basename(old)[len(slot) + 2:-len(".fbx")]
        ok, why = direction_ok(slot, flatten(stem))
        if ok:
            ok, why = gender_ok(slot, flatten(stem))
        if ok:
            ok, why = turn_ok(slot, flatten(stem))
        if ok:
            ok, why = posture_ok(slot, old)
        if ok:
            print(f"  kept      {os.path.basename(old)} — no pattern names it "
                  f"now, but the screen still passes it")
            continue
        # `os.replace`, NOT `os.rename`. This runs on Jafar's Windows machine,
        # where renaming onto an existing path raises FileExistsError — and the
        # target exists on the SECOND run for the same slot, which is exactly
        # the run this is for. `replace` overwrites on both platforms, and what
        # it overwrites is a previously-rejected copy of the same slot that is
        # already in git history.
        os.replace(old, old + ".rejected")
        moved.append((os.path.basename(old), why))
        print(f"  set aside {os.path.basename(old)} — {why}")
    return moved


#: Where the last real harvest's listing lives once it has been committed.
#: This is the whole catalogue as MixamoHarvester named it, 2,846 lines, and
#: it is the only description of the harvest that exists on this side.
CATALOGUE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "..", "ledger", "Assets", "Characters",
                         "_catalogue.txt")

#: What the last real pick actually COPIED, slot -> record. The manifest, not
#: the folder: the folder says which files are there and this says which name
#: each slot was answered with, which is the thing a name screen reads.
PICKS = os.path.join(os.path.dirname(CATALOGUE), "_picks.json")


def _picks(path=PICKS):
    """The landed manifest, or {} when there is none — so "no reversed clip
    shipped" and "no manifest was read" print differently (rule 3b)."""
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (ValueError, OSError):
        return {}


def dead_patterns(catalogue_path=CATALOGUE):
    """Every (slot, index, pattern) that matches NO catalogued name.

    `dryrun` asks whether a SLOT found something, which a slot passes on any
    one of its patterns. This asks the question of each pattern separately,
    because that is the level the answer was hiding at: ten doubled backslashes
    sat next to working patterns and no check could see them.

    Returns None when there is no catalogue, so "nothing dead" and "nothing
    read" are different answers (rule 3b).
    """
    if not os.path.isfile(catalogue_path):
        return None
    with open(catalogue_path, encoding="utf-8") as fh:
        flat = [flatten(line.strip()) for line in fh if line.strip()]
    if not flat:
        return None
    dead = []
    for slot, _tier, patterns in WANTS:
        for i, pat in enumerate(patterns):
            rx = re.compile(pat)
            if not any(rx.search(name) for name in flat):
                dead.append((slot, i, pat))
    return dead


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
        # SLOT PASSED, so the direction screen applies here as well. Without
        # it this reported `walk_start <- Start Walking Backwards` as an EXACT
        # match and the one check that runs in this container agreed with the
        # mis-pick.
        hit, depth, _digest = pick(items, patterns, slot=slot)
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

        # THE POSTURE CHECK, BOTH WAYS. Neither half uses a synthetic file:
        # the whole fault being screened for is that a file's CONTENTS
        # disagree with its name, and only a real harvest file has contents.
        # The two halves point at different real files on purpose — accepting
        # at what SHIPS, so a bad re-pick goes red here; rejecting at
        # `known-bad/`, so a good re-pick cannot empty it.
        shipped = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "..", "ledger", "Assets", "Characters")
        def one(slot):
            for folder in ("A", "B", "C", "D"):
                d = os.path.join(shipped, folder)
                if not os.path.isdir(d):
                    continue
                for f in sorted(os.listdir(d)):
                    if f.startswith(slot + "__") and f.endswith(".fbx"):
                        return os.path.join(d, f)
            return None

        # ACCEPTING: the shipped clips, INCLUDING the five the 21 August
        # re-pick fixed. They were the rejecting case until that morning, and
        # moving them across is the whole point — this half must track what
        # ships, so a future re-pick that lands a stationary walk goes red.
        #
        # `run` is the load-bearing one for the hip axis: it reads 74cm, inside
        # the crouch band, and any bound tight enough to catch `walk_stop` at
        # 76 would reject it.
        accepted, axes_seen = 0, set()
        for slot in ("run", "walk_f", "knockdown", "walk", "idle", "talk",
                     "jog", "collapse", "lie_still"):
            f = one(slot)
            if f is None:
                continue            # a missing slot is --dryrun's report, not this one
            axes = screens(slot)
            if not axes:
                failures.append("%s is in the accepting list but the screen "
                                "examines no axis on it, so it passes for free"
                                % slot)
                continue
            accepted += 1
            axes_seen.update(axes)
            ok, why = posture_ok(slot, f)
            if not ok:
                failures.append("the shipped %s clip is refused by the screen: "
                                "%s" % (slot, why))
        # The denominator, and it is a COVERAGE one rather than a count,
        # because the question is "was any axis left with nothing to accept"
        # and a count cannot answer that.
        #
        # `floor` JOINED THE LIST ON 21 AUGUST and was deliberately out of it
        # before: the only floor slot is `lie_still`, it was holding a clip
        # whose hips sat at 96cm and travelled 2.18m, and requiring an axis
        # that nothing could satisfy would have been a red gate demanding a
        # clip the harvest had not produced. The second re-pick landed
        # `Laying Idle` — 13.6cm, travel zero — so there is now an honest
        # accepting case and the axis is required.
        short = {"motion", "upright", "falls", "floor"} - axes_seen
        if short:
            failures.append("the accepting case never exercised the %s "
                            "axis — a screen with nothing to accept on an axis "
                            "is untested on it" % "/".join(sorted(short)))

        # REJECTING: the preserved bad clips, one per branch of `posture_ok`.
        # A MISSING FIXTURE IS A FAILURE, NOT A SKIP — the old version skipped
        # absent slots, which is how a re-pick could silently retire five
        # assertions at once and still print PASSED.
        bad_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "known-bad")
        refused = 0
        for fname, slot, branch in KNOWN_BAD:
            p = os.path.join(bad_dir, fname)
            if not os.path.isfile(p):
                failures.append("known-bad/%s is not there — the rejecting "
                                "case for the %r branch cannot run"
                                % (fname, branch))
                continue
            ok, why = posture_ok(slot, p)
            if ok:
                failures.append("the screen accepted known-bad/%s asked as %s"
                                % (fname, slot))
                continue
            # A REFUSAL FOR THE WRONG REASON IS A PASSING TEST ON A BROKEN
            # AXIS. The motion axis runs first and refuses most of these files
            # under their own names, so without this the hip and falls
            # branches could both be dead and every line here still green.
            if branch not in why:
                failures.append("known-bad/%s was refused as %s on the wrong "
                                "branch — %r does not mention %r"
                                % (fname, slot, why, branch))
                continue
            refused += 1
        if accepted or refused:
            print("  posture screen: %d shipped clip(s) accepted across the "
                  "%s axes, %d known-bad clip(s) refused on %d branch(es)"
                  % (accepted, "/".join(sorted(axes_seen)) or "no",
                     refused, len(set(b for _f, _s, b in KNOWN_BAD))))

        # THE DIRECTION SCREEN, AND THE ACCEPTING CASE IS FIRST BECAUSE IT IS
        # THE ONE THAT COULD EMPTY A SLOT THE STREET PLAYS. `back_away` holds
        # `Walk Backward` and must go on holding it: retreating backwards is
        # what that slot IS, and a screen that refuses it to fix `walk_start`
        # is rule 5's ratchet — a guard that cannot tell a regression from the
        # thing working.
        #
        # Names are harvester-shaped (`{animation}_{character id}`), because
        # that shape is what defeated the `$` anchors and a fixture without it
        # tests a string nobody ever picks from.
        ID_A = "_2dee24f8-3b49-48af-b735-c6377509eaac"
        ID_B = "_4f5d21e1-4ccc-41f1-b35b-fb2547bd8493"

        def harvest(subdir, *files):
            d = os.path.join(tmp, subdir)
            os.makedirs(d)
            for i, n in enumerate(files):
                with open(os.path.join(d, n + ".fbx"), "wb") as fh:
                    fh.write(b"DIR-%02d" % i)      # distinct, or the dup check bites
            return catalogue(d)

        back = harvest("dir_back", "Walk Backward" + ID_A)
        hit, depth, _g = pick(back, [r"\bwalk(ing)? backward"], {}, {},
                              slot="back_away")
        if hit is None:
            failures.append("the direction screen emptied `back_away`, whose "
                            "whole job is walking backwards")
        elif depth != 0:
            failures.append("`back_away` took its backwards clip only as a "
                            "substitute")

        # ACCEPTING: a genuine forward start is still picked, with the
        # backwards sibling sitting beside it exactly as in the real harvest.
        both = harvest("dir_both", "Start Walking" + ID_A,
                       "Start Walking Backwards" + ID_B)
        hit, depth, _g = pick(both, [r"^start walking\b"], {}, {},
                              slot="walk_start")
        if hit is None or not hit[1].startswith("Start Walking_"):
            failures.append("a genuine forward start was not picked when one "
                            "was there: %r" % (hit and hit[1]))

        # REJECTING, WITH NO WAY OUT — and this is the case that shipped. The
        # backwards clip is the ONLY candidate, it passes every reading of the
        # file (hips 144..150cm, travel 0.94m), and the slot must come back
        # MISSING rather than send the whole town off backwards. An empty slot
        # falls back to the locomotion tree; a wrong one does not.
        only = harvest("dir_only", "Start Walking Backwards" + ID_B)
        with open(os.devnull, "w") as null:
            with contextlib.redirect_stdout(null):
                hit, _d, _g = pick(only, [r"^start walking\b",
                                          r"\bstart walking\b"], {}, {},
                                   slot="walk_start")
        if hit is not None:
            failures.append("the picker took %r for `walk_start` — every man "
                            "in the city sets off backwards" % hit[1])

        # AND THE SCREEN'S OWN TABLE, BOTH WAYS, over the slots it governs and
        # the two it deliberately does not.
        for slot, name, want_ok in (("walk", "Walking" + ID_A, True),
                                    ("walk", "Walking Backwards" + ID_A, False),
                                    ("run", "Running Backward" + ID_B, False),
                                    ("turn_right", "Backward Right Turn" + ID_A,
                                     False),
                                    ("back_away", "Walk Backward" + ID_A, True),
                                    ("stagger", "Stumble Backwards" + ID_A, True),
                                    ("collapse", "Dying Backwards" + ID_A, True)):
            got, _why = direction_ok(slot, flatten(name))
            if got != want_ok:
                failures.append("direction_ok(%s, %r) is %s, wanted %s"
                                % (slot, name, got, want_ok))

        # AND `turn_ok`'S TABLE, ACCEPTING FIRST. The rejecting half is easy
        # here and the accepting half is the one that matters: the first
        # version of this screen was about COSTUMES, and it refused `idle` =
        # `Mutant Breathing Idle` — the clip every person in Meridian plays
        # while standing still. It was withdrawn for that and the axis moved
        # to the motion; the idle is in the table below so the withdrawal
        # cannot be quietly undone.
        for slot, name, want_ok in (
                ("idle", "Mutant Breathing Idle" + ID_A, True),
                ("walk", "Walking" + ID_A, True),
                ("walk_start", "Start Walking" + ID_A, True),
                ("walk_start", "Catwalk Walk Start Turn 180 Left" + ID_A, False),
                ("walk_stop", "Catwalk Walk Stop Twist L" + ID_A, False),
                ("turn_right", "Right Turn 90" + ID_A, True)):
            got, _why = turn_ok(slot, flatten(name))
            if got != want_ok:
                failures.append("turn_ok(%s, %r) is %s, wanted %s"
                                % (slot, name, got, want_ok))

        # THE SHIPPED CLIPS ARE THE ACCEPTING FIXTURE, and this asserts the
        # SIZE of the refusal rather than that there is none: a screen that
        # refuses nothing at all is not running, and one that refuses several
        # is the ratchet that emptied the idle. Exactly one, and it is the
        # sashay this screen was written for — until a re-pick empties that
        # slot, after which zero is the right answer and the assertion says so.
        # THE SELFTEST RUNS WITH NO `--out`, so it resolves the shipped tree
        # the same way `CATALOGUE` does rather than borrowing main()'s local.
        chars = os.path.dirname(CATALOGUE)
        on_disk = sorted(glob.glob(os.path.join(chars, "*", "*__*.fbx")))
        refused = []
        for f in on_disk:
            slot_s, _, stem_s = os.path.basename(f)[:-len(".fbx")].partition("__")
            if stem_s and not turn_ok(slot_s, flatten(stem_s))[0]:
                refused.append("%s=%s" % (slot_s, stem_s))
        if not on_disk:
            failures.append("no shipped clips — turn_ok's accepting fixture is "
                            "testing nothing")
        elif len(refused) > 1 or (refused and "walk_start" not in refused[0]):
            failures.append("turn_ok refuses %d of %d shipped clip(s), wanted "
                            "at most the walk_start sashay: %s"
                            % (len(refused), len(on_disk), ", ".join(refused)))

        # THE FIXTURES ARE IN THE COMMITTED CATALOGUE, WHICH A RE-PICK CANNOT
        # EMPTY. `known-bad/` exists because the rejecting half used to point
        # at the SHIPPED clips and died the moment the work was done; the
        # harvest LISTING is the same idea for a name — `Start Walking
        # Backwards` stays in it however the picks move, and so does the
        # forward name the accepting half needs.
        cat = []
        if os.path.isfile(CATALOGUE):
            with open(CATALOGUE, encoding="utf-8") as fh:
                cat = [flatten(l.strip()) for l in fh if l.strip()]
        good = [n for n in cat if direction_ok("walk_start", n)[0]
                and n.startswith("start walking")]
        bad_names = [n for n in cat if not direction_ok("walk_start", n)[0]]
        if not cat:
            failures.append("no committed catalogue — the direction screen has "
                            "nothing real to accept or refuse")
        else:
            if not good:
                failures.append("no catalogued name the direction screen "
                                "ACCEPTS for walk_start — the accepting half "
                                "is testing nothing")
            if not bad_names:
                failures.append("no catalogued name the direction screen "
                                "REFUSES for walk_start — the rejecting half "
                                "is testing nothing")
            print("  direction screen: %d forward-only slot(s); of %d "
                  "catalogued name(s), %d refused for walk_start, %d accepted "
                  "as a plain forward start"
                  % (len(FORWARD_ONLY), len(cat), len(bad_names), len(good)))

        # THE LIVE SURVEY — PRINTED, NOT GATED. Every clip we actually ship,
        # read under its own slot. It is not a failure here because the fault
        # it names can only be fixed by a re-pick on a machine this container
        # never sees, and a gate nobody can commit past is the ratchet again.
        # It is PRINTED because a zero needs a denominator and because the
        # outstanding fault should say its own name every run.
        shipped_names, refused_names = 0, []
        for slot, entry in sorted(_picks().items()):
            found = entry.get("found")
            if not found:
                continue
            shipped_names += 1
            ok, why = direction_ok(slot, flatten(found))
            if not ok:
                refused_names.append((slot, found.split("_2dee")[0]
                                      .split("_4f5d")[0], why))
        if shipped_names:
            print("  shipped names: %d read, %d accepted, %d refused by the "
                  "direction screen"
                  % (shipped_names, shipped_names - len(refused_names),
                     len(refused_names)))
            for slot, name, _why in refused_names:
                print("      REVERSED CLIP IN A FORWARD SLOT: %-12s <- %s "
                      "(fix is a re-pick, not an edit here)" % (slot, name))
        else:
            print("  shipped names: nothing measured — no _picks.json to read")

        # SET-ASIDE READS THE NAME TOO, BOTH WAYS. This is the twin site: the
        # backwards clip passes every reading of the FILE, so without the name
        # check here a re-pick would report `walk_start` MISSING and leave the
        # backwards clip sitting in the build being loaded.
        keeper = one("back_away")
        if keeper is None:
            failures.append("set-aside's direction case was not tested — need "
                            "the shipped `back_away` clip")
        else:
            dpen = os.path.join(tmp, "dirpen")
            os.makedirs(os.path.join(dpen, "B"))
            # ACCEPTING: a backwards clip in the slot that WANTS one stays.
            stay = os.path.join(dpen, "B",
                                "back_away__Walk Backward" + ID_A + ".fbx")
            # REJECTING: the same bytes under a forward slot's name go. Same
            # bytes on purpose — the NAME is the whole evidence, and pinning
            # this to the currently-shipped bad file would retire the test the
            # day the re-pick lands.
            go = os.path.join(dpen, "B",
                              "walk_start__Start Walking Backwards"
                              + ID_B + ".fbx")
            shutil.copy2(keeper, stay)
            shutil.copy2(keeper, go)
            with open(os.devnull, "w") as null:
                with contextlib.redirect_stdout(null):
                    stayed = set_aside(dpen, "back_away")
                    went = set_aside(dpen, "walk_start")
            if stayed or not os.path.isfile(stay):
                failures.append("set-aside moved `back_away`'s backwards clip "
                                "— that empties the slot that wants one")
            if len(went) != 1 or os.path.isfile(go):
                failures.append("set-aside left a reversed clip in a forward "
                                "slot — the game would go on loading it")
            if not os.path.isfile(go + ".rejected"):
                failures.append("the reversed clip was destroyed rather than "
                                "set aside")

        # THE FROZEN PREFERENCE, BOTH WAYS, and the SECOND case is the one that
        # matters: a refusal here empties `lean`, which the street plays and
        # for which the catalogue offers nothing else.
        froz, clean = one("lean"), one("run")
        if froz is None or clean is None:
            failures.append("the frozen preference was not tested — need the "
                            "shipped `lean` and `run` clips")
        else:
            fd = os.path.join(tmp, "froz")
            os.makedirs(fd)
            # The frozen one gets the SHORTER name, so preferring the clean one
            # has to beat the shortest-name tiebreak rather than ride on it.
            shutil.copy2(froz, os.path.join(fd, "Zed.fbx"))
            shutil.copy2(clean, os.path.join(fd, "Zed Longer Name.fbx"))
            with open(os.devnull, "w") as null:
                with contextlib.redirect_stdout(null):
                    hit, _d, _g = pick(catalogue(fd), [r"^zed\b"], {}, {},
                                       slot="hands_up")
            if hit is None:
                failures.append("the frozen preference refused a slot outright "
                                "when a clean candidate existed")
            elif hit[1] != "Zed Longer Name":
                failures.append("the frozen preference took %r over the clean "
                                "candidate" % hit[1])

            # AND TAKEN WHEN IT IS THE ONLY THING THERE.
            od = os.path.join(tmp, "onlyfroz")
            os.makedirs(od)
            shutil.copy2(froz, os.path.join(od, "Zed.fbx"))
            with open(os.devnull, "w") as null:
                with contextlib.redirect_stdout(null):
                    hit, _d, _g = pick(catalogue(od), [r"^zed\b"], {}, {},
                                       slot="hands_up")
            if hit is None:
                failures.append("a frozen clip with no alternative was refused "
                                "— that empties `lean`, which the street plays")

        # SET-ASIDE, BOTH WAYS. It moves a file, so the case it must NOT act on
        # is the expensive one: a slot the patterns stopped naming may still
        # hold a good clip, and moving that is the ratchet rule 5 forbids.
        good = one("run")
        bad = os.path.join(bad_dir, KNOWN_BAD[0][0])
        if good is None or not os.path.isfile(bad):
            failures.append("set-aside was not tested — need a shipped `run` "
                            "clip and known-bad/%s" % KNOWN_BAD[0][0])
        else:
            pen = os.path.join(tmp, "pen")
            os.makedirs(os.path.join(pen, "A"))
            keep = os.path.join(pen, "A", "run__" + os.path.basename(good))
            drop = os.path.join(pen, "A", "walk__Walking.fbx")
            shutil.copy2(good, keep)
            shutil.copy2(bad, drop)

            # ACCEPTING (i.e. leaving alone): the screen passes it, so it stays.
            with open(os.devnull, "w") as null:
                with contextlib.redirect_stdout(null):
                    kept_moved = set_aside(pen, "run")
                    bad_moved = set_aside(pen, "walk")
            if kept_moved:
                failures.append("set-aside moved the shipped run clip, which "
                                "the screen passes — that is the ratchet")
            if not os.path.isfile(keep):
                failures.append("set-aside removed a clip the screen passes")

            # REJECTING: the screen refuses it, so it leaves the build.
            if len(bad_moved) != 1:
                failures.append("set-aside left a refused clip in the slot — "
                                "the game would go on loading it")
            if os.path.isfile(drop):
                failures.append("the refused clip is still a .fbx, so Unity "
                                "would still import it")
            if not os.path.isfile(drop + ".rejected"):
                failures.append("the refused clip was destroyed rather than "
                                "set aside")

            # AND THE SECOND RUN, which is the one that would break. The
            # `.rejected` target now exists, and `os.rename` onto an existing
            # path raises FileExistsError on Windows — where this actually
            # runs. A tool that works once and throws the next time is the
            # accepting case going unrun in its most expensive form.
            shutil.copy2(bad, drop)
            try:
                with open(os.devnull, "w") as null:
                    with contextlib.redirect_stdout(null):
                        again = set_aside(pen, "walk")
                if len(again) != 1 or os.path.isfile(drop):
                    failures.append("the second set-aside for a slot did not "
                                    "move the clip")
            except OSError as e:
                failures.append("the second set-aside for a slot raised %s — "
                                "it would fail on Jafar's machine, not here"
                                % e.__class__.__name__)

        # AND AN UNREADABLE FILE IS NOT A FAULT (rule 3b): a reader that
        # cannot open something has not found anything.
        ok, _why = posture_ok("walk", os.path.join(tmp, "not-an-fbx.txt"))
        if not ok:
            failures.append("an unreadable file was treated as a bad posture")

        # And the check must not fire on distinct files, or it would empty
        # the harvest one slot at a time.
        if len(set(cache.values())) < 3:
            failures.append("three distinct files did not hash to three values")

    # TWO WAYS OF WRITING A PATTERN THAT CAN NEVER MATCH, and both are
    # mechanical — no name in a Mixamo catalogue can satisfy either, so there
    # is no false positive to weigh.
    #
    # A `$` ANCHOR: the harvester appends the character id, so `^walking$` can
    # never see the end of "walking x bot". Fourteen slots went in one
    # afternoon.
    #
    # A DOUBLED BACKSLASH: `r"^sitting\\b"` is backslash-then-b, which asks for
    # a literal backslash in an animation name. Ten patterns across six slots,
    # all mine, all made while replacing the `$` anchors above with `\b` —
    # the fix for one impossible form written in another.
    for slot, _tier, patterns in WANTS:
        for pat in patterns:
            if pat.rstrip().endswith("$"):
                failures.append("%s: pattern %r ends in $ — the harvester "
                                "appends the character id, so it cannot match"
                                % (slot, pat))
            if "\\\\" in pat:
                failures.append("%s: pattern %r has a doubled backslash, so it "
                                "asks for a literal one in a clip name"
                                % (slot, pat))

    # EVERY SLOT MUST MATCH A REAL NAME, tried against the names the last
    # harvest actually produced.
    #
    # THIS USED TO CLAIM IT CAUGHT "ALL OF THEM, INCLUDING THE ONES NOBODY HAS
    # THOUGHT OF", and it was wrong the day it was written. It asks whether a
    # SLOT matched, and a slot is satisfied by any one of its patterns — so a
    # dead pattern sitting beside a live one is invisible to it. That is how
    # ten doubled backslashes shipped: `sit_drink` reported `none of 3 patterns
    # matched` while only two of the three could ever have matched anything,
    # and `block_hold` was down to one live pattern out of five. The widening
    # written to fill those exact holes was inert for the exact slots it was
    # for.
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

        # AND THE SAME QUESTION ONE LEVEL DOWN, REPORTED RATHER THAN FAILED.
        # A pattern matching nothing is not automatically a bug — eight of them
        # are honest alternates this harvest happens not to carry, like
        # `\bsurrender\b` for `hands_up`. It is only a bug when the pattern is
        # impossible, which the two checks above already catch. So this prints
        # the count and the names: a silently-discarded alternative stops being
        # indistinguishable from one that was tried and lost.
        dead = dead_patterns()
        if dead is not None:
            live = sum(len(p) for _s, _t, p in WANTS) - len(dead)
            print("  patterns: %d of %d match at least one catalogued name; "
                  "%d match none" % (live, live + len(dead), len(dead)))
            for slot, _i, pat in dead:
                print("      no name for %-12s %r" % (slot, pat))

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
    copied = missing = substituted = stale = 0
    # {content hash: the slot that claimed it}, so a collision can name the
    # other slot rather than just refusing.
    taken, hash_cache = {}, {}
    for slot, tier, patterns in WANTS:
        if tier not in args.tiers:
            continue
        hit, depth, digest = pick(items, patterns, taken, hash_cache, slot=slot)
        if hit is None:
            print(f"  MISSING  [{tier}] {slot:14s} — none of {len(patterns)} patterns matched")
            aside = set_aside(out, slot)
            report[slot] = {"tier": tier, "found": None,
                            "tried": patterns,
                            "setAside": [n for n, _why in aside]}
            missing += 1
            stale += len(aside)
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
    print(f"copied {copied}, substituted {substituted}, missing {missing}, "
          f"set aside {stale}")
    print(f"picks -> {out}")
    print()
    print("Commit and push BOTH the fbx files and _catalogue.txt / _picks.json.")
    print("The catalogue is the part that stops me guessing at clip names.")
    if missing:
        print()
        print("Missing slots are listed in _picks.json. Do not go hunting for")
        print("them by hand — send the catalogue and I will pick the real names.")
    if stale:
        # SAY WHAT A SET-ASIDE MEANS FOR THE GAME, not just that it happened.
        # The line above already says a slot is missing, and for eight slots on
        # 21 August that read as "nothing changed" while the game went on
        # loading a refused clip. An empty slot and a wrongly-filled one need
        # different next actions, so they have to look different here.
        print()
        print(f"{stale} clip(s) renamed to .rejected: a slot found nothing and")
        print("the clip already in it fails the posture/travel screen, so it")
        print("was serving the wrong motion. Those slots are now EMPTY rather")
        print("than wrong. Commit the renames along with everything else.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
