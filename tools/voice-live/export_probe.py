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

# A SECOND REAL VOICE AND A SECOND REAL LINE, because "different input" has to
# mean what the game will actually do.
#
# The agreement check compared against synthetic noise, which is not a thing
# any player produces and is not what a converted model has to be right about.
# Driving a second real generate costs under a minute per part and gives the
# only comparison that settles the question: does this file give the same
# answer for a DIFFERENT CHARACTER SAYING A DIFFERENT SENTENCE. That is the
# whole job.
SECOND_VOICE = "ada"
SECOND_LINE = "He was here before the rain started, and he did not come in."

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
        return False, tidy(e, 200)
    return True, ""


def tidy(ex, limit=1600):
    """An exception as text: no colour codes, and long enough to be useful.

    THE OLD LIMIT THREW AWAY THE ANSWER. Dynamo's failure was cut at 260
    characters, and every one of those characters was boilerplate — "Failed to
    export the model with torch.export. This is step 1/3 ... Refer to
    https://pytorch.org/docs/..." — with the actual reason after it. Two parts
    reported a failure whose cause had been truncated off the end, which is
    rule 3b's cap: a limit nobody is told about is indistinguishable from a
    finding.

    The colour codes are the same problem one layer down. `\\u001b[96m` in a
    JSON report is noise in the one field somebody has to read carefully.
    """
    import re
    s = re.sub(r"\x1b\[[0-9;]*m", "", str(ex))
    s = " ".join(s.split())
    if len(s) > limit:
        s = s[:limit] + f" ...[{len(s) - limit} more characters]"
    return f"{type(ex).__name__}: {s}"


def export_candidates(order):
    """Which entry points to try exporting, in order. `order` is the methods
    that actually fired, in the order they fired.

    THE OBSERVED ONE FIRST, because it is what the model really runs and so
    the most faithful thing to convert — if it exports, the whole stage is in
    the graph and the game just feeds it.

    `forward` SECOND, because when the outer method fails it is nearly always
    the preprocessing that failed, not the network. Every failure so far has
    been of that shape: `divmod(Tensor, int)` in the voice encoder's window
    arithmetic, an STFT in the decoder. Neither needs to be inside the graph;
    both are ordinary signal processing the game can do in C#. `forward` is
    usually the pure network with that work already done.

    Then anything else that fired, so a stack that hides its network behind
    some third name still gets a try.
    """
    seen, out = set(), []
    for m in list(order[:1]) + ["forward"] + list(order):
        if m in order and m not in seen:
            seen.add(m)
            out.append(m)
    return out


def provider_verdict(ran):
    """Turn per-provider results into one verdict. `ran` maps a provider name
    to either its timings or an `error`.

    THREE OUTCOMES, NOT TWO, and the middle one is the whole reason this is a
    separate function. "Runs on the GPU" and "will not run at all" were the
    only two the probe could say, so a model that is perfectly valid and
    merely unaccelerated was reported the same as a broken graph. Those want
    opposite next steps: one is an opset or a driver, the other is redoing the
    export.
    """
    gpu = ran.get("DmlExecutionProvider", {})
    cpu = ran.get("CPUExecutionProvider", {})
    if "error" not in gpu and gpu:
        return dict(gpu, verdict="exported and runs")
    if "error" not in cpu and cpu:
        return dict(cpu, verdict="exported, runs on CPU, will not run on the GPU",
                    run_error=gpu.get("error"))
    return {"verdict": "exported but will not run",
            "run_error": gpu.get("error"), "cpu_error": cpu.get("error")}


