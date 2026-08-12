#!/usr/bin/env python3
"""SEVERAL LINES, MORE THAN ONE VOICE, ONE FILE TO PLAY.

    python3 tools/voice-live/speak-a-few.py

ONE LINE IN ONE VOICE IS ONE SAMPLE. The no-guidance graph was approved off a
single sentence spoken by Rocco, and the fault guidance exists to prevent —
the model wandering off the words without its second opinion — is exactly the
kind that shows up on the fourth line rather than the first. A decision taken
from one reading is this project's oldest mistake wearing new clothes.

So this speaks a handful of lines across the voices that are precomputed, and
writes them as ONE waveform with a gap between each. One file to play, because
a listening test that needs six double-clicks is a listening test that gets
done once.

THE SAME CRUDE SAMPLER `time-a-line` USES, deliberately. Every judgement made
so far has been on that sampler's output, and swapping in a better one here
would mean the comparison is against something nobody has heard. It is not the
shipped sampler — `Core/SpeechLoop` is, and it matches the model's own to 1e-5
— but it is the one these ears are calibrated to.

THE LINES ARE CHOSEN TO BE AWKWARD. A number, a name, a question, a short
mutter and a long sentence: the model has more ways to go wrong on those than
on a comfortable declarative, and a test made of comfortable declaratives
proves that comfortable declaratives work.
"""
import argparse
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "tools" / "voice-live" / "game-out"
CONDS = ROOT / "game-design" / "voice-conds"
WAV = ROOT / "game-design" / "voice-live" / "spoken.wav"
REPORT = ROOT / "game-design" / "voice-live" / "speed-report.txt"

START_SPEECH = 6561
STOP_SPEECH = 6562
CEILING = 1000
GAP_SECONDS = 0.5

LINES = [
    "No.",
    "Seen the van again. Thursday, same as last Thursday.",
    "You want me to say that in front of Rocco?",
    "Forty-two crates, and not one of them opened where I could see it.",
    "I was nowhere near the yard, and you know it, and so does he.",
]


