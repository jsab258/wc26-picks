# LEDGER — roadmap

> **STATUS — LIVE, verified 2026-08-03.** The plan and the build state. If this
> and another doc disagree, this wins. If it is wrong, that is a bug in this file.

**The plan lives here.** Chronology, post-mortems and superseded plans are in
`roadmap-history.md`. Nobody should have to open a second document to find out
what happens next.

---

## The screen

| | | |
|---|---|---|
| **now** | M17 — the game looks and sounds like itself | 17.4/17.6/17.9 closed · 17.7 part done · **17.1: the player stands up again — confirmed in the frame, not just in a number. Two faults left in the same body: the arms hang 119° out from the sides, and it renders as bare mannequin while `bodyDressed=1` reports it clothed** |
| **also now** | M18 — the second life | family verified running · **companion still the one failing gate: she walks at 1.7m and sees the deed WORSE than the street does** · vice and lifestyle deferred |
| **next** | M19 — the people are thinking | inputs judged and fixed · **input parity done: a conversation can be carried without typing** · **outputs now judged too: the dialogue benchmark is a measured 78, no longer the word `unjudged`** |
| | M20 — the town you learn | **days now differ from each other** · **the district cut is OFF — filling the city beats shrinking it, measured** · the cast tiering is what remains |
| | M21 — the two ledgers | empire growth, law as a tool, and what expansion costs you |
| | M22 — the shape of a playthrough | onboarding, pacing, replayability, succession |
| | M23 — firearms | M16 phase 5, deliberately last |
| | M24 — ship | performance, platforms, controller, QA, licences, packaging |
| **shipped** | M0–M16, Acts I–III, the perception and consequence engine | |
| **waiting on Jafar** | a character MESH, which only he can buy | 17.1b. The 44 imported files are animation clips; the body itself is `X Bot.fbx`, Mixamo's free grey mannequin, and the noon frame shows exactly that — a featureless figure with a blue hip band. No amount of dressing code makes a placeholder into a person. Nothing else is blocked on him — the API spend he approved on 3 August is spent and delivered |

**The strategy every milestone below is judged against.**

**Get as close as possible to KCD2's immersion with the means we have, and use
LLM characters to beat it in the one place authored games cannot compete: the
people are THINKING, not triggering.**

Every NPC reaction in KCD2 is authored, and outside what the writer anticipated
there is nothing. Here, what a person thinks of you is computed from what they
saw or were told, then spoken in their own character by a model — so they can be
WRONG about you, be argued with, and hold a grudge over a thing that never
happened. The one axis where we do not approximate KCD2 but beat it.

**Replaced 2026-08-01.** The old line was *"be incomparable on three axes and
honest about the rest"* — a differentiation strategy, and following it faithfully
produced a 95-scoring consequence engine attached to a town of silent boxes.
Post-mortem in `roadmap-history.md`.

The consequence engine is not wasted by this. It stops being the product and
becomes the reason the conversations matter: the person talking to you knows
what you did and who told them.

**Worse at, and at peace with it:** visual fidelity, animation, traversal scale,
driving, content volume, combat depth. **Never worse at:** characters, dialogue,
whether the town feels inhabited, whether anything you do is remembered.

Scores per dimension are in `agency-model.md`, re-scored against the code on
2026-07-31.

---

## M16 — PERCEPTION, WEAPONS AND VIOLENCE *(shipped)*

A crime game in a city that perceives, reacts and remembers. Spec:
`weapons-spec.md`. Phases 1, 1b, 2, 3 and 4 all **shipped and gated**: vision
and hearing, witnesses with an ID ladder and a delivery window, misattribution,
melee and concealment and the frisk, provenance and disposal. Phase 5 is
firearms and is M23, deliberately last.

The §4.7 gate holds — *the same killing leaves no witness in an empty alley,
several in a market, and none in the back room of a busy pub* — asserted by the
sim rather than argued for. Phase detail and post-mortems in
`roadmap-history.md`.

**The risk it exposed still sets the pace of everything below:** the Game layer
does not compile locally. Only lint, ShapeCheck and CoreTests run here, so every
wiring change costs a ~28-minute Windows CI round trip.

---

## M17 — THE GAME LOOKS AND SOUNDS LIKE ITSELF

