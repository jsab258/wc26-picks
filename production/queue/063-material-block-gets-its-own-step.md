line: infrastructure (the Unreal workflow)
spec: game-design/decision-2026-09-03-texture-staging-and-the-still-gate-ratchet.md, ruling C and E
acceptance: tools/workflow-size.py prints BOTH blocks under the watermark AND a landed run still carries materialStatus into ue-build.txt; plus materialScriptMinutes measures the script rather than the editor process
max_sessions: 1
status: READY 2026-09-03. engine-specialist, small. BINDING: this is the NEXT edit to that run block, ahead of any other change to it.

## Why it is next and not now

The build block has 17 characters of headroom under the measured watermark.
The ruling establishes that this is headroom against the largest block ever
ACCEPTED (23184 in tools/workflow-size.py line 51), not against a cliff, and
the block is at a size that has already shipped. So run 20 goes first, because
splitting first would route a whole run's evidence through a step nobody has
ever dispatched.

But the bound does not move. No further character goes into that block. If run
20's read-out demands an edit there, THIS ITEM LANDS FIRST.

The block reads `$ue`, `$buildBat`, `$proj` and appends to `$L`, all
step-local, so the split is mechanical rather than a redesign.

## Folded in: materialScriptMinutes measures the wrong thing

The timer at workflow line 304 wraps the `UnrealEditor-Cmd` process, so it
measures editor startup plus the script while its name claims the script. Same
mislabel class as `materialScriptExit`, which run 19 exposed and this batch
renamed. One rename or one re-placement once the step boundary exists, and it
does not earn its own item.
