# What else we missed about speech — audit, 2026-07-30

> **STATUS — LOG, 2026-07-30. NOT CURRENT.** A record of what was true on the
> day, kept because the reasoning is worth having. **Do not read it as the
> present state** — for that, `roadmap.md`. Items called "open" here have
> very likely been closed since.

> *"pretty big oversight not to think about accents until now. what else in the
> world of speech/voices did we miss?"*

Fair. Accent was not an oversight of detail, it was a **decision nobody made**,
which meant a filter list made it. So this audit looks for the same shape:
things about voice that are currently being decided by default.

Checked against the repo rather than recalled. What follows is what is
genuinely absent, ranked by what it costs to find out late.

---

## Already handled — not gaps

- **Runtime vs pre-generated split**, with a per-hour cost estimate and an open
  decision. `production-plan-audio-art.md` §1.
- **Subtitles-first**, so voice failures degrade to text. design-doc §9, m0-plan.
- **One engine**, Kokoro dropped deliberately. `decisions-pending.md`.
- **Consent rule** for source corpora, held through three corpus changes.

---

## STATUS, 2026-07-30 night

| # | Gap | State |
|---|---|---|
| 1 | Barks are not sounds | **DONE** — `Perception.LoudConversation/LoudRemark`, routed through `SpeechBubble.Say` |
| 2 | The telephone sounds like the room | **DONE** — `Acoustics` 300–3400 band, four line kinds, `CanPlaceTheVoice`, `Bleed`; `Audio.OpenLine` |
| 3 | Non-verbal voice | **NEEDS JAFAR** — a purchase; see `decisions-pending.md` |
| 4 | Deaf players get nothing | **DONE** — `Core/Captions` + `CaptionBar`, gated in the sim |
| 5 | Same character, same voice next week | **DONE** — `VoiceBank` naming + seed, mirrored in Python and pinned by shared vectors |
| 6 | Voices do not change with state | open, after the above |
| 7 | No voice bus | **DONE** — Voice source, own fader, distance filter |
| 8 | Lip sync | deferred **in writing**, which was the ask |

Two things surfaced while closing these that were not in the original eight,
and both are worse than most of what was:

**The crowd pool is six voices.** Not a number anybody chose for the street
— it is how many "crowd" entries the casting sheet happens to fund. Six is
thin: the ear picks a repeat out of a busy street inside a minute. The fix
is casting, not code.

**The casting sheet and the game roster do not use the same names.** The
sheet has `kest`, `vesna`, `marla`; the game's gossipers include `sera`,
`aldous`, `danny`, `halvard`, `june`, `zlata`. Some are one person under two
names and some are people nobody has cast. Unknown ids fall through to a
crowd voice rather than throwing, so the symptom is a named character
quietly sounding like a passer-by rather than a crash. **This is a casting
task somebody has to actually sit down and do.**

---

## 1. Barks are not sounds *(cheapest to fix now, worst to fix later)*

`Perceivers.cs` and `NpcWalker.cs` contain no reference to barks at all. The
perception layer built today models loudness, ambient masking, occlusion and
audible radius — and **a person shouting is not routed through any of it.**

So right now: a bark cannot be overheard by a third party, cannot mask the
player's own noise, does not carry further at 3am than at noon, and cannot be
the thing that draws a constable. Every one of those is already built and
tested; the wire is simply missing.

`Notice.Noise` and `Reaction.LoudnessOf` exist. Alarm is already the only loud
reaction. This is a connection, not a system.

**Cost of lateness:** Phase 2 wires reaction and Phase 3 wires violence. Both
will assume the voice channel behaves like every other sound, and it does not.

## 2. The telephone sounds like the room

The phone is not decoration — it is *"the second channel"*, a core mechanic
with its own milestone (M10). And there is **no telephone audio treatment
anywhere in the project**: no band-limiting, no handset colouration, no
line noise.

A voice on the phone that is pixel-identical to the same voice in the room
throws away the mechanic's whole identity. This is one filter and a bus, and
it is the single cheapest large win in the audio layer.

## 3. Non-verbal voice does not come from a text-to-speech engine

Grunts, pain, exertion, the intake of breath before a swing, the sound
somebody makes when they are hit. **A cloner turns text into speech; it does
not produce any of these**, and no amount of prompting gets them out of it.

Combat Phase 3 is unplayable without them — a fight where nobody makes a
sound reads as a puppet show. This needs a *different source* than the voice
pipeline: either a foley library, or recorded human effort sounds, or a
generative audio model. **It has lead time, which is why it is here and not
in a Phase 3 ticket.**

## 4. The perception design leans on voice, and deaf players get nothing

`weapons-spec.md` §6.2 has four redundant channels telling you that you have
been noticed. **Two of them are voice** — the remark, and the crowd going
quiet. Subtitles-first covers *what was said*; it does not cover *the street
went silent*, which is a sound with no words in it.

This is the sharpest one, because it is a hole in a design I spent today
building and calling redundant. Redundancy that collapses to two channels for
a deaf player is not redundancy.

## 5. The same character must sound the same next week

Nothing specifies determinism. A cloner given the same reference and the same
line can produce different takes; if the bark bank is ever regenerated,
characters drift. Seed, cache, and a hash of (reference, text, parameters)
belong in the generator before there is a bank worth keeping.

## 6. Voices do not change with state

The game models injury, scars, drinking, exhaustion and running. A voice that
sounds identical while winded, drunk, or three days after a beating is a
missed opportunity in a game whose whole subject is consequence. Chatterbox's
exaggeration control gets some of this; breath and strain do not.

## 7. No voice bus

`Audio.cs` has ducking for overheard conversation and a music bus, and **no
dedicated speech channel**. Speech needs its own level, its own ducking of
music and ambience, and a distance attenuation curve that is not the one used
for footsteps.

## 8. Lip sync — deferred, but it should be a written deferral

No visemes anywhere. Correct for Tier 1 boxes and fine for X Bot and Y Bot,
who have no faces. **It stops being fine the moment Tier 2 characters arrive**,
and the honest options then are: keep the camera off faces during speech, buy
a viseme solution, or accept moving-mouthless talking heads. Written down so
it is a choice later rather than a surprise.

---

## And one that is a decision, not work

**Cloning a donor's voice is a step beyond training on it.** The rule I have
held is that clips come only from corpora whose contributors donated their
voices to build speech technology. Cloning is arguably within that; it is also
arguably not what a Common Voice contributor pictured. Nobody is identifiable
in the output, and no public figures are used — but the honest position is
that this is *your* call to make explicitly rather than mine to keep assuming.

---

## Recommended order

1. **Barks into the hearing model** — hours, and it gets more expensive every
   phase.
2. **Telephone treatment** — hours, and the mechanic needs it.
3. **Deaf-player channel** for "you have been noticed" — design work, and it
   belongs in the spec I just wrote rather than bolted on later.
4. **Determinism** — before any bank is generated.
5. **Non-verbal sourcing decision** — has lead time; needed for Phase 3.
6. Voice bus, state-modified voice, lip-sync deferral — after the above.
