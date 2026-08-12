"""ONE TREATMENT FOR EVERY LISTENING FILE — because the third copy popped.

The cold-vocoder click was found by ear, measured in a file, and fixed twice:
in `Core/SpeechSamples` for the game and inline in `speak-a-few` for the
five-line test file. `time-a-line` writes a wav too, raw, and the very next
file Jafar heard came from it — pop and all. One idea had THREE
implementations and the unfixed one was the one that travelled. The rule
broken has a name in CLAUDE.md: the moment a fix works, grep for its
distinguishing token and read every other hit.

So the treatment is one function now, and the tools that write audio call it
instead of carrying their own copy. It mirrors `Core/SpeechSamples.Feather`
exactly: 25ms of hard zero (the vocoder's cold-start transient lives in the
first ~16ms and a fade only SCALES a click), a 10ms raised-cosine rise, 20ms
fall, with clamps so a mutter survives its own repairs. `LEAD_SECONDS` of
silence goes at the front of a FILE (not each line): players that swallow the
opening instants of a stream ate a word once, and the lead is for the
listener's equipment — the game needs none because its clips start inside a
running mix.
"""

LEAD_SECONDS = 0.5
SAMPLE_RATE = 24000


def feather(np, wav):
    """In place, on a 1-D float array at 24kHz. Returns it for chaining."""
    n = wav.shape[-1]
    if n == 0:
        return wav
    # GATED, NOT UNCONDITIONAL — mirrors Core/SpeechSamples exactly. A fixed
    # 25ms mute ate the "S" of a render that started speaking at zero and
    # turned it into a "tch"; the cold-vocoder click is only audible against
    # silence, so a loud-then-quiet head is a click and a sustained head is a
    # voice that keeps its onset.
    probe = min(int(SAMPLE_RATE * 0.016), n)
    tail = min(int(SAMPLE_RATE * 0.064), n)
    click_peak = float(np.abs(wav[:probe]).max()) if probe else 0.0
    after_peak = float(np.abs(wav[probe:tail]).max()) if tail > probe else 0.0
    isolated = after_peak < 0.01 and click_peak > after_peak * 2
    mute = min(int(SAMPLE_RATE * 0.025), n // 4) if isolated else 0
    up = min(int(SAMPLE_RATE * 0.010), max(0, n // 2 - mute))
    down = min(int(SAMPLE_RATE * 0.020), n // 2)
    wav[:mute] = 0.0
    if up > 0:
        wav[mute:mute + up] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(up) / up)
    if down > 0:
        wav[-down:] *= (0.5 - 0.5 * np.cos(np.pi * np.arange(down) / down))[::-1]
    return wav


def lead(np, dtype):
    """The file's opening silence, for the listener's player."""
    return np.zeros(int(LEAD_SECONDS * SAMPLE_RATE), dtype=dtype)
