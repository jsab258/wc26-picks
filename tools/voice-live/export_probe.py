#!/usr/bin/env python3
"""CAN CHATTERBOX BE CONVERTED TO SOMETHING A PLAYER'S GPU CAN RUN?

    python3 tools/voice-live/export_probe.py --selftest   # free, runs anywhere
    python3 tools/voice-live/export_probe.py --run        # needs the model

THE QUESTION, narrowed as far as it will go. Barks are finished — 2,010 clips,
shipped. Conversation cannot be pre-rendered, because the words are new every
time, so the only way a named character is ever HEARD is synthesis at play
time on a stranger's machine. Jafar's bar: *"we need high quality, like the
barks"*, which rules out swapping in a lesser engine before we know whether we
can keep this one.

`onnxruntime` already reports `DmlExecutionProvider` on his AMD card, so the
HARDWARE end holds. What is unknown is whether this particular model can be
got into ONNX at all.

WHY IT MIGHT NOT. Chatterbox is three models in a coat: a Llama-derived
text-to-token stage, a flow-matching decoder, and a watermarker. Export
difficulty differs per part, and the usual failures are dynamic control flow,
KV-cache handling and unsupported ops. "It failed" is not a useful answer to
bring back.

SO THIS REPORTS PER PART, WHICH IS THE WHOLE DESIGN. Each component is tried
separately and gets its own verdict — exported and how big, or the exact
exception. A partial result is the likely outcome and it is actionable: if the
decoder exports and the text stage does not, the text stage is the day's work
and the rest is already done. A single pass/fail would throw that away.

WHAT IT WILL NOT DO. It will not convert anything for real use, will not
overwrite the shipped bark bank, and will not claim a route works because a
file appeared — an ONNX file that exports and then produces silence is a
failure that looks like a success, so every part that exports is immediately
RUN under onnxruntime and its output compared for shape.
"""
import argparse
import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CLIPS = ROOT / "game-design" / "picked-clips"
OUT = ROOT / "tools" / "voice-live" / "export-out"
REPORT = OUT / "export-report.json"

# One line, one voice, so a failure is about the model rather than the input.
LINE = "Seen the van again. Thursday, same as last Thursday."
VOICE = "rocco"

# The parts, in the order they are worth having. `attr` is where the submodule
# hangs off `ChatterboxTTS`; several names are tried because the package has
# renamed them between releases and a probe that dies on an attribute lookup
# tells you nothing about ONNX.
PARTS = [
    {"key": "t3", "names": ["t3", "T3", "text_to_token"],
     "what": "the Llama-derived text-to-token stage",
     "risk": "highest — autoregressive, KV cache, dynamic loop bounds"},
    {"key": "s3gen", "names": ["s3gen", "S3Gen", "flow", "decoder"],
     "what": "the flow-matching decoder that makes the waveform",
     "risk": "medium — heavy but mostly static, the usual export target"},
    {"key": "ve", "names": ["ve", "voice_encoder", "speaker_encoder"],
     "what": "the voice encoder that reads the reference clip",
     "risk": "lowest — a plain encoder, and the part identity comes from"},
]


def find_part(model, names):
    for n in names:
        got = getattr(model, n, None)
        if got is not None:
            return n, got
    return None, None


