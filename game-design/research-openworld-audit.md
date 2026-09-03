# Open-World Feature Audit — GTA5/KCD2-class features vs. LEDGER

> **STATUS: LOG, 2026-07. NOT CURRENT.** A record of what was true on the
> day, kept because the reasoning is worth having. **Do not read it as the
> present state** — for that, `roadmap.md`. Items called "open" here have
> very likely been closed since.

84 features across six domains, each judged against the five novelty claims,
the pillars, and Risk 1 (simulation jank via scope creep). Produced by a
six-agent audit panel 2026-07-25; synthesized with the player's density
correction: density itself is NOT rejected — AI generation (design-doc §10)
collapses the cost of people, text, voice, and variation, so density plays
route through the generation pipeline rather than being cut.

## Adopt soon (M4–M5 window)

### Full daily schedule anchors (bed/meals/work)  `KCD2` · cost S · domain simulation
- **What:** Every NPC runs a deterministic daily routine of anchored activities — sleep, meals, work, leisure — at fixed venues and times.
- **LEDGER mapping:** LEDGER's schedules exist and already drive gossip-circle co-location; the missing piece is anchor granularity — named venues and hours for meals/sleep/work per Tier-1/2 card — so the player can learn who is where when: plan drop windows around witness positions, intercept a rumor-carrier before their evening circle, and give M3's schedule-conflict story beats concrete colliding venues.
- **Why:** Claim #4 ('living city at honest scale') and P2 need schedules to be a learnable puzzle, not just a sim substrate — KCD2's lesson is that anchors are what players memorize and exploit. It is nearly free: the mill already keys off co-location, so richer anchors are richer gossip topology with no new system. Keep anchors deterministic — that preserves Monte-Carlo balance-lab reproducibility and guards Risk 1.

