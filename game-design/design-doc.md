# LEDGER — Founding Design Document

Working title: **LEDGER** (your two lives are two accounts, and you are always balancing them).
Genre: open-city crime sim × slice-of-life social RPG. Single-player, premium, PC first.
Engine: Unity 6, C#. Status: founding doc v1 (2026-07). Companion file: `research-mechanics.md`.

---

## 1. High concept

You arrive alone in Meridian Bay with one suitcase and a letter: an uncle you barely knew has
died and left you his bar. The bar is real. So is what came with it — a half-dead criminal
outfit: two aging loyalists, a book of uncollectable debts, and a territory the city's three
established organizations have already begun to carve up.

By day you build a life: a job, an apartment, friendships, maybe love. By night you rebuild
the family business. Every person in the city — hundreds of them — is a character with a
schedule, a personality, and a **persistent memory of everything you've said and done**. They
talk to each other. Word spreads. The game is keeping your two lives apart in a city that
never stops comparing notes.

Breaking Bad as a systemic game: the drama isn't scripted — it leaks.

## 2. Why this game (novelty claims)

Claims we make explicitly, so every design decision can be tested against them:

1. **NPCs genuinely remember — forever.** Real conversations (LLM-driven, voiced), with
   persistent per-character memory. Not a dialogue tree in disguise.
2. **The double life is mechanical, not cinematic.** Cover stories only matter if NPCs can
   compare notes. Ours can: information propagates person-to-person through schedule
   intersections. Your girlfriend can catch your alibi from your coworker. No scripted game
   can do this; it is the heart of the game.
3. **Secrets are loot.** What you know about people — and what they know about you — is the
   primary currency and progression system (CK3 hooks × Outer Wilds knowledge-progression).
4. **A living city at honest scale.** Hundreds of schedule-simulated characters (KCD2-proven
   scale), any of whom can be promoted by attention into a full character.
5. **Emergent betrayal.** Your organization is made of individuals with loyalty, fear, and
   grievances. Betrayal is never a cutscene; it is caused, and it is preventable.

If a feature serves none of these, it is cut.

## 3. Design pillars

- **P1 — Two lives, one clock.** Time is the resource the two lives fight over. Every hour
  spent on one is an hour not spent protecting the other.
- **P2 — Information is physical.** Facts exist in NPC memories, move between people, decay
  into rumor, and can be bought, planted, or silenced.
- **P3 — People, not units.** Every recruit, rival, lover, and witness is an individual whose
  relationship to you is personal history, not a meter.
- **P4 — Authored spine, systemic flesh, LLM skin.** The main plot is authored; the world's
  reactions are systemic; the words are generated. Each layer is protected from the others.
- **P5 — Consequences persist.** No quest resets, no memory wipes. The city's state is the
  save file.

## 4. Core loops

### Inner loop (minutes): the encounter
Talk / observe / act. A conversation that yields a secret; a delivery that builds trust; a
lie that plants a false memory. Every encounter writes to somebody's memory file.

### Middle loop (session): the day — Persona-style calendar
A day has time slots (morning / afternoon / evening / night). Obligations (day job shifts,
dates, collections, meets) compete for slots. End-of-day is a natural save/stop point with a
ledger summary: money moved, secrets gained, rumors spreading, loyalty shifts. The two lives
cross-feed Dave-the-Diver style: at work you plan the night; at night you worry about
tomorrow's lunch with her parents.

### Outer loop (campaign): the two ledgers
Grow the empire (territory, rackets, crew) while growing the life (relationships, standing,
comfort). The city squeezes both: rivals move on your territory, loved ones ask harder
questions. Acts advance when the authored spine's pressure points fire (see §8).

### Session hooks
"One more day" comes from: (a) an unresolved thread every evening (the sim guarantees one —
a rumor in flight, a recruit wavering, a date promised), (b) end-of-day ledger dangling
tomorrow's opportunity, (c) rising stakes — the bigger both lives grow, the more each day
can win or lose.
**Design rule — no hard timers** (player decision, 2026-07): nothing in the game expires on
a countdown. Pressure comes from escalation and consequence — rivals react to what you do,
not to a clock. The player sets the pace; the world raises the stakes.
No dark patterns: no dailies, no timers, no FOMO. Retention through curiosity and stakes.

