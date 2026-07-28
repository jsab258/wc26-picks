#!/usr/bin/env python3
"""
LEDGER — local TTS benchmark.  ONE FILE.  Download it, run it.

    python ledger_tts_bench.py

That is the whole thing. It builds a separate clean environment PER ENGINE,
installs what that engine needs, generates the audio, and tells you what to
listen for. No repo, no config, no other files.

Options (all optional):
    --engine kokoro         one engine, or a list: --engine kokoro,chatterbox
    --yes                   don't ask before installing
    --quick                 fewer lines
    --no-open               don't open the output folder
    --keep-going            don't stop when one engine fails

WHY EACH ENGINE IS HERE

  kokoro      small, fast, American English. The live-dialogue bet: if this
              is good enough we can voice speech AS IT HAPPENS, which is the
              whole reason to do this locally at all.
  chatterbox  the answer to what piper failed. It has an explicit
              EXAGGERATION control, so the game can say "grave" or "bored"
              and have the model actually do it. Also clones a voice from
              ~10 seconds of reference.
  xtts        voice CLONING. If its clones hold up, the seam between
              pre-generated barks and live lines disappears.
  piper       CPU-only, very fast, lower ceiling. THE CONTROL CASE — already
              run, already judged: "very obviously synthetic, no emphasis,
              very unnatural." That is the floor. Anything that is not
              audibly better than piper is not worth its cost.
  eleven      OPT-IN paid reference (free tier is enough for this test).
              Never runs unless you ask for it AND set ELEVENLABS_API_KEY.
              It is here to calibrate the ceiling: if local is close, we
              ship local; if the gap is huge, we know what we are giving up.

WHAT THIS IS DECIDING, in order of importance:

  1. CONSISTENCY — ten lines, one character, back to back. A model that
     cannot make them sound like ONE PERSON cannot voice a character.
  2. DIRECTION — the same sentence, once bored, once grave. Our advantage
     over recorded barks is that the game always knows how the speaker
     feels; a model that ignores direction throws that away. Piper scored
     zero here. This is now the headline test.
  3. SPEED — real-time factor. Under ~0.35 we can voice live dialogue with
     no perceptible wait. Over ~1.0 it is offline-only.
  4. FOOTPRINT — VRAM, because this ships to players.

The lines are real game dialogue. Testing TTS on "the quick brown fox" tells
you nothing.
"""

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
import traceback
import wave
from pathlib import Path

# Bumped on every change. Printed at startup so a stale copy in the Downloads
# folder announces itself instead of reproducing an old failure exactly.
VERSION = "2026-07-28.8  (says what your GPU actually is, and what that costs you)"

HERE = Path(__file__).resolve().parent
OUT = HERE / "ledger-tts-out"

TORCH_CUDA_INDEX = "https://download.pytorch.org/whl/cu126"

# --------------------------------------------------------------- the lines

VOICES = {
    "lena":    "Lena, late 30s, the bar's bookkeeper. Dry, careful, has known the family twenty years.",
    "rocco":   "Rocco, 50s, works the door. Night circle. Tired, decent, seen everything.",
    "mara":    "Mara Ellis, 40s, police detective. Never threatens; does not need to.",
    "crowd_m": "An anonymous man on the street.",
    "crowd_f": "An anonymous woman on the street.",
}

FEMALE = ("lena", "mara", "crowd_f")

CASES = [
    ("bark_overheard_certain", "rocco", "low, leaning in, certain of what he saw",
     "I'm telling you, he was down at the warehouse the night it went up."),
    ("bark_overheard_doubtful", "crowd_f", "offhand, unconvinced, already moving on",
     "There's a story going round that he keeps hours nobody keeps. Probably nothing."),
    ("bark_warning", "rocco", "quiet warning between friends, not a threat",
     "I'd keep that behind my teeth if I were you."),
    ("emphasis_test", "lena", "the stress MUST land on 'your'",
     "That's your problem, not mine."),
    ("same_line_BORED", "lena", "bored, end of a long shift, barely listening",
     "So which is it going to be?"),
    ("same_line_GRAVE", "lena", "grave, the most serious question she has ever asked him",
     "So which is it going to be?"),
    ("long_dialogue", "lena", "steady, laying it out on the counter, no drama",
     "Seven days. You've seen what it is now. Mickey never chose. He let the street "
     "choose for him, a week at a time, and it used him up."),
    ("authority_cold", "mara", "polite, procedural, faintly bored - the menace is that there is none",
     "The inspection closes on day fourteen. Two days remain. You have been given "
     "what you asked for twice, and refused once."),
    ("ambient_prices", "crowd_m", "grumbling to a neighbour, mid-conversation",
     "Bread's gone up again. Again."),
    ("ambient_reply", "crowd_f", "resigned, half-shrug",
     "You'll get used to it. We always do."),
    ("refusal", "crowd_m", "shutting a door on the conversation, not hostile",
     "I've nothing for you today."),
    ("hard_prosody", "rocco", "numbers must sound SPOKEN, not read",
     "Your name's in Mickey's book for $120, and day 8 is when he'd have asked."),
]

