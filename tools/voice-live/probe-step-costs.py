#!/usr/bin/env python3
"""WHERE DOES A 42ms STEP GO — experiment 1 of the latency plan.

    python3 tools/voice-live/probe-step-costs.py
    python3 tools/voice-live/probe-step-costs.py --selftest

FOUR QUESTIONS, ONE RUN, because a round trip to the machine with the card
costs the same whether it carries one or four. The plan this serves is
`game-design/live-speech-latency.md`; nothing here changes any graph.

1. WHICH CARD. Every report so far says "DmlExecutionProvider", which names
   the driver and not the hardware. The numbers in the plan describe one AMD
   card and should say which.

2. DOES THE STEP GROW WITH POSITION. The hypothesis: the loop round-trips the
   whole KV cache (~74MB at mid-sentence, fp32) through host memory every
   step, and that transfer grows linearly with position while the compute
   grows only mildly. Median step time at four positions gives the slope. A
   flat slope KILLS the cache-residency lever and the plan says so in
   advance rather than after.

3. CAN PYTHON KEEP THE CACHE ON THE DEVICE. onnxruntime's IOBinding can bind
   outputs on-device and feed them straight back as inputs, skipping both
   copies. Whether the DML build of the PYTHON package supports device
   ortvalues is exactly the kind of thing that must be run rather than read
   about — if it refuses, that is a finding (the production path is C#'s
   OrtIoBinding either way), not a failure.

4. WHAT DOES DECODING NEXT TO THE LOOP COST. Streaming decodes chunk N while
   the loop generates chunk N+1, on the same card. The sustainability margin
   in the plan assumed no contention; this measures it: step medians with a
   decode running against step medians alone.
"""
import argparse
import pathlib
import platform
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "tools" / "voice-live" / "game-out"
CONDS = ROOT / "game-design" / "voice-conds"
REPORT = ROOT / "game-design" / "voice-live" / "step-report.txt"
VOICE = "rocco"

# Step-time medians are taken over windows centred on these positions. 400 is
# past any line the game will speak; the point is the SLOPE, not the realism.
POSITIONS = (10, 100, 200, 400)
WINDOW = 12


def fit(points):
    """Least squares; returns (intercept, slope). Same shape as
    time-the-shape's, retyped here because importing across hyphenated tool
    files needs path games and two ten-line fits are cheaper than that."""
    n = len(points)
    if n < 2:
        return None, None
    sx = sum(p[0] for p in points)
    sy = sum(p[1] for p in points)
    sxx = sum(p[0] * p[0] for p in points)
    sxy = sum(p[0] * p[1] for p in points)
    d = n * sxx - sx * sx
    if abs(d) < 1e-12:
        return None, None
    m = (n * sxy - sx * sy) / d
    return (sy - m * sx) / n, m


def gpu_name():
    """The adapter's name, from Windows itself. Torch cannot answer this —
    the environment ships CPU torch — and onnxruntime's python API names the
    provider, not the card."""
    if platform.system() != "Windows":
        return "(not Windows — no adapter to name)"
    for cmd in (["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_VideoController).Name"],
                ["wmic", "path", "win32_VideoController", "get", "name"]):
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            lines = [l.strip() for l in p.stdout.splitlines()
                     if l.strip() and l.strip().lower() != "name"]
            if lines:
                return " / ".join(lines)
        except Exception:
            continue
    return "(could not ask Windows for the adapter name)"