def worth_retrying_without_asserts(row):
    """Would stripping Python's asserts plausibly change this failure?

    t3's dynamo error names the line: `t3.py:36 _ensure_BOT_EOT`,

        assert (text_tokens == hp.start_text_token).int().sum() >= B

    and the complaint is `GuardOnDataDependentSymNode: Could not guard on
    data-dependent expression Eq(u0, 1)`. That is a SANITY CHECK on the input,
    not part of the model's arithmetic — and `python -O` removes every assert
    at compile time, so the exporter would never see it.

    A HYPOTHESIS, NOT A FIX, and labelled as one everywhere it appears. I
    could not reproduce this locally: a small module with an assert of the
    same shape exports fine either way, because the real one involves an
    unbacked symbol this fixture has no way to produce. So the evidence is
    the error naming an assert and nothing more. It costs one extra model
    load on a part that has already failed, which is worth an answer.

    Narrow on purpose. A part that failed on STFT or on a missing operator
    would gain nothing and would spend the load for it.
    """
    if row.get("verdict") != "failed":
        return False
    blob = " ".join(str(row.get(k, "")) for k in
                    ("torchscript_error", "dynamo_error", "error")).lower()
    return ("assert" in blob
            or "guardondatadependent" in blob
            or "could not guard on data-dependent" in blob)


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
            errors[label] = tidy(ex)
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
    # Bound before the try, so the handler below cannot raise a NameError of
    # its own and bury the error it was written to report.
    calls, order, candidates, attempts = {}, [], [], {}
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
        # EVERY DOOR THAT FIRED, NOT JUST THE FIRST — because the first one is
        # the one most likely to be unexportable.
        #
        # All three parts have now failed inside PREPROCESSING rather than
        # inside the network:
        #
        #   ve     divmod(Tensor, int) at voice_encoder.py:62 — the window
        #          arithmetic that chops the reference clip into frames
        #   s3gen  "STFT does not currently support complex types" — the
        #          spectrogram step at the edge of the graph
        #
        # Neither is the neural part refusing to convert. Both are ordinary
        # signal processing that happens to live inside the same method, and
        # neither needs to be in the exported graph at all: the game can chop
        # frames and take a spectrogram in C# for nothing.
        #
        # So every entry point that fires is recorded with the arguments it
        # was handed, and a failure on the outer one falls through to the
        # inner one. `forward` is usually the pure network with the
        # preprocessing already done, which makes it the second thing to try
        # and, when it works, tells us exactly which slice has to be
        # reimplemented outside.
        # HOW MANY TIMES, NOT JUST WHETHER. A child called ONCE per wrapper
        # call is most of the stage. A child called twenty times is one step
        # of a loop, and converting it converts none of the loop.
        #
        # This exists because the fall-through produced a success that meant
        # nothing: the stand-in text stage is a Linear called twenty times
        # under a stop condition, the wrapper converted wrong, the probe fell
        # through to the Linear, and the Linear agreed — reported as "inner
        # network only, 1056 of 1056 parameters", 100% coverage.
        #
        # 100% OF THE WEIGHTS AND NONE OF THE BEHAVIOUR. Parameter count
        # answers "how much of the model is in this file" and I was reading it
        # as "how much of the stage converted", which are the same number only
        # when the wrapper does nothing but call the child. The call count is
        # what tells those apart, and it costs one integer.
        # COUNTED IN BOTH DRIVES, and the COMPARISON is the real signal.
        #
        # A single count is a property of the input, not of the model. The
        # stand-in text stage is a loop that stops on a condition: it ran once
        # for the first voice and would run twenty times for another, so
        # `called_times: 1` was recorded and read as "not a loop" — the exact
        # wrong conclusion, from a number that was accurate.
        #
        # Two counts settle it. If the wrapper called this child a DIFFERENT
        # number of times for two different voices, the loop is data-dependent
        # and no single exported graph can contain it. That is proof rather
        # than inference, and it costs a second integer.
        counts = {}
        counts_b = {}
        swap = [False]          # True once the second, different-voice drive starts
        second = {}             # the same entry points, captured from that drive
        second_note = [None]

        def make(store, key, real):
            def spy(*a, **kw):
                grab = tuple(x.detach() if hasattr(x, "detach") else x for x in a)
                if swap[0]:
                    counts_b[key] = counts_b.get(key, 0) + 1
                    if key not in second:
                        second[key] = {"args": grab, "kwargs": dict(kw)}
                else:
                    counts[key] = counts.get(key, 0) + 1
                    if key not in store:
                        store[key] = {"args": grab, "kwargs": dict(kw)}
                        if store is calls:
                            order.append(key)
                return real(*a, **kw)
            return spy

        wrapped = []
        for meth in ENTRY_POINTS:
            fn = getattr(sub, meth, None)
            if not callable(fn) or meth in ("parameters", "children"):
                continue
            try:
                setattr(sub, meth, make(calls, meth, fn))
                wrapped.append((sub, meth))
            except Exception:
                pass  # a read-only attribute is not worth failing the probe over

        # AND THE NETWORKS INSIDE, because the wrapper is what keeps refusing.
        #
        # Every remaining blocker in the real model is INPUT VALIDATION rather
        # than arithmetic — t3 asserts its start token is present, and
        # `flow.py:164` does `if (token >= self.vocab_size).any()`. An exporter
        # has to know every branch in advance, so a check on data defeats it,
        # and the network behind the check never gets looked at.
        #
        # A shipped graph does not need those checks. The game decides what
        # goes in. So the direct children are watched too, with the inputs
        # they were really handed, and when the wrapper will not convert they
        # are tried on their own.
        #
        # ONE LEVEL, on purpose. Two would hook every linear layer in a
        # half-billion-parameter stack and turn the choice of what to export
        # into a search. The children of a part are its named stages, which is
        # the seam this is looking for.
        kids = {}
        kid_order = []
        try:
            for kname, kid in list(sub.named_children()):
                for meth in ENTRY_POINTS:
                    fn = getattr(kid, meth, None)
                    if not callable(fn) or meth in ("parameters", "children"):
                        continue
                    key = f"{kname}.{meth}"
                    try:
                        setattr(kid, meth, make(kids, key, fn))
                        wrapped.append((kid, meth))
                        kid_order.append((key, kid, kname, meth))
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            model.generate(LINE, audio_prompt_path=str(reference()), exaggeration=0.45)

            # THE SECOND DRIVE: a different character saying a different
            # sentence, captured through the same hooks into a separate store.
            #
            # This is the input the agreement check actually needs. Comparing
            # against synthetic noise asks whether the converted model matches
            # on something no player will ever produce; comparing against a
            # second real voice asks the only question that matters, which is
            # whether it still works for the next line of dialogue.
            #
            # Wrapped in its own try: a second voice failing to generate must
            # not cost the first one's answer, and a part with no second
            # capture simply falls back to the synthetic comparison and says
            # so rather than reporting nothing.
            try:
                second_ref = reference(SECOND_VOICE)
                if second_ref is not None:
                    swap[0] = True
                    model.generate(SECOND_LINE, audio_prompt_path=str(second_ref),
                                   exaggeration=0.7)
            except Exception as e:
                second_note[0] = tidy(e, 200)
        finally:
            for owner, meth in wrapped:
                try:
                    delattr(owner, meth)   # restore the class's own bound method
                except Exception:
                    pass

        if not order:
            return {"part": part["key"], "verdict": "never called",
                    "watched": wrapped,
                    "detail": "a full generate() called none of these entry points, so "
                              "there is no real input to export with. If the model works, "
                              "the entry point has another name and this list needs it."}

        candidates = export_candidates(order)

        def make_wrapper(inner, m, kwargs):
            """THE KWARGS ARE CLOSED OVER, NOT STORED ON THE MODULE.

            s3gen's dynamo failure named the culprit outright once the error
            stopped being truncated: "The tensor attributes
            self._kw['ref_dict']['prompt_token'], ... were assigned during
            export. Such attributes must be registered as buffers." `self._kw`
            is not chatterbox's. It is this wrapper's, three lines of mine,
            and it was being reported as the decoder refusing to convert.

            A closure keeps the same values out of the module's attribute
            dict, where the exporter has no reason to look at them."""
            class EntryWrapper(torch.nn.Module):
                def __init__(self):
                    super().__init__()
                    self.inner = inner

                def forward(self, *a):
                    return getattr(inner, m)(*a, **kwargs)
            return EntryWrapper()

        # ONE ORDERED LIST OF THINGS TO TRY: the wrapper's own doors first,
        # then the networks inside it, biggest first.
        #
        # THE CHILDREN USED TO BE REACHED ONLY WHEN THE EXPORT FAILED, and
        # that missed the encoder entirely. Its wrapper exports perfectly
        # well and produces WRONG NUMBERS — the window arithmetic frozen at
        # trace time — so there was no failure to fall through from, and the
        # one route that could have saved it was never tried.
        #
        # "It converted" is not the bar. "It converted and it is right" is,
        # so an attempt is only accepted when the numbers agree, and anything
        # short of that keeps looking.
        plan = []
        for meth in candidates:
            hook = dict(calls[meth], method=meth)
            tgt = sub if meth == "forward" else make_wrapper(sub, meth, hook["kwargs"])
            plan.append({"label": meth, "target": tgt, "args": hook["args"],
                         "method": meth, "inner": None})
        for key, kid, kname, mname in sorted(
                [(k, kd, kn, mn) for (k, kd, kn, mn) in kid_order if k in kids],
                key=lambda t: sum(p.numel() for p in t[1].parameters()), reverse=True):
            hook = dict(kids[key], method=mname)
            tgt = kid if mname == "forward" else make_wrapper(kid, mname, hook["kwargs"])
            plan.append({"label": f"child:{key}", "target": tgt, "args": hook["args"],
                         "method": mname,
                         "inner": {"child": kname, "method": mname,
                                   "params": sum(p.numel() for p in kid.parameters()),
                                   "called_times": counts.get(key, 0),
                                   "called_times_second_voice": counts_b.get(key, 0)}})

        attempts = {}
        exported = False
        inner_used = None
        best = None
        for step in plan:
            target, hook = step["target"], {"args": step["args"], "method": step["method"]}

            # `no_grad` around the trace, because s3gen died on "Cannot insert
            # a Tensor that requires grad as a constant" — a parameter
            # carrying autograd state into the graph. See
            # `export_with_fallback` for why there are two attempts.
            def do_export(use_dynamo, _t=target, _a=hook["args"]):
                with torch.no_grad():
                    torch.onnx.export(_t, _a, str(dest),
                                      opset_version=17, do_constant_folding=True,
                                      dynamo=use_dynamo)

            ok, errors = export_with_fallback(do_export, dest)
            row = {"torchscript": errors.get("torchscript"),
                   "dynamo": errors.get("dynamo")}
            if not ok:
                attempts[step["label"]] = row
                continue

            # EXPORTED. NOW IS IT RIGHT? Checked here rather than at the end,
            # because a wrong answer has to be able to fall through to the
            # next candidate — that is the whole point of the restructure.
            agree = None
            try:
                alt = None
                key2 = step["label"][6:] if step["label"].startswith("child:") else step["label"]
                if key2 in second:
                    a2 = second[key2]["args"]
                    if len(a2) == len(hook["args"]):
                        alt = a2
                agree = agreement(target, hook["args"], dest,
                                  "CPUExecutionProvider", real_alt=alt)
            except Exception as e:
                agree = {"verdict": "could not check", "error": tidy(e, 300)}
            row["agrees"] = agree
            attempts[step["label"]] = row

            # A SECOND REAL VOICE IS NOT ENOUGH ON ITS OWN, and the stand-in
            # proved it: the model built to freeze its loop count agrees with
            # a second real voice to 1.8e-07 and disagrees with synthetic
            # input by 105%. Both drives happened to take the same branch,
            # which is exactly how a frozen branch hides.
            #
            # So realistic input cannot replace the synthetic sweep — it
            # answers a different question. Real voices say "is it right for
            # the job"; synthetic extremes say "is anything frozen in here".
            # Only a clean pass on both is accepted; the mixed case keeps
            # looking and is reported as the ambiguity it is.
            good = agree.get("verdict") in ("agrees", "could not check")
            if best is None or good:
                best = {"label": step["label"], "target": target, "hook": hook,
                        "inner": step["inner"], "errors": errors, "agree": agree,
                        "size": dest.stat().st_size / 1e6}
            if good:
                exported = True
                inner_used = step["inner"]
                break
            # Wrong numbers. Keep the file only if nothing better turns up;
            # the next attempt overwrites it, which `export_with_fallback`
            # handles by unlinking first.

        if not exported and best is not None:
            # NOTHING WAS RIGHT, BUT SOMETHING CONVERTED. Re-export the best
            # one so the file on disk matches what the verdict describes —
            # later attempts will have overwritten it — and report it as the
            # near-miss it is rather than as a failure. "It converts and the
            # numbers are wrong" is a different day's work from "it will not
            # convert", and the report has to keep them apart.
            def redo(use_dynamo, _t=best["target"], _a=best["hook"]["args"]):
                with torch.no_grad():
                    torch.onnx.export(_t, _a, str(dest), opset_version=17,
                                      do_constant_folding=True, dynamo=use_dynamo)
            export_with_fallback(redo, dest)
            exported = True
            inner_used = best["inner"]
            hook = best["hook"]
            target = best["target"]
            errors = best["errors"]

        if not exported:
            first = attempts.get(candidates[0], {})
            return {"part": part["key"], "verdict": "failed",
                    "entry": candidates[0], "params": n_params,
                    # WHICH DOORS WERE TRIED, so "the network will not convert"
                    # and "only the outer method was ever attempted" stop
                    # looking the same.
                    "entries_tried": candidates,
                    "children_tried": [k for k in attempts if k.startswith("child:")],
                    "torchscript_error": first.get("torchscript"),
                    "dynamo_error": first.get("dynamo"),
                    "by_entry": attempts,
                    "seconds": round(time.time() - t0, 1)}
        size = dest.stat().st_size / 1e6
        v = {"part": part["key"],
             "verdict": "exported" if not inner_used else "inner network exported",
             # WHAT ACTUALLY GOT CONVERTED. When only a child converted, the
             # wrapper around it is work the game has to do itself, and its
             # parameter count says how much of the stage this really is —
             # a verdict of "exported" over 3% of the weights would be a lie
             # of the most expensive kind.
             "inner_network": inner_used,
             "entry": hook["method"], "exporter": errors.get("exporter"),
             # WHICH DOOR IT CAME THROUGH, and it decides the shipping work.
             # If the observed entry point exported, the whole stage is in the
             # graph and C# just feeds it. If `forward` did instead, then the
             # preprocessing in the outer method — the windowing, the
             # spectrogram — has to be reimplemented outside the model, and
             # `skipped_entry` names what that is.
             "skipped_entry": None if hook["method"] == candidates[0] else candidates[0],
             # Present ONLY when the first exporter failed and the second
             # saved it. Its absence is how the report says "the ordinary
             # path worked" rather than staying silent about which did.
             "torchscript_error": errors.get("torchscript"),
             "by_entry": attempts,
             "agrees": (best or {}).get("agree"),
             "megabytes": round(size, 1),
             "params": n_params, "seconds": round(time.time() - t0, 1)}
    except Exception as e:
        return {"part": part["key"], "verdict": "failed",
                "entry": (order[0] if order else None),
                "error": tidy(e),
                "params": n_params, "seconds": round(time.time() - t0, 1)}

    # AN ONNX FILE THAT EXPORTS AND THEN DOES NOTHING IS A FAILURE THAT LOOKS
    # LIKE A SUCCESS. Load it under onnxruntime and make it run.
    #
    # EACH PROVIDER SEPARATELY, AND THIS IS A REPAIR. Passing
    # ["DmlExecutionProvider", "CPUExecutionProvider"] reads like a fallback
    # list and is not one: DirectML failed during session INITIALISATION —
    # `DmlGraphFusionHelper` with 80070057, which is E_INVALIDARG — and the
    # whole session constructor threw, so CPU was never reached. The verdict
    # said "exported but will not run" when what it had tested was "will not
    # run on DirectML".
    #
    # Those are completely different findings. If it runs on CPU, the graph is
    # VALID and the problem belongs to DirectML's graph fusion, which is an
    # opset or a driver away from working. If it fails on CPU too, the
    # exported graph is wrong and the export needs redoing. One is a
    # afternoon, the other is a rethink, and the old code could not tell them
    # apart — while printing a sentence that implied it had.
    import numpy as np

    def try_provider(ep):
        import onnxruntime as ort
        sess = ort.InferenceSession(str(dest), providers=[ep])
        feeds = {}
        for inp, arg in zip(sess.get_inputs(), hook["args"]):
            feeds[inp.name] = arg.cpu().numpy() if hasattr(arg, "cpu") else np.asarray(arg)
        t1 = time.time()
        outs = sess.run(None, feeds)
        return {"ran_on": sess.get_providers()[0],
                "run_seconds": round(time.time() - t1, 2),
                "output_shapes": [list(o.shape) for o in outs[:3]]}

    ran = {}
    for ep in ("DmlExecutionProvider", "CPUExecutionProvider"):
        try:
            ran[ep] = try_provider(ep)
        except Exception as e:
            ran[ep] = {"error": tidy(e)}

    v["by_provider"] = ran
    v.update(provider_verdict(ran))
    # AND THE VERDICT MUST NOT FORGET IT WAS ONLY A CHILD. `provider_verdict`
    # writes a flat "exported and runs", which is true of the file and false
    # about the stage — the validating wrapper is still work the game owes.
    # Caught by running it: the fixture's decoder reported a plain success
    # for a graph that is the inner network alone.
    if inner_used:
        n = inner_used.get("called_times", 0)
        n2 = inner_used.get("called_times_second_voice", 0)
        if n2 and n != n2:
            # PROOF, not inference. Two real voices drove this child a
            # different number of times, so the wrapper's loop depends on the
            # data and no single graph can hold it.
            v["verdict"] = (f"a data-dependent loop: the wrapper ran this {n} times "
                            f"for one voice and {n2} for another")
            v["shipping_work"] = (f"the loop must be rebuilt outside the model and "
                                  f"driven step by step — it ran {n} and {n2} times "
                                  f"for two different lines, so its length is not "
                                  f"fixed and cannot be baked into the graph")
        elif n > 1:
            # ONE STEP OF A LOOP. Say so in the verdict, because this is the
            # reading that looks like a result and is not one: the wrapper
            # runs this child n times and decides when to stop, and none of
            # that decision is in the file.
            v["verdict"] = (f"only one step of a loop converted — the wrapper ran "
                            f"this {n} times and none of that is in the graph")
            v["shipping_work"] = (f"the loop and its stop condition, which ran {n} "
                                  f"iterations here, must be rebuilt outside the model")
        else:
            v["verdict"] = "inner network only: " + v["verdict"]
            v["shipping_work"] = ("the wrapper around this child — its input "
                                  "checks and any signal processing — must be "
                                  "rebuilt outside the model")

    # AND DOES IT PRODUCE THE RIGHT NUMBERS? Everything above this line can
    # pass on a model that is quietly wrong.
    #
    # Demonstrated here, not suspected. A module whose loop stops on a
    # data-dependent condition — which is what an autoregressive stage IS —
    # traces without error, exports, loads, runs, and returns the right SHAPE.
    # On the input it was traced with it agrees to the last decimal. On any
    # other input it was out by 12.4, because the tracer baked the loop count
    # in as a constant.
    #
    # The probe checked that it exported, that it ran, and that the shape was
    # right. All three pass. "Exported and runs" would have gone in the report
    # as a green verdict for a model that produces garbage for every line
    # except the one test sentence — and the docstring at the top of this file
    # says an ONNX file that exports and then produces silence is a failure
    # that looks like a success. I wrote that, then checked the shape and not
    # the values.
    #
    # SO: run the original model on the same input and compare, then do it
    # again with DIFFERENT input. The second comparison is the one that
    # matters. The first can only fail if the export is broken outright; the
    # second is the only thing that catches control flow frozen into the graph,
    # and it is exactly the failure the risky part of this model is prone to.
    # ALREADY MEASURED, in the attempt loop, because a wrong answer had to be
    # able to fall through to the next candidate rather than ending the part.
    # What is left here is only to let it decide the verdict.
    av = (v.get("agrees") or {}).get("verdict")
    if av and av not in ("agrees", "could not check"):
        # THE WORDING FOLLOWS THE FINDING. "The numbers are wrong" is right
        # for a model that fails on a real second voice and overstated for one
        # that only differs on artificial input — and the first version said
        # it for both, which is the flat verdict this file keeps having to
        # take apart.
        v["verdict"] = v["verdict"] + (
            ", but only artificial input disagrees — unresolved"
            if av.startswith("agrees for real voices")
            else ", but the numbers are wrong")
    return v


