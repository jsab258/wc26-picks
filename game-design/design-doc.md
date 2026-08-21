# LEDGER — Design Document

> **STATUS — LIVE, verified 2026-08-18, reference.** The founding document: what the
> game is, what it is made of, and what is not built yet. If it is wrong, that is a bug
> in this file. `roadmap.md` owns the plan and wins on any question of what happens next.

**LEDGER** — your two lives are two accounts, and you are always balancing them.

Open-city crime sim × slice-of-life social RPG. Single-player, premium, PC first.
Unity 6, C#. A British port town called Meridian, **late-analog**: landlines, payphones,
answering machines, messages left with people. No internet, no mobiles.

---

## 1. What the game is

> **LEDGER is a crime game in a city that perceives, reacts and remembers.**
>
> Violence, weapons and the physical business of committing crimes are core pillars.
> What distinguishes them from the same verbs in other crime games is that every act is
> perceived PARTIALLY, by people with real sight and hearing, who then behave
> differently, tell each other, and remember.

Neither half survives alone. A crime game with a thin reaction layer is something this
project cannot out-produce. A reaction layer with nothing to react to is a chat
simulator. **The value is entirely in the join**, and every argument in this document
should be tested against that sentence rather than against either half of it.

### The premise

You are **Tom Novak**, and you arrive alone in Meridian with one suitcase and a letter.
Mickey, your mother's brother, has died and left you his pub. The pub is real. So is
what came with it: a half-dead criminal outfit, two ageing loyalists, a book of
uncollectable debts, and a territory the town's three established organisations have
already begun to carve up.

By day you build a life — a job, a room, friendships, maybe love. By night you rebuild
the family business. Every person in the town is a character with a schedule, a
personality, and a persistent memory of everything you have said and done. They talk to
each other. Word spreads. The game is keeping your two lives apart in a town that never
stops comparing notes.

Breaking Bad as a systemic game: the drama is not scripted, it leaks.

### The quality target

A high-quality indie game. The bar is Disco Elysium, Papers Please, Rimworld, Shadows
of Doubt: reviews well, sells, gets covered. Explicitly not chasing AAA breadth — the
realistic ceiling is AA / premium indie (Kingdom Come 1, Hunt: Showdown, Mount &
Blade), and the winning position is *the game that does one thing no AAA studio can
currently do, at a polish level that reads as excellent*.

The comparison that governs scope is KCD2: unmistakably deeper in social memory,
consequence and information. **The visual bar changed 21 Aug 2026, by Jafar's
direct order: match GTA V (PS3, 2013).** The old "worse-looking, at peace with
that trade" framing is retired — depth stays the moat, but the street has to
hold up next to a thirteen-year-old console game, on Meridian's own content.
Plan in `roadmap.md` M17.10; decomposition in `visual-bar-spec.md`.

---

## 2. The claims

Stated explicitly so that every design decision can be tested against them. **A feature
that serves none of these is cut.**

1. **Acts are perceived partially, by people.** Every crime game asks whether a witness
   saw you. This one asks which parts they got, and whether they can put a name to it.
   Seven perceivable slots, a five-rung identification ladder, and the top rung is
   *recognition* — which needs a relationship, not a distance. At twenty metres in the
   rain a stranger sees a shape and **your neighbour sees you.** That inverts the
   tactics: the dangerous witness is not the closest one, it is the one who knows you.
   Measured in the perception lab: partial observation is 95% of outcomes, and
   darkness cuts naming by 4.6×.

2. **NPCs genuinely remember, forever.** Real conversations, model-driven and voiced,
   with persistent per-character memory. Not a dialogue tree in disguise.

3. **The double life is mechanical, not cinematic.** Cover stories only matter if NPCs
   can compare notes, and these can: information propagates person-to-person through
   schedule intersections. Your partner can catch your alibi from your coworker. No
   scripted game can do this.

4. **Secrets are loot.** What you know about people — and what they know about you — is
   the primary currency and the progression system. CK3 hooks crossed with Outer Wilds
   knowledge-progression.

5. **A living town at honest scale.** Any resident can be promoted by attention into a
   full character. Almost none are simulated at any moment, and the design is honest
   about that (§7.2). The whole town persists as a seed plus its exceptions.

6. **Betrayal is emergent.** Your organisation is made of individuals with loyalty,
   fear and grievances. Betrayal is never a cutscene; it is caused, and it is
   preventable.

---

## 3. Pillars

- **P1 — Two lives, one clock.** Time is the resource the two lives fight over. Every
  hour spent on one is an hour not spent protecting the other.
- **P2 — Information is physical.** Facts exist in NPC memories, move between people,
  decay into rumour, and can be bought, planted or silenced.
- **P3 — People, not units.** Every recruit, rival, lover and witness is an individual
  whose relationship to you is personal history, not a meter.
- **P4 — Authored anchors, simulated bones, model as director and interface.** What
  stays authored is *anchors*: the acts' hard turns, the Tier-1 cast, the rules of the
  world. What stays simulated is the *bones*: money, time, information, standing. Every
  outcome the player feels is decided in deterministic C#. The model is the
  **interface** (the player says anything and it is routed into real mechanics) and the
  **director** (nightly world-level authoring read off actual state) — never the
  referee. It classifies and performs; it does not adjudicate. Full argument in §11.
- **P5 — Consequences persist.** No quest resets, no memory wipes. The town's state is
  the save file.

---

## 4. The perception chain

The design has one spine, and it runs in this order:

    PERCEPTION → OBSERVATION → REACTION → MEMORY & TALK

