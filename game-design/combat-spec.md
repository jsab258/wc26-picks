# Combat — spec and plan

**Status: SPEC, 2026-07-28.** Requested by Jafar: *"update combat on the
roadmap. needs to be properly specced and planned. UI/UX needs to be high
quality."* Nothing here is built. The consequence layer it stands on is.

---

## 0. Why this is not a normal combat spec

Combat was **deferred by Jafar**, and the reasoning is on record in
`Core/Harm.cs`: positioning-and-timing combat cannot be judged on capsules
and needs the art pass. That was right, and it produced something unusual —
**the aftermath of violence was built before the violence.** Injuries
persist and heal on a schedule, untreated wounds turn bad, treatment costs
money AND plants a witness who can place you somewhere on a Tuesday, feuds
run between named people, scars are permanent, and lost capability now shows
in the walk.

So we are not adding combat to a game. We are adding **the last missing verb
to a consequence system that has been waiting for it.**

That inverts the usual design order and it is the best thing about our
position. Most games build the punch and bolt consequences on afterwards,
which is why the consequences are always thin. Ours are already thick.

## 1. THE FILTER, from `agency-model.md`

> *Every non-social system exists to give the social system stakes. Money
> buys silence. **Violence is seen.***

That one clause decides the entire design. In LEDGER the antagonist is
gossip. A fight is therefore **the loudest possible event in the game** —
not because of damage, but because of witnesses.

Everything below follows from it.

## 2. What combat must NOT be

Stated first, because the failure modes here are more dangerous than the
opportunities.

- **NOT a win condition.** You cannot punch your way to owning the street.
  The moment violence is the efficient solution, the gossip game is dead and
  we have made a worse brawler. **Note the tension with the lethality answer,
  because it is real:** killing a witness genuinely does solve that
  witness. The resolution is not to make it fail — it is that the SECOND
  problem is always larger than the first. Violence has to work and cost more
  than it saves, which is a harder thing to balance than violence that simply
  does not work.
- **NOT empowering.** Tom Novak runs a bar. He is not a fighter, and the
  moment-to-moment should feel dangerous and slightly out of control. If the
  player feels *good* at fighting, the fiction and the systems both break.
- **NOT frequent.** If it happens every session it becomes the game. Target:
  a handful of fights in a full playthrough, each one memorable and each one
  a mistake or a last resort.
- **NOT free.** Every swing has a cost even when you win: witnesses, an
  injury that lasts days, money spent on treatment that itself becomes
  evidence, and a feud that outlives the fight.
- **NOT a separate mode.** No arena, no lock-on state you enter and exit, no
  music sting that announces "combat now". It happens on the street, in the
  middle of everything else, and it ends the way real fights end — abruptly
  and awkwardly.

## 3. THE VERBS

Deliberately few. A small verb set that each mean something beats a large
one where the player mashes.

| Verb | What it is | Cost |
|---|---|---|
| **Square up** | Not an attack. A stance change, visible to everyone, that says this is about to happen | Witnesses start paying attention BEFORE anything lands |
| **Strike** | One committed swing. Slow, telegraphed, heavy | Leaves you open; misses hurt you more than them |
| **Shove** | Create distance, break a grab, knock someone off a doorway | Cheap, non-injuring, and the de-escalation tool |
| **Guard** | Absorb rather than avoid. Reduces harm, does not remove it | Cannot guard forever; a held guard becomes a grab |
| **Back off** | Leave. Explicitly a verb, explicitly viable | The best option in most fights, and the game should say so |

A sixth verb follows from the lethality answer and is deliberately NOT in
the table above, because it is not a combat move: **finishing** somebody who
is already down. Separated on purpose — it should never be something that
happens in the flow of a scuffle, it should be a decision made in the quiet
afterwards, with the person on the ground and the street watching. That is
the beat the whole game is built to make heavy.