### Witnesses report crimes to authority  `KCD2` · cost M · domain simulation
- **What:** An NPC who witnesses a crime actively seeks out a guard and files a report, which triggers a bounded investigation rather than instant omniscient pursuit.
- **LEDGER mapping:** Today drop witnesses feed ambient gossip and statistical heat. Add a directed edge: witness facts about drops route toward cop-nodes and into Detective Ellis's markdown memory on schedule intersection, with the mill's existing hop delay. Heat becomes literally 'what witnesses actually saw and told' (§6.5's own words). Counterplay is the existing verbs — pay off or intimidate the witness during the hop window, before the report lands.
- **Why:** M4 builds Ellis anyway; this makes her knowledge memory-backed instead of heat-meter-backed, honoring claim #2 and P2. It also creates the race-against-the-hop tension the gossip mill was built to deliver — the player watching the Ledger UI wondering whether the witness has talked yet is the game's core fantasy, aimed at the law.

### Police search AI (last-known-position, canvassing)  `GTA5` · cost M · domain simulation
- **What:** Police search intelligently around the player's last known position, canvassing the area rather than tracking the player psychically.
- **LEDGER mapping:** Invert it into Ellis-as-agent-in-the-gossip-graph: her AI is a retrieval policy — visit the drop site, schedule interviews with NPCs whose memory files hold relevant facts, corroborate (raising heat exactly the way the mill already computes corroborating heat), confront on threshold. Player counterplay targets her sources, not her: discredit a witness before her interview lands, plant a counter-story she will retrieve, spend a hook on someone in her chain.
- **Why:** The best adopt in this domain. It is cheap because the mill already stores who-knows-what — Ellis is a gossip node with agency. It turns M4's scheduled Ellis from a heat-triggered appearance into claim #2 made antagonist-shaped, and 'police AI as fact-collection instead of radius-search' is a genuine inversion of the GTA form that only LEDGER's architecture can do. She must obey the same rule as everyone: she acts on what her memory file contains, never on ground truth.

### Conspicuousness and carried evidence (bloody/dirty clothing)  `KCD2` · cost S · domain simulation
- **What:** The player's appearance state — blood, dirt, dress quality — changes how NPCs perceive, trust, and comment on them.
- **LEDGER mapping:** Extends M3's disguise v0 from a binary coat into a carried-evidence state: after a night drop, traces (bloodied cuff, smoke smell, dock grime) raise witness confidence in the mill and can spawn contradiction facts at the day job next morning ('he came in looking rough') unless the player changes and cleans — feeding suspicion exactly the 'caught out of place' fuel §6.4 enumerates.
- **Why:** The cheapest generator of cross-life contradictions, which is claim #2's core drama, and it gives the disguise coat a consequence dimension beyond the witness-confidence multiplier. KCD2 proved players internalize 'clean up before town' within an hour — it becomes ritual, and the ritual is the double-life fantasy embodied. Slots naturally into the M4 window on top of M3's disguise groundwork.

### Dirt/blood/appearance state readable by NPCs  `KCD2` · cost M · domain player-systems
- **What:** Visible dirt, blood, and clothing quality on the avatar change NPC reactions, comments, and treatment.
- **LEDGER mapping:** A 3-4 flag appearance state (bloodied, dirty, dressed-up) written into witness facts: blood after a night drop raises witness confidence and becomes a gossip topic; arriving at a day-life scene marked wrong triggers M4 probing questions ('what happened to your shirt?').
- **Why:** This is claim 2 made physical — your body is an alibi that can contradict your story, and the gossip mill already knows how to move the resulting fact. M3's disguise/appearance v0 (clothing state feeding witness confidence) is already on the roadmap; evidence-grade appearance flags are the natural M4 companion to suspicion-threshold confrontations. Keep it flags, not a per-garment fluid sim — that way lies Shadows-of-Doubt jank (risk 1).

### The debt book (loan-collection loop)  `genre-generic` · cost M · domain economy-activities
- **What:** A loan-sharking loop: track debtors, choose collection pressure, restructure or forgive.
- **LEDGER mapping:** The inherited 'book of uncollectable debts' from §1 becomes hooks v1's tutorial content: each debtor is a pre-authored leverage target, collection verbs reuse the built trait-gated damage-control architecture (lean/forgive/restructure), and 'forgive the debt for what you know' is a one-button bridge converting dirty money into secrets.
- **Why:** M4 builds hooks and needs concrete targets to teach them; the fiction already hands the player a list on day one. It requires almost no new systems — debtor cards plus verb reskins — and it makes claim 3 (secrets are loot) playable immediately instead of waiting for organic discovery. Highest value-per-cost item in this domain.

### Lifestyle assets as visible progression  `GTA5` · cost S · domain economy-activities
- **What:** Buy visible upgrades — apartment, wardrobe, car — as money sinks and status signals.
- **LEDGER mapping:** Already half-specified in §6.7: each visible asset becomes a typed fact in the gossip mill ('new coat, new watch — on bar wages?'), checked against NPCs' beliefs about your clean income, so conspicuous spending is literally evidence with hops, decay, and corroboration like any other rumor.
- **Why:** GTA sells assets as pure reward; LEDGER's twist — assets are self-inflicted rumors — is a claim-2 feature the M3 clean/dirty system sets up and M4 can finish for one asset class (clothing rides the existing disguise-coat state). Cheap because the mill already carries typed facts; this just adds a source that is the player's own purchase.

### Authored vantage points  `genre-generic` · cost M · domain space-traversal
- **What:** A handful of authored elevated or concealed spots from which the player can observe without being observed (RDR2 scouting, Watch Dogs cameras, distilled).
- **LEDGER mapping:** Inverts the built witness pipeline: at a vantage point (the bar's upstairs window, a fire-escape landing, a container stack), the player witnesses NPC schedule intersections and mints facts into PlayerKnowledge — 'Danny Ro's man meets the customs clerk, Tuesdays.' That gives M4's secrets-as-loot a non-conversational acquisition channel using machinery that already exists (events already generate witness records; point the camera the other way).
- **Why:** Directly powers claim #3 in the M4 window, and rewards claim #4's schedule sim by making NPC routines worth watching, not just talking to. Crucially this is authored spots, not a climbing system — five hand-placed positions per district, gated by access (a hook on the landlord gets you the roof key, which is claim #3 feeding itself).

### Travel time as clock cost  `KCD2` · cost S · domain space-traversal
- **What:** Moving through the world consumes in-game time that other obligations compete for.
- **LEDGER mapping:** Formalize per-location walk times against the day's time structure now, so M3's schedule-conflict beats can be spatial: the Fairview dinner versus the 22:00 dock drop is unwinnable because of the 40-minute crosstown walk, not because a designer said so. Later, where you live — above the bar or out in Fairview — becomes a self-selected difficulty dial for the double life: commute distance between your two lives is cover, and it is cost.
- **Why:** P1 says time is the resource the two lives fight over, and geography is the most honest, least gamey way to charge for it. It also honors the no-hard-timers rule: pressure comes from distance and scheduling, not countdowns. Right now it is a lookup table; retrofitting it after the map is built means re-tuning every beat.

### One contiguous map via seamless district streaming  `GTA5` · cost M · domain space-traversal
- **What:** A seamless world with no loading boundaries between areas (GTA5's whole map; KCD2's Kuttenberg region), versus discrete zones.
- **LEDGER mapping:** Contiguity is load-bearing for LEDGER specifically because information travels physically: an NPC commuting from The Hook to Downtown carries a rumor across the border, and following or being followed must work across districts. The runtime form should be per-district additive scenes streamed seamlessly, with the C# sim — already statistical off-screen by design — never depending on what is loaded.
- **Why:** The doc commits to one contiguous map (§7) and claim #2 quietly depends on it — a loading screen that teleports rumor-carriers would make propagation feel authored, not physical. The architectural decision (world coordinates, streaming scaffold, sim/scene decoupling) belongs inside M5's HDRP rebuild where it costs M; retrofitting it under seven built districts in M6+ is XL. Lock the architecture soon, build the acreage later.

### Diegetic UI minimalism — no floating meters  `KCD2` · cost S · domain presentation
- **What:** KCD2 ships near-zero HUD: no floating markers or bars; state is read from the world and from menus framed as period objects.
- **LEDGER mapping:** Lock as a UI constitution before M4 adds suspicion thresholds, hooks, and Ellis: suspicion is never a visible number or icon over a head — you read it in the LLM's performance (probing questions, cooled tone) and in loyal-NPC warnings; hooks and leads surface only in the Ledger book; no minimap rumor pings. The Ledger UI stays the single aggregation point and it is already belief-only, never ground truth.
- **Why:** Directly protects claims 1 and 2: floating suspicion meters would reduce LLM characters back to bars-with-faces and leak ground truth the doc explicitly forbids. The cost is a written principle plus restraint, but the timing is urgent — M4 (thresholded confrontations, Ellis, hooks) is exactly when a lazy debug meter becomes shipped UI. Cheapest feature on this list per unit of identity.

### Ambient street chatter as the literal gossip mill  `genre-generic` · cost M · domain presentation
- **What:** GTA5-style pedestrian chatter, upgraded: overheard NPC conversations whose content is the actual simulation state.
- **LEDGER mapping:** LEDGER is the one game where barks can be true: two Tier-3 NPCs at a schedule intersection render the real rumor object passing between them (topic, blurred details, confidence band → bark template), and overhearing it writes a lead into PlayerKnowledge — making eavesdropping a diegetic input channel for the Ledger UI, exactly the 'learned leads' acquisition the M3 re-key needs. Walking your own district becomes reading the city's mind.
- **Why:** The single highest-leverage presentation feature available: it is claim 2 made audible, it feeds the never-ground-truth Ledger through play instead of menus, and it creates the marketing moment no competitor can copy (the lie you told Tuesday, overheard mutated on Thursday). Text barks from templated rumor renders in the M4 window (the mill and PlayerKnowledge both exist now); ElevenLabs pre-generated variants at slice time. Do this before any generic bark table exists, so no slop chatter ever ships.

### Recognition barks — the city greets what it remembers  `RDR2` · cost S · domain presentation
- **What:** RDR2 NPCs remember recent player deeds and appearance, and say so in passing ('heard about that mess in Valentine').
- **LEDGER mapping:** A directed variant of the chatter feature: Tier-2/3 NPCs whose memory or received rumors include the player emit one-line greetings sourced from that state — warmth from a favor remembered, a too-pointed 'late night again?' from a neighbour whose suspicion crossed the probe threshold. Reuses the same rumor-to-bark templating; also doubles as soft feedback that a rumor reached this district (local information ecosystems made audible).
- **Why:** Claims 1 and 2 at street level: persistent memory is only believable if it leaks into passing contact, not just seated conversations — RDR2 proved this single trick carries enormous alive-ness per line of dialogue. It's an S once the ambient-chatter templating exists (same M4 window), and it gives the suspicion-threshold work a cheap surface: the probe stage of probe-verify-confront can begin as a bark before it's a scene.

### The world moves without you (timed obligations)  `KCD2` · cost S · domain narrative-encounters
- **What:** Quest events proceed on NPC schedules whether or not the player shows up.
- **LEDGER mapping:** 'Absence is an event': any accepted obligation the player skips (Ada's tea, a drop window, a date) writes a memory to the waiting NPC and can seed a mill fact ('he never came'), reusing schedules + conflict beats + the mill with zero new systems; consequences escalate, nothing expires.
- **Why:** This is the one timed-quest form that fits the no-hard-timers rule exactly as roadmap item 10 hopes — pressure from consequence, not countdown — and it sharpens claim #2: a no-show is a contradiction the city can compare notes about. It's a natural extension of M3.5's schedule-conflict beats; do it in M4.

### Multi-system quest solutions  `KCD2` · cost S · domain narrative-encounters
- **What:** Every quest is solvable through several independent systems — persuade, bribe, steal, fight, reputation.
- **LEDGER mapping:** An authoring rule for conflict beats and M4's Ellis confrontations: every beat must accept at least three shipped verbs (bribe/intimidate/discredit/lie-low/confess/plant doubt) plus one knowledge solve — a previously learned secret spent as a hook trumps the trait check.
- **Why:** LEDGER already owns the verb set and the trait-gated resolution; KCD2's lesson here is discipline, not machinery. The mandatory knowledge-solve is what turns claim #3 (secrets are loot) from a system into felt progression — the confrontation you breeze past because of what you learned on day 2 — and it costs authoring rules, not code.

### Camp-companion ambient dialogue (the bar as camp)  `RDR2` · cost M · domain narrative-encounters
- **What:** Companions at the home base chat among themselves about recent events and pull the player into conversation.
- **LEDGER mapping:** The bar is the camp: Rocco, Lena, and regulars run mill-state-keyed idle chatter (cheap-model tier or pre-generated banks per doc section 9), and overheard lines are a diegetic PlayerKnowledge feed — loitering in your own bar becomes how you learn what the street believes, honoring 'never ground truth'.
- **Why:** It solves the Ledger UI's acquisition problem (leads must be learned through play) with the game's warmest content instead of menus, and it generalizes M3.6's loyal-NPC warnings into ambient life, serving claims #2 and #4. Ship it text-first in M4; voice it in the slice.

### Emergent anecdote generation ('did you hear about...')  `genre-generic` · cost S · domain narrative-encounters
- **What:** NPCs retell notable events as anecdotes — including the player's own deeds, mutated by transmission.
- **LEDGER mapping:** Render mill facts — hops, confidence, and blurred details are already stored — into NPC-voiced retellings: the player hears their Tuesday drop come back as a garbled legend, which updates PlayerKnowledge (hearing your own rumor is the honest way to learn the city knows) and opens a play: correct it, encourage it, or seed a false version and listen for it to return.
- **Why:** This is LEDGER's signature moment and near-free — every field the narration needs already exists in the mill, and no shipped game can narrate the player's own past back at them with drift. It proves claims #1, #2, and #4 in a single line of dialogue; build in M4 and make it headline the slice demo.

### NPC-initiated encounters  `RDR2` · cost M · domain narrative-encounters
- **What:** Characters seek the player out on their own initiative to confront, warn, or invite.
- **LEDGER mapping:** Give M4's suspicion thresholds (probe → verify → confront) and loyalty warnings a body: past a threshold, the NPC's schedule spawns a seek-player task and the scene happens on their timing at your location — suspicion stops being a number and starts walking through your door.
- **Why:** It's the physicalization of section 6.4 already scheduled for M4, and the strongest dread mechanic the game can own: Detective Ellis sitting at your pub unannounced is claim #2's set-piece, generated rather than scripted. GTA5 did this with phone nags; LEDGER can do it with feet and schedules.

## Adopt at the vertical slice

### Ambient population density (crowds and traffic)  `GTA5` · cost M · domain simulation
- **What:** Dense pedestrian and vehicle streams that make streets read as alive regardless of simulation depth.
- **LEDGER mapping:** Vehicles are cut, so the LEDGER version is the Tier-3 ring at one-street scale: a modest crowd of schedule-simulated bodies around The Hook, any of whom instantiates a Tier-2 card the moment the player engages — 'the city has no non-characters, only characters nobody has looked at yet' (§5). Citywide GTA-density is an XL problem for M6+.
- **Why:** Claim #4 is a stated novelty claim and the vertical slice is its proof moment: the demo beat where a random pedestrian turns out to have a name, a schedule, and an opinion of you is the trailer shot. But density beyond one street before the slice is Risk 5 (scale seduction) verbatim — the doc says the slice is one district and it must be great before anything widens.

### NPC persistence surface (recognition greetings and grudges)  `RDR2` · cost S · domain simulation
- **What:** NPCs remember prior interactions across days and greet, thank, or snub the player unprompted when they cross paths again.
- **LEDGER mapping:** LEDGER's memory backend already exceeds RDR2's — what is missing is the ambient surface: templated barks generated from existing reflection beliefs ('heard the bar's under new management', a cold shoulder from someone holding a bad rumor) with zero LLM calls, so memory is visible before the player ever opens a conversation. Barks that reference held rumors also double as organic PlayerKnowledge leads, feeding the Ledger UI the way the roadmap wants leads learned.
- **Why:** Claim #1 is only persuasive if players notice it without being told, and RDR2 proved recognition barks are the highest-visibility-per-dollar memory signal in the genre. Templating from reflection beliefs keeps it inside the $0.05/hour envelope (§9), and the slice is the is-this-fun gate where the memory fantasy must land in the first ten minutes.

### Tavern dice with NPC opponents  `KCD2` · cost M · domain economy-activities
- **What:** A stakes-based dice minigame (Farkle) playable against NPCs in taverns, with cheating options.
- **LEDGER mapping:** Reborn as a back-room liar's-dice night at your own bar: each hand is a paced container for LLM conversation beats — losing small money loosens tongues, reading bluffs is diegetic tell-reading, and the relaxed night circle is exactly where the gossip mill lets secrets slip, feeding PlayerKnowledge and future hooks.
- **Why:** The cheapest charm-density win for The Hook: it gives the slice's five Tier-1 characters a reason to sit across a table and talk (claims 1 and 3), it's a secret-extraction verb that isn't interrogation, and liar's dice in a game about maintaining lies is thematically load-bearing. Keep the game itself trivially simple; the value is the conversation frame, not the dice.

### Walkable-scale town  `KCD2` · cost L · domain space-traversal
- **What:** Rattay/Kuttenberg-sized spaces where every destination is minutes on foot and NPCs visibly commute through shared streets.
- **LEDGER mapping:** The Hook in the M5 slice should be built to this metric: bar, cast homes, dock, church, and drop sites inside a 2-4 minute walk radius, so the whole cast's schedule routes cross in view of the player and of each other. This is a sizing constraint on the already-planned M5 city-pack assembly, not new work on top of it.
- **Why:** Claim #4 cites KCD2-proven scale, and what KCD2 proved is density-with-schedules, not size. Walkable compression is the spatial precondition of claim #2: witnesses, tails, and alibi contradictions only read if the player can see schedule intersections happen without a minimap telling them about it.

### Landmarks-as-navigation  `RDR2` · cost S · domain space-traversal
- **What:** Orienting by skyline silhouettes and learned geography rather than UI markers (RDR2/KCD2 sensibility, GTA5's readable skyline).
- **LEDGER mapping:** Give The Hook two or three always-visible verticals — the bar's neon, a dock crane, the church tower — and never ship GPS routing. NPC-given directions reference landmarks, which routes wayfinding through conversation, the game's core verb.
- **Why:** The player's mental map of the city should mirror the game's thesis: knowledge-as-progression (claim #3's ethos, §6.3's 'the skill tree is your own mental map'). Learning the streets is the same activity as learning NPC schedules, and at one-district slice scale this costs almost nothing.

### Crowd density as witness gradient  `GTA5` · cost M · domain space-traversal
- **What:** Ambient pedestrian population that varies believably per block and per hour (GTA5's pedestrian density, KCD2's LOD crowds).
- **LEDGER mapping:** Spatializes the already-built witness system: per-block, per-hour density profiles set witness-spawn probability and quality for night work, making where and when a route decision — Copper Row at noon is saturated, Ironside at 3am is the doc's own 'places without witnesses.' The disguise coat and heat corroboration already consume witness quality; this just makes the input legible in space instead of an abstract roll.
- **Why:** Converts the week campaign's invisible witness math into readable streetscape, serving claims #2 and #4 at once: the player learns the city's quiet hours the same way they learn NPC schedules. It reuses the Tier-3 crowd layer already planned for the slice, and a v0 (three density tiers by block and time-of-day on The Hook) is well inside M5's budget.

### Time-lapse transitions between day slots  `GTA5` · cost S · domain presentation
- **What:** The sped-up sky-and-streets cinematic when GTA characters sleep or time skips.
- **LEDGER mapping:** LEDGER's middle loop is a Persona-style slotted day; a 4-6 second time-lapse (sky wheel, streets emptying/filling per actual NPC schedules) between morning/afternoon/evening/night slots, landing on the end-of-day ledger summary (roadmap M3 item 6), makes P1 — two lives, one clock — something you feel rather than read.
- **Why:** Cheapest possible juice for the game's central resource (time), and it composes with already-scheduled work: the M3 end-of-day summary needs an entrance, and the day/night cycle already exists from M0. Bonus honesty: because Tier-3 crowds are genuinely schedule-simulated, the time-lapse can show the real sim, not a canned skybox — a free proof of claim 4 in every transition.

### Diegetic time cues — bells, foghorn, last call  `KCD2` · cost S · domain presentation
- **What:** KCD2's church bells mark canonical hours so players feel time without a clock widget.
- **LEDGER mapping:** The Hook gets a harbor foghorn at slot boundaries, the bar rings last call as the 22:00 drop window opens, Ironside's shift whistle marks morning — and the roadmap's open item 10 (the drop window is 'the closest thing we have to a timer') gets answered diegetically: no countdown UI ever; the world tells you the hour and outfit patience decays softly if you're late.
- **Why:** Serves P1 and directly implements the no-hard-timers design rule's spirit at the exact spot the roadmap flags as a playtest risk. It's a handful of audio events keyed to the existing time system, naturally part of M5's audio pass, and it gives the slice's single district an acoustic signature for free.

### Camp life → the living bar  `RDR2` · cost L · domain presentation
- **What:** RDR2's camp: the gang idles, chats, and reflects story state between missions, making the faction feel like people.
- **LEDGER mapping:** The bar is LEDGER's camp and it already has the sim RDR2 faked: Rocco and Lena run real schedules and real memories, so idle bar life (glass-polishing, book-keeping, crew nursing drinks) plus overheard crew banter can render actual state — a low-loyalty recruit audibly grumbling about his cut is claim 5's 'rot is visible early to the attentive' made literal, sourced from his genuine memory/loyalty values, not a bark table.
- **Why:** The vertical slice's is-this-fun gate lives or dies on whether The Hook feels inhabited, and the bar is the room the player returns to every day of the week campaign. Scope it hard to earn L not XL: Mixamo idle sets, pre-generated bark banks parameterized by loyalty/suspicion bands (no live LLM for ambience, per the cost envelope), five characters max. This is the demo's establishing shot.

### Cinematic conversation camera  `RDR2` · cost M · domain presentation
- **What:** RDR2's optional cinematic framing — letterboxed, composed shots during conversations and travel.
- **LEDGER mapping:** Drop the travel half (small map, no vehicles); adopt the conversation half: LLM scenes get composed over-shoulder framing with state-reactive cuts — a probing question at a suspicion threshold earns a slow push-in, a dinner-table scene holds a two-shot while small talk sits over dread. The camera reads game state the player can't see numerically (which the diegetic-minimalism rule requires).
- **Why:** The doc names dinner-table scenes 'the game's best content,' and right now that content is text exchange; the slice must prove LLM conversation feels like drama, not chat. A camera that performs suspicion state is the presentation layer of claim 1 and of the 'LLM performs, game state decides' guardrail — the framing telegraphs the stakes the meters no longer show. Three or four shot templates plus threshold triggers, not a cinematography system.

### Consequences that surface days later  `KCD2` · cost M · domain narrative-encounters
- **What:** Actions trigger delayed follow-ups — steal from a merchant and guards question you a day later; kindness returns as a gift.
- **LEDGER mapping:** 'Consequence beats': conflict beats whose fire conditions are elapsed-days plus mill/hook state — the witness you bribed on day 2 returns for more on day 5, the man you discredited tells his version to Ellis — using the existing beat-trigger machinery plus a day-offset condition that queries the mill.
- **Why:** The slice's 7 days of Act I live or die on day-6 payoffs of day-2 choices; this makes claim #1 legible (memory-forever means the bill arrives late) and it's cheap because the mill already stores the who/what/when. Author 6-10 of these for the slice — they are the difference between a week and seven disconnected days.

### Stranger arcs across chapters  `RDR2` · cost M · domain narrative-encounters
- **What:** Recurring strangers whose later encounters reflect the state your earlier choices left them in.
- **LEDGER mapping:** A promoted-NPC arc pattern: a tiny authored state machine (helped/exploited/ignored) selects each re-encounter's premise, while the LLM performs the changed scene from the NPC's own markdown memory file — the re-encounter is literally generated from what they remember of you.
- **Why:** Nothing demonstrates claim #1 like meeting someone again and hearing your own history in their mouth. RDR2 faked this with branching script; LEDGER can do it for real, and one or two arcs (Ada and Father Emil are ideal) in the slice is the cleanest proof that the memory tech is a game, not a chatbot.

### Chance-encounter recognition on the street  `RDR2` · cost S · domain narrative-encounters
- **What:** Ambient roadside encounters where passersby react to who the player is and what they have done.
- **LEDGER mapping:** Recognition, not combat: when a schedule intersection puts the player near an NPC holding a player-fact above a confidence threshold, play a cheap reaction — crossing the street, staring, whispering to a companion, or a one-line approach — as a bark layer over existing mill and schedule data.
- **Why:** RDR2/GTA5's ambush-and-rescue form needs combat verbs LEDGER cut, but the recognition kernel makes the mill visible on the street without opening a menu. The whisper you notice across the road is claim #2 rendered in body language — the cheapest possible sell of 'the city compares notes', and pure demo value for the is-this-fun gate.

### Mission variety across the campaign  `GTA5` · cost M · domain narrative-encounters
- **What:** Missions deliberately rotate structures and verb mixes so no two feel alike.
- **LEDGER mapping:** Drop variants for the week campaign: each night's job gets a distinct witness/heat/social profile — a handoff among bar regulars, an Ironside meet with no witnesses but a treacherous partner, a Copper Row run past a talkative street — so a different system bites each night; same verbs, different information problems.
- **Why:** Day 4 of the current week risks feeling like day 2 with bigger numbers. GTA5 bought variety with bespoke scripting; LEDGER can get it by parameterizing the drop's exposure profile against systems that already exist, which respects Risk 1 while feeding claim #2 — each variant endangers a different part of which life.

## Adopt later (post-slice)

### Stolen-goods recognition / item provenance  `KCD2` · cost M · domain simulation
- **What:** Stolen items carry provenance; owners and merchants recognise them on sight and react (refuse trade, call guards).
- **LEDGER mapping:** The currency half is already adopted: clean/dirty money in M3 is exactly this mechanic applied to cash — spending dirty visibly is the recognition event, logged as evidence by witnesses. The object half (fenced loot a Tier-2 recognises — 'isn't that Ada's brooch?') is P2 in its purest form, information physically attached to an object, and would define the fencing racket's exposure profile.
- **Why:** Rackets are M6+; building object provenance before fencing exists is a system without a consumer — exactly the scope creep Risk 1 warns against. Park it with the fencing racket spec and let M3's dirty-money version prove the recognition loop first.

### Role disguises (pass as courier/staff/uniform)  `KCD2 / genre-generic (Hitman)` · cost L · domain player-systems
- **What:** Wearing an outfit associated with a role or faction lets you move through spaces as that role until someone sees through it.
- **LEDGER mapping:** Extends the day/night disguise coat into a third claimed identity: a per-NPC recognition check (how well this person knows your face, from their memory file) against outfit-role fit; being recognised trips no alarm — it mints a high-confidence contradiction fact ('I saw the barman dressed as a Vane courier') that enters the mill.
- **Why:** Novel here precisely because of claim 2 — in Hitman a blown disguise means combat, in LEDGER it is a rumor with your name on it, the scariest object in the game. But it needs rival interiors and Tier-2 density (M6+ districts) to have anywhere to matter, and per-NPC face-recognition modelling is real work. Post-slice, after the coat proves the two-identity version is fun.

### Gambling den as operating racket  `genre-generic` · cost L · domain economy-activities
- **What:** An owned illegal card room: staff it, set the rake, attract patrons, absorb the exposure.
- **LEDGER mapping:** A §6.5 racket assembled from LEDGER's own primitives: patrons form a dense owned night circle (a gossip hub where you set the guest list), the house's book of who's in debt mints weak hooks per §6.3, the dealer is a Tier-2 hire whose loyalty gates skimming, and every patron is a witness on the exposure profile.
- **Why:** The best-fitting racket in the genre because the house hears everything — it converts claim 4's living city into claim 3's loot inside a room the player owns, and dirty rake feeds the M3 laundering loop. But it's a full operating loop plus a venue; scheduling it inside M4-M5 would endanger the slice, so it lands with the rackets system post-slice, second after protection.

### Protection racket as operating loop  `genre-generic` · cost L · domain economy-activities
- **What:** Collect regular payments from local businesses in exchange for security against rivals and misfortune.
- **LEDGER mapping:** Each protected shopkeeper is a named individual paying out of fear or earned loyalty (§6.5's distinction), collections are calendar obligations competing for P1 time slots, a rival leaning on your street is an attack on relationships not map paint (§7 territory-is-social), and protected shopkeepers are witness nodes whose disposition decides what reaches Ellis.
- **Why:** This should be the first racket built post-slice: §6.5 already sketches it, it scales the week campaign's street into a territory made of individuals (claims 4 and 5), and failing to actually protect someone creates the grievance-to-defection chain claim 5 needs. Later than M5 only because the slice must stay one bar deep — Risk 1 discipline.

### Crew cuts & payroll  `GTA5` · cost M · domain economy-activities
- **What:** Heist crew members demand percentage cuts scaled to skill; cheaper crew underperform.
- **LEDGER mapping:** The cut becomes standing loyalty history per §6.5 ('cuts paid'): pay rates are promises NPCs remember forever (claim 1), crew compare notes on cuts through the same gossip channels that carry everything else, and discovered skimming or favoritism is a grievance event on the road to claim 5's betrayal.
- **Why:** GTA treats the cut as a one-shot price/performance slider; LEDGER should treat it as a relationship instrument — the mill guarantees your crew will find out who got paid what, which no scripted game can do. Needs a crew larger than Rocco and Lena, so it lands with post-slice recruitment, but the cut field belongs in the crew data model from day one.

### District identity  `GTA5` · cost XL · domain space-traversal
- **What:** Each neighbourhood instantly readable through architecture, signage, crowd type, and ambient audio.
- **LEDGER mapping:** Each of the seven §7 districts maps to one coherent asset pack plus a local information ecosystem — identity is aesthetic and epistemic at once. Crossing a border should mean entering a different rumor climate, witness density, and heat profile: a rumor can own Copper Row and not exist in Fairview, and the streetscape should tell you which regime you are in.
- **Why:** Already doctrine in §7, but Risk 5 says the slice is one district and it must be great first. The M5 Hook should lock the district template — asset kit, palette, soundscape, crowd profile, info-ecosystem parameters as data — so M6+ stamps six more districts through the pipeline instead of hand-building them. Adopting the template discipline now is what makes the XL later affordable.

### In-world news reacting to player crimes (radio news / RDR2 newspapers)  `GTA5` · cost M · domain presentation
- **What:** News broadcasts and papers that report the player's story-visible crimes back to them.
- **LEDGER mapping:** Map it as the top tier of the exposure fuse: when district heat plus corroboration crosses a threshold, a local paper runs the story — which injects a high-confidence, multi-district fact into the gossip mill in one hop. Ties directly to Noor (journalist love interest, 'dangerous choice') as an authored pressure point: dating her means sleeping next to the broadcast layer.
- **Why:** It genuinely serves claim 2 (information is physical), but it is also the one presentation feature that can break the game's elegance: broadcast bypasses person-to-person propagation, which the doc calls the heart of the game. So it must be rare, threshold-gated, and mostly authored (an Act II beat), not a systemic channel. Post-slice, after the person-to-person mill has proven itself in playtest; building it earlier risks papering over the core system instead of showcasing it.

### Dynamic weather  `GTA5` · cost M · domain presentation
- **What:** A weather cycle (clear/rain/fog) that changes the look and feel of the open world.
- **LEDGER mapping:** Weather gets mechanical teeth or it doesn't ship: rain and fog reduce street witness density (fewer Tier-3 bodies out → fewer witness events at nightly drops) and raise disguise effectiveness (the disguise coat is unremarkable in rain → lower witness confidence feeding the mill). Two or three states, no full meteorology.
- **Why:** The witness-density mapping is real and legible — players would learn 'rainy nights are working nights,' which deepens the drop-planning loop without new systems, only modifiers on existing ones (witness spawn, confidence). But it is pure Risk-1 scope creep before the slice: HDRP rain, wet surfaces, and audio are polish-budget items, and M2's balance lab would need re-tuning for the witness modifier. Post-slice, as a named small feature, capped at 'modifier plus mood.'

### Friend-activity hangouts  `GTA5` · cost M · domain narrative-encounters
- **What:** Optional shared activities (darts, drinks, a drive) that frame bonding dialogue with companions.
- **LEDGER mapping:** Strip the minigame, keep the frame: an 'activity scene' is a conversation container (a walk along Gullwing, cards at the bar) that grants section 6.4's time-spent suspicion maintenance and writes shared-history memories that later corroborate alibis — 'we were playing cards Thursday' becomes evidence you manufactured.
- **Why:** The doc is explicit that the honest life is not a minigame, and the slice's relationship content should stay pure conversation. Post-slice, though, activity frames give maintenance mechanical texture plus the LEDGER twist — hangouts as alibi manufacturing serves claim #2 directly. Wait until the day-job world lands.

## Adapt heavily (the idea survives, the form changes)

### Jail / pillory punishment chain  `KCD2` · cost M · domain simulation
- **What:** Getting caught leads to sentencing: time-skipped jail terms and public pillory shame that NPCs witness and remember.
- **LEDGER mapping:** LEDGER's version is not a jail sim but 'taken in for questioning' — an Ellis confrontation beat (M4 threshold ladder) that consumes time slots (P1's actual currency), injects a high-confidence fact ('Ellis pulled him in') into the mill, and spikes suspicion across the honest life. The pillory needs no building: the gossip mill IS the pillory.
- **Why:** Losing hours is the one punishment LEDGER can make sting without combat or a game-over, and the reputational fallout rides entirely on built systems. But a literal jail (cells, sentences, world-ticks-without-you, escape content) serves no claim and adds a whole sim mode — cut the form, keep the cost. This also gives Ellis a mid-tier consequence between probing questions and the exposure fuse, which the escalation ladder currently lacks.

### Regional reputation meter  `KCD2` · cost S · domain simulation
- **What:** A numeric per-region standing accumulated from deeds, adjusting prices, greetings, and guard tolerance in that region.
- **LEDGER mapping:** LEDGER's district reputation must remain what §7 specifies: the emergent aggregate of individual memories, locally wrong where the rumor hasn't traveled. The only legitimate meter-shaped thing is a district 'temperature' readout inside the Ledger UI, derived from PlayerKnowledge — what you believe each district has heard — never from ground truth.
- **Why:** research-mechanics.md already ruled on this: per-individual opinion feels real, region meters feel gamey. Adopting KCD2's meter would flatten the gossip mill's best trick — a district that hasn't heard yet — into a number, and a ground-truth meter would repeat the exact 'never ground truth' violation the roadmap just spent M3.1 fixing. The adapted belief-derived readout gives the Ledger UI a district view for free.

### Dynamic world events / random encounters  `GTA5` · cost M · domain simulation
- **What:** Ambient vignettes — muggings, breakdowns, crimes-in-progress — spawned near the player for the world to feel eventful.
- **LEDGER mapping:** Do not spawn random spectacle; schedule witnessable secrets instead — authored-template moments embedded in Tier-2 routines (the pharmacist's 23:00 handoff in Ironside, the cop's ex-wife's weekly meeting) that the player can observe to acquire hook material. This is the intake faucet claim #3 currently lacks: M4 lets the player spend hooks, but no roadmap system generates learnable secrets outside conversation. Witnessing reuses the existing witness/schedule code with roles reversed — the player as witness.
- **Why:** Random dice-roll spawns serve no claim and add jank surface (Risk 1). Schedule-anchored witnessable events serve claims #3 and #4 simultaneously, make the offensive half of the secrets economy skill-based (case a routine like a job, per the KCD2 'city as learnable puzzle' lesson), and cost mostly content templates, not systems. The form must change — from spectacle to intelligence-gathering — which is exactly what adapt-heavily means.

### Visible dialogue-check triad (speech/charisma/coercion)  `KCD2` · cost S · domain player-systems
- **What:** Dialogue options display which stat they test and the odds, letting the player pick an approach vector per NPC.
- **LEDGER mapping:** The approach-vector idea already exists as the trait-gated damage-control verbs (bribe/intimidate/discredit/lie-low); the adaptation is making each NPC's susceptibility discoverable through observation, failed attempts, and gossip, recorded as a fallible read in the Ledger UI — never shown as an odds number.
- **Why:** KCD2's real insight — different people yield to different levers — is core to LEDGER, but printing odds would replace reading people with reading UI. Let Sam mention the dock foreman 'only respects money,' let a failed intimidation teach you Ada can't be scared, and let the Ledger record your belief about it. That converts KCD2's stat check into claim-3 knowledge-as-progression and feeds directly into the M4 hooks work.

### Dress-for-the-audience (outfit charisma)  `KCD2` · cost S · domain player-systems
- **What:** Summed clothing stats produce a charisma value that modifies dialogue checks and how classes of NPCs treat you.
- **LEDGER mapping:** Drop the summed number; make outfit context-fit one plausibility input to the existing resolver — a suit makes the 'office job' cover story land Downtown, dock clothes make you unremarkable in The Hook, and expensive clothes without clean income feed section 6.7's 'how does he afford that?' suspicion.
- **Why:** The kernel — clothes are a claim about who you are — is pure claim 2, and LEDGER uniquely punishes overdressing because lifestyle is evidence in the clean/dirty economy. As a charisma scalar it is a stat to grind; as a plausibility/consistency input it is another note the city can compare. The resolver input is nearly free now; the visual half slots at the vertical slice when clothing assets exist.

### Stealth movement system (crouch, vision cones, noise)  `KCD2 / genre-generic` · cost M · domain player-systems
- **What:** A moment-to-moment sneaking sim with visibility, noise, conspicuousness, and takedowns.
- **LEDGER mapping:** LEDGER's stealth is social: the question is never 'am I in the guard's cone' but 'who was scheduled to be on this street and will they talk.' The surviving idea is witness geometry as a learnable puzzle — choosing drop routes and times against NPC schedules the player has learned, with presence/absence and light level deciding whether a witness fact is created and at what confidence.
- **Why:** A literal stealth sim is the biggest scope-creep trap in this domain (risk 1) and drags combat back in via takedowns. But KCD2's 'schedules turn the city into a puzzle' is already the research doc's steal-list item 5 — LEDGER should let players study routines via the Ledger and beat the mill by routing around eyes, strengthening claims 2 and 4 with zero new sim layers until the slice's 3D pass.

### Radial verb wheel  `GTA5` · cost S · domain player-systems
- **What:** A hold-to-open radial menu for fast selection among a small set of always-available actions (the weapon wheel).
- **LEDGER mapping:** Reskin as the social verb wheel: during or after an encounter, hold to pick bribe / lean on / plant doubt / lie low / confess / call in a hook, with unavailable verbs visibly gated by trait or PlayerKnowledge ('you don't know anything to discredit her with — yet').
- **Why:** Pure interface steal — the form (weapons) changes, the ergonomics survive. LEDGER's verbs are its guns, and showing why a verb is greyed out quietly teaches the resolver's inputs (relationship, evidence, plausibility) without printing odds, reinforcing the anti-stat stance rather than eroding it. Build at the slice when input/UX gets its polish pass; the toast-era UI doesn't need it yet.

### Persistent avatar wear (weight, beard, injuries)  `RDR2` · cost M · domain player-systems
- **What:** The avatar's body visibly changes over time from behavior — weight from eating, beard growth, lingering wounds.
- **LEDGER mapping:** Skip the grooming sim; keep a small worn-state vector (exhausted, bruised, limping) set by night activity, perceivable by scheduled contacts: Elias notices you're wrecked at Tuesday lunch, the observation becomes a memory, repeated observations feed reflection into a belief ('he's hiding something') and suspicion.
- **Why:** RDR2 uses the body for immersion; LEDGER should use it for claim 2 — your face is a document the day life reads, and 'office workers don't get black eyes' is a contradiction the mill can carry. Since injuries already persist per section 6.5, exposing them as gossip-able facts is mostly wiring into existing systems; the text-level version could land alongside M4 confrontations, visuals at the slice.

### Perk trees / trainer-taught abilities  `KCD2` · cost M · domain player-systems
- **What:** Level-up perk choices plus trainer NPCs who teach new capabilities for money and XP.
- **LEDGER mapping:** Replace points with people: new player verbs and capacities are taught or enabled by individuals — Rocco teaches proper leaning-on (upgrades intimidate), Lena's books raise laundering capacity, the Fixer sells the discredit playbook, a recruited pharmacist IS the perk that opens a verb.
- **Why:** A perk tree externalizes growth into a menu, but its kernel — capabilities expand over a campaign — is worth keeping, and LEDGER's cast design already contains the answer: Tier-2 mechanical individuality means who you know is the skill tree. Routing every capability gain through a person makes progression serve claims 3 and 5 (a disloyal specialist walking out takes the verb with them) instead of undermining the anti-stat stance.

### Front businesses & property acquisition  `GTA5` · cost M · domain economy-activities
- **What:** Buy businesses and properties that generate passive weekly income plus occasional management missions.
- **LEDGER mapping:** Survives only as laundering capacity: each acquired front (laundromat, chip shop) raises the till-laundering throughput cap the M3 clean/dirty system already meters, and must be staffed by a named Tier-2 individual whose loyalty/fear/competence sets skim rate and exposure profile — no anonymous income tickers.
- **Why:** GTA's passive-income form serves no novelty claim and is the map-painting territory model doc §7 explicitly rejects; but fronts-as-throughput serves claim 5 (the manager is a betrayal vector who knows the books) and extends the §6.7 loop already landing in M3. Build post-slice, when a second front is actually needed — one bar is enough for the week campaign.

### Heist planning & crew selection  `GTA5` · cost L · domain economy-activities
- **What:** Choose an approach, hire crew with skill/cut tradeoffs, run setup missions, execute a multi-stage score.
- **LEDGER mapping:** The score as a planning layer over the existing nightly-drop machinery: a big job needs 2-3 named crew, each pick adds a person who now knows (a fact written to their memory file — a betrayal vector), setup steps are spent hooks (the customs clerk's rota, the pharmacist's key), and execution resolves through the same witness/heat/Monte-Carlo resolution as drops — no bespoke action levels, no combat.
- **Why:** GTA's execution layer needs level design, guns, and vehicles LEDGER deliberately lacks; but the planning layer is the most on-pillar thing in GTA5 — picking crew is literally choosing who holds your secret (claims 3 and 5), and cheap-vs-good crew becomes the §6.5 loyal-vs-competent tension. Post-slice: it's the campaign-scale payoff for M4 hooks plus rackets.

### Side-hustle odd jobs  `GTA5` · cost M · domain economy-activities
- **What:** Repeatable freelance gigs (taxi fares, towing, bounty work) for pocket money.
- **LEDGER mapping:** Survives as alibi gigs: small clean-money jobs whose real product is a corroborable schedule entry — three NPCs saw you couriering in Copper Row at 23:00, and the built contradiction system treats that as alibi evidence when your night self is questioned.
- **Why:** As content filler it serves nothing; as purchasable alibis it serves claim 2 directly — the double life needs a supply of verifiable honest hours, and gigs let the player manufacture them at the cost of drop-window time (P1's one-clock tension). Slot it with the day-job world the roadmap already defers post-slice.

### Business raid & defense events  `GTA5` · cost M · domain economy-activities
- **What:** Owned businesses periodically get attacked or raided, forcing defense responses and resupply.
- **LEDGER mapping:** Raids become social events with provenance: a cop raid on your den fires only because a specific witness's testimony reached Ellis through the mill's hop chain, a rival lean-on targets a specific shopkeeper whose fear flipped — every raid has a findable source the player can trace in the Ledger UI and answer with the existing damage-control verbs.
- **Why:** GTA's random-timer raids violate the no-hard-timers rule (§4) and would read as dice rolls; sourced raids are the payoff of claims 1-2 — the sim already tracks who saw what and who told whom, so consequence events must be legible outputs of it, never RNG. Needs rackets to exist first, so post-slice by dependency.

### Radio-while-driving, remapped to the street-as-radio  `GTA5` · cost M · domain space-traversal
- **What:** GTA fills dead traversal time with characterful ambient audio; LEDGER's equivalent is overheard street talk between NPCs.
- **LEDGER mapping:** The gossip mill already stores per-NPC rumor holdings with confidence and hops. A bark layer reads a nearby Tier-2/3 pair's shared salient facts and voices a one-line exchange from a pre-generated TTS bank per rumor template — so walking past people leaks real mill state, and hearing it can mint a 'learned lead' into PlayerKnowledge exactly the way the Ledger UI wants leads acquired.
- **Why:** Turns traversal downtime into the game's best advertisement for itself: hearing a stranger repeat the rumor you started is claims #2 and #4 made audible, and the research doc notes players love gossip they can see working. The form must change completely (no radio, no music curation) — only the function, characterful ambient audio during movement, survives.

### Interiors everywhere  `KCD2` · cost L · domain space-traversal
- **What:** Nearly every building enterable with no loading doors, and NPC routines that route indoors.
- **LEDGER mapping:** Interiors are where LEDGER's mechanics actually live — witness-free conversation, eavesdropping through doors, and M4's secrets-as-loot acquisition. But only buildings that appear in a Tier-1/2 schedule need to open. Rule: enterable iff someone's schedule routes there; facade otherwise, promoted to real interior if its occupant gets promoted.
- **Why:** 'Everywhere' is exactly the Shadows of Doubt scope creep Risk 1 warns about. 'Wherever the sim routes' captures the mechanical payoff — indoors changes the witness math and heat profile of any act, and doors are eavesdropping affordances feeding claim #3 — using the kit-built interiors §10 already plans, at a fraction of the surface area.

### Fast travel with interruptions / diegetic taxis  `KCD2` · cost M · domain space-traversal
- **What:** KCD2 abstracts long travel on the map but interrupts it with encounters; GTA5 offers taxi skips as the diegetic version.
- **LEDGER mapping:** LEDGER's form, once districts exceed one: a cab that costs clock time plus clean money, goes only to addresses already in PlayerKnowledge, logs the cabbie as a witness in the mill, and whose 'interruptions' are sim-sourced sightings ('Ada saw you cross Copper Row at 1am in the coat') rather than random encounters.
- **Why:** Fast travel that erases time or witnesses would break P1 (time is the contested resource) and claim #2 (movement creates information). This form makes every skip a deliberate information trade — pay to be somewhere fast, accept that a memory record of the trip now exists in somebody's head. Random-encounter interruptions specifically must not survive the port; the no-hard-timers, sim-causes-everything doctrine demands sightings come from real schedule state.

### Diegetic venue/district sound identity (radio idea, re-homed)  `GTA5` · cost M · domain presentation
- **What:** The surviving kernel of GTA's radio: each place has a musical fingerprint — the bar's jukebox, Copper Row market noise, The Strip's club bleed-through.
- **LEDGER mapping:** Identity moves from the player's car to LEDGER's places: each of the seven districts gets an original (not licensed) ambient-music palette, and the bar jukebox becomes a tiny player-expression toy in the home base; music state can shade with campaign state (the bar goes quiet in a high-heat week).
- **Why:** Supports claim 4 (living city at honest scale) as presentation rather than mechanics, which is exactly what the M5 audio pass (already scoped: audio+voice via ElevenLabs) needs to make The Hook feel like a place. Original ambient loops per district are cheap; do the bar + The Hook flavors at slice time, the rest when districts expand. Adapted, not adopted: no stations, no licenses, no vehicle context.

### Phone as diegetic UI  `GTA5` · cost S · domain presentation
- **What:** GTA5 routes menus, contacts, missions, and the internet through an in-fiction smartphone.
- **LEDGER mapping:** The diegetic-container idea survives; the phone must die. LEDGER's container is the title artifact: the uncle's physical ledger book in the bar's back office — the Ledger UI (PlayerKnowledge belief-state, M3.1) rendered as handwritten pages you literally keep two sets of books in. Critically, this is also a fiction ruling: ubiquitous smartphones would make schedule-intersection gossip implausible (why walk a rumor across town?), so the setting should be phone-light by design.
- **Why:** This is the rare presentation decision that defends a novelty claim rather than decorating one: claim 2 depends on information moving through physical co-location, and the doc's fiction currently has no stated position on phones. Rule on it now (S cost — a paragraph in the doc plus art direction for the Ledger UI skin at slice time), because retrofitting a phone-free fiction after the slice ships screenshots is much harder.

### Seasons and festivals  `KCD2` · cost M · domain presentation
- **What:** KCD2's world observes calendar rhythms — feast days and community events that change NPC behavior for a day.
- **LEDGER mapping:** Seasons are meaningless inside a 7-day campaign: reject that half unexamined. The festival kernel is gold, adapted: a one-day Copper Row street festival as an authored conflict beat where every schedule breaks and everyone co-locates — a gossip superspreader event (hop counts spike, corroboration heat compounds, alibis are unverifiable because nobody was where they usually are) and the doc's guaranteed Act II collision (someone from each life in the same crowd).
- **Why:** This is presentation that stress-tests the core system on purpose — claim 2 made spectacular — and it slots into the existing authored-conflict-beats machinery (M3 item 5) rather than needing a new one. Post-slice timing: it needs the mill stable under abnormal co-location density, which the balance lab should Monte-Carlo first, or it becomes a Shadows-of-Doubt jank generator on the game's loudest day.

### Photo mode → evidence camera  `genre-generic` · cost M · domain presentation
- **What:** The now-standard pause-and-compose photo mode for sharing screenshots.
- **LEDGER mapping:** Vanilla photo mode serves zero novelty claims — by the iron rule it's cut. Adapted, the camera becomes a mechanic: photographing an NPC in a compromising place creates a fact object with photographic certainty (no decay, no mutation) that feeds the M4 hooks system as premium leverage — and staged photos feed the doc's existing 'staged evidence' suspicion counterplay. What you can prove becomes a tier above what you merely know.
- **Why:** This turns a marketing checkbox into claim 3 (secrets are loot) infrastructure: hooks currently rest on conversational knowledge, and a non-decaying evidence tier gives the player an offensive verb with real fiction (blackmail photos are the genre's oldest currency). Build it with or just after M4's hooks so it reuses the fact/hook pipeline; a cosmetic share-screenshot mode can ride along post-slice for nearly free once the camera exists.

### Strangers & Freaks micro-arcs  `GTA5` · cost M · domain narrative-encounters
- **What:** Discoverable eccentric side characters with short multi-encounter storylines off the critical path.
- **LEDGER mapping:** Author 3-5 'freak' cards as pre-promoted Tier-2s seeded on schedules in The Hook; each is a 2-3 beat micro-arc built entirely from existing conflict-beat triggers and resolved through existing verbs (learn a secret, spend a hook, damage-control, confess), paying out a mill lead or a hook rather than cash.
- **Why:** GTA5's form is bespoke scripted mission gameplay per freak — exactly the per-feature scripting that fed Shadows of Doubt's jank (Risk 1) and it serves no novelty claim as-is; but the kernel — authored eccentrics who reward attention — is claim #4's promotion pipeline given faces, and conversation-first vignettes cost cards, not systems. Iron rule: never build unique mechanics per stranger.

### Heist planning and crew staffing  `GTA5` · cost L · domain narrative-encounters
- **What:** Big jobs with an approach choice and crew selection where crew quality and cut decisions drive the outcome.
- **LEDGER mapping:** A weekly 'big job' resolved by the sim, not setpiece play: staff it from recruited Tier-2s, compute outcomes from competence/loyalty/fear, and emit the aftermath as witnesses, mill facts, and grievances — the underpaid driver's resentment becomes a betrayal seed.
- **Why:** The GTA5 form is a driving-and-shooting setpiece, and both verbs are deliberately absent from LEDGER, so the form must invert into plan → sim resolution → played aftermath scenes. The decision layer is a perfect claim-#5 (emergent betrayal) engine, but it needs the crew system, which is M6+ territory — build nothing here before post-slice.

## Rejected (with reasons)

### NPC needs simulation (hunger/fatigue/mood drives)  `KCD2` · cost L · domain simulation
- **What:** NPCs carry internal need meters that interrupt or reshape their schedules when hunger, fatigue, or mood demands it.
- **LEDGER mapping:** Nothing in LEDGER consumes a hunger value: the mill, heat corroboration, suspicion, and damage-control verbs all key off position, relationship, and memory — not physiology. Needs would only make gossip-circle attendance stochastic.
- **Why:** Serves none of the five novelty claims — the iron rule cuts it. Worse, it actively harms the design: nondeterministic witness positions break the balance lab's CI-reproducible weeks and destroy the player's ability to plan around learned patterns. LEDGER NPCs should be creatures of habit precisely because habits are what the player exploits. This is textbook Risk 1 (Shadows of Doubt jank via sim layers nobody asked for).

### Wanted-level stars with escalation/evasion  `GTA5` · cost L · domain simulation
- **What:** A real-time 1–5 star meter escalating police aggression, evaded by breaking line of sight and waiting out a cooldown.
- **LEDGER mapping:** No clean mapping: no combat, no vehicles, no real-time chases in v1. Heat is already per-district and witness-driven; the escalation ladder LEDGER needs is the M4 suspicion thresholds (probe → verify → confront); 'evasion' already exists as the lie-low verb.
- **Why:** The star meter is the philosophical opposite of claim #2: GTA police know you're guilty by fiat the instant you act; LEDGER's entire novelty is that the city has to find out, person by person. Adopting it would demand chase and combat content the doc explicitly deferred, and would paper over the memory-backed heat system with an abstract alarm — 'suspicion, not alarms' is the research doc's own steal-list line.

### Honor system (global morality meter)  `RDR2` · cost S · domain simulation
- **What:** A single global honor score, shifted by deeds, that gates story branches and changes prices, greetings, and world reactions everywhere at once.
- **LEDGER mapping:** None. A meter every NPC magically reads violates P3 and claim #1; LEDGER's 'honor' is already emergent — what each individual has heard and come to believe, district by district, with the locally-wrong pockets the mill produces. A global score would also hand the player a ground-truth morality readout, which the Ledger UI is expressly forbidden from being.
- **Why:** The cheapest feature on this list and still wrong: research-mechanics.md's reputation section says single global meters feel gamey while per-individual opinion feels real, and LEDGER's gossip network is named there as 'the best version.' Adopting honor would flatten the game's central differentiator to save UI work it doesn't need saved.

### Profiler-style NPC inspection (scan anyone for backstory)  `genre-generic` · cost S · domain simulation
- **What:** Watch Dogs' canonical overlay: point at any NPC and instantly read their occupation, income, and a secret.
- **LEDGER mapping:** Superficially matches 'no non-characters' and Tier-2 instantiation-on-attention, but it hands out for free the thing LEDGER sells. Secrets must be earned through conversation, observation (witnessable events), and the mill — then tracked as belief in PlayerKnowledge, not served as UI truth.
- **Why:** Claim #3 makes knowledge the loot and the progression; a profiler is a free knowledge faucet that bypasses every acquisition system the game is built on, and it violates 'never ground truth' at the UI layer the roadmap just repaired. The research doc's Watch Dogs Legion lesson applies directly: free information about everyone made players care about no one. The correct LEDGER expression of the profiler fantasy already exists — it is the Ledger UI, populated only by what you actually learned.

### Skill-by-use stat progression  `KCD2 (also GTA5 stats)` · cost M · domain player-systems
- **What:** Core stats (Speech, Strength, stealth; GTA5's driving/shooting) level up automatically through repeated use, gating checks and unlocking perks.
- **LEDGER mapping:** Would bolt a numeric competence layer onto conversation and the damage-control verbs — e.g. a Speech level modifying bribe/intimidate outcomes that are today resolved by relationship, evidence, plausibility, and NPC traits per section 6.4.
- **Why:** Direct violation of the anti-stat stance: section 6.3 defines the skill tree as 'the player's own mental map of who knows what,' and 6.4 says game state, not numbers, decides persuasion. Worse, use-based XP pays the player to spam LLM conversations — inflating the <$0.05/hour cost envelope and manufacturing exactly the slop-dialogue failure mode the research doc warns about. Serves none of the five claims; progression is already PlayerKnowledge + hooks + relationships.

### Lockpicking minigame  `KCD2` · cost M · domain player-systems
- **What:** A dexterity minigame gating entry to locked doors and chests.
- **LEDGER mapping:** Physical access to secret-bearing spaces (a diary in a flat, the rival's back office) could feed secrets-as-loot, but a reflex minigame would be doing the resolving.
- **Why:** Serves no claim as a minigame: LEDGER's locks should be people. Getting into a room is a social problem — get invited, spend a weak hook on the cleaner, borrow a key through a recruit's unique access — which routes the burglary fantasy through claims 3 and 5 instead of around them. A dexterity check that bypasses the social sim is a door out of the game's actual content, and it smuggles in a burglary/loot loop v1 explicitly cut.

### Character special abilities  `GTA5` · cost M · domain player-systems
- **What:** Per-protagonist activatable superpowers (bullet time, driving slow-mo, damage-resist rage) charged by play.
- **LEDGER mapping:** The social equivalent would be a charge-up 'charm mode' or 'read mode' that wins conversations or reveals NPC state on demand, overriding the section 6.4 resolver.
- **Why:** A player-side jailbreak button. Sections 6.4 and 9 are explicit that outcome-bearing moments resolve from game state and the LLM only performs; an activatable social super would override that resolution and delete the reading-people skill with one input. There is also no combat/vehicle substrate for the power fantasy. Serves zero claims; actively damages claims 1 and 2.

### Cores / survival needs  `RDR2` · cost L · domain player-systems
- **What:** Health/stamina/dead-eye cores drain over time and are maintained by eating, sleeping, and grooming.
- **LEDGER mapping:** Would add hunger/sleep meters competing for the P1 time economy alongside the obligations, dates, and drops that already contest each slot.
- **Why:** Survival needs are deliberately absent and the doc is right: P1's pressure must come from meaningful obligations in two lives, not from feeding a meter — chores are false opportunity cost. Cores are also a large tuning/jank surface (risk 1) serving zero claims. The one defensible sliver, sleep as a day boundary, already exists as the Persona-style calendar.

### Honor / global morality meter  `RDR2` · cost S · domain player-systems
- **What:** A single world-visible morality scalar shifting greetings, prices, and endings.
- **LEDGER mapping:** Would sit beside — and fight — the gossip network as a second, authorless source of NPC attitude toward the player.
- **Why:** LEDGER's whole bet (claims 2 and 4, pillar P3) is that reputation is the aggregate of what individuals actually heard — locally wrong by design, one district at a time. A global meter is exactly the gamey shortcut the research doc warns against ('single global meters feel gamey'), and it would leak information the player hasn't earned, violating the Ledger UI's never-ground-truth rule. Cheap to build, expensive to un-teach.

### NPC profiler overlay  `Watch Dogs` · cost M · domain player-systems
- **What:** Point-and-scan instantly reveals any NPC's name, job, income, and a secret.
- **LEDGER mapping:** Would overlay ground-truth NPC data on the crowd, bypassing conversation, observation, and the gossip mill as the routes into PlayerKnowledge.
- **Why:** The exact inverse of the game. The Ledger UI is defined as what you believe the city knows — never ground truth, learned only through play. A profiler is omniscience on a button: it collapses claim 3 (secrets are loot you earn) into free pickups, deletes the reading-people skill, and makes every Tier-3 'character nobody has looked at yet' pre-looked-at. Watch Dogs Legion is already the doc's cautionary tale; its signature verb belongs in the cautionary pile too.

### Stock market with insider manipulation  `GTA5` · cost L · domain economy-activities
- **What:** LCN/BAWSAQ markets the player can move via missions and trade on with foreknowledge.
- **LEDGER mapping:** No plausible mapping: Meridian Bay is seven neighbourhoods of individuals, not an abstract market, and the only LEDGER-native version of 'act on private information before it's public' is already the gossip mill plus hooks.
- **Why:** Fails the §2 iron rule outright — a price sim serves none of the five claims, adds a parallel abstract economy that competes with the person-to-person information economy (P2), and is a textbook Risk-1 scope magnet. The one good idea inside it (profit from foreknowledge) reappears properly as fixing games in your own gambling den.

### Haggling  `KCD2` · cost M · domain economy-activities
- **What:** A price-negotiation minigame on merchant transactions, modified by speech stats and reputation.
- **LEDGER mapping:** Prices in LEDGER (bribe sizes, fence rates, a debtor's terms) should resolve exactly like the built damage-control verbs: trait-and-relationship-gated outcomes decided by game state, performed by the LLM inside the conversation itself.
- **Why:** A second persuasion system beside the conversation engine is the one thing §6.4 forbids — either the minigame can beat the game-state check (players jailbreak prices) or it can't (it's theater). The negotiation content is already covered by 'game state decides, LLM performs'; a dedicated haggle UI adds jank surface (Risk 1) and serves no claim.

### Alchemy/crafting production loops  `KCD2` · cost L · domain economy-activities
- **What:** Hands-on multi-step crafting minigames (brewing, blacksmithing) feeding an item economy.
- **LEDGER mapping:** No mapping: LEDGER has no item economy and no survival needs, and its 'production' (contraband) is deliberately abstracted into drops and rackets resolved by the sim, not benches.
- **Why:** Serves zero claims, drags in inventory/item systems the game has consciously avoided, and is precisely the Shadows-of-Doubt scope spiral Risk 1 names — every crafting bench is a hundred bugs that buy no drama. If contraband production ever needs texture, it should be people texture (a cook with a breaking point, claim 5), not a stirring minigame.

### Horse ownership  `KCD2` · cost XL · domain economy-activities
- **What:** A persistent owned mount with bonding, saddlebag inventory, and mobility upgrades.
- **LEDGER mapping:** None: vehicles are deliberately absent, the slice is one walkable street, and the only surviving sliver — a prized possession that signals wealth — is already covered by §6.7 lifestyle assets.
- **Why:** The doc cut vehicles by name (Risk 1) and the one-district scale makes mobility upgrades meaningless; any mount/vehicle system reopens traversal, pathing, and animation costs that serve no claim. The easiest cut on this list.

### Driving as core traversal  `GTA5` · cost XL · domain space-traversal
- **What:** Player-piloted cars with a traffic simulation, handling model, and collisions as the primary means of crossing the map.
- **LEDGER mapping:** No LEDGER system needs piloted vehicles: schedules, gossip intersections, witnesses, and tails are all pedestrian-scale events. A traffic sim would be a second full simulation competing with the gossip mill for the project's jank budget, and it drags map scale up with it.
- **Why:** Serves none of the five novelty claims; the doc already cut vehicles for v1 and Risk 1 names simulation jank as the project-killer. The one salvageable sliver is a parked car as a §6.7 lifestyle purchase that feeds 'how does he afford that?' suspicion — a prop plus a clean/dirty-economy flag in M3's money system, not a vehicle system.

### GTA5-scale map  `GTA5` · cost XL · domain space-traversal
- **What:** Tens of square kilometers sized around vehicle speeds, with correspondingly sparse per-block density.
- **LEDGER mapping:** LEDGER's core spatial event is a schedule intersection witnessed on foot. GTA-scale spacing makes those intersections statistically invisible to the player and to each other, and it forces the just-rejected vehicles back in to make traversal tolerable.
- **Why:** Claim #4 is honest scale in cast and simulation, not acreage. Seven KCD2-town-sized districts, each crossable in a few minutes on foot, is the correct total footprint; anything larger dilutes the gossip mill's collision rate, starves the witness system, and resurrects Risk 1 (scale seduction is Risk 5 by name).

### Minimap with GPS route painting  `GTA5` · cost S · domain space-traversal
- **What:** A persistent corner minimap with turn-by-turn route lines to the current objective.
- **LEDGER mapping:** It would collapse traversal into line-following, delete the learned-geography layer that schedules-as-puzzle depends on, and violate the game's epistemology: a HUD that always knows where things are contradicts the Ledger UI principle that the player only sees what they have learned — never ground truth.
- **Why:** Cheapness is the trap here — it is an S-cost feature that quietly kills claim #4's legibility and the knowledge-as-progression spine. A diegetic paper district map (no player dot, no routes) covers orientation, and the Ledger UI remains the game's single information surface. 'Never ground truth' should govern navigation exactly as it governs rumors.

### Rooftop and vertical traversal  `GTA5` · cost XL · domain space-traversal
- **What:** Climbing, parkour, rooftop routes, and aerial viewpoints as traversal options (GTA5 hills/helicopters, Watch Dogs rooftops and drones).
- **LEDGER mapping:** LEDGER's simulation is ground-plane: schedules, sightlines, gossip circles, and witness generation all happen at street level. A climbing system adds animation, camera, and navmesh cost, and its main gameplay output — escape routes that bypass people — dodges the witness system instead of engaging it.
- **Why:** Serves no novelty claim, and actively undermines one: 'escape over the roofs' converts the intended social counterplay (bribe, intimidate, discredit, lie low) into physical avoidance, deflating the damage-control verbs that are already built and working. This is the clearest cut in the domain.

### Licensed radio stations / music-as-identity  `GTA5` · cost XL · domain presentation
- **What:** Curated licensed-music radio stations that function as world identity and player self-expression while driving.
- **LEDGER mapping:** No mapping: LEDGER has no vehicles (deliberately absent), so there is no diegetic slot where station-surfing lives, and licensed music attaches to no system — not the gossip mill, not suspicion, not the ledger.
- **Why:** Fails the iron rule outright — serves none of the five novelty claims — and licensing cost/legal overhead is the worst possible spend for a premium indie whose budget must go to LLM inference and the vertical slice. The identity-through-music idea is salvageable, but not in this form (see the venue-music entry).

### Protagonist switching  `GTA5` · cost XL · domain narrative-encounters
- **What:** Multiple playable protagonists you can swap between mid-campaign, each living their own life.
- **LEDGER mapping:** Would fork the object of every NPC memory file ('the player') and break the suspicion/cover model, which assumes one body keeping two stories straight; a second playable body is a free alibi machine.
- **Why:** It dissolves novelty claim #2 — LEDGER is one person balancing two accounts, and switching trivializes contradiction-driven suspicion. The switching camera's real payoff (the world lives while you're away) is already delivered better by schedules, the gossip mill, and the end-of-day ledger summary.

### Checkpoint retry on mission failure  `GTA5` · cost S · domain narrative-encounters
- **What:** Failed missions restart from a checkpoint with world state rolled back.
- **LEDGER mapping:** Incompatible with P5 ('no quest resets; the city's state is the save file'): a botched drop must be absorbed as witnesses, heat, and mill facts, with the week's exposure fuse and win/lose as the only reset boundary.
- **Why:** Cheap to build and poison to the premise: if failure rolls back, NPC memories lie and claim #1 collapses. LEDGER's whole bet is that a bad night becomes next week's rumor, not a loading screen — and the week-restart loop already gives players a fair reset at exactly the right granularity.
