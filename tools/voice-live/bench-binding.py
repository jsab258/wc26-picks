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
import time

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


def command(voice="rocco", short=False):
    """The argv this hands to dotnet — one place, so the selftest and the
    run cannot drift apart."""
    argv = ["dotnet", "run", "-c", "Release", "--project", str(BENCH), "--",
            "--models", str(OUT), "--conds", str(CONDS),
            "--tokenizer", str(TOKENIZER), "--voice", voice,
            "--text", LINE, "--positions", "10,100,200,400", "--window", "12"]
    if short:
        argv += ["--short", "1"]
    return argv


def missing_files():
    """Everything absent, by name — the denominator on every refusal."""
    gone = [f"game-out/{g}" for g in GRAPHS if not (OUT / g).exists()]
    if not TOKENIZER.exists():
        gone.append("tools/voice-live/tokenizer.json")
    if not (CONDS / "rocco.bin").exists():
        gone.append("game-design/voice-conds/rocco.bin")
    return gone


def sdk_missing(which=None, probe=None):
    """Why there is no usable .NET SDK, or None when there is one.

    `which("dotnet")` IS NOT THE CHECK, and the first run on the PC proved
    it: the bare dotnet HOST ships with all sorts of applications, so the
    executable was on PATH, my guard passed, and `dotnet run` answered with
    Microsoft's page of resolution advice instead of this file's one-line
    install. The question is whether an SDK is INSTALLED, and the host
    itself answers it: `--list-sdks`, empty meaning no.
    """
    which = which or shutil.which
    if which("dotnet") is None:
        return "no dotnet on PATH at all"

    def real_probe():
        p = subprocess.run(["dotnet", "--list-sdks"], capture_output=True,
                           text=True, timeout=60)
        return p.returncode, p.stdout
    try:
        rc, out = (probe or real_probe)()
    except Exception as e:
        return f"dotnet --list-sdks died: {type(e).__name__}"
    if rc != 0 or not out.strip():
        return "dotnet is on PATH but it is the bare host — no SDK installed"
    return None


# How long the job waits for the SDK to be installed before giving up. A
# refusal CONSUMES the request id — the watcher records every finished run —
# so "refuse and ask again" costs a round trip through the repository per
# attempt, and the first two attempts did exactly that. Waiting turns the
# install into the only manual step: winget drops the SDK into the dotnet
# root that is already on PATH, so a fresh `--list-sdks` subprocess sees it
# with no restart, and the job carries on by itself. Thirty minutes against
# the watcher's 3600s step timeout leaves the bench half an hour to run.
WAIT_SECONDS = 1800


def main(short=False):
    why = sdk_missing()
    if why:
        print(f"bench-binding: no .NET SDK yet ({why}).")
        print("  One-time install, and this job then continues BY ITSELF:")
        print("      winget install Microsoft.DotNet.SDK.8")
        print(f"  waiting up to {WAIT_SECONDS // 60} minutes for it...")
        sys.stdout.flush()
        t0 = time.time()
        while time.time() - t0 < WAIT_SECONDS:
            time.sleep(15)
            why = sdk_missing()
            if why is None:
                print(f"  the SDK appeared after {int(time.time() - t0)}s "
                      "— carrying on.")
                break
        if why:
            print("bench-binding: no SDK arrived within the wait — run the "
                  "install above and ask for this job again.")
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
    r = subprocess.run(command(short=short), cwd=str(ROOT))
    # AND CARRY THE WAV BACK. The bench now speaks a whole line through the
    # game's own `SpeechLoop.Run` and writes it beside itself; a sound
    # nobody can hear proves as little as the numbers did. Copied to the
    # published folder rather than left in a working directory, because the
    # publisher moves NAMED files and a result it cannot see did not happen.
    spoke = ROOT / "bench-spoke.wav"
    if spoke.exists():
        dest = ROOT / "game-design" / "voice-live" / "bench-spoke.wav"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(spoke, dest)
        print(f"  the game's own code spoke: {dest.name} "
              f"({spoke.stat().st_size // 1024} KB)")
    else:
        print("  no bench-spoke.wav — the C# path did not produce audio")
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
    # BOTH SHAPES, because a flag that is only ever built one way is a flag
    # nobody has run. The short set has to reach the bench as an argument
    # the bench understands, and `--short 1` is that argument.
    short_cmd = command(short=True)
    check("--short" in short_cmd and short_cmd[short_cmd.index("--short") + 1] == "1",
          "the short-line set reaches the bench as a flag it parses")
    check("--short" not in cmd,
          "and the ordinary run does not carry it")
    # AND THE ENTRY POINT ACCEPTS WHAT THE WATCHER SENDS. This is the check
    # that was missing when `short-lines` exited 2 in zero seconds.
    try:
        parsed = parser().parse_args(["--short"])
        check(parsed.short is True,
              "THE SCRIPT ITSELF ACCEPTS --short, which is what the watcher "
              "passes and what argparse rejected")
    except SystemExit:
        check(False, "THE SCRIPT ITSELF ACCEPTS --short",
              "argparse exited instead of parsing it")
    check(parser().parse_args([]).short is False,
          "and defaults to the ordinary set when nothing is passed")
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

    # THE SDK CHECK, BOTH FATES AND THE ONE THAT BIT. The first PC run had
    # dotnet on PATH — the bare host, no SDK — and a `which`-based guard
    # waved it through to Microsoft's error page. Planted probes cover the
    # exact transcript that came back.
    check(sdk_missing(which=lambda n: None) is not None,
          "no dotnet at all is refused")
    check(sdk_missing(which=lambda n: "dotnet",
                      probe=lambda: (0, "")) is not None,
          "and the bare host with an empty SDK list is refused too — the "
          "fate the first PC run proved")
    check(sdk_missing(which=lambda n: "dotnet",
                      probe=lambda: (1, "No .NET SDKs were found.")) is not None,
          "and a host that errors on --list-sdks is refused")
    check(sdk_missing(which=lambda n: "dotnet",
                      probe=lambda: (0, "8.0.404 [C:\\Program Files\\dotnet\\sdk]\n"))
          is None,
          "while an installed SDK passes — the accepting half")

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
    import atexit as _ax, shutil as _sh   # same leak as export-decode's: 19.8GB of these in one evening
    _ax.register(_sh.rmtree, tmp, True)
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


def parser():
    """The parser, NAMED so the selftest can run the real one.

    `--short` was read straight off `sys.argv` by a helper, which looked
    fine and could never work: `argparse` sees the flag first, does not
    recognise it, and exits 2 before any of this file's code runs. The job
    died in zero seconds on Jafar's machine.

    The selftest was no help because it checked the argv this file BUILDS
    for the bench and never that this file ACCEPTS the flag the watcher
    passes it — the half I wrote, not the entry point. Both are checked now,
    and the parser is here rather than inline so the check can use the real
    one instead of a copy that agrees with itself.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--short", action="store_true",
                    help="speak the five short lines instead of the usual set")
    return ap


if __name__ == "__main__":
    a = parser().parse_args()
    sys.exit(selftest() if a.selftest else main(short=a.short))
