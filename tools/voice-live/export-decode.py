#!/usr/bin/env python3
"""SOUND TOKENS INTO A WAVEFORM — THE LAST STAGE THAT WAS STILL IN PYTHON.

    python3 tools/voice-live/export-decode.py            # needs the weights
    python3 tools/voice-live/export-decode.py --selftest  # needs nothing

`SpeechLoop` produces speech TOKENS, which are not audio. Turning them into
samples is `s3gen`: a flow decoder that draws a mel spectrogram, then the
vocoder that turns that picture of the sound into a waveform. `vocoder.py`
proved the second half converts. This is both halves as one graph, which is
what `ISpeechBackend.Decode` needs.

ONE GRAPH RATHER THAN TWO, unlike the text stage. There the split is forced:
the prefill runs once and the step runs hundreds of times, so they cannot be
one call. Here nothing runs twice — tokens go in, samples come out — and a
seam is a place for the game to hold a tensor it should not have to.

THE NOISE IS AN INPUT, AND THAT IS A SHIPPING DECISION.

Three separate places in this path draw Gaussian noise: the flow decoder
starts from it, and the vocoder's source module adds it twice. That is by
design — it is a neural source-filter vocoder and the noise is the source. It
also means the pipeline disagrees with ITSELF by 5.5 on the same input, which
is the same magnitude as a completely broken conversion, so nothing about the
conversion is checkable until the noise stops moving.

Handing it in fixes both halves at once: the graph becomes comparable, and the
game owns the noise and can seed it per line, which is `VoiceBank`'s
determinism rule reaching the last stage. Same call this file's neighbour made
about the vocoder's source signal, for the same reason.

THE SHAPES ARE MEASURED, NOT DERIVED. The game has to size two noise tensors,
and a formula worked out on paper is a formula that is wrong in one of its
cases. `--selftest` runs the real thing at several token counts, prints what
each draw was actually asked for, and checks the formula against it.

AND THE DRAWS ARE COUNTED, WHICH IS HOW THE THIRD ONE TURNED OUT TO BE DEAD.
Three draws happen and only two are supplied; the waveform still repeats
exactly, which is the proof that the vocoder discards the third — and the
source agrees, `s, _, _ = self.m_source(s)` at both call sites. Without the
count, "it repeats" would equally have meant the patch caught everything, and
the two readings want different graphs.

THE LENGTH OF THE SENTENCE WANTED TO BE A CONSTANT IN FOUR PLACES. A shape
read into a Python int and then written into an op is frozen at whatever the
trace saw: the graph exports, agrees to seven decimal places at that one
length, and refuses every other. `dynamic_cfm` and `dynamic_flow` replace
those four with the identical arithmetic built from tensors, and both are
checked against the originals before anything is exported — the solver one
agrees to exactly zero.
"""
import argparse
import contextlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "tools" / "voice-live" / "game-out"
VOICE = "rocco"
STAMP = "decode"

# Measured, not assumed — see `shapes()` and the selftest that checks it.
MELS_PER_TOKEN = 2
SAMPLES_PER_MEL = 480
HARMONICS = 9


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


def shapes(n_prompt_tok, n_prompt_mel, n_tokens):
    """The noise tensors the game supplies, from three counts it already has.

    THE PROMPT'S MEL COUNT IS NOT TWICE ITS TOKEN COUNT, and assuming it was
    is a bug this formula had until a prompt length it was not traced at went
    through it. Of the nineteen committed voices, eighteen have exactly two
    mel frames per prompt token and one has 419 against 418 — the extractor
    and the tokeniser disagree by a frame on that clip. The generated part is
    `2*(prompt_tokens + tokens) - prompt_mels`, so on that one voice it is one
    frame SHORT of twice the tokens, and every downstream size with it.

    THREE DRAWS HAPPEN AND ONLY TWO MATTER. `SourceModuleHnNSF.forward`
    returns `(sine_merge, noise, uv)` and both call sites in `HiFTGenerator`
    write `s, _, _ = self.m_source(s)` — so its noise is computed and dropped
    on the floor. Shipping an input for it would be 3 MB per line of Gaussian
    numbers generated in C# and handed to a graph that never reads them, and
    the exporter deletes the input anyway. The selftest proves it is dead
    rather than taking the deletion as evidence.
    """
    h = MELS_PER_TOKEN * (n_prompt_tok + n_tokens)
    wav = (h - n_prompt_mel) * SAMPLES_PER_MEL
    return {"z": (1, 80, h), "sine_noise": (1, HARMONICS, wav)}


@contextlib.contextmanager
def noise_from(torch, supply):
    """Hand the model its randomness instead of letting it draw its own.

    Returns a box carrying what was ASKED for and how many times, because a
    patch that catches two of three draws looks exactly like a conversion that
    is slightly wrong.
    """
    real = torch.randn_like
    box = {"asked": [], "served": 0, "short": 0}

    def fake(x, *a, **k):
        box["asked"].append(tuple(x.shape))
        i = box["served"]
        if i < len(supply):
            box["served"] += 1
            return supply[i]
        box["short"] += 1
        return real(x, *a, **k)

    torch.randn_like = fake
    try:
        yield box
    finally:
        torch.randn_like = real


@contextlib.contextmanager
def dynamic_cfm(torch):
    """KEEP THE SOLVER'S SCRATCH BUFFERS THE SIZE OF THE SENTENCE.

    `ConditionalCFM.solve_euler` allocates six buffers up front:

        B, T = mu.size(0), x.size(2)
        x_in = torch.zeros([2 * B, 80, T], ...)

    `x.size(2)` is a PYTHON INT. Traced, it becomes a constant, so the graph
    exports, runs, and agrees to 1.8e-06 at the one length it was traced with
    and throws `invalid expand shape` at every other. Exactly the fault the
    position had in the text stage, in a different disguise — and caught the
    same way, by running at a length it was not traced at.

    THIS IS THE SAME ARITHMETIC, NOT A REWRITE OF IT. The original zeroes a
    buffer then fills the halves it wants: both halves for x, mask and t; the
    first half only for mu, spks and cond, leaving the second half zero. That
    IS a concatenation with zeros, written as an in-place fill. Building it
    with `cat` keeps every shape derived from a tensor, so the length stays an
    axis instead of a number.

    Reimplementing model internals is how the sampler and the tokeniser went
    subtly wrong here, so this does not get taken on trust: the selftest runs
    the original and this side by side on the same noise and requires them to
    agree, before anything is exported.

    The source's own comment warns off `cat` — "it may cause memory format
    changed and trt infer with wrong results". That is about TensorRT, which
    is not what this ships on, and the agreement check is what settles it
    rather than the comment.
    """
    from chatterbox.models.s3gen.flow_matching import ConditionalCFM
    real = ConditionalCFM.solve_euler

    def solve(self, x, t_span, mu, mask, spks, cond, meanflow=False):
        if meanflow:                      # never taken by the English model
            return real(self, x, t_span, mu, mask, spks, cond, meanflow)
        want = self.estimator.dtype

        def cast(v):
            return v if not v.dtype.is_floating_point or v.dtype == want else v.to(want)

        out_dtype = x.dtype
        x, t_span, mu, mask, spks, cond = (cast(v) for v in
                                           (x, t_span, mu, mask, spks, cond))
        for t, r in zip(t_span[:-1], t_span[1:]):
            t, r = t.unsqueeze(0), r.unsqueeze(0)
            dxdt = self.estimator.forward(
                x=torch.cat([x, x], 0),
                mask=torch.cat([mask, mask], 0),
                mu=torch.cat([mu, torch.zeros_like(mu)], 0),
                t=torch.cat([t, t], 0),
                spks=torch.cat([spks, torch.zeros_like(spks)], 0),
                cond=torch.cat([cond, torch.zeros_like(cond)], 0),
                r=None)
            keep, drop = dxdt.chunk(2, dim=0)
            x = x + (r - t) * ((1.0 + self.inference_cfg_rate) * keep
                               - self.inference_cfg_rate * drop)
        return x.to(out_dtype)

    ConditionalCFM.solve_euler = solve
    try:
        yield
    finally:
        ConditionalCFM.solve_euler = real


