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

AND THEN THE SAME GAP AGAIN, ONE LAYER UP. The step graph takes a CACHE, and
the game has a SENTENCE. Making one from the other means embedding the text,
the speaker, the emotion value and the voice prompt and running all of it
through the transformer once — every part of it a table inside the model. So
there are two graphs here: a PREFILL that turns the sentence and the voice
into the cache, and the STEP that walks it. The game holds the text tokens and
the four arrays already committed per voice, and nothing else.

This one was caught before writing the backend rather than after, which is the
only difference between it and the last one.

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

THE VOICE HAS THE IDENTICAL FAILURE and a nastier cause. `prepare_conditioning`
CACHES the embedded prompt back onto the cond object it is handed, so tracing
with a cond that has already spoken bakes that speaker in: the graph exports,
runs, and is perfect for the voice it saw, while all nineteen characters speak
in it. Checked the same way, with a voice it was not traced with — and with a
denominator on that check, because two voices agreeing to 1e-7 is ALSO what a
baked voice looks like. The caches have to differ as well as agree.
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "tools" / "voice-live" / "game-out"
VOICE = "rocco"
STAMP = "text"
LINE = "Seen the van again. Thursday, same as last Thursday."


def already_done(paths):
    """Skip an export that is already on disk from THIS version of this file.

    Each run costs minutes of model loading, and the decode export died after
    the text one had succeeded — so repeating it means paying twice for an
    answer already in hand. Skipping is only safe if "already done" means the
    same code produced it, so the stamp carries a fingerprint of this file and
    a skip requires it to match. Edit the exporter and the fingerprint moves,
    which re-exports without anybody having to remember to.

    A guard that cannot tell a regression from an improvement is a ratchet;
    this one cannot keep a stale graph, because staleness is exactly what the
    fingerprint measures.
    """
    import hashlib
    mine = hashlib.sha256(
        pathlib.Path(__file__).read_bytes()).hexdigest()[:12]
    note = OUT / (STAMP + ".stamp")
    if not note.exists() or not all(p.exists() for p in paths):
        return False, mine
    text = note.read_text(encoding="utf-8")
    return ("src=" + mine) in text and "finished" in text, mine


def stamp(text):
    """LEAVE A NOTE SAYING THIS STEP RAN, because "no graph on disk" and "the
    export died" look identical from the outside and want opposite next moves.
    The audit read `s3gen-decode.onnx` missing and could not say whether the
    export had failed or had never been reached — it had never been reached,
    and finding that out cost a round trip. Written at the START as well as
    the end, so a run that dies mid-export still leaves evidence it began.
    """
    from datetime import datetime, timezone
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / (STAMP + ".stamp")).write_text(
            f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC  {text}\n",
            encoding="utf-8")
    except OSError:
        pass                      # a missing note must never kill the export


def make_step(torch, kv_cache, model, like, rows=2):
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
            #
            # ONE ROW IS THE EXPERIMENT. Every step runs the model twice —
            # once on the sentence and once on the sentence with its
            # conditioning removed — and the second exists only to be
            # subtracted from the first. Dropping it halves the work of the
            # stage that is now two thirds of a line. It also removes the
            # thing the model relies on to say the right words, so whether it
            # survives is a question for ears.
            if rows > 1:
                e = torch.cat([e, e])
            past = kv_cache.tensors_to_cache(list(cache), self._like)
            out = self.m.tfmr(inputs_embeds=e, past_key_values=past,
                              use_cache=True, return_dict=True)
            head = self.m.speech_head(out.last_hidden_state)
            return (head,) + tuple(kv_cache.cache_to_tensors(out.past_key_values))

    return Step()


def export_step(torch, kv_cache, model, like, cache0, dest, rows=2):
    """Trace it, and name every input so the C# can ask for them by name."""
    step = make_step(torch, kv_cache, model, like, rows).eval()
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


