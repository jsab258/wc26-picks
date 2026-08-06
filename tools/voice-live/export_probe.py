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
# EVERY DOOR A SUBMODULE MIGHT BE CALLED THROUGH. `forward` is the one a
# torch hook watches and the one `torch.onnx.export` traces; TTS stacks
# routinely do their real work in `inference` instead, which is exactly how
# the first run reported a decoder that plainly ran as "never called".
#
# Named here rather than inline so the self-test can assert the list, and so
# adding a door is one edit in one place.
ENTRY_POINTS = ("forward", "inference", "generate", "infer", "encode", "decode")

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


def dynamo_ready():
    """Is the SECOND exporter actually installed? Returns (ok, reason).

    THE FALLBACK NEVER RAN. Both t3 and s3gen came back with
    `dynamo_error: ModuleNotFoundError: No module named 'onnxscript'` — so
    the run reported two model failures when the truth was one missing
    package and a fallback that never got to try. That is rule 3b's shape:
    an absence dressed as a finding.

    It is worse than a plain zero, because the message sits in a field named
    for the model's behaviour. Checked ONCE, up front, and reported as an
    environment fact — so "the newer exporter cannot handle this" and "the
    newer exporter was not installed" stop looking identical.
    """
    try:
        import onnxscript  # noqa: F401
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:120]}"
    return True, ""


def merge_part_reports(out_dir, parts):
    """Collect one JSON per part into the single report.

    A part that left no file at all did not merely fail — its PROCESS died,
    which is a different fact and the one worth saying out loud. Silence
    would otherwise read as "not attempted".
    """
    rows = []
    for part in parts:
        f = out_dir / f"{part['key']}.json"
        if not f.exists():
            rows.append({"part": part["key"], "verdict": "died",
                         "what": part["what"],
                         "error": "the worker process produced no result at all — "
                                  "it crashed, ran out of memory, or was killed"})
            continue
        try:
            rows.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:
            rows.append({"part": part["key"], "verdict": "died",
                         "what": part["what"],
                         "error": f"unreadable result: {type(e).__name__}: {e}"})
    return rows