CONSISTENCY_VOICE = "lena"
CONSISTENCY = [
    "Storeroom's nothing. Mind the step.",
    "You're back late.",
    "Mickey kept more than one set of books.",
    "I've known better people do worse for less.",
    "Don't ask me about the landlord.",
    "That's talk. People love talk.",
    "It'll turn. It always turns.",
    "I moved them because you asked me to.",
    "Seven days, and you've seen what it is.",
    "So which is it going to be?",
]

# Direction is a sentence written for a human actor. Engines that take a
# scalar need it turned into a number, and the two same_line cases have to
# land at opposite ends or the test proves nothing.
_FLAT = ("bored", "offhand", "resigned", "shrug", "unconvinced", "procedural",
         "no drama", "not hostile", "neutral")
_HOT = ("grave", "certain", "warning", "serious", "menace", "cold", "leaning in")


def intensity(direction):
    """0 = flat delivery, 1 = fully committed. Used by engines with a knob."""
    d = (direction or "").lower()
    if any(k in d for k in _FLAT):
        return 0.25
    if any(k in d for k in _HOT):
        return 0.8
    return 0.5


# --------------------------------------------------------------- utilities

def say(msg=""):
    print(msg, flush=True)


def rule(msg):
    say("\n" + "=" * 66)
    say(msg)
    say("=" * 66)


def venv_python(venv_dir):
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def has_nvidia():
    try:
        subprocess.run(["nvidia-smi"], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False


def gpu_kind():
    """What card is in the machine, and be honest about what it buys.

    "none detected" was misleading: it only ever meant "no nvidia-smi", so an
    AMD card read as no card at all and looked like a PATH problem to fix.
    It is not fixable. **PyTorch has no Windows AMD backend** — ROCm is Linux
    only — so on Windows every torch engine here runs on the CPU no matter
    what is in the case. torch-directml exists but does not carry models of
    this shape.

    That is worth knowing BEFORE waiting rather than after, and it is much
    less bad than it sounds: bark generation is offline and one-time, so slow
    is merely slow. It only rules out live dialogue on this machine, and only
    on this machine — what ships to players depends on THEIR card.
    """
    if has_nvidia():
        return "nvidia"
    if sys.platform.startswith("win"):
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_VideoController).Name"],
                capture_output=True, text=True, timeout=20).stdout.lower()
            if "radeon" in out or "amd" in out:
                return "amd"
            if "intel" in out:
                return "intel"
        except Exception:
            pass
    return "none"


def write_wav(path, samples, rate):
    path.parent.mkdir(parents=True, exist_ok=True)
    # A wav still open in an audio player is locked on Windows, and losing a
    # whole case because you were listening to the last run's copy is absurd.
    if path.exists():
        try:
            path.unlink()
        except OSError:
            for n in range(2, 20):
                alt = path.with_name(f"{path.stem}_{n}{path.suffix}")
                if not alt.exists():
                    say(f"    ({path.name} was open elsewhere — wrote {alt.name})")
                    path = alt
                    break
    try:
        import numpy as np
        a = samples
        if hasattr(a, "detach"):
            a = a.detach().cpu().numpy()
        a = np.asarray(a).squeeze()
        if a.dtype.kind == "f":
            a = (np.clip(a, -1.0, 1.0) * 32767).astype("<i2")
        else:
            a = a.astype("<i2")
        raw = a.tobytes()
    except ImportError:
        import array
        raw = array.array("h", [int(max(-1.0, min(1.0, float(s))) * 32767)
                                for s in samples]).tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(raw)


def length_of(samples, rate):
    try:
        n = len(samples)
    except TypeError:
        n = int(samples.shape[-1])
    if n == 0:
        return 0.0
    return n / float(rate)


