# Production plan — voice, characters, art direction, feel, budget

**Status: PROPOSAL for Jafar, 2026-07-28.** Answers his six questions after
the M15 playtest. Nothing here has been bought or started. Prices are
estimates from what I know and **must be re-checked at purchase time** —
treat them as order-of-magnitude, not quotes.

---

## 1. Voice / TTS — the questions I need answered first

He is right that this is the whole ballgame: *"we are letting AI do what
KCD2/GTA5 used voice actors for, it can't sound obviously AI."* Before I
write a line of integration code, six things decide the entire approach.

### 1a. The finding that changes the architecture

**Most of our speech does not need to be generated at runtime.** Split it:

| Channel | Volume | Runtime? | Implication |
|---|---|---|---|
| Ambient life, barks, recognition, refusals | Large but FINITE | No | Pre-generate offline, ship as audio assets, zero runtime cost |
| Named-cast free dialogue (LLM) | Unbounded | Yes | Streaming TTS, per-hour cost, latency matters |

That split is the difference between a viable product and an unshippable
one, because of this:

**Rough runtime cost per hour of play, cast dialogue only** — assume 20
conversations/hour, ~6 replies each, ~25 words ≈ 900 characters, so ~18k
characters/hour:

- Premium emotional TTS (ElevenLabs-class, ~$0.15–0.30 / 1k chars):
  **~$3–5 per hour of play.** Unshippable as a paid product; fine for our
  own playtesting.
- Commodity TTS (OpenAI-class, ~$0.015 / 1k chars): **~$0.25/hour.**
  Viable, but this is also the tier that sounds most obviously synthetic.
- **Local model on the player's GPU (XTTS/F5/Kokoro-class): $0/hour**, no
  API dependency, works offline — at the cost of install size, a GPU
  requirement, and quality that needs testing.

**Therefore the recommended shape:** premium voices for the ten named cast
members (low volume, highest quality bar, much of it pre-generatable), and
either commodity-cheap or local for everything else. Ambient barks get the
premium treatment ONCE, offline, because they are finite.

### 1b. What actually makes TTS sound "obviously AI"

Not the timbre — modern models are fine there. The tells are:
- **Flat affect and uniform pacing.** Every line the same energy.
- **Wrong emphasis** on the semantically loaded word.
- **No breath, no hesitation, no overlap.** Real speech has friction.
- **Wrong reading of ambiguity** — "That's *your* problem" vs "That's your
  *problem*."
- **Emotional monotony across context** — the same delivery whether the
  character is frightened or bored.

Mitigations that actually work: models with explicit style/emotion control;
per-line direction (we know the speaker's suspicion, loyalty, and stance —
we can pass "wary, lowered voice" as a style tag from real game state);
generating 2–3 takes and keeping the best; and deliberate imperfection
(room tone, breath, occasional stumble).

**We have an unfair advantage here:** the game already computes the
emotional state behind every line. Most TTS work is done blind; ours can be
directed from the simulation.

### 1c. THE QUESTIONS I NEED ANSWERED

1. **Setting and accent.** The names are Slavic (Zlatko, Vesna, Rita,
   Joey) but the writing is English. Is this a fictional Eastern European
   port, an émigré quarter in an English-speaking city, or somewhere
   unnamed? **This matters more than the model choice** — non-native
   accents are the single thing current TTS does least convincingly. If
   the answer is "everyone has a Slavic accent in English", the quality bar
   gets much harder to clear and I would push back toward "unnamed city,
   neutral voices with regional character in the WRITING rather than the
   accent."
2. **Era.** Cars, telephones, ledgers, no computers — I have been writing
   toward interwar/post-war. Confirm, because it drives voice casting,
   music, and every art decision below.
3. **Shipping model.** Personal project / demo / actual commercial release?
   This decides whether $3/hour runtime cost is acceptable.
4. **Player-supplied keys?** The game already asks for an Anthropic key.
   Is "bring your own TTS key" acceptable, or must it work out of the box?
