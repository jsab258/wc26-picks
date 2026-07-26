# LEDGER — Reconciled Roadmap (v1, 2026-07-25)

The founding doc's milestone list (§11) and our built reality have drifted — mostly
because M1/M2 were re-scoped by player decisions (gossip first, then the week campaign).
This document reconciles the two: what §11 called "M1 living block / M2 double-life MVP"
is partially built; several doc systems were missed along the way and are folded back in
below. This supersedes §11's numbering going forward.

## Where we actually are (vs. the doc)

Built and CI-validated: schedules, day/night, gossip propagation with decay and
contradiction (§6.2 core), suspicion values (§6.4 partial), damage-control verbs with
trait-gated outcomes (§6.4's "game state decides, LLM performs" — honored), the week
campaign (win/lose/economy), 4 conversational NPCs with persistent markdown memory +
reflection (§6.1 fully honored), balance lab, full-week sim in CI.

## Missed items found on doc reread (2026-07-25)

1. **"Never ground truth" violation (§6.2).** The damage-control buttons key off the
   actual rumor network state — the player is omniscient about who holds what. The doc is
   explicit: the player sees what they *believe* the city knows. Fix: a PlayerKnowledge
   model — a lead becomes actionable only once learned (an NPC alludes to it in
   conversation, you witnessed the witness, or a friendly NPC warns you). The Ledger UI
   (v0) renders this belief-state — it is the game's title and was missing from all plans.
2. **Clean/dirty money (§6.7) — missed entirely.** One cash pool today. Night pay must be
   dirty; spending dirty money visibly is evidence; the bar launders (capacity upgradeable
   — this absorbs the earlier "bar investment" M3 idea). Lifestyle purchases raise
   "how does he afford that?" suspicion when clean income doesn't cover them.
3. **Secrets are loot (§6.3, novelty claim #3) — entirely unbuilt.** Everything flows
   one way today (rumors about the player). The player's offensive half — learning NPC
   secrets in conversation, holding hooks, spending them for favors/coercion/protection —
   is a top-5 novelty claim and appears in no milestone. Scheduled M4.
4. **Suspicion thresholds → behavior (§6.4).** Suspicion is a number that colors dialogue;
   the doc requires escalating behavior: probing questions → checking with others →
   confrontation. Scheduled M4 alongside Ossei.
5. **The investigator is already authored (§8).** The "constable at high heat" idea from
   the M3/M4 discussion has a name: **Detective Mara Ossei** — patient, personal,
   incorruptible-so-far. Build her as written.
6. **End-of-day ledger summary (§4).** The Persona-style day anchor (money moved, rumors
   in flight, loyalty shifts, tomorrow's dangling thread) — we have toasts only. Cheap,
   high-impact, M3.
7. **Persistence is a pillar, not polish (P5).** "The city's state is the save file."
   Today rumors/campaign state don't survive a restart while NPC memories do — an
   inconsistent world. Promoted from "M8 hardening" to M4.
8. **Cost envelope telemetry (§9).** Target < $0.05/hour ambient, "measured from day
   one." CostTracker exists but no per-hour readout. Small M3 task (F1 + sim report).
9. **Output validator (§9).** Character-break/length/leak checks on LLM output — M5.
10. **No-hard-timers rule (§4) vs. drop windows.** The nightly 22:00–02:00 job window is
    defensible as a *scheduled obligation* (the doc's middle loop is built on those), not
    a FOMO countdown — but it's the closest thing we have to a timer. Watch it in
    playtest; if it feels like a countdown, soften (the outfit waits, but patience decays
    per hour late).

## Open items needing a player decision (flagged, not blocking)

- **Cast drift vs. doc.** Doc: Sam = first friend/coworker (day-life ring); Ada =
  landlady. Ours (approved cards): Sam = street go-between, Ada = retired teacher.
  Recommendation: keep our approved cards — they fit the one-street scale — and re-home
  the doc's "first friend" role in a future coworker when the day job exists. The doc's
  §8 cast list gets revised at vertical-slice time.
- **Melee combat.** Doc §11-M2 wanted a graybox melee pass; doc risk #1 says "no combat
  v1." Recommendation: stay combat-free until after the vertical slice; revisit with the
  Sleeping-Dogs-lineage spec (§6.5) as its own milestone if the game needs it.

## The plan forward

- **M3 — The honest ledger** (next; starts after the PC playtest + tuning):
  1. PlayerKnowledge + Ledger UI v0 — belief-state, never ground truth; damage-control
     verbs re-keyed to it. The playtest build's omniscient buttons become "learned leads."
  2. Clean/dirty money + laundering through the bar (absorbs bar investment).
  3. Disguise/appearance v0 — day/night clothing state feeding witness confidence.
  4. End-of-day ledger summary screen.
  5. Schedule-conflict story beats (a day-world invitation colliding with a drop window).
  6. Consequential loyalty (visible, affects warnings: a loyal NPC tells you what they
     heard before it spreads — which also feeds PlayerKnowledge naturally).
  7. Cost-per-hour telemetry surfaced.
- **M4 — The other side of the street — COMPLETE 2026-07-26**: hooks v1, suspicion
  escalation ladder, Det. Ossei (+witness interviews), save/load — PLUS the audit
  adopt-soon set: recognition barks, eavesdropping channel, debt book, response
  validator. Next stop M5 requires the player: playtest gate, purchases, HDRP, voice,
  Noor approval (drafted). Autonomous pre-M5 runway: balance-lab expansion, Tier-2
  sample ring, onboarding pass, AI-playtest hardening.
- **M5 — Vertical slice** (doc M3): The Hook polished (HDRP swap, city pack, character
  models/Mixamo, audio+voice via ElevenLabs), 5 Tier-1 characters (Rocco, Lena, Sam, one
  love interest — Noor or Elias, player's pick — and Ossei), 7 in-game days of Act I,
  output validator, onboarding. The is-this-fun gate and the demo artifact.
- **M6 — The Open City (Empire v1) — CORE SHIPPED 2026-07-26** (approved same
  day, built during the 24h autonomous run): open mode from day 8 with
  scarring Falls, businesses (clean/debt/hook routes), crew (need/hook),
  collection + protection rackets through the real mill, the observing
  Dockside rival, district geometry for the full HookMap, 14 generated
  residents walking (22 NPCs), balance-lab-proven no-death-spiral economy.
  See `empire-roster.md` + `balance-findings-open.md`. Remaining M6 flesh:
  ring-card promotions (Ferko/Ruta/Vesna/Tibor), more batch walkers +
  businesses, deliberate outfit-independence path, Act II authoring on top.
- **M7+ — per doc §11 M4+**: further districts/cast/acts expansion, LLM
  productization (bundled inference, cost model, offline fallback), hardening,
  Steam page. Nemesis-patent design review before any rival-hierarchy work (§6.5 ⚠).

## NEW DIRECTION — the agency model (player, 2026-07-26)

`agency-model.md` now sets the depth target for every dimension of the
game, benchmarked outside-in against GTA5 / RDR2 / KCD2 / BG3 / Hitman /
Sims / CK3 rather than inside-out from our codebase. It raises economy,
violence and traversal well above the earlier plan, adds six dimensions
that the inside-out view had missed entirely, and settles phones as
canon. Everything below is re-sequenced against it.

**The three raises:** economy to full district simulation (85), violence
staged to melee-then-guns (70 end state), traversal by breadth of place
(65). **The additions:** operation planning (75 — the biggest hole found),
multiple-solutions-per-obstacle as a project law (80), access as soft keys
(65), communication at distance (60), companionship (55), home that reacts
(50). **Unchanged refusals:** body needs, vehicle simulation, minigames,
gear treadmills.

### Approval state (2026-07-26)

All eight outside-in dimensions APPROVED, plus vehicles/driving approved
for the late roadmap. Approved-and-specced, buildable without further
input: Act II (four questions answered), Tier-1 batch 2 cards, operation
planning, access soft keys, companionship, home-that-reacts, multiple
solutions as law. Approved but needing a design decision before build:
visible odds (style), interiority (shape for an authored protagonist),
competence (what unlocks), phones (setting era). Approved but deliberately
sequenced late: economy at depth (wants the first playtest), staged
violence beyond the consequence layer (wants art), vehicles.

### Re-sequenced plan

- **M5 — Vertical slice** stays next and stays the gate. Nothing below is
  worth building on a loop no human has played for one minute.
- **M6 — The Open City**: core shipped; remaining flesh unchanged, plus
  the faction-agency Core already landed (arms are rosters of real people;
  poaching is the existing recruit verbs aimed at someone with an
  employer; pledge/break allegiance with standing and tribute).
- **M7 — Operation planning + access.** The two highest-value additions
  from the outside-in pass, both cheap in the way that matters (decisions,
  not animation): plan a job (approach / crew / hour / gear) and execute
  it against the live witness system; soft-key access gating rooms and
  people by standing, notoriety, dress, and introductions.
- **M8 — The living economy.** District-scale simulation with legibility
  as the hard requirement: costs, suppliers, customers, wages, prices —
  every number surfaced as a person's circumstance. Balance lab gates it
  against inflation/collapse before it ships.
- **M9 — Phones + the distance layer.** A second information channel with
  its own reach and fidelity, plus the counterplay it invites (messages
  left with people, wiretaps, being reachable at the wrong moment).
- **M10 — Violence, staged.** Consequence layer can land earlier and
  cheaply (injuries, hospital, feuds); playable melee is its own milestone
  after the slice's art pass; firearms last, when the city can react.
- **Ongoing across all of the above**: districts by generation (traversal
  breadth), companionship, home-that-reacts, legacy/succession into Act
  III, notoriety, family, vice.

## RE-SEQUENCED — the first-principles pass (player, 2026-07-26)

The player asked whether this is the game we would build from first
principles given the tools we actually have. Three gaps came out of that
(full argument in design doc §17); the player's instruction was **"router
first, economy after — close the gaps you found by planning/reordering
properly and then building."** This section supersedes the M7–M10 ordering
directly above it. Pillar P4 is rewritten in the design doc to match:
*authored anchors, simulated bones, LLM director and interface.*

The gaps, in the order they are now being closed:

1. **The verb space is hand-enumerated.** Every mechanical action the
   player can take had to be authored *and given a button*. That is how a
   game is built when there is no model in the loop. With one, the verb
   space can be open while the verb implementation stays closed.
2. **The story is hand-authored where it should be directed.** Authored
   beats fire on state, which is good, but they are finite and were all
   written before the player's city existed.
3. **The population is 36.** Not a constraint — a decision we never
   revisited after proving generation works (60 cards, 19 calls, ~92k
   tokens).

### The new order

- **M6.5 — The intent router — SHIPPED 2026-07-26.** `IntentRouter` +
  `Adjudicator` in Core, `IntentBridge` in the game layer, 55 new
  CoreTests (394 total) and an 11-check SimHarness scenario (57 total)
  with a live-mode half that asks a real model to route real phrasings.
  The catalogue is read off the ACTUAL BUTTONS — a verb is offered to the
  router if and only if its button is on screen and clickable — so drift
  between what a player can click and what they can say is structurally
  impossible, and typing a verb runs the identical handler clicking it
  does. Spec as designed and built:
  The player types anything; a fast model classifies it against the verbs
  genuinely available in that exact moment and returns a mechanical verb
  with arguments, a novel action adjudicated by a state check, or pure
  narrative that falls through to the conversation engine as today.
  **Classification, not adjudication** — the returned verb must be a member
  of a closed set built from live state, anything else is rejected and
  downgraded to speech, and outcomes are still computed by the same
  deterministic C# the buttons call. Chosen first because it is *purely
  additive*: every existing button keeps working unchanged, and text that
  routes to nothing behaves exactly as it does today. A lexical fast path
  handles unambiguous phrasings for free and is the full fallback when no
  model is available. Novel actions get a closed requirement vocabulary
  (cash / dirty cash / standing / hook / crew / hour / heat) and a closed
  effect vocabulary with clamped magnitudes, so they are small and real
  instead of large and fake.
- **M7 — The living economy — SHIPPED 2026-07-26.** `Economy` +
  `EconomySetup` + `SupplierCast` in Core/Game, 31 new CoreTests (425
  total), a new `economyOk` gate in the in-engine CI sim, and a 900-campaign
  balance-lab pass (`balance-findings-economy.md`).

  **The loop:** squeezing the street makes the street poorer, and a poorer
  street spends less in your bar — so the racket that pays dirty money at
  night quietly costs clean money in the morning. The lab confirms it is a
  genuine trade rather than a tax: aggressive play earns $1697 in racket
  income over three weeks and ends **$94 down** on a campaign that ran no
  rackets at all. No dominant strategy, which is why this was worth
  building instead of adding another income line.

  **Legibility was the hard requirement and it held.** Nothing surfaces as
  a percentage — asserted in the tests, not just intended. Prices rising is
  Mirek asking for more and not explaining the difference. A poorer street
  is two regulars drinking at home.

  **Suppliers are people, not rows.** Mirek the drayman and Anton the
  wholesaler walk the district on their own rounds, carry the economy's
  state in their own words through `ExtraContext`, and can be settled with
  — a verb the intent router picked up for free the moment its button
  existed. Anton is the man Mirela's recruitment need has referred to since
  the roster was written; he now exists.

  **Neglect loses a supplier; a poor neighbourhood only makes him dearer.**
  The first build lost one in 100% of aggressive campaigns, which is a
  scripted event wearing a simulation's clothes. Retuned so paying on time
  outweighs the worst drift the street can apply.

  Safe to ship under a game about to be played: an unsqueezed campaign sits
  at a takings factor of ~0.98, i.e. unchanged.
- **M7.5 — Operation planning + access** (was M7). Still high value, still
  cheap; the router makes planning *say-able* rather than menu-only, so it
  benefits from being built after it.
- **M8 — The Director.** A nightly world-level LLM pass that reads actual
  state and authors the next pressure from it, built from existing
  primitives only (inject a fact, change a schedule, make a demand,
  arrange a meeting) and validated against what those primitives permit.
  Authored anchors still fire; the Director fills the space between them,
  which today is empty.
- **M9 — Population scale.** Thousands, via generation plus level-of-detail
  simulation (full fidelity near the player's attention, statistical
  elsewhere — the KCD2 approach, and the same work as production item P5).
- **M10 — Phones + the distance layer** (was M9). Unchanged.
- **M11 — Violence, staged** (was M10). Unchanged.
- **M12 — Vehicles.** Approved for the late roadmap; unchanged.

**LLM cost:** deferred by the player, explicitly not a build-time blocker.
If we publish, the pricing models to weigh are subscription, pay-as-you-go,
cheap purchase plus a local model, or a dedicated server. `ILlmClient` is a
one-method interface precisely so none of these is a rewrite, and
`CostTracker` keeps the decision anchored to real measured numbers. See
design doc §16.1.

### PRODUCTION TRACK — added 2026-07-26 (player: "these all need to go on
### the roadmap and be built too"). Target: high-quality indie.

The design doc tracked mechanics only; these are the things that turn a
systems prototype into a product. They run in PARALLEL with the design
milestones rather than after them, because several get harder the longer
they are deferred (save versioning especially).

- **P1 — Front end** (tonight): main menu, new game / continue, options
  (audio / video / gameplay), key rebinding, pause menu, quit. The game
  currently boots straight into play and cannot be exited cleanly.
- **P2 — Save robustness** (tonight): a version field with migration,
  multiple slots, corruption recovery. Today: one autosave, no version —
  and every patch silently risks players' saves.
- **P3 — Audio** (tonight, procedural first): music, ambience, footsteps,
  doors, UI feedback, mixer. The game is silent. Procedural/synthesised
  sources first via the AssetLibrary pattern, so purchased or recorded
  audio drops in later with no code change — exactly how textures work.
- **P4 — Accessibility**: subtitle sizing, colourblind-safe palette,
  remappable input, text scaling. The no-hard-timers rule already helps.
- **P5 — Performance**: KCD2-style LOD and statistical simulation for
  distant districts (doc §9, unimplemented), draw-call/memory budgets.
- **P6 — Controller + Steam Deck.**
- **P7 — Localisation**: externalise UI and authored strings. Generated
  dialogue can be produced directly in the target language — an advantage.
- **P8 — Platform**: Steam page, achievements, cloud saves, release build
  pipeline.
- **P9 — QA matrix**: human test plan layered on the automated harness.
- **P10 — LLM productization** (see doc §16): inference economics
  decision, content safety and red-teaming, age-rating strategy. The
  highest-risk item in the entire project and the one needing you earliest.

Rule reaffirmed from §2: if a feature serves none of the five novelty claims, it is cut.
