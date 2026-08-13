#!/usr/bin/env python3
"""WHAT THE COST IS MADE OF — startup, and how the decode grows with a line.

    python3 tools/voice-live/time-the-shape.py
    python3 tools/voice-live/time-the-shape.py --selftest

TWO QUESTIONS, ONE ROUND TRIP, because a round trip to Jafar's machine costs
the same whether it carries one measurement or two.

**Startup.** `time-a-line` measured three sessions opening in 184 seconds, of
which `s3gen-decode` alone was 178. That is three minutes of a player staring
at a loading screen for one of the three files. The number that says what to
do about it is not in that run: opening the same file on the CPU provider took
190 seconds, so whatever is expensive is NOT DirectML compiling kernels — it
happens before any provider sees the graph. This times the file three ways and
prints all three, because "which of these is faster" is the question and one
configuration cannot answer it.

**How the decode grows.** `SpeechDirector.Projected` estimates a line's cost as
steps divided by a measured step rate. That is the TEXT stage only. On the
measured run the text stage was 3.8 seconds of a 7.3-second line and the
decode was the other half, and the director cannot see it at all — it has no
term for it, so no amount of learning will teach it one. Before adding a term
there has to be a shape to add: is the decode a constant, or does it grow with
the line, and how fast. This runs it at six token counts and prints the series.

THE SERIES SITS ABOVE THE FIT ON PURPOSE. A slope through six points is a
summary, and this project has a long list of summaries that were true and
answered a different question than the one being asked. The raw numbers are
what a person can look at and say "that is not a straight line".

THE TOKENS ARE RANDOM AND THAT IS FINE HERE. The decode graph does the same
arithmetic whatever the token values are — the cost is set by how many there
are. What comes out is noise rather than speech, which is why this tool writes
no waveform: `time-a-line` is the one that produces something to listen to.
"""
import argparse
import pathlib
import platform
import sys
import time
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "tools" / "voice-live" / "game-out"
CONDS = ROOT / "game-design" / "voice-conds"
REPORT = ROOT / "game-design" / "voice-live" / "shape-report.txt"
VOICE = "rocco"

# How many acoustic tokens to decode at. 86 was one real line; the spread
# either side is what shows whether the cost follows the line's length.
TOKEN_COUNTS = (10, 25, 50, 86, 170, 340)


def fit(points):
    """Least squares through (n, seconds) — returns (constant, per_token).

    Two returns rather than one 'seconds per token', because those are
    different claims and only both together can say whether a short line is
    cheap. A pure per-token rate computed from a cost that is mostly constant
    reads as though ten tokens would take a tenth of the time.
    """
    n = len(points)
    if n < 2:
        return None, None
    sx = sum(p[0] for p in points)
    sy = sum(p[1] for p in points)
    sxx = sum(p[0] * p[0] for p in points)
    sxy = sum(p[0] * p[1] for p in points)
    denom = n * sxx - sx * sx
    if abs(denom) < 1e-12:
        return None, None
    slope = (n * sxy - sx * sy) / denom
    return (sy - slope * sx) / n, slope


def open_ways(ort, path, want, say):
    """Time opening one graph several ways. Returns {name: seconds or None}.

    EVERY WAY NAMED, INCLUDING THE ONES THAT FAIL. A configuration that threw
    and a configuration that was never tried look identical in a table of
    timings, and they want opposite next moves.
    """
    ways, saved = {}, path.parent / (path.stem + ".opt.onnx")

    def timed(name, make):
        t0 = time.time()
        try:
            make()
        except Exception as e:
            ways[name] = None
            say(f"  {name}: could not run — {type(e).__name__}: {e}"[:200])
            return
        ways[name] = time.time() - t0
        say(f"  {name}: {ways[name]:.1f}s")

    def plain():
        ort.InferenceSession(str(path), providers=want)

    def bare():
        so = ort.SessionOptions()
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
        ort.InferenceSession(str(path), so, providers=want)

    def write_opt():
        so = ort.SessionOptions()
        so.optimized_model_filepath = str(saved)
        ort.InferenceSession(str(path), so, providers=want)

    def reopen():
        ort.InferenceSession(str(saved), providers=want)

    def on_cpu():
        ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])

    timed("as shipped", plain)
    # WHICH LAYER OWNS THE THREE MINUTES. Optimisation was ruled out by
    # the two ways below (turning it OFF made it worse), which leaves
    # weight loading and DirectML's own kernel work — and those two are
    # separated by asking the CPU provider to open the identical file.
    # A fast CPU open convicts DML; a slow one convicts the 1.3GB of
    # weights, and only the first of those has a fix worth chasing.
    timed("on the CPU provider (no DirectML)", on_cpu)
    timed("with graph optimisation off", bare)
    timed("writing an optimised copy (one time, at build)", write_opt)
    if saved.exists():
        mb = saved.stat().st_size / (1024 * 1024)
        say(f"  the optimised copy is {mb:.0f} MB")
        timed("opening the optimised copy", reopen)
    else:
        ways["opening the optimised copy"] = None
        say("  the optimised copy was not written, so it could not be reopened")
    return ways