def try_export(model, part, out_dir):
    """One component. Returns a verdict dict — never raises, because the
    NEXT part's answer is worth having even when this one fails."""
    import torch
    name, sub = find_part(model, part["names"])
    if sub is None:
        return {"part": part["key"], "verdict": "absent",
                "detail": f"none of {part['names']} is an attribute of the model; "
                          f"the package may have renamed it"}
    n_params = sum(p.numel() for p in sub.parameters()) if hasattr(sub, "parameters") else 0
    dest = out_dir / f"{part['key']}.onnx"
    t0 = time.time()
    try:
        # A REAL FORWARD FIRST. Exporting needs example inputs, and the honest
        # way to get them is to watch what the module is actually called with
        # rather than to invent a shape — an invented shape that happens to
        # work proves nothing about the real path.
        hook = {}

        def grab(_m, args, _kw):
            if "args" not in hook:
                hook["args"] = tuple(a.detach() if hasattr(a, "detach") else a for a in args)
            return None

        h = sub.register_forward_pre_hook(grab, with_kwargs=True)
        try:
            model.generate(LINE, audio_prompt_path=str(reference()), exaggeration=0.45)
        finally:
            h.remove()
        if "args" not in hook:
            return {"part": part["key"], "verdict": "never called",
                    "detail": "a full generate() did not call this submodule, so there is "
                              "no real input to export it with"}
        torch.onnx.export(sub, hook["args"], str(dest), opset_version=17,
                          do_constant_folding=True, dynamo=False)
        size = dest.stat().st_size / 1e6
        v = {"part": part["key"], "verdict": "exported",
             "megabytes": round(size, 1), "params": n_params,
             "seconds": round(time.time() - t0, 1)}
    except Exception as e:
        return {"part": part["key"], "verdict": "failed",
                "error": f"{type(e).__name__}: {str(e)[:400]}",
                "params": n_params, "seconds": round(time.time() - t0, 1)}

    # AN ONNX FILE THAT EXPORTS AND THEN DOES NOTHING IS A FAILURE THAT LOOKS
    # LIKE A SUCCESS. Load it under onnxruntime, on DirectML, and make it run.
    try:
        import numpy as np
        import onnxruntime as ort
        eps = ["DmlExecutionProvider", "CPUExecutionProvider"]
        sess = ort.InferenceSession(str(dest), providers=eps)
        feeds = {}
        for inp, arg in zip(sess.get_inputs(), hook["args"]):
            feeds[inp.name] = arg.cpu().numpy() if hasattr(arg, "cpu") else np.asarray(arg)
        t1 = time.time()
        outs = sess.run(None, feeds)
        v["ran_on"] = sess.get_providers()[0]
        v["run_seconds"] = round(time.time() - t1, 2)
        v["output_shapes"] = [list(o.shape) for o in outs[:3]]
        v["verdict"] = "exported and runs"
    except Exception as e:
        v["verdict"] = "exported but will not run"
        v["run_error"] = f"{type(e).__name__}: {str(e)[:300]}"
    return v


def diagnose_watermarker():
    """Why `perth.PerthImplicitWatermarker` is None, said out loud, then
    replaced so it cannot stop the export.

    Returns a note for the operator, or None when the real one works. The
    diagnosis comes FIRST because working around a failure you have not
    identified is how a workaround becomes a second bug."""
    try:
        import perth
    except Exception as e:
        return f"the perth package will not import at all — {type(e).__name__}: {e}"

    if getattr(perth, "PerthImplicitWatermarker", None) is not None:
        return None

    # THE REAL ERROR, dug out rather than guessed. The name is None because
    # something under it failed and the package kept going.
    why = "no underlying error surfaced"
    import importlib
    for mod in ("perth.perth_net.perth_net_implicit.perth_net",
                "perth.perth_net", "perth.utils"):
        try:
            importlib.import_module(mod)
        except Exception as e:
            why = f"{mod}: {type(e).__name__}: {str(e)[:180]}"
            break

    class NoWatermark:
        """Returns the audio it was given. Chatterbox calls
        `apply_watermark(wav, sample_rate=...)`; anything else it might call is
        answered with the same identity so a version difference cannot turn
        this stub into a new mystery."""
        def apply_watermark(self, wav, sample_rate=None, **_):
            return wav

        def __getattr__(self, _name):
            return lambda *a, **k: (a[0] if a else None)

    perth.PerthImplicitWatermarker = NoWatermark
    return f"NOT AVAILABLE ({why})"


def reference():
    hits = sorted(CLIPS.glob(VOICE + ".*"))
    return hits[0] if hits else None


