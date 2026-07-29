# LEDGER — Founding Design Document

Working title: **LEDGER** (your two lives are two accounts, and you are always balancing them).
Genre: open-city crime sim × slice-of-life social RPG. Single-player, premium, PC first.
Engine: Unity 6, C#. Setting: **late-analog** — landlines, payphones, answering machines,
messages left with people; no internet, no mobiles.

**Quality target: a high-quality indie game** (player decision 2026-07-26) — the bar is
Disco Elysium / Papers Please / Rimworld / Shadows of Doubt: reviews well, sells, gets
covered. Explicitly NOT chasing AAA breadth; the realistic ceiling for this team is AA /
premium indie (Kingdom Come 1, Hunt: Showdown, Mount & Blade), and the winning position is
*the game that does one thing no AAA studio can currently do, at a polish level that reads
as excellent*.

Status: founding doc **v2.0** (2026-07-26 — rewritten against built reality after the
agency-model discussion; §§14-16 are new). Companions: `agency-model.md` (depth targets per
dimension, and the filters that govern scope), `roadmap.md` (live milestone plan),
`process.md` (decision log), `act1-draft.md` / `act2-draft.md` (the authored spine),
`empire-roster.md`, `balance-findings-open.md`, `how-to-play.md`.

---

## 1. High concept

You are **Tom Novak**, and you arrive alone in Meridian Bay with one suitcase and a letter:
Mickey, your mother's brother, has died and left you his bar. The bar is real. So is what came with it — a half-dead criminal
outfit: two aging loyalists, a book of uncollectable debts, and a territory the city's three
established organizations have already begun to carve up.

By day you build a life: a job, an apartment, friendships, maybe love. By night you rebuild
the family business. Every person in the city — hundreds of them — is a character with a
schedule, a personality, and a **persistent memory of everything you've said and done**. They
talk to each other. Word spreads. The game is keeping your two lives apart in a city that
never stops comparing notes.

Breaking Bad as a systemic game: the drama isn't scripted — it leaks.

## 2. Why this game (novelty claims)

Claims we make explicitly, so every design decision can be tested against them:

1. **NPCs genuinely remember — forever.** Real conversations (LLM-driven, voiced), with
   persistent per-character memory. Not a dialogue tree in disguise.
2. **The double life is mechanical, not cinematic.** Cover stories only matter if NPCs can
   compare notes. Ours can: information propagates person-to-person through schedule
   intersections. Your girlfriend can catch your alibi from your coworker. No scripted game
   can do this; it is the heart of the game.
3. **Secrets are loot.** What you know about people — and what they know about you — is the
   primary currency and progression system (CK3 hooks × Outer Wilds knowledge-progression).
4. **A living city at honest scale.** Thousands of residents (3000 as of M9, 2026-07-26),
   any of whom can be promoted by attention into a full character. Almost none of them are
   simulated at any moment, and the design is honest about that: a **Near** band walks the
   world with a full brain, a **Mid** band lives in the gossip mill without a body — carrying
   and passing talk you have not met yet — and the **Far** band is a record that answers
   exactly one question, *roughly what share of this district has heard it*, saturating
   because a story never reaches literally everyone. When a Far resident is promoted, that
   share decides via a stable hash whether **this** person had heard it, so leaving a street
   and coming back finds the same neighbourhood rather than a re-rolled one. Anyone
   load-bearing is exempt from the caps, and the gossip mill outright refuses to forget
   somebody who is carrying a rumor or a memory: the world must not lose things because the
   player walked around a corner. The whole city persists as a seed plus the exceptions.
5. **Emergent betrayal.** Your organization is made of individuals with loyalty, fear, and
   grievances. Betrayal is never a cutscene; it is caused, and it is preventable.

If a feature serves none of these, it is cut.

## 3. Design pillars

- **P1 — Two lives, one clock.** Time is the resource the two lives fight over. Every hour
  spent on one is an hour not spent protecting the other.
- **P2 — Information is physical.** Facts exist in NPC memories, move between people, decay
  into rumor, and can be bought, planted, or silenced.
- **P3 — People, not units.** Every recruit, rival, lover, and witness is an individual whose
  relationship to you is personal history, not a meter.
- **P4 — Authored anchors, simulated bones, LLM director and interface.** *(revised
  2026-07-26 — see §17.)* The original wording was "authored spine, systemic flesh, LLM
  skin", and it under-used the model on both ends. The model is not only the skin: it is
  also the **interface** (the player says anything and it is routed into real mechanics)
  and the **director** (nightly world-level authoring read off the actual state). What
  stays authored shrinks to *anchors* — the acts' hard turns, the Tier-1 cast, the rules
  of the world. What stays simulated is the *bones* — money, time, information, standing;
  every outcome the player feels is still decided in deterministic C#. Each layer is
  still protected from the others: the model classifies and performs, it never adjudicates.
- **P5 — Consequences persist.** No quest resets, no memory wipes. The city's state is the
  save file.

## 4. Core loops

### Inner loop (minutes): the encounter
Talk / observe / act. A conversation that yields a secret; a delivery that builds trust; a
lie that plants a false memory. Every encounter writes to somebody's memory file.

### Middle loop (session): the day — Persona-style calendar
A day has time slots (morning / afternoon / evening / night). Obligations (day job shifts,
dates, collections, meets) compete for slots. End-of-day is a natural save/stop point with a
ledger summary: money moved, secrets gained, rumors spreading, loyalty shifts. The two lives
cross-feed Dave-the-Diver style: at work you plan the night; at night you worry about
tomorrow's lunch with her parents.

