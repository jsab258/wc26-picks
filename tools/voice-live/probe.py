#!/usr/bin/env python3
"""CAN THE CAST SPEAK LIVE, ON A PLAYER'S GPU, AT THE QUALITY OF THE BARKS?

    python3 tools/voice-live/probe.py --selftest   # free, runs anywhere
    python3 tools/voice-live/probe.py --backends   # what this machine can do
    python3 tools/voice-live/probe.py --run        # the real thing, needs a GPU

WHY. Barks are pre-rendered and finished. Conversation cannot be: the words
are new every time, so the only way a named character is ever HEARD is
synthesis at play time, on the player's machine.

Jafar set the bar: *"we need high quality, like the barks."* That single
sentence decides the shape of this probe, because it means the first question
is NOT "what small fast engine could we use" — it is **"can we keep the engine
we already chose by ear."** A cheaper engine is a fallback to be measured
against chatterbox, never a substitute assumed to be good enough.

THE CONSTRAINT THE FIRST BENCHMARK NEVER HAD. §1g-bis of the production plan:
this code runs on a stranger's machine, so it must be vendor-neutral (AMD,
NVIDIA, Intel), shippable inside a Unity build, and fast enough that a reply
does not arrive after the moment has passed. The original benchmark optimised
quality on one dev box and never asked any of that.

FOUR ROUTES, IN THE ORDER THEY PRESERVE QUALITY:

  A  chatterbox exported to ONNX, run on DirectML
     Quality identical by construction — it is the same weights. Ships as a
     DLL, callable from C#, no Python. If this works, everything else is
     moot. Highest risk: a Llama-derived backbone, a flow decoder and a
     watermarker, none of which export cleanly by default.

  B  chatterbox under torch-directml - RULED OUT 5 Aug, with an error.
     `torch-directml` pins torch==2.4.1 and `chatterbox-tts` requires 2.6.0.
     In one environment pip swaps one for the other and leaves binaries that
     cannot load. A version deadlock, not a capability gap. It cost nothing
     that mattered: this route was never shippable, and route A uses no torch
     at run time at all.

  C  a small ONNX-native engine with the cast voice BAKED IN at build time
     The insight worth testing: nothing needs to clone at RUNTIME. Rocco's
     voice never changes between players, so the cloning can happen once, on
     our machine, producing a small fixed-voice model per character. Runtime
     then does the easy job that exports cleanly and runs anywhere.
     Quality unknown and that is exactly what this probe is for.

  D  no live voice
     Conversation stays read. The honest fallback, and it must stay on the
     list — a probe with no failing outcome is a probe that will find a
     success.

WHAT THIS TOOL WILL NOT DO. It will not tell you an approach is good. It
renders ONE line per working route, puts them beside a real bark from the
shipped bank, and leaves the judgement to the person who set the bar. Every
quality decision in this project so far was made by Jafar's ears and the two
that were not — kokoro, piper — were both reversed.
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CLIPS = ROOT / "game-design" / "picked-clips"
BANK = ROOT / "ledger" / "Assets" / "StreamingAssets" / "Audio" / "Voice"
OUT = ROOT / "tools" / "voice-live" / "out"

# The line every route says, so the comparison is like for like. Long enough
# to hear prosody, short enough that a slow route still finishes, and it is a
# line Rocco would actually say rather than a pangram — the question is
# whether he sounds like himself, which a nonsense sentence cannot answer.
TEST_LINE = ("Seen the van again. Thursday, same as last Thursday. "
             "Anyway. You having one?")

# Rocco, because his reference clip is in the repo and his card gives him the
# most distinctive delivery of the four principals.
TEST_VOICE = "rocco"


def backends():
    """WHAT THIS MACHINE CAN ACTUALLY DO, reported rather than assumed.

    The plan carried "torch-directml does not carry models of this shape" as a
    bare sentence with no test, no error and no date beside it, while every
    other decision in that file cites what was run. This prints what is
    installed and what each thing says about itself, so the next claim has
    something under it."""
    found = {}

    def probe(name, fn):
        try:
            found[name] = fn()
        except Exception as e:
            found[name] = f"no — {type(e).__name__}: {str(e)[:70]}"

    def torch_info():
        import torch
        bits = [f"torch {torch.__version__}"]
        bits.append("cuda" if torch.cuda.is_available() else "no cuda")
        return ", ".join(bits)

    def directml():
        import torch_directml
        return f"torch-directml, {torch_directml.device_count()} device(s)"

    def onnxrt():
        import onnxruntime as ort
        eps = ort.get_available_providers()
        dml = "DmlExecutionProvider" in eps
        return (f"onnxruntime {ort.__version__}, DirectML "
                f"{'AVAILABLE' if dml else 'MISSING'} — {', '.join(eps)}")

    def chatterbox():
        import chatterbox
        return "installed"

    probe("torch", torch_info)
    probe("torch-directml", directml)
    probe("onnxruntime", onnxrt)
    probe("chatterbox", chatterbox)
    return found


def cmd_backends(args):
    print("  what this machine can run:\n")
    f = backends()
    for k in ("torch", "torch-directml", "onnxruntime", "chatterbox"):
        print(f"    {k:16} {f.get(k, 'not checked')}")
    print()
    # ROUTE READINESS, said plainly, because "onnxruntime is installed" and
    # "route A can be attempted" are different facts and only the second is
    # actionable.
    # ROUTE A NEEDS DIRECTML AND NOTHING ELSE, which the first version got
    # wrong by also demanding chatterbox. That turned a YES into "not ready"
    # and nearly buried the one positive result under two unrelated failures:
    # onnxruntime-directml has no torch dependency in either direction, and
    # torch is needed once on OUR machine to export, never at run time.
    ok_a = "DirectML AVAILABLE" in str(f.get("onnxruntime", ""))
    ok_b = "torch-directml," in str(f.get("torch-directml", "")) and \
           "installed" in str(f.get("chatterbox", ""))
    print(f"    route A (ONNX + DirectML)  "
          f"{'GPU CONFIRMED - the export is what remains' if ok_a else 'DirectML not available'}")
    print(f"    route B (torch-directml)   {'ready to attempt' if ok_b else 'not ready'}")
    print("    route C (baked small voice) needs a training run, not just an install")
    print("    route D (no live voice)     always available, and stays on the list")
    return 0


def reference_for(voice_id):
    """The clip that decides identity. Same one the bark bank was cloned from,
    so a live route is being compared against its own sibling rather than
    against a different recording of a different person."""
    hits = sorted(CLIPS.glob(voice_id + ".*"))
    return hits[0] if hits else None


def a_bark_by(voice_id):
    """One clip from the shipped bank, as the QUALITY FLOOR to beat.

    The comparison that matters is not "is this good" in the abstract. It is
    "does this sound like the street already sounds", and the only honest way
    to ask that is to put them next to each other."""
    if not BANK.exists():
        return None
    # Crowd voices carry the bank; the cast have none yet, which is the whole
    # reason this probe exists.
    for d in sorted(BANK.iterdir()):
        if d.is_dir():
            got = sorted(d.glob("*.wav"))
            if got:
                return got[0]
    return None


def page(rows, dest):
    """A listening page, because a table of milliseconds cannot answer the
    question that was asked. Standalone and offline — the voice-fetch page
    learned that lesson the hard way when a relative <audio src> needed a
    server and the phone it was opened on had none."""
    body = []
    for r in rows:
        body.append(
            f"<section><h2>{r['route']}</h2>"
            f"<p class=n>{r['note']}</p>"
            + (f"<audio controls src='{r['file']}'></audio>" if r.get("file")
               else "<p class=x>nothing rendered</p>")
            + (f"<p class=t>first audio after {r['seconds']:.2f}s</p>"
               if r.get("seconds") else "")
            + "</section>")
    dest.write_text(
        "<!doctype html><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        "<title>LEDGER — live voice probe</title><style>"
        "body{font:16px/1.5 system-ui;margin:0 auto;padding:1.5rem;max-width:44rem;"
        "background:#14140f;color:#e8e2d0}h1{font-size:1.3rem}h2{font-size:1rem;margin:0 0 .2rem}"
        "section{border-top:1px solid #3a3a30;padding:1.1rem 0}audio{width:100%;margin:.4rem 0}"
        ".n{color:#a09880;margin:.2rem 0 .5rem}.t{color:#7d8f6a;font-size:.85rem;margin:.2rem 0 0}"
        ".x{color:#b06a5a}</style>"
        f"<h1>Does the cast sound like the street?</h1>"
        f"<p class=n>Same line, every route that ran. The first player is a real "
        f"clip from the shipped bark bank — that is the bar.</p>"
        + "".join(body), encoding="utf-8")
    return dest


def cmd_run(args):
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []

    bark = a_bark_by(TEST_VOICE)
    if bark:
        shutil.copy2(bark, OUT / "0-the-bar.wav")
        rows.append({"route": "The bar — a clip from the shipped bark bank",
                     "note": "This is the quality every route below has to reach.",
                     "file": "0-the-bar.wav"})
    else:
        rows.append({"route": "The bar", "note":
                     "No bark bank on disk yet, so there is nothing to compare against. "
                     "Render it first.", "file": None})

    ref = reference_for(TEST_VOICE)
    if ref is None:
        print(f"probe: no reference clip for '{TEST_VOICE}' in {CLIPS}")
        return 1
    shutil.copy2(ref, OUT / ("1-reference" + ref.suffix))
    rows.append({"route": "The reference — the VCTK speaker Rocco is cloned from",
                 "note": "Identity comes from here, in every route.",
                 "file": "1-reference" + ref.suffix})

    f = backends()
    have_cb = "installed" in str(f.get("chatterbox", ""))

    # ROUTE B FIRST, DELIBERATELY, THOUGH IT IS SECOND IN THE DOCSTRING.
    # It is the cheapest thing that produces AUDIO at the right quality, so it
    # answers the speed question before anybody spends a day on an ONNX export
    # that might not be possible. A route that cannot ship can still kill or
    # confirm the idea.
    if have_cb and "torch-directml," in str(f.get("torch-directml", "")):
        rows.append(run_torch_dml())
    else:
        rows.append({"route": "B — chatterbox on torch-directml",
                     "note": f"Not attempted. {f.get('torch-directml')}", "file": None})

    rows.append({"route": "A — chatterbox exported to ONNX, on DirectML",
                 "note": "Not attempted yet: the export itself is the experiment and it "
                         "needs its own session. This probe exists to decide whether that "
                         "day is worth spending.", "file": None})
    rows.append({"route": "C — a small model with the voice baked in",
                 "note": "Needs a training run, not an install. Only worth doing if A and B "
                         "both fail, because it is the only route that risks the quality bar.",
                 "file": None})

    p = page(rows, OUT / "listen.html")
    print(f"\n  wrote {p}")
    print("  open it and listen. The question is not 'is it fast' — it is")
    print("  'does that sound like the street already sounds'.")
    return 0


def run_torch_dml():
    """Chatterbox on the DirectML device. Same weights, so same quality; the
    only question this answers is SPEED on a real gamer GPU."""
    try:
        import torch_directml
        from chatterbox.tts import ChatterboxTTS
        import torchaudio
        dev = torch_directml.device()
        t0 = time.time()
        import export_probe
        model = export_probe.load_model(dev)
        load = time.time() - t0
        t1 = time.time()
        wav = model.generate(TEST_LINE, audio_prompt_path=str(reference_for(TEST_VOICE)),
                             exaggeration=0.45)
        took = time.time() - t1
        torchaudio.save(str(OUT / "2-torch-directml.wav"), wav, model.sr,
                        encoding="PCM_S", bits_per_sample=16)
        secs = wav.shape[-1] / model.sr
        return {"route": "B — chatterbox on torch-directml (your GPU)",
                "note": f"Model loaded in {load:.1f}s, once. {secs:.1f}s of speech in "
                        f"{took:.2f}s — {took/max(secs,0.01):.2f}x real time. "
                        f"Under 1.0 means it can keep up with a conversation.",
                "file": "2-torch-directml.wav", "seconds": took}
    except Exception as e:
        return {"route": "B — chatterbox on torch-directml",
                "note": f"FAILED: {type(e).__name__}: {str(e)[:200]}. "
                        f"This is the error the plan asserted without ever printing.",
                "file": None}


def selftest():
    """Everything that does not need a GPU, because that is the half that can
    be wrong here — and today the one path that needed hardware was the one
    path that shipped unexecuted."""
    fails, ran = [], []

    def check(ok, what):
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}")
        ran.append(what)
        if not ok:
            fails.append(what)

    b = backends()
    check(set(b) == {"torch", "torch-directml", "onnxruntime", "chatterbox"},
          f"every backend is probed and reported ({len(b)})")
    check(all(isinstance(v, str) for v in b.values()),
          "a missing backend reports WHY rather than throwing")

    check(reference_for(TEST_VOICE) is not None,
          f"the reference clip for '{TEST_VOICE}' is on disk")
    check(len(TEST_LINE) > 40, "the test line is long enough to hear prosody")

    import tempfile
    tmp = Path(tempfile.mkdtemp())
    try:
        rows = [{"route": "x", "note": "y", "file": "a.wav", "seconds": 1.2},
                {"route": "z", "note": "w", "file": None}]
        p = page(rows, tmp / "listen.html")
        html = p.read_text(encoding="utf-8")
        check("<audio controls" in html, "a route with audio gets a player")
        check("nothing rendered" in html, "a route without audio says so rather than "
                                          "showing an empty player")
        check("viewport" in html, "the page has a viewport tag — the listening page "
                                  "shipped without one and was unusable on a phone")
        check("first audio after 1.20s" in html, "timings reach the page")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bark = a_bark_by(TEST_VOICE)
    check(bark is not None or not BANK.exists(),
          f"a bark is found to compare against, or the bank is honestly absent "
          f"({bark.name if bark else 'no bank yet'})")

    print(f"\nvoice-live --selftest: {'PASS' if not fails else str(len(fails)) + ' FAILED'} — "
          f"{len(ran)} checks, none of which need a GPU")
    return 0 if not fails else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backends", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.run:
        return cmd_run(args)
    return cmd_backends(args)


if __name__ == "__main__":
    sys.exit(main())
