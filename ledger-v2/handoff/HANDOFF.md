# HANDOFF: LEDGER v2 boot instructions for the Claude Code session

Date: 2026-08-31. Origin: claude.ai planning session with Jafar. Authority: this package supersedes all prior roadmaps, design docs and specs in this repo. Legacy documents become inputs, not law.

## Read order (mandatory, before any work)
1. handoff/canon-task.md, then produce canon.md at repo root
2. respec/vision-pillars-v2.md
3. respec/scope-v2.md and respec/roadmap-v2.md
4. respec/decision-register/ (D1 to D7)
5. studio-v2/ (all six files, runner.md included)
6. research/waste-lessons.md and research/license-allowlist.md
7. respec/reference-extraction.md and research/ summaries as needed

## Repo migration (first commit)
1. Create legacy/ and move the old roadmap.md, design-doc.md and superseded specs into it with a SUPERSEDED header pointing here. Do not delete anything.
2. Keep: the deterministic Core and its test suite (behavioral definition of the sim), the voice pipeline and 2,010 clips, agent-reports/, roadmap-history.md, all writing as raw material.
3. Update CLAUDE.md to point at this package as the source of truth and to enforce research/license-allowlist.md and the formatting law (no em-dashes, no italics).

## First five tasks (Phase 0)
1. Write canon.md per handoff/canon-task.md. List conflicts, do not silently resolve them.
2. Stand up the studio-v2 scaffold: agent role definitions with standing constraints baked in, per-agent namespaced scratch dirs, branch-per-agent with an integrator role, the token ledger file, and the overnight runner per studio-v2/runner.md (queue, dispatch prompt, loop script, hooks, kill switch).
3. Kick off D1, the engine probe, exactly as specified in respec/decision-register/D1-engine-probe.md. Two-week timebox. Record the decision with measurements.
4. Run one content assembly line end to end as a pilot (dialogue bank for one NPC archetype): spec, author, verify, integrate, record. Request a judge calibration sample from Jafar (30 to 50 items).
5. Produce the first weekly brief for Jafar in the operations.md format, including the decision queue.

## Jafar actions
1. Commit this package to the repo root as ledger-v2/ (or merge its contents at root, your call, record which).
2. (Done, nothing to export: both full research reports are already in research/full/.)
3. Answer the judge calibration sample when the session requests it.
4. Approve or amend canon.md when presented.
