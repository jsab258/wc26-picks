---
description: Rules for CI workflows and anything that runs on or reads from the build pipeline
globs: [".github/workflows/**", "**/ci/**", "tools/*dispatch*", "tools/*landed*"]
---

# CI and the feedback channel

- **The evidence channel is a file committed by CI** — stills, a
  `key=value` verdict naming its commit on line 1, per-run copies keyed by
  short-sha. Log tails, step summaries and artifact hosts have all failed;
  a committed file has not.
- **Verify a job's EFFECTS, not its exit code.** Jobs have reported
  success while deleting content, pushing nothing, and truncating their
  own logs.
- **A run that measured nothing must say so** (`NO RUN`) and must not
  carry forward the previous run's files under its own name — "the build
  carried the commit" and "the build measured anything" are different
  facts.
- **Stage outputs by NAME, never `git add <directory>`** — a failed run
  otherwise commits its stale checkout's files as its own evidence.
- **Watch by ancestry** (`is there a landed run whose commit CONTAINS
  mine`), never by branch movement or run name; capture the sha BEFORE
  dispatching. Dispatch takes a branch, and the runner checks out whatever
  it points at when it starts.
- **Expensive jobs are opt-in** (`workflow_dispatch`); concurrency groups
  scope to the expensive job only; cheap checks never queue behind a
  stream. Know what your pushes trigger.
- **Batch changes per dispatch** — the round trip costs the same carrying
  one change or six — and respect the project's stated concurrency limit
  (licence seats and shared runners fail SILENTLY in the only channel you
  can read).
- **Any cap in a log-extraction step must announce when it bites** — a
  `| head -N` that outgrew its input once read as "three of five systems
  failed" when nothing was broken.
