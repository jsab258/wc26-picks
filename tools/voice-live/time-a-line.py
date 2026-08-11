#!/usr/bin/env python3
"""HOW LONG DOES ONE LINE ACTUALLY TAKE, ON THE REAL RUNTIME.

    python3 tools/voice-live/time-a-line.py

THE ONE NUMBER THAT DECIDES WHETHER ANY OF THIS SHIPS. Everything else about
live speech is now built and checked: three graphs that agree with the
original, a loop that conforms to the model's own sampler, routing, a queue, a
worker, a backend that compiles. None of it matters if a character takes
fifteen seconds to say six words.

WHAT WE HAVE INSTEAD OF A MEASUREMENT. 11.9 seconds for ~3.5s of speech, in
PyTorch, on a CPU, in a Python process — measured on 7 August and quoted ever
since as though it described the game. It does not. It is a different runtime,
a different precision path, and it does not touch the graphs that actually
ship. Reading it as the game's number is the peak-for-a-median mistake wearing
different clothes.

So this runs the SHIPPED graphs through onnxruntime the way the game will:
prefill once, step until the model stops, decode the tokens to samples. The
sampler here is deliberately crude — the timing question does not care which
token wins, only how many steps happen and how long each takes — and the step
count is reported beside the time so the two cannot be confused.

IT REPORTS WHICH PROVIDER RAN, which is not a detail. The probe measured the
CPU beating DirectML 4.4x per step on this model and nobody has explained it;
a timing with no provider named is a number that cannot be compared to the
next one.

AND IT SENDS ITSELF BACK, into `game-design/voice-live/speed-report.txt`, for
the reason every other measurement here does: an answer that travels by hand
eventually does not arrive.
"""
import argparse
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "tools" / "voice-live" / "game-out"
CONDS = ROOT / "game-design" / "voice-conds"
REPORT = ROOT / "game-design" / "voice-live" / "speed-report.txt"
VOICE = "rocco"
LINE = "Seen the van again. Thursday, same as last Thursday."

# From `Core/SpeechVocab` — the same constants the C# uses.
START_SPEECH = 6561
STOP_SPEECH = 6562
CEILING = 1000


def pick(np, logits, rng, rows):
    """A token, cheaply. NOT the shipped sampler.

    The C# does classifier-free guidance, a repetition penalty, temperature,
    and min-p, and `sampler-reference.py` proves it matches the model's own to
    1e-5. None of that changes how long a step TAKES, and reimplementing it
    here would be a third copy of a thing that has already gone subtly wrong
    twice. The guidance combination is kept because it decides which token
    comes out, and therefore how many steps a line runs for — which is half
    the answer being measured.
    """
    v = logits.reshape(rows, -1)
    x = v[0] + 0.5 * (v[0] - v[1]) if rows > 1 else v[0]
    x = x / 0.8
    x = x - x.max()
    p = np.exp(x)
    p[p < 0.05 * p.max()] = 0.0        # min_p, roughly
    s = p.sum()
    if s <= 0:
        return int(np.argmax(x))
    return int(rng.choice(len(p), p=p / s))


