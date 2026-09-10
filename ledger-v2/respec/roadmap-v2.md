# Roadmap v2 (2026-08-31)

FOLDED 2026-09-10, AND THIS IS NOT THE PLAN ANY MORE. Jafar ruled one plan in
the cleanup batch of 2026-09-10: `production/ladder.md` plus
`production/queue/`. The phase rows below and their exit gates were copied into
`production/ladder.md` under "The phases, and the exit gate each one gets out
on", which is where they are now maintained. Change a gate THERE.

WHY THIS FILE STILL EXISTS AT THIS PATH rather than under `legacy/`. Three live
readers name it and two of them belong to a lane this batch may not touch:
`CLAUDE.md` line 133 calls it the plan, `.claude/agents/planner.md` line 3 tells
the planner to decompose its milestones, and
`tools/dashboard/build-dashboard.py` PARSES the phase table below
(`SOURCES["roadmap"]` at line 417, read by `read_phases` at line 577 and parsed
by `parse_roadmap` at line 311, all measured 2026-09-10) to derive the current
phase for the dashboard. Moving the file would break all three, so the
path stays and the table stays parseable. When CLAUDE.md and the planner brief
are repointed, this file can move and the dashboard source moves with it.

Row law: each milestone row stays under 80 words, carries an instrument link and a verified date; detail lives in a milestone file; landed rows move to roadmap-history. Rows over the cap, or stale against code changes touching their area, fail the doc-decay gate.

| Phase | Milestone | Exit gate (instrumented) | Systems carried (READ IT, NEVER COPY IT: see below) |
|---|---|---|---|
| R | Respec landed, canon written and approved | Jafar approves canon.md and this package | read the validator |
| 0 | Studio v2 scaffold; D1 engine probe; one assembly line piloted (dialogue bank); judge calibration | D1 decision recorded with measurements; pilot line yields a verified piece; judge agreement at or above threshold in studio-v2/verification.md | read the validator |
| 1 | Engine of consequence: Core on chosen engine (perception, memory, gossip, schedules, save), largely transliteration guarded by the existing test suite | Gossip instrument green: witnessed crime reaches a second and third NPC within one in-game week; sim holds frame budget at target resident count; Core tests pass; arrest reachable from live play: the arrest outcome's callers outside Core counted and printed, not zero | read the validator |
| 2 | A street that lives: one street at the visual bar; kit and decal density; moving faces; live voice loop; the Ledger (D12); what-they-know HUD only for law enforcement in wanted states; petty crime verbs; witness-to-phone-box chase; 30 to 50 residents | Jafar feel check passed; screenshot bar met per D7 judges; conversation latency within budget; phase has a time budget set at kickoff | read the validator |
| 3 | The town: full Phase A scope; interior tiers; economy and cash; factions; narrative v2; radio, TV and brand bible; venues | Hours-of-content instrument; repetition blind test passed (no detectable line repetition in a 2-hour session); Meridian Test conditions 2 and 3 sampled | read the validator |
| 4 | Fists: melee combat, improvised weapons, scarce firearms as events | Core combat resolves a blow from a call site outside Core, callers counted and printed, in a landed run; feel check; a gunshot produces a measured town-wide perception event | read the validator |
| 5 | The region: Phase B land, driving, traffic | Gated on 3 and 4; gates set at kickoff | read the validator |
| 6 | Ship-prep (deferred until quality bar met) | The Meridian Test, all four conditions | read the validator |

Standing rule: every phase with a taste gate also gets a time or attempt budget at kickoff, set while calm. M17.10's lesson: instrumented phases, bounded milestones.

## The systems column: why its cells no longer carry a number

