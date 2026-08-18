# LEDGER — roadmap

> **STATUS — LIVE, verified 2026-08-04.** The plan and the build state. If this
> and another doc disagree, this wins. If it is wrong, that is a bug in this file.

**The plan lives here.** Chronology, post-mortems and superseded plans are in
`roadmap-history.md`. Nobody should have to open a second document to find out
what happens next.

---

## The screen

| | | |
|---|---|---|
| **now** | M17 — the game looks and sounds like itself | 17.4/17.6/17.9 closed · 17.7 part done · **17.1 and 17.1b CLOSED**: eight real bodies, `bodyChoices=10`, textures extracted, foot IK on both feet, the twelve NEAREST people wearing them. **What is open is SAMENESS, not absence** — ten models dress forty-three named people, so two on screen always share a face (`fourteen people, eight faces`). Breadth, cadence, loop phase and head scale vary and are confirmed; the limp IS wired and live (`Rig.Limp` drives the dip every solve; three walkers limping in the 8520994 run, amplitude 0.05 — small enough to read as subtle rather than absent, retune only off a still that says otherwise). The genuinely open half of sameness is the MODEL COUNT, which is a purchase decision, not code. The wardrobe wash is fixed and measured (near-white 39% predicted to 7.7% of 4,904 washes) with a per-material albedo anchor. The night skyline is occupancy-lit (`windowsLit=1747` of 2447). Full account in `roadmap-history.md` |
| **also now** | M18 — the second life | family verified running · **the companion is CLOSED, 4 Aug**: she was never too slow, she had no idea where the player WAS — a walker learns the transform from one proximity sweep and both the escort's target and its catch-up speed were guarded on having it, so falling behind is what stopped her following. Bound at recruit time and picked by proximity now: `companionAtRecruit=9.2` against 23.8, `companionDist=4.2` at the deed, `deedWaitedDays=0` · vice and lifestyle deferred |
| **next** | M19 — the people are thinking | inputs judged and fixed · **input parity done: a conversation can be carried without typing** · **outputs now judged too: the dialogue benchmark is a measured 78, no longer the word `unjudged`** |
| | M20 — the town you learn | **days now differ from each other** · **the district cut is OFF — filling the city beats shrinking it, measured** · the cast tiering is what remains |
| | M21 — the two ledgers | **started 4 Aug, and law-as-a-tool is now a complete verb.** An accusation is weighed by what the street will tell a detective rather than by whether it is true; making one marks you; and a charge that sticks points the detective at somebody else for four days before she comes back with exactly what she had. Allegiance shifts: pledge, refuse, walk out — three methods that existed, were tested, and had no callers. **AND 5 AUG: THE LAW COULD NEVER ACTUALLY ESCALATE, FOR THE WHOLE PROJECT.** `Killing.TopicKey` built its mill key by hand while `Fact` lowercases, so every victim — all capitalised — was filed under one key and looked up under another. `LiveWitnesses` returned nobody in every run ever kept, so the inquiry could not pass Procedure, the paper never named the player, the redirect had nothing to relieve, and `CoatHost.Arrested` still has no caller. Fixed, probed against real Core and guarded by a CoreTest tested both ways — so the verb was complete and the CHAIN it drives was dead, which reads identically from inside Core. What remains is the surface a player accuses somebody FROM, empire growth, notoriety and the competence axis |
| | M22 — the shape of a playthrough | onboarding, pacing, replayability, succession |
| | M23 — firearms | M16 phase 5, deliberately last |
| | M24 — ship | performance, platforms, controller, QA, licences, packaging |
| **shipped** | M0–M16, Acts I–III, the perception and consequence engine | **with one correction, 4 Aug: M16's fighting does not run.** The consequence half is real and gated; the exchange of blows is Core-only and nothing calls it — see M16 below |
| **waiting on Jafar** | nothing | The Mixamo fetch is DONE — he ran it 4 Aug and eight bodies landed. **And the claim this row carried was wrong and the build said so: it read "because those models arrive TEXTURED, the wardrobe leaves them alone entirely", and `bodyKeptMats=0` with thirty materials and zero textures says they do not.** Mixamo embeds its textures INSIDE the FBX and Unity extracts nothing on its own, so "textured" was true of the file and false of the import — a distinction nothing here had ever had to make. No purchase is pending and nothing is blocked on him |

**The strategy every milestone below is judged against.**

**Get as close as possible to KCD2's immersion with the means we have, and use
LLM characters to beat it in the one place authored games cannot compete: the
people are THINKING, not triggering.**

