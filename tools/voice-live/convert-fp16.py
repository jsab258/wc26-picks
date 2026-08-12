#!/usr/bin/env python3
"""HALVE THE TEXT GRAPHS — lever B of the latency plan.

    python3 tools/voice-live/convert-fp16.py            # convert game-out's
    python3 tools/voice-live/convert-fp16.py --selftest

WHY THIS SHOULD WORK, measured rather than hoped. The step probe put a third
to a half of every step on the PCIe bus: 142us per position of fp32 cache
round-tripping between host and card. The model's own upstream weights are
BFLOAT16 — we exported at fp32, which is DOUBLE the bandwidth the model was
trained to need, on the exact axis the probe convicted. fp16 halves the
weights, the compute reads, and every byte of the cache that crosses the bus.
The RX 6700 is RDNA2, which runs fp16 at full rate.

THE CACHE CROSSES AS FP16, WHICH IS THE POINT. `keep_io_types=True` would
leave the boundary fp32 and CAST the whole cache both ways every step —
adding work to the exact place the probe said the time goes. So the I/O
becomes fp16 too, and the C# side's hot loop needs NO conversion at all: the
cache is pass-through (outputs fed back as inputs untouched), and only the
small per-line arrays (a voice's floats in, one row of logits out) convert at
the edges, where onnxruntime's own Float16 type does it.

CONVERTED FROM THE SHIPPED FP32 GRAPHS, not re-exported. The trace is the
part that has gone subtly wrong five times; the conversion is arithmetic on a
file that already agrees with the original to 1.7e-06. One step, reversible,
and the fp32 graphs stay on disk beside the halves.

WHAT DECIDES IT. Numbers here (a tiny real T3, fp16 against fp32); then
`time-a-line --fp16` on the real card for the step rate; then ears on a
five-line file, because a sampler reads RELATIVE odds and fp16 noise that
looks tiny can still reorder near-ties.
"""
import argparse
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "tools" / "voice-live" / "game-out"
GRAPHS = ("t3-prefill", "t3-step")


def convert(src, dest, say):
    import onnx
    # ONNXRUNTIME'S OWN PASS, NOT onnxconverter-common's. The first attempt
    # used the latter and it left ONE node mixed — a Div in the perceiver's
    # attention bound to fp16 on one side and fp32 on the other — so the
    # converted graph would not even load. onnxruntime ships its own fork of
    # the same converter, hardened by their LLM pipelines; the selftest is
    # what caught the difference, on a tiny real T3, in seconds instead of on
    # a 2GB file on the machine that matters.
    from onnxruntime.transformers.float16 import convert_float_to_float16

    t0 = time.time()
    # STALE OUTPUT IS DELETED FIRST, because onnx's external-data writer
    # APPENDS. The first run halved the graphs; the re-run 'converted' them
    # back to full size, because saving over an existing .data file adds the
    # new weights after the old ones instead of replacing them. The size
    # guard caught it — the doubled file read as 'did not shrink' — and this
    # is the actual repair: a job that can be re-run must own its outputs
    # from a clean slate every time.
    for stale in dest.parent.glob(dest.stem + "*"):
        stale.unlink()
    model = onnx.load(str(src))
    # keep_io_types=False ON PURPOSE — see the header. The cache boundary
    # must be fp16 or every step pays a full-cache cast in each direction.
    fp16 = convert_float_to_float16(
        model, keep_io_types=False, disable_shape_infer=True)
    onnx.save(fp16, str(dest),
              save_as_external_data=src.stat().st_size > 1_500_000_000,
              location=dest.name + ".data" if src.stat().st_size > 1_500_000_000 else None)
    a = src.stat().st_size / 1e6
    b = sum(f.stat().st_size for f in dest.parent.glob(dest.stem + "*")) / 1e6
    say(f"  {src.name}: {a:.0f} MB -> {b:.0f} MB in {time.time() - t0:.0f}s")
    return b < a * 0.75


def run(say):
    missing = [n for n in GRAPHS if not (OUT / f"{n}.onnx").exists()]
    if missing:
        say(f"  no fp32 graphs to convert: {', '.join(missing)} — run "
            f"'5 EXPORT FOR THE GAME.bat' first")
        return 1
    ok = True
    for n in GRAPHS:
        shrunk = convert(OUT / f"{n}.onnx", OUT / f"{n}-fp16.onnx", say)
        # A CONVERSION THAT DID NOT SHRINK DID NOT CONVERT. The weights are
        # ~99% of these files; a size that barely moved means the pass left
        # them fp32 and reporting success would ship the old cost under the
        # new name.
        if not shrunk:
            say(f"  {n}: the fp16 copy is not materially smaller — treating "
                f"this as a failed conversion")
            ok = False
    return 0 if ok else 1


