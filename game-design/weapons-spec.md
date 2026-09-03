# PERCEPTION, WEAPONS AND VIOLENCE — spec v5, APPROVED, BUILDING

> **STATUS: SPEC.** The design for M16 — perception, weapons and violence. Stable reference:
> build state lives in `roadmap.md`, not here. A spec that disagrees
> with the roadmap is out of date about what got built, not about what
> was intended.

**Status: APPROVED IN FULL, 2026-07-29. Cleared to build.** *"approved."*

This is now the spec for the largest single feature in the project. It
supersedes `combat-spec.md` §0's framing of violence as deferred, and
`agency-model.md`'s *"violence is seen"* clause is folded into §1 rather than
governing it.

- v1 (2026-07-29) — **rejected the same day, correctly.**
- v2 (2026-07-29) — §1 reframing **APPROVED**, §2 perception-before-weapons
  **APPROVED**, guns at the last phase **APPROVED**. §4 (observation) and §5
  (weapons) sent back: *"seems a bit shallow at first glance. think about it
  in more detail and check other high quality games."*
- v2.1 (2026-07-29) — §4 and §5 rebuilt from the ground up; new §6 on feel
  and legibility, which is what *"it has to be EXCEPTIONALLY GOOD from a game
  feel and UI/UX pov"* actually requires; new §7 answering the acquisition
  question the original brief asked and v2 did not. Verdicts: **§4.5 the
  delivery window APPROVED**, **§6 approved in general**. Three sent back:
  - *"7 feels too few and low budget. think and research some more"* → §5
  - *"[attention] feels not explicit enough and depends a lot on how clearly
    we model and animate characters. alternative ideas?"* → §6.2
  - §4 and §7 — *"I don't get it, explain"*. Explained in chat 2026-07-29;
    both still open.
- v2.2 (2026-07-29) — **§5 is now seven families, ~16 carried objects, the
  environment as a weapon family of its own, and kit** — the Hitman argument
  that accidents and world objects expand a small arsenal further than more
  guns do. **§6.2's attention readout is now four redundant channels led by
  audio rather than by animation**, plus an explicit accessibility marker,
  because betting the most important feedback in the game on the weakest asset
  we own was the right thing to be challenged on.
- v3 (2026-07-29) — **APPROVED IN FULL.** No content change from v2.2; the status
  and §12 are rewritten as a record of what was approved rather than a list of
  asks, and §13 states the two assumptions I am proceeding on and the two
  things from Jafar that would make the work materially better.
- **v4 (this)** — a cold audit of v3 found fourteen gaps (§14), including a
  straight contradiction between §4.4 and §6.2. All fourteen are resolved in
  §§15–18: the ghost is now restricted, **symmetry** and **arrest** are
  approved and specified, the victim perceives, accidents are constrained,
  and the document finally has **numbers, a performance design, a persistence
  schema, a lab and an estimate.**

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

> *"the most immersive thing about KCD two is the NPCs, how they react to you
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

### And what v2 got wrong, since the same rule applies

v2's §4 was **a list of six labels I made up.** It read as a taxonomy but it
was a guess dressed as a model: six named outcomes with no generator behind
them, so there was no way to ask whether a seventh existed, no way to test
that a given geometry produced one rather than another, and no way for the
system to surprise me. That is the definition of shallow, and it is why it
looked thin at a glance.

v2's §5 was **six weapons scored on six columns that were all about the
victim and none about the player.** Nothing about what it costs to draw it,
nothing about what happens when it goes wrong, nothing about what it leaves
behind, nothing about what carrying it does to you socially, and — the real
omission — **no acknowledgement that most weapon use in a crime story is
threat, not injury.**

Both are rebuilt below against a generator rather than a list.

---

## 1. WHAT THIS GAME IS — restated *(APPROVED)*

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

## 2. RESEARCH — nine systems, and what we take from each

v2 cited four. The four still stand; five more were added for v2.1 and two of
them changed the design rather than decorating it.

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

### Splinter Cell: Chaos Theory — noise is *relative*, and this one changed the design

