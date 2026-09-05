# Roadmap v2 (2026-08-31)

Row law: each milestone row stays under 80 words, carries an instrument link and a verified date; detail lives in a milestone file; landed rows move to roadmap-history. Rows over the cap, or stale against code changes touching their area, fail the doc-decay gate.

| Phase | Milestone | Exit gate (instrumented) | Systems carried (production/systems-inventory.json, verified 2026-09-05) |
|---|---|---|---|
| R | Respec landed, canon written and approved | Jafar approves canon.md and this package | 0 of 27, by design |
| 0 | Studio v2 scaffold; D1 engine probe; one assembly line piloted (dialogue bank); judge calibration | D1 decision recorded with measurements; pilot line yields a verified piece; judge agreement at or above threshold in studio-v2/verification.md | 1 of 27: 1 partial |
| 1 | Engine of consequence: Core on chosen engine (perception, memory, gossip, schedules, save), largely transliteration guarded by the existing test suite | Gossip instrument green: witnessed crime reaches a second and third NPC within one in-game week; sim holds frame budget at target resident count; Core tests pass; arrest reachable from live play: the arrest outcome's callers outside Core counted and printed, not zero | 3 of 27: 2 exists, 1 partial |
| 2 | A street that lives: one street at the visual bar; kit and decal density; moving faces; live voice loop; the Ledger (D12); what-they-know HUD only for law enforcement in wanted states; petty crime verbs; witness-to-phone-box chase; 30 to 50 residents | Jafar feel check passed; screenshot bar met per D7 judges; conversation latency within budget; phase has a time budget set at kickoff | 7 of 27: 7 exists |
| 3 | The town: full Phase A scope; interior tiers; economy and cash; factions; narrative v2; radio, TV and brand bible; venues | Hours-of-content instrument; repetition blind test passed (no detectable line repetition in a 2-hour session); Meridian Test conditions 2 and 3 sampled | 4 of 27: 3 partial, 1 absent |
| 4 | Fists: melee combat, improvised weapons, scarce firearms as events | Core combat resolves a blow from a call site outside Core, callers counted and printed, in a landed run; feel check; a gunshot produces a measured town-wide perception event | 2 of 27: 2 partial |
| 5 | The region: Phase B land, driving, traffic | Gated on 3 and 4; gates set at kickoff | 1 of 27: 1 partial |
| 6 | Ship-prep (deferred until quality bar met) | The Meridian Test, all four conditions | 9 of 27: 4 exists, 3 partial, 2 absent |

Standing rule: every phase with a taste gate also gets a time or attempt budget at kickoff, set while calm. M17.10's lesson: instrumented phases, bounded milestones.

## The systems column: what it counts, and what it does not

A whole-file census of `production/systems-inventory.json` on 2026-09-05,
grouped by its `phase` field, against the 27 names pinned in queue 098. The
eight cells sum to 27 of 27, so every system names a row and every row can
say what it carries. Phase R carries 0 by design: it is the respec and holds
no player-facing system. The column is a hand census, counted twice
(planner and director) and dated; nothing yet checks it against the file,
which is the queued row-law checker's job.

Read the entries through the validator, never around it. A refused
inventory exits non-zero and emits nothing, so a broken file cannot be read
as a plan:

    python3 tools/systems-inventory-check.py --emit-json > inv.json
    python3 -c "import json;[print(e['phase'],e['status'],e['name']) for e in json.load(open('inv.json'))]" | sort

IT IS NOT A GATE READING. `exists` means a path resolves and, where a token
is given, that token is in it. A token in a comment satisfies it. It does
not mean the row's milestone clause is met: phase 2 counts 7 of 7 as exists
while its own what-they-know HUD clause is not among them, as the HUD
entry's note says. A count of `exists` is a floor under a phase, never a
gate reading for it.

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
