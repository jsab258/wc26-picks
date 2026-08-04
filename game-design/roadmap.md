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
| **now** | M17 — the game looks and sounds like itself | 17.4/17.6/17.9 closed · 17.7 part done · **17.1 CLOSED, and 17.1b is no longer waiting on anybody. Jafar ran the fetch on 4 Aug: eight real bodies landed, `bodyChoices` went 2 to 10, all fifty-two models carry valid human avatars, and the noon frame shows the player as a human mesh with limbs and a walk pose rather than a box.** What is open is that every body renders as ONE FLAT COLOUR — measured, not judged from the still: thirty materials across ten models, every one on the Standard shader and every one with no texture. Unity does not unpack embedded FBX media and has to be asked; explicit extraction is in flight. **Foot IK is wired as of 4 Aug** and has not yet run once |
| **also now** | M18 — the second life | family verified running · **the companion's cause is found, 4 Aug: she was never walking too slowly, she had no idea where the player WAS.** A walker learns the player's transform from one proximity sweep, and both the escort's target and its catch-up speed are guarded on having it — so falling behind is what stops you following, and it compounds. Bound at recruit time now; the gate had read `dist=29.4m` through a catch-up-speed fix that could not have helped. **CONFIRMED GREEN 4 Aug on `180f626`: `companionAtRecruit=9.2` against the 23.8m that made it red, `companionDist=4.2` at the deed, `deedWaitedDays=0` — she is recruited near, so the two-day wait never has to fire.** The escort was being picked by walker-list position, wherever she happened to be standing in the city; she is picked by proximity now · vice and lifestyle deferred |
| **next** | M19 — the people are thinking | inputs judged and fixed · **input parity done: a conversation can be carried without typing** · **outputs now judged too: the dialogue benchmark is a measured 78, no longer the word `unjudged`** |
| | M20 — the town you learn | **days now differ from each other** · **the district cut is OFF — filling the city beats shrinking it, measured** · the cast tiering is what remains |
| | M21 — the two ledgers | **started 4 Aug, and law-as-a-tool is now a complete verb.** An accusation is weighed by what the street will tell a detective rather than by whether it is true; making one marks you; and a charge that sticks points the detective at somebody else for four days before she comes back with exactly what she had. Allegiance shifts: pledge, refuse, walk out — three methods that existed, were tested, and had no callers. What remains is the surface a player accuses somebody FROM, empire growth, notoriety and the competence axis |
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
saw or were told, then spoken in their own character by a model — so they can be
WRONG about you, be argued with, and hold a grudge over a thing that never
happened. The one axis where we do not approximate KCD2 but beat it.

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

Phases 1–4 shipped and gated; phase 5 is firearms and is M23. The §4.7 gate
holds — *the same killing leaves no witness in an empty alley, several in a
market, and none in the back room of a busy pub*. Detail and post-mortems in
`roadmap-history.md`.

**"SHIPPED" IS TRUE OF THE CONSEQUENCE HALF AND NOT OF THE FIGHTING, found
2026-08-04 by reading the code rather than this table.** A killing is staged
as an EVENT — `ViolenceHost` sets a lethal flag and resolves the witnesses —
and everything downstream of that genuinely runs. There is no exchange of
blows anywhere: `Available`, `Resolve` and `StaminaCost` model stamina,
footing, guarding and reach, are tested, and **`Combat.` occurs exactly once
in the whole Game layer**, on an unrelated stamina line. Nothing constructs
a `Fighter`. It hid here because the gate certifying M16 asks about
WITNESSES, and a fight that cannot start still leaves an empty alley empty —
and on the reach ledger because only `Breathe` has a name that does not
collide with another Core type's method, so a four-method gap showed as one.
Fixing it is a milestone and it needs a done-condition measuring a FIGHT.

**The risk it exposed sets the pace of everything below:** the Game layer does
not compile locally, so every wiring change costs a ~28-minute round trip.

---

## M17 — THE GAME LOOKS AND SOUNDS LIKE ITSELF

**Why first.** A player judges a game in ninety seconds, and none of the depth
below is visible in them. Almost nothing here is new design.

