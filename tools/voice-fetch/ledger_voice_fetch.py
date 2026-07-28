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
    --candidates 5          how many voices to offer per character (default 4)
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
    dict(id="lena", name="LENA", tier="principal", gender="female_feminine",
         age=("thirties", "fourties"),
         brief="Bar's bookkeeper, late 30s. Mid-low, dry, unhurried. She has "
               "known this family twenty years and is never surprised by it. "
               "WHAT MUST COME THROUGH: withheld judgement — she knows more "
               "than she says in every line. If it sounds like it is telling "
               "you everything, it is the wrong voice. Avoid bright, young, warm."),
    dict(id="rocco", name="ROCCO", tier="principal", gender="male_masculine",
         age=("fourties", "fifties", "sixties"),
         brief="Works the door, 50s. Low, worn, slightly gravelly. Money is "
               "always a little short and it is audible. WHAT MUST COME "
               "THROUGH: decency without softness. Not a tough-guy voice — a "
               "tired one."),
    dict(id="ellis", name="MARA ELLIS", tier="principal", gender="female_feminine",
         age=("fourties", "fifties"),
         brief="Detective, 40s. Level, unhurried, PLEASANT. WHAT MUST COME "
               "THROUGH: that she never has to raise her voice. Cast against "
               "type — pick the warmest, most reasonable voice here. A cold "
               "voice makes her a villain; a courteous one makes her inevitable."),
    dict(id="reese", name="TOBIAS REESE", tier="principal", gender="male_masculine",
         age=("fourties", "fifties"),
         brief="Board of Excise, the audit's face. Precise, mid register, "
               "faintly bureaucratic. WHAT MUST COME THROUGH: that this is not "
               "personal. He is reading from a procedure and the procedure "
               "will convict you."),
    dict(id="kest", name="SERA KEST", tier="principal", gender="female_feminine",
         age=("thirties", "fourties"),
         brief="Rival head. Controlled, harder than Lena, younger than Mara. "
               "WHAT MUST COME THROUGH: someone used to being agreed with."),

    dict(id="sam", name="SAM", tier="street", gender="male_masculine",
         age=("twenties", "thirties"),
         brief="Walks the block at all hours, trades in being useful. Mid-high, "
               "quick, ingratiating, never still. THE FASTEST TALKER IN THE "
               "GAME — the voice should sound like it is already moving on to "
               "the next person."),
    dict(id="ada", name="ADA", tier="street", gender="female_feminine",
         age=("sixties", "seventies"),
         brief="Retired schoolteacher, the street's unofficial conscience. "
               "Older, clear, precise diction. WHAT MUST COME THROUGH: that "
               "she expects to be listened to, and is usually right."),
    dict(id="vesna", name="VESNA", tier="street", gender="female_feminine",
         age=("fourties", "fifties"),
         brief="Keeps house at the chapel, the quietest well of information. "
               "Soft, low volume, careful. QUIET IS THE CASTING — everything "
               "she knows arrived through a door left ajar."),
    dict(id="marla", name="MARLA", tier="street", gender="female_feminine",
         age=("fourties", "fifties"),
         brief="Vegetable stall at the market corner. Warm, carrying, "
               "market-pitch. The loudest woman in the cast and the most "
               "ordinary."),
    dict(id="joey", name="JOEY", tier="street", gender="male_masculine",
         age=("fourties", "fifties"),
         brief="Dock hand, twenty years on the water. Big, slow, plain. One "
               "daughter he would burn the port down for. SIMPLICITY IS THE "
               "CASTING — no irony in the voice at all."),
    dict(id="rita", name="RITA", tier="street", gender="female_feminine",
         age=("thirties", "fourties"),
         brief="Left-handed, owes nobody an explanation. Blunt, flat, short. "
               "The one who ends conversations."),
    dict(id="hal", name="HAL", tier="street", gender="male_masculine",
         age=("thirties", "fourties"),
         brief="Carries messages, meetings, prices, peace. Neutral to the "
               "point of being forgettable — DELIBERATELY THE LEAST "
               "DISTINCTIVE VOICE IN THE GAME. That is his job. If a candidate "
               "is interesting, it is wrong."),
    dict(id="emil", name="FATHER EMIL", tier="street", gender="male_masculine",
         age=("sixties", "seventies"),
         brief="Older, measured, resonant. Used to being heard in a room that "
               "goes quiet for him."),

    # Six anonymous voices. The bar here is INVERTED: a crowd voice you can
    # recognise stops being a crowd, so the right pick is the dullest one.
    dict(id="crowd_m1", name="CROWD — male, young", tier="crowd",
         gender="male_masculine", age=("twenties",), brief=None),
    dict(id="crowd_m2", name="CROWD — male, middle", tier="crowd",
         gender="male_masculine", age=("fourties",), brief=None),
    dict(id="crowd_m3", name="CROWD — male, older", tier="crowd",
         gender="male_masculine", age=("sixties",), brief=None),
    dict(id="crowd_f1", name="CROWD — female, young", tier="crowd",
         gender="female_feminine", age=("twenties",), brief=None),
    dict(id="crowd_f2", name="CROWD — female, middle", tier="crowd",
         gender="female_feminine", age=("fourties",), brief=None),
    dict(id="crowd_f3", name="CROWD — female, older", tier="crowd",
         gender="female_feminine", age=("sixties",), brief=None),
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
FETCH_PKGS = ["datasets>=3", "soundfile", "librosa"]
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
    stamp.write_text("ok\n")
    return py