def peak_vram_mb():
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.max_memory_allocated() / (1024 * 1024)
    except Exception:
        pass
    return None


def device():
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def refs_dir():
    """Reference clips for the cloning engines, keyed by stem.

    THE IDEA THAT MAKES CLONING A DIRECTION MECHANISM. A cloning model has
    no exaggeration dial, so it looks undirectable — but it copies the
    delivery of whatever it is given, which means the reference clip IS the
    direction. Drop `lena.wav`, `lena.grave.wav` and `lena.bored.wav` and a
    clone engine can be told how to say a line after all, using the same
    stage direction the scalar engines get.

    That matters because the game knows the mood of every line it will ever
    generate, and there are only a handful of moods — so this scales to
    thousands of barks off five minutes of reference audio.
    """
    d = HERE / "refs"
    out = {}
    if d.exists():
        for f in sorted(d.glob("*.wav")):
            out[f.stem] = str(f)
    return out


def ref_for(refs, voice, direction):
    """Best available clip: mood-matched first, plain voice second."""
    if not refs:
        return None
    i = intensity(direction)
    mood = "grave" if i >= 0.7 else "bored" if i <= 0.3 else None
    if mood and f"{voice}.{mood}" in refs:
        return refs[f"{voice}.{mood}"]
    return refs.get(voice)


def allow_full_torch_load():
    """torch 2.6 flipped torch.load to weights_only=True by default, which
    breaks every TTS checkpoint that carries a config object. This is the
    single most common reason a working engine suddenly stops loading."""
    import torch
    if getattr(torch.load, "_ledger_patched", False):
        return
    original = torch.load

    def patched(*a, **k):
        k["weights_only"] = False
        return original(*a, **k)

    patched._ledger_patched = True
    torch.load = patched


# ---------------------------------------------------------------- engines

class Kokoro:
    name = "kokoro"
    note = "small and fast; American English. The live-dialogue bet."
    # misaki[en] is what actually turns text into phonemes, and it carries a
    # bundled espeak-ng so Windows needs no MSI. Leaving it out is why kokoro
    # installs cleanly and then refuses to run.
    pkgs = ("kokoro>=0.9.4", "misaki[en]", "soundfile", "numpy", "huggingface_hub")
    probe = "kokoro"          # importable == installed
    directable = False
    MAP = {"lena": "af_heart", "mara": "af_bella", "crowd_f": "af_sarah",
           "rocco": "am_michael", "crowd_m": "am_adam"}

    def load(self):
        from kokoro import KPipeline
        try:
            self.pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
        except TypeError:
            self.pipe = KPipeline(lang_code="a")      # older signature

    def synth(self, text, voice, direction):
        import numpy as np
        parts = []
        # No emotion control, so the only lever is pace. It is a weak lever
        # and the listening test should say so honestly.
        speed = 0.92 + 0.16 * intensity(direction)
        for chunk in self.pipe(text, voice=self.MAP.get(voice, "af_heart"), speed=speed):
            audio = getattr(chunk, "audio", None)
            if audio is None:
                audio = chunk[2] if isinstance(chunk, (tuple, list)) else chunk
            if hasattr(audio, "detach"):
                audio = audio.detach().cpu().numpy()
            parts.append(np.asarray(audio).squeeze())
        if not parts:
            raise RuntimeError("kokoro produced no audio for this line")
        return np.concatenate(parts), 24000


