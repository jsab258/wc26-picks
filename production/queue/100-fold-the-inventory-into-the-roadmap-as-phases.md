line: production (the plan)
spec: production/NOW.md, "JAFAR'S STANDING ORDER, 2026-09-05", item 4, third part
acceptance: every phase value used in the inventory names a row that exists in ledger-v2/respec/roadmap-v2.md, printed as phasesCovered=N/M with any orphan phase named; every inventory entry carries a phase, with any deliberately unassigned entry listed by name and counted rather than left blank; `python3 tools/docs-check.py` stays green with every roadmap row under the 80-word cap, measured after the edit; a planted entry with a phase that names no row FAILS the check, and a planted row pushed over 80 words fails docs-check, both shown; the diff is reviewed by a director before commit because it touches the roadmap
max_sessions: 1
status: READY 2026-09-05. Item 4 part three, and the LAST studio item of the week under the standing rule. planner or systems-builder, with a director review before it lands.

## What the fold is, and what it is not

The inventory already carries a phase per system. The fold makes that field
mean something: every phase it uses must be a real roadmap row, and every
roadmap row must be able to say which systems it carries.

IT IS NOT 27 NAMES PASTED INTO A TABLE. The row law in roadmap-v2.md caps each
milestone row at 80 words, requires an instrument link and a verified date, and
fails the doc-decay gate when a row grows or goes stale. So the roadmap points
at the inventory, filtered by phase, and the detail stays in the data file
where a machine can read it.

The rows that exist today are R, 0, 1, 2, 3, 4, 5 and 6. If the inventory needs
a phase those rows do not offer, that is a finding for the director, not a new
row invented in a builder pass.

## The escalation is mechanical and it is not optional

CLAUDE.md's escalation list names anything touching premise, roadmap or
CLAUDE.md. This task touches the roadmap, so a director is spawned to review
the diff before it commits, and the ruling is a decision record under
`game-design/` carrying its RULING stamp. A builder that lands this without one
has broken the cadence gate, not tidied a document.

## What the ruling has to answer

Which systems moved phase and why, in one line each. A fold that quietly
reschedules half the player-facing surface is a plan change wearing the clothes
of a data entry task. The set that moved is small enough to list, and if it is
not, that is itself the finding.

## Both halves, accepting first

Accepting: the check over the live inventory and the live roadmap prints
`phasesCovered=N/M` with no orphans, and docs-check is green with every row's
word count printed.

Rejecting, two planted cases: an inventory entry whose phase names no row,
which must fail with that entry named; and a roadmap row edited over the cap,
which must fail docs-check. The second matters because the fold's obvious
failure mode is a row that grows a list.

## Depends on, and what it blocks

Depends on queue 098 for the phase field. Blocks nothing in the queue, but the
standing rule says that when item 4 lands THE STUDIO STOPS BUILDING STUDIO THIS
WEEK, so this item is the boundary: anything process-shaped after it goes to
the queue and waits.
