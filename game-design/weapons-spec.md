# WEAPONS, CARRYING AND ACQUISITION — proposal

**Status: PROPOSAL. Nothing built. Awaiting Jafar's approval.**
Written 2026-07-29, after: *"we have to build it properly from the start…
you need to really think through this one thoroughly… research other games…
then propose it, and then I'll approve."*

Standing quality bar for this and everything after it: **as close to the
best games in the genre as our limits allow.** Where a limit binds, this
document names it rather than quietly designing around it.

---

## 0. What was already decided, so it is not re-opened

From `combat-spec.md` §7, answered 2026-07-28, and this proposal obeys all
of it:

| | |
|---|---|
| Who swings first | **Both** — the player can start it |
| Lethality | **Yes, rarely and permanently** |
| Readout | Diegetic + heavy feedback, architected so a minimal HUD is a toggle |
| Auto-resolve | Yes, for accessibility |

New, 2026-07-29: **violence is a verb, killing included, weapons gated
fists → knives → guns later, built properly from the start.**

---

## 1. THE SPINE — one sentence, and everything else derives from it

> **A weapon is not a damage value. It is a fact about you that other
> people can know.**

This is the only framing under which a weapon system belongs in LEDGER at
all. Our antagonist is gossip; our best-tested system is a per-person
belief network with confidence, decay, contradiction and suppression. A
weapon that is only a stat is a foreign object in that game. A weapon that
is *a thing people find out about you* is native to it.

So every weapon in this design carries four social properties before it
carries a single combat one:

| Property | The question it answers |
|---|---|
| **Concealment** | Can it be found on you, and by whom? |
| **Legibility** | What does carrying it say about the man carrying it? |
| **Escalation** | What does drawing it do to a scene before it touches anyone? |
| **Provenance** | Where did it come from, and who can trace it back? |

Combat stats — reach, speed, lethality — are secondary and largely already
written in `Core/Combat`.

---

## 2. What other games do, and what we take

Researched rather than recalled. Four systems, four different lessons.

### Hitman — items are socially legible, not just tools