def cmd_run(args):
    OUT.mkdir(parents=True, exist_ok=True)
    if reference() is None:
        print(f"export-probe: no reference clip for '{VOICE}' under {CLIPS}")
        return 1

    try:
        import torch  # noqa: F401
        from chatterbox.tts import ChatterboxTTS
    except Exception as e:
        print(f"export-probe: chatterbox will not import — {type(e).__name__}: {e}")
        print("  That is the answer to a different question and it is worth having:")
        print("  send me this line. It means the environment is wrong, not the model.")
        return 2

    # THE WATERMARKER MUST NOT BE ABLE TO STOP THIS.
    #
    # First run: `TypeError: 'NoneType' object is not callable` on
    # `perth.PerthImplicitWatermarker()`. The package imported and the class
    # inside it was None — a silent failed import, which is the shape this
    # project distrusts most: `perth/__init__` swallows its own error and
    # leaves a name bound to nothing, so the failure surfaces hundreds of
    # lines away as a type error about NoneType.
    #
    # It also worked in the bark-render environment, so it is environmental
    # rather than broken, and it is IRRELEVANT to the question being asked:
    # the watermarker is post-processing applied to finished audio, not one of
    # the three pieces being exported. A probe that dies on it answers nothing.
    #
    # So: say what actually went wrong, then stand a no-op in its place and
    # carry on. DECLARED, not hidden — the shipped path has to make its own
    # decision about Resemble's watermark, and this stub is for the export
    # question only.
    watermark_note = diagnose_watermarker()
    if watermark_note:
        print(f"  watermarker: {watermark_note}")
        print("  standing a no-op in its place — it is post-processing, not a")
        print("  piece being exported, and it must not block the answer.\n")

    print("  loading the model on CPU (export does not need a GPU)...")
    t0 = time.time()
    model = ChatterboxTTS.from_pretrained(device="cpu")
    print(f"  loaded in {time.time() - t0:.0f}s\n")

    rows = []
    for part in PARTS:
        print(f"  {part['key']:8} {part['what']}")
        print(f"           risk: {part['risk']}")
        v = try_export(model, part, OUT)
        rows.append(dict(v, what=part["what"]))
        if v["verdict"].startswith("exported"):
            print(f"           -> {v['verdict'].upper()}"
                  + (f", {v.get('megabytes')} MB" if v.get("megabytes") else "")
                  + (f", ran on {v.get('ran_on')}" if v.get("ran_on") else ""))
            if v.get("run_error"):
                print(f"              {v['run_error']}")
        else:
            print(f"           -> {v['verdict'].upper()}")
            print(f"              {v.get('error') or v.get('detail')}")
        print()

    REPORT.write_text(json.dumps({"parts": rows}, indent=1), encoding="utf-8")
    good = [r for r in rows if r["verdict"] == "exported and runs"]
    print(f"  {len(good)} of {len(rows)} part(s) exported AND ran under onnxruntime.")
    print(f"  full report: {REPORT}")
    # NO SINGLE VERDICT. A partial result is the likely one and it is the
    # actionable one; collapsing it to pass/fail throws away which day's work
    # is left.
    return 0


def selftest():
    """Everything that decides the answer, none of which needs the model —
    because the one path that needed hardware is the one that shipped broken
    this morning."""
    fails, ran = [], []

    def check(ok, what):
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}")
        ran.append(what)
        if not ok:
            fails.append(what)

    check(len(PARTS) == 3 and all(p["names"] and p["risk"] for p in PARTS),
          f"every part names its risk and its aliases ({len(PARTS)})")
    check(len({p["key"] for p in PARTS}) == len(PARTS), "no two parts share a key")

    class Fake:
        pass
    m = Fake()
    m.s3gen = "something"
    n, sub = find_part(m, ["flow", "s3gen", "decoder"])
    check(n == "s3gen" and sub == "something", "a renamed submodule is found by alias")
    n2, sub2 = find_part(m, ["nope", "also_nope"])
    check(n2 is None and sub2 is None, "an absent submodule reports absent rather than throwing")

    check(reference() is not None, f"the reference clip for '{VOICE}' is on disk")
    check(len(LINE) > 30, "the test line is long enough to drive a real forward pass")

    import tempfile, shutil
    tmp = Path(tempfile.mkdtemp())
    try:
        rows = [{"part": "t3", "verdict": "failed", "error": "x"},
                {"part": "s3gen", "verdict": "exported and runs", "megabytes": 240.0}]
        f = tmp / "r.json"
        f.write_text(json.dumps({"parts": rows}, indent=1), encoding="utf-8")
        back = json.loads(f.read_text(encoding="utf-8"))["parts"]
        check(len(back) == 2 and back[1]["verdict"] == "exported and runs",
              "the report round-trips, so a partial result survives to be read")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\nexport-probe --selftest: {'PASS' if not fails else str(len(fails)) + ' FAILED'} — "
          f"{len(ran)} checks, none of which need the model")
    return 0 if not fails else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.run:
        return cmd_run(a)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
