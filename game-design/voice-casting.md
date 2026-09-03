# Voice casting

> **STATUS: LIVE, verified 2026-08-04.** who sounds like what, the 19 cast voices,
> and what actually generates the audio.
> Kept current. If it is wrong, that is a bug in this file.

## CAST — all nineteen, 2026-07-31

Jafar listened and picked. Recorded by **speaker id**, not candidate number: a
number means a row on one particular page, a speaker id means a person, and the
page gets regenerated.

| character | speaker | accent | age |
|---|---|---|---|
| `lena` | **p228** | English | 22 |
| `rocco` | **p227** | English | 38 |
| `ellis` | **p231** | English | 23 |
| `reese` | **p256** | English | 24 |
| `kest` | **p244** | English | 22 |
| `sam` | **p241** | Scottish | 21 |
| `ada` | **p276** | English | 24 |
| `vesna` | **p238** | NorthernIrish | 22 |
| `marla` | **p282** | English | 23 |
| `joey` | **p263** | Scottish | 22 |
| `rita` | **p249** | Scottish | 22 |
| `hal` | **p273** | English | 23 |
| `emil` | **p245** | Irish | 25 |
| `crowd_m1` | **p287** | English | 23 |
| `crowd_m2` | **p272** | Scottish | 23 |
| `crowd_m3` | **p292** | NorthernIrish | 23 |
| `crowd_f1` | **p266** | Irish | 22 |
| `crowd_f2` | **p265** | Scottish | 23 |
| `crowd_f3` | **p288** | Irish | 22 |

The chosen clips are copied to `game-design/picked-clips/<character>.<speaker>.mp3`,
a directory nothing in the fetch pipeline writes to. The identity of a choice
and the evidence for it live together.

**Checked rather than assumed:** nobody is cast twice, and the sixteen picked
before the final crowd fetch still resolve to the same sixteen people — the run
that filled the crowd moved nobody. That is what the cross-run claim seeding
exists for, confirmed against real picks rather than a fixture.

**Rocco is p227, age 38** — the oldest speaker VCTK holds, and precisely the
voice the age filter discarded on the morning of the 31st for being two decades
short of a fifties brief. The whole day turned on that filter being wrong.

## HOW THE AUDIO GETS MADE — added 2026-08-04, because it was asked twice

This file said who sounds like what and never said what turns that into sound,
so the question had to be answered out of `production-plan-audio-art.md` twice
in one week. It belongs here too.

**Engine: chatterbox. Local, on Jafar's machine, $0, no API.** Decided
2026-07-28 on the direction test — §1i of the production plan is headed
"DECIDED", and the benchmark ran four engines: piper as the deliberate control
floor, kokoro, xtts and chatterbox. Three failed the direction test
identically; one passed. Jafar's own verdicts: *"chatterbox sounds pretty
good"*, bored-vs-grave *"different with chatterbox"*, ten lines in one voice
*"was, alive"*, and *"don't like the actual voice"*.

**That last verdict is why the table above exists.** The reference clip decides
IDENTITY and the engine's exaggeration parameter decides DIRECTION — bored 0.25
through urgent 0.85. So the model's own voice is never heard; it wears one of
the nineteen picked above.

**There is nothing to record.** The nineteen clips in
`game-design/picked-clips/` are the reference audio, and they are VCTK speakers
who donated their voices to speech research. Jafar, 2026-07-31: *"free
obviously. i won't be recording anything."*

**The one number nobody has: seconds per clip on his GPU.** Everything else
about the pipeline is decided. The plan's own first step is a run that
generates twenty clips and reports the rate, and until that lands any schedule
for the bark bank is a guess.

---

## Who is still uncast — RE-COUNTED 2026-08-04, and it was two numbers

**`verify.py` reports 4 and this file said 15, and both were right about
different sets.** That is unreadable, so: `tools/voice-cast-check.py` walks the
TIER-1 ids only — ten of them — and reports **Aldous Vane, Danny Ro, June and
Zlata** as the four principals with no cast voice. The fifteen this file used
to claim was a count over all named characters, taken on 31 July and never
re-taken.

**Ossei is uncast and is not in either list**, which is the sharpest reason to
write this down: he has no id in `VoiceBank` at all, so the tier-1 check cannot
see him, and he is an Act III condition. Checked directly rather than inferred
from a count.

The whole-roster figure is deliberately not restated here until something
counts it, because a number nobody has re-measured is worse than no number.

Uncast characters fall through to a crowd voice rather than throwing, so the
symptom is a named character quietly sounding like a passer-by.

---

## Accent — decided 2026-07-30, moved 2026-07-31

**English base, with the other accents as deliberate texture at the edges.**

The first version of this table said *American* base, for a reason that was
sound at the time: the writing sat in that register and the surnames read as a
port built on arrivals. Jafar chose the British setting on 2026-07-31 and the
premise turned out to be wrong in a useful way — counting whole words, the
project was already writing `flat`, `colour`, `pavement`, `constable`,
`neighbourhood`, `kerb`, and naming streets Saltmarket, Quay Street, The
Esplanade, Weighhouse Lane. The city had been a British port town all along.
See `setting-britain-2026-07-31.md`.