Every system in §7 sits at one of those stages, and the ordering is the point: talk is
the *fourth* stage, not the foundation. A rumour is only worth simulating because
somebody imperfectly saw something first.

**Partial observation is a generator, not a list.** An act exposes seven perceivable
slots — what happened, who did it, what they looked like, what they carried, where,
when, and which way they went — and a witness may get any subset. Identification runs
on a separate five-rung ladder, from *somebody was there* to *that was Tom Novak*, and
the top rung is **recognition**: the same distance and the same light identify you to
your neighbour and not to a stranger. That requires an acquaintance graph with real
familiarity in it, which is why no other crime game is in a position to build it.

**Believing something and being willing to say it are different values.** A witness who
is certain and frightened is not a witness who talks.

**A witness is a deadline.** Somebody who saw you is a person walking somewhere to tell
someone, and they are interceptable until they arrive.

**Light and sound are already computed and must be read.** The lighting model knows the
light level everywhere at every hour. Whether a man is standing under a lamp or in a
doorway decides what he can see, and perception is what makes the art and audio work
load-bearing rather than decorative.

The reference point for reactivity is KCD2: NPCs who react to what you do, including
things that are not crimes.

---

## 5. Loops

### Inner loop — the encounter (minutes)

Talk, observe, act. A conversation that yields a secret; a delivery that builds trust;
a lie that plants a false memory. Every encounter writes to somebody's memory.

### Middle loop — the day (a session)

A Persona-style calendar: morning, afternoon, evening, night. Obligations — shifts,
dates, collections, meets — compete for slots. End of day is a natural save and stop
point with a ledger summary: money moved, secrets gained, rumours spreading, loyalty
shifts. The two lives cross-feed: at work you plan the night, at night you worry about
tomorrow's lunch with her parents.

### The two modes

**Week mode (days 1–7)** is Act I's on-ramp: survive the week, learn every system under
real stakes, answer Lena's question on day seven.

**Open mode (day 8 on)** is the game: no verdict, no countdown, no win condition.
Losing remains possible but **scars rather than ends** — exposure means the Fall: days
inside, unwashed cash seized, every rumour about you collapsing into public fact, and
you start again from there. An ending screen would contradict P5.

### Outer loop — the two ledgers (a campaign)

Grow the empire (territory, rackets, crew) while growing the life (relationships,
standing, comfort). The town squeezes both: rivals move on your territory, loved ones
ask harder questions. Acts advance when the authored spine's pressure points fire (§9).

### Session hooks

"One more day" comes from three places: an unresolved thread every evening — the
simulation guarantees one, a rumour in flight, a recruit wavering, a date promised; the
end-of-day ledger dangling tomorrow's opportunity; and rising stakes, because the
bigger both lives grow the more each day can win or lose.

**No hard timers.** Nothing in the game expires on a countdown. Pressure comes from
escalation and consequence — rivals react to what you do, not to a clock. The player
sets the pace; the world raises the stakes. No dailies, no FOMO, no dark patterns.
Retention through curiosity and stakes.

---

## 6. The cast

Three tiers, which is the Watch Dogs Legion lesson taken seriously: procedural people
are worthless unless some of them can become real.

