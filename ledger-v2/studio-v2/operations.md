# Operations: Jafar interface, sessions, tokens

## Jafar interface (the whole surface)
1. Weekly brief (or per burst): one page: landed, in flight, blocked, numbers (throughput, budgets, judge agreement), next.
2. Decision queue: non-technical calls only, each a card: question, options, recommendation, consequence, deadline-if-any. Everything else is decided downstream and recorded.
3. Playtest requests: a build plus a 15-minute script of what to feel-check.
4. One-click runs: any local generation need ships as a .bat that is idempotent, non-interactive, logs to a file, writes outputs to a known folder, and prints DONE or the failure. Nothing that needs Jafar to babysit.

## Session and brief rules (paid for by named failures, research/waste-lessons.md)
1. One brief, one deliverable. Multi-deliverable briefs are rejected at spec.
2. Turn ceilings generous, with resumable state: every long-running agent writes a state file it can resume from; running out of turns costs a resume, not the work.
3. Standing constraints live in agent definitions, never in briefs.
4. Per-agent namespaced scratch directories; no shared scratchpad files.
5. Branch or worktree per agent; a single integrator role merges. No commit-gate serialization of parallel work.
6. Context hygiene: agents read schemas and slices, not the repo; readers get file paths plus line ranges where known.
7. Autonomous operation runs as a loop of disposable headless sessions per studio-v2/runner.md. Manual /clear discipline applies to interactive human sessions only; the runner never needs it.

## Phase exit checklist (a phase is not closed until all four hold)
1. The phase's exit gate, as instrumented in roadmap-v2.md, is green.
2. Phase-exit retrospective held: what cost more than it should, what a
   gate missed, what a person had to catch. Findings enter through
   learning.md like every other lesson and terminate the same four ways.
3. HARVEST executed per learning.md: portable lessons distilled into
   game-studio (frozen otherwise, D10), committed to its main naming the
   phase, diff summarized in the morning brief, README status line updated.
4. The weekly process audit (production/queue/900) is clean or its
   violations are queue items.

The lessons pipeline, the harvest mechanics and the terminated-lessons
index live in learning.md; that file is the front door to how this studio
learns.

## Token economics
1. Ledger: production/token-ledger.md records per-department spend estimates per week and escalations to top models with reasons.
2. Routing law as in organization.md; violations are audit findings.
3. Bulk content only in batches with fixed specs; cache and reuse prompts; never regenerate what a verifier can repair.
4. Roadmap and canon stay small enough to be cheap to read every session (row caps, 600-word canon).