## 5. The cast — three tiers (the Watch Dogs Legion lesson)

- **Tier 1 — Authored core (~14).** Handwritten cards, arcs, and voices. See §9.
- **Tier 2 — Generated middle ring (~150–300).** Full character cards (personality, history,
  job, home, schedule, connections, one secret, one need), AI-generated in batch, then
  hand-touched. Each has mechanical individuality: a unique skill, access, or connection
  (the customs clerk, the pharmacist with debts, the cop's ex-wife) so *who* you recruit or
  befriend matters. Anyone the player invests in can be **promoted**: their card deepens,
  their memory file grows, they join active story systems.
- **Tier 3 — Crowd (~thousands).** Schedule-simulated bodies that make streets alive
  (KCD2-style AI level-of-detail). Talking to one instantiates a Tier-2 card on the spot —
  the city has no "non-characters," only characters nobody has looked at yet.

## 6. The systems

### 6.1 Memory (the foundation)
Per-character memory following the Stanford generative-agents architecture:
- **Memory stream**: timestamped events (conversations, sightings, heard rumors).
- **Retrieval**: relevance × recency × importance scoring picks what enters an LLM call.
- **Reflection**: periodic summarization into stable beliefs ("I trust him", "he was lying
  about the fire") — bounds cost and context, and *beliefs formed from false rumors are the
  gameplay*.
Storage: human-readable markdown per character (debuggable, moddable, versionable).

### 6.2 Information & gossip
Facts are typed objects (who/what/when/certainty/source). When two NPCs' schedules
intersect and their relationship clears a threshold, facts about salient topics (the player,
crimes, romances) can transfer, with mutation: certainty decays, details blur into rumor.
Player-facing: the **Ledger UI** shows what you *believe* the city knows — never ground
truth. Counterplay: silence a witness (many ways, most non-violent), buy a rumor's source,
plant a counter-story, or get ahead of it by confessing.

### 6.3 Secrets, hooks, leverage (CK3-shaped)
Learning a shameful secret grants a **weak hook** (one big favor); a criminal secret grants
a **strong hook** (standing coercion, protection from hostile acts). Hooks work on you too:
what rivals and cops learn about your night life becomes their leverage. The investigation
skill-tree is the player's own mental map of who knows what — knowledge-as-progression.

### 6.4 Suspicion & cover (the double-life core)
Every Tier-1/2 character tracks **suspicion** toward each of your lives. Suspicion rises
from contradictions (caught out of place, alibi conflicts with another NPC's memory,
unexplained money) and falls with maintenance (time spent, consistent stories, staged
evidence). Thresholds trigger behavior: probing questions → checking with others →
confrontation. Crucially: **persuasion outcomes are decided by game state** (relationship,
evidence, plausibility), the LLM performs the scene. Players can't jailbreak an NPC into
believing the unbelievable; NPCs can't be talked out of what they remember seeing.

### 6.5 The empire (bottom-up crime sim)
- **Crew**: recruited individuals from Tier 2, each with loyalty (to you personally), fear,
  ambition, competence, and a breaking point. Loyalty is history: promises kept, cuts paid,
  respect shown, family remembered. Rot is visible early to the attentive.
- **Rackets**: protection, smuggling, gambling, fencing, debt-collection — each a small
  operating loop with staffing choices and exposure profile.
- **Heat**: per-district and per-investigator attention, driven by what witnesses actually
  saw and told. Reduce by laying low, scapegoats, corrupted officials (hooks!).
- **Rivals**: three authored organizations with distinct doctrines (Old-money machine:
  corruption and lawyers; the Dockside syndicate: muscle and smuggling; the New crew:
  tech-forward, flashy, reckless). Their org charts are individuals — flippable, bribable,
  with their own loyalty rot. ⚠ Design note: internal rival hierarchies must be reviewed
  against the Nemesis patent (US10926179B2, active to 2036) — no promotion-by-defeating-
  the-player structures. Rival advancement is driven by their internal politics, not by
  encounters with the player.
- **Combat — melee-first, guns rare** (player decision, 2026-07). Physical, readable
  third-person brawling in the Sleeping Dogs lineage: fists, grapples, improvised objects;
  skill is positioning, timing, and reading opponents. Firearms exist and change everything:
  drawing one escalates a scene, firing one is a city-level event (witnesses, heat spike,
  blood feuds). Presentation is hard-hitting but not gory — impact over blood. Violence
  stays consequence-heavy in the sim: injuries persist, crew members carry trauma, and
  every fight happened in front of somebody who remembers it.

### 6.6 The honest life
A day job (chosen from a few tracks — bar, courier, office) that provides cover, income,
and a social graph. Relationships (friendship and romance) built through real conversation
and remembered shared history, not gift-grinding. The honest life is not a mini-game; it is
the stakes. The people in it are the ones your other life endangers, and the game's best
content — dinner-table scenes where suspicion sits under small talk — lives here.

### 6.7 Economy
Two currencies that resist mixing: clean money (spendable anywhere, slow) and dirty money
(fast, but spending it visibly is evidence — laundering through the bar/rackets is a core
loop). Lifestyle upgrades (apartment, clothes, car) improve both lives but raise "how does
he afford that?" suspicion if income doesn't cover them.

## 7. The city — Meridian Bay

A dense coastal city, one contiguous map, seven districts, each a personality and an
asset-pack-coherent build target:
1. **The Hook** (old port) — your bar, docks, smuggling, the Dockside syndicate.
2. **Copper Row** (immigrant market quarter) — dense street life, cash economies, loyalty.
3. **Downtown** — the day-job world, offices, the machine's lawyers, money laundering.
4. **The Strip** (entertainment) — clubs, gambling, the New crew, information nightlife.
5. **Fairview** (residential hills) — where the honest life aspires to live; quiet money.
6. **Ironside** (industrial) — warehouses, logistics, places without witnesses.
7. **Gullwing** (faded resort waterfront) — off-season melancholy, hideouts, endgame turf.

Districts have local information ecosystems: a rumor can own Copper Row and not exist in
Fairview. Territory control is social (who talks to you, who pays, who warns you) not a
map-painting minigame.

## 8. Narrative

**Structure: authored spine, systemic flesh, LLM skin (P4).**
The spine is fixed pressure points that fire on conditions, not dates alone — the world
state at firing time makes each playthrough's version different.

- **Act I — The Inheritance.** Arrival, the bar, discovering what it really is. Choice of
  posture (wind it down / take it over) that the game then makes hard to keep.
- **Act II — The Squeeze.** Growth attracts the three rivals and one authored investigator,
  Detective **Mara Ossei** — patient, personal, incorruptible-so-far. The two lives begin
  colliding through the gossip system; Act II's set pieces are systemic collisions the spine
  guarantees (someone from each life ends up in a room together).
- **Act III — The Ledger Comes Due.** A triggered crisis forces the books open: the endgame
  matrix is *empire × life* — keep both (hardest, requires the city's information landscape
  actively managed), lose one to save the other, burn both, or the quiet ending: hand the
  empire to a crew member you built up, and see if what you built survives you.

**Core cast (Tier 1, sketch):** Rocco & Lena (the inherited loyalists — old muscle, older
bookkeeper); the three rival heads (Aldous Vane / "the Widow" Sera Kest / Danny Ro); Det.
Mara Ossei; the day-life ring: Sam (first friend, coworker), Ada (landlady, sees
everything), the love-interest options (Noor — journalist, dangerous choice; Elias —
teacher, innocence at stake), June (uncle's estranged daughter, moral mirror), Father Emil
(knows the uncle's real history), and the Fixer (broker between all three rivals, gossip
system personified). ~14 total; full cards to be written next.

## 9. AI architecture (runtime)

- **Dialogue LLM, tiered**: cheap/fast model (Haiku-class) for Tier-2/ambient; stronger
  model (Sonnet-class) for Tier-1 scenes and reflection passes. Provider-agnostic client;
  local-model fallback evaluated later for cost/offline.
- **Guardrails**: player input treated as untrusted; system prompts carry character card +
  retrieved memories + *hard state* (what this NPC knows/can do). Outcome-bearing moments
  (persuade/intimidate/seduce/confess) resolve as game-state checks first; LLM narrates the
  result. Output passes a validator (stays in character, no leaked instructions, length cap).
- **Voice**: TTS per character (cloud API at first; pre-generated banks for ambient barks;
  streaming for live dialogue). Subtitles-first design so voice failures degrade gracefully.
- **Simulation**: schedules + gossip + suspicion run on plain C# (no LLM), tick-based, with
  KCD2-style LOD: full sim near player, statistical sim elsewhere. LLM only fires on
  player engagement and nightly "reflection" batches.
- **Cost envelope** (target): < $0.05 per played hour ambient, spikes during heavy Tier-1
  scenes acceptable. Measured from prototype day one.

## 10. Content pipeline (AI-first)

- **City**: purchased modular city asset packs (HDRP-compatible) + procedural placement
  scripts (block assembly, props, signage, interiors from kits). Manual work: curation
  passes, not modeling.
- **Characters**: base meshes from a character system (evaluate: Character Creator 4
  pipeline vs. Unity asset-store systems) + Mixamo/asset animation libraries; batch
  variation (clothing, body, face) by script.
- **Cards & schedules**: generated in batch by LLM from district/occupation templates,
  validated by script (schedule feasibility, home/job existence), hand-touched on promotion.
- **Rendering**: HDRP, realistic-stylized target ("good indie realism": clean PBR, strong
  lighting/atmosphere over asset density). Fallback to URP only if HDRP perf fails on
  mid hardware.
- **Writing**: authored spine and Tier-1 cards are human+AI collaborative; everything else
  generated-then-curated.

## 11. Milestones

- **M0 — Tech spike (the proof)**: one Unity city block, day/night cycle, player controller,
  3 NPCs with schedules; one full LLM character with card, memory file, reflection, voice,
  and a suspicion value the player can move. *Proves every risky pillar at once.*
- **M1 — The living block**: one district, ~30 schedule-simulated NPCs, gossip propagation
  demonstrably working (plant a fact, watch it travel), Ledger UI v0.
- **M2 — The double life MVP**: day job + one racket + calendar/time slots + clean/dirty
  money + suspicion with confrontations + first-pass melee combat (graybox arena, feel
  before fidelity). First "one more day" playtest.
- **M3 — Vertical slice**: The Hook district polished, 5 Tier-1 characters (Rocco, Lena,
  Sam, one love interest, Ossei), 7 in-game days of Act I, voice throughout. The
  is-this-fun gate and the demo artifact.
- **M4+**: expand districts/cast/acts; combat-adjacent systems decision; performance
  hardening; Steam page.

Scope honesty: M0–M2 are heavily AI-buildable (code, cards, pipelines). M3 is where taste,
iteration, and playtesting (the human's real job) dominate.

## 12. Risks

1. **Simulation jank** (Shadows of Doubt's fate): mitigated by scope discipline — gossip
   and schedules first-class, everything else cut ruthlessly in v1 (no combat, no vehicles
   v1, interiors from kits).
2. **LLM cost/latency drift**: measured from M0; tiering + reflection keep context small.
3. **Slop dialogue**: every conversation must be able to *change state*; card quality bar;
   Tier-1 always hand-polished.
4. **Nemesis patent** (rival hierarchies): design review checkpoint before building rival
   internals (see §6.5).
5. **Scale seduction**: the city wants to grow; the vertical slice is one district and it
   must be great before anything widens.
6. **Player-driven derailment**: authored spine fires on conditions — needs careful design
   so systemic chaos delays but cannot orphan the plot.

## 13. Architecture principle: separability

All narrative/content packs (character cards, scenes, districts, rating-sensitive content)
load as data, cleanly separated from engine/systems code, so the project can be forked or
modded into variant editions without touching the simulation core. Content pipeline and
memory formats are plain text (markdown/JSON) end to end.

---

*Next documents: `cast-tier1.md` (full core-cast cards), `systems-gossip.md` (propagation
spec), `m0-plan.md` (tech-spike build plan for Unity).*
