#!/usr/bin/env python3
"""
LEDGER — local TTS benchmark.

Run this on the GAMING PC, not in CI. It answers four questions, in order of
how much they matter to the project:

  1. CONSISTENCY — can the model say ten lines that sound like ONE PERSON?
     A model that fails this cannot voice a character however good any single
     line is, and it decides our whole voice architecture.
  2. DIRECTION — does the same sentence change when the direction changes?
     ("So which is it going to be?" bored vs grave.) The simulation always
     knows the emotional state; a model that ignores it wastes our one
     structural advantage over KCD2's recorded barks.
  3. SPEED — real-time factor. Under ~0.35 RTF we can voice live dialogue
     with no perceptible wait. Above ~1.0 it is offline-only.
  4. FOOTPRINT — VRAM and install size, because this ships to players.

It writes WAVs you can listen to and a table you can send back. It does NOT
pick a winner: ears decide that, and they are yours.

USAGE
  python bench.py --list                 # what adapters are available
  python bench.py --engine kokoro        # run one
  python bench.py --engine all           # run everything installed
  python bench.py --engine kokoro --consistency-only

Output lands in ./out/<engine>/ as WAVs plus report.md.

ADDING AN ENGINE: write a class with .name, .available(), .synth(text, voice,
direction) -> (samples, sample_rate), and register it in ENGINES. The adapters
below are written defensively against APIs I cannot test from here — if one
has drifted, the error message will say so plainly rather than crashing the
run, and fixing an adapter is a five-line job.
"""

import argparse
import json
import os
import statistics
import sys
import time
import wave
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"


# ---------------------------------------------------------------- utilities

def write_wav(path: Path, samples, rate: int):
    """Write float(-1..1) or int16 samples to a 16-bit mono WAV."""
    import array
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import numpy as np
        a = np.asarray(samples).squeeze()
        if a.dtype.kind == "f":
            a = np.clip(a, -1.0, 1.0)
            a = (a * 32767).astype("<i2")
        else:
            a = a.astype("<i2")
        raw = a.tobytes()
    except ImportError:
        arr = array.array("h", [int(max(-1.0, min(1.0, s)) * 32767) for s in samples])
        raw = arr.tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(raw)


def duration_of(samples, rate: int) -> float:
    try:
        n = len(samples)
    except TypeError:
        n = samples.shape[-1]
    return n / float(rate)


def vram_mb():
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.max_memory_allocated() / (1024 * 1024)
    except Exception:
        pass
    return None


# ----------------------------------------------------------------- adapters

class Engine:
    name = "base"
    note = ""

    def available(self):
        raise NotImplementedError

    def load(self):
        pass

    def synth(self, text, voice, direction):
        """Return (samples, sample_rate)."""
        raise NotImplementedError


class Kokoro(Engine):
    """Small, fast, English-first. The 'good enough and quick' candidate —
    the one most likely to be usable for LIVE dialogue on a mid-range GPU."""
    name = "kokoro"
    note = "small/fast; American English is its strength; limited emotional control"

    VOICE_MAP = {
        "lena": "af_heart", "mara": "af_bella", "crowd_f": "af_sarah",
        "rocco": "am_michael", "crowd_m": "am_adam",
    }

    def available(self):
        try:
            import kokoro  # noqa: F401
            return True
        except Exception:
            return False

    def load(self):
        from kokoro import KPipeline
        self.pipe = KPipeline(lang_code="a")   # 'a' = American English

    def synth(self, text, voice, direction):
        v = self.VOICE_MAP.get(voice, "af_heart")
        chunks = []
        for _, _, audio in self.pipe(text, voice=v):
            chunks.append(audio)
        try:
            import numpy as np
            return np.concatenate([c.detach().cpu().numpy() if hasattr(c, "detach") else c
                                   for c in chunks]), 24000
        except ImportError:
            flat = []
            for c in chunks:
                flat.extend(list(c))
            return flat, 24000


class XTTS(Engine):
    """Voice CLONING from a reference clip. This is the one that could solve
    the pre-generated-vs-runtime seam: define a character's voice once, then
    reproduce it forever at zero runtime cost."""
    name = "xtts"
    note = "zero-shot voice cloning; heavier (~4GB VRAM); the consistency answer if it holds up"

    def available(self):
        try:
            from TTS.api import TTS  # noqa: F401
            return True
        except Exception:
            return False

    def load(self):
        from TTS.api import TTS
        import torch
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(dev)
        self.refs = {}
        refdir = HERE / "refs"
        if refdir.exists():
            for f in refdir.glob("*.wav"):
                self.refs[f.stem] = str(f)
        if not self.refs:
            print("  ! xtts: no reference clips in ./refs/<voice>.wav — cloning "
                  "cannot be tested. Put 6-10s of clean speech per voice there.")

    def synth(self, text, voice, direction):
        ref = self.refs.get(voice) or next(iter(self.refs.values()), None)
        if ref is None:
            raise RuntimeError("no reference wav available for cloning")
        wav = self.tts.tts(text=text, speaker_wav=ref, language="en")
        return wav, 24000