Every NPC reaction in KCD2 is authored, and outside what the writer anticipated
there is nothing. Here, what a person thinks of you is computed from what they
saw or were told, then spoken in character by a model — so they can be WRONG
about you, be argued with, and hold a grudge over a thing that never happened.
The consequence engine is not wasted by this: it stops being the product and
becomes the reason the conversations matter.

**Worse at, and at peace with it:** visual fidelity, animation, traversal scale,
driving, content volume, combat depth. **Never worse at:** characters, dialogue,
whether the town feels inhabited, whether anything you do is remembered.

Scores per dimension are in `agency-model.md`, re-scored against the code on
2026-07-31.

---

## M16 — PERCEPTION, WEAPONS AND VIOLENCE *(shipped, with one correction)*

Phases 1–4 shipped and gated; phase 5 is firearms and is M23. The §4.7 gate
holds — *the same killing leaves no witness in an empty alley, several in a
market, and none in the back room of a busy pub*.

**"Shipped" is true of the CONSEQUENCE half and not of the fighting**, found
2026-08-04 by reading the code rather than this table: violence is staged as an
event, everything downstream runs, and there is no exchange of blows anywhere.
Fixing it needs a done-condition that measures a FIGHT. **The risk it exposed
set the pace of everything below, and 5 Aug removed it:** the Game layer now
compiles here in six seconds (`tools/gamecheck.py`), so a wiring error costs a
keystroke rather than a round trip. Accounts in `roadmap-history.md`.

---

## M17 — THE GAME LOOKS AND SOUNDS LIKE ITSELF

**Why first.** A player judges a game in ninety seconds and none of the depth
below is visible in them. Almost nothing here is new design.

