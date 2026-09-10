# The plan: the visual ladder, and the phases underneath it

STATUS: LIVE. verified 2026-09-10. THIS FILE PLUS `production/queue/` IS THE
PLAN, ruled by Jafar 2026-09-10 in the same cleanup batch that gave the project
one decision register. Before that ruling there were four plan documents and a
reader had to guess which one governed. The fold is recorded at the bottom of
this file, under "The fold of 2026-09-10".

The ladder itself was ruled by Jafar 2026-09-09, item 5 of that
morning's message, and his own words are the whole specification: "The next
ladder is visual-first... The crime and gossip work continues underneath; the
ladder measures what I can see."

THIS FILE IS READ BY A MACHINE. `tools/map.py` renders the table below as the
project overview's first screen, so the columns are a contract: `rung`, `name`,
`status`, `done looks like`. Status is exactly one of `done`, `current`, `next`,
`later`. Exactly one row may be `current`. Change a rung's name here and the
map changes; there is no second copy.

WHAT THE LADDER MEASURES, AND WHAT THE PHASES MEASURE. The rung table below is
ONE AXIS, the one Jafar can see without being told what to look at, and it ends
at the Meridian Test's first condition: a person who loves GTA or KCD2 plays
thirty minutes and does not bounce off the visuals. The phases and their exit
gates, further down this file, are the other axis: what gets built, in what
order, and what has to be true before a phase is done. They are not two plans.
The rung is what Jafar looks at this week; the phase is what the work is for.
`production/queue/` is where both turn into items somebody can pick up.

WHY IT IS VISUAL-FIRST NOW. The art line shipped its research and its plans and
skipped its visual half, and the channel was reporting counts rather than
outcomes, so two weeks of work were legible to the studio and invisible to him.
A ladder whose rungs are all pictures cannot have that failure.

## The rungs

| rung | name | status | done looks like |
|---|---|---|---|
| 1 | The street matched to the Hook sheet | current | The built Quay Street rendered from the SAME viewpoint as the lower panel of OUR OWN Hook sheet, approved by Jafar 2026-09-10 and made the reference panel in place of the outside one, with rain, a wet road, worn materials and sky, and you judging the two side by side. Your judgement is the gate; no number passes this rung. |
| 2 | Props read as their materials | next | Every placed prop reads as the material it is meant to be, and the first-batch clutter is placed per `production/art/atlas-01/PRODUCTION-CATALOGUE.md` on `origin/art/atlas-01`, which is where the atlas lives and not in this checkout, in a frame he can see it in. |
| 3 | Mickey's frontage on the street | next | The frontage stands on Quay Street at the bay count you rule. IT IS A MINICAB OFFICE, NOT A PUB, by your ruling 6 of 2026-09-10, so the design is `production/art/mickeys-cars/`, not `production/art/atlas-01/MICKEYS.md` on `origin/art/atlas-01`, which D17 supersedes for the trade while its siting, two bays and fascia stand. |
| 4 | People on the street | next | People on the street with varied bodies, not one body repeated, in a frame. |
| 5 | A face that moves and a voice | later | One face that moves and one voice, per decision record D2. |
| 6 | Mickey's enterable | later | He can walk in through the door he saw from the street, into the cab office drawn in `production/art/mickeys-cars/`: the waiting room, the counter and the speaking gap, with the drivers' room beyond it that the public never enters. |
| 7 | Your thirty-minute dry run | later | You play for thirty minutes. The four conditions of the Meridian Test are read off that session and nothing else. |

## The rule about the rungs

A RUNG IS CLEARED BY YOUR EYE, NOT BY A GATE. Every rung above describes a
picture or a session, and the studio's numbers exist to tell us whether the
picture is worth sending, never to declare the rung passed. CLAUDE.md rule 4 is
the reason: a green number may not stand in for the frame it claims to describe.