5. **Full voice or partial?** Fully voiced cast + ambient? Or the KCD2-lite
   approach — cast voiced, crowd barks voiced, long-tail dialogue text?
6. **Local model acceptable?** Adds GPU requirement and ~1–3GB install, in
   exchange for zero runtime cost and offline play.

---

## 2. Character models + animation — "ok, how?"

Four routes, with my recommendation.

| Route | What | Cost | Verdict |
|---|---|---|---|
| **A. Modular stylised** (Synty-class) | Mix-and-match heads/bodies/clothes, low-poly, distinctive | ~$50–200 | **RECOMMENDED** if art direction is stylised |
| **B. Character Creator 4 pipeline** | Reallusion CC4 generates unlimited realistic humans, auto-rigged, Unity export | ~$300–600 | Best if realism-lite; heavier pipeline |
| **C. MetaHuman** | Epic, photoreal, free | $0 | **Effectively out** — Unreal-first, Unity path is painful and licence-restricted |
| **D. Commission bespoke** | An artist makes our cast | $2–10k+ | Later, for the ten named cast only, if the project proves itself |

**Animation is separate from models and is where the feel lives:**
- **Mixamo** — free mocap library (idle, walk, run, talk, gesture, sit).
  Good enough for everything except the cast's key scenes.
- **Unity Animation Rigging package** — free, and this is the one that
  matters: **look-at IK** makes the gaze system I just built actually
  read. Without it, "they turn to watch you" is a rotating capsule.
- **A locomotion controller** with proper blend trees (~$50–100 on the
  asset store, or hand-built) — no snapping between idle/walk/run.
- **Occupation loops** — the market seller actually selling. This is what
  KCD2 does that reads as "alive," and it's animation work, not AI work.

**Recommended stack: modular stylised characters + Mixamo + Animation
Rigging (look-at) + a blend-tree locomotion controller.** Roughly $150–300
and a lot of my integration time.

---

## 3. Barks at quality

**Not runtime generation. Offline generation into a curated bank.**

Pipeline:
1. Enumerate the real situations the simulation produces (rumour of kind X
   at confidence Y told by archetype Z; refusal; recognition; ambient
   topic per economic state).
2. Generate many candidates per situation with the LLM, given the
   character archetype and emotional state as direction.
3. **Curate.** A human pass keeping the good ones — this is the step that
   separates "AI slop" from writing, and it is not optional.
4. Voice the survivors with the premium model, offline.
5. Ship as audio + text. Zero runtime cost, unlimited quality headroom.

Target: **~2,000–5,000 lines**, versus the ~40 hand-written templates in
today's build (which will start repeating within minutes — that is a real
defect in what I shipped this morning, and this is its fix).

---

## 4. Art direction — elaborate and suggest

### The strategic frame
Competing with KCD2 on realism is a losing game: they have an art army and
we do not, and realism is the one lane where a small budget guarantees we
look cheap. Disco Elysium, Pentiment and Obra Dinn are deeply immersive on
small budgets because their style is coherent, distinctive, and
*achievable*.

### Four candidates

**A. STYLISED NOIR — RECOMMENDED.**
Period-plausible forms, heavily restricted palette, strong directional
light. Faces simplified but expressive; silhouette-first design (hats,
coats, distinctive shapes) so characters read at distance — which is
exactly what the gaze/stance system needs.
- Palette: desaturated blue-greys and wet stone, punctured by warm sodium
  pools from streetlamps and bar windows.
- **Weather and fog do the heavy lifting.** Volumetric fog, rain, steam
  from gratings: they cut draw distance (a performance win), hide
  low-detail geometry (a budget win), and create mood (an art win). This
  is the single highest-leverage art decision available to us.
- Post: film grain, vignette, slight bloom on light sources.
- Reference: the street level of *Blade Runner*, the palette of *Road to
  Perdition*, the character read of *Disco Elysium*.
- **Why it fits THIS game:** it is a game about perception, rumour and
  what people think they saw. A subjective, high-contrast, half-obscured
  world is thematically correct, not just cheap.