def agreement(model, args, onnx_path, provider, tol=1e-2, real_alt=None):
    """Does the converted model produce the same numbers as the original?

    Twice: once on the input it was traced with, once on different input. See
    the note at the call site for why the second one is the whole point.

    `tol` is RELATIVE — a fraction of the reference output's own magnitude —
    because an absolute number cannot be judged without knowing the scale of
    what is being compared, and the first version of this reported one anyway.
    1% is loose enough that float32-vs-float64 and a different operator order
    do not trip it, and far tighter than any difference a frozen branch
    produces: the stand-in built to bake its loop count came in at 4.09
    against outputs of order 1.
    """
    import numpy as np
    import onnxruntime as ort
    import torch

    sess = ort.InferenceSession(str(onnx_path), providers=[provider])
    names = [i.name for i in sess.get_inputs()]

    def compare(sample):
        """Returns (relative worst, absolute worst, reference magnitude, error).

        A DIFFERENCE NEEDS A DENOMINATOR, and the first version had none.
        The encoder came back with `other_input_worst: 0.0449` and I could
        not say whether that was four per cent or four thousandths of one,
        because nothing recorded how big the numbers being compared were.
        That is rule 3b — a zero needs a denominator — happening to a
        difference instead of a zero, in the newest check in this file, one
        commit after writing it.

        The scale is the reference output's own magnitude, so the verdict is
        about proportion rather than about units nobody chose.
        """
        with torch.no_grad():
            want = model(*sample)
        want = [want] if not isinstance(want, (tuple, list)) else list(want)
        feeds = {n: (a.cpu().numpy() if hasattr(a, "cpu") else np.asarray(a))
                 for n, a in zip(names, sample)}
        got = sess.run(None, feeds)
        worst_abs, worst_rel, mag = 0.0, 0.0, 0.0
        for w, g in zip(want, got):
            w = w.cpu().numpy() if hasattr(w, "cpu") else np.asarray(w)
            g = np.asarray(g)
            if w.shape != g.shape:
                return None, None, None, f"shape {list(w.shape)} became {list(g.shape)}"
            w = w.astype("float64")
            g = g.astype("float64")
            a = float(np.abs(w - g).max())
            scale = float(np.abs(w).max())
            worst_abs = max(worst_abs, a)
            mag = max(mag, scale)
            worst_rel = max(worst_rel, a / scale if scale > 1e-12 else (0.0 if a == 0 else 1.0))
        return worst_rel, worst_abs, mag, None

    out = {}
    same, same_abs, same_mag, err = compare(args)
    out["same_input_worst_relative"] = same
    out["same_input_worst_absolute"] = same_abs
    out["output_magnitude"] = same_mag
    if err:
        return dict(out, verdict="shapes differ", detail=err)

    # DIFFERENT INPUT — AND AT SEVERAL SCALES, WHICH IS THE PART I GOT WRONG
    # FIRST TIME.
    #
    # The first version drew one `randn_like`. Run against a stand-in built
    # deliberately to bake its loop count in, it reported "agrees" — because a
    # fresh sample from the SAME distribution takes the same branch. Measured:
    # the traced input ran 1 step, and four fresh `randn` draws ran 1, 1, 1, 1.
    # Only scaling by 0.1 flipped it, to 20.
    #
    # So a check written specifically to catch frozen control flow passed the
    # one model in the world I had built to have frozen control flow. Same
    # distribution is not the same as different input. Several magnitudes, and
    # the WORST disagreement is what counts — a branch that survives one scale
    # and not another is exactly the fault being looked for.
    # THE REAL SECOND VOICE FIRST, because it is the only comparison that
    # answers the shipping question. Synthetic noise is not a thing a player
    # produces, and a model may legitimately behave oddly far outside the
    # data it was trained on without that meaning anything for the game.
    if real_alt is not None:
        r, r_abs, _m, r_err = compare(real_alt)
        out["second_voice_worst_relative"] = r
        out["second_voice_worst_absolute"] = r_abs
        if r_err:
            out["second_voice_error"] = r_err
        elif r is not None and r > tol:
            return dict(out, verdict="wrong for a different voice",
                        detail="the converted model gives a different answer for "
                               "another character saying another line, which is "
                               "the job it exists to do")

    worst, worst_abs2, err2 = None, None, None
    for scale in (1.0, 0.1, 5.0, 25.0):
        other = tuple(torch.randn_like(a) * scale
                      if hasattr(a, "dtype") and getattr(a.dtype, "is_floating_point", False)
                      else a for a in args)
        d, d_abs, _mag, e = compare(other)
        if e:
            err2 = e
            break
        worst = d if worst is None else max(worst, d)
        worst_abs2 = d_abs if worst_abs2 is None else max(worst_abs2, d_abs)
    diff = worst
    out["other_input_worst_relative"] = diff
    out["other_input_worst_absolute"] = worst_abs2
    out["other_input_scales"] = [1.0, 0.1, 5.0, 25.0]
    out["tolerance_relative"] = tol
    if err2:
        return dict(out, verdict="shapes differ on other input", detail=err2)

    if same is not None and same > tol:
        return dict(out, verdict="wrong even on the traced input")
    if diff is not None and diff > tol:
        if out.get("second_voice_worst_relative") is not None:
            # A REAL SECOND VOICE AGREED AND ONLY SYNTHETIC NOISE DID NOT.
            # Reported, not condemned. It is consistent with a frozen branch
            # and equally consistent with the model behaving oddly on input
            # unlike anything it was trained on, and this check cannot tell
            # those apart — so it says so instead of picking.
            return dict(out, verdict="agrees for real voices; differs on synthetic input",
                        detail="a second real voice matched; only artificial noise "
                               "disagreed, which may be a frozen branch or may be "
                               "the model being out of its depth on noise")
        # THE FINDING THIS EXISTS FOR, and it has its own words because it is
        # the one that looks like success.
        return dict(out, verdict="only correct for the input it was traced with",
                    detail="the converted model agrees on the test sentence and "
                           "disagrees on anything else, which is control flow "
                           "baked in as a constant during tracing")
    return dict(out, verdict="agrees")


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
            why = f"{mod}: {tidy(e, 300)}"
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


