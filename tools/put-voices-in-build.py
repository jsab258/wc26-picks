#!/usr/bin/env python3
"""PUT THE THREE GRAPHS INTO A DOWNLOADED BUILD, SO CHARACTERS SPEAK.

    python3 tools/put-voices-in-build.py "C:/path/to/LEDGER"
    python3 tools/put-voices-in-build.py --selftest

THE LAST STEP NOBODY HAD WRITTEN, and the reason live speech has worked for
days without anybody being able to PLAY it.

Everything else already lands. CI builds the player, fetches the three
onnxruntime DLLs into it, and stages the vocabulary and all nineteen voices
into `StreamingAssets/Voice/`. What CI cannot do is carry the three graphs:
they are 4.5 GB, gitignored, and exist only on the machine that exported
them. So every build ever downloaded has reported `no t3-prefill.onnx` and
fallen back to the recorded bank — correctly, and invisibly, for days.

The gap is a FILE COPY, not a rebuild. `StreamingAssets` is a plain folder
inside the shipped player, so the graphs can be dropped into a build that
already exists. No Unity, no compile, no round trip: download the build,
run this, and the game speaks.

IT REFUSES RATHER THAN COPYING 1.3 GB INTO THE WRONG PLACE. A path that is
not a build, a build compiled without the speech runtime, a missing graph —
each is a named failure before anything is written, because the failure this
tool exists to end was itself a silent one.

AND IT READS BACK WHAT IT WROTE. A copy that reports success while landing a
truncated file is the same class of fault as the missing step it fixes, so
every destination is stat'd after the write and the sizes must match.
"""
import argparse
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
GRAPHS_SRC = ROOT / "tools" / "voice-live" / "game-out"
VOCAB_SRC = ROOT / "tools" / "voice-live" / "tokenizer.json"
CONDS_SRC = ROOT / "game-design" / "voice-conds"

# The three the backend opens by name. The fourth (`s3gen-chunk.onnx`) is
# deliberately absent: streaming is closed on these weights — see
# `export-decode.chunked_attention` — and a graph the game will never use is
# 500 MB of copying to no purpose.
GRAPHS = ["t3-prefill.onnx", "t3-step.onnx", "s3gen-decode.onnx"]

# What a real Windows build has in it, checked before anything is copied.
# `LEDGER_Data` is Unity's name for the payload folder beside the exe.
DATA_DIR = "LEDGER_Data"
# One of the DLLs the build job fetches. Without it `OnnxSpeech` was never
# compiled — `#if LEDGER_ONNX` — so the graphs would sit there unread and
# the game would report no backend for a completely different reason.
RUNTIME_DLL = "onnxruntime.dll"


def find_data(build):
    """The build's payload folder, or None with a reason."""
    if not build.exists():
        return None, f"there is nothing at {build}"
    if build.name == DATA_DIR:
        build = build.parent           # somebody passed the inner folder
    data = build / DATA_DIR
    if not data.is_dir():
        return None, (f"{build} does not look like a LEDGER build — no "
                      f"{DATA_DIR} folder in it")
    return data, None


def has_runtime(data):
    """Whether the speech runtime was compiled into this build.

    Searched rather than assumed at one path: Unity's plugin layout has
    moved between versions, and a wrong constant here would report "no
    speech runtime" about a build that has one — sending somebody to
    rebuild when all they needed was to copy.
    """
    for p in data.rglob(RUNTIME_DLL):
        return p
    return None


