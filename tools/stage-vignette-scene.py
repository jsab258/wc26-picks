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
    if len(shots) != 4:
        return None, "expected 4 matched shots (two cameras by two conditions, " \
                     "which is what the re-scope ruling judges on), found %d" % len(shots)
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
        # work this tool prompts can never break the tool.
        print("stage-vignette-scene --selftest: the live scene passes "
              "(%d required keys, %d shots, %d blocks, %d furniture)"
              % (len(REQUIRED), len(scene["shots"]), len(scene["blocks"]),
                 len(scene["furniture"])))
        # AND THE REJECTING CASE, synthetic, so a real edit cannot make it pass.
        bad = pathlib.Path(__file__).parent / ".vignette-selftest-reject.json"
        bad.write_text('{"street":{}}')
        try:
            _, why2 = check(bad)
            if why2 is None:
                print("stage-vignette-scene --selftest: FAILED THE CASE IT MUST "
                      "REJECT - a scene with nothing in it was accepted")
                return 2
            print("stage-vignette-scene --selftest: rejects an empty scene (%s)" % why2)
        finally:
            bad.unlink(missing_ok=True)
        return 0

    DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC, DEST)
    print("stage-vignette-scene: staged 1 file, %d bytes, %d shots -> %s"
          % (DEST.stat().st_size, len(scene["shots"]),
             DEST.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
