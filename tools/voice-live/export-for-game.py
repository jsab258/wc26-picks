#!/usr/bin/env python3
"""EXPORT THE GRAPH THE GAME NEEDS, WHICH IS NOT THE ONE THE PROBE MADE.

    python3 tools/voice-live/export-for-game.py            # needs the weights
    python3 tools/voice-live/export-for-game.py --selftest  # needs nothing

WHY THIS IS A SECOND EXPORTER.

`export_probe.py` answered "can this model be converted at all". It took each
network apart, tried every door, and succeeded: the transformer converts and
agrees to 6.5e-07. That question is closed and this does not reopen it.

This answers a different one: WHAT SHAPE MUST THE GRAPH BE FOR THE GAME TO
DRIVE IT. The probe's t3 graph takes `inputs_embeds` — the EMBEDDING of a
token, not the token. Turning one into the other is

    speech_emb(token) + speech_pos_emb.get_fixed_embedding(position)

two lookup tables that live in the model and are NOT in the exported graph. So
the game would have to ship them, about 50 MB, and reimplement the lookup —
which is the class of thing this project has already been burned by twice: a
sampler and a tokeniser, each reimplemented, each producing perfectly
plausible speech when subtly wrong.

FOUND BY TRYING TO WRITE THE BACKEND, and only then. Everything else was in
place — the loop, the sampler, the tokeniser, the queue, the worker, the frame
pump — and the one method that hands a token to the model could not be
written, because the model does not take one. A missing INPUT is invisible in
a report that says "exported and runs, agrees to 6.5e-07", and it was.

So the graph takes a token and a position, does the embedding inside where the
weights already are, and the game hands over two integers.

CHECKED HERE, WITHOUT THE WEIGHTS. `--selftest` builds a REAL `T3` with a
tiny Llama in place of the 520M one: same class, same wiring, same awkward
operations, 6M parameters instead of 520M. Conversion does not care about the
size of a weight, so this is the whole question minus the download — the same
trick that caught the cache-assembly bug against a real `LlamaModel` and
proved the vocoder against a real `HiFTGenerator`.

AND IT CHECKS THE POSITION AT SEVERAL VALUES, which is the fault that would
otherwise ship silently. A position passed as a Python int becomes a constant
in the graph: it exports, it runs, it agrees perfectly at the position it was
traced with, and every token after the first is embedded at the wrong place in
the sentence. Passed as a tensor it stays an input — and the only way to know
which happened is to run it at a position it was not traced at.
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "tools" / "voice-live" / "game-out"
VOICE = "rocco"
LINE = "Seen the van again. Thursday, same as last Thursday."


def make_step(torch, kv_cache, model, like):
    """One step of the text stage, as the game will drive it.

    `like` is a real cache to rebuild against — the layer count, head count
    and head width all come from the model, and a cache invented here would
    have the wrong ones.
    """

    class Step(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.m = model
            self._like = like

        def forward(self, token, position, *cache):
            # THE EMBEDDING HAPPENS HERE, inside the graph, against the
            # model's own tables. This is the whole reason the file exists.
            e = self.m.speech_emb(token) + self.m.speech_pos_emb.get_fixed_embedding(position)
            # TWO ROWS, WHICH IS THE GUIDANCE. `SpeechLoop.Guided` combines
            # them on the C# side, out in the open where it is testable
            # without a GPU.
            e = torch.cat([e, e])
            past = kv_cache.tensors_to_cache(list(cache), self._like)
            out = self.m.tfmr(inputs_embeds=e, past_key_values=past,
                              use_cache=True, return_dict=True)
            head = self.m.speech_head(out.last_hidden_state)
            return (head,) + tuple(kv_cache.cache_to_tensors(out.past_key_values))

    return Step()


def export_step(torch, kv_cache, model, like, cache0, dest):
    """Trace it, and name every input so the C# can ask for them by name."""
    step = make_step(torch, kv_cache, model, like).eval()
    tok = torch.tensor([[7]], dtype=torch.long)
    pos = torch.tensor(3)
    args = (tok, pos) + tuple(cache0)
    names = ["token", "position"] + [f"cache{i}" for i in range(len(cache0))]
    outs = ["logits"] + [f"newcache{i}" for i in range(len(cache0))]
    # THE CACHE'S TIME AXIS IS DYNAMIC. It grows by one every step, so a graph
    # frozen at one length is a graph that can say one word.
    axes = {n: {0: "batch", 2: "past"} for n in names[2:]}
    with torch.no_grad():
        torch.onnx.export(step, args, str(dest), opset_version=17, dynamo=False,
                          input_names=names, output_names=outs, dynamic_axes=axes)
    return step, args, names


