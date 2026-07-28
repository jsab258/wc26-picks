# TTS benchmark — run this on the gaming PC

Twenty minutes of setup, five minutes of listening, and it decides the whole
voice architecture. **Run it while I build the art pass.**

## What it is actually testing

Not "does it sound nice." Four things, in order of importance:

1. **CONSISTENCY.** Ten lines, one character, back to back. If a model can't
   make them sound like *one person*, it cannot voice a character however
   good any single line is. **This is the test that decides everything else.**
2. **DIRECTION.** The same sentence — *"So which is it going to be?"* — once
   bored, once grave. If the model ignores direction, we throw away our one
   structural advantage over KCD2's recorded barks: our simulation always
   knows how the speaker feels, and can say so.
3. **SPEED.** Real-time factor. Under ~0.35 we can voice live dialogue with
   no perceptible wait. Above ~1.0 it's offline-only.
4. **FOOTPRINT.** VRAM and install size — this ships to players.

The lines are **real game dialogue**, not "the quick brown fox." Testing TTS
on neutral sentences tells you nothing.

## Setup

```bash
cd tools/tts-benchmark
python -m venv .venv
# Windows:
.venv\Scripts\activate
# (mac/linux: source .venv/bin/activate)

pip install numpy
```

Then install whichever engines you want to compare. **Start with Kokoro** —
it's the smallest and most likely to be usable for live dialogue:

```bash
# 1. Kokoro — small, fast, American English. The "good enough and quick" bet.
pip install kokoro soundfile

# 2. XTTS — voice CLONING. The one that could solve the pre-generated vs
#    runtime seam (see below). Heavier, ~4GB VRAM.
pip install TTS
#    then put 6-10 seconds of clean reference speech per voice in:
#      refs/lena.wav  refs/rocco.wav  refs/mara.wav  refs/crowd_m.wav  refs/crowd_f.wav
#    (any clean American-accented speech works for a test — even your own)

# 3. Piper — CPU-only, fast, lower ceiling. The CONTROL CASE: if something
#    more expensive isn't audibly better than this, it isn't worth its cost.
pip install piper-tts
#    download a voice from the piper releases, then:
#      set PIPER_MODEL=C:\path\to\en_US-lessac-medium.onnx
```

Versions move fast and my knowledge has a cutoff — if a `pip install` or an
API has drifted, the script will tell you which adapter failed and the fix is
a few lines in `bench.py`. Send me the error.

## Run

```bash
python bench.py --list          # what's installed
python bench.py --engine all    # everything installed
```

## Then listen, in this order

1. **`out/<engine>/consistency/00..09.wav`** — play all ten straight through.
   *Is this one person?* If no, that engine is out for character voice
   regardless of anything else.
2. **`same_line_bored.wav` vs `same_line_grave.wav`** — identical text.
   Obviously different, or the same reading twice?
3. **`emphasis_test.wav`** — "That's **your** problem." Does the stress land
   on *your*? This is the single best test of whether a model reads meaning
   or just words.
4. **`hard_prosody.wav`** — is "$120" spoken as *a hundred and twenty* and
   "day 8" as *day eight*? Or read as symbols?
5. **`long_dialogue.wav`** — does it stay alive to the end, or flatten out?

## What to send back

`out/` zipped, or just tell me per engine: *one person or several? did
direction land? did the emphasis land? and did anything sound obviously
synthetic — and how?* The last one is the bar you set.

## The seam problem this is really about

If we voice pre-generated barks with an expensive model and live dialogue
with a cheap one, **the same character will have two voices.** That's worse
than no voice at all.

Three ways out, and this benchmark tells us which is open:

- **A. Cloning (best).** Define each character's voice ONCE as a reference
  clip, then use a cloning model for *everything* — barks and live dialogue
  both. Identity comes from the reference, not the engine, so it's consistent
  by construction and free at runtime. **This is what XTTS is in the test
  for.** If its clones hold up, this is the answer.
- **B. One model throughout.** Pick a single engine good enough for both.
  Consistency guaranteed, quality capped at that engine.
- **C. Split by who, not by when.** Named cast always on one engine; the
  anonymous crowd on another. This works because **the seam only matters
  *within* a character** — nobody notices that a passing stranger's voice
  engine differs from Lena's. Cheapest, and safe.

Two mitigations apply whichever we pick, and both are free:

- **One post-processing chain for all voice** — same EQ, same room reverb,
  same light compression. Unifying the acoustic *space* hides a surprising
  amount of engine difference.
- **Context already differs.** Barks are heard across a street, through
  weather, at distance (so: filtered, quieter, reverberant). Live dialogue is
  close and clean. Those are different acoustic situations anyway, which
  masks a lot on its own.