**Why first.** A player judges a game in ninety seconds, and none of the depth
below is visible in them. Almost nothing here is new design.

| | what | state | risk |
|---|---|---|---|
| 17.1 | **Integrate the Mixamo bodies** | **The standing-up half is CLOSED, 2026-08-03, and closed the way it should have been the first time — by opening `review_day1_noon.jpg` and seeing a figure on its feet, with `preHeadAboveHips=0.520` and `headAboveHips=0.522` agreeing on either side of the solve.** It took eight builds and a four-stage bracket because `bodyUp=1.000` reads the ROOT and structurally cannot see the skeleton, so the first close was certified by an instrument blind to the fault. Two independent faults in our own rig, both ours: the rest-restore asked whether an Animator EXISTED rather than whether anything was DRIVING the pose, so the body composed onto its own previous output for ever; and `Swing` composed onto a live rotation instead of assigning from a rest one. **Still open in the same body:** the arms sit 119° out from the sides (`restArmDrop=0.0` → `liveArmDrop=118.8`, and `ArmSwing` maxes at 22° so it cannot be that alone — the pre-solve sample that splits it is in flight), and the figure reads bare. | **arms open; upside-down closed** |
| 17.1b | **Bodies and faces for EVERYONE** | new 2026-08-01, and the largest single immersion gap. **2026-08-03, from the frame: the player is not "skinned but undressed", it is Mixamo's free `X Bot` mannequin** — `CharacterPrefab.BodyModel` names it, and the 44 imported files are animation clips carrying no mesh of their own. So `bodyDressed=1` is true and useless: the coat went on, onto a placeholder. The whole town is coloured boxes and the one skinned body is a shop dummy. Buying a real character mesh is Jafar's call and nothing here substitutes for it | **open — the biggest immersion gap** |
| 17.2 | **Generate the cast voices** — clones from the 19 reference clips | cast and consent-approved; **19 reference clips picked**. Blocked on a SCOPE decision, not on tooling — see below | **high, and it is scheduling** |
| 17.3 | **Cast the 15 named characters with no voice** | Ossei among them, and he is an Act III condition | low |
| 17.4 | **Bark curation** — the bark bank, read line by line | **DONE 2026-07-31** (884ce9a). 2,604 lines read by family. Everything mechanical was already clean; the two finds were things no check could see — `exchange.tell.certain` had six of fourteen openers starting the same way, and six `ambient.pair.ordinary` replies each answered one specific opener while `Answer()` picks them independently. Both now gated in `BarkGen` at a threshold read off the printed series | closed |
| 17.5 | **Non-verbal foley** — grunts, pain, exertion | decided: CC0 through the voice pipeline | low |
| 17.6 | **Surfaces** — a real texture set for the twelve logical surfaces `AssetLibrary` already asks for | **DONE 2026-08-01.** 12 CC0 albedos from ambientCG committed, attributed, `pack_check` green. Verified in a render: the noir tint neutralises the source saturation | closed |
| 17.7 | **Props, buildings and vehicles** — authored geometry instead of primitives | **PART DONE.** Vehicles: per-kind silhouettes, wheels at real proportions, density 28. "Buildings are cubes" was wrong both ways — they are box ASSEMBLIES (body, roof, setback tier, rooftop tank). **2026-08-01:** windows split from one band per floor into panes with piers, ground floor deliberately one wide shopfront light, gated to near-core buildings on the ramp the facades already use; overhead cables strung (`Dressing.CableAt`, off the reach ledger). Still open: cornices, and doors as geometry | medium — volume, not difficulty |
| 17.8 | **Weapons and held objects** — the player's hands are empty | shipped: `HeldObject` draws from the hand, silhouette derived from reach | low |
| 17.9 | **A font that ships, and icons** | **DONE 2026-08-01.** PT Sans (SIL OFL) committed with its licence beside it; `fontless=0` every run | closed |

**17.6–17.9 were found by an audit on 2026-07-31, not by the plan** — this file
was derived from the work queue rather than from a definition of done, so it was
silent about nine whole categories. Cause in `completeness-audit-2026-07-31.md`.

