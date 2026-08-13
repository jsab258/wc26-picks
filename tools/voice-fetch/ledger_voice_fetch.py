#!/usr/bin/env python3
"""
LEDGER — voice reference fetcher.  ONE FILE.  Download it, run it.

    python ledger_voice_fetch.py

That is the whole thing. It builds its own environment, streams Mozilla
Common Voice, assembles about ten seconds of ONE SPEAKER per candidate,
and lays the candidates out in a web page with each character's casting
brief printed above its players. You listen and type numbers. Nothing else.

Options (all optional):
    --who lena,rocco        just these characters
    --candidates 8          how many DISTINCT voices per character (default 4)
    --source libritts       fallback corpus if Common Voice is unreachable
    --selftest              prove the assembly logic with no network at all
    --install               after you have filled in picks.txt: build the
                            final reference clips into ledger/Assets/Voices/
    --yes                   don't ask before installing packages
    --no-open               don't open the page when it is built

WHY THIS EXISTS

Chatterbox clones a voice from about ten seconds of reference audio. So we
do not pick a voice off a list — WHATEVER CLIP WE HAND IT BECOMES THE
CHARACTER. That inverts the usual casting problem: instead of hunting for a
voice that already sounds like Lena, we describe Lena and then find any clip
carrying that timbre. The briefs below are written as descriptions of what
must come through, not as preferences, which is the only reason this is
sourceable at all.

THE CONSENT RULE, held unprompted

Clips come only from corpora whose contributors donated their voices TO
BUILD SPEECH TECHNOLOGY. Common Voice (CC0) first, LibriTTS as fallback.
Not merely "free to copy" — public domain settles copyright and does not
settle consent, and a volunteer who read a novel aloud did not agree to
become a character in a crime game. No identifiable public figures, ever.

ABOUT MOODS — this changed, and it makes your job shorter

The casting doc asked for three clips per principal: neutral, grave, bored.
That was written before the direction test came back. Common Voice
contributors read neutral sentences, so a "grave" clip is not something that
corpus contains — but chatterbox has an explicit EXAGGERATION control, and
the benchmark proved it works on real game lines. So the reference clip
decides IDENTITY and exaggeration decides DIRECTION. One clip per character.

That takes the sourcing from 37 clips to 19, and your listening pass from
about forty minutes to about fifteen.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time as _time
import wave
from pathlib import Path

VERSION = "2026-07-28.1"

HERE = Path(__file__).resolve().parent
OUT = HERE / "ledger-voices-out"
PICKS = OUT / "picks.txt"
VENV = HERE / ".venv-voices"

# Chatterbox wants roughly this much of one speaker. Under about eight
# seconds the clone gets thin; over about fifteen it stops improving and
# starts costing generation time on every single line.
TARGET_SECONDS = 11.0
MIN_SECONDS = 8.0
SAMPLE_RATE = 24000


# ---------------------------------------------------------------------------
# THE CAST
#
# `want` is metadata to filter the corpus on; `brief` is what has to come
# through, printed above the players so you are judging against the character
# rather than against "which voice is nicest".
# ---------------------------------------------------------------------------

CAST = [
    dict(id="lena", name="LENA", tier="principal", accent="english", gender="female_feminine",
         age=("thirties", "fourties"),
         brief="Bar's bookkeeper, late 30s. Mid-low, dry, unhurried. She has "
               "known this family twenty years and is never surprised by it. "
               "WHAT MUST COME THROUGH: withheld judgement — she knows more "
               "than she says in every line. If it sounds like it is telling "
               "you everything, it is the wrong voice. Avoid bright, young, warm."),
    dict(id="rocco", name="ROCCO", tier="principal", accent="english", gender="male_masculine",
         age=("fourties", "fifties", "sixties"),
         brief="Works the door, 50s. Low, worn, slightly gravelly. Money is "
               "always a little short and it is audible. WHAT MUST COME "
               "THROUGH: decency without softness. Not a tough-guy voice — a "
               "tired one."),
    dict(id="ellis", name="MARA ELLIS", tier="principal", accent="english", gender="female_feminine",
         age=("fourties", "fifties"),
         brief="Detective, 40s. Level, unhurried, PLEASANT. WHAT MUST COME "
               "THROUGH: that she never has to raise her voice. Cast against "
               "type — pick the warmest, most reasonable voice here. A cold "
               "voice makes her a villain; a courteous one makes her inevitable."),
    dict(id="reese", name="TOBIAS REESE", tier="principal", accent="english", gender="male_masculine",
         age=("fourties", "fifties"),
         brief="Board of Excise, the audit's face. Precise, mid register, "
               "faintly bureaucratic. WHAT MUST COME THROUGH: that this is not "
               "personal. He is reading from a procedure and the procedure "
               "will convict you."),
    dict(id="kest", name="SERA KEST", tier="principal", accent="english", gender="female_feminine",
         age=("thirties", "fourties"),
         brief="Rival head. Controlled, harder than Lena, younger than Mara. "
               "WHAT MUST COME THROUGH: someone used to being agreed with."),

    # THE FOUR WHO WERE AUTHORED AND NEVER CAST, added 13 Aug.
    #
    # `voice-cast-check` has reported these as unvoiced for weeks and the
    # reason was one layer further back than anybody looked: they had no
    # entry HERE, so no clip could ever be fetched for them, so no voice
    # could ever be picked. Each currently draws from the crowd pool —
    # four named people, two of them central to an act, sounding like
    # passers-by, and nothing in the game says so out loud.
    #
    # Briefs are compressed from `game-design/cast-tier1-batch2.md` rather
    # than invented here: one source for who these people are.
    dict(id="aldous", name="ALDOUS VANE", tier="principal", accent="english",
         gender="male_masculine", age=("sixties", "seventies"),
         brief="Third-generation head of the Vane interests: property, law, "
               "and influence that never appears in a ledger. Sixty-one, "
               "silver, unhurried. Old money's grammar; apologises before "
               "ruining you. WHAT MUST COME THROUGH: he has never raised "
               "his voice because he has never needed to. If it sounds like "
               "it wants something from you, it is the wrong voice."),
    dict(id="danny", name="DANNY RO", tier="principal", accent="english",
         gender="male_masculine", age=("twenties", "thirties"),
         brief="Twenty-six, runs the New crew out of two clubs on the Strip. "
               "Loud on purpose, underestimated on purpose. Fast modern "
               "slang worn like a borrowed jacket, laughs at his own "
               "threats. WHAT MUST COME THROUGH: the quickness UNDER the "
               "recklessness — the costume is the loudness, not the man. "
               "Avoid anything genuinely stupid-sounding."),
    dict(id="june", name="JUNE", tier="principal", accent="english",
         gender="female_feminine", age=("thirties", "fourties"),
         brief="Mickey\'s estranged daughter, thirty-four, a nurse across "
               "town. Flat, clinical understatement; questions that are "
               "really diagnoses. WHAT MUST COME THROUGH: not hostility — "
               "hope, which is worse. She has already watched this business "
               "eat one man. Avoid warm, avoid bitter."),
    dict(id="zlata", name="ZLATA", tier="street", accent="english",
         gender="female_feminine", age=("fourties", "fifties"),
         brief="Runs dispatch at the port-side parcel office. Forty-three, "
               "loud laugh, rapid and teasing, nicknames within the hour, "
               "swears affectionately in three languages. WHAT MUST COME "
               "THROUGH: warmth that includes you before you agree to it — "
               "she is the first friend the honest life hands you free."),

    dict(id="sam", name="SAM", tier="street", accent="scottish", gender="male_masculine",
         age=("twenties", "thirties"),
         brief="Walks the block at all hours, trades in being useful. Mid-high, "
               "quick, ingratiating, never still. THE FASTEST TALKER IN THE "
               "GAME — the voice should sound like it is already moving on to "
               "the next person."),
    dict(id="ada", name="ADA", tier="street", accent="english", gender="female_feminine",
         age=("sixties", "seventies"),
         brief="Retired schoolteacher, the street's unofficial conscience. "
               "Older, clear, precise diction. WHAT MUST COME THROUGH: that "
               "she expects to be listened to, and is usually right."),
    dict(id="vesna", name="VESNA", tier="street", accent="northernirish", gender="female_feminine",
         age=("fourties", "fifties"),
         brief="Keeps house at the chapel, the quietest well of information. "
               "Soft, low volume, careful. QUIET IS THE CASTING — everything "
               "she knows arrived through a door left ajar."),
    dict(id="marla", name="MARLA", tier="street", accent="english", gender="female_feminine",
         age=("fourties", "fifties"),
         brief="Vegetable stall at the market corner. Warm, carrying, "
               "market-pitch. The loudest woman in the cast and the most "
               "ordinary."),
    dict(id="joey", name="JOEY", tier="street", accent="scottish", gender="male_masculine",
         age=("fourties", "fifties"),
         brief="Dock hand, twenty years on the water. Big, slow, plain. One "
               "daughter he would burn the port down for. SIMPLICITY IS THE "
               "CASTING — no irony in the voice at all."),
    dict(id="rita", name="RITA", tier="street", accent="scottish", gender="female_feminine",
         age=("thirties", "fourties"),
         brief="Left-handed, owes nobody an explanation. Blunt, flat, short. "
               "The one who ends conversations."),
    dict(id="hal", name="HAL", tier="street", accent="english", gender="male_masculine",
         age=("thirties", "fourties"),
         brief="Carries messages, meetings, prices, peace. Neutral to the "
               "point of being forgettable — DELIBERATELY THE LEAST "
               "DISTINCTIVE VOICE IN THE GAME. That is his job. If a candidate "
               "is interesting, it is wrong."),
    dict(id="emil", name="FATHER EMIL", tier="street", accent="irish", gender="male_masculine",
         age=("sixties", "seventies"),
         brief="Older, measured, resonant. Used to being heard in a room that "
               "goes quiet for him."),

    # Six anonymous voices. The bar here is INVERTED: a crowd voice you can
    # recognise stops being a crowd, so the right pick is the dullest one.
    dict(id="crowd_m1", name="CROWD — male, young", tier="crowd",
         accent="any", gender="male_masculine", age=("twenties",), brief=None),
    dict(id="crowd_m2", name="CROWD — male, middle", tier="crowd",
         accent="any", gender="male_masculine", age=("fourties",), brief=None),
    dict(id="crowd_m3", name="CROWD — male, older", tier="crowd",
         accent="any", gender="male_masculine", age=("sixties",), brief=None),
    dict(id="crowd_f1", name="CROWD — female, young", tier="crowd",
         accent="any", gender="female_feminine", age=("twenties",), brief=None),
    dict(id="crowd_f2", name="CROWD — female, middle", tier="crowd",
         accent="any", gender="female_feminine", age=("fourties",), brief=None),
    dict(id="crowd_f3", name="CROWD — female, older", tier="crowd",
         accent="any", gender="female_feminine", age=("sixties",), brief=None),
]

CROWD_BRIEF = ("Anonymous. The bar here is INVERTED: they must be "
               "UNMEMORABLE, because a crowd voice you can recognise stops "
               "being a crowd. Pick the dullest one. If a candidate is "
               "interesting, it is wrong.")

# What the game passes chatterbox per stage direction, now that direction is
# a parameter rather than a second clip. Written here because the fetcher is
# what the casting doc will point at, and a table that lives in two files
# drifts.
EXAGGERATION = {
    "neutral": 0.5,
    "bored":   0.25,
    "grave":   0.7,
    "urgent":  0.85,
    "warm":    0.6,
}


def brief_of(c):
    return c["brief"] or CROWD_BRIEF


# ---------------------------------------------------------------------------
# audio assembly — the part that is actually hard, and the part --selftest
# proves without touching the network
# ---------------------------------------------------------------------------

def assemble(clips, target=TARGET_SECONDS, rate=SAMPLE_RATE, gap=0.25):
    """Join one speaker's clips into a single reference of about `target`
    seconds, with a short silence between them.

    Common Voice sentences run three to six seconds, so a single clip is
    never enough for a clone. Concatenating the SAME SPEAKER is the whole
    trick — and the gap matters: butt-joined sentences give the model a
    speaker who never breathes, and it learns to generate that.

    Returns a float32 numpy array, or None if there was not enough.
    """
    import numpy as np

    if not clips:
        return None
    silence = np.zeros(int(rate * gap), dtype=np.float32)
    out, total = [], 0.0
    for c in clips:
        c = np.asarray(c, dtype=np.float32).reshape(-1)
        if c.size == 0:
            continue
        if out:
            out.append(silence)
            total += gap
        out.append(c)
        total += c.size / float(rate)
        # Stop at the target rather than at the clip that crosses it: an
        # extra four seconds is four seconds of nothing gained and a longer
        # wait on every generated line for the rest of the project.
        if total >= target:
            break
    if total < MIN_SECONDS:
        return None
    joined = np.concatenate(out)
    # Hard cap, so a single long clip cannot blow past the target.
    return joined[: int(rate * (target + 1.0))]


def normalise(samples, peak=0.89):
    """Match loudness across candidates so you are judging the VOICE and not
    the microphone. Peak rather than RMS: these are single speakers in
    quiet rooms, and RMS normalisation of a whisper lifts its room tone
    into the recording."""
    import numpy as np

    s = np.asarray(samples, dtype=np.float32).reshape(-1)
    m = float(np.max(np.abs(s))) if s.size else 0.0
    if m <= 1e-6:
        return s
    return s * (peak / m)


def resample(samples, src_rate, dst_rate=SAMPLE_RATE):
    """Linear resample. Good enough: this is reference audio for a cloner,
    not a master. Avoids dragging in scipy for one call."""
    import numpy as np

    s = np.asarray(samples, dtype=np.float32).reshape(-1)
    if src_rate == dst_rate or s.size == 0:
        return s
    n = int(round(s.size * dst_rate / float(src_rate)))
    if n <= 1:
        return np.zeros(0, dtype=np.float32)
    x = np.linspace(0.0, s.size - 1.0, n, dtype=np.float64)
    return np.interp(x, np.arange(s.size), s).astype(np.float32)


def write_wav(path, samples, rate=SAMPLE_RATE):
    import numpy as np

    s = np.clip(np.asarray(samples, dtype=np.float32).reshape(-1), -1.0, 1.0)
    pcm = (s * 32767.0).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())


def seconds_of(path):
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


# ---------------------------------------------------------------------------
# environment
# ---------------------------------------------------------------------------

# Split, because --selftest exercises the assembly logic and needs only
# numpy. Making a self-test wait on a 400MB dataset stack is how a self-test
# stops being run.
CORE_PKGS = ["numpy"]
# PINNED BELOW 3 DELIBERATELY. v3 dropped dataset loading scripts, which
# killed the only Common Voice mirror we can reach without a gated licence —
# and Common Voice is the route with GENDER and AGE on every row. Pinning
# >=3 was me choosing the version that cannot load the corpus I chose, and
# the cost was 19 shortlists filtered by nothing.
#
# v2 also decodes audio without torchcodec, so this removes the two-gigabyte
# PyTorch dependency as a side effect rather than as a workaround.
FETCH_PKGS = ["datasets>=2.19,<3", "huggingface_hub<1.0", "soundfile", "librosa"]
PKGS = CORE_PKGS + FETCH_PKGS


def venv_python():
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def ensure_venv(assume_yes, core_only=False):
    stamp = VENV / (".ledger-core" if core_only else ".ledger-ok")
    need = CORE_PKGS if core_only else PKGS
    probe_import = "import numpy" if core_only else "import numpy, datasets, soundfile"
    py = venv_python()
    # THE STAMP RECORDS WHAT WAS INSTALLED, not merely that something was.
    # A stamp saying "ok" cannot notice that the required versions changed, so
    # a pin added here would never reach a machine that had already built the
    # environment — the fix would ship and nothing would happen.
    spec = "\n".join(need)
    if stamp.exists() and py.exists() and stamp.read_text(encoding="utf-8").strip() != spec.strip():
        print("  dependencies changed since this environment was built; rebuilding")
        shutil.rmtree(VENV, ignore_errors=True)
        py = venv_python()
    if stamp.exists() and py.exists():
        # Re-probe every cached environment rather than trusting the stamp.
        # A stamp that outlives a broken install is how a fixed bug keeps
        # reproducing (learned the hard way on the TTS benchmark).
        probe = subprocess.run([str(py), "-c", probe_import], capture_output=True)
        if probe.returncode == 0:
            return py
        print("  cached environment no longer imports; rebuilding it")
        shutil.rmtree(VENV, ignore_errors=True)

    if not assume_yes:
        print(f"\nThis installs {', '.join(need)} into {VENV}")
        print("Nothing is installed system-wide, and deleting that folder undoes it.")
        if input("Continue? [Y/n] ").strip().lower() in ("n", "no"):
            sys.exit(1)

    print(f"  building {VENV.name} ...")
    if not py.exists():
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
        py = venv_python()
        subprocess.run([str(py), "-m", "pip", "install", "-q", "--upgrade", "pip"], check=True)
    subprocess.run([str(py), "-m", "pip", "install", "-q", *need], check=True)
    subprocess.run([str(py), "-c", probe_import], check=True)
    stamp.write_text(spec + "\n", encoding="utf-8")
    return py


def audio_quality(mono):
    """Score a mono clip 0..1 on things that make a reference unusable.

    A cloner inherits everything about its reference: hiss, clipping, room,
    and dead air. "Legit bad quality" was an accurate description of what a
    corpus of laptop microphones offers when nothing screens it, and no amount
    of listening should be spent on a clip that measurement can reject.

    Three cheap measures, all of which a human hears immediately:
      * CLIPPING - samples pinned at the rail. Distortion is unrecoverable.
      * DEAD AIR - the fraction that is near-silence. A ten-second reference
        that is half silence is a five-second reference.
      * LEVEL    - RMS. Too quiet means the noise floor comes up with it when
        the clip is normalised.
    """
    import numpy as np
    if mono is None or len(mono) == 0:
        return 0.0
    x = np.abs(np.asarray(mono, dtype=np.float32))
    peak = float(x.max()) or 1e-9
    clipped = float((x >= 0.98).mean())
    quiet = float((x < 0.02 * peak).mean())
    rms = float(np.sqrt(np.mean(np.square(np.asarray(mono, dtype=np.float32)))))

    score = 1.0
    score -= min(1.0, clipped * 40.0)     # 2.5% clipped is a write-off
    score -= max(0.0, (quiet - 0.35) * 2.0)
    if rms < 0.02:
        score -= 0.5
    elif rms < 0.05:
        score -= 0.2
    return max(0.0, min(1.0, score))


# The bar a candidate must clear to be offered at all. Set to reject the
# obviously broken rather than to grade the merely ordinary — taste is the
# listener's job, distortion is not.
QUALITY_FLOOR = 0.55


# ---------------------------------------------------------------------------
# fetching (runs INSIDE the venv, via --worker)
# ---------------------------------------------------------------------------

CV_DATASET = "fsicoli/common_voice_17_0"   # ungated mirror; same CC0 clips

# ACCENTS WE CAN USE. Common Voice English is majority non-native, and a
# late-analog city cannot be cast from a pool where most voices carry an
# accent from somewhere the game does not contain. Rows carry an `accents`
# field; when it is present and says something we cannot use, skip.
#
# Empty accent is ALLOWED rather than rejected — a great many rows have no
# accent recorded, and rejecting them would throw away most of the corpus.
ACCENTS_WANTED = ("united states", "england", "canadian", "australian",
                  "irish", "scottish", "new zealand", "american")
LIBRITTS_DATASET = "blabble-io/libritts_r"

# VCTK: 110 English speakers recorded in a treated room at Edinburgh, each
# labelled with gender, age and accent. Studio-clean and consistent, which is
# what "legit bad quality, strong accents" was asking for — and the setting is
# LATE-ANALOG, the eighties and nineties, so modern natural speech is correct
# rather than a compromise.
#
# Consent holds exactly as before: VCTK speakers were recruited and recorded
# for speech-technology research. That is the same standard that put Common
# Voice first, not a relaxation of it.
#
# Several ids, tried in order, because the Hub moves datasets between
# namespaces and this environment cannot reach it to check which one is live.
VCTK_DATASETS = ("CSTR-Edinburgh/vctk", "vctk", "sanchit-gandhi/vctk")

# VCTK accents worth casting from, matched loosely. Everything else is a real
# accent belonging to a place this game does not contain.
VCTK_ACCENTS = ("english", "american", "scottish", "irish", "canadian",
                "northernirish", "welsh", "australian")


# ACCENT, CANONICALISED. VCTK says "American", "Scottish", "NorthernIrish";
# Common Voice says "United States English", "England English". One table, in
# priority order, because "english" is a substring of "united states english"
# and checking it first would make every American speaker an Englishman.
ACCENT_ALIASES = (
    ("american",  ("american", "united states", "us english")),
    ("canadian",  ("canadian", "canada")),
    ("australian", ("australian", "australia")),
    ("scottish",  ("scottish", "scotland")),
    ("northernirish", ("northernirish", "northern irish", "northern ireland")),
    ("irish",     ("irish", "ireland")),
    ("welsh",     ("welsh", "wales")),
    ("english",   ("english", "england")),
)


def canon_accent(value):
    """The canonical name for whatever this corpus calls an accent."""
    v = (value or "").strip().lower()
    if not v:
        return ""
    for canon, aliases in ACCENT_ALIASES:
        if any(a in v for a in aliases):
            return canon
    return "other"


def accent_ok(row_value, spec_value):
    """A character with an accent gets that accent, and nothing else.

    THE POINT OF THE WHOLE FIELD: an unnamed accent used to mean "whatever the
    stream reached first", which put a Scottish voice on an American principal
    by luck rather than by choice. If the brief names one, it is required.
    """
    want = (spec_value or "").strip().lower()
    got = canon_accent(row_value)
    # "any" IS NOT THE SAME AS UNSET. Unset means "some accent I recognise";
    # `any` means the brief genuinely does not care, including the accents
    # this file has no name for. It exists for the crowd, where a mixed wash
    # is the correct answer rather than a compromise.
    if want == "any":
        return True
    if not want:
        return got in ("american", "english", "scottish", "irish",
                       "northernirish", "canadian", "welsh", "australian", "")
    if not got:
        return False        # unknown accent cannot satisfy a named one
    return got == want


def same_gender(row_value, spec_value):
    """Corpora disagree about how to spell this; the game should not care.

    Common Voice 17 says `male_masculine`, VCTK says `M`, LibriTTS says
    nothing at all. Normalising in one place beats three filters that each
    know one vocabulary — and a mismatch here does not fail loudly, it
    silently casts Rocco as a woman, which is exactly what happened.
    """
    def norm(v):
        v = (v or "").strip().lower()
        if not v:
            return ""
        if v.startswith("m"):
            return "male"
        if v.startswith("f") or v.startswith("w"):
            return "female"
        return v
    a, b = norm(row_value), norm(spec_value)
    if not a or not b:
        return None          # unknown — the caller decides
    return a == b


# Common Voice's own spelling, including its "fourties". The briefs are
# written in this vocabulary, so this is the list they are checked against
# rather than a second one somebody invented alongside it.
CV_AGE_BANDS = ("teens", "twenties", "thirties", "fourties",
                "fifties", "sixties", "seventies", "eighties", "nineties")


def age_band(value):
    """VCTK records a number; the briefs are written in Common Voice bands.

    THE OLD VERSION COULD NOT PRODUCE "thirties" OR "fifties". It had three
    branches — under 30, under 50, else — returning twenties, fourties and
    sixties, so a thirty-five-year-old came back "fourties" and a fifty-five-
    year-old came back "sixties". Two of the nine bands were unreachable, and
    they are two the cast asks for by name: Lena is thirties, Rocco fifties.
    Any brief naming one of them could only ever be satisfied by accident.

    A decade is a decade. `n // 10` is the whole rule.
    """
    raw = str(value).strip().lower()
    # Already a band — Common Voice hands these back as words, and passing
    # one through int() was how every Common Voice age silently became "".
    if raw in CV_AGE_BANDS:
        return raw
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return ""
    if n < 10:
        return ""
    idx = min(n // 10, 9)
    return CV_AGE_BANDS[idx - 1]


def age_gap(value, wanted):
    """How far a speaker's decade is from the one the brief asked for.

    AGE IS A PREFERENCE, NOT A FILTER, AND THIS IS THE FUNCTION THAT DEMOTES
    IT. Fifteen CI runs produced three fillable characters out of nineteen,
    and the strided diagnose finally said why: VCTK's speakers are 22, 23, 38
    — it was recorded from university-age volunteers and its whole range is
    roughly 18 to 38. The cast asks for fourties, fifties and sixties for
    almost every principal. Rocco is 50s. Ellis is 40s. Reese is fifty-ish.
    Against this corpus those briefs could never be satisfied by anybody, and
    27.7% of all rejections were this one field.

    That is not a shortage in the corpus. It is the wrong question being
    asked of it. THESE ARE REFERENCE CLIPS FOR CASTING A TIMBRE, not the
    shipped performance — and a speaker's chronological age does not decide
    whether the voice suits the part. A 38-year-old with a low, worn, dry
    voice is a better Rocco than a 55-year-old with a light one, and the only
    instrument that can tell the difference is somebody listening. Filtering
    on the metadata throws the candidate away before the ears ever get a vote.

    So age never rejects anybody now. It orders them: distance in decades
    from the nearest requested band, smallest first, so the closest-aged
    speakers are candidate 01 and the rest are still on the page underneath.
    An unrecorded age scores 1 — behind an exact match, ahead of a speaker
    known to be three decades out.
    """
    if not wanted:
        return 0
    band = age_band(value)
    if not band:
        return 1
    if band in wanted:
        return 0
    here = CV_AGE_BANDS.index(band)
    return min(abs(here - CV_AGE_BANDS.index(w))
               for w in wanted if w in CV_AGE_BANDS) or 1


def inventory(out_path):
    """Enumerate every speaker in the corpus, reading no audio at all.

    THE INSTRUMENT THAT WAS MISSING ALL DAY. Every fact about VCTK — who is in
    it, which accents, who is still unclaimed, where they sit in the stream —
    has been inferred from the side effects of a forty-minute fetch, because
    HuggingFace is blocked from the dev box and a CI run was the only way to
    ask. That is why every answer arrived as a surprise and every estimate was
    wrong: experiments were being run where a lookup was wanted.

    This reads ONLY `speaker_id, gender, accent, age`. The audio column holds
    the entire ten gigabytes and is never touched — parquet stores columns
    separately, so projecting four small ones reads almost nothing.

    Emits, per speaker: their attributes and the first row offset they appear
    at. After this runs once, "can crowd_f1 be filled, by whom, and from which
    offset" is a question answered locally in a second.
    """
    import json as _json
    wanted_cols = ["speaker_id", "gender", "accent", "age"]
    rows_seen = 0
    speakers = {}
    how = None

    # PARQUET WITH COLUMN PROJECTION FIRST. This is the cheap path and the
    # reason the whole idea works.
    try:
        import pyarrow.dataset as _pads
        import huggingface_hub as _hub
        files = [f for f in _hub.list_repo_files(VCTK_DATASETS[0], repo_type="dataset",
                                                 revision="refs/convert/parquet")
                 if f.endswith(".parquet")]
        if not files:
            raise RuntimeError("no parquet files listed")
        urls = [_hub.hf_hub_url(VCTK_DATASETS[0], f, repo_type="dataset",
                                revision="refs/convert/parquet") for f in files]
        import fsspec
        fs = fsspec.filesystem("http")
        ds = _pads.dataset([fs.open(u) for u in sorted(urls)], format="parquet")
        for batch in ds.to_batches(columns=wanted_cols):
            cols = {c: batch.column(c).to_pylist() for c in wanted_cols}
            for i in range(batch.num_rows):
                sid = str(cols["speaker_id"][i])
                if sid not in speakers:
                    speakers[sid] = dict(speaker=sid,
                                         gender=str(cols["gender"][i] or ""),
                                         accent=str(cols["accent"][i] or ""),
                                         age=str(cols["age"][i] or ""),
                                         first_row=rows_seen, rows=0)
                speakers[sid]["rows"] += 1
                rows_seen += 1
        how = "parquet column projection"
    except Exception as e:                        # noqa: BLE001
        print(f"  parquet projection unavailable ({type(e).__name__}: "
              f"{str(e).splitlines()[0][:120]})")
        # FALLBACK: stream, but drop the audio column before iterating so the
        # decoder is never invoked. Slower than parquet, far cheaper than a
        # fetch, and it SAYS it took this path rather than pretending.
        routes = _routes_for("vctk", CAST)
        ds = None
        for name, opener in routes:
            try:
                ds, _key, _audio, _m = opener()
                break
            except Exception as e2:               # noqa: BLE001
                print(f"    {name} failed: {type(e2).__name__}")
        if ds is None:
            raise RuntimeError("no route to the corpus at all")
        try:
            ds = ds.remove_columns(["audio"])
        except Exception:                          # noqa: BLE001
            pass
        for row in ds:
            sid = str(row.get("speaker_id") or "")
            if sid:
                if sid not in speakers:
                    speakers[sid] = dict(speaker=sid,
                                         gender=str(row.get("gender") or ""),
                                         accent=str(row.get("accent") or ""),
                                         age=str(row.get("age") or ""),
                                         first_row=rows_seen, rows=0)
                speakers[sid]["rows"] += 1
            rows_seen += 1
        how = "streaming without the audio column"

    table = sorted(speakers.values(), key=lambda s: s["first_row"])
    out_path.write_text(_json.dumps(
        dict(corpus=VCTK_DATASETS[0], read_by=how, rows=rows_seen,
             speakers=table), indent=1) + "\n", encoding="utf-8")

    print(f"  read by: {how}")
    print(f"  {rows_seen} rows, {len(table)} distinct speakers")
    from collections import Counter
    print(f"  accents: {dict(Counter(s['accent'] for s in table).most_common())}")
    print(f"  genders: {dict(Counter(s['gender'] for s in table).most_common())}")
    print(f"  last speaker first appears at row {table[-1]['first_row']}")
    print(f"  written: {out_path}")
    return 0


def _routes_for(source, cast=None):
    """The corpus routes, in order, as (name, opener) pairs.

    MODULE LEVEL SO TWO CALLERS SHARE ONE COPY. These openers used to be
    nested inside `fetch`, which meant `diagnose` could only have reached
    them by duplicating them — and a diagnostic that is a COPY of the thing
    it diagnoses tells you about the copy. It has to open the corpus the same
    way the real run does or it is theatre.
    """
    # THE IMPORT LIVES IN THE OPENERS, not here. Listing the routes is not
    # the same act as opening one, and a factory that needs the corpus
    # library merely to name its routes cannot have its shape checked
    # without installing two hundred megabytes of it. That is exactly why
    # `_routes_for` returning None survived a green selftest.
    def open_common_voice(revision=None):
        from datasets import load_dataset
        kw = dict(split="train", streaming=True)
        if revision:
            kw["revision"] = revision
        # `datasets` 2.16 and later refuse to execute a dataset loading script
        # unless told to, and the reachable Common Voice mirror is a script.
        # Without this the route raises, we fall through to a corpus with no
        # gender metadata, and nineteen briefs get filtered by nothing.
        try:
            ds = load_dataset(CV_DATASET, "en", trust_remote_code=True, **kw)
        except TypeError:
            # Older or newer versions that do not know the argument.
            ds = load_dataset(CV_DATASET, "en", **kw)
        def matches(row, spec):
            g = (row.get("gender") or "").strip()
            # Through the shared normaliser, not a raw string compare: the
            # vocabularies differ between corpora and a mismatch here is
            # silent.
            if spec.get("gender") and same_gender(g, spec["gender"]) is False:
                return False
            # Age orders, it does not reject — see `age_gap`.
            if not accent_ok(row.get("accents") or row.get("accent"),
                             spec.get("accent")):
                return False
            # A row with no metadata at all is not a match — it is an
            # unknown, and filling a shortlist with unknowns is the same as
            # not filtering.
            return bool(g)
        return ds, "client_id", "audio", matches

    def open_vctk():
        from datasets import load_dataset
        last = None
        # EACH MIRROR TWICE: the ordinary way, then via the parquet export.
        #
        # `BadZipFile: File is not a zip file` is what both full VCTK mirrors
        # answer with — a broken archive upstream, nothing to do with us. The
        # only id that opens is a PARTIAL copy, which is why aligning the
        # accent brief to the corpus changed the yield from five characters
        # to four instead of unlocking the cast: the pool was never big
        # enough for any brief to matter.
        #
        # The Hub auto-generates a parquet export at `refs/convert/parquet`
        # for every dataset, and it is built from the data rather than from
        # the archive — so it sidesteps the corrupt zip entirely. This
        # fetcher already used that trick for Common Voice and never tried it
        # on VCTK, which is the whole of this change.
        attempts = [(name, rev) for name in VCTK_DATASETS
                    for rev in (None, "refs/convert/parquet")]
        for name, revision in attempts:
            try:
                # SAME PERMISSION THE COMMON VOICE OPENER NEEDED. All three
                # VCTK mirrors are script-backed, so without this `datasets`
                # asks "Do you wish to run the custom code? [y/N]" — and a CI
                # runner cannot answer a prompt, so every id declined itself.
                kw = dict(split="train", streaming=True)
                if revision:
                    kw["revision"] = revision
                try:
                    ds = load_dataset(name, trust_remote_code=True, **kw)
                except TypeError:
                    ds = load_dataset(name, **kw)
                # AND PULL A ROW BEFORE BELIEVING THIS MIRROR.
                #
                # `load_dataset(streaming=True)` is LAZY: it returns happily
                # without touching the network, so the first id in the list
                # always "succeeded", `break` fired, and the other two mirrors
                # were NEVER TRIED. The failure surfaced later, at the route
                # level, where it read as "VCTK is unavailable" — so the
                # corpus Jafar actually chose has never once been used, and
                # every run silently fell through to Common Voice.
                #
                # This is the same lesson already written twenty lines below
                # for the route list, applied one level down. Learning it in
                # one place and not the other is how it stayed hidden.
                next(iter(ds))
                print(f"    vctk mirror {name}"
                      f"{'@parquet' if revision else ''} opened")
                break
            except Exception as e:              # noqa: BLE001 - try the next id
                print(f"    vctk mirror {name}"
                      f"{'@parquet' if revision else ''} failed: "
                      f"{type(e).__name__}: {str(e).strip().splitlines()[0][:120]}")
                last = e
        else:
            raise last or RuntimeError("no VCTK id resolved")

        def matches(row, spec):
            g = same_gender(row.get("gender") or row.get("sex"),
                            spec.get("gender"))
            if g is False:
                return False
            if g is None:
                return False        # no gender on the row is not a match
            if not accent_ok(row.get("accent") or row.get("accents"),
                             spec.get("accent")):
                return False
            # NO AGE TEST HERE — see `age_gap`. VCTK tops out around 38 and
            # the cast is mostly middle-aged, so an age filter empties the
            # corpus for sixteen of nineteen characters. It orders the
            # shortlist instead of gating entry to it.
            return True

        return ds, "speaker_id", "audio", matches

    def open_libritts():
        from datasets import load_dataset
        ds = load_dataset(LIBRITTS_DATASET, "clean", split="train.clean.100",
                          streaming=True)
        def matches(row, spec):
            # LibriTTS carries no age or gender in the row, so every brief
            # sees every speaker and the filtering is your ears. Said out
            # loud rather than silently pretending the filter worked.
            return True
        return ds, "speaker_id", "audio", matches

    if source == "libritts":
        return [("libritts", open_libritts)]
    # A NAMED CORPUS IS BINDING. Jafar chose VCTK because Common Voice
    # sounded bad; every run after that decision silently used Common Voice
    # anyway, because VCTK was merely FIRST in a fallback list rather than
    # required. A night of listening candidates was generated from the corpus
    # he had already rejected, and nothing in the output said so.
    #
    # The file already hard-stops on a LibriTTS fallback for precisely this
    # reason. That rule was written for one corpus and never generalised.
    if source == "vctk":
        return [("vctk", open_vctk)]
    return [
        ("vctk", open_vctk),
        ("commonvoice", lambda: open_common_voice()),
        ("commonvoice-parquet",
         lambda: open_common_voice(revision="refs/convert/parquet")),
        ("libritts", open_libritts),
    ]


def diagnose(source, cast, rows=60):
    """Open every route, read some rows, and say WHY each brief rejects them.

    WHY THIS EXISTS, and why it prints its answer LAST.

    Run 7 streamed for forty-five minutes, exited zero, and banked nothing.
    The one line naming the reason sat in a log the GitHub API returns only
    the tail of, and `datasets` fills that tail with a thousand lines of
    "Reading metadata..." progress. Two attempts to route the answer around
    it — an artifact, then a step summary — both failed to come back through
    any API I can read.

    So the answer goes at the very END, in a compact block, because the tail
    is the part I can actually see. Everything above it is allowed to be
    noise.

    And it reports a REJECTION BREAKDOWN rather than a pass rate. "4 of 40
    rows accepted" says the filter is strict; it does not say whether the
    strictness is gender, age, accent, or a corpus that fills none of them.
    Those have completely different fixes and one of them is not a bug.
    """
    import os
    # The progress bars are what evicted the answer from the log last time.
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("HF_DATASETS_DISABLE_PROGRESS_BARS", "1")
    try:
        import datasets as _d
        _d.disable_progress_bars()
    except Exception:                            # noqa: BLE001
        pass

    report = []
    opened_name = None
    detail = {}

    for name, opener in _routes_for(source, cast):
        try:
            ds, key_speaker, key_audio, matches = opener()
            first = next(iter(ds))
        except Exception as e:                   # noqa: BLE001
            report.append(f"{name}: DID NOT OPEN — {type(e).__name__}: "
                          f"{str(e).strip().splitlines()[0][:120]}")
            continue
        report.append(f"{name}: opened")
        if opened_name is not None:
            continue                             # keep probing, but only measure the first
        opened_name = name

        # STRIDE ACROSS SPEAKERS, do not read the first N rows.
        #
        # VCTK is ordered BY SPEAKER, roughly four hundred utterances each.
        # Reading sixty consecutive rows read ONE PERSON — a 23-year-old
        # English woman — and reported "18 of 19 characters match nothing",
        # which I nearly read as a partial corpus. It was a sample that could
        # not see past the first speaker in a corpus sorted by speaker.
        #
        # Skipping ahead between reads costs nothing on a streaming dataset
        # and is the difference between measuring a corpus and measuring
        # whoever happens to be first in it.
        it = iter(ds)
        seen = 0
        vocab = {"gender": set(), "age": set(), "accent": set()}
        # WHY each brief said no, counted per clause.
        why = {"gender": 0, "age": 0, "accent": 0, "no-gender-on-row": 0, "accepted": 0}
        # HOW BIG IS THE POOL — the number that would have ended this two
        # days ago. Nineteen briefs cannot be filled from a corpus offering
        # eight voices, whatever their accents are, and rewriting the briefs
        # cannot change it. VCTK proper has 110 speakers.
        speakers = set()
        per_character = {c["id"]: 0 for c in cast}
        sampled = [first]
        # STRIDE MUST SPAN THE WHOLE CORPUS, NOT THE FRONT OF IT. The first
        # strided run used 97, which over 60 samples walks 5,820 rows of a
        # ~44,000-row corpus — the first 13%. VCTK is ordered by speaker, so
        # that is the first dozen or so speakers and nobody else, and the
        # report came back "accent: ['English']" as though the corpus had no
        # Scots in it at all. It has 34. The sample was measuring where it
        # started, not what was there.
        #
        # VCTK gives each speaker ~400 utterances, so a stride near 400 lands
        # roughly one fresh speaker per sample and 60 samples reach ~60 of the
        # 110. 401 is prime, which keeps it from locking onto any speaker's
        # block boundary.
        STRIDE = 401
        try:
            skip = 0
            for r in it:
                skip += 1
                if skip % STRIDE:
                    continue
                sampled.append(r)
                if len(sampled) >= rows:
                    break
        except Exception:                        # noqa: BLE001 - short corpus
            pass
        for row in sampled:
            seen += 1
            g = (row.get("gender") or row.get("sex") or "")
            a = (row.get("age") or "")
            ac = (row.get("accent") or row.get("accents") or "")
            vocab["gender"].add(str(g)[:24]); vocab["age"].add(str(a)[:24])
            vocab["accent"].add(str(ac)[:24])
            sp = row.get(key_speaker)
            if sp:
                speakers.add(str(sp))
            for c in cast:
                if matches(row, c):
                    per_character[c["id"]] += 1
                    why["accepted"] += 1
                    continue
                # Re-derive the clause that failed. Same helpers the filter
                # uses, so this cannot disagree with it about the verdict.
                if not str(g).strip():
                    why["no-gender-on-row"] += 1
                elif c.get("gender") and same_gender(g, c["gender"]) is False:
                    why["gender"] += 1
                elif not accent_ok(ac, c.get("accent")):
                    why["accent"] += 1
                else:
                    # Cannot happen any more: age lost its veto (`age_gap`).
                    # Kept as a tripwire — if this ever counts above zero,
                    # a filter has grown back.
                    why["age"] += 1
        detail = dict(seen=seen, vocab=vocab, why=why, per_character=per_character,
                      columns=sorted(first.keys()), key_speaker=key_speaker,
                      speakers=speakers)

    # ---- THE ANSWER, LAST, COMPACT ----
    print("\n\n================ DIAGNOSE ================")
    for line in report:
        print("  " + line)
    if not detail:
        print("  NO ROUTE OPENED — nothing else can be said")
        print("==========================================")
        return 1
    print(f"  measuring: {opened_name}, {detail['seen']} rows")
    print(f"  DISTINCT SPEAKERS in those rows: {len(detail['speakers'])}"
          f"   (VCTK proper has 110)")
    print(f"  columns: {','.join(detail['columns'])[:160]}")
    for field in ("gender", "age", "accent"):
        vals = sorted(v for v in detail["vocab"][field] if v)
        print(f"  {field:7}: {vals[:6] if vals else 'EMPTY ON EVERY ROW'}")
    tries = detail["seen"] * len(cast)
    w = detail["why"]
    print(f"  brief x row decisions: {tries}")
    for k in ("accepted", "gender", "accent", "age", "no-gender-on-row"):
        print(f"    {k:18} {w[k]:6}  ({100.0 * w[k] / max(1, tries):5.1f}%)")
    dead = [cid for cid, n in detail["per_character"].items() if n == 0]
    print(f"  characters matching NOTHING: {len(dead)}/{len(cast)}")
    if dead:
        print("    " + ", ".join(dead))
    live = {cid: n for cid, n in detail["per_character"].items() if n}
    print(f"  characters with matches: {live if live else 'none'}")
    print("==========================================")
    return 0


def fetch(source, cast, candidates, out_dir, budget_minutes=0, skip_rows=0):
    """Stream a corpus and bank enough audio per speaker to make candidates.

    Streaming rather than downloading: Common Voice English is tens of
    gigabytes and we need about four minutes of it. A script that makes you
    wait for an 80GB tarball is a script you do not run.
    """
    import io as _io
    import numpy as np
    import soundfile as _sf
    from datasets import load_dataset

    wanted = {}
    for c in cast:
        # `used` is the speakers this character already has a finished
        # candidate from. Without it a shortlist can be one voice N times.
        wanted[c["id"]] = dict(spec=c, banked={}, done=[], used=set())

    # THREE ROUTES, TRIED IN ORDER, because the first one broke on contact
    # and none of them can be tested from where this was written.
    #
    # `datasets` v3 removed support for dataset loading SCRIPTS, and the
    # ungated Common Voice mirror is script-based — so the very first real run
    # died on "Dataset scripts are no longer supported, but found
    # common_voice_17_0.py" and told the user to re-run with a flag. Telling
    # somebody to retry by hand is not a fallback, it is a to-do item.
    #
    #   1. Common Voice the ordinary way. Works if `datasets` is v2, and is
    #      the route with age and gender metadata, so the shortlists are
    #      filtered rather than merely long.
    #   2. Common Voice via `refs/convert/parquet` — the parquet export the
    #      Hub generates for every dataset, which has no script and therefore
    #      no v3 problem.
    #   3. LibriTTS-R, which is parquet-native and always loadable.
    #
    # Whichever wins is NAMED in the output, because a shortlist filtered by
    # metadata and a shortlist filtered by nothing are different things and
    # the casting notes need to say which one you were listening to.

    routes = _routes_for(source, cast)

    ds = key_speaker = key_audio = matches = None
    used = None
    for name, opener in routes:
        try:
            ds, key_speaker, key_audio, matches = opener()
            # AND PULL ONE ROW BEFORE BELIEVING IT. `load_dataset(streaming=True)`
            # is lazy: it returns happily and fails on first access. The run
            # before this printed "source: vctk" and then died fetching a row,
            # so the log named a corpus that had never produced anything —
            # a success message for work that had not happened, which is the
            # same fault this project has now fixed in four other places.
            next(iter(ds))
            used = name
            print(f"  source: {name}")
            break
        except Exception as e:                  # noqa: BLE001 - report and try next
            line = str(e).strip().splitlines()[0][:160]
            print(f"  {name} unavailable: {type(e).__name__}: {line}")
    if ds is None:
        raise RuntimeError("no corpus could be opened; see the reasons above")

    # DO NOT LET `datasets` DECODE THE AUDIO. Since v3 its Audio feature
    # decodes through `torchcodec`, so a row access raises
    #     ImportError: To support decoding audio data, please install 'torchcodec'
    # and torchcodec means PyTorch: well over two gigabytes of wheels to turn
    # some WAV bytes into a float array. `soundfile` is already a dependency
    # here and does exactly that.
    #
    # `decode=False` hands back the raw bytes instead, which we read ourselves
    # below. Wrapped because the cast is unavailable on some dataset shapes,
    # and a failure here should fall through to the decoded path rather than
    # end the run.
    try:
        from datasets import Audio
        ds = ds.cast_column(key_audio, Audio(decode=False))
        print("  audio: decoding with soundfile, not torchcodec")
    except Exception as e:                      # noqa: BLE001 - report, continue
        print(f"  audio: could not disable library decoding ({type(e).__name__}); "
              f"using whatever the library returns")
    # AN UNFILTERED SHORTLIST IS NOT A SHORTLIST, and printing a NOTE about
    # it was not enough. The run before this one fell through to LibriTTS,
    # said so in one line among many, and produced nineteen gender-blind
    # lists: Rocco a woman, Mara Ellis a man, Sam a woman. Fifteen minutes of
    # listening spent on candidates that could not have been right.
    #
    # So this now STOPS. A corpus with no gender is fine for a deliberate
    # `--source libritts`, where the operator has chosen it; it is not fine as
    # a silent fallback from the corpus that does have gender.
    # THE SAME RULE, GENERALISED. Falling back from the corpus that was
    # chosen to one that was rejected is not a fallback, it is a substitution
    # nobody agreed to.
    if source and source not in ("", "auto") and used != source:
        raise RuntimeError(
            f"asked for {source!r} and got {used!r}. The reasons {source} did "
            f"not open are printed above.\n"
            f"  Nothing is written, because a shortlist from the wrong corpus "
            f"is worse than no shortlist: it costs a listening pass to find "
            f"out.\n"
            f"  To accept {used!r} deliberately:  --source {used}")
    if used == "libritts" and source != "libritts":
        raise RuntimeError(
            "fell back to LibriTTS, which carries no gender or age, so every "
            "brief would be filtered by nothing -- which is how Rocco came out "
            "a woman last time.\n"
            "  The Common Voice failures are printed above; send them to me.\n"
            "  To proceed anyway with ears-only filtering:\n"
            "      python ledger_voice_fetch.py --source libritts")

    # START PAST THE GROUND ALREADY WALKED.
    #
    # A targeted run for three crowd voices scanned fifty thousand rows in its
    # full thirty-eight minutes and banked nothing at all. Not a bug and not a
    # corpus limit: VCTK is ordered by speaker, the previous run had claimed
    # every speaker in the first fifty thousand rows, and the budget stops at
    # the same place every time. The unclaimed voices live PAST where the
    # clock runs out, so re-running reads the same exhausted stretch again and
    # comes back empty again, for as long as anybody cares to repeat it.
    if skip_rows > 0:
        print(f"  skipping the first {skip_rows} rows — already picked over")
        ds = ds.skip(skip_rows)

    claimed = {}          # speaker -> the character who owns them

    # A TARGETED RUN INHERITS WHO IS ALREADY SPOKEN FOR.
    #
    # `claimed` is built fresh each run, so cross-character exclusivity only
    # ever held WITHIN one run. Fetching three missing crowd voices on their
    # own started from an empty table and handed them the same speakers the
    # first characters got last time: crowd_f1 came back as p230/p228/p229/
    # p225 — Lena's exact shortlist, including p228, the voice that had just
    # been cast AS Lena. A crowd voice you recognise stops being a crowd, and
    # this one was the bookkeeper.
    #
    # Everybody on the existing page who is not being re-fetched keeps their
    # speakers. The rule was always "one speaker, one character"; it just had
    # no memory across runs.
    _here = {c["id"] for c in cast}
    for _cid, _rows in _rows_from_existing_page(out_dir).items():
        if _cid in _here:
            continue                      # being replaced by this run
        for _r in _rows:
            if _r.get("speaker"):
                claimed[_r["speaker"]] = _cid
    if claimed:
        print(f"  {len(claimed)} speaker(s) already spoken for by "
              f"{len({v for v in claimed.values()})} character(s) — not offered again")
    seen_rows = 0
    # A WALL-CLOCK BUDGET, because the row count was never the thing that ran
    # out. Three CI runs were killed by the job cap and every one of them
    # produced EXACTLY NOTHING — the clips are held in memory and written in
    # one go at the end of this function, so being killed a minute early and
    # being killed at the start are the same outcome. Forty-five thousand
    # rows of "we nearly had it" is worth less than eleven clips.
    #
    # The script now decides to stop rather than waiting to be killed, and
    # what it has banked is written out. `deadline` of 0 means no budget.
    started = _time.monotonic()
    stopped_early = None
    for row in ds:
        seen_rows += 1
        if seen_rows % 2000 == 0:
            left = sum(1 for w in wanted.values() if len(w["done"]) < candidates)
            spent = (_time.monotonic() - started) / 60.0
            print(f"    {seen_rows} rows scanned, {left} characters still short, "
                  f"{spent:.1f} min spent")
        if all(len(w["done"]) >= candidates for w in wanted.values()):
            break
        if budget_minutes and (_time.monotonic() - started) / 60.0 >= budget_minutes:
            stopped_early = f"time: {budget_minutes} minute budget spent"
            print(f"    stopping: {stopped_early} — writing what we have")
            break
        if seen_rows > 400000:
            stopped_early = "rows: scanned 400k"
            print("    stopping: scanned 400k rows, taking what we have")
            break

        # DECIDE BEFORE DECODING. The loop used to read and resample the audio
        # of EVERY row and only then ask whether anybody wanted that speaker —
        # so a corpus of forty-four thousand utterances was fully decoded to
        # fill a hundred-odd slots, and the run before this one was still going
        # at fifty minutes against a sixty-minute cap.
        #
        # Metadata is already in the row. Ask first, decode second.
        speaker = row.get(key_speaker) or ""
        if not speaker:
            continue
        owner = claimed.get(speaker)
        if owner is not None:
            # Known speaker: only their owner can still want them.
            w = wanted.get(owner)
            if w is None or len(w["done"]) >= candidates:
                continue
        else:
            # New speaker: does any unfilled character's brief accept them?
            if not any(len(w["done"]) < candidates and matches(row, w["spec"])
                       for w in wanted.values()):
                continue

        audio = row.get(key_audio)
        if not audio:
            continue
        arr = audio.get("array")
        rate = audio.get("sampling_rate")
        if arr is None:
            # The undecoded shape: raw file bytes, which soundfile reads
            # directly. This is the normal path now that the cast above
            # switches decoding off.
            raw = audio.get("bytes")
            if not raw:
                continue
            try:
                arr, rate = _sf.read(_io.BytesIO(raw), dtype="float32",
                                     always_2d=False)
            except Exception:                   # noqa: BLE001 - one bad row
                continue
            arr = np.asarray(arr, dtype=np.float32)
            if arr.ndim == 2:
                # Average the channels rather than reshaping, which would
                # interleave them and produce a clip at double speed.
                arr = arr.mean(axis=1)
        if arr is None or not rate:
            continue
        mono = resample(np.asarray(arr, dtype=np.float32).reshape(-1), rate)

        # ONE SPEAKER, ONE CHARACTER. Without this every character banks the
        # same speaker from the same row — and on a corpus with no metadata,
        # where `matches` is true for everyone, that means all nineteen
        # shortlists come out nearly identical. Which is exactly what
        # happened: "a lot of them have the same voice".
        #
        # The first unfilled character to want a speaker claims them, and no
        # one else may bank them afterwards.
        #
        # AND ONE CANDIDATE PER SPEAKER, WHICH THE RULE ABOVE DOES NOT GIVE
        # YOU. Jafar listened to the delivered page and said the four Lena
        # candidates were plainly the same person. They were. `claimed` stops
        # a speaker being shared BETWEEN characters and does nothing about a
        # character taking the same speaker again: once Lena claimed p225,
        # every later p225 row still matched her, she was still under quota,
        # so she banked another candidate from the same voice. VCTK stores
        # ~400 consecutive utterances per speaker, so she filled all six slots
        # out of one speaker's block before the stream reached anybody else.
        #
        # The arithmetic was in the log the whole time: 20,000 rows is about
        # fifty speakers, and six distinct voices for nineteen characters
        # needs a hundred and fourteen. It was never possible, and the page
        # did not show the speaker id, so nothing said so.
        #
        # A shortlist of one voice six times is not a shortlist.
        for cid, w in wanted.items():
            if len(w["done"]) >= candidates:
                continue
            if owner is not None and owner != cid:
                continue
            if speaker in w["used"]:
                continue          # already gave this character a candidate
            if speaker in w["banked"] or matches(row, w["spec"]):
                if owner is None:
                    claimed[speaker] = cid
                    owner = cid
                bank = w["banked"].setdefault(speaker, [])
                if len(bank) > 12:
                    continue
                bank.append(mono)
                joined = assemble(bank)
                if joined is not None:
                    clip_ = normalise(joined)
                    q = audio_quality(clip_)
                    if q < QUALITY_FLOOR:
                        # Measured as unusable — clipped, mostly silence, or
                        # too quiet to normalise without lifting the hiss with
                        # it. Dropped before anybody spends a minute on it, and
                        # the speaker is released so somebody else can have
                        # them if they are the only one left.
                        w["rejected"] = w.get("rejected", 0) + 1
                        del w["banked"][speaker]
                        claimed.pop(speaker, None)
                        break
                    # AGE AND ACCENT TRAVEL WITH THE CLIP. Age stopped being
                    # a filter, which means the listener is now the one
                    # weighing it — and they cannot weigh what the page does
                    # not show them. "Does this 24-year-old read as fifty?"
                    # is a fair question and an answerable one, but only if
                    # the number is on screen next to the play button.
                    w["used"].add(speaker)
                    w["done"].append((speaker, clip_, q,
                                      age_gap(row.get("age"), w["spec"].get("age")),
                                      str(row.get("age") or "?")[:12],
                                      str(row.get("accent")
                                          or row.get("accents") or "?")[:20]))
                    del w["banked"][speaker]
                break   # one character per row; sharing a voice defeats casting

    made = {}
    for cid, w in wanted.items():
        files = []
        # CLOSEST IN AGE FIRST, THEN CLEANEST. The listener's time is the
        # scarce thing, so the ordering carries both things measurement knows:
        # how near the speaker's decade is to the brief, and how clean the
        # recording measured. Age lost its veto (see `age_gap`) but it keeps
        # its vote, and it votes here.
        ranked = sorted(w["done"], key=lambda d: (d[3], -d[2]))
        for i, (speaker, samples, _q, gap, age, acc) in enumerate(ranked[:candidates], 1):
            p = out_dir / cid / f"candidate-{i:02d}.wav"
            write_wav(p, samples)
            files.append(dict(n=i, file=f"{cid}/candidate-{i:02d}.wav",
                              speaker=str(speaker)[:12], age=age, accent=acc,
                              onbrief=(gap == 0),
                              seconds=round(len(samples) / float(SAMPLE_RATE), 1)))
        made[cid] = files

    # DISTINCT VOICES, COUNTED AND SAID OUT LOUD. The run that delivered six
    # candidates per character delivered one voice six times, reported "114
    # candidate(s) for 19 of 19 characters", and was believed. A count of
    # clips is not a count of choices, so both are printed and they must
    # agree — if they ever diverge again the log says so before anybody
    # spends an evening listening.
    dupes = []
    for cid, files in made.items():
        ids = [f.get("speaker") for f in files if f.get("speaker")]
        if ids and len(set(ids)) < len(ids):
            dupes.append(f"{cid}({len(ids)} clips, {len(set(ids))} voices)")
    voices = sum(len({f.get("speaker") for f in files if f.get("speaker")})
                 for files in made.values())
    print(f"  {sum(len(f) for f in made.values())} clip(s) from {voices} distinct voice(s)")
    if dupes:
        print("  SAME VOICE TWICE IN ONE SHORTLIST — that is not a shortlist: "
              + ", ".join(dupes[:8]))

    # AND SAY WHAT IS MISSING. A truncated run that reports the same way as a
    # complete one is the thing that makes a half-empty listening page look
    # like a casting problem rather than a budget one.
    if stopped_early:
        short = [cid for cid, f in made.items() if len(f) < candidates]
        print(f"  TRUNCATED ({stopped_early}). "
              f"{sum(len(f) for f in made.values())} clips written; "
              f"{len(short)} characters short of {candidates}: "
              + (", ".join(short[:12]) if short else "none"))
    # THE CORPUS THAT ANSWERED, not the one that was asked for. `build_page`
    # was handed `args.source` — the REQUEST — and printed it as though it
    # were the result. So the page said "commonvoice" for a run whose log
    # said `source: vctk`, and the two disagreed in the one field the
    # listening pass most needs to trust.
    #
    # It cost real time: I read the page label, told Jafar his clips were
    # from the corpus he had rejected, and nearly deleted them. The comment
    # forty lines up already says "whichever wins is NAMED in the output,
    # because the casting notes need to say which one you were listening to."
    # It was named in the log and not in the page.
    return made, used


# ---------------------------------------------------------------------------
# the listening page
# ---------------------------------------------------------------------------

def _rows_from_existing_page(out_dir):
    """The candidate rows already on the committed page, per character.

    SO A TARGETED RUN ADDS RATHER THAN REPLACES. `--who crowd_f1` filters the
    cast down to one character, and `build_page` then rebuilt the whole page
    from that one — silently dropping the other eighteen, including sixteen
    that had clips sitting right there on disk. Fetching three missing voices
    would have deleted the page for everybody else.

    Read back rather than recomputed: the rows carry their own durations and
    speaker ids, and nothing here needs to decode an mp3 to reuse them.
    """
    import re
    page = out_dir / "listen.html"
    if not page.exists():
        return {}
    html = page.read_text(encoding="utf-8")
    out = {}
    for cid, body in re.findall(r'<section id="([a-z0-9_]+)">(.*?)</section>',
                                html, re.S):
        rows = []
        for n, (src, meta) in enumerate(
                re.findall(r'<audio controls preload=none src="([^"]+)"></audio>'
                           r'\s*<span class=meta>([^<]*)', body), 1):
            bits = [b.strip() for b in meta.split("&middot;")]
            secs = bits[0].rstrip("s") if bits else "0"
            rows.append(dict(
                n=n, file=src,
                seconds=float(secs) if secs.replace(".", "", 1).isdigit() else 0.0,
                speaker=bits[1] if len(bits) > 1 else "",
                age=bits[2].replace("age ", "") if len(bits) > 2 else "",
                accent=bits[3] if len(bits) > 3 else ""))
        if rows:
            out[cid] = rows
    return out


def build_page(cast, made, out_dir, source, keep_existing=False):
    """The listening page — and it is a MOBILE page, because that is where the
    listening actually happens.

    TWO THINGS WERE WRONG WITH THE OLD ONE AND BOTH WERE INVISIBLE FROM HERE.

    It had no viewport meta tag, so a phone rendered it at desktop width and
    every control came out a third of the size of a fingertip. And it had no
    picking UI at all — it printed "write `lena 3` in picks.txt", which is an
    instruction you cannot follow on a phone. Jafar reported clicking "copy
    picks" and nothing happening; there was no such button on this page to
    click, and the one he had was from a throwaway I never folded back in.

    So: radio buttons big enough to hit, picks kept in localStorage so a
    reload on a train does not lose an hour of listening, and a copy control
    that CANNOT silently fail — `navigator.clipboard` needs a secure context
    and quietly rejects without one, which is precisely what "nothing happens"
    looks like. It tries the clipboard, falls back to execCommand, and either
    way leaves the text visible and selectable with the result said out loud.
    """
    if keep_existing:
        for cid, rows in _rows_from_existing_page(out_dir).items():
            if not made.get(cid):
                made[cid] = rows
    picked_total = sum(len(v) for v in made.values())
    short = [c["id"] for c in cast if len(made.get(c["id"], [])) == 0]
    rows = []
    for c in cast:
        files = made.get(c["id"], [])
        players = "".join(
            # THE AUDIO IS NOT INSIDE THE LABEL. It was, and a label
            # activates from anywhere inside it — so tapping PLAY would have
            # cast the vote, and every candidate you listened to would have
            # selected itself in passing. The label now wraps the radio and
            # its number only; the play control is a sibling.
            f'<div class="cand{" on" if f.get("onbrief") else ""}">'
            f'<label class=pickbox>'
            f'<input type=radio name="pick-{c["id"]}" value="{f["n"]}">'
            f'<span class=n>{f["n"]}</span></label>'
            f'<audio controls preload=none src="{f["file"]}"></audio>'
            # The metadata is omitted rather than printed as "?" when a page
            # is rebuilt from clips on disk, where the corpus row is long gone.
            # A row of question marks reads as broken; a row without them reads
            # as a duration, which is what it is.
            # THE SPEAKER ID IS ON THE PAGE. It was not, and that is how a
            # shortlist of the same voice six times over got delivered and
            # believed: nothing on screen distinguished six clips of one
            # person from six people, so it took somebody listening to catch
            # it. Two candidates showing the same id is now a visible fault
            # rather than an audible one.
            f'<span class=meta>{f["seconds"]}s'
            + (f' &middot; {f["speaker"]}' if f.get("speaker") else "")
            + (f' &middot; age {f["age"]}' if f.get("age") else "")
            + (f' &middot; {f["accent"]}' if f.get("accent") else "")
            + '</span></div>'
            for f in files)
        if not players:
            players = ('<p class=none>Nothing matched this brief in the rows '
                       'scanned. Re-run with a larger <code>--candidates</code>, '
                       'or fall back to <code>--source libritts</code>.</p>')
        rows.append(f"""
  <section id="{c['id']}">
    <h2>{c['name']} <code>{c['id']}</code></h2>
    <p class=brief>{brief_of(c)}</p>
    {players}
    <button class=clear type=button data-clear="{c['id']}">clear</button>
  </section>""")

    warn = ""
    if short:
        warn = (f"<p class=warn>{len(short)} character(s) came up empty: "
                f"<code>{', '.join(short)}</code>. That is reported rather than "
                f"quietly skipped.</p>")

    # RAW. The page carries JavaScript, and JavaScript carries backslashes:
    # `join('\n')` in a normal triple-quoted string is parsed by PYTHON
    # first, which turns it into a real newline and leaves the browser an
    # unterminated string literal. The page then died on load with "Invalid
    # or unexpected token" and every control on it did nothing — which is
    # exactly the symptom that started this.
    html = r"""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>LEDGER - voice casting</title>