def run(say):
    import numpy as np
    import onnxruntime as ort

    dec_path = OUT / "s3gen-decode.onnx"
    if not dec_path.exists():
        say(f"  no decode graph at {dec_path} — run '5 EXPORT FOR THE GAME.bat' "
            f"or the 'export-graphs' job first.")
        return 1
    npz = CONDS / f"{VOICE}.npz"
    if not npz.exists():
        say(f"  no voice at {npz}")
        return 1

    have = ort.get_available_providers()
    want = [p for p in ("DmlExecutionProvider", "CUDAExecutionProvider",
                        "CPUExecutionProvider") if p in have]
    say(f"  providers available: {', '.join(have)}")
    say(f"  using: {want[0]}")
    say("")
    say("  STARTUP — the same file opened four ways:")
    ways = open_ways(ort, dec_path, want, say)
    ran = [k for k, v in ways.items() if v is not None]
    say(f"  {len(ran)} of {len(ways)} ways ran")
    best = min(((v, k) for k, v in ways.items()
                if v is not None and not k.startswith("writing")), default=None)
    shipped = ways.get("as shipped")
    if best and shipped:
        if best[1] == "as shipped":
            say(f"  -> nothing beat the shipped path ({shipped:.1f}s); the cost "
                f"is not graph optimisation")
        else:
            say(f"  -> '{best[1]}' opens in {best[0]:.1f}s against "
                f"{shipped:.1f}s as shipped, {shipped / max(best[0], 1e-6):.1f}x")

    # ---- HOW THE DECODE GROWS ------------------------------------------
    say("")
    say("  THE DECODE, at six line lengths:")
    z = np.load(npz)
    sess = ort.InferenceSession(str(dec_path), providers=want)
    rng = np.random.default_rng(11)
    n_p = z["gen.prompt_token"].shape[1]
    n_pm = z["gen.prompt_feat"].shape[1]
    points, series = [], []
    for n in TOKEN_COUNTS:
        h = 2 * (n_p + n)
        wav_len = (h - n_pm) * 480
        feed = {
            "tokens": rng.integers(0, 6561, (1, n)).astype(np.int64),
            "prompt_token": z["gen.prompt_token"].astype(np.int64),
            "prompt_feat": z["gen.prompt_feat"].astype(np.float32),
            "embedding": z["gen.embedding"].astype(np.float32),
            "z": rng.standard_normal((1, 80, h)).astype(np.float32),
            "sine_noise": rng.standard_normal((1, 9, wav_len)).astype(np.float32)}
        # TWICE, AND BOTH PRINTED. The first run of any size pays for whatever
        # the runtime allocates for that shape; a table of first runs would
        # measure allocation and call it decoding.
        got = []
        for _ in range(2):
            t0 = time.time()
            wav = sess.run(None, feed)[0]
            got.append(time.time() - t0)
        secs = min(got)
        seconds_of_audio = wav.shape[-1] / 24000.0
        points.append((n, secs))
        series.append(f"{n}tok={got[0]:.2f}/{got[1]:.2f}s({seconds_of_audio:.1f}s audio)")
    say("  " + "  ".join(series))
    const, per = fit(points)
    if const is not None:
        say(f"  -> about {const:.2f}s before a single token, plus "
            f"{per * 1000:.1f}ms per token")
        say(f"     so an 86-token line is {const + per * 86:.1f}s of decoding, "
            f"and a 20-token one is {const + per * 20:.1f}s")
        # WHAT IT MEANS FOR THE DIRECTOR, said here because the number is
        # useless sitting in a file nobody reads next to the code that needs
        # it. `Projected` currently answers "how long will the TEXT take".
        say(f"     `SpeechDirector.Projected` has no term for any of this; on "
            f"the measured line it was missing about half the wait.")

    # ---- WHERE THE FIXED COST ACTUALLY GOES -----------------------------
    #
    # THE SUSPICION, WRITTEN DOWN BEFORE THE NUMBERS SO IT CAN BE WRONG. The
    # decoder is handed the voice's reference clip along with the line, and it
    # decodes BOTH: the mel sequence is `2 * (prompt_tokens + line_tokens)`
    # frames long, and this voice's prompt is 250 tokens. So a ten-token
    # mutter asks the network to work through 500 frames of somebody else's
    # sentence before it reaches the first word of its own.
    #
    # If that is where the 2.7 seconds live, they are not a fixed cost at all
    # — they are a per-prompt cost, and the prompt is a number we choose. If
    # it is not, the fixed cost is real and this rules the cheap fix out,
    # which is worth two minutes either way.
    say("")
    say("  THE SAME LINE, WITH SHORTER VOICE PROMPTS:")
    line_n = 50
    prompts, pseries = [], []
    for p in (n_p, 150, 100, 50, 25):
        if p > n_p:
            continue
        h = 2 * (p + line_n)
        wav_len = (h - 2 * p) * 480
        feed = {
            "tokens": rng.integers(0, 6561, (1, line_n)).astype(np.int64),
            "prompt_token": z["gen.prompt_token"][:, :p].astype(np.int64),
            "prompt_feat": z["gen.prompt_feat"][:, :2 * p, :].astype(np.float32),
            "embedding": z["gen.embedding"].astype(np.float32),
            "z": rng.standard_normal((1, 80, h)).astype(np.float32),
            "sine_noise": rng.standard_normal((1, 9, wav_len)).astype(np.float32)}
        got = []
        try:
            for _ in range(2):
                t0 = time.time()
                sess.run(None, feed)
                got.append(time.time() - t0)
        except Exception as e:
            pseries.append(f"{p}prompt=refused({type(e).__name__})")
            continue
        prompts.append((p, min(got)))
        pseries.append(f"{p}prompt={got[0]:.2f}/{got[1]:.2f}s")
    say("  " + "  ".join(pseries))
    # A DENOMINATOR ON A REFUSAL. A graph that will not take a shorter prompt
    # is a finding — it means the length was baked in at trace time — and it
    # must not read as "the shorter prompt was no faster".
    say(f"  {len(prompts)} of {len(pseries)} prompt lengths ran, on a "
        f"{line_n}-token line")
    pc, pp = fit(prompts)
    if pc is not None:
        say(f"  -> about {pc:.2f}s regardless, plus {pp * 1000:.1f}ms per "
            f"prompt token")
        say(f"     the shipped {n_p}-token prompt therefore costs "
            f"{pp * n_p:.1f}s of every line spoken in this voice")
    return 0


