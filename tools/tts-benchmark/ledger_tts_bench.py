#!/usr/bin/env python3
"""
LEDGER — local TTS benchmark.  ONE FILE.  Download it, run it.

    python ledger_tts_bench.py

That is the whole thing. It checks what is installed, offers to install what
is missing, generates the audio, and tells you what to listen for. No repo,
no config, no other files.

Options (all optional):
    --yes            install missing engines without asking
    --engine kokoro  just one engine (kokoro | xtts | piper)
    --quick          fewer lines, faster pass
    --no-open        do not open the output folder at the end

WHAT THIS IS DECIDING, in order of importance:

  1. CONSISTENCY — ten lines, one character, back to back. A model that
     cannot make them sound like ONE PERSON cannot voice a character however
     good any single line is. This decides the whole voice architecture.
  2. DIRECTION — the same sentence, once bored, once grave. Our advantage
     over recorded barks is that the game always knows how the speaker
     feels; a model that ignores direction throws that away.
  3. SPEED — real-time factor. Under ~0.35 we can voice live dialogue with
     no perceptible wait. Over ~1.0 it is offline-only.
  4. FOOTPRINT — VRAM, because this ships to players.

The lines are real game dialogue. Testing TTS on "the quick brown fox" tells
you nothing.
"""

import argparse
import os
import statistics
import subprocess
import sys
import time
import wave
from pathlib import Path

# Bumped on every change. Printed at startup so a stale copy in the Downloads
# folder announces itself instead of reproducing an old failure exactly.
VERSION = "2026-07-28.4  (clean-venv bootstrap, piper API drift, real errors)"

OUT = Path(__file__).parent / "ledger-tts-out"

# --------------------------------------------------------------- the lines

VOICES = {
    "lena":    "Lena, late 30s, the bar's bookkeeper. Dry, careful, has known the family twenty years.",
    "rocco":   "Rocco, 50s, works the door. Night circle. Tired, decent, seen everything.",
    "mara":    "Mara Ellis, 40s, police detective. Never threatens; does not need to.",
    "crowd_m": "An anonymous man on the street.",
    "crowd_f": "An anonymous woman on the street.",
}

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

# --------------------------------------------------------------- utilities

def say(msg=""):
    print(msg, flush=True)


def in_venv():
    return sys.prefix != sys.base_prefix


def venv_python(venv_dir):
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def bootstrap_clean_env(assume_yes):
    """Build our own environment and re-run inside it.

    THE REASON: installing TTS engines into whatever interpreter happens to
    be on PATH means fighting whatever is already there. Jafar's miniconda
    base carried a years-old torch (pytorch-lightning 1.7.6), and every
    modern engine failed with `cannot import name 'DTensor'` — a version
    conflict that has nothing to do with the engines and cannot be fixed by
    reinstalling them. A private venv sidesteps the whole class of problem.
    """
    venv_dir = Path(__file__).parent / ".ledger-tts-venv"
    py = venv_python(venv_dir)
    if not py.exists():
        say(f"\n  Building a clean environment in {venv_dir.name}")
        say("  (your main Python is left completely alone)")
        if not assume_yes:
            try:
                if input("  Go ahead? [Y/n] ").strip().lower() in ("n", "no"):
                    return None
            except EOFError:
                pass
        try:
            subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
            subprocess.check_call([str(py), "-m", "pip", "install", "--quiet",
                                   "--upgrade", "pip"])
        except subprocess.CalledProcessError as e:
            say(f"  ! could not create the venv: {e}")
            return None
    return py


def pip_install(*pkgs, assume_yes=False):
    say(f"\n  Need: {' '.join(pkgs)}")
    if not assume_yes:
        try:
            if input("  Install now with pip? [y/N] ").strip().lower() not in ("y", "yes"):
                return False
        except EOFError:
            return False
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", *pkgs])
        return True
    except subprocess.CalledProcessError as e:
        say(f"  ! pip failed ({e}). Install by hand and re-run.")
        return False


def fetch(url, filename):
    """Download a model file next to the script, once."""
    dest = Path(__file__).parent / "models" / filename
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    import urllib.request
    say(f"  downloading {filename} ...")
    try:
        urllib.request.urlretrieve(url, dest)
        say(f"  got {dest.stat().st_size // (1024*1024)} MB")
    except Exception as e:
        raise RuntimeError(f"could not download {filename}: {e}")
    return dest


def write_wav(path, samples, rate):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import numpy as np
        a = np.asarray(samples).squeeze()
        if hasattr(a, "detach"):
            a = a.detach().cpu().numpy()
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
    return n / float(rate)


def peak_vram_mb():
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.max_memory_allocated() / (1024 * 1024)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------- engines