def export_with_fallback(export_fn, dest):
    """Try both exporters, keep both errors, and never let a stale file lie.

    TWO EXPORTERS, BECAUSE THEY FAIL AT DIFFERENT THINGS. The old TorchScript
    tracer goes first: when it works its output is the most predictable. It
    cannot follow an in-place write into a KV cache — t3 died on "We don't
    have an op for aten::scatter_", which is a limit of that tracer rather
    than a fault in the model, and retrying it cannot help. `dynamo=True` is
    PyTorch's newer exporter and handles exactly that class of dynamic
    control flow, so a TorchScript failure falls through to it rather than
    ending the part.

    BOTH messages are reported even when the second one saves the export.
    "It failed" hides WHICH exporter is the blocker, and that is the
    difference between "restructure the model" and "use the other exporter".

    THE UNLINK IS THE LOAD-BEARING LINE. A failed export can leave a partial
    `.onnx` behind, and a previous run's good one is worse — both survive to
    be `stat`-ed, loaded and reported on by the step below, which would read
    a stale success as this run's. That is rule 3b wearing a filename: a file
    that is present tells you nothing about whether THIS attempt produced it.
    Scoped to exactly the path this call writes, which is what rule 5 asks.

    Returns (exported, errors). On success `errors["exporter"]` names the one
    that worked; a torchscript entry alongside it means the fallback was
    needed.
    """
    errors = {}
    for label, use_dynamo in (("torchscript", False), ("dynamo", True)):
        try:
            if dest.exists():
                dest.unlink()
        except OSError:
            pass
        try:
            export_fn(use_dynamo)
        except Exception as ex:
            errors[label] = f"{type(ex).__name__}: {str(ex)[:260]}"
            continue
        # AND IT HAS TO HAVE WRITTEN SOMETHING. An exporter that returns
        # without raising and without producing a file would otherwise be
        # reported as a success, and `dest.stat()` would throw into the outer
        # handler where it reads as an export error rather than as this.
        if not dest.exists():
            errors[label] = "returned without raising but wrote no file"
            continue
        errors["exporter"] = label
        return True, errors
    return False, errors


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
    # RE-ASSERTED PER PART. `torch.onnx.export` flips train/eval and does not
    # reliably put it back, so part three inherited part two's mode. Cheap
    # insurance against a failure that belongs to a different part.
    for m in (model, sub):
        if hasattr(m, "eval"):
            m.eval()
    dest = out_dir / f"{part['key']}.onnx"
    t0 = time.time()
    try:
        # WATCH EVERY DOOR, NOT JUST `forward`.
        #
        # The first version registered a forward pre-hook and reported t3 and
        # s3gen as "never called" — from a `generate()` that plainly produced
        # audio, so it plainly called them. The tool was honest about what it
        # SAW and wrong about what that meant: chatterbox drives these stages
        # through custom `inference()` methods, and a forward hook never fires
        # for a method that is not `forward`.
        #
        # That is a fault in the instrument, not the subject, and it is the
        # shape CLAUDE.md rule 3 names: when a result is surprising, check the
        # ruler before the reading. "The model does not call its own decoder"
        # should have been unbelievable on its face.
        #
        # So every plausible entry point is wrapped and the one that actually
        # fires is RECORDED — which matters twice over, because
        # `torch.onnx.export` traces `forward`. If the real work lives in
        # `inference`, exporting the module directly would export the wrong
        # thing and look like it worked.
        hook = {}
        wrapped = []
        for meth in ENTRY_POINTS:
            fn = getattr(sub, meth, None)
            if not callable(fn) or meth in ("parameters", "children"):
                continue

            def make(m_name, real):
                def spy(*a, **kw):
                    if "args" not in hook:
                        hook["method"] = m_name
                        hook["args"] = tuple(x.detach() if hasattr(x, "detach") else x
                                             for x in a)
                        hook["kwargs"] = dict(kw)
                    return real(*a, **kw)
                return spy
            try:
                setattr(sub, meth, make(meth, fn))
                wrapped.append(meth)
            except Exception:
                pass  # a read-only attribute is not worth failing the probe over

        try:
            model.generate(LINE, audio_prompt_path=str(reference()), exaggeration=0.45)
        finally:
            for meth in wrapped:
                try:
                    delattr(sub, meth)   # restore the class's own bound method
                except Exception:
                    pass

        if "args" not in hook:
            return {"part": part["key"], "verdict": "never called",
                    "watched": wrapped,
                    "detail": "a full generate() called none of these entry points, so "
                              "there is no real input to export with. If the model works, "
                              "the entry point has another name and this list needs it."}

        # EXPORT WHAT IS ACTUALLY CALLED. When the work is in `inference`, the
        # module is wrapped in a thin `forward` that calls it, so the trace
        # follows the real path rather than whatever `forward` happens to do.
        target = sub
        if hook["method"] != "forward":
            class EntryWrapper(torch.nn.Module):
                def __init__(self, inner, meth, kwargs):
                    super().__init__()
                    self.inner = inner
                    self._meth = meth
                    self._kw = kwargs

                def forward(self, *a):
                    return getattr(self.inner, self._meth)(*a, **self._kw)
            target = EntryWrapper(sub, hook["method"], hook["kwargs"])

        # `no_grad` around the trace, because s3gen died on "Cannot insert a
        # Tensor that requires grad as a constant" — a parameter carrying
        # autograd state into the graph. See `export_with_fallback` for why
        # there are two attempts.
        def do_export(use_dynamo):
            with torch.no_grad():
                torch.onnx.export(target, hook["args"], str(dest),
                                  opset_version=17, do_constant_folding=True,
                                  dynamo=use_dynamo)

        exported, errors = export_with_fallback(do_export, dest)
        if not exported:
            return {"part": part["key"], "verdict": "failed",
                    "entry": hook.get("method"), "params": n_params,
                    "torchscript_error": errors.get("torchscript"),
                    "dynamo_error": errors.get("dynamo"),
                    "seconds": round(time.time() - t0, 1)}
        size = dest.stat().st_size / 1e6
        v = {"part": part["key"], "verdict": "exported",
             "entry": hook["method"], "exporter": errors.get("exporter"),
             # Present ONLY when the first exporter failed and the second
             # saved it. Its absence is how the report says "the ordinary
             # path worked" rather than staying silent about which did.
             "torchscript_error": errors.get("torchscript"),
             "megabytes": round(size, 1),
             "params": n_params, "seconds": round(time.time() - t0, 1)}
    except Exception as e:
        return {"part": part["key"], "verdict": "failed",
                "entry": hook.get("method"),
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
    """Orchestrator. One worker process per part, so the parts are actually
    independent — which is what this probe has claimed to be since it was
    written, and was not.

    THE PARTS WERE NEVER ISOLATED. Detecting the entry point means calling
    `model.generate()`, which runs the WHOLE pipeline, and each part was then
    exported from one long-lived model in one process. So every part inherited
    whatever the parts before it left behind.

    That is not a theory, it is the shape of the evidence. `ve` exported
    cleanly on the one run where t3 and s3gen never reached `torch.onnx.export`
    at all, and has failed on every run since where they did — the same error,
    at the same tenth of a second, before any entry point was recorded. I
    guessed train/eval mode, fixed that, and it changed nothing, so the guess
    was wrong and the leak is something else.

    Rather than guess again: give each part its own process and its own
    freshly-loaded model. Nothing can cross. If `ve` now exports, the leak was
    real and is gone; if it fails identically in a clean process, the cause is
    `ve` itself and every run up to now has been pointing at the wrong thing.
    The fix and the experiment are the same change, which is why it is worth
    the extra model load per part.

    It also means a part that runs out of memory or dies outright takes only
    itself down. The old loop lost every later answer with it.
    """
    import subprocess
    OUT.mkdir(parents=True, exist_ok=True)

    # STAMPED AND BLANKED BEFORE ANYTHING ELSE, and this is a repair.
    #
    # A run that bails early used to leave the PREVIOUS run's report sitting
    # in place, complete and plausible and months out of date if you like. It
    # cost a round trip: an old report was read back to me as a new result,
    # and the only reason it was caught is that three exports had produced
    # timings identical to a tenth of a second, which no two real runs do.
    #
    # I had already fixed exactly this one level down — the per-part files
    # below are deleted for the same reason, in the same commit — and did not
    # look at the file those files are merged INTO. One idea, two
    # implementations, and the one nobody looked at is the one missing the
    # line. That is written in CLAUDE.md as the most repeated fault in the
    # project and I walked into it inside the fix for its sibling.
    #
    # So the report is overwritten FIRST, with a marker saying it did not
    # finish. Every exit after this point replaces it. There is no path that
    # leaves the old one readable.
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")

    def report(rows, note=None):
        REPORT.write_text(json.dumps(
            {"run_started": stamp, "note": note, "parts": rows},
            indent=1), encoding="utf-8")

    report([], "this run did not finish — it exited before trying anything")

    if reference() is None:
        msg = f"no reference clip for '{VOICE}' under {CLIPS}"
        print(f"export-probe: {msg}")
        report([], msg)
        return 1

    ok, why = dynamo_ready()
    if not ok:
        print(f"  NOTE: the second exporter is not installed — {why}")
        print("  Only the older tracer will be tried. That is an environment")
        print("  answer, not a model one, and the last run reported it as if it")
        print("  were the model refusing.\n")

    # A STALE RESULT MUST NOT SURVIVE INTO THIS RUN'S REPORT. Each worker
    # writes one file and the merge reads them back, so a leftover from an
    # earlier run would be indistinguishable from an answer produced now.
    for part in PARTS:
        f = OUT / f"{part['key']}.json"
        if f.exists():
            f.unlink()

    for i, part in enumerate(PARTS, 1):
        print(f"  [{i}/{len(PARTS)}] {part['key']:8} {part['what']}")
        print(f"           risk: {part['risk']}")
        print("           (its own process, with its own freshly-loaded model)")
        r = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                            "--one", part["key"]])
        if r.returncode == 2:
            # chatterbox will not import. Every later part would say the same
            # thing at the same cost, so stop rather than pay three model
            # loads to print one environment error three times.
            print("\n  chatterbox will not import, so nothing can be tried.")
            report(merge_part_reports(OUT, PARTS),
                   "stopped at the first part: chatterbox will not import. "
                   "That is an environment answer, not a model one.")
            return 2
        print()

    rows = merge_part_reports(OUT, PARTS)
    report(rows, None if ok else
           f"the second exporter was not installed ({why}), so only the older "
           f"tracer was tried and no dynamo result here is about the model")
    good = [r for r in rows if r.get("verdict") == "exported and runs"]
    print(f"  {len(good)} of {len(rows)} part(s) exported AND ran under onnxruntime.")
    for r in rows:
        print(f"    {r['part']:8} {r.get('verdict', '?')}")
    # PRINTED SO THE CONSOLE AND THE FILE CAN BE COMPARED. If they disagree,
    # the file on screen is not the one this run wrote.
    print(f"  full report: {REPORT}")
    print(f"  this run is stamped {stamp} — the report says the same, and if it")
    print("  does not, you are looking at an older file.")
    return 0