class Chatterbox:
    name = "chatterbox"
    note = "explicit EXAGGERATION control + zero-shot cloning. The answer to piper's flat affect."
    # resemble-perth named explicitly because chatterbox constructs its
    # watermarker unconditionally and never declares it loudly enough.
    pkgs = ("chatterbox-tts", "resemble-perth")
    probe = "chatterbox.tts"          # importable == installed
    directable = True

    @staticmethod
    def fix_watermarker():
        """chatterbox's constructor ends with

            self.watermarker = perth.PerthImplicitWatermarker()

        unconditionally. resemble-perth's __init__ wraps its own imports in
        a try/except and binds the name to None when they fail, so a broken
        dependency does not surface as an ImportError at import time — it
        surfaces 3.2 GB of model downloads later as 'NoneType object is not
        callable', pointing at a line that looks perfectly fine.

        So: find out why it is None, say so, and substitute a no-op rather
        than lose the only engine in this benchmark with a direction control
        to a watermarking library we are not testing.

        NOTE FOR SHIPPING, not for the benchmark: the watermarker exists so
        generated speech stays identifiable as generated. If chatterbox wins,
        fix perth properly and keep it — do not carry this stub forward.
        """
        try:
            import perth
        except ImportError as e:
            return f"perth is not installed at all ({e})"
        if getattr(perth, "PerthImplicitWatermarker", None) is not None:
            return None

        reason = "no reason reported"
        try:
            import perth.perth_net.perth_net_implicit.perth_watermarker  # noqa: F401
        except Exception as e:
            reason = f"{type(e).__name__}: {e}"

        class _NoWatermark:
            def apply_watermark(self, wav, watermark=None, sample_rate=44100, **kw):
                return wav

            def get_watermark(self, *a, **kw):
                return None

        perth.PerthImplicitWatermarker = _NoWatermark
        return reason

    def load(self):
        allow_full_torch_load()
        why = self.fix_watermarker()
        if why:
            say(f"  perth's watermarker was unusable, running without it: {why}")
        from chatterbox.tts import ChatterboxTTS
        self.model = ChatterboxTTS.from_pretrained(device=device())
        self.rate = int(getattr(self.model, "sr", 24000))
        self.refs = refs_dir()
        if not self.refs:
            say("  (no ./refs/*.wav — using the model's default voice; cloning untested)")

    def synth(self, text, voice, direction):
        i = intensity(direction)
        kw = {}
        ref = ref_for(self.refs, voice, direction)
        if ref:
            kw["audio_prompt_path"] = ref
        try:
            wav = self.model.generate(
                text,
                exaggeration=0.3 + 0.6 * i,
                # Lower cfg_weight slows the pace, which is what stops a
                # committed reading from turning into a rushed one.
                cfg_weight=0.5 - 0.2 * i,
                **kw)
        except TypeError:
            wav = self.model.generate(text, **kw)
        return wav, self.rate


class XTTS:
    name = "xtts"
    note = "voice CLONING. If its clones hold up, the pre-generated/live seam disappears."
    # torch and torchaudio named EXPLICITLY. coqui-tts declares them, pip
    # exited 0, and the environment came out with no torch in it — so the
    # declaration is not something to rely on. Naming them costs nothing when
    # they would have been installed anyway.
    pkgs = ("torch", "torchaudio", "coqui-tts")   # the maintained fork; the abandoned "TTS" caps out below py3.12
    probe = "TTS.api"          # importable == installed
    directable = False

    # xtts_v2 ships ~58 studio speakers, so this runs with NO reference clips
    # at all. Requiring refs is why it produced nothing last time.
    PREFERRED = {"lena": "Sofia Hellen", "mara": "Brenda Stern",
                 "crowd_f": "Ana Florence", "rocco": "Damien Black",
                 "crowd_m": "Craig Gutsy"}

    def load(self):
        os.environ["COQUI_TOS_AGREED"] = "1"
        allow_full_torch_load()
        from TTS.api import TTS
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device())
        self.speakers = [s for s in (getattr(self.tts, "speakers", None) or [])]
        self.refs = refs_dir()
        if self.refs:
            say(f"  cloning from ./refs/: {', '.join(sorted(self.refs))}")
        elif self.speakers:
            say(f"  {len(self.speakers)} built-in speakers; cloning untested "
                f"(drop 6-10s wavs in ./refs/ to test it)")

    def speaker_for(self, voice):
        want = self.PREFERRED.get(voice)
        if want and want in self.speakers:
            return want
        if not self.speakers:
            return None
        # Deterministic fallback so a rerun gives the same voice: sorted
        # order, offset by where this voice sits in our own cast.
        order = sorted(self.speakers)
        idx = sorted(VOICES).index(voice) if voice in VOICES else 0
        return order[(idx * 7) % len(order)]

    def synth(self, text, voice, direction):
        ref = ref_for(self.refs, voice, direction)
        if ref:
            return self.tts.tts(text=text, speaker_wav=ref, language="en"), 24000
        sp = self.speaker_for(voice)
        if sp is None:
            raise RuntimeError("no built-in speakers and no ./refs/*.wav — cannot synthesise")
        return self.tts.tts(text=text, speaker=sp, language="en"), 24000