| | accent | why |
|---|---|---|
| **All five principals** | english | one register at the centre, so the edges can differ and mean something |
| Ada, Marla, Hal | english | the street the player lives on |
| **Sam, Joey, Rita** | scottish | being from elsewhere as characterisation rather than noise |
| **Vesna** | northernirish | came from elsewhere and learned it here — keep her the outsider |
| **Father Emil** | irish | Irish clergy in a British port is the ordinary case, not a flourish |
| Crowd (6) | **any** | see below — the background is where a port city sounds like one |

One American slot is held in reserve rather than deleted, for a character who
earns being visibly not from here.

### The crowd takes any accent — 2026-07-31

The six pool voices asked for English and Scottish, and the last three of them
starved: the principals had claimed nearly every English speaker VCTK has, and
a targeted run for the remaining slots came back with nothing at all.

The shortage is what forced the question, but it is not the answer. **A crowd
in a British dock town should be mixed.** A uniformly English background was
the wrong picture regardless of what the corpus could supply — it is the same
argument that made Sam and Joey Scottish, applied to the people who never get
named. Irish, Welsh, Indian and Scottish voices in the wash of a port city are
not texture added on top; they are what a port city sounds like.

So the crowd briefs ask for `any`, which is a distinct value from unset: unset
means "an accent this file has a name for", `any` means the brief genuinely
does not care. An Indian voice on the dock front satisfies `any` and is
rejected by unset, which is exactly the distinction wanted.

**The base accent is now measured over the thirteen named characters, not all
nineteen.** English is 8 of 13 there and still clearly the base. Counting a
deliberately mixed crowd against a "the base must dominate" check would make
that check argue with the design it exists to protect.

The three crowd voices already cast — crowd_m1 (English), crowd_m2 and
crowd_f2 (Scottish) — are unaffected and are themselves a reasonable mix.

**The principals must share the base, and the selftest enforces it.** My first
draft gave Rocco and Sera Kest Scottish voices because the timbre suited them,
and the check caught it: if the principals are split, the base is not a base
and everything is texture.

## Age is a preference, not a filter — 2026-07-31

**This is what cost fifteen CI runs.** The briefs ask for fourties, fifties and
sixties for almost every principal — Rocco is 50s, Ellis 40s, Reese fifty-ish.
VCTK was recorded from university-age volunteers and its speakers are 19 to 38.
Against this corpus those briefs could not be satisfied by anybody alive in it,
and 27.7% of every rejection was that one field.

The corpus was not the problem. **These are reference clips for casting a
timbre, not the shipped performance**, and a speaker's chronological age does
not decide whether the voice suits the part. A 38-year-old with a low, worn,
dry voice is a better Rocco than a 55-year-old with a light one, and the only
instrument that can tell them apart is somebody listening.

So age never rejects. It orders: distance in decades from the nearest
requested band, closest first, then cleanest recording. The listening page
shows each candidate's real age and marks the on-brief decade with a green
dot, because the listener is now the one weighing it.

### What that changed, measured

| | before | after |
|---|---|---|
| characters matching **nothing** | 16 of 19 | **0 of 19** |
| rows accepted | 5.3% | **23.9%** |
| rejected on age | 27.7% | **0%** |
| accents the sample could see | English only | English, Scottish, Irish, NorthernIrish, Welsh, Indian |

The accent column moved for a second reason: the diagnostic's sampling stride
was 97, which over 60 samples walks the first 13% of a 44,000-row corpus. VCTK
is ordered by speaker, so it was reading the first dozen speakers and reporting
on the corpus. Stride is 401 now — prime, near VCTK's ~400 utterances per
speaker — so each sample lands on a fresh voice.

**The thin slots, and they are thin by accent rather than by age:** Emil
(irish) and Vesna (northernirish) draw from a handful of speakers each, and
the Scottish women (Rita, crowd_f2) are not much better. Those are the ones to
watch on a short run; everybody else has depth.

## How casting works here, which is not how it usually works

Chatterbox clones from about ten seconds of reference audio. So we do not
pick a voice off a list — **whatever clip we hand it becomes the character.**
That inverts the usual problem: instead of hunting for a voice that already
sounds like Lena, we describe Lena and then find any clip with that timbre.

And because the benchmark reads `lena.wav`, `lena.grave.wav` and
`lena.bored.wav`, picking by the line's stage direction, the same clips carry
**casting and direction at once**. Three clips per major character, one per
minor. Under four minutes of audio for the entire cast.

## The rule I am holding to, unprompted

Clips come only from corpora whose contributors donated their voices **to
build speech technology** — Mozilla Common Voice (CC0) first, LibriTTS as
fallback. Not merely "free to copy": public domain settles copyright and does
not settle consent, and a volunteer who read a novel aloud did not agree to
become a character in a crime game.

**No identifiable public figures.** If a character needs a voice I cannot
source cleanly, I will say so rather than quietly reach for something looser.

---

## THE CAST