def selftest():
    fails, ran = [], []

    def check(ok, what, got=""):
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}" + ("" if ok else f" — {got}"))
        ran.append(what)
        if not ok:
            fails.append(what)

    try:
        import numpy as np
        import torch
        import onnxruntime as ort
        from chatterbox.models.t3.llama_configs import LLAMA_CONFIGS
        from chatterbox.models.t3.modules.t3_config import T3Config
        from chatterbox.models.t3.t3 import T3
    except ImportError as e:
        # A DENOMINATOR ON THE SKIP. "chatterbox is not installed" and "the
        # graph is the right shape" must not print the same way.
        print(f"  skipped: {e} — 0 of 7 checks run, nothing was exported")
        print("\nexport-for-game --selftest: SKIPPED — 0 checks")
        return 0

    import pathlib as _p
    import tempfile
    sys.path.insert(0, str(_p.Path(__file__).resolve().parent))
    import kv_cache

    tmp = _p.Path(tempfile.mkdtemp())

    # A REAL T3 WITH A TINY LLAMA. Same class, same wiring, same operations;
    # 6M parameters instead of 520M, and conversion does not care about the
    # size of a weight.
    LLAMA_CONFIGS["Llama_520M"] = dict(LLAMA_CONFIGS["Llama_520M"])
    LLAMA_CONFIGS["Llama_520M"].update(hidden_size=64, intermediate_size=128,
                                       num_hidden_layers=2, num_attention_heads=4,
                                       num_key_value_heads=4)
    torch.manual_seed(20260807)
    t3 = T3(T3Config()).eval()
    for p in t3.parameters():
        p.requires_grad_(False)
    check(t3.speech_emb.weight.shape[0] == 8194,
          "a real T3 builds with the shipped vocabulary width",
          str(tuple(t3.speech_emb.weight.shape)))

    with torch.no_grad():
        seed = t3.tfmr(inputs_embeds=torch.randn(2, 12, 64), use_cache=True,
                       return_dict=True)
    cache0 = kv_cache.cache_to_tensors(seed.past_key_values)
    check(len(cache0) == 4 and cache0[0].shape[0] == 2,
          f"and a cache of {len(cache0)} tensors, two rows wide for the guidance",
          str(tuple(cache0[0].shape)))

    step, args, names = export_step(torch, kv_cache, t3, seed.past_key_values,
                                    cache0, tmp / "t3step.onnx")
    check((tmp / "t3step.onnx").exists(), "the step graph exports")

    with torch.no_grad():
        ref = step(*args)
    sess = ort.InferenceSession(str(tmp / "t3step.onnx"),
                                providers=["CPUExecutionProvider"])
    feeds = {"token": args[0].numpy(), "position": args[1].numpy()}
    feeds.update({f"cache{i}": t.numpy() for i, t in enumerate(cache0)})
    got = sess.run(None, feeds)
    rel = float(np.abs(ref[0].numpy() - got[0]).max()) \
        / max(float(np.abs(ref[0].numpy()).max()), 1e-12)
    check(rel < 1e-4, f"and agrees with pytorch to {rel:.1e}", f"{rel:.2e}")
    check(len(got) == 1 + len(cache0),
          f"returning the head plus {len(cache0)} updated cache tensors",
          str(len(got)))
    check(got[1].shape[2] == cache0[0].shape[2] + 1,
          "whose sequence has grown by the one token just processed")

    # THE CHECK THAT MATTERS MOST. A position passed as a Python int becomes a
    # CONSTANT: the graph exports, runs, and agrees perfectly at the position
    # it was traced with, while every later token is embedded at the wrong
    # place in the sentence. Only a position it was NOT traced at can tell.
    series = {}
    for p in (0, 1, 9, 40):
        with torch.no_grad():
            want = step(args[0], torch.tensor(p), *cache0)[0].numpy()
        alt = dict(feeds)
        alt["position"] = np.array(p, dtype=np.int64)
        series[p] = float(np.abs(want - sess.run(None, alt)[0]).max()) \
            / max(float(np.abs(want).max()), 1e-12)
    print("        series: traced(3)=%.1e  " % rel
          + "  ".join(f"{p}={v:.1e}" for p, v in series.items()))
    check(max(series.values()) < 1e-4,
          f"and at four positions it was NOT traced at, worst "
          f"{max(series.values()):.1e} — so the position is an input and not a "
          f"constant", f"{max(series.values()):.2e}")

    print(f"\nexport-for-game --selftest: "
          f"{'PASS' if not fails else str(len(fails)) + ' FAILED'} — {len(ran)} checks "
          f"against a real T3")
    return 1 if fails else 0


