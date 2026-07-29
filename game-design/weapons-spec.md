# PERCEPTION, WEAPONS AND VIOLENCE — proposal v2

**Status: PROPOSAL. Nothing built. Awaiting Jafar's approval.**
v1 written 2026-07-29 and **rejected the same day, correctly.** v2 rewritten
against the correction.

---

## 0. WHAT V1 GOT WRONG, because the error is the useful part

v1's spine was *"a weapon is not a damage value, it is a fact about you that
other people can know."*

That sentence is true and it is not sufficient. Building on it alone turned a
crime game into a reputation game with knives in it. It deleted the entire
tactical layer — the moment-to-moment question of **who can see me, who can
hear me, and which tool works from here** — and replaced it with a
bookkeeping question about what people believe afterwards.

Jafar's correction, and it resets the design:

> *"the most immersive thing about KCD2 is the NPCs, how they react to you
> and what happens in the world depending on your actions… you could have a
> pistol and make a loud noise and everybody hears you and sees a person
> dropping. Or a pistol with a silencer, then they don't hear the shot but
> they see someone dropping. Or they see you pulling a gun but don't see who
> drops, or they see the whole thing… You're basing everything on gossip
> alone. That's not the entire game… It's a crime game, so violence and
> weapons should be a huge part of it."*

**The pipeline was backwards.** Gossip is not the foundation; it is the
*fourth* stage of one. The foundation is perception.

```
  PERCEPTION  →  OBSERVATION  →  REACTION  →  MEMORY & TALK
  can they      what exactly     what do they   what does the
  see/hear it?  did they learn?  do about it?   street know later?
```

LEDGER's existing strength is stages 3 and 4. **Stages 1 and 2 barely exist**,
and they are where the immersion Jafar is describing actually comes from.

---

## 1. WHAT THIS GAME IS — restated

The old framing — *"the antagonist is gossip"* — is a good slogan that became
a straitjacket. Corrected:

> **LEDGER is a crime game in a city that perceives, reacts and remembers.**
>
> Violence and weapons are a core pillar, not a footnote. What makes them
> matter more here than in other crime games is that every act is *witnessed
> partially* by people with real senses, who then behave differently, tell
> each other, and remember.

Neither half is decoration. A crime game with a thin reaction layer is GTA;
a reaction layer with no crime in it is a chat simulator. The whole value is
the join.

This supersedes the framing in `design-doc.md` §2 and `agency-model.md`'s
*"violence is seen"* clause — which was right, but was being read as *"and
that is all violence is."*

---

## 2. RESEARCH — what four systems teach, and what we take

### Thief: The Dark Project — light and sound as the central mechanic