**B. Interwar realism-lite.** Period-accurate, simplified materials.
Honest but lands in the uncanny valley and costs the most. Not recommended.

**C. Hard graphic / extreme stylisation** (1-bit, heavy dither, à la Obra
Dinn). Cheapest and most distinctive, but fights the game's need for
readable faces and subtle social signals. Not recommended, though a
striking option if budget collapses.

**D. Diorama / tilt-shift.** Wrong — it distances the player, and this game
needs intimacy.

### If A is chosen, the concrete first pass
1. Lighting and fog rebuild (free, biggest single visual gain).
2. Wet-surface materials + reflections (cheap, high production value).
3. Rain and its audio (cheap, transformative).
4. Restricted palette enforced across every existing material.
5. Modular period building/prop packs consistent with the palette.

---

## 5. Game feel — what I mean

The moment-to-moment tactile response. The difference between a character
who *moves* and one who *teleports smoothly*. Concretely, what LEDGER lacks:

- **Movement weight** — acceleration and deceleration curves rather than
  instant velocity; a turn that takes a moment.
- **Animation blending** — no snapping between idle/walk/run.
- **Camera craft** — subtle sway, slight positional lag, FOV widening when
  running, a small settle when you stop.
- **Footsteps by surface** — stone, wood, gravel, puddle, with variation
  so it never sounds looped.
- **Interaction feedback** — a door that has a handle sound, an animation,
  and a tiny camera nudge; money that has a weight to it.
- **Breath and effort** when running; a different gait when hurt (we
  already model injury — it should be visible in the walk).
- **Continuous time-of-day** light transitions rather than steps.
- **UI sound** with a consistent material identity.

None of it is expensive. All of it is what people mean when they say a game
feels "finished" versus "a prototype."

---

## 6. Budget estimate

**Upfront, one-time (asset purchases):**

| Item | Low | High | Note |
|---|---|---|---|
| Characters (modular stylised) | $50 | $200 | Route A |
| — or Character Creator 4 pipeline | $300 | $600 | Route B instead |
| Locomotion controller | $0 | $100 | Hand-buildable |
| Animations (Mixamo) | $0 | $0 | Free |
| Environment: buildings/props packs | $150 | $700 | Period-consistent |
| Audio: ambience + SFX libraries | $50 | $300 | |
| Bark voice generation (one-time, ~3k lines) | $30 | $120 | ~180k chars |
| **Upfront total (Route A)** | **~$280** | **~$1,420** | |
| **Upfront total (Route B)** | **~$530** | **~$1,820** | |

**Recurring, per hour of play:**

| Item | Cost/hour | Note |
|---|---|---|
| LLM dialogue | <$0.05 | existing target, already measured by CostTracker |
| TTS — premium streaming | $3–5 | **unshippable commercially** |
| TTS — commodity streaming | ~$0.25 | viable |
| TTS — local model | $0 | + GPU requirement, install size |

**Optional / later:**
- Bespoke character art for the ten named cast: $2,000–10,000+
- Original music: $0 (we have procedural) to $2,000+
- Professional sound design pass: $1,000+

**Headline: roughly $300–1,500 gets us models, animation, environment art,
audio libraries and a fully voiced bark bank.** The recurring TTS cost for
live dialogue is the real strategic decision, and it points hard at a local
model or a tiered approach.

**The honest caveat:** buying assets does not make a game look coherent.
Art direction and integration do, and that is my time, not money. The
budget above is the cheap half of the problem.

---

## 7. What I need from Jafar to proceed

1. **Answers to the six voice questions in §1c** — especially setting/accent
   and shipping model.
2. **Art direction: confirm A (stylised noir) or pick another.**
3. **A budget ceiling**, so I can spec exact products rather than ranges.
4. **Character route A or B** (follows from art direction).

With those four, I can produce a specific shopping list with named products
and current prices for approval, and start on the free work immediately —
lighting/fog/palette, game feel, look-at rigging, and the offline bark
generation pipeline, none of which need a purchase.