class Kokoro:
    name = "kokoro"
    note = "small and fast; American English is its strength. The live-dialogue bet."
    pkgs = ("kokoro", "soundfile", "numpy")
    MAP = {"lena": "af_heart", "mara": "af_bella", "crowd_f": "af_sarah",
           "rocco": "am_michael", "crowd_m": "am_adam"}

    def probe(self):
        try:
            import kokoro                                                 # noqa
            return True, ""
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"

    def load(self):
        from kokoro import KPipeline
        try:
            self.pipe = KPipeline(lang_code="a")      # American English
        except Exception as e:
            if "espeak" in str(e).lower():
                raise RuntimeError(
                    "kokoro needs espeak-ng for some words. On Windows install "
                    "the espeak-ng MSI from github.com/espeak-ng/espeak-ng/releases "
                    "and re-run.") from e
            raise

    def synth(self, text, voice, direction):
        import numpy as np
        parts = []
        for chunk in self.pipe(text, voice=self.MAP.get(voice, "af_heart")):
            audio = chunk[2] if isinstance(chunk, (tuple, list)) else chunk
            if hasattr(audio, "detach"):
                audio = audio.detach().cpu().numpy()
            parts.append(np.asarray(audio).squeeze())
        return np.concatenate(parts), 24000


class XTTS:
    name = "xtts"
    note = "voice CLONING. If its clones hold up, the pre-generated/live seam disappears."
    pkgs = ("coqui-tts",)   # the maintained fork; old "TTS" caps out below py3.12

    def probe(self):
        try:
            from TTS.api import TTS                                       # noqa
            return True, ""
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"

    def load(self):
        from TTS.api import TTS
        import torch
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        os.environ.setdefault("COQUI_TOS_AGREED", "1")
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(dev)
        self.refs = {}
        refdir = Path(__file__).parent / "refs"
        if refdir.exists():
            for f in refdir.glob("*.wav"):
                self.refs[f.stem] = str(f)
        if not self.refs:
            say("  ! xtts: no reference clips found, so cloning is untested.")
            say("    Put 6-10s of clean speech per voice in ./refs/ as")
            say("    lena.wav rocco.wav mara.wav crowd_m.wav crowd_f.wav")
            say("    (any clean American speech works for a test - even yours)")

    def synth(self, text, voice, direction):
        ref = self.refs.get(voice) or (next(iter(self.refs.values())) if self.refs else None)
        if ref is None:
            raise RuntimeError("no reference wav in ./refs/ - cloning cannot run")
        return self.tts.tts(text=text, speaker_wav=ref, language="en"), 24000


class Piper:
    name = "piper"
    note = "CPU-only, very fast, lower ceiling. The control case."
    pkgs = ("piper-tts",)

    def probe(self):
        try:
            import piper                                                  # noqa
            return True, ""
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"

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

        # Newest: synthesize() yields AudioChunk objects.
        try:
            chunks = list(self.voice.synthesize(text))
            if chunks and hasattr(chunks[0], "audio_int16_bytes"):
                raw = b"".join(c.audio_int16_bytes for c in chunks)
                rate = int(getattr(chunks[0], "sample_rate", rate))
                return array.array("h", raw), rate
        except TypeError:
            pass                      # older signature wants a second argument

        # Middle: a raw byte stream.
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


ENGINES = [Kokoro(), XTTS(), Piper()]


# -------------------------------------------------------------------- run

