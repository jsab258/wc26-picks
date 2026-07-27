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
- **M7.5 — Operation planning + access — CORE SHIPPED 2026-07-26, WIRING
  PENDING.** Both landed as Core with full test coverage (`Access.cs` +32
  tests, `Operation.cs` +48 tests, 584 total) and **neither is reachable
  from the game yet.**

  That was a deliberate call rather than an oversight. Four Unity-layer
  systems went in the same night and two of them broke the build, so the
  last two milestones went in where the tests actually prove them instead
  of where they could fail twenty minutes away on a runner. Wiring is the
  first job next session and is small — the intent router picks both up the
  moment their buttons exist, which is the router's whole point.

  **Access.** Nothing is locked. A gate lists several keys and holding any
  one opens it, which turns "multiple solutions per obstacle" from a thing
  to remember into a structural property. Keys: standing with an
  organization, street noise in *both* directions (some rooms open only to
  somebody nobody has heard of, others only to somebody who already is
  somebody), dress, an introduction, money, the hour, leverage on the
  doorman, headcount. The cheapest key held wins, so a player carrying both
  an introduction and sixty dollars does not silently spend the sixty. A
  refusal is a person talking who names the way in you came *closest* to
  having, with the figure — a door you cannot open and cannot learn about
  is level geometry rather than a system. A gate with no keys is a design
  failure, so it simply opens.

  **Operation planning.** Four choices — approach, hour, who you bring,
  tools — each trading something you want for something else you want. The
  trade is asserted rather than assumed: forcing it is *both* likelier to
  work and much likelier to be seen, so there is no dominant approach. The
  read is qualitative per the approved decision on visible odds, and the
  test sweeps the whole risk range checking no digit ever reaches the
  player; it also names the single decision most worth changing, so a bad
  plan says *which* choice is bad. Three outcome bands, and the middle one
  is the interesting one: most of the way, leaving in a hurry, and a
  half-done job is still done. A failure leaves the job there and harder.
  Outcomes are computed in C# from competence, hour, heat, the coat and the
  target; no model is consulted, and what the model does afterwards is
  voice the people who saw it.

  **Still needed before either is worth playing:** content. Gates on actual
  places and a handful of authored targets. The systems are ready; the
  street has nothing to gate yet.