| | what | state | risk |
|---|---|---|---|
| 17.1 | **Integrate the Mixamo bodies** | **CLOSED 2026-08-03 except the mesh.** The figure stands, the arms hang, and forty-one imported clips are being played by a locomotion blend tree. It took eight builds and two faults that were both ours, not Mixamo's, and it was closed by LOOKING at `review_day1_noon.jpg` after a gate blind to the fault had certified it once already. Full account in `roadmap-history.md`. What remains is that the body is a grey preview mannequin — that is 17.1b | **arms open; upside-down closed** |
| 17.1b | **Bodies and faces for EVERYONE** | **RUNNING 2026-08-04, confirmed by build: `walkerBodies=12`, `bodyKeptMats=1`, textures extracted, foot IK driving both feet.** Three things had to be true and now are: eight real Mixamo bodies are on disk (`bodyChoices=10`, all models carrying valid human avatars); their textures are extracted and reaching the mesh (`bodyKeptMats` non-zero, and the noon still shows a figure with skin, hair and clothes rather than a flat silhouette); and the named cast is attached to them. **`RealBody.TryAttach` had exactly ONE caller — `PlayerController` — so the player was a person and all sixty-seven walkers were articulated boxes.** The anonymous crowd keeps mannequins by choice: they are never spoken to and read fine at the distance you see them, and bounding it to the cast means the number of skinned bodies is something somebody chose. Gait bias, bad leg and idle phase come across from `Physique.For`, the same deterministic source `Mannequin` uses, so the cast does not walk in unison — the one way real bodies could have read as worse than the boxes. **`walkerBodies` came back non-zero, so the wiring is closed and what remains is cost.** Forty-four bodies is 1,037,694 skinned vertices against 16,338 for one — about 23k a body, which is what a Mixamo character costs, so it is real work rather than a GPU-less runner's noise. Bounded at twelve; and since 4 Aug the twelve are chosen every second by distance to the player, using `Population`'s own near band rather than a second definition of near, so the person in front of you is the one wearing a face. Full account in `roadmap-history.md`. **2026-08-04 LATE — three faults the medians could not see.** `armWidest=54.5` beside `armCrowdWidest=53.5` — taking the player out barely moves it — and printed off `Rig.ArmSwing`, a normal stride puts the forearm at 48.3 degrees from vertical at 1.4 m/s and 55.1 at 2.0. **So the figures that looked like scarecrows in two night stills are people walking with bent elbows, and the T-pose hypothesis is retracted**; `animBodies=6 animDriven=6 animAdvancing=6` says nothing is frozen in a bind pose either. What those frames actually show is the mob, and overlapping bodies at 1280x720 read as splayed limbs. `crowdHuddleWorst=41` — forty-one people within two metres of one person — while `crowdGapMedian=0.44` calls the street comfortable; the ring they stand on was a fixed 0.8m, giving each of them twelve centimetres of arc, and is packing-derived now. And the eight pieces of clutter in the road all belong to registered PLACES, which are set back from an authored map coordinate while block buildings are inset from a kerb — two rules for one idea, and only one of them knows where the road is. History in `roadmap-history.md` | **wired; risk is now cost, not absence** |
| 17.2 | **Generate the cast voices** — clones from the 19 reference clips | cast and consent-approved; **19 reference clips picked**. Blocked on a SCOPE decision, not on tooling — see below | **high, and it is scheduling** |
| 17.3 | **Cast the 15 named characters with no voice** | Ossei among them, and he is an Act III condition | low |
| 17.4 | **Bark curation** — the bark bank, read line by line | **DONE 2026-07-31** (884ce9a). 2,604 lines read by family. Everything mechanical was already clean; the two finds were things no check could see — `exchange.tell.certain` had six of fourteen openers starting the same way, and six `ambient.pair.ordinary` replies each answered one specific opener while `Answer()` picks them independently. Both now gated in `BarkGen` at a threshold read off the printed series | closed |
| 17.5 | **Non-verbal foley** — grunts, pain, exertion | decided: CC0 through the voice pipeline | low |
| 17.6 | **Surfaces** — a real texture set for the twelve logical surfaces `AssetLibrary` already asks for | **DONE 2026-08-01.** 12 CC0 albedos from ambientCG committed, attributed, `pack_check` green. Verified in a render: the noir tint neutralises the source saturation | closed |
| 17.7 | **Props, buildings and vehicles** — authored geometry instead of primitives | **PART DONE.** Vehicles: per-kind silhouettes, wheels at real proportions, density 28. "Buildings are cubes" was wrong both ways — they are box ASSEMBLIES (body, roof, setback tier, rooftop tank). **2026-08-01:** windows split from one band per floor into panes with piers, ground floor deliberately one wide shopfront light, gated to near-core buildings on the ramp the facades already use; overhead cables strung (`Dressing.CableAt`, off the reach ledger). **2026-08-04, CONFIRMED BY BUILD: the night skyline stopped being one colour** — `windowsLit=1747` of 2447 against a measured `windowsHome=0.70`, and the still shows lit and dark windows on the same floor where there was a wall of identical cream. Shopfronts then became the loudest thing left, so they follow OPENING HOURS rather than occupancy, about a third keeping late hours. Every window in seven districts was lit by a single call writing one emissive to all of them, which is why the night still reads as a wall of identical cream rectangles. It is occupancy now, not jitter: `Core/Occupancy` asks the real population whether each person is at work, out for the evening, or in, from the work hours and circle the generator already gave them — so a dark window is information rather than decoration, and `windowsLit/windowsTotal/windowsHome` print the cause beside the effect. **And bus stops and cab ranks exist** — `transit=8`, against a prediction of 6 to 8 written before the dispatch. The bus has been routed, dwelling and drawn since it was written and nothing marked where it stopped, so an eight-second halt at a bare corner read as a bug — two reach-ledger entries that both described missing behaviour when the gap was signage. What IS open: the back of a block gets bins and drainpipes but no geometry of its own | medium — volume, not difficulty |
| 17.8 | **Weapons and held objects** — the player's hands are empty | shipped: `HeldObject` draws from the hand, silhouette derived from reach | low |
| 17.9 | **A font that ships, and icons** | **DONE 2026-08-01.** PT Sans (SIL OFL) committed with its licence beside it; `fontless=0` every run | closed |

**17.6–17.9 were found by an audit, not by the plan** — this file was derived
from the work queue rather than from a definition of done, so it was silent
about nine whole categories. Cause in `completeness-audit-2026-07-31.md`. **The
2026-08-18 audit is the same shape aimed at the design doc** and found five more
(romance, job tracks, smuggling, interiors, the session-hook guarantee), now
placed in M18/M20/M21/M22.

§4 chose stylised noir for the reason that still holds — a game about what people
think they saw should look subjective and half-obscured, and weather and fog cut
draw distance, hide low-detail geometry and make mood at once.

**The project can see itself.** Every Windows build commits four stills, a clip
contact sheet and a `verdict.txt` to `game-design/sim-shots/`. **Judge M17 from
the stills, not from the source** — and read all four before reading any gate.

**Done when.** A sim screenshot shows a skinned body walking with foot IK, and
`bodiesOk` gates on the Avatar being bound rather than on `Mannequin` boxes;
every named character speaks in their cast voice; the bark bank has been read
end to end; effort sounds exist for Phase 3's fight.