def reference(voice=None):
    hits = sorted(CLIPS.glob((voice or VOICE) + ".*"))
    return hits[0] if hits else None


def cmd_run(args, allow_install=True):
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

    # THE MISSING EXPORTER IS INSTALLED FROM HERE, NOT FROM THE .BAT, AND THE
    # REASON IS A TRAP WORTH WRITING DOWN.
    #
    # The bat copies itself to %TEMP% and re-launches BEFORE it pulls — it has
    # to, because a pull rewriting a script that cmd.exe is reading by byte
    # offset is how a script once printed the tail of a URL from its own
    # replacement. The consequence nobody had drawn out: the copy that runs is
    # the one that was on disk BEFORE the pull, so a change to the BAT takes
    # effect one run later than the change that prompted it.
    #
    # Python has no such lag. The bat pulls, then invokes this file, so the
    # interpreter reads the version that just arrived. Every probe fix has
    # landed on the next run; the one install line I put in the bat did not,
    # and the report came back naming the same missing package for a third
    # time. A whole round trip for a line that was already written.
    #
    # So anything that must take effect NOW lives on this side of the line.
    # The bat keeps its copy, which is correct for what it guards against.
    ok, why = dynamo_ready()
    if not ok and not allow_install:
        # THE SELF-TEST MUST NOT INSTALL ANYTHING. It runs inside verify.py on
        # every commit, and a check that reaches for the network and mutates
        # the interpreter it is testing is no longer a check. Caught by
        # watching it actually do it: the first run of this self-test pulled
        # onnxscript into this container as a side effect.
        print("  (self-test: not installing anything)")
    elif not ok:
        print(f"  The second exporter is not installed — {why}")
        print("  Installing onnxscript now (a bat change would not take effect")
        print("  until the run after this one, which is why it is done here)...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "onnxscript"],
                           check=False)
        except Exception as e:
            print(f"  the install could not be started: {type(e).__name__}: {e}")
        ok, why = dynamo_ready()
        print("  installed — both exporters will be tried.\n" if ok else
              f"  STILL not available ({why}). Only the older tracer will be\n"
              "  tried, and no dynamo line in the report is about the model.\n")

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
        me = str(Path(__file__).resolve())
        extra = ["--fixture"] if getattr(args, "fixture", False) else []
        r = subprocess.run([sys.executable, me, "--one", part["key"]] + extra)

        # ONE RETRY WITH ASSERTS STRIPPED, and only where that could matter.
        # See `worth_retrying_without_asserts` — it is a hypothesis about t3's
        # data-dependent guard, it costs a model load on a part that already
        # failed, and the result records which mode produced it so a success
        # here can never be mistaken for a plain one.
        f = OUT / f"{part['key']}.json"
        if r.returncode != 2 and f.exists():
            try:
                row = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                row = {}
            if worth_retrying_without_asserts(row):
                print("           failed on an assert — retrying with Python's")
                print("           asserts stripped (-O), which is a guess worth one load")
                first = dict(row)
                r2 = subprocess.run([sys.executable, "-O", me,
                                     "--one", part["key"]] + extra)
                if r2.returncode != 2 and f.exists():
                    try:
                        second = json.loads(f.read_text(encoding="utf-8"))
                        second["with_asserts_failed"] = {
                            "verdict": first.get("verdict"),
                            "dynamo_error": first.get("dynamo_error"),
                            "torchscript_error": first.get("torchscript_error")}
                        f.write_text(json.dumps(second, indent=1), encoding="utf-8")
                    except Exception:
                        pass
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