@contextlib.contextmanager
def dynamic_flow(torch):
    """THE SAME FAULT AGAIN, THREE MORE TIMES, IN `flow.inference`.

    `dynamic_cfm` fixed the solver's scratch buffers. The graph then failed at
    an untraced length anyway, on a different node, because the sentence
    length is turned into a Python int in three more places before the solver
    is ever reached:

      `make_pad_mask` ends `lengths.max().item()`, so its `arange` is a fixed
      row of numbers — the mask is the traced sentence's length for ever.

      `conds = torch.zeros([B, mel_len1 + mel_len2, ...])` sizes the
      conditioning block from `h.shape[1]`, an int.

      `feat = feat[:, :, mel_len1:]` cuts the prompt back off at a constant.

    One idea, four implementations, and fixing the first three would have
    shipped a graph that still only says one length of sentence. The rule is
    the mechanical one: the moment a fix works, grep for what it was fixing.
    Here the distinguishing token is a shape used as a number.

    EVERY REPLACEMENT IS DERIVED FROM A TENSOR, which is the whole trick — a
    length that comes out of `.shape` is a constant the moment it is written
    into an op, and the same length taken as `ones_like(...).sum()` stays an
    axis. Checked against the original at several lengths before use, because
    this is model internals and model internals are what went subtly wrong
    twice in this project already.
    """
    import torch.nn.functional as F
    from chatterbox.models.s3gen import flow as flow_mod
    from chatterbox.models.s3gen.transformer import upsample_encoder as up_mod
    from chatterbox.models.s3gen.flow import CausalMaskedDiffWithXvec

    def dyn_pad_mask(lengths, max_len=0):
        lengths = lengths.long()
        end = torch.tensor(max_len, device=lengths.device) if max_len > 0 \
            else lengths.max()
        seq = torch.arange(0, end, dtype=torch.int64, device=lengths.device)
        return seq.unsqueeze(0).expand(lengths.size(0), -1) >= lengths.unsqueeze(-1)

    def inference(self, token, token_len, prompt_token, prompt_token_len,
                  prompt_feat, prompt_feat_len, embedding, finalize,
                  n_timesteps=10, noised_mels=None, meanflow=False):
        B = token.size(0)
        embedding = F.normalize(torch.atleast_2d(embedding), dim=1)
        embedding = self.spk_embed_affine_layer(embedding)

        full = torch.concat([prompt_token, token], dim=1)
        # LENGTHS TAKEN FROM THE TENSORS THEMSELVES. `prompt_token_len +
        # token_len` are the caller's ints; counting the rows keeps the axis.
        full_len = torch.ones_like(full[0], dtype=torch.long).sum().unsqueeze(0)
        mask = torch.ones_like(full, dtype=embedding.dtype).unsqueeze(-1)
        emb = self.input_embedding(full.long()) * mask

        h, h_masks = self.encoder(emb, full_len)
        if torch.is_tensor(finalize):
            # ONE GRAPH FOR BOTH FATES. A python bool freezes whichever
            # branch the trace walked, so the chunk graph takes `final` as a
            # 0/1 tensor and expresses the lookahead trim as arithmetic:
            # keep everything when final, drop the last lookahead frames
            # when not. And the mask length comes from the TRIMMED h — the
            # original computes it from the pre-trim masks, which hands the
            # decoder a mask longer than its input whenever finalize is
            # False; single-sequence inference has no padding, so the
            # trimmed length IS the mask.
            ahead = self.pre_lookahead_len * self.token_mel_ratio
            n_full = torch.ones_like(h[0, :, 0], dtype=torch.long).sum()
            keep_n = n_full - (1 - finalize.long()) * ahead
            h = torch.index_select(h, 1,
                                   torch.arange(0, keep_n, device=h.device))
            h_lengths = keep_n.unsqueeze(0)
        else:
            if finalize is False:
                h = h[:, :-self.pre_lookahead_len * self.token_mel_ratio]
            h_lengths = h_masks.sum(dim=-1).squeeze(dim=-1)
        h = self.encoder_proj(h)

        # THE CONDITIONING BLOCK: the prompt's mels, then zeros for the part
        # being generated. The tail is whatever is LEFT of `h` after the
        # prompt, which is not the same as two frames per token — of the
        # nineteen committed voices, one has a 419-frame prompt against 418
        # tokens' worth, because the mel extractor and the tokeniser disagree
        # by a frame on that clip. The original takes the difference and so
        # does this; sizing it from the token count would have been right for
        # eighteen voices and a frame wrong for the nineteenth.
        n_prompt = torch.ones_like(prompt_feat[0, :, 0], dtype=torch.long).sum()
        n_h = torch.ones_like(h[0, :, 0], dtype=torch.long).sum()
        tail = torch.index_select(torch.zeros_like(h), 1,
                                  torch.arange(n_prompt, n_h, device=h.device))
        conds = torch.cat([prompt_feat, tail], dim=1).transpose(1, 2)

        m2 = (~flow_mod.make_pad_mask(h_lengths)).unsqueeze(1).to(h)
        if m2.shape[0] != B:
            m2 = m2.repeat(B, 1, 1)

        feat, _ = self.decoder(mu=h.transpose(1, 2).contiguous(), mask=m2,
                               spks=embedding, cond=conds, n_timesteps=n_timesteps,
                               noised_mels=noised_mels, meanflow=meanflow)
        # AND CUT THE PROMPT BACK OFF BY INDEX RATHER THAN BY SLICE, so the
        # cut point is a number the graph computes instead of one it stores.
        start = torch.ones_like(prompt_feat[0, :, 0], dtype=torch.long).sum()
        total = torch.ones_like(feat[0, 0, :], dtype=torch.long).sum()
        keep = torch.arange(start, total, device=feat.device)
        return torch.index_select(feat, 2, keep), None

    saved = (flow_mod.make_pad_mask, up_mod.make_pad_mask,
             CausalMaskedDiffWithXvec.inference)
    flow_mod.make_pad_mask = dyn_pad_mask
    up_mod.make_pad_mask = dyn_pad_mask
    CausalMaskedDiffWithXvec.inference = inference
    try:
        yield
    finally:
        (flow_mod.make_pad_mask, up_mod.make_pad_mask,
         CausalMaskedDiffWithXvec.inference) = saved