class Piper:
    name = "piper"
    note = "CPU-only, very fast, lower ceiling. THE CONTROL CASE (already judged: too synthetic)."
    pkgs = ("piper-tts",)
    probe = "piper"          # importable == installed
    directable = False

    VOICE_URL = ("https://huggingface.co/rhasspy/piper-voices/resolve/main/"
                 "en/en_US/lessac/medium/en_US-lessac-medium.onnx")

    def load(self):
        from piper import PiperVoice
        model = os.environ.get("PIPER_MODEL", "")
        if not model or not Path(model).exists():
            model = str(fetch(self.VOICE_URL, "en_US-lessac-medium.onnx"))
            fetch(self.VOICE_URL + ".json", "en_US-lessac-medium.onnx.json")
        self.voice = PiperVoice.load(model)

    def synth(self, text, voice, direction):
        """Piper's API has changed shape across versions; try each in turn
        rather than pinning a version that may not exist tomorrow."""
        import io, array
        rate = int(getattr(getattr(self.voice, "config", None), "sample_rate", 22050))

        try:
            chunks = list(self.voice.synthesize(text))
            if chunks and hasattr(chunks[0], "audio_int16_bytes"):
                raw = b"".join(c.audio_int16_bytes for c in chunks)
                rate = int(getattr(chunks[0], "sample_rate", rate))
                return array.array("h", raw), rate
        except TypeError:
            pass                      # older signature wants a second argument

        if hasattr(self.voice, "synthesize_stream_raw"):
            raw = b"".join(self.voice.synthesize_stream_raw(text))
            return array.array("h", raw), rate

        # Oldest: writes into a wave file we must configure FIRST — not
        # doing so is exactly the "# channels not specified" error.
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
            self.voice.synthesize(text, w)
        buf.seek(0)
        with wave.open(buf, "rb") as r:
            return array.array("h", r.readframes(r.getnframes())), r.getframerate()


class Eleven:
    """OPT-IN ONLY. Never installed or run unless explicitly requested, and it
    needs a key you create yourself. It exists purely to calibrate the ceiling
    — the free tier covers this benchmark several times over."""
    name = "eleven"
    note = "PAID reference (opt-in). Calibrates how far local actually is from the ceiling."
    pkgs = ("elevenlabs",)
    probe = "elevenlabs"          # importable == installed
    directable = False
    opt_in = True

    IDS = {"lena": "EXAVITQu4vr4xnSDxMaL",     # Bella
           "mara": "21m00Tcm4TlvDq8ikWAM",     # Rachel
           "crowd_f": "MF3mGyEYCl7XYWbV9V6O",  # Elli
           "rocco": "pNInz6obpgDQGcFmaJgB",    # Adam
           "crowd_m": "ErXwobaYiN019PkySvjV"}  # Antoni

    def load(self):
        key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
        if not key:
            raise RuntimeError(
                "set ELEVENLABS_API_KEY first (free tier is enough).\n"
                "    Windows:  setx ELEVENLABS_API_KEY \"...\"  then open a new terminal")
        from elevenlabs.client import ElevenLabs
        self.client = ElevenLabs(api_key=key)

    def synth(self, text, voice, direction):
        import array
        stream = self.client.text_to_speech.convert(
            voice_id=self.IDS.get(voice, self.IDS["lena"]),
            model_id="eleven_multilingual_v2",
            text=text,
            output_format="pcm_24000")
        raw = b"".join(stream)
        return array.array("h", raw), 24000


ENGINES = [Kokoro(), Chatterbox(), XTTS(), Piper(), Eleven()]
BY_NAME = {e.name: e for e in ENGINES}
DEFAULT_ORDER = ["kokoro", "chatterbox", "xtts", "piper"]


def fetch(url, filename):
    """Download a model file next to the script, once."""
    dest = HERE / "models" / filename
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    import urllib.request
    say(f"  downloading {filename} ...")
    urllib.request.urlretrieve(url, dest)
    say(f"  got {dest.stat().st_size // (1024*1024)} MB")
    return dest


# --------------------------------------------------------------- the worker

