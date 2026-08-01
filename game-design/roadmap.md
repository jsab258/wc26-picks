# LEDGER — roadmap

> **STATUS — LIVE, verified 2026-07-31.** the plan and the build state. If this
> and another doc disagree, this wins.
> Kept current. If it is wrong, that is a bug in this file.

**The plan lives here.** Every dated build state, post-mortem and superseded
plan is in `roadmap-history.md`; if a section here starts growing a chronology
it is in the wrong file. What this file must never do again is make somebody
open a second document to find out what happens next.

---

## The screen

| | | |
|---|---|---|
| **now** | M16 — perception, weapons, violence | **phases 1–4 shipped and gated**; 5 is M21 |
| **next** | M17 — the game looks and sounds like itself | bodies, voices, barks, foley, **surfaces, props, weapons** |
| | M18 — the second life | home, family, companionship, vice |
| | M19 — the city pushes back | allegiance, law as a tool, notoriety, competence |
| | M20 — the shape of a playthrough | onboarding, pacing, replayability, succession |
| | M21 — firearms | M16 phase 5, deliberately last |
| | M22 — ship | performance, platforms, controller, QA, **licences, packaging, fonts** |
| **shipped** | M0–M15, Acts I–III, seven districts, the British setting | |
| **waiting on Jafar** | nothing | |

**The strategy every milestone below is judged against.** Be incomparable on
three axes and honest about the rest: social memory **93**, consequence
persistence **95**, information **90** — against a best-in-class of 60, 85 and
65 across GTA5, RDR2, KCD2, BG3, Hitman, Sims and CK3. That is not "close to"
them, it is a category they do not enter. The precedent is Disco Elysium
against Baldur's Gate 3: it did not win on production values, it won by being
unmatched on one axis and unembarrassed about the others. Scores per dimension
are in `agency-model.md`, re-scored against the code on 2026-07-31.

---

## M16 — PERCEPTION, WEAPONS AND VIOLENCE *(now)*

The largest feature in the project and the one that changes the framing: a
crime game in a city that perceives, reacts and remembers. Spec:
`weapons-spec.md`.

| phase | | state |
|---|---|---|
| 1 | vision, hearing, masking, investigation | **shipped, gated** |
| 1b | vignette, noise ring, four attention channels, captions | **shipped, gated** |
| 2 | witnesses, slots, ID ladder, delivery window, misattribution | **shipped, gated** — the ghost landed 2026-07-31 |
| 3 | melee, carry, concealment, the frisk, blood | **shipped, gated** 2026-07-31 |
| 4 | provenance, acquisition, disposal, accidents | **shipped, gated** 2026-07-31 |
| 5 | firearms | M21, deliberately last |

**Phase 3 — what is in it.** Hands, blunt, edged and ligature as tested state
machines; brandish as a verb of its own, because §5.1 says the threat is the
main use; carry as hands-and-a-coat rather than a grid; concealment as the
real stat; the frisk, and what refusing one costs; blood as evidence that ages,
is noticeable at a distance and in a light level, and can be washed given water
and privacy.

**Phase 3 — done when.** The §4.7 gate: *the same killing leaves no witness in
an empty alley, several in a market, and none in the back room of a busy pub.*
One act, three places, three outcomes, asserted in the sim rather than argued
for.

**Phase 4 — what is in it.** Provenance as a permanent property of an object;
the four acquisition routes, all of them social; disposal as a verb somebody
can watch you perform; Ellis looking for the object rather than for you; and
accidents — the only violence in the game that produces no crime.

**Phase 4 — done when.** A weapon acquired by each of the four routes carries
a different traceability, and disposal seen by a witness produces a different
residual risk from disposal unseen. Both are numbers `Core/Traces` already
computes and nothing currently calls.

**The real work in both was wiring, and the reach check found more of it than
the hand analysis had.** An afternoon's manual gap analysis over 61 public Core
APIs said roughly 40 had no call site. `tools/ReachCheck` ran the same question
as a call-graph walk in a second and said **131**. Thirty-eight of those were
M16 phases 2–4 — `Brandish` 0, `MayFrisk` 0, `Acquire` 0, `Traceability` 0 —
built, tested, green and unreachable, which is this project's oldest failure
mode. The ledger stood at **89** when the phases landed, and it can only count
down: wiring an API without deleting its row fails the build too.