ONE RUNG AT A TIME, and the art line takes at most a quarter of the week's
points (ruled 2026-09-08, carried 2026-09-09). The crime, gossip and memory work
continues underneath on the rest.

A RUNG NEVER MOVES BACKWARDS QUIETLY. If a later landing breaks a cleared rung,
the row goes back to `current` and the reason is written into the row, because a
ladder that only climbs is a ladder that lies.


## The phases, and the exit gate each one gets out on

Folded in from `ledger-v2/respec/roadmap-v2.md` on 2026-09-10, where these rows
were the whole plan from the respec of 2026-08-31. A gate here is a measurement,
not an opinion, and the phase is not done until the gate reads true.

ROW LAW, carried with the rows: a milestone stays under 80 words, carries an
instrument link and a verified date, and detail lives in a milestone file. THE
LAW IS NOT MET AND NOTHING MEASURES IT. Counted by hand on 2026-09-05, whole
row: R 18 words, phase 0 39, 1 70, 2 68, 3 49, 4 44, 5 22, 6 22, worst 70 of 80;
0 of 8 rows carries an instrument link or a verified date. `tools/docs-check.py`
walks `game-design/` only and no tool reads a doc-decay rule, so the cap above is
a hand count and not a gate. The checker is a queued process item,
`production/queue/107-the-row-law-nothing-enforces.md`.

- **Phase R, respec landed, canon written and approved.** Exit gate: Jafar
  approves `canon.md` and the respec package.
- **Phase 0, studio v2 scaffold; D1 engine probe; one assembly line piloted
  (dialogue bank); judge calibration.** Exit gate: D1 decision recorded with
  measurements; the pilot line yields a verified piece; judge agreement at or
  above the threshold in `ledger-v2/studio-v2/verification.md`.
- **Phase 1, the engine of consequence: Core on the chosen engine (perception,
  memory, gossip, schedules, save), largely transliteration guarded by the
  existing test suite.** Exit gate: the gossip instrument green, a witnessed
  crime reaching a second and a third NPC within one in-game week; the sim
  holding frame budget at target resident count; Core tests passing; and arrest
  reachable from live play, meaning the arrest outcome's callers outside Core
  counted and printed, not zero.
- **Phase 2, a street that lives:** one street at the visual bar; kit and decal
  density; moving faces; the live voice loop; the Ledger (D12); a
  what-they-know HUD for law enforcement in wanted states only; petty crime
  verbs; the witness-to-phone-box chase; 30 to 50 residents. Exit gate: Jafar's
  feel check passed; the screenshot bar met per D7 judges; conversation latency
  within budget; and the phase carrying a time budget set at kickoff.
- **Phase 3, the town:** full Phase A scope; interior tiers; economy and cash;
  factions; narrative v2; radio, TV and the brand bible; venues. Exit gate: the
  hours-of-content instrument; the repetition blind test passed, no detectable
  line repetition in a two-hour session; Meridian Test conditions 2 and 3
  sampled.
- **Phase 4, fists:** melee combat, improvised weapons, scarce firearms as
  events. Exit gate: Core combat resolving a blow from a call site outside Core,
  callers counted and printed, in a landed run; a feel check; and a gunshot
  producing a measured town-wide perception event.
- **Phase 5, the region:** Phase B land, driving, traffic. Gated on 3 and 4;
  gates set at kickoff.
- **Phase 6, ship-prep,** deferred until the quality bar is met. Exit gate: the
  Meridian Test, all four conditions.

STANDING RULE, carried with the rows: every phase with a taste gate also gets a
time or attempt budget at kickoff, set while calm. M17.10's lesson, instrumented
phases and bounded milestones.

