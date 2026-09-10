#!/usr/bin/env python3
"""PUT THE SHARED D1b SCENE WHERE THE UNITY PLAYER LOOKS FOR IT.

    python3 tools/stage-vignette-scene.py            # stage it
    python3 tools/stage-vignette-scene.py --selftest # check without staging

ONE SOURCE, STAGED, NOT COMMITTED TWICE. `game-design/decision-D1b-rescope.md`
makes one shared JSON the admissibility rule of the whole engine comparison:
every object in each engine arrives via its generator from THAT file, and a
hand-edited scene disqualifies the still. Two copies of the scene in git would
be two scenes the moment somebody edits the near one, and both stills would
still look fine. So `production/specs/vignette-scene.json` is the source and
this puts it where Unity will carry it into a player build. Same shape, and
the same reason, as tools/stage-voice-assets.py.

IT COUNTS WHAT IT MOVED AND CHECKS THE FILE PARSES. A staging step that
silently copies nothing produces a run that reports `nothing measured`, which
is correct but arrives a round trip later than it needs to.
"""
import argparse
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "production" / "specs" / "vignette-scene.json"
DEST = ROOT / "ledger" / "Assets" / "StreamingAssets" / "Vignette" / "scene.json"

# The keys StreetVignette.Read will throw on if they are absent. Checked here
# so a malformed scene fails at staging, in a log anybody can read, rather
# than inside a headless player whose only channel is the verdict file.
REQUIRED = ["street", "blocks", "shopfront", "facade", "roofline", "lighting",
            "furniture", "scatter", "surface_tiling", "cameras", "conditions", "shots"]

# THE FOUR JUDGED PAIRS, BY ID, AND WHY IT IS PRESENCE AND NOT A TOTAL.
# Two cameras by two conditions IS the four pairs the re-scope ruling judges
# on, and production/specs/vignette-bill-of-materials.md says so in as many
# words; four camera positions by two conditions would be eight pairs and a
# different bar. The bound this replaced was `len(shots) != 4`, which lived
# inside check() and so refused on the STAGING path too: the scene grew to 25
# shots on 2026-09-09 and the next Windows dispatch would have died at
# "Stage the D1b vignette scene", a build-killing step with no
# continue-on-error. Presence by id asserts MORE than that count did, not
# less: a count of four is satisfied by four arbitrary rows, and by one pair
# duplicated with another missing. The total is printed, never asserted,
# because probe rows are added and removed by ruling and a staging step is
# not where that argument belongs.
# Amendment 4 of game-design/decision-2026-09-09-ruling-the-grid-batch-review.md,
# queue 231 first half.
JUDGED = ["vign_camA_day", "vign_camA_night", "vign_camB_day", "vign_camB_night"]


def check(src):
    if not src.exists():
        return None, "no scene at %s" % src
    try:
        scene = json.loads(src.read_text())
    except Exception as e:  # noqa: BLE001 - the message is the whole point
        return None, "scene does not parse: %s" % e
    missing = [k for k in REQUIRED if k not in scene]
    if missing:
        return None, "scene is missing %d of %d required keys: %s" % (
            len(missing), len(REQUIRED), ",".join(missing))
    shots = scene.get("shots", [])
    ids = [s.get("id", "") for s in shots if isinstance(s, dict)]
    absent = [j for j in JUDGED if j not in ids]
    if absent:
        return None, "scene is missing %d of %d judged pair ids (%s) out of %d shots " \
                     "present; the four judged ids are two cameras by two conditions, " \
                     "which is what the re-scope ruling judges on" % (
                         len(absent), len(JUDGED), ",".join(absent), len(shots))
    return scene, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    scene, why = check(SRC)
    if why:
        print("stage-vignette-scene: FAILED - %s" % why)
        return 1

    if args.selftest:
        # ACCEPTING CASE FIRST, and it is the live file: the scene the
        # comparison will actually be shot from is the fixture, so doing the
        # work this tool prompts can never break the tool. THE TOTAL IS
        # PRINTED AND NOT ASSERTED, so a reader sees the shot list growing
        # without the staging step refusing on the growth.
        print("stage-vignette-scene --selftest: the live scene passes "
              "(%d required keys, %d of %d judged pair ids present, %d shots, "
              "%d blocks, %d furniture)"
              % (len(REQUIRED), len(JUDGED), len(JUDGED), len(scene["shots"]),
                 len(scene["blocks"]), len(scene["furniture"])))
        # AND THE REJECTING CASES, synthetic, so a real edit cannot make them
        # pass. TWO OF THEM, BECAUSE THEY ARE DIFFERENT BRANCHES: an empty
        # scene returns at the required-keys check and never reaches the shot
        # list, which is why the shot bound that killed the build had never
        # been reached by a test. The second fixture carries every required
        # key so it gets there.
        bad = pathlib.Path(__file__).parent / ".vignette-selftest-reject.json"
        short = pathlib.Path(__file__).parent / ".vignette-selftest-reject-judged.json"
        missing_id = JUDGED[-1]
        fixture = dict((k, {}) for k in REQUIRED)
        fixture["shots"] = [{"id": j, "camera": "cam_A", "condition": "overcast_day"}
                            for j in JUDGED if j != missing_id]
        bad.write_text('{"street":{}}')
        short.write_text(json.dumps(fixture))
        try:
            _, why2 = check(bad)
            if why2 is None:
                print("stage-vignette-scene --selftest: FAILED THE CASE IT MUST "
                      "REJECT - a scene with nothing in it was accepted")
                return 2
            print("stage-vignette-scene --selftest: rejects an empty scene (%s)" % why2)
            # THE BRANCH THE BUILD DIED ON, NOW REACHED BY A TEST: twelve
            # required keys, three of the four judged ids, refused by name.
            _, why3 = check(short)
            if why3 is None:
                print("stage-vignette-scene --selftest: FAILED THE CASE IT MUST "
                      "REJECT - a scene missing the judged pair id %s was accepted"
                      % missing_id)
                return 3
            if missing_id not in why3:
                print("stage-vignette-scene --selftest: FAILED - the refusal does "
                      "not name the missing judged id %s (%s)" % (missing_id, why3))
                return 4
            print("stage-vignette-scene --selftest: rejects a scene with 3 of 4 "
                  "judged pair ids and names the missing one (%s)" % why3)
        finally:
            bad.unlink(missing_ok=True)
            short.unlink(missing_ok=True)
        return 0

    DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC, DEST)
    print("stage-vignette-scene: staged 1 file, %d bytes, %d shots -> %s"
          % (DEST.stat().st_size, len(scene["shots"]),
             DEST.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