**Risk.** The Game layer does not compile locally; only lint, ShapeCheck and
2,884 CoreTests run here. Every wiring change is verified by a ~28-minute
Windows CI run, and that round trip sets the pace.

---

## M17 — THE GAME LOOKS AND SOUNDS LIKE ITSELF

**Why first, ahead of every system below.** A player judges a game in ninety
seconds. Right now it animates boxes and speaks in silence, and none of the
depth below is visible in those ninety seconds. Almost nothing here is new
design — every item has a working system underneath already.

| | what | state | risk |
|---|---|---|---|
| 17.1 | **Integrate the Mixamo bodies** — import as Humanoid, bind through `CharacterRig`, retarget 41 clips | 41 clips and two bodies committed; **nothing references them** | **the one real unknown** |
| 17.2 | **Generate the 19 cast voices** — chatterbox clones from the reference clips | cast and consent-approved 2026-07-31 | low |
| 17.3 | **Cast the 15 named characters with no voice** | Ossei among them, and he is an Act III condition | low |
| 17.4 | **Bark curation** — the bark bank, read line by line | **DONE 2026-07-31** (884ce9a). 2,604 lines read by family. Everything mechanical was already clean; the two finds were things no check could see — `exchange.tell.certain` had six of fourteen openers starting the same way, and six `ambient.pair.ordinary` replies each answered one specific opener while `Answer()` picks them independently. Both now gated in `BarkGen` at a threshold read off the printed series | closed |
| 17.5 | **Non-verbal foley** — grunts, pain, exertion | decided: CC0 through the voice pipeline | low |
| 17.6 | **Surfaces** — a real texture set for the twelve logical surfaces `AssetLibrary` already asks for | **DONE 2026-08-01.** 12 CC0 albedos from ambientCG committed, attributed, `pack_check` green. Verified in a render: the noir tint neutralises the source saturation | closed |
| 17.7 | **Props, buildings and vehicles** — authored geometry instead of primitives | **PART DONE.** Vehicles had per-kind silhouettes already and now have wheels, verified against real proportions (car dia/hi 0.40, bus 0.34); density 14 -> 28 so a street reads occupied. Buildings and street furniture are still cubes | medium — the volume of work, not the difficulty |
| 17.8 | **Weapons and held objects** — the player's hands are empty | shipped: `HeldObject` draws from the hand, silhouette derived from reach | low |
| 17.9 | **A font that ships, and icons** | **DONE 2026-08-01.** PT Sans (SIL OFL) committed with its licence beside it; `fontless=0` every run | closed |

**17.6–17.9 were found by an audit on 2026-07-31, not by the plan.** Jafar asked
whether the roadmap covered textures and models; it did not, and eight other
categories were missing with them. `completeness-audit-2026-07-31.md` has the
evidence and the cause. The short version: this file was derived from the work
queue rather than from a definition of done, so it was complete about the things
somebody was already thinking about and silent about the rest.

**The visual target is coherence, not fidelity.** `production-plan-audio-art.md`
§4 chose stylised noir for the reason that still holds — a game about what people
think they saw should look subjective and half-obscured, and weather and fog do
the heavy lifting because they cut draw distance, hide low-detail geometry and
create mood at once. One palette across seven districts beats scattered
high-resolution assets, and none of it needs a purchase: CC0 PBR sources cover
every surface name already in `AssetLibrary`.

**17.6's blocker cleared two days ago and nobody noticed.** §4 item 5 put
building and prop packs on hold on 2026-07-28 pending the character direction;
Mixamo landed 2026-07-30. A blocked item living only in a spec unblocks silently
and then waits forever, which is the argument for this table carrying it.

**17.1 is the risk and it is worth naming precisely.** No `.meta` files are
tracked anywhere in this project, so FBX import settings are not under version
control, and Unity does not default a model to Humanoid. `CharacterRig` needs
Humanoid — the Avatar is the contract, deliberately, because Mixamo's bone
names are stable right up until somebody re-exports from Blender. Committing
import settings changes a project convention, and it is the one piece that
cannot be checked locally at all: Unity decides, and the first evidence is a
CI screenshot.

**The project can now see itself, as of 2026-08-01.** Every Windows build
commits four stills and a `verdict.txt` to `game-design/sim-shots/`, and that
loop found, in its first hours: names drawn over rooftops, street signs reading
as doubled glyphs, a noon sky at 2.6x the scene mean, a crowd dressed off the
whole colour wheel, and a wardrobe 1.83x over its designed share of olive. It
also cleared three textures and one set of wheel proportions that I had
condemned from a low-resolution frame and that were correct all along. Judge M17
from the stills, not from the source.