| | what | state | risk |
|---|---|---|---|
| 17.1 | **Integrate the Mixamo bodies** | **CLOSED 2026-08-03 except the mesh.** The figure stands, the arms hang, and forty-one imported clips are being played by a locomotion blend tree. It took eight builds and two faults that were both ours, not Mixamo's, and it was closed by LOOKING at `review_day1_noon.jpg` after a gate blind to the fault had certified it once already. Full account in `roadmap-history.md`. What remains is that the body is a grey preview mannequin — that is 17.1b | **arms open; upside-down closed** |
| 17.1b | **Bodies and faces for EVERYONE** | **WIRED 2026-08-04, awaiting its first build.** Three things had to be true and now are: eight real Mixamo bodies are on disk (`bodyChoices=10`, all models carrying valid human avatars); their textures are extracted and reaching the mesh (`bodyKeptMats` non-zero, and the noon still shows a figure with skin, hair and clothes rather than a flat silhouette); and the named cast is attached to them. **`RealBody.TryAttach` had exactly ONE caller — `PlayerController` — so the player was a person and all sixty-seven walkers were articulated boxes.** The anonymous crowd keeps mannequins by choice: they are never spoken to and read fine at the distance you see them, and bounding it to the cast means the number of skinned bodies is something somebody chose. Gait bias, bad leg and idle phase come across from `Physique.For`, the same deterministic source `Mannequin` uses, so the cast does not walk in unison — the one way real bodies could have read as worse than the boxes. **NOT CLOSED until `walkerBodies` comes back non-zero**, because a claim that runs ahead of the build is the fault this file exists to avoid. The prerequisite is the part worth remembering: `TryAttach` publishes statics that five clauses of the `bodies` gate read as THE PLAYER's, so attaching walkers without separating them first would have made all five silently describe the last walker, and a corrupted gate reads exactly like a passing one. History in `roadmap-history.md` | **wired; risk is now cost, not absence** |
| 17.2 | **Generate the cast voices** — clones from the 19 reference clips | cast and consent-approved; **19 reference clips picked**. Blocked on a SCOPE decision, not on tooling — see below | **high, and it is scheduling** |
| 17.3 | **Cast the 15 named characters with no voice** | Ossei among them, and he is an Act III condition | low |
| 17.4 | **Bark curation** — the bark bank, read line by line | **DONE 2026-07-31** (884ce9a). 2,604 lines read by family. Everything mechanical was already clean; the two finds were things no check could see — `exchange.tell.certain` had six of fourteen openers starting the same way, and six `ambient.pair.ordinary` replies each answered one specific opener while `Answer()` picks them independently. Both now gated in `BarkGen` at a threshold read off the printed series | closed |
| 17.5 | **Non-verbal foley** — grunts, pain, exertion | decided: CC0 through the voice pipeline | low |
| 17.6 | **Surfaces** — a real texture set for the twelve logical surfaces `AssetLibrary` already asks for | **DONE 2026-08-01.** 12 CC0 albedos from ambientCG committed, attributed, `pack_check` green. Verified in a render: the noir tint neutralises the source saturation | closed |
| 17.7 | **Props, buildings and vehicles** — authored geometry instead of primitives | **PART DONE.** Vehicles: per-kind silhouettes, wheels at real proportions, density 28. "Buildings are cubes" was wrong both ways — they are box ASSEMBLIES (body, roof, setback tier, rooftop tank). **2026-08-01:** windows split from one band per floor into panes with piers, ground floor deliberately one wide shopfront light, gated to near-core buildings on the ramp the facades already use; overhead cables strung (`Dressing.CableAt`, off the reach ledger). **"Still open: cornices, and doors as geometry" was wrong on both counts and cost a wasted change on 3 August** — `GroundFloor` has been building a fascia, a recessed door and a parapet cornice on every street-facing mass for as long as it has existed, three lines apart, and I wrote a second door system in Core with four tests before reading it. **And "nothing distinguishes a shop from a house from a warehouse except the sign" is also wrong, checked 2026-08-04 by opening `GroundFloor`.** Premise kind already drives the fascia (a shop gets a signboard band, a house deliberately does not — "a signboard over somebody's front room is the fastest way to make a residential street look like a high street"), the door WIDTH via `Dressing.DoorWidth`, and the door HEIGHT — a warehouse gets 3.2m because a loading door has to take a cart. Third false "still open" in this row: it previously claimed cornices and doors were missing when both were built three lines apart, and that one cost a wasted change. What IS open: the back of a block gets bins and drainpipes but no geometry of its own | medium — volume, not difficulty |
| 17.8 | **Weapons and held objects** — the player's hands are empty | shipped: `HeldObject` draws from the hand, silhouette derived from reach | low |
| 17.9 | **A font that ships, and icons** | **DONE 2026-08-01.** PT Sans (SIL OFL) committed with its licence beside it; `fontless=0` every run | closed |