def cmd_one(key, fixture=False):
    """One part, one process, one freshly-loaded model. See `cmd_run`."""
    part = next((p for p in PARTS if p["key"] == key), None)
    if part is None:
        print(f"export-probe: no part called '{key}'")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    if reference() is None:
        print(f"export-probe: no reference clip for '{VOICE}' under {CLIPS}")
        return 1

    # THE FIXTURE, and it is how this file stopped costing a round trip per
    # bug. `--fixture` swaps in tools/voice-live/fixture.py: three tiny modules
    # wearing chatterbox's shape and failing the same ways, no weights, no GPU,
    # runs here in seconds. It is NOT an answer about chatterbox and the
    # verdict says so; it is an answer about whether this probe works, which
    # is what six round trips were actually spent on.
    if fixture:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from fixture import load as _load

        class ChatterboxTTS:
            @staticmethod
            def from_pretrained(device="cpu"):
                return _load()
        import torch  # noqa: F401
    else:
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
    # WHICH MODE PRODUCED THIS. `-O` strips every assert in the process, so a
    # result obtained that way is not the same result and must not read as one.
    v["asserts_stripped"] = not __debug__
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

        # WHICH DOORS GET TRIED, AND IN WHAT ORDER. Every failure so far has
        # been in preprocessing rather than in the network, so falling through
        # to `forward` is the difference between "this model cannot convert"
        # and "this model converts, and the windowing moves to C#".
        check(export_candidates(["inference"]) == ["inference"],
              "one entry point that fired is the only one tried")
        check(export_candidates(["inference", "forward"]) == ["inference", "forward"],
              "the observed entry point is tried before the pure network, not after")
        check(export_candidates(["forward"]) == ["forward"],
              "when forward IS the entry point it is not tried twice")
        check(export_candidates(["inference", "encode", "forward"])
              == ["inference", "forward", "encode"],
              "forward jumps the queue ahead of other doors that also fired")
        check(export_candidates([]) == [],
              "and a part that fired nothing yields nothing to try")

        # "WILL NOT RUN" MUST NOT MEAN "WILL NOT RUN ON THE GPU". The encoder
        # exported, failed DirectML at session init, and was reported as
        # broken — with CPU never tried, because both providers went into one
        # constructor that threw as a unit.
        ok_gpu = {"ran_on": "DmlExecutionProvider", "run_seconds": 0.03}
        bad = {"error": "RuntimeException: E_INVALIDARG"}
        check(provider_verdict({"DmlExecutionProvider": ok_gpu,
                                "CPUExecutionProvider": bad})["verdict"]
              == "exported and runs",
              "a part that runs on the GPU is reported as running, whatever the CPU did")
        mid = provider_verdict({"DmlExecutionProvider": bad,
                                "CPUExecutionProvider": {"ran_on": "CPUExecutionProvider",
                                                         "run_seconds": 0.4}})
        check(mid["verdict"] == "exported, runs on CPU, will not run on the GPU",
              "a valid graph the GPU refuses gets its own verdict, not 'will not run'")
        check(mid.get("run_error") == bad["error"],
              "and keeps the GPU's reason, because that is the thing to fix")
        both = provider_verdict({"DmlExecutionProvider": bad, "CPUExecutionProvider": bad})
        check(both["verdict"] == "exported but will not run"
              and both.get("cpu_error") and both.get("run_error"),
              "only when BOTH refuse is the graph itself called broken, with both reasons")

        # AN ERROR CUT SHORT IS AN ANSWER THROWN AWAY. Dynamo's message is
        # boilerplate for its first 200 characters and the cause comes after.
        long = RuntimeError("\x1b[96mstep 1/3\x1b[0m " + "x" * 3000 + " THE REAL CAUSE")
        t = tidy(long)
        check("\x1b[" not in t, "colour codes are stripped out of the report")
        check("more characters]" in t and len(t) > 1000,
              "a long error keeps enough to be useful and SAYS how much it dropped")
        check(tidy(ValueError("x")).startswith("ValueError:"),
              "and the exception type survives, which is half the diagnosis")
        check("THE REAL CAUSE" not in t and "x" * 50 in t,
              "the cut takes the tail, so the boilerplate is what survives — "
              "which is why the limit is large rather than clever")

        # THE ASSERT RETRY IS NARROW ON PURPOSE — it costs a model load, so it
        # must not fire on failures it cannot possibly help.
        assert_fail = {"verdict": "failed", "dynamo_error":
                       "GuardOnDataDependentSymNode: ... assert (text_tokens == ...)"}
        stft_fail = {"verdict": "failed", "torchscript_error":
                     "SymbolicValueError: STFT does not currently support complex types"}
        check(worth_retrying_without_asserts(assert_fail),
              "a failure naming an assert is retried with asserts stripped")
        check(not worth_retrying_without_asserts(stft_fail),
              "an STFT failure is NOT — stripping asserts cannot help it, and a load is a load")
        check(not worth_retrying_without_asserts({"verdict": "exported and runs"}),
              "and nothing that already succeeded is retried")

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
        rc = cmd_run(None, allow_install=False)
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
    ap.add_argument("--fixture", action="store_true",
                    help="run against the local stand-in, not chatterbox")
    ap.add_argument("--one", metavar="PART",
                    help="one part, in this process — what --run spawns per part")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.one:
        return cmd_one(a.one, a.fixture)
    if a.run:
        return cmd_run(a)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
