# voice-gen — rendering the bark bank

**Run this on your machine, not in CI.** The render needs a GPU and chatterbox;
everything else here works anywhere.

```
python3 tools/voice-gen/ledger_voice_gen.py --plan       # what would render
python3 tools/voice-gen/ledger_voice_gen.py --rate 20    # DO THIS FIRST
python3 tools/voice-gen/ledger_voice_gen.py --all        # the batch
```

## The number to get first

`--rate 20` renders twenty lines and prints how long each took, then projects
the full batch. **Nothing about the schedule is known until that lands** — the
only figure anyone has is ~6× slower than real time on a CPU, measured during
the engine benchmark, and a GPU changes that by a factor nobody here can guess.

It samples one line from each direction band rather than the first twenty
lines, so the first thing you listen to also answers the question this
container cannot: whether a line at 0.30 and a line at 0.80 actually sound
differently directed. If they do not, the direction map is wrong and it is
better to know that after twenty renders than after three hundred.

## What it renders, and what it does not

| | |
|---|---|
| **336 lines** | the atomic slots — what actually gets spoken |
| **2,268 lines** | pair slots, rendered **not at all** |

A pair slot holds strings like `Bit of nonsense going about — the new owner was
at the warehouse on Tuesday. || God. And here?`. They were enumerated so a human
could review distinct conversations, and both halves already exist as atomic
lines. `BarkGen.Answer()` picks an opener and a reply *independently* at run
time, so those 2,268 strings are never spoken as written. Rendering them would
be seven times the work and every file would be unplayable.

The self-test asserts this both ways — no atomic line contains the separator,
and every sampled pair line is two lines that already exist — so if the claim
ever stops being true, the commit that broke it goes red rather than a night of
rendering.

## Voices

Barks carry no speaker. They are lines any passer-by says, so they render in the
six street voices from `game-design/picked-clips/`, assigned by position so the
336 lines split exactly 56 apiece. `--voices-per-line 2` doubles the batch and
gives every line two distinct voices; the default is 1, because variety in this
bank comes from having fourteen ways to say each thing rather than six people to
say it.

## Safety

It never deletes and never overwrites unasked. A re-run **skips** what exists,
which is also what makes it resumable — kill it and start it again. `--force`
counts and names what it is about to replace before replacing it.

That is not general caution: a CI run once committed an empty output directory
over 24 clips that had already been listened to and picked from, and reported
success.

## The direction values — authored, then confirmed

They are a judgement about how each kind of line is said. `recognition.avoids`
at 0.30 is muttered at the pavement; `recognition.confronts` at 0.80 is the
loudest thing in the game. They could not be measured from a container with no
GPU and no model, so they shipped as a named guess and `--rate` was built to
sample one line per band rather than the first twenty, so the first listen
would settle it.

**Confirmed 5 August.** Bands 0.25, 0.30, 0.45, 0.60 and 0.80 were rendered and
listened to; they read as different people in different moods. Still open to
argument, no longer unverified.

## Resume, and why it is not just "does the file exist"

Each clip records what it was rendered FROM: the line, the voice, the direction.
A re-run skips only what still matches. The first version compared filenames
alone, and a filename is `slot.index.voice.wav` — it carries none of the text.
So when an encoding bug was fixed in the bark bank, the clips already on disk
kept their names, kept being skipped, and would have shipped with the mangled
words spoken into them.

Four states: **missing**, **fresh**, **stale** (text, voice or direction moved
since), and **unknown** (on disk with nothing recording what it came from —
re-rendered rather than trusted, because a clip with no record is not evidence).
