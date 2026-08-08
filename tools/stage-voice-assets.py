#!/usr/bin/env python3
"""PUT THE VOCABULARY AND THE VOICES WHERE THE GAME LOOKS FOR THEM.

    python3 tools/stage-voice-assets.py            # stage them
    python3 tools/stage-voice-assets.py --selftest # check without staging

THE BUILD SAID `speechVocab=none speechVoices=0`, and both were true. The
vocabulary lives in `tools/voice-live/` because that is where the probe wrote
it, and the nineteen voices live in `game-design/voice-conds/` because that is
where they were computed. `Audio` reads neither of those at runtime — it reads
`StreamingAssets/Voice/`, which nothing was filling.

So the director has been measuring every line in CHARACTERS rather than in
tokens for its cost estimate, and `VoiceFor` has been returning null for every
character in the game. Neither is visible as a failure; both read as a game
that simply prefers the bank.

STAGED RATHER THAN COMMITTED TWICE. Copying the files into `Assets/` would put
a second copy of all nineteen voices in git, and two copies of one thing drift
— which is the fault this project keeps finding, in its data instead of its
code for once. There is one source for each and this puts it where Unity will
carry it into the build.

IT COUNTS WHAT IT MOVED. A staging step that silently copies nothing produces
exactly the verdict that prompted this file, so the count is the output and a
missing source is a named failure rather than an empty directory.
"""
import argparse
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
VOCAB_SRC = ROOT / "tools" / "voice-live" / "tokenizer.json"
CONDS_SRC = ROOT / "game-design" / "voice-conds"
DEST = ROOT / "ledger" / "Assets" / "StreamingAssets" / "Voice"


def check_sources():
    """What is missing, by name. Empty list means everything is there."""
    missing = []
    if not VOCAB_SRC.exists():
        missing.append(f"no vocabulary at {VOCAB_SRC.relative_to(ROOT)}")
    else:
        try:
            json.loads(VOCAB_SRC.read_text(encoding="utf-8"))
        except Exception as e:
            missing.append(f"the vocabulary is not JSON: {type(e).__name__}")
    if not CONDS_SRC.is_dir():
        missing.append(f"no voices at {CONDS_SRC.relative_to(ROOT)}")
    elif not list(CONDS_SRC.glob("*.bin")):
        missing.append(f"{CONDS_SRC.relative_to(ROOT)} holds no .bin voices — "
                       f"run precompute-voices --repack")
    return missing


def stage(say=print):
    missing = check_sources()
    if missing:
        for m in missing:
            say(f"  MISSING: {m}")
        return 1
    (DEST / "conds").mkdir(parents=True, exist_ok=True)
    shutil.copy2(VOCAB_SRC, DEST / "tokenizer.json")
    n = 0
    for f in sorted(CONDS_SRC.glob("*.bin")):
        shutil.copy2(f, DEST / "conds" / f.name)
        n += 1
    kb = sum(p.stat().st_size for p in DEST.rglob("*") if p.is_file()) / 1024
    say(f"  staged: 1 vocabulary + {n} voice(s), {kb:.0f} KB, into "
        f"{DEST.relative_to(ROOT)}")
    return 0


def selftest():
    fails, ran = [], []

    def check(ok, what, got=""):
        print(("  ok    " if ok else "  FAIL  ") + what + (f"   [{got}]" if got else ""))
        ran.append(what)
        if not ok:
            fails.append(what)

    missing = check_sources()
    check(not missing, "both sources are present and the vocabulary parses",
          "; ".join(missing))

    # THE NAMES THE GAME ACTUALLY OPENS. `Audio` reads `Voice/tokenizer.json`
    # and `Voice/conds/*.bin`; staging to any other name is a copy nothing
    # reads, and would look exactly like this working.
    src = (ROOT / "ledger" / "Assets" / "Scripts" / "Game" / "Audio.cs").read_text(
        encoding="utf-8")
    check('"Voice", "tokenizer.json"' in src,
          "and Audio still opens Voice/tokenizer.json — the name staged here")
    check('"Voice", "conds"' in src,
          "and Voice/conds for the voices")

    n = len(list(CONDS_SRC.glob("*.bin"))) if CONDS_SRC.is_dir() else 0
    npz = len(list(CONDS_SRC.glob("*.npz"))) if CONDS_SRC.is_dir() else 0
    check(n > 0 and n == npz,
          f"every computed voice has a .bin the game can read — {n} of {npz}",
          f"{n} bin / {npz} npz")

    print(f"\nstage-voice-assets --selftest: "
          f"{'PASS' if not fails else str(len(fails)) + ' FAILED'} — {len(ran)} checks")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else stage()


if __name__ == "__main__":
    sys.exit(main())
