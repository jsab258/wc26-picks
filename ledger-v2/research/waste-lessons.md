# Waste lessons (extracted 2026-08-31 from agent-reports/process-faults-25aug.md, both CLAUDE.md files, roadmap-history.md)

Each lesson is now an operating rule in studio-v2/operations.md. Named failures, kept so nobody relearns them at full price.

1. maxTurns ceilings too tight: four parallel agents, about 398k tokens, zero delivered on first pass, several stopped one step short of done. Rule: generous ceilings, resumable state files, one deliverable per brief.
2. Standing constraints retyped into every brief. Rule: constraints live in agent definitions.
3. Multi-deliverable briefs caused partial delivery counted as none. Rule: one brief, one deliverable.
4. Shared scratchpad filename collisions corrupted outputs (including a commit message). Rule: per-agent namespaced scratch.
5. Single-writer commit gate fought multi-agent work. Rule: branch per agent, integrator merges.
6. Giant stale roadmap rows re-read at top-model prices; rows drifted for weeks; audits, not the plan, found 17.6 to 17.9. Rule: 80-word row cap, verified dates, doc-decay gate, history file on landing.
7. Top-model usage for mechanical work. Rule: routing law plus token ledger with recorded escalations.
8. Decisions living only in session memory (the era drift caught 2026-08-31). Rule: canon.md plus decision records; anything decided verbally gets written the same day.
