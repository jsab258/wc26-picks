#!/usr/bin/env python3
"""AUDIT THE EXPORTED GRAPHS FROM THE FILES ALONE, AND WRITE IT DOWN.

    python3 tools/voice-live/check-graphs.py            # needs the .onnx files
    python3 tools/voice-live/check-graphs.py --selftest  # needs nothing

TWO REASONS THIS EXISTS, AND THE SECOND IS THE REAL ONE.

The first is speed. `export-for-game.py` checks its work against pytorch,
which means loading 2 GB of weights: minutes, and a download the first time.
The two faults worth catching need neither. "Is the speaker baked into the
graph" is answered by running the graph twice with two different voices and
seeing whether the answers differ — no reference model, no download, seconds.
Same for the position. A baked input is a CONSTANT, and a constant cannot
disagree with itself.

The second is that the export's answer reached me by being copied out of a
console window by hand, and the first time it mattered it did not arrive. That
is rule 12: a blocked channel is not an inconvenience to work around, it is
the bug. So this writes `game-design/voice-live/export-report.txt`, which is
tracked, committed by the bat that runs it, and still there tomorrow.

WHAT IT CANNOT ANSWER. Agreement with the original needs the original, so that
stays in `export-for-game.py`. This is the cheap half, and the cheap half is
the one that had no answer at all.

THE REJECTING CASE IS BUILDABLE, WHICH IS RARE AND WORTH IT. A baked voice is
not hypothetical here: handing `prepare_conditioning` a cond it has already
seen produces exactly that graph, because it caches the embedded prompt back
onto the object. `--selftest` exports one deliberately and checks this tool
calls it — and exports a good one and checks this tool passes it, which is the
half that usually goes unrun.
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "tools" / "voice-live" / "game-out"
CONDS = ROOT / "game-design" / "voice-conds"
REPORT = ROOT / "game-design" / "voice-live" / "export-report.txt"

# The names the game asks for. A graph that exports perfectly under different
# names is a graph the C# cannot drive, and nothing else here would notice.
PREFILL_IN = ["text_tokens", "speaker_emb", "cond_speech_tokens", "emotion_adv"]
STEP_IN = ["token", "position"]
DECODE_IN = ["tokens", "prompt_token", "prompt_feat", "embedding", "z", "sine_noise"]


ONNX_NP = {"tensor(int64)": "int64", "tensor(int32)": "int32",
           "tensor(float)": "float32", "tensor(double)": "float64",
           "tensor(float16)": "float16", "tensor(bool)": "bool"}


def audit(np, ort, step_path, prefill_path, voices, say):
    """Everything answerable from the files. Returns a list of failures."""
    bad = []

    def want(ok, what, got=""):
        say(("  ok    " if ok else "  FAIL  ") + what + (f"   [{got}]" if got else ""))
        if not ok:
            bad.append(what)

    # WHAT EACH EXPORT STEP ACTUALLY DID, before anything about the files.
    # A missing graph has two causes with opposite next moves — the step never
    # ran, or it ran and died — and the file's absence cannot tell them apart.
    for note in ("text", "decode"):
        f = step_path.parent / (note + ".stamp")
        line = (f.read_text(encoding="utf-8").strip() if f.exists()
                else "NO RECORD — this step has never been run here")
        say(f"        {note} export: {line}")
        # A RECORDED FAILURE IS A FINDING, not a line of colour. Printing it
        # and then reporting "all clear" because the older graphs happen to be
        # on disk is the shape of a green result that means nothing.
        if "FAILED" in line:
            want(False, f"the {note} export finished", line)

    for p in (step_path, prefill_path):
        mb = p.stat().st_size / (1024 * 1024) if p.exists() else 0
        # ONNX splits weights into sidecar files past 2 GB, so the graph on
        # its own can be small while the export is whole. Count the folder.
        side = sum(f.stat().st_size for f in p.parent.glob(p.stem + "*")) / (1024 * 1024)
        want(p.exists(), f"{p.name} is on disk", f"{mb:.0f} MB, {side:.0f} MB with weights")
    if bad:
        return bad

    pre = ort.InferenceSession(str(prefill_path), providers=["CPUExecutionProvider"])
    stp = ort.InferenceSession(str(step_path), providers=["CPUExecutionProvider"])
    pin = [i.name for i in pre.get_inputs()]
    sin = [i.name for i in stp.get_inputs()]
    # A DEAD INPUT IS DELETED, NOT LEFT DANGLING. If part of the conditioning
    # got baked in as a constant, the tensor that fed it stops being read and
    # the exporter drops it from the graph entirely — so a MISSING name here
    # is not a naming slip, it is that part of the voice frozen. Named one by
    # one because "the four inputs are present" cannot say which is gone.
    for n in PREFILL_IN:
        want(n in pin, f"the prefill still takes '{n}' — it was not folded away "
             f"into a constant", ", ".join(pin))
    want(sin[:len(STEP_IN)] == STEP_IN,
         "the step takes a token and a position", ", ".join(sin[:3]))
    pout = [o.name for o in pre.get_outputs()]
    # THE PREFILL'S FIRST OUTPUT IS THE FIRST TOKEN'S ODDS, AND ITS ABSENCE IS
    # WHAT CUT THE OPENING WORDS OFF THE LINE. A prefill that returns only a
    # cache forces the caller to invent a first step by feeding the start
    # token a second time, which embeds it twice, shifts every position by one
    # and loses the token the model would have chosen. Every number this tool
    # prints agreed to six decimal places while that was happening — a missing
    # OUTPUT is not a disagreement, so nothing that compares values can see it.
    want(pout[:1] == ["logits"],
         "the prefill returns the first token's odds, not only a cache",
         ", ".join(pout[:3]))
    if bad:
        return bad
    n_cache = len(pout) - 1
    want(n_cache == len(sin) - 2 and n_cache == len(stp.get_outputs()) - 1,
         f"and its {n_cache} cache outputs are exactly the step's cache inputs",
         f"prefill out {n_cache}, step in {len(sin) - 2}, step out {len(stp.get_outputs()) - 1}")
    if bad:
        return bad

    # ASK THE GRAPH WHAT IT TAKES. `text_to_tokens` returns an `IntTensor`, so
    # the real prefill declares int32 — while the selftest built its own with
    # `torch.randint`, which is int64, and passed happily. Fifth time a
    # stand-in has agreed with me instead of with reality, and the fix is the
    # same every time: read it off the thing rather than assume it.
    dt = {i.name: ONNX_NP.get(i.type) for i in list(pre.get_inputs()) + list(stp.get_inputs())}
    unknown = sorted(n for n, t in dt.items() if t is None)
    want(not unknown, "every input has a type this tool knows how to feed",
         ", ".join(f"{n}:{i.type}" for i in pre.get_inputs() for n in [i.name]
                   if n in unknown))
    if bad:
        return bad
    say("        types: " + "  ".join(f"{i.name}={i.type}" for i in pre.get_inputs())
        + f"  |  token={dt['token']}, position={dt['position']}")

    def cast(name, v):
        return np.asarray(v).astype(dt[name], copy=False)

    text = cast("text_tokens", [[10, 20, 30, 40, 50, 60]])

    def prefill(v):
        return pre.run(None, {"text_tokens": text,
                              "speaker_emb": cast("speaker_emb", v["speaker_emb"]),
                              "cond_speech_tokens": cast("cond_speech_tokens",
                                                         v["cond_speech_tokens"]),
                              "emotion_adv": cast("emotion_adv", v["emotion_adv"])})

    # A DENOMINATOR ON THE VOICE CHECK. "The voices differ" from one voice is
    # not a result, it is an empty loop reading as a pass.
    want(len(voices) >= 2, f"{len(voices)} voices available to compare",
         ", ".join(n for n, _ in voices[:4]) + ("..." if len(voices) > 4 else ""))
    if bad:
        return bad

    (n0, v0), (n1, v1) = voices[0], voices[1]
    p0 = prefill(v0)
    c0 = p0[1:]                       # the cache; p0[0] is the first odds
    repeat = max(float(np.abs(a - b).max()) for a, b in zip(p0, prefill(v0)))

    # ONE FIELD AT A TIME, WHICH IS THE WHOLE POINT. Swapping two voices
    # wholesale moves three fields together, so the cache moving proves only
    # that SOMETHING is live. The real fault is narrower than that: a cached
    # prompt embedding freezes the prompt while the speaker vector stays an
    # input, and a whole-voice comparison would pass that graph happily. Two
    # numbers that can only move together are one number twice.
    # `emotion_adv` is NUDGED rather than swapped, because every shipped voice
    # carries the same 0.5 — swapping it moves nothing and would read as a
    # baked input. A test that cannot tell "frozen" from "identical on both
    # sides" is measuring the fixture, not the graph.
    alt = {"speaker_emb": v1["speaker_emb"],
           "cond_speech_tokens": v1["cond_speech_tokens"],
           "emotion_adv": v0["emotion_adv"] + np.float32(0.25)}
    moves = {}
    for field in PREFILL_IN[1:]:
        if field not in pin:
            continue                      # already reported above
        mixed = dict(v0)
        mixed[field] = alt[field]
        moves[field] = max(float(np.abs(a - b).max())
                           for a, b in zip(p0, prefill(mixed)))
    say(f"        voices: {n0} -> {n1} one field at a time (emotion nudged) — "
        + "  ".join(f"{k}={v:.3f}" for k, v in moves.items())
        + f";  {n0} twice differs by {repeat:.1e}")
    for field, m in moves.items():
        want(m > 1e-3, f"changing '{field}' alone changes the cache — that part "
             f"of the voice is an input, not baked in", f"{m:.4f}")
    want(repeat < 1e-6, "and the same voice twice gives the same cache",
         f"{repeat:.1e}")
    want(all(np.isfinite(a).all() for a in p0), "with no infinities or NaNs in it")

    # THE POSITION, THE SAME WAY. Traced as a Python int it becomes a constant
    # and every word after the first sits at the wrong place in the sentence.
    tok = cast("token", [[7]])
    feed = {f"cache{i}": c for i, c in enumerate(c0)}
    feed["token"] = tok
    at = {}
    for p in (1, 2, 17):
        feed["position"] = cast("position", p)
        at[p] = stp.run(None, feed)[0]
    moved = max(float(np.abs(at[1] - at[p]).max()) for p in (2, 17))
    say(f"        position: 1 vs 2 and 17 move the answer by {moved:.3f}")
    want(moved > 1e-4, "the position changes the answer — it is an input, not "
         "baked into the graph", f"{moved:.4f}")
    # AND THE TWO SETS OF ODDS ARE THE SAME SHAPE. The game samples the first
    # token from the prefill and every later one from the step, with one array
    # and one sampler; a prefill whose head is a different width would be a
    # buffer overrun on the very first word.
    want(p0[0].shape[-1] == at[1].shape[-1],
         "and the prefill's odds are the same width as the step's — one array "
         "feeds one sampler", f"prefill {p0[0].shape[-1]}, step {at[1].shape[-1]}")

    # AND THEY HAVE TO JOIN. Both graphs can be perfect and still not chain;
    # that seam is where this project keeps finding the missing line.
    live, grew = c0, []
    for p in (1, 2, 3):
        f2 = {f"cache{i}": c for i, c in enumerate(live)}
        f2["token"], f2["position"] = tok, cast("position", p)
        got = stp.run(None, f2)
        live = got[1:]
        grew.append(live[0].shape[2])
    want(grew == [c0[0].shape[2] + i + 1 for i in range(3)],
         f"the prefill's cache drives the step three times, growing by one each",
         f"{c0[0].shape[2]} -> {grew}")
    want(np.isfinite(at[1]).all(), "and the answer it gives is a number")

    # ---- THE DECODE GRAPH, sound tokens into a waveform ------------------
    dec_path = step_path.parent / "s3gen-decode.onnx"
    if not dec_path.exists():
        want(False, f"{dec_path.name} is on disk — the decode graph was not "
             f"exported, so nothing turns tokens into audio yet")
        return bad
    dec = ort.InferenceSession(str(dec_path), providers=["CPUExecutionProvider"])
    din = [i.name for i in dec.get_inputs()]
    for n in DECODE_IN:
        want(n in din, f"the decode graph still takes '{n}'", ", ".join(din))
    if bad:
        return bad
    ddt = {i.name: ONNX_NP.get(i.type) for i in dec.get_inputs()}

    def decode(v, n_tok, seed):
        p = v["gen_prompt_token"].shape[1]
        pm = v["gen_prompt_feat"].shape[1]
        h = 2 * (p + n_tok)
        r = np.random.default_rng(seed)
        feed = {"tokens": r.integers(0, 6561, (1, n_tok)).astype(ddt["tokens"]),
                "prompt_token": v["gen_prompt_token"].astype(ddt["prompt_token"]),
                "prompt_feat": v["gen_prompt_feat"].astype(ddt["prompt_feat"]),
                "embedding": v["gen_embedding"].astype(ddt["embedding"]),
                "z": r.standard_normal((1, 80, h)).astype(ddt["z"]),
                "sine_noise": r.standard_normal(
                    (1, 9, (h - pm) * 480)).astype(ddt["sine_noise"])}
        return dec.run(None, feed)[0], (h - pm) * 480

    # THE LENGTHS ARE THE WHOLE QUESTION HERE. Four separate places in this
    # path turned the sentence length into a constant, so a decode graph that
    # runs at one length and refuses another is the expected failure, not an
    # exotic one. Two token counts and two voices, which vary the prompt too.
    lens = {}
    for name, v in voices[:2]:
        for n_tok in (6, 15):
            wav, expect = decode(v, n_tok, 4)
            lens[(name, n_tok)] = (wav.shape[-1], expect)
    say("        decode: " + "  ".join(
        f"{n}/{t}tok={got}smp" for (n, t), (got, _) in lens.items()))
    want(all(got == expect for got, expect in lens.values()),
         "the decode graph runs at two token counts and two voices, and the "
         "sample count follows the formula each time",
         "; ".join(f"{k}: got {g} want {w}" for k, (g, w) in lens.items()
                   if g != w))
    first = decode(voices[0][1], 6, 4)[0]
    want(np.isfinite(first).all() and float(np.abs(first).max()) > 1e-6,
         "and it produces a waveform rather than silence or NaN",
         f"peak {float(np.abs(first).max()):.4f}")
    return bad


def load_voices(np, folder, limit=3):
    out = []
    for f in sorted(folder.glob("*.npz")):
        z = np.load(f)
        if "t3.speaker_emb" not in z.files:
            continue
        out.append((f.stem, {"speaker_emb": z["t3.speaker_emb"],
                             "cond_speech_tokens": z["t3.cond_prompt_speech_tokens"],
                             "emotion_adv": z["t3.emotion_adv"],
                             "gen_prompt_token": z["gen.prompt_token"],
                             "gen_prompt_feat": z["gen.prompt_feat"],
                             "gen_embedding": z["gen.embedding"]}))
        if len(out) == limit:
            break
    return out


def cmd_run():
    import numpy as np
    import onnxruntime as ort

    lines = []

    def say(s):
        print(s)
        lines.append(s)

    # WHO RAN IT AND WHEN, ON LINE ONE. The exported graphs only exist on
    # Jafar's machine, so a report written anywhere else is a report about
    # nothing — and it would land in the same file looking identical. Same
    # fault as a build committing the stills it checked out rather than the
    # ones it rendered: the file is only evidence if it says where it came
    # from.
    import getpass
    import platform
    import socket
    from datetime import datetime, timezone
    say("LEDGER — the exported speech graphs, read from the files themselves")
    say(f"ran on {socket.gethostname()} ({platform.system()}) as "
        f"{getpass.getuser()}, {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    say(f"graphs looked for in {OUT}")
    say("")
    # A CRASH IS A RESULT AND MUST TRAVEL LIKE ONE. The first real run threw
    # on a dtype and wrote no file at all, so the whole point of this tool —
    # that its answer comes back without anyone copying it — was defeated by
    # the one outcome nobody plans for. An unhandled exception is exactly the
    # case where the report matters most, because it is the case where there
    # is nothing else to go on.
    import traceback
    voices = load_voices(np, CONDS)
    try:
        bad = audit(np, ort, OUT / "t3-step.onnx", OUT / "t3-prefill.onnx",
                    voices, say)
    except Exception as e:
        say("")
        say(f"  CRASHED  {type(e).__name__}: {e}")
        for line in traceback.format_exc().splitlines():
            say("    " + line)
        bad = [f"the check itself crashed: {type(e).__name__}"]
    say("")
    say(f"RESULT: {'all clear' if not bad else str(len(bad)) + ' PROBLEM(S)'}")
    for b in bad:
        say(f"  - {b}")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # `relative_to` RAISES rather than falling back when the path is outside
    # the repo, and it sits AFTER the write — so the report landed and the
    # tool still exited on a traceback. Found by running the crash path, which
    # is the whole argument for running it.
    try:
        where = REPORT.relative_to(ROOT)
    except ValueError:
        where = REPORT
    print(f"\n  written to {where}")
    return 1 if bad else 0


def selftest():
    try:
        import numpy as np
        import onnxruntime as ort
        import torch
        from chatterbox.models.t3.t3 import T3
        from chatterbox.models.t3.modules.t3_config import T3Config
        from chatterbox.models.t3.modules.cond_enc import T3Cond
        from chatterbox.models.t3.modules.perceiver import Perceiver
        from chatterbox.models.t3.llama_configs import LLAMA_CONFIGS
    except ImportError as e:
        print(f"check-graphs --selftest: SKIPPED — {e}")
        return 0

    import tempfile
    import warnings
    import importlib.util
    warnings.filterwarnings("ignore")
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import kv_cache
    # `export-for-game.py` has a hyphen in it, so it cannot be imported by
    # name. Loading it by path keeps the exporters in ONE place — a second
    # copy of `export_prefill` here would be the "one idea, two
    # implementations" fault this tool exists to catch.
    here = pathlib.Path(__file__).resolve().parent

    def by_path(name, fname):
        spec = importlib.util.spec_from_file_location(name, here / fname)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    efg = by_path("efg", "export-for-game.py")
    edc = by_path("edc", "export-decode.py")

    fails, ran, out = [], [], []

    def say(s):
        out.append(s)

    def check(ok, what, got=""):
        ran.append(what)
        print(("  ok    " if ok else "  FAIL  ") + what + (f"   [{got}]" if got else ""))
        if not ok:
            fails.append(what)

    tmp = pathlib.Path(tempfile.mkdtemp())
    import atexit as _ax, shutil as _sh   # same leak as export-decode's: 19.8GB of these in one evening
    _ax.register(_sh.rmtree, tmp, True)
    LLAMA_CONFIGS["Llama_520M"] = dict(LLAMA_CONFIGS["Llama_520M"])
    LLAMA_CONFIGS["Llama_520M"].update(hidden_size=64, intermediate_size=128,
                                       num_hidden_layers=2, num_attention_heads=4,
                                       num_key_value_heads=4)
    torch.manual_seed(20260808)
    t3 = T3(T3Config()).eval()
    for p in t3.parameters():
        p.requires_grad_(False)
    t3.cond_enc.perceiver = Perceiver(pre_attention_query_size=64, embedding_dim=64,
                                      num_attn_heads=2).eval()
    for p in t3.cond_enc.perceiver.parameters():
        p.requires_grad_(False)

    hp = t3.hp

    def a_voice(seed):
        g = torch.Generator().manual_seed(seed)
        return dict(speaker_emb=torch.randn(1, hp.speaker_embed_size, generator=g),
                    cond_prompt_speech_tokens=torch.randint(
                        0, 6561, (1, hp.speech_cond_prompt_len), generator=g),
                    emotion_adv=0.5 * torch.ones(1, 1, 1))

    with torch.no_grad():
        seed = t3.tfmr(inputs_embeds=torch.randn(2, 12, 64), use_cache=True,
                       return_dict=True)
    cache0 = kv_cache.cache_to_tensors(seed.past_key_values)
    efg.export_step(torch, kv_cache, t3, seed.past_key_values, cache0,
                    tmp / "t3-step.onnx")
    # INT32, BECAUSE THAT IS WHAT THE REAL ONE IS. `text_to_tokens` returns a
    # `torch.IntTensor`; this fixture used `torch.randint`, which is int64,
    # and so the graph under test took a type the shipped graph never will.
    # It passed, and the real run threw on the first line that fed it. A
    # stand-in that differs from the thing in the one respect being tested is
    # worse than no stand-in.
    efg.export_prefill(torch, kv_cache, t3, a_voice(1),
                       torch.randint(0, 100, (1, 9), dtype=torch.int32),
                       tmp / "t3-prefill.onnx", len(cache0))
    efg.export_prefill(torch, kv_cache, t3, a_voice(1),
                       torch.randint(0, 100, (1, 9), dtype=torch.int64),
                       tmp / "wide.onnx", len(cache0))

    # A DECODE GRAPH TOO, from the same exporter the real run uses. Building
    # a second one here would be the "one idea, two implementations" fault
    # this file exists to catch, committed by the file itself.
    from stft_patch import patched
    flow_s, gen_s = edc.build_small(torch)
    PT, NT = 5, 7
    ptok = torch.randint(0, 6561, (1, PT))
    pfeat = torch.randn(1, edc.MELS_PER_TOKEN * PT, 80)
    with patched(), edc.dynamic_cfm(torch), edc.dynamic_flow(torch):
        edc.export_decode(torch, flow_s, gen_s,
                          (torch.randint(0, 6561, (1, NT)), ptok, pfeat,
                           torch.randn(1, 192))
                          + tuple(edc.draw(torch, PT, edc.MELS_PER_TOKEN * PT, NT, 2)),
                          tmp / "s3gen-decode.onnx")

    def a_gen(i):
        g = torch.Generator().manual_seed(100 + i)
        n = PT + i                       # a different prompt length per voice
        return {"gen_prompt_token": torch.randint(0, 6561, (1, n), generator=g).numpy(),
                "gen_prompt_feat": torch.randn(1, edc.MELS_PER_TOKEN * n, 80,
                                               generator=g).numpy(),
                "gen_embedding": torch.randn(1, 192, generator=g).numpy()}

    voices = [(f"v{i}", {"speaker_emb": a_voice(i)["speaker_emb"].numpy(),
                         "cond_speech_tokens": a_voice(i)["cond_prompt_speech_tokens"].numpy(),
                         "emotion_adv": a_voice(i)["emotion_adv"].numpy(),
                         **a_gen(i)})
              for i in (1, 2, 3)]

    # THE ACCEPTING CASE FIRST, because the expensive failure is a check
    # nothing survives — and that half is the one that goes unrun.
    bad = audit(np, ort, tmp / "t3-step.onnx", tmp / "t3-prefill.onnx", voices, say)
    for line in out:
        if line.strip().startswith(("voices:", "position:")):
            print("      " + line.strip())
    check(not bad, "a correctly exported pair passes the audit (int32 text, as "
          "the real tokeniser emits)", "; ".join(bad) if bad else "")

    out.clear()
    badw = audit(np, ort, tmp / "t3-step.onnx", tmp / "wide.onnx", voices, say)
    check(not badw, "and one taking int64 text passes too — the tool reads the "
          "type off the graph rather than assuming one",
          "; ".join(badw) if badw else "")

    # AND THE REJECTING CASE, WHICH IS BUILDABLE HERE. Handing
    # `prepare_conditioning` a cond it has already seen leaves the embedded
    # prompt cached on it, and tracing then bakes that speaker in.
    used = T3Cond(**a_voice(1), cond_prompt_speech_emb=None)
    with torch.no_grad():
        t3.prepare_conditioning(used)          # populates cond_prompt_speech_emb
    assert used.cond_prompt_speech_emb is not None

    class Baked(torch.nn.Module):
        def forward(self, text_tokens, speaker_emb, cond_speech_tokens, emotion_adv):
            tt = torch.nn.functional.pad(text_tokens, (1, 0), value=hp.start_text_token)
            tt = torch.nn.functional.pad(tt, (0, 1), value=hp.stop_text_token)
            tt = torch.cat([tt, tt], dim=0)
            embeds, _ = t3.prepare_input_embeds(
                t3_cond=used, text_tokens=tt,
                speech_tokens=hp.start_speech_token * torch.ones_like(tt[:, :1]),
                cfg_weight=0.5)
            o = t3.tfmr(inputs_embeds=embeds, use_cache=True, return_dict=True)
            # THE LOGITS ARE HERE ON PURPOSE, in a graph whose fault is the
            # baked voice. A fixture missing them too would be rejected for
            # the wrong reason and this check would stop testing what it says
            # it tests — the rejecting case has to be wrong in exactly one way.
            head = t3.speech_head(o.last_hidden_state[:, -1:])
            return (head,) + tuple(kv_cache.cache_to_tensors(o.past_key_values))

    names = PREFILL_IN
    args = (torch.randint(0, 100, (1, 9)), used.speaker_emb,
            used.cond_prompt_speech_tokens, used.emotion_adv)
    with torch.no_grad():
        torch.onnx.export(Baked().eval(), args, str(tmp / "baked.onnx"),
                          opset_version=17, dynamo=False, input_names=names,
                          output_names=["logits"]
                          + [f"cache{i}" for i in range(len(cache0))],
                          dynamic_axes={"text_tokens": {1: "text"},
                                        "cond_speech_tokens": {1: "prompt"}})
    out.clear()
    bad2 = audit(np, ort, tmp / "t3-step.onnx", tmp / "baked.onnx", voices, say)
    # AND IT IS CAUGHT BY THE MISSING INPUT, which is what a baked prompt
    # actually looks like: the tensor stops being read and the exporter
    # deletes it. The whole-voice comparison I wrote first would have PASSED
    # this graph, because `speaker_emb` is still live and still moves the
    # cache — three fields confounded into one number, the fault rule 2 is
    # about, found by running the rejecting case rather than by reasoning.
    check(any("cond_speech_tokens" in b for b in bad2),
          "and a graph with the voice prompt baked in is CAUGHT — the check can fail",
          "; ".join(bad2) if bad2 else "nothing flagged")

    # AND THE GRAPH THAT ACTUALLY SHIPPED, which is what the odds check was
    # added for: a prefill returning only its cache. It passed every check in
    # this file for four days on six decimal places of agreement, and Jafar
    # heard the fault in two seconds — the line began at "van again" instead
    # of "Seen the van again". The body comes from the ONE exporter, so this
    # fixture differs from the good graph in exactly the output that matters.
    good = efg.make_prefill(torch, kv_cache, t3).eval()

    class CacheOnly(torch.nn.Module):
        def forward(self, text_tokens, speaker_emb, cond_speech_tokens, emotion_adv):
            return good(text_tokens, speaker_emb, cond_speech_tokens,
                        emotion_adv)[1:]

    with torch.no_grad():
        torch.onnx.export(
            CacheOnly().eval(),
            (torch.randint(0, 100, (1, 9), dtype=torch.int32),
             *[a_voice(1)[k] for k in ("speaker_emb", "cond_prompt_speech_tokens",
                                       "emotion_adv")]),
            str(tmp / "cacheonly.onnx"), opset_version=17, dynamo=False,
            input_names=PREFILL_IN,
            output_names=[f"cache{i}" for i in range(len(cache0))],
            dynamic_axes={"text_tokens": {1: "text"},
                          "cond_speech_tokens": {1: "prompt"}})
    out.clear()
    bad5 = audit(np, ort, tmp / "t3-step.onnx", tmp / "cacheonly.onnx", voices, say)
    check(any("first token's odds" in b for b in bad5),
          "and a prefill that returns only a cache is CAUGHT — the graph that "
          "cut the opening words off the line",
          "; ".join(bad5) if bad5 else "nothing flagged")

    # A ONE-VOICE FOLDER MUST NOT READ AS CLEAN. An empty comparison passes
    # every test in it, which is rule 3b: a zero needs a denominator.
    out.clear()
    bad3 = audit(np, ort, tmp / "t3-step.onnx", tmp / "t3-prefill.onnx", voices[:1], say)
    check(any("voices available" in b for b in bad3),
          "and one voice is reported as too few to compare, not as a pass",
          "; ".join(bad3) if bad3 else "nothing flagged")

    # AND A MISSING FILE IS A NAMED FAILURE, not a traceback.
    out.clear()
    bad4 = audit(np, ort, tmp / "t3-step.onnx", tmp / "nope.onnx", voices, say)
    check(any("nope.onnx" in b for b in bad4),
          "and a missing graph is named rather than thrown",
          "; ".join(bad4) if bad4 else "nothing flagged")

    # AND THE CRASH PATH, RUN RATHER THAN REASONED ABOUT. The first real run
    # threw on a dtype and wrote nothing, which defeated the one thing this
    # tool is for. A handler nobody has watched work is a handler.
    def boom(*a, **k):
        raise RuntimeError("deliberate")

    crash = tmp / "crash-report.txt"
    keep_audit, keep_report = globals()["audit"], globals()["REPORT"]
    try:
        globals()["audit"], globals()["REPORT"] = boom, crash
        rc = cmd_run()
    finally:
        globals()["audit"], globals()["REPORT"] = keep_audit, keep_report
    wrote = crash.read_text(encoding="utf-8") if crash.exists() else ""
    check(rc != 0 and "deliberate" in wrote and "CRASHED" in wrote,
          "and when the check itself throws, the report is still written and "
          "names the throw", f"rc={rc}, {len(wrote)} bytes")

    print(f"\ncheck-graphs --selftest: "
          f"{'PASS' if not fails else str(len(fails)) + ' FAILED'} — {len(ran)} checks, "
          f"both the accepting and the rejecting case")
    return 1 if fails else 0


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
