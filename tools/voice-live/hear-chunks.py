#!/usr/bin/env python3
"""ONE LINE RENDERED WHOLE AND THEN IN PIECES, so ears judge the seams.

    python3 tools/voice-live/hear-chunks.py            # needs all four graphs
    python3 tools/voice-live/hear-chunks.py --selftest  # needs nothing

The chunk graph's selftest proves the arithmetic: lengths close, the
lookahead trims, the seam cache is consumed. None of that says a boundary is
INAUDIBLE, and the whole reason the seam cache exists upstream is that a
boundary without it clicks. So this renders the sweep's nine-word line twice
— once through the whole-line graph, once through chunks the size the game
will stream — and writes both into one file with a gap between them. If the
second half has ticks the first half lacks, the seams are audible and the
chunk size or the cache handling is wrong; if the two halves sound alike,
streaming costs nothing the ear can hear.

AND IT TIMES WHAT LATENCY ACTUALLY BUYS. The per-chunk seconds are printed
as a series — first chunk first, because that number IS time-to-first-sound
once the step loop feeds tokens fast enough — and the chunk total beside the
whole-line cost, because the flow re-renders everything each chunk and that
overhead should be seen, not reasoned about.

THE CHUNK PLAN IS A PURE FUNCTION, deliberately: `plan_chunks` is the one
place the boundary arithmetic lives in python, `Core/SpeechStream` mirrors
it in C#, and the two carry each other's names so the next person greps
their way to the twin instead of discovering it after they differ.
"""
import argparse
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "tools" / "voice-live" / "game-out"
CONDS = ROOT / "game-design" / "voice-conds"
WAV = ROOT / "game-design" / "voice-live" / "chunked.wav"
REPORT = ROOT / "game-design" / "voice-live" / "chunk-report.txt"

START_SPEECH = 6561
STOP_SPEECH = 6562
CEILING = 1000
MELS_PER_TOKEN = 2
SAMPLES_PER_MEL = 480
LOOKAHEAD_TOKENS = 3          # flow.pre_lookahead_len, read off the model
VOICE = "rocco"
LINE = "Seen the van again. Thursday, same as last Thursday."
CHUNK_TOKENS = 24             # ~0.96s of audio a piece


def plan_chunks(n_tokens, chunk=CHUNK_TOKENS, lookahead=LOOKAHEAD_TOKENS):
    """Which decode calls a finished line of `n_tokens` becomes.

    Returns [(visible_tokens, mel_offset, final)] — each call sees the line
    up to `visible_tokens`, skips `mel_offset` mels already rendered, and
    only the final call keeps the last `lookahead` tokens' mels. Mirrored by
    `Core/SpeechStream.Plan`; change one and change the other.
    """
    if n_tokens <= 0:
        return []
    plan = []
    done = 0                        # mels already rendered
    seen = 0
    while True:
        seen = min(seen + chunk, n_tokens)
        final = seen >= n_tokens
        avail = MELS_PER_TOKEN * seen - (0 if final else MELS_PER_TOKEN * lookahead)
        if final or avail > done:
            plan.append((seen, done, final))
            done = avail
        if final:
            return plan


