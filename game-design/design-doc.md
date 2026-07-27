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

You arrive alone in Meridian Bay with one suitcase and a letter: an uncle you barely knew has
died and left you his bar. The bar is real. So is what came with it — a half-dead criminal
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
- **Combat — melee-first, guns rare** (player decision, 2026-07). Physical, readable
  third-person brawling in the Sleeping Dogs lineage: fists, grapples, improvised objects;
  skill is positioning, timing, and reading opponents. Firearms exist and change everything:
  drawing one escalates a scene, firing one is a city-level event (witnesses, heat spike,
  blood feuds). Presentation is hard-hitting but not gory — impact over blood. Violence
  stays consequence-heavy in the sim: injuries persist, crew members carry trauma, and
  every fight happened in front of somebody who remembers it.

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

**Suppliers are people.** Somebody brings the drink, and he is not a supply-chain node: he
comes on Thursdays, remembers when he was last paid, sells to eight other places on this
street and hears what all of them are worried about. Neglect loses him. A poor neighbourhood
does not — it only makes him dearer, and he tells you so himself.

**Legibility is a hard requirement, not a preference.** No number in this system is ever
shown as a number. Prices rising is Mirek asking for more and not explaining the difference;
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

**Built as of 2026-07-27: the Hook and Copper Row. The other five are names in
this document and nothing on the ground.**

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
  Detective **Mara Ossei** — patient, personal, incorruptible-so-far. The two lives begin
  colliding through the gossip system; Act II's set pieces are systemic collisions the spine
  guarantees (someone from each life ends up in a room together).
- **Act III — The Ledger Comes Due.** A triggered crisis forces the books open: the endgame
  matrix is *empire × life* — keep both (hardest, requires the city's information landscape
  actively managed), lose one to save the other, burn both, or the quiet ending: hand the
  empire to a crew member you built up, and see if what you built survives you.

**Core cast (Tier 1, sketch):** Rocco & Lena (the inherited loyalists — old muscle, older
bookkeeper); the three rival heads (Aldous Vane / "the Widow" Sera Kest / Danny Ro); Det.
Mara Ossei; the day-life ring: Sam (first friend, coworker), Ada (landlady, sees
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
confrontations, Det. Ossei, save/load), M5 vertical slice (the original M3: The Hook
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

## 18. What has actually been built since the first-principles pass (2026-07-27)

This document was last reconciled with the code at M9. Six milestones landed
after that in about eighteen hours, and the doc was silent on all of them —
which is exactly how a design document becomes a historical artifact. Written
down here so §§1-17 can be read knowing what is true.

### The protagonist has a name

**Tomas Vrba**, Marek's sister's boy. Marek is *your mother's brother*, named
in §1 and now load-bearing.

The part that is a design decision rather than a naming decision: **"the new
owner" was never a placeholder.** It is what people call you before they know
you, and this is a game about being known. So the name is something the street
LEARNS, and what somebody calls you is a readout of where you stand with them —
the new owner, then Vrba, then Tomas, then Toma, which two or three people ever
get to. The gate is knowing rather than liking. Gender stays deliberately
unset; the street mostly uses the surname, so a later choice costs nothing.

### M7.5 — access and operations, wired

Soft keys on real doors (§6.4's cover made spatial): a gate lists several ways
in and any of them works, the cheapest key you hold wins, and a refusal names
the way in you came closest to having. Operation planning is four decisions and
a read in words — never a percentage.

### M10 — phones and the distance layer

Delivers §1's "late-analog" setting as a system. **A phone is a place, not a
pocket**: you ring the bar, or the boarding-house hall phone, and whoever is
near it answers. Reaching somebody is a gamble on their afternoon; somebody
else picking up is the interesting outcome, not a failure; a message left with
a person travels as talk at one hop and second-hand confidence.

The trade is symmetric and is the point: a line reaches across the city
instantly and cannot read a face, so suspicion moves at 45% on a call. Your
lies land better and so do theirs, which is what stops it being an upgrade
over walking there.

### M11 — the consequence layer of violence (melee still deferred)

§8's combat line said injuries persist, crew carry trauma, and every fight
happened in front of somebody who remembers it. None of that needs a brawling
system and all of it needed to exist BEFORE one, because a punch with no
aftermath teaches the player that violence is free.

Injuries last, compound, show as a look rather than a number, and **turn if
untreated** — which is what makes the infirmary a decision, and treatment costs
clean money because you cannot hand a doctor a roll of night money. Trauma is
cumulative and does not heal with the wound. **Feuds are first-class**, not
suspicion: they do not decay when you leave the room and evidence cannot settle
them, only somebody choosing to stop. Two people in a hot feud will not work
together, which is a scheduling problem solved with people rather than a menu.

### M12 — streets, traffic, and a driveable car (pulled forward by the player)

The diagnosis was not "no cars". The district was a 90x90m slab — **about the
size of one real city block** — with buildings and no streets. §7's "dense
coastal city" was not being delivered by the geometry.

Now: a real grid on 26m spacing with chamfered corners, sixteen blocks, ten
named streets. Traffic as a deterministic Core model with six vehicle kinds,
lights, stop signs, and four properties held as tests that cannot be judged
from a screenshot. A driveable car — kinematic, arcade, no tyre model, which
does NOT contradict the agency model's "no drivable-vehicle physics, ever".

**And a car is a thing witnesses describe**, whether or not you wore the coat.
The disguise buys doubt about your face and none about the vehicle.

**Collisions hurt and never kill** (player decision, 2026-07-27). Nothing in
the code can produce a death — a property, not a tuning value. AI drivers brake
for everybody; only the player's car can strike anybody, because the player is
holding the wheel.

### M13 — finite counterparty purses

§6.7's economy was finite in one direction only: squeezing the street made it
poorer and the bar took less, but every counterparty still had infinite
pockets. A purse is now what somebody can lay hands on TODAY. Ask for more and
you get what is there; the balance stays on the page; a debtor you emptied goes
to a patron overnight and the money MOVES rather than appearing, leaving a
favour the Director can read.

### Copper Row is on the ground

§7 lists seven districts. **Two now exist.** Copper Row has its own grid, its
own streets, its own places, and its own people — and about a third of the city
crosses one of two bridges to work, which is what makes a chokepoint a place
where things can happen.

**The other five districts remain names in this document.** Downtown, The
Strip, Fairview, Ironside and Gullwing have no geography, no places, and no
cast. Ironside is referenced by the population generator and by research notes
as though it exists; it does not.

### What §§1-17 still describe that does not exist

Stated plainly so this document stops overselling the build:

- **Playable melee.** Deferred to after the art pass. Correct call.
- **Five of seven districts.**
- **Act III.** Drafted (`act3-draft.md`), and the endgame matrix is written and
  tested as Core code — but it is NOT wired into the game and no ending can
  currently fire. The crisis (an audit) is awaiting the player's approval.
- **Act II's seven pressure points.** Drafted and approved 2026-07-26; the
  machinery exists, the authored moments are not all fired.
- **The day job**, romance, and most of §6.6's honest life.
- **HDRP, the city pack, and voice.** All deliberately deferred; the game runs
  on procedural fallbacks by design.

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