**Done when.** A sim screenshot shows a skinned body walking with foot IK, and
`bodiesOk` gates on the Avatar being bound rather than on `Mannequin` boxes;
every named character speaks in their cast voice; the bark bank has been read
end to end; effort sounds exist for Phase 3's fight.

**Depends on.** Nothing. All five can start today.

---

## M18 — THE SECOND LIFE

**The lowest scores on the board are all the same half of the premise.** The
design doc's genre line is *"open-city crime sim × slice-of-life social RPG"*
and the slice-of-life side reads 5 to 25 across every dimension.

| dimension | now | target |
|---|---|---|
| Home / base that reacts | 10 | 50 |
| Family & dependents | 15 | 50 |
| Companionship — who is with you | 15 | 55 |
| Self-presentation / lifestyle | 25 | 35 |
| Vice & addiction | 5 | 40 |

**Why it matters more than its scores suggest.** A belief network is only
frightening if the people in it are people you would miss. The game can
currently model the street knowing you are a criminal, and cannot model
anybody being at home waiting for you. Every consequence the moat produces
lands on nothing.

**What is in it.**
- **Home as a place that reacts.** The rooms above the pub change with money,
  heat and who has been in them. A base that reads your week back to you.
- **Companionship.** `CrewMember` exists as a roster entry; nobody walks beside
  you. Somebody accompanying you sees what you do — which makes them a witness
  under M16's rules, and that is the interesting version.
- **Family and dependents.** The people whose week is worse when yours is.
- **Vice.** A cost that is not money and not heat.
- **Lifestyle.** `Core/Coat` and `Core/Dressing` exist; what you wear should be
  read by the street, and it already can be — `Reaction.CataloguesYourCoat` has
  no caller.

**Done when.** A run where the player never goes home is measurably worse in
the endings matrix than one where they do — and the difference comes from
relationships rather than from a stat.

**Depends on.** M17 for anybody to look like a person while doing it.

---

## M19 — THE CITY PUSHES BACK

Where the crime half is thin. Four dimensions, and one of them is the sharpest
single item left in the project.

| dimension | now | target | what is missing |
|---|---|---|---|
| Faction politics / allegiance | 45 | 75 | rivals exist; allegiance never shifts |
| **Law as a tool** | 40 | 70 | you are *subject* to the law; you cannot *use* it |
| Public notoriety | 40 | 60 | a number that gates doors, with no press and no reputation events |
| Character competence | 10 | 40 | crew have competence; the player has none, and `Harm` only ever subtracts |
| Visible odds | 0 | 50 | the player cannot see what a plan risks before committing to it |

**Law as a tool is the one to build first.** The game already has an excise
audit, a detective with a case, and police escalation on a body. Being able to
*point* those at somebody — inform, press a charge, tip Ellis off, let a rival's
books be the ones that do not reconcile — turns the game's central threat into
a verb the player can hold. It reuses the entire information layer rather than
adding one, and it is the strongest expression of the moat: a crime game where
your best weapon is what people believe.

**Visible odds is the cheapest.** `Core/Operation` already computes risk; the
player simply cannot see it. BG3 scores 95 here for showing a percentage.

**Done when.** A player can end a rival without touching them, and the sim can
demonstrate it: allegiance moves, a charge lands, and the rival's access closes
because of what the street believes rather than because of a fight.

**Depends on.** M16 for the observation model the accusations run on.

---

## M20 — THE SHAPE OF A PLAYTHROUGH

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

## M21 — FIREARMS

M16 phase 5, held back on purpose. A gun in a game about being watched is a
different game, and it should arrive when everything that observes it is
finished: the ladder, the delivery window, provenance, disposal, notoriety.
Building it earlier would have made every one of those decisions easier and
wronger.

---

## M22 — SHIP

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

## The scope call that is still open

`the-gap.md` §4 argued for **two or three dense districts rather than seven
graybox ones** — the gossip system is *better* in a small world where the same
faces recur, rumours reach people who matter, and the player learns a street
rather than a map. Seven were built.

Nothing since has made the argument wrong, and M17's cost scales directly with
district count: set dressing, lighting, population, and every animation seen at
every distance.

**Recommendation: finish two districts to a shippable standard and leave the
other five at current fidelity.** Not a cut — a focus. Depth over breadth is the
whole strategy, and this is the one place the build currently argues with it.

