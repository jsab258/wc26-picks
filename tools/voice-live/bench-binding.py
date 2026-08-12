#!/usr/bin/env python3
"""RUN THE RESIDENCY BENCH ON THE MACHINE WITH THE CARD.

    python3 tools/voice-live/bench-binding.py            # the PC, via the watcher
    python3 tools/voice-live/bench-binding.py --selftest  # needs nothing

`OnnxSpeech` grew a bound path: with DirectML present the KV cache stays in
device memory instead of crossing PCIe twice a step (measured: 31.8ms flat +
142us/position of pure round-trip). The python preview of that idea died in
the DML provider with an access violation — twice — and an access violation
cannot be caught from C# either, so the path must be RUN on the real card
before any Unity build leans on it. `ledger/SpeechBench` is that run: one
session, both paths, logits compared float-for-float, then steps timed in the
same position buckets as `probe-step-costs.py` so the histories line up.

THIS FILE IS ONLY THE DRIVER, and it exists because the bench needs three
things the watcher's other jobs never did:

  the .NET SDK      — checked FIRST, by name, because `dotnet run` missing
                      prints a shell error that reads like a repo fault.
                      If it is absent this says exactly what to install and
                      stops; that is a manual step for Jafar, named as one.
  the native DLLs   — onnxruntime.dll and DirectML.dll beside the exe.
                      `fetch-onnxruntime.py` (no flags) lands both plus the
                      managed assembly in `ledger/.onnx-cache`; the csproj
                      copies them out. Fetched here only when missing.
  the graphs        — the same `game-out` set every other job reads. Absent
                      graphs are named per file, the habit every sibling
                      tool has, because "it failed" and "you never exported"
                      want different next moves.
"""
import argparse
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "tools" / "voice-live" / "game-out"
CONDS = ROOT / "game-design" / "voice-conds"
TOKENIZER = ROOT / "tools" / "voice-live" / "tokenizer.json"
CACHE = ROOT / "ledger" / ".onnx-cache"
BENCH = ROOT / "ledger" / "SpeechBench"

GRAPHS = ["t3-prefill.onnx", "t3-step.onnx", "s3gen-decode.onnx"]
NATIVE = ["onnxruntime.dll", "DirectML.dll", "Microsoft.ML.OnnxRuntime.dll"]

# The nine-word line the fp16 sweep used (its line 2 — COUNTED, after
# "twelve-word" survived three files without anyone counting it), so every
# number this produces reads against the sweep's and the probe's.
LINE = "Seen the van again. Thursday, same as last Thursday."


def command(voice="rocco"):
    """The argv this hands to dotnet — one place, so the selftest and the
    run cannot drift apart."""
    return ["dotnet", "run", "-c", "Release", "--project", str(BENCH), "--",
            "--models", str(OUT), "--conds", str(CONDS),
            "--tokenizer", str(TOKENIZER), "--voice", voice,
            "--text", LINE, "--positions", "10,100,200,400", "--window", "12"]


def missing_files():
    """Everything absent, by name — the denominator on every refusal."""
    gone = [f"game-out/{g}" for g in GRAPHS if not (OUT / g).exists()]
    if not TOKENIZER.exists():
        gone.append("tools/voice-live/tokenizer.json")
    if not (CONDS / "rocco.bin").exists():
        gone.append("game-design/voice-conds/rocco.bin")
    return gone


def main():
    if shutil.which("dotnet") is None:
        print("bench-binding: NO .NET SDK on this machine — the bench is a")
        print("  C# console app so it can drive the game's real backend.")
        print("  One-time install:  winget install Microsoft.DotNet.SDK.8")
        print("  then run this job again.")
        return 1

    gone = missing_files()
    if gone:
        print("bench-binding: missing " + ", ".join(gone))
        print("  the graphs come from the export-graphs job; nothing here "
              "can make them")
        return 1

    if any(not (CACHE / n).exists() for n in NATIVE):
        print("bench-binding: fetching the onnxruntime DLLs (one-time)...")
        r = subprocess.run([sys.executable,
                            str(ROOT / "tools" / "fetch-onnxruntime.py"),
                            "--dest", str(CACHE)])
        if r.returncode != 0:
            return r.returncode

    print("bench-binding: building and running the bench "
          "(first build takes a minute)...")
    sys.stdout.flush()
    # STREAMED, NOT CAPTURED. The probe that captured its output and died on
    # a timeout published an hour of silence and lost the half it had done;
    # everything since streams so a dead run still shows where it stopped.
    r = subprocess.run(command())
    return r.returncode


def selftest():
    global OUT, CONDS, TOKENIZER
    fails, ran = [], []

    def check(ok, what, got=""):
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}" + ("" if ok else f" — {got}"))
        ran.append(what)
        if not ok:
            fails.append(what)

    cmd = command()
    check(cmd[0] == "dotnet" and "--project" in cmd,
          "the bench runs through dotnet with an explicit project",
          " ".join(cmd[:6]))
    check(str(BENCH) in cmd and (BENCH / "SpeechBench.csproj").exists(),
          "and the project it names exists in the repository",
          str(BENCH))
    check(cmd[cmd.index("--text") + 1] == LINE and len(LINE.split()) == 9,
          "the text is the sweep's nine-word van line, so the numbers read "
          "against the sweep's", f"{len(LINE.split())} words")
    check("10,100,200,400" in cmd,
          "and the positions are the python probe's buckets, so the "
          "histories line up")

    # THE REFUSALS NAME WHAT IS ABSENT. On this container the graphs are
    # genuinely absent, so the real function is its own rejecting fixture.
    gone = missing_files()
    check(any("t3-prefill" in g for g in gone) or (OUT / GRAPHS[0]).exists(),
          "a missing graph is named per file rather than summarised",
          ", ".join(gone) or "nothing missing")

    # And the accepting half of that check, from a planted set: every file
    # present means NO refusal, which is the case that usually goes unrun.
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp())
    keep = OUT, CONDS, TOKENIZER
    try:
        OUT = tmp / "game-out"
        CONDS = tmp / "conds"
        TOKENIZER = tmp / "tokenizer.json"
        OUT.mkdir()
        CONDS.mkdir()
        for g in GRAPHS:
            (OUT / g).write_bytes(b"x")
        (CONDS / "rocco.bin").write_bytes(b"x")
        TOKENIZER.write_text("{}", encoding="utf-8")
        check(missing_files() == [],
              "and a complete set raises no refusal at all",
              ", ".join(missing_files()))
    finally:
        OUT, CONDS, TOKENIZER = keep

    print(f"\nbench-binding --selftest: "
          f"{'PASS' if not fails else 'FAIL'} — {len(ran)} checks")
    return 0 if not fails else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else main())
