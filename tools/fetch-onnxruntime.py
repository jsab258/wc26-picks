#!/usr/bin/env python3
"""FETCH THE SPEECH RUNTIME, AND PROVE IT LANDED.

    python3 tools/fetch-onnxruntime.py --dest ledger/Assets/Plugins/onnxruntime \
                                       --define ledger/Assets/csc.rsp

WHY THIS IS PYTHON RATHER THAN A FEW LINES OF POWERSHELL IN THE WORKFLOW.

The PowerShell version could only ever run inside a ~28-minute Windows build,
so it shipped unexercised, and it turned a missing download into something
worse than a missing feature: a build that compiled the backend against an
assembly that was not there, and therefore answered no question at all.

WHAT ACTUALLY HAPPENED, having read it properly the second time. The download
SUCCEEDED. `Microsoft.ML.OnnxRuntime.DirectML` contains three native
`onnxruntime.dll` builds and NO managed assembly — the C# side is a separate
package, and `Microsoft.AI.DirectML` is a third. The step copied the native
DLL, counted one file, saw one is more than zero, and wrote the define. Unity
then compiled `OnnxSpeech.cs` against a `Microsoft.ML` namespace that did not
exist, and the whole build died on CS0234.

So the fault is not the fetch. It is that the guard counted DLLs instead of
checking WHICH files arrived: "the download worked" and "the thing I need is
here" are different claims, and only the second one is worth gating on.

I ALSO MISDIAGNOSED IT ONCE, WHICH IS WORTH RECORDING. The first check said
the v2 URL 404s, and it does — to a HEAD request. It answers GET and redirects
to the CDN perfectly well, which is what the runner did. A one-second step
looked like an instant 404 and was in fact a fast download. Probing with the
wrong verb and believing the answer is rule 3 with the instrument being curl.

This file uses the flat container URL because it is the documented one and it
was downloaded end to end from here before being committed, rather than
because the other is broken.

IT VERIFIES WHAT LANDED RATHER THAN WHAT IT ASKED FOR. Each package names the
files it must contribute, and a missing one is a named failure. "The download
succeeded" and "the DLLs are on disk" are different claims, and the first one
is what a step reports when a URL quietly changes shape.
"""
import argparse
import io
import pathlib
import sys
import urllib.request
import zipfile

# PINNED, AND THE VERSIONS ARE NOT INDEPENDENT. The DirectML package's own
# nuspec requires exactly these two; taking a newer Managed against this
# native runtime is the kind of mismatch that loads fine and then throws on
# the first session.
PACKAGES = [
    ("Microsoft.ML.OnnxRuntime.DirectML", "1.20.1",
     ["runtimes/win-x64/native/onnxruntime.dll"]),
    ("Microsoft.ML.OnnxRuntime.Managed", "1.20.1",
     ["lib/netstandard2.0/Microsoft.ML.OnnxRuntime.dll"]),
    ("Microsoft.AI.DirectML", "1.15.2",
     ["bin/x64-win/DirectML.dll"]),
]


def url_for(pkg, ver):
    low = pkg.lower()
    return (f"https://api.nuget.org/v3-flatcontainer/{low}/{ver}/"
            f"{low}.{ver}.nupkg")


def fetch(pkg, ver, wanted, dest, say):
    """Download one package and copy out the files it owes. Returns names."""
    try:
        with urllib.request.urlopen(url_for(pkg, ver), timeout=180) as r:
            blob = r.read()
    except Exception as e:
        say(f"  {pkg} {ver}: DOWNLOAD FAILED — {type(e).__name__}: {e}")
        return None
    try:
        z = zipfile.ZipFile(io.BytesIO(blob))
    except Exception as e:
        say(f"  {pkg} {ver}: not a package — {type(e).__name__}: {e}")
        return None

    inside = {n.lower(): n for n in z.namelist()}
    got = []
    for want in wanted:
        real = inside.get(want.lower())
        if real is None:
            # THE ONE THAT MATTERS. A package whose layout moved downloads
            # perfectly and delivers nothing, which is indistinguishable from
            # success unless the arrival is checked rather than the request.
            say(f"  {pkg} {ver}: no '{want}' inside ({len(inside)} entries)")
            return None
        out = dest / pathlib.PurePosixPath(real).name
        out.write_bytes(z.read(real))
        got.append((out.name, out.stat().st_size))
    mb = sum(s for _, s in got) / (1024 * 1024)
    say(f"  {pkg} {ver}: {', '.join(n for n, _ in got)} ({mb:.1f} MB)")
    return [n for n, _ in got]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True)
    ap.add_argument("--managed-only", action="store_true",
                    help="just the C# assembly (210 KB) — all a COMPILE check "
                         "needs, against 32 MB for a runnable build")
    ap.add_argument("--define",
                    help="write '-define:LEDGER_ONNX' here, but ONLY if every "
                         "file arrived")
    a = ap.parse_args()

    lines = []

    def say(s):
        print(s)
        lines.append(s)

    dest = pathlib.Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    say(f"speech runtime -> {dest}")

    landed = []
    todo = [p for p in PACKAGES if not a.managed_only or "Managed" in p[0]]
    for pkg, ver, wanted in todo:
        got = fetch(pkg, ver, wanted, dest, say)
        if got is None:
            say("speech runtime: INCOMPLETE — the backend stays off and the "
                "build carries on without it.")
            return 1
        landed += got

    # THE DEFINE IS THE LAST THING, after every file is on disk. Written
    # earlier it would turn a partial download into a build that compiles
    # against an assembly that is not there — trading a missing feature for a
    # dead build, which is the trade this whole arrangement exists to avoid.
    if a.define:
        pathlib.Path(a.define).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(a.define).write_text("-define:LEDGER_ONNX\n", encoding="utf-8")
        say(f"speech runtime: {len(landed)} file(s), LEDGER_ONNX defined in "
            f"{a.define}")
    else:
        say(f"speech runtime: {len(landed)} file(s), no define asked for")
    return 0


if __name__ == "__main__":
    sys.exit(main())