def run(say):
    import numpy as np
    import onnxruntime as ort

    paths = {n: OUT / f"{n}.onnx"
             for n in ("t3-prefill", "t3-step", "s3gen-decode")}
    missing = [p.name for p in paths.values() if not p.exists()]
    if missing:
        say(f"  no graphs on this machine: {', '.join(missing)}")
        say("  run '5 EXPORT FOR THE GAME.bat' first.")
        return 1

    have = ort.get_available_providers()
    want = [p for p in ("DmlExecutionProvider", "CUDAExecutionProvider",
                        "CPUExecutionProvider") if p in have]
    say(f"  providers available: {', '.join(have)}")
    say(f"  using: {want[0]}")

    # EACH SESSION TIMED SEPARATELY. "Three sessions opened in 201s" says
    # startup is unacceptable and not which file caused it — and they are
    # 2001 MB, 1941 MB and 540 MB, so the answer is not obvious from size.
    sess, opened = {}, {}
    for k, v in paths.items():
        t0 = time.time()
        sess[k] = ort.InferenceSession(str(v), providers=want)
        opened[k] = time.time() - t0
        say(f"  opened {k} in {opened[k]:.1f}s")
    say(f"  three sessions in {sum(opened.values()):.1f}s total")

    z = np.load(CONDS / f"{VOICE}.npz")
    dt = {i.name: i.type for i in sess["t3-prefill"].get_inputs()}

    def as_np(name, arr):
        kind = {"tensor(int64)": np.int64, "tensor(int32)": np.int32,
                "tensor(float)": np.float32}[dt[name]]
        return np.asarray(arr).astype(kind, copy=False)

    # THE SHIPPED VOCABULARY, AND THE MODEL'S OWN TEXT TIDY-UP WHEN IT IS
    # IMPORTABLE. `Core/SpeechText` ports `punc_norm` and matches it on
    # fourteen inputs; using the original here keeps this measurement from
    # depending on that port being right, which is a separate question.
    from tokenizers import Tokenizer
    here = pathlib.Path(__file__).resolve().parent
    text = LINE
    try:
        from chatterbox.models.t3.modules.t3_config import T3Config  # noqa: F401
        from chatterbox.tts import punc_norm
        text = punc_norm(text)
    except Exception:
        say("  (chatterbox not importable — timing the raw line, unnormalised)")
    tok_json = here / "tokenizer.json"
    if not tok_json.exists():
        say(f"  no vocabulary at {tok_json}")
        return 1
    ids = Tokenizer.from_file(str(tok_json)).encode(
        text.replace(" ", "[SPACE]"), add_special_tokens=False).ids
    say(f"  the line is {len(ids)} tokens: \"{LINE}\"")

    t0 = time.time()
    cache = sess["t3-prefill"].run(None, {
        "text_tokens": as_np("text_tokens", [ids]),
        "speaker_emb": as_np("speaker_emb", z["t3.speaker_emb"]),
        "cond_speech_tokens": as_np("cond_speech_tokens",
                                    z["t3.cond_prompt_speech_tokens"]),
        "emotion_adv": as_np("emotion_adv", z["t3.emotion_adv"])})
    prefill = time.time() - t0
    say(f"  prefill: {prefill:.2f}s")

    rng = np.random.default_rng(7)
    names = [f"cache{i}" for i in range(len(cache))]
    rows = 2
    tok, tokens, per_step = START_SPEECH, [], []
    t_loop = time.time()
    for step in range(1, CEILING + 1):
        feed = dict(zip(names, cache))
        feed["token"] = np.array([[tok]], dtype=np.int64)
        feed["position"] = np.array(step, dtype=np.int64)
        t1 = time.time()
        got = sess["t3-step"].run(None, feed)
        per_step.append(time.time() - t1)
        cache = got[1:]
        tok = pick(np, got[0].astype(np.float64), rng, rows)
        if tok == STOP_SPEECH:
            break
        if tok < START_SPEECH:
            tokens.append(tok)
    loop = time.time() - t_loop

    # THE SERIES, NOT JUST THE MEAN. A first step that pays for a warm-up and
    # three hundred that do not is two populations, and a mean hides which.
    ps = np.array(per_step)
    say(f"  {len(per_step)} steps in {loop:.1f}s — first {ps[0] * 1000:.0f}ms, "
        f"median {np.median(ps) * 1000:.0f}ms, "
        f"slowest {ps.max() * 1000:.0f}ms")
    say(f"  {len(tokens)} acoustic tokens kept")

    if not tokens:
        say("  nothing to decode — the loop produced no acoustic tokens.")
        return 1

    n_p = z["gen.prompt_token"].shape[1]
    n_pm = z["gen.prompt_feat"].shape[1]
    h = 2 * (n_p + len(tokens))
    wav_len = (h - n_pm) * 480
    # THE SAME INPUT FOR BOTH PROVIDERS. Redrawing the noise would time two
    # different pieces of work and call the difference a provider.
    feed_decode = {
        "tokens": np.asarray([tokens], dtype=np.int64),
        "prompt_token": z["gen.prompt_token"].astype(np.int64),
        "prompt_feat": z["gen.prompt_feat"].astype(np.float32),
        "embedding": z["gen.embedding"].astype(np.float32),
        "z": rng.standard_normal((1, 80, h)).astype(np.float32),
        "sine_noise": rng.standard_normal((1, 9, wav_len)).astype(np.float32)}
    t2 = time.time()
    wav = sess["s3gen-decode"].run(None, feed_decode)[0]
    decode = time.time() - t2

    # THE DECODE, ON THE OTHER PROVIDER TOO — the experiment this run exists
    # for. The talking stage came out 3.5x FASTER than PyTorch and the decode
    # 3x slower, which is not a conversion cost; it is one stage disagreeing
    # with one provider. The probe already saw the CPU beat DirectML 4.4x per
    # step on the text model and nobody explained it, so this asks the same
    # question of the stage that is now the bottleneck.
    #
    # The session is opened and timed separately, because "the CPU decodes
    # faster" is only useful if opening a second session does not cost more
    # than it saves at startup.
    if want[0] != "CPUExecutionProvider":
        try:
            t3 = time.time()
            cpu = ort.InferenceSession(str(paths["s3gen-decode"]),
                                       providers=["CPUExecutionProvider"])
            cpu_open = time.time() - t3
            t4 = time.time()
            cpu.run(None, feed_decode)
            cpu_decode = time.time() - t4
            say(f"  decode on CPU: {cpu_decode:.2f}s "
                f"(session opened in {cpu_open:.1f}s)")
            # THE RATIO THE RIGHT WAY ROUND. The first version printed
            # "the CPU is 0.3x slower", which is the reciprocal of what it
            # meant and reads as a mild difference when the truth was 3.2x —
            # a number that misreports is worse than no number, and this one
            # was about to settle a design decision.
            if cpu_decode < decode:
                say(f"  -> the CPU is {decode / max(cpu_decode, 1e-6):.1f}x "
                    f"FASTER at this stage")
            else:
                say(f"  -> the CPU is {cpu_decode / max(decode, 1e-6):.1f}x "
                    f"SLOWER at this stage — DirectML is the right place "
                    f"for it")
        except Exception as e:
            say(f"  decode on CPU: could not run — {type(e).__name__}: {e}")

    seconds = wav.shape[-1] / 24000.0
    total = prefill + loop + decode
    say(f"  decode: {decode:.2f}s for {seconds:.1f}s of audio")
    say("")
    say(f"  ONE LINE: {total:.1f}s of work for {seconds:.1f}s of speech "
        f"— {total / max(seconds, 1e-6):.1f}x real time")
    say(f"  split: prefill {prefill:.1f}s, {len(per_step)} steps {loop:.1f}s, "
        f"decode {decode:.1f}s")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fromtemp", action="store_true", help=argparse.SUPPRESS)
    ap.parse_args()

    import getpass
    import platform
    import socket
    from datetime import datetime, timezone
    lines = []

    def say(s):
        print(s)
        lines.append(s)

    say("LEDGER — how long one spoken line actually takes")
    say(f"ran on {socket.gethostname()} ({platform.system()}) as "
        f"{getpass.getuser()}, {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    say("")
    try:
        rc = run(say)
    except Exception as e:
        import traceback
        say(f"  CRASHED  {type(e).__name__}: {e}")
        for l in traceback.format_exc().splitlines():
            say("    " + l)
        rc = 1
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n  written to {REPORT.name}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