def selftest():
    fails, ran = [], []

    def check(ok, what, got=""):
        print(("  ok    " if ok else "  FAIL  ") + what + (f"   [{got}]" if got else ""))
        ran.append(what)
        if not ok:
            fails.append(what)

    # THE FIT, ON A LINE IT MUST RECOVER EXACTLY. A least squares that returns
    # the wrong slope would publish a decode cost nobody could tell was wrong,
    # because the series above it would still look reasonable.
    c, m = fit([(10, 1.5), (20, 2.0), (40, 3.0)])
    check(c is not None and abs(c - 1.0) < 1e-9 and abs(m - 0.05) < 1e-9,
          "the fit recovers a straight line exactly", f"{c}, {m}")
    c2, m2 = fit([(10, 1.0), (10, 2.0)])
    check(c2 is None and m2 is None,
          "and two points at the same length are refused rather than divided by "
          "zero", f"{c2}, {m2}")
    check(fit([(1, 1.0)]) == (None, None),
          "and one point is not a slope")

    # A CURVE IS NOT FORCED TO LOOK STRAIGHT. The fit will happily draw a line
    # through a quadratic; this is the check that says so out loud, so the
    # SERIES stays the evidence and the fit stays a summary.
    c3, m3 = fit([(10, 1.0), (20, 4.0), (40, 16.0)])
    worst = max(abs((c3 + m3 * n) - y) for n, y in
                [(10, 1.0), (20, 4.0), (40, 16.0)])
    check(worst > 0.5,
          f"a curve fitted as a line is off by {worst:.1f}s at some point — the "
          f"series is the evidence, the fit is a summary", f"{worst:.2f}")

    # THE REFUSAL PATH, RUN. A tool that throws when the graphs are absent
    # tells the watcher nothing it can act on.
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
    check(rc == 1 and any("no decode graph" in s for s in said),
          "and with no graphs on the machine it names what is missing rather "
          "than throwing", "; ".join(said)[:90])

    print(f"\ntime-the-shape --selftest: "
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

    # WHERE AND WHEN, because this file travels back to a container that has
    # no GPU and cannot tell a stale report from a fresh one by looking.
    say("LEDGER — what the speech cost is made of")
    say(f"ran on {platform.node()} ({platform.system()}) , "
        f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    say(f"graphs in {OUT}")
    say("")
    rc = run(say)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n  written to {REPORT.relative_to(ROOT)}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
