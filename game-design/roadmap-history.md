# LEDGER — roadmap history

> **STATUS — LOG, 2026-07-31. NOT CURRENT.** Every dated build state, milestone
> approval and post-mortem from 2026-07-24 to 2026-07-31, kept whole because
> the reasoning in them is worth having and several are the record of a
> decision. **Do not read it as the present state** — for that, `roadmap.md`,
> which is now short enough to read in a minute.
>
> This file exists because the roadmap had grown to 1,525 lines of which
> roughly 85% was chronology: thirteen "BUILD STATE — date" sections
> interleaved with milestone definitions, a 219-line "STILL OPEN" list dated
> four days before anybody read it, and a 337-line re-sequencing from the 26th.
> Jafar, having read it after a doc audit that had only stamped a banner on
> the top of it: *"its a fucking mess... is that what a roadmap doc should look
> like to you?"* No.

> **STATUS — LIVE, verified 2026-07-31.** the plan and the build state. If this and another doc disagree, this wins.
> Kept current. If it is wrong, that is a bug in this file.

The founding doc's milestone list (§11) and our built reality have drifted — mostly
because M1/M2 were re-scoped by player decisions (gossip first, then the week campaign).
This document reconciles the two: what §11 called "M1 living block / M2 double-life MVP"
is partially built; several doc systems were missed along the way and are folded back in
below. This supersedes §11's numbering going forward.

## 20 Aug — the outer districts were never empty; the map was asking the wrong place

The single largest visible fault in the project, and it had two wrong
explanations before the right one.

**The symptom.** Seven district photographs, the first ever taken of six of
them. `district_downtown` and `district_fairview` read as a road with four cars
on a vast grey plain; the Hook beside them has terraces, signs, props and
people. That was an impression off a JPEG, and a pixel statistic over the seven
frames could not tell them apart at all — block spread 37-44 and flat ground
5-8% in every one, because textured ground varies as much as a street does.

**The first measurement chose the right question.** `parcelsByDistrict`, from
the builder rather than from pixels, came back `none:268` of 376 parcels — 71%
of every terrace in the world in no district, Fairview absent entirely. The
ordering looked like the finding I expected (the Hook rich, the outer districts
bare) and was ranking block spacing. Only 71% being *impossible* rather than
merely surprising caught it.

**The first wrong explanation.** `DistrictAt` pads a district by a flat 12m and
block spacing runs 20-34m, so a parcel outside the outermost avenue sits up to
half a block past the box. Plausible, internally consistent, and wrong.

**The second wrong explanation, which cost a day.** Widening the margin turned
the traffic gate red, so it was recorded as "the real fix is not free — it
wedges a bicycle" and queued rather than shipped. A ten-seed sweep then found
wedging on 4 of 10 seeds at double density on unmodified code, and that was
written up as "wedging is a standing fragility, not something this change
invented". Both readings came from the same broken instrument.

**The gate was the fault.** "In a minute of traffic, nobody is permanently
wedged" sampled a vehicle's edge and position, stepped sixty seconds, and
sampled again. Two instants cannot see the minute between them: a car that
leaves, drives a loop and returns reads exactly like one that never moved. The
flagged car reported `edgesSeenInWindow=8`. It had crossed the Exchange twice.

**The real cause.** `WideBlocks` scales the whole city about the origin by
`StretchX`=2.15 and `StretchZ`=1.15. Every consumer of the avenue arrays goes
through `ScaleAbout` — the junction grid, the block rectangles, the address
migration. `DistrictAt` read them raw, so it tested scaled positions against
unscaled boxes. Near the origin that is a small error, which is exactly why the
Hook, Copper Row and Ironside kept working and it survived this long.

| district | avenue centre x | x 2.15 | measured block cluster |
|---|---|---|---|
| the Exchange | -155 | -333.3 | **-333.3** |
| Fairview | -160 | -344.0 | **-344.0** |
| the Parade | 118 | 253.7 | **254.0** |
| Gullwing | 128 | 275.2 | **275.0** |

The Exchange's buildings stand 178m from the streets named for it. **38 of 52
block centres were in no district at all, and the Exchange, the Parade,
Fairview and Gullwing contained none.** After the fix: 0 of 52 outside, every
district has blocks (16/8/6/6/8/4/4), no two boxes overlap.

**And the margin never mattered.** With the box in the right place, margins of
12, 20 and 26 assign all 52 blocks identically.

**An independent measurement agreed, and it was predicted in advance.** The
sight-line depth metric shipped the same build with its prediction written into
the emitter before the run: the tour camera stands 14m up and 34m back at about
20 degrees down, so flat empty ground should read north of 40m and a built
street ten to twenty. Result: the Hook **24.3m**, Copper Row 40.6, the Parade
41.5, Ironside 41.5, Gullwing 43.1, Downtown 45.6, Fairview 45.6. Six districts
reading as bare ground, one reading as built, with the boundary exactly where
the arithmetic put it.

**Not a reporting fix.** `Traffic.LocalJunctions` keeps journeys local with
`DistrictAt`, the patrol beat decides where police work with it, and
`PopulationHost` places people with it. All three have been running against
boxes in the wrong part of the map.

**What now guards it.** CoreTests asserts that every block is inside some
district and that every district has blocks — a property of the map, needing no
measured bound. The wedge gate reads the whole window (every distinct edge a
vehicle touches, on every step) and its predicate is asserted in both
directions, with the real eight-edge reading kept as a fixture so the
regression cannot come back quietly.

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
   confrontation. Scheduled M4 alongside Ellis.
5. **The investigator is already authored (§8).** The "constable at high heat" idea from
   the M3/M4 discussion has a name: **Detective Mara Ellis** — patient, personal,
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
  escalation ladder, Det. Ellis (+witness interviews), save/load — PLUS the audit
  adopt-soon set: recognition barks, eavesdropping channel, debt book, response
  validator. Next stop M5 requires the player: playtest gate, purchases, HDRP, voice,
  Noor approval (drafted). Autonomous pre-M5 runway: balance-lab expansion, Tier-2
  sample ring, onboarding pass, AI-playtest hardening.