**17.2 was never blocked on Jafar** — the 15,624-clip figure was a cross
product, not a measurement. Real demand is `clipsAsked=276 voicesAsked=6`, an
afternoon. Post-mortem in `roadmap-history.md`.

**The visual target is coherence, not fidelity.** `production-plan-audio-art.md`
§4 chose stylised noir for the reason that still holds — a game about what people
think they saw should look subjective and half-obscured, and weather and fog cut
draw distance, hide low-detail geometry and make mood at once. One palette across
seven districts beats scattered high-resolution assets, and none of it needs a
purchase.

**The project can see itself.** Every Windows build commits four stills and a
`verdict.txt` to `game-design/sim-shots/`. **Judge M17 from the stills, not from
the source** — and read all four before reading any gate. What that loop has
found, and the 17.1 import risk as it stood before it closed, are in
`roadmap-history.md` §"seeing the game, 2026-08-01".

**Done when.** A sim screenshot shows a skinned body walking with foot IK, and
`bodiesOk` gates on the Avatar being bound rather than on `Mannequin` boxes;
every named character speaks in their cast voice; the bark bank has been read
end to end; effort sounds exist for Phase 3's fight.

**Depends on.** Nothing. All five can start today.

---

## M18 — THE SECOND LIFE

**Why it matters more than its scores suggest.** A belief network is only
frightening if the people in it are people you would miss. Dimension scores and
the full argument are in `agency-model.md` and `roadmap-history.md`.

**What is in it.**
- **Home as a place that reacts.** The rooms above the pub change with money,
  heat and who has been in them. A base that reads your week back to you.
- **Companionship.** **DONE 2026-08-01.** `Core/Companionship` + `CompanionHost`
  + `NpcWalker.Escorting`. The companion is a witness through
  `Witnesses.Resolve` **by standing there** — no companion branch anywhere in
  the perception path — and adds no new threshold: both join/leave lines are
  taken from `Empire`'s recruit and poach floors, and whether they spot a
  watcher is `Perception` from where they stand. Gated on the comparison
  (`companionRung >= streetRung >= 4`), because a gate on their rung alone
  would pass on a run where the whole street had a clean look.
- **Family and dependents.** **DONE 2026-08-01.** `Core/Household` +
  `HouseholdHost`. Neglect has no number anything reads: a dependent below
  `TalkFreely` is added to the mill as an ordinary agent whose loyalty is their
  bond, so the people closest to you become the people most willing to talk.
- **Vice.** A cost that is not money and not heat. **Not started.**
- **Lifestyle.** **Not started, and the substrate this entry claimed does not
  exist.** It said *"`Core/Coat` and `Core/Dressing` exist; what you wear should
  be read by the street, and it already can be — `Reaction.CataloguesYourCoat`
  has no caller."* Checked 2026-08-01: `Coat` is weapons **concealment**,
  `Dressing` is **street furniture** placement, and `CataloguesYourCoat` DOES
  have a caller (`CoatHost.Arrested`) — which itself has none, so it is the
  whole `Reaction.Lawful` arrest path that is unwired, and that is an M19
  finding rather than a lifestyle one. Nothing here is self-presentation.
  Lifestyle needs **building**, not wiring, and `Core/Wardrobe` (which dresses
  the crowd) is the only real starting point.

**Done when.** A run where the player never goes home is measurably worse in
the endings matrix than one where they do — and the difference comes from
relationships rather than from a stat.

**Depends on.** M17 for anybody to look like a person while doing it.

---

## M19 — THE PEOPLE ARE THINKING *(next, and the centrepiece)*

The conversation system is wired, tested and reachable. **Nobody has ever sat
down and asked whether talking to these people is any good.** That is the
largest unexamined risk in the project: if the writing is flat, every milestone
either side of it is decoration, and we would be paying to voice something that
needs rewriting.

- **Judge the existing conversation as WRITING**, at length, with a verdict.
  Costs nothing and happens BEFORE voices are generated.
- Then make it good: character voice held under pressure, memory of what you
  actually did, refusal to break when pushed.
- **Negotiation as the empire's verb.** Recruiting, bribing, threatening, being
  talked round — scenes rather than menu picks. This is where the model earns
  its place, because no authored tree affords it at scale.
- NPCs who are **wrong about you** and can be argued with.