**Depends on.** Nothing. All five can start today.

---

## M18 — THE SECOND LIFE

**Why it matters more than its scores suggest.** A belief network is only
frightening if the people in it are people you would miss. Scores and the full
argument: `agency-model.md`.

**What is in it.**
- **Home as a place that reacts.** The rooms above the pub change with money,
  heat and who has been in them. A base that reads your week back to you.
- **Companionship.** **DONE 2026-08-01, and closed 4 Aug** — she is a witness by
  standing there, with no companion branch in the perception path. Account and
  the following-distance fault in `roadmap-history.md`.
- **Family and dependents.** **DONE 2026-08-01.** A dependent below `TalkFreely`
  joins the mill as an ordinary agent whose loyalty is their bond, so the people
  closest to you become the people most willing to talk.
- **Vice.** A cost that is not money and not heat. **Not started.**
- **Lifestyle.** **Not started**, and it needs BUILDING rather than wiring —
  `Core/Wardrobe` is the only real starting point. (The substrate this entry
  once claimed turned out to be weapons concealment and street furniture;
  account in `roadmap-history.md`.)
- **Romance. NOT STARTED AND, UNTIL 2026-08-18, IN NO MILESTONE AT ALL** — found
  by auditing `design-doc.md` against this file. §6.6 names "friendship and
  romance", and §2's flagship illustration of the second novelty claim is *"your
  girlfriend can catch your alibi from your coworker"*: the clearest sentence
  anyone has written about why this game is worth making depends on a system
  that does not exist. What exists is friendship-shaped — every few days the
  person who thinks best of you asks for an evening. The propagation underneath
  is real and running; what is missing is the relationship that makes catching
  an alibi hurt. **Done when** a partner holds a belief about the player that
  came from a third party, and the endings matrix separates a run where it was
  managed from one where it was not. **Depends on** nothing. **Risk: this may
  deserve to be a milestone rather than a bullet**, and that is Jafar's call.
- **The other day-job tracks.** §6.6 offers "bar, courier, office"; `Core/DayJob`
  has no track concept — it is the courier round, singular, so a choice the doc
  offers on the player's first morning has never existed. **Done when** two
  tracks run end to end and each shows a different social graph and cover.

**Done when.** A run where the player never goes home is measurably worse in
the endings matrix than one where they do — and the difference comes from
relationships rather than from a stat.

**Depends on.** M17 for anybody to look like a person while doing it.

---

## M19 — THE PEOPLE ARE THINKING *(next, and the centrepiece)*

**THE WRITING HAS BEEN JUDGED AND IT IS GOOD — the project's largest unexamined
risk is retired.** Forty real exchanges through the live engine, read line by
line on 3 August, scoring **78**: four voices stay four voices with the name
tags removed, they catch a checkable lie for reasons grounded in who they are,
and jailbreaks land in fiction rather than as refusals. Account and transcript
in `roadmap-history.md` and `writing-check-free.md`.

- **CONFIRMED 5 AUGUST, and the re-read found worse than either closure.** Both original faults are closed. **But all four voices answered "what's the mood" with the single word "Quiet.", in both paid runs, eight for eight** — every reply good alone, so it passed two readings and both checks, because the fault lives BETWEEN replies and nothing looked there. Each card now has a `What You Notice First` so they answer from different places. **And the cast was inventing people** — Frank Doyle's two-year tab, old Duffy's chair, Mrs Bartholomew, Vic, Ray, none of whom exist — the law breaking at its most expensive point, since a model that mints a person with a history has taken over deciding. Names are now limited to what the prompt already contains. **Checking is free from here**: `ConvoProbe --dump-prompts` needs no API call. Transcript and full account in `writing-check-free.md`.
- Then make it good: voice held under pressure, memory of what you did.
- **Negotiation as the empire's verb — THE NEXT THING, and it is rule 6.** Recruiting, bribing, threatening, being talked round as scenes rather than menu picks; no authored tree affords it at scale. `Core/Negotiation` is complete and tested — five levers, resistance, resentment, novelty decay, a walk-out, and a `LoyaltyCost` charged after the scene whether you won or lost, so a negotiation can be won and still be a mistake. **It has NO Game-layer caller, so not one line has ever run** — the same shape the law layer had until yesterday, and indistinguishable from working when read from inside Core.
- NPCs who are **wrong about you** and can be argued with.

