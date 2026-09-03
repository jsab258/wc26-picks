# Combat — spec and plan

> **STATUS: SPEC.** The design for combat, phases 1-3b. Stable reference:
> build state lives in `roadmap.md`, not here. A spec that disagrees
> with the roadmap is out of date about what got built, not about what
> was intended.

**Status: PHASES 1, 2 AND 3b BUILT, 2026-07-28.** Requested by Jafar:
*"update combat on the roadmap. needs to be properly specced and planned.
UI/UX needs to be high quality."*

Built: `Core/Combat.cs` (the verbs, footing, stamina, reach),
`Core/Combat.cs`'s `Violence` (who saw it), and `Core/Homicide.cs` (the
body, the police, the crew who watched). Remaining: phase 3 (animation,
telegraphs, hit reactions) which is blocked on characters, and phase 4
(BalanceLab tuning) which follows it.

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

**Phase 3b — The body. BUILT.** `Core/Homicide.cs`, and the guards it
needed inside the gossip mill.

The design problem was never "how does killing work" — it was making the
trade in §2 true *as arithmetic* rather than as an assertion in this
document. Killing has to genuinely work or the choice is fake, and it has
to cost more than it saves or the gossip game is dead. Both, at once.

`HomicideBook.Pressure` is where that lands. Bodies weigh 0.4 each; the
strongest living witness who can name you weighs up to 0.6; every witness
after the first adds 0.25. Read the table it produces:

| Situation | Pressure | Police |
|---|---|---|
| One body, nobody saw | 0.40 | Procedure |
| One body, one witness through a wall | 0.76 | Investigation |
| One body, one witness who watched | 1.00 | **Manhunt** |
| Two bodies, nobody left alive to talk | 0.80 | Investigation |
| Three bodies, nobody left | 1.20 | **Manhunt** |

Lines three and four are the whole feature. Killing the only witness to
your killing **really does** take the manhunt off you — it has to, or the
player stops believing the system inside one attempt. It takes you to an
investigation. It never takes you back to procedure, and it never takes
you back to nothing. Do it once more and you are measurably past where the
first body left you.

**The asymmetry, enforced one machine at a time.** A `Rumor.Indelible`
flag, and every containment tool in the game steps over it: `Age` does not
cool it, `Discredit` refuses outright (and does not burn the once-per-story
denial on the way past), `Bribe` and `Intimidate` are refused with their
own outcome rather than a lie about the story having died down, a leash and
a suppression do not stop it spreading, and it crosses every mouth on the
street without losing a point of confidence. Fifty-four days of lying low
does nothing to it. It also survives `StrongestSurvivingPlayerLead`, so no
amount of managing the information landscape makes Ellis's case answerable
once there is a body.

**Ellis.** A body is how a detective gets assigned, so from Procedure up she
is on the street whatever the talk is doing and the heat threshold stops
mattering — and there is no calm-down path any more. Investigation forces
Act III open, because the audit clock is a paperwork clock and this is not.
Manhunt takes the Quiet ending off the table outright: a successor can
inherit a licence, never a homicide.

**The crew who watched** get a permanent loyalty *ceiling* rather than a
loyalty hit — paying them well never lifts it back off — and the one who
goes to the police is the frightened one, not the disloyal one.

39 checks; 16 deliberate breaks confirmed red first.

**Phase 4 — Tuning against the fiction. THE HALF THAT NEEDS NO ART IS RUN.**

What decides whether violence is the efficient path is not the animation —
it is the arithmetic in `Combat`, `Homicide` and the gossip mill, and all
three exist. So `BalanceLab`'s `RunViolenceLab` runs it now: three people
saw the player do something they should not have, four ways to answer it,
a real spread of dispositions, then a week of the street doing what the
street does.

```
answer            lead police          $cost  quiet? bodies
leave-it          0.28 None                0    100%    0.0
bribe             0.18 None              414    100%    0.0
intimidate        0.23 None                0    100%    0.0
kill-one          0.91 Manhunt             0     13%    1.0
kill-all          1.00 Manhunt             0      0%    3.0
```

`lead` is the strongest surviving story a magistrate could be handed;
below 0.50 the case is answerable. **The design holds.** Killing is not
merely no better than paying — it is three to five times worse on the only
metric that decides the ending, and it takes the quiet exit off the table
in 87% of runs at one body and 100% at three. Money buys the best outcome
and costs money; lying low genuinely works, which is the "let it cool"
option working as designed.

The 13% at one body is not noise: it is the fraction of runs where nobody
was in the alley. **Kill somebody with no witnesses and you can still get
away with it.** That is the design too — it is what makes choosing the
alley at three in the morning a real decision rather than a flavour of the
same outcome.

### The exchange itself — RUN 2026-07-28, and it found a real defect

The violence lab answers the strategic question. This answers the
moment-to-moment one, and §2 names the failure to hunt: *"if the player
feels GOOD at fighting, the fiction and the systems both break."*

**First run, at the original constants:**

```
policy        win%  down%  hurt  blows  gassed%
mash           76%    24%  0.63    1.8       0%
```

Mashing Strike won three exchanges in four AND took the least punishment
doing it. The cause was not the balance of the verbs — it was that **a
clean strike did 0.86 against a floor of 1.0, so a fight was over in two
blows.** Stamina fell from 1.00 to 0.88 across an entire fight. Guard,
footing and stamina never got a turn: every mechanic in `Combat.cs`
except Strike was decoration.

Every unit test passed throughout. They were all true, and the system was
still hollow — which is the difference between checking rules and
checking balance.

**Retuned:** floor 1.0 → 2.8, strike cost 0.22 → 0.34, recovery 0.18 →
0.09, guard absorption 0.35 → 0.22.

```
policy        win%  down%  hurt  blows  gassed%
mash           15%    67%  2.52    8.9     100%
guard-then-hit    0%     3%  2.05   11.0     100%
patient        26%    46%  2.39    9.6       0%
shove-and-go    0%     0%  0.00    2.0       0%
back-off        0%     0%  0.00    0.0       0%
```

- **Mashing gasses out every time and puts Tom on the ground two thirds
  of the time.** The stamina mechanic finally reaches the fight.
- **Patience beats it** — more wins, fewer knockdowns, never gassed. A
  player who learns the system is rewarded, which is not the same as
  being made good at fighting.
- **Even the best line wins a quarter of the time and takes 2.39
  punishment** — most of a knockdown. Winning costs.
- **Guard-then-hit does not lose, it runs out of clock**: 2.32 damage
  against a floor of 2.8 across forty exchanges. Two men who cannot
  fight, flailing until they stop. That is better fiction than a win.
- **Backing off and shoving-then-leaving take nothing at all**, which is
  §3 saying the de-escalation tools should be the best option and the
  game should say so.

The lab also had to be corrected: its first version did not model a shove
creating distance, so it scored the de-escalation tool as "stand still
and get hit twice". The table said the best verb was the worst line, and
it was the LAB that was wrong.

Guards against the inert-system defect now live in CoreTests — a fight
must take three swings, the swinger must be spent by the end, and a guard
must save most of a blow — so the hollow version cannot come back
silently.

What is still blocked: the feel of it. Whether a swing READS is a phase 3
question and needs bodies. *~1 day once they land.*

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