The first game to build play on light and sound rather than combat. The
**light gem** gives constant feedback on how visible you are, computed from
the light level at your position. Surfaces change how loud you are — carpet
and grass mute footsteps enough to run up behind someone; tile and metal
give you away. ([Thief Wiki — Light Gem](https://thief.fandom.com/wiki/Light_Gem),
[Immersive Sim Wiki](http://immersivesim.wikidot.com/game:thief))

**We take: light level as a first-class input to being seen.** We already
have a full time-of-day and lamp model — `LightModel`, night amount, 360
light shafts, wet reflections. **We have been rendering that light for weeks
and no NPC has ever used it.** A man standing under a lamp is more visible
than a man ten metres away in a doorway, and we already know both numbers.

### Splinter Cell / general stealth AI — graduated states, not binary

Detection builds over time inside a vision cone rather than firing instantly;
cones have bands — unaware, aware-of-movement, fully aware. Hearing radius
**scales with the agent's alert state**, so an already-nervous person hears
more, which produces escalation without a state machine.
([Game Developer — Splinter Cell: Blacklist stealth AI](https://www.gamedeveloper.com/design/bringing-balance-to-stealth-ai-in-splinter-cell-blacklist),
[Stealth game sight cones](https://www.dailygamedesigns.com/games/134-stealth-game-sight-cones/))

**We take: graduated detection and alert-scaled hearing.** Never a binary
"spotted".

### Hitman — the crime and the criminal are separate observations

The distinction that matters most for us: *"the crime can be witnessed —
your target can be seen dying — without you being spotted."* Suppressors do
not make a shot silent; **they shrink the radius in which it is heard**, and
a second shot inside a minute is treated as a gunshot rather than a
curiosity. NPCs investigate noises.
([Hitman Wiki — Alert Levels](https://hitman.fandom.com/wiki/Alert_Levels),
[Witness mechanics](https://www.hitmanforum.com/t/witnesses-mechanics/21574),
[Game Informer — Hitman 3 guide](https://gameinformer.com/feature/2021/01/24/hitman-3-beginners-guide-essential-tips-to-become-a-silent-assassin))

**We take: the act and the actor are two different facts,** and suppression
is a radius, not a mute button. This is precisely Jafar's example.

### Kingdom Come: Deliverance 2 — the world reacts to everything, not just crime

NPCs remember hostility and theft; they follow daily routines; and reactions
fire on things that are not crimes at all — being drunk in daylight, walking
around undressed. The reactivity is broad, not just a wanted meter.
([Game Rant — KCD2 reactive systems](https://gamerant.com/kingdom-come-deliverance-2-reactive-system-dialogue-evil-crime-npc-replay/),
[KCD2 NPC guide](https://kingdomcomedeliverance2.wiki.fextralife.com/NPCs))

**We take: the reaction layer is not a crime subsystem.** The same perception
model that notices a knife should notice a bloodstain, a man running at
night, a fight, or somebody standing where they should not be.

---

## 3. THE FOUNDATION — `Core/Perception`

The system everything else needs and we do not have.

### 3.1 Vision

Per person, per frame-ish (throttled by distance — we already LOD walkers):

| Input | Source |
|---|---|
| **Cone** | Facing + FOV. Peripheral band detects motion only |
| **Range** | Falls off; identification range is much shorter than detection range |
| **Occlusion** | Line of sight. `Acoustics` already does occlusion raycasts |
| **Light level** | `LightModel` + lamp proximity + night amount. **Already computed** |
| **Motion** | Running is far more visible than standing still |
| **Time in cone** | Detection accumulates; a glance is not a look |

Output is not a boolean. It is a **confidence that this person is being
seen**, and separately **whether they can be identified** — which is where
the runner's coat, distance and darkness already earn their keep.

### 3.2 Hearing

Every noteworthy event emits a **sound event**: position, loudness, kind.

- Radius derives from loudness. `Core/Mixing.Reach` already maps a bus to a
  distance in metres — the same idea, reusable.
- **Occluded by walls**, attenuated by rain and by the street bed. `Acoustics`
  exists and does this for the player's ears; it needs to serve NPC ears too.
- **Radius scales with alert state.** A calm man ignores a bang two streets
  away; a frightened one hears a footstep behind him.
- Hearing gives **direction and distance, not identity.** You hear a shot;
  you do not hear who fired it. That asymmetry is the entire design space.

### 3.3 What this buys immediately, before any weapon exists

- People notice you loitering.
- People notice you running at night.
- Someone standing under a lamp is seen from across the street; the same
  person in a doorway is not.
- A shout draws heads. A door slam draws heads.

**That is the KCD2 feeling, and none of it requires violence.** It is worth
building for its own sake.

---

## 4. OBSERVATION — the layer that makes weapons interesting

The user's insight, formalised. When something happens, each person nearby
gets **one of these**, not a shared "saw it" flag:

| Observation | What they know | Typical cause |
|---|---|---|
| **Full** | The act, the actor, the victim | Close, lit, facing it |
| **Act, no actor** | Someone was killed; no idea by whom | Saw the drop from across the street; suppressed shot |
| **Actor, no act** | Tom drew a weapon; did not see what happened | Line of sight broken at the wrong moment |
| **Sound only** | A shot, a scream, a struggle — direction and distance | Loud weapon behind a wall |
| **Aftermath** | Found a body, blood, a broken door | Arrived later |
| **Flight** | Saw someone running from where it happened | The most common real-world witness |

Each becomes a different `Fact` with different confidence — and the existing
gossip mill, contradiction and discredit systems consume them unchanged.
**This is the join between the tactical and social layers, and it is the
single most valuable thing in this document.**

It also produces the drama automatically: two witnesses with *different*
partial observations who compare notes and assemble something closer to the
truth than either had. We already have `CompareNotes`. It has never had
partial information to work with.

---

## 5. WEAPONS — a table of perception profiles

Now weapons are a genuine tactical choice, because they differ along the
axes the world actually senses.

| Weapon | Noise | Reach | Speed | Victim cries out | Body | Concealable |
|---|---|---|---|---|---|---|
| **Fists** | Struggle — moderate, close | 0.8m | slow | yes, throughout | rarely | n/a |
| **Knife** | Quiet act | 1.0m | fast | yes, briefly | yes | yes |
| **Wire** | **Silent** | contact, from behind | slow | **no** | yes | yes |
| **Pistol** | **Loud — district** | 20m+ | instant | no | yes | poorly |
| **Suppressed pistol** | Quiet — one room | 20m+ | instant | no | yes | poorly |
| **Improvised** (bottle, bar) | Loud impact | 1.2m | medium | yes | rarely | no |

Read across the rows and the choices are real, and they are *situational*
rather than a power ladder:

- **Crowded street, must be done now** → suppressed pistol. They see a man
  drop and have no idea where it came from. *Act, no actor* for everyone.
- **Alone with him in a back room** → knife. Fast, quiet, but he cries out and
  anyone in the next room gets *sound only*.
- **He must not make a sound and you have time** → wire. Requires being
  unseen AND behind him. Catastrophic if interrupted mid-way.
- **You want it heard** → pistol. Sometimes the point of violence is the
  message, and this game should let you send it.
- **You do not want to kill anybody** → fists. Loud, messy, leaves a living
  witness who is now your enemy.

**Note what is absent: damage numbers.** No weapon is *better*. The pistol is
not an upgrade over the knife; it is louder and works at range. That is how
this stays a crime game rather than becoming a power fantasy.

---

## 6. REACTION — what people DO, which is where immersion lives

Graduated, per person, driven by their own observation and temperament
(`Gossiper` already has nerve and greed):

1. **Notice** — head turns. Free, constant, and the thing that makes a street
   feel alive.
2. **Investigate** — walks toward a noise. The single highest-value behaviour
   in the whole system: it turns one sound into a moving problem.
3. **Alarm** — shouts. Which is itself a loud sound event, so alarm
   propagates through the same hearing system. **Panic is emergent, not
   scripted.**
4. **Flee** — runs. Nerve decides.
5. **Fetch the law** — goes to find Ellis. We have her, and she has a ladder.
6. **Intervene** — rare, high-nerve, and it should be genuinely dangerous.

Bodies are discovered by whoever walks past next, which means **time and
routes matter** — an alley at 3am buys you hours; the market at noon buys
you seconds.

---

## 7. WHAT ALREADY EXISTS, AND WHAT IS GENUINELY NEW

Being honest about cost, because this is a large proposal.

**Exists and is reusable:**
- `Acoustics` — occlusion, space kinds, wetness. Currently player-ears only.
- `Mixing.Reach` — loudness → metres, per bus.
- `LightModel` + the whole lighting pass — light level anywhere, any hour.
- `Violence.Saw`, `KillingConfidence`, `Notoriety`, `HomicideBook`, `Police`.
- `Core/Combat` phases 1–4, tuned.
- Gossip mill: facts, confidence, decay, contradiction, `CompareNotes`.
- Walkers with facing, routines, nerve, and now bodies that turn their heads.
- The runner's coat as an identification-degrader.

**Genuinely new:**
- `Core/Perception` — vision cones with light and occlusion; hearing with
  loudness and alert scaling. **The big one.**
- `Core/Observation` — partial witness outcomes.
- Reaction behaviours: investigate, alarm-propagation, flee, fetch.
- The weapon table and its verbs.
- Body discovery by passers-by.
- Performance: perception for ~50 visible walkers, throttled by distance.
  This is the main technical risk and it is a real one.

---

## 8. PHASING — each phase playable, provable, and useful alone

**Phase 1 — perception, no weapons.** Vision cones with light and occlusion;
hearing with loudness. NPCs notice, turn, and investigate noises. **Ship
this and play it even if weapons never follow** — it is the KCD2 feeling and
it stands on its own. Sim gate: a walker in light is detected at greater
range than one in shadow; a sound behind a wall is not heard.

**Phase 2 — observation and reaction.** Partial observations become facts;
alarm propagates as sound; flee and fetch-the-law. Sim gate: one event
produces *different* observations for differently-placed witnesses, and
`CompareNotes` assembles more truth than either held.

**Phase 3 — melee.** Fists and knife against the existing combat model.
Carrying and the frisk (v1 §6 survives intact). Sim gate: a knife killing
in an empty alley leaves no witness; the same killing in a market does.

**Phase 4 — the murder weapon.** Provenance, disposal as a verb that can
itself be witnessed, Ellis looking for the object. *(Kept from v1 — it
survives the rewrite unchanged and I still think it is the best single idea
here.)*

**Phase 5 — firearms.** Pistol and suppressed pistol, which is where the
perception model finally pays off in full. Deliberately last: it is the
loudest change to the fiction and the easiest thing to get wrong.

---

## 9. WHAT I STILL RECOMMEND AGAINST

Reduced from v1, because several of v1's refusals were over-cautious.

- **No inventory grid or weight.** Still. The decision is *what did I bring
  tonight*, made at the door. Carrying two or three things is fine; managing
  a bag is a different game.
- **No weapon durability, crafting or upgrades.** A pistol should not level
  up. Progression here is access, information and standing.
- **No random world loot.** Weapons come from places that make sense.
- **No damage numbers or health bars.** Consistent with `combat-spec.md` §4.

**Withdrawn from v1:** the claim that guns change the fiction too much to
build. They change it a great deal, which is why they are Phase 5 — but the
perception system is what makes a gun interesting rather than a win button,
and with it in place a gun is a *tool with a huge noise radius* rather than
an escalation of damage.

---

## 10. THE RISK, RESTATED HONESTLY

v1 said combat was the easiest way to ruin this game. That was overstated in
one direction and I want to correct it rather than repeat it.

**The real risk is building a perception system that is too coarse to be
fair.** Stealth-adjacent systems live or die on whether the player can
predict them. If a player cannot tell why they were seen, the system feels
broken no matter how sophisticated it is — which is exactly why Thief put a
light gem on the screen.

So: **feedback is not optional here.** The player must be able to read their
own visibility and noise. `combat-spec.md` §7c already committed to readout
values existing as data whether or not anything draws them; this extends
that to visibility and loudness from day one.

The second risk is performance, and §7 names it.

---

## 11. WHAT I NEED FROM YOU

1. **The reframing in §1** — crime game in a city that perceives and
   remembers; violence a core pillar; gossip the consequence layer rather
   than the foundation. This replaces the old "antagonist is gossip"
   framing in `design-doc.md`.
2. **Perception first, weapons second (§8 Phase 1)** — build senses before
   tools, and ship the senses alone if you like them.
3. **The observation table (§4)** — the six partial outcomes. This is the
   join, and if the shape is wrong everything above it is wrong.
4. **The weapon table (§5)** — situational rather than a power ladder, and
   whether the six rows are the right six.
5. **Guns at Phase 5** rather than never.

If §1 and §4 are right, the rest is detail I can carry.
