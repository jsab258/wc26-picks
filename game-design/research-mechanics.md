# Mechanics Research — Retention, Innovation, AI-NPC Best Practices

Research pass for the game concept "8+10" (double-life: honest citizen + criminal boss, big city,
large LLM-driven cast with persistent memory). Date: 2026-07. Feeds into the founding design doc.

---

## 1. LLM-driven NPCs: state of the art (shipped, 2023–2026)

**It works and has shipped.** Key evidence:

- **Suck Up!** (2023) — viral hit where the entire game is talking your way past AI NPCs.
  Proof that conversation-as-core-mechanic is fun when NPCs have *distinct personalities,
  skepticism levels, and a goal the player is working against*. Also shipped a community
  character-card creator — validates our card-based cast generation plan.
- **Mantella** (Skyrim mod, ~500k+ users) — every NPC LLM-driven with voice + memory.
  Latency of 2–6 s per reply is tolerated by players but noticeable. NPCs stay in character
  via lore-constrained prompts (an Imperial can't be talked into loving Stormcloaks).
- **Where Winds Meet** (2025, 2M+ concurrent) — first AAA-scale open world with LLM NPC
  features; players mostly use them to mess around, reception "very positive."
- **AI2U** (2025) — escape-room structure around LLM characters; niche but proven.
- **Stanford "Generative Agents" / Smallville** (2023) — the reference architecture for
  persistent agent memory: **memory stream → retrieval scoring → reflection (periodic
  summarization into higher-level facts)**. 25 agents autonomously organised a party and
  spread invitations through their social network. Our md-file memory plan is exactly this
  pattern; reflection = the summarization step we already planned.

**Known failure modes to design against:**

1. **Latency** — 2–6 s per reply. Mitigate: LLM for dialogue and high-level decisions only;
   plain code for moment-to-moment behavior; streaming text; "thinking" animations.
2. **Slop** — without strong character cards, stakes, and integration with game systems,
   AI dialogue is "pleasant, grammatically correct, completely forgettable."
   Conversations must *do* something mechanical (reveal info, move loyalty, create hooks).
3. **Players jailbreaking NPCs** — roleplay injection, escalation, "ignore your instructions."
   Mitigate: treat player input as untrusted; hard game-state gates on what persuasion can
   achieve (an NPC *cannot* hand over the safe code unless the game systems say the check
   passed — the LLM colors the refusal/agreement, it doesn't decide it).
4. **Loss of authored tension** — if the LLM can resolve anything, plots deflate. Authored
   spine + systemic middle + LLM surface is the right layering.
5. **Cost** — ~100 LLM calls per talky session adds up. Mitigate: cheap model tier for
   ambient NPCs, better model for core cast; LLM calls only on engagement; pre-generated
   ambient voice banks; context kept small via reflection summaries.

## 2. Retention & loop design (premium single-player, no dark patterns)

- **Nested loops** — inner loop (minutes): a conversation, a job, a heist step; middle loop
  (session): the in-game day; outer loop (campaign): empire growth, relationship arcs,
  story acts. Each loop's payoff seeds the next loop's goal.
- **The calendar/day structure (Persona 5)** — a day with limited time slots forces
  opportunity-cost decisions (see the girlfriend, or meet the fence?). Creates natural
  session boundaries and "one more day" pull. Deadline pressure paces the story.
  This maps perfectly onto the double-life concept: *time is the resource the two lives
  compete for.*
- **Dual-loop cross-feeding (Dave the Diver)** — two contrasting loops where each half
  makes you think about the other ("while diving you plan the restaurant; while serving
  you plan the dive"). Directly our structure: while at the day job you plan the racket;
  while running the racket you worry about dinner with your girlfriend's parents.
- **Knowledge as progression (Outer Wilds, Obra Dinn)** — the player's own understanding
  is the progression currency; nothing to grind, everything to learn. For us: *secrets are
  loot.* What you know about people is power (see CK3 hooks below) — and NPC memory files
  make knowledge literally exist in the world.
- **Avoid** F2P-style retention (daily login rewards, timers, FOMO): player-hostile in a
  premium game; retention must come from loop quality and curiosity.

## 3. Social simulation systems

- **NPC schedules (Kingdom Come: Deliverance 1/2)** — full daily routines for ~2,400 NPCs
  via aggressive AI level-of-detail (full sim near player, statistical sim far away).
  Schedules turn the city into a puzzle (learn patterns → plan crimes) and make it feel
  alive. KCD2's GDC talk is the technical reference when we build this.
- **Gossip / information propagation (Shadows of Doubt, CK3)** — NPC-to-NPC information
  spread is shippable and players love it when they can *see* it working. Shadows of Doubt:
  fully simulated city where every citizen has home/job/routine — praised as the best
  "solving a murder" sim ever; main criticism was bugs/jank, i.e. execution risk, not
  concept risk. Lesson: constrain scope, polish the sim.
- **Secrets & leverage (Crusader Kings 3)** — the hooks system: discover a shameful secret →
  weak hook (one favor); criminal secret → strong hook (repeatable coercion, protection
  from hostile action). A clean, proven mechanization of blackmail/favors. **Steal this
  shape** for the crime layer: information → leverage → power, all per-individual.
- **Reputation** — per-individual opinion (CK3, Gothic, Kenshi) feels real; single global
  meters feel gamey. Our gossip network gives us the best version: reputation *is* the
  aggregate of what individuals have heard, and it can be locally wrong (a district that
  hasn't heard the rumor yet).
- **⚠ Nemesis system patent (US10926179B2, Warner Bros)** — active until **Aug 2036**.
  Covers the specific Shadow of Mordor design: procedurally generated enemy hierarchies
  where enemies remember encounters, are promoted/demoted within a faction power
  structure in response to fights with the player, etc. Our systems (individual memory,
  loyalty, gossip, recruitment) are distinct in mechanism and purpose, but when we design
  rival-gang internal hierarchies we must NOT clone the promotion-through-defeating-the-
  player structure. Flag for a design review before building rival-faction internals.

## 4. Cautionary tale: Watch Dogs Legion

"Play as anyone" with thousands of generated NPCs → "care about no one." Generated
characters without authored identity are empty shells; no central protagonist gutted the
story; nothing one operative could do that another couldn't, so switching was pointless.

**Lessons for us (directly addresses our large-cast plan):**
1. Keep a fixed, authored protagonist and an authored core cast (~10–15) with real arcs.
2. Generated characters need *mechanical* individuality (unique skills, connections,
   secrets, leverage) so choosing one over another matters.
3. Generation is a floor, not a ceiling: generated cards should be hand-touched for anyone
   promoted into a story role ("authored polish pass" as content pipeline stage).

## 5. Mechanics shortlist for the design doc (the steal list)

1. **Calendar + time-slot day structure** — the two lives compete for the same hours (Persona 5).
2. **Dual cross-feeding loops** — day life ↔ night empire, each half plans the other (Dave the Diver).
3. **Secrets-as-loot + hooks** — information → weak/strong leverage on individuals (CK3),
   powered by real NPC memory.
4. **Gossip propagation with visible consequences** — schedule-intersection-based spread;
   cover stories that can actually unravel (Shadows of Doubt, upgraded by LLM memory).
5. **Full schedule sim with LOD** — city as learnable puzzle (KCD2 techniques).
6. **Memory stream + retrieval + reflection** per character (Stanford architecture) —
   md files as planned; reflection keeps context/cost bounded.
7. **Suspicion, not alarms** — persuasion/deception gated by game-state checks the LLM
   colors but doesn't decide.
8. **Authored spine / systemic middle / LLM surface** — three-layer narrative so emergent
   drama can't deflate the plot.
9. **Knowledge-as-progression for the investigation half** — the player's map of who knows
   what, who owes whom, is the real skill tree (Outer Wilds principle).
10. **Tiered cast** — authored core, generated-with-polish middle ring, crowd layer;
    promotion pipeline between tiers.

## Sources

- https://massivelyop.com/2025/11/17/where-winds-meet-scores-positive-steam-reviews-and-2m-concurrency-as-players-screw-with-llm-powered-npcs/
- https://wanderfolk.ai/ai-npcs-in-games/
- https://www.totallyhuman.io/blog/the-surprising-new-number-of-genai-games-on-steam
- https://store.steampowered.com/app/2726370/Suck_Up/
- https://tvtropes.org/pmwiki/pmwiki.php/VideoGame/SuckUp
- https://www.nexusmods.com/skyrimspecialedition/mods/98631
- https://www.uploadvr.com/playing-skyrim-vr-with-chatgpt-powering-npc-conversations/
- https://github.com/art-from-the-machine/Mantella
- https://dl.acm.org/doi/fullHtml/10.1145/3586183.3606763 (Generative Agents paper)
- https://www.subodhjena.com/blog/generative-agents-memory-stanford
- https://medium.com/counterarts/the-psychology-behind-persona-5-3ee51e5f82b
- https://greygonegaming.wordpress.com/2017/07/19/in-the-spotlight-the-pacing-of-persona-5/
- https://justingarydesign.substack.com/p/loops-and-tension
- https://tonogameconsultants.com/gameloop/
- https://www.gamesradar.com/games/simulation/shadows-of-doubt-review/
- https://en.wikipedia.org/wiki/Shadows_of_Doubt
- https://patents.google.com/patent/US10926179B2/en
- https://www.gamespot.com/articles/monoliths-shadow-of-mordor-nemesis-system-patent-doesnt-expire-for-another-decade/1100-6529722/
- https://forum.paradoxplaza.com/forum/threads/ck3-dev-diary-5-schemes-secrets-and-hooks.1289167/
- https://ck3.paradoxwikis.com/Hooks
- https://www.avclub.com/dave-the-diver-review-gameplay-loop-roguelike-fish-restaurant-management
- https://www.gamedeveloper.com/design/dave-the-diver
- https://gdcvault.com/play/1027008/Independent-Games-Summit-Sparking-Curiosity
- https://www.gamedeveloper.com/design/live-die-repeat-how-i-outer-wilds-i-piques-curiosity-in-an-ambivalent-solar-system
- https://schedule.gdconf.com/session/supporting-thousands-of-npcs-in-kingdom-come-deliverance-kingdom-come-deliverance-ii/915120
- https://gamerant.com/open-world-games-realistic-daily-routine-simulations/
- https://wolfsgamingblog.com/2020/11/14/watch-dogs-legion-review-play-as-anyone-care-about-no-one/
- https://www.cbr.com/watch-dogs-legion-recruit-play-anyone-holds-game-back/
- https://arxiv.org/html/2505.04806v1 (prompt injection / jailbreak survey)