<style>
 /* THE GAME'S OWN PALETTE, not one invented for this page. `UiTheme.cs` has
    had these since the UI pass: a green-biased near-black rather than a
    neutral one, amber for anything that wants attention, and the ledger's
    credit-green. The first draft of this page used a brown ground and brass
    gold, which looked fine and belonged to nothing. A casting tool for
    LEDGER should look like LEDGER.

    Deliberately dark-only. This is a listening tool for a night-time game and
    `color-scheme: dark` keeps the browser's own furniture in step; a light
    variant would be a different object, not a courtesy. */
 :root {
   color-scheme: dark;
   --ground:   #0c0f0e;   /* UiTheme.PanelDeep */
   --surface:  #101514;   /* UiTheme.PanelBg   */
   --field:    #0d1110;   /* UiTheme.Field     */
   --button:   #1c2422;   /* UiTheme.ButtonBg  */
   --hairline: #2a3431;   /* UiTheme.Hairline  */
   --ink:      #e6ece8;   /* UiTheme.Ink       */
   --dim:      #93a09a;   /* UiTheme.Dim       */
   --amber:    #ffa636;   /* UiTheme.Amber     */
   --amber-soft:#ffc272;  /* UiTheme.AmberSoft */
   --credit:   #4fc98c;   /* UiTheme.Credit    */
 }
 /* CONTENT-BOX IS WHY THE PAGE SCROLLED SIDEWAYS. `.meta` is flex-basis
    100% with a left indent, and under the default box model the indent is
    added to the 100% rather than taken out of it — 394px inside a 390px
    phone. One line, and the whole page stops overflowing. */
 *, *::before, *::after { box-sizing: border-box; }
 body { font: 16px/1.5 system-ui, -apple-system, sans-serif; max-width: 62rem;
        margin: 0 auto; padding: 1.2rem 1rem 7rem;
        background: var(--ground); color: var(--ink); }
 h1 { letter-spacing:.34em; font-weight:400; font-size:1.15rem;
      color: var(--dim); text-transform: uppercase; margin:0 0 .2rem; }
 h2 { margin:0 0 .3rem; font-weight:600; font-size:1.1rem; text-wrap: balance; }
 code { color: var(--amber); font-size:.9em; }
 section { border-top:1px solid var(--hairline); padding:1.2rem 0; }
 .brief { color: var(--dim); margin:.2rem 0 1rem; font-size:.95rem;
          max-width: 62ch; }
 .cand { display:flex; align-items:center; gap:.6rem; margin:.3rem 0;
         padding:.55rem .6rem; border-radius:.4rem; min-height:2.9rem;
         background: var(--surface); border:1px solid transparent;
         flex-wrap:wrap; }
 .cand:has(input:checked) { border-color: var(--amber); background:#16201d; }
 /* The tap target is the label, so it gets the padding rather than the
    radio: a 12px dot is not something to aim at on a moving train. */
 .pickbox { display:flex; align-items:center; gap:.5rem; flex:none;
            padding:.5rem .4rem; margin:-.5rem 0; cursor:pointer;
            border-radius:.3rem; }
 .cand input { width:1.35rem; height:1.35rem; accent-color: var(--amber);
               flex:none; }
 .cand audio { flex:1 1 14rem; min-width:0; height:2.2rem; }
 .n { width:1.5rem; text-align:right; color: var(--amber);
      font-variant-numeric: tabular-nums; flex:none; }
 .meta { color: var(--dim); font-size:.8rem; flex:1 0 100%; padding-left:3.6rem;
         font-variant-numeric: tabular-nums; }
 /* On the brief's own decade. Age no longer filters, so this is the only
    thing that still says which candidates the brief actually asked for, and
    it borrows the ledger's credit-green rather than a colour of its own. */
 .cand.on .n::after { content:"\2022"; color: var(--credit); margin-left:.25rem; }
 .none, .warn { color: var(--amber-soft); }
 .how { background: var(--surface); padding:1rem 1.2rem;
        border-left:3px solid var(--amber); font-size:.95rem; max-width:62ch; }
 .how p { margin:.5rem 0; }
 .clear { background:none; border:1px solid var(--hairline); color: var(--dim);
          padding:.35rem .8rem; border-radius:.3rem; font-size:.8rem;
          margin-top:.5rem; cursor:pointer; }
 #bar { position:fixed; left:0; right:0; bottom:0; background: var(--surface);
        border-top:1px solid var(--hairline); padding:.7rem 1rem;
        display:flex; gap:.7rem; align-items:center; flex-wrap:wrap; }
 #bar button { background: var(--amber); border:0; color: var(--ground);
               font-weight:600; padding:.7rem 1.1rem; border-radius:.4rem;
               font-size:1rem; cursor:pointer; }
 #count { color: var(--ink); font-size:.9rem; font-variant-numeric: tabular-nums; }
 /* WHAT IS LEFT, not just what is done. Nineteen characters is more than
    anybody holds in their head, and "7 picked" does not tell you who to go
    back to. */
 #left { color: var(--dim); font-size:.8rem; flex:1 0 100%; }
 #said { color: var(--credit); font-size:.9rem; }
 #out { width:100%; min-height:5rem; background: var(--field); color: var(--ink);
        border:1px solid var(--hairline); border-radius:.4rem; padding:.6rem;
        font-family:ui-monospace,monospace; font-size:.9rem; }
 details { margin-top:.6rem; width:100%; }
 summary { color: var(--dim); font-size:.85rem; cursor:pointer; }
 /* Keyboard users get to see where they are. */
 :focus-visible { outline:2px solid var(--amber); outline-offset:2px; }
 </style>