def cmd_one(key):
    """One part, one process, one freshly-loaded model. See `cmd_run`."""
    part = next((p for p in PARTS if p["key"] == key), None)
    if part is None:
        print(f"export-probe: no part called '{key}'")
        return 1
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

    # EVAL MODE AND NO GRADIENTS, and the record of what each one was for.
    #
    # `no_grad` (in `try_export`) FIXED ITS FAULT and the report proves it:
    # s3gen's "Cannot insert a Tensor that requires grad as a constant" is
    # gone, replaced by a genuinely different and much later error about STFT.
    # That one is real.
    #
    # `eval()` DID NOT FIX WHAT I SAID IT WOULD. I read `ve`'s "Expected more
    # than 1 value per channel when training" as training mode left behind by
    # an earlier part, wrote that down as the diagnosis, and it came back
    # identical — same message, same tenth of a second, entry still null.
    # The reasoning was plausible and the fix was cheap and it was still a
    # guess, which is the thing this project keeps paying for.
    #
    # It stays because it is correct hygiene and costs nothing. It is NOT the
    # explanation for `ve`, and the isolation in `cmd_run` is what will
    # actually settle that — see the note there.
    import torch
    for m in (model, getattr(model, "t3", None), getattr(model, "s3gen", None),
              getattr(model, "ve", None)):
        if m is not None and hasattr(m, "eval"):
            m.eval()
        if m is not None and hasattr(m, "parameters"):
            for prm in m.parameters():
                prm.requires_grad_(False)
    print(f"  loaded in {time.time() - t0:.0f}s, eval mode, gradients off\n")

    v = dict(try_export(model, part, OUT), what=part["what"])
    if v["verdict"].startswith("exported"):
        print(f"           -> {v['verdict'].upper()}"
              + (f", {v.get('megabytes')} MB" if v.get("megabytes") else "")
              + (f", ran on {v.get('ran_on')}" if v.get("ran_on") else ""))
        if v.get("run_error"):
            print(f"              {v['run_error']}")
    else:
        print(f"           -> {v['verdict'].upper()}")
        print(f"              {v.get('error') or v.get('detail') or v.get('torchscript_error')}")

    (OUT / f"{part['key']}.json").write_text(json.dumps(v, indent=1), encoding="utf-8")
    # ALWAYS ZERO. The worker's exit code says whether the PROBE ran, not
    # whether the part exported — the orchestrator reads the verdict from the
    # file. Conflating the two is how "the model cannot convert" and "the
    # script fell over" end up looking the same, which is the fault this
    # whole probe exists to avoid making.
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

    # THE FAULT THE FIRST RUN FOUND, asserted so it cannot come back: hooking
    # only `forward` reported a decoder that plainly ran as "never called".
    check("forward" in ENTRY_POINTS and "inference" in ENTRY_POINTS,
          f"every likely entry point is watched, not just forward ({len(ENTRY_POINTS)})")
    check(ENTRY_POINTS[0] == "forward",
          "forward is tried first, because when it IS the entry point no wrapper is needed")

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

        # THE FALLBACK, DRIVEN WITH A FAKE EXPORTER. All four paths, none of
        # which needs torch — and this exists because the last thing shipped
        # from this folder without being executed was a NameError on a line
        # only a GPU could reach, and it cost a two-hour batch. A fake
        # `export_fn` is all it takes to run every branch here.
        d = tmp / "p.onnx"

        def writes(_use_dynamo):
            d.write_bytes(b"onnx")

        def raises(_use_dynamo):
            raise RuntimeError("no op for aten::scatter_")

        seen = []

        def only_dynamo(use_dynamo):
            seen.append(use_dynamo)
            if not use_dynamo:
                raise RuntimeError("no op for aten::scatter_")
            d.write_bytes(b"onnx")

        def silent(_use_dynamo):
            pass

        ok, errs = export_with_fallback(writes, d)
        check(ok and errs.get("exporter") == "torchscript" and "dynamo" not in errs,
              "the ordinary path exports on the first exporter and never tries the second")

        d.write_bytes(b"stale from an earlier run")
        ok, errs = export_with_fallback(raises, d)
        check(not ok and "torchscript" in errs and "dynamo" in errs,
              "when both exporters fail, both errors are kept")
        check(not d.exists(),
              "and a previous run's file is gone, so a stale export cannot be read as this one's")

        d.unlink(missing_ok=True)
        ok, errs = export_with_fallback(only_dynamo, d)
        check(ok and errs.get("exporter") == "dynamo" and errs.get("torchscript"),
              "a torchscript failure falls through to dynamo, and says why it had to")
        check(seen == [False, True],
              "in that order — the predictable tracer first, the fallback second")

        d.unlink(missing_ok=True)
        ok, errs = export_with_fallback(silent, d)
        check(not ok and "wrote no file" in str(errs.get("dynamo", "")),
              "an exporter that returns without writing anything is a failure, not a success")

        # THE MERGE, which is what turns three separate processes back into
        # one report. Its failure mode is silence: a worker that dies leaves
        # no file, and a missing row reads as "not attempted" rather than as
        # the crash it was.
        md = tmp / "merged"
        md.mkdir()
        (md / "t3.json").write_text(json.dumps(
            {"part": "t3", "verdict": "exported and runs"}), encoding="utf-8")
        (md / "ve.json").write_text("{not json at all", encoding="utf-8")
        merged = merge_part_reports(md, PARTS)
        by = {r["part"]: r for r in merged}
        check(len(merged) == len(PARTS),
              "every part gets a row even when its process wrote nothing")
        check(by["t3"]["verdict"] == "exported and runs",
              "a worker's own verdict survives the merge intact")
        check(by["s3gen"]["verdict"] == "died" and "crashed" in by["s3gen"]["error"],
              "a part whose process vanished is reported as died, not as absent")
        check(by["ve"]["verdict"] == "died" and "unreadable" in by["ve"]["error"],
              "and a half-written result file is a death too, not a parse crash")

        # A MISSING EXPORTER IS AN ENVIRONMENT FACT. Both real parts came back
        # blaming the model for a package that was never installed.
        ready, why = dynamo_ready()
        check(isinstance(ready, bool) and (ready or why),
              "the second exporter's absence is detectable, and says which package")

        check(all(p["key"] in {q["key"] for q in PARTS} for p in PARTS)
              and cmd_one("no-such-part") == 1,
              "asking for a part that does not exist fails instead of guessing one")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # A STALE REPORT MUST NOT SURVIVE A RUN THAT BAILED, and this one is run
    # for real rather than simulated, because the fault it guards against was
    # an old report being read back to me as a new result.
    #
    # Only where chatterbox is absent — on a machine that HAS it this would
    # load the model and take minutes, and a self-test that expensive stops
    # being run. That is the honest trade and it is stated rather than hidden:
    # this container is where `verify.py` runs, and it has no torch.
    try:
        import torch  # noqa: F401
        check(True, "stale-report check skipped: this machine can really run the probe")
    except Exception:
        OUT.mkdir(parents=True, exist_ok=True)
        planted = {"parts": [{"part": "t3", "verdict": "exported and runs",
                              "seconds": 106.9}]}
        REPORT.write_text(json.dumps(planted), encoding="utf-8")
        rc = cmd_run(None)
        after = json.loads(REPORT.read_text(encoding="utf-8"))
        check(rc == 2, "a run with no chatterbox stops at the first part")
        check(after.get("parts") != planted["parts"],
              "and the previous run's report does NOT survive it")
        check(bool(after.get("run_started")),
              "the report it leaves is stamped with when the run started")
        check("chatterbox" in str(after.get("note", "")),
              "and says why it stopped, so an empty result is not read as a finding")

    print(f"\nexport-probe --selftest: {'PASS' if not fails else str(len(fails)) + ' FAILED'} — "
          f"{len(ran)} checks, none of which need the model")
    return 0 if not fails else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--one", metavar="PART",
                    help="one part, in this process — what --run spawns per part")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.one:
        return cmd_one(a.one)
    if a.run:
        return cmd_run(a)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