TWO GATES WERE REPAIRED ON 2026-09-05 AND THE REPAIR IS WHY TWO ROWS READ AS
THEY DO. Phase 4's gate used to read "combat runs and is called from live play",
which the walk loop already satisfied through `Combat.StaminaAfterMoving` at
`Game/PlayerController.cs:399`, the one Core combat method with a caller outside
Core, and it is the stamina term: the gate could not tell a fight from a walk, so
it now names a resolved blow. Phase 1's gate did not see arrest, and
`CoatHost.Arrested` had no callers, so the gate would have gone green with the
consequence spine's terminal state unreachable: it now names arrest. Both are a
director's call on an approved package and Jafar reverts either on one word.
Ruling: `game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md`.

## How many systems each phase carries: read it, never copy it

The phase rows used to carry a per-phase count of
`production/systems-inventory.json`. THOSE CELLS ARE GONE AND ARE NOT REPLACED BY
HAND. They existed only because somebody copied the validator's printed `byPhase`
line into a table, and they went stale inside a day, twice: the file moved from
27 entries to 69 on 2026-09-09 and from 69 to 91 on 2026-09-10. A plan carrying
a hand-copied census is a plan that lies about its own size.

Read it through the validator, never around it. A refused inventory exits
non-zero and emits nothing, so a broken file cannot be read as a plan:

    python3 tools/systems-inventory-check.py --emit-json > inv.json
    python3 -c "import json;[print(e['phase'],e['status'],e['name']) for e in json.load(open('inv.json'))]" | sort

AND THE STATUS IT PRINTS IS NOT A GATE READING. Jafar ruled on 2026-09-09 that
status on that page is a TYPED JUDGEMENT, attributable to a person and a date and
changed by a ruling rather than by a grep; `exists` no longer means that a path
resolves. The standard the typing follows: a tile is green only if the thing its
name promises can happen to a player in a build that exists today. So a count of
`exists` is a reading of somebody's judgement, never a gate reading, and never a
floor a gate may stand on. Ruling:
`game-design/decision-2026-09-09-ruling-typed-systems-inventory.md`.

## The Meridian Test, which is the last gate of all

COPIED, NOT AUTHORED HERE. The source is
`ledger-v2/respec/vision-pillars-v2.md`, and `tools/goal-block-check.py`, run by hand
(nothing calls it yet; see the wiring item), checks that the copy in
`CLAUDE.md` matches that source. IT DOES NOT CHECK THIS COPY.
If this one and the source ever differ, the source wins and the difference is a
bug in this file.

The goal is met when all four hold:

1. A person who loves GTA or KCD2 plays 30 minutes and does not bounce off the
   visuals.
2. Within those 30 minutes the world visibly knows them at least once:
   recognized, gossiped about, or confronted with something they did earlier.
3. They describe the town as alive without being prompted.
4. Jafar, on a free evening, chooses playing LEDGER over replaying KCD2.

Rung 7 above is where those four get read, off one session and nothing else.

## The fold of 2026-09-10: what folded in, and what could not move

Jafar ruled one plan in the cleanup batch of 2026-09-10: this file plus
`production/queue/`. What folded in, and what did not:

- `ledger-v2/respec/roadmap-v2.md` FOLDED IN and STAYED AT ITS PATH. Its phase
  rows and their exit gates are above, and its stale systems column is replaced
  by the validator command above. The file could not move under `legacy/`
  because `CLAUDE.md` line 133 names it as the plan and `.claude/agents/planner.md`
  line 3 tells the planner to decompose its milestones, and a separate lane owns
  both of those files. `tools/dashboard/build-dashboard.py` also parses its phase
  table (`SOURCES["roadmap"]`, and `parse_roadmap`). So the file keeps its path
  and now carries a banner saying the plan is here.
- `production/quality-ladder.md` STAYED IN PLACE, unfolded, and it is not a
  second plan. It is the close-question instrument of this one: before an item
  closes, is this the best available result or the first working one. `CLAUDE.md`
  line 205 names it as the place that question is asked, so it cannot move
  either.
- `game-design/queue.md` was already retired and is not touched.
  `tools/queue-check.py` prints `retiredNotRead=game-design/queue.md`.
- `production/week-plan.md` was already gone.