<h1>L E D G E R</h1>
<p>Voice casting &mdash; __TOTAL__ candidates from <b>__SOURCE__</b>.</p>
__WARN__
<div class=how>
<p><b>What to do.</b> Play the candidates under each brief and tap the one you
want. Judge against the brief, not against which voice is nicest &mdash;
whatever clip we hand the cloner BECOMES the character.</p>
<p><b>Age is a preference now, not a filter.</b> A green dot marks the
candidates in the decade the brief asked for; everyone else is still on the
page because a young voice can read older and the only way to know is to
listen. The age shown is the speaker's real one.</p>
<p>Picks are kept on this device as you go, so you can close this and come
back. When you are done, hit <b>Copy picks</b> at the bottom and send them
over.</p>
</div>
__ROWS__
<div id=bar>
  <button type=button id=copy>Copy picks</button>
  <span id=count></span><span id=said></span>
  <span id=left></span>
  <details><summary>show / edit the text</summary>
    <textarea id=out readonly></textarea>
  </details>
</div>
<script>
(function () {
  var KEY = 'ledger-voice-picks';
  var saved = {};
  try { saved = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { saved = {}; }

  // Restore before wiring, so restoring does not fire the change handler
  // once per character and write the same thing back nineteen times.
  Object.keys(saved).forEach(function (id) {
    var el = document.querySelector('input[name="pick-' + id + '"][value="' + saved[id] + '"]');
    if (el) el.checked = true;
  });

  function text() {
    return Object.keys(saved).sort().map(function (id) {
      return id + ' ' + saved[id];
    }).join('\n');
  }
  // Every character that has candidates to choose between. Read from the
  // page rather than passed in, so it cannot drift from what is rendered.
  var ALL = Array.prototype.map.call(
    document.querySelectorAll('section'), function (s) { return s.id; })
    .filter(function (id) {
      return document.querySelector('input[name="pick-' + id + '"]');
    });

  function refresh() {
    var n = Object.keys(saved).length;
    document.getElementById('count').textContent = n + ' of ' + ALL.length + ' picked';
    var todo = ALL.filter(function (id) { return !(id in saved); });
    document.getElementById('left').textContent =
      todo.length ? 'still to do: ' + todo.join(', ') : 'that is all of them.';
    document.getElementById('out').value = text();
    try { localStorage.setItem(KEY, JSON.stringify(saved)); } catch (e) {}
  }

  document.addEventListener('change', function (ev) {
    var t = ev.target;
    if (!t.name || t.name.indexOf('pick-') !== 0) return;
    saved[t.name.slice(5)] = t.value;
    refresh();
  });
  document.addEventListener('click', function (ev) {
    var id = ev.target.getAttribute && ev.target.getAttribute('data-clear');
    if (!id) return;
    delete saved[id];
    var el = document.querySelector('input[name="pick-' + id + '"]:checked');
    if (el) el.checked = false;
    refresh();
  });

  // ONE AUDIO AT A TIME. Two clips playing over each other is not a
  // comparison, and on a phone the second one is usually an accident.
  document.addEventListener('play', function (ev) {
    var all = document.getElementsByTagName('audio');
    for (var i = 0; i < all.length; i++) if (all[i] !== ev.target) all[i].pause();
  }, true);

  document.getElementById('copy').addEventListener('click', function () {
    var said = document.getElementById('said');
    var body = text();
    if (!body) { said.textContent = 'nothing picked yet'; return; }
    var box = document.getElementById('out');
    box.closest('details').open = true;

    function manual() {
      // LAST RESORT THAT STILL WORKS. Selecting the text means the OS copy
      // affordance is one long-press away even when both APIs are refused,
      // which beats a button that does nothing and says nothing.
      box.removeAttribute('readonly');
      box.focus(); box.setSelectionRange(0, body.length);
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      box.setAttribute('readonly', 'readonly');
      said.textContent = ok ? 'copied' : 'select the text above and copy it';
    }
    // navigator.clipboard is undefined outside a secure context and its
    // promise rejects without one. Unhandled, that is exactly "I clicked
    // copy picks and nothing happened".
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(body).then(function () {
        said.textContent = 'copied';
      }, manual);
    } else { manual(); }
  });

  // KEEP THE BAR OFF THE CONTENT. Measured rather than guessed, and
  // re-measured when the text panel opens, which is when it doubles in
  // height and swallows the last section.
  var bar = document.getElementById('bar');
  function pad() {
    document.body.style.paddingBottom = (bar.offsetHeight + 24) + 'px';
  }
  document.querySelector('#bar details').addEventListener('toggle', pad);
  window.addEventListener('resize', pad);

  refresh();
  pad();
})();
</script>
"""
    html = (html.replace("__TOTAL__", str(picked_total))
                .replace("__SOURCE__", str(source))
                .replace("__WARN__", warn)
                .replace("__ROWS__", "".join(rows)))
    (out_dir / "listen.html").write_text(html, encoding="utf-8")

    if not PICKS.exists():
        lines = ["# LEDGER voice picks. One line per character: <id> <candidate number>",
                 "# Delete the # in front of a line and put the winning number after it.",
                 "# Leave any you are unsure about — re-run the fetcher for more.", ""]
        for c in cast:
            lines.append(f"# {c['id']} 1    # {c['name']}")
        PICKS.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_picks():
    if not PICKS.exists():
        return {}
    picks = {}
    for line in PICKS.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            picks[parts[0]] = int(parts[1])
        except ValueError:
            continue
    return picks


def install(cast, repo_root):
    picks = read_picks()
    if not picks:
        print("No picks yet. Open ledger-voices-out/picks.txt and fill it in.")
        return 1
    dest = repo_root / "ledger" / "Assets" / "Voices"
    dest.mkdir(parents=True, exist_ok=True)
    known = {c["id"] for c in cast}
    installed, missing, unknown = [], [], []
    for cid, n in sorted(picks.items()):
        if cid not in known:
            unknown.append(cid)
            continue
        src = OUT / cid / f"candidate-{n:02d}.wav"
        if not src.exists():
            missing.append(f"{cid} #{n}")
            continue
        shutil.copyfile(src, dest / f"{cid}.wav")
        installed.append(f"{cid} <- candidate-{n:02d} ({seconds_of(src):.1f}s)")

    (dest / "casting.json").write_text(json.dumps(
        dict(version=VERSION, exaggeration=EXAGGERATION,
             cast={c["id"]: dict(name=c["name"], tier=c["tier"]) for c in cast},
             picked=picks), indent=2), encoding="utf-8")

    for line in installed:
        print("  " + line)
    if unknown:
        print(f"  ! not in the cast, ignored: {', '.join(unknown)}")
    if missing:
        print(f"  ! picked but no such candidate on disk: {', '.join(missing)}")
    print(f"\n{len(installed)} reference clip(s) in {dest}")
    print("Commit them and the game has a cast.")
    return 0 if installed else 1


# ---------------------------------------------------------------------------
# selftest — the assembly logic, with no network at all
# ---------------------------------------------------------------------------

def selftest():
    import numpy as np

    ok = fail = 0

    def check(cond, what, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"  ok   {what}")
        else:
            fail += 1
            print(f"  FAIL {what}" + (f" — {detail}" if detail else ""))

    def clip(sec, amp=0.4):
        n = int(SAMPLE_RATE * sec)
        return (np.sin(np.linspace(0, 220 * sec, n)) * amp).astype(np.float32)

    # One Common Voice sentence is never enough for a clone.
    check(assemble([clip(4.0)]) is None,
          "a single four-second sentence is refused, not shipped thin")
    check(assemble([clip(3.0), clip(3.0)]) is None,
          "and so is six seconds — under the floor is under the floor")

    joined = assemble([clip(4.0), clip(4.0), clip(4.0)])
    check(joined is not None, "three sentences make a usable reference")
    secs = len(joined) / SAMPLE_RATE
    check(MIN_SECONDS <= secs <= TARGET_SECONDS + 1.05,
          "and it lands in the window the cloner wants", f"{secs:.1f}s")

    many = assemble([clip(4.0)] * 30)
    check(len(many) / SAMPLE_RATE <= TARGET_SECONDS + 1.05,
          "thirty sentences do not become thirty seconds — every extra second "
          "costs on every line generated for the rest of the project",
          f"{len(many)/SAMPLE_RATE:.1f}s")

    one_long = assemble([clip(40.0)])
    check(one_long is not None and len(one_long) / SAMPLE_RATE <= TARGET_SECONDS + 1.05,
          "and a single very long clip is capped rather than passed through",
          f"{len(one_long)/SAMPLE_RATE:.1f}s")

    # The gap. A speaker who never breathes is a speaker the model learns.
    two = assemble([clip(5.0), clip(5.0)])
    quiet = np.sum(np.abs(two) < 1e-6)
    check(quiet > SAMPLE_RATE * 0.2,
          "there is real silence between sentences, so the clone learns a "
          "speaker who breathes", f"{quiet/SAMPLE_RATE:.2f}s of silence")

    check(assemble([]) is None and assemble(None) is None,
          "nothing in, nothing out — no crash on an empty bank")
    check(assemble([np.zeros(0, dtype=np.float32), clip(4.0), clip(4.0),
                    clip(4.0)]) is not None,
          "and an empty clip in the middle is stepped over")

    # Loudness, so you judge the voice and not the microphone.
    loud = normalise(clip(2.0, amp=0.9))
    soft = normalise(clip(2.0, amp=0.02))
    check(abs(float(np.max(np.abs(loud))) - float(np.max(np.abs(soft)))) < 1e-3,
          "a whisper and a shout arrive at the same level")
    check(float(np.max(np.abs(normalise(np.zeros(100, dtype=np.float32))))) == 0.0,
          "and silence is left alone rather than divided by")
    check(float(np.max(np.abs(loud))) <= 1.0,
          "nothing is normalised into clipping")

    # Resampling.
    r = resample(clip(1.0), 48000, 24000)
    check(abs(len(r) - SAMPLE_RATE * 0.5) <= 1,
          "48k halves into 24k", f"{len(r)} samples")
    same = clip(1.0)
    check(resample(same, SAMPLE_RATE, SAMPLE_RATE) is not None
          and len(resample(same, SAMPLE_RATE, SAMPLE_RATE)) == len(same),
          "and a matching rate is passed straight through")
    check(len(resample(np.zeros(0, dtype=np.float32), 48000)) == 0,
          "an empty clip resamples to an empty clip")

    # The cast table itself, because a typo here is a silently missing voice.
    ids = [c["id"] for c in CAST]
    check(len(ids) == len(set(ids)), "every character id is unique")
    check(all(c.get("gender") for c in CAST), "every brief carries a filter")
    check(all(c.get("accent") for c in CAST), "and an accent, chosen rather than drawn")
    check(canon_accent("United States English") == "american"
          and canon_accent("American") == "american",
          "an American is an American in either corpus's vocabulary")
    check(canon_accent("English") == "english" and canon_accent("Scottish") == "scottish",
          "and England and Scotland are not the same place")
    check(not accent_ok("Scottish", "american"),
          "a Scottish speaker cannot fill an American brief")
    check(accent_ok("NorthernIrish", "northernirish") and not accent_ok("", "irish"),
          "an unknown accent cannot satisfy a named one")
    # "any" IS A REAL VALUE, NOT AN EMPTY ONE. Unset means "an accent I have
    # a name for"; `any` means the brief does not care at all. The crowd
    # needs the second, and an Indian voice on a British dock is the case
    # that distinguishes them.
    check(accent_ok("Indian", "any") and accent_ok("Scottish", "any")
          and accent_ok("", "any"),
          "an `any` brief takes every accent, including ones with no canon name")
    check(not accent_ok("Indian", ""),
          "while an unset brief still means an accent this file can name")
    check(all(c["accent"] == "any" for c in CAST if c["tier"] == "crowd"),
          "and the crowd asks for any of them, because a dock town is mixed")
    # THE PROPERTY, NOT THE VALUE. This check was written when the base
    # accent was American and it asserted the literal string, so when the
    # city became British it went red for a change that was correct — while
    # a genuinely broken map (principals split across two accents) would
    # have passed it in the old world just as happily. Its own name says
    # what it means to test: they SHARE one, whichever one it is.
    _principals = [c for c in CAST if c["tier"] == "principal"]
    _base = {c["accent"] for c in _principals}
    check(len(_base) == 1,
          "the principals share one accent, which is what makes the others texture",
          str(sorted(_base)))
    # And that base has to be the majority of the cast, or "base" is just a
    # word for the accent five people happen to have.
    #
    # THE CROWD IS EXCLUDED FROM THAT COUNT, DELIBERATELY. Their briefs ask
    # for `any` accent now: the principals had taken nearly every English
    # speaker in VCTK and the last three crowd slots were starving, but the
    # real argument is not the shortage — a crowd in a British dock town
    # SHOULD be mixed, and a uniformly English one was the wrong picture all
    # along. It is the same reasoning that made Sam and Joey Scottish.
    #
    # So the base accent is a claim about the people you meet and talk to,
    # not about the background wash. Counting a deliberately mixed crowd
    # against it would make this check contradict the design it exists to
    # protect. Among the thirteen named characters English is still 8.
    _all = [c["accent"] for c in CAST if c["tier"] != "crowd"]
    check(_base and _all.count(list(_base)[0]) > len(_all) / 2,
          "and that accent is the majority of the whole cast, not just the principals",
          "%s = %d of %d" % (list(_base)[0] if _base else "?",
                             _all.count(list(_base)[0]) if _base else 0, len(_all)))
    check(len({c["accent"] for c in CAST}) >= 3,
          "and the edges are not all the same either")
    check(all(brief_of(c) for c in CAST), "and every brief has text to judge against")
    check(len(CAST) == 19,
          "nineteen clips, not thirty-seven — moods are an exaggeration "
          "parameter now, not a second recording", f"{len(CAST)}")
    check(set(EXAGGERATION) >= {"neutral", "grave", "bored"},
          "and the directions the benchmark proved are all mapped")
    check(EXAGGERATION["bored"] < EXAGGERATION["neutral"] < EXAGGERATION["grave"],
          "with the values ordered the way the listening test heard them")

    # Round trip through a real file.
    tmp = OUT / "_selftest" / "t.wav"
    write_wav(tmp, joined)
    check(abs(seconds_of(tmp) - secs) < 0.01, "a written clip reads back the same length")
    shutil.rmtree(tmp.parent, ignore_errors=True)

    # THE ROUTES ARE A SHAPE, AND THE SHAPE IS TESTABLE WITHOUT A NETWORK.
    # `_routes_for` returned None for one commit -- an extraction pushed the
    # three openers out to module level, so the function body was a docstring
    # and an import. The selftest passed all twenty-nine checks anyway, because
    # not one of them called it, and the failure surfaced as a TypeError in CI
    # thirty seconds into a job.
    #
    # Opening a corpus needs the internet. Checking that the factory returns a
    # non-empty list of (name, callable) does not, and that is the half that
    # broke.
    for _src in ("", "libritts", "commonvoice"):
        _r = _routes_for(_src, CAST)
        check(isinstance(_r, list) and len(_r) > 0,
              "_routes_for(%r) returns a non-empty list" % _src, repr(_r)[:60])
        check(all(isinstance(n, str) and callable(o) for n, o in (_r or [])),
              "_routes_for(%r) returns (name, callable) pairs" % _src)
    check([n for n, _ in _routes_for("", CAST)][0] == "vctk",
          "vctk is tried first, which is the corpus decision that was made")
    check(_routes_for("libritts", CAST)[0][0] == "libritts",
          "an explicit --source libritts does not silently try others first")

    # AGE BANDS. The old age_band had three branches and could not return
    # "thirties" or "fifties" at all -- two of the nine bands, and two the cast
    # asks for by name. Every value in the vocabulary must be reachable.
    check(age_band(35) == "thirties", "a 35-year-old is in their thirties", age_band(35))
    check(age_band(55) == "fifties", "a 55-year-old is in their fifties", age_band(55))
    check(age_band(22) == "twenties" and age_band(45) == "fourties"
          and age_band(68) == "sixties", "and the rest of the decades line up")
    _reach = {age_band(n) for n in range(10, 100)}
    check(all(b in _reach for b in CV_AGE_BANDS[:-1]),
          "every band below ninety is reachable from some age",
          str(sorted(CV_AGE_BANDS[i] for i in range(len(CV_AGE_BANDS) - 1)
                     if CV_AGE_BANDS[i] not in _reach)))
    # Common Voice hands back WORDS, not numbers. Passing one through int() was
    # how every Common Voice age silently became "" and stopped filtering.
    check(age_band("thirties") == "thirties" and age_band("fifties") == "fifties",
          "a band that arrives as a word survives the round trip")
    # A TARGETED RUN MUST NOT RE-OFFER SOMEBODY ELSE'S VOICE. Three missing
    # crowd voices were fetched alone and came back holding Lena's entire
    # shortlist, p228 included -- the clip she had just been cast from. The
    # exclusivity rule was real and had no memory across runs.
    import tempfile
    _tmp = Path(tempfile.mkdtemp())
    _rows = [dict(n=i, file=f"lena/candidate-{i:02d}.mp3", seconds=8.0,
                  speaker=f"p{224 + i}", age="22", accent="English")
             for i in range(1, 5)]
    # build_page writes picks.txt at module scope; point it somewhere
    # disposable without turning PICKS into a local in this function.
    globals()["PICKS"] = _tmp / "picks.txt"
    build_page([c for c in CAST if c["id"] == "lena"], {"lena": _rows}, _tmp, "vctk")
    _back = _rows_from_existing_page(_tmp)
    check([r["speaker"] for r in _back.get("lena", [])] == ["p225", "p226", "p227", "p228"],
          "a page round-trips its speaker ids",
          str([r.get("speaker") for r in _back.get("lena", [])]))
    # The seeding is what fetch() does with that: everybody NOT in this run's
    # cast keeps their speakers.
    _here = {"crowd_f1"}
    _claimed = {r["speaker"]: cid for cid, rs in _back.items() if cid not in _here
                for r in rs if r.get("speaker")}
    check(_claimed.get("p228") == "lena",
          "and a run for crowd_f1 alone still finds Lena holding p228",
          str(_claimed))
    check("crowd_f1" not in _claimed.values(),
          "while the character being re-fetched is left free to claim afresh")
    shutil.rmtree(_tmp, ignore_errors=True)

    # AGE ORDERS, IT NEVER REJECTS. The single most expensive bug in this
    # pipeline was not a crash: sixteen of nineteen characters were unfillable
    # because the briefs ask for fourties/fifties/sixties and VCTK's speakers
    # are 22 to 38. The corpus was fine. The filter was asking metadata to do
    # a job that belongs to somebody's ears.
    #
    # THE STRUCTURAL CHECK: run every character's brief against the ages VCTK
    # actually contains, and require that not one of them is emptied by age.
    # This is the check that, had it existed, would have ended this two days
    # ago -- so it is written against the real numbers, not against a fixture.
    _vctk_ages = (22, 23, 24, 26, 29, 31, 38)
    for _c in CAST:
        _gaps = [age_gap(n, _c.get("age")) for n in _vctk_ages]
        check(all(isinstance(g, int) for g in _gaps) and len(_gaps) == len(_vctk_ages),
              "%s: age scores every VCTK speaker rather than excluding them" % _c["id"])
    # 38 is in their thirties, and thirties to fifties is two bands, not one.
    # The first draft of this check asserted 1 and the check was wrong, not the
    # function -- which is the correct way round for once.
    check(age_gap(38, ("fifties", "sixties")) == 2,
          "the oldest voice VCTK has scores two bands off Rocco, and is still offered",
          age_gap(38, ("fifties", "sixties")))
    check(age_gap(35, ("thirties", "fourties")) == 0,
          "an exact band scores zero and sorts first", age_gap(35, ("thirties",)))
    check(age_gap(22, ("sixties",)) > age_gap(38, ("sixties",)),
          "and further away sorts later, so the ordering still carries the brief")
    check(age_gap(None, ("fifties",)) == 1 and age_gap("", ("fifties",)) == 1,
          "an unrecorded age sits behind an exact match, not behind everybody")
    check(age_gap(22, ()) == 0 and age_gap(22, None) == 0,
          "a brief with no age asked for treats every speaker equally")

    check(age_band("") == "" and age_band(None) == "" and age_band("abc") == "",
          "and an unusable age is empty rather than a wrong guess")
    # Every age the cast asks for has to exist in the vocabulary, or the brief
    # can never be satisfied by anything.
    _asked = {a for c in CAST for a in (c.get("age") or ())}
    check(_asked <= set(CV_AGE_BANDS),
          "every age band the cast asks for is one the corpus can supply",
          str(sorted(_asked - set(CV_AGE_BANDS))))

    # A NAMED CORPUS IS BINDING, and this is the check that would have caught
    # the whole affair: VCTK was chosen and Common Voice was used, for every run
    # after the decision, silently.
    check([n for n, _ in _routes_for("vctk", CAST)] == ["vctk"],
          "--source vctk offers VCTK and nothing else to fall back to",
          str([n for n, _ in _routes_for("vctk", CAST)]))
    check([n for n, _ in _routes_for("commonvoice", CAST)][0] == "vctk",
          "an unnamed preference still TRIES vctk first")

    print(f"\n{ok} passed, {fail} failed")
    return 1 if fail else 0


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--who", default="")
    # FOUR. A candidate is one distinct speaker now, and six each across the
    # nineteen briefs needs 114 different people out of a corpus with 110,
    # partitioned by accent and gender before anybody chooses.
    ap.add_argument("--candidates", type=int, default=4)
    # WALL CLOCK, not rows. Three CI runs were killed by the job cap with
    # nothing to show, because the clips are written in one go at the end.
    # 0 disables it, which is right for a laptop nobody is billing.
    ap.add_argument("--skip-rows", type=int, default=0, dest="skip_rows",
                    help="start this many rows into the corpus — the stretch a "
                         "previous run already claimed every speaker from")
    ap.add_argument("--minutes", type=int, default=0,
                    help="stop scanning after N minutes and write what is banked")
    ap.add_argument("--source", default="commonvoice",
                    choices=["vctk", "commonvoice", "libritts"])
    ap.add_argument("--inventory", action="store_true",
                    help="enumerate every speaker in the corpus from metadata "
                         "only, and write the table to vctk-speakers.json")
    ap.add_argument("--selftest", action="store_true")
    # TWO MINUTES INSTEAD OF FORTY-FIVE. Opens each route, reads a few rows,
    # and prints what the filter actually sees. See `diagnose` for why.
    ap.add_argument("--diagnose", action="store_true",
                    help="open the corpus, read a few rows, report what the filter sees")
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()

    print(f"LEDGER voice fetcher {VERSION}")
    OUT.mkdir(parents=True, exist_ok=True)

    cast = CAST
    if args.who:
        want = {w.strip() for w in args.who.split(",") if w.strip()}
        cast = [c for c in CAST if c["id"] in want]
        unknown = want - {c["id"] for c in CAST}
        if unknown:
            print(f"  ! no such character: {', '.join(sorted(unknown))}")
        if not cast:
            return 1

    if args.install:
        return install(CAST, HERE.parent.parent)

    if args.selftest:
        try:
            import numpy  # noqa: F401
        except ImportError:
            py = ensure_venv(args.yes, core_only=True)
            return subprocess.run([str(py), str(Path(__file__).resolve()),
                                   "--selftest", "--worker"]).returncode
        return selftest()

    if args.inventory:
        # Needs the venv for pyarrow/datasets, same as a fetch.
        if not args.worker:
            py = ensure_venv(args.yes)
            return subprocess.run([str(py), str(Path(__file__).resolve()),
                                   "--inventory", "--worker", "--yes"]).returncode
        return inventory(HERE / "vctk-speakers.json")

    if not args.worker:
        py = ensure_venv(args.yes)
        # EVERY FLAG, FORWARDED. This list used to be hand-written and it
        # silently dropped `--minutes`, so the wall-clock budget I added to
        # stop CI runs dying with nothing NEVER REACHED THE PROCESS THAT DOES
        # THE WORK. The parent parsed it, printed nothing, and re-executed a
        # worker with no budget at all.
        #
        # That is the whole class: a hand-maintained forwarding list is a
        # second copy of the argument spec, and the second copy is always the
        # one that rots. Anything added to the parser from here on has to be
        # added here too, so the ones that take a value are listed once and
        # the flags once, rather than each being spelled out.
        cmd = [str(py), str(Path(__file__).resolve()), "--worker"]
        for name, value in (("--candidates", args.candidates),
                            ("--source", args.source),
                            ("--who", args.who),
                            ("--skip-rows", args.skip_rows),
                            ("--minutes", args.minutes)):
            if value not in (None, "", 0):
                cmd += [name, str(value)]
        for name, flag in (("--no-open", args.no_open),
                           ("--diagnose", args.diagnose)):
            if flag:
                cmd += [name]
        return subprocess.run(cmd).returncode

    if args.diagnose:
        return diagnose(args.source, cast)

    print(f"  streaming {args.source} for {len(cast)} character(s), "
          f"{args.candidates} candidate(s) each")
    print("  this scans the corpus rather than downloading it; expect a few minutes\n")
    try:
        made, used_source = fetch(args.source, cast, args.candidates, OUT,
                                  args.minutes, args.skip_rows)
    except Exception as e:
        print(f"\n  fetch failed: {type(e).__name__}: {e}")
        if args.source == "commonvoice":
            print("  try:  python ledger_voice_fetch.py --source libritts")
        return 1

    # A `--who` run is ADDITIVE, and that needs BOTH halves: the rows of
    # everybody not re-fetched are read back off the existing page, and the
    # page is rendered over the WHOLE cast rather than the filtered one.
    # Merging the rows alone still produced a one-character page, because the
    # renderer loops over the cast it was handed.
    build_page(CAST if args.who else cast, made, OUT, used_source,
               keep_existing=bool(args.who))
    total = sum(len(v) for v in made.values())
    empty = [c["id"] for c in cast if not made.get(c["id"])]
    print(f"\n  {total} candidate(s) for {len(cast) - len(empty)} of {len(cast)} characters")
    if empty:
        print(f"  ! nothing for: {', '.join(empty)}")
    print(f"  page:  {OUT / 'listen.html'}")
    print(f"  picks: {PICKS}")

    if not args.no_open:
        page = str(OUT / "listen.html")
        try:
            if sys.platform == "win32":
                os.startfile(page)  # noqa
            elif sys.platform == "darwin":
                subprocess.run(["open", page])
            else:
                subprocess.run(["xdg-open", page])
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
