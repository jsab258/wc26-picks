# The Agency Model — what this game gives the player, and how deep

Direction set by the player 2026-07-26 in discussion. This supersedes any
implicit scoping in the founding doc and drives `roadmap.md` from here on.

## The framing

Agency is not one spectrum from "current game" to "real life." Every game
picks a handful of dimensions, makes them deep, and abstracts or deletes
the rest. What follows is our chosen profile, benchmarked outside-in
against shipped state-of-the-art rather than inside-out from our codebase.

**The filter that decides everything:** *every non-social system exists to
give the social system stakes.* Money buys silence. Violence is seen.
Health is how you meet June. Clothes are how the street reads you. A
system that does not feed the social layer is grind.

**The grind test:** a system that asks for a DECISION occasionally, with
consequences that ripple for days, is depth. A system that asks for
MAINTENANCE on a timer is a chore. Hunger bars are chores; the crew's cut
is a decision. Every system also needs a lazy path and an invested path,
and nothing may punish a player for ignoring it.

**Conversation is never mandatory.** A full loop must be playable with a
few chip taps; talking is how you go deep, never how you make progress.
This is the LLM-specific grind risk and the reason chips exist.

## Benchmark (0-100 by dimension)

| Dimension | GTA5 | RDR2 | KCD2 | BG3 | Hitman | Sims | CK3 | LEDGER now | **target** |
|---|---|---|---|---|---|---|---|---|---|
| Social: talk, trust, memory | 5 | 20 | 35 | 60* | 10 | 40 | 55 | 93 | **98** |
| Consequence persistence | 5 | 30 | 60 | 70 | 15 | 40 | 85 | 95 | **100** |
| Information / who knows what | 5 | 15 | 40 | 25 | 30 | 5 | 65 | 90 | **95** |
| Time & opportunity cost | 10 | 40 | 70 | 30 | 20 | 80 | 60 | 85 | **90** |
| **Economy (full simulation)** | 15 | 25 | 55 | 20 | 5 | 60 | 45 | 80 | **85** |
| Faction politics / allegiance | 10 | 20 | 45 | 55 | 5 | 0 | 90 | 35 | **75** |
| **Operation planning** | 70 | 25 | 20 | 45 | 95 | 5 | 30 | **5** | **75** |
| Law & institutions as a tool | 5 | 25 | 55 | 20 | 10 | 5 | 60 | 15 | **70** |
| Legacy & succession | 0 | 10 | 15 | 20 | 0 | 55 | 95 | 20 | **70** |
| **Violence (staged: melee then guns)** | 90 | 90 | 80 | 85 | 70 | 5 | 20 | 0 | **70** |
| **Traversal & place** | 95 | 90 | 70 | 30 | 40 | 15 | 0 | 20 | **65** |
| Class & access (soft keys) | 10 | 25 | 60 | 30 | 95 | 20 | 50 | 10 | **65** |
| Multiple solutions per obstacle | 30 | 25 | 55 | 85 | 95 | 20 | 40 | 60 | **80** |
| Companionship (who's with you) | 25 | 75 | 30 | 90 | 0 | 45 | 20 | 0 | **55** |
| Public notoriety | 20 | 45 | 50 | 30 | 25 | 15 | 60 | 25 | **60** |
| Communication at distance | 40 | 5 | 0 | 5 | 20 | 50 | 30 | 0 | **60** |
| Constraint (arrest, surveillance) | 30 | 40 | 65 | 20 | 40 | 10 | 35 | 40 | **55** |
| Home / base that reacts | 25 | 70 | 40 | 50 | 0 | 95 | 30 | 10 | **50** |
| Family & dependents | 5 | 30 | 10 | 25 | 0 | 90 | 95 | 15 | **50** |
| Character competence | 20 | 45 | 90 | 95 | 30 | 60 | 40 | 0 | **40** |
| Vice & addiction | 15 | 25 | 40 | 10 | 0 | 30 | 25 | 5 | **40** |
| Self-presentation / lifestyle | 45 | 55 | 50 | 30 | 60 | 85 | 25 | 15 | **35** |
| Visible odds | 0 | 0 | 15 | 95 | 10 | 5 | 70 | 0 | **50** |
| Interiority (psyche as system) | 0 | 15 | 0 | 20 | 0 | 30 | 20 | 0 | **30** |
| Vehicles / driving | 95 | 60 | 50 | 0 | 10 | 20 | 0 | 0 | **40, late — superseded, see below** |
| Body needs (eat/sleep/hygiene) | 5 | 45 | 75 | 15 | 0 | 90 | 10 | 0 | **0** |
| Crafting / minigames | 20 | 70 | 85 | 30 | 15 | 55 | 0 | 0 | **0** |

\* BG3's social score is AUTHORED breadth — thousands of hand-written
branches. It anticipates; it does not simulate. Outside the anticipated
space there is nothing. That is the ceiling we are trying to break.

## The seven decisions this encodes

1. **Deepest social simulation ever shipped**, and deliberately
   unremarkable in the dimensions that don't serve it.
2. **Economy simulated end to end** at district scale — every business has
   costs, suppliers, customers; residents earn and spend; prices move; the
   rackets extract from a real flow. Rule: every economic number must be
   legible as somebody's circumstance, or it is invisible weather. The
   player may squeeze the economy, never micromanage it.
3. **Violence is staged, not skipped**: consequence layer first (injuries
   that persist, the hospital, witnesses, feuds), melee as its own
   milestone after the slice's art pass, firearms last — a fired gun is a
   city-level event and the city must be able to react before it exists.
4. **Traversal grows by BREADTH OF PLACE, not by movement simulation**:
   more districts, walkable density, interiors from kits, and cheap modes
   (Ferko's cab as fast travel with a conversation attached, the ferry, a
   courier bicycle). No drivable-vehicle physics, ever. What makes
   traversal immersive is what happens while you move, and that engine we
   already have.
5. **Operation planning becomes a first-class loop** (the biggest hole
   found in the outside-in pass): choose the approach, the people, the
   hour, the gear; execute; survive contact. This is where crew
   competence, loyalty, and the witness system finally converge into a
   scene. Cheap for us — planning is decisions, not animation.
6. **Access is a soft-key system** (Hitman's lesson): places and people
   have an admission price paid in standing, notoriety, dress,
   introductions, or an appointment brokered by Halvard. The map becomes
   socially gated rather than physically gated, and lifestyle purchases
   finally have a job.
7. **Phones exist** (player decision 2026-07-26). Calls and messages at
   distance: warn people, coordinate crew you cannot see, be reachable —
   and be *called*. Note the cost this incurs: information no longer
   travels only at the speed people physically cross paths, so the gossip
   mill needs a phone channel with its own reach and fidelity rules, and
   surveillance/wiretaps become a natural counterplay.

## The outside-in additions — APPROVED 2026-07-26 (all eight)

1. **Operation planning (75)** — choose approach, people, hour, gear; then
   survive contact. The largest gap found; where crew competence, loyalty
   and the witness system converge into a scene.
2. **Multiple solutions per obstacle (80)** — a project law, not a
   feature: every locked problem gets three or four legitimate keys. The
   businesses' buy/debt/leverage triple is the template.
3. **Companionship (55)** — crew and friends accompany you, observe what
   happens, and remember it.
4. **Home / base that reacts (50)** — the bar changes as you do.
5. **Character competence (40)** — options unlocked, never numbers that
   rise (the 2026-07-25 no-grindable-stats rule stands).
6. **Access as soft keys (65)** — Hitman's lesson: places and people cost
   standing, notoriety, dress, an introduction, or a brokered appointment.
7. **Visible odds (50)** — DECIDED: *qualitative read*, never percentages.
   Characters estimate ("this will probably go badly"); the game never
   becomes a spreadsheet.
8. **Interiority (30)** — DECIDED: *pressure, not personality*. The
   protagonist's own nerve, guilt and appetite surface as intrusive lines
   in the moment ("you can still walk out of this room"). Never stats,
   never a Disco-style cast of inner voices.

**Competence (40) — DECIDED**: tracked per domain (collections,
conversations, night work), unlocking *approaches* rather than raising
numbers, surfaced as the character noticing what they couldn't before.

**Setting era — DECIDED: late-analog.** Landlines, payphones, answering
machines, messages left with people. Information gains a second channel
without travelling at internet speed, which preserves the mill's core
constraint and makes wiretaps, missed calls and being unreachable into
real play. Cards and generation prompts inherit this.

**Vehicles / driving (40): SUPERSEDED AND BUILT** (player, 2026-07-26:
*"city can't feel real or immersive without cars and real streets"*).

The score of 40 was answering the wrong question. It weighed driving as a
MECHANIC — and as a mechanic it really is expensive and
non-differentiating, which is why the model put it late. The player's
argument was about IMMERSION: a city with two roads and nothing moving on
it does not read as a place, and every social system in this project is
standing on the claim that this IS a place. Under that framing the streets
are not competing with the systems above; they are the ground the systems
stand on.

The diagnosis bore that out. The district was a 90×90m slab with buildings
and no streets — about the size of one real city block. So M12 was pulled
forward and built: a real grid, traffic, signs, lights, and a car you can
drive. See `streets-and-cars-spec.md` and roadmap M12.

Point 4 above ("no drivable-vehicle physics, ever") stands as written and
is not contradicted by this. There is still no vehicle physics: the car is
kinematic and arcade, there is no tyre model, no damage, no fuel, and no
pursuit. What was built is the CITY, with something moving in it.

## Explicitly refused

Lockpicking/alchemy/crafting minigames, gear treadmills, body-needs
maintenance. Expensive, non-differentiating, and hostile to the anti-grind
rules above.

## Built against this model, 2026-07-26 (night)

Four dimensions moved, and one of them is not on the table above because
the table did not have a row for it.

- **Economy 65 → 80** (target 85). District money is now finite and
  simulated: squeezing the street makes it poorer, and a poorer street
  spends less in your bar. Suppliers are people with names, opinions and
  prices. Every number surfaces as a person's circumstance and never as a
  percentage — asserted in the tests. The remaining 5 is other districts,
  which do not exist yet.
- **Multiple solutions per obstacle 35 → 60** (target 80). Not because new
  solutions were authored, but because the intent router made the existing
  ones reachable by *saying* them, and added a third class: actions the
  verb list never anticipated, adjudicated against real state with clamped
  effects. The remaining 20 wants operation planning (M7.5).
- **Social 90 → 93** (target 98). The Director makes the social layer
  originate pressure rather than only absorb it.
- **Living-city scale.** 36 people → 3000, with the KCD2 band arrangement.
  This dimension was never in the benchmark table and should have been; it
  is now tracked in the roadmap under M9.

**The dimension the model was missing entirely: INTERFACE.** Every game in
the benchmark table has a fixed verb set, because none of them can afford
anything else. That is the one place where this project's tools are not
merely competitive but categorically different, and the model scored it
nowhere. The router is the first payment on it. It is worth adding as a
row the next time this table is revised — and it is the row where our
target should be 100, because nobody else can reach it.