def run(build, say):
    data, why = find_data(build)
    if data is None:
        say(f"  {why}")
        return 1

    dll = has_runtime(data)
    if dll is None:
        say(f"  this build has no {RUNTIME_DLL} in it, so it was compiled "
            f"WITHOUT the speech runtime and no graph can help it.")
        say(f"  (the build job fetches the runtime; a build from a run where "
            f"that download failed is a build that can only use the bank.)")
        return 1
    say(f"  speech runtime present: {dll.relative_to(data)}")

    missing = [g for g in GRAPHS if not (GRAPHS_SRC / g).exists()]
    if missing:
        say(f"  no graphs to copy: {', '.join(missing)} not in {GRAPHS_SRC}")
        say(f"  run '5 EXPORT FOR THE GAME.bat' first — this machine is the "
            f"only one that has them.")
        return 1

    dest = data / "StreamingAssets" / "Voice"
    (dest / "models").mkdir(parents=True, exist_ok=True)

    moved = 0
    for g in GRAPHS:
        src = GRAPHS_SRC / g
        # External weight files travel with their graph. `s3gen-decode.onnx`
        # is over the 2 GB protobuf limit at some export settings and then
        # ships as `.onnx` plus `.onnx.data`; copying only the first leaves
        # a graph that loads and then dies looking for its weights.
        for part in sorted(GRAPHS_SRC.glob(g + "*")):
            target = dest / "models" / part.name
            shutil.copy2(part, target)
            # READ BACK. A copy that half-lands is the silent failure this
            # whole tool exists to end.
            if not target.exists() or target.stat().st_size != part.stat().st_size:
                say(f"  COPY FAILED: {part.name} did not land whole")
                return 1
            moved += 1
            say(f"  {part.name}  {part.stat().st_size / 1e6:.0f} MB")

    # The vocabulary and the voices SHOULD already be there — CI stages them
    # into the build — but a build from before that step, or one assembled by
    # hand, would be missing them and the failure reads as a mute game rather
    # than as a missing file. Cheap to check, cheaper than the round trip.
    extra = 0
    if VOCAB_SRC.exists() and not (dest / "tokenizer.json").exists():
        shutil.copy2(VOCAB_SRC, dest / "tokenizer.json")
        extra += 1
    if CONDS_SRC.is_dir():
        (dest / "conds").mkdir(parents=True, exist_ok=True)
        for npz in sorted(CONDS_SRC.glob("*.npz")):
            if not (dest / "conds" / npz.name).exists():
                shutil.copy2(npz, dest / "conds" / npz.name)
                extra += 1

    say(f"  {moved} graph file(s) copied"
        + (f", plus {extra} vocabulary/voice file(s) the build was missing"
           if extra else ""))
    say(f"  into {dest}")
    say("")
    say("  Start the game. Opening the graphs takes about 40 seconds and now "
        "happens in the background, so the game is playable immediately and "
        "characters gain their voices shortly after.")
    return 0


def selftest():
    import tempfile
    fails, ran = [], []

    def check(ok, what, got=""):
        print(("  ok    " if ok else "  FAIL  ") + what
              + (f"   [{got}]" if got else ""))
        ran.append(what)
        if not ok:
            fails.append(what)

    quiet = []
    tmp = pathlib.Path(tempfile.mkdtemp())
    import atexit
    atexit.register(shutil.rmtree, tmp, True)

    # ---- THE REJECTING CASES, each with its own reason ----
    check(run(tmp / "nothing-here", quiet.append) == 1,
          "a path with nothing at it is refused")

    plain = tmp / "just-a-folder"
    plain.mkdir()
    check(run(plain, quiet.append) == 1,
          "a folder that is not a build is refused")

    noruntime = tmp / "build-without-runtime"
    (noruntime / DATA_DIR).mkdir(parents=True)
    check(run(noruntime, quiet.append) == 1,
          "a build compiled without the speech runtime is refused, rather "
          "than being given 1.3 GB it cannot read")

    # ---- AND THE CASE IT MUST ACCEPT, which is the half that goes unrun ----
    #
    # Rule 5b: every guard above passes on its failure. This one is the
    # reason the tool exists, and it is built from fakes so it can run on a
    # machine with no graphs and no build — the two things this tool is for.
    build = tmp / "LEDGER"
    data = build / DATA_DIR
    (data / "Plugins" / "x86_64").mkdir(parents=True)
    (data / "Plugins" / "x86_64" / RUNTIME_DLL).write_bytes(b"not really a dll")

    fake_src = tmp / "graphs"
    fake_src.mkdir()
    for g in GRAPHS:
        (fake_src / g).write_bytes(b"x" * 2048)
    # One of them with external weights beside it, because that is the case
    # a partial copy would break silently.
    (fake_src / (GRAPHS[2] + ".data")).write_bytes(b"y" * 4096)

    global GRAPHS_SRC
    keep = GRAPHS_SRC
    GRAPHS_SRC = fake_src
    try:
        rc = run(build, quiet.append)
    finally:
        GRAPHS_SRC = keep

    check(rc == 0, "AND A REAL BUILD WITH REAL GRAPHS IS ACCEPTED",
          "; ".join(quiet[-3:])[:80])
    models = data / "StreamingAssets" / "Voice" / "models"
    check(all((models / g).exists() for g in GRAPHS),
          "and all three graphs land where the backend looks for them")
    check((models / (GRAPHS[2] + ".data")).exists(),
          "and a graph's external weights travel with it, which a "
          "name-by-name copy would have dropped")

    print(f"\nput-voices-in-build --selftest: "
          f"{'PASS' if not fails else str(len(fails)) + ' FAILED'} — "
          f"{len(ran)} checks")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("build", nargs="?", help="the unzipped LEDGER build folder")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.build:
        ap.error("give me the build folder, or --selftest")

    def say(s):
        print(s, flush=True)

    say("LEDGER — putting the voices into a build")
    return run(pathlib.Path(a.build), say)


if __name__ == "__main__":
    sys.exit(main())