### The two modes (added v2.0)
**Week mode (days 1-7)** is Act I's on-ramp: survive the week, learn every system under
real stakes, answer Lena's question on day seven. **Open mode (day 8 on)** is the game:
no verdict, no countdown, no win condition. Losing remains possible but *scars* rather than
ends — exposure means the Fall (days inside, unwashed cash seized, every rumour about you
collapsing into public fact, and you start again from there). An ending screen would
contradict P5.

### Outer loop (campaign): the two ledgers
Grow the empire (territory, rackets, crew) while growing the life (relationships, standing,
comfort). The city squeezes both: rivals move on your territory, loved ones ask harder
questions. Acts advance when the authored spine's pressure points fire (see §8).

### Session hooks
"One more day" comes from: (a) an unresolved thread every evening (the sim guarantees one —
a rumor in flight, a recruit wavering, a date promised), (b) end-of-day ledger dangling
tomorrow's opportunity, (c) rising stakes — the bigger both lives grow, the more each day
can win or lose.
**Design rule — no hard timers** (player decision, 2026-07): nothing in the game expires on
a countdown. Pressure comes from escalation and consequence — rivals react to what you do,
not to a clock. The player sets the pace; the world raises the stakes.
No dark patterns: no dailies, no timers, no FOMO. Retention through curiosity and stakes.

## 5. The cast — three tiers (the Watch Dogs Legion lesson)