def say_lines(say, fp16=False):
    import numpy as np
    import onnxruntime as ort

    paths = {"t3-prefill": OUT / "t3-prefill.onnx",
             "t3-step": OUT / "t3-step.onnx",
             "s3gen-decode": OUT / "s3gen-decode.onnx",
             "s3gen-chunk": OUT / "s3gen-chunk.onnx"}
    missing = [p.name for p in paths.values() if not p.exists()]
    if missing:
        say(f"  no graphs on this machine: {', '.join(missing)}")
        return 1

    import importlib.util
    here = pathlib.Path(__file__).resolve().parent

    def by_path(name):
        spec = importlib.util.spec_from_file_location(name, here / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    sampler = by_path("crude_sampler")
    la = by_path("line_audio")

    z = np.load(CONDS / f"{VOICE}.npz")
    have = ort.get_available_providers()
    want = [p for p in ("DmlExecutionProvider", "CPUExecutionProvider")
            if p in have]
    say(f"  using: {want[0]}")
    t0 = time.time()
    sess = {k: ort.InferenceSession(str(v), providers=want)
            for k, v in paths.items()}
    say(f"  four sessions in {time.time() - t0:.1f}s")

    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(str(here / "tokenizer.json"))
    text = LINE
    try:
        from chatterbox.tts import punc_norm
        text = punc_norm(text)
    except Exception:
        say("  (chatterbox not importable — speaking the raw line)")
    ids = tok.encode(text.replace(" ", "[SPACE]"),
                     add_special_tokens=False).ids

    dt = {i.name: i.type for i in sess["t3-prefill"].get_inputs()}

    def as_np(name, arr):
        kind = {"tensor(int64)": np.int64, "tensor(int32)": np.int32,
                "tensor(float)": np.float32}[dt[name]]
        return np.asarray(arr).astype(kind, copy=False)

    # ---- the tokens, once — both renders speak the same take ----
    first = sess["t3-prefill"].run(None, {
        "text_tokens": as_np("text_tokens", [ids]),
        "speaker_emb": as_np("speaker_emb", z["t3.speaker_emb"]),
        "cond_speech_tokens": as_np("cond_speech_tokens",
                                    z["t3.cond_prompt_speech_tokens"]),
        "emotion_adv": as_np("emotion_adv", z["t3.emotion_adv"])})
    rows = int(first[0].shape[0])
    cache = first[1:]
    names = [f"cache{j}" for j in range(len(cache))]
    rng = np.random.default_rng(1001)
    said = set()
    tk = sampler.pick(np, first[0], rng, rows, said)
    said.add(tk)
    tokens = [] if tk in (START_SPEECH, STOP_SPEECH) else [tk]
    for step in range(1, CEILING + 1):
        if tk == STOP_SPEECH:
            break
        feed = dict(zip(names, cache))
        feed["token"] = np.array([[tk]], dtype=np.int64)
        feed["position"] = np.array(step, dtype=np.int64)
        got = sess["t3-step"].run(None, feed)
        cache = got[1:]
        tk = sampler.pick(np, got[0], rng, rows, said)
        said.add(tk)
        if tk < START_SPEECH:
            tokens.append(tk)
    say(f"  {len(tokens)} tokens for the line")

    pt = z["gen.prompt_token"]
    pf = z["gen.prompt_feat"]
    P = pt.shape[1]
    pmel = pf.shape[1]
    seed = np.random.default_rng(77)

    def gauss(shape):
        return seed.standard_normal(shape).astype(np.float32)

    def whole():
        n = len(tokens)
        h = MELS_PER_TOKEN * (P + n)
        wav = (h - pmel) * SAMPLES_PER_MEL
        t = time.time()
        w = sess["s3gen-decode"].run(None, {
            "tokens": np.array([tokens], dtype=np.int64),
            "prompt_token": pt.astype(np.int64),
            "prompt_feat": pf.astype(np.float32),
            "embedding": z["gen.embedding"].astype(np.float32),
            "z": gauss((1, 80, h)),
            "sine_noise": gauss((1, 9, wav))})[0][0]
        return w, time.time() - t

    def fit(cs, feed):
        """Cast the float feeds to whatever this session's inputs want.
        The fp16 graphs take float16 everywhere a float crosses; the seam
        tensors a session returns already carry its own dtype and pass
        back through untouched."""
        kinds = {i.name: i.type for i in cs.get_inputs()}
        return {k: (v.astype(np.float16)
                    if kinds.get(k) == "tensor(float16)"
                    and getattr(v, "dtype", None) == np.float32 else v)
                for k, v in feed.items()}

    def chunked(cs, graph_path, label):
        plan = plan_chunks(len(tokens))
        pieces, times = [], []
        # THE UPSTREAM SEAM: CosyVoice2's own design, traced. Eight cached
        # mels ride in front of every chunk after the first, only their
        # 3840 samples of source feed back, and the caller crossfades the
        # re-rendered seam over the tail it HELD BACK from the previous
        # chunk. The first call carries NOTHING — both caches empty, the
        # whole-line function exactly — because every approximation tried
        # in its place was measurable: eight zero mels perturbed the f0
        # RNN past one seam (chunks-5), one zero source sample rippled at
        # 1.2e-02 across the head (chunks-6). Whether DirectML accepts the
        # zero-length feeds is this trip's question, and the differential
        # below names the refuser if not.
        SRC = 8 * SAMPLES_PER_MEL
        window = np.hamming(2 * SRC).astype(np.float32)
        rise, fall = window[:SRC], window[SRC:]
        # Zero-LENGTH, matching the export checks: the first call is the
        # whole-line function with nothing added. Whether DirectML accepts
        # a zero-length cache here is exactly what the per-chunk
        # differential below answers — the one-sample version cost 1.2e-02
        # of head ripple on the real weights (chunks-6).
        src = np.zeros((1, 1, 0), dtype=np.float32)
        # EMPTY on the first call — the whole-line function exactly. The
        # zeros-seam version perturbed the real model's f0 RNN past one
        # seam (chunks-5) and the export guard refused it. If DirectML
        # refuses the empty CONCAT instead, the differential below names
        # it, which is this trip's question.
        cmel = np.zeros((1, 80, 0), dtype=np.float32)
        held = None
        # THE SAME FEED, BOTH PROVIDERS, kept from the differential run: a
        # call DirectML refuses is re-run, feed unchanged, on a CPU session
        # of the SAME graph, and the printout names who refused what.
        cpu = [None]

        def on_cpu(feed):
            if cpu[0] is None:
                say(f"    opening a CPU session of the {label} chunk graph "
                    "for the differential...")
                cpu[0] = ort.InferenceSession(
                    str(graph_path), providers=["CPUExecutionProvider"])
            return cpu[0].run(None, fit(cpu[0], feed))

        wore = []
        first_fresh = (MELS_PER_TOKEN * (P + plan[0][0])
                       - (0 if plan[0][2] else
                          MELS_PER_TOKEN * LOOKAHEAD_TOKENS)) - pmel
        assert first_fresh * SAMPLES_PER_MEL >= SRC or plan[0][2], \
            "the first chunk must out-render the holdback — grow the " \
            "first chunk"
        for visible, offset, final in plan:
            h = MELS_PER_TOKEN * (P + visible) \
                - (0 if final else MELS_PER_TOKEN * LOOKAHEAD_TOKENS)
            fresh = (h - pmel) - offset
            # The ride-in region's sine noise is zeros in front (its source
            # is overwritten by the cache); an empty first-call seam pads
            # nothing.
            ride = cmel.shape[2] * SAMPLES_PER_MEL
            sine = np.concatenate(
                [np.zeros((1, 9, ride), dtype=np.float32),
                 gauss((1, 9, fresh * SAMPLES_PER_MEL))], axis=2) \
                if ride else gauss((1, 9, fresh * SAMPLES_PER_MEL))
            feed = {
                "tokens": np.array([tokens[:visible]], dtype=np.int64),
                "prompt_token": pt.astype(np.int64),
                "prompt_feat": pf.astype(np.float32),
                "embedding": z["gen.embedding"].astype(np.float32),
                "z": gauss((1, 80, h)),
                "sine_noise": sine,
                "cache_source": src,
                "cache_mel": cmel,
                "mel_offset": np.array(offset, dtype=np.int64),
                "final": np.array(1 if final else 0, dtype=np.int64)}
            say(f"    chunk visible={visible} offset={offset} final={final} "
                f"cache={src.shape} z={feed['z'].shape} noise={sine.shape}")
            t = time.time()
            try:
                w, src, cmel = cs.run(None, fit(cs, feed))
                wore.append("dml")
            except Exception as e:
                say(f"    DML REFUSED: {str(e).splitlines()[0][:180]}")
                try:
                    w, src, cmel = on_cpu(feed)
                    wore.append("cpu")
                    say("    and the CPU session ACCEPTED the identical "
                        "feed — the provider is the refuser, not the graph")
                except Exception as e2:
                    say(f"    CPU ALSO REFUSED: "
                        f"{str(e2).splitlines()[0][:180]}")
                    say("    both providers refuse this feed — the GRAPH "
                        "is wrong, and the shapes above are the case")
                    raise
            times.append(time.time() - t)
            w = w[0]
            if held is not None:
                w = w.copy()
                w[:SRC] = w[:SRC] * rise + held * fall
            if final:
                pieces.append(w)
            else:
                pieces.append(w[:-SRC])
                held = w[-SRC:]
        say("    providers used per chunk: " + "/".join(wore))
        return np.concatenate(pieces).astype(np.float32), times, plan

    w_whole, t_whole = whole()
    w_chunk, times, plan = chunked(sess["s3gen-chunk"],
                                   paths["s3gen-chunk"], "fp32")
    say(f"  whole: {t_whole:.2f}s for {len(w_whole) / 24000:.1f}s of speech")
    say(f"  chunks: {len(plan)} pieces "
        + "/".join(f"{t:.2f}" for t in times)
        + f"s (first piece {times[0]:.2f}s — that is time-to-first-sound's "
        "decode share)")
    say(f"  chunk total {sum(times):.2f}s vs whole {t_whole:.2f}s — the "
        f"re-render overhead is {sum(times) - t_whole:+.2f}s")
    if len(w_chunk) != len(w_whole):
        say(f"  LENGTHS DIFFER: chunked {len(w_chunk)} vs whole "
            f"{len(w_whole)} samples — the plan is wrong, do not listen yet")
        return 1

    # THE FP16 LEVER, A/B'd IN THE SAME TRIP when the halved graph is on
    # disk (convert-fp16 --only s3gen). Same tokens, same noise seeds,
    # same plan — the only variable is the arithmetic's width, so the
    # timing gap is the lever's worth and the third wav segment is its
    # price in sound.
    w_16 = None
    fp16_path = OUT / "s3gen-chunk-fp16.onnx"
    if fp16_path.exists():
        t0 = time.time()
        cs16 = ort.InferenceSession(str(fp16_path), providers=want)
        say(f"  fp16 chunk session in {time.time() - t0:.1f}s")
        w_16, t16, _ = chunked(cs16, fp16_path, "fp16")
        say(f"  fp16 chunks: " + "/".join(f"{t:.2f}" for t in t16)
            + f"s — total {sum(t16):.2f}s vs fp32's {sum(times):.2f}s")
        drel = float(np.abs(w_16 - w_chunk).max())             / max(float(np.abs(w_chunk).max()), 1e-9)
        say(f"  fp16 waveform sits {drel:.1%} of full scale from fp32 — "
            f"the third segment is the ear's judge")
        if len(w_16) != len(w_chunk):
            say(f"  FP16 LENGTHS DIFFER: {len(w_16)} vs {len(w_chunk)} — "
                f"not writing its segment")
            w_16 = None
    else:
        say("  (no s3gen-chunk-fp16.onnx — run convert-fp16 --only s3gen "
            "for the A/B)")

    gap = np.zeros(12000, dtype=np.float32)
    both = np.concatenate([la.lead(np, np.float32),
                           la.feather(np, w_whole.copy()), gap,
                           la.feather(np, w_chunk.copy())]
                          + ([gap, la.feather(np, w_16.copy())]
                             if w_16 is not None else []))
    peak = float(np.abs(both).max())
    if peak > 0:
        both = both * (0.85 / peak)
    import wave
    import struct
    WAV.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(WAV), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(24000)
        f.writeframes(struct.pack(f"<{len(both)}h",
                                  *(both * 32767).astype(np.int16)))
    say(f"  wrote chunked.wav — the line WHOLE, a breath, the same line "
        f"in {len(plan)} chunks"
        + (", a breath, and the chunks again in fp16"
           if w_16 is not None else "")
        + ". If a later copy ticks or hisses where the first is clean, "
          "say which; if you cannot tell them apart, the lever is free.")
    return 0


def selftest():
    fails, ran = [], []

    def check(ok, what, got=""):
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}" + ("" if ok else f" — {got}"))
        ran.append(what)
        if not ok:
            fails.append(what)

    # The plan's arithmetic, on the cases the game will actually hit.
    p = plan_chunks(86)
    check(p[-1][2] and p[-1][0] == 86,
          "the final chunk sees every token", str(p[-1]))
    check(all(not f for _, _, f in p[:-1]),
          "and only the final chunk is final")
    mels = 0
    ok_cover = True
    for visible, offset, final in p:
        if offset != mels:
            ok_cover = False
        mels = MELS_PER_TOKEN * visible \
            - (0 if final else MELS_PER_TOKEN * LOOKAHEAD_TOKENS)
    check(ok_cover and mels == MELS_PER_TOKEN * 86,
          "every mel is rendered exactly once across the plan",
          f"ended at {mels} of {MELS_PER_TOKEN * 86}")
    check(all(p[i][1] < p[i + 1][1] for i in range(len(p) - 1)),
          "and offsets strictly advance — no chunk re-says a mel")

    check(plan_chunks(5) == [(5, 0, True)],
          "a line shorter than one chunk is a single final call",
          str(plan_chunks(5)))
    check(plan_chunks(24) == [(24, 0, True)],
          "a line of exactly one chunk is a single final call",
          str(plan_chunks(24)))
    check(plan_chunks(0) == [], "and an empty line plans nothing")
    # 25 tokens: first chunk holds back the 3-token lookahead, the final
    # call releases it plus the one new token.
    check(plan_chunks(25) == [(24, 0, False), (25, 42, True)],
          "a one-token tail still gets a final call that releases the "
          "held-back lookahead", str(plan_chunks(25)))

    # The refusal names what is absent, per rule 3b.
    global OUT
    keep = OUT
    try:
        OUT = pathlib.Path("/nonexistent-graphs")
        said = []
        rc = say_lines(said.append)
        check(rc == 1 and any("s3gen-chunk" in s for s in said),
              "with no graphs it names every missing file rather than "
              "throwing", "; ".join(said))
    finally:
        OUT = keep

    print(f"\nhear-chunks --selftest: "
          f"{'PASS' if not fails else str(len(fails)) + ' FAILED'} — "
          f"{len(ran)} checks")
    return 0 if not fails else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    lines = []

    def say(s):
        print(s)
        lines.append(s)

    rc = say_lines(say)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    sys.exit(main())
