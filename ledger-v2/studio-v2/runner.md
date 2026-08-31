# The Runner: autonomous multi-session operation (overnight and beyond)

Principle: sessions are disposable workers, the repo is the memory, a night is a loop of fresh sessions. No session should ever live long enough for auto-compaction to matter; process exit replaces /clear. Jafar never manages context.

## Components (built during the Phase 0 scaffold)

1. Work queue. production/queue/ holds task files NNN-slug.md, each with: pipeline/line, spec reference, acceptance checks, max_sessions. Folder is the state machine: queue/ to active/ to done/ or blocked/. A planner session decomposes roadmap milestones into queue tasks; tasks obey the one-brief-one-deliverable law.
2. Dispatch prompt. tools/runner/dispatch.md, fixed text: read CLAUDE.md, canon.md, current roadmap state and your task file; do the one task; verify against the gates; commit on the night branch; move the task file to done/ with a result note (or blocked/ with a reason); update your resumable state file if unfinished and enqueue a continuation task pointing at it; then exit. Never wait for input.
3. Loop script. tools/runner/run-night.ps1 (plus a run-night.bat wrapper for one click): while queue non-empty, launch claude -p with the dispatch prompt, generous --max-turns, logging each iteration to production/logs/night-YYYYMMDD/. Caps: max iterations, wall-clock limit, and a STOP file checked between iterations as the kill switch.
4. Failure policy. Two consecutive failures on the same task move it to blocked/ with the logs linked; the loop moves on. Blocked items surface in the morning brief, never silently retried all night.
5. Git discipline. Each night runs on branch night/YYYYMMDD (worktrees if agents run in parallel). An integrator task at the end of the queue merges only what passes CI and the standing gates. Main is never written directly by the runner.
6. Continuation, not compaction. A task too big for one session writes its state file and re-enqueues a continuation. Compaction is a backstop only: SessionStart hook rehydrates canon plus roadmap plus task state; PreCompact hook dumps session state to a file first. If PreCompact fires more than rarely, the tasks are cut too large; fix the planner, not the window.
7. Permissions. .claude/settings.json pre-approves the runner's tool allowlist so nothing prompts interactively. The runner may never: delete outside the repo, force-push, touch main, spend above the night budget, or reach network destinations beyond the configured allowlist.
8. Morning brief. The final queue item every night generates the brief and the decision queue per operations.md. Jafar wakes to: landed, blocked, numbers, decisions needed.

## Sizing rule
Tasks are sized so a typical session finishes one comfortably inside its turn cap. When in doubt, cut the task smaller; many small verified pieces beat one large unverified one, and the throughput ledger counts verified pieces anyway.

## Brief delivery and the guarantee chain
Reporting never depends on the health of what it reports on, and the default needs nothing outside this machine.
1. Rich brief: the final queue task (LLM) writes production/briefs/night-YYYYMMDD.md per operations.md.
2. Fallback brief: if that session fails, the loop script composes a mechanical brief with zero model calls: queue folder counts (done, blocked, untouched), night-branch git log, gate results, token ledger, tail of the last failing log.
3. Exit-path delivery (runs on success, failure, or kill switch): write the brief, copy it to production/briefs/latest.md, fire a Windows toast if the machine is awake.
4. Morning surfacing: the SessionStart hook prints the latest brief when Jafar opens Claude Code, unprompted.
5. Scheduling: the scaffold registers Windows Task Scheduler entries (via schtasks) for the nightly runner start at a configured time, so nights need no manual trigger. run-night.bat stays as the manual option; the STOP file stays as the kill switch. Claude Code writes and registers these; Windows executes them.
Optional escalations, off by default, each set up once if ever wanted: email delivery (one SMTP call in the exit path, credentials in the uncommitted tools/runner/config.local) and off-machine dead-man alerting for the PC-died-overnight case (a single ping to healthchecks.io or a self-hosted n8n webhook; the service alerts on silence by 07:00).
Worst case by design is never a missing brief; it is a fallback brief, or a machine you can see is off.