**INPUT PARITY — a rule, checked, not promised.** Every conversational action is
reachable with a stick and two buttons. Typing and dictation stay first-class
alternatives, never removed and never required. The check: no dialogue state is
reachable ONLY by text.

The fix is to stop the model PARSING and start it OFFERING: it writes four
things Tom could say right now, from live state, and you pick one. `IntentRouter`
exists and is tested; the change is that it maps stick input to the same intent,
plus an approach radial (press, lie, offer, soften). *(This inverts a 2026-07-26
decision still in the code — `DialogueUI` reads "clicking one says it; typing
stays the game".)*

**A side effect worth having: the chips ARE the odds display.** An option
reading *"ask him why he was on Quay Street"* only appears if you know he was.
That answers `agency-model`'s visible-odds row (scored 0, target 50) without a
percentage anywhere on screen — the player sees what they hold by seeing what
they can say.

**And the couch problem is reading, not typing** — nobody wants three paragraphs
at two metres from a television, which makes 17.2's voices load-bearing rather
than polish.

**Done when.** A conversation with somebody who half-saw you do something is
worth having twice, their opinion changed because of what you said rather than
because a flag flipped, and the whole exchange was played on a controller.

**Depends on.** M17 for anybody to have a face while doing it.

---

## M20 — THE TOWN YOU LEARN

**THE DISTRICT CUT IS OFF — filling the city beats shrinking it, and this
section said the opposite until 2026-08-18.** It read "Keep the Hook, Copper Row
and Ironside; cut four" while the screen table at the top of this same file
said the cut was off, measured. Two halves of one document giving opposite
instructions is the exact failure `roadmap.md` exists to prevent, and it stood
for two weeks.

What the measurement still says, and it is why the question was live:
`ledger/Recurrence` counts how many people an ordinary resident crosses in a
day — **6.5 at seven districts, 12.1 at two, 12.9 at three**, 32% more at face
range. Concentration nearly doubles recurrence, which is the mechanism by which
a place becomes familiar. **The answer was to raise density rather than cut
area**, which buys the same recurrence without throwing away Ironside — the
design's own "warehouses, logistics, places without witnesses", and its best
unobserved location.

- **Days that differ from each other.** `OutdoorsAt` and `OutdoorPosition` take
  an hour and reduce it mod 24 — there is no day parameter anywhere in the
  routine model, so every Tuesday is every Saturday and recurrence is total and
  unearned. Found by the tool above while measuring something else.
- **Tier the cast**, because recognition and relationship have different
  cognitive costs: a named few with faces, voices and memory; a recognisable
  many with a name and a routine; a crowd that witnesses and fills a market.
  Dunbar's layers (~5 / ~15 / ~50 / ~150) are the scale.
- **Population is a dial, not a cliff, and it sits at 700.** 350 gives 5.1
  crossings a day, 700 gives 12.9, 1400 gives 21.9, 2800 gives 38.9 — roughly
  linear, so the crowd tier is sized against a frame budget rather than opinion.
  (`design-doc.md` claimed 3000 until 2026-08-18; the build has never run it.)
- Routines legible enough that following somebody for an afternoon holds up.

**Constraint to respect: 14 character models, and it is a FETCH, not a purchase.**
This read "44 models ... until somebody buys more" — wrong twice: 44 was the
animation CLIP count, and every body came free. Sameness is the real cap: 14
models dress 43 named people, so two on screen always share a face.

- **Interiors beyond the pub. NOT STARTED AND, UNTIL 2026-08-18, IN NO MILESTONE.**
  `design-doc.md` §18 has carried "every other door is a threshold, not a room"
  for weeks with nothing owning it. It belongs here rather than in the art
  milestone: a room you can enter is what makes a routine followable and a
  regular recognisable, which is this milestone's whole done-condition. **Done
  when** three interiors a routine actually visits can be entered, and somebody
  can be found inside one by following them. Kit-built, per §12's risk note.

**Done when.** You recognise a regular by their coat before you can see their
face, and you are right.

---

## M21 — THE TWO LEDGERS

You inherit a pub, two workers and your father's debts. The day side is a
licence, a till and wages. The night side pays better than the bar ever will.
**The game is named for the two books that do not balance** — and the build
already tracks them apart: one run closed with £0 clean against £354 dirty,
which is the whole story in two numbers.

**Everything you gain is a person who knows something about you.** A `CrewMember`
IS a gossip agent, with their own memory, loyalty and mouth. Recruiting
manufactures a witness with a wage. Expansion and exposure are the same system
read from either end — and as of 4 Aug the street finally hears about a poach.

| dimension | now | target | what is missing |
|---|---|---|---|
| Faction politics / allegiance | 45 | 75 | **allegiance shifts as of 4 Aug.** `PledgeTo` and `BreakWith` were written, tested and unwired — three methods were the whole gap. Both now run through `GameController` and broadcast to the street, and a poach finally reaches the gossip layer instead of moving two numbers in silence. Still missing: a place in the UI for the player to choose it, and standing that moves from anything other than the summit |
| **Law as a tool** | 40 | 70 | **the verb exists as of 4 Aug.** `Core/Informing` weighs an accusation against what the street would tell a detective, on the same magistrate's bar Act III uses, and returns the mark that goes on the player for having informed. `Core/Claims` turns a typed alibi into a `Fact`, so `ProcessClaim` and `PlayerClaims` run for the first time. **Redirecting an inquiry landed too (4 Aug).** `HomicideBook.PointAt` stores who the law is asking about instead of you; the relief comes off the NAMED half of the pressure only, never off the bodies, so a charge that sticks walks a manhunt back to an investigation and can never walk it to nothing — 1.00 to 0.73, then 0.80, 0.87, 0.93 and back to 1.00 over four days. `EvidenceHost.InquiryOf` was a second implementation of the same arithmetic and now delegates. **AND THE ROW'S "still missing" WAS UNDERSTATED, corrected 4 Aug late by two new instruments agreeing.** It said the gap was the surface a player names somebody FROM. The gap is the whole chain into the law. `GameController.RecordKilling` is the only path into `HomicideBook` and has NO CALLERS, so the register is empty in every run, `Pressure` is zero, `Stage` is `None`, and `inquiry=None` in all 131 kept verdicts — with `pressNamed=0` and `redirectRelief=0.00` beside it as the same finding wearing other names. `EvidenceHost.WhoWouldTalk` — who among the witnesses would actually go to the police — has no callers either. So Core holds a complete, tested law layer and the Game layer calls none of it: nothing records a body, nothing asks who would talk, no inquiry ever rises, and every stage above `Procedure` has never executed once. `tools/lint-unreached.py` exists because `ReachCheck` covers only CORE APIs and this was all on the other side. Still missing: the chain, and then the surface |
| Public notoriety | 60 | 60 | **its own number as of 4 Aug, and two sources.** `AccessHost` fed the door gates `CurrentHeat` — one variable under two names, so a door opened because the police lost interest rather than because nobody had heard of you. Notoriety now accumulates on its own and decays proportionally at a tenth of heat's rate, so six weeks of quiet still leaves a killer halfway known. It rises on a witnessed act of violence and on informing on somebody, weighted by whether it stuck and doubled if anybody saw you go in. **The accumulation had to change with the second source**: taking a maximum was harmless while violence was the only caller and would have meant one killing silencing every later source for ever — built, wired and invisible. **AND IT CHANGES WHAT THE PLAYER CAN DO, proven end to end on 4 Aug rather than assumed.** The two notoriety-keyed places in the world are tried twice each every run — at the value the run actually built and again at zero — because a single reading cannot tell "notoriety opened this" from "this was open to anybody", and both doors have other keys. The result: the loft above the laundry, the quiet room that closes as you become somebody, is SHUT at 0.87 and would be open at nothing. The repair yard, which only opens to somebody the street talks about, is open either way — its other keys carried it. One door of two, and that is the honest score. **AND THE PRESS LANDED 4 Aug**, which was the other named gap: every other channel in this game moves person to person and decays, so a killing in an empty alley was known to nobody for ever and being known could only be bought with witnesses. The paper is the one channel with no hops — but it does not know secrets (a story carries your name only when somebody would already say it to a detective, otherwise it prints the act and not the name, and an unnamed story makes you no better known at all), it is not an eyewitness (a reader believes less, on the number the phone layer already uses), and most things are not news. Still missing: press, and a surface the player informs FROM |
| Character competence | 10 | 40 | crew have it; the player has none, and `Harm` only ever subtracts. **The third brick landed 4 Aug and is RUNNING (`e51c681`): `exposureYours=30 exposureTheirs=2`, weights 10.23 against 0.76, and the ledger screen says "Most of what the street has on you, it got from seeing you — your people have cost you little."** It is not the face-count the design note reads like: the street files a runner's round against the PLAYER by design, so what differs is CONFIDENCE — a racket rumour lands at `0.45 + 0.35 * (1 - competence)`, meaning a capable runner leaves a weak link and a clumsy one a strong one. That mechanic had run for weeks with nobody able to see it. **"None of the three yet CHANGES anything the player can do" stopped being true on 4 Aug** — see the notoriety row: a door in the world is shut against the player because of what the street knows, and the same door would be open to a nobody. **AND THE FIRST OF THE TWO CLOSES SOMETHING AS OF 4 Aug, wired and gated, awaiting its run.** `MissedSinceLastDelivery` had one consumer — a line on the ledger screen — so a player could read it and the world could not. `Core/Reliability` turns it into talk: two misses and the day circle starts saying it, four and it is a reputation, a delivery clears it, and the confidence floor is the same 0.45 the racket rumour uses so a first mention of unreliability is worth what a first mention of anything is. **Social rather than economic on purpose** — making the outfit stop posting drops would turn the already-struggling `jobRan` gate permanently red, which is a guard blocking the case it exists to check. It is also the honest precondition for a later economic consequence: the work should dry up because word got round, not because a counter crossed a line. **AND THE SECOND BRICK WAS NEVER DEAD — this row said so and I repeated it three minutes after writing the first half of this sentence.** `DaysSkimmed` is not a display counter: skimming takes 0.05 of a runner's loyalty every payday, writes them a memory every third day (*"Light again. The pays the same every day; my envelope doesn't. I keep my own book on this."*), and past a breaking point a need-route runner QUITS — the round dies, the racket unestablishes, and the street hears him go. That is a full consequence chain and it has been running. The row's claim that "neither yet closes anything" was true of missed nights and false of this, and checking took one grep. **AND THE LIMP IS ON THE STREET AT LAST, 4 Aug late.** `CharacterRig.Capability` drives an authored asymmetry with five tests and a matching footstep rhythm, and it had exactly one writer — `PlayerController` — so every walker sat at the default and nobody in this city had ever limped, whatever was done to them. Wired through the population pass, and the run proves the condition exists rather than assuming it: `limpNames=[Filip,Hana,June,Rocco,Sam] limpNow=3 limpOf=50 limpWorst=0.05`. It also found the two limps disagreeing by a factor of sixteen on one capability — the sound shortened Sam's bad step by 43cm and the pose by 2.6cm — because one scalar drove both hip and knee, which move the foot in opposite directions, and because the stance scale alternated by PHASE while being applied to one LEG. Both fixed; the size is `Gait.MaxAsymmetry`, the audio's own, so there is one asymmetry constant in the game. What IS still missing is the PLAYER's side: `Harm` only subtracts, and there is nothing the player gets better at |

**Law as a tool was the one to build first, and the spine of it is in** (4 Aug):
an accusation is weighed by what people will say to a detective rather than by
whether it is true, and the mark for informing is a return value no caller can
skip. The rest still stands — the game has an excise audit, a detective with a
case and police escalation on a body, and being able to *point* those at
somebody turns its central threat into a verb the player can hold, reusing the
information layer rather than adding one.

**Growth is the competence axis, and there is NO EGO METER.** A number the
player tops up kills the story the mechanic exists to tell. Instead it is a run
of individually reasonable decisions that compound — the bigger cut, the job
done yourself, the sixth night missed — every one of which the game already
punishes. What it owes the player is the ability to SEE the shape forming:
M19's chips, and the ledger's DOUBT section as of 4 August.

**The empire grows in DEPTH, not area.** Four businesses on a street where you
know every face beats twelve across a map.

**Two of the five rackets do not exist, and nobody had planned them** — found
2026-08-18 by auditing `design-doc.md` against this file. §6.5 names protection,
smuggling, gambling, fencing and debt-collection; `EmpireSetup` builds
collection, protection and fencing. **Smuggling is the conspicuous one**: this
is a port town whose Act III threat is Customs and Excise, and there is nothing
to be caught smuggling. It is also the racket with the most natural exposure
profile — a cargo, a shed, an hour, a person who signs — and the one that would
make the existing audit mechanic bite. **Done when** a smuggling round runs on
the same `Racket` substrate as the other three and an Act III audit can land on
its paperwork. Gambling is the weaker of the two and can wait behind it.

**The rival is a person, not a stage counter — and she rings you as of 4 August**:
being unreachable is a position you can take and the first thing in the game
that charges for it. **Still missing: the third answer** — picking up and saying
no needs a prompt, which belongs with the UI. Account in `roadmap-history.md`.

**Done when.** A player can end a rival without touching them — allegiance
moves, a charge lands, their access closes because of what the street believes —
and a player who overreached can name the night it became inevitable.

**Depends on.** M16 for the observation model, M19 for the conversations the
negotiations happen in.

---

## M22 — THE SHAPE OF A PLAYTHROUGH

Not a systems milestone. The one that decides the review score, and the one a
systems-first project is most likely to skip.

- **Onboarding.** The first fifteen minutes have to teach a belief network, an
  economy, a schedule and a double life. They currently teach none of it, and
  every system above is invisible to somebody who bounces in minute three.
- **Pacing and difficulty.** Seven authored days, then an open city, then an
  audit. Whether that curve holds is unmeasured — the balance lab tests
  outcomes, not the felt shape of a week.
- **Replayability.** Five endings exist; whether a *second run feels different*
  is the untested claim. The Director and the gossip mill are the two systems
  that could make it true, if the Director is authoring real variety.
- **Legacy & succession, 40 → 70.** Succession exists only at the ending; a
  hand-over that matters mid-game is what turns a campaign into a dynasty.
- **The session-hook guarantee. NOT BUILT AND, UNTIL 2026-08-18, IN NO
  MILESTONE.** `design-doc.md` §4 says the player's "one more day" comes from
  *"an unresolved thread every evening — **the sim guarantees one**"*. Nothing
  guarantees it. It is the document's only explicit retention claim, and having
  no owner made it read as a solved problem in the one section anyone checks
  for whether the game is sticky. It is also the cheapest item here: every
  input exists (a rumour in flight, a recruit wavering, an evening promised, a
  debt due) and the end-of-day summary is already the right surface. **Done
  when** no closed day in a full run ends with nothing outstanding, and the
  summary NAMES the thread rather than counting it.

**Done when.** Two full playthroughs by somebody who has not read the design
docs, with notes, and a measured difference between them.

**Depends on.** Everything above, because it is the milestone that judges them.

---

## M23 — FIREARMS

M16 phase 5, held back on purpose. A gun in a game about being watched is a
different game, and it should arrive when everything that observes it is
finished: the ladder, the delivery window, provenance, disposal, notoriety.

---

## M24 — SHIP

Performance budgets held under load; **macOS builds green and packages, and has
never been LAUNCHED by a person** (the workflow proves the app exists and names
its architecture; only real hardware can prove it runs — Jafar's machine is an
M-series Air, so it is native arm64 rather than Rosetta); controller support (28
`Input.*` calls to move onto an action map — contained, not a rewrite, and zero
`OnGUI` so the focus model already applies); accessibility beyond the caption
channel; and `qa-matrix.md` run for real by a person rather than by a harness.

**And the four things that turn a build into something a person installs**,
added by an audit because none of them had an owner:

| | what | why it is not optional |
|---|---|---|
| 22.1 | **Credits, attribution and a licence file** | **VCTK is CC BY 4.0 — attribution is required.** Mixamo carries its own terms, CC0 packs usually request it. There is no `LICENSE`, no credits screen and no attribution file in the project |
| 22.2 | **A localisation decision, recorded** | there is no localisation infrastructure and every player-facing string is a C# literal. English-only is a legitimate answer; never having decided is not |
| 22.3 | **Packaging** | no app icon, no splash, no store metadata. CI makes a build artefact and nothing turns it into an install |
| 22.4 | **Fonts that ship with the game** | `UiTheme` borrows Segoe UI from the OS, which is Microsoft-licensed and not redistributable, and falls through to Arial elsewhere — so the typography differs per machine |

**Done when.** Somebody who is not on this project can install it, see who made
it and what it is built from, and read every screen in the same typeface the
build intended.

---

## What we should never chase

Traversal scale, animation fidelity, vehicle handling, crafting, body needs.
Aiming high means being unmistakably deeper than KCD2 while looking
unmistakably worse, and being at peace with that trade rather than quietly
spending a year losing it.

---

## At risk

- **The frame gate is the only live red** — `game=17.55ms` against a 12ms
  budget, failing 28 of 141 runs. CI timings are the wrong machine to tune on.
- **The reach ledger is 37 typed entries, counting down only** — the debt
  measured, not cleared. Read each entry's REASON as well as its name: reasons
  decay exactly like comments and three were wrong on 4 August alone.
- **Two clips have a frozen root and one slot's identity is unresolved** —
  `game-design/clip-findings.txt`, which is a ceiling and can only be lowered.

*(The working rules that used to be repeated here live in `CLAUDE.md`, which is
read at the start of every session. Two copies of a rule is one copy that goes
stale, and this one had: it still described a 89-entry reach ledger and a crowd
of boxes months after both changed.)*