THE PER-PHASE CELLS ARE GONE AND ARE NOT REPLACED BY HAND. They were a whole-file
census of `production/systems-inventory.json` copied by hand from the validator's
printed `byPhase` line, and they went stale inside a day, twice: the file moved
from 27 entries to 69 on 2026-09-09 and from 69 to 91 on 2026-09-10, measured by
`python3 tools/systems-inventory-check.py`, which printed `accepted
problems=0/checks=2594` on the 91-entry file. Every cell that read "of 69" was
therefore false within hours of being written. A plan carrying a hand-copied
census is a plan that lies about its own size, so the cells now say to read the
validator.

Read the entries through the validator, never around it. A refused inventory
exits non-zero and emits nothing, so a broken file cannot be read as a plan:

    python3 tools/systems-inventory-check.py --emit-json > inv.json
    python3 -c "import json;[print(e['phase'],e['status'],e['name']) for e in json.load(open('inv.json'))]" | sort

IT IS NOT A GATE READING. Jafar ruled on 2026-09-09 that status on that page is a
TYPED JUDGEMENT, attributable to a person and a date and changed by a ruling
rather than by a grep; `exists` no longer means that a path resolves. The standard
the typing follows: a tile is green only if the thing its name promises can happen
to a player in a build that exists today. So a count of `exists` is a reading of
somebody's judgement, never a gate reading, and never a floor a gate may stand on.
Ruling: `game-design/decision-2026-09-09-ruling-typed-systems-inventory.md`.

## The fold of 2026-09-05: two gates repaired, four findings open

Ruling: `game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md`.
No row's phase value moved, 0 of 27.

REPAIRED. Phase 4's gate read "Combat runs and is called from live play" and
was already met, before phase 1, by the walk loop: `Ledger.Core.Combat.StaminaAfterMoving`
is called at `Game/PlayerController.cs:399`, the one Core combat method with
a caller outside Core, and it is the stamina term. The gate could not tell a
fight from a walk, so it now names a resolved blow. Phase 1 is the engine of
consequence and its gate did not see arrest: `CoatHost.Arrested` has 0
callers (2 occurrences in the tree, the definition and a comment in
`Core/Homicide.cs` recording the absence), so the gate would go green with
the consequence spine's terminal state unreachable. It now names arrest.
Both are a director's call on an approved package; Jafar reverts either on
one word.

OPEN, recorded and not repaired:

1. Phase 4 sizes combat as unwritten work. `Core/Combat.cs` is written (Blow,
   Fighter, BlowResult, FightWitness, Resolve, Available, StaminaCost) and the
   inventory scores it partial. The open work is call sites, not design.
2. Phase 6 is five words and carries 9 of 27 systems, more than any row,
   including 2 of the 3 absent (gamepad, photo mode) and the local-LLM half
   of graphics settings. Its gate, the Meridian Test, measures none of the
   nine. Whether ship-prep requires every phase-6 system to read exists is
   Jafar's call and is not made here.
3. Phase 3 names seven items and map and minimap is not one; the inventory
   schedules it into phase 3 with zero code and blocker D12. The row waits on
   D12.
4. The row law above demands an instrument link, a verified date and an
   80-word cap per row. 0 of 8 rows carries a link or a date, and nothing
   measures any of it: `tools/docs-check.py` walks `game-design/` only, and no
   tool reads "doc-decay". Counted by hand for this edit, whole row: R 18,
   0 39, 1 70, 2 68, 3 49, 4 44, 5 22, 6 22; worst 70 of 80. Before the fold:
   13, 34, 47, 63, 42, 28, 17, 13. The checker is a queued process item and
   waits, by the standing rule, until the studio builds studio again.


## The typed contract of 2026-09-09

Ruling:
`game-design/decision-2026-09-09-ruling-typed-systems-inventory.md`. The
inventory moved from 27 entries to 69 and from an evidenced status to a
typed one; the systems column above was re-read from the new census on
2026-09-09. The fold section above is the record of 5 September and its
arithmetic was true of the 27-entry file, so it is not re-counted here.
Its sentence about `Arrested` having 2 occurrences is still true as
scoped: 2 under `ledger/Assets/Scripts`, 3 under `ledger/`, 0 callers in
both readings.