def _by_path(name):
    import importlib.util
    here = pathlib.Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location(name, here / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_la = _by_path("line_audio")


def _shared_pick():
    """Shared with `time-a-line` — see `crude_sampler.py` for why the
    repetition penalty is not optional in a listening tool."""
    import importlib.util
    here = pathlib.Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("crude_sampler",
                                                  here / "crude_sampler.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(say):
    import numpy as np
    import onnxruntime as ort

    paths = {n: OUT / f"{n}.onnx"
             for n in ("t3-prefill", "t3-step", "s3gen-decode")}
    missing = [p.name for p in paths.values() if not p.exists()]
    if missing:
        say(f"  no graphs on this machine: {', '.join(missing)}")
        return 1
    sampler = _shared_pick()
    voices = sorted(p.stem for p in CONDS.glob("*.npz"))
    if not voices:
        say(f"  no precomputed voices in {CONDS}")
        return 1
    # A DENOMINATOR ON THE CAST. "It sounded fine" from one voice is the
    # finding this file exists to stop being made again.
    chosen = [v for v in ("rocco", "ada", "michelle") if v in voices][:3]
    if len(chosen) < 2:
        chosen = voices[:3]
    say(f"  {len(voices)} voices precomputed, speaking with {len(chosen)}: "
        + ", ".join(chosen))

    have = ort.get_available_providers()
    want = [p for p in ("DmlExecutionProvider", "CUDAExecutionProvider",
                        "CPUExecutionProvider") if p in have]
    say(f"  using: {want[0]}")
    t0 = time.time()
    sess = {k: ort.InferenceSession(str(v), providers=want)
            for k, v in paths.items()}
    say(f"  three sessions in {time.time() - t0:.1f}s")

    from tokenizers import Tokenizer
    here = pathlib.Path(__file__).resolve().parent
    tok = Tokenizer.from_file(str(here / "tokenizer.json"))
    norm = None
    try:
        from chatterbox.tts import punc_norm
        norm = punc_norm
    except Exception:
        say("  (chatterbox not importable — speaking the raw lines)")

    dt = {i.name: i.type for i in sess["t3-prefill"].get_inputs()}

    def as_np(name, arr):
        kind = {"tensor(int64)": np.int64, "tensor(int32)": np.int32,
                "tensor(float)": np.float32}[dt[name]]
        return np.asarray(arr).astype(kind, copy=False)

    pieces, spoken, total = [], [], 0.0
    for i, line in enumerate(LINES):
        voice = chosen[i % len(chosen)]
        z = np.load(CONDS / f"{voice}.npz")
        text = norm(line) if norm else line
        ids = tok.encode(text.replace(" ", "[SPACE]"),
                         add_special_tokens=False).ids
        t_line = time.time()
        first = sess["t3-prefill"].run(None, {
            "text_tokens": as_np("text_tokens", [ids]),
            "speaker_emb": as_np("speaker_emb", z["t3.speaker_emb"]),
            "cond_speech_tokens": as_np("cond_speech_tokens",
                                        z["t3.cond_prompt_speech_tokens"]),
            "emotion_adv": as_np("emotion_adv", z["t3.emotion_adv"])})
        # READ OFF THE GRAPH. An assumed 2 against a one-row export folds the
        # odds into two half-rows and samples fluent nonsense.
        rows = int(first[0].shape[0])
        cache = first[1:]
        names = [f"cache{j}" for j in range(len(cache))]
        # SEEDED PER LINE, so two runs of this file are comparable to each
        # other. `VoiceBank.Seed` is the game's version of the same rule.
        rng = np.random.default_rng(1000 + i)
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
        if not tokens:
            say(f"  {voice}: produced nothing for \"{line}\"")
            continue
        n = len(tokens)
        n_p = z["gen.prompt_token"].shape[1]
        n_pm = z["gen.prompt_feat"].shape[1]
        h = 2 * (n_p + n)
        wav_len = (h - n_pm) * 480
        gr = np.random.default_rng(2000 + i)
        wav = sess["s3gen-decode"].run(None, {
            "tokens": np.asarray([tokens], dtype=np.int64),
            "prompt_token": z["gen.prompt_token"].astype(np.int64),
            "prompt_feat": z["gen.prompt_feat"].astype(np.float32),
            "embedding": z["gen.embedding"].astype(np.float32),
            "z": gr.standard_normal((1, 80, h)).astype(np.float32),
            "sine_noise": gr.standard_normal((1, 9, wav_len)).astype(np.float32),
        })[0].reshape(-1)
        secs = wav.shape[-1] / 24000.0
        took = time.time() - t_line
        total += took
        # FEATHER THE EDGES — the same ramps `Core/SpeechSamples` now applies
        # in the game, mirrored here because Jafar heard the pop in THIS
        # file: a decode starts at a non-zero sample, and the step from the
        # gap's zeros to that value is an audible click on every line.
        # THE SHARED TREATMENT — see line_audio.py for why it is one
        # function: the inline copy here was the second implementation and a
        # third, unfixed one in time-a-line was the file that popped next.
        wav = _la.feather(np, wav)
        if not pieces:
            pieces.append(_la.lead(np, wav.dtype))
        pieces.append(wav)
        pieces.append(np.zeros(int(GAP_SECONDS * 24000), dtype=wav.dtype))
        spoken.append(f"  {i + 1}. {voice}: {n} tokens, {secs:.1f}s of speech, "
                      f"{took:.1f}s to make — \"{line}\"")

    for s in spoken:
        say(s)
    if not pieces:
        say("  nothing was spoken at all")
        return 1
    say(f"  {len(spoken)} of {len(LINES)} lines spoken, {total:.0f}s of work "
        f"in {len(chosen)} voice(s), {rows} row(s) of odds"
        + (" — no guidance" if rows == 1 else " — classifier-free guidance"))

    import wave
    all_wav = np.concatenate(pieces)
    peak = float(np.abs(all_wav).max())
    if peak <= 0:
        say("  the waveform is silence — nothing to listen to")
        return 1
    pcm = (np.clip(all_wav / max(peak, 1e-9) * 0.85, -1, 1)
           * 32767).astype(np.int16)
    WAV.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(WAV), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(pcm.tobytes())
    say(f"  wrote {WAV.name} — {WAV.stat().st_size // 1024} KB, "
        f"{all_wav.shape[-1] / 24000.0:.1f}s, {len(spoken)} lines with "
        f"{GAP_SECONDS}s between them")
    return 0


def selftest():
    fails, ran = [], []

    def check(ok, what, got=""):
        print(("  ok    " if ok else "  FAIL  ") + what + (f"   [{got}]" if got else ""))
        ran.append(what)
        if not ok:
            fails.append(what)

    # THE LINES ARE THE FIXTURE, so what is asserted is that they are awkward
    # rather than that the code runs. A listening test made of comfortable
    # sentences proves comfortable sentences work.
    check(len(LINES) >= 4, f"{len(LINES)} lines, not one", str(len(LINES)))
    check(any(len(l) < 8 for l in LINES), "one of them is a mutter")
    check(any(len(l) > 50 for l in LINES), "and one is long enough to wander in")
    check(any(any(c.isdigit() for c in l) for l in LINES)
          or any("-" in l for l in LINES), "and one carries a number")
    check(any(l.rstrip().endswith("?") for l in LINES), "and one is a question")

    # THE PENALTY, ON BOTH SIGNS OF LOGIT. The HF convention divides a
    # positive logit and MULTIPLIES a negative one; get the branch wrong and
    # repetition becomes MORE likely exactly when the model is unsure. This is
    # the single line whose absence invalidated the first no-guidance test.
    import numpy as np
    sampler = _shared_pick()
    row = np.array([2.0, -2.0, 1.0])
    out = sampler.penalise(np, row.copy(), {0, 1})
    check(float(out[0]) < 2.0 and float(out[1]) < -2.0 and float(out[2]) == 1.0,
          "an already-said token becomes LESS likely on both signs of logit, "
          "and unsaid ones are untouched", str(out))

    said = []
    global OUT
    keep = OUT
    OUT = pathlib.Path("/nonexistent-graphs")
    try:
        rc = run(said.append)
    except Exception as e:
        rc, said = -1, [f"threw {type(e).__name__}"]
    finally:
        OUT = keep
    check(rc == 1 and any("no graphs" in s for s in said),
          "and with no graphs it names what is missing rather than throwing",
          "; ".join(said)[:70])

    print(f"\nspeak-a-few --selftest: "
          f"{'PASS' if not fails else str(len(fails)) + ' FAILED'} — {len(ran)} checks")
    return 1 if fails else 0


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

    import platform
    from datetime import datetime, timezone
    say("LEDGER — a few lines, more than one voice")
    say(f"ran on {platform.node()} ({platform.system()}), "
        f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    say("")
    rc = run(say)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    sys.exit(main())
