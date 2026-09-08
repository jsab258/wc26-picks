---
description: Rules for CI workflows and anything that runs on or reads from the build pipeline
globs: [".github/workflows/**", "**/ci/**", "tools/*dispatch*", "tools/*landed*"]
---

# CI and the feedback channel

- **When something is SILENT, run the existing entry point on the machine
  and read its output before proposing a mechanism.** Ruled by Jafar
  2026-09-08. On the night of 7 September the studio produced four
  explanations for a silent Telegram channel, and every one was refuted by a
  single measurement that could have been taken first: the bot is dead
  (refuted by uptime), the poll loop is wedged (by a clean restart that
  changed nothing), the credentials refuse writes (by `pushDryRunExit=0`),
  the work sits downstream of the poll (by fixing it, loading it, and still
  silence). The answer came from running `--send-outbox` once, an entry
  point that already existed. A fifth guess was then made in the opposite
  direction from four receipts when sixteen were available. THE ENTRY POINT
  IS CHEAPER THAN THE ARGUMENT, and it answers rather than narrows.

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

**Where these came from.** The incidents are
`ledger-v2/studio-v2/casebook-build-and-evidence.md`, which carries CLAUDE.md
rule 12 and the project mechanics in full: the compile errors a
reference-independent check cannot see and the five lints written for them,
the licence-seat failure that looks exactly like a compile error, the build
that committed stills it could not have rendered, the container rollback, and
the verdict-format rules. Read it before diagnosing a build from its colour.