*Jafar, 2026-07-31: "fine with the district thing."*

## What we should never chase

Traversal scale, animation fidelity, vehicle handling, crafting, body needs.
Aiming high means being unmistakably deeper than KCD2 while looking
unmistakably worse, and being at peace with that trade rather than quietly
spending a year losing it.

---

## The testing system

Researched and planned 2026-07-31 on Jafar's instruction; **applying it across
the game is gated on his word.** Five layers, in `testing-system.md`:

| | layer | catches | when |
|---|---|---|---|
| 1 | **Reach** — every public Core API has a caller | *built is not running*; ~40 APIs with no call site | before M16 ph.3/4 land |
| 2 | **Shape** — text, audio and assets are well-formed | 21 of 42 gossip templates rendering a lowercase sentence under 2,883 green tests | before M16 ph.3/4 land |
| 3 | **Pixels** — golden-frame perceptual regression | a shader change turning every night purple | after M17 |
| 4 | **Time** — determinism, replay, 100-day soak, save/load chaos | a bug that is currently unreproducible | after M17 |
| 5 | **Adversary** — input fuzzing, a bot that plays badly, exploit search | softlocks and dominant strategies | after M17 |

What already exists is stronger than the gap list suggests: 2,884 CoreTests,
**21 mutation-testing specs** (`breakrun.py` — most studios do not do this),
20 gated sim claims, an LLM-vs-LLM playtest, Monte-Carlo balance, and content
enumeration that measures repeat intervals rather than asserting them.

## At risk

- **Windows CI is red.** `nightNotDarker` compared one noon frame to one night
  frame out of eleven days and failed on a thousandth. The gate now uses the
  whole series and prints it; unverified until the next run.
- **The animation import** (M17.1) cannot be checked locally at all.
- **Phases 2–4 were built, tested and disconnected** — ~40 Core APIs with no
  call site. Being fixed now, and the reason to distrust "built" as a status.

## The ship checklist — every category, and who owns it

**This table exists because the roadmap did not have one, and nine categories
were missing.** A milestone may not claim a category it has not named. Anything
here with no owner is a gap whether or not somebody is currently thinking about
it — which is the whole failure the 2026-07-31 audit found, and it is `built is
not running` one level up: a category with no milestone looks finished in a
roadmap exactly like a system with no call site looks finished in a review.

| | owner | state |
|---|---|---|
| Simulation systems | M16, M18–M21 | the moat; in progress |
| Character models and animation | 17.1 | committed, not imported |
| Voices | 17.2, 17.3 | cast; generation pending |
| Barks | 17.4 | 2,604 lines enumerated, curation mine |
| Foley | 17.5 | decided free, not sourced |
| Surfaces and textures | **17.6** | nothing |
| Props, buildings, vehicles | **17.7** | primitives |
| Weapons and held objects | **17.8** | invisible |
| Fonts and icons | **17.9**, 22.4 | borrowed from the OS |
| Music | shipped M13 | procedural layer, running |
| Lighting, weather, post | shipped | noir pass, grain, bloom, AO, reflections |
| UI and menus | shipped | text-only, no icons |
| Save / load | shipped | atomic, slots, backup recovery |
| Onboarding and pacing | M20 | not started |
| Performance | M22, testing Layer 4 | gated per run, no trend yet |
| Platforms | M22 | Windows green, macOS compiles, never run |
| Controller | M22 | 28 `Input.*` calls to move |
| Accessibility | M22 | caption channel only |
| Testing | testing-system.md | Layers 1–2 built, 3–5 planned |
| Credits, licences, attribution | **22.1** | nothing, and CC BY 4.0 requires it |
| Localisation | **22.2** | no infrastructure, no decision on record |
| Packaging and release | **22.3** | nothing |

## The rules this project runs on

- **Measure before you gate.** A threshold set without a measured value is how
  `nightNotDarker` came to fail on noise and `deedSlotSets` went ungated for
  days.
- **Check the ruler before the reading.** Three times this month the instrument
  was at fault — `breakrun.py` reverting one file of a two-file spec, the bark
  manifest written to an untracked path, a diagnostic sampling one speaker and
  reporting on a corpus.
- **Built is not running.** A system with no call site is not a feature, and it
  looks exactly like one in a code review.
- **Nothing here requires a purchase.** Characters, animations and voices all
  came free; the last item on the shopping list was decided free on 2026-07-31.