**INPUT PARITY — a rule, checked, not promised.** Every conversational action is
reachable with a stick and two buttons. Typing and dictation stay first-class
alternatives, never removed and never required. The check: no dialogue state is
reachable ONLY by text.

*This inverts a decision from 2026-07-26 that is still in the code —
`DialogueUI` reads "clicking one says it; typing stays the game", with chips as
a convenience on top of an `InputField`.* The fix is to stop the model PARSING
and start it OFFERING: it writes four things Tom could say right now, from live
state, and you pick one. `IntentRouter` already exists and is tested — today it
maps typed text to an intent, and the change is that it maps stick input to the
same intent. Plus an approach radial (press, lie, offer, soften) where you
choose the intent and the model writes Tom's words.

**A side effect worth having: the chips ARE the odds display.** An option
reading *"ask him why he was on Quay Street"* only appears if you know he was.
That answers `agency-model`'s visible-odds row (scored 0, target 50) without a
percentage anywhere on screen — the player sees what they hold by seeing what
they can say.

**And the couch problem is reading, not typing.** Nobody wants three paragraphs
at two metres from a television, which makes 17.2's voices load-bearing rather
than polish. Replies stay short; subtitles optional.

**Done when.** A conversation with somebody who half-saw you do something is
worth having twice, their opinion changed because of what you said rather than
because a flag flipped, and the whole exchange was played on a controller.

**Depends on.** M17 for anybody to have a face while doing it.

---

## M20 — THE TOWN YOU LEARN

**Three districts, and the number is measured rather than argued.**
`ledger/Recurrence` links the real `Population` model and counts how many people
an ordinary resident crosses in a day: **6.5 at seven districts, 12.1 at two,
12.9 at three** — and 32% more at face range. Concentration nearly doubles
recurrence, which is the mechanism by which a place becomes familiar.

Three beats two because Ironside houses 4% of the city and employs 20%: it drags
commuters across the map and manufactures crossings. It is also the design's own
*"warehouses, logistics, places without witnesses"*, so cutting it would have
cost the game its best unobserved location. **Keep the Hook, Copper Row and
Ironside; cut four.** This supersedes the two-district call of 2026-07-31, which
was right about cutting and wrong about how far.

- **Days that differ from each other.** `OutdoorsAt` and `OutdoorPosition` take
  an hour and reduce it mod 24 — there is no day parameter anywhere in the
  routine model, so every Tuesday is every Saturday and recurrence is total and
  unearned. Found by the tool above while measuring something else.
- **Tier the cast**, because recognition and relationship have different
  cognitive costs: a named few with faces and voices and real memory, a
  recognisable many with a name and a routine, a crowd that witnesses and
  gossips and fills a market. Dunbar's layers (~5 / ~15 / ~50 / ~150) are the
  scale; the sizes come from the sweep below and from a frame budget nobody has
  measured yet.
- **Population is a dial, not a cliff.** Three districts: 350 people gives 5.1
  crossings a day, 700 gives 12.9, 1400 gives 21.9, 2800 gives 38.9. Roughly
  linear, so the crowd tier can be sized against performance rather than opinion.
- Routines legible enough that following somebody for an afternoon holds up.

**Constraint to respect:** 44 character models exist, measured every build. That
caps distinct NAMED faces until somebody buys more, which is Jafar's call.

**Done when.** You recognise a regular by their coat before you can see their
face, and you are right.

---

## M21 — THE TWO LEDGERS

You inherit a pub, two workers and your father's debts. The day side is a
licence, a till and wages. The night side pays better than the bar ever will.
**The game is named for the two books that do not balance** — and the build
already tracks them apart: one run closed with £0 clean against £354 dirty,
which is the whole story in two numbers.

**Everything you gain is a person who knows something about you.** This is
already true in code and only needs surfacing: a `CrewMember` IS a gossip agent,
with their own memory, loyalty and mouth. Recruiting manufactures a witness with
a wage. Lose them below the poach line and they walk carrying everything they
stood next to. Expansion and exposure are the same system read from either end.

