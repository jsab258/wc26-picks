# Pending Player Decisions

Standing queue for anything the autonomous build loop cannot decide alone.
Each entry has options and a recommendation so they can be answered in batch.
Answered items move to the decision log in `process.md`.
Standing rule (2026-07-26): every queued decision is ALSO spelled out in chat
as answerable options — the doc is the record, the chat is the interface.

## Open now

*(nothing blocking — the all-night run works on standing mandates. Items
for whenever you surface, in the order I'd want them answered:)*

0. **~~The protagonist has no name.~~ ANSWERED 2026-07-27 — delegated to me.**
   He is **Tomas Vrba**, Marek's sister's boy, off the boat with a suitcase
   and a letter. Vrba sits beside Sedlak, Brela and Farid without sounding
   imported, it is two syllables and hard to soften, and it is a word
   (willow) — the kind of name a city shortens without affection.

   **The part that turned out to be a design decision:** I came to this
   expecting to find-and-replace "the new owner" and that would have been
   wrong. *"The new owner" is not a placeholder — it is what people call
   you before they know you*, and this is a game about being known. So the
   name is something the street LEARNS, and what somebody calls you is now
   a readout of where you stand:

   | | |
   |---|---|
   | the new owner | they know the bar changed hands, not who you are |
   | Vrba | you are a fact on this street now |
   | Tomas | they decided about you, and it was fine |
   | Toma | two or three people, ever |

   Appended to every conversation's scene, so the model uses the right one
   without it being hand-written into thirty character cards. Renaming is
   free and field-by-field — it is data, not a constant — and gender is
   deliberately still unset, since the street mostly uses the surname.

0b. **Day length.** A day is 12 real minutes. Nobody has ever checked
   whether that feels right, because nobody has played it. This is the
   single number most likely to be wrong and the cheapest to change — one
   constant. Judge it in the first session: does the drop window feel like
   an obligation or a countdown, and does the morning arrive too fast to
   act on what you learned last night?

1. **Empire tuning taste check.** This has moved since it was written. With
   the living economy in (M7), aggressive play now nets $94 LESS than
   running no rackets at all, despite $1697 of racket income — because
   squeezing the street makes the street poorer and your bar takes less.
   That is the intended shape ("position over profit", now with a real
   mechanism), but it is a strong reading and only play will say whether it
   reads as a meaningful trade or as futility. RECOMMEND: feel it first;
   `SqueezeCostsProsperity` is the one knob and it is documented.
2. **Playtest when ready** — the latest green LEDGER-Windows artifact is
   the whole game now. A suggested first session (~45 min):
   - Play the week straight: talk to Lena day 1 (the cellar line), meet
     Noor day 2 (she'll bring up the fire), honor Ada's tea (day 3) and
     Rocco's toast (day 5), make your drops in the coat.
   - Day 7: answer Lena's question over the true books. Then press SPACE.
   - In the open city: talk to Sam (sort what he needs, put him on the
     collection round), find Viktor (buy his marker with dirty cash, then
     turn the key), then talk to Ruta once the shop is yours — her line is
     the best money on the street. Press L: THE TWO BOOKS.
   - Watch what the Dockside arm does about it. Try skimming someone's
     envelope for a few days and read their memory file (F1) after.
   - Things to judge: does the week feel like a tutorial or a slog? Does
     day 8 feel like an opening? Is the empire's pace right? Chips useful?

## Will need you at the vertical slice (M5) — ALL DEFERRED as long as possible (player, 2026-07-26)

Player direction: delay purchases/accounts/manual steps as far as they can be
delayed and keep building everything else on procedural/fallback assets. Each
item below now lists its true blocking point — the moment further delay stops
being possible:

1. **Asset budget release** (~$40–60 city pack; Character Creator ~$99/yr
   go/no-go). Blocks: only the final art pass of M5 — layout, lighting,
   systems, story all proceed on AssetLibrary procedural fallbacks (designed
   for exactly this: pack drops in with no code change).
2. **HDRP swap session** (human in the Unity editor). Blocks: final slice
   visuals only; built-in RP remains the working target until then.
3. **ElevenLabs voice** (account, key, casting). Blocks: voiced-slice gate
   only; subtitles-first design (§9) means everything ships text until then.
4. **The is-this-fun gate** — your playtest verdict on the M2–M4 loop (the
   LEDGER-Windows artifact from any green build). Cannot be deferred
   indefinitely: it decides whether M5 polishes this design or we iterate
   the core first. Also watch: drop-window feel (obligation vs countdown).
5. **API-key batch session** for Tier-2 district generation (Open City
   decision 3: generation ships WITH Empire v1/M6). Blocks: M6 kickoff.

## ~~Traffic: can you run people over?~~ ANSWERED 2026-07-27 — the middle option

**Collisions that hurt but do not kill**, as chosen. Built the same morning.

A knock at walking pace is nothing; the top of the arcade speed range is a
broken bone and a very bad morning, and that is the whole range. Nothing in
the code can produce a death, which is a property rather than a tuning
value.

What it costs the player is the interesting part, and none of it is new
machinery — it all lands in systems that already existed:

- The victim is really hurt, on the M11 harm system: it persists, it shows,
  it turns if nobody treats it.
- They remember it in their own words, and lose a lot of loyalty. *"It was
  not on purpose. That is not the same as it being nothing."*
- Everyone nearby holds it as a hard fact at 0.95 confidence — **and this
  is the one thing the coat cannot soften**, because they did not see a
  figure, they saw a car and what it did.
- It records a low-heat exchange rather than a feud. An accident is not a
  war. It is the kind of thing that becomes one if it goes unanswered, and
  that is left to the player.
- Your car stops hard, so you get the beat where you understand what just
  happened instead of leaving it behind at forty.

AI drivers still brake for everybody, always. An NPC car maiming a
pedestrian while the player watches is a consequence with no decision
attached, which is the definition of noise. **Only the player's car can
strike anybody**, because the player is holding the wheel — and that is
exactly the difference between a system and a decision.

## The old writeup, for the record

**Was: no.** Cars brake for anybody in the road and wait there while
they stand in it. That is enforced in Core and held as a test, so it is a
design position rather than something that merely has not been built.

I built it that way and flagged it rather than deciding it, because it is a
real fork and it is yours:

- **Keep it (recommended).** Vehicular death would eat the gossip and
  investigation systems whole — every witness in the district would have
  exactly one thing to talk about for the rest of the campaign, and the
  careful machinery around disguise, confidence decay and hard facts would be
  drowned out by the loudest possible event. It also makes the streets safe
  to walk, which is what makes the crowd usable as ambience.
- **Add it as a consequence system.** Doable, but it is not "turn off the
  brake": it needs manslaughter as a state the world reacts to — a body, a
  crowd, an investigation with a different shape from the ones we have, and
  a rival/police response. That is a milestone, not a flag.
- **Middle option.** Collisions that hurt but do not kill: knocked down,
  gets up, is furious, remembers your car. This sits inside the systems we
  already have — it is a hard fact with a vehicle attached — and costs a
  fraction of the second option.

No action needed before you play. The city works either way.

## Standing rules honored meanwhile

- Design/story/character decisions → this queue, with a recommendation,
  AND spelled out in chat.
- Purchases/keys/accounts → never without you; now also: as late as possible.
- Model/config → unchanged unless you ask.