def run_engine(engine, quick):
    """Runs INSIDE that engine's own venv. Writes audio, report.md, result.json."""
    outdir = OUT / engine.name
    outdir.mkdir(parents=True, exist_ok=True)
    result = {"engine": engine.name, "ok": False, "error": None,
              "median_rtf": None, "vram_mb": None, "device": None, "rows": []}

    say(f"\n=== {engine.name} — {engine.note}")
    t0 = time.time()
    try:
        engine.load()
    except Exception as e:
        detail = traceback.format_exc()
        (outdir / "error.txt").write_text(detail, encoding="utf-8")
        say(f"  ! could not load: {type(e).__name__}: {e}")
        for line in detail.strip().splitlines()[-6:]:
            say(f"    | {line}")
        say(f"    full traceback -> {outdir / 'error.txt'}")
        result["error"] = f"{type(e).__name__}: {e}"
        (outdir / "result.json").write_text(json.dumps(result), encoding="utf-8")
        return result

    result["device"] = device()
    say(f"  loaded in {time.time() - t0:.1f}s on {result['device']}")

    # Warm up OUTSIDE the timing loop. The first call always pays for lazy
    # imports and kernel compilation, and last run that made case one look
    # ten times slower than every other case.
    try:
        engine.synth("Ready.", CONSISTENCY_VOICE, "neutral")
    except Exception:
        pass

    cases = CASES[:6] if quick else CASES
    rtfs, failures = [], 0

    for cid, voice, direction, text in cases:
        try:
            t = time.time()
            samples, rate = engine.synth(text, voice, direction)
            gen = time.time() - t
            dur = length_of(samples, rate)
            if dur <= 0:
                raise RuntimeError("produced zero samples")
            rtf = gen / dur
            rtfs.append(rtf)
            write_wav(outdir / f"{cid}.wav", samples, rate)
            result["rows"].append([cid, voice, f"{dur:.1f}s", f"{gen:.2f}s", f"{rtf:.2f}"])
            say(f"  {cid:26} {dur:5.1f}s audio  {gen:5.2f}s gen  RTF {rtf:.2f}")
        except Exception as e:
            failures += 1
            say(f"  ! {cid}: {type(e).__name__}: {e}")
            result["rows"].append([cid, voice, "-", "-", f"FAILED {type(e).__name__}: {e}"])
            if failures == 1:
                (outdir / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")

    say("  --- consistency probe (the decisive one)")
    for i, text in enumerate(CONSISTENCY[:4] if quick else CONSISTENCY):
        try:
            samples, rate = engine.synth(text, CONSISTENCY_VOICE, "neutral, in character")
            write_wav(outdir / "CONSISTENCY" / f"{i:02d}.wav", samples, rate)
        except Exception as e:
            say(f"  ! consistency {i}: {type(e).__name__}: {e}")
            break

    result["vram_mb"] = peak_vram_mb()
    result["median_rtf"] = statistics.median(rtfs) if rtfs else None
    result["ok"] = bool(rtfs)
    if not result["ok"] and not result["error"]:
        result["error"] = "loaded, but every line failed to synthesise"

    with (outdir / "report.md").open("w", encoding="utf-8") as f:
        f.write(f"# {engine.name}\n\n{engine.note}\n\n")
        f.write(f"- device: {result['device']}\n")
        f.write(f"- peak VRAM: {result['vram_mb']:.0f} MB\n"
                if result["vram_mb"] else "- peak VRAM: n/a (CPU)\n")
        if result["median_rtf"] is not None:
            f.write(f"- median RTF: {result['median_rtf']:.2f} "
                    f"(under 0.35 = usable for LIVE dialogue)\n")
        f.write(f"- takes direction: {'yes' if engine.directable else 'no (text only)'}\n")
        f.write("\n| case | voice | audio | gen | RTF |\n|---|---|---|---|---|\n")
        for r in result["rows"]:
            f.write("| " + " | ".join(r) + " |\n")

    (outdir / "result.json").write_text(json.dumps(result), encoding="utf-8")
    return result


# --------------------------------------------------------------- the driver

def ensure_venv(engine, assume_yes):
    """One environment per engine. THE REASON: these packages pin conflicting
    torch versions, and last time installing one quietly broke the next. A
    private venv each means an engine can only ever fail on its own terms."""
    venv_dir = HERE / f".venv-{engine.name}"
    py = venv_python(venv_dir)
    stamp = venv_dir / ".ledger-installed"

    def works():
        if not py.exists():
            return False
        return subprocess.run([str(py), "-c", f"import {engine.probe}"],
                              capture_output=True, text=True).returncode == 0

    # RE-PROBE EVEN A STAMPED VENV. v6 added an install check and it never
    # ran: the broken .venv-xtts from v5 still had its "installed" stamp, so
    # the early return fired and the environment sailed straight past the
    # verification added to catch exactly it. A stamp records that we once
    # finished installing, not that the result works — and only the second
    # of those is worth anything.
    if stamp.exists() and works():
        return py
    if stamp.exists():
        say(f"\n  {venv_dir.name} exists but cannot 'import {engine.probe}' — repairing it")
        stamp.unlink(missing_ok=True)

    if not py.exists():
        say(f"\n  building {venv_dir.name}  (a few GB; your main Python is untouched)")
        if not assume_yes:
            try:
                if input("  go ahead? [Y/n] ").strip().lower() in ("n", "no"):
                    return None
            except EOFError:
                pass
        try:
            subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
        except subprocess.CalledProcessError as e:
            say(f"  ! could not create the venv: {e}")
            return None

    def pip(*args, quiet=True):
        cmd = [str(py), "-m", "pip", "install", *(["--quiet"] if quiet else []), *args]
        return subprocess.call(cmd)

    pip("--upgrade", "pip", "wheel")
    say(f"  installing {' '.join(engine.pkgs)} ... (this is the slow part)")
    code = pip(*engine.pkgs)

    # TRUST NOTHING. pip exited 0 for coqui-tts and left the environment
    # without torch in it, so the engine failed later with a bare
    # ModuleNotFoundError and the actual resolution failure was invisible —
    # --quiet had swallowed it. An install is not finished until the thing
    # it was supposed to install can be imported.
    probe = subprocess.run([str(py), "-c", f"import {engine.probe}"],
                           capture_output=True, text=True)
    if code != 0 or probe.returncode != 0:
        say(f"  ! {engine.name} did not install cleanly. Re-running pip loudly so the")
        say(f"    real reason is on screen rather than hidden behind --quiet:")
        pip(*engine.pkgs, quiet=False)
        probe = subprocess.run([str(py), "-c", f"import {engine.probe}"],
                               capture_output=True, text=True)
        if probe.returncode != 0:
            tail = (probe.stderr or "").strip().splitlines()[-3:]
            say(f"  ! still cannot 'import {engine.probe}':")
            for t in tail:
                say(f"      {t}")
            return None
        say(f"  the retry fixed it — carrying on.")

    # If there is an NVIDIA card, make sure torch can actually see it. pip's
    # default wheel on Windows is CPU-only, which turns a 0.2 RTF into a 5.0
    # and makes the speed column meaningless.
    if has_nvidia():
        probe = ("import torch,sys;"
                 "print(torch.__version__, torch.cuda.is_available())")
        r = subprocess.run([str(py), "-c", probe], capture_output=True, text=True)
        if r.returncode == 0 and "False" in r.stdout:
            ver = r.stdout.split()[0].split("+")[0]
            say(f"  NVIDIA card found but torch {ver} is CPU-only — fetching the CUDA build")
            pip(f"torch=={ver}", "torchaudio", "--index-url", TORCH_CUDA_INDEX)

    stamp.write_text("ok", encoding="utf-8")
    return py


def drive(names, args):
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for name in names:
        engine = BY_NAME[name]
        py = ensure_venv(engine, args.yes)
        if py is None:
            results.append({"engine": name, "ok": False,
                            "error": "environment could not be built"})
            if not args.keep_going:
                say("  (--keep-going to carry on past this)")
            continue
        cmd = [str(py), str(Path(__file__).resolve()), "--worker", name]
        if args.quick:
            cmd.append("--quick")
        subprocess.call(cmd)
        rp = OUT / name / "result.json"
        if rp.exists():
            results.append(json.loads(rp.read_text(encoding="utf-8")))
        else:
            results.append({"engine": name, "ok": False,
                            "error": "the worker exited without writing a result"})
    return results


def summarise(results):
    rule("RESULTS")
    say(f"{'engine':12} {'status':10} {'RTF':>6}  {'VRAM':>8}  direction  notes")
    lines = []
    for r in results:
        e = BY_NAME.get(r["engine"])
        rtf = f"{r['median_rtf']:.2f}" if r.get("median_rtf") is not None else "-"
        vram = f"{r['vram_mb']:.0f}MB" if r.get("vram_mb") else (r.get("device") or "-")
        status = "ok" if r.get("ok") else "FAILED"
        direct = ("yes" if e and e.directable else "no ") if e else "?  "
        note = "" if r.get("ok") else (r.get("error") or "")
        say(f"{r['engine']:12} {status:10} {rtf:>6}  {vram:>8}  {direct:9}  {note[:40]}")
        lines.append(f"| {r['engine']} | {status} | {rtf} | {vram} | {direct.strip()} | {note} |")

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "SUMMARY.md").open("w", encoding="utf-8") as f:
        f.write(f"# LEDGER TTS benchmark\n\nv{VERSION}\n\n")
        f.write("| engine | status | median RTF | VRAM/device | takes direction | note |\n")
        f.write("|---|---|---|---|---|---|\n")
        f.write("\n".join(lines) + "\n")
        f.write("\nRTF under 0.35 = fast enough to voice dialogue live.\n")

    failed = [r for r in results if not r.get("ok")]
    if failed:
        say("\nDidn't produce audio:")
        for r in failed:
            say(f"  {r['engine']}: {r.get('error')}")
            p = OUT / r["engine"] / "error.txt"
            if p.exists():
                say(f"    full traceback: {p}")
        say("\n  ^ paste those lines to me and I'll fix them.")