def median(xs):
    ys = sorted(xs)
    return ys[len(ys) // 2]


def run(say):
    import numpy as np
    import onnxruntime as ort

    paths = {n: OUT / f"{n}.onnx"
             for n in ("t3-prefill", "t3-step", "s3gen-decode")}
    missing = [p.name for p in paths.values() if not p.exists()]
    if missing:
        say(f"  no graphs on this machine: {', '.join(missing)}")
        return 1
    npz = CONDS / f"{VOICE}.npz"
    if not npz.exists():
        say(f"  no voice at {npz}")
        return 1

    say(f"  card: {gpu_name()}")
    have = ort.get_available_providers()
    want = [p for p in ("DmlExecutionProvider", "CUDAExecutionProvider",
                        "CPUExecutionProvider") if p in have]
    say(f"  provider: {want[0]}")

    z = np.load(npz)
    t0 = time.time()
    pre = ort.InferenceSession(str(paths["t3-prefill"]), providers=want)
    stp = ort.InferenceSession(str(paths["t3-step"]), providers=want)
    say(f"  prefill + step sessions in {time.time() - t0:.1f}s")

    dt = {i.name: i.type for i in pre.get_inputs()}

    def as_np(name, arr):
        kind = {"tensor(int64)": np.int64, "tensor(int32)": np.int32,
                "tensor(float)": np.float32}[dt[name]]
        return np.asarray(arr).astype(kind, copy=False)

    ids = list(range(10, 40))          # 30 arbitrary text tokens; timing only
    first = pre.run(None, {
        "text_tokens": as_np("text_tokens", [ids]),
        "speaker_emb": as_np("speaker_emb", z["t3.speaker_emb"]),
        "cond_speech_tokens": as_np("cond_speech_tokens",
                                    z["t3.cond_prompt_speech_tokens"]),
        "emotion_adv": as_np("emotion_adv", z["t3.emotion_adv"])})
    cache = list(first[1:])
    names = [f"cache{i}" for i in range(len(cache))]
    base = cache[0].shape[2]
    say(f"  cache starts at {base} positions, "
        f"{sum(c.nbytes for c in cache) / 1e6:.0f} MB across {len(cache)} tensors")

    # ---- 2. THE SLOPE -----------------------------------------------------
    tok = np.array([[7]], dtype=np.int64)
    times = {}                          # position -> seconds
    top = max(POSITIONS) + WINDOW // 2 + 1
    for step in range(1, top):
        feed = dict(zip(names, cache))
        feed["token"] = tok
        feed["position"] = np.array(step, dtype=np.int64)
        t1 = time.time()
        got = stp.run(None, feed)
        times[step] = time.time() - t1
        cache = got[1:]
    buckets = []
    for p in POSITIONS:
        window = [times[s] for s in times
                  if abs(s - p) <= WINDOW // 2 and s > 2]
        buckets.append((p, median(window)))
    say("  step medians: " + "  ".join(f"pos{p}={v * 1000:.1f}ms"
                                       for p, v in buckets))
    c0, slope = fit(buckets)
    total_at_100 = c0 + slope * 100
    share = slope * 100 / total_at_100 if total_at_100 > 0 else 0.0
    say(f"  -> {c0 * 1000:.1f}ms flat + {slope * 1e6:.1f}us per position; at "
        f"position 100 the position-linear part is {share:.0%} of the step")
    if slope * 1e6 < 20:
        say("  -> the slope is nearly FLAT: shipping the cache is not what a "
            "step costs, and the residency lever dies here")
    else:
        say("  -> the step grows with how much sentence is behind it — "
            "consistent with the cache round-trip; residency is worth building")

    # ---- 3. CAN PYTHON BIND THE CACHE ON-DEVICE ---------------------------
    # Timed against the SAME positions as a plain run, or the comparison
    # means nothing. A refusal is reported by name.
    say("")
    say("SECTION: io-binding (if the report ends here, THIS is what hung)")
    try:
        bind_cache = [ort.OrtValue.ortvalue_from_numpy(c, "dml", 0)
                      for c in first[1:]]
        binding = stp.io_binding()
        plain = []
        cache2 = list(first[1:])
        for step in range(1, 41):
            feed = dict(zip(names, cache2))
            feed["token"] = tok
            feed["position"] = np.array(step, dtype=np.int64)
            t1 = time.time()
            got = stp.run(None, feed)
            plain.append(time.time() - t1)
            cache2 = got[1:]
        bound = []
        for step in range(1, 41):
            binding.clear_binding_inputs()
            binding.clear_binding_outputs()
            binding.bind_cpu_input("token", tok)
            binding.bind_cpu_input("position", np.array(step, dtype=np.int64))
            for n, v in zip(names, bind_cache):
                binding.bind_ortvalue_input(n, v)
            binding.bind_output("logits", "cpu")
            for i in range(len(names)):
                binding.bind_output(f"newcache{i}", "dml", 0)
            t1 = time.time()
            stp.run_with_iobinding(binding)
            outs = binding.get_outputs()
            bound.append(time.time() - t1)
            bind_cache = outs[1:]
        say(f"  IOBinding on dml WORKS in python: bound median "
            f"{median(bound) * 1000:.1f}ms vs plain {median(plain) * 1000:.1f}ms "
            f"over the same 40 positions — "
            f"{median(plain) / max(median(bound), 1e-9):.2f}x")
    except Exception as e:
        say(f"  IOBinding on dml refused in python: {type(e).__name__}: "
            f"{str(e)[:140]}")
        say("  -> not a dead end — the game is C#, whose OrtIoBinding is the "
            "production path; this just says python cannot preview it")

    # ---- 4. CONTENTION ----------------------------------------------------
    say("")
    say("SECTION: contention — two sessions on one DML device (if the report "
        "ends here, concurrent Run() on this driver is the hang, which is "
        "itself the answer streaming needed)")
    t0 = time.time()
    dec = ort.InferenceSession(str(paths["s3gen-decode"]), providers=want)
    say(f"  decode session in {time.time() - t0:.1f}s")
    n_p = z["gen.prompt_token"].shape[1]
    n_pm = z["gen.prompt_feat"].shape[1]
    n = 25                              # one streaming chunk's worth
    h = 2 * (n_p + n)
    rng = np.random.default_rng(3)
    dfeed = {
        "tokens": rng.integers(0, 6561, (1, n)).astype(np.int64),
        "prompt_token": z["gen.prompt_token"].astype(np.int64),
        "prompt_feat": z["gen.prompt_feat"].astype(np.float32),
        "embedding": z["gen.embedding"].astype(np.float32),
        "z": rng.standard_normal((1, 80, h)).astype(np.float32),
        "sine_noise": rng.standard_normal(
            (1, 9, (h - n_pm) * 480)).astype(np.float32)}
    dec.run(None, dfeed)                # warm

    stop = threading.Event()
    decodes = []

    def keep_decoding():
        while not stop.is_set():
            t1 = time.time()
            dec.run(None, dfeed)
            decodes.append(time.time() - t1)

    quiet = []
    cache3 = list(first[1:])
    for step in range(1, 41):
        feed = dict(zip(names, cache3))
        feed["token"] = tok
        feed["position"] = np.array(step, dtype=np.int64)
        t1 = time.time()
        got = stp.run(None, feed)
        quiet.append(time.time() - t1)
        cache3 = got[1:]
    thread = threading.Thread(target=keep_decoding)
    thread.start()
    busy = []
    try:
        for step in range(41, 101):
            feed = dict(zip(names, cache3))
            feed["token"] = tok
            feed["position"] = np.array(step, dtype=np.int64)
            t1 = time.time()
            got = stp.run(None, feed)
            busy.append(time.time() - t1)
            cache3 = got[1:]
    finally:
        stop.set()
        thread.join(timeout=60)
    qm, bm = median(quiet), median(busy)
    say(f"  steps alone: {qm * 1000:.1f}ms   with a 25-token decode running "
        f"beside them: {bm * 1000:.1f}ms   ({bm / max(qm, 1e-9):.2f}x) — "
        f"{len(decodes)} decode(s) completed meanwhile")
    rate = 1.0 / bm if bm > 0 else 0.0
    say(f"  -> under contention this card generates {rate:.1f} tok/s against "
        f"the 25.0 playback needs"
        + (" — STREAMING WOULD UNDERRUN HERE TODAY" if rate < 25.0
           else " — the margin holds"))
    return 0


def selftest():
    fails, ran = [], []

    def check(ok, what, got=""):
        print(("  ok    " if ok else "  FAIL  ") + what + (f"   [{got}]" if got else ""))
        ran.append(what)
        if not ok:
            fails.append(what)

    c, m = fit([(10, 1.0), (100, 1.9), (200, 2.9), (400, 4.9)])
    check(c is not None and abs(c - 0.9032) < 0.02 and abs(m - 0.01) < 0.001,
          "the fit recovers a known slope through four position buckets",
          f"{c:.3f}, {m:.5f}")
    check(fit([(1, 1.0)]) == (None, None), "and one bucket is not a slope")
    check(median([3, 1, 2]) == 2 and median([4, 1, 3, 2]) == 3,
          "the median is the middle, not the mean — one scheduling hiccup "
          "must not move it")

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

    print(f"\nprobe-step-costs --selftest: "
          f"{'PASS' if not fails else str(len(fails)) + ' FAILED'} — {len(ran)} checks")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    # WRITE-THROUGH, NOT AT THE END. The first run of this probe hung inside
    # a native call, the watcher killed it at the hour, and every number it
    # had already measured died with it — the report was only written on
    # success. A probe whose job is diagnosing hangs must survive one: each
    # line lands on disk as it is said, flushed, so a killed run leaves the
    # slope on disk and its last line names the section it died in.
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("", encoding="utf-8")

    def say(s):
        print(s, flush=True)
        with REPORT.open("a", encoding="utf-8") as f:
            f.write(s + "\n")

    say("LEDGER — where a step goes (latency plan, experiment 1)")
    say(f"ran on {platform.node()} ({platform.system()}), "
        f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    say("")
    rc = run(say)
    print(f"\n  written to {REPORT.relative_to(ROOT)}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
