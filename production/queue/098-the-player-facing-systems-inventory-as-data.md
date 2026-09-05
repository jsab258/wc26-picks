line: production (the plan)
spec: production/NOW.md, "JAFAR'S STANDING ORDER, 2026-09-05", item 4, first part
acceptance: one machine-readable inventory file where every entry carries all six ruled fields with values from the fixed sets, and its validator prints entries=N namesFromOrder=27 covered=27/27 naming any name with no entry; an entry whose status is exists or partial and whose evidence path does not resolve in this checkout is REFUSED, as is an entry whose area, status, class or phase is not in the fixed set, both proven with planted entries; an empty or unreadable inventory makes the validator print the words "nothing measured" rather than passing; and the validator is called by `python3 ledger/verify.py` so the file cannot rot silently
max_sessions: 1
status: READY 2026-09-05. Item 4 part one, and 099 and 100 both wait on it. instrument-builder or systems-builder.

## The names, carried here so nobody re-derives them

Copied from item 4 of the standing order. Counted by splitting that sentence on
its commas: TWENTY-SEVEN names. The brief that commissioned this task said 28,
and the discrepancy is recorded rather than resolved by adding one: if a name
is missing it is added by Jafar or a director, not by a builder making the
count fit.

The order says "At minimum", so the inventory may hold MORE entries than names.
It may never hold fewer.

1. the Ledger notebook
2. HUD
3. menus
4. controls
5. camera
6. first hour and tutorial
7. save and load
8. new game
9. settings
10. accessibility
11. subtitles
12. gamepad
13. pause
14. map and minimap
15. inventory
16. economy and trading
17. combat
18. music
19. SFX
20. audio mix
21. loading and streaming
22. failure states and autosave policy
23. time and calendar display
24. graphics settings including the local-LLM toggle
25. credits and attributions
26. photo mode
27. feedback path

## The six fields, ruled, with their fixed sets

    name      the name above, unchanged
    area      moat | world | player-facing | content | studio
    status    exists | partial | absent
    class     cheap-to-author | taste-bound | moat-adjacent
    phase     R | 0 | 1 | 2 | 3 | 4 | 5 | 6, from roadmap-v2.md
    blocker   what blocks it: a queue number, a decision, or the word none

## A seventh field, added here with its reason

`evidence`, REQUIRED when status is exists or partial. A status word with no
path is exactly the claim this project keeps being burned by: 37 props and 14
decals were counted as progress while `grep -c "base-mesh|BaseMesh"` returned 0
in both street scripts. So "exists" means a path that resolves, and the
validator proves it. Absent entries carry no evidence and must not fake one.

This is an addition beyond the six Jafar named, it is named as an addition
here, and a director may cut it. What may not happen is a status word that
nobody can check.

## Data, not prose, and that is the whole point

The file is read by the map view (queue 099) and by the roadmap fold (queue
100). Prose would have to be re-parsed by both, so the entries are structured
and the only prose is a one-line note per entry if it is needed.

## Both halves, accepting first

Accepting: the live inventory validates, and the validator prints the coverage
against 27 with any uncovered name listed by name.

Rejecting, three planted cases: an entry claiming `exists` whose evidence path
does not resolve; an entry with an area word that is not one of the five; and
an empty file, which must print "nothing measured" rather than passing on zero
problems found in zero entries. A zero with no denominator cannot tell nothing
from fine.

## Depends on, and what it blocks

Depends on nothing. Blocks queue 099 (the map view renders this data) and queue
100 (the roadmap fold reads the phase field). Research on the taste-bound
systems is coming separately from the planning session and is not part of this
task.