**17.6–17.9 were found by an audit on 2026-07-31, not by the plan** — this file
was derived from the work queue rather than from a definition of done, so it was
silent about nine whole categories. Cause in `completeness-audit-2026-07-31.md`.

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

**Everything you gain is a person who knows something about you.** A `CrewMember`
IS a gossip agent, with their own memory, loyalty and mouth. Recruiting
manufactures a witness with a wage. Expansion and exposure are the same system
read from either end — and as of 4 Aug the street finally hears about a poach.

| dimension | now | target | what is missing |
|---|---|---|---|
| Faction politics / allegiance | 45 | 75 | **allegiance shifts as of 4 Aug.** `PledgeTo` and `BreakWith` were written, tested and unwired — three methods were the whole gap. Both now run through `GameController` and broadcast to the street, and a poach finally reaches the gossip layer instead of moving two numbers in silence. Still missing: a place in the UI for the player to choose it, and standing that moves from anything other than the summit |
| **Law as a tool** | 40 | 70 | **the verb exists as of 4 Aug.** `Core/Informing` weighs an accusation against what the street would tell a detective, on the same magistrate's bar Act III uses, and returns the mark that goes on the player for having informed. `Core/Claims` turns a typed alibi into a `Fact`, so `ProcessClaim` and `PlayerClaims` run for the first time. **Redirecting an inquiry landed too (4 Aug).** `HomicideBook.PointAt` stores who the law is asking about instead of you; the relief comes off the NAMED half of the pressure only, never off the bodies, so a charge that sticks walks a manhunt back to an investigation and can never walk it to nothing — 1.00 to 0.73, then 0.80, 0.87, 0.93 and back to 1.00 over four days. `EvidenceHost.InquiryOf` was a second implementation of the same arithmetic and now delegates. Still missing: the surface a player names somebody FROM |
| Public notoriety | 40 | 60 | a number that gates doors, with no press and no reputation events |
| Character competence | 10 | 40 | crew have it; the player has none, and `Harm` only ever subtracts. **The third brick landed 4 Aug and is RUNNING (`e51c681`): `exposureYours=30 exposureTheirs=2`, weights 10.23 against 0.76, and the ledger screen says "Most of what the street has on you, it got from seeing you — your people have cost you little."** It is not the face-count the design note reads like: the street files a runner's round against the PLAYER by design, so what differs is CONFIDENCE — a racket rumour lands at `0.45 + 0.35 * (1 - competence)`, meaning a capable runner leaves a weak link and a clumsy one a strong one. That mechanic had run for weeks with nobody able to see it. Still missing: the first two bricks are visible (missed nights, skimmed envelopes) and none of the three yet CHANGES anything the player can do |

**Law as a tool was the one to build first, and the spine of it is in** (4 Aug):
an accusation is weighed by what people will say to a detective rather than by
whether it is true, and the mark for having informed is a return value so no
caller can skip the cost. The rest of the original plan still stands: The game already has an excise
audit, a detective with a case, and police escalation on a body. Being able to
*point* those at somebody — inform, press a charge, tip Ellis off, let a rival's
books be the ones that do not reconcile — turns the game's central threat into a
verb the player can hold. It reuses the whole information layer rather than
adding one: a crime game where your best weapon is what people believe.

**Growth is the competence axis, and there is NO EGO METER.** A number the
player tops up kills the story the mechanic exists to tell. Instead it is a run
of individually reasonable decisions that compound: take the bigger cut because
you earned it and loyalty erodes; do this one yourself because the lad would
botch it and four people see your face instead of his; miss tonight because this
job matters, and that is the sixth night running. The game already punishes
every one. What it owes the player is the ability to SEE the shape forming —
M19's chips, and as of 4 August the ledger's DOUBT section, which finally
reads back why each person stopped trusting you.

**The empire grows in DEPTH, not area.** Four businesses on a street where you
know every face beats twelve across a map.

**The rival is a person, not a stage counter — and this was half wrong when
written.** `ResolveTable` already offers terms, takes accept/defy/counter, moves
standing and attention, and writes the answer into her people's memory. What is
actually missing is her RINGING you: the summit is a place you go, not a call
you take, and `Phones` has been built since M10.

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