Each entry is a brief, not a preference. It says what must come through, so
any clip that carries it is a valid casting — which is what makes this
sourceable at all.

### Principals

**LENA** — bar's bookkeeper, late 30s. Female, mid-low register, dry.
*Unhurried.* She has known this family twenty years and is never surprised by
it. **The thing that must come through: withheld judgement.** She knows more
than she says in every single line, and if the voice sounds like it is
telling you everything, it is the wrong voice. Avoid bright, young, warm.
Moods: neutral, grave, bored.

**ROCCO** — works the door, 50s, night circle. Male, low, worn, slightly
gravelly. Money is always a little short and it is audible. **What must come
through: decency without softness.** He sees everything on this street and
forgets none of it, and he tells you anyway because he likes you. Not a
tough-guy voice — a tired one. Moods: neutral, grave, bored.

**MARA ELLIS** — detective, 40s. Female, level, unhurried, *pleasant.*
**What must come through: that she never has to raise her voice.** The menace
is entirely in how ordinary she sounds. Cast against type: pick the warmest,
most reasonable voice in the shortlist. A cold voice makes her a villain; a
courteous one makes her inevitable. Moods: neutral, grave.

**TOBIAS REESE** — Board of Excise, the audit's face. Male, precise, mid
register, faintly bureaucratic. **What must come through: that this is not
personal.** He is reading from a procedure and the procedure will convict
you. Moods: neutral, grave.

**SERA KEST** — rival head. Female, controlled, harder than Lena, younger
than Mara. **What must come through: someone used to being agreed with.**
Moods: neutral, grave.

### The street — the ones who carry the gossip

**SAM** — walks the block at all hours, trades in being useful. Male,
mid-high, quick, ingratiating, never still. **The fastest talker in the
game.** If something is being said on Hook Street, Sam has heard it, and the
voice should sound like it is already moving on to the next person.

**ADA** — retired schoolteacher, the street's unofficial conscience. Female,
older, clear, precise diction. **What must come through: that she expects to
be listened to**, and is usually right.

**VESNA** — keeps house at the chapel, the quietest well of information.
Female, soft, low volume, careful. **Quiet is the casting.** Everything she
knows arrived through a door left ajar.

**MARLA** — vegetable stall at the market corner. Female, warm, carrying,
market-pitch. Knows every daytime stomach on the street. The loudest woman in
the cast and the most ordinary.

**JOEY** — dock hand, twenty years on the water. Male, big, slow, plain. One
daughter he would burn the port down for. **Simplicity is the casting** — no
irony in the voice at all.

**RITA** — left-handed, owes nobody an explanation. Female, blunt, flat,
short. The one who ends conversations.

**HAL** — carries messages, meetings, prices, peace. Nobody knows his first
name or his last. Male, neutral to the point of being forgettable —
**deliberately the least distinctive voice in the game.** That is his job.

**FATHER EMIL** — male, older, measured, resonant. Used to being heard in a
room that goes quiet for him.

### The rest

Tibor, Ferko, June, Victor, Zlata, Danny Ro, Mitch Sedlak, Aldous Vane, Tony
Brela: assign from the crowd pool with per-character pitch and pace offsets
rather than dedicated clips, until playtest says one of them needs to be
somebody. **Spending a clip on a character nobody remembers is how a cast
becomes a phone book.**

### Crowd

Six anonymous voices — three male, three female, spread across age. The bar
for these is different: they must be *unmemorable*, because a crowd voice you
can recognise stops being a crowd. Pitch-shifted variants multiply six into
enough.

---

## The blocker, stated plainly

**I cannot fetch these.** Common Voice, HuggingFace and OpenSLR are all
blocked from this environment — I checked, it is the same wall that stops me
reaching the CC0 texture sites. Verified, not assumed.

So the sourcing is Jafar's, and my job was to make it one command rather
than an afternoon. **BUILT 2026-07-28: `tools/voice-fetch/`.**

```
python ledger_voice_fetch.py          # streams candidates, opens a page
# ... listen, write picks into picks.txt ...
python ledger_voice_fetch.py --install
```

It builds its own environment, **streams** Common Voice rather than
downloading it (the English tarball is tens of gigabytes and we need three
and a half minutes of it), filters rows on the age and gender each brief
asks for, and lays the candidates out in a page with the brief printed above
the players.

The part that is actually hard, and the part the self-test covers: a Common
Voice sentence is three to six seconds and a clone needs about eleven, so a
candidate is **the same speaker concatenated** — with real silence between
sentences, because butt-joined audio teaches the model a speaker who never
breathes. 22 checks cover the assembly, the loudness match, the resampling
and the cast table, and **none of them touch the network**, which is the
only reason I could verify any of it from here.

**What I could not test: the download itself.** Common Voice, HuggingFace
and OpenSLR are all blocked from this environment — verified, not assumed.
So the fetch path reports per character what it could not find rather than
failing quietly, and there is a `--source libritts` fallback whose rows
carry no age or gender at all (the script says so instead of pretending the
filter worked).

Casting stays mine as delegated; his part is a listening pass, not research.

---