def make_decode(torch, flow, gen, steps=10):
    """Tokens and a voice in, samples out. The noise arrives as inputs."""

    class Decode(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.flow = flow
            self.gen = gen
            # WHAT THE LAST CALL ASKED FOR, so the shapes can be MEASURED
            # from the real run. The first version of this test opened its
            # own `noise_from` around the module — which the one inside
            # forward shadows, so it observed nothing and reported an empty
            # list as agreement. A patch outside a patch sees no draws.
            self.seen = {}

        def forward(self, tokens, prompt_token, prompt_feat, embedding,
                    z, sine_noise):
            n = tokens.shape[1]
            p = prompt_token.shape[1]
            with noise_from(torch, [z, sine_noise]) as box:
                mel, _ = self.flow.inference(
                    token=tokens, token_len=torch.tensor([n]),
                    prompt_token=prompt_token,
                    prompt_token_len=torch.tensor([p]),
                    prompt_feat=prompt_feat, prompt_feat_len=None,
                    embedding=embedding, finalize=True, n_timesteps=steps)
                wav, _ = self.gen.inference(
                    speech_feat=mel, cache_source=torch.zeros(1, 1, 0))
            self.seen = box
            return wav

    return Decode()


def export_decode(torch, flow, gen, args, dest, steps=10):
    dec = make_decode(torch, flow, gen, steps).eval()
    names = ["tokens", "prompt_token", "prompt_feat", "embedding",
             "z", "sine_noise"]
    axes = {"tokens": {1: "n"}, "prompt_token": {1: "p"},
            "prompt_feat": {1: "pmel"}, "z": {2: "mel"},
            "sine_noise": {2: "smp"}, "wav": {1: "smp"}}
    with torch.no_grad():
        torch.onnx.export(dec, args, str(dest), opset_version=17, dynamo=False,
                          input_names=names, output_names=["wav"],
                          dynamic_axes=axes)
    return dec


# The streaming vocoder's seam, in mel frames — CosyVoice2's
# `mel_cache_len`, at chatterbox's 480 samples per mel. Everything about the
# seam (the mel prepend, the source tail, the caller's crossfade window and
# holdback) is this one number.
MEL_CACHE = 8


def pad_sine(torch, sine, mels=MEL_CACHE):
    """Seam-region sine noise rides IN FRONT of the line's own, so a chunk's
    fresh samples keep the same noise the whole-line render would give them:
    vocoder sample k is line sample k minus the seam. The seam region's own
    noise is zeros — its source is overwritten by `cache_source` anyway.
    `mels` is the RIDE-IN's length: 8 after the first call, 0 on it (an
    empty seam pads nothing, and the first call IS the whole-line render)."""
    if mels == 0:
        return sine
    head = torch.zeros(sine.shape[0], sine.shape[1], mels * 480)
    return torch.cat([head, sine], dim=2)


def make_chunk(torch, flow, gen, steps=10):
    """The STREAMING half: a piece of the line in, a piece of the wav out.

    The whole-line graph exists and is ear-approved; this one is what turns
    the 17ms resident step rate into a character who starts TALKING before
    the sentence is finished computing. It is the upstream package's own
    streaming design, traced: the flow re-renders every token so far (with
    the lookahead trimmed unless `final`), `mel_offset` cuts off the mels
    already spoken, and the vocoder renders only the fresh ones with
    `cache_source` carrying its source signal across the seam — the
    mechanism upstream added "to avoid glitch", and the reason a chunked
    line does not click at every boundary.

    WHY THE FLOW RE-RENDERS RATHER THAN CACHES: that is upstream's design,
    not a shortcut — each chunk's mels are drawn in the context of
    everything said so far, so per-chunk cost grows along the line. At four
    solver steps and game-length lines the cost stays under the audio it
    yields, and the alternative — exporting the flow's internal streaming
    cache — is a different, riskier surgery for a cost that is not the
    problem yet.
    """

    class Chunk(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.flow = flow
            self.gen = gen
            self.seen = {}

        def forward(self, tokens, prompt_token, prompt_feat, embedding,
                    z, sine_noise, cache_source, cache_mel, mel_offset,
                    final):
            n = tokens.shape[1]
            p = prompt_token.shape[1]
            with noise_from(torch, [z, sine_noise]) as box:
                mel, _ = self.flow.inference(
                    token=tokens, token_len=torch.tensor([n]),
                    prompt_token=prompt_token,
                    prompt_token_len=torch.tensor([p]),
                    prompt_feat=prompt_feat, prompt_feat_len=None,
                    embedding=embedding, finalize=final, n_timesteps=steps)
                # Only the mels nobody has heard yet reach the vocoder; the
                # cut point is computed, not stored, for the same reason as
                # every other length in this file.
                total = torch.ones_like(mel[0, 0, :], dtype=torch.long).sum()
                fresh = torch.index_select(
                    mel, 2,
                    torch.arange(mel_offset.long(), total, device=mel.device))
                # EIGHT CACHED MELS RIDE IN FRONT, which is the upstream
                # streaming design this graph existed to trace and the first
                # version skipped: CosyVoice2's `token2wav` prepends the
                # last `mel_cache_len=8` mels it vocoded and hands back only
                # the last `8*480` samples of the SOURCE, so the harmonic
                # source is continuous across the seam while the overlap
                # region is re-rendered and crossfaded by the caller. The
                # first version fed the whole previous source back instead —
                # temporally wrong, and a crash the moment a chunk was
                # shorter than its predecessor, which the final one usually
                # is.
                #
                # THE FIRST CALL'S SEAM IS EMPTY — (1,80,0) — because that
                # is upstream's first call and therefore the whole-line
                # function exactly. The second version sent EIGHT ZERO MELS
                # instead, dodging a zero-length tensor for DirectML's sake,
                # and the REAL model's f0 RNN carried that perturbation far
                # past the seam: residue 0.5-1.1 across eight mels and
                # 8.2e-03 beyond, where the small random model had decayed
                # to 5.1e-05 — the guard refused it, correctly. The
                # remaining DirectML risk is the empty CONCAT, and the
                # listening harness's per-chunk differential names the
                # refuser if that fear is real.
                voc_in = torch.cat([cache_mel, fresh], dim=2)
                wav, src = self.gen.inference(speech_feat=voc_in,
                                              cache_source=cache_source)
            self.seen = box
            # The tails the NEXT call needs, cut here so both are
            # fixed-shape outputs: 8 mels and their 3840 samples of source.
            return wav, src[:, :, -MEL_CACHE * 480:], \
                voc_in[:, :, -MEL_CACHE:]

    return Chunk()


def export_chunk(torch, flow, gen, args, dest, steps=10):
    dec = make_chunk(torch, flow, gen, steps).eval()
    names = ["tokens", "prompt_token", "prompt_feat", "embedding",
             "z", "sine_noise", "cache_source", "cache_mel", "mel_offset",
             "final"]
    # Both tail OUTPUTS are static shapes — every call returns full seams.
    # The two cache INPUTS are dynamic for the first call: both EMPTY,
    # the whole-line function exactly.
    axes = {"tokens": {1: "n"}, "prompt_token": {1: "p"},
            "prompt_feat": {1: "pmel"}, "z": {2: "mel"},
            "sine_noise": {2: "smp"}, "cache_source": {2: "src"},
            "cache_mel": {2: "cmel"}, "wav": {1: "smp"}}
    with torch.no_grad():
        torch.onnx.export(dec, args, str(dest), opset_version=17, dynamo=False,
                          input_names=names,
                          output_names=["wav", "source", "mel_tail"],
                          dynamic_axes=axes)
    return dec


def build_small(torch):
    """A real flow and a real vocoder, shrunk where the classes allow it."""
    from chatterbox.models.s3gen.flow import CausalMaskedDiffWithXvec
    from chatterbox.models.s3gen.flow_matching import CausalConditionalCFM
    from chatterbox.models.s3gen.decoder import ConditionalDecoder
    from chatterbox.models.s3gen.transformer.upsample_encoder import (
        UpsampleConformerEncoder, PreLookaheadLayer, Upsample1D)
    from chatterbox.models.s3gen.configs import CFM_PARAMS
    from chatterbox.models.s3gen.hifigan import HiFTGenerator
    from chatterbox.models.s3gen.f0_predictor import ConvRNNF0Predictor
    from chatterbox.models.s3gen.const import S3GEN_SR

    enc = UpsampleConformerEncoder(
        output_size=64, attention_heads=2, linear_units=128, num_blocks=1,
        dropout_rate=0.0, positional_dropout_rate=0.0, attention_dropout_rate=0.0,
        normalize_before=True, input_layer='linear',
        pos_enc_layer_type='rel_pos_espnet', selfattention_layer_type='rel_selfattn',
        input_size=64, use_cnn_module=False, macaron_style=False)
    # `PreLookaheadLayer` and `Upsample1D` are constructed with a literal 512
    # rather than from the config, so the shrink has to reach in. Same reach
    # the perceiver needs in `export-for-game`; real classes either way.
    enc.pre_lookahead_layer = PreLookaheadLayer(channels=64, pre_lookahead_len=3)
    enc.up_layer = Upsample1D(channels=64, out_channels=64, stride=2)
    enc.up_encoders = enc.up_encoders[:1]
    est = ConditionalDecoder(in_channels=320, out_channels=80, causal=True,
                             channels=[64], dropout=0.0, attention_head_dim=32,
                             n_blocks=1, num_mid_blocks=1, num_heads=2, act_fn='gelu')
    flow = CausalMaskedDiffWithXvec(
        input_size=64, encoder=enc,
        decoder=CausalConditionalCFM(spk_emb_dim=80, cfm_params=CFM_PARAMS,
                                     estimator=est)).eval()
    # THE VOCODER IS NOT SHRUNK, and it is built with the six arguments
    # `S3Token2Wav` passes rather than the class defaults — the defaults give
    # 256 samples per mel frame where the shipped one gives 480, which is the
    # number the game sizes its noise from.
    gen = HiFTGenerator(
        sampling_rate=S3GEN_SR, upsample_rates=[8, 5, 3],
        upsample_kernel_sizes=[16, 11, 7], source_resblock_kernel_sizes=[7, 7, 11],
        source_resblock_dilation_sizes=[[1, 3, 5], [1, 3, 5], [1, 3, 5]],
        f0_predictor=ConvRNNF0Predictor()).eval()
    for p in list(flow.parameters()) + list(gen.parameters()):
        p.requires_grad_(False)
    return flow, gen


def draw(torch, n_prompt_tok, n_prompt_mel, n_tokens, seed):
    g = torch.Generator().manual_seed(seed)
    return [torch.randn(s, generator=g)
            for s in shapes(n_prompt_tok, n_prompt_mel, n_tokens).values()]


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
    except ImportError as e:
        print(f"  skipped: {e} — 0 of 7 checks run, nothing was converted")
        print("\nexport-decode --selftest: SKIPPED — 0 checks")
        return 0

    import tempfile
    import warnings
    warnings.filterwarnings("ignore")
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from stft_patch import patched
    from export_probe import npy

    # CLEANED ON EXIT, HOWEVER THE SELFTEST ENDS. Each run writes ~350MB of
    # graphs here, and the version without this line leaked 19.8GB of them
    # in one evening — verify runs this, so every commit paid the toll, and
    # the disk hit the wall mid-verify twice before the leak was found.
    tmp = pathlib.Path(tempfile.mkdtemp())
    import atexit, shutil
    atexit.register(shutil.rmtree, tmp, True)
    torch.manual_seed(20260808)
    flow, gen = build_small(torch)

    P, T = 6, 9
    tok = torch.randint(0, 6561, (1, T))
    ptok = torch.randint(0, 6561, (1, P))
    # REQUIRING GRAD, BECAUSE THE REAL ONES DO. `model.conds.gen` holds
    # tensors that track gradients, and `.numpy()` on one of those raises
    # rather than returning an array. Built with a plain `torch.randn` this
    # fixture could not express that, so the export died on Jafar's machine at
    # the check step with the graph already written. A stand-in that is easier
    # than the real thing tests the easier thing.
    pfeat = torch.randn(1, MELS_PER_TOKEN * P, 80).requires_grad_(True)
    emb = torch.randn(1, 192).requires_grad_(True)
    noise = draw(torch, P, MELS_PER_TOKEN * P, T, 1)
    dec = make_decode(torch, flow, gen).eval()

    # 1. THE PATH IS RANDOM BY DESIGN. Naming this is what makes every number
    # below mean anything — 5.5 apart on the same input is also what a broken
    # conversion looks like, and that ambiguity cost a wrong diagnosis once.
    with torch.inference_mode():
        a = dec(tok, ptok, pfeat, emb, *draw(torch, P, MELS_PER_TOKEN * P, T, 11))
        b = dec(tok, ptok, pfeat, emb, *draw(torch, P, MELS_PER_TOKEN * P, T, 22))
    spread = float((a - b).abs().max()) / max(float(a.abs().max()), 1e-12)
    check(spread > 1e-3,
          f"the decode path is random by design — two seeds give waveforms "
          f"{spread:.2f} apart", f"{spread:.2e}")

    # 2. AND WITH THE NOISE HANDED IN IT REPEATS EXACTLY, so a disagreement
    # from here is the conversion and nothing else.
    with torch.inference_mode():
        want = dec(tok, ptok, pfeat, emb, *noise)
        again = dec(tok, ptok, pfeat, emb, *noise)
    check(float((want - again).abs().max()) == 0.0,
          "and with the noise handed in it repeats exactly — every draw was "
          "intercepted")

    # 3. THE DENOMINATOR ON CHECK 2, AND THE PROOF THAT THE THIRD DRAW IS
    # DEAD. Three draws happen; two are supplied and the third falls through
    # to a real random number. Check 2 passing while one draw is still random
    # is not a weakness in the test — it is the evidence that the vocoder
    # discards it, which is what `s, _, _ = self.m_source(s)` says in the
    # source. Without this line, "repeats exactly" could equally mean the
    # patch caught everything, and the two cases want different graphs.
    box = dec.seen
    print(f"        draws: asked for {box['asked']}")
    check(box["served"] == 2 and box["short"] == 1,
          f"three draws happen, two are supplied and one falls through — and "
          f"the waveform above still repeated exactly, so that one is dropped "
          f"by the vocoder", f"served {box['served']}, fell through {box['short']}")

    # 4. THE SHAPES THE GAME MUST SIZE, measured at three token counts. A
    # formula right for one length is not a formula. Read off the module,
    # because a patch wrapped around a patch sees nothing — the first version
    # of this check did exactly that and printed an empty list as agreement.
    series = {}
    for p, t in ((6, 9), (6, 20), (11, 9)):
        with torch.inference_mode():
            dec(torch.randint(0, 6561, (1, t)), torch.randint(0, 6561, (1, p)),
                torch.randn(1, MELS_PER_TOKEN * p, 80), emb, *draw(torch, p, MELS_PER_TOKEN * p, t, 3))
        series[(p, t)] = dec.seen["asked"][:2]
    ok_shape = all(list(shapes(p, MELS_PER_TOKEN * p, t).values()) == asked
                   for (p, t), asked in series.items())
    for (p, t), asked in series.items():
        print(f"        p={p} n={t}: asked {asked}  formula "
              f"{list(shapes(p, MELS_PER_TOKEN * p, t).values())}")
    check(ok_shape, "the two supplied noise sizes follow the formula the game "
          "will use, at three different lengths")

    # 5. THE SOLVER PATCH IS THE SAME ARITHMETIC, checked before it is used
    # for anything. Reimplementing model internals is how the sampler and the
    # tokeniser went subtly wrong here, so this one is measured rather than
    # reasoned about.
    with torch.inference_mode():
        plain = dec(tok, ptok, pfeat, emb, *noise)
        with dynamic_cfm(torch), dynamic_flow(torch):
            swapped = dec(tok, ptok, pfeat, emb, *noise)
    same = float((plain - swapped).abs().max()) / max(float(plain.abs().max()), 1e-12)
    check(same < 1e-5,
          f"the dynamic-length solver agrees with the original to {same:.1e} — "
          f"it is the same arithmetic, not a rewrite of it", f"{same:.2e}")

    # 6/7. IT CONVERTS, AND AGREES.
    args = (tok, ptok, pfeat, emb) + tuple(noise)
    ok, why = True, ""
    try:
        with patched(), dynamic_cfm(torch), dynamic_flow(torch):
            export_decode(torch, flow, gen, args, tmp / "decode.onnx")
    except Exception as e:
        ok, why = False, f"{type(e).__name__}: {e}"
    check(ok, "the decode graph converts", why[:150])
    if not ok:
        print(f"\nexport-decode --selftest: {len(fails)} FAILED — {len(ran)} checks")
        return 1

    sess = ort.InferenceSession(str(tmp / "decode.onnx"),
                                providers=["CPUExecutionProvider"])
    with torch.inference_mode(), dynamic_cfm(torch), dynamic_flow(torch):
        want = dec(tok, ptok, pfeat, emb, *noise)
    feed = dict(zip(["tokens", "prompt_token", "prompt_feat", "embedding",
                     "z", "sine_noise"],
                    [npy(t) for t in args]))
    got = sess.run(None, feed)[0]
    rel = float(np.abs(npy(want) - got).max()) \
        / max(float(np.abs(npy(want)).max()), 1e-12)
    check(rel < 1e-4, f"and agrees with pytorch to {rel:.1e}", f"{rel:.2e}")

    # 7. AT LENGTHS IT WAS NOT TRACED AT, or it can say exactly one sentence.
    alt = {}
    for t in (4, 14, 25):
        tk = torch.randint(0, 6561, (1, t))
        nz = draw(torch, P, MELS_PER_TOKEN * P, t, 7)
        with torch.inference_mode(), dynamic_cfm(torch), dynamic_flow(torch):
            w2 = npy(dec(tk, ptok, pfeat, emb, *nz))
        g2 = sess.run(None, dict(zip(feed.keys(),
                                     [npy(tk), npy(ptok), npy(pfeat),
                                      npy(emb)] + [npy(n) for n in nz])))[0]
        alt[t] = (float(np.abs(w2 - g2).max()) / max(float(np.abs(w2).max()), 1e-12),
                  g2.shape[-1])
    print(f"        series: traced({T})={rel:.1e}  "
          + "  ".join(f"{t}={v:.1e}({s}smp)" for t, (v, s) in alt.items()))
    worst = max(v for v, _ in alt.values())
    check(worst < 1e-4,
          f"and at three token counts it was NOT traced at, worst {worst:.1e}",
          f"{worst:.2e}")

    # 8. AND AT PROMPT LENGTHS IT WAS NOT TRACED AT, which is a separate axis
    # and one I nearly shipped untested. The nineteen committed voices carry
    # SIX different prompt lengths, so a prompt frozen at the traced value
    # would work for the voice this was exported with and fail for the rest.
    # The last pair is the real oddity from the data: a prompt whose mel
    # frames are one MORE than twice its tokens, which is what makes the tail
    # a subtraction rather than a multiplication.
    pro = {}
    for p, pm in ((3, 6), (11, 22), (6, 13)):
        pt = torch.randint(0, 6561, (1, p))
        pf = torch.randn(1, pm, 80)
        nz = draw(torch, p, pm, T, 9)
        with torch.inference_mode(), dynamic_cfm(torch), dynamic_flow(torch):
            w3 = npy(dec(tok, pt, pf, emb, *nz))
        g3 = sess.run(None, dict(zip(feed.keys(),
                                     [npy(tok), npy(pt), npy(pf),
                                      npy(emb)] + [npy(n) for n in nz])))[0]
        pro[(p, pm)] = (float(np.abs(w3 - g3).max())
                        / max(float(np.abs(w3).max()), 1e-12), g3.shape[-1])
    print(f"        prompts: traced({P},{MELS_PER_TOKEN * P})  "
          + "  ".join(f"({p},{pm})={v:.1e}({s}smp)" for (p, pm), (v, s) in pro.items()))
    pworst = max(v for v, _ in pro.values())
    check(pworst < 1e-4,
          f"and at three prompt lengths it was NOT traced at, including one "
          f"whose mels exceed twice its tokens, worst {pworst:.1e}",
          f"{pworst:.2e}")

    # ---- 9+. THE STREAMING GRAPH, same small model ----
    ahead = flow.pre_lookahead_len * flow.token_mel_ratio
    SRC_CACHE = MEL_CACHE * SAMPLES_PER_MEL
    ok, why = True, ""
    try:
        cargs = (tok, ptok, pfeat, emb,
                 noise[0], pad_sine(torch, noise[1]),
                 torch.zeros(1, 1, 1), torch.zeros(1, 80, MEL_CACHE),
                 torch.tensor(0, dtype=torch.long),
                 torch.tensor(1, dtype=torch.long))
        with patched(), dynamic_cfm(torch), dynamic_flow(torch):
            export_chunk(torch, flow, gen, cargs, tmp / "chunk.onnx")
    except Exception as e:
        ok, why = False, f"{type(e).__name__}: {e}"
    check(ok, "the CHUNK graph converts — mel offset, an 8-mel seam ride-in "
          "and a tensor-driven finalize", why[:150])
    if ok:
        cs = ort.InferenceSession(str(tmp / "chunk.onnx"),
                                  providers=["CPUExecutionProvider"])
        ckeys = ["tokens", "prompt_token", "prompt_feat", "embedding",
                 "z", "sine_noise", "cache_source", "cache_mel",
                 "mel_offset", "final"]

        def crun(tk, nz, csrc, cmel, off, fin):
            return cs.run(None, dict(zip(
                ckeys, [npy(tk), npy(ptok), npy(pfeat), npy(emb),
                        npy(nz[0]),
                        npy(pad_sine(torch, nz[1], cmel.shape[2])),
                        csrc, cmel,
                        np.array(off, dtype=np.int64),
                        np.array(fin, dtype=np.int64)])))

        # BOTH caches empty on a first call — the whole-line function
        # with nothing added. The one-sample source overwrite was tried
        # instead and its ripple on the REAL weights peaked at 1.2e-02
        # mid-head (chunks-6); zero-length-on-DML is the open question the
        # listening harness's differential answers directly.
        esrc = np.zeros((1, 1, 0), dtype=np.float32)
        emel = np.zeros((1, 80, 0), dtype=np.float32)

        # The accepting case: asked the whole-line question — final, from
        # the start, an EMPTY seam — it must BE the whole-line answer,
        # because with no ride-in this is the identical computation. The
        # one-sample source cache silences sample 0 and the model's own
        # trim silences the first 480 anyway, so the compare starts there.
        # (The zeros-seam version of this check bounded a decaying residue
        # instead; the REAL model's trained RNN carried it past one seam
        # at 8.2e-03 and the guard refused the graph. Empty is exact.)
        wc, sc, mt = crun(tok, noise, esrc, emel, 0, 1)
        scale = max(float(np.abs(got).max()), 1e-12)
        prof = [float(np.abs(wc[:, i * 480:(i + 1) * 480]
                             - got[:, i * 480:(i + 1) * 480]).max()) / scale
                for i in range(1, min(9, wc.shape[1] // 480))]
        print("        empty-seam residue per mel: "
              + " ".join(f"{v:.1e}" for v in prof))
        dw = float(np.abs(wc[:, 480:] - got[:, 480:]).max()) / scale
        check(wc.shape[1] == got.shape[1],
              "chunk(final,offset0,empty-seam) is whole-line SIZED",
              f"{wc.shape[1]} vs {got.shape[1]}")
        # 1e-3, not 1e-4: two separately-traced graphs disagree by ~4e-4 of
        # fp32 noise at untraced lengths (the whole-line export itself
        # reads 4.0e-04 against pytorch there). The fault this bound exists
        # to catch measured 0.5-1.1 — three orders above it.
        check(dw < 1e-3, f"and IS the whole-line answer from sample 480, "
              f"to {dw:.1e}", f"{dw:.2e}")
        check(sc.shape[2] == SRC_CACHE and mt.shape[2] == MEL_CACHE,
              "and both tails are their fixed seam sizes",
              f"src {sc.shape} mel {mt.shape}")

        # A real two-chunk render, run the way the game will run it:
        # chunk 1 non-final (empty seam, lookahead trimmed, holdback kept),
        # then the final chunk rides in on chunk 1's tails. The lengths
        # must close exactly, and the seam must be CONSUMED — a dead cache
        # input is a click at every boundary that nothing else would name.
        pmel = pfeat.shape[1]
        # n1 = 8 of 9, not half: the small geometry must give the first
        # chunk more render than the holdback it keeps back, as every real
        # plan's first chunk has, or emit1 goes negative and the closing
        # check tests an impossible case.
        n1 = T - 1
        m1 = MELS_PER_TOKEN * (P + n1) - ahead - pmel
        assert m1 * SAMPLES_PER_MEL > SRC_CACHE, "test geometry too small"
        nz1 = draw(torch, P, pmel, n1, 11)
        nz1 = (nz1[0][:, :, :pmel + m1],
               nz1[1][:, :, :m1 * SAMPLES_PER_MEL])
        w1, s1, m1t = crun(tok[:, :n1], nz1, esrc, emel, 0, 0)
        check(w1.shape[1] == m1 * SAMPLES_PER_MEL,
              f"a first chunk renders exactly its {ahead}-mel-lookahead-"
              f"trimmed fresh, no ride-in",
              f"{w1.shape[1]} vs {m1 * SAMPLES_PER_MEL}")
        full_mels = MELS_PER_TOKEN * (P + T) - pmel
        nz2 = draw(torch, P, pmel, T, 11)
        nz2 = (nz2[0], nz2[1][:, :, m1 * SAMPLES_PER_MEL:])
        w2a, _, _ = crun(tok, nz2, s1, m1t, m1, 1)
        # Same call, same mel seam, DIFFERENT source cache — the pair that
        # proves cache_source is live. (cache_mel proves itself: the
        # render is a ride-in longer whenever it is present.)
        w2c, _, _ = crun(tok, nz2, esrc, m1t, m1, 1)
        # Caller algebra: chunk 1 emits its render minus the holdback; the
        # final chunk emits everything, its first SRC_CACHE samples
        # crossfading over the holdback.
        emit1 = w1.shape[1] - SRC_CACHE
        emit2 = w2a.shape[1]
        check(emit1 + emit2 == full_mels * SAMPLES_PER_MEL,
              "and the emitted stream closes to the whole line's count",
              f"{emit1}+{emit2} vs {full_mels * SAMPLES_PER_MEL}")
        check(float(np.abs(w2a - w2c).max()) > 0,
              "and the source seam is consumed — the same final chunk "
              "with a different cache differs, so the input is live")

    print(f"\nexport-decode --selftest: "
          f"{'PASS' if not fails else str(len(fails)) + ' FAILED'} — {len(ran)} checks "
          f"against a real flow decoder and the shipped vocoder")
    return 1 if fails else 0


def cmd_run(force=False, steps=4):
    # THE STEP COUNT IS PART OF WHAT "ALREADY DONE" MEANS. The skip compares
    # the exporter's own source against the last run's; a graph built with a
    # different number of solver steps is a different graph from identical
    # code, and skipping it would hand back the old one looking current.
    # The count is recorded in a sidecar and COMPARED — this line used to
    # read `steps == 10`, which was the default's value baked in prose, so
    # the day the default moved to four the skip quietly stopped firing and
    # every job re-paid minutes of export for graphs already on disk.
    done, src = already_done([OUT / "s3gen-decode.onnx",
                              OUT / "s3gen-chunk.onnx"])
    steps_file = OUT / "decode.steps"
    same_steps = steps_file.exists() and steps_file.read_text().strip() == str(steps)
    if done and same_steps and not force:
        print("  already exported by this same code at these steps — skipping.")
        print("  (delete the .onnx files, or pass --force, to redo it)")
        return 0
    stamp(f"started  src={src}  steps={steps}")
    import time
    import numpy as np
    import torch
    from chatterbox.tts import ChatterboxTTS

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import export_probe
    from export_probe import npy
    from stft_patch import patched

    ref = export_probe.reference(VOICE)
    if ref is None:
        print(f"  no reference clip for '{VOICE}'")
        return 1
    print(f"  voice: {VOICE} ({ref.name})")
    print("  loading the model...")
    model = export_probe.load_model("cpu")
    model.prepare_conditionals(str(ref))
    OUT.mkdir(parents=True, exist_ok=True)

    d = model.conds.gen
    ptok, pfeat = d["prompt_token"].cpu(), d["prompt_feat"].cpu()
    emb = d["embedding"].cpu()
    P, T = ptok.shape[1], 24
    tok = torch.randint(0, 6561, (1, T))
    noise = draw(torch, P, pfeat.shape[1], T, 20260808)
    print(f"  prompt {P} tokens, tracing on {T} speech tokens")

    t0 = time.time()
    dest = OUT / "s3gen-decode.onnx"
    args = (tok, ptok, pfeat, emb) + tuple(noise)
    with patched(), dynamic_cfm(torch), dynamic_flow(torch):
        dec = export_decode(torch, model.s3gen.flow, model.s3gen.mel2wav,
                            args, dest, steps)
    mb = sum(f.stat().st_size for f in OUT.glob("s3gen-decode*")) / (1024 * 1024)
    print(f"  exported in {time.time() - t0:.0f}s, {mb:.0f} MB -> {dest.name}")

    import onnxruntime as ort
    sess = ort.InferenceSession(str(dest), providers=["CPUExecutionProvider"])
    keys = ["tokens", "prompt_token", "prompt_feat", "embedding",
            "z", "sine_noise"]
    with torch.inference_mode(), dynamic_cfm(torch), dynamic_flow(torch):
        want = npy(dec(*args))
    got = sess.run(None, dict(zip(keys, [npy(t) for t in args])))[0]
    rel = float(np.abs(want - got).max()) / max(float(np.abs(want).max()), 1e-12)
    print(f"  agrees with pytorch to {rel:.1e} at the traced length "
          f"({got.shape[-1]} samples, {got.shape[-1] / 24000:.1f}s)")

    worst = 0.0
    for t in (8, 40):
        tk = torch.randint(0, 6561, (1, t))
        nz = draw(torch, P, MELS_PER_TOKEN * P, t, 5)
        with torch.inference_mode(), dynamic_cfm(torch), dynamic_flow(torch):
            w2 = npy(dec(tk, ptok, pfeat, emb, *nz))
        g2 = sess.run(None, dict(zip(keys, [npy(tk), npy(ptok), npy(pfeat),
                                            npy(emb)] + [npy(n) for n in nz])))[0]
        worst = max(worst, float(np.abs(w2 - g2).max())
                    / max(float(np.abs(w2).max()), 1e-12))
    print(f"  and to {worst:.1e} at two lengths it was NOT traced at")

    # THE NUMBER IN UNITS SOMEBODY CAN JUDGE. A relative disagreement means
    # nothing on its own; the same figure against the waveform's peak is a
    # count of 16-bit steps, and that is a statement about whether anyone
    # could hear it. The first real run read 7.0e-05 and 1.5e-04, which is
    # 2.3 and 4.9 steps — below anything audible in a game mix, and two orders
    # worse than the small-model check because the real graph is far deeper
    # and float32 error accumulates through it.
    import math
    print(f"  which is {20 * math.log10(max(worst, 1e-12)):.0f} dB below the "
          f"peak, about {worst * 32768:.1f} steps of 16-bit audio")

    # AND IT IS CHECKED RATHER THAN PRINTED, which it was not. The selftest
    # has bounded this at 1e-4 since it was written; the real run reported
    # 1.5e-4 and still said "finished", because nothing here read its own
    # output. A measurement no one gates on is a number in a log.
    #
    # The bound is 1e-3 — about thirty-two steps of 16-bit, still far below
    # audible — rather than the selftest's 1e-4, because the real graph is
    # legitimately noisier than the shrunk one and holding it to the smaller
    # model's figure would be a threshold set from the wrong subject. ONE run
    # is not a distribution: the value is printed every time so a series
    # accumulates, and this is a ceiling on "obviously broken" rather than a
    # claim about what is normal.
    if worst > 1e-3:
        print(f"  REFUSED: {worst:.1e} is too far from the original to trust "
              f"({worst * 32768:.0f} steps of 16-bit audio).")
        stamp(f"FAILED — disagreement {worst:.1e} above the 1e-3 ceiling")
        return 1

    # ---- THE STREAMING GRAPH, beside the whole-line one ----
    t0 = time.time()
    chunk_dest = OUT / "s3gen-chunk.onnx"
    off0 = torch.tensor(0, dtype=torch.long)
    fin1 = torch.tensor(1, dtype=torch.long)
    # Traced with a NONZERO seam cache so the source overwrite inside the
    # vocoder is not traced against a degenerate zero-length edge; the axis
    # is dynamic and the one-sample first-chunk case is what runs. The mel
    # seam is a FIXED (1,80,8) by design, so it is traced at its only size,
    # and the sine noise carries the seam's 3840 samples in front.
    seed_cache = torch.zeros(1, 1, 480)
    cargs = (tok, ptok, pfeat, emb,
             noise[0], pad_sine(torch, noise[1]),
             seed_cache, torch.zeros(1, 80, MEL_CACHE), off0, fin1)
    with patched(), dynamic_cfm(torch), dynamic_flow(torch):
        export_chunk(torch, model.s3gen.flow, model.s3gen.mel2wav,
                     cargs, chunk_dest, steps)
    cmb = sum(f.stat().st_size for f in OUT.glob("s3gen-chunk*")) / (1024 * 1024)
    print(f"  chunk graph exported in {time.time() - t0:.0f}s, {cmb:.0f} MB")

    csess = ort.InferenceSession(str(chunk_dest),
                                 providers=["CPUExecutionProvider"])
    # THE SELFTEST'S TWIN, and the twin is named: `cmd_selftest` has this
    # same driver against the small model, and the chunks-4 round trip died
    # on exactly this pair drifting — the signature grew `cache_mel` there
    # and not here. A feed change edits BOTH or fails on the PC.
    ckeys = ["tokens", "prompt_token", "prompt_feat", "embedding",
             "z", "sine_noise", "cache_source", "cache_mel",
             "mel_offset", "final"]

    def crun(tk, nz, csrc, cmel, off, fin):
        feed = dict(zip(ckeys, [npy(tk), npy(ptok), npy(pfeat), npy(emb),
                                npy(nz[0]),
                                npy(pad_sine(torch, nz[1], cmel.shape[2])),
                                csrc, cmel,
                                np.array(off, dtype=np.int64),
                                np.array(fin, dtype=np.int64)]))
        return csess.run(None, feed)

    SRC_CACHE = MEL_CACHE * SAMPLES_PER_MEL
    esrc = np.zeros((1, 1, 0), dtype=np.float32)   # see the selftest's note
    emel = np.zeros((1, 80, 0), dtype=np.float32)

    # THE ACCEPTING CASE FIRST: final, from the start, both caches EMPTY —
    # the identical computation to the whole-line graph, so the answer must
    # MATCH it, not resemble it. The model's own trim silences the first
    # 480 samples anyway, so the compare starts there. (The zeros-seam version bounded a decaying
    # residue; the real model's trained RNN carried it past one seam at
    # 8.2e-03 and this check refused the graph — chunks-5, 12 Aug.)
    wav_c, src_c, mel_t = crun(tok, noise, esrc, emel, 0, 1)
    scale = max(float(np.abs(got).max()), 1e-12)
    prof = [float(np.abs(wav_c[:, i * 480:(i + 1) * 480]
                         - got[:, i * 480:(i + 1) * 480]).max()) / scale
            for i in range(1, min(9, wav_c.shape[1] // 480))]
    print("  empty-seam residue per mel: "
          + " ".join(f"{v:.1e}" for v in prof))
    dwhole = float(np.abs(wav_c[:, 480:] - got[:, 480:]).max()) / scale
    print(f"  chunk(final,offset0,empty-seam) matches the whole graph from "
          f"sample 480 to {dwhole:.1e}")
    # 1e-3: separately-traced graphs carry ~4e-4 of fp32 trace noise; the
    # fault this catches (chunks-5's zeros-seam) measured 8.2e-03 and up.
    if wav_c.shape[1] != got.shape[1] or dwhole > 1e-3:
        print("  REFUSED: the chunk graph disagrees with the whole-line one "
              "on the identical question.")
        stamp(f"FAILED — chunk-vs-whole {dwhole:.1e} above 1e-4, "
              f"{wav_c.shape[1]} vs {got.shape[1]} samples")
        return 1

    # AND A REAL TWO-CHUNK RENDER, run the way the game will run it: a
    # first chunk on the empty seam, then the final riding its tails.
    # The emitted algebra must close and the seam must be demonstrably
    # CONSUMED — a dead cache input would ship a click at every boundary
    # and nothing else would say so.
    ahead = model.s3gen.flow.pre_lookahead_len * model.s3gen.flow.token_mel_ratio
    n1 = T // 2
    tk1 = tok[:, :n1]
    pmel = pfeat.shape[1]
    m1 = MELS_PER_TOKEN * (P + n1) - ahead - pmel
    nz1 = draw(torch, P, pmel, n1, 20260808)
    nz1 = (nz1[0][:, :, :pmel + m1], nz1[1][:, :, :m1 * SAMPLES_PER_MEL])
    w1, s1, m1t = crun(tk1, nz1, esrc, emel, 0, 0)
    ok1 = w1.shape[1] == m1 * SAMPLES_PER_MEL
    full_mels = MELS_PER_TOKEN * (P + T) - pmel
    nz2 = draw(torch, P, pmel, T, 20260808)
    # The sine noise covers the seam ride-in plus the FRESH samples — the
    # vocoder never re-sees the mels already emitted beyond its seam.
    nz2 = (nz2[0], nz2[1][:, :, m1 * SAMPLES_PER_MEL:])
    w2a, _, _ = crun(tok, nz2, s1, m1t, m1, 1)
    # Different source cache, same mel seam: the liveness pair. cache_mel
    # proves itself by the ride-in lengthening the render.
    w2c, _, _ = crun(tok, nz2, esrc, m1t, m1, 1)
    emit1 = w1.shape[1] - SRC_CACHE                 # the holdback
    emit2 = w2a.shape[1]                            # the final brings it home
    ok2 = emit1 + emit2 == full_mels * SAMPLES_PER_MEL
    seam_live = float(np.abs(w2a - w2c).max()) > 0
    print(f"  two chunks emit {emit1} + {emit2} samples "
          f"(algebra {'closes' if ok1 and ok2 else 'DOES NOT CLOSE'}), "
          f"seam {'consumed' if seam_live else 'DEAD'}")
    if not (ok1 and ok2 and seam_live):
        stamp("FAILED — chunk lengths or seam cache wrong; see output")
        return 1

    steps_file.write_text(str(steps), encoding="utf-8")
    print()
    stamp(f"finished  src={src} — {rel:.1e} traced, {worst:.1e} untraced, "
          f"{mb:.0f}+{cmb:.0f} MB, chunk {dwhole:.1e}")
    print("  ------------------------------------------------------------")
    print("  Tokens and a voice in, samples out — whole, or now in pieces:")
    print("  the chunk graph is what lets a character start talking before")
    print("  the sentence is finished computing.")
    print("  ------------------------------------------------------------")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="re-export even if it is already done")
    # HOW MANY STEPS THE FLOW SOLVER TAKES, and it is the biggest number in
    # this file. The solver's loop is UNROLLED into the traced graph, so ten
    # steps means ten copies of the estimator: it sets the file's size, the
    # ~200 seconds a session takes to open, and the seconds a line takes to
    # decode, all at once. Whether four sounds as good as ten is a question
    # for ears, not for me.
    # FOUR IS THE SHIPPED NUMBER NOW, AND THE DEFAULT HAD TO MOVE WITH IT.
    #
    # Jafar listened to four against ten and could not tell them apart, so
    # four is what this game uses: it opens the decode session in 38.7s
    # against 178-225s, and decodes a line in 1.6s against 3.4s.
    #
    # Leaving the default at ten would have been a trap of exactly the kind
    # this project keeps writing down. The next `export-graphs` run would
    # quietly rebuild at ten, nothing would fail, no check would go red, and
    # the three-minute startup would come back — to be rediscovered days
    # later by somebody wondering why it felt slow again.
    ap.add_argument("--steps", type=int, default=4,
                    help="flow solver steps baked into the graph (default 4, "
                         "was 10 until listening said four is the same)")
    ap.add_argument("--fromtemp", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    try:
        return cmd_run(a.force, a.steps)
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