**Guns are out of scope for this spec.** The agency model staged violence as
melee-then-guns; melee has to prove it earns its place first, and a gun in
this game changes the fiction from *a man in trouble* to *a man with a gun*.
Revisit only after melee has shipped and been played.

## 4. UI/UX — and this is the part that has to be right

Jafar: *"UI/UX needs to be high quality."* Concretely, that means it should
be **almost entirely absent**, because this is the same principle M15 was
built on: the simulation IS the interface.

### No health bar. No damage numbers. No hit markers.

We already have the machinery to do without them, and every one of these is
a system announcing itself:

- **Your condition is written on your body.** The limp already exists and is
  driven by real capability. Add breathing that gets ragged, a guard that
  drops as you tire, a camera that drifts and settles harder. A player who
  has to check a bar is a player who has stopped looking at the fight.
- **Their condition is written on theirs.** Stance, guard height, how they
  hold the injured side. `HarmBook.LooksLike` already returns exactly this
  and nothing has ever displayed it.
- **Threat is read from the world.** The gaze and stance systems already
  compute who is watching you and how they feel. Somebody who is about to
  swing has been staring for three seconds.

### What the interface DOES do

- **Contextual prompt, fading, forgiving, buffered.** All three already
  built. The prompt for "square up" appears the way the talk prompt does.
- **Telegraph, not tell.** Every incoming strike has a readable wind-up. The
  `VerbBeat` clock is exactly this shape — anticipation, action,
  consequence, recovery — and it already exists and is tested.
- **Sound carries most of it.** Breath, the scuff of a foot, the crowd
  reacting. `Acoustics` and the foley layer are already there.
- **One deliberate exception: the audience.** After a fight the player needs
  to understand what it COST, and that is not visible. That is the one place
  a piece of interface earns its keep — and it should be Mickey's book or a
  line of dialogue, not a toast. Held for M15.3, which is the same problem.

### Accessibility, stated up front rather than retrofitted

Timing-based combat excludes people. Options for a longer telegraph window,
and an auto-resolve for players who want the story and not the fight. Neither
is a difficulty setting — both are the same fight at a different tempo.

## 5. What already exists to build on

This is why the estimate below is small.

| Have | Used for |
|---|---|
| `VerbBeat` | Anticipation/action/consequence/recovery — the exact shape of a swing |
| `HarmBook` | Injuries, healing, wounds turning bad, treatment, feuds, scars |
| `Gait` / limp | Condition written on the body, already driven by capability |
| `Bumps` | Contact classification and stagger, already tested |
| `GossipMill` + `Acoustics` | Who saw it, how well, and how sure they are |
| `StreetVoice` stance ladder | Who is hostile enough to start one |
| Camera rig, momentum | Weight and readability |

**Genuinely new: four verbs, an enemy AI that can telegraph and react, and
the animation to read it.** That last one is why this waits for characters.

## 6. THE PLAN

**Gated on characters landing.** Not on principle — a swing on a capsule
cannot be read, and an unreadable telegraph makes a timing system into a
coin flip.

**Phase 1 — Core, and it can start now.** `Combat.cs`: the verb set as
tested state machines on `VerbBeat`, reach and timing windows, guard
absorption, the stagger model, and the rule that connects a landed strike to
`HarmBook`. Engine-free, testable, no art needed. *~1 day.*

**Phase 2 — The witness rules.** A fight is an event the mill can carry.
Who saw it, from how far, through what — `Acoustics.OverheardConfidence`
already answers this for speech and the same shape works for a scuffle.
Fighting in an alley at night is genuinely different from fighting outside
the bar at noon, and that difference IS the game. *~half a day.*

**Phase 3 — Bodies and telegraphs.** Animation, the read, hit reactions,
the guard. **Blocked on characters.** *~2 days.*

**Phase 3b — The body.** A killing as a permanent, undiscreditable fact in
the mill; police escalation on Mara Ellis; crew who saw it. **This is the
largest genuinely new piece of work in the spec** and it is a consequence of
the lethality answer, not of the fighting. *~2 days.*