- **M5 — Vertical slice** (doc M3): The Hook polished (HDRP swap, city pack, character
  models/Mixamo, audio+voice via ElevenLabs), 5 Tier-1 characters (Rocco, Lena, Sam, one
  love interest — Noor or Elias, player's pick — and Ellis), 7 in-game days of Act I,
  output validator, onboarding. The is-this-fun gate and the demo artifact.
- **M6 — The Open City (Empire v1) — CORE SHIPPED 2026-07-26** (approved same
  day, built during the 24h autonomous run): open mode from day 8 with
  scarring Falls, businesses (clean/debt/hook routes), crew (need/hook),
  collection + protection rackets through the real mill, the observing
  Dockside rival, district geometry for the full HookMap, 14 generated
  residents walking (22 NPCs), balance-lab-proven no-death-spiral economy.
  See `empire-roster.md` + `balance-findings-open.md`. Remaining M6 flesh:
  ring-card promotions (Ferko/Rita/Vesna/Tibor), more batch walkers +
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
  Mitch asking for more and not explaining the difference. A poorer street
  is two regulars drinking at home.

  **Suppliers are people, not rows.** Mitch the drayman and Tony the
  wholesaler walk the district on their own rounds, carry the economy's
  state in their own words through `ExtraContext`, and can be settled with
  — a verb the intent router picked up for free the moment its button
  existed. Tony is the man Marla's recruitment need has referred to since
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
  Mitch is coming on day 14" would undo the game.

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
  COUNTERPARTY still had infinite pockets — Rita owed $180 and produced $180
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
mandate asks to see the pub's books, and the pub's books are the one document
in this game that has been quietly lying since day one. It cannot be fought —
only survived, deflected, or answered by choosing which life to keep.

- **It opens off the world**, not off a day number: the Table answered, plus
  either Ellis able to name the rackets or an operation too big for a bar to
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
  Hal sells you out of it at half what it cost (fronts back to their
  owners, rounds stopped, crew paid off — and how they take it depends on the
  cut they were on). Ellis points the audit elsewhere, and burns by name
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
- **The audit has a face.** Tobias Reese, Board of Excise. Not corrupt, and
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

Which is the rule's second half: **a gate about something that HAPPENED must be
latched when it happens.** Reading a mutable world at the end and treating the
answer as history is a different failure from the vacuous conditional and it
hides just as well.

**And it has a mirror image, found an hour later when the fixed build came back
naming `actTwoMissed=[pp6]`.** Act II's gate asserts the implication "wherever
a pressure point's condition holds, its flag is set", and PP6's firing
condition and the gate's condition were textually identical — so the gate was
not catching a drift, it was losing a race. It asked once, at the end, while
`CheckActTwo` runs on a 30-frame cadence: a condition that comes true in the
world's last hour is reported missing before the game has been given a single
tick in which to fire the beat. Now sampled hourly, with the conditions in one
place so sampler and gate cannot drift, and a beat fails only if it stays due
AND unfired across consecutive samples.

**The pair is the actual lesson, and it is worth stating as a pair:** the car
gate read a world that had MOVED ON and erased the evidence; the Act II gate
read a world that had not yet CAUGHT UP. Both were end-of-run reads of
something still in motion, and they fail in opposite directions — which is
why "just look at the end state" is not a safe default for either.

A footnote worth keeping, because it cost most of a morning: the sim's verdict
was believed unreadable from this environment and five builds went into moving
the print statement. It was always readable — `get_job_logs` with
`failed_only=true` and a `run_id` returns the whole line, while the per-job
`job_id` call returns a ~4KB tail. **Re-check the retrieval before rebuilding
the sender.**

Losing the week is still reported rather than papered over: whether a careful
player survives at the current gossip rate is a real balance question.

## BUILD STATE — 2026-07-28 08:25Z

**Run 30342318038 GREEN on `claude/game-dev-ai-automation-2h67ix`.** All
104 audit findings dispositioned, both delegated decisions built, Phase 3
complete (UI content coverage, P2 save robustness, QA matrix), M14 (seven
districts), P5 (district pulse + budget gates), P3 (score). CoreTests
1573, SimHarness 71, lint 0, ShapeCheck 0. Artifact: LEDGER-Windows.

Next is not code: it is `game-design/qa-matrix.md` and a human.

## BUILD STATE — 2026-07-28 late

Everything below happened after the 08:25Z entry above, which had stopped
being true by lunchtime.

**Shipped today, all green in CI:**

| | |
|---|---|
| **Game feel §1-§4, §6, §8** | Momentum and turn radius; camera spring, speed-linked FOV, look-ahead, collision, head bob; footsteps by surface with variants; **the limp**; acoustics (reverb by space, distance filtering, occlusion on speech, half-heard lines); interaction grammar (verb clock, doors with mass, bump reactions); input buffering and forgiveness wired; **the Fall staged behind a curtain**; foley and material impacts; the coat as a real verb |
| **Art pass** | Weather, wetness, neon, palette, fog (morning) — then **rain audio** and the **material palette sweep** (evening), which were the two items of the plan's concrete first pass that the first art commit skipped |
| **Voice** | Benchmark built and run four times against real game dialogue. **Engine decided: chatterbox**, on the direction test. Kokoro dropped. XTTS moot |
| **CI instrumentation** | Render colour fingerprint (caught a real neon defect on its first run), saturation metric, hourly street-density sampler |
| **Verification** | CoreTests 1595 → **1750**. Roughly 30 deliberate regressions reintroduced and caught across the day, two of which found bugs that would otherwise have shipped |

**The lesson worth keeping from today:** three separate times, the METRIC was
wrong rather than the thing it measured — brightRgb averaged colour to white,
satRgb averaged hues to khaki, and the TTS bench measured the wrong tensor
axis and reported a real-time factor of 326711. Each looked like a
catastrophic result and was a broken ruler. Check the ruler first.

## STILL OPEN — the honest list (2026-07-27, kept current)

Kept current alongside the shipped entries, because a roadmap that only grows
a "done" column stops being a plan.

**All six open decisions answered by Jafar, 2026-07-27.** Act III's crisis is
the **audit**; Copper Row is **re-cut as the market quarter** (done); the UI
smoke test is **"yes, very important"**; **Ironside next and the rest later**;
the sim-bot and purse changes stand.

- ~~**M14 — DISTRICTS 4-7**~~ BUILT 2026-07-28 (player: *"m14 now"*). All
  seven districts on the ground, each with §7's character expressed the way
  this map expresses character — block size, connector count, massing, and
  who sleeps there. Downtown works and does not sleep; Fairview sleeps and
  does not work; the Strip's workforce keeps night hours; Gullwing is
  nearly empty both ways, which is its mechanic. Chokepoint connectors
  throughout; the two-bridge rule holds on the actual water. Places,
  phones and population shares wired; the map tests scaled themselves.

**OPEN AS OF 2026-07-28 EVENING — the current front:**

*Waiting on Jafar — and as of this entry, THE ONLY THINGS WAITING ON
ANYBODY:*

> **STALE — read M16.0 instead (2026-07-31).** This list is dated 2026-07-28
> and the Mixamo item below was DONE on 2026-07-30: 41 clips and two bodies
> are in `ledger/Assets/Characters/`. I reported it to Jafar as the project's
> biggest open blocker by quoting this section without checking whether it was
> current, and he had to tell me it was finished. A "still open" list that is
> not dated at the point of reading is a trap; this one now says so in place.

- ~~**Mixamo characters + animations.**~~ **DONE 2026-07-30 — see M16.0.**
  ~4 characters and ~13 animations, downloaded and committed. Art direction
  moved to semi-realistic after he rejected the Synty low-poly look. Blocked
  foot IK, the coat reading at distance, fatigue breathing, and moving the
  limp from the footstep rhythm onto the body.
- **The voice listening pass.** `tools/voice-fetch/` makes this two commands
  and about fifteen minutes; see below.
- **Bark curation, step 3.** A human pass, and not optional — it is what
  separates writing from AI slop. Steps 1 and 2 are done.

*Mine, and CLEARED 2026-07-28:*
- ~~**Voice casting**~~ — cast written as briefs rather than preferences (a
  brief is sourceable, a preference is not), and `tools/voice-fetch/` built:
  streams Common Voice, assembles eleven seconds of one speaker per
  candidate, lays them out under their briefs. Cut from 37 clips to 19 —
  a correction, not a saving: Common Voice contributors read neutral
  sentences, so the mood variants were never sourceable from it, and the
  direction test proved chatterbox's exaggeration control does moods.
- ~~**Bark enumeration and generation**~~ — `ledger/BarkGen` walks the state
  space and measures the banks instead of asserting them. It found every
  slot repeating inside ninety seconds, and a pairing bug no line count
  could see (openers welded to replies by `seed + 1`: fourteen banks of
  fourteen giving fourteen conversations, not 196). 58 lines → 420.
- ~~**Grain, vignette, bloom**~~ — `FilmGrade` + `LedgerFilmGrade.shader`,
  three passes, fails closed to unfiltered.
- ~~**Game feel leftovers**~~ — ALL of them. Objects react to being brushed;
  puddles splash; day/night is a continuous equal-power crossfade instead of
  a single-frame swap at 20:00; menus fade, swap and change the world under
  black; kerbs and stairs are no longer walls. **§8 of the feel spec is
  closed.**
- ~~**The root-motion vs code-driven decision**~~ — **CODE-DRIVEN**, decided
  and written into the feel spec §2 before the animations land, because
  after they land it is a rewrite. The cost is named rather than hidden:
  foot sliding, which foot IK fixes, and which is cheaper to fix than a
  movement model is to replace.
- **Street density** — sampler shipped; the numbers arrive with the next CI
  run, so this is waiting on a machine rather than on a person. The question
  "is 700 NPCs right" was the wrong question: 700 is the size of the social
  graph, density is a different knob.

*COMBAT — specced 2026-07-28, see `game-design/combat-spec.md`:*

Deferred by Jafar earlier, correctly, on the grounds that timing combat
cannot be judged on capsules. That deferral produced something unusual and
valuable: **the aftermath of violence was built before the violence.**
Injuries persist and turn bad, treatment costs money and plants a witness,
feuds outlive fights, scars are permanent, and lost capability now shows in
the walk. We are not adding combat to a game — we are adding the last
missing verb to a consequence system that has been waiting for it.

The filter that decides the design, from `agency-model.md`: *violence is
SEEN*. In a game whose antagonist is gossip, a fight is the loudest possible
event, and its cost is witnesses rather than damage.

| Phase | What | State |
|---|---|---|
| 1 | `Core/Combat.cs` — the verbs as tested state machines, reach, guard, footing, stamina | **BUILT 2026-07-28** |
| 2 | Witness rules — who saw it, from how far, through what | **BUILT 2026-07-28** |
| 3b | `Core/Homicide.cs` — the body as an undiscreditable fact, police escalation on Ellis, the crew who watched | **BUILT 2026-07-28** |
| 3 | Bodies on screen, telegraphs, hit reactions | **Blocked — characters** |
| 4 | Tuning so violence is never the efficient path. A BalanceLab job: if Monte Carlo says fighting wins, the design is wrong however it plays | After 3 |

**Phase 3b is where the lethality answer cashes out**, and the design
problem was never "how does killing work". It was making the trade true as
ARITHMETIC rather than as an assertion in a document — killing has to
genuinely work or the choice is fake, and it has to cost more than it saves
or the gossip game is dead. `HomicideBook.Pressure`:

| Situation | Pressure | Police |
|---|---|---|
| One body, nobody saw | 0.40 | Procedure |
| One body, a witness through a wall | 0.76 | Investigation |
| One body, a witness who watched | 1.00 | **Manhunt** |
| Two bodies, nobody left alive to talk | 0.80 | Investigation |
| Three bodies, nobody left | 1.20 | **Manhunt** |

Lines three and four are the feature. Killing the only witness **really
does** take the manhunt off you — it has to, or the player stops believing
the system inside one attempt. It never takes you back to procedure, and
the body you add to fix the last one leaves you past where the first one
put you.

**UI/UX target: almost entirely absent.** No health bar, no damage numbers,
no hit markers, no combat mode. Condition is written on the body — the limp
already is — and `HarmBook.LooksLike` has returned exactly this since it was
written and nothing has ever displayed it. Same principle as M15: the
simulation IS the interface.

**All four decisions ANSWERED by Jafar 2026-07-28.** Player can start
fights; **killing witnesses is possible, rare and permanent** ("violence is
a part of our crime world and a legit tool"); guns out of scope for now;
readout diegetic-plus-heavy-feedback with a minimal HUD kept possible later.

The lethality answer overruled my recommendation and improved the design.
In a game whose antagonist is gossip, killing a witness is the most on-theme
violent act available: it WORKS — the rumour stops — and it creates a far
worse problem than the one it solved, which is the trade this whole game is
about. My objection was protecting the simulation from a shock it should be
built to absorb, so the objection became the specification instead: **a body
is the one fact in this game that cannot be discredited**, and that asymmetry
against every other rumour is what makes it terrifying rather than efficient.
It adds a phase — police escalation on Mara Ellis, the crew who watched —
which is the largest genuinely new work in the spec and comes from the
lethality answer rather than from the fighting.

**The risk, named rather than discovered later:** combat is the single
easiest way to ruin this game. It is the most familiar verb in the medium,
it attracts effort, and it will pull the design toward being about itself.
If phases 1 and 2 land and it still reads as a distraction, the correct
decision is to stop there and leave violence as something that happens TO
you.

*Blocked on a real refactor, named rather than quietly dropped:*
- **General audio occlusion.** Speech is occluded; every other source is 2D,
  so doing it properly means per-source 3D audio. Half-doing it gives a
  muffled bin beside an unmuffled car.

*On hold by decision:*
- **M15.3** — deleting the ledger panel and toasts for Mickey's book as a
  physical prop. Held until Jafar has played M15.1-2, because it removes
  things that currently work.
- **Environment art packs.** Would clash with semi-realistic characters.
  Waits on the character look being settled.

**Unblocked and queued:**

- ~~**Act II's seven pressure points.**~~ CORRECTED 2026-07-27. This entry said
  the authored moments were not all fired; they are, and have been. What was
  actually missing was PROOF — Act I had a sim gate and Act III got one, and
  the middle of the spine had none. Now gated on the implication "wherever a
  pressure point's condition holds, its flag is set", which catches a beat
  that can never fire without pretending a nine-day sim reached a summit.

  What remains genuinely open in Act II is playtest, not code: nobody has
  seen the seven fire in a long campaign, so their PACING is unverified.
- ~~**Act III's own gaps.**~~ ALL THREE CLOSED 2026-07-27. PP5 is a scene now
  (two calls down the M10 exchange, and reaching one is not reaching another);
  the audit has a face in **Tobias Reese**, Board of Excise, who sits in the
  bar from nine until six; and the ending distribution has been measured over
  400 worlds a row rather than inferred from CoreTests
  (`balance-findings-endings.md`).

  What replaced them is smaller and sharper. The in-engine Act III gate had
  never executed once — it staged on a day the clock steps over — and on run
  30259492282 it finally did: **the audit opened, closed on day 8, and
  resolved to `Kingdom`.** It has now run exactly ONCE, so treat its first
  green as new information rather than as confirmation. Still open and
  genuinely a playtest question: **the inspector is inert for a player who
  never built an empire.**
- ~~**Front-end completeness.**~~ CLOSED 2026-07-28. Every panel closes on
  Escape (the chain was missing Plan/Phone/summary — audit), no panel traps
  the player (the lock policy is one method and the smoke test asserts
  through it), and options apply on the newer panels: every font size in
  the UI routes through UiTheme.Scaled, with the build-time limitation
  stated on the options screen itself. The rebind screen's completeness is
  now a standing smoke assertion, not a one-time fix.
- ~~**UI test coverage is still the weakest link.**~~ CLOSED as specified
  2026-07-28: every panel's smoke check now carries a CONTENT predicate
  read off the live Text components (the ledger its sections, the pause
  menu its verbs, the plan a REAL seeded plan, the rebind screen the full
  set of actions the game listens for), and the ui gate floors the report
  count so a dropped panel reds the build. What remains beyond this is
  per-string assertion depth — a matter of degree, no longer a named gap.
- ~~**Ironside has no geography**~~ — BUILT 2026-07-27. 34m blocks, two goods
  roads off Ironside Road, seven places, and a population split that houses
  one person in fourteen there and employs one in three. Downtown, The Strip,
  Fairview and Gullwing remain names in §7, deferred by the player.
- **Purses in more payment paths** — bribes and payoffs DONE (money you spend
  on people lands in their drawer). Supplier payments deliberately excluded:
  that is money leaving the player's own already-finite pocket.

  ~~What is left is one thing and it needs a decision: the rackets are still
  an infinite pocket.~~ **ANSWERED AND BUILT 2026-07-27** (Jafar: *"couple
  it"*). Racket income now scales with the street it squeezes, and says so
  rather than quietly paying less. Nothing is left open on purses.
- ~~**The lab does not test a squeezed street's effect on purses.**~~
  MEASURED 2026-07-28 in the open lab, where prosperity moves: six days of
  refill after a day-15 collection sweep reads 346/306/203 dollars for
  Control/Cautious/Aggressive (street 0.48/0.40/0.29). Squeezing the
  street empties the pockets you later collect from, ~40% at the hard end.

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

- ~~**P1 — Front end**~~ DONE (2026-07-26/27, entry never struck): main
  menu, new game/continue + slot copies, one OptionsScreen shared with the
  pause menu, rebinding (completeness now smoke-asserted), pause, quit.
- ~~**P2 — Save robustness**~~ DONE 2026-07-28: version field + migration
  (2026-07-27), atomic write-then-swap with .bak, corruption recovery with
  quarantine and an in-fiction line, three rotating manual copies ("Keep a
  copy" / "Open the copy — day N"), Continue opens the newest save, and a
  new game no longer burns the player's snapshots. The sim asserts the
  backup line exists after a second write.
- ~~**P3 — Audio**~~ COMPLETE 2026-07-28: the score joined the ambience —
  a procedural aeolian piece under a sparse pentatonic line, night as the
  day's tune with the lights off, ducked to a third while people talk.
  Same drop-in pattern as everything else: composed music replaces it by
  file name, no code change.
- **P4 — Accessibility** — PARTIAL: colourblind-safe palette (toggle,
  UiTheme-wide), remappable input, and text scaling (now reaching every
  UI font) exist. STILL OPEN: an audit against a real checklist — e.g.
  reduced motion, input hold/toggle alternatives, readable-font option —
  and whether dialogue needs subtitle-style presentation options at all.
- **P5 — Performance** — HALF BUILT 2026-07-28: the district pulse is
  §9's "statistical sim elsewhere" made concrete (the far city summarized,
  cashed in at promotion), and the sim now GATES on deterministic entity
  budgets while reporting frame times and heap. STILL OPEN: draw-call
  counts and real frame budgets on target hardware — Jafar's machine, via
  the QA matrix.
- **P6 — Controller + Steam Deck.**
- **P7 — Localisation**: externalise UI and authored strings. Generated
  dialogue can be produced directly in the target language — an advantage.
- **P8 — Platform**: Steam page, achievements, cloud saves, release build
  pipeline.
- ~~**P9 — QA matrix**~~ WRITTEN 2026-07-28: `game-design/qa-matrix.md`,
  every row something automation cannot establish, half-coverage named.
- **P10 — LLM productization** (see doc §16): inference economics
  decision, content safety and red-teaming, age-rating strategy. The
  highest-risk item in the entire project and the one needing you earliest.

Rule reaffirmed from §2: if a feature serves none of the five novelty claims, it is cut.

## BUILD STATE — 2026-07-29 13:11Z, GREEN

Run 30453392188, commit `96f95e2`. `no failing gates`, `pass=True`. The
first fully green Windows build the project has produced, and the one to
play.

**Shipped since the 28th:**

| | Work | Where |
|---|---|---|
| Bodies | 13-box mannequin in a real joint hierarchy; proportions, stride, idle phase and head varied per person off their name | `Game/Mannequin`, `Core/Physique` |
| Motion matching | Feature layout, normalisation, cost weighting, search cadence, jump margin, clip boundaries, inertial blend — against a stand-in corpus | `Core/MotionMatch` |
| Confabs + the hush | Pairs stop and talk; they break off when the player walks up, and only if it was about him | `Core/Confab`, `Game/NpcWalker` |
| The mix | Asymmetric ducking, per-bus depth, voice budgets, incoherent crowd summing | `Core/Mixing` |
| Wet reflections | Probe capture published as the scene reflection — see the note below | `Game/WetReflections` |
| Graphics presets | Three stops; the crowd is deliberately the last thing cut | `Core/Detail`, Options → Graphics |
| Frame readout | Typical and worst-of-3s on F1, because CI has no GPU and cannot produce the number | `Core/FrameRate` |
| Image statistics | Local spread, darkened/brightened fractions — the rulers three render gates should always have used | `Core/ImageStats` |

**FIVE SYSTEMS WERE FOUND BUILT AND NOT RUNNING.** The post-processing
stack (attached to a child of the camera, so `OnRenderImage` never fired).
The cinematic camera (switched off in the sim by its own guard). The
authored beats (never attended in any verified run). `StemGain` (returned
the mixer's number, not the AudioSource's). The reflection probe (refreshed
142 times a run and lit nothing — a renderer only samples a probe when its
bounds sit inside the probe's box, and the road's meshes dwarf it).

Each was built, tested, correct, and connected to nothing. **The
generalisation, which now has a name in `the-gap.md`: an A/B is only a
measurement if the thing it switches is switched by the time the frame is
drawn.**

**And four gates were measuring the wrong quantity** — grain (global
variance, which clamping at black can drive the wrong way outright),
occlusion (a global mean diluting a local effect), bloom (a global
bright-pixel count that collapses when the camera is not facing a lamp),
and the beat approach distance (sampled once per in-game hour, so it could
not see a close pass). Thresholds are derived from first principles now
rather than tuned until green.

**Suspicion becomes behaviour, verified.** `checks` and `confronts` read
zero on every run this project had ever produced, because nothing pushed a
tracker past 0.50/0.80. Staged on day ten in the open city — deliberately
after the week is decided, because staging it on day six tipped the verdict
and a probe that alters the result beside it is not a probe.

**Still outstanding, and all three are Jafar's:** the voice listening pass
(one-click launchers now in `tools/voice-fetch`), the Mixamo download
(free, and the real animation item), and the violence decision below.

## M16 — PERCEPTION, WEAPONS AND VIOLENCE (approved 2026-07-29)

`weapons-spec.md` v3, **approved in full**. The largest single feature in the
project, and it changes the game's framing: LEDGER is a crime game in a city
that perceives, reacts and remembers — gossip is the consequence layer, not
the foundation.

This supersedes M11's deferral of violence and closes the *"is violence a
verb"* question in `decisions-pending.md`.

**Phase 1 — perception, no weapons.** Vision with cone, range, occlusion,
light level and motion; hearing with loudness, occlusion, **ambient masking**
and alert scaling. NPCs notice, turn, and investigate. Ships to a playtest on
its own. *Gates: a walker in light is detected further than one in shadow; a
sound behind a wall is not heard; a sound under the ambient floor is not
heard.*

**Phase 1b — legibility, alongside Phase 1, not after.** The vignette
response to light level, the one-frame noise ring at the true audible radius,
and the four attention channels (street goes quiet, barks, behaviour break,
music stem) plus the optional accessibility marker. *Gates: the vignette
measurably changes with light level via `ImageStats`; the ring radius equals
the acoustic model's radius, asserted against the model rather than a copied
constant.*

**Phase 2 — observation and reaction.** Slots, the five-rung identification
ladder, certainty vs willingness, mutual awareness, the delivery window, and
the witness ghost. Alarm propagates as sound; flee, deliver, fetch. *Gates:
the five claims in spec §4.7 — including that the same witness at the same
distance reaches rung 4 for an acquaintance and rung 1 for a stranger, and
that the ghost matches the belief record rather than the player's true
position.*

**Phase 3 — melee and carry.** Hands, blunt, edged, ligature. Brandish as a
verb. Carry, concealment, the frisk, blood on clothes. *Gate: the same
killing leaves no witness in an empty alley, several in a market, and none
in the back room of a busy bar.*

**Phase 4 — the murder weapon and the environment.** Provenance, the four
acquisition routes, disposal as a witnessable verb, Ellis looking for the
object — and accidents, which are the only violence in the game that produce
no crime.

**Phase 5 — firearms.** Deliberately last.

**Assumptions on record** (spec §13): perception runs for events the player is
party to rather than for all three thousand residents, and Phase 1 goes to a
playtest alone.

**Post-approval audit (spec §14) found fourteen gaps; all are resolved in
spec v4 §§15–18.** Four change the plan above:

- **Non-crime reactions move into Phase 1**, and Phase 1 now has a *behaviour*
  gate — loitering draws a look and a remark, running at night turns heads a
  walk does not, a 3am door slam brings somebody to a window. The old gate
  tested detection ranges, which would have let a city that computes perfectly
  and reacts to nothing go green.
- **The ghost is restricted to mutual awareness only**, because showing it for
  every witness destroyed the case where you are seen and never know it.
- **Two approved additions:** symmetry as the planning rule — *if you can tell
  he is facing you, he can see you*, gated on a silhouette measurement at 18m
  with the survey verb as the designated fallback — and **arrest with no
  chase** when a constable watches you do it.
- **`Violence.Saw` and `KillingConfidence` are superseded, not reused.**

**Estimate: ~17 days** (spec §18, plus the lab and the facing art). Phase 1 +
1b is 4.5 of them and is the hedge. `RunPerceptionLab` lands with Phase 2.

### M16.0 — THE MIXAMO DROP — **DONE, 2026-07-30**

**41 clips and two bodies, in the repo.** `ledger/Assets/Characters/`:
X Bot and Y Bot as skinned T-pose meshes (verified: `Geometry 5`, `Skin 1`,
~110-130 `Cluster` entries, ~72 bones each), and 41 animation clips sorted
into tiers, each named `{slot}__{mixamo name}.fbx` with `_picks.json`
recording exactly which clip answered which slot and whether it was an exact
match or a substitute.

**The catalogue is the quiet win.** `_catalogue.txt` lists all 2,589 animation
names on the account. Every Mixamo clip name written in this document before
today was recalled from training data rather than read; four of the first
picks were wrong because of it and eleven useful clips were invisible to me.
Notably a complete **Standing Block start / hold / end / react-large** set,
which turns the guard from a state into an action, plus the fight-idle
transitions, `Drawing Gun` for Phase 5, and stairs up and down.

Two slots are honest substitutes: `hands_up` is **Defeat** because Mixamo has
no "Surrender" and no "Hands Up" — checked in the catalogue, not assumed — and
`lean` is **Leaning** rather than a lean-against-wall.

---

#### The original ask, kept for the record

### M16.0 — THE MIXAMO DROP. **JAFAR'S TASK, and it is a real dependency**

Free, no account of mine, no purchase: Jafar downloads the characters and the
animation set from Mixamo and hands them over. Recorded here as a milestone
item rather than a footnote because **two things in this project are blocked
on it and one of them is combat.**

**Why it matters, specifically:**

1. **Combat.** `combat-spec.md` §6 Phase 3 has been explicitly blocked on
   characters since it was written — *"a swing on a capsule cannot be read,
   and an unreadable telegraph makes a timing system into a coin flip."*
   Telegraphs, hit reactions and the guard are the whole feel of a fight and
   none of them can be judged on boxes. This is the gate on melee, not the
   Core work, which is already built and tuned.
2. **The draw.** Weapons spec §6.3 calls it *"the most important animation in
   the game"* — one second, visible to everyone in a cone, and it cannot be
   taken back. Everything social about weapons hangs off it.
3. **Facing, and therefore the symmetry rule.** Spec §15.1 is designed to work
   on thirteen boxes at Tier 1 so Phase 1 is not blocked — but real heads,
   necks, shoulders and turn-in-place clips are what make it comfortable
   rather than marginal. **The silhouette gate is the acceptance test for the
   drop.**

**What is wanted, in rough priority:**

| | Clips |
|---|---|
| **Locomotion** | idle, walk, run, **turn-in-place (L/R)**, start/stop |
| **Attention** | look-around, head/aim offsets, standing conversation, listen |
| **Reaction** | flinch, startle, back-away, hands-up |
| **Combat** *(unblocks combat Phase 3)* | guard, strike, shove, stagger, take-hit, knockdown, get-up |
| **The draw** | reach-to-coat, present, holster |
| **Life** | sit, lean, work-at-counter, drink, smoke |
| **The end** | collapse, fall-down-stairs, lie-still |

A neutral male and female body each is enough to start; the procedural
mannequin rig was built against capsules precisely so a Mixamo skeleton drops
straight onto it.

### M16 BUILD STATE — 2026-07-30, overnight

**Phases 1, 1b, 2-Core, 3-Core and 5-Core are built.** 2578 CoreTests checks
(from 2299 at the start of the night), 83 deliberate breaks across five new
spec files, all confirmed red.

| File | What it is | Breaks |
|---|---|---|
| `Core/Perception.cs` | Vision with cone, range, light, motion and time-in-cone; hearing with loudness, **ambient masking**, occlusion and alert scaling; the five-rung identification ladder; the symmetry rule | 15 |
| `Core/Observation.cs` | Seven slots, separate actor/victim sightlines, certainty vs willingness, mutual awareness, the delivery window, hardening, misattribution | 19 |
| `Core/Notice.cs` | Non-crime reactions, and **the street going quiet** | 15 |
| `Core/Reaction.cs` | The ladder, alarm as a sound event, arrest with no chase, the survivor | 15 |
| `Core/Arsenal.cs` | Nineteen objects, seven families, brandish, carry, the frisk | 18 |
| `Core/Traces.cs` | Blood, and provenance/disposal | 16 |
| `Game/Perceivers.cs` | The bridge, and the frame budget |  |
| `LightModel` additions | The visibility readout — the vignette breathes with the light on the player | in `notice.json` |
| `BalanceLab.RunPerceptionLab` | The distribution nobody had measured |  |

**Three things the night established that were not in the spec:**

1. **`Vantage` needed separate sightlines for the actor and the victim.** A
   test asserting four witnesses produce four different slot sets got three,
   because one distance and one light level for "the event" makes
   *act-no-actor* unreachable — which is Jafar's own headline example. `Sight`
   was split off mid-build.
2. **A street that has gone quiet because it is watching you is a street where
   your next sound carries further.** Being noticed makes you louder. That
   fell out of putting masking and the hush on one number and is asserted.
3. **Nothing local compiles the Game layer.** A `double` Core constant landing
   in a `float` Unity field cost a build. `lint-usings.py` now has a CS0266
   rule that catches it in three seconds.

**Measured, not asserted** (`RunPerceptionLab`): partial observation is the
common case — sound-only 27%, nothing 27%, act-no-actor 21%, aftermath 12%,
**full 4.8%**. Somebody can name the player at 4% of events by day and 1.3% at
night, so **darkness cuts naming by 4.6x**. Accidents are available in 12.5%
of situations and brandishing produces Comply only 6.5% of the time, so
neither of the two dominance risks in spec §11 is realised.

**Not yet built:** NPCs walking toward a noise (hearing is in Core and not yet
driving behaviour), the noise ring, the witness ghost, melee verbs against the
new model, acquisition UI, firearms.

### M16 BUILD STATE — 2026-07-30 08:44Z, **GREEN**

Run 30526392229 (`de7d5a9`): **no failing gates, pass=True.** Thirty-odd gates,
including the new perception one, which a city that computes perfectly and reacts
to nothing cannot pass.

```
looks=817  loiterLooks=15 loiterNotices=1  nightRunLooks=4 nightRunNotices=4
sounds=1170  investigations=17  slamInvestigations=17  standoffs=43
litRange=37.7m  darkRange=23.4m  hushPeak=0.99
ringsSized=660  ringOk=True  perceptionWhy=ok
lastDay=13  meanFrame=286.32ms  perfOk=True  pass=True
```

**ONE CAVEAT INSIDE THE GREEN, stated because "green" must not imply more than
it says.** `ringsDrawn=0` against `ringsSized=660`: the noise ring's arithmetic
is verified — the radius it would use equals the model's, asserted against the
model rather than a copied constant — and **the circle has still never appeared
on screen in a built player.** The likely cause is the sprite shader being
stripped from the build, which is a rendering problem rather than a perception
one, and separating the two claims is what made that legible instead of looking
like a broken hearing model. It is the top follow-up: one of the two legibility
devices is currently invisible.

**What eight builds cost, and what they bought.** Every failure was mine and
each one was a different species:

| | |
|---|---|
| A `double` Core constant in a `float` Unity field | nothing local compiles the Game layer; there is a lint rule for it now |
| Sound emission behind a sim-mode early return | the sim could never see a footstep; hearing read as zero by construction |
| "Running" hard-coded at 3.2 m/s | this game's WALK is 4.0 — every night walk registered as a sprint |
| Standoff per-person cooldown only | 292 beats in nine days; a flourish that often is the ambient state |
| Hush dividing attending by present | one person nearby silenced the whole street |
| Probes waiting for an audience | never fired once; they now walk to somebody |
| A stale lamp cache | two views of one set; light attribution measured darkness against darkness |
| `BindPlayer` called from a path the sim never runs | the ring had no player to size against |
| The crowd charged twice in the ambient floor | a 3am slam came out quieter than the street it was slammed on |

**And two reds that were not mine.** `verdictSane` and the
preset/reflection/specular trio both recovered with no change from me —
stochastic, and both would have been damaged by "fixing" them. Declining to
weaken a gate to change its colour was the right call twice.

### M16.1 — THE RING, AND THE GUESS I MADE ABOUT IT

**STATUS: the ring is on screen, and the perception gate is green.** Run
30540250029 (`8f0a8ca`): `perceptionWhy=ok perceptionOk=True`, with
`ringSeen=1.4006%` of the frame changed at a mean rise of 0.38,
`ringPaintUsed=Hidden/LedgerRing`, `slamDrewRing=True`, `ringNoMaterial=0`.

**It took THREE bugs, not two, and I was wrong about the cause twice.** Below is
the whole sequence, kept because the wrong answers cost more than the right one
and are the more useful record.

The caveat above says the likely cause was the sprite shader being stripped from
the build. **That was a guess and it was wrong.** There were two bugs, neither of
them the shader, and the second would have kept the circle invisible even after
the first was fixed.

**Bug one — the cooldown counted the wrong thing.** Rings were rate-limited in
`Perceivers.Emit` to one every 0.55s, and the limit was spent by every ring
*measured*. Walking emits a footstep per stride, which at CI's 290ms frames is
about one a frame, and each of those spent the cooldown while carrying 3.6m —
far too little to be worth drawing. So there was always a ring's-worth of
cooldown standing between the player and the next circle, and the sounds the
device exists to explain arrived inside a footstep's shadow. `ringsSized=660`
was six hundred and sixty footsteps; the one door slam in thirteen days had a
coin-flip chance of getting through and lost it.

The rule now tracks what was **drawn**, and a meaningfully louder sound preempts
it and replaces the circle on the ground. *A footstep can never block a gunshot.*

**Bug two — the circle was standing on its edge.** The vertices were built flat
in local XZ and the transform was then rotated +90° about X, which puts the ring
in the world XY plane and aims the ribbon at the road. The comment on that line
read *"flat on the ground rather than standing up like a hoop"*, and the code did
precisely the opposite. Vertices now go in local XY with a −90° rotation, worked
through on paper because there is no way to look at it from here.

**Three things changed about how this is verified**, because the previous gate
passed a build in which the circle never once appeared:

1. **The draw rule moved to Core** (`Perception.RingDraw`). It lived in the Game
   layer, which nothing local compiles, and that is the whole reason a rule
   discarding every worthwhile ring survived. Eight CoreTests and four break
   specs, all four red.
2. **`slamDrewRing`** — the slam probe fires on four separate nights instead of
   once, and checks in the same frame whether a circle was created. A probe that
   fires once and can be silently robbed is not evidence.
3. **`ringSeen`** — the sim renders one frame with the ring's renderer off and
   one with it on and counts brightened pixels, the same A/B ruler as occlusion
   and reflections. **"Drawn" means an object exists; this means it is on
   screen.** Those are different claims and the distance between them was a
   circle standing on its edge.

The skip reasons are also itemised now — `small` / `shadowed` / `no-material`
mean three completely different things, and one `Shown` counter collapsing them
is what let me tell the wrong story with a straight face. **The lesson is the
project's oldest one in a new costume: check the ruler before the reading.** A
counter that goes up when a `GameObject` is constructed is a ruler for
construction, not for visibility, and I read it as though it were both.

**Bug three — there was no material at all, and that killed both fixes.** With
the cooldown and the geometry corrected the circle was still invisible, and the
gate said `ringSeen=0.0000%`: not approximately nothing, *exactly* nothing, which
is a different and much more informative number.

At that point I stopped guessing and made the sim measure every candidate in one
run — three materials, two layouts, and a positive control. That single build
answered five questions:

| measured | verdict |
|---|---|
| `control=17.8%` | the A/B is not blind, so the zeros are real |
| `ringNoMaterial=4` | **a runtime `LineRenderer` has no material in this build.** `sharedMaterial` is null. My comment insisted it "ships with the component and therefore cannot be stripped" |
| `sprites` == `default` to 4 dp | assigning `Sprites/Default` changed *nothing*, because `Shader.Find` returns null for it — it is not in the build |
| ~~`particles=0.0000`~~ | **this reading was wrong and I have withdrawn it** — see below |
| `transformZ=0.0000` vs billboard `0.7279` | **my reading of `LineAlignment.TransformZ` was backwards.** The paper derivation was wrong and only a rendered frame caught it |

So the ring now has **`Assets/Resources/LedgerRing.shader`** — unlit, because a
lit circle in a 3am street is a black circle; vertex-coloured, so the fade rides
on the LineRenderer's own gradient; alpha blended; `ZTest Always` like the light
shafts. It lives in `Resources` because everything in `Resources` is in the
player by definition, which is the actual reason the grade and the shafts work
where a built-in shader name does not.

**Two things worth keeping about the method rather than the bug.**

*One measured build beats five guessed ones.* Each hypothesis costs half an hour
of CI. Testing four at once, with a control, cost the same half hour and settled
all of them — including two facts I would have got wrong by reasoning.

*The sweep had a bug of its own, and the numbers exposed it.* `None` measured
0.7279% running first and 0.0000% running fourth, from identical code. `Destroy`
is deferred to the end of the frame, so each destroyed probe was still in the
scene for the next arm's renders, drawing its circle in the same place — every
arm after the first was reading through the one before it. Probes are now
switched off before being destroyed. **A diagnostic that can mislead is worse
than none, because it is believed.**

**AND ONE FINDING ABOVE IS WITHDRAWN, because it came from that broken sweep.**
I wrote that `Legacy Shaders/Particles/Alpha Blended` "is in the build and draws
nothing". With the probes fixed, the green run reports
`sprites=0.7018 particles=0.7018 none=0.7018` — all three identical, which is the
signature of all three falling back to *no material at all*. So the correct
reading is simpler: **neither built-in shader is in this build**, and a
null-material line renderer draws something anyway (0.70% of the frame, almost
certainly the magenta error shader). `Hidden/LedgerRing` measures 1.2344%, nearly
double, and is what the game uses.

Worth stating because it is the same mistake twice in one night: I drew a
confident conclusion from an instrument I had not yet checked. The instrument was
the thing at fault both times.

### M16 BUILD STATE — 2026-07-30 13:19Z, **GREEN, and this time the ring is in it**

Run 30544776454 (`fdea294`): **no failing gates, pass=True.**

```
perceptionOk=True  perceptionWhy=ok
ringsDrawn=4  slamDrewRing=True  ringNoMaterial=0  ringPaintUsed=Hidden/LedgerRing
ringSeen=1.2344%  ringRise=0.4496   ringControl=17.3637
looks=861  loiterLooks=11  nightRunLooks=9  sounds=1102  investigations=77
slamInvestigations=21  standoffs=41  litRange=37.7m  darkRange=23.4m  hushPeak=0.99
aoRounds=3  presetHit=14.74 (was 0.00)  reflHit=5.13  specHit=33.52
meanFrame=292.87ms  perfOk=True  lastDay=13
```

**The three-evening fix worked, and the size of the effect is the evidence.**
`presetHit` went from 0.00% to 14.74%, `reflHit` from 0.00 to 5.13, `specHit`
from 0.00 to 33.52 — with the thresholds untouched. Three gates had been reading
one instant of one evening, and the instant was often uninformative.

**Phase 1 and Phase 1b of `weapons-spec.md` are done.** The city sees, hears,
notices, investigates, and can be read without a HUD. Phases 2–5 remain, and
none of the arsenal is on a button yet.

### M16.2 — THE VOICE AUDIT, closed except the parts that are purchases (2026-07-30 night)

Jafar, after the accent oversight: *"what else in the world of speech/voices
did we miss?"* Eight gaps were written up. Five are now built, one is
deferred in writing, one is a purchase and one is a decision.

**Items 2, 5 and 7 turned out to be one piece of work.** The voice bus had
been fully described in `Core/Mixing` since the day it was written — reach,
budget, duck depth, protection rule — and connected to no AudioSource at
all. Speech in this game was text in a bubble. Wiring it needed a filename;
a filename needs a naming rule; a naming rule that survives regeneration
*is* determinism. Three audit items, one commit.

The telephone got the treatment its milestone always implied: the ITU
300–3400 band, a handset resonance, four line kinds, and two things that are
mechanics rather than decoration — **you cannot place a voice on a bad
line**, which is why anonymous calls work in every crime story ever written,
and **the caller's room comes down the wire**, so a hall behind Ellis tells
you which building he is standing in with no dialogue written for it.

**Item 4 was the sharpest, because it was a hole in a spec I wrote.** §6.2
gives four redundant channels for "you have been noticed" and calls the
redundancy the point. Three are audio. "Subtitles-first" renders exactly one
of them, because subtitles are for what was *said* and nobody subtitles a
room going silent. So for a deaf player the four channels were one.
`Core/Captions` + `CaptionBar` closes it, wired at `Perceivers.Emit` for the
same reason the noise ring lives there, and **gated**: `perceptionOk` now
requires the caption channel to have carried.

#### The three things that went wrong, and they are the useful part

**The caption bar was dead on arrival and looked wired.** Two of its three
channels are POLLED in `Update` rather than pushed, and the only thing that
created the object was `Show()`. A hush could never have appeared. Exactly
the ring's failure — a system built, plausible, and never once running —
caught this time before the build rather than after four of them.

**`breakrun.py` had been lying, and only a two-file spec could show it.** It
reverted the file the next break touched and not the others, so break N
stayed applied while break N+1 ran and the reported failure belonged to the
previous defect. Every spec until now was single-file. It reads as
mislabelling and is not: a defect still in the tree can be caught by the
previous round's check instead of its own, turning a SURVIVED into a RED —
the instrument claiming coverage it does not have, in the harness whose only
job is to prove coverage is real. **Third time this month the instrument was
the thing at fault.**

It paid for itself immediately. With it fixed, a break that drops the good
handset below the elision threshold SURVIVED — the check tested a single
seed and drew a lucky one. And `breaks/notice.json`, the other two-file
spec, turned out to have two stale anchors that had not been exercised in
some time while the tally quietly counted them as survivors.

**I asserted a crowd pool of twenty-four voices with a confident argument
for it.** The casting sheet funds six. Twenty-four would have named files
nobody was ever going to generate. Six is thin and is now written down as
thin, because the fix is casting, not a larger constant.

#### Still open

- **Non-verbal voice (item 3)** — grunts, pain, exertion. A cloner cannot
  make these at all. Phase 3 needs them and it has lead time. A purchase,
  so it is Jafar's: `decisions-pending.md`.
- **The casting sheet and the game roster use different names.** `kest` vs
  `sera`, and several gossipers nobody has cast. Unknown ids fall through to
  a crowd voice rather than throwing, so the symptom is a named character
  quietly sounding like a passer-by. A casting task.
- Items 6 and 8 — state-modified voice, lip sync — after the above.

### macOS — compiled for the first time (2026-07-30 night)

Never once built. No platform `#if` anywhere, no `.exe` assumption, nothing
in the way — which is precisely the sort of "should work" this project keeps
catching itself saying. `CiBuild` now takes a target and there is a macOS
job. Compile-only: the sim gates are green on Windows and paying macOS
runner rates for a second copy of them buys nothing.

Controller support is a real but contained job, checked rather than assumed:
zero `OnGUI` (all four UI files are uGUI Canvas, so the EventSystem focus
model already applies) and 27 `Input.*` calls across six files. The work is
moving those onto an action map, not a rewrite.

---

## BUILD STATE — 2026-07-31 evening. **The day the voices got cast.**

### What shipped

**THE CITY IS BRITISH.** Jafar's call. The finding was that the writing had
been British all along — `flat`, `colour`, `pavement`, `constable`, `kerb`, and
streets named Saltmarket, Quay Street, The Esplanade, Weighhouse Lane. The
American accent brief was the outlier, not the prose. Full consequence analysis
in `setting-britain-2026-07-31.md`. Currency is `£`. The bar is **the pub**,
and the counter is still the bar, because in British usage it is. The owner is
**the landlord**, which is the change that earns the decision: a job title
became a relationship, in a game about rent and obligation.

**THE AUDIT IS CUSTOMS AND EXCISE.** Section 112 of the Customs and Excise
Management Act — real, and the actual power of entry. "Revenue" turned out to
be correct excise vocabulary rather than an Americanism: a licensed publican is
statutorily a *revenue trader*, so nothing was renamed and the instrument is
now named instead. The duty clause gives `LedgerStrain`'s one-third laundering
ceiling a reason it never had — an officer reads takings against duty paid on
stock, and drink you never bought cannot have been drunk. And s.112(2) says an
officer may not enter after dark without a constable, which is now one of
Reese's hard facts and is the obvious next Act III beat.

**ALL NINETEEN VOICES ARE CAST.** `game-design/voice-picks.json` records them
by speaker id; the chosen clips are copied to `game-design/picked-clips/`,
named by speaker, where nothing in the fetch pipeline writes. Named cast:
English 8, Scottish 3, Northern Irish 1, Irish 1. Crowd pool: Irish 2,
Scottish 2, English 1, Northern Irish 1.

**The crowd takes any accent.** The pool starved because the principals had
claimed nearly every English speaker in VCTK — but the shortage only forced
the question. A crowd in a British dock town *should* be mixed, and a uniformly
English one was the wrong picture regardless of supply.

### What it cost, and the part worth keeping

Twenty-four hours, six defects, each found by shipping something broken.
`voice-pipeline-plan-2026-07-31.md` has the full account and the nine
invariants the pipeline now holds. The one-line version: **there was no way to
ask the corpus a question except by running a forty-minute fetch**, so every
fact about VCTK was inferred from side effects. That is why every estimate was
wrong.

Jafar caught the worst of them by ear — four "different" candidates for Lena
that were the same speaker four times. The rule stopping a speaker being shared
BETWEEN characters said nothing about one character taking the same speaker
repeatedly, and VCTK stores ~400 consecutive utterances per speaker.

**Instruments built as a result**, and these are the durable output:

- `--inventory` — reads the corpus speaker table from metadata only, no audio.
  Built, **not yet run**.
- `page_check.py` — drives the listening page in a 390px browser. Twelve
  assertions. Found six faults in a page that had been shipped.
- `mp3trim.py` — frame-accurate mp3 cutting, no re-encode.
- `tools/docs-check.py` — every design doc must declare LIVE / SPEC / LOG.
- A per-character CI guard: any character that had clips and now has none
  fails the commit, whatever the totals say.

### Open, and honest about it

- **Windows CI is RED** (run 154). `nightNotDarker` measured night at 0.136
  against noon's 0.135 — a real render issue, undiagnosed. `suspicionActs` was
  unsatisfiable (staging on day 10, CI ran 9 days) and is fixed by running 11.
  Which of the two is still failing is not visible in the log tail.
- **M16 Phase 2 is built but partly ungated.** `deedSlotSets` is reported and
  not asserted, deliberately: setting a threshold without a measured value is
  the mistake this project keeps making.
- **Phase 2 remainder** — alarm propagation, the witness ghost, routing
  witnesses on the real map.
- **15 named characters have no dedicated voice**, Ossei among them, and he is
  an Act III condition. They fall through to crowd voices.
- **Bark curation** — 336 unique authored lines across 24 slots. **Mine, on
  Jafar's instruction 2026-07-31** (*"you will do that, and do it thoroughly
  and properly"*). The 2,268 other entries in `barks.json` are `telling ||
  reply` combinations, derived rather than written.
- **Non-verbal voice (grunts, pain, exertion)** — **DECIDED 2026-07-31: the
  free CC0 route**, not a purchase and not a recording session. Jafar: *"free
  obviously. i won't be recording anything."* Needs a source adapter on the
  existing fetch pipeline.

## 2026-08-01 — the reach check found more wiring than the hand analysis had

Moved out of `roadmap.md` when that file crossed its 400-line LIVE limit. The
finding is worth keeping; it is not the present state.

An afternoon's manual gap analysis over 61 public Core APIs said roughly 40 had
no call site. `tools/ReachCheck` ran the same question as a call-graph walk in
a second and said **131**. Thirty-eight of those were M16 phases 2–4 —
`Brandish` 0, `MayFrisk` 0, `Acquire` 0, `Traceability` 0 — built, tested,
green and unreachable, which is this project's oldest failure mode.

The lesson is the ratio rather than either number: a careful human sweep found
under a third of it, in an afternoon, and was believed. The ledger stood at
**89** when the phases landed and can only count down — wiring an API without
deleting its row fails the build too.

## 2026-07-31 — a blocker that cleared and nobody noticed

Moved out of `roadmap.md` when 17.6 closed and the file hit its 400-line LIVE
limit. The mechanism is the part worth keeping.

`production-plan-audio-art.md` §4 item 5 put building and prop packs on hold on
2026-07-28 pending the character direction. Mixamo landed on 2026-07-30, which
unblocked them, and nothing said so for two days.

A blocked item that lives only in a spec unblocks SILENTLY and then waits
forever — there is no event, no check, and nobody re-reads a spec to find out
what became possible. That is the argument for the M17 table in `roadmap.md`
carrying every item's state rather than pointing at the document that holds it.

---

## seeing the game, 2026-08-01

Moved out of `roadmap.md` when it crossed the 400-line LIVE limit. Both entries
were true when written; the first is now closed and the second is chronology.

**17.1 was the risk and it was worth naming precisely** (written before it
closed). No `.meta` files are tracked anywhere in this project, so FBX import
settings are not under version control, and Unity does not default a model to
Humanoid. `CharacterRig` needs Humanoid — the Avatar is the contract,
deliberately, because Mixamo's bone names are stable right up until somebody
re-exports from Blender. Committing import settings changes a project
convention, and it was the one piece that could not be checked locally at all:
Unity decides, and the first evidence is a CI screenshot.

**Closed 2026-08-01.** `CharacterAudit: models=44 humanoid=44
validHumanAvatar=44`, and then `bodyUp=1.000` once `bakeAxisConversion` was set
— without which the body imported Z-up and lay on its back in the road, which
is exactly the class of fault only a screenshot could show.

**The project can now see itself, as of 2026-08-01.** Every Windows build
commits four stills and a `verdict.txt` to `game-design/sim-shots/`, and that
loop found, in its first hours: names drawn over rooftops, street signs reading
as doubled glyphs, a noon sky at 2.6x the scene mean, a crowd dressed off the
whole colour wheel, and a wardrobe 1.83x over its designed share of olive. It
also cleared three textures and one set of wheel proportions that I had
condemned from a low-resolution frame and that were correct all along.

**And then the limit of it.** Three faults were found by a human opening one of
those stills and none by a gate: a hand lookup that could only see one body
tier, a white capsule drawn over the bought body, and that body lying flat on
its back. In the third case I read `playerPrimitive=False` off the done-line and
called the body confirmed while the noon frame in the same directory showed it
magenta on its back — having written myself the instruction to open it. That is
why `CLAUDE.md` §4 now says to read every still BEFORE any gate, and never the
gate instead of the artifact.


---

## moved out of roadmap.md, 2026-08-01

The strategy rewrite (KCD2 immersion rather than a systems spike) added two
milestones and pushed the LIVE plan over its 400-line limit. These three
sections are REFERENCE and HISTORY rather than plan, so they moved here instead
of the limit moving. The scope call in particular is superseded: it argued for
two districts and `ledger/Recurrence` measured three as better.

## The testing system

Researched and planned 2026-07-31 on Jafar's instruction. Five layers, specced
in `testing-system.md`:

| | layer | catches | when |
|---|---|---|---|
| 1 | **Reach** — every public Core API has a caller | *built is not running*; ~40 APIs with no call site | before M16 ph.3/4 land |
| 2 | **Shape** — text, audio and assets are well-formed | 21 of 42 gossip templates rendering a lowercase sentence under 2,883 green tests | before M16 ph.3/4 land |
| 3 | **Pixels** — golden-frame perceptual regression | a shader change turning every night purple | **ledger landed**, tolerance unmeasured |
| 4 | **Time** — determinism, 500-day soak, save/load chaos | a bug that is currently unreproducible | **landed**; replay-log half open |
| 5 | **Adversary** — input fuzzing, a bot that plays badly, exploit search | softlocks and dominant strategies | **router+validator landed**; bot open |

**All five layers now have a gate, and `verify.py` runs every one on every
commit.** What each found, since a layer that found nothing is a layer nobody
has watched fire:

- **3 PIXELS**, half. Twenty frames were fingerprinted per run and reported
  through two channels this environment cannot read; they now go to committed
  `sim-shots/frames.tsv`, with `tools/frame-drift.py` printing per-shot deltas
  into `verdict.txt`. **Open:** the GATING half — a tolerance is a threshold and
  the rasteriser's noise floor is unmeasured, which is how `nightNotDarker`
  failed at 0.136 against 0.135. **Depends on** two clean runs.
- **4 TIME**, both gates. `SaveChaos` fuzzes the codec, `Soak` runs 500 days
  twice comparing per-day digests. **Seven player-reachable faults**: two
  exceptions the front end could not catch, a save loading into day 0, an int
  overflow flipping a job count negative, a purse and a patience bypassing their
  own clamps, and an unbounded `SuspicionTracker.Reasons` — found by the growth
  SERIES, not a total, since rumours oscillated 9–74 in the same run because
  gossip decays. **Open:** replay from a seed plus an input log (Unity).
- **5 ADVERSARY**, the boundary. Twenty families, five seeds, 700 rounds, and
  **not one routed a verb the catalogue did not contain** — the one function
  written as a security boundary was written correctly. Found a public
  off-by-one (`ResponseValidator` appended its ellipsis after cutting to
  `MaxChars`; measured 901) and a fault in itself: every family asserts a
  REFUSAL, so a router refusing everything scores perfectly. Positive controls
  go first now. **Open:** the bot that plays badly (Unity).

Beside them: 2,965 CoreTests, **21 mutation-testing specs** (`breakrun.py` —
most studios do not), 20 gated sim claims, an LLM-vs-LLM playtest and
Monte-Carlo balance.


## The ship checklist — every category, and who owns it

**This table exists because the roadmap did not have one, and nine categories
were missing.** A milestone may not claim a category it has not named, and a
category with no owner is a gap whether or not anybody is thinking about it —
`built is not running` one level up: a category with no milestone looks
finished in a roadmap exactly like a system with no call site does in review.

| | owner | state |
|---|---|---|
| Simulation systems | M16, M18–M21 | the moat; in progress |
| Character models and animation | 17.1 | **imported and attached**; player only |
| Voices | 17.2, 17.3 | 19 references picked; generation blocked on scope |
| Barks | 17.4 | 2,604 lines enumerated, curation mine |
| Foley | 17.5 | decided free, not sourced |
| Surfaces and textures | 17.6 | **12 CC0 albedos, attributed, verified in a render** |
| Props, buildings, vehicles | **17.7** | vehicles done; buildings are blocks, need ground floors |
| Weapons and held objects | 17.8 | **drawn from the hand, on either body tier** |
| Fonts and icons | 17.9, **22.4** | **PT Sans ships with its licence**; icons nothing |
| Music | shipped M13 | procedural layer, running |
| Lighting, weather, post | shipped | noir pass, grain, bloom, AO, reflections |
| UI and menus | shipped | text-only, no icons |
| Save / load | shipped | atomic, slots, backup recovery |
| Onboarding and pacing | M20 | not started |
| Performance | M22, Layer 4 | gated per run; frames.tsv starts the trend |
| Platforms | M22 | Windows green, macOS compiles, never run |
| Controller | M22 | 28 `Input.*` calls to move |
| Accessibility | M22 | caption channel only |
| Testing | testing-system.md | **all five layers gated**; 3 reports, 4–5 partial |
| Credits, licences, attribution | **22.1** | nothing, and CC BY 4.0 requires it |
| Localisation | **22.2** | no infrastructure, no decision on record |
| Packaging and release | **22.3** | nothing |


## The scope call, decided

**Finish two districts to a shippable standard; leave the other five at current
fidelity.** Not a cut — a focus. `the-gap.md` §4's argument was that gossip is
*better* in a small world where the same faces recur, and M17's cost scales
directly with district count. Seven were built; two get finished.

*Jafar, 2026-07-31: "fine with the district thing."* The heading said "still
open" for a day after he closed it, which is how a live doc goes stale.


**The lowest scores on the board are all the same half of the premise.** The
design doc's genre line is *"open-city crime sim × slice-of-life social RPG"*
and the slice-of-life side reads 5 to 25 across every dimension.

| dimension | now | target |
|---|---|---|
| Home / base that reacts | 10 | 50 |
| Family & dependents | 15 | 50 |
| Companionship — who is with you | 15 | 55 |
| Self-presentation / lifestyle | 25 | 35 |
| Vice & addiction | 5 | 40 |

**Why it matters more than its scores suggest.** A belief network is only
frightening if the people in it are people you would miss. The game can
currently model the street knowing you are a criminal, and cannot model
anybody being at home waiting for you. Every consequence the moat produces
lands on nothing.


**17.2 WAS NEVER BLOCKED ON JAFAR — I HAD MULTIPLIED INSTEAD OF MEASURING.**
This paragraph said the work needed a scope decision from him because the bark
bank is 2,604 distinct lines and six crowd voices makes **15,624 clips**, all
nineteen makes 49,476, and on a CPU runner that is CI-days.

That number is a cross product, not a demand. `VoiceBank.ClipName` keys on
(voice, exact text), so a line is only ever synthesised for the voices that
actually say it — and the sim now prints what a real week asks for:
**`clipsAsked=276 voicesAsked=6`**. Fifty-six times smaller than the figure
this file used to justify escalating, and an afternoon's work rather than
CI-days.

Still true and unchanged: LLM-authored dialogue can never be pre-generated,
because the text is not known until it is written. That is a property of the
design, not a blocker on this item.


**REPLACED 2026-08-01, and the old line is worth keeping visible because
following it faithfully is what went wrong.** It read: *"Be incomparable on
three axes and honest about the rest — social memory 93, consequence persistence
95, information 90"*, with Disco Elysium against Baldur's Gate 3 as the
precedent. That is a DIFFERENTIATION strategy, not an immersion one, and pursued
for weeks it produced a 95-scoring consequence engine attached to a town of
silent boxes: 447 lines of speech wanted and zero played, every character except
the player a coloured box, and the immersion milestone repeatedly losing its
slot to systems work. Jafar's actual goal, stated at the start and restated on
2026-08-01, was always to get as near as possible to the games he rates — KCD2
and GTA5 — with AI-heavy means.


**Why first, ahead of every system below.** A player judges a game in ninety
seconds. Right now it animates boxes and speaks in silence, and none of the
depth below is visible in those ninety seconds. Almost nothing here is new
design — every item has a working system underneath already.

## M16 — what shipped, in full *(moved out of roadmap.md 2026-08-04)*

A crime game in a city that perceives, reacts and remembers. Spec:
`weapons-spec.md`. Phases 1, 1b, 2, 3 and 4 all shipped and gated: vision and
hearing, witnesses with an ID ladder and a delivery window, misattribution,
melee and concealment and the frisk, provenance and disposal. Phase 5 is
firearms and is M23, deliberately last.

The §4.7 gate is asserted by the sim rather than argued for. Only lint,
ShapeCheck and CoreTests run in the dev container.

Moved here because roadmap.md is a LIVE plan capped at 400 lines and a shipped
milestone's detail is chronology. The cap fired the moment M21 gained the
paragraph describing what actually landed, which is the cap working: the plan
stays about what happens next.

---

## M17.1 — the upside-down player and the arms, closed 2026-08-03

Moved out of `roadmap.md` on 2026-08-04 because it is chronology, and rule 10
says the plan holds the plan. Kept whole: two of the three lessons in it are
about instruments certifying what they cannot see, and that keeps happening.

**The standing-up half is CLOSED, 2026-08-03, and closed the way it should have been the first time — by opening `review_day1_noon.jpg` and seeing a figure on its feet, with `preHeadAboveHips=0.520` and `headAboveHips=0.522` agreeing on either side of the solve.** It took eight builds and a four-stage bracket because `bodyUp=1.000` reads the ROOT and structurally cannot see the skeleton, so the first close was certified by an instrument blind to the fault. Two independent faults in our own rig, both ours: the rest-restore asked whether an Animator EXISTED rather than whether anything was DRIVING the pose, so the body composed onto its own previous output for ever; and `Swing` composed onto a live rotation instead of assigning from a rest one. **The arms are closed too, 2026-08-03.** They were never a rig fault: nothing had ever animated this body. Forty-one clips were imported and audited every build — `clips=44` reported as a success for days — and not one was ever bound to anything. A locomotion blend tree now plays idle/walk/run, and the giveaway was a reading of EXACTLY 90.0° on both sides of our solve: a clip being evaluated lands anywhere, not on the bind pose to a tenth. `CullUpdateTransforms` skips retargeting when no camera reports the renderer visible, and the sim renders on demand into a RenderTexture rather than running a live camera, so the body sat frozen between shots. `AlwaysAnimate` on the one bought body. `animClipTime=473.97` where it would have been 0, and the noon frame shows arms at the sides. **Note the metric changed meaning:** `liveArmDrop` is worst-over-run, which asked "do they EVER stick out" of a static bind pose and now catches the peak of an arm swing — 63° is a walk cycle, not a fault. **Still open: the figure reads bare, and that is 17.1b.**

---

## Two post-mortems moved out of the plan, 2026-08-04

Both record a decision that still stands; neither is the plan. Moved when the
M16 fighting correction took `roadmap.md` over its 400-line budget, because
trimming the new fact to keep old chronology would have been the wrong way
round.

**Replaced 2026-08-01.** The old line was *"be incomparable on three axes and
honest about the rest"* — a differentiation strategy, and following it faithfully
produced a 95-scoring consequence engine attached to a town of silent boxes.
Post-mortem in `roadmap-history.md`.

**17.2 was never blocked on Jafar** — the 15,624-clip figure was a cross
product, not a measurement. Real demand is `clipsAsked=276 voicesAsked=6`, an
afternoon. Post-mortem in `roadmap-history.md`.

**The visual target is coherence, not fidelity.** `production-plan-audio-art.md`

## 17.1b — the trap that had to be cleared before a single walker body attached

Moved out of `roadmap.md` on 4 August under rule 10: the live plan stays under
400 lines and this is an account of something solved, not a statement of what
happens next.

The prerequisite is the part worth remembering: `TryAttach` publishes statics that five clauses of the `bodies` gate read as THE PLAYER's, so attaching walkers without separating them first would have made all five silently describe the last walker, and a corrupted gate reads exactly like a passing one.

The shape is worth keeping because it is not specific to bodies. A function
that publishes statics, called for a second subject, silently re-points every
reader of those statics at the new subject — and a gate reading them cannot
tell that it has changed what it is about. `TryAttachExtra` saves and restores
the whole published set for exactly this reason, and the five clauses it
protects are named in `RealBody` itself.

## 17.7 — three false "still open" claims in one roadmap row

Moved out of `roadmap.md` on 4 August under rule 10. Each of these was a
statement that something was MISSING which was not missing, and the first one
cost a wasted change — a second door system built in Core, with four tests,
against a wall that already had a door.

**"Still open: cornices, and doors as geometry" was wrong on both counts and cost a wasted change on 3 August** — `GroundFloor` has been building a fascia, a recessed door and a parapet cornice on every street-facing mass for as long as it has existed, three lines apart, and I wrote a second door system in Core with four tests before reading it. **And "nothing distinguishes a shop from a house from a warehouse except the sign" is also wrong, checked 2026-08-04 by opening `GroundFloor`.** Premise kind already drives the fascia (a shop gets a signboard band, a house deliberately does not — "a signboard over somebody's front room is the fastest way to make a residential street look like a high street"), the door WIDTH via `Dressing.DoorWidth`, and the door HEIGHT — a warehouse gets 3.2m because a loading door has to take a cart. Third false "still open" in this row: it previously claimed cornices and doors were missing when both were built three lines apart, and that one cost a wasted change.

The reusable part is rule 3's corollary: a doc saying something is missing is
an ANALYSIS, not evidence, and its "still open" lists decay exactly like
comments do. Grep is not enough either — grep found the call site and I read
past it. Open the function.

## M16 — why "shipped" hid a system that has never run

Moved out of `roadmap.md` on 4 August under rule 10, which caps the live plan
at 400 lines so it stays scannable. The finding stays in the live row; this is
the account of how it stayed hidden for as long as it did.

**"SHIPPED" IS TRUE OF THE CONSEQUENCE HALF AND NOT OF THE FIGHTING, found
2026-08-04 by reading the code rather than this table.** A killing is staged
as an EVENT — `ViolenceHost` sets a lethal flag and resolves the witnesses —
and everything downstream of that genuinely runs. There is no exchange of
blows anywhere: `Available`, `Resolve` and `StaminaCost` model stamina,
footing, guarding and reach, are tested, and **`Combat.` occurs exactly once
in the whole Game layer**, on an unrelated stamina line. Nothing constructs
a `Fighter`. It hid here because the gate certifying M16 asks about
WITNESSES, and a fight that cannot start still leaves an empty alley empty —
and on the reach ledger because only `Breathe` has a name that does not
collide with another Core type's method, so a four-method gap showed as one.
Fixing it is a milestone and it needs a done-condition measuring a FIGHT.

**The risk it exposed sets the pace of everything below:** the Game layer does
not compile locally, so every wiring change costs a ~28-minute round trip.

---

Two mechanisms kept it invisible and both are reusable. The gate certifying
M16 asks about WITNESSES, and a fight that cannot start still leaves an empty
alley empty — a gate can only ever fail on the question it asks. And on the
reach ledger the four-method gap showed as ONE entry, because only `Breathe`
has a name that does not collide with another Core type's method and the reach
tool matches by name.

---

## 2026-08-05 — what the screen table used to carry

Moved out of `roadmap.md`'s screen table, which had grown two cells of four
thousand characters each — a diary in a table row, which is rule 10's failure
mode in miniature and makes the one document that is supposed to be scannable
in a minute unscannable. The reasoning is worth keeping; it is not worth
keeping where the plan lives.

### M17, as the screen table carried it

| **now** | M17 — the game looks and sounds like itself | 17.4/17.6/17.9 closed · 17.7 part done · **17.1 CLOSED, and 17.1b is no longer waiting on anybody. Jafar ran the fetch on 4 Aug: eight real bodies landed, `bodyChoices` went 2 to 10, all fifty-two models carry valid human avatars, and the noon frame shows the player as a human mesh with limbs and a walk pose rather than a box.** **The textures are fixed and confirmed: extraction pulled 54 of them from 10 of 10 models, `bodyKeptMats=1`, and the noon frame shows skin, hair, a white top and yellow trousers where the day before there was a flat blue silhouette.** Unity does not unpack embedded FBX media and had never been asked to. **Foot IK runs** — 46,786 frames, both feet, none undriven. What is open is the COST and the SAMENESS. 44 skinned bodies took the frame budget red, so the set is bounded at twelve and spent on the twelve NEAREST rather than the twelve first — the noon frame has real people in the foreground where boxes stood. But ten body models dress forty-three named people, so at least two on screen always share one, and the frame shows two women in identical trousers with one of them the player. Texture extraction silently switched the wardrobe off the morning it landed — the paint step reports "nothing to paint, all renderers came textured" — so the models are now the only thing telling people apart. A per-person wash over the kept texture is the mechanism, and it has now been wrong twice. The first attempt reported one renderer tinted against 1,586 body attachments because I had put its counter inside the save-and-restore set that protects the player's gate clauses. **The second ran 5,334 times and changed nothing for a third of the city**: it took the band's hue and half its saturation at value 1.0, and black and grey share a hue range and a saturation floor, so VALUE is the only axis separating a fifth of the street from a sixth of it and value was the axis being discarded. Replicated over the real roster, 39% of people washed to within 5% of white — and a multiply by white is the identity, so the counter proving the system ran could never tell it running from it doing nothing. Fixed in `Core/Wardrobe.Wash` with the floor taken from a swept series, a CoreTest holding both ends, and `bodyWashWhite` as the reading that would have caught it. **The wash then measurably worked and the frame still looked loud**: near-white cases fell from a predicted 39% to a measured 7.7% of 4,904 washes, and the two women are still in bright yellow — because the wash maps the wardrobe onto [0.45, 1.0] and no multiply capped at 1.0 brings a value-0.9 albedo under a 0.46 ceiling. `bodyAlbedo` measures the sheets so the ceiling comes from evidence. **AND THE SAMENESS HAS A NUMBER AT LAST: fourteen people on screen wearing eight faces.** Which sent a grep at what else varies, and found that the bought bodies were scaled by height alone while the thirteen-box mannequins had always varied in build — so upgrading a walker to a real body LOST a shape trait, on the twelve nearest people. Breadth, cadence and loop phase are wired and CONFIRMED — `bodyBreadths` lists twenty-two distinct values from 0.87 to 1.16 and `phasesSeeded=45`, so build varies and nobody steps in lockstep. Head scale followed once reading the file showed the Animator writes no scale at all. The limp is the fourth and is NOT wired, and reading it found something under it: the rig ASSIGNS a driven body's hip position from a rest pose while COMPOSING its rotation, so the bought animation's vertical rhythm is discarded and replaced by a phase the clip does not share. `hipOverride` measures it before anything touches it. **And the wash's anchor is per-material now**: `bodyAlbedo` read seventeen sheets from 0.04 to 0.78 against a 0.46 ceiling, eight of them above it, so multiplying by wardrobeValue/albedo lands a garment on its band and needs no constant — `bodyWashWhite` went 22.3 to 37.1 and the noon still shows muted olive where the trousers were bright yellow all day |

### M18, as the screen table carried it

| **also now** | M18 — the second life | family verified running · **the companion's cause is found, 4 Aug: she was never walking too slowly, she had no idea where the player WAS.** A walker learns the player's transform from one proximity sweep, and both the escort's target and its catch-up speed are guarded on having it — so falling behind is what stops you following, and it compounds. Bound at recruit time now; the gate had read `dist=29.4m` through a catch-up-speed fix that could not have helped. **CONFIRMED GREEN 4 Aug on `180f626`: `companionAtRecruit=9.2` against the 23.8m that made it red, `companionDist=4.2` at the deed, `deedWaitedDays=0` — she is recruited near, so the two-day wait never has to fire.** The escort was being picked by walker-list position, wherever she happened to be standing in the city; she is picked by proximity now · vice and lifestyle deferred |

### And one claim in it is now settled by measurement

The M17 cell ended on the wardrobe wash and "the noon still shows muted olive
where the trousers were bright yellow all day". On 5 August I read
`review_day1_noon` again, saw bright yellow trousers, and went to check the
palette rather than argue: seven of the eight bands top out between 0.09 and
0.55 saturation, the only hot one is `shellsuit` at 0.62-0.85 with a weight of
one in thirty-one, and `shellsuit` sits at hue 0.82-0.90, which is magenta. No
band covers 0.12-0.36 above 0.26 saturation, so a saturated yellow cannot come
out of the table at all. `crowdSatRange=0.06..0.73` in the landed verdict is
the shellsuit band doing its job.

Which means the wash story here is probably right and my eyes are the
unreliable instrument — the sixth thing condemned off a still and cleared by a
number. The note is in `Core/Wardrobe.cs` beside the band table, where the next
person will hit it before re-opening the question.

---

## From the queue, 7 August — what build `4e3eef3` settled

Moved out of `queue.md` to keep it under the 400-line limit for a live
plan. The open questions stayed behind; this is the settled part.

#### WHAT `4e3eef3` SETTLED — THE LAW WORKS NOW

- **THE POLICE CAN COME AFTER YOU, FOR THE FIRST TIME EVER.** `homHoldsIt=27`
  of 27 stored (was 0 of 21), `homNamed=27` (was 0), `homPressure=7.50`
  (was 0.40), **`homInquiry=Manhunt`** — a stage no run has ever reached.
  `actThree=True ending=BurnBoth` both unmoved, which is what the staging
  after `AuditClosed` predicted. The capital-letter fix did all of it.
  **OPEN, AND IT IS THE NEXT THING:** `inquiry=Procedure` on the done line,
  which is the stage at the END of the run against `homInquiry` at the
  killing. So it escalated and settled back, `redirected=0 pointedAt=nobody`
  so the redirect is not the cause, and I do not yet know what is. Two
  candidates: rumour confidence ageing below `TestimonyGrade`, or `Pressure`
  reading a day. **Do not assume heat fading by design — measure it.**

- **THE SUCCESSION MOVED ONE LINK ON.** `joeyRuns=True`, and `successorWhy`
  now lists only Sam and Rocco — **Joey has dropped off it, so he passes
  `CouldHold`.** `handed=False` still, so `ReadySuccessor` returns a man and
  something after it refuses. That is a different function and a much smaller
  search than the 138 runs of nothing.

- **THE LANES WORKED, AND I HAVE BEEN READING A PEAK AS THE STREET.**
  `crowdGapMedian` 0.26 → **0.45**, the best ever recorded — and
  **`crowdHuddle=11`, the MEDIAN huddle, against a recent median of 20**
  (series 11, 20, 31, 21, 20, 25, 29, 20, …). The typical street is now
  eleven people within two metres and comfortably spaced.
  **`crowdHuddleWorst=40` is one instant in fifteen days**, and this file has
  led with it for four builds as though it described the street. That is the
  peak-as-description fault, on the metric this project has spent the most
  time on. Both numbers matter and neither answers the other.
  The branch counts also refute my own framing: `steerDirect=52193` is 87% of
  all steering, `steerJunction=1564` is 2.6%, `steerOrigin=0` — so the origin
  fallback never fires, that hypothesis is dead, and spreading the 13% who
  route via a shared point is what moved the median. **What is left is a
  transient crossing at one instant, not a permanent crush**, and it should
  be judged against a still before any more work goes into it.

- **THE LEAN IS A WALKER, NOT THE PLAYER.** `leanWorstIsWalker=True` with
  `leanTypical=-7.1`. One body in a crowd of fifty, bent over, while the
  street stands upright — nearly invisible. Drops down the list.

- **THE RELIABILITY PLANT WORKS NOW.** `reliabilityFiled=1 dropsSkipped=3
  reliabilityRead=[Slipping after 2]`. Stopping on the outcome rather than at
  a fixed count of two is what did it: it needed three skips to land two
  consecutive ones.

- **THE SUMMONS IS NOW HONESTLY MISSED.** `summonsTaken=0` still, and
  `summonsMissWhy=[a line was live and he was not near it]` — but that
  sentence now describes NINE AT NIGHT rather than breakfast, which is the
  whole point of the same-instant fix. The mechanic is right and the
  condition is unplanted. **Plant it next: stand the player at a live box at
  the ring hour.** Held back deliberately so a moving `summonsTaken` could be
  attributed; it did not move, so the plant is now unambiguous.



## Moved out of `queue.md`, 17 Aug — settled, kept for the reasoning

The queue is capped at 400 lines by `docs-check` precisely so this
migration happens instead of the file becoming a diary. These blocks
were all closed work.

### THE CLIPS LANDED AND THE STREET IS ALIVE.
Jafar's Mixamo harvest came in complete — 54 slots, zero missing —
and replaced two absurd survivors (walk start/stop were FASHION
CATWALK turns). Ten clips had no consumer; they have one now. People
talk, argue, lean, look bored, smoke outside the pub, work counters,
carry shopping. `activityPeak` 1 -> 18 once the states went on ALL
FOUR controllers rather than the canonical one. Old-person gait is
live off `idle_old`/`walk_old`, and the crowd stops being boxes
within 14m at the same cap.

Also closed: the intermittent traffic red (a cab idling on a rank
spur, which is a LANE, so `OnRoad` called correct behaviour a fault —
the gate was measuring the model), zebra crossings with belisha
beacons, cables that only hang where two buildings hold them, the
width-aware bubble cap, every chimney smoking, and the two white
pills at the kerb.

THE PILLS COST FOUR BUILDS AND THE LESSON IS RULE ONE. Identified
three times off a JPEG — capsule, default material, smoke — all three
wrong. Nine lines of numpy over the committed frame answered it in one
turn: two tall white blobs, and the city builds exactly two pillar
boxes at 0.48x1.1m. Their red was a property-block tint that never
reached the renderer; it lives in a shared material now. **MEASURE
THE FRAME** — it is cheap, it is already in the repo, and on 17 Aug
it did it again: three more wrong readings of one walker, killed by
counting magenta pixels (zero) and then by measuring the rig.

NEXT: T3 queue points and standing destinations; then the freeze
decision (recommendation KEEP, unchanged and now stronger); then the
street-spec topology re-plan, whose case is the ~110 parcel ceiling.


### Closed 17 Aug — the pink figure

1. **CLOSED — the pink figure was never a fault.** Three explanations
   went out unchecked and measurement killed all three: zero magenta
   pixels, not a broken mesh, and not cartoon proportions (7.63 heads).
   It is Sporty Granny as authored. The measuring instead found two
   models nobody had looked at — The Boss 0.762 and Big Vegas 0.761
   against a realistic cluster of 0.806–0.837 — now kept out by
   `Core/Proportion` rather than a name list. Pool 8 -> 6. **Owed:
   more realistic bodies, a Mixamo pick and Jafar's step** — sameness
   got worse to buy this.



### Moved out of `queue.md` — playtest push and live-speech state

### THE PLAYTEST PUSH — sequence, not calendar (Jafar: "forget exact
### days, just keep the sequence")

**The plan is `playtest-plan.md`** — MacBook Air, three players. Order
there wins over order here. Everything below stands but YIELDS: live
speech is parked (no DirectML on the machine) and the visual and
playability work takes the slots. The deterministic retry design, the
constant-gate plants and the frame-gate CPU work resume after.

**SETTLED, so it stops being re-litigated: the daylight grade.** Two
iterations, judged on matched dry-noon pairs rather than per-day
medians (weather is not pinned between runs, so a median compares
different weather). Worst noon came 0.494 → 0.446, bright pixels
48% → 39%, nights held 0.10–0.13, brick still legible. Further cuts
start re-crushing the brick. The grade stays.

**Still owed from that push:** Jafar's Mixamo session then per-physique
controllers; freeze, final builds, smoke test. The glowing box in
day2_night's plaza is the bar sign's bare back face — one-line
material fix, behind the playtest-critical work.

### LIVE SPEECH — PARKED until after the playtest

State in one paragraph, full accounts in the git log: the C# side
speaks on Jafar's card (~1.1x realtime, pops fixed, 23 voices cast).
The "ah" filler is a deterministic bad draw per (voice, line), so the
fix is DETECT AND RETRY WITH THE SEED PERTURBED — designed, not built.
Streaming and fp16 are closed (worse, measured). `put-voices-in-build.py`
is selftested but has NEVER run against a real build; that is the first
item on resuming. No live speech on the playtest Mac (no GPU) —
recorded bank only, which the verdict's speech keys already measure.



### The two perf fixes, in full — one worked, one did not

   **THE TWO PERF FIXES, MEASURED — ONE WORKED, ONE DID NOT.**

   `traffic`: 4.67 -> 4.27 -> **2.23**. Hoisting the road heading out
   of the per-hazard loop roughly halved it, well outside the prior
   spread. One sample; treat as strong, not settled.

   `npcs`: 9.36 -> 8.43 -> **8.63**. Did NOT move. The broad-phase in
   `StepApart` works exactly as designed — `crowdApartPairs=5288` of
   `crowdApartCalls=63298`, so of ~3.3M candidate pairs only 0.16%
   reach a square root — and the time stayed put anyway. **So the
   commit title "that is why the street is empty" was overstated and
   is corrected here.** Removing the sqrt did not help because the
   ITERATION is what costs: the sweep still visits every walker for
   every walker, and only the work per visit got cheaper. Still O(n²),
   just with a smaller constant. A spatial bucket is the real fix and
   is not yet written; the cost of the crowd is still somewhere inside
   `Tick` that nothing has isolated.



### The kit building measurements, in full

   **MEASURED — eleven fetched, `tools/prop-dimensions.py`, and the
   answer is NOT the terraces.**

       building-a              733 verts   88 x 129 x  94
       building-b              762         97 x 129 x  94
       building-type-a         707        130 x  83 x 103
       skyscraper-a            978        136 x 288 x 136
       low-detail-building-a   104         50 x 200 x  50
       low-detail-building-c    90         50 x 225 x  50

   Read the RATIOS: kit units are not metres (its `sedan` is 150x145x255
   and a sedan is 4.2m long) and `TrafficHost` already rescales a kit
   mesh on instantiate, so proportion is what decides.

   **Every full building has a roughly SQUARE plan** — 88x94, 97x94,
   130x103. Our terrace parcels are about 1:2, narrow frontage and
   deep. These are detached standalone blocks and cannot be terrace
   units at any scale. That closes the "just switch to them" option on
   geometry rather than on taste.

   **The low-detail set is the find: 90–112 verts at a 1:4 tower
   ratio.** Trivial against a scene already carrying ~280k vertices in
   bodies alone, and exactly the shape a DISTANT SKYLINE wants — which
   is where the queue guessed our system was weakest, now with evidence
   under it. That is the next step, not a terrace swap.



### The street-density series, in full

   **MEASURED, THREE RUNS: `5/2/52`, `8/5/55`, `3/2/52`** — in shot /
   within 25m / alive. Three to eight people visible, two to five close
   enough to read as a person. **NOTHING CHANGED DENSITY BETWEEN THEM,
   so that spread is the instrument, not progress** — the shot stands
   somewhere different each run. A camera sees ~60 degrees, so bodies
   scattered round the player put ~1 in 6 in frame however the cap is
   set, which is why the cap is not the lever it looks like.



### The perf hunt, in full

   **THE COST IS NPCs AND TRAFFIC, NOT SUN.** `sun` has read 0.91,
   3.15 and 1.26 across runs that changed nothing relevant to it, so
   the old "sun is a quarter of the budget" line was reading noise.
   Frame numbers move with the runner too, so compare within a run.

   **PERF, MEASURED.** `traffic` 4.67 -> 4.27 -> **2.23**: hoisting
   the road heading out of the per-hazard loop roughly halved it. One
   sample, so strong not settled. `npcs` 9.36 -> 8.43 -> **8.63**: did
   NOT move, though the broad-phase drops 99.8% of pairs before any
   square root (`crowdApartPairs=5288` of `crowdApartCalls=63298`). So
   the ITERATION is the cost, not the arithmetic in it — still O(n²)
   with a smaller constant, and the commit title claiming otherwise is
   corrected. `crowdApartMs` lands next build and says whether a
   spatial bucket is worth writing at all. Accounts in
   `roadmap-history.md`.

   **CORRECTION — f802928's commit message costs a walker at "~0.58ms"
   by dividing `npcs` by `crowdWalkers=12`.** Wrong denominator: that
   scope ticks every entry of `_npcs`, i.e. `walkers=55`. ~0.13ms each,
   and not flat — the separation term is quadratic in the crowd.

   The comment beside `PopulationCount = 700` also still describes the
   city BEFORE the stretch. Re-read it when the numbers land.



### The body-budget finding, in full

   **THE BODY BUDGET IS SPENT ON WHO IS NEAREST, NOT ON WHO YOU ARE
   LOOKING AT — and that is a game fault, not an instrument one.**

   `streetBodiesSkinned` went 0/3, then 2/6 after re-ranking from the
   camera, then 0/6 again once the camera stepped clear of the parked
   car. The reason is in `SceneAudit`'s near list: `Ch03:1.89m`,
   `Ch02_Body:1.93m` — skinned bodies a metre or two from the lens and
   OUT OF FRAME, beating the four people in shot at 10–25m to all 12
   grants. `NearMetres=34` and `crowdBodyMetres=14`, so the in-frame
   ones are eligible; they simply lose on raw distance.

   **So the still is telling the truth and should not be "fixed".** A
   player standing there sees exactly this: the people they are
   LOOKING AT are mannequins while the budget went to somebody behind
   their shoulder. Biasing the shot's ranking would make the frame
   flatter than the game, which is worse than a frame that shows the
   fault.

   The fix belongs in play: rank the budget with a forward bias, so
   the twelve skinned bodies are the twelve you can see. Not done —
   it changes play behaviour and wants judgement about how strong the
   bias is, which is a decision and not a tidy-up.



### The white pills — five wrong identifications, in full

   **THE WHITE PILLS ARE STILL UNIDENTIFIED — AND THE PREVIOUS COMMIT
   SAID OTHERWISE, WRONGLY.** 19f0cfd claimed `bodyAlbedo` had been
   naming them all along. It had not. `AlbedoValueOf` is called on
   `m.mainTexture` of a REAL BODY's material (`RealBody.cs:1100`), so
   that series measures the brightness of skinned Mixamo TEXTURES —
   not the pale blobs, which appear in frames where
   `streetBodiesSkinned` is low. If anything the evidence points away
   from skinned bodies. **Fifth wrong identification of this thing, and
   the first one I published.** The tell I ignored: I found a number
   that fitted the story and stopped checking what it measured.

   What is actually known: the blobs are 73x137 and 23x42 px, aspect
   1.88 / 1.83, fill 0.88 / 0.87 — one object at two distances.
   Run-time `capsules=0` and `undressed=0` rule out a bare primitive
   and an untextured renderer with an instrument that can now see
   walkers. **Intermittent** — the next frame had none, with nothing
   changed. Next step is a number that fires WHEN one is on screen,
   not another look at a still.



### The capsule audit's timing fault, in full

   **AND THE CAPSULE AUDIT USED TO BE BLIND.** `AuditUndressed` ran
   inside `WorldBuilder.Build`, BEFORE any walker spawned, so
   `capsules`/`undressed` were BUILD-time readings of a RUN-time
   condition — every walker begins as a `PrimitiveType.Capsule` that
   `Mannequin.Build` strips. Now re-run at the done line: still 0/0,
   but those zeros finally carry information.



### The rain item, and how it was lost and recovered

1. **THE RAIN READS AS BLACK SCRATCHES AT EYE LEVEL — RECOVERED, NOT
   RESOLVED.** *(on screen — the first player-height frame, dfefd62)*
   From the elevated review camera the rain pass looked fine; from the
   player's own eyes the sky is dense dark striation. Likely sized for
   a downward view: read streak width / alpha / length against camera
   pitch. **Cannot be judged on any frame since** — every recent run
   has come back dry, so this needs a run with rain, not another look.

   This item was LOST when the density work replaced it, and came back
   only because a container rollback surfaced the old file. It arrived
   bundled with a claim that the pink figure was error-shader magenta:
   **that half is REFUTED** — the frame holds zero magenta pixels and
   she measures 7.63 heads. Kept apart so the dead half cannot
   resurrect itself the next time this text is found.



### The white pills, full account

   **THE WHITE PILLS ARE STILL UNIDENTIFIED, and 19f0cfd claimed
   otherwise — wrongly.** `AlbedoValueOf` runs on a REAL BODY's
   `m.mainTexture` (`RealBody.cs:1100`), so `bodyAlbedo` measures
   skinned Mixamo TEXTURES, not the pale blobs — which show up in
   frames where `streetBodiesSkinned` is low. **Fifth wrong
   identification, first one published**: it arrived as a NUMBER, and a
   number felt pre-checked. Known: one object at two distances (aspect
   1.88/1.83, fill 0.88/0.87); run-time `capsules=0`/`undressed=0` rule
   out a primitive and an untextured renderer. **Intermittent.** Next
   step is a number that fires WHILE one is on screen. Full account in
   `roadmap-history.md`.


---

## M0–M3.1 as built — moved out of `design-doc.md`, 2026-08-18

The design document carried this record under a heading called "Milestones" that
had said, since 2026-07-25, that `roadmap.md` superseded its numbering. It was a
fossil sitting in the middle of a founding document, and it is chronology, so it
belongs here. Nothing is changed; it is only relocated.

The original section sketched M0–M4. The built milestones diverged from that sketch
by player decision — gossip before scale, the week campaign before the day job.

**Built and CI-validated (2026-07):**

- **M0 — Tech spike.** One code-built city block, day/night, four scheduled NPCs,
  Lena as a full LLM character (card, markdown memory, retrieval, reflection,
  suspicion), automated Windows builds with an in-engine self-test sim. Voice was
  deferred to the vertical slice by decision.
- **M1 — The gossip engine** (was "living block", re-scoped). Person-to-person
  rumour propagation through physical co-location, confidence decay,
  contradiction-driven suspicion, day and night circles; the player's damage-control
  verbs — pay off, lean on, plant doubt, lie low — with trait-decided outcomes; the
  whole cast conversational.
- **M2 — The week** (was "double-life MVP", re-scoped). Nightly outfit drops that
  create witnesses, bar takings taxed by street heat, outfit patience, the exposure
  fuse, win or lose the week, restart. The balance lab (Monte-Carlo bot weeks) tuned
  heat corroboration, money, and the once-per-story denial cap. The full seven-day
  campaign played in CI on every build.
- **M3.1 — The Ledger.** `PlayerKnowledge` belief-state and Ledger UI v0 — "what you
  believe the city knows, never ground truth" — learned only through play, with
  loyal-NPC warnings.

**Scope honesty, as written at the time:** systems milestones are heavily
AI-buildable (code, cards, pipelines). The vertical slice is where taste, iteration
and playtesting — the human's real job — dominate.

---

## The body budget, closed — 2026-08-19

Cut from `queue.md` when the queue hit its length cap. The residue that is
still live stayed there; this is the settled account.

**The complaint** was that the street looked empty at eye level. The cause was
the LOD ranking: bodies a metre behind the camera outranked the people in
shot. The first fix was a multiplier on the squared distance, and it could
never have worked — 1m behind ranks 1 against 20m ahead at 400, and no
multiplier closes that gap. Being behind now costs a flat amount of apparent
distance instead, three quarters of `NearMetres`, which is the band's own
number rather than a new one.

**`bodyLodInShot / bodyLodShotInBand = 87.8%`.** Of the walkers who are both
visible and close enough to be granted a body, seven in eight get one. The
missing eighth is the rank hysteresis working: an off-screen incumbent keeps
its body for two extra ranks, which is what stopped the set churning three
times a second.

**The denominator was the whole argument.** The first version divided by
`bodyLodShotEligible`, which counts people beyond the band who can never be
granted anything, and read 43.6%. The same run, against the walkers actually
in the band, reads 87.8%. And before either, `bodyLodInShot` was a last-wins
field assigned every pass and read at the end — it reported `0 of 1` on a run
with 46 eligible walkers.

**What that left is a different question.** 13.1 walkers in frame per pass and
only 6.5 of them inside the 34m band: half the people you can see are too far
away to ever be skinned. That is band and density, not budget.

**Cost, stated:** grants went 0.74 to 0.96 per pass and stayed, so turning
round is about 30% more instantiates. Read per pass, because run lengths
differ (374, 373, 446).

**Two instruments fixed on the way through.** `bodyLiftedCrowd`'s comment
claimed the opposite of what it counts — true before the `cast` flag landed
and false after — and the capsule audit ran before any walker had spawned.
Both keys kept their names, since they have landed series.

**Perf, settled and retired in the same round:** traffic halved, the
separation sweep priced at 0.8ms against a 12ms budget so the rewrite is not
worth doing, and `sun` shown to be noise.

---

## The review stills were photographs of a wall — 2026-08-19

Cut from `queue.md` when the work closed. What stayed there is the one live
residue: the metric is narrower than its name.

**The finding.** Opening all six committed stills — which rule 4 asks for and
which had not been done in a while — showed `review_day2_noon` as a stone wall
across the right half and `review_day5_noon` as roof and awning slabs across
the middle. A third of the primary evidence this project reads every build
showed almost no street.

**No gate could have said so**, and that is the interesting part. Every one
asks about a SYSTEM — are the billboards aimed, is the text the right way
round, did the bodies get skinned — and all of them pass perfectly on a
photograph of a wall. `review_street` had had a declutter loop since a lamp
column filled its frame; the day stills never got one and were taken wherever
the sim's camera happened to be standing.

**A duplicate was written and deleted.** The first response was a fresh 35-ray
grid, which turned out to duplicate an existing 84-ray one forty lines further
down the same function, with a better exclusion list. Rule 3: when your own
analysis says something is missing, open the file.

**What was actually missing was narrower.** `shotNearFracWorst=1.00
where=[day13_night]` — and `day13_night` is not a picture this build commits.
The sim shoots about twenty times a run and keeps about six, and the
measurement never told the two sets apart, so the worst reading named a frame
nobody can open while the two bad stills went unnamed. It now carries the
per-shot series and a separate worst over the stills that became FILES,
claimed at the write site so one place knows which pictures exist.

**Then the bound, from a run rather than from taste.** `682e676` printed a
run's twenty shots sorted:

    0.00 x13  0.05  0.06  0.10 | 0.37  0.48  0.60  1.00

Cleanly bimodal, so the threshold went in the widest empty stretch at 0.25 —
0.15 clear of the worst good frame and 0.12 clear of the best bad one. The
measurement shipped one build EARLIER with no loop attached, deliberately,
because there was no run to set a bound from.

**Straight back, never re-aimed.** The aim is what the shot is OF, and a dozen
comments across the codebase cite these file names as the evidence for
particular findings; a frame re-pointed to find air would quietly falsify all
of them. Eight steps of 1.5m, and a camera that cannot get clear goes back
where it stood.

**Three mistakes caught before it shipped.** The series was being recorded
above the loop, so it would have published fractions describing camera
positions the sim never photographed. The restore position was captured
beside the render-target save, three hundred lines below the loop, by which
point the camera had already moved — "restoring" would have left it displaced
for the rest of the run, a screenshot fix quietly becoming a gameplay change.
And the 84-ray grid was about to exist twice.

**Exercised on the case it was built for, two builds later.** `b71c71f` was
mild — `shotNearBefore=0.29`, one step — so it proved nothing. `01f4eeb` ran
into a real one: `shotNearBefore=0.83 shotNudges=8 shotNudgesWorked=5
shotNudgesGaveUp=0`. Five blocked shots, all cleared, averaging 1.6 steps, and
the twenty-shot series topped out at 0.18 against that pre-loop
`0.37 0.48 0.60 1.00` tail.

---

## Patrol density, and four wrong theories — 2026-08-19

Cut from `queue.md` at the length cap.

1. **PATROL DENSITY FOLLOWS THE INQUIRY.** `PatrolWeightFor(Inquiry)` is a
   pure Core function — None 1, Procedure 2, Investigation 3, Manhunt 5,
   which on 28 vehicles is 2 patrol cars quiet against 6 under a manhunt.
   Conversion runs right after `SetHour` and only on PARKED cars, so nothing
   changes shape in front of the player.

   **EVERY LINK FIRES** (`b71c71f`): `patrolWant=6 patrolNow=6
   patrolsChanged=5 patrolBodies=5`, meshes following kinds. Then the in-shot
   counter found they were invisible — `patrolInShotMean=0.10` under a full
   manhunt, one frame in ten.

   **EVERY NUMBER I QUOTED WAS TWO REGIMES AVERAGED.** `shotsOnBeat=3/20`
   against `shotDistricts=[the_Hook:20]` and `patrolBeat=the_Hook`: the last
   is the END-of-run value, and **seventeen of twenty shots measured a town
   with no manhunt in it**. So 0.10, 0.20 and 0.25 were all mixtures.
   `patrolOnBeatMean=0.00` over 3 shots against `0.18` over 17 — zero of
   three separates nothing, so there is still no measurement here.

   **Ruled out, each for one measurement:** the cameras (frames hold 2.75-4.75
   vehicles); too few cars (6 of 28); and my own tidy theory that `Rebalance`
   converting dormant cars built the patrol fleet from the vehicles that sleep
   most — probed hour by hour, patrols are 6 of 6 awake 07:00-23:00.

   **Still unread:** six cars that never stop are six brief crossings. A
   patrol PARKED at a junction with its beacon lit stays in frame and is
   worth more than three that drive past. A feature, not a knob.


---

## The gates --constant work list, long form — 2026-08-19

12. **THE REST OF WHAT `gates --constant` FOUND, AND IT IS A WORK LIST.**
   Sixty keys have never been anything but zero across 131 runs. Most are fault
   counters doing their job — `errors=0`, `idLeaks=0`, `blankLabels=0`,
   `panelsBad=0`, `offRoad=0`. These are the ones that are not:

   - **`threat` has only ever seen one outcome.** `brandishes=1` a run, so
     `called=0 complied=0 undraw=False` CANNOT be sampled — one brandish gives
     one answer, `FleeScreaming` every time. Plant several, at people with
     different nerve.
   - **`departed=0` and `carriedOut=0` are the live zeros**; `adds` reads 10,
     and this entry claimed otherwise for four builds off prose.
   - **`groundless=False`** — a carry has never been groundless.
   - **`summonsTaken=0` — fixed 5 August, awaiting its own build.** The nightly
     pass sampled the player's position at breakfast against lines live at hour
     21; now sampled at the ring hour. **The plant is deliberately NOT in the
     same build**, so a moving `summonsTaken` is attributable to this alone.

   **The rule for every one of these is the same and it is rule 5b's
   corollary: PLANT the condition, never loosen the bound.** And do them one
   or two at a time — a build carrying five new staged behaviours cannot
   attribute a red gate to any of them.


---

## The police car, and reading a model instead of a comment — 2026-08-19

1. **NO BUS AND NO BICYCLE EXIST IN THE KIT — the remaining primitives.**
   `vehicleFellBack=[bus,bike x6]`. All 50 models in the car-kit listing ARE
   extracted and neither a bus nor a bicycle is among them, so this is a
   sourcing gap and the fix is another CC0 kit, not more code. Bikes are
   almost all of it, so one bicycle model closes it.

   **THE POLICE CAR IS IN.** "Wrong era, wrong town" was a guess about a file
   nobody had opened: a plain saloon a fifth longer than the sedan whose body
   maps to the WHITE region of the shared colormap (#cbcbde) where every
   other car is mid-slate. Blue beacon on a plinth we add, exempt from the
   noir multiply, push bar dropped by name. `vehiclesKitted` 18/28 -> 21/28.
   `ambulance` and `firetruck` stay out — both mid-slate in this palette.