def listening_guide(results):
    ok = [r["engine"] for r in results if r.get("ok")]
    if not ok:
        return
    rule("NOW LISTEN, IN THIS ORDER")
    say(f"""Engines with audio: {', '.join(ok)}
Piper is already judged — it is the FLOOR. The question for every other
engine is only: is it audibly better than piper, and by how much?

1. same_line_BORED.wav  vs  same_line_GRAVE.wav      <-- THE HEADLINE TEST
   Identical text, opposite direction. Piper scored zero here. If an engine
   makes these obviously different, that alone justifies choosing it: it
   means the game can direct its own actors from simulation state.

2. CONSISTENCY/00..09.wav — play straight through.
   Piper was "consistent but literally all of them sound the same." That is
   flat affect, not character. Listen for one person who is ALIVE, not one
   person who is uniform.

3. emphasis_test.wav — "That's YOUR problem." Does the stress land on
   'your'? Best single test of whether a model reads meaning or words.

4. hard_prosody.wav — "$120" as 'a hundred and twenty', "day 8" as
   'day eight'? Piper got this right, so it is table stakes, not a win.

5. long_dialogue.wav — does it stay alive to the end, or flatten out?

Then per engine, in one line each: better than piper or not, and where.
""")


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--engine", default="all",
                    help="all | a name | a comma list (kokoro,chatterbox,xtts,piper,eleven)")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--keep-going", action="store_true", default=True)
    ap.add_argument("--worker", default=None, help=argparse.SUPPRESS)
    a = ap.parse_args()

    # Worker mode: we are already inside an engine's venv.
    if a.worker:
        e = BY_NAME.get(a.worker)
        if e is None:
            say(f"unknown engine '{a.worker}'")
            return 2
        return 0 if run_engine(e, a.quick)["ok"] else 1

    say(f"LEDGER TTS benchmark   v{VERSION}")
    kind = gpu_kind()
    say(f"python {sys.version.split()[0]}   gpu: {kind}")
    say(f"output: {OUT}")
    if kind in ("amd", "intel"):
        say(f"\n  NOTE: torch has no Windows {kind.upper()} backend (ROCm is Linux only), so")
        say("  every engine here runs on the CPU. Nothing is misconfigured and there")
        say("  is nothing to fix. Budget MINUTES per engine, not seconds, and do not")
        say("  kill it when it goes quiet — chatterbox and xtts are the slow ones.")
        say("  This matters less than it looks: barks are generated offline, once.")
        say("  It only rules out LIVE dialogue on this machine, and what ships to")
        say("  players depends on their card, not yours.")

    if a.engine == "all":
        names = list(DEFAULT_ORDER)
    else:
        names = [n.strip() for n in a.engine.split(",") if n.strip()]
        bad = [n for n in names if n not in BY_NAME]
        if bad:
            say(f"no such engine: {', '.join(bad)}  "
                f"(have: {', '.join(BY_NAME)})")
            return 2

    # piper is already judged; running it again is only useful as an
    # A/B reference, and it is cheap, so keep it — but say why it is there.
    say(f"\nrunning: {', '.join(names)}")
    say("each engine gets its OWN environment, so one bad install cannot")
    say("break the next. First run downloads models and is slow.")

    results = drive(names, a)
    summarise(results)
    listening_guide(results)

    say(f"\nAudio and reports: {OUT}")
    if not a.no_open:
        try:
            if sys.platform.startswith("win"):
                os.startfile(OUT)                                   # noqa
            elif sys.platform == "darwin":
                subprocess.run(["open", str(OUT)], check=False)
            else:
                subprocess.run(["xdg-open", str(OUT)], check=False)
        except Exception:
            pass
    return 0 if any(r.get("ok") for r in results) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        say("\nstopped.")
        sys.exit(130)