Frisking (pat-down) and metal detectors make the question "what are you
carrying" a first-class mechanic, with a nuanced ontology: coins,
fibrewire and lockpicks pass, tools do not; a dropped briefcase provokes
the same reaction as a dropped firearm. Players learn to test items by
drawing them near NPCs and watching the suspicion meter spike.
([Hitman Wiki — Frisking](https://hitman.fandom.com/wiki/Frisking),
[Steam discussion — prohibited items](https://steamcommunity.com/app/236870/discussions/0/357288572124057455/))

**We take:** the frisk, and the idea that concealability is a per-item
property with social consequences. **We leave:** the item-taxonomy puzzle.
We will have three or four weapons, not forty.

### Kingdom Come: Deliverance — reputation changes how often you are searched

A drawn weapon gets you confronted by NPCs. Reputation determines whether
guards search you, whether they chase minor crimes, and how warmly
townsfolk treat you.
([KCD Wiki — Reputation](https://kingdom-come-deliverance.fandom.com/wiki/Reputation),
[Crime and reputation](https://kingdomcomedeliverance-archive.fandom.com/wiki/Crime_and_reputation))

**We take:** standing gates the frisk. We already have standing and heat —
a man the street trusts does not get patted down at the door.
**We leave:** a global reputation number. Ours is per-person and better.

### Red Dead Redemption 2 — witnesses who can or cannot identify you

Witnesses are marked and colour-coded: white means they saw it but cannot
name you, red means they can. A bandana or mask reduces identification.
Weapons must be holstered to surrender.
([RDR2 Wiki — Wanted System](https://www.rdr2.org/wiki/wanted-system/),
[GamesRadar — bounty and wanted level](https://www.gamesradar.com/red-dead-redemption-2-bounty-and-wanted-level/))

**We take:** the saw-it / can-name-you split — **and we already have both
halves.** `Violence.Saw` records witnesses; the runner's coat already
exists as a disguise that degrades identification. This is the closest fit
of the four and costs us almost nothing.

### Inventory design generally — do not add weight unless weight is the game

The consensus is unambiguous: encumbrance is worth having only when
resource management is part of the core loop; otherwise skip it. Slot
systems flatten meaningful differences (a rocket launcher and a potato
occupy one slot each); weight systems add granularity at the cost of
fiddliness. Many games hybridise.
([ResetEra discussion](https://www.resetera.com/threads/do-you-prefer-a-weight-system-or-inventory-slots.847011/),
[Bio Break — does inventory weight help immersion](https://biobreak.wordpress.com/2020/05/19/does-inventory-weight-help-rpg-immersion/))

**We take:** the negative result. **LEDGER has no encumbrance and no
inventory grid.** Carrying capacity is not our core loop and a Tetris bag
would be a different game wearing our fiction.

---

## 3. THE CARRY MODEL — three places, no screen

Not an inventory. **Three locations, and the interesting one is the middle.**

| Where | What it means |
|---|---|
| **At the bar** | Everything you own that you did not bring. Safe, and searchable by anyone who gets inside. |
| **On you** | What you chose when you walked out of the door. Concealed or not. |
| **In hand** | Drawn. Visible to everyone. A social act, not a combat one. |

**The decision the player makes is at the door, not in a menu.** Leaving
the bar with a knife is the same shape of decision as putting on the
runner's coat — which already exists, is already a soft key, and already
carries social cost. We are extending an established verb, not inventing a
screen.

**No weight. No slots. No grid.** You can carry one weapon and the ordinary
contents of a man's pockets. If a second weapon ever matters we will
revisit, and I doubt it will.

**Why this is right for us:** the whole design pressure in LEDGER is toward
*fewer, heavier decisions*. An inventory screen converts one heavy decision
(am I the kind of man who goes out armed tonight?) into twenty light ones.

---

## 4. THE WEAPONS

Three tiers, and the third is architecture-only for now.

### Tier 1 — hands. Always available.

Fists are not a weapon, they are the absence of one. No concealment
problem, lowest escalation, rarely lethal (the existing `Harm` model
already produces injuries, not corpses, from unarmed exchanges).

**Design purpose:** fists are the control case. Every escalation above them
should feel like a decision the player made, and they can only feel that
way if there is a floor that costs nothing.

### Tier 2 — the knife. THE tier that matters, and it is nearly free.

**Acquisition is diegetic and costs nothing: you own a bar with a
kitchen.** Tom Novak does not need a black market to find a knife; he needs
to decide to put one in his coat. That single fact removes an entire
economy from Phase 1 and is better fiction than any shop.

| Property | Value |
|---|---|
| Concealment | High — under a coat, found only by a frisk |
| Legibility | Severe. Drawing one says *this is not a fight, this is an attempt* |
| Escalation | Maximum. A knife turns a scuffle into a thing people remember |
| Provenance | **Yours.** It came from your kitchen and can be traced to you |

That last row is the design. **A knife from your own bar is evidence with
your name on it** — which is the most LEDGER-shaped property a weapon could
possibly have, and it arrives for free from the fiction.

### Tier 3 — guns. ARCHITECTURE NOW, CONTENT LATER.

`combat-spec.md` argues guns change the fiction from *a man in trouble* to
*a man with a gun*, and I still think that is true. But Jafar is right that
building for them later is how you end up rewriting.

**So: the model carries `Range`, `Loudness` and `Draw time` from day one,
and no gun exists.** A pistol becomes a data row plus an animation, not a
system. Concretely, the axes below are in the type from the first commit:

- `Reach` — fists 0.8m, knife 1.0m, pistol 20m+
- `Loudness` — how far the *event* travels. A punch is heard by the street;
  a shot is heard by the district. This one number is what makes a gun a
  different game, and having it present but unused costs nothing.
- `Draw` — seconds to bring into hand from concealment. The knife's is
  short; a coat pocket is not a holster.
- `Lethality` — probability band, feeding the existing `Harm`/`Homicide`
  split.

**I am not proposing we build a gun. I am proposing we never have to
retrofit one.**

---

## 5. ACQUISITION — three routes, and each one is a gossip event

The rule: **acquiring a weapon must create information about you.** A shop
that silently increments a counter is the failure mode.

| Route | Cost | The information it creates |
|---|---|---|
| **Owned** (kitchen) | Free | None — but the object is traceable to you |
| **Bought** (a named person) | Money + a favour | *Someone knows you went looking.* The seller is a person with a memory, a loyalty and a price for their silence |
| **Taken** (off someone you beat) | A fight | *Someone lost it.* They can recognise it later, and so can their friends |

This is deliberately the same shape as the existing `Access` soft-key
system: you do not "have" a weapon the way you have an item, you have a
relationship with how you got it.

**Phase 1 only needs the first row.** Buying and taking are Phase 3.

**Not proposed:** random world loot. Finding a knife in a crate is the
single fastest way to make the object meaningless, and meaninglessness is
the thing we are most trying to avoid.

---

## 6. THE FRISK — where carrying gets its teeth

`Core/Access` already models doors as soft keys with a doorman, a refusal
line and conditions. Carrying extends it by one condition.

- Some rooms search you. The card room, Ellis's station, anywhere that
  matters.
- **Standing and heat gate the search**, KCD-style: a man the street trusts
  walks in; a man it is talking about gets patted down.
- Being caught carrying is not a fail state. It is a **refusal with a
  memory** — the doorman now knows something, and the doorman talks.

This is the mechanism that makes "am I carrying tonight?" a real question
rather than a free buff. It also costs us very little: the door system,
the refusal lines and the gossip propagation all already exist.

---

## 7. DRAWING — the loud act, and it is not the swing

From `combat-spec.md`, **square up** is already a verb whose cost is that
witnesses start paying attention *before anything lands*. Drawing a weapon
is that same beat with a much larger radius and a permanent memory.

- Drawing is visible at conversational distance and beyond.
- Everyone in `Violence.Saw` range records it, whether or not it is used.
- **A drawn knife that is never used is still a fact about you**, and one
  that cannot be discredited by the usual means because several people saw
  the same thing.

**This is where most of the play is**, and it is why the system is worth
building. The interesting decisions are draw / don't draw and carry / don't
carry — not which of six blades has better DPS.

---

## 8. THE MURDER WEAPON — the part I have not seen done well elsewhere

If killing is permanent and a body is a fact that cannot be discredited
(`combat-spec.md` §7b), then **the object that did it is physical evidence
and should behave like it.**

- A weapon used in a killing gains provenance: it is *the* knife now.
- Ellis's investigation ladder can look for it. She already escalates
  procedure → investigation → manhunt.
- **Disposal becomes a verb** — the river, the furnace in the cellar,
  burying it. Each has a cost and each can be *seen*, which folds it
  straight back into the witness system.
- Keeping it is the lazy option and the dangerous one. Getting rid of it is
  a scene, at night, that somebody might watch.

I flag this as the highest-value single idea in this document. It uses only
systems we already have, it is dramatically strong, and it is the sort of
thing this game can do that a bigger-budget crime game usually cannot,
because their gossip layer is thin and ours is the whole point.

---

## 9. WHAT I AM DELIBERATELY NOT PROPOSING

Stated so approving this is not accidentally approving them.

- **No inventory screen, grid or weight.** §3.
- **No durability or repair.** Ours is a two-week story; a knife does not
  wear out in two weeks, and it adds maintenance chores to a game about
  people.
- **No crafting.** Wrong genre, wrong protagonist.
- **No weapon progression or upgrades.** A knife should not get better.
  Character progress in LEDGER is social, not martial, and a stat ladder
  would quietly argue the opposite.
- **No hotbar or quick-swap.** You have hands or you have a knife.
- **No random loot.** §5.
- **No gun content.** §4.

Every one of these is a thing a normal crime game would have. Each is left
out because it would move the centre of gravity away from the street.

---

## 10. PHASING — each phase is playable and provable on its own

Following the project's established pattern: Core-first where the logic
belongs there, a sim gate per phase that proves the claim in-engine.

**Phase 1 — carry and draw (no acquisition, no economy).**
`Core/Carry`: the three places, concealment, legibility, draw time. The
kitchen knife. Drawing is seen and remembered. Sim gate: a weapon is
carried, drawn, witnessed, and the witness's belief about the player
changes.

**Phase 2 — the frisk.** One condition added to `Core/Access`, gated on
standing and heat. Sim gate: the same door admits an unarmed player and
refuses an armed one, and the doorman remembers.

**Phase 3 — acquisition.** Bought and taken, each creating its information.
Sim gate: buying a weapon creates a person who knows, and that knowledge
travels.

**Phase 4 — the murder weapon.** Provenance, disposal, Ellis looking for
it. Sim gate: a killing produces a traceable object; disposal removes the
trace and can itself be witnessed.

**Phase 5 (only if Phases 1–4 feel right) — guns as content.** Data rows
against axes that already exist.

**The kill switch, restated from `combat-spec.md` §8:** if Phase 1 and 2
land and it still feels like a distraction from the gossip game, the
correct decision is to stop and leave violence as something that happens
*to* you. This document does not change that.

---

## 11. THE RISK, NAMED

Combat is the easiest way to ruin this game — it is the most familiar verb
in the medium and it will pull effort toward itself. Weapons multiply that
risk, because weapons are the most *collectible*-feeling thing a game can
have, and collecting is exactly the wrong instinct here.

The mitigation is the whole of §9: keep the object count tiny, refuse every
mechanic that rewards accumulation, and make the interesting question
social rather than tactical.

**If the player ever asks "which knife is best" instead of "should I take
one", the design has failed** — and that sentence is the acceptance test
for the entire system.

---

## 12. WHAT I NEED FROM YOU

Approve, amend, or reject. Specifically:

1. **The spine (§1)** — weapons as social facts rather than stats. Everything
   else hangs off this.
2. **No inventory screen, no weight (§3)** — the biggest structural call.
3. **The kitchen knife as Phase-1 acquisition (§4)** — free, diegetic, and
   traceable to you.
4. **The murder weapon (§8)** — the highest-value idea here, and the most
   new work.
5. **Guns: axes now, content later (§4)** — confirms your "properly from the
   start" without building a shooter.

If §1 and §3 are right, the rest is detail I can carry. If either is wrong,
tell me now, because everything below them is built on top.