def cmd_run():
    import time
    import numpy as np
    import torch
    from chatterbox.tts import ChatterboxTTS

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import export_probe
    import kv_cache
    import speak

    note = export_probe.diagnose_watermarker()
    if note:
        print(f"  watermarker: {note} (not used here)")
    ref = export_probe.reference(VOICE)
    if ref is None:
        print(f"  no reference clip for '{VOICE}'")
        return 1

    print(f"  voice: {VOICE} ({ref.name})")
    print("  loading the model...")
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxTTS.from_pretrained(device=dev)
    model.prepare_conditionals(str(ref))
    OUT.mkdir(parents=True, exist_ok=True)

    # A REAL CACHE, FROM A REAL LINE. Its layer count, head count and head
    # width all come from the model; one invented here would have none of them
    # right, and the graph would be shaped for a model that does not exist.
    print("  running one line to shape the graph against a real cache...")
    with torch.inference_mode():
        tt = model.tokenizer.text_to_tokens(LINE).to(model.device)
        tt = torch.cat([tt, tt], dim=0)
        import torch.nn.functional as F
        hp = model.t3.hp
        tt = F.pad(tt, (1, 0), value=hp.start_text_token)
        tt = F.pad(tt, (0, 1), value=hp.stop_text_token)
        embeds, _ = model.t3.prepare_input_embeds(
            t3_cond=model.conds.t3, text_tokens=tt,
            speech_tokens=hp.start_speech_token * torch.ones_like(tt[:, :1]),
            cfg_weight=0.5)
        primed = model.t3.tfmr(inputs_embeds=embeds, use_cache=True, return_dict=True)
    cache0 = kv_cache.cache_to_tensors(primed.past_key_values)
    print(f"    cache: {len(cache0)} tensors, {tuple(cache0[0].shape)}")

    t0 = time.time()
    dest = OUT / "t3-step.onnx"
    step, args, names = export_step(torch, kv_cache, model.t3,
                                    primed.past_key_values, cache0, dest)
    mb = sum(f.stat().st_size for f in OUT.glob("t3-step*")) / (1024 * 1024)
    print(f"  exported in {time.time() - t0:.0f}s, {mb:.0f} MB -> {dest.name}")

    # RUN IT, AND AT A POSITION IT WAS NOT TRACED AT. Same check the selftest
    # makes against a small model, made here against the real one, because a
    # baked position is the fault this whole file exists to avoid.
    import onnxruntime as ort
    sess = ort.InferenceSession(str(dest), providers=["CPUExecutionProvider"])
    with torch.no_grad():
        want = step(*args)[0].numpy()
    feeds = {"token": args[0].numpy(), "position": args[1].numpy()}
    feeds.update({f"cache{i}": t.numpy() for i, t in enumerate(cache0)})
    rel = float(np.abs(want - sess.run(None, feeds)[0]).max()) \
        / max(float(np.abs(want).max()), 1e-12)
    print(f"  agrees with pytorch to {rel:.1e} at the traced position")
    worst = 0.0
    for p in (0, 1, 9, 40):
        with torch.no_grad():
            w2 = step(args[0], torch.tensor(p), *cache0)[0].numpy()
        alt = dict(feeds)
        alt["position"] = np.array(p, dtype=np.int64)
        worst = max(worst, float(np.abs(w2 - sess.run(None, alt)[0]).max())
                    / max(float(np.abs(w2).max()), 1e-12))
    print(f"  and to {worst:.1e} at four positions it was NOT traced at")
    print()
    print("  ------------------------------------------------------------")
    print("  This graph takes a TOKEN and a POSITION. The game hands over two")
    print("  integers and never touches the model's embedding tables.")
    print("  ------------------------------------------------------------")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--fromtemp", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    try:
        return cmd_run()
    except ImportError as e:
        print(f"  cannot run: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
