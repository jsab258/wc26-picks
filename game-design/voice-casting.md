# Voice casting

**Delegated by Jafar 2026-07-28** ("you decide"). Engine is **chatterbox**,
decided on the direction test — see `production-plan-audio-art.md` §1i.

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

## Total to source — REVISED DOWN 2026-07-28, from 37 to 19

The three-clips-per-principal plan was written before the direction test
came back, and it is wrong in a way worth stating rather than quietly
fixing.

**Common Voice contributors read neutral sentences.** A "grave" clip is not
something that corpus contains, so the mood variants were never sourceable
from it in the first place. What the benchmark actually proved is that
**chatterbox's exaggeration control does moods** — Jafar heard it himself on
`same_line_BORED.wav` against `same_line_GRAVE.wav`.

So the reference clip decides **identity** and the exaggeration parameter
decides **direction**. One clip per character.

| | clips |
|---|---|
| 5 principals × 1 | 5 |
| 8 street × 1 | 8 |
| 6 crowd × 1 | 6 |
| **Total** | **19 clips, ~11s each ≈ 3.5 minutes of audio** |

Direction, as parameters rather than recordings:

| Stage direction | exaggeration |
|---|---|
| bored | 0.25 |
| neutral | 0.5 |
| warm | 0.6 |
| grave | 0.7 |
| urgent | 0.85 |

That table lives in `tools/voice-fetch/ledger_voice_fetch.py` so it exists
in exactly one place, and the fetcher writes it into `casting.json` beside
the clips.

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
