# After M16 — the rest of the roadmap

> **STATUS — SPEC.** The design for the milestones between M16 and a shippable
> game. Stable reference: build state lives in `roadmap.md`, not here. A spec
> that disagrees with the roadmap is out of date about what got built, not
> about what was intended.

Written 2026-07-31, after re-scoring `agency-model.md` against the code.
Jafar's framing: *"goal is a high quality indie game but always looking at
SOTA games — specifically KCD2, RDR2, GTA5 — for immersion, quality,
completeness, replayability, complexity. We're not going to reach that level
in every aspect but we can get very close and we can exceed them in others."*

---

## The honest position

**M16 finishes the systems. It does not finish the game.** After it, every
dimension that read 0 has a number, and violence — the last missing verb in a
consequence system that had been waiting for it — exists.

What separates that from a game is three things, in this order of risk:

1. **Presentation.** Nineteen voices are cast and none generated. Forty-one
   animation clips are committed and nothing references them. This is the
   single largest gap between what the game *is* and what it *reads as*, and
   almost none of it is new design.
2. **The dimensions that are still low**, which are real features rather than
   polish — and which are exactly the "second life" half of the premise.
3. **The shape of a playthrough** — onboarding, pacing, and whether a second
   run differs. Untested, and the difference between a 6 and an 8 in this
   genre.

## The strategy, restated so the milestones can be judged against it

**Be incomparable on three axes and honest about the rest.** Social memory 93,
consequence persistence 95, information 90 — against best-in-class scores of
60, 85 and 65 across GTA5, RDR2, KCD2, BG3, Hitman, Sims and CK3. That is not
"close to" them; it is a category they do not enter.

The precedent is Disco Elysium against Baldur's Gate 3: it did not win on
production values, it won by being unmatched on one axis and unembarrassed
about the others.

**Everything below either defends that moat or removes a reason to bounce off
the game before reaching it.**

---

## M17 — THE GAME LOOKS AND SOUNDS LIKE ITSELF

The highest perceived-quality-per-hour work in the project, and the least
design risk: all of it has a working system underneath already.

| | | risk |
|---|---|---|
| Integrate the Mixamo bodies | 41 clips, two bodies, committed and unreferenced; the game still animates `Mannequin` boxes | **the one unknown** — no `.meta` files are tracked, so import settings are not under version control and Unity does not default to Humanoid |
| Generate the 19 voices | cast and approved 2026-07-31; chatterbox clones from the reference clips | low |
| Cast the 15 named characters with no voice | Ossei among them, and he is an Act III condition | low |
| Bark curation | 336 authored lines, read line by line | none — mine |
| Non-verbal foley | CC0 effort recordings through the voice pipeline | low |

**Why first:** a player judges a game in ninety seconds, and every one of the
systems below is invisible in the first ninety seconds of a game animating
boxes and speaking in silence.

## M18 — THE SECOND LIFE

The lowest scores on the board are all the same half of the premise. LEDGER is
*"open-city crime sim × slice-of-life social RPG"* and the slice-of-life side
scores 10–25 across the board.

| dimension | now | target |
|---|---|---|
| Home / base that reacts | 10 | 50 |
| Family & dependents | 15 | 50 |
| Companionship — who is with you | 15 | 55 |
| Self-presentation / lifestyle | 25 | 35 |
| Vice & addiction | 5 | 40 |

**This is the milestone that makes the moat matter.** A belief network is only
frightening if the people in it are people you would miss. Right now the game
can model the street knowing you are a criminal, and cannot model anybody
being at home waiting for you.

## M19 — THE CITY PUSHES BACK

Where the crime half is thin.

| dimension | now | target | what is missing |
|---|---|---|---|
| Faction politics / allegiance | 45 | 75 | rivals exist; allegiance never shifts |
| Law as a tool | 40 | 70 | you are *subject* to the law; you cannot *use* it |
| Public notoriety | 40 | 60 | a number that gates doors, with no press and no reputation events |
| Character competence | 10 | 40 | crew have competence, the player has none — `Harm` only ever subtracts |
| Visible odds | 0 | 50 | the player cannot see what a plan risks |

**Law as a tool is the sharpest of these.** The game already has an excise
audit, a detective and police escalation. Being able to *point* those at a
rival — inform, press a charge, tip off Ellis — turns a threat into a verb,
and it reuses everything the information layer already does.

## M20 — THE SHAPE OF A PLAYTHROUGH

Not a systems milestone. The one that decides the review score.

- **Onboarding.** The first fifteen minutes teach a belief network, an economy,
  a schedule and a double life. Currently they teach none of it.
- **Pacing and difficulty.** Seven days, then an open city, then an audit.
  Whether that curve holds is unmeasured.
- **Replayability.** Five endings exist. Whether a second run *feels* different
  is the untested claim, and the Director plus the gossip mill are the two
  systems that could make it true.
- **Legacy & succession, 40 → 70.** Succession exists only at the ending. A
  hand-over that matters mid-game is what turns one campaign into a dynasty.

## M21 — M16 PHASE 5, FIREARMS

Deliberately last, per the weapons spec. A gun in a game about being watched
is a different game, and it should arrive when everything that observes it is
finished.

## M22 — SHIP

Performance budgets, macOS (compiles today), controller support (27 `Input.*`
calls to move onto an action map — contained, not a rewrite), accessibility
beyond the caption channel, and the QA matrix run for real.

---

## The scope call that is still open, and I would raise it again

`the-gap.md` §4 argued hard for **cutting from seven districts to two or
three, and making those dense** — on the grounds that the gossip system is
*better* in a small world where the same faces recur and rumours reach people
who matter, and that seven graybox districts is the weaker game as well as the
more expensive one.

Seven were built. Nothing since has made that argument wrong, and M17's cost
scales with district count: set dressing, lighting, population and every
animation seen at every distance.

**Recommendation: pick two districts to finish to a shippable standard, and
leave the other five at their current fidelity.** Not a cut — a focus. Depth
over breadth is the entire strategy, and this is the one place where the build
is currently arguing with it.

## What we should never chase

Traversal scale, animation fidelity, vehicle handling, crafting, body needs.
Aiming high means being unmistakably deeper than KCD2 while looking
unmistakably worse, and being at peace with the trade rather than quietly
spending a year losing it.
