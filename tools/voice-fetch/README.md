# LEDGER — voice reference fetcher

**Your part is two commands and a listening pass.**

```
python ledger_voice_fetch.py          # streams candidates, opens a page
# ... listen, write picks into ledger-voices-out/picks.txt ...
python ledger_voice_fetch.py --install
```

That is it. The first command builds its own environment, streams Mozilla
Common Voice (it does **not** download the 80GB tarball), assembles about
eleven seconds of one speaker per candidate, and opens a page with each
character's casting brief printed above its players. The second copies your
picks into `ledger/Assets/Voices/` with a `casting.json`.

## Why the briefs are written the way they are

Chatterbox clones from about ten seconds of reference audio, so **whatever
clip we hand it becomes the character.** That inverts the usual casting
problem: rather than hunting for a voice that already sounds like Lena, the
doc describes Lena and any clip carrying that timbre is a valid casting.

Judge against the brief, not against which voice is nicest. For Hal and the
crowd the bar is *inverted* — if a candidate is interesting, it is wrong.

## Moods are a parameter now, not a second recording

The casting doc originally asked for three clips per principal (neutral,
grave, bored). Common Voice contributors read neutral sentences, so a
"grave" clip is not something that corpus contains — but chatterbox has an
explicit exaggeration control and the benchmark proved it works on real game
lines. The reference clip decides **identity**; exaggeration decides
**direction**.

37 clips became 19, and the listening pass went from about forty minutes to
about fifteen.

## The consent rule

Clips come only from corpora whose contributors donated their voices *to
build speech technology* — Common Voice (CC0) first, LibriTTS as fallback.
Public domain settles copyright and does not settle consent. No identifiable
public figures.

## If Common Voice will not stream

```
python ledger_voice_fetch.py --source libritts
```

LibriTTS rows carry no age or gender, so every brief sees every speaker and
the filtering is entirely your ears. The script says so rather than
pretending the filter worked.

## Other flags

| | |
|---|---|
| `--who lena,rocco` | just these characters |
| `--candidates 6` | more voices per character (default 4) |
| `--selftest` | proves the assembly logic with no network at all |
| `--yes` | don't ask before installing packages |
| `--no-open` | don't open the page |

## What `--selftest` is for

The interesting logic is not the download, it is the assembly: a single
Common Voice sentence is three to six seconds and a clone needs ten, so
candidates are built by concatenating the **same speaker** with real silence
between sentences (butt-joined audio teaches the model a speaker who never
breathes). 22 checks cover that, the loudness match, the resampling and the
cast table, and none of them touch the network.

**I could not test the download path from here** — Common Voice, HuggingFace
and OpenSLR are all blocked from my environment. That is why the fetch path
reports what it could not find per character instead of failing quietly, and
why there is a fallback corpus.