- **Tier 1 — authored core (~14).** Handwritten cards, arcs and voices.
- **Tier 2 — generated middle ring (~150–300).** Full character cards — personality,
  history, job, home, schedule, connections, one secret, one need — generated in batch
  and hand-touched. Each has mechanical individuality: a unique skill, access or
  connection (the customs clerk, the pharmacist with debts, the constable's ex-wife)
  so that *who* you recruit or befriend matters. Anyone the player invests in can be
  **promoted**: their card deepens, their memory grows, they join the story systems.
- **Tier 3 — the crowd.** Schedule-simulated bodies that make streets alive. Talking to
  one instantiates a Tier-2 card on the spot. The town has no "non-characters", only
  characters nobody has looked at yet.

**What the town calls you.** The street learns your name rather than being told it, and
what somebody calls you is a readout of where you stand with them: *the new owner*
(they know the pub changed hands, not who you are) → *Novak* (you are a fact on this
street) → *Tom* (they decided about you and it was fine) → *Toma* (two or three people,
ever). The gate is knowing, not liking: somebody can think well of you and still not
know what to call you.

**Core cast (Tier 1).** Rocco and Lena, the inherited loyalists — old muscle, older
bookkeeper. The three rival heads: Aldous Vane, Sera Kest — "the Widow" — and Danny Ro. Detective Mara
Ellis. The day-life ring: Sam, Ada, June (the uncle's estranged daughter and the moral
mirror), Father Emil (who knows the uncle's real history), the love-interest options —
Noor, a journalist and the dangerous choice, and Elias, a teacher with innocence at
stake — and the Fixer, broker between all three rivals and the gossip system
personified.

> **Open question.** The built cards drift from this sketch: Sam and Ada were written
> to fit a one-street scale rather than the day-job world, which did not exist when
> they were cast. Either the sketch is revised to match the cards, or these roles are
> re-homed in new characters now the day-job world exists. Not yet decided.

---

## 7. Systems

### 7.1 Memory

Per-character memory on the Stanford generative-agents architecture:

- **Memory stream** — timestamped events: conversations, sightings, heard rumours.
- **Retrieval** — relevance × recency × importance decides what enters a model call.
- **Reflection** — periodic summarisation into stable beliefs ("I trust him", "he was
  lying about the fire"). This bounds cost and context, and **beliefs formed from false
  rumours are the gameplay**.

Storage is human-readable markdown per character: debuggable, moddable, versionable.

### 7.2 Information and gossip

Facts are typed objects — who, what, when, certainty, source. When two NPCs' schedules
intersect and their relationship clears a threshold, facts about salient topics can
transfer, with mutation: certainty decays, details blur into rumour.

The player never sees ground truth. The **Ledger UI** shows what you *believe* the town
knows. Counterplay: silence a witness (many ways, most non-violent), buy a rumour's
source, plant a counter-story, or get ahead of it by confessing.

**Scale is a three-band scheme, and the design is honest about it.** A **Near** band
walks the world with a full brain. A **Mid** band lives in the gossip mill without a
body, carrying and passing talk about people you have not met. The **Far** band is a
record that answers exactly one question — roughly what share of this district has
heard it — and it saturates, because a story never reaches literally everyone. When a
Far resident is promoted, that share decides via a stable hash whether **this** person
had heard it, so leaving a street and coming back finds the same neighbourhood rather
than a re-rolled one.

Anyone load-bearing is exempt from the caps, and the mill outright refuses to forget
somebody carrying a rumour or a memory. **The world must not lose things because the
player walked round a corner.**

Districts have local information ecosystems: a rumour can own Copper Row and not exist
in Fairview.

**The population is a dial, not a ceiling.** It sits at 700. Measured: 350 residents
give an ordinary person 5.1 crossings a day, 700 give 12.9, 1,400 give 21.9, 2,800 give
38.9 — roughly linear. So the number is sized against a frame budget rather than a
design wall, and whether to raise it is an open question owned by the roadmap.

### 7.3 The telephone

§1's late-analog setting made into a system. **A phone is a place, not a pocket.** You
ring the pub, or the boarding-house hall phone, or the foundry office across the water,
and whoever is near it answers.

That single constraint generates the play. Reaching somebody is a gamble on their
afternoon. **Somebody else picking up is the interesting outcome, not a failure** —
now they know you called, and you must decide whether to leave word. A message left
with a person enters the mill as talk at one hop and second-hand confidence, which is
what a passed-along message actually is. Being unreachable at the wrong moment is
something that happens *to* the player, which a walking city could never do.

Wiretaps are the natural counterplay and follow from the same fiction.

### 7.4 Secrets, hooks and leverage

Learning a shameful secret grants a **weak hook** — one large favour. A criminal secret
grants a **strong hook** — standing coercion, and protection from hostile acts.

Hooks work on you too: what rivals and police learn about your night life becomes their
leverage. There is no investigation skill tree; the progression is the player's own
mental map of who knows what.

### 7.5 Suspicion and cover

Every Tier-1 and Tier-2 character tracks **suspicion** toward each of your lives.

It rises from contradictions — caught out of place, an alibi that conflicts with
another NPC's memory, unexplained money — and falls with maintenance: time spent,
consistent stories, staged evidence. Thresholds change behaviour: probing questions,
then checking with others, then confrontation.

**Persuasion outcomes are decided by game state** — relationship, evidence,
plausibility — and the model performs the scene. Players cannot talk an NPC into
believing the unbelievable, and NPCs cannot be talked out of what they remember seeing.

**On the telephone both of you are half-blind.** A voice on a line is not a face across
a table, so suspicion moves at 45% of its in-person weight, **in both directions**.
Your lies land better and so do theirs. That symmetry is deliberate: it stops the phone
being a straight upgrade over walking there, and makes "say this to their face or say
it down a wire" a real choice rather than a convenience.

### 7.6 The empire

- **Crew.** Recruited individuals from Tier 2, each with loyalty (to you personally),
  fear, ambition, competence and a breaking point. Loyalty is history: promises kept,
  cuts paid, respect shown, family remembered. Rot is visible early to the attentive.
- **Rackets.** Protection, smuggling, gambling, fencing, debt collection — each a small
  operating loop with staffing choices and an exposure profile.
- **Heat.** Per-district and per-investigator attention, driven by what witnesses
  actually saw and told. Reduced by lying low, by scapegoats, by corrupted officials.
- **Rivals.** Three authored organisations with distinct doctrines: the old-money
  machine (corruption and lawyers), the dockside syndicate (muscle and smuggling), the
  new crew (flashy, reckless). Their org charts are individuals — flippable, bribable,
  with their own loyalty rot.

> **Constraint: the Nemesis patent** (US10926179B2, active to 2036). No
> promotion-by-defeating-the-player structures anywhere. Rival advancement is driven by
> their internal politics, never by encounters with the player. Design review before
> building any rival internals.

**Faction agency.** The three organisations are rosters of people who already walk the
street, so poaching is not a new verb — it is recruit-by-need and recruit-by-hook aimed
at somebody who already had an employer. Allegiance is a state: pledge to an arm for
protection and tribute, or break with them and never be trusted again.

### 7.7 Violence

Staged deliberately: **consequence first, melee second, guns last.**

The fighting is Sleeping Dogs-lineage — physical, readable, third-person; fists,
grapples, improvised objects; skill is positioning, timing and reading opponents.
Firearms exist and change everything: drawing one escalates a scene, firing one is a
town-level event. Impact over blood, never gory.

**Playable melee is deferred until after the art pass**, because positioning-and-timing
combat cannot be judged on capsules.

**The consequence layer came first on purpose**, because a punch with no aftermath
teaches the player that violence is free, and that lesson is very hard to take back
later. It is built on one rule: **an injury is information.** It is on your face, the
infirmary keeps hours and has neighbours, and a man with his hand dressed on Tuesday
cannot claim he was somewhere quiet on Monday night. Getting hurt costs you capability
*and* the ability to have been elsewhere.

- Injuries persist, compound, and show as a look rather than a number.
- **They turn if untreated**, which is what makes the infirmary a decision. Treatment
  takes clean money — you cannot hand a doctor a roll of night money and expect the
  visit to be remembered for the right reason.
- **Trauma is cumulative and does not heal with the wound.** That is the whole
  difference between an injury and a scar.
- **Feuds are first-class, and are not suspicion.** A feud does not decay when you
  leave the room, and evidence cannot settle it — only somebody choosing to stop can.
  Two people in a hot feud will not work together, which is a scheduling problem solved
  with people rather than with a menu.

### 7.8 The honest life

A day job, chosen from a few tracks — bar, courier, office — providing cover, income
and a social graph. Relationships built through real conversation and remembered shared
history, never gift-grinding.

The honest life is not a mini-game, it is the stakes. The people in it are the ones
your other life endangers, and the game's best content — dinner-table scenes where
suspicion sits under small talk — lives here.

The courier track runs out of Meridian Parcel: Zlata's board goes up each morning until
noon, take the satchel, walk the route, deliver by evening for clean pay *and* cover —
a day worked in company colours lets a whole day-circle's suspicion breathe out. One
round a day, so the morning spent on parcels is a morning not spent on the other ledger
(P1 made literal). The open town keeps its own social calendar: every few days the
person who thinks best of you asks for an evening.

### 7.9 Economy

Two currencies that resist mixing: **clean money** (spendable anywhere, slow) and
**dirty money** (fast, but spending it visibly is evidence). Laundering through the pub
and the rackets is a core loop. Lifestyle upgrades — a better room, clothes, a car —
improve both lives but raise *how does he afford that?* if income does not cover them.

**The street has its own money.** It is not a payout table: the district holds a finite
amount, and everything you do changes it. Rackets take money out; wages and generous
cuts put money back; heat keeps people indoors. Prosperity and prices drift over a
week, never overnight, so a decision can be felt before its consequence lands — and
both feed the pub's daily takings.

**Squeezing the street therefore makes the street poorer, and a poorer street spends
less in your pub.** The racket that pays dirty money at night quietly costs clean money
in the morning, and past a point it costs more than it pays. Measured: aggressive play
finishes £94 *behind* a campaign that ran no rackets at all, despite £1,697 of racket
income. The trade is real and there is no dominant answer.

**And the screw turns twice.** For a while that was only half the loop — the take
drained the street and nothing let the street limit the take, so you collected the same
sixty a day from a district you had emptied. Now a racket's income scales with the
street it is squeezing, and a starved district simply has less to hand over. It says so
rather than quietly paying less: *"They're not holding out. There's nothing on that
street to hold out with."* Over 400 simulated worlds, cautious play's rounds fell from
468 to 434 as prosperity dropped to 0.40. Squeezing harder is genuinely capable of
earning you less.

**Nobody has infinite pockets.** A purse is what somebody can lay hands on **today** —
not their wealth, not their income, the money in the drawer. Ask for more and you get
what is there and the balance stays on the page, so a big marker stops being a
transaction and becomes a relationship: four visits, or one visit and a decision about
what you are willing to do to shorten it. Purses fill from the district's prosperity,
so squeezing the street drains the pockets you are trying to collect from — and it
arrives a few days later, when you have started relying on being paid. A debtor you
emptied goes to a patron overnight: **the money moves rather than appearing**, and the
favour they now owe is world state the Director can read. You will usually not know it
happened. You will notice they paid, and that they were colder about it than the money
explains.

**Suppliers are people.** Somebody brings the drink, and he is not a supply-chain node:
he comes on Thursdays, remembers when he was last paid, sells to eight other places on
this street and hears what all of them are worried about. Neglect loses him. A poor
neighbourhood does not — it only makes him dearer, and he tells you so himself.

**Legibility is a hard requirement, not a preference.** No number in this system is
ever shown as a number. Prices rising is Mitch asking for more and not explaining the
difference; a poorer street is two regulars drinking at home. If a value cannot be said
as somebody's circumstance, it is not surfaced at all — and that rule is asserted in the
test suite rather than merely intended.

---

## 8. The town

Meridian is one contiguous map, seven districts, each with a personality and an
asset-coherent build target:

1. **the Hook** — old port. Your pub, the docks, smuggling, the dockside syndicate.
2. **Copper Row** — immigrant market quarter. Dense street life, cash economies,
   loyalty.
3. **the Exchange** — the day-job world. Offices, the machine's lawyers, laundering.
4. **the Parade** — entertainment. Clubs, gambling, the new crew, information
   nightlife.
5. **Fairview** — residential hills. Where the honest life aspires to live; quiet
   money.
6. **Ironside** — industrial. Warehouses, logistics, places without witnesses.
7. **Gullwing** — faded resort waterfront. Off-season melancholy, hideouts, endgame
   turf.

The founding three differ in the two ways a map can actually differ, and both are
legible from the street without a word of explanation:

| | block size | who is there |
|---|---|---|
| **Copper Row** | 20m — tightest | dense, and there all day and all night |
| **the Hook** | 26m | where you live, and where the game happens |
| **Ironside** | 34m — widest | one person in fourteen sleeps there; one in three works there |

Ironside's brief is *warehouses, logistics, places without witnesses*, and only the
third of those is a mechanic. What makes a place unwitnessed is that nobody is in it —
so Ironside is a district you can be busy in at noon and alone in at midnight, and its
blocks are long low sheds with few doors rather than terraces with windows above them.
Everything the player can do anywhere else they can do here; the difference is only who
sees it, which is the difference this game is made of.

Territory control is social — who talks to you, who pays, who warns you — never a
map-painting minigame.

### 8.1 Streets, traffic and the car

The town is built streets-first, buildings fitted into blocks rather than the reverse.
An early version was a 90×90m slab with buildings and no streets — about the size of one
real city block — which is why it read as a diorama rather than a place. A walkable
block is 79m in Portland and 113m in Barcelona's Eixample; games compress, and the
research is consistent that **density carries the feeling of size, not area**.

- **A real grid.** 26m spacing in the Hook, tighter 20m in Copper Row so it reads older
  the moment you walk into it. Square kerb corners with the kerb line closed through
  them, which is what reads British.
- **Named streets in every district**, with the plates and the gossip reading the same
  table, so the town can never tell the player one name and a character another. An
  address is the unit people give directions in. Plates are mounted on corner
  buildings, as a council mounts them.
- **Two bridges between the districts, and only two.** A chokepoint is a place where
  things can happen: somebody waiting at a bridge is a scene, somebody waiting on an
  open grid is a man standing in a road. About a third of the town crosses one to work.
- **Traffic** as a deterministic, engine-free model: six vehicle kinds, lights at the
  big crossings, painted give-way bars elsewhere, buses that keep a circuit and cabs
  that idle at ranks. Four properties are held as tests because none can be judged from
  a screenshot — nobody overlaps, nobody crosses a stop line on red, nobody drives
  through a person, and the grid never wedges solid.
- **A driveable car**, arcade and kinematic: no gears, damage, fuel or tyre model. What
  it is *for* is that **a car is a thing witnesses describe**, and they describe it
  whether or not you wore the coat. A disguise buys doubt about your face and none at
  all about the vehicle standing in the street.
- **Collisions hurt and never kill.** Nothing in the code can produce a death — a
  property, not a tuning value. The victim is really injured on the system in §7.7,
  everyone nearby holds it as hard fact, and it records a low-heat exchange rather than
  a feud, because an accident is not a war until it goes unanswered. AI drivers brake
  for everybody; **only the player's car can strike anyone**, because the player is
  holding the wheel, and that is the difference between a system and a decision.

### 8.2 How the town looks

Contiguous terraces with party walls and chimneys rather than detached boxes.
Continuous pavements with square kerb corners. British sign grammar: name plates on
corner buildings, give-way paint, single yellows. Lamps with heads, parked cars,
shopfront fasciae with painted trade names, a crane-and-gasometer skyline. Detail in
`town-plan.md`.

**The look is stylised noir, and the reason is mechanical rather than aesthetic.** A game
about what people *think* they saw should look subjective and half-obscured. Weather and
fog cut draw distance, hide low-detail geometry, and make mood — three jobs from one
decision, and the first of them is what §4 is measuring.

---

## 9. Narrative

**Authored anchors, simulated bones, model as director.** The anchors are fixed
pressure points that fire on conditions rather than on dates alone, so the world state
at firing time makes each playthrough's version different.

**Between the anchors, the Director.** Authored beats are finite and were all written
before the player's town existed. So every few nights a world-level pass reads the
actual state — who is angry, who is exposed, what has been left undone, what the
street's money is doing — and authors the next pressure from it, using five primitives
and no others: put a fact in the mill, arrange a meeting, make a demand, change where
somebody is, seed a grievance.

It proposes an occasion; the simulation runs it, exactly as it runs an authored one.
Every person it names must exist, every pressure must justify itself from something
concrete, and **pressure comes from what the player neglected, never from bad luck** —
inventing a stranger, an accident or a coincidence is forbidden in the prompt and
discarded in validation. Most nights the correct answer is that nothing happens, and
the prompt argues for it. The player is never shown what is pending: §7.2's rule holds.

### The three acts

**Act I — The Inheritance.** Arrival, the pub, discovering what it really is. A choice
of posture — wind it down or take it over — that the game then makes hard to keep.

**Act II — The Squeeze.** Growth attracts the three rivals and one authored
investigator: Detective **Mara Ellis**, patient, personal, incorruptible so far. The
two lives begin colliding through the gossip system, and Act II's set pieces are
systemic collisions the spine guarantees — somebody from each life ends up in a room
together.

**Act III — The Ledger Comes Due.** The crisis is an **audit**, the least dramatic
instrument available, which is what makes it frightening. Somebody with a mandate asks
to see the pub's books, and the books are the one document in this game that has been
quietly lying since day one. Everything the player did to the ledger becomes evidence
in the other direction, **and it is wrong in both directions**: launder too little and
the night money has nowhere to have come from, launder too much and the pub earned more
than a pub on this street possibly could.

### The endgame

The matrix is *empire × life*, and **the player never picks an ending from a list**.
Each is a condition the world can be in when the books open. Several can be live at
once, and the last thing the player did decides between them.

- **Both** — keep everything. Requires the information landscape actively managed, not
  merely a big empire and a friend. Deliberately not achievable on a first playthrough.
- **The Kingdom** — you keep it all, and nobody is left who knew you before it.
- **The Straight Life** — you dissolve the business to keep the people.
- **Burn Both** — what doing nothing produces, which is why it is the default rather
  than a special case: the ledger comes due whether or not you answer it.
- **The Quiet Ending** — hand it to a crew member you built up. Not a fifth cell but a
  way of leaving the matrix; the only one you cannot reach by accident, and **the only
  ending with an epilogue** — three days where you are not in charge and you watch
  whether what you built holds, without a verb.

**The books have to hold.** Keeping anything requires the ledger to survive being
looked at. Managing every mouth on the street does not save books that describe a
business which does not exist, and that is the whole reason the crisis is an audit
rather than a raid. Two exemptions, both the price of a door: selling up (there is
nothing left to be in them) and handing over (the inspection lands on whoever signed).

**The audit has a face: Tobias Reese, Board of Excise.** Not corrupt — load-bearing
rather than characterisation, because an inspector with a price collapses the matrix
into *did you save up*. Not cruel either, which is the frightening part. He sits at a
table in the pub from nine until six and does not go anywhere else. The only thing
about him that moves is **how much he reads**: one item a day for six days, produce it
or tell him to put it in writing. It is the act's only verb that is not irreversible,
and the only one that costs nothing but attention.

**Attention must not be the whole game.** Measured: six answered mornings once
outweighed three acts of laundering, and the aggressive plan ended 100% Kingdom
whatever it had done to its books. Cooperation's relief is halved now and stonewalling
keeps its full weight — **being difficult moves him further than cooperating does**,
which is the asymmetry an inspector who cannot be bought should have. Aggressive play
now ends 100% Burn Both; cautious-and-answered splits 48/52. Paperwork buys room, not
absolution.

**The last day is a scene, not a countdown.** Two calls, and reaching one is not
reaching another: Lena moves the real books (gated on loyalty — a felony at a few
hours' notice, and her refusal has her own reason), somebody on the crew is told to go
quiet, or somebody in the day life hears it from you rather than from the street. All
three run down the telephone system, so whether you reach anybody at all is a question
about where they are standing.

**The act's best scene is its cheapest.** Lena knows exactly where the lie holds and
where it does not, and telling you is gated entirely on her loyalty. That is the thesis
of the project stated as a mechanic.

---

## 10. Agency, and the filters on scope

`agency-model.md` is canon and scores ~28 dimensions against shipped state of the art.
Two filters govern every scope decision:

1. **Every non-social system exists to give the social system stakes.** Money buys
   silence, violence is seen, health is how you meet June, clothes are how the street
   reads you. A system that does not feed the social layer is grind.
2. **Decisions ripple; maintenance is a chore.** Every system needs a lazy path and an
   invested path, and nothing may punish a player for ignoring it. Conversation must
   never be mandatory for progress — a full loop is playable with a few chip taps.

Headline targets: social memory 98, persistence 100, information 95, time 90, economy
85, multiple-solutions-per-obstacle 80 (a project law, not a feature), faction politics
75, operation planning 75, law-as-a-tool 70, legacy 70, violence 70 (staged), traversal
65 (breadth of place, never vehicle simulation), access-as-soft-keys 65.

**Refused outright:** body needs, crafting and lockpicking minigames, gear treadmills.

**Also settled:** visible odds are qualitative reads, never percentages; interiority is
*pressure, not personality* — the protagonist's nerve, guilt and appetite as intrusive
lines, never stats; competence tracks per domain and unlocks approaches rather than
raising numbers.

**Input parity is a rule, not an aspiration.** Every conversational action is reachable
with a stick and two buttons; typing and dictation stay first-class and never required.
The check: no dialogue state is reachable only by text.

---

## 11. Where the model sits

The honest question is: *if we were building the best possible game with the tools we
actually have — an agent that writes code, and a model that can be part of the running
game — is this what we would end up with?* Three places where the answer was no, and
what each became.

### The verb space is open; the verb implementation is closed

A conventional design gives the player a set of context-sensitive buttons — pay off,
lean on, plant doubt, collect, forgive, buy, squeeze, recruit, pledge. Every one has to
be authored, named and given a button, which is why games without a model in the loop
have a small verb set and enormous content around it.

> **The intent router.** The player types anything. A fast model classifies that text
> against the verbs genuinely available in this exact moment and returns one of three
> things: an existing mechanical verb with arguments, a novel action the game
> adjudicates against a state check, or pure narrative that goes to the conversation
> engine.

The critical property is that this is **classification, not adjudication**. The router
picks from a closed set assembled from live game state; anything it returns that is not
in that set is rejected and downgraded to speech. Outcomes are computed by the same
deterministic C# the buttons called. The model has moved from the skin to the
*interface*, not to the referee's chair.

The novel-action path is the interesting half. A player who says *"I'll tell Sera's
dockers that Vane's been shorting them"* is not doing anything the buttons offer, but
the game knows what the words touch: standing with two arms, a fact in the mill, a
place and an hour. So the router names a **requirement** from a closed vocabulary —
cash, dirty cash, standing, a hook on a person, crew, hour of day, heat — and the game
evaluates it, applying one **effect** from a closed vocabulary with clamped magnitude.
Novel actions are therefore *small and real* rather than large and fake.

It degrades cleanly. A lexical fast path handles unambiguous phrasings for free and
instantly, and is the complete fallback when no model is available.

### The story is directed, not only authored

Authored pressure points firing on state conditions are a real improvement over dated
beats, but the pressure a player feels on day 30 was still written on day 1, and there
is a finite number of them. The Director (§9) fills the space between the anchors,
under the same guardrail shape as the router: it proposes a pressure built from
existing primitives and the simulation runs it, validated against what the primitives
permit.

### Density is purchasable

Tier-2 generation produced 60 validator-passed cards in 19 calls for about 92k tokens.
The population number was never a constraint, only a decision — which is why §7.2
treats it as a dial.

### Runtime architecture

- **Tiered dialogue.** A cheap, fast model for Tier-2 and ambient; a stronger one for
  Tier-1 scenes and reflection passes. The client is provider-agnostic; a local-model
  fallback is evaluated later for cost and offline play.
- **Guardrails.** Player input is untrusted. System prompts carry the character card,
  retrieved memories and *hard state* — what this NPC knows and can do.
  Outcome-bearing moments — persuade, intimidate, seduce, confess — resolve as
  game-state checks first, and the model narrates the result. Output passes a validator: stays in character, no leaked instructions, length
  capped.
- **Voice.** TTS per character — cloud at first, pre-generated banks for ambient barks,
  streaming for live dialogue. Subtitles-first, so voice failures degrade gracefully.
- **Simulation.** Schedules, gossip and suspicion run on plain C#, tick-based, with
  KCD2-style level of detail: full simulation near the player, statistical elsewhere.
  The model fires only on player engagement and nightly reflection batches.
- **Cost envelope.** Target under $0.05 per played hour ambient; spikes during heavy
  Tier-1 scenes are acceptable. Measured from day one.

**Voice sourcing is consent-bound.** Only corpora whose contributors donated their
voices to build speech technology, and no identifiable public figures, ever.

---

## 12. Content pipeline

- **Town.** Modular city asset packs plus procedural placement — block assembly, props,
  signage, interiors from kits. The manual work is curation passes, not modelling.
- **Characters.** Base meshes and animation libraries from Mixamo, with batch variation
  in clothing, body and face by script.
- **Cards and schedules.** Generated in batch from district and occupation templates,
  validated by script (schedule feasibility, home and job existence), hand-touched on
  promotion.
- **Rendering.** A realistic-stylised target: clean PBR, strong lighting and atmosphere
  over asset density. HDRP is deliberately post-playtest and the current material work
  is pipeline-portable.
- **Writing.** The authored spine and Tier-1 cards are human-and-model collaborative;
  everything else is generated then curated.

---

## 13. Production requirements

A shipped game needs all of the following, none optional:

- **Front end** — main menu, new game and continue, options (audio, video, gameplay),
  key rebinding, pause, quit.
- **Audio** — music, ambience, footsteps, doors, UI feedback, and the mixer to balance
  them.
- **Save robustness** — versioned saves with migration, multiple slots, corruption
  recovery.
- **Accessibility** — subtitle sizing, colourblind-safe UI, remappable input, text
  scaling, and the no-timer guarantee that is already a design rule.
- **Localisation** — UI and authored strings externalised. Generated dialogue is a
  special case: the model can speak the target language directly, which is an advantage
  rather than a cost.
- **Performance** — level of detail and statistical simulation for distant districts,
  draw-call and memory budgets.
- **Controller support** and Steam Deck verification.
- **Platform** — Steam page, achievements, cloud saves, a release build pipeline.
- **QA** — a human test matrix on top of the automated harness. That harness is
  unusually strong for a project this size (3,620 unit checks, an eleven-day in-engine
  simulation on every build, Monte-Carlo balance runs, an AI playtest harness) and it
  materially reduces, but does not replace, human QA.

---

## 14. Shipping a game with a model in it

Three problems specific to this design, each of which can sink it.

**1. Inference economics.** Target under $0.05 per played hour ambient. The pricing
decision is deferred and is explicitly not a build-time blocker. Four models are on the
table:

- **subscription** — recurring fee, studio pays inference, margin scales with
  retention;
- **pay-as-you-go** — player buys credits, cost tracks usage honestly, worst first-run
  feel;
- **cheap purchase plus local model** — one-time price, inference on the player's
  machine, a quality drop and a hardware floor, but zero marginal cost and it works
  offline;
- **dedicated server** — hosted inference the studio operates, best control over
  quality and safety, highest fixed cost.

Nothing in the architecture picks one, and that is deliberate: the client is a
one-method interface, so a local model is a new implementation rather than a rewrite.
Cost is measured from day one so the decision is made against real numbers. The router
makes this sharper, not worse — it adds one cheap classification call per typed line on
the ambient tier, and it can fall back to the lexical path with no model at all.

**2. Content safety.** Generated characters will eventually say something indefensible.
A response validator exists; shipping needs guardrails, moderation, red-teaming and a
documented policy.

**3. Age rating.** ESRB and PEGI rate authored content; this is generated at runtime.
No clean industry precedent exists. Needs a human with a legal budget, early.

**The quality risk that outranks all three: slop.** If conversations read as chatbot
rather than person, the entire pitch collapses and nothing else in this document
matters. That means relentless card and prompt iteration, a model strong enough to hold
character, and latency low enough that talking feels alive.

---

## 15. Risks

1. **Simulation jank** — Shadows of Doubt's fate. Mitigated by scope discipline: gossip
   and schedules first-class, everything else cut ruthlessly.
2. **Cost and latency drift** — measured from the first milestone; tiering and
   reflection keep context small.
3. **Slop dialogue** — every conversation must be able to *change state*; a card
   quality bar; Tier-1 always hand-polished.
4. **The Nemesis patent** — a design review checkpoint before building rival internals
   (§7.6).
5. **Scale seduction** — the town wants to grow. The vertical slice is one district and
   it must be great before anything widens.
6. **Player-driven derailment** — the authored spine fires on conditions, which needs
   careful design so that systemic chaos delays the plot but cannot orphan it.

---

## 16. Architecture principle: separability

All narrative and content packs — character cards, scenes, districts, rating-sensitive
content — load as data, cleanly separated from engine and systems code, so the project
can be forked or modded into variant editions without touching the simulation core.
Content pipeline and memory formats are plain text, markdown and JSON, end to end.

---

## 17. What is not built yet

*Audited 2026-08-18 against the code and against `roadmap.md`.*

Kept deliberately and kept current. A design document that only accumulates achievements
stops being usable for planning.

**What was checked and is sound** — a list of gaps with no denominator cannot tell a
thorough audit from a lazy one: memory and nightly reflection; typed facts and the
gossip mill; the telephone as a place; weak and strong hooks; suspicion with its
confrontation ladder; the three rival arms with the three doctrines §7.6 names;
injuries that persist, turn if untreated and leave cumulative trauma; feuds as
first-class; the courier track; two currencies and laundering; the end-of-day summary;
the name ladder; the recognition ladder; no hard timers; the session-hook guarantee;
and the Nemesis constraint (the rival type is flat, with no promotion ladder anywhere).

### Unbuilt, and owned by a milestone

- **The two ledgers.** Empire growth, law as a tool, what expansion costs. The largest
  piece of unwritten *game*, as opposed to unfinished presentation.
- **The shape of a playthrough.** Onboarding beyond the first minutes, pacing,
  replayability, succession.
- **A played endgame.** Act III is built, measured and tested; nobody has sat down and
  reached it. Measured is not the same as felt.
- **Act II's seven pressure points, all fired in one run.** The machinery exists; this
  is still the thinnest stretch of the spine.
- **Live speech in a build a person has run.** The pipeline speaks on the dev machine;
  the voice models exist only there, and the copy-into-a-build script has never been run
  against a real build. The "ah"-filler retry fix is designed and unbuilt.
- **Vice and lifestyle** — §7.9's upgrades, the better room. Not started.
- **Romance.** Promoted to its own milestone, because §2's flagship illustration of the
  double life needs a partner to exist and none does. The propagation machinery
  underneath is real and running; what is missing is the relationship that makes
  catching an alibi hurt.
- **The other day-job tracks.** §7.8 offers bar, courier and office. The day-job system
  has no track concept: it is the courier round, singular. A choice this document
  offers the player on his first morning has never existed.
- **Smuggling and gambling.** Five rackets are named in §7.6 and three are built —
  collection, protection, fencing. Smuggling is the conspicuous absence: this is a port
  town whose Act III threat is Customs and Excise, and there is nothing to be caught at.
- **Interiors beyond the pub.** Every other door is a threshold.
- **A handful of story branches that have never fired in any recorded run.** A
  constant-key sweep finds them; planting their trigger conditions is ongoing.
- **HDRP.** Deliberately post-playtest.

### Needs scheduling rather than waiting

- **Reaction animation** — flinch, greeting, turn-to-look. The clips are on disk and the
  perception events they wire to already fire, so this is wiring rather than sourcing —
  with one caveat: of the six clips this needs, `head_no` is one of ten in the harvest
  found on 2026-08-18 to play a motion other than the one its name claims. Account and
  the current list in `clip-findings.txt`.

---

## 18. Settled decisions

Recorded here so they are not re-opened. Each was decided by Jafar.

- **The setting is a British port town, and it was discovered rather than chosen.** The
  prose had been writing *flat*, *colour*, *pavement*, *constable*, *neighbourhood* and
  *kerb* for weeks, and the streets were already Saltmarket, Quay Street, The
  Esplanade, Weighhouse Lane, Tannery Row. The American accent brief was the outlier.
  Money is £, the inherited business is a pub whose counter is the bar, its owner is the
  landlord, and the Act III audit is Customs and Excise under s.112 of the Customs and
  Excise Management Act. Consequences in `setting-britain-2026-07-31.md`.
- **The era is the late 1980s / early 1990s, and the currency follows from it.** Money
  is decimal — pounds and pence. Late-analog is load-bearing rather than flavour: it is
  what turns missed calls, wiretaps and being unreachable into mechanics.
- **The framing is the join, not gossip alone.** *"You're basing everything on gossip
  alone. That's not the entire game or it shouldn't be. It's a crime game, so violence
  and weapons should be a huge part of it. And the gossip and characters talking is just
  to make it better, more realistic, more relatable, more immersive… But that doesn't
  mean it's a text game which is just based on dialogue and combat and everything else
  doesn't play a role."* §1 is the result.
- **Quality target: high-quality indie**, not AAA breadth.
- **No hard timers**, anywhere, ever.
- **Violence is staged** — consequence first, melee second, firearms last.
- **Collisions hurt and never kill**, as a property of the code rather than a tuning
  value.
- **"Both" is not achievable on a first playthrough**, and the Quiet Ending is the only
  ending with an epilogue.
- **The population is a dial**, sized against a frame budget, not a design ceiling.
- **The standing order on quality:** use creativity, skill and available resources to
  get the best possible result in all aspects of the game — the best result *available*,
  not the first one that works.

---

## Companion documents

| document | what it owns |
|---|---|
| `roadmap.md` | the live plan, and the tiebreak on what happens next |
| `roadmap-history.md` | chronology, post-mortems, superseded plans, the M0–M3.1 as-built record |
| `agency-model.md` | depth targets per dimension, and the scope filters |
| `town-plan.md` | how the streets and buildings are expressed |
| `queue.md` | the next few hours of the roadmap |
| `process.md` | the decision log |
| `act1-draft.md`, `act2-draft.md`, `act3-draft.md` | the authored spine |
| `empire-roster.md` | the rival organisations and their people |
| `how-to-play.md` | the player-facing explanation |
| `setting-britain-2026-07-31.md` | the setting decision and its consequences |
