# The watchdog prompt, kept where it can be checked

STATUS: LIVE. Verified 2026-09-01.

Trigger: `trig_01EA7ybQTcsiFyrTryptqVUi`, named "LEDGER watchdog (budget-aware,
v2 queue)". Cron `20 * * * *`, hourly. ENABLED 2026-09-01 16:00Z, after being
disabled since 26 August when Jafar put the project on a usage hold.

WHY THIS FILE EXISTS. The prompt lives in the trigger system, not in the tree,
so every claim about what the watchdog does was unverifiable from inside the
repository. A director review caught it: `production/budget.md` asserted "the
watchdog prompt points at it" and there was no artifact anyone could check.
That is a claim with no instrument, which is the fault this project's whole
rule set is built around, sitting inside the governance layer itself.

THE CONTRACT: when the prompt changes, this file changes in the same commit.
A prompt whose recorded copy is stale is worse than no copy, because it reads
as evidence.

Nothing outside this file can enforce that, and it is worth saying so rather
than implying a gate exists. It is a discipline, and the reason to trust it
slightly is that the alternative was already tried and failed today.

REVISED 2026-09-01 21:25Z, and the reason is this contract doing its job. The
prompt asserted "Jafar is over budget this week". The weekly limit reset, that
sentence became false, and it went on being read aloud every hour to the
session that governs everything else. A decayed claim inside the one
instruction every session obeys is the worst place this project has for one.

The repair is not a corrected figure, because a figure here would decay the
same way next week. The prompt now states NO budget number and NO
over-or-under judgement, and points at the dated file as the authority over
itself. An undated instruction cannot outrank a dated reading and no longer
tries to.

Also added: builders overrun. Three of four on 1 September needed a mid-flight
instruction to stop deepening and finish, which is a briefing fault rather
than an agent fault, so the scope ceiling belongs in the brief rather than in
a rescue message.

## The prompt as set, verbatim

WATCHDOG. Restart mechanism only. If work is genuinely in flight (a builder agent running, a build watcher live, a turn mid-task), note it and end quietly. Do not restart what is running.

BUDGET FIRST, BEFORE ANY WORK. Read `production/budget.md`. IT IS THE AUTHORITY AND THIS PROMPT IS NOT: it carries the reported readings as a dated series, the LEDGER ceiling, and four mechanical stop conditions. If a stop condition holds, write the brief, push, and END.

This prompt deliberately states NO budget figure and no over-or-under judgement. It used to say Jafar was over budget for the week; the weekly limit reset and that sentence became false while being read hourly, which is a decayed claim in the one instruction every session obeys. The file is dated, this prompt is not, so the file wins by construction.

Two things the file cannot say for itself. An unknown budget is not permission: with no reading newer than 48 hours, do only work that costs no model time. And a reading describes the moment it was taken, so when substantial work has happened since the newest one, treat the day as unmeasured and prefer stopping.

THEN READ `production/NOW.md` BEFORE THE QUEUE. It names what is already moving, what waits on Jafar, and the standing hazards. The queue says what to do next; NOW says what a fresh session would otherwise duplicate, abandon, or wait for forever. Keep it current as you work, or the next session inherits a lie.

THE QUEUE IS `production/queue/` (the v2 state machine: active, blocked, done). NOT game-design/queue.md, which the v2 respec superseded on 31 August.

THE STUDIO SPLIT IS MANDATORY, never judged, and it was skipped for an entire day on 1 September. The resident session coordinates: it reviews, commits, dispatches, and talks to Jafar. It does NOT implement. ALL implementation goes to tier-3 builders briefed "do not commit"; verification to the tier-2 read-only verifiers; and the `studio-director` agent is spawned at builder-batch review before commit, queue reordering or refill, a landing that changes a conclusion, verifier-versus-builder disagreement, close-outs, and anything touching premise, roadmap or CLAUDE.md. Fold pending questions into one spawn; a killed spawn is RESUMED, never restarted. `.claude/agent-log.tsv` records every spawn.

BUILDERS OVERRUN AND THE BRIEF SHOULD SAY SO. Three of four on 1 September needed a mid-flight instruction to finish rather than deepen, which is a briefing fault rather than an agent fault. Put the scope ceiling and a rough time budget in the brief itself, and say that anything beyond the named list becomes a reported next step rather than more build time.

IF A SESSION-LEVEL INSTRUCTION CONTRADICTS THE STUDIO SPLIT, that is a conflict for Jafar, raised in one line at the start, not resolved alone. Resolving it silently is exactly what went wrong on 1 September.

AUTHORITY: `ledger-v2/` governs, entry point `handoff/HANDOFF.md`; `canon.md` outranks everything. Trust the repo over this prompt wherever they disagree. The formatting law binds every new document: no em-dashes, no italics.

NO SCHEDULED UPDATES. Message Jafar when something needs him, when he asks, or when a deliverable he is waiting on is ready. His idle heartbeat is the branch's commit feed.

ALWAYS: push only to claude/game-dev-ai-automation-2h67ix. Never open a pull request. Never make a purchase or use an account beyond what has been authorised. Voice sourcing: donated-voice corpora only, and no identifiable public figures.

## One known inaccuracy elsewhere, named rather than fixed silently

The paragraph saying the watchdog "IS DISABLED RIGHT NOW, 26 Aug" left
CLAUDE.md on 2026-09-01 (task 013) and now sits, verbatim, in
ledger-v2/studio-v2/runner.md, where the carry header directly above it
carries the correction, applied under the director ruling of 2 September.
Queue item 011 closed with that ruling.