# ---------------------------------------------------------------------------
# fetching (runs INSIDE the venv, via --worker)
# ---------------------------------------------------------------------------

CV_DATASET = "fsicoli/common_voice_17_0"   # ungated mirror; same CC0 clips
LIBRITTS_DATASET = "blabble-io/libritts_r"


def fetch(source, cast, candidates, out_dir):
    """Stream a corpus and bank enough audio per speaker to make candidates.

    Streaming rather than downloading: Common Voice English is tens of
    gigabytes and we need about four minutes of it. A script that makes you
    wait for an 80GB tarball is a script you do not run.
    """
    import numpy as np
    from datasets import load_dataset

    wanted = {}
    for c in cast:
        wanted[c["id"]] = dict(spec=c, banked={}, done=[])

    if source == "libritts":
        ds = load_dataset(LIBRITTS_DATASET, "clean", split="train.clean.100",
                          streaming=True)
        key_speaker, key_audio = "speaker_id", "audio"
        def matches(row, spec):
            # LibriTTS carries no age or gender in the row, so every brief
            # sees every speaker and the filtering is your ears. Said out
            # loud rather than silently pretending the filter worked.
            return True
    else:
        ds = load_dataset(CV_DATASET, "en", split="train", streaming=True)
        key_speaker, key_audio = "client_id", "audio"
        def matches(row, spec):
            g = (row.get("gender") or "").strip()
            a = (row.get("age") or "").strip()
            if spec.get("gender") and g and g != spec["gender"]:
                return False
            if spec.get("age") and a and a not in spec["age"]:
                return False
            # A row with no metadata at all is not a match — it is an
            # unknown, and filling a shortlist with unknowns is the same as
            # not filtering.
            return bool(g)

    seen_rows = 0
    for row in ds:
        seen_rows += 1
        if seen_rows % 2000 == 0:
            left = sum(1 for w in wanted.values() if len(w["done"]) < candidates)
            print(f"    {seen_rows} rows scanned, {left} characters still short")
        if all(len(w["done"]) >= candidates for w in wanted.values()):
            break
        if seen_rows > 400000:
            print("    stopping: scanned 400k rows, taking what we have")
            break

        audio = row.get(key_audio)
        if not audio:
            continue
        arr = audio.get("array")
        rate = audio.get("sampling_rate")
        if arr is None or not rate:
            continue
        speaker = row.get(key_speaker) or ""
        if not speaker:
            continue
        mono = resample(np.asarray(arr, dtype=np.float32).reshape(-1), rate)

        for cid, w in wanted.items():
            if len(w["done"]) >= candidates:
                continue
            if speaker in w["banked"] or matches(row, w["spec"]):
                bank = w["banked"].setdefault(speaker, [])
                if len(bank) > 12:
                    continue
                bank.append(mono)
                joined = assemble(bank)
                if joined is not None:
                    w["done"].append((speaker, normalise(joined)))
                    del w["banked"][speaker]
                break   # one character per row; sharing a voice defeats casting

    made = {}
    for cid, w in wanted.items():
        files = []
        for i, (speaker, samples) in enumerate(w["done"][:candidates], 1):
            p = out_dir / cid / f"candidate-{i:02d}.wav"
            write_wav(p, samples)
            files.append(dict(n=i, file=f"{cid}/candidate-{i:02d}.wav",
                              speaker=str(speaker)[:12],
                              seconds=round(len(samples) / float(SAMPLE_RATE), 1)))
        made[cid] = files
    return made