def run(engine, quick):
    say(f"\n=== {engine.name} — {engine.note}")
    t0 = time.time()
    try:
        engine.load()
    except Exception as e:
        say(f"  ! could not load: {e}")
        return None
    say(f"  loaded in {time.time() - t0:.1f}s")

    outdir = OUT / engine.name
    cases = CASES[:5] if quick else CASES
    rows, rtfs = [], []

    for cid, voice, direction, text in cases:
        try:
            t = time.time()
            samples, rate = engine.synth(text, voice, direction)
            gen = time.time() - t
            dur = length_of(samples, rate)
            rtf = gen / dur if dur > 0 else 0
            rtfs.append(rtf)
            write_wav(outdir / f"{cid}.wav", samples, rate)
            rows.append((cid, voice, f"{dur:.1f}s", f"{gen:.2f}s", f"{rtf:.2f}"))
            say(f"  {cid:26} {dur:5.1f}s audio  {gen:5.2f}s gen  RTF {rtf:.2f}")
        except Exception as e:
            say(f"  ! {cid}: {e}")
            rows.append((cid, voice, "-", "-", f"FAILED {e}"))

    say("  --- consistency probe (the decisive one)")
    lines = CONSISTENCY[:4] if quick else CONSISTENCY
    for i, text in enumerate(lines):
        try:
            samples, rate = engine.synth(text, CONSISTENCY_VOICE, "neutral, in character")
            write_wav(outdir / "CONSISTENCY" / f"{i:02d}.wav", samples, rate)
        except Exception as e:
            say(f"  ! consistency {i}: {e}")
            break
    say(f"  wrote {outdir / 'CONSISTENCY'}")

    v = peak_vram_mb()
    outdir.mkdir(parents=True, exist_ok=True)   # nothing may have been written
    rep = outdir / "report.md"
    with rep.open("w", encoding="utf-8") as f:
        f.write(f"# {engine.name}\n\n{engine.note}\n\n")
        f.write(f"- peak VRAM: {v:.0f} MB\n" if v else "- peak VRAM: n/a (CPU)\n")
        if rtfs:
            f.write(f"- median RTF: {statistics.median(rtfs):.2f} "
                    f"(under 0.35 = usable for LIVE dialogue)\n")
        f.write("\n| case | voice | audio | gen | RTF |\n|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(r) + " |\n")
    return rep


def listening_guide():
    say("""
==================== NOW LISTEN, IN THIS ORDER ====================

1. CONSISTENCY/00..09.wav  — play all of them straight through.
   *Is this one person?*  If not, that engine cannot voice a character,
   whatever any single line sounded like. This decides everything.

2. same_line_BORED.wav  vs  same_line_GRAVE.wav
   Identical text, opposite direction. Obviously different, or the same
   reading twice?

3. emphasis_test.wav — "That's YOUR problem." Does the stress land on
   'your'? Best single test of whether a model reads meaning or words.

4. hard_prosody.wav — is "$120" spoken as 'a hundred and twenty' and
   "day 8" as 'day eight'? Or read out as symbols?

5. long_dialogue.wav — does it stay alive to the end, or flatten out?

Then tell me, per engine: one person or several? did direction land? did
the emphasis land? and did anything sound obviously synthetic — and how?
That last one is the bar you set.
===================================================================
""")


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--engine", default="all")
    ap.add_argument("--yes", action="store_true", help="install missing engines without asking")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--here", action="store_true",
                    help="install into the current Python instead of a private venv")
    a = ap.parse_args()

    say(f"LEDGER TTS benchmark   v{VERSION}")
    say(f"python {sys.version.split()[0]}{'  (private venv)' if in_venv() else ''}")
    say(f"output: {OUT}")

    chosen = [e for e in ENGINES if a.engine in ("all", e.name)]
    if not chosen:
        say(f"no such engine '{a.engine}' (kokoro | xtts | piper | all)")
        return 2

    missing = [e for e in chosen if not e.probe()[0]]

    # Anything to install? Do it in OUR OWN environment, not whatever
    # interpreter happens to be on PATH, and re-run in there.
    if missing and not in_venv() and not a.here:
        py = bootstrap_clean_env(a.yes)
        if py:
            say("  re-running inside the clean environment...\n")
            cmd = [str(py), str(Path(__file__).resolve())] + sys.argv[1:]
            return subprocess.call(cmd)
        say("  carrying on in the current environment instead.")

    if missing:
        say("\nNot installed yet:")
        for e in missing:
            say(f"  {e.name:8} pip install {' '.join(e.pkgs)}")
        if a.engine == "all" and len(missing) == len(chosen):
            say("\nStart with kokoro — smallest and fastest.")
        for e in missing:
            if pip_install(*e.pkgs, assume_yes=a.yes):
                # A package installed INTO A RUNNING PROCESS is invisible until
                # the import caches are dropped. Without this the engine you
                # just installed looks absent and silently never runs.
                import importlib
                importlib.invalidate_caches()
                ok, err = e.probe()
                say(f"  installed {e.name}" if ok else f"  installed {e.name}, but it will not import yet:")
                if not ok:
                    say(f"    {err}")
                    say(f"    -> this usually just needs a fresh process. Re-run the script.")

    ready = []
    for e in chosen:
        ok, err = e.probe()
        if ok:
            ready.append(e)
        elif e in missing:
            pass                      # already explained above
        else:
            say(f"\n=== {e.name}: cannot import — {err}")

    if not ready:
        say("\nNothing runnable in THIS process.")
        say("If something installed just now, simply run the script again —")
        say("a fresh process will pick it up.")
        return 1

    reports = [r for r in (run(e, a.quick) for e in ready) if r]
    if not reports:
        say("\nNo engine produced audio. Send me the errors above.")
        return 1

    listening_guide()
    say(f"Audio and reports: {OUT}")
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
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        say("\nstopped.")
        sys.exit(130)