class Piper(Engine):
    """CPU-only, very fast, lower ceiling. The floor of the comparison: if
    something more expensive is not audibly better than this, it is not worth
    its cost."""
    name = "piper"
    note = "CPU-only, very fast, robotic-leaning; the control case"

    def available(self):
        try:
            import piper  # noqa: F401
            return True
        except Exception:
            return False

    def load(self):
        from piper import PiperVoice
        model = os.environ.get("PIPER_MODEL")
        if not model or not Path(model).exists():
            raise RuntimeError("set PIPER_MODEL=/path/to/en_US-*.onnx")
        self.voice = PiperVoice.load(model)

    def synth(self, text, voice, direction):
        import io
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            self.voice.synthesize(text, w)
        buf.seek(0)
        with wave.open(buf, "rb") as r:
            rate = r.getframerate()
            frames = r.readframes(r.getnframes())
        import array
        return array.array("h", frames), rate


ENGINES = [Kokoro(), XTTS(), Piper()]


# --------------------------------------------------------------------- run

def run_engine(eng, data, consistency_only=False):
    print(f"\n=== {eng.name} — {eng.note}")
    t0 = time.time()
    try:
        eng.load()
    except Exception as e:
        print(f"  ! load failed: {e}")
        return None
    load_s = time.time() - t0
    print(f"  loaded in {load_s:.1f}s")

    outdir = OUT / eng.name
    rows = []
    rtfs = []

    cases = [] if consistency_only else data["cases"]
    for c in cases:
        try:
            t = time.time()
            samples, rate = eng.synth(c["text"], c["voice"], c.get("direction", ""))
            gen = time.time() - t
            dur = duration_of(samples, rate)
            rtf = gen / dur if dur > 0 else float("inf")
            rtfs.append(rtf)
            write_wav(outdir / f"{c['id']}.wav", samples, rate)
            rows.append((c["id"], c["voice"], f"{dur:.1f}s", f"{gen:.2f}s", f"{rtf:.2f}"))
            print(f"  {c['id']:28} {dur:5.1f}s audio  {gen:5.2f}s gen  RTF {rtf:.2f}")
        except Exception as e:
            print(f"  ! {c['id']}: {e}")
            rows.append((c["id"], c["voice"], "-", "-", f"FAILED: {e}"))

    # The decisive test.
    probe = data["consistency_probe"]
    print(f"  --- consistency probe ({len(probe['texts'])} lines, one character)")
    for i, text in enumerate(probe["texts"]):
        try:
            samples, rate = eng.synth(text, probe["voice"], "neutral, in character")
            write_wav(outdir / "consistency" / f"{i:02d}.wav", samples, rate)
        except Exception as e:
            print(f"  ! consistency {i}: {e}")
            break
    print(f"  wrote {outdir/'consistency'} — LISTEN TO THESE BACK TO BACK.")

    v = vram_mb()
    report = outdir / "report.md"
    with report.open("w") as f:
        f.write(f"# {eng.name}\n\n{eng.note}\n\n")
        f.write(f"- load time: {load_s:.1f}s\n")
        f.write(f"- peak VRAM: {v:.0f} MB\n" if v else "- peak VRAM: n/a (CPU)\n")
        if rtfs:
            f.write(f"- median RTF: {statistics.median(rtfs):.2f} "
                    f"(under 0.35 = usable for live dialogue)\n")
        f.write("\n| case | voice | audio | gen | RTF |\n|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(r) + " |\n")
        f.write("\n## What to listen for\n\n"
                "1. **consistency/** — ten lines, one character. Do they sound like\n"
                "   one person? This decides the architecture.\n"
                "2. **same_line_bored vs same_line_grave** — identical text, opposite\n"
                "   direction. Are they obviously different?\n"
                "3. **emphasis_test** — does the stress land on 'your'?\n"
                "4. **hard_prosody** — are '$120' and 'day 8' spoken or read?\n"
                "5. **long_dialogue** — does it stay alive to the end or flatten out?\n")
    print(f"  report: {report}")
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="all")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--consistency-only", action="store_true")
    a = ap.parse_args()

    data = json.loads((HERE / "lines.json").read_text())

    if a.list:
        print("engine    available  note")
        for e in ENGINES:
            print(f"{e.name:9} {str(e.available()):10} {e.note}")
        return 0

    chosen = [e for e in ENGINES if a.engine in ("all", e.name)]
    if not chosen:
        print(f"no such engine: {a.engine}")
        return 2

    ran = 0
    for e in chosen:
        if not e.available():
            print(f"\n=== {e.name}: NOT INSTALLED (skipping) — see README")
            continue
        run_engine(e, data, a.consistency_only)
        ran += 1

    if ran == 0:
        print("\nNothing installed yet. See README.md for the pip lines.")
        return 1
    print(f"\nDone. Send back ./out/ (or just listen and tell me what you think).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
