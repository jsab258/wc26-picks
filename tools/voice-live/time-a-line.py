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

IT REPORTS WHICH PROVIDER RAN, which is not a detail — and it now MEASURES
both rather than reporting one. An early probe read the CPU beating DirectML
4.4x per step, on a different graph, and that number was quoted for days. On
the graphs that ship the card is 1.3x faster per step and 3.5x faster at the
decode, so both stages stay on it. A timing with no provider named is a number
that cannot be compared to the next one; a provider chosen from a stale reading
is worse.

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


def _shared_pick():
    """The sampler lives in `crude_sampler.py`, shared with `speak-a-few`.

    It was duplicated here without a repetition penalty, and that absence
    invalidated a whole experiment — see the module's header. The penalty also
    changes HOW MANY steps a line runs, which is half of what this tool
    measures, so a timing without it times lines that cannot happen.
    """
    import importlib.util
    here = pathlib.Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("crude_sampler",
                                                  here / "crude_sampler.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.pick


def run(say, fp16=False):
    import numpy as np
    import onnxruntime as ort

    # THE TEXT GRAPHS SWAP FOR THEIR HALVES UNDER --fp16; the decode stays
    # fp32 — it was never the bandwidth problem and one variable moves at a
    # time.
    suf = "-fp16" if fp16 else ""
    paths = {"t3-prefill": OUT / f"t3-prefill{suf}.onnx",
             "t3-step": OUT / f"t3-step{suf}.onnx",
             "s3gen-decode": OUT / "s3gen-decode.onnx"}
    missing = [p.name for p in paths.values() if not p.exists()]
    if missing:
        say(f"  no graphs on this machine: {', '.join(missing)}")
        say("  run '5 EXPORT FOR THE GAME.bat' first"
            + (" and then convert-fp16.py" if fp16 else "") + ".")
        return 1
    if fp16:
        say("  TEXT GRAPHS: FP16 — this run measures lever B")

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
                "tensor(float)": np.float32,
                "tensor(float16)": np.float16}[dt[name]]
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
    first = sess["t3-prefill"].run(None, {
        "text_tokens": as_np("text_tokens", [ids]),
        "speaker_emb": as_np("speaker_emb", z["t3.speaker_emb"]),
        "cond_speech_tokens": as_np("cond_speech_tokens",
                                    z["t3.cond_prompt_speech_tokens"]),
        "emotion_adv": as_np("emotion_adv", z["t3.emotion_adv"])})
    prefill = time.time() - t0
    # TWICE, because the fp16 run measured 1.06s against fp32's 0.30s and one
    # run cannot say whether that is the graph or one-time kernel warm-up.
    # The second run is the discriminator: if it comes back near fp32's
    # number, the cost is warm-up and the game can pay it once at load with a
    # throwaway prefill; if it stays high, the converter's inserted casts are
    # in the conditioning path and lever B owes an investigation.
    t0b = time.time()
    sess["t3-prefill"].run(None, {
        "text_tokens": as_np("text_tokens", [ids]),
        "speaker_emb": as_np("speaker_emb", z["t3.speaker_emb"]),
        "cond_speech_tokens": as_np("cond_speech_tokens",
                                    z["t3.cond_prompt_speech_tokens"]),
        "emotion_adv": as_np("emotion_adv", z["t3.emotion_adv"])})
    prefill2 = time.time() - t0b
    say(f"  prefill: {prefill:.2f}s (second run {prefill2:.2f}s — the gap "
        f"between them is one-time warm-up, the second is the real cost)")

    pick = _shared_pick()
    said = set()
    rng = np.random.default_rng(7)
    # THE FIRST TOKEN COMES OUT OF THE PREFILL, and the version that did not
    # take it is what Jafar heard: the line started at "van again" instead of
    # "Seen the van again". Running the whole sentence through the model
    # produces the odds for the first spoken token as a by-product; a loop
    # that ignores them has to feed the start token a second time to get
    # something back, which embeds it twice, shifts every position by one and
    # drops the token the model had already chosen. Nothing numerical could
    # see it — both sides agreed about the values that were there.
    cache = first[1:]
    names = [f"cache{i}" for i in range(len(cache))]
    # READ OFF THE GRAPH, NOT ASSUMED. This was 2, which was true of every
    # graph that had ever existed — and the moment a one-row export was
    # possible an assumed 2 would have reshaped the odds into two half-rows
    # and sampled from nonsense, quietly, with a plausible-sounding line
    # coming out the other end.
    rows = int(first[0].shape[0])
    say(f"  the graph gives {rows} row(s) of odds"
        + (" — classifier-free guidance" if rows > 1 else " — no guidance"))
    tok = pick(np, first[0], rng, rows, said)
    said.add(tok)
    tokens = [] if tok in (START_SPEECH, STOP_SPEECH) else [tok]
    per_step = []
    t_loop = time.time()
    for step in range(1, CEILING + 1):
        # THE STOP IS TESTED BEFORE THE TOKEN IS FED, not after it is drawn,
        # because the first token now arrives from outside this loop and a
        # test that only ran at the bottom would feed the stop marker back
        # into the model on a one-token line.
        if tok == STOP_SPEECH:
            break
        feed = dict(zip(names, cache))
        feed["token"] = np.array([[tok]], dtype=np.int64)
        feed["position"] = np.array(step, dtype=np.int64)
        t1 = time.time()
        got = sess["t3-step"].run(None, feed)
        per_step.append(time.time() - t1)
        cache = got[1:]
        tok = pick(np, got[0], rng, rows, said)
        said.add(tok)
        if tok < START_SPEECH:
            tokens.append(tok)
    loop = time.time() - t_loop

    # THE SERIES, NOT JUST THE MEAN. A first step that pays for a warm-up and
    # three hundred that do not is two populations, and a mean hides which.
    if not per_step:
        say("  the prefill's first token was the stop marker — no steps ran.")
        return 1
    ps = np.array(per_step)
    say(f"  {len(per_step)} steps in {loop:.1f}s — first {ps[0] * 1000:.0f}ms, "
        f"median {np.median(ps) * 1000:.0f}ms, "
        f"slowest {ps.max() * 1000:.0f}ms")
    say(f"  {len(tokens)} acoustic tokens kept")

    # ---- AND THE STEP LOOP IS NOW THE BOTTLENECK, so ask it the same
    # ---- question the decode was asked.
    #
    # With four solver steps the decode is 1.6s of a line and these 86 steps
    # are 3.5-4.7s. The old probe measured the CPU beating DirectML 4.4x PER
    # STEP on the text model and nobody ever explained it or re-checked it on
    # the graphs that actually ship. If it still holds, the text stage belongs
    # on the CPU and the decode on the card, which is a shipping decision
    # nobody can make without this number.
    #
    # TEN STEPS, ON THE CACHE THE REAL LINE ENDED WITH, so the comparison is
    # made where the work is heaviest rather than at position one.
    if want[0] != "CPUExecutionProvider":
        try:
            t0 = time.time()
            cpu_step = ort.InferenceSession(str(paths["t3-step"]),
                                            providers=["CPUExecutionProvider"])
            cpu_open = time.time() - t0
            probe = dict(zip(names, cache))
            probe["token"] = np.array([[7]], dtype=np.int64)
            probe["position"] = np.array(len(per_step), dtype=np.int64)
            here, there = [], []
            for _ in range(10):
                t0 = time.time()
                sess["t3-step"].run(None, probe)
                here.append(time.time() - t0)
                t0 = time.time()
                cpu_step.run(None, probe)
                there.append(time.time() - t0)
            # MEDIAN, NOT MEAN. One scheduling hiccup in ten runs moves a mean
            # and cannot move a median, and this number decides where a stage
            # runs.
            a = float(np.median(here)) * 1000
            b = float(np.median(there)) * 1000
            say(f"  one step, {want[0].replace('ExecutionProvider','')}: "
                f"{a:.0f}ms   CPU: {b:.0f}ms   (CPU session opened in "
                f"{cpu_open:.1f}s)")
            if b < a * 0.9:
                say(f"  -> the CPU is {a / max(b, 1e-6):.1f}x FASTER per step "
                    f"— the text stage belongs there, and a whole line would "
                    f"take {b * len(per_step) / 1000:.1f}s instead of "
                    f"{a * len(per_step) / 1000:.1f}s")
            elif a < b * 0.9:
                say(f"  -> the card is {b / max(a, 1e-6):.1f}x faster per step; "
                    f"the old 4.4x CPU reading does not hold on these graphs")
            else:
                say("  -> the two are within 10% of each other per step")
        except Exception as e:
            say(f"  one step on CPU: could not run — {type(e).__name__}: {e}")

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
    # with one provider. Asked of both stages now, and both answered the same
    # way: the card wins. The old probe's 4.4x reading for the CPU was taken
    # on a different graph and does not survive contact with these.
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

    # KEEP THE WAVEFORM. The graphs agree with the original to six decimal
    # places and NOBODY HAS HEARD THEM. Those are different claims: a wrong
    # position, a frozen voice or a mangled decode can all sit inside a tiny
    # numerical difference, and the one test that catches all three at once is
    # a person listening for five seconds. This tool was already producing the
    # audio and discarding it, which is the same waste as measuring a room and
    # not looking at it.
    import struct
    import wave
    # THE SHARED TREATMENT, not a fourth copy. The cold-vocoder click was
    # fixed in Core and in speak-a-few, and the next file Jafar heard came
    # from HERE, raw — the grep-for-the-twin rule, missed again and paid for
    # again. `line_audio.feather` is the one implementation now.
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        "line_audio", pathlib.Path(__file__).resolve().parent / "line_audio.py")
    _la = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_la)
    out = REPORT.parent / "spoken.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    flat = np.asarray(wav).reshape(-1).astype(np.float64).copy()
    flat = _la.feather(np, flat)
    flat = np.concatenate([_la.lead(np, flat.dtype), flat])
    flat = np.clip(flat, -1.0, 1.0)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)          # s3gen's own rate; a wrong one is a
        w.writeframes(struct.pack(     # chipmunk rather than an error
            "<%dh" % len(flat), *(int(v * 32767) for v in flat)))
    say(f"  wrote {out.name} — {out.stat().st_size / 1024:.0f} KB, "
        f"{len(flat) / 24000:.1f}s, through the SHIPPED graphs")

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
    # THE FLAG THE FIRST WIRING SILENTLY LOST. The edit script anchored on a
    # --selftest block this file does not have, str.replace no-ops on a
    # missing needle, and the harness printed "wired" unconditionally — so
    # the job crossed to the other machine to fail on argparse. An edit is
    # verified by GREPPING THE RESULT, not by the editor saying it ran.
    ap.add_argument("--fp16", action="store_true",
                    help="time the fp16 text graphs (lever B)")
    a = ap.parse_args()

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
        rc = run(say, a.fp16)
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