- **M8 — The Director — SHIPPED 2026-07-26.** `Director` + `DirectorBook`
  in Core, `DirectorHost` in the game layer, 42 new CoreTests (467 total),
  a 13-check SimHarness scenario (70 total) with a live half, and a
  `directorOk` gate in the in-engine CI sim.

  A world-level pass — not a character-level one — that every few nights
  reads the actual state and authors the next pressure from it. Five
  primitives and nothing else: put a fact in the mill, arrange a meeting,
  make a demand, change where somebody is, seed a grievance. Plus
  **nothing**, which the prompt argues for explicitly and which is the
  correct answer most nights ("*a world that produces an event every few
  days is a soap opera, not a place*").

  **Same law as the router: proposal, not adjudication.** Every person it
  names must exist in the snapshot it was given; every kind must be one the
  game has a primitive for; every pressure must justify itself from
  something concrete in the state, or it is discarded whole. Nothing is
  coerced into validity. A doctored *save* is refused on the same terms.

  **Pressure comes from neglect, not from bad luck.** The snapshot leads
  with what the player has left undone — a supplier unpaid, a crew member
  skimmed for weeks, a debt uncollected, stories in the street unanswered —
  and the prompt forbids inventing a stranger, an accident or a
  coincidence. This is the design decision that separates a director from a
  random event table.

  **Pacing is deterministic and checked before any call is made**: two
  pressures in flight at most, three days minimum between passes, and a
  window of one to four days so the player always has a day to see it
  coming. Demands are capped at $800 — a demand nobody could meet is an
  ending, not a pressure — and grievances at 0.2, the same ceiling the
  router's novel actions live under.

  **The player is never shown the pending list.** §6.2 says the player sees
  what they believe, never ground truth; a panel reading "a demand from
  Mirek is coming on day 14" would undo the game.

  Degrades to silence: no key, a failed call, or a refused proposal all
  produce an ordinary night. CI has no key, so the nightly pass never
  speaks there — the firing path is therefore staged by hand each build so
  the code most likely to break is the code most exercised.
- **M9 — Population scale — SHIPPED 2026-07-26.** `Population` in Core,
  `PopulationHost` in the game layer, 37 new CoreTests (504 total) and a
  `crowdOk` gate in the in-engine CI sim. **The city went from 36 people to
  3000.** This also delivers most of production item P5.

  Three bands, KCD2's arrangement: **Near** is a walker with a full brain
  (capped at 22 on top of the ~36 authored and generated cast); **Mid** is
  in the gossip mill and nowhere else — they carry and pass talk without
  rendering (capped at 110); **Far** is a record contributing only
  statistically, and thousands of those cost nothing. Re-banded every three
  seconds around wherever the player actually is, and only what *changed*
  is acted on.

  **The Far band is honest about what it doesn't know.** It answers exactly
  one question — roughly what share of the district has heard the talk —
  and it saturates, because a story never reaches literally everyone. When
  somebody is promoted, that share decides *deterministically*, via a
  stable hash of their id, whether this particular person had heard it. So
  walking away and coming back finds the same neighbourhood rather than a
  re-rolled one.

  **Anyone load-bearing is never demoted.** Crew, anyone holding a rumor
  about the player, anyone the player has met. And `GossipMill.Forget`
  *refuses* to drop somebody carrying a rumor or a memory — the world must
  not forget things because the player walked around a corner. Pillar P5
  outranks the frame budget.

  **The whole city saves as a seed plus the exceptions** — a few hundred
  bytes rather than 3000 records — which is the actual point of generating
  people rather than authoring them.

  Generation is deterministic and takes under half a second for 3000: 1200
  name combinations, 30 trades, day and night shifts, home and work
  anchors, and traits. Past 1200 people share a name with somebody, which
  is true of real streets.
- **M10 — PHONES + THE DISTANCE LAYER — SHIPPED 2026-07-27.** `Phones` in
  Core, five lines wired, a panel to ring from. **A phone is a place, not a
  pocket**: you ring the bar or the boarding-house hall phone and whoever is
  near it answers, so reaching somebody is a gamble on their afternoon and
  somebody else picking up is the interesting outcome rather than a failure.
  Messages left with a person travel as talk at one hop. Suspicion moves at
  45% on a line, in both directions, which is what stops it being a straight
  upgrade over walking there. Reachability reads live positions, not schedule
  tables — the schedule would have said yes while the person was two districts
  away. CI gate: eighteen calls over nine days must include at least one that
  got through AND at least one that did not.
- **M11 — VIOLENCE, STAGED — CONSEQUENCE LAYER SHIPPED 2026-07-27, MELEE
  DEFERRED.** `Harm` in Core, wired to the operation board. Injuries persist,
  compound, show as a look, and **turn if untreated** — which is what makes the
  infirmary a decision. Trauma is cumulative and does not heal with the wound.
  Feuds are first-class rather than suspicion: time cools them and never
  finishes them, and two people in a hot feud will not work together. A failed
  job breaks something, a partial cuts and bruises, a clean job hurts nobody.
  Getting hurt for you COSTS loyalty rather than earning it.
- **M13 — FINITE COUNTERPARTY PURSES — SHIPPED 2026-07-27** (see the full
  entry below; listed here so the milestone list reads in order).
- **COPPER ROW — SHIPPED 2026-07-27.** The city's second district. `StreetMap`
  generalised from one hardcoded grid to a district table, with the Hook's
  junction ids untouched. Copper Row is tighter (20m blocks), has its own
  streets and eight places, and its people actually live there — the population
  anchors were hardcoded to the Hook, so three hundred residents "of Copper
  Row" had been living in the wrong district. About a third of the city crosses
  one of the two bridges to work.
- **M12 — STREETS AND CARS — PULLED FORWARD, player 2026-07-26.**
  *"city can't feel real or immersive without cars and real streets. spec it
  and add it to the roadmap. needs to be built by 8 am. melee later."*

  This supersedes the agency model's "vehicles: 40, late, non-differentiating"
  line, and the reframing is what changes it: the argument is about
  IMMERSION, not about driving as a mechanic. A city with no traffic and one
  crossroads does not read as a city, and every social system in this project
  stands on the claim that this is a real place.

  The diagnosis is sharper than "no cars". The district's BUILDINGS already
  exist — geometry is placed at all fifteen planned locations. What does not
  exist is any street connecting them: there are exactly two roads, the
  founding cross at x=0 and z=0, and twenty-two locations sit in open ground.
  The city has buildings and no streets, which is precisely why it reads as
  a diorama.

  Full spec in `streets-and-cars-spec.md`. In short: a real grid of five
  north–south and five east–west avenues on irregular spacing (the founding
  cross is two of them, so nothing built moves), every map place connected to
  it by a lane, three road classes, and the whole network as engine-free data
  in Core so the walkers can follow actual streets, the cars have something
  to drive on, and CoreTests can prove every address is reachable from every
  other. Then traffic, then a driveable car, then witnesses who describe it.

  Built in an order where the game is playable at every commit and the least
  important thing arrives last — road geometry alone fixes the diorama
  problem, so if the runway runs out everything from traffic down is cut
  before the city stops looking like a city.

  NOT in scope, deliberately: running people over, car ownership and
  customisation, police pursuit, damage, fuel, parking. Those are a different
  game's Tuesday.

  **STATUS, 2026-07-27 — BUILT.** The player extended the scope in a second
  message (*"traffic lights/signs, collisions, different kinds of vehicles
  (trucks, cars, vuses, taxis, bikes), etx etc?"*) and approved a seven-item
  order. All seven landed:

  1. **Walkers on pavements.** `NpcWalker.Steer` followed "the nearest point
     on the founding cross", which was a fair description of the city when it
     had two roads. It now uses the real network and offsets to the pavement,
     so the crowd walks down streets instead of cutting across blocks.
  2. **Traffic**, as a deterministic fixed-substep model in Core. Four
     properties are held as tests because none of them can be judged from a
     screenshot: nobody overlaps, nobody crosses a stop line on red, nobody
     drives through a person, and the grid never wedges solid. Three of the
     four failed the first time they were asked — including a genuine
     three-way deadlock at one junction.
  3. **Vehicle variety** — car, van, lorry, bus, cab, bicycle as a data table
     rather than six subclasses, differing in length, speed, braking and three
     behaviour flags. Buses run a circuit and dwell at stops, cabs idle at the
     ferry stop and the cab rank, bicycles thread the lanes and ride near the
     kerb.
  4. **Signs** — stop signs on every approach that exists, no-entry discs
     where the lanes leave a junction, and street-name plates. Ten named
     streets, with `StreetMap.AddressOf` shared by the plates and the gossip,
     so the city can never tell the player one name and a character another.
  5. **Traffic lights** at the four junctions where two avenues cross in the
     interior. A pure function of the clock rather than a state machine, so a
     light cannot drift out of step with its own render and needs no saving.
  6. **The driveable car** — get in, drive, get out. Kinematic, not a
     rigidbody: Core steps the AI traffic against its own rules and a physics
     body dropped into that is two systems arguing over the same metre of road.
  7. **Witnesses describe the vehicle**, and describe it whether or not the
     player wore the coat. The disguise buys doubt about the face and none at
     all about the car in the street.

  Frame cost went in BEFORE the traffic rather than after: `Perf` reports mean
  frame, p95 and worst frame in the sim report, and a traffic tick averaging
  over 4ms fails the build.

  Still not in scope, and now a decision the player should make rather than
  one taken quietly: **running people over remains impossible** — cars brake
  and wait. See `decisions-pending.md`.

- **M11 — Violence, staged — MELEE DEFERRED** (player, same message). The
  consequence layer (injuries that persist, crew trauma, feuds) is unaffected
  and stays near. Playable brawling waits for the art pass: the spec is
  positioning, timing and reading opponents, which is animation and readable
  body language, and none of that can be judged on capsules.

- **M13 — FINITE COUNTERPARTY PURSES** (player, 2026-07-27, after asking how
  KCD2's economy works). *"add it to the end of the roadmap and spec/build
  it."*

  The living economy (M7) made the district's money finite in one direction:
  squeeze the street, the street gets poorer, the bar takes less. But every
  COUNTERPARTY still had infinite pockets — Ruta owed $180 and produced $180
  on demand, out of a starving street, in one movement. That is a payout table
  wearing a person's face, which is the exact failure the rest of this project
  is built to avoid.

  KCD2's traders hold a finite purse, and it is the best thing in that game's
  economy: you cannot convert four suits of looted plate to cash in one place,
  so money becomes a logistics problem and the map gets bigger without gaining
  a metre. The version that belongs HERE is not logistics. It is *who has the
  cash, and what do they want for fronting it* — which is a conversation.

  Full spec in `counterparty-purses-spec.md`. In short:

  - **A purse is what somebody can lay hands on today** — not their wealth,
    not their income, the money in the drawer. Cash, weekly flow, ceiling;
    none of the three is ever shown.
  - **Purses fill from the district's prosperity**, so squeezing the street
    drains the pockets you are trying to collect from — and it arrives a few
    days later, when you have started relying on being paid. Two turns of the
    same screw, and the second is the one that hurts.
  - **Asking for more than somebody has gets you what they have.** Collection
    gains a fourth outcome — paid what they could — and a big marker stops
    being a transaction and becomes a relationship: four visits, or one visit
    and a decision about what you are willing to do to shorten it.
  - **They can go and get it.** A debtor emptied and still owing borrows from
    a patron overnight. The money MOVES rather than appearing, and the favour
    they now owe is real world state the Director can read. You will often not
    know it happened; you will notice they paid, and that they are colder
    about it than the money explains.
  - **Generated on demand from a stable hash**, so all three thousand
    residents have consistent means without anybody authoring three thousand
    numbers. Only the named cast is hand-written, and only where their means
    are character: Sam turns over sixty a week and owes a hundred and twenty,
    which was never going to be one visit.

  NOT in scope: rackets (already coupled through prosperity — a per-business
  till would double-count the same pressure), banking, interest, or a lending
  market. One patron, one favour.

  The failure mode to watch is KCD2's own: its early economy is tight and
  memorable and then crafting turns into a money printer and it stops
  existing. If purses make collection weaker without making anything else
  weaker, they have moved the optimum rather than deepened the choice — so the
  balance lab runs against this before it is called done.

### ACT III — THE LEDGER COMES DUE — SHIPPED 2026-07-27

The last authored act, and the one the whole game had been pointing at with
nothing at the end of it: the ending arithmetic had existed since the act was
drafted, and no path through the game could reach it.

The crisis is the **audit** (player decision, 2026-07-27). Somebody with a
mandate asks to see the bar's books, and the bar's books are the one document
in this game that has been quietly lying since day one. It cannot be fought —
only survived, deflected, or answered by choosing which life to keep.

- **It opens off the world**, not off a day number: the Table answered, plus
  either Ossei able to name the rackets or an operation too big for a bar to
  explain its own money. The letter names a date six days out. That date is
  the clock — the player is never shown a countdown.
- **The strain is wrong in BOTH directions.** Launder too little and the night
  money has nowhere to have come from; launder too much and the bar earned
  more than a bar on this street possibly could. Said as a shape ("these books
  describe a business that does not exist"), never as a figure.
- **Five pressure points off real state.** PP2 waits until the player is
  standing in front of Lena, because the scene *is* her deciding what they
  have earned — and what she shows them is gated entirely on loyalty. PP4
  fires the moment somebody on the crew could genuinely hold it, which is a
  fact about how the player has treated their people.
- **Three verbs, each in front of the person it costs something with.**
  Halvard sells you out of it at half what it cost (fronts back to their
  owners, rounds stopped, crew paid off — and how they take it depends on the
  cut they were on). Ossei points the audit elsewhere, and burns by name
  whoever gave her the statement that made it possible. The successor gets it
  signed over.
- **No ending menu, anywhere.** Each ending is a condition the world can be IN
  when the books are opened; several can be live at once, and the last thing
  the player did decides. A player who does nothing still gets an ending,
  because the audit was never waiting for them to be ready.
- **The Quiet Ending is the only one with an after** — three mornings in which
  you hear about the street the way anybody who left hears about anywhere, and
  what arrives is decided by the world you handed over.

Verification: 15 new CoreTests (1205 total) over the epilogue, the one-way
flags surviving a reload, and dissolution moving the world rather than
clearing a flag; plus an in-engine sim gate that stages the preconditions on
day 9 and asserts the audit closes on an ending that is not `None`.

**Finished the same day, in four more passes:**

- **The ending actually reads the books.** `Eligible()` never consulted the
  strain — it was computed, worded, shown to the player, and ignored by the
  function that decides. Three acts of laundering decisions were decorative.
  Keeping anything now requires the ledger to survive being looked at, with
  two deliberate exemptions: selling up (nothing left to be in them) and
  handing over (it lands on whoever signed).
- **The audit has a face.** Tobias Reisz, Board of Excise. Not corrupt, and
  that is load-bearing rather than characterisation — an inspector with a
  price turns the ending matrix into "did you save up". One item a day for six
  days: produce it or tell him to put it in writing. The only Act III verb
  that is not irreversible and the only one that costs nothing but attention.
- **PP5 is a scene.** Two calls on the last day: Lena moves the real books
  (gated on loyalty, and her refusal has her own reason), a crew member is
  told to go quiet, or somebody in the day life hears it from you first. All
  three run down the M10 exchange, so reaching anybody at all is a question
  about where they happen to be standing.
- **The distribution is measured** (`balance-findings-endings.md`). Three
  holes: a player who never built an empire had exactly one ending; Both fired
  51-58% against a decision that it should not be first-playthrough
  reachable; and empire-kept + life-kept + audit-survived fell through the
  matrix into losing everything. All three closed. CoreTests 1291.

Still open in Act III, and both are Jafar's: `decisions-pending.md` #10 (the
inspector may be too decisive) and the fact that nobody has PLAYED the
endgame — measured is not the same as felt.

### CI HONESTY — 2026-07-27, and the most useful thing found all day

A build went green having tested almost none of the game. The sim bot lost
the week on day six, so the open city never opened, so every gate guarding
itself on `OpenMode` passed **on its own precondition being false** — empire,
Director, operations, Act II, Act III. Nine simulated days, the entire second
half skipped, CI reporting success, and the Act III gate written that morning
had never once run.

The rule that came out of it: **a conditional check is worth its green tick
only if something asserts the condition was reached.** Applied as:

- a **coverage floor** — day eight arrives without the city open, the sim
  opens it (the bot's job is not to *deserve* the open city, it is to exercise
  it), and `coverageOk` fails the build if the run skipped the second half;
- `perfOk` no longer passes on having recorded no samples at all;
- the traffic following-distance check reports `not-measured` instead of a
  sentinel that read like proven clearance;
- and `ShapeCheck` now keeps CS0103 for lower-case names, so a mistyped local
  is caught in a second rather than nine minutes into a runner.

**And then the floor paid for itself within the day.** With the vacuum drained
the gates finally reported, and named four: `director`, `ops`, `witnessCar`,
`coverage`. Two bugs, neither in the game, both in the tests.

Three of the four were **unsatisfiable**. The Director, the operations plan and
Act III all staged on `now.Day >= 9`, and day 9 cannot be reached in a nine-day
run — the Fall moves the calendar forward three days rather than simulating
them, so a fall late on day 8 lands the world on day 11 and the run ends before
hour 11 comes round again. Those gates had never once been evaluated, and only
looked green because they were also vacuous. Staging now keys on the open city
existing rather than on a date, and the sim reclaims days the clock skips —
three days inside is world time, not simulated time.

The fourth was **asking the wrong question**. The car gate read the gossip mill
at the end of the run, and the Fall deliberately clears every rumor about the
player. So with a fall in the middle it was asking "did the Fall happen" and
answering truthfully. Now latched hourly, while the run happens.

Which is the rule's second half, and it earned its place three times in one
morning: **a gate about something that HAPPENED must be latched when it
happens.** Reading a mutable world at the end and treating the answer as
history is a different failure from the vacuous conditional and it hides just
as well.

A footnote worth keeping, because it cost most of a morning: the sim's verdict
was believed unreadable from this environment and five builds went into moving
the print statement. It was always readable — `get_job_logs` with
`failed_only=true` and a `run_id` returns the whole line, while the per-job
`job_id` call returns a ~4KB tail. **Re-check the retrieval before rebuilding
the sender.**

Losing the week is still reported rather than papered over: whether a careful
player survives at the current gossip rate is a real balance question.

## STILL OPEN — the honest list (2026-07-27)

Kept current alongside the shipped entries, because a roadmap that only grows
a "done" column stops being a plan.

**All six open decisions answered by Jafar, 2026-07-27.** Act III's crisis is
the **audit**; Copper Row is **re-cut as the market quarter** (done); the UI
smoke test is **"yes, very important"**; **Ironside next and the rest later**;
the sim-bot and purse changes stand.

- **M14 — DISTRICTS 4-7, LATER** (player, 2026-07-27: *"ironside, rest
  later"*). Downtown, The Strip, Fairview and Gullwing stay names in the design
  doc until there is a reason to build them. Three districts is enough to prove
  the district system; seven is enough to spend a runway on. Ironside is the
  exception because the code already half-believes in it — the population
  generator and the research notes both reference it as though it exists.

**Unblocked and queued:**

- ~~**Act II's seven pressure points.**~~ CORRECTED 2026-07-27. This entry said
  the authored moments were not all fired; they are, and have been. What was
  actually missing was PROOF — Act I had a sim gate and Act III got one, and
  the middle of the spine had none. Now gated on the implication "wherever a
  pressure point's condition holds, its flag is set", which catches a beat
  that can never fire without pretending a nine-day sim reached a summit.

  What remains genuinely open in Act II is playtest, not code: nobody has
  seen the seven fire in a long campaign, so their PACING is unverified.
- **Act III's own gaps.** The act ships whole, and three things in it are
  thinner than the rest: PP5 ("the last day, and the phone") is a line of
  text rather than a scene; the audit has no in-fiction inspector to talk to;
  and there is no way to see the endgame except by reaching it, so the only
  balance evidence for how often each ending fires is CoreTests.
- **Front-end completeness.** P1 shipped a main menu, options and a pause menu.
  The rebind screen had drifted to six actions while the game listened for nine
  (fixed 2026-07-27). Not yet verified: every panel closes on Escape, no panel
  traps the player, and options actually apply on the newer panels (Plan,
  Phone, Ledger).
- **UI has no automated test coverage at all.** Every one of the 1182 tests is
  Core logic; nothing tests a panel. This is the weakest verification in the
  project and it should stop being invisible.
- ~~**Ironside has no geography**~~ — BUILT 2026-07-27. 34m blocks, two goods
  roads off Ironside Road, seven places, and a population split that houses
  one person in fourteen there and employs one in three. Downtown, The Strip,
  Fairview and Gullwing remain names in §7, deferred by the player.
- **Purses in more payment paths** — bribes and payoffs DONE (money you spend
  on people lands in their drawer). Supplier payments deliberately excluded:
  that is money leaving the player's own already-finite pocket.

  What is left is one thing and it needs a decision: **the rackets are still
  an infinite pocket**, and the spec's reason for excluding them ("already
  coupled through prosperity") is wrong in the direction that matters — the
  take drains the street but the street never limits the take. See
  `decisions-pending.md` #9.
- **The lab does not test a squeezed street's effect on purses**, because week
  mode holds prosperity at the ordinary half by construction. That coupling is
  proven in CoreTests only.

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