| dimension | now | target | what is missing |
|---|---|---|---|
| Faction politics / allegiance | 45 | 75 | rivals exist; allegiance never shifts |
| **Law as a tool** | 40 | 70 | you are *subject* to the law; you cannot *use* it |
| Public notoriety | 40 | 60 | a number that gates doors, with no press and no reputation events |
| Character competence | 10 | 40 | crew have it; the player has none, and `Harm` only ever subtracts |

**Law as a tool is the one to build first.** The game already has an excise
audit, a detective with a case, and police escalation on a body. Being able to
*point* those at somebody — inform, press a charge, tip Ellis off, let a rival's
books be the ones that do not reconcile — turns the game's central threat into a
verb the player can hold. It reuses the whole information layer rather than
adding one: a crime game where your best weapon is what people believe.

**Growth is the competence axis, and there is NO EGO METER.** The obvious
implementation is a number the player learns to top up, which kills the story
the mechanic exists to tell. Instead it is a run of individually reasonable
decisions that compound: take the bigger cut because you earned it, and loyalty
erodes; do this one yourself because the lad would botch it, and four people see
your face instead of his; miss tonight because this job matters, and that is the
sixth night running. The game already punishes every one of those. What it owes
the player is the ability to see the shape forming, which M19's chips supply.

**The empire grows in DEPTH, not area.** Four businesses on a street where you
know every face beats twelve across a map — legible, affordable, and it agrees
with M20's cut.

**The rival is a person, not a stage counter.** Sera Kest has a name and an
escalation number; she should be able to ring you, offer terms, be refused, and
remember it.

**Done when.** A player can end a rival without touching them — allegiance
moves, a charge lands, their access closes because of what the street believes.
And a player who overreached can look back and name the night it became
inevitable.

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
- **Replayability.** Five endings exist. Whether a *second run feels different*
  is the untested claim, and the Director plus the gossip mill are the two
  systems that could make it true — different people knowing different things
  is a different game, if the Director is actually authoring variety.
- **Legacy & succession, 40 → 70.** Succession exists only at the ending. A
  hand-over that matters mid-game is what turns one campaign into a dynasty,
  and CK3 scores 95 here for exactly that.

**Done when.** Two full playthroughs by somebody who has not read the design
docs, with notes, and a measured difference between them.

**Depends on.** Everything above, because it is the milestone that judges them.

---

## M23 — FIREARMS

M16 phase 5, held back on purpose. A gun in a game about being watched is a
different game, and it should arrive when everything that observes it is
finished: the ladder, the delivery window, provenance, disposal, notoriety.
Building it earlier would have made every one of those decisions easier and
wronger.

---

## M24 — SHIP

Performance budgets held under load; macOS (compiles today, never run);
controller support (28 `Input.*` calls to move onto an action map — contained,
not a rewrite, and zero `OnGUI` so the focus model already applies);
accessibility beyond the caption channel; and `qa-matrix.md` run for real by a
person rather than asserted by a harness.

**And the four things that turn a build into something a person installs**,
added by the 2026-07-31 audit because none of them had an owner:

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

- **Windows CI is green** (`2cd11c2`, pass=True). `nightNotDarker` is settled.
- **The animation import** (M17.1) is unverifiable locally but CI says it works:
  `humanoid=44 validHumanAvatar=44`, `realBody=1` scaled x0.949 from raw 1.90m.
  Player skinned; the crowd stays boxes until one is costed on a GPU-less runner.
- **Phases 2–4 were built, tested and disconnected.** `tools/ReachCheck` runs
  every commit; the ledger is 89 typed entries, counting down only — the debt
  *measured*, not cleared.

## The rules this project runs on

- **Measure before you gate.** A threshold set without a measured value is how
  `nightNotDarker` failed on noise. Print the series first — it is what
  separated a leaking reasons trail from a healthy rumour count.
- **Check the ruler before the reading.** The instrument was at fault four
  times this month: `breakrun.py` reverting one file of a two-file spec, a bark
  manifest written to an untracked path, a diagnostic reporting on a corpus it
  had sampled one speaker of, and an Adversary control asserting behaviour the
  router had reasoned its way out of.
- **Built is not running.** A system with no call site is not a feature and
  looks exactly like one in review — `SuspicionTracker.Reasons` is the newest.
- **Nothing here requires a purchase.** Characters, animations and voices came
  free; the last shopping-list item was decided free on 2026-07-31.