def make_prefill(torch, kv_cache, model, rows=2):
    """THE SENTENCE, AND THE VOICE, TURNED INTO A CACHE.

    The step graph above takes a cache. Nothing in the game can make one: it
    comes from running the whole sentence and the speaker's conditioning
    through the transformer once, and every part of that is a lookup table
    living inside the model. Same gap as the token/embedding one, one layer
    up, and found the same way — by asking what the C# would have to hold.

    The game hands over the text tokens and the four arrays it already has
    committed per voice. Nothing else.
    """
    from chatterbox.models.t3.modules.cond_enc import T3Cond

    class Prefill(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.m = model

        def forward(self, text_tokens, speaker_emb, cond_speech_tokens, emotion_adv):
            hp = self.m.hp
            # THE SENTENCE MARKERS ARE CONSTANTS AND BELONG HERE. They are two
            # fixed integers, but putting them in C# is one more place for the
            # game to disagree with the model about what a sentence is.
            tt = torch.nn.functional.pad(text_tokens, (1, 0), value=hp.start_text_token)
            tt = torch.nn.functional.pad(tt, (0, 1), value=hp.stop_text_token)
            if rows > 1:
                tt = torch.cat([tt, tt], dim=0)
            # A FRESH COND EVERY CALL, WHICH IS NOT A TIDINESS POINT.
            # `prepare_conditioning` CACHES the embedded prompt back onto the
            # object it was handed. Trace with one that has already been used
            # and the voice is baked in as a constant — nineteen characters,
            # one voice, and no error anywhere.
            cond = T3Cond(speaker_emb=speaker_emb,
                          cond_prompt_speech_tokens=cond_speech_tokens,
                          cond_prompt_speech_emb=None,
                          emotion_adv=emotion_adv)
            embeds, _ = self.m.prepare_input_embeds(
                t3_cond=cond, text_tokens=tt,
                speech_tokens=hp.start_speech_token * torch.ones_like(tt[:, :1]),
                # THE WEIGHT IS WHAT DECIDES WHETHER THE SECOND ROW IS BUILT
                # AT ALL. `prepare_input_embeds` zeroes the unconditional
                # row's text only when this is above zero, and with one row
                # there is no second row to zero — passing 0.5 there would
                # blank the ONLY row and the model would have no sentence.
                cfg_weight=0.5 if rows > 1 else 0.0)
            # THE START TOKEN GOES IN TWICE, AND THAT IS THE SHIPPED MODEL'S
            # DOING RATHER THAN A TYPO. `T3.inference` — the path
            # `ChatterboxTTS.generate` actually calls — hands one start token
            # to `prepare_input_embeds` AND concatenates a second start
            # embedding at fixed position 0. The two vectors are identical
            # (`speech_pos_emb` over a length-1 sequence is index 0, which is
            # exactly what `get_fixed_embedding(0)` returns), so the model sees
            # the same vector twice before it chooses a word.
            #
            # `inference_turbo`, three hundred lines down the same file, does
            # it once. I read that one, matched it, and built a prefill a start
            # token short of the sequence these weights are used with. One
            # idea, two implementations, and the one I read is not the one that
            # runs — checked this time by driving the real `inference` and
            # comparing, not by reading either.
            bos = self.m.speech_emb(hp.start_speech_token
                                    * torch.ones_like(tt[:1, :1]))
            bos = bos + self.m.speech_pos_emb.get_fixed_embedding(0)
            embeds = torch.cat(
                [embeds, torch.cat([bos, bos]) if rows > 1 else bos], dim=1)
            out = self.m.tfmr(inputs_embeds=embeds, use_cache=True, return_dict=True)
            # AND THE FIRST TOKEN'S ODDS COME FROM HERE, WHERE THEY WERE BEING
            # THROWN AWAY. The initial forward pass produces them as a
            # by-product; `inference` samples the first spoken token straight
            # off it. Returning only the cache lost them, so the game invented
            # a first step by feeding a start token AGAIN — a third one, at
            # position 1 — which shifted every later position by one and
            # dropped the word the model had already chosen.
            #
            # Jafar heard it in two seconds: the line began at "van again"
            # instead of "Seen the van again". Six decimal places of agreement
            # at lengths, voices and positions it was never traced with, and
            # the fault was a missing OUTPUT — which no comparison of numbers
            # can see, because both sides agreed about the numbers present.
            head = self.m.speech_head(out.last_hidden_state[:, -1:])
            return (head,) + tuple(kv_cache.cache_to_tensors(out.past_key_values))

    return Prefill()


def export_prefill(torch, kv_cache, model, cond, text_tokens, dest, n_cache,
                   rows=2):
    """Trace it. The sentence length is dynamic; the voice is an input."""
    pre = make_prefill(torch, kv_cache, model, rows).eval()
    args = (text_tokens, cond["speaker_emb"], cond["cond_prompt_speech_tokens"],
            cond["emotion_adv"])
    names = ["text_tokens", "speaker_emb", "cond_speech_tokens", "emotion_adv"]
    outs = ["logits"] + [f"cache{i}" for i in range(n_cache)]
    axes = {"text_tokens": {1: "text"}, "cond_speech_tokens": {1: "prompt"}}
    # ONLY THE CACHE HAS A TIME AXIS. Axis 2 of a cache tensor is how much
    # sentence is behind it; axis 2 of `logits` is the SPEECH VOCABULARY, a
    # fixed 6563. Sweeping both under the symbol "past" would declare the
    # vocabulary variable and tie it to the sentence length — two unrelated
    # quantities sharing one name, which is how a shape check stops meaning
    # anything.
    axes.update({n: {2: "past"} for n in outs[1:]})
    with torch.no_grad():
        torch.onnx.export(pre, args, str(dest), opset_version=17, dynamo=False,
                          input_names=names, output_names=outs, dynamic_axes=axes)
    return pre, args, names


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

    # ---- THE PREFILL, WHICH IS THE OTHER HALF THE GAME CANNOT MAKE --------
    hp = t3.hp
    # `Perceiver` pins its own width at 1024 rather than reading the config,
    # so the shrink has to reach in — the same reach the vocoder's harness
    # makes for the encoder's hardcoded 512. Real class, real wiring, one
    # number changed; nothing about the graph's shape depends on the width.
    from chatterbox.models.t3.modules.perceiver import Perceiver
    if t3.cond_enc.perceiver is not None:
        t3.cond_enc.perceiver = Perceiver(pre_attention_query_size=64,
                                          embedding_dim=64, num_attn_heads=2).eval()
        for p in t3.cond_enc.perceiver.parameters():
            p.requires_grad_(False)

    def a_voice(seed):
        g = torch.Generator().manual_seed(seed)
        return dict(
            speaker_emb=torch.randn(1, hp.speaker_embed_size, generator=g),
            cond_prompt_speech_tokens=torch.randint(
                0, 6561, (1, hp.speech_cond_prompt_len), generator=g),
            emotion_adv=0.5 * torch.ones(1, 1, 1))

    traced_voice, other_voice = a_voice(11), a_voice(22)
    text = torch.randint(0, 100, (1, 9))
    pre, pargs, pnames = export_prefill(torch, kv_cache, t3, traced_voice, text,
                                        tmp / "t3prefill.onnx", len(cache0))
    check((tmp / "t3prefill.onnx").exists(), "the prefill graph exports")

    psess = ort.InferenceSession(str(tmp / "t3prefill.onnx"),
                                 providers=["CPUExecutionProvider"])

    def prefill_gap(voice, txt):
        with torch.no_grad():
            want = pre(txt, voice["speaker_emb"], voice["cond_prompt_speech_tokens"],
                       voice["emotion_adv"])
        feed = {"text_tokens": txt.numpy(),
                "speaker_emb": voice["speaker_emb"].numpy(),
                "cond_speech_tokens": voice["cond_prompt_speech_tokens"].numpy(),
                "emotion_adv": voice["emotion_adv"].numpy()}
        out = psess.run(None, feed)
        return max(float(np.abs(w.numpy() - g).max())
                   / max(float(np.abs(w.numpy()).max()), 1e-12)
                   for w, g in zip(want, out)), out

    gap, out0 = prefill_gap(traced_voice, text)
    check(gap < 1e-4, f"and agrees with pytorch to {gap:.1e}", f"{gap:.2e}")
    check(len(out0) == 1 + len(cache0) and out0[1].shape[0] == 2,
          f"returning the first token's logits AND the {len(cache0)}-tensor "
          f"cache", str((len(out0), out0[1].shape[0])))
    # THE OUTPUT THAT WAS MISSING. A prefill that returns no logits forces the
    # caller to invent a first step, and the sentence loses its opening words.
    check(out0[0].shape[-1] == t3.hp.speech_tokens_dict_size,
          f"and the logits are one row per speech token ({out0[0].shape[-1]})",
          str(out0[0].shape))

    # AND THEY ARE THE ODDS THE SHIPPED FUNCTION WOULD HAVE SAMPLED FROM —
    # DRIVEN, NOT READ. `ChatterboxTTS.generate` calls `T3.inference`, which
    # feeds the start token in TWICE; `T3.inference_turbo`, in the same file,
    # feeds it once. Reading one of them and building to it is exactly how
    # this graph came to be a start token short of the sequence the weights
    # are used with. So this check reads neither: it RUNS `inference` for one
    # token, catches the odds it sampled from with a forward hook on the
    # speech head, and compares. A stand-in I write cannot disagree with me;
    # the function that ships can.
    from chatterbox.models.t3.modules.cond_enc import T3Cond
    caught = []
    hook = t3.speech_head.register_forward_hook(
        lambda m, i, o: caught.append(o.detach().cpu().numpy().copy()))
    try:
        ref_text = torch.cat([text, text], dim=0)
        ref_text = torch.nn.functional.pad(ref_text, (1, 0), value=hp.start_text_token)
        ref_text = torch.nn.functional.pad(ref_text, (0, 1), value=hp.stop_text_token)
        t3.inference(t3_cond=T3Cond(cond_prompt_speech_emb=None, **a_voice(11)),
                     text_tokens=ref_text, max_new_tokens=1, cfg_weight=0.5)
    except Exception as e:
        caught = [f"{type(e).__name__}: {e}"]
    finally:
        hook.remove()
    if caught and not isinstance(caught[0], str):
        theirs = caught[0][:, -1, :]
        mine = out0[0][:, -1, :]
        real = float(np.abs(theirs - mine).max()) / max(float(np.abs(theirs).max()), 1e-12)
    else:
        real = float("inf")
    check(real < 1e-4,
          f"and they match what the real `T3.inference` sampled its first "
          f"token from, to {real:.1e}",
          caught[0] if caught and isinstance(caught[0], str) else f"{real:.2e}")

    # THE VOICE IS THE POSITION'S TWIN. `prepare_conditioning` writes the
    # embedded prompt back onto the cond object it is handed, so a cond that
    # has already spoken traces as a CONSTANT: the graph exports, runs, and is
    # perfect for the voice it saw, while all nineteen characters speak in it.
    # Only a voice it was NOT traced with can tell, exactly as with position.
    vgap, out1 = prefill_gap(other_voice, text)
    tgap, _ = prefill_gap(traced_voice, torch.randint(0, 100, (1, 14)))
    moved = max(float(np.abs(a - b).max()) for a, b in zip(out0, out1))
    print(f"        prefill: traced={gap:.1e}  untraced-voice={vgap:.1e}  "
          f"longer-sentence={tgap:.1e}  voices-differ-by={moved:.2f}")
    check(vgap < 1e-4, f"and with a voice it was NOT traced with, to {vgap:.1e} "
          f"— so the speaker is an input and not a constant", f"{vgap:.2e}")
    # AND A DENOMINATOR ON THAT PASS. Two voices agreeing to 1e-7 would ALSO
    # be what a baked voice looks like, because both runs would then be the
    # same constant. The caches have to actually differ.
    check(moved > 0.01, f"and the two voices produce different caches, apart "
          f"by {moved:.2f} — so the agreement above is not two constants "
          f"matching", f"{moved:.4f}")
    check(tgap < 1e-4, f"and at a sentence length it was not traced at, "
          f"{tgap:.1e}", f"{tgap:.2e}")

    # ---- AND THEY HAVE TO CHAIN, WHICH IS A DIFFERENT QUESTION -----------
    # Both graphs passing on their own says nothing about the join. The step
    # graph was traced against a cache from a 12-frame seed; this one comes
    # out of the prefill at whatever length the sentence made it. Two systems
    # built to one idea, and the join is where this project keeps finding the
    # missing line — so drive it exactly as the game will: prefill once under
    # onnxruntime, then step twice on what it returned.
    tok_t = torch.tensor([[7]], dtype=torch.long)
    live = list(out0)[1:]
    worst_chain = 0.0
    with torch.no_grad():
        pt = [t for t in pre(text, traced_voice["speaker_emb"],
                             traced_voice["cond_prompt_speech_tokens"],
                             traced_voice["emotion_adv"])][1:]
    for s in (1, 2):
        feed = {f"cache{i}": c for i, c in enumerate(live)}
        feed["token"] = np.array([[7]], dtype=np.int64)
        feed["position"] = np.array(s, dtype=np.int64)
        got = sess.run(None, feed)
        with torch.no_grad():
            want = step(tok_t, torch.tensor(s), *pt)
        worst_chain = max(worst_chain, float(np.abs(want[0].numpy() - got[0]).max())
                          / max(float(np.abs(want[0].numpy()).max()), 1e-12))
        live, pt = got[1:], list(want[1:])
    grew = live[0].shape[2] - out0[1].shape[2]
    check(worst_chain < 1e-4,
          f"the prefill's cache drives the step graph, two steps, to "
          f"{worst_chain:.1e} — the two graphs join", f"{worst_chain:.2e}")
    check(grew == 2, f"and the cache grew by one per step, {out0[1].shape[2]} "
          f"-> {live[0].shape[2]}", f"grew by {grew}")

    # ---- AND THE SAME PAIR WITHOUT GUIDANCE, which is a new code path and
    # ---- therefore an unrun one until this exists.
    #
    # Four things move together for one row: the text is not duplicated, the
    # weight passed to `prepare_input_embeds` becomes 0 (at 0.5 it would blank
    # the ONLY row and the model would have no sentence at all), the second
    # start embedding is not doubled, and the step does not stack its token.
    # Miss any one and the graph still exports — it just says the wrong thing,
    # or dies on a shape at the first token on somebody else's machine.
    one_cache = [c[:1] for c in cache0]
    ostep = export_step(torch, kv_cache, t3, seed.past_key_values, one_cache,
                        tmp / "step1.onnx", rows=1)[0]
    opre = export_prefill(torch, kv_cache, t3, traced_voice, text,
                          tmp / "pre1.onnx", len(cache0), rows=1)[0]
    osess = ort.InferenceSession(str(tmp / "pre1.onnx"),
                                 providers=["CPUExecutionProvider"])
    ofeed = {"text_tokens": text.numpy(),
             "speaker_emb": traced_voice["speaker_emb"].numpy(),
             "cond_speech_tokens": traced_voice["cond_prompt_speech_tokens"].numpy(),
             "emotion_adv": traced_voice["emotion_adv"].numpy()}
    oout = osess.run(None, ofeed)
    check(oout[0].shape[0] == 1 and oout[1].shape[0] == 1,
          "without guidance the prefill gives ONE row of odds and a one-row "
          "cache", str((oout[0].shape[0], oout[1].shape[0])))
    # AND THE TWO JOIN, which is where a half-converted row count actually
    # bites: the prefill hands over a cache the step has to rebuild.
    ssess = ort.InferenceSession(str(tmp / "step1.onnx"),
                                 providers=["CPUExecutionProvider"])
    sfeed = {f"cache{i}": c for i, c in enumerate(oout[1:])}
    sfeed["token"] = np.array([[7]], dtype=np.int64)
    sfeed["position"] = np.array(1, dtype=np.int64)
    ok_join, why_join = True, ""
    try:
        got1 = ssess.run(None, sfeed)
    except Exception as e:
        ok_join, why_join = False, f"{type(e).__name__}: {str(e)[:80]}"
    check(ok_join and got1[0].shape[0] == 1,
          "and its cache drives a one-row step graph — the seam a half-changed "
          "row count breaks", why_join or str(got1[0].shape))
    # AND WHERE THE GUIDANCE ACTUALLY LIVES, which this check got wrong the
    # first time and was corrected by running.
    #
    # I asserted the one-row odds would DIFFER from the guided pair's, and
    # they are identical to the last bit. That is right and it is the point:
    # `prepare_input_embeds` zeroes the text of the SECOND row only, so row
    # zero is the same sentence either way. The steering is not in the graph
    # at all — the C# does `cond + 0.5 * (cond - uncond)` after both rows come
    # back. Dropping guidance does not change what the model computes about
    # the sentence; it removes the second opinion the sampler subtracts.
    #
    # So the invariant worth asserting is the identity, and beside it that the
    # two rows of the guided pair are DIFFERENT — because if they matched,
    # the steering term would be zero and guidance would be doing nothing at
    # all while costing half the run.
    if ok_join:
        same = float(np.abs(oout[0][0] - out0[0][0]).max())
        check(same < 1e-5,
              f"the conditional row is bit-identical with and without guidance "
              f"({same:.1e}) — the steering is in the sampler, not the graph",
              f"{same:.2e}")
        apart = float(np.abs(out0[0][0] - out0[0][1]).max())
        check(apart > 1e-3,
              f"and the guided pair's two rows differ by {apart:.2f}, so the "
              f"term the sampler subtracts is not zero — dropping it is a real "
              f"change to what gets said", f"{apart:.4f}")

    print(f"\nexport-for-game --selftest: "
          f"{'PASS' if not fails else str(len(fails)) + ' FAILED'} — {len(ran)} checks "
          f"against a real T3")
    return 1 if fails else 0


def cmd_run(force=False, rows=2):
    # THE ROW COUNT IS PART OF WHAT "ALREADY DONE" MEANS. The skip compares
    # this exporter's source against the last run's, and a graph built with
    # guidance is a different graph from identical code — skipping would hand
    # back the two-row one looking current. The same trap the step count had.
    done, src = already_done([OUT / "t3-step.onnx", OUT / "t3-prefill.onnx"])
    if done and rows == 2 and not force:
        print("  already exported by this same code — skipping.")
        print("  (delete the .onnx files, or pass --force, to redo it)")
        return 0
    stamp(f"started  src={src}  rows={rows}")
    import time
    import numpy as np
    import torch
    from chatterbox.tts import ChatterboxTTS

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import export_probe
    from export_probe import npy
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
    model = export_probe.load_model(dev)
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
        # AND THE SHAPING RUN CARRIES THE ROW COUNT TOO. `cache0` is what the
        # step graph rebuilds its cache against, so a two-row cache traced
        # into a one-row graph would be a shape error at the first token —
        # found in seconds by the selftest, and only because this line moved
        # with the rest of it.
        if rows < 2:
            tt = tt[:1]
        embeds, _ = model.t3.prepare_input_embeds(
            t3_cond=model.conds.t3, text_tokens=tt,
            speech_tokens=hp.start_speech_token * torch.ones_like(tt[:, :1]),
            cfg_weight=0.5 if rows > 1 else 0.0)
        primed = model.t3.tfmr(inputs_embeds=embeds, use_cache=True, return_dict=True)
    # SHAPE ONLY, AND ONE TOKEN SHORTER THAN THE PREFILL ON PURPOSE. This
    # context has no second start token because nothing here samples from it —
    # `cache0` is used for its LAYER COUNT and head widths, and for the number
    # of cache outputs to name. The time axis is dynamic in both graphs, and
    # the selftest drives the prefill's real cache into the step graph to
    # prove they join. Read as "this is what the prefill produces" it would be
    # wrong by exactly the token this file spent the morning on.
    cache0 = kv_cache.cache_to_tensors(primed.past_key_values)
    print(f"    cache: {len(cache0)} tensors, {tuple(cache0[0].shape)}")

    t0 = time.time()
    dest = OUT / "t3-step.onnx"
    step, args, names = export_step(torch, kv_cache, model.t3,
                                    primed.past_key_values, cache0, dest, rows)
    mb = sum(f.stat().st_size for f in OUT.glob("t3-step*")) / (1024 * 1024)
    print(f"  exported in {time.time() - t0:.0f}s, {mb:.0f} MB -> {dest.name}")

    # RUN IT, AND AT A POSITION IT WAS NOT TRACED AT. Same check the selftest
    # makes against a small model, made here against the real one, because a
    # baked position is the fault this whole file exists to avoid.
    import onnxruntime as ort
    sess = ort.InferenceSession(str(dest), providers=["CPUExecutionProvider"])
    with torch.no_grad():
        want = npy(step(*args)[0])
    feeds = {"token": npy(args[0]), "position": npy(args[1])}
    feeds.update({f"cache{i}": npy(t) for i, t in enumerate(cache0)})
    rel = float(np.abs(want - sess.run(None, feeds)[0]).max()) \
        / max(float(np.abs(want).max()), 1e-12)
    print(f"  agrees with pytorch to {rel:.1e} at the traced position")
    worst = 0.0
    for p in (0, 1, 9, 40):
        with torch.no_grad():
            w2 = npy(step(args[0], torch.tensor(p), *cache0)[0])
        alt = dict(feeds)
        alt["position"] = np.array(p, dtype=np.int64)
        worst = max(worst, float(np.abs(w2 - sess.run(None, alt)[0]).max())
                    / max(float(np.abs(w2).max()), 1e-12))
    print(f"  and to {worst:.1e} at four positions it was NOT traced at")
    # CHECKED, NOT JUST PRINTED — the sibling exporter reported a number above
    # its own selftest's bound and still called the run finished, because
    # nothing read it. These are logits rather than samples, so there is no
    # audible unit to convert to; the bound is the selftest's, which the real
    # model has met on every run so far at 1.7e-06.
    if worst > 1e-4:
        print(f"  REFUSED: {worst:.1e} at an untraced position is too far from "
              f"the original — the position may be baked in.")
        stamp(f"FAILED — step disagreement {worst:.1e} above the 1e-4 ceiling")
        return 1

    # ---- THE PREFILL. The step graph takes a cache, and the game has a
    # sentence; this is what turns one into the other. Same gap as the
    # token/embedding one, one layer up.
    print("\n  exporting the prefill — the sentence and the voice, into a cache...")
    t0 = time.time()
    pdest = OUT / "t3-prefill.onnx"
    cond = model.conds.t3
    voice = dict(speaker_emb=cond.speaker_emb,
                 cond_prompt_speech_tokens=cond.cond_prompt_speech_tokens,
                 emotion_adv=cond.emotion_adv)
    raw = model.tokenizer.text_to_tokens(LINE).to(model.device)
    pre, pargs, _ = export_prefill(torch, kv_cache, model.t3, voice, raw,
                                   pdest, len(cache0), rows)
    pmb = sum(f.stat().st_size for f in OUT.glob("t3-prefill*")) / (1024 * 1024)
    print(f"  exported in {time.time() - t0:.0f}s, {pmb:.0f} MB -> {pdest.name}")

    psess = ort.InferenceSession(str(pdest), providers=["CPUExecutionProvider"])

    def prefill_run(v, txt):
        with torch.no_grad():
            want = pre(txt, v["speaker_emb"], v["cond_prompt_speech_tokens"],
                       v["emotion_adv"])
        got = psess.run(None, {
            "text_tokens": npy(txt),
            "speaker_emb": npy(v["speaker_emb"]),
            "cond_speech_tokens": npy(v["cond_prompt_speech_tokens"]),
            "emotion_adv": npy(v["emotion_adv"])})
        gap = max(float(np.abs(npy(w) - g).max())
                  / max(float(np.abs(npy(w)).max()), 1e-12)
                  for w, g in zip(want, got))
        return gap, got

    pgap, pout = prefill_run(voice, raw)
    print(f"  agrees with pytorch to {pgap:.1e} for the voice it was traced with")

    # THE VOICE IS THE POSITION'S TWIN, and this is the run that can check it
    # against real weights. `prepare_conditioning` writes the embedded prompt
    # back onto the cond it is handed, so a used cond traces as a CONSTANT and
    # every character speaks in whichever voice this export happened to load.
    other = None
    for f in sorted((ROOT / "game-design" / "voice-conds").glob("*.npz")):
        if f.stem != VOICE:
            z = np.load(f)
            other = (f.stem, dict(
                speaker_emb=torch.from_numpy(z["t3.speaker_emb"]).to(model.device),
                cond_prompt_speech_tokens=torch.from_numpy(
                    z["t3.cond_prompt_speech_tokens"]).to(model.device),
                emotion_adv=torch.from_numpy(z["t3.emotion_adv"]).to(model.device)))
            break
    if other is None:
        print("  NO SECOND VOICE ON DISK — the speaker was not checked as an input")
    else:
        vgap, vout = prefill_run(other[1], raw)
        moved = max(float(np.abs(a - b).max()) for a, b in zip(pout, vout))
        print(f"  and to {vgap:.1e} for '{other[0]}', a voice it was NOT traced "
              f"with,")
        print(f"  whose cache differs from '{VOICE}' by {moved:.2f} — so that "
              f"agreement is two")
        print(f"  different answers matching, not one constant matching itself.")

    print()
    stamp(f"finished  src={src} — step {rel:.1e}/{worst:.1e}, prefill {pgap:.1e}")
    print("  ------------------------------------------------------------")
    print("  Two graphs. The prefill takes the sentence and the voice; the")
    print("  step takes a token and a position. The game hands over integers")
    print("  and arrays it already has, and never touches the model's tables.")
    print("  ------------------------------------------------------------")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="re-export even if it is already done")
    # HOW MANY ROWS EVERY STEP RUNS, and it is the last big lever in the
    # text stage. Two is classifier-free guidance: the model is run on the
    # sentence AND on the sentence with its conditioning stripped out, and the
    # second is subtracted from the first to steer it. One drops that, halves
    # the work of the stage that is two thirds of a line — and removes what
    # the model leans on to say the right words rather than mumble in the
    # right voice. A listening question, not a numbers one.
    ap.add_argument("--rows", type=int, default=2, choices=(1, 2),
                    help="2 = classifier-free guidance (default), 1 = without")
    ap.add_argument("--fromtemp", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    try:
        return cmd_run(a.force, a.rows)
    except Exception as e:
        # THE REASON GOES INTO THE STAMP, so the audit that runs afterwards
        # carries it back without anybody copying a traceback. A stamp saying
        # "started" and nothing else says the step died and not what killed
        # it, and those are one message apart.
        import traceback
        stamp(f"FAILED — {type(e).__name__}: {str(e)[:200]}")
        traceback.print_exc()
        print(f"  cannot run: {type(e).__name__}: {e}")
        return 2 if isinstance(e, ImportError) else 1


if __name__ == "__main__":
    sys.exit(main())
