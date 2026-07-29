# PERCEPTION, WEAPONS AND VIOLENCE — spec v3, APPROVED

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
- **v3 (this) — APPROVED IN FULL.** No content change from v2.2; the status
  and §12 are rewritten as a record of what was approved rather than a list of
  asks, and §13 states the two assumptions I am proceeding on and the two
  things from Jafar that would make the work materially better.

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

**What they think they know — the ghost, and this is the idea I would defend
hardest in the whole document.**

Conviction leaves a silhouette where the enemy believes you are. Ours leaves
**a silhouette of what the witness believes, drawn from the actual belief
record** — and because our witnesses hold slots and rungs rather than a
position, the ghost can show *the shape of their misunderstanding*:

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
- `Violence.Saw`, `KillingConfidence`, `Notoriety`, `HomicideBook`, `Police`.
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
**Ship this and play it even if weapons never follow.** Sim gate: a walker in
light is detected at greater range than one in shadow; a sound behind a wall
is not heard; a sound under the ambient floor is not heard.

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
5. **Scope.** This is the largest single proposal in the project. Phase 1 is
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