Chaos Theory shows two meters, light and sound, and the sound meter shows
**the ambient noise of the area alongside the noise you are making.** As long
as your noise stays under the ambient level you are effectively inaudible;
next to a running generator the ambient can mask even gunfire.
([Splinter Cell Wiki — Stealth Meter](https://splintercell.fandom.com/wiki/Stealth_Meter))

**We take masking, and it is the single best mechanical find in this
research pass.** A loudness in metres is a mediocre model; **a loudness
*relative to what is already happening* is a great one**, and it turns
systems we have already built and are currently only using for mixing into
gameplay:

- **Rain** — we model it, it changes the mix, and it is on a real weather
  clock. Rain is cover.
- **The bar** — a room with a jukebox and forty people is the loudest place
  in the game. Doing something in the back room of your own bar during a
  busy night is *quieter* than doing it in an empty alley.
- **Traffic and the market** — `streets-and-cars-spec.md` exists; a passing
  truck is a two-second window.
- **Time of day** — 4am is the most dangerous hour to make a noise, and no
  tutorial has to say so.

This gives the player a *schedule-shaped* tactical layer that costs almost
nothing to build, because the ambient bed is already computed for the mixer.

### Splinter Cell: Blacklist / general stealth AI — graduated states, not binary

Detection builds over time inside a vision cone rather than firing instantly;
cones have bands — unaware, aware-of-movement, fully aware. Hearing radius
**scales with the agent's alert state**, so an already-nervous person hears
more, which produces escalation without a state machine.
([Game Developer — Splinter Cell: Blacklist stealth AI](https://www.gamedeveloper.com/design/bringing-balance-to-stealth-ai-in-splinter-cell-blacklist),
[Stealth game sight cones](https://www.dailygamedesigns.com/games/134-stealth-game-sight-cones/))

**We take: graduated detection and alert-scaled hearing.** Never a binary
"spotted".

### Splinter Cell: Conviction — the readout with no icon, and the ghost

Conviction removed the stealth meter entirely: **in shadow the screen is
black and white; when you are visible, colour returns.** And when you break
line of sight, the game leaves **a ghost silhouette of Sam where the enemies
still believe he is**, so the player can read the AI's belief directly and
play against it. ([Splinter Cell Wiki — Stealth](https://splintercell.fandom.com/wiki/Stealth),
[Conviction](https://en.wikipedia.org/wiki/Tom_Clancy%27s_Splinter_Cell:_Conviction))

**We take both, and the ghost becomes the centrepiece of §6.** Conviction's
ghost showed one thing: where they think you are. Ours can show *what they
think they know*, because unlike Conviction we actually keep that as data.

There is a warning attached, from the same series: a Splinter Cell designer
has argued publicly that **modern lighting has made stealth games harder to
read** — realistic light is worse at telling a player whether they are hidden
than the flat, legible light of 2002.
([Game Developer](https://www.gamedeveloper.com/design/splinter-cell-designer-says-modern-lighting-have-made-stealth-games-harder-to-read))
That is a direct hit on us: we shipped wet reflections, 360 volumetric shafts
and a tonemap last night. **Our own art pass is the main threat to this
system's legibility**, and §6 has to answer it rather than hope.

### Hitman — the crime and the criminal are separate observations

The distinction that matters most for us: *"the crime can be witnessed —
your target can be seen dying — without you being spotted."* Suppressors do
not make a shot silent; **they shrink the radius in which it is heard**, and
a second shot inside a minute is treated as a gunshot rather than a
curiosity. NPCs investigate noises. Suspicion is a *meter that fills while
you are looked at*, not a trigger, and specific people —
[Enforcers](https://hitman.fandom.com/wiki/Enforcers) — see through what
everyone else accepts.
([Alert Levels](https://hitman.fandom.com/wiki/Alert_Levels),
[Witness mechanics](https://www.hitmanforum.com/t/witnesses-mechanics/21574),
[Game Informer — Hitman 3 guide](https://gameinformer.com/feature/2021/01/24/hitman-3-beginners-guide-essential-tips-to-become-a-silent-assassin))

**We take: the act and the actor are two different facts,** suppression is a
radius rather than a mute button, and **some people are much harder to fool
than others** — which for us is not a special NPC class but simply *people
who know Tom well*, which we already model.

### Red Dead Redemption 2 — the witness is a deadline, not a flag

The mechanic v2 was missing entirely. In RDR2 a crime with a witness does not
immediately become a bounty: **the witness has to reach a lawman and report
it**, and in the meantime they are a person walking somewhere. The HUD marks
each witness with an eye, **white if they cannot identify you and red if they
can** — mask and distance change which. You can **threaten** a witness and
they will usually drop it; you can outrun them; you can kill them, and
killing them in front of somebody else simply makes a new one.
([Red Dead Wiki — Eyewitness](https://reddead.fandom.com/wiki/Eyewitness),
[RDR2 Wanted System](https://www.rdr2.org/wiki/wanted-system/),
[GamesRadar](https://www.gamesradar.com/red-dead-redemption-2-bounty-and-wanted-level/))

**We take the delivery window and the identification split**, and both go
into §4. This is the mechanic that makes the minutes after a crime into
gameplay rather than a fade to black — and our version is better than RDR2's
by default, because a witness in LEDGER does not walk to an abstract lawman,
they walk to *a named person with a schedule and an opinion*, and who they
choose to tell is itself characterisation.

### Kingdom Come: Deliverance 2 — the world reacts to everything, and blood is evidence

NPCs remember hostility and theft; they follow daily routines; and reactions
fire on things that are not crimes at all — being drunk in daylight, walking
around undressed. Two details we take directly: **bloodied clothes and gear
give an intimidation bonus but can get you accused of a murder if you wear
them near the scene**, and cleanliness is a tracked, visible state.
([Game Rant — KCD2 reactive systems](https://gamerant.com/kingdom-come-deliverance-2-reactive-system-dialogue-evil-crime-npc-replay/),
[KCD2 speech checks](https://gamerant.com/kingdom-come-deliverance-2-kcd2-how-pass-speech-checks-intimidation-persuasion-coercion-dialogue/),
[KCD crimes guide](https://patchcrazy.co.uk/crimes-guide-in-kingdom-come-deliverance-2/),
[Cleanliness](https://kingdom-come-deliverance.fandom.com/wiki/Cleanliness))

**We take: the aftermath is worn.** Blood on your coat is an observable that
follows you home, into the bar, into a conversation with someone who loves
you. It is the cheapest possible way to make one violent minute cost three
in-game days, and it needs no new perception code — it is another thing
people can *see*.

### Shadows of Doubt — the forensic trail, and our nearest peer

Explicitly on our benchmark list in `design-doc.md`. Murders are simulated
rather than authored, and the evidence they leave is a real spread:
fingerprints on the weapon and on doors and light switches, **footprints**,
witness statements, phone logs, receipts. The murder weapon is a physical
object that may or may not be at the scene.
([ColePowered devblog](https://colepowered.com/shadows-of-doubt-devblog-10-gameplay-loop/),
[HackerNoon guide](https://hackernoon.com/shadows-of-doubt-a-guide-to-investigating-crime-scenes-and-solving-murder-cases),
[Dot Esports](https://dotesports.com/indies/news/shadows-of-doubt-fingerprint-database-how-to-solve-murder-cases))

**We take: the trail is physical and it is on the *object*.** This is the
strongest argument for the murder-weapon phase, and it is worth noting that
Shadows of Doubt puts the player on the *detective* side of exactly this
machine. We are building the other half of a game that already sold, which
is a good sign about the appetite and a good source of specifics.

### Dishonored — the non-lethal route has to be as expressive as the lethal one

Chaos is measured by how many people you kill and the world darkens with it;
critically, Arkane did not implement non-lethality as a restriction but built
**a full set of satisfying non-lethal answers** so that the low-chaos route
uses more of the game rather than less.
([CBR on the chaos system](https://www.cbr.com/dishonored-chaos-mechanic-ludonarrative-dissonance-arkane/))

**We take the warning.** If our only non-lethal option is "punch him and
hope", then killing is the *designed* path and everything else is a penalty
box. §5 answers this with the cosh and with threat-as-a-verb.

### Metal Gear Solid V and Sifu — forgiveness, and weight

MGSV's **Reflex Mode** gives a slow-motion window at the moment you are
spotted, and Kojima was explicit that it exists because the AI is
unpredictable, that it can be turned off, and that the player is rewarded for
not using it. ([Metal Gear Wiki](https://metalgear.fandom.com/wiki/Reflex_Mode))
Sifu's melee reads as heavy because of animation weight and hitstop — impact
frames sell a blow more than damage numbers ever do.
([Unreal Engine developer interview](https://www.unrealengine.com/en-US/developer-interviews/old-boy-john-wick-sifu-the-design-of-a-pak-mei-master))

**We take: one optional forgiveness window, and weight over numbers.** Both
land in §6.

### Assassin's Creed — the cautionary tale on social stealth

Blending into crowds was AC's signature and it was **stripped back out of the
series**, partly because tailing-and-blending missions were widely disliked
as fiddly and contrived.
([Game Developer](https://www.gamedeveloper.com/design/why-assassin-s-creed-series-isn-t-social-stealth-and-what-to-do-about-that-),
[GamesRadar](https://www.gamesradar.com/inside-the-revival-of-social-stealth-games/))

**We take the negative lesson: blending must not be a button.** In LEDGER you
are not disguised — you are a man who lives here and has a reason to be on
this street. Being unremarkable should be a *consequence of behaving
normally*, never a mode you enter. If we ever add a "blend" key we have got
it wrong.

---

## 3. THE FOUNDATION — `Core/Perception` *(APPROVED as the first thing to build)*

The system everything else needs and we do not have.

### 3.1 Vision

Per person, throttled by distance — we already LOD walkers:

| Input | Source |
|---|---|
| **Cone** | Facing + FOV. Peripheral band detects motion only |
| **Range** | Falls off; identification range is much shorter than detection range |
| **Occlusion** | Line of sight. `Acoustics` already does occlusion raycasts |
| **Light level** | `LightModel` + lamp proximity + night amount. **Already computed** |
| **Motion** | Running is far more visible than standing still |
| **Time in cone** | Detection accumulates; a glance is not a look |

Output is not a boolean. It is a **confidence that this person is being
seen**, and separately **whether they can be identified** — §4.2.

### 3.2 Hearing, with masking

Every noteworthy event emits a **sound event**: position, loudness, kind.

- Radius derives from loudness. `Core/Mixing.Reach` already maps a bus to a
  distance in metres — the same idea, reusable.
- **Occluded by walls**, attenuated by rain and by the street bed.
  `Acoustics` exists and does this for the player's ears; it needs to serve
  NPC ears too.
- **Masked by ambient**, per Chaos Theory. The audible radius is not
  `f(loudness)` but `f(loudness − ambient at the listener)`. Rain, a crowd, a
  jukebox and traffic all already exist as numbers in the mixer.
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
- **The city gets quiet hours and loud hours**, and the player learns them.

**That is the KCD2 feeling, and none of it requires violence.**

---

## 4. OBSERVATION — rebuilt as a generator, not a list

The join between the tactical and social layers. v2 listed six outcomes;
v2.1 defines the machine that produces them, of which those six are the
common cases.

### 4.1 An act is not atomic — it has **slots**, and each is perceived separately

A violent event is a short sequence, and a witness fills in whichever parts
their senses caught. Seven slots:

| Slot | What it is | Typically caught by |
|---|---|---|
| **Precursor** | You following him; the argument; you waiting in the doorway | Anyone with time and a line of sight |
| **Draw** | The weapon appearing | Vision only. Loud in social terms even if silent |
| **Act** | The blow, the shot, the struggle | Vision, or hearing if loud enough |
| **Victim** | Who went down | Vision. Identification runs separately (§4.2) |
| **Actor** | Who did it | Vision **and** identification |
| **Flight** | Someone leaving, fast | The most common real witness, and the cheapest |
| **Aftermath** | Body, blood, broken door, an object left behind | Anyone arriving later — including you, tomorrow |

**The six named observations from v2 are now emergent**, which is the point:

| Name | Slots filled |
|---|---|
| Full | Act + Victim + Actor |
| Act, no actor | Act + Victim |
| Actor, no act | Draw + Actor |
| Sound only | Act (heard), direction and distance only |
| Aftermath | Aftermath |
| Flight | Flight (+ maybe Actor) |

And the model immediately produces cases I did not think of, which is how I
know it is a model and not a list:

- **Precursor only** — someone saw you follow him in and saw nothing else.
  Useless in isolation; *devastating* when a second witness supplies the
  aftermath and the two of them talk. `CompareNotes` has never had anything
  this good to work with.
- **Draw + Flight, no act** — they saw you pull it and saw you go. They will
  swear you did it. They may be wrong.
- **Victim + Aftermath, no act, no actor** — they watched a man fall and
  never knew why. This is the suppressed-pistol case from Jafar's own
  example, and it now falls out of the model rather than being written in.

Each slot fills with its own confidence, and each becomes a `Fact` the
existing mill carries unchanged.

### 4.2 Identification is a ladder, not a flag

RDR2's white-eye/red-eye split with more rungs, because a partial
identification is the most useful thing a witness can have:

| Rung | What they can say | What decides it |
|---|---|---|
| 0 | *"Someone."* | Beyond identification range, or dark, or from behind |
| 1 | *"A man. Big. Long coat."* | Silhouette: build, gait, what you are wearing |
| 2 | *"A man with a limp."* / *"The one with the scar."* | A distinguishing mark — **and we already have limps, scars and the runner's coat, all driven by real state** |
| 3 | *"I'd know him again."* | Face seen, close and lit, but a stranger |
| 4 | *"That's Tom. Runs the bar on Hook Street."* | **Recognition** — and this is ours alone |

**The ladder is not monotonic, and that is deliberate** (clarified in the v4
review pass, where the word *ladder* was found to be misleading). Rung 3 is a
face at 8m; rung 4 is recognition at 25m. **An acquaintance therefore reaches
rung 4 without ever passing through rung 3**, and a stranger tops out at 3 no
matter how close they get. They are two different things — *how much detail
can you describe* and *can you put a name to it* — and only the second one
needs a relationship. A stranger at arm's length still cannot tell anyone who
you are.

**Rung 4 is the mechanic no AAA crime game has, and it is free to us.** A
stranger at twenty metres in the rain gets rung 1. Your neighbour, at the
same twenty metres in the same rain, gets rung 4 — because she has known you
for a month and she knows how you walk. We have a three-thousand-person
acquaintance graph with real familiarity values in it. Nobody else can do
this, and it turns *"who was on that street"* from a distance calculation
into a social one.

The consequence is a whole tactic: **the dangerous witness is not the closest
one, it is the one who knows you.** And it gives the double life real teeth —
the more people you know, the fewer streets you can act on.

### 4.3 Believing it and saying it are different — and this is the best lever we have

v2 collapsed these. Separated:

- **Certainty** — how sure they are. Feeds `Fact` confidence. Exists.
- **Willingness** — whether they will say it, to whom, and when.

Willingness is decided by things we already simulate: nerve, loyalty, what
they owe you, what they think of the victim, whether they fear the outfit —
**and what they themselves were doing there.** A man who saw you because he
was somewhere he should not have been is a witness who will not come forward,
and the player's route to safety is to find out *why he was on Hook Street at
two in the morning*.

That is the whole game's thesis expressed inside the violence system:
**secrets are loot, and the answer to a witness is usually not a knife.** It
also means the non-lethal answers are the *rich* ones rather than the
penalty-box ones, which is the Dishonored lesson applied without a chaos
meter.

### 4.4 Mutual awareness — four states, and one of them is the best beat in the game

Did *they* know they were seen? Did *you* know you were seen?

| | You don't know | You know |
|---|---|---|
| **They don't know you saw them** | Neither of you knows. The quiet horror case — you have a witness and no idea | You can act: follow, intercept, get ahead of it |
| **They know you saw them** | **The worst case, and the game must allow it.** They are already walking to tell someone and you are going home | **The standoff.** Eye contact across a street. He knows. You know he knows |

The bottom-right cell is a scene, not a state. It is the single most
dramatic moment this system can produce and it costs nothing to detect —
both perception records already exist. §6 gives it the one deliberate piece
of presentation in the whole design.

**And the two right-hand cells are the only ones that produce a ghost** (§6.2,
as restricted in v4). The left-hand column — where you were seen and did not
know it — deliberately gives the player nothing. That silence is the feature.

### 4.5 The delivery window — a witness is a deadline

Straight from RDR2, and it converts the minutes after a crime into play.

Between **observing** and **the street knowing**, the witness is a person
walking somewhere with a purpose:

1. They pick a destination — a constable, Ellis, the victim's brother, their
   own kitchen, the bar. **Who they choose is characterisation**, and unlike
   RDR2's abstract lawman ours is a named person with a schedule.
2. They walk it, on real routes, at their real speed. Somebody frightened
   runs; somebody unsure sits with it for an hour first.
3. On arrival, the observation enters the mill and becomes everybody's.

During that window the player can: **follow, talk, pay, threaten, help, or
kill** — and every one of those is itself an act that can be observed by
somebody else. Threatening a witness in front of a second witness is how a
manageable night becomes a catastrophe, and `HomicideBook.Pressure` already
proves we model that escalation honestly rather than letting the player
tidy up.

It also creates the best kind of pressure: **you know it is happening and you
have to decide fast, in public, while the street watches you decide.**

### 4.6 Witnesses are wrong, and being wrong is content

Partial slots plus a rung-1 or rung-2 identification plus familiarity bias
produces genuine misattribution: *a long coat, at night, near the docks* is
Nikos to somebody who expects Nikos. We already have contradiction, decay and
discredit, and none of them mean anything if every fact is true.

Three things follow:

- The player can be **wrongly accused**, which the story wants.
- The player can **let a false belief stand**, which is a real moral choice
  and costs nothing to implement — it is the absence of an action.
- The player can **plant an impression** rather than evidence: be seen doing
  something innocuous in the wrong coat. Cheap, deniable, and very much this
  game.

### 4.7 What this buys, stated as testable claims

Each of these is a sim gate, not a hope:

1. One event, four witnesses at four positions, produces **four different
   slot sets**.
2. Two witnesses with disjoint partial slots, put in the same room, produce
   via `CompareNotes` **a truth neither of them held**.
3. The same witness at the same distance in the same light reaches **rung 4
   for an acquaintance and rung 1 for a stranger.**
4. A witness intercepted before delivery leaves **no trace in the mill**; the
   same witness intercepted one minute later leaves an indelible one.
5. A rung-2 identification of a common coat produces a **named accusation of
   the wrong man** at least sometimes, and the mill carries it as a fact with
   normal confidence.

---

## 5. WEAPONS — the tactical table, rebuilt

### 5.1 First: the threat is the main use

The correction to v2's biggest omission. In a crime story, most of what a
weapon does happens *before* anyone is hurt. **Brandish is a verb**, and it
has its own outcome table, driven by the target's nerve and their read of
you:

| Outcome | When | What it costs you |
|---|---|---|
| **Comply** | High fear, low nerve, private | Nothing now. They remember, permanently |
| **Freeze** | The common case | Time, which is the resource that matters |
| **Flee, screaming** | Low nerve in public | A loud sound event, and now everyone is looking |
| **Call the bluff** | High nerve, or they know Tom is not a killer | Humiliating, public, and it hardens them |
| **Escalate** | They are armed, or they are one of the outfits | The worst outcome available and it is on you |

This single verb does more work than any weapon row below it: it makes
carrying meaningful without killing, it gives fists and knives a non-lethal
expressive range, and it means a pistol is terrifying to *hold* even if you
never fire it.

**And it is reversible in exactly one direction.** You can always escalate
from threat to act. You can never un-draw.

### 5.2 The roster is families and objects, not a list of seven

v2.1 offered seven rows. Jafar: *"7 feels too few and low budget."* Correct,
and the fix is not "add three more knives" — it is that a small team makes an
arsenal feel large the way **Hitman** does: a modest set of *carried* weapons,
a much larger set of *objects in the world*, and a category of kill that uses
no weapon at all. Blood Money's accident system is the canonical example —
pushing a man over a rail expands the perceived arsenal far more than another
pistol does. ([Hitman Wiki — Staged Accident](https://hitman.fandom.com/wiki/Staged_Accident),
[Weapons](https://hitman.fandom.com/wiki/Weapons_(Feature)))

For comparison, Mafia II — a bigger team, a similar setting — shipped roughly
fifteen firearms and almost no melee.
([Mafia Wiki](https://mafiagame.fandom.com/wiki/Weapons_in_Mafia_II),
[IMFDB](https://www.imfdb.org/wiki/Mafia_II)) We should not try to beat that on
gun count. We should beat it on **what each object means**, and win on breadth
by counting the things Mafia II did not have: the environment, and the kit.

**Seven families. Around sixteen carryable objects, plus the world.**

#### Family 1 — Hands (2)

| | Notes |
|---|---|
| **Fists** | Loses to a ready man. Loud, slow, public, and it leaves him alive |
| **Brass knuckles** | Era-correct, pocket-sized, innocent-looking. Turns fists from *loses* into *wins fast* — and marks the face, so the man you left alive is walking evidence |

#### Family 2 — Blunt (4)

| | Notes |
|---|---|
| **Cosh / blackjack** | The reliable non-lethal. Leaves bruising a doctor can read |
| **Bottle** | Everywhere, innocent until swung, breaks — then you are holding a stub and bleeding |
| **Bar / tyre iron / pipe** | A world object, not carried. Heavy, lethal by accident more than intent |
| **Baseball bat** | Carryable, *not* concealable. **A man walking down Hook Street with a bat has already said something**, and that is its real use |

#### Family 3 — Edged (4), and they are genuinely different

| | Notes |
|---|---|
| **Switchblade** | Small, concealable, fast. Unreliable through a winter coat |
| **Kitchen knife** | Found in every building in the game. **Untraceable by being ordinary** — a knife that came from the victim's own kitchen has no provenance to follow |
| **Ice pick** | Historically the mob's own tool: cheap, needs no permit, and explains itself if found on you. Leaves a wound a hurried coroner can miss ([Deadliest Warrior Wiki](https://deadliestwarrior.fandom.com/wiki/Ice_Pick), [National Crime Syndicate](https://nationalcrimesyndicate.com/top-5-weapons-used-mob/)) |
| **Straight razor** | Terrifying to *brandish* and poor at killing. Exists almost entirely for §5.1 |

#### Family 4 — Ligature (2)

| | Notes |
|---|---|
| **Wire / garrote** | Silent, from behind, cannot be aborted |
| **Cord, belt, scarf** | The improvised version. Same profile, slower, worse, and always to hand |

#### Family 5 — Firearms (5), **Phase 5**

Small calibres, because that is what this fiction actually used: the .22, the
.32 and the .38 snub were the mob's working guns, and most were thrown away
within the hour. ([GunMag Warehouse — Guns of the Mob](https://gunmagwarehouse.com/blog/guns-of-the-mob-the-most-popular-firearms-used-by-the-mafia/))

| | Notes |
|---|---|
| **.22 target pistol** | Quiet for a gun, small, and **contemptuous** — a .22 to the back of the head says *this was a job*, and the street reads it that way |
| **.38 snub revolver** | The everyman's gun. **Leaves no casing**, because revolvers do not eject — a real forensic difference at zero art cost |
| **.45 automatic** | Loud, war surplus, **throws brass onto the pavement** that Ellis can find and tie to the weapon |
| **Suppressed .22** | The quiet one. A radius, not a mute button |
| **Sawn-off shotgun** | Not concealable, one use, one message, and no taking it back |

**The revolver-versus-automatic distinction is the kind of depth that costs
nothing and pays forever.** Choosing the snub because it leaves nothing behind
is a real decision made with real knowledge, and it never needs a tutorial.

#### Family 6 — The environment, and this is where the roster stops being a list

**An accident is the only violence in this game that produces no crime.** The
observation model returns *Aftermath* with the wrong content: a man fell down
the stairs. Nobody is looking for anybody.

Stairs and railings. A window. The dock. A road and a moving car. Fire. Water.
The machinery in the back of a workshop. A bad drink and a long walk home.

These use places we have already built, they need no new weapon art, and they
are **thematically exact for Tom Novak** — a man who runs a bar and is not a
killer, right up until a stairwell solves a problem for him. This family alone
does more for the felt size of the arsenal than five more pistols would.

**Three constraints, added in v4 (audit finding D), because unqualified this
family ends the design.** §11 worried that the threat verb might solve
everything and nobody asked the same question here: if the stairs always work,
the optimal player never touches a weapon again.

1. **It needs position and privacy that most situations do not offer.** He has
   to be at the top of the stairs, near the rail, beside the road — and you
   have to be alone with him there. It is opportunistic, not a plan you can
   always execute.
2. **Being seen doing it is the worst observation in the game.** There is no
   ambiguity in a push: no weapon, no struggle, no argument to point at. A
   *Full* slot set on an accident is more damning than one on a stabbing.
3. **A suspicious death still gets a coroner.** An accident converts a manhunt
   into an inquest, not into nothing — and an inquest is a slow, quiet, very
   LEDGER kind of pressure. Two accidents around one man is itself a pattern.

BalanceLab proves it, the way `RunViolenceLab` proved the kill-the-witness
trade rather than asserting it.

#### Family 7 — Kit, which is not weapons and decides whether any of it works

Gloves. A second coat, to change into. A bag. A car. A torch. A bottle of
something, to make a man slow and talkative. Keys and the access they buy.

This is what makes the loadout-at-the-door decision (§7.1) interesting: **the
best answer is often not another weapon.**

### 5.3 The columns — thirteen axes, and this is where the depth actually is

Every carried object is scored on all of these. Sixteen objects × thirteen
axes is a far bigger design space than a longer list of guns, and none of it
is a damage number.

| Axis | Why it matters |
|---|---|
| **Noise made** | Feeds hearing directly |
| **What can mask it** | Rain, a crowd, a jukebox, traffic — the schedule becomes tactical |
| **Reach** | 0.8m to 20m+ |
| **Time to ready** | The draw is a commitment and it is seen |
| **Can it be aborted?** | The wire cannot. Everything else can |
| **Victim cries out** | The difference between one witness and four |
| **Against a ready, armed man** | Most of the roster says *lose*. Tom runs a bar |
| **Leaves a body** | Or does not — the cosh and the knuckles |
| **What it leaves at the scene** | Wound signature, brass, glass, nothing |
| **What it leaves on you** | Blood on a coat is a problem at 9am |
| **Carrying it** | Innocent, concealable, damning, impossible to explain |
| **Provenance** | Bought and traceable, or a kitchen knife nobody can follow |
| **How it fails** | The character of the weapon, and the column v2 was missing |

Worked examples, so the table is not abstract:

| Weapon | Noise | Ready | Abort | Cries out | On you | At the scene | Fails by |
|---|---|---|---|---|---|---|---|
| **Fists** | Scuffle | — | Freely | Throughout | Knuckles | Your face in his memory | Losing, in public, slowly |
| **Cosh** | Low thud | ~1s | Yes | Once | Nothing | Bruising a doctor reads | Not dropping him first time |
| **Ice pick** | Low | ~1s | Until it lands | Briefly | Blood | A wound that reads as something else | His hand getting to it |
| **Wire** | **None** | ~2s, both hands | **No** | **No** | Nothing | A mark on the neck | His hand getting under it |
| **.38 snub** | **Very loud** | ~1.5s, seen | Yes, but the draw was seen | No | Nothing | **No casing** | Missing, and now everyone is coming |
| **.45 auto** | **Very loud** | ~1.5s, seen | Same | No | Nothing | **Brass on the pavement** | Same, plus evidence |
| **Suppressed .22** | One room | ~1.5s, seen | Same | No | Nothing | A casing, no memory of a bang | Missing, quietly |
| **Stairs** | A fall | — | Until you touch him | Once | Nothing | **A man who fell down the stairs** | Him surviving it |

### 5.4 Situations, which is how a player actually thinks

- **Crowded street, must be now** → suppressed .22. He drops; nobody knows
  where it came from. *Victim + Aftermath* for everyone, no actor slot at all.
- **Alone with him in the back room, on a busy night** → any knife. He cries
  out; the jukebox eats it. Masking is the entire reason this works.
- **It must never be a crime at all** → the stairs.
- **It must not be traceable to you** → his own kitchen knife, left there.
- **It must leave nothing at the scene** → the snub, not the automatic.
- **You want it heard** → the .45, or the sawn-off. Sometimes the point of
  violence is the message.
- **He must stop and must not die** → cosh, or knuckles.
- **You do not want this to happen at all** → brandish, and let him decide.

### 5.5 What stays out

No damage numbers, no health bars, no durability, no crafting, no upgrades —
consistent with `combat-spec.md` §4. **No rifles, no automatic weapons.** A
Thompson is a different genre; this game tops out at a sawn-off, and it should
feel like too much when it happens.

## 6. FEEL AND LEGIBILITY — the section the quality bar demands

> *"it has to be EXCEPTIONALLY GOOD from a game feel and UI/UX pov. we don't
> ship low quality / AI slop here."*

This is the part that decides whether any of the above is any good, so it
gets designed rather than assumed.

### 6.1 The problem, named

`combat-spec.md` §4 committed to an interface that is *almost entirely
absent* — the simulation is the interface. That doctrine is right, and
**perception is the one place it needs a stated exception**, because a rule
the player cannot predict is not immersive, it is unfair. Thief put a gem on
the screen for a reason.

And we have made it harder for ourselves: the lighting pass shipped last
night — wet reflections, volumetric shafts, tonemap, vignette, grain — is
exactly the *realistic light* that a Splinter Cell designer has publicly
blamed for making modern stealth unreadable. **A more beautiful street is a
less legible one.** We should assume this is true of ours until a person
plays it.

The player must be able to answer three questions at all times, and nothing
else:

1. **Am I visible right now?**
2. **How far did that carry?**
3. **Who noticed, and what do they think they know?**

### 6.2 The four candidate treatments, and the recommendation

| | Approach | Verdict |
|---|---|---|
| (a) | **Meters** — Thief's gem, Chaos Theory's two bars | Explicit, learnable, proven. And wrong for us: Tom Novak is a man who runs a bar, not an operative with a HUD |
| (b) | **Conviction desaturation** — the frame itself tells you | Beautiful, no icons, and we own the post stack. Risk: it fights the art we just built |
| (c) | **Purely diegetic** — read it off heads turning | Purest, and what the combat spec wants. Fails alone: **you cannot see behind you** |
| (d) | **Hybrid, weighted to the world** | **RECOMMENDED** |

**The recommendation, concretely:**

**Visibility — the frame breathes, and there is no icon.**
Conviction's insight at a tenth of the strength. When you are lit and
exposed, the vignette opens and the image cools very slightly; in shadow it
closes and warms. Sub-threshold in a screenshot, learnable inside an hour of
play, and it never once says the word "detected". We already own every knob
this needs and — crucially — **we have just built the tooling to prove it
actually changes the pixels** (`ImageStats`, and the A/B gates that caught
five systems built and not running).

**Noise — one ring, one moment.**
At the instant a sound is made, a single ring on the ground at the true
audible radius *after* occlusion and masking, and then it is gone. Not a
persistent overlay, not a meter. It teaches the model in three or four uses
and then the player stops needing it — which is the mark of good feedback.
This is Chaos Theory's ambient bar converted into something a third-person
game can show without a HUD.

**Attention — four redundant channels, and audio carries it, not animation.**

v2.1 said *"a person who has noticed you looks at you"* and left it there.
Jafar, correctly: *"feels not explicit enough and depends a lot on how clearly
we model and animate characters."* That is the right objection. Our bodies are
thirteen boxes; faces do not exist; a held look versus a glance is exactly the
read that capsules cannot deliver. Betting the most important feedback in the
game on the weakest thing we own is how this fails.

So the primary channel is **sound**, which is the strongest thing we own — we
have a voice engine, generated barks, spatial audio, an ambient bed per space
and adaptive music stems that already run. And there are **four channels, made
deliberately redundant: any two of them should be enough.**

**1. The street goes quiet — and this is the best idea in the section.**
The exact inverse of masking (§3.2), for free, from the same system.
Conversation near you stops. The jukebox keeps playing; the voices around it
do not. A crowd going quiet is the most recognisable "you have been noticed"
signal a human being knows, it is *more* frightening than any icon, it needs
**zero animation**, and we already model the ambient bed per space and already
generate NPC-to-NPC speech. It also runs backwards: **the street resuming is
how the player learns the event is over**, which is the other thing
stealth-adjacent games are chronically bad at communicating.

**2. Barks — the person says something.** `BarkGen` and the voice engine
exist. *"Hoy."* A hushed *"that's him."* Thief did this in 1998 and it is
still the standard, because a bark carries **state and direction at once** —
direction free from spatial audio, which is the answer to the objection that
purely diegetic feedback fails behind you.

**3. Behaviour break — the motion changes, which reads at any fidelity.**
Not a facial expression. A walker who was walking **stops**. A pair who were
talking **turn**. The eye detects a change in motion far better than it reads
a face, so this channel works on boxes today and gets *better* when characters
land rather than depending on them. Escalation stays self-explaining because
an investigating NPC **walks toward the thing**.

**4. One music stem.** We built adaptive layers driven by real state and they
are running in the build. A single low stem enters when someone's attention is
genuinely on you, and nothing else in the mix is allowed to do that. It is an
emotional channel rather than an informational one, and it is the one players
read fastest.

**And an explicit marker, in accessibility, off by default.** Stated up front
rather than retrofitted, per `combat-spec.md` §4. Three of the four channels
above are audio, so hearing loss disables the system almost entirely — the
honest answer is an optional small eye at the frame edge, RDR2-style, **white
when they cannot identify you and filled when they can**, rather than
pretending the diegetic version serves everybody. It is a presentation option,
not a difficulty setting.

**The test that keeps this honest:** play a scene with the sound off, and play
it with the picture off. If either pass leaves the player unable to tell they
were noticed, the channels are not redundant and one of them is decoration.
This is checkable in a playtest and it is on the QA matrix rather than in a
designer's hope.

**What they think they know — the ghost, RESTRICTED (v4, audit finding A).**

v3 showed this for every witness, which quietly destroyed §4.4's *"quiet
horror case"*: if the ghost always appears, being seen without knowing it
cannot exist. **The ghost now appears only when the awareness was mutual —
only when Tom saw them see him** (§4.4, the two right-hand cells).

That makes it honest as well as compatible. It is no longer a readout of
another person's mind, which Tom has no right to; it is a picture of a thing
the character actually experienced — you caught her eye, so you know roughly
what she got. **When you are seen and do not notice, there is no ghost and no
warning at all**, and the first you hear of it is a rumour three days later.

Within that restriction it works as designed. Conviction leaves a silhouette
where the enemy believes you are; ours shows *the shape of their
misunderstanding*, because our witnesses hold slots and rungs rather than a
position:

- They only got rung 1 → the ghost is **a coat with no face**.
- They got the act but not the actor → the ghost stands over the victim and
  **has no head turned toward you at all**.
- They got you at rung 4 → **the ghost is you**, and that is the moment the
  player should feel their stomach drop.
- They are wrong → **the ghost is Nikos**, and the player can see the lie
  they are about to be given, and decide whether to correct it.

It appears for a moment as you break away, and never again. It is the
observation model made visible, it costs almost nothing on top of the data
we would already be keeping, and I am not aware of another game that shows
the *content* of a witness's belief rather than its location.

**It is not a legibility channel.** §6.2's four channels cover *being
noticed*, which the player is owed. What a witness concluded is not owed, and
the restriction above is what keeps the dread in the design.

**The standoff gets the one flourish.** When mutual awareness closes (§4.4,
bottom-right), the street audio ducks for about four tenths of a second and
the vignette tightens. Not slow motion, not a cutscene, no sting. One beat
that says *he has seen you, and he knows that you know*. Used exactly once
per event and never for anything else, so it never becomes wallpaper.

### 6.3 Feel

- **The draw is the most important animation in the game.** It is slow enough
  to be a decision, visible to everyone in a cone, and it cannot be taken
  back. Everything social about weapons hangs off this one second.
- **Weight over numbers.** Sifu's lesson: impact frames, hitstop and recovery
  sell a blow; our `VerbBeat` already models anticipation → action →
  consequence → recovery, which is the right shape and is already tested.
- **Sound carries the violence**, per `combat-spec.md` §4 — breath, the scuff
  of a foot, the crowd changing. And now the crowd changing is *literally the
  perception system reacting*, not a canned layer.
- **One optional forgiveness window**, MGSV's Reflex reasoned honestly: a
  brief slow at the moment you are first noticed, **off by default**,
  presented alongside the existing telegraph-window option as a tempo
  setting rather than a difficulty. Kojima's own framing — the AI is
  unpredictable, so give people a valve, and reward not using it.

### 6.4 How we prove it, which is the part we are actually good at

Every claim above becomes a gate, because last night established that a
system which is *built* is not a system which *runs*:

- The vignette and temperature **measurably change** with light level —
  `ImageStats` A/B, the same shape that caught the post stack doing nothing
  for weeks.
- The noise ring's radius **equals the acoustic model's radius**, asserted
  against the model rather than a copied constant. (The `scoreAudible` lesson:
  assert proportionality, never re-type the number.)
- The ghost matches **the witness's belief record**, not the player's true
  position — the one test that catches the entire class of bug where a
  perception UI quietly shows the truth instead of the belief.
- A frame-time budget for perception across ~50 visible walkers, measured on
  Jafar's machine, because ours has no GPU.

---

## 7. ACQUISITION AND CARRY — the part of the brief v2 never answered

> *"we need kind of, like, an inventory, a way to buy, or acquire weapons by,
> I don't know, buying from someone, stealing, finding randomly."*

### 7.1 Carrying: hands and a coat, not a grid

The constraint is **concealment, not weight.** You have your hands and what
fits under a coat: realistically two objects, three if one of them is small
and you do not mind being obvious.

The decision is *what did I bring tonight*, and it is made **at the door** —
before you know what the night holds, which is what makes it a decision. No
grid, no weight, no bag management; that is a different game and it is not
this one.

There is one screen and it is the coat, not a menu: what is on you, and what
is at home in the bar.

### 7.2 The frisk, and why concealment is the real stat

Carrying is a state other people can discover. Ellis can ask. A doorman can
check. Someone who bumps into you can feel it. A knife found on you at the
wrong moment is worse than the knife ever was — which is why the "carrying
it" row of §5.2 matters more than the reach row.

### 7.3 Where weapons come from — four routes, all of them social

**No random world loot.** A pistol in a bin is a video game; a pistol you can
name the seller of is this game.

1. **Bought, from a person.** A supplier is a *character* with a schedule, a
   price, an opinion of you, and a memory. He can be leaned on later, by you
   or by Ellis. Buying is a relationship, and the relationship is the
   interesting half.
2. **Stolen.** From a person or a place, on a real schedule — and **they
   notice it is gone**, at a time you can predict if you know their routine.
   A stolen weapon is a weapon somebody is already angry about.
3. **Taken.** Off someone in a fight, or off a body. Free, immediate, and
   the worst possible provenance.
4. **Found — exactly once, and authored.** Mickey's. There is something in
   the bar that was his, and finding it is a story beat rather than a loot
   drop. Everything else is earned.

### 7.4 Provenance is permanent, and it is the Phase-4 payoff

Every weapon instance remembers where it came from and what has been done
with it. That is what makes the murder weapon a real object: it can be
found, it can be traced back to the man who sold it, it can be planted, and
**disposing of it is a verb that can itself be witnessed** — which is the
best single idea in v1 and it survives untouched.

Shadows of Doubt is the proof that this half is compelling, since it puts
the player on the *other* side of exactly this machine.

---

## 8. REACTION — what people DO

Graduated, per person, driven by their own observation and temperament
(`Gossiper` already has nerve and greed):

1. **Notice** — head turns. Free, constant, and the thing that makes a street
   feel alive.
2. **Investigate** — walks toward a noise. The single highest-value behaviour
   in the whole system: it turns one sound into a moving problem, and it is
   self-explaining to the player.
3. **Alarm** — shouts. Which is itself a loud sound event, so alarm
   propagates through the same hearing system. **Panic is emergent, not
   scripted.**
4. **Flee** — runs. Nerve decides.
5. **Deliver** — goes to tell someone, per §4.5. The deadline.
6. **Fetch the law** — goes to find Ellis. We have her, and she has a ladder.
7. **Intervene** — rare, high-nerve, and it should be genuinely dangerous.

Bodies are discovered by whoever walks past next, which means **time and
routes matter** — an alley at 3am buys you hours; the market at noon buys
you seconds.

---

## 9. WHAT ALREADY EXISTS, AND WHAT IS GENUINELY NEW

**Exists and is reusable:**
- `Acoustics` — occlusion, space kinds, wetness. Currently player-ears only.
- `Mixing.Reach` — loudness → metres, per bus. And the ambient bed, which is
  what masking needs.
- `LightModel` + the lighting pass — light level anywhere, any hour.
- `Notoriety`, `HomicideBook`, `Police` — reusable unchanged.
- `Violence.Saw` and `KillingConfidence` — **NOT reusable, and v3 was wrong to
  list them as such** (audit finding E). The observation model replaces what
  they do, and leaving both would give the build two systems deciding who saw
  a killing. Disposition, fixed before Phase 2: `Violence.Saw` becomes a thin
  adapter over `Core/Observation`, `KillingConfidence` is *derived* from slots
  and rungs rather than computed separately, and a test asserts the old path
  has no remaining callers. This project has already lost a night to a system
  that was built, correct and attached to nothing; two live systems doing the
  same job is the same bug with the sign flipped.
- `Core/Combat` phases 1–4, tuned.
- Gossip mill: facts, confidence, decay, contradiction, `CompareNotes`.
- Walkers with facing, routines, nerve, gaze and head-turn.
- **The acquaintance graph** — which is what makes §4.2 rung 4 possible.
- Limp, scars, the runner's coat — the rung-2 distinguishing marks.
- `ImageStats` and the A/B gate tooling — which is how §6 gets proven.

**Genuinely new:**
- `Core/Perception` — vision with light and occlusion; hearing with loudness,
  masking and alert scaling. **The big one.**
- `Core/Observation` — slots, rungs, certainty/willingness, mutual awareness,
  the delivery window, and false belief.
- Reaction behaviours: investigate, alarm propagation, flee, deliver, fetch.
- The weapon table, brandish-as-a-verb, and carry/concealment.
- Acquisition: the supplier, theft with a noticing owner, provenance.
- The legibility layer in §6, including the ghost.
- Blood and cleanliness as an observable state on the player.
- Performance: perception for ~50 visible walkers, throttled by distance.
  **The main technical risk and a real one.**

---

## 10. PHASING — each phase playable, provable, and useful alone

**Phase 1 — perception, no weapons.** Vision with light and occlusion;
hearing with loudness and masking. NPCs notice, turn, and investigate.
**Ship this and play it even if weapons never follow.**

*Machinery gate:* a walker in light is detected at greater range than one in
shadow; a sound behind a wall is not heard; a sound under the ambient floor is
not heard.

***Behaviour* gate, added in v4 (audit finding J), and this is the one that
matters.** v3 tested only the machinery, which means a green Phase 1 could
have shipped a city that computes perfectly and reacts to nothing — this
project's signature failure mode. So the reactions to non-crimes ship *in*
Phase 1 rather than waiting for Phase 2, and the gate asserts behaviour:

- **Loitering** under a lamp for thirty seconds produces at least one person
  who looks and one who remarks on it.
- **Running at night** in a residential street turns heads that walking does
  not.
- **A slammed door** at 3am brings somebody to a window; the same slam at noon
  does not.
- **Standing where you should not be** — behind a counter, in a yard — is
  noticed faster than standing on the pavement.

That list *is* §3.3's promise, and until it is green Phase 1 is not done.

**Phase 1b — legibility, alongside it.** The vignette response and the noise
ring. Small, and it goes in *with* Phase 1 rather than after, because a
perception system nobody can read cannot be evaluated by a playtest.

**Phase 2 — observation and reaction.** Slots, rungs, willingness, the
delivery window, the ghost. Alarm propagates; flee and fetch. Sim gate: the
five claims in §4.7.

**Phase 3 — melee and carry.** Fists, cosh, knife, improvised. Brandish as a
verb. Carrying, concealment and the frisk. Blood on clothes. Sim gate: a
knife killing in an empty alley leaves no witness; the same killing in a
market does; the same killing in the back room of a busy bar is heard by
nobody and seen by two.

**Phase 4 — the murder weapon.** Provenance, acquisition routes, disposal as
a witnessable verb, Ellis looking for the object.

**Phase 5 — firearms.** Pistol and suppressed pistol, where the perception
model finally pays off in full. Deliberately last: the loudest change to the
fiction and the easiest thing to get wrong.

---

## 11. RISKS, HONESTLY

1. **A perception system too coarse to be fair.** The main one. Stealth-
   adjacent systems live or die on predictability, and §6 exists entirely to
   answer this. If a player cannot tell why they were seen, no amount of
   sophistication saves it.
2. **Our own art fights our own legibility.** Named in §6.1, and it is a
   genuine tension between two things we both want.
3. **Performance.** ~50 walkers × vision × hearing, every frame-ish, on a
   machine we have never measured. Throttling is designed in from the start;
   the budget gets a gate.
4. **The threat verb being better than every other verb.** If brandishing
   solves everything, we have built a different game. It needs the
   call-the-bluff and escalate outcomes to have real teeth, and BalanceLab is
   where that gets proven rather than asserted.
5. **Accidents becoming the dominant strategy.** Same shape as risk 4 and
   missed until the v4 audit. Constrained in §5.2 Family 6; proven in the lab.
6. **Facing not being readable**, which is the condition Jafar attached to the
   symmetry rule. §15.1 states the rule against what we can actually render
   and gives it a measurable gate rather than an assurance.
7. **Scope.** This is the largest single proposal in the project. Phase 1 is
   the hedge: it is worth playing on its own, and if it is not, we stop.

---

## 12. THE APPROVAL RECORD

Everything in this document is approved. Kept as a record of what was asked
and what changed, because the corrections are the reason it is any good.

| Point | Verdict | What the challenge changed |
|---|---|---|
| §1 — crime game in a city that perceives, reacts and remembers | **APPROVED** (v2) | Replaced *"the antagonist is gossip"*, which had become a straitjacket |
| §3 — perception before weapons; Phase 1 shippable alone | **APPROVED** (v2) | — |
| §5 — firearms exist, at the last phase | **APPROVED** (v2) | Withdrew v1's refusal to build guns at all |
| §4.5 — the delivery window | **APPROVED** (v2.1) | The addition that turns the minutes after a crime into play |
| §6 — legibility in general | **APPROVED** (v2.1) | — |
| §4 — slots, rungs, willingness, awareness | **APPROVED** (v3) | *"a bit shallow"* → replaced six invented labels with a generator; recognition by people who know you became the centre |
| §5 — the roster | **APPROVED** (v3) | *"7 feels too few and low budget"* → seven families, ~16 carried objects, **the environment as a family of its own**, and kit |
| §6.2 — how the player knows they were noticed | **APPROVED** (v3) | *"depends a lot on how clearly we model and animate characters"* → four redundant channels led by **audio**, plus an accessibility marker |
| §7 — acquisition and carry | **APPROVED** (v3) | *"I don't get it"* → separated *what is on you tonight* from *where it came from*; provenance is what makes Phase 4 work |

## 13. BEFORE THE FIRST LINE — assumptions and asks

**Nothing blocks Phase 1.** It is Core work plus Unity wiring, no purchases,
no accounts, no assets. Two assumptions are stated here rather than discovered
in the diff:

1. **Perception is computed for events the player is party to, not for the
   whole city.** Two NPCs seeing each other across a market does not run a
   vision cone; the Mid band's gossip mill already handles NPC-to-NPC
   information without bodies, and it is tested. Extending sight and hearing
   to all three thousand residents would cost the frame budget and buy
   almost nothing the mill does not already produce. Revisit if it ever feels
   like the world only reacts when the player is looking.
2. **Phase 1 ships to a playtest on its own**, before observation and before
   any weapon exists, per §10 — a street that notices you is worth playing
   and worth judging by itself. If it is not good on its own, that is the
   cheapest possible moment to find out.

**Two things from Jafar that would materially improve the work**, neither
blocking:

- **The F1 frame-rate number**, once, from anywhere in the current build.
  Perception for ~50 visible walkers is the main technical risk in this
  document (§11.3) and CI has no GPU, so the throttling design is currently
  being chosen against a number nobody has ever measured.
- **The voice listening pass**, ~15 minutes with `1 LISTEN.bat`. Two of the
  four attention channels in §6.2 are voice — barks, and the street going
  quiet. They can be built and gated with placeholder audio; they cannot be
  *judged* without real voices.

---

## 14. AUDIT OF THIS DOCUMENT — 2026-07-29, after approval

Read cold, looking for holes, at Jafar's request. Fourteen findings. Four of
them are design problems rather than gaps, and one is a straight contradiction
between two things this document is proud of.

Nothing here reopens the approval. Items marked **NEEDS A CALL** change
something Jafar approved and should not be resolved by me alone.

### A. The ghost contradicts the dread — **the worst finding, and it is real**

§4.4 calls the case where *neither of you knows* **"the quiet horror case"**
and treats not knowing as a feature. §6.2 then shows the player a ghost of
what the witness believes.

**If the ghost always appears, the quiet horror case cannot exist.** The two
best ideas in the document cancel each other out and no version of this
document noticed.

**Fix, and it improves both:** the ghost appears **only when Tom saw them see
him** — the two right-hand cells of §4.4. It becomes not a readout but *the
representation of a thing the character actually experienced*: you caught his
eye, so you know what he got. When you were seen and did not notice, **there
is no ghost and no warning**, and the first you hear of it is a rumour three
days later. That is the horror, preserved, and it also removes the fictional
cheat of showing the player another person's mind.

**Consequence:** the ghost stops being a general legibility device, so §6.2
loses a channel it was leaning on. That is correct — legibility should cover
*being noticed* (four channels, all preserved) rather than *what they
concluded*, which the player has no right to know.

### B. Nothing here is predictive — the player can plan nothing — **NEEDS A CALL**

Every device in §6 is **reactive**: it tells you that you were seen, that a
noise carried, that someone is walking to tell somebody. Thief's light gem is
**prospective** — it tells you your state *before* you commit.

**Stealth-adjacent play is planning, and this document gives the player
nothing to plan with.** The vignette covers *am I lit*, and that is the only
forward-looking signal in eighty pages. There is nothing for *could that man
see this doorway* or *would a shot here reach the market*.

Three options:

1. **Symmetry, stated as a rule the player can learn:** if you can see his
   eyes, he can see you. Zero interface, one sentence in the how-to-play, and
   it makes the camera the planning tool. **Recommended.**
2. **A survey verb** — hold a key to stand still and study the street;
   attention channels sharpen, sounds are labelled by direction. Diegetic,
   costs a moment of time, no HUD.
3. Cones drawn on the ground. Legible, and completely wrong for this game.

Option 1 is nearly free and is the one I would build. It needs a call because
it constrains the camera and the vision model to agree, forever.

### C. The victim is not a person in this document

The whole spec is player → target → witnesses. **The target perceives too**,
and the document never says so. He can see you coming, run, fight, scream,
**survive**, recognise you, and become the most dangerous witness in the game:
the one who was close, lit, facing you, and has every reason to talk.

`combat-spec.md` already models injury, feuds and capability loss, so the
survivor is half-built. It is not referenced here once.

**Fix:** the target runs the same perception and observation model as any
witness, with a bias — being attacked guarantees rung 3 and usually rung 4.
"He lived" becomes the loudest possible outcome, which is exactly right for a
game where killing is meant to cost more than it saves.

### D. Accidents may be the dominant strategy — **the risk §11 missed**

§11.4 worries that the threat verb solves everything. Nobody asked the same
question about Family 6. **"The only violence that produces no crime"** is a
sentence that, unqualified, ends the design: if the stairs always work, the
optimal player never touches a weapon again.

**Fix, three constraints:** an accident needs *position and privacy* that most
situations do not offer; **being seen doing it is worse than any other
observation** because the act reads as unambiguous murder; and a suspicious
death still gets a coroner, so it converts a manhunt into an inquest rather
than into nothing. BalanceLab proves it the way `RunViolenceLab` proved the
kill-the-witness trade.

### E. Two competing witness systems — **an integration ambiguity, and this project has been bitten by exactly this**

§9 lists `Violence.Saw` and `KillingConfidence` as *"exists and is
reusable"*. They are not reusable — the observation model **replaces** what
they do. Left as it stands, the build ends up with two systems deciding who
saw a killing, and the project has already lost a night to a system that was
built, correct and attached to nothing.

**Fix:** state the disposition explicitly before Phase 2 starts.
`Violence.Saw` becomes a thin adapter over `Core/Observation` or it is
deleted; `KillingConfidence` is derived from slots and rungs rather than
computed separately. Written down now, checked by a test that the old path
has no callers.

### F. No numbers anywhere, in a document whose project motto is *check the ruler before the reading*

Detection range, identification range, FOV, peripheral band width, seconds of
accumulation, the ambient floor in dB-equivalents, how far a .38 carries, how
long a delivery walk takes. **Not one figure appears in this spec**, so the
first implementation will invent them all and there will be nothing to check
it against.

**Fix:** a calibration table before Phase 1 — first-guess values, each with
the reason it was chosen and the gate that would catch it being wrong. They
will all move. The point is that they move *from* somewhere.

### G. The performance risk is named three times and designed nowhere

*"Throttled by distance"* is the entire mitigation for the #3 risk, and the
project already has a Near / Mid / Far band model that this document never
mentions.

**Fix:** say it concretely — only the Near band perceives; vision recomputes
on a staggered schedule rather than every frame for everyone; hearing is
event-driven and therefore nearly free; a stated millisecond budget with a
gate that fails the build when it is exceeded. This is cheap to specify and
expensive to retrofit.

### H. Persistence is never mentioned once

New durable state: observation records, in-flight witnesses mid-delivery,
carried objects, provenance, blood on clothes, mutual-awareness pairs.
**Saving mid-delivery and reloading is an obvious case and the document is
silent on it.** The project has atomic saves, backups and slots, so the
machinery exists; the schema work does not.

### I. There is no acute response — what happens the moment a constable sees you — **NEEDS A CALL**

`Police` has procedure → investigation → manhunt, which is a *slow* ladder
measured in days. This document adds acts that a policeman can watch happen,
and then says nothing about the next sixty seconds. Is there a chase? An
arrest? Can the player be taken? We have a prison system and a decision on
record about what prison does to the information landscape, and none of it is
wired to being caught in the act.

**Recommendation: yes to arrest, no to a chase.** A foot chase is a different
game and we would do it badly. Being taken — with the street watching, and
everything you were carrying now in a drawer at the station — is both cheaper
and more in keeping. But it is a real design decision and it belongs to Jafar.

### J. Phase 1's gate does not test Phase 1's promise

§3.3 promises the KCD2 feeling *before any weapon exists* — people noticing
you loiter, noticing you run at night, heads turning at a slammed door. **The
Phase 1 gate in §10 tests only detection ranges and occlusion**, which is the
machinery, not the experience. A green Phase 1 could therefore ship a city
that computes perfectly and reacts to nothing, and that failure mode is this
project's signature.

**Fix:** Phase 1's gate asserts a *behaviour* — loitering under a lamp for
thirty seconds produces at least one person who looks and one who comments —
and the reactions to non-crimes ship *in* Phase 1 rather than in Phase 2.

### K. Blood and cleanliness are half a sentence

Listed as new, used as a weapon-table column, never specified: how long it
lasts, what removes it, who notices it and at what light level, whether it is
rung-2 identification evidence, and what a coat in a bin does. It is one of
the cheapest good ideas here and it is currently a promise.

### L. The frisk is three sentences and it is the entire cost of carrying

Who can frisk, on what trigger, what a refusal costs, what happens when
something is found, and whether concealment is a property of the object, the
coat, or both. §7.2 asserts that this row matters more than reach and then
does not define it.

### M. Witness memory does not change with time, and real memory does

The mill ages *facts*. It does not model the thing that makes eyewitnesses
notorious: **accuracy falls while confidence rises**, and a hesitant
identification hardens into a certain one after a week of telling the story.
That is free drama, it is true, and it would make `Discredit` far more
interesting.

### N. No estimates, and no lab

Every other spec in this project costs its phases and gets a BalanceLab
scenario. This one, the largest, has neither. Phase 1 cannot be scheduled
against anything, and there is no `RunPerceptionLab` to answer whether the
tuning is sane — which is how `RunViolenceLab` caught mashing winning 76% of
fights.

### Summary

**All fourteen resolved in v4.** Both calls came back approved — symmetry
*"ok provided our characters/models and animations can handle that"*, and
arrest *"ok"*. The condition on symmetry is answered with a measurement rather
than an assurance in §15.1.

| | Finding | Resolved in |
|---|---|---|
| A | Ghost contradicts the dread | §6.2 — ghost restricted to mutual awareness only |
| B | Nothing is predictive | §15.1 — symmetry, with a silhouette gate and a named fallback |
| C | The victim is not modelled | §15.3 — the target perceives; the survivor is the worst witness |
| D | Accidents may dominate | §5.2 Family 6 — three constraints; risk 5; lab scenario |
| E | Two witness systems | §9 — `Violence.Saw` becomes an adapter, `KillingConfidence` derived |
| F | No numbers | §16 — vision, hearing and time tables |
| G | Performance undesigned | §17.1 — Near band only, 6Hz staggered, 1.2ms budget with a gate |
| H | Persistence unmentioned | §17.2 — schema per phase, not after |
| I | No acute police response | §15.2 — arrest, no chase |
| J | Phase 1 gate misses the point | §10 — a behaviour gate, and non-crime reactions ship in Phase 1 |
| K | Blood unspecified | §15.4 |
| L | The frisk unspecified | §15.5 |
| M | Memory does not change | §15.6 — accuracy falls, confidence rises |
| N | No estimates, no lab | §18 — ~16 days, and `RunPerceptionLab` |

---

## 15. THE RULES THAT WERE MISSING — resolutions to the audit

### 15.1 Symmetry — the planning rule. **APPROVED, with a condition**

> *"1. ok provided our characters/models and animations can handle that."*

Audit finding B: every device in v3 was reactive. Nothing let the player judge
a doorway *before* committing, and stealth-adjacent play is planning.

**The rule: if you can tell he is facing you, and you are in light, he can
see you.**

**Both halves, because the review pass caught the first version
over-promising.** *"If he is facing you, he can see you"* is false in the dark
— which is the condition most of this game happens in — because the vision
model multiplies every range by light level. So the rule is two readings the
player already has: **his facing**, off his silhouette, and **their own
exposure**, off the vignette (§6.2). Neither is new interface. The rule is
that those two things, together, are the whole answer — there is no hidden
third factor.

**And Jafar's condition is the whole problem, so it gets answered rather than
promised.**

**Correction, v5.** v4 said *"there are no faces in this game and there may
never be."* **That was wrong and Jafar corrected it:** Mixamo characters and
animations are a planned, funded-at-zero-cost dependency, and downloading them
is **his task, not mine.** They are a roadmap item (M16.0), not a hope. The
rule below is therefore designed to a **two-tier standard**:

- **Tier 1, today, on thirteen boxes.** The rule must work now, or Phase 1 is
  blocked on an asset drop and the whole *"ship perception on its own"* hedge
  collapses.
- **Tier 2, when the characters land.** Facing becomes trivially readable — a
  real head, a real neck, real shoulders, and turn-in-place animation. The
  same gate reruns and should pass by a much wider margin.

**The silhouette gate below is therefore also the acceptance test for the
Mixamo drop**, which is a better use of it than checking a box.

We still cannot render eyes at Tier 1, so the rule is stated against the one
thing that reads at distance in both tiers — **orientation** — and three
things make orientation legible rather than hoped for:

1. **Heads turn further and slower than they really would.** Standard
   animation exaggeration. A head at 40° of yaw reads in silhouette; a head at
   12° does not. The gaze system already turns heads; the values change, not
   the code.
2. **The head is the one part of the mannequin allowed a front.** A hat brim,
   a hair block, a collar — something whose silhouette differs front-to-back.
   Thirteen boxes cannot show a face and do not need to; they need an
   asymmetric head, which is one box.
3. **The body commits.** Someone genuinely looking at you turns their
   shoulders, not just their neck. Torso yaw is a much larger silhouette
   change than head yaw and it reads at twice the distance.

**The gate, because a condition without a measurement is an assurance.**
Render a walker at the ranges that matter — 8m, 18m, 35m — at the game's
darkest playable light, facing toward and facing away, and measure the
difference between the two silhouettes with `ImageStats`. **If front and back
are not measurably distinguishable at 18m, the rule cannot carry the design**
and we say so rather than shipping an unfair system.

**Tier 2 changes the numbers, not the design.** With real characters the head
has a face, the neck and shoulders separate, and Mixamo's turn-in-place clips
give the body a genuine commit rather than a slerp. Expect the 18m threshold
to become comfortable and 35m to become possible. **Nothing in the rule
changes** — which is the point of writing it against orientation rather than
against faces.

**The fallback if that gate fails at Tier 1**, and it is a real plan rather
than a shrug: the **survey verb** — stand still, hold a key, and attention sharpens
and sound directions resolve. It costs a moment of time, adds no HUD, and it
works at any fidelity because it is not asking the player to read a
silhouette. v3 listed it as an alternative; v4 makes it the designated
fallback, chosen by a measurement rather than by argument.

**What symmetry buys, and why it is worth the constraint.** It makes the
camera the planning tool with no interface at all: you look at the street, and
looking *is* the mechanic. It costs one line in `how-to-play.md`. And it binds
the camera and the vision model together permanently — if the vision cone and
what the camera shows ever disagree, the rule becomes a lie and the system
becomes unfair. That is the price, it is on record, and there is a gate for it
too: **the vision model and the rendered facing must be asserted equal**, not
independently maintained.

### 15.2 Caught in the act — **ARREST, NO CHASE. APPROVED**

Audit finding I: `Police` runs a ladder measured in days, and v3 added acts a
constable can watch happen and then said nothing about the next sixty seconds.

**Arrest.** A constable with a *Full* or *Actor* observation of you closes,
and being taken is the outcome. Not a health bar, not a fight — a hand on your
arm, the street watching, and everything that was in your coat now in a drawer
at the station.

**No chase**, and this is a refusal rather than an omission. A foot chase is a
different genre, it would be the least distinguished thing in the game, and it
would teach the player that violence is an action sequence. **Running is still
allowed and it still works** — but it works through the systems that already
exist: you get away because he did not identify you, because the street was
busy, because you had somewhere to be. Not because you outran him around a
corner.

**What arrest connects to, all of it already built:**

- Everything you were carrying is now catalogued. A knife is a conversation; a
  pistol is a different conversation.
- Provenance (§7.4) becomes the interrogation: *where did you get it.*
- The prison decision already on record in `decisions-pending.md` governs what
  it does to the information landscape.
- **You were seen being taken**, which is itself an event with witnesses. Half
  the street watched Tom Novak get walked to a car.

**Resisting is allowed, and it is the worst outcome in the game** (v5; Jafar:
*"resist arrest: ok"*). Not disallowed, not soft-failed — permitted, and
catastrophic. A fight with a constable in public is an unambiguous *Full*
observation for everybody on the street, with the one person present whose
word carries by default. It converts a survivable arrest into a manhunt, it is
the fastest route to the worst ending in the game, and **the game will not
warn you.** The prompt says the same thing it always says.

That is the correct shape for it: the option has to exist, because a game
where the law is unresistable is not a crime game — and it has to be a
mistake, because Tom Novak fighting a policeman is a man ending his own life
in ninety seconds.

**The escape hatch is social, not athletic:** a constable who cannot identify
you has nothing to arrest, which puts the whole weight back on §4.2's ladder
where it belongs.

### 15.3 The victim is a person who perceives — audit finding C

v3 was player → target → witnesses throughout. The target has senses too, and
**the most dangerous witness in this game is the man you failed to kill**:
close, lit, facing you, and with every reason in the world to talk.

- The target runs the same perception and observation model as anybody else,
  with one bias: **being attacked guarantees rung 3 and usually rung 4.** He
  was looking right at you.
- He can see it coming — which is what "against a ready, armed man" in §5.3
  actually means, and it is now a perception result rather than a table entry.
- He can run, and a fleeing target is a *delivering witness* (§4.5) who also
  happens to be the victim. That is the tensest chase in the design and it
  needs no chase mechanic — he is going somewhere and you know where.
- **He can survive.** `combat-spec.md` already models injury, healing, wounds
  turning bad, treatment and feuds; the survivor arrives fully built and has
  never been connected to anything.
- Treatment plants a second witness, which `HarmBook` already does: a doctor
  who can place a knife wound on a Tuesday.

This is the strongest argument in the document that killing costs more than it
saves, and v3 did not contain it.

### 15.4 Blood — audit finding K

Promised in three places, specified in none.

- **It appears** on the actor for edged, ligature-with-struggle and improvised
  weapons; never for firearms, the cosh, or an accident.
- **It is rung-2 evidence** — a distinguishing mark, exactly like the limp.
  Not proof of anything; a thing people can describe.
- **It is noticed by light and proximity**, through the same vision model.
  A stain reads at conversational distance under a lamp and not at all across
  a dark street. Nobody spots it at 20m at 3am, and everybody spots it in the
  bar.
- **It persists until you deal with it**, and dealing with it is the point:
  washing takes time and a place, changing needs a second coat you thought to
  bring (§5.2, Family 7), and getting rid of the old one is a disposal that can
  be witnessed like any other (§7.4).
- **Who sees it matters more than that it exists.** Blood noticed by a stranger
  is a rumour. Blood noticed by the woman you are seeing is a scene.

The KCD2 lesson holds: one violent minute should cost three in-game days, and
this is the cheapest possible way to buy that.

### 15.5 The frisk — audit finding L

§7.2 claimed the *carrying* row matters more than the *reach* row and then
gave the mechanism three sentences.

- **Who can:** a constable at any point once you are a person of interest;
  a doorman at a place that has one; one of the outfits, as a demonstration;
  Ellis, as a conversation rather than a search.
- **On what trigger:** never at random. It follows suspicion, a place with a
  rule, or someone deciding to make a point.
- **Refusing is an answer.** It is not a crime and it is not free — refusing a
  doorman means not going in, refusing a constable is itself something people
  saw you do.
- **Concealment belongs to the object AND the coat.** A switchblade is
  concealable in anything; a sawn-off is concealable in nothing; the coat
  moves everything one step. This is why Family 7 is not padding.
- **Found is worse than used.** A clean knife found on you the night after a
  stabbing on your street is not evidence of anything and will convict you
  socially anyway. That asymmetry is the whole reason the loadout decision at
  the door has teeth.

### 15.6 Memory hardens as it decays — audit finding M

The mill ages facts. It does not model the thing eyewitnesses are notorious
for: **accuracy falls while confidence rises.**

A hesitant *"I think it was a big man in a long coat"* becomes, after a week
of telling it, a certain *"it was Tom Novak."* The rung can climb without a
single new observation, purely from retelling and from what the teller already
believed (§4.6's familiarity bias).

- It is true, it is free drama, and it makes `Discredit` genuinely interesting
  — attacking a hardened memory is attacking someone's certainty rather than
  their honesty.
- It gives **time pressure in the other direction**: a witness left alone gets
  *more* dangerous, not less, which is a much better clock than decay alone.
- And it lets the player be destroyed by something that never happened, which
  §4.6 already argued the story wants.

**The interaction with `Rumor.Indelible`, resolved (v5, second-pass finding;
Jafar: "hardening: agree").** Homicide facts are indelible and `Discredit`
refuses them outright. If a *hardened false* memory inherited that, being
wrongly accused would become unanswerable, and §4.6's best idea would turn
into a punishment.

**The rule: hardening raises confidence; it never confers indelibility.**
Indelible is a property of *a body existing*, not of anybody's certainty. So a
false accusation can harden all the way to rung 4 and remain fully
discreditable — you are arguing with a person's confidence rather than with a
corpse. And the asymmetry stays intact in the direction that matters: a true
homicide rumour is still beyond every containment tool in the game.

---

## 16. CALIBRATION — the first numbers, audit finding F

v3 contained **no figures at all**, in a project whose standing lesson is
*check the ruler before the reading*. Without a table the implementation
invents everything and there is nothing to check it against.

**These are first guesses. Every one of them will move.** The point is that
each has a reason and a gate, so it moves *from* somewhere.

### 16.1 Vision

| Quantity | First value | Why |
|---|---|---|
| Full cone | 120° total | Human-ish; wide enough that hiding behind someone's shoulder is not trivial |
| Acuity band | inner 60° | Outside it, motion only — Blacklist's band model |
| Detection range, clear daylight | 40m | You can tell a person is there across a street and not much further |
| Rung 1, silhouette | ≤ 35m | Build and coat read almost as far as presence does |
| Rung 2, a mark | ≤ 18m | A limp is a gait, so it reads further than a scar |
| Rung 3, a face | ≤ 8m | Deliberately short. Faces are close-range |
| **Rung 4, recognition** | **≤ 25m** | **Further than a face**, because you know how a friend walks. The single most characteristic number in the table |
| Light multiplier | day 1.0 · under a lamp 0.7 · unlit street 0.25 · doorway 0.12 | Multiplies every range above. `LightModel` already returns this |
| Notice time | 0.35s in the acuity band | A glance is not a look |
| Identification time | 1.2s continuous | Recognition is slower than detection |
| Motion | running ×2.0 · walking ×1.0 · still ×0.5 | Stillness is a tactic |

### 16.2 Hearing

Loudness in dB-like units. **The audible radius is**

```
    r = 1.5m × 2^((L − A) / 8),  capped at 250m
    inaudible when L ≤ A
```

where `L` is the event's loudness and `A` is **the ambient floor at the
listener** — not at the source, which is what lets a shot inside a loud bar be
heard by the quiet street outside once occlusion has taken its cut.

| Ambient floor at the listener | Value |
|---|---|
| Residential street, 3am | 15 |
| Daytime street | 45 |
| Market at noon | 58 |
| The bar on a busy night | 68 |
| Heavy rain, outdoors | +12 to any of the above |

| Event | Loudness |
|---|---|
| Footstep, walking | 25 |
| Footstep, running | 38 |
| Door slam | 55 |
| Shout | 65 |
| Bottle smashing | 70 |
| Wire | — |
| Suppressed .22 | 62 |
| .38 snub | 100 |

**These numbers are the second draft, not the first.** The v4 review pass
caught the first set putting a walking footstep at 20 against a 3am floor of
25, which made footsteps *inaudible in a silent street* — flatly contradicting
§3.2's own example of the frightened man who hears a footstep behind him. The
corrected pair gives 3.6m, which is about right for a man who is listening.

Worked, so the table can be checked rather than trusted:

| Event | Where | Carries |
|---|---|---|
| Walking footstep | residential, 3am | **3.6m** — behind you, and only if he is listening |
| Walking footstep | daytime street | **nothing** |
| Suppressed .22 | the bar, busy | **nothing** |
| Suppressed .22 | residential, 3am | **86m** — the length of the street |
| .38 snub | daytime street | **177m** |
| Shout | market at noon | **2.2m** — which is why shouting in a market does not work |

**And this replaces the noise column in §5.2**, which described loudness in
absolute terms — *"one room"*, *"district"* — a habit left over from v2 that
contradicts the entire relative model. A suppressed pistol is not a
one-room weapon; it is a one-room weapon *in a bar* and an eighty-metre weapon
*at 3am*. The prose was wrong and the table is right.

Alert state multiplies the listener's effective floor downward by up to 8
units — the frightened man who hears a footstep.

### 16.3 Time

| Quantity | First value |
|---|---|
| Delivery walk, typical | 2–9 minutes, real routes, real speeds |
| Frightened witness | runs, and picks the nearest destination |
| Unsure witness | sits with it 20–90 minutes first |
| Body discovery, alley at 3am | hours |
| Body discovery, market at noon | under a minute |
| Standoff beat (§6.2) | 0.4s duck, once per event |
| Memory hardening (§15.6) | rung +1 per ~4 retellings, confidence +0.1 per retelling |

---

## 17. PERFORMANCE AND PERSISTENCE — audit findings G and H

### 17.1 Performance, designed rather than acknowledged

v3 said *"throttled by distance"* three times and never mentioned the
Near / Mid / Far band model this project already has.

- **Only the Near band perceives.** Mid-band residents carry and pass talk
  without bodies, which is tested and works; giving three thousand people
  vision cones would cost the frame and buy nothing the mill does not already
  produce. This is assumption 1 in §13, made concrete.
- **Vision recomputes at ~6Hz, staggered**, not every frame for everyone. A
  head turning a sixth of a second late is invisible; sixty cone tests a frame
  is not.
- **Hearing is event-driven and therefore nearly free.** Sounds are rare;
  there is no per-frame cost at all, just a radius test against the Near band
  when something happens.
- **Occlusion is the expensive part**, so it is the last test rather than the
  first: cone, then range, then light, then — only if all three pass — a ray.
- **Budget: 1.2ms per frame for all perception at 60fps**, with a gate that
  fails the build when the sim exceeds it. A number nobody has measured on
  real hardware, which is exactly why it needs a gate rather than a hope.

### 17.2 Persistence, which v3 never mentioned once

New durable state, and the obvious case — **saving while a witness is halfway
through a delivery walk** — had no answer:

| State | Persisted as |
|---|---|
| Observation records | Slot set, rungs, certainty, willingness, per witness per event |
| In-flight deliveries | Destination, progress, and the deadline they are walking toward |
| Mutual-awareness pairs | Both halves, because the ghost depends on it |
| Carried objects | What is on you, what is at home |
| Provenance | Per weapon instance, permanently |
| Blood and cleanliness | With the timestamp it was acquired |
| Alert states | Per person, decaying |

The machinery exists — atomic writes, backups, slots, all built and tested.
This is schema work, and it goes in **with** each phase rather than after it,
because a save format retrofitted is a save format broken.

---

## 18. COST AND THE LAB — audit finding N

Every other spec in this project costs its phases and gets a lab scenario.
The largest one had neither.

| Phase | Core | Unity / wiring | Total |
|---|---|---|---|
| 1 — perception + non-crime reactions | ~2 days | ~1 day | **~3 days** |
| 1b — legibility | ~0.5 day | ~1 day | **~1.5 days** |
| 2 — observation, reaction, the ghost | ~2.5 days | ~1 day | **~3.5 days** |
| 3 — melee, carry, blood, the frisk | ~2 days | ~1.5 days | **~3.5 days** |
| 4 — the murder weapon, acquisition, accidents | ~2 days | ~1 day | **~3 days** |
| 5 — firearms | ~1 day | ~0.5 day | **~1.5 days** |

**~16 days of build**, and the estimate is honest about being the largest
single feature in the project. Phase 1 and 1b are the hedge and they are four
and a half of those days.

**`RunPerceptionLab`**, in BalanceLab, answering the questions no unit test
can:

- Across a hundred randomised events, **what is the distribution of slot
  sets**? If 80% are *Full*, the perception model is too generous and the
  partial-witness design does nothing.
- **How often does the optimal player reach for an accident?** If it is most
  of the time, §5.2's three constraints are not enough (risk 5).
- **How often does brandishing end it?** Same question, risk 4.
- **What does a week look like after one killing**, by weapon — witnesses,
  deliveries intercepted, police ladder reached, quiet endings still available.
  `RunViolenceLab` already produces exactly this shape of table.
- **Does the survivor dominate?** If failing to kill is always worse than
  never trying, §15.3 has been tuned into a trap rather than a choice.

---

*Sources consulted for v2.1 and v2.2, beyond those cited inline in v2:*
[Splinter Cell Stealth Meter](https://splintercell.fandom.com/wiki/Stealth_Meter) ·
[Splinter Cell stealth / Conviction](https://splintercell.fandom.com/wiki/Stealth) ·
[Conviction](https://en.wikipedia.org/wiki/Tom_Clancy%27s_Splinter_Cell:_Conviction) ·
[Modern lighting vs stealth readability](https://www.gamedeveloper.com/design/splinter-cell-designer-says-modern-lighting-have-made-stealth-games-harder-to-read) ·
[RDR2 Eyewitness](https://reddead.fandom.com/wiki/Eyewitness) ·
[RDR2 Wanted System](https://www.rdr2.org/wiki/wanted-system/) ·
[GamesRadar RDR2 bounty](https://www.gamesradar.com/red-dead-redemption-2-bounty-and-wanted-level/) ·
[Hitman Enforcers](https://hitman.fandom.com/wiki/Enforcers) ·
[Shadows of Doubt devblog](https://colepowered.com/shadows-of-doubt-devblog-10-gameplay-loop/) ·
[Shadows of Doubt investigation guide](https://hackernoon.com/shadows-of-doubt-a-guide-to-investigating-crime-scenes-and-solving-murder-cases) ·
[Shadows of Doubt fingerprints](https://dotesports.com/indies/news/shadows-of-doubt-fingerprint-database-how-to-solve-murder-cases) ·
[Dishonored chaos](https://www.cbr.com/dishonored-chaos-mechanic-ludonarrative-dissonance-arkane/) ·
[MGSV Reflex Mode](https://metalgear.fandom.com/wiki/Reflex_Mode) ·
[MGSV CQC](https://www.metalgearinformer.com/?p=8749) ·
[Sifu combat design](https://www.unrealengine.com/en-US/developer-interviews/old-boy-john-wick-sifu-the-design-of-a-pak-mei-master) ·
[KCD2 speech checks / bloodied gear](https://gamerant.com/kingdom-come-deliverance-2-kcd2-how-pass-speech-checks-intimidation-persuasion-coercion-dialogue/) ·
[KCD2 crimes](https://patchcrazy.co.uk/crimes-guide-in-kingdom-come-deliverance-2/) ·
[KCD cleanliness](https://kingdom-come-deliverance.fandom.com/wiki/Cleanliness) ·
[AC and social stealth](https://www.gamedeveloper.com/design/why-assassin-s-creed-series-isn-t-social-stealth-and-what-to-do-about-that-) ·
[Revival of social stealth](https://www.gamesradar.com/inside-the-revival-of-social-stealth-games/) ·
[Hitman staged accidents](https://hitman.fandom.com/wiki/Staged_Accident) ·
[Hitman weapons](https://hitman.fandom.com/wiki/Weapons_(Feature)) ·
[Mafia II weapons](https://mafiagame.fandom.com/wiki/Weapons_in_Mafia_II) ·
[Mafia II on IMFDB](https://www.imfdb.org/wiki/Mafia_II) ·
[Guns of the Mob](https://gunmagwarehouse.com/blog/guns-of-the-mob-the-most-popular-firearms-used-by-the-mafia/) ·
[Top weapons used by the mob](https://nationalcrimesyndicate.com/top-5-weapons-used-mob/) ·
[Ice pick](https://deadliestwarrior.fandom.com/wiki/Ice_Pick)