# ---------------------------------------------------------------------------
# the listening page
# ---------------------------------------------------------------------------

def build_page(cast, made, out_dir, source):
    short = [c["id"] for c in cast if len(made.get(c["id"], [])) == 0]
    rows = []
    for c in cast:
        files = made.get(c["id"], [])
        players = "".join(
            f'<div class=cand><span class=n>{f["n"]}</span>'
            f'<audio controls preload=none src="{f["file"]}"></audio>'
            f'<span class=meta>{f["seconds"]}s</span></div>'
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
    <p class=pick>Winner → write <code>{c['id']} N</code> in picks.txt</p>
  </section>""")

    warn = ""
    if short:
        warn = (f"<p class=warn>{len(short)} character(s) came up empty: "
                f"<code>{', '.join(short)}</code>. That is reported rather than "
                f"quietly skipped.</p>")

    html = f"""<!doctype html><meta charset=utf-8>
<title>LEDGER — voice casting</title>
<style>
 body {{ font: 16px/1.5 system-ui, sans-serif; max-width: 62rem; margin: 2rem auto;
        padding: 0 1rem; background:#12100e; color:#e8e2d8; }}
 h1 {{ letter-spacing:.3em; font-weight:400; }}
 h2 {{ margin:0 0 .3rem; font-weight:500; }}
 code {{ color:#c9a227; }}
 section {{ border-top:1px solid #2c2822; padding:1.4rem 0; }}
 .brief {{ color:#b6ada0; margin:.2rem 0 1rem; }}
 .cand {{ display:flex; align-items:center; gap:.7rem; margin:.35rem 0; }}
 .n {{ width:1.6rem; text-align:right; color:#c9a227; }}
 .meta {{ color:#6d675e; font-size:.85rem; }}
 .pick {{ color:#6d675e; font-size:.9rem; margin:.7rem 0 0; }}
 .none, .warn {{ color:#c98b27; }}
 .how {{ background:#1a1714; padding:1rem 1.2rem; border-left:3px solid #c9a227; }}
</style>
<h1>L E D G E R</h1>
<p>Voice casting — {sum(len(v) for v in made.values())} candidates from
<b>{source}</b>.</p>
{warn}
<div class=how>
<p><b>What to do.</b> Play the candidates under each brief. Judge against the
brief, not against which voice is nicest — whatever clip we hand the cloner
BECOMES the character.</p>
<p>Open <code>picks.txt</code> next to this page and write one line per
character: <code>lena 3</code>. Skip any you are unsure about; you can run
this again.</p>
<p>Then: <code>python ledger_voice_fetch.py --install</code></p>
<p>Direction is a parameter, not a second clip — the cloner's exaggeration
control does moods, so one clip per character is the whole ask.</p>
</div>
{''.join(rows)}
"""
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

    print(f"\n{ok} passed, {fail} failed")
    return 1 if fail else 0


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--who", default="")
    ap.add_argument("--candidates", type=int, default=4)
    ap.add_argument("--source", default="commonvoice",
                    choices=["commonvoice", "libritts"])
    ap.add_argument("--selftest", action="store_true")
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

    if not args.worker:
        py = ensure_venv(args.yes)
        cmd = [str(py), str(Path(__file__).resolve()), "--worker",
               "--candidates", str(args.candidates), "--source", args.source]
        if args.who:
            cmd += ["--who", args.who]
        if args.no_open:
            cmd += ["--no-open"]
        return subprocess.run(cmd).returncode

    print(f"  streaming {args.source} for {len(cast)} character(s), "
          f"{args.candidates} candidate(s) each")
    print("  this scans the corpus rather than downloading it; expect a few minutes\n")
    try:
        made = fetch(args.source, cast, args.candidates, OUT)
    except Exception as e:
        print(f"\n  fetch failed: {type(e).__name__}: {e}")
        if args.source == "commonvoice":
            print("  try:  python ledger_voice_fetch.py --source libritts")
        return 1

    build_page(cast, made, OUT, args.source)
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