- **Tier 1 — Authored core (~14).** Handwritten cards, arcs, and voices. See §9.
- **Tier 2 — Generated middle ring (~150–300).** Full character cards (personality, history,
  job, home, schedule, connections, one secret, one need), AI-generated in batch, then
  hand-touched. Each has mechanical individuality: a unique skill, access, or connection
  (the customs clerk, the pharmacist with debts, the cop's ex-wife) so *who* you recruit or
  befriend matters. Anyone the player invests in can be **promoted**: their card deepens,
  their memory file grows, they join active story systems.
- **Tier 3 — Crowd (~thousands).** Schedule-simulated bodies that make streets alive
  (KCD2-style AI level-of-detail). Talking to one instantiates a Tier-2 card on the spot —
  the city has no "non-characters," only characters nobody has looked at yet.

**What the city calls you.** The street learns your name rather than being told it, and what
somebody calls you is a readout of where you stand with them: *the new owner* (they know the
bar changed hands, not who you are) → *Novak* (you are a fact on this street) → *Tom* (they
decided about you and it was fine) → *Toma* (two or three people, ever). The gate is knowing,
not liking — somebody can think well of you and still not know what to call you. It is
appended to every conversation's scene from one place rather than written into thirty cards.

## 6. The systems

### 6.1 Memory (the foundation)
Per-character memory following the Stanford generative-agents architecture:
- **Memory stream**: timestamped events (conversations, sightings, heard rumors).
- **Retrieval**: relevance × recency × importance scoring picks what enters an LLM call.
- **Reflection**: periodic summarization into stable beliefs ("I trust him", "he was lying
  about the fire") — bounds cost and context, and *beliefs formed from false rumors are the
  gameplay*.
Storage: human-readable markdown per character (debuggable, moddable, versionable).

### 6.2 Information & gossip
Facts are typed objects (who/what/when/certainty/source). When two NPCs' schedules
intersect and their relationship clears a threshold, facts about salient topics (the player,
crimes, romances) can transfer, with mutation: certainty decays, details blur into rumor.
Player-facing: the **Ledger UI** shows what you *believe* the city knows — never ground
truth. Counterplay: silence a witness (many ways, most non-violent), buy a rumor's source,
plant a counter-story, or get ahead of it by confessing.

**The second channel: the telephone (built).** §1's late-analog setting made into a system.
**A phone is a place, not a pocket** — you ring the bar, or the boarding-house hall phone, or
the foundry office across the water, and whoever is near it answers. That single constraint
generates the play: reaching somebody is a gamble on their afternoon; **somebody else picking
up is the interesting outcome, not a failure**, because now they know you called and you must
decide whether to leave word; a message left with a person enters the mill as talk at one hop
and second-hand confidence, which is what a passed-along message actually is. Being
unreachable at the wrong moment is now something that happens *to* the player, which a
walking city could never do.

### 6.3 Secrets, hooks, leverage (CK3-shaped)
Learning a shameful secret grants a **weak hook** (one big favor); a criminal secret grants
a **strong hook** (standing coercion, protection from hostile acts). Hooks work on you too:
what rivals and cops learn about your night life becomes their leverage. The investigation
skill-tree is the player's own mental map of who knows what — knowledge-as-progression.

### 6.4 Suspicion & cover (the double-life core)
Every Tier-1/2 character tracks **suspicion** toward each of your lives. Suspicion rises
from contradictions (caught out of place, alibi conflicts with another NPC's memory,
unexplained money) and falls with maintenance (time spent, consistent stories, staged
evidence). Thresholds trigger behavior: probing questions → checking with others →
confrontation. Crucially: **persuasion outcomes are decided by game state** (relationship,
evidence, plausibility), the LLM performs the scene. Players can't jailbreak an NPC into
believing the unbelievable; NPCs can't be talked out of what they remember seeing.

**On the telephone, both of you are half-blind (built).** A voice on a line is not a face
across a table, so suspicion moves at 45% of its in-person weight — in *both* directions.
Your lies land better and so do theirs. That symmetry is deliberate: it stops the phone being
a straight upgrade over walking there, and makes "say this to their face or say it down a
wire" a real choice rather than a convenience.

### 6.5 The empire (bottom-up crime sim)
- **Crew**: recruited individuals from Tier 2, each with loyalty (to you personally), fear,
  ambition, competence, and a breaking point. Loyalty is history: promises kept, cuts paid,
  respect shown, family remembered. Rot is visible early to the attentive.
- **Rackets**: protection, smuggling, gambling, fencing, debt-collection — each a small
  operating loop with staffing choices and exposure profile.
- **Heat**: per-district and per-investigator attention, driven by what witnesses actually
  saw and told. Reduce by laying low, scapegoats, corrupted officials (hooks!).
- **Rivals**: three authored organizations with distinct doctrines (Old-money machine:
  corruption and lawyers; the Dockside syndicate: muscle and smuggling; the New crew:
  tech-forward, flashy, reckless). Their org charts are individuals — flippable, bribable,
  with their own loyalty rot. ⚠ Design note: internal rival hierarchies must be reviewed
  against the Nemesis patent (US10926179B2, active to 2036) — no promotion-by-defeating-
  the-player structures. Rival advancement is driven by their internal politics, not by
  encounters with the player.
- **Violence, staged — consequence first, melee second, guns last** (player decisions
  2026-07-26/27). The eventual fighting is Sleeping Dogs-lineage: physical, readable,
  third-person; fists, grapples, improvised objects; skill is positioning, timing and reading
  opponents. Firearms exist and change everything — drawing one escalates a scene, firing one
  is a city-level event. Impact over blood, never gory. **Playable melee is deferred until
  after the art pass**, because positioning-and-timing combat cannot be judged on capsules.

  **The consequence layer is BUILT and came first on purpose**, because a punch with no
  aftermath teaches the player that violence is free and that lesson is very hard to take
  back later. The rule it is built on: **an injury is information.** It is on your face, the
  infirmary keeps hours and neighbours, and a man with his hand dressed on Tuesday cannot
  claim he was somewhere quiet on Monday night — getting hurt costs you capability *and* the
  ability to have been elsewhere.
    - Injuries persist, compound, and show as a look rather than a number.
    - **They turn if untreated**, which is what makes the infirmary a decision. Treatment
      takes clean money: you cannot hand a doctor a roll of night money and expect the visit
      to be remembered for the right reason.
    - **Trauma is cumulative and does not heal with the wound** — that is the whole
      difference between an injury and a scar.
    - **Feuds are first-class, not suspicion.** A feud does not decay when you leave the room
      and evidence cannot settle it; only somebody choosing to stop can. Two people in a hot
      feud will not work together, which is a scheduling problem solved with people rather
      than with a menu.
  Violence currently enters through systems that already exist — a job that goes wrong, a
  rival's answer, the Fall — rather than through a fight the player drives.

### 6.6 The honest life
A day job (chosen from a few tracks — bar, courier, office) that provides cover, income,
and a social graph. Relationships (friendship and romance) built through real conversation
and remembered shared history, not gift-grinding. The honest life is not a mini-game; it is
the stakes. The people in it are the ones your other life endangers, and the game's best
content — dinner-table scenes where suspicion sits under small talk — lives here.

**Built (v2.0):** the courier track at Meridian Parcel. Zlata's board goes up each morning
until noon; take the satchel, walk the route, deliver by evening for clean pay AND cover —
a day worked in company colours lets the whole day circle's suspicion breathe out. One
round a day; the morning spent on parcels is a morning not spent on the other ledger (P1
made literal). The open city also keeps its own social calendar: every few days the person
who thinks best of you asks for an evening.

### 6.7 Economy
Two currencies that resist mixing: clean money (spendable anywhere, slow) and dirty money
(fast, but spending it visibly is evidence — laundering through the bar/rackets is a core
loop). Lifestyle upgrades (apartment, clothes, car) improve both lives but raise "how does
he afford that?" suspicion if income doesn't cover them.

**The district's own money (M7, built 2026-07-26).** The street is not a payout table. It
holds a finite amount of money, and everything you do to it changes how much. Rackets take
money out; wages and generous cuts put money back; heat keeps people indoors. Prosperity and
prices drift over a week, never overnight, so a decision can be felt before its consequence
lands — and both feed the bar's daily takings. **Squeezing the street therefore makes the
street poorer, and a poorer street spends less in your bar**: the racket that pays dirty
money at night quietly costs clean money in the morning, and past a point it costs more than
it pays. The balance lab puts aggressive play $94 *behind* a campaign that ran no rackets
at all, despite $1697 of racket income — the trade is real, and there is no dominant answer.

**And the screw turns twice (decision 9, 2026-07-27).** The paragraph above was only half
the loop for a while: the take drained the street, and nothing let the street limit the
take. You collected the same sixty a day from a district you had emptied. Now the racket's
income scales with the street it is squeezing, so a starved district simply has less to
hand over — and it says so rather than quietly paying less: *"They're not holding out.
There's nothing on that street to hold out with."* Over 400 worlds, cautious play's rounds
fell 468 → 434 as prosperity dropped to 0.40. Squeezing harder is now genuinely capable of
earning you less, which is the shape this system was always supposed to have.

**Suppliers are people.** Somebody brings the drink, and he is not a supply-chain node: he
comes on Thursdays, remembers when he was last paid, sells to eight other places on this
street and hears what all of them are worried about. Neglect loses him. A poor neighbourhood
does not — it only makes him dearer, and he tells you so himself.

**Nobody has infinite pockets either (M13, built 2026-07-27).** The economy was finite in
one direction only — squeeze the street, the street gets poorer — while every *counterparty*
still produced whatever they owed on demand, out of a starving district, in one movement. A
purse is now what somebody can lay hands on **today**: not their wealth, not their income,
the money in the drawer. Ask for more and you get what is there and the balance stays on the
page, so a big marker stops being a transaction and becomes a relationship — four visits, or
one visit and a decision about what you are willing to do to shorten it. Purses fill from the
district's prosperity, so squeezing the street drains the pockets you are trying to collect
from, and it arrives a few days later when you have started relying on being paid. A debtor
you emptied goes to a patron overnight: **the money moves rather than appearing**, and the
favour they now owe is world state the Director can read. You will usually not know it
happened — you will notice they paid, and that they are colder about it than the money
explains.

**Legibility is a hard requirement, not a preference.** No number in this system is ever
shown as a number. Prices rising is Mitch asking for more and not explaining the difference;
a poorer street is two regulars drinking at home. If a value cannot be said as somebody's
circumstance, it is not surfaced at all — and that rule is asserted in the test suite rather
than merely intended.

## 7. The city — Meridian Bay

A dense coastal city, one contiguous map, seven districts, each a personality and an
asset-pack-coherent build target:
1. **The Hook** (old port) — your bar, docks, smuggling, the Dockside syndicate.
2. **Copper Row** (immigrant market quarter) — dense street life, cash economies, loyalty.
3. **Downtown** — the day-job world, offices, the machine's lawyers, money laundering.
4. **The Strip** (entertainment) — clubs, gambling, the New crew, information nightlife.
5. **Fairview** (residential hills) — where the honest life aspires to live; quiet money.
6. **Ironside** (industrial) — warehouses, logistics, places without witnesses.
7. **Gullwing** (faded resort waterfront) — off-season melancholy, hideouts, endgame turf.

**Built as of 2026-07-27: the Hook, Copper Row and Ironside. The other four are names in
this document and nothing on the ground** — Downtown, The Strip, Fairview and Gullwing have
no geometry, no places and no cast (player decision, 2026-07-27: *"ironside, rest later"* —
three districts prove the system, seven spend a runway).

The three that exist are deliberately different in the two ways a map can actually be
different, and both are legible from the street without a word of explanation:

| | block size | who is there |
|---|---|---|
| **Copper Row** | 20m — tightest | dense, and there all day and all night |
| **the Hook** | 26m | where you live, and where the game happens |
| **Ironside** | 34m — widest | one person in fourteen sleeps there; one in three works there |

Ironside's brief is *warehouses, logistics, places without witnesses*, and the third of those
is the only one that is a mechanic. What makes a place unwitnessed is that nobody is in it —
so Ironside is a district you can be busy in at noon and alone in at midnight, and its blocks
are long low sheds with few doors rather than terraces with windows above them. Everything the
player can do anywhere else they can do here; the difference is only who sees it, which is the
difference this game is made of.

### 7.1 Streets, traffic, and the car (M12, built 2026-07-26/27)

The district used to be a 90×90m slab with buildings and no streets — **about the size of one
real city block** — which is why it read as a diorama rather than a place. A walkable block is
79m in Portland and 113m in Barcelona's Eixample; games compress, and the research is
consistent that DENSITY carries the feeling of size rather than area does.

- **A real grid**, streets first and buildings fitted into blocks rather than the reverse.
  26m spacing in the Hook, tighter 20m in Copper Row so it reads older the moment you walk
  into it. Chamfered junction corners — Barcelona's trick, nearly free, and the single
  cheapest thing that makes a grid read as designed rather than as graph paper.
- **Ten named streets**, with the plates and the gossip reading the same table, so the city
  can never tell the player one name and a character another. An address is the unit people
  give directions in.
- **Two bridges between the districts, and only two.** A chokepoint is a place where things
  can happen: somebody waiting at a bridge is a scene, somebody waiting on an open grid is a
  man standing in a road. About a third of the city crosses one to work.
- **Traffic** as a deterministic engine-free model: six vehicle kinds, lights at the big
  crossings, stop signs elsewhere, buses that keep a circuit and cabs that idle at ranks.
  Four properties are held as tests because none can be judged from a screenshot — nobody
  overlaps, nobody crosses a stop line on red, nobody drives through a person, and the grid
  never wedges solid.
- **A driveable car.** Arcade and kinematic — no gears, damage, fuel or tyre model, which
  does not contradict the agency model's "no drivable-vehicle physics, ever". What it is
  *for* is that **a car is a thing witnesses describe**, and they describe it whether or not
  you wore the coat. The disguise buys doubt about your face and none at all about the
  vehicle standing in the street.
- **Collisions hurt and never kill** (player decision, 2026-07-27). Nothing in the code can
  produce a death — a property, not a tuning value. The victim is really injured on the
  system above, everyone nearby holds it as hard fact, and it records a low-heat exchange
  rather than a feud, because an accident is not a war until it goes unanswered. AI drivers
  brake for everybody; **only the player's car can strike anyone**, because the player is
  holding the wheel, and that is the difference between a system and a decision.

Districts have local information ecosystems: a rumor can own Copper Row and not exist in
Fairview. Territory control is social (who talks to you, who pays, who warns you) not a
map-painting minigame.

## 8. Narrative

**Structure: authored anchors, simulated bones, LLM director (P4, revised — see §17).**
The anchors are fixed pressure points that fire on conditions, not dates alone — the world
state at firing time makes each playthrough's version different.

**Between the anchors, the Director (M8, built 2026-07-26).** Authored beats are finite and
were all written before the player's city existed. So every few nights a world-level pass
reads the actual state — who is angry, who is exposed, what has been left undone, what the
street's money is doing — and authors the next pressure from it, using five primitives and
no others: put a fact in the mill, arrange a meeting, make a demand, change where somebody
is, seed a grievance. It proposes an occasion; the simulation runs it, exactly as it runs an
authored one. Every person it names must exist, every pressure must justify itself from
something concrete, and **pressure comes from what the player neglected, never from bad
luck** — inventing a stranger, an accident or a coincidence is forbidden in the prompt and
discarded in validation. Most nights the correct answer is that nothing happens, and the
prompt argues for it. The player is never shown what is pending: §6.2's rule holds.

- **Act I — The Inheritance.** Arrival, the bar, discovering what it really is. Choice of
  posture (wind it down / take it over) that the game then makes hard to keep.
- **Act II — The Squeeze.** Growth attracts the three rivals and one authored investigator,
  Detective **Mara Ellis** — patient, personal, incorruptible-so-far. The two lives begin
  colliding through the gossip system; Act II's set pieces are systemic collisions the spine
  guarantees (someone from each life ends up in a room together).
- **Act III — The Ledger Comes Due** (`act3-draft.md`; drafted, approved and wired
  2026-07-27 — the act opens off world state, runs its six days, and resolves in play).
  The crisis is an **audit** — the least dramatic instrument available, which is what
  makes it frightening. Somebody with a mandate asks to see the bar's books, and the books are
  the one document in this game that has been quietly lying since day one. Everything the
  player did to the ledger becomes evidence in the other direction, **and it is wrong in both
  directions**: launder too little and the night money has nowhere to have come from, launder
  too much and the bar earned more than a bar on this street possibly could.

  The endgame matrix is *empire × life*, and **the player never picks an ending from a list**.
  Each is a condition the world can be IN when the books open; several can be live at once and
  the last thing the player did decides between them:
    - **Both** — keep everything. Requires the information landscape actively managed, not
      merely a big empire and a friend. Deliberately not achievable on a first playthrough
      (player decision, 2026-07-27).
    - **The Kingdom** — you keep it all and nobody is left who knew you before it.
    - **The Straight Life** — you dissolve the business to keep the people.
    - **Burn Both** — what doing nothing produces, which is why it is the default rather than
      a special case: the ledger comes due whether or not you answer it.
    - **The Quiet Ending** — hand it to a crew member you built up. Not a fifth cell but a way
      of leaving the matrix; the only one you cannot reach by accident, and **the only ending
      with an epilogue** — three days where you are not in charge and you watch whether what
      you built holds, without a verb (player decision, 2026-07-27).

  The act's best scene is its cheapest: **Lena knows exactly where the lie holds and where it
  does not, and telling you is gated entirely on her loyalty.** That is the thesis of the
  project stated as a mechanic.

  **The books have to hold.** Keeping anything requires the ledger to survive being looked
  at — managing every mouth on the street does not save books that describe a business which
  does not exist, and that is the whole reason the crisis is an audit rather than a raid.
  Two exemptions, both the price of a door: selling up (there is nothing left to be in them)
  and handing over (the inspection lands on whoever signed).

  **The audit has a face: Tobias Reese, Board of Excise.** Not corrupt — load-bearing rather
  than characterisation, because an inspector with a price collapses the matrix into *did you
  save up*. Not cruel either, which is the frightening part. He sits at a table in the bar
  from nine until six and does not go anywhere else. The only thing about him that moves is
  **how much he reads**: one item a day for six days, produce it or tell him to put it in
  writing. It is the act's only verb that is not irreversible and the only one that costs
  nothing but attention.

  **But attention must not be the whole game (decision 10, 2026-07-27).** Measured for the
  first time, six answered mornings outweighed three acts of laundering: the aggressive plan
  ended 100% Kingdom whatever it had done to its books. Cooperation's relief was halved, and
  stonewalling kept its full weight — **being difficult moves him further than cooperating
  does**, which is the asymmetry an inspector who cannot be bought should have. Aggressive
  play now ends 100% Burn Both; cautious-and-answered splits 48/52. Paperwork buys you room,
  not absolution.

  **The last day is a scene, not a countdown.** Two calls, and reaching one is not reaching
  another: Lena moves the real books (gated on loyalty — a felony at a few hours' notice, and
  her refusal has her own reason), somebody on the crew is told to go quiet, or somebody in
  the day life hears it from you rather than from the street. All three run down the M10
  exchange, so whether you reach anybody at all is a question about where they are standing.

**Core cast (Tier 1, sketch):** Rocco & Lena (the inherited loyalists — old muscle, older
bookkeeper); the three rival heads (Aldous Vane / "the Widow" Sera Kest / Danny Ro); Det.
Mara Ellis; the day-life ring: Sam (first friend, coworker), Ada (landlady, sees
everything), the love-interest options (Noor — journalist, dangerous choice; Elias —
teacher, innocence at stake), June (uncle's estranged daughter, moral mirror), Father Emil
(knows the uncle's real history), and the Fixer (broker between all three rivals, gossip
system personified). ~14 total; full cards to be written next.

> **Status note (2026-07-25).** The prototype's approved cast cards drift from this
> sketch: Sam is currently a street go-between (both circles) and Ada a retired
> schoolteacher across from the bar — both fit the one-street scale better than
> "coworker" and "landlady" while the day job doesn't exist yet. Open decision: either
> this sketch is revised to match, or the doc roles are re-homed in new characters when
> the day-job world arrives (see `roadmap.md`, open items).

## 9. AI architecture (runtime)

- **Dialogue LLM, tiered**: cheap/fast model (Haiku-class) for Tier-2/ambient; stronger
  model (Sonnet-class) for Tier-1 scenes and reflection passes. Provider-agnostic client;
  local-model fallback evaluated later for cost/offline.
- **Guardrails**: player input treated as untrusted; system prompts carry character card +
  retrieved memories + *hard state* (what this NPC knows/can do). Outcome-bearing moments
  (persuade/intimidate/seduce/confess) resolve as game-state checks first; LLM narrates the
  result. Output passes a validator (stays in character, no leaked instructions, length cap).
- **Voice**: TTS per character (cloud API at first; pre-generated banks for ambient barks;
  streaming for live dialogue). Subtitles-first design so voice failures degrade gracefully.
- **Simulation**: schedules + gossip + suspicion run on plain C# (no LLM), tick-based, with
  KCD2-style LOD: full sim near player, statistical sim elsewhere. LLM only fires on
  player engagement and nightly "reflection" batches.
- **Cost envelope** (target): < $0.05 per played hour ambient, spikes during heavy Tier-1
  scenes acceptable. Measured from prototype day one.

## 10. Content pipeline (AI-first)

- **City**: purchased modular city asset packs (HDRP-compatible) + procedural placement
  scripts (block assembly, props, signage, interiors from kits). Manual work: curation
  passes, not modeling.
- **Characters**: base meshes from a character system (evaluate: Character Creator 4
  pipeline vs. Unity asset-store systems) + Mixamo/asset animation libraries; batch
  variation (clothing, body, face) by script.
- **Cards & schedules**: generated in batch by LLM from district/occupation templates,
  validated by script (schedule feasibility, home/job existence), hand-touched on promotion.
- **Rendering**: HDRP, realistic-stylized target ("good indie realism": clean PBR, strong
  lighting/atmosphere over asset density). Fallback to URP only if HDRP perf fails on
  mid hardware.
- **Writing**: authored spine and Tier-1 cards are human+AI collaborative; everything else
  generated-then-curated.

## 11. Milestones (revised 2026-07-25 — live plan lives in `roadmap.md`)

This section originally sketched M0–M4; the built milestones diverged from it by player
decision (gossip before scale, the week campaign before the day job). What follows is the
as-built record; `roadmap.md` carries the forward plan and supersedes this section's
numbering.

**Built and CI-validated (2026-07):**
- **M0 — Tech spike**: one code-built city block, day/night, 4 scheduled NPCs, Lena as a
  full LLM character (card, markdown memory, retrieval, reflection, suspicion), automated
  Windows builds with an in-engine self-test sim. *(Voice deferred to the vertical slice
  by decision.)*
- **M1 — The gossip engine** (was "living block", re-scoped): person-to-person rumor
  propagation through physical co-location, confidence decay, contradiction-driven
  suspicion, day/night circles; the player's damage-control verbs (pay off / lean on /
  plant doubt / lie low) with trait-decided outcomes; the whole cast conversational.
- **M2 — The week** (was "double-life MVP", re-scoped): nightly outfit drops that create
  witnesses, bar takings taxed by street heat, outfit patience, exposure fuse, win/lose
  the week, restart. Balance lab (Monte-Carlo bot weeks) tuned heat corroboration, money,
  and the once-per-story denial cap. Full 7-day campaign plays in CI on every build.
- **M3.1 — The Ledger**: PlayerKnowledge belief-state + Ledger UI v0 ("what you believe
  the city knows — never ground truth"), learned only through play; loyal-NPC warnings.

**Forward plan — see `roadmap.md`:** M3 (clean/dirty money + laundering, disguise,
end-of-day summary, conflict beats), M4 (secrets-as-loot hooks, suspicion-threshold
confrontations, Det. Ellis, save/load), M5 vertical slice (the original M3: The Hook
polished, 5 Tier-1 characters, 7 days of Act I, voice throughout — the is-this-fun gate),
M6+ expansion. Not-yet-scheduled from the original sketch: day job, rackets, calendar
slots UI, melee combat (deliberately deferred; see roadmap open items).

Scope honesty: systems milestones are heavily AI-buildable (code, cards, pipelines). The
vertical slice is where taste, iteration, and playtesting (the human's real job) dominate.

## 14. Agency: what the player can actually do (added v2.0)

`agency-model.md` is canon and scores ~28 dimensions against shipped state-of-the-art. Two
filters govern every scope decision:

1. **Every non-social system exists to give the social system stakes.** Money buys silence,
   violence is seen, health is how you meet June, clothes are how the street reads you. A
   system that does not feed the social layer is grind.
2. **Decisions ripple; maintenance is a chore.** Every system needs a lazy path and an
   invested path, and nothing may punish a player for ignoring it. Conversation must never
   be mandatory for progress — a full loop is playable with a few chip taps.

Headline targets: social memory 98, persistence 100, information 95, time 90, economy 85,
multiple-solutions-per-obstacle 80 (a project law, not a feature), faction politics 75,
operation planning 75, law-as-a-tool 70, legacy 70, violence 70 (staged), traversal 65
(breadth of place, never vehicle simulation), access-as-soft-keys 65. Refused outright:
body needs, crafting/lockpicking minigames, gear treadmills.

**Faction agency (built):** the three organizations are rosters of people who already walk
the street, so poaching is not a new verb — it is recruit-by-need and recruit-by-hook aimed
at someone who already had an employer. Allegiance is a state: pledge to an arm for
protection and tribute, or break with them and never be trusted again.

**Decided in the same discussion:** phones exist (late-analog, so information gains a
channel without travelling at internet speed, and wiretaps become natural counterplay);
visible odds are qualitative reads, never percentages; interiority is *pressure, not
personality* (the protagonist's nerve, guilt and appetite as intrusive lines, never stats);
competence tracks per domain and unlocks approaches rather than raising numbers;
vehicles/driving are approved but sequenced late.

## 15. Production requirements (added v2.0)

The design doc previously tracked mechanics only. A shipped game needs all of the
following, none of which is optional, and each of which is now on the roadmap:

- **Front end**: main menu, new game / continue, options (audio, video, gameplay), key
  rebinding, pause menu, quit. None of this exists today.
- **Audio**: music, ambience, footsteps, doors, UI feedback, and the mixer to balance them.
  Currently the game is entirely silent.
- **Save robustness**: versioned saves with migration, multiple slots, corruption recovery.
  We have one autosave slot and no version field.
- **Accessibility**: subtitle sizing, colourblind-safe UI, remappable input, no-timer
  guarantees (already a design rule), text scaling.
- **Localisation**: UI and authored strings externalised; generated dialogue is a special
  case (the model can speak the target language directly — an advantage, not a cost).
- **Performance**: LOD and statistical simulation for distant districts (doc §9 already
  specifies KCD2-style LOD; unimplemented), draw-call and memory budgets.
- **Controller support** and Steam Deck verification.
- **Platform**: Steam page, achievements, cloud saves, build pipeline for release.
- **QA**: a human test matrix on top of the automated harness (334 unit checks, a 9-day
  in-engine simulation per build, Monte-Carlo balance runs, an AI playtest harness — this
  infrastructure is unusually strong for the project's size and materially reduces, but
  does not replace, human QA).

## 16. Shipping an LLM game (added v2.0)

Three problems specific to this design, each of which can sink it:

1. **Inference economics.** Target < $0.05 per played hour ambient. **Deferred by the
   player, 2026-07-26** — explicitly not a build-time blocker; revisited only if we decide
   to publish. The four pricing models on the table then:
   - **subscription** — recurring fee, studio pays inference, margin scales with retention;
   - **pay-as-you-go** — player buys credits, cost tracks usage honestly, worst first-run
     feel;
   - **cheap purchase + local LLM** — one-time price, inference on the player's machine,
     quality drop and a hardware floor, but zero marginal cost and it works offline;
   - **dedicated server** — hosted inference the studio operates, best control over
     quality/safety, highest fixed cost.
   Nothing in the architecture picks one for us, and that is deliberate: `ILlmClient` is a
   one-method interface, so a local model is a new implementation, not a rewrite. Cost is
   measured from day one (`CostTracker`) so the decision is made against real numbers.
   The router (§17) makes this sharper, not worse: it adds one cheap classification call
   per typed line, on the ambient tier, and it can fall back to the lexical path entirely
   with no LLM at all.
2. **Content safety.** Generated characters will eventually say something indefensible.
   We have a response validator; shipping needs guardrails, moderation, red-teaming, and a
   documented policy.
3. **Age rating.** ESRB/PEGI rate authored content; ours is generated at runtime. No clean
   industry precedent exists. Needs a human with a legal budget, early.

**The quality risk that outranks all three:** slop. If conversations read as chatbot rather
than person, the entire pitch collapses and nothing else in this document matters. That
means relentless card and prompt iteration, a model strong enough to hold character, and
latency low enough that talking feels alive.

## 17. The first-principles pass (added 2026-07-26)

The player asked the right question: *if we were building the best possible game with the
tools we actually have — an agent that writes code and a model that can be part of the
running game — is this what we would end up with?* Honest answer: no, not quite. Three
places where the design was still built like a game made by a team of forty people who do
not have a language model, rather than one that does.

### Gap 1 — the verb space is hand-enumerated

Today the player's mechanical vocabulary is a set of context-sensitive buttons: pay off,
lean on, plant doubt, use what you know, collect, forgive, buy, squeeze, recruit, pledge.
Every one had to be authored, named, and given a button. That is the correct way to build
a game *without* a model in the loop, and it is why open-world games have a small verb set
and enormous content around it.

With a model, the verb *space* can be open while the verb *implementation* stays closed:

> **The intent router.** The player types anything. A fast model classifies that text
> against the verbs that are genuinely available in this exact moment, and returns one of
> three things: (a) an existing mechanical verb with arguments, (b) a novel action the game
> adjudicates against a state check, or (c) pure narrative that goes to the conversation
> engine as it does today.

The critical property is that this is **classification, not adjudication**. The router
picks from a closed set assembled from live game state; anything it returns that is not in
that set is rejected and downgraded to speech. Outcomes are still computed by the same
deterministic C# the buttons called. This preserves "game state decides, LLM performs"
exactly — the model has been moved from the *skin* to the *interface*, not to the referee's
chair.

The novel-action path is the interesting half. A player who says *"I'll tell Sera's dockers
that Vane's been shorting them"* is not doing anything the buttons offer, but the game
knows what the words touch: standing with two arms, a fact in the mill, a place and an
hour. So the router names a **requirement** from a closed vocabulary (cash / dirty cash /
standing / a hook on a person / crew / hour of day / heat) and the game evaluates it,
applying one **effect** from a closed vocabulary with clamped magnitude. Novel actions can
therefore be *small and real* rather than large and fake.

It degrades cleanly: a lexical fast path handles unambiguous phrasings for free and
instantly, and is also the complete fallback when there is no model available.

### Gap 2 — the story is hand-authored where it should be directed

Act I's pressure points and Act II's Squeeze are authored beats that fire on state
conditions. That is a real improvement over dated beats, but it still means the pressure a
player feels on day 30 was written by us on day 1, and there are a finite number of them.

> **The Director.** A nightly world-level pass — not a character-level one — that reads the
> actual state (who is angry, who is exposed, what the player has been ignoring, which
> relationships are load-bearing) and *authors the next pressure from it*.

Same guardrail shape as the router: the Director does not invent outcomes or bypass systems.
It proposes a pressure built from existing primitives — a fact injected into the mill, an
NPC's schedule changed, a demand made, a meeting arranged — and the simulation runs it. Its
output is validated against what the primitives permit. Authored anchors still exist and
still fire; the Director fills the enormous space between them, which today is empty.

### Gap 3 — the population is 36

We already proved density is purchasable: Tier-2 generation produced 60 validator-passed
cards in 19 calls for about 92k tokens. The population number is therefore not a
constraint, it is a decision we never revisited. Thousands is reachable with generation
plus a level-of-detail scheme where only the people near the player's attention are
simulated at full fidelity, exactly as KCD2 does it.

### What this changes in the plan

Pillar P4 is rewritten (see §3). The roadmap is re-sequenced: the router first (it is
purely additive — every existing verb keeps working, and typed text that routes to nothing
falls through to conversation exactly as today), then the economy substrate, then the
Director, then population scale. The economy is still worth building; it is simply the
*conservative* kind of depth, and it is better built underneath a game whose interface has
already stopped being a list of buttons.

## 18. What this document describes that does not exist yet (2026-07-27)

Kept deliberately, and kept current. A design document that only accumulates achievements
stops being usable for planning, and this one was drifting that way.

- **Playable melee.** Deferred until after the art pass. The consequence layer is built.
- **Four of the seven districts** in §7 — Downtown, The Strip, Fairview and Gullwing. Three
  exist. Deferred by the player, 2026-07-27.
- **Act II's seven pressure points.** Drafted and approved 2026-07-26; the machinery exists,
  the authored moments are not all fired. With Act I and Act III both running end to end,
  this is now the thinnest stretch of the spine.
- **A played endgame.** Act III is built, measured and tested; nobody has sat down and
  reached it. Measured is not the same as felt, and the distribution
  (`balance-findings-endings.md`) cannot tell us whether the six days have the right shape.
- **Most of §6.6's honest life** beyond the courier track: romance, the other job tracks, the
  apartment.
- **Lifestyle upgrades** in §6.7 — apartment, clothes, car as status. The car exists as
  transport and evidence, not as a purchase.
- **HDRP, the city pack, and voice.** Deliberately deferred; the game runs on procedural
  fallbacks by design, and the pack drops in with no code change.

## 12. Risks

1. **Simulation jank** (Shadows of Doubt's fate): mitigated by scope discipline — gossip
   and schedules first-class, everything else cut ruthlessly in v1 (no combat, no vehicles
   v1, interiors from kits).
2. **LLM cost/latency drift**: measured from M0; tiering + reflection keep context small.
3. **Slop dialogue**: every conversation must be able to *change state*; card quality bar;
   Tier-1 always hand-polished.
4. **Nemesis patent** (rival hierarchies): design review checkpoint before building rival
   internals (see §6.5).
5. **Scale seduction**: the city wants to grow; the vertical slice is one district and it
   must be great before anything widens.
6. **Player-driven derailment**: authored spine fires on conditions — needs careful design
   so systemic chaos delays but cannot orphan the plot.

## 13. Architecture principle: separability

All narrative/content packs (character cards, scenes, districts, rating-sensitive content)
load as data, cleanly separated from engine/systems code, so the project can be forked or
modded into variant editions without touching the simulation core. Content pipeline and
memory formats are plain text (markdown/JSON) end to end.

---

*Next documents: `cast-tier1.md` (full core-cast cards), `systems-gossip.md` (propagation
spec), `m0-plan.md` (tech-spike build plan for Unity).*

## 19. What changed on 2026-07-29 (and what it means for this document)

`roadmap.md` carries the build state; this section records only what
affects the DESIGN as written above.

**§6 systems — the street now shows the gossip.** Pairs stop, square off
at conversational distance, and break off when the player walks up if the
talk was about him. That is the first time the belief network has been
visible without opening a panel, and it is the single largest change to how
§2's premise reads in play.

**§6 — suspicion now becomes behaviour in a verified build.** Someone at
0.80 steps into the player's path; someone at 0.50 compares notes with a
neighbour. Both were written long ago and neither had ever executed.

**§14 agency — violence is still not a verb, and that is now an explicit
open decision** rather than an implicit deferral. See
`decisions-pending.md`.

**§15 production — the mocap line is optional, the Mixamo line is not.**
Motion matching is built and waits on a corpus that Mixamo does not sell;
Mixamo's free models and clips remain the outstanding animation item and
cost nothing.

**§8/§17 — nothing in the fiction changed.** No character, place, act or
ending was altered. The work was the layer between the writing and the
screen, which is exactly where this document said the gap was.