**Phase 4 — Tuning against the fiction.** Make sure violence is never the
efficient path. This is a BalanceLab job, not a feel job: if a Monte Carlo
run says fighting wins, the design is wrong regardless of how it plays.
*~1 day.*

## 7. DECISIONS — ANSWERED by Jafar, 2026-07-28

| Question | Answer |
|---|---|
| On-screen readout | **Diegetic + heavy feedback now**, *"might need minimal hud later on"* |
| Who swings first | **Both.** *"should also be possible to kill witnesses for example. consequences, yes (cops?) but violence is a part of our crime world and a legit tool"* |
| Lethality | **Yes, rarely and permanently** |
| Guns | **Out of scope for now** |

### 7a. THE LETHALITY ANSWER IS BETTER THAN MY RECOMMENDATION, and I want to
### say why rather than just comply

I argued for no deaths on the grounds that one would dominate the gossip
system so completely that nothing else would matter. That was protecting the
simulation from a shock it should be built to absorb.

**In a game whose antagonist is gossip, killing a witness is the most
on-theme violent act available.** It WORKS — the rumour stops, the person
who saw you cannot tell anyone — and it creates a far worse problem than the
one it solved. That is precisely the trade this entire game is about, and it
is a better version of the design than the one I proposed.

So the concern does not disappear; it becomes the specification.

### 7b. WHAT A BODY DOES, which is now the most important part of this spec

A killing is not damage. It is a permanent change of game state, and it must
be modelled as one:

- **A body is a fact that cannot be discredited.** Every other rumour in this
  game can be muddied, contradicted, suppressed or left to decay. The
  discredit mechanics, the leashes, the confidence decay — none of them touch
  a corpse. This is the one input the gossip mill must treat as absolute, and
  that asymmetry is what makes it terrifying rather than efficient.
- **It solves the immediate problem completely.** Whoever saw you is gone.
  The design must be honest about this or the choice is fake — if killing a
  witness does not actually stop the rumour, the player will notice
  immediately and stop believing the whole system.
- **It brings police, which is a new pressure track.** Mara Ellis already
  exists as an inspector who never threatens. A killing escalates her from
  procedure to investigation, and she is the one character in the game
  equipped to carry that. *This is genuinely new work and I am not going to
  pretend otherwise.*
- **Who ELSE saw.** Acoustics and the gossip mill already answer "who was in
  earshot" precisely. Killing one witness where three were present is the
  mechanism by which this spirals, and it needs no new system at all.
- **The crew know.** A recruit who watched you do it carries it, and loyalty
  is already modelled. Nobody who saw it is ever quite the same about you.
- **Rare and permanent.** No undo, no forgiveness track, and it should be
  possible to complete a whole playthrough having never done it.

### 7c. Consequences for the UI answer

Diegetic-plus-heavy-feedback now, and **architected so a minimal HUD is a
settings toggle rather than a rewrite.** That means the readout values —
stamina, threat, incoming telegraph — exist as data from day one regardless
of whether anything draws them. Building "no HUD" as an absence would make
adding one later a retrofit; building it as a renderer that is currently
switched off makes it a Tuesday.

### 7d. Still mine to decide, and I am deciding it

**Auto-resolve for accessibility: yes.** Timing-based combat excludes people,
and this is the same fight at a different tempo rather than a difficulty
setting.

## 8. The risk worth naming

**Combat is the single easiest way to ruin this game.** It is the most
familiar verb in the medium, it attracts effort, and it will pull the whole
design toward being about itself. Every hour spent on it is an hour not
spent on gossip, and the moment it becomes fun in its own right it competes
with the thing the game is actually about.

The honest position: this is worth building *because the consequence layer
already exists and is going unused* — not because the game needs fighting.
If Phase 1 and 2 land and it still feels like a distraction, the correct
decision is to stop there and leave violence as something that happens TO
you.