def selftest():
    fails, ran = [], []

    def check(ok, what, got=""):
        print(("  ok    " if ok else "  FAIL  ") + what + (f"   [{got}]" if got else ""))
        ran.append(what)
        if not ok:
            fails.append(what)

    try:
        import numpy as np
        import torch
        import onnxruntime as ort
        from chatterbox.models.t3.t3 import T3
        from chatterbox.models.t3.modules.t3_config import T3Config
        from chatterbox.models.t3.modules.perceiver import Perceiver
        from chatterbox.models.t3.llama_configs import LLAMA_CONFIGS
    except ImportError as e:
        print(f"convert-fp16 --selftest: SKIPPED — {e}")
        return 0
    import importlib.util
    import tempfile
    import warnings
    warnings.filterwarnings("ignore")
    here = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    import kv_cache
    spec = importlib.util.spec_from_file_location("efg", here / "export-for-game.py")
    efg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(efg)

    tmp = pathlib.Path(tempfile.mkdtemp())
    LLAMA_CONFIGS["Llama_520M"] = dict(LLAMA_CONFIGS["Llama_520M"])
    LLAMA_CONFIGS["Llama_520M"].update(hidden_size=64, intermediate_size=128,
                                       num_hidden_layers=2, num_attention_heads=4,
                                       num_key_value_heads=4)
    torch.manual_seed(20260812)
    t3 = T3(T3Config()).eval()
    for p in t3.parameters():
        p.requires_grad_(False)
    t3.cond_enc.perceiver = Perceiver(pre_attention_query_size=64, embedding_dim=64,
                                      num_attn_heads=2).eval()
    for p in t3.cond_enc.perceiver.parameters():
        p.requires_grad_(False)
    hp = t3.hp

    voice = dict(speaker_emb=torch.randn(1, hp.speaker_embed_size),
                 cond_prompt_speech_tokens=torch.randint(0, 6561, (1, hp.speech_cond_prompt_len)),
                 emotion_adv=0.5 * torch.ones(1, 1, 1))
    with torch.no_grad():
        seed = t3.tfmr(inputs_embeds=torch.randn(2, 12, 64), use_cache=True,
                       return_dict=True)
    cache0 = kv_cache.cache_to_tensors(seed.past_key_values)
    efg.export_step(torch, kv_cache, t3, seed.past_key_values, cache0,
                    tmp / "t3-step.onnx")
    efg.export_prefill(torch, kv_cache, t3, voice,
                       torch.randint(0, 100, (1, 9), dtype=torch.int32),
                       tmp / "t3-prefill.onnx", len(cache0))

    # A STALE .data FILE FROM AN EARLIER RUN, PLANTED. onnx appends to an
    # existing external-data file rather than replacing it, which is how the
    # real re-run doubled a 1GB file back to 2GB. The selftest cannot reach
    # the external-data path itself — tiny graphs stay inline — so it asserts
    # the repair directly: stale outputs are gone after a convert.
    junk = tmp / "t3-prefill-fp16.onnx.data"
    junk.write_bytes(b"x" * 4096)

    said = []
    global OUT
    keep = OUT
    OUT = tmp
    try:
        rc = run(said.append)
    finally:
        OUT = keep
    check(rc == 0, "both tiny graphs convert and shrink",
          "; ".join(said)[-90:])
    check(not junk.exists(),
          "and a stale external-data file from an earlier run is deleted "
          "before converting — onnx APPENDS to those, which is how a re-run "
          "doubled a real graph back to full size")

    pre32 = ort.InferenceSession(str(tmp / "t3-prefill.onnx"),
                                 providers=["CPUExecutionProvider"])
    pre16 = ort.InferenceSession(str(tmp / "t3-prefill-fp16.onnx"),
                                 providers=["CPUExecutionProvider"])
    stp16 = ort.InferenceSession(str(tmp / "t3-step-fp16.onnx"),
                                 providers=["CPUExecutionProvider"])
    feed32 = {"text_tokens": np.random.randint(0, 100, (1, 9)).astype(np.int32),
              "speaker_emb": voice["speaker_emb"].numpy(),
              "cond_speech_tokens": voice["cond_prompt_speech_tokens"].numpy(),
              "emotion_adv": voice["emotion_adv"].numpy()}
    out32 = pre32.run(None, feed32)
    feed16 = dict(feed32)
    feed16["speaker_emb"] = feed32["speaker_emb"].astype(np.float16)
    feed16["emotion_adv"] = feed32["emotion_adv"].astype(np.float16)
    out16 = pre16.run(None, feed16)

    check(out16[0].dtype == np.float16 and out16[1].dtype == np.float16,
          "the fp16 prefill takes fp16 floats and gives fp16 odds and cache — "
          "the boundary converted, so the C# loop never casts",
          f"{out16[0].dtype}, {out16[1].dtype}")

    rel = float(np.abs(out16[0].astype(np.float32) - out32[0]).max()) \
        / max(float(np.abs(out32[0]).max()), 1e-9)
    check(rel < 5e-2,
          f"the first token's odds agree with fp32 to {rel:.1%} — noise, not a "
          f"different opinion", f"{rel:.3f}")

    # AND THE HALVED CACHE DRIVES THE HALVED STEP. The seam between the two
    # graphs is where every conversion fault in this project has lived.
    live = list(out16[1:])
    worst = 0.0
    live32 = list(out32[1:])
    for s in (1, 2):
        f16 = {f"cache{i}": c for i, c in enumerate(live)}
        f16["token"] = np.array([[7]], dtype=np.int64)
        f16["position"] = np.array(s, dtype=np.int64)
        got16 = stp16.run(None, f16)
        live = got16[1:]
    check(np.isfinite(got16[0].astype(np.float32)).all()
          and got16[1].shape[2] == out16[1].shape[2] + 2,
          "the fp16 prefill's cache drives the fp16 step twice, growing by one "
          "per step, with finite odds throughout",
          f"grew {out16[1].shape[2]} -> {got16[1].shape[2]}")

    print(f"\nconvert-fp16 --selftest: "
          f"{'PASS' if not fails else str(len(fails)) + ' FAILED'} — {len(ran)} checks")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    def say(s):
        print(s, flush=True)

    say("LEDGER — halving the text graphs (latency plan, lever B)")
    return run(say)


if __name__ == "__main__":
    sys.exit(main())
